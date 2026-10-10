# Sources IA — MATRICE WEB2 Rattrapage

## Outils d'IA utilises

| Outil | Modele | Usage |
|---|---|---|
| opencode | z-ai/glm-5.2 (OpenRouter) | Assistance au developpement tout au long du projet |

## Nature de l'assistance

L'IA a ete utilisee pour :

- **Structuration du projet** : arborescence des dossiers, organisation des modules F2 et I3.
- **Implementation du code** : composant React (`PlanningList`), pipeline Python,
  tests Vitest et unittest, configuration (Vitest, package.json).
- **Workflow Git** : creation de branches, pull requests, protection de branche.
- **Redaction des traces de preuve** : captures textuelles des tests rouge/vert.

## Limites de l'assistance

- Le sujet, les donnees et les regles de traitement sont fournis par l'enonce du rattrapage.
- Toutes les decisions de conception (choix des corrections, strategies de test, regles de
  validation) decoulent directement des exigences du sujet, pas de l'IA.
- L'IA n'a pas genere de contenu externe (pas de copie-colle de documentation, pas de
  code provenant d'autres sources). Tout le code a ete ecrit a partir des exigences du sujet.
- Les tests observent le comportement rendu (roles ARIA, textes, presence/absence),
  conformement a l'exigence « ne masquez pas les promesses rejetees ; snapshots et couverture
  seuls ne suffisent pas ».

## Verification humaine

L'auteur (Paul COMPAGNON) a verifie :
- Les resultats attendus des tests (F2 : 6/6 verts apres correction ; I3 : invariant 12=6+4+2).
- La coherence des normalisations (dates, periodes, statuts, groupes, modes).
- Le respect du perimetre (pas de backend, pas de base de donnees, pas d'application complete).
