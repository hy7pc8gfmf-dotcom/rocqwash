# rocqwash Architecture (English)

Purpose.  Reference architecture of the rocqwash toolchain for Coq/Rocq
  constructive-mathematics projects: the three-chain layout, the toolchain
  data-flow stages, the per-module component table, the `cli/rocqwash`
  routing contract, the cpu_guard thermal protocol, and the planned design
  targets. Implemented and pending components are labeled as such.
Interface.  Documentation face; it defines no interface of its own and
  documents the unified entry `cli/rocqwash` plus each component's CLI
  surface. It pairs with the Chinese mirror `docs/zh/architecture.md`.
Dependencies.  Statements describe components under `scan/`, `names/`,
  `wash/`, `verify/`, `seam/`, `certify/`, `watch/`, `tools/`, `wrapper/`,
  `recipes/`, `examples/`, and `tests/`, checked against those sources at
  the stated snapshot date.
Evidence.  Component rows carry the implementing file names; stage and
  status claims were checked against the source tree; the demo chain cites
  `examples/README.md`; the suite size cites `tests/run_tests.sh`.
Exit-codes.  None of its own; the exit codes it documents are described
  exactly as implemented in the §5 table.

> Snapshot: October 31, 2026 — the certify deep piece `push_gate.py` (push-window
> four-criteria + UNION v2 manifest) and the first `watch/` piece `watch.py` landed;
> suite extended to 16 cases (the rqwash2 agent). This document faithfully reflects
> the current state of the repository: implemented components are checked against the
> source code, pending components are labeled as such (empty dirs / placeholders).
> Chinese mirror: [`docs/zh/architecture.md`](../zh/architecture.md). The repo is under
> active development (modules land continuously); the code is the source of truth.

## 1. Positioning & Core Principle

rocqwash is a mechanical diagnosis / washing / verification / certification toolchain
for Coq/Rocq constructive mathematics projects:

> **Core principle**: What can be mechanically verified via type-theoretic structural
> criteria shall never be delegated to probabilistic models.

Three honesty laws run through all components:

1. **Report the list, not a verdict of cleanliness** (E364 blind-zone law) — the
   scanner only emits a hit list with per-hit classification notes; a "no leakage"
   verdict may only come from the kernel census (SortAlive `__`-census); any 0-hit
   result must additionally pass the negative-vector control (E364 vectors embedded
   in `--selftest`).
2. **fail-loud** — assertion failures / missing files / unknown commands exit
   non-zero; silent error swallowing is forbidden; unterminated comments/strings and
   orphan closers are all ledgered.
3. **Idempotent & replayable** — wash/patch operations are exact-string + count
   asserted + skip-if-already-applied; safe to replay.

## 2. Three Chains in One

```
Toolchain        (scripts + templates + canonical recipes)
    ↓
Logic Chain      (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## 3. Toolchain Data Flow

```
                  ┌────────────────────────────────────────────────────┐
                  │ tools/cpu_guard.sh v3 — thermal wrapper for ALL compiles │
                  │ (FRONT/MID/BACK dynamic ladder queue + pmset gate)      │
                  └────────────────────────┬───────────────────────────┘
                                           │ wraps every compile
  .v ──▶ scan ──▶ names ──▶ wash ──▶ compile ──▶ verify(R4) ──▶ seam ──▶ certify ──▶ watch
        done     done     done    (guard)     done*        done*     done     done

  done* = first generic per-file piece landed (wash: ledger executor · verify: four-pack ·
          seam: fingerprint probe; the full R4 three-source conjunction remains TODO)

  Unified entry: cli/rocqwash (subcommands scan / names / wash / verify / seam / certify / watch)
```

| Stage | Input | Output | Status |
|---|---|---|---|
| scan | single `.v` | hit list + classification notes (stdout / `--json` / `--hits-csv`) | implemented |
| probe | candidates TSV + source tree + world dir | batch closure-compatibility ledger JSON (rc triage + red-cause classes; resume-idempotent) | implemented (`wash/probe_engine.py`; every probe compile wrapped by cpu_guard) |
| names | one or two `.v` | ordered statement-name list + N=N ordered-equality assertion | implemented |
| wash | single `.v` + ledger JSON | washed `.v` (exact-string + count, idempotent) | implemented (`wash_engine.py`, ledger must be explicit); effort / work stream batch tool also landed |
| compile | `.v` | `.vo` (magic `436f712100015ff4` check) | via cpu_guard |
| verify(R4) | `.v`+`.vo` pair (± rc/log evidence) | green-verdict four-pack per-piece ledger + verdict | implemented (`verify_vo.py`); full R4 three-source unified entry is TODO (see §4 note) |
| seam | single `.v` | W13 four-mechanism fingerprint candidate list + prescription mapping | implemented (`seam_probe.py`, candidates not verdicts) |
| certify | dir / multi-world + manifest | two-tier freeze manifest freeze/check + push-window four-criteria + UNION v2 + frozen-eight registry check | implemented (`freeze_manifest.py` + `push_gate.py` + `frozen8.py`, see note ③) |
| watch | runs evidence / remote | CI in-flight monitoring + pin-IP push (dry-run default) + ls-remote confirmation | implemented (`watch.py`, zero-route by construction) |

## 4. Component Table (verified against source)

Shape column: **generic per-file** = argparse interface, auto-routed by
`cli/rocqwash`; **effort / work stream tool** = `_`-prefixed, hardcoded paths, no per-file argv,
NOT auto-run by the unified entry (invoke directly with `python3`).

| Module | File | Shape | Status | Notes |
|---|---|---|---|---|
| `scan/` | `mac_stmt_scan.py` | generic per-file | **implemented** | Statement-face Prop bare-form scanner: five frozen lane families P1–P5 (13 sub-channels: Qlt/Qle/`==`/exists·and·or·not·false/bare `=`/`<=`·`<`·`>=`·`>`) + three negative-capture families (P6_In/P8_True/P9_proper — conclusion-position CAPTURE / premise-position EXEMPT); 4-way classification RED/WHITELIST/EXEMPT/CAPTURE; whitelist & BRIDGE_FAMILY registry; mixed-face (carrier co-present with bare form) detection; `--manifest` four-ledger reconciliation (swallowed/blind/kind_drift/line_drift, blind=∅ asserted); `--selftest` E364 frozen vectors; `--baseline` S09 reference run |
| `scan/` | `dual_scan.py` (with `scan_v4_token.py`) | generic per-file | **implemented** (v32, November 3, 2026, toolified from `seat_wash66/w66_dual_scan.py`) | Dual-scanner cross-check driver: scan_v4_token (token-level) + mac_stmt_scan (statement-face level) scan the same candidate files -> per-file dual rc/station counts/hit line-sets -> diff report (only_v4 / only_stmt / common, by line number) + `--out` report JSON (sorted iteration + sort_keys; byte-identical on re-run). Instrument-level facts are stated mechanically per file: both word-face scanners are structurally blind to application/type-face red causes (the S07-lineage Illegal-application family) — scanner consensus is not a completeness certificate, one-sided stations are reported as-is for a third source. `--dir/--file/--out/--scan-v4/--mac-stmt/--timeout` fully parameterized, zero hard-coded paths, zero network; exit code = number of failed scans (station counts never fail). Ten-section `tests/test_dual_scan.py` (suite case 42) |
| `names/` | `mac_stmt_names.py` | generic per-file | **implemented** | Top-level statement-name ordinal extractor: census scope (9 kinds, no Let) / `--include-let` rendezvous scope; `--compare` ordered 1:1 equality assertion between two files (N=N form, exit 2 on mismatch); `--expect` count assertion; `--kinds` filter; ARM2 proof-body consumption; Unicode identifiers; fail-loud throughout |
| `wash/` | `wash_engine.py` | generic per-file | **implemented** (October 31, 2026) | Generic per-file canonical wash engine: the `_abl1_wash.py` apply loop generalized 1:1 into an argv-driven ledger executor — exact-string + count assertions + idempotent (skip when new form present and old gone) + nested-bracket awareness (bracket-balance checked after comment/string masking) + write isolation (never rewrites `--file`) + fail-loud (any FAIL → that file not written). Ledger JSON = field-for-field translation of the PATCHES ledger (tag/old/new/expect). No ledger → exit 3 (nothing guessed; SKIP semantics). `--selftest` seven frozen vectors |
| `wash/` | `_abl1_wash.py` | effort / work stream tool | landed | abl1 batch wash tool: exact-string + count assertions + idempotent (skip when new form already on disk); nested-bracket aware; `ROOT` hardcoded to an external effort / work stream sandbox, no argv |
| `verify/` | `verify_vo.py` | generic per-file | **implemented** (October 31, 2026) | Generic per-file green-verdict four-pack checker: a (.v, .vo) pair plus optional rc/log evidence — ① exit==0 (`--rc`/`--exit-file`) ② log with zero Error lines ③ .vo magic `436f712100015ff4` ④ .vo strictly newer than .v; criteria inherited frozen from `_parse_fin_mac.py:82-108`; missing evidence = NOT-RUN, explicitly ledgered, never counted green (③④ always checked); `--selftest` nine frozen vectors |
| `verify/` | `_parse_fin_mac.py` | effort / work stream tool | landed | censusFIN_mac parse lane: extraction-erasure semantics (RED iff `__` appears in let body / type annotation, incl. Set-cloaked Prop) + green-verdict four-pack (exit code / log zero Error / `.vo` magic / `.vo` mtime freshness) + ann-regex dual-form law |
| `verify/` | `gate4_comment_guard.py` | effort / work stream tool | landed | Gate-4 header-comment five-field mechanical guard v2.1: five lexeme families + three domains + judging principle; zero compile / zero network / zero tree writes |
| `verify/` | `retrofit_gate7_irr.py` | effort / work stream tool | landed | Gate-7 English adaptation: touches comments only, never code tokens; frozen-md5 + token-stream identity assertions, fail-loud no-write |
| `seam/` | `seam_probe.py` | generic per-file | **implemented** (October 31, 2026) | W13 four-mechanism generation-gap fingerprint probe: ① `==`-statement × rewrite/ring/reflexivity → `qeq_imp_qeqT` flip-back ② `apply (`/`rewrite (` full-application forms → keyed-matching instantiation ③ `rewrite` of a this-file premiss-carrying lemma (depth-0 `->` after colon) → assert-ification + dual-shore bridge ④ multi-line Require / statement-face qualified names absent from the Require set (prelude exemption registry excluded) → topology completion. Segmentation/lexeme canon reimplemented locally from the frozen scan canon; E364 blind-zone law (candidates, not verdicts; 0 hits ≠ "seamless"); `--selftest` four positive vectors + masking negatives |
| `certify/` | `freeze_manifest.py` | generic per-file | **implemented** (October 31, 2026) | Two-tier freeze manifest: tier1 per-file md5 (deterministic walk, `relpath  md5` line ledger) + tier2 = md5 of the tier1 ledger text (tampering with the manifest is detected); freeze idempotent (no timestamps; same tree reproduces a byte-identical manifest) + check three-way reconciliation (changed/added/removed; zero drift exit 0); `.git/` and the manifest itself excluded |
| `certify/` | `push_gate.py` | generic per-file | **implemented** (October 31, 2026, the rqwash2 agent) | certify deep piece (coexists with frozen v1; read-only import of its tier1_lines/tier2_of inherits the frozen accounting format): `window` mechanical check of the push-window four-criteria — c1 CI in-flight = 0 (`--runs-json` pre-fetched evidence / `--ci-capped-min` reflog push-timeline evidence; the tool itself does zero networking; no evidence = NOT-RUN = window closed, fail-closed) + c2 local ≥ remote (behind = 0 after fetch) + c3 fetch clean (ls-remote read twice, same sha, remote sha is an ancestor of HEAD) + c4 cert green (suite rc = 0 mandatory + optional `--freeze-manifest` zero drift); judges the window, never pushes — OPEN exit 0 / CLOSED (incl. NOT-RUN) exit 1. `union-freeze`/`union-check` UNION v2 multi-world manifest (schema rocqwash-union-manifest/2): per-world tier1/tier2 inherits v1 + a third tier union_tier2 (md5 of the per-world tier2 line ledger) + `--tier2` side file; freeze idempotent byte-identical + check per-world three-way reconciliation + three-tier cross-checks; `--selftest` UNION six vectors + window four vectors (local path remotes, zero network) |
| `certify/` | `frozen8.py` | generic per-file | **implemented** (November 1, 2026, landed in the v3 collection round; rqsup4 round-5 route fill) | Frozen-eight in-service registry check (schema rocqwash-frozen8-manifest/1, ledger source = the update ledger `更新账.md` §`三`): `--selftest` four in-ledger judgment vectors + `check --list <manifest> --tier2 <side>` four-ring cross-check (tier2 self-consistency / manifest ≡ ledger / disk ≡ ledger / side file; 0 changed / 0 removed); covered by suite cases t_frozen8 + t_frozen8_check. The CLI route `rocqwash certify frozen8` was added in rqsup4 round 5 (the piece landed in v3 but the route table lacked it — a legal generic entry was blocked by unknown-sub-verb, a contract drift now fixed) |
| `watch/` | `watch.py` | generic per-file | **implemented** (October 31, 2026, the rqwash2 agent) | First watch piece: `ci` CI in-flight monitoring (`--runs-json` offline evidence / `--repo owner/name --online` read-only urllib query; `--interval/--timeout` polling; any status≠completed counts as in-flight, fail-closed; NETWORK-UNREACHABLE honestly ledgered) + `push` pin-IP push wrapper (default DRY-RUN: prints the ledger, zero network, zero execution; `--yes` actually pushes; remote URL host rewritten to `--pin-ip` preserving userinfo/port + `http.<rewritten>.extraheader=Host:` per the effort / work stream recipe; output masking = `--mask` strings ∪ URL userinfo password ∪ env ROCQWASH_MASK → `***MASKED***`; `--ssl-verify-off` must be explicit and warns loudly) + `confirm` ls-remote N-read confirmation (N≥2 — the double-read discipline floor; all reads equal → PUSH-CONFIRMED). **Structurally zero route**: no rerun/cancel/workflow_dispatch code paths exist — the no-route rule is guaranteed by construction; the tool compiles nothing, all compiles still go through the frozen cpu_guard wrapper. `--selftest` zero-network vectors (ci four + rewrite/mask units + push dry-run + env masking + confirm three, local path remotes) |
| `tools/` | `cpu_guard.sh` | generic | **implemented** | cpu_guard v3 thermal wrapper (see §6) |
| `tools/` | `select_audit.py` | generic per-file | **implemented** (November 1, 2026, rqsupport lesson ② · rqsup4 real-table audit) | Selection auditor (nw6 + enbig7 lessons tooled): batch selection lists are grepped against the tree's order.txt by **full-table read** (memory forbidden) — DUP-BATCH in-batch duplicates / DUP-CROSS cross-batch claim collisions (same-domain dual-agent precursor) / NOT-IN-ORDER names absent from the table / DUP-ORDER duplicate rows in the registry itself; `--grep` single-name full-table stand-in; name normalization accepts `#gen-tag`/`.v`/bare/`/`-path forms; `--json` ledger. Real-table precedents (rqsup4 inspection, November 1, 2026): scripts/order.txt (671 rows) CLEAN / Live table (199 rows) DUP-ORDER×2 on record (UpReqBanachExpAdd·abl_normconv_real each R28+R29 — recorded, not judged). Nine-judgment selftest + `tests/test_select_audit.py` (suite case 27) |
| `tools/` | `_gen_fin_mac.py` / `_abl1_4b_compile.py` | effort / work stream tools | landed | censusFIN SortAlive probe template generator (parameterized module/world/dep-chain); R4 4b ocamlc compile driver (hardcoded opam paths) |
| `cli/` | `rocqwash` | unified entry | **implemented** | Seven-subcommand routing (contract in §5; October 31, 2026 fixed the run_module branches missing `shift` — the subcommand name leaked into routed tools, now aligned with the §5 "1:1 passthrough" contract) |
| `wrapper/` | `coqc_shim.sh` + `gate7_probe.sh` | adapter layer (bash · not CLI-routed) | **implemented** (October 31, 2026, the rqadapt agent) | Canonical adapter face for the gate7 probe chain (out-of-repo piece `ConstructiveWorld-Set/scripts/gates/gate7_extract_run.py`, read-only frozen in its own repo): `coqc_shim.sh` = canonical argv shim from gate7's `--coqc` parameter to the local Live toolchain `rocq c` (zero-logic 1:1 passthrough; `GATE7_PROBE_ROCQ` override; missing rocq → exit 9; **no guard nesting inside the shim** — gate7 invokes the shim as a per-module subprocess, re-wrapping on the same registry = deadlock, the nw8 precedent); `gate7_probe.sh` = canonical launcher (env.sh canonicalization + `unset COQLIB ROCQLIB` + `ulimit -s 65532`; guard wraps the python process only [`-Front 0 -Mid 1 -MaxWaitSec 600`, `GATE7_PROBE_REG` lane split]; `python3 -B` forbids `__pycache__` writes into the read-only original repo; order assembly [`--module`/`--order` exactly one]; args after `--` forwarded verbatim to gate7 [`--gate --baseline …`]; `--dry-run` ledger). **Zero criterion duplication** — green/red, magic counts, erasure candidates are judged solely by the gate7 original; exit codes pass through 1:1 (2 = this layer's usage error, 9 = missing file, otherwise gate7's own 0/1/2). Thirteen-judgment selftest `tests/test_gate7_wrapper.py` (zero compile, zero writes; suite case 18); E2E smoke on a read-only world copy ran S01_BaseRing live: names=69 rc=0 magic=0/0, equal to the committed baseline. Earlier adapter pieces in the same dir: `guard.sh` (pass-through for frozen `tools/cpu_guard.sh`) + `scan_station.py` (scan original-identification wrapper; see `tests/test_scan_station.py` and the update ledger) |
| `wash/` | `world_hook.py` | generic per-file | **implemented** (November 1, 2026, rqsupport lesson ① · rqsup4 real-tree audit) | wash_engine world-base verification hook (nw5 lesson: assert world = certified generation before born; stale generations forbidden): `--world` + parameterized anchors via `--manifest`/`--anchor` (built-in nw5ver five anchors); the assertion precedes any engine behavior (failure exit 9, zero writes, zero half-state); args after a bare `--` forward verbatim to wash_engine (read-only import of the frozen engine, zero-byte reuse). Real-tree precedents (rqsup4 inspection, November 1, 2026): built-in anchors vs `seat_nw5ver/tree` **5/5 MATCH**; same anchors vs `seat_dver2/tree` (newer generation) 3 WDIFF + 1 WMISS → **RED rc 9** (anchors must follow the generation — mechanically demonstrated). Twelve-judgment selftest + `tests/test_world_hook.py` (suite case 26) |
| `verify/` | `verify_gate6.py` | generic per-file | **implemented** (November 1, 2026, rqsupport lesson ③ · rqsup4 real-tree audit) | gate6 census thin wrapper + EntropyUnsatMark precedent mechanized: (1) thin invocation of the out-of-repo original `gate6_statement_census.py` (1:1 args, rc passthrough, zero criterion duplication; guard launcher face is `wrapper/gate6_census.sh`); (2) EUM-VERDICT four judgments (treatment must lower ch1 / names stay ordered-equal on surviving files / side channels ch2·ch3 zero growth + new files axiom-free born / retirement is INFO, not penalized). Real-tree precedent (rqsup4 inspection, November 1, 2026): `--tree seat_eum/work` → `files=1 ch1=0 ch3=0 names=5` (equals the precedent after-report). Ten-judgment selftest + `tests/test_verify_gate6.py` (suite case 28) |
| `recipes/` | `S07_projection_reanchor_E5.md` + `ENBIG7_same_domain_collision_PW1.md` | prescription docs | **implemented** (November 1, 2026, rqsupport lesson ④ + rqsup4 lesson ③) | Two precedent-documentation pieces: **E5** = statement-surface projection re-anchor prescription (Class field projections carrying the statement surface → extraction Obj.magic 293 → three-mapping re-anchor to zero; knife-face three-way table + four acceptance proofs + tooling wiring; precedent source: the reanchor work stream); **PW1** = same-domain dual-agent collision private-world rebuild prescription (dver2-enbig7 precedent, arbitration 36c35816: converge → wait-for-quiet → full re-audit → private-world reborn in order.txt chain order → three full md5 re-audits; five fixed steps + tooling wiring + boundaries). Machine-checked by `tests/test_recipe_s07.py` (case 29) + `tests/test_recipe_enbig7_pw1.py` (case 30) |
| `wrapper/` | `precedent_station.py` | combiner station (not CLI-routed) | **implemented** (November 1, 2026, rqsup4 lesson ⑤) | Three-precedent acceptance-chain combiner (three-precedent playbook toolified): the shared acceptance chain of the E7 carrier-relay / R23 notation-recarrier / E5 projection-re-anchor precedents — ① names comparison (N=N ordered-equal) → ② gate4 → ③ gate7 launcher (optional step, real compile; default light chain ①②) — in one station command; `--knife` records the knife face (station-ledger bookkeeping only); zero criterion duplication — the three steps' verdicts come solely from each original's rc, and gate7's magic=0 hard acceptance stays with its own gate form (args after a bare `--` forwarded verbatim); hard-wins aggregation law (0 all-green / 1 hard-red / 2 REVIEW·usage·assert-fail / 9 missing, zero steps started); pin assertion face for the two frozen originals (gate7 launcher is non-frozen, recorded not judged). Ten-judgment selftest + `tests/test_precedent_station.py` (suite case 31); E2E: `seat_rqsup4` sandbox world (S01_BaseRing freshly born) gate7 step live-run `names=69 rc=0 magic=0/0` + GATE7-GREEN, idempotent replay equal (measured November 1, 2026) |
| `examples/` | `demo_prop_leak.v` et al. | demo | **implemented** | Single-file full-chain demo (see `examples/README.md`, with measured results). Since October 31, 2026 the wash step runs for real: `washed/demo_ledger.json` (16 exact-string patches) drives `wash_engine.py`, and the engine output is **byte-identical** to the reference `washed/demo_prop_leak_washed.v` (cmp assertion; idempotent replay applied=0 skipped=16) |
| `wash/` | `probe_engine.py` | generic per-file | **implemented** (v30, November 3, 2026, toolified ①) | Batch closure-compatibility probe engine (1:1 generalization of `seat_wash13/probe_batch.py`): candidates TSV (required cols `件名`/`md5` · optional `RED`) × source tree × world dir → per-file cp → `rocq c` probe (wrapped by cpu_guard when `--guard` given; exit code read directly from subprocess returncode, no pipes; `--timeout` expiry → rc=124) → rc triage verdict: rc0+RED>0=WASHABLE / rc0+RED=0=BORN-CLEAN / rc0+RED-missing=RC0 (three-way split not decidable, reported as-is) / rc1=red-cause classification (MISSING_LIB missing-library [captured lib name into missing field] / ILLEGAL_APP / NO_SUBTERM / FACE face-mismatch — drift family / OTHER / UNKNOWN) → ledger JSON (schema rocqwash-probe-ledger/1; resume-idempotent: existing record with same md5 skips, `--fresh` re-probes; re-running the same candidate set is byte-identical). Post-probe cleanup: the five artifacts move out of the world into `--logdir` as evidence. Four-judgment selftest + `tests/test_probe_engine.py` nine sections (suite case 38; real-rocq full chain gated by ROCWASH_ROCQ, SKIP by default) |
| `tools/` | `chain_graph.py` | generic per-file | **implemented** (v30, November 3, 2026, toolified ②) | Multi-ledger probe merge → chain-root graph → TOP ranking (1:1 generalization of `seat_wash25/w25_merge_ledgers.py`): N-ledger union (argv order = merge order; later ledger overrides; batches accumulate full history; probe_engine "records" shell and W13-style bare dict both accepted) → missing-lib extraction (missing field preferred, red-text regex fallback) → rc1 missing grouping lib→dependents/n/batches + **root self-washability fields** (self.probed/rc/verdict/washable — washable=true = washing this root unlocks its dependents; false = mid-chain block; UNPROBED = root not in candidate set) → TOP ranking markdown + json (dependents descending; `--top` cutoff; json `top_order` preserves rank explicitly; sorted iteration + sort_keys determinism, byte-identical reruns). Six-judgment selftest + `tests/test_chain_graph.py` seven sections (suite case 39) |
| `tools/` | `ledger_sync.py` | generic per-file | **implemented** (v30, November 3, 2026, toolified ③ · v2.1 same-day additions) | Probe-ledger × status-ledger TSV merge sync (from the November 3, 2026 status-ledger v2 practice): E1 dedup (same-name rows keep first, each loudly recorded) / E3 ghost (probed name absent from TSV — recorded only, never row-added) / MD5-DRIFT (probe md5 ≠ TSV md5 — annotated, not upgraded) / NO-MD5 (W13-style record without md5 — same) / GEN-DIVERGENCE (v2.1: records carrying divergence_with/divergence_md5 are surfaced per-entry loudly with an idempotent row note probe:gen-div:\<dropped\> — the divergence priority is codified: the kept generation is the one the downstream freeze ledger references on its basis roster; the dropped generation is annotated, never discarded) / probe-ledger shape recognition (v2.1: records shell / freeze-ledger `items` subkey shell / bare dict filtered by record shape with non-record metadata keys counted loudly into meta_skipped, zero records after filtering → fail-loud rc2) / column validation fail-loud (missing required cols `件名`/`md5`/`RED`/`状态`/`备注` or ragged row width → rc2, no output) → sync actions = idempotent note tag in the remark column (probe:rc0 / probe:rc1:\<class\> / probe:timeout / probe:no-src) + `--policy unprobed-only` default upgrade (UNPROBED rows: rc0→WASHABLE / rc1→DRIFT-BLOCKED; higher statuses never downgraded; annotate-only = notes only) → new TSV + optional `--report` JSON (schema rocqwash-ledger-sync/1). Same-input reruns are byte-identical. Thirteen-judgment selftest + `tests/test_ledger_sync.py` ten sections (suite case 40) |
| `docs/` | this tree | docs | **implemented** | zh/en bilingual architecture docs |
| `tests/` | `run_tests.sh` + 24 test files + `fixtures/` | generic | **implemented** | Test-suite master entry: `bash tests/run_tests.sh` (**43 cases**, positive/negative pairs; all-green exit 0 / any-red exit 1; idempotent, zero repo writes; `ROCQWASH_TESTS_FAIL_PROBE=1` injects an always-red case as suite self-check); covers scan selftest / names `--expect` pos·with-Let·neg / gate4 clean·dirty / adaptation dry-run / wash effort / work stream-tool three-judgment / wash_engine six-judgment / verify_vo thirteen-judgment (incl. `--require-fresh` fresh-compile defense, four vectors — divmod_gen stale-vo false-green toolified) / seam_probe four-mechanism / freeze_manifest four-judgment / push_gate UNION six + window four / watch zero-network vectors / cpu_guard `-Direct` smoke + exit-code propagation / scan_station nine-judgment / gate7 adapter thirteen-judgment / verify_born nine-judgment / frozen8 four + check / quad8 eight + check / frozen_call five / gate6·born launcher / world_hook five / select_audit five / verify_gate6 five / recipe_s07 five / recipe_pw1 five / precedent_station seven / netname_normalize nine-section (.v.v netname normalizer, toolified ①) / verify_fresh eight-section (fresh-compile defense, toolified ②) / extract_magic eleven-section (gate7 extraction-face Obj.magic per-module gate, pit-ledger entry-10 toolified ③) / scan_v4_token eleven-judgment (token-level census, W15 toolified ①) / cure_pack eleven-judgment (consumer-cure canonical pack, W15 toolified ②) / erasure_classifier thirteen-judgment (erasure six clusters, W15 toolified ③) / probe_engine nine-section (batch closure probe, v30 toolified ①) / chain_graph seven-section (chain-root graph, v30 toolified ②) / ledger_sync ten-section (ledger sync, v30 toolified ③·v2.1 adds items shell / metadata filtering / GEN-DIVERGENCE) / comment_pack six-section (comment-domain sweep sidecar, v31: nested-comment+string state machine / flag-word exchange / header replacement / w7 code-line-equality projection / idempotence / CLI three codes) / dual_scan ten-section (dual-scanner cross-check driver, v32 toolified from the W66 field report: dual scan x per-file diff report / deterministic byte-identical reports / CLI four codes) / cure_pack v32 extension (S07-lineage five-pattern selftests + S07 fixture flows + conflict --json rc4 regression + gated S07 compile arc red->green->extraction 0/0) / cure_pack v34 extension (E2/E3 extraction-defect-family five-pattern selftests + two fixture flows + gated E2/E3 compile arc: pre-fix compiles green = extraction-time family -> cured green -> E2 face 'a1 -> nat->nat monomorphised + consumer-unit magic 0/0 + world accessor debt pinned=1) (suite 43 cases; per-case criteria in [`tests/README.md`](../../tests/README.md)) |
| `workflows/` | — (empty) | — | pending | CI workflow placeholder (`.github/workflows/ci.yml` on file: macOS suite gate) |

> Note ①: `verify/` now holds four non-underscore-prefixed files — the historical
> effort / work stream tools `gate4_comment_guard.py`, `retrofit_gate7_irr.py` plus the generic
> `verify_vo.py` and `verify_gate6.py` (landed November 1, 2026, rqsupport lesson ③).
> On October 31, 2026 the adapter work stream landed an **explicit sub-verb
> route**: `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit [args…]` exec-passes
> 1:1 (same contract shape as certify/; the `verify_gate6` sub-verb was added November 1, 2026
> in rqsup4 round 4 — the post-integration route-gap fix); bare `verify` still
> exits 4 with a
> listing for manual disambiguation, unknown sub-verbs exit 2, `verify help`
> prints the sub-help. **Zero frozen-file changes (rename-free unification)**;
> calling `python3 verify/verify_vo.py --v ... --vo ...` directly still works.
>
> Note ②: the extraction side of the full R4 three-source conjunction (bare
> full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0) depends on
> the `_abl1_4b_compile.py` ocamlc linker path (hardcoded opam paths); generalizing it
> is over the scope of this round and is **honestly logged as TODO** — `verify_vo.py`
> currently covers the four-pack segment (compiled-artifact side); the extraction-side
> three-source conjunction awaits a later work stream.
>
> Note ③: `certify/` now holds three generic pieces — `freeze_manifest.py` (frozen),
> `push_gate.py` (landed October 31, 2026 by the rqwash2 agent) and `frozen8.py` (the frozen-eight
> registry check, landed in the v3 collection round before the rqsup4 round-5
> inspection). **On October 31, 2026 the rqadapt agent landed the explicit CLI route**:
> `cli/rocqwash certify
> freeze|push_gate|frozen8 [args...]` routes by sub-verb with 1:1 passthrough (args and
> exit codes unrewritten; `--help` after a sub-verb reaches each piece's own
> argparse; the `frozen8` sub-verb was added November 1, 2026
> in rqsup4 round 5 —
> the post-integration route-gap fix); with no sub-verb it still exits 4 with a listing for manual
> disambiguation (same contract shape as verify/); an unknown sub-verb exits 2.
> The CLI-side unification is done — the `_`-prefix rename route still awaits the
> freeze lift.
>
> Note ④: `watch/watch.py push` defaults to DRY-RUN (prints the ledger, zero network,
> zero execution); `--yes` actually pushes. The push discipline used here =
> `push_gate.py window` first (CLOSED → no push) → `watch.py push` with the real rc
> → `watch.py confirm` double ls-remote read.
>
> Note ⑤: `wrapper/` = the **adapter-layer family directory** (canonical in-repo
> adapter faces for frozen / out-of-repo pieces; always new files, never touching
> the in-service originals). On October 31, 2026 the rqadapt agent landed the gate7 probe-chain
> adapter (`coqc_shim.sh` + `gate7_probe.sh`, canonicalizing the hand-made
> shims/launchers each effort / work stream kept in its own domain — nw7/nw8 precedent;
> zero criterion duplication, exit codes pass through 1:1); the same work stream's earlier
> rounds landed `guard.sh` (cpu_guard pass-through) + `scan_station.py` (scan
> identification wrapper). Adapter layers are not routed through `cli/rocqwash`
> (bash face; invoke as `bash wrapper/…` directly); every compile still goes
> through the frozen cpu_guard wrapper.

## 5. `cli/rocqwash` Unified-Entry Routing Contract

```
rocqwash <subcommand> [args...]
  scan     → scan/mac_stmt_scan.py (args & exit codes passed through 1:1)
  names    → names/mac_stmt_names.py (same)
  wash|verify|seam|certify|watch → dynamic per-module routing:
      · exactly one NON-underscore-prefixed .py in the module dir = generic
        per-file entry → auto-routed
      · underscore-prefixed .py = effort / work stream tool → NOT auto-run (prevents
        accidental writes to external sandboxes)
      · no generic entry → exit 3; multiple generic entries → exit 4 (listed
        for manual disambiguation)
```

Exit-code table:

| Tool | 0 | 2 | 3 | 4 | 9 |
|---|---|---|---|---|---|
| `scan --file` | list printed (hits are findings, not failures) | `--selftest` vector failure | — | — | file missing |
| `names` | list / assertions pass | `--expect`/`--compare` assertion failure | — | — | file missing |
| `wash/wash_engine.py` | full ledger APPLY/SKIP (fail=NO) | any FAIL = 1; malformed ledger / usage = 2 | no ledger (nothing guessed; SKIP semantics) | — | `--file`/`--patch` missing |
| `verify/verify_vo.py` | four-pack PASS | usage error (--rc/--exit-file mutual exclusion etc.) | — | — | path missing (any red FAIL = 1) |
| `seam/seam_probe.py` | ledger printed (candidates are findings, not failures) | `--selftest` vector failure | — | — | `--file` missing |
| `certify/freeze_manifest.py` | freeze done / check zero drift | usage error / malformed manifest | — | — | dir/manifest missing (check drift = 1) |
| `certify/push_gate.py` | window = OPEN / union-check zero drift / union-freeze done | usage error / malformed manifest (union-check drift = 1; window CLOSED incl. NOT-RUN = 1) | — | — | repo/manifest/world-root missing |
| `watch/watch.py` | ci = CI-IDLE / push DRY-RUN / confirm PUSH-CONFIRMED (real push = git rc passthrough) | usage error (ci active>0 or unusable evidence = 1; confirm mismatch = 1) | — | — | repo/remote/file missing |
| `cli/rocqwash` | — | unknown subcommand | no generic per-file entry | ambiguous generic entry | entry script missing |
| `tools/cpu_guard.sh` | — | — | — | — | — (exit code = wrapped command's) |

## 6. `tools/cpu_guard.sh` v3 (Dynamic Ladder-Queue Thermal Protocol)

Every compile goes through cpu_guard (thermal-overload protection, criteria first):

```
bash tools/cpu_guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct]
                        [-ThrottleFloor 90] [-ThermalMaxWait 3600] [-Reg <dir>] -- <command...>
```

- **Ladder queue**: FIFO registration on entry; position <Front (default 2) = FRONT
  tier, nice 0 full speed; <Front+Mid (default +2) = MID tier, nice 10; further back
  = queued polling, demoted to BACK (`taskpolicy -b nice -n 19`) after
  `MaxWaitSec` (900 s) so nothing starves.
- **Thermal gate** (all tiers, never ABORTs on hardware reality): when
  `pmset -g therm` reports `CPU_Speed_Limit` < `ThrottleFloor` (90%), cool down in a
  polling loop; at `ThermalMaxWait` (3600 s) warn and proceed degraded.
- **`-Direct`**: probe bypass — no queue, no registration, immediate background nice 19
  execution (protects small probes from starvation).
- **Dual-lane `-Reg <dir>`**: separate registration tables; two lanes queue
  independently; default behavior unchanged when `-Reg` is omitted.
- **Stale-slot cleanup**: registration slots are validated with `kill -0` and reaped;
  exit code = wrapped command's exit code.

## 7. Planned Component Design Targets (canonical: README "Seven Canonical Steps" & "W13")

- **7 canonical wash steps (unskippable)**: ①cp source into sandbox (write isolation)
  → ②three-state triage (true-wash / bridge-retain = exception registry / UNCERTAIN =
  probe-first) → ③canonical face-mapping wash (Qlt→QltT / Qle→QleT' / `==`→QeqT /
  bare `=`→Id+id_cong / nat≤→NatLe) → ④compile verification (RC=0 / magic
  `436f712100015ff4` / vo newer than v / PA Closed / coqchk Axioms:none) → ⑤R4
  three-source conjunction (bare full-extraction magic=0 + probe dual-face magic=0 +
  five-pattern grep=0) → ⑥gate7 English adaptation (CJK→0 + five-field header 30-line
  cap) → ⑦N=N name-table assertion (`mac_stmt_names.py` ordinal full-equality) + freeze md5. Any
  failure = honest WIP, no
  green-washing.
- **W13 four mechanisms**: ① `==`-statement rewrite/ring/reflexivity structurally
  unusable on QeqT(Id) goals → flip back via `qeq_imp_qeqT` first; ② keyed-matching
  instantiation (supply-side parameter must take the actual goal shape); ③
  premiss-carrying lemma consumption (assert-ification + dual-shore bridge); ④
  cross-line Require topology leak (statement-level multi-line awareness + driver
  idempotent resume).

## 8. Related Documents

- Chinese mirror: [`docs/zh/architecture.md`](../zh/architecture.md)
- Contributing workflow / code style / test requirements / cpu_guard usage:
  [`../CONTRIBUTING.md`](../../CONTRIBUTING.md)
- Full-chain demo: [`../../examples/README.md`](../../examples/README.md)
- Test suite: [`../../tests/README.md`](../../tests/README.md) (`bash tests/run_tests.sh`)
- Project overview: [`../../README.md`](../../README.md)
