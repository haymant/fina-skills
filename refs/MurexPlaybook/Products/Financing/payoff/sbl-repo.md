# SBL and Basket Repo Financing: Payoff Interpretation

## Purpose and scope

**Stock borrowing/lending (SBL)** and **Basket Repo** are financing structures that exchange securities for either a fee, cash, or other securities. In the source playbook, their stated business uses are financing positions, covering short sales, and managing collateral. The source distinguishes four economic variations: vanilla SBL, cash-backed basket SBL financing, Basket Repo, and collateral swaps. [1]

This chapter separates **documented facts** from **implementation recommendations**. The source is a risk-overview document, not a contractual cashflow specification. It defines only a small number of economic legs and risk measures; it does not provide dates, currencies, quantities, rate conventions, fee formulas, collateral substitutions, close-out terms, or Murex Flex code. Consequently, the payoff descriptions below preserve the stated economics without filling those gaps with assumed parameters.

> **Interpretive boundary.** A risk exposure formula is not itself a contractual payoff. The source’s settlement-risk and potential-credit-exposure calculations are therefore shown as monitoring outputs, not booked economic cashflows.

## Product taxonomy and Murex classification

The following table records the classifications actually present in the source. Product labels are business descriptions; the source does **not** supply a Murex trade-family name, Murex product-group identifier, booking type code, Flex header, or payoff-script identifier. The documented limit routing (`EQ_SBL`, `CN_SBL`) is a counterparty-risk grouping, not evidence of a deal-product group. [1]

| Economic variation | Documented purpose / exchange | Murex family, group, and type evidence | Cash component in source |
|---|---|---|---|
| **Vanilla SBL** | An equity or bond is lent against a fee. | Described as an equity/bond SBL product type; no configured Murex family or type code is given. | No accompanying cash leg. [1] |
| **SBL Financing (Basket)** | A basket of securities is lent against a cash amount. | Described as an SBL financing/basket product type; no configured Murex family or type code is given. | Yes. [1] |
| **Basket Repo** | A basket is exchanged for cash and is to be reversed on a future date. | Described as a Basket Repo product type; no configured Murex family or type code is given. | Yes. [1] |
| **Collateral Swap** | A package combines SBL and Basket Repo components to exchange one form of collateral for another. | No configured Murex family or type code is given. | The risk section states that it has no cash component for the stated settlement-risk calculation. [1] |

**Documented Murex limit grouping.** The source says that these products are routed to dedicated groups `EQ_SBL` and `CN_SBL` for potential-credit-exposure (PCE) monitoring. It does not state which trade or counterparty condition selects one group rather than the other. [1]

## Flex header and payoff-script availability

No Flex header, Flex block, script text, script version, generated event name, or payoff function is included in the source. It is therefore not possible to reproduce, validate, or claim the existence of a Murex payoff script from this material.

**Implementation recommendation.** Keep the economic product label, risk agreement tag, cash/security legs, and risk-calculation fields separate in the deal graph. If a downstream configuration contains a Flex header or script, treat that artifact as the authority for event timing and signed amounts. Do not infer a script merely from the high-level labels in the table above.

## State variables and observation rules

### Documented variables

The source supplies the following variables for risk treatment. It does not identify a formal payoff state vector or its observation calendar.

| Symbol | Meaning in this chapter | What the source says | Observation rule supported by the source |
|---|---|---|---|
| \(MV_t\) | Market value of the security or securities basket at evaluation time \(t\) | Used in simplified PCE calculations. [1] | The source assumes daily margining under GMRA or GMSLA, but does not state a valuation time, price source, or business-day convention. [1] |
| \(C_t\) | Cash amount being exchanged at evaluation time \(t\) | Used in settlement-risk and basket PCE calculations. [1] | Present only for the cash-exchange structures discussed below; no reset or accrual rule is given. |
| \(h\) | Haircut | Used in the no-cash equity/bond SBL PCE formula. Trade-level haircuts are captured through UDFs for the discussed calculation. [1] | No range, sign convention, or update rule is specified. |
| \(A_t\) | PCE add-on | Added in both simplified PCE formulas. [1] | No construction, calibration, or frequency is specified. |
| \(G\) | Governing-agreement tag | GMSLA is required for SBL, GMRA for Repo, and BMLA may be represented in the ISDA field for China-based entities when GMSLA is absent. [1] | Tested by an automated pre-deal sanity check. [1] |
| \(N\) | Trade notional amount | Mentioned only for the punitive pre-deal exposure. [1] | No contractual definition, currency, or relation to \(MV_t\) is given. |

The documented monitoring relationships are:

\[
SR_t = C_t
\]

for transactions involving a cash exchange, namely SBL Financing (Basket) and Basket Repo, and

\[
PCE_t^{\mathrm{no\ cash}} = MV_t \times h + A_t
\]

for equity/bond SBL without cash. For Basket Repo and SBL Financing, the simplified relationship is

\[
PCE_t^{\mathrm{cash\ basket}} = \left|MV_t - C_t\right| + A_t.
\]

These equations are documented risk measures. They do not establish that \(MV_t\), \(C_t\), \(h\), or \(A_t\) is settled as a deal cashflow. [1]

### Observation and lifecycle effects

**Documented facts.** Correct governing-agreement tags are a booking gate. An SBL booking without GMSLA, or without the permitted BMLA treatment for the stated China case, fails its pre-deal check. Repo has an analogous GMRA check. The resulting workflow temporarily allocates a punitive risk exposure equal to \(100\%\) of notional until resolved. [1]

The PCE discussion assumes that GMRA- or GMSLA-governed transactions are daily margined. It explains this as requiring additional collateral to maintain the agreed haircut when security market values move, reducing the stated effective market exposure to the difference between securities value and exchanged cash. [1] This is **path dependent for risk monitoring** because a later \(MV_t\) and any collateral response affect exposure. The source does not provide the margin-call schedule, settlement mechanism, threshold, minimum transfer amount, or cashflow events required to turn that statement into a contractual margin payoff.

**Implementation recommendation.** Model agreement validation as a pre-booking/lifecycle state and model daily margin as a separate collateral process, not as an assumed coupon. Persist observed \(MV_t\), \(C_t\), \(h\), and \(A_t\) with their effective dates. Add only the margin transfers that a confirmed term sheet or Flex implementation explicitly creates.

## Economic payoff branches

The source specifies economics qualitatively. To keep directions neutral, let \(Q^{sec}\) denote the agreed security or basket delivery and let \(F\) denote the stated SBL fee amount, if any. A plus/minus sign below is from one designated party’s perspective; the opposite party receives the sign-reversed leg. Neither \(Q^{sec}\) nor \(F\) is parameterized in the source.

### Vanilla SBL: security loan plus fee

**Documented facts.** Vanilla SBL is a straightforward loan of an equity or bond against a fee and has no accompanying cash leg. [1]

| Component | Payoff treatment warranted by the source | What must not be inferred |
|---|---|---|
| Funding / principal | No cash funding or principal leg is documented. | Do not synthesize a cash consideration from the fee. |
| Coupon / fee | A fee leg exists conceptually: \(\pm F\). [1] | The amount, payer, accrual basis, dates, currency, and payment frequency are not specified. |
| Embedded option / residual | No embedded option or residual payoff is described. | Do not introduce recall, termination, manufactured-payment, substitution, or exercise features. |

A security-loan graph may include security delivery and return **only when contractual terms confirm those events**. The source calls the transaction a loan but does not specify its opening, return, or termination dates.

### SBL Financing (Basket): securities against cash

**Documented facts.** SBL Financing (Basket) lends a securities basket against a cash amount. It is subject to the stated settlement-risk measure, \(SR_t=C_t\), and its simplified PCE is \(\left|MV_t-C_t\right|+A_t\). [1]

| Component | Payoff treatment warranted by the source | What must not be inferred |
|---|---|---|
| Funding / principal | A security-basket exchange against a cash amount is present: \(\mp Q^{sec}\) and \(\pm C\). [1] | The initial settlement date, reversal date, and whether cash resets are absent. |
| Coupon / fee | No fee, financing rate, coupon, or accrual formula is supplied. | Do not derive interest from the word “financing.” |
| Embedded option / residual | No optionality or residual leg is documented. | Haircut and PCE add-on are risk inputs, not option payoffs. |

### Basket Repo: initial exchange and contractual reversal

**Documented facts.** A Basket Repo exchanges a securities basket for cash and includes an agreement to reverse the transaction at a future date. [1] This is the only product in the source with an explicit forward reversal statement.

For an implementation-neutral party perspective, the minimum two-stage representation is

\[
\begin{aligned}
\text{Opening:} && \mp Q^{sec}_0 &\quad \pm C_0,\\
\text{Reversal at } T: && \pm Q^{sec}_T &\quad \mp C_T.
\end{aligned}
\]

Here \(C_0\), \(C_T\), \(Q^{sec}_0\), and \(Q^{sec}_T\) are deliberately generic contractual quantities. The source confirms the exchange and reversal but does not say whether the returned cash amount differs from the opening cash amount, or why it might differ.

| Component | Payoff treatment warranted by the source | What must not be inferred |
|---|---|---|
| Funding / principal | Cash and security-basket legs at the exchange, with corresponding reversing legs at a future date. [1] | Repo rate, repurchase price formula, accrued interest, term, and settlement calendar are absent. |
| Coupon / fee | No standalone coupon or fee is stated. | A financing return cannot be calculated from the available text. |
| Embedded option / residual | No embedded option or residual payoff is described. | Do not add substitution, margin-option, early-termination, or buy-in logic. |

### Collateral swap: package-level component treatment

**Documented facts.** A collateral swap combines SBL and Basket Repo components to exchange one type of collateral for another. The same source says collateral swaps do not have a cash component for its settlement-risk calculation. [1]

The resulting payoff is **not fully determinable** from the document. In particular, the statement that the package combines SBL and Basket Repo components sits alongside the source’s settlement-risk scope that excludes collateral swaps because they have no cash component. This may describe a net or package treatment rather than every component’s gross movement, but the source does not resolve it.

**Implementation recommendation.** Represent the package as a container with separately identified SBL and Repo component graphs. Suppress or net cash only where the actual booking terms or Flex configuration explicitly directs it. Do not use the settlement-risk exclusion alone to conclude that every underlying repo cash leg has been eliminated.

## Short payoff tree

```text
SBL / Repo financing trade
|
+-- Vanilla SBL
|   +-- security loan (delivery/return dates not documented)
|   +-- fee ±F; no cash funding leg
|
+-- SBL Financing (Basket)
|   +-- securities basket ↔ cash amount ±C
|   +-- no documented rate, fee, or reversal schedule
|
+-- Basket Repo
|   +-- opening: securities basket ↔ cash C0
|   +-- future reversal: securities basket ↔ cash CT
|
+-- Collateral Swap
    +-- package of SBL and Basket Repo components
    +-- no package payoff decomposition documented
```

## Mapping from source/Flex blocks to payoff inputs

There are **no source Flex blocks to map**. The table below is therefore an implementation adapter, not a statement about an existing Murex layout. It provides a controlled mapping for an eventual Flex header or deal extractor while retaining `Not documented` where the source supplies no field.

| Source concept or prospective block | Proposed payoff-graph input | Provenance and constraint |
|---|---|---|
| Product variation selector | `product_variant` = Vanilla SBL / SBL Financing (Basket) / Basket Repo / Collateral Swap | The four labels are documented. [1] A configured code is not. |
| Security or basket | `security_leg` with identity and signed quantity | A security or basket exchange/loan is documented. Security identifier, quantity, currency, settlement date, and substitutions are not. |
| Cash amount | `cash_leg.amount = C` | Documented for SBL Financing and Basket Repo. [1] Direction, currency, and schedule are not. |
| SBL fee | `fee_leg.amount = F` | A vanilla-SBL fee is documented. [1] Its calculation and schedule are not. |
| Repo reversal | `reversal_event` with future date and reversing security/cash legs | Only Basket Repo has an explicitly stated future reversal. [1] Returned amounts and date are not supplied. |
| Agreement tag | `legal_agreement` = GMSLA / GMRA / permitted BMLA treatment | Used as lifecycle eligibility/risk-routing data, not as a cashflow amount. [1] |
| Market value, haircut, add-on | `risk_state = (MV_t,h,A_t)` | Inputs to simplified risk measures. [1] They should not automatically generate economic legs. |
| Cash amount for risk | `risk_state.cash = C_t` | Drives the stated SR/PCE formulas where applicable. [1] |
| Limit group | `risk_route` = `EQ_SBL` or `CN_SBL` | Documented routing groups, but selector logic is absent. [1] |
| Flex header / payoff script | `script_ref`, `event_rules` | **Not documented.** Populate only from actual configuration. |

## Recommended explicit payoff graph

The following graph design is an **implementation recommendation**. It is designed to make economic movements, risk states, and lifecycle controls auditable without treating risk formulas as settlement legs.

1. Create a **Trade Root** node with `product_variant`, party orientation, and trade identity. The party orientation determines every cash and security sign.
2. Attach an **Agreement Validation** node carrying `legal_agreement`. Before activation, evaluate the documented GMSLA/GMRA/BMLA condition. A failure routes to a risk-workflow state with the documented temporary \(100\%\times N\) exposure; it must not emit an invented contractual cashflow. [1]
3. Attach one or more **Economic Leg** nodes. Vanilla SBL has a fee node and confirmed security-loan events. SBL Financing has a security node plus cash node. Basket Repo has paired opening and future-reversal security/cash nodes. Collateral Swap is a package node whose components remain explicit until terms prescribe netting.
4. Attach a **Risk-State** node containing \(MV_t\), \(C_t\), \(h\), and \(A_t\). Compute `SR` and simplified `PCE` in a separate risk-output subgraph using the documented equations. [1]
5. Attach a **Margin Lifecycle** node only if actual deal data defines calls and transfers. It may observe daily \(MV_t\), consistent with the source’s daily-margin assumption, but must not manufacture transfer amounts or schedules. [1]
6. Reject graph validation if a branch needs an unspecified amount, date, direction, or convention. The validation output should identify the missing contractual input rather than defaulting it.

A compact logical graph is:

```text
Trade Root
 ├─ Agreement Validation ──fail──> Workflow / temporary risk exposure 100% × N
 ├─ Economic Legs
 │   ├─ Security or basket delivery
 │   ├─ Cash exchange (only where documented)
 │   ├─ Vanilla-SBL fee (only where documented)
 │   └─ Repo future reversal (Basket Repo only)
 └─ Risk-State Observations ──> SR and PCE outputs
       (MVt, Ct, h, At; not contractual cashflows)
```

## Limitations and unresolved ambiguities

The document is intentionally high level, so the following elements cannot be calculated or configured from it alone:

- **Cashflow specification:** no dates, currency, settlement calendar, direction convention, quantities, rate, day count, compounding, fee frequency, or price/reset formula is stated.
- **Security-leg detail:** there is no instrument identifier, basket composition, valuation source, corporate-action treatment, substitution rule, or delivery/return convention.
- **Margin mechanics:** daily margining is an assumption for the described risk calculation. Thresholds, timing, eligible collateral, transfer direction, and whether margin itself is a booked event are not provided. [1]
- **Legal and routing logic:** required agreement tags are stated, but the full counterparty-tag implementation and the rule selecting `EQ_SBL` versus `CN_SBL` are not. [1]
- **Package treatment:** the collateral-swap description and its settlement-risk exclusion do not provide enough detail to decide gross versus net component cashflows.
- **Optionality:** the source contains no optionality, termination, default close-out, recall, or residual-value terms. No embedded option valuation follows from the text.
- **Wrong-way risk:** Bond SBL is stated to have explicit WWR; equity SBL does not require it; Basket Repo incorporates it in the Structured PCE add-on; and collateral-swap treatment depends on components. [1] These are risk-treatment statements, not payoff branches.

The appropriate completion criterion for an implementation is therefore modest: it should reproduce the documented exchange structure and risk relationships, visibly label absent contract terms, and require authoritative deal/Flex configuration before producing an executable cashflow schedule.

## References

[1]: ../SBL_Repo.md "Product and Risk Overview: SBL & Basket Repo"
