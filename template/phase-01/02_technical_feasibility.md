# Phase 1.2 — Technical Feasibility

**Objective:** Choose a tech stack you can actually deliver alone, list every external dependency, and plan for what could go wrong.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] Every stack layer has a choice, a version and a reason
- [ ] Every external service has a fallback
- [ ] Your stack is written in `AGENTS.md`
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Tech Stack Selection & Justification

Guiding questions: What have you already used? Is the documentation good? Can you finish it alone in the time you have?

| Layer | Your choice (with version) | Alternative considered | Why this choice |
|---|---|---|---|
| Backend language & framework | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| Database | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| Client (mobile or web) | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| Authentication | [STUDENT INPUT: e.g. JWT or a managed auth service; the client sends its token as `Authorization: Bearer <token>`] | [STUDENT INPUT] | [STUDENT INPUT] |
| API testing tool | [STUDENT INPUT: e.g. Bruno, Postman, Insomnia] | [STUDENT INPUT] | [STUDENT INPUT] |
| Hosting / running locally | [STUDENT INPUT: e.g. Docker, local install, a cloud service] | [STUDENT INPUT] | [STUDENT INPUT] |

## 2. Third-Party Service Dependencies

Only list services you will really use (e.g. cloud storage, maps, SMS, payment gateway, push notifications). API keys go in a git-ignored `.env` file, never in Git.

| Service | Purpose | Provider | Free-tier limit | Fallback if it fails |
|---|---|---|---|---|
| [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| | | | | |

## 3. Top Risks

| Risk | What you'll do about it |
|---|---|
| [STUDENT INPUT: e.g. I have never used this framework] | [STUDENT INPUT: e.g. follow its official tutorial in week 2] |
| | |
| | |
