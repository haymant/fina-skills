# FinA Model-Wiring Registry

This directory records how each product family connects shared semantics, lifecycle, pricing backends, risk profiles, and evidence gates. YAML entries are governance inputs for agents and reviewers; canonical payload compatibility remains defined by the repository-root `schema/` contracts.

## Entry selection

Load the product-family YAML before changing a scheduler handler, pricing backend, risk profile, lifecycle event, or E2E evidence command. Keep logical handlers separate from actual implementations. A backend marked `native_cpp` is not proven by its presence in YAML; the E2E must assert its engine marker and native module/build identity.

## Current entries

| Product family | Entry | Status |
|---|---|---|
| FCN / ELI | [`fcn.yaml`](fcn.yaml) | Executable native daily-term-sheet E2E |
| Range accrual / RAKI | [`range-accrual.yaml`](range-accrual.yaml) | Registry design; implementation evidence pending |
| Reverse KIKO | [`reverse-kiko.yaml`](reverse-kiko.yaml) | Registry design; implementation evidence pending |

## Versioning

Increment `version` when product semantics, lifecycle, backend selection, risk conventions, or evidence gates change. Record source revisions in the entry and preserve historical evidence outside this directory.
