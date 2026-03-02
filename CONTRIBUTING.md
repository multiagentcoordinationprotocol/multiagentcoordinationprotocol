
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

## Technical Requirements

- Protobuf MUST compile successfully.
- JSON examples MUST validate against the JSON Schema.
- Backward compatibility MUST be addressed explicitly.
- Mode extensions MUST NOT violate MACP Core invariants.

## Community

All contributors must follow the Code of Conduct.
