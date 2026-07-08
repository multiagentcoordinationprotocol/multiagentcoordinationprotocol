# Invalid envelope fixtures (negative schema tests)

Each file in this directory is an envelope that MUST be **rejected** by
`schemas/json/macp-envelope.schema.json`. They are regression tests for the
schema's structural constraints: if a schema change accidentally loosens a
constraint, `scripts/validate-json.sh` fails because one of these fixtures
starts validating.

Each fixture carries a top-level `_invalid_because` annotation stating the
constraint it violates and the RFC section that defines it. The envelope
schema permits unknown fields (forward compatibility), so the annotation
itself never causes the rejection.

| Fixture | Violated constraint |
|---------|---------------------|
| `signal_with_session_id.json` | Signals are ambient: `mode` and `session_id` MUST be empty (RFC-MACP-0001 §6) |
| `session_scoped_empty_session_id.json` | Session-scoped messages MUST carry non-empty `mode` and `session_id` (RFC-MACP-0001 §6) |
| `payload_and_payload_b64.json` | `payload` and `payload_b64` are mutually exclusive (RFC-MACP-0001 §10) |
| `missing_payload.json` | Exactly one of `payload` / `payload_b64` is required (RFC-MACP-0001 §10) |
| `bad_macp_version.json` | `macp_version` MUST be semantic-version formatted |
| `session_start_missing_versions.json` | SessionStart MUST bind `ttl_ms`, `mode_version`, `configuration_version` (RFC-MACP-0001 §7, RFC-MACP-0003) |

To add a case: drop a new `.json` file here with an `_invalid_because`
annotation — `validate-json.sh` picks it up automatically and asserts it fails
envelope validation.
