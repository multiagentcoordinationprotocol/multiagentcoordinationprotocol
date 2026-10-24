# Policy Packs

> **Status:** Non-normative (explanatory). In case of conflict, the referenced RFC is authoritative.
> **Reference:** [RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md), [RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md), [RFC-MACP-0011](../rfcs/RFC-MACP-0011-quorum-mode.md)

A policy pack is a ready-made governance policy you can copy, rename and register. Each pack in [`examples/policies/`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/tree/main/examples/policies) is a complete `PolicyDescriptor` written only with the rule fields RFC-MACP-0012 already defines. Each one is backed by a conformance fixture that runs it against a runtime and checks both the session it allows and the messages it refuses.

| Pack | Mode | What it enforces | File | Conformance fixture |
|---|---|---|---|---|
| Human sign-off | Decision | Only a named approver may emit the binding Commitment | [`human-signoff.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policies/human-signoff.json) | [`decision_policy_pack_human_signoff.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/conformance/decision_policy_pack_human_signoff.json) |
| Two-agent rule | Quorum | Two distinct approvers, whatever the request asks for | [`two-agent-rule.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policies/two-agent-rule.json) | [`quorum_policy_pack_two_agent_rule.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/conformance/quorum_policy_pack_two_agent_rule.json) |
| Compliance vote | Decision | No positive outcome until the compliance agent votes APPROVE | [`compliance-vote.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policies/compliance-vote.json) | [`decision_policy_pack_compliance_vote.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/conformance/decision_policy_pack_compliance_vote.json) |
| No self-approval | — | Not expressible today; see [below](#not-expressible-no-self-approval) | — | — |

## What a policy can and cannot see

Read this before you pick a pack. It explains why two of the packs carry only part of the rule their name suggests.

A policy is evaluated over the session's **accepted history**: who the participants are, who sent which message, and how they voted, approved or objected. No rule field reads the **contents** of a payload. A policy cannot say "if the amount is above $10,000" or "if the data contains PII", because no field in any rule schema refers to payload values ([RFC-MACP-0012 Section 4](../rfcs/RFC-MACP-0012-policy.md)). Rule objects are closed, so you cannot add such a field to a policy either.

The condition therefore lives **outside** the policy. Whatever starts the session (an orchestrator, an SDK client, a gateway) checks the amount or the data classification and picks the policy by setting `policy_version` in `SessionStart`. The runtime resolves that policy once, binds it to the session and enforces it for the session's whole life ([RFC-MACP-0012 Section 6.1](../rfcs/RFC-MACP-0012-policy.md)). The runtime does **not** check that the right policy was chosen. If the selection matters for audit, state the reason in the session itself, for example in the Proposal's `rationale` or the ApprovalRequest's `summary`, so it is part of the replayable history. Make the choice in code you control.

## Using a pack

1. Copy the file and change `policy_id` to an identifier in your own namespace, for example `policy.acme.human-signoff`. The `policy.std.` namespace and `policy.default` are reserved ([RFC-MACP-0012 Section 2.2](../rfcs/RFC-MACP-0012-policy.md)). The packs use `policy.packs.*` as a placeholder namespace.
2. Replace the example sender identifiers (`agent://human-approver`, `agent://compliance`) with the authenticated sender identities in your deployment.
3. Register the descriptor with `RegisterPolicy` ([RFC-MACP-0012 Section 7](../rfcs/RFC-MACP-0012-policy.md)). A descriptor is immutable once registered, so a changed rule needs a new `policy_id` ([Section 2.3](../rfcs/RFC-MACP-0012-policy.md)).
4. Start sessions with `SessionStart.policy_version` set to that `policy_id`.

All three packs declare `schema_version: 3`. That is the version under which a voting algorithm is binding on its own, and an empty tally denies a commitment instead of letting it through ([RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md), "Empty tally"). Keep it at 3 when you adapt a pack.

## Human sign-off

**The rule:** agents may propose, evaluate, object and vote, but the decision binds only when a named approver emits the Commitment.

```json
{
  "voting": { "algorithm": "none" },
  "commitment": {
    "authority": "designated_role",
    "designated_roles": ["agent://human-approver"]
  }
}
```

**How it works.** By default the session initiator holds Commitment authority in Decision Mode ([RFC-MACP-0007 Section 2.1](../rfcs/RFC-MACP-0007-decision-mode.md)). `commitment.authority: "designated_role"` replaces that default, and only senders listed in `designated_roles` may commit. A Commitment from anyone else, the initiator included, is a sender-authorization failure and is rejected with `FORBIDDEN`, not `POLICY_DENIED` ([RFC-MACP-0012 Section 10](../rfcs/RFC-MACP-0012-policy.md)). `voting.algorithm: "none"` means the agents' votes are recorded as advice and do not gate the approver. To require a passing agent vote as well as the sign-off, set an algorithm such as `majority` instead.

**What the fixture proves.** The planner proposes a payment and the analyst votes APPROVE. A Commitment from the initiator and one from the approving analyst are both rejected with `FORBIDDEN`. The approver's Commitment is accepted and the session resolves.

**Limits.**

- *"Above $X."* The amount condition is not part of the policy (see [What a policy can and cannot see](#what-a-policy-can-and-cannot-see)). Select this pack at `SessionStart` for the sessions that need sign-off.
- *"Human."* The protocol identifies senders, not people. The rule holds only as far as your authentication binds `agent://human-approver` to a person, for example a credential that only an approval UI holds ([RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md)).
- *Role names.* The schema describes `designated_roles` entries as "participant IDs or roles", but no RFC defines a role vocabulary or how a sender acquires a role. Listing sender identifiers, as this pack does, is the portable form.

## Two-agent rule

**The rule:** an action is approved only after two different participants have approved it. This is also called the four-eyes principle.

```json
{
  "threshold": { "type": "n_of_m", "value": 2 }
}
```

**How it works.** A Quorum `ApprovalRequest` carries its own `required_approvals`. A policy `threshold` **replaces** that value ([RFC-MACP-0011 Section 5](../rfcs/RFC-MACP-0011-quorum-mode.md), rule 6), so the coordinator cannot lower the bar by asking for one approval. Each eligible participant casts at most one ballot per request, and a second ballot from the same sender is rejected (rule 3). Two approvals therefore always come from two distinct declared participants. The coordinator is not a voter unless it is also listed in `participants` ([RFC-MACP-0011 Section 2.1](../rfcs/RFC-MACP-0011-quorum-mode.md)).

**What the fixture proves.** The request asks for `required_approvals: 1`. After one approval, a positive Commitment is rejected with `INVALID_ENVELOPE` because the session is not yet eligible (rule 4). The same approver's second Approve is rejected. A second approver's Approve makes the session eligible, and the Commitment is accepted.

**Limits.** Two approvals from two *identifiers* are only as independent as those identifiers. If one operator controls both agents, the rule is met on paper only. That is a deployment property the protocol cannot see. If the coordinator should not approve its own request, keep it out of `participants`.

## Compliance vote

**The rule:** a decision cannot resolve positively until the compliance agent has voted APPROVE. Other agents still vote, and their votes are recorded, but they cannot carry the decision without compliance.

```json
{
  "voting": {
    "algorithm": "weighted",
    "threshold": 1,
    "weights": { "agent://compliance": 1 }
  }
}
```

**How it works.** Under `weighted`, the `weights` map defines the electorate. A participant missing from the map has weight 0: its vote is accepted and kept in history, but it is non-decisive ([RFC-MACP-0012 Section 4.1](../rfcs/RFC-MACP-0012-policy.md), "weighted electorate"). With the compliance agent as the only weighted voter, the decisive tally is empty until compliance votes. Under `schema_version: 3` an empty tally denies a commitment in both directions, with `POLICY_DENIED`. After compliance votes APPROVE, the approve share is 1/1 and the commitment is allowed. If compliance votes REJECT, the decisive reject allows a negative commitment ([RFC-MACP-0007 Section 6.2](../rfcs/RFC-MACP-0007-decision-mode.md)).

**What the fixture proves.** The planner and the analyst both vote APPROVE. A positive Commitment is still rejected with `POLICY_DENIED`. After the compliance agent votes APPROVE, the Commitment is accepted, and all three ballots stay in the recorded mode state.

**Limits.**

- *"PII requires."* Detecting personal data is not part of the policy (see [What a policy can and cannot see](#what-a-policy-can-and-cannot-see)). Select this pack at `SessionStart` for sessions that touch personal data.
- *Compliance plus a majority.* The pack makes compliance's vote **sufficient** as well as necessary. Requiring both a compliance approval and a majority of the other agents is not expressible: one session has one algorithm, and `weighted` with several weights is a single pooled ratio, not two separate gates. Two sessions run in sequence can approximate it.

## Not expressible: no self-approval

**The intended rule:** the agent that proposed or requested an action may not be one of the approvers that carry it.

No current rule field states this, and this page does not invent one. The candidates we checked:

- **Decision Mode** has no rule that relates a voter to the proposal's author. A proposer's own APPROVE counts like any other vote under every algorithm. Leaving the proposer out of `weights` works only when you know before the session starts who will propose, and then it removes that agent's vote on *every* proposal, not just its own.
- **Proposal Mode** has `acceptance.criterion`, whose values include `counterparty`. RFC-MACP-0012 Section 4.3 lists the value, but no RFC defines what it means, and RFC-MACP-0008 does not mention it. A pack that relied on one runtime's reading of it would not be portable, so we do not ship one.
- **Quorum Mode** already keeps the coordinator from approving its own request, unless the coordinator is also listed in `participants` ([RFC-MACP-0011 Section 2.1](../rfcs/RFC-MACP-0011-quorum-mode.md)). That is a property of the mode and the participant list, not of a policy, so it needs no pack. Build the two-agent rule session with the coordinator outside `participants` and you get no self-approval for free.

A real "no self-approval" policy would need a new rule field with defined semantics, which means an RFC-MACP-0012 revision ([CONTRIBUTING.md](../CONTRIBUTING.md)). Until then, use the Quorum roster property above. A vendor-extension key (RFC-MACP-0012 Section 4, "Vendor-extension keys") could also add the restriction, but only on runtimes that implement that extension.

## How CI holds the packs

`make json-validate` (`scripts/validate-json.sh`):

- validates every file in `examples/policies/` against [`macp-policy-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-policy-descriptor.schema.json);
- validates each pack's `rules` object against its mode's rule schema in `schemas/json/policy/`;
- requires each pack to be inlined, unchanged, by exactly one conformance fixture.

`make conformance-lint` checks that each fixture is internally consistent. Runtimes replay the fixtures as part of the canonical conformance pack ([conformance.md](conformance.md)).
