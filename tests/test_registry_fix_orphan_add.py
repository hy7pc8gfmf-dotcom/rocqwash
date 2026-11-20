#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_fix_orphan_add.py — ORPHAN-ADD apply-path tests for tools/registry_fix.py (rocqwash tests/).

Purpose.  Pin the ORPHAN-ADD apply path behind the opt-in flag --orphan-add: registry_audit --fix-plan
  emits ORPHAN-ADD prescriptions in two directions.  order-only prescriptions are mechanically solvable
  (placeholder-free template, "X.v" or "Sub/X.v"; _CoqProject rows carry no anchor) and are the apply path
  under test; project-only prescriptions embed "#R<SEQ>-<MD5_8>" sequence placeholders (a registry-side
  decision; mechanical anchor fabrication is forbidden by the tool contract) and stay on the skip list under
  any flag.  A paired ".v.v" suffix-twin key would double-register the module and is skipped as
  ORPHAN-ADD-SKIP-SUFFIX-TWIN for human adjudication.  Checks: 1 default-off parity (frozen legacy classes
  untouched); 2 dry run under the flag (rc=0, zero write, the order-only prescription staged, project-only
  stays skipped); 3 apply under the flag (rc=0, all assertions PASS including orphan resolution, exactly one
  appended tail row, order book bytes identical to the flag-off run); 4 project-only stays non-mechanical;
  5 suffix-twin guard (no row appended for the twin); 6 blast injection (rc=2, rollback restores both books
  byte-for-byte); 7 stale-prescription guards (a coqproject row already hashing to the key ->
  ORPHAN-ADD-SKIP-KEY-PRESENT; a key missing from the order book -> staging AssertBlast
  ORPHAN-ADD-KEY-NOT-IN-ORDER, rc=2, zero write); 8 determinism (identical book bytes and per-item md5 accounts).

Interface.  python3 tests/test_registry_fix_orphan_add.py     # via tests/run_tests.sh
  python3 -B tests/test_registry_fix_orphan_add.py  # manual (-B: no cache)

Dependencies.  Python 3 standard library only; every check runs on self-built mkdtemp fixtures
  cleaned in a finally block; zero writes to the real repository, zero network, zero compile;
  subprocess calls use -B.

Evidence.  Per-check subprocess reports (items / skip / assertions / md5 accounts) are parsed; the
  byte-for-byte rollback comparison and the two-fixture determinism pair pin crash safety and
  reproducibility.

Exit-codes.  0 = all checks pass; 1 = any check failing (fail-loud listing, no silent swallow).
"""
import io
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import registry_fix as rf  # noqa: E402  (fixture builders reused verbatim)

FIX = os.path.join(TOOLS, "registry_fix.py")
AUDIT = os.path.join(TOOLS, "registry_audit.py")
MARK = "REGISTRY-FIX-ORPHAN-ADD PASS"


def run_tool(tool, argv, env_extra=None):
    """Subprocess one tool call (stdout+stderr merged, deterministic env)."""
    env = dict(os.environ)
    env.pop(rf.INJECT_ENV, None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-B", tool] + argv,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    out = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p.returncode, out


def run_audit(order_p, project_p, world, json_p):
    """Fresh files-mode fix-plan audit over the fixture books."""
    rc, out = run_tool(AUDIT, ["--order", order_p, "--project", project_p,
                               "--anchor-src", world, "--fix-plan",
                               "--json", json_p])
    assert rc == 0, "audit should exit 0, got %d\n%s" % (rc, out)
    with io.open(json_p, encoding="utf-8") as fh:
        return json.load(fh)


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def run_fix_on(d, extra, env_extra=None, tag="rep.json"):
    """Run registry_fix over fixture dir d with extra argv; return payload."""
    rep = os.path.join(d, tag)
    rc, out = run_tool(FIX, ["--audit-json", os.path.join(d, "audit.json"),
                             "--order", os.path.join(d, "order.txt"),
                             "--project", os.path.join(d, "_CoqProject"),
                             "--anchor-src", os.path.join(d, "world")]
                       + extra + ["--json", rep], env_extra)
    if not os.path.isfile(rep):
        raise AssertionError("registry_fix rc=%d, no report at %s\n%s"
                             % (rc, rep, out[-600:]))
    return rc, out, rep


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_rf_orphan_")
    try:
        # Shared fixture state for checks 1-2 (same audit, same books).
        d12 = os.path.join(tmp, "base")
        os.makedirs(d12)
        o12, p12, w12 = rf.build_fixture(d12)
        run_audit(o12, p12, w12, os.path.join(d12, "audit.json"))
        base_o, base_p = read_bytes(o12), read_bytes(p12)

        # ---- check 1: default-off parity (legacy classes untouched) ----
        rc, out, rep1 = run_fix_on(d12, [])
        with io.open(rep1, encoding="utf-8") as fh:
            r1 = json.load(fh)
        ok = (rc == 0 and r1["mode"] == "DRY-RUN"
              and r1["stats"]["items_total"] == 16
              and not [it for it in r1["items"] if it["kind"] == "ORPHAN-ADD"]
              and {"ORPHAN-ADD-SKIP-NON-MECHANICAL"} <=
                  {s["kind"] for s in r1["skip"]})
        if not ok:
            fails.append("check1 default-off parity red: rc=%d items=%d "
                         "kinds=%s" % (rc, r1["stats"]["items_total"],
                                       sorted({s["kind"] for s in r1["skip"]})))

        # ---- check 2: --orphan-add dry run (staged item, zero write) ----
        rc, out, rep2 = run_fix_on(d12, ["--orphan-add"])
        with io.open(rep2, encoding="utf-8") as fh:
            r2 = json.load(fh)
        adds = [it for it in r2["items"] if it["kind"] == "ORPHAN-ADD"]
        ok = (rc == 0 and r2["mode"] == "DRY-RUN" and len(adds) == 1
              and adds[0]["book"] == "coqproject" and adds[0]["key"] == "OrphO"
              and adds[0]["row"] == "OrphO.v"
              and read_bytes(o12) == base_o and read_bytes(p12) == base_p)
        if not ok:
            fails.append("check2 dry-run red: rc=%d adds=%s write_drift=%s"
                         % (rc, adds,
                            read_bytes(o12) != base_o
                            or read_bytes(p12) != base_p))

        # ---- checks 3+4: --orphan-add --apply vs flag-off apply ----
        d3 = os.path.join(tmp, "apply")
        os.makedirs(d3)
        o3, p3, w3 = rf.build_fixture(d3)
        run_audit(o3, p3, w3, os.path.join(d3, "audit.json"))
        d3b = os.path.join(tmp, "apply_off")
        os.makedirs(d3b)
        o3b, p3b, w3b = rf.build_fixture(d3b)
        run_audit(o3b, p3b, w3b, os.path.join(d3b, "audit.json"))
        rc_off, out_off, rep3b = run_fix_on(
            d3b, ["--apply", "--work-dir", os.path.join(d3b, "work")])
        rc_on, out_on, rep3 = run_fix_on(
            d3, ["--orphan-add", "--apply",
                 "--work-dir", os.path.join(d3, "work")])
        with io.open(rep3, encoding="utf-8") as fh:
            r3 = json.load(fh)
        with io.open(rep3b, encoding="utf-8") as fh:
            r3b = json.load(fh)
        p_on, p_off = read_bytes(p3), read_bytes(p3b)
        ok = (rc_on == 0 and rc_off == 0
              and r3["assertions"]["ran"] is True
              and r3["assertions"]["treated_duplicates_zero"] == "PASS"
              and r3["assertions"]["anchor_text_no_new_dups"] == "PASS"
              and r3["assertions"]["orphans_no_new"] == "PASS"
              and r3["assertions"]["orphans_resolved"] == "PASS"
              and r3["assertions"]["orphan_add_duplicates_zero"] == "PASS"
              and read_bytes(o3) == read_bytes(o3b))   # order book untouched
        # Precise appended-row assertion: flag-on coqproject is the flag-off
        # coqproject plus exactly one extra tail row "OrphO.v".
        off_rows = p_off.decode("utf-8").strip().split("\n")
        on_rows = p_on.decode("utf-8").strip().split("\n")
        ok = ok and (on_rows == off_rows + ["OrphO.v"]) \
            and on_rows.count("OrphO.v") == 1 \
            and r3["stats"]["items_executed_orphan_add"] == 1 \
            and r3["summary"]["items_executed"] == \
            r3b["summary"]["items_executed"] + 1
        if not ok:
            fails.append("check3/4 apply red: rc_on=%d rc_off=%d "
                         "assertions=%s rows_on=%d rows_off=%d"
                         % (rc_on, rc_off, r3["assertions"], len(on_rows),
                            len(off_rows)))
        skip_o = [s for s in r3["skip"]
                  if s["kind"] == "ORPHAN-ADD-SKIP-NON-MECHANICAL"]
        if not (len(skip_o) == 1 and skip_o[0]["key"] == "OrphP"):
            fails.append("check4 project-only skip red: %s" % (skip_o,))

        # ---- check 5: suffix-twin guard (paired ".v.v" registration) ----
        d5 = os.path.join(tmp, "twin")
        os.makedirs(d5)
        o5, p5, w5 = rf.build_fixture(d5)
        with io.open(o5, "ab") as fh:
            fh.write(b"Twin.v#R5-bbbb0001\n")
        with io.open(p5, "ab") as fh:
            fh.write(b"Twin.v.v\n")
        run_audit(o5, p5, w5, os.path.join(d5, "audit.json"))
        pre5 = (read_bytes(o5), read_bytes(p5))
        rc5, out5, rep5 = run_fix_on(
            d5, ["--orphan-add", "--apply",
                 "--work-dir", os.path.join(d5, "work")])
        with io.open(rep5, encoding="utf-8") as fh:
            r5 = json.load(fh)
        twins = [s for s in r5["skip"]
                 if s["kind"] == "ORPHAN-ADD-SKIP-SUFFIX-TWIN"]
        on5 = read_bytes(p5).decode("utf-8").strip().split("\n")
        ok = (rc5 == 0 and len(twins) == 1 and twins[0]["key"] == "Twin"
              and twins[0].get("twin_key") == "Twin.v"
              and on5.count("Twin.v") == 0          # no second spelling
              and on5.count("OrphO.v") == 1         # eligible entry ran
              and r5["assertions"]["orphans_resolved"] == "PASS")
        if not ok:
            fails.append("check5 suffix-twin red: rc=%d twins=%s rows=%s"
                         % (rc5, twins, [r for r in on5 if "Twin" in r]))

        # ---- check 6: blast injection -> rollback byte-for-byte ----
        d6 = os.path.join(tmp, "blast")
        os.makedirs(d6)
        o6, p6, w6 = rf.build_fixture(d6)
        run_audit(o6, p6, w6, os.path.join(d6, "audit.json"))
        pre6 = (read_bytes(o6), read_bytes(p6))
        rc6, out6, rep6 = run_fix_on(
            d6, ["--orphan-add", "--apply",
                 "--work-dir", os.path.join(d6, "work")],
            env_extra={rf.INJECT_ENV: "post-write"})
        with io.open(rep6, encoding="utf-8") as fh:
            r6 = json.load(fh)
        ok = (rc6 == 2 and "INJECTED-POST-WRITE-BLAST" in out6
              and (read_bytes(o6), read_bytes(p6)) == pre6
              and r6["writes"]["rolled_back"] is True
              and r6["rollback_evidence"]["all_restored"] is True
              and all(os.path.isfile(w["backup"])
                      for w in r6["writes"]["books"]))
        if not ok:
            fails.append("check6 blast rollback red: rc=%d restored=%s"
                         % (rc6, r6.get("rollback_evidence")))

        # ---- check 7a: key already present in the target book -> skip ----
        d7 = os.path.join(tmp, "stale")
        os.makedirs(d7)
        o7, p7, w7 = rf.build_fixture(d7)
        run_audit(o7, p7, w7, os.path.join(d7, "audit.json"))
        with io.open(p7, "ab") as fh:
            fh.write(b"OrphO.v\n")     # drift: key registered after audit
        rc7, out7, rep7 = run_fix_on(
            d7, ["--orphan-add", "--apply",
                 "--work-dir", os.path.join(d7, "work")])
        with io.open(rep7, encoding="utf-8") as fh:
            r7 = json.load(fh)
        pres = [s for s in r7["skip"]
                if s["kind"] == "ORPHAN-ADD-SKIP-KEY-PRESENT"]
        on7 = read_bytes(p7).decode("utf-8").strip().split("\n")
        ok = (rc7 == 0 and len(pres) == 1 and pres[0]["key"] == "OrphO"
              and on7.count("OrphO.v") == 1   # manual row kept, no second spelling
              and not [it for it in r7["items"]
                       if it["kind"] == "ORPHAN-ADD"])
        if not ok:
            fails.append("check7a key-present skip red: rc=%d pres=%s"
                         % (rc7, pres))

        # ---- check 7b: key missing from the order book -> staging blast ----
        d7b = os.path.join(tmp, "stale_order")
        os.makedirs(d7b)
        o7b, p7b, w7b = rf.build_fixture(d7b)
        run_audit(o7b, p7b, w7b, os.path.join(d7b, "audit.json"))
        rows7 = [l for l in read_bytes(o7b).decode("utf-8").split("\n") if l]
        rows7 = [l for l in rows7 if not l.startswith("OrphO.v#")]
        with io.open(o7b, "wb") as fh:
            fh.write(("\n".join(rows7) + "\n").encode("utf-8"))
        pre7b = (read_bytes(o7b), read_bytes(p7b))
        wd7b = os.path.join(d7b, "work")
        rc7b, out7b, _rep7b = run_fix_on(
            d7b, ["--orphan-add", "--apply", "--work-dir", wd7b])
        ok = (rc7b == 2 and "ORPHAN-ADD-KEY-NOT-IN-ORDER" in out7b
              and (read_bytes(o7b), read_bytes(p7b)) == pre7b
              and not os.path.exists(wd7b))   # staging blast: zero write
        if not ok:
            fails.append("check7b not-in-order blast red: rc=%d out=%s"
                         % (rc7b, out7b[-400:]))

        # ---- check 8: determinism (two fresh fixtures under the flag) ----
        runs = []
        for tag in ("det1", "det2"):
            dd = os.path.join(tmp, tag)
            os.makedirs(dd)
            od, pd, wd = rf.build_fixture(dd)
            run_audit(od, pd, wd, os.path.join(dd, "audit.json"))
            rc8, _o8, rep8 = run_fix_on(
                dd, ["--orphan-add", "--apply",
                     "--work-dir", os.path.join(dd, "work")], tag=tag + ".json")
            assert rc8 == 0, "determinism apply should exit 0, got %d" % rc8
            with io.open(rep8, encoding="utf-8") as fh:
                items = json.load(fh)["items"]
            runs.append((read_bytes(od), read_bytes(pd),
                         [(it["kind"], it["key"], it.get("row"),
                           it["md5_before"], it["md5_after"]) for it in items]))
        if not (runs[0][0] == runs[1][0] and runs[0][1] == runs[1][1]
                and runs[0][2] == runs[1][2]):
            fails.append("check8 determinism red: book bytes or md5 accounts "
                         "drifted between fresh fixtures")

        print("== test_registry_fix_orphan_add: %d checks, %d red =="
              % (8, len(fails)))
        for f in fails:
            print("FAIL:", f)
        if not fails:
            print(MARK)
        return 1 if fails else 0
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
