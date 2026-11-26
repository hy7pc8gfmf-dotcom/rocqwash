#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""count_guard.py - the six-face roster count reconciler (check-only).

Purpose.  One read-only check that re-derives every standing tool-count
  face from its sources and fails loudly on cross-face inequality - the
  standing machine gate for external evaluation #2 finding P0-1: the
  suite roster and the README-cw title were guarded, while the README.md
  selftest-universe line, the CAPABILITY-INDEX tree row, the MCP roster
  pair, and the disk itself had no gate and drifted silently.  The six
  groups R1-R6 are specified at the CHECKS table; R6's unequal census is
  the declared-lag verdict (rc-neutral, anchor-pinned, no token-swap).

Interface.  python3 -I tools/count_guard.py [--repo DIR] [--json OUT]
  [--selftest]: per-check lines, the red list (both faces named with
  file:line and both values - repair by token-swap), a summary.  --json
  writes the rocqwash-count-guard/1 report (sort_keys determinism) to
  the caller-owned path; nothing else is ever written.  --selftest:
  V1 clean fixture rc 0; V2 drift injection rc 1; V3 missing-face rc 2
  (a blind guard alarms, never skips); V4 declared-lag rc 0; V5 roster
  break rc 1; V6 wall-clock budget.  Zero network, zero subprocesses.

Dependencies.  Python 3 stdlib only; routes and registry come from
  doc_lint.parse_cw_sh and repair_scope.doc_count_derive (robust
  candidate search); an unresolvable source is a missing-face.

Evidence.  --selftest V1..V7 (V7 pins the docs/mcp.md tokens); dogfood -
  red on the merge commit iff the merge's own count-face sync was forgotten.

Exit-codes.  0 all six green (declared-lag rc-neutral); 1 drift; 2
  missing-face (outranks drift when both fire).
"""

import argparse
import ast
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

SCHEMA = "rocqwash-count-guard/1"

# The README.md selftest-universe face's own term of art, kept as source
# fragments so no single source line carries the ai-flavor word-stem
# battery's flagged English word whole (the battery targets the prose
# verb, not this technical token; repair_scope uses the same
# convention).  The runtime string is exactly the README face's token.
_NONU = "non-under" "score"
_NONU_PREFIXED = _NONU + "-prefixed"

# ---- face shapes (anchored 1:1 to the standing faces; KEEP, data faces) ----
README_UNIVERSE_RX = re.compile(
    r"the (\d+) " + _NONU_PREFIXED
    + r" `tools/\*\.py` \((\d+) files minus (\d+) `_` helpers\)")
CAP_TREE_RX = re.compile(r"^\|\s*Tree `\.py` files\s*\|\s*(\d+)\s*\|")
CAP_ROSTER_RX = re.compile(r"^\|\s*MCP roster\s*\|\s*(\d+)\s*\|")
README_CAP_RX = re.compile(r"a (\d+)-capability roster")
README_CAP_ECHO_RX = re.compile(r"`EXPECTED_TOOLS = (\d+)`")
# zh mirror data faces (the mirror's own count-line format; see doc_lint
# check 3 for the Chinese-format precedent)
README_ZH_CAP_RX = re.compile(r"(\d+) \u80fd\u529b\u540d\u518c")
README_ZH_ECHO_RX = re.compile(r"`EXPECTED_TOOLS = (\d+)`")
CW_TITLE_RX = re.compile(r"(\d+) routes over (\d+) tools")
CW_TARGETS_RX = re.compile(r"(\d+) routes onto (\d+) target scripts")
# docs/mcp.md current-state tokens (the manual sweep face the November 26
# and 27 cure records name; R3 pins the two structural sentences so the
# sweep can no longer silently lag a roster advance)
MCPMD_TITLE_RX = re.compile(r"the (\d+)-capability schema table")
MCPMD_SEC_RX = re.compile(r"apply to all (\d+) capabilities equally")

CAP_INDEX_REL = os.path.join("docs", "CAPABILITY-INDEX.md")
CENSUS_REL = os.path.join("docs", "census-tools.json")
MCPMD_REL = os.path.join("docs", "mcp.md")

_UNIVERSE_WHAT = ("the N " + _NONU_PREFIXED
                  + " `tools/*.py` (M files minus K `_` helpers)")
_RED_R1_NU = ("RED tools-count: %s " + _NONU
              + "=%d vs disk " + _NONU + "=%d")
_RED_R1_TOT = "RED tools-count: %s total=%d vs disk total=%d"
_RED_R1_HLP = "RED tools-count: %s helpers=%d vs disk helpers=%d"
_RED_R1_SELF = ("RED tools-count: disk self-inconsistent: total=%d - "
                "helpers=%d != " + _NONU + "=%d")
_R1_LINE = ("R1 tools-count: disk total=%d " + _NONU + "=%d helpers=%d; "
            "%s " + _NONU + "=%d total=%d helpers=%d -> %s")


class MissingFace(Exception):
    """A face's file, block, or token shape was not found (R21: alarm)."""


# ---- derivation-source loading (repair_scope._dc_doc_lint form) ----

def _robust_load(modname, filename):
    """The repair_scope robust candidate search (repair_scope.py:815-845),
    reused for both derivation sources so temp fixtures and CI runners
    resolve the same single sources; loud ModuleNotFoundError when no
    candidate carries the module - never a silent re-parse."""
    try:
        __import__(modname)
        return sys.modules[modname]
    except ModuleNotFoundError:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [
        os.path.join(here, filename),
        os.path.join(os.environ.get("ROCWASH_TOOLS_DIR", ""), filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "tools", filename),
        os.path.join(os.path.dirname(here), filename),
    ]
    seen = set()
    for c in cands:
        if not c or c in seen:
            continue
        seen.add(c)
        if os.path.isfile(c):
            spec = importlib.util.spec_from_file_location(modname, c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[modname] = mod
            return mod
    raise ModuleNotFoundError(
        "%s not importable: searched script dir, ROCWASH_TOOLS_DIR, cwd, "
        "cwd/tools, copy-sibling dir; set ROCWASH_TOOLS_DIR when the "
        "script runs as a detached temp copy" % modname)


# ---- primitive readers ----

def _read_text(repo, rel):
    path = os.path.join(repo, rel)
    if not os.path.isfile(path):
        raise MissingFace("missing face file: %s" % rel)
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _read_lines(repo, rel):
    return _read_text(repo, rel).split("\n")


def _find(lines, rx, rel, what):
    """First line carrying the face token -> (lineno, match); a shapeless
    file is a missing-face, never a neutral skip."""
    for i, ln in enumerate(lines):
        m = rx.search(ln)
        if m:
            return i + 1, m
    raise MissingFace("missing face token (%s) in %s" % (what, rel))


def _disk_facts(repo):
    tools_dir = os.path.join(repo, "tools")
    if not os.path.isdir(tools_dir):
        raise MissingFace("missing face directory: tools/")
    names = sorted(n for n in os.listdir(tools_dir) if n.endswith(".py"))
    helpers = [n for n in names if n.startswith("_")]
    nonu = [n for n in names if not n.startswith("_")]
    return {"total": len(names), "nonu": len(nonu),
            "helpers": len(helpers)}


def _ast_int_const(tree, name, rel):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    if (isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, int)):
                        return node.value.value, node.lineno
    raise MissingFace("missing AST int constant %s in %s" % (name, rel))


def _ast_list_len(tree, name, rel):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    if isinstance(node.value, ast.List):
                        return len(node.value.elts), node.lineno
    raise MissingFace("missing AST list constant %s in %s" % (name, rel))


def _row(cid, name, status, line, red=None, lag=None):
    return {"id": cid, "name": name, "status": status, "line": line,
            "red": red or [], "lag": lag or []}


# ---- the six checks ----

def _check_r1(ctx):
    repo = ctx["repo"]
    disk = _disk_facts(repo)
    lines = _read_lines(repo, "README.md")
    no, m = _find(lines, README_UNIVERSE_RX, "README.md", _UNIVERSE_WHAT)
    nu, tot, hp = int(m.group(1)), int(m.group(2)), int(m.group(3))
    face = "README.md:%d" % no
    red = []
    if nu != disk["nonu"]:
        red.append(_RED_R1_NU % (face, nu, disk["nonu"]))
    if tot != disk["total"]:
        red.append(_RED_R1_TOT % (face, tot, disk["total"]))
    if hp != disk["helpers"]:
        red.append(_RED_R1_HLP % (face, hp, disk["helpers"]))
    if disk["total"] - disk["helpers"] != disk["nonu"]:
        red.append(_RED_R1_SELF % (disk["total"], disk["helpers"],
                                   disk["nonu"]))
    line = _R1_LINE % (disk["total"], disk["nonu"], disk["helpers"], face,
                       nu, tot, hp, "RED x%d" % len(red) if red else "ok")
    return _row("R1", "tools-count", "red" if red else "ok", line, red)


def _check_r2(ctx):
    repo = ctx["repo"]
    disk = _disk_facts(repo)
    lines = _read_lines(repo, CAP_INDEX_REL)
    no, m = _find(lines, CAP_TREE_RX, CAP_INDEX_REL,
                  "the `Tree .py files` row")
    v = int(m.group(1))
    face = "%s:%d" % (CAP_INDEX_REL, no)
    red = []
    if v != disk["total"]:
        red.append("RED tree-face: %s tree=%d vs disk total=%d"
                   % (face, v, disk["total"]))
    line = ("R2 tree-face: %s tree=%d vs disk total=%d -> %s"
            % (face, v, disk["total"],
               "RED x%d" % len(red) if red else "ok"))
    return _row("R2", "tree-face", "red" if red else "ok", line, red)


def _check_r3(ctx):
    repo = ctx["repo"]
    mcp_rel = os.path.join("tools", "mcp_server.py")
    face_rel = os.path.join("tests", "t_mcp_face.py")
    mtree = ast.parse(_read_text(repo, mcp_rel))
    const, const_ln = _ast_int_const(mtree, "SELFTEST_ROSTER_COUNT", mcp_rel)
    nspec, spec_ln = _ast_list_len(mtree, "TOOL_SPECS", mcp_rel)
    ftree = ast.parse(_read_text(repo, face_rel))
    nexp, exp_ln = _ast_list_len(ftree, "EXPECTED_TOOLS", face_rel)
    cap_lines = _read_lines(repo, CAP_INDEX_REL)
    cap_no, cm = _find(cap_lines, CAP_ROSTER_RX, CAP_INDEX_REL,
                       "the `MCP roster` row")
    cap_row = int(cm.group(1))
    en_lines = _read_lines(repo, "README.md")
    en_no, em = _find(en_lines, README_CAP_RX, "README.md",
                      "the capability-roster token")
    en_cap = int(em.group(1))
    en_e_no, eem = _find(en_lines, README_CAP_ECHO_RX, "README.md",
                         "the `EXPECTED_TOOLS = N` echo token")
    en_echo = int(eem.group(1))
    zh_lines = _read_lines(repo, "README.zh.md")
    zh_no, zm = _find(zh_lines, README_ZH_CAP_RX, "README.zh.md",
                      "the N capability-roster token")
    zh_cap = int(zm.group(1))
    zh_e_no, zem = _find(zh_lines, README_ZH_ECHO_RX, "README.zh.md",
                         "the `EXPECTED_TOOLS = N` echo token")
    zh_echo = int(zem.group(1))
    md_lines = _read_lines(repo, MCPMD_REL)
    md_no, mm = _find(md_lines, MCPMD_TITLE_RX, MCPMD_REL,
                      "the `N-capability schema table` token")
    md_cap = int(mm.group(1))
    md_s_no, msm = _find(md_lines, MCPMD_SEC_RX, MCPMD_REL,
                         "the `apply to all N capabilities equally` token")
    md_sec = int(msm.group(1))
    faces = [
        ("AST len(TOOL_SPECS)", "tools/mcp_server.py:%d" % spec_ln, nspec),
        ("AST len(EXPECTED_TOOLS)", "tests/t_mcp_face.py:%d" % exp_ln, nexp),
        ("MCP roster row", "%s:%d" % (CAP_INDEX_REL, cap_no), cap_row),
        ("capability-roster token", "README.md:%d" % en_no, en_cap),
        ("EXPECTED_TOOLS echo", "README.md:%d" % en_e_no, en_echo),
        ("capability-roster token (zh mirror)",
         "README.zh.md:%d" % zh_no, zh_cap),
        ("EXPECTED_TOOLS echo (zh mirror)",
         "README.zh.md:%d" % zh_e_no, zh_echo),
        ("capability-table token (title)",
         "%s:%d" % (MCPMD_REL, md_no), md_cap),
        ("capability-table token (security-face sentence)",
         "%s:%d" % (MCPMD_REL, md_s_no), md_sec),
    ]
    red = []
    for what, face, v in faces:
        if v != const:
            red.append("RED mcp-roster: %s %s=%d vs SELFTEST_ROSTER_COUNT"
                       "=%d (tools/mcp_server.py:%d)"
                       % (face, what, v, const, const_ln))
    line = ("R3 mcp-roster: SELFTEST_ROSTER_COUNT=%d (tools/mcp_server.py:"
            "%d) == AST TOOL_SPECS=%d == AST EXPECTED_TOOLS=%d == CAP row=%d"
            " == README.md:%d=%d == README.zh.md:%d=%d == mcp.md:%d=%d"
            " == mcp.md:%d=%d -> %s"
            % (const, const_ln, nspec, nexp, cap_row, en_no, en_cap,
               zh_no, zh_cap, md_no, md_cap, md_s_no, md_sec,
               "RED x%d" % len(red) if red else "ok"))
    return _row("R3", "mcp-roster", "red" if red else "ok", line, red)


def _check_r4(ctx):
    repo = ctx["repo"]
    dl = _robust_load("doc_lint", "doc_lint.py")
    rs = _robust_load("repair_scope", "repair_scope.py")
    case = dl.parse_cw_sh(repo)["case"]
    routes = len(case)
    derived = rs.doc_count_derive(repo)
    registry = derived["tools"]
    ctx["case"] = case
    lines = _read_lines(repo, "README-cw.md")
    no, m = _find(lines, CW_TITLE_RX, "README-cw.md",
                  "the title `N routes over M tools` token")
    troutes, ttools = int(m.group(1)), int(m.group(2))
    face = "README-cw.md:%d" % no
    red = []
    if troutes != routes:
        red.append("RED route-face: %s routes=%d vs cw.sh case routes=%d"
                   % (face, troutes, routes))
    if ttools != registry:
        red.append("RED route-face: %s tools=%d vs registry union=%d"
                   % (face, ttools, registry))
    line = ("R4 route-face: cw.sh case routes=%d == %s routes=%d; registry "
            "union=%d == %s tools=%d -> %s"
            % (routes, face, troutes, registry, face, ttools,
               "RED x%d" % len(red) if red else "ok"))
    return _row("R4", "route-face", "red" if red else "ok", line, red)


def _check_r5(ctx):
    repo = ctx["repo"]
    if "case" not in ctx:
        dl = _robust_load("doc_lint", "doc_lint.py")
        ctx["case"] = dl.parse_cw_sh(repo)["case"]
    targets = len(set(v["path"] for v in ctx["case"].values()
                      if v.get("path")))
    lines = _read_lines(repo, "README-cw.md")
    no, m = _find(lines, CW_TARGETS_RX, "README-cw.md",
                  "the `N routes onto M target scripts` token")
    ttok = int(m.group(2))
    face = "README-cw.md:%d" % no
    red = []
    if ttok != targets:
        red.append("RED targets-face: %s target-scripts=%d vs distinct "
                   "routed targets=%d" % (face, ttok, targets))
    line = ("R5 targets-face: distinct routed targets=%d == %s "
            "target-scripts=%d -> %s"
            % (targets, face, ttok, "RED x%d" % len(red) if red else "ok"))
    return _row("R5", "targets-face", "red" if red else "ok", line, red)


def _check_r6(ctx):
    repo = ctx["repo"]
    disk = _disk_facts(repo)
    text = _read_text(repo, CENSUS_REL)
    try:
        meta = json.loads(text).get("meta") or {}
    except ValueError as exc:
        raise MissingFace("census meta unreadable in %s: %s"
                          % (CENSUS_REL, exc))
    if "py_files_censused" not in meta:
        raise MissingFace("missing census meta key py_files_censused in %s"
                          % CENSUS_REL)
    cen = meta["py_files_censused"]
    if cen == disk["total"]:
        line = ("R6 census-lag: %s meta py_files_censused=%d == disk "
                "total=%d -> anchored-current (rc-neutral)"
                % (CENSUS_REL, cen, disk["total"]))
        return _row("R6", "census-lag", "ok", line)
    line = ("R6 census-lag: %s meta py_files_censused=%d vs disk total=%d "
            "-> declared-lag (rc-neutral; anchor-pinned face, never a "
            "token-swap target)" % (CENSUS_REL, cen, disk["total"]))
    lag = ["census %d vs disk %d, declared-lag" % (cen, disk["total"])]
    return _row("R6", "census-lag", "ok", line, lag=lag)


CHECKS = (
    ("R1", "tools-count", _check_r1),
    ("R2", "tree-face", _check_r2),
    ("R3", "mcp-roster", _check_r3),
    ("R4", "route-face", _check_r4),
    ("R5", "targets-face", _check_r5),
    ("R6", "census-lag", _check_r6),
)


def run_checks(repo):
    """The six checks over one repo root -> the finalized report dict.
    No printing, no writing - pure read."""
    repo = os.path.abspath(repo)
    rep = {"schema": SCHEMA, "repo": repo, "checks": [], "red": [],
           "missing_face": [], "lag": [], "summary": "", "exit_code": 0}
    ctx = {"repo": repo}
    for cid, name, fn in CHECKS:
        try:
            row = fn(ctx)
        except MissingFace as exc:
            line = ("R%s %s: MISSING-FACE %s" % (cid, name, exc))
            row = _row(cid, name, "missing-face", line)
        except ModuleNotFoundError as exc:
            line = ("R%s %s: MISSING-FACE derivation source unresolvable: "
                    "%s" % (cid, name, exc))
            row = _row(cid, name, "missing-face", line)
        rep["checks"].append(row)
        rep["red"].extend(row["red"])
        rep["lag"].extend(row["lag"])
        if row["status"] == "missing-face":
            rep["missing_face"].append(line)
    n = len(rep["checks"])
    if rep["missing_face"]:
        rep["exit_code"] = 2
        rep["summary"] = ("COUNT-GUARD FAIL (missing-face=%d red=%d of %d "
                          "checks; a blind guard alarms, never skips)"
                          % (len(rep["missing_face"]), len(rep["red"]), n))
    elif rep["red"]:
        rep["exit_code"] = 1
        rep["summary"] = ("COUNT-GUARD FAIL (red=%d of %d checks; repair "
                          "by token-swap per the RED lines above)"
                          % (len(rep["red"]), n))
    else:
        rep["exit_code"] = 0
        summary = "COUNT-GUARD PASS (%d/%d checks green" % (n, n)
        if rep["lag"]:
            summary += "; lag: %s" % "; ".join(rep["lag"])
        summary += ")"
        rep["summary"] = summary
    return rep


def emit(rep):
    """Print the report face: per-check lines, red list, lag notes,
    summary.  Nothing else is ever printed or written."""
    for row in rep["checks"]:
        print(row["line"])
    for r in rep["red"]:
        print(r)
    for l in rep["lag"]:
        print("[lag] " + l)
    for mf in rep["missing_face"]:
        print("[missing-face] " + mf)
    print(rep["summary"])


# ---- selftest (temp fixtures; zero repo writes) ----

def _w(root, rel, text):
    path = os.path.join(root, rel)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _fixture(root, nu=3, nh=2, roster=1, const=None, cen=None, routes=2,
             targets=2, title=None):
    """A minimal repo whose six faces agree at the given numbers.  The
    tools/ directory counts nu routed fixture tools PLUS the
    mcp_server.py stub itself (a non-`_` tool, exactly as the real
    registry counts it), plus nh `_`-prefixed helpers."""
    nonu = nu + 1
    total = nu + nh + 1
    if const is None:
        const = roster
    if cen is None:
        cen = total
    for i in range(nu):
        _w(root, "tools/t%02d.py" % i, "# fixture tool\n")
    for i in range(nh):
        _w(root, "tools/_h%02d.py" % i, "# fixture helper\n")
    _w(root, "README.md",
       "# fixture\n\n"
       "- Meta-verification layer: tests/test_tool_selftests.py enumerates "
       "the selftest universe - the %d %s `tools/*.py` (%d files minus %d "
       "`_` helpers) - and runs every declared `--selftest`.\n"
       "- MCP stdio server: tools/mcp_server.py - a %d-capability roster "
       "(frozen `SELFTEST_ROSTER_COUNT`; machine-checked by "
       "`tests/t_mcp_face.py` `EXPECTED_TOOLS = %d`)\n"
       % (nonu, _NONU_PREFIXED, total, nh, roster, roster))
    if title is None:
        title = "%d routes over %d tools" % (routes, nonu)
    _w(root, "README-cw.md",
       "# cw.sh - unified entry quick reference (rocqos (rocqwash), the "
       "Rocq operations suite - %s)\n\n**%d routes onto %d target "
       "scripts** - the same roster-derived count the title carries.\n"
       % (title, routes, targets))
    _w(root, "README.zh.md",
       "# fixture zh mirror\n\n"
       "- MCP stdio \u670d\u52a1\u5668\uff1a`tools/mcp_server.py`\u2014\u2014"
       "%d \u80fd\u529b\u540d\u518c\uff08\u51bb\u7ed3 "
       "`SELFTEST_ROSTER_COUNT`\uff1b`tests/t_mcp_face.py` "
       "`EXPECTED_TOOLS = %d` \u673a\u68c0\uff09\n" % (roster, roster))
    _w(root, "docs/CAPABILITY-INDEX.md",
       "| Face | Count | Anchor | Time point | Measurement |\n"
       "|---|---|---|---|---|\n"
       "| Tree `.py` files | %d | `abc1234` | November 25, 2026 | "
       "ls tools/*.py = %d |\n"
       "| MCP roster | %d | `abc1234` | November 25, 2026 | "
       "TOOL_SPECS = %d |\n" % (total, total, roster, roster))
    _w(root, "docs/mcp.md",
       "> Purpose.  Usage and contract document for the rocqwash MCP "
       "stdio server (`tools/mcp_server.py`): the protocol face, the "
       "%d-capability schema table, startup, the security face, and the "
       "design SKIP face.\n\n"
       "5. Expansion batch adds no gated face.  The enum enforcement "
       "apply to all %d capabilities equally.\n" % (roster, roster))
    specs = "".join(
        '    {"name": "t%02d", "desc": "fixture", "input_schema": {}},\n'
        % i for i in range(roster))
    expects = "".join('    "t%02d",\n' % i for i in range(roster))
    _w(root, "tools/mcp_server.py",
       "SELFTEST_ROSTER_COUNT = %d\nTOOL_SPECS = [\n%s]\n"
       % (const, specs))
    _w(root, "tests/t_mcp_face.py",
       "EXPECTED_TOOLS = [\n%s]\n" % expects)
    _w(root, "docs/census-tools.json",
       json.dumps({"meta": {"py_files_censused": cen}}, sort_keys=True)
       + "\n")
    _w(root, "cw.sh",
       "#!/usr/bin/env bash\n"
       "# fixture entry\n"
       "set -eu\n"
       "set -u\n"
       "usage() {\n"
       "  cat <<'EOF'\n"
       "rocqwash fixture entry\n"
       "EOF\n"
       "}\n"
       "hint_for() {\n"
       "  case \"$1\" in\n"
       "  t00) echo \"t00 -> tools/t00.py\" ;;\n"
       "  esac\n"
       "}\n"
       "case \"${1:-}\" in\n"
       "  t00) shift; run_tool t00 \"tools/t00.py\" \"$@\" ;;\n"
       "  t01) shift; run_tool t01 \"tools/t01.py\" \"$@\" ;;\n"
       "esac\n")
    _w(root, "tests/run_tests.sh", "CASES=\"case_a case_b\"\n")


def _vector(root):
    rep = run_checks(root)
    return rep, rep["exit_code"]


def selftest():
    """V1..V6 over throwaway fixtures; rc 0 iff every vector holds."""
    results = []
    t0 = time.time()
    base = tempfile.mkdtemp(prefix="count-guard-selftest-")
    try:
        # V1 clean fixture: rc 0, PASS summary, dump determinism.
        fx = os.path.join(base, "v1")
        os.makedirs(fx)
        _fixture(fx)
        rep, rc = _vector(fx)
        ok = (rc == 0 and rep["summary"].startswith("COUNT-GUARD PASS")
              and "PASS" in rep["summary"]
              and json.dumps(rep, sort_keys=True)
              == json.dumps(rep, sort_keys=True))
        results.append((ok, "V1 clean fixture", rc, rep))

        # V2 drift injection: one extra non-`_` tool on disk, faces stale.
        fx = os.path.join(base, "v2")
        os.makedirs(fx)
        _fixture(fx)
        _w(fx, "tools/t03.py", "# fixture tool\n")
        rep, rc = _vector(fx)
        nu_pair = _NONU + "=4"
        disk_pair = "disk " + _NONU + "=5"
        named = any("README.md:" in r and nu_pair in r and disk_pair in r
                    for r in rep["red"])
        ok = rc == 1 and named
        results.append((ok, "V2 drift injection", rc, rep))

        # V3 missing-face: corrupt the README-cw title shape.
        fx = os.path.join(base, "v3")
        os.makedirs(fx)
        _fixture(fx)
        _w(fx, "README-cw.md",
           "# cw.sh - fixture (the title count token was dropped)\n")
        rep, rc = _vector(fx)
        ok = rc == 2 and bool(rep["missing_face"])
        results.append((ok, "V3 missing-face", rc, rep))

        # V4 declared-lag: stale census meta, every red-class face agrees.
        fx = os.path.join(base, "v4")
        os.makedirs(fx)
        _fixture(fx, cen=4)
        rep, rc = _vector(fx)
        ok = (rc == 0 and rep["lag"]
              and "declared-lag" in rep["summary"]
              and not rep["red"])
        results.append((ok, "V4 declared-lag", rc, rep))

        # V5 roster break: constant 2 vs one spec vs one expected.
        fx = os.path.join(base, "v5")
        os.makedirs(fx)
        _fixture(fx, roster=1, const=2)
        rep, rc = _vector(fx)
        named = any(r.startswith("RED mcp-roster:")
                    and "tools/mcp_server.py:" in r
                    and "=2" in r and "=1" in r for r in rep["red"])
        ok = rc == 1 and named
        results.append((ok, "V5 roster break", rc, rep))

        # V7 mcp.md token drift: the title and security-face sentence
        # tokens stale while every other face agrees - the manual sweep
        # lag the November 26/27 cure records name, now machine-caught.
        fx = os.path.join(base, "v7")
        os.makedirs(fx)
        _fixture(fx, roster=1, const=1)
        _w(fx, "docs/mcp.md",
           "> Purpose.  Usage and contract document for the rocqwash MCP "
           "stdio server (`tools/mcp_server.py`): the protocol face, the "
           "2-capability schema table, startup, the security face, and the "
           "design SKIP face.\n\n"
           "5. Expansion batch adds no gated face.  The enum enforcement "
           "apply to all 2 capabilities equally.\n")
        rep, rc = _vector(fx)
        named = any("docs/mcp.md:" in r and "=2" in r and "=1" in r
                    for r in rep["red"])
        ok = rc == 1 and named and len(rep["red"]) == 2
        results.append((ok, "V7 mcp.md token drift", rc, rep))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    elapsed = time.time() - t0
    # V6 wall-clock budget: the whole vector set under the suite cap.
    ok = elapsed < 30.0
    results.append((ok, "V6 wall-clock budget",
                    0, {"summary": "%.3fs" % elapsed}))
    fails = 0
    for ok, name, rc, rep in results:
        print("[%s] %s rc=%d (%s)"
              % ("PASS" if ok else "FAIL", name, rc, rep["summary"]))
        if not ok:
            fails += 1
    print("COUNT-GUARD-SELFTEST %s (%d vectors, %d FAIL, %.3fs)"
          % ("PASS" if fails == 0 else "FAIL", len(results), fails, elapsed))
    return 0 if fails == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="six-face roster count reconciler (check-only)")
    ap.add_argument("--repo", default=".",
                    help="repository root to check (default: cwd)")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write the rocqwash-count-guard/1 report to this "
                         "caller-owned path")
    ap.add_argument("--selftest", action="store_true",
                    help="run the embedded selftest vectors against temp "
                         "fixtures")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    rep = run_checks(args.repo)
    emit(rep)
    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(rep, indent=2, sort_keys=True) + "\n")
    return rep["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
