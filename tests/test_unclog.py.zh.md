#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_unclog.py — tools/unclog.py 自测壳（tests/·20261111 v37 集成席挂接）

疏通堵塞闭环引擎（probe 归集→chain_graph 挑根→cure_applier apply→rescan/
resprobe 复核→verdict 判定·五步闭环·schema rocqwash-unclog/1）挂接件：器自带
--selftest 十矢量冻结向量组（绿径/诚实墙＋零链根补判/cure-miss/轮尽/缺省关
实证/JSON 幂等/frozen 在册红拒/--loop 哨态 JSONL/CLI 四码·全 --injector canned
罐装零真编译零真网络）已由铸席自证（退出码口径 2/2/9 三向由本集成席实跑验证：
--bogus=2·无参=2·--src 缺路=9），本壳只把它接进套件总入口并加用法面冒烟：
  1 --selftest rc=0 且 stdout 含 "UNCLOG-SELFTEST PASS" 冻结标记
  2 --help rc=0（argparse 用法面在位）
  3 --bogus rc=2／无输入面 rc=2／--src 缺路 rc=9（退出码口径抽验）

用法：
  python3 tests/test_unclog.py        # 套件内经 run_tests.sh 调
  python3 -B tests/test_unclog.py     # 手动（-B 禁 __pycache__）

零触律：零真编译零网络零触真仓零写盘（--selftest 自管 tmp 工作目录·本壳
只探用法面不跑真闭环）；python3 -B 禁 __pycache__。
退出码：0=三判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "unclog.py")
MARK = "UNCLOG-SELFTEST PASS"


def run(args):
    """子进程跑闭环引擎（stdout+stderr 合流·零写盘零网络零编译）。"""
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
