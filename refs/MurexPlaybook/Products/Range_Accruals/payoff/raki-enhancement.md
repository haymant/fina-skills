# RAKI Enhancements: Payoff Chapter

## Scope

This document is an enhancement design for RAKI-style products rather than a single Murex booking specification. It adds coupon barriers, memory coupons, memory KO, and non-memory KO to the common range-accrual and KI framework. It should be treated as a feature contract to be mapped into a concrete Flex header and payoff script. [1]

## Base coupon and coupon barrier

For period \(i\), define:

\[
P^{base}_i=AccruRate_i\frac{N_{1,i}}{N_{2,i}}+FixCoupon1_i.
\]

A coupon barrier tests WPS against a configured level. If the condition is not satisfied, the current coupon is withheld. With memory enabled, withheld coupons accumulate. When a later period satisfies the barrier, the current coupon and the accumulated unpaid coupons are released. The source states that coupon-barrier/memory-coupon and global KO are mutually exclusive. [1]

An implementation should represent `unpaid_coupon_balance` as explicit state and emit a release node rather than rewriting prior cashflows.

## KO states

Non-memory KO triggers when WPS reaches its barrier on the relevant local or global observation. Memory KO tracks each underlying separately and triggers only after every underlying has reached its memory barrier at least once. Both local and global forms can be supported. If both trigger together, global KO has precedence. [1]

The KO rate is:

\[
P_{KO}=P_i+KOBonus+ReturnRatio.
\]

For a global KO, range accrual is measured through the trigger date, while the period denominator remains the configured total accrual-day count. Payment can occur at period end or on the KO date.

## Terminal hierarchy

If no KO occurs, the source describes three maturity cases:

```text
WPS ≥ Lower Call Strike
  → capped/floored call-like participation + ReturnRatio

WPS < Lower Call Strike and KI occurred
  → KI1 or KI2 capped/floored participation by maturity barrier

WPS < Lower Call Strike and no KI
  → capped/floored combination of upside and downside participation
```

The KI branch is:

\[
P_{mat}=P_N+g_{KI,k}(WPS)+ReturnRatio,
\]

where \(k\) is selected by the maturity-barrier test. The no-KI branch is:

\[
P_{mat}=P_N+\max\{Floor,\min[Cap,
PR_{NOKI1}(WPS/Strike1-1)^+
+PR_{NOKI2}(1-WPS/Strike2)^+]
\}+ReturnRatio.
\]

Each capped/floored function must be an independent graph node. Do not flatten the hierarchy into a single delta-like formula.

## Economic decomposition

| Component | Interpretation |
|---|---|
| Funding / principal | Return-ratio contribution and the notional-return behavior selected by the concrete product. |
| Coupon | Range accrual, fixed coupon, coupon-barrier withholding, memory release, and KO bonus. |
| Embedded option / residual | Memory/non-memory barrier survival, KI state, call-like participation, put-like participation, caps, floors, and maturity branch selection. |

This is an economic decomposition for explainability; it does not assert that Murex books separate legal instruments.

## Flex and graph mapping

A concrete implementation should map range dates to an accrual schedule, period rows to coupon and barrier parameters, KO blocks to local/global state updates, and KNOCKIN fields to terminal residual nodes. The common graph is:

```text
fixings → range count / coupon barrier → coupon balance
       → local/global KO state → KO settlement
       → KI state → maturity hierarchy → cashflow and evidence
```

The graph must reject incompatible feature combinations, especially global KO together with coupon-barrier memory behavior. Every comparison operator is a parameter, not a hard-coded inequality.

## Limitations

The source does not identify one header, script, model group, complete field dictionary, or concrete lifecycle event contract. It also leaves memory release indexing, partial-period KO accrual, missing-fixing treatment, and rate-to-cashflow conversion open. Promote these decisions into a product-specific registry only after an owning Murex configuration or parity fixture exists. [1]

## References

[1]: ../RAKI_Enhancement.md "Murex Playbook — RAKI Enhancement Overview"
