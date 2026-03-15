# RFC-MACP-0007
# Multi-Agent Coordination Protocol (MACP) - Decision Mode

**Document:** RFC-MACP-0007
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.decision.v1`, the standards-track Decision Mode for bounded multi-party decisions. Decision Mode lets declared participants submit proposals, evaluations, objections, and votes, and it terminates with a single authoritative `Commitment`.

## 1. Purpose

Decision Mode is the foundational MACP primitive for convergent choice. It is appropriate when participants need to compare options and produce a single bound outcome inside one Session.

Decision Mode is intentionally narrower than a general workflow engine:

- it standardizes transcript semantics,
- it does not standardize one universal scoring or voting algorithm,
- decision policy is bound through `mode_version`, `configuration_version`, and `policy_version` at `SessionStart`.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.decision.v1`
- **Participant model:** `declared`

The eligible participant set is bound at `SessionStart`. Only declared participants MAY emit Decision Mode messages.

## 3. SessionStart requirements

A Decision Mode Session SHOULD bind the following fields explicitly in `SessionStartPayload`:

- `participants` - decision participants,
- `mode_version` - the decision-mode semantic profile,
- `configuration_version` - voting or evaluation profile,
- `policy_version` - decision policy or governance profile,
- `ttl_ms` - explicit decision deadline,
- `context` - optional bound decision context.

## 4. Message types

Decision Mode defines the following mode-specific message types:

- **Proposal** - creates an option for consideration.
- **Evaluation** - records analysis of a proposal.
- **Objection** - records a concern or blocking issue.
- **Vote** - records a participant preference.
- **Commitment** - authoritative terminal outcome.

Canonical payloads are defined in `decision.proto`.

## 5. Validation rules

Implementations of `macp.mode.decision.v1` MUST enforce the following:

1. `Proposal.proposal_id` MUST be unique within the Session.
2. `Evaluation`, `Objection`, and `Vote` MUST reference an existing `proposal_id`.
3. A participant MAY cast at most one `Vote` per `proposal_id` unless a stricter or more permissive rule is explicitly bound in configuration. Base Decision Mode v1 assumes one vote per participant per proposal.
4. The runtime or policy authority MUST reject `Commitment` from unauthorized senders.
5. The Session MUST NOT resolve before at least one proposal exists unless policy explicitly allows a no-go outcome with zero proposals.

## 6. Terminal semantics

Decision Mode resolves when an authorized `Commitment` is accepted.

The `CommitmentPayload` SHOULD identify:

- the selected action,
- the authority scope,
- the `mode_version`, `configuration_version`, and `policy_version` that governed the decision,
- a reason that can be replayed and audited.

The mode does not prescribe a single voting algorithm. A runtime or deployment may use majority vote, weighted vote, objection handling, veto rules, or another deterministic policy, provided that the policy is version-bound and replay-safe.

## 7. Determinism class

Decision Mode claims **semantic-deterministic** determinism.

Given the same accepted message history, the same participant set, and the same bound mode/configuration/policy versions, the same semantic outcome MUST be produced.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate the sender of each evaluation, objection, vote, and commitment,
- reject messages from non-participants,
- protect confidential decision context and proposal data,
- ensure only authorized actors can emit `Commitment`,
- preserve append-only accepted history for audit and replay.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/decision/v1/decision.proto`
- `schemas/modes/decision.proto`

Example transcript:

- `examples/decision-mode-session.json`
