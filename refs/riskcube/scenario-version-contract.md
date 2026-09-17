# RiskCube scenario and version contract

## Purpose

Use this reference for scenario/version catalog design, lifecycle actions, batch triggering, and reproducibility. The POC in `fina-pricer` is a reference for concepts only; do not copy its JSON-cell storage or naming choices.

## Canonical distinction

A **scenario** is a durable market-data definition. It describes a base, snapshot, current-market resolver, or rule-based shock. A **version** is an immutable release/execution anchor for a population and engine configuration. A scenario may be reused across versions; a version may contain multiple scenarios. A trigger creates an immutable execution instance that links one version to one scenario and one dataset manifest.

Use the machine-readable contracts:

- `schema/riskcube/scenario.schema.json`
- `schema/riskcube/version.schema.json`

Keep stable human keys (`scenario_key`, `version_key`) separate from compact database identifiers (`scenario_id`, `version_id`). Allocate identifiers once and never recycle them. Never mutate a scenario or version referenced by a completed instance; create a new key/version instead.

## Lifecycle

1. **Create** a draft scenario or version after validating key uniqueness and snapshot timestamps.
2. **Validate** references, market-data availability, trade-repository snapshot, authorization, and request/template compatibility.
3. **Run** one or more scenario instances under a version. Persist status transitions and idempotency keys.
4. **Complete** only after all generated datasets, manifests, checksums, and row counts pass validation.
5. **Publish** a report metadata record pointing at the completed version and dataset. Publishing never copies generated measures into JSON.
6. **Retire** metadata without deleting immutable data. Deletion is allowed only for unused drafts.

Required execution identity is `instance_id`, `batch_key`, `version_key`, `scenario_key`, `scenario_id`, `version_id`, engine/schema revisions, request hash, source snapshot times, status, timestamps, and dataset manifest URI.

## Scenario rules

Represent manipulations as typed rules (`spot`, `volatility`, `fx`, `interest_rate`, `dividend`, `fx_volatility`) with explicit operation (`absolute`, `relative`, `set`, or `parallel`) and optional scope. A current-market report is a resolver-backed scenario, not invented data. Store references to snapshots or request templates, not large generated payloads or credentials.

## Version rules

A version is the reproducibility boundary. It pins the trade population, market-data as-of, engine version, schema version, and participating scenario keys. A rerun with changed inputs creates another version or an execution instance under a new batch key; it must not overwrite a completed partition.

## Actions

Recommended logical operations are `riskcube.scenario.create`, `.update-draft`, `.list`, `.get`, `.retire`; `riskcube.version.create`, `.list`, `.get`, `.retire`; and `riskcube.instance.trigger`, `.cancel`, `.retry`. `update-draft` must reject completed or referenced definitions. `trigger` must be idempotent on `(version_key, scenario_key, batch_key, request_hash)`.

## Provenance and failure

Record validation errors as structured evidence. A failed instance keeps its metadata and diagnostic references; it does not publish a partial report. Retries create a new instance or a new attempt identifier and never rewrite an already completed dataset.
