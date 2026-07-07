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

## 8. Published Proto Packages

The canonical protos under `schemas/proto/` are published as packages in
every supported language (crates.io `macp-proto`, PyPI `macp-proto`, npm
`@multiagentcoordinationprotocol/proto`, Go module, Maven, NuGet). Rules:

- **One shared version across all languages per release**, cut by tagging
  `proto-vX.Y.Z` (or `workflow_dispatch` with an explicit version). Do NOT
  use bare `vX.Y.Z` tags for proto releases — the tag trigger matches
  `proto-v*` only, and bare `v*` tags are reserved for spec-level releases.
- Field additions are proto3-backward-compatible and bump the PATCH/MINOR
  version; anything wire-breaking is not permitted post-freeze without a
  new package major.
- **Generated-code dependency floors are part of the release contract.**
  For languages where the package ships *generated code* (Python), the
  code-generator version pinned in `publish-proto-packages.yml`
  (`grpcio-tools`) determines the real runtime floors of the generated
  code. The floors declared in `packages/proto-python/pyproject.toml`
  MUST equal what the pinned generator's output actually requires, and
  the generator pin and the declared floors MUST be bumped together in
  the same change. (Issue #53 is the cautionary tale: an unpinned
  generator silently raised the real floor above the declared one, and
  wheels 0.1.4–0.1.7 could not be imported at their declared minimums.)
- Raw-proto packages (`proto-rust`, `proto-npm`) carry no generated code
  and are exempt from the floor rule; they must stay byte-identical to
  `schemas/proto/` (`make check-proto-sync`).
