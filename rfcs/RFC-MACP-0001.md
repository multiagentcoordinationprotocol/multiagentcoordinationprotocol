# RFC-MACP-0001

## Multi-Agent Coordination Protocol (MACP)

**Version:** 1.0 (Draft)
**Status:** Standards Track
**Last Updated:** 2026-03-01
**Canonical Wire Format:** Protocol Buffers
**Normative Transport:** gRPC over HTTP/2
**Required JSON Mapping:** Yes
**Media Types:** `application/macp+proto`, `application/macp+json`

> This document is an independent “RFC-style” specification intended for open publication.
> It is not an IETF RFC.

---

## Abstract

The Multi-Agent Coordination Protocol (MACP) defines a **structural coordination kernel** for ecosystems of autonomous agents. MACP introduces one strict invariant:

**Binding, convergent coordination MUST occur inside explicit, bounded Coordination Sessions.**

All other interaction is treated as **ambient** and non-binding, carried via Signals.

MACP intentionally does **not** define arbitration mathematics, decision theory, governance policy, domain logic, or tool execution semantics. Those behaviors are defined by **Coordination Modes** layered above MACP Core, operating within MACP’s structural constraints.

This document specifies MACP Core: its architectural model, envelope wire format, session lifecycle state machine, delivery and idempotency requirements, transport semantics, canonical JSON mapping, error model, security requirements, and extensibility framework.

---

## Status of This Memo

This document is Draft Standards Track. Implementations MAY adopt it experimentally. Backward-incompatible changes may occur until this document reaches Final status.

---

## Table of Contents

1. Introduction
2. Conformance and Terminology
3. Design Goals and Non-Goals
4. Architectural Model
5. Core Concepts
6. Message Model
7. Coordination Session Lifecycle
8. Delivery, Ordering, Idempotency
9. Transport Requirements
10. Discovery and Capability Advertisement
11. Utilities
12. Cancellation
13. Errors
14. Security Considerations
15. Observability and Trace Propagation
16. Determinism and Replay Integrity
17. Versioning and Compatibility
18. Media Types and JSON Mapping
19. Resource Limits and Flow Control
20. Registry Framework
21. Extensibility
22. IANA Considerations
23. References
Appendix A: Protobuf Definitions
Appendix B: Canonical JSON Examples
Appendix C: Agent Manifest (Recommended)
Appendix D: Mode Descriptor (Recommended)
Appendix E: Relationship to MCP and ACP (Informative)

---

## 1. Introduction

Modern agent systems increasingly resemble **distributed ecosystems** rather than isolated model calls. Without explicit coordination boundaries, these ecosystems tend to accumulate:

* ambiguous authority (“who decides?”),
* implicit negotiation loops,
* recursive dependency graphs,
* non-reproducible outcomes,
* and “infinite chat” failure modes (unbounded conversation masquerading as coordination).

MACP addresses these failure modes with a minimal, structural separation:

* **Ambient Interaction (Signals):** always allowed; non-binding; continuous.
* **Coordinated Convergence (Sessions):** explicitly created; bounded by TTL; binding outcomes occur only here.

MACP is compatible with many topologies (one-to-many, many-to-many, quorum, delegated evaluation, hierarchical orchestration). MACP’s role is to ensure coordination remains **explicit, bounded, isolated, replayable, and structurally enforceable**.

---

## 2. Conformance and Terminology

The key words **“MUST”**, **“MUST NOT”**, **“REQUIRED”**, **“SHALL”**, **“SHALL NOT”**, **“SHOULD”**, **“SHOULD NOT”**, and **“MAY”** in this document are to be interpreted as described in BCP 14.

A MACP implementation is compliant if it satisfies all normative requirements in this document for:

* Envelope validation,
* Session lifecycle enforcement,
* Isolation guarantees,
* Delivery and idempotency behavior,
* Transport semantics,
* JSON mapping behavior (when `application/macp+json` is supported).

### 2.1 Entities

* **Agent:** An identifiable computational entity capable of sending and receiving MACP Envelopes.
* **MACP Runtime:** The logical system responsible for enforcing session state transitions, isolation, ordering, deduplication, and structural validation. The runtime may be centralized or distributed, but its behavior MUST be logically consistent with this specification.
* **Coordination Mode (Mode):** A semantic extension operating within MACP’s structural constraints that defines how coordination unfolds within a session.

### 2.2 Binding vs Non-binding

* **Non-binding:** Messages that provide information but MUST NOT change session state or create a terminal outcome (e.g., Signals).
* **Binding:** Messages that are allowed (by a Mode) to produce outcomes that terminate a session and/or constitute commitments.

MACP Core does not define domain-specific binding semantics. It only defines the structural boundary where binding is allowed: the Coordination Session.

---

## 3. Design Goals and Non-Goals

### 3.1 Design Goals

MACP is designed to provide:

1. **Explicit Coordination Boundaries**
   Coordination MUST start via `SessionStart`. There is no implicit coordination.

2. **Isolation**
   Sessions are isolated from one another. Cross-session ordering is not guaranteed.

3. **Monotonic Lifecycle**
   Sessions transition monotonically: `OPEN → (RESOLVED | EXPIRED)`.

4. **Append-only History**
   Accepted session messages are immutable and recorded append-only.

5. **Replay Integrity**
   Replaying the same accepted Envelope sequence under the same Mode and configuration versions MUST reproduce the same state transitions.

6. **Transport Independence**
   MACP defines a canonical envelope and transport requirements; it does not require a single deployment topology.

### 3.2 Non-Goals

MACP Core does **not** define:

* arbitration algorithms,
* policy languages,
* tool execution semantics,
* governance frameworks,
* “what is correct” for a given Mode.

MACP Core enforces structure; Modes define meaning.

---

## 4. Architectural Model

MACP separates interaction into two planes:

### 4.1 Ambient Plane: Signals

Agents MAY continuously exchange Signals. Signals are informational, correlate-able, and observable, but **MUST NOT**:

* start a session,
* mutate a session state,
* change session participants,
* resolve or expire a session.

Signals can be used for telemetry, observations, partial evaluations, or local state announcements.

### 4.2 Coordination Plane: Sessions

A Coordination Session is created only by `SessionStart`. Within a session, messages are:

* scoped by `session_id`,
* ordered by the runtime within that session stream,
* validated against the session lifecycle,
* recorded append-only.

**All binding convergence MUST occur within sessions.**

### 4.3 Session-Scoped Communication Rule

Within an active Coordination Session, compliant agents **MUST NOT** bypass MACP by directly invoking one another to advance session binding outcomes.

* All session-scoped coordination messages MUST flow through the MACP Runtime.
* Outside active sessions, agents MAY communicate directly or via other protocols, subject to local policy.

> Rationale: This preserves replayability, isolation, and enforceable boundaries.

---

## 5. Core Concepts

### 5.1 Envelope

Every MACP message is wrapped in an **Envelope** (Section 6). The Envelope provides:

* protocol versioning,
* session scoping,
* sender identity,
* message identity for idempotency,
* timestamp for observability,
* opaque payload bytes (Core- or Mode-defined).

### 5.2 Coordination Session

A Coordination Session is a bounded context with properties:

* unique `session_id`,
* declared `mode`,
* declared participants set (Mode-defined interpretation),
* bounded TTL,
* append-only message log,
* terminal outcome: `RESOLVED` or `EXPIRED`.

### 5.3 Coordination Mode

A Mode defines:

* allowed message types,
* participant rules,
* termination (what message ends the session),
* determinism claims,
* commitment semantics (if any),
* and any Mode-specific schemas inside `payload`.

Modes MUST NOT violate MACP Core invariants.

### 5.4 Commitment

MACP Core does not mandate a single “commitment” schema, but it defines a **recommended convention**:

* A Mode SHOULD use a terminal message type called `Commitment` (or a namespaced equivalent) to represent a binding outcome.
* A Commitment SHOULD be immutable, and SHOULD include the versions necessary for replay attribution (Mode version, policy/profile version, configuration version).

A standard optional `CommitmentPayload` is provided in Appendix A as a reusable building block.

### 5.5 Session Graph Safety (Optional)

If an implementation supports *nested* or *linked* sessions (e.g., Session A spawns Session B), it MUST enforce:

* **depth limits** (maximum nesting depth),
* **hop limits** (maximum cross-session traversals),
* and **cycle prevention** (no cyclic coordination graphs).

MACP Core does not require nested sessions, but it requires safety guardrails if they are implemented.

---

## 6. Message Model

### 6.1 Envelope Schema (Canonical Protobuf)

```protobuf
syntax = "proto3";

package macp.v1;

message Envelope {
  string macp_version = 1;        // e.g. "1.0"
  string mode = 2;                // e.g. "macp.mode.decision.v1"
  string message_type = 3;        // e.g. "SessionStart", "Signal", "Commitment"
  string message_id = 4;          // globally unique
  string session_id = 5;          // empty for ambient messages (Signals)
  string sender = 6;              // agent identifier
  int64  timestamp_unix_ms = 7;   // informational
  bytes  payload = 8;             // serialized payload (Core or Mode defined)
}
```

#### 6.1.1 Envelope Field Requirements

* `macp_version` MUST be present and MUST be compatible with this specification (Section 17).
* `mode` MUST be present for all messages.
  * For session-scoped messages, `mode` MUST be the session’s Mode identifier.
  * For Signals, `mode` SHOULD be `macp.core.signal.v1` unless an application defines a different non-session signal namespace.
* `message_type` MUST be present.
* `message_id` MUST be globally unique (Section 8).
* `session_id`:
  * MUST be empty for Signals, unless explicitly observational/correlational (Section 6.3.2).
  * MUST be non-empty for all session-scoped coordination messages.
* `sender` MUST be present and SHOULD be stable within the scope of the runtime.
* `timestamp_unix_ms` is informational. Receivers MUST NOT rely on it for ordering.
* `payload` MUST be present (may be empty) and MUST be interpretable according to `mode` and `message_type`.

Unknown Protobuf fields MUST be ignored for forward compatibility.

### 6.2 Core Message Types

MACP Core defines the following message types:

* `Signal` (ambient)
* `SessionStart` (creates a session)
* `SessionCancel` (runtime-emitted terminal annotation for cancellation; optional but RECOMMENDED)
* `Commitment` (Mode-defined terminal; recommended convention)
* `SessionEnd` (Mode-defined terminal without commitment semantics; optional convention)

Modes MAY define additional message types.

### 6.3 Core Payloads

The `payload` bytes MUST contain a serialized Protobuf message whose schema is determined by `message_type`:

* For `Signal`, payload MUST be `SignalPayload` (Appendix A).
* For `SessionStart`, payload MUST be `SessionStartPayload` (Appendix A).
* For `SessionCancel`, payload SHOULD be `SessionCancelPayload` (Appendix A).
* For Mode-defined message types, payload MUST be defined by that Mode.

#### 6.3.1 SignalPayload (Core)

Signals are non-binding ambient messages.

#### 6.3.2 Observational Signals Referencing Sessions

Signals MAY include `session_id` for correlation (e.g., “agent X observed state relevant to session S”), but:

* Signals MUST NOT change session state.
* Signals MUST NOT be used as a substitute for session-scoped messages.
* Runtimes MUST NOT treat Signals as terminal or binding.

#### 6.3.3 Optional Resource Roots

`SessionStartPayload` MAY include `roots`: a list of URI boundaries relevant to the session (e.g., repositories, datasets, API domains).

* Roots are informational to MACP Core.
* Modes MAY choose to interpret roots as binding constraints.
* Agents SHOULD respect roots when performing Mode actions.

This mirrors boundary-disclosure patterns used by other protocols (e.g., MCP “roots” for filesystem boundaries).

---

## 7. Coordination Session Lifecycle

### 7.1 Session States

MACP defines the following session states:

* **OPEN:** The session exists and accepts session-scoped messages.
* **RESOLVED:** The session has terminated via a Mode-defined terminal condition.
* **EXPIRED:** The session has terminated due to TTL elapsing or explicit cancellation.

No transition from `RESOLVED` or `EXPIRED` back to `OPEN` is permitted.

### 7.2 Session Creation

A session is created upon acceptance of a valid `SessionStart` message.

* `SessionStart` is authoritative: there is no implicit coordination and no handshake requirement at MACP Core.
* Runtimes MAY reject a `SessionStart` if it violates structural constraints (invalid TTL, invalid Envelope, unsupported mode, etc.).

### 7.3 SessionStart Requirements

A `SessionStart` message MUST include:

* a new unique `session_id`,
* a `mode` identifier,
* a `SessionStartPayload` with a TTL (bounded lifetime),
* and a globally unique `message_id`.

Duplicate SessionStart messages:

* If an identical `SessionStart` (same `message_id`) is received, it MUST be treated as a duplicate (idempotent) and MUST NOT create a second session.
* If a `SessionStart` is received for an existing `session_id` with a different `message_id`, it MUST be rejected.

### 7.4 Acceptance Rules for Session-Scoped Messages

For any Envelope with a non-empty `session_id`:

1. The session MUST exist.
2. The session MUST be `OPEN`.
3. The Envelope MUST pass validation (Section 6.1.1).
4. The Envelope MUST not be a duplicate within the session (Section 8.2).
5. The sender MUST be authorized for that session (Section 14).

If any check fails, the runtime MUST reject the message and MUST NOT create side effects.

### 7.5 Termination

A session transitions from `OPEN` to `RESOLVED` upon receipt of the first Mode-defined terminal message.

A session transitions from `OPEN` to `EXPIRED` when:

* TTL elapses, or
* explicit cancellation occurs, or
* the runtime deterministically enforces expiration due to policy/resource constraints.

A termination message received after the session is `EXPIRED` MUST be rejected and MUST NOT retroactively alter the session state.

---

## 8. Delivery, Ordering, Idempotency

### 8.1 Delivery Semantics

MACP assumes **at-least-once delivery** at the transport layer. Senders MAY retry messages on transient failures.

### 8.2 Idempotency

Runtimes MUST enforce idempotency using `message_id`:

* If an Envelope with a previously accepted `message_id` is received within the same session, it MUST be treated as a duplicate and MUST NOT produce side effects.

Runtimes SHOULD maintain a replay cache for duplicates for at least the lifetime of the session and a configurable grace period.

### 8.3 Ordering

Ordering MUST be preserved **within a session** as observed from the runtime’s accepted session log.

* In a single bidirectional stream, gRPC preserves message order; however, multiple senders may interleave. The runtime MUST define the session’s total order as the order of acceptance into the append-only log.
* Cross-session ordering is not guaranteed and MUST NOT be relied upon.

### 8.4 Exactly-Once Effects (Mode Responsibility)

MACP provides idempotent acceptance. Exactly-once *external effects* (e.g., calling tools, executing transactions) are the responsibility of the Mode and/or application, typically by:

* using Commitment messages as the sole point of effect,
* embedding external transaction IDs,
* or using saga-like compensation patterns.

---

## 9. Transport Requirements

### 9.1 Normative Transport

The normative transport is **gRPC over HTTP/2**, with support for **bidirectional streaming**.

### 9.2 Canonical gRPC Service

```protobuf
service MACPService {
  rpc SendMessage(Envelope) returns (Ack);
  rpc StreamSession(stream Envelope) returns (stream Envelope);
  rpc GetSession(SessionQuery) returns (SessionMetadata);
  rpc CancelSession(CancelSessionRequest) returns (Ack);
}
```

* `SendMessage` provides unary delivery with idempotent acknowledgement.
* `StreamSession` provides bidirectional streaming for concurrent coordination.
* `GetSession` returns session metadata including lifecycle state.
* `CancelSession` cancels a session (Section 12).

### 9.3 Streaming Requirements

Implementations MUST:

* support bidirectional streaming for coordination,
* propagate backpressure (HTTP/2 flow control),
* avoid unbounded buffering (Section 19),
* preserve per-session ordering as defined in Section 8.3.

### 9.4 Optional REST Transport

Implementations MAY expose REST endpoints for interoperability.

* REST implementations MUST use `application/macp+json` and the canonical JSON mapping (Section 18).
* Streaming over REST SHOULD use Server-Sent Events (SSE) or WebSockets.

> ACP provides an example of REST + streaming interaction patterns, including agent discovery and streamed execution over `text/event-stream`.

---

## 10. Discovery and Capability Advertisement

MACP Core does not mandate a discovery mechanism, but interoperable ecosystems benefit from being able to discover:

* available agents,
* supported Modes and Mode versions,
* transport endpoints,
* authentication requirements,
* and (optionally) Mode schemas.

### 10.1 Recommended Agent Manifest

Agents SHOULD expose a machine-readable Agent Manifest (Appendix C).

The manifest pattern is widely used in agent protocols to advertise identity, capabilities, and supported content types.

### 10.2 Recommended Mode Descriptor

Mode Providers SHOULD expose Mode Descriptors (Appendix D) describing:

* Mode identifier and versioning,
* supported message types,
* terminal message types,
* determinism claim,
* any payload schema references.

### 10.3 Capability Negotiation (Optional)

MACP implementations MAY negotiate runtime capabilities at connection time (e.g., supported MACP minor versions, max payload size, compression, supported authentication schemes).

This mirrors capability negotiation patterns common in protocols such as MCP.

### 10.4 Optional Discovery Service (Non-Normative)

To align with common “list and call” ecosystem patterns (e.g., MCP listing tools/prompts and notifying when lists change), deployments MAY define a discovery API.

A suggested shape (non-normative):

* `ListAgents` / `GetAgent` (agent catalog)
* `ListModes` / `GetMode` (mode catalog)
* `WatchRegistry` (stream changes; equivalent to “list changed” notifications)

> This section is provided as a blueprint; MACP Core does not require it.

---

## 11. Utilities

MACP Core focuses on coordination structure. However, real deployments often require small utilities for liveness and progress reporting.

### 11.1 Ping (Optional)

Implementations MAY provide a ping mechanism so either party can verify liveness.

One reference pattern is MCP’s ping request/response utility.

In MACP deployments, ping MAY be implemented via:

* standard gRPC health checking, OR
* an optional `Ping` RPC in a utility service, OR
* a `Signal` with `signal_type="ping"` and an application-level “pong”.

### 11.2 Progress Signals (Optional)

Long-running session activities often benefit from progress reporting. Implementations MAY support progress reporting via Signals.

A reference pattern is MCP’s progress notifications keyed by a progress token and optionally including `progress`, `total`, and `message`.

In MACP, progress SHOULD be modeled as a `Signal` whose `data` contains a `ProgressPayload` (Appendix A) and MAY include:

* `session_id` (correlating the progress to a session),
* and/or a target `message_id`.

Progress MUST remain non-binding and MUST NOT terminate sessions.

---

## 12. Cancellation

MACP supports cancellation at two levels:

### 12.1 Session Cancellation (Core)

Session cancellation is explicit via `CancelSession(CancelSessionRequest)`.

* Cancellation transitions the session to `EXPIRED`.
* Cancellation MUST NOT mutate prior session history.
* Cancellation MUST be idempotent per session.

If `SessionCancel` is implemented (RECOMMENDED), the runtime SHOULD emit a `SessionCancel` Envelope into the session log to make the terminal cause explicit and replayable.

### 12.2 In-Progress Operation Cancellation (Mode/Utility)

Some Modes may define long-running in-session operations. Implementations MAY support message-level cancellation by defining a Mode message type such as `CancelMessage` referencing a prior `message_id`.

As a reference pattern, MCP cancels in-progress requests via a cancellation notification that references the original request ID and includes an optional reason.

---

## 13. Errors

### 13.1 Structured Error Object

Errors MUST be represented using structured error objects.

```protobuf
message MACPError {
  string code = 1;        // stable machine-readable code
  string message = 2;     // human-readable
  string session_id = 3;  // optional
  string message_id = 4;  // optional (the message that failed)
  bytes  details = 5;     // optional, mode-specific
}
```

### 13.2 Common Error Codes

Implementations SHOULD support at least:

* `INVALID_ENVELOPE`
* `UNSUPPORTED_VERSION`
* `UNSUPPORTED_MODE`
* `INVALID_MESSAGE_TYPE`
* `DUPLICATE_MESSAGE`
* `SESSION_NOT_FOUND`
* `SESSION_NOT_OPEN`
* `SESSION_EXPIRED`
* `UNAUTHENTICATED`
* `FORBIDDEN`
* `PAYLOAD_TOO_LARGE`
* `RATE_LIMITED`
* `INTERNAL`

Modes MAY define additional namespaced error codes.

### 13.3 gRPC and HTTP Mapping

Implementations SHOULD map errors consistently to:

* gRPC status codes (`INVALID_ARGUMENT`, `NOT_FOUND`, `FAILED_PRECONDITION`, `PERMISSION_DENIED`, etc.)
* HTTP status codes when using REST (`400`, `401`, `403`, `404`, `409`, `413`, `429`, `500`).

---

## 14. Security Considerations

### 14.1 Transport Security

All MACP deployments MUST use encrypted transport (TLS).

### 14.2 Authentication and Authorization

Authentication MAY use JWT, mTLS, OAuth2/OIDC, or equivalent.

Authorization MUST be enforced **before** processing session-scoped messages. At minimum:

* the runtime MUST validate that the sender is authorized for the session,
* and MUST prevent cross-session message injection via strict validation.

### 14.3 Replay and Injection Protection

Runtimes MUST protect against replay and duplication using `message_id` deduplication (Section 8.2).

`session_id` values MUST be cryptographically strong and unguessable.

### 14.4 Denial-of-Service Mitigation

Implementations MUST defend against:

* SessionStart flooding (rate limit / admission control),
* payload amplification (size limits),
* unbounded buffering (backpressure),
* and session graph attacks if nested sessions are supported (Section 5.5).

---

## 15. Observability and Trace Propagation

Implementations SHOULD support distributed tracing.

* Trace identifiers SHOULD be propagated via gRPC metadata.
* Implementations SHOULD be compatible with W3C Trace Context and OpenTelemetry.

Trace propagation MUST NOT compromise session isolation.

---

## 16. Determinism and Replay Integrity

MACP guarantees **structural replay integrity**:

Replaying identical accepted Envelope sequences under identical:

* `macp_version`,
* Mode identifier and Mode version,
* and configuration version(s),

MUST produce identical **state transitions** (OPEN/RESOLVED/EXPIRED).

If a Mode claims determinism, it MUST specify what constitutes identical semantic outcome and which inputs are in scope (e.g., randomness sources, external I/O, time).

A Commitment (if used) SHOULD include the versions used to compute it.

---

## 17. Versioning and Compatibility

### 17.1 MACP Version

`macp_version` MUST follow semantic versioning.

* Major version mismatches MUST result in rejection.
* Minor version differences SHOULD be backward compatible.

### 17.2 Mode Version

Modes MUST include explicit version identifiers (via `mode` naming and/or payload fields).

Agents MUST reject unsupported Mode versions deterministically.

### 17.3 Forward Compatibility

Forward compatibility MUST be achieved by ignoring unknown Protobuf fields and unknown JSON properties.

---

## 18. Media Types and JSON Mapping

### 18.1 Media Types

MACP defines:

* `application/macp+proto` — Protobuf Envelope messages
* `application/macp+json` — Canonical JSON Envelope representation

### 18.2 Canonical JSON Envelope

The canonical JSON representation exists for interoperability, gateways, debugging, and REST support.

For `application/macp+json`, an Envelope MUST be represented as a JSON object with the following top-level keys:

* `macp_version` (string)
* `mode` (string)
* `message_type` (string)
* `message_id` (string)
* `session_id` (string, empty for Signals)
* `sender` (string)
* `timestamp` (ISO-8601 / RFC3339 string, UTC recommended)
* either:
  * `payload` (JSON value), OR
  * `payload_b64` (base64 string) for opaque payloads

When `payload` is used for Core payloads (SignalPayload, SessionStartPayload, SessionCancelPayload), the JSON object MUST follow the Protobuf field names, with Protobuf `bytes` fields represented as base64 strings.

> Note: MCP relies on JSON-RPC message structures and defines utilities like cancellation, progress, and capability negotiation; MACP’s JSON mapping exists primarily for gateways, debugging, and REST compatibility.

---

## 19. Resource Limits and Flow Control

Implementations MUST define and enforce:

* maximum payload size,
* maximum concurrent OPEN sessions per agent (recommended),
* maximum participant count per session (recommended),
* maximum session TTL (recommended).

Backpressure MUST propagate to senders during streaming sessions. The runtime MUST avoid unbounded buffering.

---

## 20. Registry Framework

MACP establishes a registry framework for:

* Mode identifiers and versions,
* error codes,
* media types,
* and optional utility schemas.

Mode identifiers SHOULD be namespaced (e.g., `macp.mode.decision.v1`). Experimental modes SHOULD use reverse-domain naming to prevent collision.

---

## 21. Extensibility

Future specifications MAY define:

* nested sessions and session graphs,
* quorum / voting semantics,
* routing federation,
* trust and weighting mechanisms,
* cryptographic commitments,
* cross-session references.

All extensions MUST preserve MACP Core invariants: explicit sessions, monotonic lifecycle, isolation, append-only history, and idempotent acceptance.

---

## 22. IANA Considerations

This document defines media types `application/macp+proto` and `application/macp+json`. Formal IANA registration is OPTIONAL for community deployments and MAY be pursued as MACP matures.

---

## 23. References

### 23.1 Normative References

This specification uses BCP 14 requirement keywords (MUST, SHOULD, MAY, etc.).  

### 23.2 Informative References

* **[MCP]** Model Context Protocol Specification (Version 2025-11-25): https://modelcontextprotocol.io/specification/2025-11-25/  
* **[MCP-SERVER]** MCP Server specification: https://modelcontextprotocol.io/specification/2025-11-25/server  
* **[MCP-ROOTS]** MCP Client Roots: https://modelcontextprotocol.io/specification/2025-11-25/client/roots  
* **[MCP-CANCEL]** MCP Cancellation utility: https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation  
* **[MCP-PING]** MCP Ping utility: https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/ping  
* **[MCP-PROGRESS]** MCP Progress utility: https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress  
* **[MCP-PROMPTS]** MCP Prompts: https://modelcontextprotocol.io/specification/2025-11-25/server/prompts  
* **[MCP-TOOLS]** MCP Tools: https://modelcontextprotocol.io/specification/2025-11-25/server/tools  

* **[ACP]** Agent Communication Protocol documentation: https://agentcommunicationprotocol.dev/introduction/welcome  
* **[ACP-ARCH]** ACP Architecture: https://agentcommunicationprotocol.dev/core-concepts/architecture  
* **[ACP-MANIFEST]** ACP Agent Manifest: https://agentcommunicationprotocol.dev/core-concepts/agent-manifest  
* **[ACP-OPENAPI]** ACP OpenAPI specification: https://raw.githubusercontent.com/i-am-bee/acp/main/docs/spec/openapi.yaml  

---


# Appendix A: Protobuf Definitions (MACP Core)

```protobuf
syntax = "proto3";
package macp.v1;

message Envelope {
  string macp_version = 1;
  string mode = 2;
  string message_type = 3;
  string message_id = 4;
  string session_id = 5;
  string sender = 6;
  int64 timestamp_unix_ms = 7;
  bytes payload = 8;
}

message Ack {
  bool ok = 1;
  bool duplicate = 2;
  string message_id = 3;
  string session_id = 4;
  int64 accepted_at_unix_ms = 5;
  SessionState session_state = 6;
  MACPError error = 7;
}

message MACPError {
  string code = 1;
  string message = 2;
  string session_id = 3;
  string message_id = 4;
  bytes details = 5;
}

message SignalPayload {
  string signal_type = 1;
  bytes data = 2;
  double confidence = 3;
}

message ProgressPayload {
  string progress_token = 1;     // caller-chosen token, unique among active ops
  double progress = 2;           // MUST be monotonically increasing for a token
  double total = 3;              // optional; 0 if unknown
  string message = 4;            // optional human-readable
  string target_message_id = 5;  // optional: which message/op this refers to
}

message Root {
  string uri = 1;   // absolute URI
  string name = 2;  // optional
}

message SessionStartPayload {
  string intent = 1;
  repeated string participants = 2;
  string mode_version = 3;
  string configuration_version = 4;
  int64 ttl_ms = 5;
  bytes context = 6;

  // Optional boundaries the Mode may interpret:
  repeated Root roots = 7;
}

message SessionCancelPayload {
  string reason = 1;
  string cancelled_by = 2; // identifier of actor (optional)
}

enum SessionState {
  SESSION_STATE_UNSPECIFIED = 0;
  OPEN = 1;
  RESOLVED = 2;
  EXPIRED = 3;
}

message SessionMetadata {
  string session_id = 1;
  string mode = 2;
  SessionState state = 3;
  int64 started_at_unix_ms = 4;
  int64 expires_at_unix_ms = 5;
}

message SessionQuery {
  string session_id = 1;
}

message CancelSessionRequest {
  string session_id = 1;
  string reason = 2;
}
```

### Optional (Recommended) Commitment Payload

```protobuf
message CommitmentPayload {
  string commitment_id = 1;
  string action = 2;
  string authority_scope = 3;
  string reason = 4;

  string mode_version = 5;
  string policy_version = 6;
  string configuration_version = 7;
}
```

---

# Appendix B: Canonical JSON Examples

## B.1 Signal

```json
{
  "macp_version": "1.0",
  "mode": "macp.core.signal.v1",
  "message_type": "Signal",
  "message_id": "01HV0Q1Y8J1J9Q3C2A6JH0ZP3K",
  "session_id": "",
  "sender": "agent://telemetry.observer",
  "timestamp": "2026-03-01T20:24:00Z",
  "payload": {
    "signal_type": "observation.latency",
    "data": "AAECAwQ=",
    "confidence": 0.92
  }
}
```

## B.2 SessionStart

```json
{
  "macp_version": "1.0",
  "mode": "macp.mode.decision.v1",
  "message_type": "SessionStart",
  "message_id": "01HV0Q2A9G4Z0FQ9C3Z9VZP8W1",
  "session_id": "01HV0Q2A8W0Y2XQ5N1R8Y2K9B3",
  "sender": "agent://orchestrator",
  "timestamp": "2026-03-01T20:24:01Z",
  "payload": {
    "intent": "Select a vendor for OCR pipeline",
    "participants": ["agent://orchestrator", "agent://security", "agent://finance"],
    "mode_version": "1.0.0",
    "configuration_version": "runtime-2026.03.01",
    "ttl_ms": 900000,
    "context": "eyJidWRnZXQiOiAxMDAwMH0="
  }
}
```

## B.3 SessionCancel (runtime-emitted)

```json
{
  "macp_version": "1.0",
  "mode": "macp.mode.decision.v1",
  "message_type": "SessionCancel",
  "message_id": "01HV0Q2Z3YQ2R5WZ9VQJH0D1X1",
  "session_id": "01HV0Q2A8W0Y2XQ5N1R8Y2K9B3",
  "sender": "runtime://macp.example",
  "timestamp": "2026-03-01T20:28:00Z",
  "payload": {
    "reason": "User requested cancellation",
    "cancelled_by": "user://alice"
  }
}
```

## B.4 Commitment (Mode-defined terminal)

```json
{
  "macp_version": "1.0",
  "mode": "macp.mode.decision.v1",
  "message_type": "Commitment",
  "message_id": "01HV0Q3BX2K3B4Q8J6T2K2S9M0",
  "session_id": "01HV0Q2A8W0Y2XQ5N1R8Y2K9B3",
  "sender": "agent://orchestrator",
  "timestamp": "2026-03-01T20:30:10Z",
  "payload": {
    "commitment_id": "d4f9c5c0-3c7b-4b70-9f0c-2d57f6a3b1a2",
    "action": "vendor.select",
    "authority_scope": "procurement",
    "reason": "Vendor B meets security + budget constraints",
    "mode_version": "1.0.0",
    "policy_version": "org-procurement-2026.02",
    "configuration_version": "runtime-2026.03.01"
  }
}
```

---

# Appendix C: Agent Manifest (Recommended)

Agents SHOULD expose a manifest (JSON) describing identity and capabilities.

This appendix provides a recommended shape aligned with common agent ecosystem practices (including RFC1123-like agent naming and content type declarations).

```json
{
  "agent_id": "orchestrator",
  "display_name": "Orchestrator",
  "description": "Coordinates multi-agent sessions and emits commitments.",
  "endpoints": [
    {
      "transport": "grpc",
      "uri": "dns:///macp-runtime.example.com:443"
    }
  ],
  "authentication": {
    "required": true,
    "schemes": ["mtls", "jwt"]
  },
  "supported_modes": [
    {
      "mode": "macp.mode.decision.v1",
      "versions": ["1.0.0"]
    }
  ],
  "input_content_types": ["application/macp+proto", "application/macp+json"],
  "output_content_types": ["application/macp+proto", "application/macp+json"],
  "limits": {
    "max_payload_bytes": 1048576,
    "max_open_sessions": 100
  }
}
```

---

# Appendix D: Mode Descriptor (Recommended)

```json
{
  "mode": "macp.mode.decision.v1",
  "mode_version": "1.0.0",
  "title": "Decision Mode",
  "description": "Collects proposals and produces a single binding Commitment.",
  "deterministic": true,
  "message_types": [
    "Proposal",
    "Vote",
    "Commitment"
  ],
  "terminal_message_types": [
    "Commitment"
  ],
  "schemas": {
    "Proposal": "https://example.org/schemas/mode/decision/proposal.json",
    "Vote": "https://example.org/schemas/mode/decision/vote.json",
    "Commitment": "https://example.org/schemas/mode/decision/commitment.json"
  }
}
```

---

# Appendix E: Relationship to MCP and ACP (Informative)

* **MCP** standardizes how AI applications connect to external context and capabilities using JSON-RPC, with features like prompts, tools, roots, and utilities such as cancellation/progress. MACP can be used *alongside* MCP: a Mode may coordinate when (and whether) an agent is allowed to invoke MCP tools.

* **ACP** demonstrates practical patterns for agent discovery, manifest metadata, and REST + streaming interactions (including SSE). MACP borrows the *idea* of manifests and discovery from this ecosystem, while remaining focused on session-bounded convergence rather than run execution APIs.
