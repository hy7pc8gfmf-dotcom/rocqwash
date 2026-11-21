# ops-live-run-log: live drill compilation · close-out verification record (November 11, 2026)

> Purpose.  Verbatim record of the close-out round's three-check final run (doc_lint / destructive-surface matrix / full suite) plus the day's live-evidence digest (the audit arc, doc_lint's two real-repository states, the cw_doctor health check, the net_probe dual probe) and the resident watcher's runnable-state declaration.
> Interface.  Document face only. Every recorded command and output line is transcribed from the run it names; each section names its evidence file path. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The tool and suite faces named per section (`tools/doc_lint.py`, `tests/test_destructive_matrix.py`, `tests/run_tests.sh`, `tools/cw_sentinel.py`); no runtime dependency.
> Evidence.  Every value comes from a real run or a real read of the same day (rocqwash v41 · HEAD `c5df4d4`), fail-loud, no cosmeticizing; the evidence-path table in section 4 lists every source with its timestamp. Chinese annotations inside recorded output lines are the recorded runs' original wording, translated at the normalization round; the verbatim originals are in the `.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the recorded tools keep their implemented exit-code semantics unchanged.

Scope: the close-out agent's three-check final run + compilation (record-keeping work · zero code changes). Repository: rocqwash v41 · HEAD `c5df4d4`.
Accounting: every number comes from the same day's real runs / real reads, fail-loud, no cosmeticizing; each section names its evidence file path or the command run with its exit code.
No-touch declaration: the frozen eight / quad8 / `更新账.md` untouched; `cw.sh` / the full test suite / the README family belong to the integration agent; untouched by this record.

---

## 1. The three-check final run record (per item: command + rc + key output lines)

All three-check commands ran wrapped in the thermal guard (`bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120 --`; guard banner `[cpu_guard] FRONT launch pos=0 waited=0s tlevel=0`, the per-run records are on file).

### ① doc_lint --repo (documentation-vs-implementation consistency, three checks · acceptance drift=0)

```bash
python3 tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash --json /tmp/wash_gate1_predoc.json
```

- **run A (the baseline before this record was written) rc=1 · drift_total=1; recorded failing as it is**:
  - `[flag] drift  docs/roadmap-v43-plus-20261111.md` +
    `refs=32；unresolved=7；oos=0；drift=1；L100: missing flag (phantom citation / surplus reference): the nearest tool before --injector, tools/baseline_diff.py's emitted help, has no such flag (5 flags emitted) · the pool tools/baseline_diff.py,tools/doc_lint.py likewise has none`
  - the other 19 faces all ok (tool_table: the 20 tools cross-checked identical at all four places; count CASES=56, five rows complete; flags: 13 faces zero drift).
  - drift-source attribution (git-proven): `git status --porcelain` shows `?? docs/roadmap-v43-plus-20261111.md` (untracked · mtime 08:00); a piece still in flight from another agent, not yet collected (the same batch's `?? docs/rocqwash-service-campaign-total-v1.0-20261111.md` already had drift=0); this is not drift on any face committed at `c5df4d4`; that piece belongs to its designated agent, and the close-out agent changes no code and stays inside its territory.
  - `tools/baseline_diff.py --help` really emits only the two flags `--json --md` (proven by a real run).
- Final run (the same command rerun after this record was written): rc and drift_total are recorded in the same day's close-out report notes; the drift criterion is a mechanical function of tree content, and the 20 new faces of this record enter the scan.
- Output account: `/tmp/wash_gate1_predoc.json` (schema `rocqwash-doclint/1` · sort_keys deterministic).

### ② The destructive-surface re-check matrix (acceptance: 17 verdicts all passing)

```bash
python3 -B tests/test_destructive_matrix.py
```

- **rc=0**, line-by-line record: `== destructive-matrix: 17 rows passing / 0 rows broken ==`;
  `DESTRUCTIVE-MATRIX PASS: all 17 refuse-to-write verdicts passing (unclog×4/wash_shape×4/pushci×3/cw_sentinel×2/registry_union×2/cure_applier×2 · all tmp fixtures + injector-canned, zero real network, zero real repository, zero real compilation)`
- The 17 rows: U1 missing `--apply` writes nothing / U2 `--audit` writes nothing + mutual exclusion rc=2 / U3 frozen entries refused failing / U4 non-chain-root files never touched passively / W1 the plan stage writes nothing by default / W2 partial never reported as shaped / W3 frozen names refused rc=2 / W4 header-map same-slot mutual exclusion rc=2 / P1 `--dry-run` zero side effects / P2 content-failing zero rerun / P3 heal stops at cap exhaustion / S1 report-only by default / S2 on-red both paths same guard rc=2 / R1 registry dry run writes nothing / R2 applies only under `--apply` + no `--out` rc=2 / C1 cure dry run writes nothing / C2 applies only under `--apply` + a failed idempotence refuses the write; all PASS.

### ③ The full-suite self-test (acceptance: zero failing · the SKIP rows listed as they are)

```bash
bash tests/run_tests.sh
```

- **rc=0**, summary line verbatim: `== 汇总: 52 过 / 0 红 / 4 略 / 共 56 例 ==` (the suite's summary line, 52 passing / 0 failing / 4 skipped / 56 cases total; the verbatim Chinese form is in the `.zh.md` archive);
  the skip line: `略例（正本环境缺·真本机全跑）: t_gate7_wrapper t_quad8_check t_gate6_born_wrapper t_verify_gate6` (skip examples, originals missing from this environment · fully run on the real machine)
  (each of the four was a `SKIP (正本环境缺·rc=111)`; originals missing from this environment · rc=111).
- PASS-count proof: `grep -cE ' PASS$'` = 52; first and last lines `[1/56] t_scan_selftest PASS` … `[56/56] t_baseline_diff PASS` (the full-suite record is `/tmp/wash_gate3_suite.log`).
- Three-check attribution: ② ③ passing; ① run A failed on another agent's in-flight piece (see above, not cosmeticized).

---

## 2. The live-drill history digest (distilled from live evidence already produced today)

### 2.1 The three audit shots (a real read of `/tmp/audit_run*.log` + `/tmp/audit_b48_b53_baseline.json`)

- **Shot 1** (`/tmp/audit_run.log` · 06:15): `[audit] collect: probe failing 27: CurriculumOptTemp,…,tlw1728R2_r2_res1_moment` (all 27 listed); `WALL: - — no-chain-root (none of the 27 failing pieces has a missing-library chain root (generation-gap / tool-caused failing · no forced fixes)…)`; `[audit] timing: enumerate=None manifest=2.955s probe+chain=0.477s total=3.786s`; `AUDIT: 27 failing, 1 wall — the baseline report applies nothing and writes nothing to the tree (exit 0)`; `VERDICT: audit (exit 0)`.
- **Final shot** (`/tmp/audit_run3.log` · 07:12): `[audit] collect: probe failing 0: -`; `[audit] root=- cures=0 (audit baseline·red=0)`; `[audit] timing: enumerate=None manifest=1.289s probe+chain=190.728s total=194.086s`; `AUDIT: 0 failing, 0 walls — the baseline report applies nothing and writes nothing to the tree (exit 0)`.
- Output account (`/tmp/audit_b48_b53_baseline.json`): schema `rocqwash-unclog/1`; `final`: `cures_applied_total=0 · cures_planned_total=0 · red_files=[] · rounds_run=1 · verdict="audit" · wall_count=0`; `rounds[1].probe_summary`: `n_records=27 · n_red=0 · red_files=[] · source="probe"`; `timing.total_s=194.086`.
- Attribution: the same `--candidates /tmp/audit27.tsv` (27 faces) shows a real-machine two-state arc **failing 27 → failing 0**, with audit applying nothing and writing nothing to the tree throughout (exit 0); the wall verdict went from "1 (no-chain-root · no forced fixes)" to zero. Honest note: the audit pieces on file under /tmp number four (audit27.tsv · two logs · one output account); the between-shots process pieces are not on file; the two logs' timestamps are shot 1 and the final shot.

### 2.2 doc_lint's two real-repository states (drift=3 → 0)

- **The drift=3 state** (`/tmp/doclint_real2.json` · 05:56; the same day's `/tmp/dl_run_a.json` · 05:59 cross-proves the same values): all three drift rows are `tools/` generic entries (defined at `cli/rocqwash:9`, non-underscore-prefixed .py) without a cw.sh case route (route missing), target = `tools/doc_lint.py` / `tools/netname_normalize.py` / `tools/select_audit.py`.
- **The drift=0 state** (`/tmp/doclint_v41.json` · 07:47; plus run A's output `/tmp/wash_gate1_predoc.json` tool_table row from the same day): `cw.sh` four-place + `tools/` cross-checks identical (20 tools complete at all four places · paths interlock) + the reconcile has zero gaps (all 15 `tools/` generic entries routed).
- Fix cause: the cw.sh route completion landed (HEAD commit message `netname-normalize/select-audit routes landed` · a real read of git log `c5df4d4`). run A's single residual failing source = another agent's in-flight untracked piece (see §1①); the committed faces' 20-tool table shows zero drift.

### 2.3 The cw_doctor real-machine health check (91.67 healthy)

- Evidence: `/tmp/cwdoc_real.json` (04:54). `score=91.67` · `verdict="healthy"` · `healthy_min=90.0` · `active_weight=60`; domain accounts: `env`=100.0/healthy (toolchain_dyld_doctor · missing_refs=[]); `net`=75.0/partial (up 3/4 · `down_endpoints:["https://github.com"]`); `clog`/`registry`=skip (skipped by default · the advice lists the rerun method as it is).
- Attribution: the real machine's default-endpoint health check passes the healthy line (90); the net domain's partial drags the score without hiding it (75 = 3/4 · same source as §2.4).

### 2.4 The net_probe real-machine dual probe (UNSTABLE, failing loudly)

- Evidence: `/tmp/rocqwash_livecheck_net.json` (two rounds, 02:22–02:23 · schema `rocqwash-net-probe/1`). Both rounds the same shape: `api.github.com`=200 ok / `productionresultssa1.blob.core.windows.net`=400 ok (reachable = ok · a non-2xx is also judged) / `results-receiver-actions.githubusercontent.com`=500 ok / `github.com`=`http_code:null · ok:false`, down in both rounds; **`verdict:"UNSTABLE"`**.
- Attribution: 4 endpoints, 3 up 1 down, outside the stability window; the failing verdict is loud and as-is: UNSTABLE, not passing; a same-source cross-proof of §2.3's net-domain score of 75.

---

## 3. The background watcher's runnable-state declaration (sentinel --loop · transcribed from the tool faces)

### 3.1 The dependency face (a real read of tools/cw_sentinel.py)

- Pure stdlib: imports = argparse/datetime/io/json/os/re/subprocess/sys/tempfile/time/urllib.error/urllib.request (`tools/cw_sentinel.py:153-164`) plus the same-directory shared piece `tools/_http_backoff.py` (`:186` sys.path injection · the backoff pure functions shared by three tools). **Zero third-party packages**.
- Subprocess engines all pre-existing (orchestration adds no new engine): classification = ci_triage --offline (a real subprocess doing real classification · zero network); chain roots = chain_graph.py; preset actions unclog (**`--apply` not added by default = dry run only**) and pushci `--dry-run` (plan only by default).
- The only external dependency: the GitHub token read from column 6 of the `~/.netrc` `machine github.com` line (parameterized by `--netrc`); zero network when the CI path is unused.

### 3.2 The startup command (the verbatim shape from cw.sh:41)

```bash
cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
```

- Dual mode: `--once` runs one patrol round, emits, and exits (for workflow steps) / `--loop --interval S` resident. Flag reality is proven one by one from argparse (`tools/cw_sentinel.py:1075-1147`): --once/--loop/--interval/--max-rounds/--watch-repo/--branch/--watch-ledgers/--watch-buildlog/--state-file/--emit/--emit-max-bytes/--rebuild-state/--on-red/--on-red-preset/--on-red-arg/--netrc/--timeout/--retry-max/--subproc-timeout/--injector/--sleep-scale/--json all really emitted.
- Usage checks: `--interval` belongs to `--loop` only; given together with `--once` rc=2 (`:966-967`); `--on-red`/`--on-red-preset` must come with `--emit` (a side action must land with the event stream · missing rc=2 · given together mutually exclusive rc=2).

### 3.3 The JSONL consumption method (docstring + live state)

- The event stream: `--emit FILE` appends line by line with flush + fsync; stdout mirrors it loudly. Line schema = `rocqwash-sentinel-event/1`, keys sort_keys, line order = production order.
- `seq` is monotonic within the stream: with `--emit` in place it continues across processes from the main body's plus rotated files' existing line count; **a consumer sorting by seq restores the global order** (across generations too; when `--emit-max-bytes` is exceeded the file rotates FILE.1→FILE.2 keeping 2 generations · `seq` continues across generations without renumbering).
- The three signal sources (combinable · at least one): ① the CI path `--watch-repo` (new completed run → jobs → ci_triage classification · state-file seen idempotence) ② the local-ledger path `--watch-ledgers` (new probe/ledger JSON → chain_graph → TOP-chain-root blocking events) ③ the local-blockage path `--watch-buildlog` (tail incremental grep · the word faces BUILD-FAIL / EXIT=134 / Error: · full lines only, to prevent half-line false hits).

### 3.4 The live smoke test (a real run at this record's close-out · rc=0)

```bash
python3 tools/cw_sentinel.py --once --watch-buildlog /tmp/wash_sentinel_smoke_buildlog.log --emit /tmp/wash_sentinel_smoke_events.jsonl --state-file /tmp/wash_sentinel_smoke_state.json --sleep-scale 0 --json /tmp/wash_sentinel_smoke_report.json
```

- The emitted event line (`/tmp/wash_sentinel_smoke_events.jsonl` · selected keys):
  `{"hits": ["Error:FooBar required"], "hits_total": 1, "kind": "build-signal", …, "schema": "rocqwash-sentinel-event/1", "seq": 1, "truncated": false}`; note "a failing result is data, not a tool failure": `--once` with a failing event still exits rc=0 (the event enters the account · exit-code semantics are separate).
- The tool's self-test history (a same-day real-run record): `/tmp/sentinel_final.log` (06:45 · the predecessor version, 11 sections PASS) → `/tmp/final_cw_sentinel.out` (all 12 sections passing: ① once idempotence ② ledger ③ buildlog increment ④ on-red ⑤ loop, three rounds of JSONL sequence ⑥ emit sort_keys/seq ⑦ determinism ⑧ the CLI's four codes ⑨ preset expansion ⑩ resilience backoff 403×3→[2,4,8] · Retry-After · 503 exhaustion 9 ⑪ state crash recovery ⑫ emit rotation over 2 generations); i.e. the v41 full assertion face PASS.
- **Readiness conclusion**: this machine's `--once` smoke test rc=0 with events actually emitted = the watcher runs; zero missing dependencies + the state/emit disk faces complete + the resilience layer's self-test passed = `--loop` resident ready (startup command as §3.2 · the CI path needs netrc in place; the local-ledger and blockage paths run standalone with zero external dependencies).

---

## 4. The evidence file path table

| class | path | timestamp (11-11) |
|---|---|---|
| audit shot 1 | /tmp/audit_run.log | 06:15 |
| audit final shot | /tmp/audit_run3.log | 07:12 |
| audit output account | /tmp/audit_b48_b53_baseline.json | 07:12 |
| audit candidate face | /tmp/audit27.tsv | 05:16 |
| doclint drift=3 state | /tmp/doclint_real2.json (/tmp/dl_run_a.json cross-proves the same values) | 05:56 (05:59) |
| doclint drift=0 state | /tmp/doclint_v41.json | 07:47 |
| doclint run A output | /tmp/wash_gate1_predoc.json | at this record's close-out |
| cw_doctor 91.67 | /tmp/cwdoc_real.json | 04:54 |
| net_probe UNSTABLE | /tmp/rocqwash_livecheck_net.json | 02:22–02:23 |
| watcher self-test, 12 sections | /tmp/final_cw_sentinel.out (/tmp/sentinel_final.log, the 11-section predecessor) | 06:45 (04:55) |
| watcher live smoke test | /tmp/wash_sentinel_smoke_{buildlog.log,events.jsonl,state.json,report.json} | at this record's close-out |
| check ② full-line record | this record §1② (transcribed line by line) | at this record's close-out |
| check ③ full-suite record | /tmp/wash_gate3_suite.log | at this record's close-out |

(Wherever "at this record's close-out" appears = a real run inside the session that wrote this record; each /tmp piece's timestamp was taken live with `ls -la`.)
