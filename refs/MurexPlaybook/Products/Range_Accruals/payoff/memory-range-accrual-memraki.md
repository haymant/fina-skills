# MemRaki: Payoff Chapter

## Purpose and classification

**MemRaki** is an equity memory range-accrual note. It retains the Raki periodic range coupon and KI maturity structure but replaces ordinary WPS-only KO tests with memory KO conditions. A local or global KO is accepted only after the configured normalized-price condition has been satisfied at least once for every underlying. [1]

Murex books the product as `EQD` / `OPT` / `FLEX` with Flex Header and pricing payoff `EqFlexMemR`. The documented model group is `EQ_MEMRAKI`. [1]

## State and observation rules

For period \(i\):

\[
P_i=AccruRate_i\frac{N_{1,i}}{N_{2,i}}+FixCoupon_i.
\]

`RGACCDATE` supplies accrual dates. `RGACCLKO+` supplies periods, payment dates, ranges, local barriers, and coupons. `GLOBALKO*` supplies global observation mode and schedule. `KNOCKIN*` supplies the maturity KI branch.

For underlying \(k\), define a memory flag:

\[
L_k(t)=1\{\exists u\le t:S_k(u)/S_k(0)\ge LocMemBar\},
\]

with an analogous global flag \(G_k(t)\). A local memory KO occurs when every \(L_k=1\); a global memory KO occurs when every \(G_k=1\). The supplied note states that lock flags and lock dates are stored in `KIKOSEL*`; it does not fully define reset or correction behavior. [1]

## Payoff branches

A memory local KO pays:

\[
P_{LKO}=P_i+LocalKOBonus+ReturnRatio.
\]

A memory global KO pays:

\[
P_{GKO}=P_i+GlobalKOBonus+ReturnRatio.
\]

The accrued rate is measured through the KO date. If both local and global KO are recognized on the same day, global KO takes precedence. If no KO occurs, the maturity payoff follows the configured KI or non-KI Raki-style branch. The source says this may involve a call/put option on basket performance but does not provide the complete terminal formula; do not manufacture one. [1]

## Economic decomposition

| Component | Interpretation |
|---|---|
| Funding / principal | `ReturnRatio` contribution and returned notional on KO or maturity, subject to configured conversion. |
| Coupon | Periodic range accrual, fixed coupon, and KO bonus coupon. |
| Embedded option / residual | Memory barrier survival plus the unspecified KI/non-KI terminal option branch. |

The memory feature is not a coupon by itself. It is a path-state mechanism that gates KO termination and therefore changes the timing and continuation value of all other components.

## Flex-block mapping

| Block | Payoff graph role |
|---|---|
| `KIKOSEL*` | Feature flags, initial fixings, local/global lock flags and dates. |
| `RGACCDATE` | Accrual fixing schedule. |
| `RGACCLKO+` | Range periods, local KO, global coupon/barrier parameters, comparison operators. |
| `GLOBALKO*` | Global discrete/continuous observation schedule. |
| `KNOCKIN*` | KI barrier, observation, and terminal call/put parameters. |

## Explicit payoff graph

```text
initial fixings → per-underlying local/global memory flags
                 → all-underlying aggregation → LKO/GKO state
range observations → N1/N2 → periodic coupon
KI observations → ki_seen
KO gate → KO coupon + return, otherwise maturity KI/non-KI residual
```

The graph must load historical lock flags as authoritative realized state. It should preserve the first date each constituent became locked, the date the full basket condition became true, the selected KO type, and the accrued fixing counts.

## Lifecycle and constraints

Fixing updates the range and memory state. `Knock` settles accrued coupon, KO bonus, and returned notional. Maturity selects the KI/non-KI residual only if no KO has occurred. The documented product excludes Composite, Quanto, and other complex FX rules; basket currency equals premium currency, quantity principal is unsupported, tenor is limited to two years, and single-equity instruments are unsupported. [1]

The source leaves exact memory-date semantics, missing-fixing correction, KI terminal formula, endpoint operators, and rate-to-cashflow conversion unresolved. These require Murex configuration or executable parity evidence.

## References

[1]: ../Memory_Range_Accrual_MemRaki.md "Murex Playbook — EQ Memory Range Accrual (MemRaki)"
