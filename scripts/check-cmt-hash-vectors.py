#!/usr/bin/env python3
"""Check the RFC-MACP-0013 canonical commitment hash reference vectors.

CI. Runs with bare `python3` -- no venv, no `pip install` -- so this script
imports **stdlib only** (json, hashlib, sys, pathlib). It never imports the
third-party `jcs` PyPI package (or `protobuf`); `jcs` is scripts/gen-cmt-hash-vectors.py's
job, and that script is dev-time only and never runs in CI. See
RFC-MACP-0013 Section 4 and plans/rfc-macp-0013-implementation.md Phase 2
for why the two are kept as separate files with separate dependency
budgets.

For each compute vector under schemas/conformance/cmt-hash/*.json (every
*.json file except vector-schema.json), this script:

  1. Re-derives the RFC 8785 JCS canonicalization of the vector's `payload`
     field with a hand-written ~40-line serializer (see `jcs_canonicalize`
     below), using the subset RFC-MACP-0013 Section 4's normative subset
     note permits: strings, exactly one boolean, and one optional nested
     object -- no JSON numbers, no JSON arrays. Because every member name
     in the frozen field set (RFC-MACP-0013 Section 5) is ASCII, RFC 8785's
     UTF-16-code-unit key-ordering rule reduces, for member names, to plain
     string sort.
  2. Re-derives the domain-separated preimage and the SHA-256 hash.
  3. Diffs all three (jcs_utf8_hex, preimage_utf8_hex, hash) against the
     vector's pinned fields and reports the first point of divergence.
  4. Enforces every vector's `must_differ_from` field as an inequality
     assertion: this is the machine-checked "003 != 004" requirement of
     RFC-MACP-0013 Section 11 -- two passing equality checks do not, by
     themselves, prove the unset-vs-empty distinction (Section 3, rule 3)
     is actually implemented.
  5. Verifies every vector through RFC-MACP-0013 Section 6's verification
     operation, using a minimal stdlib-only Protobuf wire decoder for
     CommitmentPayload/CommitmentRef (see `verify` below). A VERIFY vector
     (006-010: `wire_hex`, `claimed_hash`, `expected_outcome`) must return
     its `expected_outcome`; a COMPUTE vector (001-005) is re-encoded to wire
     and must return *match* on its own pinned hash. A short list of inline
     self-checks pins the three Section 6 wire-decoding rules (malformed is
     cannot-verify; repeated known fields merge; zero-length is vector 003)
     and the non-canonical-claim-is-mismatch rule.

Run: `python3 scripts/check-cmt-hash-vectors.py` (exits non-zero on any
mismatch or missing must_differ_from inequality).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

VECTORS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "conformance" / "cmt-hash"
PREIMAGE_PREFIX = b"macp-commitment-hash/1:"

# RFC-MACP-0013 Section 5's frozen nine-field constraint (D5): a
# CommitmentPayload projection MUST contain exactly these fields and no
# others. A payload carrying an unrecognized field is not a valid input to
# the Section 4 algorithm and MUST be treated as cannot-verify (Section 5)
# rather than silently hashed.
ALLOWED_PAYLOAD_FIELDS = {
    "commitment_id",
    "action",
    "authority_scope",
    "reason",
    "mode_version",
    "policy_version",
    "configuration_version",
    "outcome_positive",
    "supersedes",
}
ALLOWED_SUPERSEDES_FIELDS = {"session_id", "commitment_hash"}

# Expected shape of the fixture pack (RFC-MACP-0013 Section 11). These are
# asserted after processing so a silently-deleted vector file, or a silently
# -removed must_differ_from field, fails the run instead of just shrinking
# the reported N/M counts.
EXPECTED_VECTOR_COUNT = 10
EXPECTED_INEQUALITY_COUNT = 1
# Compute vectors 001-005 count as match (their own hash, verified through
# the wire path); verify vectors 006-010 count as their expected_outcome.
EXPECTED_OUTCOME_COUNTS = {"match": 5, "mismatch": 3, "cannot_verify": 2}

# RFC 8785 Section 3.2.2.2: short-form escapes for these control characters;
# everything else below 0x20 gets a \u00XX escape. `"` and `\` are always
# escaped. Everything at or above 0x20 (including non-ASCII and astral-plane
# codepoints) is emitted as literal UTF-8.
_SHORT_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\",
}


def jcs_escape_string(s: str) -> str:
    """RFC 8785 Section 3.2.2.2 string escaping for our subset (no arrays,
    no numbers -- this function only ever sees string *values*)."""
    out = ["\""]
    for ch in s:
        cp = ord(ch)
        if cp in _SHORT_ESCAPES:
            out.append(_SHORT_ESCAPES[cp])
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append("\"")
    return "".join(out)


def jcs_canonicalize(obj) -> bytes:
    """Hand-written RFC 8785 JCS serializer restricted to the subset
    RFC-MACP-0013 Section 4 requires: JSON objects, strings, and booleans.
    No numbers, no arrays, no null -- those are unreachable on a conforming
    CommitmentPayload projection and are intentionally not supported here.
    """
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if isinstance(obj, str):
        return jcs_escape_string(obj).encode("utf-8")
    if isinstance(obj, dict):
        # Member names in the frozen field set (RFC-MACP-0013 Section 5) are
        # all ASCII, so RFC 8785's UTF-16-code-unit key-ordering rule
        # reduces to plain string sort for our purposes.
        keys = sorted(obj.keys())
        parts = []
        for key in keys:
            parts.append(jcs_escape_string(key).encode("utf-8") + b":" + jcs_canonicalize(obj[key]))
        return b"{" + b",".join(parts) + b"}"
    raise TypeError(
        f"unsupported type {type(obj).__name__} in commitment-hash projection "
        "(only string, bool, and object are valid per RFC-MACP-0013 Section 4)"
    )


def compute_hash(payload: dict) -> tuple[bytes, bytes, str]:
    jcs_bytes = jcs_canonicalize(payload)
    preimage = PREIMAGE_PREFIX + jcs_bytes
    digest = hashlib.sha256(preimage).hexdigest()
    return jcs_bytes, preimage, f"sha256:{digest}"


# --- Verification (RFC-MACP-0013 Section 6) ------------------------------
# A minimal, dependency-free Protobuf wire decoder for exactly
# CommitmentPayload and CommitmentRef. Any field number outside the frozen
# set, at either level, and any encoding that does not parse, raises
# CannotVerify. Repeated known fields follow Protobuf merge semantics.

STRING_FIELDS = (
    "commitment_id", "action", "authority_scope", "reason",
    "mode_version", "policy_version", "configuration_version",
)
REF_FIELDS = {1: ("session_id", "string"), 2: ("commitment_hash", "string")}
PAYLOAD_FIELDS = {
    **{n: (name, "string") for n, name in enumerate(STRING_FIELDS, start=1)},
    8: ("outcome_positive", "bool"),
    9: ("supersedes", "ref"),
}
OUTCOMES = ("match", "mismatch", "cannot_verify")


class CannotVerify(Exception):
    pass


def _read_varint(buf: bytes, i: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):  # at most 10 bytes
        if i >= len(buf):
            break
        byte = buf[i]
        i += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, i
    raise CannotVerify("truncated or over-long varint")


def _decode(buf: bytes, fields: dict) -> dict:
    out: dict = {}
    i = 0
    while i < len(buf):
        key, i = _read_varint(buf, i)
        number, wire_type = key >> 3, key & 7
        if number == 0:
            raise CannotVerify("field number 0")
        if number not in fields:
            raise CannotVerify(f"unknown field {number}")
        name, kind = fields[number]
        if wire_type != (0 if kind == "bool" else 2):
            raise CannotVerify(f"field {number} has wrong wire type {wire_type}")
        value, i = _read_varint(buf, i)
        if kind == "bool":
            out[name] = value != 0  # last scalar wins
            continue
        if i + value > len(buf):
            raise CannotVerify(f"field {number} runs past the end")
        body, i = buf[i:i + value], i + value
        if kind == "string":
            try:
                out[name] = body.decode("utf-8")  # strict: rejects invalid UTF-8
            except UnicodeDecodeError as exc:
                raise CannotVerify(f"field {number}: invalid UTF-8") from exc
        else:  # a message field merges with any earlier occurrence
            out[name] = {**out.get(name, {}), **_decode(body, REF_FIELDS)}
    return out


def decode_payload(wire: bytes) -> dict:
    """Decode a CommitmentPayload into its Section 3 projection."""
    d = _decode(wire, PAYLOAD_FIELDS)
    payload = {name: d.get(name, "") for name in STRING_FIELDS}
    payload["outcome_positive"] = d.get("outcome_positive", False)
    if "supersedes" in d:
        ref = d["supersedes"]
        payload["supersedes"] = {k: ref.get(k, "") for k in ("session_id", "commitment_hash")}
    return payload


def verify(wire: bytes, claimed: str) -> str:
    """RFC-MACP-0013 Section 6: exactly one of match | mismatch | cannot_verify.
    The claim is compared as an exact string, so a non-canonical claim is
    mismatch; cannot_verify is reserved for the payload encoding."""
    try:
        payload = decode_payload(wire)
    except CannotVerify:
        return "cannot_verify"
    return "match" if claimed == compute_hash(payload)[2] else "mismatch"


def _len_field(number: int, body: bytes) -> bytes:
    out = bytearray([number << 3 | 2])
    n = len(body)
    while n >= 0x80:
        out.append(n & 0x7F | 0x80)
        n >>= 7
    return bytes(out) + bytes([n]) + body


def encode_payload(payload: dict) -> bytes:
    """proto3 encoding of a projection (defaults omitted). Used to hold every
    compute vector to *match* on its own pinned hash through the wire path."""
    out = b"".join(
        _len_field(n, payload[name].encode("utf-8"))
        for n, name in enumerate(STRING_FIELDS, start=1) if payload[name]
    )
    if payload["outcome_positive"]:
        out += b"\x40\x01"
    if "supersedes" in payload:
        ref = payload["supersedes"]
        out += _len_field(9, b"".join(
            _len_field(n, ref[k].encode("utf-8"))
            for n, k in ((1, "session_id"), (2, "commitment_hash")) if ref[k]
        ))
    return out


def verify_self_checks(by_name: dict) -> list[str]:
    """Pin the three Section 6 wire-decoding rules and the non-canonical-claim
    rule against cases the vector files do not spell out."""
    try:
        h1, h2, h3 = (by_name[n]["hash"] for n in (
            "cmt_hash_001_minimal", "cmt_hash_002_supersedes", "cmt_hash_003_all_empty"))
        p2 = by_name["cmt_hash_002_supersedes"]["payload"]
        w1 = encode_payload(by_name["cmt_hash_001_minimal"]["payload"])
    except (KeyError, TypeError):
        return ["self-checks: compute vectors 001-003 are missing or malformed"]
    ref = p2["supersedes"]
    split_ref = (encode_payload({**p2, "supersedes": {**ref, "commitment_hash": ""}})
                 + _len_field(9, _len_field(2, ref["commitment_hash"].encode())))
    cases = [
        ("rule 3: zero-length wire is vector 003", b"", h3, "match"),
        ("rule 1: truncated string body", w1[:-3], h1, "cannot_verify"),
        ("rule 1: key with no length", b"\x0a", h1, "cannot_verify"),
        ("rule 1: truncated varint", b"\x40\x80", h1, "cannot_verify"),
        ("rule 1: group wire type", b"\x0b", h1, "cannot_verify"),
        ("rule 1: field number 0", b"\x00\x00", h1, "cannot_verify"),
        ("rule 1: invalid UTF-8", b"\x0a\x01\xff", h1, "cannot_verify"),
        ("rule 1: known field, wrong wire type", b"\x0d\x00\x00\x00\x00", h1, "cannot_verify"),
        ("rule 2: last scalar wins", b"\x0a\x02zz\x40\x00" + w1, h1, "match"),
        ("rule 2: supersedes merges", split_ref, h2, "match"),
        ("non-canonical claim: SHA256: prefix", w1, "SHA256:" + h1[7:], "mismatch"),
        ("non-canonical claim: leading space", w1, " " + h1, "mismatch"),
        ("non-canonical claim: trailing newline", w1, h1 + "\n", "mismatch"),
    ]
    errors = []
    for label, wire, claimed, expected in cases:
        got = verify(wire, claimed)
        print(f"{'ok  ' if got == expected else 'FAIL'} self-check {label}: {got}")
        if got != expected:
            errors.append(f"self-check '{label}': expected {expected}, got {got}")
    return errors


def check_verify_vector(path: Path, data: dict) -> tuple[list[str], str | None]:
    errors = [f"{path.name}: verify vector missing '{k}'"
              for k in ("wire_hex", "claimed_hash", "expected_outcome") if k not in data]
    errors += [f"{path.name}: verify vector must not carry compute field '{k}'"
               for k in ("payload", "jcs_utf8_hex", "preimage_utf8_hex", "hash") if k in data]
    if errors:
        return errors, None
    if data["expected_outcome"] not in OUTCOMES:
        return [f"{path.name}: expected_outcome must be one of {OUTCOMES}"], None
    try:
        wire = bytes.fromhex(data["wire_hex"])
    except (TypeError, ValueError):
        return [f"{path.name}: wire_hex is not hex"], None
    if wire.hex() != data["wire_hex"]:
        return [f"{path.name}: wire_hex must be lowercase hex"], None
    got = verify(wire, data["claimed_hash"])
    if got != data["expected_outcome"]:
        return [f"{path.name}: expected_outcome={data['expected_outcome']!r} "
                f"but verification returned {got!r}"], None
    return [], got


def check_vector(path: Path) -> tuple[list[str], str | None]:
    """Return (errors, verification outcome) for one vector file. A compute
    vector's outcome is that of verifying its own pinned hash, which MUST be
    match."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="ascii"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: invalid JSON: {exc}"], None
    if data.get("name") != path.stem:
        return [f"{path.name}: 'name' must equal the file basename"], None
    if "wire_hex" in data or "expected_outcome" in data or "claimed_hash" in data:
        return check_verify_vector(path, data)

    for key in ("name", "payload", "jcs_utf8_hex", "preimage_utf8_hex", "hash"):
        if key not in data:
            errors.append(f"{path.name}: missing required key '{key}'")
    if errors:
        return errors, None

    # Frozen nine-field constraint (RFC-MACP-0013 Section 5, D5): any
    # unrecognized top-level payload field -- or unrecognized field nested
    # under 'supersedes' -- means this payload is not a valid input to the
    # Section 4 algorithm at all, so we fail loudly here instead of hashing
    # it and reporting a misleadingly "valid" canonical hash.
    payload = data["payload"]
    if isinstance(payload, dict):
        for field in payload:
            if field not in ALLOWED_PAYLOAD_FIELDS:
                errors.append(
                    f"{path.name}: payload has unrecognized field '{field}' -- "
                    "RFC-MACP-0013 Section 5's frozen field set permits only "
                    f"{sorted(ALLOWED_PAYLOAD_FIELDS)}"
                )
        supersedes = payload.get("supersedes")
        if isinstance(supersedes, dict):
            for field in supersedes:
                if field not in ALLOWED_SUPERSEDES_FIELDS:
                    errors.append(
                        f"{path.name}: payload.supersedes has unrecognized field '{field}' -- "
                        f"RFC-MACP-0013 Section 5 permits only {sorted(ALLOWED_SUPERSEDES_FIELDS)}"
                    )
    if errors:
        return errors, None

    jcs_bytes, preimage, digest = compute_hash(data["payload"])

    if jcs_bytes.hex() != data["jcs_utf8_hex"]:
        errors.append(
            f"{path.name}: jcs_utf8_hex mismatch: "
            f"pinned={data['jcs_utf8_hex']!r} recomputed={jcs_bytes.hex()!r}"
        )
    if preimage.hex() != data["preimage_utf8_hex"]:
        errors.append(
            f"{path.name}: preimage_utf8_hex mismatch: "
            f"pinned={data['preimage_utf8_hex']!r} recomputed={preimage.hex()!r}"
        )
    if digest != data["hash"]:
        errors.append(f"{path.name}: hash mismatch: pinned={data['hash']!r} recomputed={digest!r}")

    # A compute vector keeps meaning *match* on its own hash: encode the
    # payload, verify it through the wire path, and require match.
    outcome = verify(encode_payload(data["payload"]), data["hash"])
    if outcome != "match":
        errors.append(f"{path.name}: verifying the pinned hash over the payload's wire "
                      f"encoding returned {outcome!r}, expected 'match'")
    return errors, outcome


def main() -> int:
    vector_paths = sorted(
        p for p in VECTORS_DIR.glob("*.json") if p.name != "vector-schema.json"
    )
    if not vector_paths:
        print(f"No vectors found in {VECTORS_DIR}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    vectors_by_name: dict[str, dict] = {}
    checked = 0
    outcome_counts = {o: 0 for o in OUTCOMES}

    for path in vector_paths:
        errors, outcome = check_vector(path)
        if errors:
            all_errors.extend(errors)
            print(f"FAIL {path.name}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"ok   {path.name}  outcome={outcome}")
            checked += 1
            outcome_counts[outcome] += 1
        try:
            data = json.loads(path.read_text(encoding="ascii"))
            vectors_by_name[data.get("name", path.stem)] = data
        except (OSError, json.JSONDecodeError):
            pass

    # must_differ_from: machine-checked inequality assertions.
    inequalities_checked = 0
    for name, data in vectors_by_name.items():
        target_name = data.get("must_differ_from")
        if target_name is None:
            continue
        target = vectors_by_name.get(target_name)
        if target is None:
            msg = f"{name}: must_differ_from references unknown vector '{target_name}'"
            print(f"FAIL {name} must_differ_from {target_name}")
            print(f"  - {msg}")
            all_errors.append(msg)
            continue
        inequalities_checked += 1
        if data.get("hash") == target.get("hash"):
            msg = (
                f"{name}: must_differ_from '{target_name}' FAILED -- both hash to {data.get('hash')!r} "
                "(unset-vs-empty distinction is not being enforced)"
            )
            print(f"FAIL {name} != {target_name}  (must_differ_from)")
            print(f"  - {msg}")
            all_errors.append(msg)
        else:
            print(f"ok   {name} != {target_name}  (must_differ_from satisfied)")

    all_errors.extend(verify_self_checks(vectors_by_name))

    # Expected-count assertions: a deleted vector file, a removed
    # must_differ_from field, or a vector whose expected_outcome was edited
    # must not pass silently with a smaller N/M.
    if outcome_counts != EXPECTED_OUTCOME_COUNTS:
        msg = f"expected outcomes {EXPECTED_OUTCOME_COUNTS}, found {outcome_counts}"
        print(f"FAIL outcome count: {msg}", file=sys.stderr)
        all_errors.append(msg)
    if len(vector_paths) != EXPECTED_VECTOR_COUNT:
        msg = (
            f"expected {EXPECTED_VECTOR_COUNT} vector files, found {len(vector_paths)} "
            "-- a vector may be missing"
        )
        print(f"FAIL vector count: {msg}", file=sys.stderr)
        all_errors.append(msg)
    if inequalities_checked != EXPECTED_INEQUALITY_COUNT:
        msg = (
            f"expected {EXPECTED_INEQUALITY_COUNT} inequality assertion(s), found "
            f"{inequalities_checked} -- must_differ_from may have been removed"
        )
        print(f"FAIL inequality count: {msg}", file=sys.stderr)
        all_errors.append(msg)

    if all_errors:
        print(f"\n{len(all_errors)} error(s) found.", file=sys.stderr)
        return 1

    print(
        f"\nAll {checked} commitment-hash vectors checked ({outcome_counts}), "
        f"{inequalities_checked} inequality assertion(s) and the verify self-checks satisfied."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
