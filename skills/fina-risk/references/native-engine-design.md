# Native C++ Engine Design for Payoff Coverage

## Goal

Use this guide when extending `fina-risk` to cover a Murex payoff-script requirement for FCN, ELI, RakiPlus, or another structured product. Translate economics into the canonical payoff graph first. Extend C++ only for semantics that the current native lane does not implement.

## Required architecture

Keep the layers distinct:

```text
Murex/Flex terms
→ canonical terms projection
→ payoff graph and lifecycle state
→ typed C++ kernel
→ pybind or stdio MCP adapter
→ typed result, leg allocation, and evidence
```

C++ owns pricing and risk math. Python owns orchestration, schema validation, ETL, and MCP transport. FinAP calls a logical server-side operation such as `quote.price`; it must not select a native library, call an arbitrary MCP tool, or use `fina_pricer_mcp_url` from browser code.

## Recommended source organization

Refactor the current monolithic kernel toward this structure without breaking the existing ABI:

```text
cpp/include/fina_risk/
  types.hpp
  terms.hpp
  observations.hpp
  state.hpp
  schedule.hpp
  indicators.hpp
  coupon.hpp
  barriers.hpp
  terminal_option.hpp
  funding.hpp
  settlement.hpp
  leg_result.hpp
  engine.hpp

cpp/src/fina_risk/
  schedule.cpp
  indicators.cpp
  coupon.cpp
  barriers.cpp
  terminal_option.cpp
  funding.cpp
  settlement.cpp
  engine.cpp
```

Keep `fina_risk_cpp.hpp` as a compatibility facade while introducing the focused headers. Keep pybind bindings thin. Keep MCP transport in Python or in the dedicated stdio adapter, never in payoff functions.

## Inline functions and performance

Yes, each feature or payoff branch can be a small `inline` function, provided it is a pure typed function and the hot loop does not perform dynamic work:

```cpp
inline bool in_range(double x, const Range& r) noexcept;
inline bool hits_ko(double indicator, const Barrier& b) noexcept;
inline void update_memory(State& s, const MemoryTerms& t, bool qualifies) noexcept;
inline double coupon_rate(const CouponTerms& t, const PeriodState& p) noexcept;
inline double terminal_residual(const TerminalTerms& t, const State& s, double performance) noexcept;
```

Use headers for short hot-path functions and `.cpp` files for parsing, schedule expansion, orchestration, and result assembly. Do not assume one giant translation unit is faster. Measure with release builds, link-time optimization where available, and the same path cube. Use `std::span`, contiguous arrays, pre-expanded schedules, and OpenMP around independent paths. Avoid JSON, strings, heap allocation, virtual dispatch, locks, and exceptions inside path-by-observation loops.

Use structure-of-arrays state for large batches when fields are processed column-wise. Preserve common random numbers for base, bump, and reprice. Treat `-ffast-math` as an optimization requiring conformance evidence, not as a semantic choice.

## Typed state and branch ordering

Separate immutable terms from mutable path state:

```cpp
struct Terms { /* normalized product inputs */ };
struct Observation { /* date, fixing, source, validity */ };
struct State {
    bool terminated;
    bool knock_in_seen;
    bool global_ko_seen;
    double unpaid_coupon;
    std::span<std::uint8_t> memory_locks;
};
```

Implement branch ordering in named functions. A typical order is schedule and fixing validation, memory updates, global/local KO precedence, coupon accrual, KI update, terminal residual, then settlement. Once terminated, later coupon and maturity nodes must not settle.

## Leg result contract

Return explicit legs rather than forcing callers to infer decomposition from aggregate fields:

```text
FUNDING
COUPON
PUT / Terminal Optionality
```

Each leg should carry a stable ID, role, PV, currency, payment schedule or cashflows, source term paths, payoff graph node, and origin (`compiled_payoff` or `pricing_engine`). The result should also carry state transitions, selected KO/KI branch, engine marker, process/request IDs, schema version, and evidence status.

## Conformance workflow

For every new branch:

1. Add or update the canonical terms and payoff graph node.
2. Add a readable reference-oracle fixture.
3. Add a native C++ unit fixture for the same state transition.
4. Compare each leg, cashflow, branch state, KO/KI date, and aggregate PV.
5. Test boundary equality, missing fixings, same-day event precedence, memory carry, and payment-date discounting.
6. Run the actual Python/stdio MCP E2E, not schema validation alone.
7. Record native engine marker, source revision, seed, paths, tolerances, and evidence manifest.

Classify coverage as `implemented_and_evidenced`, `implemented_but_not_evidenced`, `represented_but_not_implemented`, `unsupported`, or `ambiguous_in_source`.

## Stdio MCP target

The intended runtime path is:

```text
FinAP server action
→ stdio MCP client
→ fina-risk tool
→ ETL and terms projection
→ native C++ callable
→ typed quote/reprice result
→ leg allocation and evidence
```

Preserve the existing Python FastMCP orchestration and pybind ABI while adding a stable native operation for FCN quote/reprice. The stdio tool should accept a validated pricing request and return a typed result. It must not require the caller to reconstruct legacy `Chunk.Jobs` or infer which job is funding, coupon, or put.

## Developer-agent prompt

> Read `skills/fina-risk/SKILL.md`, `skills/fina-risk/references/backend-conformance.md`, `skills/fina-risk/references/native-engine-design.md`, `refs/MurexPlaybook/Products/Range_Accruals/payoff/raki-plus.md`, `refs/MurexPlaybook/Products/Range_Accruals/payoff/raki-plus-native-engine-methodology.md`, `model-registry/fcn.yaml`, and the canonical pricing/result schemas before coding.
>
> Study the current `fina-risk` repository. Preserve the existing native ABI and working parity lanes, but refactor the C++ implementation so FCN/RakiPlus payoff branches are organized into focused typed headers/source files for terms, observations, state, coupon, barriers, terminal optionality, funding, settlement, and result assembly. Keep small pure hot-path functions inline where justified. Keep JSON parsing, orchestration, MCP transport, and error-envelope construction outside the path × observation loop.
>
> Make the FCN RFQ-to-native-pricing path executable end to end. Accept the canonical FCN pricing request rather than requiring callers to infer legacy job positions. Compile terms into a typed FCN/RakiPlus representation, evaluate range accrual, fixed coupon, coupon barrier/memory, local/global KO precedence, KI state, terminal optionality, funding, payment-date discounting, and cash/physical settlement according to the documented contract. Mark unsupported or ambiguous branches explicitly instead of inventing behavior.
>
> Return explicit leg-level results for `FUNDING`, `COUPON`, and `PUT / Terminal Optionality`, together with cashflows, state transitions, selected branch, engine marker, source revision, request/process IDs, schema versions, and evidence status. Keep the reference/oracle lane and native lane separate and compare them on deterministic fixtures.
>
> Add unit and conformance fixtures for ordinary coupon, in-range and out-of-range days, coupon-memory release, local KO, global KO, same-day KO precedence, KI/no-KI maturity branches, memory KO locks, final fixing, payment-date discounting, physical-delivery flags, and boundary equality operators. Test missing-fixing and unresolved semantics explicitly.
>
> Add or update a thin stdio MCP tool/adapter in the existing Python FastMCP architecture. FinAP will call this logical operation through its authenticated server action; do not expose MCP credentials or tool selection to browser code and do not use `fina_pricer_mcp_url`. Ensure the tool executes the real native C++ lane, not a mocked or schema-only response.
>
> Benchmark before and after the refactor using identical path cubes, seeds, paths, observations, and compiler settings. Report throughput, allocation behavior, memory footprint, and numerical drift. Run C++ tests, Python tests, the real stdio MCP E2E, and the FCN evidence-manifest validator. Update the model registry only for capabilities that are actually implemented and evidenced. Report changed files, commands, engine marker, parity results, unresolved contract questions, and any assumptions.
