# Proposal: findings from a library embedder of the MACP crates

**Document:** rfcs/proposals/seam-embedder-findings-2026-10.md
**Stage:** Idea / pre-Draft proposal. This is not a numbered RFC. It asks for discussion through the RFC-proposal issue and, for each item, a PR against the RFC it amends.
**Status:** Proposed
**Date:** 2026-10-13
**Pinned spec revision:** [`c2d0a5d`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/tree/c2d0a5d9b4b4ba2f28db2acd50e82a9a1a03a3fe) (RFC-MACP-0012 1.6.1-draft)
**Pinned reference implementation:** macp-runtime [`fb10fb2`](https://github.com/multiagentcoordinationprotocol/macp-runtime/tree/fb10fb29b0f3f76db565444d56d390824674fe04) (crates 0.8.8; code-identical to 0.8.6 apart from rustdoc)
**Amends (if accepted):** RFC-MACP-0003, 0004, 0006, 0007, 0009, 0010, 0011, 0012; `registries/error-codes.md`; `CONTRIBUTING.md`

All RFC line anchors below are at `c2d0a5d`. All implementation anchors are at `fb10fb2`.

---

## Summary

Seam is a coordination service that embeds `macp-core`, `macp-modes`, `macp-policy` and `macp-pb` as a library. It drives `macp_modes::step::step` directly and does not run `MACPRuntimeService`. Building and reviewing Seam against the RFC set exposed eleven places where the specification is silent, ambiguous, internally inconsistent, or out of step with the reference implementation. This proposal sets out each one with:

- the problem, quoted at the pinned revision;
- concrete replacement or added normative text;
- the conformance vectors that would pin it;
- a compatibility statement.

Defects that are purely implementation bugs, where the RFC is already clear, are not argued here. They are listed in the [implementation tracking](#implementation-tracking) section and filed against macp-runtime.

| # | Item | Amends | Class |
|---|---|---|---|
| S1 | No vendor-extension slot for rule keys that carry meaning | RFC-0012 §4, §8 | Security (blocks closed-rule enforcement) |
| S2 | The admission gate names the rule schemas only, not the descriptor schema | RFC-0012 §3, §7 | Security / correctness |
| S3 | No delegated (on-behalf-of) submission model for `sender` | RFC-0004 §3, §4 | Security |
| S4 | Quorum rule 6 contradicts the reference implementation's refusal | RFC-0011 §5 rule 6 | Correctness |
| S5 | "A different `target_participant`" does not say different from what | RFC-0010 §5 rule 3a | Correctness |
| S6 | The effect of a pre-assignment `TaskReject` on a broadcast task is undefined | RFC-0009 §5 rules 2, 3c | Correctness |
| S7 | Decision enums: the "UPPER_CASE, case-sensitive" rule conflicts with lowercase severities; the empty-severity default is unspecified | RFC-0007 §4 | Correctness |
| S8 | The required unauthenticated-Signal annotation has no wire field | RFC-0004 §4.1 | Editorial / security |
| S9 | RFC-0006 §3 lists 22 RPCs; `core.proto` defines 24 | RFC-0006 §3 | Editorial |
| S10 | `CANCELLED` is missing from several terminal-state lists | RFC-0003 §1, §5; error-codes; CONTRIBUTING | Editorial |
| S11 | No conformance vectors exist for S1–S7 | `schemas/conformance`, `schemas/json/tests` | Conformance |

## Motivation

RFC-MACP-0001 §2 (L55) defines a **MACP Runtime** as "the logical system responsible for enforcing session state transitions, ordering, deduplication, validation, authorization, and isolation". An embedder that mints envelopes server-side and drives the reference crates in-process meets that definition. It still has no `Send`, no `Initialize` and no `WatchSignals`.

Three properties of such an embedder expose gaps that a gRPC-only reading of the RFCs does not:

1. **It is the only party that sees the policy.** Admission rules that the reference server enforces outside the library (for example, the descriptor schema) are invisible to an embedder unless the RFC names them as admission obligations.
2. **It submits on behalf of participants.** A gateway that authenticates an owner or service principal and then emits envelopes for panel members has no sanctioned model under RFC-0004 §3. Without one, every such deployment is non-conformant by construction, and nothing distinguishes a well-designed gateway from a careless one.
3. **It needs product-specific governance keys next to standard ones.** Closed rule objects (RFC-0012 1.4.0) are the right default. However, the only escape, the `^[_$]` annotation namespace, is semantically inert by definition. An embedder with an additional restriction, such as "every vote must carry a reason", therefore has nowhere conformant to put it.

The items below are ordered security first.

---

## S1. A vendor-extension namespace in `rules` (RFC-0012 §4)

### Problem

RFC-0012 §4 (L107) makes rule objects closed:

> a runtime MUST reject at admission a `PolicyDescriptor` whose `rules` object carries an undefined key at any nesting level.

Its only escape (L109) is inert by definition:

> Keys matching the pattern `^[_$]` … carry no governance semantics, and an evaluator MUST ignore them when computing any outcome.

Some deployments carry restrictions that MACP does not define. The motivating case is Seam's `rules.seam.capture_dissent`. When it is `true`, every `Vote` and quorum ballot must carry a non-empty reason, and the runtime rejects one without a reason. That restriction:

- is not an annotation, because it changes which envelopes are accepted;
- cannot move under `_seam`, because §4 forbids giving an annotation semantics;
- cannot stay as `seam`, because §4 rejects it at admission.

As a result, an implementation that enforces §4 would refuse every such production policy. A vendor that wants conformance has only bad options:

- strip the key before admission, which hides governance-relevant content from the MACP layer and from §8 equality;
- or move the restriction out of `rules` into a side channel the specification does not see.

### Proposed normative change

Add to RFC-0012 §4, after the annotation-namespace paragraph:

> **Vendor-extension keys.** A key matching `^x-[a-z0-9]+(\.[a-z0-9-]+)+$` at the **top level** of a `rules` object is a vendor-extension key. Its name is the reverse-domain identifier of the vendor or product that defines it (for example `x-com.example.governance`), and its value MUST be a JSON object. Vendor-extension keys are not legal at any nested level.
>
> A vendor extension MAY only **restrict**: it MAY cause a runtime that implements it to reject an envelope or deny a commitment that standard rules would accept. It MUST NOT cause acceptance of anything that standard rules or mode validation reject. This is the additivity principle of RFC-MACP-0002 §8.1 applied to policy content.
>
> A runtime MUST reject at admission, with `INVALID_POLICY_DEFINITION`, a descriptor carrying a vendor-extension key that the runtime does not implement. A restriction its author relied on is never silently dropped; this is the same failure the closed-object rule prevents. A runtime MAY advertise the extensions it implements (Section 9).
>
> MACP-standard evaluation (Sections 4.1–4.5 and 6) MUST ignore vendor-extension keys when computing any standard outcome. Unlike annotation keys, vendor-extension keys **are** part of `rules` equality for Sections 2.2 and 8.

Amend §8's equality sentence to read "modulo the `^[_$]` annotation namespace of §4 (vendor-extension keys are not excluded)".

Amend §9 by adding `repeated string rule_extensions = 4;` to `PolicyRegistryCapability`. This is an additive proto change.

Schemas: add `"patternProperties": {"^x-[a-z0-9]+(\\.[a-z0-9-]+)+$": {"type": "object"}}` at the top level of each `*-rules.schema.json`. Leave nested levels at `^[_$]` only.

### Conformance vectors

- `schemas/json/tests/valid-policy-rules/vendor-extension.json`: decision rules with `x-com.example.gov: {"require_reason": true}`. Valid.
- `invalid-policy-rules/vendor-extension-nested.json`: the same key under `voting`. Invalid.
- `invalid-policy-rules/vendor-extension-non-object.json`: `"x-com.example.gov": true`. Invalid.
- `invalid-policy-rules/vendor-extension-bad-name.json`: `"x-seam": {}`, which is not reverse-domain. Invalid.
- Parity contract: a `policy_equality` vector showing that two rules objects differing only in an `x-` key are **not** equal, while two differing only in an `_` key are.

### Compatibility

The change is additive to the schemas. It changes no `schema_version` and touches no stored descriptor. Descriptors that today carry an unknown top-level key are already non-conformant under 1.4.0, so the new namespace only creates a legal home for them. The admission rejection of unimplemented extensions is new behaviour, but it applies only to keys that 1.4.0 already rejects.

---

## S2. Name the descriptor schema in the admission gate (RFC-0012 §3, §7)

### Problem

§3 (L93) says a runtime "MUST accept every schema version it supports (`{1, 2, 3}`)". `macp-policy-descriptor.schema.json` pins `schema_version` to `enum: [1, 2, 3]` (spec #115) and makes `description` required (1.5.0). However, §7's admission clause (L387) names only the **rule** schemas:

> `rules` MUST validate against the target mode's rule JSON Schema if a schema exists. This validation is an **admission-time** gate …

No sentence makes the **descriptor** schema an admission obligation. The 1.5.0 changelog acknowledges that "§7 and §8 item 4 are worded for the *rule* JSON Schemas … neither clause literally covers it."

The reference implementation reads the gap literally. macp-runtime#167 was closed on the grounds that §3 "constrains which versions a runtime *supports at evaluation*, not which ones the registry admits". So `schema_version: 99` registers (`crates/macp-policy/src/registry.rs:301` refuses only `0`) and then denies every commitment at evaluation (`crates/macp-policy/src/evaluator.rs:24-37`).

For an embedder, that turns a typo into a session that silently cannot resolve, discovered only at commit time.

### Proposed normative change

Replace the §7 bullet with:

> - The descriptor MUST validate against `schemas/json/macp-policy-descriptor.schema.json`, and `rules` MUST validate against the target mode's rule JSON Schema if one exists. Both validations are **admission-time** gates: …(remainder unchanged).

Add to §3 after L93:

> A runtime MUST reject at admission, with `INVALID_POLICY_DEFINITION`, a descriptor whose `schema_version` is not one it supports. Deferring the check to evaluation is non-conformant: it admits a policy under which no commitment can ever be authorized.

Add to §3 a note on `description`:

> On the Protobuf binding, where proto3 cannot distinguish an absent string from an empty one, an empty `description` satisfies the presence requirement.

### Conformance vectors

`invalid-policy-descriptors/schema-version-out-of-range.json` already exists. Add a runtime-facing transcript, `policy_admission_schema_version.json`, in which `RegisterPolicy` with `schema_version: 99` returns `INVALID_POLICY_DEFINITION`. This is needed because the current corpus exercises the JSON Schema but not the admission rule.

### Compatibility

The change clarifies existing intent. The only runtimes affected are those that admit out-of-range versions, and under those every commit is already denied, so nothing that works today stops working.

---

## S3. Delegated (on-behalf-of) submission (RFC-0004 §3, §4)

### Problem

RFC-0004 §3 (L36):

> The `sender` field MUST be derived from authenticated identity and MUST NOT be accepted as a self-asserted free-form value.

§4 requires the runtime to verify that "the sender is authenticated". No text covers a **gateway**: a runtime front-end that authenticates one principal, such as a service account or an orchestrating owner, and emits envelopes whose `sender` is a different session participant. Common examples:

- a council orchestrator that collects votes from model calls it makes itself;
- a human-in-the-loop UI that submits on behalf of reviewers;
- an embedder such as Seam, where only the session owner holds a credential and participants are labels on an admitted panel.

All of these are non-conformant under the literal text. Nothing distinguishes a gateway that binds each participant to an authorization grant from one that accepts any string. Today, one compromised owner credential can cast every panel member's ballot, and the specification has no vocabulary to say what a gateway owes in order to prevent that.

### Proposed normative change

Add RFC-0004 §3.1:

> ### 3.1 Delegated submission
>
> A runtime MAY accept a session-scoped envelope whose `sender` differs from the authenticated principal of the submitting connection (the **submitter**) only when all of the following hold:
>
> 1. The submitter is authenticated per Section 3.
> 2. The submitter holds a **delegation** naming that `sender` for that session, established before the envelope is accepted. Examples: a signed grant, a session-scoped token, or an operator-configured panel binding. The delegation MUST be scoped to a session, or to a set of sessions, and to the message types it covers.
> 3. The runtime records the submitter's identity alongside the accepted envelope, in a field or log annotation outside `Envelope`, so that an auditor can distinguish delegated acceptance from direct acceptance.
> 4. A runtime that accepts delegated submissions MUST advertise it (capability `security.delegated_submission`) and MUST document the delegation mechanisms it accepts.
>
> A delegation does not satisfy rule 4 of Section 4 by itself: the delegated `sender` MUST still be authorized for the session and the message type. A runtime MUST NOT treat an unscoped submitter credential as a delegation for every participant.

Add to §4's first bullet: "the sender is authenticated, **or is covered by a delegation per §3.1**".

Registry: add `security.delegated_submission` to `registries/capabilities.md`.

### Conformance vectors

These are policy-level rather than transcript-level. Add a `docs/security.md` checklist entry and a parity-contract `capabilities` entry. Transcript fixtures cannot express authentication, so none is proposed.

### Compatibility

The change is additive. Runtimes that never accept delegated submissions are unaffected. Deployments that already delegate gain a conformant path, and must add the audit record (item 3).

---

## S4. Quorum rule 6: an unreachable override (RFC-0011 §5)

### Problem

RFC-0011 §5 rule 6 (L74):

> An `n_of_m` override greater than the count of eligible participants is not rejected at admission … and simply makes the threshold unreachable, so the Session becomes eligible for `Commitment` under rule 4's second clause … with the negative outcome of rule 4b.

The reference implementation deliberately does the opposite. `crates/macp-modes/src/mode/quorum.rs:384-411` rejects the `ApprovalRequest` with `INVALID_ENVELOPE` when the effective threshold falls outside `1..=participants`. `commitment_ready` (`:328`) additionally requires `counted > 0`. Both were added for macp-runtime#145, because "the coordinator could then seal a binding negative Commitment with no ballot cast".

Reproduced against 0.8.6: under `{"threshold":{"type":"n_of_m","value":5}}` with 3 participants, `ApprovalRequest` returns `Err(InvalidPayload)`.

Two conformant-looking runtimes therefore disagree. Under rule 6 as written, a coordinator can seal `quorum.rejected` before any participant has seen the request. That is a binding adverse outcome with no participant input, which is the hazard #145 closed.

### Proposed normative change

Replace the third sentence of rule 6 with:

> An `n_of_m` override greater than the count of eligible participants, or a `percentage` override that resolves to an effective count of zero or above that count, makes the request unsatisfiable. A runtime MUST reject the `ApprovalRequest` with `INVALID_ENVELOPE` when its effective threshold, after the override, lies outside `1..=eligible participants`. The rule schema cannot see a participant count, so this check happens at `ApprovalRequest`, not at policy admission. Because the request never enters history, no negative `Commitment` can be sealed without a ballot.

Delete the sentence beginning "Note that rule 4b's own antecedent …", which the new text makes moot. Add to rule 4: "The second clause applies only once at least one ballot has been accepted."

### Conformance vectors

- `quorum_reject_paths.json`: add a case where the policy override `n_of_m 5` over 3 participants causes `ApprovalRequest` to be rejected with `INVALID_ENVELOPE`.
- A case where `percentage 100` over 3 participants is accepted, with the effective threshold of 3 within range.
- A case where `Commitment` with `outcome_positive: false` before any ballot is rejected `INVALID_ENVELOPE`.

### Compatibility

This changes behaviour for runtimes that follow the current text literally. No stored history is affected: the rejected `ApprovalRequest` never entered history, and a session sealed negative with zero ballots replays identically because replay does not revalidate. If the maintainers prefer the current text, the alternative is to keep rule 6 and have the reference implementation drop its refusal. Either way, the RFC and the reference implementation must agree.

---

## S5. Re-offer after a decline (RFC-0010 §5 rule 3a)

### Problem

RFC-0010 §5 rule 3a (L69):

> If the target declines or is unreachable, a new `HandoffOffer` MUST be issued with a different `target_participant` and a new `handoff_id`.

The rule does not say whether "different" means different from the declining target or from every prior target. The reference implementation enforces neither (`crates/macp-modes/src/mode/handoff.rs:483-503`). Reproduced: offer `h1` goes to `t1`, `t1` declines, and offer `h2` to `t1` is accepted. This lets an owner pressure a target into accepting by re-offering repeatedly.

### Proposed normative change

Replace the second sentence of 3a with:

> If the target declines, a new `HandoffOffer` MUST carry a new `handoff_id` and a `target_participant` that has not previously declined an offer in this Session; a runtime MUST reject it with `INVALID_ENVELOPE` otherwise. An offer that expired unanswered under no implicit-accept policy does not bar its target from a later offer.

### Conformance vectors

`handoff_reject_paths.json`: Offer(h1→t1) accepted; Decline(h1, t1) accepted; Offer(h2→t1) rejected `INVALID_ENVELOPE`; Offer(h3→t2) accepted.

### Compatibility

This tightens validation. Histories that already contain a re-offer to a declined target replay unchanged, because replay does not revalidate client-boundary rules.

---

## S6. Pre-assignment `TaskReject` on a broadcast task (RFC-0009 §5)

### Problem

Rule 2 (L68) lets any eligible declared participant send `TaskReject` when `requested_assignee` is empty. Rule 3a (L70) designates the first accepted `TaskAccept` as assignee. Rule 3c (L72) and `allow_reassignment_on_reject` concern only the **active assignee** rejecting. Nothing says what a `TaskReject` from a non-assigned participant does before anyone has accepted.

The reference implementation treats it as a reassignment trigger (`crates/macp-modes/src/mode/task.rs:228-243`). Reproduced: on a broadcast task, a reject from `w1` causes a later first-ever `TaskAccept` from `w2` to be refused with `POLICY_DENIED` ("reassignment after rejection not allowed by policy"). So one participant's decline vetoes the whole pool, which contradicts rule 3a's "from any eligible participant".

### Proposed normative change

Add rule 2a:

> 2a. When `requested_assignee` is empty, a `TaskReject` from an eligible participant while no assignee is active records that participant's decline only. It does not change the eligibility of other participants, and `allow_reassignment_on_reject` does not govern it. A participant that has declined MUST NOT later send `TaskAccept` for the same task. When `requested_assignee` is non-empty, that participant's `TaskReject` leaves no eligible assignee, and the Session becomes eligible for a negative `Commitment`.

### Conformance vectors

`task_reject_paths.json`: on a broadcast task, `w1` sends TaskReject (accept), `w2` sends TaskAccept (accept, assignee `w2`), and `w1` sends TaskAccept (reject `INVALID_ENVELOPE`).

### Compatibility

This relaxes validation in one case. Runtimes that refuse the `w2` accept today rejected an envelope, which never entered history, so replay is unaffected.

---

## S7. Decision Mode enum casing (RFC-0007 §4)

### Problem

L80 says: "All enum-like string values in Decision Mode use UPPER_CASE. Comparisons MUST be case-sensitive." L76 and `decision.proto:22` define Objection severity as lowercase (`low | medium | high | critical`), and so does `critical_severity_vetoes` matching on `"critical"`. The rule is therefore false of one of the four enums it covers.

The reference implementation is case-insensitive for all four (`crates/macp-modes/src/mode/decision.rs:179,190,207-208,226`). Reproduced: `Vote{vote:"approve"}` is accepted. An empty `severity` silently becomes `"medium"` (`:203-205`), and no RFC states that default.

### Proposed normative change

Replace L80 with:

> `Evaluation.recommendation` and `Vote.vote` values are UPPER_CASE; `Objection.severity` values are lowercase. Comparisons MUST be case-sensitive, and a runtime MUST reject with `INVALID_ENVELOPE` a value that matches a defined value only case-insensitively. An empty `Objection.severity` MUST be rejected with `INVALID_ENVELOPE`.

The maintainers may instead prefer to codify `medium` as the default for an empty severity. That is acceptable, but it must be written down, because severity drives `critical_severity_vetoes`.

### Conformance vectors

`decision_reject_paths.json` gains three rejections, each `INVALID_ENVELOPE`:

- `Vote{vote:"approve"}`;
- `Evaluation{recommendation:"Approve"}`;
- `Objection{severity:""}` (or, under the alternative, an accept that pins `medium`).

### Compatibility

This tightens validation. Clients sending non-canonical casing break, which is the intent of the existing MUST. Stored histories replay unchanged.

---

## S8. Unauthenticated-Signal annotation has no wire field (RFC-0004 §4.1)

### Problem

L48 says unauthenticated Signals "MUST NOT … be forwarded to `WatchSignals` subscribers without annotation indicating their unauthenticated status". `WatchSignalsResponse` (`core.proto:409-411`) carries only `Envelope envelope = 1`, and `Envelope` (`envelope.proto`) has no authentication field. The MUST therefore cannot be met on the gRPC binding.

### Proposed normative change

Add `bool sender_authenticated = 2;` to `WatchSignalsResponse`, which is an additive proto change. Amend L48 to: "…without `WatchSignalsResponse.sender_authenticated = false`." Add the same flag to the HTTP and WebSocket bindings in RFC-0006 where Signals are delivered.

### Conformance vectors

None as a transcript. Add a `schemas/parity/contract.json` proto-field entry.

### Compatibility

Additive. Old clients ignore the field. In proto3 an absent field reads as `false` (unauthenticated), which is the safe direction.

---

## S9. RFC-0006 §3 RPC listing (editorial)

### Problem

The `MACPRuntimeService` block in RFC-0006 §3 (L57-L84) lists 22 RPCs. `schemas/proto/macp/v1/core.proto` defines 24. `SuspendSession` and `ResumeSession`, which RFC-0001 §7.5 depends on, are missing. The text calls the proto authoritative, but the listing is the copy readers see.

### Proposed change

Insert `rpc SuspendSession(…)` and `rpc ResumeSession(…)` after `CancelSession`. Extend `scripts/check-proto-parity.sh` (or `check-prose.py`) to assert that the listing equals the proto's `rpc` set.

### Compatibility

Editorial.

---

## S10. `CANCELLED` missing from terminal-state lists (editorial)

### Problem

RFC-0001 §7.2 (L230-L240) defines three terminal states: `RESOLVED`, `EXPIRED` and `CANCELLED`. These sites still list two:

- RFC-0003 §1 (L30): "produce the same terminal state (RESOLVED or EXPIRED)";
- RFC-0003 §5 (L106): "identical lifecycle transitions (OPEN, RESOLVED, EXPIRED)", which also omits `SUSPENDED`;
- `registries/error-codes.md` (L16): `SESSION_NOT_OPEN` reads "Session already resolved or expired", although §7.5 also returns it for `SUSPENDED` sessions and §7.3 returns it for `CANCELLED` ones;
- `CONTRIBUTING.md` (L9): "Monotonic lifecycle (OPEN → RESOLVED | EXPIRED)".

### Proposed change

- RFC-0003 §1: "(RESOLVED, EXPIRED, or CANCELLED)".
- RFC-0003 §5: "(OPEN, SUSPENDED, RESOLVED, EXPIRED, CANCELLED)".
- `error-codes.md`: "Session is not OPEN (resolved, expired, cancelled, or suspended)".
- `CONTRIBUTING.md`: "OPEN → RESOLVED | EXPIRED | CANCELLED".
- Add the four sites to `check-prose.py`'s state-list agreement check.

### Compatibility

Editorial.

---

## S11. Conformance coverage summary

The vectors proposed above, collected for one PR:

| Corpus | New files / cases |
|---|---|
| `schemas/json/tests/valid-policy-rules/` | `vendor-extension.json` (S1) |
| `schemas/json/tests/invalid-policy-rules/` | `vendor-extension-nested.json`, `vendor-extension-non-object.json`, `vendor-extension-bad-name.json` (S1) |
| `schemas/json/tests/invalid-policy-rules/` | `veto-threshold-zero.json`, `minimum-confidence-above-one.json`. These already violate the schema; they are added so that the §7 admission gate is exercised for range constraints, not only for unknown keys |
| `schemas/conformance/` | `policy_admission_schema_version.json` (S2); cases in `quorum_reject_paths.json` (S4), `handoff_reject_paths.json` (S5), `task_reject_paths.json` (S6) and `decision_reject_paths.json` (S7) |
| `schemas/parity/contract.json` | `policy_equality` vendor-extension vector (S1); `WatchSignalsResponse.sender_authenticated` (S8) |

---

## Implementation tracking

Implementation items in macp-runtime where the RFC is already clear are filed separately at https://github.com/multiagentcoordinationprotocol/macp-runtime/issues/227. In summary:

- **I3.** No RFC-0013 §5/§6 verify API that can return *cannot-verify*.
- **I4.** `macp_modes::step` never synthesizes the RFC-0010 §5.1(2) implicit `HandoffAccept`, and it dispatches through `on_message` (the envelope clock) rather than `on_message_at`. Step-only embedders therefore cannot meet §5.1 at `semantics_rev ≥ 2`.
- **I5.** `step` skips per-message checks that the server performs outside the library, such as `macp_version` and session-id strength, and does not document them as embedder obligations.
- **I6.** `schema_version` outside `{1, 2, 3}` is admitted and then denies every commit (S2).
- **I7–I10.** Task pre-assignment reject (S6), handoff re-offer to a declined target (S5), the quorum unreachable-override divergence (S4), and decision enum casing (S7). Each is resolved whichever way the corresponding spec item lands.
- **I11.** No public resolver for the session-bound suspend cap.

## Disclosure

The author operates Seam, whose production policies use `rules.seam.capture_dissent`. S1 therefore resolves a conformance problem for the author's own deployment. The proposed design is vendor-neutral: restrict-only, fail-closed on unknown extensions, and included in equality. It is offered so that closed-rule enforcement can be applied by every runtime without breaking any embedder.
