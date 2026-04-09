#!/usr/bin/env bash
# Generate Swift protobuf files from .proto sources.
# Requires: protoc-gen-swift, protoc-gen-grpc-swift
#   brew install swift-protobuf protoc-gen-grpc-swift
set -euo pipefail
cd "$(dirname "$0")"

PROTO_DIR="proto"
OUT_DIR="Sources/MACPProto"

PROTOS=(
  macp/v1/envelope.proto
  macp/v1/core.proto
  macp/v1/policy.proto
  macp/modes/decision/v1/decision.proto
  macp/modes/proposal/v1/proposal.proto
  macp/modes/task/v1/task.proto
  macp/modes/handoff/v1/handoff.proto
  macp/modes/quorum/v1/quorum.proto
)

echo "Generating Swift protobuf code..."

# grpc-swift v2.x installs the plugin as protoc-gen-grpc-swift-2
GRPC_PLUGIN="$(command -v protoc-gen-grpc-swift-2 || command -v protoc-gen-grpc-swift)"
protoc \
  --plugin=protoc-gen-grpc-swift="$GRPC_PLUGIN" \
  --proto_path="$PROTO_DIR" \
  --swift_out="$OUT_DIR" \
  --swift_opt=Visibility=Public \
  --grpc-swift_out="$OUT_DIR" \
  --grpc-swift_opt=Visibility=Public \
  "${PROTOS[@]}"

# Remove the placeholder if generated files exist
rm -f "$OUT_DIR/placeholder.swift"
echo "Done. Generated files in $OUT_DIR/"
