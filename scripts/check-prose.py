#!/usr/bin/env python3
"""Check RFC prose against the artifacts that implement it (issue #107).

`make validate` checks that JSON validates, protos compile, indexes are in sync,
and fixtures are internally consistent. It never checks that an RFC's prose is
TRUE, or that two RFCs agree. During the schema_version 3 work `make validate`
stayed green while RFC-MACP-0012 made four false claims about its own canonical
schemas, while two RFCs gave opposite answers about the same tally, and while a
justification rested on a section that does not exist.

"Is this paragraph true?" is not a lint rule. These six checks are the fraction
that is mechanical:

  1. line-number anchors   -- `(:102)`-style citations drift on every edit above
                              them. Cite by heading; headings do not drift.
  2. schema_version agreement -- the set is enumerated in seven places across
                              markdown, .proto comments, and JSON Schema -- six of
                              them prose, the seventh the descriptor schema's own
                              `enum`. lint_fixtures.py is the source of truth they
                              are all compared against, not one of the seven.
                              Nothing kept them in step; #99 fixed the first six by
                              hand. The seventh (#115) is structural rather than
                              prose: the descriptor schema's own `enum`, which
                              ENFORCES the set the other six merely describe.
  3. RFC cross-references  -- a `§N.M` pointing at a section that does not exist
                              is mechanically detectable.
  4. cited terms present   -- a sentence citing an RFC for a claim, where the cited
                              RFC never mentions the term, is detectable. That is the
                              shape of #103: "Abstentions are excluded (RFC-MACP-0004)"
                              against an RFC containing the word zero times.
  5. RFC version census    -- README hand-maintains a per-RFC version roll-call
                              that nothing verifies. #99 had to correct it by hand,
                              and the quorum/error-code work invalidated it twice more.
  6. own check count       -- two documents and this docstring each claim how many
                              checks run here -- five claims across three files --
                              and nothing held them in step: README said four while
                              docs/policy.md said five and five ran (#119). The count
                              is derived from main()'s AST, so it cannot go stale.
                              This check counts itself.

Reporting follows check-indexes.sh: accumulate every failure and report them all,
rather than dying on the first. One run should surface the whole list.
"""
import ast
import json
import os
import re
import sys

ROOT = os.environ.get("MACP_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FAILURES = []
CHECKS = 0

# Spelled number words, for prose that writes counts as words. Module scope
# because check_version_census and check_check_count both read it.
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
         12: "twelve", 13: "thirteen", 14: "fourteen"}


def fail(msg):
    FAILURES.append(msg)


def rel(p):
    return os.path.relpath(p, ROOT)


def walk(subdir, ext):
    base = os.path.join(ROOT, subdir)
    for dirpath, _, filenames in os.walk(base):
        for fn in sorted(filenames):
            if fn.endswith(ext):
                yield os.path.join(dirpath, fn)


# --------------------------------------------------------------------------
# 1. Line-number anchors
# --------------------------------------------------------------------------
# The pattern is deliberately `\(:[0-9]` and not the `\(:\d+\)` originally
# proposed: the latter misses `(:31, :58)` and `(:62-64)`, which are exactly the
# forms that were on disk.
# No close-paren requirement: `(:42,\n:58)` split across two lines evaded a
# `\(:[0-9][^)]*\)` pattern entirely, while AC1's own grep still found it.
ANCHOR = re.compile(r"\(:[0-9]")


def check_line_anchors():
    global CHECKS
    print("-- Line-number anchors (cite by heading, not by line) --")
    hits = 0
    for sub, ext in (("schemas", ".json"), ("schemas", ".md"), ("rfcs", ".md"),
                     ("docs", ".md"), ("registries", ".md")):
        for path in walk(sub, ext):
            for i, line in enumerate(open(path, encoding="utf-8"), 1):
                for m in ANCHOR.finditer(line):
                    hits += 1
                    fail("%s:%d: line-number anchor %s -- cite the heading instead; "
                         "line numbers drift on every edit above them"
                         % (rel(path), i, m.group(0)))
    CHECKS += 1
    print("  [OK] no line-number anchors" if not hits
          else "  [X] %d line-number anchor(s)" % hits)


# --------------------------------------------------------------------------
# 2. schema_version enumeration agreement
# --------------------------------------------------------------------------
def check_schema_versions():
    global CHECKS
    print("-- schema_version enumerations agree --")
    before_failures = len(FAILURES)
    canonical = None
    src = None
    lint = os.path.join(ROOT, "schemas/conformance/lint_fixtures.py")
    if os.path.isfile(lint):
        m = re.search(r"VALID_POLICY_SCHEMA_VERSIONS\s*=\s*\{([^}]*)\}",
                      open(lint, encoding="utf-8").read())
        if m:
            canonical = {int(x) for x in re.findall(r"\d+", m.group(1))}
            src = "lint_fixtures.py"
    if canonical is None:
        fail("could not read VALID_POLICY_SCHEMA_VERSIONS from "
             "schemas/conformance/lint_fixtures.py -- it is the machine-readable "
             "source of truth for this check")
        CHECKS += 1
        print("  [X] canonical set unreadable")
        return

    # Sites that spell the set out in prose or comments.
    sites = [
        ("rfcs/RFC-MACP-0012-policy.md", r"Version of the rule schema used \(([^)]*)\)"),
        # A SECOND site in the same file -- §3's "MUST accept every schema version
        # it supports" sentence. Missed by the original sweep; mutating it to {1,2,3,4}
        # passed every check in the repository.
        ("rfcs/RFC-MACP-0012-policy.md", r"MUST accept every schema version it supports \(`?\{([^}]*)\}"),
        ("docs/policy.md", r"Version of the rule schema used \(([^)]*)\)"),
        ("schemas/json/macp-policy-descriptor.schema.json",
         r"Version of the rule schema used \(([^)]*)\)"),
        ("schemas/conformance/README.md", r"`schema_version` in \{([^}]*)\}"),
        ("schemas/proto/macp/v1/policy.proto",
         r"RFC-MACP-0012 defines versions ([^)]*)\)"),
    ]
    checked = 0
    for relpath, pattern in sites:
        path = os.path.join(ROOT, relpath)
        if not os.path.isfile(path):
            fail("%s: expected to enumerate schema_version but the file is missing"
                 % relpath)
            continue
        text = open(path, encoding="utf-8").read()
        m = re.search(pattern, text)
        if not m:
            fail("%s: no schema_version enumeration found. Either the wording "
                 "changed (update the pattern in scripts/check-prose.py) or the "
                 "enumeration was dropped -- both need a human." % relpath)
            continue
        found = {int(x) for x in re.findall(r"\d+", m.group(1))}
        checked += 1
        if found != canonical:
            fail("%s: enumerates schema_version %s but %s says %s"
                 % (relpath, sorted(found), src, sorted(canonical)))
    # Seventh site, and the only STRUCTURAL one. The descriptor schema does not
    # merely describe the legal set in prose -- it is the artifact that ENFORCES
    # it. Those are two different claims about the same file, so the file is
    # deliberately checked twice: the regex row above proves the sentence still
    # reads 1/2/3, and this proves ajv will actually reject a 4. Before #115 the
    # first held and the second did not.
    #
    # Read as JSON rather than by regex: a pattern over `"enum": [1, 2, 3]` is
    # brittle to whitespace and re-indentation, and would match the same digits
    # sitting inside a description string.
    desc_rel = "schemas/json/macp-policy-descriptor.schema.json"
    desc_path = os.path.join(ROOT, desc_rel)
    if not os.path.isfile(desc_path):
        fail("%s: expected to ENFORCE the schema_version set but the file is missing"
             % desc_rel)
    else:
        try:
            desc = json.load(open(desc_path, encoding="utf-8"))
        except ValueError as exc:
            fail("%s: not parseable as JSON, so its schema_version enum cannot be "
                 "checked (%s)" % (desc_rel, exc))
            desc = None
        if desc is not None:
            enum = desc.get("properties", {}).get("schema_version", {}).get("enum")
            # Every branch below must FAIL rather than raise. This file's own
            # discipline is to accumulate failures and report them all (see the
            # module docstring), and a traceback here would take the remaining
            # checks down with it.
            if enum is None:
                # A dropped enum is precisely the regression this site exists for:
                # the prose would still read 1/2/3 while the schema accepted 99.
                fail("%s: properties.schema_version has no `enum` -- the legal set "
                     "would be described but not enforced, which is the defect #115 "
                     "fixed" % desc_rel)
            elif not isinstance(enum, list):
                # `"enum": "123"` is not valid JSON Schema, but iterating it would
                # yield the characters 1/2/3 and silently agree with the canonical
                # set. ajv catches the malformed schema downstream; this site must
                # not report agreement it did not actually verify.
                fail("%s: properties.schema_version.enum is %s, not a list"
                     % (desc_rel, type(enum).__name__))
            elif not all(isinstance(x, int) and not isinstance(x, bool) for x in enum):
                # `[1, 2, "3"]` is valid JSON Schema and compiles clean, but paired
                # with `"type": "integer"` the string member can never match, so the
                # schema would enforce a smaller set than it advertises.
                fail("%s: properties.schema_version.enum contains a non-integer "
                     "member (%r) -- with `type: integer` such a member can never "
                     "match, so the enforced set is narrower than the declared one"
                     % (desc_rel, enum))
            else:
                checked += 1
                found = set(enum)
                if found != canonical:
                    fail("%s: ENFORCES schema_version %s but %s says %s"
                         % (desc_rel, sorted(found), src, sorted(canonical)))

    CHECKS += 1
    if len(FAILURES) == before_failures:
        print("  [OK] %d site(s) agree on %s" % (checked, sorted(canonical)))
    else:
        print("  [X] %d site(s) disagree or are unreadable"
              % (len(FAILURES) - before_failures))


# --------------------------------------------------------------------------
# 3. RFC cross-reference resolution
# --------------------------------------------------------------------------
HEADING = re.compile(r"^#{2,6}\s+([0-9]+(?:\.[0-9]+)*)\.?\s+\S", re.M)
# A MACP RFC token. The `-MACP-` infix is required so IETF citations such as
# "RFC 8785 §3.2.2.3" (four of them in RFC-MACP-0013) are never considered.
RFC_TOKEN = re.compile(r"RFC-MACP-(\d{4})")
# ANY rfc-ish token, MACP or not. Needed to tell "the nearest citation is a
# foreign standard" from "there is no citation, so this is a self-reference":
# RFC-MACP-0013 cites `RFC 8785 §3.2.2.3` four times, and attributing those
# section numbers to RFC-MACP-0013 itself is a false positive.
ANY_RFC_TOKEN = re.compile(r"RFC[\s-]?(?:MACP-)?(\d{4})")
SECTION_REF = re.compile(r"(?:§|Section\s+)([0-9]+(?:\.[0-9]+)*)")


def rfc_sections():
    out = {}
    for path in walk("rfcs", ".md"):
        m = re.search(r"RFC-MACP-(\d{4})", os.path.basename(path))
        if not m:
            continue
        num = m.group(1)
        text = open(path, encoding="utf-8").read()
        secs = set(HEADING.findall(text))
        # An index file (RFC-MACP-0001.md) has no numbered sections; the real
        # spec is RFC-MACP-0001-core.md. Merge rather than let one clobber the other.
        out.setdefault(num, set()).update(secs)
    return out


def check_xrefs():
    global CHECKS
    print("-- RFC cross-references resolve --")
    sections = rfc_sections()
    scanned = 0
    hits = 0
    for sub, ext in (("rfcs", ".md"), ("docs", ".md"), ("registries", ".md")):
        for path in walk(sub, ext):
            self_num = None
            m = re.search(r"RFC-MACP-(\d{4})", os.path.basename(path))
            if m:
                self_num = m.group(1)
            for i, line in enumerate(open(path, encoding="utf-8"), 1):
                for ref in SECTION_REF.finditer(line):
                    scanned += 1
                    sec = ref.group(1)
                    # Attribution, in priority order:
                    #  (d) SELF FIRST -- a bare section reference in RFC-000X means
                    #      RFC-000X, even when a foreign RFC token appears earlier
                    #      on the line. Without this rule the checker fires false
                    #      positives on every self-reference that follows a
                    #      cross-reference, which is common in changelogs.
                    #  (b) otherwise the NEAREST PRECEDING MACP RFC token.
                    before = line[: ref.start()]

                    # Rule 1 -- FOREIGN FIRST. If the nearest RFC-ish token of any
                    # kind is not a MACP one, the reference belongs to that standard.
                    # RFC-MACP-0013 cites `RFC 8785 §3.2.2.3` four times.
                    toks = list(RFC_TOKEN.finditer(before))
                    any_toks = list(ANY_RFC_TOKEN.finditer(before))
                    if any_toks and (not toks or any_toks[-1].start() > toks[-1].start()):
                        continue

                    # Rule 2 -- NEAREST ANTECEDENT, sentence-scoped. Not a character
                    # window: `docs/policy.md` misattributes under a window.
                    sentence = re.split(r"(?<=[.;])\s", before)[-1]
                    sent_toks = list(RFC_TOKEN.finditer(sentence))
                    target = sent_toks[-1].group(1) if sent_toks else None

                    # Rule 3 -- SELF-PREFERENCE, but only as a FALLBACK. Checking self
                    # first would mask a genuine error whenever the citing document
                    # happens to have a section of the same number -- measured at 63%
                    # of all citations. So: resolve against the explicit target first,
                    # and fall back to self only if the target does not have it.
                    # That keeps "...RFC-MACP-0007 §6.2 (§4.1)" green, where §4.1 is
                    # this document's own, without suppressing real misses.
                    if target is not None and target in sections:
                        if sec in sections[target]:
                            continue
                        if self_num and sec in sections.get(self_num, ()):
                            continue

                    if target is None:
                        if self_num and sec in sections.get(self_num, ()):
                            continue
                        # Rule 4 -- BARE, and not a section this document has. Report
                        # rather than letting it fall through to some earlier RFC that
                        # happens to have a section of the same number: that is exactly
                        # how a dangling reference resolves green while silently meaning
                        # the wrong document.
                        if self_num:
                            hits += 1
                            fail("%s:%d: bare §%s is not a section of this document "
                                 "(RFC-MACP-%s). Name the document if it means another."
                                 % (rel(path), i, sec, self_num))
                        continue

                    if target not in sections:
                        hits += 1
                        fail("%s:%d: cites RFC-MACP-%s, which does not exist"
                             % (rel(path), i, target))
                        continue
                    if sec not in sections[target]:
                        hits += 1
                        fail("%s:%d: cites RFC-MACP-%s §%s, which does not exist "
                             "(that document has §%s)"
                             % (rel(path), i, target, sec,
                                ", §".join(sorted(sections[target])[:6]) + "..."))
    CHECKS += 1
    print("  [OK] %d cross-reference(s) resolve" % scanned if not hits
          else "  [X] %d unresolvable of %d" % (hits, scanned))


# --------------------------------------------------------------------------
# 5. README per-RFC version census
#    (Banners are numbered by RUN order, matching main() and the module
#    docstring. This one is defined before check 4 but runs after it.)
# --------------------------------------------------------------------------
VERSION_HDR = re.compile(r"^\*\*Version:\*\*\s*(\S+)", re.M)


def check_version_census():
    global CHECKS
    print("-- README per-RFC version census --")
    actual = {}
    for path in walk("rfcs", ".md"):
        m = re.search(r"RFC-MACP-(\d{4})", os.path.basename(path))
        if not m:
            continue
        v = VERSION_HDR.search(open(path, encoding="utf-8").read())
        if v:
            # .strip() matters: two RFC headers carry trailing whitespace.
            actual["RFC-MACP-" + m.group(1)] = v.group(1).strip()
    readme = os.path.join(ROOT, "README.md")
    text = open(readme, encoding="utf-8").read()
    CHECKS += 1
    if not actual:
        fail("no RFC **Version:** headers found -- the census cannot be checked")
        print("  [X] no versions parsed")
        return

    # Every RFC that is NOT at the baseline must be named in the census sentence
    # with its exact version. The baseline count is stated as a word, which is
    # checked separately below.
    baseline = "1.0.0-draft"
    m = re.search(r"\*\*What is not frozen:\*\*[^\n]*", text)
    if not m:
        fail("README.md: could not find the '**What is not frozen:**' census "
             "sentence -- if it moved, update this check")
        print("  [X] census sentence not found")
        return
    sentence = m.group(0)
    problems = 0
    for name, ver in sorted(actual.items()):
        if ver == baseline:
            if name in sentence:
                problems += 1
                fail("README.md census names %s, but it is at the baseline %s -- "
                     "it should be part of the unnamed count" % (name, baseline))
            continue
        if name not in sentence:
            problems += 1
            fail("README.md census does not name %s, which is at %s (not the "
                 "%s baseline)" % (name, ver, baseline))
            continue
        # Named -- check the version travels with it. Take the nearest version
        # string following the name.
        tail = sentence[sentence.index(name):]
        vm = re.search(r"`([0-9]+\.[0-9]+\.[0-9]+-draft)`", tail)
        if not vm or vm.group(1) != ver:
            problems += 1
            fail("README.md census pairs %s with %s but its header says %s"
                 % (name, vm.group(1) if vm else "no version", ver))
    n_base = sum(1 for v in actual.values() if v == baseline)
    word = WORDS.get(n_base)
    if word and not re.search(r"\b%s at\b" % word, sentence):
        problems += 1
        fail("README.md census: %d RFC(s) are at %s, so the sentence should read "
             "'%s at' -- it does not" % (n_base, baseline, word))
    total = len(actual)
    tword = WORDS.get(total)
    if tword and not re.search(r"\b%s RFCs\b" % tword, sentence):
        problems += 1
        fail("README.md census: there are %d RFCs, so the sentence should say "
             "'%s RFCs'" % (total, tword))
    print("  [OK] census matches all %d RFC headers" % total if not problems
          else "  [X] %d census mismatch(es)" % problems)


# --------------------------------------------------------------------------
# 4. Cited-RFC term checks
# --------------------------------------------------------------------------
# The other half of #107's cross-reference item: "a `see RFC-MACP-000X` for a term
# that RFC never mentions". RFC-MACP-0012 §4.1 cited RFC-MACP-0004 for abstention
# handling; RFC-MACP-0004 contains the word zero times (#103).
#
# This is a CURATED table, not a prover. Deciding in general which noun a bare
# citation is vouching for is not mechanical. What is mechanical is holding known
# claims to account, so each row is a regression guard on one citation that was
# either wrong once or is load-bearing enough to be worth pinning. Add a row
# whenever a citation asserts that another document covers a specific term.
# Keyed on the CLAIMING SENTENCE, not merely the file: find the sentence in
# `citing` that contains `anchor`, read whichever RFC it cites, and require that
# RFC to actually contain `term`. That is the exact shape of #103 -- "Abstentions
# are excluded ... (RFC-MACP-0004)", where RFC-MACP-0004 contains the word zero
# times -- so reintroducing it fails here rather than passing CI.
CITED_TERMS = [
    # (citing file, phrase locating the claiming sentence, term the cited RFC must contain)
    ("rfcs/RFC-MACP-0012-policy.md", "Abstentions are excluded", "abstain"),
    ("rfcs/RFC-MACP-0011-quorum-mode.md", "resolved to an effective approval count", "ceiling"),
    ("rfcs/RFC-MACP-0002-modes.md", "fails bound governance-policy evaluation", "POLICY_DENIED"),
]


def check_cited_terms():
    global CHECKS
    print("-- Cited RFCs actually discuss the terms cited for --")
    ok = 0
    for citing, anchor, term in CITED_TERMS:
        citing_path = os.path.join(ROOT, citing)
        if not os.path.isfile(citing_path):
            fail("%s: cited-term row names a file that does not exist" % citing)
            continue
        citing_text = open(citing_path, encoding="utf-8").read()
        if anchor not in citing_text:
            fail("%s: cited-term row anchors on %r, which is no longer present -- "
                 "update the row in scripts/check-prose.py" % (citing, anchor))
            continue
        # The sentence making the claim, and the RFC it cites.
        idx = citing_text.index(anchor)
        tail = citing_text[idx:]
        end = re.search(r"(?<=[.])\s", tail)
        sentence = tail[: end.start()] if end else tail[:400]
        cited = RFC_TOKEN.findall(sentence)
        if not cited:
            fail("%s: the sentence containing %r cites no RFC at all, so the claim "
                 "about '%s' is unsourced" % (citing, anchor, term))
            continue
        cited_num = cited[0]
        matches = [p for p in walk("rfcs", ".md")
                   if ("RFC-MACP-" + cited_num) in os.path.basename(p)
                   and os.path.basename(p) != "RFC-MACP-0001.md"]
        if not matches:
            fail("%s: cites RFC-MACP-%s, which has no file" % (citing, cited_num))
            continue
        body = "".join(open(m, encoding="utf-8").read().lower() for m in matches)
        if term.lower() not in body:
            fail("%s cites RFC-MACP-%s for '%s', but RFC-MACP-%s never mentions it "
                 "-- a citation that does not resolve is a defect in a specification"
                 % (citing, cited_num, term, cited_num))
            continue
        ok += 1
    CHECKS += 1
    print("  [OK] %d cited term(s) present in the cited RFC" % ok if ok == len(CITED_TERMS)
          else "  [X] %d of %d cited term(s) missing" % (len(CITED_TERMS) - ok, len(CITED_TERMS)))


def _word_to_int(word):
    """Reverse WORDS. Case-insensitive; None for anything unmapped."""
    lowered = word.lower()
    for n, w in WORDS.items():
        if w == lowered:
            return n
    return None


def check_check_count():
    """Assert that every prose claim about HOW MANY checks this file runs is true.

    Canonical value: the number of `check_*()` calls in `main()`, read from the
    AST. Structural, not textual -- the same reasoning as check_schema_versions,
    which `json.load`s the descriptor schema rather than regexing its `enum`. A
    regex over the source would have to tell a call apart from the six `def`
    lines and from the bare check names in this file's comments and docstrings;
    the AST sees only calls.

    THIS CHECK COUNTS ITSELF. Adding it moved the canonical value from five to
    six, and every prose site with it. That is deliberate: excluding itself would
    make main() print one number while the documents said another -- precisely
    the drift this check exists to catch (issue #119). It is not circular: the
    canonical value is a fact about the file's AST, computed before any
    comparison, that merely happens to count this function too.

    ENFORCED -- five claims across three files: the four count words (README.md
    x1, docs/policy.md x2, this MODULE's docstring x1), and the number of items
    in the MODULE docstring's numbered list. Note that is the module docstring at
    the top of this file, not the one you are reading.

    NOT ENFORCED, and therefore a human obligation: the LENGTH of the two
    enumerations in the documents -- README.md's comma-separated clause and
    docs/policy.md's bullet list -- and, at every site including the module
    docstring, whether the items truthfully describe the checks that run. Adding
    a check means growing those two lists by hand. Neither is checked here, for
    different reasons: docs/policy.md's bullet list is cleanly countable and is
    simply not checked, while README's clause has no per-item marker to anchor
    on -- counting it needs a regex pinned to that one sentence, and that breaks
    the first time an item contains a comma. Do not read a green run as evidence
    that either list is complete or accurate.
    """
    global CHECKS
    CHECKS += 1
    print("-- check-prose.py's own check count --")
    src_path = os.path.join(ROOT, "scripts", "check-prose.py")
    try:
        tree = ast.parse(open(src_path, encoding="utf-8").read())
    except (OSError, SyntaxError) as exc:
        fail("check-prose.py could not be read or parsed, so its own check "
             "count is unknown: %s" % exc)
        print("  [X] scripts/check-prose.py unreadable or unparseable")
        return

    main_fn = next((n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    if main_fn is None:
        fail("check-prose.py has no top-level main(), so its own check count "
             "cannot be derived")
        print("  [X] no top-level main() found")
        return

    called = [n.func.id for n in ast.walk(main_fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id.startswith("check_")]
    canonical = len(called)
    if canonical == 0:
        fail("check-prose.py's main() calls no check_*() function -- a canonical "
             "count of 0 is never right, and would make every prose site "
             "'disagree' with nonsense")
        print("  [X] main() calls no check_*()")
        return

    problems = 0

    # Every check_* function must reach `CHECKS += 1`, or the summary line
    # under-counts and this check blames the documents for a code bug.
    # Assert EXISTENCE per function, never a total: check_schema_versions
    # carries two such AugAssigns, one per return path, so summing across the
    # module yields one more than the canonical count and fails on correct code.
    #
    # Two residual holes, both known and both bounded. Neither is worth more
    # machinery than this comment.
    #
    # (1) EXISTENCE cannot see PARTIAL coverage: a function that bumps on one
    # return path but not another passes here. NO function has that shape today
    # -- audited by AST, every check_* either bumps unconditionally before any
    # return, or has no return at all, and check_schema_versions bumps on both
    # of its paths (inside the `canonical is None` arm and again on the normal
    # one). So the hole is a class with no current members, not a live defect.
    # It would bite a future check that returns early without bumping.
    #
    # (2) A check_*() call in unreachable code inside main() -- `if False: ...`
    # -- inflates the canonical count. It then fails every site loudly rather
    # than passing silently, which is the safe direction.
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef)
                and node.name.startswith("check_")):
            continue
        if not any(isinstance(a, ast.AugAssign)
                   and isinstance(a.target, ast.Name)
                   and a.target.id == "CHECKS"
                   for a in ast.walk(node)):
            problems += 1
            fail("check-prose.py: %s() never does `CHECKS += 1`, so the summary "
                 "line will under-count the checks that actually ran"
                 % node.name)

    doc = ast.get_docstring(tree) or ""
    # Read the docstring via the AST rather than by slicing the file, so the
    # numbered-item regex below cannot wander into a numbered list elsewhere
    # in the module.
    sites = [
        ("README.md",
         "README.md", r"(\w+) mechanical propert"),
        ('docs/policy.md ("checks, chosen because they are mechanical")',
         "docs/policy.md", r"(\w+) checks, chosen because they are mechanical"),
        ('docs/policy.md ("narrow classes above")',
         "docs/policy.md", r"(\w+) narrow classes"),
        ("scripts/check-prose.py module docstring (count word)",
         None, r"These (\w+) checks are the fraction"),
    ]
    for label, relpath, pattern in sites:
        if relpath is None:
            text = doc
        else:
            try:
                text = open(os.path.join(ROOT, relpath), encoding="utf-8").read()
            except OSError as exc:
                problems += 1
                fail("%s could not be read to check its count claim: %s"
                     % (label, exc))
                continue
        m = re.search(pattern, text)
        if not m:
            problems += 1
            fail("%s: no check-count claim matched /%s/ -- the sentence was "
                 "reworded or removed, so nothing holds it to %d"
                 % (label, pattern, canonical))
            continue
        found = _word_to_int(m.group(1))
        if found is None:
            problems += 1
            fail("%s claims %r checks, which is not a number word this script "
                 "knows; main() calls %d" % (label, m.group(1), canonical))
        elif found != canonical:
            problems += 1
            fail("%s says %s (%d) checks, but main() calls %d: %s"
                 % (label, m.group(1), found, canonical, ", ".join(called)))

    items = re.findall(r"^\s{2,}(\d+)\.\s", doc, re.M)
    if len(items) != canonical:
        problems += 1
        fail("scripts/check-prose.py module docstring (numbered list) has %d "
             "item(s), but main() calls %d check_*(): %s"
             % (len(items), canonical, ", ".join(called)))

    print("  [OK] %d check(s) in main(), and all %d prose site(s) agree"
          % (canonical, len(sites) + 1) if not problems
          else "  [X] %d check-count problem(s)" % problems)


def main():
    print("Checking RFC prose against the artifacts that implement it...")
    print("")
    check_line_anchors()
    check_schema_versions()
    check_xrefs()
    check_cited_terms()
    check_version_census()
    check_check_count()
    print("")
    print("-------------------------------------")
    if FAILURES:
        for f in FAILURES:
            print("  [X] %s" % f)
        print("")
        print("[X] %d prose check failure(s) across %d check(s)"
              % (len(FAILURES), CHECKS))
        return 1
    print("[OK] All %d prose checks passed" % CHECKS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
