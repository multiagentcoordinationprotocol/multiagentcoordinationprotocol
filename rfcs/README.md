# MACP RFC Set

The MACP standard is intentionally split.

- **RFC-MACP-0001 Core** - base protocol, lifecycle, transport, registries, and compatibility model
- **RFC-MACP-0002 Modes** - semantic extension model and main-repo mode boundary
- **RFC-MACP-0003 Determinism** - replay integrity and deterministic behavior
- **RFC-MACP-0004 Security** - threat model and security requirements
- **RFC-MACP-0005 Discovery & Manifests** - agent/runtime discovery, manifest schemas, well-known endpoints
- **RFC-MACP-0006 Transport Bindings** - standard transport bindings for MACP messages (gRPC, HTTP, WebSocket, Message Bus)
- **RFC-MACP-0007 Decision Mode** - proposals, evaluations, votes, and a single binding outcome
- **RFC-MACP-0008 Proposal Mode** - proposal and counterproposal negotiation
- **RFC-MACP-0009 Task Mode** - bounded task delegation
- **RFC-MACP-0010 Handoff Mode** - responsibility transfer between participants
- **RFC-MACP-0011 Quorum Mode** - threshold approval and rejection

### Companion Content

- **`registries/`** - initial registry definitions for capabilities, error codes, media types, transports, and standard mode identifiers
- **`schemas/`** - canonical Protobuf definitions and human-friendly entrypoints for Core and standard modes
- **`examples/`** - discovery examples and one transcript for each standard mode in the main repo
