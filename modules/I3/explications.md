# I3 — Structuration de flux

## Pipeline

Lecture → validation → normalisation → déduplication → sortie, ligne à ligne, en **streaming** (le fichier n'est jamais chargé en entier en mémoire).

1. **Lecture** : chaque ligne physique est lue dans l'ordre. Une ligne vide (ou ne contenant que des espaces) est **ignorée** (non comptée dans `lus`) mais le numéro de ligne physique est conservé pour `source_line`. Les autres lignes sont comptées dans `lus`.
2. **Validation + normalisation** (par ligne, fusionnées) :
   - `id` / `title` : chaînes **non vides après `trim`** ; `id` **sensible à la casse**.
   - `date` : `YYYY-MM-DD` **ou** `DD/MM/YYYY`, validité **calendaire** vérifiée via `datetime.date` (arithmétique pure, **sans fuseau horaire**) ; sortie au format `YYYY-MM-DD`.
   - `period` : `am`/`matin → am` ; `pm`/`apres-midi`/`après-midi → pm`.
   - `group` ∈ {`A`, `B`, `Promotion`} ; `mode` ∈ {`DG`, `CE`, `AUTO`}.
   - `domain` ∈ {`web`, `data`, `ia`, `design`, `marketing`, `cyber`, `system`, `projet`}.
   - `teacherId` : `null`, `t1`, `t2` ou `t3` ; **une chaîne vide est invalide**.
   - `status` : `propose → proposed`, `confirme → confirmed` (et formes canoniques).
   - Contraintes croisées : `AUTO` ⇒ `teacherId: null` **et** `status: "proposed"` ; `confirmed` ⇒ **formateur requis** (`teacherId` ∈ {`t1`,`t2`,`t3`}).
   - Un JSON **malformé** ou un **champ invalide** provoque un **rejet** et le **traitement continue** : chaque rejet produit une entrée `{ "source_line": n, "motif": "..." }` dans `rejets.ndjson` avec un motif explicite.
3. **Déduplication** : la validation **précède** la dédup. Un `set` des `id` déjà acceptés est tenu en mémoire. Seule la **première occurrence valide** d'un identifiant est retenue ; une occurrence valide ultérieure → `doublons` (ni `rejets`, ni `acceptes`). Un identifiant déjà **rejeté** ne marque pas le `set` : la première occurrence **valide** reste la retenue.
4. **Sorties** :
   - `acceptes.ndjson` : objets normalisés, **ordre de lecture**, avec `source_line`.
   - `rejets.ndjson` : une entrée par ligne rejetée, `source_line` + `motif` explicite.
   - `stats.json` : `{ "lus", "acceptes", "rejets", "doublons" }`.

## Invariant

```
lus = acceptes + rejets + doublons
```

Chaque ligne non vide est comptée dans `lus` exactement une fois, puis rangée dans exactement une catégorie : `acceptes`, `rejets` ou `doublons`. L'invariant est **asserté dans le code** (`traiter`) et **vérifié par les tests** (`test_fichier_fourni`, `test_ligne_vide…`, `test_doublon`, `test_poursuite…`).

Sur `seances.ndjson` : `lus=12, acceptes=6, rejets=4, doublons=2` → `12 = 6 + 4 + 2 ✓`.

## Mémoire utilisée

- **Lecture en streaming** : une seule ligne en mémoire à la fois (itération fichier), pas de chargement global du fichier.
- **Déduplication** : un `set` des identifiants **acceptés**, de taille `O(u)` où `u` = nombre d'identifiants **uniques valides** (ici `u = 6`). Un ensemble est acceptable car `u` reste borné par le nombre réel de séances ; l'empreinte croît linéairement avec le nombre de séances distinctes, pas avec la taille du fichier.

### Croissance discutée

Si le nombre d'identifiants uniques devenait très grand (plusieurs millions), ce `set` pourrait poser un problème mémoire. Pistes envisageables si besoin :
- limiter aux `id` récents (fenêtre glissante) si l'ordre de duplication est local ;
- utiliser un **filtre de Bloom** (compact, ~probabiliste) si on accepte de rares faux positifs de doublon ;
- déporter l'ensemble sur disque (table externe / base) pour un volume massif.

Dans le périmètre du rattrapage (quelques dizaines de séances), un `set` en mémoire reste la solution la plus simple, exacte et lisible.

## Déterminisme / reproductibilité

Aucune opération dépendante du fuseau horaire de la machine : les dates sont construites via `datetime.date` (calendrier pur, **sans `tzinfo`**, **sans `today()`/`now()`**). Le même fichier produit donc toujours le même résultat, sur n'importe quelle machine.

## Commande exacte de lancement

```bash
python3 pipeline.py seances.ndjson acceptes.ndjson rejets.ndjson stats.json
# (défauts = ces chemins, donc `python3 pipeline.py` suffit depuis modules/I3/)
```

Tests (non interactifs) :

```bash
python3 -m unittest -v test_pipeline.py
```

## Couverture des tests

| Test | Couvre |
|---|---|
| `test_entree_valide_normalisee` | entrée valide + normalisation (date, period, status) |
| `test_date_invalide` | entrée invalide (date non calendaire 2026-02-30) |
| `test_periode_invalide` | entrée invalide (`soir` hors domaine) |
| `test_doublon` | doublon → `doublons`, ni accepté ni rejeté |
| `test_json_malforme` | JSON tronqué → rejet « JSON malformé » |
| `test_ligne_vide_ignoree_mais_source_line_conservee` | ligne vide ignorée + numérotation physique conservée |
| `test_poursuite_apres_ligne_incorrecte` | poursuite du traitement après une ligne incorrecte |
| `test_fichier_fourni` | fichier `seances.ndjson` complet + invariant |
| `test_determinisme` | deux runs identiques → même résultat |