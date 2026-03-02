#!/usr/bin/env bash

# Validate JSON examples against the MACP JSON Schema

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SCHEMA_FILE="${PROJECT_ROOT}/schemas/json/macp-envelope.schema.json"
EXAMPLES_DIR="${PROJECT_ROOT}/examples/json"

echo "Validating JSON examples against schema..."
echo "Schema: ${SCHEMA_FILE}"
echo "Examples: ${EXAMPLES_DIR}/*.json"
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

# Validate each JSON example file
for example_file in "${EXAMPLES_DIR}"/*.json; do
    if [ -f "$example_file" ]; then
        TOTAL=$((TOTAL + 1))
        echo "Validating: $(basename "$example_file")"

        if ajv validate -s "${SCHEMA_FILE}" -d "${example_file}" --spec=draft2020 --strict=false; then
            VALIDATED=$((VALIDATED + 1))
            echo "  ✓ Valid"
        else
            echo "  ✗ Invalid"
            exit 1
        fi
        echo ""
    fi
done

if [ $TOTAL -eq 0 ]; then
    echo "Warning: No JSON example files found in ${EXAMPLES_DIR}"
    exit 1
fi

echo "─────────────────────────────────────"
echo "✓ All ${VALIDATED}/${TOTAL} JSON examples are valid"
