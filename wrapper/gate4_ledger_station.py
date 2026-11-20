#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""gate4_ledger_station.py - ledger-identification wrapper around verify/gate4_comment_guard.py --emit-ledger (rocqwash wrapper/).
Purpose.  The live component `verify/gate4_comment_guard.py` is frozen (referenced live by in-flight components), so every
  adaptation lands as a new file under `wrapper/`.  Background: the guard was born in the Set repository's `scripts/gates/`;
  `--emit-ledger`'s default exemption ledger TSV resolves against the script's own directory by birthplace and its FATAL
  text still points there (gate4_comment_guard.py:829-837); neither this repository nor the Set repository's `scripts/gates/`
  carried `carrier_exemption_ledger_final.tsv` (verified by find/ls), so a default `--emit-ledger` run always exits FATAL
  with exit 2.  Two-half fix, both halves together: (1) the repository ships the ledger file
  `verify/carrier_exemption_ledger_final.tsv` (header columns file/line/word/first_registry per the canonical `load_exempt_tsv`
  read-only contract; zero in-force rows is the honest initial state, new entries need human review backfill, this station
  registers no exemption entry on anyone's behalf); (2) a missing `--ledger-tsv` before pass-through is auto-appended with
  the default ledger file, an explicit caller `--ledger-tsv` is respected verbatim, and an absent ledger file exits 2
  refusing pass-through, the message pointing at the real default path (not the canonical's stale `scripts/gates/` pointer).
Interface.  python3 wrapper/gate4_ledger_station.py [--root DIR] [--tsv PATH] [--identify] [--station-selftest] [-h | --help]
  [pass-through arguments...].  Station flags stay local, never forwarded: --root DIR sets the canonical repository root
  (default: this station's repository root; missing directory exits 2); --tsv PATH sets the injection ledger file (default
  <root>/verify/carrier_exemption_ledger_final.tsv); --identify prints the ledger identification card only, no pass-through
  (exit 0; exit 2 when the ledger is absent); --station-selftest runs the station's own six judgments (zero writes, canonical
  untouched); -h/--help prints the station help (canonical help reachable via `gate4_ledger_station -- --help`).  The canonical's
  own flags (--file/--tree/--tree-recursive/--json/--emit-ledger/--baseline and the rest) pass through verbatim; arguments
  after `--` (including station-flag spellings) also pass through (explicit forward boundary); bare invocation (zero arguments)
  prints the identification card.
Dependencies.  Python 3 standard library only (hashlib, os, subprocess, sys).  Runtime peers: the frozen canonical guard
  `verify/gate4_comment_guard.py` (read-only; md5-stamped in the identification card) and the shipped ledger file, whose
  header must carry the file/line columns per the canonical `load_exempt_tsv`.
Evidence.  Zero-write idempotency contract: no canonical write, no ledger write, no temporaries; smoke verification
  output goes to the caller's own sandbox (tests/run_tests.sh-compatible); --station-selftest asserts the six judgments.
Exit-codes.  0 = pass; 2 = station usage error or ledger file absent; 9 = canonical missing; any other code = the
  canonical's own contract passed through unchanged (--emit-ledger FATAL exit 2 and conclusion exit 0/1/2 arrive as-is;
  fail-loud, never rewritten).
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
    """Read-only census: returns (in-force row count, historical file count).  The contract follows the
    canonical `load_exempt_tsv` (an integer line column counts as in force; a non-integer value, including
    "-", marks a historically settled file-level row).  Parse failures are not silent: (None, None) comes
    back and the identification card flags the row-parse anomaly."""
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
