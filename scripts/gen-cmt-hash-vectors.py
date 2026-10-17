#!/usr/bin/env python3
"""Regenerate the RFC-MACP-0013 canonical commitment hash reference vectors.

DEV-TIME ONLY. This script imports the third-party `jcs` PyPI package
(https://pypi.org/project/jcs/, an RFC 8785 JSON Canonicalization Scheme
implementation) and is NEVER run in CI -- CI runs
scripts/check-cmt-hash-vectors.py instead, which is stdlib-only and
re-derives the same values with a hand-written serializer. See that script's
docstring and RFC-MACP-0013 Section 4 for why the two are kept separate.

Install the dependency locally before running this script:

    pip install jcs

Vectors under schemas/conformance/cmt-hash/ are GENERATED, NEVER
hand-edited. If you need to change a vector, change the inline payload
table below and re-run this script; do not edit the *.json files directly.
After running, `git diff --exit-code schemas/conformance/cmt-hash/` should
be clean if nothing was meant to change (byte-for-byte reproducibility is
part of Phase 2's acceptance criteria).

Algorithm (RFC-MACP-0013 Section 4):
    1. Project the CommitmentPayload to JSON (Section 3).
    2. Canonicalize the projection with JCS (RFC 8785) -> bytes C.
    3. Preimage P = ASCII("macp-commitment-hash/1:") || C.
    4. hash = "sha256:" + lowercase-hex(SHA-256(P)).

Vectors 001-005 are COMPUTE vectors (payload in, hash out). Vectors 006-010
are VERIFY vectors (RFC-MACP-0013 Section 6): each pins a payload's Protobuf
wire encoding (`wire_hex`), a `claimed_hash`, and the `expected_outcome`
(match | mismatch | cannot_verify) a conforming verifier MUST return. Their
values are the ones pinned by macp-runtime's
`macp_core::commitment_hash::verify_commitment_hash` crate tests.

Run: `python3 scripts/gen-cmt-hash-vectors.py`
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jcs  # third-party; dev-only, see module docstring

LABEL = "macp-commitment-hash/1"
PREIMAGE_PREFIX = b"macp-commitment-hash/1:"

OUT_DIR = Path(__file__).resolve().parent.parent / "schemas" / "conformance" / "cmt-hash"


def commitment_hash(payload: dict) -> tuple[bytes, bytes, str]:
    """Return (jcs_bytes, preimage_bytes, hash_string) for a projected payload."""
    jcs_bytes = jcs.canonicalize(payload)
    preimage = PREIMAGE_PREFIX + jcs_bytes
    digest = hashlib.sha256(preimage).hexdigest()
    return jcs_bytes, preimage, f"sha256:{digest}"


# --- Inline payload table -----------------------------------------------
# Vectors are never derived from one another in this table (H11): each is
# spelled out in full, even where it happens to share values with another
# vector, so nobody "helpfully" derives 005 from 001 by mistake.

_p001 = {
    "commitment_id": "c1",
    "action": "decision.approved",
    "authority_scope": "seam",
    "reason": "sealed by seam",
    "mode_version": "macp.mode.decision.v1",
    "policy_version": "1.0.0",
    "configuration_version": "1.0.0",
    "outcome_positive": True,
}
_, _, _hash001 = commitment_hash(_p001)

_p002 = {
    "commitment_id": "c2",
    "action": "decision.approved",
    "authority_scope": "seam",
    "reason": "sealed by seam",
    "mode_version": "macp.mode.decision.v1",
    "policy_version": "1.0.0",
    "configuration_version": "1.0.0",
    "outcome_positive": True,
    "supersedes": {
        "session_id": "prior-sess",
        "commitment_hash": _hash001,
    },
}

_p003 = {
    "commitment_id": "",
    "action": "",
    "authority_scope": "",
    "reason": "",
    "mode_version": "",
    "policy_version": "",
    "configuration_version": "",
    "outcome_positive": False,
}

_p004 = {
    "commitment_id": "",
    "action": "",
    "authority_scope": "",
    "reason": "",
    "mode_version": "",
    "policy_version": "",
    "configuration_version": "",
    "outcome_positive": False,
    "supersedes": {
        "session_id": "",
        "commitment_hash": "",
    },
}

# NOT derived from 001 (H11): outcome_positive is false and commitment_id is
# "c5". Exercises RFC 8785 3.2.2 escaping: embedded quote and backslash in
# `action`; TAB and LF short-form escapes, non-ASCII, and an astral-plane
# codepoint (U+1F702, surrogate pair D83D DF02) in `reason`.
_p005 = {
    "commitment_id": "c5",
    "action": 'decision."appro\\ved"',
    "authority_scope": "café",
    "reason": "ré\tsumé\n— naïve \U0001F702",
    "mode_version": "macp.mode.decision.v1",
    "policy_version": "1.0.0",
    "configuration_version": "1.0.0",
    "outcome_positive": False,
}

def _key(field: int, wire_type: int) -> bytes:
    """Protobuf field key as a varint (two bytes suffice for field < 2048)."""
    k = field << 3 | wire_type
    return bytes([k]) if k < 0x80 else bytes([k & 0x7F | 0x80, k >> 7])


def _len_field(field: int, body: bytes) -> bytes:
    assert len(body) < 0x80, "single-byte length only; enough for these vectors"
    return _key(field, 2) + bytes([len(body)]) + body


def encode_wire(payload: dict) -> bytes:
    """proto3 encoding of a projected CommitmentPayload: default-valued
    scalars omitted, fields in field-number order. A `_tail` key (in the
    payload or in `supersedes`) is raw wire bytes appended to that message;
    it is never projected or hashed."""
    out = b""
    for num, name in enumerate(STRING_FIELDS, start=1):
        if payload[name]:
            out += _len_field(num, payload[name].encode("utf-8"))
    if payload["outcome_positive"]:
        out += _key(8, 0) + b"\x01"
    if "supersedes" in payload:
        ref = payload["supersedes"]
        body = b""
        for num, name in ((1, "session_id"), (2, "commitment_hash")):
            if ref[name]:
                body += _len_field(num, ref[name].encode("utf-8"))
        out += _len_field(9, body + ref.get("_tail", b""))
    return out + payload.get("_tail", b"")


STRING_FIELDS = (
    "commitment_id", "action", "authority_scope", "reason",
    "mode_version", "policy_version", "configuration_version",
)

# --- Verify vectors (RFC-MACP-0013 Section 6) ----------------------------
_w001 = encode_wire(_p001)

_p006_wire = dict(_p001, _tail=_key(99, 2) + b"\x01x")  # field 99 = "x"

_p009_covered = dict(_p001, supersedes={"session_id": "s0", "commitment_hash": _hash001})
_, _, _hash009_covered = commitment_hash(_p009_covered)
_p009_wire = dict(_p001, supersedes={
    "session_id": "s0",
    "commitment_hash": _hash001,
    "_tail": _key(3, 2) + b"\x01z",  # unknown CommitmentRef field 3 = "z"
})

VERIFY_VECTORS = [
    {
        "name": "cmt_hash_006_unknown_field",
        "description": (
            "the wire of cmt_hash_001_minimal with CommitmentPayload field 99 = \"x\" "
            "appended; a field outside the frozen set (RFC-MACP-0013 Section 5) is "
            "cannot-verify, never dropped and hashed"
        ),
        "wire": encode_wire(_p006_wire),
        "claimed_hash": _hash001,
        "expected_outcome": "cannot_verify",
    },
    {
        "name": "cmt_hash_007_mismatch",
        "description": (
            "exactly the wire of cmt_hash_001_minimal; the claimed hash differs from "
            "001's hash in one hex digit"
        ),
        "wire": _w001,
        "claimed_hash": "sha256:9f59e9d114d11860d48aa2bcb8cda458b9618b1cc8560595a802b68c4af85d41",
        "expected_outcome": "mismatch",
    },
    {
        "name": "cmt_hash_008_noncanonical_claim",
        "description": (
            "the wire of cmt_hash_007_mismatch with 001's hash in uppercase hex; a "
            "claimed hash not in canonical form is mismatch, never normalized"
        ),
        "wire": _w001,
        "claimed_hash": "sha256:9F58E9D114D11860D48AA2BCB8CDA458B9618B1CC8560595A802B68C4AF85D41",
        "expected_outcome": "mismatch",
    },
    {
        "name": "cmt_hash_009_unknown_supersedes_field",
        "description": (
            "the payload of cmt_hash_001_minimal plus supersedes {session_id \"s0\", "
            "commitment_hash = 001's hash, unknown CommitmentRef field 3 = \"z\"}; the claim "
            "is the correct hash of the covered payload WITHOUT field 3, so a verifier that "
            "drops unknown fields reports match where a conforming one reports cannot-verify"
        ),
        "wire": encode_wire(_p009_wire),
        "claimed_hash": _hash009_covered,
        "expected_outcome": "cannot_verify",
    },
    {
        "name": "cmt_hash_010_no_prefix",
        "description": (
            "the wire of cmt_hash_007_mismatch with 001's hex digits and no sha256: "
            "prefix; mismatch, never an error -- cannot-verify is reserved for the "
            "payload encoding, never the claim"
        ),
        "wire": _w001,
        "claimed_hash": "9f58e9d114d11860d48aa2bcb8cda458b9618b1cc8560595a802b68c4af85d41",
        "expected_outcome": "mismatch",
    },
]

VECTORS = [
    {
        "name": "cmt_hash_001_minimal",
        "description": "baseline; no supersedes",
        "payload": _p001,
    },
    {
        "name": "cmt_hash_002_supersedes",
        "description": (
            "= cmt_hash_001_minimal with commitment_id \"c2\" and supersedes chained to "
            "001's own hash; inside supersedes, JCS sorts commitment_hash before session_id"
        ),
        "payload": _p002,
    },
    {
        "name": "cmt_hash_003_all_empty",
        "description": "every string field \"\", outcome_positive false, no supersedes",
        "payload": _p003,
    },
    {
        "name": "cmt_hash_004_empty_supersedes",
        "description": (
            "identical to cmt_hash_003_all_empty except supersedes is present with both "
            "session_id and commitment_hash set to \"\" -- not well-formed per "
            "RFC-MACP-0001 7.3.1, but hashable per RFC-MACP-0013 Section 6"
        ),
        "payload": _p004,
        "must_differ_from": "cmt_hash_003_all_empty",
    },
    {
        "name": "cmt_hash_005_escapes",
        "description": (
            "RFC 8785 3.2.2 escaping: embedded quote/backslash, tab/newline short-form "
            "escapes, non-ASCII, and an astral-plane codepoint; NOT derived from 001"
        ),
        "payload": _p005,
    },
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for vector in VECTORS:
        payload = vector["payload"]
        jcs_bytes, preimage, digest = commitment_hash(payload)
        out = {
            "name": vector["name"],
            "description": vector["description"],
            "label": LABEL,
            "payload": payload,
            "jcs_utf8_hex": jcs_bytes.hex(),
            "preimage_utf8_hex": preimage.hex(),
            "hash": digest,
        }
        if "must_differ_from" in vector:
            out["must_differ_from"] = vector["must_differ_from"]
        out_path = OUT_DIR / f"{vector['name']}.json"
        # ensure_ascii=True: the vector pack must be pure ASCII on disk (H11 /
        # Phase 2 approach notes) -- vector 005 contains a literal backslash and
        # an astral-plane codepoint that a well-meaning formatter can mangle.
        text = json.dumps(out, indent=2, ensure_ascii=True, sort_keys=False) + "\n"
        out_path.write_text(text, encoding="ascii")
        print(f"wrote {out_path.relative_to(OUT_DIR.parent.parent.parent)}  hash={digest}")
    for vector in VERIFY_VECTORS:
        out = {
            "name": vector["name"],
            "description": vector["description"],
            "label": LABEL,
            "wire_hex": vector["wire"].hex(),
            "claimed_hash": vector["claimed_hash"],
            "expected_outcome": vector["expected_outcome"],
        }
        out_path = OUT_DIR / f"{vector['name']}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
        print(f"wrote {out_path.relative_to(OUT_DIR.parent.parent.parent)}  "
              f"outcome={vector['expected_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
