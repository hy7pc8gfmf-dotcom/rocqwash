#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_ratchet.py - the nine-metric capability ratchet (tools/).
Purpose.  Keep capability as an append-only series of readings that only
  rolls forward.  Nine frozen metrics - four capability-carrier faces
  (triage_classes, regression_vectors, taxonomy_rows, cure_patterns) and
  five mechanism faces (mcp_roster, selftest_vectors, repair_action_rate,
  b_gate_ready_classes, calibration_agreement_rate) - are re-derived at
  every run from their source accounts, never hand-filled; every reading
  carries {metric, family, value, basis, window {from_sha, to_sha},
  source}.  calibration_agreement_rate is null while the calibration
  ledger has zero entries (unmeasured is null, never 0).
Interface.  `python -I -B tools/capability_ratchet.py [--repo DIR]
  [--measure [--json [PATH]]] [--gate --baseline FILE] [--compare FILE]
  [--append FILE [--allow-dirty-anchor]] [--from-sha SHA] [--selftest]`.
Dependencies.  Python 3 stdlib only; two owning tools spawned read-only for
  their stdout faces (mcp_server --selftest, test_tool_selftests), two
  imported in-process (learning_feedback, b_gate_audit); local `git` anchors
  the window; zero network.
Evidence.  --selftest: an offline vector group on canned sources and private
  temporary ledgers; its last stdout line is exactly `selftest: <n>
  vector(s), <k> FAIL`; negative controls cover a hand-edited reading, a
  deleted historical line, and a drifted ledger head.
Exit-codes.  0 green (measure, gate at-or-above, compare equal, append
  landed, selftest pass); 1 red (gate regression, compare mismatch); 2 usage,
  shape, IO, or environment fault - fail loud, no advisory downgrade.
"""

# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget).
#
# Reading set.  The frozen nine split into two evolution families: strength
# = triage_classes, regression_vectors, taxonomy_rows, cure_patterns,
# mcp_roster, selftest_vectors; gap-fill = repair_action_rate,
# b_gate_ready_classes, calibration_agreement_rate.  The gate judges per
# metric, so both families hold their line and no family average can hide
# a single drop.
#
# Source accounts (read-only, never hand-filled).  Four counts read JSON
# data files and one fixture directory in place.  mcp_roster and
# selftest_vectors spawn the owning tools for their stdout faces
# (`mcp_server.py --selftest`, `tests/test_tool_selftests.py`).  The two
# learning_feedback lines and the b_gate_audit line are rendered
# in-process through the owning tools' own summarize / print_summary faces
# - the same text their default runs print - so a derivation never
# rewrites the two tracked reports those default runs write
# (docs/scheduling-feedback.json, docs/b-gate-audit.json).  The external
# recompute card reproduces every reading with the owning tools' own
# command lines.
#
# Window anchor and tree state.  window.to_sha is HEAD at the run
# (`git rev-parse HEAD`; a non-repo fails loud, never a synthetic sha);
# from_sha is --from-sha, else to_sha (append: the head line's to_sha).
# Readings come from the working tree, so every snapshot also carries
# tree_state {dirty, changed_paths, scope}: the `git status --porcelain
# -uall` count under the source paths.  A non-clean tree means the readings are
# reproducible at the anchor only once those paths are committed.  measure,
# gate, and compare disclose this on stderr and still run; --append refuses
# it unless --allow-dirty-anchor is given (the line is then recorded as
# provisional).
#
# Ledger.  docs/capability-ratchet.jsonl is append-only; each line is one
# snapshot plus {seq, prev_digest, digest}, sha256 over the canonical
# snapshot bytes, chained to the predecessor.  Every load validates the
# whole chain: a deleted line breaks prev_digest, a hand-edited field
# breaks its own digest.  --append writes exactly one line and is the only
# writing mode; history is never rewritten (the only legal baseline move is
# forward).  The append face stays CLI-side (not exposed over MCP).
#
# Modes.  --measure prints one line per metric plus a summary; --json bare
# prints exactly one JSON object on stdout, --json PATH writes that object
# to the caller-named path.  --gate --baseline FILE judges fresh readings
# against one baseline snapshot: strictly below is rc 1, flat or above rc 0
# (an unmeasured null against a measured number reads as a drop, the
# reverse as a first measurement); the baseline file may be a plain
# snapshot object or the ledger itself (the head line anchors).
# --compare FILE validates the ledger chain first, then requires fresh
# value equality with the head line (rc 1 on any mismatch).  Together with
# --measure the readings print first and the compare verdict decides the
# exit code (the external recompute card form).  --baseline accepts any
# numeric value because the acceptance direction test inflates baseline
# values uniformly; range plausibility of the two rate metrics is enforced
# on the fresh side.
#
# Flag shape.  --selftest takes no other flag; --append, --gate, and the
# measure/compare pair are mutually exclusive; --json needs --measure and
# takes no --compare (the JSON face stays a single object); --baseline is
# read only by --gate; --allow-dirty-anchor only by --append.  An IO fault
# on a caller-named path (missing file, a directory in place of a file, an
# unwritable target) is rc 2, never a traceback and never rc 1: rc 1 is
# reserved for a real red.

import argparse
import contextlib
import datetime
import hashlib
import importlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash-capability-ratchet/1"

# The frozen nine: metric name -> evolution family.  The family is the tag
# every reading carries (strength = an evidenced capability made thicker,
# gap-fill = an absent capability brought into being); the gate is per
# metric, so the family split keeps both evolution lines honest without
# weakening the wall.
STRENGTH = "strength"
GAP_FILL = "gap-fill"
METRIC_FAMILIES = {
    "triage_classes": STRENGTH,
    "regression_vectors": STRENGTH,
    "taxonomy_rows": STRENGTH,
    "cure_patterns": STRENGTH,
    "mcp_roster": STRENGTH,
    "selftest_vectors": STRENGTH,
    "repair_action_rate": GAP_FILL,
    "b_gate_ready_classes": GAP_FILL,
    "calibration_agreement_rate": GAP_FILL,
}

# The two readings that are shares of a unit: a fresh value outside [0, 1]
# is a derivation fault, never a reading.
RATE_METRICS = ("repair_action_rate", "calibration_agreement_rate")
RATE_EPSILON = 1e-9

# The standing ledgers the in-process source faces read (repo-relative).
ROUND_LEDGER = ("docs", "round-ledger.jsonl")
ROUND_STATE = ("docs", "round-state.json")
EXP_LEDGER = ("docs", "exp-ledger.jsonl")
TAXONOMY = ("tools", "taxonomy.json")

# The paths every reading is derived from: a working tree that differs from
# HEAD under any of them does not exist at the window anchor yet.
SOURCE_PATHSPECS = (
    "tools", "tests", "wash/cure_pack.json", "docs/ci-triage-table.json",
    "docs/round-ledger.jsonl", "docs/round-state.json",
    "docs/exp-ledger.jsonl",
)

TREE_STATE_KEYS = {"dirty", "changed_paths", "scope"}

GENESIS_PREV_DIGEST = "genesis"

# ---- per-source parsers (pure functions; the selftest feeds them canned
# lines so the frozen vectors stay deterministic and repository-write-free) ----

ROSTER_RX = re.compile(r"roster (\d+) specs")
META_SUMMARY_RX = re.compile(r"\[SUMMARY\] pass=(\d+) skip=(\d+) exempt=(\d+)"
                             r" fail=(\d+) total=(\d+)")
REPAIR_RX = re.compile(r"repair_action_rate=([0-9.]+)")
CALIBRATION_RX = re.compile(r"calibration: ledger_present=(\w+) entries=(\d+)"
                            r" agreement_rate=(None|[0-9.]+)")
READY_RX = re.compile(r"ready classes: (\d+) of (\d+) needed")

SHA_RX = re.compile(r"\A[0-9a-f]{40}\Z")


def parse_roster(stdout):
    """mcp_server --selftest stdout -> int spec count; None when absent."""
    m = ROSTER_RX.search(stdout)
    return int(m.group(1)) if m else None


def parse_meta_pass(stdout):
    """test_tool_selftests stdout -> int green selftest faces (the SUMMARY
    pass field); None when the SUMMARY line never appeared."""
    m = META_SUMMARY_RX.search(stdout)
    return int(m.group(1)) if m else None


def parse_repair_rate(stdout):
    """learning_feedback stdout -> float repair_action_rate; None absent."""
    m = REPAIR_RX.search(stdout)
    return float(m.group(1)) if m else None


def parse_calibration(stdout):
    """learning_feedback stdout -> (agreement_rate, entries).  Zero entries
    or an explicit None both map to None: unmeasured is null, never 0."""
    m = CALIBRATION_RX.search(stdout)
    if not m:
        return None, None
    entries = int(m.group(2))
    token = m.group(3)
    if entries == 0 or token == "None":
        return None, entries
    return float(token), entries


def parse_ready_classes(stdout):
    """b_gate_audit stdout -> int ready classes; None when absent."""
    m = READY_RX.search(stdout)
    return int(m.group(1)) if m else None


def rate_fault(metric, value):
    """Fresh-side range rule: None when the reading is admissible, else the
    fault text.  Only the two rate metrics are range-bound; null is the
    unmeasured reading and is admissible."""
    if metric not in RATE_METRICS or value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "%s value is not a number: %r" % (metric, value)
    if value < -RATE_EPSILON or value > 1 + RATE_EPSILON:
        return ("%s value %r is a share of a unit and lies outside [0, 1]"
                % (metric, value))
    return None


# ---- window anchor and tree state ----

def head_sha(repo):
    """The repository window anchor; a fault here is loud, never synthetic."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except OSError as exc:
        raise ShapeError("window anchor unavailable (git spawn failed): %s"
                         % exc)
    if proc.returncode != 0:
        raise ShapeError("window anchor unavailable (git rev-parse rc %d in"
                         " %s)" % (proc.returncode, repo))
    sha = proc.stdout.decode("utf-8", errors="replace").strip()
    if not SHA_RX.match(sha):
        raise ShapeError("window anchor is not a 40-hex commit sha: %r" % sha)
    return sha


def count_changed(porcelain_text):
    """Number of changed paths in one `git status --porcelain -uall`
    listing (one line per path; blank lines carry no path; -uall lists an
    untracked directory file by file, so the count is per path)."""
    return len([line for line in porcelain_text.splitlines() if line.strip()])


def state_from_porcelain(porcelain_text):
    """The tree_state record of one `git status --porcelain -uall` listing."""
    changed = count_changed(porcelain_text)
    return {"dirty": changed > 0, "changed_paths": changed,
            "scope": "git status --porcelain -uall -- "
                     + " ".join(SOURCE_PATHSPECS)}


def tree_state(repo):
    """Working-tree state under the source paths, relative to HEAD.  The
    readings are taken from the working tree while the window anchor is
    HEAD, so a non-clean tree is disclosed here, never guessed away."""
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain", "-uall",
             "--"] + list(SOURCE_PATHSPECS), cwd=repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except OSError as exc:
        raise ShapeError("tree state unavailable (git spawn failed): %s" % exc)
    except subprocess.TimeoutExpired:
        raise ShapeError("tree state unavailable (git status timed out in %s)"
                         % repo)
    if proc.returncode != 0:
        raise ShapeError("tree state unavailable (git status rc %d in %s)"
                         % (proc.returncode, repo))
    return state_from_porcelain(
        proc.stdout.decode("utf-8", errors="replace"))


# ---- source derivations (read-only toward every source account) ----

class ShapeError(Exception):
    """A source, ledger, or snapshot shape fault (fail loud, rc 2)."""


def _spawn(repo, args, timeout, isolated=True):
    """One read-only child face; captured stdout, never merged stderr.
    isolated=True matches the guide's recompute cards (`python -I tools/...`);
    the meta aggregation runs isolated=False (`python -B
    tests/test_tool_selftests.py`, its sanctioned invocation - under -I one
    of its own subprocess-driven parity vectors mis-resolves, and the card
    is the face of record)."""
    argv = [sys.executable] + (["-I"] if isolated else []) + ["-B"] + args
    try:
        proc = subprocess.run(
            argv, cwd=repo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except OSError as exc:
        raise ShapeError("source face spawn failed (%s): %s"
                         % (args[0], exc))
    except subprocess.TimeoutExpired:
        raise ShapeError("source face timed out after %ss: %s"
                         % (timeout, args[0]))
    if proc.returncode != 0:
        raise ShapeError("source face exited rc %d: %s (stderr: %s)"
                         % (proc.returncode, args[0],
                            proc.stderr.decode("utf-8", errors="replace")
                            .strip()[:200]))
    return proc.stdout.decode("utf-8", errors="replace")


def _sibling(name):
    """Import one owning tool module from this file's directory (isolated
    mode puts no script directory on sys.path)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        return importlib.import_module(name)
    except SystemExit as exc:
        raise ShapeError("sibling module %s refused to import (exit %r)"
                         % (name, exc.code))
    except ImportError as exc:
        raise ShapeError("sibling module %s is required (%s)" % (name, exc))


def _learning_summary(repo):
    """The learning_feedback summary block rendered in-process: the text its
    default run prints, minus that run's one tracked write.  An account
    error is loud here exactly as it is on the tool's own rc 1."""
    module = _sibling("learning_feedback")
    try:
        face = module.build_face(os.path.join(repo, *ROUND_LEDGER),
                                 os.path.join(repo, *ROUND_STATE),
                                 os.path.join(repo, *EXP_LEDGER))
    except Exception as exc:
        raise ShapeError("learning_feedback face could not be cast (%s: %s)"
                         % (type(exc).__name__, exc))
    errors = (list(face["rounds"]["errors"])
              + list(face["repair_outcomes"]["errors"])
              + list(face["calibration"]["errors"]))
    if errors:
        raise ShapeError("learning_feedback face carries %d account error(s):"
                         " %s" % (len(errors), errors[0]))
    return module.summarize(face, "/".join(module.OUT_DEFAULT))


def _b_gate_summary(repo):
    """The b_gate_audit summary rendered in-process (its print_summary face
    captured), minus that run's one tracked write."""
    module = _sibling("b_gate_audit")
    try:
        report, _ = module.build_report(
            os.path.join(repo, *ROUND_LEDGER),
            os.path.join(repo, *ROUND_STATE),
            os.path.join(repo, *TAXONOMY))
    except Exception as exc:
        raise ShapeError("b_gate_audit face could not be built (%s: %s)"
                         % (type(exc).__name__, exc))
    if report["errors"]:
        raise ShapeError("b_gate_audit face carries %d read error(s): %s"
                         % (len(report["errors"]), report["errors"][0]))
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.print_summary(report, "/".join(module.DEFAULT_OUT))
    return buffer.getvalue()


def _json_count(path, key):
    """Element count of one JSON object member; absent file or member is a
    loud fault (a blind metric never reads as zero)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise ShapeError("source file unreadable (%s): %s" % (path, exc))
    except ValueError as exc:
        raise ShapeError("source file is not valid JSON (%s): %s" % (path, exc))
    if not isinstance(data, dict) or key not in data \
            or not isinstance(data[key], list):
        raise ShapeError("source file %s lacks the %r object-member list"
                         % (path, key))
    return len(data[key])


def _fixture_count(directory, prefix):
    """Count the triage regression-vector fixtures (the selftest fixture set
    of tools/ci_triage.py).  A missing directory is a loud fault."""
    if not os.path.isdir(directory):
        raise ShapeError("fixture directory missing: %s" % directory)
    names = [n for n in os.listdir(directory)
             if n.startswith(prefix) and n.endswith(".json")]
    return len(names)


def derive_metrics(repo, from_sha, to_sha, state=None):
    """Fresh readings of the frozen nine, straight from the source accounts.

    Every reading carries its six fields (metric, family, value, basis,
    window, source); the per-source basis states the derivation caliber so
    a reading cannot be read under two calibers.  Source faces only read:
    two are spawned for their stdout, two are rendered in-process without
    their tracked writes.  state is a precomputed tree_state (the append
    face resolves it before deriving); None derives it here.
    """
    src = lambda *parts: os.path.join(repo, *parts)

    roster = parse_roster(_spawn(repo, [os.path.join("tools", "mcp_server.py"),
                                        "--selftest"], timeout=120))
    if roster is None:
        raise ShapeError("mcp_server --selftest carried no roster line")
    meta_pass = parse_meta_pass(_spawn(repo, [os.path.join("tests",
                                                           "test_tool_selftests.py")],
                                       timeout=300, isolated=False))
    if meta_pass is None:
        raise ShapeError("test_tool_selftests carried no [SUMMARY] line")
    feedback = _learning_summary(repo)
    repair = parse_repair_rate(feedback)
    if repair is None:
        raise ShapeError("learning_feedback carried no repair_action_rate")
    agree, entries = parse_calibration(feedback)
    if entries is None:
        raise ShapeError("learning_feedback carried no calibration line")
    ready = parse_ready_classes(_b_gate_summary(repo))
    if ready is None:
        raise ShapeError("b_gate_audit carried no ready-classes line")
    for metric, value in (("repair_action_rate", repair),
                          ("calibration_agreement_rate", agree)):
        fault = rate_fault(metric, value)
        if fault:
            raise ShapeError(fault)

    triage = _json_count(src("docs", "ci-triage-table.json"), "classes")
    vectors = _fixture_count(src("tests", "fixtures"), "ci_triage_")
    taxonomy = _json_count(src("tools", "taxonomy.json"), "rows")
    cure = _json_count(src("wash", "cure_pack.json"), "patterns")

    if state is None:
        state = tree_state(repo)
    window = {"from_sha": from_sha, "to_sha": to_sha}
    metrics = [
        _reading("triage_classes", triage, window,
                 "len(classes) of docs/ci-triage-table.json (the standing "
                 "CI failing-case classification table, one class per "
                 "marker family)",
                 "docs/ci-triage-table.json"),
        _reading("regression_vectors", vectors, window,
                 "count of tests/fixtures/ci_triage_*.json (the canned "
                 "failure-log fixture vectors tools/ci_triage.py --selftest "
                 "consumes; the fixture set is the regression thickness)",
                 "tests/fixtures/ci_triage_*.json"),
        _reading("taxonomy_rows", taxonomy, window,
                 "len(rows) of tools/taxonomy.json (the vacgen statement "
                 "taxonomy the recognition face classifies against)",
                 "tools/taxonomy.json"),
        _reading("cure_patterns", cure, window,
                 "len(patterns) of wash/cure_pack.json (the wash cure "
                 "pattern pack)",
                 "wash/cure_pack.json"),
        _reading("mcp_roster", roster, window,
                 "the roster count word of `mcp_server.py --selftest` "
                 "(TOOL_SPECS length, the frozen SELFTEST_ROSTER_COUNT "
                 "vector)",
                 "tools/mcp_server.py --selftest"),
        _reading("selftest_vectors", meta_pass, window,
                 "the [SUMMARY] pass field of tests/test_tool_selftests.py "
                 "(tool --selftest faces green under the per-tool 120s cap; "
                 "a red or vanished face drops this reading and trips the "
                 "gate; the count is environment-dependent - a face that "
                 "skips where its toolchain is absent is not green there)",
                 "tests/test_tool_selftests.py [SUMMARY]"),
        _reading("repair_action_rate", repair, window,
                 "the repair_action_rate token of the `learning_feedback.py` "
                 "summary line (repaired / (repaired + escalated + "
                 "watch_only + unrecorded) over the round repair ledger; "
                 "the summary is rendered in-process, so a derivation never "
                 "rewrites docs/scheduling-feedback.json)",
                 "tools/learning_feedback.py repair: line"),
        _reading("b_gate_ready_classes", ready, window,
                 "the ready-classes count of the `b_gate_audit.py` summary "
                 "(classes holding threshold instances and rounds; the "
                 "B-level admission gate's ignition gauge; the summary is "
                 "rendered in-process, so a derivation never rewrites "
                 "docs/b-gate-audit.json)",
                 "tools/b_gate_audit.py ready classes line"),
        _reading("calibration_agreement_rate", agree, window,
                 "the agreement_rate token of the `learning_feedback.py` "
                 "summary line (predicted-confidence x measured-rc pairing "
                 "over the calibration ledger); zero entries reads null = "
                 "unmeasured, never 0 (%d entries at this window)" % entries,
                 "tools/learning_feedback.py calibration: line"),
    ]
    return {
        "schema": SCHEMA,
        "ts": _utc_now(),
        "window": window,
        "tree_state": dict(state),
        "scan_face": ("read-only derivation of the nine metrics over their "
                      "source accounts: four counts read three JSON data "
                      "files and one fixture directory in place, two "
                      "owning-tool stdout faces are spawned (mcp_server "
                      "--selftest, test_tool_selftests [SUMMARY]), and two "
                      "owning-tool summaries are rendered in-process "
                      "(learning_feedback, b_gate_audit); zero bytes written "
                      "inside the repository"),
        "metrics": metrics,
    }


def _reading(metric, value, window, basis, source):
    """One reading: {metric, family, value, basis, window, source}."""
    return {
        "metric": metric,
        "family": METRIC_FAMILIES[metric],
        "value": value,
        "basis": basis,
        "window": dict(window),
        "source": source,
    }


def _utc_now():
    """UTC second-resolution ISO-8601 stamp (the readings-ledger ts face)."""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")


# ---- snapshot shape validation, digest, hash chain ----

READING_KEYS = {"metric", "family", "value", "basis", "window", "source"}


def validate_snapshot(snap):
    """Structural validation of one snapshot object; a ShapeError names the
    first fault.  The nine-name set and the per-reading six-key shape are
    frozen here - the same discipline as a roster freeze."""
    if not isinstance(snap, dict):
        raise ShapeError("snapshot is not a JSON object")
    if snap.get("schema") != SCHEMA:
        raise ShapeError("snapshot schema is %r, expected %r"
                         % (snap.get("schema"), SCHEMA))
    window = snap.get("window")
    if not _window_ok(window):
        raise ShapeError("snapshot window is not a {from_sha,to_sha} pair of "
                         "40-hex shas: %r" % (window,))
    if "tree_state" in snap and not _tree_state_ok(snap["tree_state"]):
        raise ShapeError("snapshot tree_state is not a {dirty, changed_paths,"
                         " scope} record with dirty == (changed_paths > 0):"
                         " %r" % (snap["tree_state"],))
    metrics = snap.get("metrics")
    if not isinstance(metrics, list) or len(metrics) != len(METRIC_FAMILIES):
        raise ShapeError("snapshot metrics must hold exactly the frozen nine,"
                         " found %r" % (len(metrics) if isinstance(metrics,
                                                                list)
                                        else metrics))
    seen = []
    for reading in metrics:
        if not isinstance(reading, dict) or set(reading) != READING_KEYS:
            raise ShapeError("reading keys are not exactly %s: %r"
                             % (sorted(READING_KEYS), sorted(reading)
                                if isinstance(reading, dict) else reading))
        metric = reading["metric"]
        if metric not in METRIC_FAMILIES:
            raise ShapeError("unknown metric name: %r" % (metric,))
        if metric in seen:
            raise ShapeError("duplicate metric reading: %r" % (metric,))
        seen.append(metric)
        if reading["family"] != METRIC_FAMILIES[metric]:
            raise ShapeError("metric %s carries family %r, the frozen family "
                             "is %r" % (metric, reading["family"],
                                        METRIC_FAMILIES[metric]))
        value = reading["value"]
        if value is not None and not isinstance(value, (int, float)) \
                or isinstance(value, bool):
            raise ShapeError("metric %s value is not a number or null: %r"
                             % (metric, value))
        # No range assertion on a stored value: the baseline loader must
        # accept any numeric value (the acceptance direction test inflates
        # baseline values uniformly); range plausibility of the two rate
        # metrics is enforced where readings are born (rate_fault).
        for key in ("basis", "source"):
            if not isinstance(reading[key], str) or not reading[key].strip():
                raise ShapeError("metric %s carries an empty %s (a reading "
                                 "without its caliber is a hand-fill)"
                                 % (metric, key))
        if not _window_ok(reading["window"]):
            raise ShapeError("metric %s window is not a sha pair: %r"
                             % (metric, reading["window"]))
    if set(seen) != set(METRIC_FAMILIES):
        raise ShapeError("metrics held %s, the frozen nine require %s"
                         % (sorted(seen), sorted(METRIC_FAMILIES)))
    return True


def _window_ok(window):
    return (isinstance(window, dict)
            and set(window) == {"from_sha", "to_sha"}
            and all(isinstance(window[k], str) and SHA_RX.match(window[k])
                    for k in ("from_sha", "to_sha")))


def _tree_state_ok(state):
    """A tree_state record is well formed when its keys are exactly the
    three, changed_paths is a non-negative plain int, and dirty is its
    truth (a zero count cannot be dirty, a non-zero count cannot be clean)."""
    return (isinstance(state, dict) and set(state) == TREE_STATE_KEYS
            and isinstance(state["dirty"], bool)
            and isinstance(state["changed_paths"], int)
            and not isinstance(state["changed_paths"], bool)
            and state["changed_paths"] >= 0
            and state["dirty"] == (state["changed_paths"] > 0)
            and isinstance(state["scope"], str) and state["scope"].strip())


def snapshot_digest(snap):
    """sha256 over the canonical snapshot bytes (every field but digest)."""
    body = {k: v for k, v in snap.items() if k != "digest"}
    blob = json.dumps(body, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def validate_ledger_line(line, expect_seq, expect_prev):
    """One chain-linked ledger line in; the chain contract out.  A line is
    the snapshot plus {seq, prev_digest, digest}; any fault is loud."""
    if not isinstance(line, dict):
        raise ShapeError("ledger line is not a JSON object")
    for key in ("seq", "prev_digest", "digest"):
        if key not in line:
            raise ShapeError("ledger line lacks the chain field %r" % (key,))
    if line["seq"] != expect_seq:
        raise ShapeError("ledger seq out of order: line carries %r, the "
                         "append-only chain expects %d (history was edited "
                         "or deleted)" % (line["seq"], expect_seq))
    if line["prev_digest"] != expect_prev:
        raise ShapeError("ledger chain broken at seq %d: prev_digest %r does "
                         "not match the predecessor digest %r (a historical "
                         "line was deleted or swapped)"
                         % (expect_seq, line["prev_digest"], expect_prev))
    digest = snapshot_digest(line)
    if digest != line["digest"]:
        raise ShapeError("ledger line seq %d fails its own digest (a field "
                         "was hand-edited): recorded %r, recomputed %r"
                         % (expect_seq, line["digest"], digest))
    validate_snapshot(line)
    return line


def load_ledger(path):
    """Whole-file chain validation; returns the validated lines in order.
    An empty or absent ledger is genesis-legal (returns [])."""
    if not os.path.isfile(path):
        return []
    lines = []
    expect_seq, expect_prev = 1, GENESIS_PREV_DIGEST
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    for no, raw_line in enumerate(raw.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            line = json.loads(stripped)
        except ValueError as exc:
            raise ShapeError("%s line %d is not valid JSON: %s"
                             % (path, no, exc))
        lines.append(validate_ledger_line(line, expect_seq, expect_prev))
        expect_seq += 1
        expect_prev = line["digest"]
    return lines


def _values(snap):
    """metric -> value map of a validated snapshot."""
    return {r["metric"]: r["value"] for r in snap["metrics"]}


def load_baseline(path):
    """The gate's baseline loader.  A single snapshot object (plain JSON)
    and the capability ledger file itself are both accepted: the ledger is
    JSONL and every line is a chain-linked snapshot, so the whole-file
    chain is validated and the head line anchors the gate (the ask's
    baseline contract: each ledger line is a snapshot in the same
    format)."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    try:
        snap = json.loads(raw)
    except ValueError:
        lines = load_ledger(path)
        if not lines:
            raise ShapeError("%s holds no snapshot line" % path)
        return lines[-1]
    if isinstance(snap, list):
        if not snap:
            raise ShapeError("%s holds an empty snapshot list" % path)
        lines = []
        expect_seq, expect_prev = 1, GENESIS_PREV_DIGEST
        for line in snap:
            lines.append(validate_ledger_line(line, expect_seq, expect_prev))
            expect_seq += 1
            expect_prev = line["digest"]
        return lines[-1]
    if "digest" in snap:
        return validate_ledger_line(snap, snap["seq"], snap["prev_digest"])
    validate_snapshot(snap)
    return snap


# ---- judgments ----

def judge_gate(base_values, fresh_values):
    """The ratchet direction: strictly-below is red, flat or above is
    green.  None (unmeasured) semantics: None vs None flat; a number vs None
    red (the measurement regressed to unmeasured); None vs a number green
    (first measurement is a rise).  Returns (ok, rows)."""
    rows, ok = [], True
    for metric in METRIC_FAMILIES:
        base, fresh = base_values[metric], fresh_values[metric]
        if base is None and fresh is None:
            verdict = "flat (unmeasured)"
        elif base is not None and fresh is None:
            verdict = "RED (measured -> unmeasured)"
            ok = False
        elif base is None and fresh is not None:
            verdict = "up (first measurement)"
        elif fresh < base:
            verdict = "RED (below baseline)"
            ok = False
        elif fresh == base:
            verdict = "flat"
        else:
            verdict = "up"
        rows.append((metric, base, fresh, verdict))
    return ok, rows


def judge_compare(head_values, fresh_values):
    """The runtime anti-tamper guarantee: a fresh derivation must equal the
    ledger head exactly (value equality per metric; window and ts naturally
    move).  Returns (ok, rows)."""
    rows, ok = [], True
    for metric in METRIC_FAMILIES:
        head, fresh = head_values[metric], fresh_values[metric]
        if head == fresh:
            verdict = "equal"
        else:
            verdict = "RED (fresh %r != ledger head %r)" % (fresh, head)
            ok = False
        rows.append((metric, head, fresh, verdict))
    return ok, rows


# ---- CLI faces ----

def _print_measure(snap):
    for r in snap["metrics"]:
        sys.stdout.write("%-28s %-9s value=%s\n  basis: %s\n  source: %s\n"
                         % (r["metric"], r["family"], r["value"],
                            r["basis"], r["source"]))
    sys.stdout.write("window %s..%s schema %s\n"
                     % (snap["window"]["from_sha"][:12],
                        snap["window"]["to_sha"][:12], snap["schema"]))


def _require_parent_dir(path, label):
    """Fail before any derivation when the caller-named output path cannot
    be written (its parent directory is absent)."""
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise ShapeError("%s target directory missing: %s" % (label, parent))


def _anchor_note(snap, provisional):
    """Disclose a working tree that differs from HEAD under the source
    paths: such readings are reproducible at the window anchor only once
    those paths are committed.  Written to stderr so the JSON face stays a
    single object."""
    state = snap.get("tree_state")
    if not state or not state["dirty"]:
        return
    sys.stderr.write(
        "WINDOW ANCHOR NOTE: the working tree differs from HEAD in %d source"
        " path(s); these readings describe the working tree and are"
        " reproducible at the window anchor only once those paths are"
        " committed%s\n"
        % (state["changed_paths"],
           " (this ledger line is provisional: tree_state.dirty)"
           if provisional else ""))


def mode_fault(args):
    """The flag-shape contract; returns the fault text, or None when the
    requested modes are coherent."""
    modes = [name for name, hit in (
        ("--measure", args.measure),
        ("--gate", args.gate),
        ("--compare", args.compare is not None),
        ("--append", args.append is not None),
        ("--selftest", args.selftest)) if hit]
    if args.selftest and (len(modes) > 1 or args.json_out is not None
                          or args.baseline or args.from_sha
                          or args.allow_dirty_anchor):
        return "--selftest takes no other flag"
    if not modes:
        return ("one of --measure / --gate / --compare / --append /"
                " --selftest is required")
    if args.append is not None and len(modes) > 1:
        return "--append takes no other mode"
    if args.gate and len(modes) > 1:
        return "--gate takes no other mode"
    if args.gate and not args.baseline:
        return "--gate requires --baseline FILE"
    if args.baseline and not args.gate:
        return "--baseline is read only by --gate"
    if args.json_out is not None and not args.measure:
        return "--json prints the snapshot: it needs --measure"
    if args.json_out is not None and args.compare is not None:
        return ("--json takes no --compare (the JSON face stays a single"
                " object)")
    if args.allow_dirty_anchor and args.append is None:
        return "--allow-dirty-anchor is read only by --append"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="nine-metric capability ratchet (measure/gate/compare/"
                    "append/selftest), schema " + SCHEMA)
    parser.add_argument("--repo", default=None,
                        help="repository root (default: the tree this file "
                             "lives in)")
    parser.add_argument("--measure", action="store_true",
                        help="derive fresh readings from the source accounts")
    parser.add_argument("--json", nargs="?", const=True, default=None,
                        dest="json_out",
                        help="with --measure: bare, print the single snapshot "
                             "JSON object on stdout; with a PATH argument, "
                             "write that object to the caller-named path")
    parser.add_argument("--gate", action="store_true",
                        help="judge fresh readings against --baseline "
                             "(below=rc1, flat/above=rc0)")
    parser.add_argument("--baseline", default=None,
                        help="baseline snapshot file (a capability-ratchet "
                             "ledger line is a valid baseline)")
    parser.add_argument("--compare", default=None, metavar="LEDGER",
                        help="validate the whole ledger chain and require "
                             "fresh values equal to the head line (with "
                             "--measure the readings print first; the "
                             "compare verdict decides the exit code)")
    parser.add_argument("--append", default=None, metavar="LEDGER",
                        help="append exactly one chain-linked snapshot line "
                             "(the append face stays CLI-side)")
    parser.add_argument("--allow-dirty-anchor", action="store_true",
                        dest="allow_dirty_anchor",
                        help="append: let the line be recorded on a working "
                             "tree that differs from HEAD under the source "
                             "paths (the line is stamped provisional)")
    parser.add_argument("--from-sha", default=None, dest="from_sha",
                        help="window start sha (default: with a ledger head "
                             "present, its to_sha; otherwise HEAD)")
    parser.add_argument("--selftest", action="store_true",
                        help="run the frozen vector group (offline, "
                             "repository-write-free)")
    args = parser.parse_args(argv)
    fault = mode_fault(args)
    if fault:
        sys.stderr.write("USAGE FAULT: %s\n" % fault)
        return 2

    repo = args.repo or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    try:
        if args.selftest:
            return selftest()
        to_sha = head_sha(repo)
        if args.from_sha and not SHA_RX.match(args.from_sha):
            raise ShapeError("--from-sha is not a 40-hex sha: %r"
                             % (args.from_sha,))
        # The ledger and the baseline resolve before any derivation, so a
        # broken chain or an unreadable baseline never spawns a source face.
        head = None
        if args.compare is not None:
            lines = load_ledger(args.compare)
            if not lines:
                raise ShapeError("--compare ledger %s holds no line (an empty"
                                 " ledger cannot anchor a compare)"
                                 % args.compare)
            head = lines[-1]
        if args.gate:
            base = load_baseline(args.baseline)
        if args.append is not None:
            _require_parent_dir(args.append, "append")
        if args.json_out is not None and args.json_out is not True:
            _require_parent_dir(args.json_out, "--json")
        from_sha, seq, prev, state = to_sha, None, None, None
        if args.append is not None:
            lines = load_ledger(args.append)
            state = tree_state(repo)
            if state["dirty"] and not args.allow_dirty_anchor:
                raise ShapeError(
                    "refusing to append: the working tree differs from HEAD"
                    " in %d source path(s); an append-only ledger line must"
                    " be reproducible at its window anchor - commit those"
                    " paths first, or pass --allow-dirty-anchor to record a"
                    " provisional line" % state["changed_paths"])
            if lines:
                from_sha = lines[-1]["window"]["to_sha"]
                seq, prev = lines[-1]["seq"] + 1, lines[-1]["digest"]
            else:
                from_sha, seq, prev = to_sha, 1, GENESIS_PREV_DIGEST
        snap = derive_metrics(repo, args.from_sha or from_sha, to_sha, state)
        _anchor_note(snap, args.append is not None)

        if args.append is not None:
            line = dict(snap)
            line["seq"] = seq
            line["prev_digest"] = prev
            line["digest"] = snapshot_digest(line)
            with open(args.append, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, ensure_ascii=False,
                                    sort_keys=True) + "\n")
            sys.stdout.write("APPEND OK seq=%d window %s..%s -> %s\n"
                             % (seq, from_sha[:12], to_sha[:12],
                                args.append))
            return 0
        if args.measure:
            if args.json_out is True:
                sys.stdout.write(json.dumps(snap, ensure_ascii=False,
                                            sort_keys=True) + "\n")
            elif args.json_out:
                with open(args.json_out, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps(snap, ensure_ascii=False,
                                        sort_keys=True) + "\n")
                sys.stdout.write("MEASURE OK -> %s\n" % args.json_out)
            else:
                _print_measure(snap)
        if args.gate:
            ok, rows = judge_gate(_values(base), _values(snap))
            for metric, base_v, fresh_v, verdict in rows:
                sys.stdout.write("gate %-28s baseline=%s fresh=%s %s\n"
                                 % (metric, base_v, fresh_v, verdict))
            if ok:
                sys.stdout.write("GATE PASS (%d metrics at or above baseline,"
                                 " window %s..%s)\n"
                                 % (len(rows),
                                    snap["window"]["from_sha"][:12],
                                    snap["window"]["to_sha"][:12]))
                return 0
            sys.stdout.write("GATE RED (%d metric(s) below baseline; the "
                             "ratchet only rolls forward)\n"
                             % sum(1 for r in rows if "RED" in r[3]))
            return 1
        if args.compare is not None:
            ok, rows = judge_compare(_values(head), _values(snap))
            for metric, head_v, fresh_v, verdict in rows:
                sys.stdout.write("compare %-26s ledger=%s fresh=%s %s\n"
                                 % (metric, head_v, fresh_v, verdict))
            if ok:
                sys.stdout.write("COMPARE PASS (fresh derivation equals the "
                                 "ledger head, seq %d)\n" % head["seq"])
                return 0
            sys.stdout.write("COMPARE RED (the ledger head no longer matches "
                             "the sources: hand-edit or drift - append a new "
                             "window, never rewrite)\n")
            return 1
        return 0
    except ShapeError as exc:
        sys.stderr.write("SHAPE FAULT: %s\n" % exc)
        return 2
    except OSError as exc:
        sys.stderr.write("IO FAULT: %s\n" % exc)
        return 2


# ---- selftest (offline, synthetic sources, private temp files only) ----

def raised_values(values):
    """The acceptance direction shape over a value map: every measured value
    up by one (the two rates leave [0, 1]); unmeasured stays null."""
    raised = dict(values)
    for metric in raised:
        if raised[metric] is not None:
            raised[metric] = raised[metric] + 1
    return raised


def selftest():
    """The frozen vector group.  Every vector is offline and deterministic:
    the per-source parsers read canned lines; the chain and judgment faces
    run over synthetic snapshots in a private temporary directory; the CLI
    faces run under canned source derivations (the derivation, the window
    anchor, and the tree state are replaced in-process for one call and
    restored).  The negative controls prove - through --compare itself,
    never through a helper alone - that a hand-edited reading is rejected,
    that a deleted historical line is rejected, and that a drifted ledger
    head is red.  Zero network, zero repository writes.  The last stdout
    line is exactly `selftest: <n> vector(s), <k> FAIL`; n is the number of
    distinct vector ids actually exercised, never a typed-in number."""
    fails = []
    vectors = []

    def check(vec, name, cond, detail=""):
        """One assertion under its vector id."""
        if vec not in vectors:
            vectors.append(vec)
        if not cond:
            fails.append("%s %s: %s" % (vec, name, detail or "assertion red"))

    SHA = "0123456789abcdef0123456789abcdef01234567"

    def snap_of(values, from_sha=None, to_sha=None):
        """A valid synthetic snapshot with caller-forced values."""
        window = {"from_sha": from_sha or SHA, "to_sha": to_sha or SHA}
        return {
            "schema": SCHEMA,
            "ts": "2026-11-25T00:00:00Z",
            "window": window,
            "metrics": [
                _reading(m, values.get(m, 1), window, "synthetic basis",
                         "synthetic source")
                for m in METRIC_FAMILIES
            ],
        }

    full = {m: 1 for m in METRIC_FAMILIES}
    full["repair_action_rate"] = 0.5

    real_derive, real_head, real_tree = derive_metrics, head_sha, tree_state
    spawns = []

    def canned_state(dirty):
        return {"dirty": dirty, "changed_paths": 3 if dirty else 0,
                "scope": "canned selftest tree"}

    def run_cli(argv, values, dirty=False):
        """main() under canned source faces -> (rc, stdout, stderr,
        derivations).  The three environment-facing functions are replaced
        for the call and restored in every case."""
        global derive_metrics, head_sha, tree_state

        def fake_derive(repo, from_sha, to_sha, state=None):
            spawns.append((from_sha, to_sha))
            window = {"from_sha": from_sha, "to_sha": to_sha}
            return {"schema": SCHEMA, "ts": "2026-11-25T00:00:00Z",
                    "window": window,
                    "tree_state": state if state is not None
                    else canned_state(dirty),
                    "scan_face": "canned selftest derivation",
                    "metrics": [_reading(m, values.get(m, 1), window,
                                         "synthetic basis",
                                         "synthetic source")
                                for m in METRIC_FAMILIES]}
        spawns[:] = []
        derive_metrics = fake_derive
        head_sha = lambda repo: SHA
        tree_state = lambda repo: canned_state(dirty)
        out, err = io.StringIO(), io.StringIO()
        rc, escaped = None, ""
        try:
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                rc = main(argv)
        except Exception as exc:
            # a fault escaping main() is itself a red (a traceback is never
            # the contract); it is reported under the probing vector
            escaped = "ESCAPED %s: %s" % (type(exc).__name__, exc)
        finally:
            derive_metrics, head_sha, tree_state = (real_derive, real_head,
                                                    real_tree)
        return rc, out.getvalue(), err.getvalue() + escaped, len(spawns)

    def try_load(path):
        """load_ledger without raising: the lines, or None on a fault."""
        try:
            return load_ledger(path)
        except ShapeError:
            return None

    # v1  the frozen nine: names, families, and the six-key reading shape
    snap = snap_of(full)
    validate_snapshot(snap)
    names = {r["metric"] for r in snap["metrics"]}
    check("v1", "frozen nine names", names == set(METRIC_FAMILIES), str(names))
    check("v1", "families split strength and gap-fill",
          {r["metric"] for r in snap["metrics"] if r["family"] == STRENGTH}
          == {"triage_classes", "regression_vectors", "taxonomy_rows",
              "cure_patterns", "mcp_roster", "selftest_vectors"}
          and {r["metric"] for r in snap["metrics"] if r["family"] == GAP_FILL}
          == {"repair_action_rate", "b_gate_ready_classes",
              "calibration_agreement_rate"})
    check("v1", "families tagged",
          all(r["family"] in (STRENGTH, GAP_FILL) for r in snap["metrics"]))

    # v2  every reading carries the five reading fields plus family
    check("v2", "reading fields",
          all(set(r) == READING_KEYS for r in snap["metrics"]))

    # v3  the calibration-null rule: entries=0 reads None, never 0
    check("v3", "calibration null",
          parse_calibration("calibration: ledger_present=true entries=0 "
                            "agreement_rate=None") == (None, 0))
    check("v3", "calibration measured",
          abs(parse_calibration("calibration: ledger_present=true entries=17 "
                                "agreement_rate=0.6667")[0] - 0.6667) < 1e-9)

    # v4  the roster parser on the real word face shape
    check("v4", "roster parse",
          parse_roster("MCP-SERVER-SELFTEST PASS (roster 56 specs, name map "
                       "complete, schema validation green)") == 56)

    # v5  the meta SUMMARY parser (the pass field is the reading)
    check("v5", "meta summary parse",
          parse_meta_pass("[SUMMARY] pass=70 skip=2 exempt=0 fail=0 total=72 "
                          "universe=tools/*.py") == 70)

    # v6  the repair-rate parser
    check("v6", "repair parse",
          abs(parse_repair_rate("repair: repaired=25 escalated=0 "
                                "watch_only_guard_correct=2 unrecorded=58 "
                                "repair_action_rate=0.2941")
              - 0.2941) < 1e-9)

    # v7  the ready-classes parser
    check("v7", "ready parse",
          parse_ready_classes("verdict: not-ready\nready classes: 0 of 3 "
                              "needed") == 0)

    # v8  digest determinism and tamper sensitivity
    d1 = snapshot_digest(snap)
    check("v8", "digest deterministic", d1 == snapshot_digest(snap_of(full)))
    tampered = snap_of(full)
    tampered["metrics"][0]["value"] = 2
    check("v8", "digest tamper-sensitive", d1 != snapshot_digest(tampered))

    # v9-v13, v19, v20, v22  ledgers, CLI faces, and the negative controls
    with tempfile.TemporaryDirectory(prefix="cap_ratchet_self_") as tmp:
        def write_lines(name, objs):
            """One JSON value per line; returns the path."""
            target = os.path.join(tmp, name)
            with open(target, "w", encoding="utf-8") as fh:
                for obj in objs:
                    fh.write(json.dumps(obj, sort_keys=True,
                                        ensure_ascii=False) + "\n")
            return target

        def without_chain(line):
            """The snapshot body of a ledger line (no seq / prev / digest)."""
            body = {k: v for k, v in line.items()
                    if k not in ("seq", "prev_digest", "digest")}
            body["metrics"] = [dict(r) for r in line["metrics"]]
            return body

        def raised(line):
            """The acceptance direction shape: every measured value up by
            one (the two rates leave [0, 1])."""
            body = without_chain(line)
            for r in body["metrics"]:
                if r["value"] is not None:
                    r["value"] = r["value"] + 1
            return body

        def hand_edited(line, metric, value, reseal):
            """One reading changed by hand.  reseal=False keeps the stale
            digest (the chain check must catch it); reseal=True recomputes
            the digest, so the chain passes and only the fresh equality of
            --compare can catch the edit."""
            edited = without_chain(line)
            edited.update({k: line[k] for k in ("seq", "prev_digest")})
            for r in edited["metrics"]:
                if r["metric"] == metric:
                    r["value"] = value
            edited["digest"] = snapshot_digest(edited) if reseal \
                else line["digest"]
            return edited

        path = os.path.join(tmp, "ledger.jsonl")
        lines, prev = [], GENESIS_PREV_DIGEST
        for seq, bump in ((1, {}), (2, {"taxonomy_rows": 2}),
                          (3, {"taxonomy_rows": 3, "cure_patterns": 2})):
            vals = dict(full)
            vals.update(bump)
            line = dict(snap_of(vals))
            line["seq"] = seq
            line["prev_digest"] = prev
            line["digest"] = snapshot_digest(line)
            lines.append(line)
            prev = line["digest"]
        write_lines("ledger.jsonl", lines)
        loaded = load_ledger(path)
        check("v9", "chain validates",
              len(loaded) == 3 and loaded[-1]["seq"] == 3)
        head_values = _values(loaded[-1])
        rc, out, err, spawned = run_cli(["--compare", path], head_values)
        check("v9", "cli compare equal green",
              rc == 0 and "COMPARE PASS" in out and spawned == 1,
              "rc=%r out=%r err=%r spawned=%d" % (rc, out[-160:], err[-160:],
                                                  spawned))

        # v10  an inflated reading with its stale digest is rejected, and
        # --compare rejects it before any fresh derivation is spawned
        inflated = dict(lines[1])
        inflated["metrics"] = [dict(r) for r in lines[1]["metrics"]]
        for r in inflated["metrics"]:
            if r["metric"] == "taxonomy_rows":
                r["value"] = 99
        try:
            validate_ledger_line(inflated, 2, lines[0]["digest"])
            check("v10", "inflated reading rejected", False,
                  "an inflated reading passed the digest check")
        except ShapeError:
            check("v10", "inflated reading rejected", True)
        stale = write_lines("stale.jsonl",
                            [lines[0], hand_edited(lines[1], "taxonomy_rows",
                                                   99, False), lines[2]])
        rc, out, err, spawned = run_cli(["--compare", stale], head_values)
        check("v10", "cli compare rejects the hand-edited reading",
              rc == 2 and "fails its own digest" in err and spawned == 0,
              "rc=%r err=%r spawned=%d" % (rc, err[-160:], spawned))
        rc, out, err, spawned = run_cli(["--measure", "--compare", stale],
                                        head_values)
        check("v20", "card form rejects the hand-edited ledger",
              rc == 2 and "SHAPE FAULT" in err and spawned == 0,
              "rc=%r err=%r spawned=%d" % (rc, err[-160:], spawned))

        # v11  the deleted-history negative: removing a historical line
        # breaks the chain
        with open(path, "r", encoding="utf-8") as fh:
            file_lines = [l for l in fh.read().splitlines() if l.strip()]
        del file_lines[1]
        truncated = write_lines("truncated.jsonl",
                                [json.loads(l) for l in file_lines])
        check("v11", "deleted history rejected", try_load(truncated) is None)
        rc, out, err, spawned = run_cli(["--compare", truncated], head_values)
        check("v11", "cli compare rejects the deleted historical line",
              rc == 2 and "SHAPE FAULT" in err and spawned == 0,
              "rc=%r err=%r spawned=%d" % (rc, err[-160:], spawned))

        # v12  compare green: fresh equal to the ledger head
        ok, _ = judge_compare(head_values, dict(head_values))
        check("v12", "compare equal green", ok)

        # v13  the drifted-head negative: the ledger head claims
        # taxonomy_rows=99 under a recomputed digest (the chain alone
        # accepts it) while the fresh derivation reads the true 3
        fresh_values = dict(head_values)
        fresh_values["taxonomy_rows"] = 1
        ok, rows = judge_compare(head_values, fresh_values)
        check("v13", "compare drift red", not ok)
        drifted = write_lines("drifted.jsonl",
                              [lines[0], lines[1],
                               hand_edited(lines[2], "taxonomy_rows", 99,
                                           True)])
        check("v13", "resealed edit is invisible to the chain alone",
              len(try_load(drifted) or []) == 3)
        rc, out, err, spawned = run_cli(["--compare", drifted], head_values)
        check("v13", "cli compare red on the resealed inflated head",
              rc == 1 and "COMPARE RED" in out and spawned == 1,
              "rc=%r out=%r spawned=%d" % (rc, out[-160:], spawned))
        rc, out, err, spawned = run_cli(["--measure", "--compare", drifted],
                                        head_values)
        check("v20", "card form prints the readings and is red on drift",
              rc == 1 and "COMPARE RED" in out
              and out.count("  basis: ") == len(METRIC_FAMILIES),
              "rc=%r out=%r spawned=%d" % (rc, out[-160:], spawned))
        rc, out, err, spawned = run_cli(["--measure", "--compare", path],
                                        head_values)
        check("v20", "card form green on the honest ledger",
              rc == 0 and "COMPARE PASS" in out and spawned == 1,
              "rc=%r out=%r spawned=%d" % (rc, out[-160:], spawned))

        # v14  the gate direction triple through the CLI face, with the
        # ledger itself as the baseline (its head line anchors)
        below = dict(head_values)
        below["taxonomy_rows"] = 2
        rc, out, err, spawned = run_cli(["--gate", "--baseline", path], below)
        check("v14", "cli gate below red",
              rc == 1 and "GATE RED" in out, "rc=%r out=%r" % (rc, out[-160:]))
        rc, out, err, spawned = run_cli(["--gate", "--baseline", path],
                                        head_values)
        check("v14", "cli gate flat green",
              rc == 0 and "GATE PASS" in out,
              "rc=%r out=%r" % (rc, out[-160:]))
        above = dict(head_values)
        above["taxonomy_rows"] = 4
        rc, out, err, spawned = run_cli(["--gate", "--baseline", path], above)
        check("v14", "cli gate up green",
              rc == 0 and "GATE PASS" in out,
              "rc=%r out=%r" % (rc, out[-160:]))
        body = write_lines("snap.json", [without_chain(lines[2])])
        rc, out, err, spawned = run_cli(["--gate", "--baseline", body],
                                        head_values)
        check("v14", "cli gate reads a plain snapshot baseline",
              rc == 0 and "GATE PASS" in out,
              "rc=%r err=%r" % (rc, err[-160:]))
        higher = write_lines("higher.json", [raised(lines[2])])
        rc, out, err, spawned = run_cli(["--gate", "--baseline", higher],
                                        head_values)
        check("v14", "cli gate judges the uniformly raised baseline",
              rc == 1 and "GATE RED" in out and "SHAPE FAULT" not in err,
              "rc=%r out=%r err=%r" % (rc, out[-160:], err[-160:]))

        # v19  usage, shape, and IO faults are rc 2 - never a traceback,
        # never rc 1 (rc 1 is reserved for a real red)
        absent = os.path.join(tmp, "absent.json")
        probes = [
            ("no mode", [], 0),
            ("gate without baseline", ["--gate"], 0),
            ("baseline without gate", ["--baseline", path], 0),
            ("missing baseline file", ["--gate", "--baseline", absent], 0),
            ("baseline is a directory", ["--gate", "--baseline", tmp], 0),
            ("compare on an empty ledger", ["--compare", absent], 0),
            ("selftest with another mode", ["--selftest", "--measure"], 0),
            ("json without measure", ["--json"], 0),
            ("json with compare", ["--measure", "--compare", path, "--json"],
             0),
            ("append with measure",
             ["--append", os.path.join(tmp, "x.jsonl"), "--measure"], 0),
            ("allow-dirty-anchor without append",
             ["--measure", "--allow-dirty-anchor"], 0),
            ("json path under a missing directory",
             ["--measure", "--json", os.path.join(tmp, "no_dir", "o.json")],
             0),
            ("append path under a missing directory",
             ["--append", os.path.join(tmp, "no_dir", "o.jsonl")], 0),
            ("from-sha not a sha", ["--measure", "--from-sha", "junk"], 0),
        ]
        for name, argv, want in probes:
            rc, out, err, spawned = run_cli(argv, head_values)
            check("v19", "rc 2: " + name,
                  rc == 2 and "ESCAPED" not in err and spawned == want,
                  "rc=%r err=%r spawned=%d" % (rc, err[-200:], spawned))
        check("v19", "no probe left a file behind",
              not os.path.exists(os.path.join(tmp, "x.jsonl"))
              and not os.path.exists(os.path.join(tmp, "no_dir")))

        # v21  the tree-state disclosure leaves the verdicts untouched
        rc, out, err, spawned = run_cli(["--measure", "--json"], head_values,
                                        dirty=True)
        try:
            printed = json.loads(out)
        except ValueError:
            printed = None
        check("v21", "json face stays one object on a dirty tree",
              rc == 0 and printed is not None
              and out.count("\n") == 1
              and printed["tree_state"] == canned_state(True)
              and len(printed["metrics"]) == len(METRIC_FAMILIES))
        check("v21", "dirty note goes to stderr",
              "WINDOW ANCHOR NOTE" in err and "3 source path(s)" in err)
        rc, out, err, spawned = run_cli(["--gate", "--baseline", path],
                                        head_values, dirty=True)
        check("v21", "gate still judges on a dirty tree",
              rc == 0 and "GATE PASS" in out and "WINDOW ANCHOR NOTE" in err)
        rc, out, err, spawned = run_cli(["--measure"], head_values,
                                        dirty=False)
        check("v21", "clean tree prints no note",
              rc == 0 and "WINDOW ANCHOR NOTE" not in err)

        # v22  the append guard: a dirty tree needs the explicit flag
        led = os.path.join(tmp, "append.jsonl")
        rc, out, err, spawned = run_cli(["--append", led], head_values,
                                        dirty=True)
        check("v22", "append refuses a dirty tree",
              rc == 2 and "refusing to append" in err and spawned == 0
              and not os.path.exists(led),
              "rc=%r err=%r spawned=%d" % (rc, err[-160:], spawned))
        rc, out, err, spawned = run_cli(
            ["--append", led, "--allow-dirty-anchor"], head_values, dirty=True)
        appended = try_load(led)
        check("v22", "flagged dirty append lands stamped provisional",
              rc == 0 and "APPEND OK seq=1" in out
              and appended is not None and len(appended) == 1
              and appended[0]["tree_state"] == canned_state(True)
              and appended[0]["prev_digest"] == GENESIS_PREV_DIGEST
              and "provisional" in err,
              "rc=%r out=%r err=%r" % (rc, out[-160:], err[-160:]))
        clean = os.path.join(tmp, "clean.jsonl")
        rc, out, err, spawned = run_cli(["--append", clean], head_values)
        first = try_load(clean)
        check("v22", "clean append green and not provisional",
              rc == 0 and "APPEND OK seq=1" in out and first is not None
              and len(first) == 1
              and first[0]["tree_state"] == canned_state(False)
              and "WINDOW ANCHOR NOTE" not in err,
              "rc=%r out=%r err=%r" % (rc, out[-160:], err[-160:]))
        rc, out, err, spawned = run_cli(["--append", clean], head_values)
        chain = try_load(clean)
        check("v22", "second append chains to the first",
              rc == 0 and "APPEND OK seq=2" in out and chain is not None
              and len(chain) == 2
              and chain[1]["prev_digest"] == chain[0]["digest"]
              and chain[1]["window"]["from_sha"] == SHA,
              "rc=%r out=%r" % (rc, out[-160:]))
        broken = write_lines("broken.jsonl", [lines[0], lines[1]])
        with open(broken, "a", encoding="utf-8") as fh:
            fh.write("not json\n")
        rc, out, err, spawned = run_cli(["--append", broken], head_values)
        with open(broken, "r", encoding="utf-8") as fh:
            survived = len([l for l in fh.read().splitlines() if l.strip()])
        check("v22", "append never extends a damaged ledger",
              rc == 2 and spawned == 0 and survived == 3,
              "rc=%r spawned=%d lines=%d" % (rc, spawned, survived))

    # v14  the gate direction triple (function face)
    base = _values(snap_of(full))
    below = dict(base)
    below["cure_patterns"] = 0
    check("v14", "gate below red", not judge_gate(base, below)[0])
    check("v14", "gate flat green", judge_gate(base, dict(base))[0])
    above = dict(base)
    above["triage_classes"] = 2
    check("v14", "gate up green", judge_gate(base, above)[0])

    # v15  the unmeasured-null gate semantics: None->None flat, number->None
    # red (a lost measurement is a regression), None->number a rise
    none_base = dict(full)
    none_base["calibration_agreement_rate"] = None
    fresh_none = dict(none_base)
    check("v15", "null-null flat", judge_gate(none_base, fresh_none)[0])
    fresh_lost = dict(none_base)
    fresh_lost["calibration_agreement_rate"] = None
    lost_base = dict(full)
    lost_base["calibration_agreement_rate"] = 0.5
    check("v15", "measured->null red",
          not judge_gate(lost_base, fresh_lost)[0])
    unmeasured_base = dict(none_base)
    fresh_measured = dict(none_base)
    fresh_measured["calibration_agreement_rate"] = 0.5
    check("v15", "null->measured up",
          judge_gate(unmeasured_base, fresh_measured)[0])

    # v16  a reading without its basis (a hand-fill shape) is rejected
    naked = snap_of(full)
    naked["metrics"][0]["basis"] = ""
    try:
        validate_snapshot(naked)
        check("v16", "empty basis rejected", False,
              "a basis-less reading passed validation")
    except ShapeError:
        check("v16", "empty basis rejected", True)

    # v17  the genesis append shape: seq 1 with the genesis prev_digest
    genesis = dict(snap_of(full))
    genesis["seq"] = 1
    genesis["prev_digest"] = GENESIS_PREV_DIGEST
    genesis["digest"] = snapshot_digest(genesis)
    check("v17", "genesis line validates",
          validate_ledger_line(genesis, 1, GENESIS_PREV_DIGEST) is genesis)

    # v18  the fresh-side rate range: a share of a unit outside [0, 1] is
    # a derivation fault; a stored baseline value is not range-judged
    check("v18", "fresh rates inside the unit accepted",
          rate_fault("repair_action_rate", 0.2941) is None
          and rate_fault("repair_action_rate", 0) is None
          and rate_fault("repair_action_rate", 1) is None
          and rate_fault("calibration_agreement_rate", 0.6667) is None)
    check("v18", "fresh rate above one rejected",
          rate_fault("repair_action_rate", 1.2941) is not None)
    check("v18", "fresh negative rate rejected",
          rate_fault("calibration_agreement_rate", -0.01) is not None)
    check("v18", "unmeasured null accepted",
          rate_fault("calibration_agreement_rate", None) is None)
    check("v18", "count metrics are not range-bound",
          rate_fault("triage_classes", 99) is None)
    validate_snapshot(snap_of(raised_values(full)))
    check("v18", "stored values are not range-judged", True)

    # v21  the tree-state record on canned porcelain text and shapes
    check("v21", "porcelain count",
          count_changed("") == 0 and count_changed("\n") == 0
          and count_changed(" M tools/mcp_server.py\n"
                            "?? tools/capability_ratchet.py\n") == 2
          and count_changed(" M a\n\n D b\n") == 2)
    clean_state = state_from_porcelain("")
    dirty_state = state_from_porcelain(" M tools/mcp_server.py\n"
                                       "?? tools/capability_ratchet.py\n")
    check("v21", "porcelain to tree state",
          clean_state["dirty"] is False and clean_state["changed_paths"] == 0
          and dirty_state["dirty"] is True
          and dirty_state["changed_paths"] == 2
          and _tree_state_ok(clean_state) and _tree_state_ok(dirty_state))
    def covered(path):
        """A source path sits under an exact pathspec or a directory one."""
        return any(path == spec or path.startswith(spec + "/")
                   for spec in SOURCE_PATHSPECS)

    accounts = ["/".join(p) for p in (ROUND_LEDGER, ROUND_STATE, EXP_LEDGER,
                                      TAXONOMY)] + [
        "tools/mcp_server.py", "tools/capability_ratchet.py",
        "tests/test_tool_selftests.py", "tests/fixtures/ci_triage_x.json",
        "docs/ci-triage-table.json", "wash/cure_pack.json"]
    check("v21", "source paths cover every source account",
          all(covered(p) for p in accounts),
          str([p for p in accounts if not covered(p)]))
    check("v21", "consistent tree states accepted",
          _tree_state_ok({"dirty": False, "changed_paths": 0, "scope": "s"})
          and _tree_state_ok({"dirty": True, "changed_paths": 4,
                              "scope": "s"}))
    check("v21", "inconsistent tree states rejected",
          not _tree_state_ok({"dirty": True, "changed_paths": 0, "scope": "s"})
          and not _tree_state_ok({"dirty": False, "changed_paths": 2,
                                  "scope": "s"})
          and not _tree_state_ok({"dirty": True, "changed_paths": -1,
                                  "scope": "s"})
          and not _tree_state_ok({"dirty": "yes", "changed_paths": 1,
                                  "scope": "s"})
          and not _tree_state_ok({"dirty": True, "changed_paths": 1,
                                  "scope": ""}))
    stamped = snap_of(full)
    stamped["tree_state"] = {"dirty": True, "changed_paths": 0, "scope": "s"}
    try:
        validate_snapshot(stamped)
        check("v21", "snapshot rejects a malformed tree state", False,
              "a malformed tree state passed validation")
    except ShapeError:
        check("v21", "snapshot rejects a malformed tree state", True)
    check("v21", "tree state is part of the digest",
          snapshot_digest(snap_of(full))
          != snapshot_digest(dict(snap_of(full),
                                  tree_state=canned_state(True))))

    # v23  the derivation wiring under canned source faces: what the parsers
    # read is what the snapshot carries (the unmeasured calibration stays
    # null end to end; a fresh rate outside the unit is a fault)
    real_sources = (_spawn, _learning_summary, _b_gate_summary, _json_count,
                    _fixture_count, tree_state)

    def canned_feedback(rate, entries, agreement):
        return ("scheduling-feedback: schema canned\n"
                "rounds: total=2 auto=1 human_approved=1"
                " approval_rate_auto=0.5\n"
                "repair: repaired=25 escalated=0 watch_only_guard_correct=2"
                " unrecorded=58 repair_action_rate=%s\n"
                "calibration: ledger_present=%s entries=%d agreement_rate=%s\n"
                % (rate, "true" if entries else "false", entries, agreement))

    def run_derive(feedback, roster_line, summary_line):
        """derive_metrics under canned source faces -> (snapshot, fault)."""
        global _spawn, _learning_summary, _b_gate_summary, _json_count
        global _fixture_count, tree_state

        def fake_spawn(repo, args, timeout, isolated=True):
            if args[0].endswith("mcp_server.py"):
                return roster_line
            return summary_line

        def fake_learning(repo):
            if feedback == "ACCOUNT ERROR":
                raise ShapeError("learning_feedback face carries 1 account"
                                 " error(s): canned")
            return feedback

        def fake_b_gate(repo):
            return ("verdict: not-ready\nready classes: 0 of 3 needed\n"
                    "remaining_to_b: 3\n")

        def fake_json_count(path, key):
            return {"classes": 24, "rows": 6, "patterns": 25}[key]

        snapshot, fault = None, None
        _spawn, _learning_summary, _b_gate_summary = (fake_spawn,
                                                      fake_learning,
                                                      fake_b_gate)
        _json_count, _fixture_count = fake_json_count, lambda d, p: 10
        tree_state = lambda repo: canned_state(False)
        try:
            snapshot = derive_metrics(os.sep + "canned", SHA, SHA)
        except ShapeError as exc:
            fault = str(exc)
        finally:
            (_spawn, _learning_summary, _b_gate_summary, _json_count,
             _fixture_count, tree_state) = real_sources
        return snapshot, fault

    roster = "MCP-SERVER-SELFTEST PASS (roster 57 specs, name map complete)"
    summary = ("[SUMMARY] pass=71 skip=2 exempt=0 fail=0 total=73"
               " universe=tools/*.py")
    snapshot, fault = run_derive(canned_feedback("0.2941", 0, "None"), roster,
                                 summary)
    check("v23", "canned derivation validates", fault is None and snapshot
          is not None and validate_snapshot(snapshot) is True, str(fault))
    if snapshot is not None:
        values = _values(snapshot)
        check("v23", "canned readings carry their source values",
              values == {"triage_classes": 24, "regression_vectors": 10,
                         "taxonomy_rows": 6, "cure_patterns": 25,
                         "mcp_roster": 57, "selftest_vectors": 71,
                         "repair_action_rate": 0.2941,
                         "b_gate_ready_classes": 0,
                         "calibration_agreement_rate": None}, str(values))
        check("v23", "unmeasured calibration stays null end to end",
              values["calibration_agreement_rate"] is None)
        check("v23", "snapshot carries the tree state",
              snapshot["tree_state"] == canned_state(False)
              and snapshot["window"] == {"from_sha": SHA, "to_sha": SHA})
    snapshot, fault = run_derive(canned_feedback("0.5", 5, "0.0"), roster,
                                 summary)
    check("v23", "a measured zero is 0.0, not null",
          fault is None and snapshot is not None
          and _values(snapshot)["calibration_agreement_rate"] == 0.0,
          str(fault))
    snapshot, fault = run_derive(canned_feedback("1.2941", 0, "None"), roster,
                                 summary)
    check("v23", "fresh rate outside the unit is a fault",
          snapshot is None and fault is not None and "[0, 1]" in fault,
          str(fault))
    snapshot, fault = run_derive(canned_feedback("0.2941", 5, "1.5"), roster,
                                 summary)
    check("v23", "fresh agreement rate outside the unit is a fault",
          snapshot is None and fault is not None and "[0, 1]" in fault,
          str(fault))
    snapshot, fault = run_derive("ACCOUNT ERROR", roster, summary)
    check("v23", "a source account error is loud",
          snapshot is None and fault is not None
          and "account error" in fault, str(fault))
    snapshot, fault = run_derive(canned_feedback("0.2941", 0, "None"),
                                 "no roster word here", summary)
    check("v23", "a missing roster word is a fault",
          snapshot is None and fault is not None, str(fault))
    snapshot, fault = run_derive(canned_feedback("0.2941", 0, "None"), roster,
                                 "no summary word here")
    check("v23", "a missing SUMMARY word is a fault",
          snapshot is None and fault is not None, str(fault))

    n = len(vectors)
    k = len(fails)
    for fail in fails:
        sys.stderr.write("CAPABILITY-RATCHET-SELFTEST FAIL %s\n" % fail)
    verdict = "PASS" if not fails else "FAIL"
    sys.stdout.write("CAPABILITY-RATCHET-SELFTEST %s\n" % verdict)
    sys.stdout.write("selftest: %d vector(s), %d FAIL\n" % (n, k))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
