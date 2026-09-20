# `contract.json` — cross-implementation parity contract

## Purpose

This directory holds `contract.json`, a small, hand-maintained manifest pinning values that
today already agree — with matching values but no shared source of truth — across this
repo (where applicable), `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript`.
`scripts/check-parity-contract.py` holds every value that has an in-repo source (a
registry, an RFC prose block, the proto file, or the conformance fixture corpus) to that
source, so this file is never itself an unverified third copy of anything.

**This file is non-normative.** It *projects* values whose actual normative home — where
one exists — is named in that section's own `source` field. `contract.json` MUST NOT
itself be cited as a normative source anywhere in this repo's docs or RFCs; cite the named
RFC section, registry, or proto file instead. Several values pinned here have **no**
normative home at all today (see "Open items" below) — the manifest says so explicitly
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
| `contribute_payload` | runtime, both SDKs | The `Contribute` payload's proto vs. legacy-JSON byte disambiguation: decode order, first-byte facts, and generated round-trip vectors |
| `contribute_acceptance` | runtime only | Behavior not yet confirmed across all three implementations (see "Open items") |

Every section carries:
- `applies_to` — which of `macp-runtime` / `macp-sdk-python` / `macp-sdk-typescript` MUST
  assert this section. Adding a consumer to a section's `applies_to` is a MINOR version
  bump (see Versioning) and is expected to turn that consumer's CI red at its next pin
  bump until it actually wires the assertion — that is the mechanism working as designed.
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

Deliberately **not** seeded in v1.0.0, tracked as follow-up work instead of silently
patched over here:

- **`Contribute` payload decode on non-canonical inputs.** "No known drift" is true only
  on the canonical vectors this manifest pins. On non-canonical inputs (leading
  whitespace, a non-string `value`, an empty payload) the three implementations already
  disagree — seeding a value the implementations don't actually agree on would poison this
  mechanism's credibility on day one. Tracked as a follow-up issue per SDK.
- **`macp_version` `"1.0"` has no normative literal in any RFC.** A candidate
  one-sentence RFC-MACP-0001 amendment is tracked as its own future RFC PR, not folded into
  this manifest.
- **`contribute_acceptance.empty_payload` is `macp-runtime`-only.** Whether both SDKs
  should reject an empty `Contribute` payload the same way is an open cross-SDK question,
  tracked as a follow-up issue; only once both SDKs agree does the corresponding value get
  added to `contribute_acceptance.applies_to` (a MINOR bump).
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
