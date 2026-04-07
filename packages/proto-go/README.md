# macp-proto-go

Pre-generated Go protobuf and gRPC bindings for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

```bash
go get github.com/multiagentcoordinationprotocol/macp-proto-go
```

## Usage

```go
import (
    corev1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/v1"
    decisionv1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/modes/decision/v1"
    proposalv1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/modes/proposal/v1"
    taskv1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/modes/task/v1"
    handoffv1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/modes/handoff/v1"
    quorumv1 "github.com/multiagentcoordinationprotocol/macp-proto-go/macp/modes/quorum/v1"
)
```

### Packages included

- `macp/v1` - Envelope, core payloads, capabilities, policy descriptors, and gRPC service
- `macp/modes/decision/v1` - Decision Mode
- `macp/modes/proposal/v1` - Proposal Mode
- `macp/modes/task/v1` - Task Mode
- `macp/modes/handoff/v1` - Handoff Mode
- `macp/modes/quorum/v1` - Quorum Mode

## Versioning

This module uses git tags for versioning. Pin to a specific version
(e.g., `go get ...@v0.1.0`) to avoid unexpected breaking changes.
