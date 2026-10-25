#!/usr/bin/env python3
"""Regenerate the RFC-MACP-0013 Appendix A decision-receipt reference vectors.

DEV-TIME ONLY. This script imports two third-party packages, `jcs` (RFC 8785)
and `cryptography` (Ed25519 signing), and is NEVER run in CI. CI runs
scripts/check-receipt-vectors.py instead, which is stdlib-only and re-derives
every outcome with its own JCS serializer and its own Ed25519 verifier, so a
bug shared by this script and that one has to be written twice.

    pip install jcs cryptography

Vectors under schemas/conformance/receipt/ are GENERATED, NEVER hand-edited.
Change the table below and re-run; Ed25519 signatures are deterministic, so
`git diff --exit-code schemas/conformance/receipt/` is clean when nothing was
meant to change.

Keys (Appendix A.5): `example-1` is the appendix's example key, seed =
SHA-256("macp-receipt example key"). `example-2` exists only so a vector can
carry a valid signature from a key the verifier does not trust; its seed is
SHA-256("macp-receipt example key 2").

Each vector pins a receipt, the verifier's trusted keys, and the outcomes a
conforming verifier returns under Appendix A.4: `integrity`, one entry per
attestation, and an overall `verdict`. The vocabulary is underscore-separated,
matching the cmt-hash vectors (`cannot_verify`, `unknown_key`, ...).

Run: `python3 scripts/gen-receipt-vectors.py`
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path

import jcs  # third-party; dev-only
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "schemas" / "conformance" / "receipt"
EXAMPLE = ROOT / "examples" / "discovery" / "decision_receipt.json"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def key(seed_text: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed_text.encode()).digest())


KEYS = {"example-1": key("macp-receipt example key"), "example-2": key("macp-receipt example key 2")}
PUBLIC = {
    kid: b64url(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))
    for kid, k in KEYS.items()
}
assert PUBLIC["example-1"] == "TDVzkxaSf6_Oxu7mmn5TbCkF80s8Ulh33qKQsi0gnZM"  # Appendix A.5


def cmt_hash(commitment: dict) -> str:
    return "sha256:" + hashlib.sha256(b"macp-commitment-hash/1:" + jcs.canonicalize(commitment)).hexdigest()


def body(receipt: dict) -> bytes:
    return jcs.canonicalize({k: v for k, v in receipt.items() if k != "attestations"})


def jws(receipt: dict, kid: str, alg: str = "EdDSA") -> str:
    header = b64url(json.dumps({"alg": alg, "kid": kid}, separators=(",", ":")).encode())
    signing_input = f"{header}.{b64url(body(receipt))}".encode()
    return f"{header}..{b64url(KEYS[kid].sign(signing_input))}"


def wire(commitment: dict) -> bytes:
    """proto3 encoding of a CommitmentPayload projection (defaults omitted)."""
    def field(number: int, data: bytes) -> bytes:
        out, n = bytearray([number << 3 | 2]), len(data)
        while n >= 0x80:
            out.append(n & 0x7F | 0x80)
            n >>= 7
        return bytes(out) + bytes([n]) + data

    names = ("commitment_id", "action", "authority_scope", "reason",
             "mode_version", "policy_version", "configuration_version")
    out = b"".join(field(i, commitment[n].encode()) for i, n in enumerate(names, 1) if commitment[n])
    if commitment["outcome_positive"]:
        out += b"\x40\x01"
    if "supersedes" in commitment:
        ref = commitment["supersedes"]
        out += field(9, b"".join(field(i, ref[k].encode())
                                 for i, k in ((1, "session_id"), (2, "commitment_hash")) if ref[k]))
    return out


# The appendix's example receipt is vector 001, unchanged.
BASE = json.loads(EXAMPLE.read_text())
BASE_UNSIGNED = {k: v for k, v in BASE.items() if k != "attestations"}
assert BASE["commitment_hash"] == cmt_hash(BASE["commitment"])
assert BASE["attestations"] == [{"type": "jws", "jws": jws(BASE_UNSIGNED, "example-1")}], \
    "examples/discovery/decision_receipt.json is not signed by example-1 over its own body"

TRUST_1 = {"example-1": PUBLIC["example-1"]}


def receipt(**overrides) -> dict:
    r = copy.deepcopy(BASE_UNSIGNED)
    r.update(overrides)
    return r


def signed(r: dict, *kids: str) -> dict:
    return {**r, "attestations": [{"type": "jws", "jws": jws(r, kid)} for kid in kids]}


def vectors() -> list[dict]:
    out = []

    def add(name, description, rcpt, integrity, attestations, verdict, trusted=TRUST_1):
        out.append({
            "name": name,
            "description": description,
            "receipt": rcpt,
            "trusted_keys": trusted,
            "expected": {"integrity": integrity, "attestations": attestations, "verdict": verdict},
        })

    add("receipt_001_attested",
        "the Appendix A example, unchanged: integrity holds and the example-1 JWS is valid",
        BASE, "match", ["valid"], "attested")

    add("receipt_002_integrity_only",
        "no attestations, with a transcript digest so the body carries two JCS integers (rev, message_count)",
        {**receipt(transcript={"digest_alg": "example-sha256-envelopes", "digest": "sha256:" + "ab" * 32,
                               "message_count": 7}), "attestations": []},
        "match", [], "integrity_only")

    tampered = receipt()
    signed_tampered = signed(tampered, "example-1")
    signed_tampered["commitment"] = {**tampered["commitment"], "reason": "sealed by someone else"}
    add("receipt_003_commitment_tampered",
        "commitment.reason edited after issue: the recorded hash no longer matches, so verification stops "
        "and the (otherwise valid) signature is never evaluated",
        signed_tampered, "mismatch", [], "unverified")

    reissued = signed(receipt(), "example-1")
    reissued["issuer"] = "runtime:impostor"
    add("receipt_004_body_tampered",
        "issuer edited after signing: integrity still matches, but the JWS no longer covers the body",
        reissued, "match", ["invalid"], "integrity_only")

    add("receipt_005_untrusted_key",
        "a valid signature from example-2, which this verifier does not trust",
        signed(receipt(), "example-2"), "match", ["unknown_key"], "integrity_only")

    add("receipt_006_one_of_two",
        "two attestations, one from an untrusted key and one valid: one valid attestation is enough",
        signed(receipt(), "example-2", "example-1"), "match", ["unknown_key", "valid"], "attested")

    r = receipt()
    hs = {**r, "attestations": [{"type": "jws", "jws": jws(r, "example-1", alg="HS256")}]}
    add("receipt_007_unsupported_alg",
        "a JWS whose protected header names HS256, which Appendix A.3 does not allow: unsupported, "
        "whatever bytes follow",
        hs, "match", ["unsupported"], "integrity_only")

    r = receipt()
    add("receipt_008_vendor_binds_other",
        "a vendor attestation with binds=other is informative only and never establishes authenticity",
        {**r, "attestations": [{"type": "vendor", "format": "org.example.trust-token", "binds": "other",
                                "value": "opaque"}]},
        "match", ["unsupported"], "integrity_only")

    add("receipt_009_unknown_format",
        "receipt_format macp-receipt/2 is not implemented: the verifier refuses before checking anything",
        {**receipt(receipt_format="macp-receipt/2"), "attestations": []},
        None, [], "refused")

    r = receipt(commitment_wire_b64=base64.b64encode(wire(BASE["commitment"])).decode())
    add("receipt_010_wire_match",
        "commitment_wire_b64 present: the wire passes Section 6.1 and projects to `commitment`",
        signed(r, "example-1"), "match", ["valid"], "attested")

    r = receipt(commitment_wire_b64="not base64!")
    add("receipt_011_wire_undecodable",
        "commitment_wire_b64 does not decode: integrity is cannot_verify and verification stops",
        signed(r, "example-1"), "cannot_verify", [], "unverified")

    other = {**BASE["commitment"], "reason": "a different reason"}
    w = base64.b64encode(wire(other)).decode()
    r = receipt(commitment_wire_b64=w)
    add("receipt_012_wire_disagrees",
        "commitment_wire_b64 decodes to a different Commitment than `commitment`: mismatch",
        signed(r, "example-1"), "mismatch", [], "unverified")

    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for v in vectors():
        (OUT_DIR / f"{v['name']}.json").write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(vectors())} vectors to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
