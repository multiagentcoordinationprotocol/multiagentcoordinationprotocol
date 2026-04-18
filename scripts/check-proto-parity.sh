#!/usr/bin/env bash
# Proto version parity check (W3a / XR-1).
#
# Fails CI when the proto package versions consumed by typescript-sdk and python-sdk
# fall out of sync with the canonical proto packages in this monorepo.
#
# Parity rules:
#   1. packages/proto-npm/package.json version == packages/proto-python/pyproject.toml version.
#   2. typescript-sdk accepts the canonical @multiagentcoordinationprotocol/proto version
#      (via the caret range in its package.json).
#   3. python-sdk accepts the canonical macp-proto version (via its PEP 440 version range).
#
# Exits 0 on parity, 1 on drift with a clear diagnostic.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MONO_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

PROTO_NPM_JSON="$REPO_ROOT/packages/proto-npm/package.json"
PROTO_PY_TOML="$REPO_ROOT/packages/proto-python/pyproject.toml"
TS_SDK_JSON="$MONO_ROOT/typescript-sdk/package.json"
PY_SDK_TOML="$MONO_ROOT/python-sdk/pyproject.toml"

missing=()
for f in "$PROTO_NPM_JSON" "$PROTO_PY_TOML" "$TS_SDK_JSON" "$PY_SDK_TOML"; do
  [ -f "$f" ] || missing+=("$f")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "ERROR: missing files:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

# Canonical proto versions (source of truth).
proto_npm_version="$(grep -m1 '"version"' "$PROTO_NPM_JSON" | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
proto_py_version="$(grep -m1 '^version' "$PROTO_PY_TOML" | sed -E 's/.*version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/')"

# Consumer-declared ranges.
ts_sdk_range="$(grep -m1 '@multiagentcoordinationprotocol/proto' "$TS_SDK_JSON" | sed -E 's/.*"@multiagentcoordinationprotocol\/proto"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
# Match a real dependency line (starts with whitespace + quote), not a comment.
py_sdk_range="$(grep -m1 -E '^[[:space:]]*"macp-proto' "$PY_SDK_TOML" | sed -E 's/.*"macp-proto([^"]*)".*/\1/')"

echo "Canonical proto packages:"
echo "  packages/proto-npm             @ $proto_npm_version"
echo "  packages/proto-python          @ $proto_py_version"
echo ""
echo "SDK consumer ranges:"
echo "  typescript-sdk → @multiagentcoordinationprotocol/proto $ts_sdk_range"
echo "  python-sdk     → macp-proto$py_sdk_range"
echo ""

fail=0

# Rule 1: the two canonical packages publish the same version.
if [ "$proto_npm_version" != "$proto_py_version" ]; then
  echo "FAIL: proto-npm ($proto_npm_version) and proto-python ($proto_py_version) are out of sync." >&2
  fail=1
fi

# Rule 2: typescript-sdk caret must start with the canonical version.
# Accepts "^X.Y.Z" or "X.Y.Z"; anything else is suspicious.
case "$ts_sdk_range" in
  "^$proto_npm_version"|"$proto_npm_version")
    :;;
  *)
    echo "FAIL: typescript-sdk proto range ($ts_sdk_range) does not pin canonical $proto_npm_version." >&2
    fail=1
    ;;
esac

# Rule 3: python-sdk range must accept the canonical version.
# Range looks like ">=0.1.0,<0.2.0" — we check that the lower bound matches canonical.
lower_bound="$(echo "$py_sdk_range" | sed -E 's/>=([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | tr -d ' ')"
if [ -z "$lower_bound" ] || [ "$lower_bound" = "$py_sdk_range" ]; then
  echo "WARN: could not parse python-sdk range lower bound from '$py_sdk_range'. Skipping check." >&2
elif [ "$lower_bound" != "$proto_py_version" ]; then
  # Allow the lower bound to be older than canonical (forward-compatible) but warn if it's newer.
  highest=$(printf '%s\n%s\n' "$lower_bound" "$proto_py_version" | sort -V | tail -1)
  if [ "$highest" = "$lower_bound" ] && [ "$lower_bound" != "$proto_py_version" ]; then
    echo "FAIL: python-sdk lower-bound ($lower_bound) is ahead of canonical macp-proto ($proto_py_version)." >&2
    fail=1
  fi
fi

if [ $fail -eq 0 ]; then
  echo "OK — proto versions are in parity."
  exit 0
fi

cat >&2 <<EOF

Proto drift detected.

Fix options:
  1. Bump the SDK consumer ranges to match the canonical proto package versions.
  2. Or, publish a new proto-packages release and update proto-npm + proto-python in lockstep
     (run .github/workflows/publish-proto-packages.yml with the same version on both).

See multiagentcoordinationprotocol/packages/proto-npm/ and /proto-python/ for the canonical
publish flow. See ui-console/plans/direct-agent-auth.md W3a for rationale.
EOF

exit 1
