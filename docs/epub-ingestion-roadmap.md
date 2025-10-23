# EPUB Ingestion Roadmap

This roadmap lays out the steps for understanding and extracting structured flavor-pairing data from the EPUB editions of *The Flavor Bible*, *The Vegetarian Flavor Bible*, *The Flavor Matrix*, and related sources. Because each EPUB bundle contains many discrete XHTML files, we can evaluate and ingest them piece-by-piece to stay within token and processing limits.

## 1. Prepare Representative Samples

- Copy the EPUB files into `docs/`.
- Unpack each archive using `Expand-Archive` (PowerShell) or any ZIP extractor. Suggested structure:
  ```
  docs/raw/
    flavor-bible.epub
  docs/extracted/
    flavor-bible/
      META-INF/
      OEBPS/
        content.opf
        nav.xhtml / toc.ncx
        Text/*.xhtml
  ```
- Select one small XHTML chapter per book as a reference sample for analysis.

## 2. Analyze EPUB Structure

- **Manifest (`content.opf`)**: Lists every resource, includes role information (chapters, images, CSS). Note primary directories (`Text/`, `Styles/`, etc.).
- **Navigation (`nav.xhtml` or `toc.ncx`)**: Shows hierarchy of chapters/sections. Identify sections that map to ingredient listings, flavor wheels, or pairing tables.
- **Chapter XHTML files**: Inspect markup patterns (tables, definition lists, headings) that encode ingredient relationships.

Document findings in a shared table (e.g., `docs/structure-notes.md`) noting:
- File path
- Markup pattern (table, list, paragraph)
- Entities present (ingredients, descriptors, techniques, citations)
- Edge hints (e.g., bullet list of pairings, bold headings for primary ingredient)

## 3. Define Graph Taxonomy

From the structural notes, draft the node/relationship schema for each source:

- **The Flavor Bible**: Typically center ingredient with sub-headings for pairings, flavor descriptions, seasonality notes. Edges: `Ingredient` ↔ `PairsWith`, `Ingredient` ↔ `Descriptor`.
- **Vegetarian Flavor Bible**: Similar structure but focused on plant-based ingredients; add node attributes indicating vegetarian applicability.
- **The Flavor Matrix**: Often ties ingredients to shared compounds. Introduce `Compound` nodes and `CONTAINS` / `BRIDGED_BY` edges.

Record all candidate node types, edge types, and key properties in `docs/graph-database-design.md` (extend existing brainstorming) with flags indicating which book supports which relationship.

## 4. Extraction Approach

- **Token-friendly workflow**: Work chapter-by-chapter. Each XHTML file is a manageable size and keeps parsing tasks within context limits.
- **Parsing helpers**: Use generic XML/XPath tools (PowerShell `[xml]`, Python `lxml`, or PHP DOMDocument) to pull structured elements without writing bespoke parsers.
- **Normalization**: Map consistent ingredient names, unify casing, capture source page numbers (available in EPUB via navigation labels).
- **Traceability**: Store `source_book`, `source_section`, and `source_path` with every node/edge for auditing.

## 5. Loading Strategy

- Transform extracted data into:
  - **CSV for SQL**: `ingredients.csv`, `pairings.csv`, `compounds.csv`, etc.
  - **Cypher scripts**: `MERGE` statements for nodes and relationships, parameterized by CSV via `LOAD CSV`.
- For Neo4j:
  - Stage CSVs in a location accessible to Neo4j.
  - Create constraint indexes (`CREATE CONSTRAINT ...`) before ingestion.
  - Use `LOAD CSV WITH HEADERS` to insert nodes, then relationships.

## 6. Incremental Validation

- Start with the sample chapters. Confirm generated graph matches the book layout.
- Iterate over additional chapters, refining parsing rules as new patterns appear.
- Once satisfied, run batch ingestion for each book, tracking progress and edge counts per section.

## Next Actions

1. Place at least one EPUB in `docs/raw/` and extract it to `docs/extracted/`.
2. Capture structural observations for a representative chapter in a new `docs/structure-notes.md`.
3. Update `docs/graph-database-design.md` with node/edge specifics tied to the sample.
4. Prototype extraction using a single tool chain (e.g., PowerShell + XPath) and validate in a small Neo4j sandbox.
