#!/usr/bin/env bash

# Validate all Protocol Buffer schemas compile correctly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_DIR="${PROJECT_ROOT}/schemas/proto"
ENTRYPOINT_DIR="${PROJECT_ROOT}/schemas"

echo "Validating Protocol Buffer schemas ..."
echo

if ! command -v protoc >/dev/null 2>&1; then
    echo "⚠️  protoc (Protocol Buffer compiler) is not installed. Skipping protobuf compilation."
    echo "Install with:"
    echo "  macOS: brew install protobuf"
    echo "  Ubuntu: sudo apt-get install -y protobuf-compiler"
    echo "Or run: make install-tools"
    exit 0
fi

# ── Canonical protos under schemas/proto/ ──
echo "── Canonical protos (${PROTO_DIR}) ──"

PROTO_FILES=()
while IFS= read -r -d '' f; do
    PROTO_FILES+=("$f")
done < <(find "${PROTO_DIR}" -type f -name '*.proto' -print0 | sort -z)

if [ ${#PROTO_FILES[@]} -eq 0 ]; then
    echo "No .proto files found under ${PROTO_DIR}"
    exit 1
fi

protoc --proto_path="${PROTO_DIR}" --descriptor_set_out=/dev/null "${PROTO_FILES[@]}"
echo "✓ All canonical protos compile successfully"
echo

# ── Entrypoint protos (schemas/*.proto, schemas/modes/*.proto) ──
# These are human-friendly aggregator files that import canonical protos.
# Unused-import warnings are expected for the aggregator pattern.
ENTRYPOINT_FILES=()
while IFS= read -r -d '' f; do
    ENTRYPOINT_FILES+=("$f")
done < <(find "${ENTRYPOINT_DIR}" -maxdepth 1 -name '*.proto' -print0 | sort -z)

while IFS= read -r -d '' f; do
    ENTRYPOINT_FILES+=("$f")
done < <(find "${ENTRYPOINT_DIR}/modes" -name '*.proto' -print0 2>/dev/null | sort -z)

if [ ${#ENTRYPOINT_FILES[@]} -gt 0 ]; then
    echo "── Entrypoint protos ──"
    echo "Note: Unused-import warnings are expected for aggregator/entrypoint files."
    echo

    protoc --proto_path="${PROTO_DIR}" --proto_path="${ENTRYPOINT_DIR}" \
        --descriptor_set_out=/dev/null "${ENTRYPOINT_FILES[@]}" 2>&1 | while IFS= read -r line; do
        echo "  [warning] ${line}"
    done
    echo "✓ All entrypoint protos compile successfully"
fi

echo
echo "─────────────────────────────────────"
echo "✓ All Protocol Buffer schemas are syntactically valid"
