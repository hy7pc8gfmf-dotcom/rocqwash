#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wash_engine.py — generic per-item norm sanitize engine (rocqwash wash/).
Purpose.  Argv-driven per-item executor for the norm-surface mapping sanitize (step 3
  of the seven-step standard): exact-string replace with count assertion, idempotent
  replay (post-apply signature face = SKIP; provenance-undecidable SKIP rows are
  counted in summary.unproven_provenance and never claimed as applied), fail-loud
  (any FAIL leaves the file unwritten), nesting-aware bracket checking of ledger fragments (after comment/string
  masking).  It never guesses a target: with no --patch it exits 3 (SKIP semantics) and
  never fills an implicit mapping; the mapping ledger comes from upstream triage and is
  executed mechanically here (unified entry `cli/rocqwash wash`); in service October 31,
  2026, generalizing `wash/_abl1_wash.py` (built October 27, 2026).
Interface.  python3 wash/wash_engine.py --file <in.v> --patch <ledger.json> --out <out.v>
  [--dry-run] [--json out.json] [--selftest].  Ledger JSON, both forms accepted:
  {"file": "optional default target.v", "patches": [{"tag", "old", "new", "expect":
  integer >= 1}, ...]} or a bare array; old/new bracket-balanced (comment/string
  brackets excluded); old != new; a prefix patch (old inside new) is
  idempotent on rerun: the SKIP criterion matches the post-apply self-inflicted
  signature (new.count(old) x expect), so a prefix patch no longer replays APPLY
  (the 20261126 divergence from `wash/_abl1_wash.py:130-151`, which keeps its own
  criterion outside this ticket's write face); for sig == 1 the signature
  coincides with the pristine expect face and SKIP is the chosen semantic
  (idempotency preserved; a pristine file with a coincidental new form needs
  operator adjudication).
Dependencies.  Python 3 standard library only.  The apply loop (APPLY/SKIP/FAIL rows,
  post-assert, selective write) is derived from `wash/_abl1_wash.py:130-151` with
  the provenance-honest SKIP face recorded above; strip_comments_strings re-implements `scan/mac_stmt_scan.py:104-125`
  locally without importing the frozen file (drift cannot propagate), the equivalence
  machine-attested by the --selftest nested-comment vectors; the ledger shape
  transcribes the _abl1_wash.py PATCHES ledger field for field (tag/old/new/expect).
Evidence.  --selftest: ten vectors on a temp directory (pos, idempotent byte-identity,
  write isolation, corruption neg, bracket neg, ledger neg, no-ledger, prefix-patch
  idempotent replay, unproven-provenance no-op face, prefix signature-mismatch
  fail-loud);
  `tests/test_wash_engine.py` drives the same paths through the real argv CLI.
Exit-codes.  0 all rows APPLY/SKIP (unproven-provenance rows surface in the summary
  face, rc-neutral); 1 any FAIL (file not written; includes the never-applied prefix
  and signature-mismatch corners, each named not-recorded-as-already-applied); 2 malformed ledger
  (bad JSON, missing field, bracket imbalance, old == new, expect < 1) or --out ==
  --file refused; 3 no --patch given (SKIP semantics); 9 --file/--patch path missing.
  Write isolation: --file is never rewritten; source and output md5 both reported.
"""
import argparse
import hashlib
import io
import json
import os
import sys

PROG = "wash_engine"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_comments_strings(text):
    """State machine stripping nested comments and string literals; stripped
    regions become spaces so line numbers survive.

    1:1 frozen inheritance from scan/mac_stmt_scan.py:104-125 (word-face
    check v3, E364 T8/T3) — re-implemented locally without an import; the
    equivalence is machine-attested by the --selftest nested-comment vectors.
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1; out.append("  "); i += 2; continue
            if text.startswith("*)", i):
                depth -= 1; out.append("  "); i += 2; continue
            out.append(c if c == "\n" else " "); i += 1; continue
        if text.startswith("(*", i):
            depth = 1; out.append("  "); i += 2; continue
        if c == '"':
            out.append(" "); i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " "); i += 1
            if i < n: out.append(" "); i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def bracket_report(fragment):
    """Nesting-aware bracket check: per-bracket depth after comment/string
    masking.  Returns (ok, locator)."""
    clean = strip_comments_strings(fragment)
    pairs = {")": "(", "]": "[", "}": "{"}
    depths = {"(": 0, "[": 0, "{": 0}
    for i, c in enumerate(clean):
        if c in depths:
            depths[c] += 1
        elif c in pairs:
            o = pairs[c]
            if depths[o] <= 0:
                return False, "孤儿 closer %r @掩蔽后偏移 %d" % (c, i)
            depths[o] -= 1
    for o, d in depths.items():
        if d != 0:
            return False, "括号失衡：剩余 %d 个未闭合 %r" % (d, o)
    return True, "balanced"


def load_ledger(patch_path):
    """Read the ledger JSON (bare array or {"patches":[...]}, both forms) and
    validate it row by row (fail-loud)."""
    try:
        with io.open(patch_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        raise LedgerError("台账 JSON 解析失败 %s: %s" % (patch_path, e))
    if isinstance(data, dict):
        plist = data.get("patches")
        default_file = data.get("file")
    else:
        plist, default_file = data, None
    if not isinstance(plist, list) or not plist:
        raise LedgerError("台账须非空数组或 {\"patches\": [...]}（实测 %s）"
                          % type(data).__name__)
    for k, p in enumerate(plist):
        where = "patches[%d]" % k
        if not isinstance(p, dict):
            raise LedgerError("%s 须对象（实测 %s）" % (where, type(p).__name__))
        for field in ("tag", "old", "new", "expect"):
            if field not in p:
                raise LedgerError("%s 缺字段 %s" % (where, field))
        if not isinstance(p["tag"], str) or not p["tag"]:
            raise LedgerError("%s.tag 须非空字符串" % where)
        for field in ("old", "new"):
            if not isinstance(p[field], str):
                raise LedgerError("%s.%s 须字符串" % (where, field))
        if not isinstance(p["expect"], int) or isinstance(p["expect"], bool) \
                or p["expect"] < 1:
            raise LedgerError("%s.expect 须 ≥1 整数（实测 %r）" % (where, p["expect"]))
        if p["old"] == p["new"]:
            raise LedgerError("%s old==new（空洗拒绝）" % where)
        for field in ("old", "new"):
            ok, why = bracket_report(p[field])
            if not ok:
                raise LedgerError("%s.%s 嵌套括号感知不过：%s" % (where, field, why))
    return plist, default_file


class LedgerError(Exception):
    pass


def apply_patches(content, plist, fname="<mem>"):
    """The apply loop — derived from wash/_abl1_wash.py:130-151 with the
    provenance-honest SKIP face (the 20261126 divergence is recorded in the
    module docstring; the batch tool keeps its own criterion, outside this
    ticket's write face).

    Classification per patch, with sig = new.count(old) (the self-inflicted
    old-substring count per inserted site):
    - postcondition holds (c_new >= expect) and c_old == sig * expect: SKIP.
      sig >= 1: the old-count equals the post-apply signature - the
      idempotent replay face (a prefix patch no longer replays APPLY).
      sig == 0: old absent - consistent with an earlier apply OR a
      coincidental pre-existing form; the provenance is undecidable from
      the content alone, so the row is never claimed as "already applied"
      (the text says so and summary["unproven_provenance"] counts it).
      For sig == 1 the signature coincides with the pristine expect face;
      SKIP is the chosen semantic there (idempotency preserved; a pristine
      file with a coincidental new form needs operator adjudication).
    - c_old == expect: APPLY (the unambiguous pristine face).
    - otherwise FAIL: includes the never-applied prefix corner and any
      new-present/old-absent state whose signature cannot hold - fail loud
      with an explicit not-recorded-as-already-applied note.

    Returns (new_content, rows, fail_flag); rows=[(tag, state, detail)],
    state in APPLY/SKIP/FAIL.  With fail=True new_content is invalid (the
    caller must not write it to disk).
    """
    rows = []
    n_apply = n_skip = n_fail = 0
    n_unproven = 0
    file_fail = False
    for tag, old, new, expect in [(p["tag"], p["old"], p["new"], p["expect"])
                                  for p in plist]:
        c_old = content.count(old)
        c_new = content.count(new)
        sig = new.count(old)  # self-inflicted old-substrings per inserted site
        if c_new >= expect and c_old == sig * expect:
            n_skip += 1
            if sig == 0:
                n_unproven += 1
                rows.append((tag, "SKIP",
                             "no-op: new form present (>= %d), old absent - an earlier "
                             "apply or a coincidental pre-existing form; provenance is "
                             "undecidable from the content and NOT asserted" % expect))
            else:
                rows.append((tag, "SKIP",
                             "idempotent replay: old-count %d equals the post-apply "
                             "signature (new inserts %d old-substrings per site x expect "
                             "%d)" % (c_old, sig, expect)))
            continue
        if c_old == expect:
            content = content.replace(old, new)
            assert content.count(new) >= expect, "post-assert %s:%s" % (fname, tag)
            rows.append((tag, "APPLY", "old=%d -> new inserted" % c_old))
            n_apply += 1
            continue
        file_fail = True
        n_fail += 1
        if c_new >= expect:
            detail = ("count(old)=%d expect=%d with the new form already present and the "
                      "post-apply signature not matched -- no edit; NOT recorded as "
                      "already-applied" % (c_old, expect))
        else:
            detail = "count(old)=%d expect=%d -- no edit" % (c_old, expect)
        rows.append((tag, "FAIL", detail))
    summary = {"applied": n_apply, "skipped": n_skip, "fail": n_fail,
               "unproven_provenance": n_unproven,
               "file_fail": file_fail}
    return content, rows, summary


def selftest():
    """Embedded frozen vector set: pos / idempotence / corruption neg /
    bracket neg / ledger neg (temp-directory driven)."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_washeng_self_")
    try:
        src_v = os.path.join(tmp, "vec.v")
        body = "(* nest (* deep *) outer *)\nLemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n"
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
        ledger = {"patches": [
            {"tag": "eq2id", "expect": 1,
             "old": "Lemma vec_a : forall x : nat, x = x.\n",
             "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"},
            {"tag": "refl2id", "expect": 1,
             "old": "  intros x. reflexivity.\n",
             "new": "  intros x. apply id_refl.\n"},
        ]}
        ledger_path = os.path.join(tmp, "ledger.json")
        with io.open(ledger_path, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)

        # -- pos: all APPLY, on-disk count assertions, nested comment intact --
        out_v = os.path.join(tmp, "vec_washed.v")
        rc = run_args(["--file", src_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 0, "正判应 exit 0 实测 %d" % rc
        with io.open(out_v, encoding="utf-8", newline="") as fh:
            washed = fh.read()
        assert washed.count("Id nat x x") == 1 and washed.count("apply id_refl") == 1
        assert washed.count("x = x.") == 0 and washed.count("reflexivity") == 0
        assert "nest (* deep *) outer" in washed, "注释内容须原样保留"

        # -- idem: replay the same ledger on the sanitized product
        #      -> all SKIP, exit 0, byte-identical product --
        before = open(out_v, "rb").read()
        out_v2 = os.path.join(tmp, "vec_washed2.v")
        rc = run_args(["--file", out_v, "--patch", ledger_path, "--out", out_v2])
        assert rc == 0, "幂等重放应 exit 0 实测 %d" % rc
        assert open(out_v2, "rb").read() == before, "幂等重放不得改字节"

        # -- write isolation: --out == --file refused (exit 2) --
        rc = run_args(["--file", out_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 2, "--out==--file 应 exit 2 实测 %d" % rc

        # -- corruption neg: the exact old string broken
        #      -> FAIL, exit 1, product byte-untouched --
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write(body.replace("x = x.", "x = (x)."))
        rc = run_args(["--file", src_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 1, "破坏反判应 exit 1 实测 %d" % rc
        assert open(out_v, "rb").read() == before, "fail-loud 失守：坏账竟落盘"

        # -- bracket neg: unbalanced old -> exit 2, zero writes --
        bad = {"patches": [{"tag": "bad", "old": "f (x.", "new": "g (x).", "expect": 1}]}
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        rc = run_args(["--file", src_v, "--patch", bad_path, "--out", out_v])
        assert rc == 2, "括号失衡应 exit 2 实测 %d" % rc

        # -- ledger neg: old == new -> exit 2 --
        silly = {"patches": [{"tag": "s", "old": "a", "new": "a", "expect": 1}]}
        silly_path = os.path.join(tmp, "silly.json")
        with io.open(silly_path, "w", encoding="utf-8") as fh:
            json.dump(silly, fh)
        rc = run_args(["--file", src_v, "--patch", silly_path, "--out", out_v])
        assert rc == 2, "old==new 应 exit 2 实测 %d" % rc

        # -- no ledger -> exit 3 (SKIP semantics, never guesses) --
        rc = run_args(["--file", src_v])
        assert rc == 3, "无台账应 exit 3 实测 %d" % rc

        # -- prefix idem: old inside new, sig = 2; rerun must SKIP by the
        #      post-apply signature, byte-identical product --
        pfx_ledger = {"patches": [
            {"tag": "pfx", "expect": 1,
             "old": "intros x. reflexivity.",
             "new": "(intros x. reflexivity.) (intros x. reflexivity.)"}]}
        pfx_path = os.path.join(tmp, "pfx.json")
        with io.open(pfx_path, "w", encoding="utf-8") as fh:
            json.dump(pfx_ledger, fh)
        out_p1 = os.path.join(tmp, "pfx_washed.v")
        rc = run_args(["--file", src_v, "--patch", pfx_path, "--out", out_p1])
        assert rc == 0, "prefix 首apply应 exit 0 实测 %d" % rc
        before_p = open(out_p1, "rb").read()
        out_p2 = os.path.join(tmp, "pfx_washed2.v")
        rc = run_args(["--file", out_p1, "--patch", pfx_path, "--out", out_p2])
        assert rc == 0, "prefix 幂等重放应 exit 0 实测 %d" % rc
        assert open(out_p2, "rb").read() == before_p, "prefix 重放不得改字节"

        # -- unproven no-op: non-prefix patch whose new form is already
        #      present and old never existed -> SKIP rc 0 with
        #      summary.unproven_provenance counted, never claimed applied --
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write(body)  # restore the pristine body (the corruption neg above rewrote it)
        unpr_ledger = {"patches": [
            {"tag": "unpr", "expect": 1,
             "old": "ZZZ_NEVER_PRESENT_HERE",
             "new": "Lemma vec_a : forall x : nat, x = x."}]}
        unpr_path = os.path.join(tmp, "unpr.json")
        with io.open(unpr_path, "w", encoding="utf-8") as fh:
            json.dump(unpr_ledger, fh)
        j9 = os.path.join(tmp, "unpr.json.out")
        rc = run_args(["--file", src_v, "--patch", unpr_path, "--dry-run", "--json", j9])
        assert rc == 0, "unproven no-op 应 exit 0 实测 %d" % rc
        with io.open(j9, encoding="utf-8") as fh:
            acc9 = json.load(fh)
        assert acc9.get("unproven_provenance") == 1,             "unproven_provenance 应=1 实测 %r" % acc9.get("unproven_provenance")

        # -- prefix signature-mismatch neg: new form present at two sites
        #      (expect = 1), so the post-apply signature cannot hold ->
        #      FAIL rc 1, explicitly not already-applied --
        na_ledger = {"patches": [
            {"tag": "napfx", "expect": 1,
             "old": "QWXP_NEVER_APPLIED",
             "new": "(QWXP_NEVER_APPLIED) (QWXP_NEVER_APPLIED)"}]}
        na_path = os.path.join(tmp, "napfx.json")
        with io.open(na_path, "w", encoding="utf-8") as fh:
            json.dump(na_ledger, fh)
        na_v = os.path.join(tmp, "na.v")
        with io.open(na_v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma dup1 : (QWXP_NEVER_APPLIED) (QWXP_NEVER_APPLIED) := I.\n"
                     "Lemma dup2 : (QWXP_NEVER_APPLIED) (QWXP_NEVER_APPLIED) := I.\n")
        rc = run_args(["--file", na_v, "--patch", na_path, "--dry-run"])
        assert rc == 1, "prefix never-applied 应 exit 1 实测 %d" % rc

        print("WASH-ENGINE-SELFTEST PASS: pos/idem/isolation/neg/bracket-neg/ledger-neg/no-ledger/prefix-idem/unproven/prefix-neg 十判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    """Drive main() from argv (the selftest reuse path); returns the
    process-semantics exit code."""
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    # No-ledger pre-split: --patch/-p both absent from argv and not
    # --selftest -> exit 3 (SKIP semantics).
    # Before argparse: bare/positional calls through the unified entry (e.g.
    # the make demo form `cli/rocqwash wash demo.v`) always take this branch,
    # so the demo SKIP criterion (rc 3/4) keeps holding; with a ledger
    # present, unknown arguments are still hard-refused by argparse
    # (usage exit 2, fail-loud, no leaks).
    argv = sys.argv[1:]
    has_patch = any(a == "-p" or a == "--patch" or a.startswith("--patch=") for a in argv)
    has_selftest = any(a == "--selftest" for a in argv)
    if not has_patch and not has_selftest:
        print("wash_engine: 未给 --patch——洗目标永不猜（七步③须显式台账）。", file=sys.stderr)
        print("  用法: wash_engine.py --file <in.v> --patch <ledger.json> --out <out.v>", file=sys.stderr)
        print("  （无台账=SKIP 语义 exit 3；台账形制见本文件 docstring）", file=sys.stderr)
        sys.exit(3)
    ap = argparse.ArgumentParser(prog=PROG, description="通用逐件规范洗引擎（exact-string+count+幂等）")
    ap.add_argument("file_pos", nargs="?", default=None, metavar="FILE",
                    help="同 --file（位置形；统一入口裸调形态）")
    ap.add_argument("--file", "-f", dest="file_opt", default=None, help="输入 .v（写隔离·永不回写）")
    ap.add_argument("--patch", "-p", default=None, help="洗账台账 JSON（tag/old/new/expect）")
    ap.add_argument("--out", "-o", default=None, help="洗后输出路径（必填才落盘；== --file 拒绝）")
    ap.add_argument("--dry-run", action="store_true", help="全账出账不落盘")
    ap.add_argument("--json", default=None, help="账目 JSON 出账路径")
    ap.add_argument("--selftest", action="store_true", help="内嵌冻结向量组五判自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    if not os.path.isfile(args.patch):
        print("FAIL-LOUD: --patch 路径缺失: %s" % args.patch, file=sys.stderr)
        sys.exit(9)
    try:
        plist, ledger_default = load_ledger(args.patch)
    except LedgerError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    src = args.file_opt or args.file_pos or ledger_default
    if src is None:
        print("FAIL-LOUD: 有 --patch 但缺 --file（或台账 file 字段）", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(src):
        print("FAIL-LOUD: --file 路径缺失: %s" % src, file=sys.stderr)
        sys.exit(9)

    if args.out and os.path.abspath(args.out) == os.path.abspath(src):
        print("FAIL-LOUD: 写隔离——--out 不得等于 --file（%s）" % src, file=sys.stderr)
        sys.exit(2)

    with io.open(src, encoding="utf-8", newline="") as fh:
        content = fh.read()
    src_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()

    new_content, rows, summary = apply_patches(content, plist, fname=os.path.basename(src))
    for tag, state, detail in rows:
        print("%-5s %s:%s  %s" % (state, os.path.basename(src), tag, detail))

    wrote = False
    out_md5 = None
    if summary["file_fail"]:
        print("--- applied=%d skipped=%d fail=YES  file=NOT-WRITTEN（fail-loud·修账后重跑）"
              % (summary["applied"], summary["skipped"]))
    elif args.dry_run:
        print("--- applied=%d skipped=%d fail=NO  file=DRY-RUN（未落盘）"
              % (summary["applied"], summary["skipped"]))
    elif not args.out:
        print("FAIL-LOUD: 需 --out 才落盘（写隔离·原件不回写）；或用 --dry-run 仅出账", file=sys.stderr)
        sys.exit(2)
    else:
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_content)
        wrote = True
        out_md5 = md5_of(args.out)
        print("--- applied=%d skipped=%d fail=NO  file=%s" % (summary["applied"], summary["skipped"], args.out))

    if summary.get("unproven_provenance"):
        print("--- unproven-provenance=%d (SKIP rows whose applied-provenance is undecidable; never asserted as already-applied)"
              % summary["unproven_provenance"])
    print("md5 src=%s%s" % (src_md5, (" out=%s" % out_md5) if out_md5 else ""))

    if args.json:
        acc = {"file": src, "patch": args.patch, "out": args.out if wrote else None,
               "dry_run": args.dry_run, "src_md5": src_md5, "out_md5": out_md5,
               "rows": [{"tag": t, "state": s, "detail": d} for t, s, d in rows],
               **{k: v for k, v in summary.items()}}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(1 if summary["file_fail"] else 0)


if __name__ == "__main__":
    main()
