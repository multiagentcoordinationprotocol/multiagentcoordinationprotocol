# MACP Agent Manifest Schema Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md)

This schema gives MACP discovery a concrete, machine-readable contract.

Why it matters:

A discovery RFC explains **what a manifest means**.  
A JSON Schema explains **exactly what shape a valid manifest must have**.

That makes discovery easier to implement, easier to validate, and much more credible as a protocol ecosystem.

## Recommended placement

Put this file at:

`schemas/json/macp-agent-manifest.schema.json`

And reference it from:

- `RFC-MACP-0005 Discovery & Manifests`
- `docs/discovery.md`
- manifest examples in `examples/`

## Core design choices

The schema requires only the fields needed for practical interoperability:

- `agent_id` — unique agent identifier
- `description` — human-readable description
- `supported_modes` — at least one coordination mode
- `input_content_types` — accepted content types
- `output_content_types` — produced content types

Optional fields:

- `title` — human-readable display name
- `metadata` — arbitrary string key-value pairs
- `transport_endpoints` — array of transport endpoint objects, each containing a registered transport identifier, URI, and supported content types (see `$defs/TransportEndpoint` in the schema)

This keeps the manifest lightweight while still being implementation-ready.

Content type fields (`input_content_types`, `output_content_types`, and `transport_endpoints[*].content_types`) SHOULD use registered MACP media types such as `application/macp-envelope+proto` and `application/macp-envelope+json`.

## Example publishing pattern

A runtime or agent should publish a manifest at:

`https://<host>/.well-known/macp.json`

That document may include:

- supported MACP version
- transport endpoints
- supported modes
- auth expectations
- operational limits

## Validation

Any implementation can validate a manifest against this schema before accepting it into a registry or using it for negotiation.

This is the piece that turns discovery from “a nice doc” into “a real interoperable surface.”
