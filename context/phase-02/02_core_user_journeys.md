# Phase 2.2 — Core User Journeys

**Objective:** Describe the 5–8 most important things users do with your app, step by step, including what happens when something goes wrong. These journeys become your screens (Phase 4), your demo (Phase 6) and your test cases (Phase 7).

**Status:** Submitted · **Last updated:** 2026-10-15

## Done When

- [x] 5 to 8 journeys (UJ-01 … UJ-08), written in Given / When / Then form
- [x] Each journey has a happy path and at least one failure or edge-case path
- [x] Every Must-Have feature appears in the coverage table
- [x] Personas and terms match Phase 1

## 1. Writing Rules

- **Given** describes the starting situation, **When** the user's action, and **Then** the visible result.
- One action per **When**. Use **And** for extra steps.
- **Then** must be something you can check, such as a message, a screen or a saved record.

## 2. Journeys

---

### UJ-01 — User Registration

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara, fresh CS graduate) | Opens the app for the first time and wants to create an account | App installed; no existing account | F-01 |

```gherkin
Scenario: Happy path
  Given Dara opens the app for the first time
  When he taps "Create Account" and enters his email and a valid password
  And he submits the registration form
  Then his account is created and he is taken to the Profile Setup screen

Scenario: Email already registered
  Given Dara tries to register with an email that already exists
  When he submits the registration form
  Then the app shows an error message "This email is already registered. Please log in."
```

---

### UJ-02 — Complete User Profile

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara) | Wants to enable AI job matching by filling in his profile | Registered and logged in; profile is empty | F-02, F-07 |

```gherkin
Scenario: Happy path
  Given Dara is logged in and his profile has no skills entered
  When he navigates to the Profile screen and adds his skills (Flutter, Dart, Firebase)
  And selects his experience level (Entry-level), preferred role (Mobile Developer), and preferred location (Phnom Penh)
  And taps "Save"
  Then his profile is saved and the app confirms with a success message
  And the Recommendations screen now shows Job Listings ranked by Match Score

Scenario: Save attempted with no skills entered
  Given Dara reaches the skills section and leaves it blank
  When he taps "Save"
  Then the app shows a warning "Please add at least one skill to enable job matching"
  And the profile is not saved
```

---

### UJ-03 — Browse and Search for Jobs

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara) | Wants to find Flutter developer jobs in Phnom Penh | Logged in; Job Listings are available in the database | F-05 |

```gherkin
Scenario: Happy path
  Given Dara is on the Home / Job Feed screen
  When he types "Flutter" in the search bar and selects Location = "Phnom Penh"
  And taps the Search button
  Then a list of Job Listings matching "Flutter" in Phnom Penh is displayed
  And each listing shows the job title, company, location, and Match Score

Scenario: Search returns no results
  Given Dara searches for "Blockchain Engineer" in Phnom Penh
  When no matching Job Listings are found
  Then the app displays "No jobs found for this search. Try different keywords."
```

---

### UJ-04 — View Job Detail and Open Application Link

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara) | Finds an interesting listing and wants to read the full details and apply | Logged in; search results are shown | F-06 |

```gherkin
Scenario: Happy path
  Given Dara sees a "Flutter Mobile Developer Intern" listing in his search results
  When he taps the listing
  Then the Job Detail screen opens showing: title, company, location, salary, job type, required skills, job description, posted date, Job Source, and Match Score
  And a button "Apply on [Source Name]" is visible
  When he taps "Apply on [Source Name]"
  Then the app opens the original job posting URL in the device browser

Scenario: Application link is broken or unavailable
  Given Dara taps "Apply on [Source Name]" but the original URL no longer exists
  When the browser returns an error
  Then the app shows the message "This link is no longer available. The job may have been removed from the source."
```

---

### UJ-05 — View AI Match Score and Skill Breakdown

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara) | Wants to know how well his skills match a specific job | Logged in; profile has skills saved; Job Listing is available | F-07, F-02 |

```gherkin
Scenario: Happy path
  Given Dara opens a Job Detail screen for "Flutter Developer Intern"
  And his profile skills are: Flutter, Dart, Firebase
  And the job requires: Flutter, Dart, Firebase, Git
  When the Match Score is calculated
  Then the Job Detail screen shows: Match Score = 75%
  And a breakdown: Matching skills — Flutter, Dart, Firebase | Missing skill — Git

Scenario: Profile has no skills (matching cannot run)
  Given Dara has not added any skills to his profile
  When he opens any Job Detail screen
  Then instead of a Match Score the app shows: "Complete your profile to see your match score"
  And a shortcut link to the Profile screen is provided
```

---

### UJ-06 — View Personalized Job Recommendations

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-01 (Dara) | Opens the app and wants to see jobs best suited for him | Logged in; profile has skills saved; Job Listings are available | F-08, F-02 |

```gherkin
Scenario: Happy path
  Given Dara's profile skills are Flutter, Dart, Firebase
  When he opens the Recommendations tab
  Then the app displays a list of Job Listings ranked from highest to lowest Match Score
  And each card shows the job title, company, Match Score percentage, and matching skill tags

Scenario: No recommendations available (empty database)
  Given no Job Listings have been aggregated yet
  When Dara opens the Recommendations tab
  Then the app displays "No jobs available right now. Check back later."
```

---

### UJ-07 — Save a Job for Later

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-02 (Sreymom) | Finds an interesting listing but is not ready to apply now | Logged in; Job Listing is displayed | F-09 |

```gherkin
Scenario: Happy path
  Given Sreymom is viewing a Job Detail screen for a UX Designer role
  When she taps the "Save" (bookmark) icon
  Then the icon changes to a filled/active state
  And the listing is added to her Saved Jobs list

Scenario: User taps Save while offline
  Given Sreymom is browsing without an internet connection
  When she taps the "Save" icon
  Then the app shows "You are offline. Please connect to save jobs."
  And the job is not added to Saved Jobs
```

---

### UJ-08 — Filter Jobs by Category

| Persona | Trigger | Pre-conditions | Features |
|---|---|---|---|
| P-02 (Sreymom) | Wants to narrow job results to part-time marketing roles only | Logged in; Job Listings are available | F-05, F-11 |

```gherkin
Scenario: Happy path
  Given Sreymom is on the Job Feed screen
  When she opens the Filter panel and selects Job Type = "Part-time" and Job Category = "Marketing"
  And taps "Apply Filters"
  Then only Job Listings matching Part-time Marketing jobs are shown
  And the active filter tags are displayed at the top of the list

Scenario: Filter combination returns no results
  Given Sreymom filters for Full-time, Salary > 2000 USD, Marketing in Siem Reap
  When no Job Listings match all selected filters
  Then the app displays "No jobs match your filters. Try removing some filters."
  And an "Clear Filters" button is shown
```

---

## 3. Coverage

| Must-Have feature | Covered by journey(s) |
|---|---|
| F-01 — User Registration & Login | UJ-01 |
| F-02 — User Profile | UJ-02, UJ-05, UJ-06 |
| F-03 — Job Aggregation | UJ-03, UJ-04, UJ-06 |
| F-04 — Data Cleaning & Normalization | UJ-03 (results rely on clean data) |
| F-05 — Job Search & Basic Filters | UJ-03, UJ-08 |
| F-06 — Job Detail with Application Link | UJ-04 |
| F-07 — AI Job Matching (Match Score) | UJ-05, UJ-06 |
| F-08 — Personalized Job Recommendations | UJ-06 |
