# RFC-MACP-0013
# Multi-Agent Coordination Protocol (MACP) — Canonical Commitment Hash

**Document:** RFC-MACP-0013
**Version:** 1.4.3-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001, RFC-MACP-0003

> **Changelog — 1.4.3-draft:** `RECEIPT_UNAVAILABLE` (§13 requirement 3) is promoted from `provisional` to `permanent` in `registries/error-codes.md`, now that macp-runtime 0.11.0, macp-sdk-python and macp-sdk-typescript all ship it. Its 409 / `FAILED_PRECONDITION` mapping and meaning are unchanged; it is now a compatibility promise and is pinned in `schemas/parity/contract.json`. No wire change.
>
> **Changelog — 1.4.2-draft:** Editorial. §13 requirement 8 no longer says a runtime without a signing key publishes `{"keys":[]}` unconditionally. That sentence contradicted the same requirement's rule that every key which signed a receipt the runtime still serves stays in the key set. An unsigned runtime publishes its retired keys, and an empty set only when it has none.
>
> **Changelog — 1.4.1-draft:** Editorial. Section 5's first reconciliation item described RFC-MACP-0001 §10 as an Envelope-level mapping (§10.1–§10.7) that says nothing about a `CommitmentPayload`'s fields. RFC-MACP-0001 1.6.0-draft extends §10 to every message, so the item now says that, and cites RFC-MACP-0001 §10.14, which excludes this projection from §10's scope. The conclusion is unchanged: the projection is defined only by this RFC, and RFC-MACP-0001 §10.6 does not reach it. **Replay:** no exposure.
>
> **Changelog — 1.4.0-draft:** New §13, **Receipt Issuance (optional)**: a normative, capability-gated way for a runtime to issue the Appendix A receipts itself and publish its verification keys. Two optional RPCs, `GetDecisionReceipt` (receipt as JSON text) and `GetReceiptKeys` (a JWK Set as JSON text), are advertised by the new `Capabilities.decision_receipt` (`DecisionReceiptCapability`, `core.proto` field 8). Eleven numbered requirements cover advertisement, format, the RESOLVED-with-`CommitmentPayload` precondition (new **provisional** error code `RECEIPT_UNAVAILABLE`, 409 / `FAILED_PRECONDITION`), mandatory `commitment_wire_b64` and omitted `transcript`, the exact `jws` protected header, first-writer-wins issue-once semantics, non-interference with session state and replay, key-set rules, issuer stability, supersession, and privacy. New `schemas/json/macp-receipt-keys.schema.json` (no private members), `examples/discovery/receipt_keys.json` (the A.5 key), and the media type `application/macp-receipt+json`. Vector `receipt_010_wire_match` is named as the reference issuance shape; no vector is added or changed. Additive: Appendix A stays informative for anyone else, and a runtime that does not advertise the capability changes nothing. **Replay:** no exposure. Issuance happens after resolution, never feeds session state, and replay never signs.
>
> **Changelog — 1.3.0-draft:** Appendix A gains reference vectors. Twelve receipt vectors under `schemas/conformance/receipt/` pin, for a given receipt and set of trusted keys, the outcome a conforming verifier returns at each step of A.4: refusal, integrity (including the `commitment_wire_b64` path), one outcome per attestation, and the overall result. A.4 now names the result of a receipt whose integrity is *mismatch* or *cannot-verify*, **unverified**, which the text already implied by ending verification there. A.5 names a second key, `example-2`, which the vectors use for a valid signature from an untrusted key. The vectors are checked in CI by a stdlib-only reference verifier (`scripts/check-receipt-vectors.py`, with its own JCS and Ed25519), independent of the generator. Additive and informative: the receipt format, its schema and the signed example are unchanged, and vector `receipt_001` is that example byte for byte. **Replay:** no exposure (adoption roadmap W3.10).
>
> **Changelog — 1.2.0-draft:** New informative Appendix A defines `macp-receipt/1`, a portable decision receipt that anchors one Commitment on its canonical `commitment_hash`. Integrity is recomputed from the receipt's Section 3 projection, or verified through Section 6.1 when the wire encoding is included. Authenticity comes from typed attestations: a detached JWS (EdDSA) over the JCS receipt body, or a vendor attestation that declares what its preimage binds, so a vendor token over some other digest is reported as informative rather than as authenticity. The design is key-source-agnostic, so it does not depend on any one key service. Adds `schemas/json/macp-decision-receipt.schema.json` and a signed example. Additive and informative: nothing in Sections 1–12 changes, and no implementation is required to issue receipts. **Replay:** no exposure. A receipt is produced after resolution and never feeds session state (adoption roadmap W3.10, design pulled forward as E5).
>
> **Changelog — 1.1.0-draft:** New §6.1 (Verification) gives the three outcomes of Sections 5 and 6 — *match*, *mismatch*, *cannot-verify* — an operation and vectors. Until now every vector was a compute vector (payload in, hash out), so nothing pinned the other two outcomes: an implementation that dropped unknown fields and hashed the rest passed every vector while violating Section 5. An implementation that offers verification MUST now expose it as an operation distinct from computation, taking the payload's **wire encoding** (so unknown fields stay observable) and a claimed hash. §6.1 also states three wire-decoding rules (an unparseable encoding is *cannot-verify*; a repeated known field takes Protobuf merge semantics; a zero-length encoding is the all-default payload of vector `003` and is hashable) and that a claimed hash not in canonical form is *mismatch*, never normalized and never *cannot-verify*. §11 gains five verify vectors, `cmt_hash_006` through `cmt_hash_010`, and `vector-schema.json` gains the optional `wire_hex`, `claimed_hash` and `expected_outcome` fields that carry them; the values match the ones macp-runtime pins in its `verify_commitment_hash` crate tests. Vectors `001`–`005` are unchanged and continue to mean *match* on their computed hash. Additive: the computation, every existing hash value and the label `macp-commitment-hash/1` are unchanged, and an implementation that does not offer verification is unaffected. **Replay:** no exposure. Verification is a read-only check over a payload and a claim, and it never changes session state; no previously computed hash changes (seam-embedder-findings proposal S14, issue #185).

## Abstract

`CommitmentRef.commitment_hash` (RFC-MACP-0001 §7.3.1) is today an implementation-defined digest: Core requires it to be non-empty and uses it to chain a superseding commitment back to the commitment it revises, but defines no algorithm for computing it. This leaves every implementation free to invent its own convention, which is workable only until two implementations need to agree on a value — and a superseding commitment crossing a session boundary is exactly that case. This document ends the ambiguity: it defines a single canonical algorithm — a domain-separated SHA-256 digest over a JCS-canonicalized JSON projection of a frozen nine-field `CommitmentPayload` — and requires conforming runtimes and SDKs to compute and use it wherever a `commitment_hash` is written.

## 1. Introduction and Scope

RFC-MACP-0003 §6 ("Cryptographic Integrity (Optional)") lists "final session hashes embedded in terminal records" among the constructions high-assurance deployments MAY add, without defining how any of them are computed. RFC-MACP-0001 §7.3.1 goes further for one specific field: it makes `CommitmentRef.commitment_hash` structurally required whenever `supersedes` is present, but limits the runtime's obligation to checking that the field is non-empty. Neither document defines what value a conforming sender computes. This RFC closes that gap for `CommitmentRef.commitment_hash` only — it does not define `session_hash` or any other digest named informally in RFC-MACP-0003 §6 (see Section 10).

This document is issued as a standalone RFC rather than as an in-place amendment to RFC-MACP-0001. An in-place amendment to a `1.0.0-draft` Core RFC is invisible to anyone tracking RFC numbers by citation, and a downstream registry that anchors on this construction needs a citable, stable RFC identifier independent of Core's own revision history. RFC-MACP-0013 is that identifier.

Conforming runtimes and SDKs that construct or verify a `CommitmentRef.commitment_hash` value MUST implement the projection defined in Section 3 and the algorithm defined in Section 4. A `commitment_hash` value not produced by that algorithm is non-conforming under this RFC regardless of when it was written (see Section 9).

## 2. Conventions and Terminology

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as normative requirements, consistent with RFC-MACP-0001 §2.

A **canonical commitment hash** is the value defined by the algorithm in Section 4: the literal string `sha256:` followed by 64 lowercase hexadecimal characters.

A **projection** is the JSON object produced from a `CommitmentPayload` by applying the rules in Section 3. It is an input to hashing, not a wire-format serialization; it is never transmitted on its own.

A **label** (for example `macp-commitment-hash/1`) identifies one version of the projection rules and preimage construction defined by this RFC. See Section 7.

## 3. The Hashing Projection

The projection maps a `CommitmentPayload` (RFC-MACP-0001 Appendix A, `core.proto`) to a JSON object under four normative rules.

1. **Keys are the proto field names, in snake_case.** The projection uses `commitment_id`, `action`, `authority_scope`, `reason`, `mode_version`, `policy_version`, `configuration_version`, `outcome_positive`, and `supersedes`; inside `supersedes`, `session_id` and `commitment_hash`. An SDK that holds these values in a different internal shape (for example, lowerCamelCase field names in a TypeScript SDK) MUST project into this key set when computing or verifying the hash; it MUST NOT serialize its own internal representation and call the result a canonical commitment hash.

2. **Scalars are always materialized.** Every string field is present with its value, following the empty-string rule of RFC-MACP-0001 §10.7: an unset or empty string field is represented as `""`, never omitted and never `null`. `outcome_positive` is always present as a JSON boolean, **including when its value is `false`**. This deliberately contradicts the common proto3-JSON convention of omitting fields at their default value: for the purpose of this projection, an absent optional scalar MUST be materialized as `""` (strings) or `false` (`outcome_positive`), not dropped from the object.

3. **Message fields are omitted when unset.** `supersedes` is a message-typed field: when a `CommitmentPayload` carries no `supersedes` reference, the key `supersedes` is absent from the projection entirely — not present with a `null` or empty-object value. When `supersedes` is set, it is projected as an object carrying `session_id` and `commitment_hash` under the same string rule as rule 2. This is an *unset vs. empty* distinction, not an *empty vs. non-empty* one: a `CommitmentPayload` whose `supersedes` is present but whose `session_id` and `commitment_hash` are both the empty string projects to `{"supersedes":{"commitment_hash":"","session_id":""}}` and hashes differently from a payload where `supersedes` is absent altogether.

4. **Chaining is intended.** Because `supersedes.commitment_hash` is itself a canonical commitment hash computed under this algorithm, a superseding commitment's hash transitively covers the content of the commitment it supersedes, one link at a time.

## 4. The Algorithm

The canonical commitment hash of a `CommitmentPayload` is computed as follows:

1. Project the `CommitmentPayload` to JSON per Section 3.
2. Canonicalize the projection with **JCS** [RFC 8785]. Call the resulting UTF-8 byte sequence `C`.
3. Form the domain-separated preimage `P = ASCII("macp-commitment-hash/1:") || C`, where `||` denotes byte concatenation.
4. The canonical commitment hash is the literal string `sha256:` followed by the 64 lowercase hexadecimal characters of `SHA-256(P)` [FIPS 180-4].

**Normative subset note.** The Section 3 projection contains no JSON numbers and no JSON arrays — only strings, exactly one boolean, and one optional nested object. A conforming implementation therefore needs only the string, boolean, and object subset of [RFC 8785]; the ECMAScript number-serialization rules of RFC 8785 §3.2.2.3 are unreachable on this projection and MAY be omitted from an implementation targeting this RFC alone. Because every member name in the frozen field set (Section 5) is ASCII, the §3.2.3 UTF-16-code-unit key-ordering rule reduces, for member names, to plain byte-order comparison; string *values* remain unconstrained and still require full escaping per RFC 8785 §3.2.2.2. A conforming implementation of this subset is small — on the order of tens of lines in a typical language — and does not require a general-purpose JCS library.

## 5. Frozen Field Set and Label Versioning

This label, `macp-commitment-hash/1`, covers **exactly** the following nine fields of `CommitmentPayload`, enumerated here in proto field-number order so that this RFC is self-contained and does not silently drift when the proto is edited:

| # | Field | Type |
|---|-------|------|
| 1 | `commitment_id` | string |
| 2 | `action` | string |
| 3 | `authority_scope` | string |
| 4 | `reason` | string |
| 5 | `mode_version` | string |
| 6 | `policy_version` | string |
| 7 | `configuration_version` | string |
| 8 | `outcome_positive` | bool |
| 9 | `supersedes` | `CommitmentRef` (message) |

`supersedes`, when set, carries exactly two fields: `session_id` (1) and `commitment_hash` (2).

A `CommitmentPayload` carrying a field outside this set is **not hashable under this label**. A verifier presented with such a payload MUST return a **cannot-verify** result, which is distinct from a **mismatch** result (Section 6): cannot-verify means the label does not cover the payload's shape, while mismatch means the label covers the payload's shape but the computed hash disagrees with a claimed value.

This requires reconciling two documents, in this order:

1. The Section 3 projection is **not** the RFC-MACP-0001 §10 canonical JSON mapping. RFC-MACP-0001 §10 maps MACP messages, including a `CommitmentPayload`, to JSON on the wire, and RFC-MACP-0001 §10.14 excludes this projection from its scope. The projection defined here is a hashing projection defined solely by this RFC, so RFC-MACP-0001 §10.6 does not reach it.
2. **For the avoidance of doubt** — because RFC-MACP-0001 §10.6 is unqualified prose ("JSON consumers MUST ignore unrecognized fields for forward compatibility") and a reader could otherwise apply it by analogy to this projection — a `CommitmentPayload` carrying a field unrecognized under `macp-commitment-hash/1` is **cannot-verify**, never silently ignored.

Consequently, **adding a field to `CommitmentPayload` is a label bump to `macp-commitment-hash/2`, not a routine additive proto change.** A future `core.proto` change that adds a tenth field MUST either leave that field outside the hash (an explicit, documented exclusion) or define and advertise a new label under which it is included; it MUST NOT be added silently under the existing `macp-commitment-hash/1` label. This constraint is intentionally also recorded as a doc comment directly on `message CommitmentPayload` in `core.proto`, so that whoever adds field ten reads it at the point of change.

## 6. Hashability

The canonical commitment hash is defined over any `CommitmentPayload` value that is projectable under Section 3 and covered by the frozen field set of Section 5 — **whether or not that value satisfies the structural well-formedness obligations of RFC-MACP-0001 §7.3.1.** Hashing is a pure function of the projected field values; it MUST NOT be gated on, or skipped because of, a payload's validity under [RFC-MACP-0001](RFC-MACP-0001-core.md) §7.3.1 or any other structural check.

The practical consequence is that a verifier can always compute the canonical commitment hash of a received `CommitmentPayload` — including one whose fields are empty strings, or whose `supersedes` is present with empty sub-fields — and compare it against a claimed value. A disagreement in that comparison is a **mismatch**: a definite, reportable outcome, distinct from the **cannot-verify** outcome of Section 5, which arises only when the payload's field set falls outside what the label covers, not when its field values are themselves invalid or degenerate.

### 6.1 Verification

An implementation that offers verification MUST expose it as an operation distinct from computation, taking the payload's wire encoding (so that unknown fields remain observable) and a claimed hash, and returning exactly one of *match*, *mismatch* or *cannot-verify*. A claimed hash that is not in canonical form (Section 9) is *mismatch*.

Wire decoding for verification follows Protobuf semantics, with three outcomes stated explicitly:

1. An encoding that cannot be parsed as a `CommitmentPayload` is *cannot-verify*. This covers a truncated message, a known field number with the wrong wire type, invalid UTF-8 in a `string` field, a group, and field number 0.
2. A known field that appears more than once takes Protobuf merge semantics: the last value wins for a scalar, and messages such as `supersedes` merge.
3. A zero-length encoding is the all-default payload (vector `003`). It is hashable and is never *cannot-verify* for that reason alone.

The comparison is exact string equality against the canonical commitment hash the implementation computes, so a claim with a `SHA256:` prefix, uppercase hex, no `sha256:` prefix, or leading or trailing whitespace is *mismatch*, never normalized and never an error. *Cannot-verify* is reserved for the payload encoding (Section 5 and rule 1 above); it is never a verdict on the claim.

## 7. Wire Format and Version Negotiation

The canonical commitment hash is written on the wire as it is today: the literal string `sha256:` followed by 64 lowercase hexadecimal characters, and nothing else. The label (for example `/1`) that identifies which projection and preimage construction produced the value lives **inside the preimage only** (Section 4, step 3); it is not present in, and is not recoverable from, the output string.

This RFC states normatively:

(a) Exactly one label version is current for a given MACP protocol MINOR version.

(b) A bump to a new label (for example `macp-commitment-hash/2`) is itself a MACP protocol MINOR change, and its availability MUST be advertised as a capability — `registries/capabilities.md` is the registry of record for this advertisement.

(c) A verifier MUST recompute a canonical commitment hash using the label, or labels, admitted by the negotiated protocol version for the session in question. A verifier MUST NOT attempt to infer which label produced a given `sha256:`-prefixed value by inspecting the output string itself; the output string carries no label information to inspect.

An alternative design would embed the label directly in the output string — for example, a hypothetical `sha256/1:` prefix followed by hex, in place of plain `sha256:` followed by hex. This RFC rejects that alternative: it changes the existing wire shape of `commitment_hash`, and it breaks fit against downstream systems that already anchor on the bare `sha256:` + 64-hex shape as an opaque digest.

## 8. `commitment_hash` versus `commitment_id`

`CommitmentPayload.commitment_id` and `CommitmentRef.commitment_hash` serve different purposes and MUST NOT be treated as interchangeable.

`commitment_id` is an opaque identifier chosen by whatever mode or runtime logic assigns the commitment. This RFC does not define how `commitment_id` values are generated or how their uniqueness is enforced; it is, itself, one of the nine input fields hashed under Section 5.

`commitment_hash`, by contrast, is entirely content-derived: it is the output of the Section 4 algorithm applied to the fields of the commitment being referenced. Two commitments with different `commitment_id` values but identical projected field values produce the same `commitment_hash`; a single-field change to any of the nine fields in Section 5 changes `commitment_hash` even if `commitment_id` is left untouched. Neither field is a substitute lookup key for the other: `commitment_id` does not verify content, and `commitment_hash` does not, by itself, identify which commitment a party intended to reference absent the accompanying `session_id`.

## 9. Backward Compatibility

Conforming runtimes and SDKs MUST compute `commitment_hash` identically per this RFC, and MUST use the resulting value wherever a `commitment_hash` is written — not only when constructing a new `CommitmentRef`, but in every code path that produces one.

That second obligation, not merely the syntactic canonical-hash-shape check of RFC-MACP-0001 §7.3.1, is what makes a `commitment_hash` value computed before this RFC existed non-conforming: it was not, and cannot retroactively become, the output of the Section 4 algorithm.

This RFC adopts **hard rejection, effective immediately, with no dual-read period**: a `commitment_hash` value that does not match the syntactic shape and the semantic construction defined by this RFC is non-conforming from the day this RFC takes effect. There is no transitional window in which pre-0013 values are accepted alongside post-0013 values.

The operational consequence is concrete, not merely abstract: **a pre-0013 commitment can never be superseded by a post-0013 one.** A pre-0013 `commitment_hash` value is, in general, not a syntactically valid canonical commitment hash under the tightened RFC-MACP-0001 §7.3.1 obligation (a) this RFC requires (`^sha256:[0-9a-f]{64}$`), and even where it happens to match that syntax by coincidence, it was not produced by the Section 4 algorithm and will not verify against a recomputed value. Its hash is therefore unrepresentable as a valid `supersedes.commitment_hash` in a new, post-0013 commitment: any supersession chain that crosses the RFC-MACP-0013 boundary is **severed at that boundary, permanently**. A consumer migrating an existing chain has exactly one path forward: re-issue the current state of that chain as a new commitment under this RFC and begin a new chain from there. This RFC defines no bridging construct, translation function, or dual-format acceptance rule that would let a post-0013 commitment reference a pre-0013 predecessor.

## 10. Scope Boundary and Relationship to Other Digests

This RFC defines the value of `CommitmentRef.commitment_hash` only. `session_hash` and every other digest referenced informally in RFC-MACP-0003 §6 ("signed Envelopes, hash-chained session logs, final session hashes embedded in terminal records") remain implementation-defined; this RFC neither defines their construction nor implies that they share a construction with `commitment_hash` merely because an example shows them side by side.

**Relationship to other digests (non-normative).** The wider MACP family is known to reference at least three distinct commitment-related digest constructions: the canonical commitment hash defined by this RFC (a string-prefixed digest over JCS-canonicalized JSON); a downstream consumer's own digest, constructed as a length-prefixed field tuple hashed without any JSON encoding, surfaced as bare hexadecimal; and a further construction referenced by ACDP's anchor registry. These are distinct, non-convertible identities. This RFC defines no mapping between them and implies none. It is nonetheless worth stating plainly why the stability of the construction in Section 4 matters beyond this repository: the canonical commitment hash defined here may appear as an opaque substring inside a consumer's own digest preimage, and a downstream system that has already done so depends on this value never silently changing shape underneath it.

## 11. Testing Requirements

Conformance for this RFC is defined by ten reference vectors under `schemas/conformance/cmt-hash/`: five compute vectors and five verify vectors.

The five compute vectors each pin the payload JSON, the JCS-canonicalized output, the full domain-separated preimage, and the resulting canonical commitment hash, so that an implementation diverging from these vectors can identify at which step it diverged:

- `cmt_hash_001_minimal.json` — a baseline `CommitmentPayload` with no `supersedes`.
- `cmt_hash_002_supersedes.json` — `supersedes` set, chained: its `commitment_hash` field is `cmt_hash_001_minimal`'s output (Section 3, rule 4).
- `cmt_hash_003_all_empty.json` — every string field `""`, `outcome_positive` `false`, no `supersedes` (Section 3, rule 2).
- `cmt_hash_004_empty_supersedes.json` — identical to `cmt_hash_003_all_empty.json` except `supersedes` is **present** with both `session_id` and `commitment_hash` set to `""` — a payload that RFC-MACP-0001 §7.3.1 rejects as not well-formed, but that Section 6 of this RFC requires to be hashable regardless.
- `cmt_hash_005_escapes.json` — exercises RFC 8785 §3.2.2 escaping: embedded quote and backslash characters, tab and newline short-form escapes, non-ASCII characters, and an astral-plane codepoint requiring surrogate-pair handling in the source encoding.

A conforming implementation MUST reproduce the pinned hash for each of the five vectors above, and MUST assert that `cmt_hash_003_all_empty.json` and `cmt_hash_004_empty_supersedes.json` produce **different** canonical commitment hashes: this inequality is the sole vector-level check that the *unset vs. empty* rule of Section 3, rule 3 is actually implemented, rather than `supersedes` being treated as absent whenever its sub-fields are empty. Each compute vector also means *match*: verifying its pinned hash against the payload's wire encoding (Section 6.1) MUST return *match*.

The five verify vectors each pin a payload's Protobuf wire encoding (`wire_hex`), a `claimed_hash`, and the `expected_outcome` a conforming verifier MUST return (Section 6.1). `H001` below is `cmt_hash_001_minimal.json`'s hash:

- `cmt_hash_006_unknown_field.json` — the wire of `001` with field 99 appended, claiming `H001`: *cannot-verify* (Section 5).
- `cmt_hash_007_mismatch.json` — exactly the wire of `001`, claiming a hash that differs from `H001` in one hex digit: *mismatch*.
- `cmt_hash_008_noncanonical_claim.json` — the wire of `001`, claiming `H001` in uppercase hex: *mismatch*.
- `cmt_hash_009_unknown_supersedes_field.json` — the payload of `001` plus a `supersedes` carrying an unknown `CommitmentRef` field 3, claiming the correct hash of the covered payload *without* field 3: *cannot-verify*. An implementation that drops unknown fields and hashes the rest reports *match* here, so the vector cannot be passed by accident.
- `cmt_hash_010_no_prefix.json` — the wire of `001`, claiming `H001`'s hex digits without the `sha256:` prefix: *mismatch*, never an error.

An implementation that offers verification MUST return the pinned `expected_outcome` for each verify vector.

## 12. Security Considerations

The domain-separation prefix `macp-commitment-hash/1:` (Section 4, step 3) exists to prevent a value computed under this construction from being confusable with a digest computed over the same or similar bytes under an unrelated protocol or an unrelated label version; implementations MUST NOT omit it, and MUST NOT reuse a preimage computed without it as if it were a canonical commitment hash.

The canonical commitment hash is a content digest, not a message authentication code or a digital signature: on its own, it establishes that a claimed `CommitmentPayload` projects to a specific value, not that the value was produced by an authorized party or delivered without tampering. Deployments requiring tamper evidence or sender authenticity MUST combine this construction with the transport security, authentication, and Envelope-signing mechanisms of RFC-MACP-0004; this RFC does not substitute for them.

Because this is a public content digest rather than a keyed value, comparisons against a claimed `commitment_hash` need not be constant-time in the way a MAC or signature comparison would; SHA-256's second-preimage and collision resistance assumptions [FIPS 180-4] are the load-bearing security property here, not comparison timing.

The frozen field set (Section 5) and the RFC 8785 subset restricted to strings, one boolean, and one nested object (Section 4) are correctness properties that keep independent implementations aligned; they are not, by themselves, security boundaries. An implementation that reintroduces general JCS number or array handling on a conforming `CommitmentPayload` projection does not create a divergence, because no number or array is reachable in a well-formed projection under Section 3 — but an implementation that fails to enforce the frozen field set of Section 5 (for example, by silently including or excluding a field) produces a value that is not a canonical commitment hash at all, and MUST NOT be presented to a counterparty as one.

## 13. Receipt Issuance (Optional)

A runtime MAY issue the decision receipts of Appendix A itself and publish the keys that verify them. This section defines how. It is optional: a runtime that does not implement it is unaffected, and nothing in Sections 1–12 changes for one that does. Appendix A's format is unchanged; requirement 2 tightens two of its rules for runtime-issued receipts. The two RPCs are listed in [RFC-MACP-0006](RFC-MACP-0006-transport-bindings.md) §3 and §3.9:

```protobuf
message DecisionReceiptCapability {
  bool get_decision_receipt = 1;
  bool signed = 2;
}

rpc GetDecisionReceipt(GetDecisionReceiptRequest) returns (GetDecisionReceiptResponse);
rpc GetReceiptKeys(GetReceiptKeysRequest) returns (GetReceiptKeysResponse);
```

`GetDecisionReceipt` takes a `session_id` and returns the receipt as JSON text in `receipt_json`. `GetReceiptKeys` takes nothing and returns a JWK Set [RFC 7517] as JSON text in `jwks_json`. Both travel as JSON text, not as Protobuf mirrors: the receipt is a JSON document signed over its JCS body (A.2), so a Protobuf rendering would be a second source of truth. The media type of a receipt document is `application/macp-receipt+json` ([`registries/media-types.md`](../registries/media-types.md)).

`DecisionReceiptCapability` is `Capabilities.decision_receipt` (field 8 in [`core.proto`](../schemas/proto/macp/v1/core.proto)). `get_decision_receipt` is `true` when the runtime implements both RPCs. `signed` is `true` when every receipt the runtime issues from now on carries at least one `jws` attestation with `alg` `EdDSA`. It says nothing about receipts issued earlier. A verifier learns which algorithms the runtime signs with from the `alg` of its key-set entries, so a later revision that admits `ES256` (A.3) is additive; until then requirement 5 fixes `EdDSA`.

Requirements:

1. **Advertisement.** A runtime that implements these RPCs MUST advertise `decision_receipt.get_decision_receipt = true`. A client MUST NOT call them otherwise. A runtime that does not implement them answers both with the transport's "unimplemented" status (gRPC `UNIMPLEMENTED`).
2. **Format.** An issued receipt MUST be a `macp-receipt/1` receipt (Appendix A) that validates against [`schemas/json/macp-decision-receipt.schema.json`](../schemas/json/macp-decision-receipt.schema.json) and is verifiable by A.4. Two of Appendix A's SHOULDs are MUSTs for a runtime-issued receipt: every `jws` attestation uses `alg` `EdDSA` (A.3), and its protected header carries the `kid` (A.3).
3. **Precondition and errors.** A receipt is issued only for a session that is RESOLVED and whose resolving payload is a `CommitmentPayload`, in any mode, standard or extension. Otherwise the runtime MUST fail the call with `RECEIPT_UNAVAILABLE`, which also covers a receipt that could not be issued for any other reason. A storage failure while reading or persisting a receipt is `INTERNAL_ERROR`. An unknown session is `SESSION_NOT_FOUND`, and a caller not authorized to observe the session is `FORBIDDEN`: the caller MUST be authorized exactly as for `GetSession` ([RFC-MACP-0004](RFC-MACP-0004-security.md)). `GetReceiptKeys` needs only transport authentication, as `GetManifest` does. Runtimes SHOULD apply the rate limits and admission control of RFC-MACP-0004 to both RPCs.
4. **Contents.** `commitment_wire_b64` MUST be present and MUST be the payload bytes of the accepted resolving Envelope, verbatim (not a re-encoding of the decoded message, which could drop unknown fields), so a verifier can run Section 6.1 on it. `semantics_rev` SHOULD be present. `transcript` MUST be omitted until a transcript digest construction is specified, because a digest whose construction a verifier cannot recompute vouches for nothing.
5. **Signature header.** The protected header of every `jws` attestation MUST be exactly `{"alg":"EdDSA","kid":<kid>}`, with no `typ` and no other member. `receipt_format`, inside the signed body, already separates receipts from other signed JSON, and every existing signer and verifier uses exactly this header.
6. **Issue once.** A runtime MUST NOT serve two different attested receipts for one session; a signed candidate that loses the first write is never served. Once it has served an attested receipt, it MUST serve that receipt byte-identical on every later call. It MUST persist the first receipt it issues with first-writer-wins semantics, so that concurrent first calls, including calls served by different replicas, return the same bytes. An unattested (integrity-only) receipt MAY be replaced, once, by an attested one after a signing key is configured; an attested receipt is never replaced. `issued_at` is the time of first issuance of the receipt served.
7. **Non-interference.** Issuance MUST NOT feed session state, deduplication, lifecycle events or replay. A failure to issue a receipt MUST NOT fail, delay or alter the Commitment it describes. Replay and recovery MUST NOT sign: a receipt already persisted is served as persisted, and one never issued is issued only by a later call.
8. **Keys.** Every `kid` in the key set MUST be unique and MUST NOT be reused for a different key. Every key that signed a receipt the runtime still serves MUST stay in the key set. The key set MUST NOT contain private key members: `d`, `p`, `q`, `dp`, `dq`, `qi`, `oth` or `k` (RFC 7518 §6). When the runtime has no signing key, `signed` is `false`, and the key set holds only the retired keys this requirement keeps; it is `{"keys":[]}` when there are none. [`schemas/json/macp-receipt-keys.schema.json`](../schemas/json/macp-receipt-keys.schema.json) is its schema, and [`examples/discovery/receipt_keys.json`](../examples/discovery/receipt_keys.json) publishes the A.5 key `example-1`.
9. **Issuer.** `issuer` MUST be stable across restarts of the same runtime deployment. A verifier obtains the keys for a receipt's `kid` from the runtime that issued it; this closes, for runtime-issued receipts, the key-discovery question A.3 leaves open.
10. **One session, one receipt.** A receipt describes one session's Commitment. Under supersession ([RFC-MACP-0001](RFC-MACP-0001-core.md) §7.3.1) each session has its own receipt. A receipt never claims that its Commitment is the current one: a later session's Commitment may supersede it, and a verifier that needs currency checks the chain itself.
11. **Privacy.** A receipt reveals the full Commitment, including `reason` (A.6). Any caller authorized to observe a session can fetch its receipt, so a bearer of an observer credential can fetch every receipt it can observe, as with `GetSession`.

Vector `receipt_010_wire_match` (`schemas/conformance/receipt/`) is the reference shape of a runtime-issued receipt: `commitment_wire_b64` present, `issuer` `runtime:example`, `semantics_rev` present, no `transcript`, and one `jws` attestation whose protected header is `{"alg":"EdDSA","kid":"example-1"}`. A receipt built from compacted history needs nothing more than the resolving payload bytes, so compaction does not prevent issuance, provided the runtime keeps those bytes verbatim through compaction.

## Appendix A. Decision Receipts (Informative)

This appendix defines **`macp-receipt/1`**, a portable record of one binding Commitment that a third party can check offline. It is informative: no implementation is required to issue or verify receipts. A runtime that issues them through `GetDecisionReceipt` follows Section 13, which makes this format normative for that runtime. An implementation that does issue them, and calls them MACP decision receipts, SHOULD follow this format so that one verifier works for every issuer. The JSON Schema is [`schemas/json/macp-decision-receipt.schema.json`](../schemas/json/macp-decision-receipt.schema.json), and [`examples/discovery/decision_receipt.json`](../examples/discovery/decision_receipt.json) is a signed example.

### A.1 Two properties, kept apart

A receipt claims two different things, and a verifier reports them separately:

1. **Integrity.** The recorded Commitment has the recorded `commitment_hash`. This needs no keys: the verifier recomputes the hash from `commitment` by Section 4. When `commitment_wire_b64` is present, the verifier also runs Section 6.1 on the wire encoding, which is the only way to see unknown fields, and checks that the wire projects to `commitment`.
2. **Authenticity.** Some party vouches for that Commitment. This comes only from `attestations`, and only from an attestation whose preimage covers `commitment_hash`.

Everything is anchored on `commitment_hash`, not on any signing key or key service. That way, issuers that use different key sources (a runtime's own key, a bring-your-own key, an identity service, a vendor trust token) produce receipts that are checked the same way up to the last step.

### A.2 Fields

| Field | Required | Meaning |
|---|---|---|
| `receipt_format` | yes | the literal `macp-receipt/1` |
| `session_id`, `mode` | yes | the session the Commitment resolved |
| `commitment` | yes | the Section 3 projection of the `CommitmentPayload`. It already carries `mode_version`, `policy_version` and `configuration_version`, so the receipt does not repeat them |
| `commitment_hash` | yes | the Section 4 hash of `commitment` |
| `commitment_wire_b64` | no | the payload's Protobuf wire encoding, for full Section 6.1 verification |
| `semantics_rev` | no | `{implementation, rev}`: the RFC-MACP-0003 §3.2 revision, named together with the implementation that scopes it |
| `transcript` | no | `{digest_alg, digest, message_count}`: a digest of the session history. Its construction is implementation-defined (Section 10), so `digest_alg` names it |
| `issuer` | yes | an opaque identifier of who issued the receipt. It is not a trust anchor |
| `issued_at` | yes | RFC 3339 UTC time of issue. It is informational |
| `attestations` | yes | an array, possibly empty, of the entries in A.3 |

The **receipt body** is the receipt with `attestations` removed, canonicalized with JCS [RFC 8785]. Unlike the Section 3 projection, the body can contain integers (`rev`, `message_count`), so an issuer needs the JCS number rules for non-negative integers. Because the body contains `commitment_hash`, anything that signs the body also binds the hash.

### A.3 Attestations

- **`jws`**: a compact JWS [RFC 7515] with a detached payload (Appendix F of RFC 7515): `<protected header>..<signature>`, where the signing input uses the base64url of the receipt body. An issuer SHOULD use `EdDSA` (Ed25519) and MAY use `ES256`. A verifier that implements `jws` MUST support `EdDSA`. The protected header SHOULD carry a `kid`. How a verifier gets the key for that `kid` is outside this appendix.
- **`vendor`**: `{format, binds, value}`, an attestation in a format this appendix does not define, for example an AITP Trust Context Token. `format` names it without collisions (reverse-domain is recommended). `binds` states what its own preimage covers:
  - `commitment_hash`: the hash string itself, or a preimage that contains it verbatim.
  - `receipt`: the same receipt body a `jws` attestation signs.
  - `other`: anything else, for example a vendor digest over the vendor's own commitment fields.

  An attestation with `binds: other` is informative only and MUST NOT be reported as establishing authenticity of the receipt's Commitment, even if the verifier implements its format.

### A.4 Verification

A verifier reports one outcome for integrity and one per attestation:

1. If `receipt_format` is one it does not implement, it **refuses** the receipt.
2. **Integrity:** *match* or *mismatch*, using the Section 6.1 outcome vocabulary. If `commitment_wire_b64` is present and cannot be decoded, the result is *cannot-verify*. A *mismatch* ends verification: an attestation over a body whose hash does not match vouches for nothing.
3. **Each attestation:** *valid*, *invalid*, *unknown-key* (the format is understood but no trusted key matches), or *unsupported* (the format or `alg` is not implemented, or `binds` is `other`).
4. The receipt is **attested** for that verifier if integrity is *match* and at least one attestation is *valid*. A receipt with integrity *match* and no valid attestation is **integrity-only**. That is still useful, because it pins exactly what was decided, but nobody has vouched for it. A receipt whose integrity is *mismatch* or *cannot-verify* is **unverified**, and its attestations are not evaluated.

The vectors in `schemas/conformance/receipt/` pin these outcomes. Each one gives a receipt, the keys the verifier trusts, and the expected integrity result, attestation results and overall result, written with underscores as in the Section 11 vectors (`cannot_verify`, `unknown_key`, `integrity_only`). A verifier that implements this appendix SHOULD pass all of them. `vector-schema.json` in that directory documents the shape.

### A.5 Example key

The example's `jws` attestation is signed with an Ed25519 key that exists only for this example: the seed is SHA-256 of the ASCII string `macp-receipt example key`, and the public key, as a JWK `x`, is `TDVzkxaSf6_Oxu7mmn5TbCkF80s8Ulh33qKQsi0gnZM` with `kid` `example-1`. Its `commitment` is the payload of vector `cmt_hash_002_supersedes`, so its `commitment_hash` is that vector's pinned hash. The vectors also use a second key, `example-2`, whose seed is SHA-256 of `macp-receipt example key 2`, to carry a valid signature from a key the verifier does not trust. Both keys are public and MUST NOT be trusted outside tests. Vector `receipt_001_attested` is this example unchanged.

### A.6 Security notes

A receipt reveals the full Commitment, including `reason`. An issuer that must withhold fields cannot redact them, because redaction changes `commitment_hash`; it has to withhold the receipt instead. `issued_at` is not evidence of when the Commitment was made. A deployment that needs that proves it with a timestamping attestation. Revoking a signing key does not revoke receipts signed before the revocation: deciding whether to accept them is a verifier policy, outside this appendix.
