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
  "expected_final_state": "Resolved"
}
```

### Fields

| Field | Used By | Description |
|-------|---------|-------------|
| `mode` | Both | Mode identifier |
| `initiator` | Both | Session initiator. **Must be a member of `participants`.** |
| `participants` | Both | Session participants. Must include the initiator and every `accept` sender. |
| `messages` | Both | Ordered message sequence |
| `messages[].sender` | Both | Sender identity. For `accept` messages must be a participant; `reject` messages may come from outsiders. |
| `messages[].expect` | Both | `"accept"` or `"reject"` — whether the runtime accepts the message |
| `messages[].payload_type` | Both | `"{mode_short}.{MessageType}"` format for payload encoding |
| `policy` | Runtime | Optional inline `PolicyDescriptor` (`policy_id`, `mode`, `schema_version`, `rules`) the harness registers before `SessionStart`, so a bound (non-`none`) voting algorithm is reachable. `policy_version` must match its `policy_id`. Absent ⇒ default policy. |
| `messages[].expected_error_code` | Runtime | For `reject` messages, the error code the runtime should return (recommended) |
| `expected_final_state` | Both | Terminal state: `Open`, `Resolved`, `Suspended`, or `Cancelled`. `Resolved` ⇒ a commitment was emitted. |
| `expected_resolution` | Both | Commitment field assertions (`action`, `mode_version`, `configuration_version`, `outcome_positive`) when `Resolved` |
| `expected_mode_state` | Both | Mode-specific assertions: `phase`, `votes` (per proposal/sender), proposal/offer dispositions |

Notes:
- SDKs replay only `accept` messages through their projections (reject-path
  fixtures replay their accepted *prefix*).
- `vote` values are normalized to **uppercase** (`APPROVE` / `REJECT` /
  `ABSTAIN`); fixtures must use the uppercase form.
- Proto `bytes` payload fields (e.g. `context`) are written as plain strings and
  UTF-8 encoded by the harnesses.

## Source of truth & enforcement

This directory is the **single source of truth**. The hierarchy is:
**RFC prose ▸ runtime behavior ▸ these fixtures ▸ SDK copies.** When a fixture
disagrees with the RFC or the runtime, the fixture is wrong — fix it here.

Enforcement (all wired into CI, runs on every PR):

- **This repo** lints the fixtures for internal consistency:
  `python3 schemas/conformance/lint_fixtures.py` (initiator + every `accept`
  sender must be a participant; schema/expect/final-state validity).
- **Each SDK** runs `make verify-fixtures`, which fails the build if its vendored
  copy differs byte-for-byte from this canonical set, plus deepened conformance
  harnesses that assert transcript, commitment/resolution (incl.
  `outcome_positive`), `phase`, and `votes`.

## Syncing Fixtures

Downstream repos sync via Makefile:

```bash
make sync-fixtures     # Copy canonical fixtures into tests/conformance/
make verify-fixtures   # Fail if the local copy has drifted (CI gate)
```

## Adding or Changing Fixtures

1. Edit the JSON here in the spec repo (this is the only place fixtures are authored).
2. `python3 schemas/conformance/lint_fixtures.py` — must pass.
3. `make sync-fixtures` in **both** SDKs; review `git diff tests/conformance/`.
4. Conformance tests must pass in **both SDKs and the runtime** before the change is done.
