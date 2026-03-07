# MACP Capability Registry

This registry defines standard capability identifiers used by MACP agents and runtimes.

## Format

Capability identifiers use the pattern:

macp.<category>.<name>.v<version>

Example:

macp.signal.v1
macp.mode.decision.v1
macp.transport.grpc.v1

## Standard Capabilities

| Identifier | Description | Status | Reference |
|------------|-------------|--------|-----------|
| macp.signal.v1 | Ambient signal messaging | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| macp.session.v1 | Coordination session support | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| macp.replay.v1 | Deterministic replay support | permanent | [RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md) |
| macp.discovery.v1 | Manifest discovery support | permanent | [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md) |
| macp.transport.grpc.v1 | gRPC transport | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.http.v1 | HTTP transport | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.websocket.v1 | WebSocket transport | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |

## Extension Policy

New capabilities may be registered through:

- MACP working group review
- documented community proposal
- experimental namespace

Example experimental identifier:

com.example.capability.custom.v1
