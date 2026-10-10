# MATRICE — WEB2 — Rattrapage individuel

**Auteur** : Paul COMPAGNON
**Modules** : F2 (Tests front) + I3 (Structuration de flux)

## Structure du depot

```
MATRiCE/
├── modules/
│   ├── F2/   — Tests front (React + Vitest)
│   └── I3/   — Pipeline NDJSON (Python)
├── README.md
├── JUSTIFICATIONS.md
└── SOURCES_IA.md
```

## F2 — Tests front

Tester un composant React existant (`PlanningList`) et corriger ses defauts de maniere ciblee.

### Prerequis
- Node.js >= 18
- pnpm

### Commandes
```bash
cd modules/F2
pnpm install
pnpm test          # vitest run (non interactif)
```

### Resultats attendus
- Version initiale (`PlanningList.initial.jsx`) : 3 tests rouges (resultat vide, erreur/retry, reponses desordonnees)
- Version corrigee (`PlanningList.jsx`) : 6/6 verts

### Preuves
Traces textuelles dans `modules/F2/preuves/captures/` :
- `01-tests-rouges-avant-correction.txt` — 3 echecs sur l'initial
- `02-tests-verts-apres-correction.txt` — 6/6 reussis apres correction
- `03-test-erreur-et-retry.txt` — scenario erreur/retry (rouge sur initial)
- `04-test-reponses-dans-le-desordre.txt` — scenario desordre (rouge sur initial)

## I3 — Structuration de flux

Pipeline CLI : lecture -> validation -> normalisation -> deduplication -> sortie.

### Prerequis
- Python 3 (stdlib uniquement, zero dependance)

### Commandes
```bash
cd modules/I3
python3 pipeline.py                          # genere acceptes.ndjson, rejets.ndjson, stats.json
python3 -m unittest -v test_pipeline.py      # 9 tests
```

### Resultats attendus
- `lus=12 acceptes=6 rejets=4 doublons=2` (invariant : 12 = 6 + 4 + 2)
- 9 tests unittest OK

## Workflow Git

- Branche `main` protegee (PR requise, push directs bloques)
- PRs fusionnees :
  1. `chore: structure initiale du depot`
  2. `feat(F2): tests PlanningList — rouge puis vert`
  3. `feat(I3): ndjson pipeline — validation, normalization, dedup`
  4. `docs(F2): preuves — test traces (red/green)`

## Details

- [Justifications](JUSTIFICATIONS.md) — corrections, risques couverts, limites
- [Sources IA](SOURCES_IA.md) — outils d'IA utilises
