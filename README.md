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

## Project status

MACP is maintained by a single maintainer on a best-effort basis. Changes land when a consumer needs them; there is no release schedule and no SLA. That fact belongs at the top rather than in the commit graph, because it should inform how much of this you choose to build on.

**What is versioned and safe to pin:** the canonical Protobuf packages. Every `proto-v*` tag publishes them — to PyPI and crates.io, to GitHub Packages for the npm, Java, Kotlin, and C# artifacts, and as a Go module resolved from the tag itself. They are governed by the schema-namespace rules in [VERSIONING.md](VERSIONING.md): breaking wire changes require a new `macp.vN` namespace, and unknown fields MUST be ignored for forward compatibility.

**What is not frozen:** the RFC text. All thirteen RFCs are drafts — twelve at `**Version:** 1.0.0-draft`, RFC-MACP-0006 at `1.1.0-draft`. Nothing in this repository has been declared wire-frozen, and normative wording can still change.

**There is no promotion gate.** Every RFC's `**Status:**` line reads `Community Standards Track` — a track, not a lifecycle stage. This repository defines no Draft/Review/Final ladder, no criteria for advancing an RFC, and no mechanism beyond [CONTRIBUTING.md](CONTRIBUTING.md)'s "RFCs are accepted through community consensus". With one committer, consensus is not currently a meaningful gate. Read every RFC here as draft-quality regardless of how settled the prose reads.

What *is* mechanically enforced is narrower and real: `make validate` compiles the canonical Protobuf schemas, validates every example and conformance fixture against its JSON Schema, and checks that the indexes in this file match the files on disk. The RFC-MACP-0013 commitment-hash vectors additionally reproduce byte-for-byte in `macp-runtime` and in both SDKs. Enforcement covers the schemas and fixtures — not the normative prose.

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
      macp-run-descriptor.schema.json
      macp-agent-bootstrap.schema.json
      macp-ack.schema.json
      macp-error.schema.json
      macp-policy-descriptor.schema.json
      tests/
        invalid/          # negative envelope fixtures (MUST fail validation)
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
      proposal_happy_path.json
      proposal_negative_outcome.json
      proposal_reject_paths.json
      task_happy_path.json
      task_negative_outcome.json
      task_reject_paths.json
      handoff_happy_path.json
      handoff_negative_outcome.json
      handoff_reject_paths.json
      quorum_happy_path.json
      quorum_negative_outcome.json
      quorum_reject_paths.json
      multi_round_happy_path.json
      multi_round_reject_paths.json

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
- `experimental` - explicitly non-standard features

## Compatibility model

MACP uses a layered compatibility model:

- **Protocol version** governs base runtime behavior.
- **Schema namespace** governs canonical Protobuf compatibility (for example `macp.v1`).
- **Mode version** governs semantic behavior within a session.
- **Configuration / policy version** governs runtime behavior that is bound to replay.

Major protocol version mismatches are not compatible. Minor versions are expected to be backward compatible. Unknown fields MUST be ignored to preserve forward compatibility.

## Using MACP Proto Packages

Proto definitions are published as versioned packages. Install them as regular dependencies:

```bash
# TypeScript / Node.js
npm install @macp/proto

# Python
pip install macp-proto

# Go
go get github.com/multiagentcoordinationprotocol/macp-proto-go@proto-v0.1.0

# Java (build.gradle.kts)
# implementation("io.macp:macp-proto:0.1.0")

# Kotlin (build.gradle.kts)
# implementation("io.macp:macp-proto-kotlin:0.1.0")

# C# (.csproj)
# <PackageReference Include="Macp.Proto" Version="0.1.0" />

# Swift (Package.swift)
# .package(url: "https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol.git", from: "0.1.0")

# Rust (Cargo.toml)
# macp-proto = { git = "https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol.git", tag = "proto-v0.1.0" }
```

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

`make validate` meta-validates all JSON Schemas, validates every example and conformance fixture against its schema, asserts the negative envelope fixtures are rejected, lints conformance fixtures for internal consistency, lints and compiles all versioned Protobuf definitions, and verifies the raw-proto packages match the canonical schemas. Run `make help` for individual targets; `make install-tools` installs `ajv-cli`, `protoc`, and `buf`.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
