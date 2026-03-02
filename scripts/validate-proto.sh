#!/usr/bin/env bash

# Validate Protocol Buffer schemas compile correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROTO_DIR="${PROJECT_ROOT}/schemas/proto"
PROTO_FILE="${PROTO_DIR}/macp/v1/macp.proto"

echo "Validating Protocol Buffer schemas..."
echo "Proto file: ${PROTO_FILE}"
echo ""

# Check if protoc is installed
if ! command -v protoc >/dev/null 2>&1; then
    echo "⚠️  protoc (Protocol Buffer compiler) is not installed. Skipping protobuf compilation."
    echo "Install with:"
    echo "  macOS: brew install protobuf"
    echo "  Ubuntu: sudo apt-get install -y protobuf-compiler"
    echo "Or run: make install-tools"
    exit 0
fi

# Check protoc version
PROTOC_VERSION=$(protoc --version | awk '{print $2}')
echo "Using protoc version: ${PROTOC_VERSION}"
echo ""

# Compile the protobuf file to validate syntax
# --descriptor_set_out=/dev/null means we just validate, don't generate output
echo "Compiling protobuf schema..."
protoc \
    --proto_path="${PROTO_DIR}" \
    --descriptor_set_out=/dev/null \
    "${PROTO_FILE}"

echo "✓ Protocol Buffer schema is valid"
