# Versioning and Compatibility Policy

MACP uses a layered versioning model because the protocol is not a single thing. It is a kernel, a wire format, a family of semantic Modes, and a set of registries that must evolve without destroying replay integrity.

## 1. Protocol Version

The base protocol version is negotiated during initialization.

- **MAJOR** increments signal breaking protocol changes.
- **MINOR** increments add backward-compatible protocol features or fields.
- **PATCH** increments clarify the standard, fix examples, or tighten wording without changing behavior.

Runtimes MUST reject initialization if no mutually supported protocol version exists.

## 2. Schema Namespace Version

Canonical Protobuf schemas use package namespaces such as `macp.v1`.

- Breaking wire changes require a new namespace.
- Backward-compatible additions SHOULD remain in the current major namespace.
- Unknown fields MUST be ignored for forward compatibility.

## 3. Mode Version

Modes define semantic behavior and therefore version independently of Core.

- Breaking semantic changes require a new Mode version.
- Modes MUST declare a stable identifier and version.
- Sessions MUST bind the exact Mode version used for replay.

## 4. Configuration and Policy Version

MACP Core does not standardize policy languages, but runtimes often bind session behavior to a configuration or policy profile.

Any configuration value that can change resolution behavior SHOULD be versioned and recorded with the session. Replay MUST use the same bound versions.

## 5. Compatibility Rules

A session is replay-compatible only when these values match the original execution context:

- negotiated protocol version,
- schema namespace major version,
- Mode identifier and Mode version,
- configuration and policy version(s) that influence semantics.

## 6. Deprecation

Deprecations SHOULD be announced in two phases:

1. **Deprecated** — new use is discouraged, existing use continues.
2. **Removed** — new sessions or initialization attempts using the deprecated element are rejected.

## 7. Registry Stability

Registry entries are not all equal. Each registry entry has one of these statuses:

- **permanent** — stable and broadly interoperable
- **provisional** — usable but subject to change
- **experimental** — explicitly non-standard
- **deprecated** — retained for historical compatibility
