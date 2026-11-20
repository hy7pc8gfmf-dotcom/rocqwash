#!/bin/bash
# wrapper/born_world.sh — born 世界基正典形固化层（canonical born-world builder）
# 2026-10-31 席 rqadapt · 适配任务：组件 编译世界基（各席 born 链手造形正典化）
#
# gap（本轮补齐对象）：编译为固有 cwd 绑定形——各席 cd $SEAT/world ＋
#   rocq c -Q <world> ""（gcl 草案明文「-Q <world> ""（cwd 隔离）」；判例
#   seat_nw7/tools/_nw7_born.sh:10 cd、:13-15 `-Q . ""`；E552 装载遮蔽判例定式
#   「cd 后单一 `-Q . ""` 绑定编译·遮蔽源彻底出局」）。但该正形全靠各席手造脚本
#   逐份重写，且 nw5 代际雷（born 世界≠认证代 cp·自带旧代 .v/.vo ⇒ 假绿/装载体
#   遮蔽）无机械防线。本件把三段正形固化为仓内唯一 born 入口：
#
#     ① RUNTREE 认证代 cp   一切 .v 一律从认证代源树**现拷**入 world（禁自带旧代
#                             ——nw5 判例·world_md5_assert 账）；可选 --assert-md5
#                             对源做 manifest md5 断言（代际漂移现形 fail-loud）；
#                             cp 后逐件 cmp 字节断言。
#     ② cd world            固有 cwd 绑定形（_nw7_born.sh:10 判例）。
#     ③ -Q <world> ""       cd 后单一 `-Q . ""`（≡gcl 草案 `-Q <world> ""` cwd
#                             隔离·同物理目录同绑定）；依赖只从本 world cwd 解析，
#                             外树 .vo 零遮蔽（E552 判例）。
#   每发编译整经温控（tools/cpu_guard.sh 冻结正本·wrapper/guard.sh 直通层接线）。
#
# 用法 Usage:
#   bash wrapper/born_world.sh --runtree <认证代源目录(.v)> --world <目标世界目录>
#        (--module <名[.v]> [--module …] | --order <清单文件·逐行一名 #注释忽略>)
#        [--assert-md5 <manifest>] [--rc-out <born rc 台账>]
#        [--env <env.sh>] [--reg <dir>] [--dry-run] [-h|--help]
#   例 Example:
#     bash wrapper/born_world.sh --runtree "$RUNTREE" --world "$SB/world" \
#          --module A --module B --assert-md5 "$RUNTREE/md5_manifest.txt" \
#          --rc-out "$SB/logs/born_world.rc"
#
# 环境旋钮 Env knobs:
#   BORN_WORLD_RUNTREE  缺省认证代源树（缺省 /Users/apple/Desktop/ConstructiveWorld/
#                       ConstructiveWorld_Live——本战役判例源：rqadapt world_copy_smoke
#                       两件与其逐字节 SAME 实测 20261031）；--runtree 显式给值优先。
#   BORN_WORLD_ROCQ     rocq 绝对路径（缺省 Live toolchain 正典路径·与 wrapper/
#                       coqc_shim.sh 同旋钮值）；缺失 fail-loud exit 9。
#   BORN_WORLD_ENV      toolchain 环境源（缺省 Live/toolchain/env.sh；缺失＝响亮
#                       警告后继续——rocq 用绝对路径不依赖 PATH·不静默）。
#   BORN_WORLD_REG      guard 登记表目录（缺省 /tmp/cw_reg_born_world；席位惯例
#                       自设如 /tmp/cw_reg_<seat>，双车道互不排队）。
#   BORN_WORLD_FRONT/-MID/-MAXWAIT  guard 档位（缺省 0/1/600＝战役正典形）。
#
# 契约 Contract:
#   1. guard 接线内建（每模块一发）：`wrapper/guard.sh -Reg … -Front 0 -Mid 1
#      -MaxWaitSec 600 -- rocq c -native-compiler no -q -Q . "" <名>.v`
#      （nw7:13-15 判例逐字·rocq 走 BORN_WORLD_ROCQ 绝对路径）。**调用者禁再外套
#      guard**（同注册表死锁判例·nw8 20261031）。
#   2. nw5 代际雷三防线：①一律现拷（world 旧 .v 不复用·先 cp 后 cmp 字节断言）；
#      ②--assert-md5 manifest 逐件对**源 .v**断言（行格式兼容「<md5>␠␠<名>.v…」
#        与「MD5 (<名>.v) = <md5>」；.vo 世界账≠源账·无 .v 断言行/不等＝exit 9）；
#      ③编译前清该模块 world 内陈旧产物（.vo/.vos/.vok/.glob/.aux——nw7:12 判例）。
#   3. 链停律（gclcure born_chain 判例）：按给定序逐件 born，遇红即停，退出码＝
#      该件 rocq 退出码；红件 rc 台账照记（--rc-out 每行「<名>.v RC=<n>」）。
#   4. 环境正典化（nw7 判例逐项）：source env.sh（如有）→ unset COQLIB ROCQLIB →
#      ulimit -s 65532。
#   5. 写盘面 ROOT 声明（CONTRIBUTING §3.5）：仅 --world 目录内（cp 入的 .v＋
#      rocq 产物＋缺省 rc 台账 $WORLD/born_world.rc）＋用户显式 --rc-out 路径；
#      **不写两仓正本与各 seat 域任何路径**；--runtree 源树只读不写。
#   6. 零网络：cp/cmp/md5/rocq c 全本地。
#
# 退出码 Exit codes:
#   0   = 全序 born 绿（各件 rc=0）
#   2   = 本层用法错（未知形参/缺 --runtree/--world/order·module 缺一/二者同给/
#         模块名带路径分隔符）
#   9   = 文件缺失或代际断言败（runtree/world 不可用/某模块源缺失/md5 断言不等/
#         rocq 缺失——fail-loud 不模拟任何行为）
#   其余 = 首红件 rocq 退出码（链停透传）
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

# --- 用法面 fail-loud --------------------------------------------------------
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
  # 逐行一名·#注释与空行忽略（seat order 文件实盘形）
  while IFS= read -r line || [ -n "$line" ]; do
    m="$(printf '%s' "$line" | sed 's/#.*//' | tr -d '[:space:]')"
    [ -n "$m" ] && MODULES+=("$m")
  done < "$ORDERFILE"
  [ ${#MODULES[@]} -gt 0 ] || fail2 "--order 文件无有效模块名: $ORDERFILE"
fi

# 模块名归一：剥 .v 后缀；禁路径分隔符（world 为平树·gate6/gate7 同口径）
NORM=()
for m in "${MODULES[@]}"; do
  m="${m%.v}"
  case "$m" in
    */*|*.*) fail2 "模块名含路径/扩展形参不合法: ${m}（world 平树·只收裸名）" ;;
  esac
  NORM+=("$m")
done
MODULES=("${NORM[@]}")

# --- 代际断言（nw5 雷防线②·先于任何落盘） ------------------------------------
assert_md5() { # $1=模块名 → 源文件 md5 对 manifest 断言
  local m="$1" src="$RUNTREE/$m.v" want got line
  want="$(md5 -q "$src")" || fail9 "md5 计算失败: $src"
  # 行格式兼容：「<md5>  <名>.v…」（源 manifest 实盘形）与
  # 「MD5 (<名>.v) = <md5>」（md5 默认形）——按名定行·取行内 32-hex 令牌。
  # 只认 .v 源行：.vo 世界账 md5 与源恒不等·宁 fail-loud 不哑比（nw5 雷防线②）。
  line="$(grep -nE "(^|[^A-Za-z0-9_])${m}\.v([^A-Za-z0-9_]|$)" "$MD5MAN" 2>/dev/null | head -1 || true)"
  [ -n "$line" ] || fail9 "代际断言败：manifest 无 ${m}.v 源断言行: $MD5MAN"
  got="$(printf '%s' "$line" | grep -oE '[0-9a-fA-F]{32}' | head -1)"
  [ -n "$got" ] || fail9 "代际断言败：manifest 行无 32-hex md5: $line"
  if [ "$(printf '%s' "$got" | tr 'A-F' 'a-f')" != "$want" ]; then
    fail9 "代际断言败（nw5 雷现形）：${m}.v 源 md5=$want manifest=$got (manifest: $MD5MAN)"
  fi
  echo "MD5-ASSERT ${m}.v OK ($want)"
}

# --- dry-run 出账（零落盘） ---------------------------------------------------
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

# --- ① 认证代 cp（一律现拷＋cmp 字节断言·雷防线①③） --------------------------
mkdir -p "$WORLD" || fail9 "--world 不可建: $WORLD"
for m in "${MODULES[@]}"; do
  src="$RUNTREE/$m.v"
  [ -f "$src" ] || fail9 "认证代源缺失: $src (runtree=$RUNTREE)"
  [ -n "$MD5MAN" ] && assert_md5 "$m"
  cp -f "$src" "$WORLD/$m.v" || fail9 "cp 失败: $src -> $WORLD/$m.v"
  cmp -s "$src" "$WORLD/$m.v" || fail9 "cp 后 cmp 不等（nw5 雷防线①现形）: $WORLD/$m.v"
  # 清该模块 world 内陈旧产物（雷防线③·nw7:12 判例）
  rm -f "$WORLD/$m.vo" "$WORLD/$m.glob" "$WORLD/$m.vos" "$WORLD/$m.vok" "$WORLD/.$m.aux"
  echo "CP-OK $RUNTREE/$m.v -> $WORLD/$m.v"
done

# --- ② 环境正典化（nw7 判例） -------------------------------------------------
if [ -f "$ENVSH" ]; then
  # shellcheck disable=SC1090
  . "$ENVSH"
else
  echo "wrapper/born_world.sh: 环境源缺失(警告后继续·rocq 走绝对路径): $ENVSH" >&2
fi
unset COQLIB ROCQLIB
ulimit -s 65532 2>/dev/null || true

# --- ②③ cd world ＋ 逐件 born（链停律·rc 台账） --------------------------------
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
