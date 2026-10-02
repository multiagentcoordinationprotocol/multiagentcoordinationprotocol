#!/usr/bin/env python3
"""Regression proof that check-envelope-coverage.py's assertions bite.

Same shape as scripts/check-parity-contract-test.py (and, before that,
scripts/check-prose-test.py): copy the tree, mutate the COPY, run the real
unmodified scripts/check-envelope-coverage.py against it through the
MACP_ROOT seam that script already documents for exactly this purpose, and
assert it exits non-zero with the message the mutated assertion promises.
The real repository is never mutated.

Two mutation kinds. `MUTATIONS` edit the copied tree's schema/proto content
-- each `mutate(tree: Path) -> str` reads and rewrites whichever file(s)
under `tree` it needs (schema JSON via json.load/dump, a proto file as
text), returning a short label; the harness restores all four pristine
files after every entry regardless of which it touched, so a mutation never
needs to declare its own blast radius up front. `SOURCE_MUTATIONS` are a
different kind: they edit the COPIED checker source
(scripts/check-envelope-coverage.py) itself, because what they test is
check_own_assertion_count(), which parses that file's own source through the
same MACP_ROOT seam. They work only because run_checker() executes the REAL
checker and points MACP_ROOT at the copy: the copy is parsed, never imported
or run.

Measured, not copied from the plan that first proposed this phase, and not
restated here as a standing fact either: this checker's own source holds a
module-wide count of fail()/errors.append(...) call sites pinned by
`EXPECTED_FAIL_SITES` (`check_own_assertion_count`'s own appends excluded --
see that function's docstring for why), and `len(MUTATIONS)` /
`len(SOURCE_MUTATIONS)` are this file's own counts of the same shape. Following
check-parity-contract-test.py's documented lesson ("No count of either
quantity is stated anywhere in this file -- deliberately, and this is the
third attempt at this paragraph"): a figure nothing machine-checks, in the one
file whose purpose is to stop coverage claims from drifting, is a liability,
so re-derive these three numbers by running this file rather than trusting
any number printed in a docstring, including this one. What IS stable prose:
every site gets at least one mutation except the one named below, and exactly
one site -- shape_errors' type/$ref comparison -- gets two, since one mutation
proves the top-level comparison and the other proves it also works through
the recursive "items" leg. The one checker site with no mutation at all is
documented, not hidden: `parse_proto`'s `except OSError` branch fires only
for a proto file that EXISTS but cannot be READ, which needs a permission
bit (`chmod`) this harness deliberately does not set -- following
check-parity-contract.py's own precedent of leaving an analogous OSError
half uncovered "for a harness reason rather than a principled one", and the
plan's own instruction that nothing here depends on chmod 000 (so, unlike
scripts/check-prose-test.py, no root-skip is needed).

What this file's passing run DOES and DOES NOT prove, stated plainly rather
than inherited silently (scripts/check-parity-contract-test.py:57-78 makes
the same point at length for its own file, and the point carries over
unchanged): every fail()/errors.append(...) site in check-envelope-
coverage.py, except the one documented exception above, has at least one
designated mutation that goes red when that site is removed, the site COUNT
is itself pinned by check_own_assertion_count(), and adding a site without
touching this file leaves that pin's claim printed and false -- forcing an
edit to BOTH files, not just one. It does NOT mean a site can never again go
undetected by accident: bump EXPECTED_FAIL_SITES and this file's own
site-count claim in the same commit, add no mutation, and the run stays
green with a printed coverage claim that has gone false. That half stays
honour system, exactly as the file this is modelled on says of itself.

Many mutations here trip more than one site, because the checker's own
comparisons constrain each other (deleting one $defs entry can fail both an
existence check and a reachability one). Per this repo's established
convention (scripts/check-parity-contract-test.py's "credited" rule): a
mutation is credited with covering exactly the site its `expect` substring
names, even when it incidentally trips others too -- so a deleted site
always orphans a mutation, and the cover map stays one-directional. Each
mutation below that has unavoidable overlap says so in its own docstring.

Stdlib only, no test framework -- this repo has no pytest dependency
anywhere; every check is a small driver script wired into the Makefile, and
this follows that convention.

Run: `python3 scripts/check-envelope-coverage-test.py` (exits non-zero if
any mutation is NOT caught, i.e. if an assertion has gone decorative).
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check-envelope-coverage.py"
# Only the trees the checker actually reads: schemas/proto/**, schemas/json/**
# (one "schemas" copy covers both), plus -- since check_own_assertion_count
# landed -- its own source under scripts/. The checker that RUNS is always
# the real one at REPO_ROOT (see run_checker); the copy is parsed, never
# executed, which is the whole reason a SOURCE_MUTATIONS entry can be both
# effective (the guard sees it) and side-effect-free (nothing else does).
NEEDED = ("schemas", "scripts")

SCHEMA_REL = Path("schemas") / "json" / "macp-envelope.schema.json"
CORE_PROTO_REL = Path("schemas") / "proto" / "macp" / "v1" / "core.proto"
ENVELOPE_PROTO_REL = Path("schemas") / "proto" / "macp" / "v1" / "envelope.proto"
POLICY_PROTO_REL = Path("schemas") / "proto" / "macp" / "v1" / "policy.proto"
SOURCE_REL = Path("scripts") / "check-envelope-coverage.py"

PRISTINE_RELS = (SCHEMA_REL, CORE_PROTO_REL, ENVELOPE_PROTO_REL, POLICY_PROTO_REL)


def run_checker(tree: Path) -> tuple[int, str]:
    env = dict(os.environ, MACP_ROOT=str(tree))
    proc = subprocess.run(
        [sys.executable, str(CHECKER)], env=env, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --- schema helpers --------------------------------------------------------


def read_schema(tree: Path) -> dict:
    return json.loads((tree / SCHEMA_REL).read_text(encoding="utf-8"))


def write_schema(tree: Path, data: dict) -> None:
    (tree / SCHEMA_REL).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def find_branch(data: dict, message_type: str) -> dict:
    for branch in data["allOf"]:
        const = (
            branch.get("if", {}).get("properties", {}).get("message_type", {}).get("const")
        )
        if const == message_type:
            return branch
    raise SystemExit(
        "FAIL: no allOf branch with message_type.const == %r -- mutation is stale"
        % message_type
    )


def drop_from_description(data: dict, name: str) -> None:
    """Remove `name` from message_type's "Mode-independent Core types (...)"
    enumeration, keeping the rest of the sentence (and its commas) intact."""
    desc = data["properties"]["message_type"]["description"]
    m = re.search(r"Mode-independent Core types \(([^)]*)\)", desc)
    if not m:
        raise SystemExit(
            "FAIL: message_type's description has no \"Mode-independent Core "
            "types (...)\" sentence -- mutation is stale"
        )
    names = [n.strip() for n in m.group(1).split(",")]
    if name not in names:
        raise SystemExit("FAIL: %r not in the description enumeration -- mutation is stale" % name)
    names.remove(name)
    new_sentence = "Mode-independent Core types (%s)" % ", ".join(names)
    data["properties"]["message_type"]["description"] = desc[: m.start()] + new_sentence + desc[m.end() :]


# --- proto helpers ----------------------------------------------------------


def read_proto(tree: Path, rel: Path) -> str:
    return (tree / rel).read_text(encoding="utf-8")


def write_proto(tree: Path, rel: Path, text: str) -> None:
    (tree / rel).write_text(text, encoding="utf-8")


def delete_message_block(src: str, name: str) -> str:
    """Delete `message <name> { ... }` (top-level, 0-indent) verbatim,
    including any immediately preceding comment block, leaving everything
    else untouched. Used only for whole-payload-removal mutations."""
    pattern = re.compile(
        r"(?:^(?:[ \t]*//[^\n]*\n))*^message %s \{\n(?:.*?\n)*?^\}\n" % re.escape(name),
        re.MULTILINE,
    )
    new_src, count = pattern.subn("", src, count=1)
    if count != 1:
        raise SystemExit("FAIL: message %s not found as a deletable block -- mutation is stale" % name)
    return new_src


# --- content mutations ------------------------------------------------------
# Each takes the whole copied tree and returns a short label. Each MUST make
# the checker exit non-zero with a message containing `expect`. The harness
# restores all four pristine files after every entry.


def mutate_branch_const_dropped(tree: Path) -> str:
    """A branch keeps its payload.$ref but loses its message_type.const --
    check 1's own guard against an unidentifiable branch. Measured: also
    trips the proto-vs-branch-set and branch-vs-described-set comparisons
    (each has its own dedicated mutation elsewhere), since a branch with no
    const can contribute nothing to branch_set, which loses a member as a
    direct consequence. The `expect` substring below names only the
    const-missing message itself."""
    data = read_schema(tree)
    branch = find_branch(data, "SessionCancel")
    del branch["if"]["properties"]["message_type"]["const"]
    write_schema(tree, data)
    return "SessionCancel branch const"


def mutate_description_sentence_reworded(tree: Path) -> str:
    """The "Mode-independent Core types (...)" sentence reworded so the
    regex no longer matches it at all -- the pattern-stale branch. Measured,
    correcting an earlier draft of this docstring that wrongly claimed
    isolation: this also trips BOTH set-mismatch comparisons against
    described_set, because the pattern failure makes described_set the
    EMPTY set, which disagrees with both proto_set and branch_set as a
    direct consequence, not a separate bug. Each of those has its own
    dedicated mutation elsewhere; the `expect` substring below names only
    the pattern-stale message."""
    data = read_schema(tree)
    desc = data["properties"]["message_type"]["description"]
    if "Mode-independent Core types (" not in desc:
        raise SystemExit("FAIL: expected sentence not found -- mutation is stale")
    data["properties"]["message_type"]["description"] = desc.replace(
        "Mode-independent Core types (", "Core types independent of mode: ("
    )
    write_schema(tree, data)
    return "message_type description sentence"


def mutate_allof_branch_deleted(tree: Path) -> str:
    """A whole allOf branch deleted -- proto_set now has a member
    (SessionResume) that branch_set does not. Measured: also trips
    branch-vs-described-set (branch_set lost a member described_set still
    has), which has its own dedicated mutation elsewhere; the `expect`
    substring below names only the proto-vs-branch-set message."""
    data = read_schema(tree)
    branch = find_branch(data, "SessionResume")
    data["allOf"].remove(branch)
    write_schema(tree, data)
    return "SessionResume allOf branch"


def mutate_description_member_dropped(tree: Path) -> str:
    """SessionResume dropped from the description enumeration only -- proto
    and the allOf branches both still carry it. Measured: this still trips
    TWO comparisons, not one -- proto_set != described_set (credited below)
    AND branch_set != described_set, since branch_set also still has the
    member described_set just lost; that second one has its own dedicated
    mutation elsewhere."""
    data = read_schema(tree)
    drop_from_description(data, "SessionResume")
    write_schema(tree, data)
    return "SessionResume description entry"


def mutate_branch_const_renamed(tree: Path) -> str:
    """One branch's own const renamed to a near-miss that is neither a real
    proto payload nor in the description -- isolates "branch set disagrees
    with the description enumeration" (singular "does not match") from
    "proto disagrees with the description enumeration" (plural "do not
    match"), which stays silent here since neither proto_set nor
    described_set changed. Measured, not assumed: it unavoidably trips TWO
    other sites too, both with their own dedicated mutation elsewhere --
    proto_set != branch_set (branch_set now holds "SessionResumed" instead
    of "SessionResume"), and check 2's const/$ref-disagree guard (the
    branch's const is now "SessionResumed" but its $ref still names
    SessionResumePayload). The `expect` substring here names only the one
    message credited to this mutation."""
    data = read_schema(tree)
    branch = find_branch(data, "SessionResume")
    branch["if"]["properties"]["message_type"]["const"] = "SessionResumed"
    write_schema(tree, data)
    return "SessionResume branch const renamed"


def mutate_payload_count_pin(tree: Path) -> str:
    """SessionSuspendPayload removed from core.proto AND, in the SAME edit,
    its $defs entry, allOf branch and description mention -- so proto_set,
    branch_set and described_set all shrink together and agree with each
    other. Every comparison in check 1 stays green; only
    EXPECTED_CORE_PAYLOAD_COUNT's own pin notices the set got smaller. This
    is the one mutation that justifies the count existing at all."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    core_src = delete_message_block(core_src, "SessionSuspendPayload")
    write_proto(tree, CORE_PROTO_REL, core_src)

    data = read_schema(tree)
    if "SessionSuspendPayload" not in data["$defs"]:
        raise SystemExit("FAIL: $defs.SessionSuspendPayload not found -- mutation is stale")
    del data["$defs"]["SessionSuspendPayload"]
    branch = find_branch(data, "SessionSuspend")
    data["allOf"].remove(branch)
    drop_from_description(data, "SessionSuspend")
    write_schema(tree, data)
    return "SessionSuspendPayload removed everywhere"


def mutate_defs_entry_missing_for_new_payload(tree: Path) -> str:
    """A whole new *Payload message added to core.proto with no $defs
    counterpart at all. Measured: trips FOUR other sites too -- both of
    check 1's set comparisons against proto_set (now an 8th member),
    EXPECTED_CORE_PAYLOAD_COUNT's pin, and check 3's OWN "no $defs entry"
    message for the same name (FooPayload is itself one of proto_set, so
    check_field_coverage's BFS seeds on it directly, independent of check
    2's walk). Each has its own dedicated mutation elsewhere; the `expect`
    substring below names only check 2's specific message for this name."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    if "FooPayload" in core_src:
        raise SystemExit("FAIL: FooPayload already present -- mutation is stale")
    write_proto(tree, CORE_PROTO_REL, core_src + "\nmessage FooPayload {\n  string a = 1;\n}\n")
    return "FooPayload with no $defs entry"


def mutate_defs_entry_not_object(tree: Path) -> str:
    """A $defs entry for a real Core payload loses its "type": "object" --
    check 2's shape guard, not check 2's existence guard."""
    data = read_schema(tree)
    entry = data["$defs"]["SessionCancelPayload"]
    if entry.get("type") != "object":
        raise SystemExit("FAIL: SessionCancelPayload is not type object -- mutation is stale")
    entry["type"] = "string"
    write_schema(tree, data)
    return "SessionCancelPayload $defs type"


def mutate_branch_ref_points_at_wrong_entry(tree: Path) -> str:
    """A branch's own const and its payload.$ref disagree with each other --
    const still says SessionResume, but the $ref now points at
    SessionSuspendPayload's entry."""
    data = read_schema(tree)
    branch = find_branch(data, "SessionResume")
    branch["then"]["properties"]["payload"]["$ref"] = "#/$defs/SessionSuspendPayload"
    write_schema(tree, data)
    return "SessionResume branch $ref"


def mutate_commitment_ref_defs_entry_deleted(tree: Path) -> str:
    """$defs.CommitmentRef deleted while CommitmentPayload.supersedes still
    $refs it -- the TRANSITIVE leg of check 3 (CommitmentRef is reached via
    a message-typed field, not a Core payload itself), and proof that
    reachability survives a missing $defs entry (the N-times fix from Phase
    1/2's own verification rounds): CommitmentRef must still be visited so
    whatever it points at would also still be checked."""
    data = read_schema(tree)
    if "CommitmentRef" not in data["$defs"]:
        raise SystemExit("FAIL: $defs.CommitmentRef not found -- mutation is stale")
    del data["$defs"]["CommitmentRef"]
    write_schema(tree, data)
    return "CommitmentRef $defs entry"


def mutate_defs_properties_null(tree: Path) -> str:
    """A $defs entry's "properties" set to JSON null rather than removed --
    keeps "type": "object" and the "properties" KEY present (so check 2's
    "must be type object with a properties object" stays silent, since that
    only checks for the key's absence), isolating check 3's "no properties
    object" branch, which checks the VALUE."""
    data = read_schema(tree)
    entry = data["$defs"]["SessionCancelPayload"]
    entry["properties"] = None
    write_schema(tree, data)
    return "SessionCancelPayload $defs.properties = null"


def mutate_ttl_ms_type_wrong(tree: Path) -> str:
    """$defs.SessionStartPayload.properties.ttl_ms's "type" changed from
    integer to string -- check 5's scalar branch (criterion 2(a) of Phase
    2, carried forward per that phase's own Tests note)."""
    data = read_schema(tree)
    prop = data["$defs"]["SessionStartPayload"]["properties"]["ttl_ms"]
    if prop.get("type") != "integer":
        raise SystemExit("FAIL: ttl_ms is not type integer -- mutation is stale")
    prop["type"] = "string"
    write_schema(tree, data)
    return "SessionStartPayload.ttl_ms type"


def mutate_roots_items_ref_wrong(tree: Path) -> str:
    """$defs.SessionStartPayload.properties.roots.items.$ref repointed at
    CommitmentRef instead of Root -- check 5's repeated-message branch,
    exercised through the recursive "items" leg of shape_errors (criterion
    2(b) of Phase 2). Trips the SAME call site as the mutation above (both
    land in shape_errors' type/$ref loop); kept as a separate mutation
    anyway because it is the one that proves the RECURSION works, not just
    the top-level comparison."""
    data = read_schema(tree)
    prop = data["$defs"]["SessionStartPayload"]["properties"]["roots"]
    if prop["items"].get("$ref") != "#/$defs/Root":
        raise SystemExit("FAIL: roots.items.$ref is not Root -- mutation is stale")
    prop["items"]["$ref"] = "#/$defs/CommitmentRef"
    write_schema(tree, data)
    return "SessionStartPayload.roots.items.$ref"


def mutate_roots_items_not_object(tree: Path) -> str:
    """roots.items replaced with a non-object value -- shape_errors' guard
    that "items" itself must be an object before recursing into it."""
    data = read_schema(tree)
    prop = data["$defs"]["SessionStartPayload"]["properties"]["roots"]
    prop["items"] = "not-an-object"
    write_schema(tree, data)
    return "SessionStartPayload.roots.items"


def mutate_extensions_additional_properties_not_object(tree: Path) -> str:
    """extensions.additionalProperties replaced with a non-object value --
    the map-value counterpart of the mutation above."""
    data = read_schema(tree)
    prop = data["$defs"]["SessionStartPayload"]["properties"]["extensions"]
    prop["additionalProperties"] = "not-an-object"
    write_schema(tree, data)
    return "SessionStartPayload.extensions.additionalProperties"


def mutate_resume_payload_property_not_object(tree: Path) -> str:
    """A $defs property's own value replaced with a non-object -- check 5's
    "is not an object" guard on the PROPERTY itself, distinct from the
    items/additionalProperties guards above (those guard a nested key of an
    otherwise-object property; this guards the property itself)."""
    data = read_schema(tree)
    entry = data["$defs"]["SessionResumePayload"]
    entry["properties"]["reason"] = "not-an-object"
    write_schema(tree, data)
    return "SessionResumePayload.properties.reason"


def mutate_notes_property_added(tree: Path) -> str:
    """A JSON-only property added to a $defs entry with no proto field
    behind it -- check 6's reverse direction, no allowlist by design
    (Phase 2 criterion 2(c), carried forward)."""
    data = read_schema(tree)
    props = data["$defs"]["SessionCancelPayload"]["properties"]
    if "notes" in props:
        raise SystemExit("FAIL: notes already present -- mutation is stale")
    props["notes"] = {"type": "string"}
    write_schema(tree, data)
    return "SessionCancelPayload.properties.notes"


def mutate_second_orphan_defs_entry(tree: Path) -> str:
    """A second $defs entry added with no proto message behind it and no
    JSON_ONLY_DEFS allowlist entry -- check 6's orphan list (Phase 2
    criterion 2(d), carried forward)."""
    data = read_schema(tree)
    if "SecondOrphan" in data["$defs"]:
        raise SystemExit("FAIL: SecondOrphan already present -- mutation is stale")
    data["$defs"]["SecondOrphan"] = {"type": "string"}
    write_schema(tree, data)
    return "$defs.SecondOrphan"


def mutate_base64bytes_defs_entry_deleted(tree: Path) -> str:
    """$defs.Base64Bytes deleted while every bytes-typed field still $refs
    it -- the exact gap Phase 2's own verification gate found and closed
    (issue #173 Phase 2, commit 1adc190): Base64Bytes is never visited by
    check 3's BFS (it is a scalar-mapped $ref, not a message type), so
    check 6's JSON_ONLY_DEFS-still-exists loop is its only defence."""
    data = read_schema(tree)
    if "Base64Bytes" not in data["$defs"]:
        raise SystemExit("FAIL: $defs.Base64Bytes not found -- mutation is stale")
    del data["$defs"]["Base64Bytes"]
    write_schema(tree, data)
    return "$defs.Base64Bytes"


def mutate_top_level_timestamp_deleted(tree: Path) -> str:
    """The schema's top-level `timestamp` property deleted -- check 7,
    Envelope.timestamp_unix_ms's ENVELOPE_FIELD_MAP target no longer exists
    (Phase 2 criterion 2(e), carried forward). Isolated from the mutation
    below: the proto field keeps its own name, so ENVELOPE_FIELD_MAP's own
    key-still-a-field guard stays silent."""
    data = read_schema(tree)
    if "timestamp" not in data["properties"]:
        raise SystemExit("FAIL: top-level timestamp property not found -- mutation is stale")
    del data["properties"]["timestamp"]
    write_schema(tree, data)
    return "top-level timestamp property"


def mutate_roots_type_typo(tree: Path) -> str:
    """SessionStartPayload.roots's proto type changed from Root to RootRef,
    a name no message anywhere defines -- check 3's "referenced but
    undefined" branch. Measured, not assumed: it unavoidably trips two other
    sites too. Check 5's shape comparison fires (the schema's $ref still
    says Root, so the now-RootRef-shaped expectation disagrees with it); and
    check 6's orphan list ALSO fires for $defs.Root, since nothing in the
    proto graph points at "Root" by that name any more once the field's own
    type is renamed, so check 3's BFS stops reaching it and it looks
    abandoned in $defs. Each of those has its own dedicated mutation
    elsewhere; the `expect` substring below names only the check-3 message
    this mutation is credited for."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    needle = "repeated Root roots = 7;"
    if core_src.count(needle) != 1:
        raise SystemExit("FAIL: expected exactly one %r -- mutation is stale" % needle)
    write_proto(tree, CORE_PROTO_REL, core_src.replace(needle, "repeated RootRef roots = 7;"))
    return "SessionStartPayload.roots type"


def mutate_note_field_added(tree: Path) -> str:
    """A field added to a proto message with no corresponding JSON Schema
    property -- the regression issue #173 itself exists to catch (a forward
    gap: the proto grows a field the schema never learns about)."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    needle = (
        "message SessionSuspendPayload {\n"
        "  string reason = 1;\n"
        "  // Set by the runtime; MUST match the authenticated sender of SuspendSession.\n"
        "  string suspended_by = 2;\n"
        "}\n"
    )
    if core_src.count(needle) != 1:
        raise SystemExit("FAIL: expected SessionSuspendPayload block not found verbatim -- mutation is stale")
    replacement = needle[:-2] + "  string note = 3;\n}\n"
    write_proto(tree, CORE_PROTO_REL, core_src.replace(needle, replacement))
    return "SessionSuspendPayload.note"


def mutate_banked_ms_unmapped_scalar(tree: Path) -> str:
    """SessionResumePayload.banked_ms's proto type changed from int64 to
    sint64 -- a real proto3 scalar, but one SCALAR_JSON_TYPE deliberately
    does not carry, so check 5 must refuse to guess a shape for it rather
    than silently passing."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    needle = "int64 banked_ms = 3;"
    if core_src.count(needle) != 1:
        raise SystemExit("FAIL: expected exactly one %r -- mutation is stale" % needle)
    write_proto(tree, CORE_PROTO_REL, core_src.replace(needle, "sint64 banked_ms = 3;"))
    return "SessionResumePayload.banked_ms type"


def mutate_stray_message_added(tree: Path) -> str:
    """A message with no Payload suffix and no RPC reachability added to
    core.proto -- check 4's classification, the suffix-selector hole issue
    #173 also closes."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    if "message Stray" in core_src:
        raise SystemExit("FAIL: message Stray already present -- mutation is stale")
    write_proto(tree, CORE_PROTO_REL, core_src + "\nmessage Stray {\n  string a = 1;\n}\n")
    return "message Stray"


def mutate_duplicate_message_name(tree: Path) -> str:
    """core.proto gains a message named Envelope, duplicating
    envelope.proto's real one -- the duplicate-definition guard in main()'s
    per-file merge loop. Does not perturb check 7 (it reads envelope.proto's
    OWN parse result directly, never the merged all_messages dict the
    duplicate corrupts) or check 4 (the real Envelope stays reachable via
    SendRequest.envelope regardless of which definition backs the name in
    all_messages) -- verified, not assumed, since both of those would
    otherwise be the likely place for a surprise."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    if "message Envelope " in core_src or "message Envelope{" in core_src:
        raise SystemExit("FAIL: core.proto already defines Envelope -- mutation is stale")
    write_proto(tree, CORE_PROTO_REL, core_src + "\nmessage Envelope {\n  string x = 1;\n}\n")
    return "duplicate message Envelope"


def mutate_unrecognised_construct(tree: Path) -> str:
    """A `reserved 11;` statement added inside SessionSuspendPayload -- the
    single most important mutation in this file: it proves the parser FAILS
    on a construct it does not understand, rather than silently reading a
    short field list and reporting full coverage. A parser that under-reads
    is worse than no parser, because it reports green."""
    core_src = read_proto(tree, CORE_PROTO_REL)
    needle = "message SessionSuspendPayload {\n  string reason = 1;\n"
    if core_src.count(needle) != 1:
        raise SystemExit("FAIL: expected SessionSuspendPayload opening not found verbatim -- mutation is stale")
    write_proto(
        tree, CORE_PROTO_REL,
        core_src.replace(needle, needle + "  reserved 11;\n"),
    )
    return "reserved statement inside SessionSuspendPayload"


def mutate_envelope_message_renamed(tree: Path) -> str:
    """envelope.proto's own `message Envelope` renamed -- check 7 cannot run
    at all without finding it. Unavoidably also starves check 4's
    reachability walk of the real Envelope definition (SendRequest.envelope
    now names a message that no longer exists under that name), which has
    its own dedicated mutation elsewhere; the `expect` substring below names
    only the check-7 message."""
    envelope_src = read_proto(tree, ENVELOPE_PROTO_REL)
    needle = "message Envelope {\n"
    if envelope_src.count(needle) != 1:
        raise SystemExit("FAIL: expected exactly one %r -- mutation is stale" % needle)
    write_proto(tree, ENVELOPE_PROTO_REL, envelope_src.replace(needle, "message EnvelopeRenamed {\n", 1))
    return "envelope.proto message Envelope renamed"


def mutate_timestamp_unix_ms_field_renamed(tree: Path) -> str:
    """envelope.proto's `timestamp_unix_ms` field renamed -- ENVELOPE_FIELD_
    MAP's own key is now a dead entry pointing at a proto field that no
    longer exists under that name. Unavoidably also trips the per-field "no
    corresponding top-level property" check for the renamed field itself
    (it no longer resolves through the map OR by identity); the `expect`
    substring below names only the dead-map-key message."""
    envelope_src = read_proto(tree, ENVELOPE_PROTO_REL)
    needle = "int64 timestamp_unix_ms = 7;"
    if envelope_src.count(needle) != 1:
        raise SystemExit("FAIL: expected exactly one %r -- mutation is stale" % needle)
    write_proto(tree, ENVELOPE_PROTO_REL, envelope_src.replace(needle, "int64 timestamp_ms = 7;"))
    return "envelope.proto timestamp_unix_ms renamed"


def mutate_schema_file_deleted(tree: Path) -> str:
    """macp-envelope.schema.json deleted outright -- load_schema's OSError
    branch. No upfront is_file() guard protects the schema file the way
    main() protects the three proto files, so a plain deletion (no chmod
    needed) reaches it directly."""
    (tree / SCHEMA_REL).unlink()
    return "macp-envelope.schema.json deleted"


def mutate_schema_file_invalid_json(tree: Path) -> str:
    """macp-envelope.schema.json overwritten with text that is not valid
    JSON at all -- load_schema's JSONDecodeError branch."""
    (tree / SCHEMA_REL).write_text("{ not valid json", encoding="utf-8")
    return "macp-envelope.schema.json invalid JSON"


def mutate_schema_top_level_not_object(tree: Path) -> str:
    """macp-envelope.schema.json replaced with a validly-parsing JSON value
    that is not an object -- load_schema's "not a JSON object" branch,
    distinct from the JSON-syntax branch above."""
    (tree / SCHEMA_REL).write_text("[]\n", encoding="utf-8")
    return "macp-envelope.schema.json top-level array"


def mutate_proto_file_missing(tree: Path) -> str:
    """policy.proto deleted from the tree entirely -- main()'s own
    is_file() guard over PROTO_FILES, which runs before anything else and
    short-circuits the whole checker on the first missing file."""
    (tree / POLICY_PROTO_REL).unlink()
    return "policy.proto missing"


MUTATIONS: tuple[tuple[str, object, object], ...] = (
    ("an allOf branch has payload.$ref but no message_type.const",
     mutate_branch_const_dropped,
     "payload.$ref %r but no message_type.const" % "#/$defs/SessionCancelPayload"),
    ("the message_type description sentence is reworded past recognition",
     mutate_description_sentence_reworded,
     "no longer contains a \"Mode-independent Core types (...)\" sentence"),
    ("a whole allOf branch is deleted",
     mutate_allof_branch_deleted,
     "do not match the envelope schema's allOf branch set"),
    ("a payload is dropped from the message_type description enumeration only",
     mutate_description_member_dropped,
     "do not match message_type's description enumeration"),
    ("an allOf branch's own const is renamed to a near-miss",
     mutate_branch_const_renamed,
     "does not match message_type's description enumeration"),
    ("a Core payload is removed from proto, $defs, its branch and the description together",
     mutate_payload_count_pin,
     "expected 7 Core payload"),
    ("a new *Payload message is added to core.proto with no $defs counterpart",
     mutate_defs_entry_missing_for_new_payload,
     "core.proto message FooPayload has no $defs.FooPayload entry"),
    ("a $defs entry for a real Core payload loses \"type\": \"object\"",
     mutate_defs_entry_not_object,
     "must be \"type\": \"object\" with a properties object"),
    ("a branch's const and its payload.$ref point at different $defs entries",
     mutate_branch_ref_points_at_wrong_entry,
     "its const and its payload $ref disagree"),
    ("$defs.CommitmentRef is deleted while CommitmentPayload.supersedes still $refs it",
     mutate_commitment_ref_defs_entry_deleted,
     "CommitmentRef has no $defs.CommitmentRef entry"),
    ("a $defs entry's \"properties\" is JSON null rather than absent",
     mutate_defs_properties_null,
     "has no \"properties\" object"),
    ("ttl_ms's JSON type no longer matches its proto scalar type",
     mutate_ttl_ms_type_wrong,
     "expected type 'integer', found 'string'"),
    ("roots.items.$ref points at the wrong $defs entry",
     mutate_roots_items_ref_wrong,
     "expected $ref '#/$defs/Root', found '#/$defs/CommitmentRef'"),
    ("roots.items is not an object",
     mutate_roots_items_not_object,
     "expected an \"items\" object"),
    ("extensions.additionalProperties is not an object",
     mutate_extensions_additional_properties_not_object,
     "expected an \"additionalProperties\" object"),
    ("a $defs property's own value is not an object",
     mutate_resume_payload_property_not_object,
     "is not an object"),
    ("a JSON-only property is added to a $defs entry with no proto field behind it",
     mutate_notes_property_added,
     "has no corresponding field on message SessionCancelPayload"),
    ("a second orphan $defs entry is added",
     mutate_second_orphan_defs_entry,
     "$defs.SecondOrphan is not reachable"),
    ("$defs.Base64Bytes is deleted while still $ref'd",
     mutate_base64bytes_defs_entry_deleted,
     "is listed in JSON_ONLY_DEFS"),
    ("the schema's top-level timestamp property is deleted",
     mutate_top_level_timestamp_deleted,
     "Envelope.timestamp_unix_ms"),
    ("a field's proto type references a message that does not exist anywhere",
     mutate_roots_type_typo,
     "RootRef is referenced as a message type but has no message definition"),
    ("a proto field is added with no corresponding JSON Schema property",
     mutate_note_field_added,
     "SessionSuspendPayload.note"),
    ("a field's proto type is a scalar this checker's SCALAR_JSON_TYPE does not carry",
     mutate_banked_ms_unmapped_scalar,
     "has no JSON-shape mapping"),
    ("a message with no Payload suffix and no RPC reachability is added",
     mutate_stray_message_added,
     "Stray is neither a Core payload nor reachable"),
    ("core.proto defines a message name that envelope.proto already defines",
     mutate_duplicate_message_name,
     "message Envelope is defined more than once"),
    ("an unrecognised construct appears inside an in-scope message",
     mutate_unrecognised_construct,
     "unrecognised construct inside message SessionSuspendPayload"),
    ("envelope.proto's own Envelope message is renamed",
     mutate_envelope_message_renamed,
     "message Envelope not found in envelope.proto"),
    ("envelope.proto's timestamp_unix_ms field is renamed",
     mutate_timestamp_unix_ms_field_renamed,
     "ENVELOPE_FIELD_MAP's key 'timestamp_unix_ms' is not a field"),
    ("macp-envelope.schema.json is deleted",
     mutate_schema_file_deleted,
     "could not be read"),
    ("macp-envelope.schema.json is not valid JSON",
     mutate_schema_file_invalid_json,
     "is not valid JSON"),
    ("macp-envelope.schema.json's top level is not a JSON object",
     mutate_schema_top_level_not_object,
     "does not contain a JSON object at its top level"),
    ("a proto file is missing entirely",
     mutate_proto_file_missing,
     "policy.proto not found"),
)


# --- source mutations -------------------------------------------------------
# Edit the COPY of check-envelope-coverage.py rather than the schema/proto,
# because what they test is check_own_assertion_count(). Signature is
# `mutate(src: str) -> str`. Every one must still produce syntactically valid
# Python -- an unparseable copy trips the guard's own read/parse branch
# instead, which is itself covered by mutate_source_unparseable.


def _function_body_end_line(src: str, func: str) -> int:
    """1-based line number of `func`'s LAST top-level statement -- an
    insertion point that keeps the docstring, signature and every existing
    branch untouched, so the only thing that moves is the append count."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func:
            return node.body[-1].lineno
    raise SystemExit("FAIL: %s() not found in the checker source -- mutation is stale" % func)


def mutate_source_site_added(src: str) -> str:
    """One extra `errors.append` added to a real check function, with no
    mutation covering it -- the decay this guard exists to stop."""
    line = _function_body_end_line(src, "check_classification")
    lines = src.splitlines(keepends=True)
    lines.insert(line - 1, '    errors.append("synthetic site added by the self-test")\n')
    return "".join(lines)


def mutate_source_site_removed(src: str) -> str:
    """One `fail(...)` call removed (replaced with `pass`, span-based via
    lineno/end_lineno since the call spans multiple lines) -- the guard is
    an EQUALITY, not a floor, so it must catch a site disappearing too."""
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "fail"
        ):
            # The call at main()'s "message %s is defined more than once"
            # guard -- chosen because it is reached only via a dedicated
            # mutation above (mutate_duplicate_message_name), so removing it
            # here does not interact with any OTHER mutation's own count.
            if "defined more than once" in ast.unparse(node):
                target = node
                break
    if target is None:
        raise SystemExit("FAIL: duplicate-message fail() call not found -- mutation is stale")
    lines = src.splitlines(keepends=True)
    start, end = target.lineno - 1, target.end_lineno
    indent = len(lines[start]) - len(lines[start].lstrip())
    lines[start:end] = [" " * indent + "pass\n"]
    return "".join(lines)


def mutate_source_unparseable(src: str) -> str:
    """The copied checker source is no longer valid Python -- covers the
    guard's read/parse branch. Appending `def (` makes ast.parse raise
    while leaving the file readable, separating this from the OSError half
    (uncovered here for a harness reason: a `src -> str` mutation can only
    rewrite a file's contents, never make its path absent or unreadable)."""
    return src + "\ndef (\n"


SOURCE_MUTATIONS = (
    ("a fail()/errors.append(...) site was added with no mutation covering it",
     mutate_source_site_added,
     "but EXPECTED_FAIL_SITES pins 32"),
    ("a fail()/errors.append(...) site was removed",
     mutate_source_site_removed,
     "but EXPECTED_FAIL_SITES pins 32"),
    ("the copied checker source is unparseable, so the count cannot be measured",
     mutate_source_unparseable,
     "could not be read or parsed at"),
)


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="macp-envelope-coverage-selftest-"))
    failures: list[str] = []
    try:
        tree = tmp_root / "repo"
        tree.mkdir()
        for name in NEEDED:
            shutil.copytree(REPO_ROOT / name, tree / name, symlinks=True)

        pristine = {rel: (tree / rel).read_text(encoding="utf-8") for rel in PRISTINE_RELS}
        pristine_src = (tree / SOURCE_REL).read_text(encoding="utf-8")

        # Baseline: the untouched copy must PASS, or every "caught" result
        # below would be meaningless (a red baseline catches everything).
        code, out = run_checker(tree)
        if code != 0:
            print("FAIL baseline: the unmutated copy does not pass:\n%s" % out, file=sys.stderr)
            return 1
        print("[OK] baseline: unmutated copy passes under MACP_ROOT")

        def judge(label: str, expect, code: int, out: str) -> None:
            wanted = (expect,) if isinstance(expect, str) else expect
            missing = [w for w in wanted if w not in out]
            if code == 0:
                failures.append(
                    "%s: checker PASSED a tree it should have rejected -- the "
                    "corresponding assertion in check-envelope-coverage.py is "
                    "decorative" % label
                )
            elif missing:
                failures.append(
                    "%s: checker failed (good) but never said %s, so it failed for "
                    "the wrong reason. Output:\n%s"
                    % (label, ", ".join(repr(m) for m in missing), out)
                )
            else:
                print("[OK] caught: %s" % label)

        def restore_pristine() -> None:
            for rel, text in pristine.items():
                (tree / rel).write_text(text, encoding="utf-8")

        # Source mutations first, so the two restore paths never interleave.
        for label, mutate_src, expect in SOURCE_MUTATIONS:
            (tree / SOURCE_REL).write_text(mutate_src(pristine_src), encoding="utf-8")
            code, out = run_checker(tree)
            judge(label, expect, code, out)
            (tree / SOURCE_REL).write_text(pristine_src, encoding="utf-8")

        for label, mutate, expect in MUTATIONS:
            mutate(tree)
            code, out = run_checker(tree)
            judge(label, expect, code, out)
            restore_pristine()
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    if failures:
        for f in failures:
            print("FAIL %s" % f, file=sys.stderr)
        print(
            "\n%d of %d envelope-coverage mutations went uncaught or misdiagnosed."
            % (len(failures), len(MUTATIONS) + len(SOURCE_MUTATIONS)),
            file=sys.stderr,
        )
        return 1

    print(
        "[OK] all %d mutations rejected (%d content, %d checker-source), each for "
        "the reason it promises -- every fail()/errors.append(...) site in "
        "check-envelope-coverage.py except the one documented exception "
        "(parse_proto's unreadable-but-existing-file branch) is covered, and the "
        "site count is itself pinned"
        % (len(MUTATIONS) + len(SOURCE_MUTATIONS), len(MUTATIONS), len(SOURCE_MUTATIONS))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
