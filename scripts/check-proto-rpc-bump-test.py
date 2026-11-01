#!/usr/bin/env python3
"""Regression proof that check-proto-rpc-bump.py rejects what it promises.

Same spirit as scripts/check-envelope-coverage-test.py: build synthetic
inputs, run the REAL unmodified scripts/check-proto-rpc-bump.py against them
as a subprocess, and assert on its exit code and message. Nothing here reads
or mutates the repository's own protos or git history, and nothing touches
the network, so it runs inside `make validate`.

Each CASE writes an "old" and a "new" schemas tree into a temp directory and
runs the checker in directory mode with an old and a new version. A final
case builds a throwaway git repository with two `proto-v*` tags and runs the
checker in git mode, so the tag-resolution path ("highest proto-v* tag below
the new version") is exercised too.

Stdlib only, no test framework. Run:
`python3 scripts/check-proto-rpc-bump-test.py` (exits non-zero on any miss).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check-proto-rpc-bump.py"

BASE = """syntax = "proto3";
package demo.v1;

message PingRequest {}
message PingResponse {}
message WatchRequest {}
message WatchResponse {}

service DemoService {
  rpc Ping(PingRequest) returns (PingResponse);
  rpc Watch(WatchRequest) returns (stream WatchResponse);
}
"""

ADDED_RPC = BASE.replace(
    "  rpc Watch(",
    "  rpc Extra(PingRequest) returns (PingResponse);\n  rpc Watch(",
)

MESSAGE_ONLY = BASE.replace(
    "message PingRequest {}",
    "message PingRequest {\n  string note = 1;\n}\nmessage Unused { int32 x = 1; }\n"
    "enum Colour { COLOUR_UNSPECIFIED = 0; COLOUR_RED = 1; }",
)

CHANGED_SIGNATURE = BASE.replace(
    "rpc Ping(PingRequest) returns (PingResponse);",
    "rpc Ping(PingRequest) returns (WatchResponse);",
)

STREAM_ADDED = BASE.replace(
    "rpc Ping(PingRequest)", "rpc Ping(stream PingRequest)"
)

REMOVED_RPC = BASE.replace(
    "  rpc Watch(WatchRequest) returns (stream WatchResponse);\n", ""
)

# Same RPC set as BASE, re-spelled: comments everywhere (including ones that
# contain rpc-shaped text and braces), multi-line declarations, an options
# block, and a string literal holding a fake rpc and a brace.
REFORMATTED = """syntax = "proto3";
// service Fake { rpc Ghost(A) returns (B); }
package demo.v1;

message PingRequest {}
message PingResponse {}
message WatchRequest {}
message WatchResponse {}

/* block comment: rpc Phantom(PingRequest) returns (PingResponse); { */
service DemoService {
  // rpc Commented(PingRequest) returns (PingResponse);
  rpc
    Ping (
      PingRequest   // inline comment
    )
    returns
    ( PingResponse ) {
    option deprecated = false;
  }
  /* multi
     line */ rpc Watch(WatchRequest)
      returns (stream
               WatchResponse);
}

message Doc { string s = 1 [json_name = "rpc Fake(A) returns (B) }"]; }
"""

# A commented-out RPC added in a patch release is not an RPC change.
COMMENTED_ADD = BASE.replace(
    "  rpc Watch(",
    "  // rpc Extra(PingRequest) returns (PingResponse);\n"
    "  /* rpc Extra2(PingRequest) returns (PingResponse); */\n  rpc Watch(",
)

# A second service in a second file (mode/policy services count too).
SECOND_FILE = """syntax = "proto3";
package demo.policy.v1;
import "demo.proto";
service PolicyService {
  rpc Check(demo.v1.PingRequest) returns (demo.v1.PingResponse);
}
"""

# (name, old files, old version, new files, new version, exit, expected text)
CASES = [
    ("added rpc + patch bump fails",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": ADDED_RPC}, "0.1.14",
     1, "added:   demo.v1.DemoService/Extra(PingRequest) returns (PingResponse)"),
    ("added rpc + patch bump names the right release",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": ADDED_RPC}, "0.1.14",
     1, "release 0.2.0, not 0.1.14"),
    ("added rpc + minor bump passes",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": ADDED_RPC}, "0.2.0",
     0, "minor bump, service RPCs changed"),
    ("added rpc + major bump passes",
     {"demo.proto": BASE}, "0.9.3", {"demo.proto": ADDED_RPC}, "1.0.0",
     0, "major bump, service RPCs changed"),
    ("added rpc + minor bump that skips ahead passes",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": ADDED_RPC}, "0.3.1",
     0, "minor bump"),
    ("message/field/enum-only change + patch bump passes",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": MESSAGE_ONLY}, "0.1.14",
     0, "patch bump, no service RPC changed (2 rpcs)"),
    ("changed response type + patch bump fails",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": CHANGED_SIGNATURE}, "0.1.14",
     1, "to: demo.v1.DemoService/Ping(PingRequest) returns (WatchResponse)"),
    ("added stream keyword + patch bump fails",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": STREAM_ADDED}, "0.1.14",
     1, "to: demo.v1.DemoService/Ping(stream PingRequest) returns (PingResponse)"),
    ("removed rpc + patch bump fails",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": REMOVED_RPC}, "0.1.14",
     1, "removed: demo.v1.DemoService/Watch(WatchRequest) returns (stream WatchResponse)"),
    ("comments, multi-line rpcs, options and strings parse to the same set",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": REFORMATTED}, "0.1.14",
     0, "patch bump, no service RPC changed (2 rpcs)"),
    ("reformatted old -> added rpc still caught",
     {"demo.proto": REFORMATTED}, "0.1.13", {"demo.proto": ADDED_RPC}, "0.1.14",
     1, "added:   demo.v1.DemoService/Extra"),
    ("commented-out rpc + patch bump passes",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": COMMENTED_ADD}, "0.1.14",
     0, "no service RPC changed (2 rpcs)"),
    ("new service in a second file + patch bump fails",
     {"demo.proto": BASE}, "0.1.13",
     {"demo.proto": BASE, "policy/policy.proto": SECOND_FILE}, "0.1.14",
     1, "added:   demo.policy.v1.PolicyService/Check(demo.v1.PingRequest)"),
    ("unchanged rpcs + patch bump passes",
     {"demo.proto": BASE}, "0.1.13", {"demo.proto": BASE}, "0.1.14",
     0, "no service RPC changed"),
    ("unparseable rpc is an error, not a silent skip",
     {"demo.proto": BASE}, "0.1.13",
     {"demo.proto": BASE.replace("rpc Ping(PingRequest)", "rpc Ping(PingRequest, X)")},
     "0.2.0", 2, "only 1 parsed"),
]


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True, text=True, cwd=cwd,
    )
    return r.returncode, r.stdout + r.stderr


def git_mode_cases(tmp: Path) -> tuple[list[tuple[str, int, str, list[str]]], Path]:
    """Build a two-tag repo; return (name, exit, text, args) cases run in it."""
    repo = tmp / "repo"
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
    }

    def g(*a: str) -> None:
        subprocess.run(["git", *a], cwd=repo, env=env, check=True, capture_output=True)

    proto = repo / "schemas" / "proto" / "demo.proto"
    proto.parent.mkdir(parents=True)
    g("init", "-q")
    for text, tag in ((BASE, "proto-v0.1.9"), (BASE, "proto-v0.1.10"), (ADDED_RPC, None)):
        proto.write_text(text, encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "--allow-empty", "-m", tag or "add rpc")
        if tag:
            g("tag", tag)
    # A tag ABOVE the release must not be picked as "previous".
    g("tag", "proto-v0.3.0")
    return [
        # 0.1.10 must win over 0.1.9 (numeric, not lexical, ordering).
        ("git mode: picks highest tag below (0.1.10), patch fails", 1,
         "proto-v0.1.10 (0.1.10) -> HEAD (0.1.11): patch bump", ["--new-version", "0.1.11"]),
        ("git mode: same change as a minor passes", 0,
         "proto-v0.1.10 (0.1.10) -> HEAD (0.2.0): minor bump", ["--new-version", "0.2.0"]),
        ("git mode: --prev-tag override", 0,
         "proto-v0.1.9 (0.1.9) -> proto-v0.1.10 (0.1.10)",
         ["--new-version", "0.1.10", "--new-ref", "proto-v0.1.10", "--prev-tag", "proto-v0.1.9"]),
        ("git mode: no tag below means nothing to compare", 0,
         "nothing to compare", ["--new-version", "0.0.1"]),
    ], repo


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for i, (name, old, old_v, new, new_v, want_rc, want) in enumerate(CASES):
            old_root, new_root = tmp / f"c{i}" / "old", tmp / f"c{i}" / "new"
            write_tree(old_root, old)
            write_tree(new_root, new)
            rc, out = run([
                "--new-version", new_v, "--old-version", old_v,
                "--old-root", str(old_root), "--new-root", str(new_root),
            ])
            ok = rc == want_rc and want in out
            failures += not ok
            print(f"{'ok  ' if ok else 'MISS'} {name}")
            if not ok:
                print(f"     want exit {want_rc} and {want!r}; got exit {rc}:\n{out}")

        cases, repo = git_mode_cases(tmp)
        for name, want_rc, want, args in cases:
            rc, out = run(args, cwd=repo)
            ok = rc == want_rc and want in out
            failures += not ok
            print(f"{'ok  ' if ok else 'MISS'} {name}")
            if not ok:
                print(f"     want exit {want_rc} and {want!r}; got exit {rc}:\n{out}")

    total = len(CASES) + 4
    if failures:
        print(f"FAIL: {failures} of {total} check-proto-rpc-bump cases missed", file=sys.stderr)
        return 1
    print(f"OK: all {total} check-proto-rpc-bump cases behaved as promised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
