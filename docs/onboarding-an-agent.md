# Onboarding an agent

> How to add a new MACP-compliant agent to a deployment. One page, five steps.

Under the **direct-agent-auth** architecture (see `ui-console/plans/direct-agent-auth.md`):

- Every agent authenticates to the runtime **directly** via Bearer token.
- The control-plane **never** emits envelopes on behalf of agents — it is a scenario-agnostic observer.
- The initiator agent of a session calls `Send(SessionStart)` itself; non-initiator participants open their own `StreamSession` to receive events and emit their own envelopes.

This page shows how to onboard agent **N** in a static-token deployment (i.e., before Phase 6 JWT federation lands). Once Phase 6 ships, step 2 changes to "issue a JWT via the auth service"; the rest stays the same.

---

## Prerequisites

- A running MACP runtime with its gRPC endpoint reachable from your agent process (e.g., `runtime.internal:50051`).
- Admin access to the runtime's environment (`MACP_AUTH_TOKENS_JSON`).
- Admin access to the scenario-producing tier (e.g., examples-service `EXAMPLES_SERVICE_AGENT_TOKENS_JSON`).
- Either `macp-sdk-python >= 0.2.0` (PyPI) or `macp-sdk-typescript >= 0.2.0` (npm) available to your agent runtime.

---

## Step 1 — Decide the agent's sender id

The **sender** is the plain-string identity the runtime binds to this agent (RFC-MACP-0001 §6). Bare names are fine:

```
risk-agent
fraud-agent
my-new-agent
```

The `agent://…` prefix is a convention used by some integration tests, not a protocol requirement.

**Rules:**
- Must be non-empty.
- Must be unique across all agents that can talk to the same runtime identity registry.
- Must match the `sender` field in the runtime's identity entry for this agent (step 2).

---

## Step 2 — Generate a Bearer token and register the identity on the runtime

Generate a strong random token:

```bash
openssl rand -hex 32
```

Add an entry to the runtime's `MACP_AUTH_TOKENS_JSON`. The runtime loads this map once at boot (`runtime/src/security.rs:109-157`):

```json
{
  "tokens": [
    { "token": "<existing-agents>", "sender": "risk-agent",  "can_start_sessions": true },
    { "token": "<existing-agents>", "sender": "fraud-agent", "can_start_sessions": true },
    // add:
    {
      "token": "<your-new-token>",
      "sender": "my-new-agent",
      "can_start_sessions": true,
      "allowed_modes": ["macp.mode.decision.v1"],
      "max_open_sessions": 10
    }
  ]
}
```

**Capability guidance:**

| Flag | Set it when… |
|------|-------------|
| `can_start_sessions: true` | The agent may be a session initiator for at least one scenario. |
| `allowed_modes: [...]` | You want to restrict which modes the agent may send in. Empty/absent = unrestricted. |
| `max_open_sessions: N` | You want per-agent concurrency caps. |
| `can_manage_mode_registry: true` | The agent manages registered modes/policies (rare; usually false). |

Redeploy the runtime (or wait for hot-reload, if your deployment supports it).

---

## Step 3 — Register the token on the scenario-producing tier

In `examples-service/.env` (or equivalent), add an entry to `EXAMPLES_SERVICE_AGENT_TOKENS_JSON`:

```json
{
  "risk-agent":    "<existing token>",
  "fraud-agent":   "<existing token>",
  "my-new-agent":  "<your-new-token>"
}
```

The examples-service injects `runtime.bearerToken` into each agent's bootstrap at spawn time by looking up the sender in this map.

If you are running in a different scenario-producing tier, inject the equivalent env var using that tier's conventions. The only requirement is that the agent's bootstrap ends up with the correct Bearer token in `runtime.bearerToken`.

---

## Step 4 — Register the agent in the scenario catalog

In `examples-service/src/example-agents/example-agent-catalog.service.ts`, add an entry:

```ts
{
  agentRef: 'my-new-agent',
  framework: 'python' /* or 'langgraph' | 'langchain' | 'crewai' | 'node' */,
  role: 'evaluator',
  entrypoint: 'agents/my_new_agent/main.py', // or 'src/example-agents/runtime/my-new-agent.worker.ts'
  bootstrap: { strategy: 'external' },
  supportedScenarioRefs: ['fraud/high-value-new-device@1.0.0'],
}
```

Then add the agent to the scenario's `participants` list in its YAML.

---

## Step 5 — Pick an SDK and wire the agent loop

### Python

```python
import os
from macp_sdk import MacpClient, AuthConfig, DecisionSession, new_session_id
from macp_worker_sdk import load_bootstrap

bootstrap = load_bootstrap()
auth = AuthConfig.for_bearer(
    os.environ["MACP_RUNTIME_TOKEN"],
    expected_sender=bootstrap.participant.participant_id,
)

client = MacpClient(
    target=os.environ["MACP_RUNTIME_ADDRESS"],
    secure=os.environ.get("MACP_RUNTIME_TLS", "true").lower() == "true",
    auth=auth,
)
client.initialize()

session = DecisionSession(client, session_id=bootstrap.run.session_id, auth=auth)

if bootstrap.initiator is not None:
    # Initiator path — emit SessionStart, then kickoff.
    session.start(
        intent=bootstrap.initiator.session_start.intent,
        participants=bootstrap.initiator.session_start.participants,
        ttl_ms=bootstrap.initiator.session_start.ttl_ms,
        mode_version=bootstrap.initiator.session_start.mode_version,
        configuration_version=bootstrap.initiator.session_start.configuration_version,
        policy_version=bootstrap.initiator.session_start.policy_version,
    )
    stream = session.open_stream()
    if bootstrap.initiator.kickoff is not None:
        session.propose(bootstrap.initiator.kickoff.payload)  # or send raw envelope
else:
    # Non-initiator — just open the stream and react to events.
    stream = session.open_stream()

for envelope in stream.responses():
    # handle Proposal / Evaluation / Vote / Commitment / ...
    ...
```

### TypeScript

```ts
import { MacpClient, Auth, DecisionSession, newSessionId } from 'macp-sdk-typescript';
import { loadBootstrap } from './bootstrap';

const bootstrap = loadBootstrap();
const auth = Auth.bearer(process.env.MACP_RUNTIME_TOKEN!, {
  expectedSender: bootstrap.participant.participantId,
});

const client = new MacpClient({
  address: process.env.MACP_RUNTIME_ADDRESS!,
  secure: process.env.MACP_RUNTIME_TLS === 'true',
  auth,
});
await client.initialize();

const session = new DecisionSession(client, { sessionId: bootstrap.run.sessionId, auth });

if (bootstrap.initiator) {
  await session.start(bootstrap.initiator.sessionStart);
  const stream = session.openStream();
  if (bootstrap.initiator.kickoff) {
    await session.propose(bootstrap.initiator.kickoff.payload);
  }
  for await (const envelope of stream.responses()) {
    // handle events
  }
} else {
  const stream = session.openStream();
  for await (const envelope of stream.responses()) {
    // handle events
  }
}
```

### Cancellation (Option A — RFC-pure default)

Expose a local HTTP `POST <cancelCallback.path>` endpoint from your agent. The control-plane's UI-triggered cancel calls it; your agent responds by calling `session.cancel(reason)` on the runtime with its own identity. Runtime enforces RFC-MACP-0001 §7.2 — only the initiator (or a policy-delegated role) may cancel. See `examples-service/src/example-agents/runtime/cancel-callback-server.ts` for a reference implementation.

---

## Verify

1. Launch a scenario that includes your agent.
2. Watch the runtime logs — your agent's envelopes should show `sender=<your-agent-id>`.
3. Watch the control-plane's run event feed — no `UNAUTHENTICATED` errors.
4. If the agent is the initiator: runtime logs show `SessionStart accepted, initiator_sender=<your-agent-id>`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Agent logs `UNAUTHENTICATED` on first `send` | Runtime doesn't know the token | Check step 2 — token and sender in `MACP_AUTH_TOKENS_JSON` must exactly match. Redeploy runtime. |
| Agent throws `bootstrap.runtime.bearerToken is required` | Token map missing the sender | Check step 3 — add entry to `EXAMPLES_SERVICE_AGENT_TOKENS_JSON`. |
| Initiator's SessionStart is rejected with `Forbidden` | `can_start_sessions: false` on the runtime identity | Flip it to `true` in the runtime's `MACP_AUTH_TOKENS_JSON` entry. |
| Agent sends envelopes but they're rejected with `sender does not match identity` | Sender string mismatch | The string in `bootstrap.participant.participantId`, the envelope's `sender` field, and the runtime's identity `sender` field must all be identical byte-for-byte. Check for stray `agent://` prefixes. |
| Cancel from UI doesn't take effect | Missing `cancelCallback` or unreachable | Verify the callback is exposed from the agent and reachable from the control-plane. Verify `bootstrap.cancelCallback` is populated. |

---

## See also

- `ui-console/plans/direct-agent-auth.md` — full architecture + invariants + RFC justification
- `schemas/json/macp-run-descriptor.schema.json` — control-plane `POST /runs` contract
- `schemas/json/macp-agent-bootstrap.schema.json` — agent bootstrap contract
- `schemas/json/macp-session-metadata.schema.json` — session metadata runtime returns
- RFC-MACP-0004 §3 (Authentication) + §4 (Authorization) + §11 (Multi-tenancy)
- RFC-MACP-0001 §7 (Session lifecycle) + §7.2 (Cancellation authority)
