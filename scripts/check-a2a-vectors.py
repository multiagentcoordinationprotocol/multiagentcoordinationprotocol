#!/usr/bin/env python3
"""Check the RFC-MACP-0014 A2A binding vectors in schemas/conformance/a2a/.

CI. The mapping itself is stdlib only, like check-cmt-hash-vectors.py and
check-receipt-vectors.py: no protobuf, no jsonschema. For every vector file
(all *.json except vector-schema.json) it:

  1. checks the file name matches `id`, and that ids are unique;
  2. recomputes the result of `op` on `input` and `params` with the small
     reference mapper below, which implements RFC-MACP-0014 1.1.x (§5.1-§5.4,
     §6, §8, §9.1, §11, §12) over the RFC-MACP-0001 §10 canonical JSON
     mapping, and compares it with `expected` (parsed JSON, with a bool never
     equal to a number) or with `expected_error` (`layer` and `code`);
  3. asserts every op of the SDKs' A2A codec (S6.2) and every reject code
     appears in at least one vector, so a vector cannot be deleted unnoticed.

Then it runs ajv (already a CI dependency of `make json-validate`) to check:

  - every vector against schemas/conformance/a2a/vector-schema.json;
  - every A2A-side object a positive vector produces against its $def in
    schemas/json/macp-a2a-binding.schema.json (EnvelopePart, AckMessage,
    ObservationArtifact, SessionStateMetadata, AgentExtension), using the
    same per-$def copies scripts/extract-a2a-objects.py `wrap` writes for
    validate-json.sh;
  - every Envelope a positive vector takes or produces against
    macp-envelope.schema.json, every Ack against the Ack $def;
  - the A2A-side input of every positive decode vector against its $def,
    except the inputs listed in INPUT_SCHEMA_EXEMPT, which a decoder accepts
    although an encoder never writes them (the boolean `duplicate` of §12 is
    one: the ErrorInfo $def rejects it on purpose).

What the reference mapper does NOT do: convert a JSON `payload` object to
Protobuf bytes or back (RFC-MACP-0001 §10.13). That needs every payload
schema, which is the SDKs' job. So a JSON `payload` passes through unchanged,
which means each vector writes such a payload already in its canonical form
(every field without presence, defaults included), and no vector asks the
mapper for a conversion it cannot make: such a vector fails with
"reference mapper cannot compute". `payload_b64` and the `raw` Envelope
bytes are fully handled, the Envelope's own Protobuf encoding included.

Run: `python3 scripts/check-a2a-vectors.py` (`--no-ajv` skips the ajv steps).
"""

from __future__ import annotations

import base64
import calendar
import datetime
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VECTORS_DIR = ROOT / "schemas" / "conformance" / "a2a"
VECTOR_SCHEMA = VECTORS_DIR / "vector-schema.json"
A2A_SCHEMA = ROOT / "schemas" / "json" / "macp-a2a-binding.schema.json"
ENVELOPE_SCHEMA = ROOT / "schemas" / "json" / "macp-envelope.schema.json"
EXTRACTOR = ROOT / "scripts" / "extract-a2a-objects.py"

EXT = "https://multiagentcoordinationprotocol.io/a2a/extensions/macp/v1"
KEY_KIND = EXT + "/kind"
KEY_SEQUENCE = EXT + "/sequence"
KEY_SESSION_STATE = EXT + "/sessionState"
MT_JSON = "application/macp-envelope+json"
MT_PROTO = "application/macp-envelope+proto"
ERRORINFO_TYPE = "type.googleapis.com/google.rpc.ErrorInfo"
MACP_DOMAIN = "multiagentcoordinationprotocol.io"
TRANSPORT = "macp.transport.a2a.v1"
DEFAULT_MAX_PAYLOAD_BYTES = 1048576  # RFC-MACP-0014 §5.4

# RFC-MACP-0001 §10.12: Core message types select a Core payload in any mode.
CORE_TYPES = {"Signal", "Progress", "SessionStart", "SessionCancel", "SessionSuspend",
              "SessionResume", "Commitment"}
# registries/modes.md standards-track modes: the only modes whose mode-defined
# payloads may travel as a JSON `payload` (RFC-MACP-0014 §5.3).
STANDARD_MODES = {"macp.mode.decision.v1", "macp.mode.proposal.v1", "macp.mode.task.v1",
                  "macp.mode.handoff.v1", "macp.mode.quorum.v1"}
# The mode-defined message types of each standard mode: its <Type>Payload messages
# in schemas/proto/macp/modes/<mode>/v1/<mode>.proto.
STANDARD_MODE_TYPES = {
    "macp.mode.decision.v1": {"Proposal", "Evaluation", "Objection", "Vote"},
    "macp.mode.proposal.v1": {"Proposal", "CounterProposal", "Accept", "Reject", "Withdraw"},
    "macp.mode.task.v1": {"TaskRequest", "TaskAccept", "TaskReject", "TaskUpdate", "TaskComplete", "TaskFail"},
    "macp.mode.handoff.v1": {"HandoffOffer", "HandoffContext", "HandoffAccept", "HandoffDecline"},
    "macp.mode.quorum.v1": {"ApprovalRequest", "Approve", "Reject", "Abstain"},
}
assert set(STANDARD_MODE_TYPES) == STANDARD_MODES
# RFC-MACP-0014 §8.
STATE_MAP = {
    "SESSION_STATE_OPEN": ("TASK_STATE_WORKING", "OPEN"),
    "SESSION_STATE_SUSPENDED": ("TASK_STATE_WORKING", "SUSPENDED"),
    "SESSION_STATE_RESOLVED": ("TASK_STATE_COMPLETED", "RESOLVED"),
    "SESSION_STATE_EXPIRED": ("TASK_STATE_FAILED", "EXPIRED"),
    "SESSION_STATE_CANCELLED": ("TASK_STATE_CANCELED", "CANCELLED"),
}
SESSION_STATE_NUMBERS = {0: "SESSION_STATE_UNSPECIFIED", 1: "SESSION_STATE_OPEN",
                         2: "SESSION_STATE_RESOLVED", 3: "SESSION_STATE_EXPIRED",
                         4: "SESSION_STATE_SUSPENDED", 5: "SESSION_STATE_CANCELLED"}
MAX_SAFE = 2**53 - 1
INT64 = (-(2**63), 2**63 - 1)
MIN_MS = calendar.timegm((1, 1, 1, 0, 0, 0, 0, 0, 0)) * 1000
MAX_MS = calendar.timegm((9999, 12, 31, 23, 59, 59, 0, 0, 0)) * 1000 + 999

# Every function of the SDKs' A2A codec (Wave 6 work item S6.2), in snake_case.
OPS = ["envelope_to_a2a_part", "envelope_from_a2a_part", "envelope_to_a2a_message",
       "envelope_from_a2a_message", "ack_to_a2a_message", "ack_from_a2a_message",
       "envelope_to_a2a_artifact", "envelope_from_a2a_artifact", "session_state_to_a2a",
       "session_state_from_a2a", "macp_agent_extension", "error_info_from_a2a"]
REQUIRED_ERRORS = {("a2a", "INVALID_REQUEST"), ("macp", "INVALID_ENVELOPE"),
                   ("macp", "PAYLOAD_TOO_LARGE"), ("codec", "NOT_A_MACP_MESSAGE"),
                   ("codec", "INVALID_ACK"), ("codec", "INVALID_SEQUENCE"),
                   ("codec", "INVALID_SESSION_STATE")}

# Positive decode inputs a decoder accepts but that an encoder never writes,
# so they are not held to macp-a2a-binding.schema.json. Keyed by vector id.
INPUT_SCHEMA_EXEMPT = {
    "a2a_063_ack_unknown_state_name_dropped": "the Ack $def pins the emitted enum names",
    "a2a_064_ack_integer_state": "the Ack $def pins the emitted enum names, not integers",
    "a2a_094_error_duplicate_boolean_not_duplicate":
        "ErrorInfo.metadata.duplicate is pinned to the string \"true\"; a boolean is the point",
    "a2a_104_from_part_media_type_mixed_case":
        "EnvelopePart.mediaType is pinned to the lowercase form a sender MUST write (§5.1)",
}


class Reject(Exception):
    def __init__(self, layer: str, code: str, why: str):
        super().__init__(f"{layer}/{code}: {why}")
        self.layer, self.code = layer, code


class CannotCompute(Exception):
    """The vector needs a conversion the reference mapper does not make."""


def bad_envelope(why: str) -> Reject:
    return Reject("macp", "INVALID_ENVELOPE", why)


def bad_ack(why: str) -> Reject:
    return Reject("codec", "INVALID_ACK", why)


# --- primitives --------------------------------------------------------------

def check_utf8(text: str, err) -> str:
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise err("lone surrogate")
    return text


_B64_SHAPE = re.compile(r"\A([A-Za-z0-9+/_-]*)(={0,2})\Z")


def b64_decode(text, err) -> bytes:
    """RFC-MACP-0014 §5.3 / RFC-MACP-0001 §10.3: either alphabet but not both,
    padded or not, padding only up to a multiple of 4; non-zero trailing bits
    are accepted (both SDKs agreed in S6.1)."""
    if not isinstance(text, str):
        raise err("base64 value is not a string")
    m = _B64_SHAPE.match(text)
    if m is None:
        raise err("not base64")
    digits, pad = m.groups()
    if re.search(r"[+/]", digits) and re.search(r"[-_]", digits):
        raise err("base64 mixes the standard and URL-safe alphabets")
    if len(digits) % 4 == 1:
        raise err("base64 length is impossible")
    if pad and (len(digits) + len(pad)) % 4:
        raise err("base64 padding does not complete a quartet")
    std = digits.replace("-", "+").replace("_", "/")
    # Decode by hand so trailing bits are ignored rather than checked.
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    out, acc, bits = bytearray(), 0, 0
    for ch in std:
        acc = (acc << 6) | alphabet.index(ch)
        bits += 6
        if bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
    return bytes(out)


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")  # standard alphabet, padded


_RFC3339 = re.compile(
    r"\A([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?"
    r"(?:[Zz]|([+-])([0-9]{2}):([0-9]{2}))\Z")


def parse_timestamp(text: str) -> int:
    """Any RFC 3339 timestamp to ms, truncating below the ms; refuses a result
    outside 0001-01-01T00:00:00Z..9999-12-31T23:59:59.999Z (RFC-MACP-0001 §10.11)."""
    m = _RFC3339.match(text)
    if m is None:
        raise bad_envelope(f"timestamp {text!r} is not RFC 3339")
    year, month, day, hour, minute, second = (int(g) for g in m.groups()[:6])
    frac, sign, oh, om = m.groups()[6:]
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if not (1 <= month <= 12 and 1 <= day <= days[month - 1] and hour <= 23 and minute <= 59
            and second <= 59):
        raise bad_envelope(f"timestamp {text!r} is not a valid date-time")
    offset = 0
    if sign:
        if int(oh) > 23 or int(om) > 59:
            raise bad_envelope(f"timestamp {text!r} has an invalid offset")
        offset = (int(oh) * 60 + int(om)) * (1 if sign == "+" else -1)
    ms = (calendar.timegm((year, month, day, hour, minute, second, 0, 0, 0)) - offset * 60) * 1000
    ms += int((frac or "")[:3].ljust(3, "0"))
    if not MIN_MS <= ms <= MAX_MS:
        raise bad_envelope(f"timestamp {text!r} is outside years 0001-9999 in UTC")
    return ms


def format_timestamp(ms: int) -> str:
    """RFC-MACP-0014 §5.3: ...SSZ when the ms part is 0, else exactly 3 digits."""
    if not MIN_MS <= ms <= MAX_MS:
        raise bad_envelope(f"timestamp_unix_ms {ms} is outside years 0001-9999")
    seconds, millis = divmod(ms, 1000)
    d = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=seconds)
    # Formatted by hand: strftime's %Y does not zero-pad years below 1000 everywhere.
    text = f"{d.year:04d}-{d.month:02d}-{d.day:02d}T{d.hour:02d}:{d.minute:02d}:{d.second:02d}"
    return f"{text}Z" if millis == 0 else f"{text}.{millis:03d}Z"


def int64_from_json(value, err) -> int:
    """RFC-MACP-0001 §10.9 plus the S6.1 edge rules: a JSON number must be
    integral (5.0 and 1e3 are), finite and within 2^53-1; a quoted value must
    match ^-?[0-9]+$; both within int64."""
    if value is None:
        return 0
    if isinstance(value, bool):
        raise err("an int64 is not a boolean")
    if isinstance(value, int):
        number = value
        if abs(number) > MAX_SAFE:
            raise err("an int64 above 2^53-1 must be quoted")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise err("an int64 is not finite")
        if not value.is_integer():
            raise err("an int64 is not integral")
        number = int(value)
        if abs(number) > MAX_SAFE:
            raise err("an int64 above 2^53-1 must be quoted")
    elif isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value):
        number = int(value)
    else:
        raise err(f"{value!r} is not an int64")
    if not INT64[0] <= number <= INT64[1]:
        raise err("int64 out of range")
    return number


def int64_to_json(number: int):
    return number if abs(number) <= MAX_SAFE else str(number)


# --- Envelope: canonical JSON (RFC-MACP-0001 §10, RFC-MACP-0014 §5.3) ---------

STRINGS = ("macp_version", "mode", "message_type", "message_id", "session_id", "sender")


def mode_defined_payload_has_schema(mode: str, message_type: str) -> bool:
    """RFC-MACP-0001 §10.12: selected by the (mode, message_type) pair."""
    return message_type in CORE_TYPES or message_type in STANDARD_MODE_TYPES.get(mode, ())


def envelope_from_json(obj) -> dict:
    if not isinstance(obj, dict):
        raise bad_envelope("an Envelope is a JSON object")
    env = {}
    for name in STRINGS:
        value = obj.get(name)
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise bad_envelope(f"{name} is not a string")
        env[name] = check_utf8(value, bad_envelope)
    ts = obj.get("timestamp")
    if ts is None:
        env["timestamp_unix_ms"] = 0
    elif isinstance(ts, str):
        env["timestamp_unix_ms"] = parse_timestamp(ts)
    else:
        raise bad_envelope("timestamp is not a string")
    payload, b64 = obj.get("payload"), obj.get("payload_b64")
    if (payload is None) == (b64 is None):
        raise bad_envelope("exactly one of payload and payload_b64 is required")
    if b64 is not None:
        env["payload"] = ("bytes", b64_decode(b64, bad_envelope))
    else:
        if not isinstance(payload, dict):
            raise bad_envelope("payload is not a JSON object")
        if not mode_defined_payload_has_schema(env["mode"], env["message_type"]):
            raise bad_envelope("a JSON payload with no payload schema (send payload_b64)")
        env["payload"] = ("json", payload)
    return env


def envelope_to_json(env: dict) -> dict:
    out = {name: env[name] for name in STRINGS}
    out["timestamp"] = format_timestamp(env["timestamp_unix_ms"])
    kind, value = env["payload"]
    if kind == "json":
        out["payload"] = value  # passes through: already canonical by construction
    elif mode_defined_payload_has_schema(env["mode"], env["message_type"]):
        raise CannotCompute("payload bytes would encode as a JSON payload object")
    else:
        out["payload_b64"] = b64_encode(value)  # §5.3: ext.* / reverse-domain
    return out


def payload_size(env: dict, limit_given: bool) -> int | None:
    kind, value = env["payload"]
    if kind == "bytes":
        return len(value)
    if limit_given:
        raise CannotCompute("the size of a JSON payload needs its Protobuf conversion")
    return None


# --- Envelope: Protobuf (envelope.proto) --------------------------------------

def varint(n: int) -> bytes:
    n &= (1 << 64) - 1
    out = bytearray()
    while n > 0x7F:
        out.append(n & 0x7F | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def envelope_to_proto(env: dict) -> bytes:
    kind, payload = env["payload"]
    if kind != "bytes":
        raise CannotCompute("a raw Part needs the payload bytes of a JSON payload")
    out = bytearray()
    for number, name in enumerate(STRINGS, start=1):
        data = env[name].encode("utf-8")
        if data:
            out += varint(number << 3 | 2) + varint(len(data)) + data
    if env["timestamp_unix_ms"]:
        out += varint(7 << 3) + varint(env["timestamp_unix_ms"])
    if payload:
        out += varint(8 << 3 | 2) + varint(len(payload)) + payload
    return bytes(out)


def read_varint(buf: bytes, i: int) -> tuple[int, int]:
    result = 0
    for k in range(10):
        if i >= len(buf):
            raise bad_envelope("truncated varint")
        byte = buf[i]
        i += 1
        if k == 9 and byte > 1:
            raise bad_envelope("varint overflows 64 bits")
        result |= (byte & 0x7F) << (7 * k)
        if byte < 0x80:
            return result, i
    raise bad_envelope("varint longer than 10 bytes")


def envelope_from_proto(buf: bytes) -> dict:
    env = {name: "" for name in STRINGS}
    env["timestamp_unix_ms"] = 0
    payload = b""
    i = 0
    while i < len(buf):
        tag, i = read_varint(buf, i)
        number, wire = tag >> 3, tag & 7
        if number == 0:
            raise bad_envelope("field number 0")
        if wire == 0:
            value, i = read_varint(buf, i)
            if number == 7:
                env["timestamp_unix_ms"] = value - (1 << 64) if value >> 63 else value
            elif number in range(1, 9):
                raise CannotCompute("known field with an unexpected wire type")
        elif wire == 2:
            length, i = read_varint(buf, i)
            if i + length > len(buf):
                raise bad_envelope("truncated length-delimited field")
            chunk, i = buf[i:i + length], i + length
            if 1 <= number <= 6:
                try:
                    env[STRINGS[number - 1]] = chunk.decode("utf-8")
                except UnicodeDecodeError:
                    raise bad_envelope("string field is not UTF-8")
            elif number == 8:
                payload = chunk
            elif number == 7:
                raise CannotCompute("known field with an unexpected wire type")
        elif wire in (1, 5):
            if number in range(1, 9):
                raise CannotCompute("known field with an unexpected wire type")
            i += 8 if wire == 1 else 4
            if i > len(buf):
                raise bad_envelope("truncated fixed-width field")
        else:
            raise CannotCompute(f"wire type {wire}")
    env["payload"] = ("bytes", payload)
    return env


# --- Parts and Messages (§5.1, §5.2, §6) --------------------------------------

def envelope_media_type(part):
    """§5.1 media type comparison: (media type, has_parameters), or None when the
    Part is not an Envelope Part. Type and subtype compare ASCII case-insensitively
    (RFC 9110 §8.3.1), with surrounding spaces and tabs ignored; a `;` after the
    subtype marks parameters, even with nothing after it."""
    if not isinstance(part, dict) or not isinstance(part.get("mediaType"), str):
        return None
    head, sep, _ = part["mediaType"].partition(";")
    base = head.strip(" \t")
    if not base.isascii():
        return None
    base = base.lower()
    return (base, bool(sep)) if base in (MT_JSON, MT_PROTO) else None


def is_envelope_part(part) -> bool:
    return envelope_media_type(part) is not None


def part_from_envelope(env: dict, encoding: str) -> dict:
    if encoding == "json":
        return {"mediaType": MT_JSON, "data": envelope_to_json(env)}
    if encoding == "proto":
        return {"mediaType": MT_PROTO, "raw": b64_encode(envelope_to_proto(env))}
    raise CannotCompute(f"encoding {encoding!r}")


def envelope_from_part(part, params: dict) -> dict:
    found = envelope_media_type(part)
    if found is None:
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "not an Envelope Part")
    media_type, has_parameters = found
    if has_parameters:
        # §5.1: never skipped as a non-MACP Part; ContentTypeNotSupportedError (§11.3).
        raise Reject("a2a", "INVALID_REQUEST", "an Envelope media type with parameters (§5.1)")
    if media_type == MT_JSON:
        if not isinstance(part.get("data"), dict):
            raise bad_envelope("a JSON Envelope Part carries no data object (§5.1)")
        env = envelope_from_json(part["data"])
    else:
        if "raw" not in part:
            raise bad_envelope("a Protobuf Envelope Part carries no raw bytes (§5.1)")
        env = envelope_from_proto(b64_decode(part["raw"], bad_envelope))
    limit = params.get("max_payload_bytes", DEFAULT_MAX_PAYLOAD_BYTES)
    size = payload_size(env, "max_payload_bytes" in params)
    if size is not None and size > limit:
        raise Reject("macp", "PAYLOAD_TOO_LARGE", f"{size} > {limit} payload bytes (§5.4)")
    return env


def single_envelope_part(parts) -> dict:
    if not isinstance(parts, list):
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "no parts")
    found = [p for p in parts if is_envelope_part(p)]  # other Parts are ignored (§5.1)
    if len(found) > 1:
        raise Reject("a2a", "INVALID_REQUEST", "two or more Envelope Parts (§5.1, §11.3)")
    if not found:
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "no Envelope Part")
    return found[0]


def expected_task_id(env: dict) -> str:
    """§6.1/§6.2: empty for SessionStart and for a Signal, else the session_id."""
    return "" if env["message_type"] in ("SessionStart", "Signal") else env["session_id"]


def op_envelope_to_a2a_part(inp, params):
    return part_from_envelope(envelope_from_json(inp["envelope"]), params.get("encoding", "json"))


def op_envelope_from_a2a_part(inp, params):
    return envelope_to_json(envelope_from_part(inp["part"], params))


def op_envelope_to_a2a_message(inp, params):
    env = envelope_from_json(inp["envelope"])
    msg = {
        "messageId": params.get("message_id") or env["message_id"],  # §5.1 SHOULD
        "role": "ROLE_USER",
        "parts": [part_from_envelope(env, params.get("encoding", "json"))],
        "extensions": [EXT],
    }
    if expected_task_id(env):
        msg["taskId"] = expected_task_id(env)
    if params.get("context_id"):
        msg["contextId"] = params["context_id"]
    return msg


def op_envelope_from_a2a_message(inp, params):
    msg = inp["message"]
    if not isinstance(msg, dict):
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "not a Message")
    env = envelope_from_part(single_envelope_part(msg.get("parts")), params)
    task_id = msg.get("taskId") or ""
    # §6.1 "Later envelopes": a session-scoped Envelope after SessionStart must name
    # its own session. A non-empty taskId on a SessionStart or Signal is reported by
    # the server from its Task state (§11.3: TaskNotFound, SESSION_ALREADY_EXISTS),
    # which a codec cannot decide, so the mapper leaves it unchecked and no vector
    # pins it.
    if expected_task_id(env) and task_id != expected_task_id(env):
        raise bad_envelope("Message.taskId does not match the Envelope (§6.1)")
    return envelope_to_json(env)


# --- Ack (§5.2) ----------------------------------------------------------------

def ack_from_json(obj) -> dict:
    if not isinstance(obj, dict):
        raise bad_ack("an Ack is a JSON object")
    ack = {}
    for name in ("ok", "duplicate"):
        value = obj.get(name)
        if value is None:
            value = False
        if not isinstance(value, bool):
            raise bad_ack(f"{name} is not a boolean")
        ack[name] = value
    for name in ("message_id", "session_id"):
        value = obj.get(name)
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise bad_ack(f"{name} is not a string")
        ack[name] = check_utf8(value, bad_ack)
    ack["accepted_at_unix_ms"] = int64_from_json(obj.get("accepted_at_unix_ms"), bad_ack)
    state = obj.get("session_state")
    if state is None:
        state = "SESSION_STATE_UNSPECIFIED"
    elif isinstance(state, str):
        # RFC-MACP-0001 §10.4: an unknown name leaves the field at its default.
        state = state if state in SESSION_STATE_NUMBERS.values() else "SESSION_STATE_UNSPECIFIED"
    elif isinstance(state, (int, float)) and not isinstance(state, bool) and float(state).is_integer():
        number = int(state)
        if not -(2**31) <= number < 2**31:
            raise bad_ack("session_state out of int32 range")
        state = SESSION_STATE_NUMBERS.get(number, "SESSION_STATE_UNSPECIFIED")
    else:
        raise bad_ack("session_state is neither a name nor an integer")
    ack["session_state"] = state
    err = obj.get("error")
    if err is not None:
        if not isinstance(err, dict):
            raise bad_ack("error is not an object")
        out = {}
        for name in ("code", "message", "session_id", "message_id"):
            value = err.get(name)
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise bad_ack(f"error.{name} is not a string")
            out[name] = check_utf8(value, bad_ack)
        details = err.get("details")
        out["details"] = b"" if details is None else b64_decode(details, bad_ack)
        ack["error"] = out
    # RFC-MACP-0014 §5.2: `error` is present if and only if `ok` is false.
    if ("error" in ack) == ack["ok"]:
        raise bad_ack("error must be present exactly when ok is false (§5.2)")
    return ack


def ack_to_json(ack: dict) -> dict:
    out = {
        "ok": ack["ok"],
        "duplicate": ack["duplicate"],
        "message_id": ack["message_id"],
        "session_id": ack["session_id"],
        "accepted_at_unix_ms": int64_to_json(ack["accepted_at_unix_ms"]),
        "session_state": ack["session_state"],
    }
    if "error" in ack:
        e = ack["error"]
        out["error"] = {"code": e["code"], "message": e["message"], "session_id": e["session_id"],
                        "message_id": e["message_id"], "details": b64_encode(e["details"])}
    return out


def op_ack_to_a2a_message(inp, params):
    ack = ack_from_json(inp["ack"])
    msg = {
        "messageId": params["message_id"],
        "role": "ROLE_AGENT",
        "extensions": [EXT],
        "parts": [{"mediaType": "application/json", "data": ack_to_json(ack),
                   "metadata": {KEY_KIND: "ack"}}],
    }
    if params.get("task_id"):
        msg["taskId"] = params["task_id"]
    if params.get("context_id"):
        msg["contextId"] = params["context_id"]
    return msg


def op_ack_from_a2a_message(inp, params):
    msg = inp["message"]
    parts = msg.get("parts") if isinstance(msg, dict) else None
    acks = [p for p in parts or [] if isinstance(p, dict)
            and isinstance(p.get("metadata"), dict) and p["metadata"].get(KEY_KIND) == "ack"]
    if not acks:
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "no Ack Part")
    if len(acks) > 1:
        raise bad_ack("two Ack Parts")
    return ack_to_json(ack_from_json(acks[0].get("data")))


# --- Artifacts (§9.1) ----------------------------------------------------------

def check_sequence(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Reject("codec", "INVALID_SEQUENCE", "EXT/sequence is not a number")
    if isinstance(value, float) and not (math.isfinite(value) and value.is_integer()):
        raise Reject("codec", "INVALID_SEQUENCE", "EXT/sequence is not an integer")
    if not 1 <= int(value) <= MAX_SAFE:
        raise Reject("codec", "INVALID_SEQUENCE", "EXT/sequence is below 1")
    return int(value)


def op_envelope_to_a2a_artifact(inp, params):
    env = envelope_from_json(inp["envelope"])
    sequence = check_sequence(inp["sequence"])
    return {
        "artifactId": "macp:" + env["message_id"],
        "name": env["message_type"],
        "parts": [part_from_envelope(env, "json")],
        "metadata": {KEY_SEQUENCE: sequence},
        "extensions": [EXT],
    }


def op_envelope_from_a2a_artifact(inp, params):
    art = inp["artifact"]
    if not isinstance(art, dict):
        raise Reject("codec", "NOT_A_MACP_MESSAGE", "not an Artifact")
    meta = art.get("metadata") if isinstance(art.get("metadata"), dict) else {}
    if KEY_SEQUENCE not in meta:
        raise Reject("codec", "INVALID_SEQUENCE", "EXT/sequence is missing")
    sequence = check_sequence(meta[KEY_SEQUENCE])
    env = envelope_from_part(single_envelope_part(art.get("parts")), params)
    return {"envelope": envelope_to_json(env), "sequence": sequence}


# --- Session state (§8) --------------------------------------------------------

def op_session_state_to_a2a(inp, params):
    state = inp["session_state"]
    if state not in STATE_MAP:
        raise Reject("codec", "INVALID_SESSION_STATE", f"{state!r} has no A2A mapping")
    task_state, bare = STATE_MAP[state]
    return {"task_state": task_state, "metadata": {KEY_SESSION_STATE: bare}}


def op_session_state_from_a2a(inp, params):
    obj = inp["task_or_event"]
    meta = obj.get("metadata") if isinstance(obj, dict) else None
    value = meta.get(KEY_SESSION_STATE) if isinstance(meta, dict) else None
    # Never fall back to TaskState (§8).
    for name, (_, bare) in STATE_MAP.items():
        if value == bare:
            return name
    raise Reject("codec", "INVALID_SESSION_STATE", f"EXT/sessionState is {value!r}")


# --- AgentExtension (§3) and ErrorInfo (§11.1, §12) ---------------------------

def op_macp_agent_extension(inp, params):
    out = {
        "uri": EXT,
        "required": bool(params.get("required", False)),
        "params": {"macpVersions": params["macp_versions"], "modes": params["modes"],
                   "transport": TRANSPORT},
    }
    if params.get("manifest_url"):
        out["params"]["manifestUrl"] = params["manifest_url"]
    return out


def op_error_info_from_a2a(inp, params):
    src = inp["error_or_details"]
    details = src if isinstance(src, list) else (src.get("data") if isinstance(src, dict) else None)
    hits = [d for d in details or [] if isinstance(d, dict)
            and d.get("@type") == ERRORINFO_TYPE and d.get("domain") == MACP_DOMAIN]
    if not hits:
        return None
    info = hits[0]
    meta = info.get("metadata") if isinstance(info.get("metadata"), dict) else {}
    return {"reason": info.get("reason", ""), "domain": info["domain"], "metadata": meta,
            "duplicate": meta.get("duplicate") == "true"}  # the string only (§12)


OP_FUNCS = {name: globals()["op_" + name] for name in OPS}


# --- comparison ---------------------------------------------------------------

def same(a, b) -> bool:
    """Parsed-JSON equality: member order is irrelevant, 2 equals 2.0 (JSON
    has one number type), but a bool is never a number and "2" is never 2."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


# --- schema objects ------------------------------------------------------------

def schema_objects(v: dict) -> list[tuple[str, object, str]]:
    """(def, object, label) to validate for one positive vector. "Envelope" means
    macp-envelope.schema.json itself; every other name is an A2A $def."""
    op, inp, exp, vid = v["op"], v["input"], v["expected"], v["id"]
    objs = []

    def env_parts(parts, where):
        for i, p in enumerate(parts):
            if is_envelope_part(p):
                objs.append(("EnvelopePart", p, f"{where}.parts[{i}]"))

    if "envelope" in inp:
        objs.append(("Envelope", inp["envelope"], "input.envelope"))
    if "ack" in inp:
        objs.append(("Ack", inp["ack"], "input.ack"))
    exempt = vid in INPUT_SCHEMA_EXEMPT
    if op == "envelope_to_a2a_part":
        objs.append(("EnvelopePart", exp, "expected"))
    elif op == "envelope_to_a2a_message":
        env_parts(exp["parts"], "expected")
    elif op == "ack_to_a2a_message":
        objs.append(("AckMessage", exp, "expected"))
    elif op == "envelope_to_a2a_artifact":
        objs.append(("ObservationArtifact", exp, "expected"))
    elif op == "session_state_to_a2a":
        objs.append(("SessionStateMetadata", exp["metadata"], "expected.metadata"))
    elif op == "macp_agent_extension":
        objs.append(("AgentExtension", exp, "expected"))
    elif op == "envelope_from_a2a_part":
        objs.append(("Envelope", exp, "expected"))
        if not exempt:
            objs.append(("EnvelopePart", inp["part"], "input.part"))
    elif op == "envelope_from_a2a_message":
        objs.append(("Envelope", exp, "expected"))
        if not exempt:
            env_parts(inp["message"]["parts"], "input.message")
    elif op == "envelope_from_a2a_artifact":
        objs.append(("Envelope", exp["envelope"], "expected.envelope"))
        if not exempt:
            objs.append(("ObservationArtifact", inp["artifact"], "input.artifact"))
    elif op == "ack_from_a2a_message":
        objs.append(("Ack", exp, "expected"))
        if not exempt:
            objs.append(("AckMessage", inp["message"], "input.message"))
    elif op == "session_state_from_a2a":
        if not exempt:
            objs.append(("SessionStateMetadata", inp["task_or_event"].get("metadata", {}),
                         "input.task_or_event.metadata"))
    elif op == "error_info_from_a2a" and exp is not None and not exempt:
        src = inp["error_or_details"]
        for i, d in enumerate(src if isinstance(src, list) else src.get("data", [])):
            if d.get("@type") == ERRORINFO_TYPE and d.get("domain") == MACP_DOMAIN:
                objs.append(("ErrorInfo", d, f"input.error_or_details[{i}]"))
    return objs


def run_ajv(vectors: list[dict], paths: list[Path]) -> list[str]:
    ajv = shutil.which("ajv")
    if ajv is None:
        return ["ajv not found on PATH (npm install -g ajv-cli), or pass --no-ajv"]
    problems = []
    common = ["--spec=draft2020", "--strict=false"]

    def ajv_run(schema: Path, data: list[Path], refs: list[Path]) -> set[str]:
        cmd = [ajv, "validate", "-s", str(schema)]
        for r in refs:
            cmd += ["-r", str(r)]
        for d in data:
            cmd += ["-d", str(d)]
        res = subprocess.run(cmd + common, capture_output=True, text=True)
        text = res.stdout + res.stderr
        if res.returncode == 0:
            return set()
        bad = {str(d) for d in data if f"{d} invalid" in text}
        if not bad:  # ajv failed without naming a file (e.g. the schema did not compile)
            bad = {str(d) for d in data}
        sys.stderr.write("".join(line + "\n" for line in text.splitlines()
                                 if not line.endswith(" valid") and "unknown format" not in line))
        return bad

    for p in sorted(ajv_run(VECTOR_SCHEMA, paths, [])):
        problems.append(f"{Path(p).name}: does not validate against vector-schema.json")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "wrap").mkdir()
        res = subprocess.run([sys.executable, str(EXTRACTOR), "wrap", str(A2A_SCHEMA),
                              str(tmp / "wrap")], capture_output=True, text=True)
        if res.returncode != 0:
            return problems + ["could not write per-$def copies of macp-a2a-binding.schema.json"]
        defs = set(res.stdout.split())
        groups: dict[str, list[tuple[Path, str]]] = {}
        n = 0
        for v in vectors:
            if "expected" not in v:
                continue
            for def_name, obj, label in schema_objects(v):
                n += 1
                f = tmp / f"{n:04d}.json"
                f.write_text(json.dumps(obj))
                groups.setdefault(def_name, []).append((f, f"{v['id']}: {label}"))
        for def_name, items in sorted(groups.items()):
            if def_name == "Envelope":
                schema, refs = ENVELOPE_SCHEMA, []
            elif def_name in defs:
                schema, refs = tmp / "wrap" / f"a2a-{def_name}.schema.json", [ENVELOPE_SCHEMA]
            else:
                problems.append(f"no $def {def_name} in {A2A_SCHEMA.name}")
                continue
            bad = ajv_run(schema, [f for f, _ in items], refs)
            for f, label in items:
                if str(f) in bad:
                    problems.append(f"{label} does not validate against {def_name}")
        print(f"ajv: {len(paths)} vectors against vector-schema.json, "
              f"{n} objects against their schemas")
    return problems


# --- main ---------------------------------------------------------------------

def main() -> int:
    use_ajv = "--no-ajv" not in sys.argv[1:]
    paths = sorted(p for p in VECTORS_DIR.glob("*.json") if p.name != "vector-schema.json")
    problems, vectors, seen_ids = [], [], set()
    ops_seen, errors_seen = set(), set()
    for path in paths:
        try:
            v = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append(f"{path.name}: not JSON ({e})")
            continue
        vectors.append(v)
        vid, op = v.get("id"), v.get("op")
        if vid != path.stem:
            problems.append(f"{path.name}: id {vid!r} does not match the file name")
        if vid in seen_ids:
            problems.append(f"{path.name}: duplicate id")
        seen_ids.add(vid)
        if op not in OP_FUNCS:
            problems.append(f"{path.name}: unknown op {op!r}")
            continue
        if ("expected" in v) == ("expected_error" in v):
            problems.append(f"{path.name}: needs exactly one of expected and expected_error")
            continue
        ops_seen.add(op)
        try:
            got, err = OP_FUNCS[op](v.get("input", {}), v.get("params", {})), None
        except Reject as r:
            got, err = None, r
        except CannotCompute as c:
            problems.append(f"{path.name}: reference mapper cannot compute ({c})")
            continue
        if "expected_error" in v:
            want = v["expected_error"]
            errors_seen.add((want.get("layer"), want.get("code")))
            if err is None:
                problems.append(f"{path.name}: expected {want}, got a result:\n  "
                                + json.dumps(got, ensure_ascii=False))
            elif (err.layer, err.code) != (want.get("layer"), want.get("code")):
                problems.append(f"{path.name}: expected {want.get('layer')}/{want.get('code')}, "
                                f"got {err}")
        elif err is not None:
            problems.append(f"{path.name}: expected a result, got {err}")
        elif not same(got, v["expected"]):
            problems.append(f"{path.name}: expected differs from the reference mapper, which gives:\n  "
                            + json.dumps(got, ensure_ascii=False, sort_keys=True))
    for op in OPS:
        if op not in ops_seen:
            problems.append(f"no vector exercises {op}")
    for layer, code in sorted(REQUIRED_ERRORS - errors_seen):
        problems.append(f"no reject vector expects {layer}/{code}")
    for vid in INPUT_SCHEMA_EXEMPT:
        if vid not in seen_ids:
            problems.append(f"INPUT_SCHEMA_EXEMPT names {vid}, which is not a vector")
    print(f"reference mapper: {len(vectors)} vectors, {len(ops_seen)} ops")
    if use_ajv and not problems:
        problems += run_ajv(vectors, paths)
    for p in problems:
        print("FAIL " + p)
    if problems:
        print(f"\n{len(problems)} problem(s) in schemas/conformance/a2a/")
        return 1
    print(f"all {len(vectors)} A2A vectors match the RFC-MACP-0014 reference mapper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
