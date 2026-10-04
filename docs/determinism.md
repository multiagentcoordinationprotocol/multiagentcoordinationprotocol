# MACP Determinism and Replay Integrity

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md)

## Overview

MACP guarantees **structural replay integrity**: replaying identical accepted Envelope sequences under identical conditions MUST produce identical state transitions. This property is essential for auditability, debugging, and provenance verification.

## Core Guarantee

MACP provides this structural guarantee, normatively defined at
[RFC-MACP-0003 §1 (Structural Replay Integrity)](../rfcs/RFC-MACP-0003-determinism.md):

> Replaying identical accepted Envelope sequences under identical:
> - `macp_version`
> - Mode identifier and Mode version
> - Configuration version(s)
>
> MUST produce identical **state transitions** (OPEN → RESOLVED or OPEN → EXPIRED).

## What is Deterministic in MACP Core

See [RFC-MACP-0003 §2 (What Core Guarantees)](../rfcs/RFC-MACP-0003-determinism.md) for the
normative statement this section summarizes.

### Structural Determinism

MACP Core guarantees deterministic **structural behavior**:

1. **Session State Transitions**: Same message sequence = same final state (RESOLVED vs EXPIRED)
2. **Message Acceptance**: Same envelope sequence = same acceptance/rejection decisions
3. **Session Lifecycle**: Same SessionStart + same TTL + same messages = same lifecycle progression
4. **Idempotency**: Same `message_id` within a session always produces idempotent acceptance

### What MACP Core Does NOT Guarantee

MACP Core does NOT define determinism for:

- **Semantic outcomes**: What the "correct" decision is (Mode-defined)
- **External side effects**: Tool invocations, API calls (Mode/application responsibility)
- **Timestamp values**: `timestamp_unix_ms` is informational only
- **Ordering across sessions**: Cross-session message ordering is undefined

## Replay Scenarios

### 1. Audit and Compliance Replay

**Use Case:** Verify that a past coordination session followed correct procedures.

**Requirements:**
- Preserve session log (all accepted Envelopes in order)
- Record Mode version and configuration version
- Replay messages in identical order
- Verify final state matches historical record

**Example:**
```
Original session:
  SessionStart → Proposal → Vote → Vote → Commitment → RESOLVED

Replay:
  SessionStart → Proposal → Vote → Vote → Commitment → RESOLVED ✓
```

### 2. Debugging Replay

**Use Case:** Reproduce a bug or unexpected outcome.

**Requirements:**
- Capture full session log
- Capture Mode version, configuration version, MACP version
- Replay in test environment
- Compare state transitions and final outcomes

### 3. Forensic Replay

**Use Case:** Investigate security incident or disputed outcome.

**Requirements:**
- Immutable audit log
- Timestamp correlation with external logs
- Verify message authenticity (signatures if used)
- Check for unauthorized messages or tampering

## Versioning for Determinism

Normative home: [RFC-MACP-0003 §3 (Version Binding)](../rfcs/RFC-MACP-0003-determinism.md),
whose §3.1 worked example walks a correct replay (identical bound versions) against an
incorrect one (replaying under a newer `mode_version`, which is a what-if analysis, not
historical reconstruction) — see that section rather than a parallel example here.

### macp_version

All Envelopes in a session MUST use the same `macp_version`.

- **Major version changes**: May alter core state transition logic
- **Minor version changes**: SHOULD be backward compatible
- **Replay requirement**: Use same MACP runtime version for replay

### Mode Version

Modes MUST include explicit version identifiers:

- Via `mode` field (e.g., `macp.mode.decision.v1`)
- Via `mode_version` in SessionStartPayload
- In Commitment payloads (for attribution)

**Replay requirement:** Use same Mode version for replay

### Configuration Version

Sessions MAY reference configuration versions:

- `configuration_version` in SessionStartPayload
- `policy_version` in CommitmentPayload
- External configuration (e.g., approval thresholds, quorum sizes)

**Replay requirement:** Use identical configuration for replay

**Policy replay invariant.** When a session is governed by a policy, the resolved
`PolicyDescriptor` MUST be persisted on the session snapshot and used on replay — never
re-resolved from the registry. Policy equality for this purpose is `policy_id` +
`schema_version` + `rules`, not byte comparison, and a stored policy MUST be evaluated under
the `schema_version` it declares even when a newer one exists. See
[RFC-MACP-0012 §8 (Replay Invariant)](../rfcs/RFC-MACP-0012-policy.md) and
[docs/policy.md](policy.md#replay-invariant).

### Suspension and Resume

Suspend and resume are recorded as accepted events on the session's append-only history, so a
suspended-then-resumed session replays to the identical terminal state. The resolved
`max_suspend_ms` cap MUST be recorded on the session at `SessionStart` and replay MUST use that
recorded cap, never live runtime configuration — otherwise two runtimes (or one runtime
reconfigured between runs) could produce different terminal states on identical history. See
[RFC-MACP-0001 §7.5](../rfcs/RFC-MACP-0001-core.md), [RFC-MACP-0003 §2](../rfcs/RFC-MACP-0003-determinism.md),
and [docs/lifecycle.md](lifecycle.md).

### Example Version Attribution in Commitment

```json
{
  "commitment_id": "d4f9c5c0-3c7b-4b70-9f0c-2d57f6a3b1a2",
  "action": "vendor.select",
  "reason": "Vendor B meets security + budget constraints",
  "mode_version": "1.0.0",
  "policy_version": "org-procurement-2026.02",
  "configuration_version": "runtime-2026.03.01"
}
```

This allows replay verification: "Under these exact versions, this outcome is deterministic."

## Mode-Level Determinism

Modes MAY claim stronger determinism guarantees beyond MACP Core, per
[RFC-MACP-0003 §5 (Determinism Classes)](../rfcs/RFC-MACP-0003-determinism.md). The
standards-track classes themselves are declared in [RFC-MACP-0002 §7](../rfcs/RFC-MACP-0002-modes.md)
and summarized per mode in [`docs/modes.md`](modes.md)'s Determinism column.

### Deterministic Modes

A Mode is **deterministic** if:

- Same accepted messages → same semantic outcome
- No dependence on non-deterministic sources (time, randomness, external I/O)
- All decision logic is pure and versioned

**Example:** A voting mode where:
- 3-of-5 quorum required
- Outcome is "approved" if ≥3 votes are "yes"
- **Deterministic**: Same votes always produce same outcome

### Non-Deterministic Modes

A Mode is **non-deterministic** if:

- Outcome depends on wall-clock time beyond TTL
- Uses randomness (e.g., random selection)
- Depends on external I/O (API calls, database state)

**Example:** A mode that:
- Calls an external risk scoring API
- API returns different scores over time
- **Non-deterministic**: Replay may produce different outcome

### Determinism Claims in Mode Descriptors

Mode descriptors SHOULD declare determinism claims:

```json
{
  "mode": "macp.mode.decision.v1",
  "determinism_class": "semantic-deterministic"
}
```

## Sources of Non-Determinism to Avoid

### Time-Based Logic (Beyond TTL)

**Problem:** Different wall-clock times during replay.

**Anti-pattern:**
```javascript
if (currentTime > deadline) {
  return "expired";
}
```

**Better:** Use session TTL, which is part of SessionStart

### External I/O

**Problem:** External state may change between original run and replay.

**Anti-pattern:**
```javascript
let userProfile = await fetchUserProfile(userId);
if (userProfile.riskScore > 50) {
  return "reject";
}
```

**Better:** Bind necessary context at SessionStart — reference it via `context_id` (an opaque identifier the runtime preserves but never interprets) or carry protocol-specific bytes in `extensions`

### Randomness

**Problem:** Different random values on replay.

**Anti-pattern:**
```javascript
let selectedAgent = agents[Math.floor(Math.random() * agents.length)];
```

**Better:** Use deterministic selection (e.g., hash-based, first in list, etc.)

### Iteration Order of Unordered Collections

**Problem:** Hash maps, sets may have different iteration order.

**Anti-pattern:**
```javascript
for (let agent in agentMap) {  // Order undefined
  processVote(agentMap[agent]);
}
```

**Better:** Sort before iteration
```javascript
let sortedAgents = Object.keys(agentMap).sort();
for (let agentId of sortedAgents) {
  processVote(agentMap[agentId]);
}
```

## Handling External Side Effects

See [RFC-MACP-0003 §4 (External Side Effects)](../rfcs/RFC-MACP-0003-determinism.md).

### Tool Invocations

If a Mode coordinates tool execution:

- **Option 1 (Deterministic)**: Don't invoke tools during coordination; emit Commitment with tool execution plan
- **Option 2 (Idempotent)**: Include transaction IDs in tool calls; make tools idempotent
- **Option 3 (Logged)**: Log tool results as Mode messages; replay uses logged results

### External Transactions

For financial transactions, database writes, etc.:

- Use **saga patterns** with compensating transactions
- Include external transaction IDs in Commitment
- Ensure external systems support idempotency keys

## Replay Integrity Verification

### Verification Steps

1. **Load session log**: All accepted Envelopes in order
2. **Verify versions**: macp_version, mode, mode_version, configuration_version match
3. **Replay messages**: Feed messages to MACP runtime in same order
4. **Compare state transitions**: OPEN → RESOLVED/EXPIRED must match
5. **Compare terminal message**: the terminal `Commitment` (or mode-defined terminal message) must match (if deterministic Mode)

### Cryptographic Verification (Optional)

See [RFC-MACP-0003 §6 (Cryptographic Integrity (Optional))](../rfcs/RFC-MACP-0003-determinism.md).

For high-assurance scenarios:

- **Sign Envelopes**: Agents sign messages (include signature in metadata)
- **Hash chain**: Each message includes hash of previous message
- **Session hash**: Final session state includes hash of all messages

**Example structure:**
```json
{
  "session_id": "...",
  "final_state": "RESOLVED",
  "message_count": 5,
  "session_hash": "sha256:abcd1234...",
  "commitment_hash": "sha256:ef567890..."
}
```

`commitment_hash` is now canonically defined by [RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md); `session_hash` remains implementation-defined, as shown above. The canonical
commitment-hash vector pack is re-derived and compared against the pinned hashes by `make
cmt-hash-vectors`, and every conforming implementation MUST reproduce them, per
[RFC-MACP-0013 §11 (Testing Requirements)](../rfcs/RFC-MACP-0013-commitment-hash.md).

## Testing Determinism

See [RFC-MACP-0003 §7 (Testing Requirements)](../rfcs/RFC-MACP-0003-determinism.md). The
snippets below are illustrative; this repository's machine-checked surface is the canonical
fixture pack under [`schemas/conformance/`](../schemas/conformance/README.md) — per-message
accept/reject expectations and an `expected_mode_state`, linted for internal consistency by
`make conformance-lint` — and the per-SDK runner contract documented in
[docs/sdk-parity.md](sdk-parity.md#conformance-test-suite).

### Unit Tests for Modes

Test that same inputs produce same outputs:

```javascript
test('deterministic voting', () => {
  let session1 = runSession([vote1, vote2, vote3]);
  let session2 = runSession([vote1, vote2, vote3]);
  expect(session1.outcome).toEqual(session2.outcome);
});
```

### Replay Tests

Test that replaying a session produces identical state:

```javascript
test('session replay', () => {
  let originalSession = runSession(messages);
  let replayedSession = replaySession(messages);
  expect(replayedSession.state).toEqual(originalSession.state);
  expect(replayedSession.finalMessage).toEqual(originalSession.finalMessage);
});
```

### Fuzzing

Fuzz test message sequences to find non-deterministic edge cases:

```javascript
for (let i = 0; i < 1000; i++) {
  let messages = generateRandomMessageSequence();
  let run1 = runSession(messages);
  let run2 = runSession(messages);
  expect(run1.state).toEqual(run2.state);
}
```

## Limitations and Trade-offs

### Determinism vs. Real-Time Responsiveness

Fully deterministic systems may sacrifice real-time responsiveness:

- Cannot use wall-clock deadlines
- Cannot react to external events dynamically

**Trade-off:** Decide based on use case. Financial coordination may require full determinism; incident response may prioritize responsiveness.

### Determinism vs. External Context

Including all external context in SessionStart can lead to large payloads.

**Trade-off:** Balance between self-contained sessions and reliance on external lookups.

## Best Practices

1. **Version everything**: Mode, policy, configuration
2. **Include context in SessionStart**: Minimize external dependencies
3. **Make tools idempotent**: Use transaction IDs, support replay
4. **Log external results**: Capture API responses in session messages
5. **Test replay regularly**: Ensure determinism holds as Modes evolve
6. **Document determinism claims**: Be explicit about what is/isn't deterministic
7. **Use immutable logs**: Prevent tampering with historical sessions

## See Also

- [Architecture](architecture.md) - Append-only history and isolation
- [Lifecycle](lifecycle.md) - Session state transitions
- [Modes](modes.md) - Implementing deterministic Modes
- [RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md) - Full specification
