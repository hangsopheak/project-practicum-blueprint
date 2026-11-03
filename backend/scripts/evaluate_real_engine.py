#!/usr/bin/env python3
"""
backend/scripts/evaluate_real_engine.py
=======================================
Evaluates the REAL JobMatch engine (MiniLM embeddings + alias-normalised
skill coverage from app/services/matching_engine.py) on the benchmark data
in evaluate_recommendations.py (PROFILES, JOBS, LABELS).

Run from the backend folder:
    python scripts/evaluate_real_engine.py

Nothing here is hardcoded: the conclusion is computed from the results.
"""

import sys
import time
from pathlib import Path
from types import SimpleNamespace

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))            # lets `import app...` work
sys.path.insert(0, str(Path(__file__).parent))  # lets the dataset file import

from evaluate_recommendations import PROFILES, JOBS, LABELS  # noqa: E402
from app.services import matching_engine as me               # noqa: E402

K = 5
SYSTEMS = [
    ("Skills only (1.0/0.0)", 1.0, 0.0),
    ("Semantic only (0.0/1.0)", 0.0, 1.0),
    ("Hybrid 0.5/0.5", 0.5, 0.5),
    ("JobMatch 0.7/0.3", 0.7, 0.3),
    ("Hybrid 0.9/0.1", 0.9, 0.1),
]
DEFAULT_NAME = "JobMatch 0.7/0.3"


# ── Text builders (use the engine's own builders) ───────────────────────────
def candidate_text(p):
    prof = SimpleNamespace(preferred_role=p["role"], education=p["edu"])
    return me._build_candidate_text(prof, p["skills"])


def job_text(j):
    job = SimpleNamespace(title=j["title"], company=j["company"], description=j["desc"])
    return me._build_job_text(job)


# ── Scoring with the real engine functions ──────────────────────────────────
def score_profile(model, p, jobs):
    """Returns {job_id: (coverage, semantic)} using the real engine."""
    ct = candidate_text(p)
    cand_emb = me._embed(model, ct) if ct.strip() else None
    out = {}
    for j in jobs:
        cov = me._compute_skill_coverage(set(p["skills"]), set(j["skills"]))
        sem = me._compute_semantic_similarity(
            ct, job_text(j), candidate_emb=cand_emb, job_id=j["id"]
        )
        out[j["id"]] = (cov, sem)
    return out


def rank(scores, pool_ids, w_s, w_m):
    total = w_s + w_m
    # ties broken by job id so results are reproducible
    return sorted(
        pool_ids,
        key=lambda jid: (-(w_s * scores[jid][0] + w_m * scores[jid][1]) / total, jid),
    )


def evaluate(all_scores, pool_ids, w_s, w_m):
    """P@K and R@K averaged over profiles. Relevant set is limited to the pool,
    so the Khmer-subset recall is not penalised for English jobs."""
    pool = set(pool_ids)
    P, R = [], []
    for p in PROFILES:
        relevant = LABELS[p["id"]] & pool
        if not relevant:
            continue
        top = rank(all_scores[p["id"]], pool_ids, w_s, w_m)[:K]
        hits = sum(1 for jid in top if jid in relevant)
        P.append(hits / K)
        R.append(hits / len(relevant))
    n = len(P)
    return sum(P) / n, sum(R) / n, n


def print_table(title, all_scores, pool_ids):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)
    print(f"{'System':<26}{'P@5':>8}{'R@5':>8}{'profiles':>10}")
    print("-" * 64)
    results = {}
    for name, w_s, w_m in SYSTEMS:
        p, r, n = evaluate(all_scores, pool_ids, w_s, w_m)
        results[name] = (p, r)
        print(f"{name:<26}{p:>8.2f}{r:>8.2f}{n:>10}")
    key = lambda v: (round(v[0], 4), round(v[1], 4))
    best = max(results.values(), key=key)
    winners = [n for n, v in results.items() if key(v) == key(best)]
    print("-" * 64)
    print("Best by P@5 then R@5:", ", ".join(winners))
    if DEFAULT_NAME in winners and len(winners) == 1:
        print(f"-> {DEFAULT_NAME} is the single best system on this set.")
    elif DEFAULT_NAME in winners:
        print(f"-> {DEFAULT_NAME} ties for best; the set cannot separate them.")
    else:
        print(f"-> {DEFAULT_NAME} is NOT the best here. Report this honestly.")


def latency_report(model):
    print("\n" + "=" * 64)
    print(f"LATENCY ({len(JOBS)} jobs, this machine)")
    print("=" * 64)
    me._job_embedding_cache.clear()
    t0 = time.perf_counter()
    for j in JOBS:
        me.get_job_embedding(model, j["id"], job_text(j))
    cold = (time.perf_counter() - t0) * 1000
    print(f"Cold (encode all job texts once): {cold:8.1f} ms  ({cold / len(JOBS):.1f} ms/job)")

    repeats = 20
    t_total, t_rank_only = 0.0, 0.0
    for _ in range(repeats):
        for p in PROFILES:
            ct = candidate_text(p)
            t0 = time.perf_counter()
            cand_emb = me._embed(model, ct)          # per-request encoding
            t1 = time.perf_counter()
            for j in JOBS:
                me._compute_skill_coverage(set(p["skills"]), set(j["skills"]))
                me._compute_semantic_similarity(
                    ct, job_text(j), candidate_emb=cand_emb, job_id=j["id"]
                )
            t2 = time.perf_counter()
            t_total += (t2 - t0) * 1000
            t_rank_only += (t2 - t1) * 1000
    n = repeats * len(PROFILES)
    print(f"Warm, ranking only (candidate pre-encoded): {t_rank_only / n:8.2f} ms")
    print(f"Warm, end-to-end (includes candidate encoding): {t_total / n:8.2f} ms")
    print("Note: excludes database queries. Time the real endpoint separately.")


def error_analysis(all_scores):
    print("\n" + "=" * 64)
    print("TOP-5 PER PROFILE, JobMatch 0.7/0.3 (✓ relevant, ✗ not relevant)")
    print("=" * 64)
    titles = {j["id"]: j["title"] for j in JOBS}
    ids = [j["id"] for j in JOBS]
    for p in PROFILES:
        print(f"\nProfile {p['id']}: {p['role']}")
        for jid in rank(all_scores[p["id"]], ids, 0.7, 0.3)[:K]:
            cov, sem = all_scores[p["id"]][jid]
            mark = "✓" if jid in LABELS[p["id"]] else "✗"
            print(f"  {mark} {jid} {titles[jid][:42]:<42} cov={cov:.2f} sem={sem:.2f}")


def sensitivity_sweep(all_scores):
    print("\n" + "=" * 64)
    print("WEIGHT SENSITIVITY (in-sample, NOT a tuning result)")
    print("=" * 64)
    ids = [j["id"] for j in JOBS]
    print(f"{'w_skill/w_sem':<16}{'P@5':>8}{'R@5':>8}")
    for i in range(0, 11):
        w_s = i / 10
        p, r, _ = evaluate(all_scores, ids, w_s, 1 - w_s)
        print(f"{w_s:.1f}/{1 - w_s:.1f}{'':<9}{p:>8.2f}{r:>8.2f}")


def main():
    model = me._get_embedding_model()
    if model is None:
        sys.exit(
            "ERROR: embedding model did not load (is sentence-transformers "
            "installed and the model downloaded?). Refusing to run, because "
            "semantic scores would silently be 0.0."
        )

    all_ids = [j["id"] for j in JOBS]
    km_jobs = [j for j in JOBS if j["lang"] == "km"]
    km_ids = [j["id"] for j in km_jobs]

    all_scores = {p["id"]: score_profile(model, p, JOBS) for p in PROFILES}

    print("JOBMATCH CAMBODIA: EVALUATION OF THE REAL ENGINE")
    print(f"{len(JOBS)} jobs ({len(JOBS) - len(km_jobs)} English, {len(km_jobs)} Khmer/bilingual) "
          f"x {len(PROFILES)} profiles; model: {me._EMBEDDING_MODEL_NAME}")

    print_table("ALL 30 JOBS", all_scores, all_ids)
    print_table("KHMER / BILINGUAL SUBSET ONLY (15 jobs)", all_scores, km_ids)
    sensitivity_sweep(all_scores)
    error_analysis(all_scores)
    latency_report(model)


if __name__ == "__main__":
    main()
