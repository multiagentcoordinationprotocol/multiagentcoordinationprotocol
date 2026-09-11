# RFC-MACP-0012
# Multi-Agent Coordination Protocol (MACP) — Governance Policy Framework

**Document:** RFC-MACP-0012
**Version:** 1.2.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001, RFC-MACP-0002, RFC-MACP-0003

> **Changelog — 1.2.0-draft:** Quorum Mode threshold vocabulary (§4.2, `quorum-rules.schema.json`). (1) The `weighted` threshold type is **removed** and its identifier reserved: it was enum-legal but had no weights vocabulary, no electorate rule, and no termination arithmetic ([RFC-MACP-0011](RFC-MACP-0011-quorum-mode.md) §5 rules 2, 4, and 4a are count-only), so no conformant evaluation of it ever existed and §8 had nothing to pin. Removal is an admission-time schema tightening under §8 item 4 and changes the evaluation of no admissible descriptor; no `schema_version` bump. (2) The `percentage` ceiling rule — effective threshold `ceil(value × declared_participant_count / 100)`, fixed at `SessionStart` — is promoted from the §5.2 rationale into normative §4.2 text. It completes previously undefined behavior and is normative at **every** `schema_version`; see the completion note in §8. (3) `threshold.value` gains `exclusiveMinimum: 0`, aligning the schema with RFC-MACP-0011 §5 rule 2 — the quorum-side twin of the Decision-side floor tightening in 1.1.0-draft. (4) The `count` alias used by one implementation for `n_of_m` is confirmed **not** part of the vocabulary; the enum is `["n_of_m", "percentage"]` and closed (issue #98 item 4).
>
> **Changelog — 1.1.0-draft:** adds `schema_version: 3`, the first **semantic** schema-version bump. Under schema_version ≥ 3 every voting algorithm other than `none` is binding on its own and **fails on the empty tally** (§4.1); the legacy fail-open rule — no decisive votes produces no result, gated only by `commitment.require_vote_quorum` — is preserved for schema_version ≤ 2, which stored sessions replay under per §8. Separately, and at **every** schema version, the `weights` map is defined as the weighted electorate (omission means weight `0`) and weight-`0` votes are defined as **non-decisive**: outside the ratio, outside the decisive tally, and unable to satisfy the decline guard of [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) §6.2 (§4.1). For schema_version ≤ 2 that is not purely a clarification. The original text left the weight of an unlisted voter, the zero-total-weight `weighted` ratio (`0/0`), and its Passed/Failed/NoVotes classification undefined, and this rule completes that gap as NoVotes; but the original decline guard counted **any** explicit `REJECT`, weight-`0` included, and in one corner that defined behavior is deliberately **narrowed** — see the bounded-retroactivity note in §8. §4.1's empty-tally rules are additionally scoped to **vote-authorized** commitment, because a decline under `objection_handling.critical_objection_action: "finalize_decline"` is objection-authorized and gated by neither the tri-state nor the decline guard (RFC-MACP-0007 §6.2); §8 records that second `schema_version ≤ 2` change and why it is replay-neutral. Also: `threshold` floors are tightened in the schema (`> 0` everywhere, `≥ 0.5` for `majority`).

## Abstract

This document defines the MACP Governance Policy Framework: a declarative, deterministic, and replay-safe mechanism for binding governance rules to Coordination Sessions. Policies specify how session outcomes are determined — voting algorithms, quorum thresholds, objection handling, commitment authority, and mode-specific governance constraints. Policies are authored via SDKs, registered with the runtime, resolved at `SessionStart`, and evaluated at commitment time.

## 1. Purpose and Scope

MACP Modes (RFC-MACP-0002) define coordination semantics — valid message types, participant models, and terminal conditions. However, Modes intentionally do not prescribe governance algorithms. RFC-MACP-0007 (Decision Mode) states:

> "The mode does not prescribe a single voting algorithm. A runtime or deployment may use majority vote, weighted vote, objection handling, veto rules, or another deterministic policy, provided that the policy is version-bound and replay-safe."

The `policy_version` field exists in `SessionStartPayload` and `CommitmentPayload` (RFC-MACP-0001) but has no defined resolution or evaluation semantics. This RFC fills that gap by defining:

1. a **policy descriptor** format that any runtime in any language can interpret,
2. **rule schemas** for each standard mode's governance parameters,
3. **evaluation semantics** specifying when and how policies are applied,
4. a **default policy** that all runtimes MUST provide for backward compatibility,
5. a **registration lifecycle** for dynamic policy management via gRPC RPCs,
6. **replay invariants** ensuring policy evaluation is deterministic across implementations.

This RFC is cross-cutting: it applies to all standard modes and to extension modes that opt in.

## 2. Policy Identifiers

### 2.1 Naming Convention

Policy identifiers use the form:

`policy.{namespace}.{name}`

Examples:

- `policy.default` — the built-in default policy
- `policy.fraud.majority-veto` — a domain-specific policy
- `policy.lending.unanimous` — another domain-specific policy

### 2.2 Reserved Namespace

Two reservations exist.

**`policy.default`.** The `policy.default` identifier is reserved. Runtimes MUST NOT allow registration of a policy with this identifier; it is always pre-registered (Section 5.1). It predates the `policy.{namespace}.{name}` convention of Section 2.1 and retains its two-segment form.

**`policy.std.`.** Every identifier beginning with `policy.std.` is reserved for the built-in governance profiles published in this specification. Runtimes MUST NOT allow registration of a policy whose `policy_id` begins with `policy.std.` — via `RegisterPolicy` or via any implementation-defined loading path — unless the descriptor is one of the canonical definitions in Section 5.2. A registration that violates this MUST be rejected with `INVALID_POLICY_DEFINITION`.

Reservation is a **collision guarantee, not a provisioning requirement**:

- A runtime MAY pre-register any subset of the profiles defined in Section 5.2, including none of them. `policy.default` remains the only policy a runtime MUST provide.
- If a runtime provides a policy under a reserved `policy.std.` identifier, that policy MUST be semantically equal to the canonical definition for that identifier: every rule parameter — whether spelled out explicitly or left to its JSON Schema default — MUST resolve to the value Section 5.2 gives, and `mode` and `schema_version` MUST match. A runtime MUST NOT ship different rules under a reserved identifier.
- A `SessionStart` naming a `policy.std.` identifier the runtime does not provide is an unknown policy and MUST be rejected with `UNKNOWN_POLICY_VERSION` per Section 6.1. Clients MUST NOT assume that a reserved identifier resolves on every runtime; `ListPolicies` reports what is actually available.
- Identifiers under `policy.std.` that this specification has not assigned are reserved but unassigned: they MUST NOT be registered and MUST NOT resolve.

Identifiers outside these two reservations — including short unnamespaced forms such as `policy.majority` — are **not** reserved and remain available to deployments. Deployments SHOULD nevertheless use their own namespace (`policy.{org}.{name}`) so that later additions under `policy.std.` cannot collide with local governance rules.

### 2.3 Immutability

A registered policy identifier is immutable. To change governance rules, register a new policy with a new identifier. This ensures that `policy_version` in historical sessions always resolves to the same rules.

## 3. Policy Descriptor

A policy descriptor is a structured document with the following required fields:

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | string | Unique policy identifier (see Section 2.1) |
| `mode` | string | Target mode identifier (e.g., `macp.mode.decision.v1`) or `*` for mode-agnostic |
| `description` | string | Human-readable description of the policy's governance rules |
| `rules` | object | Mode-specific governance rules (see Section 4) |
| `schema_version` | uint32 | Version of the rule schema used (`1`, `2`, or `3`) |

Schema version `2` adds the Decision Mode decline-gating parameters (`commitment.allow_decline_over_approval`, `objection_handling.critical_objection_action`; see §4.1). That bump is **additive**: the new fields are optional and default to legacy behavior, so `schema_version: 1` policies remain valid. Declaring `schema_version: 2` signals only that the descriptor MAY use the new fields. A runtime MUST accept every schema version it supports (`{1, 2, 3}`).

Schema version `3` is the first **semantic** bump: it changes the evaluation of existing fields — the empty-tally rule of §4.1 — rather than adding fields. It is not additive: the same descriptor bytes can evaluate differently under versions 2 and 3. Authors select semantics by the version they declare; Section 8 pins every stored session to its declared version. New policies that use a voting algorithm other than `none` SHOULD declare `schema_version: 3`.

The canonical wire format is defined in `schemas/proto/macp/v1/policy.proto`. The `rules` field is JSON-encoded bytes to allow mode-specific schemas without requiring proto changes per mode.

**Encoding note:** In the Protobuf wire format, `rules` is `bytes` containing JSON-encoded text. In JSON canonical form (e.g., examples), `rules` is shown as a decoded JSON object for readability. In actual proto-to-JSON serialization, `rules` would be base64-encoded. Examples in this specification use the decoded form unless otherwise noted.

## 4. Rule Schemas

Each standard mode defines a normative JSON Schema for its governance rules. Any runtime implementation MUST interpret these rules identically given identical inputs.

### 4.1 Decision Mode Rules

Canonical schema: `schemas/json/policy/decision-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `voting` | `algorithm`, `threshold`, `quorum`, `weights` | Voting algorithm and quorum requirements |
| `objection_handling` | `critical_severity_vetoes`, `veto_threshold`, `critical_objection_action` | How critical-severity objections affect commitment eligibility |
| `evaluation` | `minimum_confidence`, `required_before_voting` | Evaluation constraints |
| `commitment` | `authority`, `designated_roles`, `require_vote_quorum`, `allow_decline_over_approval` | Who can commit and under what conditions |

**Voting algorithms:**

- `none` — no voting constraint enforced (mode's built-in logic applies)
- `majority` — at least `threshold` (default `0.5`) of the decisive votes approve; the schema constrains `threshold` to at least `0.5` (a lower ratio bar is not a majority — express one as `weighted` with equal weights)
- `supermajority` — at least `threshold` of the decisive votes approve; the schema constrains `threshold` to be greater than `0.5`
- `unanimous` — every declared participant has cast an approve vote and no reject vote was cast; `threshold` is not used
- `weighted` — weighted votes using the `weights` map; `threshold` applies to the weighted approve share. The `weights` map defines the **weighted electorate**: a declared participant absent from the map has weight `0` (an observer is expressed by omission, and the schema rejects explicit `0` values and an empty map). A vote cast by an unlisted (weight-`0`) participant is accepted as a message and preserved in history, but it is **non-decisive** under `weighted` evaluation: it contributes to neither side of the weighted ratio, does not enter the decisive tally, and does not satisfy the decline guard of RFC-MACP-0007 §6.2 — for tally purposes it is treated as an abstention. It still counts as a vote cast for the `voting.quorum` participation floor, which this rule does not alter. A ballot set cast entirely by weight-`0` participants therefore leaves the decisive tally **empty** (zero total decisive weight) — see the empty-tally rules below. This electorate rule is normative for **every** schema version. The weight of an unlisted voter and the zero-denominator weighted ratio were previously unspecified, so most of this rule completes undefined behavior; its decline-guard consequence, however, **narrows** the previously unqualified `reject_count > 0` guard of RFC-MACP-0007 §6.2 in one corner — see the bounded-retroactivity note in Section 8.
- `plurality` — more approve votes than reject votes; a tie fails; no threshold

**Threshold floor.** Wherever `threshold` is used it MUST be greater than `0`, and the schema enforces this for every algorithm. A `threshold` of `0` is satisfied by an all-`REJECT` round under both `majority` and `weighted` — the approval ratio is `0`, and `0 >= 0` holds under the inclusive comparison below — so a policy that reads as restrictive would in fact approve everything. The per-algorithm floors above (`majority` at least `0.5`, `supermajority` greater than `0.5`) are stricter bounds on top of this one. The floor is enforced unconditionally, so `unanimous` and `plurality` — which do not consult `threshold` at all — also reject an explicit `0`. That is deliberate: a `threshold` a policy author believed was in force should never be silently ignored because the chosen algorithm happens not to read it.

**Denominator.** For the ratio-based algorithms (`majority`, `supermajority`, `weighted`) the denominator is the **decisive** votes — those cast as approve or reject. Abstentions are excluded and neither help nor hinder the ratio (RFC-MACP-0004). Under `weighted`, only weight-bearing votes are decisive (see the electorate rule above); a weight-`0` ballot joins the abstentions outside the ratio.

**Inclusive comparison.** Every threshold comparison in this section is inclusive (`ratio >= threshold`). With `majority` at its default `threshold` of `0.5`, an even split therefore approves. A rule that requires strictly more approvals than rejections is `plurality`, not `majority` with `threshold: 0.5`. `unanimous` is stricter than "all decisive votes approve": a declared participant who has not voted blocks it.

**`voting.quorum` is inert on its own.** `voting.quorum` states the participation bar but does not itself gate a commitment; it is applied only when `commitment.require_vote_quorum` is `true`. A policy that sets `voting.quorum` without `require_vote_quorum` imposes no participation requirement. Under `schema_version ≥ 3` this pairing is unchanged; the flag's contribution there is purely the participation floor, since the algorithm is already binding (see **Empty tally** below).

**Empty tally (schema_version ≥ 3).** Everything in this paragraph, its bullets, and the summary following them governs **vote-authorized** commitment — commitment whose authorization derives from the computed voting result. An **objection-authorized** decline under `objection_handling.critical_objection_action: "finalize_decline"` is the single exception and is gated by none of it (RFC-MACP-0007 §6.2); the same exception applies to the legacy arm below. Under `schema_version` 3 or later, every algorithm other than `none` is binding on its own: the algorithm's predicate is evaluated over the actual tally, including the empty one, and every algorithm other than `none` **fails** when no decisive vote has been cast. This rule is primary: the per-algorithm notes below describe how each predicate realizes it, and where a predicate's own text would not fail on an empty tally, this rule controls. In the tri-state of [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) §6.2 the empty decisive tally is **NoVotes** for *every* algorithm, never **Failed** — "fails" here means the algorithm does not authorize a positive commitment, not that it produced a Failed result. The distinction does not change any outcome, because NoVotes and Failed both deny a positive commitment and an empty tally can never satisfy the decline guard; it matters only to implementations that surface the voting result, which MUST report NoVotes so that two conformant runtimes agree on what they observed.

- `majority`, `supermajority` — with zero decisive votes the approval ratio is undefined; the arm MUST fail without evaluating `ratio >= threshold`. Implementations MUST NOT compute `0/0`.
- `unanimous` — the arm MUST fail on an empty tally. With at least one declared participant this follows from the predicate as written: "every declared participant has cast an approve vote" is false when nobody has voted. With **zero** declared participants the universally quantified predicate is vacuously true and MUST NOT be taken as a pass: MACP does not require `SessionStart` to declare a non-empty `participants` list, and a zero-participant Decision session can never accept a `Vote` (only declared participants are vote-authorized, RFC-MACP-0007 §2.1), so its decisive tally is permanently empty and the empty-tally rule — not the predicate — governs. Under `schema_version ≥ 3`, `unanimous` over an empty declared set therefore always fails; such a session can positively resolve only under `voting.algorithm: "none"`.
- `weighted` — because weight-`0` votes are non-decisive (see the electorate rule above), a tally whose total decisive weight is zero **is** the empty decisive tally: it covers both no ballots at all and a complete ballot set cast entirely by weight-`0` (unlisted) participants. This state is **NoVotes** per the rule above — the point bears repeating here because the weighted case is the one where a zero denominator invites an implementation to report Failed instead: a positive commitment is denied by this rule, and a vote-authorized negative commitment is denied because no decisive reject exists — a weight-`0` `REJECT` does not satisfy the decline guard. Implementations MUST NOT compute a weighted ratio with a zero denominator.
- `plurality` — zero approvals against zero rejections is a tie, and a tie fails. No special case is required.
- `none` — unaffected; no voting constraint is enforced at any tally, so nothing in this paragraph applies to it.

A **vote-authorized** negative commitment on an empty decisive tally remains blocked by the decline guard (at least one **decisive** explicit reject; under `weighted` a `REJECT` cast by a weight-`0` participant is non-decisive and does not satisfy the guard; RFC-MACP-0007 §6.2), which — like the rulings above — does not reach `voting.algorithm == "none"`: that case is governed by the face-value exception in RFC-MACP-0007 §6.2. Under `schema_version ≥ 3` with any algorithm other than `none`, an empty tally therefore blocks **vote-authorized** commitment in both directions; the one path through it is an **objection-authorized** decline under `objection_handling.critical_objection_action: "finalize_decline"`, whose authorization is a standing critical `Objection` rather than the tally (RFC-MACP-0007 §6.2). Adding an approving ballot can never convert an allowed positive commitment into a denied one.

**Legacy empty-tally rule (schema_version ≤ 2).** Under `schema_version` 1 and 2, with any algorithm other than `none`, if no decisive vote has been cast — for `weighted`, if the total decisive weight is zero — the algorithm produces no result: it neither passes nor fails. Whether that blocks a positive commitment is then governed entirely by `commitment.require_vote_quorum`: with it `false`, a positive commitment is **not** blocked by the absence of votes, even under `majority` or `unanimous`. A schema_version ≤ 2 policy that intends its voting algorithm to be binding MUST set `commitment.require_vote_quorum` to `true`. A **vote-authorized** negative commitment is always blocked in this case: an empty tally contains no reject, and under `weighted` a `REJECT` cast by a weight-`0` participant is non-decisive and does not satisfy the decline guard (see RFC-MACP-0007 §6.2). As under `schema_version ≥ 3`, the one path through this block is an **objection-authorized** decline under `objection_handling.critical_objection_action: "finalize_decline"`, which is gated by neither the tri-state nor the decline guard and is available at every schema version that can express it (`schema_version ≥ 2`; RFC-MACP-0007 §6.2). The schema versions therefore differ only in the **positive** direction, which this arm gates solely on `commitment.require_vote_quorum`.

**Retaining the legacy arm.** The rule above is fail-open and is retained **solely** so that stored sessions replay identically (Section 8). Implementations MUST keep it, MUST NOT apply it to `schema_version ≥ 3` policies, and SHOULD warn when a newly registered `schema_version ≤ 2` policy declares a voting algorithm other than `none` without `require_vote_quorum: true`.

**Quorum:**

- `type: "count"` — minimum number of votes that must be cast
- `type: "percentage"` — minimum percentage of declared participants that must vote

**Negative-outcome parameters:**

- `commitment.allow_decline_over_approval` (bool, default `false`) — permit a negative commitment (`outcome_positive: false`) even when the vote **Passed**. With the default `false`, a passed vote authorizes only a positive commitment.
- `objection_handling.critical_objection_action` (enum `deny` | `finalize_decline` | `hold`, default `deny`) — action taken when a critical objection would block commitment: `deny` (reject the commitment; legacy behavior), `finalize_decline` (finalize the session as a negative outcome — this decline is **objection-authorized**: it is available regardless of the computed voting result, including on an empty tally under `schema_version ≥ 3`, and is not subject to the decline guard; RFC-MACP-0007 §6.2), or `hold` (reject the commitment, as `deny`, while signalling to operators that the denial is an escalation rather than a permanent refusal).

> **`deny` and `hold` are observationally identical.** Both reject the `Commitment` with `POLICY_DENIED` and leave the session `OPEN` — a rejected message never mutates accepted history or session state ([RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3), so "reject the commitment" and "leave the session open" describe the same outcome. `hold` is an operator-facing annotation on the denial, not a distinct protocol outcome. Runtimes MUST NOT expose a distinction between the two over the wire, and agents MUST NOT rely on one. Consequently the conformance corpus pins `deny` and `finalize_decline` only; a `hold` fixture would assert nothing that a `deny` fixture does not already assert.

The **decline guard** for a vote-authorized negative commitment (≥1 **decisive** explicit `Vote` with `vote == "REJECT"`; optional `commitment.require_vote_quorum`) is defined with the Decision Mode terminal semantics — see [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) §6.2. Both parameters are additive with conservative defaults that preserve pre-existing behavior; policies that use them declare `schema_version: 2` or later.

### 4.2 Quorum Mode Rules

Canonical schema: `schemas/json/policy/quorum-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `threshold` | `type`, `value` | Override the `required_approvals` from `ApprovalRequest` |
| `abstention` | `counts_toward_quorum`, `interpretation` | How abstentions affect quorum calculation |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

`threshold` is the **approval bar** — the number (or percentage) of approvals required for a positive outcome — and it is the **only gate** defined in schema_version ≤ 3. There is no separate *participation quorum* (a minimum number of ballots cast regardless of direction); implementations MUST NOT reinterpret `threshold` as one. If a participation quorum is desired, it requires a distinct rule field in a future schema version. The `percentage` threshold type is an **integer percentage (1–100)** of the participant count declared at `SessionStart`. The effective approval threshold is `ceil(value × declared_participant_count / 100)` — the product is rounded **up**, so a fractional product never lowers the bar: `value: 50` over 3 declared participants requires 2 approvals, not 1. Implementations MUST compute this threshold with exact integer arithmetic (equivalently, integer division `(value × declared_participant_count + 99) div 100`) and MUST NOT use floating-point division. The declared participant count is fixed at `SessionStart`; the effective threshold does not change as ballots, including abstentions, are cast. This rounding rule completes previously undefined behavior — earlier text of this section stated no rounding direction — and is therefore normative at **every** `schema_version` (see the completion note in Section 8). `threshold.value` MUST be greater than zero, matching [RFC-MACP-0011](RFC-MACP-0011-quorum-mode.md) Section 5, rule 2; the rule schema enforces this at admission (`exclusiveMinimum: 0`). The `weighted` threshold type is **removed as of 1.2.0-draft** and its identifier reserved: it appeared in the rule schema's enum without any defined weights vocabulary, electorate rule, or termination arithmetic, so no conformant evaluation of it ever existed. A future weighted threshold, if standardized, MUST arrive with complete semantics under a new rule field or a reinstated identifier carrying its original meaning, and the identifier MUST NOT be reused with a different meaning.

### 4.3 Proposal Mode Rules

Canonical schema: `schemas/json/policy/proposal-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `acceptance` | `criterion` | `all_parties`, `counterparty`, or `initiator` |
| `counter_proposal` | `max_rounds` | Maximum negotiation rounds (0 = unlimited) |
| `rejection` | `terminal_on_any_reject` | Whether any rejection terminates the session |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

### 4.4 Task Mode Rules

Canonical schema: `schemas/json/policy/task-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `assignment` | `allow_reassignment_on_reject` | Whether rejected tasks can be reassigned |
| `completion` | `require_output` | Whether `TaskComplete` must include output |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

### 4.5 Handoff Mode Rules

Canonical schema: `schemas/json/policy/handoff-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `acceptance` | `implicit_accept_timeout_ms` | Auto-accept after timeout (0 = no implicit accept) |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

**Determinism note:** `implicit_accept_timeout_ms` is **not** evaluated by the policy evaluator at commitment time. It is a declarative parameter consumed by the runtime's synthetic-accept mechanism, whose full normative contract — timing source (the offer's recorded acceptance time on the session timeline, excluding suspended time), lazy-at-the-latest emission into accepted history before commitment evaluation, runtime-emitted envelope convention (`sender` = target, `HandoffAcceptPayload.implicit = true`, deterministic `message_id`), and race resolution by history order — is defined in RFC-MACP-0010 §5.1. The policy evaluator only sees the resulting accepted message history, preserving the determinism requirement of Section 6.3: the timer is outside the replay boundary, its recorded product is inside.

### 4.6 Extension Mode Rules

Extension modes registered via `RegisterExtMode` MAY define custom rule schemas. The runtime SHOULD validate custom rules against the mode's declared policy schema if one exists. Extension modes without a declared policy schema accept any valid JSON as rules.

## 5. Built-in Policies

### 5.1 Default Policy

Every conformant runtime MUST pre-register the following default policy:

```json
{
  "policy_id": "policy.default",
  "mode": "*",
  "schema_version": 1,
  "description": "Default policy — mode built-in rules apply with no additional governance constraints",
  "rules": {}
}
```

The default policy applies no additional governance constraints beyond base mode validation. Mode-specific default behaviors (e.g., Decision Mode's default voting algorithm, Quorum Mode's default abstention handling) are defined by each mode's base validation rules in their respective RFCs, not by the default policy.

When `policy_version` in `SessionStartPayload` is empty or equals `policy.default`, the runtime MUST apply this default. The default policy sets all rule parameters to permissive values such that the mode's built-in validation is the only constraint applied. It does not disable mode validation — it simply adds no governance restrictions on top of it.

An empty `rules` object and a `rules` object that spells out every parameter at its JSON Schema default are the same policy. A runtime MAY pre-register either form.

### 5.2 Reserved Governance Profiles

Three common governance profiles are assigned reserved identifiers under the `policy.std.` namespace of Section 2.2. Unlike `policy.default`, they are **optional**: a runtime MAY pre-register any subset of them, and one that pre-registers none of them remains conformant. What the reservation guarantees is that these identifiers cannot be claimed by a user registration, so an identifier that does resolve resolves to the rules below on every runtime.

All three target `macp.mode.decision.v1` and declare `schema_version: 1`; they use only schema-version-1 rule fields. They are Decision Mode profiles specifically because a descriptor binds exactly one `mode` (Section 3) and because Decision Mode is the only standard mode whose rule schema can express these three bars exactly — see the note at the end of this section.

| Policy ID | Mode | Governance bar |
|-----------|------|----------------|
| `policy.std.majority` | `macp.mode.decision.v1` | At least half of the decisive votes approve |
| `policy.std.supermajority` | `macp.mode.decision.v1` | At least two-thirds of the decisive votes approve, with at least two voters |
| `policy.std.unanimous` | `macp.mode.decision.v1` | Every declared participant has approved and no reject was cast |

Each profile declares `schema_version: 1` and sets `commitment.require_vote_quorum` to `true`. Under schema-version-1 semantics that flag is what makes the voting algorithm binding on a positive commitment when no vote has been cast (see the legacy empty-tally rule in Section 4.1); under `schema_version ≥ 3` the algorithm is binding on its own and the flag's remaining contribution is the `voting.quorum` participation floor (two voters for `policy.std.supermajority`). The profiles produce identical outcomes under both semantics at every tally containing at least one decisive vote. They differ only where an empty decisive tally nonetheless clears the participation floor, which affects **all three** profiles: a lone abstention satisfies the one-vote count quorum of both `policy.std.majority` and `policy.std.unanimous` (`quorum: {"type": "count", "value": 1}`), and two abstentions satisfy `policy.std.supermajority`'s `value: 2` — tallies that schema-version-1 semantics allow to support a positive commitment and that `schema_version ≥ 3` denies. They remain at `schema_version: 1` unchanged regardless: bumping them would alter the canonical definitions that Section 2.2's semantic-equality requirement pins on every runtime, and a runtime wanting the fail-closed reading registers its own `schema_version: 3` policy rather than redefining a reserved identifier.

#### `policy.std.majority`

```json
{
  "policy_id": "policy.std.majority",
  "mode": "macp.mode.decision.v1",
  "schema_version": 1,
  "description": "Simple majority — at least half of the decisive votes approve",
  "rules": {
    "voting": {
      "algorithm": "majority",
      "threshold": 0.5,
      "quorum": { "type": "count", "value": 1 }
    },
    "commitment": { "require_vote_quorum": true }
  }
}
```

A positive commitment is allowed when at least one participant has voted and `approve / (approve + reject) >= 0.5`. The comparison is inclusive per Section 4.1, so an even split approves; a profile in which a tie fails is `plurality`, which this specification does not reserve.

#### `policy.std.supermajority`

```json
{
  "policy_id": "policy.std.supermajority",
  "mode": "macp.mode.decision.v1",
  "schema_version": 1,
  "description": "Two-thirds supermajority with a minimum of two voters",
  "rules": {
    "voting": {
      "algorithm": "supermajority",
      "threshold": 0.6666666666666666,
      "quorum": { "type": "count", "value": 2 }
    },
    "commitment": { "require_vote_quorum": true }
  }
}
```

A positive commitment is allowed when at least two participants have voted and `approve / (approve + reject) >= threshold`.

**Determinism note:** two-thirds is not exactly representable in binary floating point. The literal `0.6666666666666666` is the IEEE-754 binary64 value nearest to two-thirds, and it is the same binary64 value that `2 / 3` produces under binary64 division. Implementations MUST evaluate this comparison in binary64 so that the intended outcomes hold: 2 of 3, 4 of 6, 20 of 30, and 67 of 100 approvals pass, and 66 of 100 does not. An implementation using exact decimal or rational arithmetic would compute `2/3 < 0.6666666666666666` and reject 2 of 3, which is why the arithmetic is pinned rather than left implicit under Section 6.3.

#### `policy.std.unanimous`

```json
{
  "policy_id": "policy.std.unanimous",
  "mode": "macp.mode.decision.v1",
  "schema_version": 1,
  "description": "Unanimous — every declared participant approves and no reject is cast",
  "rules": {
    "voting": {
      "algorithm": "unanimous",
      "quorum": { "type": "count", "value": 1 }
    },
    "commitment": { "require_vote_quorum": true }
  }
}
```

A positive commitment is allowed when every identifier in the session's declared `participants` has cast an approve vote and no reject vote exists. Per Section 4.1 this is stricter than "all decisive votes approve": a participant who has not voted blocks the commitment, and `threshold` is not consulted. The `quorum` entry only keeps the algorithm binding; the all-participants requirement comes from the algorithm itself.

**Why Decision Mode only.** "Majority", "supermajority", and "unanimous" are meaningful in Quorum Mode as well, but Quorum Mode expresses its bar through `threshold` (Section 4.2), whose `n_of_m` type is an absolute approval count and whose `percentage` type is an integer 1–100 rounded up against the declared participant count (normative in Section 4.2). An absolute count cannot express a bar that scales with participants, and an integer percentage cannot express two-thirds or a strict majority exactly at every participant count: `67` requires 3 of 3 rather than 2 of 3, and `51` requires 102 of 200 rather than 101. `100` does express unanimity exactly, but reserving a single Quorum Mode profile whose siblings cannot exist would be worse than reserving none. Quorum Mode profiles are therefore left unassigned; they need an exact-fraction threshold type, which is a schema addition and out of scope here.

## 6. Evaluation Semantics

### 6.1 Policy Resolution

At `SessionStart`:

1. The runtime extracts `policy_version` from the `SessionStartPayload`.
2. If empty, the runtime resolves to `policy.default`.
3. If non-empty, the runtime looks up the policy in its registry.
4. If the policy is not found, the runtime MUST reject the `SessionStart` with error code `UNKNOWN_POLICY_VERSION`.
5. If the policy's `mode` field is not `*` and does not match the session's mode, the runtime MUST reject with `INVALID_POLICY_DEFINITION`.
6. The resolved `PolicyDescriptor` (including the full `rules` object) is stored on the session for the session's lifetime.
7. The session's persisted metadata MUST record the **resolved** policy identifier — `policy.default` when the payload was empty — not the raw payload value. Replay equality (Section 8) and any observer surface (`GetSession`, lifecycle events) refer to the resolved identifier.

**Commitment echo.** `CommitmentPayload.policy_version` binds the commitment to the session's governance policy. An **empty** `policy_version` in the commitment matches the session's bound policy (whatever it resolved to) — a client that started with an empty `policy_version` is not required to echo a value it never sent. A **non-empty** `policy_version` MUST equal the session's resolved policy identifier exactly; otherwise the runtime MUST reject the commitment as invalid. Runtimes MUST NOT require clients to echo `policy.default` literally.

### 6.2 Commitment Evaluation

When a `Commitment` envelope is received:

1. The runtime retrieves the resolved `PolicyDescriptor` from the session.
2. The runtime evaluates the policy's `rules` against the accumulated session state (proposals, evaluations, objections, votes, or mode-equivalent messages).
3. If the policy rules are satisfied, the `Commitment` is accepted and the session resolves.
4. If the policy rules are not satisfied, the runtime MUST reject the `Commitment` with error code `POLICY_DENIED` and an informative reason string.

### 6.3 Determinism Requirement

Policy evaluation MUST be a pure function of:

- the resolved policy `rules` (immutable for the session),
- the accumulated accepted message history,
- the session's declared participants.

Policy evaluation MUST NOT depend on wall-clock time, external service calls, randomness, or any state outside the session boundary.

### 6.4 Interaction with Mode Validation

Policy evaluation layers on top of mode validation. Policy rules MAY override specific mode defaults (e.g., abstention interpretation in Quorum Mode, reassignment in Task Mode) while preserving Core invariants (isolation, monotonic lifecycle, append-only history). The interaction model is: base mode validation runs first, then policy rules adjust eligible behaviors within the boundaries established by mode validation.

1. The mode's own validation rules (message type authorization, structural validation, phase transitions) execute first.
2. Policy governance rules execute second, only for `Commitment` messages that pass mode validation.
3. A `Commitment` must satisfy both mode validation and policy governance to be accepted.

## 7. Registration Lifecycle

Policies are managed through five gRPC RPCs on `MACPRuntimeService`, mirroring the extension mode lifecycle:

| RPC | Purpose |
|-----|---------|
| `RegisterPolicy` | Register a new policy descriptor |
| `UnregisterPolicy` | Remove a registered policy (does not affect active sessions) |
| `GetPolicy` | Retrieve a policy descriptor by ID |
| `ListPolicies` | List registered policies, optionally filtered by mode |
| `WatchPolicies` | Server-streaming RPC for policy registry change notifications |

Unlike `WatchModeRegistry` (which returns a lightweight `RegistryChanged` notification), `WatchPolicies` returns the full set of current policy descriptors on each change. This design reflects that policy consumers typically need the complete rule set for evaluation, not just a change signal.

Registration constraints:

- `policy.default` MUST NOT be registered or unregistered (it is built-in).
- A `policy_id` in the reserved `policy.std.` namespace MUST NOT be registered unless the descriptor is the canonical definition for that identifier (Section 2.2), and a pre-registered `policy.std.` policy MUST NOT be unregistered.
- `policy_id` MUST be unique; re-registration of an existing ID MUST fail.
- `rules` MUST validate against the target mode's rule JSON Schema if a schema exists. This validation is an **admission-time** gate: it applies when a descriptor enters the runtime — via `RegisterPolicy` or an implementation's file-loading path — against the rule schemas that runtime ships, and never afterwards. Rule schemas MAY tighten between revisions of this specification; a tightening bars *new* admissions only and does not retroactively invalidate a descriptor already admitted or stored (Section 8, item 4).
- Unregistering a policy does not affect sessions that have already resolved it.

Canonical proto definitions: `schemas/proto/macp/v1/policy.proto`

## 8. Replay Invariant

RFC-MACP-0003 (Determinism) requires that replay under identical bound versions produces identical outcomes. This RFC extends that requirement to policies:

1. The resolved `PolicyDescriptor` MUST be persisted as part of the session snapshot.
2. During replay, the runtime MUST use the stored `PolicyDescriptor`, never re-resolving from the registry.
3. If the stored policy uses `schema_version` N, the runtime MUST evaluate using schema-version-N semantics, even if a newer schema version exists.
4. Rule-schema validation (Section 7) is an admission-time gate only. The runtime MUST NOT revalidate a stored `PolicyDescriptor` against any rule JSON Schema during replay, and MUST evaluate a stored descriptor under its declared `schema_version` even if that descriptor no longer validates against the current rule schema. A schema tightening therefore never renders a stored session unreplayable.

**Bounded exception — weight-`0` decisiveness (1.1.0-draft).** Item 3 carries one deliberate, bounded exception: under `weighted`, a `REJECT` cast by a weight-`0` participant does not satisfy the decline guard of RFC-MACP-0007 §6.2 at **any** schema version, including stored `schema_version ≤ 2` descriptors. For every configuration involving an *unlisted* voter this completes behavior the original text left undefined — the voter's weight, the `0/0` ratio, and its result classification were all unspecified — and completing undefined semantics is a precondition of item 3, not a violation of it: a runtime cannot replay under semantics that determine no outcome. In exactly one configuration the original text *did* define an outcome that this rule reverses: a descriptor with an explicit `0` in `weights` (formerly schema-legal) plus `allow_decline_over_approval: true`, where a **Passed** tally whose only reject was cast by the weight-`0` participant formerly authorized a decline and no longer does. A stored session whose accepted history contains a decline accepted under that reading will not replay identically under this text. That break is accepted because it is vanishingly narrow, because descriptors with explicit `0` weights can no longer be admitted (Section 7), and because the reversed behavior was unsound: it granted a participant the policy author had explicitly stripped of voting weight the unilateral power to convert an approving weighted electorate's outcome into a decline. This is the only change in this revision that can alter a **stored** session's replay under `schema_version ≤ 2`, and no other change that could is permitted.

**Replay-neutral v≤2 change — the objection-authorized decline (1.1.0-draft).** This revision makes one further change to `schema_version ≤ 2` semantics: a decline under `objection_handling.critical_objection_action: "finalize_decline"` is objection-authorized and is gated by neither the voting tri-state nor the decline guard, at every schema version that can express the field (`schema_version ≥ 2`; §4.1 and RFC-MACP-0007 §6.2). Unlike the exception above, this one cannot alter any stored session's replay: it moves a commitment from denied to allowed, and a runtime that previously denied it **rejected** the message — rejected envelopes never enter accepted history and never alter replay outcomes ([RFC-MACP-0001](RFC-MACP-0001-core.md) §8.3). It is recorded here so that the two v≤2 changes this revision makes are findable in one place.

**Completion — Quorum `percentage` ceiling rounding (1.2.0-draft).** Section 4.2 now states the rounding direction for the Quorum Mode `percentage` threshold **and pins its denominator to the participant count declared at `SessionStart`, unaffected by ballots subsequently cast**: the effective approval count is the **ceiling** of `value × declared_participant_count / 100`. The denominator half is a second completion, distinct from rounding: [RFC-MACP-0011](RFC-MACP-0011-quorum-mode.md) §5 rule 4a removes an abstaining participant from the pool of potential approvers, which left it arguable that the percentage base shrank with it. It does not; the base is static. Earlier normative text stated no direction, so it determined no outcome at any non-integral product; stating one completes undefined semantics, which is a precondition of item 3, not a violation of it. The direction matches the only prior statement of intent in this document — the Section 5.2 rationale, whose "`67` requires 3 of 3" example is arithmetic only under ceiling. No stored session's replay is altered unless its runtime had privately chosen a direction no text licensed.

`registered_at_unix_ms` is runtime metadata and is not part of the policy's semantic identity. Replay and policy equality comparisons MUST use `policy_id` + `schema_version` + `rules` equality, not full descriptor byte comparison.

This ensures that a session replayed years later produces identical governance outcomes regardless of registry state.

## 9. Capability Advertisement

Runtimes that support the policy framework SHOULD advertise the `policy_registry` capability during `Initialize`:

```protobuf
message PolicyRegistryCapability {
  bool register_policy = 1;
  bool list_policies = 2;
  bool list_changed = 3;
}
```

This capability is added to the `Capabilities` message. Runtimes that do not support policy registration but do support policy evaluation (e.g., file-loaded policies only) SHOULD set `register_policy = false` and `list_policies = true`.

## 10. Error Codes

The following error codes are added to the MACP Error Code Registry:

| Code | Description | HTTP Status | Status | Reference |
|------|-------------|-------------|--------|-----------|
| `UNKNOWN_POLICY_VERSION` | `policy_version` not found in policy registry at SessionStart | 404 | permanent | RFC-MACP-0012 |
| `POLICY_DENIED` | Commitment rejected because governance policy rules are not satisfied. Breaches of `commitment.authority` / `commitment.designated_roles` are the exception: those are sender-authorization failures and use `FORBIDDEN`, per [RFC-MACP-0002](RFC-MACP-0002-modes.md) §6.1 and the conformance corpus. | 403 | permanent | RFC-MACP-0012 |
| `INVALID_POLICY_DEFINITION` | Policy descriptor fails validation (bad JSON, schema mismatch, mode mismatch) | 400 | permanent | RFC-MACP-0012 |

## 11. Security Considerations

Implementations MUST address all of the following:

- authenticate senders of `RegisterPolicy` and `UnregisterPolicy` requests,
- prevent unauthorized modification of the policy registry,
- ensure that resolved policies cannot be mutated after binding to a session,
- protect policy descriptors from information disclosure if they contain sensitive governance parameters,
- preserve the complete policy evaluation trail for audit and replay.

Policy evaluation MUST NOT introduce side channels: the accept/reject decision for a `Commitment` must depend solely on session state and the bound policy, not on the identity of the commitment sender beyond what the policy's `commitment.authority` rule specifies.

## 12. Canonical Schemas and Examples

Canonical proto schema:

- `schemas/proto/macp/v1/policy.proto`

Canonical JSON Schemas for governance rules:

- `schemas/json/policy/decision-rules.schema.json`
- `schemas/json/policy/quorum-rules.schema.json`
- `schemas/json/policy/proposal-rules.schema.json`
- `schemas/json/policy/task-rules.schema.json`
- `schemas/json/policy/handoff-rules.schema.json`

Well-known policy identifiers:

- `registries/policies.md`

Example transcript:

- `examples/policy-decision-session.json`

Policy registration exchange example:

- `examples/policy-registration-exchange.json`
