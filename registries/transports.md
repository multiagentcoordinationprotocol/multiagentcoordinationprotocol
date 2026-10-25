# MACP Transport Registry

Defines standardized transport bindings for MACP.

## Identifier Format

macp.transport.<name>.v<version>

## Standard Transports

| Transport | Description | Status | Reference |
|----------|-------------|--------|-----------|
| macp.transport.grpc.v1 | gRPC over HTTP/2 | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.http.v1 | HTTP JSON API | provisional | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.websocket.v1 | WebSocket streaming | provisional | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.messagebus.v1 | Message bus (Kafka/NATS/RabbitMQ) | provisional | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| macp.transport.a2a.v1 | A2A 1.0 extension binding (Envelope carried as an A2A Part) | provisional | [RFC-MACP-0014](../rfcs/RFC-MACP-0014-a2a-binding.md) |

Only gRPC is `permanent`. The HTTP, WebSocket and message-bus bindings are specified in RFC-MACP-0006, and the A2A binding in RFC-MACP-0014, but all four are `provisional`: the reference runtime implements only gRPC, and no implementation has yet shown that those bindings interoperate. A binding becomes `permanent` once two independent implementations do. Status terms are defined in [README.md](README.md).

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
A2A: agents that already speak A2A and want to join MACP sessions without a second transport
