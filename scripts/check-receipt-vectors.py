#!/usr/bin/env python3
"""Check the RFC-MACP-0013 Appendix A decision-receipt reference vectors.

CI. Stdlib only, like check-cmt-hash-vectors.py, whose JCS serializer and
Section 6.1 wire decoder this script reuses for the Commitment itself. On top
of those it carries its own pieces, written independently of
scripts/gen-receipt-vectors.py (which uses the `jcs` and `cryptography`
packages):

  - a JCS serializer for the receipt body, which, unlike the Section 3
    projection, contains non-negative integers (`rev`, `message_count`);
  - an RFC 8032 Ed25519 verifier (and the scalar multiply needed to derive
    the Appendix A.5 example key from its seed);
  - a reference Appendix A.4 verifier.

For every vector under schemas/conformance/receipt/ (all *.json except
vector-schema.json) it runs the reference verifier on `receipt` with
`trusted_keys` and compares the result with `expected`. It also checks that:

  - the file name matches `name`;
  - `trusted_keys.example-1` is the key Appendix A.5 derives from its seed;
  - vector 001's receipt is byte-for-byte examples/discovery/decision_receipt.json,
    so the signed example in the RFC cannot drift from the vectors;
  - every A.4 outcome appears in at least one vector, so a vector cannot be
    deleted without anyone noticing that an outcome went untested.

Run: `python3 scripts/check-receipt-vectors.py`
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VECTORS_DIR = ROOT / "schemas" / "conformance" / "receipt"
EXAMPLE = ROOT / "examples" / "discovery" / "decision_receipt.json"

_spec = importlib.util.spec_from_file_location("cmt", ROOT / "scripts" / "check-cmt-hash-vectors.py")
cmt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmt)

FORMAT = "macp-receipt/1"
INTEGRITY = {"match", "mismatch", "cannot_verify"}
ATTESTATION = {"valid", "invalid", "unknown_key", "unsupported"}
VERDICT = {"attested", "integrity_only", "unverified", "refused"}


# --- JCS for the receipt body (RFC 8785) ---------------------------------

def jcs(obj) -> bytes:
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if isinstance(obj, int):
        if obj < 0:
            raise ValueError("receipt bodies carry only non-negative integers")
        return str(obj).encode()
    if isinstance(obj, str):
        return cmt.jcs_escape_string(obj).encode("utf-8")
    if isinstance(obj, dict):
        # All member names in the receipt format are ASCII, so UTF-16 code-unit
        # order is plain string order.
        return b"{" + b",".join(
            cmt.jcs_escape_string(k).encode("utf-8") + b":" + jcs(obj[k]) for k in sorted(obj)
        ) + b"}"
    raise TypeError(f"unsupported type {type(obj).__name__} in a receipt body")


def receipt_body(receipt: dict) -> bytes:
    return jcs({k: v for k, v in receipt.items() if k != "attestations"})


# --- Ed25519 (RFC 8032 Section 5.1) --------------------------------------

P = 2 ** 255 - 19
Q = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


def _recover_x(y: int, sign: int):
    if y >= P:
        return None
    x2 = (y * y - 1) * pow(D * y * y + 1, P - 2, P) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    return P - x if (x & 1) != sign else x


_GY = 4 * pow(5, P - 2, P) % P
_GX = _recover_x(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)


def _add(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % P
    B = (a[1] + a[0]) * (b[1] + b[0]) % P
    C = 2 * a[3] * b[3] * D % P
    E = 2 * a[2] * b[2] % P
    e, f, g, h = B - A, E - C, E + C, B + A
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s: int, pt):
    out = (0, 1, 1, 0)
    while s:
        if s & 1:
            out = _add(out, pt)
        pt = _add(pt, pt)
        s >>= 1
    return out


def _equal(a, b) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _compress(pt) -> bytes:
    zinv = pow(pt[2], P - 2, P)
    x, y = pt[0] * zinv % P, pt[1] * zinv % P
    return (y | (x & 1) << 255).to_bytes(32, "little")


def _decompress(data: bytes):
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def ed25519_public(seed: bytes) -> bytes:
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return _compress(_mul(a, G))


def ed25519_verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(signature) != 64:
        return False
    A, R = _decompress(public), _decompress(signature[:32])
    s = int.from_bytes(signature[32:], "little")
    if A is None or R is None or s >= Q:
        return False
    h = int.from_bytes(hashlib.sha512(signature[:32] + public + message).digest(), "little") % Q
    return _equal(_mul(s, G), _add(R, _mul(h, A)))


# --- Reference Appendix A.4 verifier -------------------------------------

def _b64url_decode(text: str) -> bytes:
    if not text or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in text):
        raise ValueError("not base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def integrity(receipt: dict) -> str:
    commitment = receipt.get("commitment")
    if not isinstance(commitment, dict) or set(commitment) - cmt.ALLOWED_PAYLOAD_FIELDS:
        return "cannot_verify"
    try:
        recomputed = cmt.compute_hash(commitment)[2]
    except TypeError:
        return "cannot_verify"
    if recomputed != receipt.get("commitment_hash"):
        return "mismatch"
    if "commitment_wire_b64" in receipt:
        try:
            wire = base64.b64decode(receipt["commitment_wire_b64"], validate=True)
        except (binascii.Error, ValueError):
            return "cannot_verify"
        outcome = cmt.verify(wire, receipt["commitment_hash"])
        if outcome != "match":
            return outcome
        if cmt.decode_payload(wire) != commitment:
            return "mismatch"
    return "match"


def attestation(att: dict, body: bytes, trusted: dict) -> str:
    if att.get("type") == "vendor":
        return "unsupported"  # binds=other never counts; the reference implements no vendor format
    if att.get("type") != "jws":
        return "unsupported"
    parts = str(att.get("jws", "")).split(".")
    if len(parts) != 3 or parts[1] != "":
        return "invalid"
    try:
        header = json.loads(_b64url_decode(parts[0]))
        signature = _b64url_decode(parts[2])
    except (ValueError, json.JSONDecodeError):
        return "invalid"
    if not isinstance(header, dict) or header.get("alg") != "EdDSA":
        return "unsupported"
    key = trusted.get(header.get("kid"))
    if key is None:
        return "unknown_key"
    signing_input = parts[0].encode() + b"." + base64.urlsafe_b64encode(body).rstrip(b"=")
    return "valid" if ed25519_verify(_b64url_decode(key), signing_input, signature) else "invalid"


def verify_receipt(receipt: dict, trusted: dict) -> dict:
    if receipt.get("receipt_format") != FORMAT:
        return {"integrity": None, "attestations": [], "verdict": "refused"}
    result = integrity(receipt)
    if result != "match":
        return {"integrity": result, "attestations": [], "verdict": "unverified"}
    body = receipt_body(receipt)
    outcomes = [attestation(a, body, trusted) for a in receipt.get("attestations", [])]
    return {"integrity": "match", "attestations": outcomes,
            "verdict": "attested" if "valid" in outcomes else "integrity_only"}


# --- Driver --------------------------------------------------------------

def main() -> int:
    errors = []
    example_key = base64.urlsafe_b64encode(
        ed25519_public(hashlib.sha256(b"macp-receipt example key").digest())).rstrip(b"=").decode()
    seen = {"integrity": set(), "attestations": set(), "verdict": set()}
    paths = sorted(p for p in VECTORS_DIR.glob("*.json") if p.name != "vector-schema.json")
    if not paths:
        errors.append(f"no vectors under {VECTORS_DIR.relative_to(ROOT)}")
    for path in paths:
        v = json.loads(path.read_text())
        name = v.get("name")
        if name != path.stem:
            errors.append(f"{path.name}: name {name!r} does not match the file name")
        if v["trusted_keys"].get("example-1", example_key) != example_key:
            errors.append(f"{path.name}: trusted_keys.example-1 is not the Appendix A.5 key")
        got = verify_receipt(v["receipt"], v["trusted_keys"])
        if got != v["expected"]:
            errors.append(f"{path.name}: expected {v['expected']}, reference verifier returned {got}")
        seen["integrity"].add(v["expected"]["integrity"])
        seen["attestations"].update(v["expected"]["attestations"])
        seen["verdict"].add(v["expected"]["verdict"])
        if name == "receipt_001_attested" and v["receipt"] != json.loads(EXAMPLE.read_text()):
            errors.append(f"{path.name}: receipt differs from {EXAMPLE.relative_to(ROOT)}")
        print(f"{'ok  ' if got == v['expected'] else 'FAIL'} {path.name}: {got['verdict']}")

    for field, wanted in (("integrity", INTEGRITY), ("attestations", ATTESTATION), ("verdict", VERDICT)):
        for outcome in sorted(wanted - seen[field]):
            errors.append(f"no vector expects {field} outcome {outcome!r}")

    for e in errors:
        print("FAIL " + e)
    if errors:
        return 1
    print(f"all {len(paths)} receipt vectors match the reference verifier")
    return 0


if __name__ == "__main__":
    sys.exit(main())
