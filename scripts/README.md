# Data Processing Scripts

This folder hosts the Python utilities we use to turn the EPUB sources into clean, graph-friendly data sets.

## `process_flavor_matrix.py`

Transforms any JSON exports placed in `docs/flavor-matrix-processed/` into tabular node/edge CSVs under `build/flavor-matrix/`. The script:

1. Accepts either a single JSON array (e.g., `flavor-matrix.json`) or a directory full of per-page JSON files.
2. Validates that each entry exposes the expected fields (`ingredient`, `best_pairings`, `matrix_nodes`, etc.) and collects warnings in a processing report.
3. Emits CSVs for ingredients, pairings, substitutes, matrix nodes, and matrix edges—ready for Cypher ingestion.

Run it from the project root:

```bash
python scripts/process_flavor_matrix.py
```

## `parse_flavor_bible.py`

Ingests every ingredient section from *The Flavor Bible* (`FlavorBible_chap-3*.html`) and writes the normalised payload to `docs/flavor-bible-processed/flavor-bible.json`. Key behaviours:

- Canonicalises ingredient headings (removes “aka…”, “see also…”, “e.g…”, converts to lowercase slugs) while keeping a human-readable `display_name`.
- Filters out non-ingredient headings and pairing noise (cuisines, soups, “as a topping…”, etc.), deduplicates pairings, and retains only the highest-strength tier when the same ingredient appears multiple times.
- Normalises metadata lists (season, taste, techniques, tips, substitutes, etc.), dropping empties so the JSON is DB-ready.

Example usage (parses the whole book in one shot):

```bash
python scripts/parse_flavor_bible.py --limit 2000
```

Full rebuild (overwrite existing JSON):

```bash
python scripts/parse_flavor_bible.py --rebuild --limit 5000
```

Output: `docs/flavor-bible-processed/flavor-bible.json`

## `parse_vegetarian_flavor_bible.py`

Performs the same extraction/normalisation pipeline for *The Vegetarian Flavor Bible* (`chapter003*.xhtml`, `chapter004*.xhtml`, and `A-Z.xhtml`). Features mirror the non-vegetarian parser:

- Canonical ingredient names + display names.
- Pairing/affinity filtering (removes cuisines, dishes, contextual phrases, “as a topping…”, etc.).
- Compact metadata/notes so the JSON contains only meaningful fields.

Run:

```bash
python scripts/parse_vegetarian_flavor_bible.py --limit 2000
```

Full rebuild (overwrite existing JSON):

```bash
python scripts/parse_vegetarian_flavor_bible.py --rebuild --limit 5000
```

Output: `docs/vegetarian-flavor-bible-processed/vegetarian-flavor-bible.json`

Both parsers are idempotent—rerunning them will skip already-seen ingredients by slug. The resulting JSON files feed directly into Cypher import scripts without any additional cleanup.

## `build_canonical_registry.py`

Builds a consolidated ingredient registry across both books with aliases and conflict reporting. The script:

1. Merges the parsed JSON from the Flavor Bible and Vegetarian Flavor Bible.
2. Extracts aliases from display names (e.g., “aka”, “see also”, parenthetical variants).
3. Outputs a canonical registry plus a conflict report to help resolve ambiguous ingredients.

Run:

```bash
python scripts/build_canonical_registry.py
```

Outputs:

- `docs/canonical-registry/ingredient_registry.json`
- `docs/canonical-registry/ingredient_registry_report.json`
