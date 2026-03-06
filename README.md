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

  docs/
    architecture.md
    lifecycle.md
    runtime.md
    deployment.md
    examples.md
    modes.md
    determinism.md
    security.md

  registries/
    README.md
    capabilities.md
    error-codes.md
    media-types.md
    modes.md

  schemas/
    envelope.proto
    core.proto
    modes/
      decision.proto
    proto/
      macp/v1/
      macp/modes/decision/v1/
    json/
      macp-envelope.schema.json
      macp-agent-manifest.schema.json
      macp-mode-descriptor.schema.json

  examples/
    decision-mode-session.json
    json/
    proto/
    discovery/
```

## Reading order

If you are new to MACP, start here:

1. **[manifesto/manifesto.md](manifesto/manifesto.md)** — the category-defining argument for why a coordination kernel is needed.
2. **[RFC-MACP-0001-core.md](rfcs/RFC-MACP-0001-core.md)** — the normative core protocol.
3. **[docs/architecture.md](docs/architecture.md)** — the architectural rendering of the protocol as a system.
4. **[docs/runtime.md](docs/runtime.md)** and **[docs/deployment.md](docs/deployment.md)** — how to implement and deploy it.
5. **[RFC-MACP-0002-modes.md](rfcs/RFC-MACP-0002-modes.md)** — how semantic extensions work.

## Standards posture

MACP is intentionally split into a small set of RFCs because that makes the standard more credible and easier to evolve.

- **RFC-MACP-0001 Core** defines the base protocol, capability negotiation, the envelope model, session lifecycle, transport requirements, and registry hooks.
- **RFC-MACP-0002 Modes** defines how semantic coordination modes extend MACP without violating Core invariants.
- **RFC-MACP-0003 Determinism** defines structural replay integrity, semantic determinism classes, and side-effect handling patterns.
- **RFC-MACP-0004 Security** defines the threat model and required defenses.

This split mirrors how mature standards separate the kernel from extension documents.

## Capability negotiation

MACP runtimes and clients negotiate protocol compatibility and optional features during initialization.

The base capability model supports:

- `sessions.stream` — bidirectional session streams
- `cancellation.cancelSession` — explicit session cancellation
- `progress.progress` — non-binding progress updates
- `manifest.getManifest` — runtime/agent manifest discovery
- `modeRegistry.listModes` — mode discovery
- `modeRegistry.listChanged` — registry change notifications
- `roots.listRoots` — disclosure of coordination roots/boundaries
- `roots.listChanged` — root change notifications
- `experimental` — explicitly non-standard features

## Compatibility model

MACP uses a layered compatibility model:

- **Protocol version** governs base runtime behavior.
- **Schema namespace** governs canonical Protobuf compatibility (for example `macp.v1`).
- **Mode version** governs semantic behavior within a session.
- **Configuration / policy version** governs runtime behavior that is bound to replay.

Major protocol version mismatches are not compatible. Minor versions are expected to be backward compatible. Unknown fields MUST be ignored to preserve forward compatibility.

## Repository highlights

- **Human-friendly schema entrypoints** live directly under `schemas/`.
- **Canonical versioned schemas** live under `schemas/proto/`.
- **Registries** live under `registries/` and are designed to evolve without destabilizing the core.
- **JSON schemas** cover the canonical JSON envelope mapping, agent manifests, and mode descriptors.

## Development

```bash
make validate
```

Validation checks JSON schemas/examples and compiles all versioned Protobuf definitions if local tooling is available.

## License

MIT.
