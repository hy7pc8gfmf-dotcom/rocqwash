#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tree_audit.py - read-only tree health audit over .lean/.v source trees.
Purpose.  One JSON-line census of a source tree: file/byte/line totals,
  declaration counts split thm/defFam across two per-suffix grammar faces
  (Lean lowercase in .lean, Rocq vernacular in .v), an unsound-feature
  sweep, a trust_surface sweep of the platform blind-spot switches, and
  the comment, per-directory, largest-file, and import-root tables.
  Every counter travels as {"value": N, "basis": rule} and counting is
  byte-literal (comments and strings count); the sweep tables, field
  list, and shape contract live in the extended contract below.
Interface.  python3 tools/tree_audit.py --root DIR [--json OUT] |
  --selftest; stdout carries one JSON line and --json writes the same
  payload to OUT; stderr additionally carries the independent grep
  cross-check commands for the acceptance gate.  The full field list and
  shape are in the extended contract.
Dependencies.  Python 3 standard library only; the fast path reads each
  file once in binary and scans bytes with precompiled regexes: zero
  subprocess, zero network, zero imports of the scanned tree, zero tree
  writes.
Evidence.  --selftest builds a temporary fixture tree with hand-derived
  known counts and asserts every report field, the value/basis shape,
  the cross-grammar sum identity, the trust-surface tokens, the exit
  faces, and the --json round trip; the enumeration is in the extended
  contract.
Exit-codes.  0 green (complete scan or green selftest); 1 red (any
  selftest vector fails, any file read fails, or the --json write
  fails); 2 usage (missing or non-directory --root, --selftest combined
  with scan flags, unknown flags).
"""

# Extended contract (kept outside the five-field header so the header
# stays within the 30-line budget of the annotation standard; the moved
# facts are carried over from the former header verbatim in substance):
#
# Unsound-feature sweep tokens: sorry, sorryAx, axiom, opaque,
#   native_decide, unsafe, implemented_by, extern, ofReduceBool.
# Trust-surface sweep: the platform blind-spot switches that Print
#   Assumptions / #print axioms can never see, per-grammar fixed tables -
#   Rocq: Unset Guard Checking, Unset Positivity Checking, Unset Universe
#   Checking, Unset Elimination Schemes, native_compute, vm_compute,
#   Declare ML Module; Lean: unsafe def/theorem/instance,
#   @[implemented_by, @[extern, native_decide, Lean.ofReduceBool, partial
#   def, noncomputable, debug.skipKernelTC, set_option.  The
#   trust_surface block carries its switches and files_affected as
#   value+basis counters plus a manifest_note receipt, and scan_face
#   states what the scan covers and what it cannot see.
# Counting semantics: byte-literal (raw bytes, so comments and strings
#   count too); .lean stays lowercase, calibrated one-to-one to the
#   sandbox census_rh.py face so a same-.lean cross-check is
#   field-for-field equal; .v rides the Rocq vernacular face added by
#   R-3b because the lowercase faces undercount capitalized .v trees by
#   orders of magnitude.  The root is scanned literally (no src/
#   descent).
# Fields: files, bytes, lines, nonEmptyLines, thm, defFam, decls,
#   grammar_faces, sorry, sorryAx, axiom, opaque, native_decide, unsafe,
#   implemented_by, extern, ofReduceBool, trust_surface, commentLines,
#   blockCommentFiles, perDir, largest10, zeroDeclFiles, importRoots,
#   root, errors, errorCount, scan_face.  Shape: every field but
#   scan_face and the trust_surface block is {"value": ..., "basis":
#   ...}; trust_surface carries switches (each token a {value, basis}
#   counter), files_affected and the manifest_note receipt; perDir.value
#   maps the first path segment to {files, decls, bytes}; largest10.value
#   is [{"path","bytes"}]; importRoots.value is a top-ten [[root,count]]
#   list; errors.value is a capped string list; grammar_faces.value maps
#   the grammar name (lean, rocq) to {thm, defFam} counters that each
#   carry value + basis; scan_face has exactly the four fields scanned,
#   not_scanned, negative_finding, equivalents.
# Evidence detail: the fixture tree (.v and .lean files with hand-derived
#   known counts covering the thm/defFam split per grammar, a capitalized
#   Rocq .v fixture (3 Theorem + 1 Corollary + 2 Definition + 1 Inductive)
#   asserted through the rocq face, a no-leak guard proving the lowercase
#   faces contribute nothing to .v files, and blank / whitespace-only
#   lines); every report field asserted against those vectors; the
#   value/basis shape of every top-level key but scan_face (the
#   grammar_faces counters included), the cross-grammar sum identity,
#   basis strings naming both grammars, the grep cross-check commands
#   carrying the same keyword tables, and the four verbatim scan_face
#   strings; a trust-surface fixture pair (.v with one Unset Guard
#   Checking plus one native_compute; .lean with unsafe def,
#   @[implemented_by, native_decide and a set_option line) asserted
#   token-exact with files_affected and a zero-switch negative-finding
#   shape on the empty tree; the exit-code faces (green scan, empty tree,
#   missing root rc=2) and the --json round trip; the Deicyde mirror
#   cross-check against census_rh.py runs out of tree, and the real-tree
#   rocq acceptance gate re-derives the rocq-face counts with the printed
#   grep commands (no expected count is hardcoded in this file).

import argparse
import json
import os
import re
import shlex
import shutil
import sys
import tempfile

TOOL = "tree_audit"

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Calibration.  Every pattern below is byte-identical to the census_rh.py
# oracle in attn/_alpoge_rh_audit_20261121/ (the Deicyde cross-check face):
# thm/deffam/axiom/opaque/unsafe/commentLine are line-anchored (re.M), sorry
# and sorryAx are word-bounded tokens, native_decide is a bare token,
# implemented_by and extern are attribute prefixes, ofReduceBool is the
# Lean.ofReduceBool path, block comments are the "/-" opener, the import
# pattern captures the first dotted segment of the module name, and
# nonEmptyLines is the oracle's splitlines-then-strip face.  One deliberate
# deviation from the oracle: decls is reported here as the combined total
# thm + defFam summed across both grammar faces (8 lowercase line-start
# keywords in .lean, 15 capitalized ones in .v), not the oracle's narrower
# 5-keyword decl face, per the v2 audit contract; the two agree exactly on
# .lean trees with no structure/class/inductive at line start.  The oracle
# compiles the sorryAx pattern but never sums it; this tool closes that gap
# per the audit contract (sorryAx is a token total).  A file enters the scan
# by a .lean or .v suffix (the oracle scans .lean only), and any .git
# directory is skipped wholesale.
#
# R-3b dual grammar.  The declaration faces are chosen per source suffix:
# .lean keeps the lowercase faces above byte-identical to the oracle; .v
# counts the capitalized Rocq vernacular instead (ROCQ_THM_KEYWORDS /
# ROCQ_DEFFAM_KEYWORDS), because on real .v trees the lowercase faces
# undercount declarations by orders of magnitude.  thm, defFam and decls
# are cross-grammar totals whose basis strings name both tables, and the
# grammar_faces block carries the per-grammar sub-counts; every other sweep
# (sorry, axiom, unsafe, comments, imports, lines) stays single-table
# across both suffixes (the trust-surface sweep is the per-grammar
# exception, see Trust surface below).  The acceptance gate on a real .v
# tree re-derives
# the rocq face with the grep commands this tool prints on stderr
# (grep_crosscheck_commands); both spellings render from the same keyword
# tables, so the scanner and the independent check cannot drift, and no
# expected count lives in this file.
#
# Trust surface.  The third keyword family: the platform blind-spot
# switches that Print Assumptions / #print axioms can never see.  Unset
# Guard / Positivity / Universe / Elimination-Schemes Checking yields
# axiom-free terms that may still be unsound, and Lean's unsafe,
# implemented_by, extern, native_decide, Lean.ofReduceBool, partial def,
# noncomputable and debug.skipKernelTC are compiler-trust escapes outside
# the assumption closure, so a clean axiom receipt proves nothing about
# them; the trust_surface block receipts them instead.  The tables are
# per grammar and the .v face is case-sensitive: vernacular commands and
# declaration heads (Unset ..., Declare ML Module, unsafe
# def/theorem/instance, partial def, noncomputable, set_option) match at
# line start word-bounded, while tactic, attribute and path tokens
# (native_compute, vm_compute, @[implemented_by, @[extern, native_decide,
# Lean.ofReduceBool, debug.skipKernelTC) match word-bounded anywhere in a
# line; every switch basis names its own rule.  native_compute and
# vm_compute are certificate faces, not alarms: sound evaluation routes
# when the flag law holds (the compute flags the certificate was checked
# under match the flags the artifact runs under), so the flag-law reminder
# rides the basis receipt and no alarm is raised anywhere.  set_option is
# a separate broad face (every line-start set_option line) because the
# specific option payloads ride inside it.  Every table token is always
# reported, zero included: zero switches is a negative finding of this
# scan (manifest_note), never proof of a clean toolchain.
#
# Output shape.  Every top-level key except scan_face and the trust_surface
# block is {"value": ..., "basis": ...}; trust_surface itself carries
# switches (token -> value+basis), files_affected and the manifest_note
# receipt string; the basis is one ASCII line naming the counting rule, so a
# consumer quoting a number quotes its rule with it and two tools cannot
# hide different rules behind one field name.  scan_face carries the four
# fixed English fields scanned / not_scanned / negative_finding /
# equivalents, so a citation of any count carries the scan's coverage limits
# with it; all four strings are module constants pinned verbatim by the
# selftest.
#
# Determinism.  Counts, perDir totals, zeroDeclFiles, bytes, lines and
# nonEmptyLines are walk-order independent.  largest10 sorts (bytes, rel)
# tuples descending and importRoots sorts by descending count with ties kept
# in first-encounter order, both exactly as the oracle does, so a same-tree
# cross-check is equal; importRoots tie order is filesystem-walk dependent
# by construction.
#
# Fast path.  Each counted pass is gated on its pattern's required literal
# (see _pattern_count): a match necessarily contains the literal, so an
# absent literal skips the regex with the count provably unchanged, and
# clean files pay for only the few passes whose literals they carry.  The
# nonEmptyLines pass opens only when the file holds at least one
# non-whitespace byte (NONEMPTY_GATE); that byte must land on some
# splitlines segment stripped non-empty, so a closed gate proves the count
# is 0 and an open gate never changes it.

# Per-grammar declaration keyword tables (R-3b).  One table per grammar
# drives three consumers at once - the compiled byte regexes below, the
# per-file face choice inside audit_root, and the independent grep
# cross-check commands printed on stderr - so the scanner and the acceptance
# check share one keyword set and cannot drift apart.  .lean keeps the
# lowercase Lean faces; .v uses the capitalized Rocq vernacular.  Every
# declaration face is line-start anchored (re.M) and right word-bounded
# (\b), so "theorems_about" or a mid-line "Definition" never counts.
LEAN_THM_KEYWORDS = (b"theorem", b"lemma")
LEAN_DEFFAM_KEYWORDS = (b"def", b"abbrev", b"structure", b"class",
                        b"instance", b"inductive")
ROCQ_THM_KEYWORDS = (b"Theorem", b"Lemma", b"Corollary", b"Proposition")
ROCQ_DEFFAM_KEYWORDS = (b"Definition", b"Fixpoint", b"CoFixpoint",
                        b"Inductive", b"CoInductive", b"Class", b"Instance",
                        b"Abbreviation", b"Record", b"Scheme", b"Let")

# (grammar name, source suffix, keyword tables) in report and stderr order;
# SUFFIX_FACE maps each scanned suffix to its grammar and FACE_TABLES maps
# the grammar back to its tables.
GRAMMAR_FACES = (
    ("lean", ".lean", {"thm": LEAN_THM_KEYWORDS,
                       "defFam": LEAN_DEFFAM_KEYWORDS}),
    ("rocq", ".v", {"thm": ROCQ_THM_KEYWORDS,
                    "defFam": ROCQ_DEFFAM_KEYWORDS}),
)
SUFFIX_FACE = {suffix: name for name, suffix, _ in GRAMMAR_FACES}
FACE_TABLES = {name: tables for name, _, tables in GRAMMAR_FACES}

# Trust-surface switch tables (R-trust).  The third keyword family: the
# platform blind-spot switches that Print Assumptions / #print axioms can
# never see.  Each entry is (token, kind, regex core, fast-path gate
# literal, basis spelling); the token key is what the report shows while
# the rest is what the scanner compiles, so one table drives the byte
# regexes, the bases and the selftest vectors without a second copy to
# drift.  The core is the REGEX core (escapes allowed: \[ for the @[ head,
# \. for dotted paths) while the gate is the raw byte literal, so the two
# fields differ exactly where regex syntax needs escaping.  kind "line"
# anchors the core at line start (^\s*...\b, re.M) for
# vernacular commands and declaration heads; kind "word" wraps the core in
# \b...\b so tactic, attribute and path tokens count anywhere in a line;
# kind "prefix" matches a fixed @[... attribute head word-bounded on the
# right.  All faces are byte-literal and case-sensitive; comments and
# strings count too, as everywhere else in this scan.
ROCQ_TRUST_SWITCHES = (
    ("Unset Guard Checking", "line", b"Unset Guard Checking",
     b"Unset Guard Checking", "'Unset Guard Checking'"),
    ("Unset Positivity Checking", "line", b"Unset Positivity Checking",
     b"Unset Positivity Checking", "'Unset Positivity Checking'"),
    ("Unset Universe Checking", "line", b"Unset Universe Checking",
     b"Unset Universe Checking", "'Unset Universe Checking'"),
    ("Unset Elimination Schemes", "line", b"Unset Elimination Schemes",
     b"Unset Elimination Schemes", "'Unset Elimination Schemes'"),
    ("native_compute", "word", b"native_compute", b"native_compute",
     "'native_compute'"),
    ("vm_compute", "word", b"vm_compute", b"vm_compute", "'vm_compute'"),
    ("Declare ML Module", "line", b"Declare ML Module",
     b"Declare ML Module", "'Declare ML Module'"),
)
LEAN_TRUST_SWITCHES = (
    ("unsafe", "line", b"unsafe (def|theorem|instance)", b"unsafe",
     "'unsafe def|unsafe theorem|unsafe instance'"),
    ("implemented_by", "prefix", rb"@\[implemented_by",
     b"@[implemented_by", "'@[implemented_by'"),
    ("extern", "prefix", rb"@\[extern", b"@[extern", "'@[extern'"),
    ("native_decide", "word", b"native_decide", b"native_decide",
     "'native_decide'"),
    ("Lean.ofReduceBool", "word", b"Lean\\.ofReduceBool",
     b"Lean.ofReduceBool", "'Lean.ofReduceBool'"),
    ("partial def", "line", b"partial def", b"partial def",
     "'partial def'"),
    ("noncomputable", "line", b"noncomputable", b"noncomputable",
     "'noncomputable'"),
    ("debug.skipKernelTC", "word", b"debug\\.skipKernelTC",
     b"debug.skipKernelTC", "'debug.skipKernelTC'"),
    ("set_option", "line", b"set_option", b"set_option", "'set_option'"),
)
TRUST_FACES = (("rocq", ".v", ROCQ_TRUST_SWITCHES),
               ("lean", ".lean", LEAN_TRUST_SWITCHES))
TRUST_TABLES = {name: entries for name, _, entries in TRUST_FACES}
# Certificate faces: these two Rocq tactics are sound evaluation routes
# when the flag law holds, so their basis receipts provenance instead of
# raising an alarm (the flag-law reminder travels with the count, never as
# an alarm).
TRUST_CERTIFICATE_TOKENS = ("native_compute", "vm_compute")
# The receipt carried with every report: zero switches is a negative
# finding of this scan, never proof of a clean toolchain.
TRUST_MANIFEST_NOTE = ("zero switches is a negative finding of this scan,"
                       " not proof of a clean toolchain")


def _trust_rx(kind, core):
    """Compile one trust entry into its byte face per its kind rule."""
    if kind == "line":
        return re.compile(rb"^\s*" + core + rb"\b", re.M)
    if kind == "word":
        return re.compile(rb"\b" + core + rb"\b")
    return re.compile(core + rb"\b")  # prefix: fixed @[... attribute head


def _trust_basis(token, kind, spell, grammar, suffix):
    """Counting rule for one trust token: grammar + line-start/word-bound.

    Certificate faces append the flag-law receipt; set_option appends the
    broad-face note.  One ASCII line, like every basis in this report.
    """
    if kind == "line":
        rule = "line-start %s in %s files, word-bounded" % (spell, suffix)
    elif kind == "word":
        rule = ("word-bounded %s hits anywhere in a line in %s files"
                % (spell, suffix))
    else:
        rule = ("attribute prefix %s hits anywhere in a line in %s files"
                % (spell, suffix))
    text = ("%s (%s grammar, case-sensitive; comments and strings counted"
            " too)" % (rule, grammar))
    if token in TRUST_CERTIFICATE_TOKENS:
        text += ("; certificate face, not an alarm: sound when the flag law"
                 " holds (the compute flags the certificate was checked"
                 " under match the flags the artifact runs under), so a hit"
                 " is a receipt, not an unsoundness claim")
    if token == "set_option":
        text += ("; broad face: every set_option line counts, the option"
                 " payloads ride their own tokens")
    return text


TRUST_BASES = {(name, token): _trust_basis(token, kind, spell, name, suffix)
               for name, suffix, entries in TRUST_FACES
               for token, kind, _, _, spell in entries}


def _kw_alt(keywords):
    """Render a keyword table as its pipe-joined ASCII alternation."""
    return "|".join(k.decode("ascii") for k in keywords)


def _line_start_rx(keywords):
    """Compile a keyword table into its line-start, word-bounded byte face."""
    return re.compile(rb"^\s*(" + b"|".join(keywords) + rb")\b", re.M)


def _face_basis(counter, suffix, keywords):
    """Counting rule for one grammar face: its table + the line-start rule."""
    return ("line-start %s keywords in %s files: %s (word-bounded; comments"
            " and strings counted too)" % (counter, suffix, _kw_alt(keywords)))


def _cross_basis(counter):
    """Counting rule for a top-level counter; names BOTH grammar tables."""
    return ("cross-grammar total of line-start %s declarations, word-bounded,"
            " comments and strings counted too; %s"
            % (counter, "; ".join(
                "%s files: %s" % (suffix, _kw_alt(tables[counter]))
                for _, suffix, tables in GRAMMAR_FACES)))


RX = {
    "lean_thm": _line_start_rx(LEAN_THM_KEYWORDS),
    "lean_deffam": _line_start_rx(LEAN_DEFFAM_KEYWORDS),
    "rocq_thm": _line_start_rx(ROCQ_THM_KEYWORDS),
    "rocq_deffam": _line_start_rx(ROCQ_DEFFAM_KEYWORDS),
    "sorry": re.compile(rb"\bsorry\b"),
    "sorryAx": re.compile(rb"\bsorryAx\b"),
    "axiom": re.compile(rb"^\s*axiom\s", re.M),
    "opaque": re.compile(rb"^\s*opaque\s", re.M),
    "native_decide": re.compile(rb"native_decide"),
    "unsafe": re.compile(rb"^\s*unsafe\s", re.M),
    "implemented_by": re.compile(rb"@\[implemented_by"),
    "extern": re.compile(rb"@\[extern"),
    "ofReduceBool": re.compile(rb"Lean\.ofReduceBool"),
    "comment_line": re.compile(rb"^\s*--", re.M),
    "block_comment": re.compile(rb"/-"),
    "import": re.compile(rb"^\s*import\s+([A-Za-z_][\w.]*)", re.M),
}

# The trust faces compile into the same RX table, keyed by grammar and
# token so a .v file can never see a Lean switch token or vice versa.
for gname, _gsuffix, gentries in TRUST_FACES:
    for gtoken, gkind, gcore, _ggate, _gspell in gentries:
        RX["trust:" + gname + ":" + gtoken] = _trust_rx(gkind, gcore)

SOURCE_SUFFIXES = (".lean", ".v")
READ_ERROR_CAP = 10

# Gate for the non-empty-line pass: one byte outside the ASCII whitespace
# set proves a non-empty line exists; no such byte proves the count is 0.
NONEMPTY_GATE = re.compile(rb"[^\t\n\x0b\x0c\r ]")

# The four fixed scan-face strings.  They travel with every report so a
# consumer quoting any count also quotes the scan's coverage limits; the
# selftest pins all four verbatim.
SCAN_SCANNED = (
    "All files with a .lean or .v suffix under the root, walked recursively"
    " with .git directories skipped; each file is read once in binary and"
    " counted with fixed byte regexes chosen per grammar - Lean lowercase"
    " keywords in .lean, Rocq capitalized vernacular in .v - so comment and"
    " string content is counted too."
)
SCAN_NOT_SCANNED = (
    "Files with any other suffix, everything under .git, and anything a"
    " byte regex cannot see: identifier meaning, declaration structure,"
    " encodings, spellings outside each grammar's fixed keyword table;"
    " unreadable files appear only in errors."
)
SCAN_NEGATIVE_FINDING = (
    "A zero count is a negative finding of this scan, not an absolute"
    " claim."
)
SCAN_EQUIVALENTS = (
    "Declaration counts use two fixed keyword tables, each matched only at"
    " line start and word-bounded: .lean thm = theorem|lemma, defFam ="
    " def|abbrev|structure|class|instance|inductive; .v thm ="
    " Theorem|Lemma|Corollary|Proposition, defFam = Definition|Fixpoint|"
    "CoFixpoint|Inductive|CoInductive|Class|Instance|Abbreviation|Record|"
    "Scheme|Let.  Trust-surface switches are a third fixed family: .v"
    " counts Unset Guard Checking, Unset Positivity Checking, Unset Universe"
    " Checking, Unset Elimination Schemes, native_compute, vm_compute and"
    " Declare ML Module; .lean counts unsafe def/theorem/instance,"
    " @[implemented_by, @[extern, native_decide, Lean.ofReduceBool, partial"
    " def, noncomputable, debug.skipKernelTC and set_option, each under the"
    " fixed line-start or word-bounded rule its basis names.  An equivalent"
    " construct spelled outside its table, or a keyword not opening its"
    " line (attributes, Local/Global prefixes, nested bullets), is not"
    " exhaustively covered - trust-surface equivalents included, such as"
    " Local Unset, a Set re-enabling an unset check, or options scoped"
    " inside a section."
)


def _pattern_count(rx, literals, txt):
    """Regex match count gated by the pattern's required literal(s).

    A bytes literal opens the pass only when present; a tuple opens it when
    any member is present.  The gate never changes a count: no literal, no
    match, so the regex runs only on files that can match.
    """
    if isinstance(literals, bytes):
        if literals not in txt:
            return 0
    else:
        for lit in literals:
            if lit in txt:
                break
        else:
            return 0
    return len(rx.findall(txt))


def audit_root(root):
    """Scan root once in binary and return (report, rc).

    rc 2 names a non-directory root (a usage error), rc 1 marks a scan with
    read failures (each recorded in errors, loud), rc 0 a complete scan.
    """
    if not os.path.isdir(root):
        return None, 2
    files = 0
    total_bytes = 0
    total_lines = 0
    non_empty_lines = 0
    face_thm = {name: 0 for name, _, _ in GRAMMAR_FACES}
    face_deffam = {name: 0 for name, _, _ in GRAMMAR_FACES}
    decls = 0
    sorry = 0
    sorry_ax = 0
    axiom = 0
    opaque = 0
    native_decide = 0
    unsafe_files = 0
    implemented_by_files = 0
    extern_files = 0
    of_reduce_bool_files = 0
    trust_hits = {token: 0
                  for _, _, entries in TRUST_FACES
                  for token, _, _, _, _ in entries}
    trust_files = 0
    comment_lines = 0
    block_comment_files = 0
    zero_decl_files = 0
    per_dir = {}
    largest = []
    imports = {}
    errors = []
    for r, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fn in names:
            if not fn.endswith(SOURCE_SUFFIXES):
                continue
            path = os.path.join(r, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, "rb") as fh:
                    txt = fh.read()
            except OSError as exc:
                errors.append("read %s: %s" % (rel, exc))
                continue
            top = rel.split("/")[0]
            bucket = per_dir.setdefault(top, {"files": 0, "decls": 0,
                                              "bytes": 0})
            bucket["files"] += 1
            bucket["bytes"] += len(txt)
            files += 1
            total_bytes += len(txt)
            total_lines += txt.count(b"\n")
            if NONEMPTY_GATE.search(txt):
                non_empty_lines += sum(1 for ln in txt.splitlines()
                                       if ln.strip())
            largest.append((len(txt), rel))
            # R-3b: the declaration face is chosen per source suffix - the
            # capitalized Rocq vernacular keywords for .v, the lowercase
            # Lean keywords for .lean - so a lowercase Lean keyword inside
            # a .v file (or a capitalized vernacular keyword inside a .lean
            # file) can never count.  Every other sweep below stays
            # single-table across both grammars.
            grammar = SUFFIX_FACE[".v" if fn.endswith(".v") else ".lean"]
            tables = FACE_TABLES[grammar]
            n_thm = _pattern_count(RX[grammar + "_thm"], tables["thm"], txt)
            n_deffam = _pattern_count(RX[grammar + "_deffam"],
                                      tables["defFam"], txt)
            face_thm[grammar] += n_thm
            face_deffam[grammar] += n_deffam
            n_decl = n_thm + n_deffam
            decls += n_decl
            bucket["decls"] += n_decl
            comment_lines += _pattern_count(RX["comment_line"], b"--", txt)
            sorry += _pattern_count(RX["sorry"], b"sorry", txt)
            sorry_ax += _pattern_count(RX["sorryAx"], b"sorryAx", txt)
            axiom += _pattern_count(RX["axiom"], b"axiom", txt)
            opaque += _pattern_count(RX["opaque"], b"opaque", txt)
            native_decide += _pattern_count(RX["native_decide"],
                                            b"native_decide", txt)
            if _pattern_count(RX["unsafe"], b"unsafe", txt):
                unsafe_files += 1
            if _pattern_count(RX["implemented_by"], b"@[implemented_by",
                              txt):
                implemented_by_files += 1
            if _pattern_count(RX["extern"], b"@[extern", txt):
                extern_files += 1
            if _pattern_count(RX["ofReduceBool"], b"ofReduceBool", txt):
                of_reduce_bool_files += 1
            # R-trust: the per-grammar trust-surface face.  Only the
            # file's own grammar table runs, so a Lean switch string
            # inside a .v file (or a Rocq switch inside a .lean file)
            # can never count - the same suffix gate as the decl faces.
            saw_trust = False
            for tok, _kind, _core, gate, _spell in TRUST_TABLES[grammar]:
                n_trust = _pattern_count(
                    RX["trust:" + grammar + ":" + tok], gate, txt)
                if n_trust:
                    trust_hits[tok] += n_trust
                    saw_trust = True
            if saw_trust:
                trust_files += 1
            if _pattern_count(RX["block_comment"], b"/-", txt):
                block_comment_files += 1
            if n_decl == 0:
                zero_decl_files += 1
            if _pattern_count(RX["import"], b"import", txt):
                for m in RX["import"].findall(txt):
                    r0 = m.split(b".")[0].decode("ascii", "replace")
                    imports[r0] = imports.get(r0, 0) + 1
    thm_total = sum(face_thm.values())
    deffam_total = sum(face_deffam.values())
    face_counts = {"thm": face_thm, "defFam": face_deffam}
    largest.sort(reverse=True)
    report = {
        "files": {"value": files,
                  "basis": ".lean and .v files under the root; .git trees"
                           " are skipped"},
        "bytes": {"value": total_bytes,
                  "basis": "raw byte totals of the scanned files, binary"
                           " read"},
        "lines": {"value": total_lines,
                  "basis": "LF-terminated lines, binary read (LF byte"
                           " count)"},
        "nonEmptyLines": {"value": non_empty_lines,
                          "basis": "lines carrying at least one"
                                   " non-whitespace byte (splitlines, then"
                                   " strip)"},
        "thm": {"value": thm_total, "basis": _cross_basis("thm")},
        "defFam": {"value": deffam_total, "basis": _cross_basis("defFam")},
        "decls": {"value": decls,
                  "basis": "combined total thm + defFam summed across both"
                           " grammar faces (backward anchor)"},
        "grammar_faces": {
            "value": {
                name: {counter: {
                    "value": face_counts[counter][name],
                    "basis": _face_basis(counter, suffix, tables[counter]),
                } for counter in ("thm", "defFam")}
                for name, suffix, tables in GRAMMAR_FACES},
            "basis": "per-grammar declaration sub-counts; thm and defFam"
                     " above are the sums of the matching sub-counters, and"
                     " each sub-counter names its own keyword table",
        },
        "sorry": {"value": sorry,
                  "basis": "word-bounded 'sorry' token hits, comments and"
                           " strings included"},
        "sorryAx": {"value": sorry_ax,
                    "basis": "word-bounded 'sorryAx' token hits, comments"
                             " and strings included"},
        "axiom": {"value": axiom,
                  "basis": "'axiom ' declarations at line start"},
        "opaque": {"value": opaque,
                   "basis": "'opaque ' declarations at line start"},
        "native_decide": {"value": native_decide,
                          "basis": "bare 'native_decide' substring hits"},
        "unsafe": {"value": unsafe_files,
                   "basis": "files with at least one line starting with"
                            " 'unsafe '"},
        "implemented_by": {"value": implemented_by_files,
                           "basis": "files containing '@[implemented_by'"},
        "extern": {"value": extern_files,
                   "basis": "files containing '@[extern'"},
        "ofReduceBool": {"value": of_reduce_bool_files,
                         "basis": "files containing 'Lean.ofReduceBool'"},
        "trust_surface": {
            "switches": {token: {"value": trust_hits[token],
                                 "basis": TRUST_BASES[(name, token)]}
                         for name, _, entries in TRUST_FACES
                         for token, _, _, _, _ in entries},
            "files_affected": {"value": trust_files,
                               "basis": "distinct files carrying at least"
                                        " one switch hit"},
            "manifest_note": TRUST_MANIFEST_NOTE,
        },
        "commentLines": {"value": comment_lines,
                         "basis": "lines whose first non-space text starts"
                                  " with '--'"},
        "blockCommentFiles": {"value": block_comment_files,
                              "basis": "files containing the '/-'"
                                       " block-comment opener"},
        "perDir": {"value": per_dir,
                   "basis": "first path segment -> {files, decls, bytes};"
                                " decls is the thm + defFam face under the"
                                " file's own grammar"},
        "largest10": {"value": [{"path": rel, "bytes": n}
                                for n, rel in largest[:10]],
                      "basis": "top 10 files by raw bytes, descending;"
                               " ties break by path, descending"},
        "zeroDeclFiles": {"value": zero_decl_files,
                          "basis": "files with zero thm and zero defFam"
                                   " line-start hits under their own"
                                   " grammar face"},
        "importRoots": {"value": [[r0, n] for r0, n in
                                  sorted(imports.items(),
                                         key=lambda kv: -kv[1])[:10]],
                        "basis": "top 10 first segments of import targets"
                                 " by count; ties keep first-encounter"
                                 " order"},
        "root": {"value": root,
                 "basis": "the audit root as given; scanned literally, no"
                          " src/ descent"},
        "errors": {"value": errors[:READ_ERROR_CAP],
                   "basis": "first 10 read failures, each 'read <relative"
                            " path>: <reason>'"},
        "errorCount": {"value": len(errors),
                       "basis": "total files that failed to read; errors"
                                " is capped at 10"},
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    return report, (1 if errors else 0)


def write_json(path, payload):
    """Write the stdout payload (plus one newline) to path as UTF-8 text."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def grep_crosscheck_commands(root):
    """Render the independent grep cross-check commands for the audit root.

    The acceptance gate re-derives every grammar face with these commands
    and compares them field-for-field with the grammar_faces block; each
    pattern is rendered from the same keyword table the scanner compiles,
    so no expected count and no duplicated keyword set lives in this file.
    Each command mirrors its face exactly: -E extended regex, the leading
    ^[[:space:]]* mirrors the regex's ^\\s*, GNU grep's \\b mirrors the
    word boundary, -r walks the tree, --exclude-dir=.git matches the
    scanner's .git skip, and --include confines the command to the
    grammar's suffix, mirroring the suffix gate; LC_ALL=C keeps the reading
    byte-literal, and -o|wc -l counts one line per match exactly like the
    scanner's non-overlapping findall (a match in either spelling must end
    at the same word-bounded keyword occurrence, so the counts are 1:1).
    Returns (label, command) pairs; nothing is executed here.
    """
    commands = []
    for name, suffix, tables in GRAMMAR_FACES:
        for counter in ("thm", "defFam"):
            pattern = "^[[:space:]]*(%s)\\b" % _kw_alt(tables[counter])
            commands.append((
                "%s/%s" % (name, counter),
                "LC_ALL=C grep -rhoE --include=%s --exclude-dir=.git -e %s"
                " %s | wc -l" % (shlex.quote("*" + suffix),
                                 shlex.quote(pattern),
                                 shlex.quote(root))))
    return commands


def run_selftest():
    """Fixture vectors over temporary directories; 0 green, 1 red."""
    fails = []

    def check(name, ok, detail=""):
        if ok:
            print("[PASS] %s" % name)
        else:
            fails.append(name)
            print("[FAIL] %s %s" % (name, detail))

    tmp = tempfile.mkdtemp(prefix="tree_audit_selftest_")
    try:
        a_enc = FIXTURE_ALPHA.encode("utf-8")
        b_enc = FIXTURE_BETA.encode("utf-8")
        g_enc = FIXTURE_GAMMA.encode("utf-8")
        d_enc = FIXTURE_DELTA.encode("utf-8")
        e_enc = FIXTURE_EPSILON.encode("utf-8")
        os.mkdir(os.path.join(tmp, "sub"))
        with open(os.path.join(tmp, "alpha.v"), "wb") as fh:
            fh.write(a_enc)
        with open(os.path.join(tmp, "beta.v"), "wb") as fh:
            fh.write(b_enc)
        with open(os.path.join(tmp, "delta.v"), "wb") as fh:
            fh.write(d_enc)
        with open(os.path.join(tmp, "epsilon.v"), "wb") as fh:
            fh.write(e_enc)
        with open(os.path.join(tmp, "sub", "gamma.lean"), "wb") as fh:
            fh.write(g_enc)
        os.mkdir(os.path.join(tmp, ".git"))
        with open(os.path.join(tmp, ".git", "decoy.v"), "wb") as fh:
            fh.write(b"theorem decoy : Nat := 0\nsorry\n")
        with open(os.path.join(tmp, "notes.txt"), "wb") as fh:
            fh.write(b"sorry\ntheorem decoy : Nat := 0\n")
        report, rc = audit_root(tmp)
        check("scan-rc", rc == 0, "rc=%s" % rc)
        check("files", report["files"]["value"] == 5,
              "got %s" % report["files"]["value"])
        check("bytes", report["bytes"]["value"] ==
              len(a_enc) + len(b_enc) + len(g_enc) + len(d_enc) + len(e_enc),
              "got %s" % report["bytes"]["value"])
        # Hand-derived line totals: alpha 27 (25 non-empty: one blank, one
        # whitespace-only), beta 3, delta 9, epsilon 5, gamma 9 - all new
        # trust lines are non-empty, so 53 lines / 51 non-empty.
        check("lines", report["lines"]["value"] == 53,
              "got %s" % report["lines"]["value"])
        check("nonEmptyLines", report["nonEmptyLines"]["value"] == 51,
              "got %s" % report["nonEmptyLines"]["value"])
        # R-3b cross-grammar totals: lean carries only gamma.lean (2 thm,
        # 1 defFam) and rocq carries only delta.v (4 thm, 3 defFam);
        # alpha.v's lowercase Lean keywords contribute zero to both faces,
        # which is the no-leak guard for the suffix gate.
        check("thm", report["thm"]["value"] == 6,
              "got %s" % report["thm"]["value"])
        check("defFam", report["defFam"]["value"] == 4,
              "got %s" % report["defFam"]["value"])
        check("decls", report["decls"]["value"] == 10,
              "got %s" % report["decls"]["value"])
        check("decls-combined", report["decls"]["value"] ==
              report["thm"]["value"] + report["defFam"]["value"],
              "thm=%s defFam=%s decls=%s" % (report["thm"]["value"],
                                             report["defFam"]["value"],
                                             report["decls"]["value"]))
        # R-3b grammar_faces vectors: the capitalized .v fixture asserted
        # through the rocq face (3 Theorem + 1 Corollary = 4 thm; 2
        # Definition + 1 Inductive = 3 defFam), the .lean vectors unchanged
        # through the lean face, the schema shape (every counter carries
        # value + basis), the sum identity and basis strings naming BOTH
        # grammars.
        gf = report["grammar_faces"]["value"]
        check("grammar-face-keys",
              sorted(gf) == ["lean", "rocq"]
              and sorted(gf["lean"]) == ["defFam", "thm"]
              and sorted(gf["rocq"]) == ["defFam", "thm"],
              "got %s" % sorted(gf))
        check("rocq-thm-face", gf["rocq"]["thm"]["value"] == 4,
              "got %s" % gf["rocq"]["thm"]["value"])
        check("rocq-defFam-face", gf["rocq"]["defFam"]["value"] == 3,
              "got %s" % gf["rocq"]["defFam"]["value"])
        check("lean-thm-face", gf["lean"]["thm"]["value"] == 2,
              "got %s" % gf["lean"]["thm"]["value"])
        check("lean-defFam-face", gf["lean"]["defFam"]["value"] == 1,
              "got %s" % gf["lean"]["defFam"]["value"])
        gf_bad = [name + "/" + counter for name in gf
                  for counter in gf[name]
                  if sorted(gf[name][counter]) != ["basis", "value"]
                  or not isinstance(gf[name][counter]["value"], int)
                  or not (isinstance(gf[name][counter]["basis"], str)
                          and gf[name][counter]["basis"])]
        check("grammar-face-shape", gf_bad == [], "bad: %s" % gf_bad)
        check("grammar-sums",
              report["thm"]["value"] == gf["lean"]["thm"]["value"]
              + gf["rocq"]["thm"]["value"]
              and report["defFam"]["value"] == gf["lean"]["defFam"]["value"]
              + gf["rocq"]["defFam"]["value"],
              "thm=%s defFam=%s" % (report["thm"]["value"],
                                    report["defFam"]["value"]))
        check("thm-basis-names-both",
              "theorem" in report["thm"]["basis"]
              and "Theorem" in report["thm"]["basis"]
              and ".lean" in report["thm"]["basis"]
              and ".v" in report["thm"]["basis"],
              "got %s" % report["thm"]["basis"])
        check("defFam-basis-names-both",
              "abbrev" in report["defFam"]["basis"]
              and "Fixpoint" in report["defFam"]["basis"]
              and ".lean" in report["defFam"]["basis"]
              and ".v" in report["defFam"]["basis"],
              "got %s" % report["defFam"]["basis"])
        check("sorry", report["sorry"]["value"] == 3,
              "got %s" % report["sorry"]["value"])
        check("sorryAx", report["sorryAx"]["value"] == 2,
              "got %s" % report["sorryAx"]["value"])
        check("axiom", report["axiom"]["value"] == 1,
              "got %s" % report["axiom"]["value"])
        check("opaque", report["opaque"]["value"] == 1,
              "got %s" % report["opaque"]["value"])
        # gamma's trust lines move the cross-grammar legacy sweeps: one
        # more bare native_decide token (alpha 2 + gamma 1), one more
        # line-start 'unsafe ' file and one more '@[implemented_by' file.
        check("native_decide", report["native_decide"]["value"] == 3,
              "got %s" % report["native_decide"]["value"])
        check("unsafe", report["unsafe"]["value"] == 2,
              "got %s" % report["unsafe"]["value"])
        check("implemented_by", report["implemented_by"]["value"] == 2,
              "got %s" % report["implemented_by"]["value"])
        check("extern", report["extern"]["value"] == 1,
              "got %s" % report["extern"]["value"])
        check("ofReduceBool", report["ofReduceBool"]["value"] == 1,
              "got %s" % report["ofReduceBool"]["value"])
        # R-trust vectors: the trust-surface block.  epsilon.v carries one
        # line-start Unset Guard Checking plus one mid-line native_compute
        # ("now native_compute." proves the word-bound rule, not
        # line-start); gamma.lean carries unsafe def, @[implemented_by,
        # bare native_decide and one set_option line.  alpha.v carries the
        # same Lean switch strings but rides the rocq table, so the exact
        # counts below double as the trust no-leak guard for the suffix
        # gate (a leak would push unsafe/native_decide/implemented_by
        # above these numbers).
        ts = report["trust_surface"]
        check("trust-shape",
              sorted(ts) == ["files_affected", "manifest_note", "switches"],
              "got %s" % sorted(ts))
        expect_trust = {
            "Unset Guard Checking": 1, "Unset Positivity Checking": 0,
            "Unset Universe Checking": 0, "Unset Elimination Schemes": 0,
            "native_compute": 1, "vm_compute": 0, "Declare ML Module": 0,
            "unsafe": 1, "implemented_by": 1, "extern": 0,
            "native_decide": 1, "Lean.ofReduceBool": 0, "partial def": 0,
            "noncomputable": 0, "debug.skipKernelTC": 0, "set_option": 1,
        }
        trust_tokens = [tok for _, _, entries in TRUST_FACES
                        for tok, _, _, _, _ in entries]
        check("trust-token-keys",
              len(trust_tokens) == len(set(trust_tokens))
              and sorted(ts["switches"]) == sorted(expect_trust),
              "got %s" % sorted(ts["switches"]))
        got_trust = {t: v["value"] for t, v in ts["switches"].items()}
        check("trust-counts", got_trust == expect_trust,
              "got %s" % got_trust)
        ts_bad = [t for t, v in ts["switches"].items()
                  if sorted(v) != ["basis", "value"]
                  or not isinstance(v["value"], int)
                  or not (isinstance(v["basis"], str) and v["basis"])]
        check("trust-switch-shape", ts_bad == [], "bad: %s" % ts_bad)
        check("trust-files-shape",
              sorted(ts["files_affected"]) == ["basis", "value"],
              "got %s" % sorted(ts["files_affected"]))
        check("trust-files-affected", ts["files_affected"]["value"] == 2,
              "got %s" % ts["files_affected"]["value"])
        check("trust-manifest-note",
              ts["manifest_note"] == TRUST_MANIFEST_NOTE,
              "got %s" % ts["manifest_note"])
        trust_grammar = {tok: name
                         for name, _, entries in TRUST_FACES
                         for tok, _, _, _, _ in entries}
        trust_suffix = {"rocq": ".v", "lean": ".lean"}
        ts_basis = [t for t in ts["switches"]
                    if trust_suffix[trust_grammar[t]]
                    not in ts["switches"][t]["basis"]]
        check("trust-basis-grammar", ts_basis == [], "bad: %s" % ts_basis)
        check("trust-certificate-basis",
              all("certificate face" in ts["switches"][t]["basis"]
                  and "flag law" in ts["switches"][t]["basis"]
                  for t in TRUST_CERTIFICATE_TOKENS),
              "got %s / %s" % (ts["switches"]["native_compute"]["basis"],
                               ts["switches"]["vm_compute"]["basis"]))
        check("trust-setoption-broad",
              "broad face" in ts["switches"]["set_option"]["basis"],
              "got %s" % ts["switches"]["set_option"]["basis"])
        # epsilon.v adds one comment line: 6 -> 7.
        check("commentLines", report["commentLines"]["value"] == 7,
              "got %s" % report["commentLines"]["value"])
        check("blockCommentFiles", report["blockCommentFiles"]["value"] == 1,
              "got %s" % report["blockCommentFiles"]["value"])
        check("zeroDeclFiles", report["zeroDeclFiles"]["value"] == 3,
              "got %s" % report["zeroDeclFiles"]["value"])
        # The .git skip and the suffix filter are proven by the totals
        # above: the .git decoy would add one thm hit and one sorry token,
        # notes.txt one sorry token and one thm hit; both stay out of
        # every count.  alpha.v, beta.v and epsilon.v are the three
        # zero-decl files: alpha.v's lowercase Lean keywords do not count
        # under the rocq face (R-3b), exactly the undercount face the dual
        # grammar removes, and epsilon.v's trust lines are no declarations.
        # Shape: every top-level key but scan_face and the trust_surface
        # block carries value + basis; scan_face carries exactly the four
        # fixed fields, verbatim.
        bare = [k for k in report
                if k not in ("scan_face", "trust_surface")
                and not (isinstance(report[k], dict)
                         and "value" in report[k]
                         and "basis" in report[k])]
        check("value-basis-shape", bare == [], "bare keys: %s" % bare)
        face = report["scan_face"]
        check("scan-face-fields",
              sorted(face) == ["equivalents", "negative_finding",
                               "not_scanned", "scanned"],
              "got %s" % sorted(face))
        check("scan-face-verbatim",
              face.get("scanned") == SCAN_SCANNED
              and face.get("not_scanned") == SCAN_NOT_SCANNED
              and face.get("negative_finding") == SCAN_NEGATIVE_FINDING
              and face.get("equivalents") == SCAN_EQUIVALENTS,
              "scan_face strings drifted from the constants")
        per_dir = report["perDir"]["value"]
        check("perDir-keys",
              set(per_dir) == {"alpha.v", "beta.v", "delta.v", "epsilon.v",
                               "sub"},
              "got %s" % sorted(per_dir))
        check("perDir-alpha", per_dir.get("alpha.v") == {
            "files": 1, "decls": 0, "bytes": len(a_enc)},
            "got %s" % per_dir.get("alpha.v"))
        check("perDir-beta", per_dir.get("beta.v") == {
            "files": 1, "decls": 0, "bytes": len(b_enc)},
            "got %s" % per_dir.get("beta.v"))
        check("perDir-delta", per_dir.get("delta.v") == {
            "files": 1, "decls": 7, "bytes": len(d_enc)},
            "got %s" % per_dir.get("delta.v"))
        check("perDir-epsilon", per_dir.get("epsilon.v") == {
            "files": 1, "decls": 0, "bytes": len(e_enc)},
            "got %s" % per_dir.get("epsilon.v"))
        check("perDir-sub", per_dir.get("sub") == {
            "files": 1, "decls": 3, "bytes": len(g_enc)},
            "got %s" % per_dir.get("sub"))
        largest = report["largest10"]["value"]
        check("largest10-count", len(largest) == 5, "got %s" % len(largest))
        check("largest10-top", largest[0] == {"path": "alpha.v",
                                              "bytes": len(a_enc)},
              "got %s" % largest[0])
        imports = dict(report["importRoots"]["value"])
        check("importRoots", imports == {"Mathlib": 2, "Batteries": 1,
                                         "Init": 1} and len(imports) == 3,
              "got %s" % report["importRoots"]["value"])
        check("errors", report["errors"]["value"] == []
              and report["errorCount"]["value"] == 0,
              "got %s / %s" % (report["errors"]["value"],
                               report["errorCount"]["value"]))
        check("root-field", report["root"]["value"] == tmp,
              "got %s" % report["root"]["value"])
        # --json round trip: the file payload parses back to the report.
        json_path = os.path.join(tmp, "out.json")
        payload = json.dumps(report, ensure_ascii=False)
        write_json(json_path, payload)
        with open(json_path, "r", encoding="utf-8") as fh:
            round_trip = json.load(fh)
        check("json-round-trip", round_trip == report, "payload mismatch")
        # The printed independent-grep commands must carry the same keyword
        # tables as the scanner (string-built here, never executed).
        cmds = dict(grep_crosscheck_commands(tmp))
        check("grep-command-keys",
              sorted(cmds) == ["lean/defFam", "lean/thm", "rocq/defFam",
                               "rocq/thm"],
              "got %s" % sorted(cmds))
        check("grep-command-rocq",
              "--include='*.v'" in cmds.get("rocq/thm", "")
              and "Theorem|Lemma|Corollary|Proposition"
              in cmds.get("rocq/thm", "")
              and "\\b" in cmds.get("rocq/thm", ""),
              "got %s" % cmds.get("rocq/thm"))
        check("grep-command-lean",
              "--include='*.lean'" in cmds.get("lean/thm", "")
              and "theorem|lemma" in cmds.get("lean/thm", ""),
              "got %s" % cmds.get("lean/thm"))
        # Empty tree face: zero files, still green.
        empty = tempfile.mkdtemp(prefix="tree_audit_selftest_empty_")
        try:
            report2, rc2 = audit_root(empty)
            check("empty-rc", rc2 == 0
                  and report2["files"]["value"] == 0,
                  "rc=%s files=%s" % (rc2, report2["files"]["value"]))
            # Zero-switch negative-finding shape: every table token still
            # reported, all at 0, files_affected 0, manifest_note verbatim
            # - the zeros are this scan's negative finding, not a clean
            # toolchain proof.
            ts2 = report2["trust_surface"]
            check("empty-trust-zero-shape",
                  len(ts2["switches"]) == len(expect_trust)
                  and all(v["value"] == 0
                          for v in ts2["switches"].values())
                  and ts2["files_affected"]["value"] == 0
                  and ts2["manifest_note"] == TRUST_MANIFEST_NOTE,
                  "switches=%s files_affected=%s"
                  % ({t: v["value"] for t, v in ts2["switches"].items()},
                     ts2["files_affected"]["value"]))
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        # Missing root face: rc 2, loud.
        missing = os.path.join(tmp, "no-such-dir")
        report3, rc3 = audit_root(missing)
        check("missing-root-rc", rc3 == 2 and report3 is None,
              "rc=%s report=%s" % (rc3, report3))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        print("[SELFTEST] tree_audit red: %d vector(s) failed: %s"
              % (len(fails), ", ".join(fails)))
        return 1
    print("[SELFTEST] tree_audit green: all vectors pass")
    return 0


FIXTURE_ALPHA = (
    "-- alpha fixture header comment\n"
    "theorem alpha_one : Nat := 1\n"
    "def alpha_two : Nat := 2\n"
    "-- mentions sorry inside a comment (raw-scan sense)\n"
    "axiom alpha_ax : Prop\n"
    "opaque alpha_op : Nat := 3\n"
    "instance alpha_inst : Inhabited Nat where default := 0\n"
    "abbrev alpha_ab : Nat := 7\n"
    "@[implemented_by alpha_two] def alpha_attr : Nat := 8\n"
    '@[extern "alpha_e"] def alpha_ext : Nat := 9\n'
    "unsafe def alpha_u : Nat := 10\n"
    "sorry\n"
    "sorry\n"
    "sorryAx\n"
    "native_decide\n"
    "Lean.ofReduceBool\n"
    "import Mathlib.Data.Set\n"
    "import Batteries.Tactic\n"
    "/- block comment\n"
    "-- inside a block comment still lands on the line count\n"
    "-/\n"
    "native_decide\n"
    "structure alpha_st where\n"
    "class alpha_cl where\n"
    "inductive alpha_in | tag\n"
    "\n"
    "   \n"
)

FIXTURE_BETA = (
    "-- beta fixture: a declaration-free face\n"
    "import Mathlib.Data.Set\n"
    "prose mentions sorryAx without a declaration\n"
)

# gamma.lean: the .lean face plus the lean trust-surface hits - 2 thm and
# 1 defFam line starts as before, then one unsafe def, one @[implemented_by
# attribute, one bare native_decide and one set_option line, giving the
# four nonzero lean trust tokens (extern, Lean.ofReduceBool, partial def,
# noncomputable and debug.skipKernelTC stay at zero).
FIXTURE_GAMMA = (
    "-- gamma fixture: the .lean face\n"
    "theorem gamma_one : Nat := 1\n"
    "lemma gamma_two : Nat := 2\n"
    "def gamma_three : Nat := 3\n"
    "import Init\n"
    "unsafe def gamma_unsafe : Nat := 9\n"
    "@[implemented_by gamma_three] def gamma_impl : Nat := 10\n"
    "native_decide\n"
    "set_option maxHeartbeats 4000 in\n"
)

# delta.v: the capitalized Rocq vernacular face (R-3b).  Hand-derived
# counts: 4 thm-family line starts (3 Theorem + 1 Corollary) and 3
# defFam-family line starts (2 Definition + 1 Inductive); the "Local
# Theorem" line opens with the prefix, not the keyword, so the line-start
# limitation correctly leaves it uncounted.
FIXTURE_DELTA = (
    "-- delta fixture: the Rocq vernacular face (.v)\n"
    "Theorem delta_one : nat.\n"
    "Theorem delta_two : nat.\n"
    "Theorem delta_three : nat.\n"
    "Corollary delta_four : nat.\n"
    "Local Theorem delta_hidden : nat.\n"
    "Definition delta_five : nat := 5.\n"
    "Definition delta_six : nat := 6.\n"
    "Inductive delta_seven : Type := tag.\n"
)

# epsilon.v: the trust-surface rocq face.  Hand-derived: one line-start
# "Unset Guard Checking" and one mid-line native_compute (inside
# "now native_compute.", proving the word-bound-anywhere rule, not
# line-start); no thm/defFam keyword opens a line, so the declaration
# faces stay untouched, and vm_compute / Declare ML Module stay at zero.
FIXTURE_EPSILON = (
    "-- epsilon fixture: the trust-surface face (.v)\n"
    "Unset Guard Checking.\n"
    "Proof.\n"
    "now native_compute.\n"
    "Qed.\n"
)


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2)."""
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="read-only tree health audit over .lean/.v source trees"
                    " (one JSON line)")
    ap.add_argument("--root", metavar="DIR",
                    help="the audit root (scanned literally; .git skipped)")
    ap.add_argument("--json", metavar="OUT",
                    help="write the stdout JSON payload to OUT as well")
    ap.add_argument("--selftest", action="store_true",
                    help="run the fixture vectors on temporary directories")
    args = ap.parse_args(argv)
    if args.selftest:
        if args.root or args.json:
            ap.error("--selftest runs standalone; combine it with no scan"
                     " flags")
        return run_selftest()
    if not args.root:
        ap.error("--root is required unless --selftest is given")
    report, rc = audit_root(args.root)
    if rc == 2:
        sys.stderr.write("tree_audit: --root is not a directory: %s\n"
                         % args.root)
        return 2
    # Acceptance-gate face (R-3b): print the independent grep commands so
    # the gate can re-derive every grammar face with the SAME keyword
    # tables the scanner compiled; the commands carry no expected counts.
    for label, cmd in grep_crosscheck_commands(args.root):
        sys.stderr.write("tree_audit grep-crosscheck %s: %s\n"
                         % (label, cmd))
    payload = json.dumps(report, ensure_ascii=False)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(payload)
    if args.json:
        try:
            write_json(args.json, payload)
        except OSError as exc:
            sys.stderr.write("tree_audit: --json write failed: %s\n" % exc)
            return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
