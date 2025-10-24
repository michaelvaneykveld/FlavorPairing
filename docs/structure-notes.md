# EPUB Structure Notes

Comprehensive observations taken while completing step 2 of `docs/epub-ingestion-roadmap.md`. Samples were pulled from each extracted book under `docs/extracted/`.

## The Flavor Bible (2008, Little, Brown)

**Package / navigation**
- Manifest: `docs/extracted/flavor-bible/content.opf` (EPUB 2.0, Calibre generated). `dc:language` is set to `pt` even though the text is English. Spine entries reference XHTML files inside `OEBPS/Text/`, including split files for the long Chapter 3 lists (`FlavorBible_chap-3a.html`, `..._3c_split_000.html`, etc.).
- Navigation: `toc.ncx` only exposes a single start entry; the real table of contents lives at `OEBPS/Text/FlavorBible_toc.html` with anchors (`#chap-3a`, etc.) per chapter.
- Assets: All ingredient charts are XHTML; supporting art is stored in `OEBPS/Images/`. CSS lives at `stylesheet.css` and `page_styles.css`.

**Representative ingredient chapter (`OEBPS/Text/FlavorBible_chap-3a.html`)**

| File / Anchor | Markup pattern | Entities surfaced | Relationship / metadata cues | Extraction notes |
| --- | --- | --- | --- | --- |
| `FlavorBible_chap-3a.html` (intro paragraphs) | `<p class="calibre6">` narrative prose | Concepts explaining scoring system (Bold caps = top pairings, trailing asterisk = "ethereal") | Defines semantic meaning of typographic cues; introduces "Pairs to Avoid", "Flavor Affinities", seasonality, weight, volume, techniques | Capture once and map to parser rules so interpretation of bold/asterisk is consistent across the chapter splits |
| `#ACHIOTE` block | `<p class="h">` heading followed by `<p class="bl1">`, `<p class="nl1">` | Head ingredient, cross references `(See ...)`, season names, tastes, botanical relatives, weight/volume, techniques, tips | `Season`, `Taste`, `Weight`, `Volume`, `Techniques`, `Tips` appear as `<strong>` labels inside `bl1`/`nl1` paragraphs; values follow colon. Ingredients that pair well are individual `bl1` lines; uppercase + `<strong>` indicates "highly recommended" and uppercase + `*` (when present) indicates "ethereal" | Need to parse italic vs bold vs plain text to assign recommendation strength. Peak months are embedded as free text ("peak: July-October"). Some Unicode accents (e.g., `creme`) appear; retain UTF-8 |
| `Flavor Affinities` subsection | `<p class="h2"><strong>Flavor Affinities</strong></p>` + `bl1` list | Pre-grouped combinations (e.g., `avocado + bacon + scallions + tomatoes`) | Implicit hyperedges connecting multiple ingredients simultaneously | Store as separate relationship entity or expand into pairwise edges; keep order for trio/quartet identification |
| `boxh` / `ext` blocks | `<p class="boxh"><strong>Dishes</strong></p>` then `<p class="ext">` and `<p class="exts">` | Named chef dishes and sourcing restaurants/cities | Connect ingredients to signature dishes, chefs, restaurants, and locales | Chef lines start with em dash and include city; requires secondary parsing to split chef vs venue |
| Avoidance cues | Some ingredients include `<p class="bl1"><strong>AVOID:</strong> ...` later in lists | Incompatible pairings | Negative relationships ("avoid pairing X with Y") | Not every entry contains this; parser should look for `<strong>AVOID:` token |

**Key data themes**
- Ingredient nodes with attributes: `season`, `taste_profile`, `weight`, `volume`, `technique`, `tips`.
- Relationships: `Ingredient PAIRS_WITH Ingredient` (tiered by typography), `Ingredient HAS_BOTANICAL_RELATIVE Ingredient`, `Ingredient FEATURED_IN Dish`, `Ingredient AVOIDS Ingredient`.
- Context entities: `Cuisine/Region`, `Technique`, `Dish`, `Chef`, `Restaurant`, `City`.
- Seasonality appears both as ranges ("spring-summer") and peak months ("peak: July-October").

## The Vegetarian Flavor Bible (2014, Little, Brown)

**Package / navigation**
- Manifest: `docs/extracted/vegetarian-flavor-bible/OEBPS/package.opf` (EPUB 3.0). Navigation declared via `toc.xhtml` (EPUB 3 nav) plus legacy `toc.ncx`. Spine lists hundreds of chapter fragments (`chapter003a.xhtml` ... `chapter004za.xhtml`, `A-Z.xhtml`, etc.).
- Styling: Primary CSS `css/stylesheet.css`. Many pages mix flowable text and full-page images (`Art_Pxxx.jpg`).

**Representative ingredient list (`OEBPS/chapter003a.xhtml`, entries like Achiote Seeds)**

| File / Anchor | Markup pattern | Entities surfaced | Relationship / metadata cues | Extraction notes |
| --- | --- | --- | --- | --- |
| `chapter003a.xhtml` (section intro) | `<h1 class="chapter-title">`, `<div class="blockquote-1">`, `<p>` | Narrative describing ranking system, typography legend, seasonality explanation | Mirrors Flavor Bible guidance but tailored to vegetarian context | Same interpretation rules (bold caps = highly recommended, italics for contexts) |
| Ingredient entry container | `<div class="ingredients-entry">` (nested inside `<section class="bodymatter-rw">`), though Calibre dropped explicit wrapper -- repeated pattern of `<div class="headnote">`, `<div class="ingredients">` | Head ingredient appears in `<h1 class="entry-title">` or `<p class="subhead">`; metadata like `Season`, `Taste`, `Volume`, `Tip`, `Possible substitutes` each inside their own `<div class="headnote"><p><strong>Label:</strong> value</p>` | `Flavor`, `Weight`, `Volume`, `Function`, `Botanical relatives`, `Techniques`, `Tips`, `Possible substitutes`, dietary cues (e.g., "gluten-free") show up as labeled headnotes | Must normalize label text (capitalization varies, sometimes colon bolded) |
| Pairing lists | `<div class="ingredients"><p class="ingredient">...</p></div>` | Pairing candidates, cuisines, techniques, dish archetypes (italicized words), uppercase items for top-tier recommendations | Uppercase with `<strong>` indicates highest confidence; italics denote contextual category ("soups", "marinades") that should become nodes like `Preparation` or `DishType`; plain text indicates baseline pairs | Some lines include inline examples (`e.g., habanero`) -> parse list to extract example ingredient and parent category |
| Flavor affinities | `<div class="ingredients"><h1 class="ingredients-title">Flavor Affinities</h1> ...</div>` | Multi-ingredient combos | Same interpretation as Flavor Bible but vegetarian-focused | Entities should be stored as ordered combinations |
| Recipes / cross references | `<div class="recipe">` with `<h1 class="recipe-title">`, followed by headnotes (`Flavor`, `Volume`, `What it is`, `Ingredients list`) | Preassembled blends or sauces (e.g., `ADOBO SAUCE`) | Provide relationship edges from blend to constituent ingredients and to use cases ("tacos", "beans") | Some recipe titles include `see also` cross references; respect uppercase tokens |

**Key data themes**
- Same core ingredient metadata plus explicit `Possible substitutes`, `Nutritional` descriptors (e.g., "gluten-free"), and plant-based context (frequent `<em>` tags for meal types).
- Broader coverage of vegetarian pantry items (tempeh, seitan, kombu, seed oils) and plant-based techniques.
- Seasonality noted as ranges ("late summer-early winter"); uses en-dash in source text--capture but normalize as structured month ranges.
- Additional nodes for `PreparationType` (soups, sauces, marinades), `Cuisine`, `Course` gleaned from italicized entries.

## The Flavor Matrix (2018, Houghton Mifflin Harcourt)

**Package / navigation**
- Manifest: `docs/extracted/flavor-matrix/OEBPS/volume.opf` (EPUB 3.0). Declares `rendition:layout="pre-paginated"` with landscape spreads. Every page is a fixed-layout XHTML (`p001.xhtml` ... `p310.xhtml`) paired with high-resolution images.
- Navigation: `OEBPS/toc.xhtml` provides TOC entries for every ingredient page (`p018.xhtml` = Allium, etc.) and a full `page-list` for page numbers. No `.ncx` (EPUB 3 nav-only).
- Assets: Each page references multiple raster images (e.g., `image/1034.jpg` for Avocado matrix) plus numerous small PNGs for matrix legends. CSS: `css/idGeneratedStyles_0/1/2.css` with absolute positioning of spans.

**Representative ingredient spread (Avocado: `p030.xhtml` and matrix `p031.xhtml`)**

| File | Markup pattern | Entities surfaced | Relationship / metadata cues | Extraction notes |
| --- | --- | --- | --- | --- |
| `p030.xhtml` | Single `<div>` with absolute-positioned `<span>` layers over background image | Textual summary paragraphs; labeled lists "Best Pairings", "Surprise Pairings", "Substitutes" | Directly states top companion ingredients (e.g., "Best Pairings: Cocoa, chiles, fruit (especially citrus), butter, cream, roasted meat, seafood") and context such as biochemical rationale | Text is accessible via XML parsing despite fixed layout. Need to strip positional noise. Provides limited structured data (counts of categories, not matrix weights) |
| `p031.xhtml` | Series of `<img>` tiles and absolutely positioned single-letter spans forming the matrix grid | Axis labels (A, B, C...) and numerous small PNGs encoding circles/lines that express molecular overlaps | Visual matrix conveys compound families and connection strengths; not available as accessible text | Full pairing graph requires OCR or manual interpretation of image overlays. Each image `62x.png` corresponds to a colored node/edge. Capturing data programmatically will require computer-vision or manual annotation |
| `p252.xhtml` (Elements of Flavor, representative narrative section) | Flowed text with absolute spans similar to `p030` | Describes flavor building blocks, techniques | Conceptual relationships (e.g., acid balances fat) | Suitable for textual extraction; still fixed-layout but text accessible |

**Key data themes**
- Ingredient summaries combine biochemical justification (shared compounds, fat composition) with pairing categories.
- Distinguishes `Best Pairings`, `Surprise Pairings`, `Substitutes` as explicit labeled lists; occasionally includes `Techniques`/`Applications` in other pages (verify per ingredient).
- Core pairing matrix lives in imagery; legend icons (PNG slices) likely encode pair strength (size of circle) and flavor families (color). Need mapping of `image/62x.png` -> legend semantics using the key pages early in book.
- Provides seasonal hints indirectly ("harvested year-round") and origin notes inside summary paragraph.

## Cross-book alignment opportunities
- **Ingredient metadata**: Both Flavor Bible titles expose `Season`, `Taste`, `Weight`, `Volume`, `Techniques`, `Tips`, `Possible substitutes`, `Botanical relatives`. Flavor Matrix adds biochemical context and pairing categories (Best/Surprise/Substitute).
- **Pairing strength cues**: Flavor Bible series uses typography (plain -> bold -> BOLD CAPS -> BOLD CAPS + `*`). Vegetarian edition preserves uppercase emphasis; italics flag contextual applications. Flavor Matrix uses discrete list labels and visual matrix (size/color).
- **Relationship types**: In addition to `Ingredient <-> Ingredient` edges, all books reference `Cuisine`, `Technique`, `Dish`, `Chef/Restaurant`, `Texture`, `Season`, and sometimes `Function` (e.g., "primary function: bittering"). Negative edges ("Avoid") appear in Flavor Bible. Vegetarian edition supplies blend/recipe nodes (e.g., sauces) linking to ingredients and use cases.
- **Seasonality**: Flavor Bible entries include peak months; Vegetarian edition uses ranges with qualifiers ("year-round (dried)"). Flavor Matrix offers qualitative availability notes. All can map to a `Season` entity with month ranges and usage notes.
- **Extraction considerations**: Flavor Bible files are large but plaintext; rely on class names (`h`, `bl1`, `nl1`, `boxh`, etc.) to segment entries. Vegetarian edition uses semantic div wrappers making XPath extraction straightforward. Flavor Matrix requires hybrid approach: text lists parsed via XML; matrix data likely needs manual digitization or computer-vision with legend decoding.

These notes should support the next roadmap steps: formalizing graph taxonomy (Step 3) and designing extraction scripts tailored to each markup style.
