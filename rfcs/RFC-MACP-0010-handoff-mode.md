# RFC-MACP-0010
# Multi-Agent Coordination Protocol (MACP) - Handoff Mode

**Document:** RFC-MACP-0010
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.handoff.v1`, the standards-track MACP primitive for transferring scoped responsibility from one participant to another. Handoff Mode lets the current owner offer responsibility, provide context, and bind a successful or definitive unsuccessful outcome with `Commitment`.

## 1. Purpose

Handoff Mode exists for responsibility transfer, not ordinary task assignment. The semantic distinction is that the receiving participant is expected to assume authority or ownership over an ongoing responsibility, not simply execute a bounded sub-task.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.handoff.v1`
- **Participant model:** `delegated`

The current owner or a policy-defined coordinator is the default `Commitment` authority.

## 3. SessionStart requirements

A Handoff Mode Session SHOULD bind:

- `participants` - current owner and eligible targets,
- `mode_version` - handoff semantic profile,
- `configuration_version` - transfer profile,
- `policy_version` - authority policy,
- `ttl_ms` - deadline for the transfer,
- `context` and `roots` - any frozen handoff context or trust boundary needed for replay.

## 4. Message types

Handoff Mode defines the following mode-specific message types:

- **HandoffOffer** - proposes transfer to a target participant.
- **HandoffContext** - attaches supplemental context to a handoff offer.
- **HandoffAccept** - target accepts the offered transfer.
- **HandoffDecline** - target declines the offered transfer.
- **Commitment** - authoritative terminal outcome.

## 5. Validation rules

Implementations MUST enforce the following:

1. Every `handoff_id` MUST identify one specific handoff offer.
2. `HandoffContext`, `HandoffAccept`, and `HandoffDecline` MUST reference an existing `handoff_id`.
3. `HandoffAccept` and `HandoffDecline` MUST come from the offer's `target_participant`.
4. Once an offer has been accepted, no competing accept for that same `handoff_id` is valid.
5. A Session MAY contain multiple serial handoff offers, but only one final `Commitment` may resolve the Session.

## 6. Terminal semantics

Handoff Mode resolves only when an authorized `Commitment` is accepted.

Positive commitments SHOULD make the transfer explicit, for example `handoff.accepted`, and SHOULD bind the new responsibility holder in the reason or bound context. Negative commitments MAY bind a definitive no-target or declined outcome if policy requires an explicit failure record.

## 7. Determinism class

Handoff Mode claims **context-frozen** determinism.

The meaning of a handoff depends on the exact bound context, authority scope, and roots disclosed at `SessionStart`. Replay is semantically meaningful only if that frozen context is reproduced.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate both the current owner and the target participant,
- protect sensitive handoff context payloads,
- ensure only authorized actors can bind the final transfer with `Commitment`,
- prevent transfer confusion where context is attached to the wrong offer,
- preserve auditable accepted history for downstream accountability.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/handoff/v1/handoff.proto`
- `schemas/modes/handoff.proto`

Example transcript:

- `examples/handoff-mode-session.json`
