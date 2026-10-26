# MACP Error Code Registry

Defines machine-readable error identifiers used by MACP runtimes.

## Identifier Format

UPPER_SNAKE_CASE

## Standard Error Codes

| Code | Description | HTTP Status | gRPC Status | Status | Reference |
|------|-------------|-------------|-------------|--------|-----------|
| UNAUTHENTICATED | Authentication failed | 401 | `UNAUTHENTICATED` | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| FORBIDDEN | Authenticated sender is not authorized for the session, message type, role, or claimed authority (see RFC-MACP-0002 §6.1 for the Mode-rule mapping) | 403 | `PERMISSION_DENIED` | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md), [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| SESSION_NOT_FOUND | Session does not exist | 404 | `NOT_FOUND` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| SESSION_NOT_OPEN | Session is not OPEN (resolved, expired, cancelled, or suspended) | 409 | `FAILED_PRECONDITION` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| DUPLICATE_MESSAGE | `message_id` already accepted within the session | 409 | `ALREADY_EXISTS` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| SESSION_ALREADY_EXISTS | Session already has an accepted SessionStart for this session_id | 409 | `ALREADY_EXISTS` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| INVALID_ENVELOPE | Envelope validation failed, payload did not satisfy the required structural contract, or a session-scoped message breached the bound Mode's validation rules (sender-authorization breaches use `FORBIDDEN`; see RFC-MACP-0002 §6.1) | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md), [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| UNSUPPORTED_PROTOCOL_VERSION | No mutually supported protocol version exists, or an envelope uses an unsupported negotiated version | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| MODE_NOT_SUPPORTED | The referenced coordination mode or mode version is not supported for new sessions | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| PAYLOAD_TOO_LARGE | Payload exceeds allowed size | 413 | `RESOURCE_EXHAUSTED` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| RATE_LIMITED | Too many requests | 429 | `RESOURCE_EXHAUSTED` | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| INVALID_SESSION_ID | `session_id` format does not meet deployment requirements (e.g., not a valid UUID or base64url token) | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| INTERNAL_ERROR | Unrecoverable internal runtime error (e.g., storage failure); clients SHOULD retry or escalate | 500 | `INTERNAL` | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| UNKNOWN_POLICY_VERSION | `policy_version` not found in policy registry at SessionStart | 404 | `NOT_FOUND` | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) |
| POLICY_DENIED | Commitment rejected because governance policy rules are not satisfied | 403 | `PERMISSION_DENIED` | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) |
| INVALID_POLICY_DEFINITION | Policy descriptor fails validation (bad JSON, schema mismatch, mode mismatch) | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) |
| REGISTRY_READ_ONLY | A registry mutation (`RegisterPolicy`, `UnregisterPolicy`, `RegisterExtMode`, `UnregisterExtMode`, `PromoteMode`) was refused because this runtime's registry is not mutable over the API (for example, policies loaded from deployment configuration) | 409 | `FAILED_PRECONDITION` | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md), [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| INVALID_REQUEST | A control-plane request that is not an Envelope failed validation (for example, a negative `page_size`, an unparseable `page_token`, or a missing descriptor); Envelope failures use `INVALID_ENVELOPE` | 400 | `INVALID_ARGUMENT` | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| STREAM_LAGGED | A server-stream subscriber (`StreamSession`, `WatchSessions`, `WatchSignals`) fell behind and the runtime dropped events for it; the stream ends, and the client SHOULD resubscribe and SHOULD NOT assume it observed every event | 503 | `RESOURCE_EXHAUSTED` | permanent | [RFC-MACP-0006](../rfcs/RFC-MACP-0006-transport-bindings.md) |
| AGENT_NOT_FOUND | `GetManifest` named an `agent_id` this runtime does not host | 404 | `NOT_FOUND` | permanent | [RFC-MACP-0005](../rfcs/RFC-MACP-0005-discovery-and-manifests.md) |
| HISTORY_UNAVAILABLE | `WhatIfReplay` named a session whose full accepted history the runtime no longer holds (for example, its log was compacted into a checkpoint when it ended), so no report can be produced | 409 | `FAILED_PRECONDITION` | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) |
| UNAUTHORIZED | Historical alias for `FORBIDDEN`; new implementations SHOULD use `FORBIDDEN` | 403 | `PERMISSION_DENIED` | deprecated | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |

The **gRPC Status** column is the status code the gRPC binding MUST use when it surfaces a MACP error code as an RPC status ([RFC-MACP-0006 §3](../rfcs/RFC-MACP-0006-transport-bindings.md)). It is aligned with the **HTTP Status** column: 401 maps to `UNAUTHENTICATED`, 403 to `PERMISSION_DENIED`, 404 to `NOT_FOUND`, 400 to `INVALID_ARGUMENT`, 413 and 429 to `RESOURCE_EXHAUSTED`, and 500 to `INTERNAL`. 409 splits by cause: a lifecycle or state conflict (`SESSION_NOT_OPEN`, `HISTORY_UNAVAILABLE`) maps to `FAILED_PRECONDITION`, and an existence conflict (`DUPLICATE_MESSAGE`, `SESSION_ALREADY_EXISTS`) maps to `ALREADY_EXISTS`. The deprecated alias `UNAUTHORIZED` maps to `PERMISSION_DENIED`, the same status as the `FORBIDDEN` code it aliases. One code departs from the HTTP alignment: `STREAM_LAGGED` is HTTP 503, because the server shed the subscriber and the client did nothing wrong, but it is gRPC `RESOURCE_EXHAUSTED`, because a per-subscriber buffer was exhausted. That is the status gRPC clients of existing runtimes already receive, and `UNAVAILABLE` would wrongly invite a transparent retry of the same call.

## Stability of Permanent Codes

Runtimes, SDKs and embedders map these codes onto their own wire formats and client logic, so a `permanent` entry is a compatibility promise:

- A `permanent` code MUST NOT be renamed or removed.
- Its **HTTP Status** and **gRPC Status** mappings MUST NOT change.
- Its description MAY be clarified, but MUST NOT be narrowed so that a condition it covered moves to a different code.

A code that is superseded becomes `deprecated` and stays in this table, as `UNAUTHORIZED` has, so that recorded histories and older clients still resolve it. `provisional` codes carry no such promise until they are promoted.

## Error Design Principles

Errors should:

- be stable across versions
- avoid leaking sensitive system details
- be machine-readable
- distinguish protocol version negotiation failures from envelope-shape failures
- distinguish unsupported modes from generic invalid-envelope rejections
