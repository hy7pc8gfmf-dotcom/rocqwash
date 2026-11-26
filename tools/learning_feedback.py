#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning_feedback.py - scheduling feedback face over the three standing ledgers.
Purpose.  Read the round ledger, the round state, and the experience
  ledger strictly read-only, and cast the scheduling feedback face
  (schema rocqwash.scheduling-feedback/1) into docs/scheduling-feedback.json:
  the round admission face, the repair outcome face, the optional
  calibration reading, and the computed feedback edge (closed / partial
  / open, never hard-coded).  The opt-in --promote scan appends promotion
  event rows (rocqwash-exp/1+promotion) into docs/exp-ledger.jsonl through
  the sibling exp_port seen set (append-only, idempotent).  Missing or
  corrupt inputs land in the per-account "errors" list, never guessed;
  the run continues on the remaining valid rows and exits 1.
Interface.  `python -I tools/learning_feedback.py [--selftest]
  [--promote] [--ledger P] [--ts TS] [--actor A] [--dry-run]`; the
  default run writes exactly one file, docs/scheduling-feedback.json
  (the three inputs are never written); --promote appends the promotion
  event rows (extended contract below).
Dependencies.  Python 3 stdlib only; zero network; zero eval/exec;
  deterministic default run (--promote stamps the supplied or current UTC
  time); sibling imports exp_port (seen set, ledger resolution, line form)
  and b_gate_audit (the ready verdict, imported, never re-implemented);
  the feedback edge AST-scans tools/scheduler_lite.py (the standing
  consumer, comment-proof: a parsed source carries no comments).
Evidence.  --selftest on temporary fixtures, fourteen vectors: the eight
  standing faces plus the promotion row lock, the exp_port interop, and
  the four feedback-edge faces (closed, partial, open-kill-shape and
  tolerant-absent).
Exit-codes.  0 = face produced / promotion scan clean (appends and skips
  are both clean); 1 = at least one account error or a write failure,
  named on stdout; 2 = usage error.
"""

# Field notes (the reading rules this tool implements; consumers of the
# scheduling-feedback JSON rely on these exact definitions):
# - rounds.total counts valid round-ledger rows.  auto counts rounds with at
#   least one admission whose decision is "admitted" (the auto gear).
#   human_approved counts rounds with no admitted admission whose applied
#   classes carry a human approval in the round state (the basis names a
#   human approval).  A round with neither stays in total only (a rollback
#   or salvage shape is data, not an error).
# - approval_rate_auto = auto / total; the denominator includes
#   human-approved rounds; None when total is 0; rounded to 4 decimals.
# - by_class: one entry per class seen in classes_applied, sorted by name.
#   gear is "auto" when the class entered through an admitted admission,
#   "human" when it entered through a human-approved round-state entry, and
#   "mixed" (plus an error line) when both paths occur.  confidence comes
#   from the admission for auto and from the round-state entry for human;
#   null stays null, never guessed.
# - repair_outcomes classify each valid experience-ledger row by the action
#   vocabulary inside its points text: "action=fix-content" -> repaired;
#   "action=restore-toolchain" or "action=rerun-after-stable-window" ->
#   repaired (the mechanical-fix family: a toolchain restore and the
#   post-window rerun are repairs of the red run, not observations);
#   "action=escalated" or "action=escalate" -> escalated;
#   "action=watch-only" or "action=queue-etiquette" ->
#   watch_only_guard_correct (queue-etiquette: the D-queue-wall run
#   never executed its steps, nothing content-level was repaired).  Any
#   other row (including rows without an action token) stays unrecorded.
#   The vocabulary mirrors the outcome words the repair ledger already
#   uses; a row outside it is never forced into a state (honest
#   unrecorded, no filling).
# - repair_action_rate = repaired / total valid rows; None when total is 0.
# - calibration (optional section): the rows of the experience ledger whose
#   tool field equals "calibration_ledger" (the calibration writer
#   tools/calibration_ledger.py; its ledger path and row schema are consumed
#   read-only here).  ledger_present is true when the ledger file exists and
#   holds at least one valid row of any tool; an absent file or a row-empty
#   file reports false with null readings (stated, never padded).  entries
#   counts the calibration rows.  Each reading parses the row's points text
#   for the predicted grade (HIGH or MID) and the measured face (PASS or
#   FAIL); an entry agrees when the predicted value (HIGH=1.0, MID=0.5)
#   equals the measured value (PASS=1.0, FAIL=0.0), so a MID row cannot
#   agree at value level by construction and a HIGH row measured FAIL is
#   the rot shape.  agreement_rate = agreeing / readable entries, rounded
#   to 4 decimals, None when no entry is readable.  by_class groups by the
#   predicted grade (the calibration writer's two taxonomy confidence
#   grades), sorted by name.  A calibration row whose points text carries
#   no readable pair stays counted in entries, is excluded from the
#   readings, and is named in errors (fail loud, never swallowed).
# - feedback_edge (computed, never hard-coded): three states over the
#   standing consumer tools/scheduler_lite.py.  closed = the scheduler
#   live-reads approval_rate_auto, applies it to the round cadence, records
#   every influence, AND at least one round-ledger row carries the trace
#   (a scheduling_input object with approval_rate_auto and a non-empty
#   action); partial = the consumption is live at the plan face but the
#   face is a subset (the per-influence record site or the ledger trace
#   is missing); open = no live consumption (the kill-test state).  The
#   scan is mechanical and comment-proof: the scheduler source is parsed
#   with ast (comments never survive a parse), the declared selftest face
#   is excluded (fixture keys there are test data, not consumption), and
#   the evidence is the consumption constants plus the apply call edge
#   (a dead definition with its call sites commented out scans absent).
#   An absent or unparseable scheduler source scans absent (the consumer
#   is not there) and is stated in the note, never an error; the edge
#   face itself carries no errors list.
# - scheduling_input (the round-row trace contract): the influence record
#   a round-ledger row carries for a round steered by the scheduler:
#   {"approval_rate_auto": <num|null>, "action": <str>, "basis": <str>}.
#   The trace scan accepts only rows that are round rows (round_id and
#   mode present) whose scheduling_input is such an object with a
#   non-null rate and a non-empty action; anything else, including a
#   ledger no writer has traced yet, leaves the trace count untouched.
# - errors: per-account strings in deterministic order; an empty list is a
#   clean account.

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
#
# Event model (--promote; the promotion event output face).  One event per
#   admitted (round, class) pair, walked in round-ledger file order
#   (same-round duplicate admission entries collapse), then one event per
#   class whose b-gate count verifies ready (instances >= 3 and
#   rounds >= 1), sorted by class.  The ready verdict comes from the
#   sibling b_gate_audit build_report (imported, never re-implemented),
#   so the promotion face moves exactly with the gate.  Event ids are
#   deterministic: promotion-round-<round_id>-<class> and
#   promotion-class-ready-<class>.  A rescan of an unchanged ledger
#   recasts the same ids and every one lands on the exp_port seen set as
#   a duplicate-skip (id axis first, then the four-carrier fingerprint
#   axis), so reruns are append-only no-ops.
#
# Row shape (schema increment rocqwash-exp/1+promotion, the D1-1
#   "+reading" form; the base envelope matches exp_port so the seen set
#   owns dedupe on both axes):
#   schema       constant "rocqwash-exp/1+promotion"
#   kind         constant "promotion"
#   id           the deterministic event id above
#   ts           the scan stamp (caller-supplied or current UTC)
#   tool         constant "learning_feedback" (the writer)
#   points       one-line mechanical takeaway of the event
#   evidence     the grounding pointers: "round-ledger line N (round_id
#                R)" for admissions (one pointer); for a ready class the
#                admitting-row pointers joined with "; "
#   batch        constant "promotion-events"
#   fingerprint  exp_port.fingerprint over tool/points/evidence/batch,
#                byte-compatible with the exp_port seen set (the interop
#                vector appends through exp_port itself)
#   source_sha   md5 of the round-ledger bytes at scan time (the moving
#                grounding; state and taxonomy are named in basis)
#   basis        the derivation sentence (the source_sha/basis
#                self-certifying contract per D1-1/D3-3)
#   actor        carried verbatim when provided, omitted when empty
#                (exp_port schema increment; outside the fingerprint)
#
# Failure face.  Any read error (missing input, invalid JSON, non-round
#   row) or a corrupt exp-ledger line fails loud: nothing is appended,
#   exit 1.  --dry-run casts the events and prints the would-be ids,
#   writing nothing.  The default run never writes the three inputs;
#   only --promote writes, and it only appends.
#
# Consumer note.  Promotion rows are rows of the experience ledger, so
#   the repair outcome face counts them (no action token in their points
#   text, so the unrecorded state); the calibration section is unaffected
#   (the tool field differs from calibration_ledger).

import argparse
import ast
import contextlib
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import exp_port
except ImportError as exc:
    sys.stderr.write("learning_feedback: the sibling exp_port module is"
                     " required (%s)\n" % exc)
    sys.exit(9)
try:
    import b_gate_audit
except ImportError as exc:
    sys.stderr.write("learning_feedback: the sibling b_gate_audit module"
                     " is required (%s)\n" % exc)
    sys.exit(9)

PROG = "learning_feedback"
SCHEMA = "rocqwash.scheduling-feedback/1"
TOOL_VERSION = "1.2.0"
ROUNDS_DEFAULT = ("docs", "round-ledger.jsonl")
STATE_DEFAULT = ("docs", "round-state.json")
EXP_DEFAULT = ("docs", "exp-ledger.jsonl")
OUT_DEFAULT = ("docs", "scheduling-feedback.json")
TAXONOMY_DEFAULT = ("tools", "taxonomy.json")
CALIB_TOOL = "calibration_ledger"
CALIB_GRADES = ("HIGH", "MID")
CALIB_FACES = ("PASS", "FAIL")

# Feedback-edge constants (the computed edge; the standing consumer is the
# sibling scheduler, the rules mirror the field notes above).
SCHED_DEFAULT = ("tools", "scheduler_lite.py")
EDGE_RATE_KEY = "approval_rate_auto"
EDGE_DOC_TOKEN = "scheduling-feedback"
EDGE_APPLY_CALL = "apply_feedback_input"
EDGE_RECORD_KEY = "schedulingInput"
EDGE_TRACE_KEY = "scheduling_input"
SELFTEST_FACE_NAME = "selftest"

# Promotion face constants (the opt-in --promote writer; the default run
# never touches these).
PROMOTION_SCHEMA = "rocqwash-exp/1+promotion"
PROMOTION_KIND = "promotion"
PROMOTION_BATCH = "promotion-events"

# The action-token table, in priority order (first match wins).
REPAIR_TOKENS = (
    ("action=fix-content", "repaired"),
    ("action=restore-toolchain", "repaired"),
    ("action=rerun-after-stable-window", "repaired"),
    ("action=escalated", "escalated"),
    ("action=escalate", "escalated"),
    ("action=watch-only", "watch_only_guard_correct"),
    ("action=queue-etiquette", "watch_only_guard_correct"),
)


def _repo_root():
    """The repository root: the parent of the tools/ directory holding this file."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_jsonl(path, label):
    """Read a JSONL ledger -> (rows as (lineno, obj) pairs, errors)."""
    errors = []
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return [], ["%s not found or unreadable: %s (%s)" % (label, path, exc)]
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append("%s line %d: invalid JSON (%s)" % (label, lineno, exc))
            continue
        if not isinstance(obj, dict):
            errors.append("%s line %d: not a JSON object" % (label, lineno))
            continue
        rows.append((lineno, obj))
    return rows, errors


def _read_json(path, label):
    """Read one JSON document -> (obj or None, errors)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), []
    except OSError as exc:
        return None, ["%s not found or unreadable: %s (%s)" % (label, path, exc)]
    except json.JSONDecodeError as exc:
        return None, ["%s invalid JSON: %s (%s)" % (label, path, exc)]


def _basis_is_human(basis):
    """A round-state basis counts as a human approval when it names one."""
    if not isinstance(basis, str):
        return False
    low = basis.lower()
    return "human" in low and "approv" in low


def compute_rounds(rounds_path, state_path):
    """Cast the rounds face from the round ledger plus the round state."""
    errors = []
    rows, read_errors = _read_jsonl(rounds_path, "round-ledger")
    errors.extend(read_errors)

    state = None
    state_rows, state_errors = _read_json(state_path, "round-state")
    errors.extend(state_errors)
    state_map = {}
    if state_rows is not None:
        state = state_rows
    if isinstance(state, dict):
        for entry in state.get("admitted_classes") or []:
            if not isinstance(entry, dict) or not entry.get("class"):
                errors.append("round-state: admitted_classes entry without a"
                              " class skipped")
                continue
            state_map[entry["class"]] = entry
    elif state is not None:
        errors.append("round-state: not a JSON object")

    total = 0
    auto = 0
    human = 0
    classes = {}
    for lineno, row in rows:
        round_id = row.get("round_id")
        if round_id is None or "mode" not in row:
            errors.append("round-ledger line %d: not a round row (missing"
                          " round_id or mode)" % lineno)
            continue
        total += 1
        admissions = row.get("admissions") or []
        admitted = {}
        for adm in admissions:
            if not isinstance(adm, dict):
                errors.append("round-ledger line %d: admission is not an"
                              " object, skipped" % lineno)
                continue
            cls = adm.get("class")
            if not cls:
                errors.append("round-ledger line %d: admission without a"
                              " class, skipped" % lineno)
                continue
            if adm.get("decision") == "admitted":
                admitted[cls] = adm
        applied = row.get("classes_applied") or []
        auto_classes = set(admitted)
        human_classes = set()
        for cls in applied:
            if cls in auto_classes:
                continue
            entry = state_map.get(cls)
            if entry is not None and _basis_is_human(entry.get("basis")):
                human_classes.add(cls)
            else:
                errors.append("round-ledger line %d: class %s has neither an"
                              " admitted admission nor a human-approved"
                              " round-state entry; excluded from by_class"
                              % (lineno, cls))
        if auto_classes:
            auto += 1
        elif human_classes:
            human += 1
        for cls in sorted(auto_classes):
            conf = admitted[cls].get("confidence")
            stats = classes.setdefault(cls, {"rounds": 0, "gears": set(),
                                             "confidence": None})
            stats["rounds"] += 1
            stats["gears"].add("auto")
            if conf is not None:
                stats["confidence"] = conf
        for cls in sorted(human_classes):
            entry = state_map.get(cls)
            conf = entry.get("confidence") if entry else None
            stats = classes.setdefault(cls, {"rounds": 0, "gears": set(),
                                             "confidence": None})
            stats["rounds"] += 1
            stats["gears"].add("human")
            if conf is not None:
                stats["confidence"] = conf
    by_class = []
    for cls in sorted(classes):
        stats = classes[cls]
        gears = stats["gears"]
        if len(gears) == 1:
            gear = sorted(gears)[0]
        else:
            gear = "mixed"
            errors.append("by_class: class %s entered through both gears;"
                          " gear reported as mixed" % cls)
        by_class.append({"class": cls, "rounds": stats["rounds"],
                         "gear": gear, "confidence": stats["confidence"]})
    rate = round(auto / total, 4) if total else None
    return {"total": total, "auto": auto, "human_approved": human,
            "approval_rate_auto": rate, "by_class": by_class,
            "errors": errors}


def compute_repair(exp_rows, read_errors):
    """Cast the repair outcome face from the experience ledger rows."""
    errors = list(read_errors)
    counts = {"repaired": 0, "escalated": 0, "watch_only_guard_correct": 0,
              "unrecorded": 0}
    total = 0
    for _lineno, row in exp_rows:
        total += 1
        points = row.get("points")
        text = points if isinstance(points, str) else ""
        state = "unrecorded"
        for token, name in REPAIR_TOKENS:
            if token in text:
                state = name
                break
        counts[state] += 1
    rate = round(counts["repaired"] / total, 4) if total else None
    face = dict(counts)
    face["repair_action_rate"] = rate
    face["errors"] = errors
    return face


def _calib_face(text, token, values):
    """Read one calibration token (predicted or measured) out of the row's
    points text (word-bounded, order-free); None when the text carries no
    readable value."""
    match = re.search(r"\b%s (%s)\b" % (token, "|".join(values)), text)
    return match.group(1) if match else None


def compute_calibration(exp_rows, ledger_present):
    """Cast the optional calibration reading from the experience ledger
    rows: the entry count, the agreement rate, and the per-grade breakdown
    of the rows written by the calibration tool.  Definitions in the field
    notes above; an unreadable row is named in errors, never swallowed."""
    errors = []
    entries = 0
    readable = 0
    agreeing = 0
    grades = {}
    for lineno, row in exp_rows:
        if row.get("tool") != CALIB_TOOL:
            continue
        entries += 1
        points = row.get("points")
        text = points if isinstance(points, str) else ""
        predicted = _calib_face(text, "predicted", CALIB_GRADES)
        measured = _calib_face(text, "measured", CALIB_FACES)
        if predicted is None or measured is None:
            errors.append(
                "exp-ledger line %d: calibration entry carries no readable"
                " predicted/measured pair in its points text; counted in"
                " entries, excluded from the readings" % lineno)
            continue
        readable += 1
        agree = predicted == "HIGH" and measured == "PASS"
        if agree:
            agreeing += 1
        grade = grades.setdefault(predicted, {"entries": 0, "agreeing": 0})
        grade["entries"] += 1
        if agree:
            grade["agreeing"] += 1
    rate = round(agreeing / readable, 4) if readable else None
    by_class = [{"class": name, "entries": grade["entries"],
                 "agreeing": grade["agreeing"],
                 "agreement_rate": round(grade["agreeing"]
                                         / grade["entries"], 4)}
                for name, grade in sorted(grades.items())]
    return {"section": "calibration",
            "ledger_present": ledger_present,
            "entries": entries,
            "agreement_rate": rate,
            "by_class": by_class,
            "errors": errors}


def _str_constants(tree):
    """Every string constant in the tree (ast walk; comments never reach
    an ast, so a commented-out literal scans absent by construction)."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.add(node.value)
    return found


def _called_names(tree):
    """Every called function name in the tree (plain and attribute calls;
    a dead definition is not a call, so an uncalled consumer scans
    absent)."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                found.add(func.id)
            elif isinstance(func, ast.Attribute):
                found.add(func.attr)
    return found


def scan_scheduler_consumption(source_path):
    """AST-scan the scheduler source for the live feedback-consumption
    chain -> {"scanned", "read", "apply_edge", "record", "detail"}.

    The runtime faces are the module body minus the declared selftest
    face (fixture keys inside a selftest are test data, not consumption;
    its nested helpers never enter the walk because the selftest subtree
    is skipped whole).  Evidence: read = the consumed key and the
    consumed doc token both appear; apply_edge = the influence
    application is called; record = the per-influence record site
    exists.  An absent or unparseable source scans absent with the
    reason in detail (the consumer is not there; stated, never an
    error, never guessed).
    """
    try:
        with open(source_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        # The reason rides without the filesystem path: the detail reaches
        # the tracked face, which must stay free of machine-specific paths.
        reason = getattr(exc, "strerror", None) or type(exc).__name__
        return {"scanned": False, "read": False, "apply_edge": False,
                "record": False,
                "detail": "scheduler source unreadable (%s)" % reason}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"scanned": False, "read": False, "apply_edge": False,
                "record": False,
                "detail": "scheduler source unparseable (%s)" % exc}
    runtime = ast.Module(body=[], type_ignores=[])
    for node in tree.body:
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == SELFTEST_FACE_NAME):
            continue
        runtime.body.append(node)
    strings = _str_constants(runtime)
    calls = _called_names(runtime)
    read = any(s == EDGE_RATE_KEY for s in strings) and any(
        EDGE_DOC_TOKEN in s for s in strings)
    apply_edge = EDGE_APPLY_CALL in calls
    record = any(s == EDGE_RECORD_KEY for s in strings)
    detail = ("consumption constants and the apply call edge found"
              if (read and apply_edge)
              else "no live consumption chain in the runtime faces")
    return {"scanned": True, "read": read, "apply_edge": apply_edge,
            "record": record, "detail": detail}


def scan_ledger_trace(rounds_path):
    """Count round-ledger rows carrying the scheduling_input trace.

    A trace row is a round row (round_id and mode present) whose
    scheduling_input is an object carrying a non-null approval_rate_auto
    and a non-empty action string.  Ledger read errors stay here silent:
    the rounds account above already reports them, and the edge face
    never invents a second account.
    """
    rows, _errors = _read_jsonl(rounds_path, "round-ledger")
    traced = 0
    for _lineno, row in rows:
        if row.get("round_id") is None or "mode" not in row:
            continue
        record = row.get(EDGE_TRACE_KEY)
        if not isinstance(record, dict):
            continue
        rate = record.get("approval_rate_auto")
        action = record.get("action")
        if rate is None or isinstance(rate, bool) \
                or not isinstance(rate, (int, float)):
            continue
        if not isinstance(action, str) or not action:
            continue
        traced += 1
    return traced


def feedback_edge_grade(source_path, rounds_path, source_label=None):
    """Grade the feedback edge from the two carriers (computed, never
    hard-coded): open = no live consumption; partial = live consumption
    with a subset face (record site or ledger trace missing); closed =
    full consumption with the ledger trace landed.  The returned face is
    self-certifying: every boolean input to the grade is carried, so an
    auditor can re-derive the status from the face alone.  source_path is
    what gets scanned; the face reports scheduler_source as source_label
    when given (the default run passes the repo-relative standing path,
    since the face is a tracked artifact), else as source_path."""
    scan = scan_scheduler_consumption(source_path)
    trace_rows = scan_ledger_trace(rounds_path)
    consumed = scan["read"] and scan["apply_edge"]
    if not consumed:
        status = "open"
    elif scan["record"] and trace_rows > 0:
        status = "closed"
    else:
        status = "partial"
    if status == "open":
        note = ("edge open: no live consumption of %s in the scheduler"
                " source (%s); %d round-ledger row(s) carry %s"
                % (EDGE_RATE_KEY, scan["detail"], trace_rows,
                   EDGE_TRACE_KEY))
    elif status == "partial":
        note = ("edge partial: the scheduler consumes %s at the plan face"
                " (read=%s apply=%s record=%s) but the face is a subset;"
                " %d round-ledger row(s) carry %s"
                % (EDGE_RATE_KEY, str(scan["read"]).lower(),
                   str(scan["apply_edge"]).lower(),
                   str(scan["record"]).lower(), trace_rows, EDGE_TRACE_KEY))
    else:
        note = ("edge closed: the scheduler consumes %s (read+apply+record)"
                " and %d round-ledger row(s) carry the %s trace"
                % (EDGE_RATE_KEY, trace_rows, EDGE_TRACE_KEY))
    return {"status": status,
            "scheduler_source": (source_path if source_label is None
                                 else source_label),
            "read": scan["read"],
            "apply_edge": scan["apply_edge"],
            "record": scan["record"],
            "ledger_trace": trace_rows > 0,
            "trace_rows": trace_rows,
            "note": note}


def build_face(rounds_path, state_path, exp_path, scheduler_path=None):
    """Cast the full scheduling feedback face from the input paths (the
    scheduler source defaults to the standing consumer next to this
    file, scanned at its absolute path and reported by its repo-relative
    path so the tracked face carries no machine-specific path; selftests
    always pass an explicit fixture path, which is then reported as
    given)."""
    rounds = compute_rounds(rounds_path, state_path)
    exp_rows, exp_errors = _read_jsonl(exp_path, "exp-ledger")
    repair = compute_repair(exp_rows, exp_errors)
    ledger_present = os.path.isfile(exp_path) and bool(exp_rows)
    calibration = compute_calibration(exp_rows, ledger_present)
    source_label = None
    if scheduler_path is None:
        source_label = os.path.join(*SCHED_DEFAULT)
        scheduler_path = os.path.join(_repo_root(), *SCHED_DEFAULT)
    edge = feedback_edge_grade(scheduler_path, rounds_path, source_label)
    return {"schema": SCHEMA,
            "rounds": rounds,
            "repair_outcomes": repair,
            "calibration": calibration,
            "feedback_edge": edge}


def summarize(face, out_display):
    """One stdout summary block over a computed face."""
    rounds = face["rounds"]
    repair = face["repair_outcomes"]
    calibration = face["calibration"]
    edge = face["feedback_edge"]
    lines = ["scheduling-feedback: schema %s" % SCHEMA,
             "rounds: total=%d auto=%d human_approved=%d approval_rate_auto=%s"
             % (rounds["total"], rounds["auto"], rounds["human_approved"],
                rounds["approval_rate_auto"]),
             "repair: repaired=%d escalated=%d watch_only_guard_correct=%d"
             " unrecorded=%d repair_action_rate=%s"
             % (repair["repaired"], repair["escalated"],
                repair["watch_only_guard_correct"], repair["unrecorded"],
                repair["repair_action_rate"]),
             "calibration: ledger_present=%s entries=%d agreement_rate=%s"
             % (str(calibration["ledger_present"]).lower(),
                calibration["entries"], calibration["agreement_rate"]),
             "feedback_edge: %s (read=%s apply=%s record=%s trace_rows=%d)"
             % (edge["status"], str(edge["read"]).lower(),
                str(edge["apply_edge"]).lower(), str(edge["record"]).lower(),
                edge["trace_rows"])]
    for msg in rounds["errors"]:
        lines.append("ERROR %s" % msg)
    for msg in repair["errors"]:
        lines.append("ERROR %s" % msg)
    for msg in calibration["errors"]:
        lines.append("ERROR %s" % msg)
    error_count = (len(rounds["errors"]) + len(repair["errors"])
                   + len(calibration["errors"]))
    lines.append("errors: %d" % error_count)
    lines.append("wrote: %s" % out_display)
    return "\n".join(lines)


def run(rounds_path, state_path, exp_path, out_path):
    """Default run: build the face, write the JSON, print the summary -> exit code."""
    face = build_face(rounds_path, state_path, exp_path)
    try:
        text = json.dumps(face, indent=2, sort_keys=True, ensure_ascii=False)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    except OSError as exc:
        sys.stdout.write("ERROR output write failed: %s (%s)\n" % (out_path, exc))
        return 1
    sys.stdout.write(summarize(face, out_path) + "\n")
    clean = (not face["rounds"]["errors"]
             and not face["repair_outcomes"]["errors"]
             and not face["calibration"]["errors"])
    return 0 if clean else 1


def _file_md5(path):
    """md5 hex digest of the file bytes (the promotion source_sha form)."""
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def _utcnow_ts():
    """Current UTC time in the exp_port stamp form."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def collect_admission_events(rounds_path):
    """Walk the round ledger in file order -> (events, errors).

    One event per admitted (round, class) pair; same-round duplicate
    admission entries collapse.  Each event carries round_id, cls,
    lineno, the grounding pointer, and the admission confidence.
    """
    rows, errors = _read_jsonl(rounds_path, "round-ledger")
    events = []
    for lineno, row in rows:
        round_id = row.get("round_id")
        if round_id is None or "mode" not in row:
            errors.append("round-ledger line %d: not a round row (missing"
                          " round_id or mode)" % lineno)
            continue
        seen_in_row = set()
        for adm in row.get("admissions") or []:
            if not isinstance(adm, dict):
                errors.append("round-ledger line %d: admission is not an"
                              " object, skipped" % lineno)
                continue
            cls = adm.get("class")
            if not cls:
                errors.append("round-ledger line %d: admission without a"
                              " class, skipped" % lineno)
                continue
            if adm.get("decision") != "admitted" or cls in seen_in_row:
                continue
            seen_in_row.add(cls)
            events.append({"round_id": round_id, "cls": cls,
                           "lineno": lineno,
                           "pointer": "round-ledger line %d (round_id %s)"
                                      % (lineno, round_id),
                           "confidence": adm.get("confidence")})
    return events, errors


def collect_ready_events(rounds_path, state_path, taxonomy_path):
    """Cast the ready events through the sibling b_gate_audit verdict.

    One event per class whose report row verifies ready; returns
    (events, errors).  The verdict is imported, never re-implemented.
    """
    report, errors = b_gate_audit.build_report(rounds_path, state_path,
                                               taxonomy_path)
    events = []
    for row in report["classes"]:
        if not row["ready"]:
            continue
        events.append({"cls": row["class"], "instances": row["instances"],
                       "rounds": row["rounds"]})
    return events, errors


def _promotion_entry(eid, ts, points, evidence, basis, ledger_md5, actor):
    """One promotion entry dict (exp_port envelope + promotion fields)."""
    entry = {
        "schema": PROMOTION_SCHEMA,
        "id": eid,
        "ts": ts,
        "tool": PROG,
        "points": points,
        "evidence": evidence,
        "batch": PROMOTION_BATCH,
        "fingerprint": exp_port.fingerprint(PROG, points, evidence,
                                            PROMOTION_BATCH),
        "kind": PROMOTION_KIND,
        "source_sha": ledger_md5,
        "basis": basis,
    }
    if actor:
        entry["actor"] = actor
    return entry


def promotion_rows(rounds_path, state_path, taxonomy_path, ts, actor):
    """Cast the promotion event rows -> (rows, errors).

    Admission events first (round-ledger file order), then ready events
    (sorted by class, the b_gate_audit report order).  Row shape in the
    extended contract above.
    """
    errors = []
    ledger_md5 = _file_md5(rounds_path)
    admissions, adm_errors = collect_admission_events(rounds_path)
    errors.extend(adm_errors)
    pointers_by_class = {}
    for ev in admissions:
        pointers_by_class.setdefault(ev["cls"], []).append(ev["pointer"])
    ready, ready_errors = collect_ready_events(rounds_path, state_path,
                                               taxonomy_path)
    errors.extend(ready_errors)
    rows = []
    for ev in admissions:
        points = ("promotion event: round admission, class %s admitted in"
                  " round %s (decision=admitted)"
                  % (ev["cls"], ev["round_id"]))
        basis = ("%s records the admission; promotion row cast by the"
                 " learning_feedback --promote scan over round-ledger md5"
                 " %s" % (ev["pointer"], ledger_md5))
        rows.append(_promotion_entry(
            "promotion-round-%s-%s" % (ev["round_id"], ev["cls"]), ts,
            points, ev["pointer"], basis, ledger_md5, actor))
    for ev in ready:
        points = ("promotion event: class ready, class %s verifies the"
                  " b-gate ready threshold (instances=%d, rounds=%d)"
                  % (ev["cls"], ev["instances"], ev["rounds"]))
        pointers = pointers_by_class.get(ev["cls"], [])
        evidence = "; ".join(pointers) if pointers else (
            "b-gate class row instances=%d rounds=%d"
            % (ev["instances"], ev["rounds"]))
        basis = ("ready predicate instances >= %d and rounds >= %d per"
                 " tools/b_gate_audit.py (imported, never re-implemented);"
                 " derived from round-ledger md5 %s plus round-state and"
                 " taxonomy at scan"
                 % (b_gate_audit.THRESHOLD_INSTANCES,
                    b_gate_audit.THRESHOLD_ROUNDS, ledger_md5))
        rows.append(_promotion_entry(
            "promotion-class-ready-%s" % ev["cls"], ts, points, evidence,
            basis, ledger_md5, actor))
    return rows, errors


def append_promotion_rows(rows, ledger_path, dry_run):
    """Append rows through the exp_port seen set.

    Returns (appended_ids, skipped_pairs, lines); skipped pairs carry
    (id, axis).  Duplicates and dry-run rows write nothing.  A corrupt
    ledger returns (None, None, [error lines]) - the caller fails loud.
    """
    try:
        existing = exp_port.read_ledger(ledger_path)
    except exp_port.CorruptLedger as exc:
        return None, None, ["exp-ledger: %s" % exc]
    existing = existing if existing is not None else []
    seen_ids = set()
    seen_fps = set()
    for entry in existing:
        eid = entry.get("id")
        if isinstance(eid, str) and eid:
            seen_ids.add(eid)
        mark = entry.get("fingerprint")
        if isinstance(mark, str) and mark:
            seen_fps.add(mark)
    appended = []
    skipped = []
    lines = []
    parent = os.path.dirname(os.path.abspath(ledger_path))
    if not dry_run and parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            return None, None, ["exp-ledger parent mkdir failed: %s" % exc]
    for row in rows:
        if row["id"] in seen_ids:
            skipped.append((row["id"], "id"))
            lines.append("duplicate-skip id=%s axis=id ledger=%s"
                         % (row["id"], ledger_path))
            continue
        if row["fingerprint"] in seen_fps:
            skipped.append((row["id"], "fingerprint"))
            lines.append("duplicate-skip id=%s axis=fingerprint ledger=%s"
                         % (row["id"], ledger_path))
            continue
        if dry_run:
            lines.append("dry-run id=%s would-append ledger=%s"
                         % (row["id"], ledger_path))
            continue
        line = json.dumps(row, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
        try:
            with open(ledger_path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            return None, None, ["exp-ledger append failed: %s" % exc]
        seen_ids.add(row["id"])
        seen_fps.add(row["fingerprint"])
        appended.append(row["id"])
        lines.append("appended id=%s ledger=%s" % (row["id"], ledger_path))
    return appended, skipped, lines


def run_promotion(rounds_path, state_path, taxonomy_path, exp_path, ts,
                  actor, dry_run):
    """--promote scan: cast rows, append through the seen set, report."""
    if not exp_port.valid_ts(ts):
        sys.stderr.write("learning_feedback --promote: --ts must be an ISO"
                         " date or timestamp: %s\n" % ts)
        return 2
    try:
        rows, errors = promotion_rows(rounds_path, state_path,
                                      taxonomy_path, ts, actor)
    except OSError as exc:
        sys.stdout.write("ERROR promotion scan cannot read its inputs:"
                         " %s\n" % exc)
        return 1
    if errors:
        for msg in errors:
            sys.stdout.write("ERROR %s\n" % msg)
        sys.stdout.write("promotion scan: %d error(s); nothing appended"
                         " (fail loud)\n" % len(errors))
        return 1
    appended, skipped, lines = append_promotion_rows(rows, exp_path,
                                                     dry_run)
    if appended is None:
        for msg in lines:
            sys.stdout.write("ERROR %s\n" % msg)
        sys.stdout.write("promotion scan: the experience ledger could not"
                         " be read or written; nothing appended"
                         " (fail loud)\n")
        return 1
    for line in lines:
        sys.stdout.write(line + "\n")
    sys.stdout.write("promotion scan: events=%d appended=%d skipped=%d"
                     " dry_run=%s ledger=%s\n"
                     % (len(rows), len(appended), len(skipped),
                        str(bool(dry_run)).lower(), exp_path))
    return 0


def _write_fixture(path, lines):
    """Write one fixture file (JSONL or JSON document) into the temp root."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def _check(failures, vector, name, cond, detail):
    """Record one failed assertion for a selftest vector."""
    if not cond:
        failures.append("vector %d %s: %s" % (vector, name, detail))


# Synthetic scheduler sources for the feedback-edge vectors (fixture text,
# parsed by scan_scheduler_consumption; each shape states which evidence it
# carries so the open/partial/closed grades are pinned from both sides).
DEAD_SCHED_SOURCE = (
    "DEFAULT_PATH = ('docs', 'feedback-absent.json')\n"
    "\n"
    "def plan_face(args):\n"
    "    return {'verdict': 'quiet'}\n")
LIVE_SCHED_SOURCE = (
    "DEFAULT_FEEDBACK = ('docs', 'scheduling-feedback.json')\n"
    "\n"
    "def feedback_face(flagged):\n"
    "    doc = read_json_doc(flagged[0])\n"
    "    rounds = doc.get('rounds') or {}\n"
    "    return rounds.get('approval_rate_auto')\n"
    "\n"
    "def apply_feedback_input(interval, rate):\n"
    "    if rate is not None and rate < 0.5:\n"
    "        return interval * 2, 'cadence-interval-x2'\n"
    "    return interval, 'cadence-current'\n"
    "\n"
    "def build_plan(rate, action):\n"
    "    return {'schedulingInput': {'approvalRateAuto': rate,\n"
    "                                'action': action}}\n"
    "\n"
    "def run_plan(args):\n"
    "    rate = feedback_face(args.feedback)\n"
    "    interval, action = apply_feedback_input(60, rate)\n"
    "    return build_plan(rate, action)\n")
NORECORD_SCHED_SOURCE = (
    "DEFAULT_FEEDBACK = ('docs', 'scheduling-feedback.json')\n"
    "\n"
    "def feedback_face(flagged):\n"
    "    doc = read_json_doc(flagged[0])\n"
    "    rounds = doc.get('rounds') or {}\n"
    "    return rounds.get('approval_rate_auto')\n"
    "\n"
    "def apply_feedback_input(interval, rate):\n"
    "    return interval * 2, 'cadence-interval-x2'\n"
    "\n"
    "def build_plan(rate, action):\n"
    "    return {'rate': rate, 'action': action}\n"
    "\n"
    "def run_plan(args):\n"
    "    rate = feedback_face(args.feedback)\n"
    "    interval, action = apply_feedback_input(60, rate)\n"
    "    return build_plan(rate, action)\n")
KILLED_SCHED_SOURCE = (
    "DEFAULT_FEEDBACK = ('docs', 'scheduling-feedback.json')\n"
    "\n"
    "def feedback_face(flagged):\n"
    "    doc = read_json_doc(flagged[0])\n"
    "    rounds = doc.get('rounds') or {}\n"
    "    return rounds.get('approval_rate_auto')\n"
    "\n"
    "def apply_feedback_input(interval, rate):\n"
    "    return interval * 2, 'cadence-interval-x2'\n"
    "\n"
    "def run_plan(args):\n"
    "    # rate = feedback_face(args.feedback)\n"
    "    # interval, action = apply_feedback_input(60, rate)\n"
    "    return {'verdict': 'quiet'}\n")
SELFTEST_ONLY_SCHED_SOURCE = (
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
    "        return {'schedulingInput': {'rate': rate, 'action': action}}\n")


def selftest():
    """Fourteen offline vectors on temp fixtures; zero repository paths."""
    total_vectors = 14
    root = tempfile.mkdtemp(prefix="learning_feedback_selftest_")
    failures = []
    try:
        # Vector 1: two rounds, one auto one human-approved; the repair face
        # covers all four states once.
        v1 = os.path.join(root, "v1")
        os.mkdir(v1)
        rounds1 = os.path.join(v1, "round-ledger.jsonl")
        _write_fixture(rounds1, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["alpha"],
                        "admissions": [{"class": "alpha",
                                        "decision": "admitted",
                                        "confidence": 1.0,
                                        "basis": "gear auto: confidence 1.00"
                                                 " >= threshold 0.80"}]},
                       sort_keys=True),
            json.dumps({"round_id": 2, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["beta"], "admissions": []},
                       sort_keys=True),
        ])
        state1 = os.path.join(v1, "round-state.json")
        _write_fixture(state1, [json.dumps({
            "schema": "rocqwash.round-state/1",
            "admitted_classes": [
                {"class": "alpha", "confidence": 1.0,
                 "basis": "gear auto: confidence 1.00 >= threshold 0.80"},
                {"class": "beta", "confidence": None,
                 "basis": "human point-order approved (unconditional)"},
            ]}, sort_keys=True)])
        exp1 = os.path.join(v1, "exp-ledger.jsonl")
        _write_fixture(exp1, [
            json.dumps({"id": "EXP-1-0001", "points": "run 1: family=A"
                        " action=fix-content (auto triage)"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0002", "points": "run 2: family=B"
                        " action=escalated"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0003", "points": "run 3: family=U"
                        " action=watch-only"}, sort_keys=True),
            json.dumps({"id": "EXP-1-0004", "points": "run 4: plain note"},
                       sort_keys=True),
        ])
        sched1 = os.path.join(v1, "scheduler_lite.py")
        _write_fixture(sched1, [DEAD_SCHED_SOURCE.rstrip("\n")])
        face1 = build_face(rounds1, state1, exp1, sched1)
        expect1 = {
            "schema": SCHEMA,
            "rounds": {"total": 2, "auto": 1, "human_approved": 1,
                       "approval_rate_auto": 0.5,
                       "by_class": [
                           {"class": "alpha", "rounds": 1, "gear": "auto",
                            "confidence": 1.0},
                           {"class": "beta", "rounds": 1, "gear": "human",
                            "confidence": None}],
                       "errors": []},
            "repair_outcomes": {"repaired": 1, "escalated": 1,
                                "watch_only_guard_correct": 1,
                                "unrecorded": 1, "repair_action_rate": 0.25,
                                "errors": []},
            "calibration": {"section": "calibration", "ledger_present": True,
                            "entries": 0, "agreement_rate": None,
                            "by_class": [], "errors": []},
            "feedback_edge": {
                "status": "open", "scheduler_source": sched1,
                "read": False, "apply_edge": False, "record": False,
                "ledger_trace": False, "trace_rows": 0,
                "note": ("edge open: no live consumption of"
                         " approval_rate_auto in the scheduler source (no"
                         " live consumption chain in the runtime faces);"
                         " 0 round-ledger row(s) carry scheduling_input")},
        }
        _check(failures, 1, "face", face1 == expect1,
               "face %r != expected %r" % (face1, expect1))

        # Vector 2: corrupt-line tolerance plus an absent round-state file;
        # the run continues on the valid rows and records every error.
        v2 = os.path.join(root, "v2")
        os.mkdir(v2)
        rounds2 = os.path.join(v2, "round-ledger.jsonl")
        _write_fixture(rounds2, [
            json.dumps({"round_id": 7, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["gamma"],
                        "admissions": [{"class": "gamma",
                                        "decision": "admitted",
                                        "confidence": 0.9}]}, sort_keys=True),
            "this line is not json {{{",
        ])
        state2 = os.path.join(v2, "round-state.json")  # deliberately absent
        exp2 = os.path.join(v2, "exp-ledger.jsonl")
        _write_fixture(exp2, [
            json.dumps({"id": "EXP-2-0001", "points": "action=fix-content"},
                       sort_keys=True),
            "not a row ]]]",
        ])
        face2 = build_face(rounds2, state2, exp2)
        _check(failures, 2, "round totals", face2["rounds"]["total"] == 1
               and face2["rounds"]["auto"] == 1
               and face2["rounds"]["approval_rate_auto"] == 1.0,
               "rounds face %r" % face2["rounds"])
        _check(failures, 2, "round errors", len(face2["rounds"]["errors"]) == 2
               and any("round-ledger line 2" in m
                       for m in face2["rounds"]["errors"])
               and any("round-state" in m for m in face2["rounds"]["errors"]),
               "rounds errors %r" % face2["rounds"]["errors"])
        _check(failures, 2, "repair", face2["repair_outcomes"]["repaired"] == 1
               and face2["repair_outcomes"]["repair_action_rate"] == 1.0
               and len(face2["repair_outcomes"]["errors"]) == 1,
               "repair face %r" % face2["repair_outcomes"])

        # Vector 3: empty ledgers; zero denominators give null rates, not crashes.
        v3 = os.path.join(root, "v3")
        os.mkdir(v3)
        rounds3 = os.path.join(v3, "round-ledger.jsonl")
        state3 = os.path.join(v3, "round-state.json")
        exp3 = os.path.join(v3, "exp-ledger.jsonl")
        sched3 = os.path.join(v3, "scheduler_lite.py")
        for path in (rounds3, exp3):
            _write_fixture(path, [])
        _write_fixture(sched3, [DEAD_SCHED_SOURCE.rstrip("\n")])
        _write_fixture(state3, [json.dumps({"schema": "rocqwash.round-state/1",
                                            "admitted_classes": []},
                                           sort_keys=True)])
        face3 = build_face(rounds3, state3, exp3, sched3)
        expect3 = {
            "schema": SCHEMA,
            "rounds": {"total": 0, "auto": 0, "human_approved": 0,
                       "approval_rate_auto": None, "by_class": [],
                       "errors": []},
            "repair_outcomes": {"repaired": 0, "escalated": 0,
                                "watch_only_guard_correct": 0,
                                "unrecorded": 0, "repair_action_rate": None,
                                "errors": []},
            "calibration": {"section": "calibration", "ledger_present": False,
                            "entries": 0, "agreement_rate": None,
                            "by_class": [], "errors": []},
            "feedback_edge": {
                "status": "open", "scheduler_source": sched3,
                "read": False, "apply_edge": False, "record": False,
                "ledger_trace": False, "trace_rows": 0,
                "note": ("edge open: no live consumption of"
                         " approval_rate_auto in the scheduler source (no"
                         " live consumption chain in the runtime faces);"
                         " 0 round-ledger row(s) carry scheduling_input")},
        }
        _check(failures, 3, "face", face3 == expect3,
               "face %r != expected %r" % (face3, expect3))

        # Vector 4: the mechanical-fix family classifies as repaired; unknown
        # tokens and token-less rows stay unrecorded; no row is forced into
        # a state.
        v4 = os.path.join(root, "v4")
        os.mkdir(v4)
        rounds4 = os.path.join(v4, "round-ledger.jsonl")
        _write_fixture(rounds4, [
            json.dumps({"round_id": 9, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["delta"],
                        "admissions": [{"class": "delta",
                                        "decision": "admitted",
                                        "confidence": 0.9}]}, sort_keys=True),
        ])
        state4 = os.path.join(v4, "round-state.json")
        _write_fixture(state4, [json.dumps({"schema": "rocqwash.round-state/1",
                                            "admitted_classes": []},
                                           sort_keys=True)])
        exp4 = os.path.join(v4, "exp-ledger.jsonl")
        _write_fixture(exp4, [
            json.dumps({"id": "EXP-4-0001", "points": "run A: family=E"
                        " action=rerun-after-stable-window"}, sort_keys=True),
            json.dumps({"id": "EXP-4-0002", "points": "no action vocabulary"
                        " in this row"}, sort_keys=True),
            json.dumps({"id": "EXP-4-0003", "points": "action=unknown-thing"},
                       sort_keys=True),
        ])
        face4 = build_face(rounds4, state4, exp4)
        expect4_repair = {"repaired": 1, "escalated": 0,
                          "watch_only_guard_correct": 0, "unrecorded": 2,
                          "repair_action_rate": 0.3333, "errors": []}
        _check(failures, 4, "repair", face4["repair_outcomes"] == expect4_repair,
               "repair face %r != expected %r"
               % (face4["repair_outcomes"], expect4_repair))
        _check(failures, 4, "rounds", face4["rounds"]["total"] == 1
               and face4["rounds"]["auto"] == 1
               and not face4["rounds"]["errors"],
               "rounds face %r" % face4["rounds"])

        # Vector 5: a populated calibration account; the three readings
        # (entry count, agreement rate, per-grade breakdown) come off the
        # points text in the exact word shapes the calibration writer lays
        # down, and rows of other tools stay outside the section.
        v5 = os.path.join(root, "v5")
        os.mkdir(v5)
        rounds5 = os.path.join(v5, "round-ledger.jsonl")
        state5 = os.path.join(v5, "round-state.json")
        _write_fixture(rounds5, [
            json.dumps({"round_id": 5, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        _write_fixture(state5, [json.dumps(
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            sort_keys=True)])
        exp5 = os.path.join(v5, "exp-ledger.jsonl")
        _write_fixture(exp5, [
            json.dumps({"id": "CAL-R-001", "tool": CALIB_TOOL,
                        "points": "calibration gap 1.00 reaches the signal"
                                  " threshold: predicted HIGH, leg"
                                  " witness.lean measured FAIL (rc=1,"
                                  " expected green) for family fam.high"},
                       sort_keys=True),
            json.dumps({"id": "CAL-R-002", "tool": CALIB_TOOL,
                        "points": "calibration holds within the signal"
                                  " threshold: predicted HIGH, leg"
                                  " witness.lean measured PASS (rc=0,"
                                  " expected green), gap 0.00, family"
                                  " fam.low"},
                       sort_keys=True),
            json.dumps({"id": "CAL-R-003", "tool": CALIB_TOOL,
                        "points": "calibration holds within the signal"
                                  " threshold: predicted MID, leg"
                                  " witness.lean measured PASS (rc=0,"
                                  " expected green), gap 0.50, family"
                                  " fam.mid"},
                       sort_keys=True),
            json.dumps({"id": "EXP-5-0001", "tool": "fixture",
                        "points": "calibration holds within the signal"
                                  " threshold: predicted HIGH, leg"
                                  " witness.lean measured PASS (rc=0,"
                                  " expected green), gap 0.00, family"
                                  " other.tool"},
                       sort_keys=True),
        ])
        face5 = build_face(rounds5, state5, exp5)
        expect5_cal = {"section": "calibration", "ledger_present": True,
                       "entries": 3, "agreement_rate": 0.3333,
                       "by_class": [
                           {"class": "HIGH", "entries": 2, "agreeing": 1,
                            "agreement_rate": 0.5},
                           {"class": "MID", "entries": 1, "agreeing": 0,
                            "agreement_rate": 0.0}],
                       "errors": []}
        _check(failures, 5, "calibration", face5["calibration"] == expect5_cal,
               "calibration face %r != expected %r"
               % (face5["calibration"], expect5_cal))

        # Vector 6: an empty account and an absent account both read as
        # ledger_present=false with null readings (data, never padded).
        v6 = os.path.join(root, "v6")
        os.mkdir(v6)
        rounds6 = os.path.join(v6, "round-ledger.jsonl")
        state6 = os.path.join(v6, "round-state.json")
        _write_fixture(rounds6, [
            json.dumps({"round_id": 6, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        _write_fixture(state6, [json.dumps(
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            sort_keys=True)])
        exp6_empty = os.path.join(v6, "exp-ledger.jsonl")
        _write_fixture(exp6_empty, [])
        face6 = build_face(rounds6, state6, exp6_empty)
        _check(failures, 6, "empty ledger",
               face6["calibration"]["ledger_present"] is False
               and face6["calibration"]["entries"] == 0
               and face6["calibration"]["agreement_rate"] is None
               and face6["calibration"]["by_class"] == [],
               "calibration face %r" % face6["calibration"])
        face6_absent = build_face(rounds6, state6,
                                  os.path.join(v6, "absent-ledger.jsonl"))
        _check(failures, 6, "absent ledger",
               face6_absent["calibration"]["ledger_present"] is False
               and face6_absent["calibration"]["agreement_rate"] is None,
               "calibration face %r" % face6_absent["calibration"])

        # Vector 7: bad-row tolerance; a calibration row whose points text
        # carries no readable pair stays counted in entries, is excluded
        # from the readings, and is named in errors.
        v7 = os.path.join(root, "v7")
        os.mkdir(v7)
        rounds7 = os.path.join(v7, "round-ledger.jsonl")
        state7 = os.path.join(v7, "round-state.json")
        _write_fixture(rounds7, [
            json.dumps({"round_id": 7, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        _write_fixture(state7, [json.dumps(
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            sort_keys=True)])
        exp7 = os.path.join(v7, "exp-ledger.jsonl")
        _write_fixture(exp7, [
            json.dumps({"id": "CAL-B-001", "tool": CALIB_TOOL,
                        "points": "a calibration row whose text lost its"
                                  " reading"}, sort_keys=True),
            json.dumps({"id": "CAL-B-002", "tool": CALIB_TOOL,
                        "points": "calibration holds within the signal"
                                  " threshold: predicted MID, leg"
                                  " witness.lean measured FAIL (rc=1,"
                                  " expected green), gap 0.50, family"
                                  " fam.mid"},
                       sort_keys=True),
        ])
        face7 = build_face(rounds7, state7, exp7)
        cal7 = face7["calibration"]
        _check(failures, 7, "counts", cal7["entries"] == 2
               and cal7["agreement_rate"] == 0.0
               and cal7["by_class"] == [{"class": "MID", "entries": 1,
                                         "agreeing": 0,
                                         "agreement_rate": 0.0}],
               "calibration face %r" % cal7)
        _check(failures, 7, "error named", len(cal7["errors"]) == 1
               and "line 1" in cal7["errors"][0]
               and "calibration" in cal7["errors"][0],
               "calibration errors %r" % cal7["errors"])

        # Vector 8: the expanded writer set end to end; the two mechanical-fix
        # tokens classify repaired, queue-etiquette lands in the
        # watch_only_guard_correct slot (the D-queue-wall run never executed
        # its steps), and a token outside the table stays unrecorded (no row
        # forced into a state).
        v8 = os.path.join(root, "v8")
        os.mkdir(v8)
        rounds8 = os.path.join(v8, "round-ledger.jsonl")
        state8 = os.path.join(v8, "round-state.json")
        _write_fixture(rounds8, [
            json.dumps({"round_id": 8, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        _write_fixture(state8, [json.dumps(
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            sort_keys=True)])
        exp8 = os.path.join(v8, "exp-ledger.jsonl")
        _write_fixture(exp8, [
            json.dumps({"id": "EXP-8-0001", "points": "run 1: family=C"
                        " action=restore-toolchain"}, sort_keys=True),
            json.dumps({"id": "EXP-8-0002", "points": "run 2: family=B"
                        " action=rerun-after-stable-window"}, sort_keys=True),
            json.dumps({"id": "EXP-8-0003", "points": "run 3: family=D"
                        " action=queue-etiquette"}, sort_keys=True),
            json.dumps({"id": "EXP-8-0004", "points": "action=unknown-thing"},
                       sort_keys=True),
        ])
        face8 = build_face(rounds8, state8, exp8)
        expect8_repair = {"repaired": 2, "escalated": 0,
                          "watch_only_guard_correct": 1, "unrecorded": 1,
                          "repair_action_rate": 0.5, "errors": []}
        _check(failures, 8, "repair", face8["repair_outcomes"] == expect8_repair,
               "repair face %r != expected %r"
               % (face8["repair_outcomes"], expect8_repair))
        _check(failures, 8, "rounds", face8["rounds"]["total"] == 1
               and not face8["rounds"]["errors"],
               "rounds face %r" % face8["rounds"])

        # Vector 9: the promotion row lock.  A three-round alpha (ready),
        # a one-round beta, and a taxonomy-only gamma cast exactly four
        # admission rows plus one ready row with deterministic ids in
        # ledger order then class order; each row carries the full
        # rocqwash-exp/1+promotion shape with an exp_port-compatible
        # fingerprint; the append lands all five, and a rescan of the
        # unchanged ledger skips all five on the id axis with zero
        # writes (append-only, idempotent); --dry-run writes nothing.
        v9 = os.path.join(root, "v9")
        os.mkdir(v9)
        rounds9 = os.path.join(v9, "round-ledger.jsonl")
        rows9 = []
        for rid, classes9 in ((1, ("alpha", "beta")), (2, ("alpha",)),
                              (3, ("alpha",))):
            rows9.append(json.dumps(
                {"round_id": rid, "mode": "auto", "verify_rc": 0,
                 "classes_applied": list(classes9),
                 "admissions": [{"class": cls, "decision": "admitted",
                                 "confidence": 0.9} for cls in classes9]},
                sort_keys=True))
        _write_fixture(rounds9, rows9)
        state9 = os.path.join(v9, "round-state.json")
        _write_fixture(state9, [json.dumps(
            {"schema": "rocqwash.round-state/1",
             "admitted_classes": [{"class": "alpha", "confidence": 0.9,
                                   "basis": "gear auto"},
                                  {"class": "beta", "confidence": 0.9,
                                   "basis": "gear auto"}]},
            sort_keys=True)])
        taxonomy9 = os.path.join(v9, "taxonomy.json")
        _write_fixture(taxonomy9, [json.dumps(
            {"rows": [{"familyId": "alpha"}, {"familyId": "beta"},
                      {"familyId": "gamma"}]}, sort_keys=True)])
        exp9 = os.path.join(v9, "exp-ledger.jsonl")
        _write_fixture(exp9, [
            json.dumps({"id": "EXP-V9-0001", "tool": "fixture",
                        "points": "run 1: family=A action=fix-content"},
                       sort_keys=True),
        ])
        ts9 = "2026-11-23T00:00:00Z"
        promo_rows, errors9 = promotion_rows(rounds9, state9, taxonomy9,
                                             ts9, "")
        expect_ids = ["promotion-round-1-alpha", "promotion-round-1-beta",
                      "promotion-round-2-alpha", "promotion-round-3-alpha",
                      "promotion-class-ready-alpha"]
        _check(failures, 9, "cast errors", not errors9,
               "errors %r" % (errors9,))
        _check(failures, 9, "event ids",
               [row["id"] for row in promo_rows] == expect_ids,
               "ids %r != %r"
               % ([row["id"] for row in promo_rows], expect_ids))
        shape = {"schema", "id", "ts", "tool", "points", "evidence",
                 "batch", "fingerprint", "kind", "source_sha", "basis"}
        _check(failures, 9, "row shape",
               all(set(row) == shape for row in promo_rows),
               "field sets %r"
               % [sorted(set(row) - shape) for row in promo_rows])
        _check(failures, 9, "envelope",
               all(row["schema"] == PROMOTION_SCHEMA
                   and row["kind"] == PROMOTION_KIND
                   and row["tool"] == PROG
                   and row["batch"] == PROMOTION_BATCH
                   and row["ts"] == ts9 for row in promo_rows),
               "envelope %r"
               % [(row["schema"], row["kind"], row["tool"], row["batch"],
                   row["ts"]) for row in promo_rows])
        _check(failures, 9, "fingerprint compat",
               all(row["fingerprint"] == exp_port.fingerprint(
                   row["tool"], row["points"], row["evidence"],
                   row["batch"]) for row in promo_rows),
               "fingerprint mismatch on some row")
        ledger_md5 = _file_md5(rounds9)
        _check(failures, 9, "source_sha",
               all(row["source_sha"] == ledger_md5 for row in promo_rows),
               "source_sha %r != %r"
               % (promo_rows[0]["source_sha"], ledger_md5))
        _check(failures, 9, "admission row face",
               promo_rows[0]["points"] == (
                   "promotion event: round admission, class alpha"
                   " admitted in round 1 (decision=admitted)")
               and promo_rows[0]["evidence"]
               == "round-ledger line 1 (round_id 1)"
               and "round-ledger line 1 (round_id 1) records the"
                   " admission" in promo_rows[0]["basis"],
               "admission row %r / %r" % (promo_rows[0]["points"],
                                          promo_rows[0]["evidence"]))
        ready_row = promo_rows[-1]
        _check(failures, 9, "ready row face",
               ready_row["points"] == (
                   "promotion event: class ready, class alpha verifies"
                   " the b-gate ready threshold (instances=3, rounds=3)")
               and ready_row["evidence"] == (
                   "round-ledger line 1 (round_id 1); round-ledger line"
                   " 2 (round_id 2); round-ledger line 3 (round_id 3)")
               and "instances >= 3 and rounds >= 1" in ready_row["basis"],
               "ready row %r / %r" % (ready_row["points"],
                                      ready_row["evidence"]))
        appended9, skipped9, _lines9 = append_promotion_rows(
            promo_rows, exp9, False)
        _check(failures, 9, "append all",
               appended9 == expect_ids and not skipped9,
               "appended %r skipped %r" % (appended9, skipped9))
        with open(exp9, "r", encoding="utf-8") as fh:
            lines9 = [raw for raw in fh if raw.strip()]
        _check(failures, 9, "ledger grew",
               len(lines9) == 6
               and json.loads(lines9[-1])["id"] == expect_ids[-1],
               "ledger lines %d" % len(lines9))
        bytes9 = open(exp9, "rb").read()
        promo_again, _errors9 = promotion_rows(rounds9, state9, taxonomy9,
                                               ts9, "")
        appended9b, skipped9b, _lines9b = append_promotion_rows(
            promo_again, exp9, False)
        _check(failures, 9, "idempotent rescan",
               not appended9b
               and [pair[1] for pair in skipped9b] == ["id"] * 5,
               "rescan appended %r skipped %r"
               % (appended9b, skipped9b))
        _check(failures, 9, "rescan wrote nothing",
               open(exp9, "rb").read() == bytes9,
               "ledger bytes changed on rescan")
        dry9 = os.path.join(v9, "dry", "exp-ledger.jsonl")
        appended9c, _skipped9c, lines9c = append_promotion_rows(
            promo_rows, dry9, True)
        _check(failures, 9, "dry-run writes nothing",
               appended9c == [] and not os.path.exists(dry9)
               and all(line.startswith("dry-run id=") for line in lines9c),
               "dry-run appended %r" % (appended9c,))

        # Vector 10: the exp_port seen-set interop.  A promotion row
        # already in the ledger makes an exp_port append with the same
        # explicit id skip on the id axis and an exp_port append with the
        # same four carrier fields (different id) skip on the fingerprint
        # axis; exp_port still appends fresh content, and the mixed
        # ledger reads back through exp_port.read_ledger (one parse
        # surface).
        v10 = os.path.join(root, "v10")
        os.mkdir(v10)
        rounds10 = os.path.join(v10, "round-ledger.jsonl")
        _write_fixture(rounds10, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["solo"],
                        "admissions": [{"class": "solo",
                                        "decision": "admitted",
                                        "confidence": 0.9}]},
                       sort_keys=True),
        ])
        state10 = os.path.join(v10, "round-state.json")
        _write_fixture(state10, [json.dumps(
            {"schema": "rocqwash.round-state/1", "admitted_classes": []},
            sort_keys=True)])
        taxonomy10 = os.path.join(v10, "taxonomy.json")
        _write_fixture(taxonomy10, [json.dumps(
            {"rows": [{"familyId": "solo"}]}, sort_keys=True)])
        exp10 = os.path.join(v10, "exp-ledger.jsonl")
        rows10, errors10 = promotion_rows(rounds10, state10, taxonomy10,
                                          "2026-11-23T00:00:00Z", "")
        _check(failures, 10, "single event",
               not errors10 and len(rows10) == 1
               and rows10[0]["id"] == "promotion-round-1-solo",
               "events %r errors %r"
               % ([r["id"] for r in rows10], errors10))
        appended10, _skipped10, _lines10 = append_promotion_rows(
            rows10, exp10, False)
        _check(failures, 10, "append one",
               appended10 == ["promotion-round-1-solo"],
               "appended %r" % (appended10,))
        bytes10 = open(exp10, "rb").read()
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            rc_a = exp_port.main(["append", "--id",
                                  "promotion-round-1-solo",
                                  "--tool", "unrelated", "--points",
                                  "unrelated", "--ledger", exp10])
        _check(failures, 10, "id-axis skip",
               rc_a == 0
               and ("duplicate-skip id=promotion-round-1-solo axis=id"
                    in sink.getvalue()),
               "rc %d out %r" % (rc_a, sink.getvalue()))
        _check(failures, 10, "id-axis no write",
               open(exp10, "rb").read() == bytes10,
               "ledger bytes changed on id-axis probe")
        promo10 = rows10[0]
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            rc_b = exp_port.main(["append", "--id", "EXP-V10-OTHER",
                                  "--tool", promo10["tool"], "--points",
                                  promo10["points"], "--evidence",
                                  promo10["evidence"], "--batch",
                                  promo10["batch"], "--ledger", exp10])
        _check(failures, 10, "fingerprint-axis skip",
               rc_b == 0 and "axis=fingerprint" in sink.getvalue(),
               "rc %d out %r" % (rc_b, sink.getvalue()))
        _check(failures, 10, "fingerprint-axis no write",
               open(exp10, "rb").read() == bytes10,
               "ledger bytes changed on fingerprint-axis probe")
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            rc_c = exp_port.main(["append", "--tool", "interop",
                                  "--points", "fresh row", "--ledger",
                                  exp10])
        _check(failures, 10, "fresh append still lands",
               rc_c == 0
               and sink.getvalue().startswith("appended id=EXP-"),
               "rc %d out %r" % (rc_c, sink.getvalue()))
        entries10 = exp_port.read_ledger(exp10)
        _check(failures, 10, "one parse surface",
               entries10 is not None and len(entries10) == 2
               and entries10[0]["id"] == "promotion-round-1-solo",
               "entries %r"
               % ([e.get("id") for e in (entries10 or [])],))

        # Vector 11: the closed edge.  A live consumer source (read + apply
        # call edge + per-influence record site) plus a round-ledger row
        # carrying the scheduling_input trace grades closed with the trace
        # counted.
        v11 = os.path.join(root, "v11")
        os.mkdir(v11)
        sched11 = os.path.join(v11, "scheduler_lite.py")
        _write_fixture(sched11, [LIVE_SCHED_SOURCE.rstrip("\n")])
        rounds11 = os.path.join(v11, "round-ledger.jsonl")
        _write_fixture(rounds11, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": ["alpha"],
                        "scheduling_input": {"approval_rate_auto": 0.25,
                                             "action":
                                             "cadence-interval-x2",
                                             "basis": "fixture"},
                        "admissions": []}, sort_keys=True),
            json.dumps({"round_id": 2, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        grade11 = feedback_edge_grade(sched11, rounds11)
        _check(failures, 11, "closed edge",
               grade11["status"] == "closed" and grade11["read"] is True
               and grade11["apply_edge"] is True and grade11["record"] is True
               and grade11["ledger_trace"] is True
               and grade11["trace_rows"] == 1,
               "grade %r" % grade11)
        # A row that is not a round row, and a trace object without a
        # readable rate or action, stay outside the trace count.
        rounds11b = os.path.join(v11, "round-ledger-b.jsonl")
        _write_fixture(rounds11b, [
            json.dumps({"note": "not a round row",
                        "scheduling_input": {"approval_rate_auto": 0.25,
                                             "action": "x"}},
                       sort_keys=True),
            json.dumps({"round_id": 3, "mode": "auto", "verify_rc": 0,
                        "scheduling_input": {"approval_rate_auto": None,
                                             "action": "cadence-current"}},
                       sort_keys=True),
        ])
        grade11b = feedback_edge_grade(sched11, rounds11b)
        _check(failures, 11, "trace shape guard",
               grade11b["trace_rows"] == 0 and grade11b["status"] == "partial",
               "grade %r" % grade11b)
        # A source label rides the face in place of the scanned path (the
        # default run reports the standing consumer by its repo-relative
        # path, so the tracked face carries no machine-specific path).
        label11 = os.path.join("tools", "scheduler_lite.py")
        grade11c = feedback_edge_grade(sched11, rounds11,
                                       source_label=label11)
        _check(failures, 11, "source label carried",
               grade11c["scheduler_source"] == label11
               and grade11c["status"] == "closed"
               and grade11c["trace_rows"] == 1,
               "grade %r" % grade11c)
        _check(failures, 11, "no label keeps the scanned path",
               grade11["scheduler_source"] == sched11,
               "grade %r" % grade11)

        # Vector 12: the partial edge, both subset forms.  A live consumer
        # with no scheduling_input trace row grades partial; a live read and
        # apply edge whose record site is missing grades partial even with
        # the trace present.
        v12 = os.path.join(root, "v12")
        os.mkdir(v12)
        sched12 = os.path.join(v12, "scheduler_lite.py")
        _write_fixture(sched12, [LIVE_SCHED_SOURCE.rstrip("\n")])
        sched12b = os.path.join(v12, "scheduler_lite_b.py")
        _write_fixture(sched12b, [NORECORD_SCHED_SOURCE.rstrip("\n")])
        rounds12 = os.path.join(v12, "round-ledger.jsonl")
        _write_fixture(rounds12, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": []},
                       sort_keys=True),
        ])
        rounds12b = os.path.join(v12, "round-ledger-b.jsonl")
        _write_fixture(rounds12b, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": [],
                        "scheduling_input": {"approval_rate_auto": 0.25,
                                             "action":
                                             "cadence-interval-x2"}},
                       sort_keys=True),
        ])
        grade12 = feedback_edge_grade(sched12, rounds12)
        _check(failures, 12, "partial without trace",
               grade12["status"] == "partial" and grade12["read"] is True
               and grade12["apply_edge"] is True and grade12["record"] is True
               and grade12["ledger_trace"] is False
               and grade12["trace_rows"] == 0,
               "grade %r" % grade12)
        grade12b = feedback_edge_grade(sched12b, rounds12b)
        _check(failures, 12, "partial without record",
               grade12b["status"] == "partial" and grade12b["read"] is True
               and grade12b["apply_edge"] is True
               and grade12b["record"] is False
               and grade12b["ledger_trace"] is True,
               "grade %r" % grade12b)

        # Vector 13: the open edge, kill-test shapes.  A source whose
        # consumption call sites are commented out (the definitions stay,
        # dead code is not consumption) grades open; a source carrying the
        # markers only inside its selftest face grades open (fixture keys
        # are test data, not consumption).
        v13 = os.path.join(root, "v13")
        os.mkdir(v13)
        sched13 = os.path.join(v13, "scheduler_lite.py")
        _write_fixture(sched13, [KILLED_SCHED_SOURCE.rstrip("\n")])
        sched13b = os.path.join(v13, "scheduler_lite_b.py")
        _write_fixture(sched13b, [SELFTEST_ONLY_SCHED_SOURCE.rstrip("\n")])
        rounds13 = os.path.join(v13, "round-ledger.jsonl")
        _write_fixture(rounds13, [
            json.dumps({"round_id": 1, "mode": "auto", "verify_rc": 0,
                        "classes_applied": [], "admissions": [],
                        "scheduling_input": {"approval_rate_auto": 0.25,
                                             "action":
                                             "cadence-interval-x2"}},
                       sort_keys=True),
        ])
        grade13 = feedback_edge_grade(sched13, rounds13)
        _check(failures, 13, "open kill shape",
               grade13["status"] == "open" and grade13["apply_edge"] is False
               and grade13["read"] is True,
               "grade %r" % grade13)
        grade13b = feedback_edge_grade(sched13b, rounds13)
        _check(failures, 13, "selftest face excluded",
               grade13b["status"] == "open" and grade13b["read"] is False
               and grade13b["apply_edge"] is False
               and grade13b["record"] is False,
               "grade %r" % grade13b)

        # Vector 14: the tolerant-absent faces.  An absent scheduler source
        # and an unparseable source both grade open with the reason stated
        # in the note (never an error, never guessed); the edge face stays
        # error-free while the rounds account reports its own ledger error.
        v14 = os.path.join(root, "v14")
        os.mkdir(v14)
        rounds14 = os.path.join(v14, "round-ledger.jsonl")
        _write_fixture(rounds14, [])
        absent14 = os.path.join(v14, "absent_scheduler.py")
        grade14 = feedback_edge_grade(absent14, rounds14)
        # The stated reason names the failure, never the filesystem path
        # (the note reaches the tracked face).
        _check(failures, 14, "absent source open",
               grade14["status"] == "open" and grade14["read"] is False
               and grade14["ledger_trace"] is False
               and "unreadable" in grade14["note"]
               and absent14 not in grade14["note"],
               "grade %r" % grade14)
        bad14 = os.path.join(v14, "bad_scheduler.py")
        _write_fixture(bad14, ["def broken(:\n"])
        grade14b = feedback_edge_grade(bad14, rounds14)
        _check(failures, 14, "unparseable source open",
               grade14b["status"] == "open" and grade14b["read"] is False
               and "unparseable" in grade14b["note"]
               and bad14 not in grade14b["note"],
               "grade %r" % grade14b)
        face14 = build_face(rounds14,
                            os.path.join(v14, "round-state.json"),
                            os.path.join(v14, "exp-ledger.jsonl"), bad14)
        _check(failures, 14, "edge face has no errors list",
               "feedback_edge" in face14
               and face14["feedback_edge"]["status"] == "open"
               and face14["rounds"]["errors"],  # absent state file: one error
               "face %r" % face14["feedback_edge"])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    for line in failures:
        sys.stdout.write("FAIL %s\n" % line)
    if failures:
        red_vectors = len(set(line.split()[1] for line in failures))
        sys.stdout.write("selftest: %d of %d vectors red (%d assertions)\n"
                         % (red_vectors, total_vectors, len(failures)))
        return 1
    sys.stdout.write("selftest: %d/%d vectors green (temp fixtures only,"
                     " zero repository paths)\n" % (total_vectors,
                                                    total_vectors))
    return 0


def main(argv=None):
    """CLI entry: --selftest, the --promote scan, or the default run."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=("scheduling feedback face over the three standing"
                     " ledgers (schema %s; reads docs/round-ledger.jsonl,"
                     " docs/round-state.json, docs/exp-ledger.jsonl"
                     " read-only; writes docs/scheduling-feedback.json;"
                     " --promote appends promotion event rows into the"
                     " experience ledger)" % SCHEMA))
    parser.add_argument("--selftest", action="store_true",
                        help="run the ten selftest vectors on temporary"
                             " fixtures (zero repository paths)")
    parser.add_argument("--promote", action="store_true",
                        help="scan the standing ledgers and append the"
                             " promotion event rows into the experience"
                             " ledger (append-only, idempotent; the only"
                             " writing mode)")
    parser.add_argument("--ledger", default="",
                        help="promote: experience-ledger path override"
                             " (default: docs/exp-ledger.jsonl)")
    parser.add_argument("--ts", default="",
                        help="promote: ISO date/timestamp stamped on the"
                             " appended rows (default: now UTC)")
    parser.add_argument("--actor", default="",
                        help="promote: optional actor carried verbatim as"
                             " the actor field (schema increment, outside"
                             " the fingerprint seen set)")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="promote: cast the events and report, write"
                             " nothing")
    args = parser.parse_args(argv)
    if args.selftest:
        if args.promote:
            parser.error("--selftest takes no other mode")
        return selftest()
    root = _repo_root()
    if args.promote:
        ts = args.ts or _utcnow_ts()
        exp_path = exp_port.resolve_ledger(args.ledger)
        return run_promotion(
            os.path.join(root, *ROUNDS_DEFAULT),
            os.path.join(root, *STATE_DEFAULT),
            os.path.join(root, *TAXONOMY_DEFAULT),
            exp_path, ts, args.actor, args.dry_run)
    return run(os.path.join(root, *ROUNDS_DEFAULT),
               os.path.join(root, *STATE_DEFAULT),
               os.path.join(root, *EXP_DEFAULT),
               os.path.join(root, *OUT_DEFAULT))


if __name__ == "__main__":
    sys.exit(main())
