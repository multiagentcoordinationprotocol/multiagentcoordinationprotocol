
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
  "agent_id": "agent://fraud-detector",
  "title": "Fraud Detection Agent",
  "description": "Analyzes transactions for fraud risk",
  "supported_modes": ["macp.mode.decision.v1"],
  "input_content_types": ["application/json"],
  "output_content_types": ["application/json"]
}
```

## Registry-based Discovery

Organizations may operate registries that aggregate manifests across services.

## Security

Publish manifests over HTTPS and verify identities using public keys.
