# RFC-MACP-0003
# Multi-Agent Coordination Protocol (MACP) — Determinism and Replay Integrity

**Document:** RFC-MACP-0003  
**Version:** 1.0.0-draft  
**Status:** Community Standards Track  
**Updates:** RFC-MACP-0001

## Abstract

This document defines MACP replay semantics, structural determinism guarantees, semantic determinism classes for Modes, and recommended patterns for external side effects.

## 1. Structural Replay Integrity

MACP Core guarantees structural replay integrity.

Replaying identical accepted Envelope sequences under identical:

- negotiated protocol version,
- schema namespace major version,
- Mode identifier and Mode version,
- configuration and policy version(s)

MUST reproduce identical session state transitions and acceptance/rejection behavior.

Specifically, replay MUST:

- accept the same messages in the same order,
- produce the same acceptance/rejection decisions for each envelope, given identical validation rules and bound versions (operational rejections such as rate limiting or transient authentication failures are outside the replay determinism boundary),
- produce the same terminal state (RESOLVED or EXPIRED) and terminal message,
- produce the same `Ack` accept/reject decisions for each envelope.

Replay does NOT guarantee identical external side effects (see Section 4). Replay also does not guarantee identical error message text — only identical accept/reject outcomes.

## 2. What Core Guarantees

Core guarantees determinism for:

- session lifecycle transitions,
- within-session acceptance order,
- idempotent handling of duplicate `message_id` values,
- the terminal lifecycle state (RESOLVED, EXPIRED, or CANCELLED) when the accepted history is identical.

Core does not guarantee semantic determinism unless the Mode claims it.

`timestamp_unix_ms` is informational for ordering and display purposes and MUST NOT be used for message acceptance decisions. However, `timestamp_unix_ms` on the `SessionStart` envelope is normative for TTL computation: the session's initial absolute expiration deadline is computed as `SessionStart_envelope.timestamp_unix_ms + SessionStartPayload.ttl_ms`. During replay, the runtime MUST derive the deadline from the original session timeline, not wall-clock time. If the TTL has elapsed before a terminal condition is accepted, the session transitions to EXPIRED.

**TTL under suspension (RFC-MACP-0001 §7.5).** Suspension banks the remaining TTL rather than letting the deadline keep running, so the deadline depends on the suspend/resume timeline. This is deterministic precisely because suspend and resume are accepted, recorded events on the session's append-only history: each `SessionSuspend`/`SessionResume` envelope carries the `timestamp_unix_ms` Core uses for accounting. On suspend at time `t_s`, the runtime banks `banked = deadline − t_s`; on resume at time `t_r`, it sets `deadline = t_r + banked` (recorded in `SessionResumePayload.banked_ms`). A `SUSPENDED` session MUST NOT expire on its pre-suspension deadline. To bound indefinite pauses, the runtime MUST enforce a fixed `MAX_SUSPEND_MS` cap: if cumulative suspended duration exceeds the cap, the session transitions `SUSPENDED → EXPIRED`. Because every input to this computation (`MAX_SUSPEND_MS` and the suspend/resume event timestamps) is on the replayed timeline, replay reconstructs the identical adjusted deadline and the identical terminal state — the determinism guarantee above holds for suspended-then-resumed sessions.

## 3. Version Binding

Sessions MUST bind these immutable values at SessionStart:

- Mode version,
- configuration version,
- policy version (MUST be bound and non-empty when any governance policy is in effect; see RFC-MACP-0012).
- any context freeze identifiers required by the Mode.

Replay MUST use the same bound versions. Replaying under a newer policy or Mode version is not historical reconstruction.

### 3.1 Worked Example: Correct and Incorrect Replay

**Original session** (mode_version=1.0.0, configuration_version=org-2026.01):

```
SessionStart (session_id=abc, mode=macp.mode.decision.v1,
              mode_version=1.0.0, configuration_version=org-2026.01)
→ Proposal (option A)
→ Vote (approve A)
→ Vote (approve A)
→ Commitment (selected: A, mode_version=1.0.0)
→ RESOLVED
```

**Correct replay** — same bound versions produce identical outcome:

```
Replay with mode_version=1.0.0, configuration_version=org-2026.01
→ Same messages in same order
→ Commitment (selected: A) ✓ identical
→ RESOLVED ✓ identical
```

**Incorrect replay** — different mode_version violates version binding:

```
Replay with mode_version=2.0.0, configuration_version=org-2026.01
→ mode_version=2.0.0 may alter voting thresholds or message validation
→ Commitment outcome may differ ✗ not historical reconstruction
```

This is not a valid historical replay. It is a what-if analysis under different semantics.

## 4. External Side Effects

Modes that touch the external world SHOULD use one of these patterns:

1. **Plan then execute** — session emits a Commitment that describes a side-effect plan; execution occurs afterward with idempotency keys.
2. **Log external results** — side-effect results are recorded as accepted session messages so replay can reuse recorded outputs.
3. **Idempotent external transactions** — external systems accept transaction identifiers and de-duplicate repeat attempts.

## 5. Determinism Classes

The determinism classes defined by RFC-MACP-0002 are normative for descriptors and manifests. Each class provides the following replay guarantees:

- **structural-only**: Replay reproduces identical lifecycle transitions (OPEN, RESOLVED, EXPIRED) and identical accept/reject decisions for each envelope. Semantic outcomes (e.g., which proposal wins a decision) are NOT guaranteed to be identical.

- **semantic-deterministic**: Replay reproduces identical lifecycle transitions AND the same semantic outcome — the terminal action, committed values, and resolution are identical given the same accepted envelope sequence.

- **context-frozen**: Same guarantees as semantic-deterministic, but ONLY when the external context bound at `SessionStart` (via `context` and `roots`) is replayed exactly. If bound context differs from the original session, replay outcomes are undefined.

- **non-deterministic**: Replay reproduces identical lifecycle transitions and accept/reject decisions, but semantic outcomes may differ due to runtime state or external side effects. Runtimes SHOULD NOT attempt semantic replay for non-deterministic modes.

Modes SHOULD state which inputs are inside the determinism boundary and which are excluded.

## 6. Cryptographic Integrity (Optional)

High-assurance deployments MAY add:

- signed Envelopes,
- hash-chained session logs,
- final session hashes embedded in terminal records.

## 7. Testing Requirements

Implementations SHOULD test determinism through:

- replay tests,
- terminal race tests,
- fuzzing of message sequences,
- failover and rehydration tests.
