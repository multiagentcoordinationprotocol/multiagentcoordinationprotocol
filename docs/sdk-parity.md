# SDK Parity Requirements

This document defines what MACP SDKs must implement to be considered conformant, and the sync mechanisms that keep them aligned.

## MUST Implement

Every official MACP SDK MUST provide:

### Transport Layer
- **MacpClient** — gRPC client implementing all RPCs in `MACPRuntimeService` (currently 24, including `SuspendSession`/`ResumeSession`)
- **MacpStream** — bidirectional streaming wrapper for `StreamSession`
- **Authentication** — dev agent (`x-macp-agent-id`) and bearer token modes

### Session Helpers
- One session class per standards-track mode (Decision, Proposal, Task, Handoff, Quorum)
- Each session wraps start, mode-specific actions, commit, cancel, metadata

### Projections
- One projection class per standards-track mode
- Client-side state machines tracking transcript, phase, and commitment
- Must pass the canonical conformance fixture suite (see below)

### Policy Framework
- Policy builder functions for all 5 modes (typed rule inputs → `PolicyDescriptor`)
- Client methods: `registerPolicy`, `unregisterPolicy`, `getPolicy`, `listPolicies`

### Error Hierarchy
- `MacpSdkError` — base SDK error
- `MacpTransportError` — gRPC communication failure
- `MacpAckError` — runtime rejected the message (NACK)
- `MacpSessionError` — session-level error (wrong state)
- `MacpTimeoutError` — operation timed out
- `MacpRetryError` — all retry attempts exhausted

### Retry
- `RetryPolicy` with configurable max retries, backoff base/max, retryable error codes
- `retrySend()` / `retry_send()` with exponential backoff
- Defaults are pinned in `schemas/parity/contract.json`'s `retry` section (see "Parity-Contract Manifest Sync" below)

### Convenience Methods
- `sendSignal()` / `send_signal()` — Ambient Signal emission
- `sendProgress()` / `send_progress()` — progress tracking

### Envelope Utilities
- Envelope builder with auto-generated message IDs and timestamps
- SessionStart and Commitment payload builders with defaults
- ID generators (session, message, commitment)

## MAY Implement

Optional features that enhance the SDK but are not required for conformance:

- **Watcher classes** — convenience wrappers around streaming RPCs (vs raw iterators)
- **HTTP transport adapter** — polling transport for non-gRPC environments
- **Base session/projection classes** — shared inheritance (vs standalone classes)
- **Agent framework** — Participant abstraction, dispatcher, strategies, bootstrap
- **Logging** — structured logging helpers

## Sync Mechanisms

### Proto Sync
- **Source of truth**: Buf Schema Registry at `buf.build/multiagentcoordinationprotocol/macp`
- **Local sync**: `make sync-protos` (from BSR) or `make sync-protos-local` (from sibling RFC checkout)
- **CI enforcement**: `proto-sync` job in each SDK's CI verifies no drift against BSR

### Conformance Fixture Sync
- **Source of truth**: `schemas/conformance/` in this RFC repo is the only canonical fixture location. Fixture changes land here first, then sync downstream; the runtime vendors byte-identical copies under `tests/conformance/` and its CI byte-compares them against this directory (see `schemas/conformance/README.md`).
- **Local sync**: `make sync-fixtures` in each SDK
- **CI enforcement**: `fixture-sync` job verifies fixtures match canonical source; this repo's CI validates every fixture against `schemas/conformance/schema.json` and lints internal consistency (`make conformance-lint`)

### Adding a New RPC or Mode
1. Define in RFC repo's proto files
2. Publish to BSR
3. Each SDK runs `make sync-protos` → implements the new RPC/mode → adds tests
4. If the change affects projections, add a conformance fixture and run `make sync-fixtures` downstream

### Parity-Contract Manifest Sync
- **Source of truth**: `schemas/parity/contract.json` in this RFC repo pins values that
  already agree — with matching values but no shared source of truth — across
  `macp-runtime`, `macp-sdk-python`, and `macp-sdk-typescript` (error codes, retry
  defaults, mode/version constants, the commitment-hash format, `Contribute` payload byte
  vectors, and `ProjectionAnomaly`'s shape). It is non-normative: where a value has an
  actual normative home, the manifest's `source` field names it — e.g. `policy_version`
  traces to RFC-MACP-0012 Section 5.1, and the commitment-hash format traces to
  RFC-MACP-0013 Section 7 — and the manifest MUST NOT itself be cited as that home.
- **`applies_to` semantics**: each section names which of `macp-runtime` /
  `macp-sdk-python` / `macp-sdk-typescript` MUST assert it. Adding a consumer to a
  section's `applies_to` is a MINOR manifest bump and is expected to turn that consumer's
  CI red until it wires the corresponding assertion — at its next pin bump if it pins a spec
  revision, or on its next CI run if it tracks the default branch (see the next bullet).
- **CI enforcement in this repo**: `make parity-contract` holds every in-repo-sourced
  value in the manifest to its registry/RFC/schema/fixture source, so an edit to the
  manifest that isn't backed by a matching upstream change fails before it can land. It does
  **not** cover everything: a value whose `source` declares it a convention with no in-repo home
  often has nothing to check it against, and can be given a wrong value without turning CI red
  — which is what those `source` fields are warning you about. Some are held to other values
  inside the manifest instead, among them `contribute_payload.first_byte`'s two discriminator
  bytes, asserted against the bytes every vector leads with; `macp-runtime` asserts those same
  two markers against its vendored copy, so that drift is now caught here rather than
  downstream. Read `scripts/check-parity-contract.py` rather than any summary of it before
  assuming a section is covered.
- **Consumer wiring, and why the two vendored copies behave differently**: `macp-runtime` and
  `macp-sdk-typescript` both vendor this manifest into their own `tests/parity/` and assert
  against it in CI. `macp-sdk-python` does not vendor it at all, and no issue tracks wiring it
  up — so a manifest change reaches that SDK only when a human carries it there. The two
  existing copies pin the spec repo differently, which is what decides
  who notices a manifest change and when: `macp-runtime` checks this repo out at an explicit
  pinned revision, so it stays green until its maintainers bump that revision deliberately,
  whereas `macp-sdk-typescript` checks out the default branch, so a merged manifest change
  reaches its drift check on that repo's next CI run without anyone opting in. A manifest
  change that adds a vector or a section therefore needs a re-vendor issue filed against each
  consumer, and the unpinned one is the time-sensitive half. See `schemas/parity/README.md` for
  the full section list and versioning rules.

## Conformance Test Suite

Each SDK must include a conformance test runner that:

1. Loads all `*.json` fixtures from `tests/conformance/`
2. Replays accepted messages (where `expect == "accept"`) through the matching projection
3. Verifies transcript length, commitment presence, and commitment field values
4. Skips `multi_round` fixtures (extension mode, no required projection)
5. Skips `reject_paths` fixtures (test runtime rejection, not projection replay)

The fixture format is documented in `schemas/conformance/README.md`.
