# Phase 3.1 — Tech Stack & Feasibility

**Objective:** Choose a tech stack that fits your Must-Have features and that you can deliver alone, list the external services those features need, and plan for what could go wrong.

**Status:** Submitted · **Last updated:** 2026-10-18

## Done When

- [x] Every stack layer has a choice, a version and a reason
- [x] Every external service has a fallback
- [x] Your stack is written in `AGENTS.md`

## 1. Tech Stack Selection & Justification

| Layer | Your choice (with version) | Alternative considered | Why this choice |
|---|---|---|---|
| Backend language & framework | Python 3.11 + FastAPI (0.110+) | Node.js (Express) / Django | Fast asynchronous performance, native integration with Python data scraping (`bs4`) and AI matching (`scikit-learn`), automatic interactive Swagger API documentation. |
| Database | PostgreSQL 16 | MySQL / MongoDB | Excellent relational integrity, powerful full-text search indexing for job descriptions, JSONB support for flexible metadata, and native Docker support. |
| Client (mobile or web) | Flutter 3.44 (Dart 3.12) | Kotlin (Android) / React Native | Compiles natively to Android APK, single codebase, fast hot reload, rich component library matching the Jobko UI design kit. |
| Authentication | JWT (JSON Web Tokens) with passlib (bcrypt) | Firebase Auth / Supabase | Completely self-hosted without external third-party vendor lock-in or cost; client sends token as `Authorization: Bearer <token>`. |
| API testing tool | Postman / pytest with HTTPX | Bruno / Insomnia | Standard industry tool for team and defense demos, automated status code assertions, exports clean JSON collections into `api-specs/`. |
| Hosting / running locally | Docker Compose (for PostgreSQL) + Uvicorn locally | Manual PostgreSQL install | Reproducible database environment with `docker compose up -d db`, runs on any OS without configuration mismatches. |

## 2. Third-Party Service Dependencies

| Service | Purpose | Provider | Free-tier limit | Fallback if it fails |
|---|---|---|---|---|
| Telegram Channel API / Scraper | Ingest graduate & internship vacancies from `@internshipscambodia` for F-03 | Telegram | Unlimited for public channels | Fallback to public web preview scraping (`https://t.me/s/internshipscambodia`) via BeautifulSoup if API credentials fail. |
| Web Job Boards (CamHR, BongThom) | Ingest local Cambodian vacancies for F-03 | CamHR / BongThom | Free public web access | Retry with exponential backoff; if target site is down, serve existing cached/stored listings from PostgreSQL without disruption. |
| TypeSafe AI (Jev System One) | Structured classification (`job_category`, `job_subcategory`, `job_level`) for F-04 | TypeSafe AI | No automated free student tier (requires \$5 minimum prepaid credit). Student inquiry with academic advisor pending. | Automatic fallback to local Python deterministic rule-based classifier (`backend/app/services/job_classifier.py`). System operates 100% offline-safe and free. |

## 3. Top Risks

| Risk | What you'll do about it |
|---|---|
| Target job websites change HTML structure, breaking scrapers | Implement modular scraper functions with error logging. If a scraper fails, catch exceptions gracefully so the main API remains healthy, and update CSS selectors. |
| Scraped job posts contain messy, unstandardized text and missing salaries | Build a normalization pipeline (F-04) using regex patterns and a standardized skill taxonomy table (`skills`) to extract clean tokens regardless of format. |
| Low accuracy or black-box output in AI matching | Use Explainable AI (XAI) via Cosine Similarity with transparent skill-gap analysis (displaying exact matched skills vs missing skills) so scores are verifiable. |
| External commercial AI API costs / barriers (TypeSafe AI Jev) | Implement a robust hybrid fallback engine (`classification_source='rule'`). All 70 unit tests and DB ingestion run free and offline without external API keys. |
| Scope creep and solo developer time limits | Strictly freeze scope using the MoSCoW matrix (F-01..F-08 Must-Have only), keeping complex features like chatbots as Won't-Have. |
