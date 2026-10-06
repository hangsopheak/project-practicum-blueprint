# Agent Instructions

This is a solo Bachelor capstone monorepo. The student's planning documents in `context/` are the source of truth. Read the relevant ones before doing any work.

## Context, in reading order

1. `README.md`: project summary and current progress
2. `context/phase-01/`: the problem, users, domain terms and chosen tech stack
3. `context/phase-02/`: scope (MoSCoW matrix) and user journeys
4. `context/phase-03/`: architecture, database design and API contracts
5. `context/phase-04/`: screens and design tokens
6. `context/phase-05/` to `context/phase-08/`: implementation, testing and thesis records, once they exist

## Rules

- Never edit anything in `template/`. It belongs to the advisor.
- Only build features listed as Must-Have or Should-Have in the MoSCoW matrix. Anything else needs a scope change entry first.
- Implement endpoints exactly as the API contracts specify. If a contract must change, update the contract document first.
- An endpoint must pass in the API test collection (`api-specs/`) before any screen uses it.
- Use the domain terms from Phase 1.1 for names in code, the database and the UI.
- Never commit secrets. Real values go in git-ignored `.env` files; keep `.env.example` up to date.
- After finishing a task, update the matching tracker in `context/` and the Progress section of `README.md`.

## Stack and commands

[STUDENT INPUT: your language, framework, database and client framework, plus the commands to install, run, test and seed the project.]
