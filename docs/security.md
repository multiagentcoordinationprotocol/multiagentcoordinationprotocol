# MACP Security

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md)

## Overview

Security is a foundational requirement for MACP. This document outlines the security model, threat mitigations, and implementation requirements for MACP-compliant systems.

## Security Principles

1. **Transport Security**: All communication MUST be encrypted
2. **Authentication**: Identify all agents
3. **Authorization**: Enforce access control for sessions
4. **Isolation**: Prevent cross-session attacks
5. **Replay Protection**: Prevent message replay attacks
6. **DoS Mitigation**: Defend against resource exhaustion

## Transport Security

See [RFC-MACP-0004 §2 (Transport Security)](../rfcs/RFC-MACP-0004-security.md).

### Requirement: TLS

All MACP deployments MUST use **encrypted transport (TLS)**.

**For gRPC (normative transport):**
- TLS 1.2 or higher REQUIRED
- TLS 1.3 RECOMMENDED
- Strong cipher suites only
- Certificate validation MUST be enforced

**For optional REST transport:**
- HTTPS REQUIRED
- Same TLS requirements as gRPC

**Rationale:** Prevent eavesdropping, tampering, and man-in-the-middle attacks.

## Authentication

See [RFC-MACP-0004 §3 (Authentication)](../rfcs/RFC-MACP-0004-security.md).

### Supported Mechanisms

MACP implementations MUST support at least one of the following authentication mechanisms:

#### 1. Mutual TLS (mTLS)

- Both client and server present certificates
- Certificates identify agents
- **Recommended for agent-to-agent communication**

**Example:** Agent certificates issued by a trusted CA, with agent identifier in certificate CN or SAN

#### 2. JWT (JSON Web Tokens)

- JWTs passed via gRPC metadata or HTTP headers
- Claims include agent identifier
- Tokens signed by trusted issuer
- **Recommended for gateway/proxy scenarios**

**Token Requirements:**
- Must include `sub` (subject) claim with agent identifier
- Must include `exp` (expiration) claim
- SHOULD include `aud` (audience) claim
- Signature algorithm: RS256, ES256, or stronger

#### 3. OAuth 2.0 / OIDC

- Standard OAuth 2.0 flows
- OIDC ID tokens provide agent identity
- **Recommended for user-initiated coordination**

### Agent Identifier Mapping

The `sender` field in MACP Envelopes MUST be derived from the authenticated identity:

- **mTLS**: Extract from certificate (CN, SAN, or custom extension)
- **JWT**: Use `sub` claim
- **OIDC**: Use `sub` from ID token

## Authorization

See [RFC-MACP-0004 §4 (Authorization)](../rfcs/RFC-MACP-0004-security.md).

### Session-Level Authorization

Before processing any session-scoped message, the runtime MUST verify:

1. **The sender is authenticated**
2. **The sender is authorized for the session**

**Authorization rules are Mode-defined or deployment-defined:**

- **Participant-based**: Sender MUST be in the `participants` list from SessionStart
- **Role-based**: Sender MUST have required role/permission
- **Capability-based**: Sender MUST present valid capability token

### SessionStart Authorization

Runtimes SHOULD implement admission control for `SessionStart`:

- Rate limiting per agent
- Quota enforcement (max concurrent sessions per agent)
- Policy checks (e.g., only certain agents can initiate certain modes)

### CancelSession Authorization

By default, only the session initiator is authorized to cancel. Deployments MAY extend cancellation authority, but cancellation MUST always require authentication and authorization. `SuspendSession` and `ResumeSession` share the same authority model and the same authentication requirement as `CancelSession`, per [RFC-MACP-0001 §7.5 (Suspension and Resume)](../rfcs/RFC-MACP-0001-core.md).

### Signal Authorization

See [RFC-MACP-0004 §4.1 (Signal Authentication)](../rfcs/RFC-MACP-0004-security.md).

Signals are ambient and non-binding. In the base protocol they carry an empty `session_id` and an empty `mode`; session correlation, if needed, belongs inside `SignalPayload`. Implementations MAY:

- Require authentication for Signal submission
- Rate limit Signals per agent
- Filter/drop Signals based on policy

## Isolation

See [RFC-MACP-0004 §6 (Isolation and Injection Prevention)](../rfcs/RFC-MACP-0004-security.md).

### Session Isolation

Sessions MUST be isolated from one another:

- **Message isolation**: Messages in Session A cannot affect Session B
- **State isolation**: Session state is independent
- **Resource isolation**: DoS in one session should not affect others

### Cross-Session Message Injection Prevention

Runtimes MUST validate:

- `session_id` matches the session context
- Messages cannot be "replayed" into a different session
- `message_id` is globally unique (prevents cross-session replay)

### Multi-Tenancy Isolation

Multi-tenant MACP deployments MUST enforce tenant-scoped isolation at the authorization layer:
session identifiers scoped to a tenant namespace, rejection of a cross-tenant request even when
the `session_id` itself is valid, and agents bound to one or more tenants. MACP Core does not
define a `tenant_id` field; tenant scoping is deployment-defined. See
[RFC-MACP-0004 §11 (Multi-Tenancy Isolation)](../rfcs/RFC-MACP-0004-security.md).

## Replay Protection

See [RFC-MACP-0004 §5 (Replay Protection)](../rfcs/RFC-MACP-0004-security.md).

### message_id Deduplication

Runtimes MUST enforce idempotency using `message_id`:

- Track accepted `message_id` values per session
- Reject duplicate `message_id` within a session
- Maintain replay cache for session lifetime + grace period

**Grace period recommendation:** 5 minutes to 1 hour after session termination

### session_id Strength

`session_id` values MUST be cryptographically strong and unguessable:

- Use UUIDv4, ULID, or equivalent
- Minimum 128 bits of entropy
- Generated securely (not predictable)

**Anti-pattern:** Sequential session IDs (e.g., `session-1`, `session-2`)

### Timestamp Validation

While `timestamp_unix_ms` is informational and MUST NOT be used for ordering, implementations MAY:

- Reject messages with timestamps too far in the past/future (clock skew protection)
- Log timestamp anomalies for monitoring

## Denial-of-Service (DoS) Mitigation

See [RFC-MACP-0004 §7 (DoS Mitigation)](../rfcs/RFC-MACP-0004-security.md).

### SessionStart Flooding

**Threat:** Attacker creates many sessions to exhaust resources.

**Mitigations:**
- Rate limiting: Max SessionStart requests per agent per time window
- Admission control: Validate session parameters before creating session
- Resource quotas: Max concurrent OPEN sessions per agent

### Payload Amplification

**Threat:** Attacker sends large payloads to exhaust memory/bandwidth.

**Mitigations:**
- Maximum payload size limits (RFC recommends defining and enforcing)
- Reject oversized payloads with `PAYLOAD_TOO_LARGE` error
- **Recommended max:** 1 MB per message

### Unbounded Buffering

**Threat:** Runtime buffers unlimited messages, exhausting memory.

**Mitigations:**
- Backpressure via HTTP/2 flow control (gRPC)
- Maximum in-flight messages per session
- Reject new messages if buffer limit reached

### Session Graph Attacks (Optional Nested Sessions)

**Threat:** Deeply nested or cyclic session graphs exhaust resources.

**Mitigations (if nested sessions are supported):**
- Depth limits: Max nesting level (e.g., 3-5 levels)
- Hop limits: Max cross-session traversals
- Cycle prevention: Track session parent relationships, reject cycles

## Error Handling and Information Disclosure

### Structured Errors

MACP uses structured errors (`MACPError` message). Canonical definition:
[`schemas/proto/macp/v1/envelope.proto`](../schemas/proto/macp/v1/envelope.proto), per
[RFC-MACP-0001 §12 (Error Model)](../rfcs/RFC-MACP-0001-core.md).

### Information Leakage Prevention

Error messages SHOULD:

- Use generic error codes for authentication failures (`UNAUTHENTICATED`, not "invalid username")
- Avoid leaking session existence in `SESSION_NOT_FOUND` errors (if session IDs should be confidential)
- Not expose internal system details in `message` field

## Observability and Security Monitoring

See [RFC-MACP-0004 §8 (Auditability)](../rfcs/RFC-MACP-0004-security.md).

### Audit Logging

Implementations SHOULD log security-relevant events:

- Session creation (who, when, mode, participants)
- Session termination (outcome, reason)
- Authentication failures
- Authorization denials
- Duplicate message rejections (potential replay attacks)
- Rate limit violations

### Trace Propagation

Implementations SHOULD support distributed tracing:

- W3C Trace Context via gRPC metadata
- OpenTelemetry compatible
- **IMPORTANT:** Trace propagation MUST NOT compromise session isolation

### Anomaly Detection

Monitor for:

- Unusual session creation rates
- High duplicate message rates (replay attempts)
- Authorization failure spikes
- Timestamp anomalies

## Common Error Codes

[`registries/error-codes.md`](../registries/error-codes.md) is authoritative for the code,
HTTP status, description, and lifecycle status of every MACP error code. The table below adds
only the **Security Implication** column, which has no registry home, and covers a
security-relevant subset; the three governance-policy codes (`UNKNOWN_POLICY_VERSION`,
`POLICY_DENIED`, `INVALID_POLICY_DEFINITION`) are covered in
[`docs/policy.md`](policy.md)'s own Error Codes table rather than duplicated a third time here.

| Code | HTTP Status | Description | Security Implication |
|------|-------------|-------------|---------------------|
| `UNAUTHENTICATED` | 401 | Authentication failed | Deny access |
| `FORBIDDEN` | 403 | Authenticated sender not authorized for the session, message type, role, or claimed authority (see [RFC-MACP-0002 §6.1](../rfcs/RFC-MACP-0002-modes.md) for the Mode-rule mapping) | Deny access |
| `DUPLICATE_MESSAGE` | 409 | `message_id` already accepted within the session | Possible replay attack |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist | May leak session existence |
| `SESSION_NOT_OPEN` | 409 | Session is RESOLVED/EXPIRED | Normal termination |
| `SESSION_ALREADY_EXISTS` | 409 | Session already has an accepted SessionStart for this session_id | Possible replay or collision |
| `INVALID_ENVELOPE` | 400 | Envelope validation failed, payload structural contract not met, or mode validation rule breached | Possible attack |
| `UNSUPPORTED_PROTOCOL_VERSION` | 400 | No mutually supported protocol version | Version mismatch |
| `MODE_NOT_SUPPORTED` | 400 | Referenced mode or mode version not supported | Mode mismatch |
| `PAYLOAD_TOO_LARGE` | 413 | Payload exceeds limit | DoS mitigation |
| `RATE_LIMITED` | 429 | Too many requests | DoS mitigation |
| `INVALID_SESSION_ID` | 400 | session_id format does not meet requirements | Possible attack |
| `INTERNAL_ERROR` | 500 | Unrecoverable internal runtime error | Retry or escalate |
| `UNAUTHORIZED` | 403 | Historical alias for `FORBIDDEN` (deprecated); new implementations SHOULD use `FORBIDDEN` | Use `FORBIDDEN` instead |

## Deployment Best Practices

### Agent Identity Management

- Use short-lived credentials when possible
- Rotate certificates/tokens regularly
- Revoke compromised credentials immediately
- Maintain agent identity registry

### Session Security Policies

- Define participant authorization models per Mode
- Implement principle of least privilege
- Audit high-privilege sessions

### Network Security

- Deploy MACP runtimes in private networks when possible
- Use network segmentation to isolate agent clusters
- Implement firewall rules to restrict access to MACP endpoints

### Secrets Management

- Never hardcode credentials in agent code
- Use secret management systems (e.g., HashiCorp Vault, AWS Secrets Manager)
- Encrypt credentials at rest

## Security Considerations for Modes

Mode developers MUST consider:

- **Participant validation**: How are participants authorized? Role-based authority (e.g.
  `designated_role`/`designated_roles`) has a normative home in
  [RFC-MACP-0012 §4](../rfcs/RFC-MACP-0012-policy.md); a breach of these rules is `FORBIDDEN`,
  not `POLICY_DENIED`, per [RFC-MACP-0002 §6.1](../rfcs/RFC-MACP-0002-modes.md).
- **Commitment authority**: Who can emit binding commitments? See `commitment.authority` in
  [RFC-MACP-0012 §4](../rfcs/RFC-MACP-0012-policy.md).
- **Data confidentiality**: Should payloads be encrypted?
- **Audit requirements**: What must be logged for compliance?

**Example:** A financial approval mode might require:
- Only designated approvers can vote
- Commitment requires quorum
- All votes are logged immutably
- Sensitive financial data in payloads is encrypted

## Security Testing

### Recommended Tests

1. **Authentication bypass attempts**
2. **Authorization escalation attempts** (agent accesses session they shouldn't)
3. **Replay attack simulations** (duplicate message_id)
4. **DoS stress tests** (session flooding, payload amplification)
5. **Session isolation verification** (cross-session message injection)
6. **TLS configuration validation** (weak ciphers, certificate validation)

### Penetration Testing

Periodically conduct penetration tests focusing on:
- Agent authentication mechanisms
- Session authorization enforcement
- Message validation and injection
- Resource exhaustion vectors

## Compliance and Regulatory Considerations

See [RFC-MACP-0004 §10 (Privacy and Compliance)](../rfcs/RFC-MACP-0004-security.md).

Depending on your deployment, consider:

- **GDPR**: Personal data in payloads, right to erasure (conflicts with append-only logs)
- **HIPAA**: Healthcare data encryption, access controls
- **SOC 2**: Audit logging, access controls, encryption
- **PCI DSS**: Payment card data handling

**Recommendation:** Encrypt sensitive payloads at the application layer (Mode-level) before placing in MACP envelopes.

## See Also

- [Architecture](architecture.md) - Isolation and session boundaries
- [Lifecycle](lifecycle.md) - Session state management
- [Determinism](determinism.md) - Replay integrity
- [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) - Full security specification
