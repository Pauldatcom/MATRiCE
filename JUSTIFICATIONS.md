# Justifications — MATRICE WEB2 Rattrapage

## F2 — Tests front

### Defauts identifiés dans le composant initial

Le composant `PlanningList.initial.jsx` presentait trois defauts :

1. **Pas de gestion d'erreur** : un rejet de `loadSessions` n'etait pas attrape.
   - `loading` restait `true` indefiniment (l'UI se figeait).
   - Aucun message d'erreur visible.
   - Aucun moyen de relancer la demande.

2. **Condition de course** : lors d'un changement rapide de groupe, la reponse
   tardive d'une demande precedente pouvait ecraser le resultat de la demande
   la plus recente (pas de garde anti-reponse-perimee).

3. **Resultat vide muet** : une reponse `[]` produisait une `<ul>` vide sans
   message explicite, laissant l'utilisateur sans feedback.

### Corrections minimales appliquees

| Defaut | Correction | Risque couvert |
|---|---|---|
| Pas de gestion d'erreur | `.catch` + etat `error` + affichage `role="alert"` + bouton « Réessayer » (relance via `attempt`) | Rejet non gere (promesse « swallowed », UI figee), impossibilite de recouvrer |
| Condition de course | `let active = true` + cleanup `() => { active = false }` dans l'`useEffect` ; `setItems`/`setLoading` seulement si `active` | Reponse tardive d'une demande obsolete qui ecrase le resultat courant |
| Resultat vide muet | Message `<p>Aucune seance pour ce groupe.</p>` quand `!loading && !error && items.length === 0` | Reponse vide confondue avec un chargement ou un resultat precedent |

### Tests (6 scenarios + accessibilite)

| Test | Scenario couvert | Rouge sur initial | Vert apres correction |
|---|---|---|---|
| Chargement | Etat de chargement perceptible (`role="status"`) | vert | vert |
| Succes | Titres affiches, chargement disparu | vert | vert |
| Filtre A + accessibilite | Bon groupe demande, A+Promotion sans B, nom accessible « Groupe », focus clavier | vert | vert |
| Resultat vide | Message explicite, ancien resultat absent | rouge | vert |
| Erreur puis retry | Erreur visible, « Réessayer » relance et retrouve | rouge | vert |
| Reponses desordonnees | La reponse tardive ne remplace pas la plus recente | rouge | vert |

### Limites de la strategie

- **jsdom ne simule pas la navigation native `<select>` au clavier** (Fleche bas/haut).
  Le test prouve le nom accessible « Groupe », l'atteinte par `Tab` et le changement
  de valeur via `selectOptions`. La navigation native par fleches reste a valider en navigateur reel.
- **Les promesses rejetees ne sont pas masquees** : le composant attrape et affiche l'erreur.
- **Pas de snapshots ni de couverture seuls** : chaque test observe le rendu (roles ARIA, textes, presence/absence).
- **Perimetre** : aucun backend, pas de base de donnees, `loadSessions` injectee en prop et doublee dans les tests.

## I3 — Structuration de flux

### Pipeline

Lecture -> validation -> normalisation -> deduplication -> sortie, ligne par ligne, en streaming.

### Invariant

```
lus = acceptes + rejets + doublons
```

Chaque ligne non vide est comptee dans `lus` exactement une fois, puis rangee dans
exactement une categorie. L'invariant est asserte dans le code et verifie par les tests.

Sur `seances.ndjson` : `lus=12, acceptes=6, rejets=4, doublons=2` -> `12 = 6 + 4 + 2`.

### Memoire

- Lecture en streaming (une ligne a la fois, fichier non charge en entier).
- Deduplication via un `set` des identifiants acceptes (O(u), u = ids uniques valides).
- Croissance discutee : pour un volume massif, alternatives envisageables (fenetre glissante,
  filtre de Bloom, table externe). Dans le perimetre du rattrapage, un `set` reste la
  solution la plus simple et exacte.

### Determinisme

Aucune operation dependante du fuseau horaire : dates via `datetime.date` (calendrier pur,
sans `tzinfo`, sans `today()`/`now()`). Le meme fichier produit le meme resultat sur
n'importe quelle machine.

### Tests (9 cas)

| Test | Couvre |
|---|---|
| `test_entree_valide_normalisee` | Entree valide + normalisation (date, period, status) |
| `test_date_invalide` | Date non calendaire (2026-02-30) |
| `test_periode_invalide` | Periode hors domaine (`soir`) |
| `test_doublon` | Doublon -> `doublons`, ni accepte ni rejete |
| `test_json_malforme` | JSON tronque -> rejet « JSON malforme » |
| `test_ligne_vide_ignoree_mais_source_line_conservee` | Ligne vide ignoree + numerotation conservee |
| `test_poursuite_apres_ligne_incorrecte` | Poursuite du traitement apres une ligne incorrecte |
| `test_fichier_fourni` | Fichier `seances.ndjson` complet + invariant |
| `test_determinisme` | Deux runs identiques -> meme resultat |
