# MACP Examples

> **Status:** Non-normative (explanatory). In case of conflict, [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) is authoritative.

This repository includes illustrative transcripts for each standards-track mode and for policy-governed sessions.

## Available example transcripts

| File | Mode | What it shows |
|------|------|---------------|
| [`examples/decision-mode-session.json`](../examples/decision-mode-session.json) | `macp.mode.decision.v1` | initialization, `SessionStart`, proposal submission, evaluations, and terminal `Commitment` |
| [`examples/proposal-mode-session.json`](../examples/proposal-mode-session.json) | `macp.mode.proposal.v1` | offer, counteroffer, dual acceptance, and bound agreement |
| [`examples/task-mode-session.json`](../examples/task-mode-session.json) | `macp.mode.task.v1` | bounded delegation, progress, completion, and bound task outcome |
| [`examples/handoff-mode-session.json`](../examples/handoff-mode-session.json) | `macp.mode.handoff.v1` | responsibility transfer with context handoff and acceptance |
| [`examples/quorum-mode-session.json`](../examples/quorum-mode-session.json) | `macp.mode.quorum.v1` | threshold approval leading to a final commitment |
| [`examples/policy-decision-session.json`](../examples/policy-decision-session.json) | `macp.mode.decision.v1` | policy-governed Decision Mode with supermajority voting, quorum, and critical-severity veto (RFC-MACP-0012) |
| [`examples/policy-registration-exchange.json`](../examples/policy-registration-exchange.json) | N/A (gRPC exchange) | dynamic policy registration request and response (RFC-MACP-0012 Section 7) |

## Example shape

Each transcript is an ordered JSON document with:

- top-level metadata such as `description`, `protocol_version`, `mode`, and `session_id`,
- an ordered `messages` array,
- envelopes and initialization payloads written in replay order.

The ordering of the `messages` array is the replay order.

## What the examples demonstrate

Across the transcripts, the examples demonstrate:

- explicit initialization and capability negotiation,
- explicit `SessionStart`,
- session-scoped mode messages,
- version binding suitable for replay,
- a terminal `Commitment` that resolves the Session,
- policy resolution, governance evaluation, and deterministic commitment decisions (RFC-MACP-0012).

The important property is not the specific business scenario in each example. It is that every bound coordination event exists as a bounded transcript with a start, a lifecycle, and a terminal message.
