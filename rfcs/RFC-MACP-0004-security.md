# RFC-MACP-0004
# Multi-Agent Coordination Protocol (MACP) — Security Considerations

**Document:** RFC-MACP-0004  
**Version:** 1.2.0-draft  
**Status:** Community Standards Track  
**Updates:** RFC-MACP-0001

> **Changelog — 1.2.0-draft:** two changes from the Seam runtime's protocol pass (issue #185). **(1) `session_id` length floor.** §11.2 set a minimum strength for `session_id` but no length bound, so a runtime that capped id length could refuse an id that another conformant runtime had issued. §11.2 now lets a runtime cap `session_id` length, but the cap MUST NOT fall below 128 bytes. A `session_id` over the runtime's cap MUST be rejected with `INVALID_SESSION_ID`. Every id of 128 bytes or fewer that meets the strength requirement is therefore portable across conformant runtimes. **(2) `macp.security.delegated_submission.v1` is now `permanent`** in `registries/capabilities.md` (it was `provisional`). Its identifier and the §3.1 obligations it advertises are fixed: a semantic change ships under a new identifier (`.v2`), and the `.v1` identifier will not be reused. **Replay: neutral.** The length cap applies at `SessionStart` admission, before a session has any accepted history, and the registry status changes no behaviour.
>
> **Changelog — 1.1.0-draft:** two additions, both from the seam-embedder-findings proposal (issue #185). **(S3)** New §3.1 defines **delegated submission**: a runtime MAY accept a session-scoped envelope whose `sender` differs from the authenticated principal of the submitting connection (the *submitter*) only when the submitter is itself authenticated, holds a delegation naming that `sender` that is scoped to a session (or set of sessions) and to the message types it covers, the runtime records the submitter alongside the accepted envelope outside `Envelope`, and the runtime advertises the new capability `macp.security.delegated_submission.v1` (`registries/capabilities.md`) and documents the delegation mechanisms it accepts. §4's first bullet now reads "authenticated, or covered by a delegation per §3.1"; the delegation never substitutes for §4's session- and message-type authorization of the delegated `sender`, and an unscoped submitter credential MUST NOT be treated as a delegation for every participant. Previously §3's "MUST be derived from authenticated identity" made every gateway, human-in-the-loop UI and embedding service that submits on behalf of panel members non-conformant by construction, and gave the specification no vocabulary to distinguish a gateway that binds each participant to a grant from one that accepts any string. The change is additive: a runtime that never accepts delegated submissions is unaffected and need not advertise the capability; a deployment that already delegates gains a conformant path but must add the item-3 audit record and the item-4 advertisement. **(S8)** §4.1's requirement that an unauthenticated Signal not reach `WatchSignals` subscribers "without annotation" had no wire field to carry the annotation on the gRPC binding — `WatchSignalsResponse` held only the `Envelope`, which has no authentication field. `core.proto` gains `bool sender_authenticated = 2` on `WatchSignalsResponse`, and §4.1 now names it. The field is additive; in proto3 an absent field reads as `false`, so an old runtime, or a client built before the field existed, reads every Signal as unauthenticated — the safe direction. **Replay: neutral.** Neither change alters what a session's accepted history contains or how it is evaluated: delegation changes who may *submit* an envelope, not the envelope's content or its effect on session state, and the item-3 submitter record lives outside `Envelope` and outside the history replay re-drives ([RFC-MACP-0003](RFC-MACP-0003-determinism.md) §1). `sender_authenticated` is a delivery annotation on the ambient Signal plane, which never affects session state. The one exposure is audit, not replay: sessions a deployment accepted by delegation before this revision carry no submitter record, and an auditor cannot reconstruct one after the fact.

## Abstract

MACP is a coordination kernel. Because it governs the moment where systems become bound to outcomes, its security boundary is not optional. This document defines the threat model and required mitigations for compliant MACP deployments.

This document expands on the security requirements in [RFC-MACP-0001 Core, Section 13](RFC-MACP-0001-core.md).

## 1. Security Principles

MACP deployments MUST enforce:

- encrypted transport,
- authenticated senders,
- authorization for session-scoped messages,
- replay protection,
- session isolation,
- resource exhaustion defenses.

## 2. Transport Security

All MACP deployments MUST use encrypted transport.

For gRPC over HTTP/2, TLS 1.2 or higher is REQUIRED and TLS 1.3 is RECOMMENDED.

## 3. Authentication

Deployments MUST support at least one machine-appropriate authentication mechanism such as mTLS, JWT-based bearer identity, or OIDC-based federation.

The `sender` field MUST be derived from authenticated identity and MUST NOT be accepted as a self-asserted free-form value. Section 3.1 defines the only exception: a `sender` covered by a delegation.

### 3.1 Delegated submission

A runtime MAY accept a session-scoped envelope whose `sender` differs from the authenticated principal of the submitting connection (the **submitter**) only when all of the following hold:

1. The submitter is authenticated per Section 3.
2. The submitter holds a **delegation** naming that `sender` for that session, established before the envelope is accepted. Examples: a signed grant, a session-scoped token, or an operator-configured panel binding. The delegation MUST be scoped to a session, or to a set of sessions, and to the message types it covers.
3. The runtime records the submitter's identity alongside the accepted envelope, in a field or log annotation outside `Envelope`, so that an auditor can distinguish delegated acceptance from direct acceptance.
4. A runtime that accepts delegated submissions MUST advertise it (capability `macp.security.delegated_submission.v1`, see [`registries/capabilities.md`](../registries/capabilities.md)) and MUST document the delegation mechanisms it accepts.

A delegation does not satisfy the authorization checks of Section 4 by itself: the delegated `sender` MUST still be authorized for the session and allowed to emit the message type under the Mode. A runtime MUST NOT treat an unscoped submitter credential as a delegation for every participant.

## 4. Authorization

Before accepting a session-scoped Envelope, the runtime MUST verify:

- the sender is authenticated, or is covered by a delegation per Section 3.1,
- the sender is authorized for the session,
- the sender is allowed to emit that message type under the Mode.

### 4.1 Signal Authentication

Ambient Signals SHOULD be authenticated using the same mechanisms as session-scoped messages. Runtimes MAY accept unauthenticated Signals but MUST document this as a deployment-specific policy. Unauthenticated Signals MUST NOT influence operational decisions or be forwarded to `WatchSignals` subscribers without annotation indicating their unauthenticated status. On the gRPC binding that annotation is `WatchSignalsResponse.sender_authenticated = false`; a runtime MUST set `sender_authenticated = true` only for a Signal whose `sender` was authenticated per Section 3. Because `false` is the proto3 default, a subscriber MUST treat an absent field as unauthenticated.

## 5. Replay Protection

`message_id` deduplication is REQUIRED for idempotency within sessions. Transport-layer replay protection (TLS) provides the primary defense against network-level replay attacks. Implementations SHOULD additionally validate token freshness and MAY enforce timestamp-based anti-replay windows. `message_id` deduplication alone does not constitute complete replay protection against an attacker who can craft new messages with fresh `message_id` values. Session identifiers MUST be cryptographically strong and unguessable.

## 6. Isolation and Injection Prevention

The runtime MUST prevent:

- cross-session message injection,
- terminal messages for non-OPEN sessions,
- split-brain ordering authorities,
- mutation of accepted history.

## 7. DoS Mitigation

Deployments SHOULD enforce:

- rate limits for SessionStart,
- payload size limits,
- maximum concurrent OPEN sessions per agent,
- bounded buffering and transport backpressure.

## 8. Auditability

Security-relevant events SHOULD be logged, including:

- authentication failures,
- authorization failures,
- duplicate message rejections,
- terminal transitions,
- cancellation requests,
- quota and rate-limit violations.

## 9. Sensitive Payloads

Modes carrying sensitive content SHOULD define whether payloads require application-layer encryption in addition to transport encryption.

## 10. Privacy and Compliance

Append-only coordination logs may conflict with erasure-oriented privacy regimes. Deployments SHOULD address this through the following measures:

### 10.1 Cryptographic Erasure

To reconcile append-only session logs with GDPR right to erasure (and similar regimes), deployments SHOULD use **per-session encryption keys**. Destroying the encryption key renders the session data unrecoverable without modifying the append-only log structure. This approach preserves structural integrity while satisfying erasure requirements.

### 10.2 Data Minimization

Coordination envelopes SHOULD avoid personally identifiable information (PII). Agent identifiers SHOULD be pseudonymous where possible. Sensitive context SHOULD be referenced by opaque identifier rather than embedded directly in payloads.

### 10.3 Retention Policies

Deployments SHOULD define retention policies for session logs that account for:

- regulatory requirements (e.g., minimum retention for audit trails),
- replay integrity needs (sessions must remain replayable for the retention period),
- privacy obligations (maximum retention limits).

### 10.4 Cross-Border Data Considerations

When MACP sessions span multiple jurisdictions, deployments SHOULD consider:

- data residency requirements for session logs,
- jurisdictional restrictions on payload content,
- transfer mechanisms (e.g., Standard Contractual Clauses, adequacy decisions) for cross-border session data.

## 11. Multi-Tenancy Isolation

Multi-tenant MACP deployments MUST enforce tenant-scoped isolation.

Multi-tenant isolation is an operational concern. MACP Core (RFC-MACP-0001) does not define a `tenant_id` field in the Envelope or SessionMetadata; tenant scoping is an authorization-layer responsibility. Runtimes implementing multi-tenancy MUST enforce the following rules at the authorization layer, using deployment-defined tenant bindings (e.g., derived from authenticated identity, JWT claims, or mTLS certificate attributes).

### 11.1 Tenant-Scoped Session Namespaces

Session identifiers MUST be scoped to a tenant namespace. A session created by Tenant A MUST NOT be accessible to Tenant B.

### 11.2 Session ID Guessing Prevention

`session_id` values MUST be cryptographically strong and unguessable (see Section 5). In multi-tenant deployments, even a valid `session_id` MUST be rejected if the requesting agent is not authorized for the owning tenant.

A runtime MAY cap `session_id` length, measured in bytes of its UTF-8 encoding, to bound per-session state. A runtime that caps it MUST accept every `session_id` of 128 bytes or fewer that meets the strength requirement above, MUST reject a longer one with `INVALID_SESSION_ID`, and SHOULD document its cap. An issuer that wants its identifiers accepted by every conformant runtime SHOULD keep them within 128 bytes.

### 11.3 Authorization Boundaries

Runtimes MUST enforce tenant authorization boundaries:

- agents MUST be bound to one or more tenants,
- session-scoped messages MUST be rejected if the sender's tenant does not match the session's tenant,
- cross-tenant coordination, if supported, MUST use explicit inter-tenant session linking rather than shared session access.
