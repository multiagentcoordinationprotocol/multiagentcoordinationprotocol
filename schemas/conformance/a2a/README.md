# A2A binding codec vectors (RFC-MACP-0014)

Reference vectors for a codec of the [A2A extension binding](../../../rfcs/RFC-MACP-0014-a2a-binding.md)
(1.1.x). The SDKs vendor this directory under `tests/vectors/a2a/` (held
identical by `scripts/check-sdk-sync.py`) and run every vector against their
own A2A codec.

Each file is one vector, named after its `id` (`a2a_NNN_<slug>`):

```json
{ "id": "...", "op": "...", "description": "...", "input": { }, "params": { },
  "expected": "<the result>"  |  "expected_error": { "layer": "a2a|macp|codec", "code": "..." } }
```

`vector-schema.json` documents the shape, including which `input` and `params`
keys each `op` takes. `make a2a-vectors` runs `scripts/check-a2a-vectors.py`,
a stdlib-only reference mapper that recomputes every vector; changing any
`expected` value fails the run. All ids, timestamps and payloads are fixed, so
the vectors are deterministic.

## Ops

Every `op` is one function of the SDKs' A2A codec (Wave 6 work item S6.2),
spelled in snake_case (`envelopeToA2APart` in TypeScript is
`envelope_to_a2a_part`). The codec's constants (the extension URI, the two
Envelope media types) are pinned implicitly by the vectors that use them.

| `op` | `input` | `params` | Result | Vectors |
|---|---|---|---|---|
| `envelope_to_a2a_part` | `envelope` | `encoding` | an Envelope Part (§5.1) | 10 |
| `envelope_from_a2a_part` | `part` | `max_payload_bytes` | an Envelope | 26 |
| `envelope_to_a2a_message` | `envelope` | `encoding`, `message_id`, `context_id` | a ROLE_USER Message (§5.1, §6) | 4 |
| `envelope_from_a2a_message` | `message` | `max_payload_bytes` | an Envelope | 12 |
| `ack_to_a2a_message` | `ack` | `message_id` (required), `task_id`, `context_id` | an Ack Message (§5.2) | 7 |
| `ack_from_a2a_message` | `message` | | an Ack | 14 |
| `envelope_to_a2a_artifact` | `envelope`, `sequence` | | an Observation Artifact (§9.1) | 3 |
| `envelope_from_a2a_artifact` | `artifact` | `max_payload_bytes` | `{envelope, sequence}` | 5 |
| `session_state_to_a2a` | `session_state` | | `{task_state, metadata}` (§8) | 6 |
| `session_state_from_a2a` | `task_or_event` | | a `SESSION_STATE_*` name (§8) | 12 |
| `macp_agent_extension` | | `macp_versions`, `modes`, `required`, `manifest_url` | an AgentExtension (§3) | 2 |
| `error_info_from_a2a` | `error_or_details` | | `{reason, domain, metadata, duplicate}` or `null` (§11, §12) | 5 |

106 vectors in all: 68 positive, 38 reject.

## Conventions

- **Envelopes and Acks** in `input` and `expected` are in the canonical JSON
  mapping of RFC-MACP-0001 §10: every field without presence is present,
  defaults included; enums by name; int64 as a number up to 2^53-1 and quoted
  above; `timestamp` as `YYYY-MM-DDTHH:MM:SSZ` or with exactly three fraction
  digits (§5.3, G9); base64 standard with padding. A decoder's result is
  compared after re-encoding in that form.
- **JSON `payload` objects** are written in full canonical form. The
  reference mapper passes them through unchanged rather than converting them
  to Protobuf (RFC-MACP-0001 §10.13), so an SDK that round-trips them through
  the payload message gets the same object.
- **Payload form** (§5.3): a Core payload (SessionStart, Commitment, Signal and
  the other Core types) is a `payload` object in any mode; a mode-defined
  payload of an `ext.*` or reverse-domain mode is `payload_b64`. Raw Part
  vectors carry `payload_b64` input, so their bytes are exact.
- **`encoding`** is `"json"` (default) or `"proto"`. A `proto` Envelope is
  written in field-number order with defaults omitted.
- **`messageId`** defaults to the Envelope's `message_id`. `taskId` and
  `contextId` are omitted when empty, as `examples/a2a-binding-session.json`
  does.
- **`max_payload_bytes`** defaults to 1048576 and bounds the decoded payload
  bytes, not the base64 text or the whole Envelope (§5.4).
- **`macp_agent_extension`** always emits `required` (default `false`), never
  `description`, and `params.manifestUrl` only when `manifest_url` is given.
- **`error_info_from_a2a`** selects the ErrorInfo whose `@type` is
  `type.googleapis.com/google.rpc.ErrorInfo` and whose `domain` is
  `multiagentcoordinationprotocol.io` from a JSON-RPC error's `data` or a bare
  details array. `duplicate` is `true` only for the string `"true"` (§12); the
  boolean `true` is a plain `SESSION_NOT_OPEN` (vector 094, whose input is
  exempt from the ErrorInfo `$def` because that `$def` rejects it on purpose).

## Error layers and codes

| `layer` | `code` | Meaning |
|---|---|---|
| `a2a` | `INVALID_REQUEST` | Rejected as a whole at the A2A level: JSON-RPC -32602, or `ContentTypeNotSupportedError` for an Envelope Part whose `mediaType` carries parameters (§5.1, §11.3). |
| `macp` | `INVALID_ENVELOPE` | In-band Ack error: the Envelope Part does not decode, a payload form is wrong, or taskId names another session (§6.1, §11). |
| `macp` | `PAYLOAD_TOO_LARGE` | In-band Ack error (§5.4). |
| `codec` | `NOT_A_MACP_MESSAGE` | No Envelope Part (or no Ack Part) at all. |
| `codec` | `INVALID_ACK` | A malformed Ack Message on the client side. |
| `codec` | `INVALID_SEQUENCE` | `EXT/sequence` missing, non-integral or below 1. |
| `codec` | `INVALID_SESSION_STATE` | `EXT/sessionState` missing or not a bare state name; `SESSION_STATE_UNSPECIFIED` has no TaskState. |

The `codec` codes are local to an SDK's codec; RFC-MACP-0014 assigns no wire
code to these cases.

## S6.1 edge rules covered

Timestamp offsets, sub-millisecond truncation and the 0001-9999 range after
the offset is applied (007-009, 033-037); base64 unpadded, URL-safe, mixed
alphabets, partial or excess padding, impossible lengths and non-zero trailing
bits (010, 025, 038-044); a lone surrogate in a string (045); a raw Envelope
varint that overflows 64 bits (046); int64 quoted, unquoted at and above
2^53-1, with an exponent, with a zero fraction, with a sign or fraction in
quotes, and non-finite (051-053, 056-062); an unknown enum name and an
integer enum value (063, 064); an integral float where an integer is expected
(069); `error` present exactly when `ok` is false (099, 100); payload
selection by the `(mode, message_type)` pair (031, 101); the §5.1 media type
comparison (1.1.2-draft): a parameter-bearing Envelope Part is rejected, never
skipped, and counts toward the one-Envelope-per-Message check, and a case
variant is an Envelope Part, but a non-ASCII lookalike is not (102-106).

## S6.1 edge rules not covered, and why

- **Negative zero** (`"-0"` for a `double` or `float`, RFC-MACP-0014 §5.3 as of
  1.1.1-draft). Neither the Envelope nor the Ack has a floating-point field.
  The nearest are inside Core payloads (`SignalPayload.confidence`,
  `ProgressPayload.progress` and `total`), and a pass-through vector there
  would be computable, but `schemas/json/macp-envelope.schema.json` types
  those fields `number`, so an Envelope carrying the canonical `"-0"` fails
  the schema the checker validates every Envelope against (as `"NaN"` and
  `"Infinity"`, which RFC-MACP-0001 §10.8 allows, already do). The vector
  waits for that schema to be widened (issue #246).
- **Map key order** in emitted JSON. No Envelope, Ack or A2A-side object this
  pack produces has a Protobuf map at the level the mapper handles, and
  `expected` is compared as parsed JSON, so key order is not observable.
- **Rules inside payloads** (enum and int64 handling within a `payload`
  object, a lone surrogate in a map key). The mapper does not convert
  payloads, so these belong to the SDKs' own canonical-JSON tests.
- **Leap seconds.** RFC 3339 allows a seconds value of 60, which a Protobuf
  Timestamp cannot hold; the reference mapper refuses it, but no vector pins
  either behaviour.

## Deliberately not pinned

- Which A2A error a Message with two Envelope Parts gets when one of them
  carries parameters. §5.1 says JSON-RPC -32602, not
  `ContentTypeNotSupportedError`, but both carry `ErrorInfo.reason`
  `INVALID_REQUEST`, which is all a vector's `expected_error` names (103, 105).
- A non-empty `taskId` on a `SessionStart` or Signal Message. The server
  answers it from its Task state (§6.1, §6.2, §11.3: `TaskNotFoundError`,
  `SESSION_ALREADY_EXISTS`), which a codec cannot decide, so the reference
  mapper does not check it.
