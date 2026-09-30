# Invalid agent-bootstrap fixtures (negative schema tests)

Each file in this directory is an `examples/discovery/agent_bootstrap.json`-shaped document that
MUST be **rejected** by `schemas/json/macp-agent-bootstrap.schema.json`. They are regression tests
for that schema's constraints: if a schema change accidentally loosens one,
`scripts/validate-json.sh` fails because one of these fixtures starts validating.

Each fixture is a **complete** copy of the real example with exactly one mutation — the same
"whole document" dynamic `../invalid-policy-descriptors/README.md` and
`../invalid-parity-contract/README.md` use — plus a top-level `_invalid_because` annotation naming
the constraint it violates. The example's own `$comment` is kept, as in every sibling corpus, so
"complete copy plus one mutation" is literally true.

**Why the annotation needs no schema escape here, unlike `../invalid-parity-contract/`.** That
directory's README warns that its fixtures rely on a `patternProperties: {"^(_|\$comment)": {}}`
escape at every object level, without which the annotation becomes a second rejection reason and
the isolation guard fails for the wrong reason. This schema is different: its **top level** is
`additionalProperties: true`, so an unknown key there is not a rejection reason and no schema change
is needed.

**Put the annotation at the top level only.** Most of this schema's nested objects are closed, and
putting it inside any of them makes the fixture report two errors. Measured, the objects that are
`additionalProperties: false` are `initiator`, `initiator.session_start`,
`initiator.session_start.roots[]`, `initiator.kickoff` and `cancel_callback`; the ones that are `true`
are the top level, `auth`, and `metadata`. Note that `initiator` **itself** is closed, so "anywhere
under `initiator`" is off limits, not merely `session_start`.

## Fixture discipline

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword from the schema
should make exactly that fixture validate and leave the others rejected. Re-measured against the
flat, snake_case schema (issue #155) — grown to a 7×7 grid with two new fixtures (`anyOf` and
`minLength`, two *distinct* keywords, per the correction below). Paths below are under
`properties.initiator.properties.session_start` except the last two rows, which are top-level:

| mutation | ext-value-not-string | dead-context-field | ext-not-object | max-suspend-ms-negative | max-suspend-ms-fractional | missing-runtime-url-and-address | runtime-url-empty |
|---|---|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject | reject | reject |
| drop `properties.extensions.additionalProperties.type` | **PASS** | reject | reject | reject | reject | reject | reject |
| drop `additionalProperties` | reject | **PASS** | reject | reject | reject | reject | reject |
| drop `properties.extensions.type` | reject | reject | **PASS** | reject | reject | reject | reject |
| drop `properties.max_suspend_ms.minimum` | reject | reject | reject | **PASS** | reject | reject | reject |
| drop `properties.max_suspend_ms.type` | reject | reject | reject | reject | **PASS** | reject | reject |
| drop top-level `anyOf` | reject | reject | reject | reject | reject | **PASS** | reject |
| drop `properties.runtime_url.minLength` | reject | reject | reject | reject | reject | reject | **PASS** |

That 7×7 grid is the measured output of running the diagonal, not an intention. Each of the first
five and the seventh fixture was additionally confirmed to produce exactly **one** `ajv
--all-errors` error at the `schemaPath` its row names — which matters, see the next paragraph. The
sixth fixture (`missing_runtime_url_and_address.json`) produces three raw `ajv --all-errors` entries
(`#/anyOf/0/required`, `#/anyOf/1/required`, `#/anyOf`) — all three collapse to the same group under
`assert_fixture_isolated`'s own branch-collapsing rule (`oneOf`/`anyOf` branches fold to their
wrapper's `schemaPath`), so the harness still counts it as isolated to one reason. This is expected
for any fixture keying on an `anyOf`, not a defect: a document failing every branch of an `anyOf`
always reports one error per branch plus the wrapper.

**The container type and the value type are two constraints, not one.** `extensions` carries
`type: "object"` and its `additionalProperties` subschema carries `type: "string"`; an array passes
the second vacuously and a numeric value passes the first. Likewise `max_suspend_ms` carries both
`type: "integer"` and `minimum: 0`, and `1.5` and `-1` fail different ones. Four keywords, four
fixtures. The fifth fixture keys on `session_start`'s `additionalProperties: false`, which is what
keeps the removed `bytes context` field (RFC-MACP-0001 Section 7.4.2 records its removal, superseded
by `context_id` and `extensions`) from being re-added silently. The sixth keys on the top-level
`anyOf` added by issue #155 requiring at least one of `runtime_url`/`runtime_address` present — both
real SDK readers throw at bootstrap time if neither key is present.

**Presence and non-emptiness are two constraints too — a correction from an earlier draft of this
paragraph.** That draft claimed the present-but-empty case (`runtime_url: ""`) "has no dedicated
fixture yet, since it's the same `anyOf` keyword" the sixth fixture isolates. Measured, that's wrong:
JSON Schema's `required` checks key *presence*, not truthiness, so `runtime_url: ""` satisfies the
`anyOf` outright (the key is there) and is rejected — if at all — by `runtime_url`'s own
`minLength: 1` instead, a keyword the `anyOf` fixture's diagonal row never touches. The seventh
fixture, `runtime_url_empty.json`, isolates exactly that: `runtime_url` present but empty,
`runtime_address` absent, so the `anyOf` passes and only `minLength` fires. This is the same
"container vs. value" discipline as the `extensions`/`max_suspend_ms` pairs above, just one keyword
apart instead of two — presence and non-emptiness are different failure modes of the same field, and
each earns its own fixture here for the same reason the four `extensions`/`max_suspend_ms` keywords
each did.

**A known limit of the harness, worth stating because a fixture here is newly exposed to it.**
`assert_fixture_isolated` in `scripts/validate-json.sh` counts *distinct rejection reasons*; it does
not pin which one. So deleting the whole `extensions` property would leave
`extensions_value_not_string.json` rejected — by `session_start`'s `additionalProperties`, with
exactly one error — and the guard would still say "isolated". That is why the grid above records the
`schemaPath` expectation in prose: re-run the diagonal rather than trusting a green run when you
change this schema's shape.

## Why its own directory, and its own loop

The assert-fail loop in `scripts/validate-json.sh` binds **one** schema per directory, same as
`../invalid-policy-descriptors/`, `../invalid-parity-contract/` and the five `../invalid-*-rules/`
directories. A bootstrap fixture dropped into any of those would still be "correctly rejected" — by
the wrong schema, for the wrong reason, silently and forever.

## This schema's missing-schema guard IS shadowed

Like `../invalid-policy-descriptors/`'s and unlike `../invalid-parity-contract/`'s:
`macp-agent-bootstrap.schema.json` already has a positive consumer **earlier** in
`scripts/validate-json.sh` — the `agent_bootstrap:` row of `EXTRA_DISCOVERY_PAIRS`, which validates
`examples/discovery/agent_bootstrap.json` — so a deleted or corrupt schema fails there first and
never reaches this loop. The guard is kept as defense in depth for a checkout that lacks those
examples, where that positive block silently no-ops on its `-f` test and this guard becomes the only
thing between a missing schema and a run of cheerful "Correctly rejected" lines. See the comment in
`scripts/validate-json.sh` immediately above `INVALID_DESCRIPTOR_PAIRS` for all three rows'
shadowing status.

## RFC citations in this schema are NOT machine-checked

`check_xrefs` in `scripts/check-prose.py` walks `.md` files only, so the `RFC-MACP-0001 Section 10.3`
and `RFC-MACP-0004 Section 2` references inside this schema's `description` strings resolve by
review, not by CI. Cite the section **name** alongside the number in any new description here, and
re-read the cited section rather than assuming the number still points at it. Widening `check_xrefs`
to `schemas/**/*.json` is tracked as a follow-up.

## Adding a fixture

Add the file, then confirm the diagonal still holds by deleting each constrained keyword from a
scratch copy of the schema in turn and checking that exactly one fixture flips.
`scripts/validate-json.sh` honours a `MACP_ROOT` environment variable so the proof can run against
a throwaway tree rather than the real repository.

Fixtures here are **not** vendored by the downstream SDK or runtime repositories — only
`schemas/conformance/` is — so adding one costs those repos nothing.

A fixture that fails for the wrong reason silently stops testing anything.
