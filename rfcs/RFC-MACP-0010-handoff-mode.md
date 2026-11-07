# RFC-MACP-0010
# Multi-Agent Coordination Protocol (MACP) - Handoff Mode

**Document:** RFC-MACP-0010
**Version:** 1.3.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

> **Changelog — 1.3.0-draft:** New §6.1 states when a `Commitment` is ready, which §6 left implicit. A positive `Commitment` (`outcome_positive: true`) requires at least one offer accepted by a `HandoffAccept`, explicit or the synthetic accept of §5.1; a declined offer transfers nothing and does not satisfy it. A negative `Commitment` has no readiness precondition: it MAY be accepted with no offer ever made (the definitive no-target outcome §6 already allows), with an offer still pending, or after declines. A `Commitment` that is not ready is rejected with `INVALID_ENVELOPE` (RFC-MACP-0002 §6.1). The former §6.1 (Governance Policy) is now §6.2. Behaviour: the reference runtime accepted any `Commitment` once some offer had been accepted *or declined*, so it accepted a positive `Commitment` when the only offer had been declined, and it rejected every `Commitment`, negative included, while no offer had been settled. The positive rule tightens validation; the negative rule relaxes it. Pinned by `handoff_commitment_readiness.json` and `handoff_no_target_commitment.json`. **Replay:** the relaxation has no exposure, because a negative `Commitment` a runtime used to refuse never entered history. The tightening is exposed: `mode_version` stays `1.0.0`, and RFC-MACP-0003 §1 guarantees identical decisions only under identical validation rules, so a stored history that resolved with a positive `Commitment` after only a decline would be rejected by a runtime whose replay re-drives Mode validation under the new rule. Such a runtime needs to apply the old rule to sessions recorded under it, for example by gating it on a per-session semantics revision recorded at `SessionStart`.
>
> **Changelog — 1.2.1-draft:** §5 rule 3a's last sentence spoke of an offer that "expired unanswered under no implicit-accept policy", but Handoff Mode defines no per-offer expiry: without §5.1 an unanswered offer simply stays pending until the Session ends, and under §5.1 it is implicitly accepted rather than expired. The sentence now says what it meant: only an accepted `HandoffDecline` bars a target from a later offer. Clarification only. **Replay:** no exposure; no validation outcome changes.
>
> **Changelog — 1.2.0-draft:** Two changes. (1) §5 rule 3a's second sentence said a re-offer after a decline MUST name "a different `target_participant`" without saying different from what, and a runtime that enforced neither reading let an owner re-offer to a target that had just declined until it gave in. The sentence now bars, by name, any target that has declined an offer earlier in the Session, and names the rejection code (`INVALID_ENVELOPE`). An offer that expired unanswered with no implicit-accept policy does not bar its target. The "or is unreachable" clause is dropped: a target that never answers has not declined. (2) §5.1(2) no longer restates the obligation to append the synthetic `HandoffAccept` before evaluating the next envelope. It cites RFC-MACP-0001 §7.6 item 5 (Acceptance obligations), which now states it for every Mode's due synthetic envelopes and for every runtime, including one that embeds a library and has no `MACPRuntimeService` endpoint. Change (1) tightens validation: an offer to a previously declining target that a runtime used to accept is now rejected. Change (2) is a restatement and changes no behaviour. Source: seam-embedder-findings proposal S5 and S12, issue #185. **Replay:** change (1) is exposed. `mode_version` stays `1.0.0`, and RFC-MACP-0003 §1 guarantees identical accept/reject decisions only under identical validation rules. A stored history that already contains a re-offer to a declined target was accepted under the old wording; a runtime whose replay re-drives Mode validation under the new rule would reject that entry and diverge from the recorded outcome. A runtime that replays such histories needs to apply the old rule to sessions recorded under it, for example by gating the rule on a per-session semantics revision recorded at `SessionStart`. Histories without such a re-offer replay unchanged. Change (2) has no replay effect.
>
> **Changelog — 1.1.0-draft:** §5.1(2)'s closing sentence no longer reads as classification equivalence between the synthetic `HandoffAccept` and the `SessionSuspend`/`SessionResume`/`SessionCancel` envelopes it analogizes to — the analogy is narrowed to the replay-boundary property it actually supports, the `SessionCancel` citation is corrected from RFC-MACP-0001 §7.5 to RFC-MACP-0001 §7.3 (§7.5 covers only `SessionSuspend`/`SessionResume`), and the synthetic accept's own ordinal-consuming, stream-delivered classification (RFC-MACP-0006 §3.2) is now stated directly rather than left to a reader's inference. No behavior change — the synthetic accept's actual classification is unchanged; only what this sentence claims about it is corrected (issue #160).

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
3a. A `HandoffOffer.target_participant` MUST NOT be changed after the offer is accepted into session history. If the target declines, a new `HandoffOffer` MUST carry a new `handoff_id` and a `target_participant` that has not previously declined an offer in this Session; a runtime MUST reject it with `INVALID_ENVELOPE` otherwise. Only an accepted `HandoffDecline` bars a target. Handoff Mode defines no per-offer expiry: without an implicit-accept policy an unanswered offer stays pending (rule 5) until the Session ends, and under §5.1 it is implicitly accepted, not expired. An offer that was never declined therefore bars no one.
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

2. **The synthetic accept enters history.** Once the deadline has elapsed,
   the synthetic `HandoffAccept` is a due synthetic envelope in the sense of
   RFC-MACP-0001 §7.6 item 5 (Acceptance obligations), and that item governs
   when it is appended: before the runtime evaluates the next session-scoped
   envelope, and therefore **before any `Commitment` evaluation** that depends
   on the offer being accepted. Observing the deadline at that evaluation is
   sufficient; a timer or sweep is RECOMMENDED but not required. Because the synthetic accept is an accepted history entry, replay simply replays it: the timer itself is outside the replay boundary, its recorded product is inside — the same replay-boundary property as any runtime-authored entry that enters the log, such as the `SessionSuspend`/`SessionResume` annotations of RFC-MACP-0001 §7.5 and the `SessionCancel` annotation of RFC-MACP-0001 §7.3. This entry's *classification* for ordinal-consumption and stream delivery is a separate question, governed by RFC-MACP-0006 §3.2, and is unrelated to this replay-boundary property — unlike those three envelopes, the synthetic `HandoffAccept` is an ordinary accepted Mode message: it consumes an accepted ordinal and is delivered on a subscribe stream like any other accepted envelope.

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

### 6.1 Commitment readiness

A `Commitment` is evaluated against the offers in accepted history at its acceptance time, after any synthetic `HandoffAccept` due at that time has been appended (§5.1(2)).

1. A positive `Commitment` (`outcome_positive: true`) MUST be rejected with `INVALID_ENVELOPE` unless at least one `HandoffOffer` in the Session has been accepted by a `HandoffAccept`, explicit or synthetic (§5.1). A declined offer does not satisfy this rule, and neither does a pending one.
2. A negative `Commitment` (`outcome_positive: false`) has no readiness precondition. It MUST NOT be rejected on the ground that no offer was made, that an offer is pending, or that every offer was declined. In particular, a Session in which no `HandoffOffer` was ever accepted MAY resolve with a negative `Commitment` that binds a definitive no-target outcome.

These are Mode validation rules, not policy evaluation: neither depends on a bound policy, so a breach uses `INVALID_ENVELOPE`, never `POLICY_DENIED` (RFC-MACP-0002 §6.1). They run before governance-policy evaluation (RFC-MACP-0012 §6.4), and sender authorization (§2.1) runs before both.

### 6.2 Governance Policy

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
