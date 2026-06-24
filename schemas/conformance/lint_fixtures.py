#!/usr/bin/env python3
"""Lint the canonical MACP conformance fixtures for internal consistency.

These fixtures are the single source of truth replayed by both SDKs and the
runtime. A fixture that is internally inconsistent (e.g. an accepted message
from a non-participant) is silently wrong: SDK projection harnesses don't model
participant authorization, so the bug only surfaces against the runtime. This
linter catches that class of defect at the source, before fixtures are synced
downstream.

Run: `python schemas/conformance/lint_fixtures.py` (exits non-zero on any error).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = ("mode", "initiator", "participants", "messages", "expected_final_state")
VALID_EXPECT = {"accept", "reject"}
VALID_FINAL_STATE = {"Open", "Resolved", "Suspended", "Cancelled"}


def lint_fixture(path: Path) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for one fixture. Errors fail the build;
    warnings are advisory."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"], []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing required top-level key '{key}'")
    if errors:
        return errors, warnings

    participants = set(data["participants"])
    initiator = data["initiator"]
    if initiator not in participants:
        errors.append(f"initiator {initiator!r} is not in participants")

    final_state = data["expected_final_state"]
    if final_state not in VALID_FINAL_STATE:
        errors.append(f"expected_final_state {final_state!r} not in {sorted(VALID_FINAL_STATE)}")

    for i, msg in enumerate(data["messages"]):
        for key in ("sender", "message_type", "payload_type", "expect"):
            if key not in msg:
                errors.append(f"messages[{i}] missing '{key}'")
        expect = msg.get("expect")
        if expect not in VALID_EXPECT:
            errors.append(f"messages[{i}].expect {expect!r} not in {sorted(VALID_EXPECT)}")
        # An ACCEPTED message must come from a participant; a REJECTED message
        # may legitimately come from an outsider (that is often why it rejects).
        if expect == "accept" and msg.get("sender") not in participants:
            errors.append(
                f"messages[{i}] accepted message from non-participant {msg.get('sender')!r}"
            )
        # Documenting the expected rejection reason is recommended (lets the
        # runtime assert *why* a message rejected) but not yet universal.
        if expect == "reject" and "expected_error_code" not in msg:
            warnings.append(f"messages[{i}] reject message has no 'expected_error_code'")

    return errors, warnings


def main() -> int:
    fixtures_dir = Path(__file__).parent
    fixtures = sorted(fixtures_dir.glob("*.json"))
    if not fixtures:
        print(f"No fixtures found in {fixtures_dir}", file=sys.stderr)
        return 1

    failed = False
    warned = False
    for path in fixtures:
        errors, warnings = lint_fixture(path)
        if errors:
            failed = True
            print(f"FAIL {path.name}")
            for err in errors:
                print(f"  - error:   {err}")
        elif warnings:
            warned = True
            print(f"warn {path.name}")
        else:
            print(f"ok   {path.name}")
        for warn in warnings:
            print(f"  - warning: {warn}")

    if failed:
        print("\nConformance fixtures have consistency errors (see above).", file=sys.stderr)
        return 1
    suffix = " (with advisory warnings)" if warned else ""
    print(f"\nAll {len(fixtures)} conformance fixtures are internally consistent{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
