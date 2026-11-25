#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_recipe_s07.py — selftest for the recipe face
recipes/S07_projection_reanchor_E5.md (rocqwash tests/; five checks,
precedent-anchored; check roster in the extended contract comment below).

Purpose.  Guard the S07 projection re-anchor recipe in the tree: the
  recipe face must stay present with its precedent anchor word face
  complete, and the E5 machine check must keep its judgment on fixture
  statements — a sick statement face hits, comment-masked tokens hit
  zero, a cured face hits zero — with the frozen sanitize engine imported
  read-only as the masking oracle and the engine md5 re-asserted against
  the registered value.

Interface.  python3 -B tests/test_recipe_s07.py; suite lane `t_recipe_s07`
  (tests/run_tests.sh).

Dependencies.  Python 3 standard library only; zero network, zero
  compilation, zero repository writes; fixtures live in a mkdtemp directory
  removed in finally; the frozen engine is imported read-only.

Evidence.  Precedent source `sandbox/seat_reanchor/账/迁移账-六件重锚.md`
  (UpReqSampling case: magic 293->0; three mappings, 118 tokens; 96-line
  pulse; statement names 51=51/67=67 zero drift); the recipe face was
  documented November 1, 2026, by agent `rqsupport`.  RECIPE_ANCHORS moves
  in lockstep with the recipe face (the anchor-must-move rule).

Exit-codes.  0 = all five checks pass; 1 = any check failing.
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  The five checks,
# in execution order:
#   1 recipe present + RECIPE_ANCHORS anchor word face complete
#   2 E5 sick-face negative: a bare statement-surface projection
#     (`req (f s) (g s)`, Lemma signature position) hits the machine check
#   3 comment-masking negative: the same token inside (*...*) comments,
#     nested included, hits zero (the comment-stripping state machine
#     matches the frozen scan/mac_stmt_scan.py:104 word face; reused
#     through a read-only wash/wash_engine.py import, zero byte touch of
#     the frozen sibling)
#   4 cured-face positive: the re-anchored fixture (real_eq/real_lt/
#     real_le concrete faces) hits zero
#   5 frozen collateral: wash/wash_engine.py md5 equals the registered
#     frozen value eed0699a... (read-only import, zero touch)
# Idempotence: the temp directory is written and cleaned in the same run;
# zero repository writes, zero compilation, zero network.
import hashlib
import io
import os
import re
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPE = os.path.join(REPO, "recipes", "S07_projection_reanchor_E5.md")
ENGINE = os.path.join(REPO, "wash", "wash_engine.py")
ENGINE_FROZEN_MD5 = "b06bd886d4e47bb9cd2be1dd4e857e81"  # generation-2 frozen value (`更新账.md` generation-2 section, November 26, 2026)

RECIPE_ANCHORS = [
    "E5", "S07_RealSetoidExpLog.v:8075", "S07_RealSetoidExpLog.v:8740",
    "S02_CauchyComplete.v", "293", "96 lines", "118",
    "real_eq", "real_lt", "real_le",
    "436f7121", "UpReqSampling", "cure",  # the four-acceptance-check section words (anchor migrated to the English face token, unit u8)
]

# statement-head command words (recipe application face: signature
# statements carry Variable/Hypothesis slots; the E5 precedent census of
# 51 statements)
STMT_HEAD = re.compile(r"^\s*(Theorem|Lemma|Corollary|Proposition|Example|Remark|Fact|"
                       r"Definition|Fixpoint|Function|Instance|"
                       r"Variable|Variables|Hypothesis|Hypotheses)\b")
BARE_PROJ = re.compile(r"(?<![A-Za-z0-9_'])(req|lt|le)(?![A-Za-z0-9_'])")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def statement_bare_hits(text):
    """E5 sick-face machine check: after comment/string masking (the frozen
    engine state machine, read-only import), find bare projection tokens on
    statement surfaces.  A statement surface runs from a statement-head line
    to the period that closes it (the precedent signature faces are
    multi-line runs — `forall ...` continuation lines share the head-line
    treatment).  Returns hits [(line, token)].  The cured face (real_eq and
    the other concrete names) carries no bare token shape and hits zero
    naturally."""
    sys.path.insert(0, os.path.dirname(ENGINE))
    import wash_engine  # noqa: E402 (frozen in-service module; imported read-only, never modified)
    clean = wash_engine.strip_comments_strings(text)
    lines = clean.split("\n")
    hits = []
    in_stmt = False
    for lineno, line in enumerate(lines, 1):
        if STMT_HEAD.match(line):
            in_stmt = True
        if in_stmt:
            for m in BARE_PROJ.finditer(line):
                hits.append((lineno, m.group(1)))
            if line.rstrip().endswith("."):
                in_stmt = False  # the period closes the statement (Proof./Qed. close the same way)
    return hits


def main():
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_trecipes07_")
    try:
        # check 1: recipe present + anchor word face complete
        ok1 = os.path.isfile(RECIPE)
        if ok1:
            with io.open(RECIPE, encoding="utf-8") as fh:
                doc = fh.read()
            missing = [a for a in RECIPE_ANCHORS if a not in doc]
            ok1 = not missing
        else:
            missing = ["<处方件整缺>"]
        check("处方件锚词面", ok1, "missing=%s" % missing)

        # check 2 (E5 sick-face negative): bare statement-surface projections -> hits
        sick = ("(* req lt le 注释位裸 token 不算 *)\n"
                "Section S.\n"
                "Variable sumf : (Real -> Real) -> Real.\n"
                "Lemma row_norm : forall (f : Real -> Real),\n"
                "  (forall s : Real, req (f s) (f s)) -> req (sumf f) (sumf f).\n"
                "Proof. intros. apply H. Qed.\n"
                "End S.\n")
        hits = statement_bare_hits(sick)
        check("E5_病面负例_命中", len(hits) == 2 and all(t == "req" for _, t in hits)
              and hits[0][0] == 5,  # multi-line statement runs share treatment (two bare projections on the L5 continuation)
              "hits=%s" % hits)

        # check 3 (comment-masking negative): every bare projection sits inside
        # nested comments -> zero hits (the whole-word rule must not bite on substrings)
        masked = ("(* Lemma ghost : req x y -> lt a b. （病面示范·注释位不进提取面） *)\n"
                  "(* 外 (* 内嵌 lt le req *) 注释 *)\n"
                  "Lemma fine : mult one one = one. (* mult 内含 lt 子串·全词律不咬 *)\n"
                  "Proof. reflexivity. Qed.\n")
        hits_m = statement_bare_hits(masked)
        check("注释掩蔽负例_零命中", hits_m == [], "hits=%s" % hits_m)

        # check 4 (cured-face positive): the re-anchored fixture (three mappings
        # applied; the UpReqSampling precedent shape) -> zero hits
        cured = sick.replace("req (f s) (f s)) -> req (sumf f) (sumf f)",
                             "real_eq (f s) (f s)) -> real_eq (sumf f) (sumf f)")
        hits_c = statement_bare_hits(cured)
        check("E5_愈面正判_零命中", hits_c == [] and "real_eq" in cured,
              "hits=%s" % hits_c)

        # check 5 (frozen collateral): engine md5 still equals the registered
        # frozen value (read-only import, zero touch)
        check("冻结件零触", md5_of(ENGINE) == ENGINE_FROZEN_MD5,
              "md5=%s" % md5_of(ENGINE))

        fails = [c for c in checks if not c[1]]
        for name, ok, detail in checks:
            print("  %-18s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))
        if fails:
            print("TEST-RECIPE-S07 FAIL: %d/%d failing" % (len(fails), len(checks)))
            return 1
        print("TEST-RECIPE-S07 PASS: recipe anchors / E5 sick-face hits / comment "
              "masking zero hits / cured face zero hits / frozen collateral — all "
              "five checks pass (five-lesson fixture 5, S07 projection re-anchor E5)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
