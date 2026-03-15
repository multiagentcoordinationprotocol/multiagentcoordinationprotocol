# RFC-MACP-0011
# Multi-Agent Coordination Protocol (MACP) - Quorum Mode

**Document:** RFC-MACP-0011
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.quorum.v1`, the standards-track MACP primitive for threshold approval or rejection. Quorum Mode is narrower than Decision Mode: it standardizes one approval request, participant ballots, and a commitment once the threshold is satisfied or becomes impossible to satisfy.

## 1. Purpose

Quorum Mode is appropriate when one bounded action requires N-of-M approval rather than open-ended proposal comparison.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.quorum.v1`
- **Participant model:** `quorum`

The participant set is typically declared at `SessionStart`, but resolution is based on a threshold rather than unanimity.

## 3. SessionStart requirements

A Quorum Mode Session SHOULD bind:

- `participants` - eligible approvers,
- `mode_version` - quorum-mode semantic profile,
- `configuration_version` - approval threshold profile,
- `policy_version` - governance profile,
- `ttl_ms` - approval deadline,
- `context` - optional approval context.

Base Quorum Mode v1 assumes exactly one approval request per Session.

## 4. Message types

Quorum Mode defines the following mode-specific message types:

- **ApprovalRequest** - opens the approval request and states the threshold.
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
5. Only an authorized coordinator may emit the final `Commitment`.

## 6. Terminal semantics

Quorum Mode resolves only when an authorized `Commitment` is accepted.

Recommended `CommitmentPayload.action` values include:

- `quorum.approved`
- `quorum.rejected`

The commitment SHOULD bind the approval request identifier and the threshold profile used.

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
