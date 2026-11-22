#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# selftest face: python -I tools/vacgen_coq.py --selftest (in-process vectors;
#   zero network, zero compile, all offline; the only disk face is one batch
#   vector inside a TemporaryDirectory that is removed on exit)
"""vacgen_coq.py (v0.1) - Rocq statement-face coverage prober with shape recognition (four-layer engine, taxonomy-as-data).

Purpose.
    The Coq-side sibling of tools/vacgen.py (ticket 14 work stream 1; Rocq domain support).
    Wave 1 is a coverage/recognition face only - it enumerates the audited repo's
    own Rocq statement faces (*.v), splits each statement into its premise and
    conclusion faces, classifies every face against a data-driven taxonomy table
    (taxonomy-coq.json; zero family knowledge in-engine), and reports the Coq-L3
    coverage (recognized premises + conclusions / total) per statement and per
    batch, with honest TODO-SEAT degradation for unknown shapes (counted, never
    silent).  Layers mirror the Lean sibling (vacgen.py:11-13 docstring):
    L1 statement extraction + premise/conclusion decomposer, L2 taxonomy lookup,
    L3 confidence/coverage scoring with TODO-SEAT degradation, L4 harness modes
    (--from-v batch face, --selftest vector face).  The Lean vacgen stays
    untouched: the sibling line actively edits it, so this file shares no code
    path with it - only the architecture and the report discipline.

Interface.
    python -I tools/vacgen_coq.py --from-v <file.v|dir> [--taxonomy <path>]
            [--out <dir>] [--limit N]                 (batch, work stream 1: enumerate
            line-start Rocq assertion statements over the target .v file or the
            *.v files under the target directory, decompose and classify each,
            one JSON per statement plus <out>/summary.json)
    python -I tools/vacgen_coq.py --selftest                          (in-process
            vector face: taxonomy-load vector, recognition vectors over the
            fixture .v known families (real-lt premise + ne conclusion,
            forall-quantified conclusion, unknown-shape -> todo_seat), an L3
            computation vector, an L1 extraction/split vector, the builtin
            chain-end vector, the hole-face degradation vector, and a batch
            end-to-end vector inside a TemporaryDirectory; all offline)

Dependencies.
    Python stdlib only: argparse, contextlib, json, os, re, sys, tempfile,
    datetime.  Zero network, zero compile (no Rocq process is ever started),
    python -I compatible.  Writes only under the caller-named --out directory
    (default vacgen_coq_batch_out) - except --selftest, whose one batch vector
    writes inside a TemporaryDirectory that is removed on exit.

Evidence.
    The tool classifies word faces and never asserts mathematics - every
    unmatched face is a counted TODO-SEAT row feeding the gap telemetry, and
    every coverage number is a word-face lower bound over a dated window.  The
    taxonomy rows ground in the real Main shape census (1246 .v files scanned,
    26689 statements enumerated, 200 sampled over
    ConstructiveWorld-Main/ConstructiveWorld_Live; console
    D:/tmp/vacgen_survey/out/census_out.txt, detail
    D:/tmp/vacgen_survey/out/detail.json) and each row cites at least one real
    Main statement excerpt as anchor.

Exit-codes.
    0 = verdict ok=true (batch complete with per-statement failures counted as
        honest UNPARSED rows, never crashes; or all selftest vectors green);
    1 = batch-level fail-loud (taxonomy admission, unreadable input, zero
        statements enumerated) or any selftest vector red;
    2 = usage error (missing --from-v, non-positive --limit);
    --selftest: 0 = all vectors green, 1 = any vector red, 111 = conclusion
        vectors skipped (tool-adjacent taxonomy-coq.json absent; loud reason
        printed, the engine is still vector-proven on the builtin chain end).
"""

import argparse
import contextlib
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

TOOL_NAME = "vacgen-coq"
# Lineage.  Ported reference: the Lean sibling tools/vacgen.py v2.1.0 (4372
#   lines; four-layer taxonomy-as-data engine) - architecture, report faces and
#   selftest discipline mirrored; not a byte-shared codebase (the Lean vacgen
#   stays untouched; its sibling line actively edits it).  Ticket 14 work stream 1
#   (Rocq domain support), work order dated November 22, 2026.  Census basis:
#   the real Main shape census over ConstructiveWorld-Main/ConstructiveWorld_Live
#   (1246 .v files / 26689 statements / 200 sampled; artifacts kept outside the
#   surveyed tree at D:/tmp/vacgen_survey/).  Discipline: taxonomy-as-data,
#   TODO-SEAT honest degradation (vacgen.py:43-46 Evidence face), negative-
#   finding-boundary-law four elements on every coverage claim, dry-run
#   self-certification.
# 0.1.0 (work stream 1, November 22, 2026): initial face - L1 comment/string-masked
#   line-start assertion enumeration with the Module/Section/Namespace-End
#   full-name stack and the terminating-period capture; premise/conclusion
#   split per Rocq syntax (leading forall absorption per scope semantics +
#   top-level -> implication chain, <-> excluded); data-vs-hypothesis binder
#   seating; L2 taxonomy lookup over taxonomy-coq.json; L3 coverage with
#   honest TODO-SEAT degradation and gap telemetry; L4 --from-v batch and
#   --selftest vector faces.  No cast face: work stream 1 emits no skeleton files
#   (zero compile), so the report schema carries no skeleton paths.
TOOL_VERSION = "0.1.0"

BATCH_SUMMARY_SCHEMA = "vacgen-coq-batch-summary/1"
BATCH_REPORT_SCHEMA = "vacgen-coq-batch-statement/1"
BATCH_DEFAULT_OUT = "vacgen_coq_batch_out"
BATCH_ID_PREFIX = "vacgen-coq-batch"
GAP_TELEMETRY_TOP = 10
STATEMENT_CHAR_CAP = 20000  # monotone cap: a captured statement longer than this is an honest parse error

# ---------------------------------------------------------------- text tools
# Comment-and-string masking, the axiom_guard scanner pattern (nested (* ... *)
# comment bodies and "..." string literals are replaced with spaces so token
# scans and declaration detection never see comment text; the mask is
# length-preserving, so offsets in the masked text are offsets in the source).

BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
CLOSERS = set(BRACKET_PAIRS.values())


def mask_coq_text(src):
    """Length-preserving mask of nested (* ... *) comments and "..." strings.

    Rocq string literals escape a quote by doubling it (""); a backslash
    consumes the following character.  Masked bodies become single spaces,
    newlines survive, every other position keeps its character (comment-mimicking
    lines therefore cannot enumerate - a stronger face than the Lean
    axiom_sweep enumeration, which deliberately does not mask)."""
    out = list(src)
    i = 0
    n = len(src)
    depth = 0
    while i < n:
        if depth == 0 and src[i] == '"':
            out[i] = " "
            i += 1
            while i < n:
                if src.startswith('""', i):
                    out[i] = out[i + 1] = " "
                    i += 2
                    continue
                ch = src[i]
                if ch == "\\" and i + 1 < n:
                    out[i] = out[i + 1] = " "
                    i += 2
                    continue
                out[i] = " "
                if ch == '"':
                    i += 1
                    break
                i += 1
            continue
        if src.startswith("(*", i):
            depth += 1
            out[i] = out[i + 1] = " "
            i += 2
            continue
        if depth > 0 and src.startswith("*)", i):
            depth -= 1
            out[i] = out[i + 1] = " "
            i += 2
            continue
        i += 1
    return "".join(out)


def normalize_ws(s):
    """One whitespace-normalized word face (report and match faces both carry
    this form; the verbatim statement text stays in report.statement and in
    sources/<id>.v)."""
    return re.sub(r"[ \t\r\n]+", " ", s or "").strip()


class ParseError(Exception):
    pass


class TaxonomyError(Exception):
    pass


def find_top_char(s, ch, start=0):
    """Index of the first top-level occurrence of ch (bracket-depth aware)."""
    depth = 0
    i = start
    n = len(s)
    while i < n:
        c = s[i]
        if c in BRACKET_PAIRS:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ch:
            return i
        i += 1
    return -1


def find_top_colon(s, start=0):
    """Index of the first top-level ':' that is not a ':=' (bracket-depth
    aware), or -1 (verbatim semantics of the sibling's find_top_colon,
    vacgen.py:246-264)."""
    depth = 0
    i = start
    n = len(s)
    while i < n:
        c = s[i]
        if c in BRACKET_PAIRS:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ":":
            if i + 1 < n and s[i + 1] == "=":
                i += 2
                continue
            return i
        i += 1
    return -1


def find_top_arrow(s):
    """Index of the first top-level '->' chain arrow (bracket-depth aware),
    or -1.  The '<->' iff glyph is not a chain arrow (its '-' is preceded by
    '<' and is skipped)."""
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in BRACKET_PAIRS:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == "-" and s.startswith("->", i) \
                and (i == 0 or s[i - 1] != "<"):
            return i
        i += 1
    return -1


def strip_outer_parens(s):
    """Strip balanced outer parentheses (repeat); a pair only strips when it
    wraps the whole string (word-face helper, sibling vacgen.py:1405-1422)."""
    s = (s or "").strip()
    while len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        depth = 0
        wraps_all = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    wraps_all = False
                    break
        if not wraps_all:
            break
        s = s[1:-1].strip()
    return s


def scan_group_end(s, start):
    """End index (inclusive) of the balanced bracket group opening at s[start];
    raises ParseError on imbalance."""
    closer = BRACKET_PAIRS[s[start]]
    depth = 0
    i = start
    n = len(s)
    while i < n:
        c = s[i]
        if c in BRACKET_PAIRS:
            depth += 1
        elif c in CLOSERS:
            depth -= 1
            if depth == 0 and c == closer:
                return i
        i += 1
    raise ParseError("unbalanced bracket group in the statement face")


# ---------------------------------------------------------------- L1: statement extraction (.v face)

# Line-start Rocq vernacular assertion keywords - capitalized, word-bounded,
# the frozen work-order set.  Attribute-prefixed or indented-behind-notation
# spellings do not enumerate (declared limitation, word-face level).
STATEMENT_DECL_RE = re.compile(
    r"^[ \t]*(Theorem|Lemma|Corollary|Proposition|Example|Remark|Fact)"
    r"[ \t]+([A-Za-z_][A-Za-z0-9_']*)")
# Full names via the namespace/section/end stack (the tree_audit pattern):
# Module / Section / Namespace openers push a frame, End <name> pops it.
# `Module Type ...` frames carry no statements and are skipped.
MODULE_OPEN_RE = re.compile(
    r"^[ \t]*(Section|Namespace|Module)[ \t]+(?!Type\b)([A-Za-z_][A-Za-z0-9_']*)")
MODULE_END_RE = re.compile(r"^[ \t]*End[ \t]+([A-Za-z_][A-Za-z0-9_']*)")


def collect_v_decls(src):
    """(masked, decls) - line-start assertion enumeration over the masked text.

    Each decl carries its open-stack snapshot and the assembled full name at
    enumeration time (Module/Section/Namespace frames joined with '.')."""
    masked = mask_coq_text(src)
    decls = []
    stack = []
    offset = 0
    line_no = 0
    for line in masked.split("\n"):
        line_no += 1
        dm = STATEMENT_DECL_RE.match(line)
        if dm:
            decls.append({"kw": dm.group(1), "name": dm.group(2),
                          "line1": line_no,
                          "start": offset + dm.start(),
                          "full": ".".join(stack + [dm.group(2)])})
            offset += len(line) + 1
            continue
        om = MODULE_OPEN_RE.match(line)
        if om:
            stack.append(om.group(2))
            offset += len(line) + 1
            continue
        em = MODULE_END_RE.match(line)
        if em:
            nm = em.group(1)
            if nm in stack:
                while stack and stack.pop() != nm:
                    pass
            elif stack:
                stack.pop()
            offset += len(line) + 1
            continue
        offset += len(line) + 1
    return masked, decls


def find_statement_end(masked, start):
    """Offset of the statement's terminating period, or -1.

    A top-level '.' terminates the statement unless it is a qualified-name dot
    (followed by an identifier character) or a decimal point (followed by a
    digit).  The terminator is by construction the period before
    Proof./Admitted./Qed. - the first top-level period after the head."""
    depth = 0
    i = start
    n = len(masked)
    while i < n:
        ch = masked[i]
        if ch in BRACKET_PAIRS:
            depth += 1
        elif ch in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and ch == ".":
            nxt = masked[i + 1] if i + 1 < n else ""
            if nxt and (nxt.isalnum() or nxt in "_'"):
                i += 1
                continue
            return i
        i += 1
    return -1


# ------------------------------------------------- L1b: premise/conclusion split (Rocq syntax)

FORALL_LEAD_RE = re.compile(r"^forall(?![A-Za-z0-9_'])[ \t]*")
# Proposition markers for the binder seating test: comparison/equality glyph
# faces, negation, conjunction/disjunction notations, and the
# quantifier/lambda keywords.  `->` is deliberately NOT a marker: arrow faces
# split per the arrow rule below, so functional data binders (`f : X -> Real`,
# the common S/G-chapter spelling) agent as data while implication-typed
# applications (`le x y -> Qle a b`) still agent as hypotheses through their
# application heads.  Declared limitation: a bare `(H : P -> Q)` implication
# binder whose both arrow sides are bare identifiers seats as data (word-face
# only; no such spelling appeared among the sampled binder hypothesis faces).
PROP_MARK_COQ = re.compile(r"[<>=~]|/\\|\\/|\bforall\b|\bexists\b|\bfun\b|\blet\b")
# Known data-head families for the binder seating test (word face only): an
# application whose head carries one of these families seats as a data binder.
# Unknown-head applications agent as hypotheses (fail-safe side, declared).
DATA_HEAD_FAMILIES = ("list", "option", "prod", "sum", "sig", "sigT", "Stream")


def parse_binder_region(region):
    """Binder records over a region: paren/brace groups plus bare `names : type`
    faces, in source order (C2.2 parity: one record per name, never merged)."""
    recs = []
    buf = []

    def flush():
        text = "".join(buf).strip()
        del buf[:]
        if not text:
            return
        ci = find_top_colon(text)
        if ci >= 0:
            recs.append({"names": text[:ci].split(),
                         "type": text[ci + 1:].strip(), "kind": "bare"})
        else:
            recs.append({"names": [], "type": text, "kind": "bare"})

    i = 0
    n = len(region)
    while i < n:
        c = region[i]
        if c in "({":
            flush()
            end = scan_group_end(region, i)
            inner = region[i + 1:end]
            ci = find_top_colon(inner)
            if ci >= 0:
                recs.append({"names": inner[:ci].split(),
                             "type": inner[ci + 1:].strip(), "kind": "group"})
            else:
                recs.append({"names": [], "type": inner.strip(), "kind": "group"})
            i = end + 1
        else:
            buf.append(c)
            i += 1
    flush()
    return recs


def absorb_foralls(seg, binders_out):
    """Absorb every leading `forall ... ,` region of seg into binders_out and
    return the remainder (Rocq scope semantics: the binders scope over the
    whole remainder, so they precede the implication chain - the census
    ptp_main_fg two-forall face absorbs both)."""
    seg = seg.strip()
    while True:
        m = FORALL_LEAD_RE.match(seg)
        if not m:
            return seg
        comma = find_top_char(seg, ",", m.end())
        if comma < 0:
            raise ParseError("forall binder region without top-level comma")
        binders_out.extend(parse_binder_region(seg[m.end():comma]))
        seg = seg[comma + 1:].strip()


def split_type_chain(type_text):
    """(binders, premise_legs, conclusion) per Rocq syntax.

    Leading forall regions absorb first; then the top-level '->' chain splits
    ('<->' is not a chain arrow).  A chain piece may itself lead with forall
    (the mixa_qpow_decr census face `Qle q (1#1) -> forall m m' : nat,
    Nat.le m m' -> ...`); its binders absorb recursively and the remainder
    seats as a leg.  The final tail after the last arrow is the conclusion."""
    binders = []
    legs = []
    seg = absorb_foralls(type_text, binders)
    while True:
        ar = find_top_arrow(seg)
        if ar < 0:
            break
        piece = seg[:ar].strip()
        piece = absorb_foralls(piece, binders)
        if not piece:
            raise ParseError("empty implication leg in the statement face")
        legs.append(piece)
        seg = absorb_foralls(seg[ar + 2:], binders)
    if not seg:
        raise ParseError("empty conclusion tail in the statement face")
    return binders, [normalize_ws(l) for l in legs], normalize_ws(seg)


def is_data_type_face(t):
    """Conservative data-vs-hypothesis seating test for one binder type face
    (the sibling's looks_like_data_type principle, vacgen.py:368-380, ported
    to Rocq spellings).  True -> data variable (no premise face);
    False -> hypothesis (a premise face; the fail-safe side)."""
    t = strip_outer_parens(t or "")
    if not t:
        return False
    if PROP_MARK_COQ.search(t):
        return False
    if re.fullmatch(r"[A-Za-z_][\w'.!]*", t):
        return True  # a single (dotted) identifier is a data type face
    sides = []
    rest = t
    while True:
        ar = find_top_arrow(rest)
        if ar < 0:
            sides.append(rest)
            break
        sides.append(rest[:ar])
        rest = rest[ar + 2:]
    if len(sides) > 1:
        return all(is_data_type_face(side) for side in sides)
    m = re.match(r"^([A-Za-z_][\w'.!]*)", t)
    if m:
        head = m.group(1)
        for fam in DATA_HEAD_FAMILIES:
            if head == fam or head.startswith(fam + ".") \
                    or head.endswith("." + fam) or ("." + fam + ".") in head:
                return True
    return False


def decompose_statement(text):
    """L1 premise/conclusion decomposer over one captured statement face.

    Returns {kw, name, binders:{data, hypotheses}, premises, conclusion,
    premiseShape}.  A ':=' in the assertion face (an Example-definition
    spelling) raises non-assertion-declaration - an honest UNPARSED row,
    mirroring the sibling's C4.2 front gate (vacgen.py:674-681)."""
    masked = mask_coq_text(text).strip()
    m = STATEMENT_DECL_RE.match(masked)
    if not m:
        raise ParseError("statement head is not a Rocq assertion keyword face")
    kw, name = m.group(1), m.group(2)
    body_start = m.end()
    colon = find_top_colon(masked, body_start)
    if colon < 0:
        raise ParseError("no top-level assertion colon in the statement face")
    binder_region = masked[body_start:colon]
    type_text = masked[colon + 1:].strip()
    if type_text.endswith("."):
        type_text = type_text[:-1].rstrip()
    else:
        raise ParseError("statement face does not end at its terminating period")
    if find_top_assign(type_text) >= 0:
        raise ParseError("non-assertion-declaration: ':=' in the assertion face "
                         "(definition spelling, not a statement face)")
    group_binders = parse_binder_region(binder_region)
    forall_binders, legs, conclusion = split_type_chain(type_text)
    data, hypotheses = [], []
    for b in group_binders + forall_binders:
        names = [nm for nm in b["names"] if nm] or [""]
        btype = normalize_ws(b["type"])
        if is_data_type_face(b["type"]):
            for nm in names:
                data.append({"name": nm, "type": btype})
        else:
            for nm in names:
                hypotheses.append({"name": nm, "type": btype, "kind": b["kind"]})
    premises = [normalize_ws(p) for p in legs]
    shape = "bare" if not premises else "impl-chain(%d)" % len(premises)
    return {"status": "OK", "kw": kw, "name": name,
            "binders": {"data": data, "hypotheses": hypotheses},
            "premises": premises, "conclusion": conclusion,
            "premiseShape": shape}


def find_top_assign(s):
    """Index of the first top-level ':=' or -1 (the non-assertion probe)."""
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in BRACKET_PAIRS:
            depth += 1
        elif c in CLOSERS:
            if depth > 0:
                depth -= 1
        elif depth == 0 and c == ":" and s.startswith(":=", i):
            return i
        i += 1
    return -1


def statement_records(stmt):
    """The classification record list of one decomposed statement, in source
    order: binder-typed hypothesis faces, implication legs, then the
    conclusion record (both faces land here - the per-statement report face
    of design point 2)."""
    recs = []
    for h in stmt["binders"]["hypotheses"]:
        recs.append({"kind": "premise", "source": "binder",
                     "name": h["name"], "face": h["type"]})
    for p in stmt["premises"]:
        recs.append({"kind": "premise", "source": "leg", "name": "", "face": p})
    recs.append({"kind": "conclusion", "source": "conclusion",
                 "name": "", "face": stmt["conclusion"]})
    return recs


# ---------------------------------------------------------------- L2 taxonomy
# taxonomy-as-data: the engine contains zero premise/conclusion-family
# knowledge.  Rows live in taxonomy-coq.json; the builtin row below is only
# the fail-safe chain end - the data transcription of the census's largest
# conclusion family (rel:= 38/200, census_out.txt:70), anchored on the
# work-order sample statement.

BUILTIN_STARTER_REGEX = (r"^(?![\s\S]*(?:==|<=|>=|<>|:=|\bAnd\b|/\\))"
                         r"[\s\S]*(?<![<>=])=(?![>=])[\s\S]*$")

BUILTIN_STARTER_ROW = {
    "schemaVersion": 2,
    "familyId": "concl.eq.infix-rel",
    "cluster": "piu",
    "match": {"target": "conclusion", "regex": BUILTIN_STARTER_REGEX, "flags": ""},
    "priority": 30,
    "confidence": "HIGH",
    "censusBasis": "rel:= 38/200 sample head census (census_out.txt:70), the largest single head family",
    "mainAnchors": [
        {"file": "piu_zz_tau_enclosure_bank1.v", "line": 4065,
         "excerpt": "Lemma piu_zz_inPn_512_933 : zz_in_Pn 512 933 = false.",
         "provenance": "handoff-verbatim (ticket-14 wave-1 work order sample 1; "
                       "census detail.json records the same statement at the same file:line)"},
    ],
    "gapKeywords": ["boolean verdict", "computation anchor", "infix equality"],
    "sourceLane": "builtin-failsafe-transcription",
    "notes": ("builtin fail-safe chain end: data transcription of the "
              "concl.eq.infix-rel row of taxonomy-coq.json (bare infix = "
              "conclusion face with ==/<=/>=/<>/:=/And//\\ guards)"),
}

MATCH_TARGETS = ("premise.face", "conclusion")
REQUIRED_ROW_FIELDS = ("schemaVersion", "familyId", "cluster", "match", "priority",
                       "confidence", "censusBasis", "mainAnchors")
ROW_FLAG_MAP = {"": 0, "I": re.IGNORECASE, "IGNORECASE": re.IGNORECASE,
                "M": re.MULTILINE, "MULTILINE": re.MULTILINE,
                "S": re.DOTALL, "DOTALL": re.DOTALL}


def validate_row(row):
    """Row admission validation (C3.4 mirror): required fields + target enum +
    regex compiles + at least one Main anchor carrying a non-empty excerpt.
    Unknown fields ignored; missing required field = row invalid."""
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
    if not isinstance(row["censusBasis"], str) or not row["censusBasis"].strip():
        errs.append("censusBasis must be a non-empty string (census grounding)")
    anchors = row["mainAnchors"]
    if not isinstance(anchors, list) or len(anchors) < 1:
        errs.append("mainAnchors must be a non-empty list "
                    "(every row cites at least one real Main statement excerpt)")
    else:
        for a in anchors:
            if not isinstance(a, dict) or not a.get("excerpt", "").strip() \
                    or not a.get("file", "").strip() \
                    or not isinstance(a.get("line"), int):
                errs.append("mainAnchors entries must carry file, int line and a "
                            "non-empty verbatim excerpt")
                break
    return errs


def flags_int(flags):
    """Data-driven row match.flags -> re flag int (engine infrastructure;
    unknown values fail loud at admission)."""
    if isinstance(flags, int):
        return flags
    f = (flags or "").strip()
    if f not in ROW_FLAG_MAP:
        raise TaxonomyError("unsupported match.flags value: %r" % (flags,))
    return ROW_FLAG_MAP[f]


def load_table(rows):
    """Deterministic route order: priority desc, pattern length desc
    (specificity), familyId asc.  The engine never branches on familyId
    (sibling load_table semantics, vacgen.py:1070-1079)."""
    out = []
    for row in rows:
        flags = flags_int(row["match"].get("flags", ""))
        out.append({"row": row, "rx": re.compile(row["match"]["regex"], flags)})
    return sorted(out, key=lambda e: (-e["row"]["priority"],
                                      -len(e["row"]["match"]["regex"]),
                                      e["row"]["familyId"]))


def resolve_taxonomy_path(explicit):
    """Location chain: --taxonomy flag > VACGEN_COQ_TAXONOMY env >
    tool-adjacent taxonomy-coq.json > builtin starter row (fail-safe chain
    end; the sibling's C6.2 chain, vacgen.py:1082-1093)."""
    if explicit:
        return explicit, "--taxonomy flag"
    env = os.environ.get("VACGEN_COQ_TAXONOMY")
    if env:
        return env, "VACGEN_COQ_TAXONOMY env"
    same_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "taxonomy-coq.json")
    if os.path.isfile(same_dir):
        return same_dir, "tool-adjacent taxonomy-coq.json"
    return None, "builtin starter row (fail-safe chain end)"


def load_taxonomy(explicit):
    """Load + admit the taxonomy table.  Returns (entries, info).  A file
    whose row admission fails entirely = fail-loud (TaxonomyError, rc=1)."""
    path, source = resolve_taxonomy_path(explicit)
    info = {"source": source, "path": path, "rowsLoaded": 0, "rowsVoided": 0,
            "builtin": False, "invalid": []}
    if path is None:
        entries = load_table([BUILTIN_STARTER_ROW])
        info["rowsLoaded"], info["builtin"] = 1, True
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
            invalid.append({"familyId": row.get("familyId", "?")
                            if isinstance(row, dict) else "?", "errors": errs})
        else:
            valid.append(row)
    info["rowsLoaded"] = len(valid)
    info["rowsVoided"] = len(invalid)
    info["invalid"] = invalid
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


HOLE_RE = re.compile(r"(?<![\w'.!])_(?![\w'.!])")


def classify_record(rec, table):
    """First match wins under the deterministic table order.  Miss =
    TODO-SEAT.  Degraded faces (a standalone `_` hole) are intercepted before
    classification and forced to todo_seat with degraded=hole (C4.2 mirror:
    no third path to `recognized`).  Kind guards: conclusion rows classify
    conclusion records only, premise.face rows classify premise records only
    (the sibling's ticket-15 conclusion-row kind guard, vacgen.py:1178-1186,
    made symmetric for the two-target Coq table)."""
    face = normalize_ws(rec["face"])
    if HOLE_RE.search(face):
        return {"status": "todo_seat", "familyId": None, "confidence": None,
                "degraded": "hole", "matchedTarget": None, "face": face}
    for entry in table:
        m = entry["row"]["match"]
        target = m["target"]
        if target == "conclusion" and rec["kind"] != "conclusion":
            continue
        if target == "premise.face" and rec["kind"] != "premise":
            continue
        try:
            hit = entry["rx"].search(face) is not None
        except re.error:
            hit = False
        if hit:
            return {"status": "recognized", "familyId": entry["row"]["familyId"],
                    "confidence": entry["row"]["confidence"], "degraded": None,
                    "matchedTarget": target, "face": face}
    return {"status": "todo_seat", "familyId": None, "confidence": None,
            "degraded": None, "matchedTarget": None, "face": face}


# ---------------------------------------------------------------- L3 scoring

def tier_of(coverage_pct, total, unparsed):
    """Tier thresholds are >= monotone (C4.4 mirror).  D = degraded face."""
    if unparsed or total == 0:
        return "D"
    if coverage_pct >= 80:
        return "A"
    if coverage_pct >= 50:
        return "B"
    return "C"


def coverage_of(verdicts, unparsed=False):
    """Coq-L3 coverage of one statement: recognized faces / total faces over
    premises (binder hypotheses + implication legs) AND the conclusion - the
    acceptance metric face of design point 4.  Word-face lower bound over a
    dated window."""
    total = len(verdicts)
    recognized = sum(1 for v in verdicts if v["status"] == "recognized")
    pct = (recognized * 100 // total) if total else 0
    return {"recognized": recognized, "total": total,
            "todoSeats": total - recognized,
            "coverageLowerPct": (pct if total else None),
            "tier": tier_of(pct, total, unparsed)}


# ------------------------------------------------- gap telemetry (R-7 mirror)
# Additive report face aggregating todo_seat faces for taxonomy iteration (the
# batch long tail).  Purely additive data: never feeds the exit code.

GAP_HEAD_OPERATORS_COQ = ("==", "<=", ">=", "<->", "<>", "->", "=>",
                          "/\\", "\\/", "=", "<", ">", "~")
GAP_HEAD_IDENT_RE_COQ = re.compile(r"[A-Za-z_\u0370-\u03ff\u0100-\uffff][\w'.!]*")


def head_family(face):
    """Normalized head-symbol family of one face (word-face only; the sibling's
    conclusion_head_family, vacgen.py:1425-1444, ported to Rocq operator
    glyphs): outer balanced parentheses stripped, then the first top-level
    operator glyph (multi-char glyphs first) wins; with no top-level operator
    the first identifier token wins (lowercased, leading @ stripped); an empty
    or glyph-free face normalizes to the '?' residual (honest bucket)."""
    s = strip_outer_parens((face or "").strip())
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth > 0:
                depth -= 1
        elif depth == 0:
            for op in GAP_HEAD_OPERATORS_COQ:
                if s.startswith(op, i):
                    return op
        i += 1
    m = GAP_HEAD_IDENT_RE_COQ.search(s)
    if m:
        return m.group(0).lstrip("@").lower()
    return "?"


def gap_telemetry_block(todo_faces):
    """Build the gap_telemetry block from (kind, face) pairs of todo_seat
    faces - per statement and aggregated on the batch summary.  Families are
    ranked by count, ties broken by (kind, family), capped at the top
    GAP_TELEMETRY_TOP rows."""
    counts = {}
    for kind, face in todo_faces:
        key = (kind, head_family(face))
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))
    return {
        "todo_seats": {
            "value": len(todo_faces),
            "basis": ("premise/conclusion faces left unmatched by the "
                      "taxonomy in this batch"),
        },
        "families": [
            {"kind": kind, "family": fam,
             "count": {"value": n,
                       "basis": ("todo_seat faces with this normalized head "
                                 "symbol in this batch")}}
            for (kind, fam), n in ranked[:GAP_TELEMETRY_TOP]],
    }


def negative_finding_block(scanned_what):
    """C4.5 mirror: four elements accompany every coverage claim (negative-
    finding boundary law: a negative finding of the scan face, not an
    absolute claim)."""
    return {
        "scannedWhat": scanned_what,
        "notScanned": ("elaboration-time semantics (notation scope resolution, "
                       "implicit arguments, type-class instance resolution, "
                       "coercions); premise/conclusion spellings outside the "
                       "loaded taxonomy rows"),
        "nonAbsoluteClaim": True,
        "aliasesNotExhausted": True,
        "rescanCondition": ("taxonomy-coq row generation (new wave rows) or a "
                            "fresh Main shape census (new census window) - "
                            "earliest triggers re-scan"),
    }


def _write_json_file(path, doc):
    """House JSON face (identical to the sibling writers, vacgen.py:3058-3063):
    indent=1, ensure_ascii=False, LF newlines, one trailing newline."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


# ---------------------------------------------------------------- L4: batch face

def collect_v_targets(root):
    """[(abs_path, rel_path)] sorted - a file root scans that file, a
    directory root walks *.v recursively with .git directories skipped
    (sibling collect_lean_targets face, vacgen.py:2918-2934)."""
    if os.path.isfile(root):
        return [(os.path.abspath(root), os.path.basename(root))]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".v"):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, root).replace("\\", "/")
                out.append((abs_path, rel))
    out.sort()
    return out


def do_batch(args, ts_utc):
    """--from-v <file|dir> (batch face): enumerate the audited repo's own Rocq
    statement faces, decompose and classify each through the L1/L2/L3 layers,
    and emit one JSON per statement plus summary.json under the batch output
    root.  Per-statement failures are counted, never raised (preflight
    parity): an unparseable statement is an honest UNPARSED row with the parse
    reason carried verbatim - not a crash, and never a silent skip.
    rc 0 = batch complete; rc 1 = batch-level fail-loud."""
    print("== %s v%s statement-ingestion batch (from-v) ==" % (TOOL_NAME, TOOL_VERSION))
    try:
        table, tax_info = load_taxonomy(args.taxonomy)
    except (TaxonomyError, ValueError) as exc:
        print("FAIL-LOUD: taxonomy: %s" % exc)
        return 1
    print("[TAXONOMY]")
    print("  source: %s | rowsLoaded: %d | rowsVoided: %d | builtin: %s"
          % (tax_info["source"], tax_info["rowsLoaded"], tax_info["rowsVoided"],
             tax_info["builtin"]))

    root = args.from_v
    if not os.path.exists(root):
        print("FAIL-LOUD: --from-v target not found: %s" % root)
        return 1
    targets = collect_v_targets(root)
    unreadable = []
    enum_blocks = []
    for abs_path, rel in targets:
        try:
            with open(abs_path, "rb") as fh:
                raw = fh.read()
            src = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            # unreadable file: honest enumeration error row in the summary,
            # never a crash and never a silent skip (sibling parity)
            unreadable.append({"path": rel, "error": str(exc)})
            continue
        masked, decls = collect_v_decls(src)
        for d in decls:
            line_text = src.split("\n")[d["line1"] - 1] if d["line1"] else ""
            enum_blocks.append({"rel": rel, "abs": abs_path.replace("\\", "/"),
                                "src": src, "masked": masked, "decl": d,
                                "declLineText": line_text})
    print("[BATCH INPUT]")
    statements_enumerated = len(enum_blocks)
    print("  from-v root: %s (*.v targets: %d, statements enumerated: %d, "
          "unreadable files: %d, limit: %s)"
          % (os.path.abspath(root).replace("\\", "/"), len(targets),
             statements_enumerated, len(unreadable),
             args.limit if args.limit is not None else "none"))
    if args.limit is not None:
        enum_blocks = enum_blocks[:args.limit]
    if not enum_blocks:
        print("FAIL-LOUD: no statements enumerated (a batch classifies at least "
              "one statement; empty input is a usage error, rc=1)")
        return 1

    batch_id = "%s-%s" % (BATCH_ID_PREFIX, ts_utc[:10])
    out_root = args.out_dir or BATCH_DEFAULT_OUT
    sources_dir = os.path.join(out_root, "sources")
    reports_dir = os.path.join(out_root, "reports")
    os.makedirs(sources_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    counts = {"statements": len(enum_blocks), "ok": 0, "unparsed": 0}
    agg_rec = agg_total = 0
    batch_todo_faces = []
    rows = []
    n = len(enum_blocks)
    for i, block in enumerate(enum_blocks, 1):
        sid = "stmt_%03d" % i
        decl = block["decl"]
        doc = {
            "schema": BATCH_REPORT_SCHEMA,
            "id": sid,
            "batchId": batch_id,
            "mode": "from-v",
            "status": None,
            "source": {"kind": "v-file", "path": block["rel"],
                       "pathAbs": block["abs"], "declLine": decl["line1"],
                       "declName": decl["full"], "kw": decl["kw"]},
            "statement": None,
            "head": None,
            "binders": None,
            "premiseFace": "",
            "premises": [],
            "conclusionFace": "",
            "premiseShape": None,
            "l3": None,
            "basis": None,
            "parseError": None,
            "generatedAt": ts_utc,
        }
        stmt = None
        parse_error = None
        statement_text = None
        try:
            end = find_statement_end(block["masked"], decl["start"])
            if end < 0:
                raise ParseError(
                    "statement not terminated (no top-level period before EOF)")
            if end + 1 - decl["start"] > STATEMENT_CHAR_CAP:
                raise ParseError("statement exceeds the %d-character capture cap"
                                 % STATEMENT_CHAR_CAP)
            statement_text = block["src"][decl["start"]:end + 1]
        except ParseError as exc:
            parse_error = str(exc)
        if statement_text is not None:
            doc["statement"] = statement_text
            with open(os.path.join(sources_dir, sid + ".v"), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(statement_text)
            try:
                stmt = decompose_statement(statement_text)
            except ParseError as exc:
                parse_error = str(exc)
            except Exception as exc:  # any parse-stage failure: same honest row
                parse_error = "%s: %s" % (type(exc).__name__, exc)
        else:
            # capture failed: the decl line stays as the evidence face
            doc["statement"] = block["declLineText"]
            doc["captureError"] = parse_error
            with open(os.path.join(sources_dir, sid + ".v"), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(block["declLineText"] + "\n")

        if stmt is None:
            doc["status"] = "UNPARSED"
            doc["parseError"] = parse_error
            counts["unparsed"] += 1
            report_path = os.path.join(reports_dir, sid + ".json")
            _write_json_file(report_path, doc)
            rows.append({"id": sid, "status": "UNPARSED",
                         "head": None, "recognized": None, "total": None,
                         "report": os.path.relpath(report_path, out_root).replace("\\", "/")})
            reason = (parse_error or "").replace("\n", " ")[:90]
            print("  [%d/%d] %s UNPARSED - %s" % (i, n, sid, reason))
            continue

        premise_face = " ".join(
            "(%s : %s)" % (h["name"] or "_", h["type"])
            for h in stmt["binders"]["hypotheses"])
        doc["head"] = {"kw": stmt["kw"], "name": stmt["name"],
                       "fullName": decl["full"]}
        doc["binders"] = stmt["binders"]
        doc["premises"] = stmt["premises"]
        doc["premiseFace"] = premise_face
        doc["conclusionFace"] = stmt["conclusion"]
        doc["premiseShape"] = stmt["premiseShape"]

        verdicts = [classify_record(rec, table) for rec in statement_records(stmt)]
        cov = coverage_of(verdicts)
        doc["l3"] = cov
        doc["basis"] = {
            "records": [
                {"kind": rec["kind"], "source": rec["source"], "name": rec["name"],
                 "face": verdict["face"], "status": verdict["status"],
                 "familyId": verdict["familyId"],
                 "confidence": verdict["confidence"],
                 "degraded": verdict["degraded"],
                 "matchedTarget": verdict["matchedTarget"]}
                for rec, verdict in zip(statement_records(stmt), verdicts)],
            "taxonomy": {"path": tax_info["path"], "rowsLoaded": tax_info["rowsLoaded"],
                         "rowsVoided": tax_info["rowsVoided"], "builtin": tax_info["builtin"]},
        }
        for rec, verdict in zip(statement_records(stmt), verdicts):
            if verdict["status"] != "recognized":
                batch_todo_faces.append((rec["kind"], verdict["face"]))
        doc["status"] = "OK"
        counts["ok"] += 1
        agg_rec += cov["recognized"]
        agg_total += cov["total"]
        report_path = os.path.join(reports_dir, sid + ".json")
        _write_json_file(report_path, doc)
        rows.append({"id": sid, "status": "OK",
                     "head": "%s %s" % (stmt["kw"], decl["full"]),
                     "recognized": cov["recognized"], "total": cov["total"],
                     "report": os.path.relpath(report_path, out_root).replace("\\", "/")})
        print("  [%d/%d] %s OK %s %s | L3 %d/%d (%s%%)"
              % (i, n, sid, stmt["kw"], decl["full"], cov["recognized"],
                 cov["total"], cov["coverageLowerPct"] if cov["total"] else "-"))

    agg_pct = (agg_rec * 100 // agg_total) if agg_total else 0
    summary = {
        "schema": BATCH_SUMMARY_SCHEMA,
        "batchId": batch_id,
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "mode": "from-v",
        "input": {"fromV": os.path.abspath(args.from_v).replace("\\", "/"),
                  "filesScanned": len(targets),
                  "statementsEnumerated": statements_enumerated,
                  "statementsProcessed": len(enum_blocks),
                  "limitApplied": args.limit,
                  "unreadableFiles": unreadable},
        "taxonomy": {"path": os.path.abspath(tax_info["path"]).replace("\\", "/")
                     if tax_info["path"] else None,
                     "rowsLoaded": tax_info["rowsLoaded"],
                     "rowsVoided": tax_info["rowsVoided"],
                     "builtin": tax_info["builtin"]},
        "counts": dict(counts),
        "l3Aggregate": {"recognized": agg_rec, "total": agg_total,
                        "coverageLowerPct": agg_pct,
                        "scope": "OK rows only; word-face lower bound, dated snapshot"},
        "gap_telemetry": gap_telemetry_block(batch_todo_faces),
        "outRoot": os.path.abspath(out_root).replace("\\", "/"),
        "rows": rows,
        "negativeFinding": negative_finding_block(
            "word-face recognition over the enumerated Rocq statement faces "
            "(L1 comment/string-masked line-start enumeration + bracket-balanced "
            "binder/implication split + L2 regex rows in %s; %d row(s) loaded, "
            "%d voided at admission) over %d statement(s) processed (%d "
            "enumerated) from %d .v target(s) in from-v mode; window %s"
            % (tax_info["path"] or "builtin starter row", tax_info["rowsLoaded"],
               tax_info["rowsVoided"], len(enum_blocks), statements_enumerated,
               len(targets), ts_utc)),
        "generatedAt": ts_utc,
    }
    summary_path = os.path.join(out_root, "summary.json")
    _write_json_file(summary_path, summary)

    print("[BATCH SUMMARY]")
    print("  statements: %d | ok: %d | unparsed: %d"
          % (counts["statements"], counts["ok"], counts["unparsed"]))
    print("  L3 aggregate (OK rows only, word-face lower bound, dated %s): %d/%d = %d%%"
          % (ts_utc, agg_rec, agg_total, agg_pct))
    print("  out root: %s" % os.path.abspath(out_root).replace("\\", "/"))
    print("[REPORT] %s" % os.path.abspath(summary_path).replace("\\", "/"))
    print("[VERDICT]")
    print("  ok=true - batch complete; per-statement failures are counted rows, "
          "never silent (ok=%d unparsed=%d)" % (counts["ok"], counts["unparsed"]))
    return 0


# ---------------------------------------------------------------- selftest

# Selftest fixture .v with known families (census-real Main spellings):
#   - coqst_real_lt_prem_ne_concl: a real-lt premise (binder-typed hypothesis,
#     the pnk_log_mirror_B / w_T_sum_one census spelling) + a ne conclusion
#     (concl.neg.ne);
#   - coqst_forall_concl: a nat-le implication leg + a forall-quantified
#     (parenthesized) conclusion (concl.quantified.forall);
#   - coqst_in_module: a module-stacked fullName face with a bare infix =
#     conclusion (builtin-chain recognizable without the loaded table);
#   - coqst_unknown_face: an unknown-shape conclusion -> todo_seat.
SELFTEST_FIXTURE_V = (
    "(* vacgen-coq selftest fixture face: shapes are census-real Main\n"
    "   spellings; families: prem.cmp.applied-real-lt + concl.neg.ne,\n"
    "   prem.cmp.infix-nat-le + concl.quantified.forall, concl.eq.infix-rel,\n"
    "   and one unknown-shape face for the todo_seat vector. *)\n"
    "Module CoqstWrap.\n"
    "Lemma coqst_real_lt_prem_ne_concl : forall (q : Real) (Hq : real_lt real_zero q),\n"
    "  real_mult real_zero q <> real_one.\n"
    "Proof. Admitted.\n"
    "Lemma coqst_forall_concl : forall n : nat, (1 <= n)%nat ->\n"
    "  (forall m : nat, (m <= m)%nat).\n"
    "Proof. Admitted.\n"
    "Lemma coqst_in_module : 1 = 1.\n"
    "Proof. Admitted.\n"
    "End CoqstWrap.\n"
    "Lemma coqst_unknown_face : forall (x : Weird), gzeq x (3 # 4) /\\ Id x true.\n"
    "Proof. Admitted.\n"
)

# Batch end-to-end fixture: the fixture above plus one unterminated statement
# that must surface as an honest UNPARSED row (never a crash, never a drop).
BATCH_SELFTEST_FIXTURE_V = SELFTEST_FIXTURE_V + (
    "Lemma coqst_bad_unclosed : forall x : nat, (x <= x\n"
)


def do_selftest(ts_utc):
    """--selftest (in-process vector face; zero network, zero compile, all
    offline).  Freezes the work stream-1 recognition contract: the taxonomy-load
    vector, the recognition vectors over the fixture's known families
    (real-lt premise, ne conclusion, forall-quantified conclusion), the
    unknown-shape todo_seat vector, the hole-face degradation vector, the
    builtin chain-end vector, the L1 extraction/split vector, the L3
    computation vector, and the batch end-to-end vector (disk face confined
    to a TemporaryDirectory, removed on exit; console output captured).
    Returns 0 all green, 1 any red, 111 conclusion legs skipped (taxonomy
    table absent; loud reason printed)."""
    print("== %s v%s selftest (window %s) ==" % (TOOL_NAME, TOOL_VERSION, ts_utc))
    failures = []
    skips = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    def skip(name, reason):
        total[0] += 1
        print("SKIP " + name + " - " + reason)
        skips.append(name)

    def classify(face, kind, table):
        rec = {"kind": kind, "name": "", "face": face, "source": "selftest"}
        return classify_record(rec, table)

    def fixture_statements(text):
        """(masked, [(decl, captured_text_or_None, parse_error_or_None)]) over
        a fixture string - the L1 faces the vectors pin."""
        masked, decls = collect_v_decls(text)
        out = []
        for d in decls:
            err = None
            captured = None
            try:
                end = find_statement_end(masked, d["start"])
                if end < 0:
                    raise ParseError(
                        "statement not terminated (no top-level period before EOF)")
                captured = text[d["start"]:end + 1]
            except ParseError as exc:
                err = str(exc)
            out.append((d, captured, err))
        return masked, out

    try:
        table, tax_info = load_taxonomy(None)
    except (TaxonomyError, ValueError) as exc:
        print("FAIL selftest-setup - taxonomy load failed: %s" % exc)
        return 1
    builtin_only = bool(tax_info["builtin"])

    # T1 - taxonomy-load vector (always; the builtin chain end is a legal
    # green here - the vector face proves the engine, the deployment face is
    # proven separately by the absent-table skip below).
    t1_ok = (tax_info["rowsLoaded"] > 0 or tax_info["builtin"]) \
        and tax_info["rowsVoided"] == 0
    t1_detail = ("rowsLoaded=%d rowsVoided=%d builtin=%s source=%s"
                 % (tax_info["rowsLoaded"], tax_info["rowsVoided"],
                    tax_info["builtin"], tax_info["source"]))
    if not builtin_only:
        missing_anchors = []
        for entry in table:
            row = entry["row"]
            anchors = row.get("mainAnchors") or []
            if not anchors or not all(
                    isinstance(a, dict) and a.get("excerpt", "").strip()
                    for a in anchors):
                missing_anchors.append(row["familyId"])
            if not (row.get("censusBasis") or "").strip():
                missing_anchors.append(row["familyId"] + " (censusBasis)")
        t1_ok = t1_ok and not missing_anchors
        t1_detail += " | anchors-missing=%s" % (missing_anchors or "none")
    vec("taxonomy-load-admission", t1_ok, t1_detail)

    # T2 - recognition vectors over the fixture's known families (need the
    # loaded table; skipped loudly when only the builtin row is in force).
    if builtin_only:
        skip("premise-real-lt-recognized",
             "conclusion/recognition vectors need the loaded taxonomy-coq.json "
             "table (builtin fail-safe row in force)")
        skip("conclusion-ne-recognized",
             "conclusion/recognition vectors need the loaded taxonomy-coq.json "
             "table (builtin fail-safe row in force)")
        skip("conclusion-forall-recognized",
             "conclusion/recognition vectors need the loaded taxonomy-coq.json "
             "table (builtin fail-safe row in force)")
        skip("l3-coverage-computation",
             "exact L3 numbers need the loaded taxonomy-coq.json table")
    else:
        v = classify("real_lt real_zero q", "premise", table)
        vec("premise-real-lt-recognized",
            v["status"] == "recognized"
            and v["familyId"] == "prem.cmp.applied-real-lt"
            and v.get("matchedTarget") == "premise.face",
            "status=%s familyId=%s matchedTarget=%s"
            % (v["status"], v["familyId"], v.get("matchedTarget")))
        v = classify("real_mult real_zero q <> real_one", "conclusion", table)
        vec("conclusion-ne-recognized",
            v["status"] == "recognized" and v["familyId"] == "concl.neg.ne",
            "status=%s familyId=%s" % (v["status"], v["familyId"]))
        v = classify("(forall m : nat, (m <= m)%nat)", "conclusion", table)
        vec("conclusion-forall-recognized",
            v["status"] == "recognized"
            and v["familyId"] == "concl.quantified.forall",
            "status=%s familyId=%s" % (v["status"], v["familyId"]))

    # T3 - unknown shapes stay todo_seat (always; no row may claim them -
    # gzeq is a census face with no work stream-1 row, census_out.txt:105).
    v_p = classify("gzeq x y", "premise", table)
    v_c = classify("And (Id (f x) true) (QeqT a b)", "conclusion", table)
    vec("unknown-shape-todo-seat",
        v_p["status"] == "todo_seat" and v_p["familyId"] is None
        and v_c["status"] == "todo_seat" and v_c["familyId"] is None,
        "prem(gzeq x y)=%s concl(And ...)=%s" % (v_p["status"], v_c["status"]))

    # T4 - hole-face degradation (always; interception precedes recognition,
    # the C4.2 no-third-path contract).
    v_hp = classify("real_lt _ q", "premise", table)
    v_hc = classify("zz_in_Pn _ 933 = false", "conclusion", table)
    vec("hole-face-degraded",
        v_hp["status"] == "todo_seat" and v_hp.get("degraded") == "hole"
        and v_hc["status"] == "todo_seat" and v_hc.get("degraded") == "hole",
        "prem degraded=%s concl degraded=%s"
        % (v_hp.get("degraded"), v_hc.get("degraded")))

    # T5 - builtin chain end (always; the fail-safe row recognizes the
    # work-order sample face and the fixture's infix = face on any table).
    builtin_table = load_table([BUILTIN_STARTER_ROW])
    v_b1 = classify("zz_in_Pn 512 933 = false", "conclusion", builtin_table)
    v_b2 = classify("1 = 1", "conclusion", builtin_table)
    vec("builtin-chain-end-infix-rel",
        v_b1["status"] == "recognized"
        and v_b1["familyId"] == "concl.eq.infix-rel"
        and v_b2["status"] == "recognized",
        "sample1=%s/%s one_eq_one=%s"
        % (v_b1["status"], v_b1["familyId"], v_b2["status"]))

    # T6 - L1 extraction/split vector (always; the fixture decompose faces
    # are pinned exactly: full names via the Module stack, binder seating,
    # leg extraction, forall absorption, the terminating-period capture).
    try:
        masked, stmts = fixture_statements(SELFTEST_FIXTURE_V)
        if len(stmts) != 4 or any(err for _d, _c, err in stmts):
            vec("l1-extraction-split-faces", False,
                "statements=%d errors=%s"
                % (len(stmts), [err for _d, _c, err in stmts if err]))
        else:
            st = [decompose_statement(captured) for _d, captured, _e in stmts]
            conds = {
                "count": len(stmts) == 4,
                "fullname-1": stmts[0][0]["full"] == "CoqstWrap.coqst_real_lt_prem_ne_concl",
                "fullname-3": stmts[2][0]["full"] == "CoqstWrap.coqst_in_module",
                "fullname-4": stmts[3][0]["full"] == "coqst_unknown_face",
                "stmt1-binders": (
                    st[0]["binders"]["data"] == [{"name": "q", "type": "Real"}]
                    and st[0]["binders"]["hypotheses"]
                    == [{"name": "Hq", "type": "real_lt real_zero q", "kind": "group"}]),
                "stmt1-conclusion": st[0]["conclusion"] == "real_mult real_zero q <> real_one",
                "stmt1-shape": st[0]["premiseShape"] == "bare",
                "stmt2-leg": (st[1]["premises"] == ["(1 <= n)%nat"]
                              and st[1]["premiseShape"] == "impl-chain(1)"),
                "stmt2-conclusion": st[1]["conclusion"] == "(forall m : nat, (m <= m)%nat)",
                "stmt2-forall-absorbed": st[1]["binders"]["data"]
                == [{"name": "n", "type": "nat"}],
                "stmt3-conclusion": st[2]["conclusion"] == "1 = 1",
                "stmt4-conclusion": st[3]["conclusion"] == "gzeq x (3 # 4) /\\ Id x true",
            }
            vec("l1-extraction-split-faces", all(conds.values()),
                " ".join("%s=%s" % (k, conds[k]) for k in sorted(conds)))
    except Exception as exc:  # a vector crash is a RED, not a crash
        vec("l1-extraction-split-faces", False, "vector raised: %r" % (exc,))

    # T7 - L3 computation vector (exact numbers; needs the loaded table).
    # All four fixture statements are pinned: the in-module statement's
    # `1 = 1` conclusion is recognized by concl.eq.infix-rel (the same face
    # vector T5 proves on the builtin table) and the unknown-shape statement
    # (`gzeq x (3 # 4) /\\ Id x true`, no equality glyph, the /\\ guard) is
    # todo_seat - the two L3 boundary faces of the fixture.
    if builtin_only:
        pass  # skipped above by the T2 skip block (l3-coverage-computation)
    else:
        try:
            masked, stmts = fixture_statements(SELFTEST_FIXTURE_V)
            st = [decompose_statement(stmts[i][1]) for i in (0, 1, 2, 3)]
            covs = [coverage_of([classify_record(rec, table)
                                 for rec in statement_records(s)]) for s in st]
            conds = {
                "stmt1": covs[0] == {"recognized": 2, "total": 2, "todoSeats": 0,
                                     "coverageLowerPct": 100, "tier": "A"},
                "stmt2": covs[1] == {"recognized": 2, "total": 2, "todoSeats": 0,
                                     "coverageLowerPct": 100, "tier": "A"},
                "stmt3-in-module": covs[2] == {"recognized": 1, "total": 1,
                                               "todoSeats": 0,
                                               "coverageLowerPct": 100,
                                               "tier": "A"},
                "stmt4-unknown": covs[3] == {"recognized": 0, "total": 1,
                                             "todoSeats": 1,
                                             "coverageLowerPct": 0,
                                             "tier": "C"},
                "aggregate": (sum(c["recognized"] for c in covs) == 5
                              and sum(c["total"] for c in covs) == 6
                              and sum(c["recognized"] for c in covs) * 100
                              // sum(c["total"] for c in covs) == 83),
            }
            vec("l3-coverage-computation", all(conds.values()),
                " ".join("%s=%s" % (k, conds[k]) for k in sorted(conds))
                + " | covs=%s" % (covs,))
        except Exception as exc:
            vec("l3-coverage-computation", False, "vector raised: %r" % (exc,))

    # T8 - statement-ingestion batch end-to-end vector (always; recognition
    # counts are taxonomy-dependent and are NOT pinned - the pinned faces are
    # the honest statuses, the summary consistency, and the UNPARSED row).
    def batch_vector():
        with tempfile.TemporaryDirectory() as td:
            fixture = os.path.join(td, "fixture.v")
            with open(fixture, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(BATCH_SELFTEST_FIXTURE_V)
            out_root = os.path.join(td, "batch_out")
            ns = argparse.Namespace(from_v=fixture, out_dir=out_root,
                                    taxonomy=None, limit=None)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = do_batch(ns, ts_utc)
            with open(os.path.join(out_root, "reports", "stmt_001.json"),
                      encoding="utf-8") as fh:
                rep1 = json.load(fh)
            with open(os.path.join(out_root, "reports", "stmt_005.json"),
                      encoding="utf-8") as fh:
                rep5 = json.load(fh)
            with open(os.path.join(out_root, "summary.json"),
                      encoding="utf-8") as fh:
                summ = json.load(fh)
            ok_rows = [r for r in summ["rows"] if r["status"] == "OK"]
            conds = {
                "rc": rc == 0,
                "statuses": [r["status"] for r in summ["rows"]]
                == ["OK", "OK", "OK", "OK", "UNPARSED"],
                "summary-counts": (summ["counts"]["statements"] == 5
                                   and summ["counts"]["ok"] == 4
                                   and summ["counts"]["unparsed"] == 1),
                "unparsed-row": (rep5["status"] == "UNPARSED"
                                 and bool(rep5["parseError"])
                                 and rep5["l3"] is None),
                "statement-evidence": os.path.isfile(
                    os.path.join(out_root, "sources", "stmt_005.v")),
                "l1-face": (rep1["head"]["fullName"]
                            == "CoqstWrap.coqst_real_lt_prem_ne_concl"
                            and rep1["premiseFace"] == "(Hq : real_lt real_zero q)"
                            and rep1["conclusionFace"]
                            == "real_mult real_zero q <> real_one"),
                "aggregate-consistent": (
                    summ["l3Aggregate"]["recognized"]
                    == sum(r["recognized"] or 0 for r in ok_rows)
                    and summ["l3Aggregate"]["total"]
                    == sum(r["total"] or 0 for r in ok_rows)),
                "gap-telemetry-basis": (summ["gap_telemetry"]["todo_seats"]["basis"]
                                        == "premise/conclusion faces left "
                                           "unmatched by the taxonomy in this "
                                           "batch"),
            }
            return all(conds.values()), \
                " ".join("%s=%s" % (k, conds[k]) for k in sorted(conds))

    try:
        ok, detail = batch_vector()
        vec("batch-e2e-summary-consistency", ok, detail)
    except Exception as exc:  # a vector crash is a RED, not a crash
        vec("batch-e2e-summary-consistency", False, "vector raised: %r" % (exc,))

    print("== vacgen-coq selftest: %d vectors, %d pass, %d fail, %d skip =="
          % (total[0], total[0] - len(failures) - len(skips),
             len(failures), len(skips)))
    if failures:
        print("  ok=false - failing vectors: %s" % ", ".join(failures))
        return 1
    if skips:
        print("  skip-face: %d recognition vector(s) skipped - tool-adjacent "
              "taxonomy-coq.json absent (rc=111; loud environment-absent reason "
              "per the tools selftest contract)" % len(skips))
        return 111
    print("  ok=true - all vectors green (window %s)" % ts_utc)
    return 0


# ---------------------------------------------------------------- CLI

def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    ap = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Rocq statement-face coverage prober with shape recognition "
                    "(Coq-side sibling of vacgen.py; zero network, zero compile, "
                    "pure stdlib; classifies word faces only - every unmatched "
                    "face is a counted TODO-SEAT row).")
    ap.add_argument("--from-v", dest="from_v", default=None,
                    help="batch input: a .v file, or a directory whose *.v files "
                         "are walked recursively (.git skipped); line-start Rocq "
                         "assertion statements are enumerated, decomposed and "
                         "classified; one JSON per statement plus summary.json "
                         "under --out")
    ap.add_argument("--taxonomy", default=None,
                    help="taxonomy table path (chain: flag > VACGEN_COQ_TAXONOMY "
                         "env > tool-adjacent taxonomy-coq.json > builtin "
                         "starter row)")
    ap.add_argument("--out", dest="out_dir", default=None,
                    help="batch output root (default: vacgen_coq_batch_out); the "
                         "only disk face the batch face writes")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of statements processed after "
                         "enumeration (counted in summary.input.limitApplied)")
    ap.add_argument("--selftest", dest="selftest", action="store_true",
                    help="in-process vector face (zero network, zero compile, "
                         "all offline): taxonomy-load vector, recognition vectors "
                         "over the fixture known families, unknown-shape "
                         "todo_seat vector, hole-face degradation vector, builtin "
                         "chain-end vector, L1 extraction/split vector, L3 "
                         "computation vector, batch end-to-end vector inside a "
                         "TemporaryDirectory; standalone - other mode flags are "
                         "ignored")
    args = ap.parse_args(argv)

    ts_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.selftest:
        return do_selftest(ts_utc)

    if not args.from_v:
        ap.print_usage()
        print("FAIL-LOUD: --from-v <file|dir> is required in batch mode "
              "(usage error, rc=2)")
        return 2
    if args.limit is not None and args.limit <= 0:
        print("FAIL-LOUD: --limit must be a positive integer (usage error, rc=2)")
        return 2

    return do_batch(args, ts_utc)


if __name__ == "__main__":
    sys.exit(main())
