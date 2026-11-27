#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bus_feeder: feed a symbiosis swap package into the TODO-SEAT gap ledger.

    Purpose.  Read one offline swap package (rocqwash-symbio/1, the export
      face of tools/symbiosis_bus.py), select its gap-class entries by a
      documented recognition set, and land one gap row per selected entry
      in the gap feed ledger (default docs/gap-feed-ledger.jsonl), keyed
      by the family shape chain of tools/gap_cluster.py.  Ids and time
      points ride entry content; a repeated id or fingerprint skips
      loudly with zero writes; the experience ledger is never touched
      (the gap feed ledger is the single write face); no network face.

    Interface.  `bus_feeder.py feed --swap SWAP.jsonl [--ledger P]
      [--dry-run]` | `status [--ledger P] [--swap SWAP.jsonl ...]` |
      `--selftest`; feed takes exactly one --swap, status repeats it.

    Dependencies.  Python 3 stdlib (argparse/json/os/sys) plus first-party
      siblings for contract reuse, never for writes: tools/symbiosis_bus.py
      (swap reading, envelope validation, exit-taxonomy exceptions,
      canonical lines) and tools/gap_cluster.py (family shape keys); no
      clock and no randomness in the logic.

    Evidence.  --selftest frozen vectors on temporary fixtures;
      tests/t_bus_feeder_shape.py drives the real sample
      docs/symbiosis-swap-round1.jsonl through the dry-run face.

    Exit-codes.  0 face answered (skips, zero matches, zero gap rows are
      data); 1 selftest red; 2 usage or IO; 9 missing or corrupt input,
      nothing written.
"""
# Extended contract (kept outside the five-field block; annotation budget):
#
# Recognition set (gap-class selection; evaluated in this order, the first
#   hit wins and is reported in the row's "recognition" field):
#   1. the pitfall category token U+5751 under the top-level "category"
#      key, or under the source dict's "category" or zh "\u7c7b\u522b" key
#      (both spellings ride real packages: the vacgen exp-draft form
#      carries "category" (tools/vacgen.py:2470), the periscope round-1
#      drafts carry the zh key spelling);
#   2. the literal protocol token TODO-SEAT in points or evidence;
#   3. the literal status token status=todo_seat in evidence.
#   Divergence, closed (the gap-trigger alignment item): tools/gap_cluster.py pinned CATEGORY_PITFALL as the
#   escape "\u5748" (a different code point, U+5748) and read only the
#   "category" key spelling, so its category rule never matched the
#   U+5751 token its own producer emits; this tool pinned U+5751
#   verbatim and read both key spellings.  The gap_cluster category rule
#   now reads both tokens (U+5751 producer-real, U+5748 legacy) under
#   both key spellings at both levels (CATEGORY_PITFALL / CATEGORY_KEYS),
#   so a row selected here through the category token counts through the
#   same rule on the aggregation face (negative-finding boundary:
#   aliased gap markers beyond the declared set were not exhaustively
#   ruled out).
#
# Gap row shape (one canonical JSON line; the entry schema stays verbatim):
#   the swap entry carried verbatim (id / ts / tool / points / evidence /
#   batch / fingerprint, optional correlationId / source) plus three
#   schema increments outside the fingerprint domain:
#   correlationId  synthesized as "feed:<sourceRepo>@<anchor>" from the
#                  envelope when the entry carries none of its own;
#   shapeKey       the family shape key (fam:<familyId> when an explicit
#                  familyId is present on the entry or its source,
#                  fam:<token> when the points text carries a family
#                  token after TODO-SEAT, else shape:<abstracted text>);
#                  computed by gap_cluster.ledger_shape_key on the
#                  unmodified entry;
#   recognition    which recognition rule selected the entry
#                  (category-token | protocol-token | status-token).
#
# Idempotent seen set (the exp_port taxonomy, precedence preserved): an
#   entry whose id is already present skips on the id axis; otherwise an
#   entry whose fingerprint is already present skips on the fingerprint
#   axis; both print the loud skip line and write nothing, exit 0.  A
#   repeated id with a different fingerprint reports the collision on
#   the id axis; the row already present is never mutated (append-only).
#
# Write surface: feed writes only the gap feed ledger (default
#   docs/gap-feed-ledger.jsonl, --ledger overrides); feed --dry-run and
#   status write nothing; no face of this tool reads or writes the
#   experience ledger docs/exp-ledger.jsonl.
#
# Exit taxonomy (shared with tools/symbiosis_bus.py): BusInput -> 9
#   (missing or corrupt input, zero writes), BusIO -> 2 (OS-level
#   failure); usage errors exit 2 through argparse; a selftest red
#   exits 1.

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import gap_cluster
    import symbiosis_bus
except ImportError as exc:
    sys.stderr.write("bus_feeder: the sibling modules symbiosis_bus and "
                     "gap_cluster are required (%s)\n" % exc)
    sys.exit(9)

PROG = "bus_feeder"
PITFALL_TOKEN = "\u5751"  # the pitfall category token, code point U+5751
CATEGORY_KEYS = ("category", "\u7c7b\u522b")  # both key spellings on the bus
SEAT_TOKEN = gap_cluster.PROTOCOL_TOKEN        # the TODO-SEAT token
STATUS_TOKEN = gap_cluster.STATUS_TOKEN        # the status=todo_seat token
FEED_PREFIX = "feed:"
LEDGER_NAME = "gap-feed-ledger.jsonl"
RECOGNITION_CATEGORY = "category-token"
RECOGNITION_SEAT = "protocol-token"  # the TODO-SEAT protocol token rule
RECOGNITION_STATUS = "status-token"
SELFTEST_MARK = "BUS-FEEDER-SELFTEST PASS"
VECTOR_COUNT = 10


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_ledger(explicit):
    """--ledger wins; otherwise the in-repo default under docs/."""
    if explicit:
        return explicit
    return os.path.join(repo_root(), "docs", LEDGER_NAME)


def canonical(obj):
    """The repo-wide canonical JSON line form (delegates to symbiosis_bus)."""
    return symbiosis_bus.canonical(obj)


def source_dict(entry):
    """The source dict of an entry when it is one, else an empty dict."""
    src = entry.get("source")
    return src if isinstance(src, dict) else {}


def recognize_gap(entry):
    """Return the recognition rule name of a gap-class entry, else None.

    The three rules and their order are the documented recognition set;
    the category rule reads both key spellings at both levels and pins
    the producer's real token (U+5751), not the dead gap_cluster escape."""
    src = source_dict(entry)
    for key in CATEGORY_KEYS:
        if entry.get(key) == PITFALL_TOKEN or src.get(key) == PITFALL_TOKEN:
            return RECOGNITION_CATEGORY
    points = entry.get("points") or ""
    evidence = entry.get("evidence") or ""
    if SEAT_TOKEN in points or SEAT_TOKEN in evidence:
        return RECOGNITION_SEAT
    if STATUS_TOKEN in evidence:
        return RECOGNITION_STATUS
    return None


def build_row(entry, envelope):
    """One gap row: the entry verbatim plus the three schema increments."""
    row = dict(entry)
    correlation = entry.get("correlationId")
    if not isinstance(correlation, str) or not correlation:
        correlation = "%s%s@%s" % (FEED_PREFIX, envelope["sourceRepo"],
                                   envelope["anchor"])
    row["correlationId"] = correlation
    row["shapeKey"] = gap_cluster.ledger_shape_key(entry)
    row["recognition"] = recognize_gap(entry)
    return row


def read_feed_ledger(path):
    """Parse the gap feed ledger; None when absent; loud on damage."""
    if not os.path.isfile(path):
        return None
    rows = []
    try:
        handle = open(path, "r", encoding="utf-8")
    except OSError as exc:
        raise symbiosis_bus.BusIO("gap feed ledger unreadable: %s" % exc)
    with handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise symbiosis_bus.BusInput(
                    "gap feed ledger line %d is not valid JSON (%s): %s"
                    % (lineno, exc, os.path.abspath(path)))
            if not isinstance(obj, dict):
                raise symbiosis_bus.BusInput(
                    "gap feed ledger line %d is not a JSON object: %s"
                    % (lineno, os.path.abspath(path)))
            rows.append(obj)
    return rows


def append_row(path, row):
    """Append one canonical gap-row line; create the parent when needed."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(row) + "\n")


def select_entries(entries):
    """Split package entries into (selected gap entries, non-gap count)."""
    selected = []
    non_gap = 0
    for entry in entries:
        if recognize_gap(entry) is None:
            non_gap += 1
        else:
            selected.append(entry)
    return selected, non_gap


def cmd_feed(args):
    """Feed one swap package into the gap feed ledger.
    Input: one validated swap package plus the ledger path.  Output: one
    fed/skip line per selected gap entry plus one summary line on stdout;
    side effect: appended ledger lines only (a dry run writes nothing).
    Exit: 0 fed or skipped or dry-run (zero gap rows are data); 2 usage
    or IO; 9 ledger or package absent or damaged, nothing written."""
    path = resolve_ledger(args.ledger)
    rows = read_feed_ledger(path)
    swap_path = args.swaps[0]
    envelope, entries = symbiosis_bus.read_swap(swap_path, deep=True)
    selected, non_gap = select_entries(entries)
    seen_ids = {}
    seen_fps = {}
    for row in rows or []:
        rid = row.get("id")
        if isinstance(rid, str) and rid:
            seen_ids.setdefault(rid, row)
        mark = row.get("fingerprint")
        if isinstance(mark, str) and mark:
            seen_fps.setdefault(mark, row)
    fed = 0
    skipped = 0
    for entry in selected:
        if entry["id"] in seen_ids:
            skipped += 1
            if not args.dry_run:
                sys.stdout.write("skip id=%s axis=id ledger=%s\n"
                                 % (entry["id"], path))
            continue
        mark = entry["fingerprint"]
        if mark in seen_fps:
            skipped += 1
            if not args.dry_run:
                sys.stdout.write("skip id=%s axis=fingerprint ledger=%s\n"
                                 % (seen_fps[mark].get("id", "?"), path))
            continue
        row = build_row(entry, envelope)
        if not args.dry_run:
            append_row(path, row)
            sys.stdout.write("fed id=%s shapeKey=%s recognition=%s\n"
                             % (row["id"], row["shapeKey"],
                                row["recognition"]))
        fed += 1
    if args.dry_run:
        sys.stdout.write("feed: dry-run would-feed=%d would-skip=%d "
                         "nonGap=%d total=%d ledger=%s\n"
                         % (fed, skipped, non_gap, len(entries), path))
    else:
        sys.stdout.write("feed: gapRows=%d nonGap=%d skipped=%d total=%d "
                         "ledger=%s\n"
                         % (fed, non_gap, skipped, len(entries), path))
    return 0


def cmd_status(args):
    """Report the gap feed ledger and the shape-to-row mapping.
    Input: the ledger path plus optional swap packages.  Output: count
    and mapping lines on stdout; side effect: none.  Exit: 0 report
    printed (zero rows and an empty route set are data); 2 usage or IO;
    9 ledger or a swap file absent or damaged."""
    path = resolve_ledger(args.ledger)
    rows = read_feed_ledger(path)
    if rows is None:
        raise symbiosis_bus.BusInput("gap feed ledger not found: %s"
                                     % os.path.abspath(path))
    inbound = [row for row in rows
               if isinstance(row.get("correlationId"), str)
               and row["correlationId"].startswith(FEED_PREFIX)]
    routes = set()
    last_stamp = ""
    for row in inbound:
        tail = row["correlationId"][len(FEED_PREFIX):]
        routes.add(tail)
        stamp = row.get("ts")
        if isinstance(stamp, str) and stamp > last_stamp:
            last_stamp = stamp  # ISO strings order lexicographically
    sys.stdout.write("status: ledger=%s rows=%d inboundFeed=%d\n"
                     % (path, len(rows), len(inbound)))
    sys.stdout.write("status: routes=%s lastInboundTs=%s\n"
                     % (",".join(sorted(routes)),
                        last_stamp if last_stamp else "none"))
    shapes = {}
    for row in rows:
        key = row.get("shapeKey")
        if isinstance(key, str) and key:
            shapes.setdefault(key, []).append(str(row.get("id", "?")))
    if shapes:
        for key in sorted(shapes):
            ids = sorted(shapes[key])
            sys.stdout.write("status: shape=%s rows=%d ids=%s\n"
                             % (key, len(ids), ",".join(ids)))
    else:
        sys.stdout.write("status: shape= rows=0 (no shapeKey rows on the "
                         "ledger)\n")
    if not args.swaps:
        sys.stdout.write("status: no swap file given (pass --swap to count "
                         "a package against the ledger)\n")
    ledger_ids = set(row.get("id") for row in rows
                     if isinstance(row.get("id"), str))
    for swap_path in args.swaps or []:
        envelope, entries = symbiosis_bus.read_swap(swap_path, deep=False)
        selected, non_gap = select_entries(entries)
        present = sum(1 for entry in selected
                      if entry["id"] in ledger_ids)
        sys.stdout.write("status: swap=%s sourceRepo=%s entries=%d "
                         "gapEntries=%d nonGap=%d presentInLedger=%d new=%d\n"
                         % (swap_path, envelope["sourceRepo"], len(entries),
                            len(selected), non_gap, present,
                            len(selected) - present))
    return 0


class Capture:
    """Minimal stdout sink for one in-process CLI call."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def value(self):
        return "".join(self.parts)


def run_cli(argv):
    """Run main() in-process; SystemExit from argparse maps to its code."""
    saved = (sys.stdout, sys.stderr)
    sys.stdout = Capture()
    sys.stderr = Capture()
    try:
        try:
            rc = main(argv)
        except SystemExit as exit_obj:
            rc = exit_obj.code if isinstance(exit_obj.code, int) else 0
    finally:
        out, err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = saved
    return rc, out.value(), err.value()


def entry_fixture(eid, tool, points, evidence, batch, ts,
                  source=None, correlation=""):
    """One swap-package entry with a real exp_port fingerprint."""
    entry = {
        "schema": symbiosis_bus.exp_port.SCHEMA,
        "id": eid,
        "ts": ts,
        "tool": tool,
        "points": points,
        "evidence": evidence,
        "batch": batch,
        "fingerprint": symbiosis_bus.exp_port.fingerprint(
            tool, points, evidence, batch),
    }
    if source is not None:
        entry["source"] = source
    if correlation:
        entry["correlationId"] = correlation
    return entry


def swap_file(envelope_extra, entries):
    """Assemble swap file bytes from an envelope dict plus entry dicts."""
    envelope = dict(envelope_extra)
    return canonical(envelope) + "\n" + \
        "".join(canonical(entry) + "\n" for entry in entries)


def write_file(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def snapshot(root):
    """Relative file paths under root, for the write-surface assertion."""
    found = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            found.add(os.path.relpath(os.path.join(dirpath, name), root))
    return found


def rmtree(root):
    """Best-effort fixture teardown with os only (stdlib-tight)."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for name in filenames:
            try:
                os.remove(os.path.join(dirpath, name))
            except OSError:
                pass
        for name in dirnames:
            try:
                os.rmdir(os.path.join(dirpath, name))
            except OSError:
                pass
    try:
        os.rmdir(root)
    except OSError:
        pass


def selftest():
    """Temporary-fixture vectors; prints SELFTEST PASS, exits 0 on green."""
    fails = []
    base = (os.environ.get("TMP") or os.environ.get("TEMP")
            or os.environ.get("TMPDIR") or tempfile.gettempdir())
    if not base:
        sys.stderr.write("bus_feeder selftest: no scratch directory found "
                         "(set TMP)\n")
        return 9
    root = os.path.join(base, "bus_feeder_selftest_%d" % os.getpid())
    os.makedirs(root, exist_ok=True)
    try:
        vectors(root, fails)
    finally:
        rmtree(root)  # teardown tolerance only; vectors fail loudly above
    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (%d vectors)\n" % (SELFTEST_MARK, VECTOR_COUNT))
    return 0


def vectors(root, fails):
    """The frozen vector group; every failure appends to `fails`."""
    anchor = "3b" * 20
    envelope = {"schema": symbiosis_bus.SWAP_SCHEMA,
                "kind": symbiosis_bus.SWAP_KIND,
                "sourceRepo": "srcA", "anchor": anchor, "entryCount": 3}
    zh_key = "\u7c7b\u522b"
    entries = [
        entry_fixture("GAP-1", "vacgen2",
                      "premise face not covered by any taxonomy row "
                      "(TODO-SEAT counted, no silent degradation): "
                      "ineq.real.const-lt-field-re @ D:/fix/target.lean",
                      "report.json (assumptions[] status=todo_seat)",
                      "feed-batch-one", "2026-11-14T10:00:00Z"),
        entry_fixture("GAP-2", "periscope-collection",
                      "the window sentinel wrote its log outside the "
                      "declared output directory; the judgment face must "
                      "re-derive the artifact path, not trust the receipt",
                      "wf-script.ts:112 vs the on-disk log location",
                      "feed-batch-one", "2026-11-13",
                      source={"id": "GAP-2", zh_key: PITFALL_TOKEN}),
        entry_fixture("PLAIN-1", "exp_port",
                      "a plain precedent entry without any gap marker",
                      "ev://plain", "feed-batch-two", "2026-11-14"),
    ]
    swap = os.path.join(root, "round1.jsonl")
    write_file(swap, swap_file(envelope, entries))
    ledger = os.path.join(root, "led_a", LEDGER_NAME)

    # V1: feed lands one gap row per selected entry, keyed by shape.
    rc, out, _err = run_cli(["feed", "--swap", swap, "--ledger", ledger])
    if rc != 0 or "gapRows=2 nonGap=1 skipped=0 total=3" not in out:
        fails.append("V1 feed should land 2 of 3 rc=0 (rc=%d out=%r)"
                     % (rc, out))
    rows = read_feed_ledger(ledger) or []
    if len(rows) != 2:
        fails.append("V1 ledger should hold 2 gap rows, got %d" % len(rows))
    else:
        by_id = {row["id"]: row for row in rows}
        row1 = by_id.get("GAP-1")
        row2 = by_id.get("GAP-2")
        if row1 is None or row2 is None:
            fails.append("V1 gap rows missing: %r" % sorted(by_id))
        else:
            if row1.get("shapeKey") != "fam:ineq.real.const-lt-field-re":
                fails.append("V1 seat-token row should take the family "
                             "token key, got %r" % row1.get("shapeKey"))
            if row1.get("recognition") != RECOGNITION_SEAT:
                fails.append("V1 row1 recognition wrong: %r"
                             % row1.get("recognition"))
            if row2.get("recognition") != RECOGNITION_CATEGORY:
                fails.append("V1 row2 recognition wrong: %r"
                             % row2.get("recognition"))
            if not str(row2.get("shapeKey", "")).startswith("shape:"):
                fails.append("V1 row2 should fall to the abstract shape, "
                             "got %r" % row2.get("shapeKey"))
            if row1.get("correlationId") != "feed:srcA@%s" % anchor:
                fails.append("V1 route marker missing: %r"
                             % row1.get("correlationId"))
            if (row1.get("tool"), row1.get("ts")) != \
                    ("vacgen2", "2026-11-14T10:00:00Z"):
                fails.append("V1 carriers not carried verbatim: %r" % row1)
            if row2.get("source", {}).get(zh_key) != PITFALL_TOKEN:
                fails.append("V1 source dict not carried verbatim: %r"
                             % row2.get("source"))
            if "PLAIN-1" in by_id:
                fails.append("V1 non-gap entry must not land")

    # V2: the same package again is a zero-delta no-op on the id axis.
    before = read_bytes(ledger)
    rc, out, _err = run_cli(["feed", "--swap", swap, "--ledger", ledger])
    if rc != 0 or "gapRows=0 nonGap=1 skipped=2 total=3" not in out:
        fails.append("V2 re-feed should skip 2 rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if "axis=id" not in out:
        fails.append("V2 re-feed skips should name the id axis: %r" % out)
    if read_bytes(ledger) != before:
        fails.append("V2 idempotent re-feed changed the ledger bytes")

    # V3: the fingerprint axis fires on equal carriers under a new id, and
    # an id collision with different content skips without mutation.
    twin = entry_fixture("GAP-1-TWIN", "vacgen2", entries[0]["points"],
                         entries[0]["evidence"], entries[0]["batch"],
                         entries[0]["ts"])
    collision = entry_fixture("GAP-1", "other-tool",
                              "uncovered face (TODO-SEAT counted) under a "
                              "repeated id", "ev://x", "feed-batch-two",
                              "2026-11-15")
    swap3 = os.path.join(root, "round3.jsonl")
    write_file(swap3, swap_file(dict(envelope, entryCount=2),
                                [twin, collision]))
    rc, out, _err = run_cli(["feed", "--swap", swap3, "--ledger", ledger])
    if rc != 0 or "axis=fingerprint" not in out or "axis=id" not in out:
        fails.append("V3 should skip on both axes rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if read_bytes(ledger) != before:
        fails.append("V3 skip faces must not mutate the ledger")

    # V4: dry-run writes nothing on an absent target and holds live bytes.
    dry_ledger = os.path.join(root, "led_dry", LEDGER_NAME)
    rc, out, _err = run_cli(["feed", "--swap", swap, "--ledger", dry_ledger,
                             "--dry-run"])
    if rc != 0 or "would-feed=2" not in out:
        fails.append("V4 dry-run should answer rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if os.path.exists(dry_ledger):
        fails.append("V4 dry-run created the ledger")
    rc, out, _err = run_cli(["feed", "--swap", swap, "--ledger", ledger,
                             "--dry-run"])
    if rc != 0 or "would-skip=2" not in out:
        fails.append("V4 dry-run should count the skips (rc=%d out=%r)"
                     % (rc, out))
    if read_bytes(ledger) != before:
        fails.append("V4 dry-run on a live ledger changed bytes")

    # V5: damaged packages exit 9 with nothing written (each target absent
    # after the run); the damage set mirrors the bus import contract.
    good_entry = dict(entries[0])
    damaged = {
        "bad-json": canonical(envelope) + "\nnot-json{\n",
        "schema-drift": swap_file(dict(envelope, schema="rocqwash-symbio/9"),
                                  []),
        "count-drift": swap_file(dict(envelope, entryCount=2),
                                 [good_entry]),
        "no-id": swap_file(dict(envelope, entryCount=1),
                           [{k: v for k, v in good_entry.items()
                             if k != "id"}]),
        "bad-ts": swap_file(dict(envelope, entryCount=1),
                            [dict(good_entry, ts="not-a-date")]),
        "fp-drift": swap_file(dict(envelope, entryCount=1),
                              [dict(good_entry, points="tampered")]),
    }
    for name, payload in sorted(damaged.items()):
        target = os.path.join(root, "refuse_" + name, LEDGER_NAME)
        damaged_swap = os.path.join(root, "damaged_%s.jsonl" % name)
        write_file(damaged_swap, payload)
        rc, _out, _err = run_cli(["feed", "--swap", damaged_swap,
                                  "--ledger", target])
        if rc != 9:
            fails.append("V5 %s should exit 9 (rc=%d)" % (name, rc))
        if os.path.exists(target):
            fails.append("V5 %s wrote a ledger before refusing" % name)

    # V6: usage faces exit 2; an absent package exits 9 with no ledger.
    rc, _out, _err = run_cli([])
    if rc != 2:
        fails.append("V6 a bare run should exit 2 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["bogus"])
    if rc != 2:
        fails.append("V6 an unknown face should exit 2 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["feed", "--ledger", ledger])
    if rc != 2:
        fails.append("V6 feed without --swap should exit 2 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["feed", "--swap", swap, "--swap", swap,
                              "--ledger", ledger])
    if rc != 2:
        fails.append("V6 feed with two --swap flags should exit 2 (rc=%d)"
                     % rc)
    absent_swap = os.path.join(root, "absent.jsonl")
    no_dir = os.path.join(root, "nodir6", LEDGER_NAME)
    rc, _out, _err = run_cli(["feed", "--swap", absent_swap,
                              "--ledger", no_dir])
    if rc != 9:
        fails.append("V6 feed on an absent package should exit 9 (rc=%d)"
                     % rc)
    if os.path.exists(no_dir):
        fails.append("V6 absent-package feed must not create its ledger")

    # V7: status reports the counts, the shape mapping and a package face;
    # an absent ledger is exit 9.
    rc, out, _err = run_cli(["status", "--ledger", ledger])
    if rc != 0 or "rows=2" not in out or "inboundFeed=2" not in out \
            or "shape=fam:ineq.real.const-lt-field-re rows=1 ids=GAP-1" \
            not in out:
        fails.append("V7 status incomplete (rc=%d out=%r)" % (rc, out))
    if "no swap file given" not in out:
        fails.append("V7 status without --swap should say so (rc=%d out=%r)"
                     % (rc, out))
    rc, out, _err = run_cli(["status", "--ledger", ledger, "--swap", swap])
    if rc != 0 or "gapEntries=2" not in out or "presentInLedger=2" not in \
            out or "new=0" not in out:
        fails.append("V7 status with --swap incomplete (rc=%d out=%r)"
                     % (rc, out))
    rc, _out, _err = run_cli(["status", "--ledger",
                              os.path.join(root, "absent7", LEDGER_NAME)])
    if rc != 9:
        fails.append("V7 status on an absent ledger should exit 9 (rc=%d)"
                     % rc)

    # V8: determinism (two fresh ledgers replay byte-identically) plus the
    # gap_cluster aggregation face on the fed ledger; under the aligned
    # category rule both gap rows count (the TODO-SEAT row and the
    # zh-category row).
    replay = os.path.join(root, "led_b", LEDGER_NAME)
    rc, _out, _err = run_cli(["feed", "--swap", swap, "--ledger", replay])
    if rc != 0:
        fails.append("V8 replay feed failed (rc=%d)" % rc)
    if read_bytes(replay) != read_bytes(ledger):
        fails.append("V8 same package into two fresh ledgers must replay "
                     "byte-identically")
    aggregated = gap_cluster.aggregate([ledger], [])
    if aggregated["totals"]["ledgerGapEntries"] != 2:
        fails.append("V8 gap_cluster should count both gap rows under the "
                     "aligned rule, got %r" % aggregated["totals"])
    if aggregated["clusters"][0]["shapeKey"] != \
            "fam:ineq.real.const-lt-field-re":
        fails.append("V8 gap_cluster cluster key mismatch: %r"
                     % [c["shapeKey"] for c in aggregated["clusters"]])

    # V9: the recognition set covers both category key spellings at both
    # levels plus the status token; a plain entry stays unrecognized.
    probes = [
        ({"category": PITFALL_TOKEN}, RECOGNITION_CATEGORY),
        ({"source": {"category": PITFALL_TOKEN}}, RECOGNITION_CATEGORY),
        ({"source": {zh_key: PITFALL_TOKEN}}, RECOGNITION_CATEGORY),
        ({"points": "uncovered face (TODO-SEAT counted) for the fill round"},
         RECOGNITION_SEAT),
        ({"evidence": "report.json (status=todo_seat)"},
         RECOGNITION_STATUS),
        ({"points": "plain precedent", "evidence": "ev://x"}, None),
    ]
    for index, (fields, expected) in enumerate(probes):
        probe = dict(entry_fixture("PROBE-%d" % index, "t", "p", "e", "b",
                                   "2026-11-14"))
        probe.update(fields)
        got = recognize_gap(probe)
        if got != expected:
            fails.append("V9 probe %d recognition %r != %r"
                         % (index, got, expected))

    # V10: the write surface. Dry runs and read faces add zero files; a
    # real feed adds only its target ledger.
    before_set = snapshot(root)
    run_cli(["feed", "--swap", swap, "--ledger",
             os.path.join(root, "led_v10", LEDGER_NAME), "--dry-run"])
    run_cli(["status", "--ledger", ledger])
    run_cli(["status", "--ledger", ledger, "--swap", swap])
    after_dry = snapshot(root)
    if after_dry != before_set:
        fails.append("V10 dry/read faces added files: %r"
                     % sorted(after_dry - before_set))
    target10 = os.path.join(root, "led_v10", LEDGER_NAME)
    rc, out, _err = run_cli(["feed", "--swap", swap, "--ledger", target10])
    if rc != 0 or "gapRows=2" not in out:
        fails.append("V10 real feed failed (rc=%d out=%r)" % (rc, out))
    after_real = snapshot(root)
    if after_real - after_dry != {os.path.join("led_v10", LEDGER_NAME)}:
        fails.append("V10 real feed wrote outside its ledger: %r"
                     % sorted(after_real - after_dry))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bus_feeder.py",
        description="Feed a symbiosis swap package (rocqwash-symbio/1) into "
                    "the TODO-SEAT gap feed ledger: gap-class entries land "
                    "as family-shape-keyed gap rows, idempotent on id and "
                    "fingerprint; zero network by design.")
    parser.add_argument("--selftest", action="store_true",
                        help="run the temporary-fixture vector group")
    parser.add_argument("command", nargs="?", choices=("feed", "status"),
                        help="feed one swap package | report counts and the "
                             "shape-to-row mapping")
    parser.add_argument("--swap", action="append", dest="swaps",
                        help="feed: swap package to read (exactly one); "
                             "status: swap package to count (repeatable)")
    parser.add_argument("--ledger", default="",
                        help="gap feed ledger path override (default "
                             "docs/gap-feed-ledger.jsonl)")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="feed: validate and report, write nothing")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.command:
            parser.error("--selftest takes no subcommand")
        return selftest()
    try:
        if args.command == "feed":
            if len(args.swaps or []) != 1:
                parser.error("feed requires exactly one --swap")
            return cmd_feed(args)
        if args.command == "status":
            return cmd_status(args)
    except symbiosis_bus.BusInput as exc:
        sys.stderr.write("%s %s: %s\n" % (PROG, args.command, exc))
        return 9
    except symbiosis_bus.BusIO as exc:
        sys.stderr.write("%s %s: %s\n" % (PROG, args.command, exc))
        return 2
    parser.print_usage(sys.stderr)
    sys.stderr.write("%s: a subcommand is required: feed | status\n" % PROG)
    return 2


if __name__ == "__main__":
    sys.exit(main())
