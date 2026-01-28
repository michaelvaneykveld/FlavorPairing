# Flavor Pairing Project – Working Log & Roadmap

This document captures the project history, current state, and forward-looking plan so we can jump back in without losing momentum—no matter how many sessions we string together.

---

## Where We Started

### Initial Vision
- Build a reusable ingestion pipeline that converts flavor reference books (EPUBs) into structured, graph-friendly datasets.
- Target multiple sources:
  - *The Flavor Bible* (Karen Page & Andrew Dornenburg)
  - *The Vegetarian Flavor Bible* (Karen Page)
  - *The Flavor Matrix* (James Briscione & Brooke Parkhurst)
- Avoid manual data entry; aim for automation with scripts and parsers.
- Ultimately ingest the cleansed data into Neo4j (or similar) to explore ingredient relationships, flavor affinities, and supporting metadata.

### Early Context
- EPUBs were placed in `docs/`, with raw ZIP-like EPUB bundles plus extracted XHTML/asset directories.
- No ingestion scripts existed; all book data was untouched.
- Goal was to create canonical nodes/relationships (ingredients, pairings, affinities, techniques, seasonality, etc.) that map cleanly into a graph schema.
- Secondary needs included a cross-platform dev environment: WordPress ingestion prototype (for WP+Neo4j talk), local Docker stack for WP/Neo4j on Windows.

### Required Outcomes
- Create tooling to parse EPUB structures and produce normalized JSON.
- Document everything thoroughly (playbooks, README updates, environment setup).
- Keep private data (full EPUB bundles) out of Git while publishing computed outputs.

---

## Achievements To Date

### Environment & Tooling
1. **Dockerized WP/Neo4j setup (WSL-friendly)**
   - `infra/docker/docker-compose.yml` orchestrates WordPress (PHP FPM), MariaDB, Caddy, and Neo4j.
   - `infra/docker/README.md` & `docs/windows-stack-setup.md` document the Windows + WSL workflow (install WSL2, Docker Engine, run `docker compose up`, finish WP bootstrap, log into Neo4j Browser).
   - `.gitignore` now tracks `docs/` while excluding `docs/raw/` & `docs/extracted/` to keep EPUB bundles private but allow processed data to exist in the repo.

2. **Flavor Matrix structure mapping**
   - `docs/flavor-matrix-image-map.md` lists every XHTML page and its corresponding high-resolution wheel image (useful when running GPT-5 Vision on the Flavor Matrix charts).
   - `scripts/process_flavor_matrix.py` reads the GPT-extracted JSON and emits ingredient, pairing, substitute, and matrix-edge CSVs. Generates a `build/flavor-matrix/` structure plus a processing report.

### XHTML-to-JSON Parsers
1. **`parse_flavor_bible.py`**
   - Searches every `FlavorBible_chap-3*.html`.
   - For each ingredient:
     * Canonicalises the heading (`"ALMONDS (and UNSWEETENED ALMOND BUTTER; see also MILK, ALMOND)"` → `ingredient: almonds`, `display_name: ALMONDS (and …)`).
     * Filters out non-ingredient headings (cuisines, technique sidebars, seasonal chapters).
     * Cleans pairings (drops cuisines, soups, “as a topping…”, context-only phrases) and picks the strongest tier when duplicates appear.
     * Normalises metadata (season, taste, weight/volume, techniques, tips, substitutes) and removes empties.
     * Keeps `flavor_affinities`, `notes` only when present, deduplicated & trimmed.
   - Output: `docs/flavor-bible-processed/flavor-bible.json` (509 canonical ingredients after cleanup pass).

2. **`parse_vegetarian_flavor_bible.py`**
   - Performs the same process across `chapter003*.xhtml`, `chapter004*.xhtml`, and `A-Z.xhtml`.
   - Handles the more complex markup (nested divs with `recipe-title`, `headnote`, `ingredients` sections, etc.).
   - Output: `docs/vegetarian-flavor-bible-processed/vegetarian-flavor-bible.json` (652 canonical ingredients after cleanup pass).

3. **Shared Functionality**
   - Both scripts include:
     * `canonicalize_name()` to derive canonical names & alias display names.
     * Pairing stopword filtering (cuisines, soups, desserts, “trail mix”, etc.).
     * Tier priority map (`ethereal` > `classic` > `frequent` > `recommended`).
     * Metadata compaction (drop null/empty arrays).
     * Rerun safety: skip ingredients already present (idempotent).
    - Recent upgrades:
       * `--rebuild` flag to regenerate outputs from scratch.
       * Better pairing splitting (`and`, `or`, `&`, `/`) while respecting parentheses.
       * Expanded heading skip lists to avoid non-ingredient sections (techniques, holidays, dish headings).
       * Heading compound splitting to split merged headings and shared-base lists (e.g., “orange juice”, “orange zest”).

4. **Processed Outputs (committed)**
   - `docs/flavor-bible-processed/flavor-bible.json`
   - `docs/vegetarian-flavor-bible-processed/vegetarian-flavor-bible.json`
   - Both files are graph-ready: `ingredient` (canonical slug), `display_name`, `metadata`, `pairings`, `flavor_affinities`, `notes`.
   - Pairings include both canonical ingredient references and original display text for clarity.

### Documentation Enhancements
1. `scripts/README.md` now documents each script:
   - `process_flavor_matrix.py` (matrix CSV generator).
   - `parse_flavor_bible.py`.
   - `parse_vegetarian_flavor_bible.py`.
   - Includes usage examples (`python scripts/parse_flavor_bible.py --limit 2000`, etc.) and rebuild commands.

2. `scripts/build_canonical_registry.py` added:
   - Builds a cross-book canonical ingredient registry with aliases and conflict reporting.
   - Outputs: `docs/canonical-registry/ingredient_registry.json` and `ingredient_registry_report.json`.

2. Additional docs:
   - `docs/windows-stack-setup.md` → WSL/docker instructions.
   - `docs/structure-notes.md` → EPUB structural analysis (markup patterns, metadata cues).
   - `docs/graph-taxonomy.md` → node/edge schema and ingestion plan.
   - `docs/graph-database-design.md` → early brainstorming.
   - `docs/epub-ingestion-roadmap.md` → original ingestion checklist.

3. `TODO.md` (this file) created to carry forward context into future sessions.

4. `.gitignore` reworked to allow processed docs and scripts in Git while keeping raw EPUB archives private.

### Version Control Status
- Commits pushed to `origin/main` (repo: `github.com/michaelvaneykveld/FlavorPairing`).
- Latest commit: **“Add EPUB parsers and processed datasets”** — includes updated scripts, README, Docker config, and processed JSON outputs.
- `docs/raw/` and `docs/extracted/` remain excluded; everything else is versioned.

---

## Current State Snapshot

### Data Assets
| Dataset | File | Notes |
| --- | --- | --- |
| Flavor Bible | `docs/flavor-bible-processed/flavor-bible.json` | 509 canonical ingredients after cleanup pass. |
| Vegetarian Flavor Bible | `docs/vegetarian-flavor-bible-processed/vegetarian-flavor-bible.json` | 652 canonical ingredients after cleanup pass. |
| Flavor Matrix | `docs/flavor-matrix-processed/flavor_matrix.json`, `flavor_matrix_fixed.json` | “Fixed” JSON from GPT runs; awaiting CSV conversion if needed. |
| Structure Notes | `docs/structure-notes.md` | Field-by-field markup analysis for Flavor Bible titles. |
| Graph Taxonomy | `docs/graph-taxonomy.md` | Proposed node/relationship schema for ingestion. |
| Environment Setup | `infra/docker/*`, `docs/windows-stack-setup.md` | Docker Compose + instructions for WP+Neo4j stack. |
| Roadmaps | `docs/epub-ingestion-roadmap.md`, `docs/graph-database-design.md` | Historical planning docs. |

### Automation Scripts
| Script | Purpose | Status |
| --- | --- | --- |
| `scripts/process_flavor_matrix.py` | Converts Flavor Matrix JSON into CSV tables + report. | Ready to run (requires GPT-generated JSON in `docs/flavor-matrix-processed/`). |
| `scripts/parse_flavor_bible.py` | Produces canonical ingredient JSON for *The Flavor Bible*. | Completed with canonicalisation, filtering, metadata cleanup. |
| `scripts/parse_vegetarian_flavor_bible.py` | Same as above for *The Vegetarian Flavor Bible*. | Completed, same features. |

### Environment / Dev Setup
- WSL2 + Docker: WordPress + MariaDB + Neo4j + Caddy stack ready for local dev/testing.
- `.gitignore` ensures processed outputs are tracked; raw EPUB data stays private.

### Known Limitations / Open Issues
- Canonicalization heuristics could still produce generic terms (e.g., all “cheese” entries collapse to `cheese`, `cheese, goat`). Need reconciliation strategy when creating graph nodes.
- Current pairings reference canonical ingredient names but do not yet ensure the paired ingredient exists in the same dataset. We need a cross-book canonical ingredient map (dedupe synonyms across books).
- Flavor Matrix dataset still requires manual image OCR using GPT-5 Vision for remaining pages; CSV generation script is ready but awaits full JSON coverage.
- No Neo4j ingestion script written yet (e.g., no `cypher` templates or parameterized loader).

---

## Roadmap Ahead

### Phase 1 — Canonical Ingredient Registry
1. **Consolidate ingredient canonicalization across datasets**
   - Build a master dictionary (CSV/JSON) mapping canonical names → display names + aliases + source books.
   - Incorporate heuristics: singularize, handle plural adjectives (e.g., “greens”, “beans”), ensure “flavor” vs. “flavour” normalization.
   - Flag ambiguous entries (e.g., `cheese`, `oil`, `herbs`) requiring manual curation or taxonomy mapping.

2. **Cross-dataset reconciliation**
   - Merge Flavor Bible & Vegetarian Flavor Bible ingredient lists; identify duplicates/conflicts (e.g., `kale` vs. `greens, kale`, `mint` vs. `mint, peppermint`).
   - Create a “preferred canonical” field and map other variants to it (maybe via `canonical_id`).

3. **Pairing integrity checks**
   - Ensure every pairing target exists in the canonical registry.
   - For unknown targets, either map to nearest canonical ingredient or flag for manual review.
   - Assign standardized `relationship_type` (ingredient↔ingredient, ingredient↔preparation, ingredient↔context) based on canonical name classification.

### Phase 2 — Graph Ingestion Tooling
1. **Cypher generation utilities**
   - Build script(s) that convert JSON into parameterized CSVs suitable for `LOAD CSV` (one for nodes, one for relationships).
   - Generate Neo4j constraints (unique `Ingredient.slug`).
   - Outline `MERGE` statements for `Ingredient`, `Pairing`, `FlavorAffinity`, `Descriptor`, etc., according to `docs/graph-taxonomy.md`.

2. **Classification & tagging**
   - Add type hints (e.g., `node_type`: ingredient, preparation, context, technique). Could be an extra step in the parser or a post-processing script referencing a curated taxonomy.
   - Tag `pairings` with `relationship_type` (e.g., `ingredient_pairs_with`, `ingredient_used_in`, `ingredient_goes_with_dish`, `technique_applicable_to`, etc.).

3. **Neo4j import workflow**
   - Create `neo4j-import/` folder with instructions (`README`, `cypher/`, `csv/`).
   - Automate: `python scripts/export_to_neo4j.py` → dumps CSVs + `cypher/import.cypher`.
   - Document `neo4j-admin import` or `cypher-shell` steps.

### Phase 3 — Enrichment & QA
1. **Flavor Matrix completion**
   - Process remaining wheel images via GPT-5 Vision.
   - Standardize matrix JSON (same canonical names, filtered pairings).
   - Run `process_flavor_matrix.py` to produce node/edge CSVs.

2. **Quality Assurance**
   - Build summary reports (counts per ingredient, top pairings, ingredients lacking pairings).
   - Cross-check with sample queries (e.g., “What pairs with basil?”, “Top 5 flavor affinities for almonds”) to ensure the graph matches expectations.

3. **Documentation**
   - Extend `docs/` with:
     * `neo4j-import.md` – ingestion instructions.
     * `data-dictionary.md` – canonical fields, attribute meanings.
     * `contribution-guide.md` – how to add new sources.

### Phase 4 — Optional Enhancements
1. **WordPress integration**
   - Build WP plugin integration (custom REST endpoints) to push/pull ingredient nodes from a WP admin interface.
   - Allow editors to confirm canonical mappings within WP.

2. **Visualization**
   - Use Neo4j Bloom or GraphXR to visualize ingredient neighborhoods (maybe create a small `notebooks/` folder with sample Cypher+Python queries using `py2neo`).

3. **Analytics / Recommendation Engine**
   - Build scripts to detect co-occurrence patterns (e.g., pairings that appear in both books).
   - Score pairings by tier + number of sources.

### Phase 5 — Scale & Maintenance
1. **Automated CI checks**
   - Add tests to ensure canonicalization is stable (given sample inputs).
   - Validate JSON schema with `jsonschema` or custom validators.

2. **Extensibility**
   - Ensure the parsers allow new sources with minimal fuss (extract to generic helper modules, parameterize stopword lists, etc.).

---

## Next Steps (Short-Term)
1. **Produce canonical ingredient registry**
   - Combine both JSON outputs; generate list of unique canonical names + display names + sources.
   - Identify entries needing manual review (ambiguous or overly generic names).

2. **Design ingestion CSV format**
   - Decide on columns for nodes (`slug`, `name`, `aliases`, `source`, `metadata_json`, etc.) and relationships (`from_slug`, `to_slug`, `tier`, `source`).

3. **Write export script**
   - `scripts/export_to_neo4j.py` that reads the JSON, applies canonical registry, and emits CSVs + Cypher import script.

4. **Document ingestion procedure**
   - Create `docs/neo4j-import.md` with step-by-step instructions (prepping CSVs, running Cypher, verifying counts).

5. **Begin pairings QA**
   - Spot-check canonical + display pairings for anomalies (“Wine” vs. “Red Wine Vinegar”, etc.).
   - Decide how to handle generic pairings (e.g., `fruits`, `greens`, `hot breakfast cereals`).

6. **Check-in on Flavor Matrix coverage**
   - Confirm which wheel images have been transcribed; schedule the remainder using the GPT prompt outlined earlier.

---

## Notes & Reminders
- **Canonical vs. display names**: Current JSON retains both. When creating nodes, use `ingredient` (canonical) as the unique key; store `display_name` for UI or original text reference.
- **Pairings referencing non-existent ingredients**: Knowing which ones lack canonical matches is crucial before graph import.
- **Stopwords list**: May need expansion when we find new contexts (e.g., “sushi”, “tempura”, “pasta shapes”).
- **Unicode handling**: Both parsers now convert headings to ASCII-friendly canonical names, but display names keep accents. Ensure CSV exporters handle UTF-8.
- **Git hygiene**: With raw EPUBs excluded, repository is safe to share. Continue checking `.gitignore` before adding new directories.
- **Token/Context limits**: TODO.md serves as the memory anchor for sessions; append key changes here after each major task so future windows can catch up quickly.

---

## TL;DR Jumpstart Checklist
1. Review `docs/flavor-bible-processed/flavor-bible.json` & `docs/vegetarian-flavor-bible-processed/vegetarian-flavor-bible.json` for canonical correctness.
2. Build canonical ingredient registry (dedupe across both datasets).
3. Create export pipeline to generate Neo4j-ready CSVs or direct Cypher.
4. Finish Flavor Matrix transcription + run `process_flavor_matrix.py`.
5. Draft Neo4j import documentation (`docs/neo4j-import.md`).
6. Continue logging progress in this TODO for future context resets.

Keep this document updated after each major push so we never lose the thread. Resume from “Next Steps” whenever spinning up a fresh session.
