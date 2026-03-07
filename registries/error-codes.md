# MACP Error Code Registry

Defines machine-readable error identifiers used by MACP runtimes.

## Identifier Format

UPPER_SNAKE_CASE

## Standard Error Codes

| Code | Description | HTTP Status | Status | Reference |
|------|-------------|-------------|--------|-----------|
| UNAUTHENTICATED | Authentication failed | 401 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| FORBIDDEN | Not authorized for session | 403 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| SESSION_NOT_FOUND | Session does not exist | 404 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| SESSION_NOT_OPEN | Session already resolved or expired | 409 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| DUPLICATE_MESSAGE | message_id already processed | 409 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| INVALID_ENVELOPE | Envelope validation failed | 400 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| UNAUTHORIZED | Sender not authorized for session | 403 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |
| RATE_LIMITED | Too many requests | 429 | permanent | [RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md) |
| PAYLOAD_TOO_LARGE | Payload exceeds allowed size | 413 | permanent | [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) |

## Error Design Principles

Errors should:

- be stable across versions
- avoid leaking sensitive system details
- be machine-readable
