# RFC-MACP-0001
# Multi-Agent Coordination Protocol (MACP) — Core

**Document:** RFC-MACP-0001
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Canonical wire format:** Protocol Buffers
**Normative transport:** gRPC over HTTP/2
**Required JSON mapping:** Yes
**Intended status:** Stable Core

> This is an RFC-style open standard. It is not an IETF RFC.

---

## Abstract

The Multi-Agent Coordination Protocol (MACP) defines a structural coordination kernel for autonomous multi-agent systems. MACP introduces one strict invariant: binding, convergent coordination MUST occur inside explicit, bounded Coordination Sessions. Ambient informational exchange MAY occur continuously as Signals, but Signals MUST remain non-binding.

MACP Core does not define decision theory, arbitration mathematics, governance policy, tool semantics, or domain logic. Those behaviors are defined by Coordination Modes layered above MACP Core. MACP Core defines structure: initialization and capability negotiation, the envelope model, session lifecycle monotonicity, delivery and idempotency rules, transport semantics, canonical JSON mapping, registry hooks, and replay-preserving constraints.

---

## 1. Status of This Memo

This document is Draft Standards Track. Implementations MAY adopt it experimentally. Backward-incompatible changes remain possible until Final status.

---

## 2. Conventions and Terminology

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as normative requirements.

An **Agent** is any identifiable computational entity that emits and receives MACP Envelopes.

A **MACP Runtime** is the logical system responsible for enforcing session state transitions, ordering, deduplication, validation, authorization, and isolation.

A **Coordination Mode** (or **Mode**) is a semantic extension that defines how coordination unfolds inside a session.

A **Signal** is a non-binding informational message. A **Session** is a bounded coordination context. A **terminal** message is a Mode-defined message that causes a session to transition from OPEN to RESOLVED.

---

## 3. Scope and Design Goals

MACP Core exists to guarantee bounded coordination rather than generic messaging. It is designed to provide:

1. explicit coordination boundaries,
2. monotonic lifecycle transitions,
3. session isolation,
4. append-only accepted history,
5. replay-preserving structural behavior, and
6. transport independence through a canonical envelope.

MACP Core does **not** define arbitration algorithms, mode semantics, policy languages, or side-effect semantics.

---

## 4. Protocol Lifecycle and Capability Negotiation

### 4.1 Initialization

Before a client performs session-scoped operations, it MUST initialize against the runtime.

Initialization serves four purposes:

- protocol version negotiation,
- capability negotiation,
- implementation identification,
- initial discovery of supported modes and optional surfaces.

A client sends `InitializeRequest` containing:

- a set of supported protocol versions,
- client identity and implementation information,
- the client capabilities it supports.

The runtime replies with `InitializeResponse` containing:

- the selected protocol version,
- runtime identity and implementation information,
- the runtime capabilities it supports,
- optionally, a summary of supported modes,
- optionally, runtime-specific `instructions` (human-readable guidance or constraints for the client).

The `InitializeRequest` and `InitializeResponse` messages are defined in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto).

If there is no mutually supported protocol version, initialization MUST fail with `UNSUPPORTED_PROTOCOL_VERSION`.

### 4.2 Capability Objects

Capability negotiation is explicit. A side MUST NOT assume support for an optional feature unless that feature was successfully negotiated.

The initial registry of capabilities is defined in [registries/capabilities.md](../registries/capabilities.md). The most important initial capability surfaces are:

- `sessions.stream`
- `cancellation.cancelSession`
- `progress.progress`
- `manifest.getManifest`
- `modeRegistry.listModes`
- `modeRegistry.listChanged`
- `roots.listRoots`
- `roots.listChanged`
- `experimental.*`

### 4.3 Compatibility Behavior

A runtime MUST select one mutually supported protocol version. Clients SHOULD offer versions in descending order of preference. Runtimes SHOULD select the highest mutually supported version.

Unknown capabilities MUST be ignored unless they are explicitly required by local policy.

---

## 5. Coordination Model

MACP separates interaction into two planes.

### 5.1 Ambient Plane

The Ambient Plane carries Signals. Signals MAY be exchanged continuously. Signals are informational and observable but MUST NOT:

- start a session,
- mutate session state,
- change the participant set,
- resolve or expire a session.

In the base protocol, ambient Signals MUST carry an empty `session_id` and an empty `mode`. If a Signal needs to correlate with a Session, that correlation SHOULD be expressed inside `SignalPayload.correlation_session_id` or another payload-defined field rather than by making the Envelope session-scoped.

Runtimes MAY support a `WatchSignals` streaming RPC (see RFC-MACP-0006 §3.4) to broadcast accepted Signal envelopes to all subscribers in real time. Signals are ephemeral and are not required to enter durable replay history.

### 5.2 Coordination Plane

The Coordination Plane carries session-scoped messages. A session begins only when `SessionStart` is accepted. There is no implicit coordination.

All binding convergence MUST occur inside a Coordination Session.

### 5.3 Session-Scoped Communication Rule

Within an active session, compliant agents MUST NOT bypass MACP to advance session binding outcomes. If out-of-band communication influences a binding outcome, that information MUST be reintroduced into the session as an accepted Envelope before it can affect resolution.

---

## 6. Envelope Model

Every MACP message MUST be encapsulated in a canonical Envelope.

The Envelope provides:

- protocol versioning,
- session scoping,
- sender identity,
- message identity for idempotency,
- payload carriage for Core or Mode-specific content.

The canonical Protobuf definition is maintained under [`schemas/proto/macp/v1/envelope.proto`](../schemas/proto/macp/v1/envelope.proto). Core payload definitions (`SignalPayload`, `SessionStartPayload`, `SessionCancelPayload`, `CommitmentPayload`) are in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto).

For all accepted Envelopes:

- `message_type` MUST be non-empty,
- `message_id` MUST be non-empty,
- `sender` MUST be non-empty,
- `session_id` MUST be empty for ambient Signals and non-empty for session-scoped messages,
- `mode` MUST be empty for ambient Signals and non-empty for session-scoped messages,
- `sender` MUST be treated as authenticated/derived identity for session-scoped acceptance per RFC-MACP-0004, not as an untrusted self-asserted hint.

Unknown fields MUST be ignored for forward compatibility.

---

## 7. Sessions and Lifecycle

### 7.1 Session Creation

A session is created by accepting a valid `SessionStart` message.

A valid `SessionStart` MUST bind:

- `session_id`,
- Mode identifier,
- `mode_version`,
- `configuration_version`,
- `ttl_ms`,
- participant information (when used by the Mode),
- `context` when present,
- `roots` when present.

A Mode MAY also bind additional immutable authority roles through the accepted `SessionStart` sender or through mode-specific policy encoded in bound session context.

### 7.2 Session States

Core defines three states:

- `OPEN`
- `RESOLVED`
- `EXPIRED`

Sessions MUST transition monotonically. No transition from RESOLVED or EXPIRED back to OPEN is permitted.

### 7.3 Termination

A session transitions from OPEN to RESOLVED when the first Mode-defined terminal condition is accepted.

A session transitions from OPEN to EXPIRED when:

- TTL elapses,
- cancellation is accepted,
- or deterministic runtime policy requires expiration.

Any session-scoped message referencing a non-OPEN session MUST be rejected.

By default, only the accepted `SessionStart` sender (session initiator) is authorized to submit `CancelSession` for that session. Deployments MAY extend cancellation authority to additional roles through policy, but `CancelSession` MUST be subject to the same authentication and authorization requirements as any session-scoped operation.

---

## 8. Delivery, Ordering, and Idempotency

MACP assumes at-least-once delivery semantics at the transport layer.

### 8.1 Ordering

Ordering MUST be preserved within a session according to runtime acceptance order. Cross-session ordering is not guaranteed and MUST NOT be relied upon.

### 8.2 Idempotency

Runtimes MUST enforce idempotent handling of duplicates using `message_id`.

If an Envelope with a previously accepted `message_id` is received within the same session, the runtime MUST treat it as a duplicate and MUST NOT create side effects.

Duplicate `SessionStart` messages with the same `session_id` but different `message_id` MUST be rejected.

### 8.3 Accepted-History Discipline

Only **accepted session-scoped** Envelopes become part of authoritative accepted history. Ambient Signals MAY be handled ephemerally and are not required to enter durable replay history unless a deployment explicitly defines a signal-log profile.

Therefore, for any individual session-scoped Envelope:

- validation,
- authentication,
- authorization,
- deduplication,
- session-state checks,
- and Mode-specific structural validation

MUST all succeed before the Envelope is appended to accepted history or consumes durable deduplication state.

Rejected Envelopes MUST NOT:

- be appended to authoritative accepted history,
- consume `message_id` deduplication slots,
- mutate session state,
- or alter replay outcomes except through transient transport-level error reporting.

---

## 9. Transport Requirements

gRPC over HTTP/2 is the normative transport.

A compliant runtime MUST support:

- unary initialization,
- unary send/ack flow,
- bidirectional session streaming when `sessions.stream` is advertised,
- session metadata query,
- explicit session cancellation.

The canonical gRPC service definition is `MACPRuntimeService` in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto), which defines the following RPCs:

- `Initialize` — unary initialization and capability negotiation
- `Send` — unary envelope send with acknowledgement
- `StreamSession` — bidirectional session streaming
- `GetSession` — session metadata query; returns `SessionMetadata` including the current participant list and per-participant activity summaries (`ParticipantActivity`)
- `CancelSession` — explicit session cancellation
- `GetManifest` — agent or runtime manifest retrieval
- `ListModes` — mode registry query
- `WatchModeRegistry` — mode registry change notifications
- `ListRoots` — root listing
- `WatchRoots` — root change notifications
- `WatchSignals` — ambient signal observation (server streaming)

The proto file also defines extension mode lifecycle RPCs (`ListExtModes`, `RegisterExtMode`, `UnregisterExtMode`, `PromoteMode`); see [RFC-MACP-0002](RFC-MACP-0002-modes.md) for extension mode semantics.

Runtimes MAY expose additional bindings, including REST/JSON, provided the canonical Envelope and JSON mapping semantics are preserved. Standard transport bindings are defined in [RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md).

The media types `application/macp-envelope+proto` and `application/macp-envelope+json` are defined in [registries/media-types.md](../registries/media-types.md).

---

## 10. Canonical JSON Mapping

MACP defines a canonical JSON mapping for interoperability with REST gateways, debugging tools, and environments where Protocol Buffers are not available.

### 10.1 Field Mapping

| Protobuf field | JSON field | Mapping |
|----------------|-----------|---------|
| `timestamp_unix_ms` (int64) | `timestamp` | RFC3339 string (UTC recommended) |
| `payload` (bytes) | `payload` or `payload_b64` | See §10.2 |
| `mode` (string) | `mode` | Empty string for ambient Signals; non-empty for session-scoped messages |
| `session_id` (string) | `session_id` | Empty string for ambient Signals |
| All enum fields | Same name | String form of protobuf enum name |

### 10.2 Payload Encoding

A JSON-encoded Envelope MUST include exactly one of:

- `payload` — a decoded JSON object (preferred for Core payloads and human-readable messages), or
- `payload_b64` — an opaque base64-encoded string (used when the payload is binary or opaque).

### 10.3 Bytes Encoding

Protobuf `bytes` fields MUST be represented as base64-encoded strings in JSON.

### 10.4 Enum Representation

Protobuf enum values MUST be represented as their string names (for example `"SESSION_STATE_OPEN"`) in JSON, not as integer values.

### 10.5 Media Types

- `application/macp-envelope+proto` — Protocol Buffers wire format for canonical MACP envelopes
- `application/macp-envelope+json` — Canonical JSON mapping for MACP envelopes

### 10.6 Forward Compatibility

JSON consumers SHOULD ignore unrecognized fields for forward compatibility, consistent with the protobuf unknown field rule.

The JSON Schema for envelope validation is maintained at [`schemas/json/macp-envelope.schema.json`](../schemas/json/macp-envelope.schema.json).

---

## 11. Discovery, Manifests, and Registries

MACP supports runtime and agent discovery through manifests and descriptors.

A runtime that advertises `manifest.getManifest` SHOULD expose a machine-readable manifest describing:

- identity,
- supported Modes and versions,
- supported content types,
- optional transport endpoints,
- optional metadata useful for discovery.

A runtime that advertises `modeRegistry.listModes` SHOULD expose a list of Mode Descriptors.

If `listChanged` is advertised for a registry or roots surface, the runtime SHOULD provide change notifications using the negotiated transport.

The discovery and manifest model is specified in [RFC-MACP-0005](RFC-MACP-0005-discovery-and-manifests.md).

---

## 12. Error Model

Errors MUST be represented as structured error objects.

Core error codes are registered in [registries/error-codes.md](../registries/error-codes.md). Unknown error codes SHOULD be treated as implementation-defined failures.

Structural errors, including invalid session state, malformed envelopes, or authorization failures, MUST be terminal for the offending message but MUST NOT rewrite prior accepted history.

---

## 13. Security Considerations

All MACP deployments MUST use encrypted transport.

Session-scoped messages MUST be authenticated and authorized before they are accepted.

Runtimes MUST protect against:

- replay attacks,
- cross-session injection,
- resource exhaustion,
- split-brain ordering,
- tampering with append-only history.

The full security model is specified in [RFC-MACP-0004](RFC-MACP-0004-security.md).

---

## 14. Versioning and Compatibility Model

MACP uses a layered compatibility model.

- **Protocol version** is negotiated during initialization.
- **Schema namespace** preserves wire compatibility.
- **Mode version** preserves semantic compatibility.
- **Configuration and policy versions** preserve replay integrity.

Major protocol version mismatches MUST result in initialization failure.

Unknown Protobuf fields MUST be ignored. Unknown capabilities SHOULD be ignored unless required by policy. Deprecated registry entries MAY remain valid for replay long after they are no longer valid for new sessions.

---

## 15. Extension Model

MACP supports extensibility in three primary ways:

1. **Capabilities** — negotiated optional features,
2. **Modes** — semantic coordination extensions, and
3. **Registries** — stable, discoverable namespaces for identifiers and behaviors.

Extensions MUST preserve Core invariants:

- explicit session boundaries,
- monotonic lifecycle,
- append-only accepted history,
- session isolation,
- replay-preserving acceptance order.

Extensions that would invalidate these invariants are not MACP-compliant.

---

## 16. Registry Framework

MACP maintains initial registries for:

- capabilities,
- error codes,
- media types,
- standard mode identifiers,
- transport identifiers (see [registries/transports.md](../registries/transports.md)).

Registry policy and initial values are defined in the `registries/` directory.

The registry framework exists so that the core protocol remains small while the ecosystem can evolve without ad-hoc collisions.

---

## 17. IANA Considerations

MACP is an open, RFC-style community standard and does not request any IANA actions at this time.

---

## 18. References (Informative)

- Model Context Protocol, Lifecycle and Capabilities. https://spec.modelcontextprotocol.io/
- Model Context Protocol, Cancellation and Roots. https://spec.modelcontextprotocol.io/
- Agent Communication Protocol, Architecture and Agent Manifest. https://agentcommunicationprotocol.dev/

---

## Appendix A. Canonical Schemas

The canonical versioned Protobuf definitions for RFC-MACP-0001 are:

- `schemas/proto/macp/v1/envelope.proto`
- `schemas/proto/macp/v1/core.proto`

Human-friendly entrypoints are provided at:

- `schemas/envelope.proto`
- `schemas/core.proto`

The canonical JSON Schema definitions are:

- `schemas/json/macp-envelope.schema.json`
- `schemas/json/macp-agent-manifest.schema.json`
- `schemas/json/macp-mode-descriptor.schema.json`
