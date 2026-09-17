# Outperformance Option — Payoff Specification

## Scope and evidence boundary

This chapter specifies the **documented economics, configuration inputs, observations, and lifecycle cashflow behavior** of Murex's Equity Outperformance Option (`Oprf`). It is based solely on the accompanying product note. That note describes the commercial intent and configuration but does **not** contain the literal payoff-program text, a closed-form payoff equation, or a definition of the performance-return convention. Consequently, the branch logic below distinguishes documented facts from implementation recommendations. In particular, any implementation must keep the numerical payoff calculation as an unresolved rule until the configured `Oprf` payoff script, the termsheet, or the referenced mapping definition has been inspected. [1]

## 1. Purpose and contract identity

An Outperformance Option is an exotic equity option that measures the relative performance of a basket constituent or a basket aggregate against a designated **reference asset**. A call is intended to benefit from outperformance of the selected non-reference exposure against that reference; a put is intended to benefit from underperformance. The product therefore targets relative performance rather than the absolute direction of an individual equity or the broader market. [1]

| Item | Documented value or role |
|---|---|
| Murex family | `EQD` |
| Murex group | `OPT` |
| Murex type | `FLEX` |
| Flex header / product naming | `Oprf` is the flex header/product name used to select the corresponding payoff script. |
| Attached flex block | A single `OPRF` block is attached to the flex header. |
| Basket form | `List of Assets`; the members are observed separately rather than being described as a single composite basket index. |
| Reference asset | The first stock in the basket list, position `0`. All remaining stocks, positions `1` through `n`, are evaluated against it. |

The pricing utility is instructed to use the payoff script corresponding to the `Oprf` flex header. The source does **not** disclose the script's internal name, source code, or expression. It also notes that configured field and block names must match the C++ mapping header `eqpr/content/mx/MxMapping.h`; the mapping itself is not reproduced. [1]

## 2. Observations and payoff state variables

### 2.1 Documented observation rules

The product has two payoff observations: an **initial fixing date**, when initial reference prices of all underlyings are determined, and the **maturity date**, which is the final fixing/valuation date. The source expressly says that Oprf uses only these initial and final fixing dates to determine the payoff. Each basket asset has an associated Publisher (Archiving table) and CutOff, and the historical fixing tables receive the market-data fixings. [1]

For unambiguous graph design, this chapter uses the notation below. The notation is an **implementation convention**, not a formula supplied by the source.

| Symbol / state variable | Meaning and source mapping | Status |
|---|---|---|
| `t0` | Initial fix date. | Documented input in `OPRF`. |
| `T` | Maturity date and final fixing/valuation date. | Documented main-ticket input. |
| `j = 0` | Reference-asset list position. | Documented basket rule. |
| `j = 1..n` | Non-reference basket asset positions. | Documented basket rule. |
| `P0[j]`, `PT[j]` | Initial and final fixing for asset `j`. | Convenient graph notation; the source documents the two fixing events but not a price symbol or adjustment convention. |
| `Perf[j]` | Performance of constituent `j` relative to asset `0`. | Required economic quantity, but its arithmetic definition is not disclosed. |
| `BasketPerf` | Selection mode: `Rank` or `AVG`. | Documented `OPRF` field. |
| `PerfRank` | Rank `k` used in `Rank` mode. | Documented `OPRF` field; inapplicable for `AVG`. |
| `CP` | Call or put direction. | Documented main-ticket field. |
| `K` | Strike performance barrier. | Documented main-ticket field. |
| `Cap`, `Floor` | Maximum cap and minimum floor on the payoff. | Documented `OPRF` fields. |
| `N` | Nominal / Quantity, described as the principal size of the deal. | Documented main-ticket field; scaling convention is not disclosed. |
| `SettlementMethod` | Cash / Delivery. Cash is described as typical, not mandatory. | Documented main-ticket field. |
| `FinalPayDate`, `LastPayAmount` | Final payment date and calculated final amount used by lifecycle processing. | Documented operational outputs. |

The source does not state whether prices are adjusted for corporate actions, how FX is handled, whether the basket quantities or weights enter the calculation, or how the Publisher and CutOff resolve a missing fixing. Those items must not be implied by the notation above. [1]

### 2.2 Basket-selection branches

The `Basket Perf` and `PerfRank` fields select the relative-performance measure that enters the option. The documented branches are as follows. [1]

| `Basket Perf` | `PerfRank` | Selected measure | Economic description |
|---|---:|---|---|
| `Rank` | `1` | Best performer | The best non-reference asset relative to the reference asset. |
| `Rank` | `k`, where `1 < k < n` | Middle performer | The `k`-th ranked non-reference asset relative to the reference asset. |
| `Rank` | `n` | Worst performer | The worst non-reference asset relative to the reference asset. |
| `AVG` | Not applicable; commonly `0` or blank | Average performance | The average performance of the basket relative to the reference asset. |

The source calls Rank `1` the best and Rank `n` the worst, which establishes the intended rank semantics. It does not define the exact ordering quantity, tie-break convention, treatment of equal performances, or behavior when `PerfRank` falls outside the valid range. [1]

## 3. Payoff and cashflow branches

### 3.1 Documented option branches

At final valuation, the selected performance is obtained either through the specified rank or through the average branch. A **call** is the outperformance direction: it pays when the selected stock or basket measure outperforms the reference. A **put** is the underperformance direction: it pays when the selected measure underperforms the reference. The strike is described as a performance barrier, and `Cap` and `Floor` are described as the maximum and minimum bounds on the payoff. [1]

The following is the most complete **documented decision structure**, without inventing an arithmetic formula:

```text
Initial fixing at t0
  └─ record the required initial fixing for reference asset 0 and assets 1..n

Final fixing at T
  ├─ BasketPerf = Rank
  │    └─ select the performance at PerfRank k
  │         ├─ k = 1: best performer
  │         ├─ 1 < k < n: middle performer
  │         └─ k = n: worst performer
  └─ BasketPerf = AVG
       └─ select the basket's average relative performance

Selected performance versus reference
  ├─ CP = Call: outperformance direction
  └─ CP = Put:  underperformance direction
       └─ apply the strike-performance barrier and the stated Floor/Cap terms
            └─ calculate LastPayAmount using the configured Oprf payoff script
```

The phrase “apply the strike, Floor and Cap” is intentionally not an equation. The source does not say whether a floor is applied before or after a cap, whether the floor and cap apply to a return, an amount, or a normalized option value, whether `N` is multiplicative, or whether a non-favourable call/put state yields zero before floor treatment. These are material payoff semantics that require the actual script or termsheet. [1]

### 3.2 Lifecycle and cashflow branches

The product note supplies explicit operational cashflow behavior. These branches should be represented separately from the valuation formula so that lifecycle action cannot silently alter the payoff calculation. [1]

| Lifecycle branch | Allow condition | Documented generated cashflow / effect |
|---|---|---|
| Expiry | Only on maturity date, after the last fixing is complete. | `[Final PayDate, 0]`. |
| Exercise (`EXR`) | Only on maturity date, after the last fixing is complete. Front Office must trigger it manually and validate payment date and amount. | `[Final PayDate, LastPayAmount]`. |
| Unwind (`XIT`) | Any day after trade start. | `[Current PayDate, Present Value]`. For a full unwind of a funded deal, a `BUY` bond booking offsets the original bond and `XIT` is performed on the flex deal. |
| Restructure | Any time during the trade lifecycle. | Default Murex behavior; used to reduce nominal for a partial unwind. Unwind fees are entered as additional flows in the restructured deal. |

The source identifies **Premium Currency**, but it does not provide a premium amount, premium payment date, payment sign, or premium-cashflow construction rule. It similarly does not give a delivery workflow despite exposing the Cash / Delivery field. An implementation must therefore preserve those as independent, unspecified cashflow inputs rather than deriving them from the option payoff. [1]

## 4. Economic-leg decomposition

The product note supports the following decomposition. It is a reporting and graphing decomposition, not a claim that Murex represents the legs as separately tradable instruments.

| Leg | Documented content | Treatment in an explicit payoff graph |
|---|---|---|
| Embedded relative-performance option | Call/put exposure to a selected basket measure versus the first-listed reference asset, with strike, Floor, and Cap fields. | Model as the central `OPRF` payoff node. Keep the performance formula and cap/floor sequencing opaque until the script is available. |
| Funding / principal | `Nominal / Quantity` is the deal's principal size. For **funded deals**, principal is reflected in a linked bond booking, which is left to expire naturally. | Represent the linked bond as a separate funding/principal subgraph. Do not infer a principal redemption cashflow on the flex option itself. |
| Coupon | No coupon field or coupon cashflow is documented for the Oprf flex deal. | Do not create a coupon leg. |
| Premium / fee | Premium Currency is an input. Restructured partial unwinds may include additional unwind-fee flows. | Use external premium and fee-flow nodes only when the actual economics provide their amounts and dates. |
| Residual lifecycle settlement | Final option settlement, zero expiry flow, `XIT` present-value settlement, and restructure effects are explicitly stated. | Connect these to lifecycle-event nodes, not to an assumed periodic cashflow schedule. |

This decomposition makes a key distinction: a funded transaction may comprise a flex option and a linked bond, but the source does not permit treating the option nominal as proof of an option-principal repayment. [1]

## 5. Source-field-to-payoff mapping

| Murex source field or object | Payoff-graph input / role | Notes |
|---|---|---|
| `EQD` / `OPT` / `FLEX` | Product classification and routing guard | Confirms the contract hierarchy; it is not a numerical input. |
| Flex header `Oprf` and its selected payoff script | Payoff-engine binding | Script must be the one corresponding to `Oprf`; its literal identity and expression are absent. |
| `OPRF.Cap`, `OPRF.Floor` | Payoff bounds | Mathematical units, signs, and order of application are unspecified. |
| `OPRF.Initial fix date` | Initial observation node `t0` | Capture a fixing per required asset. |
| `OPRF.Basket Perf` | Selector-mode switch | Valid documented modes are `Rank` and `AVG`. |
| `OPRF.PerfRank` | Rank-selector input `k` | Used in `Rank`; not applicable in `AVG`. |
| Basket Type = `List of Assets` | Independent constituent-observation topology | Avoid collapsing the basket into an unverified composite index. |
| Basket asset at position `0` | Reference-asset node | This ordering is economically material. |
| Basket assets at positions `1..n` | Candidate-performance nodes | They are compared with the reference. |
| Publisher and CutOff per asset | Fixing-source metadata | Use when resolving observations from historical fixing tables. |
| Nominal / Quantity | Sizing input `N` | Scaling formula is not disclosed. |
| Call / Put | Direction switch `CP` | Call = outperformance; put = underperformance. |
| Strike | Barrier input `K` | Defined as the strike performance barrier. |
| Maturity Date | Final observation and lifecycle eligibility date `T` | The final fixing/valuation date. |
| Cash / Delivery | Settlement-mode input | Cash is typical; delivery mechanics are not provided. |
| Exercise Convention | Payment-date override input | May redefine specific payment dates; exact rule absent. |
| Premium Currency | Premium-currency metadata | Does not establish premium amount or timing. |
| `EQ_MONTECARLO` / `EQ_OPRF` GMP configuration | Pricing-model routing | The note specifies this generator/group pairing. Other model settings follow the Kiko setting, but are not payoff inputs. |

## 6. Implementation recommendation: explicit payoff graph

> **Recommendation — not documented payoff arithmetic.** Use a graph whose central valuation node calls a versioned `Oprf`-script adapter. Do not reimplement the arithmetic from the product note alone.

A robust graph can use the following nodes and interfaces:

1. **Static terms node.** Store contract family/group/type, `CP`, `N`, `K`, `Cap`, `Floor`, settlement method, exercise convention, and premium currency. Validate `BasketPerf` against `Rank`/`AVG` and preserve `PerfRank` without assigning an `AVG` value that is not present in the trade.
2. **Basket topology node.** Consume the ordered `List of Assets`. Assert that position `0` exists and is marked as the reference. Send positions `1..n` to the candidate branch. Retain Publisher and CutOff on each observation edge.
3. **Observation nodes.** At `t0` and `T`, retrieve the approved fixings. A missing fixing must enter an exception state, not an estimated-price branch, because the source identifies historical-fixing data but gives no fallback method.
4. **Opaque relative-performance node.** Pass the two sets of fixings, the asset ordering, and contract terms to the approved Oprf script or a validated equivalent. This node must own the undocumented choices: return normalization, reference comparison, treatment of weights/quantities, corporate actions, rank order, ties, strike operator, floor/cap order, and nominal scaling.
5. **Selector audit node.** Record whether `Rank` or `AVG` was chosen, the requested `PerfRank` where relevant, the constituents observed, and the selected constituent or average. This preserves an explainable audit trail without asserting arithmetic that the source omits.
6. **Final-amount node.** Accept only the script result as `LastPayAmount`; avoid applying an additional cap, floor, or nominal multiplier outside the adapter unless a validated script specification says to do so.
7. **Lifecycle settlement node.** Route the result through the documented `EXR`, expiry, `XIT`, and restructure branches. Keep a linked funded bond and any premium/fee flows in separate subgraphs.

A compact graph representation is:

```text
Terms + ordered List of Assets
             │
             ├── position 0 ──► reference fixing at t0, T
             └── positions 1..n ──► constituent fixings at t0, T
                                      │
                                      ▼
                    Oprf-script adapter (relative performance,
                    Rank/AVG, Call/Put, Strike, Floor, Cap, sizing)
                                      │
                                      ▼
                              LastPayAmount
                         ┌────────────┴────────────┐
                         ▼                         ▼
                EXR at maturity             expiry at maturity
              [FinalPayDate, amount]      [FinalPayDate, 0]

Separate lifecycle branches: XIT → [CurrentPayDate, PresentValue];
restructure → reduced nominal and any separately entered fee flows.
Separate funded branch: linked bond booking, if applicable.
```

The graph should record the GMP pairing `TYPE = EQ_MONTECARLO` and `GROUP = EQ_OPRF` as a pricing-engine configuration, not as a payoff transformation. The note says other Monte Carlo settings follow the standard Kiko setting; this statement does not provide enough information to build model dynamics, discounting, or regression settings within this chapter. [1]

## 7. Short payoff tree

```text
Active Oprf trade
├─ Before final fixing: initial fixing is recorded at t0; await final fixing at T
├─ At T after final fixing
│  ├─ Rank: choose best / k-th / worst non-reference performance
│  └─ AVG: choose average basket relative performance
│       └─ Call (outperformance) or Put (underperformance)
│            └─ Script applies strike and stated Floor/Cap terms → LastPayAmount
│                 ├─ Manual EXR → [FinalPayDate, LastPayAmount]
│                 └─ Expiry → [FinalPayDate, 0]
├─ After trade start, before or at end of life: XIT → [CurrentPayDate, PresentValue]
└─ During life: restructure → default Murex processing; reduced nominal and optional separate fee flows
```

The exercise and expiry leaves are operationally distinct even if a script has calculated a positive amount: the source requires Front Office to manually trigger `EXR` and verify the final payment date and amount. [1]

## 8. Limitations and required clarifications

The following gaps are material and are **not** resolved by the source note:

- There is no literal `Oprf` payoff script, C++ mapping, or exact payoff equation. The underlying definition of relative performance, strike comparison, payoff sign, and `N` scaling is unknown.
- The order and units of `Floor` and `Cap` are not specified. It is therefore unsafe to assume a conventional `min(max(...))` clamp.
- The rank sort key, high/low ordering convention beyond the best/worst labels, tie-break behavior, invalid-rank behavior, and averaging methodology are not specified.
- The average branch is described as the average performance of all basket assets relative to the reference asset, while the general basket rule identifies positions `1..n` as the assets evaluated against position `0`. The note does not explicitly settle whether the reference asset is included as a zero-relative-performance component of the average.
- Quantities and weights appear on the basket screen, but the note does not say whether they affect the average or ranked performance. They must not be introduced into the graph without authoritative evidence.
- No price-adjustment, corporate-action, currency-conversion, holidays, missing-fixing, or Publisher/CutOff conflict rule is supplied.
- `Cash / Delivery`, exercise convention, and premium currency are exposed as fields, but delivery mechanics, payment-date conventions, premium amount, premium date, and cashflow sign are absent.
- The funded-deal bond is mentioned only operationally. Its terms, cashflows, and linkage mechanics are outside the Oprf payoff definition.
- The Monte Carlo generator/group pairing is stated, but the market model, correlation treatment, discounting, path count, regression configuration, and the referenced Kiko settings are not included in this source.

Before production implementation or valuation reconciliation, obtain the configured `Oprf` script, the applicable termsheet, the mapping header named in the source, and representative trade/fixing test cases. These artifacts are necessary to turn the opaque script-adapter node into a verified explicit numerical payoff.

## References

[1]: refs/MurexPlaybook/Products/Other_Exotics/Outperformance.md "Equity Outperformance Option (Oprf)"
