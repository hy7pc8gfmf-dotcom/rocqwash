#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_extract_magic.py - selftest for verify/extract_magic_check.py, the
per-file Obj.magic check of the gate7 extraction face (tests/; eleven
sections, numbered by execution order).

Purpose.  Machine-checks the Obj.magic extraction gate end to end on
  stubbed toolchains: tool selftest; E2E failing/passing with the --json
  ledger interlocked; inline and driver target collection; extraction
  failure and missing-.ml fail-loud paths; the ocamlc face; the four CLI
  exit codes; the grep -c counting rule; and the blind-spot completions
  (Class fixtures, DECL_SKIP_EXT, bare `Extraction`, unknown vernacular).
Interface.  Drives `verify/extract_magic_check.py` as a python -B
  subprocess with --selftest and the full E2E flag set (--v, --world,
  --workdir, --json, --max, --rocq, --ocamlc) against fake rocq/ocamlc
  stub programs and mini worlds under a temp directory; the in-repo
  fixture names_sample.v is read-only (driver fallback).
Dependencies.  Python 3 standard library only; zero real compilation,
  zero network, zero external-repository touches; -B keeps __pycache__
  off and the temp stage is removed in finally.
Evidence.  Each section asserts rc plus VERDICT lines; the --json ledger
  fields verdict/magic_ml/mode/targets/md5_v; the driver source on disk;
  the grep_count_magic pair (2 lines, hits [1, 3]); the 15 DECL_SKIP_EXT
  tokens inside mac_stmt_names.SKIP_KINDS; fail-loud rc 9 on unknown
  vernacular.  Five assertions pin the tool's runtime word faces
  verbatim (registered corpus: tests/i18n_output_strings_census.md).
Exit-codes.  0 = all eleven sections pass; 1 = any red, each listed on
  stdout (never silent).
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "verify", "extract_magic_check.py")
NAMES_SAMPLE = os.path.join(REPO, "tests", "fixtures", "names_sample.v")

_spec = importlib.util.spec_from_file_location("emc_tool", TOOL)
emc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emc)

CANNED_ML = ("let p_one = Obj.magic (Obj.magic 1)\n"
             "let p_two = Obj.magic 2\n")
SAMPLE_NAMES = ["ns_succ", "ns_succ_ge", "ns_compose", "ns_add",
                "ns_natle_proper", "ns_δ运输", "ns_ex"]


def run(args, env=None):
    e = dict(os.environ)
    # Pin the child I/O encoding: the sections below judge CJK strings
    # emitted by the tool, so the bytes must not depend on the codepage of
    # whichever shell invoked this test (the suite entry point pins the
    # same pair for the same reason; this keeps direct invocation equally
    # deterministic).
    e["PYTHONUTF8"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=e)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(dirpath, name, text):
    fp = os.path.join(dirpath, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


# One stub source serves both fake tools; the role is picked from argv[0]
# (fake_rocq -> fake extraction, fake_oc -> fake compile).  Injection works
# through the environment, with the same meaning the earlier POSIX shell
# stubs gave the same variables:
#   EMC_FAKE_ML  canned .ml to copy next to the module name; empty or unset
#                copies nothing, so the tool reports the missing artifact
#   EMC_FAKE_RC  exit code of the fake extraction; nonzero also prints one
#                error line so the tool's rocq_tail stays non-empty
#   EMC_OC_RC    exit code of the fake compile step
STUB_SOURCE = (
    "import os\n"
    "import shutil\n"
    "import sys\n"
    "\n"
    "\n"
    "def main():\n"
    "    if 'fake_oc' in os.path.basename(sys.argv[0]):\n"
    "        return int(os.environ.get('EMC_OC_RC', '0'))\n"
    "    last = None\n"
    "    for a in sys.argv[1:]:\n"
    "        last = a\n"
    "    mod = ''\n"
    "    if last and os.path.isfile(last):\n"
    "        with open(last, encoding='utf-8', errors='replace') as fh:\n"
    "            for ln in fh:\n"
    "                if ln.startswith('Require Import'):\n"
    "                    mod = ln[len('Require Import '):].strip()\n"
    "                    break\n"
    "        if mod.endswith('.'):\n"
    "            mod = mod[:-1]\n"
    "    if not mod:\n"
    "        mod = os.path.splitext(os.path.basename(last or ''))[0]\n"
    "    mlsrc = os.environ.get('EMC_FAKE_ML')\n"
    "    if mlsrc:\n"
    "        shutil.copyfile(mlsrc, mod + '.ml')\n"
    "    rc = int(os.environ.get('EMC_FAKE_RC', '0'))\n"
    "    if rc != 0:\n"
    "        sys.stderr.write('Error: fake rocq blew up\\n')\n"
    "    return rc\n"
    "\n"
    "\n"
    "if __name__ == '__main__':\n"
    "    sys.exit(main())\n"
)


def make_stage(tmp, tag, v_text):
    """Mini world (Probe.v plus a placeholder .vo) plus the fake rocq/ocamlc
    stubs (the whole chain runs without any real compile).  The stub logic is
    one interpreter-agnostic python source; the platform glue only decides
    how the tool's single-path spawn face reaches it: POSIX execs the stub
    directly through a sys.executable shebang, Windows reaches the same
    source through a one-line .cmd shim, because CreateProcess cannot exec
    shebang scripts."""
    stage = os.path.join(tmp, tag)
    world = os.path.join(stage, "world")
    os.makedirs(world)
    v_path = wf(world, "Probe.v", v_text)
    with open(os.path.join(world, "Probe.vo"), "wb") as fh:
        fh.write(b"FAKE-VO-PLACEHOLDER")
    canned = wf(stage, "canned.ml", CANNED_ML)
    stubs = {}
    for role in ("fake_rocq", "fake_oc"):
        stub = os.path.join(stage, role + ".py")
        shebang = ("#!%s\n" % sys.executable) if os.name != "nt" else ""
        with io.open(stub, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(shebang + STUB_SOURCE)
        if os.name != "nt":
            os.chmod(stub, 0o755)
            stubs[role] = stub
        else:
            shim = os.path.join(stage, role + ".cmd")
            with io.open(shim, "w", encoding="ascii", newline="\r\n") as fh:
                fh.write('@"%s" -B "%%~dp0%s.py" %%*\r\n' % (sys.executable, role))
            stubs[role] = shim
    return stage, world, v_path, canned, stubs["fake_rocq"], stubs["fake_oc"]


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_textractmagic_")
    try:
        # Section 1: the tool's --selftest (its own built-in vectors).
        rc, out = run(["--selftest"])
        check("selftest", rc == 0 and "PASS" in out, "rc=%d %s" % (rc, out[-300:]))

        # Sections 2+3+4: the E2E trio (failing / passing with the --json
        # ledger interlocked / the inline form) over the fake-stub chain,
        # zero real compile.  The magic-context word-face assertion pins
        # the tool's runtime wording verbatim (that module is outside this
        # suite's edit scope).
        stage, world, v_path, canned, frocq, foc = make_stage(
            tmp, "s1", "Definition p_one := 1.\nDefinition p_two := 2.\n")
        wd = os.path.join(stage, "wd")
        acc = os.path.join(tmp, "acc_red.json")
        rc, out = run(["--v", v_path, "--world", world, "--workdir", wd,
                       "--json", acc, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        check("e2e_red_default_max0", rc == 1 and "VERDICT: FAIL" in out
              and "魔数行上下文" in out and "L1:" in out and "L2:" in out,
              "rc=%d" % rc)
        acc_j = json.load(io.open(acc, encoding="utf-8"))
        check("e2e_red_ledger_interlock", acc_j["verdict"] == "FAIL" and acc_j["magic_ml"] == 2
              and acc_j["max"] == 0 and len(acc_j["magic_lines"]) == 2
              and acc_j["ocamlc"]["status"] == "pass", repr(acc_j["verdict"]))
        acc2 = os.path.join(tmp, "acc_green.json")
        rc, out = run(["--v", v_path, "--world", world, "--max", "2", "--workdir", wd,
                       "--json", acc2, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        g_j = json.load(io.open(acc2, encoding="utf-8"))
        check("e2e_green_max2", rc == 0 and "VERDICT: PASS" in out
              and g_j["verdict"] == "PASS" and g_j["magic_ml"] == 2
              and g_j["mode"] == "driver"
              and g_j["targets"] == ["p_one", "p_two"],
              "rc=%d" % rc)
        check("md5_v_on_ledger", os.path.isfile(v_path)
              and g_j["md5_v"] == emc.md5_of(v_path), g_j["md5_v"])
        # Section 4: the inline form (.v carries its own Separate
        # Extraction, plus the Extraction Require line).
        stage2, world2, v_inline, canned2, frocq2, foc2 = make_stage(
            tmp, "s2",
            "From Stdlib Require Import Extraction.\n"
            "Definition i_a := 1.\nDefinition i_b := 2.\n"
            "Separate Extraction i_a i_b.\n")
        acc3 = os.path.join(tmp, "acc_inline.json")
        rc, out = run(["--v", v_inline, "--world", world2, "--max", "2",
                       "--json", acc3, "--rocq", frocq2, "--ocamlc", foc2],
                      env={"EMC_FAKE_ML": canned2})
        i_j = json.load(io.open(acc3, encoding="utf-8"))
        check("inline_form", rc == 0 and i_j["mode"] == "inline"
              and i_j["targets"] == ["i_a", "i_b"]
              and i_j["commands"] == [["i_a", "i_b"]], "rc=%d" % rc)

        # Section 5: the driver form over the in-repo minimal sample
        # names_sample.v (census 7 names; the Unicode name is kept verbatim
        # from the fixture file).
        stage3 = os.path.join(tmp, "s3")
        world3 = os.path.join(stage3, "world")
        os.makedirs(world3)
        shutil.copyfile(NAMES_SAMPLE, os.path.join(world3, "names_sample.v"))
        with open(os.path.join(world3, "names_sample.vo"), "wb") as fh:
            fh.write(b"FAKE-VO-PLACEHOLDER")
        wd3 = os.path.join(stage3, "wd")
        acc4 = os.path.join(tmp, "acc_names.json")
        rc, out = run(["--v", os.path.join(world3, "names_sample.v"),
                       "--world", world3, "--max", "0", "--workdir", wd3,
                       "--json", acc4, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned})
        n_j = json.load(io.open(acc4, encoding="utf-8"))
        drv_txt = io.open(os.path.join(wd3, "_names_sample_emc_driver.v"),
                          encoding="utf-8").read()
        check("driver_form_sample7", rc == 1 and n_j["mode"] == "driver"
              and n_j["targets"] == SAMPLE_NAMES, "rc=%d %s" % (rc, n_j["targets"]))
        check("driver_word_face", "From Stdlib Require Import Extraction." in drv_txt
              and "Require Import names_sample." in drv_txt
              and "Separate Extraction " + " ".join(SAMPLE_NAMES) + "." in drv_txt,
              drv_txt)

        # Section 6: extraction red, fake rocq rc=1 fails loud with rc 1 and
        # rocq_tail on the ledger.  The extraction-red word-face assertion
        # pins the tool's runtime wording verbatim.
        acc5 = os.path.join(tmp, "acc_rocqred.json")
        rc, out = run(["--v", v_path, "--world", world, "--json", acc5,
                       "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned, "EMC_FAKE_RC": "1"})
        r_j = json.load(io.open(acc5, encoding="utf-8"))
        check("extraction_red", rc == 1 and "提取面红" in out
              and r_j["rocq_rc"] == 1 and r_j["rocq_tail"], "rc=%d" % rc)

        # Section 7: the .ml not produced, fake rocq rc=0 without the
        # artifact fails with rc 1 (uncountable is never passing).  The
        # missing-artifact word-face assertion pins the tool's runtime
        # wording verbatim.
        rc, out = run(["--v", v_path, "--world", world, "--rocq", frocq,
                       "--ocamlc", foc], env={"EMC_FAKE_ML": ""})
        check("ml_missing_red", rc == 1 and "未产出" in out, "rc=%d" % rc)

        # Section 8: the ocamlc pair, a real-fail run is red with rc 1; the
        # absent binary is NOT-RUN (the magic count judges independently).
        acc6 = os.path.join(tmp, "acc_ocred.json")
        rc, out = run(["--v", v_path, "--world", world, "--max", "9",
                       "--json", acc6, "--rocq", frocq, "--ocamlc", foc],
                      env={"EMC_FAKE_ML": canned, "EMC_OC_RC": "1"})
        o_j = json.load(io.open(acc6, encoding="utf-8"))
        check("ocamlc_red", rc == 1 and o_j["ocamlc"]["status"] == "fail"
              and o_j["magic_ml"] == 2, "rc=%d" % rc)
        rc, out = run(["--v", v_path, "--world", world, "--max", "9",
                       "--rocq", frocq,
                       "--ocamlc", os.path.join(tmp, "no_such_ocamlc")],
                      env={"EMC_FAKE_ML": canned})
        check("ocamlc_absent_notrun", rc == 0 and "NOT-RUN" in out, "rc=%d" % rc)

        # Section 9: the CLI four-code contract (--help 0 / unknown flag 2 /
        # missing --world 2 / missing file 9).  The vo-uncompiled
        # word-face assertion pins the tool's runtime wording verbatim.
        rc, out = run(["--help"])
        check("cli_help0", rc == 0 and "usage" in out, "rc=%d" % rc)
        rc, out = run(["--bogus"])
        check("cli_unknown_flag_2", rc == 2, "rc=%d" % rc)
        rc, out = run(["--v", v_path])
        check("cli_missing_world_2", rc == 2, "rc=%d" % rc)
        rc, out = run(["--v", os.path.join(tmp, "gone.v"), "--world", world])
        check("cli_missing_v_9", rc == 9, "rc=%d" % rc)
        empty_world = os.path.join(tmp, "empty_world")
        os.makedirs(empty_world)
        rc, out = run(["--v", v_path, "--world", empty_world])
        check("cli_vo_uncompiled_9", rc == 9 and "先编后检" in out, "rc=%d" % rc)

        # Section 10: the counting semantics, grep -c (line counting;
        # several magics on one line count once), module-level interlock.
        mlf = os.path.join(tmp, "M.ml")
        wf(tmp, "M.ml", "let a = Obj.magic x\nlet b = 1\n"
                        "let c = f (Obj.magic y) (Obj.magic z)\n")
        n, hits = emc.grep_count_magic(mlf)
        check("grep_c_semantics", (n, hits) == (2, [1, 3]), "%s %s" % (n, hits))

        # Section 11: the blind-spot completion (the first-battle precedent:
        # gate7's four files split 2 PASS / 2 Class blind-spot fail-loud).
        # Class/Record declaration fixtures no longer break the census:
        # declaration and command vernacular stay out of the targets, only
        # real primary definitions are counted; DECL_SKIP_EXT is
        # registered; unknown vernacular still fails loud with rc=9.  The
        # statement-list word-face assertion pins the tool's runtime
        # wording verbatim.
        cls_fixture = (
            "Declare Scope req_scope.\n"
            "Class reqord (R : Set) : Set := mk {\n"
            "  rord_le_dec : forall a b : R, Or (le a b) (Not (le a b));\n"
            "  rlt_dec : forall a b : R, Or (lt a b) (Not (lt a b))\n"
            "}.\n"
            "Record rstore : Set := mkstore { rs_carrier : Set }.\n"
            "Scheme reqord_ind := Induction for reqord Sort Prop.\n"
            "Canonical req_can : reqord := reqord_rect.\n"
            "Section s1.\n"
            "Context {R : Set} {DO : reqord R}.\n"
            "Variable tok : R.\n"
            "Definition cls_pick (x y : R) : R := x.\n"
            "Instance req_inst : reqord nat.\n"
            "Extraction cls_pick.\n"
            "About cls_pick.\n"
            "Close Scope req_scope.\n"
            "End s1.\n")
        stage4, world4, v_cls, _, frocq4, foc4 = make_stage(tmp, "s4", cls_fixture)
        acc7 = os.path.join(tmp, "acc_cls.json")
        rc, out = run(["--v", v_cls, "--world", world4, "--max", "2", "--json", acc7,
                       "--rocq", frocq4, "--ocamlc", foc4],
                      env={"EMC_FAKE_ML": canned})
        c_j = json.load(io.open(acc7, encoding="utf-8"))
        check("class_fixture_e2e_green", rc == 0 and "VERDICT: PASS" in out
              and "语句清单异常" not in out and c_j["verdict"] == "PASS",
              "rc=%d %s" % (rc, out[-200:]))
        check("class_fixture_ledger", c_j["mode"] == "driver"
              and c_j["targets"] == ["cls_pick", "req_inst"]
              and c_j["statements"] == ["cls_pick", "req_inst"]
              and "reqord" not in c_j["targets"] and "rstore" not in c_j["targets"],
              repr(c_j["targets"]))
        check("blindspot_registry_15", len(emc.DECL_SKIP_EXT) == 15
              and all(t in emc.mac_stmt_names.SKIP_KINDS for t in emc.DECL_SKIP_EXT),
              sorted(emc.DECL_SKIP_EXT))
        # The G13 form (the second first-battle red token): a bare
        # Extraction command no longer breaks the census.
        g13 = wf(tmp, "g13.v", "Definition g_a := 1.\nExtraction g_a.\n")
        m5, t5, _ = emc.collect_targets(g13)
        check("g13_extraction_command", m5 == "driver" and t5 == ["g_a"],
              "%s %s" % (m5, t5))
        # Blind-spot narrowing is not silent widening: unknown vernacular
        # still fails loud with rc=9.
        unk = wf(tmp, "unk.v", "Bogonize widget.\nDefinition unk_ok := 1.\n")
        try:
            emc.collect_targets(unk)
            check("unknown_still_red_9", False, "SystemExit not raised")
        except SystemExit as e:
            check("unknown_still_red_9", e.code == 9, "code=%r" % (e.code,))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-24s %s %s" % (name, "PASS" if ok else "FAIL",
                                     detail if not ok else ""))
        if fails:
            print("TEST-EXTRACT-MAGIC FAIL: %d/%d red"
                  % (len(fails), len(checks)))
            return 1
        print("TEST-EXTRACT-MAGIC PASS: selftest / E2E red-green with ledger "
              "interlock / inline form / driver form over the 7-name sample "
              "with word face / extraction red / missing ml red / ocamlc red "
              "plus absent-binary NOT-RUN / CLI four codes / grep-c semantics "
              "/ blind-spot completion class fixture: all eleven sections "
              "green")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
