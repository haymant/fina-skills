# FinA Model-Wiring Registry

This directory records how each product family connects shared semantics, lifecycle, pricing backends, risk profiles, and evidence gates. YAML entries are governance inputs for agents and reviewers; canonical payload compatibility remains defined by the repository-root `schema/` contracts.

**Note on the `flex` section:** the `flex.blocks` entries (KIKOSelect, RGACCDate, etc.) are Murex legacy termsheet groupings recorded for documentation and coverage tracking only. They are **not** consumed by finap's runtime — finap's UI rendering is driven entirely by `trade.rfq-create.schema.json` → `field-ui/*.json` → `metadata-registry.ts`. Do not assume a flex-block field name maps to a React component without checking the corresponding field-ui entry and renderer assignment.

## Entry selection

Load the product-family YAML before changing a scheduler handler, pricing backend, risk profile, lifecycle event, or E2E evidence command. Keep logical handlers separate from actual implementations. A backend marked `native_cpp` is not proven by its presence in YAML; the E2E must assert its engine marker and native module/build identity.

## Current entries

| Product family | Entry | Status |
|---|---|---|
| FCN / ELI | [`fcn.yaml`](fcn.yaml) | Executable native daily-term-sheet E2E |
| Range accrual / RAKI | [`range-accrual.yaml`](range-accrual.yaml) | Registry design; implementation evidence pending |
| Reverse KIKO | [`reverse-kiko.yaml`](reverse-kiko.yaml) | Registry design; implementation evidence pending |

## Playbook coverage

Every MurexPlaybook product page should map to a registry entry (or be explicitly listed as not-yet-registered). Current coverage:

| Playbook product page | Registry entry | Notes |
|---|---|---|
| `Products/KIKO/Reverse_KIKO.md` | `reverse-kiko.yaml` | Flex header `EqFlexKioV` registered |
| `Products/Range_Accruals/Range_Accrual_Raki.md` | `range-accrual.yaml` | Family entry (`EQ_RAKI`) |
| `Products/Range_Accruals/Memory_Range_Accrual_MemRaki.md` | `range-accrual.yaml` | `EQ_MEMRAKI` alias |
| `Products/Range_Accruals/RakiPlus_MemRakiPlus.md` | `range-accrual.yaml` | RakiPlus family variant |
| `Products/Range_Accruals/RAKI_Enhancement.md` | `range-accrual.yaml` | Enhancement variant |
| `Products/Range_Accruals/Double_No_Touch_RA.md` | _not registered_ | `EqFlexDblNT` / `EQ_DBARW` — pending |
| ELIFCN_KI (legacy daily termsheet) | `fcn.yaml` | No dedicated Playbook page; blocks from `fcn-legacy-termsheet` |
| `Products/Accumulators/AQDQ.md` | _not registered_ | Pending |
| `Products/Barriers/Barrier_Option.md` | _not registered_ | `DISCBARR` family — pending |
| `Products/Barriers/Discrete_Barrier.md` | _not registered_ | Pending |
| `Products/Other_Exotics/Digital_Option.md` | _not registered_ | Pending |
| `Products/Other_Exotics/Dispersion.md` | _not registered_ | Pending |
| `Products/Other_Exotics/Outperformance.md` | _not registered_ | Pending |
| `Products/Financing/SBL_Repo.md` | _not registered_ | Financing, out of scope for equity-flow registry |

## Versioning

Increment `version` when product semantics, lifecycle, backend selection, risk conventions, or evidence gates change. Record source revisions in the entry and preserve historical evidence outside this directory.
