> **rocqwash** — operating as **rocqos**, the *Rocq operations suite*: a self-evolving operations layer for Rocq-based constructive-proof repositories. Built on Rocq 9.3. The "rocq" prefix is used with attribution to the [Rocq prover](https://rocq-prover.org) and its community; rocqos is an independent operations layer, not affiliated with Inria and not part of the Rocq distribution.

# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine
> English main page · Chinese mirror: [README.zh.md](README.zh.md) · English project page: [README_EN.md](README_EN.md)

[![CI](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml) [![macOS advisory](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml) [![certification](https://img.shields.io/badge/certification-machine--checked-brightgreen)](docs/ci-whitepaper-recursive-era-v1-20261116.md) [![Rocq](https://img.shields.io/badge/Rocq-9.3.0-blue)](https://rocq-prover.org) [![tag](https://img.shields.io/badge/tag-rw--v0.1.1--20261117-blue)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/tree/rw-v0.1.1-20261117)

> Purpose.  Repository entry document: it states what rocqwash is, how the toolchain is organized, and how to run the first scan, wash, verification, and certification commands.
> Interface.  Documents the `cli/rocqwash` entry verbs and the direct `python3` invocations shown verbatim in the fenced command blocks; names `tests/run_tests.sh` as the self-test suite entry and `make -C examples demo` as the full-chain demo.
> Dependencies.  Python 3 (>= 3.9, standard library only) for every command shown; a Rocq/Coq 9.x toolchain only for the compile-verification pieces.
> Evidence.  Every command block is runnable from a fresh clone; the self-test suite (`bash tests/run_tests.sh`, exit 0 = all passing) is the pass/fail authority for the stated case counts; component claims link to the owning tool faces.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. Where proof-unblocking is concerned, it replaces probabilistic guessing with mechanically verifiable checks: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: what can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.

## Status Snapshots

> **Service layer overview**: [service layer overview v1.0](docs/service-layer-overview-v1.0-20261111.md) (three chains in one map, plus the tool-face index) · [service effort total v1.0](docs/rocqwash-service-campaign-total-v1.0-20261111.md) (cumulative report of the seven work streams, v35-v41) · [ops live run log](docs/ops-live-run-log-20261111.md) (verbatim record of the three-gate conclude/close) · [roadmap v43+](docs/roadmap-v43-plus-20261111.md) (candidate pool — decision material, not a scheduling order; items ①②④⑦ already executed in the v47 and v48 addenda below; ③⑤⑥⑧ await designation) · [resident watcher ops manual v1.0](docs/ops-sentinel-长驻手册-v1.0-20261112.md) (deployment, usage, rotation and recovery) · [multi-repo Main adaptation survey](docs/勘形-multi-repo-Main仓适配-20261112.md) (roadmap item 7, Main repository CI shape survey; adaptation grading 4 ready-to-use / 3 minor-change / 2 medium-change)

> **v55 snapshot (November 13, 2026, signal-to-task-brief generator round, constitution law-three body)**: tool `tools/evolve.py` (in substance a signal-to-task-brief generator; the module-title face `autonomous evolution engine v1` keeps its name pending rename adjudication; schema `rocqwash-evolve/1`: the harvest→derive→draft pipeline with the autonomous-execution gate kept at human review: harvest five signal classes by subprocess of the existing engines (norm-lint fitness vs the v53 baseline with the frozen surfaces excluded / sentinel one-shot dual-repo new ci-red events with seen-idempotence / suite last state / registry-audit accounts with increment / maintained UNRECOGNIZED sentinel events) → derive fixed-rule scored candidates (impact × evidence / effort, evidence clamped 10) plus genetic standing candidates from the ledger lineage → draft the constitution three-law-preamble task brief to `--draft-out`; **draft-only spawn gate: never executes a candidate, never writes the repository**; adverse signals are data, exit 0/2/9); `--selftest` rc=0 (ten PASS vector groups); round-one live cycle (demo record `docs/演示-evolve首轮-20261113.md`: real signals S1 norm account / S2 sentinel dual-repo / S3 registry audit, zero mocks; task-brief draft `docs/evolve-draft-cycle1-20261113.md`: candidates C1–C5, TOP1 = C1 red-triage score 12.0, curable-error reduction rate honestly 0.00% (frozen ledger excluded, error 1960→1960) plus the curable-basis measurement rule registered for the engine spec; companion engine draft `docs/draft-evolve-v55-20261113.md`; ops manual `docs/ops-evolve-手册-v1.0-20261113.md`: variation/selection/inheritance mapped to implemented machinery, draft-only safety invariants); suite hook-up (`t_evolve` case in `tests/run_tests.sh` · cw.sh routes `evolve`, six-place sync, 28 tools · `doc_lint` `DEFAULT_HELP_CAP` 27→28 on the registered-tool precedent · counts synced to 63 in `tests/README.md` + `README.md`); three-gate close: doc_lint consistent (help_run=28/28·drift=0) / suite passing twice (81 cases 62 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` pass (cw.sh + run_tests.sh); norm_lint tree re-run against the v53 baseline: 152 files error 2441→2449 warn 1036→1106: the +8 error delta sits entirely on the frozen ledger's committed v54 append (`更新账.md` byte-identical to HEAD this turn, zero writes); the two new engine/suite faces (`tools/evolve.py`·`tests/test_evolve.py`) carry 0 error 0 warn, the four new doc faces carry 0 error (warn = CJK residue data per the account-doc convention).

One-line snapshots, newest first; each links the docs/ faces of its round.
The full entry prose lives in the git history of this file (CHANGELOG.md
carries v35-v39, v53, and v58-v66).

- **v57 (November 13, 2026) — evolve cycle-2 execution round**: six tool faces Englished per the annotation standard card (combined norm_lint error mass 111→0) and two triage evidence-note vectors added with the unrecognized-failure class kept un-inflated; norm_lint v3 baseline landed (`docs/norm-lint-baseline-20261113.{json,md}`); documentation check, full suite, and shell-syntax checks all passing.
- **v56 (November 13, 2026) — nine-tool translation close**: nine tool faces translated with the interface boundary machine-verified zero-change (AST comparison, 9/9 identical) and 7 new zh archives; norm_lint reconciliation error 2441→2377 against the v53 baseline (`docs/norm-lint-baseline-20261113.json`).
- **v55 (November 13, 2026) — signal-to-task-brief generator**: `tools/evolve.py` (draft-only gate: it never executes a candidate and never writes the repository); first live cycle on real signals (`docs/演示-evolve首轮-20261113.md`).
- **v54 (November 13, 2026) — contributor-isolation tooling**: protocol `docs/contrib-isolation-protocol-v1.0-20261113.md`, the read-only four-gate intake inspector `tools/contrib_intake.py`, and the dry-run-by-default prescription regenerator `tools/registry_regen.py`; pipeline live-run on Set PR#48.
- **v53 (November 13, 2026) — annotation-face normalization foundation**: annotation standard card v1.0, jargon-to-standard mapping table v1, the `tools/norm_lint.py` checker, and the first repository-wide baseline account (`docs/norm-lint-baseline-20261113.{json,md}`); full entry in [CHANGELOG.md](CHANGELOG.md).
- **v52 (November 13, 2026) — Main survey and first live closed loop**: Main new-content survey; a CI regression classified and then auto-recovered by a sibling commit in ≈20 minutes with zero manual steps (`docs/判例-R3复发-route2tierA自愈-20261113.md`); a watcher-event consumption drill.
- **v51 (November 12, 2026) — watcher resilience round**: transport-layer bounded retries with backoff and per-source fallback, the triage E-variant conclusion-position check, and the supervisor-shell deployment shape (`examples/sentinel_supervisor.sh`).
- **v50 (November 12, 2026) — 14-event classification cross-validation**: triage tool against manual review, run-level agreement 5/8 and row-level 10/14; every disagreement registered, the recognized-failure spectrum deliberately not inflated.
- **v49 (November 12, 2026) — Main repository adaptation round**: Main CI shape fixtures with triage/pushci consumption faces, the Main full-history triage ledger (369 runs), and service effort total report v2.0 (`docs/rocqwash-service-campaign-total-v2.0-20261112.md`).
- **v42 (November 11, 2026) — conclude/close ledger round**: total report, drill record, and roadmap landed in docs/ (linked in the overview line above); baseline green (documentation consistency drift=0, destructive-surface matrix 17/17, full suite zero-failing).


## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## Terms Used in This Page

The vocabulary below is used throughout without further explanation. Fuller
definitions: [docs/en/architecture.md](docs/en/architecture.md) and
[README_EN.md](README_EN.md) (the "What it is" and "Why" sections).

- **Prop leakage** — a statement still stated over the `Prop` sort instead of a Set-carried predicate form; the scanner flags such lines as RED stations. `Set` and `Prop` are mutually exclusive sorts in Coq/Rocq type theory, so the distinction is a mechanical fact, not a style preference.
- **wash** — rewriting flagged statements onto canonical Set-carried forms by exact-string, count-asserted replacement (Qlt→QltT, Qle→QleT', ==→QeqT, …); idempotent by construction, so a second run changes nothing.
- **QeqT / QltT / QleT'** — the Set-carried predicate forms the wash targets; Qeq/Qlt/Qle are the standard Prop-carried originals. A QeqT goal rejects Qeq-equality rewriting — a corollary of the Set/Prop mutual exclusion.
- **-face** — the region of a `.v` file a tool operates on: statement-face = statement lines, annotation-face = comment/header text, as opposed to proof bodies.
- **station** — a reported location: the (name, line) pair a scanner or probe lists for human adjudication; RED station = flagged as Prop leakage.
- **probe** — a trial compile: candidate files are compiled with `rocq c` inside a world and triaged by exit code into washable / born-clean / red-cause classes.
- **gate4 / gate6 / gate7** — numbered checkpoints on the canonical path: gate4 = comment hygiene; gate6 = census wrapper (`verify/verify_gate6.py`); gate7 = English adaptation (CJK→0 plus the five-field header cap).
- **W13** — the generation-gap seam probe (`seam/seam_probe.py`): classifies why a washed statement still fails, by four mechanism fingerprints, each mapped to a prescription.
- **R4** — the three-source extraction audit: bare full-extraction magic count, probe dual-face, and five-pattern grep must all come back clean (the extraction side is currently partial — see the honest-boundaries register in README_EN.md).
- **N=N** — the name-table assertion: the extractor reads N statement names before the wash and asserts the washed file declares exactly those N names in the same order (exit 2 on mismatch).
- **world** — a self-contained copy of a source tree with its own dependency closure; probes compile against a world, and multi-world (UNION v2) manifests freeze per-world md5 trees.

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push (push pinned to a fixed remote IP) + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: 25 deterministic idempotent rewrite patterns (measured at pack v1.4.1: the legacy five plus statement-face, S07-lineage and CI-extraction-defect families), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine; the per-pattern inventory is the pack itself (`wash/cure_pack.json`) | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |
| `tools/pushci.py` | Push-CI one-shot pipeline orchestrator: five stages (preflight emission gate, push, CI watch, heal, verdict with optional PR merge), seven-state verdict (`success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run`), exit codes 0/1/2/9; orchestrates the v35 four tools via subprocess, zero new engines; offline-injectable (`--injector`/`--git-caller`/`--sleep-scale`); per-stage detail in `tools/pushci.py --help` and the v36 addendum below | Deterministic state machine over mechanical gates; LLM cannot be trusted to decide emission windows or auto-heal policies |

## Repository Layout

```
rocqwash/
├── cli/rocqwash          # 统一 CLI 入口 — unified CLI entry (scan/names/wash/verify/seam/certify/watch)
├── docs/
│   ├── zh/architecture.md  # 架构文档（中文）— architecture doc (Chinese)
│   └── en/architecture.md  # 架构文档（英文镜像）— architecture doc (English mirror)
├── CONTRIBUTING.md       # 贡献指南（流程/代码规范/测试要求/cpu_guard 使用说明）
├── examples/             # 全链演示样例 + Makefile — single-file full-chain demo (scan→names→N=N→wash→verify)
├── scan/  names/         # 已实现通用逐件工具（mac_stmt_scan.py / scan_v4_token.py / dual_scan.py）— implemented generic tools
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + work-stream tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + work-stream tools
├── verify/               # verify_vo.py four-point pass criterion + 战役验证工装 — four-pack green verdict + work-stream verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（92 例）/ CI 工作流占位 — test suite (92 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> Status snapshot November 1, 2026 (inspection-and-polish pass rqsup4): `scan/`, `names/`, `tools/cpu_guard.sh`,
> `cli/`, `examples/`, `docs/`, `tests/` (34-case self-test suite) implemented and live-tested; `wash/`
> (`wash_engine.py` ledger-based wash engine + `_abl1_wash.py` effort piece + `world_hook.py` world-baseline validation hook),
> `verify/` (`verify_vo.py` four-point pass criterion + effort verify tooling + `verify_gate6.py` gate6 thin wrapper),
> `seam/` (`seam_probe.py` W13 four-mechanism fingerprint probe), `certify/` (`freeze_manifest.py`
> two-tier freeze manifest + `push_gate.py` push-window four-criteria/UNION v2 deep piece, agent rqwash2, + `frozen8.py`
> frozen-eight registry machine check), `watch/`
> (`watch.py` CI monitoring / pin-IP push / ls-remote confirmation, zero-route structural guarantee), `tools/`
> (`select_audit.py` selection auditor), `recipes/` (`S07_projection_reanchor_E5.md` +
> `ENBIG7_same_domain_collision_PW1.md`, two precedent prescription pieces), `wrapper/`
> (adapter family: gate7 probe chain `coqc_shim.sh` + `gate7_probe.sh`, cpu_guard pass-through
> `guard.sh`, scan station wrapper `scan_station.py`, agent rqadapt, three-precedent acceptance station
> `precedent_station.py`, rqsup4) all landed;
> the `verify/` unified entry is concluded/closed (explicit sub-verb routing `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`,
> rqadapt landed the three sub-verbs on October 31, 2026; a fourth inspection pass added verify_gate6 on November 1, 2026); `certify/`
> carries the same explicit routing `cli/rocqwash certify freeze|push_gate|frozen8` (a fifth inspection pass added
> frozen8 on November 1, 2026) — the frozen pieces zero-change; the R4 extraction-side three sources remain open work.
> v30 addendum (November 3, 2026, probe-effort tooling round): `wash/probe_engine.py` batch closure-compatibility
> probe (tool citation) / check (generic sense) engine + `tools/chain_graph.py` multi-ledger chain-root graph + `tools/ledger_sync.py`
> probe × status-ledger synchronizer (E1 dedup / E3 ghost / column validation fail-loud) — generalizing the W13/W25/ledger
> v2 three prototypes 1:1, all paths parameterized with zero hard-coding; self-test suite grown to 40 cases, all passing.
> v31 addendum (November 3, 2026, shape-normalization effort field-precedent tooling round): `wash/cure_pack.json` v1.1
> five patterns → fourteen (Qle/Qlt carrier-face downshift, two forms · refl bridge opener · Import-shadow direct-face two variants
> exclusive-group fail-loud · NatLe premise lift + intros-tail-guarded drop wrap) +
> `wash/cure_applier.py` face-regex domain engine (face/proof domain triggers · per-face token guards ·
> file-level preconditions) + `wash/comment_pack.json` + `comment_sweep.py` comment-domain sweep
> sidecar (nested-comment-and-string-aware state machine · flag-word exchange · data-driven header replacement · w7 code-line full-equality
> projection idempotence assertion) + `tools/ledger_sync.py` v2.1 (items subkey shell recognition + bare dict metadata
> key loud filtering + GEN-DIVERGENCE two-generation divergence surfaced — divergence precedence written down: the kept generation = the generation the downstream account
> basis ranking consumes, the dropped generation noted but never discarded); self-test suite grown to 41 cases, all passing.
> v32 addendum (November 3, 2026, S07 lineage adaptation-pattern tooling round, W66 support-agent proposal implemented):
> `wash/cure_pack.json` v1.1→v1.2, fourteen → nineteen patterns (cure32_A parameterized-shell removal with a
> :=-binding-right guard / cure32_B notation-rebind line-insert engine / cure32_C projection-bridge
> bare-name form over the face+proof domain / predicate-face convergence token_map — rename targets must take the consuming supply lemma's conclusion-face
> same constant names · delta-equivalent renamed compiles pass but extraction inserts Obj.magic / binder-shell report-only
> station — the manual-operation jurisdiction reports a station, the post-operation station count returns to zero) + `scan/dual_scan.py` two-scanner differential comparison driver
> (scan_v4 + mac_stmt_scan dual scan × per-file difference report only_v4/only_stmt) + cure_applier
> tool fix (exclusive-group conflicts + --json path report write / persist to disk, rc=4 documented value);
> self-test suite grown to 42 cases, all passing (gated S07 compile arc: failing → mechanical cure → binder operation → passing →
> extraction Obj.magic 0/0).
> v34 addendum (November 4, 2026, the CI #178 extraction-face defect-family reverse-revision round): `wash/cure_pack.json`
> v1.2→v1.3, nineteen → twenty-four patterns — the two defect families finally established in the task instruction enter the cure: E3 generic-interface instantiation
> (cure34_E3_use_station_spec: abstract-carrier application stations rewritten to a specialized shim call + cure34_E3_spec_shim
> line-insert generating the concrete-carrier intermediate Definition after the last Import; the shim body keeps the specialized abstract
> application, face_exclude protects the body against second-pass self-entanglement) + E2 record polymorphic field (cure34_E2_field_annot
> the un-annotated consumption face restated as an explicit-type-annotated intermediate Definition + cure34_E2_use_arity downstream arity
> station alongside + cure34_E2_station_unannot report-only clearing station) — five patterns all reuse the v32 engine,
> zero new engines; gated E2/E3 compile arc first-hand: pre-fix compile passing (the defect family appears at extraction), post-fix passing,
> the E2 consumption face `'a1 -> 'a1`→`nat -> nat`, the consuming unit magic 0/0, the world accessor debt=1
> mechanically pinned (real-repair work stream domain, canonical_note records the boundary). Self-test suite 43 cases.
> v36 addendum (November 11, 2026, the push-CI single-command pipeline round): `tools/pushci.py`, the post-fix push-CI
> single-command pipeline orchestrator — five-stage pipeline: preflight initiate / emit check (dyld doctor verdict + net-probe
> stable-window double check · optional gate4 header pre-scan · the no-initiate/emit-on-single-probe rule codified) → push (3 retries at 45s +
> ghproxy re-route for https://github.com/ remotes · pushed_sha = ls-remote remote tip) → watch
> (status-only polling · updated_at frozen is not a zombie verdict) → heal (ci_triage family
> routing: B/E families → stable window passed → rerun · capped at --max-heal 3 · A content-failing never auto-fixed · C toolchain stops ·
> off-table families never auto-rerun, manual attribution) → verdict ± merge (seven states success/fix-content/
> toolchain/unstable/heal-exhausted/gate4-block/dry-run · exit codes 0/1/2/9) —
> the v35 four tools (doctor/net-probe/triage/union) orchestrated via subprocess, zero new engines; offline-testable
> injection built in (--injector/--git-caller/--sleep-scale · zero real network, zero real push); self-test
> suite grown to 48 cases.
> v37 addendum (November 11, 2026, the realtime three-tool round, user directive: cooperate with the workflow's realtime dynamics to provide cleaning, shape normalization,
> troubleshooting, and blockage clearing): `tools/cw_sentinel.py` realtime watcher (three signal sources: CI runs / ledger
> chain roots / buildlog word faces → JSONL event stream · once/loop dual mode · classification fully delegated to ci_triage · chain roots
> fully delegated to chain_graph · zero actions by default) + `tools/wash_shape.py` shape-normalizing tool, canonical five-wash
> pipeline (word-face/token/header/line-end/anchor, all five washes orchestrating existing engines via subprocess · plan defaults to zero disk writes ·
> --apply re-runs the five washes after applying for verification) + `tools/unclog.py` blockage-clearing closed-loop engine (probe collection
> → chain_graph root picking → cure_applier apply → rescan/resprobe re-check → verdict
> unclogged/wall/rounds-exhausted · dry run by default · frozen-registry entries refused as failing · honest walls never forced) —
> the three tools' common interface discipline, five rules: JSON-in/JSON-out (--json report · schemas
> rocqwash-sentinel/1 · rocqwash-shape/1 · rocqwash-unclog/1 · sort_keys byte-identical) ·
> exit codes 0/1/2/9 (a failing result is data, not a tool failure · loud stdout) · --once/--loop dual mode (--interval
> adjustable · JSONL event stream --events) · offline-testable (--injector subprocess-call-layer canned +
> --sleep-scale · zero real network, zero real compiles in selftest) · orchestrate rather than rebuild (zero new engines);
> the `cw.sh` entry grows to fifteen tools (sentinel/wash-shape/unclog three routes · four-place sync) ·
> the workflow cooperation interface quick reference lives in the [README-cw.md](README-cw.md) "workflow cooperation interfaces" section;
> self-test suite grown to 51 cases (47 passing / 4 cases yield to missing originals · fully run on the real machine).
> v38 addendum (November 11, 2026, workflow integration and comprehensive checkup round, four agents cast together + integration-agent close):
> `tools/cw_doctor.py` comprehensive checkup tool, four-domain aggregation (1 environment = toolchain_dyld_doctor orchestration
> 2 network = net_probe --rounds 1 3 registry-anchor canonical-form audit 4 blockage account = probe_engine real probes
> + chain_graph chain roots — each domain orchestrates one existing tool via subprocess, zero new engines → composite health score 0-100
> + per-domain verdict + advice disposition list · schema rocqwash-cwdoctor/1 · --injector
> offline-testable · diagnose-only, never executes · a failing result is data, not a tool failure · healthy=0/degraded=1); workflow integration
> face: `examples/workflows/` three nested-segment canonical samples (backend-sentinel background watcher / step-pushci
> single-step push CI / loop-unclog blockage-record clearing · all offline-injectable shapes) +
> `docs/workflow-integration-whitepaper-v1.0-20261111.md` integration whitepaper (coordinating-session
> yield mode / background task topology / push-window four criteria × preflight check, double doors standing side by side); resilience layer: shared backoff pure function
> `tools/_http_backoff.py` (CI GET 403/429/5xx exponential backoff · Retry-After respected ·
> wired into ci_triage/cw_sentinel/pushci) + net_probe `--jitter/--seed` jitter
> + pushci `--timeout` / sentinel `--subproc-timeout` subprocess hang protection (injector
> canned paths always zero retries, zero real network); interface growth: sentinel `--on-red-preset`
> (unclog dry run / pushci dry-run preset actions · mutually exclusive with --on-red) + unclog `--audit`
> read-only blockage-account baseline (--src whole-file md5 self-proves zero disk writes before and after the run · verdict=audit exit 0);
> the `cw.sh` entry grows to sixteen tools (cw-doctor route · four-place sync); self-test suite grown to 52 cases
> (t_cw_doctor minimal selftest shell with two checks · the missing shell self-supplemented by the integration agent).
> v39 addendum (November 11, 2026, document verification and relay live-run round, four pieces cast by the tooling agent + integration-agent close):
> `tools/doc_lint.py` document ↔ implementation consistency three-check tool (1 tool-table check = cw.sh header/usage/
> hint/case four-place cross-check + tools/ generic entry reconcile 2 count check = tests/run_tests.sh CASES
> vs tests/README.md vs README.md three-way reconcile 3 flag check = docs-cited flags vs each tool's
> --help actual output, flag by flag (--help really run · cap 20 tools) — schema rocqwash-doclint/1 ·
> verdict consistent|drift · a failing result is data, not a tool failure · --selftest tmp mini-repo six vectors ·
> zero network, zero disk writes); relay live-run verification: `tests/test_relay_e2e.py` cw_sentinel
> --on-red-preset unclog full-chain three-check e2e (event trigger → --audit dry run rc=0, zero disk writes,
> md5 self-proof → JSONL same-disk unclog report path byte-for-byte differential comparison · all canned · the real-run transcript
> landed in docs/ops-realtime-service-v1.0-20261111.md, the realtime service run manual);
> shape-normalizing tool capacity growth: wash_shape `--header-map-preset NAME` designated header template library
> `tests/fixtures/header_map_v1.json` (canonical distillation of the effort · gold-standard citations on register · schema
> rocqwash-header-map/1 · mutually exclusive in the same slot as --header-map) + cure_pack v1.4 corpus survey
> round single-pattern growth: `cure39_ifq_connective_qualify` interface quantifier connective qualification (November 11, 2026
> evidence-gated survey · b48-52 wash-work stream citation commit 9a51c74 · RI0 context-piece statement-face bare
> lt/le/plus pinned at the @S01_BaseRing projection form · tree canonical form; survey discipline held — thinner-cited forms
> all left pending, none cast · fixtures cure39_t13/cure39_plain). The `cw.sh` entry grows to seventeen tools
> (doc-lint route · four-place sync); self-test suite grown to 54 cases (t_relay_e2e three-check e2e +
> t_doclint minimal selftest shell three checks · missing shells self-supplemented by the integration agent).
> v40 addendum (November 11, 2026, canonicalization consolidation round, four agents cast together + integration-agent close): `tools/baseline_diff.py`
> blockage-account baseline comparator (two unclog --audit blockage baselines, argv order old→new → new_blocks/
> resolved_blocks/persistent three lists + score_delta · verdict improved/degraded/
> stable/incomparable · account self-consistency precheck rejects hand-edited baselines · candidate-face four-tuple cross-set comparison honestly refuses to judge ·
> the timing segment stays out of the comparison = the baseline's only non-deterministic segment — schema rocqwash-baseline-diff/1 · failing is
> data, not tool failure) + `examples/baselines/` blockage-baseline in-repo procedure (naming rule
> audit-<domain>-<yyyymmdd>.json · produced by real-tree dry run · timing note · cast by the tooling agent); destructive-surface re-check matrix
> `tests/test_destructive_matrix.py` 17 rows of write-refusal criteria, one refusal per row (disk-writing tools × write faces × guardrail
> anchor file:line: unclog×4/wash_shape×4/pushci×3/cw_sentinel×2/registry_union×2/
> cure_applier×2 · all tmp fixtures + injector canned · zero real network, zero real repo, zero real compiles · matrix failing =
> a broken guardrail listed loudly as a breach · cast by the destructive-surface agent); steady-state three-tool growth: cw_sentinel `--emit-max-bytes`
> JSONL rotation (.1/.2 keep 2 generations · seq continues across generations) + `--rebuild-state` crash recovery
> (damaged state refused with failing 9 · silent rebuild forbidden · explicit rebuild the only legal path), unclog `--state-file`
> same-shape watcher-state seen differential (red-new events only-new · reads/writes the same shape as the cw_sentinel state ·
> --rounds/--loop vs --audit/--state-file two mutually exclusive groups rc=2 · damaged refused 9),
> wash_shape --loop event stream same-shape alignment (rocqwash-sentinel-event/1 · seq continues across processes
> + ts=off note) + plan cross-round cache (source md5 changed → recompute · identical → hit and reuse · plan_cache
> loud account) (cast by the steady-state agent · selftest vectors 12/13/18 grown); the `cw.sh` entry grows to
> twenty tools (baseline-diff route · six-place sync including the legal two lists and the count line); service layer overview
> [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
> (three chains one map panorama + tool-face index · cast by the docs agent); self-test suite grown to 56 cases
> (t_destructive_matrix 17-row criteria + t_baseline_diff minimal selftest shell three checks · missing shells self-supplemented by the integration
> agent).
> v41 addendum (November 11, 2026, four agents cast together + integration-agent close): cw_sentinel preset table data-driven growth to
> five presets (unclog/pushci/wash-shape/triage/cw-doctor · each carrying the dry-run-by-default invariant) +
> `--on-red-preset` repeatable chaining (executed in the given order piece by piece · one failure continues without changing the watcher exit code) +
> on-red double path under the same guard (plain `--on-red` and preset missing `--emit` both rc=2 · the destructive-surface
> matrix S2 criterion promoted · matrix still 17 rows); probe_engine `--jobs` K-way parallel sharding (default
> 1, per-piece serial with zero drift · canonical output order never drifts with completion order · duplicate candidate names fail-loud rc=2);
> unclog `--probe-parallel` probe (tool citation) / check (generic sense) parallelism pass-through (audit timing segment jobs dimension on account ·
> the same candidate face at different K comparable across runs); performance profiling procedure docs/perf-profile-v1.0-20261111.md
> + examples/baselines/perf-README.md (K=1/2/3 three-run collection · two-axis separation rule · cast by the tooling agent);
> push_gate push-window four criteria × pushci preflight check double-door normalized assessment
> docs/push-gate-dual-door-assessment-v1.0-20261111.md (assessment only, zero code changes ·
> cast by the guardrail agent). Self-test suite stays at 56 cases (52 passing / 4 cases yield to missing originals).
> v46 addendum (November 12, 2026, red-event routing and registry hygiene audit integration round, three agents cast + integration-agent close):
> `tools/red_dispatch.py` red-event router (watcher failing events → action-preset routing · three preset tiers
> report-only/suggest/auto · **zero execution by default** · suggest emits a copyable command block · auto runs on explicit
> request with a 60s cap, rc≠0 recorded loudly without changing the exit code · anti-repeat state + cooldown · five routes all on
> existing cw.sh routes, zero new engines: B/E families → pushci re-run · A-family content failing never auto-fixed, emits a fix list ·
> C family → doctor · blocking → unclog · build-signal → wash-shape · schema
> rocqwash-red-route/1 · cast by the casting agent) + `tools/registry_audit.py` registry hygiene
> auditor (order.txt/_CoqProject dual-ledger **read-only** four-account emission: duplicate rows / anchor-collision text / order
> number shape / malformed shape / missing anchor / orphans / live topology references + `--fix-plan` deterministic prescription, zero disk writes ·
> **`--apply` does not exist**, left for the executor · keyed/anchor-canonical directly reuses registry_union, zero rebuilding · the lesion
> is data, always exit 0 · schema rocqwash-registry-audit/1 · cast by the casting agent · real-repo live-run precondition
> note carries the v40 baseline procedure rule examples/baselines/README.md "real-tree live runs belong to the coordinating session · agent faces
> only attest the tool level") + `docs/评估-push_gate推窗四判据与pushci归一-20261111.md`
> push-window four criteria × pushci normalize feasibility assessment (assessment only, zero code changes · cast by the assessment agent · with v41
> guardrail agent same-topic independently written, two checks corroborate each other · verdict: keep the double doors side by side); the `cw.sh` entry grows to
> twenty-three tools (route/audit two routes · four-place sync · the assessment document is a document with no route);
> self-test suite grown to 58 cases (t_red_dispatch/t_registry_audit two minimal selftest shells ·
> missing shells self-supplemented by the integration agent).
> v47 addendum (November 12, 2026, the gated compile arc turns passing and the registry prescription executor round, three agents cast + integration-agent close):
> the gated compile arc master switch turns passing (roadmap candidate 4 · task-brief number 8A case · of the two paths A taken = pointing at the 9.3
> multiplexer `mac93_install_work/opam93/rocq93/bin/rocq` · the v43 third run 27/27 same-source proof) — `tests/run_tests.sh` master switch default-probes four paths (env set wins · external clone
> explicit designation undisturbed): `ROCWASH_ROCQ` → the t_cure_pack compile check segment + the t_probe_engine
> real rocq section; `GATE7_PROBE_SCRIPT`/`GATE6_SCRIPT` → Set repository gate7/gate6 originals on record
> designation unlocks t_gate7_wrapper/t_verify_gate6; `BORN_WORLD_ROCQ` → CW Live rocq missing
> 9.3 substitute unlocks t_gate6_born_wrapper — all gate criteria semantics zero-change (present = run · missing = SKIP ·
> env missing and volume missing still SKIP), only the default face flips; the t_quad8_check four-repository-copy missing-volume family (another family)
> not in this case; the flip is "current world generation" passing, not a 9.1 recovery (honest record per the v43 9.3 gated arc
> 27/27 same standard). + `tools/registry_fix.py` registry prescription executor (applies registry_audit
> `--fix-plan` prescriptions item by item · three prescription classes DEDUP keep-first / anchor-refresh / ORPHAN-ADD skip · **dry run by default** ·
> `--apply` post-apply three-check assertion explodes into rollback · staging fully in-memory, zero disk writes · schema
> `rocqwash-registry-fix/1` · real-tree `--apply` pending execution, not in this round); + the watcher's first real-repo deployment
> (`tools/cw_sentinel.py --loop` resident over a live effort window · JSONL event stream events=33 ·
> the v46 red-event routing consumption face in action); the `cw.sh` entry grows to twenty-four tools (registry-fix route ·
> four-place sync); self-test suite grown to 59 cases (t_registry_fix directly mounts the tool --selftest eight vectors ·
> mounted by the integration agent).
> v48 addendum (November 12, 2026, the DS4 three-account close + the resident-watcher ops manual + the Main repository survey round, three agents cast + integration-agent close):
> roadmap item 1, the DS4 K=3 account `examples/baselines/audit-k3-20261112.json`, a real-tree blockage baseline landed in the repo
> (27 pieces RC0 failing=0 · timing jobs=3 · probe_chain_s=165.202/total_s=169.684) — with K=1/K=2
> same candidate faces, baseline_diff both directions verdict=stable, three accounts agree (190.728/101.916/165.202 ·
> speedup 1.87× at the K=2 tier, the current inflection point · the K=3 negative marginal speedup recorded honestly · perf-profile section 5 three-line placeholder
> backfilled by the coordinating session with the real numbers);
> roadmap item 2, `docs/ops-sentinel-长驻手册-v1.0-20261112.md` resident-watcher ops manual completed
> (deployment placement spec / event-stream consumption and the render_events/red_dispatch interfaces / rotation and recovery discipline /
> v44-v48 evidence citations — zero code changes, zero new tools, zero new flags);
> roadmap item 7, `docs/勘形-multi-repo-Main仓适配-20261112.md` Main repository CI shape survey document
> (read-only, zero code touched · api.github.com live capture of the active coq93.yml shape · adaptation grading verdict =
> 4 ready-to-use / 3 minor-change / 2 medium-change — the pushci PR route mirror-blind bite mismatch is the biggest gap ·
> cross-repo unauthorized disk writes stay a non-negotiable constraint).
> Component-level details in [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md); contributing workflow in
> [CONTRIBUTING.md](CONTRIBUTING.md).

## Recursive Evolution Layer: Self-Verification, MCP, and the Capability Index

Since November 19, 2026 the toolchain closes its own loop: it audits its own
tree, repairs its own failing cases, and verifies its own verifiers.

- **Recursive tool family** (`tools/`): `tree_audit.py` (read-only tree health census over `.v`/`.lean` sources), `axiom_guard.py` (repo-wide axiom guard, one `Print Assumptions` verdict per theorem), `auto_round.py` (round admission, commit, ledger, rollback), `scheduler_lite.py` (TODO-SEAT threshold trigger), `repair_scope.py` (shared exclusion roster for the repair faces), `repair_weekly.py` (repair-outcome weekly distribution), `selfevolve_round.py` (one deterministic mechanical round: census → apply → verify → commit → push → CI judge).
- **Meta-verification layer**: `tests/test_tool_selftests.py` enumerates the selftest universe — the 80 non-underscore-prefixed `tools/*.py` (83 files minus 3 `_` helpers) — and runs every declared `--selftest`, failing loudly on a red, missing, or unexempted face; mounted in the suite as the `t_tool_selftests` case.
- **Methodology canon**: [docs/recursive-evolution-whitepaper-v1.0-20261121.md](docs/recursive-evolution-whitepaper-v1.0-20261121.md) — the seven laws, the seven pillars, and the section 7 live walk-through of the November 19–21, 2026 chain.
- **CI failing-case classification**: [docs/ci-triage-table.json](docs/ci-triage-table.json) v1.5 — the 19-class table (R1–R19) behind the recursive-era CI whitepaper badge above.
- **Per-tool contract surface**: [docs/CAPABILITY-INDEX.md](docs/CAPABILITY-INDEX.md) — one entry per tool, seven fields each (path, one-line purpose, invocation form, copyable example, imports, network face, SKIP face).
- **MCP stdio server**: `tools/mcp_server.py` — newline-delimited JSON-RPC 2.0 over stdio, three methods, a 58-capability roster (frozen `SELFTEST_ROSTER_COUNT`; machine-checked by `tests/t_mcp_face.py` `EXPECTED_TOOLS = 58`); protocol and security face in [docs/mcp.md](docs/mcp.md).

## Quick Start

Prerequisites (three lines):

- `python3` ≥ 3.9 — no third-party packages required
- a Rocq/Coq 9.x toolchain on `PATH` — needed only for the compile-verification pieces; everything else runs without it
- Windows: use Git Bash as your shell (the toolchain is bash + python3)

```bash
git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh          # self-test suite; exit 0 = all green
```

First run — scan a demo source for statement-face Prop leakage:

```bash
python3 scan/mac_stmt_scan.py --file examples/demo_prop_leak.v
# RED stations: ['demo_eq_self', 'demo_eq_sym', 'demo_le_eq', 'demo_le_self', 'demo_mixed']
```

First verification — comment-hygiene gate on a clean sample:

```bash
python3 verify/gate4_comment_guard.py --file tests/fixtures/gate4_clean_sample.v
# [gate4ext] ... 件数=1 (files=1)  PASS=1  FAIL=0  REVIEW(人工复核)=0 (human-review items)  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```


```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing); writes my_proof_washed.v
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Extract statement names and assert N=N against the washed file
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487
# --expect N asserts the extracted statement-name count equals N (487 is an example value)

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json   # first freeze = the certify sub-verb; second = the action name (the pair is freeze|check)
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper: pins git push to a fixed pre-resolved remote address — --pin-ip rewrites the remote URL host to that IP, --url-host keeps the original name as the Host header — so the push does not depend on DNS resolution at push time (dry-run by default; masked output; --yes actually pushes)
python3 watch/watch.py push --repo . --remote origin --pin-ip 140.82.113.3 --url-host github.com

# Post-push ls-remote double-read confirmation
python3 watch/watch.py confirm --repo . --remote origin --branch main --sha <sha>

# Equivalent direct invocation
python3 scan/mac_stmt_scan.py --file my_proof.v
python3 names/mac_stmt_names.py my_proof.v --names-out names.txt

# Full-chain demo (scan → names → N=N → wash → verify)
make -C examples demo

# Compile with thermal guard
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- rocq c -native-compiler no -Q . "" my_proof.v
# -Reg <dir> = a dedicated queue-registration lane; -Front/-Mid = ladder-queue tier cut-offs (FRONT tier runs nice 0, MID tier nice 10) — parameter reference: docs/en/architecture.md §6
```


## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Seven Canonical Steps (all mandatory, in order)

Step 3's wash rests on one type-theoretic fact: `Set` and `Prop` are mutually
exclusive sorts in Coq/Rocq, so Prop-carried statements are rewritten onto
Set-carried predicate forms rather than edited in place (see Terms).

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic `436f712100015ff4` = the `.vo` file-header magic bytes / vo newer than v / PA Closed = the Print Assumptions audit finds no axioms / coqchk Axioms:none)
5. **R4 three-source conjunction** (bare full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0)
6. **gate7 English adaptation** (CJK→0 + five-field header 30-line cap)
7. **N=N name-table assertion** (mac_stmt_names.py ordinal full-equality) + freeze md5

Each step must pass before the next. Any failure = honest WIP, no green-washing.

## Four W13 Seam Mechanisms (Generation-Gap Auto-Classification)

1. **== statement rewrite/ring/reflexivity structurally unusable on QeqT(Id) goals** → flip back via qeq_imp_qeqT first
2. **Keyed-matching instantiation**: supply-side parameter must take the actual shape in the goal
3. **Premiss-carrying lemma consumption**: assert-form conversion + dual-shore bridge
4. **Cross-line Require topology leak**: statement-level multi-line awareness + driver idempotent resume

## LLM Integration

rocqwash is designed to **complement** LLM agents, not compete with them:

- **LLM excels at**: understanding "what does this math mean" (semantic layer)
- **rocqwash excels at**: ensuring "this proof is real" (mechanical layer)

**Collaboration pattern**: LLM understands → rocqwash diagnoses → LLM fixes → rocqwash verifies → LLM commits → rocqwash certifies.

## Why rocqwash Surpasses LLM/Probabilistic Approaches

The comparison below is a capability statement, not a benchmark claim; each row
names the mechanical mechanism that replaces a guess. It is the mechanical half
of the complement split above: the LLM agent proposes and fixes, rocqwash
verifies and certifies.

| Capability | LLM | rocqwash |
|-----------|-----|----------|
| Prop leakage localization | LLM needs to read entire file and may miss lines | `mac_stmt_scan.py` pins to exact line in milliseconds |
| Missing dependency detection | LLM guesses Require chains | Require line-by-line scan + Set tree diff = mechanical exhaustive, zero omissions |
| Seam type classification | LLM reads error messages and guesses direction | W13 four-mechanism grep fingerprint → prescription mapping = mechanical, not experiential |
| Wash mapping | LLM generates tactics that may hallucinate | Canonical 7-form exact-string replacement + count==1 assertion = idempotent replayable |
| Compile verification | LLM trusts self-report | `world.run("rocq",...)` exit code = deterministic |
| R4 three-source | LLM may miss spots | bare full-closure extraction + probe dual-face + five-pattern grep = triple-source conjunction |
| N=N name-table | LLM may miscount | `mac_stmt_names.py` ordinal full-equality assertion = mechanical |
| UNION world integrity | LLM may skip dependency copies | Per-piece md5 manifest = mechanical leak-proof |

**Core barrier**: These capabilities are not "better prompts" — they are structural properties of Coq/Rocq type theory. QeqT-goal Qeq-rewrite impossibility is a corollary of Set/Prop type-theoretic mutual exclusion. No prompt engineering can override type theory.

## License

- **Code:** AGPL-3.0-or-later, see [LICENSE](LICENSE).
- **Audit documents:** `docs/audits/**` and release assets of tags `f1p-audit-*` are CC-BY-4.0, free to reuse with attribution.
- Zenodo record (audit package): DOI 10.5281/zenodo.24238998
- Zenodo (tool release v0.1.0): DOI 10.5281/zenodo.24225678
