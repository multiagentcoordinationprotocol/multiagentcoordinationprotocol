# RFC-MACP-0007
# Multi-Agent Coordination Protocol (MACP) - Decision Mode

**Document:** RFC-MACP-0007
**Version:** 1.1.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

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

### 6.2 Negative committed outcomes (vote-gated and objection-gated decline)

When a Decision session binds a governance policy with a real voting algorithm (`voting.algorithm != "none"`), the eligibility of a positive versus negative `Commitment` is gated as follows. A **vote-authorized** commitment — one whose authorization derives from the computed voting result — is gated by that result per the tri-state below; an **objection-authorized** negative commitment (defined after the face-value exception) is the single exception to this gate:

- **Passed** — a positive commitment (`outcome_positive: true`) is allowed; a negative commitment is denied **unless** `commitment.allow_decline_over_approval` is `true`.
- **Failed** — a positive commitment is denied; a negative commitment is allowed **iff** the decline guard (below) is satisfied.
- **NoVotes** — the decisive tally is empty. A negative commitment is denied: an empty decisive tally contains no decisive reject, so the decline guard cannot be satisfied. A positive commitment is governed by the bound policy's `schema_version`: under `schema_version ≥ 3` it is denied (every algorithm other than `none` fails on the empty tally), and under `schema_version ≤ 2` it is denied only when `commitment.require_vote_quorum` is `true` ([RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1). For `weighted`, a vote cast by a weight-`0` participant is **non-decisive** (RFC-MACP-0012 §4.1), so a tally whose total decisive weight is zero — including a ballot set consisting entirely of weight-`0` votes — is the NoVotes state at every schema version; the weight-`0` `REJECT`s such a tally may contain do not satisfy the decline guard.

**Decline guard (normative):** a vote-authorized negative commitment MUST be backed by at least one **decisive** explicit `Vote` with `vote == "REJECT"` (`reject_count > 0`, where `reject_count` counts decisive rejects; under `weighted` a `REJECT` cast by a weight-`0` participant is non-decisive and does not count), and, when `commitment.require_vote_quorum` is `true`, the voting quorum MUST be met. The guard applies across all three voting results and at every policy `schema_version`.

**Face-value exception:** when `voting.algorithm == "none"` (or no policy is bound), the commitment is initiator-driven and `outcome_positive` is taken at face value with no decline guard.

**Objection-authorized decline:** when the bound policy sets `objection_handling.critical_objection_action` to `finalize_decline` and a standing critical objection blocks the positive direction under the policy's objection-handling rules, a negative commitment is **objection-authorized**: its authorization is the recorded critical `Objection`, not the voting result. An objection-authorized decline is not gated by the tri-state above and is not subject to the decline guard — the objection is itself the explicit, attributable dissent the guard exists to require — and it is available at every tally, including the empty tally under `schema_version ≥ 3` ([RFC-MACP-0012](RFC-MACP-0012-policy.md) §4.1). Without this channel, a `schema_version ≥ 3` session with a non-`none` algorithm, an empty tally, and a standing critical objection could terminate only by expiry — precisely the stuck state `finalize_decline` exists to resolve. This rule applies at every schema version that can express `finalize_decline` (`schema_version ≥ 2`). It cannot alter the replay of any stored session: a runtime that formerly read the tri-state as denying such a decline rejected the message, and rejected messages never enter accepted history ([RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3).

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
