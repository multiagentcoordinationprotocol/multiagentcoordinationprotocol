# Invalid proposal-rules fixtures (negative schema tests)

Each file here is a Proposal Mode governance `rules` object that MUST be **rejected**
by `schemas/json/policy/proposal-rules.schema.json`. They are regression tests: if a
schema change loosens one of those constraints, `scripts/validate-json.sh` fails
because a fixture starts validating.

Each loop in `validate-json.sh` binds exactly ONE rule schema, which is why every
mode needs its own directory — a fixture in the wrong one would be "correctly
rejected" by the wrong schema, silently and forever.

## Honest scope

`proposal-rules.schema.json` carries only enum, type, and `minimum` constraints — no
`additionalProperties: false`, no top-level `required`. An empty `rules` object
validates against it. So these fixtures can only exercise off-enum values and wrong
types, and that is genuinely thin coverage.

They exist anyway because the alternative was **zero**: before this directory,
nothing in the repository had ever validated a Proposal Mode `rules` object against
its schema, so every constraint in it was decorative (issue #100). Tightening this
schema so a richer negative corpus is possible is tracked as follow-up work.

## Discipline

Each fixture carries `_invalid_because` naming the one constraint it violates and
the RFC section defining it. **One constraint per fixture:** removing that keyword
from the schema must make exactly that fixture validate and leave the others
rejected. A fixture that fails for the wrong reason silently stops testing anything.

These fixtures are **not** vendored by the downstream SDK or runtime repositories —
only `schemas/conformance/` is — so adding one costs those repos nothing.
