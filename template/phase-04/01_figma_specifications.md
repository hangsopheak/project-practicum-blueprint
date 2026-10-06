# Phase 4.1 — Figma Specifications

**Objective:** Design every screen before you build it: a small design system, your screens and a clickable prototype of your core journeys.

**Status:** In Progress / Submitted · **Last updated:** [STUDENT INPUT: YYYY-MM-DD]

| Item | Value |
|---|---|
| Figma view-only project URL | [STUDENT INPUT] |
| Figma interactive prototype URL | [STUDENT INPUT] |
| Target frame resolution | [STUDENT INPUT: e.g. Mobile 393×852 (iPhone 15) or Web 1440×1024] |

Set both links to "Anyone with the link can view" and test them in a private browser window.

## Done When

- [ ] Both Figma links open in a private browser window
- [ ] The Figma file has a style guide, your screens and a clickable prototype
- [ ] Every screen has an ID (SCR-01, SCR-02, …) and a Figma frame with the same name
- [ ] Every journey step from Phase 2.2 has a screen
- [ ] 6–10 key screens are exported as PNG into `context/assets/figma/` and display in this file on GitHub
- [ ] No fill-in markers left (the placeholder check prints nothing)

## 1. Your Figma File

Organise the pages however you like. Make sure the file has a style guide (colors, fonts, components), your screens, and a clickable prototype of your core journeys.

## 2. Design System Tokens

**Color palette.** Text must have a contrast ratio of at least 4.5:1 against its background.

| Token | Hex | Used for |
|---|---|---|
| Primary | [STUDENT INPUT] | [STUDENT INPUT] |
| Secondary | [STUDENT INPUT] | [STUDENT INPUT] |
| Background | [STUDENT INPUT] | [STUDENT INPUT] |
| Surface | [STUDENT INPUT] | [STUDENT INPUT] |
| Success | [STUDENT INPUT] | [STUDENT INPUT] |
| Warning | [STUDENT INPUT] | [STUDENT INPUT] |
| Error | [STUDENT INPUT] | [STUDENT INPUT] |

**Fonts**

| Use | Font, size and weight |
|---|---|
| Headings | [STUDENT INPUT: e.g. Inter 24 px bold] |
| Body text | [STUDENT INPUT] |
| Small text | [STUDENT INPUT] |

**Component inventory**

| Component | Variants and states | Done (Yes/No) |
|---|---|---|
| Buttons | [STUDENT INPUT: e.g. primary, secondary; default, pressed, disabled, loading] | |
| Text inputs | [STUDENT INPUT: e.g. default, focused, error, disabled] | |
| Dropdowns | [STUDENT INPUT] | |
| Cards | [STUDENT INPUT] | |
| Bottom navigation | [STUDENT INPUT] | |
| Loading, empty and error states | [STUDENT INPUT: e.g. spinner, "No requests yet" message with a button, error message with Retry] | |

## 3. Screen-by-Screen Catalog

| Screen ID | Screen name | Purpose | Figma frame | User journey | Endpoint |
|---|---|---|---|---|---|
| SCR-01 | [STUDENT INPUT] | [STUDENT INPUT] | [STUDENT INPUT: e.g. "SCR-01 / Login"] | [STUDENT INPUT: UJ-xx] | [STUDENT INPUT: EP-xx or none] |
| SCR-02 | | | | | |
| SCR-03 | | | | | |

## 4. Offline Asset Archive

Figma links can break or lose permissions, so keep a copy of your key screens in Git:

1. Export 6–10 key screens as PNG at 2x.
2. Save them in `context/assets/figma/`, named `SCR-01_login.png`, `SCR-02_home.png`, and so on.
3. Embed each one below with this syntax (the path is relative to this file):

```text
![SCR-01 Login](../assets/figma/SCR-01_login.png)
```

> [STUDENT INPUT: Embed 6–10 exported screens here, one per line.]
