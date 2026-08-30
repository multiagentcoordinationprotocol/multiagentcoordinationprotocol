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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
