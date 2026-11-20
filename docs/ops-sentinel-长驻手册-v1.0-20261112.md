# ops-sentinel — sentinel long-run operations manual v1.0 (November 12, 2026)

> Purpose.  Operations manual for the resident (`--loop`) mode of `tools/cw_sentinel.py`:
>   deployment, usage, rotation and recovery, and the verified-run accounts. All content cites
>   existing records (the `更新账.md` v37-v47 entries, the existing manuals and embedded blocks in
>   three grades, tool docstrings); zero code changes, zero new tools, zero new flags — every
>   command transcribes an existing canonical block or a real v44/v47/v48 run, with no invented
>   parameters. Line numbers anchor to the rocqwash v47 `6217808` working-tree current state
>   (concurrent development shifts them; on conflict the tool's `--help` and docstring win). The
>   upstream manual `ops-realtime-service` (v38 state) is verbatim-compatible;
>   this manual adds only the resident-operations face. The v1.0 addendum (the deployment-artifact
>   documentation work stream) adds §1.6, the supervisor-shell deployment form.
> Interface.  Command blocks for `bash cw.sh sentinel --once | --loop` with flags verbatim (routed
>   1:1 by `cw.sh:41-43`); the consumers `tools/render_events.py` (§2.3) and `tools/red_dispatch.py`
>   (§2.4); the supervisor shell `examples/sentinel_supervisor.sh` (§1.6).
> Dependencies.  Python 3 standard library only; the watcher body is pure logic (zero compilation,
>   zero network) and spawns `ci_triage --offline` and `chain_graph` subprocesses; run artifacts
>   live outside the repository on the ConstructiveWorld side under `_log/`, keeping the rocqwash
>   work tree clean.
> Evidence.  Claims carry tool anchors (`cw_sentinel.py:101-111`, `:47-48`, `:34-35`, `:132-135`;
>   `更新账.md:3650`); §4 accounts are verbatim ledger citations (`更新账.md:3814-3834`, `:3895`,
>   `:3999`); §4.3 placement facts were read first-hand from the v48 three-piece artifact set.
>   Candidate lineage: `更新账.md:3638` (the v37 to-do 2, `--loop` true background) →
>   `roadmap-v43-plus:30-38` (candidate ②) → the v44 field debut
>   (`更新账.md:3814-3834`) → the v47 first real-repository run (`更新账.md:3895`) → the v48
>   overnight candidate (`更新账.md:3912`) → this manual.
> Exit-codes.  Not applicable to a document face; the watcher's implemented 0/2/9 semantics
>   (`cw_sentinel.py:101-111`) are described exactly as implemented, never redesigned.

## Cross-section discipline rules

Inherited unchanged from `ops-realtime-service` v1.0 §discipline (`:10-18`): five rules.

1. **A failing result is data, not a tool failure** — CI failing events, blockages, and token hits all flow through the event stream; the watcher's patrol exits 0 as usual, and the exit code reports only the tool face (0/2/9 · `cw_sentinel.py:101-111`).
2. **Zero action is the default** — the watcher is report-only by default; changes apply only after human review, via an explicit `--apply` (`cw_sentinel.py:47-48`; the unclog dry-run-by-default invariant, `更新账.md:3650`).
3. **Offline drill pinning** — `--injector` plus `--sleep-scale 0` is the drill form; the production form carries neither (production event lines carry a real `ts` · `cw_sentinel.py:34-35`).
4. **Real compilation goes through `cpu_guard`** — the watcher body is pure logic with zero compilation and does not pass through the guard (§1.4); real compilation actions downstream of the watcher (unclog `--audit` / `--apply` with a real `--world` probe) must be given `--guard`.
5. **`--loop` requires `--state-file`** — the seen idempotent persistence layer (`rocqwash-sentinel-state/1`); the default None = in-memory state (`cw_sentinel.py:132-135`), and a loop across rounds without state re-emits duplicate events.

---

## §1 Deployment (resident attachment)

### 1.1 Flag semantics and the placement convention (suggested: repository-external, on the ConstructiveWorld side `_log/`)

| Flag | Semantics (tool-face anchor) | Resident-run convention |
|---|---|---|
| `--loop` | Resident round patrol · JSONL event-stream append (for workflow background bash tasks · `cw_sentinel.py:87-88`; argparse `:1077-1078`) | Mutually exclusive with `--once`; both given → rc=2 (`:957-959`) |
| `--interval S` | Round interval in seconds · **only with `--loop`** (`--once` with it → rc=2 · `:966-967`) · default 60 (`:1035` · argparse `:1079-1080`) | Two forms in the real-run accounts: 45s (v44 · `更新账.md:3820`) / 60s (canonical block · `README-cw.md:123`) |
| `--state-file F` | The seen idempotent persistence layer `rocqwash-sentinel-state/1` (`cw_sentinel.py:132-135`) · **required with `--loop`** (argparse `:1093-1095`) | Persisted at each round end (`:1046`) · crash-recovery discipline in §3.1 |
| `--emit F` | Event-stream JSONL append + per-line flush+fsync + stdout mirror (`cw_sentinel.py:31` · `:480-509`) | Pair with `--emit-max-bytes N` as a rotation cap against unbounded growth (§3.2) |
| `--json out` | Per-round overwrite of the report `rocqwash-sentinel/1` (sort_keys · `cw_sentinel.py:114-121`) | The actions execution account lives in the report, not in the event stream (`ops-realtime-service:80`) |

**Placement convention (suggested: repository-external, on the ConstructiveWorld side `_log/`)**: watcher outputs are run artifacts and **do not enter the rocqwash repository** (the work tree stays clean · `git commit` of them is excluded by policy) — the suggested location is the repository-external ConstructiveWorld side `_log/sentinel_<work-stream>/`, the three-piece set on one volume:

```text
_log/sentinel_<work-stream>/events.jsonl    # --emit event stream (JSONL · §2.1 schema)
_log/sentinel_<work-stream>/report.json     # --json per-round report (overwritten each round · the actions execution account)
_log/sentinel_<work-stream>/state.json      # --state-file the seen idempotent account (§3.1/§3.3)
```

- The live case = **the v48 resident placement** `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/`, the three-piece set really on disk (§4.3, read first-hand) — placement takes exactly this form.
- `--emit` / `--state-file` / `--json` are fully parameterized with zero hard-coded absolute paths (`cw_sentinel.py:150-151`, the honesty rule); `{emit_dir}` takes the directory of `--emit` (preset output lands beside the event stream · `cw_sentinel.py:78`).
- A missing ledger directory = watcher rc 9 fail-loud (`--watch-ledgers` · `poll_ledgers :633-634`); a missing buildlog file is the opposite case = zero events, not a failure (the `present=false` loud marker · `:704-706`).

### 1.2 Standard command (canonical block · copy and execute as a whole)

Carried from the canonical blocks `ops-realtime-service` §1.1 (`:22-46`) / `backend-sentinel.md` §1 (`:20-41`); adjusting the `WORK` variable per §1.1 makes it ready — no flag of the tool face is rewritten:

```bash
# ── resident-watcher standard block (run from the rocqwash repository root · routed 1:1 by cw.sh:41-43) ──────────
REPO=ORG/REPO                    # path 1: CI repository (repeatable across groups · --branch joins the nearest group)
LEDGERS_DIR=ledgers/             # path 2: probe ledger JSON directory (this path optional)
BUILDLOG=build.log               # path 3: buildlog file (this path optional)
WORK=/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48   # §1.1 placement
SENTINEL_INTERVAL=60             # round interval in seconds

# pre-spawn usage probe: --once must run through one round (exit 0) before the background resident is allowed — it stops tier-2 usage errors before the spawn
# (ops-realtime-service:33 · backend-sentinel.md:147-152)
bash cw.sh sentinel --once --watch-ledgers "$LEDGERS_DIR" \
  --state-file "$WORK/state-probe.json" --json "$WORK/report-probe.json"

# resident watcher: the three signal-source paths (CI runs / local ledger chain roots / the buildlog token surface) combine freely · at least one is required
nohup bash cw.sh sentinel --loop --interval "$SENTINEL_INTERVAL" \
  --watch-repo "$REPO" --branch main \
  --watch-ledgers "$LEDGERS_DIR" --watch-buildlog "$BUILDLOG" \
  --state-file "$WORK/state.json" --emit "$WORK/events.jsonl" \
  --emit-max-bytes 104857600 \
  --json "$WORK/report.json" \
  >/dev/null 2>&1 &
echo "SENTINEL_PID=$!"
```

Key points: `--branch` must follow inside its `--watch-repo` group (repo first, then branch; otherwise rc=2 · `parse_watch_specs :937-939`); `--emit-max-bytes` may be omitted (no rotation; on-disk management for long runs in §3.2); stdout and the event stream are byte-for-byte the same source (`emit_event` mirrors before appending · `cw_sentinel.py:485-487`), so `>/dev/null` loses no evidence.

### 1.3 The two background forms (nohup form / workflow background bash task form)

| Form | Source | Applies to |
|---|---|---|
| **A · nohup form** | `README-cw.md:123-129` (the "workflow integration interface" ⑤ typical background watcher command line) + `backend-sentinel.md:34-40` | Human/session attachment: `nohup … >/dev/null 2>&1 &` + `echo "SENTINEL_PID=$!"` |
| **B · workflow background bash task form** | `backend-sentinel.md` §5 pseudocode (`:154-160`, `world.run("bash", ["-c", "nohup … & echo $!"])`) + `ops-realtime-service:299-304`; the yield-mechanism whitepaper (`workflow-integration-whitepaper:58/:115/:128`, "yield = do not race the watcher for writes") | dynamic-workflow embedded block: after spawn and the first check, **the foreground session yields**, consuming only when it returns at checkpoints (§2.5) |

Both forms issue the same tool-face command (`cw.sh` passes it through 1:1; parameters and exit codes are not rewritten · `backend-sentinel.md:30`) — the difference is only the spawn-side carrier; the watcher itself cannot tell.

### 1.4 The cpu_guard wrapping rule

- **The watcher body does not pass through the guard**: the watcher itself is zero-compilation, zero-network (the orchestration rule, `cw_sentinel.py:143-145`; the `run_py` docstring: "a pure-logic engine with zero compilation hence passes no cpu_guard (`probe_engine.py:10` case: only real compilation needs the guard)" `:296-300`) — spawn, resident round patrol, classification (the `ci_triage --offline` subprocess), and chain roots (the `chain_graph` subprocess) are all pure logic and take no compilation budget.
- **The on-red preset dry runs do not take the guard**: unclog (without `--apply` = dry run only) / wash-shape (plan only) / pushci (`--dry-run`) / triage (`--offline` classification) / cw-doctor (all-defaults health check) — five presets, all zero-compilation bypass actions (`cw_sentinel.py:50-79` preset table · 60s cap `:229`).
- **Only real compilation actions need the guard**: watcher failing → the human-initiated unclog `--audit` / `--apply` real probes (with `--world`) follow the `ops-realtime-service` §3 procedure (`:174-256`) and must be given `--guard /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh` (non-negotiable constraint `:16-18`).
- **Authoring-side invariant**: every execution on this manual's behalf runs wrapped in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh -MaxWaitSec 120` (thermal-control v3, the all-agent wrapping rule · `cw-ci-sop` §R2) — two layers, not to be mixed with the tool-face rule above: the authoring side governs the execution carrier; the tool face governs real compilation downstream of the watcher.

### 1.5 Stopping the watcher

- **The normal path is self-stop**: `--max-rounds N` (0 = unlimited · the default · argparse `:1081-1082`) — the v44 case ran `--max-rounds 15` to completion and self-stopped (`更新账.md:3820-3821`); `--max-rounds` belongs to `--loop` only (`--once` with it → rc=2 · `:968-969`).
- Only manual stopping uses `kill "$SENTINEL_PID"` (POSIX TERM; the watcher has no trap special-casing · `ops-realtime-service:52-53`).

### 1.6 Supervisor-shell deployment form (examples/sentinel_supervisor.sh · the runtime compensation layer for the v50 crash case)

> This section is the v1.0 addendum (the deployment-artifact documentation work stream, authored by the tooling agent) — line numbers anchor to the v50 `2ab39bc` working-tree current state (all other sections still anchor to v47 `6217808`, per the drift note in the header); the deployment source is `examples/sentinel_supervisor.sh` (a 1:1 generalization of the machine-local `/tmp` runtime version · fully parameterized paths with zero hard-coded absolute paths · Chinese annotations in the script · the supervisor shell's own exit codes 0/1/2/9).

**Case source (the v50 account · `更新账.md:3999`)**: the resident watcher crashed with `IncompleteRead` in round 10 — the real crash stack `http.client.IncompleteRead(371261 read, 72721 expected)` (371261 bytes read / 72721 bytes short · a transport-layer stream break; the task brief's paraphrase and the in-flight diff of the v51 tool-fix agent corroborate the same numbers) = the second class of tool debt: the v38 backoff retry of `api_get_json` covers only the `HTTPError` status-code face (`cw_sentinel.py:375-386`), while the transport-layer half-read at `raw = resp.read()` (`cw_sentinel.py:373`) raises `http.client.IncompleteRead` (not a `URLError`/`OSError` subclass · it escapes the `:387` catch face) → uncaught traceback → rc=1 crash — **backoff does not protect the transport layer**. Two-track disposition: the supervisor-shell compensation is deployed (the machine-local runtime case: `bash /tmp/sentinel_supervisor.sh` resident under nohup; a first-hand `ps` read shows the live three-level chain PID 489 → guard → watcher subprocess) + the tool fix lands in v51 (resilience layer: bounded retries for transport-layer transient breaks + per-source skip fallback in the loop · in flight concurrently at the time of writing) — **the shell is a process-level fallback, not an in-tool repair**: after the v51 tool fix lowers the transport-layer crash probability, the shell still catches every crash form the tool does not protect (emit/rename failures, OOM, machine restart, upper-layer crashes outside the loop's per-source guard face) and the runtime state of already-deployed older forms.

**Zero state loss (first-hand read of the artifacts · restart-after-crash continuation verified)**: the `_log/sentinel_v48/` three-piece set — `report.json` has `round=3` (the post-restart new process's round number) and **no `state_rebuilt` key** (no rebuild path taken · per §3.1); `state.json` seen across both repositories: Set 30 / Main 31 (§4.3's pre-crash account was 30/30 · one natural addition during the resume window); `events.jsonl` still 33 lines · `seq` 1-33 monotonic with no repeats — **the seen idempotent account survives the crash with zero loss and zero re-reports** (per §3.3, prefer duplicates over loss — the shell compensates the crashed process, not the data; the data face heals itself through the state continuation).

**Four generalization points + rc triage (generalized against the `/tmp` runtime version)**:

| Generalization point | Canonical-form configuration (env · fully parameterized) | /tmp runtime case form |
|---|---|---|
| Restart cap | `SUPERVISOR_MAX_RESTARTS` (default 40 · when exhausted, echoes loudly and exits 1) | `for i in $(seq 1 40)` fixed-length loop |
| Backoff | `SUPERVISOR_BACKOFF_BASE` ×2 exponential · capped by `SUPERVISOR_BACKOFF_MAX` (defaults 60/600) | fixed `sleep 60` |
| state continuation note | attaching the shell echoes a loud note (seen idempotent · zero-loss continuation across restarts · silent rebuild forbidden) | comment only |
| Scheduled-withdraw hook slot | `supervisor_withdraw_hook` **left empty** (default `return 0` · the example 09:00 form sits in the function comment · withdrawal granularity = the spawn boundary · withdrawing mid-run uses a manual kill per §1.5) | no hook slot (manual kill withdraws) |
| rc triage (generalization addition) | child rc=0 = rounds exhausted, self-stop → shell exit 0; **child rc=2 = usage error → no restart loop**, fail-loud exit 2 (restarting is meaningless · the same rule as the §1.2 pre-spawn usage probe); child rc=9 (signal sources unreachable) and every other rc (including the transport-layer crash rc=1, the `IncompleteRead` case form) → backoff restart, counted against the cap | any non-zero rc → `sleep 60` restart |
| guard slot | `SENTINEL_GUARD` (default: run directly — the watcher body is pure logic with zero compilation, per §1.4) + `SENTINEL_GUARD_ARGS` (default `-MaxWaitSec 120`) | hard-coded wrap in the CW-side `cpu_guard.sh` |

**Deployment command form** (the same shape as nohup form A · §1.3; run the `--once` usage probe before attaching the shell, per §1.2) — required items fail loud: missing `SENTINEL_WORK` / `SENTINEL_WATCH_REPOS` → shell rc 2; missing repo root / watcher body / working directory → shell rc 9:

```bash
SENTINEL_WORK=/path/to/_log/sentinel_v50 \
SENTINEL_WATCH_REPOS="ORG/REPO-A ORG/REPO-B" \
[SENTINEL_GUARD=/path/to/cpu_guard.sh SENTINEL_GUARD_ARGS="-MaxWaitSec 120"] \
nohup bash examples/sentinel_supervisor.sh >/dev/null 2>&1 &
```

**Deployment-form smoke check (not a real run · `cw_sentinel --selftest` gained vectors)**: a `bash -n` syntax check + key-line grep assertions (the restart cap / backoff / state-continuation note / withdraw hook slot left empty `return 0` / the guard slot / rc triage / the three-piece placement names / the zero hard-coded `/Users/` absolute-path assertion) — static assertions with zero execution and zero network; they verify only that the deployment artifact is in the repository and that its structure is in place point by point.

---

## §2 Usage (event stream → ledger → consumption → workflow)

### 2.1 JSONL per-line schema (rocqwash-sentinel-event/1)

An event line is `json.dumps(..., sort_keys=True)` (`cw_sentinel.py:485`) — **keys are always in dictionary order · a byte-stable grep target** (`backend-sentinel.md:66-67`); line order = emission order; `seq` is monotonic within the event stream, and when `--emit` is in place it continues numbering across processes (across generations) on a base of the body plus the rotated generations' existing line counts (`cw_sentinel.py:32-34` · `emit_seq_base :465-477`) — a consumer sorting by `seq` recovers the global order. `ts` comes from the time clock (production carries a real `ts` · UTC ISO8601 `Z` form `:248-251`); `--sleep-scale 0` stops the clock and marks `ts=off` (the drill form · `:34-35`).

The four-kind per-line field table (all emission forms of `cw_sentinel.py`):

| kind | Line fields | Emission anchor |
|---|---|---|
| `ci-red` | repo/run/run_number/branch/sha/conclusion/family/action/evidence (cap 8 entries · clip 200) + note | `:614-621` (the evidence cap `:226-227`) |
| `blocking` | ledger/top_root/dependents/n/self (self judges whether the chain root is washable · the `chain_graph.py:88` case) | `:679-686` |
| `build-signal` | log/hits (cap 50)/hits_total/truncated/offset_before/offset_after | `:723-729` (the cap `:227-228`) |
| `sentinel-error` | error/code + note (the last event before the fail-loud rc exit on a hard source error) | `:1053-1056` |

A real line sample (**the v48 resident run** · `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/events.jsonl` line 1, read first-hand — production form with a real `ts` / real run id / real sha; the human-readable `evidence`/`note` strings are shown in the modules' post-translation English output forms (`ci_triage.py:1004`/`:1006` · `cw_sentinel.py:904`) and the byte-exact original line is preserved in the `.zh.md` archive sibling):

```json
{"action": "fix-content", "branch": "chore/mac-lane-gate67-v2", "conclusion": "failure", "evidence": ["red jobs 1/2: ids=[128842885978]", "rostered families: A-content-red (first match by classification precedence)"], "family": "A-content-red", "kind": "ci-red", "note": "classification=rocqwash-ci-triage/1 (ci_triage subprocess --offline)", "repo": "hy7pc8gfmf-dotcom/ConstructiveWorld-Set", "run": 42513889148, "run_number": 267, "schema": "rocqwash-sentinel-event/1", "seq": 1, "sha": "726f11ae6b620474c99382c3bbad08ccac1b9796", "ts": "2026-11-11T17:29:00Z"}
```

For production-form `blocking` / `build-signal` real-line samples see `ops-realtime-service` §1.3 (`:98-100` · a live run measured by the tooling agent · real `ts`).

### 2.2 The two consumption forms (grep coarse filter / python3 structured)

Carried as-is from `backend-sentinel.md` §2 (`:69-89`) and `ops-realtime-service` §1.2 (`:61-83`):

```bash
# grep form (zero dependencies · coarse filter — it targets the sort_keys byte order)
grep -c '"kind": "ci-red"'      "$WORK/events.jsonl"   # CI failing-event count
grep    '"kind": "blocking"'    "$WORK/events.jsonl"   # ledger blockage chain-root events
grep    '"kind": "build-signal"' "$WORK/events.jsonl"  # buildlog token-surface hit events
```

```bash
# python3 pure-stdlib form (recovers the global order by seq + reads the current round's report actions execution account)
python3 - "$WORK/events.jsonl" "$WORK/report.json" <<'PY'
import json, sys
for ln in sorted(open(sys.argv[1]), key=lambda l: json.loads(l).get("seq", 0)):
    ev = json.loads(ln)
    print(ev["kind"], ev.get("family"), ev.get("top_root"), ev.get("hits_total"))
rep = json.load(open(sys.argv[2]))   # the on-red execution account lives in the report, not in the event stream
for act in rep.get("actions", []):
    print("ON-RED rc=%s cmd=%s" % (act.get("rc"), act.get("cmd")))
PY
```

The grep form depends on key order — if the upstream tool ever changes key order, the python3 form is unaffected, so re-structured parsing is preferred (`backend-sentinel.md:185-186`, the honesty note).

### 2.3 render-events ledger rendering (watcher JSONL → markdown ledger · v45 tool)

`tools/render_events.py` (entered in the ledger at v45 · `更新账.md:3844`) is a pure consumer-side renderer, zero network, zero reconstruction:

```bash
# single-stream rendering (--events and --dir are mutually exclusive · both given or both missing → rc=2)
python3 -B tools/render_events.py --events "$WORK/events.jsonl" \
  --md "$WORK/ledger.md" --json "$WORK/summary.json"
# directory-merge form (multiple files / rotated-generation shards · recovers the global order by (seq, ts, source order, line order))
python3 -B tools/render_events.py --dir "$WORK" --md "$WORK/ledger.md"
```

- Output: a kind/family/action three-dimension distribution table + a per-event 9-column table (seq/kind/family/action/repo/run/branch/first 8 sha chars/first 2 evidence entries); `--json` summary schema `rocqwash-render-events/1` (`render_events.py:71` · the full kind spectrum at `:74`, kinds outside the spectrum grouped under `other`); `--top N` truncates the family table.
- **No deduplication**: whatever the stream holds gets rendered (duplicates are the stream's truth, not a tool fault · stated as-is in the `render_events.py` docstring "no deduplication" section); malformed-line tolerance = skip + count in `bad_lines` + rc 1 with the account still emitted (incomplete data is reported loudly).
- Exit codes 0/1/2/9: 0 = rendering completed with zero malformed lines (verdict `ok` or `empty` both 0 — a failing result is data, not a tool failure); 1 = `bad_lines>0`; 2 = usage error; 9 = input unreachable (the `render_events.py` docstring exit-codes section).
- Determinism: reruns on the same input are byte-identical (the selftest idempotency vectors); lineage = roadmap item ⑧, artifact ledger rendering (`roadmap-v43-plus:94-100`) · the v45 assertion over real watcher output (the v44 14-event family distribution recomputed independently, all correct · two runs byte-identical · `更新账.md:3844`).

### 2.4 red_dispatch router pairing (watcher failing events → action-preset routing · v46 tool)

`tools/red_dispatch.py` (entered in the ledger at v46 · `更新账.md:3865`) reads watcher-event JSONL and emits **action presets** by kind/family — the pairing example carried as-is from `README-cw.md:215-221` (the ⑨ failing-event routing embedded block):

```bash
# watcher-state pairing: the --on-red template passes the whole event stream to the router (the suggest tier emits a copy-paste block with zero execution)
bash cw.sh sentinel --once --watch-ledgers ledgers/ --emit events.jsonl \
  --on-red 'python3 tools/red_dispatch.py --event-file <json> --preset suggest'
```

Single-step direct call (without the watcher · adds one routing round over an existing event stream · report-only default with zero execution): `bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json`

- **Five routes** (routes attach only to existing `cw.sh` routes, zero new engines · the `red_dispatch.py` docstring route-table section): B/E families → pushci rerun suggestion / A family → manual-fix-note, never auto-fixed, emits a fix list / C family → doctor suggestion / blocking → unclog suggestion (`--apply` only explicit) / build-signal → wash-shape suggestion.
- **Three preset tiers**: report-only (the default · zero execution · zero side effects) / suggest (emits a copy-paste command block) / auto (**runs on your behalf only when explicit** · 60s cap · rc≠0 recorded loudly without touching the exit code · the `red_dispatch.py` docstring header `:9-11`).
- **Dedup**: `--state-file` keyed by kind+repo+run+family, cooldown default 600 (`red_dispatch.py:70-76`) · a malformed state shape → rc 9, refused, no rebuild (the same crash-recovery discipline as `cw_sentinel.py:136` · `red_dispatch.py:73-74`).
- The dry-run-by-default / apply-only-after-human-review invariant holds (gate-keeping design · the settled rule at `roadmap` ③ `:40-46` cannot be relaxed unilaterally).

### 2.5 The workflow embedded block (the `--once` step form)

`--once` = one patrol round, emits the account, exits — the workflow-step form (`cw_sentinel.py:87`) — all three usage forms are pre-existing:

1. **The pre-spawn usage probe** (stops tier-2 usage errors before the spawn): `backend-sentinel.md:147-152` / `ops-realtime-service:33` — `--once` must run through with exit 0 before the §1.3 form-B background resident is allowed.
2. **Checkpoint single-round consumption**: `backend-sentinel.md:163-172` `consume-checkpoint` — the grep count is the criterion (0 = no failing events, keep yielding · non-zero = hand to human review / a triage subagent).
3. **The first real-repository batch-patrol form**: the v47 first run was exactly the `--once` dual-repository form (`更新账.md:3895` · §4.2).

The embedded-block pseudocode is carried in full from `backend-sentinel.md` §5 (`:143-176`) — the two phases `spawn-sentinel` / `consume-checkpoint` plus the pseudocode contract (the `world.run` first argument is a compile-time literal · the exit code is the confirmation `:175-176`); the full workflow embedded-block index is at `workflow-integration-whitepaper:115` (the ① background watcher line) and `service-layer-overview:127`.

---

## §3 Rotation and recovery

### 3.1 The state crash-recovery discipline (the cw_sentinel.py:136 case)

**Case text** (the `cw_sentinel.py:136-141` docstring): corrupted state (JSON parse failure / malformed key shape) → **fail-loud rc 9 refusal — the tool neither swallows nor rebuilds** (seen is an idempotent account · a silent rebuild would lose the no-re-report guarantee for failing events · the corrupted original file is left untouched). Exactly two recovery paths:

1. **Manual deletion** — the next round starts from zero state (equivalent to first attachment: state defaults to None / a missing file = zero-state start; the same segment in the `load_state :401-420` implementation).
2. **Explicit rebuild with `--rebuild-state`** — the only legal rebuild path: discard the existing seen and start from zero · a loud `STATE-REBUILD` marker on stdout (`run_sentry :1028-1033`) + `state_rebuilt=true` in the report (`:881-882`); **it must be given together with `--state-file`, otherwise rc=2** (no state, nothing to rebuild · `:991-993` · argparse `:1102-1106`).

selftest vector ⑪ (`cw_sentinel.py:1677-1711`): the corrupted file → rc 9 refusal + the original byte-for-byte untouched + no `STATE-REBUILD` marker / the same corrupted file with `--rebuild-state` → rc 0 · the failing events reproduce (seen discarded) · state is reborn as a valid new account / rebuild missing `--state-file` → rc=2.

**The same rule, generalized (an existing tool face)**: a malformed red_dispatch dedup state → rc 9 refusal, no rebuild (the same crash-recovery discipline as `cw_sentinel.py:136` · `red_dispatch.py:73-74`) — one discipline for both idempotent-account classes, seen and dedup.

### 3.2 JSONL two-generation rotation (the v40 mechanism)

**Mechanism** (entered at v40 · `更新账.md:3704`/`:3710`, "JSONL rotation (`--emit-max-bytes` · keep 2 generations · `seq` continues across generations without renumbering)"): `--emit-max-bytes N` checks the limit before appending (existing body bytes + new-line bytes > N) → **rotate first, then append** (`cw_sentinel.py:36-41` · `emit_event :490-501`):

```text
FILE.1 → FILE.2 (an existing FILE.2 is overwritten and discarded; two generations are kept) → FILE → FILE.1 → new FILE empty
```

- A single line itself over N = a line cannot be split · write into the empty slot (after rotation a single line may still exceed the cap · the next append rotates again first);
- rename failure → 9 (`rotate_emit :451-462`); rotation prints a loud marker on stdout + an `emit_rotations` count in the report (`:883-885`);
- **`seq` continues across generations**: the numbering base = body + the `.1`/`.2` line-count sum (`emit_seq_base :465-477`) — the rotated generations belong to one event stream · a consumer sorting by `seq` **recovers the global order across generations** (`cw_sentinel.py:40-41` · `ops-live-run-log:99`);
- Usage check: must be given together with `--emit` / N<1 → rc=2 (`:984-990`);
- selftest vector ⑫ (`cw_sentinel.py:1713-1751`): three runs over the cap → the `.1`/`.2` two generations really exist · `sorted(seqs)==[1,2,3]`, no renumbering across generations · missing `--emit` / N=0 → rc=2.
- Consumer-side linkage: the `render_events --dir` form can merge the body + the rotated generations (§2.3 · `seq` re-slots across generations).

### 3.3 The seen idempotent semantics (prefer duplicates over loss)

- **The state's three dicts** (`rocqwash-sentinel-state/1` · `cw_sentinel.py:132-135`): `repos.<repo>.seen_runs` (CI run id → conclusion/run_number/branch/family) / `ledgers` (`mtime_ns`+size · the same file changed is still treated as new) / `buildlogs` (byte offset · only complete lines count, guarding against half-line false hits).
- **A passing run is also recorded in seen** (the `poll_ci_repo` docstring: "a passing run is also recorded in seen (idempotent · a second run yields zero events and zero re-classification)" `:556-558` · passing emits no events `:589-590`) — a passing run is also a real observation (v47 recorded 25 passing runs into seen silently · `更新账.md:3895`).
- **Persistence ordering**: `save_state` at each round end (`:1046`) · **events are emitted before state is saved · prefer duplicates over loss** (the `run_sentry` docstring, `cw_sentinel.py:1024-1026`) — a crash in the extreme window between emit and save may re-report · the consumer reconciles by `seq`/state (the dedup responsibility sits on the consumer side · the watcher must never silently swallow events).
- **Field cases**: the v44 resident rounds 2-15 produced zero duplicate events (`--state-file` seen in effect · `更新账.md:3824`); the v47 second run was idempotent with zero new events · state seen matching 30/30 (`更新账.md:3895`).

---

## §4 Verified-run account citations (two field rounds · file:line direct)

### 4.1 The v44 resident run: 14 events, zero duplicates (`更新账.md:3814-3834`)

| Item | Ledger text (line) |
|---|---|
| Original command | `cw_sentinel.py --loop --interval 45 --max-rounds 15 --watch-repo hy7pc8gfmf-dotcom/ConstructiveWorld-Set --state-file /tmp/sentinel_v44_state.json --emit /tmp/sentinel_v44_events.jsonl` (report-only default · zero actions) — **`更新账.md:3820`** |
| Behavior | 15 rounds × 45s, run to completion (a 12-minute window) · the first round ran retro-triage over the full effort history, 30 historical runs classified one by one via `ci_triage --offline` — **`:3821`** |
| Events | **14 events** (family: A-content-red×9 / B-netred×1 / C-toolchain-break×1 / E-coqchk-skipped×1 / UNRECOGNIZED×2; action: fix-content×9 / rerun-after-stable-window×2 / restore-toolchain×1 / watch-only×2) — **`:3822`** |
| Classification agreement (the core check) | #280→A (the stale-foundation era) / #283→C (the dyld linkage-failure day) / #289→E (the upload DNS window) / #286 cancelled→B as collateral alongside UNRECOGNIZED — the classification matches the six-scene field record item by item — **`:3823`** |
| **Idempotency (this manual's §3.3 case)** | Rounds 2-15 produced **zero duplicate events** (`--state-file` seen in effect) = the resident steady-state proof — **`:3824`** |
| Evidence artifacts | `/tmp/sentinel_v44_events.jsonl` (14 JSONL lines) / report / logs — **`:3825`** |

### 4.2 The v47 first run: 33 events on the real repositories (`更新账.md:3895`)

- **Real CI signal-source verification**: `--once` over two repositories (Set 30 runs / 15 failing · Main 30/18) → **33 events** (A19/UNREC8/E3/B2/C1) — B-netred×2 exactly matches the known NETRED failing-build families Set#269/Main#22 = the classification ground truth reconciles (`更新账.md:3895`).
- 25 passing runs recorded into seen silently = a passing run is also a real observation; **the second run was idempotent with zero new events**; two `--loop` rounds over the real network produced zero new events (`更新账.md:3895`).
- Self-attestation face: all 33 JSONL lines valid line by line · schema `rocqwash-sentinel-event/1` · `seq` increasing · state seen matching 30/30 (the `更新账.md:3895` self-attestation column).
- **Token-level erratum, recorded as-is**: the `--loop-max` flag name was an erratum → the real flag is `--max-rounds` (`更新账.md:3895`) — §1.5's flag face follows this erratum.
- Account heads: the v47 account (recorded in the small hours · `更新账.md:3888`) · the v48 candidate, "sentinel resident overnight = the first run of the resident real-background JSONL stream form" (`更新账.md:3912`).

### 4.3 The v48 resident placement as observed (the live case for the §1.1 placement convention · first-hand read)

The `/Users/apple/Desktop/ConstructiveWorld/_log/sentinel_v48/` three-piece set, on disk and read first-hand:

- `events.jsonl` **33 lines** (all `ci-red` · family distribution A-content-red×18 / UNRECOGNIZED×8 / E-coqchk-skipped×4 / B-netred×2 / C-toolchain-break×1 · real run id/sha/branch · production form with a real `ts`);
- `report.json`: `mode=loop` · `round=1`;
- `state.json`: `rocqwash-sentinel-state/1` · both repositories' seen at 30/30 each (`hy7pc8gfmf-dotcom/ConstructiveWorld-Set` + `…-Main`).
- Recorded as-is: the same magnitude as the v47 account's 33 events with a slightly different family distribution (A19→A18 · E3→E4) — two independent real runs; the classification spectrum and the seen face follow each run's own state/report; this manual records both without merging or smoothing.

### 4.4 Related accounts and document index (all pre-existing)

| Anchor | Content |
|---|---|
| `更新账.md:3638` | the v37 to-do 2, "sentinel resident real run, `--loop` true background" = this manual's candidate source |
| `更新账.md:3650` | the unclog dry-run-by-default invariant (the tool-face anchor of non-negotiable constraint 2) |
| `更新账.md:3704`/`:3710` | the v40 account · JSONL two-generation rotation + state crash-recovery semantics entered (the §3.1/§3.2 mechanism anchors) |
| `更新账.md:3753` | the v41 third run 27/27 RC0 · `probe_chain` 190.7s (the real-compilation magnitude reference) |
| `更新账.md:3801` + `perf-profile:158-163` | v43 K=2 measured 101.916s = **1.87×** (the same 27-item candidate face corroborated across two runs · DS4 backfill) — the thermal-window scheduling reference for real compilation downstream of the watcher |
| `更新账.md:3814-3834` | the v44 resident 14-event account (§4.1) |
| `更新账.md:3844` | v45 `render_events` entered in the ledger (§2.3) |
| `更新账.md:3865` | v46 `red_dispatch` entered in the ledger (§2.4) |
| `更新账.md:3888-3914` | the v47 account · 33 events, the first real-repository run (§4.2) + the v48 candidate at `:3912` |
| `更新账.md:3999` | the v50 crash case: the resident watcher's round-10 `IncompleteRead` crash = the second class of transport-layer tool debt · supervisor-shell compensation deployed · the tool fix lands in v51 (the §1.6 case source) |
| `roadmap-v43-plus:30-38` | candidate ②: the `sentinel --loop` resident first run (value/dependencies/cost/risk + the verification method at `:38`) |
| `roadmap-v43-plus:13/:35` | the scoring quiet window: for observation-class candidates, zero events during the quiet period is also a legitimate observation, not a tool failure (the scheduling-face rule) |
| `ops-live-run-log:79-111` | the background watcher's runnable-state declaration (dependencies `:83-85` · launch command `:87-94` · JSONL usage `:96-100` · live smoke check `:102-111`) |
| `ops-realtime-service` (in full) | the v38-state upstream manual (command blocks / preset comparison / the real-tree live-run procedure §3 / the yield cooperation §4) — verbatim-compatible with this manual |
| `backend-sentinel.md` (in full) | embedded block ① canonical (command blocks §1 / consumer side §2 / exit codes §4 / pseudocode §5) |

---

## Appendix: the boundary of this manual, stated as-is

1. **Nothing newly built**: zero code changes, zero new tools, zero new flags — every command is a transcription of an existing canonical block (`README-cw` ⑤⑨ / `backend-sentinel` §1 §5 / `ops-realtime-service` §1 §3) or a verbatim transcript of a real run (v44/v48); the only "new face" is the §1.1 placement variable values (repository-external, ConstructiveWorld-side `_log/`, one directory per work stream), a normalized restatement of the live v48 placement, not a new mechanism (`--emit` / `--state-file` / `--json` were already fully parameterized · `cw_sentinel.py:150-151`).
2. **No-touch reconciliation**: the frozen eight / quad8 / `更新账.md` were untouched (the ledger is cited read-only); zero git write operations.
3. **Line-number currency**: line numbers anchor to the v47 `6217808` working-tree current state (concurrent development shifts them) — on a tool-face conflict, `--help` / the docstring is the authority (precedent: the `ops-realtime-service` provenance statement `:3-8`).
4. **Evidence grading**: §2.1's v48 real line and §4.3's placement observations = read first-hand in this work stream; §4.1/§4.2 = verbatim ledger citations (the original author ran them; not re-run here); §2.3/§2.4 tool semantics = docstring reads. The watcher `--selftest` 12-section vector face and the three-check regression history are in `ops-live-run-log` §3.4 (`:110`) — this manual did not re-run the selftest, recorded as-is.
5. **v1.0 addendum reconciliation (by the tooling agent)**: §1.6 is the addendum — the newly added deployment artifact `examples/sentinel_supervisor.sh` (item 1's "nothing newly built" refers to the watcher tool face and stays; this addendum does not move that conclusion; the deployment shell is a new artifact under the repository's `examples/`, not a tool) + a deployment-form smoke vector added to `cw_sentinel --selftest` (a test artifact, not the tool face · the tool's flags unchanged); §1.6's real crash-stack form and zero-state-loss evidence = first-hand reads in this work stream (direct reads of the report/state/events three-piece set + a live three-level `ps` read); the v51 tool-fix face is paraphrased from a read of a concurrently in-flight diff (its final form follows the v51 account · this manual does not speak for it).
