# Capstone Guide

How to use this repository for your individual Bachelor capstone. Read it once at the start, then again at the start of every phase.

## 1. Getting Started

1. **Fork** this repository on GitHub. Don't just download or clone it. Your fork is your monorepo: it holds your planning documents and all of your code.
2. Clone your fork, then fill in the top of the root `README.md` (project title, your name, your advisor).
3. Write your stack into `AGENTS.md` once you have chosen it in Phase 1.2, and add the run commands once you have code.

## 2. Who Owns What

| Path | Owner | Contents |
|---|---|---|
| `template/` | Advisor | This guide, the blank phase templates and their sample images. Never edit it in your fork. |
| `context/` | You | Your completed phase documents and evidence |
| `backend/`, `mobile/`, `api-specs/` | You | Your code and your API test collection |
| `README.md`, `AGENTS.md` | You | Your project page with progress, and your instructions for AI coding assistants |

When your advisor updates the templates, click **Sync fork** on your fork's GitHub page, then run `git pull`. You never edit `template/`, so syncing never conflicts with your work.

`context/` holds your project context. The documents in it are the source of truth for you, for your advisor, and for any AI coding assistant you use (`AGENTS.md` points assistants there). The more accurate it is, the better it guides your work.

## 3. The 8-Phase Roadmap

```text
+---+-------------------------------+--------+--------------------------------------------------------+
| # | Phase                         | Weeks* | Done when                                              |
+===+===============================+========+========================================================+
| 1 | Domain & Problem Teardown     | 1-2    | Problem, persona, domain terms and competitor gap      |
|   |                               |        | documented; stack chosen.                              |
+---+-------------------------------+--------+--------------------------------------------------------+
| 2 | Scope, Logic & MoSCoW         | 3      | Every feature has an ID and one priority; Must-Haves   |
|   |                               |        | fit the time available; 5-8 user journeys written.     |
+---+-------------------------------+--------+--------------------------------------------------------+
| 3 | Architecture, ERD & API Plan  | 4-5    | Component map, ERD and API contracts done; a test      |
|   |                               |        | request saved for every endpoint (failing is OK); no   |
|   |                               |        | feature code yet.                                      |
+---+-------------------------------+--------+--------------------------------------------------------+
| 4 | UI/UX & Figma Design          | 6-7    | Figma file with design system, screens and a clickable |
|   |                               |        | prototype; 6-10 screens exported to the context/       |
|   |                               |        | folder.                                                |
+---+-------------------------------+--------+--------------------------------------------------------+
| 5 | Backend Core & API            | 8-10   | SD-1 to SD-4 done; database rebuilds from scratch;     |
|   |                               |        | every Must-Have endpoint passes its API tests with     |
|   |                               |        | real data.                                             |
+---+-------------------------------+--------+--------------------------------------------------------+
| 6 | Frontend Client & Integration | 11-13  | Every screen connected to live endpoints; loading,     |
|   |                               |        | empty and error states handled; alpha demo recorded.   |
+---+-------------------------------+--------+--------------------------------------------------------+
| 7 | QA, Bug Fixes & Test Report   | 14     | Functional, negative, security and device tests run;   |
|   |                               |        | metrics reported; no open Critical bugs.               |
+---+-------------------------------+--------+--------------------------------------------------------+
| 8 | Code Freeze, Report & Defense | 15-16  | Code frozen; runs from a fresh clone; thesis and       |
|   |                               |        | defense prepared with your institution's templates.    |
+---+-------------------------------+--------+--------------------------------------------------------+
```

(*) Suggested weeks for a 16-week semester, with the defense right after week 16; they match the Defense Preparation Timeline in Section 8. If your defense is earlier, plan backwards from Section 8 and your institution's calendar.

Phases 1–7 have templates in this folder. For Phase 8, use the thesis and defense templates from your institution.

Rules for every phase:

- No feature code before Phase 5.
- An endpoint must pass in your API test collection before you build a screen that uses it.
- Scope is frozen after Phase 2. Agree any change with your advisor and note it under Scope Changes in your Phase 2.1 document.

## 4. Working on a Phase

1. Copy the phase templates into your `context/` folder:

   ```bash
   cp template/phase-03/*.md context/phase-03/
   ```

2. Fill in every `[STUDENT INPUT: ...]` in your copy. Keep the headings and table columns.
3. Commit to `main` whenever you finish a piece of work, and mention the IDs you worked on, for example `docs(phase-03): add EP-07 contract`.
4. Keep the Progress section of the root `README.md` up to date.
5. When the phase is done, run the placeholder check. It must print nothing:

   ```bash
   grep -rn "STUDENT INPUT" context/phase-03/
   ```

6. To submit, set the phase's Status to Submitted and write the date under Submitted on, in the Progress section of the root `README.md`. If your advisor asks for rework, update the documents and submit again with the new date.

Your advisor follows your progress by reading your fork, not by reviewing pull requests. If a later phase forces a change to an earlier document, edit that document and say why in the commit message.

## 5. IDs Used Across Documents

| ID | Meaning | Defined in |
|---|---|---|
| PP-01 | Pain point | Phase 1.1 |
| P-01 | Persona | Phase 1.1 |
| F-01 | Feature | Phase 2.1 |
| UJ-01 | User journey | Phase 2.2 |
| EP-01 | API endpoint | Phase 3.3 |
| SCR-01 | Screen | Phase 4.1 |
| SD-1 | Backend sub-deliverable | Phase 5.1 |
| TC-FN-01, TC-NB-01, TC-SEC-01, TC-DEV-01 | Test cases (functional, negative/boundary, security, device) | Phase 7.1 |
| BUG-001 | Defect | Phase 7.2 |

## 6. Project Conventions

The technology is your choice; justify it in Phase 1.2. Every project follows these conventions:

- The API runs on port 8000 locally, and every route starts with `/api/v1`.
- `GET /api/v1/health` returns `200` with `{"status":"ok","timestamp":"<ISO-8601>"}`.
- Every error response has the shape `{"error":{"code":"...","message":"...","details":[]}}`.
- Protected routes use the header `Authorization: Bearer <token>`.
- The API test collection lives in `api-specs/`, using the tool of your choice (Bruno, Postman, Insomnia, …).
- Secrets live only in git-ignored `.env` files. Commit an `.env.example` file with fake values.

## 7. Prerequisites

- Git and a GitHub account.
- A Figma account (the Education plan is free).
- An API testing tool of your choice.
- Docker (recommended, for running your database).
- The runtimes and SDKs for the stack you choose in Phase 1.2.

## 8. Defense Preparation Timeline

| When (D = defense day) | Milestone |
|---|---|
| D − 4 weeks | Feature freeze: only Must-Have gaps and bug fixes from now on |
| D − 3 weeks | QA done: test report and defect log complete, no open Critical bugs |
| D − 2 weeks | Code freeze: final version on `main`, full thesis draft ready |
| D − 10 days | First timed rehearsal; backup demo video recorded |
| D − 1 week | Second rehearsal; slides and thesis revised |
| D − 3 days | Final thesis submitted (check your institution's deadline) |
| D − 1 day | Dress rehearsal on the defense laptop and phone; database re-seeded |

## 9. For the Advisor

- See every student fork: this repository → **Insights → Forks**.
- In a fork, read the Progress section of the root `README.md`. It shows each phase's status and submission date, and activity is in the commit history.
- Count the unfilled placeholders per file in a cloned fork:

  ```bash
  grep -rc "STUDENT INPUT" context/ | grep -v ":0$"
  ```

- If student work must stay private, keep this repository private (for example in a GitHub organization that allows forking). Forks of a private repository stay private, but they inherit its team permissions: students who get access through a team can read each other's forks, so give students access individually if that matters.
