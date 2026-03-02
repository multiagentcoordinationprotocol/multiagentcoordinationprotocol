# Multi-Agent Coordination Protocol (MACP)

**Version:** 1.0.0
**Status:** Draft

## Overview

The Multi-Agent Coordination Protocol (MACP) is an open standard for coordinating autonomous agents in multi-agent systems. MACP provides a structured framework for agent-to-agent communication, session management, and coordination lifecycle.

## Key Features

- **Mode-based coordination**: Flexible coordination patterns through extensible modes
- **Structured lifecycle**: Clear session states and transitions
- **Version negotiation**: Built-in support for protocol evolution
- **Language-agnostic**: Protocol Buffers and JSON support
- **Security-first**: Determinism guarantees and security considerations built-in

## Quick Start

See the [examples/](examples/) directory for sample messages and usage patterns.

## Documentation

- [Architecture](docs/architecture.md) - System design and core concepts
- [Lifecycle](docs/lifecycle.md) - Session states and transitions
- [Security](docs/security.md) - Security model and considerations
- [Modes](docs/modes.md) - How to define and implement coordination modes
- [Determinism](docs/determinism.md) - Deterministic execution guarantees

## Schemas

- **Protocol Buffers**: [schemas/proto/macp/v1/macp.proto](schemas/proto/macp/v1/macp.proto)
- **JSON Schema**: [schemas/json/macp-envelope.schema.json](schemas/json/macp-envelope.schema.json)

## RFCs

Protocol changes and proposals are tracked through RFCs in the [rfcs/](rfcs/) directory.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Governance

See [GOVERNANCE.md](GOVERNANCE.md) for information about project governance and decision-making.

## Versioning

See [VERSIONING.md](VERSIONING.md) for details on protocol and mode versioning.

## License

See [LICENSE](LICENSE) for license information.

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.
