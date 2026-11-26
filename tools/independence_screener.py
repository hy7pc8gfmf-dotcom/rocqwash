#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""independence_screener.py - name-level independence screening (rocqwash tools/).
Purpose.  The mechanical first-pass face of the independence requirement
  that mutants-v1.json records as an authoring obligation ("Anchors must
  derive their certificate independently of the suspect series") and that
  anchor_guard v2 honestly leaves as future work beyond V7's non-emptiness
  check.  Given a rocqwash.anchor/1 manifest and the rocqwash.mutants/1
  defect library, the screener extracts each mutant's site identifiers
  (the function/module names its pattern+replacement fields name - the
  suspect-series machinery; the fields are REGEX sources, so a composed
  site name rsT_recipQ appears there as the fragments rsT_ / recipQ)
  and each anchor's independent_derivation tokens, and flags every
  underscore-part INTERSECTION (parts of length >= 3) as a collision:
  an "independent" derivation that names the suspect series' own
  machinery is exactly the VACUOUS-certificate risk shape the
  requirement exists to prevent (the atanh-vs-Mercator exemplar lives one
  identifier apart: DEP-001's site set carries atanhQ_tail).  The
  intersection form is deliberately conservative: prose words can never
  false-positive because a part counts only when it equals a real
  library fragment part, and generic-name hits (the "nat" in qpow_nat)
  are listed as data for review, never judged.  Rows whose
  pattern/replacement carry no identifier at all (the
  CONST-001 numeric-literal shape) are unscreenable by name and are
  recorded as data, never judged.  This is a SCREENING face: a clean
  screen proves nothing beyond the name level - the authoring obligation
  stays with review; the report records the library's independence_note
  verbatim (the anchor_guard precedent) and says so loudly.
  Zero network, zero toolchain, zero writes beyond the caller-named --out.
Interface.  python -I tools/independence_screener.py --manifest FILE
  --library FILE [--out F] | --selftest.
Dependencies.  Python 3 standard library only; the selftest's
  subprocess face is a detached temp copy of this module only; zero
  network.
Exit-codes.  0 clean (no
  collisions); 1 collisions listed (data, fail-loud); 2 usage (bad
  schema, bad manifest shape, empty independent_derivation = the V7
  mirror, M == degenerate shapes); 9 --manifest/--library path missing.
  Deterministic: sorted collisions, double-run byte-identical.
Evidence.  --selftest: canned manifest/library fixtures (clean screen
  rc 0; collision rc 1 with the shared token named; empty derivation
  rc 2; schema mismatch rc 2; missing library path rc 9; no-name row
  recorded; determinism double-run byte-identical).
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

PROG = "independence_screener"
MANIFEST_SCHEMA = "rocqwash.anchor/1"
LIBRARY_SCHEMA = "rocqwash.mutants/1"
REPORT_SCHEMA = "rocqwash.independence-screener/1"

IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']{2,}")


class UsageError(Exception):
    pass


class MissingPathError(UsageError):
    """A caller-named path does not exist (docstring exit-code 9)."""


def _identifiers(text):
    """Ordered-unique identifier tokens of a text blob."""
    seen = []
    for tok in IDENT_RE.findall(text or ""):
        if tok not in seen:
            seen.append(tok)
    return seen


def load_json(path, what):
    if not os.path.isfile(path):
        raise MissingPathError("%s path missing: %s" % (what, path))
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        raise UsageError("%s is not valid JSON: %s" % (what, exc))


def _parts(tokens):
    """Underscore-parts (length >= 3) of identifier tokens, as a set.

    Part granularity is what makes the sharing face work at the name
    level: library pattern/replacement fields are REGEX sources, so a
    composed site name rsT_recipQ appears there as the fragments rsT_ /
    recipQ; a derivation naming rsT_recipQ shares the parts rsT and
    recipQ with those fragments.  Bare prose cannot false-positive:
    a part counts only when it equals a real library fragment part."""
    out = set()
    for t in tokens:
        for p in t.split("_"):
            if len(p) >= 3:
                out.add(p)
    return out


def screen(manifest, library):
    """Returns (report_dict, exit_rc).  Pure: no I/O, sorted output."""
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise UsageError("manifest schema must be %r (got %r)"
                         % (MANIFEST_SCHEMA, manifest.get("schema")))
    if library.get("schema") != LIBRARY_SCHEMA:
        raise UsageError("library schema must be %r (got %r)"
                         % (LIBRARY_SCHEMA, library.get("schema")))
    anchors = manifest.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        raise UsageError("manifest anchors must be a non-empty array")
    rows = library.get("mutants")
    if not isinstance(rows, list) or not rows:
        raise UsageError("library mutants must be a non-empty array")

    # mutant site-id table (sorted for determinism)
    site_ids = {}
    no_name_rows = []
    for row in rows:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid:
            raise UsageError("mutant row without a string id")
        toks = _identifiers("%s %s" % (row.get("pattern", ""),
                                       row.get("replacement", "")))
        if toks:
            site_ids[rid] = toks
        else:
            no_name_rows.append(rid)

    collisions = []
    screened = 0
    row_parts = {rid: _parts(toks) for rid, toks in site_ids.items()}
    for anchor in anchors:
        name = anchor.get("name")
        if not isinstance(name, str) or not name:
            raise UsageError("anchor without a string name")
        deriv = anchor.get("independent_derivation")
        if not isinstance(deriv, str) or not deriv:
            # the V7 mirror: anchor_guard refuses this at load; the
            # screener refuses it too (usage-shape, rc 2)
            raise UsageError("anchor %s independent_derivation must be a "
                             "non-empty string" % name)
        screened += 1
        dparts = _parts(_identifiers(deriv))
        for rid in sorted(row_parts):
            shared = sorted(dparts & row_parts[rid])
            if shared:
                collisions.append({"anchor": name, "mutant": rid,
                                   "shared": shared})
    collisions.sort(key=lambda c: (c["anchor"], c["mutant"]))
    report = {
        "schema": REPORT_SCHEMA,
        "face": "screen",
        "anchors_screened": screened,
        "rows_screened": len(rows),
        "site_id_rows": len(site_ids),
        "no_name_rows": sorted(no_name_rows),
        "collisions": collisions,
        "clean": not collisions,
        "independence_note_verbatim":
            library.get("independence_note", ""),
        "note": "name-level screening only: a clean screen is not a proof "
                "of independence - the authoring obligation stays with "
                "review (mutants-v1.json independence_note recorded "
                "verbatim above)",
    }
    return report, (0 if not collisions else 1)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="name-level independence screening over an anchor "
        "manifest against the mutant defect library")
    ap.add_argument("--manifest", help="rocqwash.anchor/1 manifest JSON")
    ap.add_argument("--library", help="rocqwash.mutants/1 library JSON")
    ap.add_argument("--out", help="report output path")
    ap.add_argument("--selftest", action="store_true",
                    help="embedded vectors on canned fixtures")
    args = ap.parse_args(argv)
    try:
        if not args.manifest or not args.library:
            raise UsageError("--manifest and --library are required")
        manifest = load_json(args.manifest, "--manifest")
        library = load_json(args.library, "--library")
        report, rc = screen(manifest, library)
    except MissingPathError as exc:
        print("PATH-MISSING: %s" % exc, file=sys.stderr)
        sys.exit(9)
    except UsageError as exc:
        print("USAGE: %s" % exc, file=sys.stderr)
        sys.exit(2)
    blob = json.dumps(report, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        print("report -> %s" % args.out)
    else:
        sys.stdout.write(blob)
    print("independence-screener: anchors=%d rows=%d collisions=%d"
          % (report["anchors_screened"], report["rows_screened"],
             len(report["collisions"])))
    sys.exit(rc)


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

    tmp = tempfile.mkdtemp(prefix="independence_screener_selftest_")
    try:
        # canned library: two rows, one with site ids, one numeric-only
        library = {
            "schema": LIBRARY_SCHEMA, "version": "v1",
            "independence_note": "authoring obligation (canned)",
            "mutants": [
                {"id": "TST-001", "class": "semantic",
                 "pattern": "\\1 (2 * \\2 + 1)",
                 "replacement": "((?:rsT_)?recipQ) \\(2 \\* k\\)"},
                {"id": "TST-NUM", "class": "semantic",
                 "pattern": "7", "replacement": "3"},
            ],
        }
        lib_path = os.path.join(tmp, "library.json")
        with io.open(lib_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(library, fh, indent=1)

        def manifest_with(derivs):
            return {"schema": MANIFEST_SCHEMA,
                    "anchors": [{"name": n, "referent": "r.v:r",
                                 "certificate_face": "f",
                                 "sample_point_count": 1, "corners": [],
                                 "independent_derivation": d,
                                 "baseline": "hold"}
                                for n, d in derivs]}

        def run(manifest_obj, out_name):
            mpath = os.path.join(tmp, out_name + ".manifest.json")
            with io.open(mpath, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(manifest_obj, fh, indent=1)
            out = os.path.join(tmp, out_name + ".report.json")
            p = subprocess.run(
                [sys.executable, "-I", "-B",
                 os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "independence_screener.py"),
                 "--manifest", mpath, "--library", lib_path,
                 "--out", out],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=60)
            return p, out

        # clean screen: derivation tokens disjoint from site ids
        p, out = run(manifest_with([("a", "atanh tail over the abs "
                                          "monotone face")]), "clean")
        ok = p.returncode == 0
        rep = {}
        if ok:
            with io.open(out, encoding="utf-8") as fh:
                rep = json.load(fh)
            ok = rep.get("clean") is True \
                and rep.get("no_name_rows") == ["TST-NUM"] \
                and rep.get("independence_note_verbatim") \
                == "authoring obligation (canned)"
        vec("clean-screen-rc0", ok, "rc=%d" % p.returncode)

        # collision: derivation names the suspect-series identifier
        p, out = run(manifest_with([("a", "atanh tail over the abs "
                                          "monotone face"),
                                    ("b", "sums rsT_recipQ over k")]),
                     "collide")
        ok = p.returncode == 1
        if ok:
            with io.open(out, encoding="utf-8") as fh:
                rep = json.load(fh)
            ok = (rep["clean"] is False and len(rep["collisions"]) == 1
                  and rep["collisions"][0]["anchor"] == "b"
                  and rep["collisions"][0]["mutant"] == "TST-001"
                  and rep["collisions"][0]["shared"] == ["recipQ", "rsT"])
        vec("collision-rc1-shared-named", ok, "rc=%d" % p.returncode)


        # empty derivation = the V7 mirror, usage rc 2
        p, _ = run(manifest_with([("a", "")]), "empty")
        vec("empty-derivation-rc2", p.returncode == 2,
            "rc=%d stderr=%s" % (p.returncode, p.stderr[-70:]))

        # schema mismatch rc 2
        p, _ = run({"schema": "other/1", "anchors": []}, "schema")
        vec("schema-mismatch-rc2", p.returncode == 2, "rc=%d" % p.returncode)

        # missing library path rc 2 (usage) not 9: the path face
        mpath = os.path.join(tmp, "clean.manifest.json")
        p = subprocess.run(
            [sys.executable, "-I", "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "independence_screener.py"),
             "--manifest", mpath, "--library",
             os.path.join(tmp, "absent.json")],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        vec("missing-library-rc9", p.returncode == 9,
            "rc=%d stderr=%s" % (p.returncode, p.stderr[-70:]))

        # determinism: double run byte-identical
        p1, o1 = run(manifest_with([("b", "sums rsT_recipQ over k")]),
                     "det1")
        p2, o2 = run(manifest_with([("b", "sums rsT_recipQ over k")]),
                     "det2")
        with io.open(o1, encoding="utf-8") as fh:
            b1 = fh.read()
        with io.open(o2, encoding="utf-8") as fh:
            b2 = fh.read()
        vec("determinism-double-run", p1.returncode == p2.returncode == 1
            and b1 == b2, "byte-identical=%s" % (b1 == b2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("INDEPENDENCE-SCREENER-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    main()
