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

### 2.1 Authority Matrix

| Message Type | Authorized Sender |
|-------------|-------------------|
| `TaskRequest` | Session initiator (requester) |
| `TaskAccept` | Requested assignee, or any eligible participant if `requested_assignee` is empty |
| `TaskReject` | Requested assignee, or any eligible participant if `requested_assignee` is empty |
| `TaskUpdate` | Active assignee only |
| `TaskComplete` | Active assignee only |
| `TaskFail` | Active assignee only |
| `Commitment` | Session initiator (default) or policy-designated authority |

Runtimes MUST reject messages from senders not authorized per this matrix.

## 3. SessionStart requirements

A Task Mode Session MUST bind:

- `participants` - requester and eligible assignee participants,
- `mode_version` - task-mode semantic profile,
- `configuration_version` - execution profile,
- `policy_version` — governance or authorization profile (MAY be empty; when empty, the runtime resolves to `policy.default` per RFC-MACP-0012 Section 5),
- `ttl_ms` - task deadline,
- `context` - optional task context and constraints.

Base Task Mode v1 assumes exactly one task request per Session.

## 4. Message types

Task Mode defines the following mode-specific message types:

- **TaskRequest** - opens the delegated task.
- **TaskAccept** - assignee accepts responsibility.
- **TaskReject** - assignee declines responsibility.
- **TaskUpdate** - non-terminal progress or status update. `TaskUpdate` does not carry an explicit `assignee` field. The runtime validates authorship via the Envelope `sender`, which MUST match the active assignee. This differs from `TaskComplete` and `TaskFail`, which redundantly include `assignee` in the payload for auditability.
- **TaskComplete** - assignee reports successful completion.
- **TaskFail** - assignee reports a bounded failure.
- **Commitment** - authoritative terminal outcome.

## 5. Validation rules

Implementations MUST enforce the following:

1. A Task Mode v1 Session MUST accept at most one `TaskRequest`.
2. `TaskAccept` or `TaskReject` MUST come from the requested assignee, or from an eligible declared participant if `requested_assignee` is empty.
3. Only one assignee may become active for the Session in base v1.
3a. The first accepted `TaskAccept` from any eligible participant designates that participant as the active assignee. Subsequent `TaskAccept` messages for the same session MUST be rejected if an active assignee is already designated.
3b. A participant who has sent `TaskAccept` MUST NOT later send `TaskReject` for the same task in base v1. `TaskAccept` is irrevocable unless policy explicitly permits reassignment.
3c. When policy sets `allow_reassignment_on_reject: true` and the active assignee sends `TaskReject`, the session returns to the pre-assignment state. Other eligible participants MAY then send `TaskAccept` for the same `task_id`. No additional `TaskRequest` is needed; the original request remains active.
4. `TaskUpdate`, `TaskComplete`, and `TaskFail` MUST come from the active assignee.
5. `TaskComplete` and `TaskFail` do not resolve the Session on their own. They make the Session eligible for `Commitment` by the requester or policy authority.

## 6. Terminal semantics

Task Mode resolves only when an authorized `Commitment` is accepted.

Implementations SHOULD use `CommitmentPayload.action` values that make the outcome explicit, for example:

- `task.completed`
- `task.failed`

The `Commitment` SHOULD bind the relevant task identifier and the versions that governed execution.

Task Mode allows both positive and negative committed outcomes (`task.completed` and `task.failed`). `CommitmentPayload.outcome_positive` MUST be set explicitly on all Task Mode commitments.

### 6.1 Governance Policy

Task sessions MAY be governed by declarative policies that constrain assignment rules, completion requirements, and commitment authority. See [RFC-MACP-0012](RFC-MACP-0012-policy.md) for the governance policy framework and `schemas/json/policy/task-rules.schema.json` for the Task Mode rule schema.

## 7. Determinism class

Task Mode claims **structural-only** determinism by default.

The coordination transcript is replay-safe, but task execution may depend on external tools, mutable inputs, or side effects outside the MACP runtime boundary. A deployment MAY define stricter profiles, but those are not part of base Task Mode v1.

## 8. Security considerations

Implementations MUST address all of the following:

- authenticate requester and assignee identities,
- ensure only authorized assignees accept or complete tasks,
- protect sensitive task inputs and outputs,
- define idempotency keys for any external side effects triggered by task execution. The normative idempotency key for task outcomes is `task_id + assignee + first_accepted_completion_message_id` (where the completion message is `TaskComplete` or `TaskFail`). Retransmissions with the same key MUST NOT re-execute side effects.
- reject forged completions and failures from non-assignees.

## 9. Canonical schemas and examples

Canonical schemas:

- `schemas/proto/macp/modes/task/v1/task.proto`
- `schemas/modes/task.proto`

Example transcript:

- `examples/task-mode-session.json`
