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
| `signal_with_session_id.json` | Signals are ambient: `session_id` MUST be empty (RFC-MACP-0001 §6) |
| `signal_with_mode.json` | Signals are ambient: `mode` MUST be empty (RFC-MACP-0001 §6) |
| `session_scoped_empty_session_id.json` | Session-scoped messages MUST carry non-empty `session_id` (RFC-MACP-0001 §6) |
| `session_scoped_empty_mode.json` | Session-scoped messages MUST carry non-empty `mode` (RFC-MACP-0001 §6) |
| `progress_mode_without_session_id.json` | `Progress` MUST have `mode` and `session_id` both empty or both non-empty — mixed (non-empty `mode`, empty `session_id`) MUST be rejected (RFC-MACP-0001 §6) |
| `progress_session_id_without_mode.json` | `Progress` MUST have `mode` and `session_id` both empty or both non-empty — mixed (empty `mode`, non-empty `session_id`) MUST be rejected (RFC-MACP-0001 §6) |
| `payload_and_payload_b64.json` | `payload` and `payload_b64` are mutually exclusive (RFC-MACP-0001 §10) |
| `missing_payload.json` | Exactly one of `payload` / `payload_b64` is required (RFC-MACP-0001 §10) |
| `bad_macp_version.json` | `macp_version` MUST be semantic-version formatted |
| `session_start_missing_versions.json` | SessionStart MUST bind `ttl_ms`, `mode_version`, `configuration_version` (RFC-MACP-0001 §7, RFC-MACP-0003) |
| `session_start_negative_max_suspend_ms.json` | `max_suspend_ms` MUST be non-negative (RFC-MACP-0001 §7.5, RFC-MACP-0003 §2) |
| `session_start_max_suspend_ms_not_integer.json` | `max_suspend_ms` MUST be an integer (RFC-MACP-0001 §7.5) |
| `commitment_supersedes_bad_hash_format.json` | `supersedes.commitment_hash` MUST be a syntactically valid canonical commitment hash: `sha256:` + 64 lowercase hex characters (RFC-MACP-0001 §7.3.1, RFC-MACP-0013) |
| `commitment_supersedes_empty_session_id.json` | `supersedes.session_id` MUST be non-empty when `supersedes` is present (RFC-MACP-0001 §7.3.1) |

`signal_with_session_id.json`/`signal_with_mode.json` and
`session_scoped_empty_session_id.json`/`session_scoped_empty_mode.json` are
split pairs, not one fixture apiece: each MUST isolate exactly one constraint
(see the repo's `CLAUDE.md`), and the original single fixture in each pair
violated `mode` and `session_id` together (issue #128). `validate-json.sh`
now asserts this with `ajv --all-errors` on every fixture in this directory,
so a fixture that regresses to a compound violation fails loudly instead of
silently losing coverage.

To add a case: drop a new `.json` file here with an `_invalid_because`
annotation — `validate-json.sh` picks it up automatically and asserts it fails
envelope validation, and that it does so for exactly one reason.
