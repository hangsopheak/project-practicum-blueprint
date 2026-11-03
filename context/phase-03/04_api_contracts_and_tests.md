# Phase 3.4 — API Contracts & Test Collection

**Objective:** Specify every endpoint before you implement it, and write a test request for each one in your API testing tool. The tests fail now and turn green during Phase 5.

**Status:** Submitted · **Last updated:** 2026-10-18

## Done When

- [x] Every endpoint has an ID (EP-01, EP-02, …) and a contract card (Section 3)
- [x] Every Must-Have journey step is covered by an endpoint
- [x] The test collection in `api-specs/` has one request per endpoint, named with its EP-ID

## 1. Conventions (all projects)

- Local base URL `http://localhost:8000`; every route starts with `/api/v1`.
- Request and response bodies are JSON.
- Protected routes need the header `Authorization: Bearer <token>`.
- Standard error response format:
  ```json
  {
    "error": {
      "code": "NOT_FOUND",
      "message": "Readable error description",
      "details": []
    }
  }
  ```
- Standard HTTP status codes: `200 OK`, `201 Created`, `400 Validation Error`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Server Error`.

## 2. API Specification Table

| ID | Method | Endpoint | Description | Auth required | Feature |
|---|---|---|---|---|---|
| EP-01 | GET | /api/v1/health | Service health check | No | n/a |
| EP-02 | POST | /api/v1/auth/register | Register a new user account | No | F-01 |
| EP-03 | POST | /api/v1/auth/login | Authenticate user and receive JWT token | No | F-01 |
| EP-04 | GET | /api/v1/profile | Retrieve current user profile and skills | Yes | F-02 |
| EP-05 | PUT | /api/v1/profile | Update candidate profile, experience, and skill tags | Yes | F-02, F-07 |
| EP-06 | GET | /api/v1/skills | Get master list of normalized skill tags for chip selection | No | F-02 |
| EP-07 | GET | /api/v1/jobs | Search and filter aggregated jobs by keyword, category, location | No | F-05 |
| EP-08 | GET | /api/v1/jobs/{id} | Get detailed job view with full requirements and external apply link | No | F-06 |
| EP-09 | GET | /api/v1/recommendations | AI matching: get personalized job feed ranked by Match Score % | Yes | F-07, F-08 |
| EP-10 | GET | /api/v1/saved-jobs | Get list of bookmarked job listings | Yes | F-09 |
| EP-11 | POST | /api/v1/saved-jobs/{job_id} | Bookmark a job listing for future review | Yes | F-09 |
| EP-12 | DELETE | /api/v1/saved-jobs/{job_id} | Remove a bookmark | Yes | F-09 |
| EP-13 | POST | /api/v1/admin/scrape | Trigger background ingestion of target sources | Yes (Admin) | F-03, F-04 |
| EP-14 | POST | /api/v1/auth/otp/send | Generate and send 6-digit OTP code to email | No | F-01 |
| EP-15 | POST | /api/v1/auth/otp/verify | Verify 6-digit OTP code and issue JWT session | No | F-01 |
| EP-16 | GET | /api/v1/sources | List all supported Cambodian recruitment job sources | No | F-03, F-04 |
| EP-17 | GET | /api/v1/sources/{id} | Get detail of a specific recruitment source | No | F-03, F-04 |

## 3. Endpoint Contract Cards

---

### EP-02 — POST /api/v1/auth/register
Registers a new candidate account.

Request body:
```json
{
  "email": "dara@example.com",
  "password": "Password123!"
}
```

Success response, 201 Created:
```json
{
  "user_id": 1,
  "email": "dara@example.com",
  "role": "user",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

| Error | When it happens |
|---|---|
| 400 VALIDATION_ERROR | Email is invalid or password is shorter than 8 characters |
| 409 CONFLICT | Email is already registered in the system |

---

### EP-03 — POST /api/v1/auth/login
Authenticates a user and returns a Bearer JWT token.

Request body:
```json
{
  "email": "dara@example.com",
  "password": "Password123!"
}
```

Success response, 200 OK:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "dara@example.com",
    "role": "user"
  }
}
```

| Error | When it happens |
|---|---|
| 400 VALIDATION_ERROR | Missing email or password fields |
| 401 UNAUTHORIZED | Incorrect email or password |

---

### EP-04 — GET /api/v1/profile
Retrieves the logged-in user's profile and skills.

Request body: `none`

Success response, 200 OK:
```json
{
  "id": 1,
  "user_id": 1,
  "full_name": "Dara Sok",
  "education": "Bachelor of Computer Science",
  "experience_level": "entry",
  "preferred_role": "Mobile Developer",
  "preferred_location": "Phnom Penh",
  "expected_salary": 800.00,
  "skills": [
    {"id": 10, "name": "Flutter", "category": "Mobile"},
    {"id": 11, "name": "Dart", "category": "Mobile"},
    {"id": 12, "name": "Firebase", "category": "Database"}
  ]
}
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Bearer token is missing or expired |
| 404 NOT_FOUND | Profile has not been created yet |

---

### EP-05 — PUT /api/v1/profile
Updates candidate information and selected skill chips.

Request body:
```json
{
  "full_name": "Dara Sok",
  "education": "Bachelor of Computer Science",
  "experience_level": "entry",
  "preferred_role": "Mobile Developer",
  "preferred_location": "Phnom Penh",
  "expected_salary": 900.00,
  "skill_ids": [10, 11, 12]
}
```

Success response, 200 OK:
```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "profile_id": 1
}
```

| Error | When it happens |
|---|---|
| 400 VALIDATION_ERROR | Empty full_name or invalid experience_level |
| 401 UNAUTHORIZED | Missing or invalid authentication token |

---

### EP-06 — GET /api/v1/skills
Retrieves the master taxonomy of skills for the mobile chip selection UI.

Request body: `none`

Success response, 200 OK:
```json
[
  {"id": 10, "name": "Flutter", "category": "Mobile"},
  {"id": 11, "name": "Dart", "category": "Mobile"},
  {"id": 12, "name": "Firebase", "category": "Database"},
  {"id": 13, "name": "Git", "category": "Tools"},
  {"id": 20, "name": "Python", "category": "Backend"},
  {"id": 21, "name": "FastAPI", "category": "Backend"}
]
```

| Error | When it happens |
|---|---|
| 500 SERVER_ERROR | Database connection issue |

---

### EP-07 — GET /api/v1/jobs
Searches and filters active aggregated vacancies. Automatically excludes duplicate listings (`duplicate_of IS NULL`).

Query Parameters: `?q=Flutter&location=Phnom+Penh&job_type=internship&since=2026-10-24T12:00:00Z&page=1&limit=20`

Request body: `none`

Success response, 200 OK:
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "id": 101,
      "title": "Junior Flutter Developer",
      "company": "ABA Bank",
      "location": "Phnom Penh",
      "job_type": "internship",
      "salary_min": 700.00,
      "salary_max": 1000.00,
      "salary_currency": "USD",
      "source": "Telegram",
      "posted_at": "2026-10-15"
    }
  ]
}
```

| Error | When it happens |
|---|---|
| 400 VALIDATION_ERROR | Invalid pagination parameter (e.g. page < 1) |

---

### EP-08 — GET /api/v1/jobs/{id}
Retrieves detailed job description and external application link.

Request body: `none`

Success response, 200 OK:
```json
{
  "id": 101,
  "title": "Junior Flutter Developer",
  "company": "ABA Bank",
  "location": "Phnom Penh",
  "job_type": "internship",
  "salary_min": 700.00,
  "salary_max": 1000.00,
  "salary_currency": "USD",
  "is_negotiable": false,
  "description": "We are seeking a motivated Flutter intern to build mobile features...",
  "source": "Telegram",
  "source_url": "https://t.me/internshipscambodia/515",
  "posted_at": "2026-10-15",
  "required_skills": [
    {"id": 10, "name": "Flutter"},
    {"id": 11, "name": "Dart"},
    {"id": 12, "name": "Firebase"},
    {"id": 13, "name": "Git"}
  ]
}
```

| Error | When it happens |
|---|---|
| 404 NOT_FOUND | Job listing with given id does not exist |

---

### EP-09 — GET /api/v1/recommendations
AI matching engine returns job listings ranked by match score percentage for the logged-in candidate.

Request body: `none`

Success response, 200 OK:
```json
[
  {
    "job_id": 101,
    "title": "Junior Flutter Developer",
    "company": "ABA Bank",
    "location": "Phnom Penh",
    "job_type": "internship",
    "salary_min": 700.00,
    "salary_max": 1000.00,
    "source": "Telegram",
    "match_score": 75.0,
    "matched_skills": ["Flutter", "Dart", "Firebase"],
    "missing_skills": ["Git"],
    "source_url": "https://t.me/internshipscambodia/515"
  }
]
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Bearer token is missing or expired |
| 400 VALIDATION_ERROR | User profile has no skills selected yet (returns prompt to add skills) |

---

### EP-10 — GET /api/v1/saved-jobs
Retrieves bookmarked jobs for the current user.

Request body: `none`

Success response, 200 OK:
```json
[
  {
    "saved_at": "2026-10-16T12:00:00Z",
    "job": {
      "id": 101,
      "title": "Junior Flutter Developer",
      "company": "ABA Bank",
      "salary_min": 700.00,
      "source": "Telegram"
    }
  }
]
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Missing authentication token |

---

### EP-11 — POST /api/v1/saved-jobs/{job_id}
Bookmarks a job listing.

Request body: `none`

Success response, 201 Created:
```json
{
  "status": "success",
  "message": "Job bookmarked successfully",
  "job_id": 101
}
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Missing authentication token |
| 404 NOT_FOUND | Job listing does not exist |
| 409 CONFLICT | Job is already in saved list |

---

### EP-12 — DELETE /api/v1/saved-jobs/{job_id}
Removes a bookmark.

Request body: `none`

Success response, 200 OK:
```json
{
  "status": "success",
  "message": "Bookmark removed"
}
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Missing authentication token |
| 404 NOT_FOUND | Bookmark not found |

---

### EP-13 — POST /api/v1/admin/scrape
Admin-only endpoint to trigger a scraping cycle on target sources.

Request body:
```json
{
  "source": "all"
}
```

Success response, 200 OK:
```json
{
  "status": "completed",
  "new_jobs_added": 15,
  "duplicates_skipped": 3,
  "timestamp": "2026-10-18T08:00:00Z"
}
```

| Error | When it happens |
|---|---|
| 401 UNAUTHORIZED | Not logged in |
| 403 FORBIDDEN | User does not have 'admin' role |

---

### EP-14 — POST /api/v1/auth/otp/send
Generates a 6-digit verification code and dispatches it to the candidate's email.

Request body:
```json
{
  "email": "dara@example.com",
  "purpose": "login_or_verify"
}
```

Success response, 200 OK:
```json
{
  "message": "OTP verification code sent to your email",
  "email": "dara@example.com",
  "expires_in_seconds": 600
}
```

| Error | When it happens |
|---|---|
| 422 VALIDATION ERROR | Invalid email address format |

---

### EP-15 — POST /api/v1/auth/otp/verify
Verifies the 6-digit code. If valid, issues a Bearer JWT access token.

Request body:
```json
{
  "email": "dara@example.com",
  "code": "123456",
  "purpose": "login_or_verify"
}
```

Success response, 200 OK:
```json
{
  "message": "OTP verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "dara@example.com",
    "role": "user"
  }
}
```

| Error | When it happens |
|---|---|
| 400 BAD REQUEST | Incorrect, expired, or already-used OTP code |

---

### EP-16 — GET /api/v1/sources
Lists all supported Cambodian recruitment job sources (Telegram channels and Web portals) with platform metadata.

Query parameters:
- `platform_type` (optional string): Filter by platform type (`telegram`, `web_portal`)
- `is_active` (optional boolean): Filter active/inactive sources

Response body (200 OK):
```json
[
  {
    "id": 1,
    "name": "Internships Cambodia",
    "code": "internships_cambodia",
    "platform_type": "telegram",
    "url": "https://t.me/internshipscambodia",
    "logo_url": "assets/icons/telegram.png",
    "is_active": true,
    "scrape_interval_minutes": 60,
    "last_scraped_at": null,
    "created_at": "2026-11-02T04:05:03.028630Z",
    "updated_at": "2026-11-02T04:05:03.028630Z"
  }
]
```

---

### EP-17 — GET /api/v1/sources/{id}
Retrieves details of a specific recruitment source by ID.

Response body (200 OK):
```json
{
  "id": 1,
  "name": "Internships Cambodia",
  "code": "internships_cambodia",
  "platform_type": "telegram",
  "url": "https://t.me/internshipscambodia",
  "logo_url": "assets/icons/telegram.png",
  "is_active": true,
  "scrape_interval_minutes": 60,
  "last_scraped_at": null,
  "created_at": "2026-11-02T04:05:03.028630Z",
  "updated_at": "2026-11-02T04:05:03.028630Z"
}
```

| Error | When it happens |
|---|---|
| 404 NOT FOUND | No source exists with the given ID |

---

## 4. Test Collection

The API test collection is exported as a standard Postman/Bruno collection located at:
`api-specs/jobmatch_api_collection.json`

| ID | Request name in collection | Assertions |
|---|---|---|
| EP-01 | EP-01 Health Check | status 200; `status` equals `"ok"` |
| EP-02 | EP-02 Register User | status 201; `user_id` is present; `token` is string |
| EP-03 | EP-03 Login User | status 200; `access_token` is present; `token_type` is `"bearer"` |
| EP-04 | EP-04 Get User Profile | status 200; `user_id` matches token; `skills` is array |
| EP-05 | EP-05 Update User Profile | status 200; `status` equals `"success"` |
| EP-06 | EP-06 Get Skills Master List | status 200; response is array; array length > 0 |
| EP-07 | EP-07 Search Job Listings | status 200; `items` is array; `total` is number |
| EP-08 | EP-08 Get Job Detail | status 200; `title` is string; `source_url` starts with `"http"` |
| EP-09 | EP-09 Get AI Recommendations | status 200; response is array; `match_score` is number >= 0 and <= 100 |
| EP-10 | EP-10 Get Saved Jobs | status 200; response is array |
| EP-11 | EP-11 Bookmark Job | status 201; `status` equals `"success"` |
| EP-12 | EP-12 Remove Bookmark | status 200; `status` equals `"success"` |
| EP-13 | EP-13 Admin Trigger Scrape | status 200; `new_jobs_added` is number |
| EP-14 | EP-14 Send Email OTP | status 200; `message` is string; `email` matches |
| EP-15 | EP-15 Verify Email OTP | status 200; `access_token` is present; `token_type` is `"bearer"` |
| EP-16 | EP-16 List Recruitment Sources | status 200; response is array; length >= 10 |
| EP-17 | EP-17 Get Source Detail | status 200; `code` is string; `platform_type` is string |
