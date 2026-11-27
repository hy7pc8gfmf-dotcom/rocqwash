#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unclog.py: blockage-clearing closed-loop engine for rocqwash (tools/).

Purpose.  Closes the manual five-step unblocking procedure into a
  self-driving loop over the existing engines; dry run by default: writes
  happen only under --apply.

Interface.  python3 tools/unclog.py --src DIR [--world DIR]
  (--candidates TSV | --chain-ledgers JSON...) [--rounds N] [--apply]
  [--audit] [--top N] [--pack FILE] [--probe-parallel K] [--json out]
  [--events F] [--loop --interval S --loop-max N --state-file F]
  [--injector DIR] | --selftest.  Report schema rocqwash-unclog/1; loop
  events are JSONL; --state-file shares the rocqwash-sentinel-state/1 shape
  with cw_sentinel (mutually readable/writable).

Dependencies.  Python 3 standard library only; probe_engine/chain_graph/
  cure_applier/scan_v4_token/frozen8 always run as subprocesses (this tool
  supplies only the glue and the state machine, following the pushci.py
  orchestration precedent); every path parameterized, zero network.

Evidence.  --selftest: fourteen frozen vectors on tmp fixture trees with
  injector-canned probe ledgers (zero real compiles; chain/cure/scan/
  frozen8 run for real): the green path, the honest wall plus the
  no-chain-root supplementary wall entry, cure-miss, rounds-exhausted,
  the default-off proof, JSON idempotence, the frozen-roster rejection,
  the loop watch mode, CLI four codes, the audit read-only baseline with
  the zero-write self-proof, the state-file differential only-new triple
  run, the mutual-exclusion gates, and the --jobs dimension; suite
  membership tests/test_unclog.py.

Exit-codes.  0 = unclogged (or audit); 1 = wall or rounds-exhausted (a
  failing result is data, not a tool failure; reported loudly); 2 = usage
  or scenario-shape error; 9 = missing path or tool failure.

Extended contract (kept below the five-field block per the annotation
standard 30-line header budget).

Closes the manual five-step unblocking procedure used by the real-time support
workflow into a self-driving loop (orchestrates existing engines rather than
reimplementing them: probe_engine/chain_graph/cure_applier/scan_v4_token/
frozen8 are always invoked as subprocesses; this tool supplies only the glue
and the state machine, following the pushci.py orchestration precedent):

  manual five steps (real-time support workflow)         this tool's loop (--rounds cap, default 5)
  ① probe collects the failure set        →  ① collect: any of three candidate sources →
                                            probe_engine produces the current failure set
  ② chain_graph picks chain roots from the graph
                                          →  ② chain root: chain_graph merges the top list →
                                            take the first entry with self.washable=true
                                            (all false = no actionable root → honest wall;
                                            nothing is forced)
  ③ cure_applier applies the cure         →  ③ apply: dry-run the root file to produce a plan →
                                            apply only when a plan exists and --apply is given
                                            (the canonical cure pack only; no free-form edits);
                                            no plan → the root is recorded as cure-miss in the
                                            wall table
  ④ re-scan / re-probe verification       →  ④ verify: scan_v4_token re-scans the treated file
                                            (cured-token residual should be zero) + probe_engine
                                            re-probes it (rc should be 0)
  ⑤ human judgment                        →  ⑤ verdict: empty failure set = verdict unclogged,
                                            exit 0; non-empty and rounds remain → next round;
                                            rounds exhausted → verdict rounds-exhausted, exit 1
                                            (with each round's record + a final probe)

Three candidate sources (mutually exclusive):
  --candidates TSV      feed the candidate list directly to probe_engine
                        (located by header column names, same convention as
                        probe_engine)
  --chain-ledgers JSON  merge existing probe ledgers (argv order = merge
                        order, later batches override earlier ones, same as
                        chain_graph); re-probe ledgers from later rounds are
                        merged round by round (resprobe: later overrides
                        earlier; the post-repair state is recorded). This
                        mode has no per-round full re-probe (runs with zero
                        world dependency).
  (neither given)       --src full-tree enumeration: walk --src collecting
                        *.v files with per-file md5 → generate the TSV (the
                        RED column is not declared; probe_engine honestly
                        reports RC0 for rc0: the chain-root washability
                        criterion is self.rc, not verdict; same convention as
                        chain_graph.py)

Failure-set criteria: a probe record with rc != 0 (rc1 failure / rc124
TIMEOUT / NO-SRC) counts as failed; the union of chain_graph stats.rc1 +
stats.other is the failure set (chain_graph.py:116-121). The verdict is
judged only on the failure set (a failing result is data, not a tool
failure; a probe_engine rc1 candidate is produced data, not a tool failure).

Honest wall (nothing is forced): when every TOP entry has
self.washable=false (a mid-chain ring: self-unwashable; or the root is not
in the candidate set: unprobed), or every washable root hits a dead end
(cure-miss: the canonical pack offers no plan / root-file-missing /
frozen-in-service: the root is on the frozen roster and is refused /
exclusive-group-conflict: variants require human selection /
idempotence-fail: the apply-time idempotence assertion refuses to write) →
verdict=wall exit 1; the wall table lists the non-actionable reason per
root; zero applies, nothing forced.

Safety rules:
  --apply defaults to off = everything is a dry run with zero disk writes
    (single switch; --yes is not needed); applies go only through the
    cure_applier canonical pack (--pack default wash/cure_pack.json);
    the apply target is always the chain-root file (<src>/<root>.v; outside
    pick there is no cure call path, so restricting applies to chain roots is
    a structural guarantee); files on the frozen roster (certify/frozen8.py
    --ledger, eight files, fetched via subprocess; a missing roster fails
    closed with 9) are pre-checked and refused: if the root name collides
    with a rostered rel / basename / extension-stripped name, or the root
    file's realpath collides with a rostered file (resolved on both the
    --src and --repo-path sides), it is refused; recorded in the wall table
    as reason=frozen-in-service, zero applies.

--audit read-only audit (real-tree blockage baseline):
  A single-pass probe dry-run collection → chain_graph → a "blockage baseline
  report" (schema rocqwash-unclog/1: final.verdict=audit; one round with
  probe_summary/chain_top present; cure/rescan/resprobe always None;
  cures_planned/cures_applied always 0; the wall table records every graph
  case: unprobed/self-unwashable/frozen-in-service per root (data recorded,
  not a stop condition; audit neither picks roots nor applies); a failure
  set with no chain root adds a no-chain-root wall entry instead of staying
  silent; exit 0; a failing result is baseline data, not a tool failure).
  Mutual exclusions: --audit with --apply → rc=2 (audit is read-only); with
  --loop → rc=2 (single-pass baseline; watch-mode cycling is not audit
  semantics); with --state-file → rc=2 (seen-state differencing is not audit
  semantics); --rounds does not apply to a single pass.
  Zero-write hard guarantee = the --src full-file md5 manifest is self-checked
  identical before and after the run (probe_engine itself copies the tree out
  for compilation (wash/probe_engine.py) and cleans up artifacts; any
  manifest mismatch fails loudly with 9; a contaminated baseline is never
  reported); workdir/--json/events writes are the audit's own duty and are
  outside the guarded domain.
  Per-phase timings (enumerate/manifest/probe+chain/total) enter
  report["timing"] = measured wall clock, the only non-deterministic part of
  the report (byte-identical reruns still hold for everything except the
  timing section); the timing section also records the jobs dimension = the
  --probe-parallel K value passed through to probe_engine --jobs (default 1):
  runs over the same candidate set with different K are comparable
  (parallel-profile collection; see examples/baselines/perf-README.md; in
  injector canned mode the parameter is bypassed but still recorded).
  Offline-testable like the closed loop: --injector canned probe doubles as
  the audit probe (selftest vector ⑩); a real-tree audit live run belongs to
  the main session (this tool proves the fixture level only).

--probe-parallel K (pass-through to probe_engine --jobs; default 1 = per-file
serial, zero drift):
  ① collect probe / ④ re-probe resprobe / --audit all share the parameter;
  candidate files are sharded across a ThreadPool (ledger record order always
  follows candidate order; completion order never changes output order, the
  determinism rule; md5_match/verdict logic unchanged; per-file build logs
  still land independently in logdir; real compilation still goes through
  --guard cpu_guard per file; the guard FRONT profile applies its own
  clamping). K>1 = multiple concurrent rocqworker processes on one machine =
  higher thermal load; with --guard given, K≤2 is advised (advisory note,
  not enforced; the user decides; thermal-control details in the parallelism
  section of the wash/probe_engine.py docstring). Injector canned mode does
  zero real compilation; the parameter is bypassed (canned data lands
  directly in workdir).

--once/--loop dual mode (shared three-tool interface rule):
  --once (default) runs a single closed loop; --loop is watch mode: the loop
  repeats (--interval seconds between cycles; --sleep-scale multiplier;
  --selftest uses 0 = zero real sleep); round events + cycle events are
  written as a JSONL stream to --events (default <workdir>/events.jsonl); a
  terminal verdict (unclogged/wall) stops and exits immediately;
  rounds-exhausted is not terminal → wait --interval and start the next
  cycle (--loop-max cap, 0 = unlimited). Mutual exclusion, spelled out:
  --rounds with --loop → rc=2 (--rounds caps the rounds of a single closed
  loop; watch-mode cycling is not its semantics; the per-cycle round cap is
  always the default 5, same rule as --audit with --loop; no silent choice
  between them).
--state-file watch-mode seen state (rocqwash-sentinel-state/1, same shape as
  cw_sentinel --state-file: same schema, same keys repos/ledgers/buildlogs;
  mutually read/write compatible):
  inter-round failure-set differencing, only-new events: each round's
  failure set is diffed against state.red_seen; newly appearing failed files
  emit {"event":"red-new", new_red:[...]} (already-seen failures are not
  reported again; seen grows monotonically); events are emitted before the
  state is saved (prefer duplicates over losing events); default None =
  differencing off (zero behavior change); a corrupted state (parse failure /
  malformed keys) → fail-loud 9, hard refusal, no silent rebuild (recovery =
  delete the file manually; the tool never swallows it).

Offline-testable (hard requirement; the subprocess-call layer is injectable;
zero real network and zero real compilation in --selftest):
  --injector DIR  DIR/scenario.json = {"probe":[probe_ledger...],
                  "resprobe":[probe_ledger...]}: the two probe_engine call
                  classes (probe/resprobe) are consumed strictly in order
                  from the canned ledgers (written verbatim into workdir and
                  then fed to the **real** chain_graph; exhaustion / missing
                  entry / malformed shape fails loudly with 2; zero real
                  compilation); chain_graph/cure_applier/scan_v4_token/
                  frozen8 are pure stdlib with zero compilation and zero
                  network and run for real under injection (real
                  orchestration, not a stub).
  --sleep-scale F multiplies every sleep by F (--selftest uses 0 = zero real
                  sleep).

Output (deterministic; sort_keys; --json reruns are byte-identical on the
same input; the report carries zero wall clock and zero absolute paths;
paths are reported as basenames only, full paths go to explicit stdout; in
audit mode the timing section is the exception = measured wall clock differs
per run, all other sections stay identical):
  --json report, schema=rocqwash-unclog/1:
    {schema, mode{source,apply,injector,loop[,audit]}, args, cycles?,
     rounds[{round, probe_summary{source,n_records,n_red,red_files,ledgers},
             chain_top[{lib,n,dependents,self{probed,rc,verdict,washable}}],
             root, root_file, cure{stage,rc,total_matches,patterns,md5_before,
             md5_after,on_disk_md5_match,reason}?, cures_planned, cures_applied,
             rescan{rc,ids,station_count,residual_zero}?,
             resprobe{rc,rc_ok,n_records,md5_match}?}],
     wall{root:{root,reason,detail}}, timing? (audit: per-phase timings + the
     jobs dimension),
     final{verdict,rounds_run,red_files,
     cures_planned_total,cures_applied_total,wall_count}, verdict}
  verdict ∈ unclogged|wall|rounds-exhausted|audit (audit = read-only
  baseline, exit 0).
  Per-round progress log line (explicit stdout): [round k/N] root=X cures=Y.

Usage (all paths parameterized; zero hardcoded absolute paths; component
paths are derived from the repository this file lives in, following the
pushci precedent):
  python3 tools/unclog.py --src DIR --world DIR \\
      [--candidates TSV | --chain-ledgers LEDGER.json ...] \\
      [--repo-path DIR] [--rounds 5] [--apply] [--top 25] [--scan-ids S]
      [--probe-resume] [--probe-parallel K] [--rocq-cmd TPL] [--guard PATH
      --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N
      --timeout S]
      [--pack cure_pack.json] [--workdir DIR] [--json out.json] [--events out.jsonl]
      [--once | --loop [--interval 60] [--loop-max 0]] [--sleep-scale 1.0]
      [--injector DIR] [--state-file STATE.json]
  python3 tools/unclog.py --src DIR [--world DIR] --audit [--injector DIR] \\
      [--repo-path DIR] [--top 25] [--probe-parallel K] [--workdir DIR] \\
      [--json out.json]
  python3 tools/unclog.py --selftest

Exit codes: 0 = unclogged / audit; 1 = wall / rounds-exhausted (a failing result is
  data, not a tool failure; explicit stdout); 2 = usage error / injection-scenario
  shape error (--rounds with --loop / --audit with --apply, --loop, or
  --state-file / --probe-parallel<1 / --state-file directory missing);
  9 = fail-loud (path missing / tool error: an engine subprocess exits nonzero
  for non-data reasons / frozen roster unavailable / full-tree enumeration
  finds zero candidates / audit zero-write self-check broken / state file
  corrupted and refused; no silent rebuild).
  --selftest: 0 = all pass / 2 = assertion failure.

World discipline: this tool never writes --world (the world's .vo foundation
is seeded by the caller per the certification rules of wash/world_hook.py;
whether a post-repair re-probe clears the failure set depends on world
generation; this tool reports honestly and never forces an outcome).
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "unclog"
SCHEMA = "rocqwash-unclog/1"
CHAIN_SCHEMA = "rocqwash-chain-graph/1"
STATE_SCHEMA = "rocqwash-sentinel-state/1"   # --state-file shares the cw_sentinel state shape
VERDICT_EXIT = {"unclogged": 0, "wall": 1, "rounds-exhausted": 1, "audit": 0}
TERMINAL_VERDICTS = ("unclogged", "wall")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
PROBE_TOOL = os.path.join(REPO_ROOT, "wash", "probe_engine.py")
CHAIN_TOOL = os.path.join(REPO_ROOT, "tools", "chain_graph.py")
CURE_TOOL = os.path.join(REPO_ROOT, "wash", "cure_applier.py")
SCAN_TOOL = os.path.join(REPO_ROOT, "scan", "scan_v4_token.py")
FROZEN8_TOOL = os.path.join(REPO_ROOT, "certify", "frozen8.py")
DEFAULT_PACK = os.path.join(REPO_ROOT, "wash", "cure_pack.json")


class UnclogError(Exception):
    """fail-loud exception carrying an exit code (2 = usage/scenario shape; 9 = missing path or tool failure)."""

    def __init__(self, msg, code=9):
        super(UnclogError, self).__init__(msg)
        self.code = code


# ---- small pieces (deterministic helpers) ----

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def basename_of(p):
    return os.path.basename(p.rstrip(os.sep)) if p else p


def sleep_scaled(sec, scale):
    """time.sleep(sec*scale); scale=0 means no real sleep (selftest vector dependency; the pushci form)."""
    time.sleep(max(0.0, float(sec) * float(scale)))


def dump_json(obj, path):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_json(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, UnicodeDecodeError, OSError) as e:
        raise UnclogError("%s JSON malformed: %s (%s)" % (what, path, e), 2)


def emit(events_fh, obj):
    """One JSONL event-stream line (sort_keys; no wall clock; deterministic content)."""
    if events_fh is None:
        return
    events_fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
    events_fh.flush()


def run_py(tool_path, cli):
    """The python3 -B <tool> <cli> subprocess single point (stdout+stderr merged; the pushci form).  Missing tool -> 9."""
    if not os.path.isfile(tool_path):
        raise UnclogError("toolchain file missing: %s" % tool_path, 9)
    p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def write_cands_tsv(path, pairs):
    """Candidates TSV (name/md5 columns; the probe_engine-required column form).  KEEP (data face): the header row is probe_engine's required TSV vocabulary."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("件名\tmd5\n")
        for name, md5 in pairs:
            fh.write("%s\t%s\n" % (name, md5))


def enumerate_tree(src):
    """Whole-tree enumeration of --src *.v -> [(name (relative path, / separated, .v stripped), md5)] (deterministic, doubly sorted)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, src).replace(os.sep, "/")
                out.append((rel[:-2], md5_of(fp)))
    return out


def tree_manifest(src):
    """The whole-file {rel (POSIX form): md5} manifest of --src (the audit
    zero-write self-proof; every file, not only .v: a one-byte add, delete or
    change shows up immediately)."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            out[os.path.relpath(fp, src).replace(os.sep, "/")] = md5_of(fp)
    return out


# ---- state (the --loop watch-mode seen persistence layer; the same shape as cw_sentinel --state-file) ----

def new_state():
    """The zero-state account (the cw_sentinel.new_state shape: three domain dicts plus this tool's differential field red_seen)."""
    return {"schema": STATE_SCHEMA, "repos": {}, "ledgers": {},
            "buildlogs": {}, "red_seen": []}


def load_state(path):
    """State loading (the cw_sentinel.load_state shape): default None / a
    missing file starts from the zero state; corruption (JSON parse failure /
    repos/ledgers/buildlogs keys missing their dict / red_seen not a list) ->
    fail-loud 9 rejection; silent rebuilding is forbidden (seen is the
    differential account; a silent rebuild would break the red-event
    re-report guarantee; the corrupted original stays untouched; recovery is
    a manual delete and a fresh zero-state start next round)."""
    if path is None:
        return new_state()
    if not os.path.isfile(path):
        return new_state()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise UnclogError("state file malformed (parse failure; silent"
                          " rebuilding forbidden): %s (%s)" % (path, e), 9)
    for k in ("repos", "ledgers", "buildlogs"):
        if not isinstance(st.get(k), dict):
            raise UnclogError("state file malformed (missing the %s dict;"
                              " silent rebuilding forbidden): %s" % (k, path), 9)
    if not isinstance(st.get("red_seen", []), list):
        raise UnclogError("state file malformed (red_seen must be a list;"
                          " silent rebuilding forbidden): %s" % path, 9)
    return st


def save_state(path, st):
    """State persistence (sort_keys canonical form; a differential event is
    emitted before this function saves: prefer a duplicate over a lost
    entry, the watch discipline).  Missing directory -> 9."""
    if path is None:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise UnclogError("state file directory missing: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- injection point: probe/resprobe probe calls canned (offline, zero real compiles) ----

class Injector(object):
    """--injector DIR/scenario.json = {"probe":[ledger...],"resprobe":[ledger...]}
    consumed strictly in order (the canned probe_engine ledger lands in the
    workdir verbatim and still feeds the real chain_graph); exhausted / missing
    series / malformed -> fail-loud 2."""

    def __init__(self, dirpath):
        sj = os.path.join(dirpath, "scenario.json")
        if not os.path.isfile(sj):
            raise UnclogError("injector scenario missing: %s" % sj, 9)
        scen = load_json(sj, "injector scenario")
        if not isinstance(scen, dict):
            raise UnclogError("injector scenario malformed (must be a dict): %s" % sj, 2)
        probe = scen.get("probe")
        if not isinstance(probe, list) or not probe:
            raise UnclogError("injector scenario lacks the canned probe series"
                              " (the offline zero-real-compile discipline;"
                              " probe must be a non-empty list): %s" % sj, 2)
        self.canned = {"probe": list(probe)}
        rp = scen.get("resprobe")
        self.canned["resprobe"] = list(rp) if isinstance(rp, list) else None
        self.counts = {"probe": 0, "resprobe": 0}

    def take(self, kind):
        lst = self.canned.get(kind)
        nth = self.counts.get(kind, 0) + 1
        if lst is None:
            raise UnclogError("injector scenario lacks the canned %s series"
                              " (call #%d of %s)" % (kind, nth, kind), 2)
        if not lst:
            raise UnclogError("injector canned %s series exhausted (call #%d)"
                              % (kind, nth), 2)
        item = lst.pop(0)
        self.counts[kind] = nth
        if not isinstance(item, dict) or not isinstance(item.get("records"), dict):
            raise UnclogError("injector canned %s entry #%d malformed (must be"
                              " a probe_ledger carrying a records dict)"
                              % (kind, nth), 2)
        return item


# ---- engine orchestration layer (probe_engine/chain_graph/cure_applier/scan_v4_token) ----

class Engines(object):
    """Subprocess orchestration of the four engines (probe/resprobe injectable;
    chain/cure/scan always run for real: pure stdlib, zero compiles, zero
    network; real orchestration, never a puppet)."""

    def __init__(self, args, injector, workdir):
        self.a = args
        self.inj = injector
        self.workdir = workdir

    # -- probe_engine (step 1 collect / step 4 re-probe; injectable) ----
    def probe(self, kind, cands_tsv, out_json):
        if self.inj is not None:
            canned = self.inj.take(kind)
            dump_json(canned, out_json)
            return 0, "[injector] canned %s -> %s" % (kind, out_json), canned
        a = self.a
        if not a.world:
            raise UnclogError("--world is required (a real %s probe; for offline use --injector)" % kind, 9)
        cli = ["--candidates", cands_tsv, "--src", a.src, "--world", a.world,
               "--out", out_json,
               "--logdir", os.path.join(self.workdir, "probe-logs"),
               "--rocq-cmd", a.rocq_cmd, "--timeout", str(a.timeout),
               "--jobs", str(a.probe_parallel)]   # --probe-parallel passthrough (default 1)
        if a.guard:
            cli += ["--guard", a.guard, "--guard-reg", a.guard_reg,
                    "--guard-front", str(a.guard_front),
                    "--guard-mid", str(a.guard_mid),
                    "--guard-maxwait", str(a.guard_maxwait)]
        if not a.probe_resume:
            cli += ["--fresh"]   # each round probes the current failure set fresh (resume would skip unchanged files and keep stale entries)
        rc, out = run_py(PROBE_TOOL, cli)
        if rc != 0:
            raise UnclogError("probe_engine tool failure rc=%d (%s): %s"
                              % (rc, kind, out[-300:]), 9)
        return rc, out, load_json(out_json, "probe ledger")

    def resprobe(self, names_md5, out_json):
        """Step 4 re-probe of the treated file: a mini candidates list -> probe_engine (fresh; the same world as the collect phase)."""
        tsv = out_json[:-len(".json")] + ".cands.tsv"
        write_cands_tsv(tsv, names_md5)
        return self.probe("resprobe", tsv, out_json)

    # -- chain_graph (step 2 chain root; always runs for real) ----
    def chain(self, ledger_paths, out_json):
        cli = list(ledger_paths) + ["--json", out_json, "--top", str(self.a.top)]
        rc, out = run_py(CHAIN_TOOL, cli)
        if rc != 0:
            raise UnclogError("chain_graph tool failure rc=%d: %s" % (rc, out[-300:]), 9)
        graph = load_json(out_json, "chain-root graph")
        if graph.get("schema") != CHAIN_SCHEMA:
            raise UnclogError("chain-root graph schema unrecognized: %r"
                              " (expected %s)"
                              % (graph.get("schema"), CHAIN_SCHEMA), 9)
        return graph, out

    # -- cure_applier (step 3 apply; always runs for real; dry run by default, --apply applies) ----
    def cure(self, root_file, apply_flag, out_json):
        cli = ["--file", root_file, "--pack", self.a.pack, "--json", out_json]
        if apply_flag:
            cli += ["--apply"]
        rc, out = run_py(CURE_TOOL, cli)
        rep = load_json(out_json, "cure report") if os.path.exists(out_json) else None
        return rc, rep, out

    # -- scan_v4_token (step 4 re-scan; always runs for real) ----
    def scan(self, root_file, out_json):
        cli = ["--file", root_file, "--ids", self.a.scan_ids, "--json", out_json]
        rc, out = run_py(SCAN_TOOL, cli)
        if rc != 0:
            raise UnclogError("scan_v4_token tool failure rc=%d: %s" % (rc, out[-300:]), 9)
        return load_json(out_json, "token survey")


# ---- the frozen roster (certify/frozen8.py; precheck rejection; missing ledger is fail-closed) ----

def frozen8_rels():
    """frozen8 --ledger subprocess fetch of the rostered eight rels (fail-closed: rc != 0 / zero rows -> 9)."""
    rc, out = run_py(FROZEN8_TOOL, ["--ledger"])
    if rc != 0:
        raise UnclogError("the frozen8 roster unavailable rc=%d (fail-closed,"
                          " applying is forbidden): %s"
                          % (rc, out[-300:]), 9)
    rels = []
    for ln in out.splitlines():
        f = ln.split()
        if len(f) == 2 and len(f[0]) == 32 and all(c in "0123456789abcdef" for c in f[0]):
            rels.append(f[1])
    if not rels:
        raise UnclogError("frozen8 --ledger output has no parseable roster rows (fail-closed, applying is forbidden)", 9)
    return rels


def build_frozen_hit(src, repo_path):
    """Roster -> a rejection-judging closure: True when the root name hits a
    rel / basename / extension-stripped name, or the root file's realpath hits
    a rostered file (resolved against both --src and --repo-path).
    -> (hit, rostered count)."""
    names, files = set(), set()
    rels = frozen8_rels()
    for rel in rels:
        names.add(rel)
        base = os.path.basename(rel)
        names.add(base)
        names.add(base.rsplit(".", 1)[0] if "." in base else base)
        for tree in (src, repo_path):
            files.add(os.path.realpath(os.path.join(tree, rel.replace("/", os.sep))))

    def hit(root_name, root_file):
        if root_name in names:
            return True
        try:
            return os.path.realpath(root_file) in files
        except OSError:
            return False

    return hit, len(rels)


# ---- closed-loop state machine (one round = 1 collect -> 2 chain root -> 3 apply -> 4 recheck; the verdict is judged at step 1) ----

def chain_top_of(graph, top_n):
    """The chain-root top-list summary (top_order keeps the explicit rank; the same rank as chain_graph)."""
    out = []
    for lib in list(graph.get("top_order", []))[:top_n]:
        e = graph["libs"][lib]
        out.append({"lib": lib, "n": e["n"], "dependents": list(e["dependents"]),
                    "self": dict(e["self"])})
    return out


def args_summary(a):
    """args -> the report["args"] summary (basenames only, zero absolute paths; shared by the closed loop and audit)."""
    return {"rounds": a.rounds, "top": a.top, "scan_ids": a.scan_ids,
            "apply": bool(a.apply), "loop": bool(a.loop),
            "loop_max": a.loop_max, "interval": a.interval,
            "sleep_scale": a.sleep_scale, "probe_resume": bool(a.probe_resume),
            "probe_parallel": a.probe_parallel,
            "src": basename_of(a.src), "world": basename_of(a.world) if a.world else None,
            "repo_path": basename_of(a.repo_path),
            "candidates": basename_of(a.candidates) if a.candidates else None,
            "chain_ledgers": [basename_of(p) for p in (a.chain_ledgers or [])],
            "pack": basename_of(a.pack),
            "injector": basename_of(a.injector) if a.injector else None,
            "state_file": basename_of(a.state_file) if a.state_file else None,
            "guard": basename_of(a.guard) if a.guard else None,
            "rocq_cmd": a.rocq_cmd, "timeout": a.timeout}


class UnclogRun(object):
    """One closed-loop cycle.  An empty failure set -> unclogged; no canonical
    washable root / every root walled -> wall; rounds exhausted with failures
    remaining -> rounds-exhausted (the final judging probe runs once more
    after the last round)."""

    def __init__(self, args, engines, frozen_hit, events_fh, cycle, source,
                 cands_tsv, workdir, state=None, state_path=None):
        self.a = args
        self.engines = engines
        self.frozen_hit = frozen_hit
        self.events_fh = events_fh
        self.cycle = cycle
        self.source = source
        self.cands_tsv = cands_tsv
        self.workdir = workdir
        self.state = state          # the watch-shaped seen account (when --state-file is given)
        self.state_path = state_path
        self.resprobe_ledgers = []
        self.last_red = []
        self.report = {
            "schema": SCHEMA,
            "mode": {"source": source, "apply": bool(args.apply),
                     "injector": args.injector is not None, "loop": bool(args.loop)},
            "args": self._args_summary(),
            "rounds": [],
            "wall": {},
            "final": {"verdict": None, "rounds_run": 0, "red_files": [],
                      "cures_planned_total": 0, "cures_applied_total": 0,
                      "wall_count": 0},
            "verdict": None,
        }

    def _args_summary(self):
        return args_summary(self.a)

    # -- the wall account (deduped by root; deterministic) ----
    def wall_add(self, root, reason, detail):
        if root not in self.report["wall"]:
            self.report["wall"][root] = {"root": root, "reason": reason,
                                         "detail": detail}
            print("WALL: %s — %s (%s)" % (root, reason, detail))

    def wall_from_graph(self, graph):
        """Top-list unwashable roots enter the wall (idempotent; a root already carrying its reason is not re-recorded)."""
        for lib in graph.get("top_order", []):
            if lib in self.report["wall"]:
                continue
            s = graph["libs"][lib]["self"]
            if not s.get("probed"):
                self.wall_add(lib, "unprobed",
                              "root file never entered the candidate set"
                              " (UNPROBED; probe it as a candidate)")
            elif not s.get("washable"):
                self.wall_add(lib, "self-unwashable",
                              "the root file is itself blocked rc=%s verdict=%s"
                              " (a mid-chain ring; cure the root's own cause"
                              " first)"
                              % (s.get("rc"), s.get("verdict")))
            # a washable root already walled (cure-miss/frozen) carries its
            # reason on the roster; not re-recorded

    # -- step 1: collect ----
    def collect(self, k):
        """-> (graph, red_files, probe_summary); the failure account = stats.rc1 union stats.other."""
        wd = self.workdir
        if self.source == "chain-ledgers":
            ledgers = list(self.a.chain_ledgers) + list(self.resprobe_ledgers)
            graph, _out = self.engines.chain(
                ledgers, os.path.join(wd, "round-%d.chain.json" % k))
            tag = "merge"
            led_bns = [basename_of(p) for p in ledgers]
        else:
            pj = os.path.join(wd, "round-%d.probe.json" % k)
            _rc, _out, _ledger = self.engines.probe("probe", self.cands_tsv, pj)
            graph, _out = self.engines.chain([pj],
                                             os.path.join(wd, "round-%d.chain.json" % k))
            tag = "probe"
            led_bns = [os.path.basename(pj)]
        red = sorted(set(graph["stats"]["rc1"]) | set(graph["stats"]["other"]))
        summary = {"source": tag, "n_records": graph["stats"]["merged_total"],
                   "n_red": len(red), "red_files": red, "ledgers": led_bns}
        return graph, red, summary

    # -- failure-account differential (the --state-file watch-shaped seen; only-new) ----
    def red_diff(self, red):
        """Cross-round failure-account differential events, only-new: a newly
        seen failing file (not in state.red_seen) emits {"event":"red-new",
        new_red:[...], red_total, seen_before}, then the seen account merges
        and persists (the event is emitted before the state is saved; prefer
        a duplicate over a lost entry, the watch discipline).  An already-seen
        failing file is not reported again (seen grows monotonically; the
        only-new semantics); the default without --state-file disables the
        differential (zero events, zero writes; behavior unchanged)."""
        if self.state_path is None:
            return
        seen = self.state.setdefault("red_seen", [])
        known = set(seen)
        new_red = [f for f in red if f not in known]
        if new_red:
            emit(self.events_fh, {"event": "red-new", "cycle": self.cycle,
                                  "new_red": list(new_red),
                                  "red_total": len(red),
                                  "seen_before": len(known)})
            seen.extend(new_red)
            seen.sort()
            save_state(self.state_path, self.state)

    # -- step 2: pick the chain root (the frozen precheck rejection embedded) ----
    def pick_root(self, graph):
        """Take the first self.washable=true entry (skipping already-walled
        ones; a frozen rejection enters the wall and the search continues).
        -> (root|None, root_file|None)."""
        for lib in graph.get("top_order", []):
            s = graph["libs"][lib]["self"]
            if not s.get("washable"):
                continue
            if lib in self.report["wall"]:
                continue
            root_file = os.path.join(self.a.src, lib.replace("/", os.sep) + ".v")
            if self.frozen_hit(lib, root_file):
                self.wall_add(lib, "frozen-in-service",
                              "the root name/file hits the frozen8 roster"
                              " (precheck rejection; nothing applied)")
                continue
            return lib, root_file
        return None, None

    # -- one round ----
    def run_round(self, k):
        a = self.a
        rd = {"round": k}
        graph, red, summary = self.collect(k)
        rd["probe_summary"] = summary
        rd["chain_top"] = chain_top_of(graph, a.top)
        self.last_red = red
        print("[round %d/%d] collect: %s failing %d: %s"
              % (k, a.rounds, summary["source"], len(red), ",".join(red) or "-"))
        self.red_diff(red)   # between-round red-account diff event, only-new (with --state-file present)

        # step 5 verdict: an empty failure account = unclogged (the final judging probe covers the post-exhaustion extra probe)
        if not red:
            rd["root"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (red empty)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "red_empty": True})
            self.report["rounds"].append(rd)
            return "unclogged"
        # step 5 verdict: rounds exhausted (the final judging probe still failing)
        if k > a.rounds:
            rd["root"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (rounds exhausted)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "red_empty": False})
            self.report["rounds"].append(rd)
            return "rounds-exhausted"

        self.wall_from_graph(graph)
        root, root_file = self.pick_root(graph)
        if root is None:
            if not graph.get("top_order"):
                # zero chain roots (no failing file has a missing-library
                # group; a generation-gap or engine-cause failure); the wall
                # account must not go silent: add a no-chain-root entry listing
                # every failing file (the verdict stays wall; never force-fitted)
                self.wall_add("-", "no-chain-root",
                              "%d failing files and none has a missing-library"
                              " chain root (generation-gap / engine-cause"
                              " failure; never force-fitted): %s"
                              % (len(red), ",".join(red)))
            rd["root"] = None
            rd["cure"] = None
            rd["cures_planned"] = 0
            rd["cures_applied"] = 0
            rd["rescan"] = None
            rd["resprobe"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (wall)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "wall": True})
            self.report["rounds"].append(rd)
            return "wall"
        rd["root"] = root
        rd["root_file"] = root + ".v"
        print("chain_top: " + ", ".join(
            "%s(n=%d,washable=%s)" % (t["lib"], t["n"], t["self"]["washable"])
            for t in rd["chain_top"][:3]))

        # step 3 apply (the canonical pack only; the chain-root file only)
        cure_info = None
        cures_planned = 0
        cures_applied = 0
        proceed = False
        if not os.path.exists(root_file):
            self.wall_add(root, "root-file-missing",
                          "the chain-root file is missing: %s (no source file"
                          " corresponds to the missing library behind the"
                          " failure)" % rd["root_file"])
        else:
            cj = os.path.join(self.workdir, "round-%d.cure.json" % k)
            rc, rep, out = self.engines.cure(root_file, False, cj)
            if rc == 4:
                self.wall_add(root, "exclusive-group-conflict",
                              "the variant requires a human --only choice"
                              " (automatic substitution forbidden); groups=%s"
                              % ((rep or {}).get("exclusive_group_conflict")))
            elif rc != 0:
                raise UnclogError("cure_applier tool failure rc=%d (dry run"
                                  " %s): %s"
                                  % (rc, root_file, out[-300:]), 9)
            else:
                total = sum(int(v.get("matches", 0))
                            for v in (rep or {}).get("report", {}).values())
                cure_info = {"stage": "dry-run", "rc": rc, "total_matches": total,
                             "patterns": dict(
                                 (pid, int(v.get("matches", 0)))
                                 for pid, v in (rep or {}).get("report", {}).items()
                                 if v.get("matches")),
                             "md5_before": (rep or {}).get("md5_before"),
                             "md5_after": (rep or {}).get("md5_after")}
                if total == 0:
                    self.wall_add(root, "cure-miss",
                                  "the canonical-pack dry run produced zero"
                                  " plan (total_matches=0)")
                else:
                    cures_planned = total
                    proceed = True
                    if a.apply:
                        aj = os.path.join(self.workdir, "round-%d.apply.json" % k)
                        rc2, rep2, out2 = self.engines.cure(root_file, True, aj)
                        if rc2 == 4:
                            self.wall_add(root, "exclusive-group-conflict",
                                          "the apply hit a variant conflict"
                                          " (zero writes)")
                            proceed = False
                        elif rc2 == 1:
                            self.wall_add(root, "idempotence-fail",
                                          "the apply idempotence assertion"
                                          " failed (cure_applier refused to"
                                          " write; the file is untouched)")
                            proceed = False
                        elif rc2 != 0:
                            raise UnclogError("cure_applier tool failure rc=%d"
                                              " (apply %s): %s"
                                              % (rc2, root_file, out2[-300:]), 9)
                        else:
                            cures_applied = total
                            cure_info["stage"] = "applied"
                            cure_info["rc"] = rc2
                            cure_info["md5_after"] = (rep2 or {}).get("md5_after")
                            cure_info["on_disk_md5_match"] = (
                                md5_of(root_file) == cure_info["md5_after"])
                            print("APPLIED %s cures=%d md5_after=%s on_disk_match=%s"
                                  % (root, cures_applied, cure_info["md5_after"],
                                     cure_info["on_disk_md5_match"]))

        # step 4 recheck (the rescan residual should be zero and the resprobe rc should be 0; reported as observed, never polished)
        rescan = None
        resprobe = None
        if proceed:
            sj = os.path.join(self.workdir, "round-%d.scan.json" % k)
            census = self.engines.scan(root_file, sj)
            st = census.get("station_count")
            rescan = {"rc": 0, "ids": a.scan_ids, "station_count": st,
                      "residual_zero": (st == 0)}
            rj = os.path.join(self.workdir, "round-%d.resprobe.json" % k)
            _rc, _out, led = self.engines.resprobe([(root, md5_of(root_file))], rj)
            recs = led.get("records", {})
            rec = recs.get(root, {})
            resprobe = {"rc": rec.get("rc"), "rc_ok": (rec.get("rc") == 0),
                        "n_records": len(recs), "md5_match": rec.get("md5_match")}
            self.resprobe_ledgers.append(rj)
            print("RECHECK %s rescan_station=%d resprobe_rc=%s"
                  % (root, st, resprobe["rc"]))

        rd["cure"] = cure_info
        rd["cures_planned"] = cures_planned
        rd["cures_applied"] = cures_applied
        rd["rescan"] = rescan
        rd["resprobe"] = resprobe
        cures_log = cures_applied if a.apply else cures_planned
        suffix = "" if (resprobe is None or resprobe["rc_ok"]) \
            else (" resprobe-rc=%s (expected 0, not reached; recorded as"
                  " observed)" % resprobe["rc"])
        rd["log"] = "[round %d/%d] root=%s cures=%d%s" % (k, a.rounds, root,
                                                          cures_log, suffix)
        print(rd["log"])
        emit(self.events_fh, {"event": "round", "cycle": self.cycle, "round": k,
                              "root": root, "cures": cures_log,
                              "cures_applied": cures_applied})
        self.report["rounds"].append(rd)
        return None   # next round

    def run(self):
        k = 0
        verdict = None
        while True:
            k += 1
            verdict = self.run_round(k)
            if verdict:
                break
        fin = self.report["final"]
        fin["verdict"] = verdict
        fin["rounds_run"] = len(self.report["rounds"])
        fin["red_files"] = list(self.last_red)
        fin["cures_planned_total"] = sum(r.get("cures_planned", 0)
                                         for r in self.report["rounds"])
        fin["cures_applied_total"] = sum(r.get("cures_applied", 0)
                                         for r in self.report["rounds"])
        fin["wall_count"] = len(self.report["wall"])
        self.report["verdict"] = verdict
        emit(self.events_fh, {"event": "cycle_end", "cycle": self.cycle,
                              "verdict": verdict,
                              "rounds_run": fin["rounds_run"]})
        return verdict, self.report


# ---- --audit read-only audit (a real-tree blockage baseline; single pass; nothing applied, nothing written to the tree) ----

def run_audit(args, engines, frozen_hit, events_fh, source, cands_tsv,
              workdir, enum_sec, holder):
    """--audit single-pass read-only baseline (real-tree baseline data): a
    whole-tree probe dry-run collect -> chain_graph -> the blockage baseline
    report.  Same schema rocqwash-unclog/1: final.verdict = audit; one round
    (probe_summary/chain_top fully present; cure/rescan/resprobe always None;
    cures_planned/cures_applied always 0); the wall account records every
    graph verdict: unprobed/self-unwashable/frozen-in-service root by root
    (data enters the account, it is not a stop condition; audit picks no root
    and applies nothing); a zero-chain-root failure account gets a
    no-chain-root entry so the wall never goes silent; exit 0 (a failing
    result is baseline data, not a tool failure).  The hard zero-write
    guarantee = the --src whole-file md5 manifest must prove identical before
    and after the run (probe_engine copies files out of the tree to compile,
    wash/probe_engine.py:163, and cleans its products at py:194; any manifest
    mismatch is fail-loud 9 and a polluted baseline is never emitted).  The
    elapsed time of each segment enters report["timing"] (the measured wall
    clock; the report's only non-deterministic section); the jobs dimension
    (the --probe-parallel K argument, the probe_engine --jobs passthrough,
    default 1) enters the same section; the same candidate face with
    different K values is comparable across runs (the parallel-profile
    collection point)."""
    a = args
    print("=== AUDIT read-only baseline (one-pass probe collect -> chain_graph; nothing applied, nothing written to the tree) ===")
    t0 = time.time()
    before = tree_manifest(a.src)
    manifest_sec = time.time() - t0
    rd = {"round": 1}
    t1 = time.time()
    if source == "chain-ledgers":
        graph, _out = engines.chain(list(a.chain_ledgers),
                                    os.path.join(workdir, "audit.chain.json"))
        summary = {"source": "merge",
                   "ledgers": [basename_of(p) for p in a.chain_ledgers]}
    else:
        pj = os.path.join(workdir, "audit.probe.json")
        _rc, _out, _led = engines.probe("probe", cands_tsv, pj)
        graph, _out = engines.chain([pj],
                                    os.path.join(workdir, "audit.chain.json"))
        summary = {"source": "probe", "ledgers": [os.path.basename(pj)]}
    probe_chain_sec = time.time() - t1
    red = sorted(set(graph["stats"]["rc1"]) | set(graph["stats"]["other"]))
    summary.update({"n_records": graph["stats"]["merged_total"],
                    "n_red": len(red), "red_files": red})
    rd["probe_summary"] = summary
    rd["chain_top"] = chain_top_of(graph, a.top)
    print("[audit] collect: %s failing %d: %s"
          % (summary["source"], len(red), ",".join(red) or "-"))
    print("chain_top: " + (", ".join(
        "%s(n=%d,washable=%s)" % (t["lib"], t["n"], t["self"]["washable"])
        for t in rd["chain_top"][:3]) or "-"))

    # the wall account (every graph verdict recorded, including the frozen precheck: data enters the account, not a stop condition)
    wall = {}

    def wall_add(root, reason, detail):
        if root not in wall:
            wall[root] = {"root": root, "reason": reason, "detail": detail}
            print("WALL: %s — %s (%s)" % (root, reason, detail))

    for lib in graph.get("top_order", []):
        s = graph["libs"][lib]["self"]
        if not s.get("probed"):
            wall_add(lib, "unprobed",
                     "root file never entered the candidate set (UNPROBED;"
                     " probe it as a candidate)")
        elif not s.get("washable"):
            wall_add(lib, "self-unwashable",
                     "the root file is itself blocked rc=%s verdict=%s"
                     " (a mid-chain ring; cure the root's own cause first)"
                     % (s.get("rc"), s.get("verdict")))
        elif frozen_hit(lib, os.path.join(a.src,
                                          lib.replace("/", os.sep) + ".v")):
            wall_add(lib, "frozen-in-service",
                     "the root name/file hits the frozen8 roster (precheck"
                     " rejection; a human-review domain)")
    if red and not graph.get("top_order"):
        wall_add("-", "no-chain-root",
                 "%d failing files and none has a missing-library chain root"
                 " (generation-gap / engine-cause failure; never"
                 " force-fitted): %s"
                 % (len(red), ",".join(red)))

    # the hard zero-write guarantee (the --src whole-file md5 manifest proves identical before/after; any violation is fail-loud 9)
    after = tree_manifest(a.src)
    if after != before:
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(k for k in set(before) & set(after)
                         if before[k] != after[k])
        raise UnclogError(
            "the audit zero-write hard guarantee broke: the --src tree was"
            " touched (changed %d / added %d / removed %d: %s)"
            % (len(changed), len(added), len(removed),
               ",".join((changed + added + removed)[:8])), 9)

    rd["root"] = None
    rd["root_file"] = None
    rd["cure"] = None
    rd["cures_planned"] = 0
    rd["cures_applied"] = 0
    rd["rescan"] = None
    rd["resprobe"] = None
    rd["log"] = "[audit] root=- cures=0 (audit baseline·red=%d)" % len(red)
    print(rd["log"])
    emit(events_fh, {"event": "round", "cycle": 1, "round": 1, "root": None,
                     "cures": 0, "audit": True, "red_empty": not red})
    emit(events_fh, {"event": "cycle_end", "cycle": 1, "verdict": "audit",
                     "rounds_run": 1})
    timing = {"enumerate_s": (round(enum_sec, 3)
                              if enum_sec is not None else None),
              "manifest_s": round(manifest_sec, 3),
              "probe_chain_s": round(probe_chain_sec, 3),
              "total_s": round(time.time() - t0, 3),
              "jobs": a.probe_parallel}
    print("[audit] timing: jobs=%d enumerate=%s manifest=%gs probe+chain=%gs"
          " total=%gs"
          % (a.probe_parallel, timing["enumerate_s"], timing["manifest_s"],
             timing["probe_chain_s"], timing["total_s"]))
    report = {
        "schema": SCHEMA,
        "mode": {"source": source, "apply": False, "audit": True,
                 "injector": a.injector is not None, "loop": False},
        "args": args_summary(a),
        "rounds": [rd],
        "wall": wall,
        "timing": timing,
        "final": {"verdict": "audit", "rounds_run": 1, "red_files": list(red),
                  "cures_planned_total": 0, "cures_applied_total": 0,
                  "wall_count": len(wall)},
        "verdict": "audit",
    }
    holder["report"] = report
    print("AUDIT: %d failing files, %d wall entries — the baseline report"
          " applies nothing and writes nothing to the tree (exit 0)"
          % (len(red), len(wall)))
    return "audit", report


# ---- main flow (--once / --loop watch mode) ----

def run(args, holder):
    # value validation (the usage-error family, exit code 2)
    if args.loop and args.rounds is not None:
        raise UnclogError("--rounds and --loop are mutually exclusive"
                          " (--rounds caps the rounds of one closed-loop pass;"
                          " the watch mode cycles whole passes and its"
                          " per-pass cap stays the default 5 — passing both"
                          " is rc=2, never a silent pick)", 2)
    if args.rounds is None:
        args.rounds = 5           # the default round cap (--rounds not given; the same value for once and loop)
    if args.rounds < 1:
        raise UnclogError("--rounds must be >= 1, got %d" % args.rounds, 2)
    if args.probe_parallel < 1:
        raise UnclogError("--probe-parallel must be >= 1, got %d (the"
                          " probe_engine --jobs passthrough; default 1)"
                          % args.probe_parallel, 2)
    if args.top < 1:
        raise UnclogError("--top must be >= 1, got %d" % args.top, 2)
    if args.interval < 0:
        raise UnclogError("--interval must be >= 0, got %s" % args.interval, 2)
    if args.sleep_scale < 0:
        raise UnclogError("--sleep-scale must be >= 0, got %s" % args.sleep_scale, 2)
    if args.loop_max < 0:
        raise UnclogError("--loop-max must be >= 0, got %d" % args.loop_max, 2)
    if args.audit and args.apply:
        raise UnclogError("--audit and --apply are mutually exclusive (the audit is read-only and applies nothing; passing both is rc=2)", 2)
    if args.audit and args.loop:
        raise UnclogError("--audit and --loop are mutually exclusive (the"
                          " audit is a single-pass baseline; the watch-mode"
                          " cycling is not audit semantics)", 2)
    if args.audit and args.state_file:
        raise UnclogError("--audit and --state-file are mutually exclusive"
                          " (the audit is a single-pass baseline; the seen"
                          " watch differential is not audit semantics)", 2)
    if args.candidates and args.chain_ledgers:
        raise UnclogError("--candidates and --chain-ledgers are mutually exclusive (pick one of the three candidate sources)", 2)

    # path validation (9; tool presence precheck)
    for label, p in (("probe_engine", PROBE_TOOL), ("chain_graph", CHAIN_TOOL),
                     ("cure_applier", CURE_TOOL), ("scan_v4_token", SCAN_TOOL),
                     ("frozen8", FROZEN8_TOOL)):
        if not os.path.isfile(p):
            raise UnclogError("tool missing: %s (%s)" % (label, p), 9)
    if not args.src:
        raise UnclogError("FAIL-LOUD: --src is required", 2)
    if not os.path.isdir(args.src):
        raise UnclogError("--src path missing: %s" % args.src, 9)
    if args.candidates and not os.path.exists(args.candidates):
        raise UnclogError("--candidates path missing: %s" % args.candidates, 9)
    for p in (args.chain_ledgers or []):
        if not os.path.exists(p):
            raise UnclogError("--chain-ledgers path missing: %s" % p, 9)
    if not os.path.exists(args.pack):
        raise UnclogError("--pack path missing: %s" % args.pack, 9)
    if args.injector and not os.path.isdir(args.injector):
        raise UnclogError("--injector directory missing: %s" % args.injector, 9)
    if args.state_file:
        d = os.path.dirname(os.path.abspath(args.state_file))
        if d and not os.path.isdir(d):
            raise UnclogError("--state-file directory missing: %s" % d, 9)

    # state loading (the --state-file watch-shaped seen; corruption rejects with 9, fail-loud)
    state = load_state(args.state_file)
    if args.state_file:
        print("state -> %s (seen %d entries; the rocqwash-sentinel-state/1"
              " shape)" % (args.state_file, len(state.get("red_seen", []))))

    # workdir
    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)
        workdir = args.workdir
    else:
        workdir = tempfile.mkdtemp(prefix="rocqwash_unclog_")
    print("workdir -> %s" % workdir)

    # the three candidate sources
    enum_sec = None
    if args.candidates:
        source, cands_tsv = "tsv", args.candidates
        print("candidate face: --candidates %s" % args.candidates)
    elif args.chain_ledgers:
        source, cands_tsv = "chain-ledgers", None
        print("candidate face: --chain-ledgers %s (merge mode; no per-round"
              " whole re-probe)" % " ".join(args.chain_ledgers))
    else:
        _t0 = time.time()
        pairs = enumerate_tree(args.src)
        enum_sec = time.time() - _t0
        if not pairs:
            raise UnclogError("--src whole-tree enumeration found zero .v candidates: %s" % args.src, 9)
        cands_tsv = os.path.join(workdir, "tree-cands.tsv")
        write_cands_tsv(cands_tsv, pairs)
        source = "tree"
        print("candidate face: --src whole-tree enumeration, %d files -> %s" % (len(pairs), cands_tsv))

    # the injector (probe/resprobe canned; zero real compiles)
    inj = Injector(args.injector) if args.injector else None
    if inj is not None:
        print("injector: %s (probe canned %d shots; resprobe canned %s)"
              % (args.injector, len(inj.canned["probe"]),
                 len(inj.canned["resprobe"]) if inj.canned["resprobe"] is not None
                 else "missing"))
    if args.probe_parallel > 1 and not inj and source != "chain-ledgers":
        print("ADVISE(thermal): --probe-parallel %d>1 means multiple"
              " in-machine rocqworkers running concurrently and a rising heat"
              " load (with --guard given, K<=2 is advised; this note is not"
              " enforced — the user decides)"
              % args.probe_parallel)

    # the frozen roster (fail-closed precheck)
    frozen_hit, frozen_n = build_frozen_hit(args.src, args.repo_path)
    print("frozen roster: %d entries (fetched live via certify/frozen8.py"
          " --ledger; precheck rejection)" % frozen_n)

    # the event stream (JSONL)
    events_path = args.events_file or \
        (os.path.join(workdir, "events.jsonl") if args.loop else None)
    events_fh = io.open(events_path, "w", encoding="utf-8", newline="\n") \
        if events_path else None

    engines = Engines(args, inj, workdir)
    cycles = []
    verdict = None
    report = None
    try:
        if args.audit:
            # --audit single-pass read-only baseline (never enters the closed loop; applies nothing; the --src md5 manifest self-proofs before/after)
            verdict, report = run_audit(args, engines, frozen_hit, events_fh,
                                        source, cands_tsv, workdir, enum_sec,
                                        holder)
            cycles.append({"cycle": 1, "verdict": verdict})
        else:
            while True:
                cycle = len(cycles) + 1
                u = UnclogRun(args, engines, frozen_hit, events_fh, cycle,
                              source, cands_tsv, workdir, state=state,
                              state_path=args.state_file)
                verdict, report = u.run()
                holder["report"] = report
                cycles.append({"cycle": cycle, "verdict": verdict})
                if verdict in TERMINAL_VERDICTS:
                    break
                if not args.loop:
                    break
                if args.loop_max and cycle >= args.loop_max:
                    break
                print("[cycle %d] %s — the watch mode rests %g s before the"
                      " next patrol"
                      % (cycle, verdict, args.interval * args.sleep_scale))
                sleep_scaled(args.interval, args.sleep_scale)
    finally:
        if events_fh is not None:
            events_fh.close()

    if len(cycles) > 1 or args.loop:
        report["cycles"] = cycles
    code = VERDICT_EXIT[verdict]
    if args.json_out:
        dump_json(report, args.json_out)
        print("report -> %s" % args.json_out)
    print("VERDICT: %s (exit %d)" % (verdict, code))
    return code


# ---- CLI ----------------------------------------------------------------------

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
        description="blockage-clearing closed-loop engine: probe collect ->"
                    " chain_graph chain root -> cure_applier apply ->"
                    " scan/probe recheck -> verdict; --rounds caps the spin;"
                    " --apply defaults off (a full dry run, zero writes);"
                    " injectable for offline use; schema rocqwash-unclog/1")
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="the source-tree root (the root file <root>.v lives"
                         " here; the whole-tree enumeration source too)")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="the world directory (the probe_engine probe cwd;"
                         " the caller seeds the .vo base per the world_hook"
                         " discipline; this tool writes nothing there; optional"
                         " in merge mode, required for a real probe)")
    ap.add_argument("--candidates", default=None, metavar="FILE",
                    help="the candidates TSV (source 1; the probe_engine"
                         " header convention)")
    ap.add_argument("--chain-ledgers", dest="chain_ledgers", nargs="+",
                    default=None, metavar="LEDGER.json",
                    help="existing probe ledgers (source 2; argv order = merge"
                         " order; later batches override earlier ones)")
    ap.add_argument("--repo-path", default=REPO_ROOT, metavar="DIR",
                    help="the resolution root for rostered frozen files (the"
                         " repository holding this tool, by default)")
    ap.add_argument("--rounds", type=int, default=None, metavar="N",
                    help="the round cap of one closed-loop pass (default 5;"
                         " rounds exhausted with failures remaining ="
                         " rounds-exhausted; mutually exclusive with --loop,"
                         " passing both is rc=2)")
    ap.add_argument("--apply", action="store_true",
                    help="the apply switch (default off = a full dry run with"
                         " zero writes; no separate --yes switch is needed)")
    ap.add_argument("--audit", action="store_true",
                    help="read-only audit: a one-pass probe collect ->"
                         " chain_graph -> the blockage baseline report"
                         " (final=audit; nothing applied; the --src whole-file"
                         " md5 manifest proves identical before and after;"
                         " cures always empty; mutually exclusive with"
                         " --apply/--loop)")
    ap.add_argument("--top", type=int, default=25, metavar="N",
                    help="the chain-root top-list truncation (default 25; the"
                         " chain_graph convention)")
    ap.add_argument("--scan-ids", dest="scan_ids", default="S", metavar="IDS",
                    help="the scan_v4_token tracked identifier (default S)")
    ap.add_argument("--pack", default=DEFAULT_PACK, metavar="FILE",
                    help="the canonical cure_pack (default"
                         " wash/cure_pack.json v1.3)")
    ap.add_argument("--probe-resume", dest="probe_resume", action="store_true",
                    help="have probe_engine resume (by default every round"
                         " probes the current failure set fresh with --fresh)")
    ap.add_argument("--probe-parallel", dest="probe_parallel", type=int,
                    default=1, metavar="K",
                    help="the probe_engine --jobs parallelism passthrough"
                         " (default 1 = file-by-file serial with zero drift;"
                         " shared by --audit; with --guard given, K<=2 is"
                         " advised for the thermal budget — the user decides)")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd",
                    default='rocq c -Q . "" {name}.v', metavar="TPL",
                    help="the probe command template passed through to"
                         " probe_engine")
    ap.add_argument("--guard", default=None, metavar="PATH",
                    help="cpu_guard.sh passed through to probe_engine"
                         " (required for real compiles)")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_unclog", metavar="DIR")
    ap.add_argument("--guard-front", dest="guard_front", type=int, default=0)
    ap.add_argument("--guard-mid", dest="guard_mid", type=int, default=1)
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int, default=600)
    ap.add_argument("--timeout", type=int, default=1500,
                    help="per-file timeout seconds passed through to"
                         " probe_engine")
    ap.add_argument("--workdir", default=None, metavar="DIR",
                    help="the per-round ledger/report artifacts directory"
                         " (default mkdtemp; the path is printed to stdout)")
    ap.add_argument("--json", dest="json_out", default=None, metavar="out.json",
                    help="the report output path (rocqwash-unclog/1;"
                         " sort_keys)")
    ap.add_argument("--events", dest="events_file", default=None, metavar="FILE",
                    help="the JSONL event-stream output (--loop defaults to"
                         " <workdir>/events.jsonl)")
    ap.add_argument("--once", action="store_true",
                    help="one closed-loop pass (the default; pairs with --loop"
                         " in the dual-mode interface discipline)")
    ap.add_argument("--loop", action="store_true",
                    help="the live watch mode: closed-loop passes repeat until"
                         " a terminal verdict or the --loop-max cap")
    ap.add_argument("--interval", type=float, default=60.0, metavar="S",
                    help="seconds between watch passes (default 60, multiplied"
                         " by --sleep-scale)")
    ap.add_argument("--loop-max", dest="loop_max", type=int, default=0, metavar="N",
                    help="the watch-pass cap (default 0 = unbounded)")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float, default=1.0,
                    metavar="F", help="the multiplier for every sleep (the"
                         " selftest uses 0 = no real sleep)")
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="offline injection: DIR/scenario.json (the"
                         " probe/resprobe canned probe_ledgers are consumed"
                         " strictly in order; zero real compiles)")
    ap.add_argument("--state-file", dest="state_file", default=None,
                    metavar="FILE",
                    help="the watch-mode seen state file"
                         " (rocqwash-sentinel-state/1; the same shape as"
                         " cw_sentinel --state-file, mutually readable and"
                         " writable; cross-round failure-account differential"
                         " events are only-new; corruption rejects with 9 and"
                         " silent rebuilding is forbidden)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    holder = {}
    try:
        code = run(args, holder)
    except UnclogError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        rep = holder.get("report")
        if rep is not None and args.json_out:
            rep.setdefault("final", {})["verdict"] = "engine-error"
            dump_json(rep, args.json_out)
            print("partial report -> %s" % args.json_out, file=sys.stderr)
        sys.exit(e.code)
    sys.exit(code)


# ---- --selftest (frozen vectors; tmp fixture trees; zero real compiles, zero network) ----

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")
NOMATCH_BODY = "Lemma ok : True.\n"


def selftest():
    """Fourteen vectors (tmp fixture trees + injector-canned probe_ledger
    series; probe/resprobe injected with zero real compiles; chain/cure/scan/
    frozen8 run for real): v1 the green path, two rounds (an --apply apply ->
    an empty failure account next round, exit 0); v2 the honest wall
    (self-unwashable, nothing applied) plus v2b the zero-chain-root failure
    account (a no-chain-root wall entry; the wall never goes silent); v3
    cure-miss enters the wall; v4 rounds exhausted (--apply applied while the
    world still fails -> rounds-exhausted with each round's record); v5 the
    --apply default-off proof (zero bytes touched); v6 JSON idempotence
    (byte-identical); v7 the frozen-roster rejection; v8 the --loop watch mode
    JSONL; v9 CLI four codes; v10 the --audit read-only baseline (zero-write
    self-proof / final=audit / cures always empty / the wall's graph verdicts /
    the frozen precheck / mutual exclusion rc=2; real-tree audit live runs
    belong to the main session; this proves the fixture level only); v11 the
    --state-file watch-shaped seen (the cross-round differential only-new
    triple run: a new failure reported / a repeated failure not reported / a
    new failure reported again; the state red_seen continues across processes;
    a corrupted state rejects with 9, silent rebuilding forbidden); v12 the
    --rounds/--loop mutual exclusion rc=2 plus the --audit/--state-file mutual
    exclusion rc=2; v13 the --jobs dimension (the audit timing section records
    jobs=K; default 1 / --probe-parallel 2 each record their own value;
    comparable across runs)."""
    tmp = tempfile.mkdtemp(prefix="rocqwash_unclog_self_")

    def run(aargs):
        p = subprocess.run(
            [sys.executable, "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          PROG + ".py")] + list(aargs),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def fixture(tag, a_body=CURE13_BODY, b_body="Require Import A.\n"):
        d = os.path.join(tmp, tag)
        src, world, wd = (os.path.join(d, x) for x in ("src", "world", "wd"))
        for p in (src, world, wd):
            os.makedirs(p)
        with io.open(os.path.join(src, "A.v"), "w", encoding="utf-8") as fh:
            fh.write(a_body)
        with io.open(os.path.join(src, "B.v"), "w", encoding="utf-8") as fh:
            fh.write(b_body)
        write_cands_tsv(os.path.join(d, "cands.tsv"),
                        [("A", md5_of(os.path.join(src, "A.v"))),
                         ("B", md5_of(os.path.join(src, "B.v")))])
        return d, src, world, wd

    def led(records):
        return {"schema": "rocqwash-probe-ledger/1", "n_records": len(records),
                "records": records}

    def rec0(f):
        return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
                "red_class": None, "verdict": "RC0", "red_count": None,
                "md5_match": None}

    def rec1(f, lib):
        return {"file": f, "md5": None, "rc": 1,
                "red": "Error: Unable to locate library | %s (while searching "
                       "for a .vos file)." % lib,
                "missing": lib, "red_class": "MISSING_LIB",
                "verdict": "RED-MISSING_LIB", "red_count": None,
                "md5_match": None}

    def scenario(dirpath, probes, resprobes=None):
        os.makedirs(dirpath, exist_ok=True)
        scen = {"probe": probes}
        if resprobes is not None:
            scen["resprobe"] = resprobes
        dump_json(scen, os.path.join(dirpath, "scenario.json"))
        return dirpath

    L1 = led({"A": rec0("A"), "B": rec1("B", "A")})          # A is a washable chain root; B misses A
    L2_GREEN = led({"A": rec0("A"), "B": rec0("B")})         # the whole world green after the repair lands
    L2_RED = led({"A": rec0("A"), "B": rec1("B", "A")})      # the world not yet repaired, still failing
    R1 = led({"A": rec0("A")})

    try:
        # v1 the green path, two rounds: round 1 cures the root A (the canonical cure13 applied) -> round 2 re-probes green, exit 0
        d, src, world, wd = fixture("v1_green")
        j1 = os.path.join(wd, "report.json")
        b_before = md5_of(os.path.join(src, "B.v"))
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
                 "--workdir", wd, "--json", j1])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "unclogged", rep["verdict"]
        assert rep["final"]["cures_applied_total"] == 1, rep["final"]
        assert "[round 1/5] root=A cures=1" in p.stdout, p.stdout[-400:]
        a_text = io.open(os.path.join(src, "A.v"), encoding="utf-8").read()
        assert "S01_BaseRing.NatLe (gnPrf f pf) k" in a_text, \
            "the applied rewrite is not the canonical form"
        assert md5_of(os.path.join(src, "B.v")) == b_before, \
            "a non-chain-root file was touched = violation"
        assert rep["rounds"][0]["rescan"]["residual_zero"] is True, rep["rounds"][0]
        assert rep["rounds"][0]["resprobe"]["rc_ok"] is True, rep["rounds"][0]
        assert rep["rounds"][0]["cure"]["on_disk_md5_match"] is True, rep["rounds"][0]
        assert rep["final"]["rounds_run"] == 2, rep["final"]
        print("v1 the green path, two rounds (--apply applied -> the failure"
              " account empty next round, exit 0): PASS")

        # v2 the honest wall: self-unwashable (a mid-chain ring); nothing applied; exit 1
        d, src, world, wd = fixture("v2_wall")
        base = os.path.join(d, "base.json")
        dump_json({"Y": {"file": "Y", "md5": None, "rc": 1,
                         "red": "Error: Illegal application", "missing": None,
                         "red_class": None, "verdict": "RED-OTHER",
                         "red_count": None, "md5_match": None},
                   "C1": rec1("C1", "Y")}, base)
        j2 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", base,
                 "--workdir", wd, "--json", j2])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j2, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["rounds"][0]["cure"] is None, \
            "a wall round must not apply anything (never force-fitted)"
        assert rep["rounds"][0]["chain_top"][0]["lib"] == "Y", rep["rounds"][0]
        assert rep["rounds"][0]["chain_top"][0]["self"]["washable"] is False
        assert rep["wall"]["Y"]["reason"] == "self-unwashable", rep["wall"]
        print("v2 the honest wall (self-unwashable, nothing applied, exit 1):"
              " PASS")

        # v2b a zero-chain-root failure account (generation-gap / engine-cause) -> the wall gains a no-chain-root entry (never silent)
        d, src, world, wd = fixture("v2b_noroot")
        base2 = os.path.join(d, "base2.json")
        dump_json({"Z1": {"file": "Z1", "md5": None, "rc": 127, "red": "",
                          "missing": None, "red_class": None,
                          "verdict": "RED-UNKNOWN", "red_count": None,
                          "md5_match": None}}, base2)
        j2b = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", base2,
                 "--workdir", wd, "--json", j2b])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j2b, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["-"]["reason"] == "no-chain-root", rep["wall"]
        assert rep["rounds"][0]["chain_top"] == [], rep["rounds"][0]
        assert rep["rounds"][0]["probe_summary"]["red_files"] == ["Z1"]
        print("v2b zero-chain-root failure account (a no-chain-root wall"
              " entry; the wall never goes silent): PASS")

        # v3 cure-miss enters the wall: a washable root but the canonical pack has no plan
        d, src, world, wd = fixture("v3_curemiss", a_body=NOMATCH_BODY)
        j3 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED]),
                 "--workdir", wd, "--json", j3])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j3, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["A"]["reason"] == "cure-miss", rep["wall"]
        assert rep["rounds"][0]["cure"]["total_matches"] == 0, rep["rounds"][0]
        assert rep["final"]["cures_applied_total"] == 0, rep["final"]
        print("v3 cure-miss enters the wall (the canonical pack has no plan;"
              " never force-fitted): PASS")

        # v4 rounds exhausted: --apply applied while the world still fails -> rounds-exhausted with each round's record
        d, src, world, wd = fixture("v4_exhaust")
        j4 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--rounds", "1", "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED], [R1]),
                 "--workdir", wd, "--json", j4])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j4, encoding="utf-8"))
        assert rep["verdict"] == "rounds-exhausted", rep["verdict"]
        assert rep["final"]["cures_applied_total"] == 1, rep["final"]
        assert rep["final"]["red_files"] == ["B"], rep["final"]
        assert "S01_BaseRing.NatLe (gnPrf f pf) k" in io.open(
            os.path.join(src, "A.v"), encoding="utf-8").read()
        assert rep["rounds"][0]["resprobe"]["rc"] == 0, rep["rounds"][0]
        print("v4 rounds exhausted (--apply applied while the world still"
              " fails; each round's record attached, exit 1): PASS")

        # v5 the --apply default-off proof: a plan exists but nothing applied -> the tmp tree untouched byte for byte
        d, src, world, wd = fixture("v5_defaultoff")
        before = {}
        for dirpath, dirnames, filenames in os.walk(src):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                before[os.path.relpath(fp, src)] = md5_of(fp)
        j5 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--rounds", "1", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED], [R1]),
                 "--workdir", wd, "--json", j5])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j5, encoding="utf-8"))
        assert rep["verdict"] == "rounds-exhausted", rep["verdict"]
        assert rep["mode"]["apply"] is False, rep["mode"]
        assert rep["final"]["cures_planned_total"] == 1, "the dry run should produce a plan"
        assert rep["final"]["cures_applied_total"] == 0, rep["final"]
        after = {}
        for dirpath, dirnames, filenames in os.walk(src):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                after[os.path.relpath(fp, src)] = md5_of(fp)
        assert before == after, \
            "the source tree changed byte-wise with --apply defaulted off =" \
            " violation"
        assert not os.path.exists(os.path.join(wd, "round-1.apply.json")), \
            "no --apply means no apply record"
        print("v5 the --apply default-off proof (a plan existed, zero bytes"
              " touched): PASS")

        # v6 JSON idempotence: a rerun with the same input is byte-identical in --json
        d, src, world, wd = fixture("v6a_idem")
        ja = os.path.join(wd, "report.json")
        run(["--src", src, "--world", world,
             "--candidates", os.path.join(d, "cands.tsv"),
             "--apply", "--injector",
             scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
             "--workdir", wd, "--json", ja])
        d, src, world, wd = fixture("v6b_idem")
        jb = os.path.join(wd, "report.json")
        run(["--src", src, "--world", world,
             "--candidates", os.path.join(d, "cands.tsv"),
             "--apply", "--injector",
             scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
             "--workdir", wd, "--json", jb])
        ba = io.open(ja, "rb").read()
        bb = io.open(jb, "rb").read()
        assert ba == bb, "a same-input rerun drifted byte-wise in --json =" \
            " violation\n%s\n%s" % (ba[-300:], bb[-300:])
        print("v6 JSON idempotence (same-input reruns are byte-identical):"
              " PASS")

        # v7 the frozen-roster rejection: the root name hits the roster (wash_engine) -> nothing applied, it enters the wall
        d, src, world, wd = fixture("v7_frozen")
        with io.open(os.path.join(src, "wash_engine.v"), "w",
                     encoding="utf-8") as fh:
            fh.write(CURE13_BODY)
        write_cands_tsv(os.path.join(d, "cands.tsv"),
                        [("A", md5_of(os.path.join(src, "A.v"))),
                         ("B", md5_of(os.path.join(src, "B.v"))),
                         ("wash_engine", md5_of(os.path.join(src, "wash_engine.v")))])
        LF = led({"wash_engine": rec0("wash_engine"), "D": rec1("D", "wash_engine")})
        j7 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [LF]),
                 "--workdir", wd, "--json", j7])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j7, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", rep["wall"]
        assert rep["rounds"][0]["cure"] is None, \
            "nothing may be applied after a frozen rejection"
        assert md5_of(os.path.join(src, "wash_engine.v")) == \
            md5_of(os.path.join(src, "wash_engine.v")), "sanity"
        frozen_body = io.open(os.path.join(src, "wash_engine.v"),
                              encoding="utf-8").read()
        assert "NatLe" not in frozen_body, "a frozen file was applied to = violation"
        print("v7 the frozen-roster rejection (fetched live from frozen8;"
              " nothing applied): PASS")

        # v8 the --loop watch mode: the JSONL event stream + stop at the terminal verdict (loop-max 1; sleep-scale 0)
        d, src, world, wd = fixture("v8_loop")
        ev = os.path.join(wd, "events.jsonl")
        j8 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--loop", "--loop-max", "1",
                 "--interval", "7", "--sleep-scale", "0", "--events", ev,
                 "--injector", scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
                 "--workdir", wd, "--json", j8])
        assert p.returncode == 0, p.stdout[-600:]
        lines = [ln for ln in io.open(ev, encoding="utf-8").read().splitlines() if ln]
        assert len(lines) >= 3, ("the event stream should contain"
                                " round/cycle_end events: %r" % lines)
        evs = [json.loads(ln) for ln in lines]
        assert evs[0]["event"] == "round" and evs[0]["root"] == "A", evs[0]
        assert evs[-1]["event"] == "cycle_end" and evs[-1]["verdict"] == "unclogged", evs[-1]
        rep = json.load(io.open(j8, encoding="utf-8"))
        assert rep["mode"]["loop"] is True and rep["cycles"][0]["verdict"] == "unclogged"
        print("v8 the --loop watch mode (the JSONL event stream; stops at the"
              " terminal verdict): PASS")

        # v9 CLI four codes
        d, src, world, wd = fixture("v9_cli")
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing --src should rc=2, got %d" % p.returncode
        p = run(["--src", os.path.join(tmp, "nope"), "--candidates",
                 os.path.join(d, "cands.tsv")])
        assert p.returncode == 9, "missing src should rc=9, got %d" % p.returncode
        p = run(["--src", src, "--candidates", os.path.join(tmp, "nope.tsv")])
        assert p.returncode == 9, "missing candidates file should rc=9, got %d" % p.returncode
        p = run(["--src", src, "--rounds", "0",
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, "--rounds 0 should rc=2, got %d" % p.returncode
        p = run(["--src", src, "--candidates", os.path.join(d, "cands.tsv"),
                 "--chain-ledgers", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, "the three-source exclusivity should rc=2, got %d" % p.returncode
        p = run(["--src", src, "--injector", os.path.join(tmp, "no_inj"),
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 9, "a missing injector scenario should rc=9, got %d" % p.returncode
        print("v9 CLI four codes (0/2/9; exclusivity; a missing injector"
              " scenario): PASS")

        # v10 the --audit read-only baseline: a whole-tree probe dry-run collect
        # -> chain_graph -> the baseline report (the zero-write self-proof;
        # final=audit; cures always empty; the wall's graph verdicts; exit 0)
        d, src, world, wd = fixture("v10_audit")
        j10 = os.path.join(wd, "report.json")
        m_before = tree_manifest(src)
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]),
                 "--workdir", wd, "--json", j10])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "audit" \
            and rep["final"]["verdict"] == "audit", rep["verdict"]
        assert rep["mode"]["audit"] is True and rep["mode"]["apply"] is False \
            and rep["mode"]["loop"] is False, rep["mode"]
        assert rep["final"]["rounds_run"] == 1, rep["final"]
        assert rep["final"]["red_files"] == ["B"], rep["final"]  # L1: B misses A
        assert rep["final"]["cures_planned_total"] == 0 \
            and rep["final"]["cures_applied_total"] == 0, rep["final"]
        assert rep["rounds"][0]["cures_planned"] == 0 \
            and rep["rounds"][0]["cures_applied"] == 0 \
            and rep["rounds"][0]["cure"] is None \
            and rep["rounds"][0]["rescan"] is None \
            and rep["rounds"][0]["resprobe"] is None, rep["rounds"][0]
        assert rep["rounds"][0]["chain_top"][0]["lib"] == "A" \
            and rep["rounds"][0]["chain_top"][0]["self"]["washable"] is True, \
            rep["rounds"][0]["chain_top"]
        assert rep["wall"] == {}, rep["wall"]   # washable and not frozen; the wall is empty
        assert rep["timing"]["enumerate_s"] is not None \
            and rep["timing"]["probe_chain_s"] >= 0 \
            and rep["timing"]["total_s"] >= 0, rep["timing"]
        assert tree_manifest(src) == m_before, \
            "the audit source tree changed byte-wise = violation"
        assert "NatLe" not in io.open(os.path.join(src, "A.v"),
                                      encoding="utf-8").read(), "链根件被动＝违例"
        print("v10 the audit read-only baseline (the zero-write self-proof;"
              " final=audit; cures always empty; the timing section): PASS")

        # v10b the audit wall account: self-unwashable enters the wall (data, not a stop condition; exit 0)
        d, src, world, wd = fixture("v10b_auditwall")
        baseb = os.path.join(d, "baseb.json")
        dump_json({"Y": {"file": "Y", "md5": None, "rc": 1,
                         "red": "Error: Illegal application", "missing": None,
                         "red_class": None, "verdict": "RED-OTHER",
                         "red_count": None, "md5_match": None},
                   "C1": rec1("C1", "Y")}, baseb)
        j10b = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", baseb, "--audit",
                 "--workdir", wd, "--json", j10b])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10b, encoding="utf-8"))
        assert rep["verdict"] == "audit" \
            and rep["wall"]["Y"]["reason"] == "self-unwashable", rep["wall"]
        assert rep["final"]["wall_count"] == 1 \
            and rep["final"]["red_files"] == ["C1", "Y"], rep["final"]  # Y itself is rc1-failing too
        print("v10b the audit wall account (self-unwashable enters the wall;"
              " exit 0, data not a stop condition): PASS")

        # v10c the audit frozen precheck: a washable root hits the roster -> frozen-in-service enters the wall
        d, src, world, wd = fixture("v10c_frozen")
        with io.open(os.path.join(src, "wash_engine.v"), "w",
                     encoding="utf-8") as fh:
            fh.write(CURE13_BODY)
        LF = led({"wash_engine": rec0("wash_engine"),
                  "D": rec1("D", "wash_engine")})
        j10c = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [LF]),
                 "--workdir", wd, "--json", j10c])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10c, encoding="utf-8"))
        assert rep["verdict"] == "audit" and \
            rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", \
            rep["wall"]
        assert "NatLe" not in io.open(os.path.join(src, "wash_engine.v"),
                                      encoding="utf-8").read(), \
            "a frozen file was applied to = violation"
        print("v10c the audit frozen precheck (fetched live from frozen8 into"
              " the wall; nothing applied): PASS")

        # v10d audit exclusivity: --apply / --loop together is rc=2
        d, src, world, wd = fixture("v10d_cli")
        p = run(["--src", src, "--audit", "--apply"])
        assert p.returncode == 2, "--audit --apply together should rc=2, got %d" \
            % p.returncode
        p = run(["--src", src, "--audit", "--loop"])
        assert p.returncode == 2, "--audit --loop together should rc=2, got %d" \
            % p.returncode
        print("v10d audit exclusivity (--apply/--loop together is rc=2):"
              " PASS")

        # v11 the --state-file watch-shaped seen: the cross-round differential
        # only-new triple run (a new failure reported / a repeated failure not
        # reported / a new failure reported again) + the state continuing
        # across processes + corruption rejecting with 9 (the chain-ledgers
        # source; zero injection, zero real compiles: the root A NOMATCH ->
        # a cure-miss wall; no rescan/resprobe path)
        d, src, world, wd = fixture("v11_state", a_body=NOMATCH_BODY)
        led1 = os.path.join(d, "led1.json")
        dump_json({"A": rec0("A"), "B": rec1("B", "A")}, led1)
        led2 = os.path.join(d, "led2.json")
        dump_json({"A": rec0("A"), "B": rec1("B", "A"), "C": rec1("C", "A")},
                  led2)
        st11 = os.path.join(d, "sentinel_state.json")

        def loop_run(ledger, ev_path, j_path):
            return run(["--src", src, "--chain-ledgers", ledger, "--loop",
                        "--interval", "7", "--sleep-scale", "0",
                        "--state-file", st11, "--events", ev_path,
                        "--json", j_path, "--workdir",
                        os.path.join(wd, "w_%s" % os.path.basename(ledger))])

        def red_news(ev_path):
            return [json.loads(ln) for ln in io.open(ev_path, encoding="utf-8")
                    if ln.strip() and json.loads(ln).get("event") == "red-new"]

        # run 1: the failure account {B} is all new -> red-new [B]; the state records seen
        ev1 = os.path.join(d, "ev1.jsonl")
        j11 = os.path.join(d, "j11.json")
        p = loop_run(led1, ev1, j11)
        assert p.returncode == 1, p.stdout[-600:]   # a failing result is data, not a tool failure (wall)
        rep = json.load(io.open(j11, encoding="utf-8"))
        assert rep["mode"]["loop"] is True, rep["mode"]
        assert rep["args"]["state_file"] == "sentinel_state.json", rep["args"]
        rn = red_news(ev1)
        assert len(rn) == 1 and rn[0]["new_red"] == ["B"] \
            and rn[0]["red_total"] == 1 and rn[0]["seen_before"] == 0 \
            and rn[0]["cycle"] == 1, rn
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA and st["red_seen"] == ["B"] \
            and st["repos"] == {} and st["ledgers"] == {} \
            and st["buildlogs"] == {}, st
        # run 2: the failure account {B,C}, B already seen -> red-new only [C] (only-new)
        ev2 = os.path.join(d, "ev2.jsonl")
        p = loop_run(led2, ev2, os.path.join(d, "j11b.json"))
        assert p.returncode == 1, p.stdout[-600:]
        rn = red_news(ev2)
        assert len(rn) == 1 and rn[0]["new_red"] == ["C"] \
            and rn[0]["red_total"] == 2 and rn[0]["seen_before"] == 1, rn
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["red_seen"] == ["B", "C"], st
        # run 3: the failure account {B,C} all seen -> zero red-new events (a repeated failure is not reported again)
        ev3 = os.path.join(d, "ev3.jsonl")
        p = loop_run(led2, ev3, os.path.join(d, "j11c.json"))
        assert p.returncode == 1, p.stdout[-600:]
        assert red_news(ev3) == [], \
            "a repeated failure should produce zero differential events: %s" \
            % red_news(ev3)
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["red_seen"] == ["B", "C"], st
        # a corrupted state rejects with 9 (silent rebuilding forbidden; the original untouched)
        stc = os.path.join(d, "corrupt_state.json")
        corrupt = '{"red_seen": BROKEN{{{'
        with io.open(stc, "w", encoding="utf-8") as fh:
            fh.write(corrupt)
        p = run(["--src", src, "--chain-ledgers", led1, "--state-file", stc,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, \
            "a corrupted state should reject with rc=9, got %d" % p.returncode
        assert "malformed" in p.stdout, p.stdout[-300:]
        assert io.open(stc, encoding="utf-8").read() == corrupt, \
            "the corrupted state was silently rewritten = violation"
        print("v11 the --state-file watch-shaped seen (the differential"
              " only-new triple run / the state continues across processes /"
              " corruption rejects with 9, silent rebuilding forbidden):"
              " PASS")

        # v12 the --rounds/--loop mutual exclusion stated explicitly rc=2 + the
        # --audit/--state-file mutual exclusion + the --probe-parallel<1 usage
        # gate rc=2 (the passthrough parameter defaults to 1; zero drift)
        d, src, world, wd = fixture("v12_mutex")
        p = run(["--src", src, "--loop", "--rounds", "3"])
        assert p.returncode == 2, \
            "--rounds --loop together should rc=2, got %d" % p.returncode
        assert "mutually exclusive" in p.stdout, p.stdout[-300:]
        p = run(["--src", src, "--loop", "--rounds", "0"])
        assert p.returncode == 2, \
            "--rounds 0 with --loop should still rc=2, got %d" % p.returncode
        p = run(["--src", src, "--audit", "--state-file",
                 os.path.join(d, "aud_state.json")])
        assert p.returncode == 2, \
            "--audit --state-file together should rc=2, got %d" % p.returncode
        assert "mutually exclusive" in p.stdout, p.stdout[-300:]
        p = run(["--src", src, "--probe-parallel", "0",
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, \
            "--probe-parallel 0 should rc=2, got %d" % p.returncode
        assert "probe-parallel" in p.stdout, p.stdout[-300:]
        print("v12 the --rounds/--loop mutual exclusion stated explicitly +"
              " the --audit/--state-file mutual exclusion + the"
              " --probe-parallel 0 usage gate (together/out-of-range rc=2):"
              " PASS")

        # v13 the --jobs dimension: the audit timing section records jobs=K
        # (the --probe-parallel argument; the probe_engine --jobs passthrough;
        # default 1); the same candidate face with different K is comparable
        # across runs (the parallel-profile collection point; in injector
        # canned mode the argument is still recorded; zero real compiles)
        d, src, world, wd = fixture("v13_jobs")
        j13a = os.path.join(wd, "report_k1.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]),
                 "--workdir", wd, "--json", j13a])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j13a, encoding="utf-8"))
        assert rep["timing"]["jobs"] == 1 and rep["args"]["probe_parallel"] == 1, \
            (rep["timing"], rep["args"])
        assert "timing: jobs=1" in p.stdout, p.stdout[-300:]
        j13b = os.path.join(wd, "report_k2.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]), "--probe-parallel", "2",
                 "--workdir", wd, "--json", j13b])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j13b, encoding="utf-8"))
        assert rep["timing"]["jobs"] == 2 and rep["args"]["probe_parallel"] == 2, \
            (rep["timing"], rep["args"])
        assert "timing: jobs=2" in p.stdout, p.stdout[-300:]
        print("v13 the --jobs dimension (the audit timing section records"
              " jobs=K; default 1 / K=2 each record their own value;"
              " comparable across runs): PASS")

        print("UNCLOG-SELFTEST PASS: all fourteen vectors pass (the green path/"
              " the honest wall + the no-chain-root supplement / cure-miss /"
              " rounds-exhausted / the default-off proof / JSON idempotence /"
              " the frozen rejection / the loop watch mode / CLI four codes /"
              " the audit read-only baseline with the zero-write self-proof /"
              " the state-file only-new differential / the --rounds--loop"
              " mutual exclusion + the --probe-parallel usage gate + the"
              " --jobs dimension)")
        return 0
    except AssertionError as e:
        print("UNCLOG-SELFTEST FAIL: %s" % e)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
