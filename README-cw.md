# cw.sh — unified entry quick reference (rocqos (rocqwash) tool suite · 63 routes over 61 tools)

> **Language versions:** this file is the English-first version of the quick
> reference. The original Chinese full text is preserved verbatim in
> [README-cw.zh.md](README-cw.zh.md) (bilingual transition archive);
> the two versions cross-reference each other. Tool names, flags, paths and
> exit-code semantics are identical in both.

Purpose.  Quick-reference contract for `cw.sh`, the repository's one-command
  entry: the per-tool routing table, repair pipelines, the exit-code
  passthrough contract, and the v37 trio's workflow-integration interface.
Interface.  Documents `bash cw.sh <tool> [args...]`; arguments and exit codes
  pass through 1:1 via `exec`; the entry is a read-only routing layer.
Dependencies.  Requires only `bash` 3.2 and `python3` >= 3.9; paths resolve
  relative to the repository root; complements `cli/rocqwash`.
Evidence.  The table condenses each tool's documented invocation face; routing
  behavior is covered by `bash tests/test_cw_entry.sh` (also in
  `bash tests/run_tests.sh`).
Exit-codes.  0 pass; 2 unknown tool or passthrough usage error; 9 target script
  missing or passthrough missing-target condition; other codes pass
  through 1:1 per each tool's convention.

## Overview

`cw.sh` is the **one-command entry** for the twenty-five tools of the rocqwash
suite — the seven tools of the v29-v32 releases, the five tools of the
v35-v39 release, the three v37 tools, the v38 aggregate doctor, the v39 trio
(doc-lint / netname-normalize / select-audit), the v40 baseline-diff, the v45
render-events ledger renderer, the v46 `red-dispatch` / `audit` pair, the v47
registry-fix prescription applier, and the annotation-face normalization
linter (norm-lint). It lives at the repository root:

```
bash cw.sh <tool> [args...]
```

- **Zero configuration** — all paths resolve relative to the repository root
  (ROOT is derived from the script's own directory); the repo can be cloned
  or relocated anywhere;
- **Passthrough** — arguments and exit codes pass through 1:1 via `exec`;
  never rewritten, never simulated;
- **bash 3.2 compatible** — runs under the stock macOS `/bin/bash`; the entry
  itself is a read-only routing layer and writes nothing;
- **Complementary to `cli/rocqwash`** — the latter routes the pre-v29 seven
  modules (scan / names / wash / verify / seam / certify / watch). The
  v29-v32 tools live in module directories that already hold several generic
  entries each, which the module-level auto-router's ambiguity guard
  (exit 4) deliberately declines to guess — this entry covers them by
  explicit tool name. The v35-v39 five tools (doctor / net-probe / triage /
  union / pushci) land in the same multi-entry `tools/` directory and are
  routed here by explicit name for the same reason.

## Tool quick reference

| Tool | Target script | Purpose | One-line example |
|------|----------|------|----------|
| `scan4` | `scan/scan_v4_token.py` | token-level qualified-identifier census (qualified names / shadowing sources / tracking ids) | `bash cw.sh scan4 --file demo.v --json report.json --text` |
| `cure` | `wash/cure_applier.py` | consumer-cure canonical pack (**dry-run by default**, `--apply` writes) | `bash cw.sh cure --file demo.v --apply` |
| `probe` | `wash/probe_engine.py` | batch closure-compatibility probe (candidate list × world directory → rc-classified ledger) | `bash cw.sh probe --candidates list.tsv --src src/ --world world/ --out ledger.json` |
| `chain` | `tools/chain_graph.py` | multi-ledger probe merge → chain-root graph + TOP ranking | `bash cw.sh chain l1.json l2.json --md top.md --top 25` |
| `sync-ledger` | `tools/ledger_sync.py` | probe-ledger × status-ledger TSV merge sync | `bash cw.sh sync-ledger --probe ledger.json --ledger status.tsv --out new.tsv --report sync.json` |
| `erasure` | `verify/erasure_classifier.py` | extraction erasure-position classification advisor (per-position classification of a `.mli`) | `bash cw.sh erasure --mli out.mli --md-out ledger.md` |
| `dual-scan` | `scan/dual_scan.py` | dual-scanner cross-check (scan_v4_token × mac_stmt_scan, per-file diff) | `bash cw.sh dual-scan --dir src/ --out report.json` |
| `doctor` | `tools/toolchain_dyld_doctor.py` | dyld toolchain-breakage diagnostics (batch EXIT=134 surface; prints restore advice, **never executes it**) | `bash cw.sh doctor --worker PATH --donor DIR --json dyld.json` |
| `net-probe` | `tools/net_probe.py` | network-window probe (double-probe stable window; a single probe never authorizes emission) | `bash cw.sh net-probe --rounds 2 --interval 60 --stable-window` |
| `triage` | `tools/ci_triage.py` | CI red-run triage (five families + green-run classification spectrum; red is data, not tool failure) | `bash cw.sh triage --repo ORG/REPO --run ID --logs` |
| `union` | `tools/registry_union.py` | registry union surgery (main as base + true-exclusive tail insertion against the merge-base; **dry-run by default**) | `bash cw.sh union --base b --main m --branch x --kind order --json r.json` |
| `pushci` | `tools/pushci.py` | push-CI one-shot pipeline (five stages: preflight emission gate → push → watch → heal → verdict ± merge; orchestrated over the four existing tools by subprocess, zero new engines; seven-state verdict `success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run` mapping to exit codes 0/1/2/9) | `bash cw.sh pushci --repo-path . --branch feature/x --json report.json` |
| `sentinel` | `tools/cw_sentinel.py` | real-time watch sentinel (three signal sources — CI runs / ledger chain-roots / buildlog tokens — → JSONL event stream; once/loop dual mode; classification delegated to ci_triage; **no action by default**; `--on-red-preset` five presets, repeatable = chained in the given order with one failure continuing the chain — unclog/pushci/wash-shape/triage/cw-doctor, each honoring its tool's dry-run-by-default discipline; mutually exclusive with `--on-red`; side-effect actions require `--emit`, both channels share the same guard, rc=2) | `bash cw.sh sentinel --once --watch-ledgers ledgers/ --on-red-preset unclog --on-red-arg src=src/ --emit events.jsonl --json r.json` |
| `wash-shape` | `tools/wash_shape.py` | canonical five-pass shaping pipeline (lexical / token / header / EOL / anchor; plan is zero-write by default; `--apply` applies, then re-runs all five passes for verification; ③ header-pass template source probed three ways: `--header-map` per-file data > `--header-map-preset` named template library `tests/fixtures/header_map_v1.json` (effort-canon distillation, schema `rocqwash-header-map/1`) > env; same-slot explicit flags mutually exclusive, rc=2) | `bash cw.sh wash-shape --file demo.v --header-map-preset campaign_set_diamond --json plan.json` |
| `unclog` | `tools/unclog.py` | blockage-unclogging closed loop (probe collection → chain_graph chain-root pick → cure_applier application → re-check → verdict `unclogged\|wall\|rounds-exhausted\|audit`; dry-run by default; frozen-listed files refused loudly; `--audit` read-only clog baseline with a zero-write self-proof; mutually exclusive with `--apply`/`--loop`; `--probe-parallel K` threads probe parallelism through probe_engine `--jobs`, recorded in the timing section so runs over the same candidate set with different K remain comparable) | `bash cw.sh unclog --src src/ --world world/ --audit --probe-parallel 2 --json r.json` |
| `cw-doctor` | `tools/cw_doctor.py` | aggregate health check across four domains (dyld environment / net_probe network / registry anchor audit / clog probe_engine + chain_graph — per-domain subprocess orchestration of the existing tools → aggregate 0-100 health score + verdict `healthy\|degraded` + advice list; **diagnosis only, never executes**; red is data, not tool failure; schema `rocqwash-cwdoctor/1`; `--injector`-offline-testable) | `bash cw.sh cw-doctor --json r.json --registry order.txt` |
| `doc-lint` | `tools/doc_lint.py` | docs↔implementation consistency linter, three checks (① the tool table cross-checked across cw.sh's four places (header/usage/hint/case) + tools/ generic-entry reconciliation; ② CASES vs tests/README.md vs README.md count three-way check; ③ doc flag references vs each tool's real `--help` output, item by item; verdict `consistent\|drift`; red is data, not tool failure; schema `rocqwash-doclint/1`; `--repo` is the audited repo root, defaults to this repo) | `bash cw.sh doc-lint --repo . --json doclint.json` |
| `baseline-diff` | `tools/baseline_diff.py` | clog-baseline differ (two `unclog --audit` baselines in argv order old→new → `new_blocks`/`resolved_blocks`/`persistent` three lists + `score_delta`; four-state verdict `improved\|degraded\|stable\|incomparable`; a self-consistency precheck rejects hand-edited ledgers; timing excluded from comparison; red is data, not tool failure; schema `rocqwash-baseline-diff/1`; intake protocol in [examples/baselines/README.md](examples/baselines/README.md)) | `bash cw.sh baseline-diff audit-wash-20261101.json audit-wash-20261111.json --md diff.md` |
| `dispatch` | `tools/red_dispatch.py` | red-event router (sentinel red events → action presets; three presets `report-only\|suggest\|auto`; **report-only, zero execution by default**; suggest prints a copy-paste command block; auto executes only when explicit, under a 60s cap, rc≠0 recorded loudly without touching the exit code; dedup state + cooldown; all routes wired onto cw.sh's existing routes, zero new engines; family-A content-red is never auto-fixed — it emits a fix list; schema `rocqwash-red-dispatch/1`) | `bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json` |
| `audit` | `tools/registry_audit.py` | registry hygiene auditor (order.txt / _CoqProject dual-book **read-only** four-account output: duplicate rows / anchor-collision text / seq-form / malformed / missing anchors / orphans / live topology references + `--fix-plan` deterministic prescription with zero writes; **`--apply` does not exist**; keys and the anchor canon are reused from registry_union, zero re-invention; findings are data, always exit 0; schema `rocqwash-registry-audit/1`; live-tree runs belong to the repository owner session — at tool level only selftest/fixture evidence is in scope, per the v40 baseline protocol in [examples/baselines/README.md](examples/baselines/README.md)) | `bash cw.sh audit --order order.txt --project _CoqProject --live-src src/ --fix-plan --json audit.json` |
| `registry-fix` | `tools/registry_fix.py` | registry prescription applier (executes the `audit --fix-plan` prescription item by item; three prescription kinds DEDUP keep-first / anchor re-stamp / ORPHAN-ADD skip; **dry-run by default**; `--apply` writes with three post-write assertions (duplicates zero-residue / anchor-collision text zero-addition / orphans non-increasing) and rolls back on any failure; staging is fully in-memory, zero write; same-parameter discipline binds audit↔applier verbatim; schema `rocqwash-registry-fix/1`) | `bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --json fix.json` |
| `norm-lint` | `tools/norm_lint.py` | annotation-face normalization linter, report-only first form (machine-checks the prose faces of `.py`/`.sh`/`.md`: header banner + five-field block `Purpose.`/`Interface.`/`Dependencies.`/`Evidence.`/`Exit-codes.` verbatim; jargon mapping-table faces at word boundaries with backtick citations exempt; CJK residue warn per file; forbidden classes warn; header budget 30 lines; `*.zh.md` and `docs/zh/` archives skipped; findings are data — the exit code never escalates on them; default jargon map `docs/jargon-to-standard-mapping-v1.md`; schema `rocqwash-norm-lint/1`) | `bash cw.sh norm-lint --tree .` |
| `help` | — | master help; `help <tool>` prints the tool's one-line usage hint | `bash cw.sh help probe` |

Typical pipeline (find → cure → re-verify):

```
bash cw.sh scan4 --file demo.v --json census.json      # 1 census
bash cw.sh cure   --file demo.v                        # 2 dry-run: inspect the plan
bash cw.sh cure   --file demo.v --apply               # 3 apply (writes)
bash cw.sh scan4  --file demo.v --json after.json      # 4 re-scan should be zero
```

CI red-run repair chain (doctor → net-probe → pushci (includes watch + heal) → triage):

```
bash cw.sh doctor --json dyld.json                              # 1 dyld breakage diagnostics (batch EXIT=134 surface; restore advice printed, never executed)
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window   # 2 double-probe stable window (two consecutive all-endpoint rounds required before emission; a single probe never authorizes)
bash cw.sh pushci --repo-path . --branch feature/x --json report.json   # 3 one-shot pipeline (preflight re-runs doctor + net-probe as a double gate → push → watch CI → heal rerun → verdict ± --merge; seven-state verdict as in the table above)
bash cw.sh triage --repo ORG/REPO --run ID --logs               # 4 on verdict≠success: red-run triage (red is data, not tool failure; per-family actions)
```

> The manual legacy chain remains available standalone: `python3
> certify/push_gate.py window ...` for the push-window four criteria plus a
> bare `git push`. The pushci preflight emission gate re-runs only the doctor
> + net-probe gates (optionally `--pre-scan-gate4` for a header pre-scan) —
> the push-window four criteria (suite green / behind=0 etc.) are not part of
> that gate; that discipline remains with `certify/push_gate.py`.

Registry hygiene loop (audit → fix · two tools, two states · dry-run first, v47):

```
bash cw.sh audit        --order order.txt --project _CoqProject --live-src src/ --fix-plan --json audit.json   # 1 read-only audit: four-account output + deterministic fix-plan prescription (zero writes)
bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --json plan.json   # 2 dry-run rehearsal (per-item md5 accounting + skip list; zero writes; assertions NOT-RUN)
bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --apply --json fixed.json   # 3 apply (three assertions: duplicates zero-residue / anchor-collision zero-addition / orphans non-increasing; rollback on any failure)
bash cw.sh audit        --order order.txt --project _CoqProject --live-src src/ --json after.json   # 4 re-audit reconciliation (duplicates should be zero)
```

> `--audit-json` must come from a same-parameter `audit --fix-plan` run (the
> prescription line numbers are bound to the audited book surface; a
> different book is a usage error, exit 2); ORPHAN-ADD entries missing a
> template ordinal or md5, and anchor-missing findings, go to the skip list
> as-is for human adjudication (mechanical anchor fabrication is forbidden);
> audit exits 0 even with count>0 (findings are data, not tool failure).
> Live-tree `--apply` runs belong to the main session (selftest/fixture-level
> verification is fully in place).


## Tool quick reference: newer waves (through tag rw-v0.1.0-20261114)

| Tool | Target script | Purpose | One-line example |
|------|----------|------|----------|
| `netname-normalize` | `tools/netname_normalize.py` | Normalizes doubled `.v.v` suffixes (map can be emitted or applied with `--apply`) | `bash cw.sh netname-normalize --dir <value> --apply` |
| `select-audit` | `tools/select_audit.py` | Audits a batch selection against the tree's order file by full-table grep | `bash cw.sh select-audit --order <value>` |
| `render-events` | `tools/render_events.py` | Renders a JSONL event stream into a markdown ledger | `bash cw.sh render-events --events <value>` |
| `registry-regen` | `tools/registry_regen.py` | Regenerates contribution registration rows onto the merge-target line (base and contribution repos, refs, piece table, and path table parameterized) | `bash cw.sh registry-regen --base-repo <value> --apply` |
| `contrib-intake` | `tools/contrib_intake.py` | Contribution intake inspector: a read-only four-gate check that issues a verdict (contribution repo, base repo, refs, paths, and jargon map all parameterized) | `bash cw.sh contrib-intake --contrib-repo <value>` |
| `evolve` | `tools/evolve.py` | Self-evolution engine v1: drafts evolution proposals from watcher events and ledger faces (sentinel, suite, and registry flag families present) | `bash cw.sh evolve --draft-out <value> --suite-now` |
| `vacgen` | `tools/vacgen.py` | Lean vacuity probe skeleton generator with a four-layer shape-recognition engine (premise decomposition, taxonomy lookup, confidence scoring, tiered harness), including a zero-compile coverage preflight and a difficulty map (`--preflight-all`) | `bash cw.sh vacgen --in <value> --force` |
| `ci-triage` | `tools/ci_triage.py` | Fetches and triages logs of failing CI runs; `--offline` switches to local log input | `bash cw.sh ci-triage --offline <value> --logs` |
| `baseline-diff-facade` | `tools/baseline_diff.py` | Compares two baseline files and reports additions and removals (JSON and markdown output) | `bash cw.sh baseline-diff-facade <old> <new> --json <value>` |
| `exp-append` | `tools/exp_port.py` | Experience-bus append face (schema rocqwash-exp/1, four fields, idempotent seen-set; duplicates return the existing id and write nothing) | `bash cw.sh exp-append append --tool <tool> --points <text> --batch <batch>` |
| `mcp-server` | `tools/mcp_server.py` | MCP stdio server (tools/list carries 24 capabilities, net-gated faces deny-by-default, unknown methods answer -32601) | `bash cw.sh mcp-server tools/mcp_server.py` |
| `periscope` | `tools/periscope.py` | Six-source peripheral intelligence collector (watch list, arXiv queries, own issues into machine-checked intel entries bound to sha and time, collision detection) | `bash cw.sh periscope --help` |
| `ai-flavor` | `tools/ai_flavor.py` | Wording detection body: a 36-face battery (10 zh, 15 en stems, 8 sentence, 3 paragraph-initial) plus a separate em-dash battery (target 0); hits are data, not errors; pure exports `detect_text(text, word_map)` and `load_word_map(path)` | `bash cw.sh ai-flavor --file docs/report.md --json out/ai-flavor-report.json` |
| `ai-flavor-apply` | `tools/ai_flavor_apply.py` | Advisory apply face: writes only through the rewrite provider (handoff default zero-network; http leg default-deny under the env gate), zh ban faces never machine-written, budget cap per file per class via `--state`, rescan residue zero gates GREEN | `bash cw.sh ai-flavor-apply --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json` |
| `auto-round` | `tools/auto_round.py` | Auto round ledger body: admission per the autonomy gear, one verified commit per round, append-only ledger JSONL, round trailers plus lightweight refs, anchor rollback via drift archive then a single revert (no reset, no force, no push), salvage round-trip, oscillation alarm and a soft stop on unreviewed rounds | `bash cw.sh auto-round status --repo-root .` |
| `i18n-pipeline` | `tools/i18n_pipeline.py` | Pipeline orchestration body: six immutable operation signatures, P0 policy pre-check (refusal is a legal exit-0 ledgered outcome), P1 segmentation under the protection list, P3 four-linkage application, P6 append-only ledger closure gate | `bash cw.sh i18n-pipeline --manifest out/run.json --stage p1 --json out/segments.json` |
| `i18n-translate` | `tools/i18n_translate.py` | Model-site layer P2: handoff form default zero-network with ten-key (including policy_precheck_ref) ingest validation; http form optional default-deny with per-segment annotation and a NETRED ledger line per call | `bash cw.sh i18n-translate --segments out/segments.json --emit out/handoff.jsonl` |
| `i18n-verify` | `tools/i18n_verify.py` | P4 runs the mechanical verify instruments as subprocesses into one matrix; P5 emits the human ten-point form and ingests verdicts fail-loud; the engine never judges | `bash cw.sh i18n-verify --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json` |
| `jargon-apply` | `tools/jargon_apply.py` | Jargon-to-standard apply face over the 62-entry map: replace entries only, human rows listed never applied, guarded rows refuse by default, plan default zero-write, apply rescans to residue zero, idempotent | `bash cw.sh jargon-apply --tree docs --plan --json out/jargon-plan.json` |
| `termbase` | `tools/termbase.py` | Read-only terminology thin layer over the E3 seed: schema validation fails loud, exact-face lookup, zero network; the E3 net interface and DIY channel stay candidates of their own seed SPECs | `bash cw.sh termbase --selftest` |

### Exit codes

| Code | Meaning |
|----|------|
| 0 | pass |
| 2 | unknown tool (`cw.sh bogus`); or the tool's own argparse usage error / assertion failure (passthrough) |
| 9 | target script missing (`cw.sh xxx: missing <path>`); or the tool's own missing-target-file condition (passthrough) |
| others | each tool's own convention, passed through 1:1 (e.g. sync-ledger `1` = sync complete with findings; net-probe `1` = unstable window; doctor `1` = missing-libs; pushci verdict seal success/dry-run=0 · heal-exhausted/unstable/toolchain=1 · fix-content/gate4-block=2 · 9 = target missing; cw-doctor `1` = degraded, aggregate health score <90, red is data not tool failure; doc-lint `1` = drift, red is data not tool failure) |

## Workflow-integration interface (shared by the v37 trio — cleaning, shaping, diagnostics and unclogging driven by live workflows)

The three v37 tools (`sentinel` / `wash-shape` / `unclog`) share a five-point
interface discipline — workflows (dynamic-workflow subagents / background
bash tasks) integrate against it without needing each tool's internals:

**① --once/--loop dual mode**: `--once` runs a single inspection/loop pass,
emits the report and exits (for inlining inside workflow steps); `--loop
--interval S` runs as a long-lived sentinel (for background bash tasks;
`--max-rounds N` caps rounds, 0 = unlimited; unclog uses `--loop-max` for
loop count — rounds-exhausted is not terminal, rest for `--interval` and
start the next loop). wash-shape defaults to once (plan section writes
nothing); `--loop` explicitly enables sentinel mode and can combine with
`--apply` to apply per round. `--sleep-scale F` multiplies all sleeps by F
(selftest uses 0 = zero real sleep).

**② JSON-in/JSON-out + JSONL event stream**: `--json OUT` emits a
deterministic report (sort_keys; schemas `rocqwash-sentinel/1`,
`rocqwash-shape/1`, `rocqwash-unclog/1`; byte-identical on re-run with the
same input); in loop mode events append line by line to `--events FILE`
(JSONL, flushed per line; line schema `rocqwash-sentinel-event/1`; sentinel
event keys include `seq`, monotonic within the event stream — consumers sort
by seq to recover the global order).

**③ --injector offline testability**: the subprocess-call layer is canned
(sentinel = canned GitHub API table `rocqwash-sentinel-injector/1`, a cache
miss fails loudly with 9 and **never silently falls through to the real
network**; wash-shape = canned `{rc,stdout,report}` engine results; unclog =
canned probe/resprobe ledger scenario.json) plus `--sleep-scale 0` — zero
real network and zero real compilation in selftest; workflow drills / CI run
fully offline.

**④ Exit codes 0/1/2/9 (red is data, not tool failure; loud stdout)**:

| Code | sentinel | wash-shape | unclog |
|----|----------|------------|--------|
| 0 | inspection complete (CI reds / blockages are event data) | clean/shaped | unclogged |
| 1 | — (reds go to the event stream) | partial/plan-miss (incomplete shaping, reported loudly) | wall/rounds-exhausted (honest wall; never forced) |
| 2 | usage error (missing mode / all three sources absent / malformed repo) | usage error / frozen-file loud refusal / engine out-of-shape exit | usage error / malformed injection scenario |
| 9 | signal source unreachable (HTTP 4xx · injector miss · subprocess rc≠0) | path missing | fail-loud (path missing / tool red / frozen unreachable) |

**⑤ Canonical background-sentinel command lines** (copy verbatim into
workflow background tasks; the event stream is tailed by the main flow):

```
# Sentinel mode: ledger chain-roots + buildlog dual-source inspection, JSONL event stream, seen-idempotent (--state-file required for loop)
nohup bash cw.sh sentinel --loop --interval 60 \
  --watch-ledgers ledgers/ --watch-buildlog build.log \
  --state-file .sentinel-state.json --emit events.jsonl \
  --json sentinel-report.json >/dev/null 2>&1 &

# Shaping sentinel mode: per-round plan → apply → re-run five-pass verification (bounded by --max-rounds)
nohup bash cw.sh wash-shape --dir src/ --loop --interval 300 --max-rounds 8 \
  --apply --events shape-events.jsonl --json shape-report.json >/dev/null 2>&1 &

# Unclogging sentinel mode: five-step loop; wall/unclogged is terminal — stop and exit
nohup bash cw.sh unclog --src src/ --world world/ --loop --interval 600 --loop-max 8 \
  --events unclog-events.jsonl --json unclog-report.json >/dev/null 2>&1 &
```

**⑥ Three canonical workflow embed blocks** (inline workflow-script steps,
all offline-injectable forms):

```
# pushci embed block (emission gate → push → watch → heal → verdict; seven-state seal routed by exit code)
bash cw.sh pushci --repo-path . --branch feature/x --json pushci.json
case $? in 0) : ;; 1|2) bash cw.sh triage --repo ORG/REPO --run ID --logs ;; esac

# unclog embed block (unclogging closed loop; verdict routed by exit code; dry-run first to read the wall account)
bash cw.sh unclog --src src/ --world world/ --json unclog.json
case $? in 0) echo unclogged ;; 1) echo "wall/rounds-exhausted: read the wall account in unclog.json for human adjudication" ;; esac

# wash-shape embed block (canonical five-pass shaping; zero-write plan first; human review, then --apply for both stages)
bash cw.sh wash-shape --file demo.v --json plan.json      # plan stage (both rc 0 and 1 carry a report)
bash cw.sh wash-shape --file demo.v --apply --json shaped.json   # apply + re-run verification
```

> The three tools orchestrate rather than re-invent: sentinel delegates
> classification entirely to `ci_triage` (direct subprocess call) and
> chain-roots entirely to `chain_graph`; wash-shape runs all five passes by
> subprocess (gate4 / scan_v4 / cure_applier / comment_sweep /
> registry_union); unclog runs all five steps by subprocess (probe_engine /
> chain_graph / cure_applier / scan_v4_token / frozen8). A workflow calling
> them calls every existing engine.

**⑦ v38 notes (preset / audit / resilience layer)** — the trio's
interface extends the five-point discipline above:

- **preset**: sentinel gains `--on-red-preset NAME` (canned red-event
  actions; a preset is template sugar; the v41 data-driven expansion grows
  the preset table to five: `unclog` = dry-run unclogging (**no --apply**;
  apply only after human review), `pushci` = `--dry-run`, plan only,
  `wash-shape` = plan only (**no --apply**; the plan writes nothing),
  `triage` = re-triage of the red run (repo/run substituted into the event),
  `cw-doctor` = all-defaults checkup — each preset automatically honors its
  tool's dry-run-by-default discipline; **repeatable = chained**, executed
  in the given order with one failure continuing the chain without touching
  the sentinel exit code (one ledger entry per action); expansion goes
  through the **same executor** as `--on-red` (60s cap, rc≠0 does not touch
  the sentinel exit code, zero new execution paths); required parameters
  pass through `--on-red-arg K=V` (the chained parameter surface = the union
  over the chain); `{emit_dir}` resolves to the directory of `--emit`;
  **mutually exclusive** with `--on-red` (both given → rc=2, fail-loud, no
  silent pick); **side-effect actions require the event stream** — plain
  `--on-red` and preset forms without `--emit` are both guarded, rc=2 (the
  v41 destructive-matrix S2 criterion, now standing). wash-shape extends the
  same way (v39 round): the ③ header-pass template source gains
  `--header-map-preset NAME` (named templates; `tests/fixtures/
  header_map_v1.json` effort-canon distillation library, schema
  `rocqwash-header-map/1`; placeholders must bind to the target file's own
  Require surface and existing header verbatim — any unbound placeholder is
  plan-miss, never fabricated; mutually exclusive with `--header-map`
  in the same slot, rc=2; template-source probe order `--header-map` >
  preset > env).
- **audit**: unclog gains `--audit`, a read-only clog baseline (one
  dry-run probe collection pass → chain_graph → baseline report;
  `final.verdict=audit`, exit 0 — the reds are baseline data, not tool
  failure; cures always 0 = zero applications, zero re-checks); the
  **zero-write hard guarantee** = an md5 inventory of all files under
  `--src`, self-verified identical before and after the run (any violation
  fails loudly with 9; a contaminated baseline is never emitted);
  mutually exclusive with `--apply`/`--loop`, rc=2; the timing section's
  measured wall clock is the report's only non-deterministic section — v41
  adds `--probe-parallel K`, threading probe parallelism through probe_engine
  `--jobs` (jobs dimension recorded in the timing section; runs over the same
  candidate set with different K stay comparable; with `--guard`, K≤2 is
  advised for the thermal self-limit).
- **resilience layer**: the CI GET 403/429/5xx exponential-backoff retry is
  extracted into the pure-function shared piece `tools/_http_backoff.py`
  (shared by `ci_triage` / `cw_sentinel` / `pushci`; `--retry-max` default 3;
  Retry-After seconds header honored; 4xx semantic surface never retried);
  net-probe gains `--jitter/--seed` (a small random pre-probe delay per
  endpoint, spreading aligned retry storms; additive-key default = zero
  behavior change); pushci gains `--timeout` (a hang cap on real
  subprocesses); sentinel gains `--subproc-timeout` (hang cap on orchestrated
  subprocesses) — **injector-canned paths never retry and never touch the
  real network** (offline-testability discipline). Per-tool details are
  anchored in their docstrings and `--help`.

**⑧ Three canonical embed blocks (examples/workflows/ · copy-paste ready) +
integration whitepaper**:

- Embed block ① background sentinel:
  [examples/workflows/backend-sentinel.md](examples/workflows/backend-sentinel.md)
  (the ⑤ background-sentinel command block, copy-paste ready + JSONL
  consumer in grep/python3 forms + exit-code branch table +
  dynamic-workflow embed pseudocode)
- Embed block ② single-step CI push:
  [examples/workflows/step-pushci.md](examples/workflows/step-pushci.md)
  (the ⑥ pushci embed block expanded: `--dry-run` first → real push →
  seven-state verdict branch table + offline drill form)
- Embed block ③ clog unclogging:
  [examples/workflows/loop-unclog.md](examples/workflows/loop-unclog.md)
  (the ⑥ unclog embed block expanded: dry-run → human review → `--apply`
  → re-check four criteria + honest-wall cause routing table)
- Integration whitepaper:
  [docs/workflow-integration-whitepaper-v1.0-20261111.md](docs/workflow-integration-whitepaper-v1.0-20261111.md)
  (main-session defer mode / background-task topology / two gates side by
  side — push-window four criteria × emission gate)
- Realtime service ops runbook:
  [docs/ops-realtime-service-v1.0-20261111.md](docs/ops-realtime-service-v1.0-20261111.md)
  (background-sentinel standard commands and JSONL consumption / preset-wired
  unclog full-chain three-criteria e2e = `tests/test_relay_e2e.py`; tmp
  injection drill transcripts on file; on conflict with a tool's `--help`,
  the tool is authoritative)
- Service-layer overview (v40):
  [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
  (three chains, one map + tool-surface index)
- Clog-baseline intake protocol (v40):
  [examples/baselines/README.md](examples/baselines/README.md)
  (`unclog --audit` baseline naming convention `audit-<domain>-<yyyymmdd>.json`
  / non-deterministic-timing note / baseline-diff reading and red-line
  discipline)

**⑨ Red-event routing embed block (v46 · red_dispatch pairing example ·
sentinel red events → action-preset routing)**:

```
# Sentinel mode → router wiring (--on-red template pairing example; <json> is the
# on-disk path of the --emit event stream — on every red event the sentinel feeds the
# whole event stream to the router; the suggest tier executes nothing and prints a copy block)
bash cw.sh sentinel --once --watch-ledgers ledgers/ --emit events.jsonl \
  --on-red 'python3 tools/red_dispatch.py --event-file <json> --preset suggest'
```

Single-step direct call (without the sentinel; adds one routing pass over an existing
event stream; report-only, zero execution by default):
`bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json`

> routes rather than executes: the five routes (B/E families →
> pushci rerun · family A → manual-fix-note, never auto-fixed, emits a
> fix list · family C → doctor · blocking → unclog · build-signal →
> wash-shape) are all wired onto cw.sh's existing routes, zero new engines; the
> three-tier preset defaults to report-only, zero execution (red is data);
> auto runs only when explicit (60s cap; rc≠0 recorded loudly without
> touching the exit code; dedup state + cooldown); when paired with the
> sentinel's `--on-red`, the `{family}/{run}/{repo}` placeholder substitution
> semantics are unchanged — the router reads the full event stream itself.

## Design contract

All paths are resolved relative to the repository root from the script's own
location (no hardcoded paths; the repo can be cloned anywhere); arguments and
exit codes pass through 1:1 via `exec` (fail-loud, never rewritten); requires
only `bash` 3.2 and `python3` ≥ 3.9, no third-party dependencies; the entry
itself is a read-only dispatcher and writes nothing. `bash cw.sh help <tool>`
prints a one-line usage hint per tool. It complements the existing
`cli/rocqwash` router, which covers the pre-v29 modules — the v29-v32 tools
live in directories with several generic entries each, where the module
auto-router's ambiguity guard declines to guess, so this entry routes them by
explicit tool name. Self-test: `bash tests/test_cw_entry.sh` (also part of
`bash tests/run_tests.sh`).

> **Chinese quick reference, full text** (original archive · bilingual transition
> archive): [README-cw.zh.md](README-cw.zh.md).
