# Discrete Barrier Worst-of / Nth Performer (DBrW): Payoff Chapter

## Purpose and scope

**DBrW** is a Murex FLEX framework for discrete equity barrier options on one or more underlyings. It unifies single-underlying and basket use cases and supports worst-of or ranked-performer observations, single or double barriers, event rebates, configurable notional return, and Basic or Quanto settlement. This chapter rephrases the supplied product note and separates documented behavior from implementation recommendations. [1]

## Murex identity and payoff script

The documented representation is `EQD` / `OPT` / `FLEX`, with Flex Header `EqFlexDBrW` and instrument `FLEX_USD`. The source identifies the Monte Carlo group as `EQ_DBARW`, but does not print a separate payoff-script identifier. The header is therefore the reliable booking identifier; any script reference must be confirmed from the deployed configuration rather than invented. [1]

## State and observations

Let normalized performance for constituent \(j\) at observation \(t\) be \(X_j(t)\). Let \(X_{(k)}(t)\) be the selected ranked performance, where rank 1 is best and rank \(N\) is worst. The selected indicator is either worst performer or the configured \(k\)-th best performer, with \(1\leq k\leq N\). [1]

The observation set may be daily through `FIXINGDATE`, periodic through `PERIODS`, or continuous through a Min-Max fixing index. For an upper barrier use a maximum-style observation; for a lower barrier use a minimum-style observation. The source does not fully define mixed double-barrier min/max resolution, so the two barrier states should remain separate in the graph.

Define:

```text
upper_hit = any selected upper observation satisfying its configured comparison
lower_hit = any selected lower observation satisfying its configured comparison
ki_seen    = upper_hit or lower_hit for a Double-In configuration
ko_seen    = upper_hit or lower_hit for a Double-Out configuration
```

## Payoff branches

Let \(V_T\) be the terminal option value from the configured strike, option direction, performer indicator, and final observation. Let \(R_b\) be the rebate associated with the barrier that triggered, and let \(r\) be the configured notional-return ratio. A normalized no-rebate option branch is:

```text
Knock-In:
  barrier hit     → option payoff V_T + applicable rebate
  no barrier hit  → zero

Knock-Out:
  barrier hit     → zero option payoff + applicable rebate
  no barrier hit  → option payoff V_T
```

The source states the settlement relationship as:

\[
Payment = (Pay_{Option}+Pay_{Rebate}-ReturnRatio)\times Notional.
\]

The sign and whether `ReturnRatio` is represented as a positive or negative displayed rate must be retained exactly from the implementation contract. Do not normalize the sign without a conformance fixture. [1]

For a double barrier, each upper and lower event should carry its own rebate and trigger identity. The source requires operational recording of which barrier triggered. Same-time upper/lower collisions are not specified and need an explicit policy.

### Rebate timing

`AT_Knock` pays the rebate at the trigger. `On_Maturity` defers it to the final scheduled maturity date. Notional return follows the same timing in the supplied description. [1]

## Economic decomposition

| Component | Interpretation | Status |
|---|---|---|
| Funding / principal return | Configured notional return, multiplied by notional and gated by the applicable settlement branch. | Documented, but sign and exact rate convention require confirmation. |
| Coupon / fee | No periodic coupon is described. A rebate is a contingent event payment, not a coupon. | Rebate documented; premium/fee absent. |
| Embedded option / residual | Terminal option value gated by KI or KO state and selected worst/ranked performer. | Core economic exposure. |

This product is therefore an event-gated option with a contingent rebate and optional principal-return treatment, not a range-accrual coupon note.

## Flex-block mapping

| Block | Documented role | Payoff graph role |
|---|---|---|
| `DISCBARR` | Barrier style, upper/lower levels, rebates, notional return, and dynamic field visibility. | Barrier predicates, rebate nodes, and principal-return gate. |
| `FIXINGDATE` | Generated daily fixing schedule. | Discrete observation stream. |
| `PERIODS` | Period windows, period strikes, barriers, rebates, and payment dates. | Time-dependent parameter resolver. |
| Underlying table | Constituents and initial reference prices. | Performance normalization and rank selection. |
| Quanto fields | FX pair, source, fixing time, timezone, rate type. | Settlement conversion node. |

## Explicit payoff graph

```text
trade terms → reference-price normalization → performer selector
           → observation schedule → upper/lower hit state
           → KI/KO gate → terminal option / rebate / return nodes
           → timing resolver → currency settlement and evidence
```

Persist fixing index, selected performer/rank, barrier side, trigger date, rebate timing, notional-return flag, and FX fixing provenance. The graph must support both option-style and note-style return configurations without hiding the distinction.

## Lifecycle, constraints, and ambiguities

`Knock` records barrier status and generates the configured rebate/return flows; `Expiry` settles surviving option and deferred rebate components. The framework does not support quantity principal, Composite FX, or more than six basket stocks, and limits tenor to 25 months. Single-equity structures use the dummy-basket representation. [1]

The source leaves equality operators, final-option formula, mixed-barrier collision ordering, exact notional-return sign, rebate scaling, and continuous observation conventions insufficiently specified. These must be resolved by deployed configuration or parity evidence.

## References

[1]: ../Discrete_Barrier.md "Murex Playbook — Discrete Barrier Worst-of / Nth Performer (DBrW)"
