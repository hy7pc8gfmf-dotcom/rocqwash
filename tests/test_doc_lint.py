#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_doc_lint.py — minimal selftest shell for tools/doc_lint.py (rocqwash tests/).

Purpose.  Wire the docs-vs-implementation consistency three-check tool
  (schema rocqwash-doclint/1) into the suite entry point (tests/run_tests.sh,
  lane `t_doclint`) and smoke its usage and exit-code faces; the checker
  attests its own --selftest frozen vector group, and this shell adds no
  vectors (marker + usage face).

Interface.  python3 tests/test_doc_lint.py    # suite lane (run_tests.sh);
  python3 -B tests/test_doc_lint.py  # manual; -B keeps __pycache__ off.
  Check 1: --selftest exits 0 and stdout carries the frozen marker
  "DOC-LINT-SELFTEST PASS"; check 2: --help exits 0 (the argparse usage
  face is present); check 3: exit-code sampling (--bogus 2 / --help-cap 0
  2 / --repo with a missing directory 9).

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/doc_lint.py as a subprocess; zero network, zero disk writes, no
  real-repository touch (the checker's --selftest synthesizes a tmp
  mini-repo fixture it writes and cleans itself).

Evidence.  The checker's --selftest frozen vector group (V1 consistent repo
  zero drift; V2 missing hint; V3 count drift; V4 phantom reference; V5 CLI
  codes plus --help-cap 0 -> 2; V6 JSON idempotence; V7 the derived help
  cap, registration auto-follow, over-cap face kept) is self-documented in
  tools/doc_lint.py; this shell re-asserts the marker and usage face and
  samples the exit codes (0=consistent, 1=drift, 2=usage, 9=missing input).

Exit-codes.  0 = all three checks pass; 1 = at least one check failing
  (the failing checks are listed loudly, never silent).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "doc_lint.py")
MARK = "DOC-LINT-SELFTEST PASS"


def run(args):
    """Run the checker in a subprocess (stdout+stderr merged; zero disk
    writes, zero network)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1: --selftest expected rc=0 with %r in stdout"
                     " (observed rc=%d)" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2: --help expected rc=0 (observed rc=%d)" % rc)
        print(out)
    rc_b, _o = run(["--bogus"])
    rc_c, _o = run(["--repo", REPO, "--help-cap", "0"])
    rc_m, _o = run(["--repo", os.path.join(REPO, "no-such-dir")])
    if not (rc_b == 2 and rc_c == 2 and rc_m == 9):
        fails.append("check 3: exit codes expected bogus=2 / --help-cap 0=2"
                     " / missing-repo=9 (observed %d/%d/%d)"
                     % (rc_b, rc_c, rc_m))
    print("== test_doc_lint: %d passing / %d failing =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
