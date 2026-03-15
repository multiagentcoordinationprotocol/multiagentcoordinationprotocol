# MACP Coordination Modes

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md)

## Overview

**Coordination Modes** define the semantic behavior of multi-agent coordination within MACP's structural constraints. MACP Core enforces structure - sessions, isolation, lifecycle, idempotent acceptance. Modes define meaning - what messages are valid, how state evolves, and when a session becomes eligible for `Commitment`.

## What belongs in the main repo

The main MACP RFC repo should contain only coordination primitives that are broadly reusable across runtimes. In practice, that means a small standard mode set:

| Mode | Use it when you need | Participant model | Determinism | RFC |
|------|----------------------|-------------------|-------------|-----|
| `macp.mode.decision.v1` | structured choice among proposals | declared | semantic-deterministic | [RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md) |
| `macp.mode.proposal.v1` | offer / counteroffer negotiation | peer | semantic-deterministic | [RFC-MACP-0008](../rfcs/RFC-MACP-0008-proposal-mode.md) |
| `macp.mode.task.v1` | bounded task delegation | orchestrated | structural-only | [RFC-MACP-0009](../rfcs/RFC-MACP-0009-task-mode.md) |
| `macp.mode.handoff.v1` | responsibility transfer | delegated | context-frozen | [RFC-MACP-0010](../rfcs/RFC-MACP-0010-handoff-mode.md) |
| `macp.mode.quorum.v1` | threshold approval or rejection | quorum | semantic-deterministic | [RFC-MACP-0011](../rfcs/RFC-MACP-0011-quorum-mode.md) |

Everything else - debate, review, critique, pipeline, swarm, auction, marketplace, and organization-specific workflows - should stay in incubator or vendor repos until it proves broad interoperable demand.

## Why these five modes

These modes map closely to recurring distributed coordination primitives:

- **Decision** - choose one option from multiple possibilities.
- **Proposal** - negotiate and refine terms.
- **Task** - delegate one bounded job.
- **Handoff** - transfer ownership or responsibility.
- **Quorum** - satisfy an approval threshold.

They are primitive enough to be reused across products and domains, but concrete enough to produce interoperable transcripts.

## Why Broadcast is not a main-repo mode

MACP already has **Signals** for ambient, non-binding dissemination. A broadcast-style session mode usually fights the core MACP model because Sessions are supposed to be bounded and convergent. If you need one-to-many notifications, prefer Signals or an external pub/sub system. If you later discover a bounded acknowledgment workflow that truly needs Session semantics, that mode can begin in an incubator repo.

## Common design rules for standards-track modes

Standards-track modes in the main repo should all do the following:

1. Bind the participant set and version surface clearly at `SessionStart`.
2. Define explicit validation rules for message ordering and references.
3. State exactly who may emit `Commitment`.
4. Declare one determinism class.
5. Provide canonical schemas and at least one transcript.
6. Avoid embedding product-specific workflows into the base mode.

## Quick selection guide

Use this rule of thumb:

- Need to compare multiple options and justify one outcome? Use **Decision**.
- Need offer / counteroffer semantics? Use **Proposal**.
- Need one agent to do bounded work for another? Use **Task**.
- Need to transfer ownership or responsibility? Use **Handoff**.
- Need N-of-M approval for one action? Use **Quorum**.

## Standard-mode summaries

### Decision Mode

Decision Mode uses `Proposal`, `Evaluation`, `Objection`, `Vote`, and a final `Commitment`. The participant set is declared up front. The mode standardizes transcript semantics, while policy/configuration decide the exact decision algorithm.

### Proposal Mode

Proposal Mode focuses on `Proposal`, `CounterProposal`, `Accept`, `Reject`, and `Withdraw`. It is lighter than Decision Mode and works best for negotiation where parties refine terms until they can commit one accepted proposal.

### Task Mode

Task Mode is for one bounded delegated task per session. `TaskComplete` and `TaskFail` report outcome, but only `Commitment` binds the authoritative final result.

### Handoff Mode

Handoff Mode is for transfer of responsibility, not just work execution. The key messages are `HandoffOffer`, `HandoffContext`, `HandoffAccept`, and `HandoffDecline`, followed by a binding `Commitment`.

### Quorum Mode

Quorum Mode is the narrowest of the five. It covers one approval request and a threshold of approvals, rejections, or abstentions that make the request eligible for a final `Commitment`.

## Schemas and examples

Canonical schemas live under `schemas/proto/macp/modes/`.

Human-friendly entrypoints live under `schemas/modes/`.

Example transcripts live under `examples/`:

- `decision-mode-session.json`
- `proposal-mode-session.json`
- `task-mode-session.json`
- `handoff-mode-session.json`
- `quorum-mode-session.json`
