
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

per [RFC-MACP-0005 §3 (Manifest Structure)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md). The
manifest JSON Schema is at [`schemas/json/macp-agent-manifest.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-agent-manifest.schema.json) —
see [`docs/agent-manifest-schema.md`](agent-manifest-schema.md) for why the schema exists
alongside the RFC. A full example is available at [`examples/discovery/agent_manifest.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/agent_manifest.json),
validated in CI by `make json-validate`.

## Well-known Discovery

Agents SHOULD publish their manifest at:

`https://<host>/.well-known/macp.json`

per [RFC-MACP-0005 §7.1 (Well-known URL)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md).

Content types SHOULD use registered MACP media types from [`registries/media-types.md`](../registries/media-types.md).

## Transport Endpoints

Manifests MAY include `transport_endpoints` to describe how MACP messages can be delivered. Each endpoint MUST include:

- a registered transport identifier (e.g., `macp.transport.grpc.v1`),
- a concrete URI,
- one or more supported content types.

per [RFC-MACP-0005 §6 (Transport Endpoints)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md).
Transport identifiers are listed in [`registries/transports.md`](../registries/transports.md). Directly connected `GetManifest` responses may omit `transport_endpoints` when the serving channel already establishes the relevant delivery coordinates or when deployment policy intentionally withholds them.

## `GetManifest` RPC

For the gRPC binding, manifests can also be retrieved via the `GetManifest` RPC, per
[RFC-MACP-0005 §7.3 (`GetManifest` RPC Semantics)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md):

- an empty `agent_id` requests the manifest of the serving runtime or agent,
- a non-empty `agent_id` requests a locally-known manifest for that identifier,
- self-manifests returned over an already-established channel may omit `transport_endpoints`.

## `ListModes` vs manifest `supported_modes`

`ListModes` returns only standards-track mode descriptors; `GetManifest` and `Initialize` may
additionally include extension mode identifiers in `supported_modes`. See
[docs/modes.md](modes.md#extension-modes) and
[RFC-MACP-0002 §12 (Extension mode lifecycle)](../rfcs/RFC-MACP-0002-modes.md) for how extension
modes are declared and discovered.

## Registry-based Discovery

Organizations may operate registries that aggregate manifests across services, per [RFC-MACP-0005 §7.2 (Registry Services) and §10 (Registries)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md).

## Security

Manifests SHOULD include only public discovery information. Transport endpoints MUST use secure transport (TLS). Secrets MUST NOT appear in manifests. See
[RFC-MACP-0005 §9 (Security Considerations)](../rfcs/RFC-MACP-0005-discovery-and-manifests.md).
