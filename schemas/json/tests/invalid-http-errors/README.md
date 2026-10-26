# Invalid HTTP error-body fixtures (negative schema tests)

Each file in this directory is an HTTP-binding error body (RFC-MACP-0006 §4.5) that MUST be
**rejected** by `schemas/json/macp-http-error.schema.json`. They are regression tests for that
schema's constraints: if a schema change accidentally loosens one, `scripts/validate-json.sh` fails
because one of these fixtures starts validating.

Each fixture is a complete copy of a valid body
(`{"error": {"code": "SESSION_NOT_FOUND", ...}}`) with exactly one mutation, plus a top-level
`_invalid_because` annotation naming the constraint it violates. The schema's top level and its
`error` object are open (receivers ignore unrecognized members, RFC-MACP-0001 §10.6), so the
annotation is not a second rejection reason. The one exception is `body_not_object.json`: it is a
JSON array, which has no place for the annotation, so its reason is the array's only element.

Mutated values are non-null on purpose. A JSON `null` decodes as the field's default
(RFC-MACP-0001 §10.10), so `"message": null` is not a wire error, even though this schema would
reject it.

## Fixture discipline

**Each fixture MUST isolate exactly one constraint.** Removing that one keyword from the schema
makes exactly that fixture validate and leaves the others rejected. Two fixtures key on `required`
(the root's and the `error` object's), at different schema paths. Measured:

| mutation | body_not_object | code_not_string | code_not_upper_snake | details_not_string | error_not_object | message_id_not_string | message_not_string | missing_code | missing_error | session_id_not_string |
|---|---|---|---|---|---|---|---|---|---|---|
| *intact* | reject | reject | reject | reject | reject | reject | reject | reject | reject | reject |
| drop root `type` | **PASS** | reject | reject | reject | reject | reject | reject | reject | reject | reject |
| drop root `required` | reject | reject | reject | reject | reject | reject | reject | reject | **PASS** | reject |
| drop `error` `type` | reject | reject | reject | reject | **PASS** | reject | reject | reject | reject | reject |
| drop `error` `required` | reject | reject | reject | reject | reject | reject | reject | **PASS** | reject | reject |
| drop `code` `type` | reject | **PASS** | reject | reject | reject | reject | reject | reject | reject | reject |
| drop `code` `pattern` | reject | reject | **PASS** | reject | reject | reject | reject | reject | reject | reject |
| drop `message` `type` | reject | reject | reject | reject | reject | reject | **PASS** | reject | reject | reject |
| drop `session_id` `type` | reject | reject | reject | reject | reject | reject | reject | reject | reject | **PASS** |
| drop `message_id` `type` | reject | reject | reject | reject | reject | **PASS** | reject | reject | reject | reject |
| drop `details` `type` | reject | reject | reject | **PASS** | reject | reject | reject | reject | reject | reject |

## What the schema cannot check

That `code` is a code actually listed in `registries/error-codes.md`, that the response's HTTP
status is that code's HTTP Status, and that `details` decodes to the JSON RFC-MACP-0006 §3.2
defines for `HISTORY_UNAVAILABLE`. The pattern only rules out a code that cannot be a registry
identifier.
