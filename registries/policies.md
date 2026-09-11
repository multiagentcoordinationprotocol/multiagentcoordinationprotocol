# MACP Policy Registry

Governance Policies define deterministic, replay-safe governance rules that are evaluated at commitment time within MACP Sessions.

## Identifier Format

Policy identifiers use the form:

`policy.{namespace}.{name}`

Example:

`policy.fraud.majority-veto`

## Reserved Policies

| Policy ID | Mode | Description | Provision | Reference |
|-----------|------|-------------|-----------|-----------|
| `policy.default` | `*` | Default policy — no additional governance constraints beyond the mode's built-in rules | required | [RFC-MACP-0012 §5.1](../rfcs/RFC-MACP-0012-policy.md) |
| `policy.std.majority` | `macp.mode.decision.v1` | Simple majority — at least half of the decisive votes approve, minimum 1 voter | optional | [RFC-MACP-0012 §5.2](../rfcs/RFC-MACP-0012-policy.md) |
| `policy.std.supermajority` | `macp.mode.decision.v1` | Two-thirds supermajority, minimum 2 voters | optional | [RFC-MACP-0012 §5.2](../rfcs/RFC-MACP-0012-policy.md) |
| `policy.std.unanimous` | `macp.mode.decision.v1` | Every declared participant approves and no reject is cast | optional | [RFC-MACP-0012 §5.2](../rfcs/RFC-MACP-0012-policy.md) |

The `policy.default` identifier is reserved and MUST NOT be registered or unregistered. It is pre-registered in every conformant runtime.

The whole `policy.std.` namespace is reserved. A runtime MAY pre-register any subset of the profiles above, including none of them — reservation is a collision guarantee, not a provisioning requirement. A runtime that does provide one MUST use the canonical rules in RFC-MACP-0012 §5.2 verbatim, and a `SessionStart` naming a `policy.std.` identifier the runtime does not provide is rejected with `UNKNOWN_POLICY_VERSION`. Identifiers under `policy.std.` not listed above are reserved but unassigned.

Short unnamespaced identifiers such as `policy.majority` are **not** reserved and remain available to deployments. Deployments SHOULD still use their own namespace (`policy.{org}.{name}`) so that later additions under `policy.std.` cannot collide with local rules.

## Registration

Policies are registered with the runtime via:

- **gRPC `RegisterPolicy` RPC** — dynamic registration at runtime
- **File loading from `MACP_POLICIES_DIR`** — static loading at startup (implementation-defined)

Both paths are **admission**: the rule-schema validation required by [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md) §7 runs when a descriptor is registered or loaded, against the rule schemas the runtime ships — and never again afterwards. Because rule schemas can tighten between releases, a policy file that loaded under an earlier release may fail to load under a later one. Such a failure bars **new** sessions from binding that policy; it MUST NOT affect stored sessions, which replay from the persisted `PolicyDescriptor` without revalidation (RFC-MACP-0012 §8, items 2 and 4), never from `MACP_POLICIES_DIR`.

## Rule Schemas

Each standard mode defines a normative JSON Schema for its governance rules:

| Mode | Rule Schema | Reference |
|------|-------------|-----------|
| `macp.mode.decision.v1` | `schemas/json/policy/decision-rules.schema.json` | [RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.quorum.v1` | `schemas/json/policy/quorum-rules.schema.json` | [RFC-MACP-0012 Section 4.2](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.proposal.v1` | `schemas/json/policy/proposal-rules.schema.json` | [RFC-MACP-0012 Section 4.3](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.task.v1` | `schemas/json/policy/task-rules.schema.json` | [RFC-MACP-0012 Section 4.4](../rfcs/RFC-MACP-0012-policy.md) |
| `macp.mode.handoff.v1` | `schemas/json/policy/handoff-rules.schema.json` | [RFC-MACP-0012 Section 4.5](../rfcs/RFC-MACP-0012-policy.md) |
