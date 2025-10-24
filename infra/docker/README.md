# Local Stack (WordPress + MariaDB + Caddy + Neo4j)

This directory contains a minimal Docker Compose setup sized for development on Windows via WSL 2. The stack runs:

- WordPress PHP-FPM (`wordpress:php8.2-fpm-alpine`)
- Caddy web server proxying PHP requests
- MariaDB for WordPress
- Neo4j Community Edition with APOC

## Files

- `docker-compose.yml` – service definitions and shared volumes.
- `Caddyfile` – web server configuration that forwards PHP requests to the FPM container.
- `.env.example` – baseline environment variables; copy to `.env` and adjust secrets.

## Usage Outline

1. Copy `.env.example` to `.env` and edit the passwords.
2. From the `infra/docker/` directory, run `docker compose up -d`.
3. Finish WordPress installation at `http://localhost/`.
4. Access Neo4j Browser at `http://localhost:7474/` (default credentials `neo4j/test` unless changed in `.env`).

> ⚠️ You need Docker Engine (or Docker Desktop) available inside WSL 2. See the root onboarding instructions for the exact setup steps on Windows.
