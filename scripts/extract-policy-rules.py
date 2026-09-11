#!/usr/bin/env python3
"""Extract every policy `rules` object in the repository, paired with its mode.

Nothing else in the repository validates a `rules` object against its mode's rule
schema: both containers -- macp-policy-descriptor.schema.json and
schemas/conformance/schema.json -- declare `rules` as a bare {"type": "object"}
with no $ref, and lint_fixtures.py only type-checks that it is an object
(issue #100). This script finds the instances so validate-json.sh can check them.

A `rules` object is located by its container, not by a hardcoded path: any JSON
object carrying BOTH a `rules` object and a sibling `mode` string is a policy
descriptor, wherever it sits. That reaches all four nesting shapes on disk --
top-level in examples/discovery/, `$.policy.rules` in conformance fixtures,
`$.policy_definition.rules` and `$.request.body.policy_descriptor.rules` in
examples/ -- and, unlike a path list, it keeps working when a new shape appears.

It also reaches fenced ```json blocks in rfcs/ and docs/, which NOTHING in the
repository reads today.

Output: one TSV line per instance -- <mode>\t<written-file>\t<label> -- with the
rules object written into the directory given as argv[1]. Mode "*" is emitted as
mode `*` so the caller can log the skip rather than dropping it silently.
"""
import json
import os
import re
import sys

ROOT = os.environ.get("MACP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Directories walked for JSON instances. schemas/json/ is deliberately absent:
# it holds schemas, not instances, and its tests/ fixtures are bare rules
# objects with no mode sibling (they are covered by the assert-fail loops).
JSON_DIRS = ["examples", "schemas/conformance"]
MD_DIRS = ["rfcs", "docs"]

# Case-insensitive on the info string: a ```JSON fence that this regex skipped would
# drop its instances silently, and the run would stay green with a lower count.
FENCE = re.compile(r"^```json\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL | re.IGNORECASE)


def find_descriptors(node, path, out, problems):
    """Yield (json-pointer-ish path, mode, rules) for every policy descriptor.

    A `rules` object with no string `mode` beside it is reported as a PROBLEM, not
    skipped: silently dropping it is how coverage evaporates while the build stays
    green -- rename `mode` to `modes` and the instance simply stops being checked.
    """
    if isinstance(node, dict):
        rules, mode = node.get("rules"), node.get("mode")
        matched = isinstance(rules, dict) and isinstance(mode, str)
        if matched:
            out.append((path or "$", mode, rules))
        elif isinstance(rules, dict):
            problems.append(
                "%s: has a `rules` object but no string `mode` beside it "
                "(mode=%r) -- a policy descriptor must carry both"
                % (path or "$", mode)
            )
        for k, v in node.items():
            # Do not descend into the `rules` value we just matched: a rules object
            # that happened to carry its own `rules`+`mode` would be counted twice.
            if matched and k == "rules":
                continue
            find_descriptors(v, "%s.%s" % (path, k), out, problems)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find_descriptors(v, "%s[%d]" % (path, i), out, problems)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: extract-policy-rules.py <output-dir>\n")
        return 2
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)

    found = []
    problems = []

    for d in JSON_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _, filenames in os.walk(base):
            for fn in sorted(filenames):
                if not fn.endswith(".json") or fn.endswith(".schema.json"):
                    continue
                if fn == "schema.json":
                    continue  # the fixture-format schema, not an instance
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                try:
                    with open(full, encoding="utf-8") as fh:
                        doc = json.load(fh)
                except (OSError, ValueError) as exc:
                    sys.stderr.write("  [X] %s: unreadable JSON: %s\n" % (rel, exc))
                    return 1
                hits = []
                find_descriptors(doc, "", hits, problems)
                for ptr, mode, rules in hits:
                    found.append((rel, ptr, mode, rules))

    for d in MD_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _, filenames in os.walk(base):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                with open(full, encoding="utf-8") as fh:
                    text = fh.read()
                for i, m in enumerate(FENCE.finditer(text)):
                    block = m.group(1)
                    line = text[: m.start()].count("\n") + 1
                    try:
                        doc = json.loads(block)
                    except ValueError:
                        # Not every json fence is a whole document -- but one that
                        # mentions "rules" and does not parse is a silent-loss vector,
                        # not a prose snippet. Fail loudly rather than skip it.
                        if '"rules"' in block:
                            problems.append(
                                "%s:%d: fence mentions \"rules\" but is not parseable JSON"
                                % (rel, line)
                            )
                        continue
                    hits = []
                    find_descriptors(doc, "", hits, problems)
                    for ptr, mode, rules in hits:
                        found.append(("%s:%d" % (rel, line), ptr, mode, rules))

    if problems:
        for prob in problems:
            sys.stderr.write("  [X] %s\n" % prob)
        return 1

    for idx, (src, ptr, mode, rules) in enumerate(found):
        target = os.path.join(outdir, "rules_%03d.json" % idx)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(rules, fh, indent=2)
        label = src if ptr in ("$", "") else "%s %s" % (src, ptr)
        sys.stdout.write("%s\t%s\t%s\n" % (mode, target, label))

    return 0


if __name__ == "__main__":
    sys.exit(main())
