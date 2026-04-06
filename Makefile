.PHONY: help validate validate-all proto-lint proto-compile proto-gen-all json-validate json-schema-validate clean install-tools \
	gen-go gen-python gen-java gen-kotlin gen-csharp gen-js sync-protos check-proto-sync

PROTO_SRC := schemas/proto
PROTO_FILES := macp/v1/envelope.proto macp/v1/core.proto macp/v1/policy.proto \
	macp/modes/decision/v1/decision.proto macp/modes/proposal/v1/proposal.proto \
	macp/modes/task/v1/task.proto macp/modes/handoff/v1/handoff.proto \
	macp/modes/quorum/v1/quorum.proto

# Default target
help:
	@echo "MACP Development Commands"
	@echo ""
	@echo "Validation:"
	@echo "  make validate              Run all validations"
	@echo "  make json-schema-validate  Validate JSON Schema itself"
	@echo "  make json-validate         Validate JSON examples against schema"
	@echo "  make proto-lint            Lint Protocol Buffer schemas"
	@echo "  make proto-compile         Compile Protocol Buffer schemas (validation)"
	@echo ""
	@echo "Code Generation (per-language into packages/):"
	@echo "  make gen-go                Generate Go into packages/proto-go/"
	@echo "  make gen-python            Generate Python into packages/proto-python/"
	@echo "  make gen-java              Generate Java into packages/proto-java/"
	@echo "  make gen-kotlin            Generate Kotlin into packages/proto-kotlin/"
	@echo "  make gen-csharp            Generate C# into packages/proto-csharp/"
	@echo "  make gen-js                Generate JavaScript into packages/proto-npm/"
	@echo "  make proto-gen-all         Generate all languages into their packages"
	@echo ""
	@echo "Proto Sync (raw-proto packages):"
	@echo "  make sync-protos           Copy canonical protos → proto-npm, proto-rust, proto-swift"
	@echo "  make check-proto-sync      Verify packages match canonical (CI guard)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                 Remove generated files"
	@echo "  make install-tools         Install required development tools"
	@echo ""

# Validate everything
validate: json-schema-validate json-validate proto-lint proto-compile check-proto-sync
	@echo "✓ All validations passed"

validate-all: validate proto-gen-all
	@echo "✓ All validations and code generation completed"

# Validate the JSON Schema itself (meta-validation)
json-schema-validate:
	@echo "Validating JSON Schema..."
	@./scripts/validate-json-schema.sh

# Validate JSON examples against the schema
json-validate:
	@echo "Validating JSON examples..."
	@./scripts/validate-json.sh

# Lint protobuf files with buf
proto-lint:
	@echo "Linting Protocol Buffers..."
	@if command -v buf >/dev/null 2>&1; then \
		buf lint; \
	else \
		echo "⚠️  buf not installed. Skipping protobuf linting."; \
		echo "   Install buf with 'make install-tools' or see https://buf.build/docs/installation"; \
	fi

# Sync canonical protos to raw-proto packages (proto-npm, proto-rust, proto-swift)
sync-protos:
	@echo "Syncing canonical protos to packages..."
	@./scripts/sync-proto-packages.sh

# Check that raw-proto packages are in sync (CI guard)
check-proto-sync:
	@echo "Checking proto package sync..."
	@./scripts/sync-proto-packages.sh --check

# Compile protobuf to validate syntax
proto-compile:
	@echo "Compiling Protocol Buffers..."
	@./scripts/validate-proto.sh

# Per-language generation (directly into packages/)
gen-go:
	@echo "Generating Go..."
	@buf generate --template buf/buf.gen.go.yaml
	@echo "✓ Go code in packages/proto-go/"

gen-python:
	@echo "Generating Python (via grpc_tools.protoc for version compatibility)..."
	@python -m grpc_tools.protoc \
		-I$(PROTO_SRC) \
		--python_out=packages/proto-python/src \
		--grpc_python_out=packages/proto-python/src \
		$(PROTO_FILES)
	@echo "✓ Python code in packages/proto-python/src/"

gen-java:
	@echo "Generating Java..."
	@buf generate --template buf/buf.gen.java.yaml
	@echo "✓ Java code in packages/proto-java/src/"

gen-kotlin:
	@echo "Generating Kotlin..."
	@buf generate --template buf/buf.gen.kotlin.yaml
	@echo "✓ Kotlin code in packages/proto-kotlin/src/"

gen-csharp:
	@echo "Generating C#..."
	@buf generate --template buf/buf.gen.csharp.yaml
	@echo "✓ C# code in packages/proto-csharp/"

gen-js:
	@echo "Generating JavaScript..."
	@buf generate --template buf/buf.gen.js.yaml
	@echo "✓ JS code in packages/proto-npm/generated/"

proto-gen-all: gen-go gen-python gen-java gen-kotlin gen-csharp gen-js
	@echo "✓ All languages generated into packages/"

# Clean generated files from packages
clean:
	@echo "Cleaning generated files..."
	@rm -rf packages/proto-go/macp/
	@rm -f packages/proto-csharp/*.cs
	@rm -rf packages/proto-java/src/main/java/io/
	@rm -rf packages/proto-kotlin/src/main/kotlin/io/
	@rm -rf packages/proto-npm/generated/
	@echo "✓ Cleaned"

# Install development tools
install-tools:
	@echo "Installing development tools..."
	@echo ""
	@echo "1. Installing buf (protobuf tooling)..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install bufbuild/buf/buf; \
	else \
		echo "Please install buf manually: https://buf.build/docs/installation"; \
	fi
	@echo ""
	@echo "2. Installing ajv-cli and ajv-formats (JSON Schema validator)..."
	@if command -v npm >/dev/null 2>&1; then \
		npm install -g ajv-cli ajv-formats; \
	else \
		echo "Please install Node.js and npm, then run: npm install -g ajv-cli ajv-formats"; \
	fi
	@echo ""
	@echo "3. Installing protoc (Protocol Buffer compiler)..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install protobuf; \
	elif command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y protobuf-compiler; \
	else \
		echo "Please install protoc manually: https://protobuf.dev/downloads/"; \
	fi
	@echo ""
	@echo "✓ Tool installation complete"
