# RFC-MACP-0011
# Multi-Agent Coordination Protocol (MACP) - Quorum Mode

**Document:** RFC-MACP-0011
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.quorum.v1`, the standards-track MACP primitive for threshold approval or rejection. Quorum Mode is narrower than Decision Mode: it standardizes one approval request, participant ballots, and a `Commitment` once the threshold is satisfied or becomes impossible to satisfy.

## 1. Purpose

Quorum Mode is appropriate when one bounded action requires N-of-M approval rather than open-ended proposal comparison.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.quorum.v1`
- **Participant model:** `quorum`

The participant set MUST be declared at `SessionStart`, but resolution is based on a threshold rather than unanimity.

### 2.1 Authority Matrix

| Message Type | Authorized Sender |
|-------------|-------------------|
| `ApprovalRequest` | Session initiator (coordinator) |
| `Approve` | Any eligible declared participant |
| `Reject` | Any eligible declared participant |
| `Abstain` | Any eligible declared participant |
| `Commitment` | Session initiator (default) or policy-designated authority |

Each eligible participant MAY cast at most one ballot across `Approve`, `Reject`, or `Abstain`. Runtimes MUST reject messages from senders not authorized per this matrix.

## 3. SessionStart requirements

A Quorum Mode Session MUST bind:

- `participants` - eligible approvers,
- `mode_version` - quorum-mode semantic profile,
- `configuration_version` - approval threshold profile,
- `policy_version` - governance profile,
- `ttl_ms` - approval deadline,
- `context` - optional approval context.

Base Quorum Mode v1 assumes exactly one approval request per Session.

## 4. Message types

Quorum Mode defines the following mode-specific message types:

- **ApprovalRequest** - opens the approval request. Includes `request_id`, `action` (what is being approved), `summary` (human-readable description), optional `details` (binary context), and `required_approvals` (the approval threshold).
- **Approve** - records an approval ballot.
- **Reject** - records a rejection ballot.
- **Abstain** - records a neutral ballot.
- **Commitment** - authoritative terminal outcome.

## 5. Validation rules

Implementations MUST enforce the following:

1. A Session MUST accept at most one `ApprovalRequest` in base v1.
2. `required_approvals` MUST be greater than zero and MUST NOT exceed the count of eligible participants.
3. Each eligible participant MAY cast at most one ballot across `Approve`, `Reject`, or `Abstain`.
4. A Session becomes eligible for `Commitment` when approvals reach the required threshold, or when the remaining possible approvals can no longer reach that threshold.
4a. `Abstain` ballots do NOT count toward `required_approvals` and do NOT count as rejections. An abstaining participant is removed from the pool of potential approvers. Therefore, a Session becomes eligible for negative `Commitment` when `(remaining_eligible_participants + current_approvals) < required_approvals`, where `remaining_eligible_participants` excludes those who have already voted (approve, reject, or abstain).
4b. When all eligible participants have abstained (or a combination of abstentions and rejections makes the threshold unreachable), the Session becomes eligible for `Commitment` with a negative outcome (e.g., `action: quorum.rejected`). The `CommitmentPayload.reason` SHOULD indicate that the threshold was not met.
5. Only an authorized coordinator may emit the final `Commitment`.

## 6. Terminal semantics

Quorum Mode resolves only when an authorized `Commitment` is accepted.

Recommended `CommitmentPayload.action` values include:

- `quorum.approved`
- `quorum.rejected`

The `Commitment` SHOULD bind the approval request identifier and the threshold profile used.

### 6.1 Governance Policy

Quorum sessions MAY be governed by declarative policies that constrain approval thresholds, abstention handling, and commitment authority. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) for the governance policy framework and `schemas/json/policy/quorum-rules.schema.json` for the Quorum Mode rule schema.

## 7. Determinism class

Quorum Mode claims **semantic-deterministic** determinism.

Given the same participant set, the same approval threshold, the same accepted ballots, and the same bound versions, implementations MUST derive the same quorum state and the same commitment eligibility.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate each ballot sender,
- reject ballots from ineligible participants,
- ensure ballots cannot be counted twice,
- protect confidential approval context where necessary,
- preserve the exact accepted ballot history for audit and replay.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/quorum/v1/quorum.proto`
- `schemas/modes/quorum.proto`

Example transcript:

- `examples/quorum-mode-session.json`
