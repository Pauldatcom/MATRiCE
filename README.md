# MATRICE — WEB2 — Individual resit

**Author**: Paul COMPAGNON
**Modules**: F2 (Front-end testing) + I3 (Stream structuring)

## Repository structure

```
MATRiCE/
├── modules/
│   ├── F2/   — Front-end tests (React + Vitest)
│   └── I3/   — NDJSON pipeline (Python)
├── README.md
├── JUSTIFICATIONS.md
└── SOURCES_IA.md
```

## F2 — Front-end testing

Test an existing React component (`PlanningList`) and fix its defects in a targeted manner.

### Prerequisites
- Node.js >= 18
- pnpm

### Commands
```bash
cd modules/F2
pnpm install
pnpm test          # vitest run (non-interactive)
```

### Expected results
- Initial version (`PlanningList.initial.jsx`): 3 red tests (empty result, error/retry, out-of-order responses)
- Corrected version (`PlanningList.jsx`): 6/6 green

### Evidence
Text traces in `modules/F2/preuves/captures/`:
- `01-tests-rouges-avant-correction.txt` — 3 failures on the initial version
- `02-tests-verts-apres-correction.txt` — 6/6 passing after correction
- `03-test-erreur-et-retry.txt` — error/retry scenario (red on initial)
- `04-test-reponses-dans-le-desordre.txt` — out-of-order scenario (red on initial)

## I3 — Stream structuring

CLI pipeline: read -> validate -> normalize -> deduplicate -> output.

### Prerequisites
- Python 3 (stdlib only, zero dependency)

### Commands
```bash
cd modules/I3
python3 pipeline.py                          # generates acceptes.ndjson, rejets.ndjson, stats.json
python3 -m unittest -v test_pipeline.py      # 9 tests
```

### Expected results
- `lus=12 acceptes=6 rejets=4 doublons=2` (invariant: 12 = 6 + 4 + 2)
- 9 unittest cases OK

## Git workflow

- `main` branch protected (PR required, direct pushes blocked)
- Merged PRs:
  1. `chore: structure initiale du depot`
  2. `feat(F2): tests PlanningList — rouge puis vert`
  3. `feat(I3): ndjson pipeline — validation, normalization, dedup`
  4. `docs(F2): preuves — test traces (red/green)`

## Details

- [Justifications](JUSTIFICATIONS.md) — corrections, risks covered, limitations
- [AI sources](SOURCES_IA.md) — AI tools used
