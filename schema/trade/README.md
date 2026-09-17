# Canonical trade repository schemas

The `schema/trade/` directory is the shared contract for the `fina-trade` repository boundary. It separates durable trade records from commands, events, market observations, and derived position views.

| Contract | Meaning | Persistence rule |
|---|---|---|
| `rfq.schema.json` | Received quote request | Mutable status, append quote versions |
| `quote.schema.json` | Immutable quote version | Never overwrite for repricing |
| `trade.schema.json` | Accepted quote as a lifecycle-managed trade | Amend through a command and event |
| `lifecycle-event.schema.json` | Committed state transition or observation event | Append-only and idempotent |
| `fixing-record.schema.json` | Market observation and payoff decision | Immutable per fixing key |
| `market-operation.schema.json` | Command envelope for lifecycle and market operations | Validate state version and idempotency |
| `position.schema.json` | Portfolio/instrument aggregate projection | Derived from non-terminal trades |

The trade service owns transactionality, identity, lifecycle state, event publication, and fixing records. The pricing service owns large pricing results and risk cubes; the trade service stores only quote summaries and durable references to those results. The UI consumes metadata and logical actions; it does not call database methods or select an MCP transport.

The former FCN-specific lifecycle schemas remain useful as product fixtures. New shared trade functionality should target these schemas and add product-specific extensions under a product namespace rather than duplicating the repository contract.
