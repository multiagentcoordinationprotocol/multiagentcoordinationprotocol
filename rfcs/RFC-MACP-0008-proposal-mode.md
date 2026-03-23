# RFC-MACP-0008
# Multi-Agent Coordination Protocol (MACP) - Proposal Mode

**Document:** RFC-MACP-0008
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.proposal.v1`, a bounded negotiation primitive for proposals and counterproposals. Proposal Mode is the main-repo standard for offer, counteroffer, acceptance, rejection, and withdrawal inside a MACP Session.

## 1. Purpose

Proposal Mode standardizes a common negotiation shape without forcing the heavier semantics of Decision Mode. It is intended for situations where participants are refining terms rather than collecting evaluations from a larger decision body.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.proposal.v1`
- **Participant model:** `peer`

The participant roles are symmetric, but the participant set MUST still be bound at `SessionStart`.

## 3. SessionStart requirements

A Proposal Mode Session MUST bind:

- `participants` - required negotiating parties,
- `mode_version` - proposal-mode semantic profile,
- `configuration_version` - optional rule profile,
- `policy_version` - optional governance profile,
- `ttl_ms` - explicit negotiation deadline,
- `context` - optional negotiation context.

Unless policy states otherwise, the session initiator is the default `Commitment` authority.

## 4. Message types

Proposal Mode defines the following mode-specific message types:

- **Proposal** - submits an initial offer.
- **CounterProposal** - submits a replacement or revised offer.
- **Accept** - accepts a specific proposal.
- **Reject** - rejects a specific proposal and MAY mark the rejection as terminal.
- **Withdraw** - withdraws a previously submitted proposal.
- **Commitment** - authoritative terminal outcome.

## 5. Validation rules

Implementations MUST enforce the following:

1. Every `proposal_id` MUST be unique within the Session.
2. `CounterProposal.supersedes_proposal_id` MUST reference an existing proposal.
3. `Accept`, `Reject`, and `Withdraw` MUST reference an existing proposal.
4. A withdrawn proposal MUST NOT later be accepted or committed.
5. A participant MAY change its acceptance target by sending a later `Accept` for a different live proposal. The latest accepted `Accept` from a participant supersedes earlier accepts from the same participant.
6. A Session becomes eligible for `Commitment` when all required participants have accepted the same live proposal, or when a terminal rejection is recorded and the authority chooses to bind that rejection.

## 6. Terminal semantics

Proposal Mode resolves only when an authorized `Commitment` is accepted.

Successful commitments SHOULD bind the accepted proposal by referencing it in the `CommitmentPayload.reason` or associated context. Negative commitments MAY bind a definitive rejected outcome, for example `proposal.rejected`, when a terminal reject has been accepted into history.

## 7. Determinism class

Proposal Mode claims **semantic-deterministic** determinism.

Given the same accepted history and the same version-bound rules, implementations MUST derive the same live proposal set, the same acceptance set, and the same commitment eligibility.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate participants before accepting proposals or acceptances,
- reject commits from unauthorized senders,
- prevent proposal confusion attacks where accepts refer to unknown or withdrawn proposals,
- protect sensitive proposal details when payloads contain confidential commercial or operational data.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/proposal/v1/proposal.proto`
- `schemas/modes/proposal.proto`

Example transcript:

- `examples/proposal-mode-session.json`
