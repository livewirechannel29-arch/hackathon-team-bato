# Architecture Notes

## System Diagram

```
                        ┌─────────────────────────────────────┐
Browser / API Client    │           Proxy  :8080               │
──────────────────────► │  Nginx (Docker) · http-proxy (local) │
                        └──────────┬────────────┬─────────────┘
                                   │            │
                  /api/orders*     │            │  /* (everything else)
                                   ▼            ▼
                        ┌──────────────┐  ┌──────────────────────┐
                        │ Modern :8082 │  │   Legacy  :8081       │
                        │              │  │                        │
                        │ PHP 8.2      │  │  PHP 5.6 / Python     │
                        │ Slim 4 + DI  │  │  Single-file monolith │
                        │ PDO prepared │  │  SQL injection (demo) │
                        │  statements  │  │  Session auth         │
                        └──────┬───────┘  └──────────┬───────────┘
                               │                     │
                               └──────────┬──────────┘
                                          │
                               ┌──────────▼──────────┐
                               │  Shared Database     │
                               │  MySQL 5.7 (Docker)  │
                               │  SQLite  (local dev) │
                               └─────────────────────┘
```

## Key Design Principles

### 1. Single Entry Point
All traffic enters through the proxy. Clients are unaware of which backend responds. This allows route ownership to transfer silently.

### 2. Shared Schema, No Sync
Legacy and modern apps query the same tables. No CDC, no event bus, no dual-write. Schema evolution is a separate concern gated on legacy retirement.

### 3. One Route at a Time
The migration checklist in `MIGRATION.md` tracks each route's extraction status and risk level. High-risk routes (state changes, auth) are extracted last.

### 4. Modern Layer is JSON API Only
The modern layer returns JSON; legacy still renders HTML. There is no UI rewrite in scope — the frontend remains coupled to legacy until all routes are extracted.

## Migration State (as of hackathon)

| Route | Method | Owner | Risk |
|-------|--------|-------|------|
| `/api/orders` | GET | Modern | Low ✓ |
| `/api/orders/:id` | GET | Modern | Low ✓ |
| `/api/orders` | POST | Legacy | Medium |
| `/api/orders/:id/ship` | POST | Legacy | High |
| `/api/customers` | GET/PUT | Legacy | Medium |
| `/api/products` | GET | Legacy | Low |
| `/api/reports` | GET | Legacy | Low |

## Auth Gap

The modern layer does **not yet validate sessions**. A middleware hook is registered in `modern/public/index.php` but not wired. This is acceptable while only GET endpoints are extracted — POST extraction must resolve this first.
