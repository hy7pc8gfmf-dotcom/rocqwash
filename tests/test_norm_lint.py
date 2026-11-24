#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_norm_lint.py — tests/ suite adapter for tools/norm_lint.py.

Purpose.  Brings the annotation-face normalization lint (report-only first
  form) into the suite entry and adds usage-face smoke checks.  The tool's
  own correctness is attested by its --selftest vectors (map-load,
  jargon-hit, fields-missing, substring-exemption, whitelist-exemption,
  english-clean, coq-comment-face); this shell wires those vectors into the
  suite and probes the exit-code contract.

Interface.  Invoked by tests/run_tests.sh (t_norm_lint) or standalone:
  python3 -B tests/test_norm_lint.py.  Three checks:
  1 --selftest exits 0 with seven PASS vector lines and no FAIL line;
  2 --help exits 0 (argparse usage face present);
  3 exit-code contract spot checks: --bogus 2; missing --tree 9;
    --selftest combined with scan flags 2; --file with an unsupported
    extension 2; missing --jargon-map 9.

Dependencies.  Python 3 standard library only (os, subprocess, sys); runs
  the tool as a subprocess with -B; no network, no compile, no writes to
  the repository.

Evidence.  Every check is a deterministic subprocess invocation against the
  in-repository tool; the exit-code probes were each verified by direct
  runs before being encoded here.

Exit-codes.  0 = all three checks pass; 1 = any check fails (fail-loud:
  each failure is listed on stdout, never silent).
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "norm_lint.py")


def run(args):
    """Run the tool as a subprocess; merged stdout+stderr, no writes."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def main():
    fails = []
    rc, out = run(["--selftest"])
    n_pass = sum(1 for line in out.splitlines() if line.startswith("PASS "))
    if rc != 0 or n_pass != 7 or "FAIL " in out:
        fails.append("check1 --selftest should exit 0 with seven PASS vector "
                     "lines and no FAIL line (got rc=%d, PASS=%d)"
                     % (rc, n_pass))
        print(out)
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check2 --help should exit 0 (got rc=%d)" % rc)
        print(out)
    probes = [
        (["--bogus"], 2),
        (["--tree", os.path.join(REPO, "no-such-dir-norm-lint-selftest")], 9),
        (["--selftest", "--tree", REPO], 2),
        (["--file", os.path.join(REPO, "LICENSE")], 2),
        (["--file", TOOL, "--jargon-map",
          os.path.join(REPO, "no-such-map-norm-lint-selftest.md")], 9),
    ]
    want = [w for _a, w in probes]
    got = []
    for args, _want in probes:
        rc_p, _out = run(args)
        got.append(rc_p)
    if got != want:
        fails.append("check3 exit-code contract should be %s (got %s)"
                     % (want, got))
    print("== test_norm_lint: %d pass / %d fail =="
          % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
