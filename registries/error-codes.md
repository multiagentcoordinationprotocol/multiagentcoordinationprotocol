# MACP Error Code Registry

Defines machine-readable error identifiers used by MACP runtimes.

## Identifier Format

UPPER_SNAKE_CASE

## Standard Error Codes

| Code | Description | HTTP Status | Status | Reference |
|------|-------------|-------------|--------|-----------|
| UNAUTHENTICATED | Authentication failed | 401 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| FORBIDDEN | Authenticated sender is not authorized for the session or message type | 403 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| SESSION_NOT_FOUND | Session does not exist | 404 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| SESSION_NOT_OPEN | Session already resolved or expired | 409 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| DUPLICATE_MESSAGE | `message_id` already accepted within the session | 409 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| INVALID_ENVELOPE | Envelope validation failed or payload did not satisfy the required structural contract | 400 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| UNSUPPORTED_PROTOCOL_VERSION | No mutually supported protocol version exists, or an envelope uses an unsupported negotiated version | 400 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| MODE_NOT_SUPPORTED | The referenced coordination mode or mode version is not supported for new sessions | 400 | permanent | [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md) |
| PAYLOAD_TOO_LARGE | Payload exceeds allowed size | 413 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| RATE_LIMITED | Too many requests | 429 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| UNAUTHORIZED | Historical alias for `FORBIDDEN`; new implementations SHOULD use `FORBIDDEN` | 403 | deprecated | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |

## Error Design Principles

Errors should:

- be stable across versions
- avoid leaking sensitive system details
- be machine-readable
- distinguish protocol version negotiation failures from envelope-shape failures
- distinguish unsupported modes from generic invalid-envelope rejections
