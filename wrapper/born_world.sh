#!/bin/bash
# wrapper/born_world.sh — canonical born-world builder: fresh-copy certified sources into a world directory and compile each module through the guard wrapper.
#
# Purpose.  Build a born world in the canonical three-step form: (1) every .v source is copied fresh
#   from the certified runtree source tree into the world directory (in-world stale sources are never
#   reused; the copy is byte-asserted with cmp); (2) the working directory is bound to the world
#   directory (cd); (3) the compile carries the single binding `-Q . ""` after the cd — the
#   cwd-isolation form — so dependencies resolve only from the world cwd and out-of-tree .vo files
#   cannot shadow the build. Reusing a previous generation's .v/.vo products inside a world directory
#   produces spurious passes and stale loads; the three mechanical defenses are listed in Contract 2.
#   Every compile launch goes through the thermal-guard wrapper (`tools/cpu_guard.sh` wired through `wrapper/guard.sh`).
#
# Interface.  bash wrapper/born_world.sh --runtree <certified source dir (.v)> --world <target world dir>
#      (--module <name[.v]> [--module ...] | --order <list file, one name per line, # comments ignored>)
#      [--assert-md5 <manifest>] [--rc-out <born rc ledger>]
#      [--env <env.sh>] [--reg <dir>] [--dry-run] [-h|--help]
#   Example:
#     bash wrapper/born_world.sh --runtree "$RUNTREE" --world "$SB/world" \
#          --module A --module B --assert-md5 "$RUNTREE/md5_manifest.txt" \
#          --rc-out "$SB/logs/born_world.rc"
#
# Environment knobs:
#   BORN_WORLD_RUNTREE  default certified runtree source tree (default /Users/apple/Desktop/
#                       ConstructiveWorld/ConstructiveWorld_Live); an explicit --runtree value takes
#                       precedence.
#   BORN_WORLD_ROCQ     absolute rocq path (default Live toolchain path; the same knob value as
#                       `wrapper/coqc_shim.sh`); missing = fail-loud exit 9.
#   BORN_WORLD_ENV      toolchain environment source (default Live/toolchain/env.sh; missing = loud
#                       warning, then continue — rocq runs by absolute path, never silently).
#   BORN_WORLD_REG      guard registry directory (default /tmp/cw_reg_born_world; a caller may point
#                       it at its own directory, so parallel lanes never queue on each other).
#   BORN_WORLD_FRONT/-MID/-MAXWAIT  guard knob levels (default 0/1/600 = the canonical form).
#
# Dependencies.  bash 3.2-compatible; md5, cmp, cp, sed, grep from the base system; the rocq binary
#   from the Live toolchain (absolute path); `wrapper/guard.sh` present in the repository (fail-loud
#   exit 9 when the guard layer is missing); zero network — cp/cmp/md5/rocq c are all local.
#
# Evidence.  tests/test_gate6_born_wrapper.py judges 10-21 exercise this script by subprocess:
#   bash -n, -h, --bogus, missing inputs, order/module mutual exclusion, md5-manifest mismatch
#   and .vo-only refusal, and the zero-write --dry-run canonical forms; judges 17, 18 and 20
#   additionally assert no stray products or stage changes behind the dry-run and rc 9 paths.
#   The dry-run output carries the exact guard knobs and the `-Q . ""` binding form.
#
# Contract:
#   1. Guard wiring is built in (one launch per module): `wrapper/guard.sh -Reg … -Front 0 -Mid 1
#      -MaxWaitSec 600 -- rocq c -native-compiler no -q -Q . "" <name>.v` (rocq runs via the
#      BORN_WORLD_ROCQ absolute path). Callers must not add another outer guard layer — two layers sharing one registry deadlock.
#   2. Three stale-generation defenses: (1) always copy fresh — in-world stale .v is never reused,
#      copy then byte-compare (cmp); (2) --assert-md5 asserts every source .v against the manifest
#      (accepted line forms: "<md5>  <name>.v..." and "MD5 (<name>.v) = <md5>"; located by name,
#      the line's 32-hex token is taken; only .v source lines count — a missing .v assertion line
#      or any mismatch = exit 9); (3) the module's stale products inside the world
#      (.vo/.vos/.vok/.glob/.aux) are removed before compiling.
#   3. Chain-stop rule: modules are born in the given order; the first failing module stops the
#      chain and its rocq exit code becomes the script's exit code; the failing module's rc is
#      still recorded (--rc-out appends one "<name>.v RC=<n>" line per module).
#   4. Environment canonicalization: source env.sh (when present) → unset COQLIB ROCQLIB → ulimit -s 65532.
#   5. Write-surface ROOT declaration (CONTRIBUTING §3.5): writes only inside the --world directory (the
#      copied .v files, the rocq products, the default rc ledger $WORLD/born_world.rc) plus the user's
#      explicit --rc-out path; no canonical repository or caller-domain path is written; --runtree is read-only.
#   6. Zero network: cp/cmp/md5/rocq c are all local operations.
# Exit-codes.  0 = the whole order born passing (every module rc=0); 2 = usage error at this layer; 9 = missing file or failed source assertion; any other code = the first failing module's rocq exit code (chain-stop pass-through).
#   0   = the whole order born passing (every module rc=0)
#   2   = usage error at this layer (unknown flag; missing --runtree/--world/order; neither one of
#         --module/--order given, or both given; module name with a path separator)
#   9   = missing file or failed source assertion (runtree/world unavailable; a module source missing;
#         md5 assertion mismatch; rocq missing — fail-loud, no behavior simulated)
#   any other code = the first failing module's rocq exit code (chain-stop pass-through)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/wrapper/guard.sh"

RUNTREE_DEF="${BORN_WORLD_RUNTREE:-/Users/apple/Desktop/ConstructiveWorld/ConstructiveWorld_Live}"
ROQC="${BORN_WORLD_ROCQ:-/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq}"
ENVSH="${BORN_WORLD_ENV:-/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/env.sh}"
REG="${BORN_WORLD_REG:-/tmp/cw_reg_born_world}"
FRONT="${BORN_WORLD_FRONT:-0}"
MID="${BORN_WORLD_MID:-1}"
MAXWAIT="${BORN_WORLD_MAXWAIT:-600}"

usage() {
  sed -n '2,62p' "$0" | grep -E '^#' | sed 's/^# \{0,1\}//'
}

RUNTREE=""; WORLD=""; ORDERFILE=""; MD5MAN=""; RCOUT=""; DRYRUN=0
MODULES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --runtree) RUNTREE="${2-}"; shift 2 ;;
    --world) WORLD="${2-}"; shift 2 ;;
    --module) MODULES+=("${2-}"); shift 2 ;;
    --order) ORDERFILE="${2-}"; shift 2 ;;
    --assert-md5) MD5MAN="${2-}"; shift 2 ;;
    --rc-out) RCOUT="${2-}"; shift 2 ;;
    --env) ENVSH="${2-}"; shift 2 ;;
    --reg) REG="${2-}"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "wrapper/born_world.sh: 未知形参 unknown arg: $1" >&2
       echo "  (-h|--help 看用法)" >&2; exit 2 ;;
  esac
done

fail2() { echo "wrapper/born_world.sh: $1" >&2; exit 2; }
fail9() { echo "wrapper/born_world.sh: $1" >&2; echo "  (fail-loud exit 9：文件缺失/代际断言败不模拟任何行为)" >&2; exit 9; }

# --- usage checks, fail-loud -------------------------------------------------
[ -n "$RUNTREE" ] || RUNTREE="$RUNTREE_DEF"
[ -n "$WORLD" ] || fail2 "缺 --world <目标世界目录>"
[ ${#MODULES[@]} -gt 0 ] || [ -n "$ORDERFILE" ] || fail2 "--order 与 --module 必给其一"
[ ${#MODULES[@]} -eq 0 ] || [ -z "$ORDERFILE" ] || fail2 "--order 与 --module 不得同给（二义）"
[ -d "$RUNTREE" ] || fail9 "--runtree 认证代源树缺失: $RUNTREE (可用 BORN_WORLD_RUNTREE/--runtree 覆写)"
[ -f "$ROQC" ] && [ -x "$ROQC" ] || fail9 "rocq 缺失/不可执行: $ROQC (可用 BORN_WORLD_ROCQ 覆写)"
[ -f "$GUARD" ] || fail9 "guard 直通层缺失: $GUARD"
[ -z "$MD5MAN" ] || [ -f "$MD5MAN" ] || fail9 "--assert-md5 manifest 缺失: $MD5MAN"

if [ -n "$ORDERFILE" ]; then
  [ -f "$ORDERFILE" ] || fail9 "--order 文件缺失: $ORDERFILE"
  # one name per line; # comments and blank lines are ignored (the on-disk order-file form)
  while IFS= read -r line || [ -n "$line" ]; do
    m="$(printf '%s' "$line" | sed 's/#.*//' | tr -d '[:space:]')"
    [ -n "$m" ] && MODULES+=("$m")
  done < "$ORDERFILE"
  [ ${#MODULES[@]} -gt 0 ] || fail2 "--order 文件无有效模块名: $ORDERFILE"
fi

# module-name normalization: strip the .v suffix; path separators rejected (world is a flat tree, same rule as gate6/gate7)
NORM=()
for m in "${MODULES[@]}"; do
  m="${m%.v}"
  case "$m" in
    */*|*.*) fail2 "模块名含路径/扩展形参不合法: ${m}（world 平树·只收裸名）" ;;
  esac
  NORM+=("$m")
done
MODULES=("${NORM[@]}")

# --- source md5 assertion (stale-generation defense 2; runs before anything is written) ------
assert_md5() { # $1 = module name; asserts the source file md5 against the manifest
  local m="$1" src="$RUNTREE/$m.v" want got line
  want="$(md5 -q "$src")" || fail9 "md5 计算失败: $src"
  # accepted line forms: "<md5>  <name>.v..." (the source manifest's on-disk form) and
  # "MD5 (<name>.v) = <md5>" (md5's default form) — the line is located by module name and its
  # 32-hex token taken; only .v source lines count — a .vo line never matches, so fail loud (defense 2).
  line="$(grep -nE "(^|[^A-Za-z0-9_])${m}\.v([^A-Za-z0-9_]|$)" "$MD5MAN" 2>/dev/null | head -1 || true)"
  [ -n "$line" ] || fail9 "代际断言败：manifest 无 ${m}.v 源断言行: $MD5MAN"
  got="$(printf '%s' "$line" | grep -oE '[0-9a-fA-F]{32}' | head -1)"
  [ -n "$got" ] || fail9 "代际断言败：manifest 行无 32-hex md5: $line"
  if [ "$(printf '%s' "$got" | tr 'A-F' 'a-f')" != "$want" ]; then
    fail9 "代际断言败（nw5 雷现形）：${m}.v 源 md5=$want manifest=$got (manifest: $MD5MAN)"
  fi
  echo "MD5-ASSERT ${m}.v OK ($want)"
}

# --- dry-run report (zero writes) --------------------------------------------
if [ "$DRYRUN" = "1" ]; then
  echo "BORN-WORLD-DRYRUN runtree: $RUNTREE"
  echo "BORN-WORLD-DRYRUN world:   $WORLD"
  [ -z "$MD5MAN" ] || echo "BORN-WORLD-DRYRUN assert-md5: $MD5MAN"
  for m in "${MODULES[@]}"; do
    echo "BORN-WORLD-DRYRUN cp: $RUNTREE/$m.v -> $WORLD/$m.v (cp+cmp 字节断言$( [ -n "$MD5MAN" ] && echo '＋manifest md5 断言'))"
  done
  echo "BORN-WORLD-DRYRUN env: source ${ENVSH:-<无>} ; unset COQLIB ROCQLIB ; ulimit -s 65532 ; cd $WORLD"
  for m in "${MODULES[@]}"; do
    printf 'BORN-WORLD-DRYRUN born: bash %q -Reg %q -Front %q -Mid %q -MaxWaitSec %q --\n' \
      "$GUARD" "$REG" "$FRONT" "$MID" "$MAXWAIT"
    printf 'BORN-WORLD-DRYRUN   %q c -native-compiler no -q -Q . "" %q\n' "$ROQC" "$m.v"
  done
  exit 0
fi

# --- step 1: certified-source copy (always fresh + cmp byte assertion; defenses 1 and 3) -----
mkdir -p "$WORLD" || fail9 "--world 不可建: $WORLD"
for m in "${MODULES[@]}"; do
  src="$RUNTREE/$m.v"
  [ -f "$src" ] || fail9 "认证代源缺失: $src (runtree=$RUNTREE)"
  [ -n "$MD5MAN" ] && assert_md5 "$m"
  cp -f "$src" "$WORLD/$m.v" || fail9 "cp 失败: $src -> $WORLD/$m.v"
  cmp -s "$src" "$WORLD/$m.v" || fail9 "cp 后 cmp 不等（nw5 雷防线①现形）: $WORLD/$m.v"
  # clear the module's stale products inside the world (defense 3)
  rm -f "$WORLD/$m.vo" "$WORLD/$m.glob" "$WORLD/$m.vos" "$WORLD/$m.vok" "$WORLD/.$m.aux"
  echo "CP-OK $RUNTREE/$m.v -> $WORLD/$m.v"
done

# --- step 2: environment canonicalization ------------------------------------
if [ -f "$ENVSH" ]; then
  # shellcheck disable=SC1090
  . "$ENVSH"
else
  echo "wrapper/born_world.sh: 环境源缺失(警告后继续·rocq 走绝对路径): $ENVSH" >&2
fi
unset COQLIB ROCQLIB
ulimit -s 65532 2>/dev/null || true

# --- steps 2-3: cd into the world + born each module (chain-stop rule; rc ledger) -------------
cd "$WORLD" || fail9 "cd world 失败: $WORLD"

[ -n "$RCOUT" ] || RCOUT="$WORLD/born_world.rc"
mkdir -p "$(dirname "$RCOUT")" 2>/dev/null || true
: > "$RCOUT" || fail9 "rc 台账不可写: $RCOUT"

for m in "${MODULES[@]}"; do
  log_rc=0
  bash "$GUARD" -Reg "$REG" -Front "$FRONT" -Mid "$MID" -MaxWaitSec "$MAXWAIT" -- \
    "$ROQC" c -native-compiler no -q -Q . "" "$m.v" || log_rc=$?
  echo "$m.v RC=$log_rc" >> "$RCOUT"
  echo "BORN $m.v rc=$log_rc"
  if [ "$log_rc" -ne 0 ]; then
    echo "wrapper/born_world.sh: 链停 CHAIN-STOP at ${m}.v (rc=${log_rc}·台账 ${RCOUT})" >&2
    exit "$log_rc"
  fi
done

echo "BORN-WORLD-ALL-DONE modules=${#MODULES[@]} world=$WORLD"
exit 0
