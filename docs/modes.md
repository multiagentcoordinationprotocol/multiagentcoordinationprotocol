# MACP Coordination Modes

> **Reference:** [RFC-MACP-0002](../rfcs/RFC-MACP-0002-modes.md)

## Overview

**Coordination Modes** define the semantic behavior of multi-agent coordination within MACP's structural constraints. While MACP Core enforces structure (sessions, isolation, lifecycle), Modes define meaning (what messages are allowed, how decisions are made, what constitutes a terminal outcome).

## What is a Mode?

A **Mode** is a specification that defines:

1. **Allowed message types** beyond MACP Core types
2. **Participant rules** (who can send what messages)
3. **Termination conditions** (what message ends the session)
4. **Determinism claims** (is the outcome reproducible?)
5. **Commitment semantics** (what does a binding outcome mean?)
6. **Payload schemas** for Mode-specific messages

**Modes MUST NOT violate MACP Core invariants.**

## Mode Responsibilities vs. Core Responsibilities

| Concern | MACP Core | Mode |
|---------|-----------|------|
| Session creation | ✓ Enforces SessionStart | Defines when to create sessions |
| Session lifecycle | ✓ Enforces OPEN → RESOLVED/EXPIRED | Defines what triggers RESOLVED |
| Message validation | ✓ Validates Envelope structure | Validates payload semantics |
| Idempotency | ✓ Enforces message_id dedup | Handles semantic idempotency |
| Isolation | ✓ Enforces session boundaries | Respects boundaries |
| Ordering | ✓ Preserves within-session order | Defines message sequence rules |
| Authorization | ✓ Provides hooks | Defines participant rules |
| Determinism | ✓ Structural replay | Defines semantic determinism |

## Mode Naming Convention

Modes SHOULD use namespaced identifiers:

- **Pattern:** `macp.mode.<name>.<version>`
- **Example:** `macp.mode.decision.v1`
- **Experimental modes:** Use reverse-domain naming (e.g., `com.example.mode.custom.v1`)

## Core Message Types (Available to All Modes)

MACP Core provides these message types:

- `Signal`: Ambient, non-binding (mode typically `macp.core.signal.v1`)
- `SessionStart`: Creates a session
- `SessionCancel`: Runtime-emitted cancellation
- `Commitment`: Recommended terminal type (convention)
- `SessionEnd`: Alternative terminal type without commitment semantics

Modes MAY define additional message types.

## Defining a Mode

### 1. Mode Specification Document

Create a specification describing:

- Mode identifier and version
- Purpose and use cases
- Message types (beyond Core)
- Participant model
- Termination conditions
- Determinism claim
- Security considerations

**Example:** `macp-mode-decision-v1-spec.md`

### 2. Mode Descriptor (Recommended)

Expose a machine-readable Mode Descriptor:

```json
{
  "mode": "macp.mode.decision.v1",
  "mode_version": "1.0.0",
  "title": "Decision Mode",
  "description": "Collects proposals and produces a single binding Commitment.",
  "deterministic": true,
  "message_types": [
    "Proposal",
    "Vote",
    "Commitment"
  ],
  "terminal_message_types": [
    "Commitment"
  ],
  "participant_model": "declared",
  "schemas": {
    "Proposal": "https://example.org/schemas/mode/decision/proposal.json",
    "Vote": "https://example.org/schemas/mode/decision/vote.json",
    "Commitment": "https://example.org/schemas/mode/decision/commitment.json"
  }
}
```

### 3. Payload Schemas

Define Protobuf schemas for Mode-specific message payloads:

```protobuf
syntax = "proto3";

package macp.mode.decision.v1;

message ProposalPayload {
  string proposal_id = 1;
  string option = 2;
  string rationale = 3;
  bytes supporting_data = 4;
}

message VotePayload {
  string proposal_id = 1;
  string vote = 2;  // "approve", "reject", "abstain"
  string voter = 3;
  string reason = 4;
}
```

## Example Mode: Decision Mode

### Purpose

Coordinate a multi-agent decision with binding outcome.

### Message Flow

```
Orchestrator → SessionStart
              → Proposal (option A)
              → Proposal (option B)

Agent 1 → Vote (approve A)
Agent 2 → Vote (approve A)
Agent 3 → Vote (approve B)

Orchestrator → Commitment (selected: A)
              → Session RESOLVED
```

### Message Types

1. **Proposal**: Submit an option for consideration
2. **Vote**: Express preference for a proposal
3. **Commitment**: Binding decision

### Rules

- **Participants**: Declared in SessionStart
- **Proposal phase**: Any participant can submit proposals
- **Voting phase**: Each participant votes once
- **Termination**: Orchestrator emits Commitment after quorum reached
- **Deterministic**: Yes (given same votes, same outcome)

### Payload Schemas

See protobuf examples above.

## Example Mode: Quorum Approval

### Purpose

Require N-of-M agent approvals for an action.

### Message Flow

```
Initiator → SessionStart (action: "deploy-to-prod", quorum: 3-of-5)

Approver 1 → Approve
Approver 2 → Approve
Approver 3 → Approve

Runtime → Commitment (status: "approved")
         → Session RESOLVED
```

### Message Types

1. **Approve**: Agent approves the action
2. **Reject**: Agent rejects the action
3. **Commitment**: Outcome (approved/rejected)

### Rules

- **Participants**: Declared approvers in SessionStart
- **Quorum**: Defined in SessionStart `context` (e.g., 3-of-5)
- **Early termination**: If rejections exceed threshold, terminate with "rejected"
- **Deterministic**: Yes

## Example Mode: Negotiation

### Purpose

Iterative proposal refinement until consensus.

### Message Flow

```
Agent A → SessionStart
         → InitialProposal (terms: {...})

Agent B → CounterProposal (modified terms: {...})
Agent A → CounterProposal (further refinement: {...})

Agent B → Accept
Agent A → Accept

Runtime → Commitment (final terms: {...})
         → Session RESOLVED
```

### Message Types

1. **InitialProposal**: Starting point
2. **CounterProposal**: Modified terms
3. **Accept**: Accept current proposal
4. **Reject**: Reject and end negotiation
5. **Commitment**: Final agreed terms

### Rules

- **Participants**: Two agents (bilateral) or N agents (multilateral)
- **Termination**: All participants Accept, or any Reject
- **Deterministic**: Yes (given same sequence, same outcome)

## Implementing a Mode

### Step 1: Define Message Schemas

Create `.proto` files for your Mode payloads:

```protobuf
syntax = "proto3";
package macp.mode.mymode.v1;

message MyModePayload {
  string action = 1;
  bytes data = 2;
}
```

### Step 2: Implement Mode Logic

Implement the Mode's message processing logic:

```javascript
class MyMode {
  constructor(sessionConfig) {
    this.config = sessionConfig;
    this.state = { phase: "collecting" };
  }

  processMessage(envelope) {
    // Validate message type
    if (!this.isValidMessageType(envelope.message_type)) {
      throw new Error("INVALID_MESSAGE_TYPE");
    }

    // Validate sender authorization
    if (!this.isAuthorized(envelope.sender, envelope.message_type)) {
      throw new Error("FORBIDDEN");
    }

    // Process message
    switch (envelope.message_type) {
      case "Proposal":
        return this.handleProposal(envelope);
      case "Vote":
        return this.handleVote(envelope);
      case "Commitment":
        return this.handleCommitment(envelope);
      default:
        throw new Error("UNKNOWN_MESSAGE_TYPE");
    }
  }

  isTerminal(envelope) {
    return envelope.message_type === "Commitment";
  }

  // ... mode-specific logic
}
```

### Step 3: Register Mode with Runtime

Register your Mode with the MACP runtime:

```javascript
runtime.registerMode("macp.mode.mymode.v1", MyMode);
```

### Step 4: Test Mode Behavior

Write tests for:

- Valid message sequences
- Invalid message sequences (should reject)
- Participant authorization
- Termination conditions
- Determinism (replay tests)

```javascript
test('mode terminates on commitment', () => {
  let mode = new MyMode(config);
  let sessionStart = createSessionStart();
  let proposal = createProposal();
  let commitment = createCommitment();

  mode.processMessage(sessionStart);
  mode.processMessage(proposal);
  mode.processMessage(commitment);

  expect(mode.isTerminal(commitment)).toBe(true);
});
```

## Mode Design Patterns

### Pattern 1: Orchestrator-Led

- One agent (orchestrator) initiates and finalizes
- Other agents provide input
- **Example:** Decision mode, where orchestrator collects proposals and votes, then commits

### Pattern 2: Peer-to-Peer Consensus

- No central orchestrator
- All participants are equal
- Terminal condition: All approve
- **Example:** Multi-party contract signing

### Pattern 3: Quorum-Based

- Subset agreement sufficient
- N-of-M participants must agree
- **Example:** Multi-signature authorization

### Pattern 4: State Machine

- Session progresses through phases
- Messages valid only in certain phases
- **Example:** Auction (submit bids → reveal bids → select winner)

### Pattern 5: Delegated Evaluation

- Initiator delegates evaluation to specialists
- Specialists provide assessments
- Initiator synthesizes and commits
- **Example:** Risk assessment (security, finance, legal specialists)

## Mode Versioning

### Semantic Versioning for Modes

Use semantic versioning:

- **Major**: Breaking changes (incompatible with previous version)
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, no semantic changes

**Example:**
- `macp.mode.decision.v1` (major version 1)
- `macp.mode.decision.v2` (breaking changes from v1)

### Version Compatibility

- Agents MUST reject Modes they don't support
- Runtimes SHOULD negotiate Mode version during SessionStart admission control
- Include `mode_version` in SessionStartPayload for explicit versioning

### Deprecation

When deprecating a Mode version:

1. Announce deprecation timeline
2. Provide migration guide
3. Support old version during transition period
4. Eventually reject SessionStart for deprecated version

## Security Considerations for Modes

### Participant Validation

Define who can:

- Initiate sessions
- Send specific message types
- Emit Commitment

**Example:** Only designated approvers can Vote in approval mode.

### Payload Validation

Validate Mode-specific payloads:

- Required fields present
- Data types correct
- Business logic constraints met

**Example:** Vote must be one of ["approve", "reject", "abstain"]

### Authority Scope

Define the scope of authority for Commitments:

```json
{
  "commitment_id": "...",
  "action": "deploy-to-prod",
  "authority_scope": "infrastructure",
  "conditions": ["quorum-met", "all-approvers-authenticated"]
}
```

### Sensitive Data

If payloads contain sensitive data:

- Encrypt at application layer before placing in Envelope
- Use separate encryption keys per session
- Consider using `payload_b64` for opaque encrypted payloads

## Best Practices

### 1. Keep Modes Simple

- One Mode, one coordination pattern
- Avoid feature creep
- Compose simple Modes rather than building monolithic ones

### 2. Make Modes Deterministic When Possible

- Easier to test
- Enables replay
- Supports audit and compliance

### 3. Version Explicitly

- Include Mode version in Descriptor
- Include mode_version in SessionStart
- Include version in Commitment for attribution

### 4. Document Participant Model

- Who can participate?
- Who can send which messages?
- Who can emit Commitment?

### 5. Provide Example Sessions

Include example message sequences in Mode documentation:

```json
// See examples/decision-mode-session.json for a full transcript
[
  { "message_type": "SessionStart", ...},
  { "message_type": "Proposal", ...},
  { "message_type": "Vote", ...},
  { "message_type": "Commitment", ...}
]
```

### 6. Test Edge Cases

- What if no votes are cast?
- What if session expires before Commitment?
- What if multiple Commitments are sent (should reject second)?

## Mode Registry (Future)

Future MACP specifications MAY define a Mode Registry:

- Catalog of standard Modes
- Mode schema repository
- Version compatibility matrix
- Community-contributed Modes

## See Also

- [Architecture](architecture.md) - Mode's role in MACP architecture
- [Lifecycle](lifecycle.md) - How Modes interact with session lifecycle
- [Security](security.md) - Security considerations for Mode implementers
- [Determinism](determinism.md) - Making Modes deterministic
- [RFC-MACP-0002 Section 3](../rfcs/RFC-MACP-0002-modes.md#3-mode-descriptor) - Mode Descriptor specification
