=== Flavor Pairing Graph ===
Contributors: flavorpairingteam
Tags: flavors, ingredients, graph, pairing, cooking
Requires at least: 6.0
Tested up to: 6.6
Stable tag: 0.1.0
Requires PHP: 7.4
License: GPLv2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.txt

Explore ingredient pairings and culinary inspiration using a graph-aware data model grounded in the Flavor Bible, Flavor Matrix, and related references.

== Description ==

Flavor Pairing Graph delivers a customizable flavor knowledge base by combining WordPress content management with a graph database. Curate ingredients, classify them in flavor families and techniques, and sync their relationships to an external graph engine for deep exploration.

== Features ==

* Ingredient custom post type with REST support.
* Flavor family and technique taxonomies for grouping.
* Admin meta boxes for flavor notes and seasonality.
* Pluggable adapter for Neo4j, Amazon Neptune, or other graph services.
* Shortcode for rendering simple pairing lists.

== Installation ==

1. Upload the `flavor-pairing` directory to the `/wp-content/plugins/` directory.
2. Activate the plugin through the `'Plugins'` menu in WordPress.
3. Configure graph connection details under Settings → Flavor Pairing (coming soon).

== Frequently Asked Questions ==

= Does this ship with a graph database? =

No. You can connect to any external graph database that exposes a compatible API (for example, Neo4j HTTP API, Amazon Neptune, or RedisGraph).

= How do I customize the schema? =

Extend the `Flavor_Pairing_Graph_Adapter` class to map WordPress objects into your graph schema. Override `run_query` and related helpers.

== Changelog ==

= 0.1.0 =
* Initial boilerplate release.
