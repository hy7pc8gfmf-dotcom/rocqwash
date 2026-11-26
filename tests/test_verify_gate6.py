#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verify_gate6.py — verify/verify_gate6.py 自测（tests/·五课反馈轮·agent rqsupport·
Purpose.  Self-test for verify/verify_gate6.py: the bare-Prop quantifier census gate on the EntropyUnsatMark case (five-lesson fixture arc, gate6 ch1).
Interface.  Direct run (python tests/test_verify_gate6.py); the before/after case-report pair plus the fixture-tree census face over the sample fixture.
Dependencies.  Python 3 standard library only; the sibling verify/verify_gate6.py and its report faces.
Evidence.  Each check asserts its verdict and prints it; the runner exits nonzero on the first failed check.
Exit-codes.  0 all checks pass; 1 at least one check failed.

20261101）

五课夹具④【gate6 ch1】：语句面裸 Prop 量词 census（EntropyUnsatMark 判例）。
判例源：seat_eum/账/gate6_report_before.json（ch1=1·L135
eum_EntropyDiffReal_section_vacuous）→ gate6_report_after.json（ch1=0·names 5=5）。

  1 自证        工具 --selftest 十判全过（rc 0）
  2 判例正判    eum before(ch1=1)→after(ch1=0·名 5=5) → GREEN rc 0
  3 ch1 滞治负例 before→before（治而未降）→ RED rc 1
  4 薄调正判    --tree 指向 fixtures 夹具树 → 经正本 census 真跑 rc 0
                （fixtures/gate6_ch1_sample.v＝eum L135 病面同形夹具·正本只读扫描）
  5 缺件负例    --judge-* 单翼 → rc 2

幂等：临时目录即写即清·正本仓只读零 __pycache__（python3 -B）·零网络。
退出码：0=五判全过；1=任一红。
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE6 = os.path.join(REPO, "verify", "verify_gate6.py")

EUM_NAMES = ["fa52_EDP_E_B_pos_unsat", "fa52_EntropyDiffReal_premises_unsat",
             "eum_E_B_pos_slot_unsat_ref", "eum_premises_unsat_ref",
             "eum_EntropyDiffReal_section_vacuous"]
EUM_CH1_HIT = {"line": 135, "cmd": "Theorem", "name": "eum_EntropyDiffReal_section_vacuous",
               "excerpt": "Theorem eum_EntropyDiffReal_section_vacuous : forall (Omega_A : "
                          "forall (E_A : Real), real_lt real_zero E_A -> Real) -> Real"}


def run(args):
    p = subprocess.run([sys.executable, "-B", GATE6] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def eum_report(ch1_hits):
    return {"summary": {"files": 1,
                        "totals": {"ch1": len(ch1_hits), "ch2": 0, "ch3": 0},
                        "statement_names": len(EUM_NAMES)},
            "files": {"EntropyUnsatMark.v": {"ch1": ch1_hits, "ch2": [], "ch3": [],
                                             "names": list(EUM_NAMES)}}}


def wf(tmp, name, obj_or_text):
    fp = os.path.join(tmp, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        if isinstance(obj_or_text, str):
            fh.write(obj_or_text)
        else:
            json.dump(obj_or_text, fh)
    return fp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tverifygate6_")
    try:
        # 1 工具自证
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2【gate6 ch1 判例正判】
        jb = wf(tmp, "before.json", eum_report([EUM_CH1_HIT]))
        ja = wf(tmp, "after.json", eum_report([]))
        p = run(["--judge-before", jb, "--judge-after", ja])
        check("eum_判例正判", p.returncode == 0 and "EUM-VERDICT-GREEN" in p.stdout,
              "rc=%d" % p.returncode)

        # 3 ch1 滞治负例：before→before
        p = run(["--judge-before", jb, "--judge-after", jb])
        check("ch1_滞治负例", p.returncode == 1 and "ch1-must-drop" in p.stdout,
              "rc=%d" % p.returncode)

        # 4 薄调正判：正本真扫 fixtures 夹具树（eum 病面同形→ch1 词面命中）
        #   census ch1＝语句面 \bProp\b 词面预筛（正本 PROP_WORD 口径）——夹具按
        #   eum L135 同病形给「语句面裸 Prop 量词」。
        tree = os.path.join(tmp, "tree")
        os.makedirs(tree)
        with io.open(os.path.join(tree, "gate6_ch1_sample.v"), "w", encoding="utf-8") as fh:
            fh.write("Theorem sample_vacuous : forall (Omega_A : Prop), Omega_A -> False.\n"
                     "Proof. intros. exact I. Qed.\n")
        jout = os.path.join(tmp, "census.json")
        p = run(["--tree", tree, "--json", jout])
        ok4 = p.returncode == 0 and "GATE6-CENSUS" in p.stdout and os.path.isfile(jout)
        if ok4:
            with io.open(jout, encoding="utf-8") as fh:
                rep = json.load(fh)
            ok4 = rep["summary"]["totals"]["ch1"] >= 1
        check("薄调正判_正本真扫", ok4, "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # 5 缺件负例：judge 单翼
        p = run(["--judge-before", jb])
        check("judge单翼_负例", p.returncode == 2, "rc=%d" % p.returncode)

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-18s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-VERIFY-GATE6 FAIL: %d/%d 红" % (len(fails), len(checks)))
            return 1
        print("TEST-VERIFY-GATE6 PASS: selftest/eum判例正判/ch1滞治负例/薄调正判/"
              "单翼负例 五判全过（五课夹具④gate6 ch1·EntropyUnsatMark 判例）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
