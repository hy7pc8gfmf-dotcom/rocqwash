#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doc_lint.py — the docs-vs-implementation consistency three-check tool (docs <-> tools reconciliation; guards against documentation drift; rocqwash tools/).

Purpose.  Runs the three checks (all purely local, zero network, zero
  compiles, Python 3 stdlib only, orchestrating zero new engines — every
  parsing rule is anchored to the current on-disk lines, no invented
  shapes) and reports whether the documentation and the implementation
  agree.  Read-only by construction: nothing is ever written into the
  audited repository.

Interface.  python3 tools/doc_lint.py [--repo DIR] [--json OUT]
  [--help-cap N] | --selftest.  Report schema rocqwash-doclint/1 (checks
  [{kind,target,status,detail}], verdict consistent|drift, counts,
  out_of_scope, registry, args; sort_keys on write; no wall-clock field;
  every path repo-relative — same-input reruns are byte-identical).  The
  --help-cap default is derived at run time (the measured registry size
  plus the HELP_CAP_MARGIN margin constant; an explicit value wins), so a
  new tool registration raises the cap with zero manual steps.  The
  checks list rows with kind in {tool_table,count,flag}, status in
  {ok,drift}, and a single-line detail (clipped at 300 chars).  The full
  three-check contract lives in the extended contract block below.

Dependencies.  Python 3 standard library only; the only subprocesses are
  local real --help runs (milliseconds; zero network, zero compiles, zero
  sleeps — --injector/--sleep-scale do not apply); every path
  parameterized, zero hardcoded paths; offline-testable by nature (the
  --selftest uses all-tmp mini-repo fixtures).

Evidence.  --selftest vectors (tmp mini-repo fixtures; the consistency
  verdict plus CLI codes plus the idempotence check): V1 a consistent mini
  repo (2 routes, all four places present; count 2 agreeing in all three
  spots; every cited flag proven) -> rc 0, verdict consistent, zero drift
  checks; V2 a missing tool-table row (the hint_for b line dropped) -> rc
  1, tool_table drift pointing at cw.sh:hint; V3 a count drift
  (tests/README.md coverage changed to 3) -> rc 1, count drift, value 3
  vs 2; V4 a phantom flag citation (docs/note.md gains a --bogus-flag
  reference) -> rc 1, flag drift; V5 CLI codes (--help 0; --bogus 2;
  missing --repo 9) plus --help-cap 0 -> 2; V6 JSON idempotence (same
  repo, two runs, different --json paths, byte-identical — the report
  never embeds its own json path).  V7 the derived help cap (the default =
  the measured registry size + the margin: the cap auto-follows a new
  tools/ registration with zero manual steps; under an explicit smaller
  cap the over-cap report face keeps its semantics: help not run,
  citations unproven, rc 1).  Suite membership tests/test_doc_lint.py.

Exit-codes.  0 = consistent (zero drift across the three checks); 1 =
  drift (any row drifted; a failing result is data, not a tool failure;
  reported loudly on stdout); 2 = usage error (argparse / --help-cap < 1);
  9 = missing (--repo directory missing / an audited-repo required input
  missing: cw.sh, README.md, README-cw.md, tests/run_tests.sh,
  tests/README.md, docs/, examples/workflows/; the --json parent directory
  missing; a tool --help failing or timing out; an undecodable doc file).
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget).
# check 1, the tool table: mutual inspection of the four cw.sh tool lists
# (header / usage / hint / case) plus reconciliation against the generic
# entry points that actually exist in tools/ (missing routes / extra rows /
# missing rows listed row by row).  The four places = the header tool table
# (cw.sh:10-50, name desc -> path, with the two-line wrapped form like the
# doctor rows at cw.sh:25-26), the usage() heredoc tool table (cw.sh:83-124),
# the hint_for() one-line hints (cw.sh:133-153, the echo string ending with
# -> path), and the case routing block (cw.sh:170-186, run_tool <name> "<rel>").
# Mutual inspection = every routed tool appears in all four places (a missing
# place is a missing row, listed per tool per place) plus per-tool path
# agreement across the four places (a mismatch or a missing -> path is
# listed).  Reconciliation = a case route whose target is missing on disk is
# an extra row (a dangling route); a tools/ non-underscore .py (a generic
# entry point, defined by the cli/rocqwash:9 anchor "the only .py without a
# leading underscore in the module directory") without a case route is a
# missing route.  help is a pseudo-route and does not compete (the cw.sh:49
# header row plus the cw.sh:187 help|-h|--help special routing; hint_for has
# no branch — the four places are asymmetric by design).
# check 2, the counts: the tests/run_tests.sh CASES count (the statically
# rostered cases at run_tests.sh:140-192; the t_fail_probe FAIL_PROBE
# self-check injection case is not counted, run_tests.sh:194-197) vs the
# tests/README.md count lines (:12 "expected 52 passes" + :15 "coverage (52
# cases)") vs the README.md case-count line (:59 "self-test suite (52 cases)
# — test suite (52 cases)").  All three values must agree; a drift is listed;
# a missing count-line shape is listed as a missing count line.  The
# "extended to N cases" history lines (README.md:83/92/101/112/123/139/156)
# are versioned history, not current counts (per-round accretion is by
# design, the same history-line form as the v38 cw.sh:2 "sixteen total") and
# stay outside the reconciliation — only the four shapes above are anchored;
# prefer fewer shapes over inventing new count forms.
# check 3, the flags: every tool flag cited in README-cw.md / README.md /
# examples/workflows/*.md / docs/*.md (docs recursive; *.zh.md and docs/zh/
# archives are exempt — annotation standard card 5.2, archive files are not
# canonical faces) is checked one by one against each tool's real --help
# output (a real subprocess --help run; rc != 0 / timeout = tool failure,
# fail-loud 9; capped at the --help-cap tools, the default cap derived at
# run time as the measured registry size plus the HELP_CAP_MARGIN margin
# constant, an explicit value winning over the derivation).  The tool set =
# cw.sh routes union the tools/ entry-point scripts whose name does not
# start with `_`; over-cap tools are truncated
# in canonical order and listed honestly as "help not run; N citations
# unproven".
# Attribution rules: tool references have two tiers (tier-1 strong = an
# on-disk path form / cli/rocqwash / a cw.sh route form; tier-2 weak = a bare
# name — a route name, a tool stem, or an on-disk out-of-scope tool stem); a
# flag is attributed to the nearest preceding tier-1 reference on its logical
# line, else tier-2 (the README.md:232 "cli/rocqwash certify push_gate
# union-freeze --world..." precedent: the bare-name union inside union-freeze
# must not steal the primary).  Flag tokens are masked before tool-reference
# search (so the probe inside --probe-resume is not swallowed by \\bprobe\\b).
# Three pool fallbacks: a prose paragraph = whole-paragraph references
# collected in two passes bounded by blank lines / fences / headings (the
# README-cw.md:77 paragraph-initial flag precedent); a code-fence command
# line = backslash continuations joined, then attributed strictly inside the
# command itself (the strongest phantom-judgment face); a code-fence comment
# line = block-pool attribution (the step-pushci.md:75-77 "# optional
# additions: --pre-scan-gate4 / --merge..." real form).  Drift has two
# directions: a missing flag (phantom / extra citation — the doc side cites a
# flag the tool does not actually emit: the primary tool's real help lacks it,
# the registry tools in the pool all lack it, and the pool has no verifiable
# oos/unknown tool; the mechanical "the same flag token repeated >= 2 is
# extra" rule was rejected by the README.md:232 union-freeze --world wa=...
# --world wb=... legitimate multi-value precedent and is not used) plus a
# dangling citation (the primary reference is unrecognized — a cw.sh
# non-route or a route target missing on disk, leaving the flag with no
# provable tool; the cw.sh bogus-style exit-code example lines carry no flags
# and are not mis-bitten).  Ownerless flags and pools containing oos/unknown
# tools are counted honestly as unresolved, never judged drift (unprovable is
# not drift — the docs/zh/architecture.md:54 ledger line "--json/--hits-csv"
# belongs to the scan-stage tool mac_stmt_scan with the context at the
# document-section level; when the mechanical check cannot attribute it, no
# drift is judged).  cli/rocqwash and non-registry tools' (certify/watch/
# wrapper/work-stream files etc.) flags are outside this check — counted into
# out_of_scope honestly (cli/rocqwash is the pre-v29 routing layer; its flags
# belong to the sub-tools, cli/rocqwash:8-11 routing contract).
# argparse wrap repair: break_on_hyphens splits tokens as "--on-red-<LF>arg"
# (evidenced by the cw_sentinel --help output) — repaired via
# (--tok)-\n<ws>(cont) before token extraction; the registry_union --help:14
# "--ref-*" wording is glob prose, its truncated tokens are noise and harmless
# to phantom judgment (this check is one-way doc->help: extra flags harvested
# from help prose only cause missed reports, never false ones — precision
# traded for zero false positives).

PROG = "doc_lint"
SCHEMA = "rocqwash-doclint/1"

HELP_CAP_MARGIN = 5       # the derived-cap margin: the check-3 cap defaults to the measured registry size plus this constant at run time (the retired DEFAULT_HELP_CAP manual constant grew only by hand edits, 20->61, one edit per tool registration, and sat exactly at the measured registry 61 at retirement, so the next registration would have truncated the sorted-order tail; a truncated tool keeps an empty help set and every doc flag cited against it is misjudged phantom - the derivation removes that manual path by construction)
HELP_TIMEOUT = 60         # --help subprocess second cap (local-file hang guard; fail-loud)
DETAIL_CAP = 300          # checks[].detail clip (the cw_doctor non_form ln[:120] form)
DRIFT_LINE_CAP = 20       # check 3 per-file phantom/dangling list cap (the total is honest; the cw_doctor cap-20 form)
LIST_CAP = 20             # the out_of_scope/registry overflow list cap (the total is honest)


def derived_help_cap(registry_rel):
    """The check-3 default cap, derived at run time from the measured
    registry (the check-1 registry_rel list: the routed cw.sh paths union
    the generic tools/ entry-point scripts, a .py file whose name does not
    start with `_`): every registered tool gets a real --help run plus
    HELP_CAP_MARGIN spare slots, and an explicit --help-cap value wins
    over the derivation.  Doc_lint's own data source for "the registered
    tool faces" is this measured registry (check 1 already builds it
    before check 3 runs), so the derivation reads the same source instead
    of re-scanning help outputs; the retirement of the manual constant
    means a new tool registration raises the cap with zero manual steps."""
    return len(registry_rel) + HELP_CAP_MARGIN

PSEUDO_ROUTES = ("help",)  # the pseudo-route (the cw.sh:49 header row; the cw.sh:187 special routing)

# repo-level universal tool flags (excluded from phantom judgment): --help is
# always present; --selftest follows the suite discipline — every rostered
# tool case in run_tests.sh really runs --selftest (t_scan_selftest /
# t_cw_doctor twelve tools directly plus t_cw_sentinel / t_wash_shape /
# t_unclog the same), and some tools handle it pre-argparse (the cw_doctor.py
# `if "--selftest" in argv` form before argparse) so --help never lists it —
# judging it a phantom flag from its help absence would be a false positive,
# hence it is always accepted.
UNIVERSAL_FLAGS = ("--help", "--selftest")

PLACE_ORDER = ("header", "usage", "hint", "case")

# ---- check 1: the cw.sh four-place parsing regexes (anchored 1:1 to the current cw.sh lines; KEEP, data faces — these anchor the real cw.sh's own section headers) ----
ROUTE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROW_PATH_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\s+.*->\s*(\S+)\s*$")
CONT_PATH_RE = re.compile(r"^->\s*(\S+)\s*$")
PENDING_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\s+\S")
TABLE_STOP_RE = re.compile(r"^(路由契约|退出码|路由说明|覆盖面注)")
HINT_RE = re.compile(r'^\s*([a-z0-9][a-z0-9-]*)\)\s+echo\s+"(.+)"\s*;;\s*$')
HINT_PATH_RE = re.compile(r"->\s*(\S+)\s*$")
CASE_RE = re.compile(
    r'^\s*([a-z0-9][a-z0-9-]*)\)\s+shift;\s*run_tool\s+\S+\s+"([^"]+)"')

# ---- check 2: count-line shapes (anchored 1:1 to the current tests/README.md:12/:15 and README.md:59 lines; KEEP, data faces — these anchor the READMEs' own Chinese count-line formats) ----
COUNT_PATTERNS = (
    ("tests/README.md", re.compile(r"覆盖面（(\d+) 例）"), "覆盖面（N 例）"),
    ("tests/README.md", re.compile(r"预期 (\d+) 过"), "预期 N 过"),
    ("README.md", re.compile(r"自测套件（(\d+) 例）"), "自测套件（N 例）"),
    ("README.md", re.compile(r"test suite \((\d+) cases\)"),
     "test suite (N cases)"),
)
CASES_RE = re.compile(r'(?ms)^CASES="(.*?)"')

# ---- check 3: doc scanning regexes ----
FLAG_RE = re.compile(r"--[A-Za-z0-9][A-Za-z0-9_-]*")
# argparse break_on_hyphens 折行复原：(--tok)-\n<ws>(cont) → --tok-cont
HYPHEN_WRAP_RE = re.compile(
    r"(--[A-Za-z0-9][A-Za-z0-9_-]*)-\n\s*([A-Za-z0-9][A-Za-z0-9_-]*)")
HELP_TOKEN_RE = re.compile(r"--([A-Za-z0-9][A-Za-z0-9_-]*)")
PATH_RE = re.compile(
    r"\b((?:tools|wash|scan|verify|certify|wrapper|watch|seam|names|recipes"
    r"|examples|docs|tests)/[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh))\b")
CLI_RE = re.compile(r"\bcli/rocqwash\b")
ROUTE_MENTION_RE = re.compile(r"\bcw\.sh\s+([a-z][a-z0-9-]*)")


class UsageError(Exception):
    """Usage error / value validation failure (exit 2)."""


class MissingInput(Exception):
    """Missing input (exit 9)."""


class ToolError(Exception):
    """Tool failure / --help failure (exit 9; fail-loud, silent degradation forbidden)."""


# ---- small pieces (deterministic helpers; local copies of the cw_doctor forms; no package layout, no cross-imports) ----

def read_text(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MissingInput("%s unreadable / decode failure: %s (%s)" % (what, path, e))


def dump_json(obj, path):
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as e:
        raise MissingInput("--json write failed: %s (%s)" % (path, e))


def rel_of(repo, p):
    """Repo-relative path (deterministic; the zero-absolute-paths-in-the-report discipline)."""
    return os.path.relpath(p, repo).replace(os.sep, "/")


def clip(s, cap=DETAIL_CAP):
    s = s if isinstance(s, str) else str(s)
    return s if len(s) <= cap else s[:cap - 1] + "…"


def line_no_of(text, pos):
    return text[:pos].count("\n") + 1


# ---- check 1: the tool table ----

def parse_table_rows(lines, ln0):
    """Table body rows -> {name: {"path": str|None, "line": int}} (only the
    route-name shape ^[a-z0-9][a-z0-9-]*$ counts; three forms: a single line
    name desc -> path; a continuation line -> path; a wrapped pending name
    whose path arrives on the next line — the cw.sh:25-26 doctor wrapped form
    1:1).  Section-boundary rows like the routing-contract / exit-codes
    headers stop the scan (TABLE_STOP_RE)."""
    rows = {}
    pending = None
    for i, raw in enumerate(lines):
        s = raw.lstrip("#").strip()
        no = ln0 + i + 1
        if TABLE_STOP_RE.match(s):
            break
        if not s:
            pending = None
            continue
        m = CONT_PATH_RE.match(s)
        if m is not None:
            if pending is not None and pending in rows \
                    and rows[pending]["path"] is None:
                rows[pending]["path"] = m.group(1)
            pending = None
            continue
        m = ROW_PATH_RE.match(s)
        if m is not None:
            rows[m.group(1)] = {"path": m.group(2), "line": no}
            pending = None
            continue
        m = PENDING_RE.match(s)
        if m is not None:
            name = m.group(1)
            if name not in rows:
                rows[name] = {"path": None, "line": no}
            pending = name
            continue
        pending = None
    return rows


def parse_cw_sh(repo):
    """cw.sh four-place list parsing -> {place: {name: {"path", "line"}}}.
    Region boundaries: the header runs to the first set -u (cw.sh:73); usage
    to the first EOF (the heredoc end); hint_for to the first column-0 };
    case to EOF (the case "${1:-}" in is the only routing case; the inner
    case "$1" in of hint_for is not mis-bitten)."""
    path = os.path.join(repo, "cw.sh")
    if not os.path.isfile(path):
        raise MissingInput("the audited repo lacks cw.sh: %s" % path)
    text = read_text(path, "cw.sh")
    lines = text.split("\n")

    def idx_of(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        return None

    setu = idx_of(lambda ln: ln.strip() == "set -u")
    if setu is None:
        raise ToolError("cw.sh shape unrecognized (no set -u boundary): %s" % path)
    u_start = idx_of(lambda ln: "usage() {" in ln)
    u_end = idx_of(lambda ln: ln.strip() == "EOF",
                   (u_start + 1) if u_start is not None else 0)
    h_start = idx_of(lambda ln: "hint_for() {" in ln)
    h_end = idx_of(lambda ln: ln.rstrip() == "}",
                   (h_start + 1) if h_start is not None else 0)
    c_start = idx_of(lambda ln: 'case "${1:-}" in' in ln)
    if u_start is None or h_start is None or c_start is None:
        raise ToolError("cw.sh shape unrecognized (one of the usage/hint_for/case boundaries missing): %s" % path)

    def table_start(lines, lo, hi, marker):
        seg = idx_of(lambda ln: marker in ln, lo)
        return seg if seg is not None and seg < hi else lo

    hdr_lo = table_start(lines, 0, setu, "工具表 Tools")
    hdr = parse_table_rows(lines[hdr_lo:setu], hdr_lo)
    usg_lo = table_start(lines, u_start, u_end, "工具 Tools:")
    usg = parse_table_rows(lines[usg_lo:u_end], usg_lo)
    hint = {}
    for i in range(h_start, (h_end if h_end is not None else len(lines))):
        m = HINT_RE.match(lines[i])
        if m is None:
            continue
        hp = HINT_PATH_RE.search(m.group(2))
        hint[m.group(1)] = {"path": hp.group(1) if hp else None,
                            "line": i + 1}
    case = {}
    for i in range(c_start, len(lines)):
        m = CASE_RE.match(lines[i])
        if m is None:
            continue
        case[m.group(1)] = {"path": m.group(2), "line": i + 1}
    return {"header": hdr, "usage": usg, "hint": hint, "case": case}


def check_tool_table(repo, places):
    """Check 1: the four-place mutual inspection plus the tools/ generic-entry
    reconciliation -> the checks list (one row each; kind=tool_table)."""
    checks = []
    routed = set(places["case"]) - set(PSEUDO_ROUTES)
    # four-place mutual inspection: every routed tool present in all four places (missing rows / dangling names listed per tool per place)
    for place in PLACE_ORDER:
        names = set(places[place]) - set(PSEUDO_ROUTES)
        for t in sorted(routed - names):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:%s" % place, "status": "drift",
                           "detail": clip("tool %s is routed in the case table"
                                          " but the %s table lacks its row"
                                          " (mutual inspection: a missing row)"
                                          % (t, place))})
        for t in sorted(names - routed):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:%s:%s" % (place, t),
                           "status": "drift",
                           "detail": clip("tool %s appears only in the %s table"
                                          " with no case route (mutual"
                                          " inspection: a dangling name)"
                                          % (t, place))})
    # per-tool path agreement (the case path is authoritative; a missing or mismatched path elsewhere is listed)
    for t in sorted(routed):
        for place in PLACE_ORDER[:-1]:
            ent = places[place].get(t)
            if ent is None:
                continue
            if ent["path"] is None:
                checks.append({"kind": "tool_table",
                               "target": "cw.sh:%s:%s" % (place, t),
                               "status": "drift",
                               "detail": clip("tool %s has no -> path on its"
                                              " %s row (a broken wrapped"
                                              " form)" % (t, place))})
            elif ent["path"] != places["case"][t]["path"]:
                checks.append({"kind": "tool_table",
                               "target": "cw.sh:%s:%s" % (place, t),
                               "status": "drift",
                               "detail": clip("tool %s paths disagree: %s=%s vs"
                                              " case=%s" % (t, place,
                                                           ent["path"],
                                                           places["case"][t]
                                                           ["path"]))})
    # reconciliation: a case route whose target is missing on disk = an extra row (a dangling route)
    tools_dir = os.path.join(repo, "tools")
    if not os.path.isdir(tools_dir):
        raise MissingInput("the audited repo lacks the tools/ directory: %s" % tools_dir)
    for t in sorted(routed):
        p = places["case"][t]["path"]
        if not os.path.isfile(os.path.join(repo, p)):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:case:%s" % t, "status": "drift",
                           "detail": clip("the route target is missing on disk:"
                                          " %s (an extra row; a dangling route)"
                                          % p)})
    # reconciliation: a tools/ non-underscore .py without a case route = a missing route (the cli/rocqwash:9 definition)
    generic = sorted(fn for fn in os.listdir(tools_dir)
                     if fn.endswith(".py") and not fn.startswith("_"))
    routed_paths = set(places["case"][t]["path"] for t in routed)
    unrouted = []
    for fn in generic:
        rel = "tools/" + fn
        if rel not in routed_paths:
            unrouted.append(rel)
            checks.append({"kind": "tool_table", "target": rel,
                           "status": "drift",
                           "detail": clip("a tools/ generic entry point (the"
                                          " cli/rocqwash:9 non-underscore .py"
                                          " definition) has no cw.sh case route"
                                          " (a missing route)")})
    if not checks:
        checks.append({"kind": "tool_table", "target": "cw.sh four places + tools/",
                       "status": "ok",
                       "detail": clip("mutual inspection agrees (%d tools in all"
                                      " four places, paths aligned) +"
                                      " reconciliation with zero gaps (all %d"
                                      " tools/ generic entry points routed)"
                                      % (len(routed), len(generic)))})
    registry_rel = sorted(set(routed_paths) |
                          set("tools/" + fn for fn in generic))
    return checks, registry_rel, unrouted


# ---- check 2: the counts ----

def check_counts(repo):
    """Check 2: the CASES count vs the tests/README.md count lines vs the README.md case-count line -> checks."""
    checks = []
    rt_rel = "tests/run_tests.sh"
    rt_path = os.path.join(repo, rt_rel)
    if not os.path.isfile(rt_path):
        raise MissingInput("the audited repo lacks %s: %s" % (rt_rel, rt_path))
    rt_text = read_text(rt_path, rt_rel)
    m = CASES_RE.search(rt_text)
    if m is None:
        raise ToolError("run_tests.sh shape unrecognized (no CASES=\" block): %s" % rt_path)
    # backslash continuations inside the bash quoted string (run_tests.sh:140
    # CASES="\ plus a trailing \ per line) are restored to whitespace before
    # tokenizing — a literal \ is not a case name
    tokens = m.group(1).replace("\\\n", " ").split()
    cases_n = len(tokens)
    cases_line = line_no_of(rt_text, m.start())
    checks.append({"kind": "count", "target": "%s:%d" % (rt_rel, cases_line),
                   "status": "ok",
                   "detail": clip("CASES rostered %d cases (statically"
                                  " rostered; the t_fail_probe FAIL_PROBE"
                                  " injection case is not counted)"
                                  % cases_n)})
    for rel, rx, label in COUNT_PATTERNS:
        fpath = os.path.join(repo, rel)
        if not os.path.isfile(fpath):
            raise MissingInput("被审仓缺 %s: %s" % (rel, fpath))
        text = read_text(fpath, rel)
        hits = list(rx.finditer(text))
        if not hits:
            checks.append({"kind": "count", "target": rel, "status": "drift",
                           "detail": clip("the count-line shape [%s] never"
                                          " appeared (the count line is"
                                          " missing)" % label)})
            continue
        for h in hits:
            no = line_no_of(text, h.start())
            val = int(h.group(1))
            if val == cases_n:
                checks.append({"kind": "count",
                               "target": "%s:%d" % (rel, no), "status": "ok",
                               "detail": clip("[%s] = %d agrees with CASES %d"
                                              % (label, val, cases_n))})
            else:
                checks.append({"kind": "count",
                               "target": "%s:%d" % (rel, no),
                               "status": "drift",
                               "detail": clip("[%s] = %d != CASES %d (count"
                                              " drift)"
                                              % (label, val, cases_n))})
    return checks, cases_n


# ---- check 3: the flags ----

# one argparse subparser face row: 2-6 spaces of indent, a bare lowercase
# dash-word name, two or more spaces, then the face description (the nested
# shape argparse renders inside the "positional arguments:" block; flat
# positional placeholders such as OLD.json or LEDGER.json never match, and
# description continuation lines sit deeper than the name rows)
SUBCOMMAND_ROW_RE = re.compile(r"^ {2,6}([a-z][a-z0-9-]*) {2,}(\S.*)$")


def run_help_flags(repo, rel):
    """A real subprocess --help run -> the actually emitted flag set (wrap
    repair included).  rc != 0 / timeout = tool failure 9.  A subparser-form
    CLI (the "positional arguments:" block listing one indented lowercase
    face row per subcommand) gets one extra --help run per listed face and
    the face's emitted flags merge into the same set, so a doc citation of a
    subcommand flag verifies against the real face; a face row whose extra
    run fails or times out contributes no flags (the top-level face stays
    the authority)."""
    p = os.path.join(repo, rel)
    try:
        pr = subprocess.run([sys.executable, "-B", p, "--help"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=HELP_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise ToolError("--help timed out (> %ds): %s (%s)" % (HELP_TIMEOUT, rel, e))
    out = pr.stdout.decode("utf-8", "replace") if isinstance(pr.stdout, bytes) \
        else (pr.stdout or "")
    if pr.returncode != 0:
        raise ToolError("--help tool failure rc=%d: %s (%s)"
                        % (pr.returncode, rel, out[-200:]))
    fixed = HYPHEN_WRAP_RE.sub(r"\1-\2", out)
    flags = set("--" + t for t in HELP_TOKEN_RE.findall(fixed))
    in_positional = False
    for line in out.split("\n"):
        if line.startswith("positional arguments:"):
            in_positional = True
            continue
        if in_positional and line and not line[0].isspace():
            in_positional = False
        if not in_positional:
            continue
        row = SUBCOMMAND_ROW_RE.match(line)
        if row is None:
            continue
        try:
            sub = subprocess.run([sys.executable, "-B", p, row.group(1),
                                  "--help"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 timeout=HELP_TIMEOUT)
        except subprocess.TimeoutExpired:
            continue
        if sub.returncode != 0:
            continue
        sub_out = sub.stdout.decode("utf-8", "replace") \
            if isinstance(sub.stdout, bytes) else (sub.stdout or "")
        sub_fixed = HYPHEN_WRAP_RE.sub(r"\1-\2", sub_out)
        flags |= set("--" + t for t in HELP_TOKEN_RE.findall(sub_fixed))
    return flags


class LintCtx(object):
    """Check 3 scanning context: the tool-set maps + the real help sets + the
    account books.  Tool references have two tiers: tier-1 strong (an on-disk
    path form / cli/rocqwash / a cw.sh route form); tier-2 weak (a bare name —
    a route name, a tool stem, or an on-disk out-of-scope tool stem).  The
    primary is the nearest preceding tier-1 reference on the line, else tier-2
    (this blocks the bare-name union inside union-freeze from stealing the
    primary in the README.md:232 "cli/rocqwash certify push_gate union-freeze
    --world..." line)."""

    def __init__(self, repo, registry_rel, route_map, help_cap):
        self.repo = repo
        self.help_cap = help_cap   # the effective cap (derived default or the explicit value)
        self.route_map = dict(route_map)
        self.stem_map = {}
        for rel in registry_rel:
            base = os.path.basename(rel)
            if base.endswith(".py"):
                self.stem_map[base[:-3]] = rel
        # on-disk out-of-scope tool stems (non-underscore .py in the module
        # directories plus tools/*.sh, excluding the registry) — so bare file
        # name citations like "wash_engine.py" can be attributed as oos
        # (unprovable but attributable, not ownerless)
        self.oos_stem_map = {}
        for d in ("tools", "wash", "scan", "verify", "certify", "wrapper",
                  "watch", "seam", "names", "recipes"):
            dd = os.path.join(repo, d)
            if not os.path.isdir(dd):
                continue
            for fn in sorted(os.listdir(dd)):
                stem = None
                if fn.endswith(".py") and not fn.startswith("_"):
                    stem = fn[:-3]
                elif d == "tools" and fn.endswith(".sh"):
                    stem = fn[:-3]
                if stem is None:
                    continue
                rel = d + "/" + fn
                if not os.path.isfile(os.path.join(repo, rel)) \
                        or rel in set(registry_rel):
                    continue
                self.oos_stem_map.setdefault(stem, rel)
        names = sorted(set(self.route_map) - set(PSEUDO_ROUTES) |
                       set(self.stem_map) | set(self.oos_stem_map),
                       key=lambda s: (-len(s), s))
        self.bare_re = re.compile(
            r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")
        self.registry = set(registry_rel)
        self.help = {}
        self.help_order = [r for r in registry_rel
                           if os.path.isfile(os.path.join(repo, r))]
        self.overflow = self.help_order[help_cap:]
        self.help_order = self.help_order[:help_cap]
        self.oos = {}          # (file_rel, target) → refs
        self.oos_total = 0

    def load_helps(self):
        """A real --help run per tool (canonical order, within the cap) -> the
        help sets (unioned with the repo-level universal flags — see
        UNIVERSAL_FLAGS)."""
        for rel in self.help_order:
            self.help[rel] = run_help_flags(self.repo, rel) | set(
                UNIVERSAL_FLAGS)

    def resolve_path(self, p):
        if p in self.registry:
            return ("tool", p)
        if os.path.isfile(os.path.join(self.repo, p)):
            return ("oos", p)
        return ("unknown", p)

    def resolve_route(self, r):
        if r in PSEUDO_ROUTES:
            return None
        p = self.route_map.get(r)
        if p is None:
            return ("unknown", "cw.sh %s (not a route)" % r)
        if not os.path.isfile(os.path.join(self.repo, p)):
            return ("unknown", "cw.sh %s (route target missing on disk: %s)" % (r, p))
        return ("tool", p)

    def resolve_bare(self, b):
        p = self.route_map.get(b) or self.stem_map.get(b)
        if p:
            return ("tool", p)
        q = self.oos_stem_map.get(b)
        if q:
            return ("oos", q)
        return None


def doc_files(repo):
    """Check 3: the reconciliation file order (the README family -> examples/workflows/*.md -> docs/ recursive; canonical order)."""
    out = ["README-cw.md", "README.md"]
    wf = os.path.join(repo, "examples", "workflows")
    if not os.path.isdir(wf):
        raise MissingInput("the audited repo lacks examples/workflows/: %s" % wf)
    out += sorted("examples/workflows/" + fn
                  for fn in os.listdir(wf) if fn.endswith(".md"))
    dd = os.path.join(repo, "docs")
    if not os.path.isdir(dd):
        raise MissingInput("the audited repo lacks docs/: %s" % dd)
    for dirpath, dirnames, filenames in os.walk(dd):
        dirnames.sort()
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            rel = rel_of(repo, os.path.join(dirpath, fn))
            # annotation standard card 5.2: archive files are not canonical
            # faces — the sibling *.zh.md archives and the docs/zh/ directory
            # are frozen historical archives (their statements are not
            # maintained as the code evolves); a consistency check against the
            # living implementation is meaningless on them, so they are
            # exempt from the scan
            if rel.startswith("docs/zh/") or rel.endswith(".zh.md"):
                continue
            out.append(rel)
    return out


def scan_doc(repo, rel, ctx):
    """Single-file check 3 scan -> (item, drift_n, refs_n).
    Three attribution routes: (1) prose paragraphs = whole paragraphs bounded
    by blank lines / fences / headings, processed in two passes (pass one
    collects the paragraph reference pool; pass two attributes line by line —
    a paragraph-initial flag like README-cw.md:77 "the --once/--loop dual
    mode" has no preceding tool reference, so the paragraph pool backs it
    up); (2) code-fence command lines = backslash continuations joined, then
    attributed strictly per command (the pool = the command's own references;
    the strongest phantom-judgment face); (3) code-fence comment lines (the
    step-pushci.md:75-77 "# optional additions: --pre-scan-gate4..." real
    form) = block-pool attribution (the whole block's references collected in
    two passes).  Reference tiers: tier 1 (path/cli/route) > tier 2 (bare
    name) — the primary is the nearest preceding tier-1, else tier 2.  Drift
    has two directions: a missing flag (phantom / extra citation — the
    primary tool's real help lacks the flag, the registry tools in the pool
    all lack it, and the pool holds no verifiable oos/unknown tool); a
    dangling citation (the primary reference is unrecognized — a cw.sh
    non-route or a route target missing on disk).  Ownerless flags and pools
    containing oos/unknown tools are counted honestly as unresolved
    (unprovable is not drift — the zh/en architecture ledger lines "--json/
    --hits-csv" belong to the scan-stage tool mac_stmt_scan: the context sits
    at the document-section level, and when the mechanical check cannot
    attribute a flag it does not judge drift).  Flag tokens are masked before
    the tool-reference search (so the probe inside --probe-resume is not
    swallowed by \\bprobe\\b)."""
    text = read_text(os.path.join(repo, rel), rel)
    lines = text.split("\n")
    drifts = []            # (line_no, detail)
    refs_total = [0]
    unres_total = [0]
    oos_local = [0]
    in_code = False
    para = []              # prose-paragraph buffer [(line_no, seg)]
    code_block = []        # code-block logical-line buffer [(line_no, joined)]
    cur = []               # code continuation assembly buffer [(line_no, seg)]
    pend_join = False

    def mentions_of(seg):
        """-> (ordered mentions [(pos, tier, (kind,key))], flag_hits
        [(pos,tok)]).  Tier 1 = a path/cli/route strong reference; tier 2 = a
        bare-name weak reference.  Flag tokens are masked first (same-length
        spaces, positions undisturbed) before the tool-reference search."""
        flag_hits = [(m.start(), m.group(0)) for m in FLAG_RE.finditer(seg)]
        masked = FLAG_RE.sub(lambda m: " " * len(m.group(0)), seg)
        mentions = []
        for m in PATH_RE.finditer(masked):
            mentions.append((m.start(), 1, ctx.resolve_path(m.group(1))))
        for m in CLI_RE.finditer(masked):
            mentions.append((m.start(), 1, ("oos", "cli/rocqwash")))
        for m in ROUTE_MENTION_RE.finditer(masked):
            ent = ctx.resolve_route(m.group(1))
            if ent is not None:
                mentions.append((m.start(), 1, ent))
        for m in ctx.bare_re.finditer(masked):
            ent = ctx.resolve_bare(m.group(1))
            if ent is not None:
                mentions.append((m.start(), 2, ent))
        mentions.sort(key=lambda t: (t[0], t[1]))
        return mentions, flag_hits

    def account(no, mentions, flag_hits, pool):
        """Attribute one logical line -> (drifts, refs, unresolved).  The
        primary = the nearest preceding tier-1 reference on the line, else
        tier 2; pool = the fallback pool (kind-tagged: tool/oos/unknown)."""
        out = []
        refs = 0
        unres = 0
        reg_pool = list(dict.fromkeys(
            k for kind, k in pool if kind == "tool"))
        unverifiable = any(kind in ("oos", "unknown") for kind, _ in pool)
        for pos, tok in flag_hits:
            refs += 1
            prim = None
            for mpos, _tier, ent in reversed(mentions):
                if mpos < pos:
                    prim = ent
                    break
            kind, key = prim if prim is not None else (None, None)
            if kind == "tool":
                if tok in ctx.help.get(key, set()):
                    continue
                if any(tok in ctx.help.get(t, set()) for t in reg_pool):
                    continue
                if unverifiable:
                    unres += 1
                    continue
                out.append((no, "missing flag (phantom / extra citation):"
                                " the nearest tool %s before %s does not emit"
                                " this flag in its real help (%d flags"
                                " emitted); the pool %s lacks it too"
                                % (tok, key,
                                   len(ctx.help.get(key, set())),
                                   ",".join(reg_pool) if reg_pool else "empty")))
            elif kind == "oos":
                ek = (rel, key)
                ctx.oos[ek] = ctx.oos.get(ek, 0) + 1
                ctx.oos_total += 1
                oos_local[0] += 1
            elif kind == "unknown":
                out.append((no, "dangling citation: the nearest tool reference"
                                " before the flag %s is unrecognized (%s) — no"
                                " tool can prove it" % (tok, key)))
            else:
                if any(tok in ctx.help.get(t, set()) for t in reg_pool):
                    continue
                unres += 1
        return out, refs, unres

    def flush_code_block():
        """The code block in two passes: pass one collects the whole-block
        reference pool (for comment lines); pass two attributes per logical
        line (command lines strictly from their own pool; comment lines from
        the block pool)."""
        nonlocal code_block, drifts
        if not code_block:
            return
        buf = code_block
        code_block = []
        scanned = []
        block_pool = []
        for no, joined in buf:
            mentions, flags = mentions_of(joined)
            for _pos, _tier, ent in mentions:
                if ent not in block_pool:
                    block_pool.append(ent)
            scanned.append((no, joined, mentions, flags))
        for no, joined, mentions, flags in scanned:
            is_comment = joined.lstrip().startswith("#")
            pool = block_pool if is_comment else \
                [ent for _pos, _tier, ent in mentions]
            d, r, u = account(no, mentions, flags, pool)
            drifts.extend(d)
            refs_total[0] += r
            unres_total[0] += u

    def flush_para():
        """The prose paragraph in two passes: pass one collects the whole-paragraph reference pool; pass two attributes line by line (the paragraph pool backs it up)."""
        nonlocal para, drifts
        if not para:
            return
        buf = para
        para = []
        pool = []
        scanned = []
        for no, seg in buf:
            mentions, flags = mentions_of(seg)
            for _pos, _tier, ent in mentions:
                if ent not in pool:
                    pool.append(ent)
            scanned.append((no, seg, mentions, flags))
        for no, seg, mentions, flags in scanned:
            d, r, u = account(no, mentions, flags, pool)
            drifts.extend(d)
            refs_total[0] += r
            unres_total[0] += u

    def flush_join():
        """Continuation-assembly close-out -> the logical line enters the code-block buffer."""
        nonlocal cur, pend_join, code_block
        if not cur:
            return
        ln0 = cur[0][0]
        joined = " ".join(s for _, s in cur)
        code_block.append((ln0, joined))
        cur = []
        pend_join = False

    for no, raw in enumerate(lines, start=1):
        seg = raw.rstrip("\r")
        st = seg.strip()
        if st.startswith("```"):
            flush_para()
            if pend_join:
                cur.append((no, ""))
                flush_join()
            flush_code_block()
            in_code = not in_code
            continue
        if in_code:
            if pend_join:
                if seg.rstrip().endswith("\\") and len(seg.rstrip()) > 1:
                    cur.append((no, seg.rstrip()[:-1]))
                    continue
                cur.append((no, seg))
                flush_join()
                continue
            if seg.rstrip().endswith("\\") and len(seg.rstrip()) > 1:
                cur.append((no, seg.rstrip()[:-1]))
                pend_join = True
                continue
            cur.append((no, seg))
            flush_join()
            continue
        # prose: a heading line forms its own paragraph (keeps the pool from leaking across sections); a blank line closes the paragraph
        if st.startswith("#"):
            flush_para()
            para.append((no, seg))
            continue
        if not st:
            flush_para()
            continue
        para.append((no, seg))
    flush_para()
    if pend_join or cur:
        flush_join()
    flush_code_block()

    drift_n = len(drifts)
    parts = ["refs=%d" % refs_total[0], "unresolved=%d" % unres_total[0],
             "oos=%d" % oos_local[0]]
    if drift_n:
        shown = drifts[:DRIFT_LINE_CAP]
        parts.append("drift=%d" % drift_n)
        parts += ["L%d: %s" % (no, clip(d, 160)) for no, d in shown]
        if len(drifts) > DRIFT_LINE_CAP:
            parts.append("%d more not listed (cap %d)"
                         % (len(drifts) - DRIFT_LINE_CAP, DRIFT_LINE_CAP))
    else:
        parts.append("drift=0")
    item = {"kind": "flag", "target": rel,
            "status": "drift" if drift_n else "ok",
            "detail": clip("; ".join(parts))}
    return item, drift_n, refs_total[0]


def check_flags(repo, ctx):
    """Check 3 main flow: real help runs -> per-file scans -> checks (one item per file plus the unproven overflow-tool items)."""
    checks = []
    files = doc_files(repo)
    ctx.load_helps()
    total_drift = 0
    for rel in files:
        item, drift_n, _refs = scan_doc(repo, rel, ctx)
        checks.append(item)
        total_drift += drift_n
    for ov_rel in ctx.overflow:
        n = _refs_for(ctx, files, ov_rel)
        if n:
            checks.append({"kind": "flag", "target": ov_rel,
                           "status": "drift",
                           "detail": clip("over the help cap %d, --help not"
                                          " run; %d doc citations unproven (the"
                                          " flag check is incomplete for this"
                                          " tool)" % (ctx.help_cap, n))})
    return checks, total_drift, files


def _refs_for(ctx, files, tool_rel):
    """An overflow tool's citation count on the doc faces (a light rescan: tool references only, no flag judging)."""
    n = 0
    for rel in files:
        text = read_text(os.path.join(ctx.repo, rel), rel)
        masked = FLAG_RE.sub(lambda m: " " * len(m.group(0)), text)
        for m in PATH_RE.finditer(masked):
            if ctx.resolve_path(m.group(1)) == ("tool", tool_rel):
                n += 1
        for m in ctx.bare_re.finditer(masked):
            if ctx.resolve_bare(m.group(1)) == ("tool", tool_rel):
                n += 1
    return n


# ---- main flow ----

def run(args):
    """Main flow: value validation (2) -> audited-repo prechecks (9) -> checks 1/2/3 one by one -> the report (0/1)."""
    if args.help_cap is not None and args.help_cap < 1:
        raise UsageError("--help-cap must be >= 1, got %d" % args.help_cap)
    repo = args.repo
    if not os.path.isdir(repo):
        raise MissingInput("--repo directory missing: %s" % repo)
    for req in ("cw.sh", "README.md", "README-cw.md", "tests/run_tests.sh",
                "tests/README.md"):
        if not os.path.isfile(os.path.join(repo, req)):
            raise MissingInput("an audited-repo required input is missing: %s"
                               % req)
    print("=== DOC-LINT (docs-vs-implementation consistency, three checks) === repo=%s"
          % os.path.basename(os.path.abspath(repo)))

    # check 1: the tool table
    places = parse_cw_sh(repo)
    tt_checks, registry_rel, unrouted = check_tool_table(repo, places)
    route_map = {name: ent["path"] for name, ent in places["case"].items()
                 if name not in PSEUDO_ROUTES}
    print("[tool_table] checks=%d unrouted=%s"
          % (len(tt_checks), ",".join(unrouted) if unrouted else "none"))

    # check 2: the counts
    cnt_checks, cases_n = check_counts(repo)
    print("[count] CASES=%d checks=%d" % (cases_n, len(cnt_checks)))

    # check 3: the flags
    help_cap = args.help_cap
    if help_cap is None:
        help_cap = derived_help_cap(registry_rel)
    ctx = LintCtx(repo, registry_rel, route_map, help_cap)
    flag_checks, flag_drift, files = check_flags(repo, ctx)
    print("[flag] docs=%d help_run=%d/%d (cap %d) drift=%d"
          % (len(files), len(ctx.help_order), len(registry_rel),
             help_cap, flag_drift))

    checks = tt_checks + cnt_checks + flag_checks
    drift_n = sum(1 for c in checks if c["status"] == "drift")
    verdict = "drift" if drift_n else "consistent"
    counts = {}
    for kind in ("tool_table", "count", "flag"):
        counts[kind] = {
            "ok": sum(1 for c in checks
                      if c["kind"] == kind and c["status"] == "ok"),
            "drift": sum(1 for c in checks
                         if c["kind"] == kind and c["status"] == "drift")}
    oos_list = [{"file": f, "tool": t, "refs": n}
                for (f, t), n in sorted(ctx.oos.items())]
    report = {
        "schema": SCHEMA,
        "verdict": verdict,
        "repo": os.path.basename(os.path.abspath(repo)),
        "checks": checks,
        "counts": counts,
        "drift_total": drift_n,
        "out_of_scope": {"total": ctx.oos_total,
                         "refs": oos_list[:LIST_CAP],
                         "capped": max(0, len(oos_list) - LIST_CAP)},
        "registry": {"scripts": registry_rel,
                     "help_run": ctx.help_order,
                     "cap": help_cap,
                     "overflow": ctx.overflow},
        "args": {"repo": os.path.basename(os.path.abspath(repo)),
                 "help_cap": help_cap},
    }
    print("--- checks ---")
    for c in checks:
        print("  [%s] %-6s %s\n    %s"
              % (c["kind"], c["status"], c["target"], c["detail"]))
    if args.json:
        dump_json(report, args.json)
        print("json -> %s" % args.json)
    print("VERDICT: %s (exit %d)"
          % (verdict, 0 if verdict == "consistent" else 1))
    return 0 if verdict == "consistent" else 1


# ---- --selftest (tmp mini-repo fixtures; the consistency vectors + CLI codes + the idempotence vector) ----

MINI_TOOL_A = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_a.py — 演示器甲（doc_lint --selftest 迷你仓夹具·旗标形制仿
scan_v4_token --file/--json 形）"""
import argparse
ap = argparse.ArgumentParser(prog="tool_a",
                             description="演示器甲：--file/--json 两旗标")
ap.add_argument("--file", metavar="F", help="目标件")
ap.add_argument("--json", metavar="OUT", help="报告出账")
ap.parse_args()
'''

MINI_TOOL_B = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_b.py — 演示器乙（doc_lint --selftest 迷你仓夹具·旗标形制仿
cure_applier --dir/--apply 形）"""
import argparse
ap = argparse.ArgumentParser(prog="tool_b",
                             description="演示器乙：--dir/--apply 两旗标")
ap.add_argument("--dir", metavar="DIR", help="目标目录")
ap.add_argument("--apply", action="store_true", help="落刀")
ap.parse_args()
'''

MINI_TOOL_C = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_c.py: fixture tool three (the V7 cap-derivation vector's newly
registered tools/ entry point; flag shape mirrors tool_a)"""
import argparse
ap = argparse.ArgumentParser(prog="tool_c",
                             description="fixture tool three: --out/--mode")
ap.add_argument("--out", metavar="OUT", help="report output path")
ap.add_argument("--mode", metavar="M", help="run mode")
ap.parse_args()
'''


def make_mini_repo(root, hint_drop=None, count_drift=False, phantom=False):
    """tmp 迷你仓 fixture（形制 1:1 仿真仓四处：头注表/usage heredoc/hint_for/
    case 分派＋CASES 块＋三计数行＋doc 面）。落盘即返（None）。"""
    os.makedirs(os.path.join(root, "tools"))
    for name, body in (("tool_a.py", MINI_TOOL_A), ("tool_b.py", MINI_TOOL_B)):
        with io.open(os.path.join(root, "tools", name), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    hint_b = ('    b) echo "cw.sh b --dir DIR [--apply]   # 演示器乙 -> '
              'tools/tool_b.py" ;;\n') if hint_drop != "b" else ""
    cw = (
        "#!/usr/bin/env bash\n"
        "# cw.sh — mini fixture 统一入口（a/b 两器）\n"
        "#\n"
        "# 用法 Usage: bash cw.sh <tool> [args...]\n"
        "#\n"
        "# 工具表 Tools:\n"
        "#   a           演示器甲 -> tools/tool_a.py\n"
        "#               cw.sh a --file <f.v> [--json out.json]\n"
        "#   b           演示器乙 -> tools/tool_b.py\n"
        "#               cw.sh b --dir DIR [--apply]\n"
        "#   help        本帮助（help <tool> = 该工具一行提示）\n"
        "#\n"
        "# 路由契约 Routing contract:\n"
        "#   1. 参数与退出码 1:1 透传。\n"
        "set -u\n"
        "ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "usage() {\n"
        "  cat <<'EOF'\n"
        "cw.sh — mini fixture\n"
        "用法 Usage: bash cw.sh <tool> [args...]\n"
        "工具 Tools:\n"
        "  a           演示器甲 -> tools/tool_a.py\n"
        "  b           演示器乙 -> tools/tool_b.py\n"
        "  help        本帮助\n"
        "退出码 Exit codes: 0=pass 2=unknown-tool 9=missing\n"
        "EOF\n"
        "}\n"
        "hint_for() {\n"
        "  case \"$1\" in\n"
        "    a) echo \"cw.sh a --file <f.v> [--json out.json]   # 演示器甲 -> "
        "tools/tool_a.py\" ;;\n"
        + hint_b +
        "    *) return 1 ;;\n"
        "  esac\n"
        "}\n"
        "run_tool() {\n"
        "  local tool=\"$1\" rel=\"$2\"\n"
        "  shift 2\n"
        "  exec python3 \"$ROOT/$rel\" \"$@\"\n"
        "}\n"
        "case \"${1:-}\" in\n"
        "  a) shift; run_tool a \"tools/tool_a.py\" \"$@\" ;;\n"
        "  b) shift; run_tool b \"tools/tool_b.py\" \"$@\" ;;\n"
        "  help|-h|--help)\n"
        "    usage\n"
        "    exit 0 ;;\n"
        "  *)\n"
        "    echo \"cw.sh: 未知工具 unknown tool: $1\" >&2\n"
        "    exit 2 ;;\n"
        "esac\n")
    with io.open(os.path.join(root, "cw.sh"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(cw)
    os.makedirs(os.path.join(root, "tests"))
    with io.open(os.path.join(root, "tests", "run_tests.sh"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "#!/bin/bash\n"
            "# run_tests.sh — mini fixture 套件\n"
            "set -u\n"
            "REPO=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n"
            "CASES=\"\\\n"
            "t_a \\\n"
            "t_b\"\n"
            "t_a() { python3 -B \"$REPO/tools/tool_a.py\" --help >/dev/null; }\n"
            "t_b() { python3 -B \"$REPO/tools/tool_b.py\" --help >/dev/null; }\n"
            "for c in $CASES; do \"$c\" || exit 1; done\n")
    n = "3" if count_drift else "2"
    with io.open(os.path.join(root, "tests", "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# tests/ — mini\n"
            "套件自检（注入一恒红例）：\n"
            "ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   "
            "# 预期 2 过 / 1 红 / EXIT 1\n"
            "\n"
            "## 覆盖面（%s 例）\n" % n +
            "| # | 用例 |\n|---|------|\n| 1 | `t_a` |\n| 2 | `t_b` |\n")
    with io.open(os.path.join(root, "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# mini repo\n"
            "```\n"
            "├── tests/  # 自测套件（2 例）— test suite (2 cases)\n"
            "```\n")
    with io.open(os.path.join(root, "README-cw.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# cw.sh mini 速查\n"
            "| 工具 | 目标脚本 | 一行示例 |\n"
            "|------|----------|----------|\n"
            "| `a` | `tools/tool_a.py` | `bash cw.sh a --file demo.v "
            "--json out.json` |\n"
            "| `b` | `tools/tool_b.py` | `bash cw.sh b --dir src/ --apply` |\n")
    phantom_line = ("python3 tools/tool_a.py --bogus-flag demo.v 幻引判例。\n"
                    if phantom else "")
    os.makedirs(os.path.join(root, "docs"))
    with io.open(os.path.join(root, "docs", "note.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# note\n"
            "普查用 python3 tools/tool_a.py --file demo.v --json out.json。\n"
            "收哨按 --max-rounds 界定（无器上下文·unresolved 不判漂判例）。\n"
            + phantom_line)
    os.makedirs(os.path.join(root, "examples", "workflows"))
    with io.open(os.path.join(root, "examples", "workflows", "wf.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# wf\n"
            "```bash\n"
            "bash cw.sh a --file demo.v --json out.json\n"
            "bash cw.sh b --dir src/ --apply\n"
            "```\n")
    return root


def selftest():
    """Vectors (tmp mini-repo fixtures; fully offline; real subprocess --help
    runs against the fixture's small tools):
    V1  a consistent mini repo with zero drift (rc 0; verdict consistent; all
        three checks ok)
    V2  a missing tool-table row (the hint b line dropped) -> rc 1; a
        tool_table drift pointing at cw.sh:hint
    V3  a count drift (coverage 3 vs 2) -> rc 1; a count drift
    V4  a phantom flag citation (docs/note.md --bogus-flag) -> rc 1; a flag
        drift
    V5  CLI codes (--help 0; --bogus 2; missing --repo 9; --help-cap 0 -> 2)
    V6  JSON idempotence (same repo, two runs, different --json paths,
        byte-identical)
    V7  the derived help cap (the default = the measured registry size +
        the margin constant; a new tools/ registration raises the cap with
        zero manual steps; an explicit smaller cap keeps the over-cap
        report face: help not run, citations unproven, the effective cap
        named in the message)
    """
    tmp = tempfile.mkdtemp(prefix="rocqwash_doclint_self_")
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, PROG + ".py")

    def run(aargs):
        e = dict(os.environ)
        p = subprocess.run([sys.executable, "-B", script] + list(aargs),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=e)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    try:
        # ---- V1 a consistent mini repo, zero drift ----
        v1 = os.path.join(tmp, "v1")
        make_mini_repo(v1)
        j1 = os.path.join(tmp, "v1.json")
        p = run(["--repo", v1, "--json", j1])
        assert p.returncode == 0, p.stdout[-1200:]
        rep = json.loads(io.open(j1, encoding="utf-8").read())
        assert rep["schema"] == SCHEMA and rep["verdict"] == "consistent", rep
        assert rep["drift_total"] == 0, rep["drift_total"]
        assert all(c["status"] == "ok" for c in rep["checks"]), rep["checks"]
        kinds = sorted(set(c["kind"] for c in rep["checks"]))
        assert kinds == ["count", "flag", "tool_table"], kinds
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["count"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["flag"]["drift"] == 0, rep["counts"]
        assert len(rep["registry"]["help_run"]) == 2, rep["registry"]
        # every cited flag proven one by one: tool a --file/--json + tool b --dir/--apply
        v1_flag = [c for c in rep["checks"]
                   if c["kind"] == "flag" and c["target"]
                   == "examples/workflows/wf.md"]
        assert v1_flag and "refs=" in v1_flag[0]["detail"], v1_flag
        # a flag citation with no tool context = counted honestly as unresolved, never drift (V1 stays consistent)
        note = [c for c in rep["checks"]
                if c["kind"] == "flag" and c["target"] == "docs/note.md"]
        assert note and "unresolved=1" in note[0]["detail"], note

        # ---- V2 a missing tool-table row (the hint b line dropped) ----
        v2 = os.path.join(tmp, "v2")
        make_mini_repo(v2, hint_drop="b")
        j2 = os.path.join(tmp, "v2.json")
        p = run(["--repo", v2, "--json", j2])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j2, encoding="utf-8").read())
        assert rep["verdict"] == "drift", rep["verdict"]
        hit = [c for c in rep["checks"]
               if c["kind"] == "tool_table" and c["status"] == "drift"
               and c["target"] == "cw.sh:hint" and " b " in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["tool_table"]["drift"] >= 1, rep["counts"]

        # ---- V3 a count drift (coverage 3 vs 2) ----
        v3 = os.path.join(tmp, "v3")
        make_mini_repo(v3, count_drift=True)
        j3 = os.path.join(tmp, "v3.json")
        p = run(["--repo", v3, "--json", j3])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j3, encoding="utf-8").read())
        hit = [c for c in rep["checks"] if c["kind"] == "count"
               and c["status"] == "drift"
               and "3 != CASES 2" in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["count"]["drift"] == 1, rep["counts"]
        # the other two checks stay at zero drift (the drift is confined to the count domain; nothing cascades)
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["flag"]["drift"] == 0, rep["counts"]

        # ---- V4 a phantom flag citation (docs/note.md --bogus-flag) ----
        v4 = os.path.join(tmp, "v4")
        make_mini_repo(v4, phantom=True)
        j4 = os.path.join(tmp, "v4.json")
        p = run(["--repo", v4, "--json", j4])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j4, encoding="utf-8").read())
        hit = [c for c in rep["checks"] if c["kind"] == "flag"
               and c["status"] == "drift" and c["target"] == "docs/note.md"
               and "phantom" in c["detail"] and "--bogus-flag" in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["flag"]["drift"] == 1, rep["counts"]
        # the other two checks stay at zero drift
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["count"]["drift"] == 0, rep["counts"]

        # ---- V5 CLI codes + the --help-cap value validation ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-300:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should rc=2, got %d" % p.returncode
        p = run(["--repo", os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "missing --repo directory should rc=9, got %d" % p.returncode
        p = run(["--repo", v1, "--help-cap", "0"])
        assert p.returncode == 2, "--help-cap 0 should rc=2, got %d" % p.returncode

        # ---- V6 JSON idempotence: same repo, two runs, different --json paths, byte-identical ----
        j6a = os.path.join(tmp, "v6a.json")
        j6b = os.path.join(tmp, "v6b.json")
        p = run(["--repo", v1, "--json", j6a])
        assert p.returncode == 0, p.stdout[-400:]
        p = run(["--repo", v1, "--json", j6b])
        assert p.returncode == 0, p.stdout[-400:]
        ba = io.open(j6a, "rb").read()
        bb = io.open(j6b, "rb").read()
        assert ba == bb, "json byte drift = violation"
        rep = json.loads(ba.decode("utf-8"))
        assert rep["schema"] == SCHEMA and "doclint" in rep["schema"]

        # ---- V7 the derived help cap + the over-cap report face ----
        # derivation: the default cap = the measured registry size + margin,
        # and the whole registry gets its real --help run (zero overflow)
        rep1 = json.loads(io.open(j1, encoding="utf-8").read())
        n1 = len(rep1["registry"]["scripts"])
        assert rep1["registry"]["cap"] == n1 + HELP_CAP_MARGIN, \
            rep1["registry"]
        assert rep1["registry"]["overflow"] == [], rep1["registry"]
        assert sorted(rep1["registry"]["help_run"]) \
            == sorted(rep1["registry"]["scripts"]), rep1["registry"]
        # registration simulation: a third tools/ entry point joins the mini
        # repo; the derived cap follows the registry (n + margin) and covers
        # the new tool with zero manual steps (the retired manual constant
        # sat at the registry size and truncated until hand-raised; the
        # unrouted tool_c shows up as the check-1 missing-route drift by
        # design, which is what makes this run exit 1)
        v7 = os.path.join(tmp, "v7")
        make_mini_repo(v7)
        with io.open(os.path.join(v7, "tools", "tool_c.py"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(MINI_TOOL_C)
        j7 = os.path.join(tmp, "v7.json")
        p = run(["--repo", v7, "--json", j7])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j7, encoding="utf-8").read())
        n7 = len(rep["registry"]["scripts"])
        assert n7 == n1 + 1, rep["registry"]
        assert rep["registry"]["cap"] == n7 + HELP_CAP_MARGIN, \
            rep["registry"]
        assert rep["registry"]["cap"] > rep1["registry"]["cap"], \
            rep["registry"]
        assert sorted(rep["registry"]["help_run"]) \
            == sorted(rep["registry"]["scripts"]), rep["registry"]
        assert rep["registry"]["overflow"] == [], rep["registry"]
        assert not any("over the help cap" in c["detail"]
                       for c in rep["checks"]), rep["checks"]
        # over-cap semantics preserved: an explicit smaller cap truncates in
        # canonical order and the over-cap report face names the EFFECTIVE
        # cap (not the derivation input), the honesty face of the truncation
        j7c = os.path.join(tmp, "v7c.json")
        p = run(["--repo", v7, "--help-cap", "1", "--json", j7c])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j7c, encoding="utf-8").read())
        assert rep["registry"]["cap"] == 1, rep["registry"]
        assert rep["registry"]["help_run"] == ["tools/tool_a.py"], \
            rep["registry"]
        assert rep["registry"]["overflow"] == ["tools/tool_b.py",
                                               "tools/tool_c.py"], \
            rep["registry"]
        hit = [c for c in rep["checks"] if c["kind"] == "flag"
               and c["status"] == "drift"
               and c["target"] == "tools/tool_b.py"
               and "over the help cap 1" in c["detail"]
               and "unproven" in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["flag"]["drift"] >= 1, rep["counts"]

        print("DOC-LINT-SELFTEST PASS: the consistent repo with zero drift /"
              " the missing tool-table row (hint) / the count drift (3 vs 2) /"
              " the phantom flag (--bogus-flag) / the CLI codes + the cap value"
              " validation / the JSON idempotence byte-identical / the derived"
              " help cap (default = registry + margin, a new registration"
              " auto-follows, the over-cap face preserved): all seven vectors"
              " pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="the docs-vs-implementation consistency three-check tool:"
                    " the tool-table check (cw.sh four-place mutual inspection +"
                    " the tools/ generic-entry reconciliation) + the count check"
                    " (CASES vs tests/README.md vs README.md) + the flag check"
                    " (doc-cited flags vs real --help output, capped)"
                    " (schema rocqwash-doclint/1)")
    ap.add_argument("--repo", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), metavar="DIR",
        help="the audited repo root (default = the parent of the"
             " tools/ directory holding this file)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="the report output path (rocqwash-doclint/1;"
                         " sort_keys determinism)")
    ap.add_argument("--help-cap", dest="help_cap", type=int,
                    default=None, metavar="N",
                    help="the check-3 --help real-run tool cap (default:"
                         " derived at run time = the measured registry size"
                         " plus the margin constant, so a new tool"
                         " registration raises the cap with zero manual"
                         " steps; an explicit value wins; over-cap tools"
                         " truncate in canonical order and are listed"
                         " honestly)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        code = run(args)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except (MissingInput, ToolError) as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
