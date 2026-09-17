# EQ Range Accrual (Raki): Payoff Chapter

## Purpose and classification

**Raki** is an equity range-accrual structured note. It pays periodic coupon amounts according to the fraction of observation days on which the selected performance indicator remains within a configured range. It may terminate through local or global KO, and its maturity result depends on KI state when no KO has occurred. [1]

The documented Murex representation is `EQD` / `OPT` / `FLEX` with Flex Header and payoff script `EqFlexRaki`. The Monte Carlo model group is `EQ_RAKI`. [1]

## State and coupon

Let \(N_{1,i}\) be qualifying days and \(N_{2,i}\) total days in period \(i\). Then:

\[
AccruFactor_i=\frac{N_{1,i}}{N_{2,i}},
\qquad
P_i=AccruRate_i AccruFactor_i+FixCoupon_i.
\]

The range indicator is typically WPS, but the exact aggregation and endpoint treatment are controlled by product fields. `RGACCDATE` supplies daily observations and `RGACCLKO` supplies periods, payment dates, range bounds, local barriers, and coupons.

## KO and KI branches

Local KO is a periodic WPS threshold test. Global KO is daily discrete or continuous. If both occur on the same date, the source treats the event as global KO. The KO rates are:

\[
P_{LKO}=P_i+LocKOCpn+ReturnRatio,
\]

\[
P_{GKO}=P_i+GblKOCpn+ReturnRatio.
\]

The accrued component is measured through the KO date. Global KO can settle at period end or on the KO date. [1]

If no KO occurs, a KI event selects a capped/floored terminal option branch; the no-KI branch pays the configured `NoKI_Pay`. The source gives the normalized structure but does not define every terminal parameter or conversion from rate to cash amount.

## Economic decomposition

| Component | Interpretation |
|---|---|
| Funding / principal | Returned notional / `ReturnRatio` at KO or maturity, subject to the concrete settlement convention. |
| Coupon | Periodic range-accrual coupon, fixed coupon, and KO coupon. |
| Embedded option / residual | Barrier survival and KI-dependent maturity option; no-KI maturity payment is a separate terminal branch. |

Accrual payments are separate from the expiry settlement in the standard flow. A mid-period GKO may combine prorated accrual with GKO coupon and return in one termination settlement.

## Flex-block mapping

| Block | Role |
|---|---|
| `KIKOSEL*` | Feature activation, return ratio, initial fixings. |
| `RGACCDATE` | Daily accrual fixing schedule. |
| `RGACCLKO` | Periods, rates, fixed coupons, range, local barriers, N1/N2. |
| `GLOBALKO*` | Global schedule, monitoring mode, payment timing. |
| `KNOCKIN*` | KI barrier, observation schedule, cap/floor/strike terminal inputs. |

## Explicit graph

```text
terms → accrual dates → indicator observations → N1/N2 → coupon flows
      → local/global KO state → KO settlement or survival
      → KI state → terminal residual / NoKI_Pay → settlement
```

Persist comparison operators, fixing source, payment timing, initial references, trigger timestamps, and the selected terminal branch. Use the native payoff script as the authority when a field’s semantics differ from this normalized representation.

## Constraints and open points

The documented product supports nominal rather than quantity principal, excludes Composite FX, requires basket and premium currency to match for the stated structure, and limits tenor to two years. The source does not fully specify missing fixing rules, indicator aggregation, endpoint equality, KO/KI collision ordering, or terminal rate scaling. [1]

## References

[1]: ../Range_Accrual_Raki.md "Murex Playbook — EQ Range Accrual (Raki)"
