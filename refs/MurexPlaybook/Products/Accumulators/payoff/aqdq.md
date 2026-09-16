# AQDQ (Equity Accumulator / Decumulator): Payoff Specification

## Scope and product purpose

**AQDQ** is Murex's flexible, path-dependent equity accumulator option. It expresses a repeated obligation to transact a specified quantity of one underlying stock at a preset strike over a schedule of periods. In an **Accumulator (AQ)**, the holder buys shares; in a **Decumulator (DQ)**, the holder sells shares. The arrangement remains live only while its knock-out condition has not been met, subject to the treatment of periods marked as guaranteed. It is a **physical-delivery** product, rather than a cash-settled equity payoff. [1]

> **Documented fact.** On each fixing date, spot is classified against the strike and a call or put quantity accrues. On observation dates, spot is tested against the applicable knock-out barrier. A qualifying knock-out terminates the deal, with remaining guaranteed-period accruals treated specially. [1]

The description below is a payoff interpretation of the documented ticket mechanics. It is not a valuation model specification and does not add market conventions that are absent from the source.

## Murex identity and configuration

| Ticket attribute | Documented value |
|---|---|
| Family | `EQD` |
| Group | `OPT` |
| Type | `FLEX` |
| Flex header | `EqFlexAccu` |
| Pricing payoff script | `EqFlexAccu` |
| Primary structural flex block | `ACCUPAY` |
| Date generation and historical-results block | `FIXING` |

`ACCUPAY` supplies the accumulator/de-accumulator selection, knock-out barrier(s), strike, call and put quantities, period-generation fields, and a per-period guarantee flag. `FIXING` generates daily fixing and knock-out observation dates and records historical outcomes as Call, Put, or KO. The pricing model also receives standard ticket information: `Nominal`, `Delivery`, `Maturity Date`, and `Premium Ccy`. The source does not state the calculation role of these standard fields, so they must not be assigned a payoff formula without confirmation. [1]

## State, dates, and observation rules

Index periods by \(p\), fixing dates in a period by \(d\), and let \(S_d\) be the observed underlying spot on date \(d\). Let \(K_p\), \(q^{C}_p\), and \(q^{P}_p\) denote, respectively, the strike, Call Qty, and Put Qty applicable to that period. Writing quantities by period makes the settlement description—whose knock-out price is a weighted average of the strikes of settled periods—usable without assuming that all periods share a strike.

The core payoff state is:

\[
\mathcal{H}_p = \{d: \text{fixing dates in period }p\},\qquad
N^C_p = \#\{d\in\mathcal{H}_p: \text{Call}(d)\},\qquad
N^P_p = \#\{d\in\mathcal{H}_p: \text{Put}(d)\}.
\]

Absent a knock-out before or at the relevant processing point, the documented normal-period accrued quantity is therefore

\[
Q_p = N^C_p q^{C}_p + N^P_p q^{P}_p.
\]

The direction is carried separately: \(\sigma=+1\) for AQ (the holder receives/buys shares) and \(\sigma=-1\) for DQ (the holder delivers/sells shares). This sign convention is an **implementation recommendation** for an explicit graph, not a new ticket field. It converts the accumulated absolute quantity into a stock-delivery direction.

### Call/put classification

On every fixing date, the source defines a **Call Day** as spot at or above the strike and a **Put Day** as spot below the strike. `StrikeCompare` controls whether equality uses the inclusive or exclusive comparison. A safe explicit rule is:

\[
\text{Call}(d)=
\begin{cases}
1,& S_d\;\odot_K\;K_p\\
0,& \text{otherwise},
\end{cases}
\qquad
\text{Put}(d)=1-\text{Call}(d),
\]

where \(\odot_K\) is the ticket-selected inclusive or exclusive strike operator. The quantities then accrue as \(q^{C}_p\) on a Call Day and \(q^{P}_p\) on a Put Day. Although the source illustrates a standard AQ with `Put Qty` often double `Call Qty`, that ratio is an example rather than a required rule. [1]

### Knock-out test and survival state

AQ uses an upper barrier, while DQ uses a lower barrier. For an AQ observation date \(o\), a KO occurs when \(S_o\;\odot_U\;B^{Up}_p\); for a DQ observation date, it occurs when \(S_o\;\odot_D\;B^{Down}_p\). `BarUpCompare` and `BarDownCompare` select the inclusive or exclusive operator (respectively \(\geq\) versus \(>\), and \(\leq\) versus \(<\)). [1]

For graph construction, define \(A_t\in\{0,1\}\) as an **implementation-state variable** meaning that the deal has not previously knocked out by time \(t\). Initialize \(A_0=1\), and set it to zero after the first qualifying KO. This latching state prevents later normal accrual or normal settlement branches from being evaluated after termination. The source establishes the termination result, but does not specify the intraday ordering when a date is both a fixing and a KO observation date; that ordering must be confirmed rather than inferred.

## Cashflow and delivery branches

The documented lifecycle supports the following branches. “Cash paid at strike” is the economically reciprocal cash leg of physical stock delivery; the source says settlement is at `Strike` but does not prescribe cashflow sign conventions or value dates, so those details remain implementation-dependent.

```text
For each scheduled observation/fixing date while active
|
+-- Applicable KO test is true?
|   |
|   +-- Yes: terminate AQDQ
|   |    +-- settle past accrued quantity
|   |    +-- add accruals for remaining Guaranteed periods (documented, detailed rule unspecified)
|   |    `-- settle at weighted-average strike across settled periods; exercise/physical delivery
|   |
|   `-- No: classify fixing, if applicable
|        +-- Call: accrue Call Qty
|        `-- Put:  accrue Put Qty
|
`-- At normal period end: exercise that period's accrued quantity at Strike
```

### Normal period completion

At a normal period end, Murex Exercise (`EXR`) settles physical delivery for the period. The exercised quantity is the period's accrued quantity \(Q_p\), and the settlement price is the strike. In explicit signed-leg form, the stock leg is \(\sigma Q_p\), while the reciprocal strike cash magnitude is \(K_p Q_p\). Thus AQ has the economic effect of acquiring \(Q_p\) shares and paying \(K_pQ_p\); DQ has the reverse delivery direction. The source documents the AQ buy and DQ sell directions and normal exercise quantity/price; the signed representation is a recommended graph convention. [1]

### Knock-out termination

On a qualifying KO, the deal terminates. Exercise quantity includes accruals from past dates plus qualifying future guaranteed-period accruals. The settlement price is the quantity-weighted average of strikes for all periods settled:

\[
\bar K_{KO}=\frac{\sum_{p\in\mathcal{P}_{KO}}K_p\,Q^{settle}_p}
{\sum_{p\in\mathcal{P}_{KO}}Q^{settle}_p},
\]

when the denominator is non-zero. Here \(\mathcal{P}_{KO}\) and \(Q^{settle}_p\) identify the periods and quantities actually included in the KO exercise. This equation restates the documented weighted-average-strike requirement in operational form. A zero-quantity handling branch is a necessary **implementation decision**, because the source does not state one.

A guaranteed period preserves entitlement to its accrual after KO. The source says this is *typically* at the most advantageous quantity and gives `Call Qty` for an accumulator as an example. It does **not** provide an exhaustive formula for AQ versus DQ, the treatment of a partially completed guaranteed period, the exact future fixing count, or an explicit definition of “most advantageous.” Therefore a payoff graph must source the guaranteed quantity from the actual Murex result/configuration or introduce a separately approved rule; it should not silently substitute \(q^C\), \(q^P\), or a multiplier.

### Other lifecycle events

Daily batch expiry (`EXP`) applies when no further cashflows remain. Manual early termination (`XIT`) is an unwind whose settlement defaults to deal market value but may be overridden. `EXR` is used for share delivery at a normal period end or KO. These are documented operational events, not additional optional payoff states. [1]

## Economic decomposition

The product is most transparent as conditional forward-style stock deliveries, not as a conventional coupon note.

| Economic leg | Interpretation | Documented boundary |
|---|---|---|
| Funding / principal-like leg | Physical stock quantity is exchanged against strike cash at each normal exercise, or in aggregate after KO. In AQ the holder buys stock; in DQ the holder sells it. | The source mandates physical delivery and strike settlement; it does not define separate funding or principal cashflows. |
| Coupon / fee leg | **No periodic coupon or fee payoff is documented.** `Premium Ccy` is a pricing input, but no premium amount, timing, or fee formula is stated. | Do not manufacture a coupon or premium cashflow from the currency field. |
| Embedded option / residual exposure | The barrier termination feature and spot-dependent call/put quantity selection create contingent, path-dependent exposure. The residual equity economics arise because quantities depend on the realized sequence of spots before KO. | This is an economic decomposition, not a claim that the ticket contains separately booked vanilla options. |

The branch-dependent quantity is economically material. For example, an AQ with a larger `Put Qty` accumulates more shares on fixing dates below strike, while the upper KO can end future accumulation when spot reaches the upper barrier. A DQ reverses the share-delivery direction and uses a lower KO. These statements follow the ticket logic; they do not imply a closed-form replication or a particular pricing model. [1]

## Path dependence and lifecycle effects

AQDQ is path dependent in three distinct ways. First, every realized fixing contributes to \(N^C_p\) or \(N^P_p\), so the delivery quantity depends on the sequence of outcomes rather than only terminal spot. Second, the first applicable barrier breach latches termination and truncates subsequent ordinary accrual. Third, the guarantee flag can cause post-KO settlement to include future-period entitlement, so identical KO spots can produce different outcomes depending on which periods are flagged and what had already accrued. Historical `FIXING` outcomes must therefore be treated as authoritative realized state, not recomputed from current market data. [1]

## Mapping flex blocks into an explicit payoff graph

The following is an **implementation recommendation** that preserves the documented data boundaries.

| Graph input or node | Source field/block | Use in the graph |
|---|---|---|
| Product direction | `ACCUPAY.Accu Type` | Select AQ/DQ, stock-delivery sign, and upper/lower KO branch. |
| Period grid | `ACCUPAY` schedule-generation fields | Create period nodes and associate their strike, quantities, and guarantee flag. |
| KO levels and equality rule | `ACCUPAY.Barr Up` / `Barr Down`; `BarUpCompare` / `BarDownCompare` | Parameterize the barrier predicate; do not hard-code inclusive tests. |
| Strike and fixing equality rule | `ACCUPAY.Strike`; `StrikeCompare` | Parameterize call/put predicate and normal strike settlement. |
| Call and put quantities | `ACCUPAY.Call Qty`; `Put Qty` | Feed the two accrual branches. |
| Guarantee state | `ACCUPAY.Guarantee Flag` per period | Gate the post-KO guaranteed-accrual subgraph, using an approved quantity rule. |
| Observation/fixing dates and realized labels | `FIXING` | Drive date-event nodes, past Call/Put/KO state, and future observation/fixing schedule. |
| Delivery, maturity, nominal, premium currency | Standard ticket fields | Carry as contractual/context inputs only until their detailed payoff roles are specified. |

A robust graph should have (1) a schedule-expansion node, (2) a historical-state loader from `FIXING`, (3) a barrier gate that updates the active latch, (4) a call/put classifier and running quantity accumulator, (5) normal-period `EXR` nodes, and (6) one KO aggregation/weighted-strike settlement node. Each cash and stock delivery should carry an explicit currency, date, direction, and physical-delivery flag. The last four attributes are necessary system-interface fields, but the source only confirms physical delivery and named date schedules; applicable conventions need to be supplied by the surrounding trade framework.

## Limitations and unresolved points

The documented product supports a single underlying only, no FX rules for that underlying, no cash settlement, and no quantity-based principal; principal must be a cash nominal. Its maximum tenor is two years. [1]

Several details cannot be safely inferred: whether barrier monitoring and fixing classification have a specified order on coincident dates; the precise calculation of guaranteed future accruals for every product direction; whether period-level strike/quantity fields can vary in all configurations; the fallback for a zero KO settlement quantity; calendar, fixing source, corporate-action, and settlement-date conventions; and the exact treatment of `Nominal`, `Delivery`, `Maturity Date`, and `Premium Ccy` in `EqFlexAccu`. These are **limitations or ambiguities in the supplied source**, not defects in the product. An implementation should make them explicit configuration decisions or obtain the authoritative payoff-script behavior before reconciliation or independent pricing.

## References

[1]: ../AQDQ.md "Murex Playbook — Equity Accumulator (AQ/DQ)"
