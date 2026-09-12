# RFC-MACP-0007
# Multi-Agent Coordination Protocol (MACP) - Decision Mode

**Document:** RFC-MACP-0007
**Version:** 1.3.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

> **Changelog — 1.3.0-draft:** §5 gains a sixth validation rule — **deliberation closes when voting begins** — requiring a runtime to reject any `Proposal`, `Evaluation` or `Objection` arriving after the first accepted `Vote`. This **pins behavior the reference runtime already implements** for all three message types, but the three arms were not equally covered before, and the difference matters to anyone implementing against the corpus rather than against the runtime. The `Evaluation` arm was already asserted executably — `schemas/conformance/decision_reject_paths.json` has pinned exactly that rejection since the corpus was runtime-verified — so for that arm this revision introduces no new rejection behavior and merely supplies the rule the corpus was asserting against nothing (issue #108). The `Objection` arm existed only as narrative inside a `_comment` in `decision_critical_objection_veto.json`, which asserts nothing executable, and the post-vote `Proposal` arm had **no** coverage at all; fixtures for both are added in this same revision. A runtime that had implemented only the Evaluation arm was passing the corpus and must now handle the other two. The rule deliberately covers all three rather than `Evaluation` alone, because an Evaluation-only rule would leave the reference runtime's `Proposal` and `Objection` rejections unsupported by any normative text. Rejections use `INVALID_ENVELOPE` per [RFC-MACP-0002](RFC-MACP-0002-modes.md) §6.1, which is the only conformant code: the sender is authorized so `FORBIDDEN` is wrong, and `POLICY_DENIED` is unproducible for a non-`Commitment`. **Replay: neutral for every conformant stored session, with one bounded exposure stated rather than argued away.** For a runtime that already implemented all three arms — which the reference runtime does — nothing changes: it never accepted such a message, so no stored history contains one. The exposure is the runtime that implemented only the Evaluation arm and was nevertheless passing the corpus, because the corpus did not constrain the other two. Such a runtime may hold a stored session whose accepted history contains a post-vote `Proposal` or `Objection`. [RFC-MACP-0003](RFC-MACP-0003-determinism.md) §1 conditions replay reproduction on *identical validation rules and bound versions*, and this revision changes a validation rule without a `mode_version` bump, so that precondition does not hold for those histories: replaying one against rule 6 would reject a message the original run accepted. The affected messages are **not** inert, and this revision does not pretend otherwise: an accepted post-vote critical `Objection` can fire a `critical_severity_vetoes` veto that rule 6 now prevents, flipping both the commitment outcome and the terminal state on replay, and an accepted post-vote `Proposal` enlarges the option set that later `Vote`s reference. The break is nevertheless accepted, on the strongest of the reasons [RFC-MACP-0012](RFC-MACP-0012-policy.md) §8's bounded exception gives — **the behavior being broken was itself unsound**. Admitting post-vote deliberation lets two conforming implementations derive different commitment eligibility from history that was identical at the time each ballot was cast, which is what Section 7's semantic-determinism claim forbids; such histories were therefore never replay-safe against a conformant peer to begin with. The exposure is also confined to runtimes diverging on one or both of the uncovered arms. A `mode_version` bump was weighed and declined — **not** because it would invalidate stored sessions, which it would not: [RFC-MACP-0003](RFC-MACP-0003-determinism.md) §3 requires replay to use the versions bound at `SessionStart`, so stored `1.0.0` sessions would continue to replay under `1.0.0`. It was declined because it imposes ecosystem-wide rebinding churn to preserve histories no conformant runtime produced. Implementations that may hold such histories should re-examine them before adopting this revision. [RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3 is unaffected either way: it fixes accepted history as immutable and keeps rejected envelopes out of it, and rule 6 changes only what a runtime accepts from here on.
>
> Also in 1.3.0-draft, §6.2 resolves an ambiguity in the **objection-authorized decline** (issue #117). The decline guard is a two-conjunct conjunction, and §6.2 waives "the decline guard" without saying whether the waiver reaches the `require_vote_quorum` conjunct. It does: the waiver covers the guard whole, and the `evaluation.*` prerequisites are waived with it. The governing principle is authorization provenance — the quorum condition legitimizes an outcome deriving its authority from the voting result, and an objection-authorized decline derives none. The strict reading is not a conservative choice but the failure mode itself: it reconstructs the stuck state this channel exists to remove. §6.2's claim that such a session "could terminate only by expiry" is also corrected — the initiator can submit `CancelSession` at any time, and a lone `ABSTAIN` clears a count-1 floor; what is unreachable is a **committed outcome**, not termination. This changes behavior for one configuration family (a met critical-severity veto with `finalize_decline` and an unmet floor, where a negative `Commitment` moves from denied to allowed) but is replay-neutral in the same [RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3 sense: a runtime that denied it rejected the message, and rejected messages never enter accepted history.
>
> **Changelog — 1.2.0-draft:** §5 rule 5 drops its "unless policy explicitly allows a no-go outcome with zero proposals" clause. No published rule schema ever defined a field that could express that allowance, and every channel that can authorize a NEGATIVE commitment requires an existing `proposal_id`, so no conforming configuration could exercise the clause and its deletion changes no conforming implementation's behavior; [RFC-MACP-0012](RFC-MACP-0012-policy.md) §8 is not engaged because no conforming stored session can contain a zero-proposal Commitment. §5 now states explicitly that every commitment path presupposes an accepted proposal and that a zero-proposal session terminates only by `SessionCancel` or expiry; §6.2's face-value exception is annotated to note that it waives the decline guard, not rule 5.
>
> §2 gains a **Zero declared participants** note, specializing §5's general statement to the zero-participant case beside the Authority Matrix it derives from. It reaches that conclusion via rule 5 rather than asserting unresolvability as a primitive — issue #106 asked for the stronger claim, which was false when filed, since rule 5 then carved out a policy-licensed zero-proposal no-go. The note restates a consequence already derivable from §2.1 and §5 rather than introducing a new rule; its one **MUST NOT** (a runtime may not treat the initiator as an implicit participant) makes the Authority Matrix's membership requirement explicit for a case implementers have gotten wrong (issue #106).
>
> **Changelog — 1.1.0-draft:** §6.2's **NoVotes** bullet now states the positive-commitment half of the rule, which it previously left to inference. Under a bound policy declaring `schema_version ≥ 3` a positive commitment is denied on an empty tally for every algorithm other than `none`; under `schema_version ≤ 2` it remains gated only by `commitment.require_vote_quorum`. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1. The decline guard is **narrowed** to count only **decisive** rejects: under `weighted` a `REJECT` cast by a weight-`0` participant is non-decisive (RFC-MACP-0012 §4.1) and does not authorize a decline, at every schema version — for `schema_version ≤ 2` descriptors this qualifies the previously unqualified `reject_count > 0` wording; RFC-MACP-0012 §8 bounds that retroactivity and states why it is accepted. §6.2 also gains an **objection-authorized decline**: a decline under `objection_handling.critical_objection_action: "finalize_decline"` is authorized by the recorded critical `Objection` rather than by the tally, so it is gated by neither the tri-state nor the decline guard, at every schema version that can express the field (`schema_version ≥ 2`). `schema_version ≥ 3` newly made that case reachable and nothing ruled on it; RFC-MACP-0012 §8 records why the ruling cannot alter any stored session's replay. The section heading changes to match. The `voting.algorithm == "none"` scoping and the face-value exception are unchanged.

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

**Zero declared participants.** A Decision session that declares no participants can never resolve positively, at any policy `schema_version`. `Proposal` is authorized only for declared participants (matrix above), so no proposal can ever enter accepted history — not even from the initiator, whose authority is role-based rather than membership-based and covers `SessionStart` and `Commitment` (`SessionCancel` is emitted by the runtime, not the initiator; see [RFC-MACP-0001](RFC-MACP-0001-core.md) §7.3). Section 5 rule 5 then bars the session from resolving in either direction, so its only terminations are cancellation and expiry. Section 5 states this consequence for the general case — any session whose participant set cannot produce a proposal; it is specialized here to the zero-participant case, beside the Authority Matrix it derives from. Runtimes MUST NOT treat the initiator as an implicit participant: doing so would admit a proposal and make the vacuously-true zero-participant case of [RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1's `unanimous` arm reachable. `schemas/conformance/decision_zero_participants.json` pins this guard.

## 3. SessionStart requirements

A Decision Mode Session MUST bind the following fields explicitly in `SessionStartPayload`:

- `participants` - decision participants,
- `mode_version` - the decision-mode semantic profile,
- `configuration_version` - voting or evaluation profile,
- `policy_version` — governance profile (MAY be empty; when empty, the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
- `ttl_ms` - explicit decision deadline,
- `context_id` - optional bound decision context reference (arbitrary attached data goes in `extensions`).

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
3. A participant MUST cast at most one `Vote` per `proposal_id`. A runtime MUST reject a second `Vote` from the same sender for the same `proposal_id`; the first accepted `Vote` stands. Configuration MAY bind a *stricter* rule (for example, restricting which participants may vote at all), but MUST NOT relax this one. A permissive multi-vote rule would need replacement or tally semantics that this mode does not define, and without them two conforming implementations could tally identical accepted history differently — which Section 7's semantic-deterministic claim forbids.
4. The runtime or policy authority MUST reject `Commitment` from unauthorized senders.
5. The Session MUST NOT resolve before at least one proposal exists.
6. Deliberation closes when voting begins. After the first `Vote` is accepted within the Session, a runtime MUST reject any subsequent `Proposal`, `Evaluation`, or `Objection`. The first accepted `Vote` fixes the option set and the deliberation record from which the voting result and the objection-handling rules of [RFC-MACP-0012](RFC-MACP-0012-policy.md) are computed; admitting post-vote deliberation messages would let two conforming implementations derive different commitment eligibility from what was identical accepted history at the time each ballot was cast — which Section 7's semantic-deterministic claim forbids. Configuration MAY bind a stricter rule (for example, closing deliberation earlier), but MUST NOT relax this one. Rejections under this rule are session-state breaches and use `INVALID_ENVELOPE` per [RFC-MACP-0002](RFC-MACP-0002-modes.md) §6.1.

Rule 5 has no exceptions in `macp.mode.decision.v1`, and it binds every commitment-authorization path of Section 6.2. An objection-authorized commitment requires a standing critical `Objection`, and a vote-authorized commitment backed by a decisive tally requires a `Vote`; both message types MUST reference an existing `proposal_id` (rule 2), so those routes presuppose an accepted `Proposal` independently of this rule. Two routes presuppose no prior message at all, and for them rule 5 is the ONLY gate: the face-value exception (Section 6.2), which is initiator-driven; and, under a bound policy with `schema_version ≤ 2` and `commitment.require_vote_quorum` false, a positive commitment on the empty tally (Section 6.2, **NoVotes**) — that commitment is vote-authorized, because its authorization derives from the computed voting result, yet it requires no `Vote` and therefore carries no `proposal_id` of its own. The face-value exception waives the decline guard, not this rule.

The only Decision Mode messages that do not reference a `proposal_id` are `Proposal` itself, `SessionStart`, `Commitment`, and the runtime lifecycle annotations (`SessionCancel`, `SessionSuspend`, `SessionResume`). It follows that a session whose declared participant set cannot produce an accepted `Proposal` can never resolve in either direction and terminates only by `SessionCancel` or expiry. A deployment that needs an auditable "no proposals arrived" terminal record SHOULD use `SessionCancel` with an explanatory reason.

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

### 6.2 Negative committed outcomes (vote-gated and objection-gated decline)

When a Decision session binds a governance policy with a real voting algorithm (`voting.algorithm != "none"`), the eligibility of a positive versus negative `Commitment` is gated as follows. A **vote-authorized** commitment — one whose authorization derives from the computed voting result — is gated by that result per the tri-state below; an **objection-authorized** negative commitment (defined after the face-value exception) is the single exception to this gate:

- **Passed** — a positive commitment (`outcome_positive: true`) is allowed; a negative commitment is denied **unless** `commitment.allow_decline_over_approval` is `true`.
- **Failed** — a positive commitment is denied; a negative commitment is allowed **iff** the decline guard (below) is satisfied.
- **NoVotes** — the decisive tally is empty. A negative commitment is denied: an empty decisive tally contains no decisive reject, so the decline guard cannot be satisfied. A positive commitment is governed by the bound policy's `schema_version`: under `schema_version ≥ 3` it is denied (every algorithm other than `none` fails on the empty tally), and under `schema_version ≤ 2` it is denied only when `commitment.require_vote_quorum` is `true` ([RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1). For `weighted`, a vote cast by a weight-`0` participant is **non-decisive** (RFC-MACP-0012 §4.1), so a tally whose total decisive weight is zero — including a ballot set consisting entirely of weight-`0` votes — is the NoVotes state at every schema version; the weight-`0` `REJECT`s such a tally may contain do not satisfy the decline guard.

**Decline guard (normative):** a vote-authorized negative commitment MUST be backed by at least one **decisive** explicit `Vote` with `vote == "REJECT"` (`reject_count > 0`, where `reject_count` counts decisive rejects; under `weighted` a `REJECT` cast by a weight-`0` participant is non-decisive and does not count), and, when `commitment.require_vote_quorum` is `true`, the voting quorum MUST be met. The guard applies across all three voting results and at every policy `schema_version`.

**Face-value exception:** when `voting.algorithm == "none"` (or no policy is bound), the commitment is initiator-driven and `outcome_positive` is taken at face value with no decline guard. Section 5 rule 5 still applies: no `Commitment` — positive or negative — may resolve the session before at least one proposal exists.

**Objection-authorized decline:** when the bound policy sets `objection_handling.critical_objection_action` to `finalize_decline` and a standing critical objection blocks the positive direction under the policy's objection-handling rules, a negative commitment is **objection-authorized**: its authorization is the recorded critical `Objection`, not the voting result. An objection-authorized decline is not gated by the tri-state above and is not subject to the decline guard — the objection is itself the explicit, attributable dissent the guard exists to require — and it is available at every tally, including the empty tally under `schema_version ≥ 3` ([RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1). The waiver covers the guard whole, its `require_vote_quorum` conjunct included: the quorum condition legitimizes an outcome that derives its authority from the voting result, and an objection-authorized decline derives none, so a runtime MUST NOT deny it for an unmet voting quorum. The `evaluation` prerequisites (`evaluation.required_before_voting`, `evaluation.minimum_confidence`; [RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1) are prerequisites of the same voting pipeline and likewise MUST NOT be applied to an objection-authorized decline. Applying either gate here reconstructs the stuck state this channel exists to remove: with the gate unmet and no ballot arriving, no `Commitment` would be acceptable in either direction. Without this channel, a `schema_version ≥ 3` session with a non-`none` algorithm, an empty tally, and a standing critical objection could reach no committed outcome at all, ending only by cancellation or expiry, neither of which records one — precisely the stuck state `finalize_decline` exists to resolve. This rule applies at every schema version that can express `finalize_decline` (`schema_version ≥ 2`). It cannot alter the replay of any stored session: a runtime that formerly read the tri-state as denying such a decline rejected the message, and rejected messages never enter accepted history ([RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3).

Both governing knobs — `commitment.allow_decline_over_approval` (bool, default `false`) and `objection_handling.critical_objection_action` (enum `deny` | `finalize_decline` | `hold`, default `deny`) — are policy-controlled with conservative defaults that preserve pre-existing behavior. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1 for their semantics.

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
