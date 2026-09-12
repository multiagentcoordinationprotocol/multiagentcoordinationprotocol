# Invalid policy-descriptor fixtures (negative schema tests)

Each file in this directory is a PolicyDescriptor document that MUST be
**rejected** by `schemas/json/macp-policy-descriptor.schema.json`. They are
regression tests for that schema's document-level constraints: if a schema
change accidentally loosens one, `scripts/validate-json.sh` fails because one of
these fixtures starts validating.

## Why this directory exists at all

Until it did, **nothing had ever exercised `macp-policy-descriptor.schema.json`
against a rejected instance.** Every descriptor on disk is a positive example,
so the schema's `required` list and `policy_id`'s `minLength` had never been
proved to fire — deleting either keyword would have left the whole repository
green. This is the descriptor-level counterpart of the gap issue #100 found at
the `rules` level.

## Why its own directory, and its own loop

The assert-fail loop in `scripts/validate-json.sh` binds **one** schema per
directory. The sibling directories `../invalid-policy-rules/`,
`../invalid-quorum-rules/`, `../invalid-proposal-rules/`,
`../invalid-task-rules/` and `../invalid-handoff-rules/` each bind a
`schemas/json/policy/*-rules.schema.json`, and `../invalid/` binds
`macp-envelope.schema.json`.

A descriptor dropped into any of those would still be "correctly rejected" — by
the wrong schema, for the wrong reason, silently and forever. That is the same
failure mode `../invalid-quorum-rules/README.md` documents, and it is why the
descriptor family gets a second table in the script rather than a sixth row in
the rules table: these schemas live in `schemas/json/` rather than
`schemas/json/policy/`, and they bind a whole document rather than a `rules`
object.

## Fixture discipline

Each fixture carries a top-level `_invalid_because` annotation naming the
constraint it violates. The descriptor schema sets no `additionalProperties`
at the root, so the annotation never causes the rejection.

**Each fixture MUST isolate exactly one constraint.** Removing that one
constraint from the schema — see the granularity note below for what counts as
one — should make exactly that fixture validate and leave the others rejected:

| mutation | missing-description | missing-rules | policy-id-empty | schema-version-out-of-range |
|---|---|---|---|---|
| *intact* | reject | reject | reject | reject |
| drop `required."rules"` | reject | **PASS** | reject | reject |
| drop `required."description"` | **PASS** | reject | reject | reject |
| drop `policy_id.minLength` | reject | reject | **PASS** | reject |
| drop `schema_version.enum` | reject | reject | reject | **PASS** |

**The granularity here is one `required` MEMBER, not one keyword.** Two fixtures
now key on `required`, so a single "drop `required`" row would flip both and read
as a violation of the one-constraint rule when nothing is wrong. `remove "rules"
from required` and `remove "description" from required` are two distinct
mutations of two distinct constraints that happen to share a keyword. Do not
"simplify" the two rows back into one.

`missing-rules.json` therefore keeps `policy_id`, `mode`, `schema_version` and
`description` populated: a fixture omitting several required keys at once would
fail for several reasons and isolate none of them. `policy-id-empty.json`
likewise supplies all five required keys so that only `minLength` stands between
it and validity, `schema-version-out-of-range.json` supplies all five with a
non-empty `policy_id` so that only the `enum` does, and
`missing-description.json` supplies the other four with a non-empty `policy_id`
and an in-range `schema_version` so that only the missing `description` does.

`missing-description.json` is the fixture for issue #120, and adding it is what
forced the other three to grow a `description` key in the same commit. RFC-MACP-0012
§3 and `docs/policy.md` had always listed five required descriptor fields; the
schema required four. Making the schema agree gave every pre-existing fixture a
**second** reason to fail — all three, not some — and `make json-validate` would
have stayed green throughout, because a fixture that fails twice is still
rejected. The whole directory's coverage would have quietly become decorative:
no mutation would have flipped any fixture. That is the concrete form of the
warning below, and it is worth re-reading before adding any constraint to
`required`.

`schema-version-out-of-range.json` is the fixture for issue #115. Until that
issue was fixed the schema said only `minimum: 1`, so a descriptor declaring
`schema_version: 99` validated clean — the legal set was documented in six
places and enforced in none of them. The enum is now also the seventh site
checked by `scripts/check-prose.py`, so the schema and the prose cannot drift
apart again.

A fixture that fails for the wrong reason silently stops testing anything.

## Adding a fixture

Add the file, then confirm the diagonal still holds by deleting each constrained
keyword from a scratch copy of the schema in turn and checking that exactly one
fixture flips. `scripts/validate-json.sh` honours a `MACP_ROOT` environment
variable so the proof can run against a throwaway tree rather than the real
repository.

Fixtures here are **not** vendored by the downstream SDK or runtime
repositories — only `schemas/conformance/` is — so adding one costs those repos
nothing.
