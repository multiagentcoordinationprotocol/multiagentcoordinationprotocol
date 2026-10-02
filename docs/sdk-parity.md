# SDK Parity Requirements

This document defines what MACP SDKs must implement to be considered conformant, and the sync mechanisms that keep them aligned.

## MUST Implement

Every official MACP SDK MUST provide:

### Transport Layer
- **MacpClient** — gRPC client implementing all RPCs in `MACPRuntimeService` (currently 24, including `SuspendSession`/`ResumeSession`)
- **MacpStream** — bidirectional streaming wrapper for `StreamSession`
- **Authentication** — dev-agent and bearer-token modes, both bearer-only (no identity header: no
  supported runtime reads one, and `macp-runtime` carries tests asserting it rejects or ignores the
  header it once accepted)

### Session Helpers
- One session class per standards-track mode (Decision, Proposal, Task, Handoff, Quorum)
- Each session wraps start, mode-specific actions, commit, cancel, metadata

### Client-Side Validation

An SDK's own validation MUST NOT reject a payload that the mode's schema and the RFCs permit.
Strictness beyond the wire contract turns a conformant message into a local error, and makes the
same session open or fail depending on which SDK's helper built it — which is a parity defect even
though every byte that reaches the runtime is valid.

The concrete rule the spec already states: per RFC-MACP-0001 Section 7.1 (Session Creation),
`intent` MAY be empty and a runtime MUST NOT reject a `SessionStart` solely because `intent` is
empty. The same reasoning extends to the other human-readable descriptive strings — `instructions`,
`summary`, `action` — which are plain proto3 singular fields with no field presence, so an omitted
value and `""` are the same bytes on the wire. A client-side required-check on any of them invents a
distinction the wire cannot carry, and a caller has no conformant way to satisfy it other than
inventing text.

**No conformance fixture can enforce this, and it would be misleading to imply otherwise.** The
runner replays *accepted* envelopes through projections (see `## Conformance Test Suite` below),
whereas a builder that refuses to construct the envelope fails before anything reaches a projection.
Enforcement here is per-SDK review, not the corpus; it was filed as `macp-sdk-typescript` #124 and
`macp-sdk-python` #93, both since closed (`macp-sdk-typescript` PR #132 is the over-strictness half).
Enforcement staying per-SDK is the durable point — the issue numbers are history, not open work.

### Projections
- One projection class per standards-track mode
- Client-side state machines tracking transcript, phase, and commitment
- Must pass the canonical conformance fixture suite (see below)

### Policy Framework
- Policy builder functions for all 5 modes (typed rule inputs → `PolicyDescriptor`)
- Client methods: `registerPolicy`, `unregisterPolicy`, `getPolicy`, `listPolicies`

### Error Hierarchy
- `MacpSdkError` — base SDK error
- `MacpTransportError` — gRPC communication failure
- `MacpAckError` — runtime rejected the message (NACK)
- `MacpSessionError` — session-level error (wrong state)
- `MacpTimeoutError` — operation timed out
- `MacpRetryError` — all retry attempts exhausted

### Retry
- `RetryPolicy` with configurable max retries, backoff base/max, retryable error codes
- `retrySend()` / `retry_send()` with exponential backoff
- Defaults are pinned in `schemas/parity/contract.json`'s `retry` section (see "Parity-Contract Manifest Sync" below)

### Convenience Methods
- `sendSignal()` / `send_signal()` — Ambient Signal emission
- `sendProgress()` / `send_progress()` — progress tracking

### Envelope Utilities
- Envelope builder with auto-generated message IDs and timestamps
- SessionStart and Commitment payload builders with defaults
- ID generators (session, message, commitment)

## MAY Implement

Optional features that enhance the SDK but are not required for conformance.

These surfaces are optional **and not parity-governed**. Two SDKs may differ here in behaviour,
shape, naming and defaults without either being non-conformant, and the parity-contract manifest
will not pin them — see the "What this manifest does not pin, and why" section of
`schemas/parity/README.md`. That section is broader than this tier: it lists seven classes the
manifest will not pin, and three of them are not MAY-tier surfaces at all — among them the MUST
rule below and this document's own Naming section below. Unpinnable by the manifest and
optional for an SDK are different statements. Two consequences are worth stating outright,
because each has been raised as a cross-SDK question:

- **A same-named helper may compute a different quantity.** The two SDKs' `majority_voter` is the
  worked example: one reads the projection's **evaluations**, the other reads the **votes already
  cast**, under the same public name, the same threshold parameter and the same `0.5` default.
  RFC-MACP-0007 Section 1 (Purpose) declines to standardize one universal voting algorithm, and
  Section 6 (Terminal semantics) repeats that a deployment may choose its own — so there is no
  upstream for this repo to project, and naming one of the two canonical here would be inventing
  decision semantics the RFC deliberately left open.
- **Permitted is not the same as good.** Saying a divergence is not a conformance defect says
  nothing about whether it is a defect. Each SDK remains free to call its own behaviour a bug and
  fix it; what this tier settles is only that neither SDK is non-conformant for differing.

The optional features themselves:

- **Watcher classes** — convenience wrappers around streaming RPCs (vs raw iterators)
- **HTTP transport adapter** — polling transport for non-gRPC environments
- **Base session/projection classes** — shared inheritance (vs standalone classes)
- **Agent framework** — Participant abstraction, dispatcher, strategies, bootstrap
- **Logging** — structured logging helpers

## Naming

Symbol names — classes, methods, types — are outside `schemas/parity/contract.json`'s scope
(see `schemas/parity/README.md`'s "What this manifest does not pin, and why" list, item 7):
every value that manifest pins names a `source`, and a symbol name has none.
This repo still expects both official SDKs to converge on shared naming for the concepts each
SDK exposes, so the standing rule for resolving a divergence lives here instead. This is an
expectation this document states, not a conformance requirement `## MUST Implement` enforces —
it applies inside the `## MAY Implement` tier too (an SDK's own strategy/agent-framework
symbols are still expected to follow it once a divergence is found there, even though that
tier's behavior itself remains unpinned and neither SDK is non-conformant for differing on it).

**The rule**, applied when a naming divergence is found between the two SDKs (or against
`macp-runtime`, where it independently implements the same concept):

- **R0 — same shape and role, or it isn't a naming question.** A pair only qualifies as a
  naming divergence if both symbols carry the same shape and the same role in their SDK. Two
  symbols that look like a naming mismatch but actually differ in shape or capability are a
  contract gap, not a naming one — settle the gap on its own terms first; a name should not be
  chosen for a mismatch that hasn't been confirmed to be the same thing.
- **R1 — where the spec names the concept, the SDK symbol follows it.** When the wire protocol
  or an RFC already names the concept, the SDK's symbol is that name under the SDK language's
  own case convention, plus any fixed suffix the RFC's own vocabulary implies (e.g. the RFC's
  message-type vocabulary making `<MessageType>Record` the pattern its projections should
  follow). A symbol that doesn't reflect the spec's own name yields to one that does.
- **R2 — where the spec is silent, the convention shared across both SDKs wins.** If neither
  the wire protocol nor an RFC names the concept, look at what both SDKs already do elsewhere
  in their own codebase. The naming pattern followed by the majority of an SDK's *own* other
  symbols — and shared with the other SDK — is the target; a lone outlier (within its own SDK,
  or against the other SDK's shared convention) yields.

This generalizes, at the symbol level, the same principle `schemas/parity/contract.json`'s
`projection_anomaly.field_case_rule` already machine-checks at the field level — a
snake_case-to-lowerCamelCase transform with no rename, reorder, add, or drop, asserted in
`macp-sdk-typescript/tests/parity/contract.test.ts`. A symbol name has no `contract.json` entry
to hold it to, because it has no `source`, but the underlying idea — the SDK's own name follows
the spec's name under its language's convention — is the same one, not a new rule invented for
this section.

**Decision record:** issue #135 is where this repo first applied this rule, ruling on ten
naming divergences found across `macp-sdk-python` and `macp-sdk-typescript` — most settled as
renames, two split out as separate shape questions rather than decided as naming, since R0
hadn't been confirmed for either. See #135's closing comment for the full per-pair table and
the follow-up issues tracking each SDK's actual rename work.

Issue #177 applied the same rule to a single pair found later: `macp-sdk-python`'s
`ProposalRecord.proposer` (`src/macp_sdk/proposal.py:28`) vs `macp-sdk-typescript`'s
`ProposalRecord.sender` (`src/projections/proposal.ts:11`) — both set from `envelope.sender`
on `Proposal`/`CounterProposal`, confirming R0. Ruled: Python renames `proposer` → `sender`.
R1 governs — the concept both symbols name is the canonical `Envelope.sender` field each SDK
copies the value from — and R2 independently agrees: Python's own sibling records in the same
file (`ProposalAcceptRecord.sender`, `ProposalRejectRecord.sender`) already use `sender`,
making `proposer` the lone outlier against Python's own file. `macp-runtime`'s internal Rust
struct (`crates/macp-modes/src/mode/proposal.rs:56`) also uses `proposer` — recorded as a
third-voter dissent, not overridden, per the same no-public-symbol-parity-obligation reasoning
#135 applied to its own runtime dissent (item 5). See #177's closing comment and
`macp-sdk-python`'s routed follow-up issue for the rename itself.

## Shape Gaps

Not every cross-SDK divergence that looks like a naming question actually is one. R0 above
already says so: a pair only qualifies as a naming divergence if both symbols carry the same
shape and the same role; a pair that doesn't is a contract gap, to be settled on its own terms
before any naming decision applies to it.

This repo has now settled one such gap, and the underlying principle generalizes, so it is
recorded here rather than left to be re-derived the next time a shape question surfaces:

**The rule:** where an SDK's own sibling projections already carry a keyed entity's derived
lifecycle state (status, assignee, progress) directly on that entity's record — rather than in
a parallel side-table keyed by the same id — a newly diverging projection should match that
established internal convention rather than stand as a lone exception. This is an R2-style
question, not R1: the wire protocol and RFCs are silent on in-memory projection shape
(`schemas/parity/README.md` items 1 and 6 already leave it unpinned), so the deciding evidence
is the convention an SDK already follows elsewhere in its own codebase, not a single external
reference point.

A narrower, adjacent point is worth separating out rather than folding in: a field whose scope
is genuinely the *session* — a cross-entity exclusivity slot, not a property of any one entity —
belongs on the containing session/mode state, not forced onto a per-entity record it doesn't
describe, even when that record is a session-scoped singleton (at most one instance per
session). This narrower point does not extend to ordinary per-entity derived state like status
or progress, which this rule's main clause already covers.

A third, categorically different case: some derived state is not a property of the entity at
all, but a **per-sender, multi-party, supersedable relation** — each participant holds (and may
change) its own value independently of every other participant's and of the entity's own
lifecycle state. Such state belongs in a collection keyed by the relation's own subject (the
sender), never denormalized onto the entity record as a single value, even where sibling
projections in the same SDK do denormalize their own single-claimant derived state onto their
own records. RFC-MACP-0008 Section 5 (Validation rules) rule 5 — "A participant MAY change its
acceptance target by sending a later `Accept` for a different live proposal. The latest accepted
`Accept` from a participant supersedes earlier accepts from the same participant." — and Section
7 (Determinism class) — implementations "MUST derive the same live proposal set, the same
acceptance set, and the same commitment eligibility" — both describe Proposal mode acceptance
this way: a set of independently-mutable per-sender facts, not a single proposal-level status
value. Like the exclusivity-slot point above, this does not extend to ordinary per-entity derived
state such as a proposal's own `Live`/`Withdrawn` disposition, which the rule's main clause
already covers.

**Decision record:** issue #165 applied this rule to `macp-sdk-python`'s Task Mode projection.
`TaskRequestRecord`/`get_task()`/`active_tasks()` carried only the original `TaskRequest`
fields, with status/progress/assignee tracked in three separate dicts on the projection —
inconsistent with Python's own `HandoffRecord`/`ProposalRecord` (both already carry derived
state on the record, each keyed by id) and with `macp-sdk-typescript`'s combined `TaskRecord`.
Ruled: `macp-sdk-python` enriches its per-task record with the derived fields, matching its own
other projections. See #165's closing comment for the full evidence table and the routed
follow-up issue.

Issue #176 applied the third clause above to Proposal mode's acceptance tracking, settled
upstream as `macp-sdk-python` issue #112. `macp-sdk-python`'s `ProposalRecord.status`
(`src/macp_sdk/proposal.py:45`) and `macp-sdk-typescript`'s `ProposalRecord.status`
(`src/projections/proposal.ts:30`) both type the field as a 3-value
`open`/`rejected`/`withdrawn` domain with no `accepted` member; `macp-runtime`'s
`ProposalDisposition` enum (`crates/macp-modes/src/mode/proposal.rs`) agrees at `Live`/
`Withdrawn`, and all three track acceptance separately, keyed by sender. Ruled: acceptance is
tracked out-of-band per sender, never denormalized onto the proposal record, matching the
third clause's rule by design rather than as a gap to fix. `schemas/parity/contract.json`'s new
`proposal_disposition` section pins the value domain this settles; it does not originate the
decision. See `macp-sdk-python` issue #112's closing comment for the original reasoning and
this repo's issue #176 for the parity-manifest follow-up.

## Sync Mechanisms

### Proto Sync
- **Source of truth**: Buf Schema Registry at `buf.build/multiagentcoordinationprotocol/macp`
- **Local sync**: `make sync-protos` (from BSR) or `make sync-protos-local` (from sibling RFC checkout)
- **CI enforcement**: `proto-sync` job in each SDK's CI verifies no drift against BSR

### Conformance Fixture Sync
- **Source of truth**: `schemas/conformance/` in this RFC repo is the only canonical fixture location. Fixture changes land here first, then sync downstream; the runtime vendors byte-identical copies under `tests/conformance/` and its CI byte-compares them against this directory (see `schemas/conformance/README.md`).
- **Local sync**: `make sync-fixtures` in each SDK
- **CI enforcement**: `fixture-sync` job verifies fixtures match canonical source; this repo's CI validates every fixture against `schemas/conformance/schema.json` and lints internal consistency (`make conformance-lint`)

### Adding a New RPC or Mode
1. Define in RFC repo's proto files
2. Publish to BSR
3. Each SDK runs `make sync-protos` → implements the new RPC/mode → adds tests
4. If the change affects projections, add a conformance fixture and run `make sync-fixtures` downstream

### Parity-Contract Manifest Sync
- **Source of truth**: `schemas/parity/contract.json` in this RFC repo pins values that
  already agree — with matching values but no shared source of truth — across
  `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript` (error codes, retry
  defaults, mode/version constants, the commitment-hash format, `Contribute` payload byte
  vectors, `ProjectionAnomaly`'s shape, and Proposal mode's per-proposal disposition and
  acceptance-tracking domain). It is non-normative: where a value has an
  actual normative home, the manifest's `source` field names it — e.g. `policy_version`
  traces to RFC-MACP-0012 Section 5.1, and the commitment-hash format traces to
  RFC-MACP-0013 Section 7 — and the manifest MUST NOT itself be cited as that home.
- **`applies_to` semantics**: each section names which of `macp-runtime` /
  `macp-sdk-python` / `macp-sdk-typescript` MUST assert it. Adding a consumer to a
  section's `applies_to` is a MINOR manifest bump and is expected to turn that consumer's
  CI red until it wires the corresponding assertion — at its next pin bump if it pins a spec
  revision, or on its next CI run if it tracks the default branch (see the next bullet).
- **CI enforcement in this repo**: `make parity-contract` holds every in-repo-sourced
  value in the manifest to its registry/RFC/schema/corpus source, so an edit to the
  manifest that isn't backed by a matching upstream change fails before it can land. It does
  **not** cover everything: a value whose `source` declares it a convention with no in-repo home
  often has nothing to check it against, and can be given a wrong value without turning CI red
  — which is what those `source` fields are warning you about. Some are held to other values
  inside the manifest instead, among them `contribute_payload.first_byte`'s two discriminator
  bytes, asserted against the bytes every vector leads with; `macp-runtime` asserts those same
  two markers against its vendored copy, so that drift is now caught here rather than
  downstream. `retry.retryable_error_codes` is another: its members must all appear in the
  manifest's own `error_codes.permanent`, which is itself held to `registries/error-codes.md`, so
  a retryable code that is not a canonical error code fails even though the `retry` section's
  `source` still reads "convention". So is `retry.backoff_schedule_seconds`: it is recomputed
  from `retry.backoff_base_seconds`, `backoff_max_seconds`, and `max_retries`, and must match
  exactly. So are `commitment_hash.accept` and `commitment_hash.reject`: each entry is checked
  against the manifest's own `commitment_hash.pattern`, not against the vector schema directly.
  Read `scripts/check-parity-contract.py` rather than any
  summary of it before assuming a section is covered.
- **Consumer wiring, and why the three vendored copies behave differently**: all three consumers —
  `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript` — now vendor this manifest into their
  own `tests/parity/` and assert against it in CI. (`macp-sdk-python` was the last to wire it up, in
  its PR #95; the note that previously stood here, saying it did not vendor the manifest at all and
  that a change reached it only when a human carried it there, is no longer true.) What decides who
  notices a manifest change and when is how each pins this repo, and they split **two against one**:
  `macp-runtime` checks this repo out at an explicit pinned revision, so it stays green until its
  maintainers bump that revision deliberately, whereas **both SDKs** check out the default branch,
  so a merged manifest change reaches their drift checks on those repos' next CI run without anyone
  opting in. **Any** manifest change therefore needs a re-vendor issue filed against each consumer,
  and the two unpinned ones are the time-sensitive half. Note "any", not "any that adds a vector or a
  section": `verify-parity` is a byte-level diff in both SDKs, and each additionally hard-asserts the
  exact `contract_version` string as a deliberate tripwire, so even an annotation-only PATCH bump
  turns both repos red. The 1.2.0 → 1.3.0 bump (`proposal_disposition`, pinning Proposal mode's
  per-proposal disposition and acceptance-tracking domain) is the current one; the issues filed
  for the preceding 1.1.1 → 1.2.0 bump, including `macp-sdk-typescript` #135, are closed. See
  `schemas/parity/README.md` for the full section list and versioning rules.

## Conformance Test Suite

Each SDK must include a conformance test runner that:

1. Loads all `*.json` fixtures from `tests/conformance/`
2. Replays accepted messages (where `expect == "accept"`) through the matching projection
3. Verifies transcript length, commitment presence, commitment field values, and — where a fixture
   declares `expected_mode_state` — the projected `phase` and `votes`
   (`schemas/conformance/README.md` pins both, and each SDK's harness asserts both)
4. Skips `multi_round` fixtures (extension mode, no required projection)
5. Skips `reject_paths` fixtures (test runtime rejection, not projection replay)

The fixture format is documented in `schemas/conformance/README.md`.
