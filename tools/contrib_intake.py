#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contrib_intake: contribution intake inspector issuing read-only four-gate verdicts.

Purpose.  Reconciles a contribution face (local clone or archive tree at a
  ref) against a base face, running four gates without short-circuit:
  `registry` replays the `registry_union` three-face union dry run (base
  face for merge-base and main, contrib face the branch), blocks on any
  assertion blast and attaches a regeneration prescription; `norm` lints
  each new or changed prose face (.py/.sh/.md) through `norm_lint.py`,
  blocking on error-level findings, recording warn-level ones;
  `gate_expectation` scans changed .v faces with `gate4_comment_guard.py`
  and prechecks gate7 probe availability (a real probe runs only when
  --rocq-cmd is given); `isolation` tallies changed paths outside the
  lane (default contrib/) as warning-level evidence.

Interface.  --contrib-repo PATH --contrib-ref REF --base-repo PATH
  [--base-ref REF] [--paths P1,P2] [--order-path PATH] [--project-path
  PATH] [--lane-prefix PREFIX] [--jargon-map PATH] [--rocq-cmd CMD]
  [--json P] | --selftest.  Schema `rocqwash-contrib-intake/1`: gates
  holds four {name, verdict, evidence[], details} objects.

Dependencies.  Python 3 stdlib only; sibling instruments `registry_union.py`
  (subprocess plus engine import), `norm_lint.py`, `verify/gate4_comment_guard.py`;
  `git` on PATH for git faces; jargon map: base docs table, then this copy.

Evidence.  --selftest builds dual git clones covering four judgments
  (clean contribution, registry collision, norm jargon hit, core-lane
  overlap) plus read-only, determinism, archive-parity and CLI checks.

Exit-codes.  0 accounted (BLOCK verdict is data); 1 instrument failure; 2 usage; 9 missing input.
"""
# Extended contract (help face; kept below the five-field block so the
# header stays within the 30-line budget of the annotation standard):
# Read-only discipline: both repository faces are never written; the write
#   surface is temp materialization plus the explicit --json target only.
# Report summary carries verdict (PASS|BLOCK), block_gates, warn_total;
#   each gate object carries name, verdict, evidence[], details.
# --contrib-repo PATH  contribution face: a git clone (any ref git resolves)
#                      or a plain archive tree; an archive tree uses its
#                      working tree as the face and records the ref as given.
# --contrib-ref REF    contribution ref (nominal for an archive face).
# --base-repo PATH / --base-ref REF   receiving face; ref defaults to main.
# --paths P1,P2        restrict the adjudication surface to these prefixes
#                      (repeatable, comma-split; exact path or prefix/ match).
# --order-path PATH    registry order book path (default order.txt).
# --project-path PATH  registry coqproject book path (default _CoqProject).
# --lane-prefix PREFIX contribution lane prefixes, comma-split (default
#                      contrib/); changed paths outside every prefix are the
#                      core overlap, warning-level evidence only.
# --jargon-map PATH    mapping table for the norm gate; default resolves the
#                      base repository's docs table first, then this
#                      repository's copy; missing exits 9.
# --rocq-cmd CMD       gate7 real probe command; when given, the probe runs
#                      `<CMD> --version` and a failure blocks the gate;
#                      when absent, the precheck records availability facts
#                      only and never executes anything.
# --json P             report target, schema rocqwash-contrib-intake/1.
# --selftest           dual-clone fixture vectors; runs standalone.
# Determinism: no wall-clock fields, sorted surfaces, repo-relative paths
# only; identical inputs rerun byte-identical.

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

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TOOLS_DIR)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  (key/anchor/union engine reuse)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: sibling tools/registry_union.py not importable "
          "(engine-reuse dependency): %s" % _e, file=sys.stderr)
    sys.exit(9)

PROG = "contrib_intake"
SCHEMA = "rocqwash-contrib-intake/1"
TOOL = "contrib_intake"

UNION_PY = os.path.join(_TOOLS_DIR, "registry_union.py")
NORM_PY = os.path.join(_TOOLS_DIR, "norm_lint.py")
GATE4_PY = os.path.join(_REPO_ROOT, "verify", "gate4_comment_guard.py")

KIND_ORDER = _ru.KIND_ORDER            # "order"
KIND_COQPROJECT = _ru.KIND_COQPROJECT  # "coqproject"

FACES = (".py", ".sh", ".md")          # prose faces the norm gate lints
WARN_KINDS = ("cjk", "forbidden", "budget")  # norm_lint warn-level kinds
DEFAULT_BASE_REF = "main"
DEFAULT_ORDER_PATH = "order.txt"
DEFAULT_PROJECT_PATH = "_CoqProject"
DEFAULT_LANE_PREFIX = "contrib/"
DEFAULT_JARGON_MAP_REL = ("docs", "jargon-to-standard-mapping-v1.md")
# gate7 probe availability faces; env knobs mirror wrapper/gate7_probe.sh
GATE7_SCRIPT_DEFAULT = ("/Users/apple/Desktop/ConstructiveWorld-Set/scripts/"
                        "gates/gate7_extract_run.py")
GATE7_ENV_DEFAULT = ("/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/"
                     "env.sh")

EVIDENCE_CAP = 8   # per-evidence item display cap (deterministic)
PATHS_CAP = 20     # per-evidence path-list display cap (deterministic)


class MissingInput(Exception):
    """Missing input (exit 9)."""


class InstrumentError(Exception):
    """Instrument failure (exit 1): no verdict can be issued."""


def shq(s):
    """Shell-quote a value for prescription command lines (deterministic)."""
    if s and re.fullmatch(r"[A-Za-z0-9_./@+=,:^-]+", s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def clip(s, cap=200):
    """Deterministic truncation for embedded instrument text."""
    s = s.strip()
    return s if len(s) <= cap else s[:cap] + "…"


def _run(argv):
    """Run a subprocess, capturing bytes (no shell; fail-loud on spawn)."""
    try:
        return subprocess.run(argv, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    except OSError as e:
        raise InstrumentError("subprocess spawn failed: %s (%s)"
                              % (" ".join(argv), e))


def _load_json(path, what):
    """Load a JSON file; unparseable output is an instrument failure."""
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        raise InstrumentError("%s output unreadable at %s: %s"
                              % (what, path, e))


def _wb(path, data):
    """Write bytes to a temp materialization path."""
    with io.open(path, "wb") as fh:
        fh.write(data)


def _first_line(raw_bytes):
    """First non-empty line of a byte stream, deterministically clipped."""
    for ln in raw_bytes.decode("utf-8", errors="replace").splitlines():
        s = ln.strip()
        if s:
            return clip(s, 120)
    return ""


# ---------- faces (git ref face or archive tree face) ----------

def _blob_sha(data, algo):
    """Git-blob-compatible content hash (header "blob <size>\\0" + data)."""
    h = hashlib.new(algo)
    h.update(b"blob %d\x00" % len(data))
    h.update(data)
    return h.hexdigest()


def detect_face_mode(path, label):
    """Directory -> "git" | "archive".  A declared git face without a usable
    git binary is a missing input (fail-loud, no silent downgrade)."""
    if not os.path.isdir(path):
        raise MissingInput("%s face path is not a directory: %s"
                           % (label, path))
    dotgit = os.path.exists(os.path.join(path, ".git"))
    git_bin = shutil.which("git")
    if git_bin is None:
        if dotgit:
            raise MissingInput("git binary unavailable but %s face %s "
                               "declares a repository" % (label, path))
        return "archive"
    p = _run(["git", "-C", path, "rev-parse", "--git-dir"])
    if p.returncode == 0:
        return "git"
    if dotgit:
        raise MissingInput("git rev-parse failed on %s face %s: %s"
                           % (label, path, clip(p.stderr.decode(
                               "utf-8", errors="replace"))))
    return "archive"


class RepoFace(object):
    """One comparison side: a git ref face or an archive tree face.

    git face: listing comes from `git ls-tree -r -l -z <ref>`; blob content
    is fetched by sha (`git cat-file blob <sha>`), so path-encoding drift
    cannot corrupt content reads.  archive face: os.walk listing with dot
    segments skipped; git-blob-compatible sha1 and sha256 are computed so
    listings stay comparable with either git object format.
    """

    def __init__(self, path, ref, label):
        self.path = os.path.abspath(path)
        self.ref = ref
        self.label = label
        self.mode = detect_face_mode(self.path, label)
        self.engine = None
        self.files = {}
        if self.mode == "git":
            p = _run(["git", "-C", self.path, "rev-parse", "--verify", ref])
            if p.returncode != 0:
                raise MissingInput("%s face ref unresolvable: %s in %s"
                                   % (label, ref, self.path))
            p2 = _run(["git", "-C", self.path, "rev-parse",
                       "--show-object-format"])
            self.engine = (p2.stdout.decode("utf-8", errors="replace").strip()
                           if p2.returncode == 0 else "sha1")
            self._list_git()
        else:
            self._list_archive()

    def _list_git(self):
        p = _run(["git", "-C", self.path, "ls-tree", "-r", "-l", "-z",
                  self.ref])
        if p.returncode != 0:
            raise MissingInput("ls-tree failed on %s face %s@%s: %s"
                               % (self.label, self.path, self.ref,
                                  clip(p.stderr.decode(
                                      "utf-8", errors="replace"))))
        for chunk in p.stdout.split(b"\0"):
            if not chunk:
                continue
            meta, _sep, path_b = chunk.partition(b"\t")
            # -l pads the size column, so split on whitespace runs
            toks = meta.split()
            if len(toks) != 4 or toks[1] != b"blob":
                continue
            rel = path_b.decode("utf-8", errors="replace")
            size = int(toks[3]) if toks[3].isdigit() else None
            self.files[rel] = {"size": size, "sha": toks[2].decode("ascii")}

    def _list_archive(self):
        for dirpath, dirnames, filenames in os.walk(self.path):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for fn in sorted(filenames):
                ap = os.path.join(dirpath, fn)
                rel = os.path.relpath(ap, self.path).replace(os.sep, "/")
                with io.open(ap, "rb") as fh:
                    data = fh.read()
                self.files[rel] = {"size": len(data),
                                   "sha1": _blob_sha(data, "sha1"),
                                   "sha256": _blob_sha(data, "sha256")}

    def has(self, rel):
        return rel in self.files

    def read_blob(self, rel):
        """Blob bytes at a listed path (git side fetches by sha)."""
        ent = self.files[rel]
        if self.mode == "git":
            p = _run(["git", "-C", self.path, "cat-file", "blob",
                      ent["sha"]])
            if p.returncode != 0:
                raise MissingInput("cat-file failed on %s face %s (%s): %s"
                                   % (self.label, rel, ent["sha"],
                                      clip(p.stderr.decode(
                                          "utf-8", errors="replace"))))
            return p.stdout
        ap = os.path.join(self.path, *rel.split("/"))
        with io.open(ap, "rb") as fh:
            return fh.read()

    def _native_sha(self, rel):
        ent = self.files[rel]
        if self.mode == "git":
            return ent["sha"]
        return ent[self.engine or "sha1"]


def _faces_differ(bf, cf, rel):
    """Content comparison across faces.  Same-engine faces compare hash
    values (git native sha, or the archive face's matching blob hash);
    only mismatched git object formats fall back to a size-guarded byte
    comparison."""
    if bf.mode == "git" and cf.mode == "git":
        eng = bf.engine if bf.engine == cf.engine else None
    else:
        eng = bf.engine if bf.mode == "git" else cf.engine
        if eng is None:  # archive vs archive: both faces carry both engines
            eng = "sha1"
    if eng is not None:
        return bf._native_sha(rel) != cf._native_sha(rel)
    be, ce = bf.files[rel], cf.files[rel]
    if be["size"] != ce["size"]:
        return True
    return bf.read_blob(rel) != cf.read_blob(rel)


# ---------- surface and filter ----------

def parse_prefixes(items):
    """Comma-joined, repeatable prefix list -> cleaned prefixes."""
    out = []
    for chunk in items or []:
        for part in chunk.split(","):
            part = part.strip().strip("/").replace(os.sep, "/")
            if part:
                out.append(part)
    return out


def in_filter(rel, prefixes):
    """Prefix membership: exact path or anything under prefix/."""
    if not prefixes:
        return True
    return any(rel == p or rel.startswith(p + "/") for p in prefixes)


def compute_changed(bf, cf, prefixes):
    """Contrib-side surface: added / modified / deleted, filter-applied."""
    added = sorted(p for p in cf.files
                   if p not in bf.files and in_filter(p, prefixes))
    deleted = sorted(p for p in bf.files
                     if p not in cf.files and in_filter(p, prefixes))
    modified = []
    for p in sorted(set(bf.files) & set(cf.files)):
        if not in_filter(p, prefixes):
            continue
        if _faces_differ(bf, cf, p):
            modified.append(p)
    return {"added": added, "modified": modified, "deleted": deleted}


def materialize(face, rel, tmpdir, tag):
    """Face blob -> temp file (flattened name keeps one file per rel path)."""
    data = face.read_blob(rel)
    flat = "%s__%s" % (tag, rel.replace("/", "_"))
    path = os.path.join(tmpdir, flat)
    _wb(path, data)
    return path


# ---------- gate 1: registry ----------

def build_prescription(args, blocked_kinds):
    """Regeneration prescription (isolation protocol §4 mechanical face):
    registry_union regenerates each collided book on the base lineage, then
    the registry_audit --fix-plan plus registry_fix chain applies the
    residual hygiene.  Caller-chosen outputs stay angle-bracketed."""
    cmds = []
    for kind, book in blocked_kinds:
        tag = kind.upper()
        cmds.append("git -C %s show %s > <CONTRIB_BOOK_%s>"
                    % (shq(args.contrib_repo),
                       shq("%s:%s" % (args.contrib_ref, book)), tag))
        cmds.append("git -C %s show %s > <BASE_BOOK_%s>"
                    % (shq(args.base_repo),
                       shq("%s:%s" % (args.base_ref, book)), tag))
        cmds.append("python3 tools/registry_union.py --base <BASE_BOOK_%s> "
                    "--main <BASE_BOOK_%s> --branch <CONTRIB_BOOK_%s> "
                    "--kind %s --out <REGEN_BOOK_%s> --apply"
                    % (tag, tag, tag, kind, tag))
    if cmds:
        cmds.append("python3 tools/registry_audit.py "
                    "--order <REGEN_BOOK_ORDER> "
                    "--project <REGEN_BOOK_COQPROJECT> --anchor-src "
                    "<LIVE_TREE> --fix-plan --json <AUDIT_JSON>")
        cmds.append("python3 tools/registry_fix.py "
                    "--audit-json <AUDIT_JSON> "
                    "--order <REGEN_BOOK_ORDER> "
                    "--project <REGEN_BOOK_COQPROJECT> "
                    "--anchor-src <LIVE_TREE> --apply "
                    "--work-dir <WORK_DIR> --json <FIX_REPORT_JSON>")
    return cmds


def _replay_union_blast(tb, tc, kind):
    """Replay the union engine in-process on a blasted simulation to derive
    structured evidence (same engine module, zero re-creation)."""
    base_lines, _e, _f = _ru.read_side(tb, "base")
    contrib_lines, _e, _f = _ru.read_side(tc, "contrib")
    blasted = None
    try:
        _ru.build_union(base_lines, base_lines, contrib_lines, kind)
    except _ru.AssertBlast as e:
        blasted = e
    if blasted is None:
        raise InstrumentError("registry_union blasted but the engine replay "
                              "passes on kind=%s — instrument drift" % kind)
    added, _nk = _ru.extract_unique(base_lines, contrib_lines, kind)
    main_keys = set()
    for ln in base_lines:
        k = _ru.key_of(ln, kind)
        if k is not None:
            main_keys.add(k)
    added_keys = []
    for ln in added:
        k = _ru.key_of(ln, kind)
        if k is not None and k not in added_keys:
            added_keys.append(k)
    colliding_keys = [k for k in added_keys if k in main_keys]
    main_pairs = _ru.dup_pairs(
        [t for t in (_ru.anchor_of(l) for l in base_lines) if t])
    out_pairs = _ru.dup_pairs(
        [t for t in (_ru.anchor_of(l) for l in base_lines + added) if t])
    new_anchor_dups = sorted(t for t in out_pairs
                             if out_pairs[t] > main_pairs.get(t, 0))
    return (blasted.code, list(blasted.items), added_keys, colliding_keys,
            new_anchor_dups)


def gate_registry(args, base_face, contrib_face, prefixes, tmpdir):
    """Gate registry: per book kind, the three-face union dry run (base face
    for --base and --main, contrib face for --branch).  Zero conflict =
    PASS; an assertion blast = BLOCK with the regeneration prescription."""
    evidence = []
    kinds_detail = {}
    blocked_kinds = []
    for kind, book in ((KIND_ORDER, args.order_path),
                       (KIND_COQPROJECT, args.project_path)):
        det = {"book_path": book}
        if prefixes and not in_filter(book, prefixes):
            det["status"] = "out-of-scope"
            evidence.append("registry: kind=%s face %s sits outside the "
                            "--paths filter — not reconciled in this run"
                            % (kind, book))
            kinds_detail[kind] = det
            continue
        if not contrib_face.has(book):
            det["status"] = "absent-in-contrib"
            evidence.append("registry: kind=%s contrib face carries no %s — "
                            "nothing to reconcile" % (kind, book))
            kinds_detail[kind] = det
            continue
        contrib_bytes = contrib_face.read_blob(book)
        base_absent = not base_face.has(book)
        base_bytes = b"" if base_absent else base_face.read_blob(book)
        try:
            contrib_bytes.decode("utf-8")
        except UnicodeDecodeError:
            det["status"] = "unreadable-contrib"
            evidence.append("registry: kind=%s contrib registry face is not "
                            "valid UTF-8 text — not mechanically "
                            "reconcilable" % kind)
            blocked_kinds.append((kind, book))
            kinds_detail[kind] = det
            continue
        if not base_absent:
            try:
                base_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise MissingInput("base face registry book is not valid "
                                   "UTF-8 text: %s in %s"
                                   % (book, args.base_repo))
        if base_absent:
            det["base_absent"] = True
            evidence.append("registry: kind=%s base face carries no %s — "
                            "union simulated against an empty base face"
                            % (kind, book))
        tb = os.path.join(tmpdir, "book_base_%s.txt" % kind)
        tc = os.path.join(tmpdir, "book_contrib_%s.txt" % kind)
        trep = os.path.join(tmpdir, "union_report_%s.json" % kind)
        _wb(tb, base_bytes)
        _wb(tc, contrib_bytes)
        argv = [sys.executable, "-B", UNION_PY, "--base", tb, "--main", tb,
                "--branch", tc, "--kind", kind, "--json", trep]
        try:
            p = subprocess.run(argv, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=300)
        except subprocess.TimeoutExpired:
            raise InstrumentError("registry_union timed out on kind=%s"
                                  % kind)
        if p.returncode == 0:
            rep = _load_json(trep, "registry_union report")
            stats = rep.get("stats") or {}
            added_keys = sorted({a.get("key") for a in rep.get("added") or []
                                 if a.get("key")})
            det["status"] = "pass"
            det["stats"] = stats
            det["added_keys"] = added_keys
            evidence.append(
                "registry: kind=%s union dry-run zero conflict — main=%s "
                "+ unique=%s = union=%s%s"
                % (kind, stats.get("main"), stats.get("unique"),
                   stats.get("union"),
                   "; contrib-only keys: " + ", ".join(added_keys)
                   if added_keys else "; no contrib-only rows"))
        elif p.returncode == 2 and b"ASSERT-BLAST" in p.stderr:
            code, items, added_keys, colliding, new_dups = \
                _replay_union_blast(tb, tc, kind)
            det["status"] = "block"
            det["assertion_code"] = code
            det["assertion_items"] = items
            det["added_keys"] = added_keys
            blocked_kinds.append((kind, book))
            evidence.append("registry: kind=%s registry_union assertion "
                            "blast %s" % (kind, code))
            if "A2" in code and colliding:
                evidence.append(
                    "registry: kind=%s contrib-added keys already "
                    "registered in the base face: %s"
                    % (kind, ", ".join(colliding)))
            if "A3" in code and new_dups:
                evidence.append(
                    "registry: kind=%s contrib rows introduce new repeated "
                    "anchor text: %s" % (kind, ", ".join(new_dups)))
        else:
            raise InstrumentError(
                "registry_union exited %d on kind=%s (stderr: %s)"
                % (p.returncode, kind,
                   clip(p.stderr.decode("utf-8", errors="replace"))))
        kinds_detail[kind] = det
    verdict = "BLOCK" if blocked_kinds else "PASS"
    details = {"kinds": kinds_detail}
    if blocked_kinds:
        details["prescription"] = build_prescription(args, blocked_kinds)
        details["prescription_note"] = (
            "the registry_union step regenerates each collided book on the "
            "base lineage (base rows preserved, contrib-only rows "
            "appended); the registry_audit --fix-plan plus registry_fix "
            "chain then applies the residual hygiene with rollback "
            "evidence")
        evidence.append("registry: regeneration prescription attached "
                        "(registry_union regeneration + registry_audit "
                        "--fix-plan + registry_fix chain) — see "
                        "details.prescription")
    return {"name": "registry", "verdict": verdict, "warn_count": 0,
            "evidence": evidence, "details": details}


# ---------- gate 2: norm ----------

def resolve_jargon_map(args):
    """--jargon-map given -> must exist; else base repository docs table,
    then this repository's copy; none present -> missing input."""
    if args.jargon_map:
        if not os.path.isfile(args.jargon_map):
            raise MissingInput("jargon map not found: %s" % args.jargon_map)
        return os.path.abspath(args.jargon_map)
    cands = [os.path.join(os.path.abspath(args.base_repo),
                          *DEFAULT_JARGON_MAP_REL),
             os.path.join(_REPO_ROOT, *DEFAULT_JARGON_MAP_REL)]
    for c in cands:
        if os.path.isfile(c):
            return c
    raise MissingInput("jargon map not found (tried: %s)"
                       % ", ".join(cands))


def gate_norm(args, contrib_face, changed, prefixes, tmpdir):
    """Gate norm: each new or changed prose face through norm_lint --file on
    materialized content; error-level findings block, warn-level ones are
    recorded only (norm_lint grading mirrored, never re-graded here)."""
    rels = sorted(p for p in set(changed["added"]) | set(changed["modified"])
                  if os.path.splitext(p)[1].lower() in FACES)
    evidence = []
    files = []
    error_total = 0
    warn_total = 0
    map_path = resolve_jargon_map(args)
    for i, rel in enumerate(rels):
        local = materialize(contrib_face, rel, tmpdir, "norm%d" % i)
        tj = os.path.join(tmpdir, "norm_report_%d.json" % i)
        argv = [sys.executable, "-B", NORM_PY, "--file", local,
                "--jargon-map", map_path, "--json", tj]
        try:
            p = subprocess.run(argv, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=300)
        except subprocess.TimeoutExpired:
            raise InstrumentError("norm_lint timed out on %s" % rel)
        if p.returncode != 0:
            raise InstrumentError(
                "norm_lint exited %d on %s (stderr: %s)"
                % (p.returncode, rel,
                   clip(p.stderr.decode("utf-8", errors="replace"))))
        rep = _load_json(tj, "norm_lint report")
        recs = rep.get("files") or []
        if len(recs) != 1:
            raise InstrumentError("norm_lint returned %d file records for "
                                  "a single --file run on %s"
                                  % (len(recs), rel))
        findings = recs[0].get("findings") or []
        errs = [f for f in findings if f.get("kind") not in WARN_KINDS]
        warns = [f for f in findings if f.get("kind") in WARN_KINDS]
        error_total += len(errs)
        warn_total += len(warns)
        files.append({"path": rel, "error": len(errs), "warn": len(warns),
                      "findings": findings})
        if errs:
            shown = "; ".join("L%s %s: %s" % (f.get("line"), f.get("kind"),
                                              f.get("term"))
                              for f in errs[:EVIDENCE_CAP])
            more = "" if len(errs) <= EVIDENCE_CAP else \
                " …(+%d more)" % (len(errs) - EVIDENCE_CAP)
            evidence.append("norm: %s — %d error-level finding(s) "
                            "(blocking): %s%s"
                            % (rel, len(errs), shown, more))
        elif warns:
            evidence.append("norm: %s — %d warn-level finding(s) recorded "
                            "(non-blocking)" % (rel, len(warns)))
    verdict = "BLOCK" if error_total else "PASS"
    if not rels:
        evidence.append("norm: no new or changed prose faces (.py/.sh/.md) "
                        "in scope")
    return {"name": "norm", "verdict": verdict, "warn_count": warn_total,
            "evidence": evidence,
            "details": {"jargon_map": map_path, "files": files,
                        "error_total": error_total,
                        "warn_total": warn_total}}


# ---------- gate 3: gate expectations ----------

GATE4_RC_VERDICT = {0: ("PASS",), 1: ("FAIL",),
                    2: ("REVIEW", "UNREADABLE")}


def gate_gate_expectation(args, contrib_face, changed, tmpdir):
    """Gate gate_expectation: gate4 --file per changed .v face (hard FAIL
    blocks; review items are recorded, non-blocking) plus the gate7 probe
    availability precheck (real probe only when --rocq-cmd is given)."""
    evidence = []
    blocked = False
    warn_count = 0
    vfiles = sorted(p for p in set(changed["added"])
                    | set(changed["modified"])
                    if p.endswith(".v"))
    rows = []
    for i, rel in enumerate(vfiles):
        local = materialize(contrib_face, rel, tmpdir, "g4_%d" % i)
        tj = os.path.join(tmpdir, "gate4_report_%d.json" % i)
        argv = [sys.executable, "-B", GATE4_PY, "--file", local,
                "--json", tj]
        try:
            p = subprocess.run(argv, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=300)
        except subprocess.TimeoutExpired:
            raise InstrumentError("gate4 timed out on %s" % rel)
        if p.returncode not in GATE4_RC_VERDICT:
            raise InstrumentError(
                "gate4 exited %d on %s (stderr: %s)"
                % (p.returncode, rel,
                   clip(p.stderr.decode("utf-8", errors="replace"))))
        out = _load_json(tj, "gate4 report")
        results = out.get("results") or []
        if len(results) != 1:
            raise InstrumentError("gate4 returned %d result records for a "
                                  "single --file run on %s"
                                  % (len(results), rel))
        r = results[0]
        verdict = r.get("verdict")
        hard = len(r.get("hard") or [])
        review = len(r.get("review") or [])
        if verdict not in GATE4_RC_VERDICT[p.returncode]:
            raise InstrumentError(
                "gate4 rc=%d but verdict=%r on %s — instrument contract "
                "drift" % (p.returncode, verdict, rel))
        rows.append({"path": rel, "verdict": verdict, "hard": hard,
                     "review": review,
                     "header_fields": r.get("header_fields") or []})
        if verdict == "FAIL":
            blocked = True
            evidence.append("gate4: %s — FAIL (hard=%d review=%d) — "
                            "blocking" % (rel, hard, review))
        elif verdict == "PASS" and review == 0:
            evidence.append("gate4: %s — PASS" % rel)
        else:
            warn_count += review
            evidence.append("gate4: %s — %s (hard=%d review=%d) — review "
                            "items recorded (non-blocking)"
                            % (rel, verdict, hard, review))
    if not vfiles:
        evidence.append("gate4: no changed .v faces in scope — per-file "
                        "scan skipped")
    gate7 = _gate7_precheck(args)
    evidence.extend(gate7["evidence"])
    blocked = blocked or gate7["blocked"]
    warn_count += gate7["warn_count"]
    verdict = "BLOCK" if blocked else "PASS"
    return {"name": "gate_expectation", "verdict": verdict,
            "warn_count": warn_count, "evidence": evidence,
            "details": {"gate4": rows, "gate7": gate7["details"]}}


def _gate7_precheck(args):
    """gate7 probe availability precheck.  availability-only mode records
    the canonical launcher faces (env knobs mirror wrapper/gate7_probe.sh)
    and executes nothing; --rocq-cmd runs `<CMD> --version` and a failure
    blocks the gate."""
    evidence = []
    blocked = False
    warn_count = 0
    script = os.environ.get("GATE7_PROBE_SCRIPT", GATE7_SCRIPT_DEFAULT)
    envsh = os.environ.get("GATE7_PROBE_ENV", GATE7_ENV_DEFAULT)
    shim = os.path.join(_REPO_ROOT, "wrapper", "coqc_shim.sh")
    faces = {
        "gate7_script": os.path.isfile(script),
        "coqc_shim": os.path.isfile(shim),
        "toolchain_env": os.path.isfile(envsh),
        "rocq_on_path": shutil.which("rocq") is not None,
        "coqc_on_path": shutil.which("coqc") is not None,
    }
    details = {"mode": None, "faces": faces, "probe": None}
    if args.rocq_cmd:
        details["mode"] = "real-probe"
        if shutil.which(args.rocq_cmd) is None \
                and not os.path.isfile(args.rocq_cmd):
            raise MissingInput("--rocq-cmd not found on this host: %s"
                               % args.rocq_cmd)
        try:
            p = subprocess.run([args.rocq_cmd, "--version"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=60)
        except subprocess.TimeoutExpired:
            details["probe"] = {"rc": None, "timed_out": True}
            blocked = True
            evidence.append("gate7: real probe timed out — gate7 toolchain "
                            "expectation not established (blocking)")
        except OSError as e:
            raise MissingInput("--rocq-cmd not executable: %s (%s)"
                               % (args.rocq_cmd, e))
        else:
            line = _first_line(p.stdout)
            details["probe"] = {"rc": p.returncode, "version_line": line}
            if p.returncode == 0 and line:
                evidence.append("gate7: real probe (%s --version) rc=0 — %s"
                                % (args.rocq_cmd, line))
            else:
                blocked = True
                evidence.append("gate7: real probe failed rc=%s — gate7 "
                                "toolchain expectation not established "
                                "(blocking)" % p.returncode)
    else:
        details["mode"] = "availability-only"
        state = " ".join("%s=%s" % (k, "present" if v else "absent")
                         for k, v in sorted(faces.items()))
        evidence.append("gate7: availability-only precheck (no --rocq-cmd "
                        "given, nothing executed) — %s" % state)
        if not any(faces.values()):
            warn_count += 1
            evidence.append("gate7: probe chain wholly unavailable on this "
                            "host — extraction expectation deferred to CI "
                            "(recorded, non-blocking)")
    return {"evidence": evidence, "blocked": blocked,
            "warn_count": warn_count, "details": details}


# ---------- gate 4: isolation ----------

def gate_isolation(args, changed, book_paths):
    """Gate isolation: tally changed paths outside the contribution lane.
    Warning-level only: the gate never blocks (protocol §2: anything a
    contribution adds outside its lane must be justified in the intake
    record; this gate is that record's mechanical face)."""
    prefixes = parse_prefixes([args.lane_prefix]) or [DEFAULT_LANE_PREFIX]
    touched = sorted(set(changed["added"]) | set(changed["modified"]))
    inside = [p for p in touched if in_filter(p, prefixes)]
    outside = [p for p in touched if not in_filter(p, prefixes)]
    deleted_outside = [p for p in changed["deleted"]
                       if not in_filter(p, prefixes)]
    overlap = len(outside) + len(deleted_outside)
    evidence = []
    lane = ", ".join("'%s/'" % p for p in prefixes)
    evidence.append("isolation: lane %s — %d changed path(s) inside, %d "
                    "outside (warning-level, non-blocking)"
                    % (lane, len(inside), overlap))
    if outside:
        shown = ", ".join(outside[:PATHS_CAP])
        more = "" if len(outside) <= PATHS_CAP else \
            " …(+%d more)" % (len(outside) - PATHS_CAP)
        evidence.append("isolation: outside-lane paths: %s%s"
                        % (shown, more))
    if deleted_outside:
        shown = ", ".join(deleted_outside[:PATHS_CAP])
        evidence.append("isolation: deleted paths outside the lane: %s"
                        % shown)
    registry_overlap = sorted(
        p for p in set(outside) | set(deleted_outside) if p in book_paths)
    if registry_overlap:
        evidence.append("isolation: registry faces among the overlap (%s) "
                        "are adjudicated by gate registry"
                        % ", ".join(registry_overlap))
    if not touched and not changed["deleted"]:
        evidence.append("isolation: empty changed surface — lane account "
                        "vacuous")
    return {"name": "isolation", "verdict": "PASS",
            "warn_count": overlap, "evidence": evidence,
            "details": {"lane_prefixes": prefixes, "inside": inside,
                        "outside": outside,
                        "deleted_outside": deleted_outside,
                        "overlap_total": overlap,
                        "registry_overlap": registry_overlap}}


# ---------- run ----------

def run_intake(args):
    """Full four-gate run -> report dict.  Gates never short-circuit; an
    instrument failure aborts with exit 1 (no verdict can be issued)."""
    for tool in (UNION_PY, NORM_PY, GATE4_PY):
        if not os.path.isfile(tool):
            raise MissingInput("sibling instrument missing: %s" % tool)
    base_face = RepoFace(args.base_repo, args.base_ref, "base")
    contrib_face = RepoFace(args.contrib_repo, args.contrib_ref, "contrib")
    prefixes = parse_prefixes(args.paths)
    changed = compute_changed(base_face, contrib_face, prefixes)
    tmpdir = tempfile.mkdtemp(prefix="rocqwash_ci_")
    try:
        gates = [
            gate_registry(args, base_face, contrib_face, prefixes, tmpdir),
            gate_norm(args, contrib_face, changed, prefixes, tmpdir),
            gate_gate_expectation(args, contrib_face, changed, tmpdir),
            gate_isolation(args, changed,
                           (args.order_path, args.project_path)),
        ]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    block_gates = [g["name"] for g in gates if g["verdict"] == "BLOCK"]
    warn_total = sum(g.get("warn_count", 0) for g in gates)
    counts = {k: len(changed[k]) for k in ("added", "modified", "deleted")}
    report = {
        "schema": SCHEMA,
        "tool": TOOL,
        "inputs": {
            "contrib_repo": args.contrib_repo,
            "contrib_ref": args.contrib_ref,
            "base_repo": args.base_repo,
            "base_ref": args.base_ref,
            "paths": prefixes,
            "order_path": args.order_path,
            "project_path": args.project_path,
            "lane_prefix": parse_prefixes([args.lane_prefix]),
            "rocq_cmd": args.rocq_cmd,
            "jargon_map_flag": args.jargon_map,
        },
        "faces": {
            "contrib": {"path": contrib_face.path, "ref": contrib_face.ref,
                        "mode": contrib_face.mode,
                        "engine": contrib_face.engine,
                        "listed_paths": len(contrib_face.files)},
            "base": {"path": base_face.path, "ref": base_face.ref,
                     "mode": base_face.mode, "engine": base_face.engine,
                     "listed_paths": len(base_face.files)},
        },
        "changed_surface": {
            "added": changed["added"],
            "modified": changed["modified"],
            "deleted": changed["deleted"],
            "counts": counts,
            "paths_filter": prefixes,
        },
        "gates": gates,
        "summary": {
            "verdict": "BLOCK" if block_gates else "PASS",
            "block_gates": block_gates,
            "gates_pass": len(gates) - len(block_gates),
            "gates_block": len(block_gates),
            "warn_total": warn_total,
            "changed_counts": counts,
        },
    }
    return report


def print_report(report):
    """Loud stdout account (deterministic)."""
    print("=== CONTRIB-INTAKE (%s) ===" % SCHEMA)
    f = report["faces"]
    print("  contrib face: %s @ %s (mode=%s)"
          % (f["contrib"]["path"], f["contrib"]["ref"],
             f["contrib"]["mode"]))
    print("  base face:    %s @ %s (mode=%s)"
          % (f["base"]["path"], f["base"]["ref"], f["base"]["mode"]))
    cs = report["changed_surface"]
    filt = cs["paths_filter"]
    print("  changed surface: added=%d modified=%d deleted=%d (paths "
          "filter: %s)"
          % (cs["counts"]["added"], cs["counts"]["modified"],
             cs["counts"]["deleted"],
             ", ".join(filt) if filt else "none"))
    for g in report["gates"]:
        print("--- gate %s: %s ---" % (g["name"], g["verdict"]))
        for ev in g["evidence"]:
            print("  " + ev)
    s = report["summary"]
    if s["verdict"] == "PASS":
        print("CONTRIB-INTAKE VERDICT: PASS — all four gates pass "
              "(warnings recorded: %d)" % s["warn_total"])
    else:
        print("CONTRIB-INTAKE VERDICT: BLOCK — blocked gates: %s (warnings "
              "recorded: %d) [verdict is data; exit 0]"
              % (", ".join(s["block_gates"]), s["warn_total"]))


def dump_json(path, obj):
    """Deterministic JSON report (sort_keys + indent=1, house style)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="contribution intake inspector issuing read-only "
                    "four-gate verdicts (registry / norm / gate "
                    "expectation / isolation)")
    ap.add_argument("--contrib-repo", required=True, metavar="PATH",
                    help="contribution face: local clone or archive tree")
    ap.add_argument("--contrib-ref", required=True, metavar="REF",
                    help="contribution ref (nominal for an archive face)")
    ap.add_argument("--base-repo", required=True, metavar="PATH",
                    help="receiving face repository path")
    ap.add_argument("--base-ref", default=DEFAULT_BASE_REF, metavar="REF",
                    help="receiving face ref (default main)")
    ap.add_argument("--paths", action="append", default=None, metavar="P1,P2",
                    help="restrict the adjudication surface (repeatable, "
                         "comma-split prefixes)")
    ap.add_argument("--order-path", default=DEFAULT_ORDER_PATH,
                    metavar="PATH", help="registry order book path")
    ap.add_argument("--project-path", default=DEFAULT_PROJECT_PATH,
                    metavar="PATH", help="registry coqproject book path")
    ap.add_argument("--lane-prefix", default=DEFAULT_LANE_PREFIX,
                    metavar="PREFIX",
                    help="contribution lane prefixes, comma-split "
                         "(default contrib/)")
    ap.add_argument("--jargon-map", default=None, metavar="PATH",
                    help="mapping table for the norm gate (default: base "
                         "repository docs table, then this repository)")
    ap.add_argument("--rocq-cmd", default=None, metavar="CMD",
                    help="gate7 real probe command (absent = "
                         "availability-only precheck)")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="report target (schema rocqwash-contrib-intake/1)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        report = run_intake(args)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except InstrumentError as e:
        print("INSTRUMENT-FAILURE: %s" % e, file=sys.stderr)
        sys.exit(1)

    print_report(report)
    if args.json:
        dump_json(args.json, report)
        print("json -> %s" % args.json)
    sys.exit(0)


# ---------- selftest ----------

CLEAN_PY = '''"""clean_extra: minimal clean python face for the intake selftest.

Purpose.  Provide a compliant prose face that the norm gate passes.
Interface.  None (fixture data).
Dependencies.  Python 3 standard library only.
Evidence.  Intake selftest asserts an empty lint report for this face.
Exit-codes.  0.
"""
# the counter invariant holds because the loop bound never decreases
COUNT = 1
'''

JARGON_PY = '''"""jargon_face: norm-gate blocking fixture for the intake selftest.

Purpose.  Carry one error-level jargon hit for the norm gate to report.
Interface.  None (fixture data).
Dependencies.  Python 3 standard library only.
Evidence.  Intake selftest asserts one jargon finding on this face.
Exit-codes.  0.
"""
# the next wave ships tomorrow
COUNT = 1
'''

CORE_PY = '''"""core_lib: base-side core fixture for the intake selftest.

Purpose.  Represent a core-lane face that a contribution may overlap.
Interface.  None (fixture data).
Dependencies.  Python 3 standard library only.
Evidence.  Intake selftest asserts lane accounting for this face.
Exit-codes.  0.
"""
CORE_COUNT = 1
'''

CORE_PY_V2 = CORE_PY.replace("CORE_COUNT = 1", "CORE_COUNT = 2")

GAMMA_V = '''(* Gamma.v — clean node fixture for the intake selftest.
   Mission.  Provide a minimal fixture that passes the gate4 comment guard.
   Dependencies.  Rocq standard library only.
   References.  rocqwash README and docs/architecture.
   Constructivity.  All statements are Set-carried; proofs close with Qed;
      no excluded middle and no classical principle appears in this sample.
   Build.  rocq c -native-compiler no -q -Q . "" Gamma.v
*)

Require Import QArith.

Lemma gamma_order : forall x y : Q, QltT x y -> QltT (x + y) (y + x).
Proof.
  intros x y H. exact H.
Qed.
'''

ORDER_V1 = "Alpha.v#R0-11111111\nBeta.v#R0-22222222\n"
ORDER_V2 = ORDER_V1 + "Delta.v#R0-44444444\n"
PROJECT_V1 = '-Q . ""\nAlpha.v\nBeta.v\n'
PROJECT_V2 = PROJECT_V1 + "Delta.v\n"

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
           "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"}


def selftest():
    """Temporary dual-clone fixture vectors (zero network, zero compile):
    1 clean contribution (all four gates PASS, registry unique rows only)
    2 registry collision (A2 blast, BLOCK, prescription attached)
    3 norm jargon hit (error-level finding, norm gate BLOCK)
    4 core-lane overlap (warning-level only, verdict PASS)
    5 read-only + determinism + archive parity + paths filter
    6 gate7 real-probe outcomes + CLI four-code checks.
    """
    import hashlib as _hashlib

    here = os.path.dirname(os.path.abspath(__file__))
    ci_py = os.path.join(here, PROG + ".py")

    def run(argv):
        p = subprocess.run([sys.executable, "-B", ci_py] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wf(path, text):
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    def git(repo, *a):
        env = dict(os.environ)
        env.update(GIT_ENV)
        p = subprocess.run(["git", "-C", repo] + list(a), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert p.returncode == 0, p.stdout
        return p.stdout.decode("utf-8", errors="replace").strip()

    def build_base_repo(root):
        """Base repository: main carries two commits (clean books, then the
        Delta rows) so a stale branch can collide on the Delta key."""
        repo = os.path.join(root, "base")
        os.makedirs(repo)
        git(repo, "init")
        br = git(repo, "symbolic-ref", "--short", "HEAD")
        if br != "main":
            git(repo, "branch", "-m", "main")
        wf(os.path.join(repo, "order.txt"), ORDER_V1)
        wf(os.path.join(repo, "_CoqProject"), PROJECT_V1)
        wf(os.path.join(repo, "core_lib.py"), CORE_PY)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base snapshot one")
        wf(os.path.join(repo, "order.txt"), ORDER_V2)
        wf(os.path.join(repo, "_CoqProject"), PROJECT_V2)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base adds Delta registry rows")
        return repo

    def clone_at(base_repo, dest, start, branch):
        p = subprocess.run(["git", "clone", "-q", base_repo, dest],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert p.returncode == 0, p.stdout
        git(dest, "checkout", "-q", "-b", branch, start)
        return dest

    def md5_of(path):
        h = _hashlib.md5()
        with io.open(path, "rb") as fh:
            h.update(fh.read())
        return h.hexdigest()

    def tree_md5(root):
        rows = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            for fn in sorted(filenames):
                rows.append((os.path.relpath(os.path.join(dirpath, fn),
                                             root), md5_of(
                                                 os.path.join(dirpath, fn))))
        return sorted(rows)

    def gates_by_name(rep):
        return dict((g["name"], g) for g in rep["gates"])

    tmp = tempfile.mkdtemp(prefix="rocqwash_ci_self_")
    try:
        base = build_base_repo(os.path.join(tmp, "v1"))
        assert git(base, "rev-parse", "--verify", "main"), "base main"

        # ---- vector 1: clean contribution -> all four gates PASS ----
        c1 = clone_at(base, os.path.join(tmp, "v1", "contrib"), "main",
                      "clean")
        wf(os.path.join(c1, "contrib", "Gamma.v"), GAMMA_V)
        wf(os.path.join(c1, "contrib", "clean_extra.py"), CLEAN_PY)
        wf(os.path.join(c1, "order.txt"),
           ORDER_V2 + "contrib/Gamma.v#R1-33333333\n")
        wf(os.path.join(c1, "_CoqProject"), PROJECT_V2 + "contrib/Gamma.v\n")
        git(c1, "add", "-A")
        git(c1, "commit", "-q", "-m", "clean contrib lane")
        r1 = os.path.join(tmp, "v1", "r1.json")
        p = run(["--contrib-repo", c1, "--contrib-ref", "clean",
                 "--base-repo", base, "--base-ref", "main", "--json", r1])
        assert p.returncode == 0, p.stdout
        rep1 = json.load(io.open(r1, encoding="utf-8"))
        assert rep1["schema"] == SCHEMA, rep1["schema"]
        assert rep1["summary"]["verdict"] == "PASS", rep1["summary"]
        assert rep1["summary"]["block_gates"] == [], rep1["summary"]
        assert rep1["changed_surface"]["added"] == \
            ["contrib/Gamma.v", "contrib/clean_extra.py"], \
            rep1["changed_surface"]
        assert rep1["changed_surface"]["modified"] == \
            ["_CoqProject", "order.txt"], rep1["changed_surface"]
        g1 = gates_by_name(rep1)
        assert all(g["verdict"] == "PASS" for g in g1.values()), g1
        k1 = g1["registry"]["details"]["kinds"]
        assert k1["order"]["status"] == "pass" \
            and k1["order"]["added_keys"] == ["contrib/Gamma.v"], k1["order"]
        assert k1["order"]["stats"]["unique"] == 1, k1["order"]["stats"]
        assert k1["coqproject"]["added_keys"] == ["Gamma"], k1["coqproject"]
        assert g1["norm"]["details"]["error_total"] == 0, g1["norm"]
        assert g1["gate_expectation"]["details"]["gate4"][0]["verdict"] \
            == "PASS", g1["gate_expectation"]
        iso1 = g1["isolation"]["details"]
        assert iso1["inside"] == ["contrib/Gamma.v", "contrib/clean_extra.py"] \
            and iso1["outside"] == ["_CoqProject", "order.txt"], iso1
        assert iso1["registry_overlap"] == ["_CoqProject", "order.txt"], iso1
        assert rep1["summary"]["warn_total"] == 2, rep1["summary"]
        print("  [1/6] clean contribution OK (verdict PASS, registry "
              "unique=1 both kinds, gate4 PASS, lane account: 2 inside / "
              "2 registry overlap, warnings recorded)")

        # ---- vector 2: registry collision -> gate registry BLOCK ----
        d2 = os.path.join(tmp, "v2")
        base2 = build_base_repo(d2)
        stale = git(base2, "rev-parse", "main~1")
        c2 = clone_at(base2, os.path.join(d2, "contrib"), stale, "collide")
        wf(os.path.join(c2, "order.txt"),
           ORDER_V1 + "Delta.v#R0-abababab\n")
        wf(os.path.join(c2, "_CoqProject"), PROJECT_V1 + "Delta.v\n")
        git(c2, "add", "-A")
        git(c2, "commit", "-q", "-m", "stale branch adds Delta row")
        r2 = os.path.join(d2, "r2.json")
        p = run(["--contrib-repo", c2, "--contrib-ref", "collide",
                 "--base-repo", base2, "--base-ref", "main", "--json", r2])
        assert p.returncode == 0, p.stdout
        rep2 = json.load(io.open(r2, encoding="utf-8"))
        assert rep2["summary"]["verdict"] == "BLOCK", rep2["summary"]
        assert rep2["summary"]["block_gates"] == ["registry"], rep2["summary"]
        g2 = gates_by_name(rep2)
        k2 = g2["registry"]["details"]["kinds"]
        assert k2["order"]["status"] == "block" \
            and k2["order"]["assertion_code"] == "A2-ADDED-KEY-IN-MAIN", \
            k2["order"]
        assert k2["coqproject"]["status"] == "pass", k2["coqproject"]
        presc = g2["registry"]["details"]["prescription"]
        assert any("registry_union.py" in c for c in presc) \
            and any("registry_audit.py" in c for c in presc) \
            and any("registry_fix.py" in c for c in presc), presc
        assert any("--kind order" in c for c in presc), presc
        assert g2["norm"]["verdict"] == "PASS" \
            and g2["gate_expectation"]["verdict"] == "PASS", g2
        assert rep2["summary"]["warn_total"] >= 1, rep2["summary"]
        print("  [2/6] registry collision OK (A2-ADDED-KEY-IN-MAIN, "
              "registry BLOCK, coqproject pass, prescription chain "
              "union+audit+fix attached)")

        # ---- vector 3: norm jargon hit -> gate norm BLOCK ----
        d3 = os.path.join(tmp, "v3")
        base3 = build_base_repo(d3)
        c3 = clone_at(base3, os.path.join(d3, "contrib"), "main", "jargon")
        wf(os.path.join(c3, "contrib", "jargon_face.py"), JARGON_PY)
        git(c3, "add", "-A")
        git(c3, "commit", "-q", "-m", "jargon face")
        r3 = os.path.join(d3, "r3.json")
        p = run(["--contrib-repo", c3, "--contrib-ref", "jargon",
                 "--base-repo", base3, "--base-ref", "main", "--json", r3])
        assert p.returncode == 0, p.stdout
        rep3 = json.load(io.open(r3, encoding="utf-8"))
        assert rep3["summary"]["verdict"] == "BLOCK", rep3["summary"]
        assert rep3["summary"]["block_gates"] == ["norm"], rep3["summary"]
        g3 = gates_by_name(rep3)
        n3 = g3["norm"]
        assert n3["details"]["error_total"] == 1, n3["details"]
        hits = [f for f in n3["details"]["files"][0]["findings"]
                if f["kind"] == "jargon"]
        assert len(hits) == 1 and hits[0]["term"] == "wave", hits
        assert g3["registry"]["verdict"] == "PASS", g3["registry"]
        print("  [3/6] norm jargon hit OK (error-level wave finding, norm "
              "BLOCK, registry PASS)")

        # ---- vector 4: core-lane overlap -> warning only, PASS ----
        d4 = os.path.join(tmp, "v4")
        base4 = build_base_repo(d4)
        c4 = clone_at(base4, os.path.join(d4, "contrib"), "main", "core")
        wf(os.path.join(c4, "core_lib.py"), CORE_PY_V2)
        git(c4, "add", "-A")
        git(c4, "commit", "-q", "-m", "core overlap")
        r4 = os.path.join(d4, "r4.json")
        p = run(["--contrib-repo", c4, "--contrib-ref", "core",
                 "--base-repo", base4, "--base-ref", "main", "--json", r4])
        assert p.returncode == 0, p.stdout
        rep4 = json.load(io.open(r4, encoding="utf-8"))
        assert rep4["summary"]["verdict"] == "PASS", rep4["summary"]
        assert rep4["summary"]["block_gates"] == [], rep4["summary"]
        g4 = gates_by_name(rep4)
        iso4 = g4["isolation"]
        assert iso4["verdict"] == "PASS" \
            and iso4["details"]["outside"] == ["core_lib.py"], iso4
        assert rep4["changed_surface"]["modified"] == ["core_lib.py"], \
            rep4["changed_surface"]
        assert g4["norm"]["details"]["error_total"] == 0, g4["norm"]
        assert rep4["summary"]["warn_total"] == 1, rep4["summary"]
        print("  [4/6] core-lane overlap OK (warning-level only, verdict "
              "PASS, overlap recorded on core_lib.py)")

        # ---- vector 5: read-only + determinism + archive + paths filter ----
        pre = tree_md5(base) + tree_md5(c1)
        r1b = os.path.join(tmp, "v1", "r1b.json")
        p = run(["--contrib-repo", c1, "--contrib-ref", "clean",
                 "--base-repo", base, "--base-ref", "main", "--json", r1b])
        assert p.returncode == 0, p.stdout
        post = tree_md5(base) + tree_md5(c1)
        assert pre == post, "read-only violation: fixture tree drift"
        assert io.open(r1b, "rb").read() == io.open(r1, "rb").read(), \
            "determinism violation: report byte drift"
        # archive parity: same content as a plain tree must diff empty
        d5 = os.path.join(tmp, "v5")
        os.makedirs(d5)
        arc = os.path.join(d5, "arc_contrib")
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            for fn in sorted(filenames):
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, base)
                with io.open(src, "rb") as fh:
                    wf(os.path.join(arc, rel),
                       fh.read().decode("utf-8", errors="replace"))
        wf(os.path.join(arc, "contrib", "archive_extra.py"), CLEAN_PY)
        r5 = os.path.join(d5, "r5.json")
        p = run(["--contrib-repo", arc, "--contrib-ref", "snapshot",
                 "--base-repo", base, "--base-ref", "main", "--json", r5])
        assert p.returncode == 0, p.stdout
        rep5 = json.load(io.open(r5, encoding="utf-8"))
        assert rep5["faces"]["contrib"]["mode"] == "archive", rep5["faces"]
        assert rep5["changed_surface"]["added"] == \
            ["contrib/archive_extra.py"], rep5["changed_surface"]
        assert rep5["changed_surface"]["modified"] == [], \
            rep5["changed_surface"]
        assert rep5["changed_surface"]["deleted"] == [], \
            rep5["changed_surface"]
        assert rep5["summary"]["verdict"] == "PASS", rep5["summary"]
        # paths filter: contrib/ scope drops the registry books from the
        # surface and marks them out-of-scope in the registry gate
        r5b = os.path.join(d5, "r5b.json")
        p = run(["--contrib-repo", c1, "--contrib-ref", "clean",
                 "--base-repo", base, "--base-ref", "main",
                 "--paths", "contrib/", "--json", r5b])
        assert p.returncode == 0, p.stdout
        rep5b = json.load(io.open(r5b, encoding="utf-8"))
        assert rep5b["changed_surface"]["added"] == \
            ["contrib/Gamma.v", "contrib/clean_extra.py"], \
            rep5b["changed_surface"]
        assert rep5b["changed_surface"]["modified"] == [], \
            rep5b["changed_surface"]
        g5b = gates_by_name(rep5b)
        assert g5b["registry"]["details"]["kinds"]["order"]["status"] \
            == "out-of-scope", g5b["registry"]
        assert g5b["isolation"]["details"]["outside"] == [], \
            g5b["isolation"]
        print("  [5/6] read-only + determinism + archive parity + paths "
              "filter OK (tree md5 stable, report byte-identical, archive "
              "diff empty plus one added face, contrib/ scope drops the "
              "books as out-of-scope)")

        # ---- vector 6: gate7 real-probe outcomes + CLI four codes ----
        r6a = os.path.join(tmp, "v1", "r6a.json")
        p = run(["--contrib-repo", c1, "--contrib-ref", "clean",
                 "--base-repo", base, "--base-ref", "main",
                 "--rocq-cmd", shutil.which("echo"), "--json", r6a])
        assert p.returncode == 0, p.stdout
        rep6a = json.load(io.open(r6a, encoding="utf-8"))
        g6a = gates_by_name(rep6a)["gate_expectation"]
        assert g6a["details"]["gate7"]["mode"] == "real-probe", g6a
        assert g6a["details"]["gate7"]["probe"]["rc"] == 0, g6a
        assert rep6a["summary"]["verdict"] == "PASS", rep6a["summary"]
        r6b = os.path.join(tmp, "v1", "r6b.json")
        p = run(["--contrib-repo", c1, "--contrib-ref", "clean",
                 "--base-repo", base, "--base-ref", "main",
                 "--rocq-cmd", shutil.which("false"), "--json", r6b])
        assert p.returncode == 0, p.stdout
        rep6b = json.load(io.open(r6b, encoding="utf-8"))
        assert rep6b["summary"]["verdict"] == "BLOCK", rep6b["summary"]
        assert rep6b["summary"]["block_gates"] == ["gate_expectation"], \
            rep6b["summary"]
        assert gates_by_name(rep6b)["gate_expectation"]["details"]\
            ["gate7"]["probe"]["rc"] == 1, rep6b["gates"]
        # CLI four codes
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should be usage 2, got %d" \
            % p.returncode
        p = run([])
        assert p.returncode == 2, "no input should be usage 2, got %d" \
            % p.returncode
        p = run(["--contrib-repo", os.path.join(tmp, "nope"),
                 "--contrib-ref", "x", "--base-repo", base,
                 "--base-ref", "main"])
        assert p.returncode == 9, "missing face should be 9, got %d" \
            % p.returncode
        p = run(["--contrib-repo", c1, "--contrib-ref", "no-such-ref",
                 "--base-repo", base, "--base-ref", "main"])
        assert p.returncode == 9, "bad ref should be 9, got %d" \
            % p.returncode
        print("  [6/6] gate7 real-probe outcomes + CLI four-codes OK "
              "(echo probe rc=0 PASS, false probe rc=1 gate BLOCK, "
              "help0/bogus2/no-input2/missing9/badref9)")

        print("CONTRIB-INTAKE-SELFTEST PASS: clean/collision/jargon/"
              "overlap four judgments plus read-only, determinism, "
              "archive parity, paths filter, probe outcomes and CLI "
              "checks all pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
