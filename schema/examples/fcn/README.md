# FCN MCP E2E example

This example uses the `ELIFCN_KI` sample instrument from `fina-risk/skills/fina-risk/refs/termsheet1.md.json` and executes the real local Python/MCP path. The process definition is [`fcn-etl-to-olap.process.json`](fcn-etl-to-olap.process.json) and conforms to the standalone `fina-process.schema.json`.

## What it proves

The runner starts from the copied legacy term sheet and executes both ETL stages through the real `run_etl_task` MCP tool before pricing. The resulting scheduler graph is:

```text
augment → compile → quote → register_trade → amend
                                      ↓ trade.lifecycle.amended
                                  reprice → OLAP grouping
```

The verification requires a schema-valid process, two real MCP ETL calls, two real MCP pricing calls, durable amended trade state, an amendment lifecycle event, a finished reprice thread, and OLAP rows derived from the reprice result. It is not a JSON-schema-only check.

## Run

From the repository root, after installing the local FinA packages and their dependencies:

```bash
python schema/examples/fcn/run_fcn_mcp_e2e.py \
  --termsheet schema/examples/fcn/termsheet1.fcn.sample.json \
  --count 1 \
  --paths 128
```

The runner imports the local `fina-risk` FastMCP object and calls `mcp.call_tool("run_etl_task", ...)` for augmentation and compilation, followed by `mcp.call_tool("pricing_and_sensitivity", ...)` for quote and reprice. It does not replace a failed real call with mock output.

The sample is copied from `fina-risk` revision `979fe0b` at the time this example was added. The source has three jobs; the example uses the full file so the tool exercises its native multi-job handling.
