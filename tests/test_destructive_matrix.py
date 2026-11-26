#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_destructive_matrix.py — cross-tool destructive-surface review matrix,
one refuse-to-write criterion per row (tests/).

Purpose.  Systematic refuse-to-write review of every tool and path that can
  write to disk: the inventory (tool x write face x guard anchor) and one
  asserted refusal criterion per row live in the extended contract comment
  block below and in the ROWS table; a matrix failure means a guard broke,
  and exit 1 lists the broken file:line loudly.
Interface.  Suite case t_destructive_matrix (tests/run_tests.sh) or manual:
  python3 -B tests/test_destructive_matrix.py.  43 rows in ROWS, each
  (row id, tool, criterion, anchor, row function), each row running in its
  own temp dir.
Dependencies.  Python 3 standard library only; the tools under review run
  as python3 -B subprocesses with canned injectors; git only for the
  scratch freeze skeleton (f8_skeleton).
Evidence.  Offline discipline: every criterion runs on tmp fixtures with
  injector canned responses (zero real network, zero real repository,
  zero real compile); the environment is sanitized (ROCWASH_HEADER_MAP /
  ROCWASH_ROCQ / ROCWASH_COQCHK stripped so no caller environment leaks
  into a verdict); output is deterministic (no wall clock, no absolute
  repo paths); any row failure, including an environment exception,
  counts as a broken guard, never silent.
Exit-codes.  0 = all 43 refuse-to-write criteria pass; 1 = at least one
  guard broke (the broken file:line and the violating evidence are
  listed).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).
#
# Systematic refuse-to-write review of every tool and path that can write to
# disk: first the inventory (tool x write face x guard anchor), then one
# asserted refusal criterion per row; a matrix failure means a guard broke,
# and exit 1 lists the broken file:line loudly.
#
# Inventory (tools that write to disk x matrix rows x guard anchors):
#   ① tools/unclog.py (the applying tool; write face = the chain-root file
#      <src>/<root>.v)
#      U1 no --apply writes nothing: the tmp source tree md5 stays constant,
#         no apply ledger, cures_applied=0
#         anchor tools/unclog.py:42 (safety rule: --apply defaults to off = a
#         full dry run writes nothing) + :583/:607 (the cure dry run and the
#         apply are the only two call sites; :607 if a.apply is the master
#         switch)
#      U2 --audit writes nothing and is mutually exclusive with --apply:
#         audit is a read-only baseline (the --src full-file md5s self-attest
#         before and after, :762) and giving both exits rc=2 (:827)
#      U3 frozen refusal: a root name/file hitting the frozen8 roster -> wall
#         frozen-in-service, zero apply
#         anchor tools/unclog.py:506 (pick_root frozen_hit precheck)
#      U4 non-root files are never touched: after --apply the treated root
#         file is canonicalized while every other file's md5 stays constant
#         (the apply target is always the chain-root file; :43-44 "no cure
#         call path outside pick", a structural guarantee)
#   ② tools/wash_shape.py (shape-normalizing tool; write face = the
#      --file/--dir intake set)
#      W1 plan defaults to zero writes: a genuinely dirty file (CRLF plus a
#         banned word) plans would-fix while the tree md5 stays constant
#         anchor tools/wash_shape.py:1254 (one_pass if self.args.apply, the
#         apply master switch)
#      W2 after --apply a partial rescan is never reported as shaped: the
#         apply "succeeds" while the rescan still finds would-fix ->
#         verdict=partial exit 1 (an unclean face is never reported as
#         shaped)
#         anchor tools/wash_shape.py:1192-1205 (verdict_of: an unclean
#         rescan never grants shaped)
#      W3 frozen-name refusal: an explicit --file naming a frozen8 roster
#         member -> rc=2 refusal (refused at intake, zero engine, zero
#         writes; the roster member is only handed over as a path)
#         anchor tools/wash_shape.py:759-761 (collect_files is_forbidden ->
#         UsageError)
#      W4 --header-map and --header-map-preset are same-slot exclusive rc=2
#         anchor tools/wash_shape.py:1887-1890 (the exclusivity preflight in
#         main)
#   ③ tools/pushci.py (push pipeline; write faces = git push / API POST
#      rerun / PR merge)
#      P1 --dry-run zero side effects: both the api_calls and git-caller
#         pipelines stay empty (zero git calls, zero API calls, zero tool
#         subprocesses), all stages empty
#         anchor tools/pushci.py:1163-1164 (run() dry_run -> run_dry
#         short-circuit) + :1116
#      P2 a content red never reruns: family=A-content-red -> fix-content
#         stops, heal.rounds empty = zero-rerun evidence (zero POST on the
#         api pipeline)
#         anchor tools/pushci.py:983-987 (the heal_round A-family
#         no-automatic-repair rule precedes the rerun)
#      P3 the heal cap stops the loop: --max-heal 3 issues exactly 3 POSTs,
#         then heal-exhausted exit 1 (the cap stops it; no fourth issue)
#         anchor tools/pushci.py:966-969 (the stage_watch heal cap gate)
#   ④ tools/cw_sentinel.py (live watcher; write face = the --on-red bypass
#      action subprocess)
#      S1 report-only by default: without --on-red and without
#         --on-red-preset there is zero subprocess action (the actions
#         ledger stays empty; a red is seen and emitted as an event, no
#         action taken)
#         anchor tools/cw_sentinel.py:713-715 (the fire_on_red check sits on
#         sentry["on_red"])
#      S2 both on-red paths share the guard: plain --on-red and
#         --on-red-preset without --emit both rc=2 (a bypass action must be
#         accompanied by an event stream on disk; the trigger evidence and
#         the actions ledger stay auditable; {emit_dir} is derived from
#         --emit and a missing stream is refused) — the v40 matrix
#         registered the gap (the plain path lacked the same guard) and v41
#         closed it
#         anchor tools/cw_sentinel.py:722-723 (expand_on_red_preset) +
#         :884-886 (the build_sentry plain guard)
#   ⑤ tools/registry_union.py (roster union operation tool; write face = the
#      --out union draft)
#      R1 dry run defaults to zero writes: --out given yet nothing lands by
#         default
#         anchor tools/registry_union.py:881-885 (the mode master switch,
#         written only if args.apply)
#      R2 applies only under --apply (plus --apply without --out -> rc=2, no
#         implicit overwrite)
#         anchor tools/registry_union.py:826 + :883-885
#   ⑥ wash/cure_applier.py (canonical-pack applying tool; write face = the
#      --file target)
#      C1 dry run defaults to zero writes: by default only the report is
#         produced, the target file md5 stays constant
#         anchor wash/cure_applier.py:1272/:1338 (if args.apply write gate)
#      C2 applies only under --apply plus the idempotence assertion refuses
#         the write: --apply lands the change and writes only after a second
#         pass with zero residue; a failed idempotence assertion (a custom
#         non-idempotent pack) -> rc=1 file NOT written
#         anchor wash/cure_applier.py:1282-1285 (the IDEMPOTENCE-FAIL
#         refusal)
#      C3 write-face byte contract: after --apply on an LF fixture the on-disk
#         bytes md5 equals the reported md5_after and no \r\n ever lands on
#         disk (io.open newline="" pin; without it Windows text mode wrote
#         CRLF while the report md5 was LF-caliber — the T0-5 md5-caliber
#         defect; second pass must stay byte-identical)
#         anchor wash/cure_applier.py:1338-1341 (pinned write face)
#      C4 compile-leg write face (T0-2/T0-3 S1 sync): the --apply compile
#         leg compiles temp-only copies (.vo never lands in the repo tree);
#         env unset -> honest not-run record with the write proceeding
#         unchanged; env set but binary missing -> rc=9 fail-loud with the
#         file NOT written (never a simulated green)
#         anchor wash/cure_applier.py:660 (compile_leg) + :1286-1336 (the
#         leg master switch) + :1300-1306 (the rc=9 fail-loud face)
#   ⑦ certify/frozen8.py (frozen-roster tool; write faces = the freeze
#      explicit --out/--tier2 pair plus the timestamp explicit --out record
#      path)
#      F1 freeze lands only the explicit two paths, and a ledger-content
#         drift refuses the roster fail-closed (rc=1, zero writes): a scratch
#         git skeleton with the ten frozen files stays tree-md5-constant
#         after freeze; a one-byte tamper of verify_vo.py -> the roster is
#         refused and --out stays zero-byte
#         anchor certify/frozen8.py:357,366 (the two explicit write sites) +
#         :334 (the fail-closed roster refusal)
#      F2 the timestamp's only write face = the explicit --out record,
#         landed only after the binding recheck passes: --out absent rc=2
#         zero-write; TSA unreachable (a closed loopback naming
#         ROCWASH_TSA_URL) rc=9 zero-write — the record lands only after the
#         digest binding recheck passes locally
#         anchor certify/frozen8.py:806 (the only write site, :799-803 the
#         binding gate ahead of it) + :772 (the reachability self-check
#         failure rc=9)
#   ⑧ tools/axiom_guard.py (axiom guard; write face = the caller-named --out
#      report volume plus one private temp workdir path; the .vo output face
#      is temp-only, zero bytes into the repository tree)
#      G1 compile-leg write face temp-only + honest skip: toolchain
#         unconfigured (no env, no flags) -> rc=111 honest skip, zero
#         judgment, the watched scratch tree md5-constant, no --out created;
#         configured binaries missing -> rc=9 fail-loud before any work
#         (zero writes, zero compiles)
#         anchor tools/axiom_guard.py:main env gate (rc 111 / rc 9 ahead of
#         guard()) + :guard private mkdtemp (write faces = workdir and the
#         caller-named --out only)
#   ⑨ tools/jargon_apply.py (wash-map applier; write face = the .py/.sh/.md
#      prose faces under --tree, or the one --file target)
#      J1 self-reference guard: the wash map's own source table
#         (--a2-table, default docs/jargon-to-standard-mapping-v1.md) is never
#         a wash target — --tree excludes it from the target set and --file on
#         it is refused rc=1 loud (a tool never washes its own map; the
#         e04f2f6 round washed it and stripped 11 of the 13 contract rows the
#         seed pins by md5)
#         anchor tools/jargon_apply.py:550-560 (skip_abs self-reference
#         exclusion) + :471-484 (--file refusal)
#   ⑩ tools/scheduler_lite.py (lite scheduler, X2 face; write face = the
#      explicit --out path only)
#      SL1 plan defaults to zero writes: with all flags canned on tmp
#         fixtures, plan produces a due verdict while the tmp tree md5 stays
#         constant; without --out nothing lands at all (dryRun=true stays
#         pinned)
#         anchor tools/scheduler_lite.py:474-476 (run_plan if args.out, the
#         only write gate) + :404 (build_plan dryRun=True always)
#      SL2 the only write face = the explicit --out, byte-deterministic: with
#         --out exactly one file lands (the plan document), the input tree
#         md5 stays constant, two runs are byte-identical (the plan_bytes
#         sort_keys deterministic byte form)
#         anchor tools/scheduler_lite.py:474-476 + :424-427 (plan_bytes
#         deterministic bytes)
#   ⑪ tools/auto_merge.py (automatic merge gate, X5 face; write face = the
#      --apply merge-ledger append path only)
#      AM1 no --apply writes nothing: merge-ok plus a supply/* whitelist
#         member (the rail rules allowed) yet the ledger is not written and
#         not created (a report --json is an explicit extra)
#         anchor tools/auto_merge.py:244-247 (run_rail if apply_mode append
#         master switch)
#      AM2 hold never authorizes plus out-of-scope branch refusal: a hold-red
#         verdict writes nothing even under --apply (rail not-eligible
#         precedes the merge ledger); a non-supply/* head rc=1 whitelist
#         refusal with zero writes
#         anchor tools/auto_merge.py:220-221 (verdict != merge-ok
#         precondition) + :225-228 (the branch whitelist gate)
#      AM3 daily budget cap plus duplicate refusal: --daily-cap 3 authorizes
#         exactly 3 rows, the 4th is refused rc=1; a same-day same-PR
#         duplicate is refused rc=1; the merge ledger stays at exactly 3
#         rows
#         anchor tools/auto_merge.py:229-233 (the daily cap gate) + :234-239
#         (the duplicate gate)
#   ⑫ tools/repair_scope.py (shared exclusion roster, F1/E2 single source)
#      plus the four E2 guard classes
#      RS1 the --check query face writes nothing and the exclusion
#         conclusions bite: shared full_frozen_files (read from the running
#         LEDGER8 AST, a missing file degrades to a loud snapshot) +
#         FROZEN_DIR_FAMILIES + LEGAL_DATA_DIR_FAMILIES + docs/zh + .zh.md
#         archive mirrors all EXCLUDED; the three class-2 repairable faces
#         (tests/README.md, README.md, the ledger) REPAIRABLE; the query
#         writes nothing
#         anchor tools/repair_scope.py:140-160
#         (exclusion_roster/full_frozen_files) + :556-576
#         (RosterResyncScope.refusal_reason) + :590-620 (check_faces)
#      E2A class-1 lane-extract (--lane-detect/--lane-apply): default
#         zero-write zero-record; an excluded ledger face (the seeds/
#         family) rc=2 refusal with zero creation; the budget cap (2 prior
#         records) rc=2 write refusal, suite bytes constant, only an
#         escalated(budget-cap) ledger row lands
#         anchor tools/repair_scope.py:477-482 (excluded-face refusal) +
#         :400-411 (_lane_ledger_gate, the ledger face under the same gate)
#         + :487-493 (the budget cap)
#      E2B class-2 roster-resync (tools/roster_resync.py): default zero-write
#         zero-record; --apply is a one-way derivation (roster bytes
#         constant, count faces repaired to the roster value, one repair one
#         ledger row); budget cap rc=1 write refusal, face bytes constant,
#         only an escalated row lands
#         anchor tools/roster_resync.py:246-248 (the default zero-write
#         gate) + :256-265 (the budget cap) + :327-334 (a frozen face is
#         escalated, never applied) + tools/repair_scope.py:556-576
#      E2C class-3 flaky-quarantine (tools/flaky_guard.py --move): a frozen
#         target (a seeds/-family roster) rc=1 refusal with zero writes and
#         zero records (the scope check precedes the probe); budget cap rc=1
#         write refusal, roster bytes constant, only an escalated ledger row
#         lands
#         anchor tools/flaky_guard.py:390-396 (_scope_check single-source
#         consumption, ahead of every plan) + :514-523 (the budget cap)
#      E2D class-4 doc-count (--doc-count-detect/--doc-count-apply): default
#         zero-write zero-record; --apply repairs to face=source and is
#         idempotent (a second pass moves zero bytes); budget cap rc=2 write
#         refusal, target-face bytes constant, only an escalated(budget-cap)
#         row lands
#         anchor tools/repair_scope.py:917-926 (the apply write-face
#         precheck) + :975-994 (the budget cap) + :997-1009 (the
#         post-assertion refusal)
#   ⑩ .github/scripts/selfheal_heartbeat.py (heartbeat tick writer; write face
#      = the caller-named --file JSONL volume, strictly append-only)
#      H1 default dry run zero-write; --apply appends exactly one tick line
#         per run and prior ledger bytes stay byte-identical (content pins,
#         never mtime pins: back-to-back writes can land on one mtime tick)
#         anchor .github/scripts/selfheal_heartbeat.py (run gate + append face)
#      H2 loss-of-contact rule: a gap strictly over 90 minutes appends an ALERT
#         line ahead of the tick; exactly 90 minutes stays silent; an ALERT
#         line is never a tick source
#         anchor .github/scripts/selfheal_heartbeat.py (planned_records gap gate)
#      H3 fail-loud: a corrupt or schema-mismatched last ledger line refuses
#         the append with rc=9 and zero bytes written; bad --now, nonpositive
#         --alert-minutes and an empty --file are usage errors rc=2
#         anchor .github/scripts/selfheal_heartbeat.py (last_tick raises + run
#         validation)
#      H4 yml wiring line-scan (stdlib only, no YAML parser dependency): the
#         heartbeat input defaults to false, HEARTBEAT=1 is exported only
#         under workflow_dispatch, the step invokes the writer with --apply
#         against docs/heartbeat.jsonl, checkout covers HEARTBEAT, the
#         rollback line names the new script
#         anchor .github/workflows/selfheal.yml (input block, guard block,
#         heartbeat step, checkout condition, rollback line)
#   ⑪ tools/repair_weekly.py (repair-outcome weekly distribution face; write
#      faces = the caller-named --out markdown face + --json report + the
#      ledger append through --record --apply; the aggregate face is
#      read-only over the ledger)
#      K1 aggregate write face: dry-run default zero-write (no --out ->
#         stdout only, tree manifest constant); with --out the face file is
#         the only write and reruns are byte-identical; the ledger input
#         never gains a byte
#         anchor tools/repair_weekly.py:main aggregate branch +
#         :render_markdown caller-named write face
#      K2 record write face: --record without --apply is plan-only (zero
#         bytes); --record --apply appends exactly one
#         rocqwash-repair-ledger/2 row; the vocabulary refusals (escalated
#         without an evidence package, a watch-only reason outside the enum,
#         a value outside the vocabulary) refuse before any byte moves
#         anchor tools/repair_weekly.py:record_row (vocabulary gate) +
#         :ledger_append (the only append face)
#      K3 fail-loud input faces: a malformed ledger row rc=2 and an
#         explicitly named absent ledger rc=9, both with zero writes
#         anchor tools/repair_weekly.py:ledger_rows (fail-loud parse) +
#         :main explicit-ledger gate
#   ⑫ wording-face honesty rows (honest-degradation wording alignment; read-only
#      line-scans: zero writes, zero subprocesses, zero tmp fixtures)
#      N1 README evolve wording alignment: the v55 snapshot line states the
#         tool in substance as a signal-to-task-brief generator, the
#         "autonomous evolution engine" label survives only as the cited
#         module-title face pending rename adjudication, and the draft-only
#         spawn-gate fact tokens stay on the line
#         anchor README.md:19 (v55 snapshot line)
#      N2 evolve.py docstring honesty note: the Purpose block carries the
#         draft-only token and the selection-not-implemented-in-this-code
#         clause while keeping the no-execution and no-repository-write
#         facts, the module title keeps its name, and the five-field doc
#         block stays within the 30-line budget
#         anchor tools/evolve.py:13-14 (docstring Purpose note lines)
#      N3 CAPABILITY-INDEX evolution_dashboard positioning note: the entry
#         carries the KPI-aggregation positioning line, the rename candidate
#         is declared but not applied, and the entry name, path, invocation
#         form, and route tokens stay untouched
#         anchor docs/CAPABILITY-INDEX.md:209 (evolution_dashboard note line)
#
# Offline discipline (hard requirement): every criterion runs on tmp fixtures
# with --injector canned responses (unclog probe/resprobe canned, wash_shape
# engine keys canned, pushci steps/jobs/git-caller canned, sentinel canned
# API) — zero real network, zero real repository, zero real compile; the only
# real subprocesses are pure-stdlib offline engines (chain_graph,
# cure_applier, scan_v4_token, frozen8 --ledger/--selftest, freeze on a
# scratch skeleton, gate4, ci_triage --offline, selfheal_heartbeat --apply;
# precedent: each tool's own --selftest; the E2C budget-cap face drives a
# three-line bash fixture suite inside tmp through the flaky_guard probe,
# same as the flaky_guard --selftest precedent).  The single exception W3
# hands over a real roster member's PATH only: the tool refuses at
# collect_files, zero reads zero writes (the wash_shape same-tool
# precedent).
#
# Self discipline: python3 -B bans __pycache__; zero repository writes (every
# artifact lives in tempfile.mkdtemp); deterministic output (no wall clock,
# no absolute repo paths); environment sanitation (ROCWASH_HEADER_MAP /
# ROCWASH_ROCQ / ROCWASH_COQCHK stripped, so no caller environment leaks into
# a verdict and no real compile leaks into the matrix); fail-loud — any row
# failure (including an environment exception) counts as broken, never
# silent.
#
# Usage:
#   python3 tests/test_destructive_matrix.py          # via run_tests.sh in the suite
#   python3 -B tests/test_destructive_matrix.py       # manual
import json
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNCLOG = os.path.join(REPO, "tools", "unclog.py")
WASH_SHAPE = os.path.join(REPO, "tools", "wash_shape.py")
PUSHCI = os.path.join(REPO, "tools", "pushci.py")
SENTINEL = os.path.join(REPO, "tools", "cw_sentinel.py")
REGISTRY_UNION = os.path.join(REPO, "tools", "registry_union.py")
CURE_APPLIER = os.path.join(REPO, "wash", "cure_applier.py")
AXIOM_GUARD = os.path.join(REPO, "tools", "axiom_guard.py")
FROZEN8 = os.path.join(REPO, "certify", "frozen8.py")
JARGON_APPLY = os.path.join(REPO, "tools", "jargon_apply.py")
SCHEDULER_LITE = os.path.join(REPO, "tools", "scheduler_lite.py")
AUTO_MERGE = os.path.join(REPO, "tools", "auto_merge.py")
REPAIR_SCOPE = os.path.join(REPO, "tools", "repair_scope.py")
ROSTER_RESYNC = os.path.join(REPO, "tools", "roster_resync.py")
FLAKY_GUARD = os.path.join(REPO, "tools", "flaky_guard.py")
SELFHEAL_HEARTBEAT = os.path.join(REPO, ".github", "scripts",
                                  "selfheal_heartbeat.py")
SELFHEAL_YML = os.path.join(REPO, ".github", "workflows", "selfheal.yml")
REPAIR_WEEKLY = os.path.join(REPO, "tools", "repair_weekly.py")
JOBS_A = os.path.join(REPO, "tests", "fixtures", "ci_triage_A_content_red.json")
JOBS_B = os.path.join(REPO, "tests", "fixtures", "ci_triage_B_netred.json")

SCHEMA_UNCLOG = "rocqwash-unclog/1"


# ---- small pieces ---------------------------------------------------------------------

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_manifest(root, skip_dirs=(".git",)):
    """{rel(POSIX): md5} manifest of every file under the directory (one
    byte added, removed or changed shows up; same accounting as unclog).

    The .git directory is skipped by default: git legitimately rewrites its
    own metadata (reflog, index, gc.log) when it resolves HEAD or refreshes
    the index, and counting those bytes turns the tool's write-face judgment
    into a statement about git's internal bookkeeping. The rows that guard
    git-object writes assert on the object store explicitly, not on the
    surrounding metadata.
    """
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            out[os.path.relpath(fp, root).replace(os.sep, "/")] = md5_of(fp)
    return out


def sh(tool_abs, argv, env_extra=None):
    """python3 -B <tool> subprocess (stdout+stderr merged; environment
    sanitation strips ROCWASH_HEADER_MAP/ROCWASH_ROCQ/ROCWASH_COQCHK so no
    caller environment leaks into a verdict and no real compile leaks into
    the offline matrix).  env_extra is the explicit injection face for the
    configured-but-missing fail-loud rows only (it can never launch a real
    compile: the missing binary check precedes every work face)."""
    env = dict(os.environ)
    env.pop("ROCWASH_HEADER_MAP", None)
    env.pop("ROCWASH_ROCQ", None)
    env.pop("ROCWASH_COQCHK", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-B", tool_abs] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def wf(path, text, newline="\n"):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)
    return path


def wj(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, sort_keys=True)
    return path


def jl(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---- unclog injector fixtures (probe/resprobe canned ledger; same shape as unclog --selftest) ----

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")


def u_led(records):
    return {"schema": "rocqwash-probe-ledger/1", "n_records": len(records),
            "records": records}


def u_rec0(f):
    return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
            "red_class": None, "verdict": "RC0", "red_count": None,
            "md5_match": None}


def u_rec1(f, lib):
    return {"file": f, "md5": None, "rc": 1,
            "red": "Error: Unable to locate library | %s (while searching "
                   "for a .vos file)." % lib,
            "missing": lib, "red_class": "MISSING_LIB",
            "verdict": "RED-MISSING_LIB", "red_count": None, "md5_match": None}


def u_fixture(tmp, tag, extra_v=None):
    """unclog tmp fixture: a src tree (A, a sanitizable chain root, plus B,
    its consumer, and any extra files) with cands.tsv and the injector
    directory skeleton.  -> (src, cands, wd, injdir)."""
    d = os.path.join(tmp, tag)
    src, wd, injdir = (os.path.join(d, x) for x in ("src", "wd", "inj"))
    for p in (src, wd, injdir):
        os.makedirs(p)
    wf(os.path.join(src, "A.v"), CURE13_BODY)
    wf(os.path.join(src, "B.v"), "Require Import A.\n")
    for name, body in (extra_v or []):
        wf(os.path.join(src, name), body)
    cands = wf(os.path.join(d, "cands.tsv"), "件名\tmd5\n")
    for dirpath, _dirs, filenames in os.walk(src):
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                rel = os.path.relpath(os.path.join(dirpath, fn), src)[:-2]
                with io.open(cands, "a", encoding="utf-8", newline="\n") as fh:
                    fh.write("%s\t%s\n" % (rel.replace(os.sep, "/"),
                                           md5_of(os.path.join(dirpath, fn))))
    return src, cands, wd, injdir


def u_scenario(injdir, probes, resprobes=None):
    scen = {"probe": probes}
    if resprobes is not None:
        scen["resprobe"] = resprobes
    wj(os.path.join(injdir, "scenario.json"), scen)
    return injdir


L1 = None    # module-level lazy build (a dict is unhashable as a default
             # argument); assigned before rows() runs


# ---- ① unclog, four rows ------------------------------------------------------------

def row_u1(tmp):
    """Without --apply nothing is written: a plan exists (cures_planned=1)
    while the tmp source tree md5 stays constant, and no apply ledger
    lands."""
    src, cands, wd, injdir = u_fixture(tmp, "u1")
    u_scenario(injdir, [L1, L1], [u_led({"A": u_rec0("A")})])
    before = tree_manifest(src)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--rounds", "1",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 1, "without --apply expected rounds-exhausted rc=1, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["schema"] == SCHEMA_UNCLOG and rep["verdict"] == "rounds-exhausted"
    assert rep["mode"]["apply"] is False, rep["mode"]
    assert rep["final"]["cures_planned_total"] == 1, "a dry run should still produce a plan"
    assert rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert tree_manifest(src) == before, "source tree bytes moved without --apply = guard broken"
    assert not os.path.exists(os.path.join(wd, "round-1.apply.json")), \
        "no apply ledger may land without --apply"


def row_u2(tmp):
    """--audit writes nothing and is mutually exclusive with --apply: audit
    is a read-only baseline (cures stay empty, tree constant);
    --audit --apply given together exits rc=2."""
    src, cands, wd, injdir = u_fixture(tmp, "u2")
    u_scenario(injdir, [L1])
    before = tree_manifest(src)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--audit",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 0, "read-only audit baseline should exit 0, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "audit" and rep["mode"]["audit"] is True
    assert rep["final"]["cures_planned_total"] == 0 \
        and rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert rep["rounds"][0]["cure"] is None, "audit must carry no apply verdict"
    assert tree_manifest(src) == before, "source tree bytes moved under audit = guard broken"
    rc2, out2 = sh(UNCLOG, ["--src", src, "--candidates", cands, "--audit",
                            "--apply"])
    assert rc2 == 2, "--audit --apply given together should rc=2, got %d\n%s" % (rc2, out2[-300:])
    assert "mutually exclusive" in out2, out2[-300:]  # synced to the translated unclog mutex message


def row_u3(tmp):
    """frozen refusal: the root name wash_engine hits the frozen8 roster
    (certify/frozen8.py --ledger reads the real roster) -> wall
    frozen-in-service, zero apply, and the roster-named fixture file stays
    byte-identical."""
    src, cands, wd, injdir = u_fixture(
        tmp, "u3", extra_v=[("wash_engine.v", CURE13_BODY)])
    LF = u_led({"wash_engine": u_rec0("wash_engine"),
                "D": u_rec1("D", "wash_engine")})
    u_scenario(injdir, [LF])
    frozen_v = os.path.join(src, "wash_engine.v")
    before = md5_of(frozen_v)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--apply",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 1, "a frozen refusal should wall rc=1, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "wall", rep["verdict"]
    assert rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", rep["wall"]
    assert rep["rounds"][0]["cure"] is None, "no apply verdict may follow a frozen refusal"
    assert rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert md5_of(frozen_v) == before, "the roster-named file was applied to = guard broken"


def row_u4(tmp):
    """Non-root files are never touched: under --apply the treated root file
    A.v is canonicalized while the consumer B.v md5 stays constant (the
    apply target is always the chain-root file; no cure call path exists
    outside pick)."""
    src, cands, wd, injdir = u_fixture(tmp, "u4")
    u_scenario(injdir, [L1, u_led({"A": u_rec0("A"), "B": u_rec0("B")})],
               [u_led({"A": u_rec0("A")})])
    b_before = md5_of(os.path.join(src, "B.v"))
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--apply",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 0, "the green-path apply should unclogged rc=0, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "unclogged"
    assert rep["final"]["cures_applied_total"] == 1, rep["final"]
    a_text = io.open(os.path.join(src, "A.v"), encoding="utf-8").read()
    assert "S01_BaseRing.NatLe (gnPrf f pf) k" in a_text, "the chain-root file was not canonicalized"
    assert rep["rounds"][0]["cure"]["on_disk_md5_match"] is True, rep["rounds"][0]
    assert md5_of(os.path.join(src, "B.v")) == b_before, \
        "a non-root file moved = guard broken (apply face out of bounds)"


# ---- ② wash_shape, four rows --------------------------------------------------------

SHAPE_HEADER = ("(* 使命：破坏面矩阵夹具。\n"
                "   依赖：无。\n"
                "   对标：无。\n"
                "   构造性：全闭合。\n"
                "   编译配方：rocq c -Q . \"\" fixture.v。 *)\n")


def row_w1(tmp):
    """plan defaults to zero writes: a genuinely dirty file (CRLF plus a
    banned-word carrier, a real gate4 verdict) plans would-fix >= 1 (a
    sanitizable face is seen) while the tree md5 stays constant."""
    d = os.path.join(tmp, "w1")
    tree, outd = os.path.join(d, "tree"), os.path.join(d, "out")
    os.makedirs(tree)
    os.makedirs(outd)
    dirty = wf(os.path.join(tree, "dirty.v"),
               (SHAPE_HEADER + "Definition a := 1. (* 这里埋一个载体词 *)\n"
                                "Definition b := 2.\n").replace("\n", "\r\n"),
               newline="")
    before = tree_manifest(tree)
    rc, out = sh(WASH_SHAPE, ["--file", dirty, "--json",
                              os.path.join(outd, "rep.json")])
    assert rc == 1, "the dirty-file plan should partial rc=1, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(outd, "rep.json"))
    assert rep["schema"] == "rocqwash-shape/1"
    assert rep["mode"] == "plan", rep["mode"]
    assert rep["verdict"] == "partial", rep["verdict"]
    assert rep["plan"]["stats"]["would_fix"] >= 1, "plan should see the sanitizable face"
    assert tree_manifest(tree) == before, "tree bytes moved under the default plan = guard broken"
    assert not os.path.exists(os.path.join(tree, ".wash_shape_json_0")), \
        "plan left a residue file on the intake face = guard broken"


def row_w2(tmp):
    """After --apply a partial rescan is never reported as shaped: gate4/
    sweep canned, the apply record succeeds while the rescan still finds
    would-fix -> verdict=partial exit 1 (verdict_of never grants shaped
    when the rescan is not clean)."""
    d = os.path.join(tmp, "w2")
    outd = os.path.join(d, "out")
    os.makedirs(outd)
    dirty = wf(os.path.join(d, "dirty2.v"), "Definition x := 1.\n")
    inj = wj(os.path.join(d, "inj.json"), {
        "gate4": {"rc": 1, "stdout": "canned-gate4", "report": {"results": [
            {"file": dirty, "verdict": "FAIL",
             "hard": [[6, "体内散块", "禁词", "载体"]], "review": []}]}},
        "scan_v4": {"rc": 0, "stdout": "canned-scan",
                    "report": {"station_count": 0, "tracked_ids": []}},
        "sweep": {"rc": 0, "stdout": "canned-sweep",
                  "report": {"report": {"flag_swaps": 1}}}})
    rc, out = sh(WASH_SHAPE, ["--file", dirty, "--apply", "--injector", inj,
                              "--json", os.path.join(outd, "rep.json")])
    assert rc == 1, "an unclean rescan should partial rc=1, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(outd, "rep.json"))
    assert rep["verdict"] == "partial", \
        "an unclean rescan reported as shaped = guard broken, got %r" % rep["verdict"]
    assert rep["apply"]["rescan"]["stats"]["would_fix"] == 1, rep["apply"]
    assert "RESCAN: would_fix=1" in out, out[-400:]


def row_w3(tmp):
    """Frozen-name refusal: an explicit --file naming a real frozen8 roster
    member (verify/gate4_comment_guard.py; the roster premise is asserted
    first) -> rc=2 refusal at intake, zero engine (the roster member is
    only handed over as a path, its content is never touched)."""
    rc, out = sh(FROZEN8, ["--ledger"])
    assert rc == 0, "frozen8 --ledger should rc=0 (the refusal premise, offline ledger)"
    roster = [ln.split()[1] for ln in out.splitlines()
              if len(ln.split()) == 2]
    target = os.path.join(REPO, "verify", "gate4_comment_guard.py")
    assert "verify/gate4_comment_guard.py" in roster, \
        "refusal premise broken: the target file is not on the frozen8 roster: %s" % roster
    rc, out = sh(WASH_SHAPE, ["--file", target, "--only", "eol"])
    assert rc == 2, "an explicitly named frozen file should be refused rc=2, got %d\n%s" % (rc, out[-400:])
    assert "rejection" in out, out[-300:]  # synced to the translated wash_shape frozen-surface rejection message


def row_w4(tmp):
    """--header-map and --header-map-preset are same-slot exclusive rc=2
    (the preflight check sits ahead of engine loading in main)."""
    d = os.path.join(tmp, "w4")
    os.makedirs(d)
    clean = wf(os.path.join(d, "clean.v"),
               SHAPE_HEADER + "Definition a := 1.\n")
    mp = wj(os.path.join(d, "map.json"), {})
    rc, out = sh(WASH_SHAPE, ["--file", clean, "--header-map", mp,
                              "--header-map-preset", "campaign_set_diamond"])
    assert rc == 2, "same-slot double flags should rc=2, got %d\n%s" % (rc, out[-400:])
    assert "same-slot" in out, out[-300:]  # synced to the translated wash_shape same-slot exclusivity message


# ---- ③ pushci, three rows ------------------------------------------------------------

SHA40 = "5f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6"
RUN_ID = 9026111201


def p_runs_body(conclusion):
    return {"total_count": 1, "workflow_runs": [
        {"id": RUN_ID, "run_number": 7, "name": "ci", "head_branch": "work",
         "head_sha": SHA40, "status": "completed", "conclusion": conclusion,
         "html_url": "https://github.com/org/repo/actions/runs/%d" % RUN_ID}]}


def p_setup(tmp, tag, api_steps, jobs=None, tools=None):
    """pushci injection setting with the steps form plus the git-caller
    form (the real call order get-url -> rev-parse -> push -> ls-remote).
    -> (repo, injdir, gitjson, api_calls_path, git_calls_path)."""
    d = os.path.join(tmp, tag)
    repo, injdir = os.path.join(d, "repo"), os.path.join(d, "inj")
    os.makedirs(repo)
    os.makedirs(injdir)
    scen = {"steps": api_steps,
            "tools": tools or {"toolchain_dyld_doctor": {"rc": 0,
                                                         "verdict": "healthy"},
                               "net_probe": {"rc": 0, "verdict": "STABLE"}}}
    if jobs is not None:
        scen["jobs"] = jobs
    wj(os.path.join(injdir, "scenario.json"), scen)
    gitjson = wj(os.path.join(d, "git.json"), {"responses": [
        {"args_contains": ["get-url"], "rc": 0,
         "stdout": "https://github.com/org/repo.git\n"},
        {"args_contains": ["rev-parse"], "rc": 0, "stdout": SHA40 + "\n"},
        {"args_contains": ["push"], "rc": 0,
         "stdout": "To https://github.com/org/repo.git\n"},
        {"args_contains": ["ls-remote"], "rc": 0,
         "stdout": "%s\trefs/heads/work\n" % SHA40}]})
    return repo, injdir, gitjson, os.path.join(injdir, "api_calls.json"), \
        os.path.join(d, "git.calls.json")


def p_fire(repo, injdir, gitjson, extra):
    env = dict(os.environ)
    env.pop("ROCWASH_MASK", None)
    cmd = [sys.executable, "-B", PUSHCI, "--repo-path", repo,
           "--branch", "work", "--remote", "origin", "--injector", injdir,
           "--git-caller", gitjson,
           "--netrc", os.path.join(tempfile.gettempdir(),
                                   "dm_no_such_netrc_parity"),
           "--sleep-scale", "0"] + list(extra)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def row_p1(tmp):
    """--dry-run has zero side effects: rc=0 verdict=dry-run, stages all
    empty, and both the api_calls and git-caller pipelines empty (zero git
    calls, zero API calls, zero tool subprocesses)."""
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p1", [])
    rep_path = os.path.join(tmp, "p1", "out.json")
    rc, out = p_fire(repo, injdir, gitjson,
                     ["--dry-run", "--pre-scan-gate4", "--json", rep_path])
    assert rc == 0, "a dry run should exit 0, got %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "dry-run" and rep["mode"] == "dry-run", rep["verdict"]
    assert rep["stages"] == {}, "a dry run must carry no stage execution record: %s" % list(rep["stages"])
    assert rep.get("plan"), "a dry run should produce a plan"
    assert os.path.isfile(api_calls) and os.path.isfile(git_calls), \
        "both pipeline record files must exist (the injection-mode evidence face)"
    assert jl(api_calls) == [], "dry-run zero-API-call evidence lost = guard broken"
    assert jl(git_calls) == [], "dry-run zero-git-call evidence lost = guard broken"


def row_p2(tmp):
    """A content red never reruns: family=A-content-red -> fix-content
    exit 2, heal.rounds empty = zero-rerun evidence (zero POST on the api
    pipeline); the evidence carries the no-automatic-repair clause."""
    jobs_a = jl(JOBS_A)
    steps = [{"at_round": 1, "responses": [
        {"method": "GET", "path": "/actions/runs?per_page=30", "status": 200,
         "body": p_runs_body("failure")}]}]
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p2", steps,
                                                          jobs=jobs_a)
    rep_path = os.path.join(tmp, "p2", "out.json")
    rc, out = p_fire(repo, injdir, gitjson, ["--json", rep_path])
    assert rc == 2, "a content red should fix-content exit 2, got %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "fix-content", rep["verdict"]
    h = rep["stages"]["heal"]
    assert h["rounds"] == [] and h["fired_total"] == 0, \
        "content-red zero-rerun evidence lost = guard broken: %r" % h
    assert h["last_triage"]["family"] == "A-content-red", h["last_triage"]
    calls = jl(api_calls)
    assert all(c["method"] != "POST" for c in calls), \
        "a POST rerun under a content red = guard broken: %r" % calls
    assert any("no automatic repair" in e for e in rep["evidence"]), rep["evidence"]


def row_p3(tmp):
    """The heal cap stops the loop: --max-heal 3 with four NETRED failure
    rounds issues exactly 3 POST reruns, then heal-exhausted exit 1 (the
    cap stops it; no fourth issue)."""
    jobs_b = jl(JOBS_B)
    steps = []
    for i in range(1, 5):
        resps = [{"method": "GET", "path": "/actions/runs?per_page=30",
                  "status": 200, "body": p_runs_body("failure")}]
        if i <= 3:
            resps.append({"method": "POST", "path": "/rerun", "status": 201,
                          "body": {}})
        steps.append({"at_round": i, "responses": resps})
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p3", steps,
                                                          jobs=jobs_b)
    rep_path = os.path.join(tmp, "p3", "out.json")
    rc, out = p_fire(repo, injdir, gitjson,
                     ["--max-heal", "3", "--json", rep_path])
    assert rc == 1, "an exhausted heal cap should heal-exhausted exit 1, got %d\n%s" \
        % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "heal-exhausted", rep["verdict"]
    h = rep["stages"]["heal"]
    assert len(h["rounds"]) == 3 and h["fired_total"] == 3, h
    calls = jl(api_calls)
    n_post = sum(1 for c in calls if c["method"] == "POST")
    n_get = sum(1 for c in calls if c["method"] == "GET")
    assert n_post == 3, "cap 3 must issue exactly 3 reruns (more or fewer is broken), got %d" % n_post
    assert n_get == 4, "four poll rounds should be 4 GETs, got %d" % n_get


# ---- ④ cw_sentinel, two rows -------------------------------------------------------

def s_canned(tmp, tag):
    """Sentinel canned API (runs red record 178 plus a jobs A-form red
    step) -> injector path."""
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    runs_body = {"total_count": 1, "workflow_runs": [
        {"id": 178, "name": "CI", "run_number": 9, "status": "completed",
         "conclusion": "failure", "head_branch": "main",
         "head_sha": "abc123def",
         "html_url": "https://github.com/org/repo/actions/runs/178"}]}
    jobs_body = {"total_count": 1, "jobs": [
        {"id": 501, "name": "build", "status": "completed",
         "conclusion": "failure", "started_at": "2026-11-10T08:00:00Z",
         "completed_at": "2026-11-10T08:01:00Z",
         "steps": [{"number": 1, "name": "Build (coqc batch)",
                    "status": "completed", "conclusion": "failure",
                    "started_at": "2026-11-10T08:00:01Z",
                    "completed_at": "2026-11-10T08:00:30Z"}]}]}
    return wj(os.path.join(d, "injector.json"), {
        "schema": "rocqwash-sentinel-injector/1", "responses": [
            {"url_contains": "/actions/runs?", "status": 200,
             "body": runs_body},
            {"url_contains": "/runs/178/jobs", "status": 200,
             "body": jobs_body}]})


def row_s1(tmp):
    """report-only by default: with neither --on-red nor --on-red-preset
    there is zero subprocess action; a CI red record emits a ci-red event
    (the red is seen) while the actions ledger stays empty (no action is
    taken)."""
    inj = s_canned(tmp, "s1")
    d = os.path.join(tmp, "s1")
    state = os.path.join(d, "state.json")
    emit = os.path.join(d, "events.jsonl")
    rep_path = os.path.join(d, "rep.json")
    rc, out = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                            "--injector", inj, "--state-file", state,
                            "--emit", emit, "--json", rep_path,
                            "--sleep-scale", "0"])
    assert rc == 0, "a report-only watch should exit 0, got %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["schema"] == "rocqwash-sentinel/1"
    evs = [json.loads(ln) for ln in io.open(emit, encoding="utf-8")
           if ln.strip()]
    assert any(e["kind"] == "ci-red" for e in evs), \
        "the red must be seen as an event (ci-red on the stream): %r" % evs
    assert rep["actions"] == [], \
        "an actions record under default report-only = guard broken (zero-subprocess-action lost): %r" \
        % rep["actions"]
    assert "on-red" not in out.replace("on-red-preset", ""), out[-300:]


def row_s2(tmp):
    """Both on-red paths carry the same guard: plain --on-red and
    --on-red-preset without --emit both exit rc=2 (a bypass action must be
    accompanied by an event stream on disk; the trigger evidence and the
    actions ledger stay auditable; {emit_dir} is derived from --emit and a
    missing stream is refused).  The v40 matrix registered the gap (the
    plain path lacked the same guard) and v41 closed it; the check sits
    ahead of build_sentry, zero watch and zero action."""
    rc, out = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                            "--on-red", "echo x", "--sleep-scale", "0"])
    assert rc == 2, "plain without --emit should rc=2, got %d\n%s" % (rc, out[-400:])
    assert "--emit" in out, out[-300:]
    rc2, out2 = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                              "--on-red-preset", "unclog",
                              "--on-red-arg", "src=" + os.path.join(tmp, "s2"),
                              "--sleep-scale", "0"])
    assert rc2 == 2, "preset without --emit should rc=2, got %d\n%s" % (rc2, out2[-400:])
    assert "--emit" in out2, out2[-300:]


# ---- ⑤ registry_union / cure_applier, five rows --------------------------------------

def r_fixture(tmp, tag):
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    base = wf(os.path.join(d, "base.txt"), "A.v\nB.v\n")
    main = wf(os.path.join(d, "main.txt"), "A.v\nB.v\n")
    branch = wf(os.path.join(d, "branch.txt"), "A.v\nB.v\nC.v\n")
    return d, base, main, branch


def row_r1(tmp):
    """registry_union dry run defaults to zero writes: --out is given yet
    nothing lands by default."""
    d, base, main, branch = r_fixture(tmp, "r1")
    outp = os.path.join(d, "union.txt")
    rep = os.path.join(d, "rep.json")
    rc, out = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                  "--branch", branch, "--kind", "order",
                                  "--out", outp, "--json", rep])
    assert rc == 0, "a dry run should exit 0, got %d\n%s" % (rc, out[-400:])
    assert not os.path.exists(outp), \
        "--out landed without --apply = guard broken (dry-run zero-write lost)"
    assert "DRY-RUN" in out, out[-300:]


def row_r2(tmp):
    """registry_union applies only under --apply: after --apply the --out
    file exists with the union rows; --apply without --out exits rc=2 (no
    implicit overwrite)."""
    d, base, main, branch = r_fixture(tmp, "r2")
    outp = os.path.join(d, "union.txt")
    rc, out = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                  "--branch", branch, "--kind", "order",
                                  "--out", outp, "--apply"])
    assert rc == 0, "--apply should exit 0, got %d\n%s" % (rc, out[-400:])
    assert os.path.isfile(outp), "--out did not land after --apply = guard broken"
    assert io.open(outp, encoding="utf-8").read() == "A.v\nB.v\nC.v\n", \
        "unexpected union file content: %r" % io.open(outp, encoding="utf-8").read()
    rc2, out2 = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                    "--branch", branch, "--kind", "order",
                                    "--apply"])
    assert rc2 == 2, "--apply without --out should rc=2, got %d\n%s" % (rc2, out2[-300:])
    assert "须配 --out" in out2, out2[-300:]


def row_c1(tmp):
    """cure_applier dry run defaults to zero writes: by default (no
    --apply) only the report is produced and the target file md5 stays
    constant."""
    d = os.path.join(tmp, "c1")
    os.makedirs(d)
    f = wf(os.path.join(d, "t.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    before = md5_of(f)
    rc, out = sh(CURE_APPLIER, ["--file", f, "--json", rep])
    assert rc == 0, "a dry run should exit 0, got %d\n%s" % (rc, out[-400:])
    r = jl(rep)
    assert r["mode"] == "DRY-RUN", r["mode"]
    assert sum(v["matches"] for v in r["report"].values()) >= 1, \
        "a dry run should carry matches (an applicable change seen but not applied)"
    assert md5_of(f) == before, "target file bytes moved under a dry run = guard broken"


def row_c2(tmp):
    """cure_applier applies only under --apply, and the idempotence
    assertion refuses the write: the canonical pack --apply canonicalizes
    the file (md5 changes, the second pass is idempotent rc=0); a custom
    non-idempotent pack under --apply exits IDEMPOTENCE-FAIL rc=1 with the
    file byte-untouched (write refused)."""
    d = os.path.join(tmp, "c2")
    os.makedirs(d)
    f = wf(os.path.join(d, "t.v"), CURE13_BODY)
    before = md5_of(f)
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply",
                                "--json", os.path.join(d, "rep.json")])
    assert rc == 0, "--apply canonical write should exit 0, got %d\n%s" % (rc, out[-400:])
    text = io.open(f, encoding="utf-8").read()
    assert "S01_BaseRing.NatLe (gnPrf f pf) k" in text, "the apply did not canonicalize"
    assert md5_of(f) != before, "the file did not move after --apply = apply face lost"
    rc2, out2 = sh(CURE_APPLIER, ["--file", f, "--apply"])
    assert rc2 == 0, "the second idempotent pass should rc=0, got %d\n%s" % (rc2, out2[-300:])
    # non-idempotent pack: trigger "a" -> template "aa" (the output hits
    # the trigger again) -> the idempotence assertion fails and refuses the write
    d2 = os.path.join(tmp, "c2b")
    os.makedirs(d2)
    g = wf(os.path.join(d2, "g.v"), "Lemma a : True.\n")
    pack = wj(os.path.join(d2, "nonidem_pack.json"), {
        "pack": "dm_nonidem", "version": "0",
        "patterns": [{"id": "dm_nonidem", "title": "matrix non-idempotent probe",
                      "engine": "line-regex", "trigger_regex": "a",
                      "template": "aa"}]})
    g_before = md5_of(g)
    rc3, out3 = sh(CURE_APPLIER, ["--file", g, "--pack", pack, "--apply"])
    assert rc3 == 1, "a failed idempotence assertion should rc=1, got %d\n%s" % (rc3, out3[-400:])
    assert "IDEMPOTENCE-FAIL" in out3, out3[-300:]
    assert md5_of(g) == g_before, "the file was written after a failed idempotence assertion = guard broken (file NOT written lost)"


def row_c3(tmp):
    """Write-face byte contract (S1 sync for the T0-5 newline change at
    wash/cure_applier.py:1090): after --apply on an all-LF fixture the
    on-disk byte md5 must equal the report's md5_after (md5s = md5 of the
    utf-8 text), no \\r\\n may land on disk, and the second idempotent pass
    must leave the bytes unchanged. Without the newline="" pin, Windows text
    mode wrote CRLF while the report md5 stayed LF-caliber, so the reported
    md5 never described the file it claims to describe."""
    d = os.path.join(tmp, "c3")
    os.makedirs(d)
    f = wf(os.path.join(d, "t3.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply",
                                "--json", os.path.join(d, "rep.json")])
    assert rc == 0, "--apply canonical write should exit 0, got %d\n%s" \
        % (rc, out[-400:])
    raw = open(f, "rb").read()
    r = jl(rep)
    on_disk_md5 = hashlib.md5(raw).hexdigest()
    assert on_disk_md5 == r["md5_after"], \
        "on-disk byte md5 %s != report md5_after %s = newline contract " \
        "broken (CRLF-caliber write face)" % (on_disk_md5, r["md5_after"])
    assert b"\r\n" not in raw, \
        "CRLF landed on disk from an all-LF fixture = byte face translated"
    rc2, out2 = sh(CURE_APPLIER, ["--file", f, "--apply",
                                  "--json", os.path.join(d, "rep2.json")])
    assert rc2 == 0, "second idempotent pass should exit 0, got %d\n%s" \
        % (rc2, out2[-300:])
    assert open(f, "rb").read() == raw, \
        "second pass drifted the on-disk bytes = idempotence broken"


# ---- ⑧ axiom_guard one row (T0-2 axiom guard S1 sync) ------------------------

def row_g1(tmp):
    """axiom_guard compile-leg write face (T0-2 axiom guard S1 sync): the
    run's only write faces are the caller-named --out report and its
    private temp workdir (the .vo output face is temp-only).  Face 1:
    toolchain unconfigured (env stripped by matrix sanitation) -> rc 111
    honest skip, zero judgment, the watched scratch tree gains zero bytes,
    and --out is not even created (the skip precedes every write face).
    Face 2: configured-but-missing binaries -> rc 9 fail-loud before any
    work (no compile can launch), the tree still gains zero bytes.  Face 3
    re-checks the --out non-creation explicitly with --out passed.  The
    real-compile coverage of the temp-only .vo face lives in the agent's
    live evidence run, outside the offline matrix (zero-real-compile
    discipline)."""
    d = os.path.join(tmp, "g1")
    tree = os.path.join(d, "tree")
    os.makedirs(tree)
    wf(os.path.join(tree, "one.v"), "Definition x := 1.\n")
    before = tree_manifest(tree)
    outp = os.path.join(d, "evid")
    rc, out = sh(AXIOM_GUARD, ["--repo", tree, "--out", outp])
    assert rc == 111, \
        "unconfigured toolchain must honestly skip rc 111, got %d\n%s" \
        % (rc, out[-400:])
    assert "SKIP" in out, \
        "rc 111 face must carry the SKIP banner: %s" % out[-300:]
    assert tree_manifest(tree) == before, \
        "skip face wrote the watched tree = write-face contract broken"
    assert not os.path.exists(outp), \
        "skip face created the --out dir = skip precedes every write face"
    rc2, out2 = sh(AXIOM_GUARD, ["--repo", tree],
                   env_extra={"ROCWASH_ROCQ": "D:/no_such_dir/rocq.exe",
                              "ROCWASH_COQCHK": "D:/no_such_dir/coqchk.exe"})
    assert rc2 == 9, \
        "configured-but-missing binaries must fail loud rc 9, got %d\n%s" \
        % (rc2, out2[-400:])
    assert "FAIL-LOUD" in out2, \
        "rc 9 face must carry the fail-loud banner: %s" % out2[-300:]
    assert tree_manifest(tree) == before, \
        "rc 9 face wrote the watched tree = write-face contract broken"


# ---- ⑥ addendum: the cure_applier compile-leg row (T0-2/T0-3 S1 duty:
# whoever writes a face, pins it in this matrix) -----------------------------

def row_c4(tmp):
    """cure_applier compile-leg write face (T0-2/T0-3 S1 sync): the --apply
    compile leg compiles temp-only copies (the repository tree gains zero
    bytes from the leg) and never activates offline.  Face 1: toolchain env
    stripped by matrix sanitation -> the leg records the honest
    not-configured status and the write proceeds with rc unchanged.
    Face 2: env set but the binary missing -> rc 9 fail-loud with the file
    NOT written (never a simulated green; the binary existence check
    precedes any compile launch, so this face stays offline).
    Face 3: a no-change second pass -> the leg records skipped-no-change
    without launching any compile.  The green->red interception and the
    temp-only .vo face of a live compile live in tests/test_cure_pack.py's
    env-gated section and the agent's evidence run, outside the offline
    matrix."""
    d = os.path.join(tmp, "c4")
    os.makedirs(d)
    f = wf(os.path.join(d, "t4.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply", "--json", rep])
    assert rc == 0, "offline --apply should exit 0, got %d\n%s" \
        % (rc, out[-400:])
    assert "COMPILE-LEG: SKIP" in out, \
        "unconfigured leg must carry the SKIP record: %s" % out[-300:]
    r = jl(rep)
    assert r.get("compile_check", {}).get("status") == "not-configured", \
        "not-configured leg must be recorded honestly: %r" % r.get("compile_check")
    d2 = os.path.join(tmp, "c4b")
    os.makedirs(d2)
    g = wf(os.path.join(d2, "g.v"), CURE13_BODY)
    g_before = md5_of(g)
    rc2, out2 = sh(CURE_APPLIER, ["--file", g, "--apply"],
                   env_extra={"ROCWASH_ROCQ": "D:/no_such_dir/rocq.exe"})
    assert rc2 == 9, \
        "configured-but-missing compiler must fail loud rc 9, got %d\n%s" \
        % (rc2, out2[-400:])
    assert "FAIL-LOUD" in out2, \
        "rc 9 face must carry the fail-loud banner: %s" % out2[-300:]
    assert md5_of(g) == g_before, \
        "rc 9 face wrote the target = write-face contract broken"
    rc3, out3 = sh(CURE_APPLIER, ["--file", f, "--apply",
                                  "--json", os.path.join(d, "rep3.json")])
    assert rc3 == 0, "no-change second pass should exit 0, got %d" % rc3
    r3 = jl(os.path.join(d, "rep3.json"))
    assert r3.get("compile_check", {}).get("status") == "skipped-no-change", \
        "no-change pass must record skipped-no-change: %r" \
        % r3.get("compile_check")


# ---- ⑦ frozen8 two rows (S1 hardening law: whoever writes a write face enters this matrix) --------------------

F8_ROSTER = [
    "certify/freeze_manifest.py",
    "certify/frozen8.py",
    "certify/push_gate.py",
    "names/mac_stmt_names.py",
    "scan/mac_stmt_scan.py",
    "seam/seam_probe.py",
    "tools/cpu_guard.sh",
    "verify/gate4_comment_guard.py",
    "verify/verify_vo.py",
    "wash/wash_engine.py",
]


def f8_skeleton(root):
    """scratch git skeleton: byte-identical copies of the ten roster files,
    one scratch commit → usable as a freeze --repo target (offline)."""
    os.makedirs(root)
    for rel in F8_ROSTER:
        fp = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        shutil.copyfile(os.path.join(REPO, rel.replace("/", os.sep)), fp)
    ident = ["-c", "user.name=dm-frozen8", "-c", "user.email=dm@frozen8.invalid"]
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    subprocess.run(["git", "-C", root] + ident + ["add", "-A"], check=True)
    subprocess.run(["git", "-C", root] + ident + ["commit", "-q", "-m", "dm"],
                   check=True)


def row_f1(tmp):
    """freeze write face: only the explicit --out/--tier2 paths land; a
    ledger-content drift refuses the roster fail-closed (rc=1, zero bytes
    at --out).  anchor certify/frozen8.py:357,366 + :334."""
    skel = os.path.join(tmp, "skel")
    f8_skeleton(skel)
    before = tree_manifest(skel)
    rc, out = sh(FROZEN8, ["freeze", "--repo", skel,
                           "--out", os.path.join(tmp, "m.json"),
                           "--tier2", os.path.join(tmp, "t2.md5")])
    assert rc == 0, "the freeze green path should exit 0, got %d\n%s" % (rc, out[-400:])
    assert tree_manifest(skel) == before, \
        "freeze wrote outside its bounds into the repository tree = guard broken (the write face is only the explicit --out/--tier2)"
    vo = os.path.join(skel, "verify", "verify_vo.py")
    with open(vo, "rb") as fh:
        data = bytearray(fh.read())
    data[len(data) // 2] ^= 0x01
    with open(vo, "wb") as fh:
        fh.write(bytes(data))
    out2 = os.path.join(tmp, "m2.json")
    rc2, o2 = sh(FROZEN8, ["freeze", "--repo", skel, "--out", out2])
    assert rc2 == 1, "a ledger-content-drift freeze should rc=1, got %d\n%s" % (rc2, o2[-400:])
    assert not os.path.exists(out2), "the refused roster still landed at --out = guard broken (zero writes)"
    assert "拒出名单" in o2, o2[-400:]


def row_f2(tmp):
    """timestamp write face: the only write face is the explicit --out
    execution record, landed only after the binding recheck passes; --out
    missing rc=2 zero-write; TSA unreachable rc=9 zero-write.  anchor
    certify/frozen8.py:806 + :772."""
    before = tree_manifest(tmp)
    man = os.path.join(REPO, "certify", "frozen8_manifest.json")
    rc, out = sh(FROZEN8, ["timestamp", "--list", man])
    assert rc == 2, "a missing --out should rc=2, got %d\n%s" % (rc, out[-300:])
    assert "需 --out" in out, out[-300:]
    tsr = os.path.join(tmp, "x.tsr")
    os.environ["ROCWASH_TSA_URL"] = "http://127.0.0.1:1/tsr"  # closed loopback
    try:
        rc9, o9 = sh(FROZEN8, ["timestamp", "--list", man, "--out", tsr])
    finally:
        os.environ.pop("ROCWASH_TSA_URL", None)
    assert rc9 == 9, "an unreachable TSA should rc=9, got %d\n%s" % (rc9, o9[-300:])
    assert "可达性自勘失败" in o9, o9[-300:]
    assert not os.path.exists(tsr), "the record still landed while unreachable = guard broken (zero writes)"
    assert tree_manifest(tmp) == before, "the timestamp failure path wrote out of bounds = guard broken"


def row_j1(tmp):
    """The sanitizing tool's self-reference guard: the mapping source table
    (--a2-table) never enters the sanitize target set; the --tree target
    set excludes it (--plan zero-write, visible on the report face) and an
    explicit --file naming it is refused rc=1.  anchor
    tools/jargon_apply.py:550-560 (skip_abs self-reference exclusion) +
    :471-484 (--file refusal)."""
    d = os.path.join(tmp, "j1")
    os.makedirs(d)
    mapdoc = wf(os.path.join(d, "jargon-to-standard-mapping-v1.md"),
                "| 判词 | conclusion | contract row. |\n")
    wf(os.path.join(d, "victim.md"), "这里有一个判词。\n")
    rep = os.path.join(tmp, "j1-report.json")
    before = tree_manifest(d)
    rc, out = sh(JARGON_APPLY, ["--tree", d, "--plan", "--a2-table", mapdoc,
                                "--json", rep])
    assert rc == 0, "plan should rc=0, got %d\n%s" % (rc, out[-400:])
    paths = [f["path"] for f in jl(rep)["files"]]
    assert "jargon-to-standard-mapping-v1.md" not in paths, \
        "the mapping source table must never enter the sanitize target set (a tool never washes its own map): %s" % paths
    assert "victim.md" in paths, \
        "an ordinary file in the same directory must stay in the target set (the exclusion must not be too wide): %s" % paths
    assert tree_manifest(d) == before, "the plan path wrote out of bounds = guard broken"
    rc, out = sh(JARGON_APPLY, ["--file", mapdoc, "--plan",
                                "--a2-table", mapdoc])
    assert rc == 1, "an explicit naming of the mapping source table should be refused rc=1, got %d\n%s" % (rc, out[-400:])
    assert "never washes its own map" in out, out[-300:]
    assert tree_manifest(d) == before, "the refusal path wrote out of bounds = guard broken"


# ---- ⑩ scheduler_lite, two rows (X6 work stream: whoever writes a write face enters this matrix)--------------------------------

SL_GAP = json.dumps({
    "schema": "rocqwash-exp/1", "id": "fix-001", "ts": "T0",
    "tool": "matrix-fixture", "batch": "b",
    "points": "uncovered face (TODO-SEAT counted, no silent "
              "degradation): ineq.demo @ D:/fix/x.lean",
    "evidence": "status=todo_seat", "fingerprint": "4" * 64}) + "\n"

SL_ROUNDS = (json.dumps({"schema": "rocqwash-round/1", "round_id": 1,
                         "timestamp_utc": "2026-11-15T04:49:24Z",
                         "verify_rc": 0, "mode": "auto"}) + "\n"
             + json.dumps({"schema": "rocqwash-round/1", "round_id": 2,
                           "timestamp_utc": "2026-11-15T16:05:30Z",
                           "verify_rc": 0, "mode": "auto"}) + "\n")

SL_AUTONOMY = json.dumps({"mode": "auto"}) + "\n"
SL_STATE = json.dumps({"schema": "rocqwash.round-state/1",
                       "admitted_classes": [
                           {"class": "jargon", "confidence": 1.0,
                            "basis": "matrix fixture"}]}) + "\n"

# The standing feedback face at the measured rate (ratchet ticket B added
# the --feedback consumption face to the scheduler; the matrix pins it to
# a canned fixture so SL1/SL2 stay hermetic regardless of the repository's
# own docs/scheduling-feedback.json state; the face is read-only, so the
# zero-write guards keep their exact meaning).
SL_FEEDBACK = json.dumps({"schema": "rocqwash.scheduling-feedback/1",
                          "rounds": {"total": 2, "auto": 1,
                                     "human_approved": 1,
                                     "approval_rate_auto": 0.5,
                                     "by_class": [], "errors": []}},
                         sort_keys=True) + "\n"


def sl_fixture(tmp, tag):
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    ledger = wf(os.path.join(d, "gap.jsonl"), SL_GAP)
    rounds = wf(os.path.join(d, "rounds.jsonl"), SL_ROUNDS)
    marker = wf(os.path.join(d, "ef-done.marker"), "abcdef1234567890\n")
    autonomy = wf(os.path.join(d, "autonomy.json"), SL_AUTONOMY)
    state = wf(os.path.join(d, "state.json"), SL_STATE)
    feedback = wf(os.path.join(d, "feedback.json"), SL_FEEDBACK)
    return ledger, rounds, marker, autonomy, state, feedback


def sl_run(argv, now="2026-11-17T00:00:00Z"):
    return sh(SCHEDULER_LITE, list(argv) + ["--now-utc", now])


def row_sl1(tmp):
    """The scheduler plan defaults to zero writes: fully flagged tmp canned
    inputs (gap/rounds/marker/gear all passing) plan a due verdict while
    the tmp tree md5 stays constant; without --out nothing lands at all;
    dryRun=true stays pinned (the ignition face is informational only and
    never initiates here)."""
    ledger, rounds, marker, autonomy, state, feedback = sl_fixture(tmp, "sl1")
    before = tree_manifest(tmp)
    rc, out = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                      "--ef-marker", marker, "--autonomy", autonomy,
                      "--state", state, "--feedback", feedback, "--json"])
    assert rc == 0, "the plan on the data state should exit 0, got %d\n%s" % (rc, out[-400:])
    plan = json.loads(out)
    assert plan["schema"] == "rocqwash.scheduler-lite.plan/1", plan["schema"]
    assert plan["verdict"] == "due" and plan["fireReady"] is True, plan
    assert plan["dryRun"] is True, "dryRun no longer always true = guard broken: %r" % plan["dryRun"]
    assert plan["ignitePipeline"] and all(s.startswith("py -I")
                                          for s in plan["ignitePipeline"]), \
        "the ignition pipeline is informational only"
    assert tree_manifest(tmp) == before, \
        "tmp tree bytes moved under plan without --out = guard broken (zero-write lost)"


def row_sl2(tmp):
    """The scheduler's only write face is the explicit --out: with --out
    exactly one file lands (a deterministic plan document), the input tree
    md5 stays constant, and two runs are byte-identical (the sort_keys
    deterministic form)."""
    ledger, rounds, marker, autonomy, state, feedback = sl_fixture(tmp, "sl2")
    outp = os.path.join(tmp, "sl2", "plan.json")
    before = tree_manifest(tmp)
    rc, out = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                      "--ef-marker", marker, "--autonomy", autonomy,
                      "--state", state, "--feedback", feedback,
                      "--out", outp])
    assert rc == 0, "plan --out should exit 0, got %d\n%s" % (rc, out[-400:])
    assert os.path.isfile(outp), "--out did not land = write face lost"
    assert tree_manifest(tmp) == before | {
        os.path.relpath(outp, tmp).replace(os.sep, "/"): md5_of(outp)}, \
        "a write face beyond --out appeared = guard broken (write face out of bounds)"
    plan = jl(outp)
    assert plan["dryRun"] is True and plan["verdict"] == "due", plan
    first = io.open(outp, "rb").read()
    rc2, _ = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                     "--ef-marker", marker, "--autonomy", autonomy,
                     "--state", state, "--feedback", feedback,
                     "--out", outp])
    assert rc2 == 0, rc2
    assert io.open(outp, "rb").read() == first, \
        "plan bytes drifted between runs = deterministic form broken (bytes lost)"


# ---- ⑪ auto_merge, three rows (X6 work stream: whoever writes a write face enters this matrix)------------------------------------

AM_SHA = "1befa2798beef00112233445566778899aabbccd"


def am_facts(path, pr, branch="supply/seat-pack", family="green", merged=False,
             ahead=1, mergeable=True, state="clean"):
    return wj(path, {
        "schema": "rocqwash-automerge-facts/1", "pr": pr,
        "repo": "rocqwash", "merged": merged, "mergeable": mergeable,
        "mergeable_state": state, "ci": {"family": family},
        "compare": {"ahead": ahead, "behind": 0,
                    "head_in_base": False,
                    "content_landed_in_base": False},
        "head_branch": branch, "note": "matrix fixture"})


def am_run(base, facts, extra):
    return sh(AUTO_MERGE, ["--facts", facts, "--ledger",
                           os.path.join(base, "am-ledger.jsonl")]
              + list(extra))


def row_am1(tmp):
    """Without --apply nothing is written: merge-ok plus a supply/* branch
    inside the whitelist (the rail rules allowed) yet the merge ledger is
    not written and not created; the allowed verdict goes to the report
    face only (--json is an explicit extra)."""
    d = os.path.join(tmp, "am1")
    os.makedirs(d)
    facts = am_facts(os.path.join(d, "facts.json"), 7)
    rep = os.path.join(d, "rep.json")
    before = tree_manifest(d)
    rc, out = am_run(d, facts, ["--head-branch", "supply/seat-pack",
                                "--json", rep])
    assert rc == 0, "an allowed dry run should exit 0, got %d\n%s" % (rc, out[-400:])
    assert "AUTO-MERGE-VERDICT: merge-ok" in out, out[-300:]
    assert "AUTO-MERGE-RAIL: allowed" in out, out[-300:]
    assert "dry run, row not written" in out, "an allowed dry run must state its dry-run record loudly"
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "the merge ledger landed without --apply = guard broken (zero-write lost)"
    r = jl(rep)
    assert r["rail"]["ledger_row_written"] is False, r["rail"]
    assert tree_manifest(d) == before | {
        os.path.relpath(rep, d).replace(os.sep, "/"): md5_of(rep)}, \
        "a write beyond the --json report face appeared = guard broken"


def row_am2(tmp):
    """hold never authorizes, and an out-of-scope branch is refused: a
    hold-red verdict writes nothing even under --apply (rail not-eligible
    precedes the merge ledger); a non-supply/* head exits rc=1 with a
    whitelist refusal and zero writes."""
    d = os.path.join(tmp, "am2")
    os.makedirs(d)
    hold = am_facts(os.path.join(d, "hold.json"), 15, family="content",
                    mergeable=False, state="dirty")
    foreign = am_facts(os.path.join(d, "foreign.json"), 16)
    before = tree_manifest(d)
    rc, out = am_run(d, hold, ["--head-branch", "supply/old-head",
                               "--apply"])
    assert rc == 0, "a hold verdict is data and should exit 0, got %d\n%s" % (rc, out[-400:])
    assert "AUTO-MERGE-VERDICT: hold-red" in out, out[-300:]
    assert "AUTO-MERGE-RAIL: not-eligible:hold-red" in out, out[-300:]
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "a hold ruling landed a merge-ledger row under --apply = guard broken (hold never authorizes)"
    rc2, out2 = am_run(d, foreign, ["--head-branch", "feature/quick-fix",
                                    "--apply"])
    assert rc2 == 1, "an out-of-scope branch should be refused rc=1, got %d\n%s" % (rc2, out2[-400:])
    assert "refused:branch-whitelist" in out2, out2[-300:]
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "the whitelist refusal still landed a merge-ledger row = guard broken (zero-write lost)"
    assert tree_manifest(d) == before, "the refusal path wrote out of bounds = guard broken"


def row_am3(tmp):
    """Daily budget cap plus duplicate refusal: --daily-cap 3 authorizes
    exactly 3 rows, the 4th is refused rc=1; a same-day same-PR duplicate
    is refused rc=1; the merge ledger stays at exactly 3 rows (the cap
    stops it; no fourth row)."""
    d = os.path.join(tmp, "am3")
    os.makedirs(d)
    ledger = os.path.join(d, "am-ledger.jsonl")
    f1 = am_facts(os.path.join(d, "f1.json"), 101, branch="supply/seat-1")
    rc, out = am_run(d, f1, ["--head-branch", "supply/seat-1", "--apply",
                             "--ledger", ledger])
    assert rc == 0, "the first issue should be allowed exit 0, got %d\n%s" % (rc, out[-400:])
    dup = am_facts(os.path.join(d, "dup.json"), 101, branch="supply/seat-1b")
    rc2, out2 = am_run(d, dup, ["--head-branch", "supply/seat-1b", "--apply",
                                "--ledger", ledger])
    assert rc2 == 1, "a same-day duplicate should be refused rc=1, got %d\n%s" % (rc2, out2[-400:])
    assert "refused:duplicate-authorization" in out2, out2[-300:]
    for i in (2, 3):
        f = am_facts(os.path.join(d, "f%d.json" % i), 100 + i,
                     branch="supply/seat-%d" % i)
        rc, out = am_run(d, f, ["--head-branch", "supply/seat-%d" % i,
                                "--apply", "--ledger", ledger])
        assert rc == 0, "issue %d should be allowed exit 0, got %d\n%s" \
            % (i, rc, out[-300:])
    rows = [json.loads(ln) for ln in io.open(ledger, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and all(r["kind"] == "authorize"
                                  and r["decision"] == "allowed"
                                  for r in rows), rows
    f4 = am_facts(os.path.join(d, "f4.json"), 104, branch="supply/seat-4")
    rc, out = am_run(d, f4, ["--head-branch", "supply/seat-4", "--apply",
                             "--ledger", ledger])
    assert rc == 1, "the 4th issue past the cap should be refused rc=1, got %d\n%s" % (rc, out[-400:])
    assert "refused:daily-budget" in out, out[-300:]
    rows2 = [json.loads(ln) for ln in io.open(ledger, encoding="utf-8")
             if ln.strip()]
    assert len(rows2) == 3, "the merge ledger must not grow past the cap or a duplicate (exactly 3 rows), got %d" % len(rows2)


# ---- ⑫ repair_scope, the shared-roster row plus the four E2 guard classes (X6 work stream: whoever writes a write face enters this matrix)--------

LANE_SUITE = (
    '#!/bin/bash\n'
    '# matrix fixture suite (tmp only)\n'
    'CASES="\\\n'
    't_real_one \\\n'
    't_ghost_lane"\n'
    'NCASES=$(echo $CASES | wc -w | tr -d \' \')\n'
    '\n'
    't_real_one() {\n'
    '  "$PY" -B "$REPO/tests/t_real_one.py"\n'
    '}\n'
    '\n'
    't_ghost_lane() {\n'
    '  "$PY" -B "$REPO/tests/t_ghost_lane.py"\n'
    '}\n')


def row_rs1(tmp):
    """repair_scope --check query face writes nothing and the exclusion
    conclusions bite: in the snapshot-degraded setting (a sandbox without
    frozen8.py, the fallback is loud) the append-only ledger faces, frozen
    rows, family directories, legal-data faces and zh archives all come
    back EXCLUDED, the three class-2 repairable faces come back
    REPAIRABLE, and the query writes nothing."""
    d = os.path.join(tmp, "rs1")
    os.makedirs(d)
    before = tree_manifest(d)
    rc, out = sh(REPAIR_SCOPE,
                 ["--repo", d, "--check", "更新账.md", "wash/wash_engine.py",
                  "certify/x.py", "README-cw.zh.md", "docs/mcp.md",
                  "tests/README.md", "README.md", "docs/repair-ledger.jsonl"])
    assert rc == 1, "a query with excluded faces should exit 1 (the conclusion is data), got %d\n%s" \
        % (rc, out[-400:])
    excluded = {ln.split()[1] for ln in out.splitlines()
                if ln.startswith("EXCLUDED ")}
    repairable = {ln.split()[1] for ln in out.splitlines()
                  if ln.startswith("REPAIRABLE ")}
    assert excluded == {"更新账.md", "wash/wash_engine.py", "certify/x.py",
                        "README-cw.zh.md", "docs/mcp.md"}, excluded
    assert repairable == {"tests/README.md", "README.md",
                          "docs/repair-ledger.jsonl"}, repairable
    assert tree_manifest(d) == before, "the query path wrote out of bounds = guard broken"


def lane_repo(tmp, tag):
    """lane-extract fixture repository: a suite (CASES with two lanes) with
    the real file in place (the $REPO/tests/ reference form) and the ghost
    file absent (tests/t_ghost_lane.py never lands, the R1 ENOENT form).
    -> (repo, suite_path)."""
    d = os.path.join(tmp, tag)
    os.makedirs(os.path.join(d, "tests"))
    sp = wf(os.path.join(d, "run_tests.sh"), LANE_SUITE)
    wf(os.path.join(d, "tests", "t_real_one.py"), "# fixture lane file\n")
    return d, sp


def row_e2a(tmp):
    """E2-1 lane-extract (--lane-detect/--lane-apply): the dry run writes
    nothing and records nothing; an excluded ledger face (the seeds/
    family) is refused rc=2 with zero creation; the budget cap (2 prior
    records) refuses the write rc=2, the suite bytes stay constant, and
    only an escalated(budget-cap) ledger row lands."""
    d, sp = lane_repo(tmp, "e2a")
    before = md5_of(sp)
    rc, out = sh(REPAIR_SCOPE, ["--repo", d, "--suite", "run_tests.sh",
                                "--lane-detect", "--json-out",
                                os.path.join(tmp, "e2a-rep.json")])
    assert rc == 0, "the dry-run detection should exit 0, got %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(tmp, "e2a-rep.json"))
    assert [g["lane"] for g in rep["ghosts"]] == ["t_ghost_lane"], rep["ghosts"]
    assert rep["applied"] is False, rep
    assert md5_of(sp) == before, "suite bytes moved under a dry run = guard broken"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "a dry run created the ledger = guard broken"
    rc2, out2 = sh(REPAIR_SCOPE, ["--repo", d, "--suite", "run_tests.sh",
                                  "--lane-detect", "--lane-apply",
                                  "--ledger", "seeds/ledger.jsonl"])
    assert rc2 == 2, "an excluded ledger face should be refused rc=2, got %d\n%s" % (rc2, out2[-400:])
    assert "REFUSED" in out2 and "excluded ledger face" in out2, out2[-300:]
    assert not os.path.isfile(os.path.join(d, "seeds", "ledger.jsonl")), \
        "the excluded-face refusal still created the ledger = guard broken (zero-write lost)"
    d4 = os.path.join(tmp, "e2a-budget")
    os.makedirs(os.path.join(d4, "tests"))
    sp4 = wf(os.path.join(d4, "run_tests.sh"), LANE_SUITE)
    wf(os.path.join(d4, "tests", "t_real_one.py"), "# fixture lane file\n")
    led = os.path.join(tmp, "e2a-ledger.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "class": "lane-extract",
             "target": "run_tests.sh",
             "outcome": "repaired(lane-unregister)", "utc": "T0"}
    with io.open(led, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_4 = md5_of(sp4)
    rc3, out3 = sh(REPAIR_SCOPE, ["--repo", d4, "--suite", "run_tests.sh",
                                  "--lane-detect", "--lane-apply",
                                  "--ledger", led])
    assert rc3 == 2, "the budget cap should refuse the write rc=2, got %d\n%s" % (rc3, out3[-400:])
    assert "budget exhausted" in out3, out3[-300:]
    assert md5_of(sp4) == md5_4, "an exhausted cap applied = guard broken (suite-bytes-constant lost)"
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and rows[-1]["outcome"] == "escalated(budget-cap)", \
        "the capped face lands only the escalated ledger row: %r" % rows[-1]


def row_e2b(tmp):
    """E2-2 roster-resync (tools/roster_resync.py): the dry run writes
    nothing and records nothing; --apply is a one-way derivation (the
    roster bytes stay constant, the count face is repaired to the roster
    value, one repair one ledger row); the budget cap refuses the write
    rc=1, the face bytes stay constant, and only an escalated row lands."""
    MINI = ('#!/bin/bash\nCASES="\\\nt_a \\\nt_b"\n'
            'for c in $CASES; do :; done\n')
    d = os.path.join(tmp, "e2b")
    os.makedirs(os.path.join(d, "tests"))
    rt = wf(os.path.join(d, "tests", "run_tests.sh"), MINI)
    cov = wf(os.path.join(d, "tests", "README.md"),
             "# mini\n\n预期 2 过\n\n## 覆盖面（3 例）\n")
    wf(os.path.join(d, "README.md"),
       "# mini\ntests/  # 自测套件（2 例） - test suite (2 cases)\n")
    md5_rt = md5_of(rt)
    before_cov = md5_of(cov)
    rc, out = sh(ROSTER_RESYNC, ["--repo", d])
    assert rc == 1, "a drifted dry run should exit 1 (drift is data), got %d\n%s" \
        % (rc, out[-400:])
    assert "drift=1" in out, out[-300:]
    assert md5_of(cov) == before_cov, "the dry run wrote the count face = guard broken"
    assert md5_of(rt) == md5_rt, "the dry run wrote the roster = guard broken (roster one-way lost)"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "a dry run created the ledger = guard broken"
    rc2, out2 = sh(ROSTER_RESYNC, ["--repo", d, "--apply"])
    assert rc2 == 0, "apply should repair to clean, got %d\n%s" % (rc2, out2[-400:])
    assert "applied=1" in out2 and "escalated=0" in out2, out2[-300:]
    assert md5_of(rt) == md5_rt, "apply wrote the roster out of bounds = guard broken (one-way lost)"
    assert "覆盖面（2 例）" in io.open(cov, encoding="utf-8").read(), \
        "the count face was not repaired to the roster value"
    led = os.path.join(d, "docs", "repair-ledger.jsonl")
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 1 and rows[0]["class"] == "roster-resync" \
        and rows[0]["outcome"] == "repaired(count-resync)", rows
    d4 = os.path.join(tmp, "e2b-budget")
    os.makedirs(os.path.join(d4, "tests"))
    rt4 = wf(os.path.join(d4, "tests", "run_tests.sh"), MINI)
    cov4 = wf(os.path.join(d4, "tests", "README.md"),
              "# mini\n\n预期 2 过\n\n## 覆盖面（9 例）\n")
    wf(os.path.join(d4, "README.md"),
       "# mini\ntests/  # 自测套件（2 例） - test suite (2 cases)\n")
    led4 = os.path.join(tmp, "e2b-ledger4.jsonl")
    prior = {"schema": "rocqwash-repair/1", "class": "roster-resync",
             "target": "tests/README.md:1", "branch": "unknown",
             "outcome": "repaired(count-resync)", "ts": "T0"}
    with io.open(led4, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_cov4 = md5_of(cov4)
    rc3, out3 = sh(ROSTER_RESYNC, ["--repo", d4, "--apply",
                                   "--ledger", led4])
    assert rc3 == 1, "the budget cap should refuse the write rc=1, got %d\n%s" % (rc3, out3[-400:])
    assert "escalated(budget-cap)" in out3, out3[-300:]
    assert md5_of(cov4) == md5_cov4, "an exhausted cap applied = guard broken (face-bytes-constant lost)"
    rows4 = [json.loads(ln) for ln in io.open(led4, encoding="utf-8")
             if ln.strip()]
    assert len(rows4) == 3 and rows4[-1]["outcome"] == "escalated(budget-cap)", \
        "the capped face lands only the escalated ledger row: %r" % rows4[-1]


def flaky_repo(tmp, tag):
    """flaky-quarantine fixture repository: a suite (CASES with one lane,
    the ONLY probe passes when run alone) plus an empty roster.
    -> (repo, suite_path, roster_path)."""
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    suite = ('#!/bin/bash\n'
             'CASES="\\\n'
             't_a"\n'
             'if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then exit 0; fi\n'
             'exit 1\n')
    sp = wf(os.path.join(d, "run_tests.sh"), suite)
    roster = wf(os.path.join(d, "advisory_roster.txt"), "# empty\n")
    return d, sp, roster


def row_e2c(tmp):
    """E2-3 flaky-quarantine (tools/flaky_guard.py --move): a frozen target
    (a seeds/-family roster) is refused rc=1 with zero writes and zero
    records (the scope check precedes the probe); the budget cap refuses
    the write rc=1, the roster bytes stay constant, and only an escalated
    ledger row lands."""
    d, sp, roster = flaky_repo(tmp, "e2c")
    before = tree_manifest(d)
    rc, out = sh(FLAKY_GUARD, ["--repo", d, "--suite",
                               os.path.join(d, "run_tests.sh"),
                               "--roster", os.path.join(d, "seeds", "adv.txt"),
                               "--ledger", os.path.join(d, "led.jsonl"),
                               "--move", "t_a", "--apply"])
    assert rc == 1, "a frozen target should be refused rc=1, got %d\n%s" % (rc, out[-400:])
    assert "REFUSED" in out and "outside the repair scope" in out, out[-300:]
    assert tree_manifest(d) == before, \
        "the frozen-target refusal wrote out of bounds = guard broken (zero-write zero-record lost)"
    d2, _sp2, roster2 = flaky_repo(tmp, "e2c-budget")
    led = os.path.join(d2, "led.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "kind": "repair",
             "class": "flaky-quarantine", "ticket": "E2-3", "target": "t_x",
             "outcome": "repaired", "branch": "nogit", "head_sha": "nogit",
             "roster": "advisory_roster.txt", "ts_utc": "T0"}
    with io.open(led, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_r2 = md5_of(roster2)
    rc2, out2 = sh(FLAKY_GUARD, ["--repo", d2, "--suite",
                                 os.path.join(d2, "run_tests.sh"),
                                 "--roster", roster2, "--ledger", led,
                                 "--move", "t_a", "--apply"])
    assert rc2 == 1, "the budget cap should refuse the write rc=1, got %d\n%s" % (rc2, out2[-400:])
    assert "budget exhausted" in out2, out2[-300:]
    assert md5_of(roster2) == md5_r2, "an exhausted cap applied = guard broken (roster-bytes-constant lost)"
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and rows[-1]["outcome"] == "escalated", \
        "the capped face lands only the escalated ledger row: %r" % rows[-1]


def row_e2d(tmp):
    """E2-4 doc-count (--doc-count-detect/--doc-count-apply): the dry run
    writes nothing and records nothing; --apply repairs to face=source and
    is idempotent (the second pass moves zero bytes); the budget cap
    refuses the write rc=2, the target-face bytes stay constant, and only
    an escalated(budget-cap) row lands."""
    CW = ("#!/usr/bin/env bash\nset -u\nusage() {\ncat <<'EOF'\n"
          "alpha   tools/alpha.py\nbeta    tools/beta.py\nEOF\n}\n"
          "hint_for() {\n  case \"$1\" in\n"
          "    alpha) echo a ;;\n    beta) echo b ;;\n  esac\n}\n"
          "case \"${1:-}\" in\n"
          "  alpha) shift; run_tool alpha \"tools/alpha.py\" \"$@\" ;;\n"
          "  beta) shift; run_tool beta \"tools/beta.py\" \"$@\" ;;\n"
          "  *) usage; exit 2 ;;\nesac\n")
    MINI_RT = '#!/usr/bin/env bash\nCASES="\\\nt_one \\\nt_two \\\n"\n'
    TOOL = '#!/usr/bin/env python3\n"""mini tool fixture."""\n'

    def mk_repo(tag, routes, tools_n):
        d = os.path.join(tmp, tag)
        os.makedirs(os.path.join(d, "tools"))
        os.makedirs(os.path.join(d, "tests"))
        wf(os.path.join(d, "cw.sh"), CW)
        wf(os.path.join(d, "tests", "run_tests.sh"), MINI_RT)
        wf(os.path.join(d, "tools", "alpha.py"), TOOL)
        wf(os.path.join(d, "tools", "beta.py"), TOOL)
        wf(os.path.join(d, "README-cw.md"),
           "# cw.sh - unified entry quick reference (rocqos (rocqwash) tool"
           " suite | %d routes over %d tools)\n" % (routes, tools_n))
        return d

    d = mk_repo("e2d", 3, 4)
    readme = os.path.join(d, "README-cw.md")
    before = md5_of(readme)
    rc, out = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-detect"])
    assert rc == 1, "drift detection should exit 1 (drift is data), got %d\n%s" \
        % (rc, out[-400:])
    assert "drift" in out and "doc={'routes': 3, 'tools': 4}" in out, \
        out[-400:]
    assert md5_of(readme) == before, "the dry run wrote the target face = guard broken"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "a dry run created the ledger = guard broken"
    rc2, out2 = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-apply"])
    assert rc2 == 0, "apply should repair to clean, got %d\n%s" % (rc2, out2[-400:])
    assert "outcome=repaired" in out2, out2[-300:]
    assert io.open(readme, encoding="utf-8").read() == \
        ("# cw.sh - unified entry quick reference (rocqos (rocqwash) tool"
         " suite | 2 routes over 2 tools)\n"), \
        "the face was not repaired to the source value"
    md5_mid = md5_of(readme)
    led = os.path.join(d, "docs", "repair-ledger.jsonl")
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 1 and rows[0]["class"] == "doc-count" \
        and rows[0]["outcome"] == "repaired(doc-count-sync)", rows
    rc3, _ = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-apply"])
    assert rc3 == 0 and md5_of(readme) == md5_mid, \
        "a non-idempotent second pass = guard broken (zero-byte lost)"
    rows3 = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
             if ln.strip()]
    assert len(rows3) == 1, "an idempotent pass must not add a ledger row, got %d" % len(rows3)
    d4 = mk_repo("e2d-budget", 9, 9)
    readme4 = os.path.join(d4, "README-cw.md")
    led4 = os.path.join(tmp, "e2d-ledger4.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "class": "doc-count",
             "target": "README-cw.md", "outcome": "repaired(doc-count-sync)",
             "utc": "T0"}
    with io.open(led4, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_r4 = md5_of(readme4)
    rc4, out4 = sh(REPAIR_SCOPE, ["--repo", d4, "--doc-count-apply",
                                  "--ledger", led4])
    assert rc4 == 2, "the budget cap should refuse the write rc=2, got %d\n%s" % (rc4, out4[-400:])
    assert "budget exhausted" in out4, out4[-300:]
    assert md5_of(readme4) == md5_r4, "an exhausted cap applied = guard broken (target-face-constant lost)"
    rows4 = [json.loads(ln) for ln in io.open(led4, encoding="utf-8")
             if ln.strip()]
    assert len(rows4) == 3 and rows4[-1]["outcome"] == "escalated(budget-cap)", \
        "the capped face lands only the escalated ledger row: %r" % rows4[-1]


# ---- matrix assembly -----------------------------------------------------------------
# ---- ⑩ selfheal_heartbeat rows (new-face section; English only) ---------------

def row_h1(tmp):
    """Default dry run is zero-write; under --apply exactly one tick line is
    appended per run and the prior ledger bytes stay byte-identical.
    Content pins, never mtime pins: back-to-back writes can land on one
    mtime tick, so an mtime comparison would be a probabilistic flake.
    anchor .github/scripts/selfheal_heartbeat.py (run gate + append face)."""
    d = os.path.join(tmp, "h1")
    os.makedirs(d)
    f = os.path.join(d, "heartbeat.jsonl")
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", f, "--now",
                                      "2026-01-01T00:00:00Z"])
    assert rc == 0, "read-only run should exit 0, got %d\n%s" % (rc, out[-300:])
    assert not os.path.exists(f), "read-only run must not create the ledger"
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", f, "--now",
                                      "2026-01-01T00:00:00Z", "--apply"])
    assert rc == 0, "apply run should exit 0, got %d\n%s" % (rc, out[-300:])
    with io.open(f, "rb") as fh:
        b1 = fh.read()
    recs = [json.loads(x) for x in b1.decode("utf-8").splitlines()]
    assert len(recs) == 1, "one apply run must append exactly one line: %s" % recs
    assert recs[0]["schema"] == "rocqwash.heartbeat/1" \
        and recs[0]["kind"] == "tick" \
        and recs[0]["tick"] == "2026-01-01T00:00:00Z" \
        and recs[0]["status"] == "ok", recs
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", f, "--now",
                                      "2026-01-01T00:10:00Z", "--apply"])
    assert rc == 0, "second apply run should exit 0, got %d\n%s" % (rc, out[-300:])
    with io.open(f, "rb") as fh:
        b2 = fh.read()
    assert b2.startswith(b1), "append-only: prior bytes must stay identical"
    recs2 = [json.loads(x) for x in b2.decode("utf-8").splitlines()]
    assert len(recs2) == 2 and all(r["kind"] == "tick" for r in recs2), recs2


def row_h2(tmp):
    """Loss-of-contact rule: a gap strictly over 90 minutes appends an ALERT
    line ahead of the tick; exactly 90 minutes stays silent; a ledger ending
    in an ALERT line still measures silence from the previous TICK, so a
    normal next interval does not stack alerts.
    anchor .github/scripts/selfheal_heartbeat.py (planned_records gap gate)."""
    d = os.path.join(tmp, "h2")
    os.makedirs(d)
    at = os.path.join(d, "at.jsonl")        # exactly at the threshold
    past = os.path.join(d, "past.jsonl")    # one second past the threshold
    src = os.path.join(d, "src.jsonl")      # alert line never a tick source
    sh(SELFHEAL_HEARTBEAT, ["--file", at, "--now", "2026-01-01T00:00:00Z",
                            "--apply"])
    sh(SELFHEAL_HEARTBEAT, ["--file", at, "--now", "2026-01-01T01:30:00Z",
                            "--apply"])
    with io.open(at, encoding="utf-8") as fh:
        recs = [json.loads(x) for x in fh.read().splitlines()]
    assert len(recs) == 2 and all(r["kind"] == "tick" for r in recs), \
        "a gap of exactly 90 minutes must stay silent: %s" % recs
    sh(SELFHEAL_HEARTBEAT, ["--file", past, "--now", "2026-01-01T00:00:00Z",
                            "--apply"])
    sh(SELFHEAL_HEARTBEAT, ["--file", past, "--now", "2026-01-01T01:30:01Z",
                            "--apply"])
    with io.open(past, encoding="utf-8") as fh:
        recs = [json.loads(x) for x in fh.read().splitlines()]
    assert len(recs) == 3, recs
    assert recs[1]["kind"] == "alert" and recs[2]["kind"] == "tick", \
        "the ALERT line must land ahead of the tick: %s" % recs
    assert recs[1]["since"] == "2026-01-01T00:00:00Z" \
        and recs[1]["gap_minutes"] > 90 \
        and recs[1]["status"] == "loss-of-contact" \
        and recs[1]["threshold_minutes"] == 90, recs[1]
    sh(SELFHEAL_HEARTBEAT, ["--file", src, "--now", "2026-01-01T00:00:00Z",
                            "--apply"])
    sh(SELFHEAL_HEARTBEAT, ["--file", src, "--now", "2026-01-01T02:00:00Z",
                            "--apply"])
    sh(SELFHEAL_HEARTBEAT, ["--file", src, "--now", "2026-01-01T02:29:00Z",
                            "--apply"])
    with io.open(src, encoding="utf-8") as fh:
        recs = [json.loads(x) for x in fh.read().splitlines()]
    alerts = [r for r in recs if r["kind"] == "alert"]
    assert len(alerts) == 1, "alert must not become a tick source: %s" % recs


def row_h3(tmp):
    """Fail-loud: a corrupt or schema-mismatched last ledger line refuses the
    append with rc=9 and zero bytes written; bad --now, nonpositive
    --alert-minutes and an empty --file are usage errors (rc=2).
    anchor .github/scripts/selfheal_heartbeat.py (last_tick raises + run
    validation + main exit map)."""
    d = os.path.join(tmp, "h3")
    os.makedirs(d)
    f = os.path.join(d, "corrupt.jsonl")
    sh(SELFHEAL_HEARTBEAT, ["--file", f, "--now", "2026-01-01T00:00:00Z",
                            "--apply"])
    with io.open(f, "a", encoding="utf-8") as fh:
        fh.write("not-json\n")
    with io.open(f, "rb") as fh:
        before = fh.read()
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", f, "--now",
                                      "2026-01-01T01:00:00Z", "--apply"])
    assert rc == 9, "corrupt ledger must fail loud rc=9, got %d\n%s" \
        % (rc, out[-300:])
    assert "not valid JSON" in out, out[-300:]
    with io.open(f, "rb") as fh:
        assert fh.read() == before, "refused run must write zero bytes"
    g = os.path.join(d, "wrongschema.jsonl")
    with io.open(g, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"schema": "other/1", "kind": "tick"}) + "\n")
    with io.open(g, "rb") as fh:
        before = fh.read()
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", g, "--now",
                                      "2026-01-01T01:00:00Z", "--apply"])
    assert rc == 9 and "schema mismatch" in out, out[-300:]
    with io.open(g, "rb") as fh:
        assert fh.read() == before, "refused run must write zero bytes"
    u = os.path.join(d, "u1.jsonl")
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", u, "--apply",
                                      "--now", "not-a-date"])
    assert rc == 2 and "bad --now" in out, out[-300:]
    assert not os.path.exists(u), "a refused run must not create the ledger"
    u = os.path.join(d, "u2.jsonl")
    rc, out = sh(SELFHEAL_HEARTBEAT, ["--file", u, "--apply",
                                      "--alert-minutes", "0"])
    assert rc == 2 and "must be positive" in out, out[-300:]
    assert not os.path.exists(u), "a refused run must not create the ledger"
    rc, out = sh(SELFHEAL_HEARTBEAT, [])
    assert rc == 2 and "--file is required" in out, out[-300:]


def row_h4(tmp):
    """Wiring face of the yml, line-scanned with the stdlib only (no YAML
    parser dependency): the heartbeat input defaults to false, HEARTBEAT=1
    is exported only under workflow_dispatch, the step calls the writer
    with --apply against docs/heartbeat.jsonl, the checkout condition
    covers HEARTBEAT, and the rollback line names the new script.
    anchor .github/workflows/selfheal.yml (input block, guard block,
    heartbeat step, checkout condition, rollback line)."""
    del tmp
    with io.open(SELFHEAL_YML, "r", encoding="utf-8") as fh:
        yml = fh.read()
    for needle in (
        "      heartbeat:",
        "        description: 'append one heartbeat tick line to "
        "docs/heartbeat.jsonl (true/false)'",
        "        default: 'false'",
        'echo "HEARTBEAT=1" >> "$GITHUB_ENV"',
        "if: env.HEARTBEAT == '1'",
        "--file docs/heartbeat.jsonl",
        "--apply",
        "selfheal_heartbeat.py",
    ):
        assert needle in yml, "yml wiring missing: %r" % needle
    lines = yml.splitlines()
    guard = [i for i, x in enumerate(lines)
             if "HEARTBEAT=1" in x and "$GITHUB_ENV" in x]
    assert len(guard) == 1, "HEARTBEAT=1 must be exported exactly once: %s" % guard
    g = guard[0]
    assert 'github.event_name }}" = "workflow_dispatch"' in lines[g - 2] \
        and "inputs.heartbeat" in lines[g - 2], \
        "the heartbeat env must sit under the dispatch-only guard: %s" \
        % lines[g - 2]
    step = [i for i, x in enumerate(lines)
            if x.strip().startswith("python3 .github/scripts/selfheal_heartbeat.py")]
    assert len(step) == 1, "exactly one writer invocation expected: %s" % step
    s = step[0]
    assert "--apply" in "\n".join(lines[s:s + 6]), \
        "the CI invocation must carry --apply: %s" % lines[s:s + 6]
    co = [i for i, x in enumerate(lines)
          if x.strip().startswith("uses: actions/checkout@")]
    assert co and any("env.HEARTBEAT == '1'" in lines[i - 1] for i in co), \
        "checkout must cover the heartbeat-only dispatch"
    assert "selfheal_heartbeat.py" in yml.split("Rollback:")[1], \
        "the rollback line must name the new script"


# ---- ⑪ repair_weekly rows (new-face section; English only) --------------------

def row_k1(tmp):
    """Aggregate write face: dry-run default is zero-write (stdout only,
    tree manifest constant); with --out the caller-named face file is the
    only write and reruns are byte-identical; the ledger input never gains
    a byte.
    anchor tools/repair_weekly.py:main aggregate branch + :render_markdown
    caller-named write face."""
    d = os.path.join(tmp, "k1")
    os.makedirs(d)
    led = os.path.join(d, "repair-ledger.jsonl")
    wf(led, json.dumps(
        {"class": "flaky-quarantine", "evidence": {"verdict": "content-red"},
         "kind": "repair", "outcome": "escalated", "schema":
         "rocqwash-repair-ledger/1", "target": "t_case", "ticket": "E2-3",
         "ts_utc": "2026-11-16T14:31:34Z"}, sort_keys=True) + "\n")
    before = tree_manifest(d)
    led_md5 = md5_of(led)
    rc, out = sh(REPAIR_WEEKLY, ["--ledger", led, "--date", "2026-11-17"])
    assert rc == 0, "dry-run aggregate should exit 0, got %d\n%s" % (
        rc, out[-300:])
    assert "repair-outcome" in out, "the E6 census must be on the face"
    assert tree_manifest(d) == before, "dry-run path wrote to disk = guard broken"
    face = os.path.join(d, "weekly.md")
    rc, out = sh(REPAIR_WEEKLY, ["--ledger", led, "--date", "2026-11-17",
                                 "--out", face])
    assert rc == 0, "--out run should exit 0, got %d\n%s" % (rc, out[-300:])
    after1 = tree_manifest(d)
    assert "weekly.md" in after1, "the face file must be the only new file"
    assert md5_of(led) == led_md5, "the ledger input must never gain a byte"
    rc, out = sh(REPAIR_WEEKLY, ["--ledger", led, "--date", "2026-11-17",
                                 "--out", face])
    assert rc == 0, "rerun should exit 0, got %d\n%s" % (rc, out[-300:])
    assert tree_manifest(d) == after1, "rerun byte drift on the write face"


def row_k2(tmp):
    """Record write face: --record without --apply is plan-only (zero
    bytes); --record --apply appends exactly one rocqwash-repair-ledger/2
    row; the vocabulary refusals (escalated without an evidence package, a
    watch-only reason outside the enum, a value outside the vocabulary)
    refuse before any byte moves.
    anchor tools/repair_weekly.py:record_row (vocabulary gate) +
    :ledger_append (the only append face)."""
    d = os.path.join(tmp, "k2")
    os.makedirs(d)
    led = os.path.join(d, "repair-ledger.jsonl")
    wf(led, "")
    base = ["--record", "--ledger", led, "--class", "flaky-quarantine",
            "--target", "t_case"]
    before = tree_manifest(d)
    led_md5 = md5_of(led)
    rc, out = sh(REPAIR_WEEKLY, base + [
        "--repair-outcome", "watch-only(guard-correct: budget)"])
    assert rc == 0, "plan should exit 0, got %d\n%s" % (rc, out[-300:])
    assert "PLAN record-row=" in out, out[-300:]
    assert tree_manifest(d) == before, "plan path wrote to disk = guard broken"
    rc, out = sh(REPAIR_WEEKLY, base + [
        "--repair-outcome", "watch-only(guard-correct: budget)",
        "--apply"])
    assert rc == 0, "apply should exit 0, got %d\n%s" % (rc, out[-300:])
    assert "APPLIED record-row-appended=1" in out, out[-300:]
    rows = [json.loads(x) for x in io.open(led, encoding="utf-8")
            if x.strip()]
    assert len(rows) == 1, "exactly one appended row expected: %s" % rows
    assert rows[0]["schema"] == "rocqwash-repair-ledger/2" \
        and rows[0]["repair-outcome"] == "watch-only(guard-correct: budget)", \
        rows
    after_apply = tree_manifest(d)
    for value, why in (
            ("escalated(evidence-package)", "escalated without evidence"),
            ("watch-only(guard-correct: vibes)", "reason outside the enum"),
            ("possibly-fine", "value outside the vocabulary")):
        rc, out = sh(REPAIR_WEEKLY, base + ["--repair-outcome", value,
                                            "--apply"])
        assert rc == 2, "%s should refuse rc=2, got %d\n%s" % (why, rc,
                                                              out[-300:])
        assert tree_manifest(d) == after_apply, \
            "%s refused but a byte moved = guard broken" % why
        assert md5_of(led) == md5_of(os.path.join(
            d, "repair-ledger.jsonl")), "the ledger changed on a refusal"


def row_k3(tmp):
    """Fail-loud input faces: a malformed ledger row exits rc=2 and an
    explicitly named absent ledger exits rc=9, both with zero writes.
    anchor tools/repair_weekly.py:ledger_rows (fail-loud parse) + :main
    explicit-ledger gate."""
    d = os.path.join(tmp, "k3")
    os.makedirs(d)
    bad = os.path.join(d, "bad.jsonl")
    wf(bad, "{not json\n")
    absent = os.path.join(d, "absent.jsonl")
    before = tree_manifest(d)
    rc, out = sh(REPAIR_WEEKLY, ["--ledger", bad, "--date", "2026-11-17"])
    assert rc == 2, "malformed ledger row should exit 2, got %d\n%s" % (
        rc, out[-300:])
    assert "FAIL-LOUD" in out, out[-300:]
    rc, out = sh(REPAIR_WEEKLY, ["--ledger", absent, "--date", "2026-11-17"])
    assert rc == 9, "explicitly absent ledger should exit 9, got %d\n%s" % (
        rc, out[-300:])
    assert "FAIL-LOUD" in out, out[-300:]
    assert not os.path.exists(absent), "the absent ledger must stay absent"
    assert tree_manifest(d) == before, "fail-loud path wrote to disk = guard broken"


# ---- ⑫ wording-face honesty rows (read-only line-scans; English only) ----------

README_MD = os.path.join(REPO, "README.md")
EVOLVE_PY = os.path.join(REPO, "tools", "evolve.py")
CAP_INDEX = os.path.join(REPO, "docs", "CAPABILITY-INDEX.md")


def row_n1(tmp):
    """README evolve wording alignment: the v55 snapshot line states the tool
    in substance as a signal-to-task-brief generator, the "autonomous
    evolution engine" label survives only as the cited module-title face
    pending rename adjudication, and the draft-only spawn-gate fact tokens
    stay on the line.
    anchor README.md:19 (v55 snapshot line)."""
    del tmp
    with io.open(README_MD, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    snap = [x for x in lines if x.startswith("> **v55 snapshot")]
    assert len(snap) == 1, \
        "exactly one v55 snapshot line expected, found %d" % len(snap)
    line = snap[0]
    assert "signal-to-task-brief generator" in line, \
        "the substance wording must be on the line: %s" % line[:160]
    raw = line.count("autonomous evolution engine")
    cited = line.count("`autonomous evolution engine v1`")
    assert raw == 1 and cited == 1, \
        "the label must survive only as the cited module-title face " \
        "(raw %d, cited %d)" % (raw, cited)
    assert "autonomous-evolution" not in line, \
        "the hyphenated label form must be gone from the line"
    assert "pending rename adjudication" in line, \
        "the rename-pending trace must be on the line"
    assert "draft-only spawn gate" in line \
        and "never writes the repository" in line, \
        "the draft-only spawn-gate fact tokens must stay on the line"


def row_n2(tmp):
    """evolve.py docstring honesty note: the Purpose block carries the
    draft-only token and the selection-not-implemented-in-this-code clause
    while keeping the no-execution and no-repository-write facts, the module
    title keeps its name, and the five-field doc block stays within the
    30-line budget.
    anchor tools/evolve.py:13-14 (docstring Purpose note lines)."""
    del tmp
    with io.open(EVOLVE_PY, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    opener = 2                       # file line 3, the module docstring opener
    assert lines[opener].startswith('"""evolve.py'), \
        "docstring opener drifted: %s" % lines[opener][:80]
    assert "autonomous evolution engine v1" in lines[opener], \
        "the module title keeps its name pending rename adjudication"
    closer = None
    for i in range(opener + 1, len(lines)):
        if lines[i] == '"""':
            closer = i
            break
    assert closer is not None, "docstring closer not found"
    budget = closer - opener + 1
    assert budget <= 30, \
        "the five-field doc block must stay within the 30-line budget: %d" \
        % budget
    block = "\n".join(lines[opener:closer + 1])
    flat = " ".join(block.split())   # collapse rewrap whitespace, match phrases
    for field in ("Purpose.", "Interface.", "Dependencies.", "Evidence.",
                  "Exit-codes."):
        assert field in block, "five-field block lost %s" % field
    assert "draft-only" in flat, "the draft-only token must be present"
    assert "selection is not implemented in this code" in flat, \
        "the selection-not-in-code clause must be present"
    assert "no candidate is executed" in flat \
        and "the repository is never written" in flat, \
        "the no-execution and no-repository-write facts must stay in Purpose"


def row_n3(tmp):
    """CAPABILITY-INDEX evolution_dashboard positioning note: the entry
    carries the KPI-aggregation positioning line, the rename candidate is
    declared but not applied, the census-transcribed Purpose face stays
    verbatim, and the entry name, path, invocation form, and route tokens
    stay untouched.
    anchor docs/CAPABILITY-INDEX.md:209 (evolution_dashboard note line)."""
    del tmp
    with io.open(CAP_INDEX, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    heads = [i for i, x in enumerate(lines)
             if x.startswith("### tools/evolution_dashboard.py")]
    assert len(heads) == 1, \
        "exactly one evolution_dashboard entry expected, found %d" % len(heads)
    h = heads[0]
    ends = [i for i in range(h + 1, len(lines))
            if lines[i].startswith("### ")]
    body = "\n".join(lines[h:ends[0] if ends else len(lines)])
    assert "a KPI aggregation read-out" in body, \
        "the KPI-aggregation positioning note must be inside the entry"
    assert "rename candidate awaiting adjudication" in body, \
        "the rename candidate must be declared but not applied"
    assert "Self-evolution dashboard: aggregates the three standing accounts" \
        in body, \
        "the census-transcribed Purpose face must stay verbatim (rename is " \
        "a candidate, not an applied change)"
    for token in ("python -I tools/evolution_dashboard.py",
                  "cw.sh evolution-dashboard"):
        assert token in "\n".join(lines), \
            "the entry path/invocation/route tokens stay untouched: %r" % token


# ---- matrix assembly -----------------------------------------------------------------

L1 = u_led({"A": u_rec0("A"), "B": u_rec1("B", "A")})   # A is a sanitizable chain root; B lacks A

ROWS = [
    ("U1", "unclog", "no --apply zero-write (tmp tree md5 constant, no apply ledger)",
     "tools/unclog.py:42,583,607", row_u1),
    ("U2", "unclog", "--audit zero-write (tree self-attested) plus mutual exclusion with --apply rc=2",
     "tools/unclog.py:827,762", row_u2),
    ("U3", "unclog", "frozen-roster refusal (read from frozen8 for real, zero apply)",
     "tools/unclog.py:506", row_u3),
    ("U4", "unclog", "non-root files never move (the apply face is always the chain-root file)",
     "tools/unclog.py:43,583,607", row_u4),
    ("W1", "wash_shape", "plan defaults to zero-write (would-fix seen while the tree stays constant)",
     "tools/wash_shape.py:1254", row_w1),
    ("W2", "wash_shape", "a partial rescan after --apply is never reported as shaped",
     "tools/wash_shape.py:1192-1205", row_w2),
    ("W3", "wash_shape", "an explicitly named frozen name refused rc=2 (refused at intake)",
     "tools/wash_shape.py:759-761", row_w3),
    ("W4", "wash_shape", "--header-map and --header-map-preset same-slot exclusive rc=2",
     "tools/wash_shape.py:1887-1890", row_w4),
    ("P1", "pushci", "--dry-run zero side effects (api_calls/git-caller pipelines both empty)",
     "tools/pushci.py:1163-1164,1116", row_p1),
    ("P2", "pushci", "a content red never reruns (heal.rounds empty, zero POST on api)",
     "tools/pushci.py:983-987", row_p2),
    ("P3", "pushci", "the heal cap stops the loop (--max-heal 3 stops after exactly 3 issues)",
     "tools/pushci.py:966-969", row_p3),
    ("S1", "cw_sentinel", "report-only by default (zero subprocess action without an on-red flag)",
     "tools/cw_sentinel.py:713-715", row_s1),
    ("S2", "cw_sentinel", "both on-red paths share the guard (plain/preset without --emit both rc=2)",
     "tools/cw_sentinel.py:722-723,884-886", row_s2),
    ("R1", "registry_union", "dry run defaults to zero-write (--out given yet nothing lands)",
     "tools/registry_union.py:881-885", row_r1),
    ("R2", "registry_union", "applies only under --apply (plus no --out rc=2, no implicit overwrite)",
     "tools/registry_union.py:826,883-885", row_r2),
    ("C1", "cure_applier", "dry run defaults to zero-write (target file md5 constant)",
     "wash/cure_applier.py:1272,1338", row_c1),
    ("C2", "cure_applier", "applies only under --apply plus idempotence-assertion write refusal (rc=1, zero bytes moved)",
     "wash/cure_applier.py:1282-1285", row_c2),
    ("C3", "cure_applier", "write-face byte contract: on-disk md5 == report md5_after, no CRLF, second pass byte-stable",
     "wash/cure_applier.py:1338-1341", row_c3),
    ("C4", "cure_applier", "compile-leg write face: temp-only copies, honest skip record, missing-binary rc=9 refuses the write, no-change pass compiles nothing",
     "wash/cure_applier.py:660,1286-1336,1300-1306", row_c4),
    ("F1", "frozen8", "freeze lands only the explicit --out/--tier2 (ledger drift refuses the roster rc=1 zero-write)",
     "certify/frozen8.py:357,366,334", row_f1),
    ("F2", "frozen8", "timestamp's only write face = the explicit --out record landed after the binding recheck (missing arg rc=2 / unreachable rc=9, both zero-write)",
     "certify/frozen8.py:806,772", row_f2),
    ("G1", "axiom_guard", "compile-leg write face temp-only: rc 111 honest skip with zero judgment and no --out / missing binaries rc=9 ahead of every work face",
     "tools/axiom_guard.py:main env gate, guard mkdtemp", row_g1),
    ("J1", "jargon_apply", "the sanitizing tool's self-reference guard: the mapping source table never enters the target set (--tree excludes it, --file refused rc=1)",
     "tools/jargon_apply.py:550-560,471-484", row_j1),
    ("SL1", "scheduler_lite", "plan defaults to zero-write (fully flagged canned inputs plan a due verdict, tree constant, dryRun always true)",
     "tools/scheduler_lite.py:474-476,404", row_sl1),
    ("SL2", "scheduler_lite", "only write face = explicit --out (exactly one file lands, input tree constant, two runs byte-identical)",
     "tools/scheduler_lite.py:474-476,424-427", row_sl2),
    ("AM1", "auto_merge", "no --apply zero-write (rail rules allowed yet the merge ledger is not created)",
     "tools/auto_merge.py:244-247", row_am1),
    ("AM2", "auto_merge", "hold never authorizes (zero writes even under --apply) plus out-of-scope branch refused rc=1 by the whitelist with zero writes",
     "tools/auto_merge.py:220-221,225-228", row_am2),
    ("AM3", "auto_merge", "daily budget cap plus duplicate refusal (exactly 3 authorize rows, the 4th/same-PR refused, the ledger does not grow)",
     "tools/auto_merge.py:229-233,234-239", row_am3),
    ("RS1", "repair_scope", "--check query face zero-write (shared-roster conclusions bite, snapshot degradation is loud)",
     "tools/repair_scope.py:140-160,556-576,590-620", row_rs1),
    ("E2A", "repair_scope", "class-1 lane-extract: default zero-write zero-record / excluded ledger face rc=2 zero creation / budget cap refuses the write, only the escalated row lands",
     "tools/repair_scope.py:477-482,400-411,487-493", row_e2a),
    ("E2B", "roster_resync", "class-2 roster-resync: default zero-write zero-record / roster one-way plus one repair one row / budget cap refuses the write, only the escalated row lands",
     "tools/roster_resync.py:246-248,256-265,327-334", row_e2b),
    ("E2C", "flaky_guard", "class-3 flaky-quarantine: frozen target rc=1 zero-write zero-record (the scope check precedes the probe) / budget cap refuses the write, only the escalated row lands",
     "tools/flaky_guard.py:390-396,514-523", row_e2c),
    ("E2D", "repair_scope", "class-4 doc-count: dry run zero-write zero-record / apply repairs to face=source idempotently, second pass zero bytes / budget cap refuses the write rc=2",
     "tools/repair_scope.py:917-926,975-994,997-1009", row_e2d),
    ("H1", "selfheal_heartbeat", "default dry run zero-write; --apply appends exactly one tick line, prior ledger bytes byte-identical (content pins, never mtimes)",
     ".github/scripts/selfheal_heartbeat.py:run gate, append_records", row_h1),
    ("H2", "selfheal_heartbeat", "loss-of-contact rule: gap strictly > 90min appends an ALERT line ahead of the tick; exactly 90min silent; ALERT never a tick source",
     ".github/scripts/selfheal_heartbeat.py:planned_records gap gate", row_h2),
    ("H3", "selfheal_heartbeat", "fail-loud: corrupt/schema-mismatched last line rc=9 zero bytes; bad --now / nonpositive --alert-minutes / empty --file rc=2",
     ".github/scripts/selfheal_heartbeat.py:last_tick raises, run validation", row_h3),
    ("H4", "selfheal_heartbeat", "yml wiring line-scan: dispatch-only HEARTBEAT guard, --apply + docs/heartbeat.jsonl invocation, input default false, checkout covers HEARTBEAT, rollback line names the script",
     ".github/workflows/selfheal.yml:heartbeat input, guard block, heartbeat step", row_h4),
    ("K1", "repair_weekly", "aggregate write face: dry-run default zero-write, --out is the only write and reruns are byte-identical, the ledger input never gains a byte",
     "tools/repair_weekly.py:main aggregate branch, render_markdown", row_k1),
    ("K2", "repair_weekly", "record write face: plan-only without --apply, --record --apply appends exactly one rocqwash-repair-ledger/2 row, vocabulary refusals move zero bytes",
     "tools/repair_weekly.py:record_row, ledger_append", row_k2),
    ("K3", "repair_weekly", "fail-loud input faces: malformed ledger row rc=2 and explicitly absent ledger rc=9, both zero-write",
     "tools/repair_weekly.py:ledger_rows, main explicit-ledger gate", row_k3),
    ("N1", "README.md", "evolve wording alignment: substance wording on the v55 snapshot line, the label cited as module title only (rename pending), draft-only spawn-gate tokens stay",
     "README.md:19", row_n1),
    ("N2", "evolve.py", "docstring honesty note: draft-only plus selection-not-in-code in Purpose, title name kept, five-field block within the 30-line budget",
     "tools/evolve.py:13-14", row_n2),
    ("N3", "CAPABILITY-INDEX", "evolution_dashboard positioning note: KPI-aggregation line inside the entry, rename candidate declared unapplied, Purpose face and path/invocation/route tokens untouched",
     "docs/CAPABILITY-INDEX.md:209", row_n3),
]


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_dm_")
    fails = []
    try:
        for rid, tool, guard, anchor, fn in ROWS:
            rowtmp = os.path.join(tmp, rid)
            os.makedirs(rowtmp)
            try:
                fn(rowtmp)
                print("PASS %s %-14s %s" % (rid, tool, guard))
            except AssertionError as e:
                fails.append((rid, anchor, guard, str(e)))
                print("FAIL %s %-14s %s" % (rid, tool, guard))
            except Exception as e:   # a row-level environment crash also counts as
                             # broken (fail-loud, never silent)
                fails.append((rid, anchor, guard, "row crashed (environment/fixture): %r" % e))
                print("FAIL %s %-14s %s (row crashed)" % (rid, tool, guard))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("== destructive-matrix: %d rows pass / %d rows broken ==" % (len(ROWS) - len(fails),
                                                          len(fails)))
    if fails:
        print("MATRIX broken-guard list (guard broken file:line):")
        for rid, anchor, guard, detail in fails:
            print("  broken %s @ %s — %s\n    violating evidence: %s" % (rid, anchor, guard,
                                                        detail))
        return 1
    print("DESTRUCTIVE-MATRIX PASS: all 43 refuse-to-write criteria pass "
          "(unclog x4/wash_shape x4/cure_applier x4/selfheal_heartbeat x4/"
          "pushci x3/auto_merge x3/repair_scope x3/repair_weekly x3/"
          "cw_sentinel x2/registry_union x2/scheduler_lite x2/wash_engine x1/"
          "axiom_guard x1/jargon_apply x1/roster_resync x1/flaky_guard x1 "
          "plus the combined rows; all tmp fixtures with injector canned "
          "responses, zero real network, zero real repository, zero real "
          "compile)")
    return 0


if __name__ == "__main__":
    sys.exit(main())