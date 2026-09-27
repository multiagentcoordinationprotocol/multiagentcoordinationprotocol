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

The re-derivation itself and the vector-count guard are covered too, though they
long predate the collision vectors: an assertion nobody has ever seen fail is
one nobody would notice deleting. `check_first_byte_markers()` gets two
mutations rather than one, because its single `errors.append` is reached through
two independent loop iterations -- drop either key from that loop and the other
mutation still passes.

Every `errors.append` in the `contribute_payload` check tree is covered: 9 error
paths, 10 mutations. That is a property worth re-checking after any edit here,
by neutering each append in a scratch copy and confirming this script goes red.

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

    The only mutation here that cannot isolate its target, and unavoidably so:
    bytes that fail `bytes.fromhex` also fail the re-derivation and the
    first-byte marker, since a re-derived hex is by construction valid and
    0x0a-leading. Three assertions fire. The `expect` substring is what proves
    the intended one is among them.
    """
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "collision_leading_brace_13":
            v["protobuf_hex"] = "zz" + v["protobuf_hex"][2:]
            return "collision_leading_brace_13"
    raise SystemExit("FAIL: collision_leading_brace_13 not found -- mutation is stale")


def find(data: dict, name: str) -> dict:
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == name:
            return v
    raise SystemExit("FAIL: vector %r not found -- mutation is stale" % name)


def mutate_first_byte_proto_marker_drifts(data: dict) -> str:
    """`first_byte.protobuf` edited away from the byte the vectors actually lead
    with. The proto tag is fixed upstream by multi_round.proto's `value = 1`, but
    nothing parses the proto file to confirm this literal, so the vectors are
    what catch a drifted marker -- and 0x0b is deliberately a near-miss of 0x0a,
    the shape a typo takes."""
    fb = data["sections"]["contribute_payload"]["first_byte"]
    if fb.get("protobuf") != "0x0a":
        raise SystemExit("FAIL: first_byte.protobuf is not 0x0a -- mutation is stale")
    fb["protobuf"] = "0x0b"
    return "first_byte.protobuf"


def mutate_first_byte_json_marker_drifts(data: dict) -> str:
    """The same drift on the other marker, which needs its own mutation: the two
    keys are separate loop iterations over separate hex fields, so neutering one
    leaves the other passing. 0x7c (`|`) is the near-miss with teeth -- it is the
    byte that would CLOSE the proto group a leading 0x7b opens."""
    fb = data["sections"]["contribute_payload"]["first_byte"]
    if fb.get("legacy_json") != "0x7b":
        raise SystemExit("FAIL: first_byte.legacy_json is not 0x7b -- mutation is stale")
    fb["legacy_json"] = "0x7c"
    return "first_byte.legacy_json"


def mutate_decode_only_legacy_hex_smuggled(data: dict) -> str:
    """A `decode_only` vector given a `legacy_json_hex` equal to its own
    `protobuf_hex`.

    The reason the re-derivation keys on the field being PRESENT rather than on
    `decode_only` being absent. The manifest schema permits `decode_only: true`
    alongside `legacy_json_hex`, so under the old `if not decode_only` gate this
    field was re-derived against nothing -- and copying the adjacent field is
    both the likeliest way it happens and the worst possible content: bytes that
    round-trip byte-identically through the canonical proto encoding, which is
    precisely the ambiguity `decode_order`'s tie-break assumes cannot arise on
    the legacy side. A first-byte check alone would not have been enough; it
    catches this particular payload but not, say, a hand-written `7b7d`.
    """
    v = find(data, "one_byte_varint_boundary")
    if not v.get("decode_only") or "legacy_json_hex" in v:
        raise SystemExit(
            "FAIL: one_byte_varint_boundary is no longer a decode_only vector "
            "without a legacy_json_hex -- mutation is stale"
        )
    v["legacy_json_hex"] = v["protobuf_hex"]
    return "one_byte_varint_boundary"


def mutate_legacy_hex_dropped_without_decode_only(data: dict) -> str:
    """The other half of that gate: a vector that simply loses its legacy form.
    Keying on presence would let this pass silently if nothing required the field
    of a vector that is not marked decode_only."""
    v = find(data, "ascii_short")
    if v.get("decode_only") or "legacy_json_hex" not in v:
        raise SystemExit("FAIL: ascii_short is no longer a legacy-carrying vector -- stale")
    del v["legacy_json_hex"]
    return "ascii_short"


def mutate_protobuf_hex_drifts(data: dict) -> str:
    """One byte of a non-collision vector's `protobuf_hex` changed, keeping valid
    hex and the 0x0a lead byte so only the re-derivation can catch it. Covers the
    oldest assertion in the file, which had no test before."""
    v = find(data, "ascii_short")
    original = v["protobuf_hex"]
    v["protobuf_hex"] = original[:-2] + ("00" if original[-2:] != "00" else "01")
    return "ascii_short"


def mutate_vector_count_guard(data: dict) -> str:
    """A non-collision vector removed, so only the total-count guard fires (the
    collision count is untouched). Also previously untested."""
    vectors = data["sections"]["contribute_payload"]["vectors"]
    kept = [v for v in vectors if v["name"] != "utf8_accent"]
    if len(kept) == len(vectors):
        raise SystemExit("FAIL: utf8_accent not found -- mutation is stale")
    data["sections"]["contribute_payload"]["vectors"] = kept
    return "utf8_accent"


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
        "the pinned legacy-JSON first-byte marker drifted from the vectors",
        mutate_first_byte_json_marker_drifts,
        "first_byte.legacy_json pins",
    ),
    (
        "a decode_only vector smuggled in a legacy_json_hex holding canonical proto",
        mutate_decode_only_legacy_hex_smuggled,
        ("legacy_json_hex", "does not match the re-derived encoding"),
    ),
    (
        "a vector lost its legacy_json_hex without being marked decode_only",
        mutate_legacy_hex_dropped_without_decode_only,
        "has no legacy_json_hex and is not marked decode_only",
    ),
    (
        "a vector's protobuf_hex drifted from its value",
        mutate_protobuf_hex_drifts,
        ("protobuf_hex", "does not match the re-derived encoding"),
    ),
    (
        "a vector was removed, dropping the total below the pinned count",
        mutate_vector_count_guard,
        "contribute_payload.vectors, found",
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
            # A tuple means every substring must appear. Two assertions share one
            # message template ("... does not match the re-derived encoding ..."),
            # so a single substring could not tell the protobuf_hex branch from
            # the legacy_json_hex one and a mis-aimed mutation would look caught.
            wanted = (expect,) if isinstance(expect, str) else expect
            data = json.loads(pristine)
            mutate(data)
            (tree / CONTRACT_REL).write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            code, out = run_checker(tree)
            missing = [w for w in wanted if w not in out]
            if code == 0:
                failures.append(
                    "%s: checker PASSED a manifest it should have rejected -- the "
                    "corresponding assertion in check-parity-contract.py is decorative" % label
                )
            elif missing:
                failures.append(
                    "%s: checker failed (good) but never said %s, so it failed for the wrong "
                    "reason. Output:\n%s" % (label, ", ".join(repr(m) for m in missing), out)
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
        print("\n%d of %d contribute_payload mutations went uncaught or misdiagnosed."
              % (len(failures), len(MUTATIONS)), file=sys.stderr)
        return 1

    print("[OK] all %d mutations rejected, each for the reason it promises -- every "
          "errors.append in the contribute_payload check tree is covered" % len(MUTATIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
