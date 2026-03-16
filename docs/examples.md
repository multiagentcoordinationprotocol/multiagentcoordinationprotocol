# MACP Examples

> **Status:** Non-normative (explanatory). In case of conflict, [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) is authoritative.

This repository now includes one illustrative transcript for each standards-track mode in the main repo.

## Available example transcripts

| File | Mode | What it shows |
|------|------|---------------|
| [`examples/decision-mode-session.json`](../examples/decision-mode-session.json) | `macp.mode.decision.v1` | initialization, `SessionStart`, proposal submission, evaluations, and terminal `Commitment` |
| [`examples/proposal-mode-session.json`](../examples/proposal-mode-session.json) | `macp.mode.proposal.v1` | offer, counteroffer, dual acceptance, and bound agreement |
| [`examples/task-mode-session.json`](../examples/task-mode-session.json) | `macp.mode.task.v1` | bounded delegation, progress, completion, and bound task outcome |
| [`examples/handoff-mode-session.json`](../examples/handoff-mode-session.json) | `macp.mode.handoff.v1` | responsibility transfer with context handoff and acceptance |
| [`examples/quorum-mode-session.json`](../examples/quorum-mode-session.json) | `macp.mode.quorum.v1` | threshold approval leading to a final commitment |

## Example shape

Each transcript is an ordered JSON document with:

- top-level metadata such as `description`, `protocol_version`, `mode`, and `session_id`,
- an ordered `messages` array,
- envelopes and initialization payloads written in replay order.

The ordering of the `messages` array is the replay order.

## What the examples demonstrate

Across the five transcripts, the examples demonstrate:

- explicit initialization and capability negotiation,
- explicit `SessionStart`,
- session-scoped mode messages,
- version binding suitable for replay,
- a terminal `Commitment` that resolves the Session.

The important property is not the specific business scenario in each example. It is that every bound coordination event exists as a bounded transcript with a start, a lifecycle, and a terminal message.
