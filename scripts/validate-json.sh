#!/usr/bin/env bash

# Validate JSON examples against the MACP JSON Schemas

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# MACP_ROOT lets the mutation proofs in the acceptance criteria run against a
# throwaway tree. Without it every check resolves from BASH_SOURCE and therefore
# always scans the real repository, which makes "prove it by mutating a copy"
# impossible -- including the missing-schema guard below, whose path is absolute.
PROJECT_ROOT="${MACP_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"

ENVELOPE_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-envelope.schema.json"
MANIFEST_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-agent-manifest.schema.json"
DESCRIPTOR_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-mode-descriptor.schema.json"
POLICY_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-policy-descriptor.schema.json"
SESSION_METADATA_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-session-metadata.schema.json"
SESSION_LIFECYCLE_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-session-lifecycle-event.schema.json"
RUN_DESCRIPTOR_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-run-descriptor.schema.json"
AGENT_BOOTSTRAP_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-agent-bootstrap.schema.json"
EXAMPLES_DIR="${PROJECT_ROOT}/examples/json"
DISCOVERY_DIR="${PROJECT_ROOT}/examples/discovery"
TRANSCRIPT_GLOB="${PROJECT_ROOT}/examples/*.json"
CONFORMANCE_DIR="${PROJECT_ROOT}/schemas/conformance"
CONFORMANCE_SCHEMA="${CONFORMANCE_DIR}/schema.json"
INVALID_ENVELOPE_DIR="${PROJECT_ROOT}/schemas/json/tests/invalid"
INVALID_POLICY_RULES_DIR="${PROJECT_ROOT}/schemas/json/tests/invalid-policy-rules"
DECISION_RULES_SCHEMA="${PROJECT_ROOT}/schemas/json/policy/decision-rules.schema.json"
POLICY_RULES_SCHEMA_DIR="${PROJECT_ROOT}/schemas/json/policy"
RULES_EXTRACTOR="${PROJECT_ROOT}/scripts/extract-policy-rules.py"
# A manifest count, not a convenience. Every silent-loss vector in the extractor --
# a fence whose info string stops matching, a `mode` key renamed, a file deleted --
# lowers this number while every remaining instance still passes. Without the pin the
# run stays green with less coverage than it reports. Bump it when adding a rules object.
EXPECTED_RULES_INSTANCES=25
INVALID_QUORUM_RULES_DIR="${PROJECT_ROOT}/schemas/json/tests/invalid-quorum-rules"
QUORUM_RULES_SCHEMA="${PROJECT_ROOT}/schemas/json/policy/quorum-rules.schema.json"

echo "Validating JSON examples against schemas..."
echo ""

# Check if ajv-cli is installed
if ! command -v ajv >/dev/null 2>&1; then
    echo "Error: ajv-cli is not installed"
    echo "Install with: npm install -g ajv-cli"
    echo "Or run: make install-tools"
    exit 1
fi

# Count total and validated files
TOTAL=0
VALIDATED=0

# Validate each JSON example file against envelope schema
echo "-- Envelope examples (${EXAMPLES_DIR}/*.json) --"
echo "Schema: ${ENVELOPE_SCHEMA}"
echo ""

for example_file in "${EXAMPLES_DIR}"/*.json; do
    if [ -f "$example_file" ]; then
        TOTAL=$((TOTAL + 1))
        echo "Validating: $(basename "$example_file")"

        if ajv validate -s "${ENVELOPE_SCHEMA}" -d "${example_file}" --spec=draft2020 --strict=false; then
            VALIDATED=$((VALIDATED + 1))
            echo "  [OK] Valid"
        else
            echo "  [X] Invalid"
            exit 1
        fi
        echo ""
    fi
done

# Validate discovery examples against their respective schemas
if [ -d "$DISCOVERY_DIR" ]; then
    echo "-- Discovery examples (${DISCOVERY_DIR}/*.json) --"
    echo ""

    for manifest_file in "${DISCOVERY_DIR}"/agent_manifest*.json; do
        if [ -f "$manifest_file" ]; then
            TOTAL=$((TOTAL + 1))
            echo "Validating: discovery/$(basename "$manifest_file") against agent-manifest schema"

            if ajv validate -s "${MANIFEST_SCHEMA}" -d "${manifest_file}" --spec=draft2020 --strict=false; then
                VALIDATED=$((VALIDATED + 1))
                echo "  [OK] Valid"
            else
                echo "  [X] Invalid"
                exit 1
            fi
            echo ""
        fi
    done

    for descriptor_file in "${DISCOVERY_DIR}"/mode_descriptor*.json; do
        if [ -f "$descriptor_file" ]; then
            TOTAL=$((TOTAL + 1))
            echo "Validating: discovery/$(basename "$descriptor_file") against mode-descriptor schema"

            if ajv validate -s "${DESCRIPTOR_SCHEMA}" -d "${descriptor_file}" --spec=draft2020 --strict=false; then
                VALIDATED=$((VALIDATED + 1))
                echo "  [OK] Valid"
            else
                echo "  [X] Invalid"
                exit 1
            fi
            echo ""
        fi
    done

    for policy_file in "${DISCOVERY_DIR}"/policy_descriptor*.json; do
        if [ -f "$policy_file" ]; then
            TOTAL=$((TOTAL + 1))
            echo "Validating: discovery/$(basename "$policy_file") against policy-descriptor schema"

            if ajv validate -s "${POLICY_SCHEMA}" -d "${policy_file}" --spec=draft2020 --strict=false; then
                VALIDATED=$((VALIDATED + 1))
                echo "  [OK] Valid"
            else
                echo "  [X] Invalid"
                exit 1
            fi
            echo ""
        fi
    done

    # Validate any discovery file whose name prefix matches a schema.
    # Each pair is "<filename-glob>:<schema-path>:<label>".
    EXTRA_DISCOVERY_PAIRS=(
        "session_metadata:${SESSION_METADATA_SCHEMA}:session-metadata"
        "session_lifecycle_event:${SESSION_LIFECYCLE_SCHEMA}:session-lifecycle-event"
        "run_descriptor:${RUN_DESCRIPTOR_SCHEMA}:run-descriptor"
        "agent_bootstrap:${AGENT_BOOTSTRAP_SCHEMA}:agent-bootstrap"
    )
    for pair in "${EXTRA_DISCOVERY_PAIRS[@]}"; do
        prefix="${pair%%:*}"
        rest="${pair#*:}"
        schema="${rest%%:*}"
        label="${rest##*:}"
        for example_file in "${DISCOVERY_DIR}/${prefix}"*.json; do
            if [ -f "$example_file" ]; then
                TOTAL=$((TOTAL + 1))
                echo "Validating: discovery/$(basename "$example_file") against ${label} schema"

                if ajv validate -s "${schema}" -d "${example_file}" --spec=draft2020 --strict=false; then
                    VALIDATED=$((VALIDATED + 1))
                    echo "  [OK] Valid"
                else
                    echo "  [X] Invalid"
                    exit 1
                fi
                echo ""
            fi
        done
    done
fi

echo "-- Composite transcripts and policy examples --"
echo "  Syntax check, and (for transcripts with a 'messages' array) per-envelope validation."
echo ""

TMP_ENV_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_ENV_DIR}"' EXIT

for transcript in ${TRANSCRIPT_GLOB}; do
    if [ -f "$transcript" ]; then
        TOTAL=$((TOTAL + 1))
        base="$(basename "$transcript")"
        echo "Validating JSON syntax: ${base}"

        if command -v python3 >/dev/null 2>&1; then
            SYNTAX_OK=$(python3 -c "import json, sys; json.load(open(sys.argv[1])); print('ok')" "$transcript" 2>/dev/null)
        elif command -v node >/dev/null 2>&1; then
            SYNTAX_OK=$(node -e "try { JSON.parse(require('fs').readFileSync(process.argv[1],'utf8')); console.log('ok') } catch(e) { process.exit(1) }" "$transcript" 2>/dev/null)
        else
            echo "  [!] Skipping: neither python3 nor node available for syntax check"
            SYNTAX_OK="skip"
        fi

        if [ "$SYNTAX_OK" = "ok" ] || [ "$SYNTAX_OK" = "skip" ]; then
            VALIDATED=$((VALIDATED + 1))
            echo "  [OK] Valid JSON"
        else
            echo "  [X] Invalid JSON"
            exit 1
        fi

        # If the document has a top-level "messages" array of envelopes,
        # validate every envelope against the envelope schema.
        if command -v python3 >/dev/null 2>&1; then
            MSG_COUNT=$(python3 -c "
import json, os, sys
doc = json.load(open(sys.argv[1]))
# Transcripts may carry envelopes under 'messages' or 'transcript'.
msgs = doc.get('messages')
if not isinstance(msgs, list):
    msgs = doc.get('transcript')
if not isinstance(msgs, list):
    print(0); sys.exit(0)
out_dir = sys.argv[2]
count = 0
for i, msg in enumerate(msgs):
    # Only validate dict entries that look like MACP envelopes
    # (i.e. have both 'macp_version' and 'message_type').
    if not (isinstance(msg, dict) and 'macp_version' in msg and 'message_type' in msg):
        continue
    with open(os.path.join(out_dir, f'msg_{i:03d}.json'), 'w') as f:
        json.dump(msg, f)
    count += 1
print(count)
" "$transcript" "${TMP_ENV_DIR}" 2>/dev/null || echo 0)

            if [ "${MSG_COUNT}" -gt 0 ]; then
                echo "  Validating ${MSG_COUNT} envelope(s) inside ${base}..."
                for i in $(seq 0 $((MSG_COUNT - 1))); do
                    idx=$(printf "%03d" "$i")
                    env_file="${TMP_ENV_DIR}/msg_${idx}.json"
                    if ! ajv validate -s "${ENVELOPE_SCHEMA}" -d "${env_file}" --spec=draft2020 --strict=false >/dev/null 2>&1; then
                        echo "  [X] Envelope #${i} in ${base} failed envelope-schema validation:"
                        ajv validate -s "${ENVELOPE_SCHEMA}" -d "${env_file}" --spec=draft2020 --strict=false || true
                        exit 1
                    fi
                    rm -f "${env_file}"
                done
                echo "  [OK] All ${MSG_COUNT} envelopes valid against envelope schema"
            fi
        fi
        echo ""
    fi
done

# Validate conformance fixtures against the fixture-format schema.
# lint_fixtures.py checks internal consistency; this checks structural shape.
if [ -f "${CONFORMANCE_SCHEMA}" ]; then
    echo "-- Conformance fixtures (${CONFORMANCE_DIR}/*.json) --"
    echo "Schema: ${CONFORMANCE_SCHEMA}"
    echo ""

    for fixture_file in "${CONFORMANCE_DIR}"/*.json; do
        if [ -f "$fixture_file" ] && [ "$(basename "$fixture_file")" != "schema.json" ]; then
            TOTAL=$((TOTAL + 1))
            echo "Validating: conformance/$(basename "$fixture_file")"

            if ajv validate -s "${CONFORMANCE_SCHEMA}" -d "${fixture_file}" --spec=draft2020 --strict=false; then
                VALIDATED=$((VALIDATED + 1))
                echo "  [OK] Valid"
            else
                echo "  [X] Invalid"
                exit 1
            fi
            echo ""
        fi
    done
fi

# Negative tests: envelopes that MUST be rejected by the envelope schema.
# If one of these validates, a schema change has loosened a constraint.
if [ -d "${INVALID_ENVELOPE_DIR}" ]; then
    echo "-- Negative envelope tests (${INVALID_ENVELOPE_DIR}/*.json) --"
    echo "  Each fixture MUST FAIL envelope-schema validation."
    echo ""

    for invalid_file in "${INVALID_ENVELOPE_DIR}"/*.json; do
        if [ -f "$invalid_file" ]; then
            TOTAL=$((TOTAL + 1))
            echo "Validating (expect reject): tests/invalid/$(basename "$invalid_file")"

            if ajv validate -s "${ENVELOPE_SCHEMA}" -d "${invalid_file}" --spec=draft2020 --strict=false >/dev/null 2>&1; then
                echo "  [X] Fixture unexpectedly PASSED validation — the envelope schema no longer rejects this case"
                exit 1
            else
                VALIDATED=$((VALIDATED + 1))
                echo "  [OK] Correctly rejected"
            fi
            echo ""
        fi
    done
fi
# --- Invalid rule fixtures, one directory per mode (MUST all FAIL) ---
#
# Table-driven because each loop binds exactly ONE rule schema. A quorum fixture
# dropped into the decision directory would be "correctly rejected" by
# decision-rules.schema.json for entirely the wrong reason -- silently, forever.
# The directory IS the binding, so adding a mode means adding a row here.
#
# Every row keeps the missing-schema guard: ajv exits non-zero for a MISSING
# schema exactly as it does for a rejected instance, so without it a renamed or
# deleted rule schema reports a run of cheerful "Correctly rejected" lines and
# nothing else in the repository would notice.
INVALID_RULES_PAIRS=(
    "invalid-policy-rules:decision-rules.schema.json:Decision"
    "invalid-quorum-rules:quorum-rules.schema.json:Quorum"
    "invalid-proposal-rules:proposal-rules.schema.json:Proposal"
    "invalid-task-rules:task-rules.schema.json:Task"
    "invalid-handoff-rules:handoff-rules.schema.json:Handoff"
)

for pair in "${INVALID_RULES_PAIRS[@]}"; do
    ir_dir="${PROJECT_ROOT}/schemas/json/tests/${pair%%:*}"
    ir_rest="${pair#*:}"
    ir_schema="${POLICY_RULES_SCHEMA_DIR}/${ir_rest%%:*}"
    ir_label="${ir_rest#*:}"

    echo "-- Negative ${ir_label}-rules tests (${ir_dir}/*.json) --"
    echo "Schema: ${ir_schema}"
    echo "Each fixture MUST FAIL validation."
    echo ""

    if [ ! -f "${ir_schema}" ]; then
        echo "[X] ${ir_label} rule schema not found: ${ir_schema}"
        exit 1
    fi
    # A deleted directory would otherwise drop a mode's entire coverage silently.
    if [ ! -d "${ir_dir}" ]; then
        echo "[X] ${ir_label} negative-fixture directory not found: ${ir_dir}"
        exit 1
    fi

    ir_count=0
    for f in "${ir_dir}"/*.json; do
        [ -f "$f" ] || continue
        ir_count=$((ir_count + 1))
        TOTAL=$((TOTAL + 1))
        echo "Checking (expect rejection): $(basename "$f")"
        if ajv validate -s "${ir_schema}" -d "${f}" --spec=draft2020 --strict=false >/dev/null 2>&1; then
            echo "  [X] Fixture unexpectedly PASSED -- ${ir_label} rule schema no longer rejects this case"
            exit 1
        fi
        VALIDATED=$((VALIDATED + 1))
        echo "  [OK] Correctly rejected"
        echo ""
    done

    if [ "${ir_count}" -eq 0 ]; then
        echo "[X] ${ir_dir} contains no fixtures -- an empty directory is not coverage."
        exit 1
    fi
done


# --- Negative policy-descriptor tests ---
#
# Sibling of the rule-schema loop above, kept as its OWN table because these
# schemas live in schemas/json/ rather than schemas/json/policy/ and bind a
# whole document rather than a `rules` object. A future descriptor-family
# schema is one row here.
#
# Until this loop existed, macp-policy-descriptor.schema.json had NO negative
# coverage of any kind: every descriptor on disk is a positive example, so
# neither its `required` list nor policy_id's `minLength` had ever been proved
# to fire. Deleting either keyword left the whole repository green.
#
# The two guards below are NOT symmetric with the rules loop's, and the
# difference is worth stating so nobody reads more into them than holds:
#
#   - The empty/missing-directory guard is first-consumer here exactly as it is
#     there. A deleted directory drops the coverage silently otherwise.
#   - The missing-schema guard is SHADOWED. Unlike the rule schemas -- whose
#     positive consumer, the rules-instance loop, runs AFTER their negative
#     loop -- this schema is already validated positively against
#     examples/discovery/policy_descriptor*.json earlier in this script, so a
#     deleted or corrupt schema fails there first and never reaches this loop.
#     It is kept as defense in depth for the checkout that lacks those
#     examples, where that positive block silently no-ops on its -f test and
#     this guard becomes the only thing standing between a missing schema and
#     a run of cheerful "Correctly rejected" lines.
INVALID_DESCRIPTOR_PAIRS=(
    "invalid-policy-descriptors:macp-policy-descriptor.schema.json:policy-descriptor"
)

for pair in "${INVALID_DESCRIPTOR_PAIRS[@]}"; do
    id_dir="${PROJECT_ROOT}/schemas/json/tests/${pair%%:*}"
    id_rest="${pair#*:}"
    id_schema="${PROJECT_ROOT}/schemas/json/${id_rest%%:*}"
    id_label="${id_rest#*:}"

    echo "-- Negative ${id_label} tests (${id_dir}/*.json) --"
    echo "Schema: ${id_schema}"
    echo "Each fixture MUST FAIL validation."
    echo ""

    if [ ! -f "${id_schema}" ]; then
        echo "[X] ${id_label} schema not found: ${id_schema}"
        exit 1
    fi
    # A deleted directory would otherwise drop this schema's entire coverage.
    if [ ! -d "${id_dir}" ]; then
        echo "[X] ${id_label} negative-fixture directory not found: ${id_dir}"
        exit 1
    fi

    id_count=0
    for f in "${id_dir}"/*.json; do
        [ -f "$f" ] || continue
        id_count=$((id_count + 1))
        TOTAL=$((TOTAL + 1))
        echo "Checking (expect rejection): $(basename "$f")"
        if ajv validate -s "${id_schema}" -d "${f}" --spec=draft2020 --strict=false >/dev/null 2>&1; then
            echo "  [X] Fixture unexpectedly PASSED -- ${id_label} schema no longer rejects this case"
            exit 1
        fi
        VALIDATED=$((VALIDATED + 1))
        echo "  [OK] Correctly rejected"
        echo ""
    done

    if [ "${id_count}" -eq 0 ]; then
        echo "[X] ${id_dir} contains no fixtures -- an empty directory is not coverage."
        exit 1
    fi
done


# --- Policy rules objects vs their mode's rule schema (issue #100) ---
#
# Until this loop existed, NOTHING validated a `rules` object against the schema
# that defines it. Both containers treat `rules` as opaque -- macp-policy-descriptor
# .schema.json and schemas/conformance/schema.json each declare it as a bare
# {"type": "object"} with no $ref -- so every constraint in every
# schemas/json/policy/*-rules.schema.json was decorative: a malformed allOf arm
# that silently never matches would compile clean and pass CI.
#
# The extractor also reaches fenced ```json blocks in rfcs/ and docs/, which no
# other check in this repository reads at all.
echo "-- Policy rules objects vs mode rule schemas (${POLICY_RULES_SCHEMA_DIR}) --"
echo ""

if [ ! -f "${RULES_EXTRACTOR}" ]; then
    echo "[X] Rules extractor not found: ${RULES_EXTRACTOR}"
    exit 1
fi

RULES_TMP="$(mktemp -d)"
# Bash keeps ONE EXIT trap: re-arming it here would silently disarm the transcript
# loop's cleanup above and leak its directory on every run. Cover both.
trap 'rm -rf "${TMP_ENV_DIR:-/nonexistent}" "${RULES_TMP:?}"' EXIT

# A failure here is fatal, not skippable: an extractor that silently emitted
# nothing would leave this whole section vacuously green.
if ! python3 "${RULES_EXTRACTOR}" "${RULES_TMP}" > "${RULES_TMP}/index.tsv"; then
    echo "[X] Rules extraction failed"
    exit 1
fi

if [ ! -s "${RULES_TMP}/index.tsv" ]; then
    echo "[X] No policy rules objects found -- the extractor matched nothing."
    echo "    There are known instances on disk, so this means extraction broke."
    exit 1
fi

RULES_FOUND="$(wc -l < "${RULES_TMP}/index.tsv" | tr -d ' ')"
if [ "${RULES_FOUND}" -ne "${EXPECTED_RULES_INSTANCES}" ]; then
    echo "[X] Expected ${EXPECTED_RULES_INSTANCES} policy rules objects, found ${RULES_FOUND}."
    echo "    Fewer means coverage was lost silently -- a renamed 'mode' key, a fence whose"
    echo "    info string no longer matches, or a deleted file. More means a new rules object"
    echo "    was added. Either way, confirm the change is intended and update"
    echo "    EXPECTED_RULES_INSTANCES in $0."
    exit 1
fi

while IFS=$'\t' read -r rule_mode rule_file rule_label; do
    [ -n "${rule_mode}" ] || continue

    # mode "*" is mode-agnostic (the default policy): no rule schema applies.
    # Logged rather than skipped silently, so the count always reconciles.
    if [ "${rule_mode}" = "*" ]; then
        echo "Skipping: ${rule_label}"
        echo "  [--] mode \"*\" is mode-agnostic; no rule schema applies"
        echo ""
        continue
    fi

    # macp.mode.<name>.v<N> -> <name>-rules.schema.json
    # Extension modes (ext.*, reverse-domain) are outside the standards-track rule
    # schemas by design -- CLAUDE.md encourages them and the repo ships
    # ext.multi_round.v1. Skip them like "*", logged; do NOT fail the build. Only an
    # unrecognized macp.mode.* identifier is an error.
    case "${rule_mode}" in
        macp.mode.*) ;;
        *)
            echo "Skipping: ${rule_label}"
            echo "  [--] extension mode \"${rule_mode}\" has no standards-track rule schema"
            echo ""
            continue
            ;;
    esac

    rule_short="$(echo "${rule_mode}" | sed -n 's/^macp\.mode\.\([a-z_]*\)\.v[0-9]*$/\1/p')"
    if [ -z "${rule_short}" ]; then
        echo "[X] ${rule_label}: malformed mode identifier \"${rule_mode}\""
        echo "    Expected macp.mode.<name>.v<N>"
        exit 1
    fi

    rule_schema="${POLICY_RULES_SCHEMA_DIR}/${rule_short}-rules.schema.json"
    # Hard-fail rather than skip: a typo'd mode that silently skipped validation
    # is precisely the failure class this loop exists to close.
    if [ ! -f "${rule_schema}" ]; then
        echo "[X] ${rule_label}: no rule schema for mode \"${rule_mode}\""
        echo "    Expected: ${rule_schema}"
        exit 1
    fi

    TOTAL=$((TOTAL + 1))
    echo "Validating: ${rule_label}  ->  $(basename "${rule_schema}")"
    if ajv validate -s "${rule_schema}" -d "${rule_file}" --spec=draft2020 --strict=false; then
        VALIDATED=$((VALIDATED + 1))
        echo "  [OK] Valid"
    else
        echo "  [X] Invalid"
        exit 1
    fi
    echo ""
done < "${RULES_TMP}/index.tsv"

if [ $TOTAL -eq 0 ]; then
    echo "Warning: No JSON example files found"
    exit 1
fi

echo "-------------------------------------"
echo "[OK] All ${VALIDATED}/${TOTAL} JSON files validated"
