# Lifecycle guidance

Model RFQ, quote, trade, instrument, and position transitions explicitly. Prefer event history plus snapshots over hidden mutable state. Record reason, actor/source, effective time, and correlation id for amendments and corporate actions.
