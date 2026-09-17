# FinA architecture and MCP integration contract

## Canonical repository architecture

**FinAP** is the Next.js-based Financial Agent App for FinA. It is the user-facing entrypoint and owns page routing, server actions, typed adapters, authorization, action metadata, and UI composition. Browser code must call FinAP server actions or typed server adapters; it must not invoke MCP transports, spawn subprocesses, access credentials, construct SQL, or resolve data-lake paths.

**fina-risk** is the pricing and risk-cube OLAP server. It owns risk computation, sensitivity/P&L/Taylor/forecast report materialization, typed Parquet datasets, DuckDB-backed report validation, and report provenance. Its MCP surface is available over local stdio for colocated FinAP deployments and Streamable HTTP for remote deployments.

**fina-olap** is the analytics MCP server. It provides typed DuckDB-over-Parquet query tools, including SSRM-compatible row queries, schema inspection, aggregation, filtering, pivoting, sorting, pagination, and export-oriented result mapping. It supports both the `fina-olap-mcp` stdio CLI and Streamable HTTP.

**fina-trade** is the trade repository MCP server. It owns trade, instrument, RFQ, quote, and position repository operations. FinAP calls it through a server-side typed adapter using stdio in the colocated deployment and Streamable HTTP when remote.

**tac-engine** is the data-lake access service. It is not part of the risk/pricing domain and must not be changed for FinAP UI work. The canonical `haymant/tac-engine` repository is a Rust rmcp stdio server and exposes lake tools such as `get_lake_bars`, `get_lake_ta`, `get_lake_sp`, `get_lake_features`, `get_lake_status`, `get_lake_coverage`, and `get_lake_calendar`, plus market snapshot/option and macro tools. FinAP may add `tac-engine` as a submodule for reference while deploying its pinned release binary; the tac-engine source remains untouched.

**tradeac** and **fina-pricer** are legacy/reference systems. Use them to understand concepts and migration constraints only. Do not update them as part of FinAP, fina-risk, or fina-skills work unless the user explicitly asks.

## Deployment and transport boundary

The default deployment is one FinAP Docker container containing the FinAP app and the colocated MCP server submodules. The Next.js server layer invokes each MCP server through its stdio CLI. Every adapter must preserve a transport-neutral request model so the same typed call can be routed to Streamable HTTP later without changing page or action contracts.

Each MCP integration must have:

1. A server-only typed request/response contract.
2. A stdio client that handles MCP initialization, tool invocation, structured content, errors, timeout, and process cleanup.
3. A transport selector that defaults to stdio and supports an explicit Streamable HTTP endpoint for remote execution.
4. No browser exposure of commands, environment credentials, SQL, filesystem paths, or raw JSON-RPC.
5. Integration tests for tool-name mapping, request validation, response normalization, timeout/error handling, and empty results.

For `/trading/rfq`, entering an underlying symbol triggers server-side tac-engine calls. Spot is read from `get_stock_snapshot` using latest trade, daily close, then quote fallback. Volatility is read from the lake feature path when available and rendered as a percentage. Historical bars use bounded `get_lake_bars` requests. Treasury rates use the macro catalog and must leave the loading state after a bounded refresh attempt, displaying an explicit empty or error state when FRED data is unavailable.

FinAP is the orchestration boundary: authentication, action preconditions, idempotency, refresh targets, evidence requirements, and UI state belong in FinAP; domain computation and durable report storage belong in fina-risk; analytical querying belongs in fina-olap; repository persistence belongs in fina-trade.

## RiskCube product flow

The canonical RiskCube pages are singular:

- `/riskcube/scenario` — define and manage durable scenario definitions.
- `/riskcube/version` — inspect immutable report/version anchors.
- `/riskcube/slice` — define a reusable slice of the current instrument universe.
- `/riskcube/cube` — select a stored report and query its OLAP dataset through `risk-table`/fina-olap.

A user first defines a slice of the current instrument universe. A report trigger then pins the slice, evaluation date, market-data datetime, selected configuration group, report kinds, and engine/schema revisions. The report run receives a unique incremental integer `version_id`; the stable report identity should include a human-readable slice/report name plus an epoch timestamp integer, for example `rates-shock-1779105600`, while the database/report anchor retains the unique integer identifier.

Configuration groups are predefined, versioned selections of report components. At minimum support sensitivity, P&L, and Taylor subsets; forecast may be included when the selected engine configuration supports it. A report is immutable after ready. Re-running with changed inputs or configuration creates a new report/version and never overwrites stored data.

Generated values are never stored in JSON. fina-risk writes typed Parquet columns using the documented Hive partition convention; DuckDB validates and queries those datasets. The normalized RFK tuple is the composite risk-factor key. Every manifest must validate format, schema, row count, RFK uniqueness, partition inventory, checksums, source snapshot times, and provenance before publication.

## Action metadata

Actions use `schema/ui/operation-action.schema.json` and are grouped under:

- `riskcube.scenario.*`
- `riskcube.version.*`
- `riskcube.slice.*`
- `riskcube.report.*`

Each action declares input and result schemas, lifecycle preconditions, idempotency identity, refresh targets, emitted events, and evidence requirements. Failed runs preserve structured diagnostics and never publish partial datasets. Retiring metadata does not delete immutable Parquet data.

## Safety and ownership rules

Never modify `tac-engine`, `tradeac`, or `fina-pricer` for a FinAP RiskCube task. Add them as submodules only when their source is needed for colocated execution or reference. If a required feature is missing from fina-olap or fina-table, stop and ask before extending those repositories; prefer an adapter or existing tool first.
