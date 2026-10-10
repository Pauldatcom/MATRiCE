# MATRICE — WEB2

**Author**: Paul COMPAGNON
**Modules**: F2 + I3

## Repository structure

```
MATRiCE/
├── modules/
│   ├── F2/   
│   └── I3/
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
pnpm test          
```
### Evidence
Screenshots in `modules/F2/preuves/captures/`:
- `01-tests-rouges-avant-correction.png` 
- `02-tests-verts-apres-correction.png`
- `03-test-erreur-et-retry.png` 
- `04-test-reponses-dans-le-desordre.png`

## I3 — Stream structuring

CLI pipeline: read -> validate -> normalize -> deduplicate -> output.

### Prerequisites
- Python 3 (stdlib only, zero dependency)

### Commands
```bash
cd modules/I3
python3 pipeline.py                          
python3 -m unittest -v test_pipeline.py     
```
## Details

- [Justifications](JUSTIFICATIONS.md) — corrections, risks covered, limitations
- [AI sources](SOURCES_IA.md) — AI tools used
