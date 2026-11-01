# @multiagentcoordinationprotocol/proto

Raw `.proto` files for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol).

## Installation

```bash
npm install @multiagentcoordinationprotocol/proto
```

## Usage

This package ships raw `.proto` files under `proto/`. Use them with your preferred protobuf toolchain (e.g., `protoc`, `buf`, `protobuf.js`).

```js
const { resolve } = require('path');
const protoDir = resolve(require.resolve('@multiagentcoordinationprotocol/proto'), '..', 'proto');
// protoDir now points to the directory containing MACP .proto files
```

The package also exports the proto directory path:

```js
const { PROTO_DIR } = require('@multiagentcoordinationprotocol/proto');
```

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

This package version tracks the proto schema version from the spec repo.
A release that adds, removes or changes a service RPC bumps the minor version (0.1.x to 0.2.0),
so a caret requirement on 0.1.x never picks up a new RPC. See
[VERSIONING.md §8](../../VERSIONING.md#8-published-proto-packages).
Pin to a specific version range (e.g., `@multiagentcoordinationprotocol/proto@^0.1.0`) to avoid
unexpected breaking changes when new proto versions are released.
