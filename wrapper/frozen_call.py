#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frozen_call.py - wrapper-layer per-call assertion: byte-identity lock for an in-service frozen component before each invocation (rocqwash wrapper/).
Purpose.  Identical frozen-component copies are deployed across the four registered
  repositories, and a task instruction may name one copy while another copy is the one that
  actually runs; this layer closes that gap mechanically: before each invocation the invoked
  copy is asserted against the reconciliation manifest (same-repo `wrapper/quad8_reconcile.py`
  freeze output; two-layer freeze, tier1 per-copy md5 plus tier2 md5 of the tier1 ledger
  text, per the `certify/freeze_manifest.py` v1 semantics); the copy must be registered at
  its exact path and its on-disk md5 must equal the registered value; every call is recorded
  as a JSONL ledger row and the command then runs with its exit code passed through
  unchanged; refusals run no command (fail-closed, no spurious pass per CONTRIBUTING §0).
Interface.  python3 wrapper/frozen_call.py [--manifest LIST.json] [--log LEDGER.jsonl] -- <copy-path> [args...]
  | --selftest.  --manifest defaults to the same-repo `wrapper/quad8_manifest.json`; --log
  defaults to `seat_rqadapt/账/quad8_call_ledger.jsonl` (env `QUAD8_CALLLOG` overrides).
  Execution mapping: `.py` -> `python3 -B` (`scan/mac_stmt_scan.py` ships no shebang and no
  executable bit, verified on the volume); `.sh` -> bash; other types execv directly
  (shebang plus executable bit).  Zero compile, zero network, zero tree writes (ledger rows
  land only on the explicit --log path).
Dependencies.  Python 3 standard library only.  The frozen peer `certify/freeze_manifest.py`
  is imported read-only (`md5_bytes`, `tier2_of`; missing peer = fail-loud exit 9); the
  manifest schema is self-owned (`rocqwash-quad8-manifest/1`).
Evidence.  --selftest runs the five fixture judgments over a temporary fixture repository
  (registered-copy passthrough with a PASS ledger row; unregistered refusal rc 8 with a
  REJECT row and no child run; drift refusal rc 8; manifest tier2 tamper refused at load
  rc 2; missing copy fail-loud rc 9).  tests/run_tests.sh case t_frozen_call and
  tests/test_clean_mode.py exercise this face by subprocess.
Exit-codes.  2 = manifest missing, malformed or tier2 broken; 8 = assertion refusal
  (unregistered or drifted); 9 = invoked copy or manifest path missing; otherwise = the
  invoked command's exit code (passthrough, never rewritten).  --selftest: 0 = five
  judgments passing, 1 = failing (assertions fail loud).
"""
import argparse
import io
import json
import os
import subprocess
import sys
from datetime import datetime

PROG = "frozen_call"

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)
DEFAULT_MANIFEST = os.path.join(_HERE, "quad8_manifest.json")
DEFAULT_LOG = ("/Users/apple/Desktop/S系Prop清除战役工单/work_Main_full"
               "/sandbox/seat_rqadapt/账/quad8_call_ledger.jsonl")


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (docs/clean-mode-manual-20261114.md). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"

_CERTDIR = os.path.join(REPO, "certify")
if _CERTDIR not in sys.path:
    sys.path.insert(0, _CERTDIR)
try:
    import freeze_manifest as _v1  # noqa: E402  (frozen in-service peer; imported read-only)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 冻结同侪 certify/freeze_manifest.py 不可导入: %s" % _e,
          file=sys.stderr)
    sys.exit(9)


def load_manifest(path):
    """Load the manifest; enforce the schema and the tier2 prior. Broken -> exit 2 (fail-closed)."""
    if not os.path.isfile(path):
        print("FAIL-LOUD: 名单缺失: %s（先跑 wrapper/quad8_reconcile.py freeze）"
              % path, file=sys.stderr)
        sys.exit(9)
    try:
        with io.open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("schema") != "rocqwash-quad8-manifest/1":
            raise ValueError("schema 不识: %r（期望 rocqwash-quad8-manifest/1）"
                             % doc.get("schema"))
        if not isinstance(doc.get("roots"), dict) or not isinstance(doc.get("tier1"), list):
            raise ValueError("roots/tier1 面缺")
        tier2 = doc.get("tier2_md5_of_tier1_text")
        if _v1.tier2_of([tuple(r) for r in doc["tier1"]]) != tier2:
            raise ValueError("tier2 自洽破（名单被改）")
    except SystemExit:
        raise
    except Exception as e:
        print("FAIL-LOUD: 名单拒入（%s）: %s" % (path, e), file=sys.stderr)
        sys.exit(2)
    return doc


def registered_map(doc):
    """Registered-copy map: {abs_path: (slug/rel, md5)} over the manifest roots."""
    out = {}
    for rel, md5 in doc["tier1"]:
        slug, rpath = rel.split("/", 1)
        root = doc["roots"].get(slug)
        if root is None:
            continue
        out[os.path.abspath(os.path.join(root, rpath))] = (rel, md5)
    return out


def append_log(log_path, record):
    try:
        parent = os.path.dirname(os.path.abspath(log_path))
        os.makedirs(parent, exist_ok=True)
        with io.open(log_path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception as e:  # a ledger write failure must not break the assertion path; report loudly on stderr
        print("frozen_call: 账行写入失败（%s）: %s" % (log_path, e), file=sys.stderr)


def dispatch_argv(copy):
    """Execution mapping: .py -> python3 -B; .sh -> bash; other types exec directly."""
    ext = os.path.splitext(copy)[1].lower()
    if ext == ".py":
        return [sys.executable, "-B", copy]
    if ext == ".sh":
        return ["bash", copy]
    return [copy]


def run_call(args):
    doc = load_manifest(args.manifest)
    reg = registered_map(doc)
    copy = os.path.abspath(args.command[0])
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "manifest": os.path.abspath(args.manifest),
           "manifest_tier2": doc.get("tier2_md5_of_tier1_text"),
           "invoked": copy,
           "argv": list(args.command)}

    def reject(code, reason):
        rec.update({"verdict": "REJECT", "reason": reason})
        append_log(args.log, rec)
        print("frozen_call REJECT(%d): %s\n  invoked: %s" % (code, reason, copy),
              file=sys.stderr)
        sys.exit(code)

    if not os.path.isfile(copy):
        reject(9, "被调副本缺失（fail-loud）")
    hit = reg.get(copy)
    if hit is None:
        reject(8, "被调副本不在册（名单 roots/rel 无此路径——工单路径≠实账路径即此现形）")
    reg_rel, reg_md5 = hit
    with open(copy, "rb") as f:
        live = _v1.md5_bytes(f.read())
    if live != reg_md5:
        reject(8, "副本漂移（在册 %s ≠ 现盘 %s）——拒执禁假绿" % (reg_md5, live))
    rec.update({"verdict": "PASS", "registered": reg_rel, "md5": live,
                "exec": dispatch_argv(copy)})
    append_log(args.log, rec)
    print("frozen_call PASS: %s md5=%s（名单 %s tier2=%s·逐调入账 %s）"
          % (reg_rel, live, os.path.basename(args.manifest),
             doc.get("tier2_md5_of_tier1_text"), args.log), file=sys.stderr)
    argv = dispatch_argv(copy) + list(args.command[1:])
    # os.execv on Windows rebuilds the command line by joining argv with
    # spaces and does not quote it, so an interpreter path containing a space
    # ("C:\Program Files\Python313\python.exe") is split and the child dies
    # on argv[0]="C:\Program". Spawning through the list form keeps the
    # exit-code passthrough without the quoting hazard.
    proc = subprocess.run(argv)
    sys.exit(proc.returncode)


def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_frozen_call_self_")
    try:
        me = os.path.abspath(__file__)
        froot = os.path.join(tmp, "rq")

        def w(rel, content):
            fp = os.path.join(froot, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)

        w("verify/gate4_comment_guard.py",
          "#!/usr/bin/env python3\nprint('CHILD-OK')\n")
        w("other/not_in_list.py", "#!/usr/bin/env python3\nprint('CHILD-OK')\n")
        child = os.path.join(froot, "verify", "gate4_comment_guard.py")
        other = os.path.join(froot, "other", "not_in_list.py")

        def run(argv):
            import subprocess
            p = subprocess.run([sys.executable, "-B", me] + argv,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return (p.returncode, p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))

        # fixture manifest: a real v1-semantics tier2, produced through the peer import
        tier1 = [["rq/verify/gate4_comment_guard.py",
                  _v1.md5_bytes(open(child, "rb").read())]]
        man = os.path.join(tmp, "m.json")
        with io.open(man, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"schema": "rocqwash-quad8-manifest/1",
                       "roots": {"rq": froot}, "n_copies": len(tier1),
                       "tier1": tier1,
                       "tier2_md5_of_tier1_text": _v1.tier2_of([tuple(r) for r in tier1])},
                      fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        log = os.path.join(tmp, "call_ledger.jsonl")

        # judgment 1 PASS: a registered-copy call runs the child command (CHILD-OK on stdout) and the PASS ledger row matches
        rc, so, se = run(["--manifest", man, "--log", log, "--", child])
        assert rc == 0 and "CHILD-OK" in so, \
            "判① 应透传子命令 rc0+stdout 实测 %d\n%s%s" % (rc, so, se)
        lines = [json.loads(l) for l in io.open(log, encoding="utf-8")]
        assert lines[-1]["verdict"] == "PASS" and lines[-1]["md5"] == tier1[0][1] \
            and lines[-1]["registered"] == "rq/verify/gate4_comment_guard.py", lines[-1]
        print("判① PASS 透传＋逐调入账 PASS: rc0·CHILD-OK·账行 PASS 咬合")

        # judgment 2 unregistered refusal: rc 8, REJECT ledger row, child command not run (no CHILD-OK)
        rc, so, se = run(["--manifest", man, "--log", log, "--", other])
        assert rc == 8 and "不在册" in se and "CHILD-OK" not in so, \
            "判② 应拒执 rc8 实测 %d\n%s%s" % (rc, so, se)
        lines = [json.loads(l) for l in io.open(log, encoding="utf-8")]
        assert lines[-1]["verdict"] == "REJECT" and "不在册" in lines[-1]["reason"], lines[-1]
        print("判② 不在册拒执 PASS: rc8·REJECT 账行·子命令未跑")

        # judgment 3 drift refusal: rc 8 (registered-copy bytes modified)
        w("verify/gate4_comment_guard.py",
          "#!/usr/bin/env python3\nprint('CHILD-DRIFT')\n")
        rc, so, se = run(["--manifest", man, "--log", log, "--", child])
        assert rc == 8 and "漂移" in se and "CHILD-DRIFT" not in so, \
            "判③ 应漂移拒执 rc8 实测 %d\n%s%s" % (rc, so, se)
        print("判③ 漂移拒执 PASS: rc8·漂移字节未执行")

        # judgment 4 manifest tier2 tamper: refused at load with rc 2
        bad = json.load(io.open(man, encoding="utf-8"))
        bad["tier1"][0][1] = "0" * 32
        bad_man = os.path.join(tmp, "bad.json")
        with io.open(bad_man, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        w("verify/gate4_comment_guard.py",
          "#!/usr/bin/env python3\nprint('CHILD-OK')\n")
        rc, so, se = run(["--manifest", bad_man, "--log", log, "--", child])
        assert rc == 2 and "tier2" in se, \
            "判④ 应拒入 rc2 实测 %d\n%s%s" % (rc, so, se)
        print("判④ 名单篡改拒入 PASS: rc2·tier2 先验咬合")

        # judgment 5 missing invoked copy: rc 9
        os.remove(child)
        rc, so, se = run(["--manifest", man, "--log", log, "--", child])
        assert rc == 9 and "缺失" in se, \
            "判⑤ 应 fail-loud rc9 实测 %d\n%s%s" % (rc, so, se)
        print("判⑤ 缺失 fail-loud PASS: rc9")

        print("FROZEN-CALL-SELFTEST PASS: 五判绿（PASS 透传入账/不在册拒/漂移拒/"
              "名单篡改拒/缺失 fail-loud）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="wrapper 层逐调断言：在役冻结组件调用前字节身份锁定＋逐调入账")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST,
                    help="四仓对账名单（缺省同仓 wrapper/quad8_manifest.json）")
    ap.add_argument("--log", default=os.environ.get("QUAD8_CALLLOG", DEFAULT_LOG),
                    help="逐调账 JSONL（缺省 seat_rqadapt/账/quad8_call_ledger.jsonl）")
    ap.add_argument("--selftest", action="store_true", help="夹具五判自证")
    ap.add_argument("command", nargs=argparse.REMAINDER,
                    help="-- <被调副本路径> [args...]")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    # Clean mode: the canonical call face is the default in-repo frozen
    # manifest or the canonical effort call log; report and refuse.
    # Explicit --manifest and --log together define a caller-owned face and
    # stay available (the fixture selftest children pass both).
    if _clean_mode() and args.command \
            and (os.path.abspath(args.manifest) == os.path.abspath(DEFAULT_MANIFEST)
                 or os.path.abspath(args.log)
                 == os.path.abspath(os.environ.get("QUAD8_CALLLOG", DEFAULT_LOG))):
        print("requires canonical environment: the default in-repo frozen "
              "manifest or the canonical campaign call log; pass explicit "
              "--manifest and --log for caller-owned faces")
        sys.exit(9)
    cmd = list(args.command)
    if cmd and cmd[0] == "--":  # argparse REMAINDER keeps the leading -- in the list (verified); strip it here
        cmd = cmd[1:]
    if not cmd:
        print("FAIL-LOUD: 用法：frozen_call.py [--manifest M] [--log L] -- "
              "<被调副本路径> [args...]", file=sys.stderr)
        sys.exit(2)
    args.command = cmd
    run_call(args)


if __name__ == "__main__":
    main()
