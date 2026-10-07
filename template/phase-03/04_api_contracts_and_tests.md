# Phase 3.4 — API Contracts & Test Collection

**Objective:** Specify every endpoint before you implement it, and write a test request for each one in your API testing tool. The tests fail now and turn green during Phase 5.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] Every endpoint has an ID (EP-01, EP-02, …) and a contract card (Section 3)
- [ ] Every Must-Have journey step is covered by an endpoint
- [ ] The test collection in `api-specs/` has one request per endpoint, named with its EP-ID
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Conventions (all projects)

- Local base URL `http://localhost:8000`; every route starts with `/api/v1`.
- Request and response bodies are JSON.
- Protected routes need the header `Authorization: Bearer <token>`.
- Every error response uses one shape: `{"error": {"code": "NOT_FOUND", "message": "Readable text", "details": []}}`
- Status codes: 200 OK, 201 Created, 400 Validation error, 401 Not logged in, 403 Not allowed, 404 Not found, 409 Conflict, 500 Server error.

## 2. API Specification Table

| ID | Method | Endpoint | Description | Auth required | Feature |
|---|---|---|---|---|---|
| EP-01 | GET | /api/v1/health | Returns `{"status":"ok","timestamp":"..."}` | No | n/a |
| EP-02 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT: Yes / No] | [STUDENT INPUT: F-xx] |
| EP-03 | | | | | |
| EP-04 | | | | | |

## 3. Endpoint Contract Cards

Copy this card once for each endpoint except EP-01.

### [STUDENT INPUT: EP-xx — METHOD /api/v1/path]

Request body (write "none" for GET/DELETE):

```json
[STUDENT INPUT: example request JSON]
```

Success response, [STUDENT INPUT: 200 or 201]:

```json
[STUDENT INPUT: example response JSON]
```

| Error | When it happens |
|---|---|
| 400 VALIDATION_ERROR | [STUDENT INPUT: which fields, which rules] |
| 401 UNAUTHORIZED | [STUDENT INPUT: or "n/a" for public endpoints] |
| 403 FORBIDDEN | [STUDENT INPUT: e.g. the record belongs to another user, or "n/a"] |
| 404 NOT_FOUND | [STUDENT INPUT: or "n/a"] |

## 4. Test Collection

Use the API testing tool you chose in Phase 3.1 (e.g. Bruno, Postman or Insomnia) and keep the collection in `api-specs/`, committed to Git. For tools that store collections in the cloud (e.g. Postman), export the collection as JSON into `api-specs/` after every change.

Rules:

- One request per endpoint, named with its EP-ID (e.g. `EP-02 Register`).
- Use a variable for the base URL (`http://localhost:8000`), never a hard-coded host.
- Every request checks the status code and at least one field in the response body.
- Never save real passwords or tokens in the collection.

| ID | Request name in collection | Assertions |
|---|---|---|
| EP-01 | [STUDENT INPUT] | status 200; `status` equals `"ok"` |
| EP-02 | [STUDENT INPUT] | [STUDENT INPUT] |
| | | |
