# RFC-MACP-0007
# Multi-Agent Coordination Protocol (MACP) - Decision Mode

**Document:** RFC-MACP-0007
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.decision.v1`, the standards-track Decision Mode for bounded multi-party decisions. Decision Mode lets declared participants submit proposals, evaluations, objections, and votes, and it terminates with a single authoritative `Commitment`. The accepted `SessionStart` sender (session initiator/coordinator) may also be separately authorized to emit `Proposal` and `Commitment`.

## 1. Purpose

Decision Mode is the foundational MACP primitive for convergent choice. It is appropriate when participants need to compare options and produce a single bound outcome inside one Session.

Decision Mode is intentionally narrower than a general workflow engine:

- it standardizes transcript semantics,
- it does not standardize one universal scoring or voting algorithm,
- decision policy is bound through `mode_version`, `configuration_version`, and `policy_version` at `SessionStart`.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.decision.v1`
- **Participant model:** `declared`

The eligible participant set is bound at `SessionStart`. The session initiator (accepted `SessionStart` sender) MUST be included in the `participants` list if they intend to emit `Proposal`, `Evaluation`, `Objection`, or `Vote` messages. The session initiator is the default `Commitment` authority regardless of participant list membership, unless a stricter policy is bound by configuration or policy.

### 2.1 Authority Matrix

The following table defines which participants are authorized to emit each message type:

| Message Type | Authorized Sender |
|-------------|-------------------|
| `Proposal` | Any declared participant |
| `Evaluation` | Any declared participant |
| `Objection` | Any declared participant |
| `Vote` | Any declared participant (at most one per proposal per participant in base v1) |
| `Commitment` | Session initiator (default) or policy-designated authority |

Runtimes MUST reject messages from senders not authorized per this matrix.

## 3. SessionStart requirements

A Decision Mode Session MUST bind the following fields explicitly in `SessionStartPayload`:

- `participants` - decision participants,
- `mode_version` - the decision-mode semantic profile,
- `configuration_version` - voting or evaluation profile,
- `policy_version` — governance profile (MAY be empty; when empty, the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
- `ttl_ms` - explicit decision deadline,
- `context` - optional bound decision context.

## 4. Message types

Decision Mode defines the following mode-specific message types:

- **Proposal** - creates an option for consideration.
- **Evaluation** - records analysis of a proposal.
  Valid recommendation values are: `APPROVE`, `REVIEW`, `BLOCK`, `REJECT`. `REVIEW` indicates that the evaluator has analyzed the proposal but does not issue a definitive recommendation — it is semantically equivalent to "analyzed, no strong stance." `REVIEW` evaluations do not block or approve a proposal; they serve as informational analysis records only.
- **Objection** - records a concern or blocking issue.

An Evaluation with `BLOCK` recommendation is an advisory assessment indicating the evaluator recommends against proceeding. An `Objection` is a formal blocking action with a severity level (`low`, `medium`, `high`, `critical`). Only Objections are subject to `objection_handling` governance rules (e.g., `critical_severity_vetoes`). A `BLOCK` evaluation does not trigger veto logic.

- **Vote** - records a participant preference. Valid vote values are: `APPROVE`, `REJECT`, `ABSTAIN`. The semantics of abstention (e.g., impact on quorum and outcome calculation) are defined by the decision policy bound at `SessionStart`. When no policy is bound, abstentions do not count toward any threshold.

All enum-like string values in Decision Mode use UPPER_CASE. Comparisons MUST be case-sensitive.
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

Decision Mode allows both positive and negative committed outcomes. `CommitmentPayload.outcome_positive` MUST be set explicitly on all Decision Mode commitments.

### 6.1 Governance Policy

Decision sessions MAY be governed by declarative policies that constrain voting algorithms, quorum requirements, objection handling, and commitment authority. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) for the governance policy framework and `schemas/json/policy/decision-rules.schema.json` for the Decision Mode rule schema.

## 7. Determinism class

Decision Mode claims **semantic-deterministic** determinism.

Given the same accepted message history, the same participant set, and the same bound mode/configuration/policy versions, the same semantic outcome MUST be produced.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate the sender of each `Proposal`, `Evaluation`, `Objection`, `Vote`, and `Commitment`,
- reject Decision Mode messages from unauthorized senders, distinguishing declared-participant authority from any separately bound coordinator authority,
- protect confidential decision context and proposal data,
- ensure only authorized actors can emit `Commitment`,
- preserve append-only accepted history for audit and replay.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/decision/v1/decision.proto`
- `schemas/modes/decision.proto`

Example transcript:

- `examples/decision-mode-session.json`
