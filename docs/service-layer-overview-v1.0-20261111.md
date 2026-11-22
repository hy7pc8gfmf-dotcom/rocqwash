# service-layer-overview: service-layer overview v1.0 (November 11, 2026)

> Purpose.  One map of the active rocqwash capability surface: **four functions** (sanitize / shape normalization / failure diagnosis / clear blockages) × **three layers** (diagnosis v35 / orchestration v36 / service v37-v39) × the **unified entry** (`cw.sh`, twenty tools) × the **workflow integration interface** (cites the whitepaper). All content is taken from the tools' live state (each tool's `--help` and docstring · the `cw.sh` tool table · the ledger sections v35-v39 · read-before-write verified on November 11, 2026 · zero invented APIs); every flag citation in this document was machine-checked one by one against the emitted `--help` faces by the `tools/doc_lint.py` flag check (check ③).
> Interface.  Document face only. Division of labor: the quick reference is [`README-cw.md`](../README-cw.md) · the interface canon is [`workflow-integration-whitepaper-v1.0-20261111.md`](workflow-integration-whitepaper-v1.0-20261111.md) · the run procedures are [`ops-realtime-service-v1.0-20261111.md`](ops-realtime-service-v1.0-20261111.md); this document is the combined picture of the three and replaces none of them. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Grounded in the rocqwash v39 tree (`caa3a28`, clean working tree at writing time) and in the tool faces cited per section; no runtime dependency.
> Evidence.  Where this document and the tools disagree, the disagreement is a bug (same rule as CONTRIBUTING §1.5); the flag citations were re-verified by the `bash cw.sh doc-lint` three-check run at writing time (zero flag drift on this file).
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

## 1. One map (the active capability surface)

```text
┌───────────────────── workflow integration surface (external orchestration engine) ─────────────────────┐
│  dynamic workflow subagents / background bash tasks                              │
│  canonical embedded blocks: the three pieces under examples/workflows/ (backend watcher · single-step pushci · unclog loop)        │
│  the five interface disciplines (whitepaper §1): schema designated · exit codes 0/1/2/9 (a failing    │
│  result is data, not a tool failure) · once/loop dual mode · injector-testable offline · orchestration adds   │
│  no new engine — call the tools, read the JSON, never rebuild the verdict logic                                                    │
└──────────────────────────▲ JSONL event stream / JSON reports────────────────────┘
┌───────────────── service layer v37-v39 (live dynamics · where the four functions land)────────────────┐
│  sanitize = wash_shape + cure (the consumer-site cure canon pack v1.4 · 25 cures)                │
│  shape normalization = the five-wash pipeline (word-face / token / header / line-ending / anchor · plan/apply two stages)            │
│  failure diagnosis = the sentinel three-source live watcher + the cw-doctor four-domain health check (aggregating the three v35 diagnosis tools)    │
│  clear blockages = the unclog loop (probe collect → chain_graph root selection → cure apply → re-check)      │
│  close out = doc-lint, the three documentation-vs-implementation consistency checks                                  │
└──────────────────────────▲ subprocess orchestration (no new engine)────────────────┘
┌───────────────── orchestration layer v36 (single-command pipeline)─────────────────────────────┐
│  pushci five stages: preflight check (doctor + net-probe double check) → push → watch → heal →       │
│  verdict±merge (the seven-state verdict register over exit codes 0/1/2/9)                            │
└──────────────────────────▲ orchestration over the four v35 tools ─────────────────────────────┘
┌───────────────── diagnosis layer v35 + the v29-v32 foundation ──────────────────────────┐
│  diagnosis trio: doctor (dyld broken linkage) · net-probe (dual-probe stability window) · triage (five-family classification)│
│  operation tool: union (registry union · dry run by default)                               │
│  foundation: scan4 survey · probe check · chain chain-root graph · cure apply · sync-ledger ·        │
│        erasure · dual-scan · netname-normalize · select-audit               │
└───────────────────────────────────────────────────────────────────────┘
        unified entry: bash cw.sh <tool> (twenty tools + help · 1:1 passthrough · bash 3.2)
```

How to read it: an external workflow stands only at the top of the map; call the tools, read the JSON, route by the five disciplines; all four functions are performed by subprocess orchestration over the existing engines (no new engine; downward reuse of the v35 diagnosis layer and the v29-v32 foundation).

## 2. The four-function matrix

| function | tools | entry (cw.sh route → script) | one-line duty | default safe state |
|---|---|---|---|---|
| sanitize | `wash_shape` + `cure_applier` | `cw.sh wash-shape`→`tools/wash_shape.py` / `cw.sh cure`→`wash/cure_applier.py` | consumer-site curing: the cure canon pack (v1.4 · 25 cures · evidence-gated) supplies the fix, wash_shape orchestrates the apply surface | both tools dry run by default · nothing is written without an explicit `--apply` |
| shape normalization | `wash_shape` (five-wash engine: gate4 / scan_v4_token / cure_applier / comment_sweep / registry_union, all subprocess) | `cw.sh wash-shape`→`tools/wash_shape.py` | the canonical-form five-wash pipeline: word-face wash / token wash / header wash / line-ending wash / anchor wash · plan/apply two stages | the plan stage writes nothing · after apply the five washes rerun to verify → shaped/partial reported as they are · frozen-roster names refused failing |
| failure diagnosis | `toolchain_dyld_doctor` + `net_probe` + `ci_triage` (v38 aggregate: `cw_doctor`) | `cw.sh doctor` / `cw.sh net-probe` / `cw.sh triage` / `cw.sh cw-doctor` | environment linkage-failure diagnosis / network dual-probe stability window / CI failing-build triage over five families → four-domain aggregated health score + advice | all diagnose and advise only · never execute on the caller's behalf · a failing result is data, not a tool failure |
| clear blockages | `unclog` + `chain_graph` | `cw.sh unclog`→`tools/unclog.py` / `cw.sh chain`→`tools/chain_graph.py` | the blockage-record loop: probe collect → chain-root selection → cure apply → rescan/resprobe re-check → verdict | unclog dry runs by default (`--audit` read-only baseline · frozen-roster entries refused) · honest walls list a reason per root, no forced fixes |

## 3. Three-layer evolution (v35 → v36 → v37-v39 · all on November 11, 2026)

| layer | work stream (commit) | tool faces | layer duty |
|---|---|---|---|
| diagnosis layer | v35 (`acf9fe6`) | doctor · net-probe · triage · union, four new tools (+ the v29-v32 foundation scan4/cure/probe/chain/sync-ledger/erasure/dual-scan) | tooling the diagnosis methods of the November 10, 2026 effort: one tool each for the environment / network / classification / registry surfaces |
| orchestration layer | v36 (`4026051`) | pushci (subprocess orchestration of the four v35 tools · no new engine) | single-command pipeline: preflight check → push → watch → heal → verdict±merge · seven-state verdict register |
| service layer | v37 (`41e74b0`) / v38 (`c205ea0`) / v39 (`caa3a28`) | v37 = unclog · wash-shape · sentinel, three tools + the five interface disciplines; v38 = the cw-doctor four-domain health check + the `--on-red-preset` hookup + the `--audit` audit + the resilience layer + three embedded blocks + the whitepaper; v39 = doc-lint + cure_pack v1.4 + the header_map_v1 template library + relay e2e + the ops manual + nineteen entry completions | batch tools → live dynamic service: the four functions made resident + health check + documentation close-out |

## 4. Entry: the full cw.sh twenty-tool table

The unified entry `bash cw.sh <tool> [args...]` (repository root · arguments and exit codes pass through 1:1 ·
`bash cw.sh help <tool>` prints a one-line hint per tool):

| route | target script | layer / function | one-liner |
|---|---|---|---|
| `scan4` | `scan/scan_v4_token.py` | foundation | token-level qualified-name survey |
| `cure` | `wash/cure_applier.py` | foundation · sanitize | the consumer-site cure canon pack (dry run by default) |
| `probe` | `wash/probe_engine.py` | foundation | batch closure-compatibility probe |
| `chain` | `tools/chain_graph.py` | foundation · clear blockages | chain-root graph over merged ledgers |
| `sync-ledger` | `tools/ledger_sync.py` | foundation | probe ledger × state ledger merge and sync |
| `erasure` | `verify/erasure_classifier.py` | foundation | erasure-site classification advisor |
| `dual-scan` | `scan/dual_scan.py` | foundation | two-scanner differential run driver |
| `doctor` | `tools/toolchain_dyld_doctor.py` | diagnosis · failure diagnosis | dyld toolchain linkage-failure diagnosis (never executes fixes) |
| `net-probe` | `tools/net_probe.py` | diagnosis · failure diagnosis | network window probe (dual-probe stability window) |
| `triage` | `tools/ci_triage.py` | diagnosis · failure diagnosis | CI failing-build triage (five families + passing builds) |
| `union` | `tools/registry_union.py` | diagnosis | registry union operation (dry run by default) |
| `pushci` | `tools/pushci.py` | orchestration | push-to-CI single-command pipeline (seven-state verdict) |
| `sentinel` | `tools/cw_sentinel.py` | service · failure diagnosis | live dynamic watcher (JSONL event stream) |
| `wash-shape` | `tools/wash_shape.py` | service · sanitize / shape normalization | the shape-normalization five-wash pipeline |
| `unclog` | `tools/unclog.py` | service · clear blockages | the clear-blockages loop engine |
| `cw-doctor` | `tools/cw_doctor.py` | service · failure diagnosis | combined health check, four-domain aggregation |
| `doc-lint` | `tools/doc_lint.py` | service · close out | documentation-vs-implementation consistency, three checks |
| `netname-normalize` | `tools/netname_normalize.py` | foundation (v39 entry completion) | .v.v double-suffix name normalization |
| `select-audit` | `tools/select_audit.py` | foundation (v39 entry completion) | batch-selection auditor (grep dedup + Require-surface audit) |
| `help` |; | pseudo-route | total help / one-line hint per tool |

## 5. Service-face interface flag quick view (verbatim from the emitted `cw.sh sentinel --help` and five more · v39 current state)

| tool (entry) | key flags | notes |
|---|---|---|
| `cw.sh sentinel` (`tools/cw_sentinel.py`) | `--once` / `--loop --interval S --max-rounds N` / `--watch-repo ORG/REPO --branch B` / `--watch-ledgers DIR` / `--watch-buildlog FILE` / `--state-file F` / `--emit F` / `--json OUT` / `--on-red 'CMD'` / `--on-red-preset NAME --on-red-arg K=V` / `--injector F` / `--sleep-scale F` | the three signal sources combine freely; `--on-red` and `--on-red-preset` are mutually exclusive rc=2; report-only by default |
| `cw.sh wash-shape` (`tools/wash_shape.py`) | `--file A.v` (multiple allowed) / `--dir TREE` / `--only KINDS` / `--header-map M` / `--header-map-preset NAME` / `--anchor-src DIR` / `--apply` / `--json OUT` / `--events F` / `--loop --interval S --max-rounds N` / `--injector SCEN.json` / `--sleep-scale F` | `--header-map` and `--header-map-preset` share one slot, mutually exclusive rc=2; the plan stage writes nothing by default |
| `cw.sh unclog` (`tools/unclog.py`) | `--src DIR --world DIR` / `--candidates TSV` / `--chain-ledgers JSON...` / `--rounds N --top N` / `--apply` / `--audit` / `--workdir DIR` / `--guard PATH --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N` / `--events F` / `--loop --interval S --loop-max N` / `--injector DIR` / `--json OUT` | dry run by default; the read-only `--audit` baseline is mutually exclusive with `--apply`/`--loop` rc=2; `--guard*` passes through to the real-compiling cpu_guard |
| `cw.sh pushci` (`tools/pushci.py`) | `--repo-path DIR --branch B` / `--pre-scan-gate4` / `--merge` / `--max-heal N` / `--timeout S` / `--dry-run` / `--json OUT` / `--injector DIR --git-caller FILE` | the verdict seven-state register over 0/1/2/9; the two offline-drill flags must come as a pair |
| `cw.sh cw-doctor` (`tools/cw_doctor.py`) | `--json OUT` / `--registry PATH` / `--src DIR --sample N --world DIR` / `--worker PATH --donor DIR` / `--endpoints URL,..` / `--guard PATH` / `--timeout S` / `--workdir DIR` / `--injector DIR` | four-domain aggregated health score 0-100 · verdict healthy/degraded; diagnoses only, never executes on the caller's behalf |
| `cw.sh doc-lint` (`tools/doc_lint.py`) | `--repo DIR` / `--json OUT` / `--help-cap N` | three-check verdict consistent/drift (a failing result is data, not a tool failure) |

## 6. The workflow integration interface (canon: whitepaper §1)

An external workflow (dynamic-workflow subagents / background bash tasks) embeds by the **five interface
disciplines** and needs no knowledge of the tools' internals (per-tool mechanics and the command canon:
[`workflow-integration-whitepaper-v1.0-20261111.md`](workflow-integration-whitepaper-v1.0-20261111.md) §1;
the quick reference is the workflow-integration-interface section of README-cw.md; CONTRIBUTING §7 is the same source):

1. **JSON-in/JSON-out · schema designated · deterministic**; accounts are always emitted through `--json` (schemas
   rocqwash-sentinel/1 · rocqwash-shape/1 · rocqwash-unclog/1 · rocqwash-pushci/1);
   in loop mode the event stream goes out line by line as JSONL over `--events`; `--json` files are written with
   sort_keys and identical inputs rerun byte-identical.
2. **Exit codes 0/1/2/9 (a failing result is data, not a tool failure)**; first split the tool face by exit code (2 = fix the invocation ·
   9 = supply the missing target), then read the JSON and split the data face by verdict/kind.
3. **--once/--loop dual mode**; `--once` inlines the step; `--loop` is a background watcher with a round cap and self-stop;
   `--sleep-scale 0` is the offline determinism pin.
4. **--injector offline-testable**; drills and CI run the fully injected form + `--sleep-scale 0`: zero real network,
   zero real compilation; uncovered paths fail loud with 9 and never silently go live.
5. **Orchestration adds no new engine**; inside the tools everything is subprocess calls to existing engines; the workflow side follows the same law: call the
   tools, read the JSON, never rebuild the verdict logic.

Three canonical embedded blocks (copy whole · the samples came from real runs):

| embedded block | file | tool | scenario |
|---|---|---|---|
| ① backend watcher | `examples/workflows/backend-sentinel.md` | sentinel | a nohup resident three-source watcher → JSONL event stream + a consumer |
| ② single-step push CI | `examples/workflows/step-pushci.md` | pushci | `--dry-run` first for human review → real push → seven-state verdict routing |
| ③ unclog loop | `examples/workflows/loop-unclog.md` | unclog | dry run → human review → `--apply` → re-check · honest-wall routing |

## 7. Three typical chains (tool-grounded commands · flags verbatim from the emitted `--help` faces of `cw_sentinel` and the rest)

```bash
# chain 1: the CI failing-build repair chain (diagnosis layer → orchestration layer · same shape as README-cw)
bash cw.sh doctor --json dyld.json
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window
bash cw.sh pushci --repo-path . --branch feature/x --json pushci-report.json
bash cw.sh triage --repo ORG/REPO --run ID --logs
```

```bash
# chain 2: the live service loop (service layer · one beat per function · read the ledger before applying)
bash cw.sh sentinel --once --watch-ledgers ledgers/ --json sentinel-report.json
bash cw.sh cw-doctor --json doctor.json --registry order.txt
bash cw.sh unclog --src src/ --world world/ --audit --json audit-baseline.json
bash cw.sh wash-shape --file demo.v --json plan.json
# (apply only after human review releases it · the allowlist form and real-compile guard procedures are in the ops manual §3)
bash cw.sh wash-shape --file demo.v --apply --json shaped.json
```

```bash
# chain 3: the documentation close-out chain (v39 · self-attestation before delivering documentation changes)
bash cw.sh doc-lint --repo . --json doclint-report.json
```

## 8. Evidence and provenance

- Written at: rocqwash v39 (`caa3a28` · clean working tree). Every flag citation came from the same day's
  per-tool `--help` real runs (wrapped in cpu_guard · 13 tools rc=0: cw_sentinel / wash_shape /
  unclog / pushci / cw_doctor / net_probe / ci_triage / toolchain_dyld_doctor /
  registry_union / chain_graph / doc_lint / cure_applier / scan_v4_token),
  and was machine-checked by the `bash cw.sh doc-lint` three-check run (zero flag drift on this file).
- Written by the documentation close-out agent (tooling · docs); its territory was this file + the CONTRIBUTING §7 addition +
  the new CHANGELOG.md entry. `cw.sh` / `tests/run_tests.sh` / the README family belonged to the integration agent and were not touched;
  the frozen eight / quad8 / `更新账.md` were not touched (`更新账.md` read-distilled only).
- Line numbers drift under concurrent multi-agent work: flags and commands are canonical in each tool's `--help` and docstring;
  on drift, re-anchor by section name (same rule as whitepaper appendix B).
