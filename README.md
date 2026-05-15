# Team Bato

## Participants

- rolando.d.de.guzman
- jyrus.d.carrasco
- kenneth.abad
- jake.r.necio

## Scenario

Scenario 1: Code Modernization

## What We Built

**Northwind Logistics** — a working demo of the Strangler Fig pattern applied to a PHP 5 monolith. A proxy layer routes traffic between the legacy app and a modern JSON API. Both run simultaneously against the same database. No cutover. No data migration. No feature freeze.

```
Browser → Proxy (:8080)
              ├─ /api/orders* → Modern layer  (PHP 8.2 / Node.js)
              └─ /*           → Legacy layer  (PHP 5 / Python)
                                      │
                               Shared database (MySQL / SQLite)
```

## Challenges Attempted

| # | Challenge | Role | Status |
|---|-----------|------|--------|
| 1 | **The Stories** | PM | Completed — user stories with acceptance criteria in `/decisions` |
| 2 | **The Patient** | Architect | Completed — PHP 5 monolith: SQL injection, God class, session globals, zero separation |
| 3 | **The Map** | Architect | Completed — Strangler Fig decomposition plan, seam identification, risk ranking in `MIGRATION.md` |
| 5 | **The Cut** | Dev | Completed — `GET /api/orders` and `GET /api/orders/:id` extracted; monolith still serves all other routes |
| 6 | **The Fence** | Dev | Completed — modern layer uses its own repository/handler pattern; legacy data model does not leak |

## Key Decisions

**Strangler Fig over big-bang rewrite** — incremental extraction keeps the legacy app live throughout. Rollback is one commented line in the proxy config. Full rationale: [ADR-001](northwind/decisions/ADR-001-strangler-fig-pattern.md)

**Shared database, no sync** — both apps query the same schema. Eliminated the need for CDC, dual-write, or event sourcing during extraction. Full rationale: [ADR-002](northwind/decisions/ADR-002-shared-database.md)

**Proxy-based route demux** — Nginx (Docker) and Node.js http-proxy (local) both sit on :8080. Adding a migrated route = one location block. Full rationale: [ADR-003](northwind/decisions/ADR-003-proxy-routing.md)

See [`northwind/decisions/`](northwind/decisions/) for all ADRs and the full [architecture diagram](northwind/decisions/ARCHITECTURE.md).

## How to Run It

**Docker (full stack — MySQL + PHP legacy + PHP modern + Nginx):**
```bash
docker compose run --rm modern composer install
cd northwind && docker compose up
```

**Local (SQLite, no Docker needed):**
```bash
cd northwind/run/
python seed.py
node proxy/proxy.js &
node modern/server.js &
python legacy_server.py
```

- Legacy HTML UI: `http://localhost:8080/` — login `admin / admin123`
- Modern JSON API: `http://localhost:8080/api/orders`
- Modern orders UI: `http://localhost:8082/` (local stack only)

## If We Had Another Day

1. **Wire auth middleware** — the modern layer has the hook registered but not enforced; POST endpoints can't be safely extracted without it
2. **Extract `POST /api/orders`** — next highest-value route; blocked on auth
3. **Characterization tests** — pin legacy behavior before extracting more routes (Challenge 4: The Pin)
4. **Contract tests** — verify modern API response shape matches legacy output on every extraction (Challenge 7)
5. **CI/CD pipeline** — independent build/deploy for legacy and modern so one failing doesn't block the other (Challenge 8)

The auth gap is the honest piece held together with tape — GET routes are safe without it, but POST extraction needs it resolved first.

## How We Used Claude Code

**What worked:**
- Generated the entire modern PHP handler/repository layer from the legacy SQL queries in one pass — saved ~2 hours of scaffolding
- Wrote the Nginx proxy config and Node.js proxy routing logic from the architecture description alone
- Produced `MIGRATION.md`, the ADRs, and this README faster than any of us could have typed them

**What surprised us:**
- Claude correctly identified the auth gap and flagged it as a blocker for POST extraction without being asked
- It refused to "fix" the SQL injection in the legacy layer once we explained it was intentional — respected the constraint

**Where it saved the most time:**
- The `CLAUDE.md` file meant every new session had full context immediately — no re-explaining the architecture or the intentional anti-patterns

See [`CLAUDE.md`](CLAUDE.md) for the full guidance file we used.
