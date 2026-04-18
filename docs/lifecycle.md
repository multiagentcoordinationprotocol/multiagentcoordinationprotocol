# MACP Session Lifecycle

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0001 Core](../rfcs/RFC-MACP-0001-core.md)

The MACP session lifecycle is a monotonic state machine. This is what turns coordination from emergent behavior into enforceable protocol state.

## Session states

- **OPEN** — session is active and accepting messages
- **RESOLVED** — session terminated via first accepted Mode-defined terminal message
- **EXPIRED** — session terminated due to TTL, cancellation, or deterministic runtime policy

No transition from RESOLVED or EXPIRED back to OPEN is permitted.

```mermaid
stateDiagram-v2
  [*] --> OPEN: SessionStart accepted
  OPEN --> RESOLVED: first accepted terminal message
  OPEN --> EXPIRED: TTL / CancelSession / deterministic runtime policy
  RESOLVED --> [*]
  EXPIRED --> [*]
```

## Admission rules for session-scoped messages

For any message with a non-empty `session_id`, the runtime MUST verify that:

1. the session exists,
2. the session is OPEN,
3. the sender is authorized,
4. the message is structurally valid,
5. the message is not a duplicate.

If any check fails, the message is rejected and does not enter history.

## Accepted-History Discipline

Only **accepted session-scoped** Envelopes become part of authoritative session history. Ambient Signals MAY be handled ephemerally and are not required to enter durable replay history unless a deployment opts into separate signal logging. Rejected Envelopes MUST NOT:

- be appended to accepted history,
- consume `message_id` deduplication slots,
- mutate session state.

All validation, authentication, authorization, deduplication, session-state checks, and Mode-specific structural validation MUST succeed before an Envelope is appended to accepted history.

## Cancellation Authority

The default cancellation authority is the session initiator. Deployments may extend this through policy, but cancellation always requires authentication and authorization.

## Terminal races

If multiple terminal messages are sent concurrently, the first one accepted into the session log determines the outcome. Later terminal messages are rejected because the session is no longer OPEN.

## Session Observation

Two RPCs provide programmatic session lifecycle observation:

- **`ListSessions`** — returns `SessionMetadata` for all known sessions. Use for initial sync. Advertised by `sessions.list_sessions`.
- **`WatchSessions`** — server-streaming RPC that emits `SessionLifecycleEvent` notifications (CREATED, RESOLVED, EXPIRED) in real time. Advertised by `sessions.watch_sessions`.

Control-planes and UIs typically call `ListSessions` on startup for a snapshot, then subscribe to `WatchSessions` for incremental updates. Events are ephemeral and not replayed.

## Session Context and Extensions

Sessions may carry optional context and extension metadata (see [RFC-MACP-0001 §7.4](../rfcs/RFC-MACP-0001-core.md)):

- **`context_id`** — an opaque string naming the structured context the session operates within (e.g., a content-addressed ID, a URI). The runtime preserves it but never interprets it.
- **`extensions`** — a map of protocol-keyed byte blocks for protocol-specific metadata (e.g., CTXM, AITP). The runtime preserves all entries but does not depend on them for core lifecycle.

Both are optional. A session with empty `context_id` and empty `extensions` behaves identically to one with both populated.
