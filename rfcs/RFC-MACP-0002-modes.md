# RFC-MACP-0002
# Multi-Agent Coordination Protocol (MACP) — Coordination Modes

**Document:** RFC-MACP-0002  
**Version:** 1.0.0-draft  
**Status:** Community Standards Track  
**Updates:** RFC-MACP-0001

## Abstract

Coordination Modes define semantic behavior inside MACP Sessions. MACP Core defines structure; Modes define meaning. This document specifies how Modes are identified, described, negotiated, registered, versioned, and constrained.

## 1. Scope

A Mode specification defines:

- its identifier and version,
- its additional message types,
- participant rules,
- termination conditions,
- determinism claims,
- commitment semantics,
- payload schemas,
- security considerations.

Modes MUST NOT violate MACP Core invariants.

## 2. Mode Identifiers

Standard Mode identifiers SHOULD use the form:

`macp.mode.<name>.v<major>`

Experimental Modes SHOULD use reverse-domain names to avoid collisions.

## 3. Mode Descriptor

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

## 4. Participant Models

This specification recognizes common participant models:

- **declared** — participant set bound at SessionStart,
- **quorum** — a subset of eligible participants may terminate,
- **orchestrated** — one actor coordinates specialists,
- **peer** — all participants are symmetric,
- **delegated** — participants may speak for sub-capabilities or delegated roles.

A Mode MUST declare which participant model it uses.

## 5. Terminal Semantics

Core requires sessions to terminate, but Core does not require all Modes to emit a Commitment. A Mode MUST declare:

- whether authoritative Commitment messages are required,
- what constitutes a terminal condition,
- whether terminal conditions are unique or can take multiple forms.

## 6. Determinism Claims

A Mode MUST declare one of the following determinism classes:

- **structural-only** — Core replay is preserved but semantic outcome is not guaranteed,
- **semantic-deterministic** — same accepted history produces the same semantic outcome,
- **context-frozen** — semantic determinism holds only if external context bound at SessionStart is replayed exactly,
- **non-deterministic** — runtime or external side effects may change semantic outcomes.

The full determinism and replay integrity model is specified in [RFC-MACP-0003](RFC-MACP-0003-determinism.md).

## 7. Semantic Idempotency

Core deduplicates messages by `message_id`, but a Mode MUST define idempotency for semantic actions that can escape the runtime boundary (for example tool execution, transaction initiation, or external write requests).

## 8. Standard Example: Decision Mode

This RFC registers `macp.mode.decision.v1` as an initial standard example Mode.

Decision Mode supports a bounded decision workflow in which participants submit proposals, evaluations, objections, or votes, and the session terminates with a Commitment.

### 8.1 Message Types

Decision Mode defines the following Mode-specific message types (from `decision.proto`):

- **Proposal** — submits an option for consideration
- **Evaluation** — provides analysis of a proposal
- **Objection** — raises a concern about a proposal
- **Vote** — expresses a preference

In addition, Decision Mode reuses the Core `Commitment` message type as its terminal message.

### 8.2 Participant Model

Decision Mode uses the **declared** participant model. The participant set is bound at `SessionStart` and MUST NOT change during the session.

### 8.3 Terminal Conditions

A Decision Mode session terminates when a `Commitment` message is accepted. Only the designated orchestrator (or the participant authorized by Mode policy) MAY emit a Commitment.

### 8.4 Determinism Class

Decision Mode claims **semantic-deterministic** determinism. Given the same accepted message history and the same mode/policy/configuration versions, the same binding outcome MUST be produced. However, the decision profile (e.g., voting thresholds, quorum rules) is configuration-dependent.

### 8.5 Canonical Schemas

Canonical schemas are provided in:

- `schemas/proto/macp/modes/decision/v1/decision.proto`
- `schemas/modes/decision.proto`

## 9. Mode Registration Policy

Modes progress through a promotion lifecycle:

1. **Experimental** — early-stage, unstable, not interoperable. SHOULD use reverse-domain identifiers.
2. **Provisional** — published specification exists but schemas may change. Listed in registries with reduced stability guarantees.
3. **Permanent** — stable schemas, at least one interoperable implementation, community review completed. Full backward-compatibility obligations apply.
4. **Deprecated** — no longer recommended for new sessions. Runtimes MAY continue to support deprecated Modes for replay purposes.

**Promotion criteria:**

- Experimental → Provisional: published specification and initial schema definitions.
- Provisional → Permanent: stable schemas, at least one interoperable implementation, and community review.
- Permanent → Deprecated: replacement Mode available or security/design issues identified. Deprecation SHOULD include a migration guide and transition timeline.

## 10. Security and Privacy

A Mode specification MUST state:

- who is allowed to emit terminal messages,
- what data classifications may appear in payloads,
- how sensitive payloads should be protected,
- any authority-scope restrictions on Commitments.

## 11. Interoperability

Runtimes SHOULD reject unsupported Mode versions deterministically at SessionStart admission time. A Mode MUST NOT silently downgrade behavior without explicit negotiation.
