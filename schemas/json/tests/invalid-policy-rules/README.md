# Invalid policy-rules fixtures (negative schema tests)

Each file in this directory is a Decision Mode governance `rules` object that
MUST be **rejected** by `schemas/json/policy/decision-rules.schema.json`. They
are regression tests for the rule schema's value constraints: if a schema change
accidentally loosens one, `scripts/validate-json.sh` fails because one of these
fixtures starts validating.

This directory exists because nothing else in the repository validates a `rules`
object against its mode's rule schema. `macp-policy-descriptor.schema.json` and
`schemas/conformance/schema.json` both treat `rules` as an opaque object with no
`$ref`, so the rule schemas are otherwise only *meta*-validated — checked for
being well-formed JSON Schema, never exercised against an instance. These
fixtures are the only thing that proves the constraints fire.

Each fixture carries a top-level `_invalid_because` annotation stating the
constraint it violates and the RFC section that defines it. The rule schema sets
no `additionalProperties: false` at the root, so the annotation itself never
causes the rejection.

Every fixture isolates exactly **one** constraint: removing that one keyword from
the schema makes exactly that fixture validate and leaves the other four
rejected. A fixture that fails for the wrong reason would silently stop testing
anything, so preserve that property when adding cases.

| Fixture | Violated constraint |
|---------|---------------------|
| `threshold-zero-weighted.json` | `voting.threshold` MUST be greater than 0 — `exclusiveMinimum: 0` (RFC-MACP-0012 §4.1; issue #98 item 2) |
| `supermajority-missing-threshold.json` | Under `supermajority`, `voting.threshold` is REQUIRED — the `supermajority` `allOf` arm's `required` (RFC-MACP-0012 §4.1; issue #101). Deliberately asymmetric with `majority`, which constrains the value without requiring the key |
| `threshold-below-half-majority.json` | Under `majority`, `voting.threshold` MUST be at least 0.5 — the `majority` `allOf` arm (RFC-MACP-0012 §4.1) |
| `weights-empty-map.json` | `voting.weights` MUST be non-empty — `minProperties: 1` (RFC-MACP-0012 §4.1; issue #98 item 3) |
| `weights-explicit-zero.json` | Every `voting.weights` value MUST be greater than 0 — per-weight `exclusiveMinimum: 0` (RFC-MACP-0012 §4.1; issue #98 item 3) |

`threshold-zero-weighted.json` deliberately uses `weighted` rather than
`supermajority`: `supermajority` with `threshold: 0` already fails via the
supermajority arm's `exclusiveMinimum: 0.5`, so it would pass this test for the
wrong reason and would keep passing even if `threshold.exclusiveMinimum` were
deleted.

To add a case: drop a new `.json` file here with an `_invalid_because`
annotation — `validate-json.sh` picks it up automatically and asserts it fails
`decision-rules.schema.json` validation. Fixtures for another mode's rule schema
need their own directory and loop, since the loop in
`scripts/validate-json.sh` binds one schema.
