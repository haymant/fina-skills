# Dev-agent prompt: build FinAP RiskCube functionality

Work in the FinAP/FinA repositories using the updated `fina-skills` contracts. Build the RiskCube functionality end to end; do not copy the `fina-pricer` POC. Treat it as a reference for lifecycle ideas only.

## Read first

- `schema/riskcube/scenario.schema.json`
- `schema/riskcube/version.schema.json`
- `schema/riskcube/report.schema.json`
- `schema/riskcube/dataset-manifest.schema.json`
- `refs/riskcube/scenario-version-contract.md`
- `refs/riskcube/report-management.md`
- `refs/riskcube/columnar-storage-and-olap.md`
- `refs/riskcube/finap-routes-and-actions.md`
- `skills/finap-dev/SKILL.md`
- `skills/fina-olap/SKILL.md`

## Requirements

1. Make `/riskcube/scenario`, `/riskcube/version`, `/riskcube/slice`, and `/riskcube/cube` the canonical routes. Redirect `/riskcube/scenarios`, `/riskcube/versions`, and `/riskcube/cubes` to their singular counterparts. Update navigation and internal links to singular names.
2. Implement typed scenario/version/report/dataset-manifest contracts and validate them on the server. Keep stable keys separate from numeric catalog identifiers. Enforce immutable completed versions, scenarios, instances, ready reports, and generated partitions.
3. Support report kinds `risk`, `pnl`, `taylor`, and `forecast`. Keep report metadata separate from generated data and UI metadata.
4. Generate typed columnar Parquet datasets queried by DuckDB. Do not store generated sensitivity, P&L, Taylor, or forecast values in JSON. Use the normalized RFK tuple as the composite risk-factor key and Hive partitioning with the documented path convention. Add manifest validation for schema, row counts, RFK uniqueness, partition inventory, and provenance.
5. For `/riskcube/cube`, use the `fina-olap` stdio MCP server through a server-side typed adapter. Pass allowlisted report views and structured SSRM requests; never expose MCP commands, DuckDB paths, credentials, or arbitrary SQL to the browser.
6. Render the cube with `fina-table`, supporting server-side filtering, sorting, grouping, pivoting, aggregation, pagination, column selection, and export. Display report/version/scenario provenance and explicit loading, empty, stale, failed, unauthorized, timeout, and export-error states.
7. Implement action metadata and server actions under namespaces `riskcube.scenario.*`, `riskcube.version.*`, `riskcube.slice.*`, and `riskcube.report.*`. Include input/result schemas, lifecycle preconditions, idempotency, refresh targets, events, and evidence requirements. Browser components call server actions only.
8. Preserve slice behavior as reusable instrument population selection. A slice is not a version, scenario, report, or data partition.
9. Add tests for schema validation, lifecycle immutability, idempotent triggers, RFK composite-key uniqueness, no-generated-values-in-JSON, Hive path resolution, fina-olap stdio query mapping, SSRM table behavior, singular-route redirects, and failure/empty states.
10. Run repository type checks, unit tests, build, and relevant integration tests. Report changed files, test commands/results, route compatibility behavior, and any unresolved dependency or connector assumptions.

## Delivery constraints

Do not silently migrate or delete old data. Do not rewrite completed partitions. Do not invent market data for current-market scenarios. If an existing POC stores sensitivity JSON, add an explicit migration/compatibility reader only if needed, but make all new writes conform to the columnar contract.
