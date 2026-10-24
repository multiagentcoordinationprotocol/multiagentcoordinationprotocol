#!/usr/bin/env python3
"""Generate the mode-as-tool schemas in schemas/json/tools/ from the mode protos.

One tool definition is written per mode message type, i.e. per `*Payload`
message in schemas/proto/macp/modes/<mode>/v1/<mode>.proto. Each file has the
shape Anthropic tool use expects ({name, description, input_schema}), which
maps one-to-one onto OpenAI function calling (see schemas/json/tools/README.md).

Source of truth is protoc itself: the protos are compiled with
`--include_source_info` into a FileDescriptorSet, which this script decodes
with a minimal protobuf wire reader (stdlib only, so CI needs nothing beyond
the protoc it already installs). Field types, field order and comments all
come from that descriptor set; nothing is written by hand.

Comment conventions read from the protos:
  * A message's description is the first paragraph of its leading comment.
  * A field's description is its whole leading comment.
  * A comment line of the form `Values: A | B | C` becomes a JSON Schema
    `enum` and is removed from the description text.

Usage:
  python3 scripts/gen-tool-schemas.py           # rewrite schemas/json/tools/
  python3 scripts/gen-tool-schemas.py --check   # regenerate in memory and diff
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.join(ROOT, "schemas", "proto")
MODES_DIR = os.path.join(PROTO_DIR, "macp", "modes")
OUT_DIR = os.path.join(ROOT, "schemas", "json", "tools")
INDEX_NAME = "index.json"

# Proto package -> mode identifier (registries/modes.md).
MODE_IDS = {
    "macp.modes.decision.v1": "macp.mode.decision.v1",
    "macp.modes.proposal.v1": "macp.mode.proposal.v1",
    "macp.modes.task.v1": "macp.mode.task.v1",
    "macp.modes.handoff.v1": "macp.mode.handoff.v1",
    "macp.modes.quorum.v1": "macp.mode.quorum.v1",
    "macp.modes.multi_round.v1": "ext.multi_round.v1",
}

# Tool names must satisfy both Anthropic and OpenAI.
NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
VALUES_RE = re.compile(r"^Values:\s*(.+)$")

# FieldDescriptorProto.Type -> JSON Schema type, following the canonical JSON
# mapping (RFC-MACP-0001 Section 10). bytes is a base64 string (Section 10.3).
TYPE_MAP = {
    1: "number",    # TYPE_DOUBLE
    2: "number",    # TYPE_FLOAT
    3: "integer",   # TYPE_INT64
    4: "integer",   # TYPE_UINT64
    5: "integer",   # TYPE_INT32
    8: "boolean",   # TYPE_BOOL
    9: "string",    # TYPE_STRING
    12: "string",   # TYPE_BYTES
    13: "integer",  # TYPE_UINT32
}
TYPE_BYTES = 12
LABEL_REPEATED = 3


def fail(msg):
    print("gen-tool-schemas: " + msg, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- wire reader

def read_varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def fields(buf):
    """Yield (field_number, wire_type, value) for one encoded message."""
    i = 0
    while i < len(buf):
        key, i = read_varint(buf, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            val, i = read_varint(buf, i)
        elif wt == 1:
            val, i = buf[i:i + 8], i + 8
        elif wt == 2:
            n, i = read_varint(buf, i)
            val, i = buf[i:i + n], i + n
        elif wt == 5:
            val, i = buf[i:i + 4], i + 4
        else:
            fail("unsupported wire type %d in descriptor set" % wt)
        yield num, wt, val


def packed_varints(buf):
    out, i = [], 0
    while i < len(buf):
        v, i = read_varint(buf, i)
        out.append(v)
    return out


# ---------------------------------------------------------- descriptor model

def parse_field(buf):
    f = {"label": 1, "proto3_optional": False}
    for num, _, val in fields(buf):
        if num == 1:
            f["name"] = val.decode()
        elif num == 4:
            f["label"] = val
        elif num == 5:
            f["type"] = val
        elif num == 6:
            f["type_name"] = val.decode()
        elif num == 17:
            f["proto3_optional"] = bool(val)
    return f


def parse_message(buf):
    m = {"fields": [], "nested": 0, "enums": 0}
    for num, _, val in fields(buf):
        if num == 1:
            m["name"] = val.decode()
        elif num == 2:
            m["fields"].append(parse_field(val))
        elif num == 3:
            m["nested"] += 1
        elif num == 4:
            m["enums"] += 1
    return m


def parse_file(buf):
    fd = {"messages": [], "comments": {}}
    for num, _, val in fields(buf):
        if num == 1:
            fd["name"] = val.decode()
        elif num == 2:
            fd["package"] = val.decode()
        elif num == 4:
            fd["messages"].append(parse_message(val))
        elif num == 9:
            for lnum, _, loc in fields(val):
                if lnum != 1:
                    continue
                path, leading = None, None
                for pnum, pwt, pval in fields(loc):
                    if pnum == 1:
                        path = tuple(packed_varints(pval) if pwt == 2 else [pval])
                    elif pnum == 3:
                        leading = pval.decode()
                if path is not None and leading is not None:
                    fd["comments"][path] = leading
    return fd


def load_descriptors():
    if shutil.which("protoc") is None:
        fail("protoc is not installed (make install-tools)")
    protos = []
    for dirpath, _, names in os.walk(MODES_DIR):
        protos += [os.path.join(dirpath, n) for n in names if n.endswith(".proto")]
    protos.sort()
    if not protos:
        fail("no mode protos under " + MODES_DIR)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "modes.pb")
        subprocess.run(
            ["protoc", "--proto_path=" + PROTO_DIR, "--include_source_info",
             "--descriptor_set_out=" + out] + protos,
            check=True,
        )
        with open(out, "rb") as fh:
            data = fh.read()
    return [parse_file(val) for num, _, val in fields(data) if num == 1]


# ------------------------------------------------------------------ comments

def comment_lines(text):
    return [line.strip() for line in (text or "").strip("\n").split("\n")]


def split_values(lines):
    """Remove a `Values: A | B` line; return (remaining_lines, enum_or_None)."""
    enum, kept = None, []
    for line in lines:
        m = VALUES_RE.match(line)
        if m:
            if enum is not None:
                fail("more than one Values: line in a comment")
            enum = [v.strip() for v in m.group(1).split("|")]
        else:
            kept.append(line)
    return kept, enum


def paragraphs(lines):
    paras, cur = [], []
    for line in lines:
        if line:
            cur.append(line)
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


# ----------------------------------------------------------------- generator

def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def build():
    tools, index = {}, []
    for fd in load_descriptors():
        pkg = fd.get("package", "")
        if pkg not in MODE_IDS:
            fail("no mode identifier mapped for package %r (%s)" % (pkg, fd.get("name")))
        mode_id = MODE_IDS[pkg]
        mode_short = pkg.split(".")[2]
        for mi, msg in enumerate(fd["messages"]):
            if not msg["name"].endswith("Payload"):
                continue
            if msg["nested"] or msg["enums"]:
                fail("%s.%s: nested types are not supported" % (pkg, msg["name"]))
            message_type = msg["name"][: -len("Payload")]
            action = snake(message_type)
            if action.startswith(mode_short + "_"):
                action = action[len(mode_short) + 1:]
            name = "macp_%s_%s" % (mode_short, action)
            if not NAME_RE.match(name):
                fail("tool name %r is not a valid tool name" % name)

            lines, enum = split_values(comment_lines(fd["comments"].get((4, mi))))
            if enum is not None:
                fail("%s.%s: Values: is only meaningful on fields" % (pkg, msg["name"]))
            paras = paragraphs(lines)
            if not paras:
                fail("%s.%s has no leading comment to describe it" % (pkg, msg["name"]))
            description = "%s Sent as message_type %s in mode %s." % (
                paras[0], message_type, mode_id)

            props, required = {}, []
            for fi, f in enumerate(msg["fields"]):
                where = "%s.%s.%s" % (pkg, msg["name"], f["name"])
                if f["type"] not in TYPE_MAP:
                    fail("%s: field type %d is not supported" % (where, f["type"]))
                flines, fenum = split_values(comment_lines(fd["comments"].get((4, mi, 2, fi))))
                ftext = " ".join(paragraphs(flines))
                if not ftext:
                    fail("%s has no leading comment to describe it" % where)
                if f["type"] == TYPE_BYTES:
                    ftext += " Base64-encoded (RFC-MACP-0001 Section 10.3)."
                schema = {"type": TYPE_MAP[f["type"]]}
                if fenum is not None:
                    if f["type"] != 9:
                        fail("%s: Values: is only supported on string fields" % where)
                    schema["enum"] = fenum
                if f["label"] == LABEL_REPEATED:
                    schema = {"type": "array", "items": schema}
                schema = dict({"description": ftext}, **schema)
                props[f["name"]] = schema
                if not f["proto3_optional"]:
                    required.append(f["name"])

            input_schema = {"type": "object", "properties": props}
            if required:
                input_schema["required"] = required
            input_schema["additionalProperties"] = False
            fname = "%s.%s.json" % (mode_short, message_type)
            if fname in tools:
                fail("duplicate tool file " + fname)
            tools[fname] = {"name": name, "description": description,
                            "input_schema": input_schema}
            index.append({"name": name, "file": fname, "mode": mode_id,
                          "message_type": message_type,
                          "payload_type": "%s.%s" % (pkg, msg["name"])})
    if not tools:
        fail("no *Payload messages found")
    index.sort(key=lambda e: e["file"])
    tools[INDEX_NAME] = {
        "_comment": "Generated by scripts/gen-tool-schemas.py from the mode protos. Do not edit.",
        "tools": index,
    }
    return {k: json.dumps(v, indent=2, ensure_ascii=False) + "\n" for k, v in tools.items()}


def on_disk():
    if not os.path.isdir(OUT_DIR):
        return {}
    out = {}
    for n in os.listdir(OUT_DIR):
        if n.endswith(".json"):
            with open(os.path.join(OUT_DIR, n), encoding="utf-8") as fh:
                out[n] = fh.read()
    return out


def main(argv):
    check = "--check" in argv[1:]
    want = build()
    have = on_disk()
    if check:
        problems = []
        for n in sorted(set(want) - set(have)):
            problems.append("missing: schemas/json/tools/" + n)
        for n in sorted(set(have) - set(want)):
            problems.append("stale (not generated): schemas/json/tools/" + n)
        for n in sorted(set(want) & set(have)):
            if want[n] != have[n]:
                problems.append("differs from generated: schemas/json/tools/" + n)
        if problems:
            for p in problems:
                print("  " + p, file=sys.stderr)
            fail("schemas/json/tools/ is out of date; run `make gen-tool-schemas` and commit")
        print("✓ schemas/json/tools/ matches the mode protos (%d tools)" % (len(want) - 1))
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    for n in set(have) - set(want):
        os.remove(os.path.join(OUT_DIR, n))
    for n, text in want.items():
        with open(os.path.join(OUT_DIR, n), "w", encoding="utf-8") as fh:
            fh.write(text)
    print("Wrote %d tool schemas to schemas/json/tools/" % (len(want) - 1))


if __name__ == "__main__":
    main(sys.argv)
