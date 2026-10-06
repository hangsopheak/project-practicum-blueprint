# Phase 6.1 — Client Architecture & State

**Objective:** Plan how your client app is organised, where its data lives, and how it talks to the backend, before you connect the screens.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

## Done When

- [ ] The folder tree matches the code in your client folder, and the component hierarchy is documented
- [ ] The state management choice has a reason
- [ ] The token is kept in secure storage
- [ ] All six service layer responsibilities are done and located in code
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Client Folder Architecture

Paste your client folder tree (for example, the output of `tree -L 3` in your client folder).

```text
[STUDENT INPUT: folder tree]
```

## 2. Component Hierarchy

| Screen (SCR-xx) | Main components | Shared components used |
|---|---|---|
| [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT] |
| | | |
| | | |

## 3. State Management Strategy

Server state is data that comes from the API (e.g. a list of orders). UI state lives only in the app (e.g. whether a modal is open).

| Decision | Your choice | Why |
|---|---|---|
| State management library | [STUDENT INPUT: e.g. Provider, Riverpod, Bloc, Zustand, Redux Toolkit, React Context, Pinia] | [STUDENT INPUT] |
| How server data is fetched and cached | [STUDENT INPUT] | [STUDENT INPUT] |
| Where the login token is stored | [STUDENT INPUT: use secure storage, never plain local storage] | [STUDENT INPUT] |

## 4. API Service Layer

All API calls go through one service layer. Record where each responsibility is implemented.

| # | Responsibility | File / function | Done (Yes/No) |
|---|---|---|---|
| 1 | Reads the base URL from environment config (never hard-coded in screens) | [STUDENT INPUT] | |
| 2 | Attaches `Authorization: Bearer <token>` to protected requests | [STUDENT INPUT] | |
| 3 | Applies a request timeout | [STUDENT INPUT] | |
| 4 | Converts the `{"error": {...}}` response into one error type that screens can use | [STUDENT INPUT] | |
| 5 | On a 401 from any request except login, logs the user out and returns to the login screen | [STUDENT INPUT] | |
| 6 | Contains no secrets (anything shipped in the client can be extracted) | [STUDENT INPUT] | |

## 5. Error Handling UX

| Situation | What the user sees |
|---|---|
| No internet / timeout | [STUDENT INPUT] |
| 400 validation error | [STUDENT INPUT: e.g. message under the invalid field] |
| 401 not logged in | [STUDENT INPUT] |
| 403 / 404 | [STUDENT INPUT] |
| 500 server error | [STUDENT INPUT] |
