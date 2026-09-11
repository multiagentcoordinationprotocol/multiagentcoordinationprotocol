
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
| `schema_version` | uint32 | Version of the rule schema used (`1`, `2`, or `3`). Version `2` adds Decision Mode decline-gating and is **additive**. Version `3` is the first **semantic** bump: it changes how an empty vote tally is evaluated (see [Empty tallies](#empty-tallies-and-schema_version) below). A stored policy is always evaluated under the version it declares, so `1` and `2` policies keep their original behavior forever. |

Canonical proto: [`schemas/proto/macp/v1/policy.proto`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/proto/macp/v1/policy.proto)
JSON Schema: [`schemas/json/macp-policy-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-policy-descriptor.schema.json)

In the Protobuf wire format, `rules` is a `string` containing JSON-encoded text. In JSON examples, `rules` is shown as a decoded JSON object for readability.

## Rule Schemas by Mode

Each standard mode defines a normative JSON Schema for its governance rules:

| Mode | Rule Schema | Key Parameters |
|------|-------------|----------------|
| Decision | [`decision-rules.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/policy/decision-rules.schema.json) | Voting algorithm, `threshold`, `weights`, quorum, objection handling, evaluation constraints, commitment authority |
| Quorum | [`quorum-rules.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/policy/quorum-rules.schema.json) | Threshold override, abstention handling, commitment authority |
| Proposal | [`proposal-rules.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/policy/proposal-rules.schema.json) | Acceptance criterion, max negotiation rounds, rejection behavior |
| Task | [`task-rules.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/policy/task-rules.schema.json) | Reassignment on reject, output requirement, commitment authority |
| Handoff | [`handoff-rules.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/policy/handoff-rules.schema.json) | Implicit accept timeout, commitment authority |

Decision Mode supports six voting algorithms: `none`, `majority`, `supermajority`, `unanimous`, `weighted`, and `plurality`. See [RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md) for full details.

`threshold` must be greater than `0`, at least `0.5` for `majority`, and greater than `0.5` for
`supermajority`. The `> 0` floor is enforced unconditionally, so `unanimous` and `plurality` —
which never consult `threshold` — still reject an explicit `0`. Threshold comparisons are **inclusive** (`ratio >=
threshold`), so `majority` at the default `0.5` approves an even split. The denominator is the
**decisive** votes — those cast as approve or reject; abstentions are excluded.

### The weighted electorate

Under `weighted`, the `weights` map **is** the electorate. A declared participant absent from the map
has weight `0`, which is how an observer is expressed — the schema rejects an explicit `0` and an
empty map. A weight-`0` vote is accepted as a message and preserved in history, but it is
**non-decisive**: it contributes to neither side of the ratio, does not enter the decisive tally, and
does not authorize a decline. It still counts as a vote cast for the `voting.quorum` participation
floor.

This rule is normative at **every** `schema_version`, not just `3`. So is the decline guard: a
**vote-authorized** negative commitment must be backed by at least one **decisive** explicit
`REJECT` vote, which means a `REJECT` from a weight-`0` participant never authorizes one.

### Empty tallies and `schema_version`

What happens when a commitment is attempted before any decisive vote has been cast depends on the
`schema_version` the bound policy declares. This is the one place the versions differ in behavior
rather than in vocabulary.

| | `schema_version` 1 and 2 | `schema_version` 3 |
|---|---|---|
| **Positive commitment** on an empty tally | The algorithm produces **no result** — it neither passes nor fails. Whether the commitment is blocked is governed **solely** by `commitment.require_vote_quorum`. With it `false` (the default), the commitment is **allowed**, even under `majority` or `unanimous`. | **Denied** for every algorithm except `none`. The algorithm is binding on its own; its predicate is evaluated over the actual tally, including the empty one, and fails. |
| **Vote-authorized negative commitment** on an empty tally | Denied for every algorithm except `none` — the decline guard needs a decisive `REJECT` and there is none. | Denied for every algorithm except `none`, for the same reason. |
| `voting.algorithm: "none"` | Unaffected. | Unaffected. |

For `weighted`, "empty tally" means **zero total decisive weight**, which covers both no ballots at
all and a complete ballot set cast entirely by weight-`0` participants.

The table governs **vote-authorized** commitment only. There is one other way a session can resolve
negatively on an empty tally, at every `schema_version` from `2` onward: if the policy sets
`objection_handling.critical_objection_action` to `finalize_decline` and a critical `Objection` is
standing, the decline is **objection-authorized** — the objection is itself the attributable
dissent the decline guard exists to require, so neither the guard nor the empty-tally rule applies.
Without that channel a session with a bound algorithm, no votes, and a standing critical objection
could only ever end by expiring.

The `1`/`2` behavior is fail-open: a policy that looks restrictive approves when nobody votes, and
adding one approving ballot could convert an allowed commitment into a denied one. It is retained
**solely** so that stored sessions replay identically — policy equality is `policy_id` +
`schema_version` + `rules`, and a runtime MUST evaluate a stored policy under the version it declares
even when a newer one exists. Implementations MUST keep this arm and MUST NOT apply it to
`schema_version` 3 **or later** policies.

**If you are writing a new policy, declare `schema_version: 3`.** If you must stay on `1` or `2` and
want the voting algorithm to be binding, set `commitment.require_vote_quorum` to `true` — that is the
only remedy available before version `3`.

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

Canonical proto definitions: [`schemas/proto/macp/v1/policy.proto`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/proto/macp/v1/policy.proto)

## Replay Invariant

The resolved `PolicyDescriptor` MUST be persisted as part of the session snapshot. During replay, the runtime MUST use the stored descriptor — never re-resolving from the registry. Policy equality uses `policy_id` + `schema_version` + `rules`, not full descriptor byte comparison. See [RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md) and [RFC-MACP-0012 Section 8](../rfcs/RFC-MACP-0012-policy.md).

## Examples

- [`examples/policy-decision-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policy-decision-session.json) — Decision Mode session governed by a supermajority voting policy with quorum and critical-severity veto
- [`examples/policy-registration-exchange.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policy-registration-exchange.json) — Dynamic policy registration request and response via gRPC

## What CI Validates

`make json-validate` checks every policy `rules` object in the repository against its mode's
rule schema in `schemas/json/policy/`. The mode is taken from the `mode` field beside the
`rules` object; `mode: "*"` (the mode-agnostic default policy) is skipped, and a `mode` naming
no known rule schema is a hard failure rather than a silent skip.

This reaches rules objects wherever they sit — discovery descriptors, conformance fixtures,
the nested descriptor in `examples/policy-registration-exchange.json`, and the fenced JSON
blocks in the RFCs and in this document.

**What it does not yet check.** None of the five rule schemas sets `additionalProperties: false`
or a top-level `required`, so an empty `rules` object validates against all of them, and an
unrecognized rule field is accepted and ignored. Decision Mode carries real constraints and
Quorum Mode carries one conditional arm; Proposal, Task, and Handoff are enum-and-type only.
A green run means nothing on disk contradicts its schema — not that the schemas are complete.

Policies for extension modes (`ext.*` and reverse-domain identifiers) are logged and skipped:
they have no standards-track rule schema by design. Only an unrecognized `macp.mode.*`
identifier is an error.

## Error Codes

| Code | Description | Reference |
|------|-------------|-----------|
| `UNKNOWN_POLICY_VERSION` | Policy not found in registry at SessionStart | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |
| `POLICY_DENIED` | Commitment rejected by governance policy rules | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |
| `INVALID_POLICY_DEFINITION` | Policy descriptor fails validation | [RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md) |

Full error code registry: [`registries/error-codes.md`](../registries/error-codes.md)
