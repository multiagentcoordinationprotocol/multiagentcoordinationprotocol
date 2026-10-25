# RFC-MACP-0014
# Multi-Agent Coordination Protocol (MACP) — A2A Extension Binding

**Document:** RFC-MACP-0014
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0006

> **Changelog — 1.0.0-draft:** Initial draft. Defines how MACP Envelopes travel over the [Agent2Agent (A2A) protocol](https://a2a-protocol.org/latest/specification/) 1.0 as an A2A *profile extension*, and registers the binding as `macp.transport.a2a.v1` with status `provisional` in [`registries/transports.md`](../registries/transports.md). The binding adds no A2A fields, enum values or methods. All MACP semantics travel in `Part` content and in `metadata` keys namespaced by the extension URI.
> **Replay:** no exposure. A transport binding does not change which envelopes a runtime accepts or in what order (RFC-MACP-0003 §1). This RFC requires that the A2A Task view never be used as a replay source (§12).

---

## Abstract

A2A gives independent agents a common way to exchange messages and track units of work as Tasks. MACP gives a group of agents a bounded session that ends in a binding, replayable outcome. This document defines an A2A extension that carries MACP Envelopes inside A2A Messages, so an agent that already speaks A2A can take part in MACP coordination without opening a second transport. It specifies how an A2A AgentCard advertises the extension and the MACP modes it serves, how one Envelope maps to one A2A `Part`, how a MACP session maps to an A2A Task, how the five MACP session states map to A2A `TaskState`, how MACP error codes map to A2A errors, and what the binding leaves out.

---

## 1. Introduction

The A2A specification defines a client–server protocol between agents. Its unit of work is a Task with its own state machine. A2A lets a deployment add behaviour through *extensions*, which are identified by a URI, declared in the AgentCard and activated per request. An extension MUST NOT add fields to A2A data structures or add enum values. It places its own data in the `metadata` maps that A2A data structures already carry (A2A *Extensions*, "Extension Scope").

This binding is a profile extension in A2A's sense. It defines how existing A2A structures are used for MACP. The terms Task, Message, Part, Artifact, AgentCard, AgentExtension, TaskState, `contextId` and `taskId` have the meanings A2A gives them, and A2A JSON field names are written as A2A's JSON serialization spells them (`taskId`, `mediaType`, `"TASK_STATE_WORKING"`). The MACP terms Envelope, session, Ack, Signal and accepted history have the meanings RFC-MACP-0001 gives them.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in RFC 2119.

### 1.1 Roles

An **A2A MACP server** is an A2A server that fronts a MACP Runtime: it is the runtime itself, or a gateway that submits to the runtime over another binding. An **A2A MACP client** is an A2A client that submits MACP Envelopes as a session participant, initiator or observer. Every participant in a session reaches the same A2A MACP server. This binding does not define a topology in which participants are A2A servers that receive envelopes from each other (§14).

### 1.2 Relationship to RFC-MACP-0006

This binding is a transport binding in the sense of RFC-MACP-0006. It inherits the obligations of RFC-MACP-0006 §2 (Envelope Transmission): it MUST preserve within-session acceptance order, idempotency, session isolation and structured error signalling. It is OPTIONAL, and it does not relax RFC-MACP-0006 §7: a runtime that offers it still supports the gRPC binding.

---

## 2. Extension Identifier

The extension URI for this version of the binding is:

```text
https://multiagentcoordinationprotocol.io/a2a/extensions/macp/v1
```

It is written `EXT` below. Every `metadata` key this binding defines is the string `EXT` followed by `/` and the key name, for example `https://multiagentcoordinationprotocol.io/a2a/extensions/macp/v1/sequence`. A2A requires a new URI for a breaking change; a breaking change to this binding MUST use a new URI ending in `/v2` and a new transport identifier `macp.transport.a2a.v2`. When a client requests a version of the extension that the server does not support, the server MUST NOT fall back to a different version, as A2A requires.

The transport identifier registered for this binding is `macp.transport.a2a.v1` (§15).

---

## 3. AgentCard Declaration

An A2A MACP server MUST declare the extension as one `AgentExtension` entry in `AgentCard.capabilities.extensions`:

| `AgentExtension` field | Value |
|---|---|
| `uri` | `EXT` |
| `description` | Human-readable text. RECOMMENDED: name the coordination modes served. |
| `required` | `true` if the server accepts only MACP traffic on this interface; `false` if it also serves ordinary A2A requests. |
| `params` | The object below. |

`params` MUST contain:

- `macpVersions` — an array of the MACP protocol versions the server accepts in `Envelope.macp_version`, for example `["1.0"]`.
- `modes` — an array of the mode identifiers the server accepts in `SessionStart`, for example `["macp.mode.decision.v1", "macp.mode.quorum.v1"]`. Each entry MUST be a mode identifier from [`registries/modes.md`](../registries/modes.md) or a reverse-domain extension mode identifier (RFC-MACP-0002).
- `transport` — the string `"macp.transport.a2a.v1"`.

`params` MAY contain `manifestUrl`, the URL of the runtime's MACP manifest (RFC-MACP-0005 §7.1). A client that needs mode descriptors, policy descriptors or the runtime's other transport endpoints SHOULD read them from the manifest. The AgentCard is not a replacement for the manifest. A MACP manifest that lists an A2A endpoint uses `transport: "macp.transport.a2a.v1"` and the AgentCard URL as its `uri` (RFC-MACP-0005 §6).

A2A requires `AgentCard.skills`. This binding does not define a mapping from MACP modes to A2A skills. A server SHOULD publish one skill that describes MACP coordination in general, and MAY publish one skill per mode.

A server SHOULD sign its AgentCard (`AgentCard.signatures`) when `params.modes` or `params.manifestUrl` is used to make authorization decisions, because an altered card can redirect a client to a different manifest.

---

## 4. Activation

A client MUST activate the extension on every request that carries a MACP Envelope, observes a MACP session or cancels one. It does so by listing `EXT` in the `A2A-Extensions` request header (or the equivalent service parameter on bindings without headers), and it MUST also list `EXT` in `Message.extensions` of every Message that carries an Envelope.

A server that activates the extension SHOULD echo `EXT` in the `A2A-Extensions` response header, as A2A recommends. A server that receives a Message carrying a `Part` whose `mediaType` is a MACP Envelope media type (§5) without the extension being activated MUST NOT accept the Envelope. It MUST reject the request with `ExtensionSupportRequiredError` (§11).

---

## 5. Envelope Carriage

### 5.1 One Envelope per Part, one Part per Message

A Message that carries MACP MUST carry exactly one Envelope, in exactly one `Part`. The Part uses one of two encodings:

| Encoding | `Part` content | `Part.mediaType` |
|---|---|---|
| JSON (REQUIRED) | `data`: the canonical JSON mapping of the Envelope (RFC-MACP-0001 §10) | `application/macp-envelope+json` |
| Protobuf (OPTIONAL) | `raw`: the protobuf-encoded `macp.v1.Envelope` (base64 in A2A JSON) | `application/macp-envelope+proto` |

Both media types are registered in [`registries/media-types.md`](../registries/media-types.md) (RFC-MACP-0001 §10.5). A server MUST accept the JSON encoding and MAY accept the protobuf encoding. A server that receives an encoding it does not accept MUST reject the request with `ContentTypeNotSupportedError` (§11).

A Message that carries an Envelope Part MAY carry other Parts. Those other Parts are not MACP. They MUST NOT be submitted to the runtime, MUST NOT affect session state, and MUST NOT be interpreted as part of the Envelope. A Message that carries two or more Envelope Parts MUST be rejected as a whole (§11), so that a single A2A request never yields more than one acceptance decision.

The Envelope is carried whole. Its fields are not copied into, or overridden by, A2A fields. In particular:

- `Envelope.message_id`, not `Message.messageId`, is the MACP idempotency key (§12). A client SHOULD set `Message.messageId` equal to `Envelope.message_id` so that A2A-level traces line up, but a server MUST deduplicate on `Envelope.message_id` whatever `Message.messageId` says.
- `Envelope.sender` is the MACP sender. `Message.role` is `"ROLE_USER"` on every client-to-server Message and carries no MACP meaning.
- `Envelope.session_id` is the session. `Message.taskId` MUST agree with it as §6 requires.

### 5.2 Ack carriage

The response to a `SendMessage` request that carries an Envelope MUST be a `Message` (the `message` branch of `SendMessageResponse`), not a `Task`. That Message has `role: "ROLE_AGENT"`, lists `EXT` in `extensions`, and carries exactly one `Part`:

- `data`: the `macp.v1.Ack` for the submitted Envelope (RFC-MACP-0006 §3.1) as JSON, using the protobuf field names and enum string names the canonical JSON mapping uses (RFC-MACP-0001 §10.4), for example `{"ok": true, "duplicate": false, "message_id": "…", "session_id": "…", "accepted_at_unix_ms": 1792918800000, "session_state": "SESSION_STATE_OPEN"}`;
- `mediaType`: `application/json`;
- `metadata`: `{ "EXT/kind": "ack" }`.

The response Message's `taskId` is the session's Task id (§6) when the Envelope was session-scoped and the session exists, and is empty for a Signal or for a rejected `SessionStart`.

The Ack is the authoritative per-envelope acceptance result, as `SendResponse.ack` is on the gRPC binding (RFC-MACP-0006 §3.1). The Ack Part is not an Envelope, and a server MUST NOT encode it as one (RFC-MACP-0006 §3.2 forbids pseudo-envelopes).

Returning a Message rather than a Task keeps the Ack per request. A Task is long-lived and is returned by later `GetTask` calls, so an Ack placed in `Task.status.message` or `Task.metadata` would be reported again for requests it does not belong to.

A server MAY support `SendStreamingMessage` for Envelope submission. If it does, the first stream event MUST be the Ack Message described here. A server that accepts a session-scoped Envelope on a streaming request MAY continue the stream with the events of §9.2.

---

## 6. Identity Mapping

### 6.1 Session to Task

Each MACP session maps to exactly one A2A Task, and each A2A Task created by this binding maps to exactly one MACP session.

- **Creation.** A client starts a session by sending a Message whose Envelope is a `SessionStart`, with `Message.taskId` empty (A2A does not allow a client to choose the id of a new Task). When the runtime accepts the `SessionStart`, the server MUST create a Task whose `id` equals `Envelope.session_id`. The id is still server-assigned in A2A's sense: the server assigns it, and assigns it only after acceptance. `session_id` already meets RFC-MACP-0004 §11.2 (unguessable), so using it as the Task id exposes nothing the session id did not.
- **Rejected `SessionStart`.** When the runtime rejects a `SessionStart`, the server MUST NOT create a Task. The rejection is reported in the Ack (§5.2). `TASK_STATE_REJECTED` is therefore never used by this binding: creating a rejected Task would occupy an id that MACP does not consider taken.
- **Duplicate `SessionStart`.** A retry of an accepted `SessionStart` with the same `Envelope.message_id` MUST NOT create a second Task. Its Ack reports the duplicate (RFC-MACP-0001 §7.6 item 6). A different `SessionStart` for a `session_id` that already has a Task is rejected with `SESSION_ALREADY_EXISTS`.
- **Later envelopes.** Every later session-scoped Envelope MUST be sent with `Message.taskId` equal to `Envelope.session_id`. A server MUST reject a Message whose `taskId` differs from the `session_id` of its Envelope, without passing the Envelope to the runtime, by returning an Ack with `ok: false` and error code `INVALID_ENVELOPE` (§11.1). This rule is what stops the A2A routing key and the MACP session key from naming different sessions (§13).
- **Runtime-emitted envelopes.** `SessionCancel`, `SessionSuspend` and `SessionResume` are emitted by the runtime only (RFC-MACP-0001 §7.3, §7.5). A server MUST reject a client Message carrying any of them with `INVALID_ENVELOPE`.

### 6.2 Signals

A Signal is ambient (RFC-MACP-0001 §5.1). A Message carrying a Signal Envelope MUST have an empty `taskId`, and the server MUST NOT create a Task for it. The response is the Ack Message of §5.2 with an empty `taskId`.

### 6.3 Context

A2A `contextId` groups related Tasks and Messages. It has no MACP meaning. A server MUST NOT use `contextId` to route an Envelope to a session, MUST NOT treat two sessions that share a `contextId` as related for any acceptance decision, and MUST NOT deliver one session's envelopes to a subscriber of another because they share a `contextId`. A server MAY set a session's Task `contextId` to `SessionStartPayload.context_id` when that field is present and A2A's `contextId` rules allow it. Several sessions, for example a session and the session that supersedes its commitment (RFC-MACP-0001 §7.3.1), MAY share a `contextId`.

---

## 7. Submission

A client submits an Envelope with `SendMessage` (JSON-RPC method `SendMessage`, HTTP+JSON `POST /message:send`, gRPC `SendMessage`). The server MUST:

1. Check A2A-level preconditions: `A2A-Version`, extension activation (§4), Part encoding (§5.1), and the `taskId` rules of §6.
2. Pass the Envelope to the runtime unchanged.
3. Return the runtime's Ack as §5.2 describes.

The server MUST NOT accept an Envelope itself, reorder Envelopes, or synthesize envelopes. Acceptance is the runtime's alone (RFC-MACP-0001 §7.6).

`SendMessageConfiguration.returnImmediately` has no effect on MACP acceptance. The Ack is returned when the runtime has decided, whatever the flag says. `SendMessageConfiguration.historyLength` does not apply, because the response is a Message.

---

## 8. Lifecycle Mapping

A2A does not let an extension add `TaskState` values. This binding therefore maps each MACP session state to an existing `TaskState`, and carries the exact MACP state in the metadata key `EXT/sessionState`, whose value is the MACP state name (`"OPEN"`, `"SUSPENDED"`, `"RESOLVED"`, `"EXPIRED"` or `"CANCELLED"`). `TaskStatus` has no `metadata` field of its own, so the key goes in `Task.metadata` on every Task and in `TaskStatusUpdateEvent.metadata` on every status event this binding produces. Both MUST carry it. An A2A MACP client MUST read `EXT/sessionState`, not `TaskState`, to learn the session state.

| MACP session state (RFC-MACP-0001 §7.2) | A2A `TaskState` | Notes |
|---|---|---|
| `OPEN` | `TASK_STATE_WORKING` | A Task is created only on acceptance, so `TASK_STATE_SUBMITTED` is not used. |
| `SUSPENDED` | `TASK_STATE_WORKING` | See §8.1. `EXT/sessionState` is `"SUSPENDED"`. |
| `RESOLVED` | `TASK_STATE_COMPLETED` | The accepted Commitment is an Artifact (§9.1). |
| `EXPIRED` | `TASK_STATE_FAILED` | A2A has no expired state. `EXT/sessionState` is `"EXPIRED"`. |
| `CANCELLED` | `TASK_STATE_CANCELED` | Spelling differs; meaning matches. |

`TASK_STATE_SUBMITTED`, `TASK_STATE_REJECTED`, `TASK_STATE_INPUT_REQUIRED` and `TASK_STATE_AUTH_REQUIRED` are not used for a MACP session's Task. A missing or failed credential is a request-level error (§11), not a Task state.

The mapping preserves MACP's monotonic lifecycle. The three MACP terminal states map to A2A terminal states, and A2A permits no transition out of a terminal state. The two non-terminal MACP states map to a non-terminal A2A state. A server MUST NOT report a terminal `TaskState` for a session the runtime has not terminated, and MUST NOT report a non-terminal `TaskState` after it has.

### 8.1 Why SUSPENDED is not INPUT_REQUIRED

`TASK_STATE_INPUT_REQUIRED` is A2A's interrupted state, and suspension is MACP's hold for human review (RFC-MACP-0001 §7.5), so it looks like a match. It is not one. `INPUT_REQUIRED` tells the client to send input, and a generic A2A client may prompt its user to do so. A suspended MACP session rejects every Mode message with `SESSION_NOT_OPEN` until it is resumed, and only `ResumeSession` resumes it. Reporting `INPUT_REQUIRED` would invite exactly the submissions the session will refuse. A client that does nothing during a hold behaves correctly, so `TASK_STATE_WORKING` is the safe report. A MACP client learns of the hold from `EXT/sessionState`.

### 8.2 Expiry and failure

`TASK_STATE_FAILED` with `EXT/sessionState: "EXPIRED"` means the session's TTL or `max_suspend_ms` cap elapsed, or deterministic runtime policy expired it (RFC-MACP-0001 §7.3). It does not mean the runtime failed. A runtime failure is reported as an error on the request that observed it (§11) and does not change the session's state.

---

## 9. Observation

### 9.1 Accepted envelopes as Artifacts

Each accepted session-scoped Envelope that consumes an ordinal under RFC-MACP-0006 §3.2 is exposed as one A2A Artifact:

| `Artifact` field | Value |
|---|---|
| `artifactId` | `"macp:"` followed by `Envelope.message_id` |
| `name` | `Envelope.message_type` |
| `parts` | One Part carrying the Envelope, encoded as §5.1 describes |
| `metadata` | `{ "EXT/sequence": N }`, where N is the 1-based ordinal of RFC-MACP-0006 §3.2 |
| `extensions` | `[EXT]` |

Runtime annotations that consume no ordinal (`SessionCancel`, `SessionSuspend`, `SessionResume`) are not exposed as Artifacts. Their effect is visible as a status change (§8), which is how RFC-MACP-0006 §3.2 already treats them on the gRPC subscribe stream.

On `RESOLVED`, the accepted Commitment is one of these Artifacts. A2A clients that only want the outcome SHOULD select the Artifact whose `name` is the Mode's terminal message type (`"Commitment"` for the standard modes).

`Task.artifacts` SHOULD list these Artifacts in ordinal order. A server MAY bound the number it returns. A client that needs the complete accepted history MUST obtain it from the runtime (for example by passive subscription, RFC-MACP-0006 §3.2) and MUST NOT assume `Task.artifacts` is complete. `Task.history` holds A2A Messages as A2A defines them. It is not the MACP accepted history: it can hold Messages whose Envelopes were rejected, and it can hold non-MACP Parts.

### 9.2 Streams

A server that sets `AgentCard.capabilities.streaming` MUST support `SubscribeToTask` on a session's Task:

- each newly accepted Envelope is sent as a `TaskArtifactUpdateEvent` carrying the Artifact of §9.1, with `append: false` and `lastChunk: true`;
- each session state change is sent as a `TaskStatusUpdateEvent` carrying the `TaskState` and `EXT/sessionState` of §8;
- events for one session MUST be sent in acceptance order, and a state change MUST be sent after the Artifact of the envelope that caused it (for example, the Commitment Artifact before the `TASK_STATE_COMPLETED` event).

A2A subscription has no resume position equivalent to `after_sequence`. A client that reconnects MUST use `EXT/sequence` to discard Artifacts it has already seen. It MUST NOT let a repeat advance its position or count twice, which is the client duty RFC-MACP-0006 §3.2 already places on gRPC subscribers under **Redelivery**. A client that detects a gap in `EXT/sequence` MUST recover the missing envelopes from `GetTask` or from the runtime.

A2A rejects `SubscribeToTask` on a Task in a terminal state. A client that wants the record of a finished session uses `GetTask` or the runtime.

### 9.3 Signals

A2A has no subscription that is not tied to a Task, so this binding does not deliver Signals to observers. A client that needs Signals uses `WatchSignals` or another binding that delivers them (RFC-MACP-0006 §3.4). A server MUST NOT create a Task in order to deliver Signals.

### 9.4 GetTask and ListTasks

`GetTask` on a session's Task returns its current state (§8) and Artifacts (§9.1). `ListTasks` MUST return only Tasks for sessions the caller is authorized to observe (§13).

---

## 10. Control Operations

### 10.1 CancelTask

`CancelTask` on a session's Task is a `CancelSession` request for that session. The server MUST pass it to the runtime with the caller's authenticated identity. The runtime applies RFC-MACP-0001 §7.3: by default only the session initiator may cancel, and policy MAY delegate the right to other roles.

On acceptance, the Task moves to `TASK_STATE_CANCELED` with `EXT/sessionState: "CANCELLED"`, and the runtime appends `SessionCancel` to the accepted history. `CancelTask` on a `SUSPENDED` session is permitted, because RFC-MACP-0001 §7.2 permits `SUSPENDED → CANCELLED`. On rejection, the server returns the error of §11.

### 10.2 Suspend and resume

A2A has no suspend or resume operation, and this binding does not define one. `SuspendSession` and `ResumeSession` are invoked over another binding (RFC-MACP-0001 §7.5). Their effects appear on the A2A Task as status changes.

---

## 11. Error Mapping

### 11.1 Two layers

An Envelope that reaches the runtime is accepted or rejected, and that decision is reported **in band**, in the Ack (§5.2), on a successful A2A response. A rejected Envelope is not an A2A protocol error. This keeps the accept/reject decision the same whatever binding carried the Envelope (RFC-MACP-0003 §1), and gives the client the exact MACP code it would get on any other binding.

The server itself reports three Envelope checks in band in the same Ack shape, because each concerns the Envelope rather than the A2A request: the `taskId` mismatch of §6.1, a client-sent runtime-emitted envelope (§6.1), and an undecodable Envelope Part (§11.2). Every other request that fails before an Envelope reaches the runtime, or that is not an Envelope submission at all (`GetTask`, `CancelTask`, `SubscribeToTask`), is reported as an **A2A error**. Every A2A error this binding produces MUST carry, in its details, a `google.rpc.ErrorInfo` object whose `reason` is the MACP error code from [`registries/error-codes.md`](../registries/error-codes.md) and whose `domain` is `multiagentcoordinationprotocol.io`. On the JSON-RPC binding that object is an element of `error.data`, with `"@type": "type.googleapis.com/google.rpc.ErrorInfo"`, as A2A requires. Its `metadata` SHOULD carry `session_id` and `message_id` when known. A server MAY include A2A's own `ErrorInfo` alongside it.

On the A2A HTTP+JSON and gRPC bindings, the status code is the one A2A assigns to the A2A error. A client MUST branch on the MACP `reason`, not on the A2A error type, because several MACP codes share one A2A error.

### 11.2 In-band codes

Once an Envelope reaches the runtime, every MACP rejection is reported in the Ack, including `INVALID_ENVELOPE`, `UNSUPPORTED_PROTOCOL_VERSION`, `MODE_NOT_SUPPORTED`, `INVALID_SESSION_ID`, `FORBIDDEN`, `DUPLICATE_MESSAGE`, `SESSION_ALREADY_EXISTS`, `UNKNOWN_POLICY_VERSION`, `POLICY_DENIED` and `INVALID_POLICY_DEFINITION`. A suspended session's `SESSION_NOT_OPEN` is also in band, because a suspended session's Task is non-terminal. A Part with an Envelope media type whose content does not decode as an Envelope is rejected in band with `INVALID_ENVELOPE`, with the Ack's `message_id` empty when it cannot be read.

`UNSUPPORTED_PROTOCOL_VERSION` concerns `Envelope.macp_version`. It is unrelated to A2A's `VersionNotSupportedError`, which concerns the `A2A-Version` header.

### 11.3 A2A-level codes

| Condition | A2A error | `ErrorInfo.reason` |
|---|---|---|
| Message carries an Envelope Part without the extension activated (§4) | `ExtensionSupportRequiredError` | `INVALID_REQUEST` |
| Envelope Part uses an encoding the server does not accept (§5.1) | `ContentTypeNotSupportedError` | `INVALID_REQUEST` |
| Message carries two or more Envelope Parts (§5.1) | JSON-RPC Invalid params (`-32602`) | `INVALID_REQUEST` |
| `Message.taskId` names a Task that does not exist, or one the caller may not observe | `TaskNotFoundError` | `SESSION_NOT_FOUND` |
| `Message.taskId` names a Task in a terminal state (A2A requires this error) | `UnsupportedOperationError` | `SESSION_NOT_OPEN` |
| `GetTask` on a Task that does not exist or that the caller may not observe | `TaskNotFoundError` | `SESSION_NOT_FOUND` |
| `SubscribeToTask` on a Task in a terminal state | `UnsupportedOperationError` | `SESSION_NOT_OPEN` |
| `CancelTask` on a Task in a terminal state | `TaskNotCancelableError` | `SESSION_NOT_OPEN` |
| `CancelTask` by a caller the runtime does not authorize to cancel | `TaskNotCancelableError` | `FORBIDDEN` |
| Request rejected for size before the Envelope is decoded | A2A request error; HTTP `413` on HTTP+JSON | `PAYLOAD_TOO_LARGE` |
| Request rejected by rate limiting before the Envelope is decoded | A2A request error; HTTP `429` on HTTP+JSON | `RATE_LIMITED` |
| Authentication failed | A2A authentication failure (HTTP `401` on HTTP+JSON) | `UNAUTHENTICATED` |
| Runtime unreachable or failed | JSON-RPC Internal error (`-32603`) | `INTERNAL_ERROR` |
| `A2A-Version` not supported | `VersionNotSupportedError` | (A2A's own; no MACP reason) |

The `taskId` mismatch of §6.1 and a client Message carrying a runtime-emitted envelope are rejected in band with `INVALID_ENVELOPE`. They do not appear in this table.

A server MUST return `TaskNotFoundError` both for a Task that does not exist and for one the caller is not authorized to observe, so that the two cannot be told apart. This is how the binding keeps session existence private, as RFC-MACP-0004 §6 requires for session isolation.

---

## 12. Ordering, Idempotency and Replay

- **Order.** The authoritative order of a session is the runtime's acceptance order (RFC-MACP-0001 §8.1), which `EXT/sequence` exposes. The order of A2A requests, of `Task.history`, of `Task.artifacts` and of stream events is not authoritative.
- **Idempotency.** A retried submission, including one with a new `Message.messageId`, is deduplicated on `Envelope.message_id` (RFC-MACP-0001 §8.2). The server MUST return the runtime's duplicate Ack and MUST NOT expose a second Artifact for it. A retry whose original was accepted can arrive after the session has terminated, most often a retried Commitment whose response was lost. A2A then requires `UnsupportedOperationError` (§11.3), so the server MUST first ask the runtime whether `Envelope.message_id` is in the session's accepted history and, if it is, MUST set `"duplicate": "true"` in that error's `ErrorInfo.metadata`. A client MUST treat such an error as the duplicate Ack of an accepted Envelope, not as a rejection.
- **Append-only.** A server MUST NOT remove, reorder or rewrite an Artifact of §9.1 once exposed. An A2A Task view MAY be truncated (§9.1). It MUST NOT be edited.
- **Replay.** The A2A Task view is a projection of accepted history and is never a replay source. Replay uses the runtime's accepted history and recorded versions (RFC-MACP-0003 §1). A replayer that has only the Artifacts of a Task MUST treat the record as incomplete unless it can show that `EXT/sequence` runs from 1 without a gap up to the terminal Envelope.

---

## 13. Security Considerations

- **Transport.** A2A over this binding MUST use TLS, as RFC-MACP-0006 §8 requires of every binding.
- **Sender binding.** The server MUST bind `Envelope.sender` to the identity authenticated by the AgentCard's `securitySchemes`, and MUST reject an Envelope whose sender is not that identity, in band, with `FORBIDDEN` (RFC-MACP-0004 §3, §4). Delegated submission follows RFC-MACP-0004 §3.1 and is not created by A2A alone: holding an A2A credential does not make the holder a delegate.
- **Session isolation.** The `taskId` rule of §6.1 and the `contextId` rule of §6.3 together stop an A2A request from delivering an Envelope to a session it does not name. `GetTask`, `ListTasks` and `SubscribeToTask` MUST be authorized against the session's participants and observers, not merely against the A2A caller's credentials (RFC-MACP-0004 §6).
- **Signals.** An A2A MACP server receiving a Signal applies RFC-MACP-0004 §4.1 like any other binding.
- **Push notifications.** A push-notification webhook receives Task state from outside the session's authorization boundary. A server MUST NOT send a MACP session's Artifacts to a push-notification endpoint unless the caller that registered it is authorized to observe the session. A server that cannot enforce this MUST return `PushNotificationNotSupportedError` for MACP Tasks.
- **Denial of service.** Rate limits, payload limits and admission control of RFC-MACP-0004 §7 apply per A2A request. Non-MACP Parts in an Envelope-carrying Message count toward the request size.
- **AgentCard integrity.** See §3 on signing the card.

---

## 14. Out of Scope

This binding does not define:

- a topology in which participants are A2A servers that receive envelopes from each other, or a gateway that fans envelopes out to participant AgentCards;
- how participants learn of a session they were named in (invitation and bootstrap). A2A push notifications MAY be used for this. Their semantics here are limited to §13;
- a mapping from MACP modes to A2A skills (§3);
- `tenant` routing beyond what A2A defines. A multi-tenant server applies RFC-MACP-0004 §11 independently of A2A's `tenant` field;
- suspend and resume over A2A (§10.2), or delivery of Signals to observers (§9.3);
- an A2A state-machine extension. This binding is a profile extension and adds no `TaskState`;
- the normative status of A2A itself. A2A 1.0 is the version this binding was written against. A later A2A version that changes the structures used here needs a new version of this binding.

---

## 15. Registry Considerations

This document registers `macp.transport.a2a.v1` in [`registries/transports.md`](../registries/transports.md) and the matching capability identifier in [`registries/capabilities.md`](../registries/capabilities.md), both with status `provisional`. Following the rule in that registry, the binding becomes `permanent` only when two independent implementations interoperate over it.

---

## Appendix A. Example (Informative)

[`examples/a2a-binding-session.json`](../examples/a2a-binding-session.json) is a complete exchange: an AgentCard declaring the extension, a `SessionStart` carried in a JSON-RPC `SendMessage` request with its Ack, a Proposal and a Vote, the Commitment, the resulting `TASK_STATE_COMPLETED` Task with its Artifacts, and two error responses (a terminal Task, and a missing extension activation). `make json-validate` validates every Envelope embedded in an A2A Part of that file against `macp-envelope.schema.json`.

A Message carrying a `Vote` looks like this on the JSON-RPC binding:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "SendMessage",
  "params": {
    "message": {
      "messageId": "01JD2A2A0V0TE0000000000003",
      "taskId": "6f1c2a9e-4b7d-4c1e-9a53-2d8f0b7e5a10",
      "role": "ROLE_USER",
      "extensions": ["https://multiagentcoordinationprotocol.io/a2a/extensions/macp/v1"],
      "parts": [
        {
          "mediaType": "application/macp-envelope+json",
          "data": {
            "macp_version": "1.0",
            "mode": "macp.mode.decision.v1",
            "message_type": "Vote",
            "message_id": "01JD2A2A0V0TE0000000000003",
            "session_id": "6f1c2a9e-4b7d-4c1e-9a53-2d8f0b7e5a10",
            "sender": "agent://fraud",
            "timestamp": "2026-10-25T09:00:02Z",
            "payload": { "proposal_id": "p-1", "vote": "APPROVE", "reason": "Within risk appetite" }
          }
        }
      ]
    }
  }
}
```
