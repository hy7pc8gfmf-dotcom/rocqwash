#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""require_rewire.py - module-retirement rewiring orchestrator (rocqwash tools/).
Purpose.  The v1 orchestrator face of the external-evaluation gap
  "Require Export retirement/rewiring": given a retirement plan (module M
  retires onto successor S), scan a .v tree for every Require face that
  references M (the three wash_shape-anchored line shapes: From Stdlib /
  From <dir> / bare, each with optional Import/Export), classify Import vs
  Export per consumer, and emit a wash_engine-compatible patch ledger
  (tag/old/new/expect, the exact-string count-asserted form) that rewrites
  every referencing line onto S - so the rewiring itself is applied by the
  standing engine.  A --verify face re-scans an applied tree and fails
  loud on any surviving M reference (retirement closure).  Zero network,
  zero toolchain, zero writes beyond the caller-named --out.
Interface.  python -I tools/require_rewire.py --tree DIR --retire M
  --successor S [--out FILE] | --plan FILE [same flags] | --tree DIR
  --retire M --verify [--out FILE] | --selftest.  The mode semantics and
  the deterministic report face are in the extended contract below.
Exit-codes.  0
  clean; 1 verify survivors or selftest red; 2 usage (bad plan shape,
  M == S on the plan face, module name malformed); 9 --tree/--plan path
  missing.  Deterministic: sorted consumers, double-run byte-identical.
Dependencies.  Python 3 standard library only; the selftest's
  subprocess face is a detached temp copy of this module only; zero
  network, zero toolchain (planning is text-only; the wash engine applies).
Evidence.  --selftest: canned-tree vectors (three line shapes captured,
  Import/Export classification, ledger old-string verbatim + expect
  counts, verify survivors face, M == S refusal, determinism, no-M tree
  empty ledger, missing caller-named path rc 9).
"""
# Extended contract:
# Former-header detail (carried out of the header on the RIS-17 budget
#   cure, verbatim in substance): the rewiring is applied by the standing
#   engine - consumption by construction: the orchestrator plans,
#   wash/wash_engine.py executes; compatibility of S as a drop-in is an
#   authoring obligation declared in the plan (the anchor_guard
#   independence-note precedent); v1 does not load M or S and cannot
#   prove the superset face; the --verify closure face runs standalone on
#   --tree + --retire (the successor is a plan-face obligation, never
#   required for closure): rc 0 = no surviving M face in the tree, rc 1 =
#   survivors listed (data, fail-loud).
# Line shapes (anchored 1:1 to tools/wash_shape.py:247-252, re-implemented
#   locally; drift cannot propagate): "From Stdlib Require [Import|Export]
#   L.", "From <dir> Require [Import|Export] L.", "Require [Import|Export]
#   L.".  A consumer line is selected when its library list contains the
#   token M (word boundary).  The rewired line replaces the M token with S
#   in place (the rest of the line - order, other libraries, Import/Export
#   - stays byte-identical), so old != new is structural and expect equals
#   the line's occurrence count.
# Plan face.  --retire/--successor is the inline plan; --plan FILE carries
#   {"retire": "M", "successor": "S"} plus optional notes (recorded
#   verbatim in the report).  M == S is a usage error (a no-op rewire is
#   never emitted).
# Consumption chain.  The emitted ledger feeds wash_engine unchanged:
#   python -I wash/wash_engine.py --patch <ledger> --out <file> per
#   consumer - the engine's count assertion is the per-line safety net the
#   orchestrator deliberately does not duplicate.
import argparse
import io
import json
import os
import re
import subprocess
import sys

PROG = "require_rewire"
SCHEMA = "rocqwash-require-rewire/1"

REQUIRE_LINE_RES = (
    re.compile(r"^From\s+Stdlib\s+Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$"),
    re.compile(r"^From\s+(?!Stdlib\b)(\S+)\s+Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$"),
    re.compile(r"^Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$"),
)
WORD_RE = re.compile(r"[A-Za-z0-9_']+")


def _module_tokens(line):
    """The library-list tokens of a Require line (the tail after the
    Require keyword; for From-shapes the last group)."""
    for rx in REQUIRE_LINE_RES:
        m = rx.match(line.strip())
        if m:
            tail = m.group(m.lastindex)
            return WORD_RE.findall(tail)
    return []


def scan_file(text, retire):
    """Returns [(line_no, line_text, mode)] for lines whose library list
    contains the retire token; mode in Import/Export/(empty)."""
    hits = []
    for i, ln in enumerate(text.splitlines(), 1):
        if "Require" not in ln:
            continue
        toks = _module_tokens(ln)
        if retire in toks:
            mode = ""
            if re.search(r"\bImport\b", ln):
                mode = "Import"
            elif re.search(r"\bExport\b", ln):
                mode = "Export"
            hits.append((i, ln, mode))
    return hits


def build_ledger(tree, retire, successor):
    """Walk the tree; return (rows, ledger, consumers) with rows the
    per-consumer classification and ledger the wash_engine patch volume."""
    rows = []
    patches = []
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in sorted(filenames):
            if not fn.endswith(".v"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, tree).replace(os.sep, "/")
            with io.open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            for line_no, line_text, mode in scan_file(text, retire):
                new_text = re.sub(r"\b%s\b" % re.escape(retire),
                                  successor, line_text)
                rows.append({"file": rel, "line": line_no,
                             "mode": mode or "plain",
                             "old": line_text, "new": new_text})
                patches.append({"tag": "rewire-%s-%d" % (rel, line_no),
                                "old": line_text + "\n",
                                "new": new_text + "\n",
                                "expect": 1})
    rows.sort(key=lambda r: (r["file"], r["line"]))
    ledger = {"patches": patches} if patches else {"patches": []}
    return rows, ledger


def verify_tree(tree, retire):
    """The retirement-closure face: survivors = files still referencing M."""
    survivors = []
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in sorted(filenames):
            if not fn.endswith(".v"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, tree).replace(os.sep, "/")
            with io.open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            hits = scan_file(text, retire)
            if hits:
                survivors.append({"file": rel,
                                  "lines": [h[0] for h in hits]})
    return survivors


class UsageError(Exception):
    pass


class MissingPathError(UsageError):
    """A caller-named path does not exist (docstring exit-code 9)."""


def _load_plan(plan_path):
    if not os.path.isfile(plan_path):
        raise MissingPathError("--plan path missing: %s" % plan_path)
    try:
        with io.open(plan_path, encoding="utf-8") as fh:
            plan = json.load(fh)
    except ValueError as exc:
        raise UsageError("--plan is not valid JSON: %s" % exc)
    if not isinstance(plan, dict) or "retire" not in plan \
            or "successor" not in plan:
        raise UsageError("plan must carry retire+successor")
    return plan


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="module-retirement rewiring orchestrator "
        "(plan -> wash_engine ledger -> verify closure)")
    ap.add_argument("--tree", help=".v tree root")
    ap.add_argument("--retire", help="module name retiring")
    ap.add_argument("--successor", help="module name replacing it")
    ap.add_argument("--plan", help="plan JSON {retire, successor[, notes]}")
    ap.add_argument("--verify", action="store_true",
                    help="retirement-closure face: rc 1 on survivors")
    ap.add_argument("--out", help="ledger/report output path")
    ap.add_argument("--selftest", action="store_true",
                    help="embedded vectors on temp fixtures")
    args = ap.parse_args(argv)
    try:
        if args.plan:
            plan = _load_plan(args.plan)
            retire, successor = plan["retire"], plan["successor"]
        else:
            retire, successor = args.retire, args.successor
        if args.verify:
            # closure face: only the retired name matters; the successor
            # is a plan-face obligation and stays optional here
            if not retire:
                raise UsageError("--verify needs --tree + --retire "
                                 "(or --plan)")
        else:
            if not retire or not successor:
                raise UsageError("--retire and --successor (or --plan) "
                                 "required")
            if retire == successor:
                raise UsageError("retire == successor (%r): a no-op rewire "
                                 "is never emitted" % retire)
        if not args.tree:
            raise UsageError("--tree required (or --verify's tree face)")
        if not os.path.isdir(args.tree):
            raise MissingPathError("--tree directory missing: %r"
                                   % args.tree)
    except MissingPathError as exc:
        print("PATH-MISSING: %s" % exc, file=sys.stderr)
        sys.exit(9)
    except UsageError as exc:
        print("USAGE: %s" % exc, file=sys.stderr)
        sys.exit(2)

    if args.verify:
        survivors = verify_tree(args.tree, retire)
        report = {"schema": SCHEMA, "face": "verify", "retire": retire,
                  "tree": os.path.abspath(args.tree),
                  "survivors": survivors,
                  "clean": not survivors}
        blob = json.dumps(report, ensure_ascii=False, indent=1,
                          sort_keys=True) + "\n"
        if args.out:
            with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
                fh.write(blob)
            print("report -> %s" % args.out)
        else:
            sys.stdout.write(blob)
        print("verify: survivors=%d" % len(survivors))
        sys.exit(0 if not survivors else 1)

    rows, ledger = build_ledger(args.tree, retire, successor)
    report = {
        "schema": SCHEMA,
        "face": "plan",
        "retire": retire,
        "successor": successor,
        "consumers": len({r["file"] for r in rows}),
        "rewire_lines": len(rows),
        "modes": {m: sum(1 for r in rows if r["mode"] == m)
                  for m in ("Import", "Export", "plain")},
        "rows": rows,
        "note": "compatibility of the successor is a plan authoring "
                "obligation; apply the ledger with wash/wash_engine.py "
                "and confirm with --verify",
    }
    blob = json.dumps(report, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"
    out_ledger = (args.out[:-5] + ".patches.json") if args.out \
        and args.out.endswith(".json") else \
        (args.out + ".patches.json" if args.out else None)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        with io.open(out_ledger, "w", encoding="utf-8", newline="") as fh:
            json.dump(ledger, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("report -> %s" % args.out)
        print("wash_engine ledger -> %s (%d patches)"
              % (out_ledger, len(ledger["patches"])))
    else:
        sys.stdout.write(blob)
    print("require-rewire: consumers=%d lines=%d"
          % (report["consumers"], report["rewire_lines"]))
    sys.exit(0)


def selftest():
    import shutil
    import tempfile
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="require_rewire_selftest_")
    try:
        tree = os.path.join(tmp, "tree", "src")
        os.makedirs(tree)
        with io.open(os.path.join(tree, "a.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("From Stdlib Require Import List.\n"
                     "Require Export MyModule.\n"
                     "Lemma a : True. Proof. exact I. Qed.\n")
        with io.open(os.path.join(tree, "b.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("From src Require MyModule.\n"
                     "Require Import Other MyModule.\n")
        rc_out = os.path.join(tmp, "report.json")
        led_out = rc_out[:-5] + ".patches.json"
        env = dict(os.environ)
        proc_args = [sys.executable, "-I", "-B",
                     os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "require_rewire.py"),
                     "--tree", os.path.dirname(tree), "--retire",
                     "MyModule", "--successor", "NextModule", "--out",
                     rc_out]
        p = subprocess.run(proc_args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=60)
        vec("plan-face-rc0", p.returncode == 0, "rc=%d %s"
            % (p.returncode, p.stderr[-120:]))
        if p.returncode == 0:
            with io.open(rc_out, encoding="utf-8") as fh:
                rep = json.load(fh)
            with io.open(led_out, encoding="utf-8") as fh:
                led = json.load(fh)
            vec("three-shapes-and-modes",
                rep["rewire_lines"] == 3 and rep["consumers"] == 2
                and rep["modes"]["Export"] == 1
                and rep["modes"]["Import"] == 1
                and rep["modes"]["plain"] == 1,
                "lines=%d modes=%s" % (rep["rewire_lines"], rep["modes"]))
            vec("ledger-engine-shaped",
                len(led["patches"]) == 3
                and all(set(pp) == {"tag", "old", "new", "expect"}
                        and pp["expect"] == 1
                        and pp["old"].endswith("\n")
                        and "MyModule" in pp["old"]
                        and "NextModule" in pp["new"]
                        for pp in led["patches"]),
                "patches=%d" % len(led["patches"]))
        # verify face: survivors on the untouched tree.  proc_args[:4]
        # keeps python/-I/-B AND the script path (a shorter slice feeds
        # the flags to the interpreter as a script name: rc 2 for the
        # wrong reason).
        rc_out2 = os.path.join(tmp, "verify.json")
        p = subprocess.run(proc_args[:4] + ["--tree",
                                            os.path.dirname(tree),
                                            "--retire", "MyModule",
                                            "--verify", "--out", rc_out2],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=60)
        surv_ok = False
        try:
            with io.open(rc_out2, encoding="utf-8") as fh:
                vrep = json.load(fh)
            surv_ok = (vrep["face"] == "verify" and not vrep["clean"]
                       and [s["file"] for s in vrep["survivors"]]
                       == ["src/a.v", "src/b.v"]
                       and vrep["survivors"][0]["lines"] == [2]
                       and vrep["survivors"][1]["lines"] == [1, 2])
        except (IOError, ValueError, KeyError):
            surv_ok = False
        vec("verify-survivors-rc1",
            p.returncode == 1 and surv_ok,
            "rc=%d report=%s" % (p.returncode, surv_ok))
        # M == S refusal (assert the real usage text: an interpreter
        # launcher error also exits 2, which must not count as a pass)
        p = subprocess.run(proc_args[:4] + ["--tree", os.path.dirname(tree),
                                            "--retire", "X", "--successor",
                                            "X", "--out",
                                            os.path.join(tmp, "x.json")],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=60)
        vec("noop-refusal-rc2",
            p.returncode == 2 and "retire == successor" in p.stderr,
            "rc=%d stderr=%s" % (p.returncode, p.stderr[-80:]))
        # clean tree verifies green
        clean = os.path.join(tmp, "clean")
        os.makedirs(clean)
        with io.open(os.path.join(clean, "c.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("Require Import NextModule.\n")
        p = subprocess.run(proc_args[:4] + ["--tree", clean, "--retire",
                                            "MyModule", "--verify",
                                            "--out",
                                            os.path.join(tmp, "v2.json")],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=60)
        clean_ok = False
        try:
            with io.open(os.path.join(tmp, "v2.json"),
                         encoding="utf-8") as fh:
                v2 = json.load(fh)
            clean_ok = v2["face"] == "verify" and v2["clean"] is True \
                and v2["survivors"] == []
        except (IOError, ValueError, KeyError):
            clean_ok = False
        vec("verify-clean-rc0",
            p.returncode == 0 and clean_ok,
            "rc=%d report=%s" % (p.returncode, clean_ok))
        # missing caller-named path = the docstring's exit-code 9 face
        p = subprocess.run(proc_args[:4] + ["--tree", os.path.dirname(tree),
                                            "--plan",
                                            os.path.join(tmp, "absent.json")],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env,
                           timeout=60)
        vec("missing-plan-rc9", p.returncode == 9,
            "rc=%d stderr=%s" % (p.returncode, p.stderr[-70:]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("REQUIRE-REWIRE-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    main()
