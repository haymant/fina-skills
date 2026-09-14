---
name: fina-e2e-coordinator
description: FinA cross-repository verification of RFQ-to-OLAP flows, real handler wiring, event subscriptions, correlation, and failure reporting. Use for integration tests and release evidence.
---

# FinA E2E Coordinator

Use when a task crosses scheduler, pricer/risk, trade, ETL, or OLAP boundaries.

## Required path

1. Register real adapters.
2. Submit one process through the scheduler.
3. Execute `quote → register_trade → amend`.
4. Publish and consume `trade.lifecycle.amended`.
5. Execute `reprice → olap` from the event/dependency graph.
6. Assert durable state, event history, derived rows, correlation ids, and JSON-serializable results.

## Evidence standard

A valid pass proves the wiring, not merely terminal status. Require two real pricing calls, an amended durable trade, delivered subscription event, finished reprice, and OLAP output derived from reprice. Report the failed task, context keys excluding secrets, error, and whether the lifecycle event was published. Do not substitute mocks after a real integration failure.

Read [`schema/lambda-task.schema.json`](../../schema/lambda-task.schema.json) when validating task declarations and the scheduler chapter for process details. The standalone schema directory is canonical; do not maintain a second embedded copy.

