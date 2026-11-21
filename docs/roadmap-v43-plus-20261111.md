# rocqwash v43+ roadmap (candidate state · pending execution, unscheduled): November 11, 2026

> Purpose.  Candidate-pool roadmap for rocqwash v43 and later, produced by the record agent: the pool is decision material, **not a scheduling order**; each item enters a work stream only after the main session designates it. Source material: the eight "boundaries and to-do" sections of the update ledger v34–v41 (`更新账.md:3543`/`:3576`/`:3605`/`:3635`/`:3666`/`:3696`/`:3725`/`:3756`) plus four in-repository procedure faces (the perf README / the ops realtime-service manual / the push-gate dual-door assessment / the workflow whitepaper).
> Interface.  Document face only; defines no tool behavior. Writing scope: this file alone (the `cw.sh` routes, the combined test suite, and the README series belong to the integration agent), so no face collides. `git commit` is out of scope: the main session performs unified commits. Repository state at issue: rocqwash v41, commit `c5df4d4`, working tree clean. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  The ledger face `更新账.md`; the document faces cited by path in the body (the perf-profile report, the push-gate dual-door assessment, the workflow whitepaper) and `examples/baselines/perf-README.md`; the tool faces `tools/unclog.py`, `wash/probe_engine.py`, `tools/wash_shape.py`, `tools/cw_sentinel.py`, `tools/pushci.py`, `tools/registry_union.py`; the test faces `tests/test_cure_pack.py`, `tests/test_probe_engine.py`, `tests/test_relay_e2e.py`, `tests/run_tests.sh`; no runtime dependency.
> Evidence.  Every line anchor, quote, and count below transcribes the named source face at the stated repository state (`c5df4d4`); the pool adds no measured numbers of its own; an item without a measurement states the method and the verification criterion instead (the DS4 discipline: numbers are never invented). The checks listed in §5 were executed on November 11, 2026, each run wrapped in cpu_guard; the doc_lint pass returned its verdict into that round's ledger record with drift=0. Section 6 (RQW12, November 14, 2026) is a later annotation: it adds, removes, and reorders no pool rows.
> Exit-codes.  Not applicable to a document face; the tools cited here keep their implemented exit-code semantics unchanged (the refuse-to-load rc2 of `tools/wash_shape.py:151-152` and the 0/1/2/9 exit-code inventory of item ⑧ are transcribed as implemented).

---

## 1. The real constraints (four · each anchored)

1. **8GB Air thermal control**: every execution goes through the `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh` wrapping invariant; the probe-side thermal warning is in the instrument (`wash/probe_engine.py:49` "K>1 in-window multi-rocqworker concurrency = thermal load ↑" · `:507` ADVISE line · `:478` likewise advises K≤2); the ≤30-piece sample-cap thermal-window procedure is on record (`examples/baselines/perf-README.md:60-68` · `:113` keep K≤2 unless the user decides otherwise).
2. **Single runner**: the suite note "the CI runner has no local master" is on record (`tests/run_tests.sh:146`); the dual-door assessment confirmed that "the current dual-door arrangement plus the canonical serial order is already the optimum under the single-runner constraint" (`docs/push-gate-dual-door-assessment-v1.0-20261111.md:209`).
3. **The quota quiet window**: a constraint given by the task instruction. The repository's on-record anchors have zero hits (this agent's full-repository grep for the terms (`积分` / `静默窗` / `quota`) ran on November 11, 2026 and returned nothing; recorded as such). Scheduling meaning: candidates of the CI-active-run kind (the real-push segments of ② and ⑦) must avoid the window and stagger their runs; for observation-kind candidates (the resident watcher of ②), zero events during the quiet window is a legitimate observation, not an instrument failure.
4. **Gold-standard discipline**: the evidence-gated precedent = 11 candidates, 1 accepted, 10 rejected with itemized reasons (`更新账.md:3680`/`:3689` "omit rather than admit unverified items, encoded in the code"); never-synthesized is enforced by the code (`wash_shape` header-map refuses to load without evidence · `tools/wash_shape.py:151-152`, probe order and plan-miss recorded as-is); the honest-boundary precedent for the gold-standard pre-repair form that cannot be fully reconstructed is on record (`更新账.md:3546`).

---

## 2. The candidate pool (8 items · numbering inherited from the task instruction · four columns each + verification criterion)

### ① probe --jobs>1 real-tree measurement (the thermal-window procedure is in place)

**Provenance**: `更新账.md:3758` (v41 to-do 1, "thermal-window candidate pending execution · the canned-mechanism evidence is complete").

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| Fills the only remaining "pending" placeholder of `docs/perf-profile-v1.0-20261111.md:19/:125` DS4; the parallel wall-clock profile moves from a method placeholder to a measurement; the last missing piece of the v41 parallel work stream's close-out | The procedure is complete: `--probe-parallel` (`tools/unclog.py:373` forwards probe_engine's `--jobs`) + real compilation through the `--rocq-cmd` template is proven runnable (v41 third run 27/27 · `更新账.md:3753`) → **no hard dependency on ④**; the thermal-window procedure (perf-README §4) | Low-medium: one run per K=1/2/3 on the same candidate face (K=1 already has a 190.7s-order reference · `perf-profile:47`) + the ledger table addition | Thermal load (K>1; the in-instrument warning note is not enforcement · the user decides); a possible single-runner starvation note; **no significant speedup or negative speedup → recorded as such** (DS4 discipline: numbers are never invented) |

**Verification criterion (what counts as done)**: on the same candidate face (`examples/baselines/audit-ConstructiveWorld_Live-20261111.json`, 27 pieces) the three K=1/2/3 accounts all exist, the timing section carries the jobs dimension, and the whole run is cpu_guard-wrapped with the traces kept; the three "pending" DS4 table rows become real numbers (negative conclusions recorded as such); the three accounts pass the baseline_diff criterion with the candidates set identical throughout = comparable.

### ② sentinel --loop first resident engagement (real-engagement consumption)

**Provenance**: `更新账.md:3638` (v37 to-do 2, "--loop real-background candidate awaiting its first real consumption scenario").

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| The watcher moves from fixture-level full verification to real engagements; the three signal sources (failing CI builds / local blockage records / build logs) get their first real consumption; the three new v41 presets (wash-shape/triage/cw-doctor · chained `--on-red-preset`) get a live exercise | A real-engagement window (the next engagement doubles as the verification · `更新账.md:3638`); the workflow embed block and the ops-manual standard command are ready (`examples/workflows/backend-sentinel.md` + ops manual §2) | **Low (zero new code)**; pure run face: a background bash task carries `--loop` + an `--emit` JSONL stream | A resident process must yield to the main session (the whitepaper's five mechanisms are in place); sparse signals inside the quiet window = zero events is a legitimate observation; side-channel actions stay dry-run only (the unclog dry-run-by-default invariant · `更新账.md:3650`) and never apply to the tree |

**Verification criterion**: during a real engagement, `tools/cw_sentinel.py --loop` runs resident → `--emit` JSONL carries ≥1 real event (kind/family/action fields all present) → a second run with `--state-file` is idempotent with zero duplicate events → the engagement report cites the event count + the consumer-side grep/python3 sample runs reconcile against it.

### ③ on-red → unclog full-auto docking assessment (automatic dry run → human-reviewed `--apply` guard design)

**Provenance**: `更新账.md:3639` (first half of v37 to-do 3); v38 landed the preset + the dry-run invariant, v39 tested relay e2e (`tests/test_relay_e2e.py`); this candidate is the **automation-boundary assessment** of the last link of the docking chain.

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| The guard design for the existing manual gap in "watcher failing → unclog dry run → human-reviewed `--apply`" becomes a document; decision material for the service layer's safe automation; a productization reuse of the dual-door assessment's methodology (option A's four reasons · `docs/push-gate-dual-door-assessment-v1.0:128/:192`) | Real event corpus from ②'s first engagement (the assessment needs real trigger samples); the agreed criterion cannot be loosened unilaterally: `--apply` off by default + allowlist human review (ops manual §3 procedure `:174`/`:228` "zero action is the default" `:12`) | Low (assessment document · **zero code change by default**; a conclusion that requires code change gets its own work stream) | The fully-automatic-apply temptation is this candidate's largest risk (gold-standard/frozen faces); the guard design must keep the dry run automatic and the tree-touching step human-reviewed; an assessment recommending loosening would violate the agreed rulings (the v38 mutual-exclusion ruling + the guard surface after v40's real-gap repair) |

**Verification criterion**: the assessment document goes into docs/ (current state → option set → recommended option + reasons + residual risks recorded as such · option-A format); a pure-assessment case keeps doc_lint drift=0 and every command block in the document passes bash -n; a case containing a code-change recommendation adds destructive-matrix verdicts + relay e2e vectors + the three checks gain no new failings.

### ④ Resolving the 9.1 toolchain dependency face (`ROCWASH_ROCQ` → 9.3 or the restored donor; the gated compile arcs' four SKIP cases turn passing)

**Provenance**: `更新账.md:3579` (v35 to-do 2) + `:3537` (route erratum: `ROCWASH_ROCQ` must point at the rocq multiplexer, not the shim).

**Current-state verification (this agent, November 11, 2026)**: the customary path `/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq` measured **No such file or directory** (the v35-recorded MISSING state still holds); the 9.3 multiplexer is verified present on the volume at `/Users/apple/Desktop/mac93_install_work/opam93/rocq93/bin/rocq` (find hit).

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| **The master switch of the gated compile arcs**: four gate positions turn passing; `tests/test_cure_pack.py:492` (compile-check leg · `:718` SKIP line) + `tests/test_probe_engine.py:259-261` (the real-rocq leg) + the two full-suite cases `tests/run_tests.sh:438/:451`; the compile-verification infrastructure for the new-style cure real-tree live runs (`更新账.md:3699`) and for ⑥ | Both alternative paths are verifiable now: A = point at 9.3 (`mac93_install_work/opam93/rocq93/bin/rocq` · the v41 third run already proved the 9.3 template runs passing from the same source) or B = restore the donor (the toolchain_dyld_doctor `--donor` tracing procedure is in the repository · **advice only; never executed on the user's behalf**); the cw_paths root-move watch table is on record (`更新账.md:3580`) | Low (A = one decision + the conventional-path recording criterion; B = medium · a real-copy restoration action) | The 9.3-vs-9.1 generation-gap semantics; turning passing means the "current active generation" passes, not a 9.1 recovery (`更新账.md:3753`, same criterion · honest boundary recorded); if the restored donor is MISSING again → the doctor diagnostic procedure is the fallback; do not confuse with the master-copy-missing SKIP family (the run_tests.sh:320/:347/:361/:379 group is the CANON check · a different family) |

**Verification criterion**: after the decision is recorded in a document; under `ROCWASH_ROCQ=<决断路径>`, `python3 -B tests/test_cure_pack.py` and `python3 -B tests/test_probe_engine.py` run with rc=0 and the output carries **no "SKIP (ROCWASH_ROCQ unset)" segment** (all four gate positions' compile arcs ran) + the full-suite 56/52/0 failing baseline does not move + the decided path matches the erratum criterion (multiplexer form).

### ⑤ wash_shape header-map template-library rolling expansion (following the engagement corpus)

**Provenance**: `更新账.md:3639` (second half of v37 to-do 3); v39 landed v1 (`campaign_set_diamond` five fields · refuse-to-load without evidence enforced by the code).

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| The header-map sanitization coverage expands with real engagement corpus; new canonical forms become new presets; the continuing fulfillment surface of the never-synthesized discipline | **Engagement corpus** (the gold-standard discipline forbids pre-fabrication: no evidence, no casting · `tools/wash_shape.py:151-152` refuse-to-load rc2); the outputs of ②'s engagement window | Low (once the corpus arrives: distill → the `tests/fixtures/` template library grows → the selftest gains vectors) | Curated-surface mis-capture (the five-field complete-piece no-mechanical-rewrite protection is in the repository · the v39 ledger); template-generation staleness (old presets drifting from new engagement forms; re-verify each placeholder citation during the rolling expansion) |

**Verification criterion**: the new preset loads through `--header-map-preset` → renders → `--apply` end-to-end partial → shaped → idempotent re-run; the "refuse to load without evidence" negative case runs rc2 live; the real-repository face is verified read-only with zero disk writes; the per-placeholder citation of "body content is never synthesized" is on record.

### ⑥ cure_pack v1.5 (the notation-rebinding variant awaits a second reproduction for promotion)

**Provenance**: `更新账.md:3680` (among v39's 10 rejections, "notation rebinding awaits a second reproduction" pending re-examination) + `:3699` (v39 to-do 2, the cure39 new-style real-tree live run pending execution).

**Current-state verification (read by this agent)**: `wash/cure_pack.json` version=**1.4.0** · patterns=**25 patterns** (including the `cure32_B_notation_rebind` notation-rebinding precedent in the repository).

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| Expansion from 25 to 26+ patterns, evidence-gated; the notation-rebinding family's second reproduction is promoted; the gold-standard "omit rather than admit" fulfilled on the positive side; v39 to-do 2 (the cure39 real-tree live run) can be filled in the same window | A real second-reproduction instance from engagements (the citation = a real diff verbatim · synthesis forbidden); **④'s gated compile arcs** (compile verification of the new cure style); an engagement window | Medium (task-instruction ruling → a new face-regex style → fixtures → the gated arc; the v34/v39 precedent procedures are complete) | No corpus means zero expansion (**recorded as such · not a failure**; the v39 single-pattern expansion set the precedent); the second reproduction is this candidate's precondition; a missing piece stays pending re-examination, never force-fitted |

**Verification criterion**: cure_applier `--selftest` gains vectors + whole-pack idempotence rc=0; the gated compile arc runs pre-fix passing → cure → cured passing → the consuming units' magic counts reconcile (depends on ④); the rejection-path itemized reasons are on record (if the second reproduction never arrives).

### ⑦ Multi-repository expansion (the adaptation face for rocqwash serving the Main repository CI)

**Provenance**: the update ledger has **no direct to-do item**; extrapolated from the v36 pushci orchestration face (`tools/pushci.py:26` remote URL derivation · host must be github.com) + the registry_union three-input face (`tools/registry_union.py:781-790` `--main`/`--branch`/`--git`); designated into the pool by the task instruction (the provenance nature is recorded as such).

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| rocqwash expands from "self-repository CI self-service" to "serving the Main repository CI"; the adaptation face of the pushci/triage/doctor trio; a cross-repository check of the service-layer whitepaper's five disciplines | Real remote credentials (**a user face**; v36 recorded "the real-push segment needs real remote credentials · a user face" `更新账.md:3608`); a shape survey of the Main repository CI (runner/signature-check differences); the item with the tightest quota-quiet-window constraint | Medium-high (shape survey → canned-scenario expansion → real-repository `--dry-run` → real push; cross-repository differences cross-checked item by item) | Cross-repository non-negotiable constraints (faces where Main-repository discipline and rocqwash discipline disagree; the adapter must never write to disk on the repository's behalf beyond its mandate); the NETRED/credential faces; CI shapes cannot be fully predicted (canned coverage is limited → the first-run `--dry-run`-first invariant · `更新账.md:3608`) |

**Verification criterion**: the Main-repository shape-survey document → the pushci_scenarios canned scenarios covering the expanded repository shapes all pass → the real-repository `--dry-run` plan face has zero side effects (HEAD/porcelain identical before and after · the v36 S6 criterion) → the real-push first engagement obtains a run with head_branch + head_sha matched → the ci_triage classification cross-checked against the reference.

### ⑧ sentinel JSONL → workflow dashboard direct feed (ledger form for artifacts)

**Provenance**: the v37 event stream is in the repository (`tools/cw_sentinel.py` `--emit` JSONL append+fsync · `docs/workflow-integration-whitepaper-v1.0-20261111.md:35/:134`) + the v40 JSONL rotation (`--emit-max-bytes` keeps 2 generations · seq numbering continues across generations) extrapolated; designated into the pool by the task instruction (the provenance nature is recorded as such).

| Value | Dependencies | Cost | Risk |
|---|---|---|---|
| The watcher event stream moves from "grep usage" to "ledger form for artifacts"; events + rotation generations + baseline_diff blockage-record differences aggregated on one page; a cross-engagement comparison surface; background-task visibility | Real event corpus from ②'s first engagement (the consumption face needs real forms); the **zero-new-engine discipline** (the aggregator is pure stdlib reading JSONL/JSON); the integration face (the four `cw.sh` route sync points + the full-suite wiring) belongs to the integration agent | Medium (one new tool: schema + sort_keys determinism + idempotent byte-identical output + `tools/cw_sentinel.py`-style `--injector` canned event vectors + the integration face) | Event schema evolution (the aggregator must fail loud on a missing key and refuse with a failing exit; silent tolerance forbidden); rotation-generation boundary reconciliation (seq never renumbers across generations); the new tool enters the doc_lint flag-reconciliation surface (the lookup burden growing from nineteen to twenty tools · an integration-agent face) |

**Verification criterion**: the aggregator `--selftest` vectors rc=0 + canned events → the ledger page written with sort_keys is byte-identical across two runs (idempotent) + a real JSONL sample (②'s output) enters the account + the exit codes 0/1/2/9 verified live + the three checks gain no new failings.

---

## 3. Ordering recommendation

**Overall order: ④→①→②→③→⑧→⑦→⑤→⑥**

| Rank | Item | One-line rationale |
|---|---|---|
| 1 | ④ | **A single decision unlocks the most downstream work** (⑥'s compile verification, the cure real-tree live runs, ①'s criterion unification) + the lowest cost + turning the four SKIP cases passing directly completes the honest face of the active suite; both paths are current-state verified in the record |
| 2 | ① | Closes out a v41 to-do directly · the procedure is complete · no hard dependency on ④ (the `--rocq-cmd` template is proven); a short, fast, closed loop |
| 3 | ② | Triggered by the engagement window · zero code; and it is the **corpus source** for ③⑧⑤; once the window opens, attaching the watcher should have top priority |
| 4 | ③ | Assessable as soon as ②'s corpus arrives · zero code change by default · the guard design is the precondition for the service layer |
| 5 | ⑧ | The service-layer consumption face · medium cost · depends on ②'s real event stream |
| 6 | ⑦ | The largest value but depends on user-face credentials + a cross-repository survey · the tightest quiet-window constraint · placed late, not dropped |
| 7-8 | ⑤⑥ | **Corpus-triggered standing candidates**; the gold standard forbids force-fitting: "no corpus, no work" is the design, not a shelving; the windows follow ② |

**Work-stream split recommendation**:
- **v43 (near work stream · zero engagement dependencies)**: ④ + ① (④ first, a half-hour-scale decision; ① three batched runs inside the thermal window).
- **v44 (the engagement work stream)**: ② resident watcher → ③ docking assessment → (corpus-triggered window: ⑤⑥ pending re-examination, promoted or not; decided as the facts stand).
- **The service layer (as needed)**: ⑧ ledger form → ⑦ multi-repository adaptation (once credentials are in place).

**Dependency points**: ④ is the verification infrastructure for ⑥ and the cure live runs; ② is the corpus infrastructure for ③⑧⑤⑥; ③⑧⑦ have zero engagement dependencies and their assessment documents can go first in parallel.

---

## 4. This document's boundary (recorded as such)

1. This document is **a candidate state**, not a scheduling order; each item waits for the main session's designation; ⑤⑥ are corpus-triggered: no work without evidence.
2. The three-check close-out belongs to the integration agent's final run: the destructive-face matrix's 17 verdicts and the full `tests/run_tests.sh` suite **were not run by this agent** (recorded as such · outside this agent's territory); this agent self-verified only the doc_lint check for this document's new pieces (§5 · 1).
3. The "quota quiet window" has no on-record anchor in the repository (§1 · 3 · zero live grep hits); carried as given by the task instruction; if a precise window definition is needed before entering a work stream, it waits for the main session to supply it.
4. ⑦⑧'s provenance nature is "designated into the pool by the task instruction · no direct ledger to-do item"; a different source from ①②③④⑤⑥'s direct ledger to-do citations, marked item by item.
5. push/commit are executed uniformly by the main session (this agent performs zero git write operations).

---

## 5. This agent's self-verification record (runs of November 11, 2026 · all wrapped in cpu_guard)

1. **The doc_lint check**: after this document was written, `python3 -B tools/doc_lint.py --repo /Users/apple/Desktop/rocqwash` ran → verdict and exit code in that round's ledger record (run immediately after writing · drift must be 0 to meet the three-check baseline; if this document's flag citations had introduced phantom references, the document would be fixed and re-run).
2. The six tools' `--help` flag full sets ran live (cw_sentinel/unclog/wash_shape/pushci/registry_union/probe_engine); this document's flag citations were checked against them one by one, not from memory.
3. `wash/cure_pack.json` read directly: version=1.4.0 · patterns=25 patterns.
4. Toolchain current state: the 9.1 customary path MISSING (verified by ls) + the 9.3 multiplexer `mac93_install_work/opam93/rocq93/bin/rocq` present on the volume (verified by find).
5. Repository current state: `git status --short` empty + `git log -1` = `c5df4d4` (v41); matches the task instruction's criterion.

---

## 6. Growth wiring annotation (RQW12 · November 14, 2026)

Annotation only: no candidate rows added, removed, or reordered; the pool above is unchanged.

The five-engine seeds (E1 ai-flavor word map, E2 jargon map, E3 termbase, E4 i18n pipeline spec, E5 engines index; per the five-engine growth design volume of November 14, 2026) are landed on main at commit `9fa2bff` (RQW12, November 14, 2026): data + SPEC faces under `seeds/` (ai_flavor, jargon, termbase, i18n, engines) plus the seed selftest `tests/t_engines_seeds.py`; zero executable engine body, since the engines themselves grow on their own wash_shape / norm_lint / evolve faces in later work streams. The seeds directory is the evolve candidate input face: the next growth cycle (RQW10 form) consumes `seeds/` as its feed. Selftest face: `python -I tests/t_engines_seeds.py` reports 5 segments / 42 checks, passing, re-run first-hand in the repo layout on November 14, 2026. Honest boundary: `tests/run_tests.sh` does not wire the seeds selftest yet, so CI run 43555890998 (passing at `9fa2bff`) did not execute it; suite wiring remains a follow-up candidate for the integration agent.
