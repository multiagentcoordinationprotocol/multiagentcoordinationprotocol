# Onboarding an agent

> How to add a new MACP-compliant agent to a deployment. One page, five steps.

Under the **direct-agent-auth** architecture:

- Every agent authenticates to the runtime **directly** via a Bearer credential — either a static token or a short-lived JWT (see Step 2).
- The control-plane **never** emits envelopes on behalf of agents — it is a scenario-agnostic observer.
- The initiator agent of a session calls `Send(SessionStart)` itself; non-initiator participants open their own `StreamSession` to receive events and emit their own envelopes.

This satisfies RFC-MACP-0004 §4 (sender MUST be derived from authenticated identity) and RFC-MACP-0001 §5.3 (no MACP bypass). The reference deployment (`macp-playground`) documents its own side of this — bootstrap files, JWT minting, policy registration — in [`docs/direct-agent-auth.md`](https://github.com/multiagentcoordinationprotocol/macp-playground/blob/main/docs/direct-agent-auth.md); the SDKs document the agent-side patterns (initiator/non-initiator code, the `expected_sender` guardrail, `session.cancel()`) in [`macp-sdk-python/docs/guides/direct-agent-auth.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/docs/guides/direct-agent-auth.md) and [`macp-sdk-typescript/docs/guides/authentication.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/docs/guides/authentication.md).

This page shows two ways to get a Bearer credential to your agent — pick whichever matches your scenario-producing tier:

- **Static bearer tokens** (Steps 2A/3A) — works with any runtime deployment, no extra services required.
- **On-demand JWT minting** (Steps 2B/3B) — how the reference `macp-playground` deployment does it today; nothing to register per agent.

---

## Prerequisites

- A running MACP runtime with its gRPC endpoint reachable from your agent process (e.g., `runtime.internal:50051`).
- **Static bearer path:** admin access to the runtime's environment (`MACP_AUTH_TOKENS_JSON` / `MACP_AUTH_TOKENS_FILE`).
- **JWT path:** admin access to the runtime's JWT resolver config (`MACP_AUTH_ISSUER`, `MACP_AUTH_AUDIENCE`, `MACP_AUTH_JWKS_URL`) and, if using `macp-playground`, to its `MACP_AUTH_SERVICE_URL` setting — see that repo's [deployment checklist](https://github.com/multiagentcoordinationprotocol/macp-playground/blob/main/docs/direct-agent-auth.md#deployment-checklist).
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
- Must match the `sender` the runtime resolves for this agent's credential (step 2).

---

## Step 2 — Configure the runtime's auth resolver

This is a one-time deployment setting, not a per-agent step — the runtime can run either or both resolvers at once (JWT-shaped tokens route to the JWT resolver, opaque tokens to the static one).

### Option A — Static bearer tokens

Generate a strong random token:

```bash
openssl rand -hex 32
```

Add an entry to the runtime's `MACP_AUTH_TOKENS_JSON`. The runtime loads this map once at boot (`crates/macp-auth/src/security.rs`, `AuthConfig::from_env`):

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

Redeploy the runtime (or wait for hot-reload, if your deployment supports it). Continue to **Step 3, Option A**.

### Option B — JWT verification (the `macp-playground` reference deployment)

Point the runtime at a JWKS source instead of a static map — no per-agent entry needed here, the runtime derives `sender` from each JWT's `sub` claim:

```bash
export MACP_AUTH_ISSUER=<issuer>
export MACP_AUTH_AUDIENCE=<audience>       # default: macp-runtime
export MACP_AUTH_JWKS_URL=<auth-service>/.well-known/jwks.json
```

The default algorithm allowlist is RS256/ES256; HS256 requires an explicit `MACP_AUTH_JWT_ALGS=HS256` opt-in. Continue to **Step 3, Option B**.

---

## Step 3 — Get the Bearer credential to your agent process

### Option A — Static bearer (your own scenario-producing tier)

Inject the token you generated in Step 2A into your agent's bootstrap however your own tier does configuration — an env var, a secrets manager entry, whatever fits. The only requirement is that the agent's bootstrap ends up with the correct Bearer token in its runtime-auth field (e.g. `runtime.bearerToken`).

### Option B — `macp-playground` (automatic, nothing to register)

The playground mints a short-lived RS256 JWT per agent spawn — `AuthTokenMinterService` calls `POST /tokens` on the auth-service configured via `MACP_AUTH_SERVICE_URL`, scoped from the agent's role (`can_start_sessions`, `allowed_modes`) with optional per-sender overrides via `MACP_AUTH_SCOPES_JSON`, and bakes the result into the agent's bootstrap file. There is no static token map to maintain and no per-agent entry to add. See the "AUTH-2" section of [`docs/direct-agent-auth.md`](https://github.com/multiagentcoordinationprotocol/macp-playground/blob/main/docs/direct-agent-auth.md#auth-2--on-demand-jwt-minting) for the minting flow, caching, and TTL constraints.

---

## Step 4 — Register the agent in the scenario catalog (`macp-playground` only)

Skip this step if you're wiring an agent into your own scenario-producing tier — it's specific to the `macp-playground` reference implementation, which needs two files:

1. Add an entry to `src/example-agents/example-agent-catalog.service.ts`:

```ts
{
  agentRef: 'my-new-agent',
  name: 'My New Agent',
  role: 'evaluator',
  description: 'What this agent evaluates.',
  framework: 'python', // or 'langgraph' | 'langchain' | 'crewai' | 'node'
  supportedScenarioRefs: ['fraud/high-value-new-device@1.0.0'],
}
```

2. Create a matching manifest at `agents/manifests/my-new-agent.json`:

```json
{
  "id": "my-new-agent",
  "name": "My New Agent",
  "framework": "python",
  "version": "1.0.0",
  "entrypoint": { "type": "python_file", "value": "agents/my_new_agent/main.py" },
  "host": { "python": "python3", "cwd": ".", "env": {}, "startupTimeoutMs": 30000 },
  "macp": { "role": "evaluator", "supportedMessageTypes": ["Evaluation"], "capabilities": [] }
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

Both SDKs auto-bind a local HTTP `POST <cancelCallback.path>` listener for you — you don't need to hand-roll one. The control-plane's UI-triggered cancel calls that listener; the SDK responds by calling `session.cancel(reason)` on the runtime with its own identity. Runtime enforces RFC-MACP-0001 §7.2 — only the initiator (or a policy-delegated role) may cancel. See the SDK guides linked above if you need to override the default cancel behavior.

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
| Agent logs `UNAUTHENTICATED` on first `send` | Runtime doesn't recognize the credential | Static bearer: check Step 2A — token and sender in `MACP_AUTH_TOKENS_JSON` must match, then redeploy. JWT: check Step 2B — issuer/audience/JWKS config on the runtime. |
| Agent's bootstrap is missing its Bearer credential | Credential never reached the agent | Static bearer: check Step 3A. `macp-playground`: check its `auth_mint_failure` logs and that `MACP_AUTH_SERVICE_URL` is reachable (Step 3B). |
| Initiator's SessionStart is rejected with `Forbidden` | `can_start_sessions: false` on the identity | Static bearer: flip it to `true` in `MACP_AUTH_TOKENS_JSON`. JWT: check the minted token's `allowed_modes`/`can_start_sessions` scopes. |
| Agent sends envelopes but they're rejected with `sender does not match identity` | Sender string mismatch | The string in `bootstrap.participant.participantId`, the envelope's `sender` field, and the runtime-resolved identity `sender` must all be identical byte-for-byte. Check for stray `agent://` prefixes. |
| Cancel from UI doesn't take effect | Missing or unreachable cancel-callback listener | Verify the SDK's auto-bound listener is reachable from the control-plane and `bootstrap.cancelCallback` is populated. |

---

## See also

- [`macp-playground/docs/direct-agent-auth.md`](https://github.com/multiagentcoordinationprotocol/macp-playground/blob/main/docs/direct-agent-auth.md) — reference deployment's bootstrap production, JWT minting, and policy registration
- [`macp-sdk-python/docs/guides/direct-agent-auth.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-python/blob/main/docs/guides/direct-agent-auth.md) and [`macp-sdk-typescript/docs/guides/authentication.md`](https://github.com/multiagentcoordinationprotocol/macp-sdk-typescript/blob/main/docs/guides/authentication.md) — agent-side patterns
- `schemas/json/macp-run-descriptor.schema.json` — control-plane `POST /runs` contract
- `schemas/json/macp-agent-bootstrap.schema.json` — agent bootstrap contract
- `schemas/json/macp-session-metadata.schema.json` — session metadata runtime returns
- RFC-MACP-0004 §3 (Authentication) + §4 (Authorization) + §11 (Multi-tenancy)
- RFC-MACP-0001 §7 (Session lifecycle) + §7.2 (Cancellation authority)
