# SDK Parity Requirements

This document defines what MACP SDKs must implement to be considered conformant, and the sync mechanisms that keep them aligned.

## MUST Implement

Every official MACP SDK MUST provide:

### Transport Layer
- **MacpClient** — gRPC client implementing all RPCs in `MACPRuntimeService` (currently 20)
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

### Convenience Methods
- `sendSignal()` / `send_signal()` — ambient signal emission
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
- **Source of truth**: `schemas/conformance/` in this RFC repo (copied from Runtime, which is authoritative)
- **Local sync**: `make sync-fixtures` in each SDK
- **CI enforcement**: `fixture-sync` job verifies fixtures match canonical source

### Adding a New RPC or Mode
1. Define in RFC repo's proto files
2. Publish to BSR
3. Each SDK runs `make sync-protos` → implements the new RPC/mode → adds tests
4. If the change affects projections, add a conformance fixture and run `make sync-fixtures` downstream

## Conformance Test Suite

Each SDK must include a conformance test runner that:

1. Loads all `*.json` fixtures from `tests/conformance/`
2. Replays accepted messages (where `expect == "accept"`) through the matching projection
3. Verifies transcript length, commitment presence, and commitment field values
4. Skips `multi_round` fixtures (extension mode, no required projection)
5. Skips `reject_paths` fixtures (test runtime rejection, not projection replay)

The fixture format is documented in `schemas/conformance/README.md`.
