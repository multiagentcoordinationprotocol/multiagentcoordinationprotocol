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
| macp.transport.messagebus.v1 | Message bus transport | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |

## Capability Registry vs. Capability Objects

The **Capability Registry** (this document) lists high-level feature identifiers used in agent manifests and discovery endpoints (see [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md)). These identifiers follow the `macp.<category>.<name>.v<version>` pattern and declare what an agent or runtime supports at the advertisement level.

The **Capability Objects** defined in [RFC-MACP-0001 Section 4.2](../rfcs/RFC-MACP-0001-core.md) are structured protobuf fields (e.g., `sessions.stream`, `cancellation.cancelSession`) exchanged during `InitializeRequest`/`InitializeResponse` negotiation. These represent fine-grained feature toggles negotiated at connection time.

Both systems serve complementary purposes:
- **Registry identifiers** appear in manifests and discovery responses to advertise broad capabilities before a connection is established.
- **Protobuf capability fields** are exchanged during the `Initialize` handshake to negotiate specific features for a given connection.

## Extension Policy

New capabilities may be registered through:

- MACP working group review
- documented community proposal
- experimental namespace

Example experimental identifier:

com.example.capability.custom.v1
