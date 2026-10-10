# AI Sources — MATRICE WEB2

## AI tools used

| Tool | Model | Usage |
|---|---|---|
| opencode | z-ai/glm-5.2 (OpenRouter) | Development assistance throughout the project |
| opencode | z-ai/glm-5.3 (OpenRouter) | Development assistance throughout the project |
| opencode | anthropic/claude-5.5 | Development assistance throughout the project |

## Nature of assistance

AI was used for:

- **Project structure**: directory layout, organization of modules F2 and I3.
- **Code implementation**: React component (`PlanningList`), Python pipeline,
  Vitest and unittest tests, configuration (Vitest, package.json).
- **Git workflow**: branch creation, pull requests, branch protection.
- **Evidence traces**: text captures of red/green test runs.

## Limitations of assistance

- The subject, data, and processing rules are provided by the assignment prompt.
- All design decisions (choice of corrections, test strategies, validation rules)
  follow directly from the subject requirements, not from the AI.
- The AI did not generate external content (no copy-paste from documentation, no
  code from other sources). All code was written from the subject requirements.
- Tests observe rendered behavior (ARIA roles, text, presence/absence), per the
  requirement "do not hide rejected promises; snapshots and coverage alone are not enough."
