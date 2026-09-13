---
name: fina-master
description: FinA master architecture and decision guide for equity-derivative trading systems. Use for retrospectives, new subsystem proposals, conflict resolution, scope control, and architecture decision records.
---

# FinA Master Architecture

Use this chapter to keep the ecosystem coherent. It is the book’s master/content skill: it defines principles, boundaries, and the route to detailed chapters.

## Architecture thesis

FinA is an equity-derivative ecosystem with shared semantics and plural runtimes. The target flow is:

`street input → ProductTerms → lifecycle/state → pricing projection → risk backends → trade event log → Parquet materialization → OLAP/UI`

The scheduler coordinates this flow but does not become the domain model or pricing engine.

## Design laws

- **Model meaning once; execute many ways.** Oracle/interpreter and compiled risk kernels must agree through a conformance corpus.
- **Events are contracts.** Publish durable lifecycle events only after the repository mutation succeeds.
- **Snapshots make hot paths reproducible.** Reprice requests carry lifecycle state and market/version inputs.
- **Columnar is the analytical boundary.** OLAP consumes versioned, auditable materializations rather than mutable service internals.
- **Scope follows the book.** Add product-family models from actual demand; avoid universal CDM-sized schema work.
- **No fake E2E.** A passing test with mocked pricing is not evidence of integration.

## Decision workflow

1. State the user journey and invariant.
2. Classify the change using `fina-index`.
3. Confirm ownership in `fina-core`.
4. Define the event/schema and compatibility policy.
5. Implement in the owning chapter; add conformance or contract tests.
6. Verify the smallest affected path and then the wired E2E path.

## Open design frontier

The current plan still identifies missing canonical `ProductTerms`, first-class `LifecycleState`, term-sheet/legacy emitters, reverse parsing, model registry/versioning, typed market topics, generic lifecycle reducers, report-version manifests, and production-scale risk materialization. Treat these as roadmap items, not silently assumed capabilities.

