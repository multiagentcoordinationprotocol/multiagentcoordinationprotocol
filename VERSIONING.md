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
every supported language: crates.io `macp-proto`, PyPI `macp-proto`, npm
`@multiagentcoordinationprotocol/proto`, the `macp-proto-go` Go module,
Maven `io.macp:macp-proto` and `io.macp:macp-proto-kotlin`, and NuGet
`Macp.Proto`. Rules:

- **One shared version across all languages per release**, cut by tagging
  `proto-vX.Y.Z` (or `workflow_dispatch` with an explicit version). Do NOT
  use bare `vX.Y.Z` tags for proto releases — the tag trigger matches
  `proto-v*` only, and bare `v*` tags are reserved for spec-level releases.
  (The stray `v0.1.4` tag is the mistake this rule exists to prevent.)
- Field additions are proto3-backward-compatible and bump the PATCH/MINOR
  version; anything wire-breaking is not permitted post-freeze without a
  new package major.
- **Generator versions MUST be pinned.** Every remote plugin in
  `buf/buf.gen.*.yaml` carries an explicit revision, and the Python generator
  (`grpcio-tools`) is pinned in both `publish-proto-packages.yml` and `ci.yml`.
  An unpinned generator floats to whatever is latest at release time, which
  silently changes the emitted code's runtime requirements between two
  releases of identical `.proto` files.
- **Generated-code dependency floors are part of the release contract.**
  Five packages ship *generated* code, and for each of them the pinned
  generator determines the real runtime requirements of the emitted code. The
  declared floors MUST equal what that generator's output actually requires,
  and the pin and the floors MUST be bumped **in the same change**:

  | Package | Floors declared in | Pinned generator |
  | --- | --- | --- |
  | `proto-python` | `packages/proto-python/pyproject.toml` | `grpcio-tools` (`publish-proto-packages.yml`, `ci.yml`) |
  | `proto-java` | `packages/proto-java/build.gradle.kts` | `protocolbuffers/java`, `grpc/java` |
  | `proto-kotlin` | `packages/proto-kotlin/build.gradle.kts` | `protocolbuffers/kotlin` |
  | `proto-csharp` | `packages/proto-csharp/Macp.Proto.csproj` | `protocolbuffers/csharp` |
  | `proto-go` | `packages/proto-go/go.mod` | `protocolbuffers/go`, `grpc/go` |

  **A build that compiles is not evidence that the floors are right.** Some
  gencode asserts its required runtime version at *class load* rather than at
  compile time — `protobuf-java` does, via
  `RuntimeVersion.validateProtobufGencodeVersion` in a static initializer. A
  package whose declared floor is below its gencode version therefore compiles
  clean, publishes, and fails for the first consumer who loads it. That is what
  issue #53 was: wheels 0.1.4–0.1.7 built and published green and could not be
  imported at their declared minimums. CI load-tests the Java artifact against
  its declared floors for this reason (`scripts/java-loadtest/LoadTest.java`);
  a compile-only check cannot detect this class of error.

  `proto-go` needs one qualification. `google.golang.org/protobuf` shares a
  release train with `protoc-gen-go` and tracks it exactly. `grpc-go` does
  not: `protoc-gen-go-grpc` versions independently, and its gencode requires
  only the `grpc.SupportPackageIsVersion*` window rather than a specific
  `grpc-go` release, so that floor moves when the window does, not when the
  plugin pin does. Note also that `go mod tidy` does **not** raise an existing
  requirement to match a newer generator — it resolves the build graph, not
  the generator — so `go.mod` is not self-healing and is maintained like every
  other declared floor above.

- Raw-proto packages (`proto-rust`, `proto-npm`) ship no generated code and
  are exempt from the floor rule; they must stay byte-identical to
  `schemas/proto/` (`make check-proto-sync`). `proto-npm` does run the JS
  generator, but only as a CI compile check: the output is gitignored and
  excluded from the published tarball, and the package declares no
  dependencies, so it has no floors to drift.
