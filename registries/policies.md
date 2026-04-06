# MACP Policy Registry

Governance Policies define deterministic, replay-safe governance rules that are evaluated at commitment time within MACP Sessions.

## Identifier Format

Policy identifiers use the form:

`policy.{namespace}.{name}`

Example:

`policy.fraud.majority-veto`

## Reserved Policies

| Policy ID | Mode | Description | Status | Reference |
|-----------|------|-------------|--------|-----------|
| `policy.default` | `*` | Default policy — no additional governance constraints beyond the mode's built-in rules | permanent | [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) |

The `policy.default` identifier is reserved and MUST NOT be registered or unregistered. It is pre-registered in every conformant runtime.

## Well-Known Policies

Well-known policies are not reserved but are recommended for common governance patterns:

| Policy ID | Mode | Description | Status |
|-----------|------|-------------|--------|
| `policy.majority` | `macp.mode.decision.v1` | Simple majority vote (>50%) with no quorum requirement | recommended |
| `policy.supermajority` | `macp.mode.decision.v1` | Two-thirds supermajority with minimum 2-voter quorum | recommended |
| `policy.unanimous` | `macp.mode.decision.v1` | All participants must vote approve; any reject blocks | recommended |

## Registration

Policies are registered with the runtime via:

- **gRPC `RegisterPolicy` RPC** — dynamic registration at runtime
- **File loading from `MACP_POLICIES_DIR`** — static loading at startup (implementation-defined)

## Rule Schemas

Each standard mode defines a normative JSON Schema for its governance rules:

| Mode | Rule Schema | Reference |
|------|-------------|-----------|
| `macp.mode.decision.v1` | `schemas/json/policy/decision-rules.schema.json` | [RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.quorum.v1` | `schemas/json/policy/quorum-rules.schema.json` | [RFC-MACP-0012 Section 4.2](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.proposal.v1` | `schemas/json/policy/proposal-rules.schema.json` | [RFC-MACP-0012 Section 4.3](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.task.v1` | `schemas/json/policy/task-rules.schema.json` | [RFC-MACP-0012 Section 4.4](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.handoff.v1` | `schemas/json/policy/handoff-rules.schema.json` | [RFC-MACP-0012 Section 4.5](../rfcs/RFC-MACP-0012-policy.md) |
