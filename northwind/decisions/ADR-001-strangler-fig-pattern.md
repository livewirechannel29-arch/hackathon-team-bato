# ADR-001: Use Strangler Fig Pattern for Modernization

**Status:** Accepted  
**Date:** 2026-05-15

## Context

Northwind Logistics runs on a PHP 5 monolith (`legacy/index.php`) with SQL injection vulnerabilities, no separation of concerns, and no test coverage. A full rewrite carries high risk: long feature freeze, big-bang cutover, and no rollback path.

## Decision

Adopt the **Strangler Fig pattern**: route all traffic through a proxy, extract one route at a time to a modern service, and keep the legacy app running until it is fully replaced. Both apps share the same database schema throughout.

## Consequences

- **No feature freeze** — legacy keeps serving unextracted routes during migration
- **Rollback = one line** — comment out the proxy rule to revert any route instantly
- **No data migration** — shared schema eliminates sync complexity
- **Incremental risk** — each extraction is independently deployable and testable
- **Dual maintenance** — until a route is deleted from legacy, two implementations exist
