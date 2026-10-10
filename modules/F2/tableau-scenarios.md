# Scenario table — F2 (PlanningList)

| Scenario | Input | Expected | Risk covered |
|---|---|---|---|
| Loading | Render, `loadSessions` returns a pending promise | `role="status"` "Loading..." visible | No perceived state during wait (frozen/silent UI) |
| Success | Resolve with 6 sessions | Titles displayed in a list, loading gone | Received data not displayed / loading never ends |
| Filter A (+ accessibility) | Reach `<select>` via keyboard (Tab) then select "Group A" | `loadSessions({ group: 'A' })` called; A + Promotion titles shown; B titles absent; `combobox` with accessible name "Group" | Wrong group requested / B sessions leaking / filter unusable via keyboard / accessible name missing |
| Empty result | Resolve with `[]` | Explicit message "No sessions...", old result absent | Empty response confused with loading or previous result |
| Error then retry | Promise rejected | `role="alert"` visible + "Retry" button; on click, `loadSessions({ group })` re-triggered and results recovered | Unhandled rejection (swallowed promise, frozen UI), no recovery |
| Out-of-order responses | Two successive requests (`all` then `A`), resolved in reverse order | Render keeps the result of the most recent request (A), not the first | Race condition: late response from an obsolete request overwriting the current result |

## Corrections applied (scenario -> correction)

- **Empty result**: added `<p>No sessions for this group.</p>` when `!loading && !error && items.length === 0`. Before, a `[]` response left an empty `<ul>` with no signal.
- **Error then retry**: added `error` state + `.catch` on the promise, `role="alert"` display, and "Retry" button that increments an `attempt` counter (`useEffect` dependency) to re-trigger the same request. Before, a rejection went unhandled (swallowed promise, `loading` stuck at `true`).
- **Out-of-order responses**: added `let active = true` + `return () => { active = false; }` in `useEffect`; `setItems`/`setLoading` only apply if the handler is still active. Before, a late response from a previous group overwrote the current result.

## Strategy limitations

- **jsdom does not simulate native `<select>` keyboard navigation** (arrow up/down). We prove the accessible name "Group" (`getByRole('combobox', { name: 'Group' })`), reachability via `Tab` (`toHaveFocus`), and value change via `selectOptions`. Native arrow navigation remains to be validated in a real browser.
- **Rejected promises are not hidden**: the component catches and displays the error (`role="alert"`); tests trigger a real rejection via `deferred().reject(new Error(...))`.
- **No snapshots or coverage alone**: every test observes the rendered output (ARIA roles, text, presence/absence), not just structure or coverage %.
- **Scope**: no backend, no database, no full application — `loadSessions` is injected as a prop and stubbed in tests via `deferred()`.
