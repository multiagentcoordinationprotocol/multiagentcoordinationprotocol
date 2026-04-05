
# MACP Transport Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) | [registries/transports.md](../registries/transports.md) | [core.proto](../schemas/proto/macp/v1/core.proto)

MACP supports multiple transport layers depending on deployment architecture.

## gRPC (Recommended)

Best for:
- high throughput coordination
- persistent streaming sessions
- microservice environments

Advantages:
- efficient binary transport
- streaming support
- strong typing via protobuf

The gRPC binding defines three categories of RPCs:

### `Send` (Unary)

The authoritative per-message request/ack surface. Use `SendResponse.ack` for standard acceptance or rejection signaling.

### `StreamSession` (Bidirectional)

An optional interactive envelope stream, advertised by `sessions.stream = true`. The stream carries canonical MACP Envelopes only — implementations MUST NOT invent ad-hoc pseudo-envelopes for acks or errors. Once bound to a `session_id`, all subsequent session-scoped envelopes on that stream MUST use the same `session_id`.

`StreamSession` is **not** a replacement for unary `Send` acknowledgements. Clients that need per-message negative acknowledgements SHOULD use `Send`. The base protocol does not define a passive attach/no-op envelope for observing an existing session, and session-scoped `Signal` envelopes are invalid as an attach mechanism. If you need zero-mutation observation, begin streaming before the activity of interest or use a deployment-specific extension outside the base protocol.

### `WatchModeRegistry` / `WatchRoots` (Server Streaming)

Optional discovery hint streams. A runtime MUST advertise the corresponding capability (`mode_registry.list_changed` or `roots.list_changed`) before these can be assumed interoperable. After receiving a change notification, clients SHOULD re-query the full surface (`ListModes` or `ListRoots`). Minimal implementations may send an initial change hint immediately after stream establishment and then stay idle until a later change occurs. Note that `ListModes` returns only standards-track modes; extension mode discovery is implementation-defined.

### `WatchSignals` (Server Streaming)

An optional server-streaming RPC that broadcasts ambient Signal envelopes to all subscribers. Signals are non-binding messages on the ambient plane — they carry empty `session_id` and empty `mode` in the Envelope. A `SignalPayload` MAY include a `correlation_session_id` to relate the signal to a session without making it session-scoped. Signals are ephemeral and are not available for replay. See [RFC-MACP-0006 §3.4](../rfcs/RFC-MACP-0006-transport-bindings.md#34-watchsignals).

### `GetSession` (Unary)

Returns a `SessionMetadata` snapshot for a given session, including the session's identity, state, timing, bound version fields, the current participant list, and per-participant activity summaries (`ParticipantActivity` with `participant_id`, `last_message_at_unix_ms`, `message_count`).

## HTTP

Best for:
- simple integrations
- environments where gRPC is restricted

## WebSockets

Best for:
- interactive coordination
- browser environments

## Message Buses

Best for:
- large distributed systems
- asynchronous coordination
- event-driven architectures

Examples: Kafka, NATS, RabbitMQ

## Transport Identifiers

Each transport binding has a registered identifier:

- `macp.transport.grpc.v1`
- `macp.transport.http.v1`
- `macp.transport.websocket.v1`
- `macp.transport.messagebus.v1`

These identifiers are used in agent manifest `transport_endpoints` to declare how an agent can be reached. See [`registries/transports.md`](../registries/transports.md).
