#!/usr/bin/env bash

# Check that the committed Python _pb2_grpc.py stubs in packages/proto-python/
# match what grpc_tools.protoc produces from the canonical schemas/proto tree.
#
# The matching is content-based: the auto-generated GRPC_GENERATED_VERSION line
# is normalized away before comparison so that differences in the local
# grpcio-tools version don't trigger spurious failures.
#
# Exits 0 on match, 1 on drift (prints unified diffs for each offender).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_DIR="${PROJECT_ROOT}/schemas/proto"
PY_DIR="${PROJECT_ROOT}/packages/proto-python/src"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Skipping: python3 not available."
    exit 0
fi

if ! python3 -c "import grpc_tools" >/dev/null 2>&1; then
    echo "Skipping: grpcio-tools not installed. Install with:"
    echo "  pip install grpcio-tools"
    exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "Generating Python protobuf stubs into ${TMP_DIR} ..."
python3 -m grpc_tools.protoc \
    -I"${PROTO_DIR}" \
    --python_out="${TMP_DIR}" \
    --grpc_python_out="${TMP_DIR}" \
    macp/v1/envelope.proto \
    macp/v1/core.proto \
    macp/v1/policy.proto \
    macp/modes/decision/v1/decision.proto \
    macp/modes/proposal/v1/proposal.proto \
    macp/modes/task/v1/task.proto \
    macp/modes/handoff/v1/handoff.proto \
    macp/modes/quorum/v1/quorum.proto

ERRORS=0

# List of committed _pb2_grpc.py files (relative to packages/proto-python/src).
STUBS=(
    "macp/v1/envelope_pb2_grpc.py"
    "macp/v1/core_pb2_grpc.py"
    "macp/v1/policy_pb2_grpc.py"
    "macp/modes/decision/v1/decision_pb2_grpc.py"
    "macp/modes/proposal/v1/proposal_pb2_grpc.py"
    "macp/modes/task/v1/task_pb2_grpc.py"
    "macp/modes/handoff/v1/handoff_pb2_grpc.py"
    "macp/modes/quorum/v1/quorum_pb2_grpc.py"
)

# Normalize away the auto-tool version string so differences in the local
# grpcio-tools version don't trigger spurious drift.
normalize() {
    sed -E "s/^GRPC_GENERATED_VERSION = '[^']*'/GRPC_GENERATED_VERSION = 'NORMALIZED'/"
}

echo ""
echo "Comparing committed stubs against freshly-generated output ..."
for rel in "${STUBS[@]}"; do
    committed="${PY_DIR}/${rel}"
    generated="${TMP_DIR}/${rel}"

    if [[ ! -f "${committed}" ]]; then
        echo "MISSING (committed): ${rel}"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    if [[ ! -f "${generated}" ]]; then
        echo "MISSING (generated): ${rel}"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    if ! diff -q \
        <(normalize < "${committed}") \
        <(normalize < "${generated}") >/dev/null 2>&1; then
        echo ""
        echo "DRIFT: ${rel}"
        diff --unified=3 \
            <(normalize < "${committed}") \
            <(normalize < "${generated}") | head -60 || true
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [[ ${ERRORS} -gt 0 ]]; then
    echo "✗ ${ERRORS} Python stub(s) are out of sync with canonical protos."
    echo "  Regenerate with:"
    echo "    python -m grpc_tools.protoc \\"
    echo "      -Ischemas/proto \\"
    echo "      --python_out=packages/proto-python/src \\"
    echo "      --grpc_python_out=packages/proto-python/src \\"
    echo "      macp/v1/*.proto macp/modes/*/v1/*.proto"
    exit 1
fi

echo "✓ All committed Python _pb2_grpc.py stubs are in sync with canonical protos."
