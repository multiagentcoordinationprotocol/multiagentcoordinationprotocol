#!/usr/bin/env bash

# Validate that all JSON Schemas are valid (meta-validation)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SCHEMA_DIR="${PROJECT_ROOT}/schemas/json"

echo "Meta-validating JSON Schemas under ${SCHEMA_DIR} ..."
echo ""

# Check if ajv-cli is installed
if ! command -v ajv >/dev/null 2>&1; then
    echo "Error: ajv-cli is not installed"
    echo "Install with: npm install -g ajv-cli"
    echo "Or run: make install-tools"
    exit 1
fi

TOTAL=0
VALIDATED=0

# Validate each JSON Schema file
# Note: Strict mode is disabled because the oneOf mutual exclusivity pattern
# uses 'not: { required: [...] }' which triggers strictRequired warnings.
# The schemas are still validated against the JSON Schema spec.
for schema_file in "${SCHEMA_DIR}"/*.schema.json; do
    if [ -f "$schema_file" ]; then
        TOTAL=$((TOTAL + 1))
        echo "Validating: $(basename "$schema_file")"

        if ajv compile -s "${schema_file}" --spec=draft2020 --strict=false; then
            VALIDATED=$((VALIDATED + 1))
            echo "  ✓ Valid"
        else
            echo "  ✗ Invalid"
            exit 1
        fi
        echo ""
    fi
done

# The A2A binding schema is a bag of $defs under an accept-anything root, and
# ajv compiles only what the root reaches, so the loop above checks its $defs
# against the meta-schema but never resolves their $refs. Compile one copy per
# $def, rooted at that $def, with the envelope schema its EnvelopePart references.
A2A_SCHEMA="${SCHEMA_DIR}/macp-a2a-binding.schema.json"
if [ -f "${A2A_SCHEMA}" ]; then
    echo "── A2A binding \$defs (macp-a2a-binding.schema.json) ──"
    echo ""
    A2A_WRAP_DIR="$(mktemp -d)"
    trap 'rm -rf "${A2A_WRAP_DIR}"' EXIT
    python3 "${PROJECT_ROOT}/scripts/extract-a2a-objects.py" wrap "${A2A_SCHEMA}" "${A2A_WRAP_DIR}" > "${A2A_WRAP_DIR}/defs.txt"
    while read -r def; do
        TOTAL=$((TOTAL + 1))
        echo "Compiling: macp-a2a-binding.schema.json#/\$defs/${def}"
        if ajv compile -s "${A2A_WRAP_DIR}/a2a-${def}.schema.json" -r "${SCHEMA_DIR}/macp-envelope.schema.json" \
            --spec=draft2020 --strict=false >/dev/null; then
            VALIDATED=$((VALIDATED + 1))
            echo "  ✓ Valid"
        else
            echo "  ✗ Invalid"
            exit 1
        fi
        echo ""
    done < "${A2A_WRAP_DIR}/defs.txt"
fi

# Validate policy rule schemas
echo "── Policy rule schemas ──"
echo ""
for schema_file in "${SCHEMA_DIR}"/policy/*.schema.json; do
    if [ -f "$schema_file" ]; then
        TOTAL=$((TOTAL + 1))
        echo "Validating: policy/$(basename "$schema_file")"

        if ajv compile -s "${schema_file}" --spec=draft2020 --strict=false; then
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
    echo "Warning: No JSON Schema files found in ${SCHEMA_DIR}"
    exit 1
fi

echo "─────────────────────────────────────"
echo "✓ All ${VALIDATED}/${TOTAL} JSON Schemas are valid"
