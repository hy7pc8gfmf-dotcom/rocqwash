# backend-sentinel.md: workflow block ①: the background watcher (nohup-resident, with a JSONL consumer) / `工作流嵌段①：后台哨（nohup 长驻＋JSONL 消费端）`

> Purpose.  The fully copyable form of the typical background-watcher command line of the `README-cw.md` "workflow cooperation interface" ⑤ section (README-cw.md:200-218), plus the JSONL consumer sample, the exit-code branch table, and the dynamic-workflow embed pseudocode; one of the three canonical workflow-block samples of rocqwash v37.
> Interface.  Document face. It documents `cw.sh sentinel` (`tools/cw_sentinel.py`; schema `rocqwash-sentinel/1` · event `rocqwash-sentinel-event/1`); the `tools/cw_sentinel.py` docstring and `--help` are the normative tool face. Citations bind to the HEAD b98fe4e commit state (concurrent multi-agent development · working-tree line numbers drift). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  `tools/cw_sentinel.py` routed through `cw.sh`; `README-cw.md` "workflow cooperation interface" (README-cw.md:161-199) for the five joint disciplines; a GitHub API token via `~/.netrc` for the CI source. No runtime dependency of this document face itself.
> Evidence.  Every output sample in §3 is a real-run record of the November 18, 2026 tmp injection drill of the current tool at HEAD b98fe4e (fixture data · zero real network, zero real compilation), not hand-written; each sample paragraph states its measured rc. The predecessor capture of November 11, 2026 (v37, commit 41e74b0), whose classifier still emitted Chinese evidence wording, is archived in the sibling `.zh.md` file; the current classifier emits the English wording shown (tools/ci_triage.py:1004,1006). The grep consumer check of §2 returned rc 0 with count 1 on the drill output.
> Exit-codes.  Not applicable to a document face; the documented watcher keeps its implemented exit-code semantics (§4) unchanged.
>
> Discipline constraints (read before use):
> - **zero action is the default**; the watcher is report-only by default and only emits the event stream and reports; `--on-red 'CMD'` is an explicit bypass action (timeout cap 60s · rc≠0 does not change the watcher's exit code) (tools/cw_sentinel.py:72-73 docstring "default none = report-only · zero action is the default").
> - **a failing result is data, not a tool failure**; CI failing/blockage states are event data; the watcher's inspection round still exits 0; the exit code states only the tool face (0 completed / 2 usage error / 9 signal source unreachable).
> - **loop must be given `--state-file`**; the seen idempotency persistence layer (`rocqwash-sentinel-state/1`); default None = in-memory state, usable for a single once round, while loop re-emits duplicate events across rounds.
> - `--emit` is **JSONL append + per-line flush+fsync** (tools/cw_sentinel.py:44, 729-745); stdout always carries a mirror (loud); `seq` is monotonic within the event stream, and with --emit in place it is based on the file's existing line count and **continues numbering across processes**; consumers sorting by seq restore the global order (tools/cw_sentinel.py:46-48, 677-679).

## 1. Canonical background-watcher command block (copy and run as a whole)

```bash
# ── backend-sentinel workflow block: three-source background watcher ─────────────
# edit these four lines to your workspace (copy the rest verbatim)
LEDGERS_DIR=ledgers/            # source ②: probe ledger JSON directory (this source is optional)
BUILDLOG=build.log              # source ③: compile-log file (this source is optional)
WORK=.                          # watcher products land here (events/report/state all under this)
SENTINEL_INTERVAL=60            # seconds between rounds

# (run this block at the rocqwash repository root; cw.sh passes cx through 1:1 — flags and exit codes are not rewritten)
# source ① polls CI of org/repo main; ② ledger-chain roots; ③ buildlog token face.
# the three sources combine freely · at least one is required; all three are on here as the canonical demonstration.
mkdir -p "$LEDGERS_DIR"
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo ORG/REPO --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/.sentinel-state.json" --emit "$WORK/events.jsonl" \
  --json "$WORK/sentinel-report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

Snippet-by-snippet:

| Snippet | Why |
|---|---|
| `nohup … &` | the dynamic-workflow background-bash-task form (README-cw.md:167 "`--loop --interval S` runs as a long-lived sentinel (for background bash tasks)") |
| `--watch-repo ORG/REPO --branch main` | source ① the CI signal (`--branch` binds to the nearest preceding `--watch-repo` group · repeatable for several groups) |
| `--watch-ledgers DIR` | source ② a new probe ledger → the chain_graph subprocess emits the TOP chain root → a `blocking` event |
| `--watch-buildlog FILE` | source ③ tail-increment grep of the token face `BUILD-FAIL` / `EXIT=134` / `Error:` (same source as `BUILDLOG_SIGNAL_RE`, tools/cw_sentinel.py:365) → a `build-signal` event |
| `--state-file …` | required with loop: seen idempotency (new runs / new ledger mtime+name / buildlog byte offsets all recorded) |
| `--emit events.jsonl` | the JSONL event stream (consumer in §2); the stdout mirror is discarded by `>/dev/null`, the evidence surface stays in --emit/--json |
| `--json sentinel-report.json` | each round overwrites the report (rocqwash-sentinel/1) |
| `>/dev/null 2>&1 &` | watcher stdout and --emit have the same byte-level origin (emit_event mirrors to stdout first, then appends, tools/cw_sentinel.py:736-745); discarding stdout discards no evidence |

**Stopping the watcher** (round-cap self-stop or manual):

```bash
# standard path: give --max-rounds N (0 = unlimited · the default) and let the watcher stop itself;
# use kill only for a manual stop (sends TERM to the PID; the watcher installs no trap — plain POSIX semantics)
kill "$SENTINEL_PID"
```

## 2. The JSONL consumer (how the workflow main flow reads the watcher)

Event lines are `json.dumps(..., sort_keys=True)` (tools/cw_sentinel.py:736); the keys are always in lexicographic order, so `"kind": "ci-red"` is a **byte-stable** grep target:

```bash
# grep form (zero-dependency · coarse filter)
grep '"kind": "ci-red"'      "$WORK/events.jsonl"   # CI-failing events
grep '"kind": "blocking"'    "$WORK/events.jsonl"   # ledger blockage chain-root events
grep '"kind": "build-signal"' "$WORK/events.jsonl"  # compile-log token-hit events
```

```bash
# python3 pure-stdlib form (structured field access · global order restored by seq)
python3 - "$WORK/events.jsonl" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    if ev["kind"] == "ci-red":
        print("CI-RED run=%s family=%s action=%s" % (ev["run"], ev["family"], ev["action"]))
    elif ev["kind"] == "blocking":
        print("BLOCKING top_root=%s dependents=%s" % (ev["top_root"], ev["dependents"]))
    elif ev["kind"] == "build-signal":
        print("BUILD-SIGNAL hits=%d" % ev["hits_total"])
PY
```

## 3. Real output samples (real runs · not hand-written)

> Measured: November 18, 2026; real runs of the current tool at HEAD b98fe4e on this machine, tmp injection drill form.
> The predecessor capture of November 11, 2026 (v37, commit 41e74b0) is archived in `backend-sentinel.md.zh.md`.

**ci-red event line** (measured rc 0 with `--once --watch-repo org/repo --branch main --injector … --emit …
--json … --sleep-scale 0`; tmp injection drill):

```json
{"action": "fix-content", "branch": "main", "conclusion": "failure", "evidence": ["red jobs 1/1: ids=[501]", "rostered families: A-content-red (first match by classification precedence)"], "family": "A-content-red", "kind": "ci-red", "note": "ts=off (--sleep-scale 0; deterministic output)|classification=rocqwash-ci-triage/1 (ci_triage subprocess --offline)", "repo": "org/repo", "run": 178, "run_number": 9, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "abc123def"}
```

**blocking + build-signal event lines** (measured rc 0 with `--once --watch-ledgers … --watch-buildlog …
--sleep-scale 0`; ledger B misses library A → chain root A):

```json
{"dependents": ["B"], "kind": "blocking", "ledger": "base.json", "n": 1, "note": "ts=off (--sleep-scale 0; deterministic output)|TOP chain root = first name in chain_graph rocqwash-chain-graph/1 top_order (self field judges chain-root washability; chain_graph.py:88 precedent)", "schema": "rocqwash-sentinel-event/1", "self": {"probed": true, "rc": 0, "verdict": "RC0", "washable": true}, "seq": 1, "top_root": "A"}
{"hits": ["BUILD-FAIL: round 1", "Error: Unable to locate library | A"], "hits_total": 2, "kind": "build-signal", "log": "/tmp/sentinel_drill/build.log", "note": "ts=off (--sleep-scale 0; deterministic output)|tokens BUILD-FAIL/EXIT=134/Error: (classification-spectrum A/C tokens; ci_triage.py:95-118 same source)", "offset_after": 64, "offset_before": 0, "schema": "rocqwash-sentinel-event/1", "seq": 2, "truncated": false}
```

**Per-round report** (rocqwash-sentinel/1 · overwrite-written · excerpt of the same run, per-event `note` field omitted for width):

```json
{
 "actions": [],
 "events": [ { "action": "fix-content", "branch": "main",
               "conclusion": "failure",
               "evidence": ["red jobs 1/1: ids=[501]",
                            "rostered families: A-content-red (first match by classification precedence)"],
               "family": "A-content-red", "kind": "ci-red", "run": 178,
               "run_number": 9, "schema": "rocqwash-sentinel-event/1",
               "seq": 1, "sha": "abc123def" } ],
 "injector": "/tmp/sentinel_drill/injector.json",
 "mode": "once",
 "round": 1,
 "schema": "rocqwash-sentinel/1",
 "sleep_scale": 0.0,
 "sources": { "ci": [ { "branches": ["main"], "new_runs": 1,
                        "red_runs": 1, "repo": "org/repo", "runs_seen": 1 } ] },
 "ts_enabled": false
}
```

**Whole background-watcher block measured** (November 18, 2026 · tmp drill form: `--loop --interval 1 --max-rounds 2
--sleep-scale 0 --watch-repo org/repo --branch main --injector …`): the watcher self-stopped after 2 rounds ·
events.jsonl received 1 line (seq 1; the second round booked zero new runs through the seen layer) ·
`grep -c '"kind": "ci-red"'` → `1` (rc 0) · process exit 0. **The production form does not carry `--injector`/
`--sleep-scale`** (those two are the offline-drill pins: README-cw.md:183-190 discipline ③).

## 4. Exit-code branch table (watcher face · a failing result is data, not a tool failure)

| Exit code | Meaning (cw_sentinel --help / docstring wording) | Workflow action |
|---|---|---|
| 0 | inspection round completed (CI failing/blockage states already booked as **events** · not a tool failure) | the background watcher ends the process on this code · the main flow reads events.jsonl and decides what follows |
| 1 |; (the watcher has no level 1: failing states travel in the event stream · never as an exit code) | never occurs; if it appears, the `cw.sh` route is abnormal; recheck it as a 9 |
| 2 | usage error (missing mode / both modes given / all three sources missing / `--branch` before `--watch-repo` / malformed repo / negative value / loop-only flags with once) | should be stopped before the background watcher starts; the §5 pseudocode places it behind a front `--once` precheck |
| 9 | signal source unreachable (CI HTTP 4xx/5xx · netrc missing · token empty · runs/jobs malformed · injector missing/malformed/canned not covered · ledgers directory missing · state malformed · subprocess rc≠0) | fail-loud, stop at once (never keep running in a broken state · tools/cw_sentinel.py:236-238 honesty rules) · fix the source by hand and restart the watcher |

## 5. dynamic-workflow embed pseudocode

```text
// workflow block ① background watcher: a background bash task + the main flow consumes the event stream (main-session step-aside mode: whitepaper §3)
// tool: cw.sh sentinel (tools/cw_sentinel.py) · schema rocqwash-sentinel/1
phase "spawn-sentinel" {
  // front usage precheck: the --once single round must pass (exit 0) before the resident background form is allowed —
  // this stops the level-2 usage error before spawn; --injector + --sleep-scale 0 is the offline drill (discipline ③)
  const probe = await world.run("bash", ["cw.sh", "sentinel", "--once",
      "--watch-ledgers", "ledgers/", "--state-file", ".sentinel-probe-state.json",
      "--json", ".sentinel-probe-report.json"]);        // the exit code is the criterion
  if (probe.exitCode !== 0) return { verdict: "sentinel-unusable", rc: probe.exitCode };

  // resident watcher: a background task (nohup … &) · world.run only spawns + first check, never waits for its end
  await world.run("bash", ["-c",
    "nohup bash cw.sh sentinel --loop --interval 60 " +
    "--watch-repo ORG/REPO --branch main " +
    "--watch-ledgers ledgers/ --watch-buildlog build.log " +
    "--state-file .sentinel-state.json --emit events.jsonl " +
    "--json sentinel-report.json >/dev/null 2>&1 & echo $!"]);
  // the main session steps aside: the following phases do their own work and return to the event stream only at checkpoints
}
phase "consume-checkpoint" {
  // consumer gate: the grep count is the criterion (0 = no failing events · non-zero = failing events exist, hand them to a human-review subagent)
  const reds = await world.run("grep", ["-c", '"kind": "ci-red"', "events.jsonl"]);
  if (reds.exitCode === 0 && Number(reds.stdout.trim()) > 0) {
    const triage = await agent({ role: "triage",   // the human-review/triage subagent reads the event lines and the report
      ask: "read the ci-red events in events.jsonl and sentinel-report.json, and give a per-family disposition"});
    return { verdict: "red-forwarded", triage };
  }
  return { verdict: "no-red-events" };
}
```

> Pseudocode contract (dynamic-workflows SKILL §5/§10): the first `world.run` argument is a compile-time literal
> command name · runtime values go into the args array; the exit code is the confirmation, and a subagent must not
> restate what the world has already adjudicated.

## 6. Honesty notes

- All output samples in this file were produced by real runs of this repository's `tools/cw_sentinel.py`
  (HEAD b98fe4e) in the tmp injection drill on November 18, 2026, not hand-written; the `"note": "ts=off…"` in the
  sample event lines is the deterministic drill-form annotation of `--sleep-scale 0` (tools/cw_sentinel.py:51,688):
  production event lines carry a real `ts`. The predecessor samples (v37 41e74b0, captured November 11, 2026)
  showed the classifier's then-Chinese evidence wording; the current classifier emits the English wording shown
  (tools/ci_triage.py:1004,1006); their verbatim record is the sibling `.zh.md` archive. Line numbers throughout
  anchor to the HEAD b98fe4e commit state (concurrent multi-agent development · working-tree line numbers drift).
- `org/repo`, run 178, the md5 values, and similar content in the samples are tmp fixture data, not signals from any
  real repository.
- The consumer grep targets depend on the event lines' sort_keys byte order (rocqwash interface discipline ·
  README-cw.md:175-181); if the upstream tool changes the key order, the grep form breaks while the python3 form is
  unaffected; prefer re-structured parsing.
- The normative home of the five joint disciplines of the three-tool interfaces is the `README-cw.md` "workflow
  cooperation interface" section (README-cw.md:161-199); this block expands its ⑤ background-watcher form
  (README-cw.md:200-218) and is verbatim-compatible with it.

(English brief) Workflow block ①: run the v37 real-time sentinel as a background
bash task (`nohup bash cw.sh sentinel --loop … --emit events.jsonl &`), consume the
JSONL event stream from the main session (grep or stdlib-python), branch on exit
codes 0/2/9 (red is data, not tool failure; it travels in events, not exit codes).
Default is report-only; `--on-red` is an explicit bypass action. `--state-file` is
required for loop idempotency. See `README-cw.md` §"workflow cooperation interface" (README-cw.md:161-199) for the
normative five-discipline contract.
