#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_scope.py - shared exclusion roster for the repair apply faces.

Purpose.  One source of truth for the faces a repair class never
  targets: the frozen ledger rows (LEDGER8 and CHECKERS read at runtime
  from certify/frozen8.py), the append-only ledger document, the
  governing documents (constitution tier, prefix-matched under docs/),
  and the frozen directory families.  Consumers edit by appending,
  never by a whole-file rewrite.

Interface.  frozen8_ledger / frozen8_checkers / ledger_doc /
  exclusion_roster / full_frozen_files / governing_doc_faces
  (repo_root), dir_family_exclusion(rel_path); constants
  SNAPSHOT_LEDGER8, SNAPSHOT_CHECKERS, FALLBACK_LEDGER_DOC,
  FROZEN_DIR_FAMILIES, LEGAL_DATA_DIR_FAMILIES, GOVERNING_DOC_PREFIXES.
  Load by path (importlib).

Dependencies.  Python 3 standard library only.  certify/frozen8.py is
  parsed as an AST literal (the module body never executes); an absent
  or damaged constant degrades to the pinned snapshot tuple, and every
  provider reports its source so the fallback stays loud.  Zero network face.

Evidence.  --selftest: runtime LEDGER8 and checkers parity, roster
  shape (ledger rows, the append-only doc, the governing faces), on-disk
  faces and family dirs, the ten-row full view, the governing roster
  guard, fixture fallback, two identical roster reads.

Exit-codes.  0 all vectors pass; 1 a failed vector; 2 usage error.
"""

import argparse
import ast
import contextlib
import io
import os
import shutil
import sys
import tempfile

TOOL = "repair_scope"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_live_repo():
    """The live repo root for the selftest live vectors: the script's
    grandparent when the module runs inside its own checkout; otherwise
    the ROCWASH_REPO_DIR override or the cwd when that directory carries
    the live markers (cw.sh + tools/). None = detached temp copy - the
    live vectors are then skipped with an honest marker (the sandbox
    vectors carry the guard logic; a detached copy has no live repo)."""
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.path.dirname(here),
             os.environ.get("ROCWASH_REPO_DIR", ""),
             os.getcwd()]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "cw.sh")) \
                and os.path.isdir(os.path.join(c, "tools")):
            return c
    return None

# pinned snapshot of certify/frozen8.py (runtime order); the runtime AST
# read stays authoritative, this tuple is only the fallback
SNAPSHOT_LEDGER8 = (
    "certify/freeze_manifest.py",
    "names/mac_stmt_names.py",
    "scan/mac_stmt_scan.py",
    "seam/seam_probe.py",
    "tools/cpu_guard.sh",
    "verify/gate4_comment_guard.py",
    "verify/verify_vo.py",
    "wash/wash_engine.py",
)
SNAPSHOT_CHECKERS = ("certify/frozen8.py", "certify/push_gate.py")
FALLBACK_LEDGER_DOC = "更新账.md"

# frozen directory families (E-series new-face guard list).  A family
# entry may be nested: a slash-free entry matches by top-level directory,
# a nested entry by path prefix (dir_family_exclusion).  tests/fixtures
# carries the mechanical-test fixtures: their bytes are test inputs (the
# gate4 dirty sample keeps its banned faces by design; the cure/probe
# fixtures pin guarded negatives that must survive every application
# verbatim), so the rewrite faces never target the subtree while the
# sibling tests/ repairable faces stay writable.
FROZEN_DIR_FAMILIES = ("certify", "scan", "verify", "wrapper", "names",
                       "seam", "seeds", "CLA", "tests/fixtures")
# legal/data faces a repair class never rewrites; the zh doc face rides the
# norm_lint archive rule instead of this roster
LEGAL_DATA_DIR_FAMILIES = ("CLA", "seeds", "docs")

# Constitution-tier governing documents (the recursive-improvement
# charter, the recursive-evolution whitepaper, the three RIS interface
# faces, and the contrib-isolation protocol, all under docs/).  Name-
# prefix matched so version-suffixed replacements stay covered; a
# machine write face never targets them, and their wording findings
# belong to the human review layer (the charter's own layer law).
GOVERNING_DOC_PREFIXES = (
    "docs/recursive-improvement-charter-",
    "docs/recursive-evolution-whitepaper-",
    "docs/ris-interface-spec-",
    "docs/ris-interface-parameters-",
    "docs/ris-whitepaper-supplement-",
    "docs/contrib-isolation-protocol-",
)


def dir_family_exclusion(rel_path):
    """The directory-family exclusion reason for a repo-relative path, or
    None.  A slash-free family matches by top-level directory; a nested
    family (containing a slash) matches by path prefix."""
    top = rel_path.split("/", 1)[0]
    if top in FROZEN_DIR_FAMILIES:
        return "directory family exclusion (%s/)" % top
    for fam in FROZEN_DIR_FAMILIES:
        if "/" in fam and (rel_path == fam
                           or rel_path.startswith(fam + "/")):
            return "directory family exclusion (%s/)" % fam
    return None


def _read_constant(repo_root, wanted):
    """(name, literal value) of the first wanted module-level constant in
    certify/frozen8.py, or None when the file or the constant is absent or
    damaged.  Parsing only, the module body never executes."""
    path = os.path.join(repo_root, "certify", "frozen8.py")
    if not os.path.isfile(path):
        return None
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, ValueError):
        return None
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) \
            else [node.target]
        ids = [getattr(t, "id", "") for t in targets]
        hit = [w for w in wanted if w in ids]
        if not hit:
            continue
        try:
            return hit[0], ast.literal_eval(node.value)
        except (ValueError, TypeError):
            return None
    return None


def _clean_rows(raw, pairs):
    """Rows as a unique non-empty str list, or None when the literal does
    not carry that shape (pairs=True for (rel, md5) tuples)."""
    try:
        if pairs:
            rows = [str(rel) for rel, _md5 in raw]
        else:
            rows = [str(rel) for rel in raw]
    except (TypeError, ValueError):
        return None
    if not rows or any(not r for r in rows) or len(set(rows)) != len(rows):
        return None
    return rows


def frozen8_ledger(repo_root):
    """In-service eight rows: (rel_paths, source).  source is
    "runtime-ledger8" (AST read) or "snapshot-fallback" (pinned tuple)."""
    got = _read_constant(repo_root, ("LEDGER8",))
    if got and got[0] == "LEDGER8":
        rows = _clean_rows(got[1], pairs=True)
        if rows:
            return rows, "runtime-ledger8"
    return list(SNAPSHOT_LEDGER8), "snapshot-fallback"


def frozen8_checkers(repo_root):
    """Meta-freeze checker rows: (rel_paths, source), same discipline."""
    got = _read_constant(repo_root, ("CHECKERS",))
    if got and got[0] == "CHECKERS":
        rows = _clean_rows(got[1], pairs=False)
        if rows:
            return rows, "runtime-checkers"
    return list(SNAPSHOT_CHECKERS), "snapshot-fallback"


def ledger_doc(repo_root):
    """Append-only ledger document name: (name, source)."""
    got = _read_constant(repo_root, ("LEDGER_DOC",))
    if got and got[0] == "LEDGER_DOC" and isinstance(got[1], str) and got[1]:
        return got[1], "runtime-ledger-doc"
    return FALLBACK_LEDGER_DOC, "snapshot-fallback"


def governing_doc_faces(repo_root):
    """Sorted repo-relative governing-document faces under docs/ whose
    names start with a GOVERNING_DOC_PREFIXES entry.  Deterministic walk
    over the docs/ directory; an absent docs/ degrades to an empty
    tuple."""
    docs_dir = os.path.join(repo_root, "docs")
    if not os.path.isdir(docs_dir):
        return ()
    out = []
    for name in sorted(os.listdir(docs_dir)):
        if not os.path.isfile(os.path.join(docs_dir, name)):
            continue
        rel = "docs/" + name
        if rel.startswith(GOVERNING_DOC_PREFIXES):
            out.append(rel)
    return tuple(out)


def exclusion_roster(repo_root):
    """(frozen_rel_files, frozen_dir_families) for repair targeting: the
    runtime LEDGER8 rows plus the append-only ledger document plus the
    governing-document faces, and the frozen directory families.  This
    is the shared F1/E2 shape."""
    rows, _src = frozen8_ledger(repo_root)
    doc, _src2 = ledger_doc(repo_root)
    return (rows + [doc] + list(governing_doc_faces(repo_root)),
            FROZEN_DIR_FAMILIES)


def full_frozen_files(repo_root):
    """Ten ledger/checker rows plus the append-only document, first-seen
    order, deduplicated."""
    rows, _ = frozen8_ledger(repo_root)
    checkers, _ = frozen8_checkers(repo_root)
    doc, _ = ledger_doc(repo_root)
    seen, out = set(), []
    for rel in rows + checkers + [doc]:
        if rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


# --- append zone: add your provider class below this marker ---
# (read-merge-write only; never rewrite the whole file; keep this marker)


# --- class 1 (lane-extract, ticket E2-1) provider scope ---
# Append guard: a merge finding LaneExtractScope already defined below
# must stay a textual no-op (idempotent append, read-merge-write).
#
# The lane-registered-file-missing guard institutionalizing commit
# 2748b52 (triage table class R1 markers: "can't open file" / "No such
# file or directory" / rc=2): a rostered CASES lane whose referenced
# file is absent is detected read-only; --lane-apply drops exactly that
# lane's registration line from the CASES roster and keeps the function
# body, so the lane re-registers (rc=111 skip protocol) once the file
# is restored.  Every applied repair appends one repair-ledger row
# (class/target/outcome, whitepaper outcome classes); the same-class
# budget per branch is capped and a cap hit escalates (anti oscillation).
# Dry run by default; the write faces pass the shared exclusion
# providers above.

import datetime as _dt  # noqa: E402  (class-1 imports, appended block)
import hashlib as _hashlib  # noqa: E402
import json as _json  # noqa: E402
import re as _re  # noqa: E402
import subprocess as _subprocess  # noqa: E402


class LaneExtractScope(object):
    """E2 class-1 repair scope: the lane-unregister guard.

    Repair face: tests/run_tests.sh (the CASES roster), one roster line
    per applied repair; the ledger face records the row.  Exclusion set
    (E2 red line, work order over the card face): the shared
    full_frozen_files view, the FROZEN_DIR_FAMILIES families, and the
    docs/zh data subtree.  The whole docs/ tree is deliberately not
    excluded here for the reason the class-3 face records: the ledger
    append face is an accounting face, not a repair target.
    """

    CLASS_ID = "lane-extract"
    TICKET = "E2-1"
    WRITABLE_FACES = ("tests/run_tests.sh", "docs/repair-ledger.jsonl")
    BUDGET_PER_BRANCH = 2
    LEDGER_FACE = "docs/repair-ledger.jsonl"
    LEDGER_ROW_SCHEMA = "rocqwash-repair-ledger/1"
    REPORT_SCHEMA = "rocqwash-lane-guard/1"
    OUTCOME_REPAIRED = "repaired(lane-unregistered)"
    DEFAULT_SUITE = "tests/run_tests.sh"

    @classmethod
    def refusal_reason(cls, rel, repo_root=REPO_ROOT):
        """The refusal reason for a repo-relative write target, or None
        when the target sits inside this class's repair scope."""
        p = (rel or "").replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if not p or p.startswith(".."):
            return "outside the repository tree"
        if p in full_frozen_files(repo_root):
            return "frozen or append-only face (shared full view)"
        hit = dir_family_exclusion(p)
        if hit is not None:
            return hit
        if p == "docs/zh" or p.startswith("docs/zh/"):
            return "data subtree exclusion (docs/zh)"
        return None

    @classmethod
    def check_writable(cls, repo_root=REPO_ROOT):
        """(ok, refusals) for the class write faces - the guard runs this
        before any byte is written (single-source consumption proof)."""
        refusals = []
        for rel in cls.WRITABLE_FACES:
            reason = cls.refusal_reason(rel, repo_root)
            if reason is not None:
                refusals.append((rel, reason))
        return (not refusals), refusals


LANE_CASES_RE = _re.compile(r'(?ms)^CASES="(.*?)"')
LANE_FUNC_RE = "(?ms)^%s\\(\\)\\s*\\{(.*?)^\\}"
LANE_REF_RE = _re.compile(r"\$(REPO|FIX)/([A-Za-z0-9_][A-Za-z0-9_./-]*)")


class LaneMissingInput(Exception):
    """Exit-code 9 face: a named input is absent or unreadable."""


class LaneRefused(Exception):
    """Exit-code 2 face: refused repair or failed post-assertion."""


def _lane_resolve(repo_root, path):
    """A relative ledger path resolves against the audited repo root,
    never against the process CWD."""
    if os.path.isabs(path):
        return path
    return os.path.join(repo_root, path.replace("/", os.sep))


def lane_norm_rel(rel):
    rel = (rel or "").replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel.strip("/")


def lane_roster_names(text):
    m = LANE_CASES_RE.search(text)
    if m is None:
        raise LaneMissingInput("suite shape unrecognized (no CASES block)")
    return m.group(1).replace("\\\n", " ").split()


def lane_function_body(text, name):
    m = _re.search(LANE_FUNC_RE % _re.escape(name), text)
    return m.group(1) if m else None


def lane_file_refs(text, name):
    """Repo-relative file references in the lane body ($REPO/... and
    $FIX/..., $FIX resolving under tests/fixtures); None when the
    rostered name has no function body at all."""
    body = lane_function_body(text, name)
    if body is None:
        return None
    refs = []
    for var, tok in LANE_REF_RE.findall(body):
        rel = tok if var == "REPO" else "tests/fixtures/" + tok
        rel = lane_norm_rel(rel)
        if "/" in rel or "." in rel:
            refs.append(rel)
    seen, out = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def lane_ghost(repo_root, text, name):
    """Ghost record for one rostered lane, None when the lane is fine.
    missing-file: every referenced file is absent (the R1 ENOENT face).
    missing-function: the roster carries a name with no t_<name> body.
    A lane with mixed present/absent refs is never a ghost here: an env
    or platform leg belongs to the rc=111 skip protocol, not to an auto
    repair."""
    refs = lane_file_refs(text, name)
    if refs is None:
        return {"lane": name, "reason": "missing-function", "refs": [],
                "action": "drop-roster-line"}
    missing = [r for r in refs
               if not os.path.isfile(os.path.join(
                   repo_root, r.replace("/", os.sep)))]
    if refs and len(missing) == len(refs):
        return {"lane": name, "reason": "missing-file", "refs": refs,
                "action": "drop-roster-line"}
    return None


def lane_detect(repo_root, suite_rel=LaneExtractScope.DEFAULT_SUITE):
    """Read-only detection over the CASES roster; (names, ghosts)."""
    path = os.path.join(repo_root, suite_rel.replace("/", os.sep))
    if not os.path.isfile(path):
        raise LaneMissingInput("missing suite file: %s" % path)
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    names = lane_roster_names(text)
    ghosts = [g for g in (lane_ghost(repo_root, text, n) for n in names)
              if g]
    return names, ghosts


def lane_drop_roster_line(text, name):
    """Remove exactly the one roster line for the lane inside the CASES
    block; when it was the block's last entry (the regex terminator is
    the roster's closing quote, so a tail line never carries the quote
    itself - the position decides), the previous surviving line's
    continuation backslash becomes the closing quote.  Bytes outside the
    block stay untouched (minimal diff, 2748b52 shape)."""
    m = LANE_CASES_RE.search(text)
    if m is None:
        raise LaneMissingInput("suite shape unrecognized (no CASES block)")
    lines = m.group(1).split("\n")
    idx = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s in (name, name + " \\", name + '"'):
            idx = i
            break
    if idx is None:
        raise LaneRefused("lane not found in the roster block: %s" % name)
    # tail entry: nothing but blank lines between the dropped line and the
    # block end (the closing quote terminates group(1) and is not carried
    # in the lines)
    was_last = all(not ln.strip() for ln in lines[idx + 1:])
    del lines[idx]
    tail_skip = 0
    if was_last:
        # the rebuilt closing quote subsumes the original terminator, so
        # exactly that one terminator character is dropped from the tail
        # splice (no doubled quote)
        if text[m.end(1):m.end(1) + 1] == '"':
            tail_skip = 1
        else:
            raise LaneRefused("roster tail shape unrecognized (the CASES "
                              "block does not close right after the last "
                              "entry); nothing written")
        for j in range(len(lines) - 1, -1, -1):
            if lines[j].strip():
                cr = "\r" if lines[j].endswith("\r") else ""
                body = lines[j].rstrip("\r").rstrip()
                if body.endswith("\\"):
                    body = body[:-1].rstrip()
                lines[j] = body + '"' + cr
                break
    return (text[:m.start(1)] + "\n".join(lines)
            + text[m.end(1) + tail_skip:])


def lane_ledger_rows(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with io.open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_json.loads(line))
            except ValueError:
                raise LaneRefused("repair ledger row is not valid JSON: %s"
                                  % path)
    return rows


def _lane_ledger_gate(repo_root, ledger_path):
    """Pre-write gate: refuse before any byte lands when the ledger face
    itself is excluded (a repair must never go through without its
    ledger row; never a partial write)."""
    resolved = _lane_resolve(repo_root, ledger_path)
    abs_path = os.path.abspath(resolved)
    base = os.path.abspath(repo_root)
    if abs_path == base or abs_path.startswith(base.rstrip(os.sep) + os.sep):
        reason = LaneExtractScope.refusal_reason(
            os.path.relpath(resolved, repo_root), repo_root)
        if reason:
            raise LaneRefused("excluded ledger face: %s" % reason)


def _lane_ledger_append(repo_root, path, row):
    """One ledger append; the ledger write face passes the same exclusion
    gate as any repair write face when it sits inside the repo."""
    resolved = _lane_resolve(repo_root, path)
    abs_path = os.path.abspath(resolved)
    base = os.path.abspath(repo_root)
    if abs_path == base or abs_path.startswith(base.rstrip(os.sep)
                                              + os.sep):
        reason = LaneExtractScope.refusal_reason(
            os.path.relpath(resolved, repo_root), repo_root)
        if reason:
            raise LaneRefused("excluded ledger face: %s" % reason)
    parent = os.path.dirname(abs_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(resolved, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(_json.dumps(row, ensure_ascii=False, sort_keys=True)
                 + "\n")


def _lane_utc():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lane_branch(repo_root):
    try:
        pr = _subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                             cwd=repo_root, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=10)
    except Exception:
        return None
    if pr.returncode != 0:
        return None
    out = pr.stdout.decode("utf-8", "replace").strip()
    return out or None


def _lane_repaired_count(rows, target):
    scope = LaneExtractScope
    return sum(1 for r in rows
               if r.get("class") == scope.CLASS_ID
               and r.get("target") == target
               and str(r.get("outcome", "")).startswith("repaired"))


def _lane_escalate(repo_root, ledger_path, target, kind, ghosts):
    row = {"schema": LaneExtractScope.LEDGER_ROW_SCHEMA,
           "class": LaneExtractScope.CLASS_ID, "target": target,
           "lanes": [g["lane"] for g in ghosts],
           "outcome": "escalated(%s)" % kind, "utc": _lane_utc()}
    try:
        _lane_ledger_append(repo_root, ledger_path, row)
    except LaneRefused:
        pass   # ledger face itself excluded: refusal stands, no row


def lane_apply(repo_root, ledger_path, ghosts, apply,
               suite_rel=LaneExtractScope.DEFAULT_SUITE):
    """Drop every ghost lane's roster line under the exclusion and budget
    gates, with post-assertions and one repair-ledger row per applied
    repair.
    Dry run by default; returns (outcome, applied)."""
    scope = LaneExtractScope
    reason = scope.refusal_reason(suite_rel, repo_root)
    if reason and apply:
        _lane_escalate(repo_root, ledger_path, lane_norm_rel(suite_rel),
                       "excluded-face", ghosts)
        raise LaneRefused("excluded repair face (%s); use the standing "
                          "sync protocol instead" % reason)
    if apply:
        _lane_ledger_gate(repo_root, ledger_path)
    target = lane_norm_rel(suite_rel)
    rows = lane_ledger_rows(_lane_resolve(repo_root, ledger_path))
    if _lane_repaired_count(rows, target) >= scope.BUDGET_PER_BRANCH:
        _lane_escalate(repo_root, ledger_path, target, "budget-cap",
                       ghosts)
        raise LaneRefused("repair budget exhausted for %s (%d prior %s "
                          "repairs); escalate to the desk"
                          % (target, scope.BUDGET_PER_BRANCH,
                             scope.CLASS_ID))
    if not ghosts:
        return "clean", False
    if not apply:
        return "planned", False
    path = os.path.join(repo_root, suite_rel.replace("/", os.sep))
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        orig = fh.read()
    names_before = lane_roster_names(orig)
    text = orig
    for g in ghosts:
        text = lane_drop_roster_line(text, g["lane"])
    dropped = [g["lane"] for g in ghosts]
    if lane_roster_names(text) != [n for n in names_before
                                   if n not in dropped]:
        raise LaneRefused("post-assertion failed: roster after the drop "
                          "is not the prior roster minus the ghost "
                          "lanes; nothing written")
    for n in lane_roster_names(text):
        if lane_function_body(text, n) is None:
            raise LaneRefused("post-assertion failed: lane %s lost its "
                              "function body; nothing written" % n)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    row = {"schema": scope.LEDGER_ROW_SCHEMA, "class": scope.CLASS_ID,
           "target": target, "lanes": dropped,
           "outcome": scope.OUTCOME_REPAIRED, "utc": _lane_utc()}
    branch = _lane_branch(repo_root)
    if branch:
        row["branch"] = branch
    _lane_ledger_append(repo_root, ledger_path, row)
    return scope.OUTCOME_REPAIRED, True


def _lane_md5(path):
    with io.open(path, "rb") as fh:
        return _hashlib.md5(fh.read()).hexdigest()


# --- class 2 (roster-resync, ticket E2-2) provider scope ---
class RosterResyncScope(object):
    """E2 class-2 repair scope: the roster count drift guard.

    Repair face: the count lines of tests/README.md and README.md are
    re-derived one-way from the tests/run_tests.sh CASES roster and the
    drifted digits are rewritten in place; the roster file itself is never
    a write target.  Exclusion set: the shared full_frozen_files view,
    the FROZEN_DIR_FAMILIES and LEGAL_DATA_DIR_FAMILIES families, and the
    docs/zh archive subtree plus the sibling .zh.md archives (annotation
    standard card 5.2), matching the class-3 refusal shape.
    """

    CLASS_ID = "roster-resync"
    TICKET = "E2-2"
    WRITABLE_FACES = ("tests/README.md", "README.md",
                      "docs/repair-ledger.jsonl")
    BUDGET_PER_BRANCH = 2
    LEDGER_FACE = "docs/repair-ledger.jsonl"
    REPAIR_ROW_SCHEMA = "rocqwash-repair/1"
    REPAIRED_OUTCOME = "repaired(count-resync)"
    ARCHIVE_PREFIXES = ("docs/zh/",)
    ARCHIVE_SUFFIXES = (".zh.md",)

    @classmethod
    def refusal_reason(cls, rel, repo_root=REPO_ROOT):
        """The refusal reason for a repo-relative write target, or None
        when the target sits inside this class's repair scope."""
        p = (rel or "").replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if not p or p.startswith(".."):
            return "outside the repository tree"
        if p in full_frozen_files(repo_root):
            return "frozen or append-only face (shared full view)"
        hit = dir_family_exclusion(p)
        if hit is not None:
            return hit
        top = p.split("/", 1)[0]
        if top in LEGAL_DATA_DIR_FAMILIES and p != cls.LEDGER_FACE:
            return "legal or data face exclusion (%s/)" % top
        if p == "docs/zh" or p.startswith("docs/zh/"):
            return "data subtree exclusion (docs/zh)"
        if p.endswith(cls.ARCHIVE_SUFFIXES):
            return "archive face exclusion (.zh.md)"
        return None

    @classmethod
    def check_writable(cls, repo_root=REPO_ROOT):
        """(ok, refusals) for the class write faces - the guard runs this
        before any byte is written (single-source consumption proof)."""
        refusals = []
        for rel in cls.WRITABLE_FACES:
            reason = cls.refusal_reason(rel, repo_root)
            if reason is not None:
                refusals.append((rel, reason))
        return (not refusals), refusals


def check_faces(repo_root, rels, a2_table=None):
    """The --check CLI face: one verdict line per rel (EXCLUDED or
    REPAIRABLE; a verdict is data).  --a2-table adds the A2 mapping-source
    table face to the exclusion set for this query (the F1 single-source
    form).  Exit 1 when any path is excluded (the documented face), 0
    when all are repairable, 9 on a missing input, 2 for argparse."""
    extra = ()
    if a2_table is not None:
        if not os.path.isfile(a2_table):
            sys.stderr.write("repair_scope: FAIL-LOUD --a2-table file"
                             " missing: %s\n" % a2_table)
            return 9
        norm = a2_table.replace("\\", "/")
        try:
            norm = os.path.relpath(a2_table, repo_root).replace("\\", "/")
        except ValueError:
            pass
        extra = (norm,)
    any_excluded = False
    try:
        for rel in rels:
            reason = RosterResyncScope.refusal_reason(rel, repo_root)
            if reason is not None:
                any_excluded = True
                print("EXCLUDED %s" % rel)
            else:
                print("REPAIRABLE %s" % rel)
    except (OSError, ValueError) as e:
        sys.stderr.write("repair_scope: FAIL-LOUD check read: %s\n" % e)
        return 9
    return 1 if any_excluded else 0


def classes_face():
    """The --classes CLI face: one line per registered repair class (class
    id, ticket, writable faces, per-branch budget) - the budget registry
    the cw.sh hint documents."""
    for cls in (LaneExtractScope, RosterResyncScope, FlakyQuarantineScope):
        print("%s %s targets=%s budget=%d"
              % (cls.CLASS_ID, cls.TICKET, ",".join(cls.WRITABLE_FACES),
                 cls.BUDGET_PER_BRANCH))
    return 0


# --- end class 2 (roster-resync, ticket E2-2) provider scope ---


# --- class 3 (flaky-quarantine, ticket E2-3) provider scope ---
class FlakyQuarantineScope(object):
    """E2 class-3 repair scope: the advisory-roster quarantine face.

    Exclusion set (the frozen-set inventory and three-anchor recipe
    techdoc, E2 section - the work order over the card face): the shared
    full_frozen_files view (runtime
    LEDGER8 rows plus the CHECKERS meta-freeze rows plus the append-only
    ledger document), the FROZEN_DIR_FAMILIES families, and the docs/zh
    archive subtree.  LEGAL_DATA_DIR_FAMILIES is the lane-extract class's
    stricter local face and is deliberately not consumed here: the repair
    ledger append face (docs/repair-ledger.jsonl) is an accounting face,
    not a repair target, and the E2 red line pins docs/zh - not the whole
    docs/ tree - as the excluded data face.
    """

    CLASS_ID = "flaky-quarantine"
    TICKET = "E2-3"
    WRITABLE_FACES = ("tests/advisory_roster.txt", "docs/repair-ledger.jsonl")
    BUDGET_PER_BRANCH = 2

    @classmethod
    def refusal_reason(cls, rel, repo_root=REPO_ROOT):
        """The refusal reason for a repo-relative write target, or None
        when the target sits inside this class's repair scope."""
        p = (rel or "").replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if not p or p.startswith(".."):
            return "outside the repository tree"
        if p in full_frozen_files(repo_root):
            return "frozen or append-only face (shared full view)"
        hit = dir_family_exclusion(p)
        if hit is not None:
            return hit
        if p == "docs/zh" or p.startswith("docs/zh/"):
            return "data subtree exclusion (docs/zh)"
        return None

    @classmethod
    def check_writable(cls, repo_root=REPO_ROOT):
        """(ok, refusals) for the class write faces - the guard runs this
        before any byte is written (single-source consumption proof)."""
        refusals = []
        for rel in cls.WRITABLE_FACES:
            reason = cls.refusal_reason(rel, repo_root)
            if reason is not None:
                refusals.append((rel, reason))
        return (not refusals), refusals


# --- class 4 (doc-count, ticket E2-4) provider scope ---
class DocCountScope(object):
    """E2 class-4 repair scope: the doc count drift guard.

    Face class: the count faces of the capability-index class, registry-
    or roster-derived doc counts such as the README-cw.md title
    "N routes over M tools".  A drifted face is recomputed one way from
    the sources (the tool registry = the cw.sh case routes joined with
    the tools/ entry points whose name does not start with '_', the same
    registry doc_lint check 1 reconciles; the test roster = the
    tests/run_tests.sh CASES count, carried for visibility) and only the
    count tokens inside the matched span are rewritten in place; the
    sources are never an edit target.  The census-time counts inside
    docs/CAPABILITY-INDEX.md are deliberately not faces: that file pins
    its counts to the census anchor (its section 6 anchor-lag register),
    so a rewrite would destroy a declared word-face fact, not repair one.

    Exclusion set (E2 red line): the shared full_frozen_files view, the
    FROZEN_DIR_FAMILIES families, the docs/zh archive subtree, plus the
    sibling .zh.md archive mirrors (annotation standard card 5.2) - a
    translation archive copies its canonical face, it is never machine
    rewritten.  LEGAL_DATA_DIR_FAMILIES is not consumed here (the
    class-3 reasoning applies: a count face may legitimately sit under
    docs/, and the red line pins docs/zh, not the whole docs/ tree).
    """

    CLASS_ID = "doc-count"
    TICKET = "E2-4"
    WRITABLE_FACES = ("README-cw.md", "docs/repair-ledger.jsonl")
    BUDGET_PER_BRANCH = 2
    LEDGER_FACE = "docs/repair-ledger.jsonl"
    LEDGER_ROW_SCHEMA = "rocqwash-repair-ledger/1"
    REPORT_SCHEMA = "rocqwash-doc-count-guard/1"
    OUTCOME_REPAIRED = "repaired(doc-count-sync)"
    ARCHIVE_SUFFIXES = (".zh.md",)

    @classmethod
    def refusal_reason(cls, rel, repo_root=REPO_ROOT):
        """The refusal reason for a repo-relative write target, or None
        when the target sits inside this class's repair scope."""
        p = (rel or "").replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if not p or p.startswith(".."):
            return "outside the repository tree"
        if p in full_frozen_files(repo_root):
            return "frozen or append-only face (shared full view)"
        hit = dir_family_exclusion(p)
        if hit is not None:
            return hit
        if p == "docs/zh" or p.startswith("docs/zh/"):
            return "data subtree exclusion (docs/zh)"
        if p.endswith(cls.ARCHIVE_SUFFIXES):
            return "archive face exclusion (.zh.md)"
        return None

    @classmethod
    def check_writable(cls, repo_root=REPO_ROOT):
        """(ok, refusals) for the class write faces - the guard runs this
        before any byte is written (single-source consumption proof)."""
        refusals = []
        for rel in cls.WRITABLE_FACES:
            reason = cls.refusal_reason(rel, repo_root)
            if reason is not None:
                refusals.append((rel, reason))
        return (not refusals), refusals


class DocCountRefused(Exception):
    """Exit-code 2 face: refused repair or failed post-assertion."""


# The face table: one row per count-carrying doc surface.  parts = the
# named groups of the pattern in reconstruction order; keys = the
# value-bearing groups (the only tokens a repair may ever touch).
# The title face anchors on the "^# cw.sh" prefix and the
# "routes over <N> tools" tail only; everything in between (the suite
# wording) is deliberately unconstrained.  The former " tool suite "
# literal requirement let a pure prose refresh (02da21f, "tool suite" ->
# "the Rocq operations suite") blind the guard while --selftest stayed
# green - triage class R21.  Suite wording must never break the face
# again: the face is the prefix + the count tail, nothing else.
DOC_COUNT_TITLE_RE = _re.compile(
    r"(?P<pre>^# cw\.sh\b[^\r\n]*? )"
    r"(?P<routes>\d+)"
    r"(?P<mid> routes over )"
    r"(?P<tools>\d+)"
    r"(?P<post> tools[^\r\n]*)",
    _re.MULTILINE)

DOC_COUNT_FACES = (
    {"file": "README-cw.md", "label": "title-routes-over-tools",
     "keys": ("routes", "tools"),
     "parts": ("pre", "routes", "mid", "tools", "post"),
     "re": DOC_COUNT_TITLE_RE},
)

# Verdict-failure statuses for the class-4 detect/apply aggregation.
# missing-face is a FAILURE class, never a neutral skip: a face listed in
# the source-of-truth table whose title shape cannot be located means the
# guard is blind on that surface, and a blind guard must alarm (triage
# class R21: "selftest PASS while face missing" - the 02da21f regression
# stayed green exactly because this class used to be skipped).  ok /
# drift / excluded / missing-file keep their standing meanings; excluded
# stays neutral (an excluded face is a guard-correct skip, like the
# self-heal watch's own skips).
DC_FAILURE_STATUSES = ("drift", "missing-face")


def _dc_failure(rows):
    """True when any detect row carries a verdict-failure status."""
    return any(r["status"] in DC_FAILURE_STATUSES for r in rows)


def _dc_doc_lint():
    """The doc_lint module (robust import: same-directory first, then
    repo-layout candidates, so the temp-fixture selftest form and CI runners
    both resolve the single derivation source for the cw.sh and roster
    parsers; loud ModuleNotFoundError when no candidate carries it)."""
    try:
        import doc_lint
        return doc_lint
    except ModuleNotFoundError:
        pass
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [
        os.path.join(here, "doc_lint.py"),
        os.path.join(os.environ.get("ROCWASH_TOOLS_DIR", ""), "doc_lint.py"),
        os.path.join(os.getcwd(), "doc_lint.py"),
        os.path.join(os.getcwd(), "tools", "doc_lint.py"),
        os.path.join(os.path.dirname(here), "doc_lint.py"),
    ]
    seen = set()
    for c in cands:
        if not c or c in seen:
            continue
        seen.add(c)
        if os.path.isfile(c):
            spec = importlib.util.spec_from_file_location("doc_lint", c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules["doc_lint"] = mod
            return mod
    raise ModuleNotFoundError(
        "doc_lint not importable: searched script dir, ROCWASH_TOOLS_DIR, "
        "cwd, cwd/tools, copy-sibling dir; set ROCWASH_TOOLS_DIR when the "
        "script runs as a detached temp copy")


def doc_count_derive(repo_root):
    """One-way count derivation -> {"routes", "tools", "cases",
    "registry"}.  routes = the cw.sh case routes; tools = the registry
    size (the routed target paths joined with the tools/ entry points
    whose name does not start with '_'); cases = the run_tests.sh CASES
    roster token count.  Raises doc_lint.MissingInput / doc_lint.ToolError
    when a source is absent or shapeless; the sources themselves are
    never an edit target of this guard."""
    dl = _dc_doc_lint()
    case = dl.parse_cw_sh(repo_root)["case"]
    paths = [v["path"] for v in case.values() if v.get("path")]
    tools_dir = os.path.join(repo_root, "tools")
    if not os.path.isdir(tools_dir):
        raise dl.MissingInput("the audited repo lacks the tools/ directory:"
                              " %s" % tools_dir)
    generic = ["tools/" + fn for fn in os.listdir(tools_dir)
               if fn.endswith(".py") and not fn.startswith("_")]
    registry = sorted(set(paths) | set(generic))
    rt_rel = "tests/run_tests.sh"
    rt_path = os.path.join(repo_root, "tests", "run_tests.sh")
    if not os.path.isfile(rt_path):
        raise dl.MissingInput("the audited repo lacks %s: %s"
                              % (rt_rel, rt_path))
    rt_text = dl.read_text(rt_path, rt_rel)
    m = dl.CASES_RE.search(rt_text)
    if m is None:
        raise dl.ToolError("run_tests.sh shape unrecognized (no CASES"
                           " block): %s" % rt_path)
    tokens = m.group(1).replace("\\\n", " ").split()
    return {"routes": len(case), "tools": len(registry),
            "cases": len(tokens), "registry": registry}


def _dc_read(repo_root, rel):
    path = os.path.join(repo_root, rel.replace("/", os.sep))
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _dc_row(face, rel, line, status, doc, source, action, detail):
    return {"kind": "doc-count", "face": face, "file": rel, "line": line,
            "status": status, "doc": doc, "source": source,
            "action": action, "detail": detail}


def doc_count_detect(repo_root, faces=None):
    """Report-first drift scan over the count faces (zero writes).  Rows
    are data: ok / drift / excluded / missing-face / missing-file.
    missing-face is a verdict-failure class (R21): a listed face whose
    title shape never appeared alarms the verdict, it is never
    neutral-skipped."""
    derived = doc_count_derive(repo_root)
    rows = []
    for face in (tuple(faces) if faces is not None else DOC_COUNT_FACES):
        rel = face["file"]
        source = {k: derived[k] for k in face["keys"]}
        if DocCountScope.refusal_reason(rel, repo_root) is not None:
            rows.append(_dc_row(face["label"], rel, None, "excluded", None,
                                source, "none",
                                "excluded face (frozen scope); never"
                                " repaired"))
            continue
        path = os.path.join(repo_root, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            rows.append(_dc_row(face["label"], rel, None, "missing-file",
                                None, source, "none",
                                "the face file is absent: %s" % rel))
            continue
        text = _dc_read(repo_root, rel)
        matches = list(face["re"].finditer(text))
        if not matches:
            rows.append(_dc_row(face["label"], rel, None, "missing-face",
                                None, source, "none",
                                "the count-face shape never appeared"
                                " (the face is missing)"))
            continue
        for m in matches:
            doc_vals = {k: int(m.group(k)) for k in face["keys"]}
            drift = {k: (doc_vals[k], derived[k])
                     for k in face["keys"] if doc_vals[k] != derived[k]}
            line = text.count("\n", 0, m.start()) + 1
            if drift:
                detail = "count drift: " + ", ".join(
                    "%s doc=%d source=%d" % (k, a, b)
                    for k, (a, b) in sorted(drift.items()))
                rows.append(_dc_row(face["label"], rel, line, "drift",
                                    doc_vals, source, "rewrite-count",
                                    detail))
            else:
                detail = "face equals the derived source (" + ", ".join(
                    "%s=%d" % (k, derived[k]) for k in face["keys"]) + ")"
                rows.append(_dc_row(face["label"], rel, line, "ok",
                                    doc_vals, source, "none", detail))
    return rows


def _dc_rebuild(match, face, derived):
    return "".join(str(derived[g]) if g in face["keys"] else match.group(g)
                   for g in face["parts"])


def _dc_ledger_path(repo_root, ledger_path):
    """The ledger face resolved: a relative path is repo-relative
    (the ledger is a repo face), an absolute path passes through.
    Never resolved against the process cwd - that let a sandbox
    selftest write rows into the real repo's ledger."""
    if os.path.isabs(ledger_path):
        return ledger_path
    return os.path.join(repo_root, ledger_path.replace("/", os.sep))


def _dc_ledger_append(repo_root, ledger_path, row):
    """One ledger append; the ledger write face passes this class's
    exclusion gate when it sits inside the repo (the class-1 shape)."""
    ledger_path = _dc_ledger_path(repo_root, ledger_path)
    abs_path = os.path.abspath(ledger_path)
    base = os.path.abspath(repo_root)
    if abs_path == base or abs_path.startswith(base.rstrip(os.sep)
                                              + os.sep):
        reason = DocCountScope.refusal_reason(
            os.path.relpath(ledger_path, repo_root), repo_root)
        if reason:
            raise DocCountRefused("excluded ledger face: %s" % reason)
    parent = os.path.dirname(abs_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(ledger_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(_json.dumps(row, ensure_ascii=False, sort_keys=True)
                 + "\n")


def doc_count_repair(repo_root, apply=False, faces=None,
                     ledger_path=DocCountScope.LEDGER_FACE):
    """Rewrite every drifted count token to face value = source value,
    under the exclusion, budget, and post-assertion gates.  Dry run by
    default (plan rows only, zero writes).  Returns (plan, applied)."""
    scope = DocCountScope
    ok_faces, refusals = scope.check_writable(repo_root)
    if apply and not ok_faces:
        raise DocCountRefused("write faces refused: %s"
                              % ("; ".join("%s (%s)" % r for r in refusals)))
    derived = doc_count_derive(repo_root)
    plan = []
    pending = []
    for face in (tuple(faces) if faces is not None else DOC_COUNT_FACES):
        rel = face["file"]
        source = {k: derived[k] for k in face["keys"]}
        row = {"kind": "doc-count", "face": face["label"], "file": rel,
               "line": None, "doc": None, "source": source}
        reason = scope.refusal_reason(rel, repo_root)
        if reason is not None:
            if apply:
                raise DocCountRefused("excluded repair face (%s); use the"
                                      " standing sync protocol instead"
                                      % reason)
            row.update({"status": "excluded", "action": "none",
                        "detail": "excluded face (frozen scope); refused"})
            plan.append(row)
            continue
        path = os.path.join(repo_root, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            row.update({"status": "missing-file", "action": "none",
                        "detail": "the face file is absent: %s" % rel})
            plan.append(row)
            continue
        raw_text = _dc_read(repo_root, rel)
        matches = list(face["re"].finditer(raw_text))
        if not matches:
            row.update({"status": "missing-face", "action": "none",
                        "detail": "the count-face shape never appeared"
                                  " (no rewrite is possible)"})
            plan.append(row)
            continue
        m = matches[0]
        row["line"] = raw_text.count("\n", 0, m.start()) + 1
        row["doc"] = {k: int(m.group(k)) for k in face["keys"]}
        if row["doc"] == source:
            row.update({"status": "ok", "action": "none",
                        "detail": "face already equals the source; zero"
                                  " bytes changed"})
            plan.append(row)
            continue
        row.update({"status": "drift", "action": "rewrite-count",
                    "detail": "count tokens rewritten to face value ="
                              " source value"})
        plan.append(row)
        pending.append((face, path, raw_text, row))
    if not apply or not pending:
        return plan, False
    for face, path, raw_text, row in pending:
        rel = face["file"]
        rows_prior = lane_ledger_rows(
            _dc_ledger_path(repo_root, ledger_path))
        prior = sum(1 for r in rows_prior
                    if r.get("class") == scope.CLASS_ID
                    and r.get("target") == rel
                    and str(r.get("outcome", "")).startswith("repaired"))
        if prior >= scope.BUDGET_PER_BRANCH:
            cap = {"schema": scope.LEDGER_ROW_SCHEMA,
                   "class": scope.CLASS_ID, "target": rel,
                   "outcome": "escalated(budget-cap)", "utc": _lane_utc()}
            try:
                _dc_ledger_append(repo_root, ledger_path, cap)
            except DocCountRefused:
                pass   # the ledger face itself excluded: refusal stands
            raise DocCountRefused(
                "repair budget exhausted for %s (%d prior %s repairs);"
                " escalate to the desk"
                % (rel, scope.BUDGET_PER_BRANCH, scope.CLASS_ID))
        new_text = face["re"].sub(
            lambda mm, f=face: _dc_rebuild(mm, f, derived), raw_text)
        m2 = face["re"].search(new_text)
        if m2 is None or {k: int(m2.group(k)) for k in face["keys"]} \
                != {k: derived[k] for k in face["keys"]}:
            row.update({"status": "refused", "action": "none",
                        "detail": "post-assertion failed: the rebuilt face"
                                  " does not equal the source; nothing"
                                  " written"})
            continue
        if new_text == raw_text:
            row.update({"status": "ok", "action": "none",
                        "detail": "face already equals the source; zero"
                                  " bytes changed"})
            continue
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
        back = _dc_read(repo_root, rel)
        m3 = face["re"].search(back)
        if m3 is None or {k: int(m3.group(k)) for k in face["keys"]} \
                != {k: derived[k] for k in face["keys"]}:
            raise DocCountRefused("post-assertion failed on %s after the"
                                  " write; the desk must reconcile" % rel)
        row["status"] = "repaired"
        ledger_row = {"schema": scope.LEDGER_ROW_SCHEMA,
                      "class": scope.CLASS_ID, "target": rel,
                      "outcome": scope.OUTCOME_REPAIRED, "utc": _lane_utc()}
        branch = _lane_branch(repo_root)
        if branch:
            ledger_row["branch"] = branch
        try:
            _dc_ledger_append(repo_root, ledger_path, ledger_row)
        except DocCountRefused:
            pass   # the ledger face itself excluded: repair stands, no row
    applied = any(r["status"] == "repaired" for r in plan)
    return plan, applied


def doc_count_cli(args):
    """Class-4 operator face (--doc-count-detect / --doc-count-apply).
    Returns the process code: 0 clean or repaired clean; 1 a verdict
    failure remaining (detect) or residual (apply) - drift, or a
    missing face (a listed face whose title shape is gone; alarm,
    never a neutral skip, R21); 2 refused; 9 missing input."""
    try:
        dl = _dc_doc_lint()
    except (ImportError, OSError) as e:
        sys.stderr.write("repair_scope: FAIL-LOUD doc_lint import failed:"
                         " %s\n" % e)
        return 9
    try:
        if not os.path.isdir(args.repo):
            sys.stderr.write("repair_scope: FAIL-LOUD --repo directory"
                             " missing: %s\n" % args.repo)
            return 9
        derived = doc_count_derive(args.repo)
        summary = {"routes": derived["routes"], "tools": derived["tools"],
                   "cases": derived["cases"]}
        if args.doc_count_detect:
            rows = doc_count_detect(args.repo)
            drift = any(r["status"] == "drift" for r in rows)
            missing = any(r["status"] == "missing-face" for r in rows)
            report = {"schema": DocCountScope.REPORT_SCHEMA,
                      "face": DocCountScope.CLASS_ID, "mode": "detect",
                      "derived": summary, "rows": rows,
                      "budget_per_branch": DocCountScope.BUDGET_PER_BRANCH}
            _dc_emit(args, report, rows,
                     "drift" if drift else ("missing-face" if missing
                                            else "clean"),
                     False, ())
            return 1 if (drift or missing) else 0
        plan, applied = doc_count_repair(args.repo, apply=True,
                                         ledger_path=args.ledger)
        rows = doc_count_detect(args.repo)
        drift = any(r["status"] == "drift" for r in rows)
        residual = _dc_failure(rows)   # drift or missing-face stays open
        outcome = ("residual-drift" if drift else
                   ("residual-missing-face" if residual else
                    ("repaired" if applied else "clean")))
        report = {"schema": DocCountScope.REPORT_SCHEMA,
                  "face": DocCountScope.CLASS_ID, "mode": "apply",
                  "derived": summary, "plan": plan, "rows": rows,
                  "budget_per_branch": DocCountScope.BUDGET_PER_BRANCH}
        _dc_emit(args, report, rows, outcome, applied, plan)
        return 1 if residual else 0
    except (dl.MissingInput, dl.ToolError, OSError) as e:
        sys.stderr.write("MISSING-INPUT: %s\n" % e)
        return 9
    except (DocCountRefused, LaneRefused) as e:
        print("REFUSED: %s" % e)
        return 2


def _dc_emit(args, report, rows, outcome, applied, plan):
    if args.json_out:
        parent = os.path.dirname(os.path.abspath(args.json_out))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(args.json_out, "w", encoding="utf-8", newline="\n") \
                as fh:
            fh.write(_json.dumps(report, ensure_ascii=False, sort_keys=True,
                                 indent=1) + "\n")
    for r in rows:
        line = "" if r.get("line") is None else ":%d" % r["line"]
        print("%s %s%s doc=%s source=%s action=%s"
              % (r["status"], r["file"], line, r.get("doc"),
                 r.get("source"), r.get("action")))
        if r.get("detail"):
            print("  %s" % r["detail"])
    for r in plan:
        if r["status"] in ("repaired", "refused"):
            print("plan %s %s - %s" % (r["status"], r["file"],
                                       r.get("detail", "")))
    print("outcome=%s applied=%s" % (outcome, str(bool(applied)).lower()))


# --- class 4 fixtures (tmp only; zero writes outside mkdtemp) ---

DC_MINI_CW_SH = "\n".join([
    "#!/usr/bin/env bash",
    "# mini route table fixture (doc-count selftest sandbox)",
    "set -u",
    "usage() {",
    "cat <<'EOF'",
    "usage: cw.sh <route> [args]",
    "Tools:",
    "alpha   tools/alpha.py",
    "beta    tools/beta.py",
    "EOF",
    "}",
    "hint_for() {",
    "  case \"$1\" in",
    "    alpha) echo \"cw.sh alpha   # alpha tool\" ;;",
    "    beta) echo \"cw.sh beta   # beta tool\" ;;",
    "  esac",
    "}",
    "case \"${1:-}\" in",
    "  alpha) shift; run_tool alpha \"tools/alpha.py\" \"$@\" ;;",
    "  beta) shift; run_tool beta \"tools/beta.py\" \"$@\" ;;",
    "  *) usage; exit 2 ;;",
    "esac",
]) + "\n"

DC_MINI_RUN_TESTS = ('#!/usr/bin/env bash\nCASES="\\\n'
                     "t_one \\\nt_two \\\n\"\n")

DC_MINI_TOOL = ('#!/usr/bin/env python3\n'
                '"""mini tool fixture (not executed by the guard)."""\n')

DC_MINI_README = ("# cw.sh - unified entry quick reference (rocqos"
                  " (rocqwash) tool suite | 2 routes over 2 tools)\n")

# The regressed title shape (02da21f refreshed the suite wording; the old
# regex - pinned to the " tool suite " literal - went blind: finditer no
# match, neutral missing-face skip, --selftest stayed green).  Under the
# modernized face regex this is simply a face whose count tail is gone:
# the missing-face fixture for the false-green kill vector (R21).
DC_MINI_README_BLIND = ("# cw.sh - unified entry quick reference (rocqos"
                        " (rocqwash), the Rocq operations suite)\n")


def _dc_face_at(rel):
    face = dict(DOC_COUNT_FACES[0])
    face["file"] = rel
    face["label"] = "title-routes-over-tools@%s" % rel
    return face


def _dc_mk_repo(root, title=None, ledger_rows=(), alt_rel=None):
    os.makedirs(os.path.join(root, "tools"), exist_ok=True)
    os.makedirs(os.path.join(root, "tests"), exist_ok=True)
    if alt_rel:
        os.makedirs(os.path.join(root, "seeds"), exist_ok=True)
    faces = {"cw.sh": DC_MINI_CW_SH,
             "tests/run_tests.sh": DC_MINI_RUN_TESTS,
             "tools/alpha.py": DC_MINI_TOOL,
             "tools/beta.py": DC_MINI_TOOL,
             alt_rel or "README-cw.md":
                 (title if title is not None else DC_MINI_README)}
    if ledger_rows:
        faces[DocCountScope.LEDGER_FACE] = "".join(
            _json.dumps(r, sort_keys=True) + "\n" for r in ledger_rows)
    for rel, text in faces.items():
        path = os.path.join(root, rel.replace("/", os.sep))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)


def _dc_write_title(root, routes, tools, rel="README-cw.md"):
    path = os.path.join(root, rel.replace("/", os.sep))
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    text = _re.sub(r"\d+ routes over \d+ tools",
                   "%d routes over %d tools" % (routes, tools), text)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _dc_read_title(root, rel="README-cw.md"):
    with io.open(os.path.join(root, rel.replace("/", os.sep)), "r",
                 encoding="utf-8", newline="") as fh:
        m = _re.search(r"(\d+) routes over (\d+) tools", fh.read())
    return (int(m.group(1)), int(m.group(2))) if m else None


def _dc_md5(path):
    with io.open(path, "rb") as fh:
        return _hashlib.md5(fh.read()).hexdigest()


def run_doc_count_selftest():
    """Class-4 fixture vectors: the red example built in a temp sandbox
    (a hand-drifted count face, then the guard repairs it), plus the
    live repo vectors.  Zero writes outside mkdtemp."""
    results = []

    def vec(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    live_repo = _resolve_live_repo()
    try:
        _dc_doc_lint()
        doc_lint_ok = True
    except ModuleNotFoundError:
        doc_lint_ok = False
    if live_repo is None and not doc_lint_ok:
        print("DOC-COUNT-SELFTEST SKIP: detached copy without doc_lint or a"
              " live repo (env-absent family, rc=111 precedent); run from the"
              " repo root or set ROCWASH_TOOLS_DIR / ROCWASH_REPO_DIR")
        return 111
    tmp = tempfile.mkdtemp(prefix="rqw_doc_count_")
    try:
        # the red example lifecycle on one sandbox repo
        repo1 = os.path.join(tmp, "r1")
        os.makedirs(repo1)
        _dc_mk_repo(repo1)
        readme1 = os.path.join(repo1, "README-cw.md")
        baseline = _dc_md5(readme1)

        derived = doc_count_derive(repo1)
        vec("sandbox-derive",
            (derived["routes"], derived["tools"], derived["cases"])
            == (2, 2, 2),
            "routes=2 tools=2 cases=2 derived from the sandbox sources")
        rows = doc_count_detect(repo1)
        vec("clean-detect",
            rows and all(r["status"] == "ok" for r in rows),
            "a consistent fixture detects zero drift")

        _dc_write_title(repo1, 3, 4)
        rows = [r for r in doc_count_detect(repo1) if r["status"] == "drift"]
        vec("drift-detect",
            len(rows) == 1
            and rows[0]["doc"] == {"routes": 3, "tools": 4}
            and rows[0]["source"] == {"routes": 2, "tools": 2}
            and rows[0]["action"] == "rewrite-count",
            "the hand-drifted face is flagged against the derived source")

        plan, applied = doc_count_repair(repo1, apply=False)
        vec("dry-run-zero-write",
            not applied and plan[0]["status"] == "drift"
            and _dc_read_title(repo1) == (3, 4)
            and not os.path.isfile(os.path.join(
                repo1, DocCountScope.LEDGER_FACE)),
            "the dry-run plan reports rewrite-count and writes nothing")

        plan, applied = doc_count_repair(repo1, apply=True)
        ledger1 = lane_ledger_rows(os.path.join(
            repo1, DocCountScope.LEDGER_FACE))
        vec("apply-sync",
            applied and plan[0]["status"] == "repaired"
            and _dc_read_title(repo1) == (2, 2)
            and len(ledger1) == 1
            and ledger1[0]["class"] == DocCountScope.CLASS_ID
            and ledger1[0]["outcome"] == DocCountScope.OUTCOME_REPAIRED
            and ledger1[0]["target"] == "README-cw.md",
            "apply lands face value = source value (3/4 -> 2/2) plus one"
            " repair-ledger row")

        md5_mid = _dc_md5(readme1)
        plan, applied = doc_count_repair(repo1, apply=True)
        vec("idempotent",
            not applied and plan[0]["status"] == "ok"
            and _dc_md5(readme1) == md5_mid
            and len(lane_ledger_rows(os.path.join(
                repo1, DocCountScope.LEDGER_FACE))) == 1,
            "a second apply is a byte-identical no-op and appends nothing")

        rows = doc_count_detect(repo1)
        vec("post-repair-clean",
            all(r["status"] == "ok" for r in rows),
            "detect reports zero drift after the repair")
        vec("tree-integrity",
            _dc_md5(readme1) == baseline,
            "the repaired face is byte-identical to its consistent"
            " baseline (the repair undid the drift exactly)")

        # excluded face refusal (directory family)
        repo2 = os.path.join(tmp, "r2")
        os.makedirs(repo2)
        _dc_mk_repo(repo2, alt_rel="seeds/x.md")
        _dc_write_title(repo2, 9, 9, rel="seeds/x.md")
        alt = (_dc_face_at("seeds/x.md"),)
        rows = doc_count_detect(repo2, faces=alt)
        before = _dc_md5(os.path.join(repo2, "seeds", "x.md"))
        plan, applied = doc_count_repair(repo2, apply=False, faces=alt)
        dry_ok = (rows[0]["status"] == "excluded"
                  and plan[0]["status"] == "excluded" and not applied)
        refused = False
        try:
            doc_count_repair(repo2, apply=True, faces=alt)
        except DocCountRefused:
            refused = True
        vec("excluded-refused",
            dry_ok and refused
            and _dc_md5(os.path.join(repo2, "seeds", "x.md")) == before,
            "an excluded face (seeds/) is refused with zero writes")

        # budget cap: two prior repairs -> refuse + escalate row
        repo3 = os.path.join(tmp, "r3")
        os.makedirs(repo3)
        prior = {"schema": DocCountScope.LEDGER_ROW_SCHEMA,
                 "class": DocCountScope.CLASS_ID, "target": "README-cw.md",
                 "outcome": DocCountScope.OUTCOME_REPAIRED}
        _dc_mk_repo(repo3, ledger_rows=(prior, prior))
        _dc_write_title(repo3, 5, 5)
        refused = False
        try:
            doc_count_repair(repo3, apply=True)
        except DocCountRefused as e:
            refused = "budget" in str(e)
        rows3 = lane_ledger_rows(os.path.join(
            repo3, DocCountScope.LEDGER_FACE))
        vec("budget-cap-refusal",
            refused and _dc_read_title(repo3) == (5, 5)
            and rows3[-1]["outcome"] == "escalated(budget-cap)",
            "a cap hit refuses the repair and lands the escalation row")

        # false-green kill (R21): a face whose title shape is gone must
        # fail the verdict - alarm, never the old neutral skip that kept
        # --selftest green while the guard was blind on the surface.
        repo4 = os.path.join(tmp, "r4")
        os.makedirs(repo4)
        _dc_mk_repo(repo4, title=DC_MINI_README_BLIND)
        rows4 = doc_count_detect(repo4)
        buf4 = io.StringIO()
        with contextlib.redirect_stdout(buf4):
            rc4 = doc_count_cli(argparse.Namespace(
                repo=repo4, doc_count_detect=True, doc_count_apply=False,
                json_out=None))
        vec("missing-face-failure",
            len(rows4) == 1 and rows4[0]["status"] == "missing-face"
            and rc4 == 1 and _dc_failure(rows4)
            and "outcome=missing-face" in buf4.getvalue(),
            "a face whose title shape is gone reads status=missing-face"
            " and the detect verdict fails (rc=1, outcome=missing-face);"
            " the old drift-only verdict returned 0 - green while blind")

        # exclusion unit vectors over the shared providers
        doc_name, _src = ledger_doc(repo1)
        vec("excl-append-only-doc",
            DocCountScope.refusal_reason(doc_name, repo1) is not None, "")
        vec("excl-family-certify",
            DocCountScope.refusal_reason(
                "certify/frozen8.py", repo1) is not None, "")
        vec("excl-family-nested-fixtures",
            DocCountScope.refusal_reason(
                "tests/fixtures/gate4_dirty_sample.v", repo1) is not None,
            "the nested family entry matches by path prefix")
        vec("allow-tests-face-outside-fixtures",
            DocCountScope.refusal_reason(
                "tests/t_probe_engine.py", repo1) is None,
            "the nested family freezes only the fixtures subtree")
        vec("excl-frozen-runtime-row",
            DocCountScope.refusal_reason(
                "wash/wash_engine.py", repo1) is not None, "")
        vec("excl-archive-docszh",
            DocCountScope.refusal_reason(
                "docs/zh/a.md", repo1) is not None, "")
        vec("excl-archive-zhmd",
            DocCountScope.refusal_reason(
                "README-cw.zh.md", repo1) is not None,
            "the .zh.md translation archive mirror is refused")
        vec("allow-canonical-face",
            DocCountScope.refusal_reason("README-cw.md", repo1) is None,
            "")
        vec("allow-source-faces",
            all(DocCountScope.refusal_reason(r, repo1) is None
                for r in ("cw.sh", "tests/run_tests.sh",
                          "tools/repair_scope.py", "docs/mcp.md")),
            "the sources and ordinary doc faces stay out of the refusal"
            " set (one-way derivation, not a write ban)")

        # live repo vectors (the module lives in this repo; a detached
        # temp copy resolves no live repo and skips them honestly - the
        # sandbox vectors above carry the guard logic in every form)
        live_repo = _resolve_live_repo()
        if live_repo:
            ok, refusals = DocCountScope.check_writable(live_repo)
            vec("check-writable-consumption", ok,
                str(refusals) if refusals else
                "the class write faces pass the shared exclusion providers")
            _rows8, src8 = frozen8_ledger(live_repo)
            vec("shared-provider-consumption", src8 == "runtime-ledger8",
                "source=%s" % src8)
            live_rows = doc_count_detect(live_repo)
            vec("live-face-equals-source",
                live_rows and not _dc_failure(live_rows),
                "the live count faces equal the live registry/roster"
                " derivation and every listed face is located; a drift or a"
                " missing face here is a live red example (R21: a blind"
                " guard is a failure verdict, never green)")
        else:
            vec("live-face-skipped", True,
                "detached temp copy: no live repo resolvable (cwd and script"
                " parent carry no cw.sh); the sandbox vectors carry the guard"
                " logic; set ROCWASH_REPO_DIR to force the live face")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok2, detail in results:
        tag = "PASS" if ok2 else "FAIL"
        if not ok2:
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("doc-count summary: %d vectors, %d FAIL"
          % (len(results), failed))
    if failed:
        print("DOC-COUNT-SELFTEST RED (%d)" % failed)
        return 1
    print("DOC-COUNT-SELFTEST PASS")
    return 0


# --- selftest vectors (in-process, real repo + one temp fixture) ---

def run_selftest(args):
    results = []

    def vec(name, ok, detail):
        results.append((name, bool(ok), detail))

    # vector 1: runtime LEDGER8 read equals the pinned snapshot
    rows, source = frozen8_ledger(REPO_ROOT)
    ok = source == "runtime-ledger8" and rows == list(SNAPSHOT_LEDGER8)
    vec("runtime-ledger8-parity", ok,
        "8 runtime rows, source=%s, order matches the pinned snapshot" % source
        if ok else "source=%s rows=%s" % (source, rows))

    # vector 2: runtime checker rows equal the pinned snapshot
    checkers, csource = frozen8_checkers(REPO_ROOT)
    ok = csource == "runtime-checkers" and checkers == list(SNAPSHOT_CHECKERS)
    vec("runtime-checkers-parity", ok,
        "checker rows=%s source=%s" % (checkers, csource))

    # vector 3: roster shape (LEDGER8 rows + the append-only doc + the
    # governing faces + families)
    files, families = exclusion_roster(REPO_ROOT)
    doc, dsource = ledger_doc(REPO_ROOT)
    gov = governing_doc_faces(REPO_ROOT)
    ok = (len(files) == len(SNAPSHOT_LEDGER8) + 1 + len(gov) and doc in files
          and families == FROZEN_DIR_FAMILIES
          and dsource == "runtime-ledger-doc")
    vec("roster-shape", ok,
        "files=%d (ledger8 %d + doc 1 + governing %d) doc=%r families=%d "
        "source=%s"
        % (len(files), len(SNAPSHOT_LEDGER8), len(gov), doc, len(families),
           dsource))

    # vector 4: the append-only face and every family dir exist on disk
    ok = os.path.isfile(os.path.join(REPO_ROOT, doc))
    missing = [d for d in FROZEN_DIR_FAMILIES
               if not os.path.isdir(os.path.join(REPO_ROOT, d))]
    ok = ok and not missing
    vec("faces-and-families-exist", ok,
        "append-only doc on disk; all 9 family dirs present"
        if ok else "doc on disk=%s; missing families: %s" % (ok, missing))

    # vector 5: the full view carries the ten-row roster plus the doc
    full = full_frozen_files(REPO_ROOT)
    ok = len(full) == 11 and "certify/frozen8.py" in full and doc in full
    vec("ten-row-view", ok,
        "full roster carries %d faces" % len(full))

    # vector 6: fixture fallback on a temp root without the frozen file
    tmp = tempfile.mkdtemp(prefix="rqw_repair_scope_")
    try:
        rows2, source2 = frozen8_ledger(tmp)
        doc2, dsource2 = ledger_doc(tmp)
        ok = (source2 == "snapshot-fallback"
              and rows2 == list(SNAPSHOT_LEDGER8)
              and dsource2 == "snapshot-fallback"
              and doc2 == FALLBACK_LEDGER_DOC)
        vec("fixture-fallback", ok,
            "temp root falls back to the pinned snapshot, no crash"
            if ok else "source2=%s doc2=%r" % (source2, doc2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # vector 7: two roster reads return equal results (idempotent read)
    ok = exclusion_roster(REPO_ROOT) == (files, families)
    vec("roster-read-idempotent", ok, "two identical shared-roster reads")

    # vector 8: the governing documents ride the shared roster; a
    # constitution-tier face is never a repair target and a plain docs
    # face stays writable
    ok = bool(gov) and all(g in files for g in gov) \
        and all(g.startswith(GOVERNING_DOC_PREFIXES) for g in gov) \
        and "docs/roadmap-v43-plus-20261111.md" not in files
    vec("governing-docs-on-roster", ok,
        "%d governing faces rostered by prefix; non-governing doc faces "
        "stay writable" % len(gov))

    failed = 0
    for name, ok2, detail in results:
        if ok2:
            tag = "PASS"
        else:
            tag = "FAIL"
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("summary: %d vectors, %d FAIL" % (len(results), failed))
    return 1 if failed else 0


def lane_guard_cli(args):
    """Class-1 operator face (--lane-detect / --lane-apply).  Returns the
    process code: 0 verdict obtained, 2 refused, 9 missing input."""
    try:
        if not os.path.isdir(args.repo):
            sys.stderr.write("repair_scope: FAIL-LOUD --repo directory"
                             " missing: %s\n" % args.repo)
            return 9
        names, ghosts = lane_detect(args.repo, args.suite)
        try:
            outcome, applied = lane_apply(args.repo, args.ledger, ghosts,
                                          args.lane_apply, args.suite)
        except LaneRefused as e:
            print("REFUSED: %s" % e)
            return 2
        report = {"schema": LaneExtractScope.REPORT_SCHEMA,
                  "face": LaneExtractScope.CLASS_ID,
                  "suite": lane_norm_rel(args.suite), "lanes": len(names),
                  "ghosts": ghosts, "outcome": outcome,
                  "applied": applied, "ledger": args.ledger,
                  "budget_per_branch": LaneExtractScope.BUDGET_PER_BRANCH}
        if args.json_out:
            parent = os.path.dirname(os.path.abspath(args.json_out))
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            with io.open(args.json_out, "w", encoding="utf-8",
                         newline="\n") as fh:
                fh.write(_json.dumps(report, ensure_ascii=False,
                                     sort_keys=True, indent=1) + "\n")
        for g in ghosts:
            print("ghost %s reason=%s refs=%s action=%s"
                  % (g["lane"], g["reason"], ",".join(g["refs"]) or "-",
                     g["action"]))
        if not ghosts:
            print("clean: %d lanes, no ghost" % len(names))
        print("outcome=%s applied=%s" % (outcome, str(applied).lower()))
        return 0
    except LaneMissingInput as e:
        print("MISSING-INPUT: %s" % e)
        return 9
    except LaneRefused as e:
        print("REFUSED: %s" % e)
        return 2


LANE_SUITE_FIXTURE = (
    '#!/bin/bash\n'
    '# fixture suite (tmp only)\n'
    'CASES="\\\n'
    't_real_one \\\n'
    't_ghost_lane \\\n'
    't_mixed_legs \\\n'
    't_real_two"\n'
    'NCASES=$(echo $CASES | wc -w | tr -d \' \')\n'
    '\n'
    't_real_one() {\n'
    '  "$PY" -B "$REPO/tests/t_real_one.py"\n'
    '}\n'
    '\n'
    't_ghost_lane() {\n'
    '  "$PY" -B "$REPO/tests/t_ghost_lane.py"\n'
    '}\n'
    '\n'
    't_mixed_legs() {\n'
    '  "$PY" -B "$REPO/tests/t_mixed_legs.py"\n'
    '  "$PY" -B "$REPO/tests/t_mixed_legs_extra.py"\n'
    '}\n'
    '\n'
    't_real_two() {\n'
    '  "$PY" -B "$REPO/tests/t_real_two.py"\n'
    '}\n')

LANE_SUITE_NO_FUNC = LANE_SUITE_FIXTURE.replace(
    't_mixed_legs \\\n', 't_no_func \\\n').replace(
    't_mixed_legs() {\n'
    '  "$PY" -B "$REPO/tests/t_mixed_legs.py"\n'
    '  "$PY" -B "$REPO/tests/t_mixed_legs_extra.py"\n'
    '}\n', '')

LANE_SUITE_TAIL = (
    '#!/bin/bash\n'
    '# fixture suite: ghost lane as the roster tail entry (tmp only)\n'
    'CASES="\\\n'
    't_real_one \\\n'
    't_ghost_lane"\n'
    'NCASES=$(echo $CASES | wc -w | tr -d \' \')\n'
    '\n'
    't_real_one() {\n'
    '  "$PY" -B "$REPO/tests/t_real_one.py"\n'
    '}\n'
    '\n'
    't_ghost_lane() {\n'
    '  "$PY" -B "$REPO/tests/t_ghost_lane.py"\n'
    '}\n')


def _lane_mk_repo(root, suite_text, ledger_rows=(), suite_rel=None,
                  stub_ledger8=False):
    suite_rel = suite_rel or LaneExtractScope.DEFAULT_SUITE
    suite_path = os.path.join(root, suite_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(suite_path), exist_ok=True)
    with io.open(suite_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(suite_text)
    if stub_ledger8:
        fpath = os.path.join(root, "certify", "frozen8.py")
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with io.open(fpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('#!/usr/bin/env python3\nLEDGER8 = (\n'
                     '    ("%s", "%032d"),\n)\n'
                     % (lane_norm_rel(suite_rel), 7))
    for rel in ("tests/t_real_one.py", "tests/t_real_two.py",
                "tests/t_mixed_legs.py"):
        p = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# fixture lane file\n")
    if ledger_rows:
        lpath = os.path.join(root, LaneExtractScope.LEDGER_FACE)
        os.makedirs(os.path.dirname(lpath), exist_ok=True)
        with io.open(lpath, "w", encoding="utf-8", newline="\n") as fh:
            for r in ledger_rows:
                fh.write(_json.dumps(r, sort_keys=True) + "\n")
    return suite_path


def lane_selftest():
    """Class-1 fixture vectors (tmp fixtures only; zero network, zero
    compile, zero writes outside mkdtemp)."""
    results = []

    def vec(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    tmp = tempfile.mkdtemp(prefix="rqw_lane_unreg_")
    try:
        # vector 1: ghost detect, dry run, zero write, deterministic report
        repo1 = os.path.join(tmp, "r1")
        os.makedirs(repo1)
        sp = _lane_mk_repo(repo1, LANE_SUITE_FIXTURE)
        md5_before = _lane_md5(sp)
        j1 = os.path.join(tmp, "rep1a.json")
        j2 = os.path.join(tmp, "rep1b.json")
        rc1 = lane_guard_cli(_lane_args(repo1, json_out=j1))
        rc1b = lane_guard_cli(_lane_args(repo1, json_out=j2))
        rep = _json.load(io.open(j1, encoding="utf-8"))
        vec("ghost-detect-dry-run", rc1 == 0 and rc1b == 0,
            "rc=%s/%s" % (rc1, rc1b))
        vec("ghost-is-missing-file",
            [g["lane"] for g in rep["ghosts"]] == ["t_ghost_lane"],
            str(rep["ghosts"]))
        vec("mixed-refs-not-ghost",
            "t_mixed_legs" not in [g["lane"] for g in rep["ghosts"]],
            "an env/platform leg belongs to the skip protocol, not a "
            "repair")
        vec("dry-run-zero-write", _lane_md5(sp) == md5_before,
            "suite bytes changed under dry run")
        vec("report-determinism",
            io.open(j1, "rb").read() == io.open(j2, "rb").read(),
            "double dry-run reports differ")
        vec("dry-run-no-ledger",
            not os.path.isfile(os.path.join(
                repo1, LaneExtractScope.LEDGER_FACE)),
            "dry run created the ledger")

        # vector 2: apply drops exactly the line, keeps the function,
        # rolls the roster count back, one repaired ledger row
        rc2 = lane_guard_cli(_lane_args(repo1, apply=True))
        text2 = io.open(sp, encoding="utf-8", newline="").read()
        names2 = lane_roster_names(text2)
        vec("apply-rc", rc2 == 0, "rc=%s" % rc2)
        vec("count-rollback",
            names2 == ["t_real_one", "t_mixed_legs", "t_real_two"],
            str(names2))
        vec("function-body-kept",
            lane_function_body(text2, "t_ghost_lane") is not None,
            "2748b52 keeps the function body")
        vec("last-entry-quote-repaired", 't_real_two"' in text2,
            "continuation close quote not rebuilt")
        rows = lane_ledger_rows(os.path.join(
            repo1, LaneExtractScope.LEDGER_FACE))
        vec("ledger-repaired-row",
            len(rows) == 1 and rows[0]["class"] == LaneExtractScope.CLASS_ID
            and rows[0]["target"] == lane_norm_rel(
                LaneExtractScope.DEFAULT_SUITE)
            and rows[0]["outcome"] == LaneExtractScope.OUTCOME_REPAIRED
            and rows[0]["lanes"] == ["t_ghost_lane"]
            and "utc" in rows[0], str(rows))

        # vector 3: rerun is clean and appends nothing
        md5_after = _lane_md5(sp)
        rc3 = lane_guard_cli(_lane_args(repo1, apply=True))
        vec("rerun-clean", rc3 == 0 and _lane_md5(sp) == md5_after
            and len(lane_ledger_rows(os.path.join(
                repo1, LaneExtractScope.LEDGER_FACE))) == 1,
            "rc=%s" % rc3)

        # vector 3b: tail-entry drop rebuilds the closing quote on the
        # previous surviving roster line (the regex terminator carries
        # the quote, never the tail line itself)
        repo3b = os.path.join(tmp, "r3b")
        os.makedirs(repo3b)
        sp3b = _lane_mk_repo(repo3b, LANE_SUITE_TAIL)
        rc3b = lane_guard_cli(_lane_args(repo3b, apply=True))
        text3b = io.open(sp3b, encoding="utf-8", newline="").read()
        names3b = lane_roster_names(text3b)
        vec("tail-entry-drop",
            rc3b == 0 and names3b == ["t_real_one"]
            and 't_real_one"' in text3b
            and lane_function_body(text3b, "t_ghost_lane") is not None,
            "rc=%s names=%s quote=%s"
            % (rc3b, names3b, 't_real_one"' in text3b))

        # vector 4: budget cap (two prior repairs) -> refuse + escalate
        repo4 = os.path.join(tmp, "r4")
        os.makedirs(repo4)
        sp4 = _lane_mk_repo(repo4, LANE_SUITE_FIXTURE, ledger_rows=(
            {"class": LaneExtractScope.CLASS_ID,
             "target": lane_norm_rel(LaneExtractScope.DEFAULT_SUITE),
             "outcome": LaneExtractScope.OUTCOME_REPAIRED},
            {"class": LaneExtractScope.CLASS_ID,
             "target": lane_norm_rel(LaneExtractScope.DEFAULT_SUITE),
             "outcome": LaneExtractScope.OUTCOME_REPAIRED}))
        md5_4 = _lane_md5(sp4)
        rc4 = lane_guard_cli(_lane_args(repo4, apply=True))
        rows4 = lane_ledger_rows(os.path.join(
            repo4, LaneExtractScope.LEDGER_FACE))
        vec("budget-cap-refusal",
            rc4 == 2 and _lane_md5(sp4) == md5_4
            and rows4[-1]["outcome"] == "escalated(budget-cap)",
            "rc=%s last=%s" % (rc4, rows4[-1]["outcome"]))

        # vector 5: excluded face (directory family) refuses under apply
        repo5 = os.path.join(tmp, "r5")
        os.makedirs(repo5)
        _lane_mk_repo(repo5, LANE_SUITE_FIXTURE,
                      suite_rel="CLA/run_tests.sh")
        rc5 = lane_guard_cli(_lane_args(repo5, apply=True,
                                        suite="CLA/run_tests.sh"))
        vec("excluded-family-refusal", rc5 == 2, "rc=%s" % rc5)

        # vector 6: excluded face (frozen row via a stub LEDGER8)
        repo6 = os.path.join(tmp, "r6")
        os.makedirs(repo6)
        _lane_mk_repo(repo6, LANE_SUITE_FIXTURE, stub_ledger8=True)
        rc6 = lane_guard_cli(_lane_args(repo6, apply=True))
        vec("excluded-frozen-refusal", rc6 == 2, "rc=%s" % rc6)

        # vector 7: clean repo, nothing written anywhere
        repo7 = os.path.join(tmp, "r7")
        os.makedirs(repo7)
        suite7 = LANE_SUITE_FIXTURE.replace("t_ghost_lane \\\n", "") \
            .replace(
                't_mixed_legs \\\n', '').replace(
                't_mixed_legs() {\n'
                '  "$PY" -B "$REPO/tests/t_mixed_legs.py"\n'
                '  "$PY" -B "$REPO/tests/t_mixed_legs_extra.py"\n'
                '}\n', '')
        sp7 = _lane_mk_repo(repo7, suite7)
        md5_7 = _lane_md5(sp7)
        rc7 = lane_guard_cli(_lane_args(repo7))
        vec("clean-repo-noop",
            rc7 == 0 and _lane_md5(sp7) == md5_7, "rc=%s" % rc7)

        # vector 8: rostered name without a function body is a ghost
        repo8 = os.path.join(tmp, "r8")
        os.makedirs(repo8)
        sp8 = _lane_mk_repo(repo8, LANE_SUITE_NO_FUNC)
        rc8 = lane_guard_cli(_lane_args(repo8, apply=True))
        text8 = io.open(sp8, encoding="utf-8", newline="").read()
        vec("missing-function-ghost",
            rc8 == 0 and "t_no_func" not in lane_roster_names(text8),
            "rc=%s names=%s" % (rc8, lane_roster_names(text8)))

        # vector 9: exclusion unit vectors over the shared providers
        vec("excl-append-only-doc",
            LaneExtractScope.refusal_reason("更新账.md") is not None, "")
        vec("excl-family-certify",
            LaneExtractScope.refusal_reason(
                "certify/freeze_manifest.py") is not None, "")
        vec("excl-family-docszh",
            LaneExtractScope.refusal_reason("docs/zh/a.md") is not None,
            "")
        vec("excl-frozen-runtime-row",
            LaneExtractScope.refusal_reason(
                "wash/wash_engine.py") is not None, "")
        vec("allow-tools-face",
            LaneExtractScope.refusal_reason("tools/x.py") is None, "")
        vec("allow-suite-face",
            LaneExtractScope.refusal_reason(
                "tests/run_tests.sh") is None, "")

        # vector 10: the ledger write face passes the same gate
        repo10 = os.path.join(tmp, "r10")
        os.makedirs(repo10)
        _lane_mk_repo(repo10, LANE_SUITE_FIXTURE)
        rc10 = lane_guard_cli(_lane_args(repo10, apply=True,
                                         ledger="seeds/ledger.jsonl"))
        vec("ledger-face-gated",
            rc10 == 2 and not os.path.isfile(os.path.join(
                repo10, "seeds", "ledger.jsonl")), "rc=%s" % rc10)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for name, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print("%s %s - %s" % (tag, name, detail))
    print("lane summary: %d vectors, %d FAIL" % (len(results), failed))
    if failed:
        print("LANE-EXTRACT-SELFTEST RED (%d)" % failed)
        return 1
    print("LANE-EXTRACT-SELFTEST PASS")
    return 0


def _lane_args(repo, apply=False, suite=None, ledger=None, json_out=None):
    """Namespace stand-in mirroring the argparse lane-face flags for the
    in-process vectors."""
    return argparse.Namespace(
        repo=repo, lane_detect=True, lane_apply=apply,
        suite=suite or LaneExtractScope.DEFAULT_SUITE,
        ledger=ledger or LaneExtractScope.LEDGER_FACE, json_out=json_out)


def main(argv=None):
    """CLI: --selftest (the v1 face, also the bare-invocation default) or
    the class-2 --check query face (--a2-table adds the F1 single-source
    A2 mapping table to the exclusion set for that one query), or the
    class-1 lane face (--lane-detect / --lane-apply)."""
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    if not argv:
        argv = ["--selftest"]
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="shared exclusion roster for the repair apply faces:"
                    " the frozen ledger rows (runtime LEDGER8/CHECKERS AST"
                    " read) + the append-only ledger document + the frozen"
                    " directory families; repair seats import the providers,"
                    " the CLI answers is-excluded queries")
    ap.add_argument("--selftest", action="store_true",
                    help="run the in-process selftest vectors")
    ap.add_argument("--repo", default=REPO_ROOT, metavar="DIR",
                    help="the repo root the relative faces resolve against")
    ap.add_argument("--check", nargs="+", metavar="REL", default=None,
                    help="one or more repo-relative faces to classify"
                        " (EXCLUDED or REPAIRABLE; a verdict is data)")
    ap.add_argument("--a2-table", dest="a2_table", default=None, metavar="P",
                    help="path of the A2 mapping-source table face; adds it"
                        " to the exclusion set for this --check query (the"
                        " F1 single-source form)")
    ap.add_argument("--classes", action="store_true",
                    help="print the registered repair-class budget registry"
                        " (class id, ticket, writable faces, budget)")
    ap.add_argument("--lane-detect", dest="lane_detect", action="store_true",
                    help="class-1 lane face: detect ghost lanes in the "
                         "CASES roster (dry run, zero write)")
    ap.add_argument("--lane-apply", dest="lane_apply", action="store_true",
                    help="class-1 lane face: land the drop of every "
                         "detected ghost lane's roster line")
    ap.add_argument("--suite", default=LaneExtractScope.DEFAULT_SUITE,
                    help="lane face: suite entry holding the CASES roster,"
                         " relative to --repo")
    ap.add_argument("--ledger", default=LaneExtractScope.LEDGER_FACE,
                    help="repair ledger path (lane and doc-count faces)")
    ap.add_argument("--json-out", dest="json_out", default=None,
                    metavar="P",
                    help="lane and doc-count face: write the report JSON to this path")
    ap.add_argument("--doc-count-detect", dest="doc_count_detect",
                    action="store_true",
                    help="class-4 doc-count face: report-first drift "
                         "scan over the registry/roster-derived count "
                         "faces (zero write)")
    ap.add_argument("--doc-count-apply", dest="doc_count_apply",
                    action="store_true",
                    help="class-4 doc-count face: land the minimal "
                         "count-token repairs under the exclusion and "
                         "budget gates")
    args = ap.parse_args(argv)
    if args.selftest:
        rc = run_selftest(argv)
        rc_lane = lane_selftest()
        rc_doc = run_doc_count_selftest()
        return 1 if (rc or rc_lane or rc_doc) else 0
    if args.lane_detect or args.lane_apply:
        if args.check is not None:
            ap.error("--check and the lane face are mutually exclusive")
        return lane_guard_cli(args)
    if args.doc_count_detect or args.doc_count_apply:
        if args.check is not None:
            ap.error("--check and the doc-count face are mutually exclusive")
        return doc_count_cli(args)
    if args.classes:
        if args.check is not None:
            ap.error("--check and --classes are mutually exclusive")
        return classes_face()
    if args.check is None:
        ap.error("--check needs at least one repo-relative face")
    if not os.path.isdir(args.repo):
        sys.stderr.write("repair_scope: FAIL-LOUD --repo directory missing:"
                         " %s\n" % args.repo)
        return 9
    return check_faces(args.repo, args.check, args.a2_table)


if __name__ == "__main__":
    sys.exit(main())
