# Murex Architecture Deep Dive: Flex, Generators, and Configuration Groups

This page explains — with a concrete worked example and an illustrative C++ code skeleton — how the core Murex concepts for structured equity development fit together:

- **Flex Headers** and **Flex Blocks**
- **Payoff Scripts** (the "nomen")
- **Model Groups** and **GMP** (Generic Market Parameters)
- **Generators** (pricing engines)
- **Sensitivity Configuration Groups**

If you are coming to Murex from another trading system, these five terms are responsible for most of the initial confusion. The good news: they form a very small set of *couplings*, and once you see the couplings, the whole architecture clicks.

---

## 1. The Big Picture: Four Layers, Three Couplings

Murex cleanly separates **what the trader sees**, **what links the product to a pricer**, **how it is valued**, and **how risk is computed**:

```
LAYER 1: BOOKING / UI ───► Flex Header + Flex Blocks   (what the trader sees & enters)
                                 │
                                 │  payoff script ("nomen") binds them together
LAYER 2: WIRING ─────────────►  Payoff Script ──► Flex Header (the UI)
                                 │              └► Model Group (pricing config)
                                 │
                                 │  GMP maps model group → generator + parameters
LAYER 3: MODEL ─────────────►  Generator (e.g. EQ_MONTECARLO Monte Carlo engine)
                                 │   consumes market data (vol, curves, divs, FX, corr)
                                 ▼   emits premium + model outputs (cashflows, KO probs)

LAYER 4: RISK ──────────────►  Sensitivity Configuration Group (MAIN / VAR / EQDELTA …)
                                 │   decides WHICH greeks get computed for this task
                                 ▼
                    simulation servers → trading matrices / LiveBook / batch reports
```

### The three relationships people mix up

| Concept | Question it answers | What it actually is |
| :--- | :--- | :--- |
| **Flex header / block** | *"What does the booking screen look like?"* | Database-stored UI definitions. Header = container, blocks = groups of fields/tables/grids. The same header can host many payoffs. |
| **Payoff script** | *"What product did the user pick?"* | The **glue**. Selecting it loads the flex header (UI) AND attaches the model group (pricing). |
| **Model group + GMP** | *"Which pricing engine, with what settings?"* | Model group = a named pricing configuration. GMP = the table that maps a group → **generator** (engine type) + its parameters (paths, seed, ...). |
| **Generator** | *"What does the math?"* | The pricing engine (Monte Carlo, PDE, analytical). Confusingly, Murex also calls data-builders "generators" (curve/surface bootstrappers) — the two are different animals. |
| **Sensitivity config group** | *"Which greeks does THIS risk job need?"* | Run-time selection: computes everything (`MAIN`), only delta (`EQDELTA`), only vega (`EQVEGA`), or nothing but NPV (`VAR`). Orthogonal to the model layer. |

**The single most important sentence on this page:** the *generator* (engine) is shared infrastructure; the *flex block ↔ C++ struct ↔ model group* coupling is where the real per-product "development" happens.

---

## 2. Concept-by-Concept Reference

### 2.1 Flex Headers & Flex Blocks

- **Flex Header** — a container/template corresponding to a product type (e.g., `EqFlexRakiP`, `EqFlexDBrW`). Renders the product's booking screen.
- **Flex Block** — a UI component grouping related economic parameters. A block can contain:
  - Input fields (numeric, string, date, checkbox, dropdown)
  - Tables/grids (underlying constituents, period-by-period parameters)
  - Dynamic visibility rules (show/hide/disable fields based on other values)
  - Read-only model-output columns (`Cashflow`, `PayRate`, `KO Prob`)

Flex definitions are stored in the Murex configuration database and rendered by the flex engine at runtime. Traders' entered values are stored as trade attributes.

### 2.2 Payoff Script (Nomen)

A naming/payoff identifier the trader selects when booking (e.g., `EqFlexDblNT`, `EqFlexAccu`). Selection triggers two things simultaneously:

1. Load the associated **Flex Header** (the booking UI).
2. Bind the trade to a **Model Group** (the pricing config).

### 2.3 Model Group & GMP

- **Model group** — a named pricing configuration tag (e.g., `EQ_DIGOPT`, `EQ_KIKOREVS`, `EQ_DBARW`). Many products may share one group; one product uses exactly one group.
- **GMP (Generic Market Parameters)** — the configuration table that maps each model group to a **generator** and its parameters. Editing GMP (e.g., paths 10,000 → 30,000) is a *data* change, not a rebuild.

### 2.4 Generator

The **pricing generator** is the engine that produces the value equation. For this playbook it is the Monte Carlo generator (`EQ_MONTECARLO`). Its GMP parameters include:

- Number of paths (e.g., 30,000 production / 10,000 for digital)
- Random seed & variance-reduction settings
- Regression order (for early/exercise features)
- Cash-flow aggregation flag (0 or 1)

**Do not confuse** the *pricing* generator with Murex *market-data* generators (the engines that bootstrap/invert yield curves or build local-vol surfaces). The former values trades; the latter build the market data the former consumes. Both are configured, but they plug in at different layers.

### 2.5 Sensitivity Configuration Group

A runtime-role concept used by the risk/simulation servers. It determines **which sensitivities get computed for a given task** (bump-and-revalue runs). It is *not* part of the pricing wiring:

| Group | Computes | Used for |
| :--- | :--- | :--- |
| `MAIN` / `SPB` | all primary greeks (Delta, Gamma, Vega, Theta, Rho, FxVega, Sticky Strike) | full trading matrices |
| `VAR` / `SPBNOSENSI` | NPV only (all greeks off) | pure P&L, fastest |
| `EQDELTA` | EQ delta only | `eq_delta` batch report |
| `EQVEGA` | EQ vega only | `eq_vega` batch report |
| `IRDELTA` | Rho / IR delta only | `IRPV01` batch report |

Apply per simulation (Securities menu) or per report (reporting setup). See Risk_Management.md for the details and greek formulas.

---

## 3. Worked Example: The Equity Digital Option

We use the product already documented in the playbook: [Digital Option](../Products/Other_Exotics/Digital_Option.md). It is the simplest product, but **every concept generalizes** to Reverse KIKO, RakiPlus, DBrW, Double No-Touch RA, etc.

Product facts (from the playbook):
- Family `EQD`, Group `OPT`, Type `FLEX`
- Flex Header `EqFlexDOpt`, single flex block `DIGITAL`
- Payoff script `EqFlexDOpt` watching the `DIGITAL` block setting at the strike
- Model group `EQ_DIGOPT`; GMP: `EQ_MONTECARLO`, paths 10,000, regression order 1, cashflows 0
- Settlement: `Nominal + Cash` or `Quantity + Delivery`

### Step 1 — Flex UI (configuration, no code)

Booking screen `EqFlexDOpt`:

```
Flex Header: EqFlexDOpt
└── Flex Block: DIGITAL
      ├── field: at_strike_behavior   (dropdown: pay / no_pay)
      └── (standard ticket fields: strike, call/put, maturity, nominal, cash/delivery …)
```

This only tells Murex: *"when a deal of this payoff is booked, render this screen."* Trader-entered values are stored with the trade.

### Step 2 — C++ Mapping (the contract)

The values entered into flex blocks must reach the C++ pricing code. A mapping layer reads trade attributes into C++ structs:

```cpp
// content/equity/src/MxMapping.h   (ILLUSTRATIVE — Murex APIs are proprietary)
// One struct per flex block you add to the product.

struct FlexDigitalBlock {          // mirrors the DIGITAL flex block
  MString at_strike_behavior;      // MUST equal the flex field name, case-sensitive
};

struct EqDigoptArgs {              // the "Arguments" struct the pricer consumes
  FlexDigitalBlock flex;
  MDate   maturity;
  double  strike;
  bool    is_call;
  double  nominal;
  bool    cash_settle;             // Nominal+Cash  /  Quantity+Delivery
};
```

**The classic bug:** flex field named `At_Strike_Behavior` but the struct reads `at_strike_behavior` → the value silently arrives empty. Field-name matching is the most common source of Flex bugs; it is why the playbook mandates mapping unit tests.

### Step 3 — Model Group & GMP → Generator (wiring)

Configuration (from the playbook's Digital Option page):

| Config item | Value |
| :--- | :--- |
| Model group | `EQ_DIGOPT` |
| GMP for that group | generator `EQ_MONTECARLO`, paths 10,000, regression order 1, cashflows 0 |

Conceptually: *"any trade using model group `EQ_DIGOPT` is priced by the Monte Carlo generator with 10,000 paths."* Selecting the payoff script `EqFlexDOpt` on the ticket wires the booking screen (Step 1) and the model group (Step 3) together.

### Step 4 — The Generator & Payoff Code (illustrative skeleton)

The MC generator is **shared infrastructure**. It simulates spot paths under the chosen diffusion (GBM / local vol calibrated from the implied vol surface), then calls a product-specific payoff evaluation, then aggregates (mean of discounted payoffs) and reports the premium.

```cpp
// content/equity/src/eq_digopt.cpp   (ILLUSTRATIVE skeleton)
namespace mceq {

// ---------------------------------------------------------------------------
// 1) Diffusion — SHARED across all MC products (Raki, KioV, DblNT, DBrW, ...).
//    Parameters (paths, seed, timesteps) come from GMP.
// ---------------------------------------------------------------------------
class MCEngine {
public:
  void GeneratePaths(PathMatrix& paths,
                     const EqDigoptArgs& args,
                     const VolSurface& vol,        // implied/local vol
                     const YieldCurve& disc,       // discount curve
                     const DividendCurve& divs);   // dividends
};

// ---------------------------------------------------------------------------
// 2) Payoff — THIS is the product-specific part a developer writes.
//    Digital is path-INDEPENDENT (terminal observation), so Evaluate() takes
//    a single terminal spot; a path-DEPENDENT product loops over the path.
// ---------------------------------------------------------------------------
class DigitalPayoff {
public:
  double Evaluate(double sT, const EqDigoptArgs& args) const {
    const bool inMoney = args.is_call ? (sT > args.strike)
                                      : (sT < args.strike);
    if (!inMoney) return 0.0;

    // edge case: fixing EXACTLY at strike → governed by the flex field
    if (args.flex.at_strike_behavior == "no_pay" && sT == args.strike)
      return 0.0;

    return args.nominal;             // "all-or-nothing" cash payout
  }
};

// ---------------------------------------------------------------------------
// 3) Aggregation — mean of discounted payoffs = premium.
//    Greeks are NOT computed here; the simulation server bump-and-revalues.
// ---------------------------------------------------------------------------
void Price(EqDigoptResult& out, const EqDigoptArgs& args,
           const PathMatrix& paths, const YieldCurve& disc) {
  double sum = 0.0;
  for (const auto& path : paths)
    sum += DigitalPayoff{}.Evaluate(path.TerminalSpot(), args);
  out.premium = disc.PV(sum / paths.size());
  out.model_ok = true;
}

} // namespace mceq
```

**Key insight:** the generator is shared; extending a product means (a) adding your struct, (b) writing `Payoff::Evaluate`, (c) wiring the model group. You almost never write a fresh engine.

### Step 5 — Greeks via Sensitivity Configuration Groups (runtime, not code)

The pricer returns **premium only**. Delta/vega/rho come from **bump-and-revalue**: shift spot +1%, reprice premium; shift spot −1%, reprice; central difference. That is orchestrated by the **simulation server**, and the *sensitivity config group* selects *which bumps* a task runs:

- `MAIN` → full greek set for trading matrices.
- `VAR` → NPV only, fastest, for P&L-only jobs.
- `EQDELTA` → delta only for the delta batch report — skips the 30+ other sensitivity bumps.

So the **generator** is *the engine*, and the **sensitivity config group** is *which sensitivities that engine gets re-run with* for a given job. Two different axes.

---

## 4. Extending to Path-Dependent Products (Reverse KIKO)

For a path-dependent payoff (e.g., [Reverse KIKO](../Products/KIKO/Reverse_KIKO.md)), nothing about the layers changes — only `Evaluate` becomes a per-path *loop*:

```cpp
// content/equity/src/eq_kio_v.cpp   (ILLUSTRATIVE — payoff loop for Reverse KIKO)
class ReverseKikoPayoff {
public:
  // CRITICAL inputs come from the flex blocks:
  //   KIKOSEL*.ReturnRatio, LOCALKO*.LocBarPrice/LocKO Cpn,
  //   GLOBALKO*.GblBarPrice, KNOCKIN*.barrier/cap/floor/strike/rebate …
  double Evaluate(const Path& path,
                  const EqKioVArgs& args) const {
    bool lko = false, gko = false, ki = false;

    for (const auto& fixing : path.Observations()) {   // monitoring dates
      const double bps = BestPerformer(fixing);        // Best Performer (BPS)

      // local KO on discrete dates, global KO each observation day
      if (pcmp(bps, args.local_ko_barrier, args.loc_bar_compare)) lko = true;
      if (pcmp(bps, args.global_ko_barrier, args.gbl_bar_compare)) gko = true;
      if (bps > args.ki_barrier) ki = true;
    }

    if (gko) return args.return_ratio + args.gbl_ko_cpn;      // precedence: GKO wins
    if (lko) return args.return_ratio + args.loc_ko_cpn;

    // no KO: payout depends on KI at maturity
    const double bpsT = BestPerformer(path.TerminalSpot());
    if (!ki) return args.rebate;
    return clamp(args.bps - args.strike, args.floor, args.cap);  // KI branch
  }

private:
  double BestPerformer(const Fixing& f) const { /* max of underlyings */ }
  double clamp(double v, double lo, double hi) const { return std::min(std::max(v, lo), hi); }
  bool   pcmp(double v, double barrier, MString op) const {
    return (op == ">=") ? (v >= barrier) : (v > barrier);
  }
};
```

Same skeleton as the digital: shared MC engine → product-specific `Evaluate` → GMP-driven settings (paths 30,000) → simulation config groups drive the greeks.

---

## 5. The Three Covenants (recap)

Every Murex structured-product development effort reduces to keeping three contracts intact:

1. **UI ↔ C++:** flex field name == struct member (case-sensitive).  
   Broken → trader's inputs never reach the model.
2. **Product ↔ Pricing:** payoff script ↔ model group ↔ GMP → generator (engine + parameters).  
   Broken → right product, wrong engine or wrong paths/seed.
3. **Risk ↔ Runtime:** simulation or report ↔ sensitivity config group.  
   Wrong → wasted compute (too many greeks) or missing risk factors (delta-gap, correlation, FX vega for quanto/basket).

---

## 6. Cross-References

- [Flex Development Guide](./Flex_Development.md) — the build workflow this deep dive supports.
- [Systematic Product Development Guide](./Product_Development_Guide.md) — program-level phases, roles, gates.
- [Common Product Features](./Common_Features.md) — the product vocabulary (barriers, accrual, FX rules, …).
- [Risk Management & Greeks](./Risk_Management.md) — greek formulas, sensitivity groups, validation.
- [Digital Option](../Products/Other_Exotics/Digital_Option.md) — the worked example's product page.
- [Reverse KIKO](../Products/KIKO/Reverse_KIKO.md) — the path-dependent extension.
- [Murex Structured Product Booking Overview](./Murex_Overview.md) — trade representation and the booking/risk data flow.