
# MACP Transport Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) | [registries/transports.md](../registries/transports.md) | [core.proto](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/proto/macp/v1/core.proto)

MACP supports multiple transport layers depending on deployment architecture.

**JSON on the wire.** Any binding that carries MACP messages as JSON (HTTP, WebSockets, A2A, a
message bus with a JSON codec) uses the canonical JSON mapping of
[RFC-MACP-0001 §10](../rfcs/RFC-MACP-0001-core.md). It covers every message, not only the
Envelope: it is proto3 JSON with a fixed list of deviations (§10.8). In short: original
`snake_case` field names only (a `sessionId` key is ignored as unknown); 64-bit integers as JSON
numbers (§10.9); defaults emitted (§10.10); and three structural transforms, the Envelope's
RFC 3339 `timestamp`, its `payload`/`payload_b64`, and `PolicyDescriptor.rules` as a JSON
object (§10.11). A JSON `payload` is selected by `(mode, message_type)`; send `payload_b64` for a
Mode the receiver may not know, or whenever you need control of the exact payload bytes, since
the receiver's deterministic conversion (§10.13) produces the bytes that history, commitment
hashes and receipts are computed over.

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
[docs/policy.md](policy.md) for the five RPCs and their semantics. A sixth, `WhatIfReplay`, is
optional and read-only: it replays a session under a candidate policy and reports how the outcome
would differ ([RFC-MACP-0012 §8.1](../rfcs/RFC-MACP-0012-policy.md#81-what-if-replay-optional)).

### Decision Receipt RPCs

Two optional RPCs, advertised by `Capabilities.decision_receipt`: `GetDecisionReceipt` returns a
`macp-receipt/1` decision receipt for a resolved session as JSON text, and `GetReceiptKeys` returns
the public keys that verify its signatures as a JWK Set. A runtime that does not advertise them
answers `UNIMPLEMENTED`. See
[RFC-MACP-0006 §3.9](../rfcs/RFC-MACP-0006-transport-bindings.md#39-decision-receipt-rpcs) and
[RFC-MACP-0013 §13](../rfcs/RFC-MACP-0013-commitment-hash.md#13-receipt-issuance-optional).

### `ListSessions` / `WatchSessions` (Session Observation)

Two RPCs for programmatic session lifecycle observation — `ListSessions` for a paginated
snapshot and `WatchSessions` for real-time lifecycle events — per
[RFC-MACP-0006 §3.8 (Session Lifecycle Observation RPCs)](../rfcs/RFC-MACP-0006-transport-bindings.md#38-session-lifecycle-observation-rpcs).
See [docs/lifecycle.md](lifecycle.md#session-observation) for the RPC pair, the event kinds, and
the typical usage pattern.

## HTTP

Best for:
- simple integrations (`curl`, any HTTP client)
- browsers
- environments where gRPC is restricted

OPTIONAL, `provisional` binding; [RFC-MACP-0006 §4 (HTTP Binding)](../rfcs/RFC-MACP-0006-transport-bindings.md#4-http-binding)
is normative. In short:

- **Same RPCs, same names.** Every RPC above is `POST {base}/macp/v1/{Method}`, for example
  `POST https://runtime.example.com/api/macp/v1/GetSession`. The request and response are the
  RPC's messages as `application/json` in the canonical JSON mapping (RFC-MACP-0001 §10). Never
  label a body `application/macp-envelope+json`: a body is a request or response message, not a
  bare Envelope.
- **Streams are server-sent events.** The watch RPCs and the passive-subscribe form of
  `StreamSession` answer `text/event-stream`, one message per `data:` line. Only `StreamSession`
  subscribe events carry `id:` (the Envelope's ordinal), so a client resumes with
  `Last-Event-ID`. A fatal end is an `event: error` carrying `{"error": ...}`, for example
  `STREAM_LAGGED`. There is no bidirectional stream over HTTP: submit Envelopes with `Send`.
- **`Send` answers 200 for every Envelope decision.** Accepted, duplicate and rejected all come
  back in the Ack. Other failures are request-level: the registry's HTTP status, an
  `{"error": <MACPError>}` body ([`macp-http-error.schema.json`](../schemas/json/macp-http-error.schema.json))
  and a `MACP-Error-Code` header. A bare `404`, `405` or `415` is a transport status with no
  MACP error code.
- **`Authorization: Bearer` only**, no cookies, CORS off unless allowlisted; browsers stream
  with `fetch`, not `EventSource`.
- **Retries:** reuse the `message_id` when retrying `Send`. A `409` on a retried control-plane
  mutation means it was possibly applied, so check with `GetSession` or `GetPolicy`.
- **Discovery:** the manifest's `transport_endpoints` entry has `uri` = the base URL and
  `content_types: ["application/json"]`; the manifest itself is at `/.well-known/macp.json`.

Worked request/response pairs, including a server-sent-event transcript and error bodies, are in
[`examples/http/`](../examples/http/).

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

## A2A

Best for:
- agents that already speak [A2A](https://a2a-protocol.org/latest/specification/)
- joining MACP sessions without opening a second transport

Each Envelope travels as one A2A `Part` under the MACP extension URI, and each session is one A2A Task whose id is the `session_id`. MACP states map onto A2A task states, with the exact state carried in metadata. Per-envelope acceptance comes back as an Ack in the response Message.

OPTIONAL, `provisional` binding; see [RFC-MACP-0014 (A2A Extension Binding)](../rfcs/RFC-MACP-0014-a2a-binding.md) and the worked exchange in [`examples/a2a-binding-session.json`](../examples/a2a-binding-session.json).

## Transport Identifiers

Each transport binding has a registered identifier:

- `macp.transport.grpc.v1`
- `macp.transport.http.v1`
- `macp.transport.websocket.v1`
- `macp.transport.messagebus.v1`
- `macp.transport.a2a.v1`

These identifiers are used in agent manifest `transport_endpoints` to declare how an agent can be reached. [`registries/transports.md`](../registries/transports.md) is authoritative for the identifier set; the list above is a convenience copy.
