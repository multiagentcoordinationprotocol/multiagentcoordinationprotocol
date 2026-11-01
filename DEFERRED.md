# Deferred

Items worth remembering that do not meet the bar for an issue (bug, blocker, security issue, design flaw, regression). One line each.


- multi_round: governance policy is never evaluated for ext.multi_round.v1 (runtime calls neither check_commitment_authority nor enforce_commitment_policy); documented as current behaviour in #241, not a bug.
- multi_round: no conformance fixture covers a non-participant Contribute (runtime multi_round.rs:178-181).
- A2A codec: the taskId/Task check is skipped when session_id is empty (Signals). Behaviour matches the reference mapper; no vector pins it (macp-sdk-python #213 note).
- A2A ErrorInfo with a non-string reason: the reference mapper passes it through and both SDKs return "". No vector pins it; align the mapper if a vector is ever added.
- A2A codec in Rust: no consumer today. seam-runtime#1342 is deferred until a design partner asks for it; if that happens, it needs a Rust port or an adapter-layer bridge (seam-runtime-7e, 2026-11-01).
- multi_round Contribute decoding (parse_contribute_value rev 3): the 460-case runtime-captured corpus is copied SDK to SDK (Py #216, TS #235) with no drift gate. Candidate: move it to a schemas/conformance dir owned by the spec.
- IMPLEMENTATIONS.md closing paragraph says only the Python SDK replays the conformance fixtures; TypeScript does too (flagged in the #249 review).
- SessionStart retry after the runtime evicts a finished session would open a new session; no RFC bounds the duplicate-tracking window (found in the #251 review, unverified against runtime retention).
