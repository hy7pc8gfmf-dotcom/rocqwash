#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_scan_station.py — selftest for wrapper/scan_station.py (rocqwash tests/).

Purpose.  Nine subprocess checks against the scan-station wrapper, expected
  outcome pinned per check:
  1 bare call: rc=0, the identification card carries the canonical file's absolute path and md5, pin_match=True
  2 assertion positive: --expect-md5 <real md5> --identify -> rc=0
  3 assertion negative: --expect-md5 <fake md5> --identify -> rc=2 (no PASS)
  4 pin assertion: --check-pin --identify -> rc=0 (canonical file undrifted, pin matches)
  5 pass-through positive: --selftest -> rc=0 and stdout carries PASS (the canonical file's frozen vector group is reachable through the station)
  6 pass-through rc rule: --file /nonexistent -> rc=9 (the canonical tool's exit-code convention relayed unchanged)
  7 canonical file missing: --root <empty root> --identify -> rc=9
  8 station self-check: --station-selftest -> rc=0 and PASS
  9 pass-through positive (file face): --file tests/fixtures/names_sample.v -> rc=0 and stdout carries "RED stations:"

Interface.  python3 tests/test_scan_station.py    # suite lane (run_tests.sh)
  python3 -B tests/test_scan_station.py  # manual (-B keeps __pycache__ off)

Dependencies.  Python 3 standard library only (hashlib, os, subprocess, sys);
  runs wrapper/scan_station.py as a subprocess; idempotent, zero disk writes
  (no --json/--hits-csv/--baseline calls; no repository or sandbox touch);
  the fixture tests/fixtures/names_sample.v is read-only.

Evidence.  Every check prints one judge line with PASS/FAIL plus the measured
  rc/stdout/stderr detail; the wrapper's --selftest and --station-selftest
  frozen vector groups are exercised live through the station.

Exit-codes.  0 = all nine checks pass; 1 = at least one check failing.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAP = os.path.join(REPO, "wrapper", "scan_station.py")
CANON = os.path.join(REPO, "scan", "mac_stmt_scan.py")
FIXTURE = os.path.join(REPO, "tests", "fixtures", "names_sample.v")
FAKE_ROOT = os.path.join(os.sep, "tmp", "rqadapt_nonexistent_root_probe")
FAKE_MD5 = "0123456789abcdef0123456789abcdef"


def md5_of(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable, "-B", WRAP] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    ok = True
    canon_md5 = md5_of(CANON)

    def judge(n, desc, cond, detail=""):
        nonlocal ok
        print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                     ("" if cond else "  " + detail)))
        ok = ok and cond

    rc, out, err = run([])
    judge(1, "裸调指认卡", rc == 0 and os.path.abspath(CANON) in out
          and canon_md5 in out and "pin_match: True" in out,
          "rc=%s out=%r err=%r" % (rc, out[:200], err[:200]))

    rc, out, err = run(["--expect-md5", canon_md5, "--identify"])
    judge(2, "附断言正判", rc == 0 and "verdict:   PASS" in out,
          "rc=%s out=%r" % (rc, out[:200]))

    rc, out, err = run(["--expect-md5", FAKE_MD5, "--identify"])
    judge(3, "附断言负判 rc=2", rc == 2 and "match=False" in out,
          "rc=%s out=%r" % (rc, out[:200]))

    rc, out, err = run(["--check-pin", "--identify"])
    judge(4, "嵌记断言", rc == 0 and "pin_match: True" in out,
          "rc=%s out=%r err=%r" % (rc, out[:200], err[:200]))

    rc, out, err = run(["--selftest"])
    judge(5, "透传正判 --selftest", rc == 0 and "PASS" in out and "[scan_station]" in err,
          "rc=%s out=%r err=%r" % (rc, out[:200], err[:200]))

    rc, out, err = run(["--file", "/nonexistent/rqadapt_probe.v"])
    judge(6, "透传 rc 透传律 rc=9", rc == 9 and "FILE-MISSING" in out,
          "rc=%s out=%r" % (rc, out[:200]))

    rc, out, err = run(["--root", FAKE_ROOT, "--identify"])
    judge(7, "正本缺失 rc=9", rc == 9 and "正本缺失" in err,
          "rc=%s err=%r" % (rc, err[:200]))

    rc, out, err = run(["--station-selftest"])
    judge(8, "站自检七判", rc == 0 and "STATION-SELFTEST" in out and "PASS" in out,
          "rc=%s out=%r" % (rc, out[:300]))

    rc, out, err = run(["--file", FIXTURE])
    judge(9, "透传正判 --file fixture", rc == 0 and "RED stations:" in out,
          "rc=%s out=%r" % (rc, out[:200]))

    print("TEST-SCAN-STATION:", "PASS (9/9)" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
