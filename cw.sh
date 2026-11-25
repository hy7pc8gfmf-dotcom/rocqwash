#!/usr/bin/env bash
# cw.sh — unified entry for the rocqwash tool suite
#         (repository root; bash 3.2 compatible).
#
# Purpose.  Routes the suite's tools by explicit tool name: one usage line and one target script per tool.
#   Arguments and exit codes pass through unchanged (direct exec, fail-loud, never rewritten).
#   The pre-v29 modules keep their dedicated cli/rocqwash router; this entry covers the newer tools/ faces.
#
# Interface.  bash cw.sh <tool> [args...]; bash cw.sh help [tool].
#   A bare cw.sh call prints the full help; cw.sh help <tool> prints the tool's one-line usage hint.
#
# Dependencies.  bash 3.2 (no associative arrays, no bash-4+ features); python3 runs every routed target.
#   ROOT derives from this script's own directory, so all paths stay repository-relative and the repository can be relocated freely.
#
# Evidence.  tests/test_cw_entry.sh exercises this entry end to end: help table, hints, passthrough, the zero-hardcoding proof, the bash 3.2 syntax check.
#   tools/doc_lint.py cross-checks the four tool-table places against the case routes on every suite run.
#
# Exit-codes.  0 pass; 2 unknown tool; 9 target script missing.
#   Any other code is the routed tool's own convention, passed through.
#
# Tool table (one usage line + target script per tool; args and exit codes pass through 1:1):
#   scan4       token-level qualified-identifier census -> scan/scan_v4_token.py
#               cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
#   cure        consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py
#               cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
#   probe       batch closure-compatibility probe engine -> wash/probe_engine.py
#               cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
#   chain       multi-ledger merge chain-root graph -> tools/chain_graph.py
#               cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
#   sync-ledger probe-ledger x status-ledger merge sync -> tools/ledger_sync.py
#               cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
#   erasure     extraction erasure-position classification advisor -> verify/erasure_classifier.py
#               cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
#   dual-scan   dual-scanner cross-check driver -> scan/dual_scan.py
#               cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
#   doctor      dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes)
#                                                    -> tools/toolchain_dyld_doctor.py
#               cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
#   net-probe   network-window probe (double-probe stable window; a single probe never authorizes emission) -> tools/net_probe.py
#               cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
#   triage      CI red-run triage (five families + green-run classification spectrum) -> tools/ci_triage.py
#               cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
#   union       registry union surgery (dry-run by default) -> tools/registry_union.py
#               cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
#   pushci      push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge)
#                                                    -> tools/pushci.py
#               cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
#   sentinel    real-time watch sentinel (three signal sources -> JSONL event stream; once/loop dual mode)
#                                                    -> tools/cw_sentinel.py
#               cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
#   wash-shape  canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default)
#                                                    -> tools/wash_shape.py
#               cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
#   unclog      blockage-unclogging closed loop (probe collection -> chain-root pick -> cure application -> re-check -> verdict; dry-run by default)
#                                                    -> tools/unclog.py
#               cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
#   cw-doctor   aggregate health check, four domains (environment/network/registry/clogs -> health score + advice; diagnosis only)
#                                                    -> tools/cw_doctor.py
#               cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
#   doc-lint    docs-to-implementation consistency linter, three checks (tool table / counts / flags; verdict consistent|drift)
#                                                    -> tools/doc_lint.py
#               cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
#   netname-normalize  .v.v double-suffix clean-name normalization (mapping table + --apply rename with md5 verification)
#                                                    -> tools/netname_normalize.py
#               cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
#   select-audit batch-selection auditor (selection list vs order.txt full-table grep dedup + Require-surface audit v6)
#                                                    -> tools/select_audit.py
#               cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]
#   baseline-diff clog-baseline differ (two unclog --audit baselines -> added/removed/persistent three lists + four-state verdict; argv order old then new)
#                                                    -> tools/baseline_diff.py
#               cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
#   render-events  sentinel-event JSONL to markdown ledger (three-dimension distribution + per-event table; malformed-line tolerant)
#                                                    -> tools/render_events.py
#               cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
#   dispatch    red-event router (sentinel red events -> action presets; three tiers report-only/suggest/auto)
#                                                    -> tools/red_dispatch.py
#               cw.sh `dispatch` --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]
#   audit       registry hygiene auditor (dual-book read-only four-account output + deterministic prescription; --apply does not exist)
#                                                    -> tools/registry_audit.py
#               cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]
#   registry-fix registry prescription applier (applies audit fix-plan items one by one; dry-run by default)
#                                                    -> tools/registry_fix.py
#               cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]
#   norm-lint   annotation-face normalization linter, report-only first form (header banner + five-field block / jargon mapping-table faces / CJK residue / forbidden classes / header budget; findings are data, the exit code never escalates on them)
#                                                    -> tools/norm_lint.py
#               cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]
#   registry-regen contribution registration-row regenerator (merge-target books verbatim + canonical #R<seq>-<md5-8> rows tail-appended in dependency order; dry-run by default)
#                                                    -> tools/registry_regen.py
#               cw.sh registry-regen --base-repo REPO --base-ref REF --contrib-repo REPO --contrib-ref REF --pieces M1,M2,... --anchor-src DIR [--dep-source require|coqdep|registry|auto] [--seq N] [--out DIR] [--apply] [--json P]
#   contrib-intake contribution intake inspector (read-only four-gate verdicts over a contribution face vs a base face: registry union dry run / norm lint / gate expectation / lane isolation; gates never short-circuit, BLOCK verdicts are data and the exit code stays 0)
#                                                    -> tools/contrib_intake.py
#               cw.sh contrib-intake --contrib-repo PATH --contrib-ref REF --base-repo PATH [--base-ref REF] [--paths P1,P2] [--order-path PATH] [--project-path PATH] [--lane-prefix PREFIX] [--jargon-map PATH] [--rocq-cmd CMD] [--json P]
#   evolve      autonomous evolution engine v1 (harvest five signal classes from the existing engines -> derive scored candidates -> draft the human-gated next-round task brief; draft-only: never executes a candidate, never writes the repository)
#                                                    -> tools/evolve.py
#               cw.sh evolve --draft-out PATH [--json P] [--top N] [--baseline P] [--watch-repo ORG/REPO]... [--sentinel-state F] [--suite-ledger F | --suite-now] [--registry-git REPO --registry-ref REF] [--selftest]
#   vacgen      Lean vacuity probe skeleton generator (four-account casting, zero compile, pure stdlib; v1 CLI face preserved, v2 flags additive) -> tools/vacgen.py
#               cw.sh vacgen --in F [--out DIR] [--toolchain T] [--snapshot S] [--preflight-all] [--taxonomy P] [--force]
#   ci-triage   CI red-run triage, alias of triage (same target script) -> tools/ci_triage.py
#               cw.sh ci-triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
#   exp-append  experience-ledger appender (schema rocqwash-exp/1, idempotent seen set; the MCP exp_append face) -> tools/exp_port.py
#               cw.sh exp-append --tool T --points P [--evidence E] [--batch B] [--id ID]
#   baseline-diff-facade  clog-baseline differ, alias of baseline-diff (same target script) -> tools/baseline_diff.py
#               cw.sh baseline-diff-facade OLD.json NEW.json [--json out.json] [--md out.md]
#   mcp-server  rocqwash MCP stdio server (JSON-RPC 2.0 over stdio; capability true names follow docs/CAPABILITY-INDEX.md) -> tools/mcp_server.py
#               cw.sh mcp-server   (stdio transport; drive from an MCP client, not interactively)
#   periscope   six-source peripheral-intelligence sweep (sentinel companion window log + judgment draft skeleton; read-only GET) -> tools/periscope.py
#               cw.sh periscope --config F [--out DIR] [--rounds N] [--dry-run]
#   ai-flavor   AI-wording word-face detection body (36-face battery + separate em-dash battery; hits are data, not errors; word map read-only) -> tools/ai_flavor.py
#               cw.sh ai-flavor --file <p> [--json out] | --tree DIR | --selftest
#   ai-flavor-apply AI-wording advisory apply face (writes only through the rewrite provider; handoff leg default zero-network; http leg default-deny; zh ban faces never machine-written) -> tools/ai_flavor_apply.py
#               cw.sh ai-flavor-apply --file <p> [--json out] [--emit-handoff out.jsonl | --apply-handoff in.jsonl --state p] [--provider handoff|http]
#   auto-round  round-ledger admission/rollback/salvage body (auto/gated gear per autonomy.json; append-only ledger; rollback = drift archive then one revert; no reset no force no push) -> tools/auto_round.py
#               cw.sh auto-round <command> [--repo-root P] [--autonomy P] [--state P] [--ledger P] [--continue] [--selftest]
#   i18n-pipeline zh-en four-linkage i18n pipeline orchestration (P0 policy pre-check / P1 segmenter / P3 four-linkage apply / P6 ledger closure; refusal is a legal exit-0 ledgered outcome) -> tools/i18n_pipeline.py
#               cw.sh i18n-pipeline --manifest run.json --stage p0|p1|p3|p6 [--json out] [--selftest]
#   i18n-translate model-site layer P2 of the i18n pipeline (handoff emit/ingest default zero-network; http leg optional default-deny; NETRED ledger line per call) -> tools/i18n_translate.py
#               cw.sh i18n-translate --segments <p> --emit out.jsonl [--prompts DIR] | --ingest in.jsonl [--provider handoff|http]
#   i18n-verify P4 mechanical verify orchestration + P5 human ten-point form face (the engine emits the form and ingests verdicts, never judges) -> tools/i18n_verify.py
#               cw.sh i18n-verify --verify-target <p> [--json out] | --emit-tenpoint <target> | --ingest-tenpoint verdicts.json | --selftest
#   jargon-apply jargon-to-standard apply face over the 62-entry map (replace entries only; human rows never machine-written; plan zero-write default; apply rescans to residue zero; idempotent) -> tools/jargon_apply.py
#               cw.sh jargon-apply --file <p> | --tree DIR [--plan | --apply] [--json out] [--guarded-interactive] [--selftest]
#   termbase    read-only terminology thin layer over seeds/termbase/termbase.json (exact-face lookup; schema validation fail-loud; a miss is data, exit 0) -> tools/termbase.py
#               cw.sh termbase --lookup <term> [--db <p>] [--json out] | --schema-check | --selftest
#   gap-cluster aggregate TODO-SEAT and gap ledger entries into a family-shape-keyed gap ledger (deterministic; byte-identical reruns; zero gaps is data) -> tools/gap_cluster.py
#               cw.sh gap-cluster [--ledger P]... [--reports P]... [--out FILE] [--json] | --selftest
#   row-render  gap ledger to candidate taxonomy rows through the E4 P2 handoff form (vacgen admission gate; ten-point human gate; a draft is written only on full admission) -> tools/row_render.py
#               cw.sh row-render --gaps P --emit OUT.jsonl | --ingest ROWS.jsonl | --check-draft DRAFT.json | --emit-tenpoint | --ingest-tenpoint V.json [--draft-out P] [--vacgen P] [--json]
#   calibration-ledger  pair vacgen v2 predicted confidence with the measured compile-leg rc into per-row calibration entries (correlationId; idempotent seen set; row-rot signal face; signals are data) -> tools/calibration_ledger.py
#               cw.sh calibration-ledger --report R.json --rc-file RC.json [--leg-map LM.json] [--default-leg NAME] [--ledger P] [--signal-threshold F] [--strict] [--dry-run] | --selftest
#   lean-sweep  vacuity probe batch sweep orchestrator (bins, dedups, casts with a zero-compile precheck; the compile leg is a designed SKIP unless --fire and the toolchain probe passes) -> tools/lean_sweep.py
#               cw.sh lean-sweep --batches B.json --out DIR [--json F] [--fire] [--lanes N] [--skip-ledgers F]... [--taxonomy FILE] [--bisect-max N] | --selftest
#   verdict-diff mechanical judge for sweep ledgers (GREEN/ALERT/BLOCKED/MISSING/SKIPPED-TIERT plus an exception list; ALERT exits 2 stop-work; baseline convergence caliber) -> tools/verdict_diff.py
#               cw.sh verdict-diff --results-lane "DIR/results-lane*.tsv" [--expected F | --batches F] [--json F] [--md F] [--baseline OLD.json] | --selftest
#   symbiosis-bus  cross-repository experience bus over docs/exp-ledger.jsonl (swap schema rocqwash-symbio/1; import walks the exp_port append face one call per entry; export/status/diff read-only; zero network by design) -> tools/symbiosis_bus.py
#               cw.sh symbiosis-bus export --out SWAP.jsonl [--ledger P] [--source-repo NAME] [--anchor HEX] [--dry-run] | import --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | diff --a A --b B
#   uplink      external return-package intake gate (verify / intake / pr-prep; md5 mismatch and missing declared members are fail-loud; the intake register row and the caller-named draft are the only writes; zero network by design) -> tools/uplink.py
#               cw.sh uplink verify --package P.zip [--digest HEX|SIDECAR] [--manifest M.md5] | intake --package P.zip --source-agent SEAT --landed-ref REF [--digest HEX|SIDECAR] [--manifest M.md5] [--register F] [--dry-run] | pr-prep --package NAME --out DRAFT.md [--register F] [--signature LINE]
#   evolution-dashboard  self-evolution dashboard over the three standing accounts (experience ledger + round ledger + vacgen v2 TODO-SEAT reports -> coverageLowerPct curve + rounds conversion + per-run gap thermometer; JSON + markdown faces; absent standing paths are data) -> tools/evolution_dashboard.py
#               cw.sh evolution-dashboard [--repo ROOT] [--exp-ledger P] [--rounds P] [--reports P]... [--json-out P] [--md-out P] [--stdout markdown|json] [--selftest]
#   bus-feeder  gap-ledger feeder for symbiosis swap packages (rocqwash-symbio/1 in, TODO-SEAT gap rows out; family-shape keyed, idempotent on id and fingerprint; the gap feed ledger is the only write face; zero network by design) -> tools/bus_feeder.py
#               cw.sh bus-feeder feed --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | --selftest
#   axiom-guard repo-wide axiom guard (every .v compiled and tri-classified: compile-ok / compile-broken debt register / skip-no-toolchain; two-level detection on compile-ok files: per-theorem Print Assumptions census plus the authoritative coqchk -o kernel recheck; Closed zero axioms, empty default whitelist; env-gated, rc 111 honest skip; zero repository writes) -> tools/axiom_guard.py
#               cw.sh axiom-guard --repo DIR [--out DIR] [--rocq BIN] [--coqchk BIN] [--allow-axiom NAME]... [--timeout SEC] [--keep]
#   source-fetch audit fetch face (dual-source cross-pin, sha256 pin from caller or CI-source file, HTML-trap sniff, NETRED backoff; honest-unverified and net-gated states are data) -> tools/source_fetch.py
#               cw.sh source-fetch --url URL [--sha256 HEX] [--sha256-source URL] [--mirror URL] [--trap-sniff] [--out DIR] [--timeout SEC] [--retries N] | --selftest
#   sweep-verdict batch sweep judge (per-lane result ledgers union-deduped into a GREEN/EXCEPTION/MISSING verdict table; expected-red interlock with baselinediff semantics; shared-append ledgers are the anti-pattern it exists to prevent) -> tools/sweep_verdict.py
#               cw.sh sweep-verdict --lanes DIR [--expected-red FILE] [--out FILE] | --selftest
#   release-chain release chain planner (issue body -> GitHub Release per-asset -> Zenodo deposit, three gated layers; dry-run by default, publish needs --confirm-publish; URLs and DOIs are taken verbatim from service responses) -> tools/release_chain.py
#               cw.sh release-chain --issue N --release-title T --assets DIR [--zenodo-meta FILE] [--repo OWNER/NAME] [--stage 1|2|3|4] [--dry-run] [--confirm-publish] | --selftest
#   claim-watch conclusion-level claim watch (the eight RH signals + three NS/Euler triggers from the seed config; machine-readable status endpoints; heartbeat silent-death and unverifiable registration; append-only actor-namespaced round ledger; live face) -> tools/claim_watch.py
#               cw.sh claim-watch --config FILE [--round-label L] [--ledger FILE] [--actor A] | --offline-selftest
#   axiom-sweep per-theorem Lean axiom-closure classifier (#print axioms via the target's own lake env; CLEAN / BENIGN-STANDARD trio / SORRY-ALARM / CUSTOM-AXIOM-ALARM / PRIVATE-COVERED / UNPARSED; closure snapshot plus baseline diff_alarm) -> tools/lean_axiom_sweep.py
#               cw.sh axiom-sweep --root FILE|DIR [--json OUT] [--snapshot OUT] [--baseline SNAP] [--allow-axiom NAME]... | --selftest
#   numeric-probe numerical claim verifier (stdlib exact arithmetic executes rational-bound and interval-containment claims; transcendental plans stay honestly PLANNED) -> tools/numeric_probe.py
#               cw.sh numeric-probe --claim FILE [--out FILE] | --selftest
#   statement-identity two-face statement identity prober (claimed vs proven normalization, three-seam classification, uncast-region matrix) -> tools/statement_identity.py
#               cw.sh statement-identity --claimed FILE --proven FILE [--out FILE] | --selftest
#   capability-index capability index reader (full and summary modes plus single-tool query over the census masters; summary exists because the full index overran harness response caps) -> tools/capability_index.py
#               cw.sh capability-index [--mode full|summary] [--tool NAME] | --selftest
#   axiom-audit Coq-side axiom audit (fixture-corpus census per coqc engine; declared axioms with file/line/form, reverse map to introducing files, platform grades classical/funext/stdlib; live engine required, unconfigured skips honestly) -> tools/axiom_audit.py

#               cw.sh axiom-audit census --repo DIR [--json OUT] | --selftest

#   vacgen-coq Coq-side statement ingestion and probe-cast planner (Rocq vernacular extraction, premise/conclusion split, data-driven taxonomy rows, Coq-L3 coverage metric; ticket 14 wave 1; zero network zero compile) -> tools/vacgen_coq.py

#               cw.sh vacgen-coq --from-v FILE|DIR [--taxonomy FILE] [--out DIR] [--limit N] | --selftest

#   flaky-guard flaky quarantine guard, repair class E2-3 (detect classifies each red case by an isolation probe: suite-red + alone-green = order-dependent, red in both contexts = content red that stays visible; --move quarantines into tests/advisory_roster.txt so the default suite drops it with a loud ADVISORY-OUT and the CI flaky-watch lane keeps observing it; scope-checked against tools/repair_scope.py, budget-capped at 2 per class per branch, ledgered in docs/repair-ledger.jsonl; dry-run by default; --restore needs green-round evidence) -> tools/flaky_guard.py
#               cw.sh flaky-guard --detect --log LOG [--json OUT] [--no-probe] | --probe CASE | --move CASE [--apply] | --restore CASE [--apply] [--green-rounds N] | --status | --selftest
#   repair-scope shared repair-scope exclusion table for the E2 guard family (frozen LEDGER8/CHECKERS rows read at runtime from certify/frozen8.py, the append-only ledger document, the frozen directory families; per-class writable faces + budget registry; the single source every repair guard imports) -> tools/repair_scope.py
#               cw.sh repair-scope --check PATH... | --classes | --selftest
#   roster-resync  roster count drift guard, repair class E2-2 (the run_tests.sh CASES roster is the only count authority; the doc_lint count lines of tests/README.md + README.md are re-derived one-way from it and the drifted digits are synced in place; the roster file is never written; scope-checked against tools/repair_scope.py, budget-capped at 2 per class per branch, every repaired line ledgered in docs/repair-ledger.jsonl; dry-run by default) -> tools/roster_resync.py
#               cw.sh roster-resync [--repo DIR] [--apply] [--ledger P] [--json OUT] | --selftest
#   scheduler-lite  TODO-SEAT threshold trigger planner for the jargon tier-B auto gear (gap feed ledger + vacgen reports through tools/gap_cluster.py plus the round cadence of docs/round-ledger.jsonl; verdict quiet | due | blocked; ignition gated on the EF all-green marker; dry-run by design: zero apply, zero commit, zero network) -> tools/scheduler_lite.py
#               cw.sh scheduler-lite [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--out F] [--json] | --selftest
#   auto-merge  X5 auto-merge gate judge plus safety rail (six-verdict mergeability enum merge-ok / hold-red / hold-conflict / already-landed / superseded-landed-elsewhere / escalate-unknown over caller-gathered facts; the five-sample calibration set S-1..S-5 pinned; rail = supply/* head-branch whitelist + daily budget cap 3 + append-only merge ledger + the post-merge red revert arc; zero network, dry run by default) -> tools/auto_merge.py
#               cw.sh auto-merge --facts F [--head-branch BR] [--allow-prefix P] [--daily-cap N] [--ledger P] [--merge-sha SHA] [--post-merge {green,transient,content,unrecognized}] [--apply] [--json OUT] | --selftest
#   jargon-map-sync  jargon map sync, md table to seed JSON (the detector map curated superset absorbed into the apply map; single-form admission: parenthetical annotations stripped, em-dash cells land as rewrite_or_delete, slash alternations and the six note-guard markers rejected; existing entries preserved with their id/exempts/cross_track_note; exact count label; plan zero-write default, --apply writes the map) -> tools/jargon_map_sync.py
#               cw.sh jargon-map-sync [--md P] [--map P] [--json P] | --apply | --selftest
#   repair-weekly  repair-outcome ledger weekly distribution face, repair class E6 (aggregates docs/repair-ledger.jsonl into the ISO-week per-red outcome census plus the class/ticket distributions; read-only over the ledger, --out/--json are the only write faces; --record appends one per-red rocqwash-repair-ledger/2 row under the enforced vocabulary, --apply required) -> tools/repair_weekly.py
#               cw.sh repair-weekly [--ledger P] [--date YYYY-MM-DD] [--out FILE] [--json P] | --record --class CLASS --target T --repair-outcome VALUE [--ticket K] [--evidence-file J] [--reason S] [--apply] | --selftest
#   selfevolve-round  one deterministic mechanical round, cron face (census jargon_apply --plan, then apply, then verify py_compile/bash -n hard gates plus norm_lint/doc_lint advisory, then auto_round commit, then push, then route the CI judge; frozen faces excluded by jargon_apply; zero qualifying fixes = clean no-op pass; apply residue nonzero = fail-loud, no commit) -> tools/selfevolve_round.py
#               cw.sh selfevolve-round [--dry-run]
#   pin-repair  provenance-pin drift repair for the jargon seed map, triage row R15 auto-repair executor (re-signs drifted provenance.sources md5 pins behind the sync tool's zero-write plan IN-SYNC verdict; --plan writes nothing, --apply touches only md5 values and re-runs the seeds suite, red verify rolls back to the pre-apply bytes; not-IN-SYNC exits without touching the seed) -> tools/pin_repair.py
#               cw.sh pin-repair --selftest | --plan | --apply [--seed P]
#   learning-feedback  scheduling feedback face over the three standing ledgers (round ledger, round state, experience ledger read-only; casts schema rocqwash.scheduling-feedback/1 into docs/scheduling-feedback.json: the auto versus human-approved round split, the approval rate, the per-class breakdown, and the four-state repair outcome tally; missing or corrupt inputs land in the errors field, never guessed) -> tools/learning_feedback.py
#               cw.sh learning-feedback [--selftest]
#   b-gate  B-level generalization threshold audit over the round records (3 instances, each grounded in at least 1 executed round; per-class instance and round counts, a per-class readiness verdict, and an explicit gap list into docs/b-gate-audit.json, schema rocqwash.b-gate-audit/1; counts are measured from the records, never inflated) -> tools/b_gate_audit.py
#               cw.sh b-gate [--selftest]
#   tree-audit  read-only tree health audit over .lean/.v source trees (one JSON-line census: totals, declarations, the unsound-feature sweep, comment faces, per-directory and largest-file tables, import roots; byte-literal counting calibrated to the census oracle; zero subprocess, zero network, zero tree writes) -> tools/tree_audit.py
#               cw.sh tree-audit --root DIR [--json OUT] | --selftest
#   pipeline-lite  gap-to-admission pipeline executor, D2-2 data layer (scheduler_lite plan verdict imported, never re-derived; gap_cluster clusters transformed to row_render gap rows with the layer-law policyPrecheckRef stamped; emit packet then ingest a backfill into a draft whose rows enter at tenpointVerdict PENDING; quiet and blocked write nothing; pending-backfill and pending-human stops are data; code-layer faces (ten-point verdicts, taxonomy row integration, apply pass, auto_round commit and approve) stay human-gated and are never composed; b-gate audit counter carried read-only; zero network) -> tools/pipeline_lite.py
#               cw.sh pipeline-lite [--plan F] [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--gap-out F] [--render-gaps F] [--packet-out F] [--backfill F] [--draft-out F] [--b-gate-audit P] [--policy-ref S] [--stop-at {data,human}] [--json] | --selftest
#   anchor-guard  anchor and certificate guard for one module directory (manifest validation V1-V10, module compile tri-classification in a private temp workdir, coqchk -o kernel recheck baseline, per-anchor probe face over vm_compute checks plus Print Assumptions, mutation kill matrix over the manifest's copied defect rows: a certificate that kills zero mutants is VACUOUS and red, a non-hold baseline is an unanchored anchor, module compile-broken is red; manifest copies its mutant rows from tools/mutants-v1.json, the guard never loads the library; env-gated, rc 111 honest skip; zero repository writes) -> tools/anchor_guard.py
#               cw.sh anchor-guard --repo DIR --manifest FILE [--out DIR] [--rocq BIN] [--coqchk BIN] [--timeout SEC] [--keep] | --selftest
#   help        this help (help <tool> = the tool's one-line usage hint)
#
# Routing contract:
#   1. All paths resolve relative to the repository root (ROOT derives from this script's own directory); zero hardcoded absolute paths, so the repository can be relocated freely.
#   2. Arguments and exit codes pass through 1:1 (direct exec, fail-loud, never rewritten); same contract as cli/rocqwash.
#   3. Exit codes: 0=pass; 2=unknown tool; 9=target script missing; anything else follows each tool's own convention and passes through (per-tool conventions: --help/--selftest=0; argparse usage errors / FAIL-LOUD assertion failures=2; missing target files=9).
#      (pushci) verdict seal: success/dry-run=0; heal-exhausted/unstable/toolchain=1; fix-content/gate4-block=2; 9=target missing.
#      (v37 trio) same shape: 0=green / inspection complete / unclogged; 1=data-side incomplete (shaping partial / plan-miss; wall / rounds-exhausted — a failing result is data, not a tool failure, reported loudly on stdout); 2=usage error; 9=missing / fail-loud.
#      (cw-doctor) same shape: 0=healthy (aggregate score >= 90); 1=degraded (a failing result is data, not a tool failure, reported loudly on stdout); 2=usage error; 9=missing / fail-loud.
#      (doc-lint) same shape: 0=consistent (all three checks drift-free); 1=drift (a check drifted; a failing result is data, not a tool failure, reported loudly on stdout); 2=usage error (--help-cap<1); 9=missing (required input absent / a failing or timed-out tool --help run, fail-loud).
#      (baseline-diff) same shape: 0=improved/stable (failing blocks fewer or equal); 1=degraded/incomparable (failing blocks increased, or an honest refusal on a changed candidate set; a failing result is data, not a tool failure, reported loudly on stdout); 2=usage error / malformed input (schema mismatch / ledger self-consistency broken); 9=path missing.
#      (route) same shape: 0=processing complete (a failing result is data, not a tool failure; a dispatched rc!=0 / timeout / dedup skip is recorded without touching the exit code); 2=usage error (--param guard / --dry-run tier mismatch / negative --cooldown); 9=missing input (event file absent / missing fields listed item by item / unresolvable parameter / metacharacter refused at construction / malformed state refused).
#      (audit) same shape: 0=report emitted (findings are data; count>0 still exits 0, reported loudly on stdout); 2=usage error (parameter mismatch / no input surface / only one of the two books given); 9=missing input (book files / git show / live-src / anchor-src absent).
#      (registry-fix) same shape: 0=dry-run report emitted, or --apply written plus all three assertions passed; 2=usage error (schema mismatch / missing fix_plan / same-parameter breach / entry key missing / AssertBlast assertion failure — the report carries evidence after a rollback); 9=missing input (audit JSON / the two books / the audit tool / anchor-src directory absent).
#      (norm-lint) same shape: 0=accounted (report-only: findings are data, the exit code never escalates on them); 1=selftest red (an assertion in the five selftest vectors failed); 2=usage error (no scan face / both --tree and --file / --gate or --strict reserved / negative --cjk-threshold); 9=missing input (tree or file absent / jargon map unreadable / CJK whitelist unreadable).
#      (registry-regen) same shape: 0=draft produced (BLOCK pieces are data, reported loudly); 1=selftest red; 2=usage error (apply without out / empty pieces / negative seq) or assertion failure (key collision / new anchor-text collision / dependency cycle / entity ambiguity / entity-blob divergence / write integrity - failure means zero writes); 9=missing input (repo / ref / book / anchor-src directory absent, coqdep absent when selected).
#      (contrib-intake) same shape: 0=verdict issued (a BLOCK verdict is data, reported loudly; gates never short-circuit); 1=instrument failure (no verdict can be issued); 2=usage error; 9=missing input (face path absent / ref unresolvable / instrument missing).
#   4. bash 3.2 compatible (no associative arrays, no bash-4+ features); the routing layer is read-only and itself writes nothing.
# Coverage note: cli/rocqwash routes the pre-v29 modules (scan/names/ wash/verify/seam/certify/watch); the v29-v32 tools, the v35-v39 five tools (doctor/net-probe/triage/union/pushci), the v37 trio (cw_sentinel/wash_shape/unclog) and the v38 aggregate doctor (cw_doctor) live in module directories holding several generic entries each, where the auto-router's ambiguity guard (exit 4) deliberately declines to guess; this entry fills the gap by explicit tool name, so the two entries are complementary.
#

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() { cat <<'EOF'
cw.sh — unified entry for the rocqwash tool suite (32 tools · bash 3.2 compatible)
(zh transition note: this help is English-first; the full original Chinese quick reference is archived in README-cw.zh.md)

Usage: bash cw.sh <tool> [args...]

Tools:
  scan4       token-level qualified-identifier census -> scan/scan_v4_token.py
              cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]
  cure        consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py
              cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]
  probe       batch closure-compatibility probe engine -> wash/probe_engine.py
              cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]
  chain       multi-ledger merge chain-root graph -> tools/chain_graph.py
              cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]
  sync-ledger probe-ledger x status-ledger merge sync -> tools/ledger_sync.py
              cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]
  erasure     extraction erasure-position classification advisor -> verify/erasure_classifier.py
              cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]
  dual-scan   dual-scanner cross-check driver -> scan/dual_scan.py
              cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]
  doctor      dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes)
                                                   -> tools/toolchain_dyld_doctor.py
              cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]
  net-probe   network-window probe (double-probe stable window; a single probe never authorizes emission) -> tools/net_probe.py
              cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]
  triage      CI red-run triage (five families + green-run classification spectrum) -> tools/ci_triage.py
              cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
  union       registry union surgery (dry-run by default) -> tools/registry_union.py
              cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-*
  pushci      push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge)
                                                   -> tools/pushci.py
              cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]
  sentinel    real-time watch sentinel (three signal sources -> JSONL event stream; once/loop dual mode)
                                                   -> tools/cw_sentinel.py
              cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]
  wash-shape  canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default)
                                                   -> tools/wash_shape.py
              cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]
  unclog      blockage-unclogging closed loop (probe collection -> chain-root pick -> cure application -> re-check -> verdict; dry-run by default)
                                                   -> tools/unclog.py
              cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--json out] [--events F] [--loop --interval S] [--injector DIR]
  cw-doctor   aggregate health check, four domains (environment/network/registry/clogs -> health score + advice; diagnosis only)
                                                   -> tools/cw_doctor.py
              cw.sh cw-doctor [--json out.json] [--registry PATH] [--src DIR --sample N] [--injector DIR]
  doc-lint    docs-to-implementation consistency linter, three checks (tool table / counts / flags; verdict consistent|drift)
                                                   -> tools/doc_lint.py
              cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]
  netname-normalize  .v.v double-suffix clean-name normalization (mapping table + --apply rename with md5 verification)
                                                   -> tools/netname_normalize.py
              cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]
  select-audit batch-selection auditor (selection list vs order.txt full-table grep dedup + Require-surface audit v6)
                                                   -> tools/select_audit.py
              cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]
  baseline-diff clog-baseline differ (two unclog --audit baselines -> added/removed/persistent three lists + four-state verdict; argv order old then new)
                                                   -> tools/baseline_diff.py
              cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]
  render-events  sentinel-event JSONL to markdown ledger (three-dimension distribution + per-event table; malformed-line tolerant)
                                                   -> tools/render_events.py
              cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]
  dispatch    red-event router (sentinel red events -> action presets; three tiers report-only/suggest/auto)
                                                   -> tools/red_dispatch.py
              cw.sh `dispatch` --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]
  audit       registry hygiene auditor (dual-book read-only four-account output + deterministic prescription; --apply does not exist)
                                                   -> tools/registry_audit.py
              cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]
  registry-fix registry prescription applier (applies audit fix-plan items one by one; dry-run by default)
                                                   -> tools/registry_fix.py
              cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]
  norm-lint   annotation-face normalization linter, report-only first form (header banner + five-field block / jargon mapping-table faces / CJK residue / forbidden classes / header budget; findings are data, the exit code never escalates on them)
                                                   -> tools/norm_lint.py
              cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]
  registry-regen contribution registration-row regenerator (merge-target books verbatim + canonical #R<seq>-<md5-8> rows tail-appended in dependency order; dry-run by default)
                                                   -> tools/registry_regen.py
              cw.sh registry-regen --base-repo REPO --base-ref REF --contrib-repo REPO --contrib-ref REF --pieces M1,M2,... --anchor-src DIR [--dep-source require|coqdep|registry|auto] [--seq N] [--out DIR] [--apply] [--json P]
  contrib-intake contribution intake inspector (read-only four-gate verdicts over a contribution face vs a base face: registry union dry run / norm lint / gate expectation / lane isolation; gates never short-circuit, BLOCK verdicts are data and the exit code stays 0)
                                                   -> tools/contrib_intake.py
              cw.sh contrib-intake --contrib-repo PATH --contrib-ref REF --base-repo PATH [--base-ref REF] [--paths P1,P2] [--order-path PATH] [--project-path PATH] [--lane-prefix PREFIX] [--jargon-map PATH] [--rocq-cmd CMD] [--json P]
  evolve      autonomous evolution engine v1 (harvest five signal classes from the existing engines -> derive scored candidates -> draft the human-gated next-round task brief; draft-only: never executes a candidate, never writes the repository)
                                                   -> tools/evolve.py
              cw.sh evolve --draft-out PATH [--json P] [--top N] [--baseline P] [--watch-repo ORG/REPO]... [--sentinel-state F] [--suite-ledger F | --suite-now] [--registry-git REPO --registry-ref REF] [--selftest]
  vacgen      Lean vacuity probe skeleton generator (four-account casting, zero compile, pure stdlib; v1 CLI face preserved, v2 flags additive) -> tools/vacgen.py
              cw.sh vacgen --in F [--out DIR] [--toolchain T] [--snapshot S] [--preflight-all] [--taxonomy P] [--force]
  ci-triage   CI red-run triage, alias of triage (same target script) -> tools/ci_triage.py
              cw.sh ci-triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]
  exp-append  experience-ledger appender (schema rocqwash-exp/1, idempotent seen set; the MCP exp_append face) -> tools/exp_port.py
              cw.sh exp-append --tool T --points P [--evidence E] [--batch B] [--id ID]
  baseline-diff-facade  clog-baseline differ, alias of baseline-diff (same target script) -> tools/baseline_diff.py
              cw.sh baseline-diff-facade OLD.json NEW.json [--json out.json] [--md out.md]
  mcp-server  rocqwash MCP stdio server (JSON-RPC 2.0 over stdio; capability true names follow docs/CAPABILITY-INDEX.md) -> tools/mcp_server.py
              cw.sh mcp-server   (stdio transport; drive from an MCP client, not interactively)
  periscope   six-source peripheral-intelligence sweep (sentinel companion window log + judgment draft skeleton; read-only GET) -> tools/periscope.py
              cw.sh periscope --config F [--out DIR] [--rounds N] [--dry-run]
  ai-flavor   AI-wording word-face detection body (36-face battery + separate em-dash battery; hits are data, not errors; word map read-only) -> tools/ai_flavor.py
              cw.sh ai-flavor --file <p> [--json out] | --tree DIR | --selftest
  ai-flavor-apply AI-wording advisory apply face (writes only through the rewrite provider; handoff leg default zero-network; http leg default-deny; zh ban faces never machine-written) -> tools/ai_flavor_apply.py
              cw.sh ai-flavor-apply --file <p> [--json out] [--emit-handoff out.jsonl | --apply-handoff in.jsonl --state p] [--provider handoff|http]
  auto-round  round-ledger admission/rollback/salvage body (auto/gated gear per autonomy.json; append-only ledger; rollback = drift archive then one revert; no reset no force no push) -> tools/auto_round.py
              cw.sh auto-round <command> [--repo-root P] [--autonomy P] [--state P] [--ledger P] [--continue] [--selftest]
  i18n-pipeline zh-en four-linkage i18n pipeline orchestration (P0 policy pre-check / P1 segmenter / P3 four-linkage apply / P6 ledger closure; refusal is a legal exit-0 ledgered outcome) -> tools/i18n_pipeline.py
              cw.sh i18n-pipeline --manifest run.json --stage p0|p1|p3|p6 [--json out] [--selftest]
  i18n-translate model-site layer P2 of the i18n pipeline (handoff emit/ingest default zero-network; http leg optional default-deny; NETRED ledger line per call) -> tools/i18n_translate.py
              cw.sh i18n-translate --segments <p> --emit out.jsonl [--prompts DIR] | --ingest in.jsonl [--provider handoff|http]
  i18n-verify P4 mechanical verify orchestration + P5 human ten-point form face (the engine emits the form and ingests verdicts, never judges) -> tools/i18n_verify.py
              cw.sh i18n-verify --verify-target <p> [--json out] | --emit-tenpoint <target> | --ingest-tenpoint verdicts.json | --selftest
  jargon-apply jargon-to-standard apply face over the 62-entry map (replace entries only; human rows never machine-written; plan zero-write default; apply rescans to residue zero; idempotent) -> tools/jargon_apply.py
              cw.sh jargon-apply --file <p> | --tree DIR [--plan | --apply] [--json out] [--guarded-interactive] [--selftest]
  termbase    read-only terminology thin layer over seeds/termbase/termbase.json (exact-face lookup; schema validation fail-loud; a miss is data, exit 0) -> tools/termbase.py
              cw.sh termbase --lookup <term> [--db <p>] [--json out] | --schema-check | --selftest
  gap-cluster aggregate TODO-SEAT and gap ledger entries into a family-shape-keyed gap ledger (deterministic; byte-identical reruns; zero gaps is data) -> tools/gap_cluster.py
              cw.sh gap-cluster [--ledger P]... [--reports P]... [--out FILE] [--json] | --selftest
  row-render  gap ledger to candidate taxonomy rows through the E4 P2 handoff form (vacgen admission gate; ten-point human gate; a draft is written only on full admission) -> tools/row_render.py
              cw.sh row-render --gaps P --emit OUT.jsonl | --ingest ROWS.jsonl | --check-draft DRAFT.json | --emit-tenpoint | --ingest-tenpoint V.json [--draft-out P] [--vacgen P] [--json]
  calibration-ledger  pair vacgen v2 predicted confidence with the measured compile-leg rc into per-row calibration entries (correlationId; idempotent seen set; row-rot signal face; signals are data) -> tools/calibration_ledger.py
              cw.sh calibration-ledger --report R.json --rc-file RC.json [--leg-map LM.json] [--default-leg NAME] [--ledger P] [--signal-threshold F] [--strict] [--dry-run] | --selftest
  lean-sweep  vacuity probe batch sweep orchestrator (bins, dedups, casts with a zero-compile precheck; the compile leg is a designed SKIP unless --fire and the toolchain probe passes) -> tools/lean_sweep.py
              cw.sh lean-sweep --batches B.json --out DIR [--json F] [--fire] [--lanes N] [--skip-ledgers F]... [--taxonomy FILE] [--bisect-max N] | --selftest
  verdict-diff mechanical judge for sweep ledgers (GREEN/ALERT/BLOCKED/MISSING/SKIPPED-TIERT plus an exception list; ALERT exits 2 stop-work; baseline convergence caliber) -> tools/verdict_diff.py
              cw.sh verdict-diff --results-lane "DIR/results-lane*.tsv" [--expected F | --batches F] [--json F] [--md F] [--baseline OLD.json] | --selftest
  symbiosis-bus  cross-repository experience bus over docs/exp-ledger.jsonl (swap schema rocqwash-symbio/1; import walks the exp_port append face one call per entry; export/status/diff read-only; zero network by design) -> tools/symbiosis_bus.py
              cw.sh symbiosis-bus export --out SWAP.jsonl [--ledger P] [--source-repo NAME] [--anchor HEX] [--dry-run] | import --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | diff --a A --b B
  uplink      external return-package intake gate (verify / intake / pr-prep; md5 mismatch and missing declared members are fail-loud; the intake register row and the caller-named draft are the only writes; zero network by design) -> tools/uplink.py
              cw.sh uplink verify --package P.zip [--digest HEX|SIDECAR] [--manifest M.md5] | intake --package P.zip --source-agent SEAT --landed-ref REF [--digest HEX|SIDECAR] [--manifest M.md5] [--register F] [--dry-run] | pr-prep --package NAME --out DRAFT.md [--register F] [--signature LINE]
  evolution-dashboard  self-evolution dashboard over the three standing accounts (experience ledger + round ledger + vacgen v2 TODO-SEAT reports -> coverageLowerPct curve + rounds conversion + per-run gap thermometer; JSON + markdown faces; absent standing paths are data) -> tools/evolution_dashboard.py
              cw.sh evolution-dashboard [--repo ROOT] [--exp-ledger P] [--rounds P] [--reports P]... [--json-out P] [--md-out P] [--stdout markdown|json] [--selftest]
  bus-feeder  gap-ledger feeder for symbiosis swap packages (rocqwash-symbio/1 in, TODO-SEAT gap rows out; family-shape keyed, idempotent on id and fingerprint; the gap feed ledger is the only write face; zero network by design) -> tools/bus_feeder.py
              cw.sh bus-feeder feed --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | --selftest
  axiom-guard repo-wide axiom guard (every .v compiled and tri-classified: compile-ok / compile-broken debt register / skip-no-toolchain; two-level detection on compile-ok files: per-theorem Print Assumptions census plus the authoritative coqchk -o kernel recheck; Closed zero axioms, empty default whitelist; env-gated, rc 111 honest skip; zero repository writes) -> tools/axiom_guard.py
              cw.sh axiom-guard --repo DIR [--out DIR] [--rocq BIN] [--coqchk BIN] [--allow-axiom NAME]... [--timeout SEC] [--keep]
  axiom-audit Coq-side axiom audit (fixture-corpus census per coqc engine; declared axioms with file/line/form, reverse map to introducing files, platform grades classical/funext/stdlib; live engine required, unconfigured skips honestly) -> tools/axiom_audit.py
              cw.sh axiom-audit census --repo DIR [--json OUT] | --selftest
  vacgen-coq Coq-side statement ingestion and probe-cast planner (Rocq vernacular extraction, premise/conclusion split, data-driven taxonomy rows, Coq-L3 coverage metric; ticket 14 wave 1; zero network zero compile) -> tools/vacgen_coq.py
              cw.sh vacgen-coq --from-v FILE|DIR [--taxonomy FILE] [--out DIR] [--limit N] | --selftest
  source-fetch audit fetch face (dual-source cross-pin, sha256 pin from caller or CI-source file, HTML-trap sniff, NETRED backoff; honest-unverified and net-gated states are data) -> tools/source_fetch.py
  cw.sh source-fetch --url URL [--sha256 HEX] [--sha256-source URL] [--mirror URL] [--trap-sniff] [--out DIR] [--timeout SEC] [--retries N] | --selftest
  sweep-verdict batch sweep judge (per-lane result ledgers union-deduped into a GREEN/EXCEPTION/MISSING verdict table; expected-red interlock with baselinediff semantics; shared-append ledgers are the anti-pattern it exists to prevent) -> tools/sweep_verdict.py
  cw.sh sweep-verdict --lanes DIR [--expected-red FILE] [--out FILE] | --selftest
  release-chain release chain planner (issue body -> GitHub Release per-asset -> Zenodo deposit, three gated layers; dry-run by default, publish needs --confirm-publish; URLs and DOIs are taken verbatim from service responses) -> tools/release_chain.py
  cw.sh release-chain --issue N --release-title T --assets DIR [--zenodo-meta FILE] [--repo OWNER/NAME] [--stage 1|2|3|4] [--dry-run] [--confirm-publish] | --selftest
  claim-watch conclusion-level claim watch (the eight RH signals + three NS/Euler triggers from the seed config; machine-readable status endpoints; heartbeat silent-death and unverifiable registration; append-only actor-namespaced round ledger; live face) -> tools/claim_watch.py
  cw.sh claim-watch --config FILE [--round-label L] [--ledger FILE] [--actor A] | --offline-selftest
  axiom-sweep per-theorem Lean axiom-closure classifier (#print axioms via the target's own lake env; CLEAN / BENIGN-STANDARD trio / SORRY-ALARM / CUSTOM-AXIOM-ALARM / PRIVATE-COVERED / UNPARSED; closure snapshot plus baseline diff_alarm) -> tools/lean_axiom_sweep.py
  cw.sh axiom-sweep --root FILE|DIR [--json OUT] [--snapshot OUT] [--baseline SNAP] [--allow-axiom NAME]... | --selftest
  numeric-probe numerical claim verifier (stdlib exact arithmetic executes rational-bound and interval-containment claims; transcendental plans stay honestly PLANNED) -> tools/numeric_probe.py
  cw.sh numeric-probe --claim FILE [--out FILE] | --selftest
  statement-identity two-face statement identity prober (claimed vs proven normalization, three-seam classification, uncast-region matrix) -> tools/statement_identity.py
  cw.sh statement-identity --claimed FILE --proven FILE [--out FILE] | --selftest
  capability-index capability index reader (full and summary modes plus single-tool query over the census masters; summary exists because the full index overran harness response caps) -> tools/capability_index.py
  cw.sh capability-index [--mode full|summary] [--tool NAME] | --selftest
  flaky-guard flaky quarantine guard, repair class E2-3 (detect classifies each red case by an isolation probe: suite-red + alone-green = order-dependent, red in both contexts = content red that stays visible; --move quarantines into tests/advisory_roster.txt so the default suite drops it with a loud ADVISORY-OUT and the CI flaky-watch lane keeps observing it; scope-checked against tools/repair_scope.py, budget-capped at 2 per class per branch, ledgered in docs/repair-ledger.jsonl; dry-run by default; --restore needs green-round evidence) -> tools/flaky_guard.py
              cw.sh flaky-guard --detect --log LOG [--json OUT] [--no-probe] | --probe CASE | --move CASE [--apply] | --restore CASE [--apply] [--green-rounds N] | --status | --selftest
  repair-scope shared repair-scope exclusion table for the E2 guard family (frozen LEDGER8/CHECKERS rows read at runtime from certify/frozen8.py, the append-only ledger document, the frozen directory families; per-class writable faces + budget registry; the single source every repair guard imports) -> tools/repair_scope.py
              cw.sh repair-scope --check PATH... | --classes | --selftest
  roster-resync  roster count drift guard, repair class E2-2 (the run_tests.sh CASES roster is the only count authority; the doc_lint count lines of tests/README.md + README.md are re-derived one-way from it and the drifted digits are synced in place; the roster file is never written; scope-checked against tools/repair_scope.py, budget-capped at 2 per class per branch, every repaired line ledgered in docs/repair-ledger.jsonl; dry-run by default) -> tools/roster_resync.py
                 cw.sh roster-resync [--repo DIR] [--apply] [--ledger P] [--json OUT] | --selftest
  scheduler-lite  TODO-SEAT threshold trigger planner for the jargon tier-B auto gear (gap feed ledger + vacgen reports through tools/gap_cluster.py plus the round cadence of docs/round-ledger.jsonl; verdict quiet | due | blocked; ignition gated on the EF all-green marker; dry-run by design: zero apply, zero commit, zero network) -> tools/scheduler_lite.py
                 cw.sh scheduler-lite [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--out F] [--json] | --selftest
  auto-merge  X5 auto-merge gate judge plus safety rail (six-verdict mergeability enum merge-ok / hold-red / hold-conflict / already-landed / superseded-landed-elsewhere / escalate-unknown over caller-gathered facts; the five-sample calibration set S-1..S-5 pinned; rail = supply/* head-branch whitelist + daily budget cap 3 + append-only merge ledger + the post-merge red revert arc; zero network, dry run by default) -> tools/auto_merge.py
              cw.sh auto-merge --facts F [--head-branch BR] [--allow-prefix P] [--daily-cap N] [--ledger P] [--merge-sha SHA] [--post-merge {green,transient,content,unrecognized}] [--apply] [--json OUT] | --selftest
  jargon-map-sync  jargon map sync, md table to seed JSON (the detector map curated superset absorbed into the apply map; single-form admission: parenthetical annotations stripped, em-dash cells land as rewrite_or_delete, slash alternations and the six note-guard markers rejected; existing entries preserved with their id/exempts/cross_track_note; exact count label; plan zero-write default, --apply writes the map) -> tools/jargon_map_sync.py
              cw.sh jargon-map-sync [--md P] [--map P] [--json P] | --apply | --selftest

  repair-weekly  repair-outcome ledger weekly distribution face, repair class E6 (aggregates docs/repair-ledger.jsonl into the ISO-week per-red outcome census plus the class/ticket distributions; read-only over the ledger, --out/--json are the only write faces; --record appends one per-red rocqwash-repair-ledger/2 row under the enforced vocabulary, --apply required) -> tools/repair_weekly.py
              cw.sh repair-weekly [--ledger P] [--date YYYY-MM-DD] [--out FILE] [--json P] | --record --class CLASS --target T --repair-outcome VALUE [--ticket K] [--evidence-file J] [--reason S] [--apply] | --selftest
  selfevolve-round  one deterministic mechanical round, cron face (census jargon_apply --plan, then apply, then verify py_compile/bash -n hard gates plus norm_lint/doc_lint advisory, then auto_round commit, then push, then route the CI judge; frozen faces excluded by jargon_apply; zero qualifying fixes = clean no-op pass; apply residue nonzero = fail-loud, no commit) -> tools/selfevolve_round.py
              cw.sh selfevolve-round [--dry-run]
  pin-repair  provenance-pin drift repair for the jargon seed map, triage row R15 auto-repair executor (re-signs drifted provenance.sources md5 pins behind the sync tool's zero-write plan IN-SYNC verdict; --plan writes nothing, --apply touches only md5 values and re-runs the seeds suite, red verify rolls back to the pre-apply bytes; not-IN-SYNC exits without touching the seed) -> tools/pin_repair.py
              cw.sh pin-repair --selftest | --plan | --apply [--seed P]
  learning-feedback  scheduling feedback face over the three standing ledgers (round ledger, round state, experience ledger read-only; casts schema rocqwash.scheduling-feedback/1 into docs/scheduling-feedback.json: the auto versus human-approved round split, the approval rate, the per-class breakdown, and the four-state repair outcome tally; missing or corrupt inputs land in the errors field, never guessed) -> tools/learning_feedback.py
              cw.sh learning-feedback [--selftest]
  b-gate  B-level generalization threshold audit over the round records (3 instances, each grounded in at least 1 executed round; per-class instance and round counts, a per-class readiness verdict, and an explicit gap list into docs/b-gate-audit.json, schema rocqwash.b-gate-audit/1; counts are measured from the records, never inflated) -> tools/b_gate_audit.py
              cw.sh b-gate [--selftest]
  tree-audit  read-only tree health audit over .lean/.v source trees (one JSON-line census: totals, declarations, the unsound-feature sweep, comment faces, per-directory and largest-file tables, import roots; byte-literal counting calibrated to the census oracle; zero subprocess, zero network, zero tree writes) -> tools/tree_audit.py
              cw.sh tree-audit --root DIR [--json OUT] | --selftest
  pipeline-lite  gap-to-admission pipeline executor, D2-2 data layer (scheduler_lite plan verdict imported, never re-derived; gap_cluster clusters transformed to row_render gap rows with the layer-law policyPrecheckRef stamped; emit packet then ingest a backfill into a draft whose rows enter at tenpointVerdict PENDING; quiet and blocked write nothing; pending-backfill and pending-human stops are data; code-layer faces (ten-point verdicts, taxonomy row integration, apply pass, auto_round commit and approve) stay human-gated and are never composed; b-gate audit counter carried read-only; zero network) -> tools/pipeline_lite.py
              cw.sh pipeline-lite [--plan F] [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--gap-out F] [--render-gaps F] [--packet-out F] [--backfill F] [--draft-out F] [--b-gate-audit P] [--policy-ref S] [--stop-at {data,human}] [--json] | --selftest
  anchor-guard  anchor and certificate guard for one module directory (manifest validation V1-V10, module compile tri-classification in a private temp workdir, coqchk -o kernel recheck baseline, per-anchor probe face over vm_compute checks plus Print Assumptions, mutation kill matrix over the manifest's copied defect rows: a certificate that kills zero mutants is VACUOUS and red, a non-hold baseline is an unanchored anchor, module compile-broken is red; manifest copies its mutant rows from tools/mutants-v1.json, the guard never loads the library; env-gated, rc 111 honest skip; zero repository writes) -> tools/anchor_guard.py
              cw.sh anchor-guard --repo DIR --manifest FILE [--out DIR] [--rocq BIN] [--coqchk BIN] [--timeout SEC] [--keep] | --selftest

  help        this help (help <tool> = the tool's one-line usage hint)

Exit codes: 0=pass  2=unknown-tool  9=target-script-missing  others = each tool's own convention, passed through
Routing notes:
  - Arguments and exit codes pass through 1:1 (direct exec; fail-loud, never rewritten); same contract as cli/rocqwash.
  - All paths resolve relative to the repository root (ROOT is derived from this script's own directory) — the repo can be relocated freely; zero hardcoded absolute paths.
  - `cw.sh <tool>` with no args prints the tool's one-line hint to stderr, then passes through; `cw.sh help <tool>` prints the hint only.
EOF
}

# One-line usage hints (shared verbatim by `help <tool>` and the pre-passthrough no-args hint)
hint_for() {  # $1=tool
  case "$1" in
    scan4)       echo "cw.sh scan4 --file <f.v> [--json out.json] [--ids S] [--text]   # token-level qualified-identifier census -> scan/scan_v4_token.py" ;;
    cure)        echo "cw.sh cure --file <f.v> [--pack P] [--only IDS] [--json out] [--apply]   # consumer-cure canonical pack (dry-run by default) -> wash/cure_applier.py" ;;
    probe)       echo "cw.sh probe --candidates <tsv> --src DIR --world DIR --out ledger.json [--fresh]   # batch closure-compatibility probe -> wash/probe_engine.py" ;;
    chain)       echo "cw.sh chain <ledger.json...> [--json out] [--md out] [--top N]   # multi-ledger merge chain-root graph -> tools/chain_graph.py" ;;
    sync-ledger) echo "cw.sh sync-ledger --probe <json> --ledger <tsv> --out <tsv> [--report r.json]   # probe-ledger x status-ledger merge -> tools/ledger_sync.py" ;;
    erasure)     echo "cw.sh erasure --mli <f.mli> [--json scan.json] [--resolve N1,N2] [--md-out f.md]   # extraction erasure-position classification advisor -> verify/erasure_classifier.py" ;;
    dual-scan)   echo "cw.sh dual-scan --dir DIR | --file <f.v> [--out report.json]   # dual-scanner cross-check -> scan/dual_scan.py" ;;
    doctor)      echo "cw.sh doctor [--worker PATH] [--donor DIR] [--json out.json] [--smoke --coqc PATH]   # dyld toolchain-breakage diagnostics (diagnose only + restore advice; never executes) -> tools/toolchain_dyld_doctor.py" ;;
    net-probe)   echo "cw.sh net-probe [--endpoints URL,..] [--rounds N] [--interval S] [--stable-window] [--json out]   # network-window probe (double-probe stable window) -> tools/net_probe.py" ;;
    triage)      echo "cw.sh triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]   # CI red-run triage (five families + green-run) -> tools/ci_triage.py" ;;
    union)       echo "cw.sh union --base B --main M --branch X --kind order [--out o --apply] | --git REPO --ref-base RB --ref-main RM --ref-branch XB   # registry union surgery (dry-run by default) -> tools/registry_union.py" ;;
    pushci)      echo "cw.sh pushci --repo-path DIR --branch B [--pre-scan-gate4] [--merge] [--max-heal N] [--json out] [--dry-run]   # push-CI one-shot pipeline (emission gate -> push -> watch -> heal -> verdict +- merge; seven-state verdict success/fix-content/toolchain/unstable/heal-exhausted/gate4-block/dry-run) -> tools/pushci.py" ;;
    sentinel)    echo "cw.sh sentinel --once | --loop [--interval S] [--watch-repo ORG/REPO [--branch B]...] [--watch-ledgers DIR] [--watch-buildlog FILE] [--state-file F] [--emit F] [--on-red 'CMD'] [--on-red-preset NAME]... [--on-red-arg K=V] [--injector F] [--json out]   # real-time watch sentinel (three signal sources CI runs / ledger chain-roots / buildlog tokens -> JSONL event stream; red is data not tool failure; no action by default; --on-red-preset five presets unclog/pushci/wash-shape/triage/cw-doctor, repeatable = chained in the given order, one failure continues the chain; mutually exclusive with --on-red; side-effect actions require --emit, both channels share the same guard) -> tools/cw_sentinel.py" ;;
    wash-shape)  echo "cw.sh wash-shape --file A.v [--file B.v...] | --dir TREE [--only KINDS] [--apply] [--header-map M] [--header-map-preset NAME] [--anchor-src DIR] [--json OUT] [--loop --interval S --events F] [--injector SCEN.json]   # canonical five-pass shaping pipeline (lexical/token/header/EOL/anchor; plan writes nothing by default; --apply applies, then re-runs the five passes for verification; --header-map-preset named header-template library tests/fixtures/header_map_v1.json, mutually exclusive with --header-map in the same slot) -> tools/wash_shape.py" ;;
    unclog)      echo "cw.sh unclog --src DIR --world DIR [--candidates TSV | --chain-ledgers JSON...] [--apply] [--audit] [--probe-parallel K] [--rounds N] [--top N] [--pack FILE] [--json out] [--events F] [--loop --interval S --loop-max N] [--injector DIR]   # blockage-unclogging closed loop (probe collection -> chain_graph chain-root pick -> cure_applier application -> re-scan/re-probe verification -> verdict unclogged/wall/rounds-exhausted/audit; dry-run by default; frozen-listed files refused loudly; --audit read-only clog baseline, zero writes, mutually exclusive with --apply/--loop; --probe-parallel K threads probe parallelism, jobs dimension recorded in the timing section) -> tools/unclog.py" ;;
    cw-doctor)   echo "cw.sh cw-doctor [--json out.json] [--workdir DIR] [--registry PATH] [--src DIR --sample N [--world DIR]] [--worker PATH] [--donor DIR] [--endpoints URL,..] [--guard PATH] [--timeout S] [--injector DIR]   # aggregate health check, four domains (dyld environment / net_probe network / registry anchor audit / clog probe + chain_graph -> aggregate health score 0-100 + verdict healthy/degraded + advice; diagnosis only, never executes; --injector offline-testable) -> tools/cw_doctor.py" ;;
    doc-lint)    echo "cw.sh doc-lint [--repo DIR] [--json OUT] [--help-cap N]   # docs-to-implementation consistency linter, three checks (1. cw.sh four-place tool-table cross-check + tools/ generic-entry reconciliation 2. CASES vs tests/README.md vs README.md counts 3. doc flag references vs each tool's real --help output; verdict consistent|drift; red is data not tool failure) -> tools/doc_lint.py" ;;
    netname-normalize) echo "cw.sh netname-normalize [--dir DIR] [--apply] [--map out.tsv] [--json out]   # .v.v double-suffix clean-name normalizer (mapping table + --apply rename with md5 verification) -> tools/netname_normalize.py" ;;
    select-audit) echo "cw.sh select-audit [--order ORDER] [--select LIST] [--grep RX] [--requires F.v] [--json out]   # batch-selection auditor (selection list vs tree order.txt full-table grep dedup + Require-surface audit v6 criteria) -> tools/select_audit.py" ;;
    render-events) echo "cw.sh render-events --events F.jsonl [--dir DIR] [--md out.md] [--json out] [--top N]   # sentinel-event JSONL to markdown ledger (kind/family/action three-dimension distribution + per-event table; malformed-line tolerant rc1; red is data not tool failure) -> tools/render_events.py" ;;
    baseline-diff) echo "cw.sh baseline-diff OLD.json NEW.json [--json out.json] [--md out.md]   # clog-baseline differ (two unclog --audit clog baselines, argv order old then new -> new_blocks/resolved_blocks/persistent three lists + score_delta; verdict improved/degraded/stable/incomparable; self-consistency precheck rejects hand-edited ledgers; timing excluded; red is data not tool failure) -> tools/baseline_diff.py" ;;
    dispatch)    echo "cw.sh dispatch --event-file <json> [--preset report-only|suggest|auto] [--json OUT] [--state-file F] [--cooldown S] [--repo-path DIR] [--param K=V] [--dry-run]   # red-event router (sentinel red events -> action presets; three presets: report-only default zero execution / suggest copy-paste command block / auto explicit only under a 60s cap, rc!=0 recorded without touching the exit code; dedup state + cooldown; all routes wired onto existing cw.sh routes, zero new engines; family-A content-red never auto-fixed, emits a fix list; red is data not tool failure) -> tools/red_dispatch.py" ;;
    audit)       echo "cw.sh audit --order ORDER --project _CoqProject | --git REPO --ref REF [--live-src DIR] [--anchor-src DIR] [--fix-plan] [--json out] [--md out]   # registry hygiene auditor (order.txt/_CoqProject dual-book read-only four-account output: duplicates / anchor collisions / seq-form / malformed / missing anchors / orphans / live topology + --fix-plan deterministic prescription, zero writes; --apply does not exist; keys and anchor canon reused from registry_union, zero re-invention; findings are data, exit 0) -> tools/registry_audit.py" ;;
    registry-fix) echo "cw.sh registry-fix --audit-json AUDIT.json --order ORDER.txt --project _CoqProject [--anchor-src DIR] [--json REPORT.json] [--apply] [--work-dir DIR]   # registry prescription applier (applies registry_audit --fix-plan prescriptions one by one; three prescription kinds DEDUP keep-first / anchor re-stamp / ORPHAN-ADD skip; dry-run by default; --apply writes, then three assertions hold or rollback; staging fully in-memory, zero writes; same-parameter discipline binds audit and applier verbatim) -> tools/registry_fix.py" ;;
    norm-lint)   echo "cw.sh norm-lint --tree DIR | --file PATH [--jargon-map P] [--cjk-threshold F] [--cjk-whitelist P] [--json P] [--md P]   # annotation-face normalization linter, report-only first form (prose faces of .py/.sh/.md: header banner + five-field block Purpose./Interface./Dependencies./Evidence./Exit-codes. verbatim; jargon mapping-table faces word-boundary; CJK residue warn; forbidden classes warn; header budget 30; findings are data, the exit code never escalates on them; *.zh.md and docs/zh/ archives skipped; default jargon map docs/jargon-to-standard-mapping-v1.md) -> tools/norm_lint.py" ;;
    registry-regen) echo "cw.sh registry-regen --base-repo REPO --base-ref REF --contrib-repo REPO --contrib-ref REF --pieces M1,M2,... --anchor-src DIR [--dep-source require|coqdep|registry|auto] [--seq N] [--out DIR] [--apply] [--json P]   # contribution registration-row regenerator (merge-target books verbatim as the draft bottom + canonical #R<seq>-<md5-8> rows for the named pieces tail-appended in dependency order, ties by the contribution registry's existing row order; BLOCK pieces listed with reasons and no rows; entity md5 cross-checked against the contribution-surface blob; three same-source assertions reused from registry_union; dry-run by default, --apply writes DIR/order.txt and DIR/_CoqProject) -> tools/registry_regen.py" ;;
    contrib-intake) echo "cw.sh contrib-intake --contrib-repo PATH --contrib-ref REF --base-repo PATH [--base-ref REF] [--paths P1,P2] [--order-path PATH] [--project-path PATH] [--lane-prefix PREFIX] [--jargon-map PATH] [--rocq-cmd CMD] [--json P]   # contribution intake inspector (read-only four-gate verdicts over a contribution face vs a base face, protocol four-check pipeline in one run: registry union dry run against the base face with a regeneration prescription on any assertion blast / norm lint of each new or changed prose face via norm_lint / gate expectation over changed .v faces with a gate7 probe precheck / lane isolation tally of changed paths outside --lane-prefix; gates never short-circuit, BLOCK verdicts are data and the exit code stays 0; zero writes into either face) -> tools/contrib_intake.py" ;;
    evolve)      echo "cw.sh evolve --draft-out PATH [--json P] [--top N] [--baseline P] [--watch-repo ORG/REPO]... [--sentinel-state F] [--suite-ledger F | --suite-now] [--registry-git REPO --registry-ref REF] [--selftest]   # autonomous evolution engine v1 (harvest five signal classes by subprocess of the existing engines: norm-lint fitness with frozen surfaces excluded / sentinel --once dual-repo new ci-red events / suite last state / registry audit accounts with increment / maintained UNRECOGNIZED sentinel events; derive fixed-rule scored candidates plus genetic standing candidates from the ledger lineage; draft the constitution three-law-preamble task brief to --draft-out; draft-only spawn gate: never executes a candidate, never writes the repository; adverse signals are data, exit 0; 2 usage; 9 missing/unreachable) -> tools/evolve.py" ;;
    vacgen)      echo "cw.sh vacgen --in F [--out DIR] [--toolchain T] [--snapshot S] [--preflight-all] [--taxonomy P] [--force]   # Lean vacuity probe skeleton generator (four-account casting, zero compile) -> tools/vacgen.py" ;;
    ci-triage)   echo "cw.sh ci-triage --repo ORG/REPO --run ID [--logs] | --offline JOBS.json [--json out]   # CI red-run triage, alias of triage -> tools/ci_triage.py" ;;
    exp-append)  echo "cw.sh exp-append --tool T --points P [--evidence E] [--batch B] [--id ID]   # experience-ledger appender (schema rocqwash-exp/1, idempotent seen set; the MCP exp_append face) -> tools/exp_port.py" ;;
    baseline-diff-facade) echo "cw.sh baseline-diff-facade OLD.json NEW.json [--json out.json] [--md out.md]   # clog-baseline differ, alias of baseline-diff -> tools/baseline_diff.py" ;;
    mcp-server)  echo "cw.sh mcp-server   # rocqwash MCP stdio server (JSON-RPC 2.0 over stdio) -> tools/mcp_server.py" ;;
    periscope)   echo "cw.sh periscope --config F [--out DIR] [--rounds N] [--dry-run]   # six-source peripheral-intelligence sweep -> tools/periscope.py" ;;
    ai-flavor)   echo "cw.sh ai-flavor --file <p> [--json out] | --tree DIR | --selftest   # AI-wording word-face detection body (36-face battery + em-dash battery; hits are data, not errors) -> tools/ai_flavor.py" ;;
    ai-flavor-apply) echo "cw.sh ai-flavor-apply --file <p> [--json out] [--emit-handoff out.jsonl | --apply-handoff in.jsonl --state p] [--provider handoff|http]   # AI-wording advisory apply face (writes only through the rewrite provider; handoff default zero-network; http leg default-deny) -> tools/ai_flavor_apply.py" ;;
    auto-round)  echo "cw.sh auto-round <command> [--repo-root P] [--autonomy P] [--state P] [--ledger P] [--continue] [--selftest]   # round-ledger admission/rollback/salvage body (commands commit/approve/anchor/rollback/salvage/merge-salvage/status/list/log; append-only; no reset no force no push) -> tools/auto_round.py" ;;
    i18n-pipeline) echo "cw.sh i18n-pipeline --manifest run.json --stage p0|p1|p3|p6 [--json out] [--selftest]   # zh-en four-linkage i18n pipeline orchestration (P0 policy / P1 segmenter / P3 apply / P6 closure; refusal is a legal exit-0 ledgered outcome) -> tools/i18n_pipeline.py" ;;
    i18n-translate) echo "cw.sh i18n-translate --segments <p> --emit out.jsonl [--prompts DIR] | --ingest in.jsonl [--provider handoff|http]   # model-site layer P2 (handoff emit/ingest default zero-network; http leg default-deny; NETRED ledger line per call) -> tools/i18n_translate.py" ;;
    i18n-verify) echo "cw.sh i18n-verify --verify-target <p> [--json out] | --emit-tenpoint <target> | --ingest-tenpoint verdicts.json | --selftest   # P4 mechanical verify orchestration + P5 human ten-point form (the engine never judges) -> tools/i18n_verify.py" ;;
    jargon-apply) echo "cw.sh jargon-apply --file <p> | --tree DIR [--plan | --apply] [--json out] [--guarded-interactive] [--selftest]   # jargon-to-standard apply face (replace entries only; plan zero-write default; apply rescans to residue zero; idempotent) -> tools/jargon_apply.py" ;;
    termbase)    echo "cw.sh termbase --lookup <term> [--db <p>] [--json out] | --schema-check | --selftest   # read-only terminology thin layer (exact-face lookup; schema fail-loud; a miss is data) -> tools/termbase.py" ;;
    gap-cluster) echo "cw.sh gap-cluster [--ledger P]... [--reports P]... [--out FILE] [--json] | --selftest   # aggregate TODO-SEAT and gap ledger entries into a family-shape-keyed gap ledger (deterministic; byte-identical reruns; zero gaps is data) -> tools/gap_cluster.py" ;;
    row-render)  echo "cw.sh row-render --gaps P --emit OUT.jsonl | --ingest ROWS.jsonl | --check-draft DRAFT.json | --emit-tenpoint | --ingest-tenpoint V.json [--draft-out P] [--vacgen P] [--json]   # gap ledger to candidate taxonomy rows through the E4 P2 handoff form (vacgen admission gate; ten-point human gate; a draft is written only on full admission) -> tools/row_render.py" ;;
    calibration-ledger) echo "cw.sh calibration-ledger --report R.json --rc-file RC.json [--leg-map LM.json] [--default-leg NAME] [--ledger P] [--signal-threshold F] [--strict] [--dry-run] | --selftest   # pair vacgen v2 predicted confidence with the measured compile-leg rc into per-row calibration entries (correlationId; idempotent seen set; row-rot signal face; signals are data) -> tools/calibration_ledger.py" ;;
    lean-sweep)  echo "cw.sh lean-sweep --batches B.json --out DIR [--json F] [--fire] [--lanes N] [--skip-ledgers F]... [--taxonomy FILE] [--bisect-max N] | --selftest   # vacuity probe batch sweep orchestrator (bins, dedups, casts with a zero-compile precheck; the compile leg is a designed SKIP unless --fire and the toolchain probe passes) -> tools/lean_sweep.py" ;;
    verdict-diff) echo "cw.sh verdict-diff --results-lane DIR/results-lane*.tsv [--expected F | --batches F] [--json F] [--md F] [--baseline OLD.json] | --selftest   # mechanical judge for sweep ledgers (GREEN/ALERT/BLOCKED/MISSING/SKIPPED-TIERT plus an exception list; ALERT exits 2 stop-work; baseline convergence caliber) -> tools/verdict_diff.py" ;;
    symbiosis-bus) echo "cw.sh symbiosis-bus export --out SWAP.jsonl [--ledger P] [--source-repo NAME] [--anchor HEX] [--dry-run] | import --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | diff --a A --b B   # cross-repository experience bus over docs/exp-ledger.jsonl (swap schema rocqwash-symbio/1; import walks the exp_port append face one call per entry; duplicate ids skip idempotently; export/status/diff read-only; zero network by design) -> tools/symbiosis_bus.py" ;;
    uplink)      echo "cw.sh uplink verify --package P.zip [--digest HEX|SIDECAR] [--manifest M.md5] | intake --package P.zip --source-seat SEAT --landed-ref REF [--digest HEX|SIDECAR] [--manifest M.md5] [--register F] [--dry-run] | pr-prep --package NAME --out DRAFT.md [--register F] [--signature LINE]   # external return-package intake gate (verify / intake / pr-prep; md5 mismatch and missing declared members are fail-loud; the intake register row and the caller-named draft are the only writes; zero network by design) -> tools/uplink.py" ;;
    evolution-dashboard) echo "cw.sh evolution-dashboard [--repo ROOT] [--exp-ledger P] [--rounds P] [--reports P]... [--json-out P] [--md-out P] [--stdout markdown|json] [--selftest]   # self-evolution dashboard over the three standing accounts (experience ledger rocqwash-exp/1 + round ledger rocqwash-round/1 + vacgen v2 TODO-SEAT report faces -> coverageLowerPct curve with per-run TODO-SEAT delta and rise flag, rounds conversion greenPct/classConversionPct, per-run gap count thermometer; absent default-path inputs are data with present=false, explicitly flagged absent paths exit 9; writes only caller-named --json-out/--md-out files; zero network) -> tools/evolution_dashboard.py" ;;
    bus-feeder)  echo "cw.sh bus-feeder feed --swap SWAP.jsonl [--ledger P] [--dry-run] | status [--ledger P] [--swap F] | --selftest   # gap-ledger feeder for symbiosis swap packages (rocqwash-symbio/1 in, TODO-SEAT gap rows out; family-shape keyed, idempotent on id and fingerprint; the gap feed ledger is the only write face; zero network by design) -> tools/bus_feeder.py" ;;
    axiom-guard) echo "cw.sh axiom-guard --repo DIR [--out DIR] [--rocq BIN] [--coqchk BIN] [--allow-axiom NAME]... [--timeout SEC] [--keep]   # repo-wide axiom guard (every .v compiled and tri-classified: compile-ok / compile-broken debt register / skip-no-toolchain; two-level detection on compile-ok files: per-theorem Print Assumptions census plus the authoritative coqchk -o kernel recheck; Closed zero axioms, empty default whitelist; write faces: the caller-named --out report and the private temp workdir only; rc 0=PASS 1=red 2=usage 9=fail-loud missing binary 111=honest skip unconfigured toolchain; ROCWASH_ROCQ/ROCWASH_COQCHK env gating; zero repository writes) -> tools/axiom_guard.py" ;;
    source-fetch) echo "cw.sh source-fetch --url URL [--sha256 HEX] [--sha256-source URL] [--mirror URL] [--trap-sniff] [--out DIR] [--timeout SEC] [--retries N] | --selftest   # audit fetch face (dual-source cross-pin, sha256 pin from caller or CI-source file, HTML-trap sniff, NETRED backoff; honest-unverified and net-gated states are data) -> tools/source_fetch.py" ;;
    sweep-verdict) echo "cw.sh sweep-verdict --lanes DIR [--expected-red FILE] [--out FILE] | --selftest   # batch sweep judge (per-lane result ledgers union-deduped into a GREEN/EXCEPTION/MISSING verdict table; expected-red interlock with baselinediff semantics) -> tools/sweep_verdict.py" ;;
    release-chain) echo "cw.sh release-chain --issue N --release-title T --assets DIR [--zenodo-meta FILE] [--repo OWNER/NAME] [--stage 1|2|3|4] [--dry-run] [--confirm-publish] | --selftest   # release chain planner (issue body -> GitHub Release per-asset -> Zenodo deposit, three gated layers; dry-run by default, publish needs --confirm-publish; URLs and DOIs are taken verbatim from service responses) -> tools/release_chain.py" ;;
    claim-watch) echo "cw.sh claim-watch --config FILE [--round-label L] [--ledger FILE] [--actor A] | --offline-selftest   # conclusion-level claim watch (the eight RH signals + three NS/Euler triggers from the seed config; machine-readable status endpoints; heartbeat silent-death and unverifiable registration; append-only actor-namespaced round ledger; live face) -> tools/claim_watch.py" ;;
    axiom-sweep) echo "cw.sh axiom-sweep --root FILE|DIR [--json OUT] [--snapshot OUT] [--baseline SNAP] [--allow-axiom NAME]... | --selftest   # per-theorem Lean axiom-closure classifier (#print axioms via the target's own lake env; CLEAN / BENIGN-STANDARD trio / SORRY-ALARM / CUSTOM-AXIOM-ALARM / PRIVATE-COVERED / UNPARSED; closure snapshot plus baseline diff_alarm) -> tools/lean_axiom_sweep.py" ;;
    numeric-probe) echo "cw.sh numeric-probe --claim FILE [--out FILE] | --selftest   # numerical claim verifier (stdlib exact arithmetic executes rational-bound and interval-containment claims; transcendental plans stay honestly PLANNED) -> tools/numeric_probe.py" ;;
    statement-identity) echo "cw.sh statement-identity --claimed FILE --proven FILE [--out FILE] | --selftest   # two-face statement identity prober (claimed vs proven normalization, three-seam classification, uncast-region matrix) -> tools/statement_identity.py" ;;
    capability-index) echo "cw.sh capability-index [--mode full|summary] [--tool NAME] | --selftest   # capability index reader (full and summary modes plus single-tool query over the census masters; summary exists because the full index overran harness response caps) -> tools/capability_index.py" ;;
    axiom-audit) echo "cw.sh axiom-audit census --repo DIR [--json OUT] | --selftest   # Coq-side axiom audit (fixture-corpus census per coqc engine; declared axioms with file/line/form, reverse map, platform grades; live engine required) -> tools/axiom_audit.py" ;;
    vacgen-coq) echo "cw.sh vacgen-coq --from-v FILE|DIR [--taxonomy FILE] [--out DIR] [--limit N] | --selftest   # Coq-side statement ingestion and probe-cast planner (Rocq vernacular extraction, premise/conclusion split, data-driven taxonomy rows, Coq-L3 coverage; zero network zero compile) -> tools/vacgen_coq.py" ;;
    flaky-guard) echo "cw.sh flaky-guard --detect --log LOG [--json OUT] [--no-probe] | --probe CASE | --move CASE [--apply] | --restore CASE [--apply] [--green-rounds N] | --status | --selftest   # flaky quarantine guard, repair class E2-3 (isolation probe verdicts order-dependent vs content-red; --move quarantines into tests/advisory_roster.txt, the default suite drops it with ADVISORY-OUT and the CI flaky-watch lane keeps observing it; scope-checked against tools/repair_scope.py, budget 2 per class per branch, ledgered in docs/repair-ledger.jsonl; dry-run by default; --restore needs green-round evidence; findings and refusals are data, rc 0/1/2/9) -> tools/flaky_guard.py" ;;
    repair-scope) echo "cw.sh repair-scope --check PATH... | --classes | --selftest   # shared repair-scope exclusion table for the E2 guard family (runtime LEDGER8/CHECKERS read from certify/frozen8.py + the append-only ledger document + the frozen directory families; per-class writable faces and budget registry; --check exits 1 when any path is excluded, a refusal verdict is data) -> tools/repair_scope.py" ;;
    roster-resync) echo "cw.sh roster-resync [--repo DIR] [--apply] [--ledger P] [--json OUT] | --selftest   # roster count drift guard, repair class E2-2 (one-way recount from the run_tests.sh CASES roster into the doc_lint count lines of tests/README.md + README.md; the roster file is never written; scope-checked against tools/repair_scope.py, budget 2 per class per branch, ledgered in docs/repair-ledger.jsonl; dry-run by default) -> tools/roster_resync.py" ;;
    scheduler-lite) echo "cw.sh scheduler-lite [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--out F] [--json] | --selftest   # TODO-SEAT threshold trigger planner for the jargon tier-B auto gear (verdict quiet | due | blocked; ignition gated on the EF all-green marker; dry-run by design: zero apply, zero commit, zero network) -> tools/scheduler_lite.py" ;;
    auto-merge) echo "cw.sh auto-merge --facts F [--head-branch BR] [--allow-prefix P] [--daily-cap N] [--ledger P] [--merge-sha SHA] [--post-merge {green,transient,content,unrecognized}] [--apply] [--json OUT] | --selftest   # X5 auto-merge gate judge plus safety rail (six-verdict mergeability enum merge-ok / hold-red / hold-conflict / already-landed / superseded-landed-elsewhere / escalate-unknown over caller-gathered facts; verdicts and rail outcomes are data rc 0, rail refusals rc 1; the five-sample calibration set S-1..S-5 pinned in --selftest; rail = supply/* head-branch whitelist + daily budget cap 3 + append-only merge ledger rows rocqwash-automerge/1 + the post-merge red revert arc: content prescribes git revert -m 1, transient a rerun window, unrecognized an escalation; zero network, dry run by default, --apply only appends ledger rows) -> tools/auto_merge.py" ;;
    jargon-map-sync) echo "cw.sh jargon-map-sync [--md P] [--map P] [--json P] | --apply | --selftest   # jargon map sync, md table -> seed JSON (detector-map superset absorbed into the apply map; single-form admission: parenthetical annotations stripped, em-dash cells land as rewrite_or_delete, slash alternations rejected, six note-guard markers rejected; existing entries preserved with their id/exempts/cross_track_note; exact count label; plan zero-write default, --apply writes the map) -> tools/jargon_map_sync.py" ;;
    repair-weekly) echo "cw.sh repair-weekly [--ledger P] [--date YYYY-MM-DD] [--out FILE] [--json P] | --record --class CLASS --target T --repair-outcome VALUE [--ticket K] [--evidence-file J] [--reason S] [--apply] | --selftest   # repair-outcome ledger weekly distribution face, repair class E6 (ISO-week per-red outcome census + class/ticket distributions; read-only over the ledger, --out/--json the only write faces; --record appends one per-red rocqwash-repair-ledger/2 row under the enforced vocabulary, --apply required) -> tools/repair_weekly.py" ;;
    selfevolve-round) echo "cw.sh selfevolve-round [--dry-run]   # one deterministic mechanical round, cron face (census jargon_apply --plan -> apply -> verify py_compile/bash -n hard gates + norm_lint/doc_lint advisory -> auto_round commit -> push -> dispatch the CI judge; frozen faces excluded by jargon_apply; zero qualifying fixes = clean no-op pass; apply residue != zero = fail-loud, no commit) -> tools/selfevolve_round.py" ;;
    pin-repair) echo "cw.sh pin-repair --selftest | --plan | --apply [--seed P]   # provenance-pin drift repair for the jargon seed map, triage row R15 auto-repair executor (re-signs drifted provenance.sources md5 pins behind the sync tool's zero-write plan IN-SYNC verdict; --plan writes nothing, --apply touches only md5 values and re-runs the seeds suite, red verify rolls back to the pre-apply bytes; not-IN-SYNC exits without touching the seed) -> tools/pin_repair.py" ;;
    learning-feedback) echo "cw.sh learning-feedback [--selftest]   # scheduling feedback face over the three standing ledgers (round ledger, round state, experience ledger read-only; casts schema rocqwash.scheduling-feedback/1 into docs/scheduling-feedback.json: the auto versus human-approved round split, the approval rate, the per-class breakdown, and the four-state repair outcome tally; missing or corrupt inputs land in the errors field, never guessed) -> tools/learning_feedback.py" ;;
    b-gate) echo "cw.sh b-gate [--selftest]   # B-level generalization threshold audit over the round records (3 instances, each grounded in at least 1 executed round; per-class instance and round counts, a per-class readiness verdict, and an explicit gap list into docs/b-gate-audit.json, schema rocqwash.b-gate-audit/1; counts are measured from the records, never inflated) -> tools/b_gate_audit.py" ;;
    tree-audit) echo "cw.sh tree-audit --root DIR [--json OUT] | --selftest   # read-only tree health audit over .lean/.v source trees (one JSON-line census; zero subprocess, zero network, zero tree writes) -> tools/tree_audit.py" ;;
    pipeline-lite) echo "cw.sh pipeline-lite [--plan F] [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--gap-out F] [--render-gaps F] [--packet-out F] [--backfill F] [--draft-out F] [--b-gate-audit P] [--policy-ref S] [--stop-at {data,human}] [--json] | --selftest   # gap-to-admission pipeline executor, D2-2 data layer (verdict imported from scheduler_lite; rows enter PENDING; code-layer faces stay human-gated; zero network) -> tools/pipeline_lite.py" ;;
    anchor-guard) echo "cw.sh anchor-guard --repo DIR --manifest FILE [--out DIR] [--rocq BIN] [--coqchk BIN] [--timeout SEC] [--keep] | --selftest   # anchor and certificate guard for one module directory (manifest validation V1-V10; compile tri-classification; coqchk -o kernel baseline; per-anchor probe face; mutation kill matrix, zero kills = VACUOUS = red; env-gated rc 111 honest skip; write faces: the caller-named --out report and the private temp workdir; rc 0=PASS 1=red 2=usage 9=fail-loud 111=honest skip) -> tools/anchor_guard.py" ;;
    *) return 1 ;;
  esac
}

# Passthrough execution (tool -> repo-root-relative script mapping; a missing script exits 9; with no args the one-line hint prints first, then passthrough)
run_tool() {  # $1=tool  $2=target-script (relative to ROOT)  rest=args passthrough
  local tool="$1" rel="$2"
  shift 2
  local script="$ROOT/$rel"
  if [ ! -f "$script" ]; then
    echo "cw.sh $tool: missing $rel" >&2
    exit 9
  fi
  if [ "$#" -eq 0 ]; then
    hint_for "$tool" >&2
  fi
  exec python3 "$script" "$@"
}

case "${1:-}" in
  scan4)       shift; run_tool scan4       "scan/scan_v4_token.py"        "$@" ;;
  cure)        shift; run_tool cure        "wash/cure_applier.py"         "$@" ;;
  probe)       shift; run_tool probe       "wash/probe_engine.py"         "$@" ;;
  chain)       shift; run_tool chain       "tools/chain_graph.py"         "$@" ;;
  sync-ledger) shift; run_tool sync-ledger "tools/ledger_sync.py"         "$@" ;;
  erasure)     shift; run_tool erasure     "verify/erasure_classifier.py" "$@" ;;
  dual-scan)   shift; run_tool dual-scan   "scan/dual_scan.py"            "$@" ;;
  doctor)      shift; run_tool doctor      "tools/toolchain_dyld_doctor.py" "$@" ;;
  net-probe)   shift; run_tool net-probe   "tools/net_probe.py"           "$@" ;;
  triage)      shift; run_tool triage      "tools/ci_triage.py"           "$@" ;;
  union)       shift; run_tool union       "tools/registry_union.py"      "$@" ;;
  pushci)      shift; run_tool pushci      "tools/pushci.py"              "$@" ;;
  sentinel)    shift; run_tool sentinel    "tools/cw_sentinel.py"         "$@" ;;
  wash-shape)  shift; run_tool wash-shape  "tools/wash_shape.py"          "$@" ;;
  unclog)      shift; run_tool unclog      "tools/unclog.py"              "$@" ;;
  cw-doctor)   shift; run_tool cw-doctor   "tools/cw_doctor.py"           "$@" ;;
  doc-lint)    shift; run_tool doc-lint    "tools/doc_lint.py"            "$@" ;;
  netname-normalize) shift; run_tool netname-normalize "tools/netname_normalize.py" "$@" ;;
  select-audit) shift; run_tool select-audit "tools/select_audit.py"        "$@" ;;
  render-events) shift; run_tool render-events "tools/render_events.py"     "$@" ;;
  baseline-diff) shift; run_tool baseline-diff "tools/baseline_diff.py"     "$@" ;;
  dispatch)    shift; run_tool dispatch    "tools/red_dispatch.py"          "$@" ;;
  audit)       shift; run_tool audit       "tools/registry_audit.py"        "$@" ;;
  registry-fix) shift; run_tool registry-fix "tools/registry_fix.py"        "$@" ;;
  norm-lint)   shift; run_tool norm-lint   "tools/norm_lint.py"             "$@" ;;
  registry-regen) shift; run_tool registry-regen "tools/registry_regen.py" "$@" ;;
  contrib-intake) shift; run_tool contrib-intake "tools/contrib_intake.py" "$@" ;;
  evolve)      shift; run_tool evolve      "tools/evolve.py"              "$@" ;;
  vacgen)      shift; run_tool vacgen      "tools/vacgen.py"             "$@" ;;
  ci-triage)   shift; run_tool ci-triage   "tools/ci_triage.py"          "$@" ;;
  baseline-diff-facade) shift; run_tool baseline-diff-facade "tools/baseline_diff.py" "$@" ;;
  exp-append)  shift; run_tool exp-append  "tools/exp_port.py"          append "$@" ;;
  mcp-server)  shift; run_tool mcp-server  "tools/mcp_server.py"   "$@" ;;
  periscope)   shift; run_tool periscope   "tools/periscope.py"   "$@" ;;
  ai-flavor)   shift; run_tool ai-flavor   "tools/ai_flavor.py"   "$@" ;;
  ai-flavor-apply) shift; run_tool ai-flavor-apply "tools/ai_flavor_apply.py"   "$@" ;;
  auto-round)  shift; run_tool auto-round  "tools/auto_round.py"   "$@" ;;
  i18n-pipeline) shift; run_tool i18n-pipeline "tools/i18n_pipeline.py"   "$@" ;;
  i18n-translate) shift; run_tool i18n-translate "tools/i18n_translate.py"   "$@" ;;
  i18n-verify) shift; run_tool i18n-verify "tools/i18n_verify.py"   "$@" ;;
  jargon-apply) shift; run_tool jargon-apply "tools/jargon_apply.py"   "$@" ;;
  termbase)    shift; run_tool termbase    "tools/termbase.py"   "$@" ;;
  gap-cluster) shift; run_tool gap-cluster "tools/gap_cluster.py" "$@" ;;
  row-render)  shift; run_tool row-render  "tools/row_render.py" "$@" ;;
  calibration-ledger) shift; run_tool calibration-ledger "tools/calibration_ledger.py" "$@" ;;
  lean-sweep)  shift; run_tool lean-sweep  "tools/lean_sweep.py" "$@" ;;
  verdict-diff) shift; run_tool verdict-diff "tools/verdict_diff.py" "$@" ;;
  symbiosis-bus) shift; run_tool symbiosis-bus "tools/symbiosis_bus.py" "$@" ;;
  uplink)      shift; run_tool uplink "tools/uplink.py" "$@" ;;
  evolution-dashboard) shift; run_tool evolution-dashboard "tools/evolution_dashboard.py" "$@" ;;
  bus-feeder)  shift; run_tool bus-feeder "tools/bus_feeder.py" "$@" ;;
  axiom-guard) shift; run_tool axiom-guard "tools/axiom_guard.py" "$@" ;;
  source-fetch) shift; run_tool source-fetch "tools/source_fetch.py" "$@" ;;
  sweep-verdict) shift; run_tool sweep-verdict "tools/sweep_verdict.py" "$@" ;;
  release-chain) shift; run_tool release-chain "tools/release_chain.py" "$@" ;;
  claim-watch) shift; run_tool claim-watch "tools/claim_watch.py" "$@" ;;
  axiom-sweep) shift; run_tool axiom-sweep "tools/lean_axiom_sweep.py" "$@" ;;
  numeric-probe) shift; run_tool numeric-probe "tools/numeric_probe.py" "$@" ;;
  statement-identity) shift; run_tool statement-identity "tools/statement_identity.py" "$@" ;;
  capability-index) shift; run_tool capability-index "tools/capability_index.py" "$@" ;;
  axiom-audit) shift; run_tool axiom-audit "tools/axiom_audit.py" "$@" ;;
  vacgen-coq) shift; run_tool vacgen-coq "tools/vacgen_coq.py" "$@" ;;
  flaky-guard) shift; run_tool flaky-guard "tools/flaky_guard.py" "$@" ;;
  repair-scope) shift; run_tool repair-scope "tools/repair_scope.py" "$@" ;;
  roster-resync) shift; run_tool roster-resync "tools/roster_resync.py" "$@" ;;
  scheduler-lite) shift; run_tool scheduler-lite "tools/scheduler_lite.py" "$@" ;;
  auto-merge) shift; run_tool auto-merge "tools/auto_merge.py" "$@" ;;
  jargon-map-sync) shift; run_tool jargon-map-sync "tools/jargon_map_sync.py" "$@" ;;
  repair-weekly) shift; run_tool repair-weekly "tools/repair_weekly.py" "$@" ;;
  selfevolve-round) shift; run_tool selfevolve-round "tools/selfevolve_round.py" "$@" ;;
  pin-repair) shift; run_tool pin-repair "tools/pin_repair.py" "$@" ;;
  learning-feedback) shift; run_tool learning-feedback "tools/learning_feedback.py" "$@" ;;
  b-gate) shift; run_tool b-gate "tools/b_gate_audit.py" "$@" ;;
  tree-audit) shift; run_tool tree-audit "tools/tree_audit.py" "$@" ;;
  pipeline-lite) shift; run_tool pipeline-lite "tools/pipeline_lite.py" "$@" ;;
  anchor-guard) shift; run_tool anchor-guard "tools/anchor_guard.py" "$@" ;;
  help|-h|--help)
    if [ "$#" -ge 2 ]; then
      if hint_for "$2"; then
        exit 0
      else
        echo "cw.sh help: unknown tool: $2 (legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events|dispatch|audit|registry-fix|norm-lint|registry-regen|contrib-intake|evolve)" >&2
        exit 2
      fi
    fi
    usage
    exit 0 ;;
  "") usage; exit 0 ;;
  *)
    echo "cw.sh: unknown tool: $1 (legal: scan4|cure|probe|chain|sync-ledger|erasure|dual-scan|doctor|net-probe|triage|union|pushci|sentinel|wash-shape|unclog|cw-doctor|doc-lint|netname-normalize|select-audit|baseline-diff|render-events|dispatch|audit|registry-fix|norm-lint|registry-regen|contrib-intake|evolve|help)" >&2
    usage >&2
    exit 2 ;;
esac
