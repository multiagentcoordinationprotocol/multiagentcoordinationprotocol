# MACP Examples

> **Status:** Non-normative (explanatory). In case of conflict, [RFC-MACP-0001](../rfcs/RFC-MACP-0001-core.md) is authoritative.

This repository includes illustrative transcripts for each standards-track mode and for policy-governed sessions.

## Available example transcripts

| File | Mode | What it shows |
|------|------|---------------|
| [`examples/decision-mode-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/decision-mode-session.json) | `macp.mode.decision.v1` | initialization, `SessionStart`, proposal, evaluations, objection, votes, and terminal `Commitment` |
| [`examples/proposal-mode-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/proposal-mode-session.json) | `macp.mode.proposal.v1` | offer, counteroffer, dual acceptance, and bound agreement |
| [`examples/task-mode-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/task-mode-session.json) | `macp.mode.task.v1` | bounded delegation, progress, completion, and bound task outcome |
| [`examples/handoff-mode-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/handoff-mode-session.json) | `macp.mode.handoff.v1` | responsibility transfer with context handoff and acceptance |
| [`examples/quorum-mode-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/quorum-mode-session.json) | `macp.mode.quorum.v1` | threshold approval leading to a final commitment |
| [`examples/policy-decision-session.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policy-decision-session.json) | `macp.mode.decision.v1` | policy-governed Decision Mode with supermajority voting, quorum, and critical-severity veto (RFC-MACP-0012) |
| [`examples/policy-registration-exchange.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/policy-registration-exchange.json) | N/A (gRPC exchange) | dynamic policy registration request and response (RFC-MACP-0012 Section 7) |

## Single-envelope examples

Standalone Envelope examples, one per Core message type, each validating against its
`$defs` entry in [`schemas/json/macp-envelope.schema.json`](../schemas/json/macp-envelope.schema.json):

| File | Message type | `$defs` entry | RFC |
|------|------|------|-----|
| [`examples/json/signal.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/signal.json) | `Signal` | `SignalPayload` | [RFC-MACP-0001 §6](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/progress_ambient.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/progress_ambient.json) | `Progress` (ambient form) | `ProgressPayload` | [RFC-MACP-0001 §6](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/session_start.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/session_start.json) | `SessionStart` | `SessionStartPayload` | [RFC-MACP-0001 §7.1](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/session_suspend.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/session_suspend.json) | `SessionSuspend` | `SessionSuspendPayload` | [RFC-MACP-0001 §7.5](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/session_resume.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/session_resume.json) | `SessionResume` | `SessionResumePayload` | [RFC-MACP-0001 §7.5](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/session_cancel.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/session_cancel.json) | `SessionCancel` | `SessionCancelPayload` | [RFC-MACP-0001 §7.3](../rfcs/RFC-MACP-0001-core.md) |
| [`examples/json/commitment.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/json/commitment.json) | `Commitment` | `CommitmentPayload` (whose optional `supersedes`/`CommitmentRef` fields are described in [RFC-MACP-0001 §7.3.1](../rfcs/RFC-MACP-0001-core.md)) | [RFC-MACP-0001 §7.3](../rfcs/RFC-MACP-0001-core.md) |

`SessionSuspendPayload`/`SessionResumePayload`, `CommitmentPayload`'s `supersedes`/
`CommitmentRef` fields, and `SessionStartPayload.max_suspend_ms` (not exercised by the example
above, which relies on the runtime default) were all added to the envelope schema this
reconciliation window (#162/#172, #161/#171, #156/#163 respectively).

## Discovery, lifecycle, and runtime examples

Single-document examples that exercise non-transcript schemas:

| File | Schema | What it shows |
|------|--------|---------------|
| [`examples/discovery/agent_manifest.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/agent_manifest.json) | [`macp-agent-manifest.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-agent-manifest.schema.json) | agent identity, supported modes, transport endpoints |
| [`examples/discovery/mode_descriptor.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/mode_descriptor.json) | [`macp-mode-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-mode-descriptor.schema.json) | mode advertisement with message types and schema URIs |
| [`examples/discovery/policy_descriptor.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/policy_descriptor.json) | [`macp-policy-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-policy-descriptor.schema.json) | governance policy advertisement (RFC-MACP-0012) |
| [`examples/discovery/policy_descriptor_decline.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/policy_descriptor_decline.json) | [`macp-policy-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-policy-descriptor.schema.json) | `critical_objection_action: finalize_decline` — a vote-gated decline finalized on critical objection |
| [`examples/discovery/session_metadata.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/session_metadata.json) | [`macp-session-metadata.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-session-metadata.schema.json) | `SessionMetadata` returned by `GetSession` |
| [`examples/discovery/session_lifecycle_event.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/session_lifecycle_event.json) | [`macp-session-lifecycle-event.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-session-lifecycle-event.schema.json) | `SessionLifecycleEvent` emitted by `WatchSessions` |
| [`examples/discovery/run_descriptor.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/run_descriptor.json) | [`macp-run-descriptor.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-run-descriptor.schema.json) | scenario-agnostic run descriptor for a control-plane `POST /runs` |
| [`examples/discovery/agent_bootstrap.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/examples/discovery/agent_bootstrap.json) | [`macp-agent-bootstrap.schema.json`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/json/macp-agent-bootstrap.schema.json) | bootstrap payload written to `MACP_BOOTSTRAP_FILE` before the initiator agent starts |

## Example shape

The canonical field mapping and payload encoding for every Envelope in these transcripts is
defined in [RFC-MACP-0001 §10.1 (Field Mapping), §10.2 (Payload Encoding)](../rfcs/RFC-MACP-0001-core.md) —
this document does not restate it. The one repository-local convention: each transcript's
`messages` array is ordered, and that order is the replay order.

> **Note:** The policy-governed examples (`policy-decision-session.json`, `policy-registration-exchange.json`) use a simplified `transcript` array with sequence numbers (`seq`) and condensed message representations. This format is intended to illustrate governance evaluation flow rather than serve as a wire-format reference. For canonical Envelope structure, refer to the standard mode transcripts. The simplification is cosmetic only for the Envelope framing: these two examples' `rules` objects are still validated in CI against `decision-rules.schema.json` by the policy-rules extractor (see [docs/policy.md](policy.md)), so the governance rules themselves are held to the same standard as everywhere else.

## What the examples demonstrate

Across the transcripts, the examples demonstrate:

- explicit initialization and capability negotiation,
- explicit `SessionStart`,
- session-scoped mode messages,
- version binding suitable for replay,
- a terminal `Commitment` that resolves the Session,
- policy resolution, governance evaluation, and deterministic commitment decisions (RFC-MACP-0012).

The important property is not the specific business scenario in each example. It is that every bound coordination event exists as a bounded transcript with a start, a lifecycle, and a terminal message.

## Related: conformance fixtures

The examples above are illustrative. For **machine-checked** message sequences with per-message accept/reject expectations — consumed by SDK projection harnesses and the runtime conformance suite — see the canonical fixture pack in [`schemas/conformance/`](https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol/blob/main/schemas/conformance/README.md). Fixtures exist for every standards-track mode plus the `ext.multi_round.v1` extension mode, and CI validates each fixture against the fixture-format schema and lints it for internal consistency.
