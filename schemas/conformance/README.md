# Conformance Fixtures

Canonical test fixtures for validating MACP SDK projections and runtime session handling.

## Purpose

These JSON fixtures define message sequences for each coordination mode. They are consumed by:

- **Runtime** — validates session state machine transitions and commitment logic
- **SDKs** — validates projection state tracking (transcript, phase, commitment fields)

## Fixture Format

Each fixture is a JSON object with:

```json
{
  "mode": "macp.mode.decision.v1",
  "initiator": "agent://lead",
  "participants": ["agent://lead", "agent://peer"],
  "mode_version": "1.0.0",
  "configuration_version": "config.default",
  "policy_version": "",
  "messages": [
    {
      "sender": "agent://lead",
      "message_type": "Proposal",
      "payload_type": "decision.Proposal",
      "payload": { "proposalId": "p-1", "option": "deploy", "rationale": "ready" },
      "expect": "accept"
    }
  ],
  "expected_final_state": "SESSION_STATE_RESOLVED"
}
```

### Fields

| Field | Used By | Description |
|-------|---------|-------------|
| `mode` | Both | Mode identifier |
| `initiator` | Both | Session initiator |
| `participants` | Both | Session participants |
| `messages` | Both | Ordered message sequence |
| `messages[].expect` | Both | `"accept"` or `"reject"` — whether the runtime accepts the message |
| `messages[].payload_type` | Both | `"{mode_short}.{MessageType}"` format for payload encoding |
| `expected_final_state` | Runtime | Expected session state after replay |
| `expected_mode_state` | Runtime | Mode-specific state assertions (optional) |

SDKs should only replay messages where `expect == "accept"` through their projections.

## Syncing Fixtures

Downstream repos sync via Makefile:

```bash
make sync-fixtures        # Copy from this directory
make sync-fixtures-local  # Copy from sibling checkout
```

CI in each repo verifies no drift against these canonical fixtures.

## Adding New Fixtures

1. Add the JSON file here in the RFC repo
2. Ensure it follows the format above
3. Run `make sync-fixtures` in downstream repos
4. Verify conformance tests pass in both SDKs and the Runtime
