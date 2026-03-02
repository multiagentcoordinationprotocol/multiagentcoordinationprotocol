#!/usr/bin/env bash

# Validate that the JSON Schema itself is valid (meta-validation)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SCHEMA_FILE="${PROJECT_ROOT}/schemas/json/macp-envelope.schema.json"

echo "Validating JSON Schema: ${SCHEMA_FILE}"

# Check if ajv-cli is installed
if ! command -v ajv >/dev/null 2>&1; then
    echo "Error: ajv-cli is not installed"
    echo "Install with: npm install -g ajv-cli"
    echo "Or run: make install-tools"
    exit 1
fi

# Validate the schema itself using JSON Schema Draft 2020-12 meta-schema
# The schema should be valid according to the JSON Schema specification
# Note: Strict mode is disabled because the oneOf mutual exclusivity pattern
# uses 'not: { required: [...] }' which triggers strictRequired warnings
# The schema is still validated against the JSON Schema spec, just without extra strict mode checks
ajv compile -s "${SCHEMA_FILE}" --spec=draft2020 --strict=false

echo "✓ JSON Schema is valid"
