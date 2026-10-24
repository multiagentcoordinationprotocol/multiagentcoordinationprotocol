# Mode-as-tool schemas

> **Status:** Non-normative. Generated from the mode protos; the protos and the mode RFCs are authoritative.

Each file here lets an LLM agent emit one MACP mode message as a tool call. There is one file per mode message type (`<mode>.<MessageType>.json`), so an agent gets a separate tool for each move it can make in a session: Decision `Proposal`, `Evaluation`, `Objection` and `Vote`; Proposal `Proposal`, `CounterProposal`, `Accept`, `Reject` and `Withdraw`; and so on for Task, Handoff, Quorum and the `ext.multi_round.v1` extension mode.

**Do not edit these files.** `scripts/gen-tool-schemas.py` writes them from `schemas/proto/macp/modes/*/v1/*.proto`. To change a description, edit the proto comment and run:

```bash
make gen-tool-schemas
```

`make proto-compile` (and CI) regenerates them in memory and fails if the committed files differ.

## Shape

Every file has three keys, the shape Anthropic tool use takes as-is:

```json
{
  "name": "macp_decision_vote",
  "description": "Vote: records a participant's preference on a proposal ... Sent as message_type Vote in mode macp.mode.decision.v1.",
  "input_schema": {
    "type": "object",
    "properties": { "proposal_id": { "description": "...", "type": "string" }, "...": {} },
    "required": ["proposal_id", "vote", "reason"],
    "additionalProperties": false
  }
}
```

- `name` is `macp_<mode>_<message_type>` in snake_case. When the message type repeats the mode name, the repeat is dropped (`TaskRequest` becomes `macp_task_request`). Every name matches `^[a-zA-Z0-9_-]{1,64}$`.
- `description` is the first paragraph of the payload message's proto comment, followed by the `message_type` and mode identifier the tool call maps to.
- `input_schema` is the payload message. Field descriptions are the field's proto comment. A proto comment line `Values: A | B | C` becomes an `enum`.

The tool input is the **payload** only, written in the canonical JSON mapping ([RFC-MACP-0001 Section 10](../../../rfcs/RFC-MACP-0001-core.md)). Your code wraps it in an Envelope: it sets `mode`, `message_type`, `session_id`, `sender` and `message_id`, and the sender's identity comes from your transport authentication, never from the model. `index.json` maps each tool `name` to its file, mode identifier, `message_type` and protobuf payload type, so the wrapping can be table-driven.

Type mapping:

| Proto type | JSON Schema | Note |
|---|---|---|
| `string` | `string` | Empty is `""`, never omitted or `null` (RFC-MACP-0001 Section 10.7) |
| `bytes` | `string` | Base64 (RFC-MACP-0001 Section 10.3). Empty is `""` |
| `bool` | `boolean` | |
| `double` | `number` | |
| `uint32`, `int64` | `integer` | Written as a JSON number, as the example transcripts do |
| `repeated T` | `array` of `T` | Empty is `[]` |

Every field is listed in `required`, because proto3 fields here have no presence and the canonical JSON mapping writes empty strings as `""` rather than leaving them out. The model sends the empty value for a field it has nothing for.

The schemas use only `type`, `description`, `enum`, `items`, `properties`, `required` and `additionalProperties: false`. That subset is accepted by Anthropic strict tool use and by OpenAI strict function calling, so you can turn strict mode on without changing a schema.

## Using them with Anthropic

Pass the file contents as an entry in `tools`. To guarantee the input matches the schema, add `"strict": true` to the entry:

```json
{ "tools": [ { "name": "macp_decision_vote", "description": "...", "input_schema": { "...": "..." }, "strict": true } ] }
```

The `tool_use` block's `input` is the payload object.

## Using them with OpenAI

Move `input_schema` to `parameters` and wrap the result. Chat Completions takes:

```json
{ "type": "function", "function": { "name": "macp_decision_vote", "description": "...", "parameters": { "...": "..." }, "strict": true } }
```

The Responses API takes the same keys without the inner `function` object: `{"type": "function", "name": ..., "description": ..., "parameters": ..., "strict": true}`. The call's `arguments` string parses to the payload object.

## What is not here

- **Commitment.** Every mode terminates with the Core `macp.v1.CommitmentPayload`, not a mode payload, so it has no file here. Its schema is the `CommitmentPayload` entry in [`macp-envelope.schema.json`](../macp-envelope.schema.json). Commitment authority is restricted by the mode and the bound policy, so give an agent a Commitment tool only when it holds that authority.
- **Who may send what.** A schema says what a message looks like, not whether the sender may send it now. The runtime enforces sender authorization, ordering and policy, and it rejects what the schema cannot see, such as a vote after commitment or a second ballot.
- **Runtime-only fields.** `HandoffAccept.implicit` is in the schema because it is in the proto, but its description states that clients must send `false`. The runtime sets `true` only on the synthetic accept it emits itself.
