# MACP Conformance Levels

This page defines what an implementation claims when it says it conforms to MACP, and which fixtures back each claim. The fixtures live in [`schemas/conformance/`](../schemas/conformance/README.md), and each spec release also ships them as a pinned bundle (see [Pinning a release bundle](../schemas/conformance/README.md#pinning-a-release-bundle)).

Levels are **informative**. The normative requirements are in the RFCs; a level names a set of fixtures that exercise them, so that two implementations can compare claims.

## Levels

Each level includes everything in the level above it.

| Level | Fixtures that must pass | What it shows |
|---|---|---|
| **Core** | `session_start_reject_paths.json`, and the commitment-hash vectors `cmt-hash/cmt_hash_001`–`010` | `SessionStart` validation ([RFC-MACP-0001 §7](../rfcs/RFC-MACP-0001-core.md)) and the canonical commitment hash, both computing it and verifying it ([RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md)) |
| **Core + Decision** | every `decision_*.json` | the Decision Mode ([RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md)), including empty tallies, vetoes and finalize-decline |
| **Standard modes** | every `proposal_*.json`, `task_*.json`, `handoff_*.json` and `quorum_*.json` | all five standard modes ([RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md) through [RFC-MACP-0011](../rfcs/RFC-MACP-0011-quorum-mode.md)) |

The `ext.multi_round.v1` extension mode has its own fixtures (`multi_round_*.json`). An implementation that supports it MAY add "+ multi_round" to its claim; it is not part of any level.

Passing a fixture means the harness rules in [`schemas/conformance/README.md`](../schemas/conformance/README.md) hold: each message is accepted or rejected as the fixture says (with `expected_error_code` where given), and the final state, resolution and mode state match.

## Profiles

A level says *what* passes. A profile says *how* the implementation was driven, because the same semantics can ship in two shapes.

| Profile | How fixtures are driven | Notes |
|---|---|---|
| **Server** | over the network, through `MACPRuntimeService` ([RFC-MACP-0006 §3](../rfcs/RFC-MACP-0006-transport-bindings.md)) | the shape most adopters run |
| **Embedded (library)** | in-process, by calling the implementation's acceptance and replay API directly, with no `MACPRuntimeService` endpoint | a runtime that embeds an implementation as a library; RFC-MACP-0001 §7.6 item 5 already applies acceptance obligations to such runtimes. See [Embedding MACP as a library](../README.md#embedding-macp-as-a-library) |

A claim names both, for example "Standard modes, Server profile" or "Standard modes, Embedded profile". An Embedded claim SHOULD also state the semantics revision it was tested at ([RFC-MACP-0003 §3.2](../rfcs/RFC-MACP-0003-determinism.md)), since that revision decides which rules replay applies.

Two things a Server-profile run cannot observe over the wire, and how a claim handles them:

- **Commitment hash.** `MACPRuntimeService` has no RPC that returns a commitment hash, so a Server claim at Core or above counts the commitment-hash vectors `cmt_hash_001`–`010` when they pass in-process against the same implementation and release. The claim says so, for example "Standard modes, Server profile (hash vectors in-process)".
- **Clock-dependent fixtures.** A fixture that needs the session clock advanced (TTL expiry) is reported as skipped with the reason `needs-clock-control` over the network, and does not count against a level. Embedded runs drive it with a controlled clock.

## Verifier role

Some implementations do not run sessions at all but check results, for example an SDK that verifies a `CommitmentRef` it received. Such an implementation claims the **Verifier** role by passing the commitment-hash vectors `cmt_hash_001`–`010`. The role is listed separately because it is not a runtime level.

## Making a claim

Implementations self-report: they run the fixtures in their own CI and link that suite from [`IMPLEMENTATIONS.md`](../IMPLEMENTATIONS.md). A Server can use the [`macp-conform`](https://crates.io/crates/macp-conform) runner instead of writing its own harness: install it with `cargo install macp-conform --features grpc`, point it at a `MACPRuntimeService` endpoint and a checkout's `schemas/conformance`, and it reports the level reached as JSON, applying the two Server-profile rules above. Its [README](https://github.com/multiagentcoordinationprotocol/macp-runtime/tree/main/crates/macp-conform) lists the flags and what a Server run leaves unverified. An Embedded implementation in another language still runs the fixtures through its own API. To be listed, open a pull request that adds a row with the level, profile, the spec commit or bundle version you test against, and a link to the CI job or test file that runs the fixtures.
