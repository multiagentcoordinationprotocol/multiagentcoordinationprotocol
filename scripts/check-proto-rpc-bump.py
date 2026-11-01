#!/usr/bin/env python3
"""Release guard: a proto release that changes a service RPC must bump the minor.

Policy (VERSIONING.md §8; issue #250): any proto
release that adds, removes or changes a service RPC -- in any service, core,
policy or mode -- bumps at least the MINOR version (0.1.x -> 0.2.0). Every
language package shares one version and one `proto-vX.Y.Z` tag, so the rule
covers them all. Consumers use caret requirements (`macp-proto = "0.1.13"`
accepts any 0.1.x), and Rust consumers generate service traits from whichever
macp-proto Cargo resolves: an RPC added in a patch release makes every
already-published consumer that lacks a handler stop compiling (E0046). This
happened with WhatIfReplay in 0.1.12 (macp-runtime#253).

What this script compares: the set of `service S { rpc R(...) returns (...) }`
signatures declared by every .proto file under schemas/proto, at two points.
A signature is `<package>.<Service>/<Rpc>(<stream?> <Request>) returns
(<stream?> <Response>)`; adding, removing or changing one counts as an RPC
change. Messages, fields, enums and rpc options are deliberately ignored.

Two ways to name the two points:

  git mode (what the release workflow runs):
    check-proto-rpc-bump.py --new-version 0.2.0 [--new-ref HEAD] [--prev-tag proto-v0.1.13]
  The previous tag defaults to the highest `proto-v*` tag whose version is
  strictly below --new-version. No such tag (first release) passes.

  directory mode (what the offline selftest drives):
    check-proto-rpc-bump.py --new-version 0.1.14 --old-version 0.1.13 \\
        --old-root DIR --new-root DIR
  Each root is a directory whose .proto files (recursively) are compared.

Exit codes: 0 pass, 1 policy violation, 2 usage or environment error.
Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PROTO_DIR = "schemas/proto"
TAG_PREFIX = "proto-v"

VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


def parse_version(text: str) -> tuple[int, int, int]:
    m = VERSION_RE.match(text.strip())
    if not m:
        raise ValueError(f"not a MAJOR.MINOR.PATCH version: {text!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_kind(old: tuple[int, int, int], new: tuple[int, int, int]) -> str:
    """'major', 'minor', 'patch', or 'none' (new is not above old)."""
    if new[0] > old[0]:
        return "major"
    if new[0] < old[0]:
        return "none"
    if new[1] > old[1]:
        return "minor"
    if new[1] < old[1]:
        return "none"
    return "patch" if new[2] > old[2] else "none"


# ── proto parsing ──────────────────────────────────────────────────────


def strip_comments(src: str) -> str:
    """Remove // and /* */ comments, leaving string literals intact.

    Comments are replaced by a space (block comments keep their newlines) so
    that tokens on either side never merge.
    """
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i : j + 1])
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            end = n if j < 0 else j + 2
            out.append(" " + "\n" * src.count("\n", i, end))
            i = end
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_strings(src: str) -> str:
    """Blank out string literal contents so braces inside them don't count."""
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', src)


PACKAGE_RE = re.compile(r"\bpackage\s+([\w.]+)\s*;")
SERVICE_RE = re.compile(r"\bservice\s+(\w+)\s*\{")
TYPE = r"\.?[\w.]+"
RPC_RE = re.compile(
    r"\brpc\s+(\w+)\s*\(\s*(stream\s+)?(" + TYPE + r")\s*\)"
    r"\s*returns\s*\(\s*(stream\s+)?(" + TYPE + r")\s*\)"
)


def matching_brace(src: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced braces in service block")


def parse_rpcs(src: str, origin: str = "<proto>") -> dict[str, str]:
    """Map `<pkg>.<Service>/<Rpc>` to its canonical signature string."""
    clean = strip_strings(strip_comments(src))
    pm = PACKAGE_RE.search(clean)
    pkg = pm.group(1) + "." if pm else ""
    rpcs: dict[str, str] = {}
    for sm in SERVICE_RE.finditer(clean):
        body_start = sm.end() - 1
        try:
            body_end = matching_brace(clean, body_start)
        except ValueError as exc:
            raise ValueError(f"{origin}: service {sm.group(1)}: {exc}") from None
        body = clean[body_start + 1 : body_end]
        service = pkg + sm.group(1)
        for rm in RPC_RE.finditer(body):
            name, s_in, req, s_out, resp = rm.groups()
            key = f"{service}/{name}"
            sig = (
                f"{key}({'stream ' if s_in else ''}{req.lstrip('.')}) returns "
                f"({'stream ' if s_out else ''}{resp.lstrip('.')})"
            )
            if key in rpcs:
                raise ValueError(f"{origin}: duplicate rpc {key}")
            rpcs[key] = sig
        # rpc-looking text that the signature regex could not read is an
        # error, not a silent skip: a skipped rpc is an undetected change.
        declared = len(re.findall(r"\brpc\s+\w+", body))
        parsed = len(RPC_RE.findall(body))
        if declared != parsed:
            raise ValueError(
                f"{origin}: service {service} declares {declared} rpc(s) "
                f"but only {parsed} parsed; extend RPC_RE"
            )
    return rpcs


def merge(sources: list[tuple[str, str]]) -> dict[str, str]:
    """Merge parse_rpcs over (origin, text) pairs."""
    out: dict[str, str] = {}
    for origin, text in sources:
        for key, sig in parse_rpcs(text, origin).items():
            if key in out:
                raise ValueError(f"{origin}: rpc {key} also declared elsewhere")
            out[key] = sig
    return out


# ── sources ────────────────────────────────────────────────────────────


def dir_sources(root: Path) -> list[tuple[str, str]]:
    return [
        (str(p.relative_to(root)), p.read_text(encoding="utf-8"))
        for p in sorted(root.rglob("*.proto"))
    ]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def git_sources(ref: str) -> list[tuple[str, str]]:
    names = git("ls-tree", "-r", "--name-only", ref, "--", PROTO_DIR).split()
    return [
        (f"{ref}:{name}", git("show", f"{ref}:{name}"))
        for name in sorted(names)
        if name.endswith(".proto")
    ]


def previous_tag(new: tuple[int, int, int]) -> str | None:
    best: tuple[tuple[int, int, int], str] | None = None
    for tag in git("tag", "--list", f"{TAG_PREFIX}*").split():
        try:
            v = parse_version(tag[len(TAG_PREFIX) :])
        except ValueError:
            continue
        if v < new and (best is None or v > best[0]):
            best = (v, tag)
    return best[1] if best else None


# ── comparison ─────────────────────────────────────────────────────────


def diff(old: dict[str, str], new: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for key in sorted(new.keys() - old.keys()):
        lines.append(f"  added:   {new[key]}")
    for key in sorted(old.keys() - new.keys()):
        lines.append(f"  removed: {old[key]}")
    for key in sorted(old.keys() & new.keys()):
        if old[key] != new[key]:
            lines.append(f"  changed: {old[key]}")
            lines.append(f"       to: {new[key]}")
    return lines


def check(
    old_label: str,
    old_version: str,
    old_rpcs: dict[str, str],
    new_label: str,
    new_version: str,
    new_rpcs: dict[str, str],
) -> int:
    kind = bump_kind(parse_version(old_version), parse_version(new_version))
    changes = diff(old_rpcs, new_rpcs)
    head = f"{old_label} ({old_version}) -> {new_label} ({new_version}): {kind} bump"
    if not changes:
        print(f"OK: {head}, no service RPC changed ({len(new_rpcs)} rpcs).")
        return 0
    if kind in ("major", "minor"):
        print(f"OK: {head}, service RPCs changed:")
        print("\n".join(changes))
        return 0
    m = parse_version(old_version)
    print(f"FAIL: {head}, but service RPCs changed:", file=sys.stderr)
    print("\n".join(changes), file=sys.stderr)
    print(
        f"A proto release that adds, removes or changes a service RPC must bump\n"
        f"the minor (or major) version: release {m[0]}.{m[1] + 1}.0, not {new_version}.\n"
        f"Consumers use caret requirements and Rust consumers generate service\n"
        f"traits, so an RPC in a patch release breaks already-published builds.\n"
        f"See VERSIONING.md §8 (issue #250).",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--new-version", required=True)
    ap.add_argument("--new-ref", default="HEAD", help="git mode: ref of the release")
    ap.add_argument("--prev-tag", help="git mode: override the previous proto-v* tag")
    ap.add_argument("--old-root", type=Path, help="directory mode: previous tree")
    ap.add_argument("--new-root", type=Path, help="directory mode: release tree")
    ap.add_argument("--old-version", help="directory mode: previous version")
    args = ap.parse_args(argv)

    try:
        new_v = parse_version(args.new_version)
        if args.old_root or args.new_root or args.old_version:
            if not (args.old_root and args.new_root and args.old_version):
                ap.error("directory mode needs --old-root, --new-root and --old-version")
            return check(
                str(args.old_root), args.old_version, merge(dir_sources(args.old_root)),
                str(args.new_root), args.new_version, merge(dir_sources(args.new_root)),
            )
        prev = args.prev_tag or previous_tag(new_v)
        if prev is None:
            print(f"OK: no {TAG_PREFIX}* tag below {args.new_version}; nothing to compare.")
            return 0
        return check(
            prev, prev[len(TAG_PREFIX) :], merge(git_sources(prev)),
            args.new_ref, args.new_version, merge(git_sources(args.new_ref)),
        )
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: git {' '.join(exc.cmd[1:])}: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
