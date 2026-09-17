# RiskCube report management

## Scope

Use this reference for the data contract, catalog metadata, report lifecycle, and UI actions for **risk**, **P&L**, **Taylor decomposition**, and **forecast** reports. The canonical metadata contract is `schema/riskcube/report.schema.json`.

## Report types

| kind | Purpose | Typical value columns |
|---|---|---|
| `risk` | Point-in-time sensitivities and valuation | `pv_amount`, `price_pct`, `delta`, `gamma`, `vega`, `rho`, `theta`, named risk measures |
| `pnl` | Actual or hypothetical P&L across dates/scenarios | `pnl_total`, `pnl_market`, `pnl_time`, `pnl_fx`, `pnl_residual` |
| `taylor` | Explain P&L with first/second/higher-order terms | `taylor_1`, `taylor_2`, `taylor_cross`, `taylor_residual` |
| `forecast` | Forward risk/P&L projections | `forecast_value`, `forecast_lower`, `forecast_upper`, `forecast_error` |

A report metadata record names dimensions, measures, source version/scenarios, filters, status, and provenance. It is not the result payload.

## Data contract

Generated measures are **columns in Parquet/DuckDB**, never JSON fields and never a JSON array embedded in a catalog record. Every generated row has a composite RFK identity. The minimum RFK columns are `rfk_type`, `rfk_underlying`, `rfk_currency_pair`, `rfk_curve`, `rfk_expiry`, `rfk_strike`, `rfk_tenor`, `rfk_temporal_role`, `rfk_date`, and `rfk_surface_parameter`; nullable axes are allowed, but the complete normalized RFK tuple is the row key.

Keep dimensions and values typed. Do not serialize `sensitivities`, `pnl`, `taylor`, or `forecast` maps into JSON. If a dynamic measure is needed, register a new typed value column and bump the dataset schema version. JSON is allowed only for small provenance, filter, error, or source-reference metadata.

## Report lifecycle

`draft → running → ready → retired`; failures transition to `failed` and retain diagnostics. A report is ready only when the manifest, schema, partition inventory, row counts, nullability checks, RFK uniqueness checks, and version/scenario provenance all agree. Reports are immutable after ready; a changed query definition or measure set creates a new report key.

## Actions and UI behavior

Define actions with the existing `schema/ui/operation-action.schema.json` format. Recommended operations:

- `riskcube.report.create` — create a draft metadata definition;
- `riskcube.report.materialize` — execute a validated report against completed instances;
- `riskcube.report.refresh` — create a new immutable materialization, never overwrite ready data;
- `riskcube.report.get` / `.list` — inspect catalog and manifest metadata;
- `riskcube.report.retire` — hide a report from default selection without deleting data;
- `riskcube.report.export` — export the current filtered OLAP view, with provenance.

Actions must declare input/result schemas, report binding, lifecycle preconditions, idempotency key, refresh targets, expected events, and evidence requirement. Browser code calls server actions or typed adapters; it never calls MCP directly.

The UI should let users choose report kind, version, scenario set, dimensions, measures, and filters, then show status/provenance before rendering values. Loading, empty, partial/failed, permission-denied, and stale-report states must be explicit. A ready report opens in the OLAP table; details and decomposition views reuse the same query source.
