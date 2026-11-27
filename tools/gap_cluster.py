#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Sign-off: \u738b\u5c0f\u54e5 (rocqwash \u81ea\u6f14\u8fdb\u7ebf\u00b7\u805a\u7c7b\u5e2d)
"""gap_cluster.py: aggregate TODO-SEAT and gap entries into a family-shape-keyed gap ledger (rocqwash tools/, pure JSON logic).

Purpose. Collect gap entries from two local faces, the experience ledger (docs/exp-ledger.jsonl, schema rocqwash-exp/1, gap-class entries carrying the protocol tokens below) and vacgen report JSON files (assumptions[] entries with status todo_seat), and aggregate them by family shape key into a gap ledger (schema rocqwash-gap-ledger/1) for the row-rendering stage. Aggregation is a pure function of the input bytes: fixed ordering rules, no wall clock, no absolute paths in the report (basenames only), so equal inputs give byte-identical output (acceptance item R5).

Interface. `python -I tools/gap_cluster.py [--ledger P]... [--reports P]... [--out FILE] [--json]` or `--selftest`; both input flags repeatable and a --reports directory expands to its *.json files in sorted order. --json prints the gap ledger to stdout; with --out alone stdout carries a one-line summary; zero gaps is data (empty cluster list, exit 0).

Dependencies. Python 3 standard library only; zero network; inputs read-only; the only write is the explicit --out file. Input schemas are read as data: rocqwash-exp/1 ledger lines and the vacgen v2 assumptions[] element key surface (kind, name, typeHead, status, familyId, confidence, matchedTarget, degraded).

Evidence. --selftest on tmp fixtures: shape abstraction, explicit-family and derived-shape clustering, ledger gap-class tokens, degraded holes, fail-loud, exit codes, byte-identical reruns (out file and stdout). Suite segment: tests/refinery_segments/gap.py.

Exit-codes. 0 aggregated (empty is data); 1 selftest red; 2 usage error; 9 missing or corrupt input, or report write failure.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile

PROG = "gap_cluster"
SCHEMA = "rocqwash-gap-ledger/1"
TOOL_VERSION = "1.0.0"

# Gap-class protocol tokens (data tokens, not prose): the ledger-side
# recognition set and the vacgen draft category tokens that exp_port carries
# verbatim in the source field. The pitfall tokens are written as escapes so
# this source face stays ASCII (annotation standard, CJK-free code faces).
# The category rule reads the producer-real token U+5751 (tools/vacgen.py
# line 2470) and the legacy pinned token U+5748, under both key spellings
# the bus carries ("category" and the zh key, tools/bus_feeder.py
# CATEGORY_KEYS), at both levels (entry key and source-dict key). Landed
# ledger rows are append-only, so the alignment is reader-side only.
PROTOCOL_TOKEN = "TODO-SEAT"
STATUS_TOKEN = "status=todo_seat"
CATEGORY_PITFALL = ("\u5751", "\u5748")
CATEGORY_KEYS = ("category", "\u7c7b\u522b")

# Family shape key rules. An explicit familyId wins (report assumption field,
# ledger entry field or ledger source field). Otherwise the ledger points text
# is probed for the family token emitted by the vacgen exp-draft line
# "...(TODO-SEAT counted, no silent degradation): <family> @ <path>", and as
# the last resort the normalized text is abstracted into a shape: identifier
# tokens become <id>, digit runs become <num>, whitespace collapses.
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.!]*")
NUM_RE = re.compile(r"[0-9]+")
FAMILY_IN_POINTS_RE = re.compile(r":\s*([a-z0-9]+(?:[.\-][a-z0-9]+)+)\s+@\s")
SHAPE_ID_SLOT = "<id>"
SHAPE_NUM_SLOT = "<num>"
CLIP_POINTS = 200  # deterministic clip for carried ledger points text


class GapInputError(Exception):
    """Missing or corrupt input (exit code 9); the message names the file."""


def abstract_shape(text):
    """Normalized shape abstraction of a type or points text (pure function)."""
    flat = " ".join((text or "").split())
    flat = IDENT_RE.sub(SHAPE_ID_SLOT, flat)
    flat = NUM_RE.sub(SHAPE_NUM_SLOT, flat)
    return "shape:" + flat


def entry_source(entry):
    """The source dict of a ledger line when it is one, else an empty dict."""
    src = entry.get("source")
    return src if isinstance(src, dict) else {}


def is_ledger_gap_entry(entry):
    """Ledger gap-class recognition: a pitfall category token under either
    key spelling ("category" or the zh key) at either level (entry key or
    source-dict key, carried verbatim from the vacgen exp-draft and the
    fed rows), the TODO-SEAT protocol token in points or evidence, or the
    status token in evidence."""
    src = entry_source(entry)
    for key in CATEGORY_KEYS:
        if entry.get(key) in CATEGORY_PITFALL or src.get(key) in CATEGORY_PITFALL:
            return True
    points = entry.get("points") or ""
    evidence = entry.get("evidence") or ""
    return (PROTOCOL_TOKEN in points or PROTOCOL_TOKEN in evidence
            or STATUS_TOKEN in evidence)


def entry_family_id(entry):
    """Explicit familyId of a ledger entry when one is carried (entry field
    first, then the verbatim source dict)."""
    src = entry_source(entry)
    fam = entry.get("familyId") or src.get("familyId")
    return str(fam) if fam else None


def ledger_shape_key(entry):
    """Family shape key of a ledger gap entry (documented priority chain)."""
    fam = entry_family_id(entry)
    if fam:
        return "fam:" + fam
    points = " ".join((entry.get("points") or "").split())
    if PROTOCOL_TOKEN in points:
        m = FAMILY_IN_POINTS_RE.search(points)
        if m:
            return "fam:" + m.group(1)
    return abstract_shape(points)


def assumption_shape_key(assumption):
    """Family shape key of a vacgen report assumption with status todo_seat:
    the explicit familyId when present, else the shape of typeHead."""
    fam = assumption.get("familyId")
    if fam:
        return "fam:" + str(fam)
    return abstract_shape(assumption.get("typeHead") or "")


def sha256_file(path):
    """sha256 of a file's bytes (input fingerprint carrier; read-only)."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def member_sort_key(member):
    """Deterministic member order: origin, file, line-or-index, id."""
    ref = member.get("ref") or {}
    pos = ref.get("line")
    if pos is None:
        pos = ref.get("index", 0)
    return (member.get("origin") or "", member.get("file") or "", pos,
            member.get("id") or "")


def make_member(origin, path, ref, entry_id, kind, name, text, family_id,
                confidence, degraded):
    """One uniform member record (both origins share the key surface)."""
    return {
        "origin": origin,
        "file": os.path.basename(path),
        "ref": ref,
        "id": entry_id,
        "kind": kind,
        "name": name,
        "text": text,
        "familyId": family_id,
        "confidence": confidence,
        "degraded": degraded,
    }


def add_member(clusters, key, member):
    """Append a member under its shape key, creating the cluster on first hit."""
    cluster = clusters.get(key)
    if cluster is None:
        cluster = {"shapeKey": key, "members": []}
        clusters[key] = cluster
    cluster["members"].append(member)


def resolve_inputs(paths, kind):
    """Expand and order one input list: duplicates collapsed, sorted path
    order (argv-order independent); a directory expands to its *.json files
    in sorted order for report inputs."""
    resolved = set()
    for path in paths:
        if os.path.isdir(path):
            if kind != "report":
                raise GapInputError("ledger input %s is a directory (ledger "
                                    "inputs are files)" % os.path.basename(path))
            for name in sorted(os.listdir(path)):
                if name.endswith(".json"):
                    resolved.add(os.path.join(path, name))
        else:
            resolved.add(path)
    return sorted(resolved)


def aggregate(ledger_paths, report_paths):
    """Pure aggregation over resolved input paths. Raises GapInputError on
    missing or corrupt inputs (fail loud, nothing written)."""
    ledgers = resolve_inputs(ledger_paths, "ledger")
    reports = resolve_inputs(report_paths, "report")
    digest_lines = []
    clusters = {}
    totals = {
        "ledgerEntries": 0,
        "ledgerGapEntries": 0,
        "ledgerNonGapEntries": 0,
        "reportAssumptions": 0,
        "reportTodoSeat": 0,
        "reportNonTodoSeat": 0,
        "gaps": 0,
        "clusters": 0,
    }
    for path in ledgers:
        digest_lines.append("ledger %s %s" % (path, sha256_file(path)))
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError as exc:
                    raise GapInputError(
                        "ledger %s line %d is not valid JSON: %s"
                        % (os.path.basename(path), lineno, exc))
                if not isinstance(entry, dict):
                    raise GapInputError(
                        "ledger %s line %d is not a JSON object"
                        % (os.path.basename(path), lineno))
                totals["ledgerEntries"] += 1
                if not is_ledger_gap_entry(entry):
                    totals["ledgerNonGapEntries"] += 1
                    continue
                totals["ledgerGapEntries"] += 1
                src = entry_source(entry)
                points = " ".join((entry.get("points") or "").split())
                add_member(clusters, ledger_shape_key(entry), make_member(
                    "ledger", path, {"line": lineno}, entry.get("id"),
                    None, None, points[:CLIP_POINTS],
                    str(src.get("familyId")) if src.get("familyId") else None,
                    None, None))
    for path in reports:
        digest_lines.append("report %s %s" % (path, sha256_file(path)))
        with open(path, encoding="utf-8") as fh:
            try:
                doc = json.load(fh)
            except ValueError as exc:
                raise GapInputError(
                    "report %s is not valid JSON: %s"
                    % (os.path.basename(path), exc))
        if not isinstance(doc, dict) or not isinstance(doc.get("assumptions"), list):
            raise GapInputError(
                "report %s carries no assumptions[] array (not a vacgen "
                "report face)" % os.path.basename(path))
        report_id = doc.get("reportId")
        for idx, assumption in enumerate(doc["assumptions"]):
            totals["reportAssumptions"] += 1
            if not isinstance(assumption, dict) or assumption.get("status") != "todo_seat":
                totals["reportNonTodoSeat"] += 1
                continue
            totals["reportTodoSeat"] += 1
            type_head = " ".join((assumption.get("typeHead") or "").split())
            add_member(clusters, assumption_shape_key(assumption), make_member(
                "report", path, {"index": idx}, report_id,
                assumption.get("kind"), assumption.get("name"), type_head,
                str(assumption["familyId"]) if assumption.get("familyId") else None,
                assumption.get("confidence"), assumption.get("degraded")))
    cluster_list = finalize_clusters(clusters, totals)
    fingerprint = hashlib.sha256(
        ("\n".join(sorted(digest_lines)) + "\n").encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA,
        "tool": {"name": PROG, "version": TOOL_VERSION},
        "inputs": {
            "ledgers": [os.path.basename(p) for p in ledgers],
            "reports": [os.path.basename(p) for p in reports],
        },
        "inputFingerprint": "sha256:" + fingerprint,
        "totals": totals,
        "clusters": cluster_list,
        "rules": dict(RULES),
        "negativeFinding": dict(NEGATIVE_FINDING),
    }


def finalize_clusters(clusters, totals):
    """Cluster assembly with the fixed ordering rules; updates totals."""
    cluster_list = []
    for key in sorted(clusters):
        members = sorted(clusters[key]["members"], key=member_sort_key)
        family_ids = sorted({m["familyId"] for m in members if m.get("familyId")})
        degraded = {}
        for m in members:
            flag = m.get("degraded")
            if flag:
                degraded[flag] = degraded.get(flag, 0) + 1
        variants = sorted({m["text"] for m in members if m.get("text")})
        cluster_list.append({
            "shapeKey": key,
            "count": len(members),
            "explicitFamilyIds": family_ids,
            "degradedCounts": degraded,
            "variants": variants,
            "members": members,
        })
    totals["clusters"] = len(cluster_list)
    totals["gaps"] = sum(c["count"] for c in cluster_list)
    return cluster_list


RULES = {
    "familyShapeKey": ("fam:<familyId> when an explicit familyId is present "
                       "(report assumption field, ledger entry field or ledger "
                       "source field, or the family token extracted from ledger "
                       "points after the TODO-SEAT token); otherwise "
                       "shape:<normalized text with identifier tokens replaced "
                       "by <id>, digit runs by <num>, whitespace collapsed>"),
    "ledgerGapClass": ("an entry counts as a gap when its category (top level "
                       "or source, under the category key or the zh key "
                       "spelling) equals a vacgen exp-draft pitfall category "
                       "token (U+5751 producer-real or U+5748 legacy), or the "
                       "protocol token TODO-SEAT occurs in points or evidence, "
                       "or evidence contains status=todo_seat"),
    "ordering": ("clusters sorted by shapeKey byte order; members sorted by "
                 "(origin, file, line-or-index, id); family, variant and "
                 "degraded lists sorted and distinct; JSON keys sorted; input "
                 "files processed in sorted path order with duplicates "
                 "collapsed"),
    "determinism": ("no wall clock, no random, no absolute paths in the "
                    "report (basenames only); identical inputs produce "
                    "byte-identical output (acceptance item R5)"),
}

NEGATIVE_FINDING = {
    "scannedWhat": ("gap-class ledger entries (pitfall category token, "
                    "TODO-SEAT in points or evidence, status=todo_seat in "
                    "evidence) in the --ledger JSONL files, and assumptions[] "
                    "entries with status todo_seat in the --reports JSON "
                    "files; nothing else"),
    "notScanned": ("free text outside the recognized fields (batch, tool, "
                   "source free-text keys); aliased gap markers in other "
                   "spellings; vacgen report faces other than assumptions[] "
                   "(coverage, cast, verdict, negativeFinding)"),
    "nonAbsoluteClaim": True,
    "aliasesNotExhausted": True,
    "rescanCondition": ("ledger or report inputs refreshed (a new exp append "
                        "or a new vacgen run), or the gap-class token set "
                        "changes"),
}


def render_report(report):
    """Deterministic JSON text: sorted keys, fixed indent, escaped non-ASCII
    (carried data appears as JSON escapes), trailing newline."""
    return json.dumps(report, sort_keys=True, indent=2,
                      ensure_ascii=True) + "\n"


# ------------------------------------------------------------- selftest ----

def selftest():
    """Embedded vectors on tmp-synthesized fixtures; zero network, zero real
    repo touch, byte-identical rerun assertions (R5)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="")
        except (AttributeError, OSError, ValueError):
            pass
    failures = []
    passed = 0

    def run(name, thunk):
        nonlocal passed
        try:
            detail = thunk()
        except AssertionError as exc:
            failures.append("%s -- %s" % (name, str(exc) or "assertion failed"))
        except Exception as exc:  # fail loud with the cause named
            failures.append("%s -- %s: %r" % (name, type(exc).__name__, exc))
        else:
            passed += 1
            print("PASS %s -- %s" % (name, detail or "ok"))

    def assert_true(cond, message):
        if not cond:
            raise AssertionError(message)

    def run_cli(args):
        import subprocess
        tool = os.path.abspath(__file__)
        return subprocess.run(
            [sys.executable, "-I", "-X", "utf8", tool] + [str(a) for a in args],
            capture_output=True, timeout=120)

    def write(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def check_shape_keys():
        a = abstract_shape("  (1 / 2) <  s.re ")
        b = abstract_shape("(1 / 2) < s.re")
        assert_true(a == b, "whitespace normalization differs: %r vs %r" % (a, b))
        assert_true(a == "shape:(<num> / <num>) < <id>",
                    "unexpected abstraction: %r" % a)
        c = abstract_shape("n <= m")
        assert_true(c == "shape:<id> <= <id>", "unexpected abstraction: %r" % c)
        return "abstraction and normalization stable"

    def check_report_clustering(tmp):
        report = {
            "reportId": "vacgenv2-fix-001",
            "assumptions": [
                {"kind": "assumption", "name": "s", "typeHead": "(1 / 2) < s.re",
                 "status": "todo_seat", "familyId": "ineq.real.const-lt-field-re",
                 "confidence": None, "matchedTarget": None, "degraded": None},
                {"kind": "assumption", "name": "t", "typeHead": "0 < eps",
                 "status": "todo_seat", "familyId": None,
                 "confidence": None, "matchedTarget": None, "degraded": None},
                {"kind": "assumption", "name": "u", "typeHead": "0 < eps",
                 "status": "todo_seat", "familyId": None,
                 "confidence": None, "matchedTarget": None, "degraded": None},
                {"kind": "assumption", "name": "v", "typeHead": "0 < delta",
                 "status": "todo_seat", "familyId": None,
                 "confidence": None, "matchedTarget": None, "degraded": None},
                {"kind": "assumption", "name": "w", "typeHead": "(1 / 2) < s.re",
                 "status": "recognized", "familyId": "ineq.real.const-lt-field-re",
                 "confidence": "HIGH", "matchedTarget": "assumption.type",
                 "degraded": None},
            ],
        }
        path = os.path.join(tmp, "report.json")
        write(path, json.dumps(report))
        got = aggregate([], [path])
        keys = [c["shapeKey"] for c in got["clusters"]]
        assert_true(keys == ["fam:ineq.real.const-lt-field-re",
                             "shape:<num> < <id>"],
                    "cluster keys wrong: %r" % keys)
        assert_true(got["clusters"][0]["count"] == 1, "explicit family count wrong")
        assert_true(got["clusters"][0]["explicitFamilyIds"] ==
                    ["ineq.real.const-lt-field-re"], "explicit family list wrong")
        assert_true(got["clusters"][1]["count"] == 3, "shape cluster count wrong")
        assert_true(got["clusters"][1]["variants"] == ["0 < delta", "0 < eps"],
                    "variants should be distinct and sorted")
        assert_true(got["totals"]["reportTodoSeat"] == 4
                    and got["totals"]["reportNonTodoSeat"] == 1,
                    "todo-seat totals wrong: %r" % got["totals"])
        assert_true(got["totals"]["gaps"] == 4, "gaps total wrong")
        return "explicit family, derived shape, recognized excluded"

    def check_ledger_gap_class(tmp):
        gap_line = {
            "schema": "rocqwash-exp/1", "id": "fix-001", "ts": "T0",
            "tool": "vacgen2", "batch": "fix-batch",
            "points": ("premise face not covered by any taxonomy row (TODO-SEAT "
                       "counted, no silent degradation): ineq.real.const-lt-field-re "
                       "@ D:/fix/target.lean"),
            "evidence": "report.json (assumptions[] status=todo_seat)",
            "fingerprint": "0" * 64,
        }
        other_line = {
            "schema": "rocqwash-exp/1", "id": "fix-002", "ts": "T0",
            "tool": "periscope", "batch": "fix-batch",
            "points": "export API query redirect precedent, eight legs lost",
            "evidence": "raw/fix.netred.txt:3-11", "fingerprint": "1" * 64,
        }
        path = os.path.join(tmp, "ledger.jsonl")
        write(path, json.dumps(gap_line) + "\n" + json.dumps(other_line) + "\n")
        got = aggregate([path], [])
        assert_true(got["totals"]["ledgerEntries"] == 2, "entry count wrong")
        assert_true(got["totals"]["ledgerGapEntries"] == 1
                    and got["totals"]["ledgerNonGapEntries"] == 1,
                    "gap-class split wrong: %r" % got["totals"])
        assert_true(got["clusters"][0]["shapeKey"] ==
                    "fam:ineq.real.const-lt-field-re",
                    "family extraction failed: %r" % got["clusters"][0]["shapeKey"])
        assert_true(got["clusters"][0]["members"][0]["ref"] == {"line": 1},
                    "member ref wrong")
        return "TODO-SEAT token and family extraction recognized"

    def check_ledger_category_token(tmp):
        draft_entry = {
            "id": "vacgenv2-abcdef01-1", "date": "T0", "tool": "vacgen2",
            "category": CATEGORY_PITFALL,
            "points": "premise face not covered by any taxonomy row",
            "evidencePointer": "report.json (assumptions[] status=todo_seat)",
            "erratumBlock": None,
            "rescanCondition": "taxonomy row generation",
        }
        path = os.path.join(tmp, "ledger-cat.jsonl")
        write(path, json.dumps({"schema": "rocqwash-exp/1", "id": "fix-003",
                                "ts": "T0", "tool": "vacgen2", "batch": "b",
                                "points": draft_entry["points"],
                                "evidence": draft_entry["evidencePointer"],
                                "fingerprint": "2" * 64,
                                "source": draft_entry}) + "\n")
        got = aggregate([path], [])
        assert_true(got["totals"]["ledgerGapEntries"] == 1,
                    "pitfall category token not recognized")
        assert_true(got["clusters"][0]["shapeKey"].startswith("shape:"),
                    "category-only entry should fall to shape key")
        return "pitfall category token recognized via source dict"

    def check_ledger_category_aligned(tmp):
        # The aligned category rule: the producer-real token U+5751 and the
        # legacy token U+5748, under the zh key and the category key, at
        # both levels. The zh-key source shape is the standing periscope
        # row in docs/gap-feed-ledger.jsonl.
        zh_row = {
            "schema": "rocqwash-exp/1", "id": "fix-013", "ts": "T0",
            "tool": "periscope", "batch": "b",
            "points": "the window sentinel wrote its log outside the "
                      "declared output directory",
            "evidence": "wf-script.ts:112 vs the on-disk log location",
            "fingerprint": "4" * 64,
            "source": {"id": "fix-013", "\u7c7b\u522b": "\u5751"},
        }
        legacy_row = {
            "schema": "rocqwash-exp/1", "id": "fix-014", "ts": "T0",
            "tool": "vacgen2", "batch": "b",
            "points": "premise face not covered by any taxonomy row",
            "evidence": "report.json (assumptions[] status=todo_seat)",
            "fingerprint": "5" * 64,
            "source": {"id": "fix-014", "category": "\u5748"},
        }
        top_row = {
            "schema": "rocqwash-exp/1", "id": "fix-015", "ts": "T0",
            "tool": "vacgen2", "batch": "b",
            "points": "premise face not covered by any taxonomy row",
            "evidence": "report.json (assumptions[] status=todo_seat)",
            "fingerprint": "6" * 64,
            "\u7c7b\u522b": "\u5751",
        }
        path = os.path.join(tmp, "ledger-cat-aligned.jsonl")
        write(path, "\n".join(json.dumps(r) for r in (zh_row, legacy_row,
                                                      top_row)) + "\n")
        got = aggregate([path], [])
        assert_true(got["totals"]["ledgerGapEntries"] == 3,
                    "aligned category rule missed a row: %r" % got["totals"])
        assert_true(got["totals"]["ledgerNonGapEntries"] == 0,
                    "aligned rule overcounted non-gap: %r" % got["totals"])
        return ("producer token, legacy token, zh key and top-level key "
                "all recognized")

    def check_degraded_hole(tmp):
        report = {"reportId": "vacgenv2-fix-002", "assumptions": [
            {"kind": "assumption", "name": "h", "typeHead": "_",
             "status": "todo_seat", "familyId": None, "confidence": None,
             "matchedTarget": None, "degraded": "hole"},
        ]}
        path = os.path.join(tmp, "report-hole.json")
        write(path, json.dumps(report))
        got = aggregate([], [path])
        assert_true(got["clusters"][0]["degradedCounts"] == {"hole": 1},
                    "degraded accounting wrong: %r" % got["clusters"][0])
        return "degraded hole accounted in its cluster"

    def check_zero_gaps(tmp):
        path = os.path.join(tmp, "empty.jsonl")
        write(path, '{"schema": "rocqwash-exp/1", "id": "fix-004", "ts": "T0",'
                    ' "tool": "x", "batch": "b", "points": "plain precedent",'
                    ' "fingerprint": "3"}\n')
        got = aggregate([path], [])
        assert_true(got["clusters"] == [] and got["totals"]["gaps"] == 0,
                    "zero-gap face wrong")
        assert_true(got["negativeFinding"]["nonAbsoluteClaim"] is True,
                    "negative finding block missing")
        return "empty cluster list is data"

    def check_corrupt_inputs(tmp):
        bad = os.path.join(tmp, "bad.jsonl")
        write(bad, '{"id": "ok"}\nnot-json-at-all\n')
        try:
            aggregate([bad], [])
        except GapInputError as exc:
            assert_true("line 2" in str(exc), "error must name the line: %r" % str(exc))
        else:
            raise AssertionError("corrupt ledger did not fail loud")
        foreign = os.path.join(tmp, "foreign.json")
        write(foreign, '{"unrelated": true}')
        try:
            aggregate([], [foreign])
        except GapInputError as exc:
            assert_true("assumptions" in str(exc), "error must name the face")
        else:
            raise AssertionError("foreign report did not fail loud")
        return "corrupt ledger line and foreign report fail loud"

    def check_r5_byte_identical(tmp):
        report = {"reportId": "vacgenv2-fix-003", "assumptions": [
            {"kind": "assumption", "name": "s", "typeHead": "(3 / 4) < t.re",
             "status": "todo_seat", "familyId": None, "confidence": None,
             "matchedTarget": None, "degraded": None},
        ]}
        ledger = {"schema": "rocqwash-exp/1", "id": "fix-005", "ts": "T0",
                  "tool": "vacgen2", "batch": "b",
                  "points": "premise face not covered by any taxonomy row "
                            "(TODO-SEAT counted, no silent degradation): "
                            "ineq.real.const-lt-field-re @ D:/fix/x.lean",
                  "evidence": "status=todo_seat", "fingerprint": "4" * 64}
        rpath = os.path.join(tmp, "r.json")
        lpath = os.path.join(tmp, "l.jsonl")
        write(rpath, json.dumps(report))
        write(lpath, json.dumps(ledger) + "\n")
        out1 = os.path.join(tmp, "g1.json")
        out2 = os.path.join(tmp, "g2.json")
        shared = os.path.join(tmp, "g.json")
        p1 = run_cli(["--ledger", lpath, "--reports", rpath, "--out", out1, "--json"])
        p2 = run_cli(["--ledger", lpath, "--reports", rpath, "--out", out2, "--json"])
        assert_true(p1.returncode == 0 and p2.returncode == 0,
                    "CLI rc nonzero: %r %r" % (p1.returncode, p2.returncode))
        with open(out1, "rb") as fh:
            d1 = fh.read()
        with open(out2, "rb") as fh:
            d2 = fh.read()
        assert_true(d1 == d2, "out files differ across runs (R5 red)")
        p3 = run_cli(["--ledger", lpath, "--reports", rpath, "--out", shared, "--json"])
        p4 = run_cli(["--ledger", lpath, "--reports", rpath, "--out", shared, "--json"])
        assert_true(p3.returncode == 0 and p4.returncode == 0,
                    "shared-out CLI rc nonzero")
        assert_true(p3.stdout == p4.stdout,
                    "stdout bytes differ across runs (R5 red)")
        assert_true(p3.stdout.startswith(d1)
                    and p3.stdout[len(d1):].startswith(b"[GAP-LEDGER] "),
                    "stdout must be the JSON text plus the one-line summary")
        got = json.loads(d1.decode("utf-8"))
        assert_true(got["schema"] == SCHEMA, "schema face wrong")
        assert_true(got["totals"]["gaps"] == 2 and got["totals"]["clusters"] == 2,
                    "mixed-source totals wrong: %r" % got["totals"])
        return "two runs byte-identical (out file and stdout, R5)"

    def check_exit_codes(tmp):
        p = run_cli(["--ledger", os.path.join(tmp, "missing.jsonl")])
        assert_true(p.returncode == 9, "missing input rc: %r" % p.returncode)
        p = run_cli(["--ledger"])
        assert_true(p.returncode == 2, "dangling flag rc: %r" % p.returncode)
        p = run_cli([])
        assert_true(p.returncode == 2, "no-input rc: %r" % p.returncode)
        p = run_cli(["--nonsense"])
        assert_true(p.returncode == 2, "unknown flag rc: %r" % p.returncode)
        return "exit codes 9/2 loud on named faces"

    with tempfile.TemporaryDirectory(prefix="gap_cluster_selftest_") as tmp:
        run("shape-keys", check_shape_keys)
        run("report-clustering", lambda: check_report_clustering(tmp))
        run("ledger-gap-class", lambda: check_ledger_gap_class(tmp))
        run("ledger-category-token", lambda: check_ledger_category_token(tmp))
        run("ledger-category-aligned", lambda: check_ledger_category_aligned(tmp))
        run("degraded-hole", lambda: check_degraded_hole(tmp))
        run("zero-gaps", lambda: check_zero_gaps(tmp))
        run("corrupt-inputs", lambda: check_corrupt_inputs(tmp))
        run("r5-byte-identical", lambda: check_r5_byte_identical(tmp))
        run("exit-codes", lambda: check_exit_codes(tmp))
    if failures:
        for f in failures:
            print("FAIL %s" % f)
        print("SELFTEST RED (%d passed, %d failed)" % (passed, len(failures)))
        return 1
    print("SELFTEST GREEN (%d passed)" % passed)
    return 0


# ------------------------------------------------------------------ main ----

def main(argv=None):
    # newline="" keeps stdout LF (no Windows CRLF translation): the stdout
    # JSON face stays byte-identical to the --out file face (R5).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="")
        except (AttributeError, OSError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Aggregate TODO-SEAT and gap entries into a "
                    "family-shape-keyed gap ledger (schema %s)." % SCHEMA)
    ap.add_argument("--ledger", action="append", default=[], metavar="PATH",
                    help="experience ledger JSONL (rocqwash-exp/1); repeatable")
    ap.add_argument("--reports", action="append", default=[], metavar="PATH",
                    help="vacgen report JSON file, or a directory of *.json "
                         "files; repeatable")
    ap.add_argument("--out", default=None, metavar="FILE",
                    help="write the gap ledger JSON to FILE")
    ap.add_argument("--json", action="store_true",
                    help="print the gap ledger JSON to stdout")
    args = ap.parse_args(argv)
    if not args.ledger and not args.reports:
        sys.stderr.write("usage error: at least one --ledger or --reports "
                         "input is required\n")
        return 2
    try:
        report = aggregate(args.ledger, args.reports)
    except GapInputError as exc:
        sys.stderr.write("FAIL-LOUD: %s\n" % exc)
        return 9
    except OSError as exc:
        sys.stderr.write("FAIL-LOUD: input unreadable: %s\n" % exc)
        return 9
    text = render_report(report)
    wrote = None
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        except OSError as exc:
            sys.stderr.write("FAIL-LOUD: cannot write %s: %s\n" % (args.out, exc))
            return 9
        wrote = args.out
    if args.json or not wrote:
        sys.stdout.write(text)
    if wrote:
        print("[GAP-LEDGER] %s (gaps=%d clusters=%d)"
              % (os.path.abspath(wrote).replace("\\", "/"),
                 report["totals"]["gaps"], len(report["clusters"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
