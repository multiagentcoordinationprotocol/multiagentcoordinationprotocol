# RFC-MACP-0006
# Multi-Agent Coordination Protocol (MACP) — Transport Bindings

**Document:** RFC-MACP-0006
**Version:** 1.9.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001

> **Changelog — 1.9.0-draft:** New §2.1 (Trace Context Propagation). Implementations SHOULD propagate W3C Trace Context (`traceparent`, `tracestate`) in transport metadata: gRPC metadata, HTTP headers, message-bus message headers, and the WebSocket handshake for a connection. A runtime MUST NOT read or write trace context in Envelope fields or in `SessionStartPayload.extensions`, and `tracestate` MUST NOT carry MACP data. On a bidirectional `StreamSession`, every Envelope inherits the stream-open context; per-message context is deferred. Names for spans, attributes and metrics are in [docs/opentelemetry.md](../docs/opentelemetry.md) (informative). Additive. **Replay:** no exposure. Trace context never enters an Envelope or accepted history, so replay of the same Envelope sequence is unaffected by whether, or how, it was traced.
>
> **Changelog — 1.8.0-draft:** §3's `MACPRuntimeService` listing and the new §3.9 add two optional RPCs for runtime-issued decision receipts, `GetDecisionReceipt` and `GetReceiptKeys` ([RFC-MACP-0013](RFC-MACP-0013-commitment-hash.md) §13). Both are advertised by the new `Capabilities.decision_receipt`. Additive: a runtime that does not advertise them answers `UNIMPLEMENTED` and changes nothing else.
>
> **Changelog — 1.7.0-draft:** §3's `MACPRuntimeService` listing and §3.7 add the optional, read-only `WhatIfReplay` RPC ([RFC-MACP-0012](RFC-MACP-0012-policy.md) §8.1).
>
> **Changelog — 1.6.0-draft:** Three amendments from the seam-embedder-findings proposal (issue #185).
> (1) S9: §3's `MACPRuntimeService` listing now includes `SuspendSession` and `ResumeSession`, which RFC-MACP-0001 §7.5 depends on. They were in `core.proto` and missing here, so the listing showed 22 of 24 RPCs. The listing now matches `core.proto`'s `rpc` set in order, and `make prose-check` enforces that. Editorial: the proto was always authoritative.
> (2) S13: §3 adds "The gRPC binding MUST map error codes to gRPC status codes per the error-codes registry", with a new **gRPC Status** column in `registries/error-codes.md` that is aligned with the HTTP column. The HTTP binding (§4) already had this obligation; the gRPC binding had none, so a server could map codes its own way. Per-message rejections still travel in `SendResponse.ack` (§3.1). The proposal also asked for a parity-contract `error_status` table. It is **deferred**: `macp-runtime`'s server currently maps `POLICY_DENIED` to `FAILED_PRECONDITION`, and `SESSION_NOT_FOUND`, `INVALID_ENVELOPE`, `DUPLICATE_MESSAGE`, `UNSUPPORTED_PROTOCOL_VERSION`, `MODE_NOT_SUPPORTED` and `UNKNOWN_POLICY_VERSION` fall through to `FAILED_PRECONDITION`. A parity entry can only pin values that already agree. **Behaviour:** this is a new MUST. That server does not conform for those seven codes until it changes, and clients that branch on its current `FAILED_PRECONDITION` for `POLICY_DENIED` will see `PERMISSION_DENIED` once it does.
> (3) S8: §3.4 defines `WatchSignalsResponse.sender_authenticated` (`false` = unauthenticated), which is the wire carrier for RFC-MACP-0004 §4.1's unauthenticated-Signal annotation. §4 and §5 require the HTTP and WebSocket bindings to deliver Signals with the same flag. The proto field itself (`bool sender_authenticated = 2;`) lands in `core.proto` through the companion S8 change, not this one; this text references it by name. Additive: an absent flag reads as `false`, which is the safe direction.
> **Replay:** no exposure. Transport status codes and the Signal authentication flag are outside accepted session history. Signals never enter it (§3.4), and a rejected envelope produces the same accept/reject decision whatever status code reports it (RFC-MACP-0003 §1).
>
> **Changelog — 1.5.0-draft:** §3.2's bookkeeping-entries list now names
> `SessionCancel` explicitly (previously reachable only via the trailing "any other
> internal log entry" catch-all), citing RFC-MACP-0001 §7.3 where it is defined.
> Clarifying prose only — RFC-MACP-0001 §7.3 already called `SessionCancel` a
> "terminal annotation", the same class of entry this section already exempted from
> ordinal-consumption and subscribe-delivery (issue #159). This section's item 4
> ("only accepted-history envelopes are delivered") means accepted-history is a
> *necessary* condition for delivery, not sufficient — bookkeeping entries are part
> of accepted history (RFC-MACP-0001 §7.3, §7.5) yet are excluded from delivery by
> this bullet; that reading already applied to `SessionSuspend`/`SessionResume` and
> is unchanged by adding `SessionCancel` to the same list.
>
> **Changelog — 1.4.0-draft:** §3.2 gains a **Redelivery** subsection stating the client-side counterpart of RFC-MACP-0001 §8.2: a client MUST tolerate being redelivered an envelope it has already observed (both from at-least-once transport and from ordinary re-subscribe replay), MUST key duplicate detection on `message_id`, and MUST NOT let a repeat advance its sequence position, count against a Mode cardinality rule, or mutate accumulated state. The sequence-counting sentence is tightened to "distinct accepted envelopes" accordingly.
>
> **Changelog — 1.3.0-draft:** §3.2 now defines what the passive-subscribe sequence *is* — the 1-based ordinal of accepted session-scoped envelopes, exclusive `after_sequence`, internal entries consuming no ordinals, stability across restart and compaction, and `FAILED_PRECONDITION` for a resume below the compacted base. Previously the sequence was specified only behaviorally ("starting from `after_sequence + 1`"), which left clients no defined way to compute their own position.
>
> **Changelog — 1.2.0-draft:** §3.8 now describes the paged `ListSessions` contract (`page_size`, opaque `page_token`, `next_page_token`), which shipped in `core.proto` without a matching prose update. The prose is a correction, not a wire change: it states what the proto already defines, including that only an empty `next_page_token` signals completion.
>
> **Changelog — 1.1.0-draft:** passive session subscription is promoted from the former Appendix A.1 to core `StreamSession` semantics in §3.2. `subscribe_session_id` and `after_sequence` are normative on every runtime that advertises `sessions.stream = true`; they are not an optional capability.

## 1. Introduction

MACP is transport-agnostic. This document defines standard transport bindings for MACP messages.

Normative transport: gRPC over HTTP/2.

See [RFC-MACP-0001 Section 9](RFC-MACP-0001-core.md#9-transport-requirements) for core transport requirements. For discovery of transport endpoints in manifests, see [RFC-MACP-0005](RFC-MACP-0005-discovery-and-manifests.md).

Registered transport identifiers are listed in [`registries/transports.md`](../registries/transports.md).

## 2. Envelope Transmission

All transports MUST carry canonical MACP Envelopes defined in RFC-MACP-0001.

Transport bindings MUST preserve:

- within-session acceptance order,
- idempotency semantics,
- session isolation,
- structured error signaling appropriate to the transport.

### 2.1 Trace Context Propagation

Implementations SHOULD propagate distributed-trace context as [W3C Trace Context](https://www.w3.org/TR/trace-context/) (`traceparent` and `tracestate`) in the transport's own metadata:

- gRPC: request metadata keys `traceparent` and `tracestate`;
- HTTP: request headers `traceparent` and `tracestate`;
- message bus: the per-message headers or properties of the bus system;
- WebSocket: the handshake request's headers, which apply to the whole connection.

A runtime MUST NOT read or write trace context in Envelope fields or in `SessionStartPayload.extensions`. Trace context is transport metadata: it is never part of an Envelope, never enters accepted history, and has no effect on acceptance or on replay (RFC-MACP-0003). `tracestate` MUST NOT carry MACP data, such as session, message or sender identifiers.

Trace context is per request, so on a bidirectional `StreamSession` (§3.2) every Envelope sent on the stream inherits the context of the stream-open request. A client that needs a distinct trace per Envelope uses `Send`. Per-message context on a stream, as an optional field of `SendRequest` or `StreamSessionRequest` outside the Envelope, is deferred and would be additive.

Span, attribute and metric names for MACP are given in [docs/opentelemetry.md](../docs/opentelemetry.md) (informative, experimental).

## 3. gRPC Binding (Normative)

Conformant implementations MUST support the gRPC binding.

The canonical gRPC service is defined in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto). The proto file is the authoritative source; the listing below is reproduced for convenience.

```protobuf
service MACPRuntimeService {
  rpc Initialize(InitializeRequest) returns (InitializeResponse);
  rpc Send(SendRequest) returns (SendResponse);
  rpc StreamSession(stream StreamSessionRequest) returns (stream StreamSessionResponse);
  rpc GetSession(GetSessionRequest) returns (GetSessionResponse);
  rpc CancelSession(CancelSessionRequest) returns (CancelSessionResponse);
  // Session suspension / resume (RFC-MACP-0001 §7.5)
  rpc SuspendSession(SuspendSessionRequest) returns (SuspendSessionResponse);
  rpc ResumeSession(ResumeSessionRequest) returns (ResumeSessionResponse);
  rpc GetManifest(GetManifestRequest) returns (GetManifestResponse);
  rpc ListModes(ListModesRequest) returns (ListModesResponse);
  rpc WatchModeRegistry(WatchModeRegistryRequest) returns (stream WatchModeRegistryResponse);
  rpc ListRoots(ListRootsRequest) returns (ListRootsResponse);
  rpc WatchRoots(WatchRootsRequest) returns (stream WatchRootsResponse);
  // Extension mode lifecycle
  rpc ListExtModes(ListExtModesRequest) returns (ListExtModesResponse);
  rpc RegisterExtMode(RegisterExtModeRequest) returns (RegisterExtModeResponse);
  rpc UnregisterExtMode(UnregisterExtModeRequest) returns (UnregisterExtModeResponse);
  rpc PromoteMode(PromoteModeRequest) returns (PromoteModeResponse);
  // Ambient Signal observation
  rpc WatchSignals(WatchSignalsRequest) returns (stream WatchSignalsResponse);
  // Session lifecycle observation (RFC-MACP-0001 §7.3)
  rpc ListSessions(ListSessionsRequest) returns (ListSessionsResponse);
  rpc WatchSessions(WatchSessionsRequest) returns (stream WatchSessionsResponse);
  // Governance policy lifecycle (RFC-MACP-0012)
  rpc RegisterPolicy(RegisterPolicyRequest) returns (RegisterPolicyResponse);
  rpc UnregisterPolicy(UnregisterPolicyRequest) returns (UnregisterPolicyResponse);
  rpc GetPolicy(GetPolicyRequest) returns (GetPolicyResponse);
  rpc ListPolicies(ListPoliciesRequest) returns (ListPoliciesResponse);
  rpc WatchPolicies(WatchPoliciesRequest) returns (stream WatchPoliciesResponse);
  // Optional, read-only what-if replay (RFC-MACP-0012 §8.1)
  rpc WhatIfReplay(WhatIfReplayRequest) returns (WhatIfReplayResponse);
  // Optional runtime-issued decision receipts (RFC-MACP-0013 §13)
  rpc GetDecisionReceipt(GetDecisionReceiptRequest) returns (GetDecisionReceiptResponse);
  rpc GetReceiptKeys(GetReceiptKeysRequest) returns (GetReceiptKeysResponse);
}
```

The listing MUST name exactly the `rpc` set of `MACPRuntimeService` in `core.proto`, in the same order; `make prose-check` enforces this.

**Error status mapping.** The gRPC binding MUST map error codes to gRPC status codes per the [error-codes registry](../registries/error-codes.md). The registry's **gRPC Status** column is the mapping. It applies wherever the binding reports a MACP error code as the RPC's own status. It does not move per-message rejections out of `SendResponse.ack` (§3.1): a rejected envelope is still reported in the Ack, with the registry code in its `MACPError`.

### 3.1 `Send`

`Send` is the authoritative per-message request/ack surface.

A compliant runtime MUST use `SendResponse.ack` for standard per-message acceptance or rejection signaling.

### 3.2 `StreamSession`

`StreamSession` is an optional interactive envelope stream advertised by `sessions.stream`.

A runtime that advertises `sessions.stream = true` MUST implement `StreamSession` with these semantics:

- the stream carries canonical MACP Envelopes only,
- once the stream is bound to a non-empty `session_id`, all subsequent session-scoped envelopes on that stream MUST use the same `session_id`,
- accepted envelopes emitted by the server MUST appear in authoritative acceptance order for that session,
- the stream MUST NOT invent ad-hoc pseudo-envelopes (informal messages that are not canonical MACP Envelopes) whose payloads encode JSON-only acks or errors unless an explicitly negotiated experimental capability allows it.

`StreamSession` is **not** the standard replacement for unary `Send` acknowledgements. Clients that require standard per-message negative acknowledgements SHOULD use `Send`.

A runtime MAY echo back accepted client-submitted envelopes on the stream as part of the authoritative accepted sequence.

Session-scoped `Signal` envelopes are invalid in the base protocol and MUST NOT be used as a stream-attach mechanism. Clients that need zero-mutation observation of an existing session MUST use the passive session subscription semantics defined below.

#### Passive Session Subscription

`StreamSessionRequest` carries two session-binding shapes:

- `envelope` — a session-scoped coordination envelope. Standard `StreamSession` behavior as specified above.
- `subscribe_session_id` (with optional `after_sequence`) — a passive-subscribe frame that binds the stream to an existing session's broadcast without emitting a coordination message.

A single `StreamSessionRequest` MUST NOT set both `envelope` and `subscribe_session_id`; a runtime MUST reject such a request as an invalid argument.

On a request with `subscribe_session_id` set, a runtime that advertises `sessions.stream = true` MUST:

1. Authorize the caller. The caller MUST be an authenticated declared participant of the session, or an observer identity admitted by deployment policy (RFC-MACP-0004 §4). Unauthorized callers MUST be rejected.
2. Replay accepted session envelopes in strict acceptance order starting from `after_sequence + 1`. When `after_sequence = 0`, replay begins at the session's first accepted envelope.
3. Switch seamlessly to live broadcast on the same stream after replay drains, preserving within-session acceptance order.
4. Never replay rejected envelopes (RFC-MACP-0001 §7.2); only accepted-history envelopes are delivered.

**Sequence semantics.** For resume to be interoperable, a runtime MUST implement `after_sequence` against the following definition of the session sequence:

- The sequence is the **1-based ordinal of accepted session-scoped envelopes**, assigned in acceptance order. The first envelope accepted on a session has ordinal 1.
- Entries a runtime records for its own bookkeeping — the `SessionSuspend` / `SessionResume` annotations of RFC-MACP-0001 §7.5, the `SessionCancel` terminal annotation of RFC-MACP-0001 §7.3, TTL expiry, storage checkpoints, and any other internal log entry — MUST NOT consume ordinals. Client-visible ordinals are therefore contiguous.
- `after_sequence` is **exclusive**. Replay resumes at `after_sequence + 1`; `after_sequence = 0` replays from the session's first accepted envelope.

The Envelope carries no sequence field on the wire (RFC-MACP-0001 §6), so a client can determine its position only by counting the **distinct accepted envelopes** it has been delivered — see **Redelivery** below, since the same envelope may arrive more than once and a repeat MUST NOT advance the count. Two obligations follow, and a runtime MUST satisfy both:

1. The envelopes delivered on a subscribe stream MUST be exactly those that consume ordinals. A runtime MUST NOT deliver an internal annotation on this stream: a client cannot distinguish it from an ordinal-consuming envelope, and would over-count.
2. An ordinal MUST be stable for the life of the session — across runtime restarts, storage migration, and log compaction. A runtime that renumbers accepted envelopes breaks every resuming client silently, because the client asks to continue from a position that no longer denotes the same envelope and history is skipped or repeated with no error surface.

**Compaction.** A runtime that compacts session history MUST record, in the compaction checkpoint, the number of accepted ordinals it discarded, so that surviving envelopes retain their original ordinals instead of being renumbered from 1. A resume whose `after_sequence` falls below the compacted base MUST be rejected with gRPC status `FAILED_PRECONDITION`, identifying the lowest ordinal still available; it MUST NOT be silently served from the oldest surviving envelope. As with §3.8's `INVALID_ARGUMENT`, this is a transport status rather than a MACP error code — the codes in [`registries/error-codes.md`](../registries/error-codes.md) are envelope-scoped, and a resume request carries no Envelope.

**Redelivery.** A client MUST tolerate being delivered an envelope it has already observed. Two independent mechanisms produce this, and neither is a malfunction:

- MACP assumes at-least-once delivery semantics at the transport layer (RFC-MACP-0001 §8), so a transport MAY present the same envelope more than once.
- Re-subscribing replays history. A client that reconnects, or that opens a subscription with an `after_sequence` at or below a position it has already consumed, is delivered every accepted envelope after that point again — including ones it has already applied. `after_sequence = 0` on a reconnect replays the entire session.

A redelivered envelope is **the same message, not a new one**. Clients MUST key duplicate detection on `message_id` — the identity the runtime itself uses for this purpose (RFC-MACP-0001 §8.2) — and MUST observe the following:

1. A redelivery MUST NOT advance the client's sequence position; only a distinct accepted envelope does. A client that counts raw delivery events rather than distinct envelopes arrives at a position ahead of the true one, and its next resume silently skips history.
2. A redelivery MUST NOT count a second time against any Mode cardinality rule. Where a Mode limits a participant to one message of a kind — RFC-MACP-0007 §5 rule 3's one `Vote` per `proposal_id`, RFC-MACP-0011 §5 rule 3's one ballot per `request_id` per eligible participant — "a second" means a distinct `message_id`, never the same envelope arriving twice.
3. A consumer that accumulates state per envelope — appending to a list, incrementing a counter — MUST be idempotent with respect to `message_id`. Re-applying a redelivered envelope MUST NOT change derived state.

Runtimes are already required to enforce duplicate handling at their own ingress (RFC-MACP-0001 §8.2), so a duplicate never enters accepted history and is never broadcast. The requirements above are the client-side counterpart: a client reconstructing session state from a stream is handed the same envelope twice through ordinary reconnection, and MUST arrive at the state the runtime holds.

A stream opened with a passive-subscribe frame is conventionally read-only. Implementations MAY refuse subsequent envelope frames on such a stream; clients that intend to coordinate on the session SHOULD open a separate `StreamSession` or use unary `Send`.

When a transport-level or stream-fatal error occurs, the runtime SHOULD use native gRPC stream termination semantics.

### 3.3 `WatchModeRegistry` and `WatchRoots`

These watch streams are optional discovery hints.

`ListModes` SHOULD return only standards-track mode descriptors. Extension mode descriptors are discoverable through implementation-defined surfaces and are not part of the base `ListModes` response.

A runtime MUST advertise `mode_registry.list_changed = true` before `WatchModeRegistry` can be assumed interoperable.
A runtime MUST advertise `roots.list_changed = true` before `WatchRoots` can be assumed interoperable.

A watch notification indicates that the corresponding registry or roots view may have changed. Clients SHOULD re-query the full surface (`ListModes` or `ListRoots`) after receiving a change notification. A minimal compliant implementation MAY send an initial change hint immediately after stream establishment and then remain idle until a later change occurs.

### 3.4 `WatchSignals`

`WatchSignals` is an optional server-streaming RPC that broadcasts Ambient Signal Envelopes to all subscribers.

Signals are non-binding messages on the ambient plane (per RFC-MACP-0001 §5.1). They MUST carry empty `session_id` and empty `mode` in the Envelope. Signals MUST NOT enter any session's accepted history or mutate session state.

A `WatchSignalsResponse` contains the full `Envelope` of each accepted Signal. The `SignalPayload` within the envelope MAY include a `correlation_session_id` to indicate which session the signal relates to, without making the Signal session-scoped.

Use cases include:
- progress notifications from agents working on evaluations
- heartbeat and liveness signals
- status updates between coordination steps

A runtime that supports `WatchSignals` MUST broadcast all accepted Signal envelopes to all active subscribers. Signals are ephemeral — they are not persisted and are not available for replay.

**Sender authentication.** Each `WatchSignalsResponse` also carries `sender_authenticated`. A runtime MUST set it to `true` only when it authenticated the Signal's sender. `false` means the sender is unauthenticated. This field is the annotation that RFC-MACP-0004 §4.1 requires before an unauthenticated Signal is forwarded to subscribers. The Envelope itself carries no authentication field, so this flag is the only place the status travels. A proto3 bool that is absent reads as `false`. A subscriber whose runtime predates the field therefore sees every Signal as unauthenticated, which is the safe direction.

### 3.5 `GetSession`

`GetSession` returns a `SessionMetadata` snapshot for the given session. The response includes the session's identity, state, timing, and bound version fields (`mode_version`, `configuration_version`, `policy_version`), as well as the current participant list, per-participant activity summaries (`ParticipantActivity`), `context_id` (if set at session creation), and `extension_keys` (the keys of any extension blocks bound at session creation). The `ParticipantActivity` entries provide `participant_id`, `last_message_at_unix_ms`, and `message_count` for each participant that has sent at least one accepted message.

### 3.6 Extension Mode Lifecycle RPCs

`ListExtModes`, `RegisterExtMode`, `UnregisterExtMode`, and `PromoteMode` manage the lifecycle of non-standards-track (extension) coordination modes. These RPCs are implementation-defined surfaces for registering, discovering, and promoting experimental modes. See [RFC-MACP-0002](RFC-MACP-0002-modes.md) for extension mode semantics and the relationship between extension and standards-track modes.

### 3.7 Policy Lifecycle RPCs

Five RPCs manage the governance policy lifecycle (see [RFC-MACP-0012](RFC-MACP-0012-policy.md)):

```protobuf
rpc RegisterPolicy(RegisterPolicyRequest) returns (RegisterPolicyResponse);
rpc UnregisterPolicy(UnregisterPolicyRequest) returns (UnregisterPolicyResponse);
rpc GetPolicy(GetPolicyRequest) returns (GetPolicyResponse);
rpc ListPolicies(ListPoliciesRequest) returns (ListPoliciesResponse);
rpc WatchPolicies(WatchPoliciesRequest) returns (stream WatchPoliciesResponse);
```

`RegisterPolicy` and `UnregisterPolicy` mutate the policy registry. `GetPolicy` and `ListPolicies` are read-only queries. `WatchPolicies` is a server-streaming RPC for policy registry change notifications.

One further policy RPC is optional and read-only. A runtime advertises it with `PolicyRegistryCapability.what_if_replay`:

```protobuf
rpc WhatIfReplay(WhatIfReplayRequest) returns (WhatIfReplayResponse);
```

`WhatIfReplay` replays a session's accepted history under a candidate policy and reports how the outcome would differ. It never alters the session or the registry. See RFC-MACP-0012 Section 8.1.

See RFC-MACP-0012 Section 7 for registration constraints and evaluation semantics.

### 3.8 Session Lifecycle Observation RPCs

`ListSessions` and `WatchSessions` provide programmatic session lifecycle observation.

```protobuf
rpc ListSessions(ListSessionsRequest) returns (ListSessionsResponse);
rpc WatchSessions(WatchSessionsRequest) returns (stream WatchSessionsResponse);
```

`ListSessions` returns a bounded page of `SessionMetadata` for the sessions the runtime currently knows about (active and terminal, subject to whatever retention the runtime applies to terminal sessions). It is paginated: a single response is not required to carry the full result set. The pagination fields are defined in [`core.proto`](../schemas/proto/macp/v1/core.proto) — `page_size` and `page_token` on `ListSessionsRequest`, `next_page_token` on `ListSessionsResponse`. A runtime MUST advertise `sessions.list_sessions = true` before `ListSessions` can be assumed interoperable.

**Page size.** `page_size` is the maximum number of entries the client wants in one response. `page_size = 0` means server-chosen default; a runtime MUST substitute a bounded default rather than returning every known session. A runtime MAY cap the effective page size below the requested value, and the cap MUST be applied silently — clamping is not an error, and the client observes it only as a page smaller than it asked for. A runtime MUST reject a negative `page_size`.

**Continuation.** `page_token` is an opaque continuation token; an empty `page_token` begins a new traversal. The client MUST pass a non-empty `next_page_token` back verbatim as the next request's `page_token`. Tokens are implementation-defined and MAY be short-lived; clients MUST NOT parse them, construct them, or carry one across runtimes. A runtime that cannot decode a supplied `page_token` — malformed, expired, or issued elsewhere — MUST reject the request with gRPC status `INVALID_ARGUMENT`; the HTTP binding maps this to `400 Bad Request`. `INVALID_ARGUMENT` here is a transport status, not a MACP error code — the codes in [`registries/error-codes.md`](../registries/error-codes.md) are envelope-scoped, and `ListSessions` carries no Envelope.

**Completion.** Only an **empty** `next_page_token` means the result set is complete. A short page — one carrying fewer entries than `page_size`, including an empty one — does **not** mean completion while `next_page_token` is non-empty. Clients MUST continue paging until the token comes back empty, and MUST NOT treat page length as a termination signal.

**Traversal semantics.** A page is not a point-in-time snapshot, and `next_page_token` is a position, not a snapshot handle. Runtimes SHOULD traverse in a stable order such that a session present for the whole traversal is returned exactly once; a session created or removed mid-traversal MAY or MAY NOT appear, depending on where it falls relative to the current position. Clients that need to observe what changes during or after a traversal SHOULD pair `ListSessions` with `WatchSessions`.

`WatchSessions` is a server-streaming RPC that emits `SessionLifecycleEvent` notifications. Each event carries an `EventType` (CREATED, RESOLVED, EXPIRED, SUSPENDED, RESUMED, or CANCELLED), the affected `SessionMetadata`, and an `observed_at_unix_ms` timestamp. A runtime MUST advertise `sessions.watch_sessions = true` before `WatchSessions` can be assumed interoperable.

Session lifecycle events are ephemeral — they are not persisted and are not available for replay. Clients that disconnect MAY miss events. Control-planes and UIs SHOULD use `ListSessions` for initial sync and `WatchSessions` for incremental updates.

### 3.9 Decision Receipt RPCs

Two RPCs are optional. A runtime advertises both with `Capabilities.decision_receipt.get_decision_receipt`; a runtime that does not advertise it answers both with `UNIMPLEMENTED`:

```protobuf
rpc GetDecisionReceipt(GetDecisionReceiptRequest) returns (GetDecisionReceiptResponse);
rpc GetReceiptKeys(GetReceiptKeysRequest) returns (GetReceiptKeysResponse);
```

`GetDecisionReceipt` returns a signed or integrity-only `macp-receipt/1` decision receipt for a resolved session, as JSON text in `receipt_json`. Its caller MUST be authorized to observe the session, exactly as for `GetSession` ([RFC-MACP-0004](RFC-MACP-0004-security.md)). A session that is not RESOLVED, or was resolved without a `CommitmentPayload`, is `RECEIPT_UNAVAILABLE`. `GetReceiptKeys` returns the public verification keys as a JWK Set in `jwks_json` and needs only transport authentication, like `GetManifest`. Neither RPC alters any session. See RFC-MACP-0013 Section 13.

## 4. HTTP Binding

The HTTP binding is OPTIONAL. Implementations providing it MUST preserve Envelope semantics and MUST map error codes to HTTP status codes per the [error-codes registry](../registries/error-codes.md).

Example endpoints:

```text
POST /macp/envelope
POST /macp/session/start
GET  /macp/session/{id}
POST /macp/session/{id}/cancel
GET  /.well-known/macp.json
```

An HTTP binding that delivers Signals to observers, for example as a server-sent-event stream or a polling response, MUST deliver each Signal with the same `sender_authenticated` flag that `WatchSignalsResponse.sender_authenticated` carries (§3.4). `false` means the sender is unauthenticated. The flag is a sibling of the Envelope and MUST NOT be placed inside it, so each delivered item is the canonical JSON mapping of `WatchSignalsResponse` (RFC-MACP-0001 §10): `{"envelope": {...}, "sender_authenticated": true}`. A receiver MUST treat an absent `sender_authenticated` as `false`, because proto3 JSON encoders commonly omit a bool whose value is `false`.

## 5. WebSocket Binding

The WebSocket binding is OPTIONAL. Implementations providing it MUST frame each Envelope as a single WebSocket message and MUST preserve per-session ordering.

A WebSocket binding that delivers Signals to observers MUST frame each Signal as a single WebSocket message carrying the canonical JSON mapping of `WatchSignalsResponse`, so that the Envelope travels with its `sender_authenticated` flag (§3.4, §4). This frame wraps one Envelope rather than being a bare Envelope, and it is used only for delivering Signals to observers. `false` means the sender is unauthenticated, and a receiver MUST treat an absent flag as `false`.

## 6. Message Bus Binding

The message bus binding is OPTIONAL. Implementations providing it MUST preserve per-session message ordering and MUST define how authoritative acceptance is established.

Example topics:

```text
macp.signals
macp.sessions.{session_id}
```

Possible systems:

- Kafka
- NATS
- RabbitMQ

## 7. Transport Selection

Implementations MUST support at least the gRPC binding. Additional transports are OPTIONAL.

- gRPC -- high throughput coordination
- HTTP -- simple integrations
- WebSocket -- interactive coordination
- Message Bus -- distributed systems

## 8. Security

All transports MUST use encrypted transport.
Authentication requirements follow RFC-MACP-0004.
