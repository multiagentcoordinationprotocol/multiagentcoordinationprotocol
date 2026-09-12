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

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword
from the schema should make exactly that fixture validate and leave the others
rejected — a perfect diagonal:

| mutation | missing-rules | policy-id-empty |
|---|---|---|
| *intact* | reject | reject |
| drop `required` | **PASS** | reject |
| drop `policy_id.minLength` | reject | **PASS** |

`missing-rules.json` therefore keeps `policy_id`, `mode` and `schema_version`
populated: a fixture omitting several required keys at once would fail for three
reasons and isolate none of them. `policy-id-empty.json` likewise supplies all
four required keys so that only `minLength` stands between it and validity.

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
