#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tool_selftests.py: tools/ selftest meta enumerator hookup (tests/).

Purpose.  The meta-verification layer for the tools/ selftest face: enumerate
  every tool under tools/*.py (helper modules whose file name starts with `_`
  are excluded) and require each to hold a declared --selftest face (the
  quoted flag literal in source) exiting rc=0, or a registered in-file
  exemption marker "# selftest-exempt: <basis>" (basis non-empty).  A red,
  missing, or undeclared selftest fails the meta test and lists the names,
  so any self-proof absence stays visible in every suite run on both CI faces.

Interface.  python3 tests/test_tool_selftests.py [--repo DIR] [--timeout N];
  suite entry via run_tests.sh t_tool_selftests.  --repo defaults to the
  repository root (the parent of tests/); --timeout is the per-tool
  subprocess cap in seconds (default 120).  An exempted tool never runs.

Dependencies.  Python 3 standard library only; one subprocess per declared
  face with python -B, the suite's own convention (no bytecode cache
  writes); zero network; zero writes (each tool's --selftest vector face
  touches its own temp fixtures only, by standing tool contract).

Evidence.  One line per tool: PASS, SKIP (rc=111, the suite's standing
  environment-absent code, with the tool's own reason), EXEMPT with the
  registered basis, or FAIL with class and detail; plus a bounded excerpt
  on a red selftest, a FAIL list, and a SUMMARY line; the universe derives
  from the tools/ directory at run time, never hard-coded.

Exit-codes.  0 all tools green, skipped, or exempted with a registered
  basis; 1 any FAIL (names listed); 2 usage error (unknown flag,
  non-positive timeout, or --repo without a tools/ directory).
"""

import argparse
import io
import os
import re
import subprocess
import sys

# The registered exemption marker: one line, "# selftest-exempt: <basis>",
# basis non-empty (leading indentation tolerated, the shape after "#" is
# literal).
EXEMPT_RE = re.compile(r"^\s*# selftest-exempt: (\S.*)$")

# A quoted "--selftest" literal in the source (an argparse flag name or a
# pre-argparse argv membership form) declares the face.  The declaration is
# judged statically from the file text: a tool without the literal has no
# face to run, and per the contract it must then hold a registered
# exemption.
QUOTED_SELFTEST_RE = re.compile(r"""["']--selftest["']""")

# The suite's standing environment-absent yield code (run_tests.sh exit
# contract: a case exiting 111 = SKIP, not red).  A tool selftest that
# declares 111 reports its own loud reason; the meta layer carries it as a
# SKIP line, visible and excluded from the FAIL list.
SKIP_RC = 111

DEFAULT_TIMEOUT = 120
EXCERPT_LINES = 3
EXCERPT_WIDTH = 160


def tool_universe(tools_dir):
    """The enumerated universe: tools/*.py sorted, leading-`_` names excluded."""
    names = sorted(fn for fn in os.listdir(tools_dir)
                   if fn.endswith(".py") and not fn.startswith("_")
                   and os.path.isfile(os.path.join(tools_dir, fn)))
    return names


def read_text(path):
    """Read one tool file as utf-8 text (strict); errors propagate."""
    with io.open(path, "r", encoding="utf-8", errors="strict") as fh:
        return fh.read()


def exempt_basis(text):
    """The registered exemption basis (first marker line wins), or None.

    A marker registers only when the basis after the colon is non-empty;
    an exemption without a basis is not a registration.
    """
    for line in text.splitlines():
        m = EXEMPT_RE.match(line)
        if m:
            return m.group(1)
    return None


def run_selftest(path, timeout):
    """One --selftest subprocess (python -B, the suite convention).

    Returns (rc, excerpt): rc is the child exit code, or None when the cap
    killed the child; the excerpt is the first EXCERPT_LINES merged
    stdout/stderr lines, each clipped, decode errors replaced.
    """
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        pr = subprocess.run(
            [sys.executable, "-B", path, "--selftest"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None, ""
    out = pr.stdout.decode("utf-8", errors="replace")
    lines = [ln[:EXCERPT_WIDTH] for ln in out.splitlines()[:EXCERPT_LINES]]
    return pr.returncode, " | ".join(lines)


def main(argv=None):
    """Run the meta enumeration; return the process exit code (0/1/2)."""
    ap = argparse.ArgumentParser(
        description="tools/ selftest meta enumerator: every tool green on"
                    " --selftest or exempted with a registered basis")
    ap.add_argument("--repo", default=None,
                    help="repository root (default: the parent of tests/)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help="per-tool subprocess cap in seconds (default %d)"
                         % DEFAULT_TIMEOUT)
    args = ap.parse_args(argv)
    if args.timeout <= 0:
        ap.error("--timeout must be a positive number of seconds")
    repo = args.repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_dir = os.path.join(repo, "tools")
    if not os.path.isdir(tools_dir):
        print("META-ENUMERATOR-ERROR: no tools/ directory under %s" % repo)
        return 2
    names = tool_universe(tools_dir)
    if not names:
        print("META-ENUMERATOR-ERROR: no tools/*.py found under %s" % tools_dir)
        return 2
    fails = []
    passed = skipped = exempted = failed = 0
    print("[META] universe=%d tools, per-tool cap %ds (failures are re-listed"
          " at the end; the per-tool log below is alphabetical)" % (len(names), args.timeout))
    for name in names:
        rel = "tools/" + name
        path = os.path.join(tools_dir, name)
        try:
            text = read_text(path)
        except (OSError, UnicodeDecodeError) as e:
            failed += 1
            fails.append(rel)
            print("[FAIL] %s unreadable: %s" % (rel, e))
            continue
        if not QUOTED_SELFTEST_RE.search(text):
            # No declared face: the contract requires a registered exemption.
            # Judged statically from the file text; the tool is not invoked.
            basis = exempt_basis(text)
            if basis is not None:
                exempted += 1
                print("[EXEMPT] %s basis=%s" % (rel, basis))
            else:
                failed += 1
                fails.append(rel)
                print("[FAIL] %s missing: no --selftest face declared in"
                      " source and no registered exemption marker" % rel)
            continue
        rc, excerpt = run_selftest(path, args.timeout)
        if rc == 0:
            passed += 1
            print("[PASS] %s" % rel)
            continue
        if rc == SKIP_RC:
            skipped += 1
            print("[SKIP] %s rc=111 (the suite's environment-absent code)%s"
                  % (rel, (" reason: %s" % excerpt) if excerpt else ""))
            continue
        failed += 1
        fails.append(rel)
        if rc is None:
            print("[FAIL] %s timeout: exceeded %ss" % (rel, args.timeout))
        else:
            detail = "red: --selftest exited rc=%s" % rc
            if excerpt:
                detail += " excerpt: %s" % excerpt
            print("[FAIL] %s %s" % (rel, detail))
    print("[SUMMARY] pass=%d skip=%d exempt=%d fail=%d total=%d"
          " universe=tools/*.py (leading-'_' names excluded) timeout=%ss"
          % (passed, skipped, exempted, failed, len(names), args.timeout))
    if fails:
        print("[FAILURES] %d: %s" % (len(fails), ", ".join(fails)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
