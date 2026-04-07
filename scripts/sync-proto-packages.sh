#!/usr/bin/env bash

# Sync canonical proto files from schemas/proto/ to raw-proto packages.
#
# Packages that ship raw .proto files (proto-npm, proto-rust, proto-swift)
# must stay byte-for-byte identical to the canonical schemas.  This script
# copies the canonical protos into each package directory.
#
# Usage:
#   ./scripts/sync-proto-packages.sh          # copy canonical → packages
#   ./scripts/sync-proto-packages.sh --check  # exit non-zero if any differ

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CANONICAL="${PROJECT_ROOT}/schemas/proto"

# Packages that ship raw .proto files (not generated code).
RAW_PACKAGES=(
  "packages/proto-npm/proto"
  "packages/proto-rust/proto"
  "packages/proto-swift/proto"
)

CHECK_MODE=false
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=true
fi

ERRORS=0

for PKG in "${RAW_PACKAGES[@]}"; do
  PKG_DIR="${PROJECT_ROOT}/${PKG}"

  if [[ ! -d "${PKG_DIR}" ]]; then
    echo "⚠️  Package dir not found: ${PKG} (skipping)"
    continue
  fi

  # Find all .proto files in canonical and compare/copy
  while IFS= read -r -d '' REL_PATH; do
    SRC="${CANONICAL}/${REL_PATH}"
    DST="${PKG_DIR}/${REL_PATH}"

    if $CHECK_MODE; then
      if [[ ! -f "${DST}" ]]; then
        echo "MISSING: ${PKG}/${REL_PATH}"
        ERRORS=$((ERRORS + 1))
      elif ! diff -q "${SRC}" "${DST}" >/dev/null 2>&1; then
        echo "DRIFT:   ${PKG}/${REL_PATH}"
        diff --unified=3 "${SRC}" "${DST}" | head -30
        echo ""
        ERRORS=$((ERRORS + 1))
      fi
    else
      mkdir -p "$(dirname "${DST}")"
      cp "${SRC}" "${DST}"
    fi
  done < <(cd "${CANONICAL}" && find . -type f -name '*.proto' | sed 's|^\./||' | sort | tr '\n' '\0')
done

if $CHECK_MODE; then
  if [[ ${ERRORS} -gt 0 ]]; then
    echo ""
    echo "✗ ${ERRORS} proto file(s) out of sync with canonical schemas."
    echo "  Run: ./scripts/sync-proto-packages.sh"
    exit 1
  else
    echo "✓ All raw-proto packages are in sync with canonical schemas."
  fi
else
  echo "✓ Synced canonical protos → ${#RAW_PACKAGES[@]} packages."
fi
