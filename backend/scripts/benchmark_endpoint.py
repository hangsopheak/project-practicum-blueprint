#!/usr/bin/env python3
"""
backend/scripts/benchmark_endpoint.py
=====================================
Benchmarks the end-to-end GET /api/v1/recommendations endpoint,
measuring database query time, model encoding time, and total HTTP response time.
"""

import time
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from main import app
from app.services import matching_engine as me

client = TestClient(app)

def benchmark():
    # Login to obtain auth token
    res = client.post("/api/v1/auth/login", json={"email": "dara@example.com", "password": "Password123!"})
    if res.status_code != 200:
        sys.exit(f"Login failed: {res.text}")
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("================================================================")
    print("JOBMATCH CAMBODIA: ENDPOINT BENCHMARK (GET /api/v1/recommendations)")
    print("================================================================")

    # 1. Cold Request (cleared cache)
    me._job_embedding_cache.clear()
    t0 = time.perf_counter()
    res_cold = client.get("/api/v1/recommendations", headers=headers)
    t_cold = (time.perf_counter() - t0) * 1000
    assert res_cold.status_code == 200, res_cold.text
    total_jobs = len(res_cold.json())
    print(f"Cold HTTP Request (all {total_jobs} active jobs, empty RAM cache): {t_cold:.2f} ms")

    # 2. Warm Requests (repeated 20 times)
    repeats = 20
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        res_warm = client.get("/api/v1/recommendations", headers=headers)
        t_warm = (time.perf_counter() - t0) * 1000
        assert res_warm.status_code == 200
        times.append(t_warm)

    avg_warm = sum(times) / len(times)
    min_warm = min(times)
    max_warm = max(times)

    print(f"Warm HTTP Request (mean over {repeats} calls): {avg_warm:.2f} ms (min: {min_warm:.2f} ms, max: {max_warm:.2f} ms)")
    print("Includes: PostgreSQL queries (eager-loaded), candidate text encoding, cached job lookups, and JSON serialization.")
    print("================================================================")

if __name__ == "__main__":
    benchmark()
