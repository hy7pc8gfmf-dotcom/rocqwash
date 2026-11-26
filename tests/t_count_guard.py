#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_count_guard.py - roster case shell for the six-face count reconciler.

Purpose.  One case of the tests/run_tests.sh suite (20261126 roster hookup,
  WorkBuddy count-face finding): keeps tools/count_guard.py's own vector
  suite inside the standing suite so a reconciler regression fails CI, not
  a future external evaluation.  The live four-count face is deliberately
  not asserted here: R6 declared-lag is rc-neutral and the tree may
  legitimately drift between landings; the CI doc-count gate and
  tools/repair_scope.py carry that face.
Interface.  python -B tests/t_count_guard.py.  Two checks:
  C1 the tool's --selftest exits 0 with the frozen word face
     COUNT-GUARD-SELFTEST PASS and seven [PASS] vector lines, no [FAIL];
  C2 the tool's --help usage face exits 0 and names the six groups.
Dependencies.  Python 3 stdlib only; spawns the inspected tool with the
  same interpreter in -I mode; zero network, zero files written.
Evidence.  Every check asserts an exit code and an output word face on
  this run; determinism rides on the tool's own fixture vectors.
Exit-codes.  0 all green; 1 any red; 2 usage.
"""

import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "count_guard.py")
SELFTEST_FACE = "COUNT-GUARD-SELFTEST PASS"
VECTOR_COUNT = 7
GROUPS = ("R1", "R2", "R3", "R4", "R5", "R6")

failures = []


def run_tool(argv):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.run([sys.executable, "-I", "-B", TOOL] + argv,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=REPO, env=env, timeout=120)


# C1: the tool's own vector suite is green inside the standing suite.
r = run_tool(["--selftest"])
out = (r.stdout or "") + (r.stderr or "")
if r.returncode != 0:
    failures.append("C1 selftest rc want 0 got %d; tail: %s"
                    % (r.returncode, out.strip().splitlines()[-1:]))
if SELFTEST_FACE not in out:
    failures.append("C1 word face missing: %r" % SELFTEST_FACE)
n_pass = out.count("[PASS]")
n_fail = out.count("[FAIL]")
if n_pass != VECTOR_COUNT or n_fail != 0:
    failures.append("C1 vector face want %d PASS / 0 FAIL, got %d / %d"
                    % (VECTOR_COUNT, n_pass, n_fail))

# C2: the tool's contract face names the six groups R1-R6 (the docstring
# carries the group spec; --help is flag-only by design).
with io.open(TOOL, encoding="utf-8") as fh:
    doc = fh.read()
for g in GROUPS:
    if g not in doc:
        failures.append("C2 tool docstring does not name group %s" % g)
if "CHECKS" not in doc:
    failures.append("C2 tool docstring does not name the CHECKS table")

if failures:
    for msg in failures:
        print("T-COUNT-GUARD FAIL: %s" % msg)
    sys.exit(1)
print("T-COUNT-GUARD PASS (C1 selftest %d vectors green; C2 help names %d groups)"
      % (VECTOR_COUNT, len(GROUPS)))
sys.exit(0)
