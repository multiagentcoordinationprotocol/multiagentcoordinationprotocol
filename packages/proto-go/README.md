# Go bindings for MACP

Go users install the protobuf and gRPC bindings that the
[Buf Schema Registry](https://buf.build/multiagentcoordinationprotocol/macp)
generates for the canonical protos. Every push to `main` pushes the module there
(see `.github/workflows/ci.yml`), and Buf regenerates the Go packages on each push.

## Installation

```bash
go get buf.build/gen/go/multiagentcoordinationprotocol/macp/protocolbuffers/go
go get buf.build/gen/go/multiagentcoordinationprotocol/macp/grpc/go
```

## Usage

```go
import (
    corev1 "buf.build/gen/go/multiagentcoordinationprotocol/macp/protocolbuffers/go/macp/v1"
    "buf.build/gen/go/multiagentcoordinationprotocol/macp/grpc/go/macp/v1/macpv1grpc"
    decisionv1 "buf.build/gen/go/multiagentcoordinationprotocol/macp/protocolbuffers/go/macp/modes/decision/v1"
)
```

The other modes follow the same pattern: `macp/modes/{proposal,task,handoff,quorum,multi_round}/v1`.

## Versioning

Buf versions each package as `<plugin version>-<commit timestamp>-<commit>.<n>`. To
pin a protocol commit, run `go get <package>@<version>`, choosing a version from
`go list -m -versions <package>`.

## This directory

Nothing here is published. `make gen-go` and CI generate Go code into this
directory only to check that the protos compile for Go. The module path in
`go.mod` names a repository that does not exist, which is why tags of this
directory could never be installed (issue #206).
