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

## 2. What Core Guarantees

Core guarantees determinism for:

- session lifecycle transitions,
- within-session acceptance order,
- idempotent handling of duplicate `message_id` values,
- the terminal lifecycle state (RESOLVED or EXPIRED) when the accepted history is identical.

Core does not guarantee semantic determinism unless the Mode claims it.

`timestamp_unix_ms` is informational and MUST NOT influence structural replay. TTL expiration during replay SHOULD use the original session timeline (computed from `SessionStart` timestamp and `ttl_ms`), not wall-clock time.

## 3. Version Binding

Sessions MUST bind these immutable values at SessionStart:

- Mode version,
- configuration version,
- policy version (if applicable). Sessions SHOULD bind policy version when applicable.
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

The determinism classes defined by RFC-MACP-0002 are normative for descriptors and manifests.

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
