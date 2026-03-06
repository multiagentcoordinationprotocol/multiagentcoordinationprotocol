# RFC-MACP-0004
# Multi-Agent Coordination Protocol (MACP) — Security Considerations

**Document:** RFC-MACP-0004  
**Version:** 1.0.0-draft  
**Status:** Community Standards Track  
**Updates:** RFC-MACP-0001

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

The `sender` field MUST be derived from authenticated identity and MUST NOT be accepted as a self-asserted free-form value.

## 4. Authorization

Before accepting a session-scoped Envelope, the runtime MUST verify:

- the sender is authenticated,
- the sender is authorized for the session,
- the sender is allowed to emit that message type under the Mode.

## 5. Replay Protection

`message_id` deduplication is REQUIRED. Session identifiers MUST be cryptographically strong and unguessable.

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

### 11.1 Tenant-Scoped Session Namespaces

Session identifiers MUST be scoped to a tenant namespace. A session created by Tenant A MUST NOT be accessible to Tenant B.

### 11.2 Session ID Guessing Prevention

`session_id` values MUST be cryptographically strong and unguessable (see Section 5). In multi-tenant deployments, even a valid `session_id` MUST be rejected if the requesting agent is not authorized for the owning tenant.

### 11.3 Authorization Boundaries

Runtimes MUST enforce tenant authorization boundaries:

- agents MUST be bound to one or more tenants,
- session-scoped messages MUST be rejected if the sender's tenant does not match the session's tenant,
- cross-tenant coordination, if supported, MUST use explicit inter-tenant session linking rather than shared session access.
