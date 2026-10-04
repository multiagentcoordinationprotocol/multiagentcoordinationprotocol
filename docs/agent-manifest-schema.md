# MACP Agent Manifest Schema Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md)

This schema gives MACP discovery a concrete, machine-readable contract.

Why it matters:

A discovery RFC explains **what a manifest means**.  
A JSON Schema explains **exactly what shape a valid manifest must have**.

That makes discovery easier to implement, easier to validate, and much more credible as a
protocol ecosystem. It is also what lets a manifest evolve without breaking older consumers:
[RFC-MACP-0005 §8 (Manifest Versioning)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md)
requires implementations to ignore unknown fields, and a machine-checked schema is what makes
"unknown field" an unambiguous, validated concept rather than an implementation's own guess.

The schema lives at [`schemas/json/macp-agent-manifest.schema.json`](../schemas/json/macp-agent-manifest.schema.json).

## Core design choices

The required and optional fields, and the `transport_endpoints` shape, are defined by the schema
itself and by [RFC-MACP-0005 §3 (Manifest Structure)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md) —
see either rather than a restated list here, so this document can't drift from the schema it
describes.

Content type fields (`input_content_types`, `output_content_types`, and `transport_endpoints[*].content_types`) SHOULD use registered MACP media types such as `application/macp-envelope+proto` and `application/macp-envelope+json`.

## Publishing a manifest

See [`docs/discovery.md`](discovery.md#well-known-discovery) for the well-known publishing
location and [RFC-MACP-0005 §7.1 (Well-known URL)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md).

## Validation

Any implementation can validate a manifest against this schema before accepting it into a registry or using it for negotiation.

This is the piece that turns discovery from “a nice doc” into “a real interoperable surface.”
