.PHONY: help validate validate-all proto-lint proto-compile proto-gen json-validate json-schema-validate clean install-tools

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
	@echo "Code Generation:"
	@echo "  make proto-gen             Generate code from protobuf (Go, Python, TypeScript)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                 Remove generated files"
	@echo "  make install-tools         Install required development tools"
	@echo ""

# Validate everything
validate: json-schema-validate json-validate proto-lint proto-compile
	@echo "✓ All validations passed"

validate-all: validate proto-gen
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

# Compile protobuf to validate syntax
proto-compile:
	@echo "Compiling Protocol Buffers..."
	@./scripts/validate-proto.sh

# Generate code from protobuf
proto-gen:
	@echo "Generating code from Protocol Buffers..."
	@if command -v buf >/dev/null 2>&1; then \
		buf generate; \
		echo "✓ Code generated in generated/ directory"; \
	else \
		echo "⚠️  buf not installed. Run 'make install-tools' or see https://buf.build/docs/installation"; \
		exit 1; \
	fi

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/
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
