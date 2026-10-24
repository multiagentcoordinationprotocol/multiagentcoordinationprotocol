# Quickstart

Run a real MACP session on your machine in about five minutes. You start the reference runtime in Docker, then three agents use the Python SDK to propose, evaluate, vote and commit a binding decision.

**No install:** open the [showcase](https://console.multiagentcoordinationprotocol.io/showcase) in the hosted console. It starts a real Decision session among rule-based agents (no LLM is called) and shows the run graph, the Decision panel and a timeline you can scrub back through. It finishes in about ten seconds.

To run one yourself, you need Docker and **Python 3.11 or later**.

## 1. Start the runtime

```bash
docker run -p 50051:50051 -e MACP_ALLOW_INSECURE=1 -e MACP_MEMORY_ONLY=1 \
  ghcr.io/multiagentcoordinationprotocol/macp-runtime:0.9.0
```

`MACP_ALLOW_INSECURE=1` allows plaintext gRPC and development identities, and `MACP_MEMORY_ONLY=1` keeps state in memory. Both are for local use only: without authentication configured, the runtime refuses to start unless `MACP_ALLOW_INSECURE=1` is set. For a real deployment, see [Deployment](deployment.md).

## 2. Install the Python SDK

```bash
pip install macp-sdk-python
```

## 3. Run a decision

Save this as `first_session.py` and run `python first_session.py`:

```python
from macp.v1.envelope_pb2 import SessionState
from macp_sdk import AuthConfig, DecisionSession, MacpClient

client = MacpClient(target="127.0.0.1:50051", allow_insecure=True,  # local dev only
                    auth=AuthConfig.for_dev_agent("coordinator"))

session = DecisionSession(client)
session.start(intent="pick a deployment plan",
              participants=["coordinator", "alice", "bob"], ttl_ms=60_000)
session.propose("p1", "deploy v2.1", rationale="tests passed")
session.evaluate("p1", "APPROVE", confidence=0.94, reason="low risk",
                 sender="alice", auth=AuthConfig.for_dev_agent("alice"))
session.vote("p1", "APPROVE", reason="ship it",
             sender="bob", auth=AuthConfig.for_dev_agent("bob"))

winner = session.decision_projection.majority_winner()
session.commit(action="deployment.approved",
               authority_scope="release-management", reason=f"winner={winner}")

meta = session.metadata().metadata
print("winner:", winner)
print("state:", SessionState.Name(meta.state), "mode:", meta.mode)
client.close()
```

Expected output (the SDK also logs a one-line warning about the insecure channel to stderr):

```text
winner: p1
state: SESSION_STATE_RESOLVED mode: macp.mode.decision.v1
```

## What just happened

1. `coordinator` opened a **Coordination Session** in the Decision Mode with a bounded TTL and three declared participants. Binding coordination happens only inside a session like this ([RFC-MACP-0001 §5](../rfcs/RFC-MACP-0001-core.md)).
2. `alice` and `bob` acted under their own identities. With `MACP_ALLOW_INSECURE=1` a development identity is just the sender name. In production, every sender is authenticated ([RFC-MACP-0004](../rfcs/RFC-MACP-0004-security.md)).
3. The runtime accepted each message into the session's append-only history, in order.
4. The `Commitment` resolved the session. `RESOLVED` is terminal: nothing can reopen or change it. The commitment carries the mode, configuration and policy versions, so replaying the same history reproduces the same outcome ([RFC-MACP-0003](../rfcs/RFC-MACP-0003-determinism.md)).

## Next steps

- [Modes](modes.md): the other four standard modes (Proposal, Task, Handoff, Quorum).
- [Architecture](architecture.md): the two planes, sessions and the envelope.
- The TypeScript SDK: `npm install macp-sdk-typescript` (see its [README](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript#readme) for the current install steps).
- [Conformance](conformance.md): what it means for an implementation to conform.

## Appendix: talk to the runtime with grpcurl

The image does not enable gRPC reflection, so pass the protos from a checkout of this repository:

```bash
grpcurl -plaintext -import-path schemas/proto -proto macp/v1/core.proto \
  -d '{"supported_protocol_versions":["1.0"]}' \
  127.0.0.1:50051 macp.v1.MACPRuntimeService/Initialize

grpcurl -plaintext -import-path schemas/proto -proto macp/v1/core.proto \
  127.0.0.1:50051 macp.v1.MACPRuntimeService/ListModes
```

`Initialize` returns the runtime's name, version and capabilities. `ListModes` lists the five standard modes.
