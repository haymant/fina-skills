# FCN Example: Source to Product to Process to Evidence

This example is intentionally split into five boundaries, following the Murex product-development paradigm without pretending that `FinaProcess` is the product definition.

```text
legacy term sheet
  → semantic terms projection
  → canonical payoff graph
  → compiled pricing request
  → native pricing result
  → executable FinaProcess
  → lifecycle and OLAP evidence
```

The **canonical payoff graph** ([`pricing/payoff-graph.example.json`](pricing/payoff-graph.example.json)) is the
explicit compiled-pricing bridge between the semantic terms and the engine request. It is a typed DAG of
payoff nodes, gates, legs, schedule, lifecycle, and C++ kernel bindings, emitted by fina-core's
`compile_payoff_graph` and lowered to `FcnTerms` and the compiled `pricing-request` shape (see
`modules/fina-core/python/fina_core/payoff.py` and [`payoff-graph.schema.json`](../../payoff-graph.schema.json)).

## Directory map

| Directory | Role | Contract |
|---|---|---|
| [`source/`](source/) | Legacy `Chunk → Jobs → commonData` input copied from `fina-risk` | [`schema/fcn-legacy-termsheet.schema.json`](../../fcn-legacy-termsheet.schema.json) |
| [`terms/`](terms/) | Explicit semantic projection used to explain product meaning | [`schema/fcn-terms-projection.schema.json`](../../fcn-terms-projection.schema.json) |
| [`etl/`](etl/) | Real MCP `augment` and `compile` outputs captured from the E2E | [`schema/fcn-etl-result.schema.json`](../../fcn-etl-result.schema.json) |
| [`pricing/`](pricing/) | Compiled payloads: canonical payoff graph, engine request, and native quote/reprice payloads | [`schema/payoff-graph.schema.json`](../../payoff-graph.schema.json), [`schema/pricing-request.schema.json`](../../pricing-request.schema.json), [`schema/fcn-native-pricing-result.schema.json`](../../fcn-native-pricing-result.schema.json) |
| [`process/`](process/) | Executable scheduler graph | [`schema/fina-process.schema.json`](../../fina-process.schema.json) |
| [`lifecycle/`](lifecycle/) | State, event, transition, fixing, and operation contracts | The five `fcn-*.schema.json` lifecycle schemas |
| [`evidence/`](evidence/) | Human-readable run/evidence notes | Runtime manifest is written outside the repository by default |

## What the sample is—and is not

[`source/termsheet1.fcn.sample.json`](source/termsheet1.fcn.sample.json) is a **legacy pricing-engine source fixture**. It conforms to `fcn-legacy-termsheet.schema.json`; it is not a `ProductTerms` object and it is not a `PricingRequest`.

[`terms/fcn-terms-projection.example.json`](terms/fcn-terms-projection.example.json) is the explicit semantic bridge. It documents the product family, legs, economics, schedule, features, settlement, and source job references. It is a migration/example contract pending final shared `ProductTerms` ownership and version freeze.

[`pricing/pricing-request.example.json`](pricing/pricing-request.example.json) is the actual request captured from the real `run_etl_task(mode="compile")` call. It validates against the canonical `schema/pricing-request.schema.json`.

The native result fixtures are captured from the compiled `fina_risk_cpp.run_daily_termsheet` call. Both quote and reprice carry the engine marker `cpp_daily_termsheet_eki` and validate against `fcn-native-pricing-result.schema.json`.

## FinaProcess in the Murex-style picture

Murex separates product configuration from the executable delivery/runtime wiring: product economics and feature blocks define what the product means; model/GMP configuration defines how it is valued; operational workflows define how it is fixed, settled, and supported.

FinA should preserve the same separation:

| FinA artifact | Murex-style role | Question answered |
|---|---|---|
| Terms projection and eventual `ProductTerms` | Product definition / feature configuration | What is the FCN payoff and its supported constraints? |
| `model-registry/fcn.yaml` | Product → model → risk → operations dictionary | Which model, backend, profiles, calendars, and evidence gates apply? |
| `pricing-request.example.json` | C++/model mapping DTO | What exact typed input reaches the pricing engine? |
| `process/fcn-etl-to-olap.process.json` | Executable operational recipe | In what dependency/event order do ETL, quote, trade, reprice, and OLAP run? |
| Lifecycle schemas | Market-operation and settlement contracts | What states, fixing records, events, and operations are valid? |
| Evidence manifest | Fixed-point/UAT/release evidence | What proves the configured product and process actually worked? |

`FinaProcess` is therefore **not** the canonical product model and should not contain the full payoff definition. It is the executable orchestration layer that consumes typed terms/pricing contracts and starts the right handlers in the right dependency and event order. One product may have multiple processes: interactive quote, booking, fixing-day operation, EOD risk, and expiry/settlement.

## Run and verify

The offline contract chain can be checked without services:

```bash
python schema/examples/fcn/verify_fcn_examples.py
python schema/examples/fcn/pricing/verify_payoff_graph.py
python schema/examples/fcn/lifecycle/verify_lifecycle.py
```

`verify_payoff_graph.py` re-runs `compile_fcn_graph_and_lower` on the projection, legacy term-sheet, and market
fixtures and asserts the emitted graph is byte-identical to the checked-in example (`graph_hash`), that the
`payoff_script` and `function_bindings` explain the fina_risk_cpp function organization, and that the lowered
`pricing_request` still conforms to the canonical request schema.

The real service-backed E2E is:

```bash
PYTHONPATH=../FinA/python:../fina-risk/src:../fina-trade:../fina-risk/cpp/build \
python schema/examples/fcn/run_fcn_mcp_e2e.py \
  --termsheet schema/examples/fcn/source/termsheet1.fcn.sample.json \
  --count 1 \
  --paths 128 \
  --seed 42 \
  --artifacts-dir schema/examples/fcn/pricing \
  --manifest /tmp/fina-evidence/fcn/latest-run.json
```

The runner validates the registry and lifecycle fixtures before creating the process. It captures the real ETL and native pricing payloads, then validates the evidence manifest after the process finishes.
