# Justifications — MATRICE WEB2

## F2 — Front-end testing

### Defects identified in the initial component

The `PlanningList.initial.jsx` component had three defects:

1. **No error handling**: a rejection from `loadSessions` was not caught.
   - `loading` stayed `true` indefinitely (UI froze).
   - No visible error message.
   - No way to retry the request.

2. **Race condition**: when switching groups quickly, a late response from a
   previous request could overwrite the result of the most recent one (no
   stale-response guard).

3. **Silent empty result**: a `[]` response produced an empty `<ul>` with no
   explicit message, leaving the user without feedback.

### Minimal corrections applied

| Defect | Correction | Risk covered |
|---|---|---|
| No error handling | `.catch` + `error` state + `role="alert"` display + "Retry" button (re-trigger via `attempt`) | Unhandled rejection (swallowed promise, frozen UI), no recovery |
| Race condition | `let active = true` + cleanup `() => { active = false }` in `useEffect`; `setItems`/`setLoading` only if `active` | Late response from an obsolete request overwriting the current result |
| Silent empty result | `<p>No sessions for this group.</p>` when `!loading && !error && items.length === 0` | Empty response confused with loading or previous result |

### Tests (6 scenarios + accessibility)

| Test | Scenario covered | Red on initial | Green after correction |
|---|---|---|---|
| Loading | Loading state perceptible (`role="status"`) | green | green |
| Success | Titles displayed, loading gone | green | green |
| Filter A + accessibility | Correct group requested, A+Promotion without B, accessible name "Group", keyboard focus | green | green |
| Empty result | Explicit message, old result absent | red | green |
| Error then retry | Visible error, "Retry" re-triggers and recovers | red | green |
| Out-of-order responses | Late response does not replace the most recent | red | green |

### Strategy limitations

- **jsdom does not simulate native `<select>` keyboard navigation** (arrow up/down).
  The test proves the accessible name "Group", reachability via `Tab` (`toHaveFocus`),
  and value change via `selectOptions`. Native arrow navigation remains to be validated
  in a real browser.
- **Rejected promises are not hidden**: the component catches and displays the error.
- **No snapshots or coverage alone**: every test observes the rendered output
  (ARIA roles, text, presence/absence).
- **Scope**: no backend, no database, no full application — `loadSessions` is injected
  as a prop and stubbed in tests via `deferred()`.

## I3 — Stream structuring

### Pipeline

Read -> validate -> normalize -> deduplicate -> output, line by line, streamed.

### Invariant

```
lus = acceptes + rejets + doublons
```

Every non-empty line is counted in `lus` exactly once, then placed in exactly one
category. The invariant is asserted in code and verified by tests.

On `seances.ndjson`: `lus=12, acceptes=6, rejets=4, doublons=2` -> `12 = 6 + 4 + 2`.

### Memory

- Streamed reading (one line at a time, file never fully loaded).
- Deduplication via a `set` of accepted ids (O(u), u = unique valid ids).
- Growth discussed: for massive volume, alternatives (sliding window, Bloom filter,
  external table). Within the assignment scope, a `set` remains the simplest exact solution.

### Determinism

No timezone-dependent operations: dates via `datetime.date` (pure calendar, no
`tzinfo`, no `today()`/`now()`). The same file produces the same result on any machine.

### Tests (9 cases)

| Test | Covers |
|---|---|
| `test_valid_entry_normalized` | Valid entry + normalization (date, period, status) |
| `test_invalid_date` | Non-calendar date (2026-02-30) |
| `test_invalid_period` | Period out of domain (`soir`) |
| `test_duplicate` | Duplicate -> `doublons`, neither accepted nor rejected |
| `test_malformed_json` | Truncated JSON -> rejection "malformed JSON" |
| `test_empty_line_ignored_source_line_preserved` | Empty line ignored + physical numbering preserved |
| `test_continuation_after_bad_line` | Processing continues after an incorrect line |
| `test_provided_file` | Full `seances.ndjson` fixture + invariant |
| `test_determinism` | Two identical runs -> same result |
