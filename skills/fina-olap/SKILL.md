---
name: fina-olap
description: FinA OLAP over local or object-store Parquet using DuckDB, ag-Grid SSRM, MCP/HTTP deployment, `fina-table`, and versioned risk reporting. Use for analytical queries, materialization, or table UI behavior.
---

# FinA OLAP

Use for analytical access to versioned risk/trade data. The OLAP boundary is columnar and query-oriented, not a substitute for lifecycle or pricing logic.

## Core flow

`SSRM request → validated schema → safe DuckDB SQL builder → source resolution → Parquet query → rows/metadata`.

Support local files and S3-compatible/GCS storage through explicit configuration. Keep object-store credentials out of requests and logs.

## UI and server

`fina-table` is a headless TanStack-based React library that emits ag-Grid-compatible SSRM requests with FinA extensions for grouping, pivot, aggregation, and level-of-detail. Keep request building, formatting, data source, and panel interactions separately testable.

The Python package exposes REST, MCP stdio/streamable HTTP, and a Vercel adapter. Treat each transport as a wrapper around the same engine.

## Version discipline

Join risk rows to trade/report manifests using explicit version anchors. Record query inputs, filters, grouping, source partitions, engine/model versions, and materialization time so a report can be reproduced.

For RiskCube data and report contracts, read [`../../refs/riskcube/report-management.md`](../../refs/riskcube/report-management.md) and [`../../refs/riskcube/columnar-storage-and-olap.md`](../../refs/riskcube/columnar-storage-and-olap.md). Generated sensitivities, P&L, Taylor, and forecast values must be typed Parquet/DuckDB columns, keyed by the normalized RFK composite key, with Hive partitioning; never query generated values from JSON blobs.

For `/riskcube/cube`, use the fina-olap stdio MCP adapter and the `fina-table` SSRM UX. Keep DuckDB paths, MCP commands, allowlists, and SQL generation server-side.

## Verification

Run Python unit/E2E tests, React unit tests, and demo/browser tests when UI behavior changes. Test filters, grouping, pivot, pagination, exports, object-store resolution, MCP transport, and path rewrites.

## Schema boundary

Risk and trade materializations use the reviewed contracts in [`schema/risk-cell.schema.json`](../../schema/risk-cell.schema.json), [`schema/pnl-explain.schema.json`](../../schema/pnl-explain.schema.json), and [`schema/storage-boundaries.schema.json`](../../schema/storage-boundaries.schema.json). RiskCube report metadata and dataset manifests use [`schema/riskcube/report.schema.json`](../../schema/riskcube/report.schema.json) and [`schema/riskcube/dataset-manifest.schema.json`](../../schema/riskcube/dataset-manifest.schema.json).
