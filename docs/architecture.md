# MACP Architecture

> **Reference:** [RFC-MACP-0001 Section 4](../rfcs/RFC-MACP-0001.md)

## Overview

The Multi-Agent Coordination Protocol (MACP) provides a **structural coordination kernel** for ecosystems of autonomous agents. MACP's architecture is built on one strict invariant:

**Binding, convergent coordination MUST occur inside explicit, bounded Coordination Sessions.**

All other interaction is treated as **ambient** and non-binding, carried via Signals.

## Design Philosophy

MACP intentionally separates **structure** from **semantics**:

- **MACP Core** enforces structural invariants: explicit sessions, monotonic lifecycle, isolation, append-only history, and idempotent acceptance
- **Coordination Modes** define semantic behaviors: arbitration algorithms, decision theory, governance policy, domain logic, and tool execution semantics

This separation allows MACP to support diverse coordination patterns while maintaining strong structural guarantees.

## Two-Plane Architecture

MACP separates interaction into two distinct planes:

### Ambient Plane: Signals

Agents MAY continuously exchange **Signals** for:
- Telemetry and observations
- Partial evaluations
- Local state announcements
- Correlation and monitoring

**Signals are informational, correlate-able, and observable, but MUST NOT:**
- Start a session
- Mutate a session state
- Change session participants
- Resolve or expire a session

**Example Use Cases:**
- "Agent X observed high latency"
- "Agent Y completed local analysis"
- "System metric Z crossed threshold"

### Coordination Plane: Sessions

A **Coordination Session** is created only by `SessionStart`. Within a session:

- Messages are scoped by `session_id`
- Ordering is preserved within the session stream
- Messages are validated against the session lifecycle
- History is recorded append-only
- **All binding convergence MUST occur here**

**Example Use Cases:**
- Multi-agent decision making
- Quorum-based approvals
- Negotiation and consensus
- Coordinated tool execution

## Core Architectural Components

### 1. Envelope

Every MACP message is wrapped in an **Envelope** that provides:

- **Protocol versioning** (`macp_version`)
- **Session scoping** (`session_id`)
- **Sender identity** (`sender`)
- **Message identity** for idempotency (`message_id`)
- **Timestamp** for observability (`timestamp_unix_ms`)
- **Opaque payload bytes** (Core- or Mode-defined)

```protobuf
message Envelope {
  string macp_version = 1;        // e.g. "1.0"
  string mode = 2;                // e.g. "macp.mode.decision.v1"
  string message_type = 3;        // e.g. "SessionStart", "Signal", "Commitment"
  string message_id = 4;          // globally unique
  string session_id = 5;          // empty for Signals
  string sender = 6;              // agent identifier
  int64  timestamp_unix_ms = 7;   // informational
  bytes  payload = 8;             // serialized payload
}
```

### 2. MACP Runtime

The **MACP Runtime** is the logical system responsible for:

- Enforcing session state transitions
- Isolation guarantees between sessions
- Message ordering and deduplication
- Structural validation
- Idempotency enforcement

The runtime may be centralized or distributed, but its behavior MUST be logically consistent with the specification.

### 3. Coordination Session

A Coordination Session is a bounded context with properties:

- **Unique `session_id`**: Cryptographically strong identifier
- **Declared `mode`**: Defines coordination semantics
- **Declared participants**: Mode-defined interpretation
- **Bounded TTL**: Session lifetime limit
- **Append-only message log**: Immutable history
- **Terminal outcome**: `RESOLVED` or `EXPIRED`

### 4. Coordination Mode

A **Mode** defines the coordination semantics within MACP's structural constraints:

- Allowed message types
- Participant rules
- Termination conditions
- Determinism claims
- Commitment semantics
- Mode-specific payload schemas

**Modes MUST NOT violate MACP Core invariants.**

## Session-Scoped Communication Rule

Within an active Coordination Session, compliant agents **MUST NOT** bypass MACP by directly invoking one another to advance session binding outcomes.

- All session-scoped coordination messages MUST flow through the MACP Runtime
- Outside active sessions, agents MAY communicate directly or via other protocols, subject to local policy

**Rationale:** This preserves replayability, isolation, and enforceable boundaries.

## Architectural Guarantees

MACP provides the following structural guarantees:

### 1. Explicit Coordination Boundaries

Coordination MUST start via `SessionStart`. There is no implicit coordination.

### 2. Isolation

Sessions are isolated from one another. Cross-session ordering is not guaranteed.

### 3. Monotonic Lifecycle

Sessions transition monotonically: `OPEN → (RESOLVED | EXPIRED)`.

### 4. Append-only History

Accepted session messages are immutable and recorded append-only.

### 5. Replay Integrity

Replaying the same accepted Envelope sequence under the same Mode and configuration versions MUST reproduce the same state transitions.

### 6. Transport Independence

MACP defines a canonical envelope and transport requirements; it does not require a single deployment topology.

## Deployment Topologies

MACP is compatible with many topologies:

- **One-to-many**: Single orchestrator with multiple agents
- **Many-to-many**: Peer-to-peer coordination
- **Quorum**: Subset agreement patterns
- **Delegated evaluation**: Agent delegates to specialists
- **Hierarchical orchestration**: Nested coordination structures

## Message Flow Example

```
┌─────────────┐                  ┌──────────────┐
│   Agent A   │                  │ MACP Runtime │
└──────┬──────┘                  └──────┬───────┘
       │                                │
       │  1. SessionStart               │
       ├───────────────────────────────>│
       │                                │ Create Session
       │  2. Ack (session_id)           │ State: OPEN
       │<───────────────────────────────┤
       │                                │
       │  3. Proposal (Mode message)    │
       ├───────────────────────────────>│
       │                                │ Validate, Append
       │  4. Ack                         │
       │<───────────────────────────────┤
       │                                │
       │  5. Commitment (terminal)      │
       ├───────────────────────────────>│
       │                                │ Transition to RESOLVED
       │  6. Ack (state=RESOLVED)       │
       │<───────────────────────────────┤
```

## Relationship to Other Protocols

### Model Context Protocol (MCP)

- **MCP** standardizes how AI applications connect to external context and capabilities using JSON-RPC
- **MACP** coordinates when and whether agents are allowed to use those capabilities
- **Integration**: A Mode may coordinate MCP tool invocations

### Agent Communication Protocol (ACP)

- **ACP** demonstrates practical patterns for agent discovery, manifest metadata, and REST + streaming
- **MACP** borrows manifest and discovery concepts while focusing on session-bounded convergence
- **Difference**: MACP emphasizes structural coordination, ACP emphasizes run execution APIs

## Extensibility

Future specifications MAY define:

- Nested sessions and session graphs
- Quorum / voting semantics
- Routing federation
- Trust and weighting mechanisms
- Cryptographic commitments
- Cross-session references

**All extensions MUST preserve MACP Core invariants.**

## Summary

MACP's architecture provides a minimal, structural foundation for multi-agent coordination:

- **Two planes**: Ambient (Signals) and Coordinated (Sessions)
- **Clear boundaries**: Explicit sessions with bounded lifetimes
- **Strong guarantees**: Isolation, monotonic lifecycle, replay integrity
- **Flexible semantics**: Modes define coordination behavior
- **Transport independence**: Multiple deployment topologies supported

This design addresses common failure modes in agent ecosystems: ambiguous authority, implicit negotiation loops, recursive dependencies, non-reproducible outcomes, and "infinite chat" failure modes.

## See Also

- [Lifecycle](lifecycle.md) - Session states and transitions
- [Security](security.md) - Security model and considerations
- [Modes](modes.md) - How to define coordination modes
- [Determinism](determinism.md) - Replay integrity guarantees
- [RFC-MACP-0001](../rfcs/RFC-MACP-0001.md) - Full specification
