# Multi-Agent Coordination Protocol (MACP)

**Version:** 1.0.0
**Status:** Draft
**License:** MIT

## Overview

The **Multi-Agent Coordination Protocol (MACP)** is an open standard for coordinating autonomous agents in multi-agent systems. MACP provides a structured framework for agent-to-agent communication, session management, and coordination lifecycle with strong guarantees for isolation, determinism, and replay integrity.

### The Core Principle

MACP introduces one strict invariant:

> **Binding, convergent coordination MUST occur inside explicit, bounded Coordination Sessions.**

All other interaction is treated as **ambient** and non-binding, carried via Signals.

## Why MACP?

Modern agent systems increasingly resemble **distributed ecosystems** rather than isolated model calls. Without explicit coordination boundaries, these ecosystems tend to accumulate:

- **Ambiguous authority** ("who decides?")
- **Implicit negotiation loops**
- **Recursive dependency graphs**
- **Non-reproducible outcomes**
- **"Infinite chat" failure modes** (unbounded conversation masquerading as coordination)

MACP addresses these failure modes with a minimal, structural separation between ambient interaction and coordinated convergence.

## Key Features

- **Mode-based coordination**: Flexible coordination patterns through extensible modes
- **Two-plane architecture**: Clear separation between ambient Signals and binding Sessions
- **Structured lifecycle**: Monotonic session states (`OPEN → RESOLVED | EXPIRED`)
- **Isolation guarantees**: Sessions are isolated from one another
- **Replay integrity**: Deterministic state transitions from identical message sequences
- **Version negotiation**: Built-in support for protocol evolution
- **Language-agnostic**: Protocol Buffers (canonical) and JSON support
- **Security-first**: Authentication, authorization, and replay protection requirements
- **Transport independence**: gRPC (normative) with optional REST support

## Quick Start

### Understanding the Architecture

MACP separates interaction into two distinct planes:

#### 1. Ambient Plane: Signals

Continuous, non-binding messages for telemetry, observations, and correlation:

```json
{
  "macp_version": "1.0",
  "mode": "macp.core.signal.v1",
  "message_type": "Signal",
  "message_id": "01HV0Q1Y8J1J9Q3C2A6JH0ZP3K",
  "session_id": "",
  "sender": "agent://telemetry.observer",
  "timestamp": "2026-03-01T20:24:00Z",
  "payload": {
    "signal_type": "observation.latency",
    "data": "AAECAwQ=",
    "confidence": 0.92
  }
}
```

**Signals MUST NOT affect session state or create binding outcomes.**

#### 2. Coordination Plane: Sessions

Explicit, bounded sessions where all binding coordination occurs:

```json
{
  "macp_version": "1.0",
  "mode": "macp.mode.decision.v1",
  "message_type": "SessionStart",
  "message_id": "01HV0Q2A9G4Z0FQ9C3Z9VZP8W1",
  "session_id": "01HV0Q2A8W0Y2XQ5N1R8Y2K9B3",
  "sender": "agent://orchestrator",
  "timestamp": "2026-03-01T20:24:01Z",
  "payload": {
    "intent": "Select a vendor for OCR pipeline",
    "participants": ["agent://orchestrator", "agent://security", "agent://finance"],
    "mode_version": "1.0.0",
    "configuration_version": "runtime-2026.03.01",
    "ttl_ms": 900000,
    "context": "eyJidWRnZXQiOiAxMDAwMH0="
  }
}
```

### Message Envelope Structure

Every MACP message uses a standard Envelope wrapper:

| Field | Type | Description |
|-------|------|-------------|
| `macp_version` | string | Protocol version (e.g., "1.0") |
| `mode` | string | Mode identifier (e.g., "macp.mode.decision.v1") |
| `message_type` | string | Message discriminator (e.g., "Signal", "SessionStart", "Commitment") |
| `message_id` | string | Globally unique identifier for idempotency |
| `session_id` | string | Empty for Signals, non-empty for session-scoped messages |
| `sender` | string | Agent identifier |
| `timestamp_unix_ms` | int64 | Informational timestamp (not used for ordering) |
| `payload` | bytes | Serialized payload (Core or Mode-defined) |

## Repository Structure

```
multiagentcoordinationprotocol/
├── .github/
│   └── workflows/
│       └── ci.yml                  # CI/CD validation workflow
├── rfcs/                           # Protocol specifications (RFC-style)
│   └── RFC-MACP-0001.md           # Core MACP specification (canonical)
├── schemas/
│   ├── proto/macp/v1/
│   │   └── macp.proto             # Canonical Protocol Buffers definitions
│   └── json/
│       └── macp-envelope.schema.json  # JSON Schema for envelope validation
├── examples/
│   ├── json/                       # Example MACP messages in JSON format
│   │   ├── signal.json
│   │   ├── session_start.json
│   │   ├── session_cancel.json
│   │   └── commitment.json
│   └── proto/                      # Binary protobuf examples
├── docs/                           # User-facing documentation
│   ├── architecture.md             # System design and core concepts
│   ├── lifecycle.md                # Session states and transitions
│   ├── security.md                 # Security model and considerations
│   ├── modes.md                    # How to define and implement coordination modes
│   └── determinism.md              # Deterministic execution guarantees
├── scripts/                        # Validation and development scripts
│   ├── validate-json-schema.sh    # Validate JSON Schema itself
│   ├── validate-json.sh           # Validate JSON examples
│   └── validate-proto.sh          # Compile and validate protobuf
├── Makefile                        # Development commands
├── buf.yaml                        # Buf linting configuration
├── buf.gen.yaml                    # Code generation configuration
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # MIT License
└── README.md                       # This file
```

## Documentation

### Core Documentation

- **[RFC-MACP-0001](rfcs/RFC-MACP-0001.md)** - The canonical protocol specification
- **[Architecture](docs/architecture.md)** - System design, two-plane architecture, and core concepts
- **[Lifecycle](docs/lifecycle.md)** - Session states, transitions, and termination conditions
- **[Security](docs/security.md)** - Security model, authentication, authorization, and threat mitigations
- **[Modes](docs/modes.md)** - How to define and implement coordination modes
- **[Determinism](docs/determinism.md)** - Replay integrity and deterministic execution guarantees

### Schemas

- **Protocol Buffers (Canonical)**: [schemas/proto/macp/v1/macp.proto](schemas/proto/macp/v1/macp.proto)
- **JSON Schema**: [schemas/json/macp-envelope.schema.json](schemas/json/macp-envelope.schema.json)

### Examples

- **[examples/json/](examples/json/)** - JSON-formatted example messages
  - [signal.json](examples/json/signal.json) - Ambient Signal example
  - [session_start.json](examples/json/session_start.json) - Session creation example
  - [commitment.json](examples/json/commitment.json) - Terminal commitment example
  - [session_cancel.json](examples/json/session_cancel.json) - Session cancellation example

## Core Concepts

### Coordination Sessions

A **Coordination Session** is a bounded context with:

- **Unique `session_id`**: Cryptographically strong identifier
- **Declared `mode`**: Defines coordination semantics
- **Declared participants**: Mode-defined interpretation
- **Bounded TTL**: Session lifetime limit (milliseconds)
- **Append-only message log**: Immutable history
- **Terminal outcome**: `RESOLVED` (successful) or `EXPIRED` (timeout/cancelled)

### Coordination Modes

A **Mode** defines coordination semantics within MACP's structural constraints:

- Allowed message types
- Participant rules and validation
- Termination conditions (what message ends the session)
- Determinism claims
- Commitment semantics (if any)
- Mode-specific payload schemas

**Modes MUST NOT violate MACP Core invariants.**

Example modes:
- `macp.mode.decision.v1` - Multi-agent decision making with binding commitments
- `macp.mode.quorum.v1` - Quorum-based approval workflows
- `macp.mode.negotiation.v1` - Iterative negotiation with consensus

### Core Message Types

| Message Type | Plane | Description |
|-------------|-------|-------------|
| `Signal` | Ambient | Non-binding informational message |
| `SessionStart` | Coordination | Creates a new coordination session |
| `SessionCancel` | Coordination | Runtime-emitted terminal annotation for cancellation |
| `Commitment` | Coordination | Mode-defined terminal message (recommended convention) |
| `SessionEnd` | Coordination | Mode-defined terminal without commitment semantics |

### Session Lifecycle

Sessions follow a monotonic state machine:

```
    SessionStart
         │
         ▼
      ┌──────┐
      │ OPEN │──────────────────┐
      └──────┘                  │
         │                      │
         │ Commitment           │ TTL Expired
         │ (Mode terminal)      │ or Cancelled
         │                      │
         ▼                      ▼
    ┌──────────┐          ┌──────────┐
    │ RESOLVED │          │ EXPIRED  │
    └──────────┘          └──────────┘
```

**No backwards transitions are permitted.**

### Structural Guarantees

MACP provides these invariants:

1. **Explicit Coordination Boundaries**: Coordination MUST start via `SessionStart`
2. **Isolation**: Sessions are isolated; cross-session ordering is not guaranteed
3. **Monotonic Lifecycle**: Sessions transition monotonically: `OPEN → (RESOLVED | EXPIRED)`
4. **Append-only History**: Accepted messages are immutable
5. **Replay Integrity**: Same message sequence + same versions = same state transitions
6. **Idempotency**: Duplicate `message_id` within session produces no side effects

## Development and Validation

### Quick Start: Local Development

MACP provides a comprehensive set of tools for local development and validation:

```bash
# Validate everything (JSON Schema, examples, protobuf)
make validate

# Validate just the JSON Schema itself (meta-validation)
make json-schema-validate

# Validate JSON examples against schema
make json-validate

# Lint protobuf files
make proto-lint

# Compile protobuf (validation)
make proto-compile

# Generate code from protobuf (Go, Python, TypeScript, JavaScript)
make proto-gen

# Clean generated files
make clean

# Install required development tools
make install-tools
```

### Development Tools

This repository includes:

- **Makefile**: Convenient commands for validation and code generation
- **buf**: Industry-standard protobuf linting and code generation
- **Validation scripts** (`scripts/`):
  - `validate-json-schema.sh` - Validates the JSON Schema itself (meta-validation)
  - `validate-json.sh` - Validates JSON examples against the schema
  - `validate-proto.sh` - Compiles and validates protobuf schemas
- **CI/CD**: Automated validation via GitHub Actions

### Working with Schemas

#### Protocol Buffers (Canonical Wire Format)

The protobuf schema at [schemas/proto/macp/v1/macp.proto](schemas/proto/macp/v1/macp.proto) is the **canonical** definition.

**Using Makefile:**
```bash
make proto-compile  # Validate compilation
make proto-lint     # Lint with buf
make proto-gen      # Generate code
```

**Manual validation:**
```bash
protoc --proto_path=schemas/proto \
       --descriptor_set_out=/dev/null \
       schemas/proto/macp/v1/macp.proto
```

#### JSON Schema Validation

The JSON schema at [schemas/json/macp-envelope.schema.json](schemas/json/macp-envelope.schema.json) validates JSON-encoded envelopes.

**Using Makefile:**
```bash
make json-schema-validate  # Validate the schema itself
make json-validate         # Validate examples against schema
```

**Manual validation:**
```bash
# Install ajv-cli
npm install -g ajv-cli

# Validate the schema itself (meta-validation)
ajv compile -s schemas/json/macp-envelope.schema.json --spec=draft2020

# Validate examples against schema
ajv validate -s schemas/json/macp-envelope.schema.json \
             -d "examples/json/*.json" --spec=draft2020
```

### Code Generation

Generate protobuf code for multiple languages:

```bash
make proto-gen
```

Generated code is placed in `generated/` (gitignored):
- `generated/go/` - Go packages
- `generated/python/` - Python modules
- `generated/js/` - JavaScript (CommonJS)

**Buf Configuration:**
- `buf.yaml` - Linting rules and breaking change detection
- `buf.gen.yaml` - Code generation configuration

### Continuous Integration

GitHub Actions automatically validates:

1. **JSON Schema meta-validation** - Ensures the schema itself is valid
2. **JSON examples validation** - Validates all examples against the schema
3. **Protobuf compilation** - Ensures protobuf schemas compile
4. **Protobuf linting** - Lints with buf for best practices
5. **Breaking change detection** - Checks for breaking changes in PRs
6. **Code generation** - Verifies schemas can generate code for multiple languages

**CI runs on:**
- All pull requests
- Pushes to `main` branch

**View workflows:** [.github/workflows/ci.yml](.github/workflows/ci.yml)

## Transport

### Normative Transport: gRPC

MACP's normative transport is **gRPC over HTTP/2** with bidirectional streaming support.

**Canonical Service Definition** (see [RFC-MACP-0001 Section 9](rfcs/RFC-MACP-0001.md#9-transport-requirements)):
```protobuf
service MACPService {
  rpc SendMessage(Envelope) returns (Ack);
  rpc StreamSession(stream Envelope) returns (stream Envelope);
  rpc GetSession(SessionQuery) returns (SessionMetadata);
  rpc CancelSession(CancelSessionRequest) returns (Ack);
}
```

### Optional: REST Transport

Implementations MAY expose REST endpoints using:
- Media type: `application/macp+json`
- Streaming via Server-Sent Events (SSE) or WebSockets

## Security Considerations

MACP requires:

- **Transport Security**: TLS for all deployments
- **Authentication**: JWT, mTLS, OAuth2/OIDC, or equivalent
- **Authorization**: Validate sender authorization before processing session-scoped messages
- **Replay Protection**: `message_id` deduplication enforcement
- **Session ID Strength**: Cryptographically strong, unguessable identifiers
- **DoS Mitigation**: Rate limiting, admission control, payload size limits, backpressure

See [Security Documentation](docs/security.md) for detailed requirements.

## Versioning and Compatibility

### Protocol Versioning

MACP uses semantic versioning in `macp_version`:
- **Major version mismatch**: MUST reject
- **Minor version difference**: SHOULD be backward compatible

### Mode Versioning

Modes MUST include explicit version identifiers. Agents MUST reject unsupported Mode versions deterministically.

### Forward Compatibility

- Unknown Protobuf fields MUST be ignored
- Unknown JSON properties MUST be ignored

## RFCs and Protocol Changes

Protocol changes require an RFC (Request for Comments):

1. Create `rfcs/RFC-MACP-XXXX.md` (sequential numbering)
2. Follow structure in [RFC-MACP-0001](rfcs/RFC-MACP-0001.md)
3. Submit as pull request for community review
4. Address feedback and iterate
5. RFCs are accepted through consensus

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full RFC process.

## Getting Started with Development

### Prerequisites

To work with this repository, you'll need:

1. **Protocol Buffer Compiler (protoc)**
   - macOS: `brew install protobuf`
   - Ubuntu: `sudo apt-get install protobuf-compiler`
   - [Other platforms](https://protobuf.dev/downloads/)

2. **buf** (Protocol Buffer tooling)
   - macOS: `brew install bufbuild/buf/buf`
   - [Other platforms](https://buf.build/docs/installation)

3. **Node.js and npm** (for JSON Schema validation)
   - [Download Node.js](https://nodejs.org/)
   - Then: `npm install -g ajv-cli`

4. **Go** (optional, for Go code generation)
   - [Download Go](https://go.dev/dl/)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/macp.git
cd macp

# Install development tools (macOS/Linux)
make install-tools

# Validate everything
make validate

# Generate code (optional)
make proto-gen
```

### Development Workflow

1. **Make changes** to schemas, documentation, or examples
2. **Validate locally**: `make validate`
3. **Fix any issues** reported by validation
4. **Commit and push**: CI will run the same validations
5. **Submit PR**: Breaking change detection runs automatically

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Types of contributions
- RFC process for protocol changes
- Schema compatibility requirements
- Technical requirements
- Community guidelines

**Key requirement:** All changes MUST preserve MACP Core invariants.

## Relationship to Other Protocols

### Model Context Protocol (MCP)

- **MCP**: Standardizes how AI applications connect to external context and capabilities (tools, prompts, resources)
- **MACP**: Coordinates when and whether agents are allowed to use those capabilities
- **Integration**: A Mode may coordinate MCP tool invocations within MACP sessions

### Agent Communication Protocol (ACP)

- **ACP**: Demonstrates practical patterns for agent discovery, manifests, and REST + streaming
- **MACP**: Borrows discovery/manifest concepts while focusing on session-bounded convergence
- **Difference**: MACP emphasizes structural coordination; ACP emphasizes run execution APIs

## Use Cases

MACP supports diverse coordination patterns:

- **Multi-agent decision making**: Collect proposals, vote, emit binding commitment
- **Quorum-based approvals**: Require N-of-M agent approvals for actions
- **Negotiation and consensus**: Iterative refinement until convergence
- **Coordinated tool execution**: Gate tool invocations through multi-agent review
- **Hierarchical orchestration**: Nested coordination with depth/hop limits
- **Audit and compliance**: Replay sessions to verify decision provenance

## Implementation Status

This repository contains the **protocol specification only**. Reference implementations and libraries are tracked separately:

- **Go**: (Coming soon)
- **Python**: (Coming soon)
- **TypeScript**: (Coming soon)
- **Rust**: (Coming soon)

## Community and Support

- **GitHub Issues**: Report bugs or suggest features
- **GitHub Discussions**: Ask questions and share ideas
- **RFC Process**: Propose protocol changes via RFCs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

MACP draws inspiration from:

- **Model Context Protocol (MCP)**: Context and capability patterns
- **Agent Communication Protocol (ACP)**: Discovery and manifest patterns
- **gRPC**: Bidirectional streaming and transport semantics
- **IETF RFC process**: Specification rigor and versioning

---

**Version:** 1.0.0 (Draft)
**Last Updated:** 2026-03-01
**Status:** Standards Track

For the complete specification, see [RFC-MACP-0001](rfcs/RFC-MACP-0001.md).
