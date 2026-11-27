#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""statement_identity.py - challenge<->proven two-face identity prober
(the encoding audit-line generation-3/4 method).
Purpose.  Take a claimed face (challenge-side statement file) and a proven
  face (the repo's certified counterpart), enumerate both statement faces
  (line-start theorem/lemma/def vernaculars over comment/string-masked
  text), normalize them for matching (whitespace collapse, declared-name
  placeholder, binder identifiers replaced with appearance-order
  placeholders, operators/head symbols kept), and answer the identity
  question mechanically at the statement face: an identity matrix
  (claimed x proven) whose cells are MATCHED / SEAM:<class> / UNMATCHED;
  UNMATCHED claimed-side cells are the uncast regions (generation-3
  method).
Interface.  python -I tools/statement_identity.py --claimed <file|dir>
  --proven <file|dir> [--out <json>] | --selftest.  One JSON report line
  (schema rocqwash-statement-identity/1); the counter shape, the pairing
  modes, and the mix refusal are in the extended contract below.
Dependencies.  Python 3 standard library only; zero network, zero compile,
  zero subprocess (the prober itself runs nothing); deterministic report
  (no wall clock, basenames only on the report face, sort_keys).
Evidence.  --selftest: tempfile-driven offline fixture vectors covering
  extraction, match and seam cells, header evidence, uncast-row
  detection, matrix vocabulary, cells-unmatched algebra, equivalence and
  tool-semantic seams, positional pairing, and dir pairwise mode.
Exit-codes.  0 report emitted (seams and uncast rows are findings, loud
  in the JSON, not failures - the seam_probe caliber); 2 usage error
  (file/dir mix, missing argument, bad --out) or selftest vector failure;
  9 missing input path.
"""
# Extended contract (kept outside the block above so the header stays
# within the 30-line budget of the annotation standard):
#   * Statement regex face = the frozen sibling canonical, 1:1 local
#     reimplementation (no import, per the anti-drift discipline of
#     seam/seam_probe.py over scan/mac_stmt_scan.py): line-start anchored
#     with the axiom_guard.py STMT_RE attribute/Locality prefix, extended
#     with Definition/Fixpoint/CoFixpoint from the seam_probe.py DECL_RE
#     face so "theorem/lemma/def" enumeration is covered on one face.
#   * Pairing: by declared name first (first occurrence wins, duplicates
#     listed loud), then by ordinal position over the leftovers.  A
#     positional candidate that fails all seam evidence and all content
#     candidacy collapses back to UNMATCHED on both sides - a proposed
#     pair is never counted as identity.
#   * Seam precedence on a matched pair: SYMBOL-RESOLUTION (same name,
#     different root-namespace/imports evidence) > TOOL-SEMANTIC
#     (attribute prefix / Instance vernacular / definition-vs-statement
#     kind / := spec wrapper present on one side only) > content
#     (normalized-equal -> MATCHED; token-aligned with every differing
#     position holding a head operator -> SEAM:DEFINITION-EQUIVALENCE,
#     flagged for human/differential confirmation, never auto-declared
#     equal) -> otherwise UNMATCHED.
#   * Imports evidence is token-scoped: the two faces' Require-header
#     root sets are compared only for the qualified roots the pair's own
#     statements reference, so a clean pair stays clean even when the two
#     files carry different headers elsewhere (this is what lets one
#     fixture pair carry both a clean match and a symbol seam).
#   * Vernacular keyword (Lemma vs Theorem) and binder spelling are
#     packaging, normalized away; kind-class (definition wrapper vs
#     statement) is NOT - it is tool-semantic evidence.
#   * DECLARATION-level caliber only: proof bodies past the statement-
#     terminating dot are never read; an all-MATCHED matrix is a negative
#     finding of this statement-face prober, not semantic identity.
#   * Former-header detail (carried out of the header on the RIS-17 budget
#     cure, verbatim in substance): the statement enumeration rides the
#     frozen sibling regex face; every counter is wrapped {value, basis}
#     and the top level carries the four-element scan_face field;
#     file+file is one pair; dir+dir is pairwise matching by normalized
#     name (casefolded alphanumeric stem, non-recursive, *.v only) over
#     one repo's two faces; a file/dir mix is refused at the front door
#     (usage error, not input); the uncast-region detection is the
#     matrix-uncast-area method.

import argparse
import hashlib
import io
import json
import os
import re
import sys

PROG = "statement_identity"
SCHEMA = "rocqwash-statement-identity/1"

# Statement families (line-start, sibling canonical face).  Group order:
# 1 = bracket attribute (#[...]), 2 = Locality keyword, 3 = vernacular,
# 4 = declared name.
DECL_RE = re.compile(
    r"(?m)^[ \t]*(?:"
    r"(#\[[^\]]*\][ \t]*\r?\n?[ \t]*)|"
    r"((?:Local|Global|Export|Declare)[ \t]+))*"
    r"(Theorem|Lemma|Corollary|Proposition|Remark|Fact|Example|Instance|"
    r"Definition|Fixpoint|CoFixpoint)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")

# Vernacular classes for wrapper evidence.
WRAPPER_KINDS = frozenset(("Definition", "Fixpoint", "CoFixpoint"))
INSTANCE_KIND = "Instance"

# Require-header evidence (seam_probe.py CH_REQUIRE face, plus the From
# clause, whose module is the namespace root of the import).  The module
# list is matched as dotted identifiers only, so the capture stops at the
# list's terminating dot instead of running into the next statement (the
# free-class capture of the raw CH_REQUIRE face overruns like that).
_REQUIRE_RE = re.compile(
    r"\bRequire\b(?:\s+(?:Import|Export))*((?:\s+"
    r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)+)")
_DOTTED_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*")
_FROM_RE = re.compile(
    r"\bFrom\b\s+([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)"
    r"\s+Require\b")

# Prologue exemption register (frozen, seam_probe.py PRELUDE_MODS): a root
# module in this register never counts as imports evidence.
PRELUDE_MODS = ("Coq", "Init", "Datatypes", "Logic", "Specif", "Nat",
                "Peano", "Decimal", "Hexadecimal", "Number", "Bool",
                "Ordinals")

# Qualified-name roots referenced inside a statement body.
_QUAL_RE = re.compile(
    r"(?<![A-Za-z0-9_'])([A-Za-z_][A-Za-z0-9_']*)\.([A-Za-z_][A-Za-z0-9_']*)")

# Binder keywords whose bound identifiers become placeholders.
_BINDER_KW_RE = re.compile(r"\b(?:forall|exists|fun|\u2200|\u2203|\u03bb)\b")
_IDENT_RE = re.compile(r"[A-Za-z_'][A-Za-z0-9_']*")

# Token stream for the definition-equivalence candidacy check (longest
# operator alternations first).
_TOKEN_RE = re.compile(
    r"[A-Za-z_'][A-Za-z0-9_']*|\d+|<->|->|==|<=|>=|=<|=>|:=|::|/\\|\\/|"
    r"[-=<>+*/@%~^|.!?:;,()\[\]{}]")

# Head operators: the differing positions that still count as definition-
# equivalence candidates.  Structural arrows (->) and the := wrapper are
# deliberately excluded: an implication-shape difference is not a head
# swap, and := is tool-semantic evidence upstream of this check.
HEAD_OPS = frozenset(("=", "==", "<->", "<=", ">=", "=<", "<", ">", "+",
                      "*", "-", "/", "::", "~", "/\\", "\\/"))

SEAM_SYMBOL = "SEAM:SYMBOL-RESOLUTION"
SEAM_DEF_EQ = "SEAM:DEFINITION-EQUIVALENCE"
SEAM_TOOL = "SEAM:TOOL-SEMANTIC"
MATCHED = "MATCHED"
UNMATCHED = "UNMATCHED"
CELL_VOCAB = frozenset((MATCHED, UNMATCHED, SEAM_SYMBOL, SEAM_DEF_EQ,
                        SEAM_TOOL))


class UsageError(Exception):
    """Usage-level fault (bad argument shapes, unwritable --out)."""


class MissingPath(Exception):
    """An input path that does not exist."""


# ---- lexical face (comment/string masking, statement termination) -----------

def mask_comments_strings(text):
    """Blank out comment and string literal bodies, preserving newlines and
    offsets 1:1 so line numbers and slices stay valid (the wash-side
    masking discipline: nested (* *) counted, backslash escapes honored,
    code positions untouched)."""
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                out.append("  ")
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                out.append("  ")
                i += 2
                continue
            out.append(c if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("(*", i):
            depth = 1
            out.append("  ")
            i += 2
            continue
        if c == '"':
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def stmt_end(clean, start_idx):
    """Statement termination: a line-start Proof keyword or a boundary dot
    (dot not preceded by a dot, followed by whitespace or EOF) - the
    frozen sibling form.  Returns (end index, how it ended)."""
    i, n = start_idx, len(clean)
    line_start = True
    while i < n:
        c = clean[i]
        if c == "\n":
            line_start = True
            i += 1
            continue
        if line_start:
            m = re.match(r"\s*Proof\b", clean[i:i + 200])
            if m:
                return i + m.end(), "Proof"
            line_start = False
        if c == ".":
            prev = clean[i - 1] if i > 0 else " "
            nxt = clean[i + 1] if i + 1 < n else " "
            if prev != "." and (nxt in " \t\r\n" or nxt == ""):
                return i + 1, "Dot"
        i += 1
    return n, "EOF"


# ---- statement extraction ----------------------------------------------------

def extract_statements(masked):
    """Enumerate the statement face: line-start theorem/lemma/def
    vernaculars, in order, with attribute presence, declared name, 1-based
    line and the masked statement body (declaration through the
    terminating dot / Proof keyword).  Statements inside consumed regions
    (a previous statement's body) are skipped."""
    out = []
    consumed = 0
    for m in DECL_RE.finditer(masked):
        if m.start() < consumed:
            continue
        kind, name = m.group(3), m.group(4)
        attr = bool(m.group(1) or m.group(2))
        end, how = stmt_end(masked, m.end())
        body = masked[m.end():end]
        consumed = end
        line = masked.count("\n", 0, m.start()) + 1
        out.append({"kind": kind, "name": name, "line": line,
                    "attr": attr, "body": body, "end_how": how})
    return out


def duplicate_names(stmts):
    """Declared names occurring more than once in one face (first
    occurrence wins in by-name pairing; the rest are listed loud)."""
    seen = {}
    dups = []
    for s in stmts:
        if s["name"] in seen and s["name"] not in dups:
            dups.append(s["name"])
        seen.setdefault(s["name"], s["line"])
    return dups


# ---- normalization for matching -----------------------------------------------

def _paren_binder_names(body, i):
    """body[i] == '('; return (bound names, index past the group).  Names
    are the identifiers before the first ':' of the group (the type
    position is not a name)."""
    depth = 0
    j = i
    n = len(body)
    while j < n:
        if body[j] == "(":
            depth += 1
        elif body[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    group = body[i + 1:j]
    head = group.split(":", 1)[0]
    return _IDENT_RE.findall(head), min(j + 1, n)


def collect_binder_names(body):
    """Bound identifiers in appearance order: after each forall/exists/fun
    keyword, the parenthesized binder groups and/or the bare identifier
    sequence up to the terminator (':' / ',' / '=>')."""
    names = []
    n = len(body)
    for m in _BINDER_KW_RE.finditer(body):
        i = m.end()
        while i < n:
            while i < n and body[i] in " \t\r\n":
                i += 1
            if i < n and body[i] == "(":
                got, i = _paren_binder_names(body, i)
                names.extend(got)
                continue
            mm = re.match(
                r"[A-Za-z_'][A-Za-z0-9_']*(?:\s+[A-Za-z_'][A-Za-z0-9_']*)*",
                body[i:])
            if not mm:
                break
            names.extend(_IDENT_RE.findall(mm.group(0)))
            i += mm.end()
            j = i
            while j < n and body[j] in " \t\r\n":
                j += 1
            if j < n and body[j] == "(":
                i = j
                continue
            break
    return names


def _word_replace(s, old, new):
    """Whole-word replacement (identifier boundaries only)."""
    if not old:
        return s
    return re.sub(r"(?<![A-Za-z0-9_'])" + re.escape(old) + r"(?![A-Za-z0-9_'])",
                  new, s)


def normalize_body(body, name):
    """Normalization for matching: declared name -> _NAME placeholder,
    binder identifiers -> _B0/_B1/... in name-appearance order, whitespace
    runs collapsed, outer whitespace stripped.  Operators and head symbols
    are kept verbatim; the vernacular keyword is already outside the body
    slice, so Lemma/Theorem packaging normalizes equal."""
    s = _word_replace(body, name, "_NAME")
    placeholders = {}
    for nm in collect_binder_names(s):
        if nm not in placeholders:
            placeholders[nm] = "_B%d" % len(placeholders)
    for nm, ph in placeholders.items():
        s = _word_replace(s, nm, ph)
    return re.sub(r"\s+", " ", s).strip()


def tokenize(norm):
    return _TOKEN_RE.findall(norm)


def is_def_equiv(nc, npro):
    """Definition-equivalence candidacy: equal-length token streams whose
    every differing position holds a head operator on both sides (heads
    differ, everything else identical after normalization).  Candidates
    are flags for human/differential confirmation, never auto-declared
    equal."""
    tc, tp = tokenize(nc), tokenize(npro)
    if len(tc) != len(tp):
        return False
    diffs = [(a, b) for a, b in zip(tc, tp) if a != b]
    if not diffs:
        return False  # fully equal is the MATCHED case, not a seam
    return all(a in HEAD_OPS and b in HEAD_OPS for a, b in diffs)


# ---- namespace / imports evidence ---------------------------------------------

def _root_of(dotted):
    root = dotted.strip().strip(".").split(".")[0]
    return root if root else None


def require_roots(masked):
    """Root modules evidenced by the file's Require headers (From-clause
    module and the Require list), prelude register exempt."""
    roots = set()
    for m in _FROM_RE.finditer(masked):
        r = _root_of(m.group(1))
        if r and r not in PRELUDE_MODS:
            roots.add(r)
    for m in _REQUIRE_RE.finditer(masked):
        for mod in _DOTTED_RE.findall(m.group(1)):
            r = _root_of(mod)
            if r and r not in PRELUDE_MODS:
                roots.add(r)
    return frozenset(roots)


def qual_roots(text):
    """Qualified-name roots referenced by a statement body (the Mod of
    Mod.name occurrences)."""
    return frozenset(m.group(1) for m in _QUAL_RE.finditer(text))


def symbol_evidence(c, p, roots_c, roots_p):
    """Root-namespace/imports evidence for a same-name pair: differing
    qualified-root sets inside the pair's statements, or a qualified root
    the pair references being present in one face's Require headers and
    absent from the other's (token-scoped header evidence)."""
    qr_c = qual_roots(c["body"])
    qr_p = qual_roots(p["body"])
    if qr_c and qr_p and qr_c != qr_p:
        return ("qualified roots differ inside the pair: claimed=%s"
                " proven=%s" % (sorted(qr_c), sorted(qr_p)))
    reasons = []
    for r in sorted(qr_c | qr_p):
        inc = r in roots_c
        inp = r in roots_p
        if inc != inp:
            reasons.append("root %s evidenced in %s Require headers only"
                           % (r, "claimed" if inc else "proven"))
    if reasons:
        return "; ".join(reasons)
    return None


def wrapper_evidence(c, p):
    """Tool-semantic evidence: attribute prefix, Instance vernacular,
    definition-wrapper kind, or := spec form present on one side only."""
    ev = []
    if c["attr"] != p["attr"]:
        ev.append("attribute prefix on %s side only"
                  % ("claimed" if c["attr"] else "proven"))
    if (c["kind"] == INSTANCE_KIND) != (p["kind"] == INSTANCE_KIND):
        ev.append("Instance vernacular on %s side only"
                  % ("claimed" if c["kind"] == INSTANCE_KIND else "proven"))
    kc = c["kind"] in WRAPPER_KINDS
    kp = p["kind"] in WRAPPER_KINDS
    if kc != kp:
        ev.append("definition-wrapper kind (%s) vs statement kind (%s)"
                  % (c["kind"] if kc else p["kind"],
                     p["kind"] if kc else c["kind"]))
    if (":=" in c["body"]) != (":=" in p["body"]):
        ev.append(":= spec wrapper on %s side only"
                  % ("claimed" if ":=" in c["body"] else "proven"))
    return "; ".join(ev) if ev else None


# ---- seam classification and pairing -------------------------------------------

def classify_pair(c, p, roots_c, roots_p, pairing):
    """Classify one matched-by-name/position pair.  Returns
    (cell, reason).  Precedence: SYMBOL-RESOLUTION > TOOL-SEMANTIC >
    content (MATCHED / DEFINITION-EQUIVALENCE) > UNMATCHED."""
    if c["name"] == p["name"]:
        ev = symbol_evidence(c, p, roots_c, roots_p)
        if ev:
            return SEAM_SYMBOL, ev
    nc = normalize_body(c["body"], c["name"])
    npro = normalize_body(p["body"], p["name"])
    candidate = (nc == npro) or is_def_equiv(nc, npro)
    wrap = wrapper_evidence(c, p)
    if wrap and (pairing == "name" or candidate):
        return SEAM_TOOL, wrap + ("" if pairing == "name"
                                  else " (positional pair, candidate content)")
    if nc == npro:
        return MATCHED, ("normalized statement bodies equal (binder-renamed,"
                         " vernacular-keyword-insensitive)")
    if is_def_equiv(nc, npro):
        return SEAM_DEF_EQ, ("token-aligned candidates differing only at head"
                             " operator position(s); flagged for human or"
                             " differential confirmation, never auto-declared"
                             " equal")
    return UNMATCHED, ("no name tie, no seam evidence, normalized bodies not"
                       " candidates")


def pair_statements(cstmts, pstmts, roots_c, roots_p):
    """Pair by declared name first (first occurrence, consumed on use),
    then by ordinal position over the leftovers.  Returns
    (matches, uncast_rows, surplus_cols) where matches is a list of
    (claimed_idx, proven_idx, pairing, cell, reason)."""
    by_name = {}
    for j, p in enumerate(pstmts):
        by_name.setdefault(p["name"], j)
    used_p = set()
    matches = []
    paired_c = set()
    # pass 1: by name
    for i, c in enumerate(cstmts):
        j = by_name.get(c["name"])
        if j is not None and j not in used_p:
            used_p.add(j)
            paired_c.add(i)
            cell, reason = classify_pair(c, pstmts[j], roots_c, roots_p,
                                         "name")
            matches.append((i, j, "name", cell, reason))
    # pass 2: positional over the leftovers (generation-3 enumeration
    # alignment; a failing candidate collapses back to UNMATCHED)
    left_c = [i for i in range(len(cstmts)) if i not in paired_c]
    left_p = [j for j in range(len(pstmts)) if j not in used_p]
    for i, j in zip(left_c, left_p):
        cell, reason = classify_pair(cstmts[i], pstmts[j], roots_c, roots_p,
                                     "position")
        if cell == UNMATCHED:
            continue
        matches.append((i, j, "position", cell, reason))
    return matches


def build_matrix(nrows, ncols, matches):
    """Dense identity matrix (claimed rows x proven cols); unpaired
    coordinates are UNMATCHED cells."""
    cells = [[UNMATCHED] * ncols for _ in range(nrows)]
    for i, j, _pairing, cell, _reason in matches:
        cells[i][j] = cell
    return cells


# ---- per-file probing -----------------------------------------------------------

def read_face(path):
    """Read one face file: bytes (md5), decoded text, masked text,
    statements, Require-header roots."""
    try:
        with io.open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise MissingPath("cannot read %s: %s" % (os.path.basename(path), exc))
    digest = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", "replace")
    masked = mask_comments_strings(text)
    stmts = extract_statements(masked)
    return {"file": os.path.basename(path), "md5": digest,
            "stmts": stmts, "roots": require_roots(masked),
            "dups": duplicate_names(stmts)}


def probe_file_pair(cpath, ppath):
    """Probe one claimed/proven file pair into a listing entry plus the
    raw tallies the top-level counters aggregate."""
    cface = read_face(cpath)
    pface = read_face(ppath)
    cstmts, pstmts = cface["stmts"], pface["stmts"]
    matches = pair_statements(cstmts, pstmts, cface["roots"], pface["roots"])
    cells = build_matrix(len(cstmts), len(pstmts), matches)

    def ref(stmt):
        return {"name": stmt["name"], "line": stmt["line"]}

    match_list = [{"claimed": ref(cstmts[i]), "proven": ref(pstmts[j]),
                   "pairing": pairing, "cell": cell, "reason": reason}
                  for i, j, pairing, cell, reason in matches]
    # Uncast / surplus are matrix-derived, not pairing-derived: a claimed
    # statement whose every cell is UNMATCHED is an uncast region even when
    # a name tie proposed a pair and the candidate collapsed (the ask's
    # generation-3 method reads the matrix cells, not the pairing book).
    uncast = [ref(cstmts[i]) for i in range(len(cstmts))
              if all(c == UNMATCHED for c in cells[i])]
    surplus = [ref(pstmts[j]) for j in range(len(pstmts))
               if all(cells[i][j] == UNMATCHED
                      for i in range(len(cstmts)))]
    tally = {"matched": 0, "symbol": 0, "defeq": 0, "tool": 0,
             "by_name": 0, "by_position": 0}
    for _i, _j, pairing, cell, _re in matches:
        if pairing == "name":
            tally["by_name"] += 1
        else:
            tally["by_position"] += 1
        if cell == MATCHED:
            tally["matched"] += 1
        elif cell == SEAM_SYMBOL:
            tally["symbol"] += 1
        elif cell == SEAM_DEF_EQ:
            tally["defeq"] += 1
        elif cell == SEAM_TOOL:
            tally["tool"] += 1
    # UNMATCHED cells = every off-diagonal coordinate plus collapsed
    # candidates; rows/cols with zero non-UNMATCHED cell are the uncast
    # (claimed side) and surplus (proven side) regions.
    uncast_rows = len(uncast)
    surplus_cols = len(surplus)
    entry = {
        "claimed": {"file": cface["file"], "md5": cface["md5"],
                    "require_roots": sorted(cface["roots"])},
        "proven": {"file": pface["file"], "md5": pface["md5"],
                   "require_roots": sorted(pface["roots"])},
        "statements_claimed": len(cstmts),
        "statements_proven": len(pstmts),
        "identity_matrix": {
            "rows": [ref(s) for s in cstmts],
            "cols": [ref(s) for s in pstmts],
            "cells": cells,
        },
        "matches": match_list,
        "uncast_claimed": uncast,
        "surplus_proven": surplus,
        "duplicate_names": {"claimed": cface["dups"],
                            "proven": pface["dups"]},
    }
    return entry, dict(tally, cells_total=len(cstmts) * len(pstmts),
                       cells_unmatched=len(cstmts) * len(pstmts)
                       - len(matches)
                       + sum(1 for _i, _j, _pa, cell, _re in matches
                             if cell == UNMATCHED),
                       uncast_rows=uncast_rows, surplus_cols=surplus_cols,
                       dup=len(cface["dups"]) + len(pface["dups"]),
                       stmts_c=len(cstmts), stmts_p=len(pstmts))


def norm_stem(path):
    """Normalized name for pairwise dir matching: casefolded alphanumeric
    stem (Foo_Proof.v and foo proof.v collide onto the same key)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^0-9a-z]+", "", stem.lower())


def list_dir_faces(path):
    """*.v files of a face directory, non-recursive, sorted."""
    names = sorted(fn for fn in os.listdir(path)
                   if fn.endswith(".v")
                   and os.path.isfile(os.path.join(path, fn)))
    return [os.path.join(path, fn) for fn in names]


# ---- judge -----------------------------------------------------------------------

SCAN_SCANNED = (
    "line-start theorem/lemma/def statement faces of the --claimed and"
    " --proven inputs (comments and string literals masked before"
    " enumeration), plus each file's Require/From header lines; in dir"
    " mode every *.v of both directories, non-recursive, sorted; nothing"
    " else is read"
)
SCAN_NOT_SCANNED = (
    "proof bodies past the statement-terminating dot (Proof/Qed are never"
    " read past), compiled artifacts (.vo/.glob), git metadata, and any"
    " file outside the given paths (dir mode reads *.v only,"
    " non-recursive)"
)
SCAN_NEGATIVE_FINDING = (
    "an all-MATCHED matrix is a negative finding of this statement-face"
    " prober over the two faces' declaration text, not an absolute claim"
    " of semantic identity: proof bodies and compiled behavior are never"
    " judged"
)
SCAN_EQUIVALENTS = (
    "not exhaustive; identity is judged on the declaration face only -"
    " binder-renamed or head-operator-differing candidates are flagged"
    " SEAM for human/differential confirmation and are never auto-declared"
    " equal; head symbols that are plain identifiers (e.g. two different"
    " relation names) do not align token-wise and land UNMATCHED"
)


def judge(claimed_path, proven_path):
    """Full judge: input-kind routing (file+file / dir+dir pairwise),
    per-pair probing, aggregated wrapped counters, listings, scan_face."""
    ck_f, ck_d = os.path.isfile(claimed_path), os.path.isdir(claimed_path)
    p_f, p_d = os.path.isfile(proven_path), os.path.isdir(proven_path)
    if not (ck_f or ck_d):
        raise MissingPath("--claimed path absent: %s"
                          % os.path.basename(claimed_path))
    if not (p_f or p_d):
        raise MissingPath("--proven path absent: %s"
                          % os.path.basename(proven_path))
    if (ck_f or p_f) and not (ck_f and p_f):
        raise UsageError(
            "--claimed and --proven must be both files or both directories"
            " (the two faces of one repo share the input kind; a file/dir"
            " mix has no pairwise semantics and is refused at the front"
            " door)")

    unpaired_c = unpaired_p = []
    if ck_f:
        pairs = [(claimed_path, proven_path)]
        mode = "single-pair"
        files_c = files_p = 1
    else:
        mode = "dir-pairwise"
        clist = list_dir_faces(claimed_path)
        plist = list_dir_faces(proven_path)
        cmap = {norm_stem(pth): pth for pth in clist}
        pmap = {norm_stem(pth): pth for pth in plist}
        pairs = [(cmap[k], pmap[k]) for k in sorted(set(cmap) & set(pmap))]
        unpaired_c = [os.path.basename(cmap[k])
                      for k in sorted(set(cmap) - set(pmap))]
        unpaired_p = [os.path.basename(pmap[k])
                      for k in sorted(set(pmap) - set(cmap))]
        files_c, files_p = len(clist), len(plist)

    entries = []
    agg = {"matched": 0, "symbol": 0, "defeq": 0, "tool": 0,
           "cells_unmatched": 0, "cells_total": 0, "uncast_rows": 0,
           "surplus_cols": 0, "dup": 0, "by_name": 0, "by_position": 0,
           "stmts_c": 0, "stmts_p": 0}
    for cpath, ppath in pairs:
        entry, t = probe_file_pair(cpath, ppath)
        entries.append(entry)
        for key in agg:
            agg[key] += t[key]

    def w(value, basis):
        return {"value": value, "basis": basis}

    report = {
        "schema": SCHEMA,
        "mode": mode,
        "inputs": {"claimed": os.path.basename(claimed_path),
                   "proven": os.path.basename(proven_path)},
        "files_claimed": w(files_c,
                           "claimed-face input files (1 for a single"
                           " --claimed file; *.v count of the directory in"
                           " dir mode)"),
        "files_proven": w(files_p,
                          "proven-face input files (same rule as"
                          " files_claimed)"),
        "pairs_probed": w(len(entries),
                          "file pairs probed (file+file is one pair; dir+dir"
                          " pairs by normalized name, both keys present)"),
        "pairs_unpaired": w(len(unpaired_c) + len(unpaired_p),
                            "face files with no normalized-name counterpart"
                            " in the other directory (dir mode only; listed"
                            " loud, never probed)"),
        "statements_claimed": w(agg["stmts_c"],
                                "statement-face declarations enumerated in"
                                " the claimed faces (line-start theorem /"
                                " lemma / def vernaculars, sibling regex"
                                " face)"),
        "statements_proven": w(agg["stmts_p"],
                               "same enumeration over the proven faces"),
        "pairs_by_name": w(agg["by_name"],
                           "matched pairs tied by declared name (first"
                           " occurrence; duplicates listed loud)"),
        "pairs_by_position": w(agg["by_position"],
                               "matched pairs tied by ordinal position over"
                               " the name-unpaired leftovers (a failing"
                               " positional candidate collapses to"
                               " UNMATCHED, never counted here)"),
        "cells_matched": w(agg["matched"],
                           "identity-matrix cells MATCHED (normalized"
                           " statement bodies equal: binder-renamed,"
                           " vernacular-keyword-insensitive)"),
        "seam_symbol_resolution": w(agg["symbol"],
                                    "cells SEAM:SYMBOL-RESOLUTION (same name,"
                                    " different root-namespace/imports"
                                    " evidence: qualified roots of the pair"
                                    " differ, or a referenced root is in one"
                                    " face's Require headers only -"
                                    " token-scoped header evidence)"),
        "seam_definition_equivalence": w(agg["defeq"],
                                         "cells SEAM:DEFINITION-EQUIVALENCE"
                                         " (token-aligned candidates differing"
                                         " only at head-operator positions;"
                                         " flagged for human/differential"
                                         " confirmation, never auto-declared"
                                         " equal)"),
        "seam_tool_semantic": w(agg["tool"],
                                "cells SEAM:TOOL-SEMANTIC (attribute prefix,"
                                " Instance vernacular, definition-wrapper"
                                " kind or := spec wrapper present on one side"
                                " only)"),
        "cells_unmatched": w(agg["cells_unmatched"],
                             "identity-matrix cells UNMATCHED (every"
                             " unpaired coordinate plus collapsed"
                             " candidates)"),
        "uncast_claimed_rows": w(agg["uncast_rows"],
                                 "claimed-side rows whose every matrix cell"
                                 " is UNMATCHED - the matrix-uncast-area"
                                 " detection, generation-3 method: a claimed"
                                 " statement with no proven-face counterpart"
                                 " cell is an uncast region of the encoding"
                                 " audit"),
        "surplus_proven_cols": w(agg["surplus_cols"],
                                 "proven-side columns whose every matrix"
                                 " cell is UNMATCHED (proven statements with"
                                 " no claimed counterpart; the transpose face"
                                 " of the uncast detection)"),
        "matrix_cells": w(agg["cells_total"],
                          "total dense matrix cells over all pairs"
                          " (claimed statements x proven statements)"),
        "duplicate_names": w(agg["dup"],
                             "declared names occurring more than once within"
                             " one face (first occurrence wins by-name"
                             " pairing; occurrences listed loud)"),
        "listings": {
            "pairs": entries,
            "unpaired_claimed": unpaired_c,
            "unpaired_proven": unpaired_p,
        },
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    return report


# ---- selftest --------------------------------------------------------------------

def selftest():
    """Fixture vectors (tempfile driven, offline, zero network/compile):
    the named fixture pair (one clean match, one symbol seam, one
    unmatched/uncast row), the matrix-shape vector, definition-equivalence
    and tool-semantic seam vectors, positional pairing, dir pairwise
    normalization, comment decoys, binder normalization and byte-stable
    determinism."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="statement_identity_self_")
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    def face(path, text):
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    try:
        # -- 1. the named fixture pair: clean match + symbol seam + uncast
        d1 = os.path.join(tmp, "fixture1")
        os.mkdir(d1)
        claimed_v = os.path.join(d1, "claimed.v")
        proven_v = os.path.join(d1, "proven.v")
        face(claimed_v,
             "(* claimed face fixture *)\n"
             "Require Import Coq.Arith.Arith.\n"
             "Lemma add_comm : forall n m : nat, n + m = m + n.\n"
             "Proof. intros. lia. Qed.\n"
             "Lemma max_le : forall a b : nat, QC.max a b = b.\n"
             "Proof. intros. apply QC.max_le. Qed.\n"
             "Lemma only_claimed : forall x : nat, x = x.\n"
             "Proof. reflexivity. Qed.\n")
        face(proven_v,
             "(* proven face fixture: QC namespace evidenced here only *)\n"
             "From QC Require Import B.\n"
             "Lemma add_comm : forall n m : nat, n + m = m + n.\n"
             "Proof. intros. apply Nat.add_comm. Qed.\n"
             "Lemma max_le : forall a b : nat, QC.max a b = b.\n"
             "Proof. intros. apply QC.max_le. Qed.\n")
        rep = judge(claimed_v, proven_v)
        pair = rep["listings"]["pairs"][0]
        mx = pair["identity_matrix"]
        check("fixture extraction 3x2",
              rep["statements_claimed"]["value"] == 3
              and rep["statements_proven"]["value"] == 2
              and len(mx["rows"]) == 3 and len(mx["cols"]) == 2,
              (rep["statements_claimed"], rep["statements_proven"]))
        check("clean match cell",
              mx["cells"][0][0] == MATCHED and len(pair["matches"]) == 2,
              mx["cells"])
        check("symbol seam cell",
              mx["cells"][1][1] == SEAM_SYMBOL
              and "QC" in pair["matches"][1]["reason"]
              and pair["matches"][1]["pairing"] == "name",
              pair["matches"])
        check("token-scoped header evidence",
              pair["claimed"]["require_roots"] == []
              and pair["proven"]["require_roots"] == ["B", "QC"]
              and mx["cells"][0][0] == MATCHED,
              (pair["claimed"]["require_roots"],
               pair["proven"]["require_roots"]))
        check("uncast row detected",
              mx["cells"][2] == [UNMATCHED, UNMATCHED]
              and rep["uncast_claimed_rows"]["value"] == 1
              and pair["uncast_claimed"] == [{"name": "only_claimed",
                                              "line": 7}],
              (mx["cells"][2], pair["uncast_claimed"]))
        check("surplus none",
              rep["surplus_proven_cols"]["value"] == 0
              and pair["surplus_proven"] == [],
              (rep["surplus_proven_cols"], pair["surplus_proven"]))

        # -- 2. matrix-shape vector (cell vocabulary, shape algebra)
        flat = [c for row in mx["cells"] for c in row]
        check("matrix-shape vocabulary",
              len(flat) == 3 * 2
              and all(c in CELL_VOCAB for c in flat)
              and sum(1 for c in flat if c != UNMATCHED)
              == rep["cells_matched"]["value"]
              + rep["seam_symbol_resolution"]["value"]
              + rep["seam_definition_equivalence"]["value"]
              + rep["seam_tool_semantic"]["value"],
              flat)
        check("cells-unmatched algebra",
              rep["cells_unmatched"]["value"]
              == rep["matrix_cells"]["value"]
              - rep["cells_matched"]["value"]
              - rep["seam_symbol_resolution"]["value"]
              - rep["seam_definition_equivalence"]["value"]
              - rep["seam_tool_semantic"]["value"],
              rep["cells_unmatched"])

        # -- 3. definition-equivalence seam: heads differ, binder-normalized
        #      candidates (never auto-declared equal)
        d2 = os.path.join(tmp, "fixture2")
        os.mkdir(d2)
        face(os.path.join(d2, "c.v"),
             "Theorem t_comm : forall x y : nat, x + y == y + x.\n"
             "Proof. intros. ring. Qed.\n")
        face(os.path.join(d2, "p.v"),
             "Lemma t_comm : forall a b : nat, a + b = b + a.\n"
             "Proof. intros. apply Nat.add_comm. Qed.\n")
        rep2 = judge(os.path.join(d2, "c.v"), os.path.join(d2, "p.v"))
        p2 = rep2["listings"]["pairs"][0]
        check("definition-equivalence seam",
              p2["identity_matrix"]["cells"][0][0] == SEAM_DEF_EQ
              and rep2["seam_definition_equivalence"]["value"] == 1
              and "never auto-declared" in p2["matches"][0]["reason"],
              p2["matches"])
        nc = normalize_body(" : forall x y : nat, x + y == y + x.", "t_comm")
        npr = normalize_body(" : forall a b : nat, a + b = b + a.", "t_comm")
        check("binder placeholders in candidates",
              nc != npr  # operators are kept verbatim, heads differ
              and is_def_equiv(nc, npr)  # candidacy is head-abstracted
              and tokenize(nc) != tokenize(npr)
              and [k for k, (a, b) in enumerate(zip(tokenize(nc),
                                                    tokenize(npr)))
                   if a != b] == [10]  # the only differing slot is the head
              and normalize_body("forall x y, x + y = y + x.", "n")
              == "forall _B0 _B1, _B0 + _B1 = _B1 + _B0.",
              (nc, npr))

        # -- 4. tool-semantic seam: wrapper packaging on one side only
        d3 = os.path.join(tmp, "fixture3")
        os.mkdir(d3)
        face(os.path.join(d3, "c.v"),
             "Lemma wrap_me : forall x : nat, P x.\n"
             "Proof. intros. exact id. Qed.\n")
        face(os.path.join(d3, "p.v"),
             "#[local] Definition wrap_me : forall x : nat, P x := id.\n")
        rep3 = judge(os.path.join(d3, "c.v"), os.path.join(d3, "p.v"))
        p3 = rep3["listings"]["pairs"][0]
        check("tool-semantic seam",
              p3["identity_matrix"]["cells"][0][0] == SEAM_TOOL
              and rep3["seam_tool_semantic"]["value"] == 1
              and "attribute prefix" in p3["matches"][0]["reason"]
              and ":=" in p3["matches"][0]["reason"],
              p3["matches"])

        # -- 5. positional pairing: name tie consumes beta; the alpha
        #      positional candidate fails -> UNMATCHED on both sides
        d4 = os.path.join(tmp, "fixture4")
        os.mkdir(d4)
        face(os.path.join(d4, "c.v"),
             "Lemma alpha : P1.\nProof. exact p1. Qed.\n"
             "Lemma beta : Q.\nProof. exact q. Qed.\n")
        face(os.path.join(d4, "p.v"),
             "Lemma alpha_prime : P2.\nProof. exact p2. Qed.\n"
             "Lemma beta : Q.\nProof. exact q. Qed.\n")
        rep4 = judge(os.path.join(d4, "c.v"), os.path.join(d4, "p.v"))
        p4 = rep4["listings"]["pairs"][0]
        check("positional candidate collapses",
              p4["identity_matrix"]["cells"][0][0] == UNMATCHED
              and p4["identity_matrix"]["cells"][1][1] == MATCHED
              and rep4["uncast_claimed_rows"]["value"] == 1
              and rep4["surplus_proven_cols"]["value"] == 1
              and rep4["pairs_by_name"]["value"] == 1
              and rep4["pairs_by_position"]["value"] == 0,
              p4["identity_matrix"]["cells"])

        # -- 5b. a name tie whose candidate collapses is still an uncast
        #        row: the matrix cells, not the pairing book, decide
        d4b = os.path.join(tmp, "fixture4b")
        os.mkdir(d4b)
        face(os.path.join(d4b, "c.v"),
             "Lemma alpha : P1.\nProof. exact p1. Qed.\n")
        face(os.path.join(d4b, "p.v"),
             "Lemma alpha : P2.\nProof. exact p2. Qed.\n")
        rep4b = judge(os.path.join(d4b, "c.v"), os.path.join(d4b, "p.v"))
        p4b = rep4b["listings"]["pairs"][0]
        check("collapsed name tie still uncast",
              p4b["identity_matrix"]["cells"][0][0] == UNMATCHED
              and rep4b["uncast_claimed_rows"]["value"] == 1
              and p4b["uncast_claimed"] == [{"name": "alpha", "line": 1}]
              and rep4b["pairs_by_name"]["value"] == 1
              and rep4b["cells_unmatched"]["value"] == 1,
              (p4b["uncast_claimed"], rep4b["uncast_claimed_rows"]))

        # -- 6. dir mode: pairwise matching by normalized name (casefold),
        #      unpaired files listed loud
        dc = os.path.join(tmp, "dir_claimed")
        dp = os.path.join(tmp, "dir_proven")
        os.mkdir(dc)
        os.mkdir(dp)
        face(os.path.join(dc, "A_Face.v"),
             "Lemma same : forall x : nat, x = x.\nProof. reflexivity. Qed.\n")
        face(os.path.join(dc, "extra_claimed.v"),
             "Lemma lonely : P.\nProof. exact p. Qed.\n")
        face(os.path.join(dp, "a_face.v"),
             "Lemma same : forall x : nat, x = x.\nProof. reflexivity. Qed.\n")
        rep5 = judge(dc, dp)
        check("dir pairwise normalized name",
              rep5["mode"] == "dir-pairwise"
              and rep5["pairs_probed"]["value"] == 1
              and rep5["listings"]["pairs"][0]["identity_matrix"]["cells"][0][0]
              == MATCHED
              and rep5["pairs_unpaired"]["value"] == 1
              and rep5["listings"]["unpaired_claimed"] == ["extra_claimed.v"]
              and rep5["listings"]["unpaired_proven"] == [],
              (rep5["mode"], rep5["listings"]["unpaired_claimed"]))

        # -- 7. comment decoy: a Theorem inside (* *) is not a statement
        d5 = os.path.join(tmp, "fixture5")
        os.mkdir(d5)
        face(os.path.join(d5, "c.v"),
             "(* Theorem hidden : False.\nProof. exact I. Qed. *)\n"
             "Lemma visible : True.\nProof. exact I. Qed.\n")
        rep6 = judge(os.path.join(d5, "c.v"), os.path.join(d5, "c.v"))
        check("masking decoy",
              rep6["statements_claimed"]["value"] == 1
              and rep6["statements_proven"]["value"] == 1
              and rep6["cells_matched"]["value"] == 1,
              rep6["statements_claimed"])

        # -- 8. determinism: byte-identical report over a re-judge
        again = judge(claimed_v, proven_v)
        check("determinism",
              json.dumps(rep, ensure_ascii=False, sort_keys=True)
              == json.dumps(again, ensure_ascii=False, sort_keys=True),
              "two judges of the same inputs diverged")

        # -- 9. report shape: wrapped counters, scan_face four elements
        bare = [k for k in rep
                if k not in ("schema", "mode", "inputs", "listings",
                             "scan_face")
                and not (isinstance(rep[k], dict)
                         and "value" in rep[k] and "basis" in rep[k])]
        check("value-basis-shape", bare == [], "bare keys: %s" % bare)
        check("scan-face-fields",
              sorted(rep["scan_face"]) == ["equivalents", "negative_finding",
                                           "not_scanned", "scanned"]
              and rep["scan_face"]["equivalents"].startswith("not exhaustive")
              and "not an absolute claim" in rep["scan_face"]["negative_finding"],
              sorted(rep["scan_face"]))

        # -- 10. usage faults: file/dir mix and missing paths
        mixed = missing = None
        try:
            judge(d1, claimed_v)  # a directory against a file
        except UsageError:
            mixed = "refused"
        except Exception as exc:  # unexpected shape - still a vector failure
            mixed = "wrong fault: %r" % (exc,)
        try:
            judge(os.path.join(tmp, "nope.v"), proven_v)
        except MissingPath:
            missing = "refused"
        except Exception as exc:
            missing = "wrong fault: %r" % (exc,)
        check("mix refused / missing path",
              mixed == "refused" and missing == "refused",
              (mixed, missing))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("STATEMENT-IDENTITY-SELFTEST FAIL: %d vector(s): %s"
              % (len(fails), ", ".join(fails)))
        return 2
    print("STATEMENT-IDENTITY-SELFTEST PASS: fixture pair (clean match +"
          " symbol seam + uncast row), matrix-shape, definition-equivalence,"
          " tool-semantic, positional collapse, dir pairwise, decoy masking,"
          " determinism, report shape, usage faults")
    return 0


# ---- CLI --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="challenge<->proven two-face statement identity prober"
                    " (identity matrix with MATCHED / SEAM:<class> /"
                    " UNMATCHED cells; uncast rows = generation-3"
                    " matrix-uncast-area detection)")
    ap.add_argument("--claimed", metavar="FILE|DIR",
                    help="claimed face: one statement file or a face"
                         " directory (*.v)")
    ap.add_argument("--proven", metavar="FILE|DIR",
                    help="proven face: the certified counterpart, same kind"
                         " as --claimed")
    ap.add_argument("--out", default=None, metavar="JSON",
                    help="write the stdout JSON payload to this path too")
    ap.add_argument("--selftest", action="store_true",
                    help="run the offline fixture vectors and exit")
    args = ap.parse_args(argv)

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        return selftest()

    if not args.claimed or not args.proven:
        print("FAIL-LOUD: --claimed and --proven are both required (the"
              " identity question needs the two faces)", file=sys.stderr)
        return 2

    try:
        report = judge(args.claimed, args.proven)
    except UsageError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 2
    except MissingPath as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        return 9

    payload = json.dumps(report, ensure_ascii=False, sort_keys=True)
    print(payload)
    if args.out:
        try:
            with io.open(args.out, "w", encoding="utf-8",
                         newline="\n") as fh:
                fh.write(payload)
                fh.write("\n")
        except OSError as exc:
            print("FAIL-LOUD: --out write failed: %s" % exc,
                  file=sys.stderr)
            return 2
        print("json -> %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
