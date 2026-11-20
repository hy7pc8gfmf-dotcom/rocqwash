# rocqwash CAPABILITY-INDEX (Tool Capability Contract Surface)

Purpose.  The single contract surface for rocqwash tool capability: one entry
  per tool, transcribed line-by-line from the same-batch word-face census, so
  that callers (workflow tickets, automation tasks, a future MCP layer) invoke
  straight from the entry line instead of hand-writing paths and arguments.
Interface.  Documentation face; each entry carries seven fields: path, one-line
  purpose, invocation form (restored from the argparse word face), a copyable
  example, imports, network face, and the SKIP face.
Dependencies.  Transcribed from the census outputs `census.md` and
  `census-tools.json` (27 `.py` files under `tools/`, AST word-face level) and
  the AST-level flag-shape table `flag-shape.json`; invocation prefixes follow
  each tool's documented form.
Evidence.  Entry lines are transcribed verbatim from the census outputs; the
  light-probe ledger in section 4 records rc and output face for the 8 probed
  items; the transcription-fidelity checks in section 5 record the line-count
  reconciliation.
Exit-codes.  None of its own; exit-code semantics are runtime evidence not
  measured at cast time (census boundary, section 3.1), described per entry as
  documented, with measured rc values for the 8 probed items.


Version anchor: `0765d671a63193430de86faf3a9790f2d8a086a0`, measured locally on November 20, 2026 (`git rev-parse HEAD` on the working tree; the remote `main` equal at this sha). The census re-scan was executed at this anchor: the census outputs `census.md`, `census-tools.json`, and `flag-shape.json` (59 `.py` files) now sit in this directory beside the builder `census_tools_build.py`. Prior anchors stay on record: the census cast at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85` (November 14, 2026) and the construction-base annotation `d6d0ec75747edee957e334d1ff9391707cb39f21` (November 15, 2026); the pre-regen §1/§2 transcribed lines remain their cast-time word-face facts, and entries added since carry their own integration notes (section 2).

## Four-Number Cross-Table (the regen generation, November 20, 2026)

The four standing counts of the tool face, each bound to its own time point and basis; none is derivable from another (the caller note of `docs/census.md` section 5 applies verbatim). Source of the November 20, 2026 readings: the count cross-table deliverable of the regen work stream (`D:/ComplexAnalysis/attn/_rqw_mcp_regen_20261120/count-table.md`, measured at this anchor) and `docs/census.md` section 5.

| Face | Count | Anchor | Time point | Measurement |
|---|---|---|---|---|
| Census-time cast | 27 | `5829f6d` | November 14, 2026 | transcribed record (the November 14, 2026 census; kept as history, not re-measured) |
| Census re-scan scope | 59 | `0765d671` | November 20, 2026 | `census-tools.json` meta `py_files_censused` = 59; `docs/census.md` section 5, measured |
| INDEX entries | 54 | `0765d671` | November 20, 2026, after this integration increment | `command grep -c "^### tools/" docs/CAPABILITY-INDEX.md` = 54; the pre-integration reading was 44 (count cross-table section 2 row 2; `docs/census.md` section 5) |
| Tree `.py` files | 59 | `0765d671` | November 20, 2026 | `ls tools/*.py \| wc -l` = 59 (count cross-table section 2 row 3); the working tree equals the committed face |
| MCP roster | 25 | `0765d671` | November 20, 2026 | `TOOL_SPECS` in `tools/mcp_server.py` = 25 and `EXPECTED_TOOLS` in `tests/t_mcp_face.py` = 25, set-equal (count cross-table sections 2 and 4); unchanged since the November 15, 2026 integration generation |

Delta note, current at this increment: tree 59 against index 54 leaves five `.py` files without an index entry (`exp_port.py`, `gap_cluster.py`, `jargon_map_sync.py`, `mcp_server.py`, `periscope.py`); the ten files this increment entered are the missing-entries supplement's scope, and the remaining five await their own lanes (`mcp_server.py` deliberately carries no hand-written entry per section 6). Index entries pointing at absent files: 0.

## 0. Positioning and How to Read


**Positioning**: this file is the single contract surface for rocqwash tool capability. One entry per tool, transcribed line-by-line from the same-batch word-face census; callers (workflow tickets, automation tasks, a future MCP layer) invoke straight from the entry line instead of hand-writing paths and arguments. Each entry carries seven fields: path, one-line purpose, invocation form (restored from the argparse word face), a copyable example, imports, network face, and the SKIP face.

When invoking from an entry, record the HEAD sha used as the version anchor; after HEAD advances, re-check the entry face following the sync duty.

**Evidence and boundary**:
- Per-item lines are transcribed verbatim from the census outputs `census.md` and machine-readable `census-tools.json` (AST word-face level; run under `python -I` with zero network; the census executed, imported, and spawned no tool). The census outputs in this directory are the re-scan generation: 59 `.py` files under `tools/`, re-scanned November 20, 2026 at HEAD `0765d671a63193430de86faf3a9790f2d8a086a0`. The first cast (27 `.py` files, census time November 14, 2026 at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`) stays on record as the source generation of the original transcribed entries; entries cast after a census carry their own integration notes (section 2), and the ten regen-generation entries carry the missing-entries supplement's measured faces with that supplement's own negative-finding boundary.
- Example lines are restored from the argparse/usage word faces (AST-level flag-shape table `flag-shape.json`; classification rule: `action=store_true/store_false/count` is boolean, everything else is value-taking) with no invention: positional arguments appear as `<name>` placeholders, value-taking flags as `--flag <value>`, boolean flags copyable as written. An example shows the call form, not a statement of which options are required; the invocation line carries the full flag face.
- Invocation prefixes follow each tool's documented form (`python` or `python3`); use the interpreter available in the calling environment.
- Exit-code semantics are runtime evidence not measured at cast time (census boundary §1); the light-probe ledger in §4 records rc and output face for the 8 measured items; the remaining items await the later verification step.
- Non-`.py` faces in `tools/` sit outside the census scope, recorded as metadata; their contract faces are not in this index. At the first cast, `cpu_guard.sh` (4,053 B) was the only such file; at the re-scan (November 20, 2026) the metadata face is `cpu_guard.sh` (4,581 B), `taxonomy.json` (3,560 B), `vacgen_env_note.md` (5,639 B), twelve `.py.zh.md` archive files, and `__pycache__/` (census section 1 boundary).

## 1. Summary Table

| File | Bytes | Lines | Doc | Arg | Pos/Opt | Network face (word) | Env markers | Basis |
|---|---|---|---|---|---|---|---|---|
| _abl1_4b_compile.py | 3,451 | 80 | Y | N | 0/0 | zero | ocaml(15) | usage |
| _gen_fin_mac.py | 9,001 | 166 | Y | Y | 0/6 | zero | ocaml(7), coq(12), thermal(3), runner(1) | arg |
| _http_backoff.py | 5,082 | 110 | Y | N | 0/0 | zero | none | usage |
| ai_flavor.py | 20,687 | 481 | Y | Y | 0/5 | zero | none | arg |
| ai_flavor_apply.py | 54,124 | 1,299 | Y | Y | 0/7 | urllib.request | env | arg |
| auto_merge.py | 28,831 | 636 | Y | Y | 0/10 | zero | none | arg |
| auto_round.py | 84,108 | 1,898 | Y | Y | 2/22 | zero | none | arg |
| axiom_guard.py | 22,281 | 504 | Y | Y | 0/7 | zero | env (ROCWASH_ROCQ, ROCWASH_COQCHK) | arg |
| b_gate_audit.py | 21,052 | 498 | Y | Y | 0/1 | zero | none | arg |
| i18n_pipeline.py | 80,939 | 1,939 | Y | Y | 0/4 | zero | env | arg |
| i18n_translate.py | 45,371 | 1,301 | Y | Y | 0/13 | urllib.request | env | arg |
| i18n_verify.py | 47,407 | 1,030 | Y | Y | 0/13 | zero | none | arg |
| jargon_apply.py | 41,610 | 967 | Y | Y | 0/10 | zero | none | arg |
| lean_sweep.py | 57,056 | 1,089 | Y | Y | 0/16 | zero | lean(23), thermal(1) | arg |
| learning_feedback.py | 35,331 | 740 | Y | Y | 0/1 | zero | none | arg |
| termbase.py | 22,477 | 520 | Y | Y | 0/5 | zero | none | arg |
| baseline_diff.py | 41,200 | 800 | Y | Y | 2/2 | zero | none | arg |
| bus_feeder.py | 33,027 | 749 | Y | Y | 1/4 | zero | none | arg |
| calibration_ledger.py | 32,404 | 747 | Y | Y | 0/12 | zero | env (ROCWASH_EXPERIENCE_DIR) | arg |
| chain_graph.py | 14,854 | 335 | Y | Y | 1/3 | zero | none | arg |
| ci_triage.py | 121,218 | 2,194 | Y | Y | 0/11 | urllib.request | coq(109), win(4), runner(2) | arg |
| contrib_intake.py | 62,133 | 1,365 | Y | Y | 0/11 | git: clone | coq(23) | arg |
| cw_doctor.py | 58,988 | 1,176 | Y | Y | 0/15 | zero | env, coq(5), dyld(31), thermal(5) | arg |
| cw_sentinel.py | 119,753 | 2,168 | Y | Y | 0/23 | http.client, socket, urllib.request | coq(1), thermal(3) | arg |
| doc_lint.py | 61,486 | 1,291 | Y | Y | 0/3 | zero | none | arg |
| evolution_dashboard.py | 38,249 | 811 | Y | Y | 0/8 | zero | none | arg |
| evolve.py | 90,890 | 1,819 | Y | Y | 0/19 | zero | coq(7) | arg |
| flaky_guard.py | 49,683 | 1,173 | Y | Y | 0/18 | zero | env (ROCWASH_ADVISORY_ROSTER, ROCWASH_PY, ROCWASH_TESTS_EXCLUDE, ROCWASH_TESTS_ONLY) | arg |
| gap_cluster.py | 30,859 | 657 | Y | Y | 0/4 | zero | none | arg |
| ledger_sync.py | 26,938 | 549 | Y | Y | 0/5 | zero | none | arg |
| net_probe.py | 19,076 | 412 | Y | Y | 0/7 | socket, urllib.request | none (network is its subject) | arg |
| netname_normalize.py | 15,059 | 332 | Y | Y | 0/4 | zero | none | arg |
| norm_lint.py | 32,256 | 823 | Y | Y | 0/8 | zero | none | arg |
| pin_repair.py | 38,338 | 899 | Y | Y | 0/4 | zero | none | arg |
| pushci.py | 108,070 | 2,134 | Y | Y | 0/21 | urllib.request, git: push+ls-remote | env, coq(11) | arg |
| red_dispatch.py | 48,353 | 935 | Y | Y | 0/10 | zero | coq(5), thermal(1) | arg |
| registry_audit.py | 51,476 | 1,054 | Y | Y | 0/11 | zero | coq(12) | arg |
| registry_fix.py | 60,064 | 1,161 | Y | Y | 0/8 | zero | env, coq(5) | arg |
| registry_regen.py | 61,590 | 1,346 | Y | Y | 0/15 | zero | coq(37) | arg |
| registry_union.py | 42,872 | 931 | Y | Y | 0/14 | zero | coq(4) | arg |
| render_events.py | 26,635 | 547 | Y | Y | 0/5 | zero | none | arg |
| repair_scope.py | 78,951 | 1,856 | Y | Y | 0/12 | zero | thermal(1) | arg |
| repair_weekly.py | 34,095 | 769 | Y | Y | 0/13 | zero | none | arg |
| roster_resync.py | 27,142 | 619 | Y | Y | 0/4 | zero | none | arg |
| row_render.py | 66,691 | 1,867 | Y | Y | 0/16 | urllib.request | lean(15) | arg |
| scheduler_lite.py | 29,088 | 695 | Y | Y | 1/11 | zero | none | arg |
| select_audit.py | 32,930 | 654 | Y | Y | 0/6 | zero | ocaml/opam token(2) | arg |
| selfevolve_round.py | 31,385 | 732 | Y | Y | 0/4 | urllib.request | env | arg |
| symbiosis_bus.py | 39,500 | 878 | Y | Y | 1/9 | zero | none | arg |
| toolchain_dyld_doctor.py | 23,777 | 492 | Y | Y | 0/6 | zero | env, coq(32), dyld(39), thermal(5) | arg |
| unclog.py | 103,325 | 1,943 | Y | Y | 0/30 | zero | coq(5), thermal(2) | arg |
| uplink.py | 59,383 | 1,392 | Y | Y | 1/15 | zero | none | arg |
| vacgen.py | 122,111 | 2,625 | Y | Y | 0/20 | zero | lean(64), thermal(3) | arg |
| verdict_diff.py | 33,797 | 668 | Y | Y | 0/6 | zero | none | arg |
| wash_shape.py | 110,172 | 2,285 | Y | Y | 0/16 | zero | env, coq(6) | arg |


Legend: Doc = module docstring present; Arg = argparse import present; Pos/Opt = positional/optional flag counts; Network face = three-channel word-face reading (zero = no hit in any channel); Env markers = marker families with word-face hit counts (ocaml = ocamlc/ocamldep/opam; coq = coqc/coqtop/coqchk/coqdep/rocq family; thermal = cpu_guard/_THERMAL family; runner = self-hosted/actions-runner; win = Windows guard wording; env = ROCWASH_* environment variables; dyld = macOS dyld tooling face; lean = lake/mathlib/Lean/elan family). Env markers are word-face hits, not proof of runtime requirements (boundary in §3.1). Basis = invocation reconstruction source (arg = argparse; usage = usage string).

## 2. Per-Item Contract Lines

55 items in filename order; each entry transcribes the census verbatim; the only added line is the Example line.

Integration note (the engine-body ticket, at integration): the seven engine-body entries are inserted in filename order, transcribed from docs/engine-body-capabilities.md (the lane-8 draft) and re-verified live by the integration agent per file (--selftest); the Status line is this batch's added line (declared single-line addition); the section 1 rows carry live measurements on the integration tree; the aggregates below stay the census-time word-face facts.

Integration note (the symbiosis ticket, at integration): the symbiosis_bus entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python tools/symbiosis_bus.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on the integration tree; the Status line is this batch's added line (declared single-line addition). The `symbiosis_status` MCP face in `tests/t_mcp_face.py` (the 25-capability roster) hangs its contract on this entry. `tools/uplink.py` sits on disk untracked (the uplink ticket's deliverable); its census-grade entry awaits that lane's own integration increment and is deliberately not hand-written here.

Integration note (the uplink ticket, at integration): the uplink entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python tools/uplink.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on the integration tree; the Status line is this batch's added line (declared single-line addition). The `cw.sh uplink` route (header table / usage / hint_for / case, all four places) lands with this increment; the measured `grep -c uplink cw.sh` count rides with this note as its evidence. The register file `docs/uplink-intake.jsonl` (schema `rocqwash-uplink/1`, comment-header form, zero real rows) and `tests/t_uplink_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) hang their contracts on this entry. `docs/uplink_sop.md` is the operation manual.

Integration note (the evolution-dashboard ticket, at integration): the evolution_dashboard entry below is inserted in filename order; the purpose, invocation, and example lines are transcribed from this tree's live `python -I tools/evolution_dashboard.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the Status line is this batch's added line (declared single-line addition). The `cw.sh evolution-dashboard` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 47 to 48 under the same registered-tool precedent. `tests/t_evolution_dashboard_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) hangs its contract on this entry. Current-tree state: `docs/round-ledger.jsonl` and `docs/vacgen-reports/` are absent, which is a data state inside the tool's contract (reported as present=false); the curve goes live once the first round row and the first vacgen report land.

Integration note (the bus-feeder ticket, at integration): the bus_feeder entry below is inserted in filename order (between baseline_diff and chain_graph); the purpose, invocation, and example lines are transcribed from this tree's live `py -I -B tools/bus_feeder.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the Status line is this batch's added line (declared single-line addition). The `cw.sh bus-feeder` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 48 to 49 under the same registered-tool precedent (under concurrent writers, the 47 to 48 bump was landed first by the evolution-dashboard lane). `tests/t_bus_feeder_shape.py` (run directly, deliberately not rostered in tests/run_tests.sh: the roster count is coupled to the README count lines, whose rewrite belongs to the work stream holding that authorization) and `docs/symbiosis_sop.md` section 6 (the feed-face contract increment) hang their contracts on this entry. The recognition-set divergence is on record: the `tools/gap_cluster.py` category token escape `\u5748` (U+5748) differs in code point from the token its own producer emits (U+5751, `tools/vacgen.py` line 2470) and reads only the `category` key spelling, so the feeder pins U+5751 itself and reads both key spellings (the divergence is documented in that tool's extended contract comment and in the SOP section boundary line); the gap_cluster body is outside this ticket's write face.

Integration note (the substrate compile-loop and axiom-guard ticket, at integration): the axiom_guard entry below is inserted in filename order (between auto_round and i18n_pipeline); the purpose, invocation, and example lines are transcribed from this tree's live `py -B tools/axiom_guard.py --help` word face and the module docstring (not a census product; this entry is transcribed from the live word face); the section 1 row carries live measurements on this tree; the Status line is this batch's added line (declared single-line addition). The `cw.sh axiom-guard` route (header table / usage / hint_for / case, all four places) lands with this increment, together with the `DEFAULT_HELP_CAP` bump 49 to 50 under the same registered-tool precedent. This tool is the package's axiom guard (the owner of the repo's most serious misalignment named in audit report section 3.2): compile tri-classification (compile-ok / compile-broken debt register / skip-no-toolchain) plus two-level detection on compile-ok files (light face = per-theorem Print Assumptions census; heavy face = coqchk -o kernel recheck as the authority; the token-quarantine face is not adopted per the gate5 precedent: quarantine only, never a verdict). `ROCWASH_ROCQ` / `ROCWASH_COQCHK` environment gating (unconfigured = rc 111 honest skip). Write faces: the caller-named `--out` report volume plus a private temp workdir (the .vo output face is temp-only; the repository tree gains zero bytes); the byte-identical double run is measured and on record. Two destructive-matrix rows (this tool's compile-leg write face and the cure_applier compile-leg write face) hang on this entry as `tests/test_destructive_matrix.py` additions of the same batch.

Integration note (the recursive three-gap batch, at cast): the b_gate_audit, learning_feedback, and pin_repair entries below are inserted in filename order at their alphabetical slots (b_gate_audit between ai_flavor_apply and baseline_diff; learning_feedback between jargon_apply and ledger_sync; pin_repair between norm_lint and pushci); the three tools are this batch's parallel deliverables and the entries are cast from the batch contract faces under the contract-first rule (the entry text rides the contract, not a live tool face, and does not wait for the tool lanes); each entry carries a Status line as this batch's added line (declared single-line addition). The section 1 rows carry the same contract-face declarations (Doc/Arg/Pos-Opt/Network face/Env markers/Basis from the contract-mandated faces); the Bytes and Lines cells stay `pending` until the tool lanes' own integration increments carry the on-disk measurements. The section header count line above is advanced to the live entry count per the live-count rule; the census-scope count (27 `.py` files at census time), the aggregates at the end of this section, and the section 5 fidelity line stay the records of their own cast times and are not rewritten.

Integration note (the A-batch closed loop, at cast): the selfevolve_round entry below is inserted in filename order (between select_audit and symbiosis_bus); the tool predates this increment on disk (the standing cron round, the cw.sh route selfevolve-round) but carried no index entry at the cast base, so the entry is cast here from the A-batch contract faces under the contract-first rule (the entry text rides the contract, not a live --help face: the tool reads its flags from sys.argv, carries no argparse, and its live flag face grows by the tool lane's own increment); the section 1 row carries the contract-face declarations (Doc Y; Arg N, no argparse import on the tree word face; Pos/Opt 0/2, the boolean flags --dry-run and --pin-repair; Network face from the word face, urllib.request plus the git push token; Env markers: env; Basis: usage), and the Bytes and Lines cells stay `pending` until the tool lane's own integration increment carries the on-disk measurements. The section header count line is advanced to the live entry count per the live-count rule (43 to 44); the census-scope count, the aggregates at the end of this section, and the section 5 fidelity line stay the records of their own cast times and are not rewritten.

Integration note (the four-[contracted] pending-slot backfill, at integration): the pending Bytes and Lines cells of the four [contracted] section 1 rows (b_gate_audit, learning_feedback, pin_repair, selfevolve_round) are filled from the four-tool measurement of the regen work stream (read-only AST probe under `python -I` plus `wc` cross-check plus `--help` light probes, rc=0 on all four, at HEAD `0765d671` on November 20, 2026; all four files clean against HEAD, so the values are committed values). The selfevolve_round row advances three cells to the measured face per that measurement's divergence table (Arg N to Y, Basis usage to arg, Pos/Opt 0/2 to 0/4) and its Invocation line advances to the measured `--help` face; the A-batch note above stays as written for its own time. The four entries' itemized import slots are filled with the measured lists. Three divergence readings stay deliberately unintegrated, riding the tool lane's own re-check: the contract SKIP face's `ROCQWASH_REPAIR_PLAN_LEDGER` token is absent from the current selfevolve_round word face (the section 1 env cell keeps its cast-time reading); the live learning_feedback `--help` face says seven selftest vectors against the four-vector wording of the entry line; and the measured `git push` subprocess token on selfevolve_round is recorded in the measurement and not carried into the section 1 network cell.

Integration note (the missing-entries supplement, at integration): the ten entries below are inserted in filename order (auto_merge between ai_flavor_apply and b_gate_audit; calibration_ledger between bus_feeder and chain_graph; flaky_guard between axiom_guard and i18n_pipeline; lean_sweep between jargon_apply and learning_feedback; repair_scope, repair_weekly, roster_resync, and row_render between render_events and select_audit; scheduler_lite between row_render and select_audit; verdict_diff between vacgen and wash_shape); the entries are transcribed verbatim from the missing-entries supplement of the regen work stream, cast from live `--help` word faces (rc=0 on all ten) plus module docstrings at HEAD `0765d671` on November 20, 2026 (not census products; the supplement's negative-finding boundary governs); each entry's Status line is this batch's added line (declared single-line addition), and the supplement's phrase "the INDEX integration increment rides the census lane's own re-run" reads as this integration, the same re-scan generation that lands the census trio in this directory. The ten section 1 rows carry the supplement's live measurements; the section header count line above is advanced to the live entry count per the live-count rule (44 to 54); the census-scope count, the aggregates at the end of this section, and the section 5 fidelity line stay the records of their own cast times and are not rewritten.

Integration note (the MCP roster-expansion work stream 1, the M1 ticket, at integration): the MCP roster grows 25 to 31 with six new faces (`termbase`, `verdict_diff`, `learning_feedback`, `b_gate_audit`, `evolution_dashboard`, `gap_cluster` in `tools/mcp_server.py`, `tests/t_mcp_face.py` EXPECTED_TOOLS, and `docs/mcp.md` section 3), and every one of the six hangs its spec contract on this file's section 2 entry lines. Five of the six entries already stood in this section at the ticket's baseline `c48a548a` (termbase, verdict_diff, learning_feedback, b_gate_audit, evolution_dashboard); the one entry this increment adds is the gap_cluster entry below, inserted in filename order (between flaky_guard and i18n_pipeline), transcribed from the live `python -I tools/gap_cluster.py --help` word face (rc=0, measured November 21, 2026) and the module docstring at HEAD `c48a548a` (not a census product; the same supplement-era negative-finding boundary governs), and its Status line is this batch's added line (declared single-line addition). The gap_cluster section 1 row carries this session's live measurements (Bytes/Lines via `wc`, Doc/Arg/Pos-Opt from the argparse word face, the network and environment cells from the word-face scan: zero transport-class import faces, zero `ROCWASH_*` literals). The section header count line above is advanced to the live entry count per the live-count rule (54 to 55); the census-scope count, the aggregates at the end of this section, the section 5 fidelity line, and the cross-table rows above stay the records of their own cast times and are not rewritten.

### tools/_abl1_4b_compile.py
- Purpose: Internal helper: incremental OCaml compilation of an extracted module directory in dependency fixpoint order (interface files first), optionally linking and running a driver; exits loudly if `ocamlc`/`ocamldep` are absent from PATH (`_abl1_4b_compile.py:12-20`).
- Invocation: `python3 _abl1_4b_compile.py <extract_dir> [driver.ml]` (restored from the usage string; this file has no argparse)
- Example: `python3 _abl1_4b_compile.py <extract_dir>`
- Imports: os, re, shutil, subprocess, sys (all standard library)
- Network face: zero (three channels, zero hits)
- SKIP face: needs the OCaml toolchain (ocaml/ocamldep word face, 15 hits); the caller supplies its own opam environment

### tools/_gen_fin_mac.py
- Purpose: Internal helper: renders a probe template into a target-environment form (source module, module name, world name, output directory, and requires list all parameterized).
- Invocation: `python tools/_gen_fin_mac.py [--source] [--module] [--world] [--world-name] [--outdir] [--requires]`
- Example: `python tools/_gen_fin_mac.py --source <value>`
- Imports: argparse, io, json, os, sys + in-repo `names/mac_stmt_names.py` (cross-directory reference via sys.path injection)
- Network face: zero
- SKIP face: ocaml/opam word face (7), coq family word face (12), cpu_guard word face (3), actions-runner word face (1); the generated targets face a specific compile environment

### tools/_http_backoff.py
- Purpose: Internal shared helper: pure-function HTTP rate-limit backoff with a frozen-vector selftest, no transport and no IO; imported by ci_triage, cw_sentinel, and pushci (word face).
- Invocation: `python3 tools/_http_backoff.py --selftest` (restored from the usage string; this file has no argparse)
- Example: `python3 tools/_http_backoff.py --selftest`
- Imports: sys (single item)
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/ai_flavor.py
- Status: [live](engine-body ticket lane 1 deliverable, integrated at the merge, the E1 detection body)
- Purpose: Wording detection body: a 36-face battery (10 zh, 15 en stems, 8 sentence, 3 paragraph-initial) plus a separate em-dash battery (U+2014 count, target 0); the word map is read-only from `seeds/ai_flavor/word-map.json` (regex literals transcribed verbatim); hits are data, not errors; pure exports `detect_text(text, word_map)` and `load_word_map(path)`.
- Invocation: `python -I tools/ai_flavor.py --file <p> [--json <out>]` / `--tree <dir>` (*.py *.sh *.md *.json *.ts) / `--selftest`
- Example: `python -I tools/ai_flavor.py --file docs/report.md --json out/ai-flavor-report.json`
- Imports: argparse, json, os, re, sys (all standard library)
- Network face: zero
- SKIP face: report-first, zero writes; exit 1 = hits present (data); the em-dash target covers the whole scope including this file itself; the `--selftest` self-exemption covers only the wording battery (data-exemption rule), not the em-dash battery

### tools/ai_flavor_apply.py
- Status: [live](engine-body ticket lane 3 deliverable, integrated at the merge, the E1 apply face)
- Purpose: Advisory apply face: all writes are advisory and gated behind the write gate (`--apply-handoff` / `--provider http`); rewrites always go through the rewrite provider (the handoff form is zero-network by default: `--emit-handoff` emits the segment package, and after backfill `--apply-handoff` validates and writes; the http leg is default-deny); the 10 zh ban faces are never machine-written, stem faces take the register-neutral plain form, and sentence faces are deleted or restated; the budget cap is one round per target file per class (`--state`, default `<file>.aiflavor-state.json` beside the target file); after rewriting, the detection re-run must reach residue zero to gate GREEN.
- Invocation: `python -I tools/ai_flavor_apply.py --file <p> [--json <out>] [--emit-handoff <out.jsonl> | --apply-handoff <in.jsonl> --state <p>] [--provider handoff|http]`
- Example: `python -I tools/ai_flavor_apply.py --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json`
- Imports: argparse, importlib.util, io, json, os, re, sys, tempfile, time, urllib.request + in-repo `tools/ai_flavor.py` (same directory)
- Network face: handoff face zero; http leg non-zero (default-deny: `ROCQWASH_MCP_ALLOW_NET=1` plus `ROCQWASH_LLM_ENDPOINT` / `ROCQWASH_LLM_MODEL` / `ROCQWASH_LLM_KEY`: missing any of the three refuses loudly and names the missing item; each call writes a NETRED ledger line including failures; credential values never hit disk or logs)
- SKIP face: the 10 zh faces are disposition=human, never machine-written; handoff ingest refuses fail-loud (`rejected[]` reported as-is); without model configuration the handoff form is fully functional (the model site plays the executing-agent role)

### tools/auto_merge.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/auto_merge.py --help` word face (rc=0) and the module docstring, `auto_merge.py:3-30`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: X5 auto-merge gate judge and safety rail: judges one pull request against the six-verdict mergeability enum (merge-ok / hold-red / hold-conflict / already-landed / superseded-landed-elsewhere / escalate-unknown) from caller-gathered facts (schema `rocqwash-automerge-facts/1`; the CI verdict, mergeability, and containment signals are caller-gathered via `git rev-list base...head` plus a tree-level containment check), then runs the safety rail: only merge-ok with a `supply/*` head branch is auto-execution eligible, under a daily budget cap (default 3) against the append-only merge ledger (default `docs/auto-merge-ledger.jsonl`); post-merge red prescribes revert (content) / rerun window (transient) / escalation (unknown); dry run by default.
- Invocation: `python3 tools/auto_merge.py --facts F.json [--head-branch BR] [--allow-prefix P] [--daily-cap N] [--ledger P] [--merge-sha SHA] [--post-merge FAM] [--apply] [--json OUT] | --selftest` (`--post-merge` takes one of the four post-merge families green / transient / content / unrecognized and runs the revert arc against the ledger instead of the judge)
- Example: `python3 tools/auto_merge.py --facts <value> --json <value>`
- Imports: argparse, json, os, shutil, sys, tempfile, time (all standard library; the doc face states zero third-party imports and no subprocess)
- Network face: zero (no transport-class imports, no subprocess; the CI verdict, mergeability, and containment inputs ride the caller-gathered facts file, so the network face belongs to the caller, not this judge)
- SKIP face: exit 0 completed (verdicts are data); 1 refused (rail refusal or duplicate); 2 usage; 9 missing or malformed input; `--selftest` 0 all vectors pass / 2 assertion failure (frozen vectors: calibration samples S-1..S-5, the unrecognized-family escalation, ordering pins, whitelist both ways, budget cap, dry-run zero-write, duplicate refusals, the revert arc four families, byte-identical reruns, CLI codes); the only write faces are the `--apply` ledger append and the `--json` report; schemas `rocqwash-automerge-facts/1` (facts) and `rocqwash-automerge/1` (report, ledger)

### tools/b_gate_audit.py
- Status: [contracted](B-gate audit deliverable, cast from the batch contract face under the contract-first parallel rule; the [live] marker rides the tool lane's own integration increment)
- Purpose: B-level generalization threshold audit: per class, counts the instances (admissions occurrences in the round ledger, deduplicated within one round) and the distinct admitting rounds, and issues a readiness verdict against the threshold of 3 instances with at least 1 admitted round each; a class is ready when instances >= 3 and rounds >= 1; writes `docs/b-gate-audit.json` (schema `rocqwash.b-gate-audit/1`) carrying the threshold, the per-class readings (`class`/`instances`/`rounds`/`ready`/`gap`), the ready-class list, `verdict`, and `remaining_to_b`; an empty record reads verdict `not-ready` with remaining 3, reported as data and never padded.
- Invocation: `python -I tools/b_gate_audit.py [--selftest]` (the default run reads the round ledger, the round state, and the taxonomy word table, and writes the audit file plus a stdout summary)
- Example: `python -I tools/b_gate_audit.py --selftest`
- Imports: standard library only per the contract face (argparse CLI, JSON reading, tempfile fixtures); the itemized import list, measured at HEAD `0765d671` (the four-tool backfill): argparse, contextlib, io, json, os, sys, tempfile at module level, no function-local imports, zero in-repo imports
- Network face: zero (no network by design per the contract face)
- SKIP face: exit 0 = readings are data (a `not-ready` verdict on empty or below-threshold classes is a data state, never padded); a bad ledger row or a missing record lands in an `error` field and the stdout summary fails loud, continuing rather than silently skipping; the only write face is `docs/b-gate-audit.json`; `--selftest` runs four offline vectors on tempfile fixtures (a threshold-passing class, a single-instance class, an empty record, bad-row tolerance), zero network, zero touches of the real records

### tools/baseline_diff.py
- Purpose: Compares two baseline files and reports additions and removals (JSON and markdown output).
- Invocation: `python tools/baseline_diff.py <old> <new> [--json] [--md]`
- Example: `python tools/baseline_diff.py <old> <new> --json <value>`
- Imports: argparse, io, json, os, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/bus_feeder.py
- Status: [live](gap-ledger feeder ticket deliverable, integrated, added by this batch)
- Purpose: Gap-ledger feeder for symbiosis swap packages: `feed` reads one offline swap package (schema `rocqwash-symbio/1`, the export face of `tools/symbiosis_bus.py`), selects gap-class entries by the three-rule recognition set (the producer's real pitfall category token U+5751 under the top-level `category` key or the source dict's `category` / zh key spellings; the literal `TODO-SEAT` token in points or evidence; the literal `status=todo_seat` token in evidence), and lands exactly one gap row per selected entry in the gap feed ledger (default `docs/gap-feed-ledger.jsonl`, `--ledger` overrides): the row keeps the entry verbatim (schema `rocqwash-exp/1`, the fingerprint domain untouched) plus three schema increments outside the fingerprint domain (`correlationId` = `feed:<sourceRepo>@<anchor>`, `shapeKey` from the `tools/gap_cluster.py` family-shape key chain, `recognition` = the rule name); repeated ids and fingerprints skip loudly with zero writes (idempotent, byte-identical replay); `status` reports row counts, routes, the shape-to-rows mapping, and per-package present/new readings. Ids and time points ride entry content, never a clock; the gap feed ledger is the only write face; zero network by design.
- Invocation: `python tools/bus_feeder.py [--selftest] {feed,status} --swap SWAP.jsonl [--ledger P] [--dry-run]` (`--swap` exactly one on the feed face, repeatable on the status face)
- Example: `python tools/bus_feeder.py feed --swap docs/symbiosis-swap-round1.jsonl --ledger docs/gap-feed-ledger.jsonl --dry-run`
- Imports: argparse, json, os, sys + in-repo `tools/symbiosis_bus.py` (same directory; swap-package reading, envelope validation, shared exit-code exceptions, canonical line form) + in-repo `tools/gap_cluster.py` (family-shape key chain and shape abstraction)
- Network face: zero (three channels, zero hits; no network by design)
- SKIP face: exit 0 = readings are data (skip rows / zero hits / zero gap rows all reported as-is); 1 = selftest vector group failing; 2 = usage or IO; 9 = missing or damaged input (swap package / ledger row bad JSON, envelope drift, fingerprint distortion) with zero writes; the recognition-set divergence (gap_cluster category token code point U+5748 vs the producer's U+5751) is on record in that tool's extended contract comment and the `docs/symbiosis_sop.md` section-6 boundary line; real-sample dry-run reading `would-feed=1 nonGap=26 total=27`

### tools/calibration_ledger.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/calibration_ledger.py --help` word face (rc=0) and the module docstring, `calibration_ledger.py:3-32`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: W4 calibration ledger for the experience ledger: pairs each per-row predicted confidence in a vacgen v2 report with the measured compile-leg rc face and appends one calibration entry per paired row into `docs/exp-ledger.jsonl` (schema `rocqwash-exp/1`, carrying `correlationId` = the report id) through the experience-bus port's idempotent seen set, so a rerun writes zero new rows; rows whose gap reaches the signal threshold (default 0.75) form the row-rot signal face, and signals are data, not errors; the confidence scale maps HIGH to 1.0 and MID to 0.5, the measured side is 1.0 pass / 0.0 fail, and the fingerprint helper stays byte-identical to `tools/exp_port.py` (the seen-set key contract).
- Invocation: `python -I tools/calibration_ledger.py --report R.json --rc-file RC.json [--leg-map LM.json] [--default-leg NAME] [--ledger P] [--batch B] [--ts TS] [--signal-threshold F] [--signals-out P] [--strict] [--dry-run] [--selftest]` (ledger resolution: `--ledger` wins, then `ROCWASH_EXPERIENCE_DIR`, then `<repo>/docs/exp-ledger.jsonl`)
- Example: `python -I tools/calibration_ledger.py --report <value> --rc-file <value> --dry-run`
- Imports: argparse, datetime, hashlib, io, json, os, shutil, sys, tempfile (all standard library; the `exp_port.py` relationship is a byte-identical-helper contract, not an import)
- Network face: zero
- SKIP face: exit 0 appended / duplicate-skip / answered (signals are data); 1 selftest red; 2 usage error; 4 `--strict` with a signal row present; 9 bad input; every rc face declares its "expected" side (green|red) so red legs are judged by declared semantics, never inferred; writes go through append-only opens (existing lines are never rewritten) plus the `--signals-out` JSON (schema `rocqwash-calibration/1`); `--dry-run` validates and reports, writes nothing

### tools/chain_graph.py
- Purpose: Merges multiple probe ledgers into a chain-root graph and a ranked list.
- Invocation: `python tools/chain_graph.py <ledgers> [--json] [--md] [--top]`
- Example: `python tools/chain_graph.py <ledgers> --json <value>`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/ci_triage.py
- Purpose: Fetches and triages logs of failing CI runs; `--offline` switches to local log input.
- Invocation: `python tools/ci_triage.py [--offline] [--repo] [--run] [--logs] [--no-dump-filter] [--netrc] [--baseline-seconds] [--baseline-step] [--timeout] [--retry-max] [--json]`
- Example: `python tools/ci_triage.py --offline <value> --logs`
- Imports: argparse, datetime, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request + in-repo `tools/_http_backoff.py`
- Network face: non-zero (urllib.request; plus a subprocess-bridge token hit)
- SKIP face: coq family word face (109, including log-parsing vocabulary), Windows guard word face (4), self-hosted runner word face (2); runs need a network window except with `--offline`

### tools/contrib_intake.py
- Purpose: Contribution intake inspector: a read-only four-gate check that issues a verdict (contribution repo, base repo, refs, paths, and jargon map all parameterized).
- Invocation: `python tools/contrib_intake.py [--contrib-repo] [--contrib-ref] [--base-repo] [--base-ref] [--paths] [--order-path] [--project-path] [--lane-prefix] [--jargon-map] [--rocq-cmd] [--json]`
- Example: `python tools/contrib_intake.py --contrib-repo <value>`
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile + in-repo `tools/registry_union.py`
- Network face: non-zero (git subprocess token face: `clone`; no transport-class imports)
- SKIP face: coq family word face (23); runs involve git clone (network)

### tools/cw_doctor.py
- Purpose: Aggregate health checker rolling up several domains (registry, source, world, worker, dyld, endpoints, guard domains all present in the flag face).
- Invocation: `python tools/cw_doctor.py [--json] [--workdir] [--registry] [--src] [--sample] [--world] [--worker] [--donor] [--endpoints] [--guard] [--guard-reg] [--guard-maxwait] [--timeout] [--rocq-cmd] [--injector]`
- Example: `python tools/cw_doctor.py --json <value>`
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero (the `--endpoints` flag is a parameter face; domain probes may be delegated externally)
- SKIP face: the `ROCWASH_ROCQWORKER` environment variable, coq family word face (5), dyld tooling face (31), cpu_guard word face (5)

### tools/cw_sentinel.py
- Purpose: Resident real-time watcher over a repo, ledgers, and the build log, emitting a JSONL event stream, with on-red hooks and a loop mode.
- Invocation: `python tools/cw_sentinel.py [--once] [--loop] [--interval] [--max-rounds] [--watch-repo] [--branch] [--watch-ledgers] [--watch-buildlog] [--state-file] [--emit] [--emit-max-bytes] [--rebuild-state] [--on-red] [--on-red-preset] [--on-red-arg] [--netrc] [--timeout] [--retry-max] [--net-retries] [--subproc-timeout] [--injector] [--sleep-scale] [--json]`
- Example: `python tools/cw_sentinel.py --interval <value> --once`
- Imports: argparse, datetime, http.client, io, json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request + in-repo `tools/_http_backoff.py`
- Network face: non-zero (http.client, socket, urllib.request; a subprocess-bridge token hit)
- SKIP face: coq family word face (1), cpu_guard word face (3); runs need a network window

### tools/doc_lint.py
- Purpose: Docs-versus-implementation consistency checker: routing tables, the face of cw.sh, and the `--help` face.
- Invocation: `python tools/doc_lint.py [--repo] [--json] [--help-cap]`
- Example: `python tools/doc_lint.py --repo <value>`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/evolution_dashboard.py
- Status: [live](self-evolution dashboard ticket deliverable, integrated, added by this batch)
- Positioning: the dashboard is the standing **a KPI aggregation read-out** face over the three ledgers; the rocqos rename candidate awaiting adjudication (rename is a candidate, not an applied change)
- Purpose: Self-evolution dashboard: aggregates the three standing accounts (the experience ledger `docs/exp-ledger.jsonl` schema `rocqwash-exp/1`, the round ledger `docs/round-ledger.jsonl` schema `rocqwash-round/1`, and the vacgen v2 report JSON file family) into one dashboard: the coverageLowerPct curve (one point per report run, ordered by content-borne time point, with a per-point TODO-SEAT delta and rise flag), the rounds conversion face (greenPct = the share of rounds with verify_rc 0; classConversionPct = admissions against classes_applied), and the thermometer reading (the latest curve point). An absent default-path account is a data state (present=false, reported as-is); an explicitly flagged absent path exits 9. The only writes are the caller-named `--json-out` / `--md-out` files; zero network by design.
- Invocation: `python -I tools/evolution_dashboard.py [--repo <root>] [--exp-ledger <p>] [--rounds <p>] [--reports <p>]... [--json-out <p>] [--md-out <p>] [--stdout markdown|json] [--selftest]`
- Example: `python -I tools/evolution_dashboard.py --json-out docs/dashboard.json --md-out docs/dashboard.md`
- Imports: argparse, json, os, shutil, sys, tempfile (all standard library)
- Network face: zero (no socket face; no network by design)
- SKIP face: exit 0 = readings are data (absent accounts / zero entries / zero rounds / zero report runs all marked as-is); 1 = selftest failing; 2 = usage error (including a bad `--stdout` value); 9 = explicitly flagged absent path / ledger row or report not JSON / no vacgen face / output write failure (zero writes); time points always ride input content, never a clock; the `--reports` directory expands to a sorted *.json sequence

### tools/evolve.py
- Purpose: Self-evolution engine v1: drafts evolution proposals from watcher events and ledger faces (sentinel, suite, and registry flag families present).
- Invocation: `python tools/evolve.py [--draft-out] [--json] [--repo-root] [--top] [--baseline] [--jargon-map] [--watch-repo] [--sentinel-state] [--sentinel-state-seed] [--sentinel-branch] [--sentinel-events] [--sentinel-injector] [--suite-ledger] [--suite-now] [--registry-git] [--registry-ref] [--git-path-order] [--git-path-project] [--registry-baseline]`
- Example: `python tools/evolve.py --draft-out <value> --suite-now`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile + in-repo `certify/frozen8.py` (cross-directory reference via sys.path injection)
- Network face: zero (git subcommand token face, local operations only: status/commit/add)
- SKIP face: coq family word face (7)

### tools/auto_round.py
- Status: [live](engine-body ticket lane 9 deliverable, integrated at the merge, the round-ledger / rollback / salvage body)
- Purpose: Auto round ledger body: dual-gear admission from `autonomy.json` (auto self-approves, gated waits for human approval; the same code path `admission_decision`), a ten-key round ledger JSONL per §7.2 (append-only), commit trailers (`Rocqwash-Round`/-Mode/Salvage-Of), a lightweight ref `refs/rocqwash/rounds/\<n\>`, rollback = archive to `refs/rocqwash/drift/` first then a single revert back to the anchor (zero reset, zero force, zero push), a salvage refinement-package round-trip, an oscillation alarm, and a soft stop on `max_unreviewed_rounds` (`--continue` releases it explicitly), plus the three query faces status/list/log.
- Invocation: `python -I tools/auto_round.py <command> [--repo-root <p>] [--autonomy <p>] [--state <p>] [--ledger <p>] [--continue]`; commands: commit / approve / anchor / rollback / salvage / merge-salvage / status / list / log; plus `--selftest`
- Example: `python -I tools/auto_round.py status --repo-root .`
- Imports: argparse, datetime, json, os, shutil, subprocess, sys, tempfile (all standard library)
- Network face: zero (the V18 anti-network self-scan: socket/urllib/ftplib/smtplib/http.client word faces are negative-scan tokens, not call faces)
- SKIP face: the git commit face runs via subprocess (alive only when git is present); every change face verifies before writing; the round ledger is append-only (rewriting historical rows is forbidden)

### tools/axiom_guard.py
- Status: [live](substrate compile-loop and axiom-guard ticket deliverable, integrated, added by this batch)
- Purpose: Repo-wide axiom guard: compiles and tri-classifies every .v file under the repo (23 files at the reference HEAD, .git excluded): compile-ok / compile-broken into the debt register with error tails / skip-no-toolchain, and judges every compile-ok file at two levels: the light face, a per-theorem Print Assumptions census (statement names extracted through a comment/string masking scanner, one batched census compile attributed in order, per-statement fallback when the marker count mismatches), and the heavy face, a coqchk -o kernel recheck whose CONTEXT SUMMARY Axioms section is the only judged section (stdlib index-relaxation sections are never judged) as the authoritative verdict. The token-quarantine face is not adopted (the gate5 precedent: quarantine only, never a verdict). The repo standard is Closed zero axioms with an empty default whitelist (`--allow-axiom` repeats); a light-face axiom fails the file (pre-screen), a heavy-face axiom or an unjudgeable heavy face fails the file (unjudgeable is not green); compile-broken files are debt, not red. Compiles run in a private temp workdir (the .vo output face is temp-only; the repository tree gains zero bytes; the source directory is mapped -Q read-only so built sibling worlds resolve); the report volume is `axiom-guard-report.json` under the caller-named `--out` (sorted inputs, no wall clock, byte-identical double run).
- Invocation: `python3 tools/axiom_guard.py --repo <dir> [--out <dir>] [--rocq <bin>] [--coqchk <bin>] [--allow-axiom <name>]... [--timeout <sec>] [--keep]`
- Example: `ROCWASH_ROCQ=/path/rocq ROCWASH_COQCHK=/path/coqchk python3 tools/axiom_guard.py --repo . --out evid/t0-2`
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (all standard library) + external binaries rocq / coqchk (provided by flag or env; missing either = skip, never simulated)
- Network face: zero (subprocesses are local rocq/coqchk compile and kernel recheck only; no network by design)
- SKIP face: exit 0 = PASS (compile-broken files sit in the debt register, not red); 1 = failing (an axiom outside the whitelist, or an unjudgeable heavy face); 2 = usage error; 9 = fail-loud (a configured binary path does not exist / `--repo` missing); 111 = rocq or coqchk unconfigured (neither flag nor env) as an honest skip, judging nothing rather than simulating (carrying the verify/ rc 111 convention); `ROCWASH_ROCQ` / `ROCWASH_COQCHK` environment gating; the token-quarantine face is not adopted (the gate5 precedent: quarantine only, never a verdict); real runs must be wrapped by `tools/cpu_guard.sh` (carrying the extract_magic_check contract form)

### tools/flaky_guard.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/flaky_guard.py --help` word face (rc=0) and the module docstring, `flaky_guard.py:3-31`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: repair class E2-3, order-dependence detection and advisory-roster quarantine: classifies each red case in a suite log by an isolation probe (suite-red plus alone-green = order-dependent; red in both contexts = content red that stays visible) and, on `--apply`, moves an order-dependent case into `tests/advisory_roster.txt` so the default suite drops it (loud ADVISORY-OUT line) while the CI flaky-watch lane keeps observing it; applies are scope-checked against `tools/repair_scope.py`, budget-capped at 2 per class per branch, and ledgered (`docs/repair-ledger.jsonl`, rows `rocqwash-repair-ledger/1`); `--restore` returns a case after green-round evidence (default 3 consecutive rounds); dry run is the default and `--apply` is the only write face; report schema `rocqwash-flaky-detect/1`.
- Invocation: `python -I tools/flaky_guard.py --detect --log LOG [--json OUT] [--no-probe] | --probe CASE | --move CASE [--apply] | --restore CASE [--apply] [--green-rounds N] | --status | --selftest` plus the shared flags `--budget N` (override the per-branch repair budget, default from repair_scope), `--probe-timeout S` (default 300), `--repo DIR`, `--roster PATH` (default `tests/advisory_roster.txt`), `--ledger PATH` (default `docs/repair-ledger.jsonl`), `--suite PATH` (default `tests/run_tests.sh`), `--py EXE` (interpreter for the suite's child processes, default this interpreter)
- Example: `python -I tools/flaky_guard.py --detect --log <value> --json <value>`
- Imports: argparse, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, time (all standard library) + in-repo `tools/repair_scope.py` (loaded by path; mandatory, absence is a fail-loud rc 9, never a silent inline fallback)
- Network face: zero (no transport-class imports; the subprocess faces are the local suite entry run through bash and a local `git rev-parse --abbrev-ref HEAD`)
- SKIP face: exit 0 accounted (verdicts, plans, refusals are data); 1 refused (frozen target, budget cap, content-red, not-yet-green) or selftest red; 2 usage or malformed input; 9 missing input; the isolation probe reads rc 0 alone-green / 1 content-red / 2 selection error (unknown case) / 111 canonical skip (no evidence either way) / timeout = no evidence; `--status` is read-only; write faces (roster, ledger, `--json` report) land only behind `--apply`; the `--selftest` sandbox vector group drives a mini-suite through the full arc with zero real-repo writes

### tools/gap_cluster.py
- Status: [live](the MCP roster-expansion work stream 1 cast, November 21, 2026: transcribed from the live `python -I tools/gap_cluster.py --help` word face (rc=0) and the module docstring, at HEAD `c48a548a`; not a census product; the entry-less listing this file's delta note records reads one name smaller from this increment)
- Purpose: aggregate TODO-SEAT and gap entries into a family-shape-keyed gap ledger (schema `rocqwash-gap-ledger/1`): collects gap entries from two local faces, the experience ledger (`docs/exp-ledger.jsonl`, schema `rocqwash-exp/1`, gap-class entries carrying the protocol tokens) and vacgen report JSON files (`assumptions[]` entries with status `todo_seat`), and aggregates them by family shape key for the row-rendering stage; aggregation is a pure function of the input bytes: fixed ordering rules, no wall clock, no absolute paths in the report (basenames only), so equal inputs give byte-identical output; zero gaps is data (empty cluster list, exit 0).
- Invocation: `python -I tools/gap_cluster.py [--ledger P]... [--reports P]... [--out FILE] [--json]` (both input flags repeatable and a `--reports` directory expands to its `*.json` files in sorted order; `--json` prints the gap ledger to stdout; with `--out` alone stdout carries a one-line summary)
- Example: `python -I tools/gap_cluster.py --ledger <value> --out <value>`
- Imports: argparse, hashlib, json, os, re, subprocess (function level, inside the selftest harness), sys, tempfile
- Network face: zero
- SKIP face: exit 0 aggregated (empty is data); 1 selftest red; 2 usage error; 9 missing or corrupt input, or report write failure; the only write is the explicit caller-named `--out` file; input schemas are read as data (`rocqwash-exp/1` ledger lines and the vacgen v2 `assumptions[]` element key surface)

### tools/i18n_pipeline.py
- Status: [live](engine-body ticket lane 4 deliverable, integrated at the merge, the E4 orchestration body P0/P1/P3/P6)
- Purpose: zh<->en four-linkage pipeline orchestration body with six immutable operation signatures (carried from `seeds/i18n/pipeline_stub.py`): P0 policy pre-check (the repo/paper/supplement regime table; a refusal is a legal exit-0 ledgered outcome), P1 segmenter (protection list; a segment is a contiguous prose-line range; the ten-key segment ledger includes policy_precheck_ref), P3 four-linkage orchestration (L1 termbase lookup, L2 jargon projection, L3 CJK zero residue plus em-dash density, L4 ai_flavor detection), and P6 segment-ledger closure verification.
- Invocation: `python -I tools/i18n_pipeline.py --manifest <run.json> --stage p0|p1|p3|p6 [--json <out>]` / `--selftest`
- Example: `python -I tools/i18n_pipeline.py --manifest out/run.json --stage p1 --json out/segments.json`
- Imports: argparse, io, json, os, re, subprocess, sys, tempfile + in-repo `tools/jargon_apply.py` / `tools/i18n_translate.py` / `tools/i18n_verify.py` / `tools/termbase.py` (the assembly face)
- Network face: zero (the P2 network face lives entirely in the `tools/i18n_translate.py` provider)
- SKIP face: a P0 refusal is a legal outcome, not a failure (the ledger carries its row); closure verification refuses to close fail-loud when unsatisfied; the assembly leg fails loud when the lane-5/lane-6 modules are absent

### tools/i18n_translate.py
- Status: [live](engine-body ticket lane 5 deliverable, integrated at the merge, the E4 model-site layer P2)
- Purpose: Model-site layer P2: the handoff form is zero-network by default (`--emit` emits the segment package; after backfill `--ingest` runs ten-key validation including policy_precheck_ref; a missing model_id or missing annotation is a violation and the ingest refuses fail-loud); the http form is optional default-deny (an OpenAI-compatible endpoint is called per segment and annotated per segment with `annotation_site="model"`; the NETRED ledger carries one line per call including failures); the prompt template comes from `--prompts <dir>` (built-in constants by default).
- Invocation: `python -I tools/i18n_translate.py --segments <p> --emit <out.jsonl> [--prompts <dir>]` / `--ingest <in.jsonl>` / `--provider handoff|http`
- Example: `python -I tools/i18n_translate.py --segments out/segments.json --emit out/handoff.jsonl`
- Imports: argparse, io, json, os, re, sys, tempfile, time, urllib.request
- Network face: handoff face zero; http leg non-zero (default-deny: the three environment-gate variables refuse loudly when any is missing and name the missing item; a NETRED ledger line per call including failures; credential values never hit disk or logs)
- SKIP face: the only network face in the ticket is the http provider leg; a missing environment gate refuses rather than degrades; a machine segment with zero annotations is a pipeline violation refused by the ten-key ingest (including policy_precheck_ref)

### tools/i18n_verify.py
- Status: [live](engine-body ticket lane 6 deliverable, integrated at the merge, the E4 P4/P5 body)
- Purpose: P4 mechanical verification orchestration (subprocess calls to `tools/ai_flavor.py` / `tools/norm_lint.py --jargon-map` / `tools/doc_lint.py`, merged into the verification matrix JSON `rocqwash.i18n.verify/1`); P5 human ten-point form (`--emit-tenpoint` emits the review form, taking a variant per target-face shape; `--ingest-tenpoint` validates verdicts and writes them back to the segment ledger field `tenpoint_verdict`; the engine never judges for the human).
- Invocation: `python -I tools/i18n_verify.py --verify-target <p> [--json <out>]` / `--emit-tenpoint <target>` / `--ingest-tenpoint <verdicts.json>` / `--selftest`
- Example: `python -I tools/i18n_verify.py --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json`
- Imports: argparse, io, json, os, subprocess, sys, tempfile + local instrument subprocesses (`tools/ai_flavor.py` / `tools/norm_lint.py` / `tools/doc_lint.py`)
- Network face: zero (subprocesses are local tools in read-only probe runs)
- SKIP face: the P5 ten-point form is a human gate (the engine emits the form and writes verdicts back, it never produces a verdict); a missing subprocess target fails loud; the verdicts file schema is `rocqwash.tenpoint.verdicts/1`

### tools/jargon_apply.py
- Status: [live](engine-body ticket lane 2 deliverable, integrated at the merge, the E2 apply face plus pure-function library)
- Purpose: Jargon-to-standard apply face: data read-only from `seeds/jargon/jargon-map.json` (62 entries); only `disposition:"replace"` entries are machine-written; `rewrite_or_delete` entries are never machine-written (findings list their disposition as human); guarded rows refuse by default (`--guarded-interactive` emits the per-row query file); the preserve carve-out rides the exempt mechanism; identifier positions are never rewritten (backtick spans are masked); the default plan writes nothing and lists before/after pairs; `--apply` rescans to residue zero before exit 0; idempotent.
- Invocation: `python -I tools/jargon_apply.py --file <p> | --tree <dir> [--plan | --apply] [--json <out>] [--guarded-interactive]` / `--selftest`
- Example: `python -I tools/jargon_apply.py --tree docs --plan --json out/jargon-plan.json`
- Imports: argparse, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile + in-repo `tools/norm_lint.py` (the same-source matcher)
- Network face: zero
- SKIP face: zero writes by default; `rewrite_or_delete` rows are disposition=human; a non-zero rescan residue exits non-zero (verification failing); idempotent (a second apply reports zero would-fix)

### tools/lean_sweep.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/lean_sweep.py --help` word face (rc=0) and the module docstring, `lean_sweep.py:2-31`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: Lean vacuity probe batch sweep orchestrator (seed completion): bins vacuity probe files (witness, boundary, the canonical five refutation forms full / point / tactics / noclassic / band) into per-lane compile shots, dedups every probe against the union of all prior lane ledgers (skip-existing on the canonical key batchId|idx|probe), casts merged shots with a row-offset map plus a zero-compile syntax precheck, and fires only when `--fire` is given and the toolchain probe passes; the compile leg is a designed SKIP in the default face (loud declaration, no spawn); a lane that trips the ALERT gate writes its marker and stops before its next shot (judge side = `verdict_diff.py`, the double gate), with a bisect fallback and a stop-race terminal recheck; batches plan schema `rocqwash-lean-sweep.batches/1`, status JSON schema `rocqwash-lean-sweep.status/1`, lane ledgers in the canonical five-column form batchId|idx|probe|status|rc; `--taxonomy` pins the consumer contract for row_render candidate rows (the C3.4 row contract mirrored from vacgen.py validate_row plus the canonical five-form caliber).
- Invocation: `python -I tools/lean_sweep.py --batches B.json --out DIR [--json F] [--fire] [--worktree WT] [--lake PATH] [--guard PATH] [--core N] [--lanes N] [--skip-ledgers [F ...]] [--taxonomy FILE] [--max-shot-items N] [--big-item-bytes N] [--liveness-interval S] [--bisect-max N] [--timeout-s S] | --selftest` (defaults: cores 4, lanes 12 (1..16), shot cap 30, slow-lane threshold 51200 bytes, liveness 70 s, bisect budget 8, per-shot timeout 600 s)
- Example: `python -I tools/lean_sweep.py --batches <value> --out <value>` (the default face: designed SKIP, shots cast and prechecked as plan artifacts, nothing spawns)
- Imports: argparse, hashlib, json, os, re, shutil, subprocess, sys, time (all standard library)
- Network face: zero (no transport-class imports; the fire leg shells out to the local lake binary, optionally wrapped in the thermal guard, and only after the toolchain probe passes)
- SKIP face: exit 0 ok (designed skips declared loud; `--fire` with lake absent prints SKIP-TOOLCHAIN-ABSENT and the compile leg stays a declared skip with rc 0); 1 failing sweep data; 2 ALERT freeze (stop-work) or usage or malformed form (the banner names which); 3 syntax precheck refusal, nothing fires; 9 missing input path; `--fire` without `--worktree` is a usage error (rc 2); lean/lake/mathlib word face (23 hits) and cpu_guard word face (1 hit) are word-face facts, and the compile-verification leg needs a Lean toolchain (a design SKIP face)
- Note: `--selftest` is documented on the doc face and dispatched via `sys.argv` before argparse (`lean_sweep.py:912-913`); the argparse flag face (16 flags) does not list it. Recorded as the doc-versus-argparse divergence form (the `net_probe` precedent in INDEX section 2).

### tools/learning_feedback.py
- Status: [contracted](learning-feedback deliverable, cast from the batch contract face under the contract-first parallel rule; the [live] marker rides the tool lane's own integration increment)
- Purpose: Scheduling feedback edge: reads the three standing accounts (`docs/round-ledger.jsonl`, `docs/round-state.json`, `docs/exp-ledger.jsonl`) and computes the scheduling-readable feedback file `docs/scheduling-feedback.json` (schema `rocqwash.scheduling-feedback/1`): the round totals with the auto and human-approved split, the approval rate over all rounds (human-approved rounds stay in the denominator), the per-class gear and confidence readings, and the four-state repair outcome tally (repaired / escalated / watch-only-guard-correct, with rows that fit no state honestly counted as `unrecorded`); the feedback edge is declared open: the approval rate becomes readable while scheduling does not yet consume it (declared blank).
- Invocation: `python -I tools/learning_feedback.py [--selftest]` (the default run reads the three accounts and writes the feedback file plus a stdout summary)
- Example: `python -I tools/learning_feedback.py --selftest`
- Imports: standard library only per the contract face (argparse CLI, JSONL reading, tempfile fixtures); the itemized import list, measured at HEAD `0765d671` (the four-tool backfill): argparse, json, os, re, shutil, sys, tempfile at module level, no function-local imports, zero in-repo imports
- Network face: zero (no network by design per the contract face)
- SKIP face: exit 0 = readings are data (a missing account or a damaged row lands in an `error` field, the stdout summary fails loud, and the run continues rather than silently skipping; `repair_action_rate` reads null on a zero denominator, reported as declared, never padded); the only write face is `docs/scheduling-feedback.json`; `--selftest` runs four vectors on tempfile fixtures (one auto plus one human round, bad-row tolerance, an empty account, all-unrecorded outcomes), zero network, zero touches of the real accounts

### tools/ledger_sync.py
- Purpose: TSV merge synchronizer between the probe ledger and the status ledger (policy parameterized).
- Invocation: `python tools/ledger_sync.py [--probe] [--ledger] [--out] [--report] [--policy]`
- Example: `python tools/ledger_sync.py --probe <value>`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/net_probe.py
- Purpose: Network-window probe: bare-GET reachability over all endpoints for N rounds; a window counts as stable only after two consecutive all-endpoint passes.
- Invocation: `python tools/net_probe.py [--endpoints] [--rounds] [--interval] [--stable-window] [--jitter] [--seed] [--json]` (flag-value details: `--endpoints` is a comma-separated endpoint list, `--rounds`/`--interval` are numeric; see the per-flag kwargs face of `argparse.add_argument` in the JSON)
- Example: `python tools/net_probe.py --endpoints <value> --stable-window`
- Imports: argparse, datetime, io, json, os, random, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request
- Network face: non-zero (socket, urllib.request; the network is the probe's subject)
- SKIP face: no toolchain markers; runs need a network window (its own job)
- Note: The docstring usage line (`net_probe.py:20`) documents `--selftest`, dispatched manually via `sys.argv` before argparse (`net_probe.py:317-319`; `selftest()` defined at line 173); the argparse flag face (7 flags) does not list it. Recorded as a doc-versus-argparse divergence for the light-probe step to verify.

### tools/netname_normalize.py
- Purpose: Normalizes doubled `.v.v` suffixes (map can be emitted or applied with `--apply`).
- Invocation: `python tools/netname_normalize.py [--dir] [--apply] [--map] [--json]`
- Example: `python tools/netname_normalize.py --dir <value> --apply`
- Imports: argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/norm_lint.py
- Purpose: Annotation-face normalization lint, report-first form (jargon map, CJK threshold, and whitelist parameterized; built-in `--selftest`).
- Invocation: `python tools/norm_lint.py [--tree] [--file] [--jargon-map] [--cjk-threshold] [--cjk-whitelist] [--json] [--md] [--selftest]`; integration addition (engine-body ticket, at integration): `[--ai-flavor-map]` (optional ai-flavor report face; byte-identical report when absent by default)
- Example: `python tools/norm_lint.py --tree <value> --selftest`
- Imports: argparse, fnmatch, io, json, os, re, shutil, sys, tempfile, tokenize
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/pin_repair.py
- Status: [contracted](pin-repair deliverable, cast from the batch contract face under the contract-first parallel rule; the [live] marker rides the tool lane's own integration increment)
- Purpose: Pin-drift repair executor for the R15 class: reads the seed JSON's `provenance.sources` array and checks each pinned source, runs the sync tool's zero-write plan (`python -I tools/jargon_map_sync.py`), and proceeds only on the `VERDICT IN-SYNC` reading (any other verdict means content retagging, which belongs to human adjudication: exit 3 with the raw verdict reported); `--plan` reports the drifted sources (path, pinned value, current value) with zero writes; `--apply` re-signs the seed's pin fields from the sources' current evidence (JSON key order and 2-space indent preserved, only pin values change) and re-runs `python -I tests/t_engines_seeds.py` as the local verification gate, restoring the seed from the pre-apply byte snapshot (exit 4, fail-loud) when verification is not green. Provenance v2 form (schema face `docs/pin-provenance-v2.md`): repo sources are judged by the committed blob sha of their content (`git rev-parse HEAD:<path>`), external sources by two layers (the in-repo snapshot md5 everywhere; the upstream freshness layer canonical-only, an absent upstream reported as a declared skip, never a silent one); the sync tool's one-shot migration form (`python -I tools/jargon_map_sync.py --migrate`) converts the v1 seed (absolute-path md5 pins) to v2 and lands the snapshot files.
- Invocation: `python -I tools/pin_repair.py --selftest | --plan | --apply [--seed <path>]` (`--seed` defaults to `seeds/jargon/jargon-map.json`)
- Example: `python -I tools/pin_repair.py --plan`
- Imports: hashlib, io, json, subprocess named by the contract face (standard library only); the itemized import list, measured at HEAD `0765d671` (the four-tool backfill): argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile at module level, no function-local imports, zero in-repo imports
- Network face: zero (the subprocesses are the local sync tool and the local seeds suite; no network by design)
- SKIP face: exit 0 = plan reported or apply verified green (`action:"none"` when nothing drifted, `action:"plan"` on the report face, `verify:"seeds-suite-green"` after a green apply); 3 = non-IN-SYNC plan verdict (content retagging needs human adjudication, reported with the raw verdict, never machine-applied); 4 = post-apply verification not green, seed restored from the pre-apply byte snapshot, fail-loud; stdout carries one JSON result line, the human-readable process goes to stderr, and no credential value is printed; `--selftest` runs four vectors on tempfile fixtures (in-sync, drifted, absent source, non-IN-SYNC), zero network, zero touches of the real seed

### tools/pushci.py
- Purpose: One-shot push-then-CI orchestrator: push, ls-remote confirmation, CI watching, verdict reading, and heal rounds (steps, heal cap, and watch cadence parameterized).
- Invocation: `python tools/pushci.py [--repo-path] [--branch] [--base-ref] [--remote] [--pre-scan-gate4] [--pr] [--merge] [--merge-method] [--max-heal] [--watch-interval] [--probe-interval] [--watch-max-rounds] [--timeout] [--retry-max] [--steps] [--injector] [--git-caller] [--sleep-scale] [--netrc] [--json] [--dry-run]`
- Example: `python tools/pushci.py --repo-path <value> --pre-scan-gate4`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request + in-repo `tools/_http_backoff.py`
- Network face: non-zero (urllib.request; git subprocess token face: `push`, `ls-remote`; a subprocess-bridge token hit)
- SKIP face: the `ROCWASH_MASK` environment variable, coq family word face (11); runs need a network window and remote repository access rights

### tools/red_dispatch.py
- Purpose: Red-event dispatcher: routes an event file to preset actions (cooldown, state file, dry-run, and built-in `--selftest`).
- Invocation: `python tools/red_dispatch.py [--event-file] [--preset] [--json] [--state-file] [--cooldown] [--repo-path] [--param] [--on-args] [--dry-run] [--selftest]`
- Example: `python tools/red_dispatch.py --event-file <value> --dry-run`
- Imports: argparse, contextlib, io, json, os, re, shutil, subprocess, sys, tempfile, time
- Network face: zero
- SKIP face: coq family word face (5), cpu_guard word face (1)

### tools/registry_audit.py
- Purpose: Read-only hygiene audit over the two registry files, emitting a deterministic fix plan.
- Invocation: `python tools/registry_audit.py [--order] [--project] [--git] [--ref] [--git-path-order] [--git-path-project] [--live-src] [--anchor-src] [--fix-plan] [--json] [--md]`
- Example: `python tools/registry_audit.py --order <value> --fix-plan`
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile + in-repo `tools/registry_union.py`
- Network face: zero
- SKIP face: coq family word face (12)

### tools/registry_fix.py
- Purpose: Applies the fix plan produced by registry_audit (`--apply`; `ROCWASH_REGISTRY_FIX_INJECT_BLAST` is a blast-injection test hook).
- Invocation: `python tools/registry_fix.py [--audit-json] [--order] [--project] [--anchor-src] [--apply] [--work-dir] [--audit-tool] [--json]`
- Example: `python tools/registry_fix.py --audit-json <value> --apply`
- Imports: argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile + in-repo `tools/registry_union.py`
- Network face: zero
- SKIP face: the `ROCWASH_REGISTRY_FIX_INJECT_BLAST` environment variable, coq family word face (5)

### tools/registry_regen.py
- Purpose: Regenerates contribution registration rows onto the merge-target line (base and contribution repos, refs, piece table, and path table parameterized).
- Invocation: `python tools/registry_regen.py [--base-repo] [--base-ref] [--contrib-repo] [--contrib-ref] [--pieces] [--anchor-src] [--dep-source] [--seq] [--base-path-order] [--base-path-project] [--contrib-path-order] [--contrib-path-project] [--out] [--apply] [--json]`
- Example: `python tools/registry_regen.py --base-repo <value> --apply`
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile + in-repo `tools/registry_union.py`
- Network face: zero
- SKIP face: coq family word face (37)

### tools/registry_union.py
- Purpose: Three-way union merger for the registry (base/main/branch inputs; re-anchoring and kind selection parameterized).
- Invocation: `python tools/registry_union.py [--base] [--main] [--branch] [--git] [--ref-base] [--ref-main] [--ref-branch] [--git-path] [--kind] [--reanchor] [--anchor-src] [--out] [--apply] [--json]`
- Example: `python tools/registry_union.py --base <value> --apply`
- Imports: argparse, collections, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: coq family word face (4)

### tools/render_events.py
- Purpose: Renders a JSONL event stream into a markdown ledger.
- Invocation: `python tools/render_events.py [--events] [--dir] [--md] [--json] [--top]`
- Example: `python tools/render_events.py --events <value>`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: no special environment word-face markers

### tools/repair_scope.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/repair_scope.py --help` word face (rc=0) and the module docstring, `repair_scope.py:3-32`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: shared exclusion roster for the repair apply faces: one source of truth for the faces a repair class never targets, namely the frozen ledger rows (LEDGER8 and CHECKERS read at runtime from `certify/frozen8.py` parsed as an AST literal, the module body never executed, with a pinned snapshot tuple as the loud fallback), the append-only ledger document, and the frozen directory families; the provider functions (`frozen8_ledger`, `frozen8_checkers`, `ledger_doc`, `exclusion_roster`, `full_frozen_files`) are imported by the repair classes, which append below the append-zone marker with a read-merge-write edit and never a whole-file rewrite; the CLI answers is-excluded queries (`--check`, verdict EXCLUDED or REPAIRABLE, a verdict is data; `--a2-table` adds the F1 single-source A2 mapping table to the exclusion set for that one query), prints the registered repair-class budget registry (`--classes`), and carries the class-1 ghost-lane face (`--lane-detect` dry run / `--lane-apply`) and the class-4 doc-count face (`--doc-count-detect` report-first drift scan / `--doc-count-apply` minimal count-token repairs under the exclusion and budget gates); bare invocation defaults to `--selftest`.
- Invocation: `python -I tools/repair_scope.py [--selftest] [--repo DIR] [--check REL [REL ...]] [--a2-table P] [--classes] [--lane-detect] [--lane-apply] [--suite SUITE] [--ledger LEDGER] [--json-out P] [--doc-count-detect] [--doc-count-apply]` (`--check`, the lane face, the doc-count face, and `--classes` are mutually exclusive; the CLI names the conflict and exits 2)
- Example: `python -I tools/repair_scope.py --classes`
- Imports: argparse, ast, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (all standard library; `subprocess` sits at the branch-guard face, `doc_lint` is loaded at the doc-count face) + in-repo `certify/frozen8.py` read as an AST literal (never executed)
- Network face: zero (the subprocess face is a local `git rev-parse --abbrev-ref HEAD` read)
- SKIP face: exit 0 all vectors pass, or a clean `--check` / `--classes` / detect face answer; 1 a data verdict (an EXCLUDED classification, detected drift or residual, or a failed selftest vector); 2 usage error or a mutually exclusive face conflict; 9 a missing `--repo` directory or missing input path; consumers load this module by path (importlib), the same way `jargon_apply` loads `norm_lint`; `--lane-detect` and `--doc-count-detect` are zero-write faces by design

### tools/repair_weekly.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/repair_weekly.py --help` word face (rc=0) and the module docstring, `repair_weekly.py:3-32`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: repair-outcome ledger weekly distribution face (repair class E6): aggregates the repair-outcome ledger (`docs/repair-ledger.jsonl`, append-only JSONL) into the weekly distribution face, the per-red outcome census under the E6 vocabulary (repaired / escalated(evidence-package) / watch-only(guard-correct: R), R in cancel-intent | superseded | budget | out-of-scope), the class and ticket distributions, and the ISO-week slice of `--date`; `/1` rows carry the free-form outcome field and are normalized by the token before the first parenthesis (unrecognized tokens stay data; an escalated `/1` row without evidence lands in the escalated-without-evidence-package line, counted, never reclassified); `/2` rows carry repair-outcome verbatim under the enforced vocabulary (a missing repair-outcome field on a `/2` row is fail-loud); `--record` appends one per-red outcome row (schema `rocqwash-repair-ledger/2`, append-only, no dedup) and plans without `--apply`; report schema `rocqwash-repair-weekly/1`; the aggregate and JSON faces carry no wall clock (identical inputs produce byte-identical reruns).
- Invocation: `python -I tools/repair_weekly.py [--ledger P] [--date YYYY-MM-DD] [--out FILE] [--json P] | --record --class CLASS --target T --repair-outcome VALUE [--ticket K] [--evidence-file J] [--reason S] [--apply] | --selftest` (the documented route face is `cw.sh repair-weekly`, bash 3.2 compatible)
- Example: `python -I tools/repair_weekly.py --date <value> --json <value>`
- Imports: argparse, datetime, io, json, os, sys, time (module level; `hashlib`, `shutil`, `subprocess`, `tempfile` sit at function level inside the selftest harness)
- Network face: zero
- SKIP face: exit 0 report produced (an absent default-path ledger is a zero-row report); 1 selftest red; 2 usage error, malformed row, or vocabulary refusal; 9 missing input (an explicitly named `--ledger` or `--evidence-file` path absent); `--out` and `--json` are the only write faces (the record face writes the ledger only behind `--apply`); the write faces are pinned by the K rows of `tests/test_destructive_matrix.py`
- Note: the doc face states "zero subprocess"; the AST word face carries a selftest-only `subprocess` import (the CLI exit-code mapping vector, `repair_weekly.py:592-598`). The aggregate and record faces spawn nothing. Recorded as a doc-versus-AST divergence (the `net_probe` precedent form).

### tools/roster_resync.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/roster_resync.py --help` word face (rc=0) and the module docstring, `roster_resync.py:3-38`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: roster count drift guard (E2 repair class 2), one-way recount and sync: the suite roster (the CASES block of `tests/run_tests.sh`) is the only count authority; the guard recounts the roster, then rewrites every drifted count line in `tests/README.md` and `README.md` to the roster value, using the four count-line shapes imported from `doc_lint` (COUNT_PATTERNS + CASES_RE) so the shapes can never diverge from the doc_lint oracle; one-way roster to docs, the roster file is never written; dry-run by default, `--apply` is the only write face, every repaired line appends one ledger row (schema `rocqwash-repair/1`), and the shared exclusion table (`tools/repair_scope.py`, class RosterResyncScope) gates every target before any byte lands; the per-class per-branch repair budget is 2.
- Invocation: `python3 tools/roster_resync.py [--repo DIR] [--apply] [--ledger P] [--json OUT] | --selftest` (`--ledger` defaults to `docs/repair-ledger.jsonl` under the repo root; `--json` writes the plan report, schema `rocqwash-roster-resync/1`, sort_keys determinism)
- Example: `python3 tools/roster_resync.py --json <value>`
- Imports: argparse, io, json, os, subprocess, sys, time (all standard library) + in-repo `doc_lint` (COUNT_PATTERNS + CASES_RE) and `repair_scope` (RosterResyncScope), same-directory imports with an explicit `sys.path` insertion so they survive isolated interpreters (`-I` never prepends the script directory, `roster_resync.py:48-55`)
- Network face: zero (the subprocess faces are the local doc_lint verification run and a local `git rev-parse`)
- SKIP face: exit 0 clean or repaired to clean; 1 drift found (dry-run) or an escalation landed (budget cap / refused face / missing count shape / post-repair assertion); 2 usage error; 9 missing input (no roster block, unreadable count file, corrupt ledger); every outcome is loud (a red is data, never a silent pass); the roster file bytes never change and the ledger stays untouched on dry-run

### tools/row_render.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/row_render.py --help` word face (rc=0) and the module docstring, `row_render.py:1-29`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: refinery W2 row renderer: renders a gap-cluster ledger (the W1 face) into candidate taxonomy rows for `docs/drafts/taxonomy-candidates.json` through the E4 P2 handoff form: emit a render packet, an external model-side agent backfills one candidate row per gap, and ingest admits every row only when the vacgen admission gate (validate_row, C3.4) passes; the renderer delegates and never re-implements row judgment (admission from the vacgen host, the provider and NETRED faces from the i18n host, the ten-point face from the verify host, all loaded by path, a broken host is a loud failure naming the path and the face); the draft (schema `rocqwash.taxonomy-candidates/1`) carries per-row provenance (sourceGapId, sourceLane "row-render-handoff"), a flat tenpointVerdict field that starts PENDING and is rewritten by the ten-point ingest, and the four-element negative-finding boundary in its provenance block; any rejection or uncovered gap aborts the draft write (fail loud, no partial draft); re-render with the same ledger and the same backfill reproduces the draft bytes.
- Invocation: `python -I tools/row_render.py --gaps GAPS (--emit EMIT | --ingest INGEST | --check-draft D | --emit-tenpoint T | --ingest-tenpoint T --draft-out D | --provider http --netred-ledger N) [--vacgen P] [--prompts DIR] [--policy-ref R] [--ledger-out P] [--json P] [--timeout S] [--selftest]` (`--provider` takes handoff (default, zero network) or http (default-deny gate); `--vacgen` resolves flag, then the `ROW_RENDER_VACGEN` env var, then the sibling `tools/vacgen.py`; the verify host resolves `ROW_RENDER_VERIFY` then the sibling; `--timeout` defaults to 60 s)
- Example: `python -I tools/row_render.py --gaps <value> --emit <value> --json <value>`
- Imports: argparse, datetime, importlib.util, io, json, os, re, sys, tempfile, urllib.error, urllib.request (all standard library) + dynamic host loads of the sibling modules `tools/vacgen.py`, `tools/i18n_translate.py`, and `tools/i18n_verify.py`
- Network face: handoff face zero; http leg non-zero (urllib.request; default-deny gate via the i18n host's `check_net_env`: `ROCWASH_MCP_ALLOW_NET=1` plus `ROCWASH_LLM_ENDPOINT` / `ROCWASH_LLM_MODEL` / `ROCWASH_LLM_KEY` all set; one NETRED ledger line per call including failures; `--netred-ledger` is required for the http provider; credentials never enter packets, ledger rows, reports, or log lines)
- SKIP face: exit 0 success; 1 data verdict red (rejections, incomplete gap coverage, admission failures, invalid draft rows); 2 usage or environment refusal (each named on stderr); 9 input or output file unreadable; the engine never judges (the ten-point form is a human gate; the renderer only supplies the ten row-review point texts and writes the verdict frame back); the renderer-side row contract requires schemaVersion 2 and the thirteen rendered fields, keeps refutationForms inside the W6 vocabulary, and applies the trace check against declared sample faces; lean-family word face (15 hits) rides the vacgen adjacency vocabulary and is a word-face fact, not a runtime requirement
- Note: the ten-point ingest reviews the draft and writes the frame back through `--draft-out`; the admission gate and the target enum come from the loaded vacgen host (`ROW_FLAG_MAP`, `flags_int`, `MATCH_TARGETS`), so a vacgen version advance moves this tool's admission face with it.

### tools/scheduler_lite.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `py -I tools/scheduler_lite.py --help` word face (rc=0) and the module docstring, `scheduler_lite.py:3-29`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: TODO-SEAT threshold trigger face for the jargon tier-B auto gear (the lite scheduler of recursive batch 3, ticket X2): watches the TODO-SEAT gap account (the gap feed ledger `docs/gap-feed-ledger.jsonl` plus the vacgen report directory, aggregated by `tools/gap_cluster.py`) and the round cadence (`docs/round-ledger.jsonl`), and decides whether a jargon-class auto round is due under the tier-B auto gear (`autonomy.json` mode auto, admitted roster `docs/round-state.json`); ignition stays behind the EF all-green marker gate (`--ef-marker`); the face plans only and never fires (dry-run by design, the single command `plan`); the plan document (schema `rocqwash.scheduler-lite.plan/1`) carries the verdict quiet | due | blocked with reason tokens, absent defaults are data, and corrupt explicit input exits 9; the round-interval default is a measured backfill (40566 s, the round 1 to round 2 tail pair of the round ledger) and `--interval-seconds` amends the same knob; `--now-utc` overrides the plan clock so equal inputs stay byte-identical.
- Invocation: `py -I tools/scheduler_lite.py plan [--gap-ledger P]... [--reports P]... [--rounds P] [--autonomy P] [--state P] [--ef-marker P] [--threshold N] [--interval-seconds N] [--now-utc ISO8601Z] [--out FILE] [--json] | --selftest` (the positional command takes only `plan` and defaults to it; the path flags are repeatable)
- Example: `py -I tools/scheduler_lite.py plan --json`
- Imports: argparse, datetime, importlib.util, json, os, re, sys (module level; `shutil`, `subprocess`, `tempfile` sit at function level inside the selftest harness) + in-repo `tools/gap_cluster.py` (loaded by path as the same-source gap aggregator; absent module exits 9)
- Network face: zero (no transport-class imports; the ignition-step constants in the source name `jargon_apply` / `auto_round` command shapes and are informational only, this face executes neither step)
- SKIP face: exit 0 the plan face answered (quiet and blocked are data); 1 selftest red; 2 usage; 9 corrupt or explicitly missing input; `--out FILE` is the only write face; the `--json` form prints the plan document on stdout; `--selftest` fixture vectors run on tmp inputs with zero writes
- Note: `--selftest` is documented on the doc face and dispatched via `sys.argv` before argparse (`scheduler_lite.py:643-644`); the argparse flag face (11 flags plus the positional) does not list it (the `net_probe` precedent form).

### tools/select_audit.py
- Purpose: Audits a batch selection against the tree's order file by full-table grep.
- Invocation: `python tools/select_audit.py [--order] [--select] [--grep] [--requires] [--world] [--json]`
- Example: `python tools/select_audit.py --order <value>`
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: opam word face (2, semantics pending the light-probe judgment)

### tools/selfevolve_round.py
- Status: [contracted](A-batch closed-loop deliverable, cast from the batch contract face under the contract-first parallel rule; the [live] marker rides the tool lane's own integration increment)
- Purpose: One deterministic mechanical round on the cron face: census (jargon_apply --plan on the tree) -> apply -> verify (py_compile / bash -n hard gates, norm_lint / doc_lint advisory) -> auto_round commit -> push -> route the CI judge. The A-batch increment adds two faces: (1) the environment-aware pin-repair leg, active only behind the explicit `--pin-repair` flag (the hosted cron form passes no flag, zero scheduled behavior change): it plans the seed (`python -I tools/pin_repair.py --plan --seed <seed>`); pinned sources absent on the host (the hosted structural blind, absolute paths outside the repo) = one ledger row (action=plan, note=hosted-blind), then a clean zero-commit skip; drift with plan rc=0 = apply (`--apply --seed <seed>`) and one independent commit (class R15-repair, message naming the IN-SYNC plan verdict and the armed verify-rollback) carried by the round's existing push; apply rc nonzero = fail-loud, zero commit; zero drift = a one-line no-op; the leg is fenced so the round main chain never blocks on it (one ok:false ledger row, then continue). (2) consumption v2: the round report carries `cadence_hint`, read from `docs/scheduling-feedback.json` (schema rocqwash.scheduling-feedback/1; a missing file reads hint normal, note absent) and mapped by a finite constant tier table: escalated >= 3, or repaired == 0 with total repair actions >= 5, reads alert; repair_action_rate < 0.2 reads slow; otherwise normal; an alert reading also appends one cadence-alert row to `docs/repair-plan-ledger.jsonl` (schema rocqwash.repair-plan/1) and prints loud. The workflow cron expression is untouched: cadence modulation is a desk order, the report carries the hint only.
- Invocation: `python -I tools/selfevolve_round.py [--dry-run] [--pin-repair] [--seed SEED] [--selftest]` (argparse flag face, measured at HEAD `0765d671` by `--help`, rc=0; `--dry-run` is the local testing form; `--pin-repair` is the desk/local opt-in for the repair leg; the contract-era "no argparse; the flag face is read from sys.argv" reading is superseded by this measurement)
- Example: `python -I tools/selfevolve_round.py --dry-run --pin-repair`
- Imports: json, os, subprocess, sys, urllib.request (all standard library; urllib.request is the function-local import of the CI judge routing leg); the itemized import list, measured at HEAD `0765d671` (the four-tool backfill): argparse, json, os, shutil, subprocess, sys, tempfile, time, types at module level plus urllib.request function-local inside `gh_dispatch`, zero in-repo imports
- Network face: non-zero (urllib.request; the git push subprocess token face)
- SKIP face: exit 0 = green terminal states (a clean no-op pass on zero qualifying fixes, the dry-run report, or a completed round; a hosted-blind or zero-drift repair leg is a ledger data state, never a failure); nonzero exits are the fail-loud gates (unreadable census report, apply residue nonzero, admission refusal, push refusal); the repair-plan ledger path honors the `ROCQWASH_REPAIR_PLAN_LEDGER` environment override (default `docs/repair-plan-ledger.jsonl`); cadence tiers are a finite constant table (normal / slow / alert), never generated at run time; `round-plan.json` and `round-apply.json` are round runtime products

### tools/symbiosis_bus.py
- Status: [live](symbiosis-bus ticket lanes 1-3 deliverable, integrated at the merge, the four-face body of specification §1.1)
- Purpose: Cross-repository experience bus: export renders the local ledger as an offline swap package (schema `rocqwash-symbio/1`, one envelope line carrying `sourceRepo`/`anchor`/`entryCount`, then one verbatim entry line per entry); import lands each entry through the `tools/exp_port.py` append face (duplicate ids and fingerprints skip idempotently; a `symbio:<sourceRepo>@<anchor>` correlationId marks the route); status counts both directions from entry content; diff lists the entry-id difference of two ledgers. No network face by design (exchange walks offline files; the NETRED register row states no network by design).
- Invocation: `python tools/symbiosis_bus.py [--selftest] {export,import,status,diff} [--out SWAP.jsonl] [--swap SWAP.jsonl] [--ledger P] [--source-repo NAME] [--anchor HEX] [--a LEDGER_A] [--b LEDGER_B] [--dry-run]` (`--swap` exactly one on the import face, repeatable on the status face; a real export run needs `--out`)
- Example: `python tools/symbiosis_bus.py export --ledger docs/exp-ledger.jsonl --out swap-round1.jsonl --source-repo rocqwash`
- Imports: argparse, json, os, sys + in-repo `tools/exp_port.py` (same directory; the import leg rides its append contract and ledger parsing)
- Network face: zero (three channels, zero hits; no network by design)
- SKIP face: exit 0 = readings are data (duplicate-skip / zero diff / zero counts); 1 = selftest vector group error exit; 2 = usage or IO; 9 = missing or damaged input, zero writes; timestamps ride entry content, never a clock; write faces = the export `--out` file plus the ledger reached through the append face on import

### tools/termbase.py
- Status: [live](engine-body ticket lane 6 deliverable, integrated at the merge, the E3 offline lookup thin layer)
- Purpose: Read-only terminology thin layer: `seeds/termbase/termbase.json` read-only (stdlib json, schema validation fails loud), `lookup(term) -> entries` exact-face lookup (stress and fullwidth brackets stripped, faces split on separators), plus `--selftest`; zero network; the E3 net interface and DIY channel stay candidates of their own seed SPECs.
- Invocation: `python -I tools/termbase.py --lookup <term> [--db <p>] [--json <out>]` / `--schema-check` / `--selftest`
- Example: `python -I tools/termbase.py --selftest`
- Imports: argparse, json, os, sys (all standard library)
- Network face: offline zero (the networked interface is an E3 candidate, default-deny, outside this ticket)
- SKIP face: the built-in snapshot is never edited in place (the upstream terminology table is the single maintenance point); a miss is data (an empty result exits 0)

### tools/toolchain_dyld_doctor.py
- Purpose: Diagnoses broken macOS dyld toolchain links (worker/donor locating and a smoke probe, parameterized).
- Invocation: `python tools/toolchain_dyld_doctor.py [--worker] [--donor] [--smoke] [--coqc] [--guard] [--json]`
- Example: `python tools/toolchain_dyld_doctor.py --worker <value> --smoke`
- Imports: argparse, io, json, os, shutil, subprocess, sys, tempfile
- Network face: zero
- SKIP face: the `ROCWASH_ROCQWORKER` environment variable, coq family word face (32), dyld tooling face (39), cpu_guard word face (5); the diagnostic target is the macOS-specific tooling face

### tools/unclog.py
- Purpose: Blockage-clearing engine for compilation: candidate-chain probing and multi-round clearing (`--rounds`/`--apply`/`--audit`, guard coupling, and loop face parameterized).
- Invocation: `python tools/unclog.py [--src] [--world] [--candidates] [--chain-ledgers] [--repo-path] [--rounds] [--apply] [--audit] [--top] [--scan-ids] [--pack] [--probe-resume] [--probe-parallel] [--rocq-cmd] [--guard] [--guard-reg] [--guard-front] [--guard-mid] [--guard-maxwait] [--timeout] [--workdir] [--json] [--events] [--once] [--loop] [--interval] [--loop-max] [--sleep-scale] [--injector] [--state-file]`
- Example: `python tools/unclog.py --src <value> --apply`
- Imports: argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile, time
- Network face: zero
- SKIP face: coq family word face (5), cpu_guard word face (2); the clearing target faces the Coq/Rocq compile environment

### tools/uplink.py
- Status: [live](uplink ticket, three deliverables, integrated at the merge, the three-face body of specification §1.2)
- Purpose: Standard intake gate for external return packages: `verify` compares the package zip against its md5 sidecar (a 32-hex string or sidecar file) and md5sum-line manifest member by member, printing the per-file evidence list to stdout (ok / mismatch / missing / unlisted / declared-surface / dir / info plus a summary line; any mismatch or missing declared member is fail-loud rc=1); `intake` re-runs the same comparison (a red result refuses and writes nothing) and, only on green, appends exactly one register row (schema `rocqwash-uplink/1`, six fields `package` / `source-seat` / `md5` / `verified` / `landed-ref` / `exit`, verified rows only, duplicate-skip idempotent on identical parameters, `--dry-run` reports the would-append line and writes nothing); `pr-prep` renders the pull-request description draft of one register row (verified rows only, zero git calls, never opens a pull request). The zip reader is self-contained (central directory plus RFC 1951 inflate, stored and deflate members, CRC-32 checked); ZIP64, encrypted, unknown-method, multi-disk, and over-budget (2 GiB) archives are structured refusals rc=9. Deterministic byte-identical output; no clock in the logic (the register schema carries no timestamp). No network face by design (all exchange rides offline files; the NETRED register row states no network by design).
- Invocation: `python tools/uplink.py [--selftest] {verify,intake,pr-prep} --package P.zip [--digest HEX|SIDECAR] [--manifest M.md5] --source-seat SEAT --landed-ref REF [--register PATH] [--dry-run] --out DRAFT.md [--signature LINE]` (`--register` and `--registry` are dual spellings of the same slot; the verify face needs `--digest` or `--manifest`, at least one; the intake face also needs `--source-seat` and `--landed-ref`; the pr-prep face needs `--out`)
- Example: `python tools/uplink.py verify --package return.zip --manifest MANIFEST.md5`
- Imports: argparse, hashlib, json, os, re, sys (all standard library)
- Network face: zero (three channels, zero hits; no network by design)
- SKIP face: exit 0 = green terminal state (appended / duplicate-skip / dry-run / draft written); 1 = fail-loud (mismatch / missing member / unverified row / selftest vector error, zero silent skips); 2 = usage, IO, or illegal input content (a non-zip package, a malformed manifest line; refusing to read a damaged register row is not in this class); 9 = missing input or structured refusal (package / sidecar / manifest absent, register row bad JSON, ZIP64, encrypted, unknown compression method, multi-disk, over budget); write faces = the intake register file (default `docs/uplink-intake.jsonl`) plus the pr-prep `--out` file, zero other bytes in the repository tree (the shape test asserts a whole-tree checksum); `--selftest` runs 19 frozen vectors on temporary fixtures (zero writes outside the fixtures)

### tools/vacgen.py
- Purpose: Lean vacuity probe skeleton generator with a four-layer shape-recognition engine (premise decomposition, taxonomy lookup, confidence scoring, tiered harness), including a zero-compile coverage preflight and a difficulty map (`--preflight-all`); present on disk at census time and newly added to tools/, self-described as v2 in its docstring.
- Invocation: `python tools/vacgen.py [--in] [--out] [--toolchain] [--snapshot] [--audit-id] [--name] [--worktree] [--lake] [--guard] [--core] [--force] [--taxonomy] [--preflight-all] [--census] [--root] [--cluster-table] [--report] [--exp-draft] [--verify-anchors] [--mathlib]`
- Example: `python tools/vacgen.py --in <value> --force`
- Imports: argparse, datetime, fractions, hashlib, json, os, re, sys (all standard library; the file header self-describes zero third-party dependencies)
- Network face: zero
- SKIP face: lean/lake/mathlib/elan word face (64), cpu_guard word face (3); the skeleton-casting face runs zero-compile, the compile-verification leg needs a Lean toolchain (a design SKIP face)
- Note: the integration and route faces are in §3.3.

### tools/verdict_diff.py
- Status: [live](missing-entries supplement cast, November 20, 2026: transcribed from the live `python -I tools/verdict_diff.py --help` word face (rc=0) and the module docstring, `verdict_diff.py:2-31`, at HEAD `0765d671`; not a census product; the INDEX integration increment rides the census lane's own re-run)
- Purpose: mechanical judge for vacuity probe sweep results: merges the per-lane sweep ledgers (canonical five-column form batchId|idx|probe|status|rc) into one judgment table with the canonical verdict buckets GREEN / ALERT / BLOCKED / MISSING / SKIPPED-TIERT plus a named exception list, records lane conflicts (same key with differing rc or status resolves max-lane, later glob order wins, and stays on the conflict list), and with `--baseline` diffs two judgment tables under the baseline-diff convergence caliber (the verdict reads only failing-key movement: fewer failing is converged); judged per item (batchId|idx): ALERT = any canonical falsify rc=0 (stop-work freeze, judge side of the double gate with `lean_sweep.py`'s lane marker); BLOCKED = witness or boundary fired with rc != 0; GREEN = witness rc=0 AND all five canonical falsify forms at rc=1 AND boundary rc=0 or SKIP-TIERT (a tier-skipped boundary stays GREEN and is listed in the SKIPPED-TIERT annotation bucket, an item appears in exactly one primary bucket); MISSING = expected item with zero rows (only with an expected universe via `--expected` or `--batches`, otherwise declared not-computed); EXCEPTION = every unjudgeable shape, each with a reason; report schema `rocqwash-verdict-diff/1`; deterministic, no wall clock on the report face.
- Invocation: `python -I tools/verdict_diff.py --results-lane GLOB [--expected F | --batches B.json] [--baseline OLD.json] [--json F] [--md F] | --selftest` (`--results-lane` is a glob such as `DIR/results-lane*.tsv`; `--expected` and `--batches` are alternatives feeding the MISSING face; `--json` writes the report, `--md` the human-readable table)
- Example: `python -I tools/verdict_diff.py --results-lane <value> --json <value> --md <value>`
- Imports: argparse, glob, json, os, sys (module level; `shutil`, `subprocess`, `tempfile` sit at function level inside the selftest harness)
- Network face: zero (the doc face states zero network and zero compile; lane-ledger reading and judgment are local file work)
- SKIP face: exit 0 clean table; 1 failing data (BLOCKED / MISSING / EXCEPTION, or baseline degraded; a failing result is data, loud on stdout); 2 ALERT freeze gate (stop-work) or usage or malformed form (the banner names which); 9 missing input path; lane-ledger readers tolerate rows with extra columns and count malformed rows loud instead of dropping them silently; only the canonical forms full / point / tactics / noclassic / band judge GREEN, legacy faces land in the exception list
- Note: `--selftest` is documented on the doc face and dispatched via `sys.argv` before argparse (`verdict_diff.py:597-598`); the argparse flag face (6 flags) does not list it (the `net_probe` precedent form).

### tools/wash_shape.py
- Purpose: Shape-normalizing five-stage pipeline for annotation faces (header maps and presets, multi-round loop, and event stream parameterized). Integration note (engine-body ticket, at integration): wash 6 (`jargon`) was added (`tools/jargon_apply.py` machine-writes replace entries) and wash 7 (`ai-flavor`, advisory: the plan lists suggestions, `--apply` only emits the handoff segment package, writes ride the rewrite-provider round-trip); `--only` accepts `jargon` / `ai-flavor` / `6` / `7`; `--dir` also collects the .py/.sh/.md (.json/.ts) prose faces when either wash is selected.
- Invocation: `python tools/wash_shape.py [--file] [--dir] [--exclude] [--only] [--header-map] [--header-map-preset] [--anchor-src] [--repo-root] [--json] [--apply] [--loop] [--interval] [--sleep-scale] [--max-rounds] [--events] [--injector]`
- Example: `python tools/wash_shape.py --file <value> --apply`
- Imports: argparse, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, time
- Network face: zero
- SKIP face: the `ROCWASH_HEADER_MAP` environment variable, coq family word face (6)

### Aggregates for this section

Aggregates transcribed from census §4 (each line is a word-face fact at census time):

- Argparse face: 25/27 files carry an argparse import and a flag face; 2 files (`_abl1_4b_compile.py`, `_http_backoff.py`) have no argparse, their invocation form restored from usage strings (the former parses `sys.argv` positional arguments by hand, the latter documents `--selftest` on its doc face).
- Subcommand face: zero `add_parser` word-face hits across all 27 files (per-file AST scan): all are flat flag forms with no subcommand routing face.
- Network face: 22/27 files with zero hits across the three word-face channels; 5 non-zero (ci_triage, cw_sentinel, net_probe, pushci carry transport-class imports; contrib_intake carries the git `clone` subprocess token face).
- Special-environment face: 18/27 files hit at least one marker family; 9 carry no marker at all (baseline_diff, chain_graph, doc_lint, ledger_sync, netname_normalize, norm_lint, render_events, _http_backoff, plus net_probe which needs only a network window).
- Docstring face: 27/27 files carry a file-header docstring; the verbatim text is recorded in the JSON.
- Dependency face: all 27 files import standard-library or in-repo modules only, zero third-party dependencies; two in-repo cross-directory references (`evolve.py` to `certify/frozen8.py`, `_gen_fin_mac.py` to `names/mac_stmt_names.py`, both via sys.path injection) and one in-repo same-directory shared helper (`tools/_http_backoff.py`, imported by the three network tools).
- `--selftest` token face: 24/27 files carry the `--selftest` word face in source; norm_lint and red_dispatch carry an argparse flag position, net_probe dispatches manually via argv (see the §2 note), and the flag positions of the rest await the light-probe check.
- Internal-item convention: the 3 files whose names begin with `_` (`_abl1_4b_compile.py`, `_gen_fin_mac.py`, `_http_backoff.py`) self-describe as internal helper/shared items, consistent with their names.
- File size span: 3,451 B to 122,111 B; line counts 80 to 2,625.
- `vacgen.py` is a newly added file under tools/ (present on disk at census time; the earlier external account was a 23-tool snapshot; this census tabulates the current 27 files item by item, compatible with the 28/25 bookkeeping in section 6 of the reconciliation receipt: 28 = 27 py + cpu_guard.sh).

## 3. Tail

### 3.1 Negative-Finding Boundaries (four elements)

Each item below is a negative finding of that scan, not an absolute claim (transcribed from census §5).

**5.1 "zero third-party dependencies"**
1. Scanned: the module names of all import statements across the 27 files, compared three ways against the set of stdlib module names, the same-directory file names under tools/, and the full-repo `.py` file-name set (AST word face, November 14, 2026).
2. Not scanned: runtime dynamic imports (`importlib` / `__import__` call faces not dug into one by one); non-Python dependency faces (the shell environment `cpu_guard.sh` needs).
3. Not an absolute claim: only this word-face scan's zero third-party module-name hits are claimed.
4. Aliases not exhausted: import forms that build module names by dynamic string concatenation are not exhaustively ruled out.
Re-check condition: re-scan whenever a file is added under tools/ or this census re-runs.

**5.2 "22 files with a zero network face"**
1. Scanned: transport-class import faces (socket/ssl/urllib.request/http.client/requests and similar lists), subprocess-bridge token faces (curl/wget/api host names), and git network-subcommand token faces (push/fetch/clone/pull/ls-remote, three channels; November 14, 2026).
2. Not scanned: actual runtime connection behavior; dynamically constructed host names and URLs (f-string assembly forms not semantically restored one by one); the network behavior of the external programs these tools call (coqc/lake/git bodies).
3. Not an absolute claim: only this three-channel word-face scan's zero hits are claimed, not "these tools are necessarily zero-network at runtime".
4. Aliases not exhausted: endpoint injection through environment variables and network calls through shell aliases/wrapper scripts are not exhaustively ruled out.
Re-check condition: re-check together with the light-probe step measuring `--help` and exit codes; re-scan after tool versions advance.

**5.3 "zero subcommand face"**
1. Scanned: a whole-tree AST scan of `add_parser` call faces across the 27 files (0 hits).
2. Not scanned: non-argparse manual subcommand routing (`sys.argv[1]` branch-routing forms) not dug into file by file.
3. Not an absolute claim: only the argparse subcommand mechanism's word-face zero hits are claimed.
4. Aliases not exhausted: subcommand semantics carried by flag combinations (such as `--steps`, `--mode`) are not exhaustively ruled out (pushci's flag face carries `--steps`, semantics pending the light probe).
Re-check condition: re-check when the light-probe step spot-checks flag semantics.

**5.4 "18 files with special-environment faces"**
1. Scanned: word-face counts and samples for the 9 marker families (ocaml/opam, the coq/rocq family, lean/lake/mathlib, macOS dyld tooling, the Windows guard, GPG, cpu_guard thermal, self-hosted runner, `ROCWASH_*` environment variables).
2. Not scanned: real runtime environment needs; dynamically assembled environment-variable names (`"ROCWASH_" + suffix` forms) not exhaustively ruled out.
3. Not an absolute claim: marker hits are word-face facts, not proof of "required at runtime"; some sample hits come from comment and help vocabulary faces (e.g. ci_triage's coq word face is mostly log-parsing vocabulary).
4. Aliases not exhausted: other environment-dependency forms (containers, specific shells, PATH layouts) not systematically surveyed.
Re-check condition: verify item by item at the light-probe step and at later real invocations.

### 3.2 Zero-Network Declaration


**Cast face (this file itself)**: this file was cast with zero network. Casting actions were limited to: word-face reads of the pinned clone (the census AST face, the AST flag-shape face, read-only `git show --stat` and `grep` commands) and 8 local light probes (`--help` on 7 tools, `--selftest` on 1, local processes, no network); no network call occurred during casting.


**Per-item face (network reading of the 27 tools)**: the 22 zero-network readings are negative findings of the three-channel word-face scan, not absolute runtime claims; the four elements are in §3.1 item 5.2. For the five tools with a non-zero network face (ci_triage, cw_sentinel, net_probe, pushci, contrib_intake), callers must assess the network window and remote access rights against each SKIP face before invoking. The re-check conditions of §3.1 item 5.2 and the light-probe ledger (§4) apply together; re-scan after tool versions advance.

### 3.3 vacgen Section (integration note)

- **Landing facts (first-hand measured)**: `tools/vacgen.py` landed on November 13, 2026 via graft commit `5829f6d` (the version anchor of this file). `git show --stat` measured four files: `tools/vacgen.py` 2,625 lines, `docs/vacgen_sop.md` 384 lines, `tests/t_vacgen_shape.py` 51 lines, `更新账.md` +1 line. Landing-package note: RQW02.
- **Two faces**: a zero-compile face (skeleton casting runs without a Lean environment) plus a compile-verification leg (needs a Lean toolchain, a design SKIP face); the three-channel word faces (lean/lake/mathlib/elan, 64 hits) and the SKIP face are transcribed in the §2 vacgen entry. Detailed procedure = `docs/vacgen_sop.md`; shape regression selftest = `tests/t_vacgen_shape.py`.
- **Route face (re-measured November 14, 2026, current)**: the cw.sh vacgen branch has landed (commit `8e04cc6`, all four places present: header table / usage / hint_for / case; `grep -c vacgen cw.sh` = 6 measured); both `bash cw.sh vacgen ...` and the direct `python tools/vacgen.py ...` invocation forms are valid.
- **CI anchor**: the run at this head, #43421710372, concluded success (reconciliation receipt channel N3, measured November 13, 2026; the three prior runs at earlier heads were all success).

### 3.4 Provenance

- Scan tree: pinned clone `D:/ComplexAnalysis/rocqwash` at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85` (measured locally via `git rev-parse HEAD`, November 14, 2026; working tree porcelain 0 lines).
- Per-item source: `census.md` plus `census-tools.json` (with per-file sha256 anchors; builder `census_tools_build.py` in the same directory, stdlib-only, `python -I`).
- Example flag-shape basis: `flag_shape_probe.py` (AST-level read-only pass; no tool executed or imported) produced `flag-shape.json`; five counter-intuitive flags (`--offline`, `--stable-window`, `--suite-now`, `--fix-plan`, `--once`) were additionally spot-checked at source-line level, agreeing with the AST reading.
- Cast time: November 14, 2026.

Re-scan generation (November 20, 2026), the four lines above kept as written for their own time:

- Scan tree: working tree `D:/ComplexAnalysis/rocqwash` at HEAD `0765d671a63193430de86faf3a9790f2d8a086a0` (`git rev-parse HEAD` immediately before the scan; `origin/main` equal at this sha per the count cross-table; working-tree porcelain at scan time: 2 designed live-state rows, `round-plan.json` and `docs/exp-ledger.jsonl`, read-only for the census).
- Per-item source: `docs/census.md` plus `docs/census-tools.json` (59 files, per-file sha256 anchors; JSON sha256 `b5850d9bb32c5081e3a2e3318c035ffc605eb2ece085919ffc9d55383fc8e301`) plus `docs/flag-shape.json` (59 records; sha256 `bf1745afa63604d52e45d0ec7614cc9c78cf7b84735a4eec0b808d5d5c3faa4c`); the builder `census_tools_build.py` (the November 14, 2026 cast instrument, run unmodified; stdlib-only, `python -I`) now sits in this directory beside the outputs.
- Example flag-shape basis: `flag-shape.json` of this generation (AST-level read-only pass; no tool executed or imported).
- Cast time: November 20, 2026 (UTC timestamp in `census-tools.json` field `meta.generated_at_utc`).

## 4. Light-Probe Ledger

Measured November 14, 2026; command form `python -I tools/<name>.py --help` (run from the pinned clone root); rc and output face recorded per item. Light tools only; the five network-face tools and special-environment/heavy tools are marked SKIP and not probed, awaiting the later verification pass.

| # | Tool | Command | rc | Output face (head) | Verdict |
|---|---|---|---|---|---|
| 1 | baseline_diff.py | `--help` | 0 | `usage: baseline_diff [-h] [--json out.json] [--md out.md] OLD.json NEW.json` | PASS, matches the invocation form; the two positional arguments render as metavar `OLD.json` / `NEW.json` |
| 2 | chain_graph.py | `--help` | 0 | `usage: chain_graph [-h] [--json out.json] [--md out.md] [--top N] [LEDGER.json ...]` | PASS, matches |
| 3 | doc_lint.py | `--help` | 0 | `usage: doc_lint [-h] [--repo DIR] [--json out.json] [--help-cap N]` | PASS, matches |
| 4 | ledger_sync.py | `--help` | 0 | `usage: ledger_sync [-h] [--probe FILE] [--ledger FILE] [--out FILE] [--report FILE] [--policy {unprobed-only,annotate-only}]` | PASS, matches; `--policy` carries a choices face |
| 5 | render_events.py | `--help` | 0 | `usage: render_events [-h] [--events FILE.jsonl] [--dir DIR] [--md out.md] [--json out.json] [--top N]` | PASS, matches |
| 6 | norm_lint.py | `--help` | 0 | `usage: norm_lint [-h] [--tree DIR \| --file PATH] [--jargon-map JARGON_MAP] ...` | PASS, matches; `--tree`/`--file` form a mutually exclusive group |
| 7 | netname_normalize.py | `--help` | 0 | `usage: netname_normalize [-h] [--dir DIR] [--apply] [--map out.tsv] [--json JSON]` | PASS, matches |
| 8 | _http_backoff.py | `--selftest` | 0 | selftest PASS on one line (backoff sequence / cap / retry face / Retry-After subitems all pass) | PASS, the usage-face documented form holds |


Probe-side details (measured `--help` face, absent from the census word face): `--json` is value-taking repo-wide (examples show `--json <value>`); `ledger_sync --policy` choices are `{unprobed-only, annotate-only}`; `norm_lint --tree`/`--file` form a mutually exclusive group. All three are first-hand facts of the `--help` output face, with no contradiction against the census invocation face.


SKIP (not probed by this agent, awaiting the later verification pass): the five network-face tools ci_triage / cw_sentinel / net_probe / pushci / contrib_intake (their runs need a network window or remote access); special-environment/heavy tools _abl1_4b_compile (usage face; a bare call triggers the compile face), _gen_fin_mac, cw_doctor, evolve, red_dispatch, registry_audit, registry_fix, registry_regen, registry_union, select_audit, toolchain_dyld_doctor, unclog, vacgen, wash_shape. The `net_probe` `--selftest` divergence (§2 note) also awaits that step.

### 4.1 Follow-up probes

Measured November 14, 2026 against HEAD `8e04cc6f9b6ee118e8e2729e9ae3edd6a163bf79`. The census anchor above stays the cast-time anchor; this block extends the light-probe ledger without re-casting the census, and the caller duty at §0 governs re-checks after HEAD advances. Uncommitted worktree lanes were held by a concurrent integration during measurement (recorded, not attributed).

- `evolve.py` help probe rc=0: the §2 entry line matches the live help face (all 19 flags present, no incompatible names).
- One full evolve round via the §2 example line: rc=0, stdout `evolve rocqwash-evolve/1: signals=3 candidates=5 drafted=5` (baseline + suite-now + maintained sentinel events/state inputs; draft and report written to the caller's work directory).
- The §2 registry pair aimed at this tool repo: rc=9 fail-loud REGISTERED (git show main:order.txt fatal: path does not exist): `git ls-tree main` carries no order.txt and no _CoqProject anywhere in the tree; the registry signal stays pointed at the serviced books only.
- Suite face, bash form: 51 pass / 12 failing / 4 skip / 67 total, rc=1; the 12 failing cases are lane-level and tool faces registered in the cycle accounts (Windows-lane environment faces for dyld/taskpolicy, the wash_shape report fd face, the unclog cure md5 text-mode face, the red_dispatch selftest vector face, the registry_audit reanchor-order face, and the probe/verify faces owned by their own lanes). The ask's literal interpreter form against a `.sh` file is a category error (Python parses the script); the bash form is the executable face.

## 5. Register Self-Check Assertion

The authored text of this file was checked with the instrument `ai_flavor_selfcheck.sh` (36 wording faces plus the em-dash U+2014 battery; register source: glossary §4.6/§5), target = this whole file. Measured output is appended below at closing time.

Credential-face check (value-shape regex and bare-literal passes, grep over this file): 0 hits; no credential value or credential wording anywhere.

Measured output (closing time):

```
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

Execution: `sh ai_flavor_selfcheck.sh CAPABILITY-INDEX.md`, exit 0. Instrument copy: `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh` (cast November 12, 2026, the same instrument as the census).

Transcription-fidelity checks (closing time): census §3 five-field lines 135 = 135, diffs=0; negative-finding four-element rows 16 = 16, diffs=0; entry count / example lines / SKIP face 27 = 27 = 27; all 7 light-probe `--help` flag faces present (baseline_diff positional arguments render as metavars).

## 6. Anchor-lag register (growth cycle 3)

Register note (November 15, 2026, work stream-2 annotation closeout): the version anchor at the top advanced to `d6d0ec7` (the engine-body batch integration commit) as a construction-base annotation. The census cast stays pinned at `5829f6d`; no census re-scan ran (the census re-scan awaits the next work stream). The cycle-3 entry below is kept as written for its own time.

Cycle-3 entry, kept as written: the version anchor then at the top (5829f6d) lagged the working-tree HEAD (8e04cc6) by seven commits. Facts measured on the lagged state, per the caller duty in section 0:

- Committed tool count at HEAD is 28 `.py` files under `tools/` (`git ls-tree HEAD tools/`), one above the census count 27 recorded in section 1: `tools/mcp_server.py` was added after the census snapshot. Its contract face is reachable directly (`python -I tools/mcp_server.py --help`; the capability mapping is documented in `docs/mcp.md`). A census-grade entry awaits the census lane's own re-run; this register deliberately does not hand-write one.
- Two further tools sit on disk untracked: `tools/exp_port.py` (experience-bus port, schema rocqwash-exp/1, `append`/`query` faces plus `--selftest`) and `tools/periscope.py` (collection legs; operation manual at `docs/periscope_sop.md`). They join the index only once their own commits exist on the tracked face.
- Consequence for callers: entries in section 2 stay valid for the 27 censused tools at their recorded faces; for the three faces above, invoke from each tool's own `--help` word face and record the HEAD used, exactly as the caller duty requires.
