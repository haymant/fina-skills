# FinA Skills

An agent skill book for the FinA equity-derivative trading ecosystem. Load [`skills/fina-index/SKILL.md`](skills/fina-index/SKILL.md) first; it routes work to the master architecture chapter and focused implementation chapters.

## Structure

- `skills/fina-master` — architecture, principles, ADR routing, and non-goals
- `skills/fina-index` — task routing and repository map
- `skills/fina-core` — shared semantics and contracts
- `skills/fina-core-scheduler` — process orchestration and event subscriptions
- `skills/fina-etl` — street and bulk data lanes
- `skills/fina-trade` — lifecycle and durable events
- `skills/fina-risk` — pricing, risk, and backend conformance
- `skills/fina-olap` — Parquet/DuckDB, SSRM, MCP, and `fina-table`
- `skills/fina-e2e-coordinator` — cross-repository verification

The chapters intentionally contain operational knowledge and links, not vendored source code. Source evidence is drawn from `FinA` revision `7818a28` and the public sibling repositories available during this bootstrap. The `tradeac` checkout was unavailable without GitHub authentication and is therefore not treated as verified evidence.

## Maintenance

When a repository contract changes, update the owning chapter, its references, and the index routing table in the same change. Add conformance or E2E evidence before marking a capability as implemented.
