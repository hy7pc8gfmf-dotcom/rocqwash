#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_anchor_guard_shape.py - tests/ suite shell for tools/anchor_guard.py.
Purpose.  Hook the anchor and certificate guard into the tests/ tree and
  smoke its shape offline: the CLI faces, the exit-code matrix, the
  manifest validation rules driven through the module's own loader, and
  the companion mutation library volume.  Run directly; rostered in
  tests/run_tests.sh as t_anchor_guard_shape at the count-face cures
  increment (November 26, 2026, branch supply/count-face-cures-20261125),
  which owned the README count-line rewrite the earlier
  deliberate-not-rostered note deferred to.  Where the toolchain binaries are absent the guard
  honestly skips and this shell asserts the skip face itself.
Interface.  `python -I tests/t_anchor_guard_shape.py`.  Six checks; the
  check list and the vector names are the extended contract below.
Dependencies.  Python 3 stdlib only; the inspected tool is stdlib-only;
  every check runs on temporary fixtures or nonexistent scratch paths;
  nothing in the repository is written; zero network.
Evidence.  Every check asserts the exit code and the output face on this
  machine; the validation vectors raise through the tool's own loader,
  never through a re-implementation.
Exit-codes.  0 = all six checks pass; 1 = any check red (fail-loud, the
  red check is printed; no silent downgrade).
"""
# Extended contract (moved from the docstring to hold the 30-line header
# budget).  The six checks: (1) --selftest rc in {0, 111} with rc 111
#   carrying the SKIP line (rc 2 or 9 is a tier-a failure and reds this
#   shell); (2) --help rc=0 naming the seven flags and never listing
#   --selftest (dispatched pre-argparse); (3) exit-code spot checks on
#   scratch paths only (--selftest combined with another flag 2, --bogus
#   2, --repo on an absent directory 9 before any toolchain judgment,
#   unconfigured toolchain honest skip 111, configured but nonexistent
#   binary path 9); (4) manifest validation vectors through the imported
#   module (a valid manifest loads; six malformed manifests raise
#   UsageError: bad schema string, duplicate anchor name, corner set
#   missing boundary, mutant class build, unclosed replacement group,
#   dangling backreference); (5) the companion library
#   tools/mutants-v1.json reads schema rocqwash.mutants/1 and every entry
#   passes the guard's own replacement-compile and backreference rules;
#   (6) frozen shape constants (report schema rocqwash-anchor-guard/1,
#   report volume anchor-guard-report.json) and the zero-network import
#   face.  The toolchain tier (rocq compile, coqchk recheck) needs
#   configured binaries and is the tool's own --selftest face, not this
#   shell's.
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "anchor_guard.py")
LIBRARY = os.path.join(REPO, "tools", "mutants-v1.json")
FLAGS = ("--repo", "--manifest", "--out", "--rocq", "--coqchk",
         "--timeout", "--keep")

MODULE_V = """Require Import QArith_base.

Theorem t_anchor_small : True.
Proof. exact I. Qed.

Definition d_cert_bound : nat := 1.
"""


def run(args, env_extra=None):
    """Run the tool in a subprocess (stdout+stderr merged)."""
    env = dict(os.environ)
    env.pop("ROCWASH_ROCQ", None)
    env.pop("ROCWASH_COQCHK", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", TOOL]
                       + args, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, cwd=REPO, env=env)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def write_json(path, obj):
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return path


def valid_manifest(repo_dir, name="good.json"):
    return write_json(os.path.join(repo_dir, name), {
        "schema": "rocqwash.anchor/1",
        "module": "synth_mod.v",
        "anchors": [{
            "name": "a_bound",
            "referent": "t_anchor_small",
            "certificate_face": "d_cert_bound",
            "sample_points": [
                {"label": "zero", "corner": "smallest",
                 "check": "Nat.le 0 0"},
                {"label": "one", "corner": "boundary",
                 "check": "Nat.le 0 1"},
            ],
            "independent_derivation": "independent tail estimate",
        }],
        "mutants": [{
            "id": "OB1-001",
            "class": "semantic",
            "pattern": "rcp (2 * k + 1)",
            "replacement": r"rcp \(2 \* k\)",
            "evidence": "the odd series term pairs the reciprocal with 2 * k",
        }],
    })


def main():
    fails = []
    ag = None

    # Check 1: the tool's own vector suite attests green (tier a always
    # runs; the toolchain tier may honestly skip where binaries are
    # unconfigured).
    rc, out = run(["--selftest"])
    if rc not in (0, 111):
        fails.append("check1 --selftest should be rc 0 or 111, got %d\n%s"
                     % (rc, out))
    if rc == 111 and "SKIP" not in out:
        fails.append("check1 rc 111 must carry the SKIP line\n%s" % out)

    # Check 2: --help is a clean usage face naming the seven flags and
    # never listing --selftest (it is dispatched before argparse).
    rc, out = run(["--help"])
    flat = re.sub(r"-\s*\n\s*", "-", out)
    if rc != 0:
        fails.append("check2 --help should be rc=0 (rc=%d)\n%s" % (rc, out))
    for flag in FLAGS:
        if flag not in flat:
            fails.append("check2 --help should name %s\n%s" % (flag, flat))
    if "--selftest" in flat:
        fails.append("check2 --help must not list --selftest (pre-argparse "
                     "dispatch)\n%s" % flat)

    # Check 3: exit-code spot checks on scratch paths only.
    tmp = tempfile.mkdtemp(prefix="t_anchor_guard_shape_")
    try:
        rc, out = run(["--selftest", "--keep"])
        if rc != 2:
            fails.append("check3 --selftest combined with another flag "
                         "should exit 2, got %d" % rc)
        rc, _out = run(["--bogus"])
        if rc != 2:
            fails.append("check3 --bogus should exit 2, got %d" % rc)
        rc, out = run(["--repo", os.path.join(tmp, "absent_dir"),
                       "--manifest", "x.json"])
        if rc != 9 or "FAIL-LOUD" not in out:
            fails.append("check3 --repo on an absent directory should exit "
                         "9 with FAIL-LOUD before any toolchain judgment, "
                         "got %d\n%s" % (rc, out))
        with io.open(os.path.join(tmp, "synth_mod.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(MODULE_V)
        rc, out = run(["--repo", tmp,
                       "--manifest", os.path.join(tmp, "absent.json")])
        if rc != 111 or "SKIP" not in out:
            fails.append("check3 an unconfigured toolchain should exit 111 "
                         "with the SKIP line, got %d\n%s" % (rc, out))
        rc, out = run(["--repo", tmp, "--manifest",
                       os.path.join(tmp, "absent.json")],
                      env_extra={"ROCWASH_ROCQ": os.path.join(tmp, "no_rocq"),
                                 "ROCWASH_COQCHK":
                                     os.path.join(tmp, "no_coqchk")})
        if rc != 9 or "FAIL-LOUD" not in out:
            fails.append("check3 a configured but nonexistent binary path "
                         "should exit 9 with FAIL-LOUD, got %d\n%s"
                         % (rc, out))

        # Check 4: manifest validation vectors through the tool's own
        # loader (offline, no binaries needed).
        spec = importlib.util.spec_from_file_location("anchor_guard_under_test",
                                                      TOOL)
        ag = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ag)
        good = valid_manifest(tmp)
        loaded = ag.load_manifest(good, tmp)
        if loaded.get("schema") != "rocqwash.anchor/1":
            fails.append("check4 the valid manifest should load, got %r"
                         % loaded.get("schema"))

        def mutator(mutations):
            def apply(cfg):
                for action in mutations:
                    action(cfg)
            return apply

        def bad_schema(cfg):
            cfg["schema"] = "rocqwash.anchor/9"

        def dup_anchor(cfg):
            cfg["anchors"].append(dict(cfg["anchors"][0]))

        def missing_boundary(cfg):
            cfg["anchors"][0]["sample_points"] = \
                [p for p in cfg["anchors"][0]["sample_points"]
                 if p["corner"] != "boundary"]

        def build_class(cfg):
            cfg["mutants"][0]["class"] = "build"

        def unclosed_group(cfg):
            cfg["mutants"][0]["replacement"] = "([unclosed"

        def dangling_backref(cfg):
            cfg["mutants"][0]["pattern"] = r"\2x"
            cfg["mutants"][0]["replacement"] = r"(a)"

        vectors = [("bad schema string", bad_schema),
                   ("duplicate anchor name", dup_anchor),
                   ("corner set missing boundary", missing_boundary),
                   ("mutant class build", build_class),
                   ("unclosed replacement group", unclosed_group),
                   ("dangling backreference", dangling_backref)]
        for label, mutate in vectors:
            mpath = valid_manifest(tmp, "bad.json")
            cfg = json.load(io.open(mpath, encoding="utf-8"))
            mutator([mutate])(cfg)
            write_json(mpath, cfg)
            try:
                ag.load_manifest(mpath, tmp)
                fails.append("check4 %s should raise UsageError, loaded "
                             "clean" % label)
            except ag.UsageError:
                pass

        # Check 5: the companion mutation library volume is V9-clean
        # against the guard's own rules (manifests copy their rows from
        # it, so the library must pass the same admission).
        with io.open(LIBRARY, "r", encoding="utf-8") as fh:
            lib = json.load(fh)
        if lib.get("schema") != "rocqwash.mutants/1":
            fails.append("check5 library schema should be rocqwash.mutants/1,"
                         " got %r" % lib.get("schema"))
        entries = lib.get("mutants")
        if not isinstance(entries, list) or not entries:
            fails.append("check5 library should carry a non-empty mutants "
                         "array")
        else:
            for entry in entries:
                if entry.get("class") != "semantic":
                    fails.append("check5 library entry %r is not class "
                                 "semantic" % entry.get("id"))
                try:
                    rx = re.compile(entry["replacement"])
                except re.error as exc:
                    fails.append("check5 library entry %r replacement does "
                                 "not compile: %s" % (entry.get("id"), exc))
                    continue
                bad = ag.template_backref_check(entry["pattern"], rx)
                if bad:
                    fails.append("check5 library entry %r backreference "
                                 "fault: %s" % (entry.get("id"), bad))

        # Check 6: frozen shape constants and the zero-network import face.
        if ag.SCHEMA != "rocqwash-anchor-guard/1":
            fails.append("check6 report schema should be "
                         "rocqwash-anchor-guard/1, got %r" % ag.SCHEMA)
        if ag.MANIFEST_SCHEMA != "rocqwash.anchor/1":
            fails.append("check6 manifest schema should be "
                         "rocqwash.anchor/1, got %r" % ag.MANIFEST_SCHEMA)
        if ag.REPORT_NAME != "anchor-guard-report.json":
            fails.append("check6 report volume should be "
                         "anchor-guard-report.json, got %r" % ag.REPORT_NAME)
        with io.open(TOOL, "r", encoding="utf-8") as fh:
            src = fh.read()
        transport = ("import socket", "urllib", "ftplib", "smtplib",
                     "http.client")
        hits = [t for t in transport if t in src]
        if hits:
            fails.append("check6 the tool import face must stay "
                         "transport-free, found %r" % hits)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T_ANCHOR_GUARD_SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-ANCHOR-GUARD-SHAPE SUITE SHELL PASS (6 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
