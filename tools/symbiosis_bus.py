#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""symbiosis_bus: cross-repository experience bus for docs/exp-ledger.jsonl.

    Purpose.  Carry experience entries (rocqwash-exp/1) between checkouts
      as offline swap files (rocqwash-symbio/1): export stamps sourceRepo
      and the HEAD anchor; import lands one entry per exp_port.append call
      (the single write face; duplicate ids skip idempotently); status
      counts both directions from content; diff lists the id difference
      of two ledgers.  No network face by design.

    Interface.  `symbiosis_bus.py export --out SWAP.jsonl [--ledger P]
      [--source-repo NAME] [--anchor HEX] [--dry-run]` | `import --swap
      SWAP.jsonl [--ledger P] [--dry-run]` | `status [--ledger P]
      [--swap SWAP.jsonl ...]` | `diff --a P --b P` | `--selftest`.

    Dependencies.  Python 3 standard library (argparse/json/os/sys) plus
      the first-party sibling exp_port module, imported so the import
      walk runs the ledger's own write face; the anchor defaults to the
      .git HEAD commit (--anchor overrides); timestamps come from entry
      content, never from a clock.

    Evidence.  --selftest frozen vector group on temporary fixtures:
      byte-stable re-export, idempotent re-import, dry-run zero-write,
      corrupt-swap refusals, the exit-code sweep, write-surface file-set.

    Exit-codes.  0 = face answered (counts and differences are data);
      1 = selftest red, or an append failure after writes were made;
      2 = usage error or IO failure; 9 = missing or corrupt input, with
      nothing written.
"""
# Extended contract (kept outside the five-field block; annotation budget):
#
# Swap file (schema rocqwash-symbio/1), one JSON object per line:
#   line 1  envelope: schema "rocqwash-symbio/1", kind
#           "symbiosis-swap-envelope", sourceRepo (repository name),
#           anchor (source HEAD commit read from .git, or --anchor),
#           entryCount (must equal the number of entry lines that follow).
#   line 2+ entry: one ledger entry verbatim (rocqwash-exp/1: id / ts /
#           tool / points / evidence / batch / fingerprint, optional
#           correlationId and source).  Export refuses an entry whose
#           fingerprint does not match its four carrier fields; import
#           re-checks the same key before any write.
#
# Import walk:
#   every entry becomes exactly one exp_port.append call carrying the
#   entry's own id and ts, so id minting and clock reads never happen on
#   this face (an entry without id or ts is a refusal, exit 9, before any
#   write).  correlationId rides from the entry when present, else it is
#   synthesized from the envelope as "symbio:<sourceRepo>@<anchor>", so an
#   imported entry identifies its bus route from ledger content alone.
#   A repeated id (or a repeated fingerprint) is exp_port's own
#   duplicate-skip, exit 0, no write: this face never writes the ledger
#   itself.
#
# Stated boundary: the per-entry "source" provenance object of a first
#   hop does not survive a second hop, because exp_port.append carries
#   source provenance only from a --source-file path and this face writes
#   no scratch files (read-only pledge).  The envelope's sourceRepo and
#   anchor travel along as correlationId instead.
#
# Write surface: export writes only the --out path; import writes only
#   through exp_port.append into the resolved ledger; status and diff
#   write nothing.

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import exp_port
except ImportError as exc:
    sys.stderr.write("symbiosis_bus: the sibling exp_port module is required "
                     "(%s)\n" % exc)
    sys.exit(9)

SWAP_SCHEMA = "rocqwash-symbio/1"
SWAP_KIND = "symbiosis-swap-envelope"
CORRELATION_PREFIX = "symbio:"
SELFTEST_MARK = "SYMBIOSIS-BUS-SELFTEST PASS"
VECTOR_COUNT = 10


class BusInput(Exception):
    """Missing or malformed input; callers exit 9 with nothing written."""


class BusIO(Exception):
    """An input or output path failed at the OS level; callers exit 2."""


def canonical(obj):
    """The repo-wide canonical JSON line form (same bytes as exp_port)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def resolve_ledger(explicit):
    """Delegate to exp_port so both tools resolve the ledger identically."""
    return exp_port.resolve_ledger(explicit)


def read_ledger_or_fail(path):
    """Read through exp_port (one parse surface); absent or damaged exits 9."""
    try:
        entries = exp_port.read_ledger(path)
    except exp_port.CorruptLedger as exc:
        raise BusInput(str(exc))
    except OSError as exc:
        raise BusIO("ledger unreadable: %s" % exc)
    if entries is None:
        raise BusInput("ledger not found: %s" % os.path.abspath(path))
    return entries


def head_anchor():
    """Source HEAD commit from .git files; explicit refusal, never a guess."""
    git_dir = os.path.join(repo_root(), ".git")
    head_path = os.path.join(git_dir, "HEAD")
    try:
        with open(head_path, "r", encoding="utf-8") as handle:
            head = handle.read().strip()
    except OSError as exc:
        raise BusInput("anchor unavailable (.git/HEAD unreadable: %s); "
                       "pass --anchor" % exc)
    if head.startswith("ref: "):
        ref = head[5:].strip()
        ref_path = os.path.join(git_dir, *ref.split("/"))
        try:
            with open(ref_path, "r", encoding="utf-8") as handle:
                commit = handle.read().strip()
        except OSError:
            raise BusInput("anchor unavailable (ref %s is packed or absent; "
                           "pass --anchor)" % ref)
        if commit:
            return commit
        raise BusInput("anchor unavailable (ref %s resolves to an empty file; "
                       "pass --anchor)" % ref)
    if head:
        return head
    raise BusInput("anchor unavailable (.git/HEAD is empty); pass --anchor")


def repo_root():
    """Repository root: the parent of tools/ (this file lives in tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_entry_carriers(entry, where):
    """An entry must be a dict whose fingerprint matches its four carriers."""
    if not isinstance(entry, dict):
        raise BusInput("%s: not a JSON object" % where)
    for field in ("tool", "points", "evidence", "batch"):
        if not isinstance(entry.get(field), str):
            raise BusInput("%s: field %s missing or not a string"
                           % (where, field))
    if not entry["tool"] or not entry["points"]:
        raise BusInput("%s: tool and points must be non-empty" % where)
    mark = entry.get("fingerprint")
    if not isinstance(mark, str) or not mark:
        raise BusInput("%s: fingerprint missing (append through exp_port "
                       "first)" % where)
    expected = exp_port.fingerprint(entry["tool"], entry["points"],
                                    entry["evidence"], entry["batch"])
    if mark != expected:
        raise BusInput("%s: fingerprint does not match the four carrier "
                       "fields" % where)


def check_entry_for_import(entry, where):
    """Import-side keys: the carriers plus an explicit id and a valid ts."""
    check_entry_carriers(entry, where)
    eid = entry.get("id")
    if not isinstance(eid, str) or not eid:
        raise BusInput("%s: id missing (import never mints ids)" % where)
    stamp = entry.get("ts")
    if not isinstance(stamp, str) or not stamp or not exp_port.valid_ts(stamp):
        raise BusInput("%s: ts missing or not an ISO date/timestamp: %r"
                       % (where, stamp))


def check_envelope(envelope):
    """The first swap line must be a well-formed rocqwash-symbio/1 envelope."""
    if envelope.get("schema") != SWAP_SCHEMA:
        raise BusInput("envelope schema is %r, expected %r"
                       % (envelope.get("schema"), SWAP_SCHEMA))
    if envelope.get("kind") != SWAP_KIND:
        raise BusInput("envelope kind is %r, expected %r"
                       % (envelope.get("kind"), SWAP_KIND))
    for field in ("sourceRepo", "anchor"):
        value = envelope.get(field)
        if not isinstance(value, str) or not value:
            raise BusInput("envelope field %s missing or empty" % field)
    count = envelope.get("entryCount")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise BusInput("envelope entryCount must be a non-negative integer, "
                       "got %r" % (count,))


def read_swap(path, deep):
    """Read a swap file: deep=True validates every entry (import face),
    deep=False validates the envelope and entry ids only (status face)."""
    if not os.path.isfile(path):
        raise BusInput("swap file not found: %s" % os.path.abspath(path))
    envelope = None
    entries = []
    try:
        handle = open(path, "r", encoding="utf-8")
    except OSError as exc:
        raise BusIO("swap file unreadable: %s" % exc)
    with handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise BusInput("swap line %d is not valid JSON (%s): %s"
                               % (lineno, exc, os.path.abspath(path)))
            if envelope is None:
                if not isinstance(obj, dict):
                    raise BusInput("swap line 1 is not a JSON object: %s"
                                   % os.path.abspath(path))
                envelope = obj
                check_envelope(envelope)
                continue
            if not isinstance(obj, dict):
                raise BusInput("swap line %d is not a JSON object: %s"
                               % (lineno, os.path.abspath(path)))
            if deep:
                check_entry_for_import(obj, "swap %s entry line %d"
                                       % (os.path.abspath(path), lineno))
            elif not isinstance(obj.get("id"), str) or not obj["id"]:
                raise BusInput("swap %s entry line %d: id missing"
                               % (os.path.abspath(path), lineno))
            entries.append(obj)
    if envelope is None:
        raise BusInput("swap file holds no envelope line: %s"
                       % os.path.abspath(path))
    if envelope["entryCount"] != len(entries):
        raise BusInput("swap entryCount=%r but %d entry lines follow: %s"
                       % (envelope["entryCount"], len(entries),
                          os.path.abspath(path)))
    return envelope, entries


def require_ids(entries, where):
    """Every status/diff key needs a string id; entries without ids are
    damaged input, named by content."""
    for entry in entries:
        eid = entry.get("id")
        if not isinstance(eid, str) or not eid:
            raise BusInput("%s: entry without an id (tool=%r ts=%r)"
                           % (where, entry.get("tool"), entry.get("ts")))


def cmd_export(args):
    """Write the local ledger to a swap file.  Input: a resolved ledger.
    Output: one envelope line plus one canonical line per entry, in ledger
    order; stdout summary; side effect: the --out file only (a dry run
    writes nothing).  Exit: 0 written or dry-run; 2 usage or IO; 9 ledger
    or anchor unavailable, or an entry fails the fingerprint check."""
    path = resolve_ledger(args.ledger)
    entries = read_ledger_or_fail(path)
    for index, entry in enumerate(entries, 1):
        check_entry_carriers(entry, "ledger %s entry %d" % (path, index))
    anchor = args.anchor if args.anchor else head_anchor()
    source_repo = args.source_repo if args.source_repo \
        else os.path.basename(repo_root())
    envelope = {
        "schema": SWAP_SCHEMA,
        "kind": SWAP_KIND,
        "sourceRepo": source_repo,
        "anchor": anchor,
        "entryCount": len(entries),
    }
    payload = canonical(envelope) + "\n" + \
        "".join(canonical(entry) + "\n" for entry in entries)
    if args.dry_run:
        sys.stdout.write("export: dry-run would-write %d entries "
                         "schema=%s sourceRepo=%s anchor=%s out=%s\n"
                         % (len(entries), SWAP_SCHEMA, source_repo, anchor,
                            args.out))
        return 0
    try:
        parent = os.path.dirname(os.path.abspath(args.out))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except OSError as exc:
        raise BusIO("swap file not writable: %s" % exc)
    sys.stdout.write("export: wrote %d entries schema=%s sourceRepo=%s "
                     "anchor=%s out=%s\n"
                     % (len(entries), SWAP_SCHEMA, source_repo, anchor,
                        args.out))
    return 0


class Capture:
    """Minimal stdout sink for one append call (the exp_port selftest form)."""

    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def value(self):
        return "".join(self.parts)


def run_append(namespace):
    """Run one exp_port.append call with stdout captured; return (rc, out)."""
    saved = sys.stdout
    sink = Capture()
    sys.stdout = sink
    try:
        rc = exp_port.cmd_append(namespace)
    finally:
        sys.stdout = saved
    return rc, sink.value()


def cmd_import(args):
    """Land a swap file through exp_port.append, one call per entry.
    Input: a validated swap file and a ledger path.  Output: per-entry
    appends via the port, then one stdout summary; side effect: new lines
    in the ledger only (a dry run writes nothing).  Exit: 0 every entry
    appended or skipped; 1 an append call failed after writes were made;
    2 usage or IO; 9 swap or ledger unusable, nothing written."""
    path = resolve_ledger(args.ledger)
    try:
        pre_read = exp_port.read_ledger(path)
    except exp_port.CorruptLedger as exc:
        sys.stderr.write("symbiosis_bus import: %s\n" % exc)
        return 9
    except OSError as exc:
        sys.stderr.write("symbiosis_bus import: ledger unreadable: %s\n" % exc)
        return 2
    del pre_read  # the walk re-reads the ledger through exp_port per call
    swap_path = args.swaps[0]
    envelope, swap_entries = read_swap(swap_path, deep=True)
    appended = 0
    skipped = 0
    processed = 0
    for index, entry in enumerate(swap_entries, 1):
        correlation = entry.get("correlationId")
        if not isinstance(correlation, str) or not correlation:
            correlation = "%s%s@%s" % (CORRELATION_PREFIX,
                                       envelope["sourceRepo"],
                                       envelope["anchor"])
        namespace = argparse.Namespace(
            ledger=path,
            tool=entry["tool"],
            points=entry["points"],
            evidence=entry["evidence"],
            batch=entry["batch"],
            id=entry["id"],
            ts=entry["ts"],
            source_file="",
            correlation_id=correlation,
            dry_run=bool(args.dry_run),
        )
        rc, out = run_append(namespace)
        if rc == 0 and out.startswith("appended id="):
            appended += 1
        elif rc == 0 and out.startswith("dry-run id="):
            appended += 1  # a dry run counts this entry as would-append
        elif rc == 0 and out.startswith("duplicate-skip id="):
            skipped += 1
        elif rc != 0:
            sys.stderr.write(
                "symbiosis_bus import: append failed for entry %s (swap line "
                "%d of %s, rc=%d, out=%r)\n"
                % (entry["id"], index, os.path.abspath(swap_path), rc,
                   out.strip()))
            if processed == 0:
                return rc  # nothing written; pass the port's verdict through
            return 1  # writes already made; fail loud, the prefix stays valid
        else:
            sys.stderr.write(
                "symbiosis_bus import: unrecognized append output %r for "
                "entry %s\n" % (out.strip(), entry["id"]))
            return 1 if processed else 9
        processed += 1
    if args.dry_run:
        sys.stdout.write("import: dry-run would-append=%d would-skip=%d "
                         "total=%d ledger=%s\n"
                         % (appended, skipped, len(swap_entries), path))
    else:
        sys.stdout.write("import: appended=%d skipped=%d total=%d ledger=%s\n"
                         % (appended, skipped, len(swap_entries), path))
    return 0


def cmd_status(args):
    """Report both bus directions from entry content.  Input: a resolved
    ledger plus optional swap files.  Output: counts to stdout; side
    effect: none.  Exit: 0 report printed; 2 usage or IO; 9 ledger or a
    swap file absent or damaged."""
    path = resolve_ledger(args.ledger)
    entries = read_ledger_or_fail(path)
    require_ids(entries, "ledger %s" % path)
    inbound = [entry for entry in entries
               if isinstance(entry.get("correlationId"), str)
               and entry["correlationId"].startswith(CORRELATION_PREFIX)]
    sys.stdout.write("status: ledger=%s entries=%d inboundBus=%d\n"
                     % (path, len(entries), len(inbound)))
    if inbound:
        routes = []
        last_stamp = ""
        for entry in inbound:
            tail = entry["correlationId"][len(CORRELATION_PREFIX):]
            repo = tail.rsplit("@", 1)[0] if "@" in tail else tail
            if repo not in routes:
                routes.append(repo)
            stamp = entry.get("ts")
            if isinstance(stamp, str) and stamp > last_stamp:
                last_stamp = stamp  # ISO strings order lexicographically
        sys.stdout.write("status: inboundRoutes=%s lastInboundTs=%s\n"
                         % (",".join(sorted(routes)), last_stamp))
    else:
        sys.stdout.write("status: inboundRoutes= lastInboundTs=none\n")
    swaps = args.swaps or []
    if not swaps:
        sys.stdout.write("status: outbound (no swap file given; pass --swap "
                         "to count it)\n")
    for swap_path in swaps:
        envelope, swap_entries = read_swap(swap_path, deep=False)
        ledger_ids = set(entry["id"] for entry in entries)
        present = sum(1 for entry in swap_entries
                      if entry["id"] in ledger_ids)
        stamps = [entry["ts"] for entry in swap_entries
                  if isinstance(entry.get("ts"), str)]
        sys.stdout.write("status: swap=%s sourceRepo=%s entries=%d "
                         "presentInLedger=%d new=%d lastEntryTs=%s\n"
                         % (swap_path, envelope["sourceRepo"],
                            len(swap_entries), present,
                            len(swap_entries) - present,
                            max(stamps) if stamps else "none"))
    return 0


def cmd_diff(args):
    """List the id-level entry difference of two ledgers.  Input: two
    ledger paths.  Output: one only-a/only-b line per differing entry in
    ledger order, summary on stderr; side effect: none.  Exit: 0 listed
    (a difference is data); 2 usage or IO; 9 a ledger absent or damaged."""
    entries_a = read_ledger_or_fail(args.side_a)
    entries_b = read_ledger_or_fail(args.side_b)
    require_ids(entries_a, "ledger %s" % args.side_a)
    require_ids(entries_b, "ledger %s" % args.side_b)
    by_id_a = {}
    by_id_b = {}
    for entry in entries_a:
        by_id_a.setdefault(entry["id"], entry)
    for entry in entries_b:
        by_id_b.setdefault(entry["id"], entry)
    only_a = [entry for eid, entry in by_id_a.items() if eid not in by_id_b]
    only_b = [entry for eid, entry in by_id_b.items() if eid not in by_id_a]
    for entry in only_a:
        sys.stdout.write("only-a id=%s tool=%s ts=%s\n"
                         % (entry["id"], entry["tool"], entry["ts"]))
    for entry in only_b:
        sys.stdout.write("only-b id=%s tool=%s ts=%s\n"
                         % (entry["id"], entry["tool"], entry["ts"]))
    common = len(by_id_a) - len(only_a)
    sys.stderr.write("diff: only-a=%d only-b=%d common=%d (a=%s b=%s)\n"
                     % (len(only_a), len(only_b), common,
                        args.side_a, args.side_b))
    return 0


def append_fixture(ledger, tool, points, evidence, batch, eid, ts):
    """Write one fixture entry through exp_port.append (the real contract)."""
    namespace = argparse.Namespace(
        ledger=ledger, tool=tool, points=points, evidence=evidence,
        batch=batch, id=eid, ts=ts, source_file="", correlation_id="",
        dry_run=False)
    return run_append(namespace)


def swap_lines(envelope_extra, entries):
    """Assemble swap file bytes from an envelope dict plus entry dicts."""
    envelope = dict(envelope_extra)
    text = canonical(envelope) + "\n"
    text += "".join(canonical(entry) + "\n" for entry in entries)
    return text


def write_file(path, text):
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
        sys.stderr.write("symbiosis_bus selftest: no scratch directory found "
                         "(set TMP/TEMP/TMPDIR)\n")
        return 9
    root = os.path.join(base, "symbiosis_bus_selftest_%d" % os.getpid())
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
    ledger_a = os.path.join(root, "led_a", "exp-ledger.jsonl")
    ledger_b = os.path.join(root, "led_b", "exp-ledger.jsonl")
    fixture_rows = [
        ("toolA", "point one", "ev://a1", "batch-one",
         "2026-11-14T10:00:00Z"),
        ("toolB", "point two", "ev://b2", "batch-one",
         "2026-11-14T11:00:00Z"),
        ("toolC", "point three", "", "batch-two", "2026-11-15T09:30:00Z"),
    ]
    anchor = "1f" * 20

    # V1: export writes an envelope plus the entries, byte-stable on re-export.
    for index, row in enumerate(fixture_rows, 1):
        rc, out = append_fixture(ledger_a, row[0], row[1], row[2], row[3],
                                 "EXP-20261114-%04d" % index, row[4])
        if rc != 0 or not out.startswith("appended id="):
            fails.append("V1 fixture append failed (rc=%d out=%r)"
                         % (rc, out))
    swap1 = os.path.join(root, "swap-round-1.jsonl")
    rc, out, _err = run_cli(["export", "--ledger", ledger_a, "--out", swap1,
                             "--source-repo", "srcA", "--anchor", anchor])
    if rc != 0 or "wrote 3 entries" not in out:
        fails.append("V1 export should write 3 entries rc=0 (rc=%d out=%r)"
                     % (rc, out))
    lines = read_bytes(swap1).decode("utf-8").strip().split("\n")
    envelope = json.loads(lines[0])
    if envelope != {"anchor": anchor, "entryCount": 3, "kind": SWAP_KIND,
                    "schema": SWAP_SCHEMA, "sourceRepo": "srcA"}:
        fails.append("V1 envelope mismatch: %r" % envelope)
    entry_lines = [json.loads(line) for line in lines[1:]]
    if [entry["id"] for entry in entry_lines] != \
            ["EXP-20261114-0001", "EXP-20261114-0002", "EXP-20261114-0003"]:
        fails.append("V1 entry ids out of ledger order: %r" % entry_lines)
    swap1b = os.path.join(root, "swap-round-1b.jsonl")
    run_cli(["export", "--ledger", ledger_a, "--out", swap1b,
             "--source-repo", "srcA", "--anchor", anchor])
    if read_bytes(swap1) != read_bytes(swap1b):
        fails.append("V1 re-export must be byte-stable for the same input")

    # V1b: default sourceRepo is this checkout's name; the default anchor
    # is the .git HEAD commit (asserted only where .git exists).
    try:
        expected_anchor = head_anchor()
    except BusInput:
        sys.stdout.write("V1b note: no .git anchor in this checkout; the "
                         "default-anchor vector is skipped\n")
    else:
        swap1c = os.path.join(root, "swap-round-1c.jsonl")
        rc, out, _err = run_cli(["export", "--ledger", ledger_a,
                                 "--out", swap1c])
        if rc != 0:
            fails.append("V1b default-anchor export failed (rc=%d out=%r)"
                         % (rc, out))
        else:
            env_default = json.loads(
                read_bytes(swap1c).decode("utf-8").split("\n")[0])
            if env_default.get("sourceRepo") != os.path.basename(repo_root()):
                fails.append("V1b default sourceRepo mismatch: %r"
                             % env_default)
            if env_default.get("anchor") != expected_anchor:
                fails.append("V1b anchor mismatch: %r vs %r"
                             % (env_default.get("anchor"), expected_anchor))

    # V2: export dry-run writes nothing (anchor pinned; no .git dependency).
    out_dry = os.path.join(root, "swap-dry.jsonl")
    rc, out, _err = run_cli(["export", "--ledger", ledger_a, "--out", out_dry,
                             "--source-repo", "srcA", "--anchor", anchor,
                             "--dry-run"])
    if rc != 0 or "dry-run" not in out:
        fails.append("V2 export dry-run should answer rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if os.path.exists(out_dry):
        fails.append("V2 export dry-run created the swap file")

    # V3: export refusals (absent ledger 9, damaged ledger 9, no --out 2).
    rc, _out, _err = run_cli(["export", "--out", os.path.join(root, "x.jsonl"),
                              "--ledger", os.path.join(root, "absent.jsonl")])
    if rc != 9:
        fails.append("V3 export on an absent ledger should exit 9 (rc=%d)" % rc)
    bad_ledger = os.path.join(root, "bad", "exp-ledger.jsonl")
    os.makedirs(os.path.dirname(bad_ledger), exist_ok=True)
    write_file(bad_ledger, '{"id": "ok"}\nnot-json{\n')
    rc, _out, _err = run_cli(["export", "--out", os.path.join(root, "x.jsonl"),
                              "--ledger", bad_ledger])
    if rc != 9:
        fails.append("V3 export on a damaged ledger should exit 9 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["export", "--ledger", ledger_a])
    if rc != 2:
        fails.append("V3 export without --out should exit 2 (rc=%d)" % rc)

    # V4: a full import round-trip preserves id/ts/carriers and marks the route.
    rc, out, _err = run_cli(["import", "--swap", swap1, "--ledger", ledger_b])
    if rc != 0 or "appended=3 skipped=0 total=3" not in out:
        fails.append("V4 import should append 3 rc=0 (rc=%d out=%r)"
                     % (rc, out))
    else:
        landed = [json.loads(line)
                  for line in read_bytes(ledger_b).decode("utf-8").split("\n")
                  if line.strip()]
        for source, copy in zip(entry_lines, landed):
            if (source["id"], source["ts"], source["tool"], source["points"],
                    source["evidence"], source["batch"]) != \
                    (copy["id"], copy["ts"], copy["tool"], copy["points"],
                     copy["evidence"], copy["batch"]):
                fails.append("V4 entry not carried verbatim: %r vs %r"
                             % (source, copy))
            if copy.get("correlationId") != "symbio:srcA@%s" % anchor:
                fails.append("V4 route marker missing: %r" % copy)

    # V5: the same swap again skips all three and leaves the bytes alone.
    bytes_b = read_bytes(ledger_b)
    rc, out, _err = run_cli(["import", "--swap", swap1, "--ledger", ledger_b])
    if rc != 0 or "appended=0 skipped=3 total=3" not in out:
        fails.append("V5 re-import should skip 3 rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if read_bytes(ledger_b) != bytes_b:
        fails.append("V5 idempotent re-import changed the ledger bytes")

    # V6: import dry-run writes nothing on an absent target.
    ledger_c = os.path.join(root, "led_c", "exp-ledger.jsonl")
    rc, out, _err = run_cli(["import", "--swap", swap1, "--ledger", ledger_c,
                             "--dry-run"])
    if rc != 0 or "would-append=3" not in out:
        fails.append("V6 import dry-run should answer rc=0 (rc=%d out=%r)"
                     % (rc, out))
    if os.path.exists(ledger_c):
        fails.append("V6 import dry-run created the ledger")

    # V7: swap refusals exit 9 with nothing written (each target absent after).
    good_entry = dict(entry_lines[0])
    damaged = {
        "bad-json": canonical({"schema": SWAP_SCHEMA, "kind": SWAP_KIND,
                               "sourceRepo": "s", "anchor": "a",
                               "entryCount": 1}) + "\nnot-json{\n",
        "schema-drift": canonical({"schema": "rocqwash-symbio/9",
                                   "kind": SWAP_KIND, "sourceRepo": "s",
                                   "anchor": "a", "entryCount": 0}) + "\n",
        "count-drift": swap_lines({"schema": SWAP_SCHEMA, "kind": SWAP_KIND,
                                   "sourceRepo": "s", "anchor": "a",
                                   "entryCount": 2}, [good_entry]),
        "no-id": swap_lines({"schema": SWAP_SCHEMA, "kind": SWAP_KIND,
                             "sourceRepo": "s", "anchor": "a",
                             "entryCount": 1},
                            [{k: v for k, v in good_entry.items()
                              if k != "id"}]),
        "bad-ts": swap_lines({"schema": SWAP_SCHEMA, "kind": SWAP_KIND,
                              "sourceRepo": "s", "anchor": "a",
                              "entryCount": 1},
                             [dict(good_entry, ts="not-a-date")]),
        "fp-drift": swap_lines({"schema": SWAP_SCHEMA, "kind": SWAP_KIND,
                                "sourceRepo": "s", "anchor": "a",
                                "entryCount": 1},
                               [dict(good_entry, points="tampered")]),
    }
    for name, payload in sorted(damaged.items()):
        target = os.path.join(root, "refuse_" + name, "exp-ledger.jsonl")
        damaged_swap = os.path.join(root, "damaged_%s.jsonl" % name)
        write_file(damaged_swap, payload)
        rc, _out, _err = run_cli(["import", "--swap", damaged_swap,
                                  "--ledger", target])
        if rc != 9:
            fails.append("V7 %s should exit 9 (rc=%d)" % (name, rc))
        if os.path.exists(target):
            fails.append("V7 %s wrote a ledger before refusing" % name)
    rc, _out, _err = run_cli(["import", "--ledger", ledger_b])
    if rc != 2:
        fails.append("V7 import without --swap should exit 2 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["import", "--swap", swap1, "--swap", swap1,
                              "--ledger", ledger_b])
    if rc != 2:
        fails.append("V7 import with two --swap flags should exit 2 (rc=%d)"
                     % rc)

    # V8: status counts both directions from content.
    rc, out, _err = run_cli(["status", "--ledger", ledger_b, "--swap", swap1])
    if rc != 0 or "inboundBus=3" not in out or "presentInLedger=3" not in out \
            or "new=0" not in out \
            or "lastInboundTs=2026-11-15T09:30:00Z" not in out:
        fails.append("V8 status with --swap incomplete (rc=%d out=%r)"
                     % (rc, out))
    rc, out, _err = run_cli(["status", "--ledger", ledger_b])
    if rc != 0 or "no swap file given" not in out:
        fails.append("V8 status without --swap should say so (rc=%d out=%r)"
                     % (rc, out))
    rc, _out, _err = run_cli(["status", "--ledger",
                              os.path.join(root, "absent.jsonl")])
    if rc != 9:
        fails.append("V8 status on an absent ledger should exit 9 (rc=%d)" % rc)

    # V9: diff lists the id-level difference; a difference is data, exit 0.
    rc, out, err_out = run_cli(["diff", "--a", ledger_a, "--b", ledger_b])
    if rc != 0 or "only-a=0 only-b=0 common=3" not in err_out:
        fails.append("V9 diff of an imported ledger should be empty rc=0 "
                     "(rc=%d err=%r)" % (rc, err_out))
    append_fixture(ledger_a, "toolD", "point four", "", "batch-two",
                   "EXP-20261114-0004", "2026-11-15T12:00:00Z")
    rc, out, err_out = run_cli(["diff", "--a", ledger_a, "--b", ledger_b])
    if rc != 0 or "only-a id=EXP-20261114-0004" not in out \
            or "only-a=1 only-b=0 common=3" not in err_out:
        fails.append("V9 diff should name the new entry rc=0 (rc=%d out=%r "
                     "err=%r)" % (rc, out, err_out))
    rc, _out, _err = run_cli(["diff", "--a", ledger_a, "--b",
                              os.path.join(root, "absent.jsonl")])
    if rc != 9:
        fails.append("V9 diff on an absent ledger should exit 9 (rc=%d)" % rc)
    rc, _out, _err = run_cli(["diff", "--a", ledger_a])
    if rc != 2:
        fails.append("V9 diff without --b should exit 2 (rc=%d)" % rc)

    # V10: the write surface. Dry runs and read faces add zero files, and
    # a real import adds only its target ledger.
    before = snapshot(root)
    run_cli(["export", "--ledger", ledger_a, "--out",
             os.path.join(root, "swap-v10.jsonl"), "--dry-run"])
    run_cli(["import", "--swap", swap1, "--ledger",
             os.path.join(root, "led_v10", "exp-ledger.jsonl"), "--dry-run"])
    run_cli(["status", "--ledger", ledger_a, "--swap", swap1])
    run_cli(["diff", "--a", ledger_a, "--b", ledger_b])
    after_dry = snapshot(root)
    if after_dry != before:
        fails.append("V10 dry/read faces added files: %r"
                     % sorted(after_dry - before))
    rc, out, _err = run_cli(["import", "--swap", swap1, "--ledger",
                             os.path.join(root, "led_v10",
                                          "exp-ledger.jsonl")])
    if rc != 0 or "appended=3" not in out:
        fails.append("V10 real import failed (rc=%d out=%r)" % (rc, out))
    after_real = snapshot(root)
    if after_real - after_dry != {os.path.join("led_v10",
                                               "exp-ledger.jsonl")}:
        fails.append("V10 real import wrote outside its ledger: %r"
                     % sorted(after_real - after_dry))


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


def build_parser():
    parser = argparse.ArgumentParser(
        prog="symbiosis_bus.py",
        description="Cross-repository experience bus over "
                    "docs/exp-ledger.jsonl (swap schema rocqwash-symbio/1; "
                    "import walks exp_port.append).")
    parser.add_argument("--selftest", action="store_true",
                        help="run the temporary-fixture vector group")
    parser.add_argument("command", nargs="?",
                        choices=("export", "import", "status", "diff"),
                        help="export a swap file | import one through "
                             "exp_port.append | bus counts from content | "
                             "entry-id difference of two ledgers")
    parser.add_argument("--out", default="",
                        help="export: swap file to write (required for a "
                             "real export)")
    parser.add_argument("--swap", action="append", dest="swaps",
                        help="import: swap file to read (exactly one); "
                             "status: swap file to count (repeatable)")
    parser.add_argument("--ledger", default="", help="ledger path override")
    parser.add_argument("--source-repo", default="", dest="source_repo",
                        help="export: source repository name (default: this "
                             "checkout's directory name)")
    parser.add_argument("--anchor", default="",
                        help="export: source HEAD anchor (default: the "
                             "commit read from .git)")
    parser.add_argument("--a", default="", dest="side_a",
                        help="diff: first ledger path")
    parser.add_argument("--b", default="", dest="side_b",
                        help="diff: second ledger path")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="export/import: validate and report, write "
                             "nothing")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.command:
            parser.error("--selftest takes no subcommand")
        return selftest()
    try:
        if args.command == "export":
            if not args.out and not args.dry_run:
                parser.error("export requires --out (or --dry-run)")
            return cmd_export(args)
        if args.command == "import":
            if len(args.swaps or []) != 1:
                parser.error("import requires exactly one --swap")
            return cmd_import(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "diff":
            if not args.side_a or not args.side_b:
                parser.error("diff requires --a and --b")
            return cmd_diff(args)
    except BusInput as exc:
        sys.stderr.write("symbiosis_bus %s: %s\n" % (args.command, exc))
        return 9
    except BusIO as exc:
        sys.stderr.write("symbiosis_bus %s: %s\n" % (args.command, exc))
        return 2
    parser.print_usage(sys.stderr)
    sys.stderr.write("symbiosis_bus: a subcommand is required: export | "
                     "import | status | diff\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
