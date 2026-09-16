# Reverse KIKO (KioV): Payoff Specification and Murex Implementation Guide

**Product identifier:** EQ Reverse KIKO (`KioV`)  
**Murex representation:** `EQD` / `OPT` / `FLEX`  
**Flex header and pricing payoff:** `EqFlexKioV`

## 1. Purpose and scope

The **Reverse KIKO**, also called **KioV**, is a path-dependent equity-linked structured option. It may reference one equity or a basket. Its barrier tests use the basket’s **Best Performer (BPS)** rather than the worst performer. During the life of the trade, one or both knock-out mechanisms can end the contract. If the trade reaches maturity without a knock-out, the result depends on whether a knock-in has occurred. [1]

This chapter interprets the documented payoff into an explicit state-and-cashflow design. It does **not** add an investment objective, a yield promise, a BPS calculation methodology, or any contractual parameter that is not described in the source. In particular, “BPS” is retained as a model-supplied value: the source names it as the best performer but does not specify whether it is a price, a normalized performance, or the precise basket aggregation rule. [1]

> **Evidence convention.** Statements labelled **Documented** describe the supplied product specification. Statements labelled **Implementation recommendation** set out a robust way to represent that specification in an explicit payoff graph. Where the source does not resolve a point, the chapter says so rather than selecting a convention.

## 2. Murex trade identity and input surface

**Documented.** The trade is booked as a flexible equity option in family `EQD`, group `OPT`, and type `FLEX`. Selecting the `EqFlexKioV` pricing payoff on the main trade screen loads the `EqFlexKioV` flex header and the four product blocks: `KIKOSEL*`, `LOCALKO*`, `GLOBALKO*`, and `KNOCKIN*`. The main financial-definition fields identified as material are **Nominal**, **Maturity Date**, and **Premium Ccy**. Standard option fields such as an ordinary strike or call/put indicator are described as dummy fields for this product. [1]

The source names `EqFlexKioV` as the pricing payoff script, but does not provide its program text. Consequently, this chapter specifies the documented economic branches and identifies script-dependent details that should be validated against an actual Murex configuration or valuation run.

| Flex source | Documented inputs or functions | Payoff-graph mapping |
|---|---|---|
| Main trade | Nominal, maturity date, premium currency | Store as `N`, `T`, and `ccy`; do not use ordinary option strike or call/put fields as economics. |
| `KIKOSEL*` | Enable/disable switches for local KO, global KO, and KI; Return Ratio (%); initial fixing date; initial fixing prices for each basket member | Create feature flags `f_L`, `f_G`, and `f_I`; store `r` for Return Ratio and the initial-fixing records. Pass the fixing records to the BPS engine, without assuming their formula. |
| `LOCALKO*` | Periodic local-KO observation and effective-date schedules; local/global comparison controls; local barriers and coupons; period-specific global barriers and coupons; historical KO status | Create local observation rows and a period map. The rows provide local threshold/coupon pairs and provide the active period for global parameters. Preserve comparison controls and status as operational inputs. |
| `GLOBALKO*` | Daily global-KO schedules; discrete close or continuous intraday monitoring; global payment timing, either period end or KO date shifted by calendar days | Create global monitoring set, monitoring-mode flag, and payment-date resolver. |
| `KNOCKIN*` | KI barrier and schedule; discrete or continuous monitoring; Cap, Floor, Knock-In Strike (%); Rebate or default no-KI payoff settings | Create KI monitoring set/mode, threshold, and the maturity outcome parameters. |

**Documented.** If local KO is disabled, local observation dates can still be generated because they define periods for global coupons and barriers. If both KO mechanisms are disabled, the user interface generates one standard-style period with a dummy barrier of `99999` and an observation date at maturity. [1]

**Implementation recommendation.** Treat the feature flags, rather than a generated dummy barrier or schedule row, as the authority for whether a KO test exists. A disabled KO feature must contribute no trigger, even if a schedule record remains available for period administration.

## 3. Payoff state and observations

Let \(B_t\) denote the BPS value supplied for the relevant observation time \(t\). This notation does not assert how BPS is calculated. Let \(T\) be maturity, \(r\) the configured Return Ratio, and \(f_L,f_G,f_I\in\{0,1\}\) the feature-enable flags.

For each local period \(j\), define the documented row inputs \((\ell_j,e^L_j,\bar B^L_j,c^L_j)\), where \(\ell_j\) is the local observation date, \(e^L_j\) is its effective-date record, \(\bar B^L_j\) is the Local Barrier Price, and \(c^L_j\) is the Local KO Coupon. Global parameters are period-specific in `LOCALKO*`; write their active-period values as \((\bar B^G_{p(t)},c^G_{p(t)})\). The mapping \(p(t)\) assigns a global observation to its local period.

The local trigger candidate and global trigger candidate are therefore:

\[
\tau_L=\inf\left\{\ell_j:\ f_L=1\ \text{and}\ B_{\ell_j}\leq \bar B^L_j\right\},
\]

\[
\tau_G=\inf\left\{t\in\mathcal G:\ f_G=1\ \text{and}\ B_t\leq \bar B^G_{p(t)}\right\}.
\]

Here \(\mathcal G\) is the configured global schedule. Under **Discrete** global monitoring, the test uses close prices on that schedule. Under **Continuous** global monitoring, it uses intraday prices while trading. [1] If neither set is non-empty, its corresponding time is \(\infty\).

The KI flag is a memory state, not a payment event:

\[
I=\mathbf{1}\!\left\{\exists t\in\mathcal I:\ f_I=1\ \text{and}\ B_t>\bar B^I_t\right\}.
\]

\(\mathcal I\) and \(\bar B^I_t\) are supplied by the KI schedule and KI barrier configuration. KI may be checked discretely or continuously. [1] The strict inequality is material: the supplied specification uses \(B_t>\) KI barrier, whereas each KO condition uses \(B_t\leq\) its barrier. [1]

**Implementation recommendation.** Maintain three explicit lifecycle variables: `ko_state ∈ {none, local, global}`, `ki_seen ∈ {false, true}`, and `termination_time`. Update `ki_seen` monotonically while the contract remains live. Once a KO is accepted, lock `ko_state`, stop subsequent observations, and suppress the maturity branch. This yields auditable pathwise behaviour without presupposing undocumented reset or re-entry rules.

## 4. Complete payoff branches

### 4.1 KO selection and precedence

**Documented.** A local KO occurs on a periodic observation when \(B_{\ell_j}\leq\bar B^L_j\). A global KO occurs on daily or continuous observation when \(B_t\leq\bar B^G_{p(t)}\). Either event terminates the contract early. If local and global KO both occur on the same day, the event is treated as **global KO**. [1]

A useful explicit precedence rule is:

\[
\tau_{KO}=\min(\tau_L,\tau_G),\qquad
K=\begin{cases}
\mathrm{GKO},&\tau_G\leq\tau_L,\\
\mathrm{LKO},&\tau_L<\tau_G.
\end{cases}
\]

The non-strict comparison in the global case implements the documented same-day global priority. The source does not describe a finer ordering between an intraday global touch and a local close observation beyond that same-day rule.

### 4.2 Rate outcomes

The documented results are payment **rates**. Define the KI maturity rate, using the source’s unqualified BPS argument, as

\[
q_{KI}=\max\!\left(\mathrm{Floor},\ \min\!\left(\mathrm{Cap},\ B^{\mathrm{pay}}-\mathrm{Strike}\right)\right).
\]

\(B^{\mathrm{pay}}\) deliberately denotes the BPS input selected for the KI payoff. The source displays \(\mathrm{BPS}-\mathrm{Strike}\) but does not explicitly state whether this BPS is observed at maturity or at another configured valuation/fixing time. This point must be confirmed in the payoff script or booking setup.

The complete mutually exclusive rate tree is:

\[
R=\begin{cases}
c^G_{p(\tau_G)}+r, & \tau_G\leq\tau_L\ \text{and}\ \tau_G\leq T,\\
c^L_j+r, & \tau_L=\ell_j<\tau_G\ \text{and}\ \tau_L\leq T,\\
q_{KI}, & \tau_{KO}>T\ \text{and}\ I=1,\\
\mathrm{Rebate}, & \tau_{KO}>T\ \text{and}\ I=0.
\end{cases}
\]

The global and local branches each combine their applicable KO coupon with Return Ratio. A KI has no independent payment when a later or simultaneous accepted KO terminates the trade; the maturity KI or rebate branch exists only when no KO has occurred. [1]

```text
Live trade
├─ First accepted KO before/equal maturity?
│  ├─ Global KO (including same-day LKO/GKO) → GblKO Cpn + Return Ratio; terminate
│  └─ Local KO only                             → LocKO Cpn + Return Ratio; terminate
└─ No KO through maturity
   ├─ KI seen on its monitoring set             → max(Floor, min(Cap, BPS − Strike))
   └─ No KI seen                                → Rebate
```

**Implementation recommendation.** Keep \(R\) as a rate in the graph. Although Nominal is a named model input and Return Ratio is described as a notional-return percentage, the source does not state the exact conversion from each displayed payoff rate to a currency cash amount. Do not silently impose \(\mathrm{Cashflow}=N\times R\). Instead, expose a final `rate_to_cashflow` node whose convention is verified against `EqFlexKioV`, including the treatment of percentages, rounding, FX rules, and premium-currency conversion.

### 4.3 Cashflow dates

**Documented.** Local KO generates local observation and effective-date schedules. For global KO, payment can be configured for the active local period’s effective date (**Period End Date**) or for the KO trigger date shifted by configured calendar days (**KO Date**); the latter effective dates are generated in `GLOBALKO*`. Maturity branches are described as maturity payoffs. [1]

**Implementation recommendation.** Represent the date separately from the amount:

\[
D_{\mathrm{GKO}}=
\begin{cases}
e^L_{p(\tau_G)}, & \text{Period End Date mode},\\
\mathrm{Adjust}(\tau_G,\text{configured calendar days}), & \text{KO Date mode}.
\end{cases}
\]

Store \(e^L_j\) for a local KO rather than inferring its settlement usage, because the source calls it an effective-date schedule but does not explicitly state the local-KO payment-date rule. Set the no-KO branch date to \(T\). Any payment-date adjustment beyond the stated global KO-Date shift requires confirmation.

## 5. Economic-leg decomposition

The source describes one flexible exotic option rather than a portfolio of legally separate legs. The following allocation is therefore an **implementation recommendation** for reporting and graph construction, not a claim that Murex books multiple trades.

| Economic component | Pathwise amount or function | Interpretation and handling |
|---|---|---|
| Funding/principal return | \(r\), only in a KO outcome | Return Ratio is described as the early-termination notional return percentage. Model it as a contingent principal-return component, not as a scheduled redemption. No funding accrual, initial principal exchange, or separate maturity principal repayment is documented. |
| KO coupon component | \(c^L_j\) for local KO or \(c^G_{p(\tau_G)}\) for global KO | These are contingent KO coupons. They are mutually exclusive and paid only with the selected KO branch. Global coupons and barriers may vary by period. |
| Embedded option/residual component | \(q_{KI}\) after no KO and KI; otherwise Rebate after no KO and no KI | The capped/floored \(\mathrm{BPS}-\mathrm{Strike}\) function is the explicit residual option-style maturity component. The no-KI Rebate is an alternative terminal component, not an additive coupon. |
| Premium and FX mechanics | Not specified as payoff legs | Premium currency is a material field, but the source does not define a premium cashflow amount or timing. Preserve any premium lifecycle independently of the described payoff tree. |

The result should be aggregated with **branch gating**, not addition of all listed components. For example, a KI maturity residual must have zero weight in every KO path, and both KO coupons must have zero weight on every no-KO path.

## 6. Explicit payoff-graph implementation

The following graph design preserves the documented features while making state transitions and audit outputs explicit.

1. **Input nodes.** Load `N`, `T`, and `ccy` from the main trade; feature flags and initial fixing records from `KIKOSEL*`; local rows and period-level global terms from `LOCALKO*`; global schedule/mode/payment timing from `GLOBALKO*`; and KI schedule/mode, barrier, Cap, Floor, Strike, and Rebate from `KNOCKIN*`.
2. **Market-observation node.** Request the BPS at every scheduled discrete date and, where selected, the intraday monitoring stream. This node must receive BPS from a separate basket-performance component. It must not reconstruct BPS unless its calculation convention has been supplied.
3. **Period-resolution node.** For every global observation, resolve the active `LOCALKO*` period and retrieve that period’s GKO barrier and coupon. Fail validation if a live GKO observation cannot be assigned a period.
4. **Barrier-state node.** Evaluate the enabled LKO, GKO, and KI comparisons. Record the first KO time and type; resolve a same-day LKO/GKO collision as GKO. Persist `ki_seen` through the live portion of the path.
5. **Termination gate.** On KO, select exactly one early-termination rate and a GKO payment date using its configured mode. Prevent later KI or KO events from creating extra cashflows.
6. **Maturity gate.** Only when no KO is recorded, select the KI clipped payoff or Rebate at maturity. Bind the BPS argument used in the clipped payoff only after its contractual observation time is confirmed.
7. **Cashflow and audit nodes.** Convert the selected rate using a script-verified rate-to-cashflow convention. Persist BPS observations, active period, threshold/coupon used, monitoring mode, KI flag, KO type, event time, selected rate, and selected payment date. The documented Model Output fields—KO Prob, KI Prob, and CashFlow—can be populated as diagnostic outputs, but are not themselves independent economic inputs. [1]

**Implementation recommendation.** Use event ordering at the observation-day level, with a deterministic global-over-local tie breaker. For continuous monitoring, retain the observed first-touch timestamp even if settlement is configured to the period end. This distinction supports both cashflow timing and back-office explainability.

## 7. Lifecycle, path dependence, and valuation effects

The contract is **path dependent** in two independent ways. First, each KO barrier is tested over time and a single accepted KO ends the contract, making later observations economically irrelevant. Second, the KI state is based on whether the BPS has ever exceeded its barrier over its monitoring set; the terminal branch cannot be chosen from the maturity BPS alone. [1]

Initial fixing prices are entered in `KIKOSEL*`, which is a material difference from the referenced KikoPlus framework. [1] The supplied document does not state how those prices are used in the BPS calculation or how amended, corrected, or missing historical fixings affect recorded KO/KI status. A lifecycle implementation should therefore retain initial and historical observations with source/status metadata and re-evaluate only according to confirmed Murex correction policy.

**Documented.** Monte Carlo valuation is enabled through GMP type `EQ_MONTECARLO` and group `EQ_KIKOREVS`. The production example uses 30,000 paths and Cashflows set to 1. [1] These are configuration facts, not a statement that 30,000 paths is suitable for every valuation or risk purpose.

## 8. Documented constraints and unresolved points

### 8.1 Operational constraints

**Documented.** Only nominal-based principal definitions are supported; quantity principal is not. Tenors beyond two years (24 months) fail validation. Basket currency must equal Premium Currency. [1]

For FX rules, the default/no-FX-rule configuration is supported for both baskets and single underlyings. The basic \((S-K)\times X\) and fixed-quanto \((S\times1-K)\) rules are supported only for a single underlying. The composite \((S\times X-K)\) rule is unsupported for both baskets and single underlyings. [1]

### 8.2 Ambiguities requiring confirmation

| Topic | What is documented | Required confirmation before production implementation |
|---|---|---|
| BPS construction | BPS is the best performer and drives all barriers. | Underlying normalization, aggregation, currency treatment, use of initial fixings, corporate-action treatment, and whether BPS is a price or performance measure. |
| KI maturity BPS | The formula is \(\max(\mathrm{Floor},\min(\mathrm{Cap},\mathrm{BPS}-\mathrm{Strike}))\). | The observation/fixing time for this BPS and the units/scaling of BPS, Strike, Cap, and Floor. |
| Currency cash amount | Nominal and Premium Ccy are material fields; displayed KO and maturity formulas are rates. | The rate-to-cashflow multiplier, percentage conventions, rounding, and FX conversion. |
| KO chronology | Same-day LKO/GKO is global; either KO terminates early. | Ordering if a continuous intraday GKO and a local close occur on the same calendar day but at different timestamps; treatment at maturity boundaries. |
| Schedule boundaries | Blocks generate local/global/KI schedules and use calendars. | Inclusion of start/end dates, holiday adjustment conventions, period-assignment boundary rule, and observation of suspended markets. |
| Local KO payment date | Local observations and effective dates are generated. | Whether the associated effective date is always the local KO payment date and any lag/adjustment rule. |
| Feature disablement | Disabled KO fields can be hidden, while schedule rows may still be generated. | Whether all validation, risk, and back-office routines consistently gate off disabled features. |
| FX/currency wording | The source states both Basket Ccy = Premium Ccy and that a basket can fulfil a quanto payoff when basket currency differs from constituent currencies. | Definitions of basket currency versus constituent currency, and the permitted payout conversion mechanics. |

## References

[1]: ../Reverse_KIKO.md "EQ Reverse Kiko (KioV) source specification"
