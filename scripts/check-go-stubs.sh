#!/usr/bin/env bash

# Check that the committed Go protobuf stubs in packages/proto-go/ match
# what buf generate produces from the canonical schemas/proto tree.
#
# The matching is content-based: the protoc-gen-go tool version line is
# normalized away before comparison so that differences in the local
# generator version don't trigger spurious failures.
#
# Exits 0 on match, 1 on drift (prints unified diffs for each offender).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
GO_PKG_DIR="${PROJECT_ROOT}/packages/proto-go/macp"

if ! command -v buf >/dev/null 2>&1; then
    echo "Skipping: buf not installed."
    exit 0
fi

if ! command -v go >/dev/null 2>&1; then
    echo "Skipping: go not installed."
    exit 0
fi

PLUGIN_BIN="$(mktemp -d)"
TMP_OUT="$(mktemp -d)"
trap 'rm -rf "${PLUGIN_BIN}" "${TMP_OUT}"' EXIT

echo "Installing Go protoc plugins into ${PLUGIN_BIN} ..."
GOBIN="${PLUGIN_BIN}" go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
GOBIN="${PLUGIN_BIN}" go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Use a template that points to the locally-installed plugins (no BSR auth
# required) but replicates the same managed-mode settings as the canonical
# buf/buf.gen.go.yaml. The template must live inside a stable directory so
# that buf's relative-path resolution is predictable.
TEMPLATE_FILE="${PROJECT_ROOT}/buf/buf.gen.go.local.generated.yaml"
cat > "${TEMPLATE_FILE}" <<EOF
version: v2
managed:
  enabled: true
  override:
    - file_option: go_package_prefix
      value: github.com/multiagentcoordinationprotocol/macp-proto-go
plugins:
  - local: protoc-gen-go
    out: ${TMP_OUT}
    opt:
      - paths=source_relative
  - local: protoc-gen-go-grpc
    out: ${TMP_OUT}
    opt:
      - paths=source_relative
EOF
trap 'rm -rf "${PLUGIN_BIN}" "${TMP_OUT}"; rm -f "${TEMPLATE_FILE}"' EXIT

echo "Regenerating Go stubs into ${TMP_OUT} ..."
(
    cd "${PROJECT_ROOT}"
    PATH="${PLUGIN_BIN}:${PATH}" buf generate \
        --template "${TEMPLATE_FILE}"
)

ERRORS=0

# Normalize tool version strings so differences in the local plugin
# version don't trigger spurious drift.
normalize() {
    sed -E \
        -e 's|^// - protoc-gen-go[^ ]*[[:space:]]+v[0-9.]+.*$|// - protoc-gen-go NORMALIZED|' \
        -e 's|^// - protoc-gen-go-grpc[^ ]*[[:space:]]+v[0-9.]+.*$|// - protoc-gen-go-grpc NORMALIZED|' \
        -e 's|^// - protoc[[:space:]]+.*$|// - protoc NORMALIZED|' \
        -e 's|^//[[:space:]]+protoc-gen-go[[:space:]]+v[0-9.]+.*$|// protoc-gen-go NORMALIZED|'
}

echo ""
echo "Comparing committed stubs against freshly-generated output ..."
while IFS= read -r -d '' committed; do
    rel="${committed#${GO_PKG_DIR}/}"
    generated="${TMP_OUT}/macp/${rel}"

    if [[ ! -f "${generated}" ]]; then
        echo "MISSING (generated): macp/${rel}"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    if ! diff -q \
        <(normalize < "${committed}") \
        <(normalize < "${generated}") >/dev/null 2>&1; then
        echo ""
        echo "DRIFT: packages/proto-go/macp/${rel}"
        diff --unified=3 \
            <(normalize < "${committed}") \
            <(normalize < "${generated}") | head -60 || true
        ERRORS=$((ERRORS + 1))
    fi
done < <(find "${GO_PKG_DIR}" -type f -name '*.go' -print0)

echo ""
if [[ ${ERRORS} -gt 0 ]]; then
    echo "✗ ${ERRORS} Go stub(s) are out of sync with canonical protos."
    echo "  Regenerate with:"
    echo "    buf generate --template buf/buf.gen.go.yaml"
    exit 1
fi

echo "✓ All committed Go protobuf stubs are in sync with canonical protos."
