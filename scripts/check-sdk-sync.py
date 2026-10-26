#!/usr/bin/env python3
"""Check that macp-sdk-python and macp-sdk-typescript vendor the same spec files as this repo.

Both SDKs copy the conformance fixtures, the commitment-hash and receipt vectors, the parity contract
and the OpenTelemetry semantic-conventions registry into their own tests. This compares the git blob SHA of every vendored copy on each SDK's
`main` with the file in this checkout, so a fixture that reached one SDK but not the other
(or reached neither) fails here instead of drifting silently.

Network-gated: run by the scheduled sdk-sync workflow, not by `make validate`.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDKS = ["macp-sdk-python", "macp-sdk-typescript"]
ORG = "multiagentcoordinationprotocol"

# spec directory -> where both SDKs vendor it, and which files count
MAPPINGS = [
    ("schemas/conformance", "tests/conformance", lambda p: p.suffix == ".json" and p.name != "schema.json"),
    ("schemas/conformance/cmt-hash", "tests/vectors/cmt-hash", lambda p: p.suffix == ".json"),
    ("schemas/conformance/receipt", "tests/vectors/receipt", lambda p: p.suffix == ".json"),
    ("schemas/parity", "tests/parity", lambda p: p.name == "contract.json"),
    ("schemas/otel", "tests/otel", lambda p: p.name == "macp-semconv.json"),
]


def blob_sha(path):
    return subprocess.run(["git", "hash-object", str(path)], capture_output=True, text=True, check=True).stdout.strip()


def sdk_tree(repo):
    headers = {"User-Agent": "macp-sdk-sync-check", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    url = f"https://api.github.com/repos/{ORG}/{repo}/git/trees/main?recursive=1"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return {e["path"]: e["sha"] for e in json.load(r)["tree"] if e["type"] == "blob"}


def main():
    trees = {repo: sdk_tree(repo) for repo in SDKS}
    problems, checked = [], 0
    for spec_dir, sdk_dir, wanted in MAPPINGS:
        spec = {p.name: blob_sha(p) for p in sorted((ROOT / spec_dir).iterdir()) if p.is_file() and wanted(p)}
        for repo, tree in trees.items():
            vendored = {Path(k).name: v for k, v in tree.items()
                        if str(Path(k).parent) == sdk_dir and wanted(Path(k))}
            for name, sha in spec.items():
                checked += 1
                if name not in vendored:
                    problems.append(f"{repo}: missing {sdk_dir}/{name}")
                elif vendored[name] != sha:
                    problems.append(f"{repo}: {sdk_dir}/{name} differs from {spec_dir}/{name}")
            for name in sorted(set(vendored) - set(spec)):
                problems.append(f"{repo}: {sdk_dir}/{name} has no counterpart in {spec_dir}")

    for p in problems:
        print("FAIL " + p)
    if problems:
        print(f"\n{len(problems)} problem(s): the SDKs are out of sync with the spec or each other")
        return 1
    print(f"all {checked} vendored copies across {len(SDKS)} SDKs match the spec")
    return 0


if __name__ == "__main__":
    sys.exit(main())
