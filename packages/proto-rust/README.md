# macp-proto

Raw `.proto` files for the [Multi-Agent Coordination Protocol (MACP)](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol), packaged as a Rust crate.

## Installation

```toml
[dependencies]
macp-proto = "0.1.0"
```

## Usage

This crate ships raw `.proto` files under `proto/`. Use them with `tonic-build` or `prost-build` in your `build.rs`:

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .compile_protos(
            &[
                "proto/macp/v1/envelope.proto",
                "proto/macp/v1/core.proto",
                "proto/macp/v1/policy.proto",
            ],
            &["proto"],
        )?;
    Ok(())
}
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
