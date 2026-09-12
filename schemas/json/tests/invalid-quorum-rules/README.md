# Invalid quorum-rules fixtures (negative schema tests)

Each file in this directory is a Quorum Mode governance `rules` object that MUST
be **rejected** by `schemas/json/policy/quorum-rules.schema.json`. They are
regression tests for that schema's value constraints: if a schema change
accidentally loosens one, `scripts/validate-json.sh` fails because one of these
fixtures starts validating.

This is the sibling of `../invalid-policy-rules/`, which covers Decision Mode.
The split is structural, not stylistic: the assert-fail loop in
`scripts/validate-json.sh` binds **one** rule schema per directory, so fixtures
for another mode need their own directory and their own loop. Dropping a quorum
fixture into the Decision directory would validate it against
`decision-rules.schema.json` and "correctly reject" it for entirely the wrong
reason — silently, and forever.

## Why this directory exists at all

Until it did, **nothing had ever exercised `quorum-rules.schema.json` against a
single instance.** There is no quorum `rules` object anywhere in the repository —
no conformance fixture, no example, no discovery descriptor — and
`scripts/validate-json-schema.sh` only `ajv compile`s the rule schemas, which
proves they are well-formed JSON Schema and nothing more. Every constraint in
the file was decorative (issue #100). `threshold-percentage-over-100.json` is
the first thing that has ever proved the `percentage` arm fires.

## Fixture discipline

Each fixture carries a top-level `_invalid_because` annotation naming the
constraint it violates and the RFC section that defines it. The rule schema sets
no `additionalProperties: false` at the root, so the annotation never causes the
rejection.

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword
from the schema should make exactly that fixture validate and leave the others
rejected — a perfect diagonal:

| mutation | weighted | zero | over100 | no-roles | roles-empty |
|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject |
| drop `enum` | **PASS** | reject | reject | reject | reject |
| drop `exclusiveMinimum` | reject | **PASS** | reject | reject | reject |
| drop percentage `maximum` | reject | reject | **PASS** | reject | reject |
| drop arm's `required` | reject | reject | reject | **PASS** | reject |
| drop arm's `minItems` | reject | reject | reject | reject | **PASS** |

Note the last row targets the **root-level** `allOf` added by issue #116, not the
`allOf` nested inside `threshold`. They are different keywords at different
depths: the nested one carries the `percentage` ceiling, and putting the
commitment arm there would have scoped it to `threshold`, where it would have
silently never fired.

A fixture that fails for the wrong reason silently stops testing anything.

Note the consequence for the enum: there can be only **one** enum fixture here.
`threshold-type-weighted.json` pins both the removal of `weighted` (issue #102)
and the refusal of the `count` alias (issue #98 item 4), because a second enum
fixture would also start validating when the `enum` keyword is dropped, breaking
the diagonal.

## Adding a fixture

Add the file, then confirm the diagonal still holds by deleting each constrained
keyword from a scratch copy of the schema in turn and checking that exactly one
fixture flips. Fixtures here are **not** vendored by the downstream SDK or
runtime repositories — only `schemas/conformance/` is — so adding one costs
those repos nothing.
