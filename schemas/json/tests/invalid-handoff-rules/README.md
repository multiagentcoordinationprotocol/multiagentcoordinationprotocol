# Invalid handoff-rules fixtures (negative schema tests)

Each file here is a Handoff Mode governance `rules` object that MUST be **rejected**
by `schemas/json/policy/handoff-rules.schema.json`. They are regression tests: if a
schema change loosens one of those constraints, `scripts/validate-json.sh` fails
because a fixture starts validating.

Each loop in `validate-json.sh` binds exactly ONE rule schema, which is why every
mode needs its own directory — a fixture in the wrong one would be "correctly
rejected" by the wrong schema, silently and forever.

## Honest scope

`handoff-rules.schema.json` carries enum, type and `minimum` constraints, and — since
issue #116 — one conditional arm with real semantic content: `commitment.authority:
"designated_role"` now requires a non-empty `commitment.designated_roles`. That arm is
the first constraint here that encodes a rule about the policy rather than a rule about
a field's shape. Everything else is still off-enum values and wrong types. Since issue #114 every
object level is closed with `additionalProperties: false`, with `^[_$]` reserved as an
annotation namespace so `_invalid_because` survives — which makes the unknown-key case
testable here for the first time. There is still no top-level `required`, so an empty
`rules` object continues to validate.

They exist anyway because the alternative was **zero**: before this directory,
nothing in the repository had ever validated a Handoff Mode `rules` object against
its schema, so every constraint in it was decorative (issue #100). Tightening this
schema so a richer negative corpus is possible is tracked as follow-up work.

## Discipline

Each fixture carries `_invalid_because` naming the one constraint it violates and
the RFC section defining it. **One constraint per fixture:** removing that keyword
from the schema must make exactly that fixture validate and leave the others
rejected. A fixture that fails for the wrong reason silently stops testing anything.

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

The two `designated-role*` fixtures split the conditional arm's two keywords, and
they are genuinely separable — proved, not assumed:

| mutation | without-roles | roles-empty |
|---|---|---|
| *intact* | reject | reject |
| drop arm's `required` | **PASS** | reject |
| drop arm's `minItems` | reject | **PASS** |

`designated-role-without-roles.json` omits the key entirely; `designated-roles-empty.json`
supplies `[]`, so the arm's `required` is satisfied and only `minItems` can fire.
Both proofs were run across all five rule directories at once, not just this one —
the arm is shared vocabulary, so a mutation in one schema must not move a fixture
in another.

These fixtures are **not** vendored by the downstream SDK or runtime repositories —
only `schemas/conformance/` is — so adding one costs those repos nothing.
