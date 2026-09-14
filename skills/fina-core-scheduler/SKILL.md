---
name: fina-core-scheduler
description: FinA process orchestration, dependency injection, event subscriptions, adapters, and MCP boundaries. Use when building or debugging FinaProcess workflows or event-triggered threads.
---

# FinA Core Scheduler

Use for process orchestration. Submit through the scheduler entrance; do not coordinate by directly calling handlers from a second ad-hoc path.

## Required workflow

1. Register adapters before process creation.
2. Declare the complete graph in one `FinaProcess`.
3. Express dependencies with `depends_on`; express dormant event work with `triggered_by`.
4. Subscribe lifecycle topics with `start_thread`.
5. Read dependency results through runtime APIs, never another handler’s mutable closure.
6. Publish lifecycle events only after durable mutation succeeds.
7. Verify behavior, correlation ids, JSON-serializable results, and event delivery.

## Canonical graph

`quote → register_trade → amend`; `trade.lifecycle.amended → reprice → olap`.

Read the repository’s `schema/fina-process.schema.json` and the existing scheduler implementation before changing YAML. The scheduler is transport-neutral. MCP registration must be proven by client configuration or a real call; do not infer it from handler names.

## Verification

Run the scheduler and wired process tests in `FinA`, then the coordinator E2E. Require exactly two real pricing calls, durable amended trade state, delivered amendment event, finished reprice, and OLAP rows derived from reprice output.

## Canonical schemas

Use [`schema/fina-process.schema.json`](../../schema/fina-process.schema.json) for process definitions and [`schema/etl.schema.json`](../../schema/etl.schema.json) for ETL pipeline declarations.
