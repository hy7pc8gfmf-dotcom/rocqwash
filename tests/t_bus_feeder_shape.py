#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_bus_feeder_shape.py: direct-run shape shell for tools/bus_feeder.py.

    Purpose.  Smoke the gap-ledger feeder offline: the CLI face naming,
      the tool's own frozen selftest group, the real swap sample
      docs/symbiosis-swap-round1.jsonl through the dry-run face (zero
      writes), the end-to-end leg from a symbiosis_bus export package to
      family-shape-keyed gap rows, idempotent re-feed (both skip axes),
      damaged-package refusals, usage and exit codes, the status mapping
      face, the write surface, and the gap_cluster aggregation boundary.

    Interface.  `py tests/t_bus_feeder_shape.py` (rostered in
      tests/run_tests.sh as case t_bus_feeder_shape on 20261115, audit
      finding P0-6; the roster count is derived one-way from the CASES
      block in tests/run_tests.sh by doc_lint's second check, and the
      README count lines follow that derived count); seven checks drive
      one tool's argparse face each in a subprocess.

    Dependencies.  Python 3 stdlib only; every check runs on temporary
      fixtures under one mkdtemp root; the repository is never written;
      zero network (NETRED: no network by construction); the real sample
      is read read-only.

    Evidence.  Every check runs a tool in a subprocess and asserts the
      exit code, the output face, or the fixture bytes on this machine;
      the end-to-end package is produced by symbiosis_bus export itself;
      the gap_cluster boundary is asserted from the aggregate() output
      face, not from prose.

    Exit-codes.  0 = all seven checks pass; 1 = any check red (fail-loud,
      the red check is printed; no silent downgrade).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "bus_feeder.py")
BUS_TOOL = os.path.join(REPO, "tools", "symbiosis_bus.py")
REAL_SAMPLE = os.path.join(REPO, "docs", "symbiosis-swap-round1.jsonl")
SWAP_SCHEMA = "rocqwash-symbio/1"
SWAP_KIND = "symbiosis-swap-envelope"
EXP_SCHEMA = "rocqwash-exp/1"
FIELDS = ("Purpose.", "Interface.", "Dependencies.", "Evidence.",
          "Exit-codes.")
FACES = ("feed", "status")
FLAGS = ("--swap", "--ledger", "--dry-run", "--selftest")
ANCHOR = "4c" * 20
SRC_REPO = "srcShape"
SEP = "\x1f"
PITFALL = "\u5751"  # the pitfall category token the producer emits
ZH_KEY = "\u7c7b\u522b"  # the zh category key spelling on the bus


def run_tool(tool, args):
    """Run a tool in a subprocess (stdout+stderr merged).  `-X utf8` pins
    the stdio encoding and `-I` isolates the child, mirroring the
    t_symbiosis_shape.py runner."""
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", tool]
                       + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def fingerprint(tool, points, evidence, batch):
    """Content key over the four carrier fields (the exp_port algorithm)."""
    payload = SEP.join([tool, points, evidence, batch])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def entry(eid, tool, points, evidence, batch, ts="2026-11-14T10:00:00Z",
          source=None):
    """A full rocqwash-exp/1 row (fixed ts: content-borne, so every
    derived expectation stays deterministic)."""
    row = {
        "schema": EXP_SCHEMA,
        "id": eid,
        "ts": ts,
        "tool": tool,
        "points": points,
        "evidence": evidence,
        "batch": batch,
        "fingerprint": fingerprint(tool, points, evidence, batch),
    }
    if source is not None:
        row["source"] = source
    return row


def canonical(obj):
    """The repo-wide canonical JSON line form (same bytes as the tools)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def write_lines(path, rows):
    """Write JSONL rows (parent dirs included)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def read_objects(path):
    """Parse a JSONL file into objects; an absent file reads as empty."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_bytes(path):
    """Byte content of a file; an absent file reads as empty so a red
    tool run records a fail line instead of crashing the shell."""
    if not os.path.isfile(path):
        return b""
    with open(path, "rb") as handle:
        return handle.read()


def swap_bytes(envelope_extra, entries):
    """Assemble swap package bytes: one envelope line, then the entries."""
    envelope = dict(envelope_extra)
    return canonical(envelope) + "\n" + \
        "".join(canonical(row) + "\n" for row in entries)


def envelope(count, anchor=ANCHOR, repo=SRC_REPO):
    """A well-formed rocqwash-symbio/1 envelope."""
    return {"schema": SWAP_SCHEMA, "kind": SWAP_KIND, "sourceRepo": repo,
            "anchor": anchor, "entryCount": count}


def snapshot(root):
    """Relative file paths under root, for the write-surface assertion."""
    found = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root))
    return found


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="t_bus_feeder_shape_")
    try:
        # Check 1: CLI face smoke - --help is rc=0 and names the two faces
        # plus the real flags; the tool source carries the five-field
        # header of the annotation standard.
        rc, out = run_tool(TOOL, ["--help"])
        flat = re.sub(r"-\s*\n\s*", "-", out)
        if rc != 0:
            fails.append("check1 --help should be rc=0 (rc=%d)\n%s"
                         % (rc, out))
        for name in FACES + FLAGS:
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

        # Check 2: the tool's own frozen selftest group is green, and the
        # real sample feeds dry-run with zero writes: the envelope line is
        # the rocqwash-symbio/1 envelope with 27 entries, the dry-run
        # reports at least one gap row, and no ledger file appears.
        rc, out = run_tool(TOOL, ["--selftest"])
        if rc != 0 or "BUS-FEEDER-SELFTEST PASS" not in out:
            fails.append("check2 --selftest should pass rc=0 (rc=%d)\n%s"
                         % (rc, out))
        if not os.path.isfile(REAL_SAMPLE):
            fails.append("check2 real sample absent: %s" % REAL_SAMPLE)
        else:
            rows = read_objects(REAL_SAMPLE)
            head = rows[0] if rows else {}
            if head.get("schema") != SWAP_SCHEMA or \
                    head.get("kind") != SWAP_KIND:
                fails.append("check2 real sample envelope drift: %r" % head)
            if head.get("entryCount") != len(rows) - 1:
                fails.append("check2 real sample entryCount mismatch: %r vs "
                             "%d entry lines" % (head.get("entryCount"),
                                                 len(rows) - 1))
            dry_ledger = os.path.join(tmp, "real", "gap-feed-ledger.jsonl")
            rc, out = run_tool(TOOL, ["feed", "--swap", REAL_SAMPLE,
                                      "--ledger", dry_ledger, "--dry-run"])
            if rc != 0 or "would-feed=" not in out:
                fails.append("check2 real-sample dry-run should be rc=0 "
                             "(rc=%d)\n%s" % (rc, out))
            m = re.search(r"would-feed=(\d+)", out)
            if m and int(m.group(1)) < 1:
                fails.append("check2 real sample should yield at least one "
                             "gap row (out=%r)" % out)
            if os.path.exists(dry_ledger):
                fails.append("check2 real-sample dry-run must not write "
                             "its ledger")

        # Check 3: end-to-end leg - a symbiosis_bus export package feeds
        # into gap rows: the TODO-SEAT row lands with its family-token
        # shape key, the plain row is excluded, carriers survive verbatim,
        # the route marker rides the envelope, and the row schema stays
        # rocqwash-exp/1 with the 64-hex fingerprint.
        seat_points = ("premise face not covered by any taxonomy row "
                       "(TODO-SEAT counted, no silent degradation): "
                       "ineq.real.const-lt-field-re @ D:/fix/target.lean")
        src_ledger = os.path.join(tmp, "src", "exp-ledger.jsonl")
        write_lines(src_ledger, [
            entry("S-GAP-1", "vacgen2", seat_points,
                  "report.json (assumptions[] status=todo_seat)", "b1"),
            entry("S-PLAIN", "exp_port", "a plain precedent entry",
                  "ev://plain", "b1"),
        ])
        pkg = os.path.join(tmp, "swap", "round1.jsonl")
        rc, out = run_tool(BUS_TOOL, ["export", "--ledger", src_ledger,
                                      "--out", pkg, "--source-repo",
                                      SRC_REPO, "--anchor", ANCHOR])
        if rc != 0 or "wrote 2 entries" not in out:
            fails.append("check3 symbiosis_bus export should write 2 "
                         "entries rc=0 (rc=%d)\n%s" % (rc, out))
        target = os.path.join(tmp, "target", "gap-feed-ledger.jsonl")
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg, "--ledger",
                                  target])
        if rc != 0 or "gapRows=1 nonGap=1 skipped=0 total=2" not in out:
            fails.append("check3 feed should land 1 of 2 rc=0 (rc=%d)\n%s"
                         % (rc, out))
        rows = read_objects(target)
        if len(rows) != 1:
            fails.append("check3 ledger should hold exactly the gap row, "
                         "got %d" % len(rows))
        else:
            row = rows[0]
            if row.get("id") != "S-GAP-1":
                fails.append("check3 the plain row must not land: %r"
                             % row.get("id"))
            if row.get("schema") != EXP_SCHEMA:
                fails.append("check3 row schema should stay %s: %r"
                             % (EXP_SCHEMA, row.get("schema")))
            mark = row.get("fingerprint")
            if not (isinstance(mark, str) and len(mark) == 64
                    and all(c in "0123456789abcdef" for c in mark)):
                fails.append("check3 row misses the 64-hex fingerprint: %r"
                             % mark)
            if row.get("shapeKey") != "fam:ineq.real.const-lt-field-re":
                fails.append("check3 shape key should be the family token, "
                             "got %r" % row.get("shapeKey"))
            if row.get("recognition") != "protocol-token":
                fails.append("check3 recognition wrong: %r"
                             % row.get("recognition"))
            if row.get("correlationId") != "feed:%s@%s" % (SRC_REPO, ANCHOR):
                fails.append("check3 route marker missing: %r"
                             % row.get("correlationId"))
            if (row.get("tool"), row.get("ts"), row.get("batch")) != \
                    ("vacgen2", "2026-11-14T10:00:00Z", "b1"):
                fails.append("check3 carriers not carried verbatim: %r"
                             % row)

        # Check 4: idempotent re-feed - the same package is a zero-delta
        # no-op (byte-identical ledger, id-axis skips); a twin (equal four
        # carriers under a new id) skips on the fingerprint axis; an id
        # collision with different gap content skips on the id axis and
        # leaves the present row untouched.
        before = read_bytes(target)
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg, "--ledger",
                                  target])
        if rc != 0 or "gapRows=0 nonGap=1 skipped=1" not in out \
                or "axis=id" not in out:
            fails.append("check4 re-feed should skip rc=0 (rc=%d)\n%s"
                         % (rc, out))
        if read_bytes(target) != before:
            fails.append("check4 re-feed must leave the ledger "
                         "byte-identical")
        twin = entry("S-TWIN", "vacgen2", seat_points,
                     "report.json (assumptions[] status=todo_seat)", "b1")
        collision = entry("S-GAP-1", "other-tool",
                          "uncovered face (TODO-SEAT counted) repeated id",
                          "ev://x", "b2", ts="2026-11-15")
        pkg4 = os.path.join(tmp, "swap", "round4.jsonl")
        with open(pkg4, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(swap_bytes(envelope(2), [twin, collision]))
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg4, "--ledger",
                                  target])
        if rc != 0 or "axis=fingerprint" not in out or "axis=id" not in out:
            fails.append("check4 twin and collision should skip on both "
                         "axes rc=0 (rc=%d)\n%s" % (rc, out))
        if read_bytes(target) != before:
            fails.append("check4 skip faces must not mutate the ledger")

        # Check 5: refusals and usage - damaged packages exit 9 with zero
        # writes (bad json line, envelope schema drift, fingerprint drift);
        # usage faces exit 2; an absent package exits 9 without creating
        # its ledger.
        good = entry("S-GAP-1", "vacgen2", seat_points,
                     "report.json (assumptions[] status=todo_seat)", "b1")
        damaged = {
            "bad-json": canonical(envelope(1)) + "\nnot-json{\n",
            "schema-drift": swap_bytes(dict(envelope(0),
                                            schema="rocqwash-symbio/9"),
                                       []),
            "fp-drift": swap_bytes(envelope(1),
                                   [dict(good, points="tampered")]),
        }
        for name, payload in sorted(damaged.items()):
            refuse_dir = os.path.join(tmp, "refuse-" + name,
                                      "gap-feed-ledger.jsonl")
            refuse_pkg = os.path.join(tmp, "swap", "bad-%s.jsonl" % name)
            with open(refuse_pkg, "w", encoding="utf-8",
                      newline="\n") as handle:
                handle.write(payload)
            rc, out = run_tool(TOOL, ["feed", "--swap", refuse_pkg,
                                      "--ledger", refuse_dir])
            if rc != 9:
                fails.append("check5 %s should exit 9 (rc=%d)\n%s"
                             % (name, rc, out))
            if os.path.exists(refuse_dir):
                fails.append("check5 %s must not write its ledger" % name)
        rc, out = run_tool(TOOL, [])
        if rc != 2:
            fails.append("check5 a bare run should exit 2, got %d" % rc)
        rc, out = run_tool(TOOL, ["bogus"])
        if rc != 2:
            fails.append("check5 an unknown face should exit 2, got %d" % rc)
        rc, out = run_tool(TOOL, ["feed", "--ledger", target])
        if rc != 2:
            fails.append("check5 feed without --swap should exit 2, got %d"
                         % rc)
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg, "--swap", pkg,
                                  "--ledger", target])
        if rc != 2:
            fails.append("check5 feed with two --swap flags should exit 2, "
                         "got %d" % rc)
        absent_pkg = os.path.join(tmp, "swap", "absent.jsonl")
        no_dir = os.path.join(tmp, "nodir5", "gap-feed-ledger.jsonl")
        rc, out = run_tool(TOOL, ["feed", "--swap", absent_pkg, "--ledger",
                                  no_dir])
        if rc != 9:
            fails.append("check5 feed on an absent package should exit 9, "
                         "got %d" % rc)
        if os.path.exists(no_dir):
            fails.append("check5 absent-package feed must not create its "
                         "ledger")

        # Check 6: status and determinism - status answers the row count,
        # the route face and the shape mapping; a --swap face reports the
        # gap-entry split and the present/new counts; an absent ledger is
        # exit 9; the same package into a second fresh ledger replays
        # byte-identically.
        rc, out = run_tool(TOOL, ["status", "--ledger", target])
        if rc != 0 or "rows=1" not in out or "inboundFeed=1" not in out \
                or "shape=fam:ineq.real.const-lt-field-re" not in out:
            fails.append("check6 status incomplete (rc=%d)\n%s" % (rc, out))
        if "no swap file given" not in out:
            fails.append("check6 status without --swap should say so")
        rc, out = run_tool(TOOL, ["status", "--ledger", target, "--swap",
                                  pkg])
        if rc != 0 or "gapEntries=1" not in out or "presentInLedger=1" \
                not in out or "new=0" not in out:
            fails.append("check6 status --swap incomplete (rc=%d)\n%s"
                         % (rc, out))
        rc, out = run_tool(TOOL, ["status", "--ledger",
                                  os.path.join(tmp, "absent6",
                                               "gap-feed-ledger.jsonl")])
        if rc != 9:
            fails.append("check6 status on an absent ledger should exit 9, "
                         "got %d" % rc)
        replay = os.path.join(tmp, "replay", "gap-feed-ledger.jsonl")
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg, "--ledger",
                                  replay])
        if rc != 0:
            fails.append("check6 replay feed should be rc=0 (rc=%d)" % rc)
        if read_bytes(replay) != read_bytes(target):
            fails.append("check6 same package into two fresh ledgers must "
                         "replay byte-identically (determinism)")

        # Check 7: write surface plus the aggregation boundary - dry runs
        # and read faces add zero files, a real feed adds only its ledger;
        # gap_cluster aggregate() counts the TODO-SEAT row and the fed
        # zh-category row as gaps (the aligned category rule reads both
        # tokens under both key spellings; asserted from the aggregate
        # output face).
        before_set = snapshot(tmp)
        run_tool(TOOL, ["feed", "--swap", pkg, "--ledger",
                        os.path.join(tmp, "w7", "gap-feed-ledger.jsonl"),
                        "--dry-run"])
        run_tool(TOOL, ["status", "--ledger", target])
        after_dry = snapshot(tmp)
        if after_dry != before_set:
            fails.append("check7 dry/read faces added files: %r"
                         % sorted(after_dry - before_set))
        w7 = os.path.join(tmp, "w7", "gap-feed-ledger.jsonl")
        rc, out = run_tool(TOOL, ["feed", "--swap", pkg, "--ledger", w7])
        if rc != 0 or "gapRows=1" not in out:
            fails.append("check7 real feed failed (rc=%d)\n%s" % (rc, out))
        after_real = snapshot(tmp)
        if after_real - after_dry != {os.path.join("w7",
                                                   "gap-feed-ledger.jsonl")}:
            fails.append("check7 real feed wrote outside its ledger: %r"
                         % sorted(after_real - after_dry))
        zh_row = entry("S-ZH", "periscope-collection",
                       "the window sentinel wrote its log outside the "
                       "declared output directory",
                       "wf-script.ts:112 vs the on-disk log location",
                       "b1", ts="2026-11-13",
                       source={"id": "S-ZH", ZH_KEY: PITFALL})
        zh_ledger = os.path.join(tmp, "zh", "gap-feed-ledger.jsonl")
        zh_pkg = os.path.join(tmp, "swap", "zh.jsonl")
        with open(zh_pkg, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(swap_bytes(envelope(1), [zh_row]))
        rc, out = run_tool(TOOL, ["feed", "--swap", zh_pkg, "--ledger",
                                  zh_ledger])
        if rc != 0 or "gapRows=1" not in out:
            fails.append("check7 zh-category feed should land one row "
                         "(rc=%d)\n%s" % (rc, out))
        fed = read_objects(zh_ledger)
        if len(fed) != 1 or fed[0].get("recognition") != "category-token":
            fails.append("check7 zh-category row recognition wrong: %r"
                         % (fed[0].get("recognition") if fed else None))
        if not str(fed[0].get("shapeKey", "")).startswith("shape:") \
                if fed else True:
            fails.append("check7 zh-category row should take the abstract "
                         "shape key")
        script = (
            "import json, sys, tempfile\n"
            "sys.path.insert(0, r'%s')\n"
            "import gap_cluster\n"
            "got = gap_cluster.aggregate([r'%s'], [])\n"
            "got2 = gap_cluster.aggregate([r'%s'], [])\n"
            "print(json.dumps({'seatLedgerGaps': "
            "got['totals']['ledgerGapEntries'], 'seatKey': "
            "got['clusters'][0]['shapeKey'], 'zhLedgerGaps': "
            "got2['totals']['ledgerGapEntries']}))\n"
        ) % (os.path.join(REPO, "tools"), w7, zh_ledger)
        probe = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8",
                                "-c", script], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, cwd=REPO)
        face = probe.stdout.decode("utf-8", errors="replace").strip()
        try:
            face_data = json.loads(face.splitlines()[-1])
        except (ValueError, IndexError):
            face_data = {}
        if face_data.get("seatLedgerGaps") != 1 or \
                face_data.get("seatKey") != "fam:ineq.real.const-lt-field-re":
            fails.append("check7 gap_cluster should count the TODO-SEAT row "
                         "as a gap under its family key, got %r" % face)
        if face_data.get("zhLedgerGaps") != 1:
            fails.append("check7 the aligned category rule should count "
                         "the zh-category row: gap_cluster reads both key "
                         "spellings, got %r" % face)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T-BUS-FEEDER-SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-BUS-FEEDER-SHAPE SUITE SHELL PASS (7 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
