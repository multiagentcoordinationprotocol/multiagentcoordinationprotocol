
# MACP Transport Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) | [registries/transports.md](../registries/transports.md) | [core.proto](../schemas/proto/macp/v1/core.proto)

MACP supports multiple transport layers depending on deployment architecture.

## gRPC (Recommended)

Best for:
- high throughput coordination
- persistent streaming sessions
- microservice environments

Advantages:
- efficient binary transport
- streaming support
- strong typing via protobuf

## HTTP

Best for:
- simple integrations
- environments where gRPC is restricted

## WebSockets

Best for:
- interactive coordination
- browser environments

## Message Buses

Best for:
- large distributed systems
- asynchronous coordination
- event-driven architectures

Examples:
Kafka
NATS
RabbitMQ
