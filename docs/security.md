# MACP Security

> **Reference:** [RFC-MACP-0001 Section 14](../rfcs/RFC-MACP-0001.md)

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

### Signal Authorization

Signals are ambient and non-binding, but implementations MAY:

- Require authentication for Signal submission
- Rate limit Signals per agent
- Filter/drop Signals based on policy

## Isolation

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

## Replay Protection

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

MACP uses structured errors (`MACPError` message):

```protobuf
message MACPError {
  string code = 1;        // Machine-readable error code
  string message = 2;     // Human-readable description
  string session_id = 3;  // Optional
  string message_id = 4;  // Optional
  bytes details = 5;      // Optional, mode-specific
}
```

### Information Leakage Prevention

Error messages SHOULD:

- Use generic error codes for authentication failures (`UNAUTHENTICATED`, not "invalid username")
- Avoid leaking session existence in `SESSION_NOT_FOUND` errors (if session IDs should be confidential)
- Not expose internal system details in `message` field

## Observability and Security Monitoring

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

| Code | HTTP Status | Description | Security Implication |
|------|-------------|-------------|---------------------|
| `UNAUTHENTICATED` | 401 | Authentication failed | Deny access |
| `FORBIDDEN` | 403 | Not authorized for session | Deny access |
| `DUPLICATE_MESSAGE` | 409 | message_id already seen | Possible replay attack |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist | May leak session existence |
| `SESSION_NOT_OPEN` | 409 | Session is RESOLVED/EXPIRED | Normal termination |
| `INVALID_ENVELOPE` | 400 | Malformed envelope | Possible attack |
| `PAYLOAD_TOO_LARGE` | 413 | Payload exceeds limit | DoS mitigation |
| `RATE_LIMITED` | 429 | Too many requests | DoS mitigation |

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

- **Participant validation**: How are participants authorized?
- **Commitment authority**: Who can emit binding commitments?
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
- [RFC-MACP-0001 Section 14](../rfcs/RFC-MACP-0001.md#14-security-considerations) - Full security specification
