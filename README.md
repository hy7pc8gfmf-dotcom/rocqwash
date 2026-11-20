> **rocqwash** — operating as **rocqos**, the *Rocq operations system*: a self-evolving operations layer for Rocq-based constructive-proof repositories. Built on Rocq 9.3. The "rocq" prefix is used with attribution to the [Rocq prover](https://rocq-prover.org) and its community; rocqos is an independent operations layer, not affiliated with Inria and not part of the Rocq distribution.

# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine
> English: [README_EN.md](README_EN.md)

[![CI](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml) [![macOS advisory](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml) [![certification](https://img.shields.io/badge/certification-machine--checked-brightgreen)](docs/ci-whitepaper-recursive-era-v1-20261116.md) [![Rocq](https://img.shields.io/badge/Rocq-9.3.0-blue)](https://rocq-prover.org) [![tag](https://img.shields.io/badge/tag-rw--v0.1.1--20261117-blue)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/tree/rw-v0.1.1-20261117)

> Purpose.  Repository entry document: it states what rocqwash is, how the toolchain is organized, and how to run the first scan, wash, verification, and certification commands.
> Interface.  Documents the `cli/rocqwash` entry verbs and the direct `python3` invocations shown verbatim in the fenced command blocks; names `tests/run_tests.sh` as the self-test suite entry and `make -C examples demo` as the full-chain demo.
> Dependencies.  Python 3 (>= 3.9, standard library only) for every command shown; a Rocq/Coq 9.x toolchain only for the compile-verification pieces.
> Evidence.  Every command block is runnable from a fresh clone; the self-test suite (`bash tests/run_tests.sh`, exit 0 = all passing) is the pass/fail authority for the stated case counts; component claims link to the owning tool faces.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. It is designed to **naturally surpass LLM/probabilistic approaches** in proof-unblocking: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: what can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.

## Status Snapshots

> **Service layer overview**: [service layer overview v1.0](docs/service-layer-overview-v1.0-20261111.md) (three chains in one map, plus the tool-face index) · [service effort total v1.0](docs/rocqwash-service-campaign-total-v1.0-20261111.md) (cumulative report of the seven work streams, v35-v41) · [ops live run log](docs/ops-live-run-log-20261111.md) (verbatim record of the three-gate conclude/close) · [roadmap v43+](docs/roadmap-v43-plus-20261111.md) (candidate pool; pending execution, not yet scheduled) · [resident watcher ops manual v1.0](docs/ops-sentinel-长驻手册-v1.0-20261112.md) (deployment, usage, rotation and recovery) · [multi-repo Main adaptation survey](docs/勘形-multi-repo-Main仓适配-20261112.md) (roadmap item 7, Main repository CI shape survey; adaptation grading 4 ready-to-use / 3 minor-change / 2 medium-change)
>
> **v42 snapshot (November 11, 2026 — conclude/close ledger round, four agents cast together plus the integration close)**: the total report, the drill record and the roadmap, three documents into docs/ (the service layer overview v40 stays in service) · cw_paths v1.x, two pieces into ConstructiveWorld · rocqwash v41 `c5df4d4`; the three-gate conclude/close baseline: doc_lint drift=0 / destructive-surface matrix 17 verdicts all passing / full suite zero failing (SKIP not counted as failing).
>
> **v57 snapshot (November 13, 2026, evolve cycle-2 execution round, draft candidates 1+2+3 executed, integration close)**: translation echelon (candidate 1, norm-baseline-guided top-6 by per-file error mass): six tool faces Englished per the annotation standard card (`tools/wash_shape.py` 25→0 · `wrapper/wash_station.py` 19→0 · `tools/ci_triage.py` 19→0 · `tools/cw_doctor.py` 17→0 · `tools/unclog.py` 16→0 · `tools/doc_lint.py` 15→0, echelon error mass 111→0; five-field headers prepended, function-level comments and CLI output literals translated, identifiers/flags/schema/exit codes zero-change; zh archives 4 new `docs/zh/` (wash_shape/wash_station/cw_doctor/doc_lint) + 2 updated (ci_triage/unclog carried prior archives); guard-anchor line sync in `tests/test_destructive_matrix.py`); registry hygiene execution (candidate 2 residue, Set-repo side, the only worker authorized to write that repository): commit `987a1b5` "registry hygiene cycle-2: reanchor canonical form (541 rows) + orphan registration (3 pieces)" landed on the `hy7pc8gfmf-dotcom/ConstructiveWorld-Set` working main (registry_fix --apply over the fresh audit fix-plan with --anchor-src for the 541 reanchor rows plus registry_regen batch-anchor --apply registering the 3 orphan pieces; verified locally by this integration turn as commit + message; push/CI evidence rides the registry worker's report); taxonomy supplement (candidate 3, evidence-not-reclassification discipline held): `tools/ci_triage.py` two-shape evidence-note vectors: the Main#3 runner-lost form (failure + zero failing steps + build step hanging in_progress + logs-GET 404 BlobNotFound) annotated `runner-lost-candidate` with the family kept UNRECOGNIZED via the new canned fixture `tests/fixtures/ci_triage_runner_lost.json` (review-ledger section 2 S3 verbatim transcription), and the #10 GATE2-ATTEST-RED auth-state form annotated `auth-state-red-maintained` (UNREC maintained, no taxonomy inflation); `docs/retro-triage-Main仓全史-20261112.md` evidence-note section; `--selftest` rc=0 with both vectors; integration close: norm_lint `--tree` fitness reconciliation against the v2 baseline: error 2377→2267 warn 1098→1092 cjk_ratio 0.214081→0.189684, files 153→154 (the cycle-2 draft face enters the scan): −111 error = the echelon's increment (six tools to zero), +1 error = ledger vintage drift (the v56 committed `更新账.md` append raced the v2 snapshot, parent-blob 492 vs HEAD 493 verified, zero ledger writes this turn), warn −21 on the echelon +8 the new draft face +1 the retro doc section +3 ledger vintage +3 the snapshot line's own date-stamp churn (v56 same convention); v3 baseline landed same-name `docs/norm-lint-baseline-20261113.{json,md}` (v2 recoverable at git HEAD; byte-identical double rerun); three-gate close: doc_lint consistent / suite passing twice (81 cases 62 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` 12 shell faces pass; selftest spot checks rc=0 ×5 (wash_shape/cw_doctor/unclog/doc_lint/ci_triage) + wash_station via `tests/test_scan_station.py` 9/9.
>
> **v56 snapshot (November 13, 2026, annotation-face Englishing round two, nine-tool translation close)**: three workers translated nine tool faces (`scan/dual_scan.py`·`tools/chain_graph.py`·`tools/ledger_sync.py`·`verify/erasure_classifier.py`·`verify/retrofit_gate7_irr.py`·`verify/verify_gate6.py`·`wash/comment_sweep.py`·`wash/cure_applier.py`·`wash/probe_engine.py`) per the annotation standard card (two-part header + five fields; function-level comments and CLI output literals included this round); interface boundary zero-change machine-verified (identifier/flag/schema/exit-code AST comparison vs HEAD, nine of nine identical); jargon word-face census per `docs/jargon-to-standard-mapping-v1.md`: mapping-table findings on the nine tools 35→0 (norm_lint authority), raw occurrences 48→3 with the 3 residue hits all in exempt JSON-schema key positions (`"seat": "W9"` fixture data etc., table section 1 identifier exemption); zh archives: 7 new `docs/zh/` records (4 Chinese module docstrings verbatim-faithful: chain_graph/ledger_sync/verify_gate6/probe_engine · comment_sweep/cure_applier pre-restructuring docstring archives with honest provenance note · adaptation_gate7_irr three-line header comment archive · dual_scan/erasure_classifier carried zero CJK at HEAD, no archive due); integration close: norm_lint `--tree` fitness reconciliation against the v53 baseline: error 2441→2377 warn 1036→1098, the nine tool faces all cured to zero findings (error −81 warn −20 = the round's fitness increment, fed to evolve cycle-2), remainder = 13 v54/v55 new faces (error 5 warn 61) + README/ledger append churn; v2 baseline landed same-name `docs/norm-lint-baseline-20261113.json` (v1 recoverable at git HEAD); three-gate close: doc_lint consistent (drift=0) / suite passing twice (81 cases 62 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` 13 shell faces pass; selftest spot checks rc=0 ×3 (`tools/chain_graph.py`·`verify/verify_gate6.py`·`wash/probe_engine.py`); `norm_lint --file` ×9 error=0.
>
> **v55 snapshot (November 13, 2026, signal-to-task-brief generator round, constitution law-three body)**: tool `tools/evolve.py` (in substance a signal-to-task-brief generator; the module-title face `autonomous evolution engine v1` keeps its name pending rename adjudication; schema `rocqwash-evolve/1`: the harvest→derive→draft pipeline with the autonomous-execution gate kept at human review: harvest five signal classes by subprocess of the existing engines (norm-lint fitness vs the v53 baseline with the frozen surfaces excluded / sentinel one-shot dual-repo new ci-red events with seen-idempotence / suite last state / registry-audit accounts with increment / maintained UNRECOGNIZED sentinel events) → derive fixed-rule scored candidates (impact × evidence / effort, evidence clamped 10) plus genetic standing candidates from the ledger lineage → draft the constitution three-law-preamble task brief to `--draft-out`; **draft-only spawn gate: never executes a candidate, never writes the repository**; adverse signals are data, exit 0/2/9); `--selftest` rc=0 (ten PASS vector groups); round-one live cycle (demo record `docs/演示-evolve首轮-20261113.md`: real signals S1 norm account / S2 sentinel dual-repo / S3 registry audit, zero mocks; task-brief draft `docs/evolve-draft-cycle1-20261113.md`: candidates C1–C5, TOP1 = C1 red-triage score 12.0, curable-error reduction rate honestly 0.00% (frozen ledger excluded, error 1960→1960) plus the curable-basis measurement rule registered for the engine spec; companion engine draft `docs/draft-evolve-v55-20261113.md`; ops manual `docs/ops-evolve-手册-v1.0-20261113.md`: variation/selection/inheritance mapped to implemented machinery, draft-only safety invariants); suite hook-up (`t_evolve` case in `tests/run_tests.sh` · cw.sh routes `evolve`, six-place sync, 28 tools · `doc_lint` `DEFAULT_HELP_CAP` 27→28 on the registered-tool precedent · counts synced to 63 in `tests/README.md` + `README.md`); three-gate close: doc_lint consistent (help_run=28/28·drift=0) / suite passing twice (81 cases 62 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` pass (cw.sh + run_tests.sh); norm_lint tree re-run against the v53 baseline: 152 files error 2441→2449 warn 1036→1106: the +8 error delta sits entirely on the frozen ledger's committed v54 append (`更新账.md` byte-identical to HEAD this turn, zero writes); the two new engine/suite faces (`tools/evolve.py`·`tests/test_evolve.py`) carry 0 error 0 warn, the four new doc faces carry 0 error (warn = CJK residue data per the account-doc convention).
>
> **v54 snapshot (November 13, 2026, contributor-isolation tooling close)**: protocol `docs/contrib-isolation-protocol-v1.0-20261113.md` (contributor-isolation protocol v1.0: isolation lanes with the Main `y_e1_gamma_nodes/` subdirectory and Set topic-branch precedents, `contrib/<lane>/` lane placement with the `# --- contrib lane rows below ---` separator segment, the four-check intake pipeline audit→norm→gate→merge over the routed registry/norm/union/fix tools, the PR#48 tail-zone regeneration rule, fetch-first/canonical-first two-stream etiquette); tools `tools/contrib_intake.py` (read-only four-gate intake inspector, schema `rocqwash-contrib-intake/1`: registry union dry run / norm lint / gate expectation / lane isolation over a contribution face vs a base face, gates never short-circuit, BLOCK verdicts are data, exit 0/1/2/9) + `tools/registry_regen.py` (merge-target books verbatim as the draft bottom + canonical `#R<seq>-<md5-8>` rows tail-appended in dependency order, dry run by default, `--apply` writes only under an explicit `--out`, schema `rocqwash-registry-regen/1`); both `--selftest` rc=0; verification record `docs/检验-PR48-intake四闸-20261113.md` (the four-check pipeline run for real on Set PR#48: audit findings as data total 564, lane norm target empty, 8/8 witness visibility satisfied with 2 build-unreachable order-row mismatches, merge-check A2 firing as the already-landed guard, landed books byte-equal to the prescribed regeneration shape in both books); suite hook-up (`t_contrib_intake`/`t_registry_regen` cases in `tests/run_tests.sh` with self-supplemented minimal shells · cw.sh routes `contrib-intake` + `registry-regen`, six-place sync, 27 tools · `doc_lint` `DEFAULT_HELP_CAP` 26→27 on the registered-tool precedent · counts synced to 62 in `tests/README.md` + `README.md`); three-gate close: doc_lint consistent (help_run=27/27·drift=0) / suite passing twice (62 cases 61 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` pass (cw.sh + run_tests.sh); norm_lint tree re-run against the v53 baseline: 146 files (+6, every new face error-level 0) error 2441→2446 warn 1036→1056: the whole delta sits on the frozen ledger `更新账.md` (byte-identical to HEAD md5 `d0059f5d…`, a vintage of the committed baseline, zero writes this turn); the four new suite/tool faces carry 0 error 0 warn.
>
> **v53 snapshot (November 13, 2026 — annotation-face normalization work stream, constitution three laws [1 internationalization/normalization/English-ization + translation replacement and the jargon ban, 2 collaboration isolation, 3 autonomous recursive evolution], four deliverables cast plus the integration close)**: the two normative documents `docs/annotation-standard-v1.0-20261113.md` (annotation standard card v1.0: two-part file header, banner plus the five fields Purpose./Interface./Dependencies./Evidence./Exit-codes. verbatim; four forbidden-word families; bilingual transition rules [translation replacement is canonical, the original Chinese goes to a .zh.md archive instead of being deleted; code identifiers, CLI flags, JSON schema fields and exit-code semantics zero-change]; error/warn grading and the checker's 0/1/2/9 semantics) and `docs/jargon-to-standard-mapping-v1.md` (jargon-to-standard mapping table v1 = the card's Appendix A, 142 active word faces, per-row context notes, identifier exemptions on register); the checker `tools/norm_lint.py` (annotation-face normalization check, report-only first form: five checks over .py/.sh/.md prose faces [header shape / jargon word faces / CJK residue / forbidden classes / 30-line header cap] · schema rocqwash-norm-lint/1 · findings are data and the exit code never escalates on them · --selftest six vectors · *.zh.md and docs/zh/ archive faces exempt from scanning) + the baseline account `docs/norm-lint-baseline-20261113.{json,md}` (the repository's state stated as it is: files=140·error=2441·warn=1036·cjk_ratio=0.248597; identical-input reruns are byte-identical); four translated faces (the entry faces `cw.sh`/`cli/rocqwash`/`README-cw.md` + the four core tools `tools/ci_triage.py`/`tools/pushci.py`/`tools/unclog.py`/`tools/cw_sentinel.py`: headers/help faces Englished, identifiers/flags/schema fields/exit-code semantics zero-change, the original Chinese archived in `README-cw.zh.md`/`cli/rocqwash.zh.md`/`docs/zh/`, six archive pieces in total with the four tools' docstrings); four integration deliverables (1 the norm_lint repository-wide baseline account = the repository-wide scan with no allowlist, stated as it is, plus byte-identical-rerun verification; 2 the t_norm_lint hookup in tests/test_norm_lint.py, a minimal selftest shell with three checks, plus the full suite passing twice, doc_lint consistent, and bash -n over all .sh faces; 3 the cw.sh norm-lint route registered, twenty-five tools, six-place sync, plus the README-cw.md tool-table row and the doc_lint DEFAULT_HELP_CAP 24→25 bump [after norm_lint's registration 25 tools; the cap overflow `wash/probe_engine.py` per the v38/v46 precedent; --jobs is real and present in the help face; phantom-citation false positives cleared] plus doc_lint archive-face exemption [*.zh.md and docs/zh/ = the card's section 5.2 archives, not canonical faces] plus about 26 narrative word-face clearances on the entry faces [work stream / effort / work stream / agent narrations, date stamps, agent, narrative-sense route rewrites]; 4 the README v53 snapshot line and the CHANGELOG v53 entry plus the final jargon sweep on register = residue registered honestly: identifier-citation class [cw.sh route names ×5, README-cw.md example commands and doc-link filename dates ×6, cli/rocqwash adaptation sub-verb names ×4] + the four tools' inline-comment residue [jargon 2-14·cjk_ratio 0.11-0.19·module docstrings already Englished·function docstrings and inline comments left to the recursive work stream's reduction baseline]); three-gate close: doc_lint consistent (help_run=25/25·drift=0) / full suite passing twice (60 cases 59 pass 0 failing 1 skip ×2, skip=t_quad8_check) / `bash -n` all passing (cw.sh + run_tests.sh).
>
> **v52 snapshot (November 13, 2026 — Main new-content survey + the R3 recurrence precedent + the watcher-event consumption drill, three agents cast plus the integration close)**: survey agent `docs/勘形-Main新内容预热-20261113.md` (follow-up to the prior `docs/勘形-multi-repo-Main仓适配-20261112.md` current-state record; read-only api evidence over Main tip `d2e74c2b`, three new-content faces: 1 the `y_e1_gamma_nodes/` subdirectory, 92 pieces coexisting at both points (unregistered by design); 2 the unif limbs work stream (`planb4_l3_limbs_discharge.v` landed Live + dual-ledger registration, three limbs discharged); 3 the gate8 permanent vacuity sentinel (9e381d61); six evidence rounds + two real `ci_triage` builds (run#50 family=none 17 steps all passing / run#46 `--logs` two-hop family=B-netred, checkout couldn't find remote ref proven directly) → **the warm-up demand list, 10 items, verdict = 2 ready-to-use / 4 minor-change / 4 pending execution**); precedent agent `docs/判例-R3复发-route2tierA自愈-20261113.md` (recurrence precedent record, the first closed loop of the service layer: Set route2-tierA run#301/302 (sha `8f59c8f`) R3 "relative path cwd=workdir misalignment, all drivers failing within the same second" recurrence: the watcher caught it live (events.jsonl seq 58, 04:38) → `ci_triage` classification A-content-red → the sibling restore `bd8f38b` automatic recovery → run#303/304 both passing; first failing to recovered ≈20 minutes, the whole loop with zero manual steps; with the Set PR#48 eight-overlapping-blob 8/8 SAME survey warm-up note); drill agent `docs/演练-哨事件消费-20261113.md` (consumption drill, zero new features, a pure live run: the resident watcher's account production (`_log/sentinel_v48/` JSONL event stream) consumed three ways: `render_events` ledger (data surface) / record list (generic prose) conversion (events_total=64·bad_lines=0) + event analysis (kind/family distribution, live-catch list, UNREC-maintained inventory) + state.json seen reconcile and report.json round-history continuation verification (round1→3 progression, the 600s cadence proven live) · 65 events in the terminal state parallel to the resident watcher's window · three mismatches against the task brief's given shape registered honestly, the actual runs taken as authoritative); three integration deliverables (the README v52 snapshot line / the full suite passing twice by standing order / the docs inventory survey = no standalone inventory document, the three pieces registered by name via this snapshot line, same method as v49-v51 · `更新账.md` untouched); three-gate close: doc_lint `--help-cap 24` consistent / full suite passing twice (59 cases 58 pass 0 failing 1 skip ×2) / `bash -n` all passing (run_tests.sh).
>
> **v51 snapshot (November 12, 2026 — watcher resilience fix + triage refinement + the supervisor-shell deployment piece, three agents cast plus the integration close)**: watcher resilience fix `tools/cw_sentinel.py` (the v50 round10 IncompleteRead transport-layer crash [`更新账.md:3999`] tool fix on two tracks: 1 the resilience layer, bounded retries for transient transport breaks, `--net-retries` default 3 with 5s/15s/45s backoff [TRANSIENT_TRANSPORT_ERRORS = IncompleteRead/RemoteDisconnected/BadStatusLine/ConnectionError/socket.timeout, distinct from the HTTPError status-code face]; exhaustion keeps the 9 fail-loud; non-transient errors are never swallowed and rethrow as-is; 2 the loop layer, per-source fallback = an erroring source skips the round with a loud source-error event · skip the round rather than crash the resident process · an unseen event re-reports next round, duplication preferred over loss · `once` passes straight through with the rc 9 fail-loud semantics unchanged; selftest vectors 14/15, two canned-injection vectors [canned IncompleteRead real-crash stack same shape 371261/72721 · loop 401 two rounds rc0 against once 9]); triage refinement `tools/ci_triage.py` (the review-ledger (data surface) / record list (generic prose) token two-shape bounded form landed: the E-variant conclusion-position check: the GATE2-ATTEST-RED / `判定=CLEAN` genuinely-executed token present [after dump-line filtering] = the attestation-state failing form stays UNRECOGNIZED and does not inflate the spectrum = the run#10 conversion acceptance check [tool verdict = re-check conclusion · the v50 E false positive cleared] · the coqchk step success fully-completed form likewise stays UNREC · the banner-absent form stays E [run#7/8/20/26]; KEY_LOG_PATTERNS gains GATE2-ATTEST-RED / R4 coverage partition / missing appendix, three tokens = all five tokens on register + dump-line filtering [teal script echo / group command lines are not genuinely-executed lines] with `--no-dump-filter` to disable + the `--offline` top-level job_logs extension slot for canned log injection; `tests/fixtures/ci_triage_gate2_only_{cancelled,failure}.json` gain canned job_logs genuinely-executed-line transcriptions [run#7 banner-absent real line + 2 dump lines / run#10 ATTEST-RED real line + 1 dump line = the evidence-trap original form on register]); supervisor-shell deployment piece `examples/sentinel_supervisor.sh` (the canonical deployment shape of the auto-restart compensation shell for a crashed resident watcher: restart cap / ×2 exponential backoff / state continuation note / scheduled-teardown hook slot left empty / rc triage [0 rounds exhausted self-stop · 2 usage error stays out of the restart loop · 9 the rest back off and count toward the cap] · all paths parameterized, zero hard-coding) + `docs/ops-sentinel-长驻手册-v1.0-20261112.md` section 1.6 supervisor deployment shape + `examples/README.md` bilingual registration; three integration deliverables (mounting confirmation = the three agents' new vectors all reach the suite through the existing t_cw_sentinel/t_ci_triage `--selftest` registered cases, run_tests.sh zero new mount points, comment registration only / the README v51 snapshot line / real-network spot check = watcher `--once` real network rc=0 after the resilience fix); three-gate close: doc_lint `--help-cap 24` consistent / full suite passing twice (59 cases 58 pass 0 failing 1 skip ×2) / `bash -n` all passing (supervisor shell + run_tests.sh).
>
> **v50 snapshot (November 12, 2026 — the UNREC 14-event classification cross-validation integration round, three agents cast plus the integration close)**: tooling agent, the triage fix (`tools/ci_triage.py` logs endpoint two-hop 415 fix [Accept application/vnd.github+json → 302 signed URL → second hop without Authorization, 200 · probe (tool citation) / check (generic sense) measured live; the 415/403/404 original codes kept as evidence] + the gate2-only joint form into spectrum variant E [the failing-step set ⊆ {gate2 + upload family} with the pure gate2 failing steps on register · the preceding build/coqchk not content-failing · provenance Main retro #7/#8/#20/#26 banner-absent four runs + #10 attestation-state failing one run] + `tests/fixtures/ci_triage_gate2_only_{cancelled,failure}.json`, two real-shape pieces [retro ledger (data surface) / record list (generic prose) run#7/#10 field-by-field transcription · selftest vector 10 hooked directly] + `docs/retro-triage-Main仓全史-20261112.md` section 8 supplement); re-check agent `docs/复核-UNREC-14事件-20261112.md` (watcher 8 + retro 6 = 14 pieces, piece-by-piece manual classification as independent ground truth · conclusion distribution over 14 rows A×1/B×1/E×8/UNREC maintained ×4 · the gate2-only step-name form's two-phase behavior: GATE-BANNER-ABSENT joint ×4 runs → E / GATE2-ATTEST-RED attestation state ×1 run (Main#10 · parser CLEAN axioms=0 · R4 partition broken) → UNREC manual attribution); verification agent `docs/验证-Main档案位实用化-20261112.md` (the Main archive slot three steps all passing: fetch direct rc=0 + tip three-face alignment `2f793c4` + registry_audit five accounts emitted + pushci --dry-run two real-repository runs idempotent and byte-identical, zero side effects); integration cross-validation (post-fix tool face `--repo/--run --logs` online re-judgment over 8 distinct runs / 14 ledger (data surface) / record list (generic prose) rows: **agreement rate run-level 5/8 · row-level 10/14** · the 3 runs and 4 rows of disagreement registered piece by piece, no forced convergence: S1 Set#284 run-level out-of-spectrum placement masking the mac primary failure [job-level tool face = A, agreeing with the re-check] · S2 Set#286 classification order E>B taking the first, masking the mac primary failure [job-level tool face = B, agreeing] · S6/R4 Main#10 E-variant false positive = the GATE2-ATTEST-RED attestation-state failing form swallowed by the step-name subset rule + the GATE-BANNER-ABSENT teal dump line as false corroboration [the genuinely-executed line = `判定=CLEAN`, axiom total = 0] = the re-check ledger (data surface) / record list (generic prose) section 3-2 trap face reproduced by the tool face: disagreement is the next candidate for the classification spectrum: scan-layer dump-line filtering / the five tokens GATE2-ATTEST-RED etc. on register / the attestation-state failing form stays UNREC and must not inflate the spectrum); three-gate close: doc_lint `--help-cap 24` consistent / full suite passing twice / `bash -n` all passing.
>
> **v49 snapshot (November 12, 2026 — the Main repository adaptation minor-change + measured conclude/close round, four agents cast together plus the integration close)**: two Main-shape fixture pieces into tests/ (`tests/fixtures/ci_triage_main_coq93.json` = Main CI 9.3 coq93.yml real shape, 16-step canned + `tests/fixtures/pushci_scenarios/s7_main_dry_run.json` = branch main direct-push route dry-run) · consumption face = `tools/ci_triage.py --selftest` vector 9, the Main-shape reading vector (compatibility table 15 rows machine-checked + the two E pieces present) + `tests/test_pushci.py` seven-scenario shell (t_ci_triage/t_pushci existing cases already mounted and registered · run_tests.sh zero changes); the retro ledger (data surface) / record list (generic prose) `docs/retro-triage-Main仓全史-20261112.md` (Main full history 369 runs actually taken · the active coq93 31 entries judged one by one + the coq#340 bridge piece · the failing-build union 19 events · reconcile with the watcher 30/30, zero disagreement); K3b resampling `examples/baselines/audit-k3b-20261112.json` (probe_chain_s=190.719 · perf-profile rule 1, first sample of the noise band [165.202, 190.719] · K=3 no gain, two runs, robust conclusion); total report v2.0 `docs/rocqwash-service-campaign-total-v2.0-20261112.md` (the v1.0 base fully preserved + the v43-v48 six-round supplement chapters); three-gate close: doc_lint `--help-cap 24` consistent / destructive-surface matrix 17 checks all passing / full suite 59 cases 58 pass 0 failing 1 skip (the t_quad8_check four-repository-copy group missing its originals · SKIP not counted as failing).


## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: twenty-four deterministic idempotent rewrite patterns — the legacy five (bridge-wrapped rewrite, goal-opening downshift, opaque-reflexivity cure, qualified successor form, NatLe supply bridge), nine v1.1 statement-face patterns from the November 3, 2026 wash-effort field report (Qle/Qlt carrier-face downshifts in token and %-scoped notation forms, refl bridge opener, Import-shadow direct-face qualification as two exclusive variants with fail-loud conflict detection, NatLe premise lift + intros-tail-guarded drop wrap), five v1.2 S07-lineage adaptation patterns from the W66 field report (parameterized-shell drop with a :=-binding-right guard, notation rebind line-insertion, @field projection-bridge bare form, predicate-face convergence token map whose targets must be the consuming supply lemma's conclusion constant names, and a report-only binder-shell station for the manual binder surgery), and five v1.3 patterns for the CI #178 extraction-defect families (E3 generic-interface instantiation: abstract-carrier application stations rewritten to a concrete-carrier specialization shim generated after the last import; E2 record polymorphic field: the un-annotated field-consumption Definition restated as an explicit-type-annotated middleware with downstream arity adaptation and a report-only sweep-completion station), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |
| `tools/pushci.py` | Push-CI one-shot pipeline orchestrator: five stages — preflight emission gate (dyld doctor verdict + net-probe stable window + optional gate4 comment pre-scan; the no-emission-on-single-probe discipline is codified here), push (retry ×3 + ghproxy re-route for https://github.com/ remotes; pushed_sha = ls-remote remote tip), CI watch (status-only polling — a frozen updated_at is not a zombie verdict), heal (ci_triage family route: NETRED/coqchk-skipped → stable-window → rerun, capped; content-red is never auto-fixed; off-table families are never auto-rerun), verdict ± PR merge — seven-state verdict (`success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|dry-run`), exit codes 0/1/2/9; orchestrates the v35 four tools via subprocess, zero new engines; fully offline-injectable (`--injector`/`--git-caller`/`--sleep-scale`) | Deterministic state machine over mechanical gates; LLM cannot be trusted to decide emission windows or auto-heal policies |

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
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + campaign tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + campaign tools
├── verify/               # verify_vo.py four-point pass criterion + 战役验证工装 — four-pack green verdict + campaign verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（87 例）/ CI 工作流占位 — test suite (87 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> Status snapshot November 1, 2026 (inspection-and-polish pass rqsup4): `scan/`, `names/`, `tools/cpu_guard.sh`,
> `cli/`, `examples/`, `docs/`, `tests/` (34-case self-test suite) implemented and live-tested; `wash/`
> (`wash_engine.py` ledger (data surface) / record list (generic prose) wash engine + `_abl1_wash.py` effort piece + `world_hook.py` world-baseline validation hook,
> lesson 1), `verify/` (`verify_vo.py` four-point pass criterion + effort verify tooling + `verify_gate6.py` gate6 thin wrapper,
> lesson 3), `seam/` (`seam_probe.py` W13 four-mechanism fingerprint probe), `certify/` (`freeze_manifest.py`
> two-tier freeze manifest + `push_gate.py` push-window four-criteria/UNION v2 deep piece, agent rqwash2, + `frozen8.py`
> frozen-eight registry machine check), `watch/`
> (`watch.py` CI monitoring / pin-IP push / ls-remote confirmation, zero-route structural guarantee), `tools/`
> (`select_audit.py` selection auditor, lesson 2), `recipes/` (`S07_projection_reanchor_E5.md`
> lesson 4 + `ENBIG7_same_domain_collision_PW1.md` lesson 3, two precedent prescription pieces), `wrapper/`
> (adapter family: gate7 probe chain `coqc_shim.sh` + `gate7_probe.sh`, cpu_guard pass-through
> `guard.sh`, scan station wrapper `scan_station.py`, agent rqadapt, three-precedent acceptance station
> `precedent_station.py`, lesson 5 rqsup4) all landed;
> the `verify/` unified entry is concluded/closed (explicit sub-verb routing `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`,
> rqadapt landed the three sub-verbs on October 31, 2026; a fourth inspection pass added verify_gate6 on November 1, 2026); `certify/`
> carries the same explicit routing `cli/rocqwash certify freeze|push_gate|frozen8` (a fifth inspection pass added
> frozen8 on November 1, 2026) — the frozen pieces zero-change; the R4 extraction-side three sources remain open work.
> v30 addendum (November 3, 2026, probe-effort tooling round): `wash/probe_engine.py` batch closure-compatibility
> probe (tool citation) / check (generic sense) engine + `tools/chain_graph.py` multi-ledger chain-root graph + `tools/ledger_sync.py`
> probe × status ledger (data surface) / record list (generic prose) synchronizer (E1 dedup / E3 ghost / column validation fail-loud) — generalizing the W13/W25/ledger (data surface) / record list (generic prose)
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
> troubleshooting, and blockage clearing): `tools/cw_sentinel.py` realtime watcher (three signal sources: CI runs / ledger (data surface) / record list (generic prose)
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

## Getting Started (5 minutes)

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
# [gate4ext] ... 件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```

## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Quick Start

```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing)
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper (dry-run by default; masked output; --yes actually pushes)
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
```

## Seven Canonical Steps (all mandatory, in order)

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic 436f712100015ff4 / vo newer than v / PA Closed / coqchk Axioms:none)
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
