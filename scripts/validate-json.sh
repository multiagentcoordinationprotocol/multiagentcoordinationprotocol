#!/usr/bin/env bash

# Validate JSON examples against the MACP JSON Schemas

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

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

if [ $TOTAL -eq 0 ]; then
    echo "Warning: No JSON example files found"
    exit 1
fi

echo "-------------------------------------"
echo "[OK] All ${VALIDATED}/${TOTAL} JSON files validated"
