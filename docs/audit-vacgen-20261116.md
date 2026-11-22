# Audit scroll: the specialized audit of `tools/vacgen.py` (batch 3 · supplementary-audit agent `G4`), verified November 16, 2026.

> Purpose.  Read-only specialized audit of `tools/vacgen.py` (2877 lines, the largest single file in the repository, TOOL_VERSION 2.1.0) and its companion faces. The scroll registers findings only, as candidate repairs; it applies no repair to the tree.
> Interface.  Document face only. Audit agent: batch 3 supplementary-audit agent `G4` (read-only, zero changes; this scroll is the only face the audit wrote). Method: a full line-by-line read of vacgen.py (2877 lines), full reads of every companion face, 14 first-hand probe rounds (the three selftests, the t_refinery aggregate, and the CLI rc / mutual-exclusion / idempotence / --force / malformed-taxonomy / def-head front check / voided rows / anchor drift / preflight end-to-end / census face check / --report / --exp-draft probes), plus grep reference scans. Grading: HIGH (a guard promise unmet or a contract break) / MEDIUM (an inert check face, split accounting, a broken fail-loud form) / LOW (dead code, wording, pointer drift). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Subject face `tools/vacgen.py`; companion faces `tests/t_vacgen_shape.py`, `tests/t_vacgen_expectedred.py`, `tests/refinery_segments/vacgen.py`, `tests/t_refinery.py`, `tests/run_tests.sh`, `tools/taxonomy.json`, `tools/mcp_server.py`, `docs/mcp.md`, `docs/vacgen_sop.md`, `tools/vacgen_env_note.md`; the update ledger `更新账.md` cited read-only. No runtime dependency.
> Evidence.  Every finding carries the first-hand evidence quoted in its table row (sections 2-5), and every executed run is listed in the section 7 provenance record; line-number anchors bind to the November 16, 2026 verified state. Zero-change declaration: the probes ran against read-only checks and temporary directories, and the only face written into the tree is this scroll.
> Exit-codes.  Not applicable to a document face; the rc values quoted in the tables are the documented tools' observed exit codes, described as implemented.

---

## 0. Overall assessment

- The tool body is healthy: all three selftests pass first-hand (t_vacgen_shape PASS 8 files, t_vacgen_expectedred 3 pass / 0 red, the refinery vacgen segment 14 pass / 0 fail), and the t_refinery aggregate is 59 pass / 0 fail; the three-mode CLI trunk contract (mutual exclusion, missing-parameter fail-loud, idempotent no-op, difference FAIL-LOUD, --force overwrite, the census face check, voided-row admission, anchor drift rc=1) conforms to design in every first-hand probe.
- The guard face carries one HIGH gap: `tests/t_vacgen_envelope_shape.py`, registered by the SOP §2.5 erratum as "the only machine-check guard for the implicit-binder engine debt", **is absent from the tree**; run_tests.sh carries only the function body (:1039-1045) and the roster does not register it (:383-384).
- The remaining 5 MEDIUM and 11 LOW items are candidate repairs; see the section 6 ledger.

---

## 1. Surface inventory (verified November 16, 2026)

### 1.1 CLI face (main, vacgen.py:2790-2873)

| Mode | Flags | rc semantics |
|---|---|---|
| cast (default) | `--in --out --toolchain --snapshot --audit-id --name --worktree --lake --guard --core --force` (v1 face, 11) + `--taxonomy --report --exp-draft` (v2 additive) | ok=0; checks red=1; fail-loud (parse/taxonomy/bare-limb/diff targets/write verification)=1; missing `--in` =2 |
| preflight (--preflight-all) | `--census --root --cluster-table --report` | ok=0; missing census/root=1; mutually exclusive with `--in` =1; census face-check mismatch=1 |
| verify-anchors (--verify-anchors) | `--mathlib --taxonomy` | ok=0; drift=1; missing `--mathlib` =1 |

Of the nine v2 flags (--taxonomy/--preflight-all/--census/--root/--cluster-table/--report/--exp-draft/--verify-anchors/--mathlib), when `--verify-anchors` and `--preflight-all` are given together the former is silently swallowed (see L1).

### 1.2 Output face (eight cast files + optional JSON)

- The eight files (vacgen.py:2241-2243): witness.lean / falsify_{full,point,tactics,noclassic,band}.lean / boundary.lean / gap_anchors.txt.
- The boundary record ships in two forms (emit_boundary:1853-1858): numeric (`BOUNDARY_SEATS` C-1..C-6, vacgen.py:1611-1676) / shape-registration (B-R + B-Sn, :1777-1850).
- `--report` JSON schema (do_cast:2343-2378): reportId/tool/in/taxonomy/l1/assumptions/coverage/cast/negativeFinding/experience/verdict{checks(17), ok, strength}.
- `--exp-draft` JSON (build_exp_draft:2456-2493): draftId/tool/date/entries (todo-family pitfall entries + canonical-form entries).
- preflight output difficulty map (:2678-2701): mapId/censusId/headPin/taxonomy/calibration/bandDefinitionBytes/files/aggregate/negativeFinding/generatedAt.

### 1.3 Engine layers (L1-L4)

- L1 decomposer: lean_strip_comments/iter_code_lines (dual-implementation comment stripping, :105-162), scan_balanced/find_decl_end/find_top_colon (:165-224), parse_binders/split_instance_binder (:493-545), looks_like_type family (:243-340), collect_variable_commands (G1, :404-447), relevant_scope_binders (R-1 v3, :360-401), decompose_head (C4.2 front check, :569-633).
- L2 taxonomy-as-data: validate_row/load_table/load_taxonomy/resolve_taxonomy_path (:834-952, four-priority chain flag > VACGEN_TAXONOMY env > tool-adjacent > builtin starter row), classify_record (first-match + hole interception + requireVarBinding, :978-1015).
- L3 scoring: tier_of/tier thresholds 80/50 (:1032-1040), band_of (S/M/L, :1052-1057), budget_minutes (:1060-1061), negative_finding_block four elements (:1064-1077).
- L4 cast: Cast class + emit_witness/emit_refutation×5/emit_boundary×2/emit_gap_anchors (:1270-1956), run_checks v1 eleven checks (:1965-2026), run_checks_v2 six checks (:2029-2079), idempotence (cast-epoch masking, :2284-2323), strength_face/W6 battery (:1088-1167).
- preflight: preflight_all (:2528-2741), load_cluster_table/classify_cluster (stratify.py parity, :2498-2525).
- verify-anchors: do_verify_anchors (:2744-2785).

### 1.4 Data face and consumer faces

- `tools/taxonomy.json` (verified 2 rows: ineq.real.const-lt-field-re / concl.real.const-lt-field-re-exists; the anchorVerifiedAt key is absent).
- `tools/mcp_server.py:207-247` vacgen_generate (arg_map, 11 parameters, see M4).
- `tests/run_tests.sh`: roster :383-384 (t_vacgen_shape / t_vacgen_expectedred) + t_refinery; function bodies :1023-1045 (including the dangling t_vacgen_envelope_shape, see H1).
- `tests/refinery_segments/vacgen.py` (402 lines, the refinery test segment; same name, not a copy; dynamically loads tools/vacgen.py; 14 checks).
- Documentation faces: docs/vacgen_sop.md (the verdict-procedure source of record + the §2.5 erratum), tools/vacgen_env_note.md (deployment-constant note), docs/mcp.md:55, docs/en/vacgen.md, the README family, the update ledger `更新账.md`.

---

## 2. Dead-code scan

| # | Symbol | Location | First-hand evidence | Grade |
|---|---|---|---|---|
| L4 | `PREMISE_INEQ_RE`, `CONST_ALT` | vacgen.py:266-272 | `grep -n "PREMISE_INEQ_RE\|CONST_ALT" tools/vacgen.py` returns only 4 hits: 2 definition lines + 3 comment mentions (:795/:822/:824, all "v1 transcription provenance" notes), zero code references. After the v2 data conversion, parsing goes through resolve_numeric_boundary's `_top_level_char` manual slicing plus parse_const_fraction's own regex | LOW |
| L5 | `envelope_prefix_segments` | vacgen.py:699-704 | Zero calls in the main flow (do_cast/run_checks_v2/envelope_statement); the only consumer is tests/refinery_segments/vacgen.py:185/197/209 (the three p25 pins). A test-only export face, not strictly dead code, but the tool has no consumer for it and no comment declares that role | LOW |
|; | Remaining full def sweep | whole file | Every symbol checked against its consumers (do_cast/preflight/verify/main/run_checks family/emit family/test segment); all remaining symbols have live references; no unwired output |; |

---

## 3. Exception-handling audit

| # | Location | Observed behavior | Grade |
|---|---|---|---|
| M1 | `load_taxonomy` vacgen.py:926-927 | `json.load(fh)` and the file open sit outside the TaxonomyError wrapping. First-hand: `--taxonomy <malformed JSON>` → rc=1 but a bare `json.decoder.JSONDecodeError: Expecting value` traceback (probe f), with no `FAIL-LOUD: taxonomy:` marker line; the except clauses at main:2860-2864 and do_cast:2103-2107 catch TaxonomyError only. Sibling OSError cases (permissions/lock) escape bare the same way. Violates the greppable marker form of the self-declared contract "row admission fail-loud (rc=1, section 6.2)" | MEDIUM |
| L9 | `do_cast` vacgen.py:2087-2091 | TOCTOU race window between the `os.path.isfile` check and the open: if the file passes isfile and is deleted before open, OSError escapes bare (UnicodeDecodeError is already wrapped at :2093-2097). Extremely low probability; registration is enough | LOW |
| L8 | `classify_record` vacgen.py:995-998 | `except re.error: hit = False`; entry["rx"] already compiled successfully at load_table:892, so re.error is unreachable at search time; a defensive dead branch (if it ever fired, the error would be swallowed into a silent miss). Harmless; registered | LOW |
|; | Remaining exception faces | Verified healthy first-hand: UnicodeDecodeError (fail-loud line), preflight per-file OSError/UnicodeDecodeError (counted UNPARSED without aborting, :2571-2577/:2652-2656), cluster table (OSError/ValueError/re.error, :2546-2550), do_verify_anchors OSError (:2766-2767), refinery segment check surfaces (:157-166, fail-loud listing) |; |

---

## 4. CLI contract audit

### 4.1 First-hand probe record (every row executed first-hand in this audit)

| Probe | Command shape (excerpt) | Measured rc | Measured output | Reading |
|---|---|---|---|---|
| a no arguments | `py -B tools/vacgen.py` | 2 | `FAIL-LOUD: --in is required in cast mode` | conforms (usage=2) |
| b preflight missing parameters | `--preflight-all` | 1 | `FAIL-LOUD: --preflight-all requires --census ... (usage error, rc=1)` | conforms, but self-describes as usage while rc=1 (L2) |
| c mutual exclusion | `--preflight-all --in x --census c --root r` | 1 | `FAIL-LOUD: ... mutually exclusive with --in` | conforms |
| d verify missing mathlib | `--verify-anchors` | 1 | `FAIL-LOUD: --verify-anchors requires --mathlib <root>` | conforms |
| e both modes given together | `--verify-anchors --preflight-all` | 1 | only the preflight missing-parameter error appears; verify-anchors gets zero mention | **L1: silently swallowed** |
| f malformed taxonomy | `--in ok.lean --taxonomy <broken>` | 1 | bare JSONDecodeError traceback | **M1** |
| g def-only head | `--in <def foo ...>` | 1 | `non-theorem-declaration: head 'def foo' ... C4.2 front gate` | conforms (C4.2 check live) |
| h idempotence | same arguments, two runs | 0/0 | `re-cast detected ... no-op (zero rewrite)` | conforms |
| i refuse write on difference | modify witness.lean on disk, rerun | 1 | `FAIL-LOUD: existing target files differ ... witness.lean` | conforms |
| h4 force | add `--force` | 0 | `cast complete: 8 file(s) written` | conforms |
| j report/exp-draft | `--report --exp-draft` | 0 | checks:17 ok:True strength.grade:full; exp entries:1 (canonical form) | conforms (but see L6 for the comment face) |
| k preflight end-to-end | census + root on a small tree | 0 | tierCounts C=1, difficulty map persisted, ok=true | conforms (accounting see M3) |
| l census face check | summary=2 vs list=1 | 1 | `FAIL-LOUD: census face mismatch` | conforms |
| m voided admission | 1 bad + 1 good taxonomy row | 0 | `rowsLoaded: 1 \| rowsVoided: 1` + per-row errors | conforms |
| n anchor drift | bogus mathlib root | 1 | `anchors checked: 2 \| drifted: 2` per-row DRIFT | conforms (wording gap L3) |

### 4.2 Contract gaps

| # | Finding | Evidence | Grade |
|---|---|---|---|
| M3 | **The L3 coverage denominator accounting splits across modes**: the cast denominator = records+conclusion+additional degraded (:2181, counted once); the preflight denominator = file_total+file_todo = r+2u+e (:2615/:2618, unrecognized faces counted twice). Verification: for the same zeta-family face, cast coverage=50% (1/2, probe j) while preflight reports 0/6 for A.lean (probe k). The difficulty map's coverageLowerPct/tier carry different values than the cast report for the same face; the self-declared "lower bound" on the preflight side is an accounting difference, not a more conservative bound | vacgen.py:2181 vs :2615/:2618; probes j/k | MEDIUM |
| M2 | **scanned_vs_declared_upper_bound passes unconditionally (an inert check face)**: fill_ledger's declared_sorry and scanned_sorry are the same expression evaluated twice (:2269-2270), so run_checks:1988-1990's `scanned > declared` is always False; one of the eleven v1 checks always PASSES, and the real "scanned-face sorry exceeds the declaration" defect is undetectable | vacgen.py:2269-2270/:1988-1990 | MEDIUM |
| L1 | `--verify-anchors` + `--preflight-all` given together: the preflight branch (:2851-2865) returns first and verify-anchors is silently swallowed | vacgen.py:2851-2867; probe e | LOW |
| L2 | Usage-error rc semantics inconsistent: missing `--in` → rc=2 (:2868-2871); missing `--census/--root` → rc=1 while self-describing as "usage error, rc=1" (:2856-2858). The sibling sweep segment's contract habit is usage=rc2 | vacgen.py:2851-2871; probes a/b | LOW |
| L3 | do_verify_anchors prints "affected rows are voided per C3.3" but the implementation only prints the report, with no void write to disk (the table stays static; later casts still load drifted rows in full) | vacgen.py:2779-2783; probe n | LOW |
| M4 | **The MCP vacgen_generate parameter face lacks the nine v2 parameters**: arg_map carries 11 parameters only (mcp_server.py:213-225), without --census/--root/--taxonomy/--cluster-table/--report/--exp-draft/--verify-anchors/--mathlib. Probe b confirms `--preflight-all` without census/root necessarily rc=1, so MCP-side preflight_all=true has no parameter path and must fail. The docs/mcp.md:55 parameter table lacks the same set, consistently with the wiring (document and wiring agree, and both are broken). The candidate repair must be additive (extend arg_map + sync docs/mcp.md); the existing signature must not move (do-not-disturb list rule 1) | mcp_server.py:213-225; docs/mcp.md:55; probe b | MEDIUM |

---

## 5. Selftest coverage audit

### 5.1 First-hand run results

| Item | Command | Result |
|---|---|---|
| t_vacgen_shape.py | `py -B tests/t_vacgen_shape.py` | PASS: four-account skeleton present (8 files) · rc=0 |
| t_vacgen_expectedred.py | `py -B tests/t_vacgen_expectedred.py` | 3 pass / 0 red · rc=0 (Lean compile leg design-SKIP) |
| refinery_segments/vacgen.py | `py -B tests/refinery_segments/vacgen.py` | 14 pass / 0 fail (import face + p25×5 + w5×5 + w6×3) |
| t_refinery.py (aggregate) | `py -B tests/t_refinery.py` | SUMMARY segments=6 passed=59 failed=0 skipped=0 |

### 5.2 Guard gaps

| # | Finding | Evidence | Grade |
|---|---|---|---|
| H1 | **t_vacgen_envelope_shape has a three-part gap (the known-debt machine-check guard is unmet)**: (a) the file `tests/t_vacgen_envelope_shape.py` is absent from the tree (`find` over the whole repository for `*envelope*` returns zero hits); (b) run_tests.sh:1039-1045 carries a function body that would execute that path, but the CASES roster (:383-384) does not register it, leaving the function dangling dead code; (c) docs/vacgen_sop.md:283-293 (the §2.5 erratum) claims the test landed and is "the only machine-check guard registering the engine debt" (the run_tests.sh:1041-1043 comment says the same). Consequence: the implicit-binder envelope engine debt (registered unrepaired in SOP §2.5) is currently in a zero-machine-check state, and fixture B's known-debt pin (the `∧ Set (` signature) is missing, so a future engine repair would give no failing signal prompting the pin update | run_tests.sh:1039-1045/:383-384; vacgen_sop.md:283-293; find verify | HIGH |
| M5 | **The taxonomy geo row claimed by SOP §2.5 is absent from the tree**: erratum item 1 (vacgen_sop.md:275-283) says `tools/taxonomy.json` already carries "builtin starter row carried verbatim + geo.symmetric-set-premise row". Verified: tools/taxonomy.json has rows=2, `ineq.real.const-lt-field-re` + `concl.real.const-lt-field-re-exists` (the latter is not mentioned by the SOP; the former shares its id with the builtin, which does not match the "added beyond carried verbatim" wording). The geo row is absent and the Mahler-family L3 improvement path (0/5 → 1/5) is not reproducible from the current tree; the SOP erratum face and the tree mismatch, with no dated erratum block | vacgen_sop.md:275-283; the taxonomy.json verified output | MEDIUM |

### 5.3 Coverage-gap list (zero-test faces; ordering reference for candidate repairs)

1. `--preflight-all` has zero coverage in full mode (census loading / face-consistency check / band / tier / cluster-table / difficulty-map schema); the M3 accounting split sits exactly in this unpinned zone.
2. `--verify-anchors` has zero coverage in full mode (the drift check, the missing --mathlib usage error); the L3 wording gap is unpinned.
3. The taxonomy admission face has zero coverage (voided-row counting, all-invalid fail-loud, empty-table builtin fallback, the FAIL-LOUD form a malformed JSON should produce); M1 is unpinned.
4. The C4.2 non-theorem-declaration front check has zero pins (the def-only rc=1 marker form).
5. The idempotent no-op / difference FAIL-LOUD / --force paths have zero pins (first-run behavior is correct, but no regression guard exists).
6. The usage rc=2 face and the both-modes mutual-exclusion face have zero pins (L1/L2 unpinned).
7. The `--exp-draft` schema face has zero pins.
8. The envelope-debt pin (the H1 file itself).

---

## 6. Candidate repair ledger by severity

| Severity | # | One-line summary | Candidate repair form (smallest diff first) |
|---|---|---|---|
| HIGH | H1 | The envelope-debt pin file is absent from the tree, the function dangles, the roster does not register it | Create tests/t_vacgen_envelope_shape.py (fixture A clean-form pin + fixture B debt pin `∧ Set (`) and register it in the roster; or first register the gap at the run_tests.sh function body |
| MEDIUM | M1 | Malformed taxonomy JSON produces a bare traceback | Wrap `except (json.JSONDecodeError, OSError) as exc: raise TaxonomyError(...)` inside load_taxonomy; zero CLI-face change |
| MEDIUM | M2 | The scanned_vs_declared check passes unconditionally | Change declared_sorry to count from the `TODO-SEAT` declaration comments, restoring the two fields' independence (a v1 check-face semantics restoration; a behavior change must be registered) |
| MEDIUM | M3 | The cast/preflight coverage denominator accounting splits | Align preflight with `total_all = file_total + extras`, or rename the difficulty map fields to distinguish the accounting (a behavior change must be registered) |
| MEDIUM | M4 | The MCP arg_map lacks the nine v2 parameters (preflight_all via MCP must fail) | Additively extend arg_map with nine entries + nine schema fields + sync the docs/mcp.md table; do not touch the existing signature (MCP do-not-disturb rule) |
| MEDIUM | M5 | The SOP §2.5 geo-row registration mismatches the tree | Add a dated erratum block to SOP §2.5 registering the current state, or additively add the geo row to taxonomy.json (the taxonomy-as-data canonical form) |
| LOW | L1 | verify-anchors is silently swallowed by preflight | Add a mutual-exclusion FAIL-LOUD to the preflight branch (additive) |
| LOW | L2 | Usage rc semantics inconsistent (2 vs 1) | Unify on usage=rc2 or register the exception |
| LOW | L3 | The verify-anchors "voided" wording has no action behind it | Change the wording to REPORTED, or write the drift list under --report (additive) |
| LOW | L4 | PREMISE_INEQ_RE/CONST_ALT dead code | Delete, or add a v1 provenance comment marker (sync the :795/:822/:824 comment mentions) |
| LOW | L5 | envelope_prefix_segments has no in-tool consumer | Add an "exported for refinery segment test face" comment (keep it; the segment depends on it) |
| LOW | L6 | The comment "v1 eleven + v2 five" describes 6 checks in fact (measured checks:17) | Change the vacgen.py:2325 comment to six (one-word diff) |
| LOW | L7 | env_note line-number pointers have drifted (:67/:68/:70/:66-72/:784-795/:789 all dead; actual 82-88/898-909/903) | Update the line numbers or switch to symbol-name pointers (drift-proof) |
| LOW | L8 | classify_record's except re.error is an unreachable dead branch | Keep (harmless defense) or delete; registration is enough |
| LOW | L9 | TOCTOU race window in the do_cast --in open | Wrap the open in try OSError → FAIL-LOUD line |
| LOW | L10 | The `--exp-draft` output wording "entrie(s)" (:2446) | One-word diff to entry/entries |
| LOW | L11 | An empty preflight M/L band prints tiers=None (:2719-2723) | Print a zero-valued dict for the empty band (cosmetic) |

Observations (registered, not repaired): preflight's `s1_names` sharing across declarations makes the requireVarBinding check looser than cast mode (:2596-2597, fail-open direction); the embedded scan has no Lean string state machine (a `sorry`/`--` inside a string literal would be misread, which sits within the declared honest boundary of the word-level lower bound); SOP §2.5 cites `vacgen.py:640-650` labeled as the 2.0.1 revision, now at 681-696 (historical note).

---

## 7. Provenance: first-hand run record (all runs executed first-hand, November 16, 2026)

```
py -B -c "import sys; print(sys.version)"                  -> 3.12.5
py -B tests/t_vacgen_shape.py                              -> PASS (8 files) rc=0
py -B tests/t_vacgen_expectedred.py                        -> 3 pass / 0 red rc=0
py -B tests/refinery_segments/vacgen.py                    -> 14 pass / 0 fail rc=0
py -B tests/t_refinery.py                                  -> 59 pass / 0 fail rc=0
py -B tools/vacgen.py                                      -> rc=2 (usage)
py -B tools/vacgen.py --preflight-all                      -> rc=1 (usage error rc=1)
py -B tools/vacgen.py --preflight-all --in x --census c --root r -> rc=1 (mutual excl)
py -B tools/vacgen.py --verify-anchors                     -> rc=1 (requires --mathlib)
py -B tools/vacgen.py --verify-anchors --preflight-all     -> rc=1 (verify swallowed, L1)
py -B tools/vacgen.py --in ok.lean --taxonomy <broken>     -> rc=1 bare JSONDecodeError (M1)
py -B tools/vacgen.py --in <def-only>                      -> rc=1 non-theorem-declaration
py -B tools/vacgen.py cast×2 / diff / --force              -> no-op / FAIL-LOUD / overwrite all conforming
py -B tools/vacgen.py --in --out --report --exp-draft      -> checks:17 ok:True grade:full; 1 entry
py -B tools/vacgen.py --preflight-all --census --root --report -> rc=0 C=1, 0/6 (M3)
py -B tools/vacgen.py --preflight-all <census mismatch>    -> rc=1 face mismatch
py -B tools/vacgen.py --in --taxonomy <1 bad row + 1 good> -> rc=0, loaded 1 voided 1
py -B tools/vacgen.py --verify-anchors --mathlib <bogus root> -> rc=1 drifted 2 (L3 wording)
find /d/ComplexAnalysis/rocqwash -name "*envelope*"        -> zero hits (H1)
grep -n "PREMISE_INEQ_RE|CONST_ALT" tools/vacgen.py        -> 2 definition lines + 3 comment mentions (L4)
grep -n "envelope_prefix_segments" ...                     -> 0 in-tool consumers (L5)
```

*Zero-change declaration: everything above is read-only verification and temporary-directory probes; the only face written into the tree is this scroll itself. Line numbers are anchored to the November 16, 2026 verified state.*
