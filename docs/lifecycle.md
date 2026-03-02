# MACP Session Lifecycle

> **Reference:** [RFC-MACP-0001 Section 7](../rfcs/RFC-MACP-0001.md)

## Overview

The MACP session lifecycle is a **monotonic state machine** that governs how Coordination Sessions are created, managed, and terminated. This design ensures predictable, enforceable coordination boundaries.

## Session States

MACP defines three session states:

| State | Description | Can Accept Messages? |
|-------|-------------|---------------------|
| **OPEN** | Session is active and accepting messages | ✓ Yes |
| **RESOLVED** | Session terminated via Mode-defined terminal condition | ✗ No |
| **EXPIRED** | Session terminated due to TTL/cancellation | ✗ No |

**Key Invariant:** No transition from `RESOLVED` or `EXPIRED` back to `OPEN` is permitted.

## State Transition Diagram

```
        SessionStart
             │
             ▼
          ┌──────┐
     ┌───►│ OPEN │────┐
     │    └──────┘    │
     │       │        │
     │       │        │ TTL Expired
     │       │        │ or Cancelled
     │       │        │
     │       │ Mode   │
     │       │ Terminal
     │       │ Message
     │       │        │
     │       ▼        ▼
     │  ┌──────────┐ ┌──────────┐
     │  │ RESOLVED │ │ EXPIRED  │
     │  └──────────┘ └──────────┘
     │       │             │
     └───────┴─────────────┘
           No further
         state transitions
```

## Session Creation

### SessionStart Message

A session is created upon acceptance of a valid `SessionStart` message.

**Requirements:**
- New unique `session_id`
- `mode` identifier
- `SessionStartPayload` with TTL
- Globally unique `message_id`

**Example:**
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

### Duplicate SessionStart Handling

- **Same `message_id`**: Treated as idempotent duplicate; MUST NOT create a second session
- **Same `session_id`, different `message_id`**: MUST be rejected

### SessionStart is Authoritative

- There is **no implicit coordination**
- No handshake requirement at MACP Core
- Runtimes MAY reject if it violates structural constraints (invalid TTL, unsupported mode, etc.)

## Session Operation (OPEN State)

### Acceptance Rules for Session-Scoped Messages

For any Envelope with a non-empty `session_id`:

1. ✓ The session MUST exist
2. ✓ The session MUST be `OPEN`
3. ✓ The Envelope MUST pass validation
4. ✓ The Envelope MUST not be a duplicate within the session
5. ✓ The sender MUST be authorized for that session

**If any check fails, the runtime MUST reject the message and MUST NOT create side effects.**

### Message Ordering

Ordering MUST be preserved **within a session** as observed from the runtime's accepted session log.

- In a bidirectional stream, gRPC preserves message order
- Multiple senders may interleave
- The runtime MUST define the session's total order as the order of acceptance into the append-only log
- **Cross-session ordering is not guaranteed** and MUST NOT be relied upon

### Idempotency

Runtimes MUST enforce idempotency using `message_id`:

- If an Envelope with a previously accepted `message_id` is received within the same session, it MUST be treated as a duplicate
- MUST NOT produce side effects
- Runtimes SHOULD maintain a replay cache for at least the lifetime of the session plus a configurable grace period

## Session Termination

### Termination via Mode-Defined Terminal Message (RESOLVED)

A session transitions from `OPEN` to `RESOLVED` upon receipt of the **first Mode-defined terminal message**.

**Common terminal message types:**
- `Commitment`: Binding outcome with version attribution
- `SessionEnd`: Non-commitment terminal (Mode-specific)

**Example Commitment:**
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

### Termination via Expiration (EXPIRED)

A session transitions from `OPEN` to `EXPIRED` when:

1. **TTL elapses**: The session's time-to-live (from `ttl_ms` in SessionStartPayload) expires
2. **Explicit cancellation**: Via `CancelSession` RPC or SessionCancel message
3. **Runtime policy**: Deterministic expiration due to resource constraints

**Important:** A termination message received **after** the session is `EXPIRED` MUST be rejected and MUST NOT retroactively alter the session state.

## Cancellation

### Session Cancellation

Session cancellation is explicit via `CancelSession(CancelSessionRequest)`.

**Requirements:**
- Cancellation transitions the session to `EXPIRED`
- Cancellation MUST NOT mutate prior session history
- Cancellation MUST be idempotent per session

### SessionCancel Envelope (Recommended)

If `SessionCancel` is implemented (RECOMMENDED), the runtime SHOULD emit a `SessionCancel` Envelope into the session log to make the terminal cause explicit and replayable.

**Example:**
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

## Session Metadata

Sessions have queryable metadata:

```protobuf
message SessionMetadata {
  string session_id = 1;
  string mode = 2;
  SessionState state = 3;
  int64 started_at_unix_ms = 4;
  int64 expires_at_unix_ms = 5;
}
```

Retrieved via `GetSession(SessionQuery)` RPC.

## Lifecycle Invariants

### Monotonic Transitions

Sessions **MUST** transition monotonically. Once a session reaches `RESOLVED` or `EXPIRED`, it cannot return to `OPEN`.

### Append-Only History

Accepted session messages are **immutable**. The session log is append-only.

### Isolation

Sessions are isolated from one another. Actions in Session A MUST NOT affect Session B's state.

### Time-Bounded

All sessions MUST have a finite TTL. Unbounded sessions are not permitted.

## Edge Cases and Error Handling

### Messages Sent to Non-Existent Session

**Error:** `SESSION_NOT_FOUND`

### Messages Sent to RESOLVED/EXPIRED Session

**Error:** `SESSION_NOT_OPEN`

### Duplicate Messages (Same message_id)

**Behavior:** Idempotent acceptance; return `Ack` with `duplicate=true`

### TTL Expiry During Message Processing

If a message is accepted while the session is still `OPEN`, but the session expires during processing:
- The message acceptance stands
- Subsequent messages will be rejected with `SESSION_EXPIRED`

### Concurrent Terminal Messages

If multiple agents send terminal messages concurrently:
- The **first accepted** terminal message determines the outcome
- Subsequent terminal messages are rejected (session no longer `OPEN`)

## Best Practices

### Set Appropriate TTLs

- Too short: Risk premature expiration
- Too long: Resource waste, delayed cleanup
- **Recommendation:** Match TTL to expected coordination duration + buffer

### Handle Cancellation Gracefully

Agents should be prepared to handle session cancellation at any time and clean up local state accordingly.

### Monitor Session State

Agents should periodically check session state via `GetSession` for long-running coordination.

### Log Terminal Causes

Always include clear `reason` fields in Commitment and SessionCancel payloads for auditability.

## See Also

- [Architecture](architecture.md) - Overall system design
- [Security](security.md) - Authorization and access control for sessions
- [Modes](modes.md) - Defining terminal conditions for modes
- [RFC-MACP-0001 Section 7](../rfcs/RFC-MACP-0001.md#7-coordination-session-lifecycle) - Full specification
