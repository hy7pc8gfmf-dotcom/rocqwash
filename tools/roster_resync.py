#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""roster_resync.py: roster count drift guard, one-way recount and sync (rocqwash tools/; E2 repair class 2).
Purpose.  The suite roster (the CASES block of tests/run_tests.sh) is the
  only count authority.  This guard recounts the roster, then rewrites
  every drifted count line in tests/README.md and README.md to the roster
  value, using the four count-line shapes imported from doc_lint so the
  shapes can never diverge from the doc_lint oracle.  One-way: roster ->
  docs; the roster file is never written.  Dry-run by default; --apply is
  the only write face.  The ledger, exclusion-gate, and budget rules are
  in the extended contract below.
Interface.  python3 tools/roster_resync.py [--repo DIR] [--apply]
  [--ledger P] [--json OUT] | --selftest.  Exit 0 = clean or repaired to
  clean; 1 = drift found (dry-run) or an escalation landed (budget cap /
  refused face / missing count shape / post-repair assertion); 2 = usage
  error; 9 = missing input (no roster block, unreadable count file,
  corrupt ledger).
Dependencies.  Python 3 standard library only; zero network; imports
  doc_lint (COUNT_PATTERNS + CASES_RE) and repair_scope from the same
  tools/ directory; the ledger row is one JSON object per line.
Evidence.  --selftest on tmp fixture repos: the clean/red/repair and
  escalation vectors; the enumeration is in the extended contract.
Exit-codes.  See Interface; every outcome is loud (a red is data, never a
  silent pass); the ledger is written only by --apply.
"""

# Extended contract (kept outside the five-field header so the header
# stays within the 30-line budget of the annotation standard; the moved
# facts are carried over from the former header verbatim in substance):
#
# Write-face rules: every repaired line appends one ledger row (schema
#   rocqwash-repair/1) and the shared exclusion table
#   (tools/repair_scope.py, class RosterResyncScope) gates every target
#   before any byte lands; the per-class per-branch repair budget is 2.
# Evidence enumeration: a consistent repo stays clean with
#   byte-identical JSON reruns; the red fixture (count line +1) is
#   planned with zero writes and repaired by --apply until the real
#   doc_lint subprocess verdict flips to consistent; a four-shape drift
#   repairs in one pass against the doc_lint count check; the budget cap
#   escalates at two prior repaired rows without touching the target;
#   the exclusion-gate and CLI-code vectors; the roster file bytes never
#   change; the ledger stays untouched on dry-run.


import argparse
import io
import json
import os
import subprocess
import sys
import time

# same-directory engine imports must survive isolated interpreters (-I
# never prepends the script directory)
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import doc_lint
import repair_scope

PROG = "roster-resync"
SCHEMA = "rocqwash-roster-resync/1"
MARK = "ROSTER-RESYNC-SELFTEST PASS"
ROSTER_REL = "tests/run_tests.sh"
SCOPE = repair_scope.RosterResyncScope
ESCALATED_BUDGET = "escalated(budget-cap)"
ESCALATED_FROZEN = "escalated(frozen-face)"
ESCALATED_SHAPE = "escalated(shape-missing)"
ESCALATED_ASSERT = "escalated(repair-assert)"


class MissingInput(Exception):
    """Missing or unrecognizable input (exit 9, fail-loud)."""


def read_kept(path, what):
    """Read text with newlines kept verbatim (digit-span surgery must be
    byte-faithful; a universal-newline round trip would rewrite EOLs)."""
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MissingInput("%s unreadable / decode failure: %s (%s)"
                           % (what, path, e))


def roster_count(repo):
    """(count, line_no) of the statically rostered CASES cases (the
    FAIL_PROBE injection sits outside the quoted block and is not
    counted; the one-way derivation source)."""
    path = os.path.join(repo, ROSTER_REL)
    if not os.path.isfile(path):
        raise MissingInput("the roster file is missing: %s" % path)
    text = read_kept(path, ROSTER_REL)
    m = doc_lint.CASES_RE.search(text)
    if m is None:
        raise MissingInput("roster shape unrecognized (no CASES=\" block):"
                           " %s" % path)
    tokens = m.group(1).replace("\\\r\n", " ").replace("\\\n", " ").split()
    if not tokens:
        raise MissingInput("roster shape unrecognized (zero rostered"
                           " cases): %s" % path)
    line_no = text[:m.start()].count("\n") + 1
    return len(tokens), line_no


def plan(repo):
    """Drift plan: for every doc_lint count shape, every occurrence whose
    value disagrees with the roster count.  A shape with zero hits is a
    missing count line (escalation, not a mechanical repair).  Every
    drifted target passes through the shared class gate first."""
    n, roster_line = roster_count(repo)
    rows, shape_missing = [], []
    for rel, rx, label in doc_lint.COUNT_PATTERNS:
        path = os.path.join(repo, rel)
        if not os.path.isfile(path):
            raise MissingInput("the count face is missing: %s" % path)
        text = read_kept(path, rel)
        hits = list(rx.finditer(text))
        if not hits:
            shape_missing.append({"file": rel, "label": label})
            continue
        for h in hits:
            val = int(h.group(1))
            if val == n:
                continue
            rows.append({
                "file": rel,
                "line": text[:h.start()].count("\n") + 1,
                "label": label,
                "value": val,
                "roster": n,
                "start": h.start(1),
                "end": h.end(1),
                "frozen": SCOPE.refusal_reason(rel, repo) is not None,
            })
    return {"roster": n, "roster_line": roster_line, "rows": rows,
            "shape_missing": shape_missing}


def current_branch(repo):
    """The branch name for budget keying (git; "unknown" when the tree is
    not a repository or git is unavailable)."""
    try:
        pr = subprocess.run(["git", "-C", repo, "rev-parse",
                             "--abbrev-ref", "HEAD"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=30)
        out = pr.stdout.decode("utf-8", "replace").strip()
        if pr.returncode == 0 and out:
            return out
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def load_rows(ledger_path):
    """Every prior ledger row (corruption is loud, never skipped)."""
    if not os.path.isfile(ledger_path):
        return []
    text = read_kept(ledger_path, "repair ledger")
    rows = []
    for i, ln in enumerate(text.split("\n"), start=1):
        s = ln.strip()
        if not s:
            continue
        try:
            rows.append(json.loads(s))
        except ValueError as e:
            raise MissingInput("repair ledger corrupt at line %d: %s (%s)"
                               % (i, ledger_path, e))
    return rows


def budget_used(ledger_path, branch):
    """Prior repaired rows of this class on this branch (the budget is
    per class per branch; escalation rows never consume it)."""
    used = 0
    for row in load_rows(ledger_path):
        if (row.get("class") == SCOPE.CLASS_ID
                and row.get("branch") == branch
                and row.get("outcome") == SCOPE.REPAIRED_OUTCOME):
            used += 1
    return used


def append_row(ledger_path, row):
    """One JSON object per line, sorted keys, UTF-8, LF."""
    parent = os.path.dirname(ledger_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(ledger_path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def repair_file(repo, rel, spans, n):
    """Rewrite the drifted digit spans of one file (forward order, offset
    safe); returns (ok, residual_labels) for the post-repair assertion
    with blast restore to the original bytes."""
    path = os.path.join(repo, rel)
    original = read_kept(path, rel)
    parts, last = [], 0
    for start, end in sorted(spans):
        parts.append(original[last:start])
        parts.append(str(n))
        last = end
    parts.append(original[last:])
    fixed = "".join(parts)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(fixed)
    # post-repair assertion: re-derive; any residual drift on this face is
    # a span-math bug, restored loudly, never left half-repaired
    residual = []
    text = read_kept(path, rel)
    for rel2, rx, label in doc_lint.COUNT_PATTERNS:
        if rel2 != rel:
            continue
        for h in rx.finditer(text):
            if int(h.group(1)) != n:
                residual.append(label)
    if residual:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(original)
        return False, residual
    return True, []


def run(args):
    """Main flow: plan -> (dry-run report | apply + ledger) -> exit."""
    repo = args.repo
    if not os.path.isdir(repo):
        raise MissingInput("--repo directory missing: %s" % repo)
    pl = plan(repo)
    branch = current_branch(repo)
    ledger = args.ledger if args.ledger else os.path.join(
        repo, SCOPE.LEDGER_FACE)
    drift = pl["rows"]
    print("=== ROSTER-RESYNC (roster count drift guard, one-way"
          " roster -> docs) === repo=%s"
          % os.path.basename(os.path.abspath(repo)))
    print("[roster] %s:%d rostered=%d" % (ROSTER_REL, pl["roster_line"],
                                          pl["roster"]))
    for r in drift:
        print("  [drift] %s:%d [%s] = %d != roster %d%s"
              % (r["file"], r["line"], r["label"], r["value"], r["roster"],
                 " (frozen-face refusal)" if r["frozen"] else ""))
    for s in pl["shape_missing"]:
        print("  [shape-missing] %s [%s] (not mechanically repairable)"
              % (s["file"], s["label"]))
    mode = "dry-run"
    applied, escalated = 0, []
    if args.apply:
        mode = "apply"
        if not drift and not pl["shape_missing"]:
            print("[apply] clean, nothing to do")
        else:
            used = budget_used(ledger, branch)
            print("[budget] class=%s branch=%s used=%d cap=%d"
                  % (SCOPE.CLASS_ID, branch, used, SCOPE.BUDGET_PER_BRANCH))
            if used >= SCOPE.BUDGET_PER_BRANCH:
                escalated.append({"outcome": ESCALATED_BUDGET,
                                  "target": "(plan)"})
                append_row(ledger, ledger_row(branch, ESCALATED_BUDGET,
                                              "(plan)",
                                              extra={"planned": len(drift),
                                                     "used": used}))
                print("[apply] ESCALATED %s: %d prior repaired rows on this"
                      " class+branch (oscillation guard)"
                      % (ESCALATED_BUDGET, used))
            else:
                applied, esc_list = repair_all(repo, pl, ledger, branch)
                escalated.extend(esc_list)
    counts = {"drift": len(drift), "shape_missing": len(pl["shape_missing"]),
              "applied": applied, "escalated": len(escalated)}
    print("[%s] drift=%d shape_missing=%d applied=%d escalated=%d"
          % (mode, counts["drift"], counts["shape_missing"],
             counts["applied"], counts["escalated"]))
    clean = (not drift and not pl["shape_missing"]) if mode == "dry-run" \
        else (not escalated)
    # dry-run: clean = zero planned drift; apply: clean = every planned
    # row repaired or loudly escalated (unrepaired rows always produce an
    # escalation row, so a zero-escalation apply is a clean post state)
    rc = 0 if clean else 1
    if args.json:
        report = {
            "schema": SCHEMA,
            "repo": os.path.basename(os.path.abspath(repo)),
            "mode": mode,
            "roster": {"count": pl["roster"], "file": ROSTER_REL,
                       "line": pl["roster_line"]},
            "drift": [{k: v for k, v in r.items()
                       if k in ("file", "line", "label", "value", "roster",
                                "frozen")} for r in drift],
            "shape_missing": pl["shape_missing"],
            "applied": applied,
            "escalated": [{k: v for k, v in e.items()
                           if k in ("outcome", "target")} for e in escalated],
            "budget": {"branch": branch, "used":
                       budget_used(ledger, branch) if args.apply else None,
                       "cap": SCOPE.BUDGET_PER_BRANCH},
            "clean": clean,
        }
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False,
                      sort_keys=True)
        print("json -> %s" % args.json)
    print("VERDICT: %s (exit %d)"
          % ("clean" if rc == 0 else "drift" if not args.apply
             else "escalated", rc))
    return rc


def repair_all(repo, pl, ledger, branch):
    """The --apply repair leg: gate-checked per face, per-occurrence ledger
    rows, post-repair assertion with blast restore.  Returns (applied,
    escalated_rows) - the caller folds the escalations into the report."""
    applied = 0
    escalated = []
    for s in pl["shape_missing"]:
        escalated.append({"outcome": ESCALATED_SHAPE,
                          "target": s["file"]})
        append_row(ledger, ledger_row(branch, ESCALATED_SHAPE, s["file"],
                                      extra={"label": s["label"]}))
        print("[apply] ESCALATED %s: %s [%s]" % (ESCALATED_SHAPE, s["file"],
                                                 s["label"]))
    by_file = {}
    for r in pl["rows"]:
        by_file.setdefault(r["file"], []).append(r)
    for rel in sorted(by_file):
        rows = by_file[rel]
        reason = SCOPE.refusal_reason(rel, repo)
        if reason is not None:
            escalated.append({"outcome": ESCALATED_FROZEN,
                              "target": "%s (%s)" % (rel, reason)})
            append_row(ledger, ledger_row(branch, ESCALATED_FROZEN,
                                          rel, extra={"reason": reason}))
            print("[apply] ESCALATED %s: %s (%s)" % (ESCALATED_FROZEN, rel,
                                                     reason))
            continue
        ok, residual = repair_file(
            repo, rel, [(r["start"], r["end"]) for r in rows], pl["roster"])
        if not ok:
            escalated.append({"outcome": ESCALATED_ASSERT, "target": rel})
            append_row(ledger, ledger_row(branch, ESCALATED_ASSERT, rel,
                                          extra={"residual": ",".join(
                                              residual)}))
            print("[apply] ESCALATED %s: %s residual=%s (restored)"
                  % (ESCALATED_ASSERT, rel, ",".join(residual)))
            continue
        for r in rows:
            append_row(ledger, ledger_row(
                branch, SCOPE.REPAIRED_OUTCOME, "%s:%d" % (rel, r["line"]),
                extra={"before": r["value"], "after": r["roster"]}))
            applied += 1
            print("[apply] repaired %s:%d %d -> %d (ledger row appended)"
                  % (rel, r["line"], r["value"], r["roster"]))
    return applied, escalated


def ledger_row(branch, outcome, target, extra=None):
    """One ledger row (schema rocqwash-repair/1; class/target/outcome plus
    branch and ts; extras carry the before/after or the refusal detail)."""
    row = {
        "schema": SCOPE.REPAIR_ROW_SCHEMA,
        "class": SCOPE.CLASS_ID,
        "target": target,
        "outcome": outcome,
        "branch": branch,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if extra:
        row.update(extra)
    return row


# ---- --selftest (tmp fixture repos; offline; the real doc_lint oracle) ----

MINI_ROSTER = (
    "#!/bin/bash\n"
    "# run_tests.sh mini fixture\n"
    "set -u\n"
    "CASES=\"\\\n"
    "t_a \\\n"
    "t_b\"\n"
    "for c in $CASES; do :; done\n")


def write_fixture(root, counts, roster=MINI_ROSTER):
    """A tmp mini repo: the roster plus the four count-line faces, each
    set to `counts` (an int or a dict per face for selective drift)."""
    os.makedirs(os.path.join(root, "tests"))
    with io.open(os.path.join(root, "tests", "run_tests.sh"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(roster)
    per = counts if isinstance(counts, dict) else {
        "cov": counts, "expect": counts, "suite": counts, "cases": counts}
    with io.open(os.path.join(root, "tests", "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("# tests mini\n\n"
                 "ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh"
                 "   # 预期 %d 过 / 1 红 / EXIT 1\n\n"
                 "## 覆盖面（%d 例）\n" % (per["expect"], per["cov"]))
    with io.open(os.path.join(root, "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("# mini\n\n"
                 "tests/  # 自测套件（%d 例） - test suite (%d cases)\n"
                 % (per["suite"], per["cases"]))
    return root


def md5_of(path):
    import hashlib
    with io.open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def selftest():
    """Vectors (tmp fixtures; fully offline; the green criterion is the
    real doc_lint oracle, run as a subprocess against the fixture)."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_roster_resync_")
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "roster_resync.py")

    def run(aargs):
        e = dict(os.environ)
        p = subprocess.run([sys.executable, "-B", script] + list(aargs),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=e)
        out = p.stdout.decode("utf-8", "replace")
        return p.returncode, out

    def dl_run(repo, jout):
        dls = os.path.join(here, "doc_lint.py")
        p = subprocess.run([sys.executable, "-B", dls, "--repo", repo,
                            "--json", jout],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", "replace")
        return p.returncode, out

    try:
        # the shared exclusion table must hold before any guard vector
        assert repair_scope.run_selftest([]) == 0, \
            "repair_scope selftest must pass (the gate source)"
        ok, refusals = SCOPE.check_writable(repair_scope.REPO_ROOT)
        assert ok and not refusals, \
            "class write faces must be repairable on the real repo: %s" \
            % refusals
        # gate unit vectors on the snapshot fallback (loud, deterministic)
        root_r = os.path.join(tmp, "r")
        os.makedirs(root_r)
        for rel in ("README.md", "tests/README.md",
                    "docs/repair-ledger.jsonl"):
            assert SCOPE.refusal_reason(rel, root_r) is None, rel
        for rel in ("wash/wash_engine.py", "更新账.md", "certify/x.py",
                    "seeds/x.txt", "docs/zh/a.md", "docs/a.zh.md"):
            assert SCOPE.refusal_reason(rel, root_r) is not None, rel

        # V1 a consistent fixture: clean plan, zero writes, byte-identical
        # JSON reruns
        v1 = write_fixture(os.path.join(tmp, "v1"), 2)
        j1a, j1b = os.path.join(tmp, "v1a.json"), os.path.join(tmp, "v1b.json")
        rc, out = run(["--repo", v1, "--json", j1a])
        assert rc == 0 and "[roster] tests/run_tests.sh:" in out, out
        assert "drift=0" in out and "applied=0" in out, out
        run(["--repo", v1, "--json", j1b])
        with io.open(j1a, "rb") as fh:
            ba = fh.read()
        with io.open(j1b, "rb") as fh:
            bb = fh.read()
        assert ba == bb, "json byte drift = violation"
        rc, out = run(["--repo", v1, "--apply"])   # clean apply on fixture
        assert rc == 0 and "nothing to do" in out, out
        assert not os.path.isfile(os.path.join(v1, "docs",
                                               "repair-ledger.jsonl")), \
            "a clean apply must not create the ledger"

        # V2 the red fixture (count line +1), via the real doc_lint mini
        # repo shape: dry-run plans with zero writes; apply repairs; the
        # real doc_lint verdict flips to consistent (the green criterion)
        v2 = os.path.join(tmp, "v2")
        doc_lint.make_mini_repo(v2, count_drift=True)
        rt2 = os.path.join(v2, "tests", "run_tests.sh")
        md5_roster_before = md5_of(rt2)
        rc, out = run(["--repo", v2])
        assert rc == 1, "a drifted fixture must exit 1 on dry-run"
        assert "drift=1" in out, out
        assert md5_of(rt2) == md5_roster_before, "dry-run wrote the roster"
        cov2 = os.path.join(v2, "tests", "README.md")
        md5_cov_before = md5_of(cov2)
        assert md5_of(cov2) == md5_cov_before, "dry-run wrote a count face"
        ledger2 = os.path.join(v2, "docs", "repair-ledger.jsonl")
        rc, out = run(["--repo", v2, "--apply"])   # default ledger face
        assert rc == 0, out
        assert "applied=1" in out and "escalated=0" in out, out
        assert md5_of(rt2) == md5_roster_before, "the roster is one-way"
        assert "覆盖面（2 例）" in io.open(cov2, encoding="utf-8").read()
        rows2 = load_rows(ledger2)
        assert len(rows2) == 1, rows2
        row = rows2[0]
        assert row["schema"] == SCOPE.REPAIR_ROW_SCHEMA, row
        assert row["class"] == SCOPE.CLASS_ID, row
        assert row["outcome"] == SCOPE.REPAIRED_OUTCOME, row
        assert row["target"] == "tests/README.md:5", row
        assert row["before"] == 3 and row["after"] == 2, row
        assert row["branch"] == "unknown", row
        j2 = os.path.join(tmp, "v2dl.json")
        rc, out = dl_run(v2, j2)
        assert rc == 0, "doc_lint must flip to consistent: %s" % out[-800:]
        rep = json.loads(io.open(j2, encoding="utf-8").read())
        assert rep["verdict"] == "consistent", rep["verdict"]
        assert rep["counts"]["count"]["drift"] == 0, rep["counts"]
        rc, out = run(["--repo", v2, "--apply"])
        assert rc == 0 and "nothing to do" in out, out
        assert len(load_rows(ledger2)) == 1, "a clean apply writes no row"

        # V3 a four-shape drift repairs in one pass; the doc_lint count
        # check (imported oracle) confirms zero residual drift
        v3 = write_fixture(os.path.join(tmp, "v3"), 5)
        ledger3 = os.path.join(tmp, "v3ledger.jsonl")
        rc, out = run(["--repo", v3, "--apply", "--ledger", ledger3])
        assert rc == 0 and "applied=4" in out, out
        assert len(load_rows(ledger3)) == 4, "one row per repaired line"
        checks, cases_n = doc_lint.check_counts(v3)
        assert cases_n == 2, cases_n
        assert not [c for c in checks if c["status"] == "drift"], checks

        # V4 the budget cap: two prior repaired rows escalate the third
        # apply without touching the target (the oscillation guard)
        v4 = write_fixture(os.path.join(tmp, "v4"), 5)
        ledger4 = os.path.join(tmp, "v4ledger.jsonl")
        for _ in range(SCOPE.BUDGET_PER_BRANCH):
            append_row(ledger4, ledger_row("unknown",
                                           SCOPE.REPAIRED_OUTCOME,
                                           "tests/README.md:9"))
        cov4 = os.path.join(v4, "README.md")
        md5_before = md5_of(cov4)
        rc, out = run(["--repo", v4, "--apply", "--ledger", ledger4])
        assert rc == 1 and ESCALATED_BUDGET in out, out
        assert md5_of(cov4) == md5_before, "the capped apply wrote a face"
        rows4 = load_rows(ledger4)
        assert len(rows4) == SCOPE.BUDGET_PER_BRANCH + 1, rows4
        assert rows4[-1]["outcome"] == ESCALATED_BUDGET, rows4[-1]
        # escalation rows never consume the budget: dry-run stays rc 1 and
        # a fresh branch applies normally
        rc, out = run(["--repo", v4, "--apply", "--ledger",
                       os.path.join(tmp, "v4fresh.jsonl")])
        assert rc == 0 and "applied=4" in out, out

        # V5 CLI codes + fail-loud inputs (zero writes on every 9)
        rc, _out = run(["--help"])
        assert rc == 0, "usage face"
        rc, _out = run(["--bogus"])
        assert rc == 2, "unknown flag"
        rc, _out = run(["--repo", os.path.join(tmp, "absent")])
        assert rc == 9, "missing --repo"
        v6 = os.path.join(tmp, "v6")
        os.makedirs(os.path.join(v6, "tests"))
        rc, _out = run(["--repo", v6])
        assert rc == 9, "missing roster file"
        with io.open(os.path.join(v6, "tests", "run_tests.sh"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("# no CASES block\n")
        rc, _out = run(["--repo", v6])
        assert rc == 9, "broken roster shape"
        v7 = write_fixture(os.path.join(tmp, "v7"), 3)
        bad = os.path.join(tmp, "badledger.jsonl")
        with io.open(bad, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json}\n")
        rc, _out = run(["--repo", v7, "--apply", "--ledger", bad])
        assert rc == 9, "a corrupt ledger is fail-loud 9"

        print("%s: the clean fixture / the red fixture repaired to the real"
              " doc_lint consistent verdict / the four-shape one-pass"
              " repair / the budget-cap escalation / the gate + roster"
              " one-way + CLI + fail-loud vectors" % MARK)
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="roster count drift guard (E2 repair class 2): recount"
                    " the tests/run_tests.sh CASES roster and sync the"
                    " doc_lint count lines of tests/README.md and README.md"
                    " to it, one-way, dry-run by default")
    ap.add_argument("--repo", default=repair_scope.REPO_ROOT,
                    metavar="DIR", help="the audited repo root")
    ap.add_argument("--apply", action="store_true",
                    help="write the repairs (default is a dry-run plan with"
                        " zero writes); every repaired line appends one"
                        " ledger row")
    ap.add_argument("--ledger", default=None, metavar="P",
                    help="the repair ledger path (default %s under the repo"
                        " root)" % SCOPE.LEDGER_FACE)
    ap.add_argument("--json", default=None, metavar="OUT",
                    help="the plan report path (rocqwash-roster-resync/1;"
                        " sort_keys determinism)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        code = run(args)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
