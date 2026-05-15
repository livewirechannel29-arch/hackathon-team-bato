# ADR-003: Proxy-Based Route Demux (Nginx / Node.js http-proxy)

**Status:** Accepted  
**Date:** 2026-05-15

## Context

The Strangler Fig pattern requires a single entry point that can route requests to either the legacy or modern app based on URL pattern, without clients knowing which backend responds.

## Decision

A **proxy layer** (Nginx in Docker Compose; Node.js `http-proxy` for local dev) sits on port 8080 and forwards:
- `/api/orders*` → modern app (:8082)
- `/*` (everything else) → legacy app (:8081)

Adding a new extracted route = one new location block in `nginx.conf` (or one `if` in `proxy.js`). Rollback = comment it out.

## Alternatives Considered

- **Feature flags inside legacy app**: would require modifying the monolith for every extraction; ruled out
- **DNS-level routing**: too coarse-grained for per-route control; ruled out

## Consequences

- Clients always hit one URL — no redirect or API versioning required
- Two proxy implementations (Nginx + Node.js) are maintained in parallel for demo flexibility
- Proxy becomes a single point of failure; mitigated by its stateless, configuration-only nature
