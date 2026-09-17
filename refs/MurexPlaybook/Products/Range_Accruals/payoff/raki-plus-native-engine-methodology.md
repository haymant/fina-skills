# RakiPlus-to-Native-Engine Methodology

## Purpose

This chapter defines how to turn a Murex payoff-script requirement into executable FinA semantics without translating Murex script syntax line by line into C++. It applies directly to FCN and ELI products whose economics are based on RakiPlus or MemRakiPlus.

The governing sequence is:

```text
Murex terms and payoff-script behavior
        ↓
canonical payoff graph and lifecycle contract
        ↓
ETL projection and pricing request
        ↓
native C++ pricing/risk kernel
        ↓
leg-level result and evidence manifest
```

The Murex script remains the source of product behavior. The canonical graph is the shared semantic contract. C++ is one optimized execution backend.

## What must and must not be translated

Do not reproduce Murex script syntax, Flex UI structure, or internal naming as the C++ design. Translate only observable economic behavior:

| Source concern | Canonical representation | Native implementation |
|---|---|---|
| Coupon barrier | Predicate over fixing and period state | Inline predicate over a compact state record |
| Memory coupon | Unpaid balance plus release transition | Scalar/vector state update |
| Local/global KO | Event predicates with precedence | Branch-specific state transition |
| KI | Persistent observation state | Terminal or pathwise gate |
| Funding | Principal and settlement node | Discounted cashflow component |
| Terminal put/residual | Explicit payoff node | Payoff function over normalized performance |
| Murex Flex block | Terms projection path | Typed input field or compiled parameter |
| Payoff script | Graph and feature contract | Kernel function set plus evidence mapping |

If a Murex behavior is undocumented, mark it as ambiguous and require a configuration fixture or parity test. Never fill the gap with a convenient default merely because it is easy to code.

## FCN/RakiPlus payoff graph

The FCN graph should preserve the explicit economic decomposition:

```text
FCN / ELI
├── FUNDING
│   └── principal return at maturity or authorized early termination
├── COUPON
│   ├── range-accrual count N1/N2
│   ├── fixed coupon
│   ├── coupon barrier
│   ├── unpaid memory balance
│   └── local/global KO coupon
└── PUT / TERMINAL OPTIONALITY
    ├── KI gate
    ├── basket performance selector
    ├── strike and participation
    ├── cap/floor
    └── cash or physical settlement
```

Each node should have a stable identifier, input term paths, lifecycle dependencies, output currency, and an evidence status. The result should expose at least Funding, Coupon, and PUT/Terminal Optionality legs. The terminal leg must not be labelled a standalone vanilla put unless the product contract proves that interpretation.

## Feature coverage matrix

Before extending C++, build a matrix with one row per feature branch:

```text
feature → source terms → graph node → lifecycle state → C++ function
        → oracle fixture → native result field → evidence check
```

Classify every row as `implemented_and_evidenced`, `implemented_but_not_evidenced`, `represented_but_not_implemented`, `unsupported`, or `ambiguous_in_source`. Only the first category is production evidence.

For the current FCN lane, the known native path already exposes a daily lifecycle entrypoint, worst-of terminal optionality, range fixing counts, unpaid memory carry, global KO gating, payment-date discounting, and central-bump delta/gamma. This is evidence of an existing foundation, not proof that the complete RakiPlus feature set is covered. Memory KO, full RakiPlus terminal branches, physical delivery, and leg-level reconciliation must be checked independently.

## State-machine design

Separate immutable terms from mutable path or lifecycle state.

```cpp
struct Terms { /* normalized product inputs */ };
struct Observation { /* fixing, date, source, validity */ };
struct State {
    bool terminated;
    bool knock_in_seen;
    bool global_ko_seen;
    double unpaid_coupon;
    std::vector<std::uint8_t> memory_locks;
};
```

A path or fixing step should update state exactly once. Keep event precedence explicit. For example, if the product contract gives global KO priority over local KO on the same date, implement that priority in one named transition function and test it directly.

## C++ organization and performance

Splitting each feature into small functions is compatible with high performance when the functions are pure, typed, and visible to the optimizer. The recommended organization is:

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

cpp/bindings/
  fina_risk_pybind.cpp

cpp/apps/
  daily_termsheet.cpp
  e2e_benchmark.cpp
```

Use headers for small, pure `inline` functions that are genuinely on the hot path. Use `.cpp` files for parsing, orchestration, result assembly, and larger algorithms. Do not put the whole product in one translation unit merely to obtain inlining; link-time optimization and compiler optimization can inline across translation units when configured.

A hot path should look like:

```cpp
inline double range_coupon(const Terms& t, const PeriodState& p) noexcept;
inline bool hits_upper_barrier(double indicator, const Barrier& b) noexcept;
inline bool hits_lower_barrier(double indicator, const Barrier& b) noexcept;
inline void apply_memory_coupon(State& s, const CouponTerms& c, bool qualifies) noexcept;
inline Event apply_ko_precedence(State& s, const BarrierObservation& o) noexcept;
inline double terminal_residual(const Terms& t, const State& s, double performance) noexcept;
```

Avoid JSON access, heap allocation, virtual dispatch, string comparison, logging, and exception construction inside path × observation loops. Parse JSON once into typed terms. Pre-expand schedules and masks. Store state in contiguous arrays when pricing many paths. Use branchless `std::max`/`std::min` or masks where it improves measured throughput, but retain a readable scalar reference implementation for conformance.

Prefer a structure-of-arrays layout for large path batches when the same state field is processed across paths. Prefer small value types and `std::span` for non-owning views. Use OpenMP or another parallel layer around independent paths, not locks inside payoff functions. Preserve common random numbers for base, bump, and reprice calculations.

Do not use `-ffast-math` as a substitute for a numerical contract. Record compiler flags, floating-point tolerances, seed, path count, and source revision in evidence. Any fast-math optimization must pass the conformance corpus.

## Two implementation lanes

Maintain two executable lanes with the same terms and graph:

1. **Reference lane.** A readable Python or scalar C++ interpreter used to define expected state transitions, cashflows, and leg decomposition.
2. **Native lane.** A vectorized or parallel C++ kernel used for production evidence and performance.

The reference lane is not the production hot path. The native lane is not allowed to silently redefine semantics. Compare PV, each leg, cashflows, state transitions, KO/KI dates, and selected Greeks.

## MCP and stdio boundary

The native C++ library should own pricing math, not MCP transport. Keep a thin adapter boundary:

```text
stdio MCP server
  → typed JSON request validation
  → ETL/terms projection
  → native C++ callable
  → typed JSON result and evidence
```

The future FinAP integration should call the `fina-risk` stdio MCP tool through an authenticated server-side adapter. It must not call `fina_pricer_mcp_url` from browser code. The adapter should expose a stable logical operation such as `quote.price`, while the registry selects `fina-risk` native C++ as the production backend.

The current repository already has a Python FastMCP orchestration layer and pybind bindings for `run_daily_termsheet` and `run_daily_termsheet_batch`. The revamp should preserve this boundary while making the typed native entrypoint capable of returning leg-level results and evidence, rather than requiring callers to infer legs from aggregate fields.

## Required evidence

A native FCN result should include:

```json
{
  "engine_marker": "cpp_fcn_rakiplus_v1",
  "source_revision": "<git revision>",
  "request_id": "<request id>",
  "process_id": "<process id>",
  "terms_schema": "fcn-terms-projection.v1",
  "legs": [
    {"name": "FUNDING", "pv": 0.0},
    {"name": "COUPON", "pv": 0.0},
    {"name": "PUT / Terminal Optionality", "pv": 0.0}
  ],
  "cashflows": [],
  "state_transitions": [],
  "evidence_status": "verified"
}
```

The engine marker must identify the actual native implementation. Schema validation alone is not evidence. The E2E must execute the real stdio MCP path, invoke ETL, call native C++, and validate the emitted manifest.

## References

[1]: ../raki-plus.md "RakiPlus and MemRakiPlus payoff chapter"
[2]: ../../../../../skills/fina-risk/SKILL.md "FinA Risk skill"
[3]: ../../../../../model-registry/fcn.yaml "FCN model-wiring registry"
