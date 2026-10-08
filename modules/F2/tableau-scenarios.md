# Tableau des scénarios — F2 (PlanningList)

| Scénario | Entrée | Attendu | Risque couvert |
|---|---|---|---|
| Chargement | Rendu, `loadSessions` renvoie une promesse en attente | `role="status"` « Chargement… » visible | Aucun état perçu pendant l'attente (UI figée/silencieuse) |
| Succès | Résolution avec les 6 séances | Titres affichés dans une liste, chargement disparu | Données reçues non affichées / chargement qui ne finit pas |
| Filtre A (+ accessibilité) | Atteinte du `<select>` au clavier (Tab) puis sélection de « Groupe A » | `loadSessions({ group: 'A' })` appelé ; titres A + Promotion affichés ; titres B absents ; `combobox` de nom accessible « Groupe » | Mauvais groupe demandé / fuite de séances B / filtre inutilisable au clavier / nom accessible absent |
| Résultat vide | Résolution avec `[]` | Message explicite « Aucune séance… », ancien résultat absent | Réponse vide confondue avec un chargement ou avec le résultat précédent |
| Erreur puis nouvelle tentative | Rejet de la promesse | `role="alert"` visible + bouton « Réessayer » ; au clic, `loadSessions({ group })` relancé et les résultats reviennent | Rejet non géré (promesse « swallowed », UI figée), impossible de recouvrer |
| Réponses désordonnées | Deux demandes successives (`all` puis `A`), résolution dans l'ordre inverse | Le rendu conserve le résultat de la demande la plus récente (A), pas celui de la première | Effet de course : réponse tardive d'une demande obsolète qui écrase le résultat courant |

## Corrections apportées (lien scénario → correction)

- **Résultat vide** : ajout d'un message `<p>Aucune séance pour ce groupe.</p>` quand `!loading && !error && items.length === 0`. Avant, une réponse `[]` laissait une `<ul>` vide sans signal.
- **Erreur puis nouvelle tentative** : ajout d'un état `error` + `.catch` sur la promesse, affichage `role="alert"`, et bouton « Réessayer » qui incrémente un compteur `attempt` (dépendance de l'`useEffect`) pour relancer la même demande. Avant, un rejet restait non traité (promesse avaleuse d'erreur, `loading` figé à `true`).
- **Réponses désordonnées** : ajout d'un garde `let active = true` + `return () => { active = false; }` dans l'`useEffect` ; `setItems`/`setLoading` ne s'appliquent que si le gestionnaire est encore actif. Avant, une réponse tardite d'un groupe précédent écrasait le résultat courant.

## Limites de la stratégie

- **jsdom ne simule pas la navigation native `<select>` au clavier** (Flèche bas / haut). On prouve le nom accessible « Groupe » (`getByRole('combobox', { name: 'Groupe' })`), l'atteinte par `Tab` (`toHaveFocus`) et le changement de valeur via `selectOptions`. La navigation native par flèches reste à valider dans un navigateur réel.
- **Les promesses rejetées ne sont pas masquées** : le composant attrape l'erreur et l'affiche (`role="alert"`) ; les tests déclenchent un vrai rejet via `deferred().reject(new Error(...))`.
- **Pas de snapshots ni de couverture seuls** : chaque test observe le rendu (rôles ARIA, textes, présence/absence), pas uniquement la structure ou le % de couverture.
- **Périmètre** : aucun backend, aucune base de données, pas d'application complète — `loadSessions` est injectée en prop et doublée dans les tests via `deferred()`.