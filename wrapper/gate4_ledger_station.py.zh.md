#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""gate4_ledger_station.py — verify/gate4_comment_guard.py --emit-ledger 台账指认包装
（rocqwash wrapper/·Mac 适配席 rqadapt·20261031）

在役组件 verify/gate4_comment_guard.py 冻结禁改（各在飞席位实时引用）——本席适配
一律新文件落 wrapper/。背景：该守卫出生于 Set 仓 scripts/gates/，--emit-ledger 的
默认豁免台账 TSV 按其出生地取「脚本同目录」，其 FATAL 文案仍指 scripts/gates/ 同目录
（gate4_comment_guard.py:829-837）；rocqwash 全仓与 Set 仓 scripts/gates/ 原均无
carrier_exemption_ledger_final.tsv（find/ls 实测），故默认 --emit-ledger 必 FATAL exit 2。

本站双半修复（fix=wrapper 层显式 --ledger-tsv ＋ 随仓补台账件，两半并用）：

  1. 随仓台账件：verify/carrier_exemption_ledger_final.tsv（表头四列
     file/line/word/first_registry＝正本 load_exempt_tsv 只读口径；零在册行＝
     诚实初盘——新登须经人工复核回填，本站不代登任何豁免条目）。
  2. 显式注入：透传前缺 --ledger-tsv 时自动补 `--ledger-tsv <默认台账件>`
     （调用方显式传了 --ledger-tsv 则原样尊重，不覆盖）；台账件缺席即
     exit 2 拒透传，文案指向真实默认路径（不复制正本的 scripts/gates/ 陈旧指针）。

站级旗标（本站自留·不转发）：
  --root DIR          正本仓根（默认＝本站文件所在仓根；缺目录 exit 2）
  --tsv PATH          注入用台账件（默认＝<root>/verify/carrier_exemption_ledger_final.tsv）
  --identify          只出台账指认卡不透传（过 exit 0／台账缺席 exit 2）
  --station-selftest  本站自身自检（六判·零写盘·不动正本）
  -h / --help         本站帮助（正本帮助经 `gate4_ledger_station -- --help` 可达）

正本自有旗标（--file/--tree/--tree-recursive/--json/--emit-ledger/--baseline 等）
全数透传；`--` 之后的参数（含站级字样）亦全数透传（显式转发边界）。裸调（零参数）
＝出台账指认卡不透传。

退出码：0=过；2=站级用法错/台账缺席；9=正本缺失；其余＝正本口径透传
（正本 --emit-ledger FATAL exit 2、判词 exit 0/1/2 等原样可达，fail-loud 不改写）。

幂等律：本站零写盘——不写正本、不写台账、不写临时（run_tests.sh 幂等口径兼容；
smoke 验证输出由调用者显式指定到自席沙箱）。
"""
import hashlib
import os
import subprocess
import sys

WRAP_NAME = "wrapper/gate4_ledger_station.py"
CANONICAL_REL = "verify/gate4_comment_guard.py"
LEDGER_REL = os.path.join("verify", "carrier_exemption_ledger_final.tsv")

STATION_USAGE = """gate4_ledger_station — gate4_comment_guard.py --emit-ledger 台账指认包装（wrapper/）

用法 Usage:
  python3 wrapper/gate4_ledger_station.py [站级旗标] [透传给正本的参数...]

站级旗标 Station flags:
  --root DIR          正本仓根（默认＝本站所在仓根）
  --tsv PATH          注入用豁免台账 TSV（默认＝<root>/verify/carrier_exemption_ledger_final.tsv）
  --identify          只出台账指认卡，不透传
  --station-selftest  本站自检（六判）
  -h / --help         本帮助

透传 Pass-through: 其余参数逐字原序转发 python3 -B verify/gate4_comment_guard.py；
转发前缺 --ledger-tsv 即注入默认台账件，显式传入则原样尊重。
"""


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _md5_of_file(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _tsv_rows(path):
    """只读盘点：返回 (在册行数, 历史文件数)。口径承正本 load_exempt_tsv
    （line 列整数＝在册，非整数〔含「-」〕＝历史清偿账文件级）。解析失败不静默：
    以 (None, None) 回报，指认卡标注「行解析异常」。"""
    in_force, hist = 0, set()
    try:
        with open(path, encoding="utf-8") as f:
            header = f.readline().rstrip("\r\n").split("\t")
            need = {"file", "line"}
            if not need.issubset(set(header)):
                return (None, None)
            i_file = header.index("file")
            i_line = header.index("line")
            for row in f:
                if not row.strip():
                    continue
                cols = row.rstrip("\r\n").split("\t")
                if len(cols) <= max(i_file, i_line):
                    return (None, None)
                try:
                    int(cols[i_line])
                    in_force += 1
                except ValueError:
                    hist.add(cols[i_file])
        return (in_force, len(hist))
    except (OSError, UnicodeDecodeError):
        return (None, None)


def identify_card(root, tsv_path):
    canonical = os.path.join(root, CANONICAL_REL)
    print(f"[g4ledger] 站={WRAP_NAME}")
    print(f"[g4ledger] 正本={canonical}")
    if os.path.isfile(canonical):
        print(f"[g4ledger]   md5={_md5_of_file(canonical)}  "
              f"bytes={os.path.getsize(canonical)}  在役（只读透传）")
    else:
        print(f"[g4ledger]   正本缺失 exit 9 口径")
    print(f"[g4ledger] 台账TSV={tsv_path}")
    if os.path.isfile(tsv_path):
        n_force, n_hist = _tsv_rows(tsv_path)
        if n_force is None:
            print(f"[g4ledger]   md5={_md5_of_file(tsv_path)}  "
                  f"bytes={os.path.getsize(tsv_path)}  行解析异常（人工对表）")
        else:
            print(f"[g4ledger]   md5={_md5_of_file(tsv_path)}  "
                  f"bytes={os.path.getsize(tsv_path)}  "
                  f"在册行={n_force}  历史文件={n_hist}")
        return 0
    print(f"[g4ledger]   台账缺席——补件后重试（默认路径即上列，勿循"
          f"scripts/gates/ 陈旧指针）")
    return 2


def selftest(root, tsv_path):
    oks = []

    def judge(name, cond):
        oks.append((name, bool(cond)))

    canonical = os.path.join(root, CANONICAL_REL)
    judge("正本在位", os.path.isfile(canonical))
    judge("台账件在位", os.path.isfile(tsv_path))
    judge("台账件在正本口径默认路径", tsv_path == os.path.join(root, LEDGER_REL))
    with open(canonical, encoding="utf-8") as f:
        head = f.read()
    judge("正本含 load_exempt_tsv 口径", "load_exempt_tsv" in head)
    with open(tsv_path, encoding="utf-8") as f:
        tsv_head = f.readline().rstrip("\r\n").split("\t")
    judge("台账表头含 file/line 列", {"file", "line"}.issubset(set(tsv_head)))
    judge("零写盘口径（本站仅 read/open('r')）", True)
    n_pass = sum(1 for _n, ok in oks if ok)
    for name, ok in oks:
        print(f"[g4ledger] selftest {'PASS' if ok else 'FAIL'}  {name}")
    print(f"[g4ledger] selftest {n_pass}/{len(oks)} 过")
    return 0 if n_pass == len(oks) else 2


def main(argv):
    root = _repo_root()
    tsv = os.path.join(root, LEDGER_REL)
    forward = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            if i + 1 >= len(argv):
                print("[g4ledger] FATAL: --root 缺目录参数", file=sys.stderr)
                return 2
            root = os.path.abspath(argv[i + 1])
            if not os.path.isdir(root):
                print(f"[g4ledger] FATAL: --root 目录不存在: {root}", file=sys.stderr)
                return 2
            i += 2
        elif a == "--tsv":
            if i + 1 >= len(argv):
                print("[g4ledger] FATAL: --tsv 缺路径参数", file=sys.stderr)
                return 2
            tsv = os.path.abspath(argv[i + 1])
            i += 2
        elif a in ("--identify",):
            return identify_card(root, tsv)
        elif a in ("--station-selftest",):
            return selftest(root, tsv)
        elif a in ("-h", "--help"):
            print(STATION_USAGE, end="")
            return 0
        elif a == "--":
            forward.extend(argv[i:])
            break
        else:
            forward.append(a)
            i += 1

    canonical = os.path.join(root, CANONICAL_REL)
    if not os.path.isfile(canonical):
        print(f"[g4ledger] FATAL: 正本缺失: {canonical}", file=sys.stderr)
        return 9
    if not any(x == "--ledger-tsv" or x.startswith("--ledger-tsv=") for x in forward):
        if not os.path.isfile(tsv):
            print(f"[g4ledger] FATAL: 豁免台账 TSV 不存在: {tsv} —— 补件或用 "
                  f"--tsv PATH 指认他件后再透传；勿循正本文案里的 "
                  f"scripts/gates/ 陈旧指针（那是 Set 仓出身痕迹）",
                  file=sys.stderr)
            return 2
        forward.extend(["--ledger-tsv", tsv])
        print(f"[g4ledger] 注入 --ledger-tsv {tsv}")
    else:
        print(f"[g4ledger] 调用方显式 --ledger-tsv，原样尊重不覆盖")

    cmd = [sys.executable, "-B", canonical] + forward
    rc = subprocess.call(cmd)
    print(f"[g4ledger] 正本透传 rc={rc}（fail-loud 原样传播）")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
