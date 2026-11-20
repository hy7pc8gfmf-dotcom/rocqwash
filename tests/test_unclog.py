#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_unclog.py — selftest shell for tools/unclog.py (rocqwash tests/).

Purpose.  Wire the blockage-clearing closed-loop engine (`probe` collection ->
  `chain_graph` root picking -> `cure_applier` apply -> rescan/`resprobe`
  recheck -> verdict decision; five-step loop, schema rocqwash-unclog/1) into
  the suite entry point and add a usage-face smoke.  The engine's own
  --selftest frozen vector group (passing path / honest wall + zero-chain-root
  recheck / cure-miss / rounds exhausted / default-off evidence / JSON
  idempotence / frozen registered failing-key rejection / --loop watcher-state
  JSONL / CLI four codes, all --injector canned: zero real compile, zero real
  network) is attested by the tool itself; this shell re-asserts:
  1 --selftest rc=0 and stdout carries the frozen marker "UNCLOG-SELFTEST PASS"
  2 --help rc=0 (the argparse usage face is present)
  3 --bogus rc=2 / no-input rc=2 / --src missing path rc=9 (exit-code sampling)

Interface.  python3 tests/test_unclog.py        # suite lane (run_tests.sh)
  python3 -B tests/test_unclog.py     # manual (-B keeps __pycache__ off)

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  tools/unclog.py as a subprocess; zero real compile, zero network, no
  real-repository touch, no disk writes (--selftest manages its own tmp working
  directory; this shell probes the usage face only, never the real loop).

Evidence.  Each check runs the live tool and compares rc and stdout against
  the frozen marker and the 2/2/9 exit-code convention of tools/unclog.py;
  failing checks print loudly, one FAIL line each, never silent.

Exit-codes.  0 = all three checks pass; 1 = at least one check failing.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "unclog.py")
MARK = "UNCLOG-SELFTEST PASS"


def run(args):
    """Run the closed-loop engine in a subprocess (stdout and stderr merged;
    zero disk writes, zero network, zero real compile)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("判1 --selftest 应 rc=0 且含 %r（实测 rc=%d）" % (MARK, rc))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("判2 --help 应 rc=0（实测 rc=%d）" % rc)
        print(out)
    rc_b, _o = run(["--bogus"])
    rc_n, _o = run([])
    rc_m, _o = run(["--src", "/tmp/rocqwash_test_unclog_missing_src_xyz"])
    if not (rc_b == 2 and rc_n == 2 and rc_m == 9):
        fails.append("判3 退出码口径应 bogus=2/无输入面=2/--src 缺路=9"
                     "（实测 %d/%d/%d）" % (rc_b, rc_n, rc_m))
    print("== test_unclog: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
