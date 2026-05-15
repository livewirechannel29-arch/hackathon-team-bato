# Northwind Logistics — Modernization Playbook

## The Constraint

We cannot rewrite the whole system. Orders are going out. Any strategy that requires
a cutover weekend, a data migration, or a feature freeze is off the table.

## The Pattern: Strangler Fig

A strangler fig wraps an existing tree, branch by branch. One day the host tree
is gone and the fig is standing on its own. We do the same thing with routes.

```
Browser
   │
   ▼
Nginx proxy  ──  /api/orders  ──▶  Modern PHP 8 app ─┐
   │                                                   ├── Same MySQL DB
   └──────────────  /*  ─────────▶  Legacy PHP 5 app ─┘
```

Both apps share the same database and schema. No data migration. No freeze.
The proxy decides which app owns each URL. Legacy handles everything until you
deliberately move a route. You move routes one at a time, on your schedule.

---

## How to Run It

```bash
# 1. Install modern dependencies
docker compose run --rm modern composer install

# 2. Start everything
docker compose up

# 3. Legacy app  →  http://localhost:8080/         (login: admin / admin123)
#    Modern API  →  http://localhost:8080/api/orders
#                   http://localhost:8080/api/orders/1
```

---

## Migration Checklist

Move a route by:
1. Building it in `modern/src/`
2. Checking that the response matches what legacy returned
3. Uncommenting the `location` block in `proxy/nginx.conf`
4. Watching logs for one business day
5. Deleting the code from `legacy/index.php`

| Route                      | Status       | Risk   | Notes                          |
|----------------------------|--------------|--------|--------------------------------|
| `GET  /api/orders`         | ✅ Extracted | Low    | Filter by status / customer    |
| `GET  /api/orders/:id`     | ✅ Extracted | Low    | Includes line items            |
| `POST /api/orders`         | Backlog      | Medium | Needs auth middleware first    |
| `POST /api/orders/:id/ship`| Backlog      | High   | State change — test carefully  |
| `GET  /api/customers`      | Backlog      | Low    | —                              |
| `PUT  /api/customers/:id`  | Backlog      | Medium | —                              |
| `GET  /api/products`       | Backlog      | Low    | —                              |
| `GET  /api/reports`        | Backlog      | Low    | Extract last — low change rate |

---

## What Changed Between Legacy and Modern

| Concern            | Legacy (`index.php`)                         | Modern (`src/`)                                 |
|--------------------|----------------------------------------------|-------------------------------------------------|
| SQL                | String concatenation, SQL injection risk     | PDO prepared statements, named parameters       |
| Auth               | `$_SESSION['uid']` globals checked inline    | Middleware (not yet wired — add before POST routes) |
| Error handling     | `error_reporting(0)`, silent failures        | Exceptions propagate, Slim error middleware     |
| Output             | Mixed HTML + PHP                             | JSON, PSR-7 responses                          |
| Database driver    | `mysql_*` (removed in PHP 7)                 | PDO (PHP 5.1+, still current)                  |
| Structure          | One 300-line file                            | Repository + Handler, autowired DI             |

---

## What We Deliberately Did Not Do

- **Schema migration.** The schema is shared. Changing it is a separate project
  with its own risk surface. Do it after the code is clean.
- **Port the HTML UI.** The legacy HTML still runs. A frontend rewrite can happen
  independently once the API layer is solid.
- **Rewrite everything at once.** The reports page changes twice a year.
  Extracting it carries more risk than it saves. Leave it in legacy indefinitely
  if that's the right call.

---

## Definition of Done

When `legacy/index.php` is empty (or deleted), the strangler has fully replaced
the host. At that point:

- Drop the `legacy` container and its PHP 5 image
- The proxy becomes optional (repurpose for load balancing or remove)
- Consolidate DB credentials into proper secrets management
