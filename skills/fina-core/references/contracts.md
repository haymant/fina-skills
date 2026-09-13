# Core contracts

Every cross-service event carries a stable event id, correlation id, topic, occurred-at timestamp, producer, schema/version, and typed payload. Use typed `market.*`, `leg.*`, `instrument.*`, `quote.*`, and `trade.lifecycle.*` topics rather than unstructured messages.

`ProductTerms` is the canonical user-facing product description. `PricingRequest` is a quote-time projection. `LifecycleState` is snapshotted into each reprice request for reproducibility; `trade_lifecycle_events` remains the audit trail, not the hot path.

An `InstrumentModel` combines structure, per-leg state-machine rules, lifecycle functions, market dependencies, and model version. A new product family should add a model plus compiled kernel/conformance corpus without changing the universal core schema.

