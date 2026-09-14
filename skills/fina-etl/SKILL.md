---
name: fina-etl
description: FinA ETL and data projection patterns from street inputs to ProductTerms and bulk legacy data to versioned Parquet. Use for ingestion graphs, transformations, schema evolution, and data-quality checks.
---

# FinA ETL

Use for two distinct lanes: low-latency street projection and high-volume legacy ingestion. Do not force them into one pipeline.

## Lanes

- **Street lane:** RFQ/term-sheet input → canonical `ProductTerms` → typed pricing projection; optimize for milliseconds and explicit validation.
- **Bulk lane:** legacy JSON/CSV/records → Rust/columnar transformations → append-only/versioned Parquet; optimize for throughput, replay, and provenance.

## Workflow

1. Validate source shape and identify product-family version.
2. Project into the canonical schema; preserve source fields and provenance where needed.
3. Apply calendar, fixing, dividend, corporate-action, and serial/ISO conventions explicitly.
4. Write version anchors and deterministic partitions.
5. Test malformed input, missing keys, schema evolution, replay, and representative scale.

Use the existing Rust `run_pipelines` path for bulk benchmarks and Python projections for tiny request graphs. Never hide a semantic conversion in an OLAP query or pricing kernel.

## Canonical schema

Use [`schema/etl.schema.json`](../../schema/etl.schema.json) for pipeline declarations.
