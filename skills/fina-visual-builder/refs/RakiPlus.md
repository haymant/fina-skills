# RakiPlus / MemRakiPlus (v2) — `EqFlexRakiP` / `EqFlexMemRP`

RakiPlus keeps the RAKI pricing foundations but changes the **booking construction**: a market-level **dummy basket** placeholder replaces the per-combination basket object, and the trade's real constituents and reference prices move **into `KIKOSelect`**. `KIKOSelect` therefore becomes the per-trade **constructor** that instantiates the DAG (binds leaves, toggles subgraphs, selects settlement, adds rounding/FX fields, seeds memory locks). See the [history section](../SKILL.md#history-raki--rakiplus--visual-blocks) for the comparison table.

## Target DAG with KIKOSelect

```mermaid
flowchart LR
  subgraph PLACE["Market-level placeholder"]
    DUMMY[("Dummy Basket<br/>e.g. HKEX EQ<br/>no constituents · Quanto")]
  end

  subgraph TRADE["Trade — EqFlexRakiP / EqFlexMemRP"]
    KIKO{{"KIKOSelect v2 — CONSTRUCTOR<br/>binds underlying + referencePrice<br/>localKO · globalKO · knockIn · memory<br/>returnRatio · Denomination · ITMPayment<br/>FXPair · FXFixSource · LKO/GKO Locked"}}
    RGACC["RGACCDATE"]
    RGACCLKO["RGACCLKO / RGACCLKO+"]
    GLOB["GLOBALKO*"]
    KIN["KNOCKIN*"]
  end

  subgraph DAG["Compiled payoff DAG — self-contained per trade"]
    FS["fixing_schedule"]
    WOP["worst_of_performance"]
    LKO["local_ko_gate"]
    GKO["global_ko_gate"]
    KI["knock_in_gate"]
    RA["range_accrual"]
    CS["coupon_strip"]
    MC["memory_carry"]
    ROUND["cashflow rounding<br/>Round(D*P,2)*Q/D"]
    TERM["terminal residual<br/>KI1 / KI2 / NoKI"]
    NR["notional_return"]
    CASH["cash_settlement"]
    PHYS["physical_delivery_settlement"]
    DISC["payment_discount"]
    AGG["aggregate_legs"]
  end

  DUMMY -.->|"market context only"| WOP
  KIKO ==>|"binds underlying + referencePrice"| WOP
  KIKO -->|"toggles LKO"| LKO
  KIKO -->|"toggles GKO"| GKO
  KIKO -->|"toggles KI"| KI
  KIKO -->|"returnRatio"| NR
  KIKO -->|"ITMPayment cash/delivery"| CASH
  KIKO -->|"ITMPayment cash/delivery"| PHYS
  KIKO -->|"Denomination"| ROUND
  KIKO -->|"FX fixing"| DISC
  KIKO -.->|"LKO/GKO Locked seed"| MC
  RGACC --> FS
  RGACCLKO --> RA
  RGACCLKO --> CS
  GLOB --> GKO
  KIN --> KI
  KIN --> TERM
  FS --> WOP
  WOP --> LKO
  WOP --> GKO
  WOP --> KI
  WOP --> RA
  WOP --> TERM
  LKO -->|"terminates period"| CS
  GKO -->|"terminates"| CS
  RA --> CS
  CS --> MC
  MC -->|"carry"| CS
  KI -->|"activates"| TERM
  GKO -->|"KO redemption"| NR
  TERM --> CASH
  TERM -->|"ITM delivery"| PHYS
  CS --> ROUND
  ROUND --> DISC
  NR --> DISC
  CASH --> DISC
  PHYS --> DISC
  DISC --> AGG
```

## What to notice

- The **thick arrow** now runs `KIKOSelect ==> worst_of_performance`: the trade constructor supplies the basket leaves, so the DAG is self-contained and no external per-combination basket is required.
- The dummy basket is a **dashed, cheap placeholder** (market context only) instead of a thick external dependency.
- `KIKOSelect v2` gained an **`ITMPayment` settlement selector** (choosing `cash_settlement` vs `physical_delivery_settlement`), a **`Denomination` rounding node**, **FX-fixing** input, and an **`LKO/GKO Locked` seed** into `memory_carry`.
- `memory_carry` and the rounding node are present because RakiPlus covers the MemRakiPlus variant; both are absent in [Raki](Raki.md).

Diff this diagram against [Raki](Raki.md): the core payoff nodes are identical, the change is entirely in **who constructs the graph**.
