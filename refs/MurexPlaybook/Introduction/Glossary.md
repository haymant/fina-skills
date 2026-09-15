# Glossary of Murex & Financial Terminology

A quick-reference glossary of the terms used across this Playbook — the Murex platform terms first, then the financial / structured-products terms. Terms marked *(Murex)* are platform-specific; the rest are standard industry terminology you will meet in term sheets and trading desks.

## A. Murex Platform Terminology

| Term | Meaning |
| :--- | :--- |
| **MX.3** | Murex's platform: a single-database front-to-back trading and risk system for capital markets. |
| **Family / Group / Type** | The 3-level instrument classification used to book a trade (e.g., `EQD` / `OPT` / `FLEX`). Determines the booking screen and behavior. |
| **FLEX** | A trade *Type* that displays a customizable, flex-driven booking screen instead of a fixed product screen. Used for exotic structured products. |
| **Flex Header** *(Murex)* | Container/UI template for a product type (e.g., `EqFlexRakiP`). Groups the flex blocks shown on the booking screen. |
| **Flex Block** *(Murex)* | A UI component grouping related economic parameters (fields, grids, dynamic display, model-output columns). |
| **Payoff script / Nomen** *(Murex)* | The identifier the trader selects at booking. It binds the **flex header** (UI) to the **model group** (pricing). |
| **Model group** *(Murex)* | A named pricing configuration (e.g., `EQ_DIGOPT`, `EQ_KIKOREVS`) that a payoff script points to. |
| **GMP (Generic Market Parameters)** *(Murex)* | Configuration binding a model group to a **generator** and its settings (paths, seed, regression order, cashflow flag). |
| **Generator** *(Murex)* | The pricing engine (e.g., Monte Carlo `EQ_MONTECARLO`, PDE, analytical). Also used for *market-data generators* that build curves/surfaces — different concept, same word. |
| **Sensitivity configuration group** *(Murex)* | Run-time selection of which greeks a simulation/report computes (`MAIN`, `VAR`, `EQDELTA`, `EQVEGA`, `IRDELTA`). |
| **Simulation / Simulation server** *(Murex)* | The environment that re-values portfolios (with bump-and-revalue for greeks, scenarios, etc.) to produce risk results. |
| **LiveBook / RTPM** *(Murex)* | Real-time portfolio risk/pricing views (positions, greeks, P&L) with live market data and what-if scenarios. |
| **Trading matrix** *(Murex)* | A risk report showing a greek bucketed by strikes/tenors (e.g., EQ delta ladder). |
| **Batch report** *(Murex)* | Scheduled, automated execution of reports (e.g., risk matrices) run from the reporting menu. |
| **Market operation (MKT OP)** *(Murex)* | A lifecycle action applied to a deal: Expiry (`EXP`), Exercise (`EXR`), Knock, Early Termination/Unwind (`XIT`), Restructure, C&R. |
| **Fixing** *(Murex)* | Recording an observed value (price, rate) for a deal on a fixing date; executed via the fixing/archiving tool. |
| **Fixing index / Min-Max fixing** *(Murex)* | For continuous monitoring, the intraday **max** price (up-barriers) or **min** price (down-barriers) is recorded on a fixing index. |
| **Schedule generator** *(Murex)* | A configurable function `F(Start, End, ScheduleGen, Calendar)` producing date series (fixing, period, payment dates). |
| **Shifter** *(Murex)* | A number of calendar/business days applied to shift an anchor date (e.g., payment date = period end + shifter). |
| **Calendar** *(Murex)* | The holiday/business-day set used by date logic (e.g., `NYSE`, `HKEX EQ`). |
| **Market data item (MD Item)** *(Murex)* | A named piece of market data consumed by models: spot, implied/local vol surface, dividend curve, yield curve, FX rate, correlation matrix. |
| **Local vol (LV)** *(Murex)* | A vol surface calibrated (Dupire) to match market prices; the diffusion basis for the equity MC generator. |
| **Datamart** *(Murex)* | The extraction layer that exports trades, P&L, cash flows, and sensitivities to downstream systems. |
| **MSL (Murex Scripting Language)** *(Murex)* | The scripting language for pre-trade rules, validation, routing, and workflow logic. |
| **MXtest / MxCI** *(Murex)* | Murex's functional-test framework and continuous-integration toolchain. |
| **MxML Exchange** *(Murex)* | Murex's XML-based import/export/interface mechanism for trades and configuration. |
| **Instrument / Contract** | The reference asset/contract a trade references (e.g., `FLEX_USD` dummy basket, an equity ticker). |
| **Dummy basket** | A market-oriented basket instrument carrying no constituents; real underlyings live in the trade's flex blocks. |
| **eTradepad** *(Murex)* | Murex's desktop trading workspace used for booking and pricing. |
| **Combined Trade / Booking sequence** *(Murex)* | Multiple trades as a single deal unit (e.g., option + its hedge), booked in one sequence. |

## B. Financial & Structured-Products Terminology

### Market & option basics

| Term | Meaning |
| :--- | :--- |
| **Underlying** | The asset the option references (single equity or basket of equities). |
| **Spot / Initial price** | Current market price / reference price at trade inception. |
| **Strike** | The agreed level at which the option is exercised / payoff is calculated. |
| **Notional / Nominal** | The principal amount on which percentage payoffs are scaled. "Nominal" principal is the supported mode for these products. |
| **Quantity principal** | Principal expressed as a number of shares instead of a cash amount (largely unsupported here). |
| **Call / Put** | Right to buy (call) or sell (put) the underlying; in structured notes "call" often = upside participation. |
| **Buy / Sell, Long / Short** | Trade direction from the desk's perspective. |
| **Vanilla option** | Standard call/put with no exotic features; the reference case for model validation. |
| **Exotic option** | An option with path-dependent or conditional features (barriers, accruals, etc.). |
| **Premium** | The price of the option (what the buyer pays). |
| **NPV / PV** | Net present value / present value of future cash flows. |

### Exotic features

| Term | Meaning |
| :--- | :--- |
| **Barrier** | A price level whose breach activates (knock-in) or terminates (knock-out) the option. |
| **Knock-In (KI)** | The option comes into existence only when the barrier is hit. |
| **Knock-Out (KO)** | The option terminates when the barrier is hit. |
| **Up-and-Out / Down-and-Out** | KO when price rises to the (upper) barrier / falls to the (lower) barrier. |
| **Up-and-In / Down-and-In** | KI when price rises to / falls to the barrier. |
| **Double barrier** | Both an upper and a lower barrier (double-out / double-in). |
| **Observation style** | How the barrier is monitored: discrete (daily close), periodic (period ends), or continuous (intraday). |
| **Rebate** | A fixed cash amount paid on a KO event; timing = Pay at Knock or On Maturity. |
| **Return ratio** | Percentage of notional returned to the investor on early termination. |
| **KO coupon / Bonus** | Extra fixed coupon paid on a KO event (`PayRate[KO] = accrued + KO Cpn + ReturnRatio`). |
| **Range accrual** | Coupon = accrual rate × (N1/N2) where N1 = days inside the range, N2 = total observation days. |
| **N1 / N2** | In-range days / total observation days for the accrual factor. |
| **Worst-of (WPS) / Best-of (BPS)** | Performances of the worst / best performing underlying in the basket. |
| **K-th best performer** | Performance of the asset ranked K (1 = best … N = worst). |
| **Average performance (AVG)** | Simple average of all constituents' performance. |
| **Memory coupon** | Unpaid coupons from missed periods are recovered later when conditions are met. |
| **Memory KO** | KO requires each underlying to have breached its barrier at least once ("locked" per name). |
| **Coupon barrier** | A level that gates whether the (memory) coupon pays in a period. |
| **Cliquet / Ratchet** | Locks in periodic gains with floor protection; no-KI Raki maturity payoff is cliquet-style. |
| **Digital (binary)** | All-or-nothing payoff: fixed amount if condition met at expiry, else zero. |
| **Averaging (Asian)** | Payoff based on averaged prices over a window rather than a single fix. |
| **Participation rate (PR / Share ratio)** | Scales the payoff (`PR × (Perf − Strike)`). |
| **Cap / Floor** | Maximum / minimum payout rate, per period or at maturity. |
| **Step-up / Step-down** | Period-varying barrier levels or coupons over the deal's life. |
| **Autocall** | An early-redemption feature where the note calls back when the underlying is above a level (common industry term; used at maturity structures here). |
| **TARN** | Target Accrual Redemption Note: the note redeems early once a cumulative coupon target is reached. |

### FX, settlement, and events

| Term | Meaning |
| :--- | :--- |
| **FX rule (Basic / Quanto / Composite)** | How the payoff converts currencies: Basic `(S−K)×X`, Quanto `(S×1−K)` (fixed FX), Composite `(S×X−K)` (mostly unsupported). |
| **Quanto** | Option on a foreign underlying settled in the premium currency at a fixed FX rate; removes FX risk for the holder. |
| **Premium currency / Basket currency** | Currency of the payoff/settlement / currency of the basket constituents. |
| **Cash settlement** | Payment of the payoff amount in cash. |
| **Delivery / Physical settlement** | Delivery of shares against payment. |
| **ITM Payment** | Field specifying cash vs delivery settlement when the deal is in the money at expiry. |
| **Fixing date / Observation date** | Date on which an underlying value is recorded for the payoff. |
| **Payment date / Effective date** | When a cash flow pays / when a period starts accruing. |
| **Business day / Modified following** | Standard convention moving a date to the next business day (with month-skip rule for modified following). |
| **Expiry** | The trade reaches maturity and final cash flows settle. |
| **Exercise** | Acting on the option right at maturity to settle the payoff. |
| **Unwind / Early termination (XIT)** | Closing a deal early at its market value. |

### Risk terminology

| Term | Meaning |
| :--- | :--- |
| **Greeks / Sensitivities** | Option risk measures: Delta, Gamma, Vega, Theta, Rho, plus exotics-specific (correlation, dividend, FX vega). |
| **Delta** | Change in premium per 1% spot move. |
| **Gamma** | Change in delta per spot move (second derivative of premium). |
| **Vega** | Change in premium per 1 vol point. |
| **Theta** | Change in premium as time passes one day. |
| **Rho / IR PV01 / DV01** | Change in premium per 10bps rate move / per 1bp (PV01). |
| **Delta gap** | The jump in delta as spot crosses a barrier — key for barrier hedging. |
| **Correlation** | Dependence between asset returns; material for basket/worst-of/quanto pricing. |
| **Bump-and-revalue** | Computing greeks by shifting market data and re-pricing (finite difference). |
| **VaR / ETL** | Value-at-Risk / Expected Tail Loss: statistical loss measures on the portfolio. |
| **P&L explain** | Daily P&L decomposed by risk factor to validate the greeks model. |