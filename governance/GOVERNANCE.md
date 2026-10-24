
# Governance Model

MACP is maintained as an open protocol specification.

## Maintainers

Maintainers are responsible for:

- Reviewing and merging pull requests
- Protecting protocol invariants
- Managing releases
- Maintaining registry consistency

## Decision Process

- Clarifications: Maintainer approval
- Backward-compatible additions: Maintainer consensus
- Breaking changes: Formal RFC process + major version bump

## RFC Lifecycle

Every RFC's header carries a `**Version:**` (a semantic version with a `-draft` suffix) and a `**Status:**` of `Community Standards Track`. That status names a track, not a lifecycle stage.

There is currently **no promotion ladder**. This repository defines no Draft → Review → Accepted → Final stages, no criteria for advancing an RFC between them, and no gate beyond [CONTRIBUTING.md](../CONTRIBUTING.md)'s community consensus. Every RFC should be read as draft-quality. The README's [Standards posture](../README.md#standards-posture) section and its version census say the same thing, and if the two documents ever disagree, the README is authoritative.

A ladder will be defined here, with entry criteria for each stage, before any RFC drops its `-draft` suffix.

## Registry Authority

The project maintains the registries in [`registries/`](../registries/README.md): modes, error codes, media types, capabilities, transports, policies and the commitment-hash label.

Experimental identifiers SHOULD use reverse-domain notation.
