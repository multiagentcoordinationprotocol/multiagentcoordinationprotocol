#!/usr/bin/env python3
"""Regression proof that check-parity-contract.py's contribute_payload
assertions bite -- the ones re-derivation alone cannot make.

`contribute_payload`'s `collision_*` vectors pin the value byte-lengths at
which a canonical proto `ContributePayload` also parses as JSON. Re-deriving
each vector's `protobuf_hex`/`legacy_json_hex` from its plaintext `value`
proves only that the pair is SELF-CONSISTENT -- it stays green on a `value`
edited to something that no longer collides, leaving a vector that asserts
nothing while CI reports success. `check_collision_vectors()` exists to close
that, and this script is what keeps `check_collision_vectors()` honest: without
it, deleting one of its `errors.append` calls would not fail any build.

`check_first_byte_markers()` is covered for the same reason and a sharper one.
Re-derivation is gated on `not decode_only`, so a `decode_only` vector's
`legacy_json_hex` -- which the manifest schema permits -- is validated by
nothing else in the file. Its two assertions are the only thing holding
`first_byte`'s pinned discriminator bytes to the vectors they describe, and the
only thing stopping the manifest from publishing a `legacy_json_hex` that a
proto-first reading could claim.

Same shape as scripts/check-prose-test.py (issue #129): copy the tree, mutate
the COPY, run the real unmodified scripts/check-parity-contract.py against it
through the `MACP_ROOT` seam that script already documents for exactly this
purpose, and assert it exits non-zero with the message the branch promises.
The real repository is never mutated.

Stdlib only, no test framework -- this repo has no pytest dependency anywhere;
every check is a small driver script wired into the Makefile, and this follows
that convention.

Run: `python3 scripts/check-parity-contract-test.py` (exits non-zero if any
mutation is NOT caught, i.e. if an assertion has gone decorative).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check-parity-contract.py"
# Only the trees the checker actually reads, rather than a whole-repo copy:
# it opens schemas/, registries/, examples/json/ and one RFC.
NEEDED = ("schemas", "registries", "examples", "rfcs")
CONTRACT_REL = Path("schemas") / "parity" / "contract.json"


def varint(n: int) -> bytes:
    """Deliberately a second implementation, not an import of the checker's
    encoder: this script must be able to build a mutation the checker would
    consider self-consistent, without inheriting the checker's own bugs."""
    if n == 0:
        return b"\x00"
    groups = []
    while n:
        groups.append(n & 0x7F)
        n >>= 7
    return bytes(g | 0x80 for g in groups[:-1]) + bytes([groups[-1]])


def reencode(vector: dict, value: str) -> None:
    """Replace a vector's `value` AND both hexes, so the mutation survives the
    checker's re-derivation and can only be caught by a collision assertion."""
    raw = value.encode("utf-8")
    vector["value"] = value
    vector["protobuf_hex"] = (bytes([0x0A]) + varint(len(raw)) + raw).hex()
    if "legacy_json_hex" in vector:
        vector["legacy_json_hex"] = (
            json.dumps({"value": value}, separators=(",", ":"), ensure_ascii=False)
            .encode("utf-8")
            .hex()
        )


def run_checker(tree: Path) -> tuple[int, str]:
    env = dict(os.environ, MACP_ROOT=str(tree))
    proc = subprocess.run(
        [sys.executable, str(CHECKER)],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --- mutations -----------------------------------------------------------------
# Each returns a short label; each MUST make the checker exit non-zero with a
# message containing `expect`.


def mutate_stops_colliding(data: dict) -> str:
    """A collision vector whose value no longer parses as JSON, at the same byte
    length -- the exact silent-decorative case the assertion exists for."""
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "collision_foreign_key_10":
            reencode(v, "z" * 10)
            return "collision_foreign_key_10"
    raise SystemExit("FAIL: collision_foreign_key_10 not found -- mutation is stale")


def mutate_value_key_branch_lost(data: dict) -> str:
    """Every collision vector reads as an object WITH a `value` key, so the
    lose-the-value-entirely branch stops being pinned.

    The replacement must still COLLIDE, or this would merely re-exercise the
    mutation above and never reach the floor assertion. 13 bytes: the length
    varint is 0x0d (CR), which is insignificant JSON whitespace, so the proto
    bytes parse as {"value": "y"} -- legacy-shaped, hence a `value` key. Note a
    10-byte replacement cannot work here: the shortest legacy-shaped object is
    `{"value":""}` at 12 bytes, which is why length 10 is structurally
    value-less and worth pinning in the first place.
    """
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "collision_foreign_key_10":
            reencode(v, '{"value":"y"}')
            return "collision_foreign_key_10"
    raise SystemExit("FAIL: collision_foreign_key_10 not found -- mutation is stale")


def mutate_collision_vector_removed(data: dict) -> str:
    """One collision vector deleted, so the count guard must notice.

    The staleness guard matters more here than in the other three: a rename
    would make the comprehension remove nothing, the checker would (correctly)
    pass an unmutated manifest, and this script would then report "the
    corresponding assertion is decorative" -- a loud failure with the wrong
    diagnosis, which is the same trap as a fixture failing for the wrong reason.
    """
    vectors = data["sections"]["contribute_payload"]["vectors"]
    kept = [v for v in vectors if v["name"] != "collision_leading_brace_32"]
    if len(kept) == len(vectors):
        raise SystemExit("FAIL: collision_leading_brace_32 not found -- mutation is stale")
    data["sections"]["contribute_payload"]["vectors"] = kept
    return "collision_leading_brace_32"


def mutate_protobuf_hex_undecodable(data: dict) -> str:
    """A collision vector whose protobuf_hex is not decodable hex at all.

    Unreachable through the schema (whose hex `pattern` forbids it), so this
    mutation writes the manifest directly. Covered anyway so that every
    errors.append in check_collision_vectors() has a test proving it fires --
    an uncovered branch is one nobody would notice deleting.
    """
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "collision_leading_brace_13":
            v["protobuf_hex"] = "zz" + v["protobuf_hex"][2:]
            return "collision_leading_brace_13"
    raise SystemExit("FAIL: collision_leading_brace_13 not found -- mutation is stale")


def mutate_first_byte_proto_marker_drifts(data: dict) -> str:
    """`first_byte.protobuf` edited away from the byte the vectors actually lead
    with. Nothing re-derives `first_byte` from anything, so the vectors are the
    only thing that can catch it -- and 0x0b is deliberately a near-miss of 0x0a,
    the shape a typo takes."""
    fb = data["sections"]["contribute_payload"]["first_byte"]
    if fb.get("protobuf") != "0x0a":
        raise SystemExit("FAIL: first_byte.protobuf is not 0x0a -- mutation is stale")
    fb["protobuf"] = "0x0b"
    return "first_byte.protobuf"


def mutate_decode_only_legacy_hex_smuggled(data: dict) -> str:
    """A `decode_only` vector given a `legacy_json_hex` equal to its own
    `protobuf_hex`.

    This is the one edit that reaches a legacy_json_hex nothing else validates:
    the checker's re-derivation is gated on `not decode_only`, and the manifest
    schema permits `decode_only: true` alongside `legacy_json_hex`, so the field
    is otherwise dead data. Copying the adjacent field is the likeliest way it
    happens, and it is the worst possible content -- bytes that round-trip
    byte-identically through the canonical proto encoding, which is precisely
    the ambiguity `decode_order`'s tie-break assumes cannot arise on the legacy
    side. Only the legacy first-byte marker stands between the manifest and
    publishing it.
    """
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "one_byte_varint_boundary":
            if not v.get("decode_only") or "legacy_json_hex" in v:
                raise SystemExit(
                    "FAIL: one_byte_varint_boundary is no longer a decode_only vector "
                    "without a legacy_json_hex -- mutation is stale"
                )
            v["legacy_json_hex"] = v["protobuf_hex"]
            return "one_byte_varint_boundary"
    raise SystemExit("FAIL: one_byte_varint_boundary not found -- mutation is stale")


MUTATIONS = (
    (
        "a collision vector's value no longer collides",
        mutate_stops_colliding,
        "the vector is decorative",
    ),
    (
        "no collision vector exercises the missing-`value`-key branch",
        mutate_value_key_branch_lost,
        "no longer pinned",
    ),
    (
        "a collision vector was removed",
        mutate_collision_vector_removed,
        "collision_* vectors, found",
    ),
    (
        "a collision vector's protobuf_hex is not decodable hex",
        mutate_protobuf_hex_undecodable,
        "is not decodable hex",
    ),
    (
        "the pinned proto first-byte marker drifted from the vectors",
        mutate_first_byte_proto_marker_drifts,
        "first_byte.protobuf pins",
    ),
    (
        "a decode_only vector smuggled in a legacy_json_hex holding canonical proto",
        mutate_decode_only_legacy_hex_smuggled,
        "first_byte.legacy_json pins",
    ),
)


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="macp-parity-selftest-"))
    failures: list[str] = []
    try:
        tree = tmp_root / "repo"
        tree.mkdir()
        for name in NEEDED:
            shutil.copytree(REPO_ROOT / name, tree / name, symlinks=True)

        pristine = (tree / CONTRACT_REL).read_text(encoding="utf-8")

        # Baseline: the untouched copy must PASS, or every "caught" result
        # below would be meaningless (a red baseline catches everything).
        code, out = run_checker(tree)
        if code != 0:
            print("FAIL baseline: the unmutated copy does not pass:\n%s" % out, file=sys.stderr)
            return 1
        print("[OK] baseline: unmutated copy passes under MACP_ROOT")

        for label, mutate, expect in MUTATIONS:
            data = json.loads(pristine)
            mutate(data)
            (tree / CONTRACT_REL).write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            code, out = run_checker(tree)
            if code == 0:
                failures.append(
                    "%s: checker PASSED a manifest it should have rejected -- the "
                    "corresponding assertion in check-parity-contract.py is decorative" % label
                )
            elif expect not in out:
                failures.append(
                    "%s: checker failed (good) but never said %r, so it failed for the wrong "
                    "reason. Output:\n%s" % (label, expect, out)
                )
            else:
                print("[OK] caught: %s" % label)
            # restore before the next mutation
            (tree / CONTRACT_REL).write_text(pristine, encoding="utf-8")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    if failures:
        for f in failures:
            print("FAIL %s" % f, file=sys.stderr)
        print("\n%d of %d contribute_payload assertions are not doing their job."
              % (len(failures), len(MUTATIONS)), file=sys.stderr)
        return 1

    print("[OK] all %d contribute_payload assertions reject what they promise to reject, for "
          "the stated reason" % len(MUTATIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
