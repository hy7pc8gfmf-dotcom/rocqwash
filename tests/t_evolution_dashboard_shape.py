#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_evolution_dashboard_shape.py - suite shell for tools/evolution_dashboard.py.
    Purpose.  Smoke the self-evolution dashboard offline: the CLI face
      naming, the three-source aggregation face (experience ledger
      rocqwash-exp/1 rows, round ledger rocqwash-round/1 rows, vacgen v2
      report faces), the conversion math, the coverageLowerPct curve
      ordering with the TODO-SEAT delta and rise flag, the default/explicit
      absence rule, the exit-code convention, determinism of both output
      faces, and the read-only posture on the live repository.
    Interface.  `py tests/t_evolution_dashboard_shape.py` (run directly;
      deliberately not rostered in tests/run_tests.sh - the same coupling
      as tests/t_exp_port.py, tests/t_periscope_shape.py and
      tests/t_symbiosis_shape.py: the roster count is mechanically coupled
      to count lines in README.md through doc_lint's second check, and
      roster insertion belongs to the work stream holding that
      authorization).  Seven checks, each driving the tool's real argparse
      face in a subprocess, plus one live read (read-only, zero writes).
    Dependencies.  Python 3 stdlib only; fixture checks run under one
      mkdtemp root; the live check reads the repository's standing account
      paths only; zero network (NETRED: no network by construction).
    Evidence.  Every fixture check runs the tool in a subprocess and
      asserts the exit code, the output face, or the fixture bytes on this
      machine; the live check asserts only states the repository can
      honestly carry at its current vintage (the experience ledger
      present, the round ledger and report directory absent as data),
      never hard counts that a ledger append would invalidate.
    Exit-codes.  0 = all seven checks pass; 1 = any check red (fail-loud,
      each red check printed; no silent downgrade).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "evolution_dashboard.py")
SCHEMA = "rocqwash-evolution-dashboard/1"
FIELDS = ("Purpose.", "Interface.", "Dependencies.", "Evidence.",
          "Exit-codes.")
FLAGS = ("--repo", "--exp-ledger", "--rounds", "--reports", "--json-out",
         "--md-out", "--stdout", "--selftest")


def run(args):
    """Run the tool in a subprocess (stdout+stderr merged).  `-I` isolates
    the child and `-B` skips bytecode writing, mirroring the
    t_symbiosis_shape.py runner; the cwd pins the live-repository check to
    the real root regardless of where the shell sits."""
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", TOOL]
                       + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def canonical(obj):
    """The repo-wide canonical JSON line form (same bytes as the tools)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def seed(path, text):
    """Write one fixture file (parent dirs included)."""
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def seed_repo(root, populated):
    """Seed one fixture repository: the standing docs/ layout, populated
    or bare (the bare form drives the absent-defaults-as-data check)."""
    docs = os.path.join(root, "docs")
    if not populated:
        os.makedirs(docs, exist_ok=True)
        return docs
    exp_rows = [
        {"schema": "rocqwash-exp/1", "id": "E-%d" % i, "ts": ts,
         "tool": "fixture", "points": "p", "evidence": "e",
         "batch": batch, "fingerprint": "f" * 64}
        for i, (ts, batch) in enumerate(
            [("2026-11-13T10:00:00Z", "batch-a"),
             ("2026-11-14T10:00:00Z", "batch-a"),
             ("2026-11-15T10:00:00Z", "batch-b")], 1)]
    round_rows = [
        {"round_id": 1, "mode": "auto", "base_sha": "b" * 40,
         "head_sha": "h" * 40, "classes_applied": ["c1", "c2", "c3"],
         "admissions": [{"class": "c1"}, {"class": "c2"}],
         "files": ["x.py"], "verify_rc": 0, "oscillation_count": 0,
         "timestamp_utc": "2026-11-15T00:00:01Z"},
        {"round_id": 2, "mode": "auto", "base_sha": "b" * 40,
         "head_sha": "h" * 40, "classes_applied": ["c4"],
         "admissions": [{"class": "c4"}], "files": ["x.py"],
         "verify_rc": 1, "oscillation_count": 0,
         "timestamp_utc": "2026-11-15T00:00:02Z"}]
    reports = {
        "r1-cast.json": {"reportId": "vacgenv2-fix-001",
                         "coverage": {"recognized": 3, "todoSeats": 2,
                                      "total": 5, "coverageLowerPct": 60,
                                      "registeredAt":
                                      "2026-11-14T01:00:00Z"},
                         "cast": {"files": 8,
                                  "todoSeatsByFile": {"witness.lean": 2}}},
        "r2-map.json": {"mapId": "vacgenv2-preflight-002",
                        "generatedAt": "2026-11-15T01:00:00Z",
                        "aggregate": {"files": 9, "recognized": 6,
                                      "assumptionsTotal": 12,
                                      "coverageLowerPct": 50,
                                      "tierCounts": {"A": 0, "B": 0, "C": 0,
                                                     "D": 9},
                                      "unparsedCount": 0}},
    }
    seed(os.path.join(docs, "exp-ledger.jsonl"),
         "".join(canonical(row) + "\n" for row in exp_rows))
    seed(os.path.join(docs, "round-ledger.jsonl"),
         "".join(canonical(row) + "\n" for row in round_rows))
    for name, doc in sorted(reports.items()):
        seed(os.path.join(docs, "vacgen-reports", name),
             canonical(doc) + "\n")
    return docs


def read_bytes(path):
    """Byte content of a file; an absent file reads as empty so a red
    tool run records a fail line instead of crashing the shell."""
    if not os.path.isfile(path):
        return b""
    with open(path, "rb") as handle:
        return handle.read()


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="t_evolution_dashboard_shape_")
    try:
        # Check 1: CLI face smoke - --help is rc=0 and names every flag;
        # the tool source carries the five-field header of the annotation
        # standard.
        rc, out = run(["--help"])
        flat = re.sub(r"-\s*\n\s*", "-", out)
        if rc != 0:
            fails.append("check1 --help should be rc=0 (rc=%d)\n%s"
                         % (rc, out))
        for name in FLAGS:
            if name not in flat:
                fails.append("check1 --help should name %s\n%s"
                             % (name, flat))
        if os.path.isfile(TOOL):
            with open(TOOL, "r", encoding="utf-8") as handle:
                src = handle.read()
            for field in FIELDS:
                if field not in src:
                    fails.append("check1 tool header misses %s" % field)
        else:
            fails.append("check1 tool file absent: %s" % TOOL)

        # Check 2: three-source happy path on fixtures - exit 0, the
        # summary line, and the JSON face carry the conversion math
        # (greenPct=66, classConversionPct=75), the curve order, the
        # TODO-SEAT delta (+4) with the rise flag, and the latest reading.
        repo1 = os.path.join(tmp, "repo1")
        seed_repo(repo1, populated=True)
        out_json = os.path.join(tmp, "o1")
        os.makedirs(out_json, exist_ok=True)
        json_path = os.path.join(out_json, "dash.json")
        rc, out = run(["--repo", repo1, "--stdout", "json",
                       "--json-out", json_path])
        if rc != 0:
            fails.append("check2 happy path should exit 0 (rc=%d)\n%s"
                         % (rc, out))
        if "experienceLedger=3 entries / 2 batches" not in out:
            fails.append("check2 summary line should carry the ledger "
                         "reading\n%s" % out.splitlines()[0] if out else out)
        doc = {}
        try:
            with open(json_path, "r", encoding="utf-8") as handle:
                doc = json.load(handle)
        except (OSError, ValueError) as exc:
            fails.append("check2 json-out unreadable: %s" % exc)
        if doc.get("schema") != SCHEMA:
            fails.append("check2 schema should be %s, got %r"
                         % (SCHEMA, doc.get("schema")))
        rounds = doc.get("rounds", {})
        if (rounds.get("roundsTotal"), rounds.get("greenRounds"),
                rounds.get("greenPct")) != (2, 1, 50):
            fails.append("check2 rounds green face should be 2/1/50: %r"
                         % rounds)
        if (rounds.get("classesAppliedTotal"),
                rounds.get("admissionsTotal"),
                rounds.get("classConversionPct")) != (4, 3, 75):
            fails.append("check2 conversion face should be 4/3/75: %r"
                         % rounds)
        coverage = doc.get("coverage", {})
        curve = coverage.get("curve", [])
        if [row.get("runId") for row in curve] != \
                ["vacgenv2-fix-001", "vacgenv2-preflight-002"]:
            fails.append("check2 curve order wrong: %r"
                         % [row.get("runId") for row in curve])
        if curve and (curve[1].get("todoSeatsDelta"),
                      curve[1].get("rising")) != (4, True):
            fails.append("check2 delta/rise face wrong: %r" % curve[1])
        if coverage.get("latest", {}).get("runId") != \
                "vacgenv2-preflight-002":
            fails.append("check2 latest reading wrong: %r"
                         % coverage.get("latest"))

        # Check 3: determinism - a second run over the same fixtures is
        # byte-identical on both faces; --stdout json equals --json-out
        # bytes.
        rc2, out2 = run(["--repo", repo1, "--stdout", "json"])
        rc3, out3 = run(["--repo", repo1, "--stdout", "json"])
        if rc2 != 0 or rc3 != 0:
            fails.append("check3 reruns should exit 0 (rc=%d/%d)"
                         % (rc2, rc3))
        body2 = out2.split("\n", 1)[1] if "\n" in out2 else ""
        body3 = out3.split("\n", 1)[1] if "\n" in out3 else ""
        if body2 != body3 or not body2:
            fails.append("check3 --stdout json must be byte-identical "
                         "across runs")
        with open(json_path, "r", encoding="utf-8") as handle:
            if handle.read() != body2:
                fails.append("check3 --json-out bytes must equal the "
                             "--stdout json face")
        md_a = os.path.join(tmp, "mda.md")
        md_b = os.path.join(tmp, "mdb.md")
        run(["--repo", repo1, "--md-out", md_a])
        run(["--repo", repo1, "--md-out", md_b])
        if read_bytes(md_a) != read_bytes(md_b) or not read_bytes(md_a):
            fails.append("check3 --md-out must be byte-identical across "
                         "runs")

        # Check 4: markdown face shape - bilingual title, English table
        # headers, the absent-face data statements.
        with open(md_a, "r", encoding="utf-8") as handle:
            md = handle.read()
        if not md.startswith("# "):
            fails.append("check4 markdown should open with a title")
        if "Evolution Dashboard" not in md.splitlines()[0]:
            fails.append("check4 title should be bilingual: %r"
                         % md.splitlines()[0])
        for header in ("| Batch | Entries | First ts | Last ts |",
                       "| Metric | Value |",
                       "| Order | Time point | Run | Shape | Files | "
                       "Recognized | Total | TODO-SEAT | Delta | "
                       "coverageLowerPct |"):
            if header not in md:
                fails.append("check4 markdown misses table header %r"
                             % header)
        if "Thermometer reading" not in md or "Rise signal" not in md:
            fails.append("check4 markdown misses the thermometer face")

        # Check 5: absence rule - a bare repo runs exit 0 with every
        # source marked absent as data; an explicitly flagged absent path
        # exits 9 with zero writes.
        repo2 = os.path.join(tmp, "repo2")
        os.makedirs(repo2, exist_ok=True)
        rc, out = run(["--repo", repo2])
        if rc != 0 or out.count("absent") < 3:
            fails.append("check5 bare repo should exit 0 with three "
                         "absent marks (rc=%d)\n%s" % (rc, out[:200]))
        guard = os.path.join(tmp, "guard", "never.json")
        rc, out = run(["--repo", repo1, "--rounds",
                       os.path.join(tmp, "absent.json"),
                       "--json-out", guard])
        if rc != 9 or os.path.exists(guard):
            fails.append("check5 explicit absent rounds should exit 9 "
                         "with zero writes (rc=%d)" % rc)
        rc, out = run(["--repo", repo1, "--reports",
                       os.path.join(tmp, "absent-dir.json")])
        if rc != 9:
            fails.append("check5 explicit absent reports should exit 9, "
                         "got %d" % rc)

        # Check 6: corrupt and faceless inputs exit 9 (fail loud, zero
        # writes); the exit-code convention spot checks: bare tool misuse
        # of --stdout exits 2.
        repo3 = os.path.join(tmp, "repo3")
        seed(os.path.join(repo3, "docs", "exp-ledger.jsonl"),
             '{"schema": "rocqwash-exp/1", "id": "x"}\nnot-json{\n')
        rc, out = run(["--repo", repo3])
        if rc != 9:
            fails.append("check6 corrupt ledger line should exit 9, got "
                         "%d" % rc)
        repo4 = os.path.join(tmp, "repo4")
        seed(os.path.join(repo4, "docs", "vacgen-reports", "f.json"),
             '{"nothing": true}\n')
        rc, out = run(["--repo", repo4])
        if rc != 9:
            fails.append("check6 faceless report should exit 9, got %d"
                         % rc)
        rc, out = run(["--repo", repo1, "--stdout", "bogus"])
        if rc != 2:
            fails.append("check6 bad --stdout should exit 2, got %d" % rc)

        # Check 7: live-repository posture - the real repo reads
        # read-only at exit 0; the experience ledger reading is present;
        # the rounds face is a live counter, so the summary is asserted
        # only for consistency with the standing round ledger account
        # (admissions rows present -> rounds=N form, otherwise the
        # rounds=absent mark; both states are legal); nothing in the
        # repository is written.
        rc, out = run([])
        if rc != 0:
            fails.append("check7 live read should exit 0 (rc=%d)\n%s"
                         % (rc, out[:200]))
        ledger = os.path.join(REPO, "docs", "round-ledger.jsonl")
        rows_total = 0
        rows_admitted = 0
        if os.path.isfile(ledger):
            with open(ledger, "r", encoding="utf-8") as handle:
                for line in handle:
                    text = line.strip()
                    if not text or text.startswith("#"):
                        continue
                    rows_total += 1
                    try:
                        row = json.loads(text)
                    except ValueError:
                        continue
                    adm = row.get("admissions")
                    if isinstance(adm, list) and adm:
                        rows_admitted += 1
        summary = out.splitlines()[0] if out else out
        if "experienceLedger=" not in summary:
            fails.append("check7 live summary should carry the ledger "
                         "reading\n%s" % (summary or out[:200]))
        rounds_m = re.search(r"rounds=(\d+)", summary)
        if rows_admitted:
            if rounds_m is None:
                fails.append("check7 round ledger has admissions rows so "
                             "the live summary should read rounds=N\n%s"
                             % (summary or out[:200]))
            elif int(rounds_m.group(1)) != rows_total:
                fails.append("check7 rounds=%s should equal the %d rows "
                             "of the round ledger\n%s"
                             % (rounds_m.group(1), rows_total, summary))
        elif "rounds=absent" not in summary:
            fails.append("check7 round ledger has no admissions rows so "
                         "the live summary should read rounds=absent\n%s"
                         % (summary or out[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T-EVOLUTION-DASHBOARD-SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-EVOLUTION-DASHBOARD-SHAPE SUITE SHELL PASS "
                     "(7 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
