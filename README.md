# Flavor Pairing Graph Plugin

This repository contains the Flavor Pairing WordPress plugin, designed to explore ingredient relationships using an external graph database. It combines structured ingredient content with graph-powered insights inspired by *The Flavor Bible*, *The Flavor Matrix*, and related references.

## Structure

- `flavor-pairing/` – WordPress plugin code and assets.
- `docs/` – Architecture notes and graph schema brainstorming.

## Getting Started

1. Copy the `flavor-pairing` directory into your WordPress installation under `wp-content/plugins/`.
2. Activate **Flavor Pairing Graph** from the WordPress admin.
3. Configure graph connection settings (adapter scaffolding provided; implement vendor specifics).

## Development

Use WordPress coding standards for PHP, enqueue scripts/styles via the provided entry points, and extend the graph adapter to integrate with your chosen graph service (Neo4j, Neptune, RedisGraph, etc.).

See `docs/graph-database-design.md` for schema brainstorming and next steps.
