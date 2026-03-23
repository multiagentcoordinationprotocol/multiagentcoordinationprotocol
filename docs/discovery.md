
# MACP Discovery Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md)

Discovery allows agents and runtimes to identify one another and understand supported capabilities.

## Manifest Overview

Each MACP component publishes a manifest describing:

- identity
- capabilities
- supported coordination modes
- transport endpoints

The manifest JSON Schema is at [`schemas/json/macp-agent-manifest.schema.json`](../schemas/json/macp-agent-manifest.schema.json). A full example is available at [`examples/discovery/agent_manifest.json`](../examples/discovery/agent_manifest.json).

## Well-known Discovery

Agents SHOULD publish their manifest at:

`https://<host>/.well-known/macp.json`

## Example Manifest

```json
{
  "agent_id": "agent://coordination.gateway",
  "title": "Coordination Gateway",
  "description": "Routes bounded MACP sessions across the standard coordination modes.",
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
      "uri": "grpcs://gateway.example.com:50051",
      "content_types": ["application/macp-envelope+proto"]
    }
  ],
  "metadata": {
    "owner": "coordination-platform"
  }
}
```

Content types SHOULD use registered MACP media types from [`registries/media-types.md`](../registries/media-types.md).

## Transport Endpoints

Manifests MAY include `transport_endpoints` to describe how MACP messages can be delivered. Each endpoint MUST include:

- a registered transport identifier (e.g., `macp.transport.grpc.v1`),
- a concrete URI,
- one or more supported content types.

Transport identifiers are listed in [`registries/transports.md`](../registries/transports.md). Directly connected `GetManifest` responses may omit `transport_endpoints` when the serving channel already establishes the relevant delivery coordinates or when deployment policy intentionally withholds them.

## `GetManifest` RPC

For the gRPC binding, manifests can also be retrieved via the `GetManifest` RPC:

- an empty `agent_id` requests the manifest of the serving runtime or agent,
- a non-empty `agent_id` requests a locally-known manifest for that identifier,
- self-manifests returned over an already-established channel may omit `transport_endpoints`.

## `ListModes` vs manifest `supported_modes`

`ListModes` returns only standards-track mode descriptors. `GetManifest` and `Initialize` may include both standards-track and extension mode identifiers in `supported_modes`. Extension mode discovery varies by runtime — some runtimes expose a separate extension listing surface.

## Registry-based Discovery

Organizations may operate registries that aggregate manifests across services.

## Security

Manifests SHOULD include only public discovery information. Transport endpoints MUST use secure transport (TLS). Secrets MUST NOT appear in manifests.
