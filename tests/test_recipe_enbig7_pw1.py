#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_recipe_enbig7_pw1.py — selftest for the recipe face
recipes/ENBIG7_same_domain_collision_PW1.md (rocqwash tests/; five checks,
precedent-anchored; check roster in the extended contract comment below).

Purpose.  Guard the ENBIG7 same-domain-collision recipe (PW1) in the tree:
  the recipe face must stay present with its precedent anchor word face
  complete, the collision-precursor machine check must keep failing a
  duplicate module claim, and the world base assertions must keep their
  judgment on the private-world rebuild — a substituted world intercepted,
  a certified-generation world passing with the pass-through engine really
  running — with the frozen engine md5 re-asserted against the registered
  value.

Interface.  python3 -B tests/test_recipe_enbig7_pw1.py; suite lane
  `t_recipe_pw1` (tests/run_tests.sh).

Dependencies.  Python 3 standard library only; zero network, zero
  compilation, zero repository writes; fixtures live in a mkdtemp directory
  removed in finally; the world base assertions are a pure md5 differential
  comparison; the frozen engine is imported read-only.

Evidence.  The guarded recipe face documents the dver2-enbig7 same-domain
  collision: arbitration 36c35816; 25/25 md5 assertions; 24 chain pieces
  born rc=0; three zero-tampering re-assertions; documented November 1,
  2026, by agent `rqsup4` (the inspection polish round).  RECIPE_ANCHORS
  moves in lockstep with the recipe face (the anchor-must-move rule).

Exit-codes.  0 = all five checks pass; 1 = any check failing.
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  The five checks,
# in execution order:
#   1 recipe present + RECIPE_ANCHORS anchor word face complete
#   2 precursor negative (the enbig7 precedent shape): the same module name
#     in two selection lists fails DUP-CROSS rc 1 (collision-precursor
#     machine check, tools/select_audit.py)
#   3 world-skew negative (the invasion-substitution shape): a fixture .vo
#     substituted against its certified-generation anchor reports WDIFF
#     rc 9 and the sanitize engine never runs, zero writes (wash/world_hook.py
#     pass-through form)
#   4 cured-face positive (the private-world-rebuilt shape): a fixture world
#     md5-equal to its certified-generation anchors passes WORLD-BASE-OK
#     rc 0 and the pass-through engine really runs and writes (anchors =
#     current-snapshot md5; the anchor-must-move rule in mechanical form)
#   5 frozen collateral: wash/wash_engine.py md5 equals the registered
#     frozen value eed0699a... (read-only import, zero touch)
# Idempotence: the temp directory is written and cleaned in the same run;
# zero repository writes, zero compilation, zero network.
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPE = os.path.join(REPO, "recipes", "ENBIG7_same_domain_collision_PW1.md")
HOOK = os.path.join(REPO, "wash", "world_hook.py")
AUDIT = os.path.join(REPO, "tools", "select_audit.py")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "b06bd886d4e47bb9cd2be1dd4e857e81"  # registered frozen value (`更新账.md` section 3)

RECIPE_ANCHORS = [
    "PW1", "collision_enbig7_20261031", "36c35816",
    "wait for quiet", "full re-audit", "私占世界", "chain order",
    "three re-assertions", "never adopted", "anchor must move",
    "world_hook", "select_audit", "DUP-CROSS",
]


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv):
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_trecipepw1_")
    try:
        # check 1: recipe present + anchor word face complete
        ok1 = os.path.isfile(RECIPE)
        missing = []
        if ok1:
            with io.open(RECIPE, encoding="utf-8") as fh:
                doc = fh.read()
            missing = [a for a in RECIPE_ANCHORS if a not in doc]
            ok1 = not missing
        else:
            missing = ["<处方件整缺>"]
        check("处方件锚词面", ok1, "missing=%s" % missing)

        # check 2 (precursor negative, the enbig7 precedent shape): the same
        # piece claimed twice -> DUP-CROSS failing rc 1
        order = os.path.join(tmp, "order.txt")
        with io.open(order, "w", encoding="utf-8") as fh:
            fh.write("S03_QExp.v#R0-d66910\nDver2_Target.v#R28-f09c39\n")
        b1 = os.path.join(tmp, "b_dver2.txt")
        b2 = os.path.join(tmp, "b_enbig7.txt")
        with io.open(b1, "w", encoding="utf-8") as fh:
            fh.write("Dver2_Target.v\n")  # the dver2 agent's selection
        with io.open(b2, "w", encoding="utf-8") as fh:
            fh.write("Dver2_Target.v\n")  # the enbig7 agent claims the same piece (out-of-bounds precursor)
        p = run([sys.executable, "-B", AUDIT, "--order", order,
                 "--select", b1, "--select", b2])
        check("前兆负例_DUP-CROSS", p.returncode == 1 and "DUP-CROSS" in p.stdout,
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # shared fixtures for checks 3/4: the private world (five anchors
        # snapshotted = certified generation; the five world_hook
        # BUILTIN_ANCHORS names) and the invaded world (same table, S01
        # replaced by a stale-generation body, the other four anchors unchanged)
        src_v = os.path.join(tmp, "vec.v")
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
        ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                               "old": "Lemma vec_a : forall x : nat, x = x.\n",
                               "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)

        ANCHOR_NAMES = ["EntropyUnsatMark", "S01_BaseRing", "S02_CauchyComplete",
                        "S03_QExp", "UpReqLpoEquiv"]  # the five world_hook BUILTIN_ANCHORS names
        world = os.path.join(tmp, "world_pw1")      # private-world-rebuilt shape: five anchors snapshotted = certified generation
        os.makedirs(world)
        anchor_args = []
        for k, name in enumerate(sorted(ANCHOR_NAMES)):
            with io.open(os.path.join(world, name + ".vo"), "wb") as fh:
                fh.write(("CERTIFIED-GEN-VO-%02d-%s\n" % (k, name)).encode())
            anchor_args += ["--anchor", "%s=%s" % (name, md5_of(os.path.join(world, name + ".vo")))]

        world_inv = os.path.join(tmp, "world_invaded")  # invasion-substitution shape: S01 replaced by its stale-generation body
        os.makedirs(world_inv)
        for name in sorted(ANCHOR_NAMES):
            body = b"INVADER-STALE-VO\n" if name == "S01_BaseRing" \
                else open(os.path.join(world, name + ".vo"), "rb").read()
            with io.open(os.path.join(world_inv, name + ".vo"), "wb") as fh:
                fh.write(body)

        out_v = os.path.join(tmp, "vec_washed.v")

        # check 3 (world-skew negative, the invasion-substitution shape): the
        # wrong-generation world -> S01 WDIFF rc 9, engine not run, zero writes
        p = run([sys.executable, "-B", HOOK, "--world", world_inv]
                + anchor_args + ["--",
                                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        check("偏斜负例_WDIFF拦截",
              p.returncode == 9 and "WDIFF" in p.stdout and not os.path.exists(out_v),
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # check 4 (cured-face positive, the private-world-rebuilt shape): the
        # certified-generation world -> WORLD-BASE-OK, the pass-through engine really runs
        p = run([sys.executable, "-B", HOOK, "--world", world]
                + anchor_args + ["--",
                                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        check("愈面正判_WORLD-BASE-OK",
              p.returncode == 0 and "WORLD-BASE-OK" in p.stdout
              and os.path.isfile(out_v),
              "rc=%d out=%s" % (p.returncode, p.stdout[:200]))

        # check 5 (frozen collateral): engine md5 still equals the registered
        # frozen value (read-only import, zero touch)
        check("冻结件零触", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-22s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-RECIPE-PW1 FAIL: %d/%d failing" % (len(fails), len(checks)))
            return 1
        print("TEST-RECIPE-PW1 PASS: recipe anchors / precursor DUP-CROSS / skew "
              "WDIFF interception / cured WORLD-BASE-OK / frozen collateral — all "
              "five checks pass (lesson 3 of the five-lesson ledger: same-domain "
              "collision private-world rebuild PW1)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
