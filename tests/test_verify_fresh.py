#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verify_fresh.py — verify/verify_vo.py --require-fresh fresh-compile 防线自测
（tests/·本轮实战判例工具化②·20261101）

Purpose.  Self-test card for verify/verify_vo.py --require-fresh: the stale-vo false-green case toolized (eight vectors).
Interface.  `python3 -B tests/test_verify_fresh.py` (also via tests/run_tests.sh); no arguments.
Dependencies.  Python 3 standard library only; drives verify/verify_vo.py (a frozen file) as a subprocess.
Evidence.  Per-judgment judge calls assert each vector's expected verdict.
Exit-codes.  0 = all eight sections pass; 1 = any vector red (fail-loud).

divmod_gen 陈旧 vo 假绿判例的工具化防线直测（--require-fresh <v> <vo>）：
  1 自证        verify_vo --selftest 十三判全过（rc 0·含防线四判）
  2 正判        魔数对＋vo 新鲜 → rc 0·FRESH-OK 词面
  3 陈 vo 负例  v mtime 拨未来 → rc 9·FAIL-LOUD 陈 vo 假绿通道词面（fail-loud）
  4 坏魔数负例  头 8 字节非 436f712100015ff4 → rc 9（新鲜也拦——非本链产物）
  5 缺件        缺 v／缺 vo → rc 9
  6 用法        单参（nargs=2）→ rc 2／与 --v/--vo 混用 → rc 2
  7 CLI 形制    --help 0／未知形参 2
  8 魔数口径    冻结向量 436f712100015ff4＝Rocq 9.1 真机产物头 8 字节
                （_reproPC2/S01_BaseRing.vo xxd 实证·本测以 bytes.fromhex 冻结在卷）

幂等：临时目录即写即清·零仓库写盘·零网络·零触真仓零编译。
抖动隔离（20261116 F3 agent）：v/vo 背靠背写盘间隔可小于本机 mtime 粒度（实测
~1ms·检验 40 轮 26 轮同刻）→「vo 严格新于 v」随机翻转（单跑/套件内皆翻）。
夹具在正判前显式钉 v=vo−10s，使判据只验语义不赌写盘时刻；判据本体在
verify/verify_vo.py（frozen8 冻结件·红禁修）不动——其 selftest 内两处背靠背
写盘（:162-165/:184-186）同病残留，待 frozen8 重签波治理（E2-3 台账升级行）。
"""
import io
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "verify", "verify_vo.py")

VO_MAGIC_HEX = "436f712100015ff4"  # 承 verify_vo.py 冻结口径（9.1 真机产物实证）


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tverifyfresh_")
    try:
        v = os.path.join(tmp, "probe.v")
        vo = os.path.join(tmp, "probe.vo")
        with io.open(v, "w", encoding="utf-8") as fh:
            fh.write("Lemma t : True.\nProof. exact I. Qed.\n")
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(VO_MAGIC_HEX) + b"\x00JUNK")
        # 钉环境（抖动隔离·承头注）：上两行背靠背写盘的间隔可小于本机 mtime
        # 粒度（~1ms）→ 同刻概率 65%（检验 40 轮 26 轮），第 2 节正判要求
        # 「vo 严格新于 v」即随机翻红（rc 9）。显式把 v 拨早 10s：正判只验
        # 判据语义（严格大于），不赌写盘时刻；第 3 节负例把 v 拨到未来 +50s
        # 仍远后于 vo，rc 9 判据不受本钉影响。
        vo_m = os.path.getmtime(vo)
        os.utime(v, (vo_m - 10.0, vo_m - 10.0))

        # 1 工具自证（十三判·含防线四判）
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout
              and "require-fresh" in p.stdout, p.stdout[-400:])

        # 2 正判：魔数对＋新鲜 → rc 0 FRESH-OK
        p = run(["--require-fresh", v, vo])
        check("正判_FRESH-OK", p.returncode == 0 and "FRESH-OK" in p.stdout,
              "rc=%d" % p.returncode)

        # 3 陈 vo 负例：v 拨未来 → rc 9 fail-loud
        import time
        stale = time.time() + 50
        os.utime(v, (stale, stale))
        p = run(["--require-fresh", v, vo])
        check("陈vo_rc9", p.returncode == 9 and "FAIL-LOUD" in p.stdout
              and "陈 vo" in p.stdout, "rc=%d" % p.returncode)
        os.utime(v, None)

        # 4 坏魔数负例：新鲜但非 9.1 头 → rc 9
        with open(vo, "wb") as f:
            f.write(b"\xde\xad\xbe\xef\x00\x01\x02\x03")
        p = run(["--require-fresh", v, vo])
        check("坏魔数_rc9", p.returncode == 9 and "436f712100015ff4" in p.stdout,
              "rc=%d" % p.returncode)
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(VO_MAGIC_HEX))

        # 5 缺件：缺 vo／缺 v → rc 9
        p = run(["--require-fresh", v, os.path.join(tmp, "gone.vo")])
        check("缺vo_9", p.returncode == 9, "rc=%d" % p.returncode)
        p = run(["--require-fresh", os.path.join(tmp, "gone.v"), vo])
        check("缺v_9", p.returncode == 9, "rc=%d" % p.returncode)

        # 6 用法：单参 → 2（argparse nargs=2）；与 --v/--vo 混用 → 2
        p = run(["--require-fresh", v])
        check("单参_2", p.returncode == 2, "rc=%d" % p.returncode)
        p = run(["--require-fresh", v, vo, "--v", v])
        check("混用_2", p.returncode == 2, "rc=%d" % p.returncode)

        # 7 CLI 形制：--help 0／未知形参 2
        p = run(["--help"])
        check("help_0", p.returncode == 0 and "usage" in p.stdout,
              "rc=%d" % p.returncode)
        p = run(["--bogus"])
        check("未知形参_2", p.returncode == 2, "rc=%d" % p.returncode)

        # 8 魔数口径冻结在卷：本测冻结向量＝verify_vo.py VO_MAGIC_HEX
        spec = None
        import importlib.util
        spec = importlib.util.spec_from_file_location("verify_vo_mod", TOOL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        check("魔数_冻结口径", mod.VO_MAGIC_HEX == VO_MAGIC_HEX,
              repr(getattr(mod, "VO_MAGIC_HEX", None)))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-16s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-VERIFY-FRESH FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-VERIFY-FRESH PASS: selftest/FRESH-OK正判/陈vo拦9/坏魔数拦9/缺件9/"
              "用法2×2/help0/魔数冻结口径 八节全过（divmod_gen 陈旧 vo 假绿判例工具化）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
