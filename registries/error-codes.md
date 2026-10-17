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
| UNAUTHORIZED | Historical alias for `FORBIDDEN`; new implementations SHOULD use `FORBIDDEN` | 403 | `PERMISSION_DENIED` | deprecated | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |

The **gRPC Status** column is the status code the gRPC binding MUST use when it surfaces a MACP error code as an RPC status ([RFC-MACP-0006 §3](../rfcs/RFC-MACP-0006-transport-bindings.md)). It is aligned with the **HTTP Status** column: 401 maps to `UNAUTHENTICATED`, 403 to `PERMISSION_DENIED`, 404 to `NOT_FOUND`, 400 to `INVALID_ARGUMENT`, 413 and 429 to `RESOURCE_EXHAUSTED`, and 500 to `INTERNAL`. 409 splits by cause: a lifecycle conflict (`SESSION_NOT_OPEN`) maps to `FAILED_PRECONDITION`, and an existence conflict (`DUPLICATE_MESSAGE`, `SESSION_ALREADY_EXISTS`) maps to `ALREADY_EXISTS`. The deprecated alias `UNAUTHORIZED` maps to `PERMISSION_DENIED`, the same status as the `FORBIDDEN` code it aliases.

## Error Design Principles

Errors should:

- be stable across versions
- avoid leaking sensitive system details
- be machine-readable
- distinguish protocol version negotiation failures from envelope-shape failures
- distinguish unsupported modes from generic invalid-envelope rejections
