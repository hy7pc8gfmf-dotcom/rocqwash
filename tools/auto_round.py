#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto_round.py: auto round ledger, admission, rollback and salvage port.

Purpose.  Close the loop after a rewrite pass: admit the rewrite classes
  per the autonomy gear, commit the touched files as one verified round,
  append one ledger row (append-only JSONL), mark the commit with round
  trailers plus a lightweight round ref, and keep anchor, rollback, drift
  salvage and the query faces on one code path; every mutating face
  validates before it writes.

Interface.  `python -I tools/auto_round.py <command>`; commands: commit,
  approve, anchor, rollback, salvage, merge-salvage, status, list, log,
  plus --selftest and --repo-root/--autonomy/--state/--ledger overrides;
  the full flag face lives in the extended contract block below.  Shared
  exports for sibling apply faces: `load_autonomy`, `admission_decision`,
  `load_state`, `load_rounds`, `next_round_id`.

Dependencies.  Python 3 standard library only; the `git` executable on
  PATH (commits, refs, revert); zero network on every face.

Evidence.  --selftest runs fixture vectors on throwaway git repositories:
  commit marking, ledger row shape, both admission gears, soft stop,
  oscillation alert, rollback archive-then-revert, salvage round trip,
  refusal branches, query faces, zero network (audit-hook observed).

Exit-codes.  0 = the face completed or answered (a nothing-to-do skip is
  data); 1 = a gate refused (pending class, soft stop, verify gate red,
  certification-face scope, selftest red); 2 = usage error; 9 = missing
  or corrupt input (damaged ledger, state, autonomy or git surface,
  unmatched salvage rows, unresolvable target).
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
#
# Commands and flags
#   commit --classes C1,C2 --files F1,F2 [--hits H.json]
#     [--class-confidence NAME=VALUE ...] [--message TEXT] [--continue]
#     [--dry-run]
#       wrap the working-tree changes of the listed files into one verified
#       round: admission per the gear, soft stop check, verify gate, one
#       commit, one lightweight ref, one ledger row.  A round whose listed
#       files carry no pending change is a loud nothing-to-do (exit 0, no
#       write), so re-running a landed round is safe.
#   approve --class NAME [--confidence X] [--note TEXT]
#       record a human admission; the class then rides as existing in both
#       gears.
#   anchor [--set SHA | --promote]
#       set or promote the review anchor (the baseline every rollback
#       returns to); no flag shows the current anchor.
#   rollback [--to anchor | SHA | round:N]
#       two mandatory steps: archive the drift chain under
#       refs/rocqwash/drift/<utc><round> (existing archives are never
#       overwritten), then one revert commit back to the target tree; the
#       gate runs on the reverted tree before the commit and a red gate
#       aborts the revert.  No reset, no history rewrite, nothing contacts
#       a remote.
#   salvage --from drift/<id> --emit OUT.jsonl
#       walk the drift chain, diff each round commit per file, and emit one
#       offer row per maximal change segment:
#       {hunk_id, round_id, class, file, before, after}
#       (class attribution follows the round row; a round that mixed
#       classes reports them joined by "+").
#   merge-salvage IN.jsonl [--from drift/<id>]
#       recompute the offer package from the drift refs, require every row
#       to match by hunk_id with an equal before text, then land the
#       refined rows as ONE gated commit behind the verify gate (trailers
#       Rocqwash-Mode: salvage and Rocqwash-Salvage-Of: drift/<id>).  Rows
#       apply in round order against an evolving per-file buffer, and each
#       before text must occur exactly once at its apply time (this is the
#       anchor-face consistency check of the contract).  Three offer
#       shapes: modify, insertion (empty before creates an absent file or
#       appends one line, deterministic), deletion (empty after removes the
#       newline-terminated before lines).  A red gate restores the touched
#       files.  The drift ref survives the merge.
#   status | list [--limit N] | log [--round N]
#       the three query faces for human review; list and log need the
#       ledger (absent ledger exits 9), status reports a fresh machine as
#       rounds=0.
#
# Gear config autonomy.json (repo root; every key optional)
#   mode                   "auto" admits a new rewrite class by threshold
#                          grade, "gated" waits for a human approval; both
#                          gears share one code path (admission_decision)
#                          and differ only in the adjudicator.
#   admission_threshold    float in [0, 1]; gear auto admits a new class
#                          when its confidence grade reaches the threshold.
#   max_unreviewed_rounds  soft stop: at that many rounds past the anchor
#                          the next commit refuses until a review promote
#                          or an explicit --continue.
#   oscillation_alert      a file:line site touched in that many rounds
#                          fires a loud drift warning and counts into
#                          oscillation_count.
#   verify_cmd             gate command as an argv list (extension key
#                          beyond the four gear keys); default runs
#                          tools/norm_lint.py --selftest from the repo
#                          root; the ledger records which gate produced
#                          verify_rc as the verify_kind key.
#
# Ledger row (docs/round-ledger.jsonl, append-only JSONL, schema
# rocqwash-round/1): the ten contract keys plus the additive verify_kind
# key on rows written since the verify-swap face (old ten-key rows stay
# valid and are never rewritten):
#   round_id, mode, base_sha, head_sha, classes_applied, admissions, files,
#   verify_rc, oscillation_count, timestamp_utc, verify_kind
# admissions rows: {class, decision, confidence, threshold, basis}; only
# classes admitted by this round appear here (out-of-band approvals live
# in the state file).  The ledger and the state file are working-tree
# records: this port never stages them, so a rollback revert cannot
# rewrite the recorded round history.
#
# State file (docs/round-state.json, schema rocqwash.round-state/1):
#   anchor           {sha, round_id} or null
#   admitted_classes [{class, confidence, basis, coq_comment_safe,
#                      timestamp_utc}]
#   line_hits        {"<file>:<line>": touch count}
#
# Certification-face scope: a .v file rides only classes whose
# coq_comment_safe flag is true; the built-in registry ships comment-face
# classes only and is never widened by machine action.

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCHEMA_ROW = "rocqwash-round/1"
SCHEMA_STATE = "rocqwash.round-state/1"
LEDGER_NAME = "round-ledger.jsonl"
STATE_NAME = "round-state.json"
AUTONOMY_NAME = "autonomy.json"
ROUND_REF_ROOT = "refs/rocqwash/rounds"
DRIFT_REF_ROOT = "refs/rocqwash/drift"
SELFTEST_MARK = "AUTO-ROUND-SELFTEST PASS"
# Audit events that constitute a network attempt (V18).  socket.connect
# covers an outbound connection; urllib.Request covers a URL open driven
# through the standard library opener.  A module loaded into sys.modules
# is not network behavior, so the vector records attempts, not imports.
NETWORK_ATTEMPT_EVENTS = ("socket.connect", "urllib.Request")
GEARS = ("auto", "gated")
MODES = ("auto", "gated", "salvage", "rollback")

DEFAULT_AUTONOMY = {
    "mode": "auto",
    "admission_threshold": 0.8,
    "max_unreviewed_rounds": 12,
    "oscillation_alert": 2,
}
# default gate: the repository self-check the baseline report pins as green
DEFAULT_VERIFY_CMD = [sys.executable, "-I", "-X", "utf8", "tools/norm_lint.py", "--selftest"]

ROW_KEYS = ("round_id", "mode", "base_sha", "head_sha", "classes_applied",
            "admissions", "files", "verify_rc", "oscillation_count",
            "timestamp_utc", "verify_kind")
# rows written before the verify-swap face carry exactly these ten keys
# and stay valid forever (additive key; old rows are never rewritten)
ROW_KEYS_LEGACY = ROW_KEYS[:-1]
STATE_KEYS = ("schema", "anchor", "admitted_classes", "line_hits")
ANCHOR_KEYS = ("sha", "round_id")
ADMIT_KEYS = ("class", "confidence", "basis", "coq_comment_safe",
              "timestamp_utc")

# factory-known comment-face classes; names follow the interface contract
# example and the E2 replace-only disposition
CLASS_REGISTRY = {
    "date-strip": {"confidence": 0.95, "coq_comment_safe": True},
    "admission-vocab": {"confidence": 0.9, "coq_comment_safe": True},
    "jargon-replace": {"confidence": 0.9, "coq_comment_safe": True},
}


class FailLoud(Exception):
    """Raised on any refusal the caller must see; carries the exit code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _utcnow():
    """Timezone-aware UTC now (datetime.utcnow is deprecated in 3.12+)."""
    return datetime.datetime.now(datetime.timezone.utc)


def _utc_ts():
    """ISO-8601 UTC timestamp string for ledger and state rows."""
    return _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_compact():
    """Compact UTC digit stamp for drift ref names (no separators)."""
    return _utcnow().strftime("%Y%m%d%H%M%S")


def iso_head(text):
    """True when the string opens with a valid ISO date head."""
    head = str(text).split("T", 1)[0]
    try:
        datetime.date.fromisoformat(head)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------- config --
def load_autonomy(path):
    """Gear config merged over the built-in defaults; damage fails loud."""
    cfg = dict(DEFAULT_AUTONOMY)
    cfg["verify_cmd"] = list(DEFAULT_VERIFY_CMD)
    if not os.path.isfile(path):
        return cfg
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError) as exc:
        raise FailLoud(9, "autonomy config unreadable: %s (%s)" % (path, exc))
    if not isinstance(raw, dict):
        raise FailLoud(9, "autonomy config must hold a JSON object: %s" % path)
    unknown = sorted(set(raw) - set(cfg))
    if unknown:
        raise FailLoud(9, "autonomy config has unknown keys %s: %s"
                       % (unknown, path))
    gear = raw.get("mode", cfg["mode"])
    if gear not in GEARS:
        raise FailLoud(9, "autonomy mode must be auto or gated: %r" % (gear,))
    cfg["mode"] = gear
    threshold = raw.get("admission_threshold", cfg["admission_threshold"])
    if (isinstance(threshold, bool) or not isinstance(threshold, (int, float))
            or not 0.0 <= float(threshold) <= 1.0):
        raise FailLoud(9, "admission_threshold must be a number in [0, 1]: %r"
                       % (threshold,))
    cfg["admission_threshold"] = float(threshold)
    cap = raw.get("max_unreviewed_rounds", cfg["max_unreviewed_rounds"])
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
        raise FailLoud(9, "max_unreviewed_rounds must be an int >= 1: %r"
                       % (cap,))
    cfg["max_unreviewed_rounds"] = cap
    alert = raw.get("oscillation_alert", cfg["oscillation_alert"])
    if isinstance(alert, bool) or not isinstance(alert, int) or alert < 1:
        raise FailLoud(9, "oscillation_alert must be an int >= 1: %r"
                       % (alert,))
    cfg["oscillation_alert"] = alert
    vcmd = raw.get("verify_cmd", cfg["verify_cmd"])
    if (not isinstance(vcmd, list) or not vcmd
            or not all(isinstance(part, str) for part in vcmd)):
        raise FailLoud(9, "verify_cmd must be a non-empty list of strings")
    cfg["verify_cmd"] = list(vcmd)
    return cfg


def admission_decision(gear, cls, confidence, threshold, known):
    """One code path for both gears; the gear only picks the adjudicator.

    Returns (decision, basis) with decision in "existing" / "admitted" /
    "pending"; gear auto admits a new class when its confidence grade
    reaches the threshold, gear gated waits for a human approval.
    """
    if cls in known:
        return "existing", "class already admitted (registry or approval)"
    if gear == "auto":
        if confidence is None:
            return "pending", ("gear auto self-admission needs a confidence "
                               "grade (registry or --class-confidence)")
        if float(confidence) >= threshold:
            return "admitted", ("gear auto: confidence %.2f >= threshold "
                                "%.2f" % (float(confidence), threshold))
        return "pending", ("gear auto: confidence %.2f below threshold %.2f"
                           % (float(confidence), threshold))
    return "pending", "gear gated: first instance awaits human approval"


def registry_confidence(cls):
    """Confidence grade of a factory-known class; None when unknown."""
    entry = CLASS_REGISTRY.get(cls)
    return entry["confidence"] if entry else None


def known_classes(state):
    """Registry names plus every approved class in the state file."""
    names = set(CLASS_REGISTRY)
    for entry in state["admitted_classes"]:
        names.add(entry["class"])
    return names


def safe_flags(state):
    """coq_comment_safe flag per known class (approval never widens it)."""
    flags = {name: CLASS_REGISTRY[name]["coq_comment_safe"]
             for name in CLASS_REGISTRY}
    for entry in state["admitted_classes"]:
        flags[entry["class"]] = bool(entry["coq_comment_safe"])
    return flags


# ----------------------------------------------------------------- state --
def blank_state():
    """Fresh state shape (schema rocqwash.round-state/1)."""
    return {"schema": SCHEMA_STATE, "anchor": None, "admitted_classes": [],
            "line_hits": {}}


def _bad(path, where, why):
    return FailLoud(9, "round state %s is corrupt at %s: %s"
                    % (path, where, why))


def validate_state(state, path):
    """Strict shape check; any deviation fails loud as corrupt input."""
    if not isinstance(state, dict):
        raise _bad(path, "root", "not a JSON object")
    if set(state) != set(STATE_KEYS):
        raise _bad(path, "root", "keys must be exactly %s" % (STATE_KEYS,))
    if state["schema"] != SCHEMA_STATE:
        raise _bad(path, "schema", str(state["schema"]))
    anchor = state["anchor"]
    if anchor is not None:
        if not isinstance(anchor, dict) or set(anchor) != set(ANCHOR_KEYS):
            raise _bad(path, "anchor", "keys must be exactly %s"
                       % (ANCHOR_KEYS,))
        if not isinstance(anchor["sha"], str) or not anchor["sha"]:
            raise _bad(path, "anchor.sha", "must be a non-empty string")
        if (isinstance(anchor["round_id"], bool)
                or not isinstance(anchor["round_id"], int)
                or anchor["round_id"] < 0):
            raise _bad(path, "anchor.round_id", "must be an int >= 0")
    for entry in state["admitted_classes"]:
        if not isinstance(entry, dict) or set(entry) != set(ADMIT_KEYS):
            raise _bad(path, "admitted_classes",
                       "entry keys must be %s" % (ADMIT_KEYS,))
        if not isinstance(entry["class"], str) or not entry["class"]:
            raise _bad(path, "admitted_classes.class", "must be a name")
        conf = entry["confidence"]
        if conf is not None and (isinstance(conf, bool)
                                 or not isinstance(conf, (int, float))):
            raise _bad(path, "admitted_classes.confidence",
                       "must be a number or null")
        if not isinstance(entry["basis"], str):
            raise _bad(path, "admitted_classes.basis", "must be a string")
        if not isinstance(entry["coq_comment_safe"], bool):
            raise _bad(path, "admitted_classes.coq_comment_safe",
                       "must be a boolean")
        if not isinstance(entry["timestamp_utc"], str) \
                or not iso_head(entry["timestamp_utc"]):
            raise _bad(path, "admitted_classes.timestamp_utc",
                       "must be an ISO timestamp")
    if not isinstance(state["line_hits"], dict):
        raise _bad(path, "line_hits", "must be a JSON object")
    for key, count in state["line_hits"].items():
        if ":" not in str(key):
            raise _bad(path, "line_hits key", str(key))
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise _bad(path, "line_hits value", "%s=%r" % (key, count))


def load_state(path):
    """State at path, or the blank shape when the file is absent."""
    if not os.path.isfile(path):
        return blank_state()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, ValueError) as exc:
        raise FailLoud(9, "round state unreadable: %s (%s)" % (path, exc))
    validate_state(state, path)
    return state


def save_state(path, state):
    """Write the state file in one compact line (parent dirs created)."""
    validate_state(state, path)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


# ---------------------------------------------------------------- ledger --
def validate_row(row, path, lineno):
    """Strict ten-key row check; any deviation fails loud as corruption."""
    where = "round ledger %s line %s" % (path, lineno)
    if not isinstance(row, dict):
        raise FailLoud(9, "%s is not a JSON object" % where)
    if set(row) not in (set(ROW_KEYS), set(ROW_KEYS_LEGACY)):
        raise FailLoud(9, "%s keys must be the ten contract keys, or the "
                          "ten plus the additive verify_kind key, got %s"
                          % (where, sorted(row)))
    rid = row["round_id"]
    if isinstance(rid, bool) or not isinstance(rid, int) or rid < 1:
        raise FailLoud(9, "%s round_id must be an int >= 1" % where)
    if row["mode"] not in MODES:
        raise FailLoud(9, "%s mode must be one of %s" % (where, MODES))
    for key in ("base_sha", "head_sha", "timestamp_utc"):
        if not isinstance(row[key], str) or not row[key]:
            raise FailLoud(9, "%s %s must be a non-empty string" % (where, key))
    if not iso_head(row["timestamp_utc"]):
        raise FailLoud(9, "%s timestamp_utc must be an ISO timestamp" % where)
    for key in ("classes_applied", "files"):
        if not isinstance(row[key], list) \
                or not all(isinstance(x, str) for x in row[key]):
            raise FailLoud(9, "%s %s must be a list of strings" % (where, key))
    if not isinstance(row["admissions"], list) \
            or not all(isinstance(x, dict) for x in row["admissions"]):
        raise FailLoud(9, "%s admissions must be a list of objects" % where)
    for key in ("verify_rc", "oscillation_count"):
        val = row[key]
        if isinstance(val, bool) or not isinstance(val, int) or val < 0:
            raise FailLoud(9, "%s %s must be an int >= 0" % (where, key))
    if "verify_kind" in row and (not isinstance(row["verify_kind"], str)
                                 or not row["verify_kind"]):
        raise FailLoud(9, "%s verify_kind must be a non-empty string"
                          % where)


def load_rounds(path):
    """Parse the round ledger; absent returns None; damage fails loud."""
    if not os.path.isfile(path):
        return None
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise FailLoud(9, "round ledger %s line %d is not valid JSON "
                                  "(%s)" % (path, lineno, exc))
            validate_row(row, path, lineno)
            rows.append(row)
    ids = [row["round_id"] for row in rows]
    if ids != list(range(1, len(ids) + 1)):
        raise FailLoud(9, "round ledger %s ids are not consecutive from 1: %s"
                       % (path, ids))
    return rows


def next_round_id(rows):
    """Next round id; ids are validated consecutive, so this is len + 1."""
    return len(rows or []) + 1


def append_row(path, row):
    """Append one ledger line (parent dirs created)."""
    validate_row(row, path, "next")
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")) + "\n")


def build_row(number, mode, base_sha, head_sha, classes, admissions, files,
              verify_rc, oscillation_count, stamp, verify_cmd=None):
    """Round row in contract key order; verify_kind rides the additive
    key and names the gate that produced verify_rc."""
    return {
        "round_id": number,
        "mode": mode,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "classes_applied": list(classes),
        "admissions": list(admissions),
        "files": list(files),
        "verify_rc": int(verify_rc),
        "oscillation_count": int(oscillation_count),
        "timestamp_utc": stamp,
        "verify_kind": verify_kind_of(verify_cmd),
    }


# ------------------------------------------------------------------- git --
def run_git(repo, git_args, stdin_text=None, timeout=120):
    """Run git inside the repo; returns (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(["git", "-C", repo] + list(git_args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              input=stdin_text, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FailLoud(9, "git not runnable (%s): %s" % (git_args, exc))
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def git_out(repo, git_args, what):
    """Run git and return stdout, or fail loud with the stderr tail."""
    rc, out, err = run_git(repo, git_args)
    if rc != 0:
        raise FailLoud(9, "%s failed (git rc=%d): %s"
                       % (what, rc, (err or out).strip()[-400:]))
    return out


def ensure_git(repo):
    """Fail loud unless the repo root is a git work tree."""
    rc, out, err = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if rc != 0 or out.strip() != "true":
        raise FailLoud(9, "not a git work tree: %s (%s)"
                       % (repo, (err or out).strip()[:200]))


def head_sha(repo):
    """Full sha of the current HEAD commit."""
    return git_out(repo, ["rev-parse", "HEAD"], "HEAD lookup").strip()


def resolve_sha(repo, name):
    """Resolve a revision to a full sha, or None when it does not resolve."""
    rc, out, _ = run_git(repo, ["rev-parse", "--verify", "--quiet",
                                name + "^{commit}"])
    return out.strip() or None if rc == 0 else None


def ref_sha(repo, refname):
    """Sha a ref points at, or None when the ref does not exist."""
    out = git_out(repo, ["for-each-ref", "--format=%(objectname)", refname],
                  "ref lookup")
    return out.strip() or None


def ref_exists(repo, refname):
    """True when the exact ref exists (loose or packed)."""
    out = git_out(repo, ["for-each-ref", refname], "ref lookup")
    return bool(out.strip())


def is_ancestor(repo, older, newer):
    """True when commit `older` is an ancestor of (or equal to) `newer`."""
    rc, _, _ = run_git(repo, ["merge-base", "--is-ancestor", older, newer])
    return rc == 0


def git_commit(repo, message):
    """Create one commit from the staged index; returns the new sha."""
    rc, out, err = run_git(repo, ["commit", "-F", "-"], stdin_text=message)
    if rc != 0:
        raise FailLoud(9, "git commit failed (rc=%d): %s"
                       % (rc, (err or out).strip()[-400:]))
    return head_sha(repo)


def round_message(text, number, mode, extra=()):
    """Commit message with the trailing round trailers."""
    lines = [text.strip(), "", "Rocqwash-Round: %d" % number,
             "Rocqwash-Mode: %s" % mode]
    lines.extend(extra)
    return "\n".join(lines) + "\n"


def changed_files(repo, files):
    """Subset of files with a pending change vs HEAD (untracked included)."""
    rc, out, err = run_git(repo, ["status", "--porcelain", "--"] + files)
    if rc != 0:
        raise FailLoud(9, "git status failed: %s" % (err or out).strip()[-400:])
    marked = set()
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        marked.add(path.replace("\\", "/"))
    return sorted(f for f in files if f in marked)


# ------------------------------------------------------------------ gate --
def verify_kind_of(cmd):
    """Ledger verify_kind token for a gate argv: the stem of the first
    gate script element (the argv element ending .py; interpreter and
    flag elements never match, the element after -c/-m is skipped), else
    "custom".  Deterministic; the default gate maps to norm_lint."""
    skip = False
    for part in cmd or []:
        if skip:
            skip = False
            continue
        if part in ("-c", "-m"):
            skip = True
            continue
        if isinstance(part, str) and part.endswith(".py"):
            return os.path.splitext(os.path.basename(part))[0]
    return "custom"


def run_verify(repo, cmd):
    """Run the mechanical verification gate from the repo root."""
    if cmd == DEFAULT_VERIFY_CMD \
            and not os.path.isfile(os.path.join(repo, "tools",
                                                "norm_lint.py")):
        raise FailLoud(9, "default verify gate script missing: "
                          "tools/norm_lint.py (set verify_cmd in "
                          "autonomy.json)")
    try:
        proc = subprocess.run(cmd, cwd=repo, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, encoding="utf-8",
                              errors="replace", timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FailLoud(9, "verify gate not runnable: %s (%s)" % (cmd, exc))
    return proc.returncode, (proc.stdout or "").strip()[-600:]


# ----------------------------------------------------------------- input --
def normalize_rel(path):
    """Repo-relative forward-slash path; refuses escapes outside the root."""
    rel = path.strip().replace("\\", "/")
    if os.path.isabs(rel) or rel.startswith("../") or rel == ".." \
            or "/../" in rel or rel.endswith("/.."):
        raise FailLoud(9, "file path must stay inside the repository: %s"
                       % rel)
    return rel


def repo_file(repo, rel):
    """Absolute path of a repo-relative file that must exist."""
    full = os.path.join(repo, rel)
    if not os.path.isfile(full):
        raise FailLoud(9, "file not found in the repository: %s" % rel)
    return full


def split_list_arg(text, flag):
    """Comma-separated non-empty list; duplicates are a usage error."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        raise FailLoud(2, "%s needs a comma-separated non-empty list" % flag)
    if len(set(parts)) != len(parts):
        raise FailLoud(2, "%s carries duplicate entries" % flag)
    return parts


def parse_class_confidence(items):
    """NAME=VALUE pairs into a dict; bad syntax is a usage error."""
    out = {}
    for item in items or []:
        name, sep, value = item.partition("=")
        if not sep or not name.strip():
            raise FailLoud(2, "--class-confidence needs NAME=VALUE, got %r"
                           % item)
        try:
            grade = float(value)
        except ValueError:
            raise FailLoud(2, "--class-confidence value must be a number: %r"
                           % item)
        if not 0.0 <= grade <= 1.0:
            raise FailLoud(2, "--class-confidence value must be in [0, 1]: "
                             "%r" % item)
        out[name.strip()] = grade
    return out


def load_hits(repo, path):
    """Parse a --hits file: [{file, line}, ...]; damage fails loud."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError) as exc:
        raise FailLoud(9, "hits file unreadable: %s (%s)" % (path, exc))
    if not isinstance(raw, list):
        raise FailLoud(9, "hits file must hold a JSON array: %s" % path)
    hits = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"file", "line"}:
            raise FailLoud(9, "each hits row must be exactly {file, line}: %r"
                           % (item,))
        rel = normalize_rel(str(item["file"]))
        line = item["line"]
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            raise FailLoud(9, "hits row line must be an int >= 1: %r"
                           % (item,))
        repo_file(repo, rel)
        hits.append({"file": rel, "line": line})
    return hits


def track_hits(state, hits, alert, persist):
    """Accumulate touch counts; return (alert sites, count) for this round."""
    alerts = []
    for hit in hits:
        key = "%s:%d" % (hit["file"], hit["line"])
        count = state["line_hits"].get(key, 0) + 1
        if persist:
            state["line_hits"][key] = count
        if count >= alert:
            alerts.append((hit["file"], hit["line"], count))
    return alerts, len(alerts)


def count_unreviewed(rows, state):
    """Rounds past the anchor (all rounds when no anchor is recorded)."""
    floor = 0
    anchor = state["anchor"]
    if anchor:
        floor = anchor["round_id"]
    return sum(1 for row in (rows or []) if row["round_id"] > floor)


def scope_refusals(files, classes, flags):
    """Certification faces ride only comment-safe classes."""
    bad = []
    for rel in files:
        if rel.endswith(".v"):
            for cls in classes:
                if not flags.get(cls, False):
                    bad.append("%s (class %s)" % (rel, cls))
    return bad


# ----------------------------------------------------------------- paths --
def resolve_paths(args, repo):
    """Ledger, state and autonomy paths with their in-repo defaults."""
    ledger = args.ledger or os.path.join(repo, "docs", LEDGER_NAME)
    state = args.state or os.path.join(repo, "docs", STATE_NAME)
    autonomy = args.autonomy or os.path.join(repo, AUTONOMY_NAME)
    return ledger, state, autonomy


def resolve_repo(args):
    """Repo root from --repo-root or the default parent of tools/."""
    root = args.repo_root or repo_root()
    if not os.path.isdir(root):
        raise FailLoud(9, "repo root is not a directory: %s" % root)
    return root


def load_all(args):
    """Repo, gear config, ledger and state in one call."""
    repo = resolve_repo(args)
    ledger, state_path, autonomy_path = resolve_paths(args, repo)
    cfg = load_autonomy(autonomy_path)
    rows = load_rounds(ledger)
    state = load_state(state_path)
    return repo, cfg, ledger, state_path, rows, state


# ---------------------------------------------------------------- commit --
def admission_rows(classes, conf_map, cfg, known):
    """Admission outcome for the gear: (new admission rows, pending list)."""
    rows, pending = [], []
    for cls in classes:
        grade = conf_map.get(cls, registry_confidence(cls))
        decision, basis = admission_decision(cfg["mode"], cls, grade,
                                             cfg["admission_threshold"], known)
        if decision == "admitted":
            rows.append({"class": cls, "decision": "admitted",
                         "confidence": float(grade),
                         "threshold": cfg["admission_threshold"],
                         "basis": basis})
        elif decision == "pending":
            pending.append("%s (%s)" % (cls, basis))
    return rows, pending


def cmd_commit(args):
    """Wrap the listed working-tree changes into one verified round."""
    repo, cfg, ledger, state_path, rows, state = load_all(args)
    ensure_git(repo)
    classes = split_list_arg(args.classes, "--classes")
    files = [normalize_rel(p) for p in split_list_arg(args.files, "--files")]
    for rel in files:
        repo_file(repo, rel)
    conf_map = parse_class_confidence(args.class_confidence)
    bad_scope = scope_refusals(files, classes, safe_flags(state))
    if bad_scope:
        raise FailLoud(1, "certification-face scope refusal: %s; only "
                          "comment-safe classes may touch .v files"
                       % "; ".join(bad_scope))
    known = known_classes(state)
    admissions, pending = admission_rows(classes, conf_map, cfg, known)
    if pending:
        raise FailLoud(1, "admission pending in gear %s: %s; remedy: "
                          "'approve --class NAME' or pass --class-confidence"
                       % (cfg["mode"], "; ".join(pending)))
    unreviewed = count_unreviewed(rows, state)
    if unreviewed >= cfg["max_unreviewed_rounds"] and not args.force_continue:
        raise FailLoud(1, "soft stop: %d unreviewed rounds reached the cap "
                          "%d; remedy: 'anchor --promote' after review, or "
                          "rerun with --continue"
                       % (unreviewed, cfg["max_unreviewed_rounds"]))
    changed = changed_files(repo, files)
    hits = load_hits(repo, args.hits) if args.hits else []
    alerts, _ = track_hits(state, hits, cfg["oscillation_alert"],
                           persist=False)
    number = next_round_id(rows)
    if args.dry_run:
        sys.stdout.write("dry-run round=%d mode=%s classes=%s changed=%d "
                         "alerts=%d gate=%s\n"
                         % (number, cfg["mode"], ",".join(classes),
                            len(changed), len(alerts),
                            " ".join(cfg["verify_cmd"])))
        return 0
    if not changed:
        sys.stdout.write("nothing-to-commit: no pending change in the "
                         "listed files (a landed round reruns as this "
                         "skip)\n")
        return 0
    verify_rc, verify_tail = run_verify(repo, cfg["verify_cmd"])
    if verify_rc != 0:
        raise FailLoud(1, "verify gate red (rc=%d); round refused; gate "
                          "tail: %s" % (verify_rc, verify_tail))
    round_ref = "%s/%d" % (ROUND_REF_ROOT, number)
    if ref_exists(repo, round_ref):
        raise FailLoud(9, "round ref already exists (refs are never "
                          "overwritten): %s" % round_ref)
    base = head_sha(repo)
    rc, _, err = run_git(repo, ["add", "--"] + files)
    if rc != 0:
        raise FailLoud(9, "git add failed: %s" % (err or "").strip()[-400:])
    message = round_message(args.message
                            or "round %d: %s in %d file(s)"
                            % (number, ", ".join(classes), len(changed)),
                            number, cfg["mode"])
    head = git_commit(repo, message)
    git_out(repo, ["update-ref", round_ref, head], "round ref move")
    alerts, osc_count = track_hits(state, hits, cfg["oscillation_alert"],
                                   persist=True)
    stamp = _utc_ts()
    for adm in admissions:
        state["admitted_classes"].append({
            "class": adm["class"],
            "confidence": adm["confidence"],
            "basis": adm["basis"],
            "coq_comment_safe": bool(
                CLASS_REGISTRY.get(adm["class"], {})
                .get("coq_comment_safe", False)),
            "timestamp_utc": stamp,
        })
    save_state(state_path, state)
    append_row(ledger, build_row(number, cfg["mode"], base, head, classes,
                                 admissions, changed, verify_rc, osc_count,
                                 stamp, verify_cmd=cfg["verify_cmd"]))
    sys.stdout.write("round=%d mode=%s head=%s files=%d classes=%s\n"
                     % (number, cfg["mode"], head[:12], len(changed),
                        ",".join(classes)))
    for adm in admissions:
        sys.stdout.write("admitted: class=%s basis=%s\n"
                         % (adm["class"], adm["basis"]))
    for rel, line, count in alerts:
        sys.stdout.write("oscillation-alert: %s:%d touched in %d rounds\n"
                         % (rel, line, count))
    return 0


# --------------------------------------------------------------- approve --
def cmd_approve(args):
    """Record a human admission into the state approval table."""
    _, _, _, state_path, _, state = load_all(args)
    conf = args.confidence
    entry = {
        "class": args.cls,
        "confidence": float(conf) if conf is not None
        else registry_confidence(args.cls),
        "basis": args.note or "human approval",
        "coq_comment_safe": bool(
            CLASS_REGISTRY.get(args.cls, {}).get("coq_comment_safe", False)),
        "timestamp_utc": _utc_ts(),
    }
    state["admitted_classes"] = [
        e for e in state["admitted_classes"] if e["class"] != args.cls]
    state["admitted_classes"].append(entry)
    save_state(state_path, state)
    sys.stdout.write("approved class=%s basis=%s\n"
                     % (args.cls, entry["basis"]))
    return 0


# ---------------------------------------------------------------- anchor --
def cmd_anchor(args):
    """Set or promote the review anchor, or show it."""
    repo, _, _, state_path, rows, state = load_all(args)
    if args.set_sha and args.promote:
        raise FailLoud(2, "--set and --promote are exclusive")
    if args.set_sha:
        ensure_git(repo)
        sha = resolve_sha(repo, args.set_sha)
        if not sha:
            raise FailLoud(9, "anchor target does not resolve: %s"
                           % args.set_sha)
        state["anchor"] = {"sha": sha, "round_id": len(rows or [])}
        save_state(state_path, state)
        sys.stdout.write("anchor set sha=%s rounds-covered=%d\n"
                         % (sha[:12], state["anchor"]["round_id"]))
        return 0
    if args.promote:
        ensure_git(repo)
        head = head_sha(repo)
        state["anchor"] = {"sha": head, "round_id": len(rows or [])}
        save_state(state_path, state)
        sys.stdout.write("anchor promoted head=%s rounds-covered=%d\n"
                         % (head[:12], state["anchor"]["round_id"]))
        return 0
    anchor = state["anchor"]
    if anchor:
        sys.stdout.write("anchor=%s round=%d\n"
                         % (anchor["sha"][:12], anchor["round_id"]))
    else:
        sys.stdout.write("anchor=none (set one with 'anchor --set SHA' or "
                         "'anchor --promote')\n")
    return 0


# -------------------------------------------------------------- rollback --
def resolve_target(repo, state, rows, to_ref):
    """Rollback target as (sha, round number) from anchor/SHA/round:N."""
    if to_ref in (None, "", "anchor"):
        anchor = state["anchor"]
        if not anchor:
            raise FailLoud(9, "no anchor recorded; set one first "
                              "('anchor --set SHA' or 'anchor --promote')")
        return anchor["sha"], anchor["round_id"]
    if to_ref.startswith("round:"):
        tail = to_ref[len("round:"):]
        if not tail.isdigit():
            raise FailLoud(2, "--to round:N needs a number, got %r" % to_ref)
        number = int(tail)
        sha = ref_sha(repo, "%s/%d" % (ROUND_REF_ROOT, number))
        if not sha:
            raise FailLoud(9, "no round ref for round %d" % number)
        return sha, number
    sha = resolve_sha(repo, to_ref)
    if not sha:
        raise FailLoud(9, "rollback target does not resolve: %s" % to_ref)
    for number in range(1, (len(rows or []) or 0) + 1):
        if ref_sha(repo, "%s/%d" % (ROUND_REF_ROOT, number)) == sha:
            return sha, number
    return sha, 0


def cmd_rollback(args):
    """Archive the drift chain first, then one revert commit back to it."""
    repo, cfg, ledger, state_path, rows, state = load_all(args)
    ensure_git(repo)
    target, target_round = resolve_target(repo, state, rows, args.to_ref)
    pre_head = head_sha(repo)
    if not is_ancestor(repo, target, pre_head):
        raise FailLoud(9, "rollback target is not on the current branch "
                          "history: %s" % target[:12])
    files = [line.replace("\\", "/") for line in git_out(
        repo, ["diff", "--name-only", target, pre_head],
        "target tree diff").splitlines() if line.strip()]
    if not files:
        sys.stdout.write("nothing-to-roll-back: HEAD tree already matches "
                         "the target baseline (%s)\n" % target[:12])
        return 0
    drift_ref = "%s/%s-%d" % (DRIFT_REF_ROOT, _utc_compact(), target_round)
    if ref_exists(repo, drift_ref):
        raise FailLoud(9, "drift ref already exists (archives are never "
                          "overwritten): %s" % drift_ref)
    git_out(repo, ["update-ref", drift_ref, pre_head], "drift archive ref")
    number = next_round_id(rows)
    round_ref = "%s/%d" % (ROUND_REF_ROOT, number)
    if ref_exists(repo, round_ref):
        raise FailLoud(9, "round ref already exists: %s" % round_ref)
    rc, _, err = run_git(repo, ["revert", "--no-commit", "%s..HEAD" % target])
    if rc != 0:
        run_git(repo, ["revert", "--abort"])
        raise FailLoud(9, "revert could not be prepared (branch left "
                          "untouched): %s" % (err or "").strip()[-400:])
    verify_rc, verify_tail = run_verify(repo, cfg["verify_cmd"])
    if verify_rc != 0:
        run_git(repo, ["revert", "--abort"])
        raise FailLoud(1, "verify gate red on the reverted tree (rc=%d); "
                          "revert aborted, branch untouched; tail: %s"
                       % (verify_rc, verify_tail))
    message = round_message("rollback to %s (drift archived as %s)"
                            % (target[:12], drift_ref), number, "rollback")
    head = git_commit(repo, message)
    git_out(repo, ["update-ref", round_ref, head], "round ref move")
    append_row(ledger, build_row(number, "rollback", pre_head, head, [], [],
                                 sorted(files), verify_rc, 0, _utc_ts(),
                                 verify_cmd=cfg["verify_cmd"]))
    sys.stdout.write("rollback round=%d drift-ref=%s head=%s files=%d\n"
                     % (number, drift_ref, head[:12], len(files)))
    return 0


# --------------------------------------------------------------- salvage --
def normalize_drift_ref(arg):
    """Accept drift/<id> or the full ref name; anything else is usage."""
    if arg.startswith(DRIFT_REF_ROOT + "/"):
        return arg
    if arg.startswith("drift/"):
        return DRIFT_REF_ROOT + "/" + arg[len("drift/"):]
    raise FailLoud(2, "--from accepts drift/<id> or %s/<id>, got %r"
                   % (DRIFT_REF_ROOT, arg))


def drift_refs(repo):
    """Every archive ref under the drift namespace, sorted."""
    out = git_out(repo, ["for-each-ref", "--format=%(refname)",
                         DRIFT_REF_ROOT], "drift ref listing")
    return sorted(line for line in out.splitlines() if line.strip())


def round_chain(repo, refname, total):
    """Round ids whose round refs sit inside the drift ref history."""
    head = ref_sha(repo, refname)
    chain = []
    for number in range(1, total + 1):
        sha = ref_sha(repo, "%s/%d" % (ROUND_REF_ROOT, number))
        if sha and is_ancestor(repo, sha, head):
            chain.append(number)
    return chain


def parse_change_segments(diff_text):
    """Maximal change segments of a unified diff, in file order."""
    segments = []
    before, after = [], []

    def flush():
        if before or after:
            segments.append(("\n".join(before), "\n".join(after)))
            del before[:], after[:]

    in_body = False
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            in_body = True
            flush()
            continue
        if not in_body:
            continue
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            before.append(line[1:])
        elif line.startswith("+"):
            after.append(line[1:])
        else:
            flush()
    flush()
    return segments


def build_package(repo, refname, rows):
    """Offer rows for a drift ref, or None when its rounds lack rows."""
    total = len(rows or [])
    if not total:
        return None
    chain = round_chain(repo, refname, total)
    if not chain:
        return None
    by_id = {row["round_id"]: row for row in rows}
    package = []
    for number in chain:
        row = by_id.get(number)
        if row is None:
            raise FailLoud(9, "round ref %d has no ledger row (ledger and "
                              "refs disagree)" % number)
        sha = ref_sha(repo, "%s/%d" % (ROUND_REF_ROOT, number))
        parent = git_out(repo, ["rev-parse", sha + "^"],
                         "parent of round %d" % number).strip()
        label = "+".join(row["classes_applied"]) or "mixed"
        for rel in row["files"]:
            diff = git_out(repo, ["diff", "--unified=3", parent, sha, "--",
                                  rel], "diff of round %d" % number)
            for k, (before, after) in enumerate(
                    parse_change_segments(diff), 1):
                package.append({
                    "hunk_id": "r%d-%s-h%d" % (number,
                                               rel.replace("/", "_"), k),
                    "round_id": number,
                    "class": label,
                    "file": rel,
                    "before": before,
                    "after": after,
                })
    package.sort(key=lambda item: item["hunk_id"])
    return package or None


def cmd_salvage(args):
    """Emit the drift refinement package in the offer-row handoff shape."""
    repo, _, ledger, _, rows, _ = load_all(args)
    ensure_git(repo)
    refname = normalize_drift_ref(args.from_ref)
    if not ref_exists(repo, refname):
        raise FailLoud(9, "drift ref not found: %s" % refname)
    package = build_package(repo, refname, rows)
    if not package:
        raise FailLoud(9, "no marked rounds under drift ref: %s" % refname)
    parent = os.path.dirname(os.path.abspath(args.emit))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(args.emit, "w", encoding="utf-8", newline="\n") as handle:
        for item in package:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    chain = sorted({item["round_id"] for item in package})
    sys.stdout.write("salvage package rows=%d chain=%s ref=%s emit=%s\n"
                     % (len(package), ",".join(str(n) for n in chain),
                        refname, args.emit))
    return 0


def load_refined(path):
    """Parse a refined package; shape damage fails loud."""
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise FailLoud(9, "refined package %s line %d is not valid "
                                  "JSON (%s)" % (path, lineno, exc))
            allowed = {"hunk_id", "round_id", "class", "file", "before",
                       "after", "refined_by", "note"}
            if not isinstance(row, dict) or not set(row) <= allowed:
                raise FailLoud(9, "refined package %s line %d has unknown "
                                  "keys or is not an object" % (path, lineno))
            for key in ("hunk_id", "after", "refined_by"):
                if not isinstance(row.get(key), str) or not row[key]:
                    raise FailLoud(9, "refined package %s line %d: %s must "
                                      "be a non-empty string"
                                   % (path, lineno, key))
            if not isinstance(row.get("before"), str):
                raise FailLoud(9, "refined package %s line %d: before must "
                                  "be a string (empty for an insertion)"
                               % (path, lineno))
            rows.append(row)
    if not rows:
        raise FailLoud(9, "refined package is empty: %s" % path)
    seen = set()
    for row in rows:
        if row["hunk_id"] in seen:
            raise FailLoud(9, "refined package carries duplicate hunk_id: %s"
                           % row["hunk_id"])
        seen.add(row["hunk_id"])
    return rows


def match_drift_ref(repo, refname, refined, rows):
    """True when the recomputed package covers every refined row."""
    package = build_package(repo, refname, rows)
    if package is None:
        return False
    by_id = {item["hunk_id"]: item for item in package}
    for row in refined:
        item = by_id.get(row["hunk_id"])
        if item is None or item["before"] != row["before"]:
            return False
        for key in ("round_id", "file", "class"):
            if key in row and str(row[key]) != str(item[key]):
                return False
    return True


def cmd_merge_salvage(args):
    """Land the refined rows as one gated salvage commit."""
    repo, cfg, ledger, _, rows, _ = load_all(args)
    ensure_git(repo)
    refined = load_refined(args.refined)
    if args.from_ref:
        candidates = [normalize_drift_ref(args.from_ref)]
    else:
        candidates = drift_refs(repo)
    if not candidates:
        raise FailLoud(9, "no drift refs exist to merge from")
    matches = [name for name in candidates
               if match_drift_ref(repo, name, refined, rows)]
    if len(matches) == 0:
        raise FailLoud(9, "no drift ref reproduces the refined rows (hunk_id "
                          "or before mismatch)")
    if len(matches) > 1:
        raise FailLoud(9, "refined rows match several drift refs %s; pass "
                          "--from to disambiguate" % matches)
    refname = matches[0]
    package = {item["hunk_id"]: item
               for item in build_package(repo, refname, rows)}
    # validate every row against the evolving per-file buffer, in round
    # order, before any write hits the working tree; three offer shapes:
    # modify (before and after non-empty), insertion (empty before: create
    # an absent file or append one line), deletion (empty after: the before
    # lines must appear newline-terminated and exactly once)
    order = sorted(refined, key=lambda r: (package[r["hunk_id"]]["round_id"],
                                           r["hunk_id"]))
    buffers = {}
    touched = []
    for row in order:
        item = package[row["hunk_id"]]
        rel = item["file"]
        full = os.path.join(repo, rel)
        before_text = row["before"]
        after_text = row["after"]
        if not os.path.isfile(full):
            if before_text == "":
                prev = buffers.get(rel)
                if prev is None:
                    merged = after_text + "\n" if after_text else ""
                else:
                    tail = "" if prev.endswith("\n") or not prev else "\n"
                    merged = prev + tail + after_text + "\n"
                buffers[rel] = merged
                if rel not in touched:
                    touched.append(rel)
                continue
            raise FailLoud(9, "target file absent in the current tree for "
                              "hunk %s (%s); nothing applied"
                           % (row["hunk_id"], rel))
        if rel not in buffers:
            rc, out, _ = run_git(repo, ["status", "--porcelain", "--", rel])
            if rc != 0 or out.strip():
                raise FailLoud(9, "working tree not clean for %s; merge "
                                  "refuses to mix uncommitted changes" % rel)
            with open(full, "r", encoding="utf-8", newline="") as handle:
                buffers[rel] = handle.read()
            touched.append(rel)
        content = buffers[rel]
        newline = "\r\n" if "\r\n" in content else "\n"
        if before_text == "":
            tail = "" if content.endswith("\n") or not content else newline
            buffers[rel] = content + tail + after_text + newline
            continue
        if after_text == "":
            needle = before_text.replace("\n", newline) + newline
        else:
            needle = before_text.replace("\n", newline)
        count = content.count(needle)
        if count == 0:
            raise FailLoud(9, "before text not found in the current tree "
                              "for hunk %s (%s); nothing applied"
                           % (row["hunk_id"], rel))
        if count > 1:
            raise FailLoud(9, "before text is ambiguous (%d occurrences) "
                              "for hunk %s (%s); nothing applied"
                           % (count, row["hunk_id"], rel))
        buffers[rel] = content.replace(
            needle, after_text.replace("\n", newline), 1)
    for rel in touched:
        with open(os.path.join(repo, rel), "w", encoding="utf-8",
                  newline="") as handle:
            handle.write(buffers[rel])
    verify_rc, verify_tail = run_verify(repo, cfg["verify_cmd"])
    if verify_rc != 0:
        run_git(repo, ["checkout", "--"] + sorted(touched))
        raise FailLoud(1, "verify gate red after the merge apply (rc=%d); "
                          "working tree restored; tail: %s"
                       % (verify_rc, verify_tail))
    number = next_round_id(rows)
    round_ref = "%s/%d" % (ROUND_REF_ROOT, number)
    if ref_exists(repo, round_ref):
        raise FailLoud(9, "round ref already exists: %s" % round_ref)
    base = head_sha(repo)
    rc, _, err = run_git(repo, ["add", "--"] + sorted(touched))
    if rc != 0:
        raise FailLoud(9, "git add failed: %s" % (err or "").strip()[-400:])
    classes = sorted({part for row in refined
                      for part in package[row["hunk_id"]]["class"].split("+")})
    short = refname[len("refs/rocqwash/"):]
    message = round_message("salvage merge of %s (%d hunk(s))"
                            % (short, len(order)), number, "salvage",
                            extra=["Rocqwash-Salvage-Of: %s" % short])
    head = git_commit(repo, message)
    git_out(repo, ["update-ref", round_ref, head], "round ref move")
    append_row(ledger, build_row(number, "salvage", base, head, classes, [],
                                 sorted(touched), verify_rc, 0, _utc_ts(),
                                 verify_cmd=cfg["verify_cmd"]))
    sys.stdout.write("salvage-merged round=%d ref=%s rows=%d head=%s\n"
                     % (number, refname, len(order), head[:12]))
    return 0


# ----------------------------------------------------------------- query --
def cmd_status(args):
    """One-glance review face: gear, anchor, counters, surfaces."""
    repo, cfg, ledger, state_path, rows, state = load_all(args)
    anchor = state["anchor"]
    sys.stdout.write("mode=%s threshold=%s cap=%d alert=%d\n"
                     % (cfg["mode"], cfg["admission_threshold"],
                        cfg["max_unreviewed_rounds"],
                        cfg["oscillation_alert"]))
    if anchor:
        sys.stdout.write("anchor=%s round=%d\n"
                         % (anchor["sha"][:12], anchor["round_id"]))
    else:
        sys.stdout.write("anchor=none\n")
    sys.stdout.write("rounds=%d unreviewed=%d/%d admitted_classes=%d "
                     "oscillation_sites=%d\n"
                     % (len(rows or []), count_unreviewed(rows or [], state),
                        cfg["max_unreviewed_rounds"],
                        len(state["admitted_classes"]),
                        len(state["line_hits"])))
    sys.stdout.write("ledger=%s state=%s\n"
                     % ("present" if rows is not None else "absent",
                        "present" if os.path.isfile(state_path) else "absent"))
    return 0


def cmd_list(args):
    """One summary line per round, ascending; --limit keeps the tail."""
    repo, _, ledger, _, rows, _ = load_all(args)
    if rows is None:
        raise FailLoud(9, "round ledger not found: %s" % ledger)
    picked = rows
    if args.limit is not None:
        if args.limit < 0:
            raise FailLoud(2, "--limit must be >= 0")
        picked = rows[-args.limit:] if args.limit else []
    for row in picked:
        sys.stdout.write("round=%d mode=%s head=%s classes=%s files=%d "
                         "verify_rc=%d\n"
                         % (row["round_id"], row["mode"],
                            row["head_sha"][:12],
                            ",".join(row["classes_applied"]) or "-",
                            len(row["files"]), row["verify_rc"]))
    sys.stderr.write("list: %d/%d rounds\n" % (len(picked), len(rows)))
    return 0


def cmd_log(args):
    """Dump ledger rows as JSON lines; --round N fetches one row."""
    repo, _, ledger, _, rows, _ = load_all(args)
    if rows is None:
        raise FailLoud(9, "round ledger not found: %s" % ledger)
    picked = rows
    if args.round_no is not None:
        picked = [row for row in rows if row["round_id"] == args.round_no]
        if not picked:
            sys.stderr.write("log: round %d not found (zero match is data)\n"
                             % args.round_no)
    for row in picked:
        sys.stdout.write(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    sys.stderr.write("log: %d/%d rows\n" % (len(picked), len(rows)))
    return 0


# -------------------------------------------------------------- selftest --
class OutputSink:
    """Minimal text sink for in-process runs (keeps imports tight)."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def getvalue(self):
        return "".join(self.parts)


def run_cli(args):
    """Run the CLI in-process and return (rc, stdout, stderr)."""
    argv = list(args)
    out = OutputSink()
    err = OutputSink()
    saved = (sys.stdout, sys.stderr)
    sys.stdout = out
    sys.stderr = err
    try:
        rc = main(argv)
    finally:
        sys.stdout, sys.stderr = saved
    return rc, out.getvalue(), err.getvalue()


def _mkrepo(tmp, name, autonomy):
    """Throwaway git repo with a probe file, a .v file and a gear config."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    run_git(root, ["init", "-q"])
    run_git(root, ["config", "user.name", "Round Fixture"])
    run_git(root, ["config", "user.email", "fixture@example.invalid"])
    run_git(root, ["config", "commit.gpgsign", "false"])
    with open(os.path.join(root, "probe.py"), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write("value = 1\n")
    with open(os.path.join(root, "guard.v"), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write("(* probe comment face *)\nDefinition probe := 1.\n")
    with open(os.path.join(root, AUTONOMY_NAME), "w", encoding="utf-8",
              newline="\n") as handle:
        json.dump(autonomy, handle)
    run_git(root, ["add", "-A"])
    run_git(root, ["commit", "-q", "-F", "-"], stdin_text="base\n")
    return root


def _good_gate():
    """A gate command that exits 0 (fixture stand-in for the repo gate)."""
    return [sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.exit(0)"]


def _red_gate():
    """A gate command that exits 7 (fixture stand-in for a red gate)."""
    return [sys.executable, "-I", "-X", "utf8", "-c", "import sys; sys.exit(7)"]


def _base_cfg(**overrides):
    """Fixture gear config with the always-green gate."""
    cfg = {"mode": "auto", "admission_threshold": 0.8,
           "max_unreviewed_rounds": 12, "oscillation_alert": 2,
           "verify_cmd": _good_gate()}
    cfg.update(overrides)
    return cfg


def _rev(repo, args):
    return git_out(repo, args, "fixture git call").strip()


def _commit_ok(root, classes, files, extra=()):
    return run_cli(["commit", "--classes", classes, "--files", files,
                    "--repo-root", root] + list(extra))


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")


def selftest():
    """Fixture vectors; prints the PASS mark and exits 0 on green."""
    fails = []
    skips = []
    # V18 instrument: an audit hook records network-attempt events for the
    # whole selftest run.  A module sitting in sys.modules is not network
    # behavior, so the criterion observes attempts instead.
    net_events = []
    sys.addaudithook(
        lambda event, args: net_events.append(event)
        if event in NETWORK_ATTEMPT_EVENTS
        else None
    )
    tmp = tempfile.mkdtemp(prefix="auto_round_selftest_")

    def check(name, cond, detail=""):
        if not cond:
            fails.append("%s: %s" % (name, detail or "assertion red"))

    try:
        # V01 gear config: defaults when absent; strict validation.
        cfg = load_autonomy(os.path.join(tmp, "absent.json"))
        check("V01 defaults", cfg["mode"] == "auto"
              and cfg["admission_threshold"] == 0.8
              and cfg["max_unreviewed_rounds"] == 12
              and cfg["oscillation_alert"] == 2, str(cfg))
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write('{"mode": "yolo"}')
        try:
            load_autonomy(bad)
            check("V01 bad gear", False, "corrupt config accepted")
        except FailLoud as exc:
            check("V01 bad gear", exc.code == 9, "code=%d" % exc.code)

        # V01b verify_kind derivation: the default gate maps to norm_lint,
        # the axiom swap maps to axiom_guard, inline gates stay custom.
        check("V01b kinds", verify_kind_of(DEFAULT_VERIFY_CMD) == "norm_lint"
              and verify_kind_of(["py", "-I", "-X", "utf8",
                                  "tools/axiom_guard.py", "--repo", "."])
              == "axiom_guard"
              and verify_kind_of(_good_gate()) == "custom"
              and verify_kind_of([]) == "custom", "derivation drifted")

        # V02 admission truth table: one code path, gear picks adjudicator.
        d1, b1 = admission_decision("auto", "new", 0.85, 0.8, set())
        check("V02 auto above", (d1, "threshold" in b1) == ("admitted", True),
              "%s %s" % (d1, b1))
        d2, _ = admission_decision("auto", "new", 0.5, 0.8, set())
        check("V02 auto below", d2 == "pending", d2)
        d3, _ = admission_decision("auto", "new", None, 0.8, set())
        check("V02 auto no-grade", d3 == "pending", d3)
        d4, b4 = admission_decision("gated", "new", 0.99, 0.8, set())
        check("V02 gated new", d4 == "pending" and "gated" in b4,
              "%s %s" % (d4, b4))
        d5, _ = admission_decision("gated", "known", None, 0.8, {"known"})
        check("V02 gated known", d5 == "existing", d5)

        # V03 ledger row validation: shape damage fails loud.
        path = os.path.join(tmp, "rows.jsonl")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"round_id": 1}\n')
        try:
            load_rounds(path)
            check("V03 short row", False, "short row accepted")
        except FailLoud as exc:
            check("V03 short row", exc.code == 9, "code=%d" % exc.code)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("not-json{\n")
        try:
            load_rounds(path)
            check("V03 bad json", False, "garbage accepted")
        except FailLoud as exc:
            check("V03 bad json", exc.code == 9, "code=%d" % exc.code)
        check("V03 absent ledger", load_rounds(
            os.path.join(tmp, "none.jsonl")) is None, "absent not None")

        # V03 additive verify_kind: legacy ten-key rows stay valid, a bad
        # token fails loud, and the eleven-key shape loads.
        legacy_row = {"round_id": 1, "mode": "auto", "base_sha": "b",
                      "head_sha": "h", "classes_applied": [],
                      "admissions": [], "files": ["f.py"], "verify_rc": 0,
                      "oscillation_count": 0,
                      "timestamp_utc": "2026-01-01T00:00:00Z"}
        legacy = os.path.join(tmp, "legacy.jsonl")
        with open(legacy, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(legacy_row, sort_keys=True) + "\n")
        old_rows = load_rounds(legacy)
        check("V03 legacy ten keys", old_rows is not None
              and len(old_rows) == 1 and "verify_kind" not in old_rows[0]
              and set(old_rows[0]) == set(ROW_KEYS_LEGACY),
              "legacy row rejected")
        badkind = os.path.join(tmp, "badkind.jsonl")
        with open(badkind, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(legacy_row, verify_kind=""),
                                    sort_keys=True) + "\n")
        try:
            load_rounds(badkind)
            check("V03 bad verify_kind", False, "empty token accepted")
        except FailLoud as exc:
            check("V03 bad verify_kind", exc.code == 9, "code=%d" % exc.code)
        eleven = os.path.join(tmp, "eleven.jsonl")
        with open(eleven, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(legacy_row,
                                         verify_kind="axiom_guard"),
                                    sort_keys=True) + "\n")
        new_rows = load_rounds(eleven)
        check("V03 eleven-key row", new_rows is not None
              and new_rows[0]["verify_kind"] == "axiom_guard",
              "eleven-key row rejected")

        if not shutil.which("git"):
            skips.append("git executable not found; repo vectors not run")
        else:
            selftest_repo_vectors(tmp, check)

        # V18 zero network: observed attempts, not module presence.  The
        # audit hook installed at selftest start recorded every
        # socket.connect and urllib.Request event; any recorded event is
        # a red.  The source scan tokens are assembled at run time so
        # this vector never trips over its own source literals.
        check("V18 no network attempt", not net_events, str(net_events))
        with open(__file__, "r", encoding="utf-8") as handle:
            source = handle.read()
        for mod in ("socket", "urllib", "ftplib", "smtplib", "http.client"):
            joined = "import " + mod
            check("V18 source scan %s" % mod, joined not in source,
                  "token present")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for line in skips:
        sys.stderr.write("SELFTEST SKIP %s\n" % line)
    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (18 vectors)\n" % SELFTEST_MARK)
    return 0


def selftest_repo_vectors(tmp, check):
    """Vectors that need a git executable; each uses a throwaway repo."""

    def write(root, rel, text):
        with open(os.path.join(root, rel), "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(text)

    def rows_of(root):
        rows = load_rounds(os.path.join(root, "docs", LEDGER_NAME))
        return rows or []

    # V04 round commit: ledger row, trailers, lightweight ref, idempotent
    # rerun as a loud nothing-to-do.
    root = _mkrepo(tmp, "v04", _base_cfg())
    base = _rev(root, ["rev-parse", "HEAD"])
    write(root, "probe.py", "value = 2\n")
    rc, out, _ = _commit_ok(root, "date-strip", "probe.py")
    check("V04 rc", rc == 0, out)
    rows = rows_of(root)
    check("V04 one row", len(rows) == 1, str(len(rows)))
    row = rows[0]
    check("V04 row keys", set(row) == set(ROW_KEYS), str(sorted(row)))
    check("V04 verify kind", row.get("verify_kind") == "custom",
          str(row.get("verify_kind")))
    check("V04 fields", row["mode"] == "auto" and row["verify_rc"] == 0
          and row["files"] == ["probe.py"]
          and row["classes_applied"] == ["date-strip"]
          and row["oscillation_count"] == 0
          and row["base_sha"] == base
          and row["head_sha"] == _rev(root, ["rev-parse", "HEAD"]),
          str(row))
    body = _rev(root, ["log", "-1", "--format=%B"])
    check("V04 trailers", "Rocqwash-Round: 1" in body
          and "Rocqwash-Mode: auto" in body, body)
    check("V04 round ref",
          _rev(root, ["for-each-ref", "--format=%(objectname)",
                      "%s/1" % ROUND_REF_ROOT]) == row["head_sha"],
          "ref mismatch")
    head_before = _rev(root, ["rev-parse", "HEAD"])
    rc, out, _ = _commit_ok(root, "date-strip", "probe.py")
    check("V04 rerun skip", rc == 0 and "nothing-to-commit" in out, out)
    check("V04 rerun silent", len(rows_of(root)) == 1
          and _rev(root, ["rev-parse", "HEAD"]) == head_before,
          "rerun wrote")

    # V05 gated gear: pending refusal, approve, same path then commits.
    root = _mkrepo(tmp, "v05", _base_cfg(mode="gated"))
    write(root, "probe.py", "value = gated\n")
    rc, _, err = _commit_ok(root, "vocab-swap", "probe.py")
    check("V05 pending refusal", rc == 1 and "pending" in err,
          "%d %s" % (rc, err))
    rc, out, _ = run_cli(["approve", "--class", "vocab-swap",
                          "--repo-root", root])
    check("V05 approve", rc == 0 and "approved" in out, out)
    rc, out, _ = _commit_ok(root, "vocab-swap", "probe.py")
    check("V05 commit after approve", rc == 0, out)
    rows = rows_of(root)
    check("V05 gated row", rows[0]["mode"] == "gated"
          and rows[0]["admissions"] == [], str(rows))
    body = _rev(root, ["log", "-1", "--format=%B"])
    check("V05 trailer gated", "Rocqwash-Mode: gated" in body, body)
    state = load_state(os.path.join(root, "docs", STATE_NAME))
    check("V05 approval table",
          state["admitted_classes"][0]["class"] == "vocab-swap"
          and state["admitted_classes"][0]["basis"] == "human approval",
          str(state))

    # V06 auto self-admission: threshold grade records the basis.
    root = _mkrepo(tmp, "v06", _base_cfg())
    write(root, "probe.py", "value = align\n")
    rc, out, _ = _commit_ok(root, "term-align", "probe.py",
                            ["--class-confidence", "term-align=0.85"])
    check("V06 self-admit rc", rc == 0, out)
    rows = rows_of(root)
    check("V06 admission row", rows[0]["admissions"]
          and rows[0]["admissions"][0]["class"] == "term-align"
          and "gear auto" in rows[0]["admissions"][0]["basis"]
          and "threshold" in rows[0]["admissions"][0]["basis"], str(rows))
    write(root, "probe.py", "value = align2\n")
    rc, _, err = _commit_ok(root, "lowball", "probe.py",
                            ["--class-confidence", "lowball=0.5"])
    check("V06 below threshold", rc == 1 and "pending" in err,
          "%d %s" % (rc, err))
    rc, _, err = _commit_ok(root, "no-grade", "probe.py")
    check("V06 no grade", rc == 1 and "pending" in err, "%d %s" % (rc, err))

    # V07 soft stop at the cap; --continue is the explicit override.
    root = _mkrepo(tmp, "v07", _base_cfg(max_unreviewed_rounds=1))
    write(root, "probe.py", "value = s1\n")
    rc, _, _ = _commit_ok(root, "date-strip", "probe.py")
    check("V07 round one", rc == 0, "first round refused")
    write(root, "probe.py", "value = s2\n")
    rc, _, err = _commit_ok(root, "date-strip", "probe.py")
    check("V07 soft stop", rc == 1 and "soft stop" in err, "%d %s"
          % (rc, err))
    rc, _, _ = _commit_ok(root, "date-strip", "probe.py", ["--continue"])
    check("V07 continue override", rc == 0, "continue still refused")

    # V08 oscillation alert at the configured repeat count.
    root = _mkrepo(tmp, "v08", _base_cfg(oscillation_alert=2))
    hits = os.path.join(root, "hits.json")
    _write_json(hits, [{"file": "probe.py", "line": 2}])
    write(root, "probe.py", "value = o1\n")
    rc, _, _ = _commit_ok(root, "date-strip", "probe.py", ["--hits", hits])
    check("V08 first touch", rc == 0, "round with hits refused")
    write(root, "probe.py", "value = o2\n")
    rc, out, _ = _commit_ok(root, "date-strip", "probe.py", ["--hits", hits])
    check("V08 alert line", rc == 0 and "oscillation-alert" in out, out)
    rows = rows_of(root)
    check("V08 row count", rows[1]["oscillation_count"] == 1, str(rows[1]))
    state = load_state(os.path.join(root, "docs", STATE_NAME))
    check("V08 site count", state["line_hits"].get("probe.py:2") == 2,
          str(state))

    # V09 rollback: archive ref first, one revert commit, drift kept.
    root = _mkrepo(tmp, "v09", _base_cfg())
    base = _rev(root, ["rev-parse", "HEAD"])
    rc, out, _ = run_cli(["anchor", "--set", base, "--repo-root", root])
    check("V09 anchor set", rc == 0 and "anchor set" in out, out)
    write(root, "probe.py", "value = d1\n")
    rc, _, _ = _commit_ok(root, "date-strip", "probe.py")
    check("V09 drift r1", rc == 0, "round 1 refused")
    write(root, "probe.py", "value = d2\n")
    rc, _, _ = _commit_ok(root, "admission-vocab", "probe.py")
    check("V09 drift r2", rc == 0, "round 2 refused")
    rc, out, _ = run_cli(["rollback", "--repo-root", root])
    check("V09 rollback rc", rc == 0 and "rollback round=3" in out, out)
    drift_ref = ""
    for line in out.splitlines():
        if line.startswith("rollback "):
            drift_ref = line.split("drift-ref=", 1)[1].split()[0]
    check("V09 drift ref named", drift_ref.startswith(DRIFT_REF_ROOT + "/"),
          drift_ref)
    check("V09 drift ref exists", ref_exists(root, drift_ref), drift_ref)
    check("V09 tree back at anchor",
          _rev(root, ["diff", "--name-only", base, "HEAD"]) == "",
          "tree not restored")
    body = _rev(root, ["log", "-1", "--format=%B"])
    check("V09 revert trailers", "Rocqwash-Mode: rollback" in body, body)
    rows = rows_of(root)
    check("V09 rollback row", rows[2]["mode"] == "rollback"
          and rows[2]["files"] == ["probe.py"]
          and rows[2]["base_sha"] and rows[2]["head_sha"], str(rows[2]))
    check("V09 round ref 3",
          _rev(root, ["for-each-ref", "--format=%(objectname)",
                      "%s/3" % ROUND_REF_ROOT]) == rows[2]["head_sha"],
          "ref mismatch")
    rc, out, _ = run_cli(["rollback", "--repo-root", root])
    check("V09 rerun skip", rc == 0 and "nothing-to-roll-back" in out, out)

    # V10 salvage round trip: emit, rejects, refined merge as one commit.
    pkg = os.path.join(root, "pkg.jsonl")
    rc, out, _ = run_cli(["salvage", "--from", drift_ref, "--emit", pkg,
                          "--repo-root", root])
    check("V10 emit rc", rc == 0 and "salvage package rows=" in out, out)
    package = _load_package(pkg, check)
    check("V10 package shape", bool(package), "empty package")
    refined_path = os.path.join(root, "refined.jsonl")
    tree_before = _rev(root, ["rev-parse", "HEAD"])
    _write_rejections(root, package, refined_path, check)
    check("V10 rejects wrote nothing",
          _rev(root, ["rev-parse", "HEAD"]) == tree_before, "tree moved")
    refined = []
    for item in package:
        refined.append({"hunk_id": item["hunk_id"],
                        "round_id": item["round_id"],
                        "class": item["class"], "file": item["file"],
                        "before": item["before"],
                        "after": item["after"] + " refined-mark",
                        "refined_by": "fixture-reviewer"})
    with open(refined_path, "w", encoding="utf-8", newline="\n") as handle:
        for row in refined:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    rc, out, _ = run_cli(["merge-salvage", refined_path, "--repo-root", root])
    check("V10 merge rc", rc == 0 and "salvage-merged round=4" in out, out)
    with open(os.path.join(root, "probe.py"), "r", encoding="utf-8") as fh:
        merged = fh.read()
    check("V10 merged text", "refined-mark" in merged, merged)
    body = _rev(root, ["log", "-1", "--format=%B"])
    check("V10 salvage trailers", "Rocqwash-Mode: salvage" in body
          and "Rocqwash-Salvage-Of:" in body, body)
    rows = rows_of(root)
    check("V10 salvage row", rows[3]["mode"] == "salvage", str(rows[3]))
    check("V10 drift kept", ref_exists(root, drift_ref), drift_ref)
    check("V10 one commit",
          len(_rev(root, ["rev-list", "%s..HEAD" % base]).splitlines()) == 4,
          "not a single merge commit")
    # anchor-face consistency: the merged hunks no longer match the tree,
    # so a rerun of the same refined package must refuse loudly.
    rc, _, err = run_cli(["merge-salvage", refined_path, "--repo-root", root])
    check("V10 tree guard", rc == 9 and "before text not found" in err,
          "%d %s" % (rc, err))
    second = os.path.join(root, "pkg2.jsonl")
    rc, _, _ = run_cli(["salvage", "--from", drift_ref, "--emit", second,
                        "--repo-root", root])
    with open(pkg, "rb") as fh:
        first_bytes = fh.read()
    with open(second, "rb") as fh:
        second_bytes = fh.read()
    check("V10 emit deterministic", first_bytes == second_bytes,
          "re-emit differs")

    # V11 corrupt ledger: commit and log fail loud rc=9.
    root = _mkrepo(tmp, "v11", _base_cfg())
    write(root, "probe.py", "value = c1\n")
    rc, _, _ = _commit_ok(root, "date-strip", "probe.py")
    check("V11 seed round", rc == 0, "seed round failed")
    ledger = os.path.join(root, "docs", LEDGER_NAME)
    with open(ledger, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("not-json{\n")
    write(root, "probe.py", "value = c2\n")
    rc, _, err = _commit_ok(root, "date-strip", "probe.py")
    check("V11 commit corrupt", rc == 9, "%d %s" % (rc, err))
    rc, _, err = run_cli(["log", "--repo-root", root])
    check("V11 log corrupt", rc == 9, "%d %s" % (rc, err))

    # V12 certification-face scope: .v rides comment-safe classes only.
    root = _mkrepo(tmp, "v12", _base_cfg(mode="gated"))
    run_cli(["approve", "--class", "vocab-swap", "--repo-root", root])
    rc, _, err = run_cli(["commit", "--classes", "vocab-swap", "--files",
                          "guard.v", "--repo-root", root])
    check("V12 scope refusal", rc == 1 and "certification-face" in err,
          "%d %s" % (rc, err))
    rc, _, _ = run_cli(["commit", "--classes", "jargon-replace", "--files",
                        "guard.v", "--repo-root", root])
    check("V12 safe class ok", rc == 0, "comment-safe class refused")

    # V13 query faces: status fresh and loaded, list, log, absent rc=9.
    root = _mkrepo(tmp, "v13", _base_cfg())
    rc, out, _ = run_cli(["status", "--repo-root", root])
    check("V13 status fresh", rc == 0 and "rounds=0" in out
          and "ledger=absent" in out, out)
    rc, _, err = run_cli(["list", "--repo-root", root])
    check("V13 list absent", rc == 9, "%d %s" % (rc, err))
    rc, _, err = run_cli(["log", "--repo-root", root])
    check("V13 log absent", rc == 9, "%d %s" % (rc, err))
    write(root, "probe.py", "value = q1\n")
    _commit_ok(root, "date-strip", "probe.py")
    rc, out, _ = run_cli(["status", "--repo-root", root])
    check("V13 status loaded", rc == 0 and "rounds=1" in out
          and "unreviewed=1/12" in out, out)
    rc, out, _ = run_cli(["list", "--repo-root", root])
    check("V13 list", rc == 0 and "round=1 mode=auto" in out, out)
    rc, out, _ = run_cli(["log", "--round", "1", "--repo-root", root])
    check("V13 log one", rc == 0 and '"round_id":1' in out, out)
    rc, _, err = run_cli(["log", "--round", "99", "--repo-root", root])
    check("V13 log zero match", rc == 0 and "not found" in err,
          "%d %s" % (rc, err))

    # V14 verify gate red: refusal, nothing committed, ledger untouched.
    root = _mkrepo(tmp, "v14", _base_cfg(verify_cmd=_red_gate()))
    head_before = _rev(root, ["rev-parse", "HEAD"])
    write(root, "probe.py", "value = r1\n")
    rc, _, err = _commit_ok(root, "date-strip", "probe.py")
    check("V14 gate red", rc == 1 and "verify gate red" in err,
          "%d %s" % (rc, err))
    check("V14 nothing landed", rows_of(root) == [], "ledger written")
    check("V14 head untouched",
          _rev(root, ["rev-parse", "HEAD"]) == head_before, "HEAD moved")

    # V15 exit-code spot checks through the real CLI process face.
    tool = os.path.abspath(__file__)
    for argv, want in ((["--bogus-flag"], 2),
                       (["commit", "--classes", "x"], 2),
                       ([], 2), (["no-such-command"], 2)):
        proc = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", tool] + argv,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, encoding="utf-8",
                              errors="replace")
        check("V15 usage %s" % " ".join(argv), proc.returncode == want,
              "rc=%d" % proc.returncode)


def _load_package(path, check):
    """Read the emitted offer package back for the vector assertions."""
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line:
                rows.append(json.loads(line))
    need = {"hunk_id", "round_id", "class", "file", "before", "after"}
    check("V10 package keys", all(set(r) == need for r in rows),
          str(rows[:1]))
    return rows


def _write_rejections(root, package, refined_path, check):
    """Three loud rejection vectors on the refined-package face."""
    item = package[0]
    cases = [
        {"hunk_id": item["hunk_id"], "before": "no-such-text",
         "after": "x", "refined_by": "fixture-reviewer"},
        {"hunk_id": item["hunk_id"], "before": item["before"],
         "after": "x", "refined_by": ""},
        {"hunk_id": "r999-nope-h1", "before": item["before"],
         "after": "x", "refined_by": "fixture-reviewer"},
    ]
    wants = ("no drift ref reproduces", "refined_by",
             "no drift ref reproduces")
    for idx, row in enumerate(cases):
        with open(refined_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(row, fh)
        rc, _, err = run_cli(["merge-salvage", refined_path, "--repo-root",
                              root])
        check("V10 reject %d" % idx, rc == 9 and wants[idx] in err,
              "%d %s" % (rc, err))


def build_parser():
    """CLI surface; usage errors exit 2 through argparse."""
    parser = argparse.ArgumentParser(
        prog="auto_round.py",
        description="Auto round ledger, admission, rollback and salvage "
                    "port (schema rocqwash-round/1, gears auto and gated).")
    parser.add_argument("--selftest", action="store_true",
                        help="run the fixture vector group")
    parser.add_argument("command", nargs="?", choices=(
        "commit", "approve", "anchor", "rollback", "salvage",
        "merge-salvage", "status", "list", "log"),
        help="round face to run")
    parser.add_argument("--repo-root", default="", dest="repo_root",
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--autonomy", default="",
                        help="gear config path (default: <root>/"
                             "autonomy.json)")
    parser.add_argument("--state", default="",
                        help="state path (default: <root>/docs/"
                             "round-state.json)")
    parser.add_argument("--ledger", default="",
                        help="ledger path (default: <root>/docs/"
                             "round-ledger.jsonl)")
    parser.add_argument("--classes", default="",
                        help="commit: comma-separated rewrite class names")
    parser.add_argument("--files", default="",
                        help="commit: comma-separated repo-relative files")
    parser.add_argument("--hits", default="",
                        help="commit: JSON file of {file, line} touch sites")
    parser.add_argument("--class-confidence", action="append", default=[],
                        dest="class_confidence", metavar="NAME=VALUE",
                        help="commit: confidence grade for a new class")
    parser.add_argument("--message", default="",
                        help="commit/merge: first line of the commit message")
    parser.add_argument("--continue", action="store_true",
                        dest="force_continue",
                        help="commit: explicit one-shot past the soft stop")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="commit: validate and report, write nothing")
    parser.add_argument("--class", default="", dest="cls",
                        help="approve: class name to admit")
    parser.add_argument("--confidence", type=float, default=None,
                        help="approve: optional confidence grade")
    parser.add_argument("--note", default="",
                        help="approve: basis note for the admission record")
    parser.add_argument("--set", default="", dest="set_sha",
                        help="anchor: set the anchor to this revision")
    parser.add_argument("--promote", action="store_true",
                        help="anchor: promote the anchor to current HEAD")
    parser.add_argument("--to", default="", dest="to_ref",
                        help="rollback: anchor | SHA | round:N "
                             "(default: the recorded anchor)")
    parser.add_argument("--from", default="", dest="from_ref",
                        help="salvage/merge: drift/<id> source ref")
    parser.add_argument("--emit", default="",
                        help="salvage: offer package output path")
    parser.add_argument("refined", nargs="?", default="",
                        help="merge-salvage: refined package path")
    parser.add_argument("--limit", type=int, default=None,
                        help="list: cap the printed rounds (tail)")
    parser.add_argument("--round", type=int, default=None, dest="round_no",
                        help="log: fetch one round row")
    return parser


COMMANDS = {
    "commit": cmd_commit,
    "approve": cmd_approve,
    "anchor": cmd_anchor,
    "rollback": cmd_rollback,
    "salvage": cmd_salvage,
    "merge-salvage": cmd_merge_salvage,
    "status": cmd_status,
    "list": cmd_list,
    "log": cmd_log,
}


def main(argv=None):
    """CLI entry; FailLoud carries its exit code to the process face."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.command:
            parser.error("--selftest takes no subcommand")
        return selftest()
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_usage(sys.stderr)
        sys.stderr.write("auto_round: a command is required: %s\n"
                         % "|".join(COMMANDS))
        return 2
    if handler is cmd_approve and not args.cls:
        parser.error("approve requires --class")
    if handler is cmd_commit and (not args.classes or not args.files):
        parser.error("commit requires --classes and --files")
    if handler is cmd_salvage:
        if not args.from_ref:
            parser.error("salvage requires --from drift/<id>")
        if not args.emit:
            parser.error("salvage requires --emit OUT.jsonl")
    if handler is cmd_merge_salvage and not args.refined:
        parser.error("merge-salvage requires a refined package path")
    try:
        return handler(args)
    except FailLoud as exc:
        sys.stderr.write("auto_round %s: %s\n" % (args.command, exc))
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
