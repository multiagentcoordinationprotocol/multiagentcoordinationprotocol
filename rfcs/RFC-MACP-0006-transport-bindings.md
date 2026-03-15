
# RFC-MACP-0006: Transport Bindings
Status: Draft
Category: Standards Track
Author: MACP Working Group

## 1. Introduction

MACP is transport-agnostic. This document defines standard transport bindings for MACP messages.

Normative transport: gRPC over HTTP/2.

See [RFC-MACP-0001 Section 9](RFC-MACP-0001-core.md#9-transport-requirements) for core transport requirements. For discovery of transport endpoints in manifests, see [RFC-MACP-0005](RFC-MACP-0005-discovery-and-manifests.md).

Registered transport identifiers are listed in [`registries/transports.md`](../registries/transports.md).

## 2. Envelope Transmission

All transports MUST carry canonical MACP Envelopes defined in RFC-MACP-0001.

Transport bindings MUST preserve:

- within-session acceptance order,
- idempotency semantics,
- session isolation,
- structured error signaling appropriate to the transport.

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

### 3.1 `Send`

`Send` is the authoritative per-message request/ack surface.

A compliant runtime MUST use `SendResponse.ack` for standard per-message acceptance or rejection signaling.

### 3.2 `StreamSession`

`StreamSession` is an optional interactive envelope stream advertised by `sessions.stream`.

A runtime that advertises `sessions.stream = true` MUST implement `StreamSession` with these semantics:

- the stream carries canonical MACP Envelopes only,
- once the stream is bound to a non-empty `session_id`, all subsequent session-scoped envelopes on that stream MUST use the same `session_id`,
- accepted envelopes emitted by the server MUST appear in authoritative acceptance order for that session,
- the stream MUST NOT invent ad-hoc pseudo-envelopes whose payloads encode JSON-only acks or errors unless an explicitly negotiated experimental capability allows it.

`StreamSession` is **not** the standard replacement for unary `Send` acknowledgements. Clients that require standard per-message negative acknowledgements SHOULD use `Send`.

A runtime MAY echo back accepted client-submitted envelopes on the stream as part of the authoritative accepted sequence.

When a transport-level or stream-fatal error occurs, the runtime SHOULD use native gRPC stream termination semantics.

### 3.3 `WatchModeRegistry` and `WatchRoots`

These watch streams are optional discovery hints.

A runtime MUST advertise `mode_registry.list_changed = true` before `WatchModeRegistry` can be assumed interoperable.
A runtime MUST advertise `roots.list_changed = true` before `WatchRoots` can be assumed interoperable.

A watch notification indicates that the corresponding registry or roots view may have changed. Clients SHOULD re-query the full surface (`ListModes` or `ListRoots`) after receiving a change notification.

## 4. HTTP Binding

The HTTP binding is OPTIONAL. Implementations providing it MUST preserve Envelope semantics and MUST map error codes to HTTP status codes per the [error-codes registry](../registries/error-codes.md).

Example endpoints:

```text
POST /macp/envelope
POST /macp/session/start
GET  /macp/session/{id}
POST /macp/session/{id}/cancel
GET  /.well-known/macp.json
```

## 5. WebSocket Binding

The WebSocket binding is OPTIONAL. Implementations providing it MUST frame each Envelope as a single WebSocket message and MUST preserve per-session ordering.

## 6. Message Bus Binding

The message bus binding is OPTIONAL. Implementations providing it MUST preserve per-session message ordering and MUST define how authoritative acceptance is established.

Example topics:

```text
macp.signals
macp.sessions.{session_id}
```

Possible systems:

- Kafka
- NATS
- RabbitMQ

## 7. Transport Selection

Implementations MUST support at least the gRPC binding. Additional transports are OPTIONAL.

- gRPC -- high throughput coordination
- HTTP -- simple integrations
- WebSocket -- interactive coordination
- Message Bus -- distributed systems

## 8. Security

All transports MUST use encrypted transport.
Authentication requirements follow RFC-MACP-0004.
