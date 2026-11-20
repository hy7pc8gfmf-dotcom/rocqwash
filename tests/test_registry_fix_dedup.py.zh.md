#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_fix_dedup.py — DEDUP-family unit tests for tools/registry_fix.py
(tests/ · RQW09 duplicates-family executor agent · 20261114)

The DUP-family apply path already exists in tools/registry_fix.py
(stage_dedup + --apply + assertion A-fix-1 + injectable blast hook); this
file does not reinvent it. It pins the DEDUP contract from the prescription
producer's semantics (tools/registry_audit.py --fix-plan, schema
rocqwash-registry-audit/1) so the family behavior is guarded by the suite:

  1. fix_plan contract: keep_line = min line number (keep-first-in-order,
     NOT prefer-canonical-anchor), drop_lines = rest ascending.
  2. Dry run: rc=0, mode DRY-RUN, writes is None, book bytes unchanged.
  3. Apply on a tmp copy: keep-first row survives verbatim (dedup is
     content-preserving; anchor normalization is REANCHOR's job, not
     DEDUP's), exactly the drop lines are removed, per-item md5 accounts
     match the on-disk bytes, post re-audit reports duplicates=0.
  4. Blast hook (ROCWASH_REGISTRY_FIX_INJECT_BLAST=post-write): rc=2,
     both books restored byte-identical, rollback evidence in the report.
  5. Stale-plan blast (plan/book drift): rc=2 DEDUP-KEEP-KEY-MISMATCH,
     zero write, work dir not created.
  6. CLI contract spot checks: help=0 / bogus=2 / no-input=2 /
     missing-audit-json=9 / bad-schema=2 / no-fix-plan=2 / same-param
     break=2 / missing-anchor-src-dir=9.

Fixtures are synthetic tmp books only; the real Main/Set registries are
never touched. Zero network, zero compile. python -B keeps __pycache__ off.

Usage:
  python3 tests/test_registry_fix_dedup.py    # via run_tests.sh
  python -B tests/test_registry_fix_dedup.py  # manual

Exit codes: 0 = all checks pass; 1 = any check red (fail loud).
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(REPO, "tools", "registry_audit.py")
FIX = os.path.join(REPO, "tools", "registry_fix.py")
INJECT_ENV = "ROCWASH_REGISTRY_FIX_INJECT_BLAST"


def md5_of(path):
    h = hashlib.md5()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def wf(path, text):
    with io.open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    return path


def run_py(script, args, env_extra=None):
    env = dict(os.environ)
    env.pop(INJECT_ENV, None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-B", script] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def audit_fixplan(order_p, project_p, out_json):
    argv = ["--order", order_p, "--project", project_p,
            "--json", out_json, "--fix-plan"]
    rc, out = run_py(AUDIT, argv)
    assert rc == 0, "audit --fix-plan should rc=0, got %d\n%s" % (rc, out)
    with io.open(out_json, encoding="utf-8") as fh:
        return json.load(fh)


def write_books(base, order_rows, project_rows):
    return (wf(os.path.join(base, "order.txt"),
               "\n".join(order_rows) + "\n"),
            wf(os.path.join(base, "_CoqProject"),
               "\n".join(project_rows) + "\n"))


def check_fix_plan_contract(tmp):
    """Check 1: keep-first direction pinned from the producer's side."""
    base = os.path.join(tmp, "c1")
    os.makedirs(base)
    order_rows = [
        "Aaa.v#R5",            # L1 seq-form anchor, FIRST occurrence
        "Aaa.v#R5-0123abcd",   # L2 canonical anchor (not the kept one)
        "Bbb.v#R6-11112222",   # L3 unrelated key
    ]
    project_rows = ["Aaa.v", "Aaa.v", "Bbb.v"]
    o, p = write_books(base, order_rows, project_rows)
    payload = audit_fixplan(o, p, os.path.join(base, "audit.json"))
    dups = payload["sections"]["duplicates"]
    assert len(dups) == 2, dups
    plan = {d["book"]: d for d in payload["fix_plan"]["dedup"]}
    assert set(plan) == {"order", "coqproject"}, sorted(plan)
    # keep-first-in-order (min line), not prefer-canonical-anchor
    assert plan["order"]["key"] == "Aaa.v", plan["order"]
    assert plan["order"]["keep_line"] == 1, plan["order"]
    assert plan["order"]["drop_lines"] == [2], plan["order"]
    assert plan["coqproject"]["key"] == "Aaa", plan["coqproject"]
    assert plan["coqproject"]["keep_line"] == 1, plan["coqproject"]
    assert plan["coqproject"]["drop_lines"] == [2], plan["coqproject"]
    print("  [1/6] fix_plan contract OK (keep=min line, drops ascending, "
          "both books)")


def check_dry_run_zero_write(tmp):
    """Check 2: dry run stages items and writes nothing."""
    base = os.path.join(tmp, "c2")
    os.makedirs(base)
    o, p = write_books(
        base,
        ["Aaa.v#R1-aaaa0001", "Bbb.v#R2-bbbb0002", "Aaa.v#R1-aaaa0002"],
        ["Aaa.v", "Bbb.v", "Aaa.v"])
    audit_fixplan(o, p, os.path.join(base, "audit.json"))
    pre = (md5_of(o), md5_of(p))
    rc, out = run_py(FIX, ["--audit-json", os.path.join(base, "audit.json"),
                           "--order", o, "--project", p])
    assert rc == 0, "dry run should rc=0, got %d\n%s" % (rc, out)
    assert "DRY-RUN" in out, out
    assert (md5_of(o), md5_of(p)) == pre, "dry run must not touch the books"
    print("  [2/6] dry-run zero-write OK (staged items, books byte-stable)")


def check_apply_keep_first(tmp):
    """Check 3: apply executes keep-first dedup with an exact per-item diff."""
    base = os.path.join(tmp, "c3")
    os.makedirs(base)
    order_rows = [
        "Aaa.v#R1-aaaa0001",   # L1 keep (first in order)
        "Bbb.v#R2-bbbb0002",   # L2 untouched
        "Aaa.v#R1-aaaa0002",   # L3 drop
        "Ccc.v#R3-cccc0003",   # L4 untouched
        "Aaa.v#R1-aaaa0003",   # L5 drop
    ]
    project_rows = ["Aaa.v", "Bbb.v", "Ccc.v", "Aaa.v"]
    o, p = write_books(base, order_rows, project_rows)
    audit_fixplan(o, p, os.path.join(base, "audit.json"))
    rc, out = run_py(FIX, ["--audit-json", os.path.join(base, "audit.json"),
                           "--order", o, "--project", p,
                           "--apply", "--work-dir", os.path.join(base, "work"),
                           "--json", os.path.join(base, "rep.json")])
    assert rc == 0, "apply should rc=0, got %d\n%s" % (rc, out)
    with io.open(os.path.join(base, "rep.json"), encoding="utf-8") as fh:
        rep = json.load(fh)
    assert rep["mode"] == "APPLY", rep["mode"]
    an = rep["assertions"]
    assert an["ran"] is True and an["treated_duplicates_zero"] == "PASS" \
        and an["anchor_text_no_new_dups"] == "PASS" \
        and an["orphans_no_new"] == "PASS", an
    items = {it["book"]: it for it in rep["items"] if it["kind"] == "DEDUP"}
    assert items["order"]["keep_line"] == 1, items["order"]
    assert items["order"]["drop_lines"] == [3, 5], items["order"]
    assert items["coqproject"]["drop_lines"] == [4], items["coqproject"]
    # exact diff: only the drop lines vanish, order of survivors preserved
    with io.open(o, encoding="utf-8") as fh:
        post = [ln for ln in fh.read().split("\n") if ln]
    assert post == [order_rows[0], order_rows[1], order_rows[3]], post
    with io.open(p, encoding="utf-8") as fh:
        post_p = [ln for ln in fh.read().split("\n") if ln]
    assert post_p == project_rows[:3], post_p
    # per-item md5 account matches the on-disk bytes (last item per book)
    writes = {w["book"]: w for w in rep["writes"]["books"]}
    assert writes["order"]["rows_before"] == 5 \
        and writes["order"]["rows_after"] == 3, writes["order"]
    assert writes["coqproject"]["rows_before"] == 4 \
        and writes["coqproject"]["rows_after"] == 3, writes["coqproject"]
    for label, path in (("order", o), ("coqproject", p)):
        last = [it for it in rep["items"] if it["book"] == label][-1]
        assert last["md5_after"] == md5_of(path), label
    # independent re-audit: duplicates gone for the treated keys
    rc, out = run_py(AUDIT, ["--order", o, "--project", p, "--json",
                             os.path.join(base, "post.json")])
    assert rc == 0, out
    with io.open(os.path.join(base, "post.json"), encoding="utf-8") as fh:
        post_payload = json.load(fh)
    assert post_payload["summary"]["duplicates"] == 0, post_payload["summary"]
    print("  [3/6] apply keep-first OK (5->3 / 4->3 rows, exact diff, "
          "md5 accounts = disk, re-audit duplicates=0)")


def check_blast_hook_rollback(tmp):
    """Check 4: injected post-write blast rolls back byte-identically."""
    base = os.path.join(tmp, "c4")
    os.makedirs(base)
    o, p = write_books(
        base,
        ["Aaa.v#R1-aaaa0001", "Bbb.v#R2-bbbb0002", "Aaa.v#R1-aaaa0009"],
        ["Aaa.v", "Bbb.v", "Aaa.v"])
    audit_fixplan(o, p, os.path.join(base, "audit.json"))
    pre = (md5_of(o), md5_of(p))
    rc, out = run_py(FIX, ["--audit-json", os.path.join(base, "audit.json"),
                           "--order", o, "--project", p,
                           "--apply", "--work-dir", os.path.join(base, "work"),
                           "--json", os.path.join(base, "rep.json")],
                     env_extra={INJECT_ENV: "post-write"})
    assert rc == 2, "injected blast should rc=2, got %d\n%s" % (rc, out)
    assert "INJECTED-POST-WRITE-BLAST" in out, out[-400:]
    assert (md5_of(o), md5_of(p)) == pre, "rollback must restore bytes"
    with io.open(os.path.join(base, "rep.json"), encoding="utf-8") as fh:
        rep = json.load(fh)
    assert rep["writes"]["rolled_back"] is True, rep["writes"]
    assert rep["rollback_evidence"]["all_restored"] is True, \
        rep["rollback_evidence"]
    for w in rep["writes"]["books"]:
        assert os.path.isfile(w["backup"]), w
    print("  [4/6] blast hook OK (rc=2, rollback byte-identical, evidence "
          "in report)")


def check_stale_plan_blast(tmp):
    """Check 5: plan/book drift fails loud at staging with zero writes."""
    base = os.path.join(tmp, "c5")
    os.makedirs(base)
    o, p = write_books(
        base,
        ["Aaa.v#R1-aaaa0001", "Bbb.v#R2-bbbb0002", "Aaa.v#R1-aaaa0009"],
        ["Aaa.v", "Bbb.v", "Aaa.v"])
    audit_fixplan(o, p, os.path.join(base, "audit.json"))
    wf(p, "Zzz.v\n" + io.open(p, "rb").read().decode("utf-8"))  # shift lines
    pre = (md5_of(o), md5_of(p))
    work = os.path.join(base, "work")
    rc, out = run_py(FIX, ["--audit-json", os.path.join(base, "audit.json"),
                           "--order", o, "--project", p,
                           "--apply", "--work-dir", work])
    assert rc == 2, "stale plan should rc=2, got %d\n%s" % (rc, out)
    assert "DEDUP-KEEP-KEY-MISMATCH" in out, out[-400:]
    assert (md5_of(o), md5_of(p)) == pre, "staging blast must not write"
    assert not os.path.exists(work), "staging blast must not create work dir"
    print("  [5/6] stale-plan blast OK (rc=2, zero write, work dir absent)")


def check_cli_contract(tmp):
    """Check 6: CLI exit-code contract spot checks."""
    base = os.path.join(tmp, "c6")
    os.makedirs(base)
    o, p = write_books(base, ["Aaa.v#R1-aaaa0001"], ["Aaa.v"])
    audit_fixplan(o, p, os.path.join(base, "audit.json"))
    nofp = os.path.join(base, "nofix.json")
    rc, _ = run_py(AUDIT, ["--order", o, "--project", p, "--json", nofp])
    assert rc == 0, rc
    cases = [
        (["--help"], 0),
        (["--bogus"], 2),
        ([], 2),
        (["--audit-json", os.path.join(base, "missing.json"),
          "--order", o, "--project", p], 9),
        (["--audit-json", os.path.join(base, "audit.json"),
          "--order", o, "--project", p,
          "--anchor-src", os.path.join(base, "no-such-dir")], 9),
    ]
    for argv, want in cases:
        rc, out = run_py(FIX, argv)
        assert rc == want, "argv %r: want rc=%d got %d\n%s" % (
            argv[0], want, rc, out[-300:])
    bad = wf(os.path.join(base, "badschema.json"),
             json.dumps({"schema": "bogus/9"}))
    rc, _ = run_py(FIX, ["--audit-json", bad, "--order", o, "--project", p])
    assert rc == 2, "bad schema should rc=2, got %d" % rc
    rc, _ = run_py(FIX, ["--audit-json", nofp,
                         "--order", o, "--project", p])
    assert rc == 2, "audit without fix_plan should rc=2, got %d" % rc
    # same-param break: audit produced for (o,p) must not run against
    # a different pair of books
    other = os.path.join(base, "other")
    os.makedirs(other)
    o2, p2 = write_books(other, ["Xxx.v#R4-dddd0004"], ["Xxx.v"])
    rc, out = run_py(FIX, ["--audit-json", os.path.join(base, "audit.json"),
                           "--order", o2, "--project", p2])
    assert rc == 2, "same-param break should rc=2, got %d" % rc
    assert "同参纪律破" in out or "same-param" in out, out[-300:]
    print("  [6/6] CLI contract OK (help=0 bogus=2 no-input=2 missing-json=9 "
          "bad-schema=2 no-fix-plan=2 same-param=2 missing-anchor-src=9)")


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_rf_dedup_")
    fails = []
    checks = (
        ("fix_plan contract", check_fix_plan_contract),
        ("dry run zero write", check_dry_run_zero_write),
        ("apply keep-first", check_apply_keep_first),
        ("blast hook rollback", check_blast_hook_rollback),
        ("stale plan blast", check_stale_plan_blast),
        ("CLI contract", check_cli_contract),
    )
    try:
        for i, (name, fn) in enumerate(checks, 1):
            try:
                fn(tmp)
            except AssertionError as e:
                fails.append("check %d (%s): %s" % (i, name, e))
            except Exception as e:  # fail loud with the original traceback
                import traceback
                fails.append("check %d (%s) unexpected %r:\n%s"
                             % (i, name, e, traceback.format_exc()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("== test_registry_fix_dedup: %d pass / %d red =="
          % (len(checks) - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
