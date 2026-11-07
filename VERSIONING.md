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
`@multiagentcoordinationprotocol/proto`, Maven `io.macp:macp-proto` and
`io.macp:macp-proto-kotlin`, and NuGet `Macp.Proto`. Go is the exception: Go
users install the packages the Buf Schema Registry generates from `main`, which
are not versioned with these releases (`packages/proto-go/README.md`). Rules:

- **One shared version across all languages per release**, cut by tagging
  `proto-vX.Y.Z` (or `workflow_dispatch` with an explicit version). Do NOT
  use bare `vX.Y.Z` tags for proto releases — the tag trigger matches
  `proto-v*` only, and bare `v*` tags are reserved for spec-level releases.
  (The stray `v0.1.4` tag is the mistake this rule exists to prevent.)
- **Choosing the number.** Compare `schemas/proto` with the previous
  `proto-v*` tag:
  - **A service RPC added, removed or changed bumps the MINOR version**
    (`0.1.x` → `0.2.0`). This applies to
    every service (`macp.v1` core, policy, or a mode) and to every language
    package, since they all share the one version and tag. A changed RPC means
    a different request type, response type, or `stream` keyword.
  - **Message, field and enum-value additions may stay PATCH releases.**
    They are proto3-backward-compatible.
  - **Removals and other breaking changes** follow the existing rules: nothing
    wire-breaking is permitted post-freeze without a new package major, and
    the PR needs the `proto-breaking` label and migration notes
    (`CONTRIBUTING.md`, "Substantive Changes").

  Why RPCs are special: consumers depend on these packages with caret
  requirements, such as `macp-proto = "0.1.13"` in Cargo or `^0.1.0` in npm.
  Before 1.0, a caret accepts any later patch but never a new minor. Rust
  consumers generate service traits in `build.rs` from whichever `macp-proto`
  Cargo resolves. An RPC added in a patch release is therefore picked up by
  every already-published consumer, which has no handler for it and stops
  compiling. That happened with `WhatIfReplay`, added in 0.1.12 as a patch:
  published `macp-runtime` 0.9.0 no longer builds without `--locked` (E0046,
  issue #250, macp-runtime#253). A minor bump is never selected by an
  existing `0.1.x` requirement, so published consumers keep building until
  they choose to upgrade. This protection depends on pre-1.0 caret
  semantics: from 1.0 on, a caret accepts new minors, so the rule MUST be
  revisited (an RPC change would need a major bump) before cutting 1.0.

  **Enforced at release.** Before anything publishes (dry runs included),
  `publish-proto-packages.yml` runs `scripts/check-proto-rpc-bump.py`. It
  compares the `service`/`rpc` signatures in every `.proto` file under
  `schemas/proto` between the release and the highest `proto-v*` tag below
  it, and fails if any signature differs while the minor (or major) version
  did not go up. The guard enforces only that minimum: it accepts an RPC
  removal on a minor bump, and the breaking-change rules above still apply.
  To check a planned version before tagging, run `git fetch --tags`, then
  `python3 scripts/check-proto-rpc-bump.py --new-version X.Y.Z` on the commit
  you plan to tag (with no local `proto-v*` tags it has nothing to compare
  and passes). `make proto-rpc-bump-selftest` proves the guard rejects what
  it should. The guard also blocks a full re-run of the workflow for 0.1.12
  and 0.1.13, which were released before it existed and added RPCs as
  patches; `npmjs_only` backfills skip it.
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

## 9. RFC Maturity and Promotion

The versions above describe the wire and the bound semantics. This section
describes the RFC *text*. Each RFC's `**Version:**` header is in one of two
maturity states:

- **Draft** — the version carries a `-draft` suffix (for example
  `1.4.0-draft`). Normative wording can still change in any revision, and the
  changelog records each change.
- **Stable** — the version has no suffix (for example `1.0.0`). Its normative
  text changes only under the rules below.

The `**Status:**` line (`Community Standards Track`) names a track, not a
maturity state, and promotion does not change it.

### 9.1 Promotion criteria

An RFC moves from Draft to Stable only when **all** of the following hold, and
the promotion PR shows the evidence for each one:

1. **Stability window.** No normative change has merged for at least **30
   days**. A change is normative if it adds, removes or alters a requirement
   (an RFC 2119 keyword, a validation rule, an error code, a state transition
   or a wire shape). Fixing a typo, a link or an example that already matched
   the text does not reset the window.
2. **No open defects.** No open issue reports a bug, contradiction or design
   flaw in the RFC.
3. **Conformance coverage.** Every validation rule and state transition the
   RFC defines that the fixture format can express has at least one fixture
   or vector that `make validate` checks: under `schemas/conformance/`, or a
   negative schema fixture under `schemas/json/tests/`. For a Mode RFC this
   includes its `*_happy_path.json` and `*_reject_paths.json` fixtures. The
   promotion PR lists every rule the format cannot express (for example, one
   reached only through an RPC other than `Send`, or one that depends on a
   caller-chosen `message_id`) and says why.
4. **Implementations pass.** The reference runtime (`macp-runtime`) passes
   that fixture set, and both SDKs (`macp-sdk-python`, `macp-sdk-typescript`)
   vendor the current fixtures (`scripts/check-sdk-sync.py` reports no drift).
   MACP has one maintainer, so these are not independent implementations; the
   promotion PR says so.
5. **Dependencies are Stable.** Every RFC that it depends on normatively (one
   whose requirements it needs in order to be implemented, not one it cites
   for information) is already Stable, or is promoted in the same PR.
6. **Maintainer sign-off.** The maintainer approves the promotion, and the
   decision is recorded in `DECISIONS.md`.

An RFC marked **provisional** (for example RFC-MACP-0014) cannot be promoted
while the external specification or registration it depends on is still
provisional.

### 9.2 Promotion

The promotion PR drops the `-draft` suffix, keeping the same `MAJOR.MINOR.PATCH`
(`1.6.1-draft` becomes `1.6.1`), and adds a changelog entry that cites the
evidence for each criterion in 9.1.

### 9.3 Changing a Stable RFC

After promotion, every revision of a Stable RFC bumps its version:

- **PATCH** — editorial only: wording, examples or links, with no change to
  what is accepted, rejected or produced.
- **MINOR** — a backward-compatible addition, such as a new optional field or
  a new error code for a case that was previously unspecified. A history that
  a conformant runtime accepted before the change MUST still replay to the same
  outcome (Section 5; RFC-MACP-0003).
- **MAJOR** — anything else, including tightening a validation rule. A Mode
  change that alters resolution also requires a new Mode version (Section 3).

A Stable RFC never returns to Draft. Work that would need to goes into a new
`-draft` revision with the next MAJOR version (for example `2.0.0-draft`),
while the Stable version stays in force until that revision is promoted.
