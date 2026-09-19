---
name: finap-dev
description: Develop and maintain FinAP, the authenticated equity-derivatives application built from the TradeAC dashboard shell. Use for FinAP pages, schema-driven React rendering, flex-block workflows, trading and RiskCube flows, FinA MCP integration, lifecycle actions, and UI provenance.
---

# FinAP Development

## Mission

Build FinAP as a focused operator application for equity-derivative trading and risk. Preserve the TradeAC dashboard shell, authentication, theme system, accessible shadcn components, and server-side integration boundaries. Do not reintroduce unrelated TradeAC screens.

Read the relevant reference before changing a feature:

- `references/business-requirements.md` — product scope, required routes, and acceptance criteria.
- `references/ui-runtime-principles.md` — schema-driven React renderer, rich arrays, expandable objects, and flex-block workflows.
- `references/fin-a-boundaries.md` — product, model, process, lifecycle, evidence, and adapter boundaries.
- `references/fcn-leg-allocation-and-actions.md` — FCN Economics and Payoff Composition, generated funding/coupon/terminal legs, logical operation actions, and the developer handoff prompt.
- `../../refs/riskcube/finap-routes-and-actions.md` — singular RiskCube routes, page responsibilities, fina-table/stdio OLAP boundary, and action namespaces.
- `../../refs/riskcube/scenario-version-contract.md` — scenario/version lifecycle and immutable execution identity.
- `../../refs/riskcube/report-management.md` — risk, P&L, Taylor, and forecast report metadata and actions.
- `../../refs/riskcube/columnar-storage-and-olap.md` — RFK composite key, Hive Parquet layout, and cube query rules.
- `../../schema/ui/ui-metadata.schema.json` — canonical shape for pages, layouts, workflows, flex blocks, renderer hints, actions, and resources.
- `../../schema/ui/leg-allocation.schema.json` — canonical separation of editable FCN economics from generated leg allocation and pricing evidence.
- `../../schema/ui/operation-action.schema.json` — canonical operation-action contract for preconditions, lifecycle gates, refreshes, events, and evidence.
- `../../schema/ui/examples/fcn-rfq.ui.json` — minimal UI metadata fixture; validate it independently before wiring a page.

## Repository rules

1. Keep route-owned code beside its route under `src/app/(main)/<group>/<page>/`.
2. Keep shared dashboard shell code under `src/app/(main)/_components/`, shared UI under `src/components/`, and shared runtime code under `src/lib/`.
3. Keep the sidebar limited to the FinAP Trading and RiskCube route families.
4. Keep authentication and authorization on the server boundary. Never handle session cookies in client components.
5. Keep MCP calls behind server actions or a typed adapter. Do not call MCP servers directly from browser code.
6. Use precise TypeScript types. Replace `Record<string, unknown>` at feature boundaries with named contract envelopes as contracts stabilize.
7. Keep JSON Schema, UI metadata, workflow metadata, and action metadata separate. Do not put rendering rules into product schemas.
8. Treat client validation as early feedback. Backend validation remains authoritative for lifecycle, authorization, product semantics, market data, and pricing.
9. Use React Hook Form for form state and AJV for JSON Schema validation when implementing the renderer runtime.
10. Preserve provenance for pricing and risk operations: request ID, process ID, schema version, scenario scope, engine marker, and evidence status.

## Development environment (before `pnpm dev`)

MCP-server submodules live under `modules/` and are invoked over stdio from
server actions. Prepare the machine once, then start the app:

1. Check out submodules and app dependencies:
   ```bash
   git submodule update --init --recursive
   npm install
   ```
2. Copy `.env.example` to `.env` and fill in `TAC_LAKE_DIR` (lake root, e.g.
   `/home/data/lake`), `APCA_API_KEY_ID`/`APCA_API_SECRET_KEY`, `FRED_API_KEY`,
   and `TRADEAC_ENGINE_BIN`.
3. Build the fina-risk native module (needed by quote/risk pricing):
   ```bash
   cd modules/fina-risk
   uv venv .venv --python 3.12
   uv sync --all-groups --frozen --python 3.12
   uv pip install --python .venv/bin/python "pybind11==3.1.0"
   cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release \
     -DPYBIND11_FINDPYTHON=ON -DPython_EXECUTABLE=$PWD/.venv/bin/python
   cmake --build cpp/build -j2
   cp cpp/build/fina_risk_cpp.cpython-312-*.so .venv/lib/python3.12/site-packages/
   ```
   FinAP launches `uv run --project modules/fina-risk fina-risk-mcp`;
   `PYTHONPATH` defaults to `modules/fina-risk/src:modules/fina-risk/cpp/build`.
4. tac-engine: use the **GitHub release binary**, not a source build. Set
   `TRADEAC_ENGINE_BIN` to the installed binary (pulled from the
   `tac-engine-v0.1.0` release tarball, `/usr/local/bin/tac-engine` in the
   Coolify image). Only `cargo build --release` in `modules/tac-engine` when
   you are developing the engine itself — a full Rust compile is otherwise an
   avoidable cost and is never required for FinAP work.
5. fina-olap and fina-table are consumed as **published binaries**, not built
   here:
   - fina-olap (PyPI, `pip install fina-olap`) ships the `fina-olap-mcp` stdio
     server; deployment sets `FINA_OLAP_MCP_BIN=/usr/local/bin/fina-olap-mcp`.
     Local development falls back to `uv run --project modules/fina-olap
     fina-olap-mcp` (the checked-out repo is the same code that gets
     published). To change OLAP behaviour, work in the fina-olap repo, bump
     the version, then push a version tag and publish a GitHub Release — the
     release workflow publishes the PyPI wheel **and** the fina-table npm
     package.
   - fina-table (npm, `fina-table` in `package.json`) is the general-purpose
     SSRM grid shared across products; do not vendor it into FinAP source.
6. Start the app: `pnpm dev`.

MCP clients are per-process singletons: after editing env, submodule code, or
the native build, restart `pnpm dev` so servers relaunch with the new state.

## Required development loop

1. Read the applicable business requirement and FinA boundary reference.
2. Inspect the closest existing screen and shared component before coding.
3. Define or update the domain contract, report/data contract, leg-allocation contract, and operation-action metadata before adding product-specific UI logic.
4. Implement the smallest route-owned component that consumes the metadata.
5. Wire server actions through a logical operation or typed adapter.
6. Handle loading, empty, error, disabled, validation, and mobile states.
7. Validate UI metadata against `schema/ui/ui-metadata.schema.json`.
8. Run `pnpm check` and `pnpm build` before declaring the change complete.
9. Record new renderer patterns, process assumptions, or contract decisions in the appropriate reference.

For RiskCube, use `/riskcube/scenario`, `/riskcube/version`, `/riskcube/slice`, and `/riskcube/cube` as canonical routes; redirect the existing plural aliases. The cube page must query generated Parquet through the fina-olap stdio MCP adapter and render with `fina-table`, never with browser-side MCP or JSON-embedded measures.

## Renderer policy

Prefer a registered renderer over page-specific field branching. Support scalar fields, nested objects, rich arrays, schedules, read-only property grids, diagnostics, and flex blocks. Unknown renderer IDs must fail validation or show a visible fallback; never silently render an incompatible control.

## Workflow policy

Use flex blocks for semantic substructures such as underlying baskets, coupon schedules, protection, settlement, scenario manipulations, and review. A child flow edits a bound sub-object or array item and returns a validated value to its parent. The parent workflow owns final submission and action invocation.

## Action policy

Metadata describes user intent and invokes a registered logical operation. An action declares input schema, record binding, state preconditions, confirmation policy, process reference, refresh targets, expected events, and evidence requirements. The backend remains the authority for authorization and transition legality.
