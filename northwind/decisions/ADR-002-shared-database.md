# ADR-002: Share Database Between Legacy and Modern Apps

**Status:** Accepted  
**Date:** 2026-05-15

## Context

During migration, both the legacy PHP 5 app and the modern layer need to serve live traffic. A separate database for the modern layer would require real-time data sync or a dual-write strategy.

## Decision

Both apps read and write the **same database schema** (`legacy/schema.sql`). No data migration is performed during route extraction. Schema changes are treated as a separate, coordinated project.

## Consequences

- Zero data migration effort during route extraction
- Schema changes must be backwards-compatible with both apps until legacy is fully retired
- No ORM on either side — raw SQL (with prepared statements on the modern side) keeps schema coupling explicit and visible
