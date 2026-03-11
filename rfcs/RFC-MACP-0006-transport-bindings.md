
# RFC-MACP-0006: Transport Bindings
Status: Draft
Category: Standards Track
Author: MACP Working Group

## 1. Introduction
MACP is transport-agnostic. This document defines standard transport bindings for MACP messages.

Normative transport: gRPC over HTTP/2.

See [RFC-MACP-0001 Section 9](RFC-MACP-0001-core.md#9-transport-requirements) for core transport requirements. For discovery of transport endpoints in agent manifests, see [RFC-MACP-0005](RFC-MACP-0005-discovery-and-manifests.md).

Registered transport identifiers are listed in [`registries/transports.md`](../registries/transports.md).

## 2. Envelope Transmission
All transports MUST carry MACP Envelopes defined in RFC-MACP-0001.

## 3. gRPC Binding (Normative)

Conformant implementations MUST support the gRPC binding.

The canonical gRPC service is defined in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto). The proto file is the authoritative source; the listing below is reproduced for convenience.

```protobuf
service MACPRuntimeService {
  rpc Initialize(InitializeRequest) returns (InitializeResponse);
  rpc Send(SendRequest) returns (SendResponse);
  rpc StreamSession(stream StreamSessionRequest) returns (stream StreamSessionResponse);
  rpc GetSession(GetSessionRequest) returns (GetSessionResponse);
  rpc CancelSession(CancelSessionRequest) returns (CancelSessionResponse);
  rpc GetManifest(GetManifestRequest) returns (GetManifestResponse);
  rpc ListModes(ListModesRequest) returns (ListModesResponse);
  rpc WatchModeRegistry(WatchModeRegistryRequest) returns (stream WatchModeRegistryResponse);
  rpc ListRoots(ListRootsRequest) returns (ListRootsResponse);
  rpc WatchRoots(WatchRootsRequest) returns (stream WatchRootsResponse);
}
```

Characteristics:
- ordered streaming
- backpressure via HTTP/2
- bidirectional coordination

## 4. HTTP Binding

The HTTP binding is OPTIONAL. Implementations providing it MUST preserve Envelope semantics and MUST map error codes to HTTP status codes per the [error-codes registry](../registries/error-codes.md).

Example endpoints:

```
POST /macp/envelope
POST /macp/session/start
GET  /macp/session/{id}
POST /macp/session/{id}/cancel
```

## 5. WebSocket Binding

The WebSocket binding is OPTIONAL. Implementations providing it MUST frame each Envelope as a single WebSocket message.

Example message:

```json
{
  "type": "envelope",
  "payload": {}
}
```

## 6. Message Bus Binding

The message bus binding is OPTIONAL. Implementations providing it MUST preserve per-session message ordering.

Example topics:

```
macp.signals
macp.sessions.{session_id}
```

Possible systems:
Kafka
NATS
RabbitMQ

## 7. Transport Selection

Implementations MUST support at least the gRPC binding. Additional transports are OPTIONAL.

gRPC -- high throughput coordination
HTTP -- simple integrations
WebSocket -- interactive coordination
Message Bus -- distributed systems

## 8. Security

All transports MUST use TLS.
Authentication requirements follow RFC-MACP-0004.
