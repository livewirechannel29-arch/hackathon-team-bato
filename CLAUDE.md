# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Northwind Logistics** — a hackathon demo of the **Strangler Fig pattern**: incrementally modernizing a legacy PHP 5 monolith by extracting routes into a modern layer behind a routing proxy, with both apps sharing the same database and running simultaneously. No cutover, no data migration, no feature freeze required.

## Running the Stack

### Docker Compose (full stack — MySQL + PHP legacy + PHP modern + Nginx)

```bash
# Install PHP dependencies first
docker compose run --rm modern composer install

# Start everything
cd northwind && docker compose up
```

- Legacy HTML UI: `http://localhost:8080/`
- Modern JSON API: `http://localhost:8080/api/orders`
- Login credentials: `admin / admin123`, `steve / steve`, `viewer / view`

### Local Node.js stack (alternative — uses SQLite, no Docker needed)

```bash
cd northwind/run/
python seed.py                  # Initialize SQLite DB
node proxy/proxy.js &           # Proxy on :8080
node modern/server.js &         # Modern API on :8082
python legacy_server.py         # Legacy on :8081
```

## Architecture

```
Browser → Proxy (:8080)
              ├─ /api/orders* → Modern layer (:8082 / modern PHP or Node.js)
              └─ /*           → Legacy layer (:8081 / PHP 5 or Python)
                                     │
                              Shared database (MySQL or SQLite)
```

**Proxy** (`northwind/proxy/nginx.conf` or `northwind/run/proxy/proxy.js`): routes by URL pattern. To migrate a route, add a location block here.

**Legacy** (`northwind/legacy/index.php`): single-file PHP 5 monolith — intentionally demonstrates SQL injection, session globals, no separation of concerns. The Python equivalent is `northwind/run/legacy_server.py`.

**Modern** (`northwind/modern/` or `northwind/run/modern/server.js`): two parallel implementations of the extracted API:
- PHP 8.2 with Slim 4, PHP-DI, PDO prepared statements, PSR-7 handlers
- Node.js with Express + better-sqlite3

**Database schema** (`northwind/legacy/schema.sql`): tables for `employees`, `customers`, `suppliers`, `products`, `orders`, `order_items`. Both layers query the same schema — no ORM used anywhere.

## Migrating a New Route

The playbook is in `northwind/MIGRATION.md`. Short version:

1. Build handler in `modern/src/Handler/` + repository method in `modern/src/Repository/OrderRepository.php`
2. Verify JSON response matches legacy output
3. Add the URL pattern to the proxy (`nginx.conf` or `proxy.js`)
4. After monitoring, delete the implementation from `legacy/index.php`

**Currently extracted**: `GET /api/orders`, `GET /api/orders/{id}`  
**Not yet migrated**: POST endpoints, customers, products, reports, auth middleware

## Key Files

| File | Purpose |
|------|---------|
| `northwind/MIGRATION.md` | Route migration checklist and architecture diagram |
| `northwind/docker-compose.yml` | Full-stack orchestration |
| `northwind/legacy/index.php` | PHP 5 monolith (intentionally vulnerable — do not "fix" SQL injection here) |
| `northwind/modern/public/index.php` | Slim 4 bootstrap + DI container setup |
| `northwind/modern/src/Handler/` | PSR-7 request handlers (one per route) |
| `northwind/modern/src/Repository/OrderRepository.php` | PDO data access with prepared statements |
| `northwind/run/modern/server.js` | Node.js equivalent of the modern API |
| `northwind/run/proxy/proxy.js` | Node.js proxy routing logic |

## Modern PHP Layer Conventions

- Constructor injection via PHP-DI (autowired) — add new dependencies to constructor, not via `new`
- Repository pattern: all SQL lives in `src/Repository/`, handlers call repositories only
- PSR-7 responses: return `$response->withJson(...)` or write to the response body
- Namespace: `Northwind\` (PSR-4, maps to `modern/src/`)

## Intentional Anti-Patterns in Legacy Layer

The legacy app deliberately contains SQL injection, `error_reporting(0)`, direct `$_SESSION` globals, and all logic in one file. This is by design for the demo — do not refactor or fix these unless the task is specifically migrating that functionality to the modern layer.
