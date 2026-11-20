#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# selftest-exempt: covered by suite cases t_vacgen_shape / t_vacgen_expectedred (roster PASS) + the vacgen segment of t_refinery (envelope wording)
"""vacgen.py (v2) - vacuity probe skeleton generator with shape recognition (four-layer engine, taxonomy-as-data).

Purpose.
    Cast the four-account vacuity probe skeleton directory for a Lean statement-face file (cast mode, v1 CLI face
    preserved verbatim) and run a zero-compile coverage preflight over a census-qualified file set
    (--preflight-all, difficulty map).  v2 layers: L1 premise decomposer (three-segment split, file-scope
    `variable` / instance-binder G1 fix), L2 taxonomy lookup (rows in taxonomy.json; zero premise-family knowledge
    in-engine), L3 confidence scoring with honest TODO-SEAT degradation (counted, never silent), L4 harness modes.

Interface.
    python -I vacgen.py --in <file.lean> --out <dir>            (cast, v1 face)
    python -I vacgen.py --preflight-all --census <census.json>  --root <clone>
            [--report <difficulty-map.json>] [--cluster-table <json>]
    python -I vacgen.py --verify-anchors --mathlib <root> --taxonomy <path>

Dependencies.
    Python stdlib only: argparse, hashlib, os, re, sys, datetime, fractions (v1 import face, vacgen.py:42-48) plus
    json (stdlib; required by the taxonomy loader, arch-spec-v2.md section 3.3 pseudocode).  Zero network,
    zero compile, python -I compatible.

Evidence.
    The tool casts skeletons and never asserts mathematics - every artifact-facing proof obligation is a declared
    TODO-SEAT agent; coverage scores are word-face lower bounds; counters are closed-window dated snapshots,
    cross-run comparisons use monotone bounds only (attestation: suite cases t_vacgen_shape,
    t_vacgen_envelope_shape, t_vacgen_expectedred in tests/run_tests.sh).

Exit-codes.
    0 = verdict ok=true (all bound-form checks green); 1 = verdict ok=false (blocked checks,
    taxonomy or anchor drift); 2 = usage error (mode exclusivity, missing --in).
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from fractions import Fraction

TOOL_NAME = "vacgen"
# Lineage.  v1 tool: D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/_tools/vacgen.py
#   (helpers inherited verbatim where marked).  Architecture spec:
#   D:/ComplexAnalysis/attn/_vacgenv2_20261113/staging/arch-spec-v2.md (contracts
#   C2.x/C3.x/C4.x/C5.x/C6.x/C7.x).  Master work order: the vacgenV2 task
#   instruction dated November 13, 2026.  Discipline: artifact-verifier-design-law
#   (monotone bounds on live counters), negative-finding-boundary-law (four
#   elements on every coverage claim), taxonomy-as-data, TODO-SEAT honest
#   degradation, dry-run self-certification.
# 2.0.1 (repair ring, November 13, 2026): C4.2 theorem-declaration front gate added in
# decompose_head (cast mode) - non-theorem-face heads (def/class/axiom/
# structure/abbrev/opaque) front-reject with marker `non-theorem-declaration`,
# never classified, never fire `recognized` (negative-sample piece D fix).
# 2.1.0 (P2-2 envelope double-layer fix): (a) L1 splitter
# re-homes named instance binders - `[inst : Foo A]` splits into binder name
# plus clean type, and the existential prefix renders `(_ : Foo A)` (the
# previous face leaked the name into the type position, `(_ : inst : Foo A)`).
# (b) W5 cast-time self-check internalized: the witness envelope's premise
# conjunction is front-gated at cast time; a bare-type conjunct limb
# (canonical word face "∧ Set (", plus the self-built per-limb family) cannot
# elaborate as a Prop, so the deformed cast dies rc=1 with marker
# `bare-type-conjunct-limb` before any skeleton text is emitted.  (c) W6
# two-dimensional verdict: after a GREEN cast the degenerate battery word-face
# scans the witness envelope (emptyset / single-point / zero-element /
# top-type / always-true faces) and the report verdict gains the `strength`
# face over the refutationForms five-word vocabulary; degeneracy is data, the
# exit-code semantics never change, and battery counters carry monotone
# bounds only (never exact-equality invariants, per the artifact-verifier
# design law).
TOOL_VERSION = "2.1.0"

DEFAULT_GUARD = "D:/ComplexAnalysis/infra/thermal/cpu_guard_v3.ps1"
DEFAULT_LAKE = "C:/Users/Live/.elan/bin/lake.exe"
DEFAULT_WORKTREE = "D:/ComplexAnalysis/attn/f2d1_sbx_20261112/worktree"
DEFAULT_CORE = 4
DEFAULT_TOOLCHAIN = "v4.35.0-rc3"
DEFAULT_SNAPSHOT = ("worktree mathlib cache: 8,567 oleans / 8,548 .lean files "
                    "@ 2026-11-12 (session default; override with --snapshot)")

REFUTATION_FACES = ("full", "point", "tactics", "noclassic", "band")
HEADER_FIELDS = ("Audit ID:", "Statement face", "Verdict semantics", "Build", "Expected-fail")
AXIOM_PROFILE = "propext / Classical.choice / Quot.sound"

OPENER_TO_CLOSER = {"(": ")", "{": "}", "[": "]", "\u23a3": "\u23a4"}  # ⦃ : ⦄
CLOSERS = set(OPENER_TO_CLOSER.values())


class ParseError(Exception):
    pass


# ---------------------------------------------------------------- text tools
# ---- verbatim inheritance from v1 (vacgen.py:75-247; contract C2.5) ----

def lean_strip_comments(src):
    """Strip Lean comments (nested /- -/ blocks and -- line comments).

    Comment content is dropped (word separators preserved) so token scans and
    declaration detection never see comment text (comment-blind scans are a
    known false-positive source)."""
    out = []
    i = 0
    n = len(src)
    depth = 0
    while i < n:
        if src.startswith("/-", i):
            depth += 1
            i += 2
            if depth == 1 and out and out[-1] not in " \n\t":
                out.append(" ")
            continue
        if depth > 0 and src.startswith("-/", i):
            depth -= 1
            i += 2
            continue
        if depth == 0 and src.startswith("--", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if depth == 0:
            out.append(src[i])
        elif src[i] == "\n":
            out.append("\n")
        i += 1
    return "".join(out)


def iter_code_lines(raw_lines):
    """Yield (lineno0, code_text) for lines carrying code (comments stripped
    within each line; block-comment depth tracked across lines)."""
    depth = 0
    for idx, line in enumerate(raw_lines):
        parts = []
        i = 0
        n = len(line)
        while i < n:
            if line.startswith("/-", i):
                depth += 1
                i += 2
                continue
            if depth > 0 and line.startswith("-/", i):
                depth -= 1
                i += 2
                continue
            if depth == 0 and line.startswith("--", i):
                break
            if depth == 0:
                parts.append(line[i])
            i += 1
        code = "".join(parts)
        if code.strip():
            yield idx, code


def scan_balanced(s, start):
    """Return (end_index_exclusive, inner_text) for the bracket group starting
    at s[start]; raises ParseError on imbalance."""
    closer = OPENER_TO_CLOSER.get(s[start])
    if closer is None:
        raise ParseError("not an opener at offset %d" % start)
    stack = [closer]
    i = start + 1
    n = len(s)
    while i < n and stack:
        c = s[i]
        if c in OPENER_TO_CLOSER:
            stack.append(OPENER_TO_CLOSER[c])
        elif c in CLOSERS:
            if stack[-1] != c:
                raise ParseError("bracket mismatch at offset %d" % i)
            stack.pop()
        i += 1
    if stack:
        raise ParseError("unbalanced brackets starting at offset %d" % start)
    return i, s[start + 1:i - 1]


def find_decl_end(code):
    """Index of the first top-level ':=' (bracket-depth aware), or -1."""
    depth = 0
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c in OPENER_TO_CLOSER:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ":" and i + 1 < n and code[i + 1] == "=":
            return i
        i += 1
    return -1


def find_top_colon(code):
    """Index of the first top-level ':' (not ':='), bracket-depth aware, or -1."""
    depth = 0
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c in OPENER_TO_CLOSER:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ":":
            if i + 1 < n and code[i + 1] == "=":
                i += 2
                continue
            return i
        i += 1
    return -1


DECL_LINE_RE = re.compile(
    r"^[ \t]*(theorem|lemma|def|abbrev|example|instance|axiom|opaque)[ \t]+([^\s(:\[{]+)"
)

IMPORT_LINE_RE = re.compile(r"^[ \t]*(?:public\s+)?import\s+\S")

# C4.2 theorem-declaration front gate (repair ring, November 13, 2026, negative-sample
# piece D): only theorem-face heads may reach the L2 classifier.  def / class /
# axiom / structure / abbrev / opaque (and any other non-theorem-face) heads
# are FRONT-REJECTED in cast mode with the honest marker
# `non-theorem-declaration` - they are never classified, never fire
# `recognized`.  `class`/`structure` never match DECL_LINE_RE at all, so they
# cannot become heads either way; the gate set follows the repair directive.
THEOREM_HEAD_KWS = ("theorem", "lemma", "example", "instance")


def looks_like_type(t):
    """Conservative shape test: is this binder type a plain type expression
    (identifiers joined by arrows) rather than a proposition?  Used only to
    split statement variables from hypotheses for the envelope/probe faces;
    everything ambiguous is treated as a hypothesis (fail-safe side)."""
    t = t.strip()
    if not t or "Prop" in t:
        return False
    if re.search(u"[\u003c\u2264\u2265\u2260\u00ac\u2208\u2209\u2200\u2203\u2194]", t):
        return False  # < <= >= != not in notin forall exists iff
    if re.search(r"(?<![<>=\u2264\u2265])=(?![=>])", t):
        return False  # bare equality
    for side in re.split(r"\u2192|->", t):
        side = side.strip()
        if not side:
            return False
        if side == "Type" or re.fullmatch(r"Type \d+", side):
            continue
        if not re.fullmatch(r"[^\W\d][\w'.!]*", side):
            return False
    return True


CONST_ALT = (r"(?:\(\s*(?P<n>\d+)\s*/\s*(?P<d>\d+)\s*:\s*[\u211d]\s*\)"
             r"|(?P<bn>\d+)\s*/\s*(?P<bd>\d+)"
             r"|\(\s*(?P<in>\d+)\s*:\s*[\u211d]\s*\))")
PREMISE_INEQ_RE = re.compile(
    r"^\s*(?P<const>" + CONST_ALT + r")\s*<\s*(?P<var>[A-Za-z_\u0100-\uffff][\w'.!]*)"
    r"\s*\.\s*re\s*$"
)


def parse_const_fraction(const_text):
    """Extract (num, den, bare_text) from a matched constant string."""
    m = re.fullmatch(r"\(\s*(\d+)\s*/\s*(\d+)\s*:\s*\u211d\s*\)", const_text.strip())
    if m:
        return int(m.group(1)), int(m.group(2)), "%s / %s" % (m.group(1), m.group(2))
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", const_text.strip())
    if m:
        return int(m.group(1)), int(m.group(2)), "%s / %s" % (m.group(1), m.group(2))
    m = re.fullmatch(r"\(\s*(\d+)\s*:\s*\u211d\s*\)", const_text.strip())
    if m:
        return int(m.group(1)), 1, str(int(m.group(1)))
    return None


# ---------------------------------------------------------------- L1 decomposer
# Three-segment split (arch-spec-v2.md section 2; probe-verified logic from
# _scratch/l1_probe.py, which passed its dry run on the G1 repro face, the
# zeta native face, and a real corpus file).

PROP_MARK = re.compile("[<\u2264\u2265\u2260\u00ac\u2208\u2209\u2200\u2203\u2194]")
BARE_EQ = re.compile(r"(?<![<>=\u2264\u2265])=(?![=>])")
SYM_TOK = re.compile(r"[^\W\d][\w'.!]*|[\u211d\u2124\u2115\u211a\u2102]|\d+|_", re.UNICODE)
IDENT_TOK = re.compile(r"[^\W\d][\w'.!]*", re.UNICODE)

VARCMD_RE = re.compile(r"^[ \t]*variables?[ \t]+")


def looks_like_type_v2(t):
    """v1 semantics + universe-star forms (Type*/Sort*) as data types.
    Star forms are accepted per arrow-chain side (v1's side-based loop is the
    semantics being extended; registered interpretation choice R-2 - a bare
    `x : iota -> Type*` binder is a data binder, not a hypothesis)."""
    t = t.strip()
    if t.endswith("*") and t[:-1].rstrip() in ("Type", "Sort"):
        return True
    sides = re.split(r"→|->", t)
    if len(sides) > 1:
        ok = True
        for side in sides:
            side = side.strip()
            if not side:
                ok = False
                break
            if side in ("Type", "Type*", "Sort", "Sort*") or re.fullmatch(r"Type \d+", side):
                continue
            if not re.fullmatch(r"[^\W\d][\w'.!]*", side):
                ok = False
                break
        if ok:
            return True
    return looks_like_type(t)


def looks_like_data_type(t):
    """Two-step data/proposition classifier (C2.3).
    True  -> S1 binder var (existentialize in the envelope);
    False -> S2 assumption (conjunct) -- the fail-safe side."""
    t = t.strip()
    if looks_like_type_v2(t):
        return True
    if PROP_MARK.search(t) or BARE_EQ.search(t):
        return False  # any proposition marker -> hypothesis (v1 face kept)
    if "(" in t or ")" in t:
        return False  # parenthesized form -> hypothesis (e.g. IsClosed (I : Set A))
    toks = t.split()
    return len(toks) >= 2 and all(SYM_TOK.fullmatch(tok) for tok in toks)


CONCL_BINDER_RE = re.compile(
    r"[∃∀]\s*([A-Za-z_Ā-￿][\w'.!]*(?:\s+[A-Za-z_Ā-￿][\w'.!]*)*)")
CONCL_PAREN_BINDER_RE = re.compile(r"\(([^():\n]{1,60}):\s")


def conclusion_local_names(conclusion):
    """Names the conclusion binds locally (`∃ D : ℕ`, `∀ j (x : T)`,
    `∀ x y : U`) - these shadow scope variables and must not count as
    references when filtering file-scope binders (R-1 v2)."""
    out = set()
    for m in CONCL_BINDER_RE.finditer(conclusion):
        out.update(m.group(1).split())
    for m in CONCL_PAREN_BINDER_RE.finditer(conclusion):
        out.update(m.group(1).split())
    return out


def relevant_scope_binders(scope_binders, binder_region, conclusion, head_line0):
    """R-1 v3 (registered refinement): keep only file-scope binders that
    precede the head declaration AND are referenced by the head statement
    face, judged BY NAME (the v1 parity principle: a variable reference is a
    binder name appearing in the statement face, vacgen.py:343).  The
    conclusion's locally bound names are excluded (they shadow scope
    variables).  Unnamed instance binders are kept in a second pass when
    their type references a kept name or a signature-region name.  Merging
    every file-wide `variable` command degenerates the envelope on
    multi-section files (measured: 149 prefixes on CoarseAssembly.lean, with
    literal-type tokens like N/Q/Z polluting a type-content reference test).
    The trial-item1 G1 face keeps all its binders (A named-referenced;
    instance types reference A)."""
    refs = set()
    for tok in IDENT_TOK.findall(binder_region + " : " + conclusion):
        refs.update(tok.split("."))
    refs -= conclusion_local_names(conclusion)
    kept_names = set()
    named_kept = []
    inst_candidates = []
    for b in scope_binders:
        if b.get("line0", 0) >= head_line0:
            continue
        if b["kind"] == "instance":
            inst_candidates.append(b)
            continue
        names = [n for n in (b.get("names") or []) if n != "_"]
        if any(n in refs for n in names):
            named_kept.append(b)
            kept_names.update(names)
    sig_refs = set()
    for tok in IDENT_TOK.findall(binder_region + " : " + conclusion):
        sig_refs.update(tok.split("."))
    sig_refs -= conclusion_local_names(conclusion)
    kept_insts = []
    for b in inst_candidates:
        toks = set()
        for tok in IDENT_TOK.findall(b.get("type", "")):
            toks.update(tok.split("."))
        if toks & (kept_names | sig_refs):
            kept_insts.append(b)
    return named_kept + kept_insts


def collect_variable_commands(code_lines, tolerant=False):
    """G1 fix: file-scope `variable`/`variables` binders become first-class
    records.  v1 swallowed these into premise text (trial item1 G1 gap).
    R-3: a command whose binder region continues onto following lines is
    joined until bracket balance (mechanical word-face continuation; the
    corpus carries multi-line variable commands, measured on
    EditApproximation.lean:13197 and CKSBondiPenrose.lean:2742).  With
    tolerant=True (preflight path) a command that never balances is
    skipped and counted in the returned degraded total instead of
    raising; cast mode keeps the fail-loud ParseError (C2.4)."""
    out = []
    degraded = 0
    lines = list(code_lines)
    n = len(lines)
    i = 0
    while i < n:
        idx, code = lines[i]
        if VARCMD_RE.match(code):
            region = code[code.index("variable") + len("variable"):]
            bs = None
            while True:
                try:
                    bs = parse_binders(region)
                    break
                except ParseError:
                    if i + 1 < n:
                        i += 1
                        region = region + " " + lines[i][1]
                        continue
                    if tolerant:
                        degraded += 1
                        break
                    raise ParseError(
                        "variable-command binder region unbalanced at line %d" % (idx + 1))
            if bs is not None:
                for b in bs:
                    b = dict(b)
                    b["source"] = "file-scope-variable"
                    b["line0"] = idx
                    out.append(b)
        i += 1
    if tolerant:
        return out, degraded
    return out


def scan_decls(code_lines):
    """All declarations (verbatim v1 :278-285 collection face)."""
    decls = []
    for idx, code in code_lines:
        dm = DECL_LINE_RE.match(code)
        if dm:
            decls.append({"kw": dm.group(1), "name": dm.group(2), "line0": idx})
    return decls


def decl_span(raw_lines, code_lines, decls, start0):
    """Raw span of one declaration: from its line to the line before the next
    declaration or the closing `end` line (blank-trimmed; verbatim v1 :287-300)."""
    later = [d["line0"] for d in decls if d["line0"] > start0]
    ends = [idx for idx, code in code_lines
            if idx > start0 and re.match(r"^[ \t]*end\b", code)]
    cut_candidates = later + ends
    end0 = (min(cut_candidates) if cut_candidates else len(raw_lines))
    span = raw_lines[start0:end0]
    while span and not span[-1].strip():
        span.pop()
    while span and not span[0].strip():
        span.pop(0)
    return span


def split_signature(joined, head_name):
    """v1 signature surgery (verbatim :302-318): top-level ':=' then top ':'.
    Returns (binder_region, conclusion).  Raises ParseError fail-loud."""
    name_pos = joined.find(head_name)
    if name_pos < 0:
        raise ParseError("declaration name not located after comment stripping")
    after_name = joined[name_pos + len(head_name):]
    decl_end = find_decl_end(after_name)
    if decl_end < 0:
        raise ParseError("no top-level ':=' found in the declaration")
    sig_text = after_name[:decl_end].strip()
    ci = find_top_colon(sig_text)
    if ci < 0:
        raise ParseError("no top-level ':' found in the signature")
    return sig_text[:ci], sig_text[ci + 1:].strip()


def split_instance_binder(text):
    """Split a named instance binder face `[inst : Foo A]` into
    (binder name, clean type).  Anonymous faces `[Foo A]` carry no top-level
    colon and return ("", text).  Only a TOP-LEVEL colon counts
    (find_top_colon is bracket-depth aware), and only a single plain
    identifier on the colon's left side is a binder name - anything else
    keeps the raw face.  This is the 2.1.0 L1 re-homing: without the split
    the existential prefix rendered the name into the type position
    (`_ : inst : Foo A`), a malformed Lean binder."""
    text = text.strip()
    ci = find_top_colon(text)
    if ci < 0:
        return "", text
    head = text[:ci].strip()
    ty = text[ci + 1:].strip()
    if head and ty and IDENT_TOK.fullmatch(head):
        return head, ty
    return "", text


def parse_binders(region):
    """Bracket scanner over a binder region (verbatim v1, vacgen.py:396-420):
    explicit (...) / implicit {...} with name lists, instance [...] binders,
    raw groups without a top-level colon.  2.1.0: instance binders carry the
    split result (instanceName / cleanType) alongside the raw type, so the
    envelope prefix renders the clean type while the falsify face keeps the
    v1 `[inst : Foo A]` form."""
    binders = []
    i = 0
    n = len(region)
    kind_map = {"(": "explicit", "{": "implicit", "⎣": "implicit", "[": "instance"}
    while i < n:
        c = region[i]
        if c in OPENER_TO_CLOSER:
            end, inner = scan_balanced(region, i)
            kind = kind_map[c]
            if kind == "instance":
                inst_nm, inst_ty = split_instance_binder(inner.strip())
                binders.append({"kind": kind, "names": [], "type": inner.strip(),
                                "instanceName": inst_nm, "cleanType": inst_ty})
            else:
                ci = find_top_colon(inner)
                if ci < 0:
                    binders.append({"kind": "raw", "names": [], "type": inner.strip()})
                else:
                    head_txt = inner[:ci].strip()
                    ty = inner[ci + 1:].strip()
                    names = head_txt.split() if head_txt else []
                    binders.append({"kind": kind, "names": names, "type": ty})
            i = end
        else:
            i += 1
    return binders


def sort_binders_into_segments(binders):
    """Route binders into S1 vars / S2 assumptions / S2 instance records
    (C2.2: one record per hypothesis, never merged; C2.3 two-step test)."""
    S1_vars, S2_assumps, S2_instances = [], [], []
    for b in binders:
        rec_source = b.get("source", "signature")
        if b["kind"] == "instance":
            S2_instances.append({"name": b.get("instanceName", ""),
                                 "type": b["type"],
                                 "cleanType": b.get("cleanType") or b["type"],
                                 "source": rec_source, "line0": b.get("line0")})
        elif looks_like_data_type(b["type"]):
            for nm in (b["names"] or ["_"]):
                S1_vars.append({"name": nm, "type": b["type"], "line0": b.get("line0")})
        else:
            for nm in (b["names"] or [""]):
                S2_assumps.append({"name": nm, "type": b["type"], "kind": b["kind"],
                                   "source": rec_source, "line0": b.get("line0")})
    return S1_vars, S2_assumps, S2_instances


def decompose_head(src):
    """Head-declaration decompose (cast mode; v1 :258-285 collection + head
    selection semantics: imports/module lines/namespace collected before the
    first declaration, verbatim v1 face)."""
    raw_lines = src.splitlines()
    code_lines = list(iter_code_lines(raw_lines))
    if not code_lines:
        raise ParseError("no code lines found in the statement-face file")
    imports = []
    namespace = None
    module_lines = []
    decls = []
    for idx, code in code_lines:
        if not decls and re.match(r"^[ \t]*module$", code):
            module_lines.append(code.strip())
            continue
        if not decls and re.match(r"^[ \t]*@\[expose\]", code):
            module_lines.append(code.strip())
            continue
        if not decls:
            if IMPORT_LINE_RE.match(code):
                imports.append(raw_lines[idx].strip())
                continue
            nm = re.match(r"^[ \t]*namespace\s+([^\s]+)", code)
            if nm and namespace is None:
                namespace = nm.group(1)
                continue
        dm = DECL_LINE_RE.match(code)
        if dm:
            decls.append({"kw": dm.group(1), "name": dm.group(2), "line0": idx})
    if not decls:
        raise ParseError("no theorem/lemma/def declaration found in the statement face")
    scope_binders = collect_variable_commands(code_lines)
    head_candidates = [d for d in decls if d["kw"] in ("theorem", "lemma")]
    head = (head_candidates[0] if head_candidates else decls[0])
    # C4.2 theorem-declaration front gate (repair ring, November 13, 2026): v1 head
    # selection is preserved verbatim, but a non-theorem-face head (the
    # `decls[0]` fallback with no theorem/lemma candidate) no longer reaches
    # the L2 classifier - negative-sample piece D showed a def-only face whose
    # builtin-shaped premise fired `recognized` HIGH (false positive).  The
    # gate front-rejects via ParseError -> cast fail-loud rc=1 (C2.4 lane,
    # same honest integration as pieces A/D2: no skeleton cast, audit agent must
    # transcribe the statement face by hand), marker `non-theorem-declaration`.
    if head["kw"] not in THEOREM_HEAD_KWS:
        raise ParseError(
            "non-theorem-declaration: head '%s %s' (line %d) carries no "
            "theorem-face keyword (theorem/lemma/example/instance); C4.2 "
            "front gate - def/class/axiom/structure/abbrev/opaque heads are "
            "front-rejected before classification and never fire `recognized`"
            % (head["kw"], head["name"], head["line0"] + 1))
    span = decl_span(raw_lines, code_lines, decls, head["line0"])
    joined = lean_strip_comments("\n".join(span))
    binder_region, conclusion = split_signature(joined, head["name"])
    sig_binders = parse_binders(binder_region)
    for b in sig_binders:
        b.setdefault("line0", head["line0"])
    scope_kept = relevant_scope_binders(scope_binders, binder_region,
                                        conclusion, head["line0"])
    binders = sorted(scope_kept + sig_binders, key=lambda b: b.get("line0", 0))
    S1_vars, S2_assumps, S2_instances = sort_binders_into_segments(binders)
    return {"status": "OK", "head": head, "head_raw_lines": span,
            "S1_vars": S1_vars, "S2_assumps": S2_assumps,
            "S2_instances": S2_instances, "S3_conclusion": conclusion,
            "scope_binders": scope_binders, "decls": decls,
            "imports": imports, "module_lines": module_lines, "namespace": namespace}


def select_theorem_lemma_decls(src):
    """Preflight full-declaration face (C5.4): all theorem/lemma declarations."""
    raw_lines = src.splitlines()
    code_lines = list(iter_code_lines(raw_lines))
    decls = scan_decls(code_lines)
    return raw_lines, code_lines, decls


def decompose_decl(raw_lines, code_lines, decls, head, scope_binders=None):
    """Per-declaration decompose for preflight; ParseError -> UNPARSED record
    (single-declaration failure never aborts the whole file, C5.4)."""
    try:
        if head["kw"] not in ("theorem", "lemma"):
            return {"status": "UNPARSED", "head": head, "S1_vars": [],
                    "S2_assumps": [], "S2_instances": [], "S3_conclusion": ""}
        span = decl_span(raw_lines, code_lines, decls, head["line0"])
        joined = lean_strip_comments("\n".join(span))
        binder_region, conclusion = split_signature(joined, head["name"])
        sig_binders = parse_binders(binder_region)
        for b in sig_binders:
            b.setdefault("line0", head["line0"])
        scope = (collect_variable_commands(code_lines)
                 if scope_binders is None else scope_binders)
        scope = relevant_scope_binders(scope, binder_region, conclusion,
                                       head["line0"])
        binders = sorted(scope + sig_binders, key=lambda b: b.get("line0", 0))
        S1_vars, S2_assumps, S2_instances = sort_binders_into_segments(binders)
        return {"status": "OK", "head": head, "S1_vars": S1_vars,
                "S2_assumps": S2_assumps, "S2_instances": S2_instances,
                "S3_conclusion": conclusion}
    except ParseError:
        return {"status": "UNPARSED", "head": head, "S1_vars": [],
                "S2_assumps": [], "S2_instances": [], "S3_conclusion": ""}


# ---- envelope (G1 fix; spec section 2.2; hand-cast precedent trial item1:65) ----

def star_to_universe0(t):
    """`Type*` -> `Type` (universe-0 honest registration); star forms are
    stripped per word so arrow chains (`iota -> Type*`) convert too."""
    t = t.strip()
    t = re.sub(r"\b(Type|Sort)\*", r"\1", t)
    return t


def envelope_statement(stmt):
    """v2 replacement for vacgen.py:563-573.  Existentialize S1 vars AND
    instance binders; hypotheses become conjuncts AFTER the prefix.
    2.1.0 double-layer assembly: the conjunction chain draws from the
    explicit-assumption segment ONLY (S2_assumps; empty conjunction renders
    the truth identity `True`, which the W6 battery measures as degeneracy
    data), and instance binders render their clean type so a named instance
    binder `[inst : Foo A]` never leaks its name into the type position."""
    conj = " \u2227 ".join(a["type"] for a in stmt["S2_assumps"]) or "True"
    prefix = ["(%s : %s)" % (v["name"], star_to_universe0(v["type"])) for v in stmt["S1_vars"]]
    prefix += ["(_ : %s)" % (i.get("cleanType") or i["type"])
               for i in stmt["S2_instances"]]
    body = conj
    for p in reversed(prefix):
        body = "\u2203 %s, %s" % (p, body)
    return body


def envelope_prefix_segments(stmt):
    segs = ["\u2203 (%s : %s)" % (v["name"], star_to_universe0(v["type"]))
            for v in stmt["S1_vars"]]
    segs += ["\u2203 (_ : %s)" % (i.get("cleanType") or i["type"])
             for i in stmt["S2_instances"]]
    return segs


def envelope_free_var_hits(stmt, env_text):
    """Check envelope_free_vars ⊆ bound_prefix_names (section 2.2): a
    statement binder name referenced anywhere in the envelope must be bound
    by its existential prefix segment (segment present in the text).  v1's
    G1 cast (A / I referenced with no prefix at all) is flagged here; legal
    residue references to prefix-bound names (quantifier scope) are not."""
    var_names = set(v["name"] for v in stmt["S1_vars"] if v["name"] != "_")
    bound = set()
    for v in stmt["S1_vars"]:
        if v["name"] != "_":
            seg = "∃ (%s : %s)" % (v["name"], star_to_universe0(v["type"]))
            if seg in env_text:
                bound.add(v["name"])
    hits = set()
    for tok in IDENT_TOK.findall(env_text):
        for frag in tok.split("."):
            if frag in var_names and frag not in bound:
                hits.add(frag)
    return sorted(hits)


# ---- W5 cast-time envelope front gate (criterion self-built; this revision
# ---- is the first envelope test face in the repo - the refinery suite's
# ---- vacgen segment builds its vectors on this word-face family) ----

BARE_TYPE_LIMB_MARKER = "bare-type-conjunct-limb"
# canonical literal face of the family: a type expression sitting in a
# Prop position after a conjunction operator (`Set (...)` applied forms)
BARE_TYPE_LIMB_CANONICAL = "∧ Set ("


def is_bare_type_limb(limb):
    """Word-face test: can this conjunction limb be a bare TYPE expression?
    Conservative (fail-safe) side: any limb carrying a proposition marker,
    a bare equality, a dependent-binder colon inside its paren group, or a
    multi-token application face reads as a proposition and never flags.
    Only pure type-expression faces (looks_like_type_v2 family) and pure
    type-application faces (`Set (...)`: one identifier head onto one
    parenthesized argument group holding no top-level colon) flag.  `True`
    (the empty-conjunction identity) is W6's degeneracy datum, never a W5
    hit."""
    t = limb.strip()
    if not t or t == "True":
        return False
    if PROP_MARK.search(t) or BARE_EQ.search(t):
        return False
    if looks_like_type_v2(t):
        return True
    m = re.match(r"^[^\W\d][\w'.!]*\s*\(", t)
    if m:
        opener = t.find("(")
        try:
            _end, inner = scan_balanced(t, opener)
        except ParseError:
            return False
        tail = t[opener + 1 + len(inner) + 1:].strip()
        if tail:
            return False  # structure after the group: not the bare family
        if find_top_colon(inner) >= 0:
            return False  # dependent-binder face: proposition
        return True
    return False


def envelope_bare_type_limb_hits(stmt, env_text=None):
    """W5 cast-time self-check: bare-type conjunct limbs in the witness
    envelope.  Two prongs over one word-face family: the canonical literal
    face `∧ Set (` found in the assembled envelope text, and the per-limb
    family over the statement's explicit-assumption segment (the only
    segment feeding the conjunction chain - a bare type in a conjunct limb
    position cannot elaborate as a Prop, so the deformed cast must die at
    cast time, before the compile leg ever runs).  Returns the sorted
    unique hit list; empty = clean."""
    if env_text is None:
        env_text = envelope_statement(stmt)
    hits = []
    if BARE_TYPE_LIMB_CANONICAL in env_text:
        hits.append(BARE_TYPE_LIMB_CANONICAL)
    for a in stmt["S2_assumps"]:
        t = a["type"].strip()
        if is_bare_type_limb(t):
            hits.append(t)
    return sorted(set(hits))


# ---------------------------------------------------------------- L2 taxonomy
# taxonomy-as-data (C3.1): the engine contains zero premise-family knowledge.
# Rows live in taxonomy.json; the builtin row below is only the fail-safe
# chain end (C6.2) - the verbatim data transcription of v1 PREMISE_INEQ_RE.

BUILTIN_STARTER_REGEX = (r"^\s*(?:(\(\s*\d+\s*/\s*\d+\s*:\s*ℝ\s*\))|(\d+\s*/\s*\d+)"
                         r"|(\(\s*\d+\s*:\s*ℝ\s*\)))\s*<\s*[A-Za-z_\u0100-\uffff][\w'.!]*\s*\.\s*re\s*$")

BUILTIN_STARTER_ROW = {
    "schemaVersion": 2,
    "familyId": "ineq.real.const-lt-field-re",
    "cluster": "annum",
    "match": {"target": "assumption.type", "regex": BUILTIN_STARTER_REGEX, "flags": ""},
    "priority": 50,
    "confidence": "HIGH",
    "witnessStrategy": ("probe-point real-part bite + envelope existentialization "
                        "(v1 native face); numeric-constant boundary block only when "
                        "this row is matched"),
    "witnessTemplate": {
        "bites": ["theorem {p}_point_re : (⟨{P}, 0⟩ : ℂ).re = {P} := rfl"],
        "boundary": {"kind": "numeric-constant", "template": "{num} / {den}"},
    },
    "requireVarBinding": True,
    "mathlibAnchors": [{"symbol": "differentiableOn_riemannZeta",
                        "relPath": "Mathlib/NumberTheory/LSeries/RiemannZeta.lean",
                        "line": 141}],
    "refutationForms": ["full", "point", "tactics", "noclassic", "band"],
    "boundaryApplicability": "numeric-constant",
    "gapKeywords": ["zeta", "critical strip", "LSeries"],
    "sourceLane": "v1-transcription",
    "sourceRowId": "v1-PREMISE_INEQ_RE",
    "notes": ("builtin fail-safe starter row: verbatim data transcription of v1 "
              "PREMISE_INEQ_RE + CONST_ALT (vacgen.py:227-233)"),
}

MATCH_TARGETS = ("assumption.type", "assumption.name", "instance.type",
                 "conclusion", "file.text")
REQUIRED_ROW_FIELDS = ("schemaVersion", "familyId", "cluster", "match", "priority",
                       "confidence", "witnessStrategy", "mathlibAnchors",
                       "refutationForms", "boundaryApplicability", "gapKeywords")


def validate_row(row):
    """Row admission validation (C3.4): required fields + target enum + regex
    compiles.  Unknown fields ignored; missing required field = row invalid."""
    errs = []
    if not isinstance(row, dict):
        return ["row is not an object"]
    for f in REQUIRED_ROW_FIELDS:
        if f not in row:
            errs.append("missing required field %s" % f)
    if errs:
        return errs
    m = row["match"]
    if not isinstance(m, dict) or m.get("target") not in MATCH_TARGETS:
        errs.append("match.target must be one of %s" % ", ".join(MATCH_TARGETS))
    rx = m.get("regex") if isinstance(m, dict) else None
    if not isinstance(rx, str) or not rx.strip():
        errs.append("match.regex missing")
    else:
        try:
            flags = m.get("flags", "")
            if not isinstance(flags, str) or flags.strip() not in ROW_FLAG_MAP:
                errs.append("match.flags unsupported (use '', I/M/S or long names)")
            else:
                re.compile(rx, ROW_FLAG_MAP[flags.strip()])
        except re.error as exc:
            errs.append("match.regex compile failed: %s" % exc)
    if not isinstance(row["priority"], int):
        errs.append("priority must be an integer")
    if row["confidence"] not in ("HIGH", "MID"):
        errs.append("confidence must be HIGH or MID")
    anc = row["mathlibAnchors"]
    if not isinstance(anc, list) or len(anc) < 1:
        errs.append("mathlibAnchors must be a non-empty list (C3.2)")
    return errs


ROW_FLAG_MAP = {"": 0, "I": re.IGNORECASE, "IGNORECASE": re.IGNORECASE,
                "M": re.MULTILINE, "MULTILINE": re.MULTILINE,
                "S": re.DOTALL, "DOTALL": re.DOTALL}


def flags_int(flags):
    """Data-driven row match.flags -> re flag int (engine infrastructure,
    not family knowledge; unknown values fail loud at admission)."""
    if isinstance(flags, int):
        return flags
    f = (flags or "").strip()
    if f not in ROW_FLAG_MAP:
        raise TaxonomyError("unsupported match.flags value: %r" % flags)
    return ROW_FLAG_MAP[f]


def load_table(rows):
    """Deterministic route order: priority desc, pattern length desc
    (specificity), familyId asc.  The engine never branches on familyId."""
    out = []
    for row in rows:
        flags = flags_int(row["match"].get("flags", ""))
        out.append({"row": row, "rx": re.compile(row["match"]["regex"], flags)})
    return sorted(out, key=lambda e: (-e["row"]["priority"],
                                      -len(e["row"]["match"]["regex"]),
                                      e["row"]["familyId"]))


def resolve_taxonomy_path(explicit):
    """C6.2 location chain: --taxonomy flag > VACGEN_TAXONOMY env >
    tool-adjacent taxonomy.json > builtin starter row (fail-safe end)."""
    if explicit:
        return explicit, "--taxonomy flag"
    env = os.environ.get("VACGEN_TAXONOMY")
    if env:
        return env, "VACGEN_TAXONOMY env"
    same_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taxonomy.json")
    if os.path.isfile(same_dir):
        return same_dir, "tool-adjacent taxonomy.json"
    return None, "builtin starter row (fail-safe chain end)"


def load_taxonomy(explicit):
    """Load + admit the taxonomy table.  Returns (entries, info).
    info: source/path/rowsLoaded/rowsVoided/builtin/invalid details.
    A file whose row admission fails entirely = fail-loud (rc=1, section 6.2)."""
    path, source = resolve_taxonomy_path(explicit)
    info = {"source": source, "path": path, "rowsLoaded": 0, "rowsVoided": 0,
            "builtin": False, "invalid": [], "anchorVerifiedAt": None}
    if path is None:
        entries = load_table([BUILTIN_STARTER_ROW])
        info["rowsLoaded"], info["builtin"] = 1, True
        info["anchorVerifiedAt"] = BUILTIN_STARTER_ROW["mathlibAnchors"][0].get("line") and "builtin"
        return entries, info
    if not os.path.isfile(path):
        raise TaxonomyError("taxonomy file not found: %s" % path)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc.get("rows") if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        raise TaxonomyError("taxonomy file must carry a rows list: %s" % path)
    valid, invalid = [], []
    for row in rows:
        errs = validate_row(row)
        if errs:
            invalid.append({"familyId": row.get("familyId", "?") if isinstance(row, dict) else "?",
                            "errors": errs})
        else:
            valid.append(row)
    info["rowsLoaded"] = len(valid)
    info["rowsVoided"] = len(invalid)
    info["invalid"] = invalid
    info["anchorVerifiedAt"] = doc.get("anchorVerifiedAt") if isinstance(doc, dict) else None
    if valid:
        return load_table(valid), info
    if invalid:
        raise TaxonomyError(
            "taxonomy row admission failed entirely (%d invalid row(s); first: %s)"
            % (len(invalid), json.dumps(invalid[0], ensure_ascii=False)[:200]))
    # empty table -> builtin fallback, declared loudly (C6.2 chain end)
    entries = load_table([BUILTIN_STARTER_ROW])
    info["rowsLoaded"], info["builtin"] = 1, True
    return entries, info


class TaxonomyError(Exception):
    pass


def face_text(rec, target, ctx):
    """Lookup face per row target (section 4.1).  Faces unavailable on a
    record kind return None (row cannot match that record)."""
    if target == "assumption.type":
        return rec["type"] if rec["kind"] == "assumption" else None
    if target == "assumption.name":
        return (rec.get("name") or "") if rec["kind"] == "assumption" else None
    if target == "instance.type":
        return rec["type"] if rec["kind"] == "instance" else None
    if target == "conclusion":
        return ctx.get("conclusion") or None
    if target == "file.text":
        return ctx.get("file_text")
    return None


HOLE_RE = re.compile(r"(?<![\w'.!])_(?![\w'.!])")


def classify_record(rec, table, ctx, ft_cache, s1_names):
    """First match wins under the deterministic table order (section 4.1).
    Miss = TODO-SEAT.  Degraded faces (bare `_` hole) are intercepted before
    classification and forced to todo_seat (C4.2 negative-sample contract:
    no third path to `recognized`)."""
    if rec["kind"] in ("assumption", "instance") and HOLE_RE.search(rec["type"]):
        return {"status": "todo_seat", "familyId": None, "confidence": None,
                "degraded": "hole"}
    for idx, entry in enumerate(table):
        m = entry["row"]["match"]
        target = m["target"]
        if target == "file.text":
            hit = ft_cache[idx]
        else:
            text = face_text(rec, target, ctx)
            if text is None:
                continue
            try:
                hit = entry["rx"].search(text) is not None
            except re.error:
                hit = False
        if not hit:
            continue
        if entry["row"].get("requireVarBinding"):
            # generic data-flagged parity check (v1: matched var must be a
            # statement variable, vacgen.py:343); applies to assumption records
            if rec["kind"] != "assumption":
                continue
            comps = set()
            for tok in IDENT_TOK.findall(rec["type"]):
                comps.update(tok.split("."))
            if not (comps & set(s1_names)):
                continue
        return {"status": "recognized", "familyId": entry["row"]["familyId"],
                "confidence": entry["row"]["confidence"], "degraded": None,
                "matchedTarget": target}
    return {"status": "todo_seat", "familyId": None, "confidence": None,
            "degraded": None}


def build_ft_cache(table, file_text):
    """Whole-text row results computed once per file (identical for every
    record of that file; deterministic, purely an evaluation cache)."""
    cache = []
    for entry in table:
        if entry["row"]["match"]["target"] == "file.text":
            cache.append(entry["rx"].search(file_text) is not None)
        else:
            cache.append(False)
    return cache


# ---------------------------------------------------------------- L3 scoring

def tier_of(coverage_pct, total, unparsed):
    """Tier thresholds are `>=` monotone (C4.4).  D = degraded face."""
    if unparsed or total == 0:
        return "D"
    if coverage_pct >= 80:
        return "A"
    if coverage_pct >= 50:
        return "B"
    return "C"


SEAT_MINUTES = 15
BAND_FACTOR = {"S": 0, "M": 30, "L": 60}
BAND_S_LIMIT = 26 * 1024      # 26,624 B (S = bytes < this)
BAND_M_LIMIT = 200 * 1024     # 204,800 B (M = bytes < this; L = bytes >= this)
CALIBRATION = ("uncalibrated extrapolation: seatMinutes=%d, bandFactor={S:%d,M:%d,L:%d}, "
               "tier thresholds 80/50" % (SEAT_MINUTES, BAND_FACTOR["S"],
                                          BAND_FACTOR["M"], BAND_FACTOR["L"]))


def band_of(bytes_):
    if bytes_ < BAND_S_LIMIT:
        return "S"
    if bytes_ < BAND_M_LIMIT:
        return "M"
    return "L"


def budget_minutes(todo_seats, band):
    return todo_seats * SEAT_MINUTES + BAND_FACTOR[band]


def negative_finding_block(scanned_what):
    """C4.5 four elements accompany every coverage claim (negative-finding
    boundary law: a negative finding of the scan face, not an absolute claim)."""
    return {
        "scannedWhat": scanned_what,
        "notScanned": ("elaboration-time semantics (synthetic holes, instance "
                       "resolution, universe constraints); aliased premise "
                       "spellings outside the loaded taxonomy rows"),
        "nonAbsoluteClaim": True,
        "aliasesNotExhausted": True,
        "rescanCondition": ("taxonomy row generation (new lanes/rows), mathlib "
                            "re-pull into the pinned worktree, or census window "
                            "change (new censusId) - earliest triggers re-scan"),
    }


# ---------------------------------------------------------------- W6 strength
# Two-dimensional verdict (satisfiable x strength): after a GREEN cast the
# degenerate battery word-face scans the witness envelope for `trivial-element`
# witness faces.  Degeneracy is DATA (the exit-code semantics never change);
# battery counters are closed-window snapshots and every invariant over them
# is a monotone bound (artifact-verifier design law: no exact-equality
# checks on live counters).

DEGENERATE_BATTERY = (
    # (class, word faces) - word-face level, lower-bound semantics: a hit
    # names a `trivial-element` witness FACE; elaboration-time witness
    # degeneracy stays invisible (declared honest boundary).
    ("emptyset", ("\u2205", r"Set\.empty\b", r"=\s*\{\s*\}")),
    ("single-point", (r"\{\s*[^\s{}|]+\s*\}",)),
    ("zero-element", (r"=\s*\(?\s*0\b", r"\bZero\.zero\b")),
    ("top-type", (r"\bTrue\b", "\u22a4", r"\bP?Unit\b")),
    ("always-true", (r"\b(\w[\w'.!]*)\s*=\s*\1\b",)),
)
# registered judgment table (word-face level): a battery hit class lowers the
# witness strength grade to the mapped refutation form.  The grade vocabulary
# is the refutationForms five-word face; the strength order
# band < noclassic < tactics < point < full is the registered scale and the
# grade is its minimum over hit classes (monotone: a dirtier battery can only
# grade lower).  A clean battery grades "full".
STRENGTH_CLASS_TO_FORM = {
    "always-true": "band",
    "top-type": "band",
    "emptyset": "noclassic",
    "single-point": "tactics",
    "zero-element": "point",
}
STRENGTH_ORDER = ("full", "point", "tactics", "noclassic", "band")
FORM_RANK = {"full": 4, "point": 3, "tactics": 2, "noclassic": 1, "band": 0}


def degenerate_battery_hits(env_text):
    """W6 degenerate battery: word-face scan of the witness envelope text.
    Returns the sorted unique hit list [(class, matched face)]; empty list =
    clean.  A hit is a `trivial-element` witness FACE on this closed scan
    window, never a semantic judgment."""
    hits = []
    for cls, faces in DEGENERATE_BATTERY:
        for rx in faces:
            for m in re.finditer(rx, env_text):
                hits.append((cls, m.group(0)))
    return sorted(set(hits))


def strength_face(env_text, satisfiable, ts_utc):
    """Build the report verdict.strength face (2.1.0 additive schema): the
    two-dimensional verdict (satisfiable x strength).  Degeneracy is data,
    not error: this face never feeds the exit code, and the battery runs
    after a GREEN verdict only (on a RED cast the face records that no
    strength reading exists)."""
    if not satisfiable:
        return {
            "satisfiable": False,
            "battery": [],
            "degenerate": None,
            "grade": None,
            "order": list(STRENGTH_ORDER),
            "scannedFace": None,
            "note": ("battery runs after GREEN only; satisfiable=false - no "
                     "strength reading on a RED cast"),
        }
    hits = degenerate_battery_hits(env_text)
    classes = sorted(set(cls for cls, _f in hits))
    if classes:
        grade = min((STRENGTH_CLASS_TO_FORM[c] for c in classes),
                    key=lambda f: FORM_RANK[f])
    else:
        grade = "full"
    by_class = []
    for c in classes:
        faces = sorted(f for cls, f in hits if cls == c)
        by_class.append({"class": c, "faces": faces, "count": len(faces)})
    return {
        "satisfiable": True,
        "battery": by_class,
        "degenerate": bool(classes),
        "grade": grade,
        "order": list(STRENGTH_ORDER),
        "scannedFace": ("witness envelope statement, word-face degenerate "
                        "battery, closed window %s" % ts_utc),
        "note": ("degeneracy is data, not error: exit-code semantics "
                 "unchanged; counters carry monotone bounds only - "
                 "exact-equality invariants on live counters are forbidden"),
    }


# ---------------------------------------------------------------- cast (L4)
# ---- verbatim inheritance from v1 emitters (vacgen.py:448-1048) ----

def sanitize_ident(stem):
    s = re.sub(r"[^A-Za-z0-9_]+", "_", stem).lower()
    s = re.sub(r"_+", "_", s).strip("_")
    if not s or s[0].isdigit():
        s = "a" + s
    return s


def census_candidates(head_name, namespace):
    """Mechanical candidates for the vacancy census chain (camel/snake/qualified
    families).  Derived by token surgery only; the audit agent must review the
    anchors before firing any census shot."""
    first_tok = head_name.split("_")[0]
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", first_tok).lower()
    parts = [w for w in snake.split("_") if w]
    camel = "".join(w[:1].upper() + w[1:] for w in parts)
    qualified = ("%s.%sCompleted" % (namespace, first_tok)) if namespace else "<Namespace>.<Head>Completed"
    return {
        "stem": first_tok,
        "v1": ["completed" + camel, camel + "Completed"],
        "v2": ["completed_" + snake, snake + "_completed"],
        "v3": [qualified, camel + ".completed"],
    }


def build_command_line(cfg, target_path):
    return ('powershell -NoProfile -ExecutionPolicy Bypass -File %s '
            '-TempLimit 98 -CoreN %d -AllowG3 -GearForce 0 -Command '
            '"cd /d %s && %s env lean %s"'
            % (cfg["guard"], cfg["core"], cfg["worktree"], cfg["lake"], target_path))


def resolve_numeric_boundary(stmt, classified, table_by_family):
    """Generic numeric-constant boundary resolution (row-data gated, C4.6):
    when the matched row declares witnessTemplate.boundary.kind =
    numeric-constant, parse the constant with the generic fraction parser and
    require the bound variable to be a statement variable (v1 parity,
    vacgen.py:338-369).  No family knowledge: the trigger is row data."""
    for rec, verdict in zip([r for r in _iter_records(stmt)], classified):
        if rec["kind"] != "assumption" or verdict["status"] != "recognized":
            continue
        row = table_by_family.get(verdict["familyId"])
        if not row:
            continue
        wt = row.get("witnessTemplate") or {}
        if (wt.get("boundary") or {}).get("kind") != "numeric-constant":
            continue
        typ = rec["type"]
        lt = _top_level_char(typ, "<")
        if lt < 0:
            continue
        const_text = typ[:lt].strip()
        right = typ[lt + 1:].strip()
        mvar = re.match(r"\s*([A-Za-z_\u0100-\uffff][\w'.!]*)\s*\.\s*re\s*$", right)
        if not mvar or mvar.group(1) not in set(v["name"] for v in stmt["S1_vars"]):
            continue
        frac = parse_const_fraction(const_text)
        if not frac:
            continue
        num, den, bare = frac
        var = mvar.group(1)
        var_type = next((v["type"] for v in stmt["S1_vars"] if v["name"] == var), "ℂ")
        b = Fraction(num, den)
        probe = 2 if b < 2 else (b.numerator // b.denominator + 1)
        return {"const_text": const_text, "bare_text": bare, "num": num, "den": den,
                "var": var, "var_type": var_type, "hyp_name": rec.get("name") or ""}, \
            {"num": num, "den": den, "text": bare}, probe
    return None, None, 2


def _iter_records(stmt):
    for a in stmt["S2_assumps"]:
        yield {"kind": "assumption", "name": a.get("name", ""), "type": a["type"],
               "source": a.get("source", "signature")}
    for i in stmt["S2_instances"]:
        yield {"kind": "instance", "name": "", "type": i["type"],
               "source": i.get("source", "signature")}


def _top_level_char(s, ch):
    """Index of the first top-level occurrence of ch (bracket-depth aware)."""
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in OPENER_TO_CLOSER:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ch:
            return i
        i += 1
    return -1


class Cast(object):
    def __init__(self, args, artifact, sha, ts_utc):
        self.args = args
        self.artifact = artifact
        self.sha = sha
        self.ts_utc = ts_utc
        stem = os.path.splitext(os.path.basename(args.in_path))[0]
        self.stem = stem
        self.name = args.name or sanitize_ident(stem)
        self.audit_id = args.audit_id or ("vacgen-" + self.name)
        self.p = "vacgen_" + self.name
        self.cfg = {
            "guard": args.guard, "lake": args.lake,
            "worktree": args.worktree, "core": args.core,
        }
        self.probe_lit = "\u27e8%d, 0\u27e9" % artifact["probe"]  # ⟨P, 0⟩
        self.out_dir = args.out_dir or os.path.join("vacgen_out", self.name)

    def header(self, target_name, title_line, semantics_lines, expected_lines, extra_lines):
        target_path = self.out_dir.replace("\\", "/") + "/" + target_name
        L = []
        L.append("/- " + title_line)
        L.append("   cast by vacgen v%s (vacuity probe skeleton generator with shape"
                 % TOOL_VERSION)
        L.append("   recognition; zero network, zero compile, pure stdlib, python -I;")
        L.append("   casts skeletons only, never assertions - every artifact-facing")
        L.append("   proof obligation is a declared TODO-SEAT seat).")
        L.append("")
        L.append("   Audit ID: %s" % self.audit_id)
        L.append("   Statement face (verbatim transcription of the audited artifact's")
        L.append("     statement face; artifact sha256 %s; the artifact file" % self.sha)
        L.append("     itself is never imported - only its import face is re-emitted and")
        L.append("     its statement face transcribed):")
        for ln in self.artifact["head_raw_lines"]:
            L.append(("     | " + ln) if ln.strip() else "     |")
        L.append("   Verdict semantics:")
        for ln in semantics_lines:
            L.append("     " + ln)
        L.append("   Build (cpu_guard v3 thermal wrapper mandatory; never run lake bare):")
        L.append("     %s" % build_command_line(self.cfg, target_path))
        L.append("   Expected-fail semantics:")
        for ln in expected_lines:
            L.append("     " + ln)
        L.append("   Toolchain pin: %s | mathlib snapshot window: %s" % (self.args.toolchain, self.args.snapshot))
        L.append("   Cast time (UTC): %s | seat: casting seat, vacgen v2 job 20261113" % self.ts_utc)
        for ln in extra_lines:
            L.append("   " + ln)
        L.append(" -/")
        return "\n".join(L)

    def import_face(self):
        L = []
        for ln in self.artifact["module_lines"]:
            L.append(ln)
        if self.artifact["imports"]:
            L.extend(self.artifact["imports"])
        else:
            L.append("-- TODO-SEAT I-0: the artifact declared no import face; add the")
            L.append("-- imports its statement face needs (for example: import Mathlib).")
        return "\n".join(L)

    def point_re(self):
        P = self.artifact["probe"]
        return ("theorem %s_point_re : (%s : \u2102).re = %d := rfl"
                % (self.p, self.probe_lit, P))

    def point_ne_one(self):
        P = self.artifact["probe"]
        return ("theorem %s_point_ne_one : (%s : \u2102) \u2260 1 := by\n"
                "  intro h\n"
                "  have h2 : (%s : \u2102).re = (1 : \u2102).re := by rw [h]\n"
                "  rw [Complex.one_re] at h2\n"
                "  exact absurd (show (%d : \u211d) = 1 from h2) (by norm_num)"
                % (self.p, self.probe_lit, self.probe_lit, P))

    def bite(self, face):
        pi = self.artifact["premise_ineq"]
        if not pi:
            return None
        return ("theorem %s_bite_%s : %s < (%s : %s).re := by\n"
                "  rw [%s_point_re]\n"
                "  norm_num"
                % (self.p, face, pi["const_text"], self.probe_lit,
                   pi["var_type"], self.p))

    def falsify_binders(self):
        parts = []
        for b in self.artifact["instance_binders"]:
            parts.append("[%s]" % b["type"])
        for v in self.artifact["variables"]:
            parts.append("(%s : %s)" % (v["name"], v["type"]))
        for h in self.artifact["hypotheses"]:
            if h["kind"] == "raw":
                parts.append(h["type"])
            else:
                parts.append("(%s : %s)" % (h["name"], h["type"]))
        return (" " + " ".join(parts)) if parts else ""

    def transcript_summary(self):
        cov = self.artifact["coverage"]
        pi = self.artifact["premise_ineq"]
        b = ("boundary %s (numeric-constant face), probe point %d"
             % (pi["bare_text"], self.artifact["probe"])) if pi else \
            "shape-registration face (no numeric-constant row matched); TODO-SEAT seats counted"
        return ("premise faces: %d total / %d recognized / %d TODO-SEAT (top family: %s) | %s"
                % (cov["total"], cov["recognized"], cov["todoSeats"],
                   cov.get("topFamily") or "none", b))

    # v1-alias faces kept for the eight-file product contract (C6.1)
    @property
    def variables(self):
        return self.artifact["variables"]

    @property
    def hypotheses(self):
        return self.artifact["hypotheses"]

    @property
    def instance_binders(self):
        return self.artifact["instance_binders"]

    def envelope_statement(self):
        return envelope_statement(self.artifact["stmt"])


def emit_witness(cast):
    p = cast.p
    seat_fill = ("\u27e8%s, by rw [%s_point_re]; norm_num\u27e9"
                 % (cast.probe_lit, p))
    semantics = [
        "PREMISE-NONEMPTY ENVELOPE (expected-green face).  The filled envelope",
        "theorem witnesses the satisfiability of the artifact's premise",
        "conjunction (statement variables AND instance binders existentially",
        "quantified, hypotheses as conjuncts after the prefix).  Compile-ok of",
        "the FILLED file (rc = 0, #print axioms within [%s]," % AXIOM_PROFILE,
        "zero sorryAx) is the constructive nonempty evidence.  Compile failure",
        "of the filled file is fail-loud: report the raw compiler output",
        "verbatim; never repair the file into green by weakening the statement",
        "face.",
    ]
    expected = [
        "EXPECTED-GREEN-AFTER-FILL.  As-cast skeleton state: the declared sorry",
        "placeholder(s) below, each annotated TODO-SEAT and counted here; the",
        "as-cast #print axioms listing shows sorryAx by design until the seats",
        "are filled - that listing is the declared skeleton state, not an audit",
        "verdict.  In the FILLED artifact any sorryAx hit is RED.  New axiom",
        "declarations: 0.  native_decide: forbidden (absent).",
    ]
    extra = [
        "Declared seats: 1 sorry placeholder (seat W-1).",
        "Cast notes: %s" % cast.transcript_summary(),
    ]
    header = cast.header(
        "witness.lean",
        "witness.lean - premise-nonempty envelope skeleton, account 1 of the",
        semantics, expected, extra)

    L = [header, "", cast.import_face(), "",
         "/- Machine bites.  The probe point and the interface vocabulary",
         "   instantiate cleanly against the transcribed premise face.  These",
         "   compile green on purpose (artifact-independent facts transcribed",
         "   verbatim from the session shape masters). -/", "",
         cast.point_re(), "", cast.point_ne_one(), "",
         "/-- Premise-nonempty envelope seat (TODO-SEAT W-1): fill a concrete",
         "witness term for the artifact's premise conjunction.  Expected fill",
         "shape for this cast: `%s`, after which the" % seat_fill,
         "file must reach zero sorry and PA within the three-standard profile. -/",
         "theorem %s_premises_witness : %s := by" % (p, cast.envelope_statement()),
         "  -- TODO-SEAT W-1 (of 1): EXPECTED-GREEN-AFTER-FILL seat - replace this",
         "  -- declared sorry placeholder with the witness term.  The generator",
         "  -- casts no assertions; the fill is the audit seat's proof obligation.",
         "  sorry", "",
         "#print axioms %s_point_re" % p,
         "#print axioms %s_point_ne_one" % p,
         "#print axioms %s_premises_witness" % p, ""]
    return "\n".join(L)


REFUTATION_FORM_TEXT = {
    "full": (
        "full-face refutation - the complete transcribed premise interface of",
        "the artifact's head statement (statement variables lifted to explicit",
        "binders), conjunction implies False.",
    ),
    "point": (
        "probe-point refutation - the premise shape instantiated at the probe",
        "point (a true, jointly consistent fact set), plus the attempt to derive",
        "False from the instantiated facts alone.",
    ),
    "tactics": (
        "tactic-battery refutation - the transcribed interface handed to one",
        "automation battery (simp / ring / omega / linarith / decide / trivial,",
        "one shot each, try-guarded); the residual goal after the battery is the",
        "verdict locus.",
    ),
    "noclassic": (
        "Classical-free refutation - the same transcribed interface attacked",
        "under a constructive discipline: the probe's own proof body uses only",
        "intro/have/rw/exact/absurd and decidable arithmetic closers; no choice-",
        "dependent tactic anywhere (token-scanned at cast time, count 0).",
    ),
    "band": (
        "boundary-band refutation - the trivial-zero band face against the",
        "claimed region: the band lies strictly below the region boundary and",
        "the probe point lies inside the region; the attempt to derive False",
        "from the band facts and the instantiated premise shape.",
    ),
}


def emit_refutation(cast, face):
    p = cast.p
    art = cast.artifact
    pi = art["premise_ineq"]
    face_title = face.upper()
    if face == "tactics":
        locus = "the residual False goal after the battery (expected verdict: unsolved goals)"
    else:
        locus = "the written-form closing readout (omega line)"
    semantics = [
        "COMPILE-MUST-FAIL PROBE, form %s: %s" % (face_title, REFUTATION_FORM_TEXT[face][0]),
    ]
    semantics += ["  " + ln for ln in REFUTATION_FORM_TEXT[face][1:]]
    semantics += [
        "The refutation theorem attempts to derive False from the transcribed",
        "premise interface at this probe strength.",
    ]
    expected = [
        "EXPECTED-FAIL (probe must fail).  rc = 0 (green) would mean the",
        "transcribed premise interface is jointly unsatisfiable at this probe",
        "strength = vacuity alert (immediate escalation, ok = false).  rc = 1",
        "(red) = nonempty evidence: the interface resisted this refutation form.",
        "Expected verdict locus: %s." % locus,
        "Declared seats: 0 sorry placeholders - the probe body must stay",
        "sorry-free (a compiling refutation probe IS the vacuity alert; the",
        "attack seat below is filled with sorry-free steps only).  New axiom",
        "declarations: 0.  native_decide: forbidden (absent).",
    ]
    extra = [
        "Cast notes: %s" % cast.transcript_summary(),
    ]
    header = cast.header(
        "falsify_%s.lean" % face,
        "falsify_%s.lean - refutation probe skeleton (face %s), account 2," % (face, face),
        semantics, expected, extra)

    seat_tag = {"full": "F", "point": "P", "tactics": "T", "noclassic": "N", "band": "B"}[face]
    seat_no = {"full": "F-1", "point": "P-1", "tactics": "T-1", "noclassic": "N-1", "band": "B-1"}[face]

    L = [header, "", cast.import_face(), "",
         "/- Machine bites.  The probe point and the interface vocabulary",
         "   instantiate cleanly against the transcribed premise face.  These",
         "   compile green on purpose (artifact-independent facts transcribed",
         "   verbatim from the session shape masters), so any red this file",
         "   produces is the expected-fail verdict and not a skeleton defect. -/",
         "", cast.point_re(), "", cast.point_ne_one(), ""]
    bite = cast.bite(face)
    if bite:
        L.append(bite)
        L.append("")
        L.append("#print axioms %s_point_re" % p)
        L.append("#print axioms %s_point_ne_one" % p)
        L.append("#print axioms %s_bite_%s" % (p, face))
    else:
        L.append("-- TODO-SEAT M-%s: premise-shape bite omitted - no matched taxonomy" % seat_no)
        L.append("-- row declares a numeric-constant bite template for this premise face;")
        L.append("-- transcribe a premise instantiation bite here from the statement")
        L.append("-- face before firing this probe (stay sorry-free).")
        L.append("")
        L.append("#print axioms %s_point_re" % p)
        L.append("#print axioms %s_point_ne_one" % p)
    L.append("")

    binders = cast.falsify_binders()
    if face == "point":
        L.append("/- Refutation, face point.  The premise shape instantiated at the probe")
        L.append("   point (machine bite, compiled green above), and the attempt to derive")
        L.append("   False from the instantiated facts alone.  The verdict lands on the")
        L.append("   written-form closing readout. -/")
        L.append("")
        L.append("theorem %s_falsify_point : False := by" % p)
        if pi:
            L.append("  have hb : %s < (%s : %s).re := by"
                     % (pi["const_text"], cast.probe_lit, pi["var_type"]))
            L.append("    rw [%s_point_re]" % p)
            L.append("    norm_num")
        else:
            L.append("  -- premise shape not machine-recognised: transcribe the premise")
            L.append("  -- instantiation at the probe point here (stay sorry-free).")
    elif face == "band":
        L.append("/- Refutation, face band.  Band facts (trivial-zero band strictly below")
        L.append("   the claimed region boundary; probe point inside the claimed region)")
        L.append("   and the attempt to derive False along the band.  The verdict lands")
        L.append("   on the written-form closing readout. -/")
        L.append("")
        L.append("theorem %s_falsify_band : False := by" % p)
        if pi:
            L.append("  have hband : (-2 : \u211d) < %s := by" % pi["bare_text"])
            L.append("    norm_num")
            L.append("  have hedge : %s < (%s : %s).re := by"
                     % (pi["const_text"], cast.probe_lit, pi["var_type"]))
            L.append("    rw [%s_point_re]" % p)
            L.append("    norm_num")
        else:
            L.append("  -- boundary constant not machine-recognised: transcribe the band")
            L.append("  -- facts (band strictly below the claimed-region boundary; probe")
            L.append("  -- point inside the region) here (stay sorry-free).")
    else:
        L.append("/- Refutation, face %s.  %s" % (face, REFUTATION_FORM_TEXT[face][0]))
        for ln in REFUTATION_FORM_TEXT[face][1:]:
            L.append("   %s" % ln)
        L.append("   The verdict lands on the written-form closing readout. -/")
        L.append("")
        L.append("theorem %s_falsify_%s%s : False := by" % (p, face, binders))

    if face == "tactics":
        L.append("  -- TODO-SEAT %s (of 1): optional premise-clause attack seat - insert" % seat_no)
        L.append("  -- sorry-free have-steps here to strengthen the battery's context; the")
        L.append("  -- battery below is the default probe strength.")
        L.append("  -- Battery, one shot each; every shot is expected to fail here when")
        L.append("  -- the instantiated clauses are jointly consistent.")
        L.append("  try simp")
        L.append("  try ring")
        L.append("  try omega")
        L.append("  try linarith")
        L.append("  try decide")
        L.append("  try trivial")
        L.append("  -- Battery exhausted; the residual False goal is the verdict locus")
        L.append("  -- (expected compiler verdict: unsolved goals).")
    else:
        L.append("  -- TODO-SEAT %s (of 1): attack-continuation seat - insert premise-clause" % seat_no)
        L.append("  -- attack steps here (probe-point instantiations, value/zero-free")
        L.append("  -- clause combination).  Inserted steps must stay sorry-free: a compiling")
        L.append("  -- refutation probe is the vacuity alert.")
        L.append("  -- Written-form closing readout: the compiler verdict is expected to")
        L.append("  -- land here.")
        L.append("  omega")
    L.append("")
    return "\n".join(L)


BOUNDARY_SEATS = [
    {
        "tag": "C-1", "stem": "trivial_zero_point_re", "needs_const": False,
        "desc": [
            "Real-part face of the trivial-zero band point: for every n : N the",
            "point -(2 * (n+1)) embedded in C has real part exactly the same",
            "integer embedded in R (closed cast chain N -> Z -> R vs N -> Z -> C).",
        ],
        "fill": "Expected fill (shape-master level): simp.",
        "tmpl": "theorem %s_trivial_zero_point_re (n : \u2115) :\n"
                "    (-(2 * ((n : \u2124) + 1)) : \u2102).re = (-(2 * ((n : \u2124) + 1)) : \u211d) := by",
    },
    {
        "tag": "C-2", "stem": "trivial_zero_band_le_minus_two", "needs_const": False,
        "desc": [
            "Band face: the trivial-zero point lies at or left of -2 on the real",
            "line (for every n : N, since n >= 0).",
        ],
        "fill": "Expected fill (shape-master level): Nat.cast_nonneg, push_cast, linarith.",
        "tmpl": "theorem %s_trivial_zero_band_le_minus_two (n : \u2115) :\n"
                "    (-(2 * ((n : \u2124) + 1)) : \u211d) \u2264 (-2 : \u211d) := by",
    },
    {
        "tag": "C-3", "stem": "minus_two_lt_boundary_const", "needs_const": True,
        "desc": [
            "Constant face: -2 is strictly below the artifact's claimed-region",
            "boundary constant (transcribed from the statement face).",
        ],
        "fill": "Expected fill (shape-master level): norm_num.",
        "tmpl": "theorem %s_minus_two_lt_boundary_const : (-2 : \u211d) < %s := by",
    },
    {
        "tag": "C-4", "stem": "boundary_band_disjoint", "needs_const": True,
        "desc": [
            "Packaging face: for every n : N the band point has real part equal",
            "to the same integer embedded in R, lies at or left of -2, and -2 is",
            "strictly below the claimed-region boundary constant.",
        ],
        "fill": "Expected fill (shape-master level): exact packaging of seats C-1/C-2/C-3.",
        "tmpl": "theorem %s_boundary_band_disjoint (n : \u2115) :\n"
                "    (-(2 * ((n : \u2124) + 1)) : \u2102).re = (-(2 * ((n : \u2124) + 1)) : \u211d)\n"
                "      \u2227 (-(2 * ((n : \u2124) + 1)) : \u211d) \u2264 (-2 : \u211d)\n"
                "      \u2227 (-2 : \u211d) < %s := by",
    },
    {
        "tag": "C-5", "stem": "trivial_zero_outside_claimed_region", "needs_const": True,
        "desc": [
            "Disjointness corollary in the artifact's claimed-region shape: for",
            "no n : N does the trivial-zero point lie in the claimed region (the",
            "boundary-constant comparison is the region's defining clause).",
        ],
        "fill": "Expected fill (shape-master level): obtain packaging, rw real-part face, push_cast, linarith.",
        "tmpl": "theorem %s_trivial_zero_outside_claimed_region (n : \u2115) :\n"
                "    \u00ac (%s < (-(2 * ((n : \u2124) + 1)) : \u2102).re) := by",
    },
    {
        "tag": "C-6", "stem": "trivial_zero_point_minus_two", "needs_const": False,
        "desc": [
            "Closed-value instantiation anchor: at n = 0 the band point is",
            "exactly -2 on the real axis.",
        ],
        "fill": "Expected fill (shape-master level): simp.",
        "tmpl": "theorem %s_trivial_zero_point_minus_two :\n"
                "    (-(2 * (((0 : \u2115) : \u2124) + 1)) : \u2102).re = (-2 : \u211d) := by",
    },
]


def emit_boundary_numeric(cast):
    """v1 numeric boundary block, emitted only when a matched row declares the
    numeric-constant boundary kind (C4.6: zeta-band seats fire only on the
    starter row face).  Verbatim v1 emit_boundary (vacgen.py:858-951)."""
    p = cast.p
    pi = cast.artifact["premise_ineq"]
    bare = pi["bare_text"] if pi else None

    seats = []
    for seat in BOUNDARY_SEATS:
        if seat["needs_const"] and bare is None:
            seats.append({"tag": seat["tag"], "stem": seat["stem"], "body": None})
        else:
            tmpl = seat["tmpl"]
            body = tmpl % ((p, bare) if tmpl.count("%s") == 2 else (p,))
            seats.append({"tag": seat["tag"], "stem": seat["stem"], "body": body})

    n_seats = len(seats)
    n_sorry = sum(1 for s in seats if s["body"] is not None)
    n_comment = n_seats - n_sorry

    semantics = [
        "SEPARATION MACHINE CHECK (norm_num level), expected-green face.  The",
        "filled boundary theorems machine-check, as closed computations over the",
        "linear order on R, that the trivial-zero band of the relevant zeta",
        "function (real points -(2*(n+1)) for all n : N, real parts <= -2) is",
        "disjoint from the artifact's claimed region (the boundary constant is",
        "transcribed from the statement face).  Compile-ok of the FILLED file is",
        "the standing positive machine evidence; it is a face check only - it",
        "does not judge the audited statement true, does not decide vacuity, and",
        "does not prove zero-freeness anywhere.",
    ]
    expected = [
        "EXPECTED-GREEN-AFTER-FILL.  As-cast skeleton state: %d declared sorry"
        % n_sorry,
        "placeholder(s) below (each annotated TODO-SEAT and counted here) plus"
        if n_comment else "placeholder(s) below, each annotated TODO-SEAT and counted here; the",
    ]
    if n_comment:
        expected += [
            " %d comment-only seat(s) (boundary constant not machine-parsed)." % n_comment,
            "the as-cast #print axioms listing shows sorryAx by design until the",
        ]
    else:
        expected += [
            "the as-cast #print axioms listing shows sorryAx by design until the",
        ]
    expected += [
        "seats are filled - that listing is the declared skeleton state, not an",
        "audit verdict.  In the FILLED artifact any sorryAx hit is RED.  New",
        "axiom declarations: 0.  native_decide: forbidden (absent).",
    ]
    extra = [
        "Declared seats: %d sorry placeholders (%s)." % (
            n_sorry, ", ".join(s["tag"] for s in seats if s["body"] is not None) or "none"),
    ]
    if n_comment:
        extra.append("Comment-only seats (transcribe the boundary constant from the")
        extra.append("  statement face by hand): %s."
                     % ", ".join(s["tag"] for s in seats if s["body"] is None))
    else:
        extra.append("Cast note: boundary constant transcribed from the statement face: %s."
                     % bare)
    header = cast.header(
        "boundary.lean",
        "boundary.lean - separation machine-check skeleton (norm_num level), account 3,",
        semantics, expected, extra)

    L = [header, "", cast.import_face(), "",
         "/-! ### Boundary seats (all TODO-SEAT, declared sorry placeholders;",
         "   the filled file must reach zero sorry and PA within the",
         "   three-standard profile) -/", ""]
    for s in seats:
        seat = next(x for x in BOUNDARY_SEATS if x["tag"] == s["tag"])
        doc = ["/-- Seat %s (TODO-SEAT): %s" % (s["tag"], seat["desc"][0])]
        doc.extend(seat["desc"][1:])
        doc.append(seat["fill"])
        doc.append("-/")
        if s["body"] is None:
            L.append("-- TODO-SEAT %s (comment-only seat): the boundary constant was not" % s["tag"])
            L.append("-- machine-parsed; transcribe the constant from the statement face and")
            L.append("-- emit this theorem (shape-master example, seat C-3 shape):")
            L.append("--   theorem %s_minus_two_lt_boundary_const : (-2 : \u211d) < 31 / 32 := by norm_num" % p)
            L.append("")
            continue
        L.append("\n".join(doc))
        L.append(s["body"])
        L.append("  -- TODO-SEAT %s: EXPECTED-GREEN-AFTER-FILL seat - replace this declared" % s["tag"])
        L.append("  -- sorry placeholder with the closed computation; zero sorry in the fill.")
        L.append("  sorry")
        L.append("")
    for s in seats:
        if s["body"] is not None:
            L.append("#print axioms %s_%s" % (p, s["stem"]))
    L.append("")
    return "\n".join(L)


def emit_boundary_shape(cast):
    """Shape-registration boundary (C4.6 G2 fix): no matched row declares a
    numeric-constant boundary, so the boundary account degrades to a shape
    registration plus closed-term machine checks (hand-cast precedent: trial
    item1 hand/boundary.lean).  Zero target-irrelevant zeta-band vocabulary;
    every agent is TODO-SEAT counted (C4.1)."""
    p = cast.p
    stmt = cast.artifact["stmt"]
    n_premises = len(stmt["S2_assumps"])
    n_shape_seats = 1 + n_premises  # registration agent + per-premise seats

    semantics = [
        "SHAPE-REGISTRATION BOUNDARY (expected-green face).  No matched",
        "taxonomy row declares a numeric-constant boundary for this premise",
        "face, so per the G2 fix the boundary account carries: (a) closed-term",
        "machine bites (generic numeric facts, norm_num level, no sorry), and",
        "(b) one TODO-SEAT registration seat per premise face plus one overall",
        "registration seat - each a premise-nonempty instantiation obligation",
        "(exhibit a concrete instance satisfying the face).  The register",
        "records the recognized premise families verbatim; it does not judge",
        "the audited statement true, does not decide vacuity, and proves no",
        "zero-freeness anywhere.",
    ]
    expected = [
        "EXPECTED-GREEN-AFTER-FILL.  As-cast skeleton state: %d declared sorry"
        % n_shape_seats,
        "placeholder(s) below (each annotated TODO-SEAT and counted here); the",
        "as-cast #print axioms listing shows sorryAx by design until the seats",
        "are filled - that listing is the declared skeleton state, not an audit",
        "verdict.  In the FILLED artifact any sorryAx hit is RED.  New axiom",
        "declarations: 0.  native_decide: forbidden (absent).",
    ]
    extra = [
        "Declared seats: %d sorry placeholders (registration + per-premise)." % n_shape_seats,
        "Cast notes: %s" % cast.transcript_summary(),
    ]
    header = cast.header(
        "boundary.lean",
        "boundary.lean - shape-registration skeleton (closed-term machine checks), account 3,",
        semantics, expected, extra)

    L = [header, "", cast.import_face(), "",
         "/-! ### Closed-term machine bites (no sorry; artifact-independent) -/", "",
         "theorem %s_boundary_num_bite : (-2 : \u211d) < 2 \u2227 (\u27e82, 0\u27e9 : \u2102).re = 2 := by"
         % p,
         "  norm_num", "",
         "#print axioms %s_boundary_num_bite" % p, "",
         "/-! ### Boundary seats (all TODO-SEAT, declared sorry placeholders;",
         "   the filled file must reach zero sorry and PA within the",
         "   three-standard profile) -/", ""]

    env = envelope_statement(stmt)
    L.append("/-- Seat B-R (TODO-SEAT): overall premise-face registration - exhibit a")
    L.append("concrete instantiation satisfying the full premise conjunction (the")
    L.append("envelope below; fill = the witness construction, then the file must")
    L.append("reach zero sorry and PA within the three-standard profile). -/")
    L.append("theorem %s_boundary_registration : %s := by" % (p, env))
    L.append("  -- TODO-SEAT B-R (of %d): EXPECTED-GREEN-AFTER-FILL seat - replace this" % n_shape_seats)
    L.append("  -- declared sorry placeholder with the concrete instantiation.")
    L.append("  sorry")
    L.append("")
    for k, a in enumerate(stmt["S2_assumps"], start=1):
        prefix = envelope_statement(dict(stmt, S2_assumps=[a], S2_instances=[]))
        L.append("/-- Seat B-S%d (TODO-SEAT): premise-face registration - exhibit a concrete" % k)
        L.append("instantiation satisfying this single premise face. -/")
        L.append("theorem %s_boundary_seat_s%d : %s := by" % (p, k, prefix))
        L.append("  -- TODO-SEAT B-S%d (of %d): EXPECTED-GREEN-AFTER-FILL seat." % (k, n_shape_seats))
        L.append("  sorry")
        L.append("")
    L.append("#print axioms %s_boundary_registration" % p)
    for k in range(1, n_premises + 1):
        L.append("#print axioms %s_boundary_seat_s%d" % (p, k))
    L.append("")
    return "\n".join(L)


def emit_boundary(cast):
    """C4.6 route: numeric-constant rows drive the v1 zeta-band block; every
    other face degrades to shape registration (all seats TODO-SEAT counted)."""
    if cast.artifact["premise_ineq"] is not None:
        return emit_boundary_numeric(cast)
    return emit_boundary_shape(cast)


def emit_gap_anchors(cast, ledger):
    p = cast.p
    art = cast.artifact
    head_name = art["head"]["name"]
    ns = art["namespace"] or "<Namespace>"
    cand = census_candidates(head_name, ns)
    L = []
    L.append("# gap_anchors.txt - vacuity gap-anchor census chain + negative-finding")
    L.append("#   four-element template + dated cast ledger (account 4 of the vacgen")
    L.append("#   four-account skeleton directory)")
    L.append("#")
    L.append("# cast by vacgen v%s at %s UTC | audit id: %s" % (TOOL_VERSION, cast.ts_utc, cast.audit_id))
    L.append("# input artifact: %s" % os.path.abspath(cast.args.in_path).replace("\\", "/"))
    L.append("# input sha256: %s (snapshot registration, dated)" % cast.sha)
    L.append("# toolchain pin: %s | mathlib snapshot window: %s" % (cast.args.toolchain, cast.args.snapshot))
    L.append("# head statement: %s%s | artifact sorry tokens (snapshot): %d"
             % ((ns + ".") if art["namespace"] else "", head_name, art["sorry_count"]))
    L.append("#")
    L.append("# This file is cast by the generator; the census shots are fired by the")
    L.append("# audit seat (the generator itself is zero-network zero-execution).")
    L.append("")
    L.append("## A. grep census chain - three variants (vacancy census)")
    L.append("#")
    L.append("# Conjunctive verdict rule: ALL THREE variants zero = ABSENT verdict on THIS")
    L.append("# scan face only (a negative finding, never an absolute claim - fill the")
    L.append("# four-element template in section B before reporting).")
    L.append("")
    L.append("# Candidate anchors below are derived mechanically from the head-statement")
    L.append("# tokens; the audit seat must review them against the statement face before")
    L.append("# firing (TODO-SEAT A-0).")
    L.append("")
    L.append("### Variant V1 (CamelCase completion family)")
    L.append("grep -rn --include='*.lean' -E \"%s\" <MATHLIB-ROOT>"
             % "|".join(cand["v1"]))
    L.append("# TODO-SEAT A-1: replace <MATHLIB-ROOT>; review candidate anchors: %s"
             % ", ".join(cand["v1"]))
    L.append("")
    L.append("### Variant V2 (snake_case completion family)")
    L.append("grep -rn --include='*.lean' -E \"%s\" <MATHLIB-ROOT>"
             % "|".join(cand["v2"]))
    L.append("# TODO-SEAT A-2: replace <MATHLIB-ROOT>; review candidate anchors: %s"
             % ", ".join(cand["v2"]))
    L.append("")
    L.append("### Variant V3 (namespace-qualified completion family)")
    L.append("grep -rn --include='*.lean' -E \"%s\" <MATHLIB-ROOT>"
             % "|".join(cand["v3"]))
    L.append("# TODO-SEAT A-3: replace <MATHLIB-ROOT>; review candidate anchors: %s"
             % ", ".join(cand["v3"]))
    L.append("")
    L.append("### Head-statement name census (interface-vocabulary presence)")
    L.append("grep -rn --include='*.lean' -F \"%s\" <MATHLIB-ROOT>" % head_name)
    L.append("")
    L.append("### Measured-template line (fill after firing; snapshot with date)")
    L.append("# measured <UTC ts> on <snapshot window>: V1=<n> V2=<n> V3=<n> -> verdict")
    L.append("")
    L.append("## B. Negative-finding four-element template (self-drawn evidence boundary)")
    L.append("#")
    L.append("# Every 'not found / zero hit / absent on this face' report MUST carry all")
    L.append("# four elements; the negative finding's force extends exactly to the faces")
    L.append("# actually scanned, no further.")
    L.append("")
    L.append("1. What was scanned (per item: surfaces, method, timestamp UTC):")
    L.append("   <which repos / trees, which search form, file-level or name-level, when>")
    L.append("")
    L.append("2. What was NOT scanned (explicit non-coverage statement):")
    L.append("   <e.g. searched by name rather than read file-by-file; process-level and")
    L.append("    aliased-directory reconnaissance not performed>")
    L.append("")
    L.append("3. Non-absolute claim wording:")
    L.append("   EN: \"<X> was not found on this scan face - a negative finding of that")
    L.append("        scan, not an absolute claim.\"")
    L.append("   CN: \u300c\u672c\u9762\u672a\u68c0\u51fa X\uff1a\u7cfb\u672c\u6b21\u626b\u63cf\u9762\u7684\u8d1f\u53d1\u73b0\uff0c\u975e\u7edd\u5bf9\u4e3b\u5f20\u3002\u300d")
    L.append("")
    L.append("4. Aliased equivalents not exhaustively ruled out:")
    L.append("   EN: \"aliased equivalents elsewhere were not exhaustively ruled out; <Y>")
    L.append("        was searched by name rather than read file-by-file.\"")
    L.append("   CN: \u300c\u4ed6\u5904\u522b\u540d\u7b49\u4ef7\u7269\u672a\u7a77\u5c3d\u6392\u9664\uff0c\u4e14 Y \u76ee\u5f55\u6309\u540d\u68c0\u7d22\u800c\u975e\u9010\u4ef6\u901a\u8bfb\u3002\u300d")
    L.append("")
    L.append("Rescan condition (companion to the boundary law: when to re-scan):")
    L.append("   <upstream mathlib push window / next audit round / named date>")
    L.append("")
    L.append("## C. Cast ledger (dated snapshot registration - not a live invariant)")
    L.append("#")
    L.append("# Fill-round discipline: the TODO-SEAT count is monotone non-increasing")
    L.append("# across filling rounds; EXPECTED-FAIL faces must never turn green (a")
    L.append("# compiling refutation probe = vacuity alert); exact-equality invariants on")
    L.append("# these counters are forbidden - snapshots are registered with dates.")
    L.append("")
    L.append("cast at %s UTC:" % cast.ts_utc)
    for row in ledger:
        L.append("  %-22s bytes=%-6d lines=%-4d declared_sorry=%d scanned_sorry=%d "
                 "todo_seats=%d print_axioms=%d"
                 % (row["file"], row["bytes"], row["lines"], row["declared_sorry"],
                    row["scanned_sorry"], row["todo_seats"], row["print_axioms"]))
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- checks

def count_todo_seats(text):
    return text.count("TODO-SEAT")


def run_checks(cast, ledger, files_text):
    """v1 eleven bound-form checks, verbatim contract (vacgen.py:1057-1117)."""
    checks = []
    blockers = []

    def add(name, ok, detail):
        checks.append((name, ok, detail))
        if not ok:
            blockers.append("%s: %s" % (name, detail))

    ref_rows = [r for r in ledger if r["file"].startswith("falsify_")]
    green_rows = [r for r in ledger
                  if r["file"] in ("witness.lean", "boundary.lean")]
    skel_rows = ref_rows + green_rows

    bad = [r["file"] for r in ref_rows if r["scanned_sorry"] > 0]
    add("refutation_faces_sorry_upper_bound", not bad,
        "scanned sorry tokens must be <= 0 per refutation face; offenders: %s" % (bad or "none"))

    low = [r["file"] for r in green_rows if r["declared_sorry"] < 1]
    add("expected_green_faces_seat_lower_bound", not low,
        "witness/boundary skeletons must carry >= 1 declared seat; offenders: %s" % (low or "none"))

    bad = [r["file"] for r in ledger if r["scanned_sorry"] > r["declared_sorry"]]
    add("scanned_vs_declared_upper_bound", not bad,
        "scanned sorry tokens exceed the declared count; offenders: %s" % (bad or "none"))

    nd = [(r["file"], r["native_decide"]) for r in ledger if r["native_decide"] > 0]
    add("native_decide_forbidden", not nd,
        "native_decide tokens found; offenders: %s" % (nd or "none"))

    ax = [(r["file"], r["axiom_decls"]) for r in ledger if r["axiom_decls"] > 0]
    add("new_axiom_declarations_zero", not ax,
        "new axiom declarations found; offenders: %s" % (ax or "none"))

    bad = [r["file"] for r in ref_rows if r["expected_fail_marker"] < 1]
    add("expected_fail_marker_present_per_refutation", not bad,
        "refutation faces must carry >= 1 EXPECTED-FAIL marker; offenders: %s" % (bad or "none"))

    bad = [r["file"] for r in green_rows if r["expected_fail_marker"] != 0]
    add("expected_fail_marker_absent_per_green", not bad,
        "expected-green faces must carry 0 EXPECTED-FAIL markers; offenders: %s" % (bad or "none"))

    bad = [r["file"] for r in skel_rows
           if any(f not in files_text[r["file"]] for f in HEADER_FIELDS)]
    add("five_header_fields_present", not bad,
        "header five fields missing; offenders: %s" % (bad or "none"))

    bad = [r["file"] for r in skel_rows if r["print_axioms"] < 1]
    add("print_axioms_present", not bad,
        "skeletons must carry >= 1 #print axioms line; offenders: %s" % (bad or "none"))

    bad = [r["file"] for r in ref_rows
           if ("theorem %s_falsify_%s" % (cast.p, r["face"])) not in files_text[r["file"]]]
    add("falsify_theorem_present", not bad,
        "refutation theorem missing; offenders: %s" % (bad or "none"))

    bad = [r["file"] for r in green_rows if r["todo_seats"] < 1]
    add("todo_seats_present_per_green", not bad,
        "expected-green skeletons must carry >= 1 TODO-SEAT annotation; offenders: %s" % (bad or "none"))

    return checks, blockers


def run_checks_v2(cast, ledger, files_text, report, taxonomy_info):
    """v2 additive bound-form checks (section 6.4), appended after the v1
    eleven; all bound-form, all closed-window."""
    checks = []
    blockers = []

    def add(name, ok, detail):
        checks.append((name, ok, detail))
        if not ok:
            blockers.append("%s: %s" % (name, detail))

    # 1. envelope_free_vars_zero: G1 recurrence detector (section 2.2)
    stmt = cast.artifact["stmt"]
    env = envelope_statement(stmt)
    hits = envelope_free_var_hits(stmt, env)
    add("envelope_free_vars_zero", not hits,
        "envelope references outside the existential prefix: %s" % (hits or "none"))

    # 2. assumptions_fully_accounted: closed-window structural identity (C4.3)
    cov = report["coverage"]
    add("assumptions_fully_accounted",
        cov["recognized"] + cov["todoSeats"] == cov["total"],
        "recognized %d + todoSeats %d == total %d" % (cov["recognized"], cov["todoSeats"], cov["total"]))

    # 3. no_silent_degradation: degraded faces must be counted (C4.1)
    deg = sum(1 for a in report["assumptions"] if a.get("degraded"))
    add("no_silent_degradation", cov["todoSeats"] >= deg,
        "degraded faces %d counted within todoSeats %d" % (deg, cov["todoSeats"]))

    # 4. negative_four_elements_present (C4.5)
    nf = report["negativeFinding"]
    ok4 = all(nf.get(k) for k in ("scannedWhat", "notScanned", "rescanCondition")) \
        and nf.get("nonAbsoluteClaim") is True and nf.get("aliasesNotExhausted") is True
    add("negative_four_elements_present", ok4,
        "four-element block present with nonAbsoluteClaim/aliasesNotExhausted true")

    # 5. taxonomy_rows_loaded_positive_or_builtin (C6.2 chain end declared)
    ok5 = taxonomy_info["rowsLoaded"] > 0 or taxonomy_info["builtin"]
    add("taxonomy_rows_loaded_positive_or_builtin", ok5,
        "rowsLoaded=%d builtin=%s source=%s" % (taxonomy_info["rowsLoaded"],
                                                taxonomy_info["builtin"], taxonomy_info["source"]))

    # 6. envelope_bare_type_limbs_zero: W5 internalized self-check (2.1.0).
    # Closed-window bound-form invariant on THIS cast's assembled envelope
    # (same family as check 1); the cast-time front gate already rejects
    # before emission, so a RED here would mean the gate was bypassed.
    limb_hits = envelope_bare_type_limb_hits(stmt, env)
    add("envelope_bare_type_limbs_zero", not limb_hits,
        "bare-type conjunct limbs in the envelope: %s" % (limb_hits or "none"))

    return checks, blockers


# ---------------------------------------------------------------- cast main

def do_cast(args, ts_utc):
    print("== %s v%s cast report ==" % (TOOL_NAME, TOOL_VERSION))
    print("[INPUT]")
    if not os.path.isfile(args.in_path):
        print("  FAIL-LOUD: --in file not found: %s" % args.in_path)
        return 1
    with open(args.in_path, "rb") as fh:
        raw = fh.read()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        src = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print("  FAIL-LOUD: --in file is not valid UTF-8: %s" % exc)
        return 1
    print("  file: %s" % os.path.abspath(args.in_path).replace("\\", "/"))
    print("  sha256: %s (snapshot registration, dated %s)" % (sha, ts_utc))
    print("  bytes: %d | lines: %d" % (len(raw), src.count("\n") + (0 if src.endswith("\n") or not src else 1)))

    # L2 taxonomy load (C6.2 chain; row admission fail-loud inside)
    try:
        table, tax_info = load_taxonomy(args.taxonomy)
    except TaxonomyError as exc:
        print("  FAIL-LOUD: taxonomy: %s" % exc)
        return 1
    print("[TAXONOMY]")
    print("  source: %s" % tax_info["source"])
    if tax_info["path"]:
        print("  path: %s" % os.path.abspath(tax_info["path"]).replace("\\", "/"))
    print("  rowsLoaded: %d | rowsVoided (admission): %d | builtin fallback: %s"
          % (tax_info["rowsLoaded"], tax_info["rowsVoided"], tax_info["builtin"]))
    if tax_info["builtin"]:
        print("  note: builtin starter row in force (fail-safe chain end; v1 native "
              "recognition face only - see taxonomy.json for the merged table)")
    for inv in tax_info["invalid"][:5]:
        print("  voided row %s: %s" % (inv["familyId"], "; ".join(inv["errors"])[:120]))
    table_by_family = {e["row"]["familyId"]: e["row"] for e in table}

    # L1 decompose (fail-loud preserved, C2.4 / vacgen.py:1174-1179 behavior)
    try:
        stmt = decompose_head(src)
    except ParseError as exc:
        print("  FAIL-LOUD: statement-face parse failed: %s" % exc)
        print("  no skeleton cast (the audit seat must transcribe the statement face by hand).")
        return 1

    # W5 cast-time envelope front gate (2.1.0): a bare-type conjunct limb in
    # the witness envelope cannot elaborate as a Prop, so the deformed cast
    # dies here with rc=1, before any skeleton text is emitted (fail-loud;
    # the statement face must be re-shaped or transcribed by hand before a
    # cast can run).  Existing output directories are never touched here.
    env_text = envelope_statement(stmt)
    limb_hits = envelope_bare_type_limb_hits(stmt, env_text)
    if limb_hits:
        print("  FAIL-LOUD: %s in the witness envelope (cast-time self-check): %s"
              % (BARE_TYPE_LIMB_MARKER, "; ".join(limb_hits)))
        print("  no skeleton cast (the premise conjunction cannot elaborate as"
              " a Prop; canonical family face: %s)" % BARE_TYPE_LIMB_CANONICAL)
        return 1

    stripped_all = lean_strip_comments(src)
    sorry_count = len(re.findall(r"\bsorry\b", stripped_all))
    axiom_decls = [d for d in stmt["decls"] if d["kw"] == "axiom"]
    sorry_ax_hits = len(re.findall(r"\bsorryAx\b", stripped_all))

    ns = stmt["namespace"]
    imports = stmt["imports"]
    module_lines = stmt["module_lines"]

    # L1 records -> L2 classify (itemized, C2.2/C4.1)
    records = list(_iter_records(stmt))
    records.append({"kind": "conclusion", "name": "", "type": stmt["S3_conclusion"],
                    "source": "signature"})
    s1_names = [v["name"] for v in stmt["S1_vars"]]
    ctx = {"conclusion": stmt["S3_conclusion"], "file_text": stripped_all}
    ft_cache = build_ft_cache(table, stripped_all)
    classified = [classify_record(r, table, ctx, ft_cache, s1_names) for r in records]
    concl_verdict = classified[-1]
    body_verdicts = classified[:-1]

    # numeric boundary resolution (row-data gated, C4.6)
    premise_ineq, boundary, probe = resolve_numeric_boundary(stmt, body_verdicts, table_by_family)
    if boundary is None:
        m = re.search(r"(?<![\w.])(\d+)\s*/\s*(\d+)(?![\w.])", " ".join(stmt["S3_conclusion"].split()))
        if m:
            boundary = {"num": int(m.group(1)), "den": int(m.group(2)),
                        "text": "%s / %s" % (m.group(1), m.group(2))}
            probe = 2 if Fraction(boundary["num"], boundary["den"]) < 2 else \
                (boundary["num"] // boundary["den"] + 1)

    # L3 coverage accounting (C4.1-C4.3)
    recognized = sum(1 for v in body_verdicts if v["status"] == "recognized")
    rec_concl = 1 if concl_verdict["status"] == "recognized" else 0
    todo_misses = sum(1 for v in body_verdicts if v["status"] == "todo_seat")
    todo_concl = 0 if concl_verdict["status"] == "recognized" else 1
    deg_holes = sum(1 for v in body_verdicts if v.get("degraded") == "hole")
    todo_degraded = deg_holes + (1 if axiom_decls else 0) + (1 if sorry_ax_hits else 0)
    todo_seats = todo_misses + todo_concl + todo_degraded
    total = len(body_verdicts) + 1 + todo_degraded
    coverage_pct = (recognized + rec_concl) * 100 // total if total else 0
    fam_counts = {}
    for v in body_verdicts:
        if v["status"] == "recognized":
            fam_counts[v["familyId"]] = fam_counts.get(v["familyId"], 0) + 1
    top_family = sorted(fam_counts.items(), key=lambda t: (-t[1], t[0]))[0][0] if fam_counts else None

    cov = {"recognized": recognized + rec_concl, "todoSeats": todo_seats,
           "total": total, "coverageLowerPct": coverage_pct,
           "registeredAt": ts_utc, "topFamily": top_family}

    ns_prefix = (ns + ".") if ns else ""
    print("[INPUT: SHAPE]")
    print("  declarations: %d | head: %s%s (%s @ line %d)"
          % (len(stmt["decls"]), ns_prefix, stmt["head"]["name"],
             stmt["head"]["kw"], stmt["head"]["line0"] + 1))
    print("  L1 split: S1 vars %d | S2 assumptions %d | S2 instance binders %d | status %s"
          % (len(stmt["S1_vars"]), len(stmt["S2_assumps"]), len(stmt["S2_instances"]),
             stmt["status"]))
    print("  L1 vars: %s" % (", ".join("%s : %s" % (v["name"], v["type"]) for v in stmt["S1_vars"]) or "-"))
    print("  L1 instances: %s" % ("; ".join(i["type"] for i in stmt["S2_instances"]) or "-"))
    print("  L1 assumptions: %s" % ("; ".join("%s : %s" % (a["name"], a["type"]) for a in stmt["S2_assumps"]) or "-"))
    print("  L3 coverage (lower bound, dated %s): %d/%d = %d%% | top family: %s"
          % (ts_utc, cov["recognized"], cov["total"], coverage_pct, top_family or "-"))
    print("  boundary: %s | probe point: %d"
          % (boundary["text"] if boundary else "shape-registration (no numeric row matched)", probe))
    print("  artifact sorry tokens (snapshot, dated %s): %d | axiom decls: %d | sorryAx: %d"
          % (ts_utc, sorry_count, len(axiom_decls), sorry_ax_hits))

    # v1-compatible artifact face (C6.1: eight-file products preserved)
    artifact = {
        "imports": imports,
        "module_lines": module_lines,
        "namespace": ns,
        "decls": stmt["decls"],
        "head": stmt["head"],
        "head_raw_lines": stmt["head_raw_lines"],
        "conclusion": stmt["S3_conclusion"],
        "proof_marker": "",
        # v1-style segments (falsify binders keep the v1 face, C6.1)
        "variables": [{"name": v["name"], "type": v["type"], "kind": "explicit"}
                      for v in stmt["S1_vars"]],
        "hypotheses": [{"name": a["name"], "type": a["type"], "kind": a.get("kind", "explicit")}
                       for a in stmt["S2_assumps"]],
        "instance_binders": [{"type": i["type"]} for i in stmt["S2_instances"]],
        "premise_ineq": premise_ineq,
        "boundary": boundary,
        "probe": probe,
        "sorry_count": sorry_count,
        "decl_count": len(stmt["decls"]),
        "status": "OK",
        "stmt": stmt,
        "coverage": cov,
    }

    cast = Cast(args, artifact, sha, ts_utc)
    print("[OUTPUT ROOT]")
    print("  %s  (four accounts, 8 files)" % os.path.abspath(cast.out_dir).replace("\\", "/"))

    targets = ["witness.lean", "falsify_full.lean", "falsify_point.lean",
               "falsify_tactics.lean", "falsify_noclassic.lean", "falsify_band.lean",
               "boundary.lean", "gap_anchors.txt"]

    texts = {}
    texts["witness.lean"] = emit_witness(cast)
    for face in REFUTATION_FACES:
        texts["falsify_%s.lean" % face] = emit_refutation(cast, face)
    texts["boundary.lean"] = emit_boundary(cast)

    os.makedirs(cast.out_dir, exist_ok=True)

    existing = {}
    for t in targets:
        tp = os.path.join(cast.out_dir, t)
        if os.path.isfile(tp):
            with open(tp, "rb") as fh:
                existing[t] = fh.read()

    def fill_ledger():
        rows = []
        for fname, text in texts.items():
            stripped = lean_strip_comments(text)
            row = {
                "file": fname,
                "face": (fname[len("falsify_"):-len(".lean")] if fname.startswith("falsify_") else None),
                "bytes": len(text.encode("utf-8")),
                "lines": text.count("\n") + 1,
                "declared_sorry": len(re.findall(r"\bsorry\b", stripped)),
                "scanned_sorry": len(re.findall(r"\bsorry\b", stripped)),
                "todo_seats": count_todo_seats(text),
                "print_axioms": len(re.findall(r"(?m)^#print axioms", text)),
                "native_decide": len(re.findall(r"\bnative_decide\b", stripped)),
                "axiom_decls": len(re.findall(r"(?m)^\s*axiom\b", stripped)),
                "expected_fail_marker": text.count("EXPECTED-FAIL"),
            }
            rows.append(row)
        return rows

    ledger = fill_ledger()
    texts["gap_anchors.txt"] = emit_gap_anchors(cast, ledger)
    ledger = fill_ledger()

    # idempotence check with cast-epoch masking (verbatim v1 :1245-1272 contract)
    foreign = [t for t in os.listdir(cast.out_dir) if t not in targets]
    iso_ts_re = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

    def masked_disk(t):
        return iso_ts_re.sub("@CAST-TIME@", existing[t].decode("utf-8", errors="replace"))

    def masked_cast(t):
        return iso_ts_re.sub("@CAST-TIME@", texts[t])

    all_present = len(existing) == len(targets)
    identical = all_present and all(masked_disk(t) == masked_cast(t) for t in targets)
    if identical and not args.force:
        print("  re-cast detected: all 8 generator targets identical under cast-epoch"
              " masking -> no-op (zero rewrite; disk keeps the original cast timestamps)")
        print("  disk verification: 8/8 targets match the cast text under cast-epoch masking")
    else:
        differing = [t for t in targets
                     if t in existing and masked_disk(t) != masked_cast(t)]
        if differing and not args.force:
            print("  FAIL-LOUD: existing target files differ from this cast beyond the"
                  " cast epoch: %s" % ", ".join(differing))
            print("  (re-run with --force to overwrite the eight generator-owned targets;")
            print("   foreign files in the output directory are never touched: %s)"
                  % (", ".join(foreign) or "none"))
            return 1
        for t in targets:
            with open(os.path.join(cast.out_dir, t), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(texts[t])
        print("  cast complete: %d file(s) written" % len(targets))
        for t in targets:
            tp = os.path.join(cast.out_dir, t)
            with open(tp, "rb") as fh:
                disk = fh.read()
            if disk != texts[t].encode("utf-8"):
                print("  FAIL-LOUD: disk write verification failed for %s (bytes differ)" % t)
                return 1
        print("  disk verification: 8/8 target files byte-identical to the cast text")
    if foreign:
        print("  foreign files present (untouched): %s" % ", ".join(sorted(foreign)))

    # ---- checks (v1 eleven + v2 five, all bound-form) ----
    files_text = texts
    checks, blockers = run_checks(cast, ledger, files_text)

    # v2 report face (section 6.4)
    assumptions_report = []
    for rec, v in zip(records, classified):
        assumptions_report.append({
            "kind": rec["kind"],
            "name": rec.get("name", ""),
            "typeHead": rec["type"][:80],
            "status": v["status"],
            "familyId": v["familyId"],
            "confidence": v["confidence"],
            "matchedTarget": v.get("matchedTarget"),
            "degraded": v.get("degraded"),
        })
    todo_by_file = {r["file"]: r["todo_seats"] for r in ledger if r["file"] != "gap_anchors.txt"}
    report = {
        "reportId": "vacgenv2-%s-%s" % (cast.name, ts_utc[:10]),
        "tool": {"name": "vacgen2", "version": TOOL_VERSION,
                 "schemaNote": ("2.1.0 additive: verdict.strength face (W6 "
                                "two-dimensional verdict), W5 cast-time "
                                "bare-type-conjunct-limb front gate, named "
                                "instance binder clean-type prefix rendering; "
                                "consumers ignore unknown fields")},
        "in": {"path": os.path.abspath(args.in_path).replace("\\", "/"), "sha256": sha},
        "taxonomy": {"path": os.path.abspath(tax_info["path"]).replace("\\", "/") if tax_info["path"] else None,
                     "source": tax_info["source"], "rowsLoaded": tax_info["rowsLoaded"],
                     "rowsVoided": tax_info["rowsVoided"], "builtin": tax_info["builtin"]},
        "l1": {"s1Vars": len(stmt["S1_vars"]), "s2Assumptions": len(stmt["S2_assumps"]),
               "s2Instances": len(stmt["S2_instances"]), "status": stmt["status"]},
        "assumptions": assumptions_report,
        "coverage": {k: cov[k] for k in ("recognized", "todoSeats", "total", "coverageLowerPct", "registeredAt")},
        "cast": {"files": 8, "todoSeatsByFile": todo_by_file},
        "negativeFinding": negative_finding_block(
            "word-face recognition (L1 bracket-balanced split + L2 regex rows in "
            "%s; %d row(s) loaded, %d voided at admission) over the head-statement "
            "premise face of %s @ %s"
            % (tax_info["path"] or "builtin starter row", tax_info["rowsLoaded"],
               tax_info["rowsVoided"], os.path.abspath(args.in_path).replace("\\", "/"), ts_utc)),
        "experience": [],
        "verdict": {"ok": None, "checks": []},
    }

    v2_checks, v2_blockers = run_checks_v2(cast, ledger, files_text, report, tax_info)
    checks = checks + v2_checks
    blockers = blockers + v2_blockers
    report["verdict"]["checks"] = [[n, ok, d] for n, ok, d in checks]
    report["verdict"]["ok"] = not blockers
    # W6 two-dimensional verdict (2.1.0): the degenerate battery runs after a
    # GREEN verdict only; the strength face is additive report data and never
    # feeds the exit code (degeneracy is data, not error).
    report["verdict"]["strength"] = strength_face(env_text, not blockers, ts_utc)

    print("[FOUR-ACCOUNT LEDGER]  (per-file, verbatim counts)")
    green = [r for r in ledger if r["file"] == "witness.lean" or r["file"] == "boundary.lean"]
    ref = [r for r in ledger if r["face"]]
    gap = [r for r in ledger if r["file"] == "gap_anchors.txt"]
    print("  account 1 - witness (premise-nonempty envelope, EXPECTED-GREEN-AFTER-FILL)")
    for r in green:
        if r["file"] == "witness.lean":
            print("    %-22s bytes=%-6d lines=%-4d declared_sorry=%d scanned_sorry=%d todo_seats=%d print_axioms=%d"
                  % (r["file"], r["bytes"], r["lines"], r["declared_sorry"], r["scanned_sorry"], r["todo_seats"], r["print_axioms"]))
    print("  account 2 - refutation five forms (EXPECTED-FAIL, zero-sorry probes)")
    for r in ref:
        print("    %-22s grade=EXPECTED-FAIL bytes=%-6d lines=%-4d declared_sorry=%d scanned_sorry=%d todo_seats=%d print_axioms=%d verdict_locus=%s"
              % (r["file"], r["bytes"], r["lines"], r["declared_sorry"], r["scanned_sorry"], r["todo_seats"], r["print_axioms"],
                 "battery residual goal" if r["face"] == "tactics" else "omega readout"))
    print("  account 3 - boundary (%s, EXPECTED-GREEN-AFTER-FILL)"
          % ("separation machine check" if premise_ineq else "shape registration"))
    for r in green:
        if r["file"] == "boundary.lean":
            print("    %-22s bytes=%-6d lines=%-4d declared_sorry=%d scanned_sorry=%d todo_seats=%d print_axioms=%d"
                  % (r["file"], r["bytes"], r["lines"], r["declared_sorry"], r["scanned_sorry"], r["todo_seats"], r["print_axioms"]))
    print("  account 4 - gap anchors (census chain + four-element template + ledger)")
    for r in gap:
        print("    %-22s bytes=%-6d lines=%-4d todo_seats=%d" % (r["file"], r["bytes"], r["lines"], r["todo_seats"]))

    print("[COVERAGE - L3 lower bound, dated snapshot %s]" % ts_utc)
    print("  recognized=%d todoSeats=%d total=%d coverageLowerPct=%d%% tier=%s topFamily=%s"
          % (cov["recognized"], cov["todoSeats"], cov["total"], coverage_pct,
             tier_of(coverage_pct, total, False), top_family or "-"))
    for rec, v in zip(records, classified):
        print("    %-10s %-12s %-24s -> %s%s%s"
              % (rec["kind"], rec.get("name", "") or "-", (rec["type"][:24] + "...") if len(rec["type"]) > 24 else rec["type"],
                 v["status"], "@" + v["familyId"] if v["familyId"] else "",
                 " [degraded:%s]" % v["degraded"] if v.get("degraded") else ""))

    print("[CHECKS - bound-form invariants on the cast window %s]" % ts_utc)
    for name, ok, detail in checks:
        print("  [%s] %s  (%s)" % ("PASS" if ok else "RED", name, detail))

    str_face = report["verdict"]["strength"]
    print("[STRENGTH]  (satisfiable x strength two-dimensional verdict;"
          " degeneracy is data, exit-code semantics unchanged)")
    if str_face["satisfiable"]:
        print("  grade: %s | degenerate: %s | order: %s"
              % (str_face["grade"], str_face["degenerate"],
                 " < ".join(str_face["order"])))
        for row in str_face["battery"]:
            print("  battery %s: count=%d (monotone bound, no exact-equality"
                  " invariant) faces=%s"
                  % (row["class"], row["count"], ", ".join(row["faces"][:3])))
        if not str_face["battery"]:
            print("  battery: clean (zero trivial-element witness faces on"
                  " this scan window)")
    else:
        print("  battery not run (GREEN-only face; satisfiable=false)")

    # optional outputs
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("[REPORT] %s" % os.path.abspath(args.report).replace("\\", "/"))
    if args.exp_draft:
        draft = build_exp_draft(report, args, ts_utc)
        with open(args.exp_draft, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(draft, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("[EXP-DRAFT] %s (%d entrie(s))" % (os.path.abspath(args.exp_draft).replace("\\", "/"), len(draft["entries"])))

    print("[VERDICT]")
    if blockers:
        print("  ok=false - %d check(s) red: %s" % (len(blockers), "; ".join(blockers)))
        return 1
    print("  ok=true - all bound-form checks green (cast window %s)" % ts_utc)
    return 0


def build_exp_draft(report, args, ts_utc):
    """RQW03 exp_port draft face (C7.2): EXP-schema field mapping, ready for
    exp_port.append machine validation.  Zero network, local file only."""
    entries = []
    seq = 0
    sha8 = report["in"]["sha256"][:8]
    todo_fams = sorted(set(a["familyId"] for a in report["assumptions"]
                           if a["status"] == "todo_seat" and a["familyId"]))
    for fam in todo_fams:
        seq += 1
        entries.append({
            "id": "vacgenv2-%s-%d" % (sha8, seq),
            "date": ts_utc[:10],
            "tool": "vacgen2",
            "category": "坑",
            "points": ("premise face not covered by any taxonomy row (TODO-SEAT "
                       "counted, no silent degradation): %s @ %s"
                       % (fam, report["in"]["path"]))[:200],
            "evidencePointer": "%s (assumptions[] status=todo_seat)" % (args.report or "<report>"),
            "erratumBlock": None,
            "rescanCondition": "taxonomy row generation or mathlib re-pull",
        })
    seq += 1
    entries.append({
        "id": "vacgenv2-%s-%d" % (sha8, seq),
        "date": ts_utc[:10],
        "tool": "vacgen2",
        "category": "正形",
        "points": ("cast ok; coverage lower bound %d%% (%d/%d, dated snapshot); "
                   "four-account skeleton cast at %s"
                   % (report["coverage"]["coverageLowerPct"], report["coverage"]["recognized"],
                      report["coverage"]["total"], report["in"]["path"]))[:200],
        "evidencePointer": "%s (coverage block)" % (args.report or "<report>"),
        "erratumBlock": None,
        "rescanCondition": "taxonomy row generation or mathlib re-pull",
    })
    return {"draftId": report["reportId"], "tool": "vacgen2", "date": ts_utc[:10],
            "entries": entries}


# ---------------------------------------------------------------- preflight

def load_cluster_table(path):
    """--cluster-table JSON (data face, same key surface as stratify.py's
    keyword table): {"clusterOrder": [...], "table": {cluster: [patterns...]}}.
    Absent -> aggregate honestly falls back to overall + bands (no clusters
    invented)."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    order = doc.get("clusterOrder") or list(doc.get("table", {}).keys())
    table = {}
    for c, pats in (doc.get("table") or {}).items():
        table[c] = [(p, re.compile(p)) for p in pats]
    return order, table


def classify_cluster(text, order, table):
    """stratify.py parity: score = distinct patterns hit, argmax with the
    fixed priority order; zero hits -> physics-misc (residual face, by design)."""
    scores = {}
    for c in order:
        n = 0
        for _p, rx in table.get(c, []):
            if rx.search(text):
                n += 1
        scores[c] = n
    scored = [(c, scores[c]) for c in order if scores[c] > 0]
    if not scored:
        return "physics-misc"
    return max(scored, key=lambda t: t[1])[0]


def preflight_all(args, table, tax_info, ts_utc):
    """--preflight-all (C5.3): census-qualified files, zero compile, per-file
    coverage row -> difficulty map.  Per-file failures never abort the run."""
    with open(args.census, encoding="utf-8") as fh:
        census = json.load(fh)
    qf = census.get("qualifiedFiles")
    if not isinstance(qf, list) or not qf:
        print("FAIL-LOUD: census has no qualifiedFiles list: %s" % args.census)
        return 1
    declared = (census.get("summary") or {}).get("qualifiedFiles")
    if declared != len(qf):
        print("FAIL-LOUD: census face mismatch: summary.qualifiedFiles=%r but "
              "qualifiedFiles list length=%d (closed-window identity violated)"
              % (declared, len(qf)))
        return 1

    order, ctable = (None, None)
    if args.cluster_table:
        try:
            order, ctable = load_cluster_table(args.cluster_table)
        except (OSError, ValueError, re.error) as exc:
            print("FAIL-LOUD: cluster table unreadable: %s" % exc)
            return 1

    table_by_family = {e["row"]["familyId"]: e["row"] for e in table}
    files_out = []
    tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    unparsed_count = 0
    by_band = {}
    by_cluster = {}
    tot_rec = tot_all = 0

    for entry in qf:
        rel = entry["path"]
        fbytes = entry.get("bytes", 0)
        band = band_of(fbytes)
        row = {"path": rel, "bytes": fbytes, "band": band,
               "assumptionsTotal": 0, "recognized": 0, "todoSeats": 0,
               "coverageLowerPct": None, "tier": "D",
               "budgetMinutes": budget_minutes(0, band),
               "status": "OK", "topFamilies": [], "unparsed": False}
        src = None
        try:
            with open(os.path.join(args.root, rel.replace("/", os.sep)), "rb") as fh:
                src = fh.read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            row["status"] = "UNPARSED"
            row["unparsed"] = True
            row["todoSeats"] = 1
            row["budgetMinutes"] = budget_minutes(1, band)
        if src is not None:
            stripped = lean_strip_comments(src)
            raw_lines, code_lines, decls = select_theorem_lemma_decls(src)
            ft_cache = build_ft_cache(table, stripped)
            thm = [d for d in decls if d["kw"] in ("theorem", "lemma")]
            if not thm and not decls:
                row["status"] = "UNPARSED"
                row["unparsed"] = True
                row["todoSeats"] = 1
            scope_b, var_deg = collect_variable_commands(code_lines, tolerant=True)
            axiom_faces = sum(1 for d in decls if d["kw"] == "axiom")
            sorry_ax = len(re.findall(r"\bsorryAx\b", stripped))
            file_rec = file_total = 0
            file_todo = axiom_faces + (1 if sorry_ax else 0) + var_deg
            fam_counts = {}
            unparsed_flag = False
            stmts = [decompose_decl(raw_lines, code_lines, decls, d, scope_binders=scope_b)
                     for d in thm]
            s1_names = sorted(set(v["name"] for st in stmts for v in st["S1_vars"]
                                  if v["name"] != "_"))
            for st in stmts:
                if st["status"] != "OK":
                    file_todo += 1
                    unparsed_flag = True
                    continue
                records = list(_iter_records(st))
                records.append({"kind": "conclusion", "name": "",
                                "type": st["S3_conclusion"], "source": "signature"})
                ctx = {"conclusion": st["S3_conclusion"], "file_text": stripped}
                for rec in records:
                    v = classify_record(rec, table, ctx, ft_cache, s1_names)
                    file_total += 1
                    if v["status"] == "recognized":
                        file_rec += 1
                        fam_counts[v["familyId"]] = fam_counts.get(v["familyId"], 0) + 1
                    else:
                        file_todo += 1
            row["assumptionsTotal"] = file_total + file_todo
            row["recognized"] = file_rec
            row["todoSeats"] = file_todo
            total_all = file_total + file_todo
            if row["unparsed"] or total_all == 0:
                row["coverageLowerPct"] = None
                row["tier"] = "D"
            else:
                pct = file_rec * 100 // total_all
                row["coverageLowerPct"] = pct
                row["tier"] = tier_of(pct, total_all, False)
            if not thm:
                row["status"] = "UNPARSED"
            elif unparsed_flag:
                row["unparsed"] = True
                row["status"] = "OK+DECL-UNPARSED"
            row["topFamilies"] = [[f, c] for f, c in
                                  sorted(fam_counts.items(), key=lambda t: (-t[1], t[0]))[:3]]
            tot_rec += file_rec
            tot_all += total_all
        if row["unparsed"]:
            unparsed_count += 1
        tier_counts[row["tier"]] += 1
        bb = by_band.setdefault(row["band"], {"files": 0, "recognized": 0, "total": 0,
                                              "todoSeats": 0, "tierCounts": {"A": 0, "B": 0, "C": 0, "D": 0}})
        bb["files"] += 1
        bb["recognized"] += row["recognized"]
        bb["total"] += row["assumptionsTotal"]
        bb["todoSeats"] += row["todoSeats"]
        bb["tierCounts"][row["tier"]] += 1
        files_out.append(row)

    # second pass cluster classification (needs the raw text; done per file above
    # would double-read - do it here once, files already read for L1; reuse bytes
    if order is not None:
        for entry, row in zip(qf, files_out):
            try:
                with open(os.path.join(args.root, entry["path"].replace("/", os.sep)), "rb") as fh:
                    text = fh.read().decode("utf-8", errors="replace")
                cl = classify_cluster(text, order, ctable)
            except (OSError, UnicodeDecodeError):
                cl = "physics-misc"
            row["cluster"] = cl
            bc = by_cluster.setdefault(cl, {"files": 0, "recognized": 0, "total": 0,
                                            "todoSeats": 0, "tierCounts": {"A": 0, "B": 0, "C": 0, "D": 0}})
            bc["files"] += 1
            bc["recognized"] += row["recognized"]
            bc["total"] += row["assumptionsTotal"]
            bc["todoSeats"] += row["todoSeats"]
            bc["tierCounts"][row["tier"]] += 1

    overall_pct = (tot_rec * 100 // tot_all) if tot_all else 0
    nmap = negative_finding_block(
        "word-face recognition over census qualifiedFiles=%d (censusId=%s, headPin=%s): "
        "L1 bracket-balanced per-declaration split + L2 regex rows (%d loaded, %d voided "
        "at admission, %s); file.text rows matched on comment-stripped text; cluster "
        "aggregation %s"
        % (len(qf), census.get("censusId"), census.get("headPin"),
           tax_info["rowsLoaded"], tax_info["rowsVoided"],
           tax_info["path"] or "builtin starter row",
           "from --cluster-table keyword data (stratify.py parity)" if order is not None
           else "absent (overall + band aggregate only; no clusters invented)"))

    doc = {
        "mapId": "vacgenv2-preflight-%s" % ts_utc[:10],
        "censusId": census.get("censusId"),
        "headPin": census.get("headPin"),
        "taxonomy": {"path": os.path.abspath(tax_info["path"]).replace("\\", "/") if tax_info["path"] else None,
                     "rowsLoaded": tax_info["rowsLoaded"], "rowsVoided": tax_info["rowsVoided"],
                     "builtin": tax_info["builtin"], "anchorVerifiedAt": tax_info["anchorVerifiedAt"]},
        "calibration": CALIBRATION + " (dated %s)" % ts_utc,
        "bandDefinitionBytes": {"S": "< %d" % BAND_S_LIMIT, "M": "< %d" % BAND_M_LIMIT,
                                "L": ">= %d" % BAND_M_LIMIT},
        "files": files_out,
        "aggregate": {
            "files": len(files_out),
            "recognized": tot_rec,
            "assumptionsTotal": tot_all,
            "coverageLowerPct": overall_pct,
            "tierCounts": tier_counts,
            "unparsedCount": unparsed_count,
            "byBand": by_band,
            "byCluster": by_cluster,
        },
        "negativeFinding": nmap,
        "generatedAt": ts_utc,
    }
    out_path = args.report or "difficulty-map.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("== %s v%s preflight report ==" % (TOOL_NAME, TOOL_VERSION))
    print("  census: %s (qualifiedFiles=%d, censusId=%s, headPin=%s)"
          % (os.path.abspath(args.census).replace("\\", "/"), len(qf),
             census.get("censusId"), census.get("headPin")))
    print("  taxonomy: rowsLoaded=%d rowsVoided=%d builtin=%s (%s)"
          % (tax_info["rowsLoaded"], tax_info["rowsVoided"], tax_info["builtin"],
             tax_info["path"] or "builtin starter row"))
    print("  tierCounts: A=%d B=%d C=%d D=%d | unparsedCount=%d"
          % (tier_counts["A"], tier_counts["B"], tier_counts["C"], tier_counts["D"],
             unparsed_count))
    print("  overall coverage lower bound (dated %s): %d/%d = %d%%"
          % (ts_utc, tot_rec, tot_all, overall_pct))
    for b in ("S", "M", "L"):
        bb = by_band.get(b, {})
        print("  band %s: files=%d recognized=%d/%d todoSeats=%d tiers=%s"
              % (b, bb.get("files", 0), bb.get("recognized", 0), bb.get("total", 0),
                 bb.get("todoSeats", 0), bb.get("tierCounts")))
    if order is not None:
        for cl in list(order) + (["physics-misc"] if "physics-misc" not in order else []):
            bc = by_cluster.get(cl)
            if bc:
                print("  cluster %-13s files=%-4d recognized=%-5d total=%-5d todoSeats=%-5d tiers=A%d B%d C%d D%d"
                      % (cl, bc["files"], bc["recognized"], bc["total"], bc["todoSeats"],
                         bc["tierCounts"]["A"], bc["tierCounts"]["B"],
                         bc["tierCounts"]["C"], bc["tierCounts"]["D"]))
    hardest = sorted(files_out, key=lambda r: (-r["budgetMinutes"], r["path"]))[:10]
    print("  top budget (uncalibrated extrapolation):")
    for r in hardest:
        print("    %-90s tier=%s budget=%dmin todo=%d"
              % (r["path"][:90], r["tier"], r["budgetMinutes"], r["todoSeats"]))
    print("[REPORT] %s" % os.path.abspath(out_path).replace("\\", "/"))
    print("[VERDICT]")
    print("  ok=true - preflight map written (per-file failures counted, not raised: "
          "unparsedCount=%d)" % unparsed_count)
    return 0


def do_verify_anchors(args, ts_utc):
    """--verify-anchors --mathlib <root> (C3.3): re-run the anchor gate over
    the loaded table; drift = row voided + drift report (rc=1)."""
    try:
        table, tax_info = load_taxonomy(args.taxonomy)
    except TaxonomyError as exc:
        print("FAIL-LOUD: taxonomy: %s" % exc)
        return 1
    if not args.mathlib:
        print("FAIL-LOUD: --verify-anchors requires --mathlib <root>")
        return 1
    drifted = []
    checked = 0
    for e in table:
        row = e["row"]
        for a in row["mathlibAnchors"]:
            checked += 1
            fp = os.path.join(args.mathlib, a["relPath"].replace("/", os.sep))
            try:
                with open(fp, encoding="utf-8", errors="replace") as fh:
                    lines = fh.read().splitlines()
                line = lines[a["line"] - 1] if 0 < a["line"] <= len(lines) else None
            except OSError:
                line = None
            if line is None or a["symbol"] not in line:
                drifted.append({"familyId": row["familyId"], "symbol": a["symbol"],
                                "relPath": a["relPath"], "line": a["line"]})
    print("== %s v%s anchor verification ==" % (TOOL_NAME, TOOL_VERSION))
    print("  table: %s (%d row(s) loaded)" % (tax_info["path"] or "builtin starter row",
                                              tax_info["rowsLoaded"]))
    print("  mathlib root: %s" % args.mathlib)
    print("  anchors checked: %d | drifted: %d" % (checked, len(drifted)))
    for d in drifted:
        print("    DRIFT %s: %s @ %s:%d" % (d["familyId"], d["symbol"], d["relPath"], d["line"]))
    print("[VERDICT]")
    if drifted:
        print("  ok=false - %d anchor(s) drifted; affected rows are voided per C3.3 "
              "(re-pin with full credentials per the anchor-generation wording form; "
              "previous anchors demoted to historical registration)" % len(drifted))
        return 1
    print("  ok=true - all carried anchors verified on pinned lines (window %s)" % ts_utc)
    return 0


# ---------------------------------------------------------------- CLI

def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    ap = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Vacuity probe skeleton generator with shape recognition "
                    "(zero network, zero compile, pure stdlib; casts skeletons only; "
                    "v1 CLI face preserved, v2 flags additive).")
    # ---- v1 protected face (verbatim semantics, vacgen.py:1131-1152) ----
    ap.add_argument("--in", dest="in_path", required=False, default=None,
                    help="(v1 face) statement-face file of the audited Lean artifact")
    ap.add_argument("--out", dest="out_dir", default=None,
                    help="(v1 face) output four-account skeleton directory (default: vacgen_out/<name>)")
    ap.add_argument("--toolchain", default=DEFAULT_TOOLCHAIN,
                    help="(v1 face) toolchain pin recorded in the headers")
    ap.add_argument("--snapshot", default=DEFAULT_SNAPSHOT,
                    help="(v1 face) mathlib snapshot window recorded in the headers")
    ap.add_argument("--audit-id", dest="audit_id", default=None,
                    help="(v1 face) audit ID for the header field (default: vacgen-<name>)")
    ap.add_argument("--name", default=None,
                    help="(v1 face) artifact name (default: sanitized input file stem)")
    ap.add_argument("--worktree", default=DEFAULT_WORKTREE,
                    help="(v1 face) compile working tree recorded in the build command line")
    ap.add_argument("--lake", default=DEFAULT_LAKE,
                    help="(v1 face) lake executable recorded in the build command line")
    ap.add_argument("--guard", default=DEFAULT_GUARD,
                    help="(v1 face) cpu_guard wrapper recorded in the build command line")
    ap.add_argument("--core", type=int, default=DEFAULT_CORE,
                    help="(v1 face) CoreN recorded in the build command line")
    ap.add_argument("--force", action="store_true",
                    help="(v1 face) overwrite the eight generator-owned targets if they exist")
    # ---- v2 additive flags (section 6.2; never touch the v1 face) ----
    ap.add_argument("--taxonomy", default=None,
                    help="(v2) taxonomy table path (chain: flag > VACGEN_TAXONOMY env > "
                         "tool-adjacent taxonomy.json > builtin starter row)")
    ap.add_argument("--preflight-all", dest="preflight_all", action="store_true",
                    help="(v2) preflight mode: census-qualified files, zero-compile "
                         "coverage pass -> difficulty map (mutually exclusive with --in)")
    ap.add_argument("--census", default=None,
                    help="(v2) census.json path (required with --preflight-all; read-only)")
    ap.add_argument("--root", default=None,
                    help="(v2) clone root the census walk used (required with --preflight-all)")
    ap.add_argument("--cluster-table", dest="cluster_table", default=None,
                    help="(v2) optional cluster keyword table JSON (stratify.py key surface) "
                         "for by-cluster aggregation")
    ap.add_argument("--report", default=None,
                    help="(v2) coverage report JSON path (cast) or difficulty map path "
                         "(preflight; default difficulty-map.json in cwd)")
    ap.add_argument("--exp-draft", dest="exp_draft", default=None,
                    help="(v2) RQW03 exp_port draft JSON path (cast mode)")
    ap.add_argument("--verify-anchors", dest="verify_anchors", action="store_true",
                    help="(v2) re-run the anchor admission gate over the loaded table")
    ap.add_argument("--mathlib", default=None,
                    help="(v2) mathlib checkout root for --verify-anchors")
    args = ap.parse_args(argv)

    ts_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # mode exclusivity + requirement checks (section 6.2/6.3)
    if args.preflight_all:
        if args.in_path:
            print("FAIL-LOUD: --preflight-all is mutually exclusive with --in "
                  "(usage error, rc=1)")
            return 1
        if not args.census or not args.root:
            print("FAIL-LOUD: --preflight-all requires --census <census.json> and "
                  "--root <clone> (usage error, rc=1)")
            return 1
        try:
            table, tax_info = load_taxonomy(args.taxonomy)
        except TaxonomyError as exc:
            print("FAIL-LOUD: taxonomy: %s" % exc)
            return 1
        return preflight_all(args, table, tax_info, ts_utc)
    if args.verify_anchors:
        return do_verify_anchors(args, ts_utc)
    if not args.in_path:
        ap.print_usage()
        print("FAIL-LOUD: --in is required in cast mode (v1 face preserved)")
        return 2

    return do_cast(args, ts_utc)


if __name__ == "__main__":
    sys.exit(main())
