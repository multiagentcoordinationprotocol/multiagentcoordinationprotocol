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
constraint it violates and the RFC section that defines it. The rule schema closes every object level with
`additionalProperties: false` (issue #114), but reserves keys matching `^[_$]` as
an annotation namespace, so the annotation itself never causes the rejection —
and each fixture is now standing proof that the escape works.

**The mutation unit for `unknown-key.json` is the whole schema, not one keyword.**
Every other fixture here isolates a single keyword. The closure is different: it
appears once per object level, so *which* occurrence rejects a given fixture
depends on where that fixture puts its unknown key — this one is rejected by the
closure at exactly one level, but a sibling fixture placing its typo elsewhere
would be rejected by a different occurrence of the same keyword. Issue #114
frames the unit accordingly: removing `additionalProperties: false` from *one
schema* must flip exactly that schema's one unknown-key fixture. That is also why
there is exactly **one** such fixture per directory — a second would flip
alongside it under the same whole-schema mutation and break the diagonal.

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword
from the schema should make exactly that fixture validate and leave the others
rejected — a perfect diagonal:

| mutation | weighted | zero | over100 | no-roles | roles-empty | unknown-key |
|---|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject | reject |
| drop `enum` | **PASS** | reject | reject | reject | reject | reject |
| drop `exclusiveMinimum` | reject | **PASS** | reject | reject | reject | reject |
| drop percentage `maximum` | reject | reject | **PASS** | reject | reject | reject |
| drop arm's `required` | reject | reject | reject | **PASS** | reject | reject |
| drop arm's `minItems` | reject | reject | reject | reject | **PASS** | reject |
| drop every `additionalProperties: false` | reject | reject | reject | reject | reject | **PASS** |

The `drop every additionalProperties: false` row is the whole-schema mutation
unit described above, not a single keyword — that is why it reads differently
from the rows before it.

Two rows above it concern the two **different** `allOf` blocks in this schema,
which sit at different depths and are easy to confuse. `drop percentage maximum`
targets the `allOf` nested **inside `threshold`**, which carries the percentage
ceiling. `drop arm's required` and `drop arm's minItems` target the
**root-level** `allOf` added by issue #116. Putting that commitment arm inside
`threshold` would have scoped it there, where it would have compiled clean,
validated clean, and silently never fired.

(Rows are named rather than referred to by position on purpose: an earlier
version of this file said "the last row" in two adjacent paragraphs meaning two
different rows, and adding a row silently falsified one of them.)

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
