
# Contributing to MACP

Thank you for contributing to the Multi-Agent Coordination Protocol (MACP).

MACP is a structural coordination standard. All changes MUST preserve core invariants:

- Explicit session boundaries
- Monotonic lifecycle (OPEN → RESOLVED | EXPIRED)
- Isolation between sessions
- Append-only history
- Idempotent message acceptance

## Types of Contributions

- Specification clarifications
- RFC updates or new RFCs
- Schema updates (Protobuf / JSON)
- Examples and tooling improvements
- CI and validation enhancements

## Submitting Changes

### Minor Clarifications
Submit a pull request directly against the relevant document.

### Substantive Changes
1. Open an issue using the RFC proposal template.
2. Discuss motivation and compatibility.
3. Submit a PR updating the relevant RFC.

Breaking changes require:
- Major version bump
- Migration notes
- Explicit compatibility statement

## Registry Additions

To add an entry to a registry (capabilities, error codes, media types, modes, or transports), submit a PR that adds a row to the relevant table in `registries/`. Each entry MUST include a `Status` value (see `registries/README.md` for valid statuses). New identifiers MUST NOT conflict with existing entries.

## RFC Proposals

To propose a new RFC:

1. Open an issue using the [RFC proposal template](.github/ISSUE_TEMPLATE/rfc_proposal.yml).
2. After discussion, create `rfcs/RFC-MACP-XXXX-<topic>.md` (sequential numbering) following the structure of existing RFCs.
3. Submit a PR referencing the issue; RFCs are accepted through community consensus.

## Technical Requirements

- Protobuf MUST compile successfully.
- JSON examples MUST validate against the JSON Schema.
- Backward compatibility MUST be addressed explicitly.
- Mode extensions MUST NOT violate MACP Core invariants.

## Proto Package Publishing

Proto definitions are published as versioned packages for downstream consumers:

| Package | Language | Registry |
|---------|----------|----------|
| `@macp/proto` | TypeScript / Node.js | npm (GitHub Packages) |
| `macp-proto` | Python | PyPI |
| `macp-proto` | Rust | Crate (git tag) |
| `macp-proto-go` | Go | Go module proxy (git tag) |
| `io.macp:macp-proto` | Java | Maven (GitHub Packages) |
| `io.macp:macp-proto-kotlin` | Kotlin | Maven (GitHub Packages) |
| `Macp.Proto` | C# | NuGet (GitHub Packages) |
| `MACPProto` | Swift | Swift Package (git tag) |

### Releasing a new proto version

1. Merge proto schema changes to `main` (the BSR push happens automatically).
2. Tag the commit: `git tag proto-v0.X.0 && git push origin proto-v0.X.0`
3. The `publish-proto-packages.yml` workflow publishes all three packages.
4. Downstream projects upgrade by bumping the dependency version in their manifest.

Each downstream project pins a specific proto version and upgrades on its own schedule.
Proto changes no longer block unrelated PRs in downstream repos.

## Normative RFCs

- **[RFC-MACP-0001 Core](rfcs/RFC-MACP-0001-core.md)** — base protocol, lifecycle, transport, registries, and compatibility model
- **[RFC-MACP-0002 Modes](rfcs/RFC-MACP-0002-modes.md)** — semantic extension model
- **[RFC-MACP-0003 Determinism](rfcs/RFC-MACP-0003-determinism.md)** — replay integrity and deterministic behavior
- **[RFC-MACP-0004 Security](rfcs/RFC-MACP-0004-security.md)** — threat model and security requirements
- **[RFC-MACP-0005 Discovery & Manifests](rfcs/RFC-MACP-0005-discovery-and-manifests.md)** — agent/runtime discovery, manifest schemas, well-known endpoints
- **[RFC-MACP-0006 Transport Bindings](rfcs/RFC-MACP-0006-transport-bindings.md)** — standard transport bindings (gRPC, HTTP, WebSocket, Message Bus)
- **[RFC-MACP-0007 Decision Mode](rfcs/RFC-MACP-0007-decision-mode.md)** — structured decision-making with proposals, evaluations, and votes
- **[RFC-MACP-0008 Proposal Mode](rfcs/RFC-MACP-0008-proposal-mode.md)** — offer/counteroffer negotiation
- **[RFC-MACP-0009 Task Mode](rfcs/RFC-MACP-0009-task-mode.md)** — bounded task delegation
- **[RFC-MACP-0010 Handoff Mode](rfcs/RFC-MACP-0010-handoff-mode.md)** — responsibility transfer
- **[RFC-MACP-0011 Quorum Mode](rfcs/RFC-MACP-0011-quorum-mode.md)** — threshold approval/rejection
- **[RFC-MACP-0012 Policy](rfcs/RFC-MACP-0012-policy.md)** — governance policy framework for declarative, replay-safe session governance

## Community

All contributors must follow the Code of Conduct.
