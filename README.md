# Multi-Agent Coordination Protocol (MACP)

**Version:** 1.0.0-draft
**Status:** Community Standards Track (Draft)
**Canonical wire format:** Protocol Buffers
**Normative transport:** gRPC over HTTP/2
**Required JSON mapping:** Yes

MACP is a coordination kernel for autonomous agent ecosystems. It exists for one reason: once intelligent systems stop being isolated tools and start behaving like ecosystems, the hard problem stops being capability and becomes convergence.

MACP introduces one strict invariant:

> **Binding, convergent coordination MUST occur inside explicit, bounded Coordination Sessions.**

Ambient interaction remains continuous and non-binding through **Signals**. Binding interaction occurs only inside **Sessions**. That separation keeps coordination explicit, bounded, auditable, and replayable.

**Try it:** the [Quickstart](docs/quickstart.md) runs a real Decision session against the reference runtime in about five minutes. **How it compares:** [Where MACP fits](docs/positioning.md) sets MACP beside MCP, A2A and framework orchestration, and says when not to use it.

## Project status

MACP is maintained by a single maintainer on a best-effort basis. Changes land when a consumer needs them; there is no release schedule and no SLA. That fact belongs at the top rather than in the commit graph, because it should inform how much of this you choose to build on.

**What is versioned and safe to pin:** the canonical Protobuf packages. Every `proto-v*` tag publishes them — to PyPI, crates.io and npmjs, and to GitHub Packages for the npm, Java, Kotlin and C# artifacts. A Go module tag is also pushed, but it is not installable yet (see [Using MACP Proto Packages](#using-macp-proto-packages)). They are governed by the schema-namespace rules in [VERSIONING.md](VERSIONING.md): breaking wire changes require a new `macp.vN` namespace, and unknown fields MUST be ignored for forward compatibility.

**What is not frozen:** the RFC text. All thirteen RFCs are drafts — two at `**Version:** 1.0.0-draft`, RFC-MACP-0002, RFC-MACP-0003, RFC-MACP-0009 and RFC-MACP-0011 at `1.1.0-draft`, RFC-MACP-0004, RFC-MACP-0010 and RFC-MACP-0013 at `1.2.0-draft`, RFC-MACP-0001 at `1.3.0-draft`, RFC-MACP-0007 at `1.4.0-draft`, RFC-MACP-0012 at `1.7.0-draft`, and RFC-MACP-0006 at `1.6.0-draft`. Nothing in this repository has been declared wire-frozen, and normative wording can still change.

**There is no promotion gate.** Every RFC's `**Status:**` line reads `Community Standards Track` — a track, not a lifecycle stage. This repository defines no Draft/Review/Final ladder, no criteria for advancing an RFC, and no mechanism beyond [CONTRIBUTING.md](CONTRIBUTING.md)'s "RFCs are accepted through community consensus". With one committer, consensus is not currently a meaningful gate. Read every RFC here as draft-quality regardless of how settled the prose reads.

What *is* mechanically enforced is narrower and real: `make validate` compiles the canonical Protobuf schemas, validates every example and conformance fixture against its JSON Schema, checks that the indexes in this file match the files on disk, and holds the cross-implementation parity-contract manifest (`schemas/parity/contract.json`) to those same in-repo sources. The RFC-MACP-0013 compute vectors (`cmt_hash_001`–`005`) additionally reproduce byte-for-byte in `macp-runtime` and in both SDKs; the verify vectors (`006`–`010`) are checked here by `make cmt-hash-vectors`, which decodes each payload's wire encoding itself. Enforcement covers the schemas and fixtures, and — as of `make prose-check` — ten mechanical properties of the normative prose: no line-number anchors, `schema_version` enumerations that agree across every site, RFC cross-references that resolve, cited RFCs that actually discuss the term they are cited for, a README version census that matches the RFC headers, a check count that agrees with every document stating it, a PolicyDescriptor required-field set that agrees across the schema, the RFC and the fixture linter, and a parity-contract "held to other manifest values" enumeration that agrees between `schemas/parity/README.md` and `docs/sdk-parity.md`, an RFC-MACP-0006 §3 RPC listing that matches `core.proto`, and session-state lists that agree with RFC-MACP-0001 §7.2. Whether a paragraph is *true* remains unenforced.

## What this repository contains

This repository is structured like a publishable protocol standard rather than a single monolithic spec. The goal is to keep the normative core small and stable while giving implementers enough architectural and operational guidance to build real runtimes.

```text
MACP/
  manifesto/
    manifesto.md

  rfcs/
    RFC-MACP-0001-core.md
    RFC-MACP-0002-modes.md
    RFC-MACP-0003-determinism.md
    RFC-MACP-0004-security.md
    RFC-MACP-0005-discovery-and-manifests.md
    RFC-MACP-0006-transport-bindings.md
    RFC-MACP-0007-decision-mode.md
    RFC-MACP-0008-proposal-mode.md
    RFC-MACP-0009-task-mode.md
    RFC-MACP-0010-handoff-mode.md
    RFC-MACP-0011-quorum-mode.md
    RFC-MACP-0012-policy.md
    RFC-MACP-0013-commitment-hash.md

  docs/
    architecture.md
    lifecycle.md
    runtime.md
    deployment.md
    examples.md
    modes.md
    determinism.md
    security.md
    discovery.md
    transports.md
    agent-manifest-schema.md
    sdk-parity.md
    conformance.md
    quickstart.md
    positioning.md
    policy-packs.md

  registries/
    README.md
    capabilities.md
    commitment-hash.md
    error-codes.md
    media-types.md
    modes.md
    policies.md
    transports.md

  schemas/
    envelope.proto            # flat entrypoints
    core.proto
    policy.proto
    modes/
      decision.proto
      proposal.proto
      task.proto
      handoff.proto
      quorum.proto
      multi_round.proto
    proto/                    # canonical versioned schemas
      macp/v1/
        envelope.proto
        core.proto
        policy.proto
      macp/modes/decision/v1/
        decision.proto
      macp/modes/proposal/v1/
        proposal.proto
      macp/modes/task/v1/
        task.proto
      macp/modes/handoff/v1/
        handoff.proto
      macp/modes/quorum/v1/
        quorum.proto
      macp/modes/multi_round/v1/
        multi_round.proto     # ext.multi_round.v1 extension mode
    json/
      macp-envelope.schema.json
      macp-agent-manifest.schema.json
      macp-mode-descriptor.schema.json
      macp-session-metadata.schema.json
      macp-session-lifecycle-event.schema.json
      macp-run-descriptor.schema.json   # non-normative product contract (control plane)
      macp-agent-bootstrap.schema.json  # non-normative product contract (agent hosts)
      macp-ack.schema.json
      macp-error.schema.json
      macp-policy-descriptor.schema.json
      macp-parity-contract.schema.json
      macp-decision-receipt.schema.json
      tests/
        invalid/          # negative envelope fixtures (MUST fail validation)
        invalid-policy-rules/  # negative Decision-rules fixtures (MUST fail validation)
        invalid-quorum-rules/  # negative Quorum-rules fixtures (MUST fail validation)
        invalid-proposal-rules/ # negative Proposal-rules fixtures (MUST fail validation)
        invalid-task-rules/    # negative Task-rules fixtures (MUST fail validation)
        invalid-handoff-rules/ # negative Handoff-rules fixtures (MUST fail validation)
        invalid-policy-descriptors/ # negative PolicyDescriptor fixtures (MUST fail validation)
        invalid-parity-contract/ # negative parity-contract fixtures (MUST fail validation)
        invalid-agent-bootstrap/ # negative agent-bootstrap fixtures (MUST fail validation)
        valid-policy-rules/    # maximal positive rules fixtures (MUST validate)
      policy/
        decision-rules.schema.json
        quorum-rules.schema.json
        proposal-rules.schema.json
        task-rules.schema.json
        handoff-rules.schema.json
    conformance/
      README.md
      schema.json         # fixture-format JSON Schema
      lint_fixtures.py    # internal-consistency linter (CI)
      cmt-hash/           # RFC-MACP-0013 canonical hash vectors + vector-schema.json
      decision_happy_path.json
      decision_negative_outcome.json
      decision_reject_paths.json
      decision_critical_objection_veto.json
      decision_critical_objection_finalize_decline.json
      decision_empty_tally_binding.json
      decision_empty_tally_legacy.json
      decision_weighted_zero_weight.json
      decision_weighted_zero_weight_v1.json
      decision_zero_participants.json
      decision_zero_proposal_commitment.json
      decision_majority_empty_tally.json
      decision_supermajority_empty_tally.json
      decision_none_v3_empty_tally.json
      decision_none_v3_empty_tally_positive.json
      decision_legacy_require_vote_quorum.json
      decision_plurality.json
      decision_finalize_decline_empty_tally.json
      decision_finalize_decline_quorum_waiver.json
      decision_policy_pack_human_signoff.json
      decision_policy_pack_compliance_vote.json
      proposal_happy_path.json
      proposal_negative_outcome.json
      proposal_reject_paths.json
      task_happy_path.json
      task_negative_outcome.json
      task_reject_paths.json
      handoff_happy_path.json
      handoff_negative_outcome.json
      handoff_reject_paths.json
      handoff_implicit_accept.json
      quorum_happy_path.json
      quorum_negative_outcome.json
      quorum_reject_paths.json
      quorum_unreachable_override.json
      quorum_percentage_override_reachable.json
      quorum_policy_pack_two_agent_rule.json
      multi_round_happy_path.json
      multi_round_reject_paths.json
      session_start_reject_paths.json
    parity/
      contract.json        # cross-implementation parity-contract manifest (issue #134)
      README.md

  examples/
    decision-mode-session.json
    proposal-mode-session.json
    task-mode-session.json
    handoff-mode-session.json
    quorum-mode-session.json
    policy-decision-session.json
    policy-registration-exchange.json
    json/
      signal.json
      session_start.json
      commitment.json
      session_cancel.json
    proto/
      envelope.bin
    discovery/
      agent_manifest.json
      mode_descriptor.json
    policies/             # ready-made policy packs (docs/policy-packs.md)
      human-signoff.json
      two-agent-rule.json
      compliance-vote.json

  governance/
    GOVERNANCE.md
```

## Reading order

If you are new to MACP, start here:

1. **[manifesto/manifesto.md](manifesto/manifesto.md)** - the category-defining argument for why a coordination kernel is needed.
2. **[RFC-MACP-0001-core.md](rfcs/RFC-MACP-0001-core.md)** - the normative core protocol.
3. **[RFC-MACP-0002-modes.md](rfcs/RFC-MACP-0002-modes.md)** - the mode extension framework and the standard-mode boundary for the main repo.
4. **[RFC-MACP-0007-decision-mode.md](rfcs/RFC-MACP-0007-decision-mode.md)** through **[RFC-MACP-0011-quorum-mode.md](rfcs/RFC-MACP-0011-quorum-mode.md)** - the standard coordination primitives defined in this repository.
5. **[RFC-MACP-0012-policy.md](rfcs/RFC-MACP-0012-policy.md)** - governance policy framework for declarative, replay-safe session governance.
6. **[RFC-MACP-0013-commitment-hash.md](rfcs/RFC-MACP-0013-commitment-hash.md)** - canonical algorithm for computing `CommitmentRef.commitment_hash`.
7. **[RFC-MACP-0003-determinism.md](rfcs/RFC-MACP-0003-determinism.md)** - replay integrity and determinism classes.
8. **[RFC-MACP-0005-discovery-and-manifests.md](rfcs/RFC-MACP-0005-discovery-and-manifests.md)** - agent and runtime discovery, manifest schemas.
9. **[RFC-MACP-0006-transport-bindings.md](rfcs/RFC-MACP-0006-transport-bindings.md)** - standard transport bindings.
10. **[docs/architecture.md](docs/architecture.md)** and **[docs/runtime.md](docs/runtime.md)** - how to implement and operate a runtime.
11. **[docs/conformance.md](docs/conformance.md)** and **[IMPLEMENTATIONS.md](IMPLEMENTATIONS.md)** - conformance levels and profiles, and the implementations that claim them.

## Standards posture

MACP is intentionally split into a small set of RFCs because that makes the standard more credible and easier to evolve.

- **RFC-MACP-0001 Core** defines the base protocol, capability negotiation, the envelope model, session lifecycle, transport requirements, and registry hooks.
- **RFC-MACP-0002 Modes** defines how semantic coordination modes extend MACP without violating Core invariants and which kinds of modes belong in the main standards repo.
- **RFC-MACP-0003 Determinism** defines structural replay integrity, semantic determinism classes, and side-effect handling patterns.
- **RFC-MACP-0004 Security** defines the threat model and required defenses.
- **RFC-MACP-0005 Discovery** defines agent and runtime discovery, manifest schemas, and well-known endpoints.
- **RFC-MACP-0006 Transport Bindings** defines standard transport bindings (gRPC, HTTP, WebSocket, Message Bus).
- **RFC-MACP-0007 through RFC-MACP-0011** define the main-repository standard modes: Decision, Proposal, Task, Handoff, and Quorum.
- **RFC-MACP-0012 Policy** defines the governance policy framework for declarative, deterministic, replay-safe session governance.
- **RFC-MACP-0013 Canonical Commitment Hash** defines the canonical algorithm for computing `CommitmentRef.commitment_hash`.

The main RFC repo standardizes only foundational coordination primitives. Domain workflows and fast-moving experiments should live in incubator or vendor repositories, not in this standards repo. Runtimes may still ship additional implementation-defined modes, but those modes should not be presented as part of the five-mode standards-track set unless they are promoted into this repo and registry.

## Capability negotiation

MACP runtimes and clients negotiate protocol compatibility and optional features during initialization.

The base capability model supports:

- `sessions.stream` - bidirectional session streams
- `sessions.list_sessions` - paginated session metadata listing
- `sessions.watch_sessions` - streaming session lifecycle events
- `cancellation.cancelSession` - explicit session cancellation
- `progress.progress` - non-binding progress updates
- `manifest.getManifest` - runtime/agent manifest discovery
- `modeRegistry.listModes` - mode discovery
- `modeRegistry.listChanged` - registry change notifications
- `roots.listRoots` - disclosure of coordination roots/boundaries
- `roots.listChanged` - root change notifications
- `policyRegistry.listPolicies` - policy discovery
- `policyRegistry.registerPolicy` - policy registration
- `policyRegistry.listChanged` - policy change notifications
- `policyRegistry.ruleExtensions` - vendor-extension rule keys the runtime implements (RFC-MACP-0012 §4, §9)
- `experimental` - explicitly non-standard features

## Embedding MACP as a library

MACP does not require a network server. A runtime MAY embed an implementation as a library and drive sessions in-process, with no `MACPRuntimeService` endpoint. The reference runtime's `macp-core`, `macp-modes`, `macp-policy` and `macp-pb` crates support this (see the runtime's `docs/embedding.md`). An embedded runtime has the same obligations as a server: acceptance obligations ([RFC-MACP-0001 §7.6](rfcs/RFC-MACP-0001-core.md)), replay integrity and semantics revisions ([RFC-MACP-0003 §3.2](rfcs/RFC-MACP-0003-determinism.md)), and the conformance fixtures under `schemas/conformance/`. [docs/conformance.md](docs/conformance.md) defines an Embedded profile for claiming conformance this way.

## Compatibility model

MACP uses a layered compatibility model:

- **Protocol version** governs base runtime behavior.
- **Schema namespace** governs canonical Protobuf compatibility (for example `macp.v1`).
- **Mode version** governs semantic behavior within a session.
- **Configuration / policy version** governs runtime behavior that is bound to replay.

Major protocol version mismatches are not compatible. Minor versions are expected to be backward compatible. Unknown fields MUST be ignored to preserve forward compatibility.

## Using MACP Proto Packages

Most users want an SDK rather than raw protos:

```bash
pip install macp-sdk-python      # Python 3.11+
npm install macp-sdk-typescript  # Node 20+
```

The [Quickstart](docs/quickstart.md) runs a session with the Python SDK. To generate your own stubs, the canonical protos are published as versioned packages on every `proto-v*` tag (currently `0.1.11`):

```bash
# Buf Schema Registry: generate stubs for any language (uses your buf.gen.yaml)
buf generate buf.build/multiagentcoordinationprotocol/macp

# Python (generated stubs)
pip install macp-proto==0.1.11

# Rust (raw .proto files; generate with prost/tonic in build.rs)
cargo add macp-proto@0.1.11

# TypeScript / Node.js (raw .proto files)
npm install @multiagentcoordinationprotocol/proto@0.1.11
```

The Java (`io.macp:macp-proto`), Kotlin (`io.macp:macp-proto-kotlin`) and C# (`Macp.Proto`) packages are published to GitHub Packages, which needs a GitHub token to install from. The Go module is not installable from its tag yet: its `go.mod` declares a module path that does not match where the tag lives. Until that is fixed, generate Go stubs with `buf generate`.

See `CONTRIBUTING.md` for the release workflow.

## Repository highlights

- **Human-friendly schema entrypoints** live directly under `schemas/`.
- **Canonical versioned schemas** live under `schemas/proto/`.
- **Registries** live under `registries/` and are designed to evolve without destabilizing the core.
- **JSON schemas** cover the canonical JSON envelope mapping, agent manifests, and mode descriptors.
- **Examples** now include one transcript for each standards-track mode defined in the main repo.

## Development

```bash
make validate
```

`make validate` meta-validates all JSON Schemas, validates every example and conformance fixture against its schema, asserts the negative envelope fixtures are rejected, lints conformance fixtures for internal consistency, checks the cross-implementation parity-contract manifest against its in-repo sources, lints and compiles all versioned Protobuf definitions, verifies the raw-proto packages match the canonical schemas, and holds `macp-envelope.schema.json`'s `$defs` to the Core payload set and field sets declared in `schemas/proto/macp/v1/core.proto` (issue #173). Run `make help` for individual targets; `make install-tools` installs `ajv-cli`, `protoc`, and `buf`.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
