# Valid policy-rules fixtures (positive schema tests)

Each file here is a governance `rules` object that MUST be **accepted** by its
mode's schema in `schemas/json/policy/`. They are the mirror of the
`../invalid-*-rules/` directories, and `scripts/validate-json.sh` fails if any
one of them is rejected.

## Why this directory exists

Because "`make json-validate` is green" proved almost nothing about four of the
five rule schemas.

Every governance `rules` object on disk that anything validates **positively** —
in the conformance corpus, the examples, the discovery descriptors, and the
fenced blocks in the RFCs — is Decision Mode or the mode-agnostic `"*"`. There is
no *valid* Quorum, Proposal, Task or Handoff `rules` object anywhere in the
repository outside this directory. (The `../invalid-*-rules/` directories hold
plenty of such objects, but every one of them is asserted to **fail**.)

So a Quorum schema that rejected **everything** would have passed every check in
this repository. The negative corpora in `../invalid-*-rules/` prove those
schemas reject what they should; nothing proved they accept what they should.
That asymmetry is what made closing them (issue #114) unfalsifiable, and it is
why this directory landed before that change rather than alongside it — a corpus
invented in the same commit as the constraint it polices is not evidence.

## Three jobs per fixture

Each file does all three at once, deliberately:

1. **Positive coverage.** A realistic, maximal `rules` object exercising every
   property its schema declares.
2. **The annotation-namespace guard.** Each carries a top-level `$comment` **and a
   `_note` at every nested object level**. Issue #114 closes these schemas with
   `additionalProperties: false` plus a `patternProperties` escape reserving keys
   matching `^[_$]`, so that annotations survive. As of this directory landing that
   change has **not** been made yet — which is deliberate: this corpus goes green
   against the open schemas first, so #114's diff shows an already-green corpus
   *staying* green rather than a corpus invented alongside the constraint it
   polices.

   Annotations sit at every level, not just the root, because an escape applied
   correctly at the root and omitted at a nested level would otherwise pass this
   entire corpus. `commitment` is the level to watch: it is the one object present
   in all five schemas.

   `scripts/validate-json.sh` **enforces** this — a fixture that is schema-valid
   but missing its root `$comment`, missing a `_note` at any nested level, or not
   carrying the satisfied `designated_role` case fails the run. Without that
   assertion the whole corpus could be reduced to `{}` and stay green, which is the
   precise unfalsifiability this directory exists to end. Do not strip the
   annotations to tidy the files up; they are the test, and the run will tell you.

   **Maximality is derived from the schema, not trusted.** Checking only the levels
   a fixture happens to contain is not enough: deleting a whole level would leave
   that check with nothing to say, and a fixture trimmed to a root plus
   `commitment` would pass while covering almost nothing. So the run reads each
   schema, collects every subschema that declares its own `properties`, and
   requires the fixture to contain all of them. Two consequences worth knowing:
   adding an object-valued property to a rule schema **fails the run until the
   fixture grows to cover it**, and `voting.weights` is deliberately out of scope
   because it declares no `properties` — it uses `additionalProperties` as a value
   schema (see below).
3. **The satisfied case of the `designated_role` arm.** Every fixture sets
   `commitment.authority: "designated_role"` **with** a non-empty
   `designated_roles`. The `../invalid-*-rules/` fixtures pin the two ways that
   arm rejects; these pin the way it accepts.

## What this corpus does not cover

`voting.weights` has no positive instance here. The Decision fixture uses
`algorithm: "majority"` and omits `weights` entirely, because mixing a weighted
electorate into a majority fixture would muddy what it proves.

That property matters for issue #114 in particular, because
`decision-rules.schema.json` uses `additionalProperties` on `weights` as a **value
schema** — a different keyword usage from the object-closing one — and a blanket
close could clobber it. The coverage exists, just not here:
`schemas/conformance/decision_weighted_zero_weight.json` and its `_v1` sibling
carry real `weights` maps and run through the rules-instance loop, so that
regression would be caught there.

## Binding is by filename, never by glob

`scripts/validate-json.sh` maps `<mode>.json` → `<mode>-rules.schema.json`
through an explicit table. Two guards keep that binding honest:

- a table row whose fixture is missing is an **error**, not a skip — so a typo'd
  or renamed file fails loudly;
- a fixture on disk that no row claims is also an **error** — otherwise it would
  be validated against no schema at all, and look like coverage while providing
  none.

Adding a mode means adding the fixture **and** the row.

## No `mode` sibling — keep them bare

These are bare `rules` objects. They deliberately do not carry a sibling `mode`
key, because `scripts/extract-policy-rules.py` identifies policy instances by
looking for an object with both `rules` and a string `mode`. It does not walk
`schemas/json` today, so these are invisible to it and `EXPECTED_RULES_INSTANCES`
is unaffected — but if that walk is ever widened, bare objects cannot be
double-counted.

## Not vendored

Like the negative corpora, these fixtures are **not** vendored by the downstream
SDK or runtime repositories — only `schemas/conformance/` is — so adding one
costs those repos nothing.
