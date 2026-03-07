# MACP Runtime

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0001 Core](../rfcs/RFC-MACP-0001-core.md)

A MACP Runtime is the system that turns the protocol from a specification into an enforceable boundary. Its purpose is not to decide what a session means. Its purpose is to decide, authoritatively and durably, which messages were accepted, in what order, under what lifecycle state, and by which versioned execution context.

## Runtime responsibilities

A compliant runtime performs a small number of structurally critical jobs:

1. initialize connections and negotiate capabilities,  
2. authenticate and authorize senders,  
3. validate Envelopes,  
4. assign accepted messages an authoritative order within a session,  
5. persist accepted history append-only,  
6. execute lifecycle transitions monotonically,  
7. dispatch accepted messages to the Mode engine.

## The admission pipeline

Admission is the most important runtime act. It is the moment a message becomes part of history.

```mermaid
flowchart LR
  In[Incoming Envelope] --> Auth[AuthN / AuthZ]
  Auth --> Validate[Envelope Validation]
  Validate --> Dedup[Deduplication by message_id]
  Dedup --> Session[Session Owner / State Check]
  Session --> Append[Append to Session Log]
  Append --> Dispatch[Mode Dispatch]
```

If a message is not appended, it did not happen from the protocol’s perspective.

## Session ownership

Each OPEN session must have exactly one ordering authority at any instant. In a distributed deployment, this usually means sharding by `session_id` and assigning ownership through leases or partition leadership.

```mermaid
flowchart TB
  R[Edge Router] -->|hash(session_id)| O1[Session Owner A]
  R -->|hash(session_id)| O2[Session Owner B]
  O1 --> L1[(Ledger Partition A)]
  O2 --> L2[(Ledger Partition B)]
```

The owner is responsible for acceptance order, lifecycle transitions, and deterministic rejection of invalid or late messages.

## Mode execution

Mode execution SHOULD be treated as a pure function over accepted history whenever possible. The runtime does not need to understand business semantics, but it does need to know when the Mode says a terminal condition has been met.

## Recovery and rehydration

Because accepted history is append-only, failed owners can recover by replaying the session log and reconstructing in-memory state. Snapshots are an optimization, not an authority.

## Cancellation

Cancellation transitions a session from OPEN to EXPIRED without rewriting history. Late-arriving messages are rejected because the lifecycle state is no longer OPEN.
