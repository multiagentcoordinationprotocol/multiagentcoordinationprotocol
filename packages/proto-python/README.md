# macp-proto

Pre-generated Python protobuf and gRPC bindings for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

```bash
pip install macp-proto
```

## Usage

```python
from macp.v1 import core_pb2, envelope_pb2, policy_pb2
from macp.modes.decision.v1 import decision_pb2
from macp.modes.proposal.v1 import proposal_pb2
from macp.modes.task.v1 import task_pb2
from macp.modes.handoff.v1 import handoff_pb2
from macp.modes.quorum.v1 import quorum_pb2
```

## Versioning

This package version tracks the proto schema version from the spec repo.
A release that adds, removes or changes a service RPC bumps the minor version (0.1.x to 0.2.0).
If you implement a gRPC servicer and want no new RPCs, pin `<0.2.0` instead of the range below. See
[VERSIONING.md §8](../../VERSIONING.md#8-published-proto-packages).
Pin to a specific version range (e.g., `macp-proto>=0.1.0,<1.0.0`) to avoid
unexpected breaking changes when new proto versions are released.
