# Flavor Pairing Graph Database Brainstorm

This document captures early thinking on how to translate insights from *The Flavor Bible*, *The Vegetarian Flavor Bible*, *The Flavor Matrix*, and similar resources into a graph data model. The objective is to support exploratory flavor pairing queries that feel natural to chefs and home cooks.

## Core Concepts

- **Ingredient Nodes**  
  - `Ingredient` nodes represent single ingredients or preparations (e.g., `Vanilla`, `Smoked Paprika`, `Miso`).  
  - Properties: `name`, `aliases`, `seasonality`, `intensity`, `category`, `flavor_notes` (keywords drawn from tasting descriptors).

- **Flavor Family Nodes**  
  - `FlavorFamily` nodes mirror recurring groupings found in the books (e.g., `Allium`, `Citrus`, `Stone Fruit`).  
  - Relationships: `(:Ingredient)-[:BELONGS_TO]->(:FlavorFamily)`.

- **Technique / Context Nodes**  
  - `Technique` nodes capture cooking methods or pairing contexts such as `Roasting`, `Infusion`, `Dessert`.  
  - Useful for conditional recommendations: `(:Ingredient)-[:SHINES_IN]->(:Technique)`.

- **Pairing Relationships**  
  - `(:Ingredient)-[:PAIRS_WITH {weight, source, rationale}]->(:Ingredient)` is directional to allow asymmetry (some books list stronger primary ↔ accent relationships).  
  - Edge properties: `weight` (strength/confidence score), `source` (book citation), `notes` (free text), `pairing_type` (classic, contrast, aromatic bridge, etc.).

- **Flavor Compound Nodes (Optional Phase)**  
  - `Compound` nodes (e.g., `Vanillin`, `Eugenol`) map the chemistry detail in *The Flavor Matrix*.  
  - Relationships: `(:Ingredient)-[:CONTAINS]->(:Compound)` and `(:Compound)-[:BRIDGES]->(:Compound)` to explain why pairings work.

- **Cuisine / Cultural Lens**  
  - `Cuisine` nodes help contextualize pairings with cultural references (e.g., `Thai`, `Mediterranean`).  
  - Relationships: `(:Ingredient)-[:POPULAR_IN]->(:Cuisine)` and `(:Pairing)-[:INSPIRED_BY]->(:Cuisine)` when modeling recipes.

## Hierarchies and Groupings

- Ingredients often inherit properties from broader families (e.g., `Blood Orange` inherits attributes from `Orange` and `Citrus`).  
  - Model with `(:Ingredient)-[:IS_VARIETY_OF]->(:Ingredient)` or `(:Ingredient)-[:PART_OF]->(:IngredientGroup)`.
- Flavor families can be nested to reflect compound families (e.g., `Tropical` has child families such as `Melon`, `Coconut`).  
  - Use `(:FlavorFamily)-[:SUBSET_OF]->(:FlavorFamily)`.

## Bridging WordPress and the Graph

1. **Ingredients**  
   - WordPress `flavor_ingredient` posts map 1:1 to `Ingredient` nodes.  
   - Custom fields: `seasonality`, `flavor_notes`, `intensity`, `aliases`.

2. **Taxonomies**  
   - `flavor_family` taxonomy → `FlavorFamily` nodes (`term_id` as primary key).  
   - `flavor_technique` taxonomy → `Technique` nodes.

3. **Pairings Data Capture**  
   - Admin UI extension will allow editors to enter complementary ingredients, weight, rationale, and references.  
   - Could model as WordPress post relationships (e.g., `post_meta` storing connected IDs) or custom REST endpoints that write directly to the graph.

4. **Synchronization Strategy**  
   - Upon publish/update of an ingredient, push node updates and relevant edges to the graph.  
   - Background task via WP Cron or Action Scheduler can rebuild pairings in batches.

## Example Traversal Queries

- Top pairings for an ingredient, ordered by strength:
  ```
  MATCH (:Ingredient {name: $ingredient})- [p:PAIRS_WITH]->(match)
  RETURN match, p.weight
  ORDER BY p.weight DESC
  LIMIT 10
  ```

- Discover bridge ingredients that share compounds:
  ```
  MATCH (a:Ingredient {name: $ingredient})-[:CONTAINS]->(compound)<-[:CONTAINS]-(bridge)
  WHERE bridge <> a
  RETURN bridge, collect(DISTINCT compound.name) AS shared_compounds
  ORDER BY size(shared_compounds) DESC
  LIMIT 10
  ```

- Suggest complementary techniques for a flavor concept:
  ```
  MATCH (:FlavorFamily {name: $family})<-[:BELONGS_TO]-(ingredient)
        -[:SHINES_IN]->(technique)
  RETURN technique.name AS technique, count(*) AS hits
  ORDER BY hits DESC
  ```

## Data Provenance and Scoring

- Each pairing should maintain source references (`source`, `page`, `confidence`).  
- Combine multiple sources into aggregated weights to identify strongest pairings.  
- Distinguish `classic` pairings from `modern` or `experimental` using categorical attributes.

## Next Steps

1. Define REST endpoints to CRUD pairing relationships (`/wp-json/flavor-pairing/v1/pairings`).  
2. Evaluate Neo4j vs. AWS Neptune vs. RedisGraph based on hosting requirements and query needs.  
3. Prototype data imports from book excerpts (manual entry initially, ETL pipeline later).  
4. Design UI components for searching pairings, filtering by technique, and visualizing graph neighborhoods.
