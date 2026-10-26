# RFC-MACP-0001
# Multi-Agent Coordination Protocol (MACP) — Core

**Document:** RFC-MACP-0001
**Version:** 1.6.0-draft
**Status:** Community Standards Track
**Canonical wire format:** Protocol Buffers
**Normative transport:** gRPC over HTTP/2
**Required JSON mapping:** Yes
**Intended status:** Stable Core

> This is an RFC-style open standard. It is not an IETF RFC.

> **Changelog — 1.6.0-draft:** §10 now defines the JSON form of every MACP message, not only
> the Envelope: Core and Mode payloads, `MACPError`, `Ack`, and every RPC request, response
> and descriptor message. The mapping is the proto3 JSON mapping with a fixed list of
> deviations (new §10.8): original field names only, so a lowerCamelCase key is an
> unrecognized field (§10.6); 64-bit integers as JSON numbers, which decoders MUST also accept
> quoted and encoders MUST quote above 2^53−1 (§10.9); default values emitted (§10.10); and
> three structural transforms, `Envelope.timestamp`, `Envelope.payload`/`payload_b64` and
> `PolicyDescriptor.rules` as a JSON object (§10.11). New §10.12 selects the payload message by
> `(mode, message_type)`, makes `payload_b64` REQUIRED when the receiver may lack the Mode's
> schema, and rejects a JSON `payload` for a Mode the receiver has no schema for with
> `INVALID_ENVELOPE`. New §10.13 fixes how a receiver converts a JSON `payload` to Protobuf
> bytes, because those bytes are what history stores and what RFC-MACP-0013 hashes and
> receipts are computed over. New §10.14 scopes the rules to wire JSON: the conformance
> fixture format and the RFC-MACP-0013 hashing projection are separate formats. §10.1–§10.7
> keep their numbers and rules; §10.3 now points at its exceptions. Every Envelope and payload in
> `examples/*.json` and `examples/json/` already conforms. Behaviour: an implementation that emitted lowerCamelCase keys,
> or quoted 64-bit integers at or below 2^53−1, now emits non-canonical JSON, and a receiver that
> accepted a JSON `payload` for an unknown Mode now rejects it. **Replay:** no exposure for
> Protobuf-submitted envelopes. A history whose JSON payloads were converted in a different
> field order was already implementation-specific; §10.13 makes the stored bytes portable
> from here on, and replay reads stored bytes, never the original JSON.

> **Changelog — 1.5.0-draft:** §4.2's capability table gains the Decision Receipt row
> (`decision_receipt`: `get_decision_receipt`, `signed`), matching the new
> `Capabilities.decision_receipt = 8` in `core.proto` that advertises the optional
> runtime-issued receipts of RFC-MACP-0013 §13. Additive: a runtime built
> against an earlier schema leaves the field unset, which correctly reads as "not offered".
> Replay-neutral: receipts are issued after resolution and never feed session state.

> **Changelog — 1.4.0-draft:** §7.1 reserves the `configuration_version` value
> `config.default` for a Mode's default configuration profile. The runtime and both SDKs
> already defaulted to it, but no specification said so: the only statement of the value was
> `schemas/parity/contract.json`, which is non-normative and cannot be cited as a source
> (issues #136, #137). The reservation changes no accepted envelope — `configuration_version`
> stays opaque, and every other value remains implementation-defined — so it is replay-neutral.

> **Changelog — 1.3.0-draft:** New §7.6 (Acceptance obligations), and §2's definition of a
> MACP Runtime gains a sentence pointing at it. The per-envelope obligations a runtime owes
> were spread across the RFC set, and several read as properties of the gRPC server rather
> than of acceptance: the `macp_version` check (§6), session-identifier strength
> (RFC-MACP-0004 §11.2, with `INVALID_SESSION_ID` named only in the error-code registry),
> the policy/mode binding at `SessionStart` (RFC-MACP-0012 §6.1 step 5), the acceptance-time
> clock (stated only for the Handoff implicit-accept timeout, RFC-MACP-0010 §5.1), the
> synthetic `HandoffAccept` (RFC-MACP-0010 §5.1), and duplicate reporting (§8.2). A system
> that embeds a library and drives it in-process meets §2's definition, but could read those
> obligations as the server's and ship without them. §7.6 states all six once, as
> obligations of every MACP Runtime whatever its transport, and requires a library that
> offers a single-envelope acceptance entry point to perform each one or document the ones
> it leaves to its caller. Item 2 names `INVALID_SESSION_ID` as the rejection code and
> requires a runtime to document the session-identifier formats it accepts; the UUID and
> base64url forms it mentions are non-exhaustive examples of formats that meet
> RFC-MACP-0004 §11.2, not a normative format list. Item 4 governs the clock a deadline is
> checked against and leaves RFC-MACP-0003 §2's TTL base (the `SessionStart` envelope's
> `timestamp_unix_ms`) unchanged. Behaviour: each obligation already exists elsewhere in the
> RFC set or in the reference server; the new requirements are the documentation duties in
> the opening paragraph and in item 2, and item 6's requirement that a duplicate be
> distinguishable from a first acceptance. A library whose entry point adds these checks
> changes behaviour for embedders that relied on their absence, which is the intent.
> Source: seam-embedder-findings proposal S12, issue #185. **Replay:** no new exposure for a
> conformant history, because §7.6 restates obligations that already bound acceptance. A
> history produced by an implementation that skipped one of them was already non-conformant
> and can diverge on a conformant replay. For example, an embedder whose library never
> appended the synthetic `HandoffAccept` could have accepted a `HandoffDecline` after the
> implicit-accept deadline. §7.6 makes that divergence visible; it does not create it.
>
> **Changelog — 1.2.0-draft:** §7.3's `SessionCancel` terminal-annotation sentence
> and §7.5's `SessionSuspend`/`SessionResume` "accepted history" sentence each gain a
> cross-reference to RFC-MACP-0006 §3.2, which states that these internal
> annotations consume no ordinal and are not delivered on a subscribe stream.
> Clarifying prose only — no change to what a conformant runtime does (issue #159).
>
> **Changelog — 1.1.0-draft:** §6 gains a normative statement of the MACP Core protocol
> version this specification defines: `1.0`. Every Envelope example in this repository, and
> every known implementation, has sent `macp_version: "1.0"` since before this RFC existed,
> but the value was never stated as a requirement anywhere — `schemas/parity/contract.json`
> could only record it as `"source": "convention"`, not as a citation (issue #137). §6 now
> requires it: a Core-only `Initialize` exchange (§4.1) MUST negotiate
> `selected_protocol_version` to `1.0`, and every Envelope's `macp_version` field MUST equal
> `1.0` for the duration of that negotiated version. This is independent of this document's
> own `**Version:**` header above, which tracks revisions to the RFC *text* (and which this
> changelog entry is itself an instance of) — not the wire protocol version the text defines.
> No behavior changes: this pins, for the first time, the value every conformant
> implementation already sends.

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

A **MACP Runtime** is the logical system responsible for enforcing session state transitions, ordering, deduplication, validation, authorization, and isolation. A system meets this definition by what it enforces, not by the transport it exposes: a system that embeds a library implementation and drives it in-process is a MACP Runtime, and the acceptance obligations of §7.6 bind it.

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

After successful initialization, every subsequent Envelope's `macp_version` field MUST match the negotiated `selected_protocol_version`. Runtimes MUST reject envelopes with a mismatched `macp_version` with error code `UNSUPPORTED_PROTOCOL_VERSION`.

If the client requires a capability that the runtime does not advertise in `InitializeResponse.capabilities`, the client SHOULD either proceed with reduced functionality or terminate the connection. Runtimes MUST NOT fail initialization due to unknown or unsupported capabilities in the request; they MUST advertise only the capabilities they support in the response.

### 4.2 Capability Objects

Capability negotiation is explicit. A side MUST NOT assume support for an optional feature unless that feature was successfully negotiated.

Capabilities are exchanged as nested Protobuf messages defined in `core.proto`. Each capability group corresponds to a field in the `Capabilities` message:

| Capability Group | Proto Field | Key Flags | Description |
|-----------------|-------------|-----------|-------------|
| Sessions | `sessions` | `stream` | Session streaming support |
| Cancellation | `cancellation` | `cancel_session` | Explicit session cancellation |
| Progress | `progress` | `progress` | Progress notifications |
| Manifest | `manifest` | `get_manifest` | Manifest retrieval |
| Mode Registry | `mode_registry` | `list_modes`, `list_changed` | Mode discovery and change notifications |
| Roots | `roots` | `list_roots`, `list_changed` | Root listing and change notifications |
| Policy Registry | `policy_registry` | `register_policy`, `list_policies`, `list_changed`, `what_if_replay` | Governance policy lifecycle (see RFC-MACP-0012) |
| Decision Receipt | `decision_receipt` | `get_decision_receipt`, `signed` | Runtime-issued decision receipts and their verification keys (see RFC-MACP-0013 §13) |
| Experimental | `experimental` | `features` (map) | Implementation-defined experimental features |

These negotiation-time capability objects are distinct from the manifest-level capability URNs defined in `registries/capabilities.md`. Negotiation capabilities describe protocol features exchanged during `Initialize`; manifest capabilities describe agent-level feature support for discovery.

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

In the base protocol, Ambient Signals MUST carry an empty `session_id` and an empty `mode`. If a Signal needs to correlate with a Session, that correlation SHOULD be expressed inside `SignalPayload.correlation_session_id` or another payload-defined field rather than by making the Envelope session-scoped.

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

The canonical Protobuf definition is maintained under [`schemas/proto/macp/v1/envelope.proto`](../schemas/proto/macp/v1/envelope.proto). Core payload definitions (`SignalPayload`, `ProgressPayload`, `SessionStartPayload`, `SessionCancelPayload`, `SessionSuspendPayload`, `SessionResumePayload`, `CommitmentPayload`) are in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto).

For all accepted Envelopes:

- `message_type` MUST be non-empty,
- `message_id` MUST be non-empty,
- `sender` MUST be non-empty,
- `session_id` and `mode` MUST both be empty for Ambient Signals,
- `session_id` and `mode` MUST agree on `Progress`: a runtime MAY accept `Progress` either in ambient form (`session_id` and `mode` both empty) or in session-scoped form (`session_id` and `mode` both non-empty); an Envelope with exactly one of the two empty MUST be rejected. Ambient `Progress` has no payload field that correlates it to a session; `ProgressPayload.target_message_id` correlates it only to the originating message. This is a distinct rule from Signals: unlike Signals, `Progress` is not required to be ambient,
- for every other message type, `session_id` and `mode` MUST both be non-empty (session-scoped),
- `sender` MUST be treated as authenticated/derived identity for session-scoped acceptance per RFC-MACP-0004, not as an untrusted self-asserted hint.

For Mode-defined payloads, `message_type` is interpreted relative to the Envelope's `mode`: `(mode, message_type)`, not `message_type` alone, is the discriminating key for a payload's declared type, and an implementation MUST NOT assume a given `message_type` denotes the same payload type across Modes. This is not a hypothetical concern — more than one Mode already declares the same payload name (for example, `ProposalPayload` is declared by both `macp.mode.decision.v1` and `macp.mode.proposal.v1`, and `RejectPayload` is declared by both `macp.mode.proposal.v1` and `macp.mode.quorum.v1`). Core types, by contrast, are mode-independent: `Signal`, `Progress`, `SessionStart`, `SessionCancel`, `SessionSuspend`, `SessionResume`, and `Commitment` each denote one payload type regardless of the Envelope's `mode`, corresponding one-to-one with the Core payload definitions listed above. This scopes the *interpretation* of `message_type` for Mode-defined payloads; it does not qualify the Core types. Per the rule above, `mode` MUST be empty for Ambient Signals, so such a Signal remains fully identified by `message_type` alone, with no `mode` to pair it with. Neither mode-independent types nor empty-`mode` Signals are made non-conforming by this rule. This clarifies how an existing discriminator is scoped; it does not establish a message-type registry.

The `cancelled_by` field in `SessionCancelPayload` is set by the runtime and MUST match the authenticated `sender` of the originating `CancelSession` RPC. It is not a self-asserted claim.

Unknown fields MUST be ignored for forward compatibility.

The MACP Core protocol version defined by this specification is `1.0`. A Core-only `Initialize` exchange (§4.1) MUST negotiate `selected_protocol_version` to `1.0`, and every Envelope's `macp_version` field MUST equal `1.0` for the duration of that negotiated version, per §4.1's match requirement. This wire protocol version is distinct from this document's own `**Version:**` header above, which tracks revisions to the RFC text, not the protocol it defines. A future breaking revision of MACP Core defines its own `macp_version` literal under the versioning model in §14; this pin is scoped to the protocol as currently specified by this RFC.

---

## 7. Sessions and Lifecycle

### 7.1 Session Creation

A session is created by accepting a valid `SessionStart` message.

A valid `SessionStart` message consists of an Envelope with a non-empty `session_id`, a non-empty `mode` field (the Mode identifier), and a non-empty `sender`, combined with a `SessionStartPayload` that MUST bind:

- `intent` (MAY be empty; descriptive only — see below),
- `mode_version`,
- `configuration_version`,
- `ttl_ms` (MUST be greater than zero),
- `participants` (when required by the Mode),
- `policy_version` (MUST be present in the payload; MAY be empty, in which case the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
- `max_suspend_ms` when present (0 or absent means the runtime's configured default; the runtime MUST record the *resolved* cap on the session — see §7.5 and RFC-MACP-0003 §2),
- `roots` when present,
- `context_id` when present (see §7.4.1),
- `extensions` when present (see §7.4.2).

`configuration_version` is an opaque string that identifies a mode-specific configuration profile. Its format and interpretation are implementation-defined and not part of the MACP interoperability contract. Runtimes MUST store the bound `configuration_version` in session metadata for replay integrity.

The `configuration_version` value `config.default` is reserved: it names the Mode's default configuration profile, with no mode-specific overrides. A client or SDK that binds no specific configuration profile SHOULD bind `config.default`, and a runtime MUST accept `config.default` for every Mode it implements. A runtime MUST NOT give `config.default` a meaning other than that Mode's default profile. No other `configuration_version` value is reserved.

`intent` is a human-readable description of why the session was opened. It MAY be empty, and a runtime MUST NOT reject a `SessionStart` solely because `intent` is empty. When present, a runtime MUST preserve it verbatim and MUST NOT modify it after the `SessionStart` is accepted — like the other bound values, it is immutable for the life of the session.

`intent` is descriptive only. It MUST NOT influence acceptance decisions, Mode semantics, or policy evaluation, and it is therefore outside the determinism boundary of RFC-MACP-0003 Section 3: two sessions differing only in `intent` MUST produce identical state transitions. Note that `intent` is not carried on `SessionMetadata`, so it is not returned by `GetSession`; consumers that need it read it from the accepted `SessionStart` envelope in session history.

A Mode MAY also bind additional immutable authority roles through the accepted `SessionStart` sender or through mode-specific policy encoded in bound session context.

### 7.2 Session States

Core defines five states:

- `OPEN`
- `SUSPENDED` — non-terminal pause of an `OPEN` session (see §7.5)
- `RESOLVED` — terminal
- `EXPIRED` — terminal
- `CANCELLED` — terminal

`RESOLVED`, `EXPIRED`, and `CANCELLED` are terminal. Sessions MUST transition monotonically with respect to termination: once a session is terminal, no further transition is permitted (in particular, no transition back to `OPEN` or `SUSPENDED`).

`SUSPENDED` is a non-terminal pause of an `OPEN` session. The complete set of permitted transitions is:

- `OPEN → SUSPENDED` and `SUSPENDED → OPEN` — suspend / resume (§7.5),
- `OPEN → RESOLVED` — the first Mode-defined terminal condition is accepted (§7.3),
- `OPEN → EXPIRED` — TTL elapses or deterministic runtime policy requires expiration (§7.3),
- `SUSPENDED → EXPIRED` — the suspended session's banked TTL elapses or `MAX_SUSPEND_MS` is exceeded (§7.5),
- `OPEN → CANCELLED` and `SUSPENDED → CANCELLED` — a `CancelSession` request is accepted (§7.3).

A commitment (the Mode terminal condition) MUST be emitted only from `OPEN`. Therefore `SUSPENDED → RESOLVED` is NOT permitted: a session MUST be resumed to `OPEN` before it can resolve. No transition out of a terminal state is permitted.

> **Breaking change (v1.0.0-draft):** Two states were added to the lifecycle — `SUSPENDED` (§7.5) and `CANCELLED` — and cancellation now terminates a session as `CANCELLED` rather than `EXPIRED`. This is a wire- and behavior-breaking change to the session state machine; runtimes and observers MUST handle the new `SessionState`/`SessionLifecycleEvent` values. No backward-compatibility shim is provided.

### 7.3 Termination

A session transitions from OPEN to RESOLVED when the first Mode-defined terminal condition is accepted. The runtime MUST process terminal messages in the following order:

1. Verify that the session is in OPEN state (reject otherwise).
2. Validate the message (authentication, authorization, Mode-specific rules, policy rules).
3. Accept the message into the session's append-only history.
4. Transition the session state from OPEN to RESOLVED.
5. Reject any subsequent session-scoped messages for this session with a non-OPEN session error.

A session transitions from OPEN to EXPIRED when:

- TTL elapses (including a suspended session's banked TTL, §7.5), or
- deterministic runtime policy requires expiration.

A session transitions to CANCELLED (from OPEN or SUSPENDED) when a `CancelSession` request is accepted. `CANCELLED` is a distinct terminal state from `EXPIRED`, so observers can tell an explicit cancellation apart from TTL/policy expiry.

Any session-scoped message referencing a non-OPEN session MUST be rejected.

By default, only the accepted `SessionStart` sender (session initiator) is authorized to submit `CancelSession` for that session. The runtime MUST record the initiator in `SessionMetadata.initiator` at session creation time for authorization checks. Deployments MAY extend cancellation authority to additional roles through policy. `CancelSession` MUST be subject to the same authentication requirements as any session-scoped operation.

`CancelSession` is the client-facing RPC. Upon accepting a `CancelSession` request, the runtime MUST transition the session to CANCELLED and append a `SessionCancel` envelope (with `SessionCancelPayload`) to the session's accepted history as a terminal annotation (as an internal annotation: it consumes no ordinal and is not delivered on a subscribe stream, see RFC-MACP-0006 §3.2). `SessionCancel` envelopes MUST NOT be submitted directly via the `Send` RPC; the runtime is the sole emitter.

`CancelSession` is a Core control-plane message. Mode-specific authorization rules (e.g., who can emit which Mode message type) do NOT apply to `CancelSession`. Only the initiator and policy-delegated roles may cancel a session.

#### 7.3.1 Commitment Supersession

`CommitmentPayload` MAY carry a `supersedes` field (`CommitmentRef { session_id, commitment_hash }`) indicating that this commitment revises an earlier one. Because a `RESOLVED` session accepts no further session-scoped messages (step 5 above), a superseding commitment cannot live in the same session as the commitment it supersedes: it is emitted in a **new** session whose `supersedes` reference points back at the earlier commitment. Supersession is therefore inherently **cross-session**.

The runtime's structural obligations are limited to: (a) if `supersedes` is present, its fields MUST be well-formed — non-empty `session_id`, and a `commitment_hash` that is a syntactically valid canonical commitment hash (RFC-MACP-0013: `sha256:` followed by 64 lowercase hex characters); and (b) the superseding party MUST be authorized in the new session under the normal authority rules. The runtime MUST NOT, as a Core obligation, resolve the reference, verify that the referenced commitment exists, was sealed, or is unforked, or decide whether the supersession is *permitted* — those are cross-session concerns. Chain resolution ("the current commitment for this matter"), supersession policy, and fork handling (whether two live successors to one commitment are allowed) are consumer governance built above Core, which MAY maintain a cross-session commitment index for the purpose. A consumer that does not use supersession is unaffected; the field is simply absent.

### 7.4 Session Context and Extensions

#### 7.4.1 Context Reference

`SessionStartPayload` MAY carry a `context_id` string field naming the structured context this session operates within (e.g., a content-addressed context identifier, a knowledge-base URI, or any opaque reference).

The runtime MUST preserve `context_id` on `SessionMetadata` for the session's lifetime. The runtime MUST NOT interpret, resolve, or validate the value — it is an opaque reference whose semantics are defined by the context protocol in use (e.g., CTXM).

Observers (including control-planes and UIs) MAY use `context_id` for indexing, linking, and display without parsing extension-specific data.

#### 7.4.2 Extension Blocks

`SessionStartPayload` MAY carry a `map<string, bytes> extensions` field containing protocol-specific extension blocks keyed by a globally unique protocol identifier (e.g., `"ctxm"`, `"aitp"`, deployment-specific names).

**Preservation rule (MUST):** The runtime MUST preserve all extension entries in the session's metadata for the session's lifetime.

**Non-dependence rule (MUST):** Core session lifecycle (creation, mode message routing, terminal transitions, cancellation, TTL expiry, deduplication, policy evaluation) MUST NOT depend on any extension block or on `context_id`. A session with empty `context_id` and empty `extensions` MUST behave identically to one with both populated, from the perspective of core protocol mechanics.

**Forward compatibility (MUST):** Runtimes MUST NOT reject a `SessionStart` because it contains unknown extension keys or an unrecognized `context_id` format.

**Extension provider hooks (MAY):** Runtimes MAY register extension providers that receive lifecycle callbacks (session-start, mode-event, session-terminal) for their declared key. Provider errors MUST NOT cause session-lifecycle failures; they SHOULD be logged and MAY be surfaced as ambient `Signal` envelopes for observability.

**Naming convention (RECOMMENDED):** Extension keys SHOULD use dot-separated reverse-domain notation for public protocols (e.g., `ctxm.v1`, `aitp.v1`) and `x-` prefix for deployment-private extensions (e.g., `x-billing`, `x-tracing`).

> **Migration note:** The former opaque `bytes context` field (field 7) has been removed from `SessionStartPayload`. It is superseded by the structured `context_id` (field 8) and `extensions` (field 9) fields. The `roots` field has been renumbered from field 8 to field 7.

### 7.5 Suspension and Resume

An `OPEN` session MAY be paused into the `SUSPENDED` state and later resumed to `OPEN`. Suspension is the Core mechanism behind human-in-the-loop and operational holds: a session that is paused for review MUST replay identically for every consumer.

**Control-plane RPCs.** `SuspendSession` and `ResumeSession` are Core control-plane RPCs, symmetric with `CancelSession`:

- `SuspendSession` is accepted only when the session is `OPEN`; it transitions the session to `SUSPENDED`.
- `ResumeSession` is accepted only when the session is `SUSPENDED`; it transitions the session back to `OPEN`.

Like `CancelSession`, they are restricted to the session initiator and policy-delegated roles, are subject to the same authentication requirements, and are NOT governed by Mode-specific authorization rules. Upon accepting a `SuspendSession` request the runtime MUST append a `SessionSuspend` envelope (with `SessionSuspendPayload`); upon accepting a `ResumeSession` request it MUST append a `SessionResume` envelope (with `SessionResumePayload`). These envelopes MUST NOT be submitted via the `Send` RPC — the runtime is the sole emitter — and they enter the accepted history so the suspension timeline is part of the replayed record (as internal annotations: they consume no ordinal and are not delivered on a subscribe stream, see RFC-MACP-0006 §3.2).

**Acceptance while suspended.** A `SUSPENDED` session is not `OPEN`; therefore any session-scoped Mode message (Proposal, Vote, Commitment, …) referencing it MUST be rejected with a non-OPEN session error, exactly as for terminal sessions (§7.3). Only `ResumeSession` (and `CancelSession`) may be accepted against a `SUSPENDED` session.

**Pausable TTL.** The session's absolute deadline is banked across suspension rather than continuing to run. On suspend, the runtime records the remaining time `banked = deadline − suspend_time`; on resume, it sets `deadline = resume_time + banked` (the resume's `banked_ms` records this value for replay). A `SUSPENDED` session MUST NOT expire on its pre-suspension deadline. To bound indefinite pauses, a runtime MUST enforce a maximum-suspension cap: if the cumulative suspended duration exceeds the cap, the session transitions `SUSPENDED → EXPIRED`. The cap is **session-bound**: it is resolved at `SessionStart` from `SessionStartPayload.max_suspend_ms` (0 or absent selects the runtime's configured default) and the resolved value MUST be recorded on the session, exactly like `ttl_ms`. Replay MUST use the recorded cap, never live runtime configuration — otherwise two runtimes (or one runtime reconfigured) would produce different terminal states on identical history. TTL accounting under suspension is normatively deterministic — see RFC-MACP-0003 §2.


### 7.6 Acceptance obligations

The obligations in this section bind every MACP Runtime, whatever its transport, including a runtime that embeds a library implementation and has no `MACPRuntimeService` endpoint. A library that offers a single-envelope acceptance entry point SHOULD perform each of them, and MUST document each one it leaves to its caller.

1. **Version.** An envelope whose `macp_version` is not a version the runtime supports (the negotiated version, where `Initialize` applies) MUST be rejected with `UNSUPPORTED_PROTOCOL_VERSION`.
2. **Session identifier.** A `SessionStart` whose `session_id` does not meet RFC-MACP-0004 §11.2 MUST be rejected with `INVALID_SESSION_ID`. A runtime MUST document the formats it accepts. As non-exhaustive examples, a UUID v4 or v7 in lowercase hyphenated form, or a base64url token of at least 22 characters, meets RFC-MACP-0004 §11.2. These examples are illustrative: they are not a normative list of accepted formats, and a runtime MAY accept other formats that meet RFC-MACP-0004 §11.2.
3. **Policy binding.** RFC-MACP-0012 §6.1 applies at every `SessionStart`, including step 5 (mode mismatch, rejected with `INVALID_POLICY_DEFINITION`).
4. **Acceptance time.** Every time-dependent rule, including TTL (§7.1), suspension banking (§7.5) and Mode timeouts such as RFC-MACP-0010 §5.1, MUST be evaluated against the runtime's recorded acceptance time. It MUST NOT be evaluated against `Envelope.timestamp_unix_ms`. The runtime MUST record the acceptance time with the accepted envelope so that replay reproduces it. This item governs the clock against which a deadline is checked. It does not move a deadline's base where another section fixes it: RFC-MACP-0003 §2 makes the accepted `SessionStart` envelope's `timestamp_unix_ms` the base of the initial TTL deadline, and that rule stands. The runtime-emitted `SessionSuspend` and `SessionResume` annotations carry the runtime's own clock, so the suspension accounting of RFC-MACP-0003 §2 already meets this item.
5. **Due synthetic envelopes.** Before evaluating a session-scoped envelope, the runtime MUST append every synthetic envelope that a Mode specifies as due at that acceptance time, such as the synthetic `HandoffAccept` of RFC-MACP-0010 §5.1. Observation at evaluation time is sufficient. A timer or sweep is RECOMMENDED but not required.
6. **Duplicates.** A duplicate (§8.2) MUST be reported to the submitter distinctly from a first acceptance and from every other rejection, either as `DUPLICATE_MESSAGE` or as an idempotent success that the submitter can recognise as a replay. This lets a caller tell a retried submission from a new one.

---

## 8. Delivery, Ordering, and Idempotency

MACP assumes at-least-once delivery semantics at the transport layer.

### 8.1 Ordering

Ordering MUST be preserved within a session according to runtime acceptance order. Cross-session ordering is not guaranteed and MUST NOT be relied upon.

For bidirectional streaming (`StreamSession`), acceptance order is defined as the order in which the runtime completes validation and appends messages to accepted history. Runtimes MUST serialize message acceptance within a single session — no parallel processing of session-scoped messages within one session is permitted.

### 8.2 Idempotency

Runtimes MUST enforce idempotent handling of duplicates using `message_id`.

If an Envelope with a previously accepted `message_id` is received within the same session, the runtime MUST treat it as a duplicate and MUST NOT create side effects.

If a `SessionStart` is received for a `session_id` that already has an accepted `SessionStart`, the runtime MUST reject the new message with error code `SESSION_ALREADY_EXISTS`, regardless of `message_id`. This is a session-existence check, not a duplicate-detection check.

### 8.3 Accepted-History Discipline

Only **accepted session-scoped** Envelopes become part of authoritative accepted history. Ambient Signals MAY be handled ephemerally and are not required to enter durable replay history unless a deployment explicitly defines a signal-log profile.

Ambient Signals carry a `message_id` for traceability but do NOT consume session-scoped deduplication slots. Runtimes MAY optionally deduplicate Signals by `message_id` if a deployment tracks them, but this is not required. Duplicate Signals MUST NOT mutate session state regardless of deduplication behavior.

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

If a `StreamSession` receives an invalid or unauthorized envelope, the runtime MUST respond with a `StreamSessionResponse` containing an `MACPError` on the same stream rather than terminating the stream. Stream termination is reserved for transport-level failures, not application-level validation errors.

- `GetSession` — session metadata query; returns `SessionMetadata` including the current participant list and per-participant activity summaries (`ParticipantActivity`)
- `CancelSession` — explicit session cancellation
- `GetManifest` — agent or runtime manifest retrieval
- `ListModes` — mode registry query
- `WatchModeRegistry` — mode registry change notifications
- `ListRoots` — root listing
- `WatchRoots` — root change notifications
- `WatchSignals` — server-streaming RPC that broadcasts accepted Ambient Signal Envelopes in real time. The stream carries only Signals (messages with empty `session_id` and empty `mode`). Signals are ephemeral; there is no built-in backlog or resume mechanism. Clients that disconnect MAY miss Signals.
- `ListSessions` — returns a bounded page of `SessionMetadata` for the sessions the runtime currently knows about, active and terminal. The listing is paginated: `page_size` bounds the page (0 selects a server-chosen default, and the runtime MAY cap the requested value), `page_token` continues a traversal, and the result set is complete only once `next_page_token` comes back empty — a short page does not signal completion. Advertised by `sessions.list_sessions`. See [RFC-MACP-0006 Section 3.8](RFC-MACP-0006-transport-bindings.md#38-session-lifecycle-observation-rpcs) for the full contract.
- `WatchSessions` — server-streaming RPC that emits `SessionLifecycleEvent` notifications when sessions are created, resolved, or expired. Advertised by `sessions.watch_sessions`.

The proto file also defines extension mode lifecycle RPCs (`ListExtModes`, `RegisterExtMode`, `UnregisterExtMode`, `PromoteMode`); see [RFC-MACP-0002](RFC-MACP-0002-modes.md) for extension mode semantics.

Runtimes MAY expose additional bindings, including REST/JSON, provided the canonical Envelope and JSON mapping semantics are preserved. Standard transport bindings are defined in [RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md).

The media types `application/macp-envelope+proto` and `application/macp-envelope+json` are defined in [registries/media-types.md](../registries/media-types.md).

---

## 10. Canonical JSON Mapping

MACP defines a canonical JSON mapping for interoperability with REST gateways, debugging tools, and environments where Protocol Buffers are not available.

The mapping covers every MACP message: the Envelope, every Core and Mode payload, `MACPError`, `Ack`, and every request, response and descriptor message in the canonical schemas (`schemas/proto/macp/`). §10.1–§10.7 state the Envelope-level rules; §10.8–§10.14 extend them to every message as the proto3 JSON mapping with a fixed list of deviations.

### 10.1 Field Mapping

| Protobuf field | JSON field | Mapping |
|----------------|-----------|---------|
| `timestamp_unix_ms` (int64) | `timestamp` | RFC3339 string (UTC recommended) |
| `payload` (bytes) | `payload` or `payload_b64` | See §10.2 |
| `mode` (string) | `mode` | Empty string for Ambient Signals; empty or non-empty for `Progress` per §6; non-empty for all other message types |
| `session_id` (string) | `session_id` | Empty string for Ambient Signals; empty or non-empty for `Progress` per §6; non-empty for all other message types |
| All enum fields | Same name | String form of protobuf enum name |

**Normative mapping rule:** In the canonical JSON form, the Protobuf field `timestamp_unix_ms` (int64, milliseconds since Unix epoch) is **renamed** to `timestamp` and **converted** to an RFC 3339 string. Encoders MUST perform this conversion when producing JSON. Decoders MUST convert `timestamp` back to `timestamp_unix_ms` when producing Protobuf. This is the only Protobuf-to-JSON field rename in the MACP envelope.

### 10.2 Payload Encoding

A JSON-encoded Envelope MUST include exactly one of:

- `payload` — a decoded JSON object (preferred for Core payloads and human-readable messages), or
- `payload_b64` — an opaque base64-encoded string (used when the payload is binary or opaque).

### 10.3 Bytes Encoding

Protobuf `bytes` fields MUST be represented as base64-encoded strings in JSON. The only exception is `Envelope.payload`, whose JSON form §10.2 and §10.12 define; this rule applies to every other `bytes` field in every message, including `map<string, bytes>` values such as `SessionStartPayload.extensions`. Encoders MUST use the standard alphabet with padding (RFC 4648 §4); decoders MUST also accept the URL-safe alphabet and unpadded input, as the proto3 JSON mapping does.

### 10.4 Enum Representation

Protobuf enum values MUST be represented as their string names (for example `"SESSION_STATE_OPEN"`) in JSON, not as integer values.

### 10.5 Media Types

- `application/macp-envelope+proto` — Protocol Buffers wire format for canonical MACP envelopes
- `application/macp-envelope+json` — Canonical JSON mapping for MACP envelopes

### 10.6 Forward Compatibility

JSON consumers MUST ignore unrecognized fields for forward compatibility, consistent with the protobuf unknown field rule. The canonical JSON Schema (`schemas/json/macp-envelope.schema.json`) is provided for strict validation contexts (e.g., conformance testing); production consumers MUST be lenient and accept envelopes containing unrecognized fields.

The JSON Schema for envelope validation is maintained at [`schemas/json/macp-envelope.schema.json`](../schemas/json/macp-envelope.schema.json).

### 10.7 Empty String Representation

In the canonical JSON mapping, empty Protobuf string fields MUST be represented as `""` (the empty string literal), not as JSON `null` and not omitted from the object. This applies to `session_id`, `mode`, and all other string fields.

Decoders MUST treat a missing string field as equivalent to `""` for backward compatibility.

Encoders SHOULD always include `session_id` and `mode` fields in the JSON object, even when empty.

### 10.8 Base Mapping and Fixed Deviations

The JSON form of any MACP message is the proto3 JSON mapping of that message ([Protocol Buffers, "ProtoJSON Format"](https://protobuf.dev/programming-guides/json/)), with exactly the deviations listed in this subsection and detailed in §10.9–§10.11. Anything this section does not change follows the proto3 JSON mapping: a message is a JSON object, a `repeated` field is a JSON array, a `map` is a JSON object keyed by the map key's string form, a `bool` is `true` or `false`, a `double` or `float` is a JSON number (or the strings `"NaN"`, `"Infinity"`, `"-Infinity"`), a 32-bit integer is a JSON number, and an enum is its value name (§10.4).

The deviations are:

1. **Original field names only.** Encoders MUST use each field's name exactly as written in the `.proto` file (`session_id`, `ttl_ms`, `accepted_at_unix_ms`). The proto3 mapping's lowerCamelCase `json_name` is not a MACP field name: a decoder MUST NOT map `sessionId` to `session_id`, and treats such a key as an unrecognized field, ignored under §10.6. An Envelope sent with `sessionId` therefore has an empty `session_id` and fails the validation of §6 and §7.6 like any other Envelope missing that field. `timestamp` is the one renamed field (§10.1, §10.11).
2. **64-bit integers as JSON numbers** (§10.9), where proto3 JSON uses quoted strings.
3. **Default values emitted** (§10.10), where proto3 JSON omits them.
4. **Three structural transforms** (§10.11): `Envelope.timestamp`, `Envelope.payload`/`payload_b64`, and `PolicyDescriptor.rules`.
5. **Unrecognized fields ignored** (§10.6), where a strict proto3 JSON parser rejects them.

No other deviation exists. A future one is a change to this RFC.

### 10.9 64-bit Integers

Fields of type `int64` and `uint64` MUST be encoded as JSON numbers, not strings. Decoders MUST also accept the quoted decimal string form (`"900000"`), which is what a stock proto3 JSON encoder emits, and treat it as the same value.

A JSON number is exact only up to 2^53−1 in IEEE 754 double-precision, which is how many JSON implementations hold numbers. An encoder MUST therefore quote any 64-bit value above 2^53−1 (or below −(2^53−1)), and a decoder that cannot represent such a number exactly MUST NOT silently round it.

Every 64-bit field MACP defines today stays below 2^53 in practice, so a conforming encoder emits all of them as plain numbers: the `*_unix_ms` timestamps (`Ack.accepted_at_unix_ms`, `PolicyDescriptor.registered_at_unix_ms`, `SessionMetadata.started_at_unix_ms` and `expires_at_unix_ms`, `TaskRequestPayload.deadline_unix_ms`, and the other `*_at_unix_ms` fields of the canonical schemas), the durations `ttl_ms`, `max_suspend_ms` and `banked_ms`, and the ordinals `after_sequence`, `history_index`, `resolved_by_history_index` and `first_divergence`. A field added later inherits this rule.

### 10.10 Default Values and Presence

Encoders SHOULD emit every field whose value is the proto3 default: `""` for strings, `0` for numbers, `false` for `bool`, the zero-valued name (for example `"SESSION_STATE_UNSPECIFIED"`) for enums, `[]` for `repeated` fields and `{}` for maps. Empty strings MUST be `""`, never `null` and never omitted (§10.7). A field with explicit presence — a message-typed field, a `proto3 optional` field such as `WhatIfReplayResponse.first_divergence`, or a member of a `oneof` — is emitted when it is set, including when it is set to its default value, and omitted when it is unset.

Decoders MUST treat an absent field as its default value (or, for a field with explicit presence, as unset), and MUST treat a JSON `null` the same way, as the proto3 JSON mapping does.

### 10.11 Structural Transforms

Three fields do not map one-to-one, and these are the only ones:

1. **`Envelope.timestamp_unix_ms` → `timestamp`.** The Envelope field is renamed and carried as an RFC 3339 string (§10.1). The transform applies to the Envelope only: `Ack.accepted_at_unix_ms` and every other `*_unix_ms` field keep their names and stay JSON numbers (§10.9). Decoders MUST accept any RFC 3339 offset and fractional seconds, converting to milliseconds since the Unix epoch and truncating digits below the millisecond; encoders SHOULD emit UTC (`Z`).
2. **`Envelope.payload` → `payload` or `payload_b64`.** The `bytes` field becomes either a JSON object, the JSON form of the payload message, or a base64 string of the payload bytes (§10.2). §10.12 says which message a JSON `payload` is and when `payload_b64` is required.
3. **`PolicyDescriptor.rules` as a JSON object.** In Protobuf, `rules` is a `string` holding JSON text ([RFC-MACP-0012](RFC-MACP-0012-policy.md)). In the canonical JSON mapping it is that JSON object, inlined, as [`schemas/json/macp-policy-descriptor.schema.json`](../schemas/json/macp-policy-descriptor.schema.json) requires. Encoders MUST emit the object. Decoders MUST also accept the string form (a JSON string whose content is the rules object's JSON text) and treat it as the same rules. A decoder converting to Protobuf serializes the object back to JSON text; RFC-MACP-0012 defines rules by their parsed content, so that text's whitespace and member order carry no meaning.

All other `bytes` fields stay base64 strings (§10.3), including `MACPError.details`, `SignalPayload.data`, every Mode payload's opaque `bytes` field and `SessionStartPayload.extensions` values.

### 10.12 Payload Selection

A JSON `payload` is the JSON form (§10.8) of the payload message selected by the Envelope's `(mode, message_type)`:

- A Core message type (`Signal`, `Progress`, `SessionStart`, `SessionCancel`, `SessionSuspend`, `SessionResume`) selects its Core payload in [`core.proto`](../schemas/proto/macp/v1/core.proto) (`SignalPayload`, `ProgressPayload`, and so on) whatever the `mode`. `Commitment` selects `CommitmentPayload`.
- Any other `message_type` selects the payload message the Mode named by `mode` declares for it ([RFC-MACP-0002](RFC-MACP-0002-modes.md)). The same `message_type` can denote different messages in different Modes, so a decoder MUST select by the pair, never by `message_type` alone.

`payload_b64` carries the payload bytes as they are, and is always permitted. It is REQUIRED when the sender cannot assume the receiver has the Mode's payload schema, for example an `ext.*` or other extension Mode registered dynamically ([RFC-MACP-0002](RFC-MACP-0002-modes.md)). A receiver given a JSON `payload` for a `(mode, message_type)` it has no payload schema for MUST reject the Envelope with `INVALID_ENVELOPE` ([registries/error-codes.md](../registries/error-codes.md)), because it cannot convert the payload to the bytes it would accept.

### 10.13 Deterministic Conversion

A receiver that accepts an Envelope whose payload arrived as JSON `payload` converts it to Protobuf bytes, and those bytes are the payload of the accepted Envelope. Accepted history stores them (§8.3), replay reads them ([RFC-MACP-0003](RFC-MACP-0003-determinism.md)), the commitment hash is computed over the `CommitmentPayload` they decode to ([RFC-MACP-0013](RFC-MACP-0013-commitment-hash.md)), and a runtime-issued receipt's `commitment_wire_b64` is these bytes verbatim (RFC-MACP-0013 §13, requirement 4). Two conforming receivers MUST therefore produce the same bytes from the same JSON `payload`. The conversion MUST:

1. emit fields in ascending field-number order;
2. omit every field whose value is the proto3 default, unless the field has explicit presence and is set (§10.10);
3. omit every unrecognized JSON member (§10.6), so that no unknown field reaches the bytes;
4. encode `repeated` scalar numeric fields packed, as proto3 does by default;
5. emit `map` entries in ascending order of their key's UTF-8 bytes, each entry with its key before its value; and
6. apply the decoding rules of §10.3 and §10.9–§10.11 (base64 alphabets, quoted 64-bit integers, `rules` string form) before encoding, so that equivalent JSON yields identical bytes.

This is the deterministic Protobuf serialization of the decoded message, and is what common Protobuf libraries produce in their deterministic mode. A client that needs control of the exact bytes, for example one that must keep a field this receiver does not know or one that pre-computes a commitment hash over its own encoding, MUST send `payload_b64` instead.

### 10.14 Scope

§10 governs JSON on the wire: an Envelope or any other MACP message carried as JSON by a transport binding ([RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md), [RFC-MACP-0014](RFC-MACP-0014-a2a-binding.md)), or served as a discovery document ([RFC-MACP-0005](RFC-MACP-0005-discovery-and-manifests.md)). It does not govern:

- the conformance fixture format ([`schemas/conformance/schema.json`](../schemas/conformance/schema.json)), a test-harness format with its own conventions (for example, empty `bytes` written as `[]`);
- the hashing projection of RFC-MACP-0013 §3 or the `macp-receipt/1` receipt body of its Appendix A, JSON documents that RFC defines on its own terms, and which §10.6 does not reach (RFC-MACP-0013 §5).

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

Ambient Signals SHOULD be authenticated using the same mechanisms as session-scoped messages. Runtimes MAY accept unauthenticated Signals but MUST document this as a deployment-specific policy. Unauthenticated Signals MUST NOT be trusted for operational decisions or forwarded to `WatchSignals` subscribers without annotation.

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
- monotonic lifecycle — terminal states (`RESOLVED`, `EXPIRED`, `CANCELLED`) are final; the non-terminal `OPEN`↔`SUSPENDED` pause (§7.5) does not violate this,
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
- policies (see [registries/policies.md](../registries/policies.md)),
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
- `schemas/json/macp-session-metadata.schema.json`
