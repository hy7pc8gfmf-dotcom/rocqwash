# ops-realtime-service: real-time service operations manual v1.0 (November 11, 2026)

> Purpose.  Operations manual for the live service layer: the resident watcher's standard command line and JSONL consumption, the three on-red preset forms compared, the real-tree live-run procedure (`--audit` baseline → human review → `--apply` allowlist), and the background-task cooperation model.
> Interface.  Document face only. Every command and field is taken from the tools' live state (`tools/cw_sentinel.py` / `tools/unclog.py` / `tools/pushci.py` / `tools/cw_doctor.py` `--help` and docstrings · rocqwash v38 `c205ea0`); line-number anchors bind to the `c205ea0` commit state (concurrent multi-agent development · working-tree line numbers drift). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The four tool faces named above plus `tests/test_relay_e2e.py` for the relay evidence; no runtime dependency.
> Evidence.  All "measured sample" blocks are real-run records of the November 11, 2026 tooling-agent tmp injection drill (fixture data · zero real network, zero real compilation); the three-verdict evidence in `tests/test_relay_e2e.py` passes (event trigger / unclog dry run rc=0 zero writes / JSONL same-disk unclog report path; three verdicts all passing · idempotent two-run rc=0). Where the tools and this manual conflict, the tools' `--help` wins. Chinese annotations inside recorded output strings are the recorded runs' original wording, translated at the normalization round; the verbatim originals are in the `.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

> Discipline constraints (apply to every section):
> - **a failing result is data, not a tool failure**; CI failings / blockages / walls are all event and report data; exit codes only state the tool face.
> - **zero action is the default**; the watcher is report-only by default; apply happens only after human review via an explicit `--apply` (auto-hookup defaulting to a dry run is an invariant, tools/cw_sentinel.py:48-49, tools/unclog.py:41-44).
> - **offline drill pin**; `--injector` + `--sleep-scale 0` is the drill form; the production form omits it (the `"note": "ts=off…"` in the samples is the drill annotation · production event lines carry a real `ts`, tools/cw_sentinel.py:34-35).
> - **real compilation always goes through cpu_guard**; every `--world` real-probe / real-apply live run must pass `--guard` (probe_engine.py:10 precedent · thermal invariant); pure logic orchestration (classification / chain roots / cure dry run) compiles nothing and needs no guard.

## §1 Background watcher: standard command and JSONL usage

### 1.1 Standard command (background resident · copy the whole block to execute)

```bash
# ── §1.1 background watcher standard block (run at the rocqwash repository root · cw.sh passes through 1:1) ──────
LEDGERS_DIR=ledgers/            # source ②: probe ledger JSON directory (this source optional)
BUILDLOG=build.log              # source ③: build log file (this source optional)
WORK=.                          # watcher output directory (events/report/state all here)
SENTINEL_INTERVAL=60            # round interval in seconds

# create the directory first (a missing ledger directory = watcher rc 9 fail-loud · a missing buildlog file instead means zero events, not a failure)
mkdir -p "$LEDGERS_DIR"
# pre-flight usage probe: --once passes one round (exit 0) before the resident form is released — catches usage-class 2 errors before spawn
bash cw.sh sentinel --once --watch-ledgers "$LEDGERS_DIR" \
  --state-file "$WORK/.sentinel-probe-state.json" \
  --json "$WORK/sentinel-probe-report.json"

# resident watcher: the three signal sources (CI runs / local ledger chain roots / buildlog word faces) combine freely
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo ORG/REPO --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/.sentinel-state.json" --emit "$WORK/events.jsonl" \
  --json "$WORK/sentinel-report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

Key points (tool-grounded anchors): `--loop` requires `--state-file` (the seen idempotence persistence layer
rocqwash-sentinel-state/1 · tools/cw_sentinel.py:98-101); `--emit` is JSONL append
with per-line flush+fsync (tools/cw_sentinel.py:31); `--json` overwrites the report each round
(rocqwash-sentinel/1 · sort_keys · tools/cw_sentinel.py:81-86); stdout and the event stream are
byte-identical sources, so `>/dev/null` loses no evidence; give `--max-rounds N` and the watcher stops itself; only a manual stop uses
`kill "$SENTINEL_PID"` (POSIX TERM · the watcher has no trap special-casing).

### 1.2 The JSONL consumer

Event lines are `json.dumps(..., sort_keys=True)` (tools/cw_sentinel.py:386); keys are always lexicographic,
`"kind": "ci-red"` is a byte-stable grep target; `seq` continues across processes
from the file's existing line count (tools/cw_sentinel.py:32-33), so a consumer that sorts by seq restores the global order.

```bash
# grep forms (zero dependencies · coarse filter)
grep -c '"kind": "ci-red"' "$WORK/events.jsonl"      # CI failing-event count
grep '"kind": "blocking"'    "$WORK/events.jsonl"    # ledger blockage chain-root events
grep '"kind": "build-signal"' "$WORK/events.jsonl"   # build-log word-face hit events
```

```bash
# python3 pure-stdlib form (structured field pickup + reading the current round's on-red execution account from the report)
python3 - "$WORK/events.jsonl" "$WORK/sentinel-report.json" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    if ev["kind"] == "ci-red":
        print("CI-RED run=%s family=%s action=%s" % (ev["run"], ev["family"], ev["action"]))
    elif ev["kind"] == "blocking":
        print("BLOCKING top_root=%s dependents=%s" % (ev["top_root"], ev["dependents"]))
    elif ev["kind"] == "build-signal":
        print("BUILD-SIGNAL hits=%d" % ev["hits_total"])
rep = json.load(open(sys.argv[2]))   # the on-red execution account lives in the report, not the event stream (§2.3 accounting)
for act in rep.get("actions", []):
    print("ON-RED rc=%s cmd=%s" % (act.get("rc"), act.get("cmd")))
PY
```

### 1.3 Real output samples (November 11, 2026 tooling-agent real-run verbatim · tmp injection drill)

The ci-red event line (`--once --watch-repo org/repo --branch main --injector … --emit …
--sleep-scale 0`, measured rc 0):

```json
{"action": "fix-content", "branch": "main", "conclusion": "failure", "evidence": ["failing piece 1/1: ids=[501]", "on-register family: A-content-red (classification order takes the first)"], "family": "A-content-red", "kind": "ci-red", "note": "ts=off (--sleep-scale 0 · deterministic output) | classification=rocqwash-ci-triage/1 (ci_triage subprocess --offline)", "repo": "org/repo", "run": 178, "run_number": 9, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "abc123def"}
```

**Production form (without `--sleep-scale 0`): event lines carry a real `ts`**; measured live run of the §1.1 block shape
(November 11, 2026 tooling agent · ledger+buildlog two sources · `--loop --max-rounds 2` self-stop rc 0):

```json
{"dependents": ["B1"], "kind": "blocking", "ledger": "ledgerA.json", "n": 1, "note": "TOP chain root = the first name of chain_graph rocqwash-chain-graph/1 top_order (the self field decides the root's washability · chain_graph.py:88 precedent)", "schema": "rocqwash-sentinel-event/1", "self": {"probed": true, "rc": 0, "verdict": null, "washable": true}, "seq": 1, "top_root": "LibX", "ts": "2026-11-10T21:43:53Z"}
{"hits": ["BUILD-FAIL at step 2"], "hits_total": 1, "kind": "build-signal", "log": "…/build.log", "note": "word faces BUILD-FAIL/EXIT=134/Error: (classification-spectrum A/C tokens · ci_triage.py:95-118 same source)", "offset_after": 29, "offset_before": 0, "schema": "rocqwash-sentinel-event/1", "seq": 2, "truncated": false, "ts": "2026-11-10T21:43:53Z"}
```

Same-run report/state account evidence: `report: mode=loop round=2` · the state records
`ledgers=1 buildlogs=1` (seen idempotence in place · the §1.1 block is copy-executable line by line).

### 1.4 Exit-code branch table (watcher face)

| code | meaning (cw_sentinel --help / docstring accounting · tools/cw_sentinel.py:72-78) | operations action |
|---|---|---|
| 0 | patrol round complete (failings already emitted as events · not a tool failure) | step aside and continue; failing events go to human-review triage (§4) |
| 1 |; (the watcher has no 1 state: failings go through the event stream, not the exit code) | should not occur; if it does, handle as 9 and re-check |
| 2 | usage error (missing mode / both modes given / all three sources missing / --branch before --watch-repo / repo shape malformed / --once given loop-only flags / on-red preset misuse) | caught before spawn by the §1.1 probe; fix the arguments and restart |
| 9 | signal source unreachable (CI HTTP 4xx/5xx · netrc missing · token empty · runs/jobs shape malformed · preset parts missing · injector missing/malformed/canned not covered · ledgers directory missing · state malformed · subprocess rc≠0/timeout) | fail-loud and stop (never run while sick) · fix the source manually and restart the watcher |

## §2 The on-red preset comparison: three forms (report-only / unclog dry run / pushci dry-run)

### 2.1 The comparison table

| item | report-only (default) | `--on-red-preset unclog` | `--on-red-preset pushci` |
|---|---|---|---|
| nature | zero action is the default (tools/cw_sentinel.py:39-40) | the preset is template sugar over the same executor as `--on-red` (py:42-44) | same as the previous column |
| expanded command (verbatim · py:150-155) | none | `python3 -B tools/unclog.py --src {src} --json {emit_dir}/unclog_{run}.json` | `python3 -B tools/pushci.py --repo-path {repo_path} --branch {branch} --json {emit_dir}/pushci_{run}.json --dry-run` |
| required `--on-red-arg` |; (given anyway = orphan → 2) | `src=<source tree root>` | `repo_path=<repository directory>` + `branch=<branch>` |
| default safe state |; | **`--apply` not added by default = unclog dry runs only** (py:48-49 invariant) | **`--dry-run` by default = plan only, zero side effects, exit 0** (tools/pushci.py:89) |
| triggering events |; (report-only also emits events) | ci-red/blocking/build-signal failing events run one by one on the caller's behalf (py:713-716) | same as the previous column |
| placeholder substitution |; | static `{src}`/`{emit_dir}` substituted at expansion time (emit_dir = the directory holding `--emit` · py:53-55); dynamic `{run}`/`{family}`/`{repo}` substituted from the event (py:666-674) | same as the previous column |
| execution cap |; | 60s (`ON_RED_TIMEOUT` · py:168); a timeout records `rc=None` | same as the previous column |
| exit-code effect |; | **a side action, not a tool face: rc≠0/timeout only enters the actions account + a stdout annotation; the watcher exit code is unchanged** (py:37-39, 682-688) | same as the previous column |
| v38 measured (tmp drill) | watcher exit 0 · `actions: []` | the unclog proxy run rc=9 entered in the account (§2.3) · watcher exit 0 | dry run rc=0 zero side effects (measured · §2.3 end) · watcher exit 0 |

### 2.2 Usage negative examples (all rc=2 fail-loud · proven by selftest py:1266-1281)

| negative example | code |
|---|---|
| `--on-red` and `--on-red-preset` given together (the preset occupies the action slot · no silent pick py:44-46) | 2 |
| unrecognized preset name | 2 |
| required argument missing (unclog missing `src=` / pushci missing any) | 2 |
| duplicate key / no `=` / empty K·V / unknown key (unclog given `world=`, which is not in its argument face) | 2 |
| preset present but `--emit` missing (`{emit_dir}` takes the event-stream directory · py:53-55) | 2 |
| `--on-red-arg` orphan (no preset present · py:808-809) | 2 |
| preset part missing (unclog.py/pushci.py files missing) | 9 (py:656-657) |

### 2.3 Live detail: the unclog proxy run's rc=9 (v38 as-is accounting)

**Measured verbatim** (tmp drill · same as tests/test_relay_e2e.py verdict 1 / the watcher selftest ⑨ precedent
tools/cw_sentinel.py:1240-1265 "the unclog proxy run (fixture without --world) must enter the account with rc=9"):

```text
on-red note: cmd rc=9 (side action; does not change the sentinel's exit code)
```

What the actions account (the `--json` report · not the event stream) records:

```json
{"cmd": "python3 -B …/tools/unclog.py --src /tmp/…/src --json /tmp/…/unclog_178.json",
 "output": "FAIL-LOUD: --world is required (the probe is a real probe; offline needs --injector)\nworkdir -> …\ncandidate face: --src full-tree enumeration, 2 pieces -> …\nfrozen on the roster: 8 pieces (certify/frozen8.py --ledger live-read · refused failing at precheck)",
 "rc": 9, "seq": 1, "kind": "ci-red"}
```

Operations reading (as it is): the preset template passes only `--src` (py:151), while unclog's real probe
requires `--world` (tools/unclog.py:295-296) and offline requires `--injector`; the preset carries neither.
So **the watcher-side proxy run = trigger on seeing a failing event** (event + execution account + report path designated), while **the unclog itself**
is started by a human per §3 (`--audit` baseline → human review → `--apply` allowlist). This is exactly where the v38 dry-run-by-default
invariant lands: the watcher's proxy run never applies anything; the unclog decision stays with the human.

The pushci preset dry-run face, one measured shot (November 11, 2026 tooling agent · `pushci.py --repo-path <tmp> --branch
main --dry-run` · rc=0 · zero side effects):

```text
=== FINAL VERDICT: dry-run (exit 0) ===
json -> …/pushci_probe.json
```

## §3 The real-tree live-run procedure (unclog --audit baseline → human review → --apply allowlist)

> `unclog.py:63` states verbatim: "a real-tree audit live run belongs to the main session (this tool proves the fixture level only)"; this section is the standard procedure for the main session to execute that live run; the command blocks below are procedure templates (before a real-tree live run, drill first in tmp fixture form; samples in §3.1).

### 3.0 Step 0: the health-check preflight (optional · recommended)

```bash
# four-domain aggregated health check (environment/network/registry/blockage · diagnosis only, zero fixing · schema rocqwash-cwdoctor/1)
# --src --sample N opens the blockage-domain sample; the real-probe world is seeded per the wash/world_hook.py certified-donor discipline
bash cw.sh cw-doctor --json doctor.json --src src/ --sample 8 \
  --world world/ --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh
```

### 3.1 Step 1: the --audit blockage baseline (zero writes · rc always 0)

```bash
# read-only audit: a single-pass probe collect → chain_graph → blockage baseline report (final=audit · cures always 0)
# --guard required (real-compile thermal control) · --json emits the baseline account · workdir collects the per-round artifacts
bash cw.sh unclog --src src/ --world world/ --audit \
  --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh \
  --workdir audit-wd/ --json audit-baseline.json
echo "AUDIT_RC=$?"    # always 0: failings are baseline data, not a tool failure (unclog.py:54 · 110)
```

Zero writes is a **hard in-tool guarantee**: the `--src` whole-file md5 manifest self-verifies identical before and after the run; any manifest mismatch
fails loud with 9 and refuses to emit (unclog.py:57-59); the per-stage durations enter `report["timing"]` (audit's only
non-deterministic section · unclog.py:60-61). Mutual exclusion: `--audit` together with `--apply`/`--loop` is rc=2
(unclog.py:55-56 · selftest vector ⑩d).

**Fixture-level measured sample** (November 11, 2026 tooling-agent real-run verbatim · a tmp tree with two pieces A/B · canned failing account B missing A):

```text
=== AUDIT read-only baseline (single-pass probe collect → chain_graph · zero applies, zero tree writes) ===
[audit] collect: probe failing 1: B
chain_top: A(n=1,washable=True)
[audit] root=- cures=0 (audit baseline·red=1)
[audit] timing: enumerate=0.0 manifest=0s probe+chain=0.064s total=0.065s
AUDIT: 1 failing, 0 walls — the baseline report applies nothing and writes nothing to the tree (exit 0)
report -> /tmp/…/unclog_178.json
VERDICT: audit (exit 0)
```

### 3.2 Step 2: human review (what to read from the baseline account)

| what to read | fields (rocqwash-unclog/1) | reading |
|---|---|---|
| failing account | `rounds[0].probe_summary.red_files` / `final.red_files` | the full failing-surface list for this round |
| washable chain-root list | `rounds[0].chain_top[].lib` + `.self.washable` | entries with `washable=true` become allowlist candidates |
| wall account | `wall.<root>.reason` | `self-unwashable`/`cure-miss`/`frozen-in-service`/`root-file-missing`/`exclusive-group-conflict`/`no-chain-root` (unclog.py:35-39 · 696-703); no forced fixes · human review decides |
| chain-root file | `rounds[0].root_file` (`<src>/<root>.v`) | the only apply-target shape (outside pick there is no cure call path · unclog.py:43-44) |

### 3.3 Step 3: the --apply allowlist live run (after human review releases it)

The allowlist mechanism = `--candidates TSV` (source ① · probe_engine's same table header `件名\tmd5`): the candidate face
narrows to the human-released pieces; chain roots come only from the allowlist account, and apply touches only allowlisted chain-root files.

```bash
# allowlist TSV: list only the chain-root files released by human review (md5 matching the audit-time value · probe_engine's same table header)
printf '件名\tmd5\nA\t<audit-time md5>\n' > cands-whitelist.tsv
# live run: --apply the single switch (off by default) · the --rounds cap prevents spinning · the post-wash re-check runs inside the loop automatically
bash cw.sh unclog --src src/ --world world/ \
  --candidates cands-whitelist.tsv --apply --rounds 5 \
  --guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh \
  --workdir apply-wd/ --json apply-report.json --events apply-events.jsonl
echo "APPLY_RC=$?"    # 0=unclogged · 1=wall/rounds-exhausted (read the account and decide · failings are data)
```

In-tool structural guarantees (no human watching needed): apply touches chain-root files only (unclog.py:43-44); only the canon pack
cure_pack v1.3, freeform forbidden (unclog.py:42-43); frozen-roster entries (live-read from certify/frozen8.py
--ledger) fail the precheck closed (unclog.py:45-47); a failed apply-idempotence assertion refuses the write
(`idempotence-fail` · unclog.py:614-617).

### 3.4 Step 4: re-check and final verdict

The in-loop automatic re-check: rescan of the cured pieces (the cured token residual should be zero) + resprobe (rc should be 0 · after the world generation changes):
`rounds[k].rescan.residual_zero` / `resprobe.rc_ok` are reported as they are, no cosmeticizing
(unclog.py:16-17, 632-649). Final verdict, three states: `unclogged` exit 0 / `wall` exit 1 (honest
walls · per-root unwashable reasons listed) / `rounds-exhausted` exit 1 (the `--rounds` cap exhausted · per-round accounts attached).
World-generation accounting: this tool never writes `--world`; whether the post-wash re-probe clears the failing set depends on the world's `.vo` base generation changing
(unclog.py:115-116); if the re-probe has not cleared, it is recorded as it is; no forced fixes.

## §4 Cooperation with the main session (background bash task + notification-driven)

### 4.1 The step-aside model

The watcher pushes no notifications; **the event stream IS the notification face** (`--emit` append with per-line fsync ·
seq continues across processes · tools/cw_sentinel.py:31-33). The cooperation shape = the main session spawns the watcher as a background bash task, then **steps
aside and continues its own work**, and only at checkpoints comes back to consume the event stream and the current report; a failing result is data, not a tool failure, and a watcher
exit of 0 makes the step-aside legitimate (README-cw.md workflow-integration-interface ⑤ · backend-sentinel.md §5 same shape).

The three output pieces (all on the same disk as `--emit`):

| output | write form | consumption |
|---|---|---|
| `events.jsonl` | append + fsync · the event face | checkpoint grep / read sorted by seq (§1.2) |
| `sentinel-report.json` | overwritten each round · **the actions execution account lives here** (§2.3 accounting) | a checkpoint reads the current round's `actions[]` |
| `unclog_{run}.json` / `pushci_{run}.json` | preset proxy-run output · the path is designated by the preset ({emit_dir} same disk · py:53-55) | existence + verdict read |

### 4.2 The notification-driven checkpoint protocol

```bash
# checkpoint consumption (executed by the main session at every step-aside return · the zero-dependency two checks)
WORK=.
grep -c '"kind": "ci-red"' "$WORK/events.jsonl"          # ① the event face: failing-event count
python3 -c "import json,sys; r=json.load(open('$WORK/sentinel-report.json')); print('round=%s actions=%d' % (r['round'], len(r['actions'])))"
                                                          # ② the execution face: the proxy-run account count
# routing: 0 failing and 0 account → keep stepping aside; failings with account → the failing pieces go to human-review triage (the §3 procedure starts)
```

Stopping the watcher: `--max-rounds N` self-stop is the proper path; only a manual stop uses `kill "$SENTINEL_PID"` (§1.1).

### 4.3 The dynamic-workflow embedded-block pseudocode (spawn + checkpoint · the on-red preset form)

```text
// embedded block: background watcher + on-red preset unclog + step-aside checkpoint (shape from backend-sentinel.md §5)
phase "spawn-sentinel" {
  // the pre-flight --once usage probe (catches usage-class 2 errors before spawn)
  const probe = await world.run("bash", ["cw.sh", "sentinel", "--once",
      "--watch-ledgers", "ledgers/", "--state-file", ".sentinel-probe-state.json",
      "--json", ".sentinel-probe-report.json"]);
  if (probe.exitCode !== 0) return { verdict: "sentinel-unusable", rc: probe.exitCode };
  // resident watcher: the side action uses the unclog preset (the dry-run-by-default invariant · the proxy-run account enters report.actions)
  await world.run("bash", ["-c",
    "nohup bash cw.sh sentinel --loop --interval 60 " +
    "--watch-repo ORG/REPO --branch main --watch-ledgers ledgers/ " +
    "--state-file .sentinel-state.json --emit events.jsonl " +
    "--json sentinel-report.json --on-red-preset unclog " +
    "--on-red-arg src=src/ >/dev/null 2>&1 & echo $!"]);
  // the main session steps aside: the following phases do their own work
}
phase "consume-checkpoint" {
  const reds = await world.run("grep", ["-c", '"kind": "ci-red"', "events.jsonl"]);
  if (reds.exitCode === 0 && Number(reds.stdout.trim()) > 0) {
    // failing pieces go to human review: the unclog itself follows the §3 procedure (audit baseline → human review → --apply allowlist)
    const triage = await agent({ role: "triage",
      ask: "read the actions account of events.jsonl and sentinel-report.json, start the unclog per §3" });
    return { verdict: "red-forwarded", triage };
  }
  return { verdict: "no-red-events" };
}
```

### 4.4 The full hookup measured chain (tmp drill · three stations · proven by the three verdicts of tests/test_relay_e2e.py)

```text
station ① the watcher leg (canned CI failing build run 178 → on-red preset proxy run): watcher exit 0 · events.jsonl carries
   1 ci-red line (seq 1) · the actions account cmd=preset expansion (with the unclog_178.json path) ·
   the proxy run rc=9 recorded as it is (§2.3)
station ② the unclog dry-run leg (the same tmp tree --audit --injector canned failing account): rc=0 · verdict=
   audit · failing red_files=[B] · the washable chain root A(washable=true) emitted · cures always 0 · the src md5
   manifest identical before and after (zero writes)
station ③ the same-disk differential check: the actions[0].cmd designated path {emit_dir}/unclog_178.json ≡ the landed report
   (schema rocqwash-unclog/1 · verdict audit)
```

The three-verdict regression: `python3 -B tests/test_relay_e2e.py` (0 = all three verdicts pass · 1 = any failing verdict listed loudly).

## Appendix: the sample and evidence index

| evidence | location |
|---|---|
| the §1.3/§2.3/§3.1/§4.4 measured samples | November 11, 2026 tooling-agent tmp injection drill, real-run verbatim (fixture data · org/repo, run 178 and the md5 values are all non-real-repository signals) |
| the three-verdict regression | `tests/test_relay_e2e.py` (verdict 1 event trigger / verdict 2 unclog dry run rc=0 zero writes / verdict 3 JSONL same-disk unclog report path) |
| the three canonical embedded blocks | `examples/workflows/backend-sentinel.md` / `step-pushci.md` / `loop-unclog.md` |
| the interface-discipline canon | `README-cw.md` workflow-integration-interface ①-⑥ |
| the tool-grounded canon | each tool's `--help` + docstring (line anchors at c205ea0 · conflicts resolve to the tool) |
