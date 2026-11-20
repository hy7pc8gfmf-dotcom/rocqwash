#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_scan_station.py — wrapper/scan_station.py 自测（tests/·Mac 适配席 rqadapt·20261031）

九判 subprocess 实跑（每例正/负判优先）：
  1 裸调指认卡        rc=0·卡含正本绝对路径与 md5·pin_match=True
  2 附断言正判        --expect-md5 <实md5> --identify → rc=0
  3 附断言负判        --expect-md5 <伪md5> --identify → rc=2（不出 PASS）
  4 嵌记断言          --check-pin --identify → rc=0（正本未漂·嵌记吻合）
  5 透传正判          --selftest → rc=0 且 stdout 含 PASS（正本 E364 冻结向量组经站可达）
  6 透传 rc 透传律    --file /nonexistent → rc=9（正本口径原样可达）
  7 正本缺失          --root <空根> --identify → rc=9
  8 站自检            --station-selftest → rc=0 且 PASS
  9 透传正判(文件面)  --file tests/fixtures/names_sample.v → rc=0 且 stdout 含 "RED stations:"

幂等：零写盘（无 --json/--hits-csv/--baseline 调用·不触仓不触沙箱）。
退出码：0=九判全过；1=任一红。
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
