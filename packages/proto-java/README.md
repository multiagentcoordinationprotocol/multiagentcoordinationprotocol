# macp-proto (Java)

Pre-generated Java protobuf and gRPC bindings for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

### Gradle

```kotlin
dependencies {
    implementation("io.macp:macp-proto:0.1.0")
}
```

### Maven

```xml
<dependency>
    <groupId>io.macp</groupId>
    <artifactId>macp-proto</artifactId>
    <version>0.1.0</version>
</dependency>
```

## Usage

```java
import io.macp.v1.Envelope;
import io.macp.v1.Core;
import io.macp.v1.Policy;
import io.macp.modes.decision.v1.Decision;
import io.macp.modes.proposal.v1.Proposal;
import io.macp.modes.task.v1.Task;
import io.macp.modes.handoff.v1.Handoff;
import io.macp.modes.quorum.v1.Quorum;
```

### Packages included

- `io.macp.v1` - Envelope, core payloads, capabilities, policy descriptors, and gRPC service
- `io.macp.modes.decision.v1` - Decision Mode
- `io.macp.modes.proposal.v1` - Proposal Mode
- `io.macp.modes.task.v1` - Task Mode
- `io.macp.modes.handoff.v1` - Handoff Mode
- `io.macp.modes.quorum.v1` - Quorum Mode

## Versioning

This package version tracks the proto schema version from the spec repo.
