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

Participant model: `peer` — participants have symmetric negotiation authority (all may Propose, CounterPropose, Accept, Reject). Commitment authority defaults to the session initiator unless overridden by policy.

### 2.1 Authority Matrix

| Message Type | Authorized Sender |
|-------------|-------------------|
| `Proposal` | Any declared participant |
| `CounterProposal` | Any declared participant |
| `Accept` | Any declared participant |
| `Reject` | Any declared participant |
| `Withdraw` | The author of the referenced proposal or counter-proposal. A `CounterProposal` creates a new `proposal_id`; only the sender of that `CounterProposal` may withdraw it. |
| `Commitment` | Session initiator (default) or policy-designated authority |

Runtimes MUST reject messages from senders not authorized per this matrix.

## 3. SessionStart requirements

A Proposal Mode Session MUST bind:

- `participants` - required negotiating parties,
- `mode_version` - proposal-mode semantic profile,
- `configuration_version` — rule profile for negotiation parameters,
- `policy_version` — governance profile (MAY be empty; when empty, the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
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
2a. A `CounterProposal` creates a new `proposal_id`. The `supersedes_proposal_id` field records semantic intent (the counteroffer is meant to replace the referenced proposal) but does NOT automatically retire the original proposal. Participants MAY accept either the original or the counteroffer. Implementations MUST track all live proposals independently.
3. `Accept`, `Reject`, and `Withdraw` MUST reference an existing proposal.
4. A withdrawn proposal MUST NOT later be accepted or committed.
5. A participant MAY change its acceptance target by sending a later `Accept` for a different live proposal. The latest accepted `Accept` from a participant supersedes earlier accepts from the same participant.
6. A Session becomes eligible for `Commitment` when all required participants have accepted the same live proposal, or when a `Reject` with `terminal=true` has been accepted. The Commitment authority (session initiator by default, or as overridden by policy) MAY emit `Commitment` to bind either a successful acceptance or a definitive rejection. The Commitment authority MAY choose not to bind a terminal rejection and MAY await further proposals instead.

In the base case (no policy override), 'required participants' means all declared participants in the `SessionStart.participants` list.

## 6. Terminal semantics

Proposal Mode resolves only when an authorized `Commitment` is accepted.

Successful commitments SHOULD bind the accepted proposal by referencing it in the `CommitmentPayload.reason` or associated context. Negative commitments MAY bind a definitive rejected outcome, for example `proposal.rejected`, when a terminal reject has been accepted into history.

### 6.1 Governance Policy

Proposal sessions MAY be governed by declarative policies that constrain acceptance criteria, negotiation rounds, and commitment authority. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) for the governance policy framework and `schemas/json/policy/proposal-rules.schema.json` for the Proposal Mode rule schema.

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
