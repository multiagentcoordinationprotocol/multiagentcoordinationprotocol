# RFC-MACP-0012
# Multi-Agent Coordination Protocol (MACP) — Governance Policy Framework

**Document:** RFC-MACP-0012
**Version:** 1.0.0-draft
**Status:** Community Standards Track
**Updates:** RFC-MACP-0001, RFC-MACP-0002, RFC-MACP-0003

## Abstract

This document defines the MACP Governance Policy Framework: a declarative, deterministic, and replay-safe mechanism for binding governance rules to Coordination Sessions. Policies specify how session outcomes are determined — voting algorithms, quorum thresholds, objection handling, commitment authority, and mode-specific governance constraints. Policies are authored via SDKs, registered with the runtime, resolved at `SessionStart`, and evaluated at commitment time.

## 1. Purpose and Scope

MACP Modes (RFC-MACP-0002) define coordination semantics — valid message types, participant models, and terminal conditions. However, Modes intentionally do not prescribe governance algorithms. RFC-MACP-0007 (Decision Mode) states:

> "The mode does not prescribe a single voting algorithm. A runtime or deployment may use majority vote, weighted vote, objection handling, veto rules, or another deterministic policy, provided that the policy is version-bound and replay-safe."

The `policy_version` field exists in `SessionStartPayload` and `CommitmentPayload` (RFC-MACP-0001) but has no defined resolution or evaluation semantics. This RFC fills that gap by defining:

1. a **policy descriptor** format that any runtime in any language can interpret,
2. **rule schemas** for each standard mode's governance parameters,
3. **evaluation semantics** specifying when and how policies are applied,
4. a **default policy** that all runtimes MUST provide for backward compatibility,
5. a **registration lifecycle** for dynamic policy management via gRPC RPCs,
6. **replay invariants** ensuring policy evaluation is deterministic across implementations.

This RFC is cross-cutting: it applies to all standard modes and to extension modes that opt in.

## 2. Policy Identifiers

### 2.1 Naming Convention

Policy identifiers use the form:

`policy.{namespace}.{name}`

Examples:

- `policy.default` — the built-in default policy
- `policy.fraud.majority-veto` — a domain-specific policy
- `policy.lending.unanimous` — another domain-specific policy

### 2.2 Reserved Namespace

The `policy.default` identifier is reserved. Runtimes MUST NOT allow registration of a policy with this identifier; it is always pre-registered.

### 2.3 Immutability

A registered policy identifier is immutable. To change governance rules, register a new policy with a new identifier. This ensures that `policy_version` in historical sessions always resolves to the same rules.

## 3. Policy Descriptor

A policy descriptor is a structured document with the following required fields:

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | string | Unique policy identifier (see Section 2.1) |
| `mode` | string | Target mode identifier (e.g., `macp.mode.decision.v1`) or `*` for mode-agnostic |
| `description` | string | Human-readable description of the policy's governance rules |
| `rules` | object | Mode-specific governance rules (see Section 4) |
| `schema_version` | uint32 | Version of the rule schema used (`1` or `2`) |

Schema version `2` adds the Decision Mode decline-gating parameters (`commitment.allow_decline_over_approval`, `objection_handling.critical_objection_action`; see §4.1). The bump is **additive**: the new fields are optional and default to legacy behavior, so `schema_version: 1` policies remain valid and a runtime MUST accept every schema version it supports (`{1, 2}`). Declaring `schema_version: 2` signals only that the descriptor MAY use the new fields.

The canonical wire format is defined in `schemas/proto/macp/v1/policy.proto`. The `rules` field is JSON-encoded bytes to allow mode-specific schemas without requiring proto changes per mode.

**Encoding note:** In the Protobuf wire format, `rules` is `bytes` containing JSON-encoded text. In JSON canonical form (e.g., examples), `rules` is shown as a decoded JSON object for readability. In actual proto-to-JSON serialization, `rules` would be base64-encoded. Examples in this specification use the decoded form unless otherwise noted.

## 4. Rule Schemas

Each standard mode defines a normative JSON Schema for its governance rules. Any runtime implementation MUST interpret these rules identically given identical inputs.

### 4.1 Decision Mode Rules

Canonical schema: `schemas/json/policy/decision-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `voting` | `algorithm`, `threshold`, `quorum`, `weights` | Voting algorithm and quorum requirements |
| `objection_handling` | `critical_severity_vetoes`, `veto_threshold`, `critical_objection_action` | How critical-severity objections affect commitment eligibility |
| `evaluation` | `minimum_confidence`, `required_before_voting` | Evaluation constraints |
| `commitment` | `authority`, `designated_roles`, `require_vote_quorum`, `allow_decline_over_approval` | Who can commit and under what conditions |

**Voting algorithms:**

- `none` — no voting constraint enforced (mode's built-in logic applies)
- `majority` — more than 50% of cast votes must approve
- `supermajority` — at least `threshold` fraction of cast votes must approve
- `unanimous` — all cast votes must approve
- `weighted` — weighted votes using `weights` map; `threshold` applies to weighted sum
- `plurality` — proposal with the most approve votes wins; no threshold

**Quorum:**

- `type: "count"` — minimum number of votes that must be cast
- `type: "percentage"` — minimum percentage of declared participants that must vote

**Negative-outcome parameters:**

- `commitment.allow_decline_over_approval` (bool, default `false`) — permit a negative commitment (`outcome_positive: false`) even when the vote **Passed**. With the default `false`, a passed vote authorizes only a positive commitment.
- `objection_handling.critical_objection_action` (enum `deny` | `finalize_decline` | `hold`, default `deny`) — action taken when a critical objection would block commitment: `deny` (reject the commitment; legacy behavior), `finalize_decline` (finalize the session as a negative outcome), or `hold` (leave the session open).

The **decline guard** for a vote-authorized negative commitment (≥1 explicit `Vote` with `vote == "REJECT"`; optional `commitment.require_vote_quorum`) is defined with the Decision Mode terminal semantics — see [RFC-MACP-0007](RFC-MACP-0007-decision-mode.md) §6.2. Both parameters are additive with conservative defaults that preserve pre-existing behavior; policies that use them declare `schema_version: 2`.

### 4.2 Quorum Mode Rules

Canonical schema: `schemas/json/policy/quorum-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `threshold` | `type`, `value` | Override the `required_approvals` from `ApprovalRequest` |
| `abstention` | `counts_toward_quorum`, `interpretation` | How abstentions affect quorum calculation |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

### 4.3 Proposal Mode Rules

Canonical schema: `schemas/json/policy/proposal-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `acceptance` | `criterion` | `all_parties`, `counterparty`, or `initiator` |
| `counter_proposal` | `max_rounds` | Maximum negotiation rounds (0 = unlimited) |
| `rejection` | `terminal_on_any_reject` | Whether any rejection terminates the session |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

### 4.4 Task Mode Rules

Canonical schema: `schemas/json/policy/task-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `assignment` | `allow_reassignment_on_reject` | Whether rejected tasks can be reassigned |
| `completion` | `require_output` | Whether `TaskComplete` must include output |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

### 4.5 Handoff Mode Rules

Canonical schema: `schemas/json/policy/handoff-rules.schema.json`

| Rule Group | Parameters | Description |
|------------|-----------|-------------|
| `acceptance` | `implicit_accept_timeout_ms` | Auto-accept after timeout (0 = no implicit accept) |
| `commitment` | `authority` | Who can emit the terminal `Commitment` |

**Determinism note:** `implicit_accept_timeout_ms` is **not** evaluated by the policy evaluator at commitment time. It is a declarative parameter consumed by the mode's timer/TTL mechanism, which emits a synthetic accept event into the session history before any commitment evaluation occurs. The policy evaluator only sees the resulting accepted message history, preserving the determinism requirement of Section 6.3.

### 4.6 Extension Mode Rules

Extension modes registered via `RegisterExtMode` MAY define custom rule schemas. The runtime SHOULD validate custom rules against the mode's declared policy schema if one exists. Extension modes without a declared policy schema accept any valid JSON as rules.

## 5. Default Policy

Every conformant runtime MUST pre-register the following default policy:

```json
{
  "policy_id": "policy.default",
  "mode": "*",
  "schema_version": 1,
  "description": "Default policy — mode built-in rules apply with no additional governance constraints",
  "rules": {}
}
```

The default policy applies no additional governance constraints beyond base mode validation. Mode-specific default behaviors (e.g., Decision Mode's default voting algorithm, Quorum Mode's default abstention handling) are defined by each mode's base validation rules in their respective RFCs, not by the default policy.

When `policy_version` in `SessionStartPayload` is empty or equals `policy.default`, the runtime MUST apply this default. The default policy sets all rule parameters to permissive values such that the mode's built-in validation is the only constraint applied. It does not disable mode validation — it simply adds no governance restrictions on top of it.

## 6. Evaluation Semantics

### 6.1 Policy Resolution

At `SessionStart`:

1. The runtime extracts `policy_version` from the `SessionStartPayload`.
2. If empty, the runtime resolves to `policy.default`.
3. If non-empty, the runtime looks up the policy in its registry.
4. If the policy is not found, the runtime MUST reject the `SessionStart` with error code `UNKNOWN_POLICY_VERSION`.
5. If the policy's `mode` field is not `*` and does not match the session's mode, the runtime MUST reject with `INVALID_POLICY_DEFINITION`.
6. The resolved `PolicyDescriptor` (including the full `rules` object) is stored on the session for the session's lifetime.

### 6.2 Commitment Evaluation

When a `Commitment` envelope is received:

1. The runtime retrieves the resolved `PolicyDescriptor` from the session.
2. The runtime evaluates the policy's `rules` against the accumulated session state (proposals, evaluations, objections, votes, or mode-equivalent messages).
3. If the policy rules are satisfied, the `Commitment` is accepted and the session resolves.
4. If the policy rules are not satisfied, the runtime MUST reject the `Commitment` with error code `POLICY_DENIED` and an informative reason string.

### 6.3 Determinism Requirement

Policy evaluation MUST be a pure function of:

- the resolved policy `rules` (immutable for the session),
- the accumulated accepted message history,
- the session's declared participants.

Policy evaluation MUST NOT depend on wall-clock time, external service calls, randomness, or any state outside the session boundary.

### 6.4 Interaction with Mode Validation

Policy evaluation layers on top of mode validation. Policy rules MAY override specific mode defaults (e.g., abstention interpretation in Quorum Mode, reassignment in Task Mode) while preserving Core invariants (isolation, monotonic lifecycle, append-only history). The interaction model is: base mode validation runs first, then policy rules adjust eligible behaviors within the boundaries established by mode validation.

1. The mode's own validation rules (message type authorization, structural validation, phase transitions) execute first.
2. Policy governance rules execute second, only for `Commitment` messages that pass mode validation.
3. A `Commitment` must satisfy both mode validation and policy governance to be accepted.

## 7. Registration Lifecycle

Policies are managed through five gRPC RPCs on `MACPRuntimeService`, mirroring the extension mode lifecycle:

| RPC | Purpose |
|-----|---------|
| `RegisterPolicy` | Register a new policy descriptor |
| `UnregisterPolicy` | Remove a registered policy (does not affect active sessions) |
| `GetPolicy` | Retrieve a policy descriptor by ID |
| `ListPolicies` | List registered policies, optionally filtered by mode |
| `WatchPolicies` | Server-streaming RPC for policy registry change notifications |

Unlike `WatchModeRegistry` (which returns a lightweight `RegistryChanged` notification), `WatchPolicies` returns the full set of current policy descriptors on each change. This design reflects that policy consumers typically need the complete rule set for evaluation, not just a change signal.

Registration constraints:

- `policy.default` MUST NOT be registered or unregistered (it is built-in).
- `policy_id` MUST be unique; re-registration of an existing ID MUST fail.
- `rules` MUST validate against the target mode's rule JSON Schema if a schema exists.
- Unregistering a policy does not affect sessions that have already resolved it.

Canonical proto definitions: `schemas/proto/macp/v1/policy.proto`

## 8. Replay Invariant

RFC-MACP-0003 (Determinism) requires that replay under identical bound versions produces identical outcomes. This RFC extends that requirement to policies:

1. The resolved `PolicyDescriptor` MUST be persisted as part of the session snapshot.
2. During replay, the runtime MUST use the stored `PolicyDescriptor`, never re-resolving from the registry.
3. If the stored policy uses `schema_version` N, the runtime MUST evaluate using schema-version-N semantics, even if a newer schema version exists.

`registered_at_unix_ms` is runtime metadata and is not part of the policy's semantic identity. Replay and policy equality comparisons MUST use `policy_id` + `schema_version` + `rules` equality, not full descriptor byte comparison.

This ensures that a session replayed years later produces identical governance outcomes regardless of registry state.

## 9. Capability Advertisement

Runtimes that support the policy framework SHOULD advertise the `policy_registry` capability during `Initialize`:

```protobuf
message PolicyRegistryCapability {
  bool register_policy = 1;
  bool list_policies = 2;
  bool list_changed = 3;
}
```

This capability is added to the `Capabilities` message. Runtimes that do not support policy registration but do support policy evaluation (e.g., file-loaded policies only) SHOULD set `register_policy = false` and `list_policies = true`.

## 10. Error Codes

The following error codes are added to the MACP Error Code Registry:

| Code | Description | HTTP Status | Status | Reference |
|------|-------------|-------------|--------|-----------|
| `UNKNOWN_POLICY_VERSION` | `policy_version` not found in policy registry at SessionStart | 404 | permanent | RFC-MACP-0012 |
| `POLICY_DENIED` | Commitment rejected because governance policy rules are not satisfied | 403 | permanent | RFC-MACP-0012 |
| `INVALID_POLICY_DEFINITION` | Policy descriptor fails validation (bad JSON, schema mismatch, mode mismatch) | 400 | permanent | RFC-MACP-0012 |

## 11. Security Considerations

Implementations MUST address all of the following:

- authenticate senders of `RegisterPolicy` and `UnregisterPolicy` requests,
- prevent unauthorized modification of the policy registry,
- ensure that resolved policies cannot be mutated after binding to a session,
- protect policy descriptors from information disclosure if they contain sensitive governance parameters,
- preserve the complete policy evaluation trail for audit and replay.

Policy evaluation MUST NOT introduce side channels: the accept/reject decision for a `Commitment` must depend solely on session state and the bound policy, not on the identity of the commitment sender beyond what the policy's `commitment.authority` rule specifies.

## 12. Canonical Schemas and Examples

Canonical proto schema:

- `schemas/proto/macp/v1/policy.proto`

Canonical JSON Schemas for governance rules:

- `schemas/json/policy/decision-rules.schema.json`
- `schemas/json/policy/quorum-rules.schema.json`
- `schemas/json/policy/proposal-rules.schema.json`
- `schemas/json/policy/task-rules.schema.json`
- `schemas/json/policy/handoff-rules.schema.json`

Well-known policy identifiers:

- `registries/policies.md`

Example transcript:

- `examples/policy-decision-session.json`

Policy registration exchange example:

- `examples/policy-registration-exchange.json`
