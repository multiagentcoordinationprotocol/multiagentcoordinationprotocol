
# MACP Transport Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) | [registries/transports.md](../registries/transports.md) | [core.proto](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/proto/macp/v1/core.proto)

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

The gRPC binding defines the following RPC categories:

### `Send` (Unary)

The authoritative per-message request/ack surface. Use `SendResponse.ack` for standard acceptance or rejection signaling.

### `StreamSession` (Bidirectional)

An optional interactive envelope stream, advertised by `sessions.stream = true`. The stream carries canonical MACP Envelopes only — implementations MUST NOT invent ad-hoc pseudo-envelopes for acks or errors. Once bound to a `session_id`, all subsequent session-scoped envelopes on that stream MUST use the same `session_id`.

`StreamSession` is **not** a replacement for unary `Send` acknowledgements. Clients that need per-message negative acknowledgements SHOULD use `Send`. Session-scoped `Signal` envelopes are invalid as an attach mechanism. For zero-mutation observation of an existing session, use the passive session subscription form defined in [RFC-MACP-0006 §3.2](../rfcs/RFC-MACP-0006-transport-bindings.md#32-streamsession): send a `StreamSessionRequest` with only `subscribe_session_id` (and optional `after_sequence`) set, and the runtime replays accepted session history and then switches seamlessly to live broadcast on the same stream. A single request MUST NOT set both `envelope` and `subscribe_session_id`; the caller MUST be an authenticated declared participant or an observer identity admitted by deployment policy.

**Sequence semantics:** the passive-subscribe sequence is the 1-based ordinal of accepted
session-scoped envelopes, and `after_sequence` is exclusive, per
[RFC-MACP-0006 §3.2](../rfcs/RFC-MACP-0006-transport-bindings.md).

**Bookkeeping entries:** the `SessionSuspend`/`SessionResume` annotations
([RFC-MACP-0001 §7.5](../rfcs/RFC-MACP-0001-core.md)), the `SessionCancel` terminal annotation
([RFC-MACP-0001 §7.3](../rfcs/RFC-MACP-0001-core.md)), TTL expiry, and storage checkpoints
consume no ordinals, so client-visible ordinals stay contiguous — accepted history is a
necessary, not sufficient, condition for subscribe delivery, per
[RFC-MACP-0006 §3.2](../rfcs/RFC-MACP-0006-transport-bindings.md).

**Redelivery:** a client MUST tolerate redelivery, key duplicate detection on `message_id`, and
MUST NOT let a repeat advance its sequence position, per
[RFC-MACP-0006 §3.2](../rfcs/RFC-MACP-0006-transport-bindings.md).

### `WatchModeRegistry` / `WatchRoots` (Server Streaming)

Optional discovery hint streams. A runtime MUST advertise the corresponding capability (`mode_registry.list_changed` or `roots.list_changed`) before these can be assumed interoperable. After receiving a change notification, clients SHOULD re-query the full surface (`ListModes` or `ListRoots`). Minimal implementations may send an initial change hint immediately after stream establishment and then stay idle until a later change occurs. Note that `ListModes` returns only standards-track modes; extension mode discovery is implementation-defined.

### `WatchSignals` (Server Streaming)

An optional server-streaming RPC that broadcasts Ambient Signal Envelopes to all subscribers. Signals are non-binding messages on the ambient plane — they carry empty `session_id` and empty `mode` in the Envelope. A `SignalPayload` MAY include a `correlation_session_id` to relate the signal to a session without making it session-scoped. Signals are ephemeral and are not available for replay. See [RFC-MACP-0006 §3.4](../rfcs/RFC-MACP-0006-transport-bindings.md#34-watchsignals).

### `GetSession` (Unary)

Returns a `SessionMetadata` snapshot for a given session. See
[RFC-MACP-0006 §3.5 (`GetSession`)](../rfcs/RFC-MACP-0006-transport-bindings.md#35-getsession) and
[`schemas/json/macp-session-metadata.schema.json`](../schemas/json/macp-session-metadata.schema.json)
for the full field set, including `ParticipantActivity`'s three fields. The response mixes
bound-at-start immutable version fields with mutable runtime-derived fields (the current
participant list, `ParticipantActivity`) — the same distinction docs/architecture.md's own §9.3
draws.

### Extension Mode Lifecycle RPCs

`ListExtModes`, `RegisterExtMode`, `UnregisterExtMode`, and `PromoteMode` manage the lifecycle of
non-standards-track (extension) coordination modes. See
[RFC-MACP-0006 §3.6](../rfcs/RFC-MACP-0006-transport-bindings.md#36-extension-mode-lifecycle-rpcs) and
[docs/modes.md](modes.md#extension-modes).

### Policy Lifecycle RPCs

Five RPCs — `RegisterPolicy`, `UnregisterPolicy`, `GetPolicy`, `ListPolicies`, `WatchPolicies` —
manage the governance policy lifecycle. See
[RFC-MACP-0006 §3.7](../rfcs/RFC-MACP-0006-transport-bindings.md#37-policy-lifecycle-rpcs) and
[docs/policy.md](policy.md) for the five RPCs and their semantics.

### `ListSessions` / `WatchSessions` (Session Observation)

Two RPCs for programmatic session lifecycle observation — `ListSessions` for a paginated
snapshot and `WatchSessions` for real-time lifecycle events — per
[RFC-MACP-0006 §3.8 (Session Lifecycle Observation RPCs)](../rfcs/RFC-MACP-0006-transport-bindings.md#38-session-lifecycle-observation-rpcs).
See [docs/lifecycle.md](lifecycle.md#session-observation) for the RPC pair, the event kinds, and
the typical usage pattern.

## HTTP

Best for:
- simple integrations
- environments where gRPC is restricted

OPTIONAL binding; see [RFC-MACP-0006 §4 (HTTP Binding)](../rfcs/RFC-MACP-0006-transport-bindings.md).

## WebSockets

Best for:
- interactive coordination
- browser environments

OPTIONAL binding; see [RFC-MACP-0006 §5 (WebSocket Binding)](../rfcs/RFC-MACP-0006-transport-bindings.md).

## Message Buses

Best for:
- large distributed systems
- asynchronous coordination
- event-driven architectures

Examples: Kafka, NATS, RabbitMQ

OPTIONAL binding; see [RFC-MACP-0006 §6 (Message Bus Binding)](../rfcs/RFC-MACP-0006-transport-bindings.md).

## Transport Identifiers

Each transport binding has a registered identifier:

- `macp.transport.grpc.v1`
- `macp.transport.http.v1`
- `macp.transport.websocket.v1`
- `macp.transport.messagebus.v1`

These identifiers are used in agent manifest `transport_endpoints` to declare how an agent can be reached. [`registries/transports.md`](../registries/transports.md) is authoritative for the identifier set; the list above is a convenience copy.
