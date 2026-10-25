# Where MACP Fits

MACP covers one job: getting several agents to a **binding, replayable outcome** that anyone can check. Examples are a vote, a quorum approval, a negotiated offer, a delegated task or a transfer of responsibility. Every claim below about another protocol links to that protocol's own specification or repository. Claims about MACP link to its RFCs.

## The thesis

Agent protocols today cover two jobs well:

- **An agent reaching tools and context.** The [Model Context Protocol](https://modelcontextprotocol.io/specification/2026-07-28/architecture) (MCP) "provides a protocol focused on context exchange and sampling coordination between clients and servers". Each client talks to exactly one server.
- **One agent talking to another.** [A2A](https://a2a-protocol.org/latest/specification/) (latest released version 1.0.0) is "an open standard designed to facilitate communication and interoperability" between independent agent systems. Its unit of work is a task with a lifecycle (submitted, working, input-required, completed, failed and so on).

Neither defines how a *group* of agents reaches a decision that binds them. A June 2026 survey of MCP, A2A, ACP, ANP and ERC-8004 found that "voting and dissent preservation are universally absent across all five protocols", and that "deliberation is absent or at most partial". It concluded that group governance is a missing layer *above* these standards, not a missing feature within them ([Kang and Diponegoro, *Governance Gaps in Agent Interoperability Protocols: What MCP, A2A, and ACP Cannot Express*, arXiv:2606.31498](https://arxiv.org/abs/2606.31498)).

MACP is meant to be that layer. It adds:

- **Explicit, bounded sessions.** Binding coordination happens only inside a session that has declared participants, a mode and a TTL. Everything outside a session is a non-binding Signal ([RFC-MACP-0001 §5](../rfcs/RFC-MACP-0001-core.md)).
- **A terminal, append-only lifecycle.** Once a session is `RESOLVED`, `EXPIRED` or `CANCELLED`, nothing reopens it, and accepted messages never change ([RFC-MACP-0001 §7](../rfcs/RFC-MACP-0001-core.md)).
- **Replay integrity.** The same accepted history under the same mode, configuration and policy versions produces the same outcome ([RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md)).
- **A verifiable commitment.** Any party can recompute the canonical commitment hash from the outcome and check it ([RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md)). Appendix A of that RFC defines an informative, portable decision receipt that can be verified offline.
- **Coordination modes.** There are five standard ways to converge: Decision, Proposal, Task, Handoff and Quorum ([RFC-MACP-0007](../rfcs/RFC-MACP-0007-decision-mode.md) through [RFC-MACP-0011](../rfcs/RFC-MACP-0011-quorum-mode.md)), plus declarative governance policy ([RFC-MACP-0012](../rfcs/RFC-MACP-0012-policy.md)).

## Comparison

| | MCP | A2A | ACP (IBM) | Framework-native orchestration | MACP |
|---|---|---|---|---|---|
| **Main job** | an agent or app reaching tools, resources and prompts | one agent delegating a task to another | agent-to-agent messaging; now merged into A2A | coordinating agents inside one program | a group of agents converging on a binding outcome |
| **Unit of interaction** | client–server request | task | run | whatever the framework defines | coordination session with a declared mode |
| **Group decision (vote, quorum)** | not defined | not defined | not defined | written by the application | standard modes (Decision, Quorum) |
| **Outcome is terminal and replayable** | n/a | task has terminal states; no replay guarantee is specified | n/a | depends on the application | yes ([RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md)) |
| **Outcome is independently verifiable** | n/a | not specified | n/a | depends on the application | canonical commitment hash ([RFC-MACP-0013](../rfcs/RFC-MACP-0013-commitment-hash.md)) |
| **Status** | [2026-07-28 spec](https://modelcontextprotocol.io/specification/2026-07-28/architecture) | [1.0.0](https://a2a-protocol.org/latest/specification/) | [archived Aug 2025](https://github.com/i-am-bee/acp); "now part of A2A" | — | 1.0.0-draft, single maintainer ([README](../README.md#project-status)) |

The MCP, A2A and ACP "not defined" cells follow the survey above and those protocols' own specifications. The framework column describes a category rather than any one product: when coordination lives inside one framework, the outcome is whatever that program returns, and other parties can check it only as far as the application lets them.

## Using MACP alongside them

MACP does not replace any of these. It sits next to them:

- **With MCP.** A MACP session decides *whether* a tool may be invoked. The resulting Commitment authorizes the call, and MCP carries it out ([architecture §14](architecture.md#14-integration-tools-prompts-and-external-capability-layers)).
- **With A2A.** An A2A task can be the work that a MACP Task or Handoff session delegates. MACP records who agreed to own it and when. Agents that already speak A2A can also take part in MACP sessions over A2A itself, through the extension binding in [RFC-MACP-0014](../rfcs/RFC-MACP-0014-a2a-binding.md).
- **With frameworks.** A framework can drive participants from one process, while MACP holds the binding record. MACP can also be embedded in-process as a library rather than spoken over gRPC (see [Embedding MACP as a library](../README.md#embedding-macp-as-a-library) and the reference runtime's [`docs/embedding.md`](https://github.com/multiagentcoordinationprotocol/macp-runtime/blob/main/docs/embedding.md)).

## When not to use MACP

- **One agent calling tools.** Use MCP. A session adds nothing when there is no group to converge.
- **Fire-and-forget delegation.** If one agent hands a task to another and nobody needs a binding record of the agreement, A2A alone is simpler.
- **Streaming, chat or telemetry.** That traffic is ambient. In MACP it would be Signals, which never bind, so there is no reason to route it through MACP.
- **Everything lives in one process you control, and nobody outside needs to check the outcome.** Framework-native orchestration is less machinery. MACP becomes useful once the outcome must be audited, replayed or trusted by someone who did not run the code.
- **You need a mature, multi-vendor standard today.** MACP is a draft with a single maintainer and one reference runtime ([README, Project status](../README.md#project-status); [IMPLEMENTATIONS.md](../IMPLEMENTATIONS.md)). Pin the versioned Protobuf packages and plan for change.

## Try it

The [Quickstart](quickstart.md) runs a real Decision session in about five minutes.
