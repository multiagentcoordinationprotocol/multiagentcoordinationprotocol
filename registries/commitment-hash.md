# MACP Commitment Hash Registry

Defines the labeled hashing projections used to compute `CommitmentRef.commitment_hash`
(the canonical commitment hash — see [RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md)).

## Identifier format

Labels use the form:

`macp-commitment-hash/<N>`

`<N>` is the integer label version. Exactly one label is current for a given MACP protocol
MINOR version (RFC-MACP-0013 §7). A new label is minted — the integer bumps — whenever the
frozen field set a label covers changes; for example, adding a field to `CommitmentPayload`
requires a bump from `macp-commitment-hash/1` to `macp-commitment-hash/2` rather than being
folded silently into the existing label (RFC-MACP-0013 §5). A label bump is itself a MACP
protocol MINOR change and MUST be advertised via `registries/capabilities.md`.

## Standard Labels

| Identifier | Description | Status | Reference |
|------------|-------------|--------|-----------|
| `macp-commitment-hash/1` | Domain-separated SHA-256 over the JCS canonicalization of the frozen nine-field CommitmentPayload projection | provisional | [RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md) |

## Not defined by this registry

This registry lists only labels for `CommitmentRef.commitment_hash`. `session_hash` and
every other digest referenced informally elsewhere in the MACP family (for example,
RFC-MACP-0003 §6's "signed Envelopes, hash-chained session logs, final session hashes
embedded in terminal records") are **not** defined by this registry and are not part of the
`macp-commitment-hash/<N>` namespace. Their construction remains implementation-defined
(RFC-MACP-0013 §10).
