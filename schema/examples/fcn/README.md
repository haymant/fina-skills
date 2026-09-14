# FCN MCP E2E example

This example uses the `ELIFCN_KI` sample instrument from `fina-risk/skills/fina-risk/refs/termsheet1.md.json` and executes the real local Python/MCP path.

## What it proves

The runner executes one real `pricing_and_sensitivity` MCP tool call for the quote and one for the event-triggered reprice. It then wires those results through the local FinA scheduler and trade adapter:

```text
quote → register_trade → amend
                     ↓ trade.lifecycle.amended
                 reprice → OLAP grouping
```

The verification requires a finished process, two real MCP pricing calls, durable amended trade state, an amendment lifecycle event, a finished reprice thread, and OLAP rows derived from the reprice result. It is not a JSON-schema-only check.

## Run

From the repository root, after installing the local FinA packages and their dependencies:

```bash
python schema/examples/fcn/run_fcn_mcp_e2e.py   --termsheet schema/examples/fcn/termsheet1.fcn.sample.json   --paths 128
```

The runner imports the local `fina-risk` FastMCP object and calls `mcp.call_tool("pricing_and_sensitivity", ...)` from Python. It does not replace a failed real pricing call with mock output.

The sample is copied from `fina-risk` revision `979fe0b` at the time this example was added. The source has three jobs; the example uses the full file so the tool exercises its native multi-job handling.
