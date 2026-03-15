# RFC-MACP-0002
# Multi-Agent Coordination Protocol (MACP) - Coordination Modes

**Document:** RFC-MACP-0002
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001

## Abstract

Coordination Modes define semantic behavior inside MACP Sessions. MACP Core defines structure; Modes define meaning. This document specifies how Modes are identified, described, negotiated, registered, versioned, and constrained. It also defines the main-repository boundary: the standards repo carries only foundational, cross-domain coordination primitives.

## 1. Scope

A Mode specification defines:

- its identifier and version,
- its additional message types,
- its participant rules,
- its state machine and validation rules,
- its termination conditions,
- its determinism claim,
- its commitment semantics,
- its payload schemas,
- its security considerations.

Modes MUST NOT violate MACP Core invariants.

## 2. What belongs in the main RFC repo

The main MACP RFC repo standardizes only foundational coordination primitives that are expected to be broadly reusable across runtimes and domains.

A Mode belongs in the main repo only if it is all of the following:

- cross-domain,
- bounded and convergent inside a MACP Session,
- stable enough to justify long-term compatibility obligations,
- likely to be implemented by multiple independent runtimes.

The main repo standardizes the following mode set:

- `macp.mode.decision.v1`
- `macp.mode.proposal.v1`
- `macp.mode.task.v1`
- `macp.mode.handoff.v1`
- `macp.mode.quorum.v1`

The following patterns are intentionally excluded from the main standards set until they demonstrate broad interoperable demand:

- workflow recipes such as debate, critique, review, pipeline, or swarm patterns,
- highly domain-specific modes,
- fast-moving experimental modes,
- broadcast-style dissemination patterns that are better modeled as ambient Signals or external pub/sub systems.

Experimental Modes SHOULD use reverse-domain identifiers to avoid collisions.

## 3. Mode identifiers

Standard Mode identifiers SHOULD use the form:

`macp.mode.<name>.v<major>`

Experimental or vendor-specific Modes SHOULD use reverse-domain names, for example:

`com.example.mode.custom.v1`

## 4. Mode Descriptor

A runtime that supports `modeRegistry.listModes` SHOULD expose a machine-readable Mode Descriptor for each supported Mode.

A Mode Descriptor SHOULD include:

- identifier,
- semantic version,
- title and description,
- determinism class,
- participant model,
- supported message types,
- terminal message types,
- schema URIs.

## 5. Participant models

This specification recognizes the following participant models:

- **declared** - participant set is bound at `SessionStart`.
- **quorum** - a subset of eligible participants may be sufficient for resolution.
- **orchestrated** - one coordinator assigns work or finalizes outcomes.
- **peer** - participants are symmetric and negotiate directly.
- **delegated** - participants may transfer or accept scoped authority.

A Mode MUST declare which participant model it uses.

## 6. Terminal and authority semantics

Core requires sessions to terminate, but Core does not require every possible Mode in the ecosystem to share the same terminal message shape. For standards-track modes in this main repo, however, v1 uses a single rule:

- `Commitment` is the authoritative terminal message for a successful or definitive outcome.

A standards-track Mode MAY define intermediate outcome messages such as `TaskComplete` or `HandoffAccept`, but those messages do not resolve the Session on their own. The Session resolves only when an authorized `Commitment` is accepted.

Each Mode MUST declare:

- who is authorized to emit `Commitment`,
- what preconditions make a Session eligible for commitment,
- whether the Mode allows definitive negative outcomes to be committed,
- whether non-terminal intermediate messages have side effects outside the runtime boundary.

`SessionCancel` and Session expiry remain Core escape paths, not normal success paths for standards-track mode outcomes.

## 7. Determinism claims

A Mode MUST declare one of the following determinism classes:

- **structural-only** - Core replay is preserved but semantic outcome is not guaranteed,
- **semantic-deterministic** - same accepted history produces the same semantic outcome,
- **context-frozen** - semantic determinism holds only if external context bound at `SessionStart` is replayed exactly,
- **non-deterministic** - runtime or external side effects may change semantic outcomes.

The full determinism and replay integrity model is specified in [RFC-MACP-0003](RFC-MACP-0003-determinism.md).

## 8. Semantic idempotency

Core deduplicates messages by `message_id`, but a Mode MUST define idempotency for semantic actions that can escape the runtime boundary, for example:

- tool execution,
- transaction initiation,
- external write requests,
- ownership transfer,
- approval or release gates.

If a Mode can trigger external side effects, its specification MUST describe how runtimes and participants prevent duplicate execution.

## 9. Standards-track Mode requirements

A Mode MUST NOT enter the main RFC repo without all of the following:

- a normative RFC,
- canonical schemas under `schemas/proto/`,
- a human-friendly entrypoint schema under `schemas/modes/`,
- at least one example transcript,
- a declared determinism class,
- a participant model,
- explicit commitment authority rules,
- security considerations,
- a registry entry in `registries/modes.md`.

## 10. Standard mode set

The standards-track Mode set in this repo is:

| Mode | Purpose | Participant model | Determinism class | Registry status | Reference |
|------|---------|-------------------|-------------------|-----------------|-----------|
| `macp.mode.decision.v1` | Structured decision with proposals, evaluations, objections, votes, and a bound outcome | declared | semantic-deterministic | permanent | [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) |
| `macp.mode.proposal.v1` | Proposal and counterproposal negotiation | peer | semantic-deterministic | provisional | [RFC-MACP-0008](RFC-MACP-0008-proposal-mode.md) |
| `macp.mode.task.v1` | Bounded task delegation | orchestrated | structural-only | provisional | [RFC-MACP-0009](RFC-MACP-0009-task-mode.md) |
| `macp.mode.handoff.v1` | Responsibility transfer | delegated | context-frozen | provisional | [RFC-MACP-0010](RFC-MACP-0010-handoff-mode.md) |
| `macp.mode.quorum.v1` | Threshold approval or rejection | quorum | semantic-deterministic | provisional | [RFC-MACP-0011](RFC-MACP-0011-quorum-mode.md) |

## 11. Mode registration policy

Modes progress through a promotion lifecycle:

1. **Experimental** - early-stage, unstable, not interoperable. SHOULD use reverse-domain identifiers.
2. **Provisional** - published specification exists but schemas or semantics may still evolve. Listed in registries with reduced stability guarantees.
3. **Permanent** - stable schemas, at least one interoperable implementation, community review completed. Full backward-compatibility obligations apply.
4. **Deprecated** - no longer recommended for new sessions. Runtimes MAY continue to support deprecated Modes for replay purposes.

Promotion criteria:

- Experimental -> Provisional: published specification and initial schema definitions.
- Provisional -> Permanent: stable schemas, at least one interoperable implementation, and community review.
- Permanent -> Deprecated: replacement Mode available or security/design issues identified. Deprecation SHOULD include a migration guide and transition timeline.

## 12. Security and privacy

A Mode specification MUST state:

- who is allowed to emit terminal messages,
- what data classifications may appear in payloads,
- how sensitive payloads should be protected,
- what authority scope a `Commitment` carries,
- how external side effects are made idempotent.

## 13. Interoperability

Runtimes SHOULD reject unsupported Mode versions deterministically at `SessionStart` admission time. A Mode MUST NOT silently downgrade behavior without explicit negotiation.
