#!/bin/bash
# wrapper/gate7_probe.sh — gate7 提取执行闸探针正典启动层（canonical gate7 probe launcher）
# 2026-10-31 席 rqadapt · 适配任务：组件 gate7 探针链（仓外件
#   ConstructiveWorld-Set/scripts/gates/gate7_extract_run.py · 在其仓只读禁改）
#
# 定位 Positioning:
#   gate7 正本（提取执行闸·红线律 IV 4a/4b：Separate Extraction 驱动单发编译＋
#   .ml/.mli 双面 Obj.magic 账＋名presence差·--gate 对 baseline 判红绿）在本机由各
#   战役席（nw7/nw8 判例 _nw7_gate7_run.sh / _nw8_gate7_v5b.sh）各自手造启动层：
#   ①source Live toolchain env.sh ②unset COQLIB ROCQLIB ③ulimit -s 65532
#   ④guard 只包 python 进程（shim 内禁再套＝同注册表死锁判例）⑤seat 自造 coqc shim。
#   本文件将其**正典化**为仓内唯一启动面：环境 canonical 化＋guard 接线＋coqc shim
#   接线（wrapper/coqc_shim.sh）＋order 装配；**判据零复制**——红绿/魔数/擦除候选
#   一切判词仍归 gate7 正本唯一出处，本层只是其新入口（防双源漂移）。
#
# 用法 Usage:
#   bash wrapper/gate7_probe.sh --tree <world 目录(.v+.vo 已建)> 
#        (--order <order 文件> | --module <名> [--module <名>...])
#        [--workdir <目录>] [--timeout <秒>] [--json <出账>]
#        [--coqc <shim>] [--gate-script <gate7.py>] [--dry-run]
#        [-- <gate7 其余形参逐字透传，如 --gate --baseline B --baseline-out O>]
#   例 Example:
#     bash wrapper/gate7_probe.sh --tree "$SB/world" --module UpAblD1S6_UpReqRealFEP \
#          --workdir "$SB/g7_work" --json "$SB/logs/gate7_probe.json" --timeout 600
#     bash wrapper/gate7_probe.sh --tree <world> --order <order.txt> -- \
#          --gate --baseline gate7_extract_baseline.json --json out.json
#
# 环境旋钮 Env knobs（缺省＝本机 Live 判例正典值）:
#   GATE7_PROBE_SCRIPT  gate7 正本路径（缺省 ConstructiveWorld-Set 仓外正典路径）
#   GATE7_PROBE_ROCQ    rocq 绝对路径（透传给 wrapper/coqc_shim.sh 同名旋钮）
#   GATE7_PROBE_ENV     toolchain 环境源（缺省 Live/toolchain/env.sh；缺失＝响亮警告
#                       后继续——shim 用绝对路径不依赖 PATH·不静默）
#   GATE7_PROBE_REG     guard 登记表目录（缺省 /tmp/cw_reg_gate7_probe；席位惯例
#                       自设如 /tmp/cw_reg_<seat>，双车道与其它席位互不排队）
#   GATE7_PROBE_FRONT/-MID/-MAXWAIT  guard 档位（缺省 0/1/600＝战役正典形）
#
# 契约 Contract:
#   1. guard 只包 python 进程（正典形 -Front 0 -Mid 1 -MaxWaitSec 600）；gate7 调
#      shim 的编译子进程全在其进程树内＝一切编译仍整经温控；shim 内零 guard
#      （死锁判例·见 coqc_shim.sh 头注）；双车道 -Reg 分道互不阻塞。
#   2. python 一律 `python3 -B`——禁向只读正本仓（ConstructiveWorld-Set）写
#      __pycache__（gate7 import 同目录 gate6_statement_census）。
#   3. --module 形：order 文件由本层装配到 <workdir>/order_gate7_probe.txt
#      （逐行一名·gate7 正本自容 .v 后缀剥离）；--order 形：文件原样直传不改动。
#   4. 写盘面 ROOT 声明（CONTRIBUTING §3.5）：仅 <workdir>（缺省
#       $PWD/gate7_probe_work）内的 order 文件与 gate7 工件＋用户指定的 --json/
#       --baseline-out 路径；**不写两仓正本与各 seat 域任何路径**；重跑幂等
#       （gate7 正本自清 workdir 旧 .ml/.mli 后重产）。
#   5. 判据零复制：本层不产生任何红绿/魔数判词；gate7 正本 stdout/JSON 是唯一判据源。
#   6. 退出码 1:1 透传：其余情形＝guard 退出码＝gate7 自身退出码
#      （0 绿/报告-only；1 闸回归；2 gate7 用法-IO 错）。
#
# 退出码 Exit codes:
#   0   = gate7 绿/报告-only（或 --dry-run 出账后）
#   2   = 本层用法错（未知形参/缺 --tree/order·module 缺一/二者同给）
#   9   = 文件缺失（gate7 正本/--tree/--order/--module 的 .v/python3/shim——fail-loud）
#   其余 = guard 透传＝gate7 自身退出码（含 1 闸红）
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHIM="$ROOT/wrapper/coqc_shim.sh"
GUARD="$ROOT/wrapper/guard.sh"

GATE7_SCRIPT="${GATE7_PROBE_SCRIPT:-/Users/apple/Desktop/ConstructiveWorld-Set/scripts/gates/gate7_extract_run.py}"
ENVSH="${GATE7_PROBE_ENV:-/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/env.sh}"
REG="${GATE7_PROBE_REG:-/tmp/cw_reg_gate7_probe}"
FRONT="${GATE7_PROBE_FRONT:-0}"
MID="${GATE7_PROBE_MID:-1}"
MAXWAIT="${GATE7_PROBE_MAXWAIT:-600}"

usage() {
  sed -n '2,50p' "$0" | grep -E '^#' | sed 's/^# \{0,1\}//'
}

TREE=""; ORDER=""; WORKDIR=""; TIMEOUT=""; JSONOUT=""; COQC=""; DRYRUN=0
MODULES=(); EXTRA=()
AFTER="--args"
while [ $# -gt 0 ]; do
  case "$1" in
    --tree) TREE="${2-}"; shift 2 ;;
    --order) ORDER="${2-}"; shift 2 ;;
    --module) MODULES+=("${2-}"); shift 2 ;;
    --workdir) WORKDIR="${2-}"; shift 2 ;;
    --timeout) TIMEOUT="${2-}"; shift 2 ;;
    --json) JSONOUT="${2-}"; shift 2 ;;
    --coqc) COQC="${2-}"; shift 2 ;;
    --gate-script) GATE7_SCRIPT="${2-}"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) AFTER="--extra"; shift; EXTRA=("$@"); break ;;
    *) echo "wrapper/gate7_probe.sh: 未知形参 unknown arg: $1" >&2
       echo "  (-h|--help 看用法; gate7 原生形参请置于 -- 之后逐字透传)" >&2; exit 2 ;;
  esac
done

fail9() { echo "wrapper/gate7_probe.sh: $1" >&2; echo "  (fail-loud exit 9：文件缺失不模拟任何行为)" >&2; exit 9; }

# --- 用法/文件面 fail-loud（先于任何 guard/编译行为） -----------------------
[ -n "$TREE" ] || { echo "wrapper/gate7_probe.sh: 缺 --tree <world>" >&2; exit 2; }
[ ${#MODULES[@]} -gt 0 ] || [ -n "$ORDER" ] || \
  { echo "wrapper/gate7_probe.sh: --order 与 --module 必给其一" >&2; exit 2; }
[ ${#MODULES[@]} -eq 0 ] || [ -z "$ORDER" ] || \
  { echo "wrapper/gate7_probe.sh: --order 与 --module 不得同给（二义）" >&2; exit 2; }
[ -d "$TREE" ] || fail9 "--tree 世界目录缺失: $TREE"
[ -f "$GATE7_SCRIPT" ] || fail9 "gate7 正本缺失: $GATE7_SCRIPT (可用 GATE7_PROBE_SCRIPT 覆写)"
[ -x "${COQC:-$SHIM}" ] || fail9 "coqc shim 缺失/不可执行: ${COQC:-$SHIM}"
command -v python3 >/dev/null 2>&1 || fail9 "python3 不在 PATH"
if [ -n "$ORDER" ]; then
  [ -f "$ORDER" ] || fail9 "--order 文件缺失: $ORDER"
else
  for m in "${MODULES[@]}"; do
    [ -f "$TREE/$m.v" ] || [ -f "$TREE/${m%.v}.v" ] || \
      fail9 "--module 的 .v 不在世界副本中: $TREE/$m.v"
  done
fi

# --- 环境正典化（nw7/nw8 判例逐项） ----------------------------------------
if [ -f "$ENVSH" ]; then
  # shellcheck disable=SC1090
  . "$ENVSH"
else
  echo "wrapper/gate7_probe.sh: 环境源缺失(警告后继续·shim 走绝对路径): $ENVSH" >&2
fi
unset COQLIB ROCQLIB
ulimit -s 65532 2>/dev/null || true

# -- workdir 装配 ------------------------------------------------------------
[ -n "$WORKDIR" ] || WORKDIR="$PWD/gate7_probe_work"
mkdir -p "$WORKDIR" || fail9 "workdir 不可建: $WORKDIR"
if [ -z "$ORDER" ]; then
  ORDER="$WORKDIR/order_gate7_probe.txt"
  : > "$ORDER"
  for m in "${MODULES[@]}"; do printf '%s\n' "$m" >> "$ORDER"; done
fi

# -- gate7 形参装配（判据零复制·形参 1:1 对齐正本 argparse） ------------------
CMD=(python3 -B "$GATE7_SCRIPT"
     --tree "$TREE"
     --order "$ORDER"
     --workdir "$WORKDIR"
     --coqc "${COQC:-$SHIM}")
[ -n "$TIMEOUT" ] && CMD+=(--timeout "$TIMEOUT")
[ -n "$JSONOUT" ] && CMD+=(--json "$JSONOUT")
[ ${#EXTRA[@]} -gt 0 ] && CMD+=("${EXTRA[@]}")

if [ "$DRYRUN" = "1" ]; then
  printf 'GATE7-PROBE-DRYRUN guard: bash %q -Reg %q -Front %q -Mid %q -MaxWaitSec %q --\n' \
    "$GUARD" "$REG" "$FRONT" "$MID" "$MAXWAIT"
  printf 'GATE7-PROBE-DRYRUN cmd:'
  printf ' %q' "${CMD[@]}"
  printf '\n'
  exit 0
fi

# -- guard 只包 python 进程（退出码 exec 透传·无改写） -----------------------
exec bash "$GUARD" -Reg "$REG" -Front "$FRONT" -Mid "$MID" -MaxWaitSec "$MAXWAIT" -- "${CMD[@]}"
