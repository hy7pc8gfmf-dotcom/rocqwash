#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_magic_check.py - per-file Obj.magic machine check of the gate7 extraction face (rocqwash verify/; ledger entry 10 toolized, November 1, 2026).

Purpose.
    Runs 97/98 washed three files clean, yet their Obj.magic increases (28/4/1 across
    the three) surfaced only at the gate7 extraction-execution gate - too late.  This
    tool is the per-file standard gate of the shape-normalization face: a washed file
    passes it before delivery, and a count over --max (default 0) is red.
Interface.
    python3 verify/extract_magic_check.py --v <file.v> --world <dir> [--max N] [--json
    out.json] [--workdir dir] [--rocq BIN] [--ocamlc BIN] [--timeout SEC] [--selftest].
    Pipeline: parse Separate Extraction targets (decoys masked; no command -> census
    fallback) -> rocq extraction (world .vo read-only, zero world writes) -> ocamlc
    (.mli then .ml, cross-module retry) -> grep -c Obj.magic on the .ml (line counting)
    -> over --max exit 1 with per-line context; --json ledger keys mode/targets/
    rocq_rc/magic_ml/magic_lines/ocamlc/verdict/md5.
Dependencies.
    Python 3 stdlib only; the frozen names/mac_stmt_names.py is imported read-only, its census
    token set extended in place since v15 (DECL_SKIP_EXT below; unknown vernacular still fails
    loud rc=9).  Thermal rule R2: no embedded guard - real runs are guard-wrapped (the
    wrapper/gate7_probe.sh contract form); suite runs on fake rocq/ocamlc stubs, zero real compile.
Evidence.
    --selftest vectors: parsing green/decoy-negative, grep -c counting, context shape,
    driver fallback/word face, E2E red-green on stubs, extraction red, the ocamlc pair,
    CLI four codes, blind-spot completion; suite: tests/test_extract_magic.py.
Exit-codes.
    0 = PASS; 1 = FAIL (three-way conclusion, never simulated: extraction red = rocq
    rc!=0 or <Mod>.ml missing; magic red = count > --max; ocamlc red = present-and-run
    rc!=0, an absent binary = NOT-RUN with the magic face judged independently); 2 =
    usage error; 9 = missing file or binary (compile is never simulated).
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True  # zero __pycache__ on import (no repository writes; per the gate7 probe contract section 2)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "names"))
import mac_stmt_names  # noqa: E402  (read-only import of the frozen file; the extraction core is reused from the same source)

# ------------------------------------------------------------------ (0) blind-spot completion face (v15; first-battle precedent toolized)
# First-battle precedent (ledger v15 section 2, re-audited on this machine): the
# gate7 extraction gate split its four files 2 PASS / 2 fail-loud - G09_MiscSmall's
# `Class` declaration and G13_EvictFam's `Extraction` command both hit unknown
# mac_stmt_names vernacular -> "statement-list anomaly" rc=9 (the gate never even
# reached the magic face).
# The statement-token-set constants live at names/mac_stmt_names.py:38-51
# TARGET_KINDS/SKIP_KINDS - that file is a frozen8 tier1 frozen file (md5 on
# register, triple-pinned at frozen8.py:76 / test_precedent_station.py:35 / the
# quad8 four-repository copy group); its source may not be edited, so this file
# extends it in place at the import face (in-process, zero byte touches to the
# frozen file):
#   declaration face = legal declaration vernacular that produces no extraction
#   products (the task instruction named Class/Record/Context/Schema/Declare/
#   Instance - of these, Record/Context/Declare were already in SKIP_KINDS and
#   Instance already in TARGET_KINDS; the actually missing ones, Class/Schema/
#   Scheme and peers, are completed below);
#   command face = the same blind-spot class as the first battle's second red,
#   G13 `Extraction` (About/Close/Recursive/Separate, same family; verified live
#   in the world at 262/9/102/102 occurrences) - none of them produce extraction
#   products in the census flow (the target set comes only from TARGET_KINDS;
#   zero frozen touches).
# The extraction-masking face is unaffected: the statement lists of the existing
# passing files keep every name; unknown vernacular still fails loud (blind-spot
# narrowing is not silent widening).
DECL_SKIP_EXT = frozenset({
    # declaration face (legal declarations; no extraction products)
    "Class", "Schema", "Scheme", "Structure", "Canonical", "Coercion",
    "Derive", "Existing", "Primitive", "Register",
    # command face (same blind-spot class as the first battle's G13 `Extraction`; verified present in the live world)
    "Extraction", "Recursive", "Separate", "About", "Close",
})
mac_stmt_names.SKIP_KINDS.update(DECL_SKIP_EXT)

PROG = "extract_magic_check"
ROQC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq"
OCAMLC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/ocamlc"
MAGIC_TOKEN = "Obj.magic"
DRIVER_PRELUDE = ("From Stdlib Require Import Extraction.\n"
                  "Require Import %s.\n"
                  "Separate Extraction %s.\n")  # per tools/_gen_fin_mac.py:126, the Stdlib form (avoids the 9.0 deprecation warning)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ (1) parsing face
def parse_separate_extraction(masked):
    """Parse the name groups of every Separate Extraction command in the masked
    text (ordered; every IDENT inside the segment is collected).

    Returns [[name, ...], ...] (one group per command; the all-names-per-command
    rule inherits cw-ci-sop section 1, E law1 - each command resets the output,
    last-write-wins, so multiple targets must be listed in one command).
    """
    cmds = []
    for m in re.finditer(r"\bSeparate\s+Extraction\b", masked):
        seg_end = mac_stmt_names.find_boundary_period(masked, m.end())
        if seg_end < 0:
            seg_end = len(masked)
        seg = masked[m.end():seg_end]
        names = re.findall(mac_stmt_names.IDENT_RE, seg)
        cmds.append(names)
    return cmds


def collect_targets(v_path):
    """Step 1: parse the Separate Extraction targets; with no command, the census
    rule collects every primary definition.

    Returns (mode, targets, extra) - mode is inline/driver; extra carries the
    per-command record or the statement-list record.  Zero primary definitions ->
    fail-loud rc=9 (nothing extractable is not passing; per the _gen_fin_mac rule).
    """
    src = io.open(v_path, encoding="utf-8-sig", errors="replace").read()
    masked = mac_stmt_names.strip_comments_strings(src)
    cmds = parse_separate_extraction(masked)
    if cmds:
        targets, seen = [], set()
        for names in cmds:
            for nm in names:
                if nm not in seen:
                    seen.add(nm)
                    targets.append(nm)
        return "inline", targets, {"commands": cmds}
    inv = mac_stmt_names.extract_statements(v_path)
    if inv["anomalies"]:
        print("FAIL-LOUD: 语句清单异常（fail-loud 逐笔·禁静默）: %s"
              % (inv["anomalies"],), file=sys.stderr)
        sys.exit(9)
    stmts = [s["name"] for s in inv["statements"]]
    if not stmts:
        print("FAIL-LOUD: 零主定义（census 口径无可提取语句）: %s" % v_path,
              file=sys.stderr)
        sys.exit(9)
    return "driver", stmts, {"statements": stmts}


def build_driver_text(module, targets):
    return DRIVER_PRELUDE % (module, " ".join(targets))


# ------------------------------------------------------------------ (3) counting face
def grep_count_magic(path):
    """Equivalent to `grep -c Obj.magic <path>` (line counting: several magics on
    one line count once).

    Returns (count, [hit line numbers...]).
    """
    n = 0
    lines_hit = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            if MAGIC_TOKEN in ln:
                n += 1
                lines_hit.append(i)
    return n, lines_hit


def magic_contexts(path, lines_hit, radius=1):
    """Magic-line context record (hit line +/- radius; the prefix 'L<n>:' marks the hit, '*' the neighbor lines)."""
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        all_lines = fh.read().splitlines()
    out = []
    for ln in lines_hit:
        for j in range(max(1, ln - radius), min(len(all_lines), ln + radius) + 1):
            mark = "L%d:" % j if j == ln else "  *"
            out.append("%-8s %s" % (mark, all_lines[j - 1]))
        if ln != lines_hit[-1]:
            out.append("  --")
    return out


# ------------------------------------------------------------------ (2) compile face
def _run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text="utf-8",
                           errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT after %ss" % timeout
    except OSError as e:
        return -8, "SPAWN-FAIL: %s" % e


def run_extraction(rocq, workdir, v_file, world, timeout):
    """One rocq extraction shot: `rocq c -native-compiler no -q -Q <world> "" <v>` (cwd = the workdir)."""
    cmd = [rocq, "c", "-native-compiler", "no", "-q", "-Q", world, "", v_file]
    return _run(cmd, workdir, timeout)


def ocamlc_face(ocamlc, workdir, main_mod, timeout):
    """ocamlc over the extraction products (the 4b face): per module .mli first,
    then .ml; cross-module dependency retry rounds.

    Returns {"status": pass/fail/NOT-RUN, "binary":..., "units": [...]} - status
    is judged by the main module's <Mod>.ml compiling; an absent binary -> NOT-RUN
    (excused, not counted red).
    """
    if not (os.path.isfile(ocamlc) and os.access(ocamlc, os.X_OK)):
        return {"status": "NOT-RUN", "binary": ocamlc, "units": [],
                "note": "ocamlc 缺卷（4b 让席·显式注记）: %s" % ocamlc}
    mods = sorted(set(f[:-3] for f in os.listdir(workdir) if f.endswith(".ml")))
    units = {m: {"module": m, "mli_rc": None, "rc": None} for m in mods}
    tails = {}
    done, pending = set(), list(mods)
    # Retry rounds: .mli and .ml failures re-enter pending equally - a missing
    # dependency .cmi is completed next round (the Clean.mli opens Datatypes
    # precedent: the mli itself needs a cross-module cmi); stop when a full
    # round completes nothing (the rest = genuinely failing)
    for _round in range(len(mods) + 2):
        if not pending:
            break
        progressed = False
        rest = []
        for m in pending:
            unit = units[m]
            mli = os.path.join(workdir, m + ".mli")
            if os.path.isfile(mli):
                rc_i, _ = _run([ocamlc, "-I", ".", "-c", m + ".mli"], workdir, timeout)
                unit["mli_rc"] = rc_i
                if rc_i != 0:
                    rest.append(m)  # no cmi generated yet; retry next round (self-recovers once the dependency lands)
                    continue
            rc_b, tail_b = _run([ocamlc, "-I", ".", "-c", m + ".ml"], workdir, timeout)
            unit["rc"] = rc_b
            if rc_b == 0:
                done.add(m)
                progressed = True
            else:
                tails[m] = tail_b[-300:]
                rest.append(m)
        pending = rest
        if not progressed:
            break
    status = "pass" if main_mod in done else "fail"
    face = {"status": status, "binary": ocamlc,
            "units": [units[m] for m in mods]}
    if status == "fail" and main_mod in tails:
        face["tail"] = tails[main_mod]
    return face


# ------------------------------------------------------------------ conclusion face
# Division rule: the .vo magic/freshness four-piece set belongs to verify_vo.py; this
# gate covers the extraction face only and never re-runs that set.
def check(v_path, world, max_magic=0, rocq=ROQC_DEFAULT, ocamlc=OCAMLC_DEFAULT,
          timeout=600, workdir=None, keep=False):
    """The full five-step chain.  Returns (exit_code, ledger_dict) - the three-way conclusion is in the module docstring."""
    v_path = os.path.abspath(v_path)
    world = os.path.abspath(world)
    module = os.path.splitext(os.path.basename(v_path))[0]
    mode, targets, extra = collect_targets(v_path)

    tmp_owner = workdir is None
    if tmp_owner:
        workdir = tempfile.mkdtemp(prefix="rocqwash_emc_")
    else:
        os.makedirs(workdir, exist_ok=True)
    try:
        # Compiled precondition: world/<Mod>.vo present (compile first, then check; the gate7 rule)
        vo = os.path.join(world, module + ".vo")
        if not os.path.isfile(vo):
            print("FAIL-LOUD: world 未编译 .vo 缺失: %s（先编后检·本闸不代编译）" % vo,
                  file=sys.stderr)
            return 9, {"module": module, "mode": mode, "targets": targets,
                       "verdict": "FAIL-LOUD-NO-VO", "world": world,
                       "missing_vo": vo}
        if not (os.path.isfile(rocq) and os.access(rocq, os.X_OK)):
            print("FAIL-LOUD: rocq 缺卷（禁模拟编译）: %s（--rocq 覆写）" % rocq,
                  file=sys.stderr)
            return 9, {"module": module, "mode": mode, "targets": targets,
                       "verdict": "FAIL-LOUD-NO-ROCQ", "rocq": rocq}

        # Step 1 draft: the driver form generates a temp draft into the workdir; the
        # inline form copies the source file into the workdir (zero world writes -
        # all products land in the workdir; the world .vo is read-only for Require)
        if mode == "driver":
            drv = os.path.join(workdir, "_%s_emc_driver.v" % module)
            with io.open(drv, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(build_driver_text(module, targets))
            compile_v = "_%s_emc_driver.v" % module
        else:
            drv = None
            compile_v = module + ".v"
            with io.open(os.path.join(workdir, compile_v), "wb") as fh:
                with open(v_path, "rb") as g:
                    fh.write(g.read())

        # Step 2: rocq extraction -> ocamlc over the products
        t0 = time.time()
        rocq_rc, rocq_out = run_extraction(rocq, workdir, compile_v, world, timeout)
        secs = round(time.time() - t0, 1)
        ml = os.path.join(workdir, module + ".ml")
        mli = os.path.join(workdir, module + ".mli")
        ml_exists = os.path.isfile(ml)
        oc = {"status": "NOT-RUN", "binary": ocamlc, "units": [],
              "note": "提取面红·4b 未跑"} if (rocq_rc != 0 or not ml_exists) \
            else ocamlc_face(ocamlc, workdir, module, timeout)

        # Step 3: grep -c Obj.magic (line counting)
        magic_ml, lines_hit = grep_count_magic(ml) if ml_exists else (None, [])
        magic_mli = grep_count_magic(mli)[0] if os.path.isfile(mli) else None
        contexts = magic_contexts(ml, lines_hit) if ml_exists and lines_hit else []
        ml_lines = io.open(ml, encoding="utf-8", errors="replace").read().splitlines() \
            if ml_exists else []

        ledger = {"tool": PROG, "v": v_path, "world": world, "module": module,
                  "mode": mode, "targets": targets,
                  "names_count": len(targets), "commands": extra.get("commands"),
                  "statements": extra.get("statements"),
                  "driver_v": drv, "workdir": workdir,
                  "rocq_rc": rocq_rc, "rocq_secs": secs,
                  "rocq_tail": (rocq_out[-400:] if rocq_rc != 0 else None),
                  "ml": ml if ml_exists else None,
                  "magic_ml": magic_ml, "magic_mli": magic_mli,
                  "magic_lines": [{"line": i, "text": ml_lines[i - 1]}
                                  for i in lines_hit] if ml_exists else [],
                  "max": max_magic, "ocamlc": oc,
                  "md5_v": md5_of(v_path), "md5_vo": md5_of(vo)}

        # Step 4: the three-way conclusion
        reds = []
        if rocq_rc != 0:
            reds.append("提取面红: rocq rc=%s" % rocq_rc)
        elif not ml_exists:
            reds.append("提取面红: <Mod>.ml 未产出（提取静默跳过?）")
        if magic_ml is not None and magic_ml > max_magic:
            reds.append("魔数面红: %d > max %d" % (magic_ml, max_magic))
        if oc["status"] == "fail":
            reds.append("ocamlc 面红: 主模编译不过")
        verdict = "FAIL" if reds else "PASS"
        ledger["verdict"] = verdict
        ledger["reds"] = reds

        print("== extract_magic 账（v=%s mode=%s）==" % (os.path.basename(v_path), mode))
        print("  module            %s" % module)
        print("  targets           %d 名 %s" % (len(targets),
                                                " ".join(targets[:8]) +
                                                (" ..." if len(targets) > 8 else "")))
        print("  rocq_extract      rc=%s (%ss)" % (rocq_rc, secs))
        print("  ocamlc            %s (%d/%d units)"
              % (oc["status"],
                 sum(1 for u in oc["units"] if u["rc"] == 0), len(oc["units"])))
        print("  magic_ml          %s （max=%d）" % (magic_ml, max_magic))
        print("  magic_mli         %s" % magic_mli)
        for r in reds:
            print("  RED: %s" % r)
        if contexts and magic_ml is not None and magic_ml > max_magic:
            print("  -- 魔数行上下文（%s）--" % ml)
            for c in contexts:
                print("  " + c)
        print("md5 v=%s" % ledger["md5_v"])
        print("VERDICT: %s" % verdict)
        return (0 if verdict == "PASS" else 1), ledger
    finally:
        if tmp_owner and not keep:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)


# ------------------------------------------------------------------ selftest
def selftest():
    """Embedded frozen vector set (temp-directory driven; the whole chain on fake
    rocq/ocamlc stubs; zero real compile, zero real-repository touches, real-chain
    E2E stays in the agent sandbox): parsing positive / comment-decoy negative /
    the grep -c counting rule / context shape / fallback primary-definition
    collection / driver draft word face / E2E red-green on stubs / extraction red
    fail-loud / the ocamlc pair / CLI four codes / the Class blind-spot completion
    (first-battle precedent shape, census no longer misjudges; the Frobnicate
    recognized-name F2 regression; unknown vernacular still red 9)."""
    import shutil
    tmp = tempfile.mkdtemp(prefix="rocqwash_emc_self_")
    try:
        # 1 parsing positive: one command with several names, segment boundary containing a period
        masked = "Definition a := 1.\nSeparate Extraction foo bar'x ns_δ. Definition b := 2.\n"
        assert parse_separate_extraction(masked) == [["foo", "bar'x", "ns_δ"]], \
            parse_separate_extraction(masked)
        # 2 comment-decoy negative: commands inside comments are not counted (no trace after stripping)
        v1 = os.path.join(tmp, "decoy.v")
        with io.open(v1, "w", encoding="utf-8") as fh:
            fh.write("(* Separate Extraction decoy_one. *)\n"
                     "Definition real_one := 1.\nSeparate Extraction real_one.\n")
        mode, targets, _ = collect_targets(v1)
        assert mode == "inline" and targets == ["real_one"], (mode, targets)
        # 3 the grep -c counting rule: several magics on one line count once
        ml = os.path.join(tmp, "M.ml")
        with io.open(ml, "w", encoding="utf-8") as fh:
            fh.write("let a = Obj.magic x\nlet b = 1\nlet c = f (Obj.magic y) (Obj.magic z)\n")
        n, hits = grep_count_magic(ml)
        assert (n, hits) == (2, [1, 3]), (n, hits)
        # 4 context shape: the L prefix on the hit line, * on the neighbor lines
        ctx = magic_contexts(ml, [1])
        assert any(x.startswith("L1:") and "Obj.magic x" in x for x in ctx)
        assert not any(x.startswith("L3") for x in ctx)
        # 5 fallback primary-definition collection: the census rule (Lemma counted, Let not, comment decoys not)
        v2 = os.path.join(tmp, "fb.v")
        with io.open(v2, "w", encoding="utf-8") as fh:
            fh.write("(* Definition ghost_in_comment := 0. *)\n"
                     "Definition fb_a := 1.\nLemma fb_l : True. Proof. exact I. Qed.\n"
                     "Let fb_let := 2.\n")
        mode2, targets2, _ = collect_targets(v2)
        assert mode2 == "driver" and targets2 == ["fb_a", "fb_l"], (mode2, targets2)
        # 6 driver draft word face: the Stdlib Extraction prelude + Require + several names in one command
        dt = build_driver_text("FB", ["fb_a", "fb_l"])
        assert "From Stdlib Require Import Extraction." in dt
        assert "Require Import FB." in dt
        assert "Separate Extraction fb_a fb_l." in dt
        # 7 E2E red-green pair (fake rocq/ocamlc stubs; temp world)
        w = os.path.join(tmp, "world")
        os.makedirs(w)
        v3 = os.path.join(w, "Probe.v")
        with io.open(v3, "w", encoding="utf-8") as fh:
            fh.write("Definition p_one := 1.\nDefinition p_two := 2.\n")
        with open(os.path.join(w, "Probe.vo"), "wb") as fh:  # compiled precondition (existence check)
            fh.write(b"FAKEVO")
        mlc = os.path.join(tmp, "canned.ml")
        with io.open(mlc, "w", encoding="utf-8") as fh:
            fh.write("let p_one = Obj.magic (Obj.magic 1)\nlet p_two = Obj.magic 2\n")
        frocq = os.path.join(tmp, "fake_rocq.sh")
        foc = os.path.join(tmp, "fake_oc.sh")
        if os.name == "nt":
            # Windows stub face (the ci.yml known_red precedent "rocq rc=-8
            # observed here": CreateProcess cannot exec shebang scripts) - the same
            # stub logic re-skinned as a .cmd shim plus a python stub (the last-arg
            # walk / the Require Import name strip / the default basename / the
            # EMC_FAKE_ML copy / the EMC_FAKE_RC exit code, each aligned with the
            # bash stub); the conclusion is unchanged, the POSIX branch keeps its bytes.
            frocq_py = os.path.join(tmp, "fake_rocq.py")
            with io.open(frocq_py, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(
                    "import os, shutil, sys\n"
                    "last = None\n"
                    "for a in sys.argv[1:]:\n"
                    "    last = a\n"
                    "mod = ''\n"
                    "if last and os.path.isfile(last):\n"
                    "    with open(last, encoding='utf-8', errors='replace') as fh:\n"
                    "        for ln in fh:\n"
                    "            if ln.startswith('Require Import'):\n"
                    "                mod = ln[len('Require Import '):].strip()\n"
                    "                break\n"
                    "    if mod.endswith('.'):\n"
                    "        mod = mod[:-1]\n"
                    "if not mod:\n"
                    "    mod = os.path.splitext(os.path.basename(last or ''))[0]\n"
                    "mlsrc = os.environ.get('EMC_FAKE_ML')\n"
                    "if mlsrc:\n"
                    "    shutil.copyfile(mlsrc, mod + '.ml')\n"
                    "sys.exit(int(os.environ.get('EMC_FAKE_RC', '0')))\n")
            with io.open(os.path.join(tmp, "fake_rocq.cmd"), "w",
                         encoding="ascii", newline="\r\n") as fh:
                fh.write('@py -B "%~dp0fake_rocq.py" %*\r\n')
            with io.open(os.path.join(tmp, "fake_oc.cmd"), "w",
                         encoding="ascii", newline="\r\n") as fh:
                fh.write("@echo off\r\n"
                         "if not defined EMC_OC_RC set \"EMC_OC_RC=0\"\r\n"
                         "exit /b %EMC_OC_RC%\r\n")
            frocq = os.path.join(tmp, "fake_rocq.cmd")
            foc = os.path.join(tmp, "fake_oc.cmd")
        else:
            with io.open(frocq, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/bash\n"
                         "for last; do :; done\n"
                         "# 真 rocq 形仿：.ml 以被提取模块命名（driver 稿取 Require Import 名；\n"
                         "# inline 稿即本件名）——承 gate7 提取产物 <Mod>.ml 口径\n"
                         "if [ -f \"$last\" ]; then\n"
                         "  mod=\"$(grep -m1 '^Require Import' \"$last\" | sed 's/^Require Import //; s/\\.$//')\"\n"
                         "fi\n"
                         "[ -n \"${mod:-}\" ] || mod=\"$(basename \"$last\" .v)\"\n"
                         "[ -n \"${EMC_FAKE_ML:-}\" ] && cp \"$EMC_FAKE_ML\" \"$mod.ml\"\n"
                         "exit \"${EMC_FAKE_RC:-0}\"\n")
            with io.open(foc, "w", encoding="utf-8") as fh:
                fh.write("#!/bin/bash\nexit \"${EMC_OC_RC:-0}\"\n")
            os.chmod(frocq, 0o755)
            os.chmod(foc, 0o755)
        os.environ["EMC_FAKE_ML"] = mlc
        wd = os.path.join(tmp, "wd")
        # red case: magic 2 > max 1 -> rc 1 fail-loud
        rc = run_args(["--v", v3, "--world", w, "--max", "1",
                       "--workdir", wd, "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "max=1 魔数 2 应红 rc=1 实测 %d" % rc
        rc = run_args(["--v", v3, "--world", w, "--max", "2", "--json",
                       os.path.join(tmp, "acc.json"), "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 0, "max=2 魔数 2 应绿 rc=0 实测 %d" % rc
        acc = json.load(io.open(os.path.join(tmp, "acc.json"), encoding="utf-8"))
        assert acc["verdict"] == "PASS" and acc["magic_ml"] == 2 \
            and acc["mode"] == "driver" and acc["targets"] == ["p_one", "p_two"], acc
        # 8 the driver draft persisted to disk (an explicit --workdir is self-managed, never auto-cleaned)
        drvt = io.open(os.path.join(wd, "_Probe_emc_driver.v"),
                       encoding="utf-8").read()
        assert "Separate Extraction p_one p_two." in drvt, drvt
        # 9 extraction red fail-loud: fake rocq rc=1 -> conclusion FAIL rc=1 (rocq_tail recorded)
        os.environ["EMC_FAKE_RC"] = "1"
        rc = run_args(["--v", v3, "--world", w, "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "提取红应 rc=1 实测 %d" % rc
        os.environ["EMC_FAKE_RC"] = "0"
        # 10 ocamlc face red (present and actually run rc=1) -> FAIL; an absent binary -> NOT-RUN, the magic face judged independently
        os.environ["EMC_OC_RC"] = "1"
        rc = run_args(["--v", v3, "--world", w, "--max", "9", "--workdir", wd,
                       "--rocq", frocq, "--ocamlc", foc])
        assert rc == 1, "ocamlc 红应 rc=1 实测 %d" % rc
        del os.environ["EMC_OC_RC"]
        rc = run_args(["--v", v3, "--world", w, "--max", "9", "--workdir", wd,
                       "--rocq", frocq,
                       "--ocamlc", os.path.join(tmp, "no_such_ocamlc")])
        assert rc == 0, "ocamlc 缺卷应 NOT-RUN 让席·魔数 2≤9 应 rc=0 实测 %d" % rc
        # 11 CLI four codes: --help 0 / unknown flag 2 / missing --world 2 / missing file 9 (missing .v / missing .vo)
        assert run_args(["--help"]) == 0
        assert run_args(["--bogus"]) == 2
        assert run_args(["--v", v3]) == 2
        assert run_args(["--v", os.path.join(tmp, "gone.v"), "--world", w]) == 9
        assert run_args(["--v", v3, "--world", os.path.join(tmp, "noworld")]) == 9
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        assert run_args(["--v", v3, "--world", w2, "--rocq", frocq]) == 9, \
            "world 未编译 .vo 缺失应 rc=9"
        # 12 v15 blind-spot completion (first-battle precedent shape): Class
        #    declarations plus command-face vernacular no longer misjudge the census
        #    as anomalous - declarations/commands stay out of the targets, only real
        #    primary definitions are counted; the Frobnicate recognized-name F2
        #    regression (the November 16, 2026 three-anchor change; the frozen file's
        #    TARGET_KINDS on-register md5 9e26c0db...); unknown vernacular still red 9
        v4 = os.path.join(tmp, "cls.v")
        with io.open(v4, "w", encoding="utf-8") as fh:
            fh.write("Declare Scope req_scope.\n"
                     "Class reqord (R : Set) : Set := mk {\n"
                     "  rord_le_dec : forall a b : R, Or (le a b) (Not (le a b));\n"
                     "  rlt_dec : forall a b : R, Or (lt a b) (Not (lt a b))\n"
                     "}.\n"
                     "Record rstore : Set := mkstore { rs_carrier : Set }.\n"
                     "Scheme reqord_ind := Induction for reqord Sort Prop.\n"
                     "Definition cls_use (x y : reqord nat) := x.\n"
                     "Extraction cls_use.\n"
                     "About cls_use.\n")
        mode4, targets4, extra4 = collect_targets(v4)
        assert mode4 == "driver" and targets4 == ["cls_use"], (mode4, targets4)
        assert extra4["statements"] == ["cls_use"], extra4["statements"]
        # F2 regression of the November 16, 2026 three-anchor change: Frobnicate is
        #   already in the frozen file's TARGET_KINDS (names/mac_stmt_names.py:40;
        #   LEDGER8 on-register md5 9e26c0db2c60ced3629a13a821bdf615) - the census
        #   recognizes the name into the targets (with the Proof body consumed as an
        #   arm), zero anomalies; blind-spot narrowing is not silent widening: the
        #   unknown-vernacular pin now uses the genuinely unknown word Gadgetize and
        #   still fails loud rc=9
        assert "Frobnicate" in mac_stmt_names.TARGET_KINDS, \
            "F2 回归: 冻结件应认 Frobnicate 语句名"
        v6 = os.path.join(tmp, "frob.v")
        with io.open(v6, "w", encoding="utf-8") as fh:
            fh.write("Frobnicate frob_one : nat. Proof. exact 1. Qed.\n"
                     "Definition frob_ok := frob_one.\n")
        mode6, targets6, extra6 = collect_targets(v6)
        assert mode6 == "driver" and targets6 == ["frob_one", "frob_ok"], \
            (mode6, targets6)
        assert extra6["statements"] == ["frob_one", "frob_ok"], extra6["statements"]
        v5 = os.path.join(tmp, "unk.v")
        with io.open(v5, "w", encoding="utf-8") as fh:
            fh.write("Gadgetize widget.\nDefinition unk_ok := 1.\n")
        try:
            collect_targets(v5)
            raise AssertionError("未知 vernacular 应 fail-loud rc=9")
        except SystemExit as e:
            assert e.code == 9, "未知 vernacular 应 rc=9 实测 %r" % (e.code,)
        print("EXTRACT-MAGIC-SELFTEST PASS: 解析正负/注释诱饵/计数grep-c口径/上下文形/"
              "fallback收集/driver稿词面/E2E红绿/提取红/ocamlc双判/CLI四码/"
              "Class盲区补全/Frobnicate认名F2回归 十二判全过")
        return 0
    finally:
        os.environ.pop("EMC_FAKE_ML", None)
        os.environ.pop("EMC_FAKE_RC", None)
        os.environ.pop("EMC_OC_RC", None)
        shutil.rmtree(tmp, ignore_errors=True)


# CLI form follows verify_vo.py: --help = 0; unknown flag / usage error = 2; missing
# --v/--world = 2; missing file (--v / --world / uncompiled world/<Mod>.vo / missing rocq
# binary) = 9 fail-loud (a missing rocq forbids simulated compilation; per the
# wrapper/coqc_shim.sh rule); red = 1.
def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="gate7 提取面 Obj.magic 逐件机检闸（Separate Extraction→rocq 提取→"
                    "ocamlc→grep -c Obj.magic→--max 判红绿）")
    ap.add_argument("--v", default=None, help="源 .v 路径（须已编译出 world/<Mod>.vo）")
    ap.add_argument("--world", default=None, help="世界目录（-Q <world> \"\"·只读）")
    ap.add_argument("--max", type=int, default=0,
                    help="Obj.magic 行计数上限（默认 0·超线 rc=1 fail-loud）")
    ap.add_argument("--json", default=None, help="台账 JSON 出账路径")
    ap.add_argument("--workdir", default=None,
                    help="提取工作目录（缺省临时目录自动清；显式给＝自管不自动清）")
    ap.add_argument("--rocq", default=ROQC_DEFAULT, help="rocq 绝对路径（缺卷 rc=9）")
    ap.add_argument("--ocamlc", default=OCAMLC_DEFAULT,
                    help="ocamlc 绝对路径（缺卷 NOT-RUN 让席不计红）")
    ap.add_argument("--timeout", type=int, default=600, help="子进程超时秒（默认 600）")
    ap.add_argument("--keep", action="store_true",
                    help="缺省临时工作目录不清理（与 --workdir 互斥使用场景）")
    ap.add_argument("--selftest", action="store_true", help="内嵌冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    if not args.v or not args.world:
        ap.error("--v 与 --world 必填（--selftest 除外）")

    for label, path in (("--v", args.v), ("--world", args.world)):
        if not os.path.exists(path):
            print("FAIL-LOUD: %s 路径缺失: %s" % (label, path), file=sys.stderr)
            sys.exit(9)

    rc, ledger = check(v_path=args.v, world=args.world, max_magic=args.max,
                       rocq=args.rocq, ocamlc=args.ocamlc, timeout=args.timeout,
                       workdir=args.workdir, keep=args.keep)
    if rc == 9:
        sys.exit(9)

    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(ledger, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(rc)


if __name__ == "__main__":
    main()
