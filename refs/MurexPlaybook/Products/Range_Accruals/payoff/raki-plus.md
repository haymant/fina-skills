# RakiPlus and MemRakiPlus — Payoff Chapter

For translating this payoff contract into the FinA native C++ lane, read [RakiPlus-to-Native-Engine Methodology](raki-plus-native-engine-methodology.md).

## Purpose, classification, and scope

**RakiPlus** and **MemRakiPlus** are the enhanced booking and operations variants of, respectively, an equity range-accrual note and an equity memory range-accrual note. Their pricing foundations remain `EqFlexRaki` and `EqFlexMemR`; the documented change is chiefly in trade representation and processing. In particular, a market-level **dummy basket** may be used as the basket definition, while the transaction-specific equity constituents and their reference prices are entered in the trade. This removes the need to maintain a separately predefined basket for each constituent combination. [1]

Both products are booked in Murex with **Family** `EQD`, **Group** `OPT`, and **Type** `FLEX`. The documented Flex Headers are `EqFlexRakiP` for RakiPlus and `EqFlexMemRP` for MemRakiPlus. The source identifies no literal payoff script, code listing, or expression-language implementation. Consequently, the formulas below are a normalized interpretation of the documented payoff description, rather than a reconstruction of an executable Murex script. [1]

> **Reading convention.** Statements marked **Documented** restate the supplied source in rephrased form. Statements marked **Implementation recommendation** describe a controlled way to represent or validate the documented economics; they are not asserted Murex behavior.

## Economic structure at a glance

The common structure pays a period rate composed of a range-accrual coupon and a fixed coupon. A local or global knock-out can terminate the deal early and add the relevant knock-out coupon and return ratio. If the deal reaches maturity without a knock-out, the final rate depends on whether a knock-in has occurred. The knock-in and no-knock-in outcomes use distinct capped and floored residual functions of the terminal worst-performance measure. [1]

MemRakiPlus retains this broad schedule but changes the knock-out test to a memory condition. Its local and global knock-outs are triggered when the stated normalized-price condition has occurred at least once for all underlyings. RakiPlus uses the stated worst-performance threshold tests instead. [1]

```text
Start of deal
├─ During a scheduled period: calculate range-accrual rate
│  ├─ Local KO condition satisfied → local KO settlement and termination
│  ├─ Else global KO condition satisfied → global KO settlement and termination
│  └─ Else → pay or retain the periodic result as configured; continue
└─ No KO by maturity
   ├─ Knock-in state is true → select KI1 or KI2 terminal residual by maturity barrier
   └─ Knock-in state is false → apply the capped/floored non-KI terminal residual
```

The tree states the documented branches, not a priority rule. In particular, the source does not say what happens if a local and global knock-out are both observed on the same relevant date.

## Payoff notation and observable state

Let period \(i\) have range-accrual rate \(A_i\), fixed coupon \(F_i\), and accrued fraction \(\alpha_i\). The source uses \(\mathrm{AccruRate}[i]\), \(\mathrm{FixCoupon}[i]\), and \(\mathrm{AccruFactor}\), respectively; the alternative notation is used only to make the equations legible. Let \(W(t)\) denote the source's **WPS** measure and let \(w= W(T_{\mathrm{mat}})\) when a maturity measure is needed. The source labels the accrual indicator as either *Worst Performance* or *All Underlying*, but does not define a mathematical aggregation convention for either. It therefore does not establish, for example, whether WPS is a minimum normalized performance, how all-underlying tests are combined, or whether a range endpoint is inclusive. [1]

For a range-accrual period, the documented state can be represented as follows:

| State or input | Meaning supported by the source | Use in the payoff |
|---|---|---|
| \(S_j(t)\), \(S_j(0)\) | Price of underlying \(j\) at an observation time and its reference price | Explicitly used in MemRakiPlus memory KO tests; reference prices are supplied with constituents. |
| \(W(t)\) | WPS / stated worst-performance measure | Used in RakiPlus KO tests and maturity formulas. |
| \(I_{i,d}\) | Indicator that the selected accrual measure is within the period's low/up range on accrual day \(d\) | Counts qualifying accrual days. |
| \(N_{1,i}\), \(N_{2,i}\) | Number of qualifying days and total accrual days | Determine \(\alpha_i=N_{1,i}/N_{2,i}\). |
| KO status | Whether termination has occurred and, for MemRakiPlus, the documented local/global lock states | Stops subsequent economics after a knock-out. |
| KI status | Whether the configured knock-in event has occurred | Selects the maturity residual branch if there is no KO. |
| \(i\), dates, and payment timing | Current period, accrual dates, KO observation dates, payment dates | Determine which conditions and cash flows are evaluated. |

**Documented observation rules.** `RGACCDATE` supplies the range-accrual fixing dates. `RGACCLKO` for RakiPlus, or `RGACCLKO+` for MemRakiPlus, supplies range-accrual periods, payment dates, and local-KO observation periods. The latter block also carries period-specific low/up range and local-KO barriers, coupons, the accrual-indicator selection, and allows period-specific global-KO coupon and barrier customization. `GLOBALKO*` specifies global-KO observation dates as discrete or continuous and whether payment is on the period-end date or the KO date. `KNOCKIN*` specifies the knock-in event, its barrier and observation dates, and the maturity payoff inputs. [1]

For **RakiPlus**, a local KO is documented when \(W(t)\geq \mathrm{LocBarPrice}\), and a global KO when \(W(t)\geq \mathrm{GblBarPrice}\). For **MemRakiPlus**, local and global memory KOs are documented when \(S_j(t)/S_j(0)\) reaches at least the corresponding memory barrier at least once for all underlyings. The source does not resolve whether “for all underlyings” requires same-time satisfaction, permits each underlying to satisfy its test on a different date, or how the two memory lock flags are updated. [1]

## Periodic range-accrual coupon and cash-flow rounding

**Documented.** Before a KO or maturity branch is applied, the period rate is

$$
P_i=A_i\alpha_i+F_i,
\qquad
\alpha_i=\frac{N_{1,i}}{N_{2,i}}.
$$

Here \(N_{1,i}\) is the number of days on which the selected accrual indicator is within the configured range, and \(N_{2,i}\) is the relevant total number of days. The source does not specify the handling of missing fixings, non-business-day observations, zero \(N_{2,i}\), range-endpoint equality, or a cancelled period. [1]

A `Denomination` field in `KIKOSELECT` changes the documented rounding of **periodic** cash flows. If \(D\) is denomination and \(Q\) is notional, then

$$
\mathrm{CashFlow}_i
=
\operatorname{Round}\!\left(D\,P_i,2\right)\frac{Q}{D}.
$$

The source contrasts this with the former convention, which effectively fixed \(D=Q\). It attributes resulting differences to rounding. It does not expressly state that this periodic rounding formula applies to terminal residuals or to the separate KO settlement flows. [1]

**Implementation recommendation.** Store the unrounded \(P_i\), \(D\), and rounded monetary amount as separate nodes. Require a nonzero denomination before evaluating the formula, and retain the original inputs and rounding result for audit. Keep the applicability of this rounding node limited to periodic flows unless configuration or test evidence confirms a broader scope.

## Early-termination branches

### RakiPlus local and global KO

**Documented.** At a RakiPlus local KO in period \(i\), the stated KO rate is

$$
P_{\mathrm{KO,L}}=P_i+\mathrm{LocKOCpn}+R,
$$

where \(R\) is `ReturnRatio`. At a global KO, it is

$$
P_{\mathrm{KO,G}}=P_i+\mathrm{GblKOCpn}+R.
$$

The barrier tests are \(W(t)\geq\mathrm{LocBarPrice}\) and \(W(t)\geq\mathrm{GblBarPrice}\), respectively. [1]

### MemRakiPlus local and global memory KO

**Documented.** The stated rate at a local memory KO in period \(i\) is

$$
P_{\mathrm{KO,Lmem}}=P_i+\mathrm{LocalKOBonus}+R,
$$

and the corresponding global memory KO rate is

$$
P_{\mathrm{KO,Gmem}}=P_i+\mathrm{GlobalKOBonus}+R.
$$

These formulas apply after the respective memory condition described above. The source names `LKO Locked` and `GKO Locked` as MemRakiPlus fields in `KIKOSELECT`; it does not describe their full state-transition logic. [1]

### Operational KO settlement

**Documented.** Murex supports standard `Knock` processing. For either local or global knock events, the described settlement contains two components: a **notional return** equal to return ratio times deal notional, and a **KO settlement coupon**. The coupon depends on KO type and timing. The source gives the local-KO period coupon and, for a global KO on a date other than period end, a pro-rated accrual plus global-KO coupon as examples. The operator selects the barrier that was knocked, after which Murex generates the configured flows. [1]

**Implementation recommendation.** Model the operational settlement as two explicit cash-flow nodes: \(Q\times R\) for notional return and a KO-coupon node whose formula is selected by KO type and payment-timing configuration. Reconcile their total with the documented KO-rate presentation, but do not force an equivalence without confirming whether the rate formula is quoted as a rate-level summary or as the exact flow construction. Represent local/global KO precedence, same-day collisions, and continuous-observation detection as explicit policy decisions because the source does not define them.

## Maturity branches when no KO occurs

Let \(P_N\) denote the source's `PayRate[NumOfPeriods]`. The documentation writes the maturity rate as \(P_N\) plus the selected residual and \(R\). It does not define whether \(P_N\) is the final period rate, a rate already paid, or an accumulated total. The equations should therefore preserve this symbolically rather than reinterpret it as a sum of all previous coupons. The MemRakiPlus formula has the same structure, with its product-specific parameters and explicitly uses \(W(T_{\mathrm{mat}})\). [1]

### Knock-in branch

**Documented.** If a knock-in has occurred and there was no KO, select one of two capped and floored linear residuals according to the maturity barrier. Define

$$
g_{\mathrm{KI},k}(w)=
\min\!\left\{\mathrm{Cap\_KI}_{k},
\max\!\left[\mathrm{Floor\_KI}_{k},
\mathrm{PR\_KI}_{k}\left(\frac{w}{\mathrm{Strike\_KI}_{k}}-1\right)\right]\right\},
\quad k\in\{1,2\}.
$$

Then the documented branch is

$$
P_{\mathrm{mat,KI}}
=
P_N+
\begin{cases}
 g_{\mathrm{KI},1}(w)+R, & w\geq \mathrm{MaturBarrier},\\
 g_{\mathrm{KI},2}(w)+R, & w<\mathrm{MaturBarrier}.
\end{cases}
$$

The compact suffix notation in this chapter denotes the source fields `Cap_KI1`, `Floor_KI1`, `PR_KI1`, and `Strike_KI1`, or their `KI2` equivalents. [1]

### No-knock-in branch

**Documented.** If no knock-in has occurred and no KO occurs, the residual is a capped and floored combination of an upside participation term and a downside participation term:

$$
g_{\mathrm{NKI}}(w)=
\max\!\left\{\mathrm{Floor},
\min\!\left[\mathrm{Cap},
\mathrm{PR\_NOKI1}\left(\frac{w}{\mathrm{Strike1}}-1\right)^+
+
\mathrm{PR\_NOKI2}\left(1-\frac{w}{\mathrm{Strike2}}\right)^+
\right]\right\},
$$

where \(x^+=\max(x,0)\). The maturity rate is

$$
P_{\mathrm{mat,NKI}}=P_N+g_{\mathrm{NKI}}(w)+R.
$$

The source calls this the non-knock-in outcome, but does not provide the exact knock-in trigger inequality or the interaction of a KI observation with concurrent KO observations. Those rules must be obtained from configuration semantics or tests, not inferred from the residual formula. [1]

`ITM Payment` in `KIKOSELECT` specifies cash or physical settlement when the deal is in the money at expiry. The document supplies no mapping from the maturity residual formula to an in-the-money test and no physical-delivery quantity formula. [1]

## Leg decomposition

The following is an **economic decomposition for implementation**, not an assertion that Murex books separate valuation instruments.

| Leg | Documented economic content | Explicit graph treatment recommended |
|---|---|---|
| Funding / principal-return leg | No conventional funding coupon is described. `ReturnRatio` appears in KO and maturity rate formulas. KO processing separately describes a notional-return flow of \(Q\times R\). The `Quantity` principal type is unsupported. [1] | Create a conditional principal-return node for KO and a separately labelled rate-level return-ratio contribution at maturity. Do not label either a funding leg unless the booking definition supplies funding terms. |
| Coupon / fee leg | The periodic rate is the range-accrual component \(A_i\alpha_i\) plus fixed coupon \(F_i\). Local/global KO coupons or bonuses augment a terminating rate. No separate fee is documented. [1] | Create one periodic coupon node per period, then KO coupon nodes selected by the termination event and timing. Preserve the distinction between fixed coupon and KO coupon/bonus. |
| Embedded option / residual leg | Local and global KO conditions, the KI-state selection, the maturity-barrier switch, and the capped/floored residuals create contingent equity exposure. [1] | Use barrier-event nodes feeding KI/KO state nodes, and use separate capped/floored residual nodes for KI1, KI2, and non-KI. Keep the terminal residual separate from the coupon leg for testing and explainability. |

## Flex-block-to-input mapping

**Documented mapping.** `KIKOSELECT` holds the actual constituents and reference prices for the dummy basket, activation controls for local KO, global KO, and KI, denomination, ITM-payment method, and quanto FX-fixing references. For MemRakiPlus it also holds the local/global KO lock fields. The dummy basket itself is a market-oriented placeholder rather than a list of the trade's individual equities, and is configured with `Multi currency rule = Quanto` in the example methodology. [1]

| Flex block | Inputs or functions evidenced in the source | Payoff-graph nodes it should feed |
|---|---|---|
| `KIKOSELECT` | Trade constituents, reference prices, KO/KI activation, denomination, ITM-payment method, FX fixing details; MemRakiPlus lock fields | Underlying/reference-price state, activation gates, rounding node, expiry settlement-method node, FX-fixing input, memory-state nodes |
| `RGACCDATE` | Range-accrual fixing dates | Accrual-date schedule and \(I_{i,d}\) observations |
| `RGACCLKO` / `RGACCLKO+` | Periods, payment dates, local-KO observation periods, low/up range, local-KO barrier and coupons, accrual-indicator choice, period-customized global-KO inputs | Period coupon, local-KO observation, period-specific KO coupon and barrier parameter nodes |
| `GLOBALKO*` | Discrete/continuous GKO dates and period-end-versus-KO-date payment logic | Global-KO observation scheduler and settlement-date selector |
| `KNOCKIN*` | KI event, barrier, observation dates, and KI/non-KI cap, floor, and strike payoff inputs | KI-state node, maturity-barrier selector, KI1/KI2/non-KI residual nodes |

**Implementation recommendation.** Treat the mapping as a directed dependency graph, not merely a field inventory. First validate activation gates and schedules. Next create fixing/observation nodes, then state-transition nodes, then rate nodes, then cash-flow and settlement nodes. This ordering prevents inactive KO/KI features from contributing inputs to the selected payoff branch. Preserve the raw block values and record the node and observation that caused each state change.

## Suggested explicit payoff graph

An auditable payoff graph can use the following dependency order:

1. **Static trade node:** basket constituents, reference prices, notional, denomination, FX-fixing references, settlement method, and activation switches.
2. **Schedule nodes:** accrual dates, range-accrual periods, payment dates, local-KO periods, global-KO dates/mode, and KI observation dates.
3. **Market-observation nodes:** \(S_j(t)\), the selected WPS/all-underlying measure, range-membership indicators, and relevant barrier comparisons.
4. **State nodes:** \(N_{1,i}\), \(N_{2,i}\), local/global KO state, MemRakiPlus lock state, KI state, and a terminal/terminated flag.
5. **Rate nodes:** periodic \(P_i\), local/global KO rate, KI1/KI2 residuals, non-KI residual, and maturity rate.
6. **Cash-flow nodes:** denomination-rounded periodic cash flow, notional return on KO, KO settlement coupon, and maturity settlement method.

**Implementation recommendation.** A graph should make the termination gate dominant: after a selected KO, no later periodic or maturity residual node should settle. The graph should also represent the global-KO payment-date selection independently of the barrier test. For continuous GKO monitoring, it should capture an observation source or event timestamp; the source establishes that continuous observation is configurable but does not define its sampling or interpolation convention.

## Path dependence and lifecycle effects

**Documented.** These products are path dependent because the periodic rate depends on the count of in-range accrual days, KO depends on observations before maturity, and maturity depends on whether KI has occurred. MemRakiPlus adds explicitly persistent local/global KO lock fields and memory KO tests based on whether specified normalized-price levels were attained at least once. A knock event terminates through the selected settlement flow. Standard `Expiry` and `Knock` market operations are supported. [1]

The operational enhancement is also material to lifecycle processing. Fixing and archiving are performed by market rather than individual security, and values are automatically populated when deals are opened for fixing, subject to confirmation. This changes the fixing workflow but does not alter the stated payoff formulas. [1]

**Implementation recommendation.** Store each confirmed observation, the applicable schedule identifier, any state transition, and generated settlement identifier. Replay should calculate the same \(N_{1,i}/N_{2,i}\) ratio and the same KO/KI state from this history. Never overwrite a prior memory-hit or KI state with a later non-hit unless product semantics explicitly provide for reset, which the source does not.

## Limits and unresolved specifications

**Documented product limits** are: basket-only use rather than a single equity; `Basic` FX rule only when basket currency equals premium currency and `Quanto` when they differ; no `Composite` FX rule; no `Quantity` principal type; a maximum tenor of 25 months; and no more than six equity underlyings in the basket. [1]

The following points are **ambiguities in the supplied material**, not omissions to be filled by assumption:

- The WPS calculation, all-underlying aggregation, range inclusivity, and treatment of unavailable fixings are not defined.
- The exact KI trigger rule and KI/KO precedence are not given, despite `KNOCKIN*` configuring a KI event and barrier.
- The same-date priority of local and global KO is not stated.
- The phrase “at least once for all underlyings” in memory KO does not say whether hits must be simultaneous.
- The source does not fully connect KO-rate formulas with the two operational KO settlement flows, nor specify whether `Denomination` rounding applies to terminal amounts.
- No physical ITM-delivery mechanics, convention for \(P_N\), or continuous-observation sampling rule is provided.

**Implementation recommendation.** Mark these items as mandatory configuration clarifications or regression-test cases. Do not encode defaults for any of them solely from the formulas in this chapter.

## References

[1]: ../RakiPlus_MemRakiPlus.md "RakiPlus & MemRakiPlus source document"
