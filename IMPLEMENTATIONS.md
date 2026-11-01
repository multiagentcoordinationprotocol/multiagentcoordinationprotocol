# MACP Implementations

Implementations that run the MACP conformance fixtures, and what they claim. Levels, profiles and the Verifier role are defined in [docs/conformance.md](docs/conformance.md). Entries are self-reported, each naming the suite that backs it, linked where the source is public. To add one, open a pull request with a new row.

## Runtimes

| Implementation | Level | Profile | Tested against | Suite |
|---|---|---|---|---|
| [macp-runtime](https://github.com/multiagentcoordinationprotocol/macp-runtime) (reference, Rust) | Standard modes + multi_round | Server; Embedded via the `macp-core`, `macp-modes`, `macp-policy` and `macp-pb` crates | spec `main`, byte-compared in CI | [`tests/conformance_loader.rs`](https://github.com/multiagentcoordinationprotocol/macp-runtime/blob/main/tests/conformance_loader.rs), [`tests/cmt_hash_vectors.rs`](https://github.com/multiagentcoordinationprotocol/macp-runtime/blob/main/tests/cmt_hash_vectors.rs), and the Server claim "Standard modes + multi_round, Server profile (hash vectors in-process)" from [`macp-conform`](https://crates.io/crates/macp-conform) against a running server in the `conform-cli` CI job ([`crates/macp-conform/tests/server_profile.rs`](https://github.com/multiagentcoordinationprotocol/macp-runtime/blob/main/crates/macp-conform/tests/server_profile.rs)) |
| Seam ([zer07labs](https://zer07labs.com), source not public) | Core + Decision, plus Quorum | Embedded: pins `macp-core`, `macp-modes`, `macp-pb` and `macp-policy` 0.9.0 and drives `macp_modes::step` and `replay` directly | spec `60262b8`, vendored files SHA-checked | `seam-coord-macp` tests `macp_conformance.rs`, `cmt_hash_vectors.rs` and `macp_parity_contract.rs` (not public). Seam's daemon refuses proposal, task and handoff sessions at open because its transport cannot drive them to a terminal; those transcripts pass through the bare engine. Policy uses the [`x-com.zer07labs.seam`](registries/policies.md) vendor key |

## Verifiers

| Implementation | Role | Suite |
|---|---|---|
| [macp-sdk-python](https://github.com/multiagentcoordinationprotocol/macp-sdk-python) | Verifier (RFC-MACP-0013) | [`tests/unit/test_commitment_hash_vectors.py`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/tests/unit/test_commitment_hash_vectors.py) |
| [macp-sdk-typescript](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript) | Verifier (RFC-MACP-0013) | [`tests/vectors/cmt-hash.test.ts`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/tests/vectors/cmt-hash.test.ts) |

The Python SDK also runs every conformance fixture against its client-side session projections (`tests/conformance/`). That checks the SDK's view of a session, not a runtime, so it is not a level claim.

## Bindings

| Implementation | Binding | Guide | Suite |
|---|---|---|---|
| [macp-sdk-python](https://github.com/multiagentcoordinationprotocol/macp-sdk-python) (`macp_sdk.a2a`, unreleased on main) | A2A (RFC-MACP-0014 1.1.2-draft) | [`docs/guides/a2a-binding.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/docs/guides/a2a-binding.md) | [`tests/unit/test_a2a.py`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/tests/unit/test_a2a.py) (every vector in [`schemas/conformance/a2a/`](schemas/conformance/a2a/)), [`tests/unit/test_a2a_interop.py`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/tests/unit/test_a2a_interop.py) (official A2A SDK 1.3, dev-only) |
| [macp-sdk-typescript](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript) (`src/a2a.ts`, `./a2a` subpath, unreleased on main) | A2A (RFC-MACP-0014 1.1.2-draft) | [`docs/guides/a2a-binding.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/docs/guides/a2a-binding.md) | [`tests/vectors/a2a.test.ts`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/tests/vectors/a2a.test.ts) (every vector in [`schemas/conformance/a2a/`](schemas/conformance/a2a/)), [`tests/unit/a2a.test.ts`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/tests/unit/a2a.test.ts) (unit tests, including interop with the official A2A SDK 1.3, dev-only) |
