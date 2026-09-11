# Conformance Fixtures

Canonical test fixtures for validating MACP SDK projections and runtime session handling.

## Purpose

These JSON fixtures define message sequences for each coordination mode. They are consumed by:

- **Runtime** — validates session state machine transitions and commitment logic
- **SDKs** — validates projection state tracking (transcript, phase, commitment fields)

## Single canonical source

This directory is the **only** canonical fixture location. `macp-runtime`
vendors byte-identical copies under `tests/conformance/` for hermetic local
runs, and its CI oracle job (a) byte-compares the vendored copies against this
directory and (b) re-runs its conformance suite directly against these files —
so the spec and the runtime cannot drift silently. Fixture changes land HERE
first, then sync downstream.

`schema.json` is the JSON Schema (draft 2020-12) for the fixture format —
payload-type names are fully-qualified proto names
(`macp.modes.decision.v1.ProposalPayload`, `macp.v1.CommitmentPayload`).
Every fixture in this directory is validated against `schema.json` in CI
(`scripts/validate-json.sh`). Keys starting with `_` (e.g. `_comment`) are
non-normative annotations allowed at the fixture and message level; harnesses
MUST ignore them.
Reject messages should carry `expected_error_code` (asserted by the runtime
harness). `lint_fixtures.py` checks internal consistency; note that initiator
participant-list membership is mode-specific (only handoff's delegated model
requires it — RFC-0010 §2; quorum's coordinator is explicitly OUTSIDE the
voter pool per RFC-0011 §2).

## Fixture Format

Each fixture is a JSON object with:

```json
{
  "mode": "macp.mode.decision.v1",
  "initiator": "agent://lead",
  "participants": ["agent://lead", "agent://peer"],
  "mode_version": "1.0.0",
  "configuration_version": "config.default",
  "policy_version": "",
  "messages": [
    {
      "sender": "agent://lead",
      "message_type": "Proposal",
      "payload_type": "macp.modes.decision.v1.ProposalPayload",
      "payload": { "proposal_id": "p-1", "option": "deploy", "rationale": "ready" },
      "expect": "accept"
    }
  ],
  "expected_final_state": "Resolved"
}
```

### Fields

| Field | Used By | Description |
|-------|---------|-------------|
| `mode` | Both | Mode identifier |
| `initiator` | Both | Session initiator. Membership in `participants` is **mode-specific** — required only by handoff's delegated model (RFC-MACP-0010 §2). Elsewhere the initiator's authority is role-based, so an initiator outside `participants` is legitimate if it sends only `SessionStart` / `Commitment` / `SessionCancel` (plus each mode's initiator-role message). See the note above the format section. |
| `participants` | Both | Declared participant roster. Must include every `accept` sender other than the initiator's role-based messages. **MAY be empty** — MACP does not require `SessionStart` to declare participants, and `decision_zero_participants.json` pins what that implies. |
| `messages` | Both | Ordered message sequence |
| `messages[].sender` | Both | Sender identity. For `accept` messages must be a participant; `reject` messages may come from outsiders. |
| `messages[].expect` | Both | `"accept"` or `"reject"` — whether the runtime accepts the message |
| `messages[].payload_type` | Both | **Fully-qualified** protobuf message name — `macp.v1.<Name>` for core payloads, `macp.modes.<mode>.v<N>.<Name>Payload` for mode payloads. Enforced by `schema.json`'s `payload_type` pattern, which **rejects** the short `decision.Proposal` form this table previously documented. |
| `policy` | Runtime | Optional inline `PolicyDescriptor` (`policy_id`, `mode`, `schema_version`, `rules`) the harness registers before `SessionStart`, so a bound (non-`none`) voting algorithm is reachable. `policy_version` must match its `policy_id`. Absent ⇒ default policy. |
| `messages[].expected_error_code` | Runtime | For `reject` messages, the error code the runtime should return (recommended) |
| `expected_final_state` | Both | Terminal state: `Open`, `Resolved`, `Suspended`, or `Cancelled`. `Resolved` ⇒ a commitment was emitted. |
| `expected_resolution` | Both | Commitment field assertions (`action`, `mode_version`, `configuration_version`, `outcome_positive`) when `Resolved` |
| `expected_mode_state` | Both | Mode-specific assertions: `phase`, `votes` (per proposal/sender), proposal/offer dispositions |

Notes:
- SDKs replay only `accept` messages through their projections (reject-path
  fixtures replay their accepted *prefix*).
- `vote` values are normalized to **uppercase** (`APPROVE` / `REJECT` /
  `ABSTAIN`); fixtures must use the uppercase form.
- Proto `bytes` payload fields (e.g. `context`) are written as plain strings and
  UTF-8 encoded by the harnesses.
- Every ballot/vote-bearing mode fixtures an *accepted* first ballot followed
  by a *rejected* duplicate from the same sender for the same
  `proposal_id`/`request_id` (`decision_reject_paths.json`,
  `quorum_reject_paths.json` — the latter includes a cross-type case, since
  the per-`request_id` cap in RFC-MACP-0011 §5 rule 3 is counted across
  `Approve`/`Reject`/`Abstain` combined). `ObjectionPayload`
  (`decision_happy_path.json`, `decision_reject_paths.json`),
  `WithdrawPayload` (`proposal_reject_paths.json`), and `TaskUpdatePayload`
  (`task_reject_paths.json`) each have at least one accepted and one
  RFC-cited rejected instance.
- **Governance policy `schema_version` semantics** are pinned in matched pairs,
  because the versions differ only in one direction and no single fixture pins
  a divergence. `decision_empty_tally_binding.json` (v3) and
  `decision_empty_tally_legacy.json` (v2) run the same `unanimous` transcript
  on an empty tally: v3 denies the positive commitment, v2 seals it under the
  preserved fail-open arm (RFC-MACP-0012 §4.1, §8). `decision_weighted_zero_weight.json`
  (v3) and `decision_weighted_zero_weight_v1.json` (v1) do the same for a
  ballot set cast entirely by weight-`0` participants, and additionally pin
  that the **vote-authorized** negative direction is denied at **every** schema
  version — the assertion that distinguishes `NoVotes` from `Failed`. (Neither
  fixture's policy sets `finalize_decline`, so the objection-authorized channel
  described below is not in play in either of them.)
  `decision_majority_empty_tally.json` and
  `decision_supermajority_empty_tally.json` cover the two ratio algorithms that
  carry the explicit "MUST NOT compute `0/0`" prohibition (`weighted`, the
  third ratio algorithm, is worded differently and covered separately above); the former also
  pins that the threshold comparison is **inclusive** (an even split approves at
  `0.5`), and the latter pins the `Failed` vs `NoVotes` distinction from the
  opposite side — a genuine `Failed` result authorizes a vote-authorized negative
  commitment, where `NoVotes` denies it.  `decision_plurality.json` pins `plurality`'s empty
  tally, its tie-fails rule, and its passing case — note it DENIES the same 1-1
  tally `decision_majority_empty_tally.json` approves.
  `decision_none_v3_empty_tally.json` is the regression guard for the `none`
  exemption at `schema_version` 3: before it, the corpus's only `none` fixture
  declared `schema_version` 2, so a runtime that swallowed `none` into the
  fail-closed arm passed every fixture here.
  `decision_legacy_require_vote_quorum.json` pins the other half of the legacy
  arm — with `commitment.require_vote_quorum` `true`, a `schema_version` 2 policy
  denies the empty tally, which is the remedy RFC-MACP-0012 §4.1 prescribes for
  pre-v3 policies.
  `decision_finalize_decline_empty_tally.json` pins the objection-authorized
  decline channel: under `schema_version` 3 with a non-`none` algorithm, an
  empty tally, and a standing critical objection, `finalize_decline` still
  seals the session negatively — the empty-tally rule gates vote-authorized
  commitments only (RFC-MACP-0007 §6.2; RFC-MACP-0012 §4.1). `decision_zero_participants.json` pins the
  authorization guard that keeps RFC-MACP-0012 §4.1's zero-participant
  `unanimous` clause unreachable at the wire: a zero-participant session
  accepts no `Proposal`, not even from the initiator.

## Source of truth & enforcement

This directory is the **single source of truth**. The hierarchy is:
**RFC prose ▸ runtime behavior ▸ these fixtures ▸ SDK copies.** When a fixture
disagrees with the RFC or the runtime, the fixture is wrong — fix it here.

Enforcement (all wired into CI, runs on every PR):

- **This repo** lints the fixtures for internal consistency:
  `python3 schemas/conformance/lint_fixtures.py` (every `accept` sender must be a
  participant, except the initiator's role-based messages; inline-policy
  `schema_version` in {1, 2, 3}; `policy_version` matching `policy_id`;
  schema/expect/final-state validity).
- **Each SDK** runs `make verify-fixtures`, which fails the build if its vendored
  copy differs byte-for-byte from this canonical set, plus deepened conformance
  harnesses that assert transcript, commitment/resolution (incl.
  `outcome_positive`), `phase`, and `votes`.

## Syncing Fixtures

Downstream repos sync via Makefile:

```bash
make sync-fixtures     # Copy canonical fixtures into tests/conformance/
make verify-fixtures   # Fail if the local copy has drifted (CI gate)
```

## `cmt-hash/` — commitment-hash test vectors (RFC-MACP-0013)

`cmt-hash/` holds a different kind of fixture than the rest of this directory:
canonical **commitment-hash vectors** for RFC-MACP-0013 Section 4 (the
canonical commitment hash algorithm), not session transcripts. Each vector
pins the projected `CommitmentPayload`, the JCS-canonicalized bytes, the
domain-separated preimage, and the resulting hash, so a diverging
implementation can identify exactly which step it diverged at. This is a
different shape from `schema.json`'s session-transcript format, deliberately
outside `schema.json`'s closed shape. `cmt-hash/vector-schema.json` documents
that shape, including RFC-MACP-0013 Section 5's frozen nine-field constraint,
but nothing invokes it directly (no ajv or other validator runs against it);
the shape it documents is instead enforced in code by
`scripts/check-cmt-hash-vectors.py`, which asserts each vector's `payload`
keys are a subset of exactly those nine fields (and, when present,
`supersedes`'s keys are a subset of exactly `session_id` and
`commitment_hash`), failing loudly on any unrecognized field.

Both `scripts/validate-json.sh` (via `"${CONFORMANCE_DIR}"/*.json`) and
`lint_fixtures.py` (via `fixtures_dir.glob("*.json")`) glob this directory
**non-recursively**, so `cmt-hash/` is invisible to both by design — it is not
an oversight. Coverage instead comes from `make cmt-hash-vectors` (wired into
`make validate` and CI), which runs `scripts/check-cmt-hash-vectors.py`
against every file in `cmt-hash/`.

Vectors are **generated** by `scripts/gen-cmt-hash-vectors.py` and must never
be hand-edited; regenerate and re-run `make cmt-hash-vectors` instead.

There are five vector files (`cmt_hash_001_minimal.json` through
`cmt_hash_005_escapes.json`). Casual references to "six cases" mean those five
files plus one machine-checked inequality assertion: `cmt_hash_004` (empty
`supersedes`) MUST hash differently from `cmt_hash_003` (no `supersedes` at
all) — asserted by `check-cmt-hash-vectors.py`, not a sixth file.

## Adding or Changing Fixtures

1. Edit the JSON here in the spec repo (this is the only place fixtures are authored).
2. `python3 schemas/conformance/lint_fixtures.py` — must pass.
3. `make sync-fixtures` in **both** SDKs; review `git diff tests/conformance/`.
4. Conformance tests must pass in **both SDKs and the runtime** before the change is done.
