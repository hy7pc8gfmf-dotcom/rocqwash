#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_vacgen_envelope_shape.py -- witness-envelope word-face shape selftest (zero-network, zero-compile).

Purpose.
    The witness envelope (the `..._premises_witness` theorem of the cast) must be well-typed
    Lean: every conjunct a Prop, every referenced binder bound by an existential prefix
    segment.  A bare TYPE in the conjunction chain (word-face signature `∧ Set (`) is
    always ill-typed (`Set X : Type`, never a Prop) and always leaves the binder unbound.
    Fixture A (well-formed face) must yield a well-formed envelope: red = REGRESSION.
    Fixture B (implicit-binder face) is the FLIPPED ENGINE-REPAIR PIN (docs/vacgen_sop.md
    section 2.5 erratum): the November 14, 2026 known-debt pin (debt signature present,
    cast green) was flipped on November 22, 2026 with the cast-repair work-stream registration
    (knife 1: L1 data-limb re-homing seats the implicit `{K : Set (...)}` binder into
    the existential prefix, vacgen.py sort_binders_into_segments/is_data_limb_face; the
    2.1.0 W5 cast-time front gate had made the old debt pin unreachable rc=1 before
    this flip).  Full pin contract beside DEBT_SIG below.

Interface.
    python -I tests/t_vacgen_envelope_shape.py   (no flags; PASS/SKIP/FAIL to stdout)

Dependencies.
    Python 3 stdlib only (os, re, subprocess, sys, tempfile); zero network, zero compile; Lean compile leg
    design-SKIP unconditionally (zero-compile suite); loud SKIP (rc 0) when tools/vacgen.py is absent.

Evidence.
    NOT a run_tests.sh CASES roster case (the roster never lists
    t_vacgen_envelope_shape; tests/run_tests.sh keeps a dead function shell for it
    that is never invoked - the stale "suite case" docstring claim was corrected
    with the pin flip).  Standalone run face only.  Contract vectors: DEBT_SIG
    and the pin comments below; fixture B green state prints the flip
    registration loud.

Exit-codes.
    0 = all checks pass (design-SKIP legs reported, never counted red); 1 = any red (fail-loud listing).
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VACGEN = os.path.normpath(os.path.join(HERE, "..", "tools", "vacgen.py"))

# Contract pins (fixtures below):
# - fixture A (well-formed face: one implicit statement variable, one Prop
#   hypothesis): the envelope MUST be well-formed - no bare-type conjunct, the
#   S1 variable bound by its prefix segment.  Red here means a REGRESSION on
#   well-formed faces.
# - fixture B (implicit-binder face: replica of the batch-1 item-16 shape,
#   implicit `{K : Set (Fin n → ℝ)}` binder): the FLIPPED ENGINE-REPAIR PIN
#   (docs/vacgen_sop.md section 2.5 erratum re-audit condition, flipped
#   November 22, 2026 with the cast-repair work-stream registration).  Pin contract:
#   cast rc=0, the debt signature `∧ Set (` ABSENT (red here = the knife-1
#   re-homing regressed and the ill-typed conjunction is back - never revert
#   the engine to keep an older pin green), and K bound by its re-homed
#   prefix segment `∃ (K : Set (…))`.  The companion face (explicit
#   hypotheses existentialized as "vars", e.g. `∃ (hK : IsCompact K)`) is
#   documented in the erratum but not pinned (formatting-sensitive word
#   face).
#
# Word-face debt signature: a bare `Set (...)` type as a conjunction member.
# `Set X : Type` can never appear as a well-formed Prop conjunct, so this
# signature has no false-positive face on well-formed envelopes.
DEBT_SIG = re.compile(r"∧\s*Set\s*\(")


def _cast(tmp, name, source):
    fx = os.path.join(tmp, name)
    with open(fx, "w", encoding="utf-8") as f:
        f.write(source)
    out = os.path.join(tmp, "out_" + name)
    r = subprocess.run([sys.executable, "-I", VACGEN, "--in", fx, "--out", out],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r, out


def _envelope_line(out):
    path = os.path.join(out, "witness.lean")
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("theorem ") and "premises_witness" in line:
                return line.rstrip("\n"), path
    return None, path


FIXTURE_A = (
    "import Mathlib.NumberTheory.LSeries.RiemannZeta\n\n"
    "namespace VacgenEnvelopeShapeA\n\n"
    "theorem demo_zero_face {s : CC} (hs : (7 / 8 : RR) < s.re) : riemannZeta s != 0 := by\n"
    "  sorry\n\n"
    "end VacgenEnvelopeShapeA\n"
).replace("EXISTS", chr(0x2203)).replace("CC", chr(0x2102)).replace("RR", chr(0x211D)).replace("!=", chr(0x2260))

FIXTURE_B = (
    "import Mathlib\n\n"
    "namespace VacgenEnvelopeShapeB\n\n"
    "theorem demo_symmetric_compact {n : NN} (hn : 1 ≤ n) {K : Set (Fin n → RR)}\n"
    "    (hK : IsCompact K) (hconv : Convex RR K) (hsym : ∀ x ∈ K, -x ∈ K) :\n"
    "    n != 0 := by\n"
    "  sorry\n\n"
    "end VacgenEnvelopeShapeB\n"
).replace("NN", chr(0x2115)).replace("RR", chr(0x211D)).replace("!=", chr(0x2260))


def main() -> int:
    if not os.path.isfile(VACGEN):
        print("SKIP: tools/vacgen.py not found (design-SKIP face)")
        return 0
    tmp = tempfile.mkdtemp(prefix="vacgen_envelope_shape_")
    fails = []

    # ---- fixture A: well-formed-envelope contract (regression pin) ----
    r, out = _cast(tmp, "fixture_a.lean", FIXTURE_A)
    if r.returncode != 0:
        fails.append("fixture A: cast rc=%d (cast itself failed)" % r.returncode)
    else:
        line, path = _envelope_line(out)
        if line is None:
            fails.append("fixture A: no premises_witness theorem line in %s" % path)
        else:
            if DEBT_SIG.search(line):
                fails.append("fixture A: REGRESSION - bare-type conjunct in the "
                             "envelope line: %s" % line.strip())
            if not re.search(r"∃\s*\(\s*s\s*:\s*ℂ\s*\)", line):
                fails.append("fixture A: S1 variable s not bound by a prefix "
                             "segment: %s" % line.strip())

    # ---- fixture B: flipped engine-repair pin (SOP section 2.5 erratum) ----
    r, out = _cast(tmp, "fixture_b.lean", FIXTURE_B)
    if r.returncode != 0:
        fails.append("fixture B: cast rc=%d (the re-homed face must cast green)"
                     % r.returncode)
    else:
        line, path = _envelope_line(out)
        if line is None:
            fails.append("fixture B: no premises_witness theorem line in %s" % path)
        else:
            if DEBT_SIG.search(line):
                fails.append("fixture B: REGRESSION - debt signature '∧ Set (' "
                             "reappeared in the envelope (knife-1 re-homing "
                             "regressed): %s" % line.strip())
            if not re.search(r"∃\s*\(\s*K\s*:\s*Set\s*\(\s*Fin\s+n\s*→\s*ℝ\s*\)\s*\)",
                             line):
                fails.append("fixture B: implicit data binder K not re-homed "
                             "into the existential prefix: %s" % line.strip())
        if not fails:
            print("== ENGINE-REPAIR PIN GREEN (flipped per SOP section 2.5 "
                  "erratum) ==")
            print("   implicit data binder K rides the existential prefix; the "
                  "debt signature is absent (cast-repair wave, November 22, "
                  "2026).")

    # ---- Lean compile leg: design-SKIP ----
    print("SKIP: Lean compile leg design-SKIP (zero-compile suite)")

    print("== t_vacgen_envelope_shape: %d pass / %d red =="
          % (2 - len(fails), len(fails)))
    for msg in fails:
        print("FAIL:", msg)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
