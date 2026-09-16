# Barrier Option (BAROPT): Payoff Chapter

## Scope and product purpose

**BAROPT** is documented as Murex's generic product type for a standard vanilla barrier option. A barrier option is an option whose final entitlement is conditional not only on the underlying price at valuation, but also on whether the underlying reaches a specified barrier during the option's life. The barrier condition can either activate the option (**knock-in**) or terminate it (**knock-out**). The barrier direction is described as **up** when it is above the initial price and **down** when it is below the initial price. [1]

This chapter is an interpretation of the documented booking fields and the standard payoff logic implied by those descriptions. It is deliberately not a product specification beyond the supplied source. In particular, it does not add rebate, premium, settlement, currency-conversion, fixing-calendar, or monitoring-window rules that are not present in that source.

## Documented Murex identity and available flex artefacts

| Item | Documented position | Payoff implication |
|---|---|---|
| Product family / group | The source calls the product a standard vanilla barrier option and identifies the generic Murex product type. It does **not** name a Murex product family or group field. | Treat the barrier family/group as unspecified in a downstream model; do not manufacture a group code. |
| Murex product type | `BAROPT`. [1] | Identifies the product as the barrier-option trade being modelled. |
| Instrument | A flexible instrument, typically `FLEX_USD` or a comparable variant, is said to be used so custom JSON parameters can be attached. [1] | The instrument name alone does not define payoff logic; the mapped trade data determine the payoff inputs. |
| Flex header | No flex header layout, named flex blocks, or header values are supplied. | No header can be reconstructed from the source. |
| Payoff script | No Murex payoff script, formula code, script identifier, or script-level output is supplied. | The payoff graph below is an **implementation recommendation**, not a transcription of an existing script. |

> **Documented fact.** The intake structure is split into `Specs`, which holds high-level product choices, and `Variables`, which holds economic and booking details. The source then maps selected fields to Murex targets. [1]

## State variables and observation rule

### Economic state

For a one-underlying implementation, the following notation makes the documented economics explicit without claiming that these are source field names:

\[
\begin{aligned}
S_0 &:= \text{initial underlying price},\\
S_t &:= \text{underlying price at time } t,\\
K &:= \text{strike},\\
H &:= \text{barrier level},\\
T &:= \text{final valuation / expiry point},\\
q &:= \text{option quantity},\\
\sigma &\in \{+1,-1\} := \text{buy/sell sign},\\
\phi &\in \{+1,-1\} := \text{call/put sign}.
\end{aligned}
\]

Here \(\phi=+1\) denotes a call and \(\phi=-1\) a put, so the vanilla payoff per unit is

\[
V_T = \max\!\left(\phi(S_T-K),0\right).
\]

This notation is a **recommended payoff representation**. The documented source provides the input concepts—initial price, strike, barrier type/level, option type, quantity, buy/sell, and final fixing/maturity dates—but not a prescribed mathematical convention, quantity unit, or settlement multiplier. [1]

### Barrier event

Let \(\mathcal O\) be the set of valid observation instants. Define the barrier-hit indicator \(I\) as follows:

\[
I=
\begin{cases}
1, & \exists t\in\mathcal O: S_t\ge H, \quad \text{for an up barrier},\\
1, & \exists t\in\mathcal O: S_t\le H, \quad \text{for a down barrier},\\
0, & \text{otherwise.}
\end{cases}
\]

The source distinguishes `Continuous` and `Discrete` observation through `Specs.Cond3`, mapped to `DiscrContinuos`. [1] In this representation, a continuous convention uses the monitored life of the option as \(\mathcal O\), while a discrete convention uses only the configured observation instants. The source does not supply the discrete dates or frequency, the start and end of the monitoring window, a price source, treatment of non-trading dates, or strict-versus-inclusive equality. Those details must remain explicit configuration choices rather than hidden assumptions.

The source also identifies up versus down relative to the initial price. [1] This is a directional description, not a complete barrier-validation rule: it does not state whether a trade with a differently placed level is rejected, repriced, or interpreted differently.

## Contractual payoff branches

The documented `EQBarrierType` is the field for barrier style, with `Down and In` given as an example. [1] Subject to the general interpretation above, the complete no-rebate terminal entitlement is:

\[
P_T^{\mathrm{long}}=
\begin{cases}
I\,V_T, & \text{knock-in},\\
(1-I)\,V_T, & \text{knock-out}.
\end{cases}
\qquad
P_T=\sigma q P_T^{\mathrm{long}}.
\]

Thus, call and put are exhausted by \(V_T\), and purchase versus sale is exhausted by \(\sigma\). Barrier direction only changes the definition of \(I\). Expanding the result gives the operative branches below.

| Barrier style | Barrier state at the end of monitoring | Long call / put result | Short result |
|---|---|---|---|
| Knock-in | Hit: \(I=1\) | \(q\max(\phi(S_T-K),0)\) | The negative of the long result |
| Knock-in | Never hit: \(I=0\) | \(0\) | \(0\) |
| Knock-out | Hit: \(I=1\) | \(0\) | \(0\) |
| Knock-out | Never hit: \(I=0\) | \(q\max(\phi(S_T-K),0)\) | The negative of the long result |

This is a **recommended no-rebate payoff graph**, based on the documented knock-in and knock-out definitions. It must not be read as evidence that BAROPT excludes rebates. The source simply supplies no rebate amount, rebate timing, premium, or other contractual cashflow field. Consequently, no such branch can be calculated from the available data.

### Short payoff tree

```text
Start: determine monitoring convention from Specs.Cond3
|
+-- Barrier observed?
    |
    +-- Yes (I = 1)
    |   +-- Knock-in  --> option active at T --> σ × q × max[φ(S_T − K), 0]
    |   +-- Knock-out --> option extinguished --> 0
    |
    +-- No (I = 0)
        +-- Knock-in  --> never activated --> 0
        +-- Knock-out --> option survives at T --> σ × q × max[φ(S_T − K), 0]
```

## Cashflow-leg interpretation

The supplied data describes a single option payoff with a path condition. It does not document a bond, loan, deposit, periodic coupon, or principal-repayment schedule. The following decomposition therefore separates what is present from what is absent.

| Leg category | Interpretation for BAROPT | Status in supplied source |
|---|---|---|
| Funding / principal | No funding advance, redemption principal, notional exchange, or accrual rule is stated. `Nominal` is mapped as a trade field, but its use as a payoff multiplier is not defined. [1] | **Not documented as a payoff leg.** Do not create a principal cashflow solely from `Nominal`. |
| Coupon / fee | No periodic coupon, fee schedule, premium amount, premium payer, or payment date is provided. | **Not documented.** Do not infer an upfront premium or a rebate. |
| Embedded option / residual leg | The documented economic feature is the barrier-conditioned vanilla call or put. In the recommended graph, this is \(I V_T\) for knock-in or \((1-I)V_T\) for knock-out. | **Meaningful and directly tied to the documented product purpose.** |

`Currency` maps to Murex trade currency (`MAR_CCY`), while `Quantity` maps to `TrancheOrder.FilledQuantity`. [1] A production cashflow engine should preserve the source's quantity and currency fields as trade attributes. Whether `Nominal`, quantity, a contract multiplier, or another convention scales the settlement amount is unresolved by the source and needs validation against the actual Murex configuration.

## Path dependence and lifecycle effects

The barrier state is **path dependent**. Terminal value \(V_T\) alone cannot determine payoff, because a knock-in requires a past hit and a knock-out requires proof that no hit occurred. A minimal lifecycle state machine is:

\[
\text{Unmonitored / Alive}
\xrightarrow{\text{barrier hit}}
\begin{cases}
\text{Activated}, & \text{knock-in},\\
\text{Extinguished}, & \text{knock-out},
\end{cases}
\xrightarrow{T}
\text{Terminal valuation and settlement decision}.
\]

For a knock-in, a hit makes the option active for final valuation. For a knock-out, a hit makes the option worthless under the no-rebate representation. If no relevant hit occurs, the respective reverse state persists through expiry. This state must be stored independently of the final fixing because it drives the final branch.

**Documented lifecycle dates** include `TradeDate`, `FinalFixingDate`, and `MaturityDate`. The source maps final fixing to the option expiration period and says maturity maps to final valuation date. [1] It does not state whether final fixing and maturity must coincide, whether the barrier observes on either date, or the settlement date after valuation. An implementation should retain both source dates and make any ordering rule configurable.

## From intake / flex data to payoff inputs

The following is the direct mapping that can be made from the source. `Specs` and `Variables` are the documented payload sections; they should not be mislabelled as an available native flex-block schema, because the source shows no such schema. [1]

| Source payload location | Murex target stated in source | Payoff-graph input or role | Treatment |
|---|---|---|---|
| `Specs.Cond0` | `Eq.Option.1.Buy/Sell` | \(\sigma\), the payer/receiver sign | Connect to the signed terminal result after validating allowed values. |
| `Specs.Cond1` | `Eq.Option.1.Payout` | \(\phi\), call or put choice | Select the vanilla payoff shape. |
| `Specs.Cond3` | `DiscrContinuos` | Observation convention and \(\mathcal O\) type | Select continuous or discrete monitoring; supply discrete dates separately because they are absent. |
| `Variables.StrikePrice` or `Variables.StrikeLevel` | `Strike` | \(K\) | Choose the populated, validated strike source; the source does not specify precedence if both are supplied. |
| `Variables.EQBarrierType` | `Barrier_Type` | Direction plus knock-in/knock-out mode | Parse the supported compound style, such as the documented example `Down and In`. |
| `Variables.BarrierLevelPercent` or `Variables.KOLevel` | `KO` | \(H\) | Normalize only with a documented conversion rule. The source says the level is often a percentage but does not define its base. |
| `Variables.UnderlyingTableList[*].T_TickerR` | `Eq.Option.1.Instrument` | Underlying identity | Bind the price process to the selected instrument. |
| `Variables.UnderlyingTableList[*].T_InitialPrice` | — | \(S_0\) | Retain for barrier-direction context and validation; it is not itself the terminal fixing. |
| `Variables.UnderlyingTableList[*].T_MXCalendar` | `CDR` | Calendar attribute | Preserve for date processing; its observation effect is not specified. |
| `Variables.FinalFixingDate` | Option expiration period | \(T\), valuation point | Use as final payoff valuation input, subject to the source's date ambiguity. |
| `Variables.MaturityDate` | Final Valuation Date | Lifecycle / valuation-date attribute | Reconcile with final fixing under a configured date-ordering rule. |
| `Variables.Quantity` | `TrancheOrder.FilledQuantity` | \(q\) | Apply only after confirming the market quantity convention. |
| `Variables.Currency` | `MAR_CCY` | Settlement-currency attribute | Carry as an output attribute; no FX rule is provided. |
| `Variables.Nominal` | `Nominal` | Trade attribute / possible scaling candidate | Keep as an input but do not insert in the formula without configuration evidence. |
| `Variables.TradeDate` | Trading Date | Trade lifecycle anchor | Use for booking chronology; no monitoring-start rule is supplied. |
| `Variables.Portfolio` | `Eq.Option.1.Portfolio` | Booking metadata | Not a payoff driver. |
| `Variables.ClientCounterpartyLabel` | `Eq.Option.1.Counterpart` | Counterparty metadata | Not a payoff driver. |

## Recommended explicit payoff graph

The following graph is **implementation guidance**, not documented Murex script logic. It makes the dependencies inspectable and avoids blending booking metadata with economics.

1. **Normalize and validate trade inputs.** Read buy/sell, call/put, barrier type, strike, barrier level, quantity, currency, underlying identifier, initial price, observation type, and lifecycle dates. Keep portfolio and counterparty outside the numerical payoff node.
2. **Parse the barrier type into two independent flags.** Produce `direction ∈ {up, down}` and `activation ∈ {in, out}`. Reject or route to manual review any value that cannot be parsed under the site's approved value list; the source provides only an example, not the exhaustive list.
3. **Build the observation schedule.** For continuous monitoring, attach the configured monitored interval. For discrete monitoring, require explicit observation dates and a price-source rule. Do not silently use a daily schedule, the exchange calendar, or the trade date as the start date, because the supplied source does not state those rules.
4. **Evaluate and persist the hit state.** Compare observed prices with \(H\) using an explicit equality convention. Store `hit=true/false` and, where available, hit timestamp and observed value. This permits correct valuation after a prior knock-in or knock-out event.
5. **Value the terminal vanilla node.** At the configured final fixing, calculate \(V_T=\max(\phi(S_T-K),0)\). The source does not identify whether cash or physical settlement applies, so this node should represent an entitlement amount rather than presume a settlement mechanism.
6. **Gate the terminal node.** Multiply by `hit` for a knock-in or by `1-hit` for a knock-out. Then apply the validated trade-side sign and confirmed quantity scaling. If nominal is a required multiplier in a particular configuration, add it only as a separately evidenced scaling node.
7. **Emit cashflow and audit state.** Attach the documented trade currency and retain input provenance, observation convention, barrier state, and valuation date. Generate separate nodes only for premium, rebate, funding, coupon, or principal when the actual trade configuration supplies their terms.

A concise graph representation is

\[
(\text{underlying observations}, H, \text{direction}, \text{observation convention})
\longrightarrow I
\]

\[
(S_T,K,\text{call/put})\longrightarrow V_T
\]

\[
(I,V_T,\text{in/out},\text{buy/sell},q)\longrightarrow P_T.
\]

## Limitations and unresolved points

The source supports the conceptual barrier branches and the field-to-Murex mapping, but leaves material implementation details open. The table below records the boundaries so a model does not turn omissions into contractual facts.

| Topic | What is documented | What remains ambiguous or absent |
|---|---|---|
| Barrier level | `BarrierLevelPercent` / `KOLevel` map to `KO`; the level is often expressed as a percentage. [1] | Percentage base, conversion to an absolute level, rounding, and precedence when both fields occur. |
| Barrier types | Knock-in, knock-out, up, and down are described; `Down and In` is an example. [1] | Exhaustive coded values, double barriers, and any special barrier variants. |
| Observation | Continuous versus discrete is mapped from `Cond3`. [1] | Monitoring start/end, discrete schedule, data source, equality rule, time zone, and holiday treatment. |
| Dates | Trade date, final fixing, and maturity fields are mapped. [1] | Date precedence, whether final fixing is observed for the barrier, payment / settlement date, and business-day adjustments. |
| Underlyings | An `UnderlyingTableList` contains one object per underlying. [1] | Whether BAROPT permits multiple economic underlyings, and how any basket or multi-underlying payoff would be formed. |
| Scaling and cashflows | Quantity and nominal are both captured; currency is a trade attribute. [1] | Contract multiplier, nominal's payoff role, premium, rebate, fees, funding, coupons, and principal. |
| Settlement | Final valuation is referenced. [1] | Cash versus physical settlement, delivered quantity, and settlement currency conventions. |
| Flex implementation | A flexible instrument is typically named `FLEX_USD` or similar. [1] | Header, blocks, scripts, input types, validation rules, and native generated cashflow definitions. |

**Practical conclusion.** BAROPT can be safely represented, from the supplied material, as a path-gated vanilla call or put with direction and monitoring convention supplied by the mapped fields. A production implementation must obtain the missing trade-template and Murex configuration details before it treats scaling, barrier conversion, observation scheduling, lifecycle ordering, or non-option cashflows as authoritative.

## References

[1]: ../Barrier_Option.md "Barrier Option (BAROPT) source document"
