#!/usr/bin/env python3
"""Collect one week of adoption metrics (the roadmap's day-90 measures) from public sources.

Each ISO week (Monday to Monday, UTC) becomes one JSON row: hosted runs, registry downloads,
GitHub stars/forks and issues/PRs opened by people other than the owner and bots. Registry
APIs only return rolling windows and the hosted control plane may purge old runs, so the
weekly adoption-metrics workflow appends each row to `adoption/metrics.jsonl` on the
`adoption-data` branch; history is kept there, never on `main`.

Every source is independent: one that fails records null plus an entry in `errors`, and the
run fails only when every source failed. Only aggregates are stored (no run ids, people or IPs).

Backfill limits: GHCR totals, stars and forks are current values with no history, so they are
recorded only for the last complete week (older weeks keep what an earlier run recorded, or
null). crates.io keeps about 90 days of daily data, pypistats about 180, and hosted runs only
reach back as far as the control plane still holds them. Registries can post a day late, so
the default run re-collects the last two complete weeks.

Network-gated: run by the scheduled adoption-metrics workflow, not by `make validate`.

    python3 scripts/collect-adoption.py                     # last two complete weeks, rows to stdout
    python3 scripts/collect-adoption.py --week 2026-10-19   # the week starting that Monday
    python3 scripts/collect-adoption.py --backfill --out adoption   # every week since 2026-09-28
    python3 scripts/collect-adoption.py --fail-source npm   # prove one failing source is isolated
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ORG = "multiagentcoordinationprotocol"
OWNER_LOGINS = {"ajit-zer07"}
BOT_LOGINS = {"macp-deps-bot[bot]"}  # any other "*[bot]" login is excluded too
FIRST_WEEK = dt.date(2026, 9, 28)  # first Monday after the hosted-runs baseline (2026-09-27)
CONSOLE_RUNS = "https://console.multiagentcoordinationprotocol.io/api/proxy/macp-control-plane/runs"
USER_AGENT = "macp-adoption-metrics (https://github.com/multiagentcoordinationprotocol/multiagentcoordinationprotocol)"

PYPI = ["macp-sdk-python", "macp-mcp", "langgraph-macp", "claude-agent-sdk-macp", "macp-proto"]
NPM = [
    "macp-sdk-typescript",
    "@multiagentcoordinationprotocol/mcp",
    "@multiagentcoordinationprotocol/proto",
    "@multiagentcoordinationprotocol/langgraph",
    "@multiagentcoordinationprotocol/claude-agent-sdk",
]
CRATES = ["macp-runtime", "macp-cli", "macp-conform", "macp-modes", "macp-core", "macp-pb", "macp-proto"]
GHCR = ["macp-runtime", "macp-control-plane", "macp-ui-console", "macp-playground"]

SOURCES = ["hosted_runs", "pypi", "npm", "crates", "ghcr_total", "github"]
ROW_KEYS = ["week", "collected_at", "errors", *SOURCES, "ttfs"]
CURRENT_ONLY_GITHUB = ("stars", "forks", "stars_by_repo")

# The day-90 targets from the roadmap, shown beside the numbers in REPORT.md.
TARGETS = [
    ("Hosted showcase runs / week", "tracked from a baseline of 0"),
    ("External issues or PRs", "at least 1"),
    ("Time to first session", "10 minutes or less (console and Docker + pip)"),
]


def get(url, headers=None, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    return body.decode() if raw else json.loads(body)


def github_headers():
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return h


def iso(d):
    return dt.datetime.combine(d, dt.time(), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hosted_runs(start, end):
    counts, offset = Counter(), 0
    while True:
        q = urllib.parse.urlencode({"createdAfter": iso(start), "createdBefore": iso(end), "includeSandbox": "true",
                                    "includeArchived": "true", "limit": 200, "offset": offset})
        page = get(f"{CONSOLE_RUNS}?{q}")["data"]
        counts.update(f"{r.get('sourceKind') or 'unknown'}:{r.get('mode') or 'unknown'}" for r in page)
        if len(page) < 200:
            break
        offset += 200
        time.sleep(1)  # the proxy's read quota is per IP
    return {
        "total": sum(counts.values()),
        "showcase_live": counts["macp-playground:live"],
        "showcase_sandbox": counts["macp-playground:sandbox"],
        "by_source": dict(sorted(counts.items())),
    }


def pypi_week(pkg, start, end):
    try:
        data = get(f"https://pypistats.org/api/packages/{pkg}/overall?mirrors=false")["data"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # not published (yet)
        raise
    days = {start + dt.timedelta(days=i) for i in range((end - start).days)}
    return sum(r["downloads"] for r in data if dt.date.fromisoformat(r["date"]) in days)


def npm_week(pkg, start, end):
    last = end - dt.timedelta(days=1)
    try:
        return get(f"https://api.npmjs.org/downloads/point/{start}:{last}/{pkg}")["downloads"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def crate_week(name, start, end):
    """Downloads in the week, summed from the daily series (crates.io keeps about 90 days)."""
    try:
        data = get(f"https://crates.io/api/v1/crates/{name}/downloads")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    days = {start + dt.timedelta(days=i) for i in range((end - start).days)}
    rows = data.get("version_downloads", []) + data.get("meta", {}).get("extra_downloads", [])
    return sum(r["downloads"] for r in rows if dt.date.fromisoformat(r["date"]) in days)


def ghcr_total(image):
    """Best effort: GHCR has no download API, so read the all-time total off the package page."""
    html = get(f"https://github.com/{ORG}/{image}/pkgs/container/{image}", raw=True)
    m = re.search(r'Total downloads</span>\s*<h3[^>]*\btitle="([\d,]+)"', html)
    if not m:
        raise ValueError(f"{image}: total downloads not found on the package page")
    return int(m.group(1).replace(",", ""))


def github(start, end):
    repos, page = [], 1
    while True:
        batch = get(f"https://api.github.com/orgs/{ORG}/repos?type=public&per_page=100&page={page}", github_headers())
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    # Exclude the owner and bots in the query: they are most of the traffic, and search stops at 1000 results.
    excluded = " ".join(f"-author:{login}" for login in sorted(OWNER_LOGINS)) + \
        " -author:app/macp-deps-bot -author:app/dependabot -author:app/github-actions"
    q = urllib.parse.quote(f"org:{ORG} created:{start}..{end - dt.timedelta(days=1)} {excluded}")
    items, page = [], 1
    while True:
        res = get(f"https://api.github.com/search/issues?q={q}&per_page=100&page={page}", github_headers())
        items += res["items"]
        if page * 100 >= min(res["total_count"], 1000) or not res["items"]:
            break
        page += 1
    external = [i for i in items
                if i["user"]["login"] not in OWNER_LOGINS | BOT_LOGINS and not i["user"]["login"].endswith("[bot]")]
    return {
        "stars": sum(r["stargazers_count"] for r in repos),
        "forks": sum(r["forks_count"] for r in repos),
        "stars_by_repo": {r["name"]: r["stargazers_count"] for r in sorted(repos, key=lambda r: r["name"])
                          if r["stargazers_count"]},
        "external_issues": sum(1 for i in external if "pull_request" not in i),
        "external_prs": sum(1 for i in external if "pull_request" in i),
        "external_author_count": len({i["user"]["login"] for i in external}),
    }


def collect(start, ttfs=None, fail=(), current=True):
    """One week's row. Values that only exist as today's totals are recorded only when `current`."""
    end = start + dt.timedelta(days=7)
    row = {"week": start.isoformat(), "collected_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "errors": {}}
    sources = {
        "hosted_runs": lambda: hosted_runs(start, end),
        "pypi": lambda: {p: pypi_week(p, start, end) for p in PYPI},
        "npm": lambda: {p: npm_week(p, start, end) for p in NPM},
        "crates": lambda: {c: crate_week(c, start, end) for c in CRATES},
        "ghcr_total": lambda: {i: ghcr_total(i) for i in GHCR},
        "github": lambda: github(start, end),
    }
    if not current:
        sources["ghcr_total"] = lambda: None
    for key, fetch in sources.items():
        try:
            if key in fail:
                raise RuntimeError("forced by --fail-source")
            row[key] = fetch()
        except Exception as e:  # each source fails on its own
            row[key] = None
            row["errors"][key] = f"{type(e).__name__}: {e}"
    if not current and row["github"]:
        row["github"].update(stars=None, forks=None, stars_by_repo=None)
    row["ttfs"] = ttfs
    assert list(row) == ROW_KEYS, list(row)
    return row


def last_complete_week(today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    this_monday = today - dt.timedelta(days=today.weekday())
    return this_monday - dt.timedelta(days=7)


def monday(s):
    d = dt.date.fromisoformat(s)
    if d.weekday() != 0:
        raise argparse.ArgumentTypeError(f"{s} is not a Monday")
    return d


def merge(path, rows):
    """Replace rows for the same week and keep the file sorted. A value the new row lacks (ttfs, or a
    current-only total recorded when that week was the latest) is kept from the earlier row."""
    existing = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing[r["week"]] = r
    for r in rows:
        old = existing.get(r["week"])
        if old:
            for key in ("ttfs", "ghcr_total"):
                if r.get(key) is None and old.get(key) is not None:
                    r[key] = old[key]
            new_g, old_g = r.get("github"), old.get("github")
            if new_g and old_g:
                for key in CURRENT_ONLY_GITHUB:
                    if new_g.get(key) is None and old_g.get(key) is not None:
                        new_g[key] = old_g[key]
        existing[r["week"]] = r
    path.write_text("".join(json.dumps(existing[w], sort_keys=True) + "\n" for w in sorted(existing)))
    return [existing[w] for w in sorted(existing)]


def total(d):
    return None if d is None else sum(v for v in d.values() if v is not None)


def report(rows):
    def cell(v):
        return "—" if v is None else str(v)
    lines = ["# MACP adoption metrics", "",
             "Collected weekly by `scripts/collect-adoption.py`. Weeks run Monday to Monday, UTC. "
             "crates.io counts are inflated by CI and mirrors; GHCR is an all-time total; stars, forks and GHCR "
             "are recorded only for the week that was latest when collected.", "",
             "| Week | Hosted runs | Showcase (live) | PyPI | npm | crates.io | Stars | External issues | External PRs | TTFS |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in reversed(rows):
        h, g = r.get("hosted_runs") or {}, r.get("github") or {}
        ttfs = r.get("ttfs")
        lines.append("| " + " | ".join([
            r["week"], cell(h.get("total")), cell(h.get("showcase_live")), cell(total(r.get("pypi"))),
            cell(total(r.get("npm"))), cell(total(r.get("crates"))), cell(g.get("stars")),
            cell(g.get("external_issues")), cell(g.get("external_prs")),
            "—" if not ttfs else f"{ttfs['minutes']} min ({ttfs['path']})"]) + " |")
    lines += ["", "## Day-90 targets", ""] + [f"- **{name}:** {target}" for name, target in TARGETS]
    errs = [(r["week"], k, v) for r in rows[-4:] for k, v in r.get("errors", {}).items()]
    if errs:
        lines += ["", "## Source errors (last 4 weeks)", ""] + [f"- {w} `{k}`: {v}" for w, k, v in errs]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--week", type=monday, help="Monday that starts the week (default: the last two complete weeks)")
    ap.add_argument("--backfill", action="store_true", help=f"every week from {FIRST_WEEK} to the last complete one")
    ap.add_argument("--ttfs-minutes", type=float, help="a timed time-to-first-session run, in minutes")
    ap.add_argument("--ttfs-path", choices=["console", "docker-pip"], help="which path was timed")
    ap.add_argument("--fail-source", action="append", default=[], choices=SOURCES,
                    help="make this source fail, to check that the others still record (repeatable)")
    ap.add_argument("--out", type=Path, help="directory holding metrics.jsonl and REPORT.md (default: print rows)")
    args = ap.parse_args()
    if (args.ttfs_minutes is None) != (args.ttfs_path is None):
        ap.error("--ttfs-minutes and --ttfs-path go together")
    if args.week and args.backfill:
        ap.error("--week and --backfill are exclusive")

    last = last_complete_week()
    weeks = [args.week] if args.week else [last - dt.timedelta(weeks=1), last]
    if args.backfill:
        weeks = [FIRST_WEEK + dt.timedelta(weeks=i) for i in range((last - FIRST_WEEK).days // 7 + 1)]
    ttfs = {"minutes": args.ttfs_minutes, "path": args.ttfs_path} if args.ttfs_minutes is not None else None

    rows = []
    for i, w in enumerate(weeks):
        rows.append(collect(w, ttfs if w == weeks[-1] else None, args.fail_source, current=w == last))
        if i < len(weeks) - 1:
            time.sleep(2)

    if all(len(r["errors"]) == len(SOURCES) for r in rows):
        for r in rows:
            print(json.dumps(r, sort_keys=True))
        print("every source failed", file=sys.stderr)
        return 1

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        merged = merge(args.out / "metrics.jsonl", rows)
        (args.out / "REPORT.md").write_text(report(merged))
        print(f"wrote {len(rows)} week(s); {len(merged)} in {args.out / 'metrics.jsonl'}")
    else:
        for r in rows:
            print(json.dumps(r, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
