# Flavor Pairing Graph Taxonomy

This document formalizes the graph schema we will apply when ingesting structured knowledge from *The Flavor Bible*, *The Vegetarian Flavor Bible*, *The Flavor Matrix*, and related sources. It expands upon the exploratory notes in `docs/structure-notes.md` and is intended to guide extraction scripts, data validation, and downstream analytics.

The taxonomy is presented in two passes. The **first pass** captures the full schema design after walking through the book structures. The **second pass** revisits the entire approach, pressure-tests assumptions, and refines the model where needed.

---

## 1. Modeling Principles (First Pass)

1. **Traceability first.** Every node or relationship created from a book must carry `source_book`, `source_section`, and `source_path` properties so we can trace back to the originating XHTML snippet.
2. **Vocabulary normalization.** Ingredient identifiers, cuisine names, techniques, and descriptors must be normalized before ingestion (case-folded, singularized, and mapped to canonical slugs).
3. **Tiered certainty.** Pairing strengths, recommendation tiers, and flags such as "avoid" or "surprise pairing" should be captured explicitly rather than implied by formatting.
4. **Composable structures.** Hyperedges such as "Flavor Affinities" or matrix clusters need a representation that supports both the original grouped suggestion and derived pairwise edges.
5. **Extensibility.** The schema should absorb future sources (chef interviews, lab data) without requiring disruptive migrations.

---

## 2. Node Definitions (First Pass)

| Label | Description | Key Properties | Source Signals |
| ----- | ----------- | -------------- | -------------- |
| `Ingredient` | Core edible items at any granularity (e.g., `Avocado`, `Lime Zest`, `Smoked Paprika`). | `name` (canonical), `slug`, `category` (produce, protein, seasoning, beverage, prepared), `aliases` (array), `description`, `source_book`, `source_section`, `source_path`, `created_at`, `updated_at`. Optional: `plant_based` (bool), `is_variety` (bool). | Heading text in Flavor Bible entries; Vegeterian flavor lists; Flavor Matrix page headings. |
| `IngredientGroup` | Logical families used for grouping entries (e.g., `Citrus`, `Allium`, `Stone Fruit`). | `name`, `slug`, `group_type` (`botanical`, `culinary`, `compound_family`), `description`, `source`. | Manifest headings, Flavor Matrix axes, book introductions. |
| `Descriptor` | Adjectives or short phrases describing taste notes, weight, volume, function (e.g., `sweet`, `quiet volume`, `primary bittering agent`). | `name`, `descriptor_type` (`taste`, `aroma`, `texture`, `function`, `weight`, `volume`), `scale` (optional numeric), `source`. | Labeled `Taste`, `Weight`, `Volume`, `Primary function` fields. |
| `Technique` | Cooking, preparation, or usage methods (`roasting`, `raw`, `infusion`). | `name`, `slug`, `technique_group` (heat, finishing, preservation), `description`, `source`. | Flavor Bible `Techniques` lists, Vegetarian technique references. |
| `Cuisine` | Culture or regional contexts (`Thai`, `Mediterranean`, `Caribbean`). | `name`, `slug`, `region`, `source`. | Lists in the books, italicized contexts, vegetarian cuisine notes. |
| `Course` | Meal or menu positions (`dessert`, `salad`, `sauce`). | `name`, `slug`, `course_group` (`meal`, `component`, `format`), `source`. | Italicized labels such as `soups`, `salads`, `tacos`. |
| `Dish` | Specific named dishes (e.g., `Avocado and Grapefruit with Poppy Seed Dressing`). | `name`, `slug`, `chef`, `restaurant`, `city`, `country`, `notes`, `source_book`, `page`. | `Dishes` boxes and Vegetarian recipe callouts. |
| `Chef` | Individuals credited with dishes. | `name`, `slug`, `bio`, `restaurant`, `city`, `source`. | Chef attributions. |
| `Restaurant` | Establishments tied to dishes. | `name`, `slug`, `city`, `region`, `country`, `source`. | Chef attributions. |
| `Season` | Time windows or peak availability periods. | `name` (e.g., `late summer`, `June-September`), `start_month`, `end_month`, `source`. | `Season:` fields, explicit peak month notes. |
| `Compound` | Flavor compounds or chemical classes. | `name`, `slug`, `compound_class`, `notes`, `source`. | Flavor Matrix introductions, compound glossaries. |
| `MatrixNode` | Visual nodes from Flavor Matrix spreads when we transcribe the graphical data. | `name`, `node_type` (`flavor_family`, `pairing_strength_marker`), `color`, `legend_code`, `source`. | Derived from matrix legend icons. |
| `AffinitySet` | Represents grouped multi-ingredient combinations (flavor trios, cliques). | `name` (derived slug), `description`, `source_book`, `source_section`, `source_path`, `rank` (if provided). | `Flavor Affinities` blocks. |

Optional future additions include `Nutrient`, `TextureProfile`, or `Product` nodes, but they are outside the current ingestion scope.

---

## 3. Relationship Definitions (First Pass)

| Relationship | Direction | Description | Key Properties | Source Signals |
| ------------- | --------- | ----------- | -------------- | -------------- |
| `(:Ingredient)-[:PAIRS_WITH]->(:Ingredient)` | Directed | Baseline pairing edge. Direction captures primary -> supporting ingredient emphasis when present. | `strength_tier` (`ethereal`, `classic`, `recommended`, `mentioned`), `rank_score` (numeric scale), `source_book`, `source_section`, `source_path`, `notes`, `avoid` (bool), `context_tags` (array), `first_seen` (date). | Formatting tiers (bold caps, uppercase, plain), explicit `AVOID` labels (set `avoid=true` with reason in notes), Flavor Matrix `Best` vs `Surprise` lists. |
| `(:Ingredient)-[:HAS_RELATION]->(:Descriptor)` | Directed | Links ingredients to descriptor values. | `descriptor_type`, `value_text`, `source`. | `Taste`, `Weight`, `Volume`, `Primary function`, `Tips` fields. |
| `(:Ingredient)-[:IN_SEASON_DURING]->(:Season)` | Directed | Connects ingredients to availability window. | `confidence`, `source`. | `Season:` fields and peak month lists. |
| `(:Ingredient)-[:BELONGS_TO]->(:IngredientGroup)` | Directed | Ingredient membership in groups or families. | `relationship_type` (`botanical`, `culinary`, `compound`), `source`. | Grouping cues, cross references (`(See Allium)`). |
| `(:Ingredient)-[:RELATED_TO]->(:Ingredient)` | Undirected (store both directions) | Used for botanical relatives, varieties, or aliases. | `relation_type` (`botanical_relative`, `variety`, `alias_of`), `source`. | `Botanical relatives:` lines; `See also` references. |
| `(:Ingredient)-[:WORKS_WITH_TECHNIQUE]->(:Technique)` | Directed | Techniques recommended for an ingredient. | `confidence`, `source`. | `Techniques:` fields. |
| `(:Ingredient)-[:POPULAR_IN]->(:Cuisine)` | Directed | Cultural context associations. | `confidence`, `source`. | Entries listing cuisines or italicized contexts. |
| `(:Ingredient)-[:SUITABLE_FOR]->(:Course)` | Directed | Common usage contexts (salads, soups, tacos). | `confidence`, `source`. | Italicized `soups`, `salads`, etc. |
| `(:Ingredient)-[:SUBSTITUTES_WITH]->(:Ingredient)` | Directed | Suggested replacements. | `context` (e.g., `for color`), `source`. | Vegetarian `Possible substitutes` fields; Matrix `Substitutes`. |
| `(:Ingredient)-[:FEATURED_IN]->(:Dish)` | Directed | Ingredient appears in named dish. | `role` (`primary`, `supporting`), `notes`, `source`. | Dishes boxes and recipe sections. |
| `(:Dish)-[:CREATED_BY]->(:Chef)` | Directed | Chef attribution. | `source`. | Chef citations. |
| `(:Dish)-[:SERVED_AT]->(:Restaurant)` | Directed | Establishment association. | `source`. | Chef citations. |
| `(:Restaurant)-[:LOCATED_IN]->(:Cuisine)` | Directed | Optional mapping from restaurant to cuisine/region. | `source`. | Derived from city/region data. |
| `(:Ingredient)-[:CONTAINS_COMPOUND]->(:Compound)` | Directed | Chemical composition. | `concentration_level` (qualitative), `source`, `notes`. | Flavor Matrix compound tables. |
| `(:Compound)-[:BRIDGES]->(:Compound)` | Directed | Chemical relationships enabling pairing. | `source`, `notes`. | Flavor Matrix explanations. |
| `(:Ingredient)-[:HAS_MATRIX_NODE]->(:MatrixNode)` | Directed | Ties ingredient to a visual node for matrix reconstruction. | `source`, `legend_code`. | Matrix legend mapping. |
| `(:AffinitySet)-[:CONTAINS]->(:Ingredient)` | Directed | Membership of hyperedge. | `position_index` (to preserve ordering), `source`. | Flavor affinity combos. |
| `(:AffinitySet)-[:SUPPORTED_BY]->(:Descriptor or :Technique or :Cuisine)` | Directed | Context metadata for the affinity. | `notes`, `source`. | Narrative text accompanying flavor trios. |

Every relationship inherits base provenance fields: `source_book`, `source_section`, `source_path`, `extracted_at`, and `confidence` (percentage or categorical).

---

## 4. Attribute Normalization Rules (First Pass)

1. **Strength tiers.** Map formatting cues to tiers:
   - `ethereal` when uppercase bold with trailing `*`.
   - `classic` when uppercase bold (no `*`).
   - `elevated` when bold (mixed case).
   - `recommended` when plain text.
   - `experimental` when listed under `Surprise Pairings`.
2. **Seasonality.** Convert textual ranges to month spans:
   - `spring` -> March-May, `late summer` -> August-September, `June-September` -> direct assignment.
   - `year-round (dried)` -> create distinct seasons for `year-round` with `form=dried`.
3. **Volume and weight descriptors.** Map to enumerations:
   - `Volume` -> `quiet`, `moderate`, `loud`.
   - `Weight` -> `light`, `medium`, `heavy`.
4. **Cuisine context.** Tag italicized contexts under `context_tags` and decide whether they belong to `Cuisine`, `Course`, or `Technique` categories based on dictionary lookups.
5. **Text cleanup.** Standardize quotes, remove trailing punctuation, expand abbreviations (e.g., `esp.` -> `especially`).

---

## 5. Source-to-Schema Mapping (First Pass)

### 5.1 The Flavor Bible
- Primary data flows: `Ingredient` nodes from headings, `PAIRS_WITH` edges from bullet lists, `AffinitySet` from `Flavor Affinities`, negative pairings from `AVOID`.
- `Descriptor` connections for taste, weight, volume, function, tips.
- `Technique`, `Cuisine`, `Course` associations derived from list entries.
- `Season` nodes from `Season:` and `peak` annotations.
- `Dish`, `Chef`, `Restaurant` nodes from `Dishes` sections.

### 5.2 The Vegetarian Flavor Bible
- Same as above, but with additional `SUBSTITUTES`, `Nutritional` flags (store as descriptors), and more frequent `Course` contexts (`soups`, `marinades`, `tacos`).
- Plant-based attribute `plant_based=true` at ingredient level.
- Additional recipe blends (e.g., `ADOBO SAUCE`) should be modeled as `Dish` nodes with `DishType='compound'`.

### 5.3 The Flavor Matrix
- Ingredient overview text yields `Descriptor` connections (origin, availability) and `PAIRS_WITH` edges from `Best Pairings` and `Surprise Pairings`.
- `Substitutes` map to `SUBSTITUTES_WITH` relationships.
- Chemical reasoning populates `Compound` nodes and `CONTAINS_COMPOUND` edges.
- Visual matrix requires manual or computer-vision extraction:
  - Each circle or node becomes a `MatrixNode`.
  - Edges between nodes capture intensity (`strength_score`) based on circle size or color (to be calibrated via legend).
  - Derived `PAIRS_WITH` edges can inherit `strength_score` from matrix data.

---

## 6. Hyperedge Handling (Flavor Affinities and Flavor Trios)

1. Each affinity group gets an `AffinitySet` node named with a slugified list (e.g., `avocado-bacon-scallions-tomatoes`).
2. `CONTAINS` edges include `position_index` to preserve author order.
3. Optionally derive pairwise edges by iterating combinations within the set and tagging them with `derived_from_affinity=true`.
4. Attach context metadata via `SUPPORTED_BY` edges (e.g., `Technique` -> `raw`, `Course` -> `salad`).
5. When the book provides ranking or narrative notes, store them in `AffinitySet.notes` or `rank`.

---

## 7. Data Provenance, Versioning, and Confidence

1. `source_book` uses a controlled vocabulary: `flavor_bible`, `vegetarian_flavor_bible`, `flavor_matrix`.
2. `source_section` is the logical chapter or anchor (e.g., `chap-3a`, `p030`).
3. `source_path` holds the relative XHTML path for reproducibility.
4. `confidence` defaults:
   - 1.0 for explicit textual statements (`Season: spring-summer`).
   - 0.8 for visually interpreted data (Flavor Matrix icons).
   - 0.6 when inferred programmatically (derived pairwise edges).
5. Maintain an `extraction_run_id` to track batch imports.

---

## 8. Implementation Phases

1. **Phase 0 (Manual Seed):** Load a minimal subset (10 ingredients per book) to validate schema, run exploratory Cypher queries, and ensure typing works.
2. **Phase 1 (Structural Ingestion):** Automate extraction of ingredient metadata, pairings, seasonality, techniques, and affinity sets for the entire Flavor Bible pair.
3. **Phase 2 (Matrix Augmentation):** Integrate Flavor Matrix textual lists and kickoff manual transcription or OCR of matrix graphics.
4. **Phase 3 (Compound Layer):** Introduce `Compound` and related edges once data quality controls are in place.
5. **Phase 4 (External Validation):** Cross-check pairings against other datasets (recipe corpora, chemical databases), adjust `confidence`, and expose the data via APIs.

---

## 9. Second Pass Reconsideration

Taking a fresh look at the entire schema, several improvements and clarifications emerged:

1. **Pairing edge representation.** Initial design used only direct `PAIRS_WITH` edges. After reconsideration, representing each pairing statement as its own `Pairing` node could simplify attaching multiple contexts (cuisine, technique, course) without duplicating edges. However, that adds complexity during traversal. Decision: retain direct edges for query performance but allow optional `Pairing` nodes for cases with rich metadata (e.g., multiple contexts, conflicting sources). Add relationship: `(:Pairing)-[:LINKS]->(:Ingredient)` with role property to support this hybrid approach when necessary.
2. **Context overloading.** Italicized entries such as `soups`, `marinades`, `salsas` can mean course, technique, or preparation. Second pass introduces a lookup priority: first check against a curated `Technique` dictionary; if absent, treat as `Course`. Only fall back to `Descriptor` when neither matches. Document this as part of ETL validation.
3. **Season modeling granularity.** Instead of a single `Season` node per textual label, use `Season` as an entity representing exact month ranges (`Mar-May`) and pair it with a `SeasonLabel` descriptor to preserve the original phrase. This avoids redundant nodes for "late summer" vs "summer (late)". Update rule: compute `start_month` and `end_month`, and set `Season.label` to the original text.
4. **Affinity sets vs dishes.** Some affinity sets blur into recipe concepts. Reconsideration suggests tagging `AffinitySet` with `set_type` (`trio`, `clique`, `recipe_seed`) so downstream tooling can decide whether to surface it as a ready-made recipe idea or a pure combination.
5. **Compound coverage.** Flavor Matrix does not list explicit compound concentrations for every ingredient. To avoid sparse graphs, add `Compound` nodes only when the source provides names. For generic statements ("rich in monounsaturated fats"), store this as a `Descriptor` link (`descriptor_type='nutrition'`) instead.
6. **Matrix data ingestion risk.** The visual nature of the Flavor Matrix means automated extraction may introduce noise. Incorporate a `verification_status` property on `MatrixNode` and all matrix-derived edges (values: `pending`, `validated`, `rejected`) and maintain a manual review queue.
7. **Version control of normalization dictionaries.** Create `NormalizationRule` metadata (not necessarily a node) in the ETL codebase to capture mapping versions. The graph itself should store `normalized_with` property referencing rule set version (e.g., `v1.0`).

With these adjustments, the schema remains performant yet flexible, and it explicitly flags areas that need manual verification or future refinement.

---

## 10. Summary of Adjustments After Second Pass

1. Added optional `Pairing` node pattern for complex pairing statements.
2. Clarified context normalization priority and categorized italicized tokens more reliably.
3. Refined `Season` modeling to store exact month ranges alongside original labels.
4. Extended `AffinitySet` with `set_type` property for disambiguation.
5. Scoped `Compound` usage to explicit mentions, re-routing general nutrition info to descriptors.
6. Introduced `verification_status` on matrix-derived data to manage transcription quality.
7. Noted the need for versioned normalization dictionaries and `normalized_with` properties.

These refinements ensure the taxonomy is both comprehensive and resilient when we scale ingestion across the three books and beyond.
