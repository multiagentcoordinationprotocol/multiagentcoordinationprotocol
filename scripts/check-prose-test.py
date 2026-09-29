#!/usr/bin/env python3
"""Regression proof for issue #129: an unreadable file must not crash check-prose.py.

Copies the real repo tree, makes one file inside the copy unreadable, then runs
the real scripts/check-prose.py (unmodified, not copied) against that tree via
MACP_ROOT -- the same seam the script already exposes for this purpose. Asserts
the run reaches its own summary line for all 8 checks rather than dying with an
uncaught traceback partway through.

POSIX only (uses os.chmod permission bits); this repo's CI runs on Linux/macOS
runners only, so no cross-platform handling is added here.

Not run as part of a pytest suite -- this repo has no test framework dependency
anywhere; every existing check is a small stdlib-only driver script wired into
the Makefile, and this follows that convention.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_PROSE = os.path.join(REPO_ROOT, "scripts", "check-prose.py")


def main():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        # chmod 000 does not block root from reading a file, so the crash path
        # this test exists to exercise would never trigger -- skip rather than
        # report a false positive.
        print("[SKIP] running as root; chmod 000 would not block reads")
        return 0

    tmp_root = tempfile.mkdtemp(prefix="macp-prose-test-")
    try:
        tree = os.path.join(tmp_root, "repo")
        shutil.copytree(REPO_ROOT, tree, symlinks=True)

        target = None
        rfcs_dir = os.path.join(tree, "rfcs")
        for fn in sorted(os.listdir(rfcs_dir)):
            if fn.endswith(".md"):
                target = os.path.join(rfcs_dir, fn)
                break
        if target is None:
            print("[FAIL] no .md file found under the copied rfcs/ to make unreadable")
            return 1

        os.chmod(target, 0o000)
        try:
            env = dict(os.environ)
            env["MACP_ROOT"] = tree
            proc = subprocess.run(
                [sys.executable, CHECK_PROSE],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            # Restore before cleanup so shutil.rmtree can remove the tree even
            # on platforms where rmtree can't unlink a 000-mode file it owns.
            os.chmod(target, 0o644)

        stdout, stderr = proc.stdout, proc.stderr

        if "Traceback (most recent call last)" in stderr:
            print("[FAIL] check-prose.py crashed with an uncaught traceback:")
            print(stderr)
            return 1

        if "prose check failure(s) across 8 check(s)" not in stdout and "[OK] All 8 prose checks passed" not in stdout:
            print("[FAIL] check-prose.py did not reach its own summary line for "
                  "all 8 checks -- run did not complete:")
            print("--- stdout ---")
            print(stdout)
            print("--- stderr ---")
            print(stderr)
            return 1

        if proc.returncode == 0:
            print("[FAIL] expected a nonzero exit (the unreadable file itself is a "
                  "reportable failure), got 0")
            return 1

        print("[OK] check-prose.py ran all 8 checks to completion with an "
              "unreadable file present, and reported it as a failure rather "
              "than crashing")
        return 0
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
