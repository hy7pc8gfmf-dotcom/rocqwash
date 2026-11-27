#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lean_axiom_sweep.py - per-theorem axiom-closure classifier for Lean claim audits.
Purpose.  Make "0 sorry 0 axiom" claims mechanically reproducible per
  theorem: each declaration of the target .lean file(s) is probed with
  `#print axioms <decl>` via the copy-append form (private temp checker
  copy, one appended probe line per declaration) and classified CLEAN /
  BENIGN-STANDARD / SORRY-ALARM / CUSTOM-AXIOM-ALARM / PRIVATE-COVERED /
  UNPARSED (honest); the class definitions and the enumeration, probe,
  gate, and pin detail live in the detail block below the header.
Interface.  python -I tools/lean_axiom_sweep.py --root <file|dir>
  [--json OUT] [--allow-axiom NAME]... [--timeout SEC] [--snapshot OUT]
  [--baseline SNAPSHOT] | --toolchain-doctor --root <file|dir> |
  --selftest; stdout carries one JSON line (rocqwash-axiom-sweep/1).
Dependencies.  Python 3 standard library only; the probe face needs a
  usable Lean 4 toolchain (lean or lake on PATH passing a version probe),
  never downloaded or simulated; without one the sweep exits 112; a
  pinned toolchain must be in the elan installed list.
Evidence.  --selftest frozen offline vectors across parse, classify,
  emission, name-keyed parse, failure isolation, snapshot/diff, and pin
  faces; the full enumeration is in the detail block.
Exit-codes.  0 green; 1 red (any alarm, UNPARSED row, or recorded
  error); 2 usage error; 112 no usable toolchain or unhonored pin; the
  per-case detail is in the detail block.
"""

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Former-header detail (carried out of the header on the RIS-12 budget
# cure, verbatim in substance):
# Interface.  --json additionally writes the same payload to OUT;
#   --snapshot additionally writes a machine closure snapshot (schema
#   rocqwash-axiom-closure-snapshot/1, deterministic); --baseline diffs
#   the current closure against a previous snapshot into the
#   closure_diff block; --toolchain-doctor prints the standalone
#   toolchain resolution-chain report (schema
#   rocqwash-toolchain-doctor/1) and exits 0 always; --selftest runs the
#   frozen offline vectors and exits.
# Dependencies.  An elan shim without a default toolchain does not pass
#   the version probe; when the target pins a toolchain (a
#   lean-toolchain file), the pin must be in the elan installed list
#   (`elan toolchain list`) for the sweep to run at all; the snapshot and
#   diff faces are toolchain-independent: the diff reads only the two
#   snapshot files' data, no Lean involvement.
# Purpose detail.  The checker runs in the target's own lake environment
#   (`lake env lean`) or against a direct lean binary.  Class
#   definitions: BENIGN-STANDARD = subset of propext, Classical.choice,
#   Quot.sound; SORRY-ALARM = sorryAx; CUSTOM-AXIOM-ALARM = any other
#   name, verbatim; PRIVATE-COVERED = a private declaration successfully
#   probed via the copy-append form, its axiom closure counts normally
#   toward the verdict, it is not a pass-by-absence.
# Evidence.  --selftest covers the parse and classify faces with canned
#   `#print axioms` fixtures for all six classes, the copy-append emission
#   face (checker text plus the emitted probe list the parse name-maps),
#   the name-keyed parse face (exact-name attribution under deliberately
#   wrong probe line numbers, a missing block leaving exactly its own row
#   UNPARSED no cascade, the mangled-private unique-suffix fallback and
#   its ambiguity refusal, double-run byte-identical), the per-probe
#   failure-isolation face (a failed or unresolved probe leaves ONLY its
#   own declaration UNPARSED, no sibling cascade), a private- plus
#   public-declaration fixture probed offline into PRIVATE-COVERED with
#   its axiom set, the report shape (every counter wrapped {value, basis},
#   scan_face four fields), the import-form checker emission and
#   module-derivation faces, the gate vector (child PATH stripped -> rc
#   112), the closure faces (snapshot determinism double-run
#   byte-identical, all four diff verdict kinds, diff_alarm true and
#   false, NEW-DEPENDENCY, baseline load error faces, the no-baseline
#   backward-compat shape), and the toolchain pin faces (upward pin
#   discovery nearest-wins, empty-pin refusal, elan list parse with
#   annotations stripped, pin membership decision, version token parses,
#   probe env injection and no-pin passthrough, toolchain-block
#   pin/target_pin/match fields, doctor payload shape over all four
#   verdicts, the pin-skip spawn face rc 112 with the doctor block and
#   the exact install command on a stripped environment, the doctor face
#   exit 0, and the doctor usage-conflict faces); zero network, zero
#   toolchain launch, zero real-repo touch.
# Exit-codes.  0 green (every classified declaration CLEAN,
#   BENIGN-STANDARD or PRIVATE-COVERED, zero UNPARSED rows, zero errors;
#   also the --toolchain-doctor diagnostic face, always); 1 red (any
#   SORRY-ALARM, CUSTOM-AXIOM-ALARM or UNPARSED row, or any recorded
#   error: unjudgeable is not green; unchanged by the diff face -
#   diff_alarm rides the payload); 2 usage error (including an unreadable
#   or wrong-schema --baseline, and --toolchain-doctor combined with scan
#   flags); 112 no usable Lean toolchain (the honest skip names the
#   requirement), or the target lean-toolchain pin cannot be honored (not
#   in the elan installed list, or the pin unreadable, or the installed
#   list unavailable: running the unverified PATH default would be the
#   toolchain drift this gate exists to prevent; the pin-skip face
#   upgrades the output with a doctor block on stdout naming the exact
#   install command); the axiom_guard rc 111 env-gate precedent family,
#   code 112 per this tool's contract.
#
# Declaration enumeration.  Byte-literal line-start regex face: optional
# Lean 4 prefix modifiers (private/protected/noncomputable/unsafe/partial/
# local/global/export) sharing the line, then theorem|lemma|def, then the
# name (ASCII identifiers with apostrophes; quoted «...» and unicode
# spellings are outside the face and surface as absence, not guesses).
# The captured modifier prefix is scanned token-wise for `private`, so a
# private declaration is flagged at enumeration time (this drives the
# PRIVATE-COVERED class: private names are invisible to import-based
# probes, the Euler pilot blind spot).  A line-start namespace/section/end
# stack builds the full probe name (namespace pushes its name, section
# pushes an empty frame, end pops one); section/variable scoping inside a
# namespace is not tracked.  Comment and string bodies are NOT masked (the
# tree_audit byte-literal convention): a block-comment line that starts
# with theorem/lemma/def enters the census and later surfaces as an
# UNPARSED row instead of being silently dropped.
#
# Probe face.  Primary form, copy-append: for each target the file text is
# copied into a checker file in a private temp directory (the repository
# tree gains zero bytes) and one probe line per declaration is APPENDED to
# the copy - `#print axioms <name> -- rocqwash-probe <name>`, one line per
# declaration in enumeration order with an exact-name marker comment.
# Because the probes run inside the file's own context, private
# declarations resolve (import-based probes cannot see them: unknown
# constant), and the file's own imports resolve exactly as the file itself
# resolves them.  Run form is unchanged: `lake env lean <copy>` with
# cwd = the project root (nearest ancestor holding lakefile.lean /
# lakefile.toml / lean-toolchain; a head "src" segment of the module path
# is dropped per the lake srcDir convention) when lake is usable and a
# project root exists; otherwise `lean <copy>` directly (cwd = project
# root or the target's directory).  The import-based checker form
# (build_checker: one import line plus one `#print axioms <name>` line per
# declaration) is kept for non-private declarations ONLY where copy-append
# is not applicable - a cross-file aggregated sweep, which this tool does
# not run today; no live caller emits it.  The probe lines carry an
# exact-name marker comment for human-readable checker text only: lean
# echoes neither comments nor probe lines, so the parse never searches
# stdout for marker text and never keys blocks to line numbers (the
# retired marker/line bookkeeping could never succeed).  Attribution is
# NAME-KEYED: the whole probe stdout is scanned for '<name>'
# does-not-depend / depends-on blocks and each reported name maps to the
# emitted probe list by exact match; a private declaration reported
# under its mangled module-private name matches by suffix containment
# ONLY when exactly one emitted declaration name is a suffix of the
# reported name (anything else stays UNPARSED, honest).  A failed or
# unresolved probe maps ONLY to its own declaration as UNPARSED (no
# cascade to siblings); the checker output is parsed regardless of the
# child exit code (info blocks and errors share the stream), and a
# whole-file failure still records the capped error tail on the file
# row, never judged.
#
# Classification face.  Each parsed axiom set classifies by the precedence
# below.  A PRIVATE declaration whose probe succeeded and whose set
# adjudicates benign (empty or trio/whitelist subset) is classed
# PRIVATE-COVERED instead of CLEAN / BENIGN-STANDARD: the class marks that
# the declaration was actually seen through the copy-append probe (its
# axiom closure rides the row and counts normally toward the verdict), NOT
# a pass-by-absence.  Alarm classes keep their precedence over the marker:
# a private declaration with sorryAx is SORRY-ALARM, one with a custom
# axiom is CUSTOM-AXIOM-ALARM.
#
# Toolchain gate.  lean and lake resolve from PATH and each is probed with
# `--version`: usable means the binary exists and the probe exits 0.  This
# is deliberate: on an elan-managed host without a configured default
# toolchain the shims exist and execute but exit 1, and existence alone
# would fake a gate pass.  Neither usable -> exit 112 before any work,
# with the requirement named on stderr (honest skip, nothing simulated).
#
# Toolchain pin gate.  Before any probing, the sweep resolves the target's
# lean-toolchain pin: the nearest lean-toolchain file walking up from the
# root (a file root starts at its own directory, a directory root at the
# directory itself), read as its first line stripped; an existing but
# unreadable or empty pin file is an honest refusal, never a guess.  The
# pin is checked against the elan installed list (`elan toolchain list`,
# trailing (default)/(overridden ...) annotations stripped).  Pin
# installed: the probes run pinned - LEAN_TOOLCHAIN=<pin> injected into
# every probe child environment (the elan-side injection channel) and the
# gate probes additionally run under the pin directory (the elan proxy
# resolves the toolchain from the cwd lean-toolchain lookup, so the
# pinned binaries, never the PATH default, answer; elan builds that
# ignore the environment variable still resolve the pin through that
# cwd lookup, and every probe cwd - the project root or the target's
# directory - always sits under the pin directory by construction).  Pin
# missing: honest skip rc 112 upgraded with a doctor block on stdout
# naming the exact one-line fix (`elan toolchain install <pin>`) and the
# judged-zero-rows disclosure.  Pin unreadable, or the elan installed
# list unavailable: the same refusal (a pin that cannot be verified must
# not silently fall back to the PATH default - that fallback is the
# toolchain drift, and an axiom set can drift across toolchain versions:
# the soundness gap this gate closes).  No pin file: today's behavior
# unchanged (PATH default resolution; the toolchain block carries
# pin/target_pin/match all null).  The toolchain block of every report
# carries the match conclusion as pin/target_pin/match alongside the
# lean/lake resolutions and usability probes.  --toolchain-doctor: the
# standalone diagnostic face - one JSON line (schema
# rocqwash-toolchain-doctor/1, every field {value, basis}) reporting the
# whole resolution chain (lean/lake PATH resolutions and version tokens,
# the target pin and its directory, the elan installed-list excerpt, the
# match verdict and the exact install command when the pin is missing)
# and exit 0 always; it judges nothing and touches nothing.
#
# Output shape.  Every top-level key except "scan_face" and the plain
# "schema" string is {"value": ..., "basis": ...} (the v2 note-5 standard,
# the tree_audit calibration face): a consumer quoting a number quotes its
# counting rule with it.  scan_face carries exactly the four fixed English
# fields scanned / not_scanned / negative_finding / equivalents and cites
# the line-start regex limitation; all four strings are module constants
# pinned verbatim by the selftest.
#
# Classification precedence (per declaration axiom set).
#   1. sorryAx present -> SORRY-ALARM (sorryAx is never admissible to the
#      whitelist: the "0 sorry" claim is this tool's audit object).
#   2. any name outside the standard trio and outside --allow-axiom ->
#      CUSTOM-AXIOM-ALARM, the custom names listed verbatim.
#   3. empty set -> CLEAN; otherwise -> BENIGN-STANDARD (the "three
#      axioms" finding [propext, Classical.choice, Quot.sound] of the
#      earlier audit work stream and subsets adjudicate here; whitelist
#      hits ride along in "allowed").
#   4. a private declaration (flagged by the enumeration modifiers scan)
#      adjudicating at step 3 is classed PRIVATE-COVERED instead of
#      CLEAN / BENIGN-STANDARD - probed through the copy-append form, its
#      axiom set rides the row normally (steps 1-2 keep their classes).
#
# Closure snapshot and diff faces (the beyond-platform capability: the
# platform tools give today's closure, nobody gives closure EVOLUTION).
#   --snapshot OUT writes a machine closure snapshot, schema
#   rocqwash-axiom-closure-snapshot/1: plain machine fields (schema, tool,
#   root, allow_axioms, counts) plus per classified declaration the full
#   probe name, file, line, class and the SORTED axiom set.  UNPARSED rows
#   carry no closure and stay out of declarations; they are recorded
#   honestly by name at snapshot level (unparsed_count/unparsed_names),
#   nothing silently dropped.  Deterministic: declaration rows sorted by
#   (name, file, line), name lists and axiom sets sorted, no wall clock -
#   the same sweep answers byte-identically, double-run byte-identical.
#   --baseline SNAPSHOT diffs the current closure against a previously
#   written snapshot into the closure_diff block, keyed by full
#   declaration name (a repeated name resolves to the last row in the
#   snapshot's sorted order).  Per declaration one verdict: UNCHANGED
#   (same axiom set), AXIOM-SET-CHANGED (from_axioms -> to_axioms listed),
#   NEW-THEOREM (name only in the current snapshot), LOST-THEOREM (name
#   absent from the current snapshot: a removal and a failed or unparsed
#   probe both surface here, snapshots record closures only).  A
#   previously-clean declaration (empty baseline axiom set) whose current
#   axiom set is non-empty is a NEW-DEPENDENCY, listed by name.  Any
#   AXIOM-SET-CHANGED verdict or any NEW-DEPENDENCY event sets the
#   top-level diff_alarm true (false otherwise; NEW-THEOREM and
#   LOST-THEOREM alone do not alarm; the flag rides the payload, the
#   sweep exit code stays the sweep's own green/red face).  closure_diff
#   and diff_alarm are {value, basis}-wrapped like every other top-level
#   report field; with no --baseline neither key exists and the report
#   shape is byte-for-byte today's (backward compatible, exit 0 as
#   today).  The diff reads ONLY the two snapshot files' data, so the
#   snapshot and diff faces are toolchain-independent; a baseline file
#   that is missing, unparseable, or not a rocqwash-axiom-closure-snapshot/1
#   document is a usage error (rc 2) named on stderr, never a guess.
#
# Determinism.  Sorted file walk, enumeration order per file, no wall
# clock in the report, fixed string caps; the same input tree with the
# same toolchain answers byte-identically.  Temp checker files are removed
# at exit (always; no retention flag exists on this tool).

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOL = "lean_axiom_sweep"
SCHEMA = "rocqwash-axiom-sweep/1"

# The three standard Lean axioms (the "three axioms" audit face).
BENIGN_STANDARD = ("propext", "Classical.choice", "Quot.sound")
SORRY_AX = "sorryAx"

# The PRIVATE-COVERED class: a private declaration successfully probed
# through the copy-append form.  Its axiom closure rides the row and
# counts normally toward the sweep verdict; it is NOT a pass-by-absence.
PRIVATE_COVERED = "PRIVATE-COVERED"
# Exact-name marker comment on every emitted probe line; human-readable
# checker text only - lean never echoes comments, so the parse never
# searches stdout for it (attribution is name-keyed over the blocks).
PROBE_MARKER = "rocqwash-probe"

# Line-start declaration enumeration (byte-literal; comment bodies unmasked).
# DECL_RE captures the modifier prefix as group 1 so the private flag is
# detectable at enumeration time (group 2 keyword, group 3 name).
DECL_MODIFIERS = (r"(?:(?:private|protected|noncomputable|unsafe|partial|"
                  r"local|global|export)[ \t]+)*")
DECL_RE = re.compile(
    r"(?m)^[ \t]*(" + DECL_MODIFIERS + r")"
    r"(theorem|lemma|def)[ \t]+([A-Za-z_][A-Za-z0-9_']*)")
NAMESPACE_RE = re.compile(r"(?m)^[ \t]*namespace[ \t]+([A-Za-z_][A-Za-z0-9_'.]*)")
SECTION_RE = re.compile(r"(?m)^[ \t]*section(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")
END_RE = re.compile(r"(?m)^[ \t]*end(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")

# `#print axioms` output faces (Lean 4 CLI message lines).  Attribution
# is NAME-KEYED: the unanchored block regexes scan the whole probe stdout
# and each reported '<name>' maps to the emitted probe list by exact
# match, with a unique-suffix fallback for mangled private names; probe
# line numbers are bookkeeping only, never parsed.  POSITION_RE (still
# tolerant of Windows drive-letter paths: the non-greedy path piece can
# only end at a `:<digits>:<digits>: ` run followed by a severity word)
# now feeds ONLY the honest per-name UNPARSED reasons: an error message
# quoting a probe's name becomes that probe's reason when its block is
# missing.  A probe whose name never parses stays UNPARSED for that ONE
# declaration - honest, no sibling cascade.
CLEAN_RE = re.compile(r"'([^']+)' does not depend on any axioms")
AXIOMS_RE = re.compile(r"'([^']+)' depends on axioms:[ \t]*\[([^\]]*)\]")
POSITION_RE = re.compile(
    r"(?m)^(?P<path>.*?):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<sev>info|error|warning): (?P<msg>.*)$")

PROJECT_MARKERS = ("lakefile.lean", "lakefile.toml", "lean-toolchain")
RAW_CAP = 200          # per-declaration raw probe block cap (chars)
ERROR_TAIL_LINES = 12  # per-file error tail cap (lines)
READ_ERROR_CAP = 10    # report error list cap
PROBE_TIMEOUT_DEFAULT = 600
GATE_PROBE_TIMEOUT = 20
PIN_FILE = "lean-toolchain"
DOCTOR_SCHEMA = "rocqwash-toolchain-doctor/1"
ELAN_LIST_TIMEOUT = 30

EXIT_OK = 0
EXIT_RED = 1
EXIT_USAGE = 2
EXIT_NO_TOOLCHAIN = 112

# The four fixed scan-face strings (pinned verbatim by the selftest; the
# equivalents field cites the line-start regex limitation per contract).
SCAN_SCANNED = (
    "Every .lean file under the root, walked recursively with .git"
    " directories skipped (or the single named file); declarations are the"
    " line-start theorem/lemma/def regex with the namespace/section/end"
    " stack for full names; each declaration is probed by `#print axioms`"
    " appended to a copy of the target file (the copy-append form, so"
    " private declarations are probed in their own file's context), run"
    " via the target's own lake environment (`lake env lean`) or a direct"
    " lean binary."
)
SCAN_NOT_SCANNED = (
    "Files with any other suffix, everything under .git, declarations whose"
    " keyword is not at a line start (attribute lines, non-line-start"
    " spellings), non-theorem/lemma/def declaration families, quoted"
    " <<..>> and non-ASCII identifier spellings, and anything the toolchain"
    " environment cannot compile: a failed or missing probe block leaves"
    " only its own declaration UNPARSED, never judged."
)
SCAN_NEGATIVE_FINDING = (
    "A zero count is a negative finding of this scan, not an absolute"
    " claim; CLEAN means `#print axioms` reported no axiom dependency under"
    " the probed environment."
)
SCAN_EQUIVALENTS = (
    "The declaration face is the fixed line-start keyword regex; equivalent"
    " constructs spelled differently (example, instance, abbrev, structure"
    " fields) are not enumerated, and comment or string lines that mimic"
    " declarations are enumerated too (bodies are not masked) and surface"
    " as UNPARSED rows rather than being silently dropped."
)

# Closure snapshot + diff faces (toolchain-independent: the diff reads
# only the two snapshots' data).
SNAPSHOT_SCHEMA = "rocqwash-axiom-closure-snapshot/1"

# The four per-declaration diff verdicts.
DIFF_UNCHANGED = "UNCHANGED"
DIFF_CHANGED = "AXIOM-SET-CHANGED"
DIFF_NEW = "NEW-THEOREM"
DIFF_LOST = "LOST-THEOREM"

# The summary/alarm basis strings (English, module constants so the
# selftest can pin them and consumers quote the counting rule verbatim).
DIFF_BASIS_UNCHANGED = (
    "same full declaration name in both snapshots with an identical axiom"
    " set")
DIFF_BASIS_CHANGED = (
    "same full declaration name whose axiom set differs; from_axioms and"
    " to_axioms list the two sets (a class drift without an axiom-set"
    " drift, for example a whitelist difference, stays UNCHANGED by this"
    " contract - both classes ride the row)")
DIFF_BASIS_NEW = (
    "full declaration name present only in the current snapshot")
DIFF_BASIS_LOST = (
    "full declaration name absent from the current snapshot: a removal and"
    " a failed or unparsed probe both surface here, snapshots record"
    " closures only")
DIFF_BASIS_NEWDEP = (
    "previously-clean declarations (empty baseline axiom set) whose"
    " current axiom set is non-empty; the names are listed in"
    " new_dependency_names")
DIFF_BASIS_ALARM = (
    "true when any AXIOM-SET-CHANGED verdict or any NEW-DEPENDENCY event"
    " exists, false otherwise; NEW-THEOREM and LOST-THEOREM alone do not"
    " alarm; the flag rides the payload, the sweep exit code stays the"
    " sweep's own green/red face")


def enumerate_decls(text):
    """[(full_name, line_no, is_private)] in file order: line-start
    theorem/lemma/def names with the namespace/section/end stack applied;
    is_private flags a declaration whose captured modifier prefix carries
    the `private` token (the prefix only ever holds the fixed modifier
    words, so a token-set membership test is exact).  Comment and string
    bodies are not masked (declared scan-face limitation)."""
    out = []
    stack = []  # namespace names (section frames push "")
    line_no = 0
    for line in text.splitlines():
        line_no += 1
        m = DECL_RE.match(line)
        if m:
            parts = [p for p in stack if p]
            parts.append(m.group(3))
            out.append((".".join(parts), line_no,
                        "private" in m.group(1).split()))
            continue
        m = NAMESPACE_RE.match(line)
        if m:
            stack.append(m.group(1))
            continue
        if SECTION_RE.match(line):
            stack.append("")
            continue
        if END_RE.match(line) and stack:
            stack.pop()
    return out


def derive_module(target):
    """(module_name, project_root_or_None) for the checker's import line.

    Project root = nearest ancestor of the target holding lakefile.lean,
    lakefile.toml or lean-toolchain; the module name is the target path
    relative to that root with separators dotted and '.lean' stripped
    (a head 'src' segment is dropped, the lake srcDir convention); with no
    project root the bare stem is used."""
    path = os.path.abspath(target)
    directory = os.path.dirname(path)
    root = None
    walker = directory
    while True:
        if any(os.path.exists(os.path.join(walker, mk))
               for mk in PROJECT_MARKERS):
            root = walker
            break
        parent = os.path.dirname(walker)
        if parent == walker:
            break
        walker = parent
    base = os.path.splitext(path)[0]
    if root and base.startswith(root + os.sep):
        rel = base[len(root) + 1:]
    else:
        rel = os.path.basename(base)
    parts = rel.split(os.sep)
    if len(parts) > 1 and parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts), root


def build_checker(module, names):
    """The import-based checker program text: one import line plus one
    `#print axioms <name>` per declaration, in enumeration order.  The
    FALLBACK probe form: import-based probes cannot see private names
    (unknown constant), so this form applies to non-private declarations
    ONLY where copy-append is not applicable - a cross-file aggregated
    sweep, which this tool does not run today; kept single-source here and
    pinned by the selftest emission vector."""
    lines = []
    if module:
        lines.append("import %s" % module)
    lines.append("")
    for nm in names:
        lines.append("#print axioms %s" % nm)
    lines.append("")
    return "\n".join(lines)


def build_copy_checker(text, names):
    """The primary copy-append probe form.  Returns (checker_text, probes)
    where checker_text is the target file's own text with one probe line
    per declaration APPENDED - `#print axioms <name> -- rocqwash-probe
    <name>`, enumeration order, exact-name marker comment (human-readable
    checker text only: lean never echoes comments, so the parse cannot
    and does not search stdout for it) - and probes is the emitted probe
    list [(checker_line_no, name)] the parser maps output blocks by NAME
    (the line numbers are bookkeeping only, never parsed).  Running the
    probes in the file's own context makes private declarations
    resolvable (the import-based form cannot see them) and needs no
    module derivation; a leading decoded BOM is dropped (a
    zero-information decoding artifact, not content masking)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # drop the trailing empty piece of a final newline
    tail_start = len(lines) + 2  # +1 blank separator line, +1 for 1-based
    probes = [(tail_start + offset, nm) for offset, nm in enumerate(names)]
    lines.append("")
    for nm in names:
        lines.append("#print axioms %s -- %s %s" % (nm, PROBE_MARKER, nm))
    return "\n".join(lines) + "\n", probes


def classify_axioms(axioms, allow):
    """(classification, custom_names, allowed_used) with the precedence of
    the detail block: sorryAx first (never whitelisted, and accounted by
    the sorry counter, so it never rides the custom list), then verbatim
    custom names outside the standard trio and the whitelist, then
    CLEAN / BENIGN-STANDARD."""
    rest = [a for a in axioms if a != SORRY_AX]
    custom = sorted(a for a in rest
                    if a not in BENIGN_STANDARD and a not in allow)
    allowed = sorted(a for a in rest
                     if a not in BENIGN_STANDARD and a in allow)
    if SORRY_AX in axioms:
        return "SORRY-ALARM", custom, allowed
    if custom:
        return "CUSTOM-AXIOM-ALARM", custom, allowed
    if not axioms:
        return "CLEAN", [], []
    return "BENIGN-STANDARD", [], allowed


def parse_print_axioms(output, probes):
    """Name-keyed attribution of `#print axioms` output blocks to the
    emitted probes - the retired marker/line bookkeeping never worked:
    lean echoes neither comments nor the probe lines, so stdout carries
    no marker text and no trustworthy line alignment.  The WHOLE probe
    stdout is scanned for '<name>' does-not-depend / depends-on blocks
    and each reported name maps to the emitted probe list [(line, name)]
    by EXACT name (the line numbers in the list are bookkeeping only).
    Returns one row per probe, in probe order: {"name", "ok", "axioms",
    "reason", "raw"}; ok=False rows are UNPARSED (honest) and map ONLY to
    their own declaration (no sibling cascade); raw is the capped output
    head.

    Mangled-private fallback: the copy-append context can report a
    private declaration under its mangled module-private name; on an
    exact miss the reported name matches by suffix containment ONLY when
    exactly one emitted declaration name is a suffix of it - zero or
    several candidates stay UNPARSED, never guessed.  A name answered
    with two DIFFERENT axiom sets (a displaced or duplicated response)
    is unusable: exactly its own row goes UNPARSED with a
    does-not-correspond reason, nothing judged.  A probe whose name
    never parses takes the first position-prefixed error message quoting
    it ('<name>' as a quoted token; unknown identifier and friends) as
    its reason, else an honest no-block reason naming the blocks that
    were reported; blocks quoting never-probed names (the target file
    may carry its own `#print` lines) attribute to nobody and ride no
    row."""
    probe_names = [nm for _ln, nm in probes]
    name_set = set(probe_names)
    # Reported name -> dict of DISTINCT axiom tuples seen (insertion
    # ordered, hence deterministic): duplicate identical blocks collapse,
    # conflicting ones stay visible.
    seen = {}
    for m in AXIOMS_RE.finditer(output):
        axioms = tuple(a.strip() for a in m.group(2).split(",") if a.strip())
        seen.setdefault(m.group(1), {})[axioms] = None
    for m in CLEAN_RE.finditer(output):
        seen.setdefault(m.group(1), {})[()] = None
    # Position-prefixed error messages feed ONLY the honest per-name
    # UNPARSED reasons, never attribution: the first error message
    # quoting a probe's name becomes that probe's reason when its block
    # is missing.
    err_by_name = {}
    for m in POSITION_RE.finditer(output):
        if m.group("sev") != "error":
            continue
        msg = m.group("msg")
        for nm in probe_names:
            if nm not in err_by_name and "'%s'" % nm in msg:
                err_by_name[nm] = msg
    # Per reported name resolve its target probe: exact first, then the
    # unique-suffix fallback; a conflicting or ambiguous reported name
    # resolves to nobody.
    target = {}       # probe name -> resolved axiom list
    rep_targets = {}  # reported name -> number of probes it could serve
    for rep, sets in seen.items():
        if len(sets) > 1:
            rep_targets[rep] = 0  # conflicting duplicate: unusable
            continue
        axioms = list(next(iter(sets)))
        if rep in name_set:
            target[rep] = axioms
            rep_targets[rep] = 1
            continue
        tgt = [nm for nm in probe_names if rep.endswith(nm)]
        rep_targets[rep] = len(tgt)
        if len(tgt) == 1 and tgt[0] not in target:
            target[tgt[0]] = axioms
    reported_sorted = sorted(seen)
    rows = []
    for nm in probe_names:
        if nm in seen and len(seen[nm]) > 1:
            variants = [list(t) for t in seen[nm]]
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": ("output does not correspond to a"
                                    " single emission: %r answered with"
                                    " %d conflicting blocks %r; nothing"
                                    " attributed"
                                    % (nm, len(variants), variants)),
                         "raw": output[:RAW_CAP]})
            continue
        if nm in target:
            rows.append({"name": nm, "ok": True, "axioms": target[nm],
                         "reason": "", "raw": ""})
            continue
        if nm in err_by_name:
            msg = err_by_name[nm].strip()[:RAW_CAP]
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": msg, "raw": output[:RAW_CAP]})
            continue
        cands = [rep for rep in seen if rep.endswith(nm)]
        if len(cands) == 1 and rep_targets[cands[0]] > 1:
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": ("reported name %r is a mangled-name"
                                    " candidate for %r but its suffix"
                                    " match is ambiguous across probes"
                                    " %r; nothing attributed"
                                    % (cands[0], nm,
                                       [p for p in probe_names
                                        if cands[0].endswith(p)])),
                         "raw": output[:RAW_CAP]})
            continue
        if len(seen) == 1:
            rep = next(iter(seen))
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": ("probe block names %r, expected %r;"
                                    " no exact or unique-suffix match"
                                    % (rep, nm)),
                         "raw": output[:RAW_CAP]})
            continue
        rows.append({"name": nm, "ok": False, "axioms": [],
                     "reason": ("no probe block found for name %r in"
                                " probe output; blocks reported: %r"
                                % (nm, reported_sorted)),
                     "raw": output[:RAW_CAP]})
    return rows


def probe_toolchain(cwd=None, env=None):
    """Resolve and probe the toolchain; returns (lean, lake, usable_lean,
    usable_lake).  Usable = found on PATH and a `--version` probe exits 0
    (the elan-shim face: the shim executes but exits 1 with 'no default
    toolchain configured', so existence alone is not usability).  cwd/env
    pin the probes to a resolution in force: with an honored pin the gate
    probes run under the pin directory and the injected environment so
    the pinned binaries answer (the elan proxy resolves the toolchain
    from the cwd lean-toolchain lookup), never the PATH default."""
    lean = shutil.which("lean")
    lake = shutil.which("lake")

    def version_ok(binary):
        if not binary:
            return False
        try:
            p = subprocess.run([binary, "--version"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               timeout=GATE_PROBE_TIMEOUT, cwd=cwd, env=env)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return p.returncode == 0

    return lean, lake, version_ok(lean), version_ok(lake)


def find_lean_pin(target):
    """(pin, pin_dir, error): the nearest lean-toolchain file walking up
    from the target (a file target starts at its own directory, a
    directory target at the directory itself), read as its first line
    stripped.  error is None on success; an existing but unreadable or
    empty pin file is an error, never a guess - a pin the sweep cannot
    read must not silently fall back to the PATH default (that fallback
    is exactly the toolchain drift the pin gate exists to prevent: an
    axiom set can drift across toolchain versions)."""
    start = os.path.abspath(target)
    directory = start if os.path.isdir(start) else os.path.dirname(start)
    walker = directory
    while True:
        pin_path = os.path.join(walker, PIN_FILE)
        if os.path.isfile(pin_path):
            try:
                with open(pin_path, "r", encoding="utf-8") as fh:
                    value = fh.readline().strip()
            except OSError as exc:
                return None, None, "cannot read %s: %s" % (pin_path, exc)
            if not value:
                return None, walker, "empty pin file %s" % pin_path
            return value, walker, None
        parent = os.path.dirname(walker)
        if parent == walker:
            return None, None, None
        walker = parent


def parse_toolchain_list(raw):
    """Installed toolchain names from `elan toolchain list` stdout: one
    name per line, any trailing parenthesized annotation stripped
    ("(default)", "(overridden by ...)"), empty lines dropped."""
    names = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        names.append(re.sub(r"\s+\([^)]*\)$", "", ln).strip())
    return names


def read_installed_toolchains(timeout=ELAN_LIST_TIMEOUT):
    """(names, error) from `elan toolchain list`; names None on any
    failure (elan absent from PATH, nonzero exit, timeout) with the
    failure named for the doctor.  An unavailable installed list is an
    honest refusal, never an empty list (a refusal to verify must not
    fake a match)."""
    elan = shutil.which("elan")
    if not elan:
        return None, "elan not found on PATH"
    try:
        p = subprocess.run([elan, "toolchain", "list"],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "elan toolchain list failed: %s" % exc
    if p.returncode != 0:
        return None, ("elan toolchain list exited %s: %s"
                      % (p.returncode,
                         p.stdout.decode("utf-8", "replace")
                         .strip()[:RAW_CAP]))
    return parse_toolchain_list(p.stdout.decode("utf-8", "replace")), None


def pin_version_of(pin):
    """The version component of a toolchain descriptor for evidence
    display: the text after the last colon with a leading v stripped
    (leanprover/lean4:v4.33.1 -> 4.33.1; v4.35.0-rc3 -> 4.35.0-rc3)."""
    tail = pin.rsplit(":", 1)[-1]
    return tail[1:] if tail.startswith("v") else tail


LEAN_VERSION_RE = re.compile(r"\(version ([^,]+),")
LAKE_VERSION_RE = re.compile(r"Lean version ([^)]+)\)")


def lean_version_of(output):
    """The version token of a `lean --version` line (Lean (version
    4.33.1, ...)); None when the output does not parse (honest null)."""
    m = LEAN_VERSION_RE.search(output)
    return m.group(1).strip() if m else None


def lake_version_of(output):
    """The Lean version token of a `lake --version` line (Lake version
    ... (Lean version 4.34.1)); None when the output does not parse."""
    m = LAKE_VERSION_RE.search(output)
    return m.group(1).strip() if m else None


def build_probe_env(base, pin):
    """The probe child environment for an honored pin: LEAN_TOOLCHAIN=<pin>
    injected over a copy of the caller's environment (the elan-side
    injection channel; elan builds that ignore the variable still resolve
    the pin through the cwd lean-toolchain lookup, which the gate aligns
    by probing under the pin directory).  With no pin the caller's
    environment passes through unchanged (no key introduced)."""
    if not pin:
        return base
    env = dict(base)
    env["LEAN_TOOLCHAIN"] = pin
    return env


def probe_version_output(binary, cwd=None, env=None,
                         timeout=GATE_PROBE_TIMEOUT):
    """(output_text, error) of `<binary> --version` under cwd/env; error
    None on a zero exit, else the capped merged output (the elan
    not-installed error rides here for the doctor)."""
    if not binary:
        return "", "binary absent"
    try:
        p = subprocess.run([binary, "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout,
                           cwd=cwd, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", str(exc)
    text = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0:
        return text, "exit %s: %s" % (p.returncode, text.strip()[:RAW_CAP])
    return text, None


def build_doctor(root, pin, pin_dir, pin_err, installed, elan_err, honored,
                 lean, lake, lean_version, lake_version):
    """Pure assembly of the toolchain resolution-chain doctor payload
    (schema rocqwash-toolchain-doctor/1): every payload field is
    {value, basis} (the v2 note-5 standard), so a consumer quoting the
    match verdict quotes its deciding rule with it.  verdict faces:
    matched (pin installed and honored), pin-missing (the installed list
    is readable and the pin is not in it), pin-unverifiable (the pin
    cannot be read, or the installed list is unavailable), no-pin (no
    lean-toolchain file above the root).  install_command carries the
    exact one-line fix whenever a known pin is not honored (the missing
    and the unverifiable faces both fix the same way)."""
    if pin_err:
        verdict = "pin-unverifiable"
    elif pin is None:
        verdict = "no-pin"
    elif elan_err:
        verdict = "pin-unverifiable"
    elif honored:
        verdict = "matched"
    else:
        verdict = "pin-missing"
    match = None if verdict == "no-pin" else bool(honored)
    install_command = ("elan toolchain install %s" % pin
                       if pin and not honored else None)
    if pin_err:
        pin_basis = pin_err
    else:
        pin_basis = ("first line of the nearest lean-toolchain file"
                     " walking up from the root; null = none found")
    if elan_err:
        installed_basis = "installed list unavailable: %s" % elan_err
    else:
        installed_basis = ("elan toolchain list, one name per line with"
                           " any trailing (default)/(overridden ...)"
                           " annotation stripped; null = unavailable")
    return {
        "schema": DOCTOR_SCHEMA,
        "root": {"value": root,
                 "basis": "the root the pin resolution walked up from"},
        "lean": {"value": lean,
                 "basis": "lean resolved from PATH (shutil.which);"
                          " null = absent"},
        "lake": {"value": lake,
                 "basis": "lake resolved from PATH (shutil.which);"
                          " null = absent"},
        "lean_version": {"value": lean_version,
                         "basis": "version token of the lean --version"
                                  " probe under the resolution in force"
                                  " (the cwd pin lookup with"
                                  " LEAN_TOOLCHAIN injected when the pin"
                                  " is honored, the PATH default"
                                  " otherwise); null = the probe failed"
                                  " or did not parse"},
        "lake_version": {"value": lake_version,
                         "basis": "Lean version token of the lake"
                                  " --version probe under the same"
                                  " resolution; null = the probe failed"
                                  " or did not parse"},
        "target_pin": {"value": pin, "basis": pin_basis},
        "pin_dir": {"value": pin_dir,
                    "basis": "directory holding that lean-toolchain file"
                             " (the elan cwd lookup root); null = none"
                             " found"},
        "installed": {"value": installed, "basis": installed_basis},
        "match": {"value": match,
                  "basis": "true = the pin is installed and the probes"
                           " run pinned (LEAN_TOOLCHAIN injected over the"
                           " cwd pin lookup); false = the pin cannot be"
                           " honored; null = no pin file above the root"},
        "install_command": {"value": install_command,
                            "basis": "the exact one-line fix whenever a"
                                     " known pin is not honored; null"
                                     " otherwise"},
        "verdict": {"value": verdict,
                    "basis": "matched / pin-missing / pin-unverifiable /"
                             " no-pin"},
    }


def collect_targets(root):
    """[(abs_path, rel_path)] sorted; a file root scans that file, a
    directory root walks *.lean skipping .git."""
    if os.path.isfile(root):
        return [(os.path.abspath(root), os.path.basename(root))]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".lean"):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, root).replace("\\", "/")
                out.append((abs_path, rel))
    out.sort()
    return out


def error_tail(output, lines=ERROR_TAIL_LINES):
    tail = [ln for ln in output.splitlines() if ln.strip()]
    return tail[-lines:]


def run_probe(argv, cwd, timeout, env=None):
    """Subprocess run with merged streams and a hard timeout; returns
    (rc, output, error) where error is None on a clean launch, "timeout"
    on a timeout, or the OS launch failure string.  env pins the child
    environment when an honored pin injects LEAN_TOOLCHAIN (None passes
    the parent environment through, today's behavior)."""
    try:
        p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout,
                           env=env)
        return p.returncode, p.stdout.decode("utf-8", "replace"), None
    except subprocess.TimeoutExpired as exc:
        partial = b""
        if exc.stdout:
            partial += exc.stdout
        if exc.stderr:
            partial += exc.stderr
        return None, partial.decode("utf-8", "replace"), "timeout"
    except OSError as exc:
        return None, "", str(exc)


def classify_decl_rows(rel, decls, parsed, allow, mode):
    """Pure per-declaration row assembly over the enumeration
    [(name, line, is_private)] and the parsed probe rows (aligned
    one-to-one by construction of the emitted probe list): each axiom set
    classifies by the detail-block precedence; a private declaration
    adjudicating benign (CLEAN / BENIGN-STANDARD) is classed
    PRIVATE-COVERED - probed through the copy-append form, its axiom
    closure rides the row and counts normally toward the verdict, not a
    pass-by-absence - while alarm classes keep their precedence over the
    marker; a failed or unresolved probe maps only to its own declaration
    as UNPARSED."""
    rows = []
    for (nm, ln, is_private), row in zip(decls, parsed):
        klass, custom, allowed = classify_axioms(
            row["axioms"] if row["ok"] else [], allow)
        if not row["ok"]:
            klass = "UNPARSED"
            custom = []
            allowed = []
        elif is_private and klass in ("CLEAN", "BENIGN-STANDARD"):
            klass = PRIVATE_COVERED
        rows.append({
            "file": rel, "line": ln, "name": nm,
            "classification": klass,
            "axioms": row["axioms"] if row["ok"] else [],
            "custom": custom, "allowed": allowed,
            "private": is_private,
            "probe": mode,
            "raw": "" if row["ok"] else row["raw"],
            "unparsed_reason": row["reason"] if not row["ok"] else "",
        })
    return rows


def sweep(root, allow, timeout, gate=None, pin=None):
    """The run face; returns (exit_code, report).  Every target is probed
    by the copy-append form (build_copy_checker): the file text plus the
    appended probe lines run in the target's own lake environment or
    against a direct lean binary, same cwd rules as ever.  Write faces:
    the private temp workdir (removed on exit) and the caller-named --json
    file handled by main.  The toolchain gate has already passed when this
    runs: gate carries the precomputed (lean, lake, usable_lean,
    usable_lake) resolution - for an honored pin, probed under the pin
    directory with the injected environment - and None re-probes the PATH
    default (today's behavior).  pin (an honored pin value or None) is
    injected into every probe child environment (LEAN_TOOLCHAIN) and
    recorded in the report's toolchain block pin/target_pin/match."""
    if gate is None:
        lean, lake, usable_lean, usable_lake = probe_toolchain()
    else:
        lean, lake, usable_lean, usable_lake = gate
    probe_env = build_probe_env(os.environ, pin)
    targets = collect_targets(root)
    work = tempfile.mkdtemp(prefix="rocqwash_axiom_sweep_")
    file_rows = []
    decl_rows = []
    errors = []
    try:
        for idx, (abs_path, rel) in enumerate(targets):
            try:
                with open(abs_path, "rb") as fh:
                    text = fh.read().decode("utf-8", "replace")
            except OSError as exc:
                errors.append("read %s: %s" % (rel, exc))
                continue
            decls = enumerate_decls(text)
            # The module name stays on the file row as honest metadata
            # (and feeds the module-derivation face); the copy-append
            # checker itself needs no import line.
            module, project_root = derive_module(abs_path)
            frow = {"file": rel, "declarations": len(decls),
                    "module": module, "probe": "", "form": "copy-append",
                    "rc": None, "error_tail": []}
            if decls:
                checker, probes = build_copy_checker(
                    text, [nm for nm, _ln, _p in decls])
                checker_path = os.path.join(work, "ck_%04d.lean" % idx)
                with open(checker_path, "w", encoding="utf-8",
                          newline="\n") as fh:
                    fh.write(checker)
                if usable_lake and project_root:
                    argv = [lake, "env", "lean", checker_path]
                    cwd = project_root
                    mode = "lake-env"
                elif usable_lean:
                    argv = [lean, checker_path]
                    cwd = project_root or os.path.dirname(abs_path)
                    mode = "lean-direct"
                else:
                    argv = [lake, "env", "lean", checker_path]
                    cwd = project_root or os.path.dirname(abs_path)
                    mode = "lake-env"
                rc, output, err = run_probe(argv, cwd, timeout,
                                            env=probe_env)
                frow["probe"] = mode
                frow["rc"] = rc
                if err is not None:
                    frow["error_tail"] = [err][:ERROR_TAIL_LINES]
                    errors.append("probe %s: %s" % (rel, err))
                elif rc != 0:
                    frow["error_tail"] = error_tail(output)
                    errors.append("probe %s: lean exited %s" % (rel, rc))
                parsed = parse_print_axioms(output, probes)
                decl_rows.extend(classify_decl_rows(
                    rel, decls, parsed, allow, mode))
            file_rows.append(frow)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    report = build_report(root, file_rows, decl_rows, errors, allow,
                          {"lean": lean, "lake": lake,
                           "usable_lean": usable_lean,
                           "usable_lake": usable_lake,
                           "pin": pin, "target_pin": pin,
                           "match": True if pin else None})
    return exit_code_for(report), report


def build_report(root, file_rows, decl_rows, errors, allow, toolchain_face,
                 diff_face=None):
    """Pure report assembly over the collected rows; the selftest schema
    vector feeds this with canned rows (offline, no toolchain).  A
    diff_face (a diff_closures payload, or None without --baseline) is
    attached as the closure_diff + diff_alarm top-level fields; without
    one the report shape is byte-for-byte today's (backward compatible)."""
    counts = {}
    for row in decl_rows:
        counts[row["classification"]] = \
            counts.get(row["classification"], 0) + 1
    clean = counts.get("CLEAN", 0)
    benign = counts.get("BENIGN-STANDARD", 0)
    sorry = counts.get("SORRY-ALARM", 0)
    custom = counts.get("CUSTOM-AXIOM-ALARM", 0)
    unparsed = counts.get("UNPARSED", 0)
    private_covered = counts.get(PRIVATE_COVERED, 0)
    custom_names = sorted({c for row in decl_rows for c in row["custom"]})
    verdict = "RED" if (sorry or custom or unparsed) else "PASS"
    report = {
        "schema": SCHEMA,
        "root": {"value": root,
                 "basis": "the scan root as given; a file root scans that"
                          " file, a directory root walks *.lean with .git"
                          " skipped"},
        "files": {"value": len(file_rows),
                  "basis": ".lean targets read (file root: 1; read failures"
                           " sit in errors, not here)"},
        "declarations": {"value": len(decl_rows),
                         "basis": "line-start theorem/lemma/def names"
                                  " enumerated per the scan_face regex"
                                  " (namespace/section/end stack applied)"},
        "classified": {"value": clean + benign + sorry + custom
                                 + private_covered,
                       "basis": "declarations whose `#print axioms` block"
                                " parsed into an axiom set"},
        "clean": {"value": clean,
                  "basis": "axiom set empty: 'does not depend on any"
                           " axioms' under the probed environment"},
        "benign_standard": {"value": benign,
                            "basis": "axiom set a subset of the standard"
                                     " trio propext, Classical.choice,"
                                     " Quot.sound (the 'three axioms'"
                                     " finding of the earlier audit"
                                     " work stream adjudicates here)"
                                     " or admitted by --allow-axiom"
                                     " (admitted names ride in the"
                                     " declaration's allowed field)"},
        "private_covered": {"value": private_covered,
                            "basis": "private declarations successfully"
                                     " probed via the copy-append form"
                                     " (private names are invisible to"
                                     " import-based probes) whose axiom"
                                     " set adjudicated benign; the"
                                     " closure rides the row and counts"
                                     " normally toward the verdict,"
                                     " this is NOT a pass-by-absence,"
                                     " and alarm classes keep their"
                                     " precedence over the marker"},
        "sorry_alarm": {"value": sorry,
                        "basis": "sorryAx in the axiom set; never"
                                 " admissible to the whitelist"},
        "custom_axiom_alarm": {"value": custom,
                               "basis": "any axiom outside the standard"
                                        " trio and the whitelist; names"
                                        " listed verbatim in"
                                        " custom_axiom_names"},
        "unparsed": {"value": unparsed,
                     "basis": "probe output not understood (missing or"
                              " mismatched block); honest, never judged,"
                              " raw block capped in the row"},
        "custom_axiom_names": {"value": custom_names,
                               "basis": "sorted unique verbatim names"
                                        " outside the standard trio and"
                                        " the whitelist across alarm rows"
                                        " (sorryAx itself is accounted by"
                                        " the sorry counter, never"
                                        " here)"},
        "allow_axioms": {"value": sorted(allow),
                         "basis": "the --allow-axiom whitelist in force;"
                                  " sorryAx is never admitted"},
        "file_rows": {"value": file_rows,
                      "basis": "per target: file, declarations, module,"
                               " probe mode, probe form (copy-append),"
                               " lean rc, capped error tail"},
        "declarations_detail": {"value": decl_rows,
                                "basis": "per declaration: file, line,"
                                         " full probe name, classification"
                                         " (CLEAN / BENIGN-STANDARD /"
                                         " SORRY-ALARM /"
                                         " CUSTOM-AXIOM-ALARM /"
                                         " PRIVATE-COVERED / UNPARSED),"
                                         " verbatim axiom set, custom and"
                                         " whitelist names, private flag,"
                                         " probe mode, capped raw block"
                                         " for unparsed rows"},
        "errors": {"value": errors[:READ_ERROR_CAP],
                   "basis": "first %d read or probe failures, each naming"
                            " the target" % READ_ERROR_CAP},
        "error_count": {"value": len(errors),
                        "basis": "total recorded read and probe failures;"
                                 " errors is capped at %d"
                                 % READ_ERROR_CAP},
        "toolchain": {"value": toolchain_face,
                      "basis": "lean/lake PATH resolutions and their"
                               " --version usability probes; the probe"
                               " mode per file is lake-env or"
                               " lean-direct; pin/target_pin carry the"
                               " target's lean-toolchain pin resolution"
                               " and match the honoring decision"
                               " (true = the probes ran pinned, the"
                               " LEAN_TOOLCHAIN injection over the cwd"
                               " lean-toolchain lookup; false = the pin"
                               " could not be honored and the sweep"
                               " skipped; null = no pin file above the"
                               " target, the PATH default ran)"},
        "verdict": {"value": verdict,
                    "basis": "RED when any SORRY-ALARM,"
                             " CUSTOM-AXIOM-ALARM or UNPARSED row exists"
                             " (unjudgeable is not green); read and probe"
                             " failures force exit 1 via error_count"
                             " without flipping this verdict"},
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }
    if diff_face is not None:
        attach_closure_diff(report, diff_face)
    return report


def exit_code_for(report):
    """0 green; 1 when the verdict is RED or any error was recorded."""
    if report["verdict"]["value"] == "RED":
        return EXIT_RED
    if report["error_count"]["value"] > 0:
        return EXIT_RED
    return EXIT_OK


def build_snapshot(root, decl_rows, allow):
    """Machine closure snapshot (schema rocqwash-axiom-closure-snapshot/1)
    over a sweep's declaration rows: per classified declaration the full
    probe name, file, line, class and the sorted axiom set.  PRIVATE-COVERED
    rows are classified rows: their closure enters the snapshot under the
    PRIVATE-COVERED class like any other.  UNPARSED rows
    carry no closure and stay out of declarations; they are recorded
    honestly by name at snapshot level, nothing silently dropped.
    Deterministic: rows sorted by (name, file, line), name lists and
    axiom sets sorted, no wall clock - the same sweep answers
    byte-identically, double-run byte-identical."""
    decls = []
    unparsed = []
    for row in decl_rows:
        if row["classification"] == "UNPARSED":
            unparsed.append(row["name"])
            continue
        decls.append({"name": row["name"],
                      "file": row["file"],
                      "line": row["line"],
                      "classification": row["classification"],
                      "axioms": sorted(row["axioms"])})
    decls.sort(key=lambda d: (d["name"], d["file"], d["line"]))
    return {
        "schema": SNAPSHOT_SCHEMA,
        "tool": TOOL,
        "root": root,
        "allow_axioms": sorted(allow),
        "declaration_count": len(decl_rows),
        "classified_count": len(decls),
        "unparsed_count": len(unparsed),
        "unparsed_names": sorted(set(unparsed)),
        "declarations": decls,
    }


def load_snapshot(path):
    """Read a closure snapshot file; returns (snapshot, error) with error
    None on success.  A missing, unparseable or wrong-schema file is a
    usage error, never a guess (a sweep report is not a snapshot)."""
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
    except OSError as exc:
        return None, "cannot read --baseline snapshot %s: %s" % (path, exc)
    try:
        data = json.loads(text)
    except ValueError as exc:
        return None, ("--baseline snapshot %s is not valid JSON: %s"
                      % (path, exc))
    if not isinstance(data, dict) or data.get("schema") != SNAPSHOT_SCHEMA:
        found = data.get("schema") if isinstance(data, dict) else None
        return None, ("--baseline snapshot %s does not carry schema %s"
                      " (found %r); a sweep report (%s) is not a snapshot"
                      % (path, SNAPSHOT_SCHEMA, found, SCHEMA))
    if not isinstance(data.get("declarations"), list):
        return None, ("--baseline snapshot %s carries no declarations"
                      " list" % path)
    return data, None


def diff_closures(baseline, current):
    """Pure per-declaration closure diff of two snapshot dicts; reads only
    the two snapshots' data, so the diff face is toolchain-independent
    (no Lean involvement).  Rows are keyed by full declaration name (a
    repeated name resolves to the last row in the snapshot's sorted
    order) and sorted by name; each carries one verdict - UNCHANGED /
    AXIOM-SET-CHANGED (from_axioms -> to_axioms listed) / NEW-THEOREM /
    LOST-THEOREM - plus new_dependency for a previously-clean declaration
    (empty baseline axiom set) whose current axiom set is non-empty.
    diff_alarm: true when any AXIOM-SET-CHANGED verdict or any
    NEW-DEPENDENCY event exists, false otherwise."""
    base_map = {}
    for decl in baseline["declarations"]:
        base_map[decl["name"]] = decl
    cur_map = {}
    for decl in current["declarations"]:
        cur_map[decl["name"]] = decl
    rows = []
    counts = {DIFF_UNCHANGED: 0, DIFF_CHANGED: 0,
              DIFF_NEW: 0, DIFF_LOST: 0}
    new_dep = []
    for nm in sorted(set(base_map) | set(cur_map)):
        b = base_map.get(nm)
        c = cur_map.get(nm)
        if b is None:
            rows.append({"name": nm, "verdict": DIFF_NEW,
                         "from_axioms": [], "to_axioms": sorted(c["axioms"]),
                         "from_classification": "",
                         "to_classification": c["classification"],
                         "new_dependency": False})
            counts[DIFF_NEW] += 1
            continue
        if c is None:
            rows.append({"name": nm, "verdict": DIFF_LOST,
                         "from_axioms": sorted(b["axioms"]),
                         "to_axioms": [],
                         "from_classification": b["classification"],
                         "to_classification": "",
                         "new_dependency": False})
            counts[DIFF_LOST] += 1
            continue
        from_ax = sorted(b["axioms"])
        to_ax = sorted(c["axioms"])
        dep = (not from_ax) and bool(to_ax)
        verdict = DIFF_CHANGED if from_ax != to_ax else DIFF_UNCHANGED
        rows.append({"name": nm, "verdict": verdict,
                     "from_axioms": from_ax, "to_axioms": to_ax,
                     "from_classification": b["classification"],
                     "to_classification": c["classification"],
                     "new_dependency": dep})
        counts[verdict] += 1
        if dep:
            new_dep.append(nm)
    alarm = counts[DIFF_CHANGED] > 0 or bool(new_dep)
    return {
        "baseline_root": baseline.get("root", ""),
        "rows": rows,
        "summary": {
            "unchanged": {"value": counts[DIFF_UNCHANGED],
                          "basis": DIFF_BASIS_UNCHANGED},
            "axiom_set_changed": {"value": counts[DIFF_CHANGED],
                                  "basis": DIFF_BASIS_CHANGED},
            "new_theorem": {"value": counts[DIFF_NEW],
                            "basis": DIFF_BASIS_NEW},
            "lost_theorem": {"value": counts[DIFF_LOST],
                             "basis": DIFF_BASIS_LOST},
            "new_dependency": {"value": len(new_dep),
                               "basis": DIFF_BASIS_NEWDEP},
        },
        "new_dependency_names": sorted(new_dep),
        "diff_alarm": {"value": alarm, "basis": DIFF_BASIS_ALARM},
    }


def attach_closure_diff(report, diff_face):
    """Insert the closure faces into a built report: closure_diff as a
    {value, basis} top-level field and diff_alarm as the top-level
    {value, basis} alarm flag (the schema-value-basis law; no --baseline
    leaves both keys out, the report shape stays today's)."""
    report["closure_diff"] = {
        "value": diff_face,
        "basis": "per-declaration closure diff of the current sweep against"
                 " the --baseline snapshot (schema %s): rows keyed by full"
                 " declaration name with verdict UNCHANGED /"
                 " AXIOM-SET-CHANGED (from_axioms -> to_axioms listed) /"
                 " NEW-THEOREM / LOST-THEOREM, a {value, basis} summary per"
                 " verdict kind and the NEW-DEPENDENCY names; computed from"
                 " the two snapshots' data only, no toolchain involvement"
                 % SNAPSHOT_SCHEMA,
    }
    report["diff_alarm"] = {
        "value": diff_face["diff_alarm"]["value"],
        "basis": DIFF_BASIS_ALARM,
    }
    return report


def write_json(path, payload):
    """Write the stdout payload (plus one newline) to path as UTF-8."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def summarize(report):
    """One stderr summary line (stdout stays the single JSON line); with a
    --baseline run the closure-diff counts ride the same line's tail."""
    sys.stderr.write(
        "AXIOM-SWEEP: %s decls=%d clean=%d benign_standard=%d sorry=%d"
        " custom=%d private_covered=%d unparsed=%d errors=%d"
        % (report["verdict"]["value"],
           report["declarations"]["value"],
           report["clean"]["value"],
           report["benign_standard"]["value"],
           report["sorry_alarm"]["value"],
           report["custom_axiom_alarm"]["value"],
           report["private_covered"]["value"],
           report["unparsed"]["value"],
           report["error_count"]["value"]))
    if "closure_diff" in report:
        sumry = report["closure_diff"]["value"]["summary"]
        sys.stderr.write(
            " closure_diff unchanged=%d changed=%d new=%d lost=%d"
            " new_dependency=%d diff_alarm=%s"
            % (sumry["unchanged"]["value"],
               sumry["axiom_set_changed"]["value"],
               sumry["new_theorem"]["value"],
               sumry["lost_theorem"]["value"],
               sumry["new_dependency"]["value"],
               report["diff_alarm"]["value"]))
    sys.stderr.write("\n")


# ---- selftest (frozen offline vectors on the parse, classify, report and
# gate faces; zero network, zero toolchain launch, zero real-repo touch) ----

# Canned `#print axioms` output fixtures in the Lean 4 CLI info-block face
# (position-prefixed message text; the parser must not line-anchor).
LEAN_OUT_CLEAN = ("ck.lean:2:0: info: 't_clean' does not depend on any"
                  " axioms\n")
LEAN_OUT_THREE = ("ck.lean:2:0: info: 't_three' depends on axioms: "
                  "[propext, Classical.choice, Quot.sound]\n")
LEAN_OUT_SUBSET = ("ck.lean:2:0: info: 't_subset' depends on axioms: "
                   "[propext]\n")
LEAN_OUT_SORRY = ("ck.lean:2:0: info: 't_sorry' depends on axioms:"
                  " [sorryAx]\n")
LEAN_OUT_CUSTOM = ("ck.lean:2:0: info: 't_custom' depends on axioms:"
                   " [my_axiom.rh]\n")
LEAN_OUT_MIXED = ("ck.lean:2:0: info: 'a' does not depend on any axioms\n"
                  "ck.lean:4:0: info: 'b' depends on axioms: "
                  "[propext, Classical.choice]\n"
                  "ck.lean:6:0: info: 'c' depends on axioms: [sorryAx]\n"
                  "ck.lean:8:0: info: 'd' depends on axioms: "
                  "[my_ax, propext]\n"
                  "ck.lean:9:0: error: declaration uses 'sorry'\n")
LEAN_OUT_GHOST = ("ck.lean:2:0: error: unknown identifier 't_ghost'\n")
LEAN_OUT_NAME_MISMATCH = (
    "ck.lean:2:0: info: 'some_other' depends on axioms: [sorryAx]\n")
LEAN_OUT_STRAY = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:3:0: info: 'b' depends on axioms: [sorryAx]\n")

# Copy-append attribution fixtures: LEAN_OUT_DISPLACED answers a probed
# name from a non-probe line (the emission-correspondence guard face);
# LEAN_OUT_ISOLATED has a failed middle probe whose siblings still parse
# (the no-cascade face the design freezes).
LEAN_OUT_DISPLACED = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:3:0: info: 'a' depends on axioms: [sorryAx]\n")
LEAN_OUT_ISOLATED = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:4:0: error: unknown identifier 'b'\n"
    "ck.lean:6:0: info: 'c' does not depend on any axioms\n")

# Name-keyed parse fixtures (the marker/line bookkeeping is retired):
# NAMEKEY_PROBES carries deliberately WRONG probe line numbers to pin
# that attribution keys the reported NAME against the emitted probe
# list, never the line.  LEAN_OUT_NAMEKEY_MISSING drops one block:
# exactly that row goes UNPARSED, siblings classify (no cascade).
# LEAN_OUT_NAMEKEY_MANGLED reports a private declaration under its
# mangled module-private name (the unique-suffix fallback face);
# LEAN_OUT_NAMEKEY_MANGLED_AMBIG reports one whose suffix is shared by
# two emitted names (the fallback must refuse: honest UNPARSED).
LEAN_OUT_NAMEKEY_FULL = (
    "ck.lean:2:0: info: 'n_clean' does not depend on any axioms\n"
    "ck.lean:4:0: info: 'n_three' depends on axioms: "
    "[propext, Classical.choice, Quot.sound]\n"
    "ck.lean:6:0: info: 'n_sorry' depends on axioms: [sorryAx]\n"
    "ck.lean:8:0: info: 'n_custom' depends on axioms: [my_ax.rh]\n"
    "ck.lean:10:0: info: 'n_priv' depends on axioms: [propext]\n")
LEAN_OUT_NAMEKEY_MISSING = (
    "ck.lean:2:0: info: 'n_clean' does not depend on any axioms\n"
    "ck.lean:4:0: info: 'n_three' depends on axioms: "
    "[propext, Classical.choice, Quot.sound]\n"
    "ck.lean:6:0: info: 'n_sorry' depends on axioms: [sorryAx]\n"
    "ck.lean:10:0: info: 'n_priv' depends on axioms: [propext]\n")
LEAN_OUT_NAMEKEY_MANGLED = (
    "ck.lean:5:0: info: '_private.My.Mod.0.priv_one' depends on axioms:"
    " [propext]\n")
LEAN_OUT_NAMEKEY_MANGLED_AMBIG = (
    "ck.lean:5:0: info: '_private.My.Mod.0.Foo.priv_bar' depends on"
    " axioms: [propext]\n")
NAMEKEY_PROBES = [(91, "n_clean"), (57, "n_three"), (33, "n_sorry"),
                  (75, "n_custom"), (12, "n_priv")]

# The design-4 offline fixture: one public and one private declaration;
# copy-append probes both (the private one classes PRIVATE-COVERED with
# its axiom set, the public one classes CLEAN).
PRIVATE_PUBLIC_LEAN = (
    "theorem pub_one : True := trivial\n"
    "\n"
    "private theorem priv_one : Nat := 1\n")

# Declaration-enumeration fixtures.
SAMPLE_LEAN = (
    "namespace Foo\n"
    "theorem bar : True := trivial\n"
    "  lemma nested : True := trivial\n"
    "end Foo\n"
    "theorem baz : True := trivial\n"
    "private theorem priv_one : Nat := 1\n"
    "noncomputable def nc_def : Nat := 2\n"
    "-- theorem dashed_out : True := trivial\n"
    "/- block comment\n"
    "theorem in_block_comment : True := trivial\n"
    "-/\n"
    "def with_apostrophe : Nat := 3\n"
    "section\n"
    "theorem in_section : True := trivial\n"
    "end\n"
    "instance : Inhabited Nat := <something>\n"
    "example : True := trivial\n"
)
SAMPLE_LEAN_NAMES = [("Foo.bar", 2, False), ("Foo.nested", 3, False),
                     ("baz", 5, False), ("priv_one", 6, True),
                     ("nc_def", 7, False), ("in_block_comment", 10, False),
                     ("with_apostrophe", 12, False),
                     ("in_section", 14, False)]


def selftest():
    """Frozen offline vectors; 0 green, 1 red with the failing names on
    stdout.  Zero network, zero toolchain launch, zero real-repo touch."""
    fails = []
    total = [0]

    def vec(name, ok, detail=""):
        total[0] += 1
        print("[PASS] %s" % name if ok else "[FAIL] %s %s" % (name, detail))
        if not ok:
            fails.append(name)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_axiom_sweep_selftest_")
    try:
        # declaration enumeration: stack, modifiers, decoys, families out;
        # the private flag rides every row
        got = enumerate_decls(SAMPLE_LEAN)
        vec("decl-enumeration", got == SAMPLE_LEAN_NAMES, "got %s" % (got,))
        vec("decl-enumeration-name-line-face",
            [(nm, ln) for nm, ln, _p in got]
            == [("Foo.bar", 2), ("Foo.nested", 3), ("baz", 5),
                ("priv_one", 6), ("nc_def", 7), ("in_block_comment", 10),
                ("with_apostrophe", 12), ("in_section", 14)],
            "got %s" % (got,))
        got2 = enumerate_decls("private noncomputable def pn : Nat := 1\n"
                               "protected theorem pt : True := trivial\n")
        vec("decl-enumeration-private-modifier-chain",
            got2 == [("pn", 1, True), ("pt", 2, False)],
            "got %s" % (got2,))

        # parse faces: the six classes plus attribution faces; blocks
        # attribute by NAME against the emitted probe list [(line, name)]
        # - the line numbers are bookkeeping only, never parsed
        rows = parse_print_axioms(LEAN_OUT_CLEAN, [(2, "t_clean")])
        vec("parse-clean", rows[0]["ok"] and rows[0]["axioms"] == [],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_THREE, [(2, "t_three")])
        vec("parse-benign-three",
            rows[0]["ok"] and rows[0]["axioms"] == list(BENIGN_STANDARD),
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SUBSET, [(2, "t_subset")])
        vec("parse-benign-subset",
            rows[0]["ok"] and rows[0]["axioms"] == ["propext"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SORRY, [(2, "t_sorry")])
        vec("parse-sorry", rows[0]["ok"] and rows[0]["axioms"] == ["sorryAx"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_CUSTOM, [(2, "t_custom")])
        vec("parse-custom",
            rows[0]["ok"] and rows[0]["axioms"] == ["my_axiom.rh"],
            "got %s" % (rows,))
        probes_mixed = [(2, "a"), (4, "b"), (6, "c"), (8, "d")]
        rows = parse_print_axioms(LEAN_OUT_MIXED, probes_mixed)
        ok = (len(rows) == 4 and rows[0]["ok"] and rows[0]["axioms"] == []
              and rows[1]["axioms"] == ["propext", "Classical.choice"]
              and rows[2]["axioms"] == ["sorryAx"]
              and rows[3]["axioms"] == ["my_ax", "propext"])
        vec("parse-mixed-attribution", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_MIXED, probes_mixed + [(10, "e")])
        ok = (rows[0]["ok"] and rows[3]["ok"]
              and not rows[4]["ok"]
              and "no probe block" in rows[4]["reason"])
        vec("parse-tail-no-block", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_GHOST, [(2, "t_ghost")])
        vec("parse-unknown-identifier",
            not rows[0]["ok"] and "unknown identifier" in rows[0]["raw"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_NAME_MISMATCH, [(2, "t_x")])
        vec("parse-name-mismatch",
            not rows[0]["ok"] and "probe block names" in rows[0]["reason"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_STRAY, [(2, "a")])
        vec("parse-stray-unknown-block-ignored",
            len(rows) == 1 and rows[0]["ok"] and rows[0]["axioms"] == [],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_DISPLACED, [(2, "a")])
        vec("parse-displaced-probed-name-guard",
            all(not r["ok"] for r in rows)
            and "does not correspond" in rows[0]["reason"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_ISOLATED,
                                  [(2, "a"), (4, "b"), (6, "c")])
        vec("parse-failed-probe-isolated",
            rows[0]["ok"] and rows[2]["ok"] and not rows[1]["ok"]
            and "unknown identifier" in rows[1]["reason"]
            and "unknown identifier" in rows[1]["raw"],
            "got %s" % (rows,))
        rows = parse_print_axioms("", [(3, "t_any")])
        vec("parse-empty-output-per-probe",
            not rows[0]["ok"]
            and "no probe block" in rows[0]["reason"],
            "got %s" % (rows,))

        # name-keyed parse faces: attribution keys the reported NAME
        # against the emitted probe list - the deliberately wrong probe
        # line numbers must not matter (the retired marker/line
        # bookkeeping never worked: lean echoes no comments)
        rows = parse_print_axioms(LEAN_OUT_NAMEKEY_FULL, NAMEKEY_PROBES)
        ok = ([r["ok"] for r in rows] == [True] * 5
              and [r["axioms"] for r in rows]
              == [[], list(BENIGN_STANDARD), ["sorryAx"], ["my_ax.rh"],
                  ["propext"]])
        vec("parse-namekey-all-classified", ok, "got %s" % (rows,))
        decls_nk = [("n_clean", 2, False), ("n_three", 4, False),
                    ("n_sorry", 6, False), ("n_custom", 8, False),
                    ("n_priv", 10, True)]
        rows = classify_decl_rows("x.lean", decls_nk, rows, [], "lake-env")
        vec("classify-namekey-all-five-classes",
            [r["classification"] for r in rows]
            == ["CLEAN", "BENIGN-STANDARD", "SORRY-ALARM",
                "CUSTOM-AXIOM-ALARM", PRIVATE_COVERED],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_NAMEKEY_MISSING, NAMEKEY_PROBES)
        ok = ([r["ok"] for r in rows]
              == [True, True, True, False, True]
              and "no probe block" in rows[3]["reason"]
              and rows[3]["raw"] != ""
              and all(r["ok"] for i, r in enumerate(rows) if i != 3))
        vec("parse-namekey-missing-one-no-cascade", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_NAMEKEY_MANGLED,
                                  [(99, "priv_one")])
        rows_c = classify_decl_rows("x.lean", [("priv_one", 5, True)],
                                    rows, [], "lake-env")
        vec("parse-namekey-mangled-suffix-fallback",
            rows[0]["ok"] and rows[0]["axioms"] == ["propext"]
            and rows_c[0]["classification"] == PRIVATE_COVERED,
            "got %s / %s" % (rows, rows_c))
        rows = parse_print_axioms(LEAN_OUT_NAMEKEY_MANGLED_AMBIG,
                                  [(99, "Foo.priv_bar"), (101, "priv_bar")])
        vec("parse-namekey-mangled-ambiguous-honest",
            all(not r["ok"] for r in rows)
            and all("ambiguous" in r["reason"] for r in rows),
            "got %s" % (rows,))
        r1 = parse_print_axioms(LEAN_OUT_NAMEKEY_FULL, NAMEKEY_PROBES)
        r2 = parse_print_axioms(LEAN_OUT_NAMEKEY_FULL, NAMEKEY_PROBES)
        vec("parse-namekey-determinism",
            json.dumps(r1, ensure_ascii=False)
            == json.dumps(r2, ensure_ascii=False),
            "double parse not byte-identical")

        # classify faces: precedence, whitelist, sorryAx never allowed
        vec("classify-clean", classify_axioms([], []) == ("CLEAN", [], []),
            "got %s" % (classify_axioms([], []),))
        vec("classify-wave2-three-axioms",
            classify_axioms(list(BENIGN_STANDARD), [])
            == ("BENIGN-STANDARD", [], []),
            "got %s" % (classify_axioms(list(BENIGN_STANDARD), []),))
        vec("classify-sorry-precedence",
            classify_axioms(["sorryAx", "my_ax"], ["my_ax"])
            == ("SORRY-ALARM", [], ["my_ax"]),
            "got %s" % (classify_axioms(["sorryAx", "my_ax"], ["my_ax"]),))
        vec("classify-sorry-custom-verbatim",
            classify_axioms(["sorryAx", "my_ax"], [])
            == ("SORRY-ALARM", ["my_ax"], []),
            "got %s" % (classify_axioms(["sorryAx", "my_ax"], []),))
        vec("classify-sorry-never-allowed",
            classify_axioms(["sorryAx"], ["sorryAx"])[0] == "SORRY-ALARM",
            "got %s" % (classify_axioms(["sorryAx"], ["sorryAx"]),))
        vec("classify-custom-verbatim",
            classify_axioms(["propext", "my_ax", "zz_ax"], [])
            == ("CUSTOM-AXIOM-ALARM", ["my_ax", "zz_ax"], []),
            "got %s" % (classify_axioms(["propext", "my_ax", "zz_ax"], []),))
        vec("classify-allow-fold",
            classify_axioms(["my_ax"], ["my_ax"])
            == ("BENIGN-STANDARD", [], ["my_ax"]),
            "got %s" % (classify_axioms(["my_ax"], ["my_ax"]),))

        # declaration-classification face: the PRIVATE-COVERED marker
        # class (private declarations probed through the copy-append
        # form), alarm precedence over the marker, and the design-4
        # private-plus-public offline fixture probed end to end
        decls_prec = [("p_sorry", 2, True), ("p_custom", 4, True),
                      ("p_ok", 6, True), ("pub", 8, False)]
        parsed_prec = [
            {"name": "p_sorry", "ok": True, "axioms": ["sorryAx"],
             "reason": "", "raw": ""},
            {"name": "p_custom", "ok": True, "axioms": ["my_ax"],
             "reason": "", "raw": ""},
            {"name": "p_ok", "ok": True, "axioms": [], "reason": "",
             "raw": ""},
            {"name": "pub", "ok": True, "axioms": [], "reason": "",
             "raw": ""},
        ]
        rows = classify_decl_rows("x.lean", decls_prec, parsed_prec, [],
                                  "lake-env")
        vec("private-alarm-precedence",
            [r["classification"] for r in rows]
            == ["SORRY-ALARM", "CUSTOM-AXIOM-ALARM", "PRIVATE-COVERED",
                "CLEAN"],
            "got %s" % (rows,))
        rows = classify_decl_rows(
            "x.lean", [("p_allow", 8, True)],
            [{"name": "p_allow", "ok": True, "axioms": ["my_ax"],
              "reason": "", "raw": ""}], ["my_ax"], "lake-env")
        vec("private-covered-allow-fold",
            rows[0]["classification"] == "PRIVATE-COVERED"
            and rows[0]["allowed"] == ["my_ax"]
            and rows[0]["axioms"] == ["my_ax"],
            "got %s" % (rows,))
        rows = classify_decl_rows("x.lean", [("u", 3, False)],
                                  [{"name": "u", "ok": False, "axioms": [],
                                    "reason": "boom", "raw": "boom"}],
                                  [], "lean-direct")
        vec("unparsed-single-row-isolation",
            rows[0]["classification"] == "UNPARSED"
            and rows[0]["unparsed_reason"] == "boom",
            "got %s" % (rows,))
        fixture_decls = enumerate_decls(PRIVATE_PUBLIC_LEAN)
        fixture_probes = build_copy_checker(
            PRIVATE_PUBLIC_LEAN, ["pub_one", "priv_one"])[1]
        answers = {"pub_one": "'pub_one' does not depend on any axioms",
                   "priv_one": "'priv_one' depends on axioms: [propext]"}
        fixture_out = "".join(
            "ck.lean:%d:0: info: %s\n" % (ln, answers[nm])
            for ln, nm in fixture_probes)
        rows = classify_decl_rows(
            "priv_pub.lean", fixture_decls,
            parse_print_axioms(fixture_out, fixture_probes), [],
            "lean-direct")
        vec("private-covered-fixture",
            [r["classification"] for r in rows]
            == ["CLEAN", "PRIVATE-COVERED"]
            and rows[1]["axioms"] == ["propext"]
            and rows[1]["private"] is True
            and rows[0]["private"] is False,
            "got %s" % (rows,))

        # checker emission and module derivation: the import form is the
        # FALLBACK face (cross-file aggregated sweeps only), pinned
        # verbatim; the copy-append form is the primary face
        checker = build_checker("My.Mod", ["a", "b"])
        vec("checker-emission",
            checker == "import My.Mod\n\n#print axioms a\n#print axioms b\n",
            "got %r" % checker)
        vec("checker-no-module",
            build_checker("", ["x"]) == "\n#print axioms x\n",
            "got %r" % build_checker("", ["x"]))
        checker_ca, probes_ca = build_copy_checker(
            PRIVATE_PUBLIC_LEAN, ["pub_one", "priv_one"])
        vec("copy-append-emission",
            checker_ca == (
                PRIVATE_PUBLIC_LEAN
                + "\n#print axioms pub_one -- rocqwash-probe pub_one\n"
                + "#print axioms priv_one -- rocqwash-probe priv_one\n")
            and probes_ca == [(5, "pub_one"), (6, "priv_one")],
            "got %r / %s" % (checker_ca, probes_ca))
        checker_empty, probes_empty = build_copy_checker("", ["x"])
        vec("copy-append-empty-file",
            checker_empty == "\n#print axioms x -- rocqwash-probe x\n"
            and probes_empty == [(2, "x")],
            "got %r / %s" % (checker_empty, probes_empty))
        proj = os.path.join(tmp, "proj")
        src = os.path.join(proj, "src", "My")
        os.makedirs(src)
        with open(os.path.join(proj, "lakefile.toml"), "wb"):
            pass
        with open(os.path.join(src, "Mod.lean"), "wb"):
            pass
        module, root = derive_module(os.path.join(src, "Mod.lean"))
        vec("module-derivation-src",
            module == "My.Mod" and os.path.samefile(root, proj),
            "got module=%r root=%r" % (module, root))
        module2, root2 = derive_module(os.path.join(tmp, "bare.lean"))
        vec("module-derivation-bare",
            module2 == "bare" and root2 is None,
            "got module=%r root=%r" % (module2, root2))

        # report schema shape over canned rows (offline, no toolchain)
        canned_files = [{"file": "a.lean", "declarations": 2,
                         "module": "A", "probe": "lean-direct",
                         "form": "copy-append",
                         "rc": 0, "error_tail": []}]
        canned_decls = [
            {"file": "a.lean", "line": 2, "name": "t_one",
             "classification": "CLEAN", "axioms": [], "custom": [],
             "allowed": [], "private": False, "probe": "lean-direct",
             "raw": "", "unparsed_reason": ""},
            {"file": "a.lean", "line": 5, "name": "t_two",
             "classification": "SORRY-ALARM", "axioms": ["sorryAx"],
             "custom": [], "allowed": [], "private": False,
             "probe": "lean-direct",
             "raw": "", "unparsed_reason": ""},
        ]
        rep = build_report("TMP", canned_files, canned_decls, [],
                           [], {"lean": None, "lake": None,
                                "usable_lean": False, "usable_lake": False})
        bare = [k for k in rep
                if k not in ("scan_face", "schema")
                and not (isinstance(rep[k], dict)
                         and "value" in rep[k] and "basis" in rep[k])]
        vec("schema-value-basis", bare == [], "bare keys: %s" % bare)
        face = rep["scan_face"]
        vec("scan-face-fields",
            sorted(face) == ["equivalents", "negative_finding",
                             "not_scanned", "scanned"],
            "got %s" % (sorted(face),))
        vec("scan-face-verbatim",
            face.get("scanned") == SCAN_SCANNED
            and face.get("not_scanned") == SCAN_NOT_SCANNED
            and face.get("negative_finding") == SCAN_NEGATIVE_FINDING
            and face.get("equivalents") == SCAN_EQUIVALENTS
            and "line-start" in SCAN_EQUIVALENTS,
            "scan_face strings drifted from the constants")
        vec("verdict-red-face", rep["verdict"]["value"] == "RED"
            and exit_code_for(rep) == 1,
            "got %s / %s" % (rep["verdict"]["value"], exit_code_for(rep)))
        clean_decls = [dict(canned_decls[0], name="t_one")]
        rep2 = build_report("TMP", canned_files, clean_decls, [], [], {})
        vec("verdict-pass-face", rep2["verdict"]["value"] == "PASS"
            and exit_code_for(rep2) == 0,
            "got %s / %s" % (rep2["verdict"]["value"], exit_code_for(rep2)))
        vec("error-forces-red-exit",
            exit_code_for(build_report("TMP", canned_files, clean_decls,
                                       ["read a.lean: boom"], [], {})) == 1,
            "errors must force exit 1")
        vec("unparsed-forces-red",
            build_report("TMP", canned_files,
                         [dict(clean_decls[0],
                               classification="UNPARSED")], [], [],
                         {})["verdict"]["value"] == "RED",
            "unjudgeable is not green")
        three_decls = [
            dict(clean_decls[0], name="t_std",
                 classification="BENIGN-STANDARD",
                 axioms=list(BENIGN_STANDARD)),
        ]
        rep3 = build_report("TMP", canned_files, three_decls, [], [], {})
        vec("wave2-three-axioms-benign",
            rep3["benign_standard"]["value"] == 1
            and rep3["custom_axiom_names"]["value"] == []
            and rep3["verdict"]["value"] == "PASS",
            "got %s" % (rep3["benign_standard"],))
        priv_decls = [dict(clean_decls[0], name="t_priv",
                           classification="PRIVATE-COVERED",
                           axioms=["propext"], private=True)]
        rep4 = build_report("TMP", canned_files, priv_decls, [], [], {})
        vec("private-covered-report-face",
            rep4["private_covered"]["value"] == 1
            and rep4["classified"]["value"] == 1
            and rep4["verdict"]["value"] == "PASS"
            and exit_code_for(rep4) == 0,
            "got %s / %s" % (rep4["private_covered"], rep4["classified"]))
        payload = json.dumps(rep, ensure_ascii=False)
        vec("single-line-json", "\n" not in payload, "payload holds a newline")
        json_path = os.path.join(tmp, "out.json")
        write_json(json_path, payload)
        with open(json_path, "r", encoding="utf-8") as fh:
            round_trip = json.load(fh)
        vec("json-round-trip", round_trip == rep, "payload mismatch")

        # closure snapshot + diff faces: pure functions over canned rows,
        # offline, zero toolchain launch (the diff face reads only the two
        # snapshots' data, so toolchain independence is by construction)
        def mk_row(name, klass, axioms, file="a.lean", line=1,
                   private=False):
            return {"file": file, "line": line, "name": name,
                    "classification": klass, "axioms": list(axioms),
                    "custom": [], "allowed": [], "private": private,
                    "probe": "lean-direct",
                    "raw": "", "unparsed_reason": ""}

        base_rows = [
            mk_row("t_unchanged", "CLEAN", [], line=2),
            mk_row("t_changed", "BENIGN-STANDARD", ["propext"], line=5),
            mk_row("t_lost", "CLEAN", [], line=7),
            mk_row("t_newdep", "CLEAN", [], line=9),
        ]
        cur_rows = [
            mk_row("t_unchanged", "CLEAN", [], line=2),
            mk_row("t_changed", "BENIGN-STANDARD",
                   ["propext", "Classical.choice"], line=5),
            mk_row("t_new", "CLEAN", [], file="b.lean", line=4),
            mk_row("t_newdep", "SORRY-ALARM", ["sorryAx"], line=9),
        ]

        # snapshot determinism: shuffled input rows must give
        # byte-identical snapshots (the sort normalizes the order)
        snap1 = build_snapshot("TMP", base_rows, [])
        snap2 = build_snapshot("TMP", list(reversed(base_rows)), [])
        vec("snapshot-determinism",
            json.dumps(snap1, ensure_ascii=False)
            == json.dumps(snap2, ensure_ascii=False),
            "shuffled input rows changed the snapshot bytes")
        vec("snapshot-shape",
            snap1["schema"] == SNAPSHOT_SCHEMA
            and snap1["tool"] == TOOL
            and [d["name"] for d in snap1["declarations"]]
                == ["t_changed", "t_lost", "t_newdep", "t_unchanged"]
            and snap1["declaration_count"] == 4
            and snap1["classified_count"] == 4
            and snap1["unparsed_count"] == 0
            and snap1["unparsed_names"] == [],
            "got %s" % (snap1,))
        snap3 = build_snapshot("TMP", [
            mk_row("t_a", "BENIGN-STANDARD",
                   ["propext", "Classical.choice"], line=2),
            mk_row("t_u", "UNPARSED", [], line=4),
        ], [])
        vec("snapshot-axioms-sorted-unparsed-honest",
            snap3["declarations"][0]["axioms"]
            == ["Classical.choice", "propext"]
            and snap3["declaration_count"] == 2
            and snap3["classified_count"] == 1
            and snap3["unparsed_count"] == 1
            and snap3["unparsed_names"] == ["t_u"]
            and all(d["name"] != "t_u" for d in snap3["declarations"]),
            "got %s" % (snap3,))
        snap_pc = build_snapshot("TMP", [
            mk_row("t_priv", "PRIVATE-COVERED", ["propext"], line=3,
                   private=True)], [])
        vec("snapshot-private-covered-closure",
            snap_pc["classified_count"] == 1
            and snap_pc["unparsed_count"] == 0
            and snap_pc["declarations"][0]["classification"]
                == "PRIVATE-COVERED"
            and snap_pc["declarations"][0]["axioms"] == ["propext"],
            "got %s" % (snap_pc,))

        # diff faces: all four verdict kinds in one pair
        base_snap = build_snapshot("BASE", base_rows, [])
        cur_snap = build_snapshot("CUR", cur_rows, [])
        diff = diff_closures(base_snap, cur_snap)
        by_verdict = {}
        for row in diff["rows"]:
            by_verdict.setdefault(row["verdict"], []).append(row["name"])
        vec("diff-all-four-verdicts",
            sorted(by_verdict.get(DIFF_UNCHANGED, [])) == ["t_unchanged"]
            and sorted(by_verdict.get(DIFF_CHANGED, []))
                == ["t_changed", "t_newdep"]
            and by_verdict.get(DIFF_NEW, []) == ["t_new"]
            and by_verdict.get(DIFF_LOST, []) == ["t_lost"],
            "got %s" % (by_verdict,))
        changed_row = next(r for r in diff["rows"]
                           if r["name"] == "t_changed")
        vec("diff-changed-from-to-listed",
            changed_row["verdict"] == DIFF_CHANGED
            and changed_row["from_axioms"] == ["propext"]
            and changed_row["to_axioms"] == ["Classical.choice", "propext"]
            and changed_row["from_classification"] == "BENIGN-STANDARD"
            and changed_row["to_classification"] == "BENIGN-STANDARD"
            and changed_row["new_dependency"] is False,
            "got %s" % (changed_row,))
        newdep_row = next(r for r in diff["rows"] if r["name"] == "t_newdep")
        vec("diff-new-dependency-alarm-true",
            newdep_row["new_dependency"] is True
            and diff["new_dependency_names"] == ["t_newdep"]
            and diff["summary"]["new_dependency"]["value"] == 1
            and diff["diff_alarm"]["value"] is True
            and diff["diff_alarm"]["basis"] == DIFF_BASIS_ALARM,
            "got %s / %s" % (newdep_row, diff["diff_alarm"]))
        vec("diff-summary-shape",
            diff["summary"]["unchanged"]["value"] == 1
            and diff["summary"]["axiom_set_changed"]["value"] == 2
            and diff["summary"]["new_theorem"]["value"] == 1
            and diff["summary"]["lost_theorem"]["value"] == 1
            and all(set(v) == {"value", "basis"}
                    for v in diff["summary"].values()),
            "got %s" % (diff["summary"],))
        vec("diff-rows-sorted-by-name",
            [r["name"] for r in diff["rows"]]
            == sorted(r["name"] for r in diff["rows"]),
            "got %s" % ([r["name"] for r in diff["rows"]],))
        calm = diff_closures(base_snap, build_snapshot("CUR", base_rows + [
            mk_row("t_extra", "CLEAN", [], file="c.lean", line=1)], []))
        vec("diff-alarm-false-face",
            calm["diff_alarm"]["value"] is False
            and calm["summary"]["axiom_set_changed"]["value"] == 0
            and calm["summary"]["new_dependency"]["value"] == 0
            and calm["summary"]["new_theorem"]["value"] == 1,
            "got %s" % (calm["diff_alarm"],))
        same = diff_closures(base_snap, build_snapshot("BASE", base_rows, []))
        vec("diff-identical-all-unchanged",
            len(same["rows"]) == 4
            and all(r["verdict"] == DIFF_UNCHANGED for r in same["rows"])
            and same["diff_alarm"]["value"] is False
            and same["summary"]["unchanged"]["value"] == 4,
            "got %s" % (same["rows"],))

        # baseline load faces: missing, unparseable, wrong-schema, and the
        # write/read round trip
        bad_json_path = os.path.join(tmp, "bad.json")
        with open(bad_json_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json")
        err_bad = load_snapshot(bad_json_path)[1]
        vec("baseline-load-bad-json",
            err_bad is not None and "not valid JSON" in err_bad,
            "got %r" % (err_bad,))
        err_absent = load_snapshot(os.path.join(tmp, "absent.json"))[1]
        vec("baseline-load-absent",
            err_absent is not None and "cannot read" in err_absent,
            "got %r" % (err_absent,))
        wrong_path = os.path.join(tmp, "wrong.json")
        write_json(wrong_path, json.dumps({"schema": SCHEMA},
                                          ensure_ascii=False))
        err_wrong = load_snapshot(wrong_path)[1]
        vec("baseline-load-wrong-schema",
            err_wrong is not None and SNAPSHOT_SCHEMA in err_wrong
            and SCHEMA in err_wrong,
            "got %r" % (err_wrong,))
        good_path = os.path.join(tmp, "good.json")
        write_json(good_path, json.dumps(base_snap, ensure_ascii=False))
        loaded, err_load = load_snapshot(good_path)
        vec("baseline-load-round-trip",
            err_load is None and loaded == base_snap,
            "got %r" % (err_load,))

        # report faces: no --baseline leaves the shape untouched (backward
        # compatible); a diff face attaches {value, basis}-wrapped
        rep_nodiff = build_report("TMP", canned_files, clean_decls, [], [],
                                  {})
        vec("no-baseline-backward-compat",
            "closure_diff" not in rep_nodiff
            and "diff_alarm" not in rep_nodiff
            and rep_nodiff["verdict"]["value"] == "PASS"
            and exit_code_for(rep_nodiff) == 0,
            "got keys %s" % (sorted(rep_nodiff),))
        rep_diff = attach_closure_diff(
            build_report("TMP", canned_files, clean_decls, [], [], {}),
            diff)
        bare_diff = [k for k in rep_diff
                     if k not in ("scan_face", "schema")
                     and not (isinstance(rep_diff[k], dict)
                              and "value" in rep_diff[k]
                              and "basis" in rep_diff[k])]
        vec("diff-report-value-basis-wrap",
            bare_diff == []
            and rep_diff["closure_diff"]["value"] is diff
            and rep_diff["diff_alarm"]["value"] is True,
            "bare keys: %s" % bare_diff)
        vec("build-report-diff-face-param",
            "closure_diff" in build_report("TMP", canned_files, clean_decls,
                                           [], [], {}, diff_face=diff)
            and "closure_diff" in build_report("TMP", canned_files,
                                               clean_decls, [], [], {},
                                               diff_face=calm),
            "build_report must accept and attach a diff face")

        # closure flag face: --snapshot/--baseline parse as values
        parsed_flags = build_parser().parse_args(
            ["--root", "x", "--snapshot", "s.json", "--baseline", "b.json"])
        vec("closure-flag-face",
            parsed_flags.snapshot == "s.json"
            and parsed_flags.baseline == "b.json",
            "got %r %r" % (parsed_flags.snapshot, parsed_flags.baseline))

        # flag face: --selftest parses standalone; usage faces rc 2
        vec("selftest-flag-face",
            build_parser().parse_args(["--selftest"]).selftest is True
            and build_parser().parse_args([]).selftest is False,
            "--selftest defaults to False and parses without --root")

        def spawn(argv, env=None, cwd=None):
            try:
                p = subprocess.run([sys.executable, "-I", "-B", script]
                                   + argv, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=120,
                                   env=env, cwd=cwd)
            except subprocess.TimeoutExpired:
                return None, "", "timeout"
            out = p.stdout.decode("utf-8", "replace")
            errout = p.stderr.decode("utf-8", "replace")
            return p.returncode, out, errout

        rc, _out, _err = spawn([])
        vec("exit-usage-no-root-rc2", rc == 2,
            "no arguments exits %s (usage error)" % rc)
        rc, _out, _err = spawn(["--root", os.path.join(tmp, "absent")])
        vec("exit-root-absent-rc2", rc == 2,
            "absent --root exits %s (usage error)" % rc)
        rc, _out, _err = spawn(["--selftest", "--snapshot",
                                os.path.join(tmp, "s.json")])
        vec("exit-selftest-with-snapshot-rc2", rc == 2,
            "--selftest with a scan flag exits %s (usage error)" % rc)

        # gate vector: child PATH stripped to an empty directory -> 112.
        # Runs on every host: absence is forced by the stripped child
        # environment, so the vector exercises the gate whether or not the
        # host toolchain is present; a host where stripping cannot force
        # absence reports red instead of passing dishonestly.
        fixture_dir = os.path.join(tmp, "fixture")
        os.makedirs(fixture_dir)
        with open(os.path.join(fixture_dir, "t.lean"), "wb") as fh:
            fh.write(b"theorem t_one : True := trivial\n")
        empty_dir = os.path.join(tmp, "empty_path")
        os.makedirs(empty_dir)
        gate_env = dict(os.environ)
        gate_env["PATH"] = empty_dir
        rc, out, err = spawn(["--root", fixture_dir],
                             env=gate_env, cwd=empty_dir)
        vec("gate-no-toolchain-rc112",
            rc == 112 and out.strip() == ""
            and "toolchain" in err,
            "rc=%s stdout=%r stderr=%r" % (rc, out[:120], err[:200]))

        # toolchain pin gate faces (offline: pure resolution, parse,
        # decision and shape vectors over temporary fixtures plus the
        # stripped-environment spawn faces; zero network, zero toolchain
        # launch, zero real-repo touch)
        pin_root = os.path.join(tmp, "pinrepo")
        pin_sub = os.path.join(pin_root, "Sub", "Deep")
        os.makedirs(pin_sub)
        with open(os.path.join(pin_root, "lean-toolchain"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("leanprover/lean4:v4.33.1\n")
        got_pin, got_dir, got_err = find_lean_pin(
            os.path.join(pin_sub, "M.lean"))
        vec("pin-discovery-upward-file-root",
            got_pin == "leanprover/lean4:v4.33.1" and got_err is None
            and os.path.samefile(got_dir, pin_root),
            "got %r %r %r" % (got_pin, got_dir, got_err))
        got_pin_d, got_dir_d, got_err_d = find_lean_pin(pin_sub)
        vec("pin-discovery-directory-root",
            got_pin_d == "leanprover/lean4:v4.33.1" and got_err_d is None
            and os.path.samefile(got_dir_d, pin_root),
            "got %r %r %r" % (got_pin_d, got_dir_d, got_err_d))
        pin_nested = os.path.join(pin_sub, "lean-toolchain")
        with open(pin_nested, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("leanprover/lean4:v4.34.1\n")
        got_pin_n, got_dir_n, got_err_n = find_lean_pin(
            os.path.join(pin_sub, "M.lean"))
        vec("pin-discovery-nearest-wins",
            got_pin_n == "leanprover/lean4:v4.34.1" and got_err_n is None
            and os.path.samefile(got_dir_n, pin_sub),
            "got %r %r %r" % (got_pin_n, got_dir_n, got_err_n))
        os.remove(pin_nested)
        no_pin_root = os.path.join(tmp, "nopin")
        os.makedirs(no_pin_root)
        got_pin_0, got_dir_0, got_err_0 = find_lean_pin(no_pin_root)
        vec("pin-discovery-none",
            got_pin_0 is None and got_dir_0 is None and got_err_0 is None,
            "got %r %r %r" % (got_pin_0, got_dir_0, got_err_0))
        empty_pin = os.path.join(no_pin_root, "lean-toolchain")
        with open(empty_pin, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n")
        _got_pin_e, _got_dir_e, got_err_e = find_lean_pin(no_pin_root)
        vec("pin-discovery-empty-file-refused",
            got_err_e is not None and "empty pin file" in got_err_e,
            "got %r" % (got_err_e,))
        os.remove(empty_pin)
        names = parse_toolchain_list(
            "leanprover/lean4:v4.33.1 (default)\n"
            "leanprover/lean4:v4.34.1\n"
            "\n"
            "v4.35.0-rc3 (overridden by 'leanprover/lean4:v4.33.1')\n")
        vec("elan-list-parse-annotations-stripped",
            names == ["leanprover/lean4:v4.33.1",
                      "leanprover/lean4:v4.34.1", "v4.35.0-rc3"],
            "got %s" % (names,))
        vec("pin-decision-membership",
            "leanprover/lean4:v4.33.1" in names
            and "leanprover/lean4:v9.9.9" not in names
            and parse_toolchain_list("") == [],
            "got %s" % (names,))
        vec("pin-version-extraction",
            pin_version_of("leanprover/lean4:v4.33.1") == "4.33.1"
            and pin_version_of("v4.35.0-rc3") == "4.35.0-rc3",
            "got %r %r" % (pin_version_of("leanprover/lean4:v4.33.1"),
                           pin_version_of("v4.35.0-rc3")))
        vec("lean-version-token-parse",
            lean_version_of("Lean (version 4.33.1,"
                            " x86_64-w64-windows-gnu, commit abc,"
                            " Release)") == "4.33.1"
            and lean_version_of("not a version line") is None,
            "got %r" % (lean_version_of("not a version line"),))
        vec("lake-version-token-parse",
            lake_version_of("Lake version 5.0.0-src+5045d00 (Lean version"
                            " 4.34.1)") == "4.34.1"
            and lake_version_of("Lake version 5.0.0") is None,
            "got %r" % (lake_version_of("Lake version 5.0.0"),))
        base_env = {"PATH": "x", "LEAN_TOOLCHAIN": "stale"}
        injected = build_probe_env(base_env, "leanprover/lean4:v4.34.1")
        vec("env-injection-pin",
            injected["LEAN_TOOLCHAIN"] == "leanprover/lean4:v4.34.1"
            and injected["PATH"] == "x" and injected is not base_env,
            "got %s" % (injected,))
        passthrough = build_probe_env(base_env, None)
        vec("env-passthrough-no-pin",
            passthrough is base_env
            and passthrough["LEAN_TOOLCHAIN"] == "stale",
            "got %s" % (passthrough,))
        rep_pin = build_report("TMP", canned_files, clean_decls, [], [],
                               {"lean": "lean", "lake": "lake",
                                "usable_lean": True, "usable_lake": True,
                                "pin": "leanprover/lean4:v4.33.1",
                                "target_pin": "leanprover/lean4:v4.33.1",
                                "match": True})
        tf = rep_pin["toolchain"]["value"]
        vec("toolchain-block-pin-fields",
            tf["pin"] == "leanprover/lean4:v4.33.1"
            and tf["target_pin"] == "leanprover/lean4:v4.33.1"
            and tf["match"] is True,
            "got %s" % (tf,))
        rep_nopin = build_report("TMP", canned_files, clean_decls, [], [],
                                 {"lean": "lean", "lake": "lake",
                                  "usable_lean": True, "usable_lake": True,
                                  "pin": None, "target_pin": None,
                                  "match": None})
        tf0 = rep_nopin["toolchain"]["value"]
        vec("toolchain-block-no-pin-fields",
            tf0["pin"] is None and tf0["target_pin"] is None
            and tf0["match"] is None,
            "got %s" % (tf0,))
        doc = build_doctor("R", "leanprover/lean4:v9.9.9", "D", None,
                           ["leanprover/lean4:v4.33.1"], None, False,
                           "lean", "lake", "4.33.1", "4.33.1")
        doc_bare = [k for k in doc
                    if k != "schema"
                    and not (isinstance(doc[k], dict)
                             and "value" in doc[k] and "basis" in doc[k])]
        vec("doctor-shape-value-basis",
            doc_bare == [] and doc["schema"] == DOCTOR_SCHEMA
            and doc["verdict"]["value"] == "pin-missing"
            and doc["match"]["value"] is False
            and doc["install_command"]["value"]
                == "elan toolchain install leanprover/lean4:v9.9.9",
            "bare keys: %s / %s" % (doc_bare, doc["verdict"]))
        doc_ok = build_doctor("R", "leanprover/lean4:v4.33.1", "D", None,
                              ["leanprover/lean4:v4.33.1"], None, True,
                              "lean", "lake", "4.33.1", "4.33.1")
        vec("doctor-matched-face",
            doc_ok["verdict"]["value"] == "matched"
            and doc_ok["match"]["value"] is True
            and doc_ok["install_command"]["value"] is None
            and doc_ok["installed"]["value"]
                == ["leanprover/lean4:v4.33.1"],
            "got %s" % (doc_ok,))
        doc_np = build_doctor("R", None, None, None, None, None, False,
                              None, None, None, None)
        vec("doctor-no-pin-face",
            doc_np["verdict"]["value"] == "no-pin"
            and doc_np["match"]["value"] is None
            and doc_np["install_command"]["value"] is None
            and doc_np["target_pin"]["value"] is None,
            "got %s" % (doc_np,))
        doc_uv = build_doctor("R", "leanprover/lean4:v4.33.1", "D", None,
                              None, "elan not found on PATH", False,
                              "lean", "lake", None, None)
        vec("doctor-unverifiable-face",
            doc_uv["verdict"]["value"] == "pin-unverifiable"
            and doc_uv["installed"]["value"] is None
            and "elan not found" in doc_uv["installed"]["basis"]
            and doc_uv["match"]["value"] is False
            and doc_uv["install_command"]["value"]
                == "elan toolchain install leanprover/lean4:v4.33.1",
            "got %s" % (doc_uv,))
        doc_ep = build_doctor("R", None, "D", "empty pin file x", None,
                              None, False, "lean", "lake", None, None)
        vec("doctor-empty-pin-refused",
            doc_ep["verdict"]["value"] == "pin-unverifiable"
            and "empty pin file" in doc_ep["target_pin"]["basis"]
            and doc_ep["install_command"]["value"] is None,
            "got %s" % (doc_ep,))

        # pin-gate spawn faces on the stripped environment (host
        # independent: the stripped child PATH forces the pin
        # unverifiable, so the gate refuses through the pin face with the
        # doctor block on stdout; a host where stripping cannot force
        # the refusal reports red instead of passing dishonestly)
        pin_fixture = os.path.join(tmp, "pinfixture")
        os.makedirs(pin_fixture)
        with open(os.path.join(pin_fixture, "lean-toolchain"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("leanprover/lean4:v9.9.9\n")
        with open(os.path.join(pin_fixture, "t.lean"), "wb") as fh:
            fh.write(b"theorem t_one : True := trivial\n")

        def parse_first_json_line(text):
            for ln in text.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    return json.loads(ln)
                except ValueError:
                    return None
            return None

        rc, out, err = spawn(["--root", pin_fixture], env=gate_env,
                             cwd=empty_dir)
        doc_line = parse_first_json_line(out)
        vec("pin-missing-rc112-doctor-stdout",
            rc == 112 and doc_line is not None
            and doc_line.get("schema") == DOCTOR_SCHEMA
            and doc_line.get("target_pin", {}).get("value")
                == "leanprover/lean4:v9.9.9"
            and doc_line.get("match", {}).get("value") is False
            and doc_line.get("install_command", {}).get("value")
                == "elan toolchain install leanprover/lean4:v9.9.9"
            and "elan toolchain install leanprover/lean4:v9.9.9" in err
            and "zero rows" in err,
            "rc=%s out=%r err=%r" % (rc, out[:200], err[:200]))
        rc, out, err = spawn(["--toolchain-doctor", "--root", pin_fixture],
                             env=gate_env, cwd=empty_dir)
        doc_line2 = parse_first_json_line(out)
        vec("doctor-flag-exit-zero-stripped-env",
            rc == 0 and doc_line2 is not None
            and doc_line2.get("schema") == DOCTOR_SCHEMA
            and doc_line2.get("verdict", {}).get("value")
                == "pin-unverifiable"
            and doc_line2.get("install_command", {}).get("value")
                == "elan toolchain install leanprover/lean4:v9.9.9",
            "rc=%s out=%r err=%r" % (rc, out[:200], err[:200]))
        rc, _out, _err = spawn(["--toolchain-doctor"], env=gate_env,
                               cwd=empty_dir)
        vec("exit-doctor-no-root-rc2", rc == 2,
            "--toolchain-doctor without --root exits %s (usage error)"
            % rc)
        rc, _out, _err = spawn(["--toolchain-doctor", "--selftest"],
                               env=gate_env, cwd=empty_dir)
        vec("exit-doctor-with-selftest-rc2", rc == 2,
            "--toolchain-doctor with --selftest exits %s (usage error)"
            % rc)
        parsed_flags = build_parser().parse_args(
            ["--root", "x", "--toolchain-doctor"])
        vec("doctor-flag-face",
            parsed_flags.toolchain_doctor is True
            and build_parser().parse_args([]).toolchain_doctor is False,
            "--toolchain-doctor defaults to False and parses with --root")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[SELFTEST] %s %s: %d vector(s), %d fail"
          % (TOOL, "green" if not fails else "red", total[0], len(fails)))
    if fails:
        print("[SELFTEST] red vectors: %s" % ", ".join(fails))
        return 1
    return 0


def build_parser():
    """The flag face; extracted so --selftest runs standalone (no --root
    required) and the usage face stays single-source."""
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="per-theorem axiom-closure classifier for Lean claim"
                    " audits (one JSON line; rc 112 without a usable"
                    " Lean toolchain)")
    ap.add_argument("--root", metavar="FILE|DIR",
                    help="target .lean file or directory (required unless"
                         " --selftest)")
    ap.add_argument("--json", metavar="OUT",
                    help="write the stdout JSON payload to OUT as well")
    ap.add_argument("--snapshot", metavar="OUT",
                    help="additionally write a machine closure snapshot"
                         " (schema %s) of the sweep to OUT: per classified"
                         " declaration the full probe name, the sorted"
                         " axiom set and the class; deterministic (sorted,"
                         " double-run byte-identical) and"
                         " toolchain-independent" % SNAPSHOT_SCHEMA)
    ap.add_argument("--baseline", metavar="SNAPSHOT",
                    help="diff the current closure against this previously"
                         " written snapshot file (schema %s) and add the"
                         " closure_diff block plus the top-level diff_alarm"
                         " flag; the diff reads only the two snapshots'"
                         " data, no Lean needed (the beyond-platform"
                         " closure-evolution audit face)"
                         % SNAPSHOT_SCHEMA)
    ap.add_argument("--toolchain-doctor", action="store_true",
                    dest="toolchain_doctor",
                    help="print the standalone toolchain resolution-chain"
                         " report (schema %s: lean/lake resolved paths"
                         " and versions, the target lean-toolchain pin,"
                         " the match verdict, the elan installed-list"
                         " excerpt, the exact install command when the"
                         " pin is missing; every field {value, basis})"
                         " and exit 0 always - the diagnostic face, it"
                         " judges nothing" % DOCTOR_SCHEMA)
    ap.add_argument("--allow-axiom", action="append", default=[],
                    dest="allow_axioms",
                    help="extra axiom name admitted into BENIGN-STANDARD"
                         " (repeatable; sorryAx is never admitted)")
    ap.add_argument("--timeout", type=int, default=PROBE_TIMEOUT_DEFAULT,
                    help="per-probe subprocess timeout seconds"
                         " (default %d)" % PROBE_TIMEOUT_DEFAULT)
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group and exit")
    return ap


def run_toolchain_doctor(root):
    """The --toolchain-doctor diagnostic face: resolve the pin chain
    (target pin, elan installed list, match verdict, effective versions
    under the resolution in force) and print one doctor JSON line;
    exit 0 always (it judges nothing and touches nothing)."""
    pin, pin_dir, pin_err = find_lean_pin(root)
    installed, elan_err = None, None
    honored = False
    if pin and not pin_err:
        installed, elan_err = read_installed_toolchains()
        honored = installed is not None and pin in installed
    lean = shutil.which("lean")
    lake = shutil.which("lake")
    if honored:
        probe_cwd, probe_env = pin_dir, build_probe_env(os.environ, pin)
    else:
        probe_cwd, probe_env = None, os.environ
    lv, _lv_err = probe_version_output(lean, cwd=probe_cwd, env=probe_env)
    kv, _kv_err = probe_version_output(lake, cwd=probe_cwd, env=probe_env)
    doctor = build_doctor(root, pin, pin_dir, pin_err, installed, elan_err,
                          honored, lean, lake, lean_version_of(lv),
                          lake_version_of(kv))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(doctor, ensure_ascii=False))
    sys.stderr.write("TOOLCHAIN-DOCTOR: verdict=%s pin=%s\n"
                     % (doctor["verdict"]["value"],
                        doctor["target_pin"]["value"]))
    return EXIT_OK


def pin_gate_skip(root, pin, pin_dir, pin_err, installed, elan_err):
    """The pin-gate honest skip face: the doctor block on stdout (the
    upgrade the pin face carries: the exact one-line fix and the
    judged-zero-rows disclosure), the SKIP line on stderr, rc 112.  The
    effective versions are probed on the PATH default resolution on
    purpose: that is the version the sweep would have drifted to without
    this gate, and the doctor records it as evidence."""
    lean = shutil.which("lean")
    lake = shutil.which("lake")
    lv, _e1 = probe_version_output(lean)
    kv, _e2 = probe_version_output(lake)
    doctor = build_doctor(root, pin, pin_dir, pin_err, installed, elan_err,
                          False, lean, lake, lean_version_of(lv),
                          lake_version_of(kv))
    if pin_err:
        reason = pin_err
    elif elan_err:
        reason = ("the elan installed list is unavailable (%s); the pin"
                  " cannot be verified" % elan_err)
    else:
        reason = "toolchain %s is not in the elan installed list" % pin
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(doctor, ensure_ascii=False))
    fix = doctor["install_command"]["value"]
    fix_line = ("; fix: %s" % fix) if fix else ""
    sys.stderr.write(
        "SKIP: the target lean-toolchain pin cannot be honored (%s)%s;"
        " the axiom sweep honestly skips and judges nothing, zero rows"
        " judged (rc %d)\n" % (reason, fix_line, EXIT_NO_TOOLCHAIN))
    return EXIT_NO_TOOLCHAIN


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2/112)."""
    args = build_parser().parse_args(argv)
    if args.selftest:
        if (args.root or args.json or args.snapshot or args.baseline
                or args.toolchain_doctor):
            build_parser().error("--selftest runs standalone; combine it"
                                 " with no scan flags")
        return selftest()
    if not args.root:
        build_parser().error("--root is required unless --selftest is"
                             " given")
    if not os.path.exists(args.root):
        sys.stderr.write("%s: --root does not exist: %s\n"
                         % (TOOL, args.root))
        return EXIT_USAGE
    if args.toolchain_doctor:
        if (args.json or args.snapshot or args.baseline or args.allow_axioms
                or args.timeout != PROBE_TIMEOUT_DEFAULT):
            build_parser().error("--toolchain-doctor runs standalone;"
                                 " combine it with no scan flags")
        return run_toolchain_doctor(args.root)
    if args.timeout < 1:
        build_parser().error("--timeout must be >= 1")
    # --baseline is validated up front (a missing, unparseable or
    # wrong-schema file is a usage error, fail fast before any probing).
    baseline_snap = None
    if args.baseline:
        baseline_snap, baseline_err = load_snapshot(args.baseline)
        if baseline_err is not None:
            sys.stderr.write("%s: %s\n" % (TOOL, baseline_err))
            return EXIT_USAGE
    # Toolchain pin gate: resolve the target's lean-toolchain pin before
    # any probing; a pin that cannot be honored refuses the run (rc 112
    # with the doctor block on stdout) instead of drifting to the PATH
    # default (an axiom set can drift across toolchain versions).
    pin, pin_dir, pin_err = find_lean_pin(args.root)
    installed, elan_err = None, None
    honored = False
    if pin and not pin_err:
        installed, elan_err = read_installed_toolchains()
        honored = installed is not None and pin in installed
    if pin_err or (pin and not honored):
        return pin_gate_skip(args.root, pin, pin_dir, pin_err, installed,
                             elan_err)
    gate = None
    probe_env = os.environ
    if pin:
        probe_env = build_probe_env(os.environ, pin)
        gate = probe_toolchain(cwd=pin_dir, env=probe_env)
        if not (gate[2] or gate[3]):
            sys.stderr.write(
                "SKIP: the pinned Lean toolchain %s is not usable (need a"
                " working `lean` or `lake` under the pinned resolution;"
                " found lean=%r lake=%r, both unusable by the version"
                " probe); the axiom sweep honestly skips and judges"
                " nothing (rc %d)\n"
                % (pin, gate[0], gate[1], EXIT_NO_TOOLCHAIN))
            return EXIT_NO_TOOLCHAIN
    else:
        gate = probe_toolchain()
    lean, lake, usable_lean, usable_lake = gate
    if not (usable_lean or usable_lake):
        sys.stderr.write(
            "SKIP: no usable Lean toolchain (need a working `lean` or"
            " `lake` on PATH with a configured default toolchain;"
            " found lean=%r lake=%r, both unusable by the version"
            " probe); the axiom sweep honestly skips and judges nothing"
            " (rc %d)\n" % (lean, lake, EXIT_NO_TOOLCHAIN))
        return EXIT_NO_TOOLCHAIN
    code, report = sweep(args.root, args.allow_axioms, args.timeout,
                         gate=gate, pin=pin)
    # Closure faces: build the current snapshot once when either flag is
    # given; with a baseline, attach the closure_diff + diff_alarm fields
    # (the exit code stays the sweep's own green/red face - diff_alarm
    # rides the payload).  A red sweep still snapshots: the evolution
    # audit wants every closure state, judged or not.
    closure_snap = None
    if args.snapshot or args.baseline:
        closure_snap = build_snapshot(args.root,
                                      report["declarations_detail"]["value"],
                                      args.allow_axioms)
    if baseline_snap is not None:
        attach_closure_diff(
            report, diff_closures(baseline_snap, closure_snap))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = json.dumps(report, ensure_ascii=False)
    print(payload)
    if args.json:
        try:
            write_json(args.json, payload)
        except OSError as exc:
            sys.stderr.write("%s: --json write failed: %s\n" % (TOOL, exc))
            return EXIT_RED
    if args.snapshot:
        try:
            write_json(args.snapshot,
                       json.dumps(closure_snap, ensure_ascii=False))
        except OSError as exc:
            sys.stderr.write("%s: --snapshot write failed: %s\n"
                             % (TOOL, exc))
            return EXIT_RED
    summarize(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
