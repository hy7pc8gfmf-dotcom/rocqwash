#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scheduler_lite.py - TODO-SEAT threshold trigger face, jargon tier-B auto gear.

Purpose.  Watches the TODO-SEAT gap account (tools/gap_cluster.py
  aggregation) and the round cadence, and decides whether a jargon-class
  auto round is due under the tier-B auto gear (autonomy.json mode auto,
  roster docs/round-state.json).  Ratchet ticket B: consumes
  rounds.approval_rate_auto from docs/scheduling-feedback.json (the
  sibling learning_feedback writer); below 0.5 the round interval
  doubles, 0.5 and up keeps the measured cadence; the applied influence
  rides the plan document (schedulingInput).  Ignition stays behind the
  EF marker gate; the face plans only and never fires.
Interface.  `py -I tools/scheduler_lite.py plan [--gap-ledger P]...
  [--reports P]... [--rounds P] [--autonomy P] [--state P] [--feedback P]
  [--ef-marker P] [--threshold N] [--interval-seconds N]
  [--now-utc ISO8601Z] [--out FILE] [--json]` or --selftest; one summary
  line or, with --json, the plan document (rocqwash.scheduler-lite.plan/1;
  verdict quiet | due | blocked; absent defaults are data, corrupt exit 9).
  MCP withholds --feedback: unflagged runs read the standing default.
Dependencies.  Python 3 stdlib only; tools/gap_cluster.py absent exits 9;
  the edge selfscan vectors load tools/learning_feedback.py by path (the
  grade face imported, never re-implemented); interval default 40566 s.
Evidence.  --selftest tmp-fixture vectors: threshold trigger and quiet,
  override, vacgen report face, measured/backfill cadence, due probes,
  gate/admission/gear blocks, feedback consumption (downshift flips due
  to blocked, current/null rates, corrupt/absent exit 9), the edge
  selfscan kill face plus the live-trace closed face, determinism, zero
  writes, CJK/em-dash-free probe.
Exit-codes.  0 = the plan face answered (quiet and blocked are data);
  1 = selftest red; 2 = usage; 9 = corrupt or explicitly missing input.
"""

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

SCHEMA = "rocqwash.scheduler-lite.plan/1"
PROG = "scheduler_lite"
TOOL_VERSION = "1"

CLASS_JARGON = "jargon"
DEFAULT_GAP_LEDGER = ("docs", "gap-feed-ledger.jsonl")
DEFAULT_REPORTS_DIR = ("docs", "vacgen-reports")
DEFAULT_ROUNDS = ("docs", "round-ledger.jsonl")
DEFAULT_STATE = ("docs", "round-state.json")
DEFAULT_AUTONOMY = ("autonomy.json",)
DEFAULT_FEEDBACK = ("docs", "scheduling-feedback.json")

DEFAULT_THRESHOLD = 1

# The standing feedback-consumption constants (ratchet ticket B): the
# approval rate key the plan face consumes from the sibling feedback doc,
# and the consumption rule - below the downshift rate the cadence
# interval doubles, 0.5 and up keeps the measured cadence, and an
# unreadable rate (no rounds yet) keeps it too.
FEEDBACK_RATE_KEY = "approval_rate_auto"
FEEDBACK_DOWNSHIFT_RATE = 0.5
FEEDBACK_DOWNSHIFT_FACTOR = 2

# Measured backfill: docs/round-ledger.jsonl tail pair, round 1
# 2026-11-15T04:49:24Z -> round 2 2026-11-15T16:05:30Z = 40566 s.
# Placeholder ruling: the E4 axiom_guard timing backfill (workflow candidate
# ruling 3) amends this one knob; --interval-seconds overrides at runtime.
DEFAULT_INTERVAL_SECONDS = 40566

TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VERDICT_QUIET = "quiet"
VERDICT_DUE = "due"
VERDICT_BLOCKED = "blocked"

# Informational only: the ignition pipeline shape the workflow would drive
# after the EF all-green gate opens.  This face executes neither step.
IGNITE_STEP_1 = "py -I -X utf8 tools/jargon_apply.py --tree --apply"
IGNITE_STEP_2 = ("py -I -X utf8 tools/auto_round.py commit --classes jargon"
                 " --files <step1 plan files> --hits <hits.json>")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CJK_RE = re.compile(u"[\u4e00-\u9fff\u3400-\u4dbf]")
_EM_DASH = u"\u2014"

_GC = None
_LF = None


class SchedulerInputError(Exception):
    """Corrupt or explicitly missing input (the exit-9 face)."""


def fail(message, code):
    sys.stderr.write(PROG + ": " + message + "\n")
    raise SystemExit(code)


def gap_cluster_module():
    """Load tools/gap_cluster.py by path (the same-source gap aggregator)."""
    global _GC
    if _GC is None:
        path = os.path.join(REPO_ROOT, "tools", "gap_cluster.py")
        if not os.path.isfile(path):
            fail("sibling tools/gap_cluster.py is absent", 9)
        spec = importlib.util.spec_from_file_location(
            "rocqwash_scheduler_gap_cluster", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _GC = mod
    return _GC


def learning_feedback_module():
    """Load tools/learning_feedback.py by path (the sibling feedback-edge
    grader; the grade face is imported, never re-implemented)."""
    global _LF
    if _LF is None:
        path = os.path.join(REPO_ROOT, "tools", "learning_feedback.py")
        if not os.path.isfile(path):
            fail("sibling tools/learning_feedback.py is absent", 9)
        spec = importlib.util.spec_from_file_location(
            "rocqwash_scheduler_learning_feedback", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LF = mod
    return _LF


def feedback_face(flagged):
    """The feedback input face: the standing approval rate the round gear
    consumes.  An explicitly flagged absent path is an exit-9 input
    error; the absent default is a data state (the sibling feedback
    writer has not run yet); a present doc without a readable
    rounds.approval_rate_auto (None or a number, never a bool) fails
    loud exit 9.  Never guessed."""
    paths, present, default_absent = resolve_member_paths(
        [flagged] if flagged else [], DEFAULT_FEEDBACK, "feedback")
    if not present:
        return {"present": False, "approvalRateAuto": None,
                "source": None,
                "note": ("feedback doc absent at the standing default %s"
                         " (data state; cadence unchanged)"
                         % os.path.join(REPO_ROOT, *DEFAULT_FEEDBACK))}
    doc = read_json_doc(paths[0])
    rounds = doc.get("rounds")
    if not isinstance(rounds, dict) or FEEDBACK_RATE_KEY not in rounds:
        raise SchedulerInputError(
            "%s carries no rounds.%s reading" % (paths[0],
                                                 FEEDBACK_RATE_KEY))
    rate = rounds[FEEDBACK_RATE_KEY]
    if rate is not None and (isinstance(rate, bool)
                             or not isinstance(rate, (int, float))):
        raise SchedulerInputError(
            "%s rounds.%s is not null or a number: %r"
            % (paths[0], FEEDBACK_RATE_KEY, rate))
    return {"present": True, "approvalRateAuto": rate,
            "source": paths[0], "note": "ok"}


def apply_feedback_input(interval, rate):
    """The consumption rule: approval_rate_auto below 0.5 downshifts the
    round cadence - the interval doubles, so the next auto round waits
    longer - and 0.5 and up (or an unreadable rate: no rounds yet) keeps
    the measured cadence.  Returns (interval, action, basis); the pair
    rides the plan document as schedulingInput so every influence stays
    traceable."""
    if rate is None:
        return interval, "cadence-current", (
            "approval_rate_auto unreadable (the feedback face holds no"
            " rounds yet); cadence unchanged")
    if rate < FEEDBACK_DOWNSHIFT_RATE:
        doubled = int(interval * FEEDBACK_DOWNSHIFT_FACTOR)
        return doubled, "cadence-interval-x2", (
            "approval_rate_auto %s < %s: round cadence downshifted, the"
            " interval doubles (%d s)" % (rate, FEEDBACK_DOWNSHIFT_RATE,
                                          doubled))
    return interval, "cadence-current", (
        "approval_rate_auto %s >= %s: cadence stays measured"
        % (rate, FEEDBACK_DOWNSHIFT_RATE))


def parse_ts(text, label):
    """Parse one ledger timestamp (ISO-8601 Z form) or raise input error."""
    if not isinstance(text, str):
        raise SchedulerInputError("%s: timestamp is not a string" % label)
    try:
        return datetime.strptime(text, TS_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        raise SchedulerInputError(
            "%s: timestamp %r is not in %s form" % (label, text, TS_FORMAT))


def now_from_args(text):
    """The plan clock: the injected --now-utc value or the real UTC clock.

    Returns (datetime, canonical_text); a malformed override raises
    SchedulerInputError so the caller can route it to the usage face.
    """
    if text is None:
        now = datetime.now(timezone.utc)
        return now, now.strftime(TS_FORMAT)
    return parse_ts(text, "--now-utc"), text


def read_jsonl_rows(path):
    """Read one JSONL file into dict rows (fail loud on corrupt lines)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError as exc:
                raise SchedulerInputError(
                    "%s line %d is not valid JSON: %s" % (path, lineno, exc))
            if not isinstance(entry, dict):
                raise SchedulerInputError(
                    "%s line %d is not a JSON object" % (path, lineno))
            rows.append(entry)
    return rows


def read_json_doc(path):
    """Read one JSON document (fail loud on corrupt content)."""
    with open(path, encoding="utf-8") as fh:
        try:
            doc = json.load(fh)
        except ValueError as exc:
            raise SchedulerInputError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise SchedulerInputError("%s is not a JSON object" % path)
    return doc


def resolve_member_paths(flagged, default, label):
    """Resolve one input face into (paths, present, default_absent).

    Absent default inputs are data states; an explicitly flagged missing
    path is an exit-9 input error.  Directories ride as-is; the aggregator
    expands report directories itself.
    """
    if flagged:
        for path in flagged:
            if not os.path.exists(path):
                raise SchedulerInputError(
                    "%s path %s does not exist" % (label, path))
        return list(flagged), True, False
    default_path = os.path.join(REPO_ROOT, *default)
    if not os.path.exists(default_path):
        return [], False, True
    return [default_path], True, False


def gap_face(gap_ledgers, reports, threshold):
    """Aggregate the TODO-SEAT gap signal through tools/gap_cluster.py."""
    gc = gap_cluster_module()
    ledger_paths, ledgers_present, ledgers_default_absent = \
        resolve_member_paths(gap_ledgers, DEFAULT_GAP_LEDGER, "gap-ledger")
    report_paths, reports_present, reports_default_absent = \
        resolve_member_paths(reports, DEFAULT_REPORTS_DIR, "reports")
    try:
        aggregated = gc.aggregate(ledger_paths, report_paths)
    except gc.GapInputError as exc:
        raise SchedulerInputError(str(exc))
    totals = aggregated["totals"]
    todo_seat_total = totals["ledgerGapEntries"] + totals["reportTodoSeat"]
    return {
        "present": bool(ledgers_present or reports_present),
        "ledgersPresent": ledgers_present,
        "reportsPresent": reports_present,
        "ledgersDefaultAbsent": ledgers_default_absent,
        "reportsDefaultAbsent": reports_default_absent,
        "ledgerEntries": totals["ledgerEntries"],
        "ledgerGapEntries": totals["ledgerGapEntries"],
        "reportAssumptions": totals["reportAssumptions"],
        "reportTodoSeat": totals["reportTodoSeat"],
        "todoSeatTotal": todo_seat_total,
        "threshold": threshold,
        "triggered": todo_seat_total >= threshold,
        "inputFingerprint": aggregated["inputFingerprint"],
    }


def cadence_face(rows, now_dt, interval_override, feedback_rate=None):
    """Measure the round cadence, apply the feedback gear, test due.

    Two or more rows: the measured interval is the tail pair delta.  Fewer
    rows fall back to the measured backfill constant.  The standing
    feedback gear (apply_feedback_input) then amends the interval BEFORE
    the due test, so the approval rate steers the decision whatever the
    interval source; the applied action and basis ride the face.  No
    standing round is not cadence-blocked (a first round cannot violate
    a spacing rule).
    """
    rounds_present = bool(rows)
    if rounds_present:
        times = []
        for idx, row in enumerate(rows, 1):
            label = "round row %d" % idx
            times.append((parse_ts(row.get("timestamp_utc"), label),
                          row.get("round_id")))
        times.sort(key=lambda pair: pair[0])
        last_ts, last_id = times[-1]
        if len(times) >= 2:
            interval = int((times[-1][0] - times[-2][0]).total_seconds())
            source = "measured"
        else:
            interval = interval_override
            source = "backfill"
    else:
        last_ts, last_id = None, None
        interval = interval_override
        source = "backfill"
    interval, fb_action, fb_basis = apply_feedback_input(interval,
                                                         feedback_rate)
    if rounds_present:
        due = now_dt >= last_ts + timedelta(seconds=interval)
        due_reason = "spacing elapsed" if due else "spacing not elapsed"
    else:
        due = True
        due_reason = "no standing round"
    return {
        "present": rounds_present,
        "roundCount": len(rows),
        "lastRoundId": last_id,
        "lastTs": last_ts.strftime(TS_FORMAT) if last_ts else None,
        "intervalSeconds": interval,
        "source": source,
        "feedbackAction": fb_action,
        "feedbackBasis": fb_basis,
        "due": due,
        "dueReason": due_reason,
    }


def tier_face(autonomy, state):
    """The tier-B auto gear face: autonomy mode plus the admitted roster."""
    mode = autonomy.get("mode")
    admitted = False
    basis = None
    for row in (state.get("admitted_classes") or []):
        if isinstance(row, dict) and row.get("class") == CLASS_JARGON:
            admitted = True
            basis = row.get("basis")
            break
    return {
        "class": CLASS_JARGON,
        "autonomyMode": mode,
        "gearAuto": mode == "auto",
        "classAdmitted": admitted,
        "admittedBasis": basis,
    }


def gate_face(marker_path):
    """The EF all-green marker gate (a data state; this face never fires)."""
    if not marker_path:
        return {"markerPath": None, "present": False, "open": False,
                "reason": "no marker path given"}
    if not os.path.isfile(marker_path):
        return {"markerPath": marker_path, "present": False, "open": False,
                "reason": "marker absent"}
    with open(marker_path, encoding="utf-8", errors="replace") as fh:
        first = (fh.readline() or "").strip()
    if not first:
        return {"markerPath": marker_path, "present": True, "open": False,
                "reason": "marker first line is empty"}
    return {"markerPath": marker_path, "present": True, "open": True,
            "reason": "marker first line non-empty"}


def build_plan(now_text, gap_signal, cadence, tier, gate, threshold,
               scheduling_input):
    """Assemble the plan document and decide the verdict (pure assembly)."""
    reasons = []
    if not gap_signal["triggered"]:
        verdict = VERDICT_QUIET
    else:
        if not gate["open"]:
            reasons.append("ef-gate-closed")
        if not tier["gearAuto"]:
            reasons.append("autonomy-gated")
        if not tier["classAdmitted"]:
            reasons.append("class-not-admitted")
        if not cadence["due"]:
            reasons.append("cadence-not-due")
        verdict = VERDICT_DUE if not reasons else VERDICT_BLOCKED
    return {
        "schema": SCHEMA,
        "tool": {"name": PROG, "version": TOOL_VERSION},
        "now": now_text,
        "gapSignal": gap_signal,
        "cadence": cadence,
        "tierB": tier,
        "efGate": gate,
        "schedulingInput": scheduling_input,
        "verdict": verdict,
        "fireReady": verdict == VERDICT_DUE,
        "reasons": reasons,
        "ignitePipeline": [IGNITE_STEP_1, IGNITE_STEP_2],
        "dryRun": True,
    }


def render_line(plan):
    """One human summary line (the non-json stdout face)."""
    gap = plan["gapSignal"]
    cad = plan["cadence"]
    tier = plan["tierB"]
    return ("scheduler-lite plan: verdict=%s todoSeat=%d/%d cadence=%s %ds "
            "due=%s gear=%s class=%s admitted=%s gate=%s feedback=%s "
            "(dry-run only; no ignition face)" % (
                plan["verdict"], gap["todoSeatTotal"], gap["threshold"],
                cad["source"], cad["intervalSeconds"],
                str(cad["due"]).lower(), tier["autonomyMode"], tier["class"],
                str(tier["classAdmitted"]).lower(),
                "open" if plan["efGate"]["open"] else "closed",
                plan["schedulingInput"]["action"]))


def plan_bytes(plan):
    """Canonical plan bytes (json sort_keys, trailing newline)."""
    return (json.dumps(plan, sort_keys=True, ensure_ascii=False,
                       indent=2) + "\n").encode("utf-8")


def run_plan(args):
    """The plan face: read inputs, decide, print, optionally write --out."""
    try:
        now_dt, now_text = now_from_args(args.now_utc)
    except SchedulerInputError:
        fail("--now-utc must be in %s form" % TS_FORMAT, 2)
    if args.threshold < 0:
        fail("--threshold must be >= 0", 2)
    interval_override = (args.interval_seconds
                         if args.interval_seconds is not None
                         else DEFAULT_INTERVAL_SECONDS)
    try:
        rounds_paths, rounds_present, _ = \
            resolve_member_paths(args.rounds, DEFAULT_ROUNDS, "rounds")
        rows = read_jsonl_rows(rounds_paths[0]) if rounds_present else []
        autonomy_paths, autonomy_present, _ = \
            resolve_member_paths(args.autonomy, DEFAULT_AUTONOMY, "autonomy")
        autonomy = read_json_doc(autonomy_paths[0]) if autonomy_present else {}
        state_paths, state_present, _ = \
            resolve_member_paths(args.state, DEFAULT_STATE, "state")
        state = read_json_doc(state_paths[0]) if state_present else {}
        gap_signal = gap_face(args.gap_ledger, args.reports, args.threshold)
        # The standing feedback-consumption path: the approval rate rides
        # the cadence decision (the gear amends the interval inside the
        # face, before the due test), and the applied influence rides the
        # plan document (schedulingInput) so every influence stays
        # traceable.
        feedback = feedback_face(args.feedback)
        cadence = cadence_face(rows, now_dt, interval_override,
                               feedback["approvalRateAuto"])
        scheduling_input = {
            "approvalRateAuto": feedback["approvalRateAuto"],
            "feedbackPresent": feedback["present"],
            "source": feedback["source"],
            "action": cadence["feedbackAction"],
            "basis": cadence["feedbackBasis"],
        }
    except SchedulerInputError as exc:
        fail(str(exc), 9)
    tier = tier_face(autonomy, state)
    gate = gate_face(args.ef_marker)
    plan = build_plan(now_text, gap_signal, cadence, tier, gate,
                      args.threshold, scheduling_input)
    payload = plan_bytes(plan)
    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(payload)
    if args.json:
        sys.stdout.buffer.write(payload)
    else:
        sys.stdout.write(render_line(plan) + "\n")
    return 0


# ------------------------------------------------------------ selftest ----

def selftest():
    """Fixture vectors on tmp inputs; fail loud, one line per vector."""
    import shutil
    import subprocess
    import tempfile

    tool = os.path.abspath(__file__)
    failures = []

    def check(name, fn):
        try:
            fn()
        except Exception as exc:  # vector boundary: report, do not raise
            failures.append("%s -- %s: %r" % (name, type(exc).__name__, exc))
        else:
            print("PASS %s" % name)

    def run_cli(argv, now="2026-11-17T00:00:00Z", out_name="plan.json"):
        out = os.path.join(TMP, out_name)
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool]
            + [str(a) for a in argv]
            + ["--json", "--out", out, "--now-utc", now],
            capture_output=True)
        plan = None
        if os.path.isfile(out):
            with open(out, "rb") as fh:
                plan = json.loads(fh.read().decode("utf-8"))
        return proc, plan, out

    def write(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def drop_flag(argv, name):
        """Remove one value-taking flag with its value from an argv copy."""
        out = []
        skip = False
        for item in argv:
            if skip:
                skip = False
                continue
            if item == name:
                skip = True
                continue
            out.append(item)
        return out

    # Fixtures mirror the repo shapes: the real docs/round-ledger.jsonl
    # tail pair (the measured 40566 s backfill source), one gap feed
    # entry in the bus_feeder recognition shape, the standing gear config.
    GAP_LINE = json.dumps({
        "schema": "rocqwash-exp/1", "id": "fix-001", "ts": "T0",
        "tool": "fixture", "batch": "b",
        "points": "uncovered face (TODO-SEAT counted, no silent "
                  "degradation): ineq.demo @ D:/fix/x.lean",
        "evidence": "status=todo_seat", "fingerprint": "4" * 64}) + "\n"
    ROUND_ROWS = (
        json.dumps({"schema": "rocqwash-round/1", "round_id": 1,
                    "timestamp_utc": "2026-11-15T04:49:24Z",
                    "verify_rc": 0, "mode": "auto"}) + "\n"
        + json.dumps({"schema": "rocqwash-round/1", "round_id": 2,
                      "timestamp_utc": "2026-11-15T16:05:30Z",
                      "verify_rc": 0, "mode": "auto"}) + "\n")
    AUTONOMY = json.dumps({"mode": "auto", "admission_threshold": 0.8}) + "\n"
    STATE = json.dumps({"schema": "rocqwash.round-state/1",
                        "admitted_classes": [
                            {"class": "jargon", "confidence": 1.0,
                             "basis": "fixture gear auto"}]}) + "\n"
    # The standing feedback face at the measured rate (the real repo
    # reading at ticket-B time): the cadence stays current, so the
    # standing vectors keep their verdicts hermetically regardless of
    # the repository's own docs/scheduling-feedback.json state.
    FEEDBACK_OK = json.dumps({"schema": "rocqwash.scheduling-feedback/1",
                              "rounds": {"total": 2, "auto": 1,
                                         "human_approved": 1,
                                         "approval_rate_auto": 0.5,
                                         "by_class": [], "errors": []}},
                             sort_keys=True) + "\n"
    TMP = tempfile.mkdtemp(prefix="scheduler_lite_selftest_")

    def all_green():
        ledger = os.path.join(TMP, "gap.jsonl")
        rounds = os.path.join(TMP, "rounds.jsonl")
        marker = os.path.join(TMP, "ef-done.marker")
        autonomy = os.path.join(TMP, "autonomy.json")
        state = os.path.join(TMP, "state.json")
        feedback = os.path.join(TMP, "feedback.json")
        write(ledger, GAP_LINE)
        write(rounds, ROUND_ROWS)
        write(marker, "abcdef1234567890\n")
        write(autonomy, AUTONOMY)
        write(state, STATE)
        write(feedback, FEEDBACK_OK)
        return ["--gap-ledger", ledger, "--rounds", rounds,
                "--ef-marker", marker, "--autonomy", autonomy,
                "--state", state, "--feedback", feedback]

    def v_due():
        proc, plan, _ = run_cli(all_green())
        assert proc.returncode == 0, proc.stderr[-300:]
        assert plan["verdict"] == "due", plan["verdict"]
        assert plan["fireReady"] is True and plan["reasons"] == [], plan
        assert plan["cadence"]["source"] == "measured", plan["cadence"]
        assert plan["cadence"]["intervalSeconds"] == 40566, plan["cadence"]
        assert plan["cadence"]["due"] is True, plan["cadence"]
        assert plan["dryRun"] is True, plan
        assert plan["efGate"]["open"] is True, plan["efGate"]

    def v_quiet():
        argv = all_green()
        write(os.path.join(TMP, "gap.jsonl"), "")
        proc, plan, _ = run_cli(argv)
        assert proc.returncode == 0, proc.stderr[-300:]
        assert plan["verdict"] == "quiet", plan["verdict"]
        assert plan["fireReady"] is False, plan
        assert plan["gapSignal"]["todoSeatTotal"] == 0, plan["gapSignal"]

    def v_threshold():
        argv = all_green()
        write(os.path.join(TMP, "gap.jsonl"), GAP_LINE + GAP_LINE)
        proc, plan, _ = run_cli(argv + ["--threshold", "3"])
        assert plan["verdict"] == "quiet", plan["verdict"]
        proc, plan, _ = run_cli(argv + ["--threshold", "2"])
        assert plan["verdict"] == "due", plan["verdict"]
        assert plan["gapSignal"]["todoSeatTotal"] == 2, plan["gapSignal"]

    def v_report_face():
        argv = all_green()
        write(os.path.join(TMP, "gap.jsonl"), "")
        rdir = os.path.join(TMP, "reports")
        os.mkdir(rdir)
        report = {"reportId": "run-1", "assumptions": [
            {"kind": "assumption", "name": "s", "typeHead": "(3 / 4) < t.re",
             "status": "todo_seat", "familyId": None, "confidence": None,
             "matchedTarget": None, "degraded": None}]}
        write(os.path.join(rdir, "run-1.json"), json.dumps(report))
        proc, plan, _ = run_cli(argv + ["--reports", rdir])
        assert plan["gapSignal"]["reportTodoSeat"] == 1, plan["gapSignal"]
        assert plan["gapSignal"]["todoSeatTotal"] == 1, plan["gapSignal"]
        assert plan["verdict"] == "due", plan["verdict"]

    def v_cadence_not_due():
        proc, plan, _ = run_cli(all_green(), now="2026-11-15T20:00:00Z")
        assert plan["verdict"] == "blocked", plan["verdict"]
        assert plan["reasons"] == ["cadence-not-due"], plan["reasons"]
        assert plan["cadence"]["due"] is False, plan["cadence"]

    def v_gate_closed():
        argv = drop_flag(all_green(), "--ef-marker")
        argv += ["--ef-marker", os.path.join(TMP, "absent.marker")]
        proc, plan, _ = run_cli(argv)
        assert plan["verdict"] == "blocked", plan["verdict"]
        assert "ef-gate-closed" in plan["reasons"], plan["reasons"]
        assert plan["efGate"]["present"] is False, plan["efGate"]

    def v_class_not_admitted():
        argv = all_green()
        write(os.path.join(TMP, "state.json"),
              json.dumps({"schema": "rocqwash.round-state/1",
                          "admitted_classes": []}) + "\n")
        proc, plan, _ = run_cli(argv)
        assert "class-not-admitted" in plan["reasons"], plan["reasons"]

    def v_autonomy_gated():
        argv = all_green()
        write(os.path.join(TMP, "autonomy.json"),
              json.dumps({"mode": "gated"}) + "\n")
        proc, plan, _ = run_cli(argv)
        assert "autonomy-gated" in plan["reasons"], plan["reasons"]

    def v_backfill_single_row():
        argv = all_green()
        write(os.path.join(TMP, "rounds.jsonl"), ROUND_ROWS.splitlines(True)[0])
        proc, plan, _ = run_cli(argv)
        assert plan["cadence"]["source"] == "backfill", plan["cadence"]
        assert plan["cadence"]["intervalSeconds"] == 40566, plan["cadence"]
        assert plan["cadence"]["due"] is True, plan["cadence"]

    def v_no_standing_round():
        argv = drop_flag(all_green(), "--rounds")
        argv += ["--rounds", os.path.join(TMP, "empty-rounds.jsonl")]
        write(os.path.join(TMP, "empty-rounds.jsonl"), "")
        proc, plan, _ = run_cli(argv)
        assert proc.returncode == 0, proc.stderr[-300:]
        assert plan["cadence"]["present"] is False, plan["cadence"]
        assert plan["cadence"]["due"] is True, plan["cadence"]
        assert plan["cadence"]["dueReason"] == "no standing round", plan

    def v_explicit_absent_exit9():
        argv = drop_flag(all_green(), "--rounds")
        argv += ["--rounds", os.path.join(TMP, "absent.jsonl")]
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool] + argv
            + ["--json", "--now-utc", "2026-11-17T00:00:00Z"],
            capture_output=True)
        assert proc.returncode == 9, proc.returncode
        argv2 = drop_flag(all_green(), "--gap-ledger")
        argv2 += ["--gap-ledger", os.path.join(TMP, "absent.jsonl")]
        proc2 = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool] + argv2
            + ["--json", "--now-utc", "2026-11-17T00:00:00Z"],
            capture_output=True)
        assert proc2.returncode == 9, proc2.returncode

    def v_corrupt_exit9():
        argv = all_green()
        write(os.path.join(TMP, "rounds.jsonl"), "{not json}\n")
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool] + argv
            + ["--json", "--now-utc", "2026-11-17T00:00:00Z"],
            capture_output=True)
        assert proc.returncode == 9, proc.returncode

    def v_determinism():
        argv = all_green()
        _, _, out1 = run_cli(argv, out_name="plan1.json")
        _, _, out2 = run_cli(argv, out_name="plan2.json")
        with open(out1, "rb") as fh:
            first = fh.read()
        with open(out2, "rb") as fh:
            second = fh.read()
        assert first == second, "plan bytes differ across reruns"

    def v_zero_writes():
        argv = all_green()
        ledger = os.path.join(TMP, "gap.jsonl")
        with open(ledger, "rb") as fh:
            before = fh.read()
        run_cli(argv, out_name="plan3.json")
        with open(ledger, "rb") as fh:
            after = fh.read()
        assert before == after, "fixture ledger was modified"

    def v_ignite_is_informational():
        proc, plan, _ = run_cli(all_green(), out_name="plan4.json")
        pipe = plan["ignitePipeline"]
        assert len(pipe) == 2, pipe
        assert all(isinstance(s, str) and s.startswith("py -I")
                   for s in pipe), pipe
        assert plan["dryRun"] is True and plan["fireReady"] is True, plan

    # Synthetic consumer sources for the edge selfscan (fixture text judged
    # by the sibling grader; they live inside this selftest face, so a scan
    # of this module's runtime faces never sees them as evidence).
    DEAD_EDGE_SOURCE = (
        "DEFAULT_PATH = ('docs', 'feedback-absent.json')\n"
        "\n"
        "def plan_face(args):\n"
        "    return {'verdict': 'quiet'}\n")
    SELFTEST_ONLY_EDGE_SOURCE = (
        "def selftest():\n"
        "    def feedback_face(flagged):\n"
        "        doc = read_json_doc(flagged[0])\n"
        "        return doc.get('rounds', {}).get('approval_rate_auto')\n"
        "\n"
        "    def apply_feedback_input(interval, rate):\n"
        "        return interval * 2, 'cadence-interval-x2'\n"
        "\n"
        "    def run_plan(args):\n"
        "        rate = feedback_face(args.feedback)\n"
        "        interval, action = apply_feedback_input(60, rate)\n"
        "        return {'schedulingInput': {'rate': rate}}\n")

    def feedback_doc(rate):
        return json.dumps({"schema": "rocqwash.scheduling-feedback/1",
                           "rounds": {"total": 4, "auto": 1,
                                      "human_approved": 3,
                                      "approval_rate_auto": rate,
                                      "by_class": [], "errors": []}},
                          sort_keys=True) + "\n"

    def v_feedback_downshift_flips_due():
        # The consumption rule bites on the decision: at the same clock a
        # rate below 0.5 doubles the interval and flips due to blocked,
        # while the measured-rate control stays due.
        argv = all_green()
        write(os.path.join(TMP, "feedback.json"), feedback_doc(0.25))
        proc, plan, _ = run_cli(argv, now="2026-11-16T08:00:00Z")
        assert proc.returncode == 0, proc.stderr[-300:]
        assert plan["verdict"] == "blocked" \
            and plan["reasons"] == ["cadence-not-due"], plan
        assert plan["cadence"]["intervalSeconds"] == 81132, plan["cadence"]
        assert plan["cadence"]["feedbackAction"] == "cadence-interval-x2", \
            plan["cadence"]
        si = plan["schedulingInput"]
        assert si["approvalRateAuto"] == 0.25 \
            and si["action"] == "cadence-interval-x2" \
            and si["feedbackPresent"] is True \
            and si["source"] == os.path.join(TMP, "feedback.json"), si
        write(os.path.join(TMP, "feedback.json"), FEEDBACK_OK)
        proc2, plan2, _ = run_cli(argv, now="2026-11-16T08:00:00Z")
        assert plan2["verdict"] == "due" and plan2["fireReady"] is True, \
            plan2["verdict"]
        assert plan2["cadence"]["intervalSeconds"] == 40566, plan2["cadence"]
        assert plan2["cadence"]["feedbackAction"] == "cadence-current", \
            plan2["cadence"]

    def v_feedback_rate_forms_current_and_null():
        # 0.5 and up keeps the measured cadence; the null rate (the real
        # zero-round shape the feedback writer casts) is a data state that
        # keeps the cadence and says so in the basis.
        argv = all_green()
        write(os.path.join(TMP, "feedback.json"), feedback_doc(0.8))
        proc, plan, _ = run_cli(argv, now="2026-11-16T08:00:00Z")
        assert plan["verdict"] == "due", plan["verdict"]
        assert plan["cadence"]["intervalSeconds"] == 40566, plan["cadence"]
        assert plan["schedulingInput"]["action"] == "cadence-current", plan
        write(os.path.join(TMP, "feedback.json"), feedback_doc(None))
        proc2, plan2, _ = run_cli(argv)
        assert plan2["verdict"] == "due", plan2["verdict"]
        si = plan2["schedulingInput"]
        assert si["approvalRateAuto"] is None \
            and si["action"] == "cadence-current" \
            and "unreadable" in si["basis"], si

    def v_feedback_bad_exit9():
        # Corrupt bytes, a doc without the rounds face, a non-numeric rate,
        # and an explicitly flagged absent path all fail loud exit 9.
        argv = all_green()
        write(os.path.join(TMP, "feedback.json"), "{not json}\n")
        proc, _, _ = run_cli(argv)
        assert proc.returncode == 9, proc.returncode
        write(os.path.join(TMP, "feedback.json"),
              json.dumps({"schema": "rocqwash.scheduling-feedback/1"}) + "\n")
        proc, _, _ = run_cli(argv)
        assert proc.returncode == 9, proc.returncode
        write(os.path.join(TMP, "feedback.json"),
              json.dumps({"rounds": {"approval_rate_auto": "high"}}) + "\n")
        proc, _, _ = run_cli(argv)
        assert proc.returncode == 9, proc.returncode
        absent = drop_flag(argv, "--feedback")
        absent += ["--feedback", os.path.join(TMP, "absent-feedback.json")]
        proc, _, _ = run_cli(absent)
        assert proc.returncode == 9, proc.returncode

    def v_edge_selfscan_kill_face():
        # The kill-test vector, standing: this module's own source grades
        # live (read + apply edge + record, no trace in the tmp ledger ->
        # partial), while a dead source (call sites commented out) and a
        # markers-only-inside-selftest source grade open.  When the real
        # consumption path is commented out for the kill test, the own-
        # source assertion here goes red.
        try:
            lf = learning_feedback_module()
        except SystemExit as exc:
            raise AssertionError("sibling learning_feedback unavailable:"
                                 " %r" % (exc,))
        empty_rounds = os.path.join(TMP, "edge-rounds.jsonl")
        write(empty_rounds, "")
        own = lf.feedback_edge_grade(os.path.abspath(__file__), empty_rounds)
        assert own["status"] == "partial", own
        assert own["read"] is True and own["apply_edge"] is True \
            and own["record"] is True and own["ledger_trace"] is False, own
        dead = os.path.join(TMP, "dead_scheduler.py")
        write(dead, DEAD_EDGE_SOURCE)
        grade_dead = lf.feedback_edge_grade(dead, empty_rounds)
        assert grade_dead["status"] == "open" and grade_dead["read"] is False, \
            grade_dead
        stonly = os.path.join(TMP, "selftest_only_scheduler.py")
        write(stonly, SELFTEST_ONLY_EDGE_SOURCE)
        grade_st = lf.feedback_edge_grade(stonly, empty_rounds)
        assert grade_st["status"] == "open" and grade_st["read"] is False, \
            grade_st

    def v_edge_live_trace_closed():
        # The closed-side vector, standing: this module's own source (a
        # live consumption path) over a round-ledger row carrying the
        # scheduling_input trace grades closed with the row counted; the
        # same source over a row whose trace carries no readable rate
        # stays below closed.  When the real consumption path is
        # commented out for the kill test, this vector goes red together
        # with the kill-face vector above.
        try:
            lf = learning_feedback_module()
        except SystemExit as exc:
            raise AssertionError("sibling learning_feedback unavailable:"
                                 " %r" % (exc,))
        traced = os.path.join(TMP, "edge-traced-rounds.jsonl")
        write(traced, json.dumps({
            "schema": "rocqwash-round/1", "round_id": 1, "mode": "auto",
            "verify_rc": 0, "classes_applied": ["jargon"],
            "admissions": [],
            "scheduling_input": {"approval_rate_auto": 0.25,
                                 "action": "cadence-interval-x2",
                                 "basis": "fixture"}}, sort_keys=True) + "\n")
        own = lf.feedback_edge_grade(os.path.abspath(__file__), traced)
        assert own["status"] == "closed", own
        assert own["read"] is True and own["apply_edge"] is True \
            and own["record"] is True and own["ledger_trace"] is True \
            and own["trace_rows"] == 1, own
        untraced = os.path.join(TMP, "edge-untraced-rounds.jsonl")
        write(untraced, json.dumps({
            "schema": "rocqwash-round/1", "round_id": 1, "mode": "auto",
            "verify_rc": 0, "classes_applied": ["jargon"],
            "admissions": [],
            "scheduling_input": {"approval_rate_auto": None,
                                 "action": "cadence-current"}},
            sort_keys=True) + "\n")
        own2 = lf.feedback_edge_grade(os.path.abspath(__file__), untraced)
        assert own2["status"] == "partial" and own2["trace_rows"] == 0, own2

    def v_source_language_surface():
        with open(tool, encoding="utf-8") as fh:
            text = fh.read()
        assert not _CJK_RE.search(text), "CJK found in source"
        assert _EM_DASH not in text, "em-dash found in source"

    try:
        check("due-all-green-measured-cadence", v_due)
        check("quiet-zero-gaps", v_quiet)
        check("threshold-override", v_threshold)
        check("vacgen-report-todo-seat-face", v_report_face)
        check("cadence-not-due-reason", v_cadence_not_due)
        check("ef-gate-closed-reason", v_gate_closed)
        check("class-not-admitted-reason", v_class_not_admitted)
        check("autonomy-gated-reason", v_autonomy_gated)
        check("backfill-single-row", v_backfill_single_row)
        check("no-standing-round-data-state", v_no_standing_round)
        check("explicit-absent-exit9", v_explicit_absent_exit9)
        check("corrupt-input-exit9", v_corrupt_exit9)
        check("determinism-fixed-now", v_determinism)
        check("zero-write-posture", v_zero_writes)
        check("ignite-pipeline-informational", v_ignite_is_informational)
        check("feedback-downshift-flips-due", v_feedback_downshift_flips_due)
        check("feedback-rate-forms-current-and-null",
              v_feedback_rate_forms_current_and_null)
        check("feedback-corrupt-malformed-explicit-absent-exit9",
              v_feedback_bad_exit9)
        check("feedback-edge-selfscan-kill-face", v_edge_selfscan_kill_face)
        check("feedback-edge-live-trace-closed", v_edge_live_trace_closed)
        check("source-cjk-free-em-dash-free", v_source_language_surface)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    if failures:
        for line in failures:
            sys.stdout.write("FAIL %s\n" % line)
        return 1
    return 0


# ------------------------------------------------------------------ main ----

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="TODO-SEAT threshold trigger face for the jargon "
                    "tier-B auto gear (dry-run planner; no ignition face)")
    parser.add_argument("command", nargs="?", default="plan",
                        choices=("plan",), help="the plan face (default)")
    parser.add_argument("--gap-ledger", action="append", default=[],
                        metavar="PATH",
                        help="gap feed ledger input (repeatable; default "
                             "docs/gap-feed-ledger.jsonl)")
    parser.add_argument("--reports", action="append", default=[],
                        metavar="PATH",
                        help="vacgen report file or directory (repeatable; "
                             "default docs/vacgen-reports)")
    parser.add_argument("--rounds", action="append", default=[],
                        metavar="PATH",
                        help="round ledger (default docs/round-ledger.jsonl)")
    parser.add_argument("--autonomy", action="append", default=[],
                        metavar="PATH",
                        help="autonomy gear config (default autonomy.json)")
    parser.add_argument("--state", action="append", default=[],
                        metavar="PATH",
                        help="round state roster (default "
                             "docs/round-state.json)")
    parser.add_argument("--feedback", default=None, metavar="PATH",
                        help="scheduling feedback document (default "
                             "docs/scheduling-feedback.json; the standing "
                             "approval-rate input the cadence consumes)")
    parser.add_argument("--ef-marker", default=None, metavar="PATH",
                        help="EF all-green marker file (the ignition gate)")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                        metavar="N",
                        help="TODO-SEAT trigger threshold (default %d)"
                             % DEFAULT_THRESHOLD)
    parser.add_argument("--interval-seconds", type=int, default=None,
                        metavar="N",
                        help="round spacing override (default: the measured "
                             "backfill %d s)" % DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--now-utc", default=None, metavar="ISO8601Z",
                        help="plan clock override (default: real UTC now)")
    parser.add_argument("--out", default=None, metavar="FILE",
                        help="plan output file (the only write face)")
    parser.add_argument("--json", action="store_true",
                        help="print the plan document on stdout")
    args = parser.parse_args(argv)
    # One member per single-file face keeps the resolution rules simple;
    # repeats beyond the first are a usage error rather than a silent pick.
    for flag in ("rounds", "autonomy", "state"):
        if len(getattr(args, flag)) > 1:
            parser.error("--%s takes one path" % flag)
    return run_plan(args)


if __name__ == "__main__":
    sys.exit(main())
