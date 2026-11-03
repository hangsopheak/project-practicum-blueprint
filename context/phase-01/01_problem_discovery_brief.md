# Phase 1.1 — Problem Discovery Brief

**Objective:** Describe the problem, who suffers from it, and why existing solutions are not good enough. Every later decision traces back to this document.

**Status:** Submitted · **Last updated:** 2026-10-15

## Done When

- [x] Every pain point has an ID (PP-01, PP-02, …) that Phase 2 can reference
- [x] The persona refers to specific pain points
- [x] At least 3 existing solutions are compared, each linked to a pain point
- [x] Your unique angle fits in one sentence

## 1. Problem Statement

Guiding questions: Who has this problem? When and how often does it happen? What does it cost them (time, money, stress)?

**Context**

> Job seekers in Cambodia must visit multiple job websites (e.g., LinkedIn, CamHR, JobsInPhnomPenh) every day to find vacancies. Each platform presents job data in different formats — for example, one site says "Mobile Developer" while another says "Mobile Application Developer" for the same type of role. Salary, location, required skills, and job type are also formatted differently across sources, making side-by-side comparison difficult. There is currently no single Cambodian-focused app that collects, cleans, and unifies job listings from multiple sources while also matching them to a user's specific skills and profile.

**Pain points**

| ID | Pain point | Who suffers | How often |
|---|---|---|---|
| PP-01 | Must visit multiple job sites to find all vacancies | Job seekers | Every job search session (daily) |
| PP-02 | Job data is inconsistent across sources (title, salary, skills format differ) | Job seekers | Every time they compare jobs |
| PP-03 | Duplicate listings appear on multiple platforms, wasting review time | Job seekers | Frequently during search |
| PP-04 | No personalized match score — user must manually judge if they qualify | Job seekers | Every job detail view |

**Problem statement in one sentence**

> Cambodian job seekers struggle to find and compare vacancies efficiently because job information is scattered across multiple platforms in inconsistent formats, which costs them significant time and leads them to miss or misjudge relevant opportunities.

## 2. Target User Persona

Guiding question: If you could build this for only one person, who would it be?

| Field | P-01 (primary) | P-02 (secondary) |
|---|---|---|
| Name, age, role | Dara, 22, final-year Computer Science student in Phnom Penh | Sreymom, 27, mid-level marketing professional looking for a career switch |
| A typical day | Attends classes, works on personal projects, checks LinkedIn and CamHR in the evening for internships and entry-level jobs | Works at an agency during the day, browses job sites on lunch break and after work |
| Daily struggles | PP-01, PP-02 — opens 3–4 different sites, sees the same jobs re-listed, and is unsure if his Flutter skills meet the requirements | PP-01, PP-03 — wastes time on duplicate listings and cannot easily filter for roles matching her current skill set |
| Goals | Land a Flutter/mobile developer internship before graduation | Find a digital-marketing or UX role that values her existing communication and design skills |
| Tech literacy | High — uses Flutter, Dart, Firebase daily; smartphone-first; uses Telegram, YouTube, and Google regularly | Medium — comfortable with apps and web, does not use developer tools |
| What they would say about the problem | "I have to open CamHR, LinkedIn, and two other sites every night just to see the same 10 jobs again." | "I never know if I'm actually qualified — I just send my CV and hope for the best." |

## 3. Domain Terminology

List the business terms of your domain, not technical terms, including status words such as Pending or Closed. They become your table names, API resources, status values and screen labels, so define each once and use it consistently.

| Term | Definition in this project | Synonyms to avoid | Business rule |
|---|---|---|---|
| Job Listing | One normalized vacancy record stored in the system, regardless of how many sources it came from | vacancy, posting, job post | Two listings from different sources are merged if they share the same company, title, and location |
| Job Source | An external website or API from which the system extracts job listings | site, platform, provider | Each source has a unique identifier and a last-fetched timestamp |
| User Profile | A registered user's personal and professional information used for job matching | resume, CV profile | A user must complete at minimum their skills and preferred role before matching is enabled |
| Skill | A specific technical or soft competency listed on either a User Profile or a Job Listing | expertise, technology, tool | Stored as normalized tags (e.g., "Flutter" not "flutter" or "Flutter SDK") |
| Match Score | A percentage value (0–100 %) indicating how well a user's profile fits a Job Listing | compatibility, relevance score | Calculated by comparing user skills and experience level against job requirements |
| Saved Job | A Job Listing that a user has bookmarked for later review | favourite, starred job | A user can save unlimited jobs; saving does not affect Match Score |
| Job Category | A standardized grouping of Job Listings by field (e.g., Software Development, Marketing) | industry, sector | Applied during data normalization to replace source-specific labels |

## 4. Competitor / Existing Solution Teardown

Guiding questions: What do people use today, including spreadsheets, chat groups or paper? Why do they still have the problem?

| Existing solution | Type | What it does well | Why it is inadequate (refer to PP-xx) |
|---|---|---|---|
| CamHR | Website / app | Cambodia-specific jobs, company profiles, job alerts | No AI matching; still requires manual browsing; data is only from CamHR's own listings (PP-01, PP-04) |
| LinkedIn | Website / app | Large global network, skill endorsements, easy apply | Not focused on Cambodia; many listings are not local; no match-score feature visible to user (PP-01, PP-04) |
| JobsInPhnomPenh | Website | Local Cambodian jobs, free to browse | Basic keyword search only; no filtering by skill or experience; no deduplication (PP-02, PP-03, PP-04) |
| Telegram job groups | Manual / chat | Real-time posts, widely used in Cambodia | Completely unstructured; no search, no filtering, no deduplication (PP-02, PP-03, PP-04) |

**Your unique angle**

> Unlike any existing solution in Cambodia, this app aggregates job listings from multiple sources into one normalized feed and uses AI-assisted skill matching to tell the user exactly how well they fit each job — before they apply.
