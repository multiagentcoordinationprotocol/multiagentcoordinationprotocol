#!/usr/bin/env bash

# Assert the hand-maintained indexes stay in sync with what is actually on disk.
#
# Adding an RFC, a registry, or a conformance fixture requires editing several
# separate index locations by hand. Nothing else in CI notices when one of them
# is missed, so drift accumulates silently (see issue #71). This script closes
# that gap for the exhaustive enumerations:
#
#   RFCs        -> README.md repo tree, rfcs/README.md, rfcs/RFC-MACP-0001.md,
#                  CONTRIBUTING.md
#   registries  -> README.md repo tree, registries/README.md
#   fixtures    -> README.md repo tree
#
# Deliberately NOT checked: README.md's "Reading order" section. It is a curated
# narrative path, not an enumeration — it collapses RFC-0007..0011 into a single
# range entry and omits RFC-0004 on purpose. Treating it as an index would either
# fail on main today or need per-file exemptions.
#
# Direction is one-way (every file on disk appears in every index). An index
# entry pointing at a deleted file is not checked here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

FAILURES=0
CHECKS=0

fail() {
    echo "  [X] $1"
    FAILURES=$((FAILURES + 1))
}

section_result() {
    if [ "${FAILURES}" -eq "$1" ]; then
        echo "  [OK] $2"
    else
        echo "  --   $2"
    fi
}

# Extract one indented block out of a repo-tree code fence: everything after the
# header line up to the next blank line.
tree_block() {
    awk -v hdr="$2" '$0 ~ hdr { inblk = 1; next } inblk && /^[[:space:]]*$/ { exit } inblk { print }' "$1"
}

require_block() {
    if [ -z "$1" ]; then
        echo "Error: could not locate the '$2' block in README.md's repo tree."
        echo "       The tree layout changed — update tree_block() in $0."
        exit 1
    fi
}

README_RFCS="$(tree_block README.md '^  rfcs/$')"
README_REGISTRIES="$(tree_block README.md '^  registries/$')"
README_CONFORMANCE="$(tree_block README.md '^    conformance/$')"

require_block "${README_RFCS}" "rfcs/"
require_block "${README_REGISTRIES}" "registries/"
require_block "${README_CONFORMANCE}" "conformance/"

echo "Checking index sync..."
echo ""

# -- RFCs -------------------------------------------------------------------
# The glob matches the numbered spec documents only; rfcs/RFC-MACP-0001.md (the
# stable compatibility index) has no descriptive suffix and is skipped.
echo "-- RFCs (rfcs/RFC-MACP-*-*.md) --"
BEFORE=${FAILURES}
for rfc_file in rfcs/RFC-MACP-*-*.md; do
    base="$(basename "${rfc_file}")"
    num="$(echo "${base}" | sed -E 's/^(RFC-MACP-[0-9]{4}).*/\1/')"
    CHECKS=$((CHECKS + 1))

    grep -qF "${base}" <<<"${README_RFCS}" \
        || fail "${base} is missing from README.md's repo tree (rfcs/ block)"
    grep -qF "**${num} " rfcs/README.md \
        || fail "${num} is missing from rfcs/README.md's RFC set bullets"
    grep -qF "(${base})" rfcs/RFC-MACP-0001.md \
        || fail "${base} is missing from rfcs/RFC-MACP-0001.md's Normative RFCs bullets"
    grep -qF "(rfcs/${base})" CONTRIBUTING.md \
        || fail "${base} is missing from CONTRIBUTING.md's Normative RFCs list"
done
section_result "${BEFORE}" "${CHECKS} RFC file(s) checked against 4 indexes"
echo ""

# -- Registries -------------------------------------------------------------
echo "-- Registries (registries/*.md) --"
BEFORE=${FAILURES}
REGISTRY_COUNT=0
for registry_file in registries/*.md; do
    base="$(basename "${registry_file}")"
    [ "${base}" = "README.md" ] && continue
    REGISTRY_COUNT=$((REGISTRY_COUNT + 1))
    CHECKS=$((CHECKS + 1))

    grep -qF "(${base})" registries/README.md \
        || fail "${base} is missing from registries/README.md's registry list"
    grep -qF "${base}" <<<"${README_REGISTRIES}" \
        || fail "${base} is missing from README.md's repo tree (registries/ block)"
done
section_result "${BEFORE}" "${REGISTRY_COUNT} registry file(s) checked against 2 indexes"
echo ""

# -- Conformance fixtures ---------------------------------------------------
# schema.json is the fixture-format schema, not a fixture. Vector packs live in
# their own subdirectory with their own schema and are listed by directory.
echo "-- Conformance fixtures (schemas/conformance/*.json) --"
BEFORE=${FAILURES}
FIXTURE_COUNT=0
for fixture_file in schemas/conformance/*.json; do
    base="$(basename "${fixture_file}")"
    [ "${base}" = "schema.json" ] && continue
    FIXTURE_COUNT=$((FIXTURE_COUNT + 1))
    CHECKS=$((CHECKS + 1))

    grep -qF "${base}" <<<"${README_CONFORMANCE}" \
        || fail "${base} is missing from README.md's fixture list (conformance/ block)"
done
section_result "${BEFORE}" "${FIXTURE_COUNT} fixture file(s) checked against 1 index"
echo ""

echo "-------------------------------------"
if [ ${FAILURES} -gt 0 ]; then
    echo "[X] ${FAILURES} missing index entr$([ ${FAILURES} -eq 1 ] && echo y || echo ies) across ${CHECKS} checked file(s)"
    echo "    Add the file(s) named above to the index location(s) named above."
    exit 1
fi

echo "[OK] All indexes in sync (${CHECKS} files checked)"
