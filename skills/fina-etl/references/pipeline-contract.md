# ETL contract

Every stage should expose input schema, output schema/version, provenance, error policy, and latency/volume target. Append-only data must be replayable; updates must be explicit rather than silently overwriting history.
