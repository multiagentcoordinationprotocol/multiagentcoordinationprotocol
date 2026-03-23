# RFC-MACP-0009
# Multi-Agent Coordination Protocol (MACP) - Task Mode

**Document:** RFC-MACP-0009
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0002

## Abstract

This document defines `macp.mode.task.v1`, the standards-track MACP primitive for bounded task delegation. Task Mode lets an orchestrator assign one task inside one Session, record assignee responses and progress, and terminate with a single authoritative `Commitment` that binds success or failure.

## 1. Purpose

Task Mode is the basic delegation primitive for multi-agent execution. It is intended for one bounded task per Session, not for open-ended job queues or workflow graphs.

## 2. Identifier and participant model

- **Mode identifier:** `macp.mode.task.v1`
- **Participant model:** `orchestrated`

The session initiator or a policy-defined coordinator is the requester and default `Commitment` authority.

## 3. SessionStart requirements

A Task Mode Session MUST bind:

- `participants` - requester and eligible assignee participants,
- `mode_version` - task-mode semantic profile,
- `configuration_version` - execution profile,
- `policy_version` - governance or authorization profile,
- `ttl_ms` - task deadline,
- `context` - optional task context and constraints.

Base Task Mode v1 assumes exactly one task request per Session.

## 4. Message types

Task Mode defines the following mode-specific message types:

- **TaskRequest** - opens the delegated task.
- **TaskAccept** - assignee accepts responsibility.
- **TaskReject** - assignee declines responsibility.
- **TaskUpdate** - non-terminal progress or status update.
- **TaskComplete** - assignee reports successful completion.
- **TaskFail** - assignee reports a bounded failure.
- **Commitment** - authoritative terminal outcome.

## 5. Validation rules

Implementations MUST enforce the following:

1. A Task Mode v1 Session MUST accept at most one `TaskRequest`.
2. `TaskAccept` or `TaskReject` MUST come from the requested assignee, or from an eligible declared participant if `requested_assignee` is empty.
3. Only one assignee may become active for the Session in base v1.
4. `TaskUpdate`, `TaskComplete`, and `TaskFail` MUST come from the active assignee.
5. `TaskComplete` and `TaskFail` do not resolve the Session on their own. They make the Session eligible for `Commitment` by the requester or policy authority.

## 6. Terminal semantics

Task Mode resolves only when an authorized `Commitment` is accepted.

Implementations SHOULD use `CommitmentPayload.action` values that make the outcome explicit, for example:

- `task.completed`
- `task.failed`

The commitment SHOULD bind the relevant task identifier and the versions that governed execution.

## 7. Determinism class

Task Mode claims **structural-only** determinism by default.

The coordination transcript is replay-safe, but task execution may depend on external tools, mutable inputs, or side effects outside the MACP runtime boundary. A deployment MAY define stricter profiles, but those are not part of base Task Mode v1.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate requester and assignee identities,
- ensure only authorized assignees accept or complete tasks,
- protect sensitive task inputs and outputs,
- define idempotency keys for any external side effects triggered by task execution,
- reject forged completions and failures from non-assignees.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/task/v1/task.proto`
- `schemas/modes/task.proto`

Example transcript:

- `examples/task-mode-session.json`
