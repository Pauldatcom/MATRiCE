# I3 — Stream structuring

## Pipeline

Read -> validate -> normalize -> deduplicate -> output, line by line, **streamed** (the file is never fully loaded into memory).

1. **Read**: each physical line is read in order. An empty line (or whitespace-only) is **ignored** (not counted in `lus`) but the physical line number is preserved for `source_line`. Other lines are counted in `lus`.
2. **Validate + normalize** (per line, merged):
   - `id` / `title`: **non-empty strings after `trim`**; `id` is **case-sensitive**.
   - `date`: `YYYY-MM-DD` **or** `DD/MM/YYYY`, **calendar** validity checked via `datetime.date` (pure arithmetic, **no timezone**); output as `YYYY-MM-DD`.
   - `period`: `am`/`matin -> am`; `pm`/`apres-midi`/`après-midi -> pm`.
   - `group` in {`A`, `B`, `Promotion`}; `mode` in {`DG`, `CE`, `AUTO`}.
   - `domain` in {`web`, `data`, `ia`, `design`, `marketing`, `cyber`, `system`, `projet`}.
   - `teacherId`: `null`, `t1`, `t2`, or `t3`; **an empty string is invalid**.
   - `status`: `propose -> proposed`, `confirme -> confirmed` (and canonical forms).
   - Cross-constraints: `AUTO` requires `teacherId: null` **and** `status: "proposed"`; `confirmed` requires a **teacher** (`teacherId` in {`t1`,`t2`,`t3`}).
   - A **malformed JSON** or an **invalid field** triggers a **rejection** and **processing continues**: each rejection produces an entry `{ "source_line": n, "motif": "..." }` in `rejets.ndjson` with an explicit reason.
3. **Deduplication**: validation **precedes** dedup. A `set` of already-accepted `id`s is held in memory. Only the **first valid occurrence** of an identifier is kept; a later valid occurrence -> `doublons` (neither `rejets` nor `acceptes`). A **rejected** identifier does not mark the `set`: the first **valid** occurrence remains the kept one.
4. **Outputs**:
   - `acceptes.ndjson`: normalized objects, **reading order**, with `source_line`.
   - `rejets.ndjson`: one entry per rejected line, `source_line` + explicit `motif`.
   - `stats.json`: `{ "lus", "acceptes", "rejets", "doublons" }`.

## Invariant

```
lus = acceptes + rejets + doublons
```

Every non-empty line is counted in `lus` exactly once, then placed in exactly one category: `acceptes`, `rejets`, or `doublons`. The invariant is **asserted in code** (`traiter`) and **verified by tests** (`test_provided_file`, `test_empty_line...`, `test_duplicate`, `test_continuation...`).

On `seances.ndjson`: `lus=12, acceptes=6, rejets=4, doublons=2` -> `12 = 6 + 4 + 2`.

## Memory usage

- **Streamed reading**: one line in memory at a time (file iteration), no full file load.
- **Deduplication**: a `set` of **accepted** identifiers, size `O(u)` where `u` = number of **unique valid** identifiers (here `u = 6`). A set is acceptable because `u` is bounded by the actual number of sessions; the footprint grows linearly with the number of distinct sessions, not with the file size.

### Growth discussion

If the number of unique identifiers became very large (millions), this `set` could pose a memory problem. Possible approaches if needed:
- limit to recent `id`s (sliding window) if duplication order is local;
- use a **Bloom filter** (compact, ~probabilistic) if rare false-positive duplicates are acceptable;
- offload the set to disk (external table / database) for massive volume.

Within the resit scope (a few dozen sessions), an in-memory `set` remains the simplest, exact, and readable solution.

## Determinism / reproducibility

No timezone-dependent operations: dates are constructed via `datetime.date` (pure calendar, **no `tzinfo`**, **no `today()`/`now()`**). The same file therefore always produces the same result on any machine.

## Exact run command

```bash
python3 pipeline.py seances.ndjson acceptes.ndjson rejets.ndjson stats.json
# (defaults = these paths, so `python3 pipeline.py` suffices from modules/I3/)
```

Tests (non-interactive):

```bash
python3 -m unittest -v test_pipeline.py
```

## Test coverage

| Test | Covers |
|---|---|
| `test_valid_entry_normalized` | Valid entry + normalization (date, period, status) |
| `test_invalid_date` | Invalid entry (non-calendar date 2026-02-30) |
| `test_invalid_period` | Invalid entry (`soir` out of domain) |
| `test_duplicate` | Duplicate -> `doublons`, neither accepted nor rejected |
| `test_malformed_json` | Truncated JSON -> rejection "malformed JSON" |
| `test_empty_line_ignored_source_line_preserved` | Empty line ignored + physical numbering preserved |
| `test_continuation_after_bad_line` | Processing continues after an incorrect line |
| `test_provided_file` | Full `seances.ndjson` fixture + invariant |
| `test_determinism` | Two identical runs -> same result |
