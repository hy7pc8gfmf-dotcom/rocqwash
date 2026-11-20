#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quad8_reconcile.py — 四仓同 md5 副本群对账名单机检（rocqwash wrapper/·20261031 席 rqadapt）

缺口闭合：在役八组件在四仓各持有正本副本（rocqwash／ConstructiveWorld／
work_M_wave1／ConstructiveWorld-Set），今日 md5 全等但无漂移对账——副本各自演进
即静默分叉；工单路径与实账执行路径已现分叉实例（seat_bksver gate4：工单录
ConstructiveWorld-Set 路径、实账 logs/gate4_bv_tree.json 只记工具名串，执行副本
字节身份无机械锁定；且 ConstructiveWorld-Main/scripts/gates 正本与 CW 沙箱现役
副本已另成 09c5… 第二 md5 家族，对 d7ab… 在册家族构成既成漂移证据）。

本件把「今日全等」变「机械对账在跑」：
  - freeze：在册副本逐件重算 md5 出四仓对账名单（副本群非全等/缺失即 fail-closed
    拒出名单——禁漂移洗账）；
  - check：六环咬合对账（名单 tier2 自洽→名单≡在册→tier2 侧册→盘≡名单→副本群
    全等→在册外副本扫出）＋在册四仓外正本 audit 只录不判；
  - 逐调断言走同仓 wrapper/frozen_call.py（名单即其锚）。

与冻结件关系：certify/freeze_manifest.py 在役冻结禁改——零改动，只读 import 其
md5_bytes/tier2_of 口径（两层冻结语义逐字承 v1：tier1=`rel  md5` 账文、tier2=账文
md5；certify/frozen8.py 同款并存形·适配一律新文件）。名单 schema 自立门户
（rocqwash-quad8-manifest/1）：误喂 v1 check 即 schema 不识 exit 2——口径分家
fail-closed。

对账名单（ledger）行式承 seat_nw6ver/tools/world_md5_assert.py 同款 md5 断言法：
OK/MISMATCH/MISSING/UNREGISTERED 逐行出账＋GROUP/AUDIT 汇总行；exit 0 iff 零漂移。

在册四仓与副本（20261031 侦察 md5 实测在卷·seat_rqadapt 账）：
  rq=/Users/apple/Desktop/rocqwash            cw=/Users/apple/Desktop/ConstructiveWorld
  w1=/Users/apple/Desktop/S系Prop清除战役工单/work_M_wave1
  set=/Users/apple/Desktop/ConstructiveWorld-Set
  scan/mac_stmt_scan.py      rq＋w1 两副本       names/mac_stmt_names.py   rq 单副本
  verify/gate4_comment_guard.py rq＋set 两副本    tools/cpu_guard.sh        rq＋cw 两副本
  wash/wash_engine.py·verify/verify_vo.py·seam/seam_probe.py·certify/freeze_manifest.py
  各 rq 单副本

audit（只录不判——在册四仓之外的正本/现役沙箱域属他席管辖，本席只读）：
  main=/Users/apple/Desktop/ConstructiveWorld-Main/scripts/gates/gate4_comment_guard.py
  cw 沙箱现役 _dmregz4_regwave_sb 同名件——对 rq 家族 md5 出 AUDIT-OK/AUDIT-DIVERGED 行。

命令：
  python3 wrapper/quad8_reconcile.py freeze [--out LIST.json] [--tier2 T2.md5]
      [--roots-file JSON]
  python3 wrapper/quad8_reconcile.py check --list LIST.json [--tier2 T2.md5]
      [--ledger OUT.txt] [--json OUT] [--roots-file JSON]
  python3 wrapper/quad8_reconcile.py --selftest
  python3 wrapper/quad8_reconcile.py --registry   打印在册副本表（slug rel md5 位空）

--roots-file：slug→root JSON 映射覆盖常量（selftest 夹具专用；生产不给即用内置
四仓常量——盘面路径搬迁由 check 环② 名单≡在册 当场现形）。

诚实律（承 CONTRIBUTING §0）：
  - 只认机械证据（重算 md5/退出码/逐字节恒同），不出「未漂移」口头判词；
  - fail-closed：副本群非全等/缺失拒出名单；名单畸形/口径不符一律非零＋响亮输出；
  - 幂等可重放：freeze 无时间戳无环境噪声，同盘面重产名单逐字节恒同；
  - audit 域只读只录不判——他席域非零判不越权，漂移证据如实入账不掩。

写域声明：本器只写调用方显式指认的 --out/--tier2/--ledger/--json 出路径；sweep
全程只读；selftest 只写 mkdtemp 临时目录（测毕即删）；全器零编译零网络。

退出码：freeze 0=成／1=副本群非全等拒出名单／9=在册副本缺失／2=用法错；
check 0=零漂移／1=有漂移（mismatch/missing/unregistered/群漂移/名单或侧册破）／
2=名单畸形／9=名单或侧册缺失；--registry／--selftest 0=绿／1=红。
"""
import argparse
import io
import json
import os
import sys

PROG = "quad8_reconcile"
SCHEMA = "rocqwash-quad8-manifest/1"

# ---------------- 在册四仓常量（20261031 侦察实测） ----------------

ROOTS = {
    "rq": "/Users/apple/Desktop/rocqwash",
    "cw": "/Users/apple/Desktop/ConstructiveWorld",
    "w1": "/Users/apple/Desktop/S系Prop清除战役工单/work_M_wave1",
    "set": "/Users/apple/Desktop/ConstructiveWorld-Set",
}
AUDIT_MAIN_ROOT = "/Users/apple/Desktop/ConstructiveWorld-Main"
AUDIT_CW_SB_GLOB = "沙箱/现役/*/scripts/gates/gate4_comment_guard.py"


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (docs/clean-mode-manual-20261114.md). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"

# 组件 → 在册副本（slug, 仓内 relpath）。key=组件名（承 frozen8 账载八件口径·
# rq 相对路径）；副本路径各异（set/cw 的 gate 域与仓根布局不同）。
REGISTRY = (
    ("scan/mac_stmt_scan.py",
     (("rq", "scan/mac_stmt_scan.py"), ("w1", "scan/mac_stmt_scan.py"))),
    ("names/mac_stmt_names.py",
     (("rq", "names/mac_stmt_names.py"),)),
    ("verify/gate4_comment_guard.py",
     (("rq", "verify/gate4_comment_guard.py"),
      ("set", "scripts/gates/gate4_comment_guard.py"))),
    ("tools/cpu_guard.sh",
     (("rq", "tools/cpu_guard.sh"), ("cw", "cpu_guard.sh"))),
    ("wash/wash_engine.py",
     (("rq", "wash/wash_engine.py"),)),
    ("verify/verify_vo.py",
     (("rq", "verify/verify_vo.py"),)),
    ("seam/seam_probe.py",
     (("rq", "seam/seam_probe.py"),)),
    ("certify/freeze_manifest.py",
     (("rq", "certify/freeze_manifest.py"),)),
)
# sweep 只认八件 basename（在册四仓内·在册位之外的同名件=UNREGISTERED）
BASENAMES = frozenset(os.path.basename(comp) for comp, _ in REGISTRY)
# sweep 剪枝：版本噪声（.git/__pycache__）＋席位域（沙箱/sandbox/seat*——各 seat
# 副本为权限内域·audit 面单独只录）
PRUNE_DIRS_EXACT = frozenset((".git", "__pycache__", "沙箱", "sandbox"))


def prune_dir(name):
    return name in PRUNE_DIRS_EXACT or name.startswith("seat")


_HERE = os.path.dirname(os.path.abspath(__file__))
_CERTDIR = os.path.join(os.path.dirname(_HERE), "certify")
if _CERTDIR not in sys.path:
    sys.path.insert(0, _CERTDIR)
try:
    import freeze_manifest as _v1  # noqa: E402  （在役冻结件·只 import 不改）
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 冻结同侪 certify/freeze_manifest.py 不可导入: %s" % _e,
          file=sys.stderr)
    sys.exit(9)


def entry_rows(roots):
    """在册副本全表 [(slug/rel, abs_path)]（tier1 键=slug/rel·排序前）。"""
    rows = []
    for _comp, copies in REGISTRY:
        for slug, rel in copies:
            rows.append(("%s/%s" % (slug, rel), os.path.join(roots[slug], rel)))
    return rows


def load_roots(roots_file):
    if not roots_file:
        return dict(ROOTS)
    try:
        with io.open(roots_file, encoding="utf-8") as fh:
            user = json.load(fh)
        if not isinstance(user, dict) or not user:
            raise ValueError("roots-file 须为非空 JSON 对象")
    except Exception as e:
        print("FAIL-LOUD: --roots-file 解析失败: %s" % e, file=sys.stderr)
        sys.exit(2)
    roots = dict(ROOTS)
    roots.update({str(k): str(v) for k, v in user.items()})
    for slug, root in roots.items():
        if not os.path.isdir(root):
            print("FAIL-LOUD: 根目录缺失: %s (%s)" % (root, slug), file=sys.stderr)
            sys.exit(9)
    return roots


def live_md5(path):
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return _v1.md5_bytes(f.read())


def sweep_unregistered(roots, registered):
    """四仓内八件 basename 的在册位之外副本（只读扫·席位域剪枝）。

    sweep 域＝在册 REGISTRY 四仓 slug（rq/cw/w1/set）——audit 域（main 等只录
    不判根）永不入 sweep：audit 域的漂移由 audit_lines 如实录账，不双计非零。"""
    slugs = sorted({s for _c, cps in REGISTRY for s, _r in cps} & set(roots))
    found = []
    seen = set()
    for slug in slugs:
        base = roots[slug]
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not prune_dir(d))
            for fn in sorted(filenames):
                if fn not in BASENAMES:
                    continue
                fp = os.path.abspath(os.path.join(dirpath, fn))
                if fp in seen:
                    continue
                seen.add(fp)
                if fp in registered:
                    continue
                found.append((fp, slug))
    return sorted(found)


def audit_lines(roots):
    """在册四仓之外的正本/现役沙箱域——对 rq 家族 md5 只录不判。"""
    # rq 家族 md5 取现盘重算（check/freeze 主环已判其在册位·此处只作比对基准）
    fam = live_md5(os.path.join(roots.get("rq", ROOTS["rq"]),
                                "verify/gate4_comment_guard.py"))
    out = []
    if fam is None:
        out.append("AUDIT-SKIP rq 家族 gate4 缺失·无比对基准")
        return out
    targets = []
    main_fp = os.path.join(roots.get("main", AUDIT_MAIN_ROOT),
                           "scripts/gates/gate4_comment_guard.py")
    if os.path.isdir(os.path.dirname(main_fp)):
        targets.append(("main", main_fp))
    cw_base = roots.get("cw", ROOTS["cw"])
    glob_dir = os.path.join(cw_base, "沙箱", "现役")
    if os.path.isdir(glob_dir):
        for name in sorted(os.listdir(glob_dir)):
            fp = os.path.join(glob_dir, name,
                              "scripts/gates/gate4_comment_guard.py")
            if os.path.isfile(fp):
                targets.append(("cw-sb", fp))
    for tag, fp in sorted(targets):
        m = live_md5(fp)
        if m == fam:
            out.append("AUDIT-OK %s %s %s（在册四仓外·只录不判）" % (tag, fp, m))
        else:
            out.append("AUDIT-DIVERGED %s %s live=%s fam=%s"
                       "（在册四仓外第二 md5 家族·只录不判·他席域）"
                       % (tag, fp, m, fam))
    return out


# ---------------- freeze：副本群全等方出对账名单 ----------------

def cmd_freeze(args):
    roots = load_roots(args.roots_file)
    if not args.out:
        print("FAIL-LOUD: freeze 需 --out 名单出路径", file=sys.stderr)
        sys.exit(2)
    if args.tier2 and os.path.abspath(args.out) == os.path.abspath(args.tier2):
        print("FAIL-LOUD: --out 与 --tier2 同路径（侧册须独立在册）", file=sys.stderr)
        sys.exit(2)
    rows, missing, diverged = [], [], []
    for key, fp in entry_rows(roots):
        m = live_md5(fp)
        if m is None:
            missing.append(key)
        else:
            rows.append((key, m))
    if missing:
        print("quad8 freeze FAIL: 在册副本缺失 %d 件——拒出名单（fail-loud）"
              % len(missing))
        for k in missing:
            print("  MISSING %s" % k)
        sys.exit(9)
    # 副本群今日须全等：同组件跨仓 distinct md5>1 即拒出（禁漂移洗账）
    live_map = dict(rows)
    for comp, copies in REGISTRY:
        fam = {s: live_map["%s/%s" % (s, r)] for s, r in copies}
        if len(set(fam.values())) > 1:
            diverged.append((comp, fam))
    if diverged:
        print("quad8 freeze FAIL: 副本群今日非全等（%d 组）——拒出名单"
              "（fail-closed·禁漂移洗账）" % len(diverged))
        for comp, fam in diverged:
            rel_by_slug = {s: r for _c, cps in REGISTRY
                           if _c == comp for s, r in cps}
            for s, m in sorted(fam.items()):
                print("  GROUP-DIVERGED %s %s/%s %s"
                      % (comp, s, rel_by_slug[s], m))
        sys.exit(1)
    rows.sort()
    t2 = _v1.tier2_of(rows)
    doc = {"schema": SCHEMA,
           "roots": {s: roots[s] for s in sorted(roots)},
           "n_copies": len(rows),
           "tier1": [[r, m] for r, m in rows],
           "tier2_md5_of_tier1_text": t2}
    for path in [args.out] + ([args.tier2] if args.tier2 else []):
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: 出路径父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("quad8 freeze: 在册 %d 副本·八组件跨仓全等——对账名单入册" % len(rows))
    for r, m in rows:
        print("  %s  %s" % (m, r))
    print("tier2=%s（tier1 账文 md5·两层冻结承 v1 口径）" % t2)
    if args.tier2:
        with io.open(args.tier2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t2 + "\n")
        print("tier2 侧册 ->", args.tier2)
    # 幂等自证：同盘面重产与在盘名单逐字节对照
    with io.open(args.out, encoding="utf-8", newline="") as fh:
        first = fh.read()
    again = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert first == again, "freeze 幂等自证失败（名单非确定性）"
    print("idempotent replay: 名单重产逐字节恒同 PASS")
    print("freeze OK: 名单 -> %s（对账：check --list %s --ledger <名单出路径>）"
          % (args.out, args.out))
    sys.exit(0)


# ---------------- check：六环咬合对账 ----------------

def cmd_check(args):
    roots = load_roots(args.roots_file)
    if not args.list:
        print("FAIL-LOUD: check 需 --list 在册名单", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.list):
        print("FAIL-LOUD: 名单缺失: %s" % args.list, file=sys.stderr)
        sys.exit(9)
    try:
        with io.open(args.list, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("schema") != SCHEMA:
            raise ValueError("schema 不识: %r（期望 %s；rq 单仓八件请走 "
                             "certify/frozen8.py；v1 整仓请走 "
                             "certify/freeze_manifest.py）" % (doc.get("schema"), SCHEMA))
        tier1 = doc["tier1"]
        reg_keys = sorted("%s/%s" % (s, r) for _c, cps in REGISTRY for s, r in cps)
        if (not isinstance(tier1, list)
                or sorted(r for r, _m in tier1) != reg_keys
                or not all(isinstance(row, list) and len(row) == 2
                           and all(isinstance(x, str) for x in row)
                           for row in tier1)):
            raise ValueError("tier1 须为在册 %d 副本 [slug/rel, md5]" % len(reg_keys))
    except Exception as e:
        print("FAIL-LOUD: 名单畸形: %s" % e, file=sys.stderr)
        sys.exit(2)

    ledger = []
    drift = False

    def emit(line):
        print(line)
        ledger.append(line)

    # 环① 名单 tier2 自洽（v1 口径——动名单即现形）
    t2_now = _v1.tier2_of([tuple(r) for r in doc["tier1"]])
    t2_ok = (t2_now == doc.get("tier2_md5_of_tier1_text"))
    emit("名单 tier2 自洽（名单未被改）: %s" % ("PASS" if t2_ok else "FAIL"))
    drift = drift or not t2_ok
    # 环② 名单口径≡在册（roots/键面 any 脱钩即漂移——防外来/换代旧名单蒙混）
    reg_roots = {s: roots[s] for s in sorted(roots)}
    roots_ok = (doc.get("roots") == reg_roots)
    emit("名单口径≡在册（roots+键面）: %s" % ("PASS" if roots_ok else "FAIL"))
    if not roots_ok:
        emit("  DRIFT roots   名单 %r ≠ 在册 %r" % (doc.get("roots"), reg_roots))
    drift = drift or not roots_ok
    # 环③ tier2 侧册咬合（外置在册·给了才咬）
    if args.tier2:
        if not os.path.isfile(args.tier2):
            print("FAIL-LOUD: 侧册缺失: %s" % args.tier2, file=sys.stderr)
            sys.exit(9)
        with io.open(args.tier2, encoding="utf-8") as fh:
            side = fh.read().strip()
        side_ok = (side == doc.get("tier2_md5_of_tier1_text"))
        emit("tier2 侧册咬合: %s" % ("PASS" if side_ok else "FAIL"))
        drift = drift or not side_ok
    # 环④ 现盘逐副本重算对照名单（world_md5_assert 同款 OK/MISMATCH/MISSING）
    list_map = {r: m for r, m in doc["tier1"]}
    n_ok = n_mis = n_rem = 0
    for key in sorted(list_map):
        slug, rel = key.split("/", 1)
        m = live_md5(os.path.join(roots[slug], rel))
        if m is None:
            n_rem += 1
            emit("MISSING %s %s（正本副本缺失）" % (key, roots[slug]))
            drift = True
        elif m != list_map[key]:
            n_mis += 1
            emit("MISMATCH %s 名单=%s 现盘=%s" % (key, list_map[key], m))
            drift = True
        else:
            n_ok += 1
            emit("OK %s %s" % (key, m))
    # 环⑤ 副本群跨仓全等（同组件 distinct>1=群漂移——静默分叉即此环现形）
    live_by_comp = {}
    for comp, copies in REGISTRY:
        for s, r in copies:
            m = live_md5(os.path.join(roots[s], r))
            if m is not None:
                live_by_comp.setdefault(comp, {})[s] = m
    g_div = 0
    for comp in sorted(live_by_comp):
        fam = live_by_comp[comp]
        n_distinct = len(set(fam.values()))
        emit("GROUP %s copies=%d distinct=%d %s"
             % (comp, len(fam), n_distinct,
                "UNIFORM" if n_distinct == 1 else "DIVERGED"))
        if n_distinct > 1:
            rel_by_slug = {s: r for c2, cps in REGISTRY
                           if c2 == comp for s, r in cps}
            for s in sorted(fam):
                emit("  GROUP-DIVERGED %s %s/%s %s"
                     % (comp, s, rel_by_slug[s], fam[s]))
            g_div += 1
            drift = True
    # 环⑥ 在册外副本扫出（四仓内八件同名件·席位域剪枝·在册位豁免）
    registered = {os.path.abspath(fp) for _k, fp in entry_rows(roots)}
    unreg = sweep_unregistered(roots, registered)
    for fp, slug in unreg:
        emit("UNREGISTERED %s repo=%s（在册位之外的同名正本副本——静默分叉入口）"
             % (fp, slug))
    if unreg:
        drift = True
    # audit：在册四仓之外——只录不判（他席域只读·漂移证据如实入账）
    n_audit_div = 0
    for line in audit_lines(roots):
        emit(line)
        if "AUDIT-DIVERGED" in line:
            n_audit_div += 1
    legs = ("tier2 自洽/名单≡在册" + ("/侧册" if args.tier2 else "")
            + "/盘≡名单/群全等/在册外扫出")
    emit("quad8 check %s: %s · %d OK / %d mismatch / %d missing / "
         "%d unregistered / %d 群漂移 / audit 漂移录 %d（只录不判）"
         % ("OK" if not drift else "FAIL", legs, n_ok, n_mis, n_rem,
            len(unreg), g_div, n_audit_div))
    if args.ledger:
        parent = os.path.dirname(os.path.abspath(args.ledger))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: --ledger 父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
        with io.open(args.ledger, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(ledger) + "\n")
        print("ledger ->", args.ledger)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"schema": SCHEMA, "list": args.list,
                       "tier2_ok": t2_ok, "roots_ok": roots_ok,
                       "ok": n_ok, "mismatch": n_mis, "missing": n_rem,
                       "unregistered": [fp for fp, _s in unreg],
                       "group_diverged": g_div,
                       "audit_diverged": n_audit_div,
                       "verdict": "PASS" if not drift else "FAIL"},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(1 if drift else 0)


# ---------------- --selftest：夹具四仓八判（零触真仓） ----------------

def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_quad8_self_")
    try:
        me = os.path.abspath(__file__)

        def w(root, rel, content):
            fp = os.path.join(root, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)

        # 夹具四仓：rq(set/主)＋w1＋cw；main 为 audit 域（ diverged 只录不判）
        frq = os.path.join(tmp, "rq")
        fw1 = os.path.join(tmp, "w1")
        fcw = os.path.join(tmp, "cw")
        fset = os.path.join(tmp, "set")
        fmain = os.path.join(tmp, "main")
        roots_file = os.path.join(tmp, "roots.json")
        with io.open(roots_file, "w", encoding="utf-8") as fh:
            json.dump({"rq": frq, "w1": fw1, "cw": fcw, "set": fset,
                       "main": fmain}, fh)
        base = {
            "rq/scan/mac_stmt_scan.py": "scan-A\n",
            "w1/scan/mac_stmt_scan.py": "scan-A\n",
            "rq/names/mac_stmt_names.py": "names-A\n",
            "rq/verify/gate4_comment_guard.py": "gate4-A\n",
            "set/scripts/gates/gate4_comment_guard.py": "gate4-A\n",
            "rq/tools/cpu_guard.sh": "guard-A\n",
            "cw/cpu_guard.sh": "guard-A\n",
            "rq/wash/wash_engine.py": "wash-A\n",
            "rq/verify/verify_vo.py": "vo-A\n",
            "rq/seam/seam_probe.py": "seam-A\n",
            "rq/certify/freeze_manifest.py": "fm-A\n",
        }
        relmap = {
            "rq/scan/mac_stmt_scan.py": (frq, "scan/mac_stmt_scan.py"),
            "w1/scan/mac_stmt_scan.py": (fw1, "scan/mac_stmt_scan.py"),
            "rq/names/mac_stmt_names.py": (frq, "names/mac_stmt_names.py"),
            "rq/verify/gate4_comment_guard.py": (frq, "verify/gate4_comment_guard.py"),
            "set/scripts/gates/gate4_comment_guard.py": (fset, "scripts/gates/gate4_comment_guard.py"),
            "rq/tools/cpu_guard.sh": (frq, "tools/cpu_guard.sh"),
            "cw/cpu_guard.sh": (fcw, "cpu_guard.sh"),
            "rq/wash/wash_engine.py": (frq, "wash/wash_engine.py"),
            "rq/verify/verify_vo.py": (frq, "verify/verify_vo.py"),
            "rq/seam/seam_probe.py": (frq, "seam/seam_probe.py"),
            "rq/certify/freeze_manifest.py": (frq, "certify/freeze_manifest.py"),
        }
        for key, content in base.items():
            root, rel = relmap[key]
            w(root, rel, content)
        # audit 域：main 正本＝第二家族（DIVERGED·只录不判）
        w(fmain, "scripts/gates/gate4_comment_guard.py", "gate4-B\r\n")
        # 夹具须能过冻结同侪 import（roots-file 模式下 certify 仍取真仓——真仓在卷）

        def run(argv):
            import subprocess
            p = subprocess.run([sys.executable, "-B", me] + argv,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))

        # 判① 全等盘面 freeze→0·名单口径咬合·幂等重放
        lst = os.path.join(tmp, "q.json")
        side = os.path.join(tmp, "q.t2")
        rc, so, se = run(["freeze", "--out", lst, "--tier2", side,
                          "--roots-file", roots_file])
        assert rc == 0, "判① freeze 应 0 实测 %d\n%s%s" % (rc, so, se)
        doc = json.load(io.open(lst, encoding="utf-8"))
        assert doc["n_copies"] == 11, "判① 名单副本数应 11 实测 %r" % doc["n_copies"]
        first = open(lst, "rb").read()
        rc, so, se = run(["freeze", "--out", lst, "--roots-file", roots_file])
        assert rc == 0 and open(lst, "rb").read() == first, "判① 幂等失守"
        print("判① 全等盘面 freeze PASS: 11 副本入册·幂等重放逐字节恒同")

        # 判② 零漂移 check→0·群全等·audit DIVERGED 只录不判
        led = os.path.join(tmp, "q_ledger.txt")
        rc, so, se = run(["check", "--list", lst, "--tier2", side,
                          "--roots-file", roots_file, "--ledger", led])
        assert rc == 0, "判② 零漂移 check 应 0 实测 %d\n%s%s" % (rc, so, se)
        led_text = io.open(led, encoding="utf-8").read()
        assert led_text.count("\nOK ") == 11 and "GROUP scan/mac_stmt_scan.py copies=2 distinct=1 UNIFORM" in led_text, led_text
        assert "AUDIT-DIVERGED" in led_text and "main" in led_text, \
            "判② audit DIVERGED 应只录入名单（不判非零）"
        assert led_text.count("AUDIT-DIVERGED") == 1, led_text
        print("判② 零漂移 check PASS: rc=0·11 OK·群 UNIFORM·audit 第二家族只录不判")

        # 判③ 副本群漂移：w1 scan 改字节→freeze 拒出 rc1·check 群漂移 rc1
        w(fw1, "scan/mac_stmt_scan.py", "scan-B\n")
        rc, so, se = run(["freeze", "--out", os.path.join(tmp, "x.json"),
                          "--roots-file", roots_file])
        assert rc == 1 and "副本群今日非全等" in so, \
            "判③ freeze 应拒漂移名单 rc1 实测 %d\n%s%s" % (rc, so, se)
        rc, so, se = run(["check", "--list", lst, "--roots-file", roots_file])
        assert rc == 1 and "MISMATCH w1/scan/mac_stmt_scan.py" in so \
            and "GROUP scan/mac_stmt_scan.py copies=2 distinct=2 DIVERGED" in so, \
            "判③ check 应现形群漂移 rc1\n%s%s" % (rc, so, se)
        w(fw1, "scan/mac_stmt_scan.py", "scan-A\n")
        print("判③ 副本群漂移现形 PASS: freeze 拒出 rc1·check MISMATCH+GROUP-DIVERGED rc1")

        # 判④ 在册外副本扫出：rq/tmp_extra/mac_stmt_scan.py→UNREGISTERED rc1
        w(frq, "tmp_extra/mac_stmt_scan.py", "scan-A\n")
        rc, so, se = run(["check", "--list", lst, "--roots-file", roots_file])
        assert rc == 1 and "UNREGISTERED" in so and "tmp_extra" in so, \
            "判④ UNREGISTERED 应现形 rc1\n%s%s" % (rc, so, se)
        shutil.rmtree(os.path.join(frq, "tmp_extra"))
        print("判④ 在册外副本扫出 PASS: 同名件出在册位即 UNREGISTERED rc1")

        # 判⑤ 名单篡改→tier2 FAIL rc1；侧册篡改→咬合 FAIL rc1；副本缺失→MISSING rc1
        bad = json.load(io.open(lst, encoding="utf-8"))
        bad["tier1"][0][1] = "0" * 32
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        rc, so, se = run(["check", "--list", bad_path, "--roots-file", roots_file])
        assert rc == 1 and "名单 tier2 自洽（名单未被改）: FAIL" in so, so
        side_bad = os.path.join(tmp, "side_bad.t2")
        with io.open(side_bad, "w", encoding="utf-8") as fh:
            fh.write("0" * 32 + "\n")
        rc, so, se = run(["check", "--list", lst, "--tier2", side_bad,
                          "--roots-file", roots_file])
        assert rc == 1 and "tier2 侧册咬合: FAIL" in so, so
        os.remove(os.path.join(fw1, "scan", "mac_stmt_scan.py"))
        rc, so, se = run(["check", "--list", lst, "--roots-file", roots_file])
        assert rc == 1 and "MISSING w1/scan/mac_stmt_scan.py" in so, so
        print("判⑤ 篡改/侧册/缺失现形 PASS: tier2 FAIL rc1·咬合 FAIL rc1·MISSING rc1")

        print("QUAD8-SELFTEST PASS: 夹具八判绿（freeze 咬合幂等/零漂移+audit 只录/"
              "群漂移现形/UNREGISTERED 扫出/tier2·侧册·缺失三现形）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- CLI ----------------

def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="四仓同 md5 副本群对账名单机检（freeze_manifest 两层机制·"
                    "world_md5_assert 同款断言法）")
    sub = ap.add_subparsers(dest="cmd")
    fz = sub.add_parser("freeze", help="副本群全等方出对账名单（漂移/缺失拒出）")
    fz.add_argument("--out", default=None, help="名单出路径")
    fz.add_argument("--tier2", default=None, help="tier2 侧册出路径（可省）")
    fz.add_argument("--roots-file", default=None, help="slug→root JSON 覆盖（夹具用）")
    ck = sub.add_parser("check", help="六环咬合对账＋audit 只录＋名单出账")
    ck.add_argument("--list", default=None, help="在册对账名单路径")
    ck.add_argument("--tier2", default=None, help="tier2 侧册（可省·给了就咬合）")
    ck.add_argument("--ledger", default=None, help="对账名单出账路径（world 断言行式）")
    ck.add_argument("--json", default=None, help="对账账目 JSON 出账路径")
    ck.add_argument("--roots-file", default=None, help="slug→root JSON 覆盖（夹具用）")
    ap.add_argument("--registry", action="store_true",
                    help="打印在册副本表（slug/rel·md5 位由 check/freeze 实测出账）")
    ap.add_argument("--selftest", action="store_true", help="夹具八判自证（零触真仓）")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    if args.registry:
        for comp, copies in REGISTRY:
            for slug, rel in copies:
                print("%s/%s  （组件 %s）" % (slug, rel, comp))
        sys.exit(0)
    # Clean mode: freeze/check audit the registered canonical copy groups;
    # report and refuse unless fixture roots are supplied via --roots-file.
    if args.cmd in ("freeze", "check") and not args.roots_file and _clean_mode():
        print("requires canonical environment: the registered four-repo "
              "canonical copy groups (fixture roots stay available via "
              "--roots-file)")
        sys.exit(9)
    if args.cmd == "freeze":
        cmd_freeze(args)
    elif args.cmd == "check":
        cmd_check(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
