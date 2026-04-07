# Macp.Proto

Pre-generated C# protobuf and gRPC bindings for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

```bash
dotnet add package Macp.Proto
```

## Usage

```csharp
using Macp.V1;
using Macp.Modes.Decision.V1;
using Macp.Modes.Proposal.V1;
using Macp.Modes.Task.V1;
using Macp.Modes.Handoff.V1;
using Macp.Modes.Quorum.V1;
```

### Namespaces included

- `Macp.V1` - Envelope, core payloads, capabilities, policy descriptors, and gRPC service
- `Macp.Modes.Decision.V1` - Decision Mode
- `Macp.Modes.Proposal.V1` - Proposal Mode
- `Macp.Modes.Task.V1` - Task Mode
- `Macp.Modes.Handoff.V1` - Handoff Mode
- `Macp.Modes.Quorum.V1` - Quorum Mode

## Versioning

This package version tracks the proto schema version from the spec repo.
