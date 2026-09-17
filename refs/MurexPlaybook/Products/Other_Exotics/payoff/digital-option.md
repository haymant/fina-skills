# Digital Option — Payoff Chapter

## 1. Purpose and scope

An **Equity Digital Option** is a binary, or all-or-nothing, equity option. At expiry, the final underlying price is tested against the strike. A successful test produces a pre-determined payoff; an unsuccessful test produces no payoff. The source identifies a Digital Call as paying when the final price is above the strike and a Digital Put as paying when it is below the strike.[1]

This chapter describes the documented product economics and expresses them as a payoff-graph design. **Documented facts** are attributed to the source. Items explicitly labelled **implementation recommendation** are a transparent way to encode those facts; they are not claimed to be Murex product specifications.

## 2. Murex representation and pricing metadata

The documented Murex booking hierarchy is shown below.

| Representation element | Documented value | Role in this chapter |
|---|---|---|
| Family | `EQD` | Product-family identification |
| Group | `OPT` | Option grouping |
| Type | `FLEX` | Indicates a Flex-based representation |
| Flex header | `EqFlexDOpt` | Header for the Digital Option representation |
| Flex block | `DIGITAL` | Defines the exercise behaviour when fixing equals strike |
| Pricing payoff script | `EqFlexDOpt` | Script named as used for pricing |

The source also records a Generic Market Parameters configuration for Monte Carlo pricing: `TYPE = EQ_MONTECARLO`, `GROUP = EQ_DIGOPT`, `Nb of Paths = 10000`, `Regression Order = 1`, and `Cashflows = 0`.[1] These are **documented configuration values**, not an assertion that the economic payoff necessarily requires Monte Carlo simulation or that the listed values should be changed or generalized.

## 3. Payoff state and observation rules

### 3.1 Documented payoff state

Let the following notation represent the fields and observations described by the source.

| Symbol / state | Meaning | Source basis |
|---|---|---|
| \(S_T\) | Final price / fixing price of the underlying at expiry | The source tests final price at expiry and refers to `Fixing Price = Strike` |
| \(K\) | Strike price | Main ticket field |
| \(T\) | Maturity date / expiry observation date | Main ticket field; payoff condition is tested at expiry |
| \(D\) | Direction: Call or Put | Main ticket field |
| \(M\) | Settlement selection: Cash or Delivery | Main ticket field |
| \(A\) | Nominal or Quantity, as applicable | Main ticket field |
| \(E\) | `DIGITAL` block setting governing the equality case | Flex-block field |

The source documents one terminal price observation: the underlying's final price at expiry. It does **not** state a monitoring schedule, an averaging method, the source/time of the fixing, a settlement date, a settlement currency, or a numerical representation for the `DIGITAL` equality convention. Those matters must not be inferred from this payoff description.[1]

### 3.2 Strict in-the-money rules

For the strict inequalities documented in the source, define the eligibility indicator \(I\):

\[
I_{\mathrm{call}} = \mathbf{1}_{\{S_T > K\}}, \qquad
I_{\mathrm{put}} = \mathbf{1}_{\{S_T < K\}}.
\]

Thus, a Call is eligible only above strike and a Put only below strike. The equality state \(S_T = K\) is deliberately not folded into either strict rule: the `DIGITAL` Flex block exists specifically to define the exercise behaviour at that edge case.[1]

> **Documented fact:** The `DIGITAL` block controls the behaviour for `Fixing Price = Strike`; dealers may configure it according to the trade terms. The source does not enumerate its possible settings or say whether equality results in exercise, expiry, or another outcome.[1]

**Implementation recommendation:** represent the equality result as a distinct configured Boolean or branch, \(I_{=} = \operatorname{ResolveDigitalEquality}(E)\), rather than silently treating equality as in- or out-of-the-money. This preserves the documented Flex dependency and prevents a strict comparison from overriding negotiated terms.

## 4. Cashflows and complete payoff branches

### 4.1 Cash settlement

For cash settlement, the documented payoff is the fixed `Notional` amount if the option is in the money and zero otherwise.[1] Subject to the equality resolution above, this can be represented as:

\[
\text{Cash payoff} = \begin{cases}
\text{Notional}, & \text{Call and } S_T>K,\\
\text{Notional}, & \text{Put and } S_T<K,\\
\text{Notional or }0, & S_T=K\text{, as determined by }E,\\
0, & \text{otherwise.}
\end{cases}
\]

The supported settlement combination explicitly documented is **Nominal + Cash**. A zero branch has no positive option settlement cashflow in this payoff description.[1]

### 4.2 Asset delivery

For asset settlement, the source says that a number of shares equal to `Notional * asset` is delivered when the payoff condition is satisfied.[1] The source uses the word `asset` in that expression without defining it as a ticket field, unit conversion, price, or multiplier. Accordingly, the documented branch is recorded faithfully as:

\[
\text{Delivered shares} = \begin{cases}
\text{Notional} \times \texttt{asset}, & \text{eligible under direction and equality rule},\\
0, & \text{otherwise.}
\end{cases}
\]

The documented supported combination is **Quantity + Delivery**. The source lists **Quantity + Cash**, **Nominal + Delivery**, and **Quantity + Delivery + Quanto** as unsupported.[1]

### 4.3 Branch completeness

The following tree expresses every terminal comparison branch without assigning an unprovided equality convention.

```text
Maturity / expiry T
└── Observe final underlying price S_T against strike K
    ├── S_T > K
    │   ├── Call: eligible → Cash: Notional; Delivery: documented shares formula
    │   └── Put: zero payoff
    ├── S_T < K
    │   ├── Put: eligible → Cash: Notional; Delivery: documented shares formula
    │   └── Call: zero payoff
    └── S_T = K
        └── Apply DIGITAL block setting E
            ├── eligible under E → settlement selected by Cash/Delivery
            └── not eligible under E → zero payoff
```

The delivery branches in the tree describe the source's stated asset-settlement economic result. They should be instantiated only where the documented settlement-combination constraint permits them.

## 5. Economic leg decomposition

The source is a payoff/configuration description and does not provide a premium, funding schedule, coupon schedule, fee schedule, discounting method, or separate principal exchange. The appropriate decomposition is consequently intentionally narrow.

| Leg category | Documented treatment | Payoff-graph interpretation |
|---|---|---|
| Funding / principal | No funding or principal leg is specified | **No node should be fabricated.** If a surrounding trade model supplies premium or funding records, represent them separately from this documented option payoff. |
| Coupon / fee | No coupon or fee is specified | **No node should be fabricated.** |
| Embedded option | The terminal digital condition is the core economic leg | A single contingent entitlement selected by Call/Put, final-price comparison, and equality setting |
| Residual settlement leg | Cash is a fixed Notional amount; delivery is the stated shares expression | Terminal cash-payment or asset-delivery node following the eligibility decision |

> **Implementation recommendation:** distinguish the **binary eligibility leg** from the **settlement realization leg**. The first produces a 0/1 decision. The second turns an eligible decision into either a cash amount or a delivery quantity. This prevents the cash and delivery representations from being conflated and makes the equality decision auditable.

## 6. Path dependence and lifecycle effects

### 6.1 Path dependence

The documented payoff is **terminal-state dependent**: it relies on the final price at expiry relative to strike. There is no stated barrier, running observation, averaging, ratchet, memory feature, or interim exercise rule. The only explicitly described special state is equality at the expiry fixing, governed by the `DIGITAL` block.[1]

The source does not establish whether the contractual product is American, Bermudan, or European by name. It does state that the payoff condition is assessed at expiry; this chapter therefore does not infer any earlier exercise opportunity.

### 6.2 Operational lifecycle

If the option is in the money at expiry, Market Operations runs an exercise procedure. For out-of-the-money deals, the source says the option is either exercised or allowed to expire with a zero payoff.[1] The `EXR` operation creates an “exercize” ticket with different defaults according to the deal representation:

| Deal representation | Documented `EXR` outcome |
|---|---|
| Nominal deal | An exercise ticket with the default calculated payoff amount; the amount can be amended |
| Quantity deal | An exercise ticket with zero payment amount that populates a new deal that can be modified |

These statements describe operational processing, not a different valuation formula. In particular, a user amendment or modification mentioned in the operational process should not be treated as an automatic payoff parameter in the pricing graph unless an implementation separately governs it.

## 7. Mapping ticket and Flex inputs into a payoff graph

### 7.1 Source-to-input map

| Source field / block | Payoff-graph input | Use |
|---|---|---|
| Nominal/Quantity | `amount_or_quantity` | Identifies the size field present on the ticket; apply only in the documented settlement combination |
| Call/Put | `direction` | Chooses \(S_T>K\) or \(S_T<K\) test |
| Cash/Delivery | `settlement_mode` | Chooses a cash-payment versus asset-delivery realization |
| Maturity Date | `expiry_date` | Dates the final observation / terminal decision |
| Strike Price | `strike` | Threshold for the final-price comparison |
| `DIGITAL` Flex-block setting | `equality_rule` | Resolves \(S_T=K\) without inventing its semantics |
| Final price / fixing price | `final_fixing` | Observed market value supplied to the terminal comparison |
| `EqFlexDOpt` header | `product_schema` metadata | Identifies the Flex header carrying the `DIGITAL` block |
| `EqFlexDOpt` payoff script | `pricing_script` metadata | Identifies the documented pricing script; it is not itself an additional payoff input |

### 7.2 Recommended explicit graph

**Implementation recommendation:** build the payoff as the following directed acyclic graph, with an external process supplying `final_fixing` on `expiry_date`:

```text
[Ticket: direction, strike, expiry_date]
                 + [Observed final_fixing at expiry]
                 │
                 v
       [Strict comparator: above / below / equal]
                 + [DIGITAL equality_rule]
                 │
                 v
          [Eligibility: 0 or 1]
                 + [Ticket: Cash / Delivery]
                 │
          ┌──────┴──────┐
          v             v
[Cash amount = Notional] [Delivery quantity = documented Notional × asset]
          │             │
          └──────┬──────┘
                 v
     [Terminal settlement output or zero]
```

Validation should first reject documented unsupported settlement configurations. It should also preserve the distinction between `Nominal` and `Quantity` rather than converting one into the other, because the source permits only **Nominal + Cash** and **Quantity + Delivery**. The source permits Quanto (`S.1-K`) and the default case with premium currency equal to underlying currency; it does not support Basic (`S-K)X`) or Composite (`SX-K`) FX rules.[1] These FX-rule constraints are validation metadata in this chapter; no FX conversion payoff is specified by the source.

The product has a documented maximum tenor of **two years**. **Implementation recommendation:** enforce this as a booking or product-validation rule using the system's authoritative date-count policy, rather than embedding an assumed day-count convention into the payoff formula. The source supplies no date-count convention.[1]

## 8. Limitations and unresolved ambiguities

The following points are intentionally left open because the source does not provide the necessary definition.

| Topic | What is documented | Limitation for a standalone payoff implementation |
|---|---|---|
| At-strike outcome | Controlled by `DIGITAL` | Allowed values and exact result are not listed; an explicit configuration mapping is required |
| Delivery amount | “number of shares equal to `Notional * asset`” | `asset` is not defined; its unit, value, and relation to Quantity are ambiguous |
| Observation convention | Final price / fixing price at expiry | Fixing source, timestamp, price adjustment, calendar, and fallback are unstated |
| Settlement mechanics | Cash or Delivery | Settlement date, currency, delivery venue, and asset identifier are unstated |
| Cash-flow scope | Binary cash amount / asset delivery | Premium, funding, fees, taxes, margins, and discounting are outside the supplied description |
| Exercise process | `EXR` ticket behaviour is described | Amendability/modification is operational; it does not define a new contractual payoff branch |
| Equality in operations | `DIGITAL` addresses equality for the product | The source does not say how an equality result interacts with the out-of-the-money exercise-or-expire operational choice |

No parameter has been added to resolve these gaps. A production implementation should obtain the missing conventions from the authoritative product schema, trade terms, and operations design before assigning values.

## References

[1] [Digital Option source document](Products/Other_Exotics/Digital_Option.md), `refs/MurexPlaybook/Products/Other_Exotics/Digital_Option.md` (repository-relative source path).
