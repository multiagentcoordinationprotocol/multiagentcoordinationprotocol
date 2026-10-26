#!/usr/bin/env python3
"""Check that every install line we advertise resolves on its public registry.

Scans the spec README and quickstart, plus the SDK and MCP-server READMEs (fetched from GitHub),
for `pip install`/`uvx`, `npm install`/`npm i -g`/`npx -y`, `cargo add`/`cargo install` and `ghcr.io/...:tag` references, then asks
PyPI, npmjs, crates.io and GHCR whether each one exists. No credentials are used, so a
line that only resolves with a token fails here, which is the point.

Network-gated: run by the scheduled install-lines workflow, not by `make validate`.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ["README.md", "docs/quickstart.md"]
REMOTE = [
    "https://raw.githubusercontent.com/multiagentcoordinationprotocol/macp-sdk-python/main/README.md",
    "https://raw.githubusercontent.com/multiagentcoordinationprotocol/macp-sdk-typescript/main/README.md",
    "https://raw.githubusercontent.com/multiagentcoordinationprotocol/macp-mcp/main/README.md",
    "https://raw.githubusercontent.com/multiagentcoordinationprotocol/macp-mcp-typescript/main/README.md",
]

PIP = re.compile(r"(?:pip install|uvx) ([A-Za-z][A-Za-z0-9_.\-]*)(?:==([0-9][\w.\-]*))?")
NPM = re.compile(r"(?:npm (?:install|i)(?: -g)?|npx -y) ((?:@[\w.\-]+/)?[A-Za-z][\w.\-]*)(?:@([0-9][\w.\-]*))?")
CARGO = re.compile(r"cargo (?:add|install) ([\w\-]+)(?:@([0-9][\w.\-]*))?")
GHCR = re.compile(r"ghcr\.io/([\w.\-]+/[\w.\-]+):([\w.\-]+)")


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "macp-install-check", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def pypi(name, version):
    data = get(f"https://pypi.org/pypi/{name}/json")
    return version is None or version in data["releases"]


def npm(name, version):
    data = get(f"https://registry.npmjs.org/{name.replace('/', '%2f')}")
    return version is None or version in data.get("versions", {})


def crates(name, version):
    data = get(f"https://crates.io/api/v1/crates/{name}")
    return version is None or any(v["num"] == version for v in data["versions"])


def ghcr(repo, tag):
    token = get(f"https://ghcr.io/token?scope=repository:{repo}:pull")["token"]
    get(f"https://ghcr.io/v2/{repo}/manifests/{tag}", {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json",
    })
    return True


CHECKS = [("pip", PIP, pypi), ("npm", NPM, npm), ("cargo", CARGO, crates), ("ghcr", GHCR, ghcr)]


def main():
    sources = {p: (ROOT / p).read_text() for p in LOCAL}
    for url in REMOTE:
        with urllib.request.urlopen(url, timeout=30) as r:
            sources[url] = r.read().decode()

    seen, failures = set(), []
    for origin, text in sources.items():
        for kind, pattern, check in CHECKS:
            for name, version in pattern.findall(text):
                key = (kind, name, version or None)
                if key in seen:
                    continue
                seen.add(key)
                label = f"{kind} {name}" + (f" {version}" if version else "")
                try:
                    ok = check(name, version or None)
                except (urllib.error.URLError, KeyError, ValueError) as e:
                    ok, label = False, f"{label} ({e})"
                print(("ok   " if ok else "FAIL ") + label + f"  [{origin}]")
                if not ok:
                    failures.append(label)

    if not seen:
        print("no install lines found; the patterns no longer match the docs")
        return 1
    if failures:
        print(f"\n{len(failures)} advertised install line(s) do not resolve publicly")
        return 1
    print(f"\nall {len(seen)} advertised install lines resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
