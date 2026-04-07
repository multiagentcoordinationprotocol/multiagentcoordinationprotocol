
# MACP Policy Guide

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md)

Governance Policies provide a declarative, deterministic, and replay-safe mechanism for binding governance rules to Coordination Sessions. They specify how session outcomes are determined — voting algorithms, quorum thresholds, objection handling, commitment authority, and mode-specific constraints.

## Why Policies Exist

Modes (RFC-MACP-0002) define coordination semantics but intentionally do not prescribe governance algorithms. Decision Mode, for example, supports majority vote, weighted vote, veto rules, and other deterministic policies. The policy framework fills that gap: policies are authored via SDKs, registered with the runtime, resolved at `SessionStart`, and evaluated at commitment time.

## Policy Identifiers

Policy identifiers use the form `policy.{namespace}.{name}`:

- `policy.default` — the built-in default policy (reserved)
- `policy.fraud.majority-veto` — a domain-specific policy
- `policy.lending.unanimous` — another domain-specific policy

The `policy.default` identifier is reserved and always pre-registered. Registered policy identifiers are immutable — to change governance rules, register a new policy with a new identifier. This ensures that `policy_version` in historical sessions always resolves to the same rules.

## Policy Descriptor

A policy descriptor has five required fields:

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | string | Unique policy identifier |
| `mode` | string | Target mode identifier or `*` for mode-agnostic |
| `description` | string | Human-readable description |
| `rules` | object | Mode-specific governance rules (see Rule Schemas) |
| `schema_version` | uint32 | Version of the rule schema used (currently `1`) |

Canonical proto: [`schemas/proto/macp/v1/policy.proto`](../schemas/proto/macp/v1/policy.proto)
JSON Schema: [`schemas/json/macp-policy-descriptor.schema.json`](../schemas/json/macp-policy-descriptor.schema.json)

In the Protobuf wire format, `rules` is `bytes` containing JSON-encoded text. In JSON examples, `rules` is shown as a decoded JSON object for readability.

## Rule Schemas by Mode

Each standard mode defines a normative JSON Schema for its governance rules:

| Mode | Rule Schema | Key Parameters |
|------|-------------|----------------|
| Decision | [`decision-rules.schema.json`](../schemas/json/policy/decision-rules.schema.json) | Voting algorithm, quorum, objection handling, evaluation constraints, commitment authority |
| Quorum | [`quorum-rules.schema.json`](../schemas/json/policy/quorum-rules.schema.json) | Threshold override, abstention handling, commitment authority |
| Proposal | [`proposal-rules.schema.json`](../schemas/json/policy/proposal-rules.schema.json) | Acceptance criterion, max negotiation rounds, rejection behavior |
| Task | [`task-rules.schema.json`](../schemas/json/policy/task-rules.schema.json) | Reassignment on reject, output requirement, commitment authority |
| Handoff | [`handoff-rules.schema.json`](../schemas/json/policy/handoff-rules.schema.json) | Implicit accept timeout, commitment authority |

Decision Mode supports six voting algorithms: `none`, `majority`, `supermajority`, `unanimous`, `weighted`, and `plurality`. See [RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md) for full details.

## Default Policy

Every conformant runtime MUST pre-register the default policy:

```json
{
  "policy_id": "policy.default",
  "mode": "*",
  "schema_version": 1,
  "description": "Default policy — mode built-in rules apply with no additional governance constraints",
  "rules": {}
}
```

When `policy_version` in `SessionStartPayload` is empty or equals `policy.default`, the runtime applies this default. It adds no governance restrictions on top of mode validation.

## Policy Evaluation

### Resolution

At `SessionStart`, the runtime resolves `policy_version` from the payload. If empty, it resolves to `policy.default`. If the policy is not found, the runtime rejects with `UNKNOWN_POLICY_VERSION`. The resolved `PolicyDescriptor` is stored on the session for its lifetime.

### Commitment Evaluation

When a `Commitment` envelope arrives, the runtime evaluates the policy's `rules` against accumulated session state. If satisfied, the `Commitment` is accepted. If not, the runtime rejects with `POLICY_DENIED`.

Policy evaluation layers on top of mode validation: mode validation runs first, then policy rules adjust eligible behaviors within mode boundaries. A `Commitment` must satisfy both to be accepted.

### Determinism

Policy evaluation MUST be a pure function of the resolved `rules`, the accumulated accepted message history, and the session's declared participants. It MUST NOT depend on wall-clock time, external calls, randomness, or state outside the session boundary. See [RFC-MACP-0012 Section 6.3](../rfcs/RFC-MACP-0012-policy.md).

## Registration Lifecycle

Policies are managed through five gRPC RPCs on `MACPRuntimeService`:

| RPC | Purpose |
|-----|---------|
| `RegisterPolicy` | Register a new policy descriptor |
| `UnregisterPolicy` | Remove a registered policy (does not affect active sessions) |
| `GetPolicy` | Retrieve a policy descriptor by ID |
| `ListPolicies` | List registered policies, optionally filtered by mode |
| `WatchPolicies` | Stream policy registry change notifications |

Registration constraints: `policy.default` cannot be registered or unregistered; `policy_id` must be unique; `rules` must validate against the target mode's rule schema.

Canonical proto definitions: [`schemas/proto/macp/v1/policy.proto`](../schemas/proto/macp/v1/policy.proto)

## Replay Invariant

The resolved `PolicyDescriptor` MUST be persisted as part of the session snapshot. During replay, the runtime MUST use the stored descriptor — never re-resolving from the registry. Policy equality uses `policy_id` + `schema_version` + `rules`, not full descriptor byte comparison. See [RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md) and [RFC-MACP-0012 Section 8](../rfcs/RFC-MACP-0012-policy.md).

## Examples

- [`examples/policy-decision-session.json`](../examples/policy-decision-session.json) — Decision Mode session governed by a supermajority voting policy with quorum and critical-severity veto
- [`examples/policy-registration-exchange.json`](../examples/policy-registration-exchange.json) — Dynamic policy registration request and response via gRPC

## Error Codes

| Code | Description | Reference |
|------|-------------|-----------|
| `UNKNOWN_POLICY_VERSION` | Policy not found in registry at SessionStart | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |
| `POLICY_DENIED` | Commitment rejected by governance policy rules | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |
| `INVALID_POLICY_DEFINITION` | Policy descriptor fails validation | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |

Full error code registry: [`registries/error-codes.md`](../registries/error-codes.md)
