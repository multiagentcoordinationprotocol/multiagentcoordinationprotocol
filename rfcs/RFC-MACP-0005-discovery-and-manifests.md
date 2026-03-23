
# RFC-MACP-0005: Discovery and Manifests
Status: Draft
Category: Standards Track
Author: MACP Working Group

## 1. Introduction

This document defines discovery and manifest mechanisms for the Multi-Agent Coordination Protocol (MACP). Discovery enables agents, runtimes, and coordination services to advertise identity, capabilities, supported coordination modes, and transport endpoints.

The MACP Manifest provides a machine-readable description of an agent or runtime instance and supports automated ecosystem composition.

See [RFC-MACP-0001 Section 11](RFC-MACP-0001-core.md#11-discovery-manifests-and-registries) for the core discovery model.

## 2. Terminology

Agent -- A computational entity participating in coordination.
Runtime -- A MACP kernel responsible for enforcing coordination sessions.
Manifest -- A machine-readable document describing identity, capabilities, modes, and transports.

## 3. Manifest Structure

The canonical protobuf definition is `macp.v1.AgentManifest` in [`schemas/proto/macp/v1/core.proto`](../schemas/proto/macp/v1/core.proto).
The canonical JSON Schema is [`schemas/json/macp-agent-manifest.schema.json`](../schemas/json/macp-agent-manifest.schema.json).

`AgentManifest` is used for both agent and runtime discovery.

A manifest MUST include the required fields defined by the schema:

- `agent_id`
- `description`
- `supported_modes`
- `input_content_types`
- `output_content_types`

A manifest MAY also include:

- `title`
- `metadata`
- `transport_endpoints`

If `transport_endpoints` are present, each endpoint MUST include:

- a registered transport identifier (for example `macp.transport.grpc.v1`),
- a concrete URI,
- one or more content types supported on that endpoint,
- optional endpoint metadata.

Example:

```json
{
  "agent_id": "agent://fraud-detector",
  "title": "Fraud Detection Agent",
  "description": "Analyzes transactions for fraud risk",
  "supported_modes": [
    "macp.mode.decision.v1",
    "macp.mode.proposal.v1",
    "macp.mode.task.v1",
    "macp.mode.handoff.v1",
    "macp.mode.quorum.v1"
  ],
  "input_content_types": [
    "application/macp-envelope+proto",
    "application/macp-envelope+json"
  ],
  "output_content_types": [
    "application/macp-envelope+proto",
    "application/macp-envelope+json"
  ],
  "transport_endpoints": [
    {
      "transport": "macp.transport.grpc.v1",
      "uri": "grpcs://fraud.example.com:50051",
      "content_types": [
        "application/macp-envelope+proto"
      ]
    }
  ],
  "metadata": {
    "owner": "risk-platform"
  }
}
```

## 4. Capability Declaration

Capabilities describe protocol features supported by the agent or runtime.
Capabilities MUST be registered in the MACP Capability Registry (see [`registries/capabilities.md`](../registries/capabilities.md)).

## 5. Mode Declaration

Agents declare supported coordination modes. Modes are defined in [RFC-MACP-0002](RFC-MACP-0002-modes.md) and, for the standards-track mode set in this repo, in [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) through [RFC-MACP-0011](RFC-MACP-0011-quorum-mode.md).

The `supported_modes` field in an AgentManifest MAY include both standards-track and non-standard mode identifiers (for example extension modes using the `ext.*` namespace). Clients SHOULD NOT assume that every identifier in `supported_modes` is a standards-track mode.

If a runtime exposes `ListModes`, the manifest's `supported_modes` MAY be a superset of the `ListModes` output because `ListModes` SHOULD return only standards-track modes while the manifest advertises the full runtime capability.

## 6. Transport Endpoints

Transport endpoints specify how MACP messages can be delivered. See [RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md) for transport binding details.

Supported transport types include registered MACP transport identifiers such as:

- `macp.transport.grpc.v1`
- `macp.transport.http.v1`
- `macp.transport.websocket.v1`
- `macp.transport.messagebus.v1`

Registered transport identifiers are listed in [`registries/transports.md`](../registries/transports.md).

`transport_endpoints` is OPTIONAL, but publishers SHOULD include at least one entry when the manifest is intended for network discovery by third parties. A directly connected `GetManifest` response MAY omit `transport_endpoints` when the current channel already establishes delivery coordinates or when deployment policy intentionally withholds them.

## 7. Discovery Mechanisms

Implementations MAY support multiple discovery mechanisms.

### 7.1 Well-known URL

A runtime or agent MAY publish its manifest at:

`https://<host>/.well-known/macp.json`

### 7.2 Registry Services

Registry services MAY index manifests across organizations.

### 7.3 `GetManifest` RPC Semantics

For the gRPC binding:

- an empty `GetManifestRequest.agent_id` requests the manifest of the serving runtime or agent,
- a non-empty `agent_id` requests a locally-known manifest for that identifier,
- if no such manifest is available, the runtime SHOULD return a transport-native not-found error,
- self-manifests returned over an already-established channel MAY omit `transport_endpoints` when the serving channel itself is the relevant delivery coordinate.

## 8. Manifest Versioning

Implementations MUST ignore unknown fields for forward compatibility.

Manifest publishers SHOULD use registered media types from [`registries/media-types.md`](../registries/media-types.md) for `input_content_types`, `output_content_types`, and `transport_endpoints[*].content_types`.

## 9. Security Considerations

Manifests SHOULD include only public discovery information.
Transport endpoints MUST use secure transport.
Sensitive authentication requirements MAY be summarized in `metadata`, but secrets MUST NOT appear in manifests.

## 10. Registries

This RFC establishes or relies on:

- Capability Registry (see [`registries/capabilities.md`](../registries/capabilities.md))
- Mode Registry (see [`registries/modes.md`](../registries/modes.md))
- Transport Registry (see [`registries/transports.md`](../registries/transports.md))
- Media Type Registry (see [`registries/media-types.md`](../registries/media-types.md))
