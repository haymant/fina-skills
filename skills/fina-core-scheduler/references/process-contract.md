# Process contract

A task context includes `correlation_id`, `inputs`, `dependency_results`, `event`, and `attempt`. Preserve these fields and avoid secrets in failure reports. `triggered_by` marks dormant work; a matching subscription activates it with the event context.
