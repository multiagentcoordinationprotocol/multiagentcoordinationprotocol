# MACP Transport Registry

Defines standardized transport bindings for MACP.

## Identifier Format

macp.transport.<name>.v<version>

## Standard Transports

| Transport | Description | Status | Reference |
|----------|-------------|--------|-----------|
| macp.transport.grpc.v1 | gRPC over HTTP/2 | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.http.v1 | HTTP JSON API | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.websocket.v1 | WebSocket streaming | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.messagebus.v1 | Message bus (Kafka/NATS/RabbitMQ) | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |

## Transport Requirements

All transports MUST:

- support secure transport (TLS)
- carry MACP Envelope messages
- preserve ordering within sessions

## Transport Selection Guidance

gRPC: high-performance internal coordination  
HTTP: simple integrations  
WebSockets: interactive environments  
Message buses: large distributed systems
