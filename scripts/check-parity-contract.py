#!/usr/bin/env python3
"""Hold schemas/parity/contract.json's pinned values to their real in-repo sources.

CI. Runs with bare `python3` -- no venv, no `pip install` -- so this script
imports **stdlib only** (json, re, sys, pathlib, os), matching the constraint
scripts/check-cmt-hash-vectors.py was built under. Honors a `MACP_ROOT`
environment-variable override, the same seam scripts/validate-json.sh and
scripts/check-prose.py already expose, so the mutation-and-restore proofs in
the plan's acceptance criteria can run against a throwaway copy of the tree
rather than mutating the real repository.

This script does **not** validate schemas/parity/contract.json's SHAPE -- that
is schemas/json/macp-parity-contract.schema.json's job, enforced positively
and negatively by scripts/validate-json.sh. This script holds each pinned
VALUE that has an in-repo source to that source:

  - error_codes.{permanent,deprecated}      <- registries/error-codes.md
  - modes.standard                          <- registries/modes.md
  - modes.extension                         <- schemas/conformance/*.json's
    `mode` fields (the only in-repo enumeration containing
    ext.multi_round.v1 -- registries/modes.md defines only the ext.*
    namespace convention, not that specific id; see schemas/parity/README.md)
  - protocol.macp_version                   <- examples/json/*.json (the
    literal's normative home is RFC-MACP-0001 Section 6; this check holds
    the examples corpus to it, it does not parse the RFC)
  - defaults.policy_version                 <- RFC-MACP-0012 Section 5.1's
    fenced JSON block, cross-checked against registries/policies.md
  - defaults.policy_builder_schema_version  <- schemas/json/
    macp-policy-descriptor.schema.json's schema_version enum
  - retry.backoff_schedule_seconds          <- recomputed from max_retries /
    backoff_base_seconds / backoff_max_seconds
  - commitment_hash.pattern                 <- schemas/conformance/cmt-hash/
    vector-schema.json's (otherwise unchecked-by-anything) hash pattern;
    every accept/reject value re-checked against the manifest's own pattern
    via re.fullmatch
  - contribute_payload.vectors[*]           <- re-derived from each vector's
    plaintext `value` with a 6-line stdlib protobuf-tag encoder and
    json.dumps; the collision_* vectors additionally have the proto/JSON
    collision they exist to pin asserted directly (their protobuf_hex bytes
    must still parse as a JSON object), since re-derivation alone would
    stay green on a `value` edited to something that no longer collides

retry.* (besides the recomputed schedule) and projection_anomaly.* have NO
in-repo source at all -- they live only in macp-sdk-python and
macp-sdk-typescript, neither of which is this repo -- so this script does not,
and cannot, check them further. The manifest marks them "convention" instead
of inventing a citation (see the manifest's own Long-term posture D7 note).

Every failure is accumulated and reported before exiting non-zero (this
repo's check-prose.py / check-indexes.sh convention) -- one bad value must
never mask another. Fixed-count assertions (EXPECTED_SECTION_COUNT etc.)
guard against a future deletion silently shrinking what is checked.

Run: `python3 scripts/check-parity-contract.py` (exits non-zero on any
mismatch or missing source).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("MACP_ROOT") or Path(__file__).resolve().parent.parent
)

CONTRACT_PATH = ROOT / "schemas" / "parity" / "contract.json"
ERROR_CODES_REGISTRY = ROOT / "registries" / "error-codes.md"
MODES_REGISTRY = ROOT / "registries" / "modes.md"
POLICIES_REGISTRY = ROOT / "registries" / "policies.md"
CONFORMANCE_DIR = ROOT / "schemas" / "conformance"
EXAMPLES_DIR = ROOT / "examples" / "json"
RFC_0012 = ROOT / "rfcs" / "RFC-MACP-0012-policy.md"
POLICY_DESCRIPTOR_SCHEMA = ROOT / "schemas" / "json" / "macp-policy-descriptor.schema.json"
CMT_HASH_VECTOR_SCHEMA = ROOT / "schemas" / "conformance" / "cmt-hash" / "vector-schema.json"

# A manifest count, not a convenience -- see Makefile's EXPECTED_RULES_INSTANCES
# for the same idiom. A silently deleted section/vector/reject case must fail
# loudly rather than shrink what is checked while staying green. Bump these
# when the manifest legitimately grows.
EXPECTED_SECTION_COUNT = 9
EXPECTED_VECTOR_COUNT = 8
EXPECTED_ACCEPT_COUNT = 1
EXPECTED_REJECT_COUNT = 11

# The collision_* vectors exist to pin the byte-lengths at which a canonical
# proto ContributePayload ALSO parses as JSON. Re-deriving their hex from
# their `value` (below) proves only that the pair is self-consistent -- it
# would stay green if a `value` were edited to something that no longer
# collides, leaving a vector that tests nothing. So the collision itself is
# asserted, and counted.
EXPECTED_COLLISION_COUNT = 4
COLLISION_PREFIX = "collision_"

ERROR_CODE_ROW_RE = re.compile(
    r"^\|\s*([A-Z][A-Z0-9_]*)\s*\|.*\|\s*(permanent|deprecated)\s*\|", re.MULTILINE
)
STANDARD_MODE_RE = re.compile(r"`(macp\.mode\.[a-z_]+\.v[0-9]+)`")
FENCED_JSON_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def proto_contribute(value: str) -> bytes:
    """6-line stdlib protobuf-tag encoder for ContributePayload.value (field 1,
    string): tag 0x0A, a base-128 varint length, then the UTF-8 bytes."""
    b = value.encode("utf-8")
    n, out = len(b), bytearray([0x0A])
    while True:
        byte, n = n & 0x7F, n >> 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            break
    return bytes(out) + b


def legacy_json_bytes(value: str) -> bytes:
    return json.dumps({"value": value}, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_error_codes(sections: dict) -> list[str]:
    text = ERROR_CODES_REGISTRY.read_text(encoding="utf-8")
    permanent_registry: set[str] = set()
    deprecated_registry: set[str] = set()
    for code, status in ERROR_CODE_ROW_RE.findall(text):
        (permanent_registry if status == "permanent" else deprecated_registry).add(code)

    manifest = sections["error_codes"]
    m_permanent, m_deprecated = set(manifest["permanent"]), set(manifest["deprecated"])
    errors = []
    if m_permanent != permanent_registry:
        errors.append(
            "error_codes.permanent %s does not match registries/error-codes.md's "
            "permanent set %s (missing=%s extra=%s)"
            % (
                sorted(m_permanent),
                sorted(permanent_registry),
                sorted(permanent_registry - m_permanent),
                sorted(m_permanent - permanent_registry),
            )
        )
    if m_deprecated != deprecated_registry:
        errors.append(
            "error_codes.deprecated %s does not match registries/error-codes.md's "
            "deprecated set %s" % (sorted(m_deprecated), sorted(deprecated_registry))
        )
    return errors


def check_modes(sections: dict) -> list[str]:
    manifest = sections["modes"]
    errors = []

    standard_registry = set(STANDARD_MODE_RE.findall(MODES_REGISTRY.read_text(encoding="utf-8")))
    m_standard = set(manifest["standard"])
    if m_standard != standard_registry:
        errors.append(
            "modes.standard %s does not match registries/modes.md's standard-mode set %s"
            % (sorted(m_standard), sorted(standard_registry))
        )

    extension_fixtures: set[str] = set()
    for f in sorted(CONFORMANCE_DIR.glob("*.json")):
        try:
            data = load_json(f)
        except (OSError, json.JSONDecodeError):
            continue
        mode = data.get("mode") if isinstance(data, dict) else None
        if isinstance(mode, str) and mode.startswith("ext."):
            extension_fixtures.add(mode)
    m_extension = set(manifest["extension"])
    if m_extension != extension_fixtures:
        errors.append(
            "modes.extension %s does not match the ext.* mode ids found in "
            "schemas/conformance/*.json's `mode` fields %s"
            % (sorted(m_extension), sorted(extension_fixtures))
        )
    return errors


def check_macp_version(sections: dict) -> list[str]:
    manifest_value = sections["protocol"]["macp_version"]
    seen: set[str] = set()
    for f in sorted(EXAMPLES_DIR.glob("*.json")):
        try:
            data = load_json(f)
        except (OSError, json.JSONDecodeError):
            continue
        v = data.get("macp_version") if isinstance(data, dict) else None
        if v is not None:
            seen.add(v)
    if not seen:
        return ["no examples/json/*.json file has a macp_version field"]
    if seen != {manifest_value}:
        return [
            "protocol.macp_version %r disagrees with examples/json/*.json's value(s) %s"
            % (manifest_value, sorted(seen))
        ]
    return []


def check_policy_version(sections: dict) -> list[str]:
    errors = []
    text = RFC_0012.read_text(encoding="utf-8")
    default_policy = None
    for block in FENCED_JSON_RE.findall(text):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("policy_id") == "policy.default":
            default_policy = data
            break

    manifest_value = sections["defaults"]["policy_version"]
    if default_policy is None:
        errors.append(
            "could not find RFC-MACP-0012's default-policy fenced JSON block "
            'containing "policy_id": "policy.default"'
        )
    elif manifest_value != default_policy["policy_id"]:
        errors.append(
            "defaults.policy_version %r != RFC-MACP-0012 Section 5.1's default "
            "policy_id %r" % (manifest_value, default_policy["policy_id"])
        )

    if "policy.default" not in POLICIES_REGISTRY.read_text(encoding="utf-8"):
        errors.append("registries/policies.md no longer mentions policy.default")
    return errors


def check_policy_builder_schema_version(sections: dict) -> list[str]:
    schema = load_json(POLICY_DESCRIPTOR_SCHEMA)
    enum = schema["properties"]["schema_version"]["enum"]
    value = sections["defaults"]["policy_builder_schema_version"]
    if value not in enum:
        return [
            "defaults.policy_builder_schema_version %r not in "
            "macp-policy-descriptor.schema.json's schema_version enum %r" % (value, enum)
        ]
    return []


def check_retry_schedule(sections: dict) -> list[str]:
    retry = sections["retry"]
    base, cap, n = retry["backoff_base_seconds"], retry["backoff_max_seconds"], retry["max_retries"]
    # 0.1 * 2**i is exact in binary for the range in play, and backoff_max
    # caps before any inexact step -- exact equality is safe here and is
    # deliberate: an epsilon comparison would hide a real drifted value.
    recomputed = [min(base * (2 ** i), cap) for i in range(n)]
    if recomputed != retry["backoff_schedule_seconds"]:
        return [
            "retry.backoff_schedule_seconds %r != recomputed %r from max_retries/"
            "backoff_base_seconds/backoff_max_seconds"
            % (retry["backoff_schedule_seconds"], recomputed)
        ]
    return []


def check_commitment_hash(sections: dict) -> list[str]:
    errors = []
    ch = sections["commitment_hash"]

    vector_schema = load_json(CMT_HASH_VECTOR_SCHEMA)
    registry_pattern = vector_schema["properties"]["hash"]["pattern"]
    if ch["pattern"] != registry_pattern:
        errors.append(
            "commitment_hash.pattern %r != schemas/conformance/cmt-hash/"
            "vector-schema.json's hash pattern %r" % (ch["pattern"], registry_pattern)
        )

    try:
        compiled = re.compile(ch["pattern"])
    except re.error as exc:
        errors.append("commitment_hash.pattern does not compile: %s" % exc)
        return errors

    for value in ch["accept"]:
        if not compiled.fullmatch(value):
            errors.append(
                "commitment_hash.accept entry %r does not fullmatch pattern %r"
                % (value, ch["pattern"])
            )
    for value in ch["reject"]:
        if compiled.fullmatch(value):
            errors.append(
                "commitment_hash.reject entry %r unexpectedly fullmatches pattern %r "
                "(accept/reject contradicts the pattern's actual behavior)"
                % (value, ch["pattern"])
            )

    if len(ch["accept"]) != EXPECTED_ACCEPT_COUNT:
        errors.append(
            "expected %d commitment_hash.accept entries, found %d"
            % (EXPECTED_ACCEPT_COUNT, len(ch["accept"]))
        )
    if len(ch["reject"]) != EXPECTED_REJECT_COUNT:
        errors.append(
            "expected %d commitment_hash.reject entries, found %d"
            % (EXPECTED_REJECT_COUNT, len(ch["reject"]))
        )
    return errors


def check_contribute_payload(sections: dict) -> list[str]:
    errors = []
    vectors = sections["contribute_payload"]["vectors"]
    if len(vectors) != EXPECTED_VECTOR_COUNT:
        errors.append(
            "expected %d contribute_payload.vectors, found %d"
            % (EXPECTED_VECTOR_COUNT, len(vectors))
        )
    for v in vectors:
        name = v.get("name", "<unnamed>")
        expected_proto = proto_contribute(v["value"]).hex()
        if v["protobuf_hex"] != expected_proto:
            errors.append(
                "contribute_payload vector %r: protobuf_hex %r does not match "
                "the re-derived encoding %r of value %r"
                % (name, v["protobuf_hex"], expected_proto, v["value"])
            )
        if not v.get("decode_only"):
            expected_json = legacy_json_bytes(v["value"]).hex()
            actual_json = v.get("legacy_json_hex")
            if actual_json != expected_json:
                errors.append(
                    "contribute_payload vector %r: legacy_json_hex %r does not match "
                    "the re-derived encoding %r of value %r"
                    % (name, actual_json, expected_json, v["value"])
                )
    errors.extend(check_collision_vectors(vectors))
    return errors


def check_collision_vectors(vectors: list) -> list[str]:
    """Assert every collision_* vector actually collides.

    The point of these vectors is that the canonical proto encoding of `value`
    is ALSO parseable as JSON, because the field-1 tag byte and the length
    varint are themselves insignificant JSON whitespace (or, at value length
    123, the literal `{`). That property lives in the bytes, not in the
    manifest's shape, so nothing above would notice if it were lost.
    """
    errors = []
    collisions = [v for v in vectors if v.get("name", "").startswith(COLLISION_PREFIX)]

    if len(collisions) != EXPECTED_COLLISION_COUNT:
        errors.append(
            "expected %d %s* vectors, found %d -- a collision vector may have been "
            "removed or renamed" % (EXPECTED_COLLISION_COUNT, COLLISION_PREFIX, len(collisions))
        )

    without_value_key = []
    for v in collisions:
        name = v.get("name", "<unnamed>")
        try:
            decoded = json.loads(bytes.fromhex(v["protobuf_hex"]).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append(
                "contribute_payload vector %r: its protobuf_hex bytes do not parse as JSON "
                "(%s), so the proto/JSON collision this vector exists to pin no longer "
                "holds -- the vector is decorative" % (name, exc)
            )
            continue
        if not isinstance(decoded, dict):
            errors.append(
                "contribute_payload vector %r: its protobuf_hex bytes parse as JSON %r, not "
                "an object -- the collision this vector pins is with a legacy-JSON *object*"
                % (name, decoded)
            )
            continue
        if "value" not in decoded:
            without_value_key.append(name)

    # Exactly one collision vector reads as an object with no `value` key. That
    # is a distinct decoder branch -- the value is lost entirely rather than
    # returned wrong -- and it is the reason the length-10 vector is pinned
    # separately from the other three.
    if collisions and len(without_value_key) != 1:
        errors.append(
            "expected exactly 1 %s* vector whose JSON reading has no `value` key (the "
            "total-data-loss branch), found %d: %s"
            % (COLLISION_PREFIX, len(without_value_key), sorted(without_value_key))
        )
    return errors


CHECKS = (
    check_error_codes,
    check_modes,
    check_macp_version,
    check_policy_version,
    check_policy_builder_schema_version,
    check_retry_schedule,
    check_commitment_hash,
    check_contribute_payload,
)


def main() -> int:
    if not CONTRACT_PATH.is_file():
        print("FAIL: parity-contract manifest not found: %s" % CONTRACT_PATH, file=sys.stderr)
        return 1

    manifest = load_json(CONTRACT_PATH)
    sections = manifest.get("sections", {})

    errors: list[str] = []
    if len(sections) != EXPECTED_SECTION_COUNT:
        errors.append(
            "expected %d sections, found %d -- a section may be missing"
            % (EXPECTED_SECTION_COUNT, len(sections))
        )

    for check in CHECKS:
        errors.extend(check(sections))

    if errors:
        for e in errors:
            print("FAIL %s" % e, file=sys.stderr)
        print("\n%d error(s) found." % len(errors), file=sys.stderr)
        return 1

    print("All parity-contract cross-checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
