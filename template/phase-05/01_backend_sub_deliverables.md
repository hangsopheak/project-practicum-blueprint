# Phase 5.1 — Backend Sub-Deliverables

**Objective:** Build the backend in four small, verifiable pieces so that you always have something working, and record how to rebuild the database from scratch.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] SD-1 to SD-4 are Done, each with a commit link
- [ ] Every Must-Have endpoint passes in your API test collection (shown in Phase 5.2)
- [ ] The runbook rebuilds the database from scratch (reset, migrate, seed) on a fresh clone
- [ ] No real secrets are committed; `backend/.env.example` lists every variable
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Sub-Deliverables

Finish them in order. Commit at the end of each one, and reference the SD in the commit message.

| SD | Scope | Done when | Endpoints | Target date | Status | Evidence (commit) |
|---|---|---|---|---|---|---|
| SD-1 | Database setup & migrations | All Phase 3.3 tables are created by migrations, and test seed data loads | none | [STUDENT INPUT] | Not started | |
| SD-2 | Authentication & authorization | Register, login, token issuing, and middleware that protects routes and checks roles | [STUDENT INPUT: EP-xx] | [STUDENT INPUT] | Not started | |
| SD-3 | Core CRUD entities | Create/read/update/delete for the primary resources, with validation | [STUDENT INPUT: EP-xx] | [STUDENT INPUT] | Not started | |
| SD-4 | Complex business logic & transactions | Calculations, multi-table writes in one transaction, status rules | [STUDENT INPUT: EP-xx] | [STUDENT INPUT] | Not started | |

Status values: Not started · In progress · Done

## 2. Implementation Notes

For each sub-deliverable, note the decisions you made and anything that differs from the Phase 3 plan. If the contract changed, update the Phase 3 document first.

- SD-1: [STUDENT INPUT: migration tool, list of tables, what the seed data contains]
- SD-2: [STUDENT INPUT: password hashing, token lifetime, roles]
- SD-3: [STUDENT INPUT: resources and validation rules]
- SD-4: [STUDENT INPUT: business rules, and which operations run in a transaction]

## 3. Environment & Database Migration Runbook

Write the exact commands for your stack. Test them on a fresh clone.

| Task | Command |
|---|---|
| Create the env file | [STUDENT INPUT: e.g. copy `backend/.env.example` to `backend/.env`] |
| Start the database | [STUDENT INPUT] |
| Run migrations | [STUDENT INPUT] |
| Seed test data | [STUDENT INPUT] |
| Reset the database (drop, migrate, seed) | [STUDENT INPUT] |
| Start the API on port 8000 | [STUDENT INPUT] |
| Run the API test collection | [STUDENT INPUT] |
| Check that it works | `curl http://localhost:8000/api/v1/health` |

Seeded test accounts (fake data only):

| Role | Email / username | Password |
|---|---|---|
| [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
