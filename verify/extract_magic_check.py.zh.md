#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_magic_check.py — gate7 提取面 Obj.magic 逐件机检闸（rocqwash verify/·20261101）

坑账第十笔工具化（承工单）：run97/98 gate7 三件涨账 28/4/1——洗形席洗完的件在
gate7 提取执行闸才现形 Obj.magic 涨账（28/4/1 三件），涨点发现太晚。本件把该教训
压成逐件标准闸，供洗形席标准闸增配：洗形逐件交付前先过本闸，--max（默认 0）超线
即红，提取面魔数不再等 gate7 闸尾才暴露。

输入＝已编译 .vo 的源 .v 文件＋世界 -Q 路径。工序五步：
  ① 从 .v 解析 Separate Extraction 目标（注释/字符串先经 mac_stmt_names
    strip_comments_strings 状态机掩蔽·注释诱饵不入账）；无 Separate Extraction
    命令则按 census 口径（names/mac_stmt_names.extract_statements·不含 Let·
    与 tools/_gen_fin_mac.py 同核）收文件全部主定义，生成临时提取稿（driver）
    入临时目录——census 语句 token 集承冻结件 TARGET/SKIP_KINDS，本件 v15 起
    import 面就地扩补声明/命令 vernacular（DECL_SKIP_EXT·Class/Schema/Scheme/
    Structure/Canonical/Coercion/Derive/Existing/Primitive/Register/Extraction/
    Recursive/Separate/About/Close——首战 G09 Class/G13 Extraction 双红盲区
    工具化·冻结件字节零触碰·未知 vernacular 仍 fail-loud rc=9）；
  ② rocq 提取（`rocq c -native-compiler no -q -Q <world> "" <稿>.v`·cwd=工作目录
    ·世界 .vo 只读供 Require·零写世界）→ ocamlc 编提取产物（逐模 .mli 先 .ml 后
    ·跨模依赖重试轮·承 gate7 4b 面）；
  ③ grep -c Obj.magic 提取 .ml 输出计数（行计数口径：一行多魔数计一）——
    .mli 面计数同法随账（信息面，不入判）；
  ④ --max N（默认 0）：计数超线 → exit 1 fail-loud 并逐行列出魔数行上下文
    （行号±1）；
  ⑤ --json 出台账（mode/targets/rocq_rc/magic_ml/magic_lines/ocamlc/verdict/md5）。

判词三向（fail-loud 不模拟）：
  - 提取面红（rocq rc≠0／<Mod>.ml 未产出）→ FAIL rc=1（不可计数≠绿）；
  - 魔数面红（grep -c 计数 > --max）→ FAIL rc=1＋上下文逐行；
  - ocamlc 面红（在卷且实跑 rc≠0）→ FAIL rc=1；ocamlc 二进制缺卷 → NOT-RUN
    随账（让席不计红·承 gate7 4b「缺卷显式注记跳过」口径），魔数面独立判。
  分工律：.vo 魔数/新鲜度四件套归 verify_vo.py，本闸只管提取面，不重复四件套。

CLI 形制承 verify_vo.py：--help=0；未知形参/用法错=2；--v/--world 缺一=2；
文件缺失（--v／--world／world/<Mod>.vo 未编译／rocq 二进制缺卷）=9 fail-loud
（rocq 缺卷禁模拟编译·承 wrapper/coqc_shim.sh 口径）；判红=1。

温控律（§R2）：本件自身不内嵌 guard（承 wrapper/gate7_probe.sh 契约形——guard
只包 python 进程，编译子进程全在其进程树内整经温控）。实跑必须 guard 包裹：
  bash tools/cpu_guard.sh -Reg /tmp/cw_reg_<席> -- python3 verify/extract_magic_check.py ...
套件内判据用假 rocq/ocamlc 桩驱动全链（零真编译·真链 E2E 归席位沙箱不入套件）。

用法：
  python3 verify/extract_magic_check.py --v <file.v> --world <dir>
      [--max N] [--json out.json] [--workdir dir] [--rocq BIN] [--ocamlc BIN]
      [--timeout SEC] [--selftest]

退出码：0=PASS；1=FAIL（三向任一红）；2=用法错；9=文件/二进制缺卷 fail-loud。
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True  # import 零 __pycache__（禁向仓写·承 gate7 探针契约§2）
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "names"))
import mac_stmt_names  # noqa: E402  （冻结件只读 import·提取核同源复用）

# ------------------------------------------------------------------ ⓪ 盲区补全面（v15·首战判例工具化）
# 首战判例（更新账 v15 §二·本席实机复勘）：gate7 提取闸四件 2 PASS／2 fail-loud——
# G09_MiscSmall `Class` 声明、G13_EvictFam `Extraction` 命令双双撞 mac_stmt_names
# 未知 vernacular→「语句清单异常」rc=9（提取闸根本没走到魔数面）。
# 语句 token 集常量定位＝names/mac_stmt_names.py:38–51 TARGET_KINDS/SKIP_KINDS——
# 该件系 frozen8 tier1 冻结件（md5 在册·frozen8.py:76/test_precedent_station.py:35/
# quad8 四仓副本群三重钉）源文件禁改，故本件 import 面就地扩补（进程内·冻结件
# 字节零触碰）：
#   声明面＝不产提取物的合法声明 vernacular（工单点名 Class/Record/Context/Schema/
#   Declare/Instance——其中 Record/Context/Declare 冻结件已在 SKIP_KINDS·Instance
#   已在 TARGET_KINDS·实缺者 Class/Schema/Scheme 等如下补齐）；
#   命令面＝首战第二红 G13 `Extraction` 同盲区类（About/Close/Recursive/Separate
#   同族·本席 live 世界实勘 262/9/102/102 处在卷）——census 流程中皆不产提取物
#   （目标集只出自 TARGET_KINDS·frozen 零触碰）。
# 提取消毒面不受影响：既有绿件语句清单逐名不变；未知 vernacular 仍 fail-loud
# （盲区收窄≠静默扩容）。
DECL_SKIP_EXT = frozenset({
    # 声明面（合法声明·不产提取物）
    "Class", "Schema", "Scheme", "Structure", "Canonical", "Coercion",
    "Derive", "Existing", "Primitive", "Register",
    # 命令面（首战 G13 `Extraction` 同盲区·live 世界实勘在卷）
    "Extraction", "Recursive", "Separate", "About", "Close",
})
mac_stmt_names.SKIP_KINDS.update(DECL_SKIP_EXT)

PROG = "extract_magic_check"
ROQC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq"
OCAMLC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/ocamlc"
MAGIC_TOKEN = "Obj.magic"
DRIVER_PRELUDE = ("From Stdlib Require Import Extraction.\n"
                  "Require Import %s.\n"
                  "Separate Extraction %s.\n")  # 承 tools/_gen_fin_mac.py:126 Stdlib 形（免 9.0 弃用警）


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ ① 解析面
def parse_separate_extraction(masked):
    """从掩蔽后文本解析全部 Separate Extraction 命令的名字组（有序·段内 IDENT 全收）。

    返回 [[名, ...], ...]（逐命令一组·单命令多名全提律承 cw-ci-sop §1·E law1——
    逐命令重置输出 last-write-wins，多目标必须单命令全提）。
    """
    cmds = []
    for m in re.finditer(r"\bSeparate\s+Extraction\b", masked):
        seg_end = mac_stmt_names.find_boundary_period(masked, m.end())
        if seg_end < 0:
            seg_end = len(masked)
        seg = masked[m.end():seg_end]
        names = re.findall(mac_stmt_names.IDENT_RE, seg)
        cmds.append(names)
    return cmds


def collect_targets(v_path):
    """工序①：解析 Separate Extraction 目标；无命令则 census 口径收全部主定义。

    返回 (mode, targets, extra)——mode ∈ inline/driver；extra 载逐命令账或
    语句清单账。零主定义 → fail-loud rc=9（无可提取面≠绿·承 _gen_fin_mac 口径）。
    """
    src = io.open(v_path, encoding="utf-8-sig", errors="replace").read()
    masked = mac_stmt_names.strip_comments_strings(src)
    cmds = parse_separate_extraction(masked)
    if cmds:
        targets, seen = [], set()
        for names in cmds:
            for nm in names:
                if nm not in seen:
                    seen.add(nm)
                    targets.append(nm)
        return "inline", targets, {"commands": cmds}
    inv = mac_stmt_names.extract_statements(v_path)
    if inv["anomalies"]:
        print("FAIL-LOUD: 语句清单异常（fail-loud 逐笔·禁静默）: %s"
              % (inv["anomalies"],), file=sys.stderr)
        sys.exit(9)
    stmts = [s["name"] for s in inv["statements"]]
    if not stmts:
        print("FAIL-LOUD: 零主定义（census 口径无可提取语句）: %s" % v_path,
              file=sys.stderr)
        sys.exit(9)
    return "driver", stmts, {"statements": stmts}


def build_driver_text(module, targets):
    return DRIVER_PRELUDE % (module, " ".join(targets))


# ------------------------------------------------------------------ ③ 计数面
def grep_count_magic(path):
    """等价 `grep -c Obj.magic <path>`（行计数口径：一行多魔数计一）。

    返回 (计数, [命中行号...])。
    """
    n = 0
    lines_hit = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            if MAGIC_TOKEN in ln:
                n += 1
                lines_hit.append(i)
    return n, lines_hit


def magic_contexts(path, lines_hit, radius=1):
    """魔数行上下文出账（命中行±radius·前缀 'L<行号>:'，邻行 '*' 标）。"""
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        all_lines = fh.read().splitlines()
    out = []
    for ln in lines_hit:
        for j in range(max(1, ln - radius), min(len(all_lines), ln + radius) + 1):
            mark = "L%d:" % j if j == ln else "  *"
            out.append("%-8s %s" % (mark, all_lines[j - 1]))
        if ln != lines_hit[-1]:
            out.append("  --")
    return out


# ------------------------------------------------------------------ ② 编译面
def _run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text="utf-8",
                           errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT after %ss" % timeout
    except OSError as e:
        return -8, "SPAWN-FAIL: %s" % e


def run_extraction(rocq, workdir, v_file, world, timeout):
    """rocq 提取一发：`rocq c -native-compiler no -q -Q <world> "" <v>`（cwd=工作目录）。"""
    cmd = [rocq, "c", "-native-compiler", "no", "-q", "-Q", world, "", v_file]
    return _run(cmd, workdir, timeout)


def ocamlc_face(ocamlc, workdir, main_mod, timeout):
    """ocamlc 编提取产物（4b 面）：逐模 .mli 先 .ml 后；跨模依赖重试轮。

    返回 {"status": pass/fail/NOT-RUN, "binary":..., "units": [...]}——
    status 以主模 <Mod>.ml 编译成功为准；二进制缺卷 → NOT-RUN（让席不计红）。
    """
    if not (os.path.isfile(ocamlc) and os.access(ocamlc, os.X_OK)):
        return {"status": "NOT-RUN", "binary": ocamlc, "units": [],
                "note": "ocamlc 缺卷（4b 让席·显式注记）: %s" % ocamlc}
    mods = sorted(set(f[:-3] for f in os.listdir(workdir) if f.endswith(".ml")))
    units = {m: {"module": m, "mli_rc": None, "rc": None} for m in mods}
    tails = {}
    done, pending = set(), list(mods)
    # 重试轮：.mli 与 .ml 失败同权入 pending——缺依赖 .cmi 下一轮补齐（Clean.mli
    # open Datatypes 判例：mli 本身即需跨模 cmi）；全轮无完成即停（余者=真红）
    for _round in range(len(mods) + 2):
        if not pending:
            break
        progressed = False
        rest = []
        for m in pending:
            unit = units[m]
            mli = os.path.join(workdir, m + ".mli")
            if os.path.isfile(mli):
                rc_i, _ = _run([ocamlc, "-I", ".", "-c", m + ".mli"], workdir, timeout)
                unit["mli_rc"] = rc_i
                if rc_i != 0:
                    rest.append(m)  # cmi 未生·下轮再试（依赖补齐后自愈）
                    continue
            rc_b, tail_b = _run([ocamlc, "-I", ".", "-c", m + ".ml"], workdir, timeout)
            unit["rc"] = rc_b
            if rc_b == 0:
                done.add(m)
                progressed = True
            else:
                tails[m] = tail_b[-300:]
                rest.append(m)
        pending = rest
        if not progressed:
            break
    status = "pass" if main_mod in done else "fail"
    face = {"status": status, "binary": ocamlc,
            "units": [units[m] for m in mods]}
    if status == "fail" and main_mod in tails:
        face["tail"] = tails[main_mod]
    return face


# ------------------------------------------------------------------ 判词面
def check(v_path, world, max_magic=0, rocq=ROQC_DEFAULT, ocamlc=OCAMLC_DEFAULT,
          timeout=600, workdir=None, keep=False):
    """五步工序全链。返回 (exit_code, ledger_dict)——判词三向见模块 docstring。"""
    v_path = os.path.abspath(v_path)
    world = os.path.abspath(world)
    module = os.path.splitext(os.path.basename(v_path))[0]
    mode, targets, extra = collect_targets(v_path)

    tmp_owner = workdir is None
    if tmp_owner:
        workdir = tempfile.mkdtemp(prefix="rocqwash_emc_")
    else:
        os.makedirs(workdir, exist_ok=True)
    try:
        # 已编译前置：world/<Mod>.vo 在卷（先编后检·gate7 同律）
        vo = os.path.join(world, module + ".vo")
        if not os.path.isfile(vo):
            print("FAIL-LOUD: world 未编译 .vo 缺失: %s（先编后检·本闸不代编译）" % vo,
                  file=sys.stderr)
            return 9, {"module": module, "mode": mode, "targets": targets,
                       "verdict": "FAIL-LOUD-NO-VO", "world": world,
                       "missing_vo": vo}
        if not (os.path.isfile(rocq) and os.access(rocq, os.X_OK)):
            print("FAIL-LOUD: rocq 缺卷（禁模拟编译）: %s（--rocq 覆写）" % rocq,
                  file=sys.stderr)
            return 9, {"module": module, "mode": mode, "targets": targets,
                       "verdict": "FAIL-LOUD-NO-ROCQ", "rocq": rocq}

        # ① 提取稿：driver 形生成临时稿入工作目录；inline 形复制源件入工作目录
        #（零写世界——产品全落工作目录，世界 .vo 只读供 Require）
        if mode == "driver":
            drv = os.path.join(workdir, "_%s_emc_driver.v" % module)
            with io.open(drv, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(build_driver_text(module, targets))
            compile_v = "_%s_emc_driver.v" % module
        else:
            drv = None
            compile_v = module + ".v"
            with io.open(os.path.join(workdir, compile_v), "wb") as fh:
                with open(v_path, "rb") as g:
                    fh.write(g.read())

        # ② rocq 提取 → ocamlc 编产物
        t0 = time.time()
        rocq_rc, rocq_out = run_extraction(rocq, workdir, compile_v, world, timeout)
        secs = round(time.time() - t0, 1)
        ml = os.path.join(workdir, module + ".ml")
        mli = os.path.join(workdir, module + ".mli")
        ml_exists = os.path.isfile(ml)
        oc = {"status": "NOT-RUN", "binary": ocamlc, "units": [],
              "note": "提取面红·4b 未跑"} if (rocq_rc != 0 or not ml_exists) \
            else ocamlc_face(ocamlc, workdir, module, timeout)

        # ③ grep -c Obj.magic（行计数口径）
        magic_ml, lines_hit = grep_count_magic(ml) if ml_exists else (None, [])
        magic_mli = grep_count_magic(mli)[0] if os.path.isfile(mli) else None
        contexts = magic_contexts(ml, lines_hit) if ml_exists and lines_hit else []
        ml_lines = io.open(ml, encoding="utf-8", errors="replace").read().splitlines() \
            if ml_exists else []

        ledger = {"tool": PROG, "v": v_path, "world": world, "module": module,
                  "mode": mode, "targets": targets,
                  "names_count": len(targets), "commands": extra.get("commands"),
                  "statements": extra.get("statements"),
                  "driver_v": drv, "workdir": workdir,
                  "rocq_rc": rocq_rc, "rocq_secs": secs,
                  "rocq_tail": (rocq_out[-400:] if rocq_rc != 0 else None),
                  "ml": ml if ml_exists else None,
                  "magic_ml": magic_ml, "magic_mli": magic_mli,
                  "magic_lines": [{"line": i, "text": ml_lines[i - 1]}
                                  for i in lines_hit] if ml_exists else [],
                  "max": max_magic, "ocamlc": oc,
                  "md5_v": md5_of(v_path), "md5_vo": md5_of(vo)}

        # ④ 判词三向
        reds = []
        if rocq_rc != 0:
            reds.append("提取面红: rocq rc=%s" % rocq_rc)
        elif not ml_exists:
            reds.append("提取面红: <Mod>.ml 未产出（提取静默跳过?）")
        if magic_ml is not None and magic_ml > max_magic:
            reds.append("魔数面红: %d > max %d" % (magic_ml, max_magic))
        if oc["status"] == "fail":
            reds.append("ocamlc 面红: 主模编译不过")
        verdict = "FAIL" if reds else "PASS"
        ledger["verdict"] = verdict
        ledger["reds"] = reds

        print("== extract_magic 账（v=%s mode=%s）==" % (os.path.basename(v_path), mode))
        print("  module            %s" % module)
        print("  targets           %d 名 %s" % (len(targets),
                                                " ".join(targets[:8]) +
                                                (" ..." if len(targets) > 8 else "")))
        print("  rocq_extract      rc=%s (%ss)" % (rocq_rc, secs))
        print("  ocamlc            %s (%d/%d units)"
              % (oc["status"],
                 sum(1 for u in oc["units"] if u["rc"] == 0), len(oc["units"])))
        print("  magic_ml          %s （max=%d）" % (magic_ml, max_magic))
        print("  magic_mli         %s" % magic_mli)
        for r in reds:
            print("  RED: %s" % r)
        if contexts and magic_ml is not None and magic_ml > max_magic:
            print("  -- 魔数行上下文（%s）--" % ml)
            for c in contexts:
                print("  " + c)
        print("md5 v=%s" % ledger["md5_v"])
        print("VERDICT: %s" % verdict)
        return (0 if verdict == "PASS" else 1), ledger
    finally:
        if tmp_owner and not keep:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)


# ------------------------------------------------------------------ selftest
def selftest():
    """内嵌冻结向量组（临时目录驱动·假 rocq/ocamlc 桩全链·零真编译零触真仓）：
    解析正/注释诱饵负／计数 grep-c 口径／上下文形／fallback 主定义收集／driver 稿
    词面／E2E 红绿双判（假桩）／提取红 fail-loud／ocamlc 双判／CLI 四码／Class
    盲区补全（首战判例形 census 不误判·Frobnicate 认名 F2 回归·未知 vernacular
    仍红 9）。"""
    import shutil
    tmp = tempfile.mkdtemp(prefix="rocqwash_emc_self_")
    try:
        # 1 解析正判：单命令多名＋段界含点
        masked = "Definition a := 1.\nSeparate Extraction foo bar'x ns_δ. Definition b := 2.\n"
        assert parse_separate_extraction(masked) == [["foo", "bar'x", "ns_δ"]], \
            parse_separate_extraction(masked)
        # 2 注释诱饵负判：注释内命令不入账（strip 后无痕）
        v1 = os.path.join(tmp, "decoy.v")
        with io.open(v1, "w", encoding="utf-8") as fh:
            fh.write("(* Separate Extraction decoy_one. *)\n"
                     "Definition real_one := 1.\nSeparate Extraction real_one.\n")
        mode, targets, _ = collect_targets(v1)
        assert mode == "inline" and targets == ["real_one"], (mode, targets)
        # 3 计数 grep-c 口径：一行多魔数计一
        ml = os.path.join(tmp, "M.ml")
        with io.open(ml, "w", encoding="utf-8") as fh:
            fh.write("let a = Obj.magic x\nlet b = 1\nlet c = f (Obj.magic y) (Obj.magic z)\n")
        n, hits = grep_count_magic(ml)
        assert (n, hits) == (2, [1, 3]), (n, hits)
        # 4 上下文形：命中行 L 前缀＋邻行 * 标
        ctx = magic_contexts(ml, [1])
        assert any(x.startswith("L1:") and "Obj.magic x" in x for x in ctx)
        assert not any(x.startswith("L3") for x in ctx)
        # 5 fallback 主定义收集：census 口径（Lemma 计入·Let 不计·注释诱饵不计）
        v2 = os.path.join(tmp, "fb.v")
        with io.open(v2, "w", encoding="utf-8") as fh:
            fh.write("(* Definition ghost_in_comment := 0. *)\n"
                     "Definition fb_a := 1.\nLemma fb_l : True. Proof. exact I. Qed.\n"
                     "Let fb_let := 2.\n")
        mode2, targets2, _ = collect_targets(v2)
        assert mode2 == "driver" and targets2 == ["fb_a", "fb_l"], (mode2, targets2)
        # 6 driver 稿词面：Stdlib Extraction 前奏＋Require＋单命令多名
        dt = build_driver_text("FB", ["fb_a", "fb_l"])
        assert "From Stdlib Require Import Extraction." in dt
        assert "Require Import FB." in dt
        assert "Separate Extraction fb_a fb_l." in dt
        # 7 E2E 红绿双判（假 rocq/ocamlc 桩·临时世界）
        w = os.path.join(tmp, "world")
        os.makedirs(w)
        v3 = os.path.join(w, "Probe.v")
        with io.open(v3, "w", encoding="utf-8") as fh:
            fh.write("Definition p_one := 1.\nDefinition p_two := 2.\n")
        with open(os.path.join(w, "Probe.vo"), "wb") as fh:  # 已编译前置件（存在性判）
            fh.write(b"FAKEVO")
        mlc = os.path.join(tmp, "canned.ml")
        with io.open(mlc, "w", encoding="utf-8") as fh:
            fh.write("let p_one = Obj.magic (Obj.magic 1)\nlet p_two = Obj.magic 2\n")
        frocq = os.path.join(tmp, "fake_rocq.sh")
        foc = os.path.join(tmp, "fake_oc.sh")
        if os.name == "nt":
            # Windows 桩面（ci.yml known_red 判例「rocq rc=-8 observed here」：
            # CreateProcess 不能直执 shebang 脚本）——同逻辑桩改 .cmd 壳＋py 桩形
            # （last 参遍历／Require Import 剥名／缺省 basename／EMC_FAKE_ML 复制／
            # EMC_FAKE_RC 退码逐条对齐 bash 桩），判词不变；POSIX 分支字节不动。
            frocq_py = os.path.join(tmp, "fake_rocq.py")
            with io.open(frocq_py, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(
                    "import os, shutil, sys\n"
                    "last = None\n"
                    "for a in sys.argv[1:]:\n"
                    "    last = a\n"
                    "mod = ''\n"
                    "if last and os.path.isfile(last):\n"
                    "    with open(last, encoding='utf-8', errors='replace') as fh:\n"
                    "        for ln in fh:\n"
                    "            if ln.startswith('Require Import'):\n"
                    "                mod = ln[len('Require Import '):].strip()\n"
                    "                break\n"
                    "    if mod.endswith('.'):\n"
                    "        mod = mod[:-1]\n"
                    "if not mod:\n"
                    "    mod = os.path.splitext(os.path.basename(last or ''))[0]\n"
                    "mlsrc = os.environ.get('EMC_FAKE_ML')\n"
                    "if mlsrc:\n"
                    "    shutil.copyfile(mlsrc, mod + '.ml')\n"
                    "sys.exit(int(os.environ.get('EMC_FAKE_RC', '0')))\n")
            with io.open(os.path.join(tmp, "fake_rocq.cmd"), "w",
                         encoding="ascii", newline="\r\n") as fh:
                fh.write('@py -B "%~dp0fake_rocq.py" %*\r\n')
            with io.open(os.path.join(tmp, "fake_oc.cmd"), "w",
                         encoding="ascii", newline="\r\n") as fh:
                fh.write("@echo off\r\n"
                         "if not defined EMC_OC_RC set \"EMC_OC_RC=0\"\r\n"
                         "exit /b %EMC_OC_RC%\r\n")
            frocq = os.path.join(tmp, "fake_rocq.cmd")
            foc = os.path.join(tmp, "fake_oc.cmd")
        else:
            with io.open(frocq, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/bash\n"
                         "for last; do :; done\n"
                         "# 真 rocq 形仿：.ml 以被提取模块命名（driver 稿取 Require Import 名；\n"
                         "# inline 稿即本件名）——承 gate7 提取产物 <Mod>.ml 口径\n"
                         "if [ -f \"$last\" ]; then\n"
                         "  mod=\"$(grep -m1 '^Require Import' \"$last\" | sed 's/^Require Import //; s/\\.$//')\"\n"
                         "fi\n"
                         "[ -n \"${mod:-}\" ] || mod=\"$(basename \"$last\" .v)\"\n"
                         "[ -n \"${EMC_FAKE_ML:-}\" ] && cp \"$EMC_FAKE_ML\" \"$mod.ml\"\n"
                         "exit \"${EMC_FAKE_RC:-0}\"\n")
            with io.open(foc, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/bash\nexit \"${EMC_OC_RC:-0}\"\n")
            os.chmod(frocq, 0o755)
            os.chmod(foc, 0o755)
        os.environ["EMC_FAKE_ML"] = mlc
        wd = os.path.join(tmp, "wd")
        # 红判：魔数 2 > max 1 → rc 1 fail-loud
        rc = run_args(["--v", v3, "--world", w, "--max", "1",
                       "--workdir", wd, "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "max=1 魔数 2 应红 rc=1 实测 %d" % rc
        rc = run_args(["--v", v3, "--world", w, "--max", "2", "--json",
                       os.path.join(tmp, "acc.json"), "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 0, "max=2 魔数 2 应绿 rc=0 实测 %d" % rc
        acc = json.load(io.open(os.path.join(tmp, "acc.json"), encoding="utf-8"))
        assert acc["verdict"] == "PASS" and acc["magic_ml"] == 2 \
            and acc["mode"] == "driver" and acc["targets"] == ["p_one", "p_two"], acc
        # 8 driver 稿落盘词面（--workdir 显式给＝自管不自动清）
        drvt = io.open(os.path.join(wd, "_Probe_emc_driver.v"),
                       encoding="utf-8").read()
        assert "Separate Extraction p_one p_two." in drvt, drvt
        # 9 提取红 fail-loud：假 rocq rc=1 → 判词 FAIL rc=1（rocq_tail 在账）
        os.environ["EMC_FAKE_RC"] = "1"
        rc = run_args(["--v", v3, "--world", w, "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "提取红应 rc=1 实测 %d" % rc
        os.environ["EMC_FAKE_RC"] = "0"
        # 10 ocamlc 面红（在卷实跑 rc=1）→ FAIL；缺卷 → NOT-RUN 魔数面独立判
        os.environ["EMC_OC_RC"] = "1"
        rc = run_args(["--v", v3, "--world", w, "--max", "9", "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "ocamlc 红应 rc=1 实测 %d" % rc
        del os.environ["EMC_OC_RC"]
        rc = run_args(["--v", v3, "--world", w, "--max", "9", "--workdir", wd,
                       "--rocq", frocq,
                       "--ocamlc", os.path.join(tmp, "no_such_ocamlc")])
        assert rc == 0, "ocamlc 缺卷应 NOT-RUN 让席·魔数 2≤9 应 rc=0 实测 %d" % rc
        # 11 CLI 四码：--help 0／未知形参 2／缺 --world 2／缺件 9（v 缺／vo 缺）
        assert run_args(["--help"]) == 0
        assert run_args(["--bogus"]) == 2
        assert run_args(["--v", v3]) == 2
        assert run_args(["--v", os.path.join(tmp, "gone.v"), "--world", w]) == 9
        assert run_args(["--v", v3, "--world", os.path.join(tmp, "noworld")]) == 9
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        assert run_args(["--v", v3, "--world", w2, "--rocq", frocq]) == 9, \
            "world 未编译 .vo 缺失应 rc=9"
        # 12 v15 盲区补全（首战判例形）：Class 声明＋命令面 vernacular census 不再
        #    误判异常——声明/命令不入目标·唯真主定义入账；Frobnicate 认名 F2 回归
        #    （20261116 三锚同改·冻结件 TARGET_KINDS 在册 md5 9e26c0db…）；未知
        #    vernacular 仍红 9
        v4 = os.path.join(tmp, "cls.v")
        with io.open(v4, "w", encoding="utf-8") as fh:
            fh.write("Declare Scope req_scope.\n"
                     "Class reqord (R : Set) : Set := mk {\n"
                     "  rord_le_dec : forall a b : R, Or (le a b) (Not (le a b));\n"
                     "  rlt_dec : forall a b : R, Or (lt a b) (Not (lt a b))\n"
                     "}.\n"
                     "Record rstore : Set := mkstore { rs_carrier : Set }.\n"
                     "Scheme reqord_ind := Induction for reqord Sort Prop.\n"
                     "Definition cls_use (x y : reqord nat) := x.\n"
                     "Extraction cls_use.\n"
                     "About cls_use.\n")
        mode4, targets4, extra4 = collect_targets(v4)
        assert mode4 == "driver" and targets4 == ["cls_use"], (mode4, targets4)
        assert extra4["statements"] == ["cls_use"], extra4["statements"]
        # F2 20261116 三锚同改回归：Frobnicate 已入冻结件 TARGET_KINDS
        #   （names/mac_stmt_names.py:40·LEDGER8 在册 md5
        #   9e26c0db2c60ced3629a13a821bdf615）——census 认名入目标（含 Proof
        #   证明体成臂消费）·零异常；盲区收窄≠静默扩容：未知 vernacular 钉子
        #   换真未知词 Gadgetize 仍 fail-loud rc=9
        assert "Frobnicate" in mac_stmt_names.TARGET_KINDS, \
            "F2 回归: 冻结件应认 Frobnicate 语句名"
        v6 = os.path.join(tmp, "frob.v")
        with io.open(v6, "w", encoding="utf-8") as fh:
            fh.write("Frobnicate frob_one : nat. Proof. exact 1. Qed.\n"
                     "Definition frob_ok := frob_one.\n")
        mode6, targets6, extra6 = collect_targets(v6)
        assert mode6 == "driver" and targets6 == ["frob_one", "frob_ok"], \
            (mode6, targets6)
        assert extra6["statements"] == ["frob_one", "frob_ok"], extra6["statements"]
        v5 = os.path.join(tmp, "unk.v")
        with io.open(v5, "w", encoding="utf-8") as fh:
            fh.write("Gadgetize widget.\nDefinition unk_ok := 1.\n")
        try:
            collect_targets(v5)
            raise AssertionError("未知 vernacular 应 fail-loud rc=9")
        except SystemExit as e:
            assert e.code == 9, "未知 vernacular 应 rc=9 实测 %r" % (e.code,)
        print("EXTRACT-MAGIC-SELFTEST PASS: 解析正负/注释诱饵/计数grep-c口径/上下文形/"
              "fallback收集/driver稿词面/E2E红绿/提取红/ocamlc双判/CLI四码/"
              "Class盲区补全/Frobnicate认名F2回归 十二判全过")
        return 0
    finally:
        os.environ.pop("EMC_FAKE_ML", None)
        os.environ.pop("EMC_FAKE_RC", None)
        os.environ.pop("EMC_OC_RC", None)
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="gate7 提取面 Obj.magic 逐件机检闸（Separate Extraction→rocq 提取→"
                    "ocamlc→grep -c Obj.magic→--max 判红绿）")
    ap.add_argument("--v", default=None, help="源 .v 路径（须已编译出 world/<Mod>.vo）")
    ap.add_argument("--world", default=None, help="世界目录（-Q <world> \"\"·只读）")
    ap.add_argument("--max", type=int, default=0,
                    help="Obj.magic 行计数上限（默认 0·超线 rc=1 fail-loud）")
    ap.add_argument("--json", default=None, help="台账 JSON 出账路径")
    ap.add_argument("--workdir", default=None,
                    help="提取工作目录（缺省临时目录自动清；显式给＝自管不自动清）")
    ap.add_argument("--rocq", default=ROQC_DEFAULT, help="rocq 绝对路径（缺卷 rc=9）")
    ap.add_argument("--ocamlc", default=OCAMLC_DEFAULT,
                    help="ocamlc 绝对路径（缺卷 NOT-RUN 让席不计红）")
    ap.add_argument("--timeout", type=int, default=600, help="子进程超时秒（默认 600）")
    ap.add_argument("--keep", action="store_true",
                    help="缺省临时工作目录不清理（与 --workdir 互斥使用场景）")
    ap.add_argument("--selftest", action="store_true", help="内嵌冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    if not args.v or not args.world:
        ap.error("--v 与 --world 必填（--selftest 除外）")

    for label, path in (("--v", args.v), ("--world", args.world)):
        if not os.path.exists(path):
            print("FAIL-LOUD: %s 路径缺失: %s" % (label, path), file=sys.stderr)
            sys.exit(9)

    rc, ledger = check(v_path=args.v, world=args.world, max_magic=args.max,
                       rocq=args.rocq, ocamlc=args.ocamlc, timeout=args.timeout,
                       workdir=args.workdir, keep=args.keep)
    if rc == 9:
        sys.exit(9)

    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(ledger, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(rc)


if __name__ == "__main__":
    main()
