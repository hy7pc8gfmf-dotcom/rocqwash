#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""axiom_guard.py - repo-wide axiom guard over every .v file (rocqwash tools/).
Purpose.  Answer "what does each theorem actually rest on?" mechanically
  for the whole repository: every .v file is compiled in a private temp
  workdir and judged at two levels (a per-theorem Print Assumptions
  census plus the coqchk kernel recheck); the standard is strict - every
  statement Closed, the axiom whitelist empty by default.  A third,
  strictly additive trust-surface face (verdict-neutral to that
  judgment) sweeps every source for the Rocq switches that disable
  kernel checks and for ML module entry points, sweeps a repo-root
  _CoqProject/_RocqProject for -admit/-type-in-type/-noinit, and counts
  vm_compute/native_compute informationally (bytecode-flag law):
  trust-surface hits are alarms, never silently passed, never
  allow-listable, and never change the compile/light/heavy verdicts or
  the exit code.
Interface.  python3 tools/axiom_guard.py --repo DIR [--out DIR]
  [--rocq BIN] [--coqchk BIN] [--allow-axiom NAME]... [--timeout SEC]
  [--keep] [--strict] | --selftest.  Binary paths resolve per flag then
  environment (--rocq / ROCWASH_ROCQ, --coqchk / ROCWASH_COQCHK);
  --out DIR receives axiom-guard-report.json (stdout summary only
  without it); --selftest runs the frozen offline vectors and exits.
Dependencies.  Python 3 standard library only; rocq and coqchk binaries
  from the environment or flags (never downloaded, never simulated).
Evidence.  Deterministic: sorted inputs, no wall clock in report or
  logic, same input tree yields the byte-identical report; write face =
  caller-named --out report plus private temp workdir (removed unless
  --keep); the destructive matrix pins this contract.  Thermal: no
  embedded guard, wrap guarded runs in tools/cpu_guard.sh (compile
  children stay in the guard's process tree).  Selftest vectors are
  offline: zero network, zero toolchain launch, zero real-repo touch.
Exit-codes.  0 PASS (zero red files; compile-broken recorded as debt;
  --strict turns compile-broken files and trust-surface alarm files red and
  lists them in report["strict_red"]);
  1 red (axiom outside the whitelist, an unjudgeable heavy face, or a
  selftest red); 2 usage error; 9 fail-loud environment (configured
  binary missing or --repo absent); 111 honest skip (toolchain
  unconfigured, reported not simulated, the verify/ rc 111 convention).
Usage:  python3 tools/axiom_guard.py --repo . --out /tmp/evid/t0-2
  python3 tools/axiom_guard.py --selftest
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Judgment faces (detail migrated from the header to hold the 30-line
# annotation budget):
#   1. Inventory: every .v under the repo except .git, sorted by relative
#      path (POSIX form in the report).
#   2. Compile classification: each file is copied byte-identical into a
#      private temp workdir and compiled there (rocq c -native-compiler
#      no -q -Q <source dir> ""), so the .vo output face is temp-only and
#      the repository tree is never written: compile-ok proceeds to
#      detection; compile-broken (rc != 0 or timeout) is recorded in the
#      debt register with the error tail (assumptions cannot be printed
#      for a file that does not compile); skip-no-toolchain exits 111
#      before any work.  The -Q mapping of the source directory makes
#      sibling .vo worlds resolvable when they are built; an unbuilt
#      Require is an honest compile-broken entry whose error tail names
#      the missing library.
#   3. Light face (pre-screen, per theorem): statement names are extracted
#      from the file with a comment/string masking scanner; census copies
#      of the file plus one "Print Assumptions <name>." line per statement
#      compile under a separate _census filename (the base .vo stays
#      intact for the heavy face); each output block maps back to its
#      statement in order (batched pass; on any marker-count mismatch the
#      file falls back to one compile per statement for exact
#      attribution).  Verdicts: closed / axioms / census-error (recorded,
#      not judged).
#   4. Heavy face (authority): coqchk -o on the base .vo of the temp copy;
#      the CONTEXT SUMMARY "* Axioms:" section is parsed (stdlib
#      index-relaxation entries live in other sections and are never
#      judged).  This is the authoritative judgment per the
#      graded-detection design; the token-quarantine face is intentionally
#      not implemented: token-level .vo scanning can quarantine suspicious
#      artifacts but cannot decide closedness (the gate5 precedent), so it
#      would add verdicts it cannot back.
#   5. Verdict: a compile-ok file is red when either face reports an axiom
#      outside the whitelist, or the heavy face cannot deliver a summary
#      (unjudgeable is not green).  Compile-broken files are debt, not
#      red.  Run verdict PASS = zero red files.
#   6. Trust surface (additive, verdict-neutral by default; under --strict
#      an alarm block fails the run via _apply_strict): under the same masking
#      scanner, every source is swept for the Rocq switches that turn
#      kernel checking off (Unset Guard/Positivity/Universe Checking,
#      Unset Elimination Schemes) and for ML entry points (Declare ML
#      Module); a repo-root _CoqProject/_RocqProject is swept for
#      -admit / -type-in-type / -noinit; vm_compute/native_compute are
#      counted informationally (verification-time concern, the
#      bytecode-flag law).  All hits land in report["trust_surface"]
#      with file/line evidence and the block verdict "alarm"; they are
#      never silently passed and allow-listing them is forbidden by
#      design (the block policy note states this).  The face never
#      touches files, debt_register, red_files or the run verdict:
#      classification output is byte-identical with and without hits.

PROG = "axiom_guard"
SCHEMA = "rocqwash-axiom-guard/1"

# Statement families the light face censuses (name-bearing vernaculars).
STMT_RE = re.compile(
    r"(?m)^[ \t]*(?:#\[[^\]]*\][ \t]*\r?\n?[ \t]*|"
    r"(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Theorem|Lemma|Corollary|Proposition|Remark|Fact|Example|Instance)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")
# coqchk CONTEXT SUMMARY section heads (line-start anchored).
SUMMARY_RE = re.compile(r"^\* Axioms:(.*)$", re.M)
SUMMARY_NEXT_RE = re.compile(r"^\* ", re.M)
CLOSED_LINE = "Closed under the global context"
ERROR_TAIL_LINES = 12


def md5_of_bytes(raw):
    return hashlib.md5(raw).hexdigest()


def mask_comments_strings(text):
    """Blank out comment and string literal bodies so name extraction only
    sees code positions (same discipline as the wash-side masking state
    machines: nested (* *) counted, backslash escapes honored)."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("(*", i):
            depth = 0
            start = i
            while i < n:
                if text.startswith("(*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*)", i):
                    depth -= 1
                    i += 2
                    if depth == 0:
                        break
                else:
                    i += 1
            out.append(" " * (i - start))
        elif text.startswith('"', i):
            start = i
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(" " * (i - start))
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def statement_names(text):
    """[(name, line_no)] of the theorem-family statements, comments and
    strings masked out first (comment decoys never enter the census)."""
    masked = mask_comments_strings(text)
    out = []
    for m in STMT_RE.finditer(masked):
        line = masked.count("\n", 0, m.start(2)) + 1
        out.append((m.group(2), line))
    return out


# ---- trust-surface face (additive, verdict-neutral; face 6) ----
# Rocq source-level switches that turn kernel-side checking off, plus the
# ML module entry point: any live occurrence is an alarm.  Tokens are the
# canonical single-space forms; the sweep itself tolerates arbitrary
# whitespace between the words of a token.
TRUST_TOKENS = (
    "Unset Guard Checking",
    "Unset Positivity Checking",
    "Unset Universe Checking",
    "Unset Elimination Schemes",
    "Declare ML Module",
)
TRUST_TOKEN_RES = tuple(
    re.compile(r"\b%s\b" % (r"\s+".join(map(re.escape, tok.split()))))
    for tok in TRUST_TOKENS)
# Repo-root project files swept by the flag-scan face (the Coq-era name
# plus its Rocq-era equivalent) and the trust-relevant flags (matched as
# whole whitespace tokens, so "-arg -type-in-type" relay lines hit).
PROJECT_FLAG_FILES = ("_CoqProject", "_RocqProject")
PROJECT_FLAG_TOKENS = ("-admit", "-type-in-type", "-noinit")
# Certificate census tokens (informational, verdict-neutral).
CERTIFICATE_TOKENS = ("vm_compute", "native_compute")
TRUST_POLICY_NOTE = (
    "Trust-surface policy: live occurrences of the Rocq switches (Unset "
    "Guard Checking, Unset Positivity Checking, Unset Universe Checking, "
    "Unset Elimination Schemes, Declare ML Module) and of the repo-root "
    "project-file flags (-admit, -type-in-type, -noinit) are alarms. "
    "Allow-listing these switches and flags is forbidden by design: a "
    "trust-surface hit is never silently passed. This face is strictly "
    "additive and verdict-neutral: the compile/light/heavy classification, "
    "debt_register, red_files and the run verdict are computed exactly as "
    "without it.")
TRUST_CERTIFICATE_NOTE = (
    "vm_compute/native_compute occurrence counts are informational and "
    "verdict-neutral: evaluation-tactic and bytecode-flag choice is a "
    "verification-time concern (the bytecode-flag law), not a static "
    "trust-surface defect; the counts never enter any verdict.")


def trust_surface_hits(text, rel):
    """[{token, file, line}] for every live (non-comment, non-string)
    occurrence of a Rocq switch token or ML module declaration in one
    source.  The sweep reuses the same masking scanner as name extraction
    (a commented-out or string-embedded switch never hits), and line
    numbers are computed on the masked text whose positions match the raw
    file, so the evidence points at the real line."""
    masked = mask_comments_strings(text)
    hits = []
    for tok, tok_re in zip(TRUST_TOKENS, TRUST_TOKEN_RES):
        for m in tok_re.finditer(masked):
            hits.append({"token": tok, "file": rel,
                         "line": masked.count("\n", 0, m.start()) + 1})
    return hits


def certificate_counts(text):
    """(vm_compute, native_compute) whole-token occurrence counts over the
    masked source.  Informational only: the bytecode-flag law makes the
    evaluation-tactic choice a verification-time concern, so this census
    never enters any verdict."""
    masked = mask_comments_strings(text)
    return tuple(len(re.findall(r"\b%s\b" % re.escape(tok), masked))
                 for tok in CERTIFICATE_TOKENS)


def project_flag_hits(repo):
    """[{token, file, line}] flag-scan face: a repo-root _CoqProject (or
    its Rocq-era _RocqProject equivalent) is swept for the trust-relevant
    flags -admit / -type-in-type / -noinit.  '#' comment tails are
    stripped first and a flag matches as a whole whitespace token, so the
    "-arg -type-in-type" relay form hits on the flag itself.  No project
    file at the root -> no hits (nothing is fabricated)."""
    hits = []
    for name in PROJECT_FLAG_FILES:
        path = os.path.join(repo, name)
        if not os.path.isfile(path):
            continue
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            for ln_no, line in enumerate(fh, 1):
                for tok in line.split("#", 1)[0].split():
                    if tok in PROJECT_FLAG_TOKENS:
                        hits.append({"token": tok, "file": name,
                                     "line": ln_no})
    return hits


def build_trust_surface(hits, vm_count, native_count):
    """Assemble the report["trust_surface"] block.  The block verdict is
    "alarm" when any source-switch or project-flag hit exists, "clean"
    otherwise - and never a silent pass: the policy note carried in the
    block states that allow-listing these switches and flags is forbidden
    by design.  Hits are sorted (file, line, token) so the block stays
    byte-identical across runs on the same input tree."""
    hits = sorted(hits, key=lambda h: (h["file"], h["line"], h["token"]))
    return {
        "verdict": "alarm" if hits else "clean",
        "hits": hits,
        "certificates": {
            "vm_compute": vm_count,
            "native_compute": native_count,
            "verdict": "informational",
            "note": TRUST_CERTIFICATE_NOTE,
        },
        "policy": TRUST_POLICY_NOTE,
    }


def run_cmd(argv, timeout):
    """Subprocess run with merged stdout/stderr and a hard timeout; the
    caller decides every verdict from (rc, output, error) - no silent
    fallback.  error is None on a clean launch, "timeout" on a timeout,
    and an OS-level message string when the binary cannot be launched."""
    try:
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace"), None
    except subprocess.TimeoutExpired as e:
        partial = b""
        if e.stdout:
            partial += e.stdout
        if e.stderr:
            partial += e.stderr
        return None, partial.decode("utf-8", "replace"), "timeout"
    except OSError as e:
        return None, "", str(e)


def error_tail(output, lines=ERROR_TAIL_LINES):
    tail = [ln for ln in output.splitlines() if ln.strip()]
    return tail[-lines:]


def strip_tmp(output, work):
    """Normalize the run's private temp directory out of compiler output so
    error tails (which embed the .v copy path) stay byte-stable across
    runs - determinism of the report volume (same input tree, same bytes)."""
    return output.replace(work, "<axguard-tmp>")


def compile_one(rocq, src_v, timeout, log_dir=None, name=None):
    """Compile one temp-side .v; returns (rc, output, error).  The .vo lands
    next to the copy (temp workdir), never in the repository."""
    argv = [rocq, "c", "-native-compiler", "no", "-q",
            "-Q", os.path.dirname(src_v) or ".", "", src_v]
    rc, out, err = run_cmd(argv, timeout)
    if log_dir and name:
        with io.open(os.path.join(log_dir, name + ".compile.log"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    return rc, out, err


def parse_axioms_summary(output):
    """Parse the coqchk CONTEXT SUMMARY axioms section.
    Returns (status, axiom_names): status in
    {"clean", "axioms", "no-summary"}.  Entries are module-qualified."""
    m = SUMMARY_RE.search(output)
    if m is None:
        return "no-summary", []
    first = m.group(1).strip()
    if first == "<none>":
        return "clean", []
    names = []
    if first:
        names.append(first)
    nxt = SUMMARY_NEXT_RE.search(output, m.end())
    body = output[m.end():nxt.start()] if nxt else output[m.end():]
    for ln in body.splitlines():
        ln = ln.strip()
        if ln:
            names.append(ln)
    return "axioms", names


def parse_census_blocks(output, statements):
    """Attribute ordered Print Assumptions blocks to statements.
    Returns a list of verdict dicts in statement order, or None when the
    marker count does not match (caller falls back to per-statement runs)."""
    markers = []  # (pos, kind)
    for m in re.finditer(re.escape(CLOSED_LINE), output):
        markers.append((m.start(), "closed"))
    for m in re.finditer(r"^Axioms:$", output, re.M):
        markers.append((m.start(), "axioms"))
    markers.sort()
    if len(markers) != len(statements):
        return None
    verdicts = []
    for k, (pos, kind) in enumerate(markers):
        end = markers[k + 1][0] if k + 1 < len(markers) else len(output)
        axioms = []
        if kind == "axioms":
            body = output[pos:end]
            for ln in body.splitlines()[1:]:
                ln = ln.strip()
                if ln and not ln.startswith(CLOSED_LINE):
                    axioms.append(ln)
        verdicts.append({"statement": statements[k][0],
                         "line": statements[k][1],
                         "verdict": kind,
                         "axioms": axioms})
    return verdicts


def census_write(census_v, base_text, statement=None):
    """Write one census copy (a separate _census filename, so the base .vo
    of the file under judgment stays intact for the heavy face)."""
    appended = (""
                if statement is None
                else "\nPrint Assumptions %s.\n" % statement)
    with io.open(census_v, "w", encoding="utf-8", newline="") as fh:
        fh.write(base_text + appended)


def light_face(rocq, base_text, work_dir, stem, statements, timeout,
               log_dir, tag):
    """Per-theorem Print Assumptions census: one batched compile first
    (ordered attribution), per-statement compiles as the exact fallback
    (a section-local name fails only its own statement, not the file)."""
    census_v = os.path.join(work_dir, stem + "_census.v")
    census_write(census_v, base_text)
    rc, out, err = compile_one(rocq, census_v, timeout, log_dir, tag)
    verdicts = None
    if rc == 0:
        verdicts = parse_census_blocks(out, statements)
    if verdicts is not None:
        return verdicts
    # fallback: one compile per statement (exact attribution, partial-tolerant)
    verdicts = []
    for nm, ln in statements:
        census_write(census_v, base_text, nm)
        rc2, out2, err2 = compile_one(rocq, census_v, timeout)
        if err2 is not None:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error",
                             "axioms": [err2]})
        elif rc2 != 0:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error",
                             "axioms": error_tail(strip_tmp(out2, work_dir),
                                                  4)})
        elif re.search(r"^Axioms:$", out2, re.M):
            block = out2[out2.index("Axioms:"):]
            axioms = [ln2.strip() for ln2 in block.splitlines()[1:]
                      if ln2.strip()]
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "axioms", "axioms": axioms})
        elif CLOSED_LINE in out2:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "closed", "axioms": []})
        else:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error", "axioms": []})
    with io.open(os.path.join(log_dir, tag + ".census.log"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    return verdicts


def _apply_strict(report, reds):
    """Strict-mode verdict face (tools/axiom_guard.py --strict): compile-broken
    files and trust-surface alarm files become red (default mode records them
    as debt / verdict-neutral and never reaches this function).  Returns the
    list of newly red names (dedup against reds; the caller stores it as
    report["strict_red"]).  Pure: no I/O, no verdict text changes beyond the
    red list."""
    strict_added = []
    for f in report.get("files", []):
        rel = f.get("file")
        if f.get("classification") == "compile-broken" and rel \
                and rel not in reds:
            reds.append(rel)
            strict_added.append(rel)
    ts = report.get("trust_surface")
    if ts and ts.get("verdict") == "alarm":
        for h in ts.get("hits", []):
            rel = h.get("file")
            if rel and rel not in reds:
                reds.append(rel)
                strict_added.append(rel)
    return strict_added


def guard(repo, rocq, coqchk, allow_axioms, timeout, out_dir, keep,
          strict=False):
    """Full run; returns (exit_code, report_dict).  Write faces: the private
    temp workdir and (when given) the caller-named --out report file.
    strict=True: compile-broken files and trust-surface alarm files enter the
    red list (default face keeps them as debt / verdict-neutral)."""
    v_files = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for fn in filenames:
            if fn.endswith(".v"):
                rel = os.path.relpath(os.path.join(dirpath, fn),
                                      repo).replace(os.sep, "/")
                v_files.append((rel, os.path.join(dirpath, fn)))
    v_files.sort()

    work = tempfile.mkdtemp(prefix="rocqwash_axiom_guard_")
    log_dir = os.path.join(work, "logs")
    os.makedirs(log_dir)
    report = {
        "schema": SCHEMA,
        "repo": os.path.abspath(repo),
        "rocq": rocq,
        "coqchk": coqchk,
        "allow_axioms": sorted(allow_axioms),
        "files_scanned": len(v_files),
        "standard": "Closed zero axioms (default whitelist empty)",
        "files": [],
        "debt_register": [],
        "red_files": [],
        "verdict": "PASS",
    }
    reds = []
    # Trust-surface accumulators (additive face, verdict-neutral).
    trust_hits = []
    vm_total = 0
    native_total = 0
    try:
        for idx, (rel, abs_path) in enumerate(v_files):
            tag = "%03d_%s" % (idx, os.path.basename(abs_path)[:-2])
            fdir = os.path.dirname(abs_path)
            wdir = os.path.join(work, "f%03d" % idx)
            os.makedirs(wdir)
            stem = os.path.basename(abs_path)[:-2]
            work_v = os.path.join(wdir, stem + ".v")
            with io.open(abs_path, "rb") as fh:
                raw = fh.read()
            with io.open(work_v, "wb") as fh:
                fh.write(raw)
            entry = {"file": rel, "md5": md5_of_bytes(raw)}
            # Trust-surface face (additive, verdict-neutral): static
            # switch-token sweep over the masked source plus the
            # informational certificate census.  Every source is scanned
            # regardless of its compile classification - a file that
            # fails to compile is still scanned for what it tries to
            # switch off - and no result here ever enters files,
            # debt_register, red_files or the run verdict.
            ts_text = raw.decode("utf-8", "replace")
            trust_hits.extend(trust_surface_hits(ts_text, rel))
            vm_n, nat_n = certificate_counts(ts_text)
            vm_total += vm_n
            native_total += nat_n
            rc, out, err = compile_one(rocq, work_v, timeout, log_dir, tag)
            if err is not None:
                entry["classification"] = "compile-broken"
                entry["compile_rc"] = -1
                entry["compile_error"] = err
                report["debt_register"].append(rel)
                report["files"].append(entry)
                continue
            if rc != 0:
                entry["classification"] = "compile-broken"
                entry["compile_rc"] = rc
                entry["error_tail"] = error_tail(strip_tmp(out, work))
                report["debt_register"].append(rel)
                report["files"].append(entry)
                continue
            entry["classification"] = "compile-ok"
            entry["compile_rc"] = 0
            base_text = raw.decode("utf-8", "replace")
            stmts = statement_names(base_text)
            entry["statements"] = len(stmts)
            entry["light_census"] = light_face(
                rocq, base_text, wdir, stem, stmts, timeout, log_dir, tag) \
                if stmts else []
            # heavy face on the base .vo (the census copies never overwrite it)
            chk_rc, chk_out, chk_err = run_cmd(
                [coqchk, "-o", "-Q", fdir, "", "-Q", wdir, "", stem],
                timeout)
            with io.open(os.path.join(log_dir, tag + ".coqchk.log"), "w",
                         encoding="utf-8", newline="\n") as fh:
                fh.write(chk_out)
            if chk_err is not None or chk_rc is None or chk_rc != 0:
                entry["heavy"] = {"verdict": "coqchk-error",
                                  "detail": chk_err or "rc %s" % chk_rc,
                                  "tail": error_tail(strip_tmp(chk_out, work),
                                                     4)}
                if rel not in reds:
                    reds.append(rel)
            else:
                status, axioms = parse_axioms_summary(chk_out)
                axioms = [a for a in axioms if a not in allow_axioms]
                entry["heavy"] = {"verdict": status,
                                  "axioms": axioms,
                                  "coqchk_rc": chk_rc}
                if status == "no-summary" or axioms:
                    if rel not in reds:
                        reds.append(rel)
            # light-face judgment (pre-screen; the heavy face stays
            # authoritative - a light red alone still fails the file)
            for v in entry.get("light_census", []):
                v["axioms"] = [a for a in v.get("axioms", [])
                               if a not in allow_axioms]
                if v["verdict"] == "axioms" and v["axioms"] \
                        and rel not in reds:
                    reds.append(rel)
            report["files"].append(entry)
        # Trust-surface assembly (additive face): source hits plus the
        # repo-root project-file flag scan land in one block with file
        # evidence; the classification keys below are computed exactly
        # as without this face.
        report["trust_surface"] = build_trust_surface(
            trust_hits + project_flag_hits(repo), vm_total, native_total)
        report["strict_red"] = _apply_strict(report, reds) if strict else []
        report["red_files"] = reds
        report["verdict"] = "RED" if reds else "PASS"
        if out_dir:
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            report_path = os.path.join(out_dir, "axiom-guard-report.json")
            with io.open(report_path, "w", encoding="utf-8",
                         newline="\n") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=1,
                          sort_keys=True)
                fh.write("\n")
            print("report -> %s" % report_path)
        _summarize(report)
        return (1 if reds else 0), report
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def _summarize(report):
    ok = [f for f in report["files"] if f["classification"] == "compile-ok"]
    broken = [f for f in report["files"]
              if f["classification"] == "compile-broken"]
    print("AXIOM-GUARD: %s" % report["verdict"])
    print("  files scanned: %d (compile-ok %d / compile-broken %d)"
          % (report["files_scanned"], len(ok), len(broken)))
    for f in ok:
        lc = f.get("light_census", [])
        closed = sum(1 for v in lc if v["verdict"] == "closed")
        hv = f.get("heavy", {}).get("verdict")
        print("  ok   %s statements=%d closed=%d heavy=%s"
              % (f["file"], len(lc), closed, hv))
    for f in broken:
        print("  debt %s (rc %s)" % (f["file"], f.get("compile_rc")))
    ts = report.get("trust_surface")
    if ts is not None:
        print("  trust-surface %s hits=%d certificates(vm_compute=%d, "
              "native_compute=%d)"
              % (ts["verdict"], len(ts["hits"]),
                 ts["certificates"]["vm_compute"],
                 ts["certificates"]["native_compute"]))
        for h in ts["hits"]:
            print("  alarm %s:%d %s" % (h["file"], h["line"], h["token"]))
    for rel in report.get("red_files", []):
        print("  RED  %s" % rel)


# ---- selftest (frozen offline vectors on the judgment faces; zero
# network, zero toolchain launch, zero real-repo touch) ----

# Heavy-face parse fixtures: coqchk CONTEXT SUMMARY shapes.
COQCHK_OUT_CLEAN = ("""CONTEXT SUMMARY
===============

* Axioms: <none>

""")
COQCHK_OUT_AXIOMS = ("""CONTEXT SUMMARY
===============

* Axioms: Coq.Logic.Classical_Prop.classic
    Coq.Logic.ClassicalUniqueChoice.classic_dep

* Principles: <none>
""")
COQCHK_OUT_NO_SUMMARY = ("""CONTEXT SUMMARY
===============

* Principles: <none>
""")

# Light-face parse fixture: one closed statement then one with axioms.
CENSUS_OUT_MIXED = ("head marker line\n"
                    "Closed under the global context\n"
                    "Axioms:\n"
                    "    Coq.Logic.Classical_Prop.classic\n")
CENSUS_STATEMENTS = [("t_closed_one", 2), ("t_axiom_one", 5)]

# Name-extraction fixture: comment and string decoys must not census.
SAMPLE_V_TEXT = ("(* Theorem decoy_in_comment : False. *)\n"
                 "Theorem t_closed_one : True.\n"
                 "Proof. exact I. Qed.\n"
                 "\n"
                 "Definition hidden := \"Theorem decoy_in_string : False.\"\n"
                 "\n"
                 "Theorem t_axiom_one : True.\n"
                 "Proof. exact I. Qed.\n")

# Trust-surface fixtures: one source carrying two live switch hits plus
# comment/string decoys that must never hit, one clean source, and one
# text for the informational certificate census (live-only counting).
TRUST_HIT_V_TEXT = ("Definition rely := 1.\n"
                    "Unset Guard Checking.\n"
                    "(* Unset Positivity Checking. comment decoy *)\n"
                    "Definition s := \"Unset Universe Checking decoy\".\n"
                    "Declare ML Module \"plugin\".\n")
TRUST_CLEAN_V_TEXT = ("(* Unset Guard Checking. comment decoy *)\n"
                      "Definition a := \"Declare ML Module string decoy\".\n"
                      "Theorem t_clean_one : True.\n"
                      "Proof. exact I. Qed.\n")
TRUST_CERT_TEXT = ("Goal True. vm_compute. reflexivity. Qed.\n"
                   "(* vm_compute comment decoy *)\n"
                   "Definition d := \"native_compute string decoy\".\n"
                   "Compute (vm_compute 3, native_compute 7).\n")


def selftest():
    """Frozen offline vectors over the judgment faces (heavy summary
    parsing, census attribution, name extraction, exit-code contract);
    zero network, zero toolchain launch, zero real-repo touch.  Returns
    0 when every vector is green, 1 with the failing names on stdout."""
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_axiom_guard_selftest_")
    try:
        # heavy-face summary parsing (the authoritative judgment input)
        status, names = parse_axioms_summary(COQCHK_OUT_AXIOMS)
        vec("summary-axioms-hit",
            status == "axioms" and names == [
                "Coq.Logic.Classical_Prop.classic",
                "Coq.Logic.ClassicalUniqueChoice.classic_dep"],
            "status=%s names=%s" % (status, names))
        status, names = parse_axioms_summary(COQCHK_OUT_CLEAN)
        vec("summary-none-clean", status == "clean" and names == [],
            "status=%s names=%s" % (status, names))
        status, names = parse_axioms_summary(COQCHK_OUT_NO_SUMMARY)
        vec("summary-absent-unjudgeable", status == "no-summary"
            and names == [], "status=%s names=%s" % (status, names))
        # light-face census attribution (ordered blocks, mismatch fallback)
        verdicts = parse_census_blocks(CENSUS_OUT_MIXED, CENSUS_STATEMENTS)
        ok = (verdicts is not None and len(verdicts) == 2
              and verdicts[0]["verdict"] == "closed"
              and verdicts[0]["axioms"] == []
              and verdicts[1]["verdict"] == "axioms"
              and verdicts[1]["axioms"] == [
                  "Coq.Logic.Classical_Prop.classic"])
        vec("census-attribution", ok, "verdicts=%s" % (verdicts,))
        vec("census-mismatch-falls-back",
            parse_census_blocks("Closed under the global context\n",
                                CENSUS_STATEMENTS) is None,
            "one marker against two statements must yield None")
        # name extraction behind the masking scanner (decoys never census)
        got = statement_names(SAMPLE_V_TEXT)
        vec("statement-names-masked",
            got == [("t_closed_one", 2), ("t_axiom_one", 7)],
            "got=%s" % (got,))
        masked = mask_comments_strings(SAMPLE_V_TEXT)
        lines = masked.splitlines()
        vec("masking-blanks-decoys",
            "decoy" not in masked
            and lines[1].startswith("Theorem t_closed_one")
            and lines[6].startswith("Theorem t_axiom_one"),
            "comment and string bodies blanked; real statements intact")
        # trust-surface face: source sweep (one live-hit fixture with
        # comment/string decoys + one clean fixture), the informational
        # certificate census, the flag scan on a temp _CoqProject, and
        # the verdict-does-not-change seam (classification outputs are
        # byte-identical with and without switch hits).
        hits = trust_surface_hits(TRUST_HIT_V_TEXT, "hit.v")
        vec("trust-source-hit",
            hits == [{"token": "Unset Guard Checking", "file": "hit.v",
                      "line": 2},
                     {"token": "Declare ML Module", "file": "hit.v",
                      "line": 5}],
            "live switches hit with file/line evidence; %s" % (hits,))
        vec("trust-source-clean",
            trust_surface_hits(TRUST_CLEAN_V_TEXT, "clean.v") == [],
            "commented-out and string-embedded switches never hit")
        vec("trust-certificate-counts",
            certificate_counts(TRUST_CERT_TEXT) == (2, 1),
            "vm_compute/native_compute counted live-only (masked decoys "
            "excluded), informational")
        proj_dir = os.path.join(tmp, "flagrepo")
        os.makedirs(proj_dir)
        with io.open(os.path.join(proj_dir, "_CoqProject"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("-R src Pkg\n"
                     "-arg -type-in-type\n"
                     "# -admit in a comment must not hit\n"
                     "-noinit\n")
        flag_hits = project_flag_hits(proj_dir)
        vec("flag-scan-hits",
            flag_hits == [{"token": "-type-in-type", "file": "_CoqProject",
                           "line": 2},
                          {"token": "-noinit", "file": "_CoqProject",
                           "line": 4}],
            "flag tokens hit with file/line evidence; comment tails "
            "stripped; -arg relay lines hit; %s" % (flag_hits,))
        clean_dir = os.path.join(tmp, "flagclean")
        os.makedirs(clean_dir)
        vec("flag-scan-absent-clean", project_flag_hits(clean_dir) == [],
            "no project file at the repo root -> no flag hits")
        # verdict-does-not-change seam: attaching the trust-surface block
        # to a fully classified report adds exactly one key and leaves
        # every classification output byte-identical, with and without
        # switch hits.
        def seed_report():
            return {"schema": SCHEMA,
                    "files": [{"file": "a.v", "md5": "0" * 32,
                               "classification": "compile-ok",
                               "compile_rc": 0, "statements": 1,
                               "light_census": [{"statement": "t",
                                                 "line": 1,
                                                 "verdict": "closed",
                                                 "axioms": []}],
                               "heavy": {"verdict": "clean",
                                         "axioms": [], "coqchk_rc": 0}}],
                    "debt_register": ["b.v"],
                    "red_files": ["a.v"],
                    "verdict": "RED"}

        ref = seed_report()
        with_hit = json.loads(json.dumps(ref))
        without_hit = json.loads(json.dumps(ref))
        with_hit["trust_surface"] = build_trust_surface(
            [{"token": "Unset Guard Checking", "file": "a.v", "line": 2}],
            1, 2)
        without_hit["trust_surface"] = build_trust_surface([], 0, 0)
        ok = (all(with_hit[k] == ref[k] and without_hit[k] == ref[k]
                  for k in ref)
              and set(with_hit) - set(ref) == {"trust_surface"}
              and set(without_hit) - set(ref) == {"trust_surface"}
              and with_hit["trust_surface"]["verdict"] == "alarm"
              and without_hit["trust_surface"]["verdict"] == "clean"
              and with_hit["verdict"] == without_hit["verdict"] == "RED"
              and with_hit["red_files"] == without_hit["red_files"] == ["a.v"]
              and with_hit["debt_register"] == ["b.v"])
        vec("trust-verdict-does-not-change", ok,
            "classification keys identical with and without hits; only "
            "trust_surface added (alarm vs clean)")
        vec("trust-policy-anti-allowlist",
            "forbidden by design" in with_hit["trust_surface"]["policy"]
            and "never silently passed"
            in with_hit["trust_surface"]["policy"]
            and "bytecode-flag law"
            in with_hit["trust_surface"]["certificates"]["note"],
            "the report itself states allow-listing is forbidden and "
            "cites the bytecode-flag law")
        # report determinism helpers
        vec("tail-and-tmp-normalize",
            len(error_tail("\n".join("ln%d" % k
                                     for k in range(20)))) == ERROR_TAIL_LINES
            and strip_tmp("x " + tmp + " y", tmp) == "x <axguard-tmp> y",
            "tail bounded at %d lines; temp path normalized"
            % ERROR_TAIL_LINES)
        # flag face: --selftest parses standalone (no --repo needed)
        vec("selftest-flag-face",
            build_parser().parse_args(["--selftest"]).selftest is True
            and build_parser().parse_args([]).selftest is False,
            "--selftest defaults to False and parses without --repo")
        # exit-code contract (same family as the documented tool codes)
        def spawn(argv, env=None):
            try:
                p = subprocess.run([sys.executable, "-B", script] + argv,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=60,
                                   env=env)
            except subprocess.TimeoutExpired:
                return None, "timeout"
            out = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            return p.returncode, out

        rc, out = spawn([])
        vec("exit-usage-error-rc2", rc == 2,
            "no arguments exits %s (usage error)" % rc)
        rc, out = spawn(["--repo", os.path.join(tmp, "absent-repo")])
        vec("exit-repo-absent-rc9", rc == 9,
            "missing --repo directory exits %s (fail-loud)" % rc)
        skip_env = dict(os.environ)
        skip_env.pop("ROCWASH_ROCQ", None)
        skip_env.pop("ROCWASH_COQCHK", None)
        rc, out = spawn(["--repo", tmp], env=skip_env)
        vec("exit-unconfigured-rc111", rc == 111,
            "unconfigured toolchain exits %s (honest skip)" % rc)
        rc, out = spawn(["--repo", tmp,
                         "--rocq", os.path.join(tmp, "no-rocq"),
                         "--coqchk", os.path.join(tmp, "no-coqchk")])
        vec("exit-binary-absent-rc9", rc == 9,
            "configured but missing binaries exit %s (fail-loud)" % rc)
        # strict-mode verdict face (_apply_strict; pure, offline vectors)
        rep = {"files": [
            {"file": "broken.v", "classification": "compile-broken"},
            {"file": "ok.v", "classification": "compile-ok"}],
            "trust_surface": {"verdict": "alarm",
                              "hits": [{"file": "hit.v", "line": 2,
                                        "token": "Unset Guard Checking"}]}}
        reds = ["already.v"]
        added = _apply_strict(rep, reds)
        vec("strict-compile-broken-red",
            "broken.v" in reds and "broken.v" in added and "ok.v" not in reds,
            "strict: compile-broken turns red; ok stays clean; added=%s" % added)
        vec("strict-trust-alarm-red",
            "hit.v" in reds and "hit.v" in added,
            "strict: trust-surface alarm file turns red; added=%s" % added)
        vec("strict-dedup",
            "broken.v" not in _apply_strict(rep, ["broken.v"]),
            "strict: an already-red name is never duplicated again")
        vec("strict-clean-pass",
            _apply_strict({"files": [], "trust_surface": {"verdict": "clean",
                                                          "hits": []}}, []) == [],
            "strict: a clean report adds nothing")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d vector(s), %d FAIL" % (total[0], len(failures)))
    if failures:
        print("selftest RED: %s" % ", ".join(failures))
        return 1
    return 0


def build_parser():
    """The flag face; extracted so --selftest runs standalone (no --repo
    required) and the usage face stays single-source."""
    ap = argparse.ArgumentParser(
        description="Repo-wide axiom guard (compile tri-classification, "
                    "per-theorem assumption census, coqchk kernel recheck).")
    ap.add_argument("--repo", help="repository root (required unless "
                                   "--selftest)")
    ap.add_argument("--out", help="report directory (report JSON written "
                                  "here; absent = stdout only)")
    ap.add_argument("--rocq", default=os.environ.get("ROCWASH_ROCQ", ""),
                    help="rocq binary (default ROCWASH_ROCQ)")
    ap.add_argument("--coqchk", default=os.environ.get("ROCWASH_COQCHK", ""),
                    help="coqchk binary (default ROCWASH_COQCHK)")
    ap.add_argument("--allow-axiom", action="append", default=[],
                    dest="allow_axioms", help="whitelisted axiom name "
                    "(repeatable; default whitelist is empty)")
    ap.add_argument("--timeout", type=int, default=600,
                    help="per-subprocess timeout seconds (default 600)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp workdir (debug face)")
    ap.add_argument("--strict", action="store_true",
                    help="strict mode: compile-broken files and trust-surface "
                    "alarm files are red (default: debt / verdict-neutral)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group and exit")
    return ap


def main():
    args = build_parser().parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.repo:
        build_parser().error("--repo is required (usage error)")
    if not os.path.isdir(args.repo):
        print("FAIL-LOUD: --repo directory missing: %s" % args.repo,
              file=sys.stderr)
        sys.exit(9)
    missing = [flag for flag, path in (("--rocq", args.rocq),
                                       ("--coqchk", args.coqchk))
               if not path]
    if missing:
        print("SKIP: %s not configured (flag or environment); the axiom "
              "guard honestly skips and judges nothing (rc 111)"
              % " and ".join(missing), file=sys.stderr)
        sys.exit(111)
    absent = [flag for flag, path in (("--rocq", args.rocq),
                                      ("--coqchk", args.coqchk))
              if not os.path.exists(path)]
    if absent:
        print("FAIL-LOUD: %s configured but binary missing: %s"
              % (" and ".join(absent),
                 " and ".join(p for p in (args.rocq, args.coqchk)
                              if not os.path.exists(p))),
              file=sys.stderr)
        sys.exit(9)

    code, _report = guard(args.repo, args.rocq, args.coqchk,
                          args.allow_axioms, args.timeout, args.out,
                          args.keep, strict=args.strict)
    sys.exit(code)


if __name__ == "__main__":
    main()
