#!/usr/bin/env python3
"""Hold macp-envelope.schema.json's $defs to core.proto's Core payload set.

Three issues (#156, #161, #162) each found the same root-cause gap by hand: a
Core message or field defined in schemas/proto/macp/v1/core.proto with no
corresponding description in schemas/json/macp-envelope.schema.json's $defs.
Nothing machine-checked that the two stayed in sync. This script does.

CI. Runs with bare `python3` -- stdlib only (json, re, sys, pathlib, os), the
same constraint scripts/check-parity-contract.py is built under. Honors a
MACP_ROOT environment-variable override, the same seam scripts/validate-json.sh
and scripts/check-parity-contract.py already expose, so the mutation-and-restore
proofs in Phase 3's self-test can run against a throwaway copy of the tree.

This script parses schemas/proto/macp/v1/{core,envelope,policy}.proto with a
deliberately narrow regex-based parser, not protoc: protoc is a *soft*
dependency in this repo (scripts/validate-proto.sh:15-22 self-skips when it is
absent) and this check must not silently stop guarding anything when that
happens. The parser understands exactly the constructs these three files use
today (messages, fields, map fields, oneof, nested/top-level enum, the one
service block) and hard-fails on anything else inside an in-scope message
body, rather than silently loosening to tolerate it.

Checks:
  1. Three-way set agreement: core.proto's `*Payload`-suffixed top-level
     messages, the envelope schema's `allOf` branches (by `const` +
     `payload.$ref`), and the `message_type` property description's
     "Mode-independent Core types (...)" enumeration all agree on the same
     7-member set, and that count is pinned.
  2. `$defs` entry existence: each of the 7 Core payloads has an
     object-typed `$defs.<Type>Payload` entry, and each `allOf` branch's
     `$ref` points at the `$defs` entry matching its own `const` -- a branch
     whose const and $ref disagree would pass both set comparisons and
     silently validate the wrong shape.
  3. Field coverage, transitive: every proto field on a Core payload (and on
     any message-typed field reached from one -- `Root`, `CommitmentRef`)
     has a matching JSON Schema property, unless the (message, field) pair
     is explicitly allowlisted in UNMAPPED_PROTO_FIELDS.
  4. Message classification: every top-level message across core.proto,
     envelope.proto and policy.proto is reachable from either a Core payload
     or the RPC service surface (`service MACPRuntimeService`'s request/
     response types, transitively). An unreachable message is neither --
     this is what closes the suffix-selector hole: a future Core payload
     added without the `Payload` suffix surfaces here instead of silently
     passing Check 1 as "not a payload".
  5. Type shapes: every field reached by Check 3 maps to the JSON shape its
     proto declaration implies -- `repeated T` to a `"type": "array"` with
     matching `items`, `map<K,V>` to a `"type": "object"` with matching
     `additionalProperties`, `bytes` to `$defs.Base64Bytes`, a message type
     to a `$ref` naming it, a scalar to SCALAR_JSON_TYPE's JSON type. Checks
     only `type`/`items`/`additionalProperties`/`$ref`; JSON-Schema-only
     authoring keywords (`required`, `minimum`, `pattern`, `description`,
     ...) have no proto counterpart and are not inspected.
  6. Reverse direction and orphan `$defs`: every property on a reached
     `$defs` entry has a proto field behind it (no allowlist in this
     direction, by choice), and every `$defs` entry overall is either
     reached or named in JSON_ONLY_DEFS.
  7. `Envelope`'s own fields: its 8 proto fields are all held to the
     schema's top-level `properties`, six by identity and two (`timestamp_
     unix_ms`, `payload`) through ENVELOPE_FIELD_MAP's normative
     non-identity mapping (RFC-MACP-0001 §10.1, §10.2).

Every failure is accumulated and reported together before exiting non-zero
(this repo's check-prose.py / check-parity-contract.py convention) -- one bad
value must never mask another.

Run: `python3 scripts/check-envelope-coverage.py` (exits non-zero on any
mismatch, missing $defs entry, uncovered field, unclassified message, or
unrecognised construct inside an in-scope message).
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("MACP_ROOT") or Path(__file__).resolve().parent.parent)
CORE_PROTO = ROOT / "schemas" / "proto" / "macp" / "v1" / "core.proto"
ENVELOPE_PROTO = ROOT / "schemas" / "proto" / "macp" / "v1" / "envelope.proto"
POLICY_PROTO = ROOT / "schemas" / "proto" / "macp" / "v1" / "policy.proto"
ENVELOPE_SCHEMA = ROOT / "schemas" / "json" / "macp-envelope.schema.json"

PROTO_FILES = (CORE_PROTO, ENVELOPE_PROTO, POLICY_PROTO)

# A manifest count, not a convenience -- the same idiom as
# check-parity-contract.py's EXPECTED_SECTION_COUNT. Check 1 proves the three
# enumerations AGREE; it cannot notice all three shrinking together. A Core
# payload deleted from the proto, its $defs entry, its allOf branch and the
# message_type description in one commit leaves every comparison green and the
# guarded surface one message smaller. This pin is what fails then.
EXPECTED_CORE_PAYLOAD_COUNT = 7

# The ONLY allowlist, and it has exactly one member. A $defs entry with no
# proto message behind it. Base64Bytes is the JSON encoding of proto `bytes`
# (RFC-MACP-0001 Section 10.3), not a message, so it is legitimately orphaned.
# Adding a member here requires a reason in this dict, not a bare name.
JSON_ONLY_DEFS = {
    "Base64Bytes": "JSON encoding of proto `bytes` (RFC-MACP-0001 Section 10.3); not a message",
}

# EMPTY ON PURPOSE, and the emptiness is the point. A (message, field) pair
# here declares a proto field deliberately absent from the canonical JSON
# mapping. No such case exists at HEAD. The default for a future case is
# therefore a HARD FAILURE, and admitting one means writing the reason down
# here where a reviewer sees it. Never add a bare entry to silence a red run.
UNMAPPED_PROTO_FIELDS: dict[tuple[str, str], str] = {}

# proto3 scalar/well-known type keywords -- anything else is a message or enum
# type reference for the purposes of the transitive walks below.
SCALAR_TYPES = frozenset({
    "double", "float", "int32", "int64", "uint32", "uint64", "sint32", "sint64",
    "fixed32", "fixed64", "sfixed32", "sfixed64", "bool", "string", "bytes",
})

# Narrower than SCALAR_TYPES on purpose, and "bytes" is deliberately absent --
# it maps to a $ref (Base64Bytes), not a bare "type" value, so Check 5 handles
# it as its own case. Only the scalar proto types that actually appear on a
# reached field today are listed; an unlisted scalar (or an enum) must hit the
# "unknown proto type" branch and fail loudly rather than silently guess a
# JSON type for a case nobody has reasoned about yet.
SCALAR_JSON_TYPE = {
    "string": "string",
    "bool": "boolean",
    "int32": "integer",
    "int64": "integer",
    "uint32": "integer",
    "uint64": "integer",
    "double": "number",
    "float": "number",
}

MAP_TYPE_RE = re.compile(r"^map<\s*([\w.]+)\s*,\s*([\w.]+)\s*>$")

MESSAGE_OPEN_RE = re.compile(r"^message\s+(\w+)\s*\{$")
MESSAGE_EMPTY_RE = re.compile(r"^message\s+(\w+)\s*\{\}$")
SERVICE_OPEN_RE = re.compile(r"^service\s+\w+\s*\{$")
TOP_ENUM_OPEN_RE = re.compile(r"^enum\s+\w+\s*\{$")
ONEOF_OPEN_RE = re.compile(r"^\s{2}oneof\s+\w+\s*\{$")
NESTED_ENUM_OPEN_RE = re.compile(r"^\s{2}enum\s+\w+\s*\{$")
CLOSE_TOP_RE = re.compile(r"^\}$")
CLOSE_NESTED_RE = re.compile(r"^\s{2}\}$")

# Anchored at exactly two spaces of indent -- an ordinary message field.
FIELD_RE = re.compile(
    r"^\s{2}(?:(repeated|optional)\s+)?"
    r"(map<\s*([\w.]+)\s*,\s*([\w.]+)\s*>|[\w.]+)\s+"
    r"([a-z_]\w*)\s*=\s*(\d+)\s*;$"
)
# Same shape, anchored at four spaces -- a oneof member. proto3 forbids
# `repeated`/`optional` inside a oneof, so that group is not offered here.
ONEOF_FIELD_RE = re.compile(
    r"^\s{4}"
    r"(map<\s*([\w.]+)\s*,\s*([\w.]+)\s*>|[\w.]+)\s+"
    r"([a-z_]\w*)\s*=\s*(\d+)\s*;$"
)

RPC_RE = re.compile(
    r"^\s*rpc\s+\w+\s*\(\s*(?:stream\s+)?([\w.]+)\s*\)\s*returns\s*\(\s*(?:stream\s+)?([\w.]+)\s*\)",
    re.MULTILINE,
)

ERRORS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class Field:
    name: str
    type: str
    repeated: bool
    line: int


def strip_comment(line: str) -> str:
    """Strip a trailing `//` comment. These files have no string literals on
    field lines, so a plain `find` is sufficient -- this is not a general
    proto lexer and must not try to become one."""
    idx = line.find("//")
    return line if idx == -1 else line[:idx]


def parse_proto(
    path: Path,
) -> tuple[dict[str, list[Field]], list[tuple[str, str, int, str]], str]:
    """Parse one .proto file into {message_name: [Field, ...]}.

    Returns (messages, unknown, raw_text). `unknown` is every unrecognised
    construct found inside a message body, as (message_name, file, line,
    raw_line) -- NOT yet filtered to in-scope messages. The caller decides,
    after the reachability walks below, which of these are worth fail()ing:
    only messages reached by Check 3's field-coverage walk (the 7 payloads
    plus any message-typed field reached from one) are reported, so a
    hypothetical future odd construct inside an RPC-only message (never
    reached by that walk) does not fail a run it has nothing to do with.

    `raw_text` is returned so a caller needing the whole file's text (Check
    4's RPC harvest, over core.proto) can reuse it instead of re-reading the
    file a second time outside this function's guard -- a second raw read
    would crash unguarded on exactly the unreadable-file case this one exists
    to handle cleanly.

    State is tracked only via `^message Name {` and its own matching `^}` --
    deliberately not a general brace-depth counter, which would mis-attribute
    or desynchronise on the two top-level non-message blocks these files carry
    (`service MACPRuntimeService { ... }`, `enum SessionState { ... }`, both
    skipped to their own 0-indent closing brace without ever setting
    `current`) and on a message's own nested `oneof`/`enum` sub-blocks (each
    closed by its distinct 2-indent `}`, never changing `current`).
    """
    try:
        full_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail("%s could not be read: %s" % (rel(path), exc))
        return {}, [], ""
    raw_lines = full_text.splitlines()

    messages: dict[str, list[Field]] = {}
    unknown: list[tuple[str, str, int, str]] = []

    current: str | None = None
    in_oneof = False
    in_nested_enum = False
    skipping_top_block = False

    for lineno, raw in enumerate(raw_lines, 1):
        text = strip_comment(raw).rstrip()
        if not text.strip():
            continue

        if skipping_top_block:
            if CLOSE_TOP_RE.match(text):
                skipping_top_block = False
            continue

        if current is None:
            if MESSAGE_EMPTY_RE.match(text):
                messages.setdefault(MESSAGE_EMPTY_RE.match(text).group(1), [])
                continue
            m_open = MESSAGE_OPEN_RE.match(text)
            if m_open:
                current = m_open.group(1)
                messages.setdefault(current, [])
                continue
            if SERVICE_OPEN_RE.match(text) or TOP_ENUM_OPEN_RE.match(text):
                skipping_top_block = True
                continue
            # syntax/package/import lines, and anything else at top level,
            # are uninteresting to this check.
            continue

        # Inside a message body (current is not None).
        if in_nested_enum:
            if CLOSE_NESTED_RE.match(text):
                in_nested_enum = False
            continue

        if in_oneof:
            if CLOSE_NESTED_RE.match(text):
                in_oneof = False
                continue
            m = ONEOF_FIELD_RE.match(text)
            if m:
                _, _, _, field_name, _num = m.groups()
                type_text = m.group(1)
                messages[current].append(Field(field_name, type_text, False, lineno))
                continue
            unknown.append((current, rel(path), lineno, raw))
            continue

        if CLOSE_TOP_RE.match(text):
            current = None
            continue
        if NESTED_ENUM_OPEN_RE.match(text):
            in_nested_enum = True
            continue
        if ONEOF_OPEN_RE.match(text):
            in_oneof = True
            continue

        m = FIELD_RE.match(text)
        if m:
            qualifier, type_text = m.group(1), m.group(2)
            field_name = m.group(5)
            messages[current].append(
                Field(field_name, type_text, qualifier == "repeated", lineno)
            )
            continue

        unknown.append((current, rel(path), lineno, raw))

    return messages, unknown, full_text


def field_type_name(field_type: str) -> str | None:
    """Resolve a field's type text to a referenced message/enum type name, or
    None if it names a proto3 scalar. For `map<K, V>`, resolves V (the value
    type) -- map keys are always scalar in proto3, and this repo's JSON
    mapping never needs the key type to walk reachability."""
    m = MAP_TYPE_RE.match(field_type)
    candidate = m.group(2) if m else field_type
    return None if candidate in SCALAR_TYPES else candidate


def load_schema() -> dict | None:
    """Returns None on failure, never {} -- a schema that genuinely parses to
    an empty object is a separate, real failure (every check below would then
    find no $defs/allOf/properties), not the same case as a read/parse error.
    Conflating the two would exit non-zero with zero FAIL lines printed."""
    try:
        data = json.loads(ENVELOPE_SCHEMA.read_text(encoding="utf-8"))
    except OSError as exc:
        fail("%s could not be read: %s" % (rel(ENVELOPE_SCHEMA), exc))
        return None
    except json.JSONDecodeError as exc:
        fail("%s is not valid JSON: %s" % (rel(ENVELOPE_SCHEMA), exc))
        return None
    if not isinstance(data, dict):
        fail("%s does not contain a JSON object at its top level" % rel(ENVELOPE_SCHEMA))
        return None
    return data


def check_three_way_agreement(
    core_messages: dict[str, list[Field]], schema: dict
) -> tuple[set[str], list[str]]:
    errors: list[str] = []

    proto_set = {name[: -len("Payload")] for name in core_messages if name.endswith("Payload")}

    branch_set: set[str] = set()
    for branch in schema.get("allOf", []):
        then = branch.get("then", {})
        ref = then.get("properties", {}).get("payload", {}).get("$ref")
        if ref is None:
            continue
        const = branch.get("if", {}).get("properties", {}).get("message_type", {}).get("const")
        if const is None:
            errors.append(
                "an allOf branch has payload.$ref %r but no message_type.const -- "
                "this branch contributes nothing to the Core-payload set and cannot "
                "be identified by name" % ref
            )
            continue
        branch_set.add(const)

    description = (
        schema.get("properties", {}).get("message_type", {}).get("description", "")
    )
    m = re.search(r"Mode-independent Core types \(([^)]*)\)", description)
    if not m:
        errors.append(
            "macp-envelope.schema.json's message_type property description no "
            "longer contains a \"Mode-independent Core types (...)\" sentence -- "
            "the sentence was reworded; update the pattern, do not assume the "
            "enumeration is gone"
        )
        described_set: set[str] = set()
    else:
        described_set = {name.strip() for name in m.group(1).split(",") if name.strip()}

    if proto_set != branch_set:
        errors.append(
            "core.proto's *Payload messages %s do not match the envelope schema's "
            "allOf branch set %s (missing=%s extra=%s)"
            % (
                sorted(proto_set), sorted(branch_set),
                sorted(proto_set - branch_set), sorted(branch_set - proto_set),
            )
        )
    if proto_set != described_set:
        errors.append(
            "core.proto's *Payload messages %s do not match message_type's "
            "description enumeration %s (missing=%s extra=%s)"
            % (
                sorted(proto_set), sorted(described_set),
                sorted(proto_set - described_set), sorted(described_set - proto_set),
            )
        )
    if branch_set != described_set:
        errors.append(
            "the envelope schema's allOf branch set %s does not match "
            "message_type's description enumeration %s (missing=%s extra=%s)"
            % (
                sorted(branch_set), sorted(described_set),
                sorted(branch_set - described_set), sorted(described_set - branch_set),
            )
        )
    if len(proto_set) != EXPECTED_CORE_PAYLOAD_COUNT:
        errors.append(
            "expected %d Core payload message(s) (core.proto's *Payload-suffixed "
            "top-level messages), found %d: %s"
            % (EXPECTED_CORE_PAYLOAD_COUNT, len(proto_set), sorted(proto_set))
        )

    return proto_set, errors


def check_defs_existence(proto_set: set[str], schema: dict) -> list[str]:
    errors: list[str] = []
    defs = schema.get("$defs", {})

    for name in sorted(proto_set):
        defs_name = "%sPayload" % name
        entry = defs.get(defs_name)
        if entry is None:
            errors.append(
                "core.proto message %sPayload has no $defs.%s entry in "
                "macp-envelope.schema.json" % (name, defs_name)
            )
            continue
        if entry.get("type") != "object" or "properties" not in entry:
            errors.append(
                "$defs.%s must be \"type\": \"object\" with a properties object "
                "describing %sPayload's fields" % (defs_name, name)
            )

    for branch in schema.get("allOf", []):
        const = branch.get("if", {}).get("properties", {}).get("message_type", {}).get("const")
        ref = branch.get("then", {}).get("properties", {}).get("payload", {}).get("$ref")
        if const is None or ref is None:
            continue
        expected_ref = "#/$defs/%sPayload" % const
        if ref != expected_ref:
            errors.append(
                "the allOf branch for message_type %r $refs %r, not %r -- its "
                "const and its payload $ref disagree on which $defs entry "
                "describes this message" % (const, ref, expected_ref)
            )

    return errors


def check_field_coverage(
    proto_set: set[str], all_messages: dict[str, list[Field]], schema: dict
) -> tuple[list[str], set[str]]:
    """Returns (errors, visited) -- `visited` is the exact set this function's
    own BFS reached (the 7 payloads plus any message-typed field reached from
    one), returned so the caller can reuse it as the scope for filtering
    unknown-construct reports, instead of re-running an equivalent BFS."""
    errors: list[str] = []
    defs = schema.get("$defs", {})

    queue: list[str] = sorted("%sPayload" % name for name in proto_set)
    visited: set[str] = set()

    while queue:
        msg_name = queue.pop(0)
        if msg_name in visited:
            continue
        visited.add(msg_name)

        fields = all_messages.get(msg_name)
        if fields is None:
            errors.append(
                "%s is referenced as a message type but has no message "
                "definition in any of core.proto/envelope.proto/policy.proto"
                % msg_name
            )
            continue

        entry = defs.get(msg_name)
        if entry is None:
            errors.append(
                "%s has no $defs.%s entry in macp-envelope.schema.json, so its "
                "field coverage cannot be checked" % (msg_name, msg_name)
            )
            properties = None
        else:
            properties = entry.get("properties")
            if properties is None:
                errors.append(
                    "$defs.%s has no \"properties\" object -- treating it as "
                    "empty would report every one of %s's fields missing as "
                    "though they were N separate defects" % (msg_name, msg_name)
                )

        # `properties is None` means the entry (or its properties) is missing
        # entirely, already reported once above -- skip the per-field check
        # so that one defect is not reported N times, one per field. The BFS
        # below still walks every field's TYPE regardless: those come from the
        # proto side, not the (possibly absent) $defs entry, so a message
        # missing its own $defs entry must not also truncate reachability for
        # whatever message-typed fields it points at.
        for field in fields:
            if (
                properties is not None
                and field.name not in properties
                and (msg_name, field.name) not in UNMAPPED_PROTO_FIELDS
            ):
                errors.append(
                    "%s.%s (%s:%d) has no corresponding property in "
                    "$defs.%s.properties"
                    % (msg_name, field.name, rel(CORE_PROTO), field.line, msg_name)
                )

            type_name = field_type_name(field.type)
            if type_name is not None and type_name not in visited:
                queue.append(type_name)

    return errors, visited


def base_shape(type_name: str) -> dict | None:
    """Expected JSON-Schema shape for one occurrence of `type_name`, ignoring
    any repeated/map wrapper -- expected_shape applies that. Returns None for
    a proto type this table has no JSON mapping for (an enum, or a scalar
    missing from SCALAR_JSON_TYPE): callers must treat None as a reportable
    error, never as "no constraint"."""
    if type_name == "bytes":
        return {"$ref": "#/$defs/Base64Bytes"}
    if type_name in SCALAR_JSON_TYPE:
        return {"type": SCALAR_JSON_TYPE[type_name]}
    if type_name in SCALAR_TYPES:
        return None
    return {"$ref": "#/$defs/%s" % type_name}


def expected_shape(field: Field) -> dict | None:
    """Expected JSON-Schema shape for `field` as a whole, repeated/map
    wrapper included. None propagates from base_shape -- an unmapped base
    type under a repeated/map wrapper is still unmapped, not "an array of
    anything"."""
    m = MAP_TYPE_RE.match(field.type)
    if m:
        value_shape = base_shape(m.group(2))
        if value_shape is None:
            return None
        return {"type": "object", "additionalProperties": value_shape}
    if field.repeated:
        item_shape = base_shape(field.type)
        if item_shape is None:
            return None
        return {"type": "array", "items": item_shape}
    return base_shape(field.type)


def shape_errors(expected: dict, actual: dict, context: str) -> list[str]:
    """Compare `actual` ($defs.<Msg>.properties.<field>) against `expected`
    on exactly type/items/additionalProperties/$ref -- the only keys
    expected_shape ever produces. Every other JSON-Schema authoring keyword
    on `actual` (required, minimum, minLength, pattern, description, format)
    has no proto counterpart and is deliberately not inspected."""
    errors: list[str] = []
    for key in ("type", "$ref"):
        if key in expected and expected[key] != actual.get(key):
            errors.append(
                "%s: expected %s %r, found %r"
                % (context, key, expected[key], actual.get(key))
            )
    if "items" in expected:
        actual_items = actual.get("items")
        if not isinstance(actual_items, dict):
            errors.append(
                "%s: expected an \"items\" object, found %r" % (context, actual_items)
            )
        else:
            errors.extend(shape_errors(expected["items"], actual_items, context + ".items"))
    if "additionalProperties" in expected:
        actual_ap = actual.get("additionalProperties")
        if not isinstance(actual_ap, dict):
            errors.append(
                "%s: expected an \"additionalProperties\" object, found %r"
                % (context, actual_ap)
            )
        else:
            errors.extend(
                shape_errors(
                    expected["additionalProperties"], actual_ap,
                    context + ".additionalProperties",
                )
            )
    return errors


def check_type_shapes(
    all_messages: dict[str, list[Field]], field_reached: set[str], schema: dict
) -> list[str]:
    """Check 5: every field on a message in `field_reached` maps to the JSON
    shape expected_shape() derives from its proto declaration. Scoped to
    field_reached, the set Check 3 already computed -- a message with no
    $defs entry at all, or a $defs entry with no "properties", or a field
    with no matching property, is already reported once by Check 3/4 and is
    skipped here rather than reported again under a different name."""
    errors: list[str] = []
    defs = schema.get("$defs", {})

    for msg_name in sorted(field_reached):
        entry = defs.get(msg_name)
        if entry is None:
            continue
        properties = entry.get("properties")
        if properties is None:
            continue
        for field in all_messages.get(msg_name, []):
            actual = properties.get(field.name)
            if actual is None:
                continue
            context = "%s.%s (%s:%d)" % (msg_name, field.name, rel(CORE_PROTO), field.line)
            expected = expected_shape(field)
            if expected is None:
                errors.append(
                    "%s has proto type %r, which has no JSON-shape mapping -- "
                    "teach SCALAR_JSON_TYPE or base_shape about it, do not "
                    "assume a shape for it" % (context, field.type)
                )
                continue
            if not isinstance(actual, dict):
                errors.append(
                    "%s: $defs.%s.properties.%s is not an object (%r)"
                    % (context, msg_name, field.name, actual)
                )
                continue
            errors.extend(shape_errors(expected, actual, context))

    return errors


def check_reverse_and_orphans(
    all_messages: dict[str, list[Field]], field_reached: set[str], schema: dict
) -> list[str]:
    """Check 6: the mirror image of Check 3. For every reached $defs entry,
    every JSON property must correspond to a real proto field -- no
    allowlist in this direction, by choice (a genuine JSON-only property
    needs an RFC updating the canonical mapping, not a dict entry here).
    Then, every $defs entry overall must be either reached or explicitly
    named in JSON_ONLY_DEFS."""
    errors: list[str] = []
    defs = schema.get("$defs", {})

    for msg_name in sorted(field_reached):
        entry = defs.get(msg_name)
        if entry is None:
            continue
        properties = entry.get("properties")
        if not properties:
            continue
        proto_field_names = {field.name for field in all_messages.get(msg_name, [])}
        for prop_name in sorted(properties):
            if prop_name not in proto_field_names:
                errors.append(
                    "$defs.%s.properties.%s has no corresponding field on "
                    "message %s -- there is no allowlist for this direction; "
                    "a genuine JSON-only property needs an RFC updating the "
                    "canonical mapping, not a dict entry here"
                    % (msg_name, prop_name, msg_name)
                )

    orphans = set(defs) - field_reached - set(JSON_ONLY_DEFS)
    for name in sorted(orphans):
        errors.append(
            "$defs.%s is not reachable from any Core payload's field graph "
            "and is not listed in JSON_ONLY_DEFS -- either wire it up or add "
            "it there with a reason" % name
        )

    return errors


# The ONLY two non-identity proto->JSON mappings in this repo, both normative
# and both envelope-level: RFC-MACP-0001 Section 10.1 (the only
# Protobuf-to-JSON field rename in the MACP envelope) and Section 10.2
# (payload bytes map to EITHER a decoded `payload` object OR `payload_b64`).
ENVELOPE_FIELD_MAP = {
    "timestamp_unix_ms": ("timestamp",),
    "payload": ("payload", "payload_b64"),
}


def check_envelope_fields(
    envelope_messages: dict[str, list[Field]], schema: dict
) -> list[str]:
    """Check 7: Envelope's own proto fields are all held to the schema's
    top-level `properties`. Six map by identity; the two in
    ENVELOPE_FIELD_MAP have a normative non-identity mapping. Does not check
    `required` or the `oneOf` -- those encode RFC-MACP-0001 §10.2's
    exactly-one rule, already enforced on instances by
    scripts/validate-json.sh."""
    errors: list[str] = []
    fields = envelope_messages.get("Envelope")
    if fields is None:
        errors.append(
            "message Envelope not found in envelope.proto -- Check 7 cannot "
            "run without it"
        )
        return errors

    top_properties = schema.get("properties", {})
    proto_field_names = {field.name for field in fields}

    for key in ENVELOPE_FIELD_MAP:
        if key not in proto_field_names:
            errors.append(
                "ENVELOPE_FIELD_MAP's key %r is not a field on message "
                "Envelope -- the proto field it named was renamed or "
                "removed; update the map, do not leave a dead entry "
                "silently satisfying this check" % key
            )

    for field in fields:
        targets = ENVELOPE_FIELD_MAP.get(field.name, (field.name,))
        if not any(target in top_properties for target in targets):
            errors.append(
                "Envelope.%s (%s:%d) has no corresponding top-level property "
                "in %s (looked for %s)"
                % (
                    field.name, rel(ENVELOPE_PROTO), field.line, rel(ENVELOPE_SCHEMA),
                    " or ".join(repr(t) for t in targets),
                )
            )

    return errors


def harvest_rpc_types(core_proto_text: str) -> set[str]:
    rpc_types: set[str] = set()
    for m in RPC_RE.finditer(core_proto_text):
        rpc_types.add(m.group(1))
        rpc_types.add(m.group(2))
    return rpc_types


def check_classification(
    proto_set: set[str],
    all_messages: dict[str, list[Field]],
    per_file_messages: dict[str, set[str]],
    rpc_types: set[str],
) -> list[str]:
    errors: list[str] = []

    payload_names = {"%sPayload" % name for name in proto_set}
    queue: list[str] = sorted(payload_names | rpc_types)
    reached: set[str] = set()

    while queue:
        name = queue.pop(0)
        if name in reached:
            continue
        reached.add(name)
        for field in all_messages.get(name, []):
            type_name = field_type_name(field.type)
            if type_name is not None and type_name not in reached:
                queue.append(type_name)

    for file_path, names in per_file_messages.items():
        for name in sorted(names):
            if name not in reached:
                errors.append(
                    "%s is neither a Core payload nor reachable from "
                    "service MACPRuntimeService's request/response surface "
                    "(%s) -- wire it up or explain why it is exempt"
                    % (name, file_path)
                )

    return errors


def main() -> int:
    for path in PROTO_FILES:
        if not path.is_file():
            fail("%s not found" % rel(path))
    if ERRORS:
        for e in ERRORS:
            print("FAIL %s" % e, file=sys.stderr)
        return 1

    core_messages, core_unknown, core_proto_text = parse_proto(CORE_PROTO)
    envelope_messages, envelope_unknown, _ = parse_proto(ENVELOPE_PROTO)
    policy_messages, policy_unknown, _ = parse_proto(POLICY_PROTO)

    all_messages: dict[str, list[Field]] = {}
    per_file_messages: dict[str, set[str]] = {}
    for path, messages in (
        (CORE_PROTO, core_messages),
        (ENVELOPE_PROTO, envelope_messages),
        (POLICY_PROTO, policy_messages),
    ):
        per_file_messages[rel(path)] = set(messages)
        for name, fields in messages.items():
            if name in all_messages:
                fail(
                    "message %s is defined more than once across "
                    "core.proto/envelope.proto/policy.proto" % name
                )
                continue
            all_messages[name] = fields

    schema = load_schema()
    if schema is None:
        for e in ERRORS:
            print("FAIL %s" % e, file=sys.stderr)
        return 1

    proto_set, errors = check_three_way_agreement(core_messages, schema)
    ERRORS.extend(errors)
    ERRORS.extend(check_defs_existence(proto_set, schema))

    field_errors, field_reached = check_field_coverage(proto_set, all_messages, schema)
    ERRORS.extend(field_errors)

    # Scope unknown-construct reporting to exactly the set check_field_coverage
    # reached (payloads + transitive message-typed fields) -- a message reached
    # only by the RPC-classification walk (Check 4) but never by this narrower
    # walk does not get its odd constructs reported (core.proto:343's oneof
    # inside StreamSessionResponse, :439's enum inside SessionLifecycleEvent --
    # neither is reached from a Core payload's own field graph).
    for msg_name, file_name, lineno, raw in core_unknown + envelope_unknown + policy_unknown:
        if msg_name in field_reached:
            fail(
                "%s:%d: unrecognised construct inside message %s: %r -- teach "
                "the parser this construct, do not loosen the field regex to "
                "tolerate it" % (file_name, lineno, msg_name, raw.strip())
            )

    rpc_types = harvest_rpc_types(core_proto_text)
    ERRORS.extend(
        check_classification(proto_set, all_messages, per_file_messages, rpc_types)
    )

    ERRORS.extend(check_type_shapes(all_messages, field_reached, schema))
    ERRORS.extend(check_reverse_and_orphans(all_messages, field_reached, schema))
    ERRORS.extend(check_envelope_fields(envelope_messages, schema))

    if ERRORS:
        for e in ERRORS:
            print("FAIL %s" % e, file=sys.stderr)
        print("\n%d error(s) found." % len(ERRORS), file=sys.stderr)
        return 1

    print(
        "All 7 envelope-coverage checks passed: %d Core payload(s) (%s) agree "
        "across proto, allOf branches and message_type's description; field "
        "coverage and shapes hold for %d reached $defs entries (%s); %d "
        "message(s) classified across the three macp/v1 protos; Envelope's "
        "own fields agree with the schema's top-level properties."
        % (
            len(proto_set), ", ".join(sorted(proto_set)),
            len(field_reached), ", ".join(sorted(field_reached)),
            sum(len(names) for names in per_file_messages.values()),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
