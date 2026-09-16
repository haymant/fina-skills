# FinA Boundaries for FinAP

| Layer | Responsibility | UI relationship |
|---|---|---|
| Product semantics | Defines instrument meaning and terms. | Reference the contract and render fields. |
| ETL | Augments, compiles, and persists canonical representations. | Show process status and result references. |
| Model wiring | Maps products to models, engines, market data, and risk profiles. | Display capability; never select engines by client convention. |
| Process | Orchestrates dependencies, tools, lifecycle, and outputs. | Invoke declared processes and show status. |
| Lifecycle | Defines legal states, transitions, events, and operations. | Offer actions with preconditions; backend is authoritative. |
| Pricing | Produces quote/reprice results from an explicit request. | Render results and provenance. |
| RiskCube/OLAP | Stores and queries scenario/version-scoped results. | Declare dimensions, measures, scope, and read-only capability. |
| Evidence | Proves execution and engine conformance. | Surface engine marker, process ID, request ID, and status. |

## Adapter boundary

The browser calls FinAP server actions. Server actions authenticate the user, validate input, resolve a logical operation, call the configured MCP adapter, normalize the result envelope, and return typed data. Do not expose MCP URLs, credentials, transport sessions, or arbitrary tool selection to browser code.

## Trading flow

```text
RFQ source → terms projection → ETL augment → ETL compile
→ pricing request → native quote/reprice → quote persistence or trade acceptance
→ lifecycle event → OLAP/RiskCube evidence
```

The UI may expose these as separate steps or linked pages, but must not collapse them into one ambiguous submit action.

## RiskCube flow

```text
scenario definition → version/snapshot selection → slice/population selection
→ scenario trigger process → version × scenario partition → read-only OLAP exploration
```

Scenario definition and execution are different actions. Cube results retain partition scope and provenance.

## Evidence and lifecycle

For production pricing or risk actions preserve request ID, process ID, input contract/version, source or registry revision, scenario/version scope, engine marker, result schema, events, and evidence manifest status. Schema validation alone is not production evidence.

Metadata describes an expected transition but cannot authorize it. The backend validates state, actor capability, reason requirements, idempotency, and legality. Refresh the record and lifecycle timeline after success.
