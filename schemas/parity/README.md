# `contract.json` — cross-implementation parity contract

## Purpose

This directory holds `contract.json`, a small, hand-maintained manifest pinning values that
today already agree — with matching values but no shared source of truth — across this
repo (where applicable), `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript`.
`scripts/check-parity-contract.py` holds every value that has an in-repo source (a
registry, an RFC prose block, a JSON Schema, or the example/conformance corpora) to that
source, so this file is never itself an unverified third copy of anything. It does not cover
everything: a value whose `source` declares it a convention with no in-repo home often has
nothing to hold it to. Some are held to other values inside this manifest instead — among them
`retry.backoff_schedule_seconds`, recomputed from the `retry` fields it derives from, and
`contribute_payload`'s two `first_byte` discriminator bytes, which must be the bytes every
vector actually leads with. Read that script rather than any summary of it, including this one,
before relying on a particular value being guarded.

**This file is non-normative.** It *projects* values whose actual normative home — where
one exists — is named in that section's own `source` field. `contract.json` MUST NOT
itself be cited as a normative source anywhere in this repo's docs or RFCs; cite the named
RFC section, registry, or proto file instead. Several values pinned here have **no**
normative home at all today (their own `source` fields say so) — the manifest says so explicitly
rather than inventing a citation, and pinning the value here does not create one.

## Sections

| Section | `applies_to` | What it pins |
|---|---|---|
| `protocol` | runtime, both SDKs | The `macp_version` envelope literal (`"1.0"`) |
| `modes` | runtime, both SDKs | The 5 registry-backed standard mode ids, plus the 1 shipped extension mode id (`ext.multi_round.v1`, not registry-backed) |
| `defaults` | runtime, both SDKs | `mode_version`, `configuration_version`, `policy_version` (`policy.default`), and the policy-builder default `schema_version` |
| `error_codes` | runtime, both SDKs | The 16 `permanent` + 1 `deprecated` canonical error-code strings |
| `retry` | both SDKs | `RetryPolicy` defaults: max retries, base/max backoff, the derived backoff schedule, the retryable error-code set, and the deliberate absence of jitter |
| `projection_anomaly` | both SDKs | The `ProjectionAnomaly` field set, field order, the two anomaly-kind strings, and the snake_case→lowerCamelCase naming transform a lowerCamelCase consumer follows |
| `commitment_hash` | runtime, both SDKs | The commitment-hash format, pinned as an accept/reject behavior table (not a shared regex string, since `macp-runtime` implements this as a hand-written byte check, not a regex) |
| `contribute_payload` | runtime, both SDKs | The `Contribute` payload's proto vs. legacy-JSON byte disambiguation: decode order, first-byte facts, and generated round-trip vectors, including the `collision_*` vectors at the value byte-lengths where a canonical-proto payload also parses as JSON |
| `contribute_acceptance` | runtime only | Whether an empty `Contribute` payload is rejected — a runtime-only acceptance gate by design, not an unconfirmed value: both SDKs deliberately decode without raising instead of gating (see the section's own `source`) |

Every section carries:
- `applies_to` — which of `macp-runtime` / `macp-sdk-python` / `macp-sdk-typescript` MUST
  assert this section. Adding a consumer to a section's `applies_to` is a MINOR version
  bump (see Versioning) and is expected to turn that consumer's CI red until it actually
  wires the assertion — at its next pin bump if it pins a spec revision, or on its next CI
  run if it tracks this repo's default branch instead. That is the mechanism working as
  designed.
- `source` — where the value actually comes from. Honest about the absence of a normative
  home where one doesn't exist, rather than inventing a citation.

## Versioning

`contract_version` is semver:

- **PATCH** — annotation or `source` text changes only; no value changes.
- **MINOR** — a new section, a new vector, a new reject example, or a new consumer named
  in a section's `applies_to`.
- **MAJOR** — an existing frozen value changes or is removed. By construction this
  requires the upstream RFC/registry/proto change to land *first* — `check-parity-contract.py`
  holds every in-repo-sourced value to its source, so an unmatched manifest edit fails the
  checker before it can land.

No git SHA is embedded in this manifest — it would be unknowable pre-merge and would churn
on every unrelated edit. Provenance of *which spec-repo commit a consumer vendored* lives
in that consumer's own tree (a `SOURCE.md`, matching how both SDKs already document their
vendored `cmt-hash` pack).

## Open items

Deliberately **not** seeded here, tracked as follow-up work instead of silently
patched over:

- **Non-string `value` in legacy `Contribute` JSON is still unpinned.** The
  canonical-proto/legacy-JSON length-collision band is now pinned by
  `contribute_payload`'s `collision_*` vectors, and empty-payload gating is settled
  (see `contribute_acceptance`'s own `source`). What remains open is what a decoder
  does with valid legacy JSON whose `value` is not a string: `macp-sdk-typescript`
  coerces it (`String(parsed.value ?? '')`), `macp-sdk-python` passes it through
  uninterpreted, and `macp-runtime` declines it outright (its legacy-JSON reader types
  `value` as a required string, so a non-string fails to deserialize). No two of the three
  agree — so no value is seeded here until they converge. Tracked as issue #142.
- **`projection_anomaly.kind`'s static contract width differs by SDK.** Python types
  `kind` as a plain `str`; TypeScript types it as a closed 2-value union. The two SDKs
  agree on every runtime value produced today, but this manifest cannot itself make
  Python's type-checker enforce the same closed set TypeScript's does — that is each SDK's
  own follow-up, not something a values manifest can fix.
- **`field_case_rule` (in `projection_anomaly`) is new prescriptive text**, not a
  projection of an existing normative statement — there is no RFC, registry, or proto home
  for the snake_case→lowerCamelCase transform contract anywhere in this repo. It is kept
  here because it is small and genuinely useful to a lowerCamelCase consumer, worded
  descriptively rather than as an RFC-2119 requirement, and covered by this file's
  non-normative disclaimer above rather than treated as an exception to it.
