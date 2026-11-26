#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verify_born.py — wrapper/verify_born.py 自测（tests/·Mac 适配席 rqadapt·20261031）

Purpose.  Self-test card for wrapper/verify_born.py: nine subprocess vectors
  over the born-workpiece judgment paths (raw form, normalized form, negative
  verdict passthrough, account JSON, forged-assertion refusal), zero
  repository writes.
Interface.  `python3 -B tests/test_verify_born.py` (also via tests/run_tests.sh);
  no arguments.
Dependencies.  Python 3 standard library only; drives wrapper/verify_born.py
  and verify/verify_vo.py as subprocesses.
Evidence.  Per-judgment judge calls assert each vector's expected verdict.
Exit-codes.  0 = all nine vectors pass; 1 = any vector red (fail-loud).

九判 subprocess 实跑（每例正/负判优先·临时目录驱动零仓写）：
  1 裸调哑成功禁律    零参 → rc=2（判绿三路径 --v/--vo/--rc-file 必填）
  2 --help            rc=0 且含用法样例
  3 站自检            --station-selftest → rc=0 且 STATION-SELFTEST PASS（九判）
  4 正本指认          --identify → rc=0·含正本绝对路径＋md5＋pin_match: True
  5 裸形 born.rc 正判  "0\\n" 原件直喂 → rc=0（横幅含「裸形/原件直喂」）
  6 前缀形正判        "BORN_RC=0" 归一化 → rc=0（横幅含「归一化 rc=0」）
  7 前缀形负判        "BORN_RC=1" → rc=1（正本 FAIL 口径透传）
  8 --json 出账       正本逐件账 JSON 落临时目录·verdict=PASS
  9 伪断言败拒        --expect-md5 <伪> → rc=2 且卡出 FAIL（不带病判绿）

幂等：正本/repository/agent 域零写盘——全部工件（.v/.vo/born.rc/log/json）落 tempfile
mkdtemp，finally 兜底清理。退出码：0=九判全过；1=任一红。
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAP = os.path.join(REPO, "wrapper", "verify_born.py")
CANON = os.path.join(REPO, "verify", "verify_vo.py")
FAKE_MD5 = "0123456789abcdef0123456789abcdef"
MAGIC = "436f712100015ff4"   # 承 verify_vo.py:40 冻结口径


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
    tmp = tempfile.mkdtemp(prefix="rocqwash_verifyborn_t_")
    try:
        # 工件面：魔数 vo（新鲜）＋ born rc 三形＋净 log
        v = os.path.join(tmp, "probe.v")
        vo = os.path.join(tmp, "probe.vo")
        with io.open(v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma t : True.\nProof. exact I. Qed.\n")
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(MAGIC) + b"\x00JUNK")
        t_v, t_vo = 1000000000, 1000000100
        os.utime(v, (t_v, t_v))
        os.utime(vo, (t_vo, t_vo))

        def rc_file(name, text):
            p = os.path.join(tmp, name)
            with io.open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            return p

        base = ["--v", v, "--vo", vo]

        def judge(n, desc, cond, detail=""):
            nonlocal ok
            print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                         ("" if cond else "  " + detail)))
            ok = ok and cond

        rc, out, err = run([])
        judge(1, "裸调哑成功禁律 rc=2", rc == 2 and "判绿三路径必填" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, _ = run(["--help"])
        judge(2, "--help rc=0", rc == 0 and "born 判绿例" in out,
              "rc=%s out=%r" % (rc, out[:200]))

        rc, out, _ = run(["--station-selftest"])
        judge(3, "站自检九判 rc=0", rc == 0 and "STATION-SELFTEST" in out and "PASS" in out,
              "rc=%s out=%r" % (rc, out[:300]))

        rc, out, _ = run(["--identify"])
        judge(4, "正本指认 pin_match", rc == 0
              and os.path.abspath(CANON) in out and md5_of(CANON) in out
              and "pin_match: True" in out,
              "rc=%s out=%r" % (rc, out[:300]))

        rf = rc_file("bare0.born.rc", "0\n")
        rc, _, err = run(base + ["--rc-file", rf])
        judge(5, "裸形 born.rc 正判 rc=0", rc == 0 and "裸形" in err and "原件直喂" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rf = rc_file("pre0.born.rc", "BORN_RC=0\n")
        rc, _, err = run(base + ["--born-rc", rf])
        judge(6, "前缀形 BORN_RC=0 正判 rc=0", rc == 0 and "归一化 rc=0" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rf = rc_file("pre1.born.rc", "BORN_RC=1\n")
        rc, _, _ = run(base + ["--rc-file", rf])
        judge(7, "前缀形 BORN_RC=1 负判 rc=1", rc == 1, "rc=%s" % rc)

        rf = rc_file("json.born.rc", "0\n")
        acc = os.path.join(tmp, "acc.json")
        rc, _, _ = run(base + ["--rc-file", rf, "--json", acc])
        j = rc == 0 and os.path.isfile(acc)
        if j:
            with io.open(acc, encoding="utf-8") as fh:
                account = json.load(fh)
            j = (account.get("verdict") == "PASS"
                 and account["pieces"]["vo_magic"]["value"] == MAGIC
                 and account["pieces"]["exit"]["source"] == "--exit-file")
        judge(8, "--json 逐件账出账", j,
              "rc=%s acc_exists=%s" % (rc, os.path.isfile(acc)))

        rf = rc_file("id.born.rc", "0\n")
        rc, out, _ = run(["--expect-md5", FAKE_MD5, "--identify"] + base
                         + ["--rc-file", rf])
        judge(9, "伪断言败拒 rc=2", rc == 2 and "FAIL（md5 断言不符" in out,
              "rc=%s out=%r" % (rc, out[:300]))

        print("TEST-VERIFY-BORN:", "PASS (9/9)" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
