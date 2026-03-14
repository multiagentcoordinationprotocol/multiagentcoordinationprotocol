
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

`StreamSession` is **not** a replacement for unary `Send` acknowledgements. Clients that need per-message negative acknowledgements SHOULD use `Send`.

### `WatchModeRegistry` / `WatchRoots` (Server Streaming)

Optional discovery hint streams. A runtime MUST advertise the corresponding capability (`mode_registry.list_changed` or `roots.list_changed`) before these can be assumed interoperable. After receiving a change notification, clients SHOULD re-query the full surface (`ListModes` or `ListRoots`).

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
