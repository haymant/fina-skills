# FinAP RiskCube routes and actions

## Route policy

Use singular canonical routes consistently:

| Canonical route | Responsibility |
|---|---|
| `/riskcube/scenario` | Scenario catalog, create/edit draft, inspect provenance, trigger runs |
| `/riskcube/version` | Immutable version catalog and instance inventory |
| `/riskcube/slice` | Reusable instrument population filters |
| `/riskcube/cube` | Report selection and OLAP exploration of generated datasets |

The existing mixed routes (`/riskcube/scenarios`, `/riskcube/versions`, `/riskcube/slice`, `/riskcube/cubes`) are compatibility aliases only. Redirect plural aliases to the singular route and do not add new links using plural names.

## Page responsibilities

**Scenario** lists stable keys, kind, version, base market-data time, repository snapshot, lifecycle state, and latest instances. Actions are create draft, edit draft, retire, and trigger. Trigger binds a version, scenario, slice, request hash, and batch key and reports the resulting instance.

**Version** lists stable version keys, status, engine/schema revisions, scenario count, instance count, row/cell count, and dataset manifests. It links to scenario and cube views but never edits a completed version.

**Slice** owns reusable instrument filters and preview counts. It is a selector for scenario/report execution, not a substitute for a version or report definition.

**Cube** selects a ready report and queries its Parquet dataset through the fina-olap stdio MCP adapter. It uses `fina-table` for server-side filtering, grouping, pivoting, aggregation, pagination, column selection, and export. It must show report/version/scenario provenance and a visible query state.

## UI/action metadata

Use `schema/ui/ui-metadata.schema.json` for page/layout/resource composition and `schema/ui/operation-action.schema.json` for operations. Keep page metadata separate from scenario/version/report domain schemas. Every action declares an input schema, result schema, record binding, preconditions, confirmation policy, idempotency path, refresh targets, events, and evidence requirement.

Server actions are the only browser boundary to fina-pricer and fina-olap. MCP tool names and command lines stay inside typed adapters. Authorization, lifecycle legality, and schema validation remain server-side.

## Required states and acceptance

Every page supports loading, empty, error, stale/failed, unauthorized, and mobile states. The cube page additionally handles missing manifest, no ready report, invalid dimension/measure selection, MCP timeout, DuckDB query error, and export failure. Refresh creates or reads immutable metadata; it never silently mutates a completed result.

The page names, action IDs, and resource IDs should be stable enough for navigation and audit events. Use `riskcube.scenario.*`, `riskcube.version.*`, `riskcube.slice.*`, and `riskcube.report.*` operation namespaces.
