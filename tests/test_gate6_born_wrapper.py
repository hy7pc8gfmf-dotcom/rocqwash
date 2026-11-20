#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gate6_born_wrapper.py — selftest for wrapper/gate6_census.sh and
wrapper/born_world.sh (tests/; 21 subprocess judges, positive/negative
pairs first).

Purpose.  Exercises both wrapper scripts through their real CLI contracts
  by subprocess: exit codes (0/2/9), usage faces, missing inputs, order/
  module mutual exclusion, md5-manifest assertions, and the zero-write
  --dry-run canonical forms.
Interface.  Invokes `wrapper/gate6_census.sh` (bash -n, -h, --bogus,
  --tree, --gate, --baseline, --dry-run, GATE6_CENSUS_SCRIPT override)
  and `wrapper/born_world.sh` (bash -n, -h, --bogus, --world, --module,
  --order, --runtree, --dry-run, --assert-md5); each judge prints
  "judge<n> <desc>: PASS|FAIL" and asserts exit codes plus verbatim
  stderr markers of the scripts' output.
Dependencies.  bash 3.2-compatible scripts plus Python 3 standard library
  only; every fixture lives in a tempfile directory cleaned in finally;
  neither canonical wrapper is touched and no agent domain is entered;
  rocq/guard binaries are never actually invoked (every fail-loud path
  fires before any compilation step).
Evidence.  The full judge roster with per-judge expectations is the
  extended contract comment below; judges 9 and 18 additionally assert
  the stage snapshot is unchanged behind the dry runs (zero writes),
  judges 17 and 20 assert no .vo product exists after the rc 9 paths,
  judge 19 asserts the order dry run lists exactly A.v and B.v from a
  commented order file, and judge 21 asserts the manifest refusal on
  .vo-only lines.
Exit-codes.  0 = all 21 judges pass; 1 = any judge failed (printed as
  judge<n> ... FAIL).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  Judge roster,
# positive/negative pairs first, zero compilation / zero network / zero
# repository writes, temp stage written and cleaned per case:
#   wrapper/gate6_census.sh:
#    1 syntax              bash -n -> rc 0
#    2 help                -h -> rc 0 with the usage header
#    3 unknown arg         --bogus -> rc 2
#    4 missing --tree      -> rc 2
#    5 tree missing        --tree <missing> -> rc 9
#    6 script missing      GATE6_CENSUS_SCRIPT=<missing> --tree <tmp> -> rc 9
#    7 gate no baseline    --gate without --baseline -> rc 2 (fail-loud
#                          precondition, same rule as the GATE6-USAGE face)
#    8 baseline missing    --baseline <missing> -> rc 9
#    9 --dry-run           -> rc 0; stdout carries the guard-knob canonical
#                          form plus python3 -B plus --tree pass-through
#                          (zero writes: no new file in the stage afterwards)
#   wrapper/born_world.sh:
#   10 syntax              bash -n -> rc 0
#   11 help                -h -> rc 0 with the usage header
#   12 unknown arg         --bogus -> rc 2
#   13 missing --world     -> rc 2
#   14 order/module both given (ambiguous) -> rc 2
#   15 runtree missing     --runtree <missing> --world <tmp> --module A -> rc 9
#   16 module with path    --module sub/A -> rc 2
#   17 source missing      no A.v under runtree (the dry-run precondition
#                          passes, the copy step fails loud) -> rc 9
#   18 --dry-run           -> rc 0; stdout carries BORN-WORLD-DRYRUN plus the
#                          guard-knob canonical form plus the `-Q . ""` form
#                          (zero writes)
#   19 order stripping     order-file comments and blank lines -> the dry run
#                          lists only the valid names
#   20 md5 mismatch        --assert-md5 with a wrong-value manifest -> rc 9
#                          with the assertion-failure marker on stderr and
#                          zero compile products (no .vo in the world)
#   21 manifest .v-only    a .vo-only manifest line -> rc 9 with the
#                          missing-source-line marker
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(REPO, "wrapper", "gate6_census.sh")
BORN = os.path.join(REPO, "wrapper", "born_world.sh")
MISSING = os.path.join(os.sep, "tmp", "rqadapt_nonexistent_gate6_born_target")


def sh(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def snapshot(d):
    out = []
    for root, _dirs, files in os.walk(d):
        out.extend(os.path.join(root, f) for f in files)
    return sorted(out)


def main():
    ok = True
    tmp = tempfile.mkdtemp(prefix="rqadapt_g6born_")
    try:
        def judge(n, desc, cond, detail=""):
            nonlocal ok
            print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                         ("" if cond else "  " + detail)))
            ok = ok and cond

        tree_tmp = os.path.join(tmp, "tree"); os.makedirs(tree_tmp)

        # ---------- gate6_census.sh ----------
        rc, out, err = sh(["bash", "-n", CENSUS])
        judge(1, "census 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", CENSUS, "-h"])
        judge(2, "census -h 用法面", rc == 0 and "gate6" in out and "用法 Usage" in out,
              "rc=%s out[:80]=%r" % (rc, out[:80]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--bogus"])
        judge(3, "census 未知形参 rc=2", rc == 2 and "未知形参" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS])
        judge(4, "census 缺 --tree rc=2", rc == 2 and "--tree" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", MISSING])
        judge(5, "census tree 缺失 rc=9", rc == 9 and "目录缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp],
                          env={"GATE6_CENSUS_SCRIPT": MISSING})
        judge(6, "census gate6 正本缺失 rc=9", rc == 9 and "gate6 正本缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--gate"])
        judge(7, "census --gate 无 --baseline rc=2", rc == 2 and "--baseline" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--baseline", MISSING])
        judge(8, "census baseline 缺失 rc=9", rc == 9 and "baseline 文件缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        before = snapshot(tmp)
        rc, out, err = sh(["bash", CENSUS, "--tree", tree_tmp, "--dry-run"])
        judge(9, "census --dry-run 正典形出账·零写盘",
              rc == 0 and "GATE6-CENSUS-DRYRUN" in out and "python3 -B" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out and snapshot(tmp) == before,
              "rc=%s out[:200]=%r" % (rc, out[:200]))

        # ---------- born_world.sh ----------
        rc, out, err = sh(["bash", "-n", BORN])
        judge(10, "born 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", BORN, "-h"])
        judge(11, "born -h 用法面", rc == 0 and "born_world" in out and "Interface." in out,
              "rc=%s out[:80]=%r" % (rc, out[:80]))

        rc, out, err = sh(["bash", BORN, "--bogus"])
        judge(12, "born 未知形参 rc=2", rc == 2 and "未知形参" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--module", "A"])
        judge(13, "born 缺 --world rc=2", rc == 2 and "--world" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--world", os.path.join(tmp, "w"),
                           "--module", "A", "--order", MISSING])
        judge(14, "born order/module 同给 rc=2", rc == 2 and "不得同给" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", MISSING,
                           "--world", os.path.join(tmp, "w"), "--module", "A"])
        judge(15, "born runtree 缺失 rc=9", rc == 9 and "源树缺失" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp,
                           "--world", os.path.join(tmp, "w"), "--module", "sub/A"])
        judge(16, "born 模块名带路径 rc=2", rc == 2 and "不合法" in err,
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp,
                           "--world", os.path.join(tmp, "w"), "--module", "A"])
        judge(17, "born 源缺失 rc=9（fail-loud 先于编译）",
              rc == 9 and "认证代源缺失" in err
              and not [f for f in snapshot(tmp) if f.endswith(".vo")],
              "rc=%s err[:120]=%r" % (rc, err[:120]))

        world18 = os.path.join(tmp, "w18")
        before = snapshot(tmp)
        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp, "--world", world18,
                           "--module", "A", "--dry-run"])
        judge(18, "born --dry-run 正形出账·零写盘",
              rc == 0 and "BORN-WORLD-DRYRUN" in out and "-Q . \"\"" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out and snapshot(tmp) == before,
              "rc=%s out[:200]=%r" % (rc, out[:200]))

        orderf = os.path.join(tmp, "order.txt")
        with open(orderf, "w", encoding="utf-8") as fh:
            fh.write("# 依赖序注释行\n\nA\n  B  \n# 尾注释\n")
        rc, out, err = sh(["bash", BORN, "--runtree", tree_tmp, "--world", world18,
                           "--order", orderf, "--dry-run"])
        listed = [ln for ln in out.splitlines() if "cp:" in ln]
        names = [ln.rsplit("/", 1)[-1].split(" ")[0] for ln in listed]
        judge(19, "born order 注释/空白剥离",
              rc == 0 and names == ["A.v", "B.v"],
              "rc=%s names=%r out[:300]=%r" % (rc, names, out[:300]))

        runtree20 = os.path.join(tmp, "rt20"); os.makedirs(runtree20)
        with open(os.path.join(runtree20, "A.v"), "w", encoding="utf-8") as fh:
            fh.write("Definition a := 1.\n")
        badman = os.path.join(tmp, "bad.md5")
        with open(badman, "w", encoding="utf-8") as fh:
            fh.write("00000000000000000000000000000000  A.v\n")
        world20 = os.path.join(tmp, "w20")
        rc, out, err = sh(["bash", BORN, "--runtree", runtree20, "--world", world20,
                           "--module", "A", "--assert-md5", badman])
        judge(20, "born 代际雷 md5 败 rc=9·零产物",
              rc == 9 and "代际断言败" in err
              and not [f for f in snapshot(tmp) if f.endswith(".vo")],
              "rc=%s err[:160]=%r" % (rc, err[:160]))

        voman = os.path.join(tmp, "vo_only.md5")
        with open(voman, "w", encoding="utf-8") as fh:
            fh.write("00000000000000000000000000000000  A.vo  OK\n")
        world21 = os.path.join(tmp, "w21")
        rc, out, err = sh(["bash", BORN, "--runtree", runtree20, "--world", world21,
                           "--module", "A", "--assert-md5", voman])
        judge(21, "born manifest 只认 .v 源行（.vo 账不哑比）",
              rc == 9 and "源断言行" in err,
              "rc=%s err[:160]=%r" % (rc, err[:160]))

        print("== test_gate6_born_wrapper: %s ==" % ("ALL PASS" if ok else "RED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
