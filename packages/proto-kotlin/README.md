# macp-proto-kotlin

Kotlin DSL extensions for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol) protobuf bindings.

## Installation

### Gradle

```kotlin
dependencies {
    implementation("io.macp:macp-proto-kotlin:0.1.0")
}
```

This package depends on `io.macp:macp-proto` (the Java bindings) and adds Kotlin-idiomatic DSL extensions.

## Usage

```kotlin
import io.macp.v1.envelope
import io.macp.v1.EnvelopeKt
import io.macp.modes.decision.v1.proposalPayload
import io.macp.modes.proposal.v1.proposalPayload as negotiationProposal
```

### Packages included

- `io.macp.v1` - Envelope, core payloads, capabilities, policy descriptors, and gRPC stubs
- `io.macp.modes.decision.v1` - Decision Mode
- `io.macp.modes.proposal.v1` - Proposal Mode
- `io.macp.modes.task.v1` - Task Mode
- `io.macp.modes.handoff.v1` - Handoff Mode
- `io.macp.modes.quorum.v1` - Quorum Mode

## Versioning

This package version tracks the proto schema version from the spec repo.
