# RAKI (v1) — `EqFlexRaki`

RAKI is the base equity range-accrual note (model group `EQ_RAKI`). The payoff blocks below are the same vocabulary used by the visual builder; the important structural fact of v1 is that the **worst-of basket is a pre-defined market object that lives outside the trade**, while `KIKOSelect` is thin — it only activates features and carries `returnRatio` / initial fixings. This is the source of the combinatorial basket maintenance described in the [history section](../SKILL.md#history-raki--rakiplus--visual-blocks).

## Target DAG with KIKOSelect

```mermaid
flowchart LR
  subgraph EXT["Booking objects outside the trade"]
    REG["BasketRegistry<br/>create · version · fix"]
    BASKET[("Pre-defined Basket<br/>one per stock combination<br/>~C(N,k) objects")]
  end

  subgraph TRADE["Trade — EqFlexRaki (model group EQ_RAKI)"]
    KIKO{{"KIKOSelect v1 (thin)<br/>localKO · globalKO · knockIn<br/>returnRatio · initial fixing"}}
    RGACC["RGACCDATE<br/>accrual date schedule"]
    RGACCLKO["RGACCLKO<br/>periods · low/up range · local barrier"]
    GLOB["GLOBALKO*<br/>KO schedule · payment timing"]
    KIN["KNOCKIN*<br/>KI barrier · terminal cap/floor/strike"]
  end

  subgraph DAG["Compiled payoff DAG"]
    FS["fixing_schedule"]
    WOP["worst_of_performance"]
    LKO["local_ko_gate"]
    GKO["global_ko_gate"]
    KI["knock_in_gate"]
    RA["range_accrual"]
    CS["coupon_strip"]
    TERM["terminal residual<br/>KI1 / KI2 / NoKI"]
    NR["notional_return"]
    CASH["cash_settlement"]
    PHYS["physical_delivery_settlement"]
    DISC["payment_discount"]
    AGG["aggregate_legs"]
  end

  REG -.->|"must pre-exist"| BASKET
  BASKET ==>|"constituents + reference prices"| WOP
  KIKO -->|"toggles LKO"| LKO
  KIKO -->|"toggles GKO"| GKO
  KIKO -->|"toggles KI"| KI
  KIKO -->|"returnRatio"| NR
  KIKO -.->|"initial fixing"| WOP
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
  KI -->|"activates"| TERM
  GKO -->|"KO redemption"| NR
  TERM --> CASH
  TERM -->|"ITM delivery"| PHYS
  CS --> DISC
  NR --> DISC
  CASH --> DISC
  PHYS --> DISC
  DISC --> AGG
```

## What to notice

- The **thick arrow** `BASKET ==> WOP` is the coupling that hurts: the compiled DAG cannot be built until an external, pre-defined basket object exists.
- `KIKOSelect v1` only has **thin dashed/activation edges** into the gate and `notional_return` blocks. It is a feature switch, not a leaf binder.
- There is no `memory_carry` and no cash-flow rounding node; those arrive with MemRaki / RakiPlus.
- The residual is a RAKI terminal family (`KI1` / `KI2` / `NoKI`), not the FCN `down_and_in_put`.

Compare with [RakiPlus](RakiPlus.md); the node vocabulary is deliberately identical so the diff is the construction pattern.
