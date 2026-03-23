# MACP Mode Registry

Coordination Modes define semantic coordination patterns within MACP Sessions.

## Identifier format

Standard identifiers use the form:

`macp.mode.<name>.v<version>`

Example:

`macp.mode.decision.v1`

## Standards-track modes in the main RFC repo

| Mode | Description | Participant model | Determinism | Status | Reference |
|------|-------------|-------------------|-------------|--------|-----------|
| `macp.mode.decision.v1` | Structured decision with proposals, evaluations, objections, votes, and one binding outcome | declared | semantic-deterministic | permanent | [RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md) |
| `macp.mode.proposal.v1` | Proposal and counterproposal negotiation | peer | semantic-deterministic | provisional | [RFC-MACP-0008](../rfcs/RFC-MACP-0008-proposal-mode.md) |
| `macp.mode.task.v1` | One bounded delegated task per Session | orchestrated | structural-only | provisional | [RFC-MACP-0009](../rfcs/RFC-MACP-0009-task-mode.md) |
| `macp.mode.handoff.v1` | Responsibility transfer across participants | delegated | context-frozen | provisional | [RFC-MACP-0010](../rfcs/RFC-MACP-0010-handoff-mode.md) |
| `macp.mode.quorum.v1` | Threshold approval or rejection for one bounded action | quorum | semantic-deterministic | provisional | [RFC-MACP-0011](../rfcs/RFC-MACP-0011-quorum-mode.md) |

## Main-repo boundary

The main MACP standards repo standardizes only foundational coordination primitives. The following kinds of modes SHOULD live in incubator or vendor repos unless they become widely interoperable:

- workflow recipes such as debate, review, critique, pipeline, and swarm patterns,
- highly domain-specific modes,
- fast-moving experimental coordination patterns,
- auction and marketplace modes that are still settling semantically,
- broadcast-style patterns that fit ambient Signals or external pub/sub better than bounded Sessions.

## Extension and experimental modes

Runtime-shipped built-in extensions SHOULD use the `ext.*` namespace:

`ext.<name>.v<major>`

Experimental or vendor-specific modes SHOULD use reverse-domain naming:

`com.example.mode.custom.v1`

Runtimes MAY implement additional non-standard modes, but those modes MUST be documented as non-standard and MUST NOT be presented as part of the standards-track set unless they are listed in this registry and backed by a main-repo RFC. `ListModes` SHOULD return only standards-track modes listed above; extension modes are discoverable through implementation-defined surfaces.
