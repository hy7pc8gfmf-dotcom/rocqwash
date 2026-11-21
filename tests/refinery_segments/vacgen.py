#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/refinery_segments/vacgen.py -- vacgen segment of the refinery suite.

Purpose.  Pin the vacgen lane deliverables at word-face level: the envelope
  double-layer fix (named instance binders render a clean existential prefix;
  the conjunction chain draws from the explicit-assumption segment only), the
  W5 cast-time bare-type-conjunct-limb front gate (canonical face "∧ Set ("
  plus the self-built limb family; a deformed cast dies rc=1 before any file
  emission, with zero false positives on the castable faces; since the
  cast-repair work stream of November 22, 2026 the gate judges only faces left
  unresolved by knife-1 data re-homing and knife-2 Prop resolution, with
  the opt-in --allow-bare-type-limb waiver registering released limbs in
  report.waiver), and the W6
  two-dimensional verdict (after GREEN the degenerate battery scans emptyset
  / single-point / zero-element / top-type / always-true word faces; the
  report verdict gains the strength face over the refutationForms five-word
  vocabulary; degeneracy is data and the exit-code semantics never change).
Interface.  run_segment_vacgen() -> (passed, failed, skipped, results) with
  results entries (status, name, detail), status in PASS/FAIL/SKIP; importing
  this module spawns nothing (import-safe); a direct run prints one line per
  check plus SEGMENT/SUMMARY/TOTAL lines.
Dependencies.  Python 3 standard library only; tools/vacgen.py loads
  dynamically from the repo tree; every probe fixture is written into a
  temporary directory and removed at segment end; zero network by
  construction (the generator is zero-network and this segment never opens
  a socket).
Evidence.  tools/vacgen.py envelope_statement / envelope_prefix_segments /
  envelope_free_var_hits / envelope_bare_type_limb_hits / is_bare_type_limb /
  degenerate_battery_hits / strength_face; live casts of the segment fixtures
  through the cast CLI face with rc, stdout markers, and the report JSON
  asserted directly.
Exit-codes.  0 zero failed checks; 1 at least one failed check (each listed,
  fail loud); 2 usage error.  SKIP lines name their missing surface and never
  count as passes.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
VACGEN = os.path.join(REPO_ROOT, "tools", "vacgen.py")
TOOL_TIMEOUT_S = 120

EXISTS = chr(0x2203)      # ∃
CC = chr(0x2102)          # ℂ
RR = chr(0x211D)          # ℝ
NEQ = chr(0x2260)         # ≠
ARROW = chr(0x2192)       # →
AND = chr(0x2227)         # ∧

REFUTATION_FORMS = ("full", "point", "tactics", "noclassic", "band")

# zeta face, byte-identical content to tests/t_vacgen_shape.py FIXTURE (the
# currently-castable regression face; zero false positives must hold here)
ZETA_FIXTURE = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenRefinerySelftest\n\n"
    "theorem demo_half_plane_nonempty : (EXISTS s : CC, (7 / 8 : RR) < s.re) := by\n"
    "  refine (2, by norm_num)\n\n"
    "theorem demo_zero_face {s : CC} (hs : (7 / 8 : RR) < s.re) : riemannZeta s != 0 := by\n"
    "  sorry\n\n"
    "end VacgenRefinerySelftest\n"
).replace("EXISTS", EXISTS).replace("CC", CC).replace("RR", RR).replace("!=", NEQ)

# single-declaration zeta face: the head carries the premise binders, so the
# envelope body is the genuine hypothesis limb and the battery grades full
ZETA_SINGLE_FIXTURE = (
    "theorem demo_zero_face {s : CC} (hs : (7 / 8 : RR) < s.re)"
    " : riemannZeta s != 0 := by\n"
    "  sorry\n"
).replace("CC", CC).replace("RR", RR).replace("!=", NEQ)

# named instance binder: the 2.1.0 L1 re-homing face (was `∃ (_ : inst : Foo A)`)
NAMED_INSTANCE_FIXTURE = (
    "variable {A : Type}\n"
    "variable [inst : Foo A]\n"
    "theorem named_inst_face (h : P A) : Q A := by\n"
    "  sorry\n"
)

# anonymous instance binder: the v1 face that must stay unchanged
ANON_INSTANCE_FIXTURE = (
    "variable {A : Type}\n"
    "variable [Foo A]\n"
    "theorem anon_inst_face (h : P A) : Q A := by\n"
    "  sorry\n"
)

# trial-item G1 face: byte-stable envelope vs the pre-fix cast (zero churn)
G1_TRIAL_FIXTURE = (
    "variable {A : Type}\n"
    "variable (I : Set A)\n"
    "theorem g1_trial_face (h : IsClosed I) : P I := by\n"
    "  sorry\n"
)
G1_TRIAL_ENVELOPE = (EXISTS + " (I : Set A), " + EXISTS +
                     " (h : IsClosed I), True")

# bare-type conjunct limb face: single limb (canonical face needs two limbs,
# so the family prong carries this one).  Cast-repair work stream, November 22,
# 2026: the head is deliberately the UNKNOWN `Pkg` - the previous `Set (...)`
# head now re-homes at L1 routing (knife 1: a data-family binder face is a
# bound variable, not a conjunct limb), so the reject vector must pin the
# family that stays loud: heads resolving neither as an own-file
# `def : Prop` nor as a predicate family head (and waived only by the
# opt-in --allow-bare-type-limb flag, registered in report.waiver).
BARE_LIMB_FIXTURE = (
    "theorem bare_limb_face {A : Type}"
    " (s : Pkg (RR XARROW RR)) (h : Nonempty A) : P s := by\n"
    "  sorry\n"
).replace("XARROW", ARROW)

# premise-free conjunction body: the envelope body degenerates to the truth
# identity; W6 must record that as data while rc stays 0
TRUE_BODY_FIXTURE = (
    "theorem true_body_face (k : Set CC) : Nonempty k := by\n"
    "  sorry\n"
)

_MODULE = None
_TMP_DIRS = []


def _load_module():
    """Load tools/vacgen.py dynamically (import-safe; no cache files)."""
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    if not os.path.isfile(VACGEN):
        return None
    spec = importlib.util.spec_from_file_location("refinery_vacgen", VACGEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _MODULE = mod
    return mod


def _cast_fixture(src_text, with_report=False):
    """Cast src_text through the CLI face in a fresh temp directory.
    with_report=True adds --report and returns the report path in its
    third position; otherwise the third value is None."""
    tmp = tempfile.mkdtemp(prefix="vacgen_refinery_")
    _TMP_DIRS.append(tmp)
    fx = os.path.join(tmp, "fixture.lean")
    with open(fx, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src_text)
    out = os.path.join(tmp, "out")
    report_path = os.path.join(tmp, "report.json") if with_report else None
    cmd = [sys.executable, "-I", "-X", "utf8", VACGEN, "--in", fx, "--out", out]
    if report_path:
        cmd += ["--report", report_path]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=TOOL_TIMEOUT_S)
    return proc, out, report_path


def check(results, name, thunk):
    """One bound check: PASS on return, FAIL on assertion, loud FAIL on any
    other raise (fail loud, never silently swallowed)."""
    try:
        detail = thunk()
        results.append(("PASS", name, detail or "ok"))
    except AssertionError as exc:
        results.append(("FAIL", name, str(exc) or "assertion failed"))
    except Exception as exc:  # noqa: BLE001 - one bad check must not hide the rest
        results.append(("FAIL", name, "%s: %s" % (type(exc).__name__, exc)))


def _thunk_import_face():
    mod = _load_module()
    assert mod is not None, "tools/vacgen.py not found at %s" % VACGEN
    for fn in ("envelope_statement", "envelope_prefix_segments",
               "envelope_free_var_hits", "envelope_bare_type_limb_hits",
               "is_bare_type_limb", "degenerate_battery_hits",
               "strength_face", "split_instance_binder"):
        assert hasattr(mod, fn), "missing engine function %s" % fn
    parts = tuple(int(x) for x in mod.TOOL_VERSION.split("."))
    assert parts >= (2, 1, 0), "TOOL_VERSION %s predates the 2.1.0 wave" % mod.TOOL_VERSION
    return "version %s with the full envelope face" % mod.TOOL_VERSION


def _thunk_p25_instance_clean_prefix():
    mod = _load_module()
    stmt = mod.decompose_head(NAMED_INSTANCE_FIXTURE)
    segs = mod.envelope_prefix_segments(stmt)
    env = mod.envelope_statement(stmt)
    want = "%s (_ : Foo A)" % EXISTS
    assert want in segs, "clean instance prefix segment missing: %r" % (segs,)
    assert ": inst :" not in env, "binder name leaked into the type position: %s" % env
    assert "inst" not in env, "binder name leaked into the envelope: %s" % env
    return "prefix segment %r clean" % (want,)


def _thunk_p25_anon_instance_unchanged():
    mod = _load_module()
    stmt = mod.decompose_head(ANON_INSTANCE_FIXTURE)
    segs = mod.envelope_prefix_segments(stmt)
    want = "%s (_ : Foo A)" % EXISTS
    assert want in segs, "anonymous instance segment changed: %r" % (segs,)
    return "anonymous face unchanged"


def _thunk_p25_conjunct_source_only():
    mod = _load_module()
    stmt = mod.decompose_head(ZETA_SINGLE_FIXTURE)
    env = mod.envelope_statement(stmt)
    want = "%s (s : %s), (7 / 8 : %s) < s.re" % (EXISTS, CC, RR)
    assert env == want, "envelope drifted from the explicit-assumption face: %s" % env
    segs = mod.envelope_prefix_segments(stmt)
    assert segs == ["%s (s : %s)" % (EXISTS, CC)], "prefix segments drifted: %r" % (segs,)
    return "envelope = %s" % env


def _thunk_p25_free_var_family():
    mod = _load_module()
    for label, src in (("zeta", ZETA_FIXTURE),
                       ("g1-trial", G1_TRIAL_FIXTURE),
                       ("named-instance", NAMED_INSTANCE_FIXTURE)):
        stmt = mod.decompose_head(src)
        env = mod.envelope_statement(stmt)
        hits = mod.envelope_free_var_hits(stmt, env)
        assert hits == [], "free-var hits on %s: %r" % (label, hits)
    return "free-var word-face family clean on 3 faces"


def _thunk_p25_g1_trial_byte_stable():
    mod = _load_module()
    stmt = mod.decompose_head(G1_TRIAL_FIXTURE)
    env = mod.envelope_statement(stmt)
    assert env == G1_TRIAL_ENVELOPE, \
        "g1-trial envelope drifted from the pre-wave cast: %s" % env
    hits = mod.envelope_bare_type_limb_hits(stmt, env)
    assert hits == [], "g1-trial face flagged by the W5 gate (false positive): %r" % (hits,)
    return "byte-stable vs the pre-wave cast, zero false positives"


def _thunk_w5_canonical_face():
    mod = _load_module()
    env = "%s (A : Type), Set (%s %s %s) %s Set (%s %s %s)" % (
        EXISTS, RR, ARROW, RR, AND, CC, ARROW, CC)
    stmt = {"S1_vars": [], "S2_assumps": [
        {"name": "s", "type": "Set (%s %s %s)" % (RR, ARROW, RR)},
        {"name": "t", "type": "Set (%s %s %s)" % (CC, ARROW, CC)},
    ], "S2_instances": []}
    hits = mod.envelope_bare_type_limb_hits(stmt, env)
    assert mod.BARE_TYPE_LIMB_CANONICAL in hits, \
        "canonical word face missing from hits: %r" % (hits,)
    assert "Set (%s %s %s)" % (RR, ARROW, RR) in hits, "limb family miss: %r" % (hits,)
    return "canonical face + limb family both fire"


def _thunk_w5_limb_family_bounds():
    mod = _load_module()
    for face in ("Set (%s %s %s)" % (RR, ARROW, RR), "Type"):
        assert mod.is_bare_type_limb(face), "family should flag %r" % face
    for face in ("IsClosed (I : Set %s)" % CC, "Nonempty A",
                 "P %s Q" % AND, "True", "(7 / 8 : %s) < s.re" % RR,
                 "Set.Icc 0 1", "ContinuousOn f (Set.Icc 0 1)"):
        assert not mod.is_bare_type_limb(face), \
            "family must not flag the proposition face %r (fail-safe side)" % face
    return "family: 2 positive, 7 negative (fail-safe side held)"


def _thunk_w5_data_limb_rehomed():
    mod = _load_module()
    stmt = mod.decompose_head(
        "theorem rehome_face (s : Set (%s %s %s)) : P s := by\n  sorry\n"
        % (RR, ARROW, RR))
    names = [v["name"] for v in stmt["S1_vars"]]
    env = mod.envelope_statement(stmt)
    want = "%s (s : Set (%s %s %s)), True" % (EXISTS, RR, ARROW, RR)
    hits = mod.envelope_bare_type_limb_hits(stmt, env)
    assert "s" in names, "data binder not re-homed into S1: %r" % (names,)
    assert env == want, "envelope drifted from the re-homed face: %s" % env
    assert hits == [], "re-homed face flagged by the W5 gate: %r" % (hits,)
    assert mod.is_bare_type_limb("Set (%s %s %s)" % (RR, ARROW, RR)), \
        "word-face family must keep flagging (the cleaning seat is L1 routing)"
    return "data binder re-homed to %r, envelope %r, word face unchanged" \
        % (names, env)


def _thunk_w5_cast_time_reject():
    proc, out, _report = _cast_fixture(BARE_LIMB_FIXTURE)
    assert proc.returncode == 1, \
        "deformed cast must die rc=1, got rc=%s (%s)" % (proc.returncode, proc.stdout[-200:])
    assert "bare-type-conjunct-limb" in proc.stdout, \
        "rejection marker missing from stdout"
    assert not os.path.isfile(os.path.join(out, "witness.lean")), \
        "skeleton text emitted despite the front gate"
    return "rc=1 before emission, marker on stdout"


def _thunk_w5_zero_false_positives_cli():
    proc, out, _report = _cast_fixture(ZETA_FIXTURE)
    assert proc.returncode == 0, \
        "castable zeta face must stay rc=0, got %s" % proc.returncode
    assert "ok=true" in proc.stdout, "cast verdict not ok=true"
    assert os.path.isfile(os.path.join(out, "witness.lean")), "skeleton missing"
    return "castable face stays green (rc=0, ok=true)"


def _thunk_w5_check_row_in_report():
    proc, _out, report_path = _cast_fixture(ZETA_FIXTURE, with_report=True)
    assert proc.returncode == 0, "green cast required, got %s" % proc.returncode
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)
    rows = {name: ok for name, ok, _d in report["verdict"]["checks"]}
    assert rows.get("envelope_bare_type_limbs_zero") is True, \
        "W5 bound-form check row missing or red"
    assert rows.get("envelope_free_vars_zero") is True, \
        "free-var check row missing or red (word-face family)"
    return "bound-form rows green in the report checks"


def _thunk_w6_strength_face_green():
    proc, _out, report_path = _cast_fixture(ZETA_SINGLE_FIXTURE, with_report=True)
    assert proc.returncode == 0, "green cast required, got %s" % proc.returncode
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)
    sf = report["verdict"]["strength"]
    assert sf["satisfiable"] is True, "strength.satisfiable must mirror GREEN"
    assert sf["grade"] == "full", "clean battery must grade full, got %s" % sf["grade"]
    assert sf["battery"] == [], "clean battery must carry no hit rows"
    assert sf["degenerate"] is False, "clean battery must not be degenerate"
    assert "monotone" in sf["note"], "registered no-exact-equality note missing"
    return "grade=full, battery clean, note carries the monotone discipline"


def _thunk_w6_exit_semantics_unchanged():
    proc, _out, report_path = _cast_fixture(TRUE_BODY_FIXTURE, with_report=True)
    assert proc.returncode == 0, \
        "degeneracy is data: exit code must stay 0, got %s" % proc.returncode
    assert "ok=true" in proc.stdout, "verdict must stay ok=true on degenerate data"
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)
    sf = report["verdict"]["strength"]
    assert sf["satisfiable"] is True, "strength.satisfiable must mirror GREEN"
    assert sf["degenerate"] is True, "truth-identity body must be flagged degenerate"
    classes = [row["class"] for row in sf["battery"]]
    assert "top-type" in classes, "top-type class missing: %r" % (classes,)
    top = next(row for row in sf["battery"] if row["class"] == "top-type")
    assert top["count"] >= 1, "monotone bound: top-type count must be >= 1"
    assert sf["grade"] in REFUTATION_FORMS, \
        "grade %r outside the refutationForms vocabulary" % (sf["grade"],)
    assert list(sf["order"]) == list(REFUTATION_FORMS), \
        "registered strength order drifted: %r" % (sf["order"],)
    return "rc=0 with degenerate data: top-type hit, grade %s" % sf["grade"]


def _thunk_w6_grade_vocabulary_pairing():
    mod = _load_module()
    assert set(mod.STRENGTH_ORDER) == set(mod.REFUTATION_FACES), \
        "strength vocabulary must pair with refutationForms"
    assert tuple(mod.STRENGTH_CLASS_TO_FORM.values()) and \
        set(mod.STRENGTH_CLASS_TO_FORM.values()) <= set(mod.REFUTATION_FACES), \
        "class-to-form table must map into the five-word vocabulary"
    sf = mod.strength_face("some genuine hypothesis face", True, "X")
    assert sf["grade"] == "full", "clean face must grade full"
    sf2 = mod.strength_face("body True", True, "X")
    assert sf2["grade"] in mod.REFUTATION_FACES, "graded outside the vocabulary"
    return "vocabulary pairs with refutationForms on the face and the table"


def run_segment_vacgen():
    """E5 segment contract: (passed, failed, skipped, results)."""
    results = []
    if not os.path.isfile(VACGEN):
        results.append(("SKIP", "import-face",
                        "tools/vacgen.py not landed yet (%s)" % VACGEN))
        return 0, 0, 1, results
    check(results, "import-face", _thunk_import_face)
    check(results, "p25-instance-clean-prefix", _thunk_p25_instance_clean_prefix)
    check(results, "p25-anon-instance-unchanged", _thunk_p25_anon_instance_unchanged)
    check(results, "p25-conjunct-source-only", _thunk_p25_conjunct_source_only)
    check(results, "p25-free-var-family", _thunk_p25_free_var_family)
    check(results, "p25-g1-trial-byte-stable", _thunk_p25_g1_trial_byte_stable)
    check(results, "w5-canonical-face", _thunk_w5_canonical_face)
    check(results, "w5-limb-family-bounds", _thunk_w5_limb_family_bounds)
    check(results, "w5-data-limb-rehomed", _thunk_w5_data_limb_rehomed)
    check(results, "w5-cast-time-reject", _thunk_w5_cast_time_reject)
    check(results, "w5-zero-false-positives-cli", _thunk_w5_zero_false_positives_cli)
    check(results, "w5-check-row-in-report", _thunk_w5_check_row_in_report)
    check(results, "w6-strength-face-green", _thunk_w6_strength_face_green)
    check(results, "w6-exit-semantics-unchanged", _thunk_w6_exit_semantics_unchanged)
    check(results, "w6-grade-vocabulary-pairing", _thunk_w6_grade_vocabulary_pairing)
    for tmp in _TMP_DIRS:
        shutil.rmtree(tmp, ignore_errors=True)
    del _TMP_DIRS[:]
    passed = sum(1 for status, _n, _d in results if status == "PASS")
    failed = sum(1 for status, _n, _d in results if status == "FAIL")
    skipped = sum(1 for status, _n, _d in results if status == "SKIP")
    return passed, failed, skipped, results


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        sys.stderr.write("usage error: this segment takes no arguments\n")
        return 2
    passed, failed, skipped, results = run_segment_vacgen()
    for status, name, detail in results:
        print("%s vacgen/%s -- %s" % (status, name, detail))
    print("SEGMENT vacgen passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    print("SUMMARY segments=1 passed=%d failed=%d skipped=%d"
          % (passed, failed, skipped))
    if failed:
        print("TOTAL-VACGEN-SEGMENT RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-VACGEN-SEGMENT GREEN (%d passed, %d skipped)"
          % (passed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
