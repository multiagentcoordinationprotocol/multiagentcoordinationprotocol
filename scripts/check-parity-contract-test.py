#!/usr/bin/env python3
"""Regression proof that check-parity-contract.py's assertions bite -- above all
the contribute_payload ones re-derivation alone cannot make.

Scope note, because it changed: this file was written for `contribute_payload`
alone, and the exhaustive-coverage claim below is still scoped to that tree. It
is no longer the only thing here. Two AREAS elsewhere in the checker now carry
mutations -- `retry.retryable_error_codes` and `check_own_contribute_error_paths` --
which is **four** covered out-of-tree `errors.append` sites, not two: the retry
membership loop is one site, and the guard contributes three of its four. They are as
real as the rest; they are
just outside what the "every append is covered" count counts, for the reason
spelled out under "The `contribute_payload` check tree" below.

Do NOT read that as a policy this file follows. It is not "every assertion that
would pass silently if deleted has a mutation" -- measured at this commit, the
checker holds **35** `errors.append` sites and this file covers **19** of them.
The 16 uncovered ones are all outside the contribute tree, and they include the
backoff-schedule assertion in the very same function as the covered retry
membership check. Out-of-tree coverage here is opportunistic, added where a phase
touched the assertion anyway. The only exhaustive claim is the tree one.

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
mutation still passes. (That single-append-inside-a-loop shape is also why those
two mutations each print one FAIL line per vector while touching only one
assertion; see the lines-vs-sites note below.)

Every `errors.append` in the `contribute_payload` check tree is covered: 15
error paths, covered by 17 of this script's mutations. Read "of" literally, and
here is the arithmetic in full so no remainder is left unexplained: the script
carries **22** mutations = 17 tree + 1 `retry` + 4 for the count guard. The two
numbers 15 and 17 are not equal and are not meant to be -- some appends need more
than one mutation (see `check_first_byte_markers` above), and no mutation is
*credited* with covering two appends, so the designated cover map stays
one-directional and a deleted append always orphans a mutation.

`check_own_contribute_error_paths()` in the checker pins that 15, and this file
carries four mutations of a second kind for it, `SOURCE_MUTATIONS`, which edit the
copied **checker source** rather than the manifest: an append added, an append
deleted, the call-graph anchor renamed, and the copy made unparseable. They work
only because run_checker() executes the REAL checker and points MACP_ROOT at the
copy, so the copy is parsed and never run.

**What that pin does and does not guarantee, measured rather than assumed.** It is
NOT true that "adding a 16th append without adding a mutation turns `make
parity-contract` red": bump `EXPECTED_CONTRIBUTE_ERROR_PATHS` to 16 in the same
commit and `parity-contract` is green. What goes red is `make
parity-contract-selftest`, because two `SOURCE_MUTATIONS` assert on the literal
strings "call tree has 16", "call tree has 14" and "pins 15". So the real property
is the composite one, and note the quantifier: adding an append forces you to touch
BOTH files, not just the checker. That is stronger than a one-file guard, and it is
also all it is -- touching both files is not the same as adding a mutation. The
coverage claim
itself is still honour-system: bump the constant, update those three literals, add
no mutation, and the run is green with a printed claim that has gone false. If you
are editing this tree, that paragraph is the one to re-read.

Read "credited" strictly: it is a claim about the cover map, NOT about blast
radius. MANY mutations here trip more than one error site, because the
manifest's fields constrain each other and one edit can violate several at once.
Each such case is noted in its own docstring, with whether the overlap was
avoidable.

Two quantities get confused here, so name them apart before measuring either.
A mutation's FAIL *lines* are how many messages the run prints; its *sites* are
how many distinct `errors.append` statements produced them. They are not the
same number, and the gap is not noise: `check_first_byte_markers` holds a single
`errors.append` inside a loop over every vector, so drifting one marker prints one
line per vector it does not skip -- measured, eight for the proto marker and SEVEN
for the legacy one, because `one_byte_varint_boundary` is `decode_only` and carries
no legacy hex to check -- from ONE site either way. That is a well-isolated mutation
being loud, not a mutation with a wide blast radius. Only the site count says
anything about whether assertions overlap. (An earlier version of this paragraph
gave "eight" for both. It was right about the proto marker and wrong about the
legacy one, which is a small illustration of why the rule below is MEASURE.)

No count of either quantity is stated anywhere in this file -- deliberately, and
this is the third attempt at this paragraph. Two successive review rounds each
corrected a figure here ("four of ten", then "seven of fourteen, two or three
sites"), and the very next phase falsified it again, because adding one assertion
silently widens the blast radius of every pre-existing mutation that touches the
same field. A figure nothing machine-checks, in the one file whose purpose is to
stop coverage claims from drifting, is a liability rather than documentation.

So: to learn the current distribution, MEASURE it. Copy the tree, apply one
mutation to the copy, run the checker under `MACP_ROOT`, count the FAIL lines,
and collapse them to sites by normalising the interpolated values out of each
message. If you add an assertion, sweep the PRE-EXISTING mutations too, not just
your own -- that is precisely the step whose omission falsified this paragraph
twice.

What the assertion above promises is only that every append has at least one
mutation that FAILS when that append is removed. That is the property worth
re-checking after any edit here, by neutering each append in a scratch copy and
confirming this script goes red for the message that append emits.

**That procedure has one step it did not need before the count guard landed, and
skipping it produces a red run that proves nothing.** Neutering an IN-TREE append
drops the measured count to 14, so `check_own_contribute_error_paths` fires and the
copy fails its BASELINE check -- you get `FAIL baseline: the unmutated copy does not
pass`, **zero** mutations run, and the neutered append's own message appears nowhere.
Red for the wrong reason, which is the exact trap this file warns about elsewhere. So
when neutering an in-tree append, bump `EXPECTED_CONTRIBUTE_ERROR_PATHS` to 14 in the
same scratch copy. The run then correctly names the orphaned mutation -- measured,
`FAIL two vectors share a name ...` for the duplicate-name append -- alongside **two
spurious failures** from the two count-literal source mutations: they still assert the
strings "call tree has 16" and "call tree has 14", while a 14-path checker emits 15 and
13. Expected noise, not a second finding. Out-of-tree appends need neither the bump nor
the noise filter.

"The `contribute_payload` check tree" means the functions reachable from
`check_contribute_payload()`, not the whole checker. An assertion in another
section is not in scope for the error-path count above and is not claimed to be
covered by it -- this script may still carry mutations for such assertions, and
those mutations are simply not what that count counts.

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

import ast
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
# it opens schemas/, registries/, examples/json/ and one RFC -- plus, since
# check_own_contribute_error_paths landed, its own source under `scripts/`.
#
# `scripts` is here for that self-read ONLY. The checker that RUNS is always the
# real one at REPO_ROOT (see run_checker); the copy is parsed, never executed.
# That asymmetry is the whole reason a source mutation below can be both
# effective (the guard sees it) and side-effect-free (nothing else does).
NEEDED = ("schemas", "registries", "examples", "rfcs", "scripts")
CONTRACT_REL = Path("schemas") / "parity" / "contract.json"
SOURCE_REL = Path("scripts") / "check-parity-contract.py"


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

    Since the name/length assertions landed, this trips THREE error sites, not
    one: re-encoding to 13 bytes while keeping the `_10` name also violates the
    name-vs-length check and shortens the pinned-length multiset. That overlap is
    unavoidable and follows from the paragraph above -- no 10-byte value can
    carry a `value` key, so there is no length-preserving way to write this
    mutation. The `expect` substring is what keeps it honest: it still proves the
    floor assertion specifically fired, and neutering that assertion alone still
    turns this mutation red.
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

    Fires three assertions, not one, and unavoidably: bytes that fail
    `bytes.fromhex` also fail the re-derivation and the first-byte marker, since
    a re-derived hex is by construction valid and 0x0a-leading. Several other
    mutations here trip more than one assertion for similar reasons -- perfect
    isolation is not available when the manifest's fields are derived from each
    other. (No count of how many; see the module docstring for why this file
    states none.) The `expect` substring is what proves the intended assertion is
    among the ones that fired.
    """
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if v["name"] == "collision_leading_brace_13":
            v["protobuf_hex"] = "zz" + v["protobuf_hex"][2:]
            return "collision_leading_brace_13"
    raise SystemExit("FAIL: collision_leading_brace_13 not found -- mutation is stale")


def mutate_collision_length_drifts_from_name(data: dict) -> str:
    """A collision vector re-encoded to a DIFFERENT byte length, keeping its name.

    It still collides (13 bytes is a genuine collision length), and both hexes are
    re-derived, so neither the collision assertion nor the re-derivation can catch
    it. This is the mutation that makes the numbers in the vector names
    load-bearing instead of decorative.

    It does NOT isolate the name-vs-length check, and an earlier version of this
    docstring wrongly claimed it did. Two error sites fire: moving a 32-byte
    vector to 13 bytes both contradicts its own name AND leaves the pinned-length
    multiset at [10, 13, 13, 123] instead of [10, 13, 32, 123]. The `expect`
    substring is what proves the name-vs-length branch is among the two, and
    neutering that branch alone still turns this mutation red.

    The case that isolates name-vs-length cleanly is a name SWAP -- exchange
    `collision_leading_brace_13` and `collision_leading_brace_32`'s names, leaving
    every value untouched: the multiset is unchanged so the set check stays
    silent, and only the per-vector comparison fires (twice). That asymmetry is
    exactly what check-parity-contract.py's own docstring means by "(4) compares
    lengths only, so two vectors could swap names and stay green" -- the two
    assertions catch overlapping but non-identical failure sets, which is why both
    exist.
    """
    v = find(data, "collision_leading_brace_32")
    if len(v["value"].encode("utf-8")) != 32:
        raise SystemExit("FAIL: collision_leading_brace_32 is not 32 bytes -- mutation is stale")
    reencode(v, '{"value":"y"}')  # 13 bytes, still collides
    return "collision_leading_brace_32"


def mutate_collision_name_loses_its_number(data: dict) -> str:
    """A collision vector renamed to drop its trailing _<int> entirely.

    Keeps the collision_ prefix, so the count guard stays quiet and the vector is
    still selected -- but the length it pins becomes unstated. Without its own
    assertion this vector would simply fall out of both length checks, which is the
    silent-exit case rather than a loud one. Trips the length-set assertion too, and
    unavoidably: a vector with no stated length contributes none, so the set is one
    short. The `expect` substring is what proves the intended branch fired.
    """
    v = find(data, "collision_leading_brace_13")
    v["name"] = "collision_leading_brace"
    return "collision_leading_brace"


def mutate_collision_band_collapses_onto_one_length(data: dict) -> str:
    """The band collapsed onto one length, with every name honestly renamed to match.

    The case the per-vector name check alone CANNOT catch, and the reason
    EXPECTED_COLLISION_LENGTHS exists: after this, every collision vector's name
    agrees with its own value's byte length, all four names are still distinct (so
    the duplicate-name check stays quiet), every hex re-derives, and all four still
    collide. Only the pinned length SET notices that three of the four lengths the
    prose claims are gone.
    """
    renamed = []
    for v in data["sections"]["contribute_payload"]["vectors"]:
        if not v["name"].startswith("collision_"):
            continue
        # 10 bytes, collides (tag 0x0a + varint 0x0a are both LF), and carries no
        # `value` key -- so the missing-value-key floor stays satisfied too.
        reencode(v, '{"a":"xx"}')
        v["name"] = "collision_%s_10" % chr(ord("a") + len(renamed))
        renamed.append(v["name"])
    if len(renamed) != 4:
        raise SystemExit(
            "FAIL: expected 4 collision_* vectors to rename, found %d -- mutation is stale"
            % len(renamed)
        )
    return ", ".join(renamed)


def find(data: dict, name: str) -> dict:
    """Return the vector with this `name`.

    Returns the FIRST match, which is only safe because the checker now rejects
    duplicate names outright (`check_contribute_payload`'s uniqueness loop, tested
    by `mutate_duplicate_vector_name` below). Before that assertion existed this
    was a silent hazard: a duplicate name made one of the pair unreachable, so a
    mutation keyed on it would exercise the wrong vector -- or the same one twice
    -- and still print "caught".
    """
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
    of a vector that is not marked decode_only.

    Since the legacy floor landed this trips two sites, not one: deleting a
    legacy form necessarily takes the carrier count from 7 to 6. Unavoidable --
    there is no way to drop a legacy_json_hex without lowering the count of
    vectors that have one. The `expect` substring keeps it honest, and neutering
    the per-vector requirement alone still turns this mutation red.
    """
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
    """A vector removed, so only the total-count guard fires.

    Targets `one_byte_varint_boundary` specifically, and the choice is what makes
    the isolation claim true rather than merely intended. It must be a vector
    that is BOTH non-collision (so the collision count and the two length checks
    stay quiet) AND a non-carrier of `legacy_json_hex` (so the legacy floor stays
    quiet). `one_byte_varint_boundary` is the only vector that is both -- it is
    the sole `decode_only` non-carrier.

    It used to remove `utf8_accent`, which was non-collision but IS a carrier. So
    when the legacy floor landed, this mutation silently started tripping two
    sites, and this docstring's word "only" silently became false. Measured after
    the retarget: exactly 1 error. If a future phase adds an assertion, re-measure
    this one before trusting the word "only" again.
    """
    vectors = data["sections"]["contribute_payload"]["vectors"]
    target = find(data, "one_byte_varint_boundary")
    if target.get("legacy_json_hex") is not None:
        raise SystemExit(
            "FAIL: one_byte_varint_boundary now carries a legacy_json_hex, so removing it "
            "would also trip the legacy floor -- retarget to another non-collision "
            "non-carrier or accept the overlap, but do not leave 'only' in the docstring"
        )
    kept = [v for v in vectors if v["name"] != "one_byte_varint_boundary"]
    if len(kept) == len(vectors):
        raise SystemExit("FAIL: one_byte_varint_boundary not found -- mutation is stale")
    data["sections"]["contribute_payload"]["vectors"] = kept
    return "one_byte_varint_boundary"


def mutate_duplicate_vector_name(data: dict) -> str:
    """Two vectors given the same `name`, with every other field left alone.

    The mutation that makes the harness's own central assumption enforced rather
    than lucky: `find()` above returns the FIRST match, so a duplicate name
    silently renders one of the pair unmutatable -- every mutation keyed on that
    name would still report "caught" while testing the wrong vector, or the same
    vector twice.

    Deliberately a RENAME, not a duplicated object. Both vectors keep their own
    `value`/`protobuf_hex`/`legacy_json_hex`, so both still re-derive cleanly;
    the total stays 8 so the count guard is silent; neither name starts with
    `collision_` so the band checks are silent. Only the uniqueness assertion can
    fire. A duplicated OBJECT would instead be the one case `"uniqueItems": true`
    already catches, which is exactly why the schema keyword is not the fix.
    """
    vectors = data["sections"]["contribute_payload"]["vectors"]
    names = [v["name"] for v in vectors]
    if "utf8_accent" not in names or "ascii_short" not in names:
        raise SystemExit(
            "FAIL: expected both utf8_accent and ascii_short to exist -- mutation is stale"
        )
    for v in vectors:
        if v["name"] == "utf8_accent":
            v["name"] = "ascii_short"
    return "utf8_accent -> ascii_short"


def mutate_empty_vector_value(data: dict) -> str:
    """A vector given `value: ""` with a hex pair that is otherwise self-consistent.

    REPLACES a vector in place rather than appending a ninth: appending would trip
    EXPECTED_VECTOR_COUNT first and the mutation would look "caught" while saying
    nothing about the empty-value assertion.

    The two hexes are chosen so that only the new assertion can fire. `0a00` is
    what this script's own encoder produces for "" (tag, then a zero length), and
    the legacy hex is `json.dumps({"value": ""})` = `{"value":""}`, 12 bytes. So
    the vector is internally consistent under every pre-existing check, which is
    the point: the manifest can be made to hold a schema-valid, self-consistent,
    and still incoherent empty-value vector, and before this assertion nothing
    said so.

    `ascii_short` is the target because it is a non-collision vector: no
    `collision_` prefix, so the count guard, the name/length checks and the
    length-set check are all silent, and the `value`-key floor is unaffected.
    """
    v = find(data, "ascii_short")
    if v["value"] == "":
        raise SystemExit("FAIL: ascii_short is already empty -- mutation is stale")
    v["value"] = ""
    v["protobuf_hex"] = "0a00"
    v["legacy_json_hex"] = b'{"value":""}'.hex()
    return "ascii_short"


def mutate_all_legacy_forms_deleted(data: dict) -> str:
    """The whole legacy half of the section deleted in one schema-valid edit.

    This is the scenario the floor exists for, and the reason it is not
    hypothetical: `decode_only: true` is a schema-legal way to omit
    `legacy_json_hex`, so marking every vector decode_only satisfies the
    per-vector requirement while removing every legacy form. Before the floor,
    this passed -- and it also silently retired
    check_first_byte_markers' legacy marker, which skips vectors that carry no
    legacy hex, so first_byte.legacy_json could then hold any byte at all.

    Setting first_byte.legacy_json to a wrong byte too is what makes that second
    consequence visible, and it was verified rather than reasoned about: with the
    floor neutered, this entire mutation -- every legacy form gone AND
    first_byte.legacy_json set to 0x00 -- passes the checker with zero errors.
    """
    vectors = data["sections"]["contribute_payload"]["vectors"]
    carriers = [v for v in vectors if v.get("legacy_json_hex") is not None]
    if len(carriers) < 2:
        raise SystemExit("FAIL: fewer than 2 legacy carriers to delete -- mutation is stale")
    for v in vectors:
        v.pop("legacy_json_hex", None)
        v["decode_only"] = True
    data["sections"]["contribute_payload"]["first_byte"]["legacy_json"] = "0x00"
    return "all %d legacy forms" % len(carriers)


def mutate_one_legacy_form_deleted(data: dict) -> str:
    """ONE legacy carrier stripped, marked decode_only so the per-vector
    requirement stays satisfied.

    Its own mutation, because it proves the floor is a FLOOR rather than an
    all-or-nothing guard: the mutation above would still be caught by a check
    that merely required "at least one legacy form somewhere", and this one would
    not. 7 -> 6 is the smallest edit the floor must reject.
    """
    v = find(data, "utf8_accent")
    if v.get("legacy_json_hex") is None:
        raise SystemExit("FAIL: utf8_accent carries no legacy_json_hex -- mutation is stale")
    del v["legacy_json_hex"]
    v["decode_only"] = True
    return "utf8_accent"


def mutate_retryable_code_not_permanent(data: dict) -> str:
    """A retryable error code that is not a canonical error code.

    The FIRST mutation in this file outside the contribute_payload tree, which is
    why the module docstring's opening had to widen.

    Two codes, one of each failure shape, because they are not the same mistake:
    `RATELIMITED` is the underscore-less typo of a real code -- the realistic way
    this breaks -- and `TEAPOT` is an outright invention. Both were verified to
    PASS before this assertion existed.

    Isolation: `retry.backoff_schedule_seconds` and the three values it is
    recomputed from are untouched, so the sibling assertion in the same function
    stays silent. Measured: 2 FAIL lines from 1 site (one per bad code), which is
    the single-append-in-a-loop shape described in the module docstring, not an
    overlap.
    """
    codes = data["sections"]["retry"]["retryable_error_codes"]
    permanent = data["sections"]["error_codes"]["permanent"]
    if "RATELIMITED" in permanent or "TEAPOT" in permanent:
        raise SystemExit(
            "FAIL: RATELIMITED/TEAPOT is now a permanent error code -- mutation is stale"
        )
    if not codes:
        raise SystemExit("FAIL: retry.retryable_error_codes is empty -- mutation is stale")
    data["sections"]["retry"]["retryable_error_codes"] = ["RATELIMITED", "TEAPOT"]
    return "retryable_error_codes"


MUTATIONS = (
    (
        "a retryable error code is not a member of error_codes.permanent",
        mutate_retryable_code_not_permanent,
        "not a member of error_codes.permanent",
    ),
    (
        "every legacy_json_hex deleted, every vector marked decode_only",
        mutate_all_legacy_forms_deleted,
        "below the floor of",
    ),
    (
        "one legacy carrier stripped, taking the count from 7 to 6",
        mutate_one_legacy_form_deleted,
        "below the floor of",
    ),
    (
        "a vector's value is empty, with an otherwise self-consistent hex pair",
        mutate_empty_vector_value,
        "has an empty `value`",
    ),
    (
        "two vectors share a name, every other field intact",
        mutate_duplicate_vector_name,
        "two vectors named",
    ),
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
        "a collision vector's byte length drifted from the length its name pins",
        mutate_collision_length_drifts_from_name,
        "in its name but its `value` is",
    ),
    (
        "a collision vector's name lost its trailing byte-length number",
        mutate_collision_name_loses_its_number,
        "does not end in _<byte-length>",
    ),
    (
        "the collision band collapsed onto one length, every name honestly renamed",
        mutate_collision_band_collapses_onto_one_length,
        "but contribute_payload.source's prose claims",
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


# --- source mutations ----------------------------------------------------------
# A different kind of mutation: these edit the COPY of check-parity-contract.py
# rather than the manifest, because what they test is
# check_own_contribute_error_paths(), which parses the checker's own source
# through the same MACP_ROOT seam. Signature is `mutate(src: str) -> str`.
#
# These can only work because run_checker() executes the REAL checker and points
# MACP_ROOT at the copy: the copy is parsed, never imported or run. So an inserted
# statement changes what the guard MEASURES without changing what any check DOES,
# and a renamed function in the copy cannot raise NameError.
#
# Every one of them must still produce syntactically valid Python. An unparseable
# copy trips the guard's read/parse branch instead, which would report "caught"
# for the wrong reason -- hence each assertion below names the guard's specific
# message, not merely a non-zero exit.


def _function_body_end_line(src: str, func: str) -> int:
    """1-based line number of `func`'s LAST top-level statement.

    Used as an insertion point: putting a statement immediately before the final
    `return errors` keeps the docstring, the signature and every existing branch
    untouched, so the only thing that moves is the append count.
    """
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func:
            return node.body[-1].lineno
    raise SystemExit("FAIL: %s() not found in the checker source -- mutation is stale" % func)


def mutate_source_error_path_added(src: str) -> str:
    """One extra `errors.append` in the tree, with no mutation covering it.

    The decay this exists to stop, in its exact shape: a new error path added to
    check_collision_vectors while check-parity-contract-test.py keeps printing
    that every path in the tree is covered.
    """
    line = _function_body_end_line(src, "check_collision_vectors")
    lines = src.splitlines(keepends=True)
    lines.insert(line - 1, '    errors.append("synthetic path added by the self-test")\n')
    return "".join(lines)


def mutate_source_error_path_deleted(src: str) -> str:
    """One `errors.append` removed from the tree.

    The guard is an EQUALITY, not a floor, so it must catch this direction too --
    a deleted path silently narrows what the checker asserts while every existing
    mutation for the REMAINING paths still passes.

    Targets check_first_byte_markers because it holds exactly ONE append, so
    "delete one path" is unambiguous and the expected count (14) does not depend
    on which of several appends got picked. The statement itself spans six lines as a
    `%` format; all seven of check_collision_vectors' are likewise multi-line `%`
    formats (of 4 to 6 lines each -- four of the seven are six-line, so do not read
    "six" as the shared property; multi-line is). Multi-line is the norm in this
    checker, not an obstacle, because the replacement below is span-based
    (`lineno - 1` through `end_lineno`) rather than line-based.
    An earlier version of this docstring claimed the target was chosen for being
    a one-line statement and contrasted it with multi-line appends elsewhere.
    Both halves were false; the real reason is the count above.
    """
    tree = ast.parse(src)
    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "check_first_byte_markers":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "append"
                        and isinstance(sub.func.value, ast.Name)
                        and sub.func.value.id == "errors"):
                    target = sub
    if target is None:
        raise SystemExit(
            "FAIL: check_first_byte_markers has no errors.append -- mutation is stale"
        )
    lines = src.splitlines(keepends=True)
    # Replace the whole statement with a `pass`, so the enclosing block does not
    # become empty and unparseable. `pass` is not an append, so the count drops.
    start, end = target.lineno - 1, target.end_lineno
    indent = len(lines[start]) - len(lines[start].lstrip())
    lines[start:end] = [" " * indent + "pass\n"]
    return "".join(lines)


def mutate_source_anchor_renamed(src: str) -> str:
    """The anchor function the call-graph walk starts from, renamed.

    A DIFFERENT failure mode from the two above, and the guard reports it
    differently: without the missing-anchor branch this would measure an empty
    tree and count 0, which an equality against 15 would catch but blame on the
    wrong thing. Renaming a CALLEE instead (check_collision_vectors, say) is the
    other mode and is caught by the equality -- see the guard's docstring.

    Only the `def` line is renamed, so the real checker's CHECKS tuple still
    resolves; the copy is parsed, not imported, so nothing raises NameError.
    """
    needle = "def check_contribute_payload("
    if src.count(needle) != 1:
        raise SystemExit(
            "FAIL: expected exactly 1 `%s`, found %d -- mutation is stale"
            % (needle, src.count(needle))
        )
    return src.replace(needle, "def check_contribute_payload_renamed(")


def mutate_source_unparseable(src: str) -> str:
    """The copied checker source is no longer valid Python.

    Covers the guard's read/parse branch. It is worth covering precisely because
    the alternative is silent: a checker whose own source cannot be parsed can
    still validate the manifest perfectly, so without this branch the append
    count would simply stop being measured and the run would stay green.

    Appending `def (` makes `ast.parse` raise while leaving the file readable, so it
    separates the parse failure from the OSError half of the same branch. It is NOT
    the smallest such edit -- a single trailing `(`, `:`, `=` or quote raises too;
    `def (` is chosen because it reads unmistakably as deliberate damage rather than
    as a stray character someone might "tidy up".

    The OSError half stays uncovered, and for a harness reason rather than a
    principled one: it needs the path to be absent or unreadable, which a
    `src -> str` mutation cannot arrange -- it can only rewrite the file's contents.

    Isolation: the checker still RUNS from the real path, so every other
    assertion behaves exactly as at baseline. Measured: 1 FAIL line, 1 site, and
    the guard returns early so nothing downstream of it reports.
    """
    return src + "\ndef (\n"


SOURCE_MUTATIONS = (
    (
        "an errors.append was added to the contribute tree with no mutation covering it",
        mutate_source_error_path_added,
        ("call tree has 16 `errors.append`", "EXPECTED_CONTRIBUTE_ERROR_PATHS pins 15"),
    ),
    (
        "an errors.append was deleted from the contribute tree",
        mutate_source_error_path_deleted,
        ("call tree has 14 `errors.append`", "EXPECTED_CONTRIBUTE_ERROR_PATHS pins 15"),
    ),
    (
        "the call-graph anchor function was renamed",
        mutate_source_anchor_renamed,
        "has no top-level check_contribute_payload()",
    ),
    (
        "the copied checker source is unparseable, so the count cannot be measured",
        mutate_source_unparseable,
        "could not be read or parsed at",
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
        pristine_src = (tree / SOURCE_REL).read_text(encoding="utf-8")

        # Baseline: the untouched copy must PASS, or every "caught" result
        # below would be meaningless (a red baseline catches everything).
        code, out = run_checker(tree)
        if code != 0:
            print("FAIL baseline: the unmutated copy does not pass:\n%s" % out, file=sys.stderr)
            return 1
        print("[OK] baseline: unmutated copy passes under MACP_ROOT")

        def judge(label: str, expect, code: int, out: str) -> None:
            """Shared verdict for both mutation kinds -- identical rules, two inputs."""
            wanted = (expect,) if isinstance(expect, str) else expect
            missing = [w for w in wanted if w not in out]
            if code == 0:
                failures.append(
                    "%s: checker PASSED a tree it should have rejected -- the "
                    "corresponding assertion in check-parity-contract.py is decorative" % label
                )
            elif missing:
                failures.append(
                    "%s: checker failed (good) but never said %s, so it failed for the wrong "
                    "reason. Output:\n%s" % (label, ", ".join(repr(m) for m in missing), out)
                )
            else:
                print("[OK] caught: %s" % label)

        # Source mutations first: they edit the copied checker rather than the
        # manifest, and running them before the manifest loop keeps the two
        # pristine-restore paths from interleaving.
        for label, mutate_src, expect in SOURCE_MUTATIONS:
            (tree / SOURCE_REL).write_text(mutate_src(pristine_src), encoding="utf-8")
            code, out = run_checker(tree)
            judge(label, expect, code, out)
            (tree / SOURCE_REL).write_text(pristine_src, encoding="utf-8")

        for label, mutate, expect in MUTATIONS:
            # A tuple means every substring must appear somewhere in the output.
            # Two assertions share one message template ("... does not match the
            # re-derived encoding ..."), so a single substring could not tell the
            # protobuf_hex branch from the legacy_json_hex one and a mis-aimed
            # mutation would look caught. This proves the intended assertion is
            # among those that fired, not that it was the only one -- see
            # mutate_protobuf_hex_undecodable for why that is the most this can
            # promise.
            data = json.loads(pristine)
            mutate(data)
            (tree / CONTRACT_REL).write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            code, out = run_checker(tree)
            judge(label, expect, code, out)
            # restore before the next mutation
            (tree / CONTRACT_REL).write_text(pristine, encoding="utf-8")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    if failures:
        for f in failures:
            print("FAIL %s" % f, file=sys.stderr)
        print("\n%d of %d parity-contract mutations went uncaught or misdiagnosed."
              % (len(failures), len(MUTATIONS) + len(SOURCE_MUTATIONS)), file=sys.stderr)
        return 1

    print("[OK] all %d mutations rejected (%d manifest, %d checker-source), each for the reason "
          "it promises -- every errors.append in the contribute_payload check tree is covered, "
          "the count of them is itself pinned, plus the out-of-tree assertions listed in this "
          "script's docstring"
          % (len(MUTATIONS) + len(SOURCE_MUTATIONS), len(MUTATIONS), len(SOURCE_MUTATIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
