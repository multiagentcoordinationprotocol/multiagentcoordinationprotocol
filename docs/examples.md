# MACP Examples

> **Status:** Non-normative (explanatory). In case of conflict, [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) is authoritative.

This repository includes illustrative transcripts for each standards-track mode and for policy-governed sessions.

## Available example transcripts

| File | Mode | What it shows |
|------|------|---------------|
| [`examples/decision-mode-session.json`](../examples/decision-mode-session.json) | `macp.mode.decision.v1` | initialization, `SessionStart`, proposal, evaluations, objection, votes, and terminal `Commitment` |
| [`examples/proposal-mode-session.json`](../examples/proposal-mode-session.json) | `macp.mode.proposal.v1` | offer, counteroffer, dual acceptance, and bound agreement |
| [`examples/task-mode-session.json`](../examples/task-mode-session.json) | `macp.mode.task.v1` | bounded delegation, progress, completion, and bound task outcome |
| [`examples/handoff-mode-session.json`](../examples/handoff-mode-session.json) | `macp.mode.handoff.v1` | responsibility transfer with context handoff and acceptance |
| [`examples/quorum-mode-session.json`](../examples/quorum-mode-session.json) | `macp.mode.quorum.v1` | threshold approval leading to a final commitment |
| [`examples/policy-decision-session.json`](../examples/policy-decision-session.json) | `macp.mode.decision.v1` | policy-governed Decision Mode with supermajority voting, quorum, and critical-severity veto (RFC-MACP-0012) |
| [`examples/policy-registration-exchange.json`](../examples/policy-registration-exchange.json) | N/A (gRPC exchange) | dynamic policy registration request and response (RFC-MACP-0012 Section 7) |

## Discovery, lifecycle, and runtime examples

Single-document examples that exercise non-transcript schemas:

| File | Schema | What it shows |
|------|--------|---------------|
| [`examples/discovery/agent_manifest.json`](../examples/discovery/agent_manifest.json) | [`macp-agent-manifest.schema.json`](../schemas/json/macp-agent-manifest.schema.json) | agent identity, supported modes, transport endpoints |
| [`examples/discovery/mode_descriptor.json`](../examples/discovery/mode_descriptor.json) | [`macp-mode-descriptor.schema.json`](../schemas/json/macp-mode-descriptor.schema.json) | mode advertisement with message types and schema URIs |
| [`examples/discovery/policy_descriptor.json`](../examples/discovery/policy_descriptor.json) | [`macp-policy-descriptor.schema.json`](../schemas/json/macp-policy-descriptor.schema.json) | governance policy advertisement (RFC-MACP-0012) |
| [`examples/discovery/session_metadata.json`](../examples/discovery/session_metadata.json) | [`macp-session-metadata.schema.json`](../schemas/json/macp-session-metadata.schema.json) | `SessionMetadata` returned by `GetSession` |
| [`examples/discovery/session_lifecycle_event.json`](../examples/discovery/session_lifecycle_event.json) | [`macp-session-lifecycle-event.schema.json`](../schemas/json/macp-session-lifecycle-event.schema.json) | `SessionLifecycleEvent` emitted by `WatchSessions` |
| [`examples/discovery/run_descriptor.json`](../examples/discovery/run_descriptor.json) | [`macp-run-descriptor.schema.json`](../schemas/json/macp-run-descriptor.schema.json) | scenario-agnostic run descriptor for a control-plane `POST /runs` |
| [`examples/discovery/agent_bootstrap.json`](../examples/discovery/agent_bootstrap.json) | [`macp-agent-bootstrap.schema.json`](../schemas/json/macp-agent-bootstrap.schema.json) | bootstrap payload written to `MACP_BOOTSTRAP_FILE` before the initiator agent starts |

## Example shape

Each transcript is an ordered JSON document with:

- top-level metadata such as `description`, `protocol_version`, `mode`, and `session_id`,
- an ordered `messages` array containing full Envelope objects in replay order,
- envelopes and initialization payloads written in replay order.

The ordering of the `messages` array is the replay order.

> **Note:** The policy-governed examples (`policy-decision-session.json`, `policy-registration-exchange.json`) use a simplified `transcript` array with sequence numbers (`seq`) and condensed message representations. This format is intended to illustrate governance evaluation flow rather than serve as a wire-format reference. For canonical Envelope structure, refer to the standard mode transcripts.

## What the examples demonstrate

Across the transcripts, the examples demonstrate:

- explicit initialization and capability negotiation,
- explicit `SessionStart`,
- session-scoped mode messages,
- version binding suitable for replay,
- a terminal `Commitment` that resolves the Session,
- policy resolution, governance evaluation, and deterministic commitment decisions (RFC-MACP-0012).

The important property is not the specific business scenario in each example. It is that every bound coordination event exists as a bounded transcript with a start, a lifecycle, and a terminal message.
