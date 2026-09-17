# Double No-Touch Range Accrual: Payoff Chapter

## Purpose and classification

The **EQ Double No-Touch RA** is a note-form equity range accrual with two knock-out boundaries. The trade pays periodic range-accrual coupons while alive and terminates if the selected upper or lower KO indicator breaches its corresponding barrier. Knock-in is disabled for this product. [1]

The documented Murex representation is `EQD` / `OPT` / `FLEX`, using Flex Header `EqFlexDblNT` inside the `KikoSwap` template. The source does not provide a literal script name; `EqFlexDblNT` should therefore be treated as the header identifier until runtime configuration confirms the payoff-script reference. [1]

## State and observation rules

For period \(i\), let \(N_{1,i}\) be the number of qualifying range days and \(N_{2,i}\) the total observation days. The selected accrual indicator may be WPS, All, BPS, or Any. The upper and lower KO indicators may independently be WPS or BPS.

The range test is parameterized by six comparison controls. It must not hard-code inclusive endpoints:

\[
AccruFactor_i = N_{1,i}/N_{2,i}.
\]

Local KO is checked periodically. Global KO is daily discrete or continuous. A continuous global observation uses the relevant intraday fixing convention; the source names Min-Max fixing behavior for barrier monitoring. [1]

## Payoff branches

The normal period rate is:

\[
P_i = AccruRate_i\frac{N_{1,i}}{N_{2,i}}+FixCoupon_i.
\]

At local KO:

\[
P_{LKO}=P_i+LocKOCpn+ReturnRatio.
\]

At global KO:

\[
P_{GKO}=P_i+GblKOCpn+ReturnRatio.
\]

For a mid-period global KO, accrual is calculated only through the trigger date. If local and global KO occur on the same date, global KO has precedence. If no KO occurs, maturity pays the final range-accrual amount plus return of principal/notional. There is no KI residual option branch. [1]

The denomination rule for periodic flows is:

\[
CashFlow_i=Round(Denomination\times P_i,2)\times\frac{Notional}{Denomination}.
\]

The source describes separate return-notional and rebate/coupon flows at knock. Preserve those as distinct graph nodes even where the UI presents a combined rate.

## Economic decomposition

| Component | Interpretation |
|---|---|
| Funding / principal | Return of notional at maturity or KO, controlled by `ReturnRatio` and settlement timing. |
| Coupon | Range-accrual coupon, fixed coupon, and KO coupon; mid-period GKO uses pro-rated accrued coupon. |
| Embedded optionality | Double no-touch survival value: the coupon and principal are contingent on avoiding both upper and lower barriers. |

There is no terminal KI option. `KNOCKIN*` is present in the UI template but unused, and `IRLEGP` is ignored because only note form is supported. [1]

## Flex-block mapping

| Block | Payoff role |
|---|---|
| `KIKOSTRUCT` | Underlyings, reference prices, feature flags, denomination, ITM settlement, FX fields. |
| `FIXINGDATE` | Daily range-accrual fixing schedule and historical-fixing status. |
| `RGACCPERIO` | Periods, range bounds, comparison operators, local/global barriers, indicator choices, coupons, and N1/N2. |
| `DAILYKO` | Global KO schedule, discrete/continuous mode, and period-end versus KO-date payment. |
| `KNOCKIN*` | Inactive for this payoff. |

## Payoff graph and lifecycle

```text
terms → schedule expansion → range indicator observations → N1/N2
      → upper/lower local and global barrier tests
      → alive/knocked state
      → periodic coupon OR prorated KO settlement OR maturity return
      → denomination / FX / settlement nodes
```

The `Knock` operation records the upper or lower barrier and emits return-notional and rebate/coupon flows. `Expiry` emits the final period accrual and principal return when no KO has occurred. Preserve all comparison operators, trigger dates, and payment-date mode in evidence.

## Constraints and unresolved semantics

The source limits the basket to six names, tenor to 25 months, excludes quantity principal and Composite FX, and supports Basic or Quanto FX. The source does not settle whether all/best/any indicator aggregation is same-date, how missing fixings are treated, or the exact conversion from displayed rate to currency amount. Those decisions require configuration or parity evidence. [1]

## References

[1]: ../Double_No_Touch_RA.md "Murex Playbook — EQ Double No-Touch Range Accrual"
