#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutant_manifest.py - manifest skeleton generator for anchor_guard (rocqwash tools/).
Purpose.  One deterministic bridge from the frozen mutation library
  (tools/mutants-v1.json, schema rocqwash.mutants/1) to an anchor_guard
  manifest skeleton (schema rocqwash.anchor/1): copies the selected mutant
  rows verbatim (never re-derived), narrows them per the author-narrowing
  precedent recorded in the library itself (PROJ-001/CONST-001 carry their
  own narrowing notes), and emits the skeleton with an empty anchors array -
  the author then fills anchors (referent/certificate_face/sample_points
  under the V1-V10 rules) before anchor_guard accepts the manifest; the
  generator states that obligation loudly on stdout and never invents
  anchors, sample points, or checks.  Zero network, zero files written
  beyond the caller-named --out.
Interface.  python -I tools/mutant_manifest.py --library FILE --module NAME.v
  [--families ID[,ID...]] [--out FILE] [--selftest].  --families selects
  library rows by exact id (default: every row); an unknown id is fail-loud
  rc 2.  Exit-codes.  0 skeleton written (or stdout when --out absent);
  1 selftest red; 2 usage (bad JSON, unknown schema, unknown family,
  module not a .v name); 9 --library/--out path unwritable or missing;
  111 honest skip is not used (the generator needs no toolchain).
Evidence.  Deterministic: sorted keys, no wall clock; the same library
  bytes and flags give the byte-identical skeleton on a double run.
  --selftest runs the embedded vectors on temp fixtures, never the real
  library (a library edit cannot break the generator's own proof).
"""
# Extended contract:
# Output shape.  {"schema": "rocqwash.anchor/1", "module": "<module>",
#   "anchors": [], "mutants": [verbatim library rows]}.  anchors is
#   deliberately empty: anchor_guard's load_manifest rejects an empty
#   anchors array (its rule V-set), so the skeleton is judgeable-by-design
#   only after authoring; the generator prints the authoring checklist
#   (referent/certificate_face must exist in the module statement census,
#   sample_points must cover smallest+boundary, independent_derivation
#   non-empty) and never fabricates those fields.
# Narrowing.  Rows whose own evidence text records the author-narrowing
#   precedent (PROJ-001, CONST-001) are copied verbatim; the generator
#   does not rewrite patterns (a wrong mechanical rewrite would be a
#   silent semantic change - the author narrows against their module and
#   records the narrowing in their own manifest copy).
# Determinism.  json.dumps(sort_keys=True, indent=1) + trailing newline;
#   rows keep library order (filtered), keys sorted - a double run over
#   the same inputs is byte-identical (selftest-asserted).
import argparse
import io
import json
import os
import sys

PROG = "mutant_manifest"
LIBRARY_SCHEMA = "rocqwash.mutants/1"
MANIFEST_SCHEMA = "rocqwash.anchor/1"

AUTHORING_CHECKLIST = (
    "authoring checklist (the skeleton is not judgeable until these are "
    "filled; anchor_guard rejects an empty anchors array by rule): "
    "1) anchors[]: name / referent / certificate_face - referent and "
    "certificate_face must appear in the module statement census (V8); "
    "2) sample_points: non-empty, corner coverage smallest+boundary (V6), "
    "check without trailing period; "
    "3) independent_derivation: non-empty (V7; name-level independence is "
    "machine-checked by anchor_guard v2); "
    "4) narrow the copied mutant rows to your module's real sites and "
    "record the narrowing in your manifest copy."
)


def build_skeleton(library, module, family_ids):
    """Returns (skeleton_dict, selected_ids) or raises UsageError."""
    if library.get("schema") != LIBRARY_SCHEMA:
        raise UsageError("library schema must be %r (got %r)"
                         % (LIBRARY_SCHEMA, library.get("schema")))
    rows = library.get("mutants")
    if not isinstance(rows, list) or not rows:
        raise UsageError("library mutants must be a non-empty array")
    if not module.endswith(".v") or not module:
        raise UsageError("--module must name a .v file (got %r)" % module)
    if family_ids is None:
        selected = list(rows)
    else:
        by_id = {}
        for row in rows:
            rid = row.get("id")
            if isinstance(rid, str):
                by_id[rid] = row
        missing = [fid for fid in family_ids if fid not in by_id]
        if missing:
            raise UsageError("unknown family id(s): %s (library has %s)"
                             % (", ".join(missing),
                                ", ".join(sorted(by_id))))
        selected = [by_id[fid] for fid in family_ids]
    skeleton = {
        "schema": MANIFEST_SCHEMA,
        "module": module,
        "anchors": [],
        "mutants": [json.loads(json.dumps(row)) for row in selected],
    }
    return skeleton, [row.get("id") for row in selected]


class UsageError(Exception):
    """A flag/shape violation: exit code 2, the offending field named."""


def run_args(argv):
    ap = argparse.ArgumentParser(prog=PROG,
                                 description="anchor_guard manifest skeleton "
                                             "generator (mutants-v1 -> "
                                             "rocqwash.anchor/1 draft)")
    ap.add_argument("--library", help="mutation library JSON "
                                      "(rocqwash.mutants/1)")
    ap.add_argument("--module", help="target module name (must end .v)")
    ap.add_argument("--families", default=None,
                    help="comma-separated family ids (default: all)")
    ap.add_argument("--out", default=None,
                    help="skeleton output path (absent = stdout)")
    ap.add_argument("--selftest", action="store_true",
                    help="embedded vectors on temp fixtures, exit")
    args = ap.parse_args(argv)
    return args


def _write_skeleton(args):
    if not os.path.isfile(args.library):
        print("FAIL-LOUD: --library path missing: %s" % args.library,
              file=sys.stderr)
        return 9
    try:
        with io.open(args.library, "r", encoding="utf-8") as fh:
            library = json.load(fh)
    except ValueError as exc:
        print("USAGE: --library is not valid JSON: %s" % exc, file=sys.stderr)
        return 2
    family_ids = None
    if args.families:
        family_ids = [f.strip() for f in args.families.split(",")
                      if f.strip()]
        if not family_ids:
            print("USAGE: --families parsed empty", file=sys.stderr)
            return 2
    try:
        skeleton, selected = build_skeleton(library, args.module, family_ids)
    except UsageError as exc:
        print("USAGE: %s" % exc, file=sys.stderr)
        return 2
    blob = json.dumps(skeleton, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"
    if args.out:
        try:
            with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
                fh.write(blob)
        except OSError as exc:
            print("FAIL-LOUD: --out write failure: %s" % exc, file=sys.stderr)
            return 9
        print("skeleton -> %s" % args.out)
    else:
        sys.stdout.write(blob)
    print("selected families: %s" % (", ".join(selected) or "(none)"))
    print(AUTHORING_CHECKLIST)
    return 0


def selftest():
    """Embedded vectors on temp fixtures; the real library is never read."""
    import shutil
    import tempfile
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    lib = {"schema": LIBRARY_SCHEMA, "mutants": [
        {"id": "FAKE-1", "class": "semantic", "pattern": "b",
         "replacement": "a", "evidence": "e1"},
        {"id": "FAKE-2", "class": "semantic", "pattern": "d",
         "replacement": "c", "evidence": "e2"}]}
    tmp = tempfile.mkdtemp(prefix="mutant_manifest_selftest_")
    try:
        lib_path = os.path.join(tmp, "lib.json")
        with io.open(lib_path, "w", encoding="utf-8") as fh:
            json.dump(lib, fh)
        # V1: full skeleton, shape and verbatim rows
        out1 = os.path.join(tmp, "m1.json")
        rc = _run_cli(["--library", lib_path, "--module", "mod.v",
                       "--out", out1])
        ok = rc == 0
        skel = {}
        if ok:
            with io.open(out1, encoding="utf-8") as fh:
                skel = json.load(fh)
        ok = ok and skel.get("schema") == MANIFEST_SCHEMA \
            and skel.get("module") == "mod.v" and skel.get("anchors") == [] \
            and [m["id"] for m in skel.get("mutants", [])] == \
            ["FAKE-1", "FAKE-2"]
        vec("full-skeleton-verbatim", ok, "rc=%d ids=%s"
            % (rc, [m.get("id") for m in skel.get("mutants", [])]))
        # V2: family filter keeps library order
        out2 = os.path.join(tmp, "m2.json")
        rc = _run_cli(["--library", lib_path, "--module", "mod.v",
                       "--families", "FAKE-2", "--out", out2])
        with io.open(out2, encoding="utf-8") as fh:
            skel2 = json.load(fh)
        vec("family-filter", rc == 0 and
            [m["id"] for m in skel2["mutants"]] == ["FAKE-2"],
            "rc=%d" % rc)
        # V3: unknown family fail-loud rc 2
        rc = _run_cli(["--library", lib_path, "--module", "mod.v",
                       "--families", "NOPE", "--out",
                       os.path.join(tmp, "m3.json")])
        vec("unknown-family-rc2", rc == 2, "rc=%d" % rc)
        # V4: missing library rc 9
        rc = _run_cli(["--library", os.path.join(tmp, "absent.json"),
                       "--module", "mod.v", "--out",
                       os.path.join(tmp, "m4.json")])
        vec("missing-library-rc9", rc == 9, "rc=%d" % rc)
        # V5: double run byte-identical
        out5a = os.path.join(tmp, "m5a.json")
        out5b = os.path.join(tmp, "m5b.json")
        _run_cli(["--library", lib_path, "--module", "mod.v", "--out", out5a])
        _run_cli(["--library", lib_path, "--module", "mod.v", "--out", out5b])
        vec("double-run-identical",
            io.open(out5a, "rb").read() == io.open(out5b, "rb").read(),
            "byte comparison")
        # V6: module without .v refused rc 2
        rc = _run_cli(["--library", lib_path, "--module", "mod.c",
                       "--out", os.path.join(tmp, "m6.json")])
        vec("module-not-v-rc2", rc == 2, "rc=%d" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("MUTANT-MANIFEST-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


def _run_cli(argv):
    """Drive run_args + _write_skeleton in-process; returns the exit code."""
    args = run_args(argv)
    return _write_skeleton(args)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    args = run_args(argv)
    if not args.library or not args.module:
        print("USAGE: --library and --module are required", file=sys.stderr)
        sys.exit(2)
    sys.exit(_write_skeleton(args))


if __name__ == "__main__":
    main()
