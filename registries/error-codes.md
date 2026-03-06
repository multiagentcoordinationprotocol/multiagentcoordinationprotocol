# MACP Error Code Registry

| Code | Meaning | Status |
|---|---|---|
| `UNSUPPORTED_PROTOCOL_VERSION` | No mutually supported protocol version exists | permanent |
| `INVALID_ENVELOPE` | Envelope failed structural validation | permanent |
| `UNAUTHENTICATED` | Authentication failed | permanent |
| `FORBIDDEN` | Sender is not authorized | permanent |
| `SESSION_NOT_FOUND` | Referenced session does not exist | permanent |
| `SESSION_NOT_OPEN` | Referenced session is not OPEN | permanent |
| `DUPLICATE_MESSAGE` | Duplicate `message_id` observed in scope | permanent |
| `MODE_NOT_SUPPORTED` | Requested Mode or Mode version is not supported | permanent |
| `PAYLOAD_TOO_LARGE` | Payload exceeds runtime limits | permanent |
| `RATE_LIMITED` | Runtime refused request due to rate limiting | provisional |
