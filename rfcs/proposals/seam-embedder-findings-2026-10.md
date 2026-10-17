# Proposal: findings from a library embedder of the MACP crates

**Document:** rfcs/proposals/seam-embedder-findings-2026-10.md
**Stage:** Idea / pre-Draft proposal. This is not a numbered RFC. It asks for discussion through the RFC-proposal issue and, for each item, a PR against the RFC it amends.
**Status:** Proposed
**Date:** 2026-10-13 (revised 2026-10-16: S12–S14 and I12–I17 added)
**Pinned spec revision:** [`c2d0a5d`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/tree/c2d0a5d9b4b4ba2f28db2acd50e82a9a1a03a3fe) (RFC-MACP-0012 1.6.1-draft)
**Pinned reference implementation:** macp-runtime [`fb10fb2`](https://github.com/multiagentcoordinationprotocol/macp-runtime/tree/fb10fb29b0f3f76db565444d56d390824674fe04) (crates 0.8.8; code-identical to 0.8.6 apart from rustdoc)
**Amends (if accepted):** RFC-MACP-0001, 0003, 0004, 0006, 0007, 0009, 0010, 0011, 0012, 0013; `registries/error-codes.md`; `schemas/conformance/schema.json`; `CONTRIBUTING.md`

All RFC line anchors below are at `c2d0a5d`. All implementation anchors are at `fb10fb2`.

---

## Summary

Seam is a coordination service that embeds `macp-core`, `macp-modes`, `macp-policy` and `macp-pb` as a library. It drives `macp_modes::step::step` directly and does not run `MACPRuntimeService`. Building and reviewing Seam against the RFC set exposed fourteen places where the specification is silent, ambiguous, internally inconsistent, or out of step with the reference implementation. This proposal sets out each one with:

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
| S4 | The reference implementation's refusal contradicts quorum rule 6; the RFC stands | RFC-0011 §5 rule 6 (vectors only) | Correctness |
| S5 | "A different `target_participant`" does not say different from what | RFC-0010 §5 rule 3a | Correctness |
| S6 | The effect of a pre-assignment `TaskReject` on a broadcast task is undefined | RFC-0009 §5 rules 2, 3c | Correctness |
| S7 | Decision enums: the "UPPER_CASE" text is wrong for lowercase severities; empty severity is invalid per the RFC | RFC-0007 §4 | Correctness |
| S8 | The required unauthenticated-Signal annotation has no wire field | RFC-0004 §4.1 | Editorial / security |
| S9 | RFC-0006 §3 lists 22 RPCs; `core.proto` defines 24 | RFC-0006 §3 | Editorial |
| S10 | `CANCELLED` is missing from several terminal-state lists | RFC-0003 §1, §5; error-codes; CONTRIBUTING | Editorial |
| S11 | No conformance vectors exist for S1–S7 and S12–S14 | `schemas/conformance`, `schemas/json/tests` | Conformance |
| S12 | Acceptance obligations that hold regardless of transport are not stated as such | RFC-0001 §2, new §7.6; RFC-0010 §5.1 | Security / correctness |
| S13 | The error-code registry maps codes to HTTP only, and `POLICY_DENIED` has no structured detail | `registries/error-codes.md`; RFC-0006 §3; RFC-0012 §6 | Correctness |
| S14 | No conformance vector exercises RFC-0013 *cannot-verify* or *mismatch* | RFC-0013 §5, §6; `schemas/conformance/cmt-hash` | Conformance |

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

## S4. Quorum rule 6: the reference implementation diverges from the RFC (RFC-0011 §5)

### Problem

RFC-0011 §5 rule 6 (L74):

> An `n_of_m` override greater than the count of eligible participants is not rejected at admission … and simply makes the threshold unreachable, so the Session becomes eligible for `Commitment` under rule 4's second clause … with the negative outcome of rule 4b.

The reference implementation deliberately does something different, and two conformant-looking runtimes therefore disagree:

- `crates/macp-modes/src/mode/quorum.rs:384-411` rejects the `ApprovalRequest` with `INVALID_ENVELOPE` when the effective threshold falls outside `1..=participants`.
- `commitment_ready` (`:327-328`) additionally requires `counted > 0` before a negative `Commitment`.

Both were added for macp-runtime#145. Reproduced against 0.8.6: under `{"threshold":{"type":"n_of_m","value":5}}` with 3 participants, `ApprovalRequest` returns `Err(InvalidPayload)`.

### Resolution (owner decision, 2026-10-16)

**The RFC text is normative, and the implementation conforms to it.** Rule 6 is internally consistent:

- rule 2 bounds only the `ApprovalRequest` payload;
- a policy override "is evaluated as given";
- rule 4's second clause makes an unreachable threshold eligible for a negative `Commitment`, and rule 4b supplies its shape. The RFC itself notes that rule 4b's antecedent does not literally cover this case, and names rule 4 as the operative clause.

The consequence that #145 objected to is that a coordinator can seal `quorum.rejected` with no ballot cast once an unreachable override is bound. That consequence follows from a misconfigured policy, which RFC-0012 admits on purpose because the schema cannot see participant counts. It does not follow from a defect in the text. **No normative change is proposed.**

Deployments that want to refuse such policies can do so by binding policies per session after checking the participant count. That restriction is outside the RFC's scope.

### Conformance vectors

Pin the RFC behaviour in `quorum_negative_outcome.json` (or `quorum_reject_paths.json`):

- An override `n_of_m 5` over 3 participants. `ApprovalRequest` is **accepted**, and a `Commitment` with `outcome_positive: false` is **accepted** immediately, with no ballot.
- An override `percentage 100` over 3 participants. `ApprovalRequest` is accepted with an effective threshold of 3. A negative `Commitment` before any ballot is rejected with `INVALID_ENVELOPE`, because the threshold is still reachable.

### Compatibility

There is no spec change. The reference implementation loosens validation in one case (I9). No stored history is affected: no request was refused in the past that could now appear in history, and replay does not revalidate.

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

## S7. Decision Mode enum casing: the RFC text is wrong for severity (RFC-0007 §4)

### Problem

L80 says: "All enum-like string values in Decision Mode use UPPER_CASE. Comparisons MUST be case-sensitive." However, L76 and `decision.proto:22` define Objection severity as lowercase (`low | medium | high | critical`), and so does `critical_severity_vetoes` matching on `"critical"`. **The RFC text is therefore wrong**: L80 is false of one of the four enums it covers.

The reference implementation is case-insensitive for all four (`crates/macp-modes/src/mode/decision.rs:179,190,207-208,226`). Reproduced: `Vote{vote:"approve"}` is accepted.

An empty `severity` silently becomes `"medium"` (`:203-205`). No RFC states that default: L76 defines severity as one of four values, and the empty string is not one of them.

### Resolution (owner decision, 2026-10-16)

The RFC is normative and the implementation conforms to it. The one place where the text is itself wrong, L80's casing claim for severity, is fixed in the text. Replace L80 with:

> `Evaluation.recommendation` and `Vote.vote` values are UPPER_CASE; `Objection.severity` values are lowercase, as listed above. Comparisons MUST be case-sensitive: a value that matches a defined value only case-insensitively is not a valid value and MUST be rejected with `INVALID_ENVELOPE`.

Empty severity follows the RFC as written. L76 makes severity one of `low`, `medium`, `high` or `critical`, so an empty or unlisted severity is not a valid value and is rejected with `INVALID_ENVELOPE`. No default exists, and the implementation's `medium` default is removed (I10). To make this explicit, add after L76: "An `Objection` whose `severity` is not one of these values MUST be rejected with `INVALID_ENVELOPE`."

### Conformance vectors

`decision_reject_paths.json` gains four rejections, each `INVALID_ENVELOPE`:

- `Vote{vote:"approve"}`;
- `Evaluation{recommendation:"Approve"}`;
- `Objection{severity:"CRITICAL"}`;
- `Objection{severity:""}`.

### Compatibility

This tightens validation. Clients that send non-canonical casing or an empty severity break, which is the intent of the existing MUST. Stored histories replay unchanged.

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

## S12. Acceptance obligations that hold regardless of transport (RFC-0001 §2, new §7.6; RFC-0010 §5.1)

### Problem

RFC-0001 §2 (L55) makes any system that enforces session state transitions, deduplication, validation and authorization a MACP Runtime. The obligations such a runtime owes on each envelope are spread across the RFC set, and several are written as properties of the gRPC server rather than of acceptance:

- the `macp_version` check (RFC-0001 §5, `UNSUPPORTED_PROTOCOL_VERSION`);
- session-id strength (RFC-0004 §11.2, L127: "cryptographically strong and unguessable"), with no stated acceptance format and no error code named in the RFC text (`INVALID_SESSION_ID` appears only in the registry);
- the policy/mode binding at `SessionStart` (RFC-0012 §6.1 step 5);
- the timing source. RFC-0010 §5.1(1) requires the runtime's recorded acceptance time, never the envelope timestamp, but only for the implicit-accept timeout. TTL (§7.1) and suspension (§7.5) do not restate it.
- the synthetic `HandoffAccept` of RFC-0010 §5.1(2), which must enter history "before any `Commitment` evaluation".

The reference library performs only some of these inside `macp_modes::step::step`. `check_preconditions` (`crates/macp-modes/src/step.rs:43-61`) checks dedup, mode, TTL and OPEN state. The version check (`src/server.rs:115`), session-id acceptance (`src/runtime.rs:384`), policy/mode binding, suspend-cap resolution (`src/runtime.rs:487-495`) and implicit-accept synthesis (`src/runtime.rs:748`) live in the server binary. An embedder that reads the RFCs as server obligations, and the library as the runtime, ships without them.

The implicit-accept case was reproduced against `fb10fb2`. A handoff session at the builder-default `semantics_rev` 3 binds `implicit_accept_timeout_ms: 1000`. An offer is accepted at t=1 000 000, and a `Commitment` is stepped at t=1 010 000. `HandoffMode::due_synthetic_envelope` returns `Some` at that instant, but `step` never asks for it, and the `Commitment` returns `Err(InvalidPayload)`. With the envelope clock at 0, which is what an embedder that mints envelopes without timestamps passes, the offer records `offered_at_ms = 0` and `due_synthetic_envelope` returns `None` permanently (`crates/macp-modes/src/mode/handoff.rs:403-460`).

### Proposed normative change

Add to RFC-0001 a new §7.6:

> ### 7.6 Acceptance obligations
>
> The obligations in this section bind every MACP Runtime, whatever its transport, including a runtime that embeds a library implementation and has no `MACPRuntimeService` endpoint. A library that offers a single-envelope acceptance entry point SHOULD perform each of them, and MUST document each one it leaves to its caller.
>
> 1. **Version.** An envelope whose `macp_version` is not a version the runtime supports (the negotiated version, where `Initialize` applies) MUST be rejected with `UNSUPPORTED_PROTOCOL_VERSION`.
> 2. **Session identifier.** A `SessionStart` whose `session_id` does not meet RFC-MACP-0004 §11.2 MUST be rejected with `INVALID_SESSION_ID`. A runtime MUST document the formats it accepts. A UUID v4 or v7 in lowercase hyphenated form, or a base64url token of at least 22 characters, meets §11.2.
> 3. **Policy binding.** RFC-MACP-0012 §6.1 applies at every `SessionStart`, including step 5 (mode mismatch).
> 4. **Acceptance time.** Every time-dependent rule, including TTL (§7.1), suspension banking (§7.5) and Mode timeouts such as RFC-MACP-0010 §5.1, MUST be evaluated against the runtime's recorded acceptance time. It MUST NOT be evaluated against `Envelope.timestamp_unix_ms`. The runtime MUST record the acceptance time with the accepted envelope so that replay reproduces it.
> 5. **Due synthetic envelopes.** Before evaluating a session-scoped envelope, the runtime MUST append every synthetic envelope that a Mode specifies as due at that acceptance time, such as RFC-MACP-0010 §5.1(2). Observation at evaluation time is sufficient. A timer or sweep is RECOMMENDED but not required.
> 6. **Duplicates.** A duplicate (§8.2) MUST be reported to the submitter distinctly from a first acceptance and from every other rejection, either as `DUPLICATE_MESSAGE` or as an idempotent success that the submitter can recognise as a replay. This lets a caller tell a retried submission from a new one.

Amend RFC-0010 §5.1(2) to cite RFC-0001 §7.6 item 5 rather than restating the obligation.

### Conformance vectors

- Extend `schemas/conformance/schema.json` with an optional per-step `accepted_at_ms`. It is the acceptance clock the harness passes, and is distinct from the envelope's `timestamp_unix_ms`. Existing transcripts need no change.
- `handoff_implicit_accept.json` is a new transcript. It binds a policy with `implicit_accept_timeout_ms: 1000`. `HandoffOffer` is accepted at `accepted_at_ms` 1000, with envelope timestamp 0. `Commitment` is accepted at 2500. The expected history contains the synthetic `HandoffAccept` (`implicit: true`) immediately before the `Commitment`. A second case resumes the session from `SUSPENDED` and shows that the suspended interval does not count.
- `session_start_reject_paths.json` is a new transcript. It covers a short `session_id` (`INVALID_SESSION_ID`), an uppercase UUID (`INVALID_SESSION_ID`), `macp_version` `"2.0"` (`UNSUPPORTED_PROTOCOL_VERSION`), and a policy bound to another mode (`INVALID_POLICY_DEFINITION`).

### Compatibility

These are clarifications. Every obligation already exists in the RFC set or the reference server. A library whose entry point adds these checks changes behaviour for embedders that relied on their absence. That is the intent.

---

## S13. Error codes: transport status and structured denial detail (`registries/error-codes.md`; RFC-0006 §3; RFC-0012 §6)

### Problem

The registry gives each code an HTTP status and nothing for gRPC. RFC-0006 L231 requires the HTTP binding to map "per the error-codes registry", but states no equivalent for the gRPC binding. The reference server maps codes in its own way (`src/server.rs:759-788`), and two of those mappings disagree with the registry's HTTP column:

- `POLICY_DENIED` becomes `FAILED_PRECONDITION`, where the registry's 403 corresponds to `PERMISSION_DENIED`;
- `SESSION_NOT_FOUND`, `SESSION_NOT_OPEN` and `INVALID_ENVELOPE` fall through to `FAILED_PRECONDITION`, where the registry has 404, 409 and 400.

An embedder that exposes its own gRPC API has no normative mapping to follow. `MacpError::error_code()` (`crates/macp-core/src/error.rs:55`) gives the registry code, but gives no status.

`POLICY_DENIED` carries reasons only as free text. The reference evaluator embeds participant identifiers in that text, for example "N blocking objection(s) (veto threshold: N), from: a, b" (`crates/macp-policy/src/evaluator.rs:232`). A runtime that must not disclose objector identities to the submitter therefore has to parse prose to redact them.

### Proposed normative change

- Add a **gRPC Status** column to the registry, aligned with the HTTP column:

  | Code | gRPC status |
  |---|---|
  | `UNAUTHENTICATED` | `UNAUTHENTICATED` |
  | `FORBIDDEN` | `PERMISSION_DENIED` |
  | `POLICY_DENIED` | `PERMISSION_DENIED` |
  | `SESSION_NOT_FOUND` | `NOT_FOUND` |
  | `UNKNOWN_POLICY_VERSION` | `NOT_FOUND` |
  | `SESSION_NOT_OPEN` | `FAILED_PRECONDITION` |
  | `DUPLICATE_MESSAGE` | `ALREADY_EXISTS` |
  | `SESSION_ALREADY_EXISTS` | `ALREADY_EXISTS` |
  | `INVALID_ENVELOPE` | `INVALID_ARGUMENT` |
  | `UNSUPPORTED_PROTOCOL_VERSION` | `INVALID_ARGUMENT` |
  | `MODE_NOT_SUPPORTED` | `INVALID_ARGUMENT` |
  | `INVALID_SESSION_ID` | `INVALID_ARGUMENT` |
  | `INVALID_POLICY_DEFINITION` | `INVALID_ARGUMENT` |
  | `PAYLOAD_TOO_LARGE` | `RESOURCE_EXHAUSTED` |
  | `RATE_LIMITED` | `RESOURCE_EXHAUSTED` |
  | `INTERNAL_ERROR` | `INTERNAL` |

- Add to RFC-0006 §3: "The gRPC binding MUST map error codes to gRPC status codes per the error-codes registry."
- Add to RFC-0012 §6.2: "A `POLICY_DENIED` rejection SHOULD carry its reasons as structured detail. Each reason carries a stable reason identifier, such as `veto`, `quorum_not_met`, `threshold_not_met`, `confidence_below_minimum` or `no_votes`, and lists the participant identifiers it relates to separately from its message. Participant identifiers MUST NOT appear only inside free text."

### Conformance vectors

Add a parity-contract `error_status` table equal to the new registry column, so that `check-proto-parity.sh` fails on drift.

### Compatibility

The new registry column is additive. Clients that branch on the reference server's current `FAILED_PRECONDITION` for `POLICY_DENIED` see a status change when the server conforms. Release notes should call this out. The structured detail is additive (SHOULD).

---

## S14. RFC-0013 verification outcomes have no vectors (RFC-0013 §5, §6)

### Problem

RFC-0013 defines three verification outcomes:

- **match**;
- **mismatch** (§6, L85);
- **cannot-verify** (§5, L72 and L77): "a `CommitmentPayload` carrying a field unrecognized under `macp-commitment-hash/1` is cannot-verify, never silently ignored".

The five vectors in `schemas/conformance/cmt-hash/` are all compute vectors: payload in, hash out. Nothing pins the other two outcomes. An implementation that drops unknown fields and hashes the rest passes every vector, yet violates §5. The reference crate exposes only a compute function (`crates/macp-core/src/commitment_hash.rs:44`), which never fails and has no verify entry point.

An embedder that seals the hash of a superseded commitment into an audit record must verify the hash a client asserts. Without a verify contract it cannot distinguish "this payload is outside the label" from "this hash is wrong".

### Proposed normative change

Add to RFC-0013 §6:

> An implementation that offers verification MUST expose it as an operation distinct from computation, taking the payload's wire encoding (so that unknown fields remain observable) and a claimed hash, and returning exactly one of *match*, *mismatch* or *cannot-verify*. A claimed hash that is not in canonical form (§9) is *mismatch*.

Extend `vector-schema.json` with optional `wire_hex` (the payload's Protobuf encoding), `claimed_hash` and `expected_outcome` (`match | mismatch | cannot_verify`). Existing vectors are unchanged and continue to mean *match* on their computed hash.

### Conformance vectors

- `cmt_hash_006_unknown_field.json`: `wire_hex` with field 99 set; `expected_outcome: cannot_verify`.
- `cmt_hash_007_mismatch.json`: the payload of `001` with a claimed hash differing in one hex digit; `mismatch`.
- `cmt_hash_008_noncanonical_claim.json`: the hash of `001` in uppercase hex; `mismatch`.
- `cmt_hash_009_unknown_supersedes_field.json`: an unknown field inside `supersedes`; `cannot_verify`.

### Compatibility

Additive. No hash value changes, and the label stays `macp-commitment-hash/1`.

---

## S11. Conformance coverage summary

The vectors proposed above, collected for one PR:

| Corpus | New files / cases |
|---|---|
| `schemas/json/tests/valid-policy-rules/` | `vendor-extension.json` (S1) |
| `schemas/json/tests/invalid-policy-rules/` | `vendor-extension-nested.json`, `vendor-extension-non-object.json`, `vendor-extension-bad-name.json` (S1) |
| `schemas/json/tests/invalid-policy-rules/` | `veto-threshold-zero.json`, `minimum-confidence-above-one.json`. These already violate the schema; they are added so that the §7 admission gate is exercised for range constraints, not only for unknown keys |
| `schemas/conformance/` | `policy_admission_schema_version.json` (S2); cases in `quorum_negative_outcome.json` (S4, pinning the existing rule 6), `handoff_reject_paths.json` (S5), `task_reject_paths.json` (S6) and `decision_reject_paths.json` (S7) |
| `schemas/parity/contract.json` | `policy_equality` vendor-extension vector (S1); `WatchSignalsResponse.sender_authenticated` (S8); `error_status` table (S13) |
| `schemas/conformance/schema.json` | optional per-step `accepted_at_ms` (S12) |
| `schemas/conformance/` | `handoff_implicit_accept.json`, `session_start_reject_paths.json` (S12) |
| `schemas/conformance/cmt-hash/` | `vector-schema.json` gains `wire_hex`, `claimed_hash`, `expected_outcome`; `cmt_hash_006`–`009` (S14) |

---

## Implementation tracking

Implementation items in macp-runtime where the RFC is already clear are filed separately at https://github.com/multiagentcoordinationprotocol/macp-runtime/issues/227. Their phasing is in macp-runtime `plans/seam-upstream-2026-10.md`, which is not tracked in git. In summary:

- **I3.** There is no RFC-0013 §5/§6 verify API that can return *cannot-verify*. It is pinned by S14.
- **I4.** `macp_modes::step` never synthesizes the RFC-0010 §5.1(2) implicit `HandoffAccept`, and it dispatches through `on_message` (the envelope clock) rather than `on_message_at`. Step-only embedders therefore cannot meet §5.1 at `semantics_rev ≥ 2`. This is reproduced in S12 and pinned by `handoff_implicit_accept.json`.
- **I5.** `step` skips per-message checks that the server performs outside the library, such as `macp_version` and session-id strength, and does not document them as embedder obligations (S12).
- **I6.** A `schema_version` outside `{1, 2, 3}` is admitted, and then every commit is denied (S2).
- **I7–I10.** These cover the task pre-assignment reject (S6) and the handoff re-offer to a declined target (S5). They also cover the quorum unreachable-override divergence (S4): the implementation conforms to RFC rule 6, dropping the `ApprovalRequest` refusal and the `counted > 0` gate for an unreachable threshold. Finally they cover decision enum casing and empty severity (S7): comparisons become case-sensitive, and an empty severity is rejected rather than defaulting to `medium`.
- **I11.** There is no public resolver for the session-bound suspend cap.
- **I12.** `MacpError` has `error_code()` (`crates/macp-core/src/error.rs:55`) but no transport status, and the server's private mapping (`src/server.rs:759`) diverges from the registry. `PolicyDenied { reasons: Vec<String> }` has no structured reasons (S13).
- **I13.** No library entry point accepts a `SessionStart`. Today an embedder must reproduce the server's `macp_version`, session-id, canonical payload, RFC-0012 §6.1 policy/mode binding and suspend-cap resolution (`src/runtime.rs:384-500`). It must also know that `Session::builder` defaults `semantics_rev` to the current revision and `ttl_expiry` to unbounded (`crates/macp-core/src/session.rs:241`) (S12).
- **I14.** The suspend-cap and cycle-cap expiry check lives only in the server (`src/runtime.rs:1248-1256`). `step`'s TTL precheck does not apply it, and `Session` has no public operation to expire (S12 item 4).
- **I15.** No library replay helper re-drives history at recorded acceptance times through `on_message_at`. The server's `src/replay.rs:133` does this, but it is not reusable.
- **I16.** Admission-time value-domain checks for rule fields that the rule schemas already bound are tracked separately. They are exercised by the S11 range vectors.
- **I17.** Several embedder needs are already met at `fb10fb2` and need only documentation:
  - `StepOutcome::Duplicate` (`crates/macp-modes/src/step.rs:111-116`) is the duplicate signal;
  - `macp_core::session::validate_session_id_for_acceptance` (`crates/macp-core/src/session.rs:686`) is public;
  - `macp_core::commitment_hash::commitment_hash` (`crates/macp-core/src/commitment_hash.rs:44`) is public;
  - `MacpError::error_code()` is public;
  - wildcard (`"*"`) policies are validated against every standards-track mode (`crates/macp-policy/src/registry.rs:384-392`);
  - `voting.threshold` is range-checked at admission (`:585`).

## Disclosure

The author operates Seam, whose production policies use `rules.seam.capture_dissent`. S1 therefore resolves a conformance problem for the author's own deployment. If S1 is accepted, Seam will rename the key to the `x-<reverse-domain>` form and enforce it in its own evaluator. The proposed design is vendor-neutral: restrict-only, fail-closed on unknown extensions, and included in equality. It is offered so that closed-rule enforcement can be applied by every runtime without breaking any embedder.
