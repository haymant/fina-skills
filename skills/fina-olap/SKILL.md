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

## Verification

Run Python unit/E2E tests, React unit tests, and demo/browser tests when UI behavior changes. Test filters, grouping, pivot, pagination, exports, object-store resolution, MCP transport, and path rewrites.

