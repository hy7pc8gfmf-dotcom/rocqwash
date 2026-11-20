#!/bin/bash
# wrapper/gate7_probe.sh — canonical gate7 extraction-run probe launcher
# Purpose.  Canonicalizes the hand-built per-effort launch steps for the
#   gate7 extraction-run gate into one in-repo entry face: toolchain
#   environment, guard wiring, coqc-shim wiring and order assembly.
#   Criterion-free by design: pass/fail verdicts, magic numbers and
#   erase-candidate rules stay owned solely by the upstream gate7 script.
# Interface.  Usage: bash wrapper/gate7_probe.sh --tree <world dir with
#   built .v+.vo> (--order <file> | --module <name>...) [--workdir <dir>]
#   [--timeout <sec>] [--json <out>] [--coqc <shim>]
#   [--gate-script <gate7.py>] [--dry-run]
#   [-- <gate7 native args passed through verbatim>]
#   Env knobs: GATE7_PROBE_SCRIPT/-ROCQ/-ENV/-REG/-FRONT/-MID/-MAXWAIT
#   (upstream gate7 path; rocq pass-through; toolchain env source: missing
#   = loud warning then continue; guard registry dir; guard tiers 0/1/600).
# Dependencies.  bash; python3 on PATH; wrapper/coqc_shim.sh; wrapper/guard.sh;
#   the upstream gate7 script; Live/toolchain/env.sh (optional); no nested guard.
# Contract.  Guard wraps only the python3 process; python runs as `python3 -B`
#   (no __pycache__ into the read-only upstream repository); writes stay in
#   the workdir plus user-given --json/--baseline-out paths; reruns are
#   idempotent (gate7 clears stale .ml/.mli and regenerates).
# Evidence.  tests/test_gate7_wrapper.py runs 13 subprocess judges over this
#   face (syntax, help, usage errors, missing inputs, shim argv contract,
#   zero-write --dry-run canonical form); --dry-run prints the assembled
#   guard and gate7 command lines and exits 0.
# Exit-codes.  0 = gate7 passing/report-only (or --dry-run output written);
#   2 = usage error (unknown argument, --tree missing, --order/--module
#   one missing or both given); 9 = missing file (gate7 script, --tree,
#   --order/--module .v, python3, shim); otherwise the guard pass-through
#   = the gate7 exit code (0 pass; 1 gate regression; 2 usage/IO error).
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

# --- usage/file-face fail-loud checks (before any guard/compile behavior) ---
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

# --- environment canonicalization (item-by-item from the stored precedent launch scripts) ---
if [ -f "$ENVSH" ]; then
  # shellcheck disable=SC1090
  . "$ENVSH"
else
  echo "wrapper/gate7_probe.sh: 环境源缺失(警告后继续·shim 走绝对路径): $ENVSH" >&2
fi
unset COQLIB ROCQLIB
ulimit -s 65532 2>/dev/null || true

# -- workdir assembly --------------------------------------------------------
[ -n "$WORKDIR" ] || WORKDIR="$PWD/gate7_probe_work"
mkdir -p "$WORKDIR" || fail9 "workdir 不可建: $WORKDIR"
if [ -z "$ORDER" ]; then
  ORDER="$WORKDIR/order_gate7_probe.txt"
  : > "$ORDER"
  for m in "${MODULES[@]}"; do printf '%s\n' "$m" >> "$ORDER"; done
fi

# -- gate7 argument assembly (zero criterion copying; arguments 1:1 with the upstream argparse) ---
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

# -- guard wraps only the python process (exit code passes through exec unchanged) ---
exec bash "$GUARD" -Reg "$REG" -Front "$FRONT" -Mid "$MID" -MaxWaitSec "$MAXWAIT" -- "${CMD[@]}"
