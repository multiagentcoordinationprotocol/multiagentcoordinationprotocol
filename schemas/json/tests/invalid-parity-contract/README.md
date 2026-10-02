# Invalid parity-contract fixtures (negative schema tests)

Each file in this directory is a `schemas/parity/contract.json`-shaped document that MUST
be **rejected** by `schemas/json/macp-parity-contract.schema.json`. They are regression
tests for that schema's constraints: if a schema change accidentally loosens one,
`scripts/validate-json.sh` fails because one of these fixtures starts validating.

Each fixture is a **complete** copy of the real manifest with exactly one mutation — the
same "whole document" dynamic `../invalid-policy-descriptors/README.md` uses — plus a
top-level `_invalid_because` annotation naming the constraint it violates. The schema's
`patternProperties: {"^(_|\$comment)": {}}` escape at every object level is what keeps that
annotation from itself becoming a second rejection reason; without it, every fixture here
would report two errors (the intended one plus `additionalProperties` on the annotation
key) and fail the isolation guard for the wrong reason.

## Fixture discipline

**Each fixture MUST isolate exactly one constraint.** Removing that one constraint from the
schema should make exactly that fixture validate and leave the others rejected:

| mutation | unknown-section | missing-section-retry | error-code-lowercase | contribute-hex-odd-length | applies-to-unknown-consumer | proposal-acceptance-tracking-unknown |
|---|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject | reject |
| drop `sections.additionalProperties` | **PASS** | reject | reject | reject | reject | reject |
| drop `retry` from `sections.required` | reject | **PASS** | reject | reject | reject | reject |
| drop `error_codes.permanent.items.pattern` | reject | reject | **PASS** | reject | reject | reject |
| drop `contribute_payload.vectors.items.properties.protobuf_hex.pattern` | reject | reject | reject | **PASS** | reject | reject |
| drop `$defs.appliesTo.items.enum` | reject | reject | reject | reject | **PASS** | reject |
| drop `proposal_disposition.properties.acceptance_tracking.enum` | reject | reject | reject | reject | reject | **PASS** |

Proven by running the diagonal (see "Adding a fixture" below); the 6×6 grid above is
exactly that proof's output.

**The granularity here is one `required` MEMBER, not one keyword**, matching
`../invalid-policy-descriptors/README.md`'s rule. `missing-section-retry.json` is the only
fixture keying on `sections.required` — a future "drop a different required section"
fixture is a **distinct** mutation of a distinct constraint that happens to share the
`required` keyword, and needs its own row, not a merge into this one.

## Why its own directory, and its own loop

The assert-fail loop in `scripts/validate-json.sh` binds **one** schema per directory,
same as `../invalid-policy-descriptors/` and the five `../invalid-*-rules/` directories. A
parity-contract fixture dropped into any of those would still be "correctly rejected" — by
the wrong schema, for the wrong reason, silently and forever.

## `contract.json`'s own positive check is separate, and not shadowed

Unlike `../invalid-policy-descriptors/`'s schema — whose missing-schema guard is
**shadowed** because that schema already has an earlier positive consumer elsewhere in the
script — `macp-parity-contract.schema.json`'s only positive consumer is the dedicated
`schemas/parity/contract.json` check that runs immediately **after** this directory's
negative loop. So this loop's missing-schema guard is that schema's **first** line of
defense, same as the `invalid-*-rules/` loops' guards are for their rule schemas. See the
comment in `scripts/validate-json.sh` immediately above `INVALID_DESCRIPTOR_PAIRS` for the
full reasoning on both rows' shadowing status.

## Adding a fixture

Add the file, then confirm the diagonal still holds by deleting each constrained keyword
from a scratch copy of the schema in turn and checking that exactly one fixture flips.
`scripts/validate-json.sh` honours a `MACP_ROOT` environment variable so the proof can run
against a throwaway tree rather than the real repository.

Fixtures here are **not** vendored by the downstream SDK or runtime repositories — only
`schemas/conformance/` is — so adding one costs those repos nothing.

A fixture that fails for the wrong reason silently stops testing anything.
