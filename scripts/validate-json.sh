#!/usr/bin/env bash

# Validate JSON examples against the MACP JSON Schemas

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENVELOPE_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-envelope.schema.json"
MANIFEST_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-agent-manifest.schema.json"
DESCRIPTOR_SCHEMA="${PROJECT_ROOT}/schemas/json/macp-mode-descriptor.schema.json"
EXAMPLES_DIR="${PROJECT_ROOT}/examples/json"
DISCOVERY_DIR="${PROJECT_ROOT}/examples/discovery"
TRANSCRIPT_GLOB="${PROJECT_ROOT}/examples/*-mode-session.json"

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
fi

echo "-- Composite transcripts (syntax check only) --"
echo ""

for transcript in ${TRANSCRIPT_GLOB}; do
    if [ -f "$transcript" ]; then
        TOTAL=$((TOTAL + 1))
        echo "Validating JSON syntax: $(basename "$transcript")"

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
        echo ""
    fi
done

if [ $TOTAL -eq 0 ]; then
    echo "Warning: No JSON example files found"
    exit 1
fi

echo "-------------------------------------"
echo "[OK] All ${VALIDATED}/${TOTAL} JSON files validated"
