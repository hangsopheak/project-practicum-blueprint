# AI-Assisted Job Aggregator Mobile Application

Bachelor of Computer Science — Individual Capstone

| | |
|---|---|
| Student | RETH CHAN RITH — E2 |
| Advisor | Sopheak |
| Term | Year 4, Semester 1 — 2026 |
| Pitch | Cambodian job seekers struggle to find and compare vacancies across multiple platforms, so this app aggregates listings from multiple sources, normalizes the data, and uses AI to match each job to the user's skill profile. |

First time here? Read the guide: [template/README.md](template/README.md)

## Progress

Update this section whenever you work on a phase. Your advisor reads it to follow your progress.

| | |
|---|---|
| Now working on | Phase 6 — Frontend Client & Integration |
| Blockers | None |
| Last updated | 2026-11-03 |

| Phase | Planned due | Status | Submitted on |
|---|---|---|---|
| 1. Domain & Problem Teardown | 2026-10-17 | Submitted | 2026-10-15 |
| 2. Scope, Logic & MoSCoW | 2026-10-17 | Submitted | 2026-10-15 |
| 3. Architecture, ERD & API Planning | 2026-10-24 | Submitted | 2026-10-18 |
| 4. UI/UX & Figma Design | 2026-10-24 | Submitted | 2026-10-19 |
| 5. Backend Core & API Implementation | 2026-10-24 | Submitted | 2026-10-19 |
| 6. Frontend Client & Integration | | Not started | |
| 7. QA, Bug Fixes & Test Report | | Not started | |
| 8. Code Freeze, Final Report & Defense | | Not started | |

Status values: Not started · In progress · Submitted · Rework needed

## Links

| Item | Link |
|---|---|
| Figma file | [Figma Design Canvas](https://www.figma.com/design/WzpxtrgeDvPQbwbw0XwyFt/MATCH-JOB?node-id=0-1&t=hzv0ZKwELP0s4A3C-1) |
| Figma prototype | [Figma Interactive Prototype](https://www.figma.com/proto/WzpxtrgeDvPQbwbw0XwyFt/MATCH-JOB?node-id=0-1&t=hzv0ZKwELP0s4A3C-1) |
| Alpha demo video | |
| Thesis | |
| Defense slides | |

## How to Run

```bash
# 1. Start the PostgreSQL database
docker compose up -d db

# 2. Install backend dependencies & configure env
cd backend && pip install -r requirements.txt
cp .env.example .env

# 3. Run Alembic database migrations
alembic upgrade head

# 4. Start the FastAPI backend server (port 8000)
uvicorn main:app --reload --port 8000

# 5. Run the complete test suite (70 automated tests)
PYTHONPATH=. tests/venv/bin/pytest tests/ -v
```

## Repository Layout

| Path | Contents |
|---|---|
| `template/` | Guide and phase templates from the advisor (do not edit) |
| `context/` | My completed phase documents and evidence |
| `backend/` | Backend code |
| `mobile/` | Flutter mobile app code |
| `api-specs/` | API test collection |
| `AGENTS.md` | Instructions for AI coding assistants |
