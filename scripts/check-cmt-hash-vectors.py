#!/usr/bin/env python3
"""Check the RFC-MACP-0013 canonical commitment hash reference vectors.

CI. Runs with bare `python3` -- no venv, no `pip install` -- so this script
imports **stdlib only** (json, hashlib, sys, pathlib). It never imports the
third-party `jcs` PyPI package; that is scripts/gen-cmt-hash-vectors.py's
job, and that script is dev-time only and never runs in CI. See
RFC-MACP-0013 Section 4 and plans/rfc-macp-0013-implementation.md Phase 2
for why the two are kept as separate files with separate dependency
budgets.

For each vector under schemas/conformance/cmt-hash/*.json (every *.json
file except vector-schema.json), this script:

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
EXPECTED_VECTOR_COUNT = 5
EXPECTED_INEQUALITY_COUNT = 1

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


def check_vector(path: Path) -> list[str]:
    """Return a list of error strings for one vector file (empty = pass)."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="ascii"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: invalid JSON: {exc}"]

    for key in ("name", "payload", "jcs_utf8_hex", "preimage_utf8_hex", "hash"):
        if key not in data:
            errors.append(f"{path.name}: missing required key '{key}'")
    if errors:
        return errors

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
        return errors

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

    return errors


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

    for path in vector_paths:
        errors = check_vector(path)
        if errors:
            all_errors.extend(errors)
            print(f"FAIL {path.name}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"ok   {path.name}  hash={json.loads(path.read_text())['hash']}")
            checked += 1
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

    # Expected-count assertions: a deleted vector file or a removed
    # must_differ_from field must not pass silently with a smaller N/M.
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
        f"\nAll {checked} commitment-hash vectors checked and "
        f"{inequalities_checked} inequality assertion(s) satisfied."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
