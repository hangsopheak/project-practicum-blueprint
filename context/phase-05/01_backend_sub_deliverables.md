# Phase 5.1 — Backend Sub-Deliverables

**Objective:** Build the backend in four small, verifiable pieces so that you always have something working, and record how to rebuild the database from scratch.

**Status:** Submitted · **Last updated:** 2026-10-24

## Done When

- [x] SD-1 to SD-4 are Done, each with verification evidence
- [x] Every Must-Have endpoint passes in your API test collection (shown in Phase 5.2)
- [x] The runbook rebuilds the database from scratch (reset, migrate, seed) on a fresh clone
- [x] No real secrets are committed; `backend/.env.example` lists every variable

## 1. Sub-Deliverables

| SD | Scope | Done when | Endpoints | Target date | Status | Evidence |
|---|---|---|---|---|---|---|
| SD-1 | Database setup & migrations | All Phase 3.3 tables created in PostgreSQL with indexes, relationships, 25-point job attributes, Alembic migrations, cross-source deduplication schema, and seed data | none | 2026-10-18 | Done | `backend/app/models/models.py`, `backend/alembic/`, `backend/seed.py` |
| SD-2 | Authentication & authorization | Register, login, email OTP verification, token issuing, and role middleware (`user`, `admin`) | EP-02, EP-03, EP-14, EP-15 | 2026-10-23 | Done | `backend/app/api/auth.py`, `email_service.py`, `deps.py` |
| SD-3 | Core CRUD entities | Create/read/update/delete for the primary resources: profiles, skills, jobs, bookmarks, and recruitment sources | EP-04, EP-05, EP-06, EP-07, EP-08, EP-10, EP-11, EP-12, EP-16, EP-17 | 2026-10-18 | Done | `backend/app/api/profile.py`, `jobs.py`, `skills.py`, `saved_jobs.py`, `sources.py` |
| SD-4 | Complex business logic & AI matching | Dual-metric AI job recommendation engine (`required_skill_coverage` + `semantic_similarity` -> `ranking_score`), data cleaning pipeline, background auto-scraper, 3-tier cross-source dedup with anti-phishing protection | EP-01, EP-09, EP-13 | 2026-10-18 | Done | `backend/app/services/matching_engine.py`, `dedup_manager.py`, `importer.py`, `scheduler.py` |

## 2. Implementation Notes

- **SD-1 (Database Setup & Alembic Migrations):** Tables created in PostgreSQL 16 Alpine Docker container with SQLAlchemy ORM declarative models. Managed via Alembic migrations (`backend/alembic/versions/cc7e0eccd8d8_add_duplicate_of_and_cross_source_dedup.py`, `d4e5f6a7b8c9_add_sources_table_and_source_id.py`, and `e5f6a7b8c9d0_add_jev_classification_columns.py`). Created tables: `users`, `profiles`, `skills`, `profile_skills`, `sources`, `job_listings` (with `source_id` foreign key, `job_category`, `job_subcategory`, `job_level`, `classification_confidence`, `classification_source`, self-referencing `duplicate_of`, contact channels, `last_seen_at`), `telegram_jobs`, `web_jobs`, `job_skills`, `saved_jobs`, `email_otps`.
- **SD-2 (Authentication & Security):** Cryptographic password hashing using `bcrypt`. Stateless JWT Bearer tokens signed with HMAC-SHA256. 6-digit cryptographic Email OTP verification with live Gmail SMTP and anti-reuse protection. Role-Based Access Control (`role == "admin"`) enforced via FastAPI dependency injection.
- **SD-3 (Core CRUD Resources):** All endpoints implement Pydantic V2 request/response schema validation. Job discovery supports search by title, company, description, and filter by source (JobNet, BongThom, Khmer24, Telegram), experience level, location, and incremental sync (`since=`). Duplicate job rows are cleanly hidden from candidate discovery.
- **SD-4 (AI Engine, Auto-Scraping, Deduplication & Classification):**
  - AI engine combines explainable skill coverage with dense multilingual vector embeddings via `paraphrase-multilingual-MiniLM-L12-v2` (384-dimensional dense vectors supporting English + Khmer Unicode script).
  - Background async scheduler polls and syncs active channels on an hourly schedule (every 60 minutes) non-blockingly.
  - Cross-source deduplication engine uses 3-tier matching (`dedup_hash` SHA-256, contact matching, and title/company fuzzy matching) with anti-phishing isolation (contacts from duplicates are never copied into the primary job).
  - Jev Structured Job Classification (`backend/app/services/job_classifier.py`): Integrates TypeSafe AI Jev API spec with deterministic Python rule-based fallback. Since TypeSafe AI requires commercial prepaid billing (\$5 minimum with no automated student tier), the system operates on the verified local fallback engine pending advisor consultation.

## 3. Environment & Database Migration Runbook

| Task | Command |
|---|---|
| Create the env file | `cp backend/.env.example backend/.env` |
| Start the database | `docker compose up -d db` |
| Run database migrations | `cd backend && alembic upgrade head` |
| Create tables & run seeds | `cd backend && python seed.py` |
| Reset the database | `docker compose down -v && docker compose up -d db && cd backend && alembic upgrade head && python seed.py` |
| Start the API on port 8000 | `cd backend && uvicorn main:app --reload --port 8000` |
| Run the API test collection | `PYTHONPATH=. tests/venv/bin/pytest tests/ -v` (70 tests) |
| Check health endpoint | `curl http://localhost:8000/api/v1/health` |

### Seeded Test Accounts (Local Testing Only):

| Role | Email | Password | Purpose |
|---|---|---|---|
| Admin | `rith512@gmail.com` | `12345678` | System admin, EP-13 scraping triggers, admin stats |
| Candidate | `dara@example.com` | `Password123!` | Test candidate with Flutter/Dart skills for AI matching |
