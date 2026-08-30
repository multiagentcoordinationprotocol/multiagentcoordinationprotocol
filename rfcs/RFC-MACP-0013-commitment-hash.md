# RFC-MACP-0013
# Multi-Agent Coordination Protocol (MACP) — Canonical Commitment Hash

**Document:** RFC-MACP-0013
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001, RFC-MACP-0003

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

1. The Section 3 projection is **not** the RFC-MACP-0001 §10 canonical JSON mapping. RFC-MACP-0001 §10 is an Envelope-level mapping (RFC-MACP-0001 §10.1–§10.7) and says nothing about the internal fields of a `CommitmentPayload`. The projection defined here is a hashing projection defined solely by this RFC, so RFC-MACP-0001 §10.6 does not reach it.
2. **For the avoidance of doubt** — because RFC-MACP-0001 §10.6 is unqualified prose ("JSON consumers MUST ignore unrecognized fields for forward compatibility") and a reader could otherwise apply it by analogy to this projection — a `CommitmentPayload` carrying a field unrecognized under `macp-commitment-hash/1` is **cannot-verify**, never silently ignored.

Consequently, **adding a field to `CommitmentPayload` is a label bump to `macp-commitment-hash/2`, not a routine additive proto change.** A future `core.proto` change that adds a tenth field MUST either leave that field outside the hash (an explicit, documented exclusion) or define and advertise a new label under which it is included; it MUST NOT be added silently under the existing `macp-commitment-hash/1` label. This constraint is intentionally also recorded as a doc comment directly on `message CommitmentPayload` in `core.proto`, so that whoever adds field ten reads it at the point of change.

## 6. Hashability

The canonical commitment hash is defined over any `CommitmentPayload` value that is projectable under Section 3 and covered by the frozen field set of Section 5 — **whether or not that value satisfies the structural well-formedness obligations of RFC-MACP-0001 §7.3.1.** Hashing is a pure function of the projected field values; it MUST NOT be gated on, or skipped because of, a payload's validity under §7.3.1 or any other structural check.

The practical consequence is that a verifier can always compute the canonical commitment hash of a received `CommitmentPayload` — including one whose fields are empty strings, or whose `supersedes` is present with empty sub-fields — and compare it against a claimed value. A disagreement in that comparison is a **mismatch**: a definite, reportable outcome, distinct from the **cannot-verify** outcome of Section 5, which arises only when the payload's field set falls outside what the label covers, not when its field values are themselves invalid or degenerate.

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

Conformance for this RFC is defined by five reference vectors, each pinning the payload JSON, the JCS-canonicalized output, the full domain-separated preimage, and the resulting canonical commitment hash, so that an implementation diverging from these vectors can identify at which step it diverged:

- `cmt_hash_001_minimal.json` — a baseline `CommitmentPayload` with no `supersedes`.
- `cmt_hash_002_supersedes.json` — `supersedes` set, chained: its `commitment_hash` field is `cmt_hash_001_minimal`'s output (Section 3, rule 4).
- `cmt_hash_003_all_empty.json` — every string field `""`, `outcome_positive` `false`, no `supersedes` (Section 3, rule 2).
- `cmt_hash_004_empty_supersedes.json` — identical to `cmt_hash_003_all_empty.json` except `supersedes` is **present** with both `session_id` and `commitment_hash` set to `""` — a payload that RFC-MACP-0001 §7.3.1 rejects as not well-formed, but that Section 6 of this RFC requires to be hashable regardless.
- `cmt_hash_005_escapes.json` — exercises RFC 8785 §3.2.2 escaping: embedded quote and backslash characters, tab and newline short-form escapes, non-ASCII characters, and an astral-plane codepoint requiring surrogate-pair handling in the source encoding.

A conforming implementation MUST reproduce the pinned hash for each of the five vectors above, and MUST assert that `cmt_hash_003_all_empty.json` and `cmt_hash_004_empty_supersedes.json` produce **different** canonical commitment hashes: this inequality is the sole vector-level check that the *unset vs. empty* rule of Section 3, rule 3 is actually implemented, rather than `supersedes` being treated as absent whenever its sub-fields are empty.

## 12. Security Considerations

The domain-separation prefix `macp-commitment-hash/1:` (Section 4, step 3) exists to prevent a value computed under this construction from being confusable with a digest computed over the same or similar bytes under an unrelated protocol or an unrelated label version; implementations MUST NOT omit it, and MUST NOT reuse a preimage computed without it as if it were a canonical commitment hash.

The canonical commitment hash is a content digest, not a message authentication code or a digital signature: on its own, it establishes that a claimed `CommitmentPayload` projects to a specific value, not that the value was produced by an authorized party or delivered without tampering. Deployments requiring tamper evidence or sender authenticity MUST combine this construction with the transport security, authentication, and Envelope-signing mechanisms of RFC-MACP-0004; this RFC does not substitute for them.

Because this is a public content digest rather than a keyed value, comparisons against a claimed `commitment_hash` need not be constant-time in the way a MAC or signature comparison would; SHA-256's second-preimage and collision resistance assumptions [FIPS 180-4] are the load-bearing security property here, not comparison timing.

The frozen field set (Section 5) and the RFC 8785 subset restricted to strings, one boolean, and one nested object (Section 4) are correctness properties that keep independent implementations aligned; they are not, by themselves, security boundaries. An implementation that reintroduces general JCS number or array handling on a conforming `CommitmentPayload` projection does not create a divergence, because no number or array is reachable in a well-formed projection under Section 3 — but an implementation that fails to enforce the frozen field set of Section 5 (for example, by silently including or excluding a field) produces a value that is not a canonical commitment hash at all, and MUST NOT be presented to a counterparty as one.
