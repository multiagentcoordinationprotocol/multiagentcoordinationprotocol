#!/usr/bin/env python3
"""Build the versioned conformance bundle attached to each spec release.

Release-time, and `make conformance-bundle` locally. Stdlib only, like the
other CI scripts. Embedders (for example Seam, which drives macp_modes::step
in-process) pin ONE tarball and ONE checksum instead of copying the fixture
files one by one.

What goes in is declared by schemas/conformance-bundle.json:

  include  glob patterns, relative to the repo root; every match is bundled
           at its repo path, so a bundled path IS the spec path.
  exclude  glob patterns removed from the include set (tooling, not data).
  moved    {"old/path": "new/path"} for every bundled path that was moved or
           renamed. Each entry stays for at least one minor release.

Output, in --out (default dist/):

  macp-conformance-<version>.tar.gz   one top-level dir macp-conformance-<version>/
                                      holding the files, MANIFEST.json and
                                      moved-files.json
  SHA256SUMS                          sha256sum format, covering the tarball

The tarball is reproducible: sorted entries, mtime 0, uid/gid 0, and gzip
without a timestamp, so the same tree always yields the same checksum.

Path stability: with --previous-manifest (the MANIFEST.json of the last
released bundle), every path in it must still be bundled or be a key in
`moved` whose target is bundled. Otherwise the build fails, because an
embedder's pin check would silently lose a file.
"""

import argparse
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "schemas" / "conformance-bundle.json"
BUNDLE_FORMAT = 1


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def collect(config: dict) -> list[str]:
    paths: set[str] = set()
    for pattern in config["include"]:
        matches = [p for p in ROOT.glob(pattern) if p.is_file()]
        if not matches:
            fail(f"include pattern {pattern!r} matches no files")
        paths.update(p.relative_to(ROOT).as_posix() for p in matches)
    for pattern in config.get("exclude", []):
        paths.difference_update(
            p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern)
        )
    return sorted(paths)


def check_moves(paths: list[str], moved: dict) -> None:
    bundled = set(paths)
    for old, new in moved.items():
        if old in bundled:
            fail(f"moved-files entry {old!r} is still bundled at its old path")
        if new not in bundled:
            fail(f"moved-files entry {old!r} -> {new!r}: target is not bundled")


def check_previous(paths: list[str], moved: dict, previous: Path) -> None:
    prev = json.loads(previous.read_text())
    bundled = set(paths)
    lost = [
        p for p in sorted(prev["files"])
        if p not in bundled and moved.get(p) not in bundled
    ]
    if lost:
        fail(
            "paths in the previous bundle are neither bundled nor in "
            f"schemas/conformance-bundle.json `moved`: {lost}"
        )


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def add_bytes(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = 0
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True, help="bundle version, e.g. 0.1.12")
    ap.add_argument("--out", default="dist", help="output directory (default dist/)")
    ap.add_argument("--previous-manifest", type=Path,
                    help="MANIFEST.json of the last released bundle")
    args = ap.parse_args()

    config = json.loads(CONFIG.read_text())
    moved = config.get("moved", {})
    paths = collect(config)
    check_moves(paths, moved)
    if args.previous_manifest:
        check_previous(paths, moved, args.previous_manifest)

    contents = {p: (ROOT / p).read_bytes() for p in paths}
    manifest = {
        "bundle_format": BUNDLE_FORMAT,
        "version": args.version,
        "spec_commit": git_commit(),
        "files": {p: hashlib.sha256(b).hexdigest() for p, b in contents.items()},
    }

    top = f"macp-conformance-{args.version}"
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for p in paths:
            add_bytes(tar, f"{top}/{p}", contents[p])
        add_bytes(tar, f"{top}/MANIFEST.json",
                  (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        add_bytes(tar, f"{top}/moved-files.json",
                  (json.dumps(moved, indent=2, sort_keys=True) + "\n").encode())

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tarball = out / f"{top}.tar.gz"
    with open(tarball, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0) as gz:
            gz.write(raw.getvalue())
    digest = hashlib.sha256(tarball.read_bytes()).hexdigest()
    (out / "SHA256SUMS").write_text(f"{digest}  {tarball.name}\n")
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"[OK] {tarball} ({len(paths)} files) sha256 {digest}")


if __name__ == "__main__":
    main()
