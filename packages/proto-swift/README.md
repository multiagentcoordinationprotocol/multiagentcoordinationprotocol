# MACPProto

Raw `.proto` files and Swift package for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

### Swift Package Manager

```swift
dependencies: [
    .package(url: "https://github.com/multiagentcoordinationprotocol/macp-proto-swift.git", from: "0.1.0"),
]
```

## Usage

```swift
import MACPProto
```

The package ships raw `.proto` files under `proto/` and uses SwiftProtobuf and gRPC Swift for code generation.

### Proto files included

- `macp/v1/envelope.proto` - Canonical Envelope, Ack, Error definitions
- `macp/v1/core.proto` - Core payloads, capabilities, gRPC service
- `macp/v1/policy.proto` - Governance policy descriptors and RPCs
- `macp/modes/decision/v1/decision.proto` - Decision Mode
- `macp/modes/proposal/v1/proposal.proto` - Proposal Mode
- `macp/modes/task/v1/task.proto` - Task Mode
- `macp/modes/handoff/v1/handoff.proto` - Handoff Mode
- `macp/modes/quorum/v1/quorum.proto` - Quorum Mode

## Versioning

This package uses git tags for versioning.
