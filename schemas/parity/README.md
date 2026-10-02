# `contract.json` — cross-implementation parity contract

## Purpose

This directory holds `contract.json`, a small, hand-maintained manifest pinning values that
today already agree — with matching values but no shared source of truth — across this
repo (where applicable), `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript`.
`scripts/check-parity-contract.py` holds every value that has an in-repo source (a
registry, an RFC prose block, a JSON Schema, or the example/conformance corpora) to that
source, so this file is never itself an unverified third copy of anything. It does not cover
everything: a value whose `source` declares it a convention with no in-repo home often has
nothing to hold it to. Some are held to other values inside this manifest instead — among them
`retry.backoff_schedule_seconds`, recomputed from the `retry` fields it derives from;
`retry.retryable_error_codes`, every member of which must appear in this manifest's own
`error_codes.permanent`; `contribute_payload`'s two `first_byte` discriminator bytes, which
must be the bytes every vector actually leads with; and `commitment_hash.accept`/
`commitment_hash.reject`, each checked against this manifest's own `commitment_hash.pattern`
rather than against the vector schema directly. Read that script rather than any summary of
it, including this one, before relying on a particular value being guarded.

**This file is non-normative.** It *projects* values whose actual normative home — where
one exists — is named in that section's own `source` field. `contract.json` MUST NOT
itself be cited as a normative source anywhere in this repo's docs or RFCs; cite the named
RFC section, registry, or proto file instead. Several values pinned here have **no**
normative home at all today (their own `source` fields say so) — the manifest says so explicitly
rather than inventing a citation, and pinning the value here does not create one.

## Sections

| Section | `applies_to` | What it pins |
|---|---|---|
| `protocol` | runtime, both SDKs | The `macp_version` envelope literal (`"1.0"`) |
| `modes` | runtime, both SDKs | The 5 registry-backed standard mode ids, plus the 1 shipped extension mode id (`ext.multi_round.v1`, not registry-backed) |
| `defaults` | runtime, both SDKs | `mode_version`, `configuration_version`, `policy_version` (`policy.default`), and the policy-builder default `schema_version` |
| `error_codes` | runtime, both SDKs | The 16 `permanent` + 1 `deprecated` canonical error-code strings |
| `retry` | both SDKs | `RetryPolicy` defaults: max retries, base/max backoff, the derived backoff schedule, the retryable error-code set, and the deliberate absence of jitter |
| `projection_anomaly` | both SDKs | The `ProjectionAnomaly` field set, field order, the four anomaly-kind strings, and the snake_case→lowerCamelCase naming transform a lowerCamelCase consumer follows |
| `commitment_hash` | runtime, both SDKs | The commitment-hash format, pinned as an accept/reject behavior table (not a shared regex string, since `macp-runtime` implements this as a hand-written byte check, not a regex) |
| `contribute_payload` | runtime, both SDKs | The `Contribute` payload's proto vs. legacy-JSON byte disambiguation: decode order, first-byte facts, and generated round-trip vectors, including the `collision_*` vectors at the value byte-lengths where a canonical-proto payload also parses as JSON |
| `contribute_acceptance` | runtime only | Whether an empty `Contribute` payload is rejected — a runtime-only acceptance gate by design, not an unconfirmed value: both SDKs deliberately decode without raising instead of gating (see the section's own `source`) |
| `proposal_disposition` | runtime, both SDKs | Proposal mode's per-proposal `mode_state_dispositions` (`Live`/`Withdrawn`) and projection `projection_status_values` (`open`/`rejected`/`withdrawn`), plus `acceptance_tracking` (`per_sender`) — acceptance is a separate per-sender relation, never denormalized onto the proposal record |

Every section carries:
- `applies_to` — which of `macp-runtime` / `macp-sdk-python` / `macp-sdk-typescript` MUST
  assert this section. Adding a consumer to a section's `applies_to` is a MINOR version
  bump (see Versioning) and is expected to turn that consumer's CI red until it actually
  wires the assertion — at its next pin bump if it pins a spec revision, or on its next CI
  run if it tracks this repo's default branch instead. That is the mechanism working as
  designed.
- `source` — where the value actually comes from. Honest about the absence of a normative
  home where one doesn't exist, rather than inventing a citation.

## What this manifest does not pin, and why

The admission rule above is positive — "values that today already agree". Its consequence is the
question most often asked of this file, so state it directly: a **disagreement** between consumers
is categorically inadmissible here. There is no way to pin a divergence, and adding one would make
every other value ambiguous about whether it records agreement or aspiration. A divergence is
either resolved upstream — in an RFC, registry, or proto, which this manifest then projects — or it
is a matter this manifest has no standing over.

The less obvious half: some values would be inadmissible **even if both consumers already agreed**,
because nothing on the wire depends on them. Pinning those would turn a cross-implementation values
manifest into a library-API specification, a different document with a different review bar.
RFC-MACP-0013 Section 3 (The Hashing Projection) states the principle this file follows — the spec
constrains an SDK's internal shape where a wire-visible value depends on it: "An SDK that
holds these values in a different internal shape … MUST project into this key set when computing or
verifying the hash." The converse — that the spec constrains internal shape ONLY there — is this
file's reading of RFC-MACP-0013's silence elsewhere rather than something it states, and it is the
reading this file acts on: where nothing on the wire depends on the shape, nothing here pins it.

The out-of-scope classes, each already visible elsewhere in this repo:

1. **In-memory decoded shapes handed to a caller.** What a decoder returns to application code for
   the same bytes — a wrapper labelling the encoding, a normalised single-key object, a
   language-native map. Identical bytes in and identical bytes out; the object in between is the
   library's. Worked example in Open items below.
2. **Agent-framework and strategy behaviour.** Participant abstractions, dispatchers, voting and
   committing strategies, bootstrap helpers. `docs/sdk-parity.md`'s `MAY Implement` tier names
   these optional, and two SDKs may implement the same-named strategy over entirely different
   inputs without either being non-conformant. RFC-MACP-0007 Section 1 (Purpose) declines to
   standardize one universal voting algorithm and Section 6 (Terminal semantics) repeats that a
   deployment may choose its own, so there is no upstream here to project.
3. **Handler-context field types.** What a framework hands a handler, and how widely it types that
   value, is framework surface — the same MAY tier.
4. **Client-side validation strictness beyond the wire.** A client that requires a field the mode's
   schema leaves optional is over-strict, and `docs/sdk-parity.md` states that as a MUST-Implement
   rule. It is still not pinnable *here*: this file holds values, and "which fields a builder
   demands of its caller" is not a value.
5. **Transport-call ergonomics.** Deadline semantics, what a watch call returns, how many flags
   gate an insecure channel. The wire contract is RFC-MACP-0006's; the call signature is the
   library's.
6. **Static type width.** Two consumers can agree on every value produced at runtime and still type
   the field differently — a plain string versus a closed union. This file cannot make one
   language's type-checker enforce another's closed set; the `projection_anomaly.kind` Open item
   below is the worked example.
7. **SDK public symbol names (classes, methods, types).** Governed by `docs/sdk-parity.md`'s
   `## Naming` section, not by this manifest — every value here names a `source`, and a symbol
   name has none. Issue #134's own proposal explicitly excluded this ("not a full symbol map —
   file/class/function names are expected and fine to diverge per language"); issue #135 is the
   decision record for the naming divergences found since.

None of this says a divergence in those classes is harmless. It says the divergence is the
consumers' to resolve, and that this file will mirror the outcome rather than originate it.

## Versioning

`contract_version` is semver:

- **PATCH** — annotation or `source` text changes only; no value changes.
- **MINOR** — a new section, a new vector, a new reject example, or a new consumer named
  in a section's `applies_to`.
- **MINOR, and with a sequencing rule of its own** — a new member added to a frozen list that has
  **no in-repo gate at all**. Today that is exactly one list: `projection_anomaly.kinds`. The MAJOR
  gate below cannot apply to it, because there is no upstream to land first — the list's source *is*
  the consumers' agreement. So the rule is sequencing instead: the new member lands here only
  **after** the consumers it describes have agreed on it. This manifest follows; it does not
  originate. A member added ahead of that agreement would be this file inventing a contract, which
  the non-normative disclaimer above forbids.

  **`retry.retryable_error_codes` is NOT in this category, despite its `source` reading
  "convention".** Its members are held to this manifest's own `error_codes.permanent`, which is
  itself held to `registries/error-codes.md` — so adding a member *does* have an upstream that must
  land first, and `make parity-contract` rejects one that has not. Which codes are worth retrying
  remains a convention; which strings may appear is registry-gated. Do not read the section's
  `source` field as meaning the whole section is ungated.
- **MAJOR** — an existing frozen value changes or is removed. By construction this
  requires the upstream RFC/registry/proto change to land *first* — `check-parity-contract.py`
  holds every in-repo-sourced value to its source, so an unmatched manifest edit fails the
  checker before it can land.

No git SHA is embedded in this manifest — it would be unknowable pre-merge and would churn
on every unrelated edit. Provenance of *which spec-repo commit a consumer vendored* lives
in that consumer's own tree (a `SOURCE.md`, matching how both SDKs already document their
vendored `cmt-hash` pack).

## Open items

Deliberately **not** seeded here, tracked as follow-up work instead of silently
patched over:

- **Non-string `value` in legacy `Contribute` JSON is still unpinned, and the live defect has
  narrowed.** The canonical-proto/legacy-JSON length-collision band is now pinned by
  `contribute_payload`'s `collision_*` vectors, empty-payload gating is settled (see
  `contribute_acceptance`'s own `source`), and `macp-sdk-typescript` now applies a canonical-proto
  tie-break before reading bytes as legacy JSON — so the collision half of this question is fixed
  downstream. What remains is what a decoder does with valid legacy JSON whose `value` is not a
  string: `macp-sdk-typescript` **coerces** it, turning a numeric `value` into its string form and a
  missing or null one into `""`; `macp-sdk-python` passes the parsed object through uninterpreted;
  and `macp-runtime` declines it outright, since its legacy-JSON reader types `value` as a required
  string. No two of the three agree — so no value is seeded here until they converge. The asymmetry
  is worth naming, because it is decidable without an RFC: a decode layer may decline to interpret
  `value`, or pass it through; **altering** it is neither, and is the odd one out however the shape
  question below is settled. Tracked as issue #142.
- **The decoded shape a `Contribute` decoder hands its caller is deliberately not pinned.** For the
  same legacy-JSON bytes, `macp-sdk-python` returns the parsed object unaltered under a wrapper that
  labels the encoding, and `macp-sdk-typescript` returns a normalised single-key object. Two
  in-memory shapes, one byte sequence, nothing wire-visible between them — class 1 of the
  out-of-scope list above. Pinning a library's return type for a value with no wire consequence
  would be a first for this repo, and RFC-MACP-0013 Section 3 (The Hashing Projection) is the
  precedent for why it is not done. Recorded as **declined**, not open: this is the second half of
  issue #142, and the answer is that this manifest is the wrong instrument, not that the question
  does not matter.
- **`projection_anomaly.kind`'s static contract width differs by SDK.** Python types
  `kind` as a plain `str`; TypeScript types it as a closed 4-value union. The two SDKs
  agree on every runtime value produced today, but this manifest cannot itself make
  Python's type-checker enforce the same closed set TypeScript's does — that is each SDK's
  own follow-up, not something a values manifest can fix.
- **`field_case_rule` (in `projection_anomaly`) is new prescriptive text**, not a
  projection of an existing normative statement — there is no RFC, registry, or proto home
  for the snake_case→lowerCamelCase transform contract anywhere in this repo. It is kept
  here because it is small and genuinely useful to a lowerCamelCase consumer, worded
  descriptively rather than as an RFC-2119 requirement, and covered by this file's
  non-normative disclaimer above rather than treated as an exception to it.
- **`projection_anomaly.kinds` mirrored the decision the SDKs have now made — one site of it is
  still unresolved.** The four kind strings pinned today come from the SDKs' own agreement, not from
  this repo: "anomaly" has zero occurrences anywhere in `rfcs/` or `registries/`, and `macp-runtime`
  has no such concept. The question this bullet used to record as open — whether discarding a
  competing `TaskAccept`, or a `Handoff` message for an already-settled handoff, should also record
  an anomaly — was settled by `macp-sdk-python` PR #95 and `macp-sdk-typescript` PR #134, which
  landed `duplicate_task_accept` and `settled_handoff` with identical spelling and identical
  declaration order on both sides. They reached this manifest as the 1.2.0 MINOR bump under the
  convention-sourced-list rule in Versioning above — mirroring, as that rule requires, rather than
  originating.

  Be precise about how much that settled, because the headline number and the behavioural one
  differ. The "frozen pending cross-SDK agreement" marker stood at **six** sites, **all six in
  `macp-sdk-typescript`**, and **five** are now resolved — but only **three** of those five record
  anything: a `TaskAccept` that loses the session's one assignee slot, and a `HandoffAccept` and a
  `HandoffDecline` against an already-settled `handoff_id`. The other **two** resolved the opposite
  way, as deliberate silent no-ops: an accept or decline naming a `handoff_id` this projection never
  saw offered is not caller misuse, since a projection that joined mid-session may legitimately never
  have observed the offer. So "five of six agreed" and "five of six now record an anomaly" are
  different claims, and only the first is true.

  **The sixth site remains unresolved**: `macp-sdk-typescript`'s `DecisionProjection` guard against a
  `Vote` arriving after `Commitment`. It is a session-terminality phase regression, not a settlement
  discard. Both SDKs already agree on its *behaviour* — the phase does not regress and nothing is
  recorded — and differ only on whether that behaviour should carry a kind at all, and if so under
  what name. It is deferred rather than tracked: no open issue anywhere covers it,
  `macp-sdk-typescript` issue #128 having scoped it out deliberately and since closed.

  Two qualifications the original form of this bullet raised still stand. RFC-MACP-0009 Section 5
  (Validation rules) rule 3a and RFC-MACP-0010 Section 5 (Validation rules) rule 4 already require
  **rejecting** the duplicate-accept cases, so no wire behaviour was ever in question here — but a
  handoff already settled by *decline* is not textually covered by either rule, so for that case the
  reject requirement is a reading rather than a quote. And both new kinds arrive with **zero**
  conformance coverage in this repo: the fixture corpus still contains no accept-after-settled and no
  duplicate-`TaskAccept` case, and because a projection consumes accepted transcripts only, a fixture
  that marks such a message `expect: "reject"` would not supply that coverage either.
- **The Decision-mode `phase` window where the two SDKs disagree stays unpinned — and one half of
  that divergence is not a naming choice at all.** `expected_mode_state.phase`
  **is** a cross-SDK contract this repo owns — it is pinned in the fixture corpus and documented in
  `schemas/conformance/README.md` — but be precise about where it is *enforced*: **each SDK's
  conformance harness asserts it; this repo's own checks do not.** `schemas/conformance/schema.json`
  types `expected_mode_state` as a bare object and `lint_fixtures.py` never mentions `phase`, so a
  nonsense phase in a fixture passes `make validate` here and fails downstream. Owning the value and
  enforcing it are different things, and only the second is downstream. The corpus pins `Voting`,
  `Committed` and `Negotiating`. It does not pin the window after a
  `Proposal` and before any `Evaluation`, which is exactly where the two differ:
  `macp-sdk-typescript` enters its `Evaluation` phase on the **`Proposal`** message,
  `macp-sdk-python` on the first **`Evaluation`** message. That window stays unpinned because the
  phase *vocabulary itself* has no normative definition anywhere in this repo — pinning it would
  invent semantics for an unspecified label. Separately, and not a naming matter:
  `macp-sdk-typescript` guards its terminal `Committed` phase against later messages and
  `macp-sdk-python` does not, so a late `Vote` moves a Python projection's `phase` back out of
  `Committed`. Calling that a violation is a **reading, not a quotation**, and the chain is worth
  stating: the monotonicity invariant in RFC-MACP-0001 Section 7.2 (Session States) is about the
  *session* state, and a mode `phase` is not a session state; what carries it across is
  RFC-MACP-0002 Section 1 (Scope), "Modes MUST NOT violate MACP Core invariants". Two honest
  qualifications follow. A conformant runtime is unlikely to deliver that late `Vote` at all: the
  accepted `Commitment` resolves the session per RFC-MACP-0001 Section 7.3 (Termination), and
  Section 7.2 permits no transition out of a terminal state — though note that Core states this as a
  constraint on *transitions*, not as an explicit "reject every later message" rule, so this too is a
  reading. Either way the divergence surfaces only on history a conformant runtime would not have
  produced. And the corpus asserts `Committed` as a
  value, not as a floor: no fixture replays anything after it. So this is the half that needs
  fixing rather than deciding, but it is defense in depth, not a broken wire contract.
  Tracked as issue #145.

  **Proposal mode's `phase` field is a different case entirely, and closed rather than
  tracked.** Like Decision's, `macp-runtime`'s Proposal-mode state machine
  (`crates/macp-modes/src/mode/proposal.rs`) carries a `phase` that reaches a `Converged`
  value neither SDK's projection represents in its own `status`/`disposition` field. But
  where the window above is an *unpinned slice inside an agreed vocabulary* — both SDKs
  agree down to the message that moves `phase`, and only the boundary between two agreed
  values is undocumented — Proposal's is a **three-way disagreement on the vocabulary
  itself**: the runtime's `phase` enum has a value (`Converged`) categorically absent from
  both SDKs' `status` domains, not merely unasserted by either of them. "What this
  manifest does not pin, and why" above says a disagreement is inadmissible here, so this
  is not an unpinned window awaiting resolution the way issue #145's is — it is closed:
  `proposal_disposition.mode_state_dispositions` and `.projection_status_values`
  deliberately exclude `phase`/`Converged` entirely, and `proposal_disposition`'s own
  `source` field states this omission in the manifest itself. Tracked as issue #176.
