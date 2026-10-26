# Invalid receipt-key-set fixtures (negative schema tests)

Each file in this directory is an `examples/discovery/receipt_keys.json`-shaped JWK Set that MUST be
**rejected** by `schemas/json/macp-receipt-keys.schema.json`, the schema of what `GetReceiptKeys`
returns (RFC-MACP-0013 §13). They are regression tests for that schema's constraints: if a schema
change accidentally loosens one, `scripts/validate-json.sh` fails because one of these fixtures
starts validating.

Each fixture is a **complete** copy of the real example with exactly one mutation, the same "whole
document" dynamic as `../invalid-agent-bootstrap/`, plus a top-level `_invalid_because` annotation
naming the constraint it violates. The schema's top level and its key objects are open (RFC 7517
allows members it does not name), so the annotation is not a second rejection reason and no schema
escape is needed.

## Fixture discipline

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword from the schema
should make exactly that fixture validate and leave the others rejected. As in
`../invalid-policy-descriptors/`, two fixtures key on the same `required` keyword
(`$defs.jwk.required`), so the diagonal is keyed on one required **member**, not one keyword: a
single "drop `required`" mutation would flip both. Measured:

| mutation | key_missing_kid | key_missing_kty | missing_keys | okp_missing_x | okp_private_d | okp_wrong_crv |
|---|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject | reject |
| drop root `required` | reject | reject | **PASS** | reject | reject | reject |
| drop `kid` from `$defs.jwk.required` | **PASS** | reject | reject | reject | reject | reject |
| drop `kty` from `$defs.jwk.required` | reject | **PASS** | reject | reject | reject | reject |
| drop `$defs.jwk.properties.d` | reject | reject | reject | reject | **PASS** | reject |
| drop `$defs.jwk.then.required` | reject | reject | reject | **PASS** | reject | reject |
| drop `$defs.jwk.then.properties.crv.const` | reject | reject | reject | reject | reject | **PASS** |

`key_missing_kty` keeps the OKP members (`crv`, `x`), but the `if` requires `kty`, so the OKP
branch does not apply and the missing `kty` is the only reason.

## What the schema cannot check

RFC-MACP-0013 §13 item 8 also requires every `kid` to be unique in the set and never reused for a
different key. Uniqueness of one member across array items is not expressible in JSON Schema, so it
has no fixture here; it is a runtime obligation.
