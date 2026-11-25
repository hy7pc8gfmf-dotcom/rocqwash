#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_world_hook.py — selftest for `wash/world_hook.py` (rocqwash tests/).

Purpose.  The world born into a sanitize run must equal the RUNTREE certified-generation copy;
  a self-carried stale generation is forbidden.  This face reproduces the recorded failure case
  (ASSERT4 in `sandbox/seat_nw5ver/账/world_md5_assert_npw.txt`: a self-carried world copy
  differing from the tree copy by WDIFF x14 / WMISS x2) as five suite-level checks, a parallel
  witness to the tool's --selftest:
  1 selftest — the tool --selftest twelve vectors pass (rc 0)
  2 stale-world neg — skewed world (stale-generation .vo) + engine passthrough -> rc 9, WDIFF
    on stdout, --out never written (the pre-born assertion intercepts; the engine never runs)
  3 WMISS neg — a certified base file missing -> rc 9, WMISS on stdout
  4 pos passthrough — certified-generation world (fixture anchors re-measured) -> rc 0, the
    engine runs, the artifact lands
  5 frozen side-evidence — md5 of `wash/wash_engine.py` equals the frozen record
    b06bd886d4e47bb9cd2be1dd4e857e81 (read-only reuse; zero bytes touched)

Interface.  python3 tests/test_world_hook.py; no flags; drives the hook via subprocess
  (sys.executable -B) and asserts on exit codes, stdout tokens (PASS, WDIFF, WMISS,
  WORLD-BASE-OK) and on-disk effects.

Dependencies.  Python 3 standard library only (hashlib, io, json, os, shutil, subprocess, sys,
  tempfile); writes only under a mkdtemp directory removed in a finally block; zero repository
  writes, zero compile, zero network; deterministic.

Evidence.  Five named checks with the name and detail printed on failure; the TEST-WORLD-HOOK
  PASS line is the conclusion; roster row: `t_world_hook` (tests/run_tests.sh, README row 26);
  the tool's --selftest is the parallel witness (check 1).

Exit-codes.  0 = all five checks passing; 1 = any check failing.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, "wash", "world_hook.py")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "b06bd886d4e47bb9cd2be1dd4e857e81"  # frozen record in `更新账.md` §3

ANCHOR_NAMES = ["S01_BaseRing", "S02_CauchyComplete", "S03_QExp",
                "UpReqLpoEquiv", "EntropyUnsatMark"]


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    p = subprocess.run([sys.executable, "-B", HOOK] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
    return p


def make_world(root, stale_first=False):
    """Fixture world: one .vo per anchor name; with stale_first=True the first file gets
    stale-generation content."""
    world = os.path.join(root, "world")
    os.makedirs(world)
    mds = {}
    for k, name in enumerate(sorted(ANCHOR_NAMES)):
        content = b"OLD-GEN-VO\n" if (stale_first and k == 0) else ("VO-%02d-%s\n" % (k, name)).encode()
        with io.open(os.path.join(world, name + ".vo"), "wb") as fh:
            fh.write(content)
        mds[name] = md5_of(os.path.join(world, name + ".vo"))
    return world, mds


def make_ledger(root):
    src_v = os.path.join(root, "vec.v")
    with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
        fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
    ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                           "old": "Lemma vec_a : forall x : nat, x = x.\n",
                           "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
    lp = os.path.join(root, "ledger.json")
    with io.open(lp, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh)
    return src_v, lp


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_tworldhook_")
    try:
        # 1: the tool's own selftest
        p = run(["--selftest"])
        check("selftest", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])

        # 2: stale-world neg — the pre-born assertion intercepts; the engine writes nothing
        stale_root = os.path.join(tmp, "stale")
        os.makedirs(stale_root)
        world_s, _ = make_world(stale_root, stale_first=True)
        src_v, lp = make_ledger(stale_root)
        out_v = os.path.join(stale_root, "vec_washed.v")
        fresh_root = os.path.join(tmp, "fresh")
        os.makedirs(fresh_root)
        world_f, mds = make_world(fresh_root)
        # certified-generation anchor manifest (suite fixture; world_md5_assert.txt table
        # form; re-measured against the fresh world)
        man = os.path.join(stale_root, "man.txt")
        with io.open(man, "w", encoding="utf-8") as fh:
            for n in sorted(mds):
                fh.write("%s  %s.vo  OK\n" % (mds[n], n))
        p = run(["--world", world_s, "--manifest", man, "--",
                 "--file", src_v, "--patch", lp, "--out", out_v])
        check("stale_world_WDIFF_neg", p.returncode == 9 and "WDIFF" in p.stdout
              and not os.path.exists(out_v),
              "rc=%d out_exists=%s" % (p.returncode, os.path.exists(out_v)))

        # 3: WMISS neg
        p = run(["--world", world_f, "--anchor", "Absent_Mod=%s" % ("0" * 32)])
        check("WMISS_neg", p.returncode == 9 and "WMISS" in p.stdout,
              "rc=%d" % p.returncode)

        # 4: pos — certified-generation world + engine passthrough -> rc 0, artifact lands
        out_v2 = os.path.join(fresh_root, "vec_washed.v")
        p = run(["--world", world_f, "--manifest", man, "--",
                 "--file", src_v, "--patch", lp, "--out", out_v2])
        check("pos_passthrough", p.returncode == 0 and os.path.isfile(out_v2)
              and "WORLD-BASE-OK" in p.stdout, "rc=%d" % p.returncode)

        # 5: frozen side-evidence — the engine md5 still equals the frozen record
        check("frozen_engine_untouched", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-22s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-WORLD-HOOK FAIL: %d/%d failing" % (len(fails), len(checks)))
            return 1
        print("TEST-WORLD-HOOK PASS: selftest / stale-world WDIFF neg / WMISS neg / "
              "pos passthrough / frozen side-evidence — all five checks passed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
