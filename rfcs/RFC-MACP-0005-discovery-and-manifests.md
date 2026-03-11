
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

The manifest JSON Schema is defined at [`schemas/json/macp-agent-manifest.schema.json`](../schemas/json/macp-agent-manifest.schema.json).

Example:

```json
{
  "agent_id": "agent://fraud-detector",
  "title": "Fraud Detection Agent",
  "description": "Analyzes transactions for fraud risk",
  "supported_modes": [
    "macp.mode.decision.v1"
  ],
  "input_content_types": [
    "application/json"
  ],
  "output_content_types": [
    "application/json"
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
Agents declare supported coordination modes. Modes are defined in RFC-MACP-0002.

## 6. Transport Endpoints
Transport endpoints specify how MACP messages can be delivered. See [RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md) for transport binding details.

Supported transport types include:
- grpc
- http
- websocket
- messagebus

Registered transport identifiers are listed in [`registries/transports.md`](../registries/transports.md).

## 7. Discovery Mechanisms
Implementations MAY support multiple discovery mechanisms.

Well-known URL:
`https://<host>/.well-known/macp.json`

Registry services MAY index manifests across organizations.

## 8. Manifest Versioning
Manifest documents MUST include all required fields defined by the manifest JSON Schema (`agent_id`, `description`, `supported_modes`, `input_content_types`, `output_content_types`).
Implementations MUST ignore unknown fields for forward compatibility.

## 9. Security Considerations
Manifests SHOULD include cryptographic identity (public key).
Transport endpoints MUST use secure transport (TLS).

## 10. Registries
This RFC establishes:
- Capability Registry (see [`registries/capabilities.md`](../registries/capabilities.md))
- Mode Registry (see [`registries/modes.md`](../registries/modes.md))
- Transport Registry (see [`registries/transports.md`](../registries/transports.md))
