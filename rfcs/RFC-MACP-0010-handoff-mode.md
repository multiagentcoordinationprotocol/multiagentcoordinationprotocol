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
- **Participant model:** `delegated` — one party (the current responsibility owner) offers authority transfer to a specific named recipient. Only the current owner can emit `HandoffOffer` messages; only the named target can accept or decline.

The accepted `SessionStart` sender is the current responsibility owner and the default `Commitment` authority. Policy MAY delegate commitment authority to a separate coordinator role.

### 2.1 Authority Matrix

| Message Type | Authorized Sender |
|-------------|-------------------|
| `HandoffOffer` | Current responsibility owner (session initiator) |
| `HandoffContext` | Current responsibility owner |

`HandoffContext` SHOULD be sent before `HandoffAccept` or `HandoffDecline` for the referenced `handoff_id`. Late context (sent after the target has already accepted or declined) is permitted but serves only as supplementary documentation, not as input to the accept/decline decision.

| `HandoffAccept` | Target participant of the referenced offer |
| `HandoffDecline` | Target participant of the referenced offer |
| `Commitment` | Current responsibility owner (default) or policy-designated authority |

Runtimes MUST reject messages from senders not authorized per this matrix.

## 3. SessionStart requirements

A Handoff Mode Session MUST bind:

- `participants` - current owner and eligible targets,
- `mode_version` - handoff semantic profile,
- `configuration_version` - transfer profile,
- `policy_version` — governance profile (MAY be empty; when empty, the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
- `ttl_ms` - deadline for the transfer,
- `context_id`, `extensions`, and `roots` - any frozen handoff context reference, attached data, or trust boundary needed for replay.

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
3a. A `HandoffOffer.target_participant` MUST NOT be changed after the offer is accepted into session history. If the target declines or is unreachable, a new `HandoffOffer` MUST be issued with a different `target_participant` and a new `handoff_id`.
4. Once an offer has been accepted, no competing accept for that same `handoff_id` is valid.
5. A Session MAY contain multiple sequential handoff offers to different targets. At most one offer may be outstanding (unaccepted and undeclined) at any time. A new `HandoffOffer` MUST NOT be issued while a prior offer is still pending. Once an offer is accepted, no further offers may be issued for the Session. Only one final `Commitment` may resolve the Session.

### 5.1 Implicit acceptance (synthetic accept)

A bound governance policy MAY declare `acceptance.implicit_accept_timeout_ms`
(RFC-MACP-0012 §4.5). When it is non-zero, an outstanding offer that the
target has neither accepted nor declined within the timeout is accepted
implicitly, under the following contract:

1. **Timing source.** The timeout is measured on the **session timeline**
   from the runtime's recorded acceptance time of the `HandoffOffer` (the
   offer log entry's acceptance timestamp) — never from client-supplied
   envelope timestamps, which are forgeable. Time during which the session
   is `SUSPENDED` does **not** count toward the timeout: the deadline is
   reached when the *unsuspended* elapsed session time since offer
   acceptance meets or exceeds the timeout. Every input to this computation
   (the offer's recorded acceptance time and the suspend/resume events) is
   on the recorded timeline.

2. **The synthetic accept enters history.** When the runtime first observes
   the deadline elapsed, it MUST append a synthetic `HandoffAccept` envelope
   to the session's accepted history — before evaluating any subsequent
   message against the offer's acceptance state, and in particular **before
   any `Commitment` evaluation** that depends on the offer being accepted. A
   runtime SHOULD observe the deadline eagerly (a timer or sweep, like TTL
   expiry); it MUST observe it lazily at the latest when processing the next
   session-scoped message. Because the synthetic accept is an accepted
   history entry, replay simply replays it: the timer itself is outside the
   replay boundary, its recorded product is inside — the same construction
   as runtime-emitted `SessionSuspend`/`SessionResume`/`SessionCancel`
   envelopes (RFC-MACP-0001 §7.5).

3. **Envelope convention.** The synthetic accept is runtime-emitted; clients
   MUST NOT submit it via `Send`. Its Envelope `sender` is the offer's
   `target_participant` (acceptance occurs on the target's behalf, keeping
   validation rule 3 coherent), `HandoffAcceptPayload.implicit` MUST be
   `true`, and `accepted_by` MUST be the target. The Envelope
   `timestamp_unix_ms` SHOULD be the computed deadline (offer acceptance
   time + timeout + suspended time within the window), not the observation
   time. The `message_id` MUST be deterministic per offer (RECOMMENDED:
   `implicit-accept:<handoff_id>`), making emission idempotent under
   at-least-once processing. A client-submitted `HandoffAccept` carrying
   `implicit: true` MUST be rejected.

4. **Races resolve by history order.** An explicit `HandoffAccept` or
   `HandoffDecline` accepted into history before the synthetic accept
   settles the offer, and the synthetic accept is then never emitted. Once
   the synthetic accept is in history, a later decline is invalid (rule 4).

## 6. Terminal semantics

Handoff Mode resolves only when an authorized `Commitment` is accepted.

Positive commitments SHOULD make the transfer explicit, for example `handoff.accepted`, and SHOULD bind the new responsibility holder in the reason or bound context. Negative commitments MAY bind a definitive no-target or declined outcome if policy requires an explicit failure record.

Handoff Mode allows negative committed outcomes (declined or no-target). `CommitmentPayload.outcome_positive` MUST be set explicitly on all Handoff Mode commitments.

### 6.1 Governance Policy

Handoff sessions MAY be governed by declarative policies that constrain acceptance timeouts and commitment authority. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) for the governance policy framework and `schemas/json/policy/handoff-rules.schema.json` for the Handoff Mode rule schema.

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
