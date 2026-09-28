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
  - retry.retryable_error_codes             <- every member must appear in this
    manifest's own error_codes.permanent (which check_error_codes holds to
    registries/error-codes.md, and which runs first). Membership only, never
    "the right subset"; `deprecated` codes are deliberately not admitted
  - commitment_hash.pattern                 <- schemas/conformance/cmt-hash/
    vector-schema.json's (otherwise unchecked-by-anything) hash pattern;
    every accept/reject value re-checked against the manifest's own pattern
    via re.fullmatch
  - contribute_payload.vectors[*]           <- re-derived from each vector's
    plaintext `value` with a 6-line stdlib protobuf-tag encoder and
    json.dumps, keyed on the hex field being present so a `decode_only`
    vector cannot carry an unchecked legacy_json_hex;
    the collision_* vectors additionally have the proto/JSON
    collision they exist to pin asserted directly -- their protobuf_hex
    bytes must still parse as JSON, and at least one of them must still
    read as something carrying no `value` key -- since re-derivation alone
    would stay green on a `value` edited to no longer collide
  - contribute_payload.first_byte              <- held to the vectors it
    describes: every protobuf_hex must lead with the pinned proto marker and
    every legacy_json_hex with the pinned JSON one, so a marker edited away
    from what the vectors actually encode is caught inside this one file

That list is what this script holds to a source. What remains unheld is
retry.max_retries / backoff_base_seconds / backoff_max_seconds / jitter, and all
of projection_anomaly.*: what those pin is a choice made in macp-sdk-python and
macp-sdk-typescript, not a value this repo states anywhere. The manifest marks
them "convention" instead of inventing a citation, and schemas/parity/README.md
explains why that is preferred to a fabricated source.

Note that retry is no longer wholly convention-sourced: retryable_error_codes is
now held to this manifest's own error_codes.permanent, and the three backoff
inputs, while unheld individually, are jointly constrained by the schedule they
recompute -- so the section is partly guarded and partly not, which is why
reading the bullet list above rather than a one-line summary of it matters.

Do not read coverage off this docstring, in either direction. Five review rounds
on this file each caught a summary of what is and is not checked drifting from
what CHECKS actually does, in one direction or the other; the code below is the
only description of that which cannot go stale. Read it before relying on a
value being guarded.

One check here is about this script rather than the manifest:
check_own_contribute_error_paths() parses this file's **own source** -- under the
same MACP_ROOT-relative ROOT, which is what makes it mutation-testable -- and
pins how many `errors.append` calls the contribute_payload check tree holds.
check-parity-contract-test.py prints a claim that every one of them is covered by
a mutation, and nothing previously made that claim fail when an append was added
without one. Same idiom as scripts/check-prose.py's check_check_count() own-count guard.

Every failure is accumulated and reported before exiting non-zero (this
repo's check-prose.py / check-indexes.sh convention) -- one bad value must
never mask another. Fixed-count assertions (EXPECTED_SECTION_COUNT etc.)
guard against a future deletion silently shrinking what is checked.

Run: `python3 scripts/check-parity-contract.py` (exits non-zero on any
mismatch or missing source).
"""

from __future__ import annotations

import ast
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

# The number of `errors.append` calls reachable from CONTRIBUTE_TREE_ANCHOR.
# check-parity-contract-test.py PRINTS a claim that every one of them is covered
# by a mutation; nothing made that claim fail when an append was added without
# one, which is what this pins. See check_own_contribute_error_paths() for why
# the count is derived from the call graph rather than a name list, and for the
# two distinct failure modes the guard has.
#
# Measured, not asserted: re-derive with an AST walk before editing this number.
EXPECTED_CONTRIBUTE_ERROR_PATHS = 15
CONTRIBUTE_TREE_ANCHOR = "check_contribute_payload"

# The collision_* vectors exist to pin the byte-lengths at which a canonical
# proto ContributePayload ALSO parses as JSON. Re-deriving their hex from
# their `value` (below) proves only that the pair is self-consistent -- it
# would stay green if a `value` were edited to something that no longer
# collides, leaving a vector that tests nothing. So the collision itself is
# asserted, and counted. Bump this when a collision length is legitimately
# added; the collision band is wider than the four pinned here. Bumping it also
# means editing prose: contribute_payload.source says "four" in three places,
# and no check holds that word to this number.
EXPECTED_COLLISION_COUNT = 4
COLLISION_PREFIX = "collision_"

# The four value byte-lengths contribute_payload.source names in prose ("at value
# byte-lengths 10, 13, 32 and 123 ..."). Pinned as a SET, not just per-vector, because
# name-vs-length agreement alone does not stop the band collapsing: four vectors renamed
# collision_a_10 ... collision_d_10, all 10 bytes, would each agree with their own name
# and still leave one length pinned four times while the prose claims four distinct ones.
# Bump this together with EXPECTED_COLLISION_COUNT when a length is legitimately added --
# and edit the prose, which names these numbers in contribute_payload.source.
EXPECTED_COLLISION_LENGTHS = (10, 13, 32, 123)

# A FLOOR, not an equality, on how many vectors carry a legacy_json_hex. See the
# long note at its use site in check_contribute_payload for why 7 and not 1, and
# for why lowering it would silently un-guard first_byte.legacy_json. Raise it
# when a legacy-carrying vector is legitimately added; never lower it without
# reading that note.
EXPECTED_MIN_LEGACY_VECTOR_COUNT = 7

ERROR_CODE_ROW_RE = re.compile(
    r"^\|\s*([A-Z][A-Z0-9_]*)\s*\|.*\|\s*(permanent|deprecated)\s*\|", re.MULTILINE
)
STANDARD_MODE_RE = re.compile(r"`(macp\.mode\.[a-z_]+\.v[0-9]+)`")
FENCED_JSON_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def proto_contribute(value: str) -> bytes:
    """6-line stdlib protobuf-tag encoder for ContributePayload.value (field 1,
    string): tag 0x0A, a base-128 varint length, then the UTF-8 bytes.

    Never called with "". Canonical proto3 gives a plain singular `string` field
    implicit presence, so the canonical encoding of value "" is ZERO bytes --
    byte-identical to an absent payload (multi_round.proto states this at the
    field). This function would instead return b"\\x0a\\x00", a two-byte encoding
    of a present-but-empty field, which is not canonical output for any input.

    There is deliberately no `if not value: return b""` guard. The sole caller
    (check_contribute_payload's vector loop) rejects an empty `value` before
    reaching here, so such a branch would be unreachable code -- and this file
    already refuses unreachable defensive branches on the grounds that nobody
    would notice deleting them. If a caller is ever added, reject there too
    rather than teaching this function to return a non-canonical two bytes or a
    zero-length string it has no way to express in `protobuf_hex`.
    """
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
    """Two independent things about `retry`, accumulated rather than short-circuited.

    The name is now narrower than the function: it also holds
    `retryable_error_codes` to the manifest's own `error_codes.permanent`.
    Renaming would touch the CHECKS tuple for no assurance gain, so the docstring
    carries the correction instead.

    This function used to `return` on the first failure. It accumulates now
    because the two assertions are unrelated -- a manifest with both a drifted
    schedule and a bogus retryable code must report both. The module docstring's
    rule is that one bad value must never mask another, and an early return here
    broke it the moment there were two values to check.
    """
    errors = []
    retry = sections["retry"]
    base, cap, n = retry["backoff_base_seconds"], retry["backoff_max_seconds"], retry["max_retries"]
    # 0.1 * 2**i is exact in binary for the range in play, and backoff_max
    # caps before any inexact step -- exact equality is safe here and is
    # deliberate: an epsilon comparison would hide a real drifted value.
    recomputed = [min(base * (2 ** i), cap) for i in range(n)]
    if recomputed != retry["backoff_schedule_seconds"]:
        errors.append(
            "retry.backoff_schedule_seconds %r != recomputed %r from max_retries/"
            "backoff_base_seconds/backoff_max_seconds"
            % (retry["backoff_schedule_seconds"], recomputed)
        )

    # Held to the MANIFEST's own error_codes.permanent, not to
    # registries/error-codes.md directly. check_error_codes already holds that
    # list to the registry and runs FIRST in CHECKS, so a registry rename yields
    # one clear failure there instead of two overlapping ones here. Same shape as
    # check_commitment_hash re-checking its accept/reject values against the
    # manifest's own `pattern` rather than re-reading the vector schema.
    #
    # Membership only -- deliberately NOT "the right subset". A retryable set
    # containing all 16 permanent codes, or none of the ones actually worth
    # retrying, passes. What this catches is a code that is not a canonical error
    # code at all: a typo (`RATELIMITED`), a renamed code, or an invented one.
    # Judging WHICH codes deserve a retry is an SDK policy call with no in-repo
    # source, which is exactly why `retry.source` marks this section a convention.
    #
    # `deprecated` is deliberately not admitted, so a retryable `UNAUTHORIZED`
    # fails. That is the right outcome -- a deprecated code should not be acquiring
    # new retry semantics -- and it is stated here so a reader does not mistake the
    # omission for an oversight.
    permanent = set(sections["error_codes"]["permanent"])
    for code in retry["retryable_error_codes"]:
        if code not in permanent:
            errors.append(
                "retry.retryable_error_codes contains %r, which is not a member of "
                "error_codes.permanent -- a retryable code that is not a canonical "
                "error code can never match a real error, so the retry policy would "
                "silently never fire for it (note `deprecated` codes are deliberately "
                "not admitted here)" % code
            )

    return errors


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
    cp = sections["contribute_payload"]
    vectors = cp["vectors"]
    if len(vectors) != EXPECTED_VECTOR_COUNT:
        errors.append(
            "expected %d contribute_payload.vectors, found %d"
            % (EXPECTED_VECTOR_COUNT, len(vectors))
        )

    # Name uniqueness, checked FIRST so that a duplicate-name manifest reports
    # the ambiguity before any message that names a vector -- every other error
    # in this tree identifies its subject by `name`, so on a duplicate the rest
    # of the run is ambiguous, and it should be known to be ambiguous rather
    # than silently so.
    #
    # Checker-side rather than schema-side on purpose. Draft 2020-12 has no
    # "unique by property" keyword; `"uniqueItems": true` on the array catches
    # only the exact-duplicate-OBJECT case, and two vectors sharing a name with
    # DIFFERENT values still validate -- which is precisely the case that lets
    # the collision band collapse onto one byte length under distinct-looking
    # entries (see check_collision_vectors). A schema-side half-measure would
    # also be invisible to the mutation harness, which never invokes ajv.
    seen: set[str] = set()
    for v in vectors:
        name = v.get("name", "<unnamed>")
        if name in seen:
            errors.append(
                "contribute_payload has two vectors named %r -- names are how every "
                "other message in this section identifies its subject, and how "
                "check-parity-contract-test.py's find() selects a vector to mutate, "
                "so a duplicate makes one of the pair unreachable and every "
                "name-bearing diagnostic ambiguous" % name
            )
        seen.add(name)

    errors.extend(check_first_byte_markers(cp))
    for v in vectors:
        name = v.get("name", "<unnamed>")

        # An empty `value` is rejected rather than encoded, and the manifest
        # cannot express a correct empty-value vector at all -- which is why
        # rejecting is the whole fix and `proto_contribute` needs no
        # empty-string branch.
        #
        # Canonical proto3 gives ContributePayload.value implicit presence, so
        # value "" encodes to ZERO bytes -- byte-identical to an absent payload
        # (multi_round.proto says so at the field itself). There is therefore no
        # `protobuf_hex` that correctly describes an empty value: the schema's
        # pattern is `^([0-9a-f]{2})+$`, one-or-more byte pairs, so the empty
        # string is schema-INVALID and `"0a00"` is a two-byte encoding of a
        # one-byte-length field, not of an absent one.
        #
        # A sibling section of this same manifest already states the answer:
        # contribute_acceptance.empty_payload is "reject", sourced to the
        # runtime's parse_contribute_value. So an empty-value vector would
        # contradict a section two keys away -- exactly the class of internal
        # contradiction this script exists to catch.
        #
        # `continue` rather than falling through, and it skips THREE remaining
        # per-vector checks, two of which would re-derive from `value` and
        # produce confusing secondary diagnostics ("protobuf_hex '0a00' does not
        # match the re-derived encoding '' of value ''"). The third -- the
        # "no legacy_json_hex and not marked decode_only" requirement -- does NOT
        # re-derive, and skipping it is a deliberate consequence rather than a
        # covered case: an empty-value vector is already being rejected, so
        # telling its author about a second, unrelated defect in the same vector
        # adds noise to a report they must act on anyway. Say so explicitly
        # because the earlier wording here claimed every skipped check re-derives,
        # which was not true of that one.
        if v["value"] == "":
            errors.append(
                "contribute_payload vector %r has an empty `value` -- canonical proto3 gives "
                "ContributePayload.value implicit presence, so an empty value encodes to zero "
                "bytes, byte-identical to an absent payload, and no protobuf_hex can describe "
                "it (the schema's `^([0-9a-f]{2})+$` makes the empty string invalid). "
                "contribute_acceptance.empty_payload already pins this case as \"reject\"" % name
            )
            continue

        expected_proto = proto_contribute(v["value"]).hex()
        if v["protobuf_hex"] != expected_proto:
            errors.append(
                "contribute_payload vector %r: protobuf_hex %r does not match "
                "the re-derived encoding %r of value %r"
                % (name, v["protobuf_hex"], expected_proto, v["value"])
            )
        # Keyed on the field being PRESENT, not on `decode_only` being absent.
        # Gating on `decode_only` left a hole: the schema permits decode_only
        # alongside a hand-written legacy_json_hex, so on such a vector the field
        # was re-derived against nothing and could hold arbitrary bytes --
        # including bytes that round-trip byte-identically through the canonical
        # proto encoding, the one thing decode_order's tie-break assumes cannot
        # happen on the legacy side. `decode_only` is now read as permission to
        # omit the legacy form rather than as an exemption from checking it: a
        # decode_only vector may still carry one, and it is re-derived like any
        # other.
        actual_json = v.get("legacy_json_hex")
        if actual_json is None:
            if not v.get("decode_only"):
                errors.append(
                    "contribute_payload vector %r has no legacy_json_hex and is not "
                    "marked decode_only -- one or the other is required, or the vector "
                    "silently stops covering the legacy form" % name
                )
        else:
            expected_json = legacy_json_bytes(v["value"]).hex()
            if actual_json != expected_json:
                errors.append(
                    "contribute_payload vector %r: legacy_json_hex %r does not match "
                    "the re-derived encoding %r of value %r"
                    % (name, actual_json, expected_json, v["value"])
                )
    # A floor on how many vectors carry the legacy form at all. Styled on
    # check_collision_vectors' value-key floor: a floor, not an equality.
    #
    # Everything above checks each legacy_json_hex that EXISTS. Nothing checked
    # how many exist -- and `decode_only: true` is a schema-legal way to omit the
    # field, so the whole legacy half of this section could be deleted in one
    # green, schema-valid commit by marking every vector decode_only. Nothing
    # else would notice: the per-vector requirement is satisfied by decode_only,
    # the re-derivation has nothing left to re-derive, and
    # check_first_byte_markers SKIPS vectors with no legacy hex -- so
    # first_byte.legacy_json would silently stop being checked at all, and could
    # then be set to any byte. That last consequence is why this floor is what
    # keeps the legacy marker non-vacuous, and why lowering it would silently
    # un-guard that marker too.
    #
    # A floor of 7 rather than 1 or an equality:
    #   - 1 would keep first_byte.legacy_json non-vacuous while still permitting
    #     6 of the 7 legacy forms to be deleted -- the coverage this section is
    #     for, gone, with one token vector left to keep the marker honest.
    #   - an equality would break on every legitimate vector addition, which is
    #     already governed by EXPECTED_VECTOR_COUNT and which the manifest's own
    #     README calls a MINOR bump. A new decode_only vector must not turn this
    #     red.
    # So: 7 catches deletion, and stays green when the section legitimately grows.
    legacy_carriers = [v for v in vectors if v.get("legacy_json_hex") is not None]
    if len(legacy_carriers) < EXPECTED_MIN_LEGACY_VECTOR_COUNT:
        errors.append(
            "only %d contribute_payload vector(s) carry a legacy_json_hex, below the floor of "
            "%d -- `decode_only` is a schema-legal way to omit the field, so without this floor "
            "the legacy half of this section could be deleted in one green commit, taking "
            "first_byte.legacy_json's only non-vacuous check with it (check_first_byte_markers "
            "skips vectors with no legacy hex)"
            % (len(legacy_carriers), EXPECTED_MIN_LEGACY_VECTOR_COUNT)
        )

    errors.extend(check_collision_vectors(vectors))
    return errors


def check_first_byte_markers(cp: dict) -> list[str]:
    """Hold contribute_payload.first_byte to the vectors it describes.

    `first_byte` pins the two discriminator bytes a decoder keys on: 0x0a for
    canonical proto and 0x7b for legacy JSON. Both are traceable to
    multi_round.proto -- `value` as field 1 fixes the proto tag, and the comment
    naming the legacy form `{"value": ""}` fixes the JSON one -- but only as
    prose no script parses, and neither byte was held to anything before this
    ran. What catches drift is the vectors: every hex in the manifest is
    re-derived from its plaintext `value` above, so a marker edited away from the
    byte the vectors actually lead with is a contradiction inside one file.

    That division of labour matters, because this function is NOT what makes a
    legacy_json_hex trustworthy -- the re-derivation above is, now that it keys
    on the field being present rather than on `decode_only` being absent. A
    re-derived legacy form always leads with `{`, so on a manifest whose hexes
    all re-derive, the only thing left for this check to catch is a drifted
    marker -- which is exactly what it is for. On a manifest that is already
    failing re-derivation it will add its own complaint too; that is noise on an
    already-red run, not a second opinion.

    Do not read these markers as a proof about protobuf, and do not reach for a
    wire-format argument to make them one -- every previous attempt at one in
    this docstring's history was wrong, each in a different way, because whether a
    `{`-leading byte string parses, and whether it then round-trips, depend on
    the group's termination and on the runtime's unknown-field handling. That
    argument belongs in the consumers' decode paths, where all three make it
    carefully; macp-runtime's parse_contribute_value docstring and
    macp-sdk-python's DiscardUnknownFields comment are the two clearest. What
    this function asserts is narrower and entirely local: the pinned marker
    bytes agree with the bytes the vectors themselves encode.

    macp-runtime asserts these same two markers against its vendored copy
    (tests/parity_contract.rs, `contribute_payload_first_byte_markers_match_vectors`),
    ungated by decode_only, so asserting them here keeps a consumer from being
    the first to notice a drifted manifest.

    Shape is not re-validated here. macp-parity-contract.schema.json requires
    first_byte with both keys present and each matching `^0x[0-9a-f]{2}$`, and
    scripts/validate-json.sh validates the manifest against that schema before
    this script runs, so a defensive branch for a malformed marker would be one
    no manifest edit could reach -- unreachable code nobody would notice
    deleting. Bare subscripts here, matching the rest of this file.
    """
    errors = []
    for key, hex_field in (("protobuf", "protobuf_hex"), ("legacy_json", "legacy_json_hex")):
        marker = cp["first_byte"][key]
        for v in cp["vectors"]:
            actual = v.get(hex_field)
            if actual is None:
                continue  # a decode_only vector legitimately carries no legacy_json_hex
            if not actual.startswith(marker[2:]):
                errors.append(
                    "contribute_payload vector %r: %s starts with %r, but "
                    "first_byte.%s pins %s -- the vector and the pinned discriminator "
                    "byte disagree"
                    % (v.get("name", "<unnamed>"), hex_field, actual[:2], key, marker)
                )
    return errors


def check_collision_vectors(vectors: list) -> list[str]:
    """Assert every collision_* vector actually collides.

    The point of these vectors is that the canonical proto encoding of `value`
    is ALSO parseable as JSON, because the field-1 tag byte and the length
    varint are themselves insignificant JSON whitespace (or, at value length
    123, the literal `{`). That property lives in the bytes, not in the
    manifest's shape, so nothing above would notice if it were lost: a `value`
    edited to something that no longer collides re-derives to a perfectly
    self-consistent hex pair.

    Five things are asserted, through seven `errors.append` calls. The two counts
    differ for a reason worth stating, since a reader counting appends against
    numbered claims would otherwise conclude the list is incomplete:

      (0) the pinned collision-vector COUNT (EXPECTED_COLLISION_COUNT), which the
          four numbered items below deliberately do not cover and which predates
          them -- one append;
      (1) two appends: an undecodable protobuf_hex is reported separately from
          hex that decodes but does not parse as JSON, because the diagnostics are
          not interchangeable (one is a malformed field, the other a vector that
          has stopped colliding);
      (2) one append;
      (3) two appends: a name with no trailing number at all is reported
          separately from a number that disagrees with the value, because the
          first leaves the pinned length UNSTATED -- such a vector contributes no
          length and would otherwise fall out of both (3) and (4) in silence;
      (4) one append.

    (1) Every collision_* vector's proto bytes still
    parse as JSON -- any JSON value, deliberately not only an object: the
    collision band includes lengths whose JSON reading is a bare number or
    string (each SDK's own 1-127 sweep enumerates them), and requiring an
    object here would reject a legitimate future vector at such a length. (2) At least one
    collision_* vector's JSON reading carries no `value` key at all, which is
    the most destructive reading of the class -- a decoder extracting `value`
    from it gets nothing rather than something wrong. That is the property
    justifying a vector at length 10 alongside the legacy-shaped ones, so it is
    held rather than left to prose. A floor, not an equality: pinning a second
    such length later is a legitimate edit, not a regression.

    (3) Each collision_* name's trailing _<int> equals its `value`'s UTF-8 byte
    length, which turns the names from decoration into the statement of which
    length each vector pins. (4) The multiset of those lengths is exactly
    EXPECTED_COLLISION_LENGTHS, which is what makes the four numbers in
    contribute_payload.source's prose load-bearing.

    (4) is not redundant with (3), and this is the reason both exist: under (3)
    alone the band can be collapsed onto a single length -- rename the four to
    collision_a_10 ... collision_d_10 and re-encode every value to 10 bytes, and
    each name still agrees with its own value while three of the four pinned
    lengths are gone. Distinct names also survive the duplicate-name check, so
    nothing else would catch it. Conversely (3) is not redundant with (4): (4)
    compares lengths only, so two vectors could swap names and stay green.

    Note that length 123 is the case where the length varint IS the `{` byte, so
    keying the check on the name's trailing number is also what keeps that pun
    honest -- collision_no_leading_brace_123 is the only vector whose collision
    comes from the varint rather than from whitespace.

    The mirror-image property -- that a legacy_json_hex can never be misread as
    canonical proto -- is not this function's job and needs no assertion of its
    own. It follows from the re-derivation in check_contribute_payload(), which
    now keys on `legacy_json_hex` being present rather than on `decode_only`
    being absent: every legacy form in the file is therefore json.dumps output,
    which always leads with `{`, and can never be the canonical encoding of
    anything.
    """
    errors = []
    collisions = [v for v in vectors if v.get("name", "").startswith(COLLISION_PREFIX)]

    if len(collisions) != EXPECTED_COLLISION_COUNT:
        errors.append(
            "expected %d %s* vectors, found %d -- a collision vector may have been "
            "removed or renamed" % (EXPECTED_COLLISION_COUNT, COLLISION_PREFIX, len(collisions))
        )

    without_value_key = []
    pinned_lengths = []
    for v in collisions:
        name = v.get("name", "<unnamed>")

        # The trailing _<int> in a collision_* name IS the value byte-length it pins.
        # Read only the LAST underscore-separated token: names carry descriptive
        # middles too (collision_no_leading_brace_123), so a regex over the whole
        # name would match the wrong number.
        suffix = name.rsplit("_", 1)[-1]
        if not suffix.isdigit():
            # Reported distinctly, and deliberately not skipped silently: a
            # collision vector renamed to drop its number would otherwise leave
            # both length checks below with nothing to say about it.
            errors.append(
                "contribute_payload vector %r matches %s* but its name does not end in "
                "_<byte-length>, so the length it pins is unstated and unchecked -- the "
                "collision band's lengths are what contribute_payload.source claims in prose"
                % (name, COLLISION_PREFIX)
            )
        else:
            claimed = int(suffix)
            actual = len(v["value"].encode("utf-8"))
            pinned_lengths.append(actual)
            if claimed != actual:
                errors.append(
                    "contribute_payload vector %r claims value byte length %d in its name "
                    "but its `value` is %d UTF-8 bytes -- the name is the only statement of "
                    "which collision length this vector pins, so a disagreement makes it "
                    "decorative" % (name, claimed, actual)
                )

        raw = v["protobuf_hex"]
        try:
            decoded_bytes = bytes.fromhex(raw)
        except ValueError as exc:
            # Not reachable while the schema's hex `pattern` holds and the
            # unconditional re-derivation above runs, but reported distinctly
            # so it can never be misread as "the collision was lost".
            errors.append(
                "contribute_payload vector %r: protobuf_hex %r is not decodable hex (%s)"
                % (name, raw, exc)
            )
            continue
        try:
            # json.JSONDecodeError and UnicodeDecodeError are both ValueError.
            decoded = json.loads(decoded_bytes.decode("utf-8"))
        except ValueError as exc:
            errors.append(
                "contribute_payload vector %r: its protobuf_hex bytes do not parse as JSON "
                "(%s), so the proto/JSON collision this vector exists to pin no longer "
                "holds -- the vector is decorative" % (name, exc)
            )
            continue
        if not isinstance(decoded, dict) or "value" not in decoded:
            without_value_key.append(name)

    if sorted(pinned_lengths) != sorted(EXPECTED_COLLISION_LENGTHS):
        errors.append(
            "the %s* vectors pin value byte lengths %s, but contribute_payload.source's prose "
            "claims %s -- a length was dropped, duplicated, or moved, so the band the "
            "tie-break exists for is no longer the band that is pinned"
            % (COLLISION_PREFIX, sorted(pinned_lengths), sorted(EXPECTED_COLLISION_LENGTHS))
        )

    if collisions and not without_value_key:
        errors.append(
            "expected at least 1 %s* vector whose JSON reading carries no `value` key "
            "(the branch where a decoder loses the value entirely rather than returning a "
            "wrong one); none of %s does, so that branch is no longer pinned"
            % (COLLISION_PREFIX, sorted(v.get("name", "<unnamed>") for v in collisions))
        )
    return errors


def check_own_contribute_error_paths(sections: dict) -> list[str]:
    """Pin the number of `errors.append` calls in the contribute_payload check tree.

    `sections` is unused. The signature matches so this can sit in CHECKS with
    the rest; what it reads is this script's own source.

    WHY THIS IS NOT REDUNDANT WITH THE SELF-TEST.
    scripts/check-parity-contract-test.py asserts every error path in this tree
    has a mutation that catches its removal, and PRINTS that claim on success.
    But it enumerates the mutations it has, not the appends that exist -- so
    adding an append with no mutation leaves the claim printed and false. The
    same decay that scripts/check-prose.py's check_check_count() own-count guard exists to
    stop, and this is modelled on it directly: parse own source under ROOT, guard
    unreadable/unparseable, guard a missing anchor, refuse a count of zero.

    WHY IT LIVES IN THE CHECKER AND NOT IN THE SELF-TEST.
    The self-test runs THIS script against a COPIED tree via MACP_ROOT. Because
    the read below is ROOT-relative, the copy's source is what gets parsed, so a
    mutation can edit it -- which is what makes the guard itself testable. In the
    self-test the guard would have no harness-native mutation at all: every
    MUTATIONS entry is `mutate(data: dict) -> str` over the manifest JSON.

    WHY THE FUNCTION SET COMES FROM THE CALL GRAPH.
    A hardcoded name tuple reintroduces the decay: an append added in a NEW
    helper called from the anchor would leave the count right and the claim
    false. So walk `ast.Call` out of the anchor, keep the names that are
    top-level functions here, and repeat transitively. Today that finds five:
    check_contribute_payload, check_first_byte_markers, check_collision_vectors,
    proto_contribute, legacy_json_bytes.

    WHY `errors.append` AND NOT ANY `.append`.
    This tree holds three non-`errors` appends -- `without_value_key.append`,
    `pinned_lengths.append`, and `out.append` inside proto_contribute. A naive
    any-`.append` count reads 18 where the real figure is 15, so the match is on
    `errors.append` specifically.

    TWO FAILURE MODES, DELIBERATELY DIFFERENT, AND ONE IS NOT THE OTHER.
    (a) Renaming or deleting the ANCHOR trips the missing-anchor branch below, by
        name. It does NOT silently measure an empty tree and report 0.
    (b) Renaming a CALLEE -- check_collision_vectors, say -- does not trip (a) at
        all: the walk just stops finding it and the count drops by that
        function's appends. What catches that is the EQUALITY, which is why this
        is an equality and not a `>=` floor. Do not assume (a) covers (b).

    THE COUNT IS SCOPED TO THIS TREE, not the whole script. Other sections'
    appends are outside it by design -- check_retry_schedule's membership check is
    one -- and the self-test says the same thing about its coverage claim.

    ONE OF THIS FUNCTION'S FOUR BRANCHES HAS NO MUTATION. The self-test covers
    the missing-anchor branch, the count-mismatch branch (in both directions) and
    the parse half of the read/parse branch. What it does NOT cover is the
    zero-count branch, which needs a checker with no error paths at all -- reached
    only by neutering all fifteen appends at once, a degenerate tree rather than
    plausible drift. The OSError half of the read/parse branch is also uncovered,
    for a harness reason rather than a principled one: every SOURCE_MUTATIONS entry
    is `mutate(src: str) -> str`, which rewrites the file's contents and so cannot
    make the path absent or unreadable -- which is what an OSError needs (a missing
    file, a missing directory, or a permission bit; any of the three, not one
    specific tree shape).

    An earlier version of this paragraph claimed the whole read/parse branch was
    impractical to reach. That was false -- appending `def (` to the copy takes
    one line -- and the branch is now covered.

    Note also that this function's own appends are NOT in the count it pins -- it
    is not in the anchor's call tree -- so a branch added here never needs the
    constant bumped.
    """
    errors: list[str] = []
    src_path = ROOT / "scripts" / "check-parity-contract.py"
    try:
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        errors.append(
            "check-parity-contract.py could not be read or parsed at %s, so the number of "
            "error paths in its own contribute_payload check tree is unknown: %s"
            % (src_path, exc)
        )
        return errors

    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    if CONTRIBUTE_TREE_ANCHOR not in funcs:
        errors.append(
            "check-parity-contract.py has no top-level %s(), which is the anchor this count "
            "walks out from -- renaming it makes the error-path count unmeasurable, and the "
            "count must not silently become 0. Update CONTRIBUTE_TREE_ANCHOR alongside the "
            "rename." % CONTRIBUTE_TREE_ANCHOR
        )
        return errors

    reached: set[str] = set()
    stack = [CONTRIBUTE_TREE_ANCHOR]
    while stack:
        name = stack.pop()
        if name in reached:
            continue
        reached.add(name)
        for node in ast.walk(funcs[name]):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in funcs):
                stack.append(node.func.id)

    found = 0
    for name in sorted(reached):
        for node in ast.walk(funcs[name]):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "append"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "errors"):
                found += 1

    if found == 0:
        errors.append(
            "the %s() call tree contains no `errors.append` at all -- a count of 0 is never "
            "right for a check whose whole job is to report mismatches, so this is a broken "
            "measurement rather than a real result" % CONTRIBUTE_TREE_ANCHOR
        )
        return errors

    if found != EXPECTED_CONTRIBUTE_ERROR_PATHS:
        errors.append(
            "the %s() call tree has %d `errors.append` call(s), but "
            "EXPECTED_CONTRIBUTE_ERROR_PATHS pins %d (tree: %s). "
            "check-parity-contract-test.py prints a claim that every one of them is covered by "
            "a mutation; adding or removing a path without touching that file would leave the "
            "claim printed and false. Add the mutation, then bump the constant -- in that order."
            % (CONTRIBUTE_TREE_ANCHOR, found, EXPECTED_CONTRIBUTE_ERROR_PATHS,
               ", ".join(sorted(reached)))
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
    check_own_contribute_error_paths,
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
