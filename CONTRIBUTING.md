
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

## Normative RFCs

- **[RFC-MACP-0001 Core](rfcs/RFC-MACP-0001-core.md)** — base protocol, lifecycle, transport, registries, and compatibility model
- **[RFC-MACP-0002 Modes](rfcs/RFC-MACP-0002-modes.md)** — semantic extension model
- **[RFC-MACP-0003 Determinism](rfcs/RFC-MACP-0003-determinism.md)** — replay integrity and deterministic behavior
- **[RFC-MACP-0004 Security](rfcs/RFC-MACP-0004-security.md)** — threat model and security requirements
- **[RFC-MACP-0005 Discovery & Manifests](rfcs/RFC-MACP-0005-discovery-and-manifests.md)** — agent/runtime discovery, manifest schemas, well-known endpoints
- **[RFC-MACP-0006 Transport Bindings](rfcs/RFC-MACP-0006-transport-bindings.md)** — standard transport bindings (gRPC, HTTP, WebSocket, Message Bus)

## Community

All contributors must follow the Code of Conduct.
