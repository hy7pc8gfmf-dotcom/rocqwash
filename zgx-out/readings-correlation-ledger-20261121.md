# Readings Correlation Ledger: Plan-Side Reading Batches 20261120 (f1b6e27 R1/R2/R3 + 3e18590 R4)

Ticket: R2-10 (readings correlation ledger, read-only analysis)
Seat: readings-correlation-ledger (identity live-lumen, host Darwin arm64)
Date: 2026-11-20
Status: DONE - all 4 ask items executed; every check below was run in this session; zero network used; zero writes to any repo tree (only the two files this ask names were written)
Sources:
- /Users/zuguangzhao/ComplexAnalysis/attn/_log/b1-recursion/R2-3-receipt.md (R1/R2/R3 three-batch record)
- /Users/zuguangzhao/rocqwash/zgx-out/ : b-gate-audit.20261119T221339Z.json, b-gate-audit.20261119T230026Z.json, b-gate-audit.20261119T232908Z.json ; scheduling-feedback.20261119T221339Z.json, scheduling-feedback.20261119T230026Z.json, scheduling-feedback.20261119T232908Z.json ; environment.txt (stamp 232908Z) ; zgx-ledger-proposals.jsonl (4 lines) ; plan-run-f1b6e27-20261120.log, plan-run-f1b6e27-20261120R2.log, plan-run-f1b6e27-20261120R3.log ; pr-description-draft-20261120.md
- /Users/zuguangzhao/ComplexAnalysis/attn/_log/b1-recursion/r4-anchor-3e18590-20261119T234622Z/ : b-gate-audit.json, scheduling-feedback.json (R4 archive)
- /Users/zuguangzhao/ComplexAnalysis/attn/_log/b1-recursion/r4-plan-run.log (R4 batch record, clone rocqwash-loop)
- Read-only local git queries against /Users/zuguangzhao/rocqwash (shallow clone, branch zgx/planface-20261120 @ f1d73e6) and /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop (full-history clone @ 3e18590)

---

## 1. Batch inventory

| batch | collect stamp (UTC) | anchor | clone | record |
|---|---|---|---|---|
| R1 | 20261119T221339Z | f1b6e27f39da80423a059c0d72848eb5e53d74ee | /Users/zuguangzhao/rocqwash | first run; PR#17 same-topic collision -> PR step halted (R2-3-receipt sections 4-6); hard network wall at clone time, worked around via depth-1 sha fetch |
| R2 | 20261119T230026Z | f1b6e27f39da80423a059c0d72848eb5e53d74ee | same clone | second sample; branch zgx/planface-20261120 pushed (07aa91e, GPG-signed); PR create denied (permissions) |
| R3 | 20261119T232908Z | f1b6e27f39da80423a059c0d72848eb5e53d74ee | same clone | third sample; one fetch failure then green retry; branch fast-forward f1d73e6; PR create denied again (same wording) |
| R4 | 20261119T234622Z | 3e185906ae62b17574df7a043394d0b640a51305 | /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop | first cross-anchor run after PR#17 automerge; origin/main moved f1b6e27 -> 3e18590 (97c809f plan-side zgx-out batch + automerge commit); artifacts archived to r4-anchor dir |

## 2. Six-tool comparison table (value by value)

All readings below are quoted from the archived JSON artifacts (steps 1-2), the three R1-R3 plan-run logs (steps 3-6), and the R4 plan-run log (steps 3-6). Each cell is the complete compact reading for that batch.

| # | tool (step) | R1 @f1b6e27 (221339Z) | R2 @f1b6e27 (230026Z) | R3 @f1b6e27 (232908Z) | R4 @3e18590 (234622Z) |
|---|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready_classes 0/3; remaining_to_b=3; concl.real.const-lt-field-re-exists: instances=1 rounds=1 not-ready; ineq.real.const-lt-field-re: instances=0 rounds=0 not-ready; jargon: instances=1 rounds=1 not-ready; errors=0 | identical (byte-identical archive) | identical (byte-identical archive) | identical (byte-identical archive; committed face == recompute, byte-identical) |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds: total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair: repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration: ledger_present=true entries=0 agreement_rate=null; feedback_edge=open; errors=0 | identical (byte-identical archive) | identical (byte-identical archive) | identical recompute (byte-identical archive); DIVERGENT vs committed face at both anchors - see section 4 |
| 3 | jargon_map_sync (step 3) | mode=plan; md_faces=143; entries=159; count=159; appended=0; updated=0; unchanged=122; retagged=0; authority_kept=4 (J098, J061, J012, J046); rejected=17 (alternation-guard); wrote=false; VERDICT IN-SYNC (plan is zero-write) | identical | identical | identical |
| 4 | pin_repair --plan (step 4) | ok=true; action=none; repairs=0; blocked=0; upstream-absent=2 (annotation-whitepaper and terminology-general-project external snapshots: pinned md5 matched, freshness declared SKIP upstream-absent); repo doc blob sha d27b6402 matched; VERDICT IN-SYNC (plan is zero-write) | identical | identical | identical |
| 5 | t_engines_seeds (step 5) | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0; declared skips recorded: test_detector_anchor (instrument at D:/ absent on mac), snapshot and transcription glossary sources absent | identical | identical | identical |
| 6 | t_engines_body (step 6) | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical | identical | identical |

### Layer A: same-anchor cross-time consistency (f1b6e27, R1 22:13Z / R2 23:00Z / R3 23:29Z)

PASS on all six tools. Three runs at three times, spanning three different network windows (R1 clone via depth-1 sha fetch during a v4-endpoint wall; R2 clean fetch; R3 first fetch failed with empty reply, retry green), all readings value-identical; the step-1 and step-2 archived artifacts are byte-identical across R1/R2/R3 (cmp evidence in section 3).

### Layer B: cross-anchor migration consistency (f1b6e27 -> 3e18590)

PASS on all six tools. The anchor move carries two commits (97c809f: plan-side zgx-out batch; 3e18590: automerge of PR#17); despite it, every tool reading is value-identical to the f1b6e27 runs; the R4 archived b-gate-audit.json and scheduling-feedback.json are byte-identical to the R3 archived files; the b-gate committed face equals the recompute byte-identically at both anchors (cmp evidence in section 3). Anchor migration changed no reading; in particular b-gate class count stayed 3 -> 3.

## 3. Byte-level and committed-face checks (all run in this session, read-only)

| check | command (abbreviated path roots: Z=/Users/zuguangzhao/rocqwash/zgx-out, R4=<log>/r4-anchor-3e18590-20261119T234622Z) | result |
|---|---|---|
| b-gate archive R1 vs R2 | cmp Z/b-gate-audit.20261119T221339Z.json Z/b-gate-audit.20261119T230026Z.json | BYTE-IDENTICAL |
| b-gate archive R2 vs R3 | cmp Z/b-gate-audit.20261119T230026Z.json Z/b-gate-audit.20261119T232908Z.json | BYTE-IDENTICAL |
| b-gate archive R3 vs R4 | cmp Z/b-gate-audit.20261119T232908Z.json R4/b-gate-audit.json | BYTE-IDENTICAL |
| scheduling archive R1 vs R2 | cmp (221339Z vs 230026Z) | BYTE-IDENTICAL |
| scheduling archive R2 vs R3 | cmp (230026Z vs 232908Z) | BYTE-IDENTICAL |
| scheduling archive R3 vs R4 | cmp (232908Z vs R4 archive) | BYTE-IDENTICAL |
| b-gate committed @f1b6e27 vs R1 recompute | git -C /Users/zuguangzhao/rocqwash show f1b6e27f39...:docs/b-gate-audit.json | cmp - Z/b-gate-audit.20261119T221339Z.json | BYTE-IDENTICAL |
| b-gate committed @3e18590 vs R4 recompute | git -C /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop show 3e185906...:docs/b-gate-audit.json | cmp - R4/b-gate-audit.json | BYTE-IDENTICAL |
| scheduling committed face @f1b6e27 | git show f1b6e27f39...:docs/scheduling-feedback.json, parsed repair_outcomes | repaired=3 unrecorded=46 rate=0.0588 wogc=2 escalated=0 |
| scheduling committed face @3e18590 | git show 3e185906...:docs/scheduling-feedback.json, parsed repair_outcomes | repaired=3 unrecorded=46 rate=0.0588 wogc=2 escalated=0 |
| exp-ledger rows @3e18590 | git -C rocqwash-loop show 3e185906...:docs/exp-ledger.jsonl | wc -l | 41 |
| exp-ledger rows @fa879e4 | git -C rocqwash-loop show fa879e4:docs/exp-ledger.jsonl | wc -l | 41 |
| PR#17 merged batch readings | git -C rocqwash-loop show 97c809f:zgx-out/scheduling-feedback.20261119T204525Z.json, parsed repair_outcomes | repaired=1 unrecorded=38 rate=0.0244 (matches every recompute) |
| PR#17 batch file scope | git -C rocqwash-loop show --name-only 97c809f | exactly 3 files, all zgx-out/ (docs/ untouched by that commit) |

## 4. The one divergence: docs/scheduling-feedback.json committed face vs recompute

| face | repair_outcomes (repaired / unrecorded / repair_action_rate) | watch_only_guard_correct | escalated |
|---|---|---|---|
| committed @f1b6e27 | 3 / 46 / 0.0588 | 2 | 0 |
| recompute @f1b6e27 (R1=R2=R3, byte-identical) | 1 / 38 / 0.0244 | 2 | 0 |
| committed @3e18590 | 3 / 46 / 0.0588 | 2 | 0 |
| recompute @3e18590 (R4, byte-identical to R3) | 1 / 38 / 0.0244 | 2 | 0 |

Exactly three values differ (repair_action_rate, repaired, unrecorded); everything else in the file, including both anchors' committed faces, is identical. The committed face was last touched by fa879e4 (verified in the full-history clone: `git log -1 <anchor> -- docs/scheduling-feedback.json` returns fa879e4 at both f1b6e27 and 3e18590; fa879e4 is an ancestor of f1b6e27; f1b6e27 itself does not touch the file), and 97c809f did not regenerate it. docs/exp-ledger.jsonl has 41 rows at both 3e18590 and fa879e4, so the committed face was generated against some other (uncommitted) ledger state - this is the recorded hypothesis of proposal line 4, not re-derived here.

## 5. Divergence trajectory: discovery -> reproduction -> cross-anchor persistence

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T0 | 2026-11-19T20:45:25Z | supply-lane PR#17 batch artifact already carries recompute-side values | git show 97c809f:zgx-out/scheduling-feedback.20261119T204525Z.json -> 1/38/0.0244 (re-verified locally this session from the merged commit) |
| T1 (discovery) | batch 221339Z; proposal ts 2026-11-19T22:17:23Z | first divergence found at anchor f1b6e27 in clone /Users/zuguangzhao/rocqwash; b-gate recompute byte-identical to committed face; divergence recorded fail-loud, cause not asserted; proposal line 1 cast | recorded commands (R2-3-receipt section 5, proposal line 1): python3 -I tools/learning_feedback.py ; git diff -- docs/scheduling-feedback.json (exactly the 3-value change) ; git diff --name-only -- docs/ (only scheduling-feedback.json) |
| T2 (repro 2) | batch 230026Z; proposal ts 23:02:10Z | second independent reproduction on same host, second batch run; same 3 values again; b-gate still byte-identical; proposal line 2 | python3 -I tools/learning_feedback.py (log plan-run-f1b6e27-20261120R2.log) ; git diff -- docs/scheduling-feedback.json |
| T3 (repro 3) | batch 232908Z; proposal ts 23:30:00Z | third independent reproduction; committed-vs-recompute checked with blob cmp (git show HEAD:docs/b-gate-audit.json | cmp -); proposal line 3 | python3 -I tools/learning_feedback.py (log ...R3.log) ; git diff -- docs/scheduling-feedback.json ; cmp b-gate blob |
| T4 (cross-anchor) | batch 234622Z; proposal ts 23:46:58Z | fourth reproduction, first at new anchor 3e18590 after PR#17 automerge; divergence survives the anchor move; committed face unchanged (3/46/0.0588); exp-ledger 41 rows at HEAD and at fa879e4 -> committed face generated against an uncommitted ledger state and never regenerated; proposal line 4; artifacts archived to r4-anchor dir | python3 -I tools/learning_feedback.py at 3e18590 (r4-plan-run.log step 2) ; git diff -- docs/scheduling-feedback.json (same 3-value hunk, quoted verbatim in r4-plan-run.log step 7) ; git show HEAD:docs/b-gate-audit.json | cmp - (rc=0) ; git fetch moved origin/main f1b6e27 -> 3e18590 ; wc -l exp-ledger 41/41 |

This session's independent corroboration of the whole trajectory (all local, zero network): both anchors' committed faces read 3/46/0.0588 (section 3); all four recompute artifacts are byte-identical; the T0 merged-batch blob reads 1/38/0.0244. Net effect: the divergence is stable across 4 batch runs, 2 clones, 2 anchors, and 3 network windows, and it survived the landing of the plan-side batch that reported it.

## 6. Proposal ledger integrity check (ask item 4): PASSED

Command run:
python3 -I -c '...json.loads per line on /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl...'

Output:
```
ascii_decode_ok=True total_lines=4
line 1: json.loads=OK actor=zgx ts=2026-11-19T22:17:23Z anchor=f1b6e27 kind=proposal ascii_only=True keys=actor,anchor,evidence,kind,points,schema,target,ts
line 2: json.loads=OK actor=zgx ts=2026-11-19T23:02:10Z anchor=f1b6e27 kind=proposal ascii_only=True keys=actor,anchor,evidence,kind,points,schema,target,ts
line 3: json.loads=OK actor=zgx ts=2026-11-19T23:30:00Z anchor=f1b6e27 kind=proposal ascii_only=True keys=actor,anchor,evidence,kind,points,schema,target,ts
line 4: json.loads=OK actor=zgx ts=2026-11-19T23:46:58Z anchor=3e18590 kind=proposal ascii_only=True keys=actor,anchor,evidence,kind,points,schema,target,ts
```
4/4 lines json.loads-valid, ASCII-only, uniform key set, ts strictly increasing, anchor sequence f1b6e27 x3 then 3e18590 x1.

## 7. Conclusions

- C1 (Layer A): same-anchor cross-time consistency at f1b6e27 holds for all six tools across R1/R2/R3 - zero value drift, artifacts byte-identical.
- C2 (Layer B): cross-anchor migration consistency f1b6e27 -> 3e18590 holds for all six tools - the anchor move (including PR#17 landing) changed no reading; b-gate class count 3 -> 3, verdict not-ready at both anchors (honest pending-state reading, not a fault).
- C3: the only non-matching face in the whole corpus is docs/scheduling-feedback.json repair_outcomes (3 values, committed 3/46/0.0588 vs recompute 1/38/0.0244), and its committed face is itself identical at both anchors. The finding is open as recorded by the proposing seats (lines 1-3 do not assert a cause; line 4 records the uncommitted-ledger-state hypothesis supported by 41/41 exp-ledger rows).
- C4: the four proposal lines form a complete discovery -> 2x reproduction -> cross-anchor chain with strictly increasing timestamps; every evidence command they cite is either present in an archived log or was re-verified locally in this session (section 3, section 5).

## 8. Honesty notes

1. This seat did not re-execute the six tools. All readings are quoted from archived JSON artifacts and batch logs produced by the four batch runs; the correlation claims rest on those artifacts plus the byte-level comparisons listed in section 3, all of which were run in this session.
2. Zero network was used in this session (NETRED honored). The PR#17 gh api contents comparison recorded in R2-3-receipt section 5.3 was executed by an earlier seat over the network at its own time and was not re-run here; the local equivalent (reading the merged blob from 97c809f) was used instead.
3. /Users/zuguangzhao/rocqwash is a shallow clone (.git/shallow grafts f1b6e27 and 3e185906; `git rev-parse f1b6e27^` fails there). Path-history queries in that clone are unreliable (a grafted root appears to touch every file in its tree - observed and discarded in this session). All history conclusions in this ledger come from the full-history clone rocqwash-loop.
4. Proposal line 4 (the R4 cross-anchor line) exists in the working tree of /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl only; the branch tip f1d73e6 still holds 3 committed lines (git show f1d73e6:...| wc -l = 3 vs file = 4). It is uncommitted/unpushed as of this reading.
5. environment.txt carries the R3 stamp (232908Z) because collect.sh rewrites it per batch; per-batch stamps live in the per-stamp JSON filenames. No R1/R2 environment snapshot survives as a separate file.
6. The upstream-absent=2 pin-repair skips are declared skips (external originals on a D:/ desktop volume, unreachable from this mac), recorded as such by every batch - they are honest declared SKIPs, not failures.
7. Attribution of the divergence is deliberately not adjudicated by this ledger; this is a correlation ledger, not a root-cause verdict. The causal hypothesis in proposal line 4 is reported as recorded.
8. Not done / not run in this session: no tool re-run, no PR/fork interaction, no state change in either clone, no writes outside the two files this ask names.

## 9. Batch extension section (2026-11-21, ticket R2-30): six-batch full comparison

Ticket: R2-30 (ledger extension seat, read-only analysis; identity live-lumen, host Darwin arm64)
Date: 2026-11-21
Scope: extend sections 1-8 with reading batches 5-6 (R2-20 receipt, R2-26 receipt) into the six-batch full comparison f1b6e27 x3 / 3e18590 x1 / 6998c40-batch x1 / c48a548 x1, plus the ask-named cross-anchor trend conclusions; verify the R2-26 new divergence proposal in the proposal ledger (json.loads). This section appends no proposal line and writes nothing in any repo tree. Read this session: R2-20-receipt.md, R2-26-receipt.md, r12-plan-run.log, r17-plan-run.log, the r12-anchor-3a56b85-20261120T141631Z/ and r17-anchor-c48a548-20261120T165150Z/ archives (out_* captures, divergence diffs, post-status files), the R1-R4 zgx-out archives, and zgx-ledger-proposals.jsonl; read-only git queries against the rocqwash-loop clone. Every check quoted below was run in this session.

### 9.1 Six-batch inventory extension and anchor chain

| batch | collect stamp (UTC) | anchor | expected anchor | clone | record |
|---|---|---|---|---|---|
| R2-20 | 20261120T141631Z | 3a56b8542807ec1dfd58762a6e3b249f0c6dcf2a | 6998c4018242944f0077c3daab604202d2e7c07d | rocqwash-loop | the "6998c40 batch": upstream tip had moved one commit past the expected 6998c40 (symbiosis_bus selftest TMP fallback); anchored at the actual tip, recorded as found (R2-20 receipt section 1, honesty note D); fetch green on first attempt; 1 new divergence -> proposal line 15; artifacts r12-anchor-.../ |
| R2-26 | 20261120T165150Z | c48a548a7bd2095bd081e6b6837266f5576dee8c | c48a548 (same) | rocqwash-loop | first sampling of c48a548 (receipt's grep over all b1-recursion receipts: 0 prior matches); fetch needed the full NETRED path (30s low-speed abort rc=128, 120s backoff, HTTP/1.1 retry rc=0); 1 new divergence (third-anchor recurrence) -> proposal line 20; artifacts r17-anchor-.../ |

Anchor chain (git rev-parse + merge-base --is-ancestor + rev-list --count, all run this session; ancestry YES at every link):

f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548, f1b6e27..c48a548 = 15 commits.

Context (not one of the six batches): r5-seat anchor 0765d671, between 3a56b85 and c48a548; 0765d671..c48a548 = 9, matching the "9 commits ahead" wording of proposal line 20.

### 9.2 Six-tool comparison, batches 5-6 (values quoted from the archived captures)

| # | tool (step) | R2-20 @3a56b85 (141631Z) | R2-26 @c48a548 (165150Z) | vs R1-R4 corpus (section 2) |
|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready classes 0 of 3 needed; remaining_to_b=3; concl.real.const-lt-field-re-exists: instances=1 rounds=1 not-ready; ineq.real.const-lt-field-re: instances=0 rounds=0 not-ready; jargon: instances=1 rounds=1 not-ready; errors=0; report written | identical (stdout capture byte-identical to R2-20's, cmp this session) | identical values; committed face == recompute at every anchor (9.3) |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds: total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair: repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration: ledger_present=true entries=0 agreement_rate=None; feedback_edge: open; errors=0 | identical (byte-identical capture) | recompute identical to R1-R4; DIVERGENT vs committed face at both new anchors (9.3) |
| 3 | jargon_map_sync (plan) | IN-SYNC (plan is zero-write) | identical (byte-identical capture) | identical |
| 4 | pin_repair --plan | ok=true action=none repairs=0 blocked=0 upstream-absent=2 (2 external snapshots SKIP-declared, consistency matched); repo pin d27b6402 == head, matched | same verdict; repo pin 83effa3f == head, matched | verdict identical; the single cross-anchor byte difference in all captured outputs is this repo-pin sha pair moving d27b6402 -> 83effa3f (pin and pinned doc blob moved together, state stayed matched) - input-tracking, unlike the stale scheduling face |
| 5 | t_engines_seeds | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0 | identical (byte-identical capture) | identical |
| 6 | t_engines_body | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical (byte-identical capture) | identical |

Six-batch matrix: all 36 tool-reading cells (6 tools x 6 batches) carry identical values (R1-R4 cells from section 2, batches 5-6 from this subsection). Not green: none in any batch.
R2-20 invocation note: pin_repair's first invocation in r12-plan-run.log is RC=2 (seat-side argv word-splitting bug; explicit-argv retry RC=0 IN-SYNC, verbatim in the log) - the table carries the retried verdict.
Cross-batch file checks (cmp, this session): the tool 1/3/5/6 stdout captures, both divergence diffs, and both post-status files are byte-identical between r12 and r17; tool 2's captures byte-identical; tool 4's captures differ exactly at the repo-pin sha pair named in row 4. Both divergence diffs are 471 bytes with the same index line a952af0..06998c8 and the same 3-value hunk.

### 9.3 Divergence face at the new anchors (extends section 4)

| face | repair_outcomes (repaired / unrecorded / rate) | wogc | escalated |
|---|---|---|---|
| committed @6998c40 | 3 / 46 / 0.0588 | 2 | 0 |
| committed @3a56b85 | 3 / 46 / 0.0588 | 2 | 0 |
| recompute @3a56b85 (R2-20) | 1 / 38 / 0.0244 | 2 | 0 |
| committed @c48a548 | 3 / 46 / 0.0588 | 2 | 0 |
| recompute @c48a548 (R2-26) | 1 / 38 / 0.0244 | 2 | 0 |

- The committed scheduling blob is the same blob a952af079aa8e6baf68b38f60a5d68248963d86e at every anchor queried this session: f1b6e27, 3e18590, 6998c40, 0765d671 (context), 3a56b85, c48a548. The stale face has not moved in 15 upstream commits; git log -1 at c48a548 for the file still returns fa879e4.
- b-gate-audit.json: the committed face at each of those anchors is BYTE-IDENTICAL to the R1-R4 recompute archive (git show <anchor>:docs/b-gate-audit.json piped to cmp against b-gate-audit.20261119T232908Z.json; blob 6c8238804de36fa94d24f12131ca696f9404983d everywhere) - consistent with the receipts' "regenerated byte-identical, no git-status entry".
- The committed-vs-produced sha256 pair (1ed190e1 / e66ca0a1) is quoted from R2-26 receipt section 3 and proposal line 20's evidence field; the produced face file was not archived, so the hashes were not recomputed this session.

### 9.4 Divergence trajectory extension (extends section 5)

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T5 (anchor 5) | batch 141631Z; proposal ts 14:18:05Z | R2-20 at 3a56b85 (expected 6998c40, tip +1): same 3-value divergence, b-gate byte-identical; proposal line 15 (regenerate and land the refreshed face) | r12-plan-run.log; r12-divergence.diff; jsonl line 15 (json.loads this session) |
| T6 (anchor 6) | batch 165150Z; proposal ts 16:56:15Z | R2-26 at c48a548: third-anchor recurrence of the same stale blob (r5 anchor 0765d671, ledger line 19, is the middle witness, cited by reference); line 20 adds the process proposal (sync guard coupling the face to its input blob shas) | r17-plan-run.log; r17-divergence.diff; jsonl line 20 (json.loads this session) |

Net after extension: the divergence is stable across all 6 ledger batches plus the r5 context anchor, 5 distinct anchors (f1b6e27, 3e18590, 0765d671, 3a56b85, c48a548), 2 clones (rocqwash for R1-R3; rocqwash-loop for R4, R2-20, R2-26), and 15 upstream commits, with the committed blob unchanged throughout and every proposal still unapplied upstream.

### 9.5 Cross-anchor trend conclusions (ask-named)

- Trend A (does the divergence persist at the new anchors?): PERSISTS, unbroken. Both new anchors re-found the identical divergence (same committed blob a952af0 at 3/46/0.0588 vs the identical deterministic recompute 1/38/0.0244); the committed face survived the two anchor moves 3e18590 -> 3a56b85 and 3a56b85 -> c48a548 untouched; the proposals now form a discovery -> 2x reproduction -> cross-anchor chain across five anchors (lines 1-4, 15, 20, with context line 19).
- Trend B (b-gate class count trend): FLAT. Ready classes 0 of 3 needed and remaining_to_b=3 at all six batches; per-class instance/round counts identical since R1 (const-lt-field-re-exists 1/1, const-lt-field-re 0/0, jargon 1/1; threshold 3 instances x 1 round); verdict not-ready everywhere; the committed b-gate face is byte-stable across all anchors. The B-gate pending state neither progressed nor regressed across the 15-commit span.
- Trend C (proposal ledger growth): 4 lines at section-6 time -> 20 lines now; the reading-batch chain for the stale face (lines 1, 2, 3, 4, 15, 19, 20) has strictly increasing ts (22:17:23Z, 23:02:10Z, 23:30:00Z, 23:46:58Z, 14:18:05Z, 15:42:14Z, 16:56:15Z); the newest line is a recurrence record plus a process proposal, not a new root-cause claim (section 8 note 7 still stands: this ledger does not adjudicate cause).

### 9.6 R2-26 new proposal verification (ask item 2): PASSED

Command (this session): python3 -I /tmp/r2-30-jsonlcheck.py - per-line json.loads over /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl, with schema/actor/kind/ASCII assertions, a ts-order check, and full-record dumps for anchor values 3a56b85/c48a548.

Output: ascii_decode_ok=True total_lines=20; 20/20 lines json.loads=OK, ascii_only=True, uniform 8-key set (actor,anchor,evidence,kind,points,schema,target,ts), schema=zgx-proposal/1, actor=zgx, kind=proposal.

- R2-26 has exactly one new divergence proposal, jsonl line 20: anchor c48a548, ts 2026-11-20T16:56:15Z, target docs/scheduling-feedback.json. VERIFIED: its content cross-checks against the r17 artifacts (same committed blob a952af0..., same 3-value hunk in the byte-identical diff file, the sha256 pair 1ed190e1/e66ca0a1 as cited, and the 9-commit distance to 0765d671 confirmed by rev-list).
- Line 15 (R2-20's proposal: anchor 3a56b85, ts 14:18:05Z) verified the same way against the r12 artifacts.
- New file-wide observation: ts is non-decreasing but NOT strictly increasing across all 20 lines - equal-ts batch groups at lines 5-9 (2026-11-20T13:00:00Z), lines 10-14 (same stamp), and lines 17-18 (2026-11-20T14:41:44Z). Section 6's strictly-increasing claim remains true for its four lines and for the reading-batch chain in Trend C.
- Lines outside the six-batch mandate (5-14: anchors 6d55f12 x5 then 666a957 x5, target repo-governance; 16-18: f1d73e6 x3; 19: 0765d671, target stale-scheduling-feedback-face) parsed valid and are recorded from the same dump; their content belongs to other seats' tickets and is not adjudicated here.

### 9.7 Honesty notes (extension)

1. This seat re-executed none of the six tools; batches 5-6 readings are quoted from the archived stdout captures and logs; R1-R4 readings are carried over from sections 1-8, with this-session spot re-checks R1=R3 and R3=R4 for both archived faces (BYTE-IDENTICAL).
2. The R2-20/R2-26 recompute faces were not archived as JSON files (the r12/r17 dirs hold captures + diffs only); byte-identity for those recomputes rests on the captures, the byte-identical 471-byte diff files, and the receipts' post-run git-status (exactly one modified path at both anchors).
3. The "6998c40 batch" label: no tool ran at 6998c40 in any batch; R2-20's six readings are at 3a56b85 (+1). 6998c40 itself was committed-face-checked only (same stale scheduling blob, same b-gate blob).
4. Zero network; zero writes to any repo tree; no proposal line appended (ask item 2 is a verification, not an append); the only writes by this seat are this appended section and R2-30-receipt.md.
5. Non-ASCII material (the external D:/ upstream snapshot paths inside the pin_repair captures) is referenced but not reproduced; this section is ASCII throughout (LC_ALL=C grep verified).
6. r5/0765d671 and jsonl lines 5-18 are context only, not re-verified beyond the dump and the committed-face queries.

## 10. Batch extension section II (2026-11-21, ticket R2-37): seven-batch full comparison and the landing chapter

Ticket: R2-37 (ledger extension seat II, read-only analysis; identity live-lumen, host Darwin arm64)
Date: 2026-11-21
Scope: extend sections 1-9 with reading batch 7 (R2-36 receipt, r20 archive) into the seven-batch full comparison f1b6e27 x3 / 3e18590 / 6998c40-label (read at 3a56b85) / c48a548 / 8502146, six tools value by value; plus the ask-named landing chapter: the desk resolve 0a0a9c43 and the post-resolve recompute diff verdict (case open vs converged). This section appends no proposal line and writes nothing in any repo tree. Read this session: R2-36-receipt.md, the r20-20261120T191930Z/ archive (six out_* captures, r20-plan-run.log, divergence diff/stat, pre/post status), the r12/r17/R1-R4 zgx-out archives, and zgx-ledger-proposals.jsonl; read-only git queries (GIT_OPTIONAL_LOCKS=0) against the rocqwash-loop clone at fixed SHAs. B7 readings are quoted from the R2-36 archived artifacts, which landed mid-session (the R2-36 seat ran concurrently with this seat; every quote below was taken from the completed archive). Every check quoted below was run in this session.

### 10.1 Seven-batch inventory and the extended anchor chain

| batch | collect stamp (UTC) | anchor | expected anchor | clone | record |
|---|---|---|---|---|---|
| R1 | 20261119T221339Z | f1b6e27 | (first run) | rocqwash | section 1 |
| R2 | 20261119T230026Z | f1b6e27 | f1b6e27 | rocqwash | section 1 |
| R3 | 20261119T232908Z | f1b6e27 | f1b6e27 | rocqwash | section 1 |
| R4 | 20261119T234622Z | 3e18590 | (first cross-anchor run) | rocqwash-loop | section 1 |
| R2-20 | 20261120T141631Z | 3a56b85 | 6998c40 (tip had moved +1) | rocqwash-loop | section 9.1 (the "6998c40 batch") |
| R2-26 | 20261120T165150Z | c48a548 | c48a548 | rocqwash-loop | section 9.1 |
| R2-36 | 20261120T191930Z | 8502146 | 8502146 or newer -> MATCH (exactly 8502146 = origin/main at fetch) | rocqwash-loop | first reading batch whose anchor descends from the desk resolve 0a0a9c43; fetch attempt 1 rc=0 elapsed 1s (single flight, no backoff); pre-run tree clean; zero net tree write (post-restore status 0) |

Anchor chain (git merge-base --is-ancestor YES at every link; rev-list --count, all run this session):

f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548 ->(+8)-> 0a0a9c43 ->(+3)-> 8502146; f1b6e27..8502146 = 26 commits (also c48a548..8502146 = 11, matching receipt and proposal line 21).

Context commits since c48a548: 0a0a9c43 is the desk-side landing of PR#18 content ("chore(zgx-out): land PR#18 content via desk resolve", single parent a07403e, non-merge); the other 10 commits in c48a548..8502146 are the i18n unit re-lay wave (u3-u13 faces) plus CAPABILITY-INDEX/jargon-exempt landings; none of them touches docs/scheduling-feedback.json (see 10.3).

### 10.2 Seven-batch six-tool comparison, value by value

B1 column carries the full compact reading (as in section 2); B2-B7 cells carry "identical" (value-identical to B1) or the exact differing bytes. Where a committed-face property is batch-specific it is named in the cell.

| # | tool (step) | B1 R1 @f1b6e27 (221339Z) | B2 R2 @f1b6e27 (230026Z) | B3 R3 @f1b6e27 (232908Z) | B4 R4 @3e18590 (234622Z) | B5 R2-20 @3a56b85 (141631Z) | B6 R2-26 @c48a548 (165150Z) | B7 R2-36 @8502146 (191930Z) |
|---|---|---|---|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready_classes 0/3; remaining_to_b=3; concl.real.const-lt-field-re-exists 1/1 not-ready; ineq.real.const-lt-field-re 0/0 not-ready; jargon 1/1 not-ready; errors=0 | identical | identical | identical (committed face == recompute, byte-identical) | identical | identical (capture byte-identical to B5) | identical (out_1 byte-identical to B6's, cmp this session); committed face @8502146 == R1-R4 recompute archive, BYTE-IDENTICAL (cmp this session) |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration ledger_present=true entries=0 agreement_rate=null; feedback_edge=open; errors=0 | identical | identical | identical recompute; DIVERGENT vs committed face (section 4) | identical | identical recompute; DIVERGENT vs committed face (9.3) | identical recompute (rerun determinism cmp rc=0); DIVERGENT vs committed face @8502146 - 10.3; case verdict: OPEN |
| 3 | jargon_map_sync (step 3) | mode=plan; md_faces=143; entries=159; count=159; appended=0 updated=0 unchanged=122 retagged=0; authority_kept=4; rejected=17; wrote=false; VERDICT IN-SYNC | identical | identical | identical | identical | identical (byte-identical capture) | identical (out_3 byte-identical to B6's, cmp this session) |
| 4 | pin_repair --plan (step 4) | ok=true action=none repairs=0 blocked=0 upstream-absent=2 (2 external snapshots SKIP-declared); repo doc pin d27b6402 == head, matched; VERDICT IN-SYNC | identical | identical | identical | identical; repo pin d27b6402 == head, matched | same verdict; repo pin 83effa3f == head, matched | same verdict; repo pin 83effa3f == head, matched (out_4 byte-identical to B6's, cmp this session); the only cross-batch byte differences in all captured outputs remain this repo-pin sha pair moving d27b6402 -> 83effa3f between B5 and B6 (r12 vs r20 capture: exactly 80 differing byte positions, chars 1087-1187, the two 40-hex pin fields, same length; cmp this session) |
| 5 | t_engines_seeds (step 5) | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0; declared skips: test_detector_anchor (D:/ instrument absent), snapshot + transcription glossary sources absent | identical | identical | identical | identical | identical (byte-identical capture) | identical (out_5 byte-identical to B6's, cmp this session) |
| 6 | t_engines_body (step 6) | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical | identical | identical | identical | identical (byte-identical capture) | identical (out_6 byte-identical to B6's, cmp this session) |

Seven-batch matrix: all 42 tool-reading cells (6 tools x 7 batches) carry identical values, except tool 4's repo-pin sha pair, which is input-tracking state (pin and pinned doc moved together, stayed matched). Not green: none in any batch.

Cross-batch byte checks run this session (cmp): B7's six stdout captures are byte-identical to B6's (r20 vs r17, 6/6 IDENTICAL); B7's divergence diff is byte-identical to both B5's and B6's (r20 == r17 == r12, 471 bytes, index a952af0..06998c8, same 3-value hunk); B7's b-gate committed face at 8502146 and at 0a0a9c43 is byte-identical to the R1-R4 recompute archive (blob 6c823880 everywhere). R2-20 invocation note from 9.2 (pin first invocation RC=2, retried clean) still applies to B5 only.

### 10.3 Landing chapter: desk resolve 0a0a9c43 and the post-resolve recompute diff (ask item 2)

What the resolve is and landed (all measured this session at the fixed SHA 0a0a9c43d4fc7aa11ba806d4ce2cc4da9375c955):

- 0a0a9c43 = single-parent commit on a07403e ("chore(zgx-out): land PR#18 content via desk resolve - her planface reading batches at anchors f1b6e27/3e18590/3a56b85/c48a548, r12 divergence evidence, governance proposals, and the dual-stamp environment snapshots (204525Z + 232908Z both preserved); zgx actor namespace (PR#18 resolve)"); ancestor of c48a548-descendant 8502146 (merge-base --is-ancestor YES twice: c48a548 -> 0a0a9c43, 0a0a9c43 -> 8502146); c48a548..0a0a9c43 = 8 commits.
- Landed exactly 38 paths, all under zgx-out/ (git show --name-only: 38 non-empty paths; grep -v '^zgx-out/' count = 0). The R20 workflow ticket wording said "40 items"; 38 is what the commit carries - recorded as measured, adjudication belongs to the landing-verify seat (R2-35), not this ledger.
- Dual-stamp environment closure VERIFIED: zgx-out/environment.20261119T204525Z.txt (blob 5dfca547) and zgx-out/environment.20261119T232908Z.txt (blob 6251fa93) both present in the commit; the two blobs are byte-identical except line 3 (stamp=20261119T204525Z vs stamp=20261119T232908Z; cat-file + diff, this session); the generic zgx-out/environment.txt in the same commit carries blob 5dfca547, i.e. the 204525Z face. This retires the section 8 note 5 gap for these two stamps: per-stamp environment snapshots now exist as committed files.
- The proposal evidence lane landed: zgx-out/zgx-ledger-proposals.jsonl at 0a0a9c43 and at 8502146 carries 20 lines (committed), i.e. the chain through line 20 (including the B5/B6 divergence lines 15/19/20 and the governance lines) is now upstream; line 21 (B7) is working-tree only at reading time (committed@8502146 = 20 lines vs file = 21; cmp EOF this session) - same uncommitted posture as every earlier batch's line (section 8 note 4 posture).
- docs/ was NOT touched by the resolve: zero of the 38 paths are outside zgx-out/; docs/scheduling-feedback.json last-touch commit at 8502146 is still fa879e4 (git log -1 --, this session); docs/b-gate-audit.json last touch remains f88fe9a (2026-11-19, the commit that introduced the tool).

Post-resolve recompute diff comparison (the ask's named check), at reading anchor 8502146:

| face | repair_outcomes (repaired / unrecorded / rate) | wogc | escalated | blob |
|---|---|---|---|---|
| committed @0a0a9c43 (desk resolve itself) | 3 / 46 / 0.0588 | 2 | 0 | a952af0 (rev-parse this session) |
| committed @8502146 (B7 anchor; parsed from git show this session) | 3 / 46 / 0.0588 | 2 | 0 | a952af0 |
| recompute @8502146 (B7, R2-36; deterministic, rerun cmp rc=0) | 1 / 38 / 0.0244 | 2 | 0 | 06998c8 (git hash-object, archived stat) |

git diff committed-vs-recompute @8502146 is exactly the same 3-value hunk (repair_action_rate 0.0588->0.0244, repaired 3->1, unrecorded 46->38), and the diff file is byte-identical (471 bytes) to the r12/r17 chapter diffs (cmp this session). Meanwhile docs/b-gate-audit.json at the same anchor remains byte-identical to its committed face (sha256 3c70b528 both sides, cmp rc=0) - the stale-face class stays specific to scheduling-feedback.json.

Verdict (ask's conditional, applied): the environment dual-stamp closure is in (0a0a9c43), and the scheduling-feedback divergence is still present after it -> the case is recorded as OPEN. In the resolve's own words as evidence: the resolve landed the evidence lane, not the face - the stale committed face survived its own landing (the resolve carries the divergence evidence in zgx-out while the face it describes stays stale in docs/).

### 10.4 Divergence trajectory extension (extends sections 5 and 9.4)

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T7 (anchor 7) | batch 191930Z; proposal ts 19:24:17Z | R2-36 at 8502146 (11 commits past c48a548; 3 commits past the desk resolve 0a0a9c43): same 3-value divergence, b-gate byte-identical; proposal line 21 = standing regeneration proposal plus the c48a548 sync-guard coupling, now worded "the face has survived three reading seats and one desk resolve while stale" | r20-plan-run.log; r20-divergence.diff; jsonl line 21 (json.loads this session, 10.6) |

Net after extension: the divergence is stable across all 7 reading batches, 8 anchors queried this ledger's span (f1b6e27, 3e18590, 6998c40, 0765d671 context, 3a56b85, c48a548, 0a0a9c43, 8502146 - the committed blob is a952af0 at every one, rev-parse this session for the two new ones), 26 upstream commits, 2 clones, 4+ network windows, and one desk action. The B5 "6998c40" label caveat from 9.7 note 3 still holds: no tool has run AT 6998c40; it and 0a0a9c43 are committed-face-check-only anchors.

### 10.5 Trend conclusions update (extends 9.5)

- Trend A (divergence persistence): PERSISTS, unbroken, and now survives a desk action. The identical face pair (a952af0 @3/46/0.0588 vs the deterministic 06998c8 @1/38/0.0244) re-appears at 8502146, whose ancestry includes the resolve that landed the case's own evidence. The chain is discovery -> 2x reproduction -> cross-anchor -> post-desk-resolve recurrence (lines 1-4, 15, 20, 21, with context 19).
- Trend B (b-gate class count trend): FLAT. B7 carries the identical per-class counts (const-lt-field-re-exists 1/1, const-lt-field-re 0/0, jargon 1/1), 0 of 3 ready, remaining_to_b=3, verdict not-ready, errors 0; the committed b-gate face is byte-identical to the R1-R4 recompute at both new anchors (cmp this session). The pending state neither progressed nor regressed across the 26-commit span.
- Trend C (proposal ledger growth): 20 -> 21 lines. The reading-batch chain for the stale face (1, 2, 3, 4, 15, 19, 20, 21) has strictly increasing ts (22:17:23Z, 23:02:10Z, 23:30:00Z, 23:46:58Z, 14:18:05Z, 15:42:14Z, 16:56:15Z, 19:24:17Z); file-wide ts remains non-decreasing only (the equal-ts groups at lines 5-9, 10-14, 17-18 from 9.6 persist). Line 21 carries no new root-cause claim; section 8 note 7 (no causal adjudication by this ledger) still stands.

### 10.6 R2-36 proposal line verification: PASSED

Command run (this session): python3 -I /tmp/r2-37-jsonlcheck.py - per-line json.loads over /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl with key-set/schema/actor/kind/ASCII assertions.

Output: ascii_decode_ok=True total_lines=21; 21/21 lines json.loads=OK, ascii_only=True, uniform 8-key set (actor,anchor,evidence,kind,points,schema,target,ts), schema=zgx-proposal/1, actor=zgx, kind=proposal; ts non-decreasing=True.

Line 21 (R2-36's new line) cross-checked this session: anchor 8502146 == rev-parse origin/main; "11 commits past c48a548" == rev-list --count c48a548..8502146 = 11 (the receipt discloses an in-place correction of a first-draft "36" to 11 before delivery; the landed line carries the verified 11); blob pair a952af0 / 06998c8 == the archived divergence diff's index line; committed-face last touch fa879e4 re-verified by git log -1. Line 21 is uncommitted (see 10.3).

### 10.7 Honesty notes (extension II)

1. This seat re-executed none of the six tools. B7 readings are quoted from the r20 archived captures, the r20-plan-run.log, and R2-36-receipt.md; the cross-batch claims rest on the byte-level comparisons in 10.2/10.3, all run in this session. B1-B6 readings are carried over from sections 2 and 9.2, with this-session spot re-checks: b-gate committed face at 0a0a9c43 and 8502146 cmp'd BYTE-IDENTICAL against the R1-R4 recompute archive.
2. The R2-36 seat ran concurrently with this seat; its receipt and archive landed mid-session. Every B7 quote in this section was taken from the completed archive (dir mtime 03:23 local) and the receipt (03:25 local), after the seat's own post-restore clean-tree state (r20-post-status.txt = 0). The B7 recompute face was not kept as a file (tree restored); byte-identity rests on the captures, the byte-identical 471-byte diff shared with r12/r17, the archived stat pair (1ed190e1 / e66ca0a1 16-char prefixes), and the pinned blob 06998c8f (git hash-object, from the archived stat).
3. The R20 ticket's "40 items" vs the measured 38 zgx-out paths in 0a0a9c43 is recorded as measured in 10.3 and left to R2-35's landing-verify scope.
4. Non-ASCII material (the zh jargon faces inside the out_3 capture, the D:/ zh upstream paths inside the out_4 capture) is referenced but not reproduced; this section is ASCII throughout. r20-plan-run.log was re-verified ASCII-clean this session (LC_ALL=C grep -nP, rc=1 = no hits).
5. Zero network (NETRED honored); zero writes to any repo tree (all git invocations read-only queries at fixed SHAs, GIT_OPTIONAL_LOCKS=0; no checkout, no fetch by this seat); no proposal line appended by this seat; the only writes by this seat are this appended section and R2-37-receipt.md.
6. The dual-stamp closure in 10.3 retires section 8 note 5's observation gap only for the two stamps now committed as files; environment.txt in the working trees is still per-batch-rewritten by collect.sh, so future batches keep their own stamp files only if the collect step archives them.
7. Attribution of the divergence remains deliberately unadjudicated by this ledger (section 8 note 7 stands). The case status after this extension: OPEN, with the standing regeneration + sync-guard proposal now recorded upstream-adjacent in lines 15/20/21 and the evidence lane itself landed via 0a0a9c43.

## 11. Batch extension section III (2026-11-21, ticket R2-51): full comparison over the ask-named anchors and the seven-sampling divergence trend

Ticket: R2-51 (ledger extension seat III, read-only analysis; identity live-lumen, host Darwin arm64)
Date: 2026-11-21
Scope: extend sections 1-10 with the two newest reading batches (r22 @ 8eff64e, self-labeled "6th sampling"; r24 @ d27af2d, self-labeled "7th sampling") into the full six-tool comparison over the ask-named anchor list f1b6e27 x3 / 3e18590 / 6998c40 / c48a548 / 8502146 / 8eff64e / d27af2d, plus the ask-named divergence seven-sampling trend conclusion (persist / converge / fluctuate, value by value). This section appends no proposal line and writes nothing in any repo tree. Read this session: R2-41-receipt.md, R2-46-receipt.md, R2-47-receipt.md, R2-48-receipt.md, R2-49-receipt.md, R2-53-receipt.md, the r22-20261120T201318Z/ and r24-20261120T212043Z/ archives (six out_* captures each, run logs, divergence diff/stat, produced faces, pre/mid/post status files, archived proposal ledgers), the r12/r17/r20/R1-R4 archives, and the shore proposals file; read-only git queries (GIT_OPTIONAL_LOCKS=0) against the rocqwash-loop clone at fixed SHAs (clone read at HEAD=origin/main=d27af2d, working tree clean, 0 status lines). Zero network. Every check quoted below was run in this session.

Source disclosure (fail-loud): the ask named R2-50-receipt.md (the 7th sampling) as input; that file does not exist - Read returned "File does not exist" and ls returned "No such file or directory" at session start, re-checked again late in the session (absent both times; no receipt numbered R2-50 or R2-51 exists, and R2-53 landed concurrently mid-session as a delivery-survival audit, not a reading batch). The 7th-sampling record was taken from the r24 archive plus R2-47-receipt.md (the seat that ran that batch); the 6th-sampling record from the r22 archive plus R2-41-receipt.md. Nothing was invented to fill the R2-50 name.

Counting note: the ask's "eight-batch" numeral does not decompose cleanly against its own anchor list, which names nine six-tool batch runs across seven distinct anchors (f1b6e27 x3 runs plus six single-run anchors); in particular 8eff64e and d27af2d are two separate complete batches on disk (seats R2-41 and R2-47, receipts on file), not one step. All nine runs are tabulated in 11.2 - nothing omitted to make the numeral fit. The divergence itself has been sampled at exactly seven anchors, matching ask item 2's "seven samplings" (11.5).

### 11.1 Batch inventory extension and the extended anchor chain

| batch | collect stamp (UTC) | anchor | expected anchor | clone | record |
|---|---|---|---|---|---|
| R2-41 (r22) | 20261120T201318Z | 8eff64e62e7338152868867ecb3e485ccfeb6d99 | 8cfebb44 (tip had moved +3: bd511c4 u14, 63026ad u15, 8eff64e u16) | rocqwash-loop | "6th sampling" (workorder R2-41 count); fetch rc=0 elapsed 1s, no backoff; pre-run tree clean; zero net tree write (post-status 0); its proposal line 22 was reverted by the seat's own restore - archived-only, see 11.4 |
| R2-47 (r24) | 20261120T212043Z | d27af2dee259d30cf560965089754607b337b545 | (moved-forward branch taken; previous anchor 8eff64e) | rocqwash-loop | "7th sampling"; fetch rc=0 elapsed 1s - a no-op confirm of an UNLOGGED actor's 2026-11-20T21:07:49Z fast-forward 8eff64e -> d27af2d (disclosed by R2-47 to netred_p6, unadjudicated here); pre-run tree clean; zero net tree write (post-status 0); proposal line 23 appended to the shore ledger |

Anchor chain (git merge-base --is-ancestor YES at every link; rev-list --count, all run this session):

f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548 ->(+8)-> 0a0a9c43 ->(+3)-> 8502146 ->(+5)-> 8eff64e ->(+3)-> d27af2d; f1b6e27..d27af2d = 34 commits (also f1b6e27..8eff64e = 31, 8502146..d27af2d = 8, c48a548..d27af2d = 19, 8eff64e..d27af2d = 3).

The +5 step 8502146..8eff64e: a4d8d50 (evolution whitepaper), 8cfebb44 (the case's SECOND desk action: landed the r17/r20 batch artifacts plus proposal line 21 upstream - 17 zgx-out paths measured this session, 16 A under zgx-out/r20-20261120T191930Z/ + 1 M ledger, zero docs/ paths), bd511c4 (u14), 63026ad (u15), 8eff64e (u16). The +3 step 8eff64e..d27af2d: a5c4a2a (u17), 2ed1c12 (u18), d27af2d (u19), all i18n unit re-lays. The whole span 8502146..d27af2d touches none of docs/scheduling-feedback.json, docs/exp-ledger.jsonl, docs/b-gate-audit.json (git log over the three paths: 0 rows, this session).

### 11.2 Nine-run six-tool comparison, value by value (ask item 1)

B1 carries the full compact reading (as in sections 2 and 10.2); B2-B7 cells are carried from sections 2 / 9.2 / 10.2; B8 (r22) and B9 (r24) cells carry this-session cmp evidence against the B7 captures. Where a committed-face property is batch-specific it is named in the cell.

| # | tool (step) | B1 R1 @f1b6e27 (221339Z) | B2 R2 @f1b6e27 | B3 R3 @f1b6e27 | B4 R4 @3e18590 | B5 r12 @3a56b85 (6998c40 label) | B6 r17 @c48a548 | B7 r20 @8502146 | B8 r22 @8eff64e (201318Z) | B9 r24 @d27af2d (212043Z) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready_classes 0/3; remaining_to_b=3; concl.real.const-lt-field-re-exists 1/1 not-ready; ineq.real.const-lt-field-re 0/0 not-ready; jargon 1/1 not-ready; errors=0 | identical | identical | identical (committed face == recompute) | identical | identical | identical | identical (out_1 byte-identical to B7's, cmp this session); committed face @8eff64e == B9's archived produced face (cmp rc=0 this session; blob 6c823880 at both anchors) | identical (out_1 byte-identical to B7's and B8's, cmp this session); committed face @d27af2d BYTE-IDENTICAL to the produced face (cmp rc=0, sha256 3c70b528 both sides) and to the R1-R4 recompute archive (cmp rc=0) |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration ledger_present=true entries=0 agreement_rate=null; feedback_edge=open; errors=0 | identical | identical | identical recompute; DIVERGENT vs committed face (section 4) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (10.3) | identical recompute (out_2 byte-identical to B7's, cmp this session); DIVERGENT vs committed face (11.3); produced face archived | identical recompute (in-run rerun out_2b byte-identical to out_2, cmp rc=0 this session - determinism re-verified); DIVERGENT (11.3); produced face archived, byte-identical to B8's (cmp this session), sha256 e66ca0a1 full value |
| 3 | jargon_map_sync (step 3) | mode=plan; md_faces=143; entries=159; count=159; appended=0 updated=0 unchanged=122 retagged=0; authority_kept=4; rejected=17; wrote=false; VERDICT IN-SYNC | identical | identical | identical | identical | identical | identical | identical (out_3 byte-identical to B7's, cmp) | identical (out_3 byte-identical to B7's and B8's, cmp) |
| 4 | pin_repair --plan (step 4) | ok=true action=none repairs=0 blocked=0 upstream-absent=2 (2 external snapshots SKIP-declared); repo doc pin d27b6402 == head, matched; VERDICT IN-SYNC | identical | identical | identical | identical; repo pin d27b6402 == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head (out_4 byte-identical to B7's, cmp) | same verdict; repo pin 83effa3f == head (out_4 byte-identical to B7's and B8's, cmp) |
| 5 | t_engines_seeds (step 5) | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0; declared skips: test_detector_anchor (D:/ instrument absent), snapshot + transcription glossary sources absent | identical | identical | identical | identical | identical | identical | identical stdout (out_5 byte-identical to B7's, cmp) | identical stdout (out_5 byte-identical to B7's and B8's, cmp) |
| 6 | t_engines_body (step 6) | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical | identical | identical | identical | identical | identical | identical (out_6 byte-identical to B7's, cmp) | identical (out_6 byte-identical to B7's and B8's, cmp) |

Nine-run matrix: all 54 tool-reading cells (6 tools x 9 runs) carry identical values, except two measured per-run byte classes, neither a reading difference: (i) tool 4's repo-pin sha pair moving d27b6402 -> 83effa3f between B5 and B6 (B6-B9 mutually byte-identical, cmp this session; input-tracking state, pin and pinned doc moved together and stayed matched); (ii) tool 5's stderr line, which differs between EVERY pair of runs exactly at the random tmpdir token of the expected fail-loud fixture (measured this session over r12/r17/r20/r22/r24: n84ph9jk / 3aytb82w / 9hz7f94y / qentrg7o / qk1v8jqi; same 206-byte shape otherwise; this refines the "only cross-anchor byte difference" wording of 9.2/10.2, which was scoped to stdout captures and specific pairs). Not green: none in any run.

Cross-run byte checks run this session (cmp): B8 vs B9 stdout captures 7 files compared (out_1, out_2, out_3, out_4, out_5, out_6, out_2b) - 6/6 identical, out_2b DIFFER because r22 archived no rerun capture (file absent, dir listing this session); B8 vs B7 stdout 6/6 IDENTICAL; B9 vs B7 stdout 6/6 IDENTICAL; all five divergence diffs (r12/r17/r20/r22/r24) are 471 bytes and byte-identical to each other (cmp x4 this session), index a952af0..06998c8; the archived r22 copies in return-package/ are byte-identical to the working r22 dir (7/7 cmp).

### 11.3 Divergence face at the new anchors (extends 9.3 / 10.3)

| face | repair_outcomes (repaired / unrecorded / rate) | wogc | escalated | blob | sha256 |
|---|---|---|---|---|---|
| committed @8eff64e | 3 / 46 / 0.0588 | 2 | 0 | a952af0 (rev-parse this session) | 1ed190e1 (same blob as d27af2d; sha256 measured at d27af2d) |
| committed @d27af2d | 3 / 46 / 0.0588 | 2 | 0 | a952af0 | 1ed190e1 (git show piped to shasum, this session) |
| recompute @8eff64e (B8) | 1 / 38 / 0.0244 | 2 | 0 | 06998c8 | e66ca0a1 (archived produced face, shasum this session) |
| recompute @d27af2d (B9) | 1 / 38 / 0.0244 | 2 | 0 | 06998c8 (git hash-object this session) | e66ca0a1 |

- The committed scheduling blob is a952af0 at every anchor this ledger has queried, now including 8eff64e and d27af2d; last touch still fa879e4 (git log -1, this session). Input side unchanged: docs/exp-ledger.jsonl at d27af2d = 41 rows, blob cf81fa36 (wc + rev-parse, this session).
- The B8 and B9 produced faces are byte-identical to each other (cmp rc=0, this session): the recompute is deterministic across two anchors, two runs, one host.
- docs/b-gate-audit.json at both new anchors: committed face byte-identical to the produced face (cmp rc=0 x2) and, at d27af2d, to the R1-R4 recompute archive (cmp rc=0); blob 6c823880 everywhere queried. The stale-face class remains scheduling-feedback-specific.
- Concurrent corroboration (cited, not re-derived here): R2-53's delivery-survival audit independently re-confirmed the a952af0 lineage at d27af2d via git log --all --find-object and recorded the regeneration proposal as still open/unapplied.

### 11.4 Divergence trajectory extension (extends sections 5, 9.4, 10.4)

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T8 (anchor 8, 6th sampling) | batch 201318Z; proposal ts 20:15:19Z | r22 at 8eff64e (5 commits past 8502146, spanning the desk landing 8cfebb44): same 3-value divergence, b-gate byte-identical; proposal line 22 cast into the loop-clone worktree ledger, then REVERTED by the seat's own zero-net-tree-write restore - the line survives only in return-package/r22-20261120T201318Z/zgx-ledger-proposals.post-append.jsonl and is absent from both live trees (shore line 22 is the fa879e4 archaeology line; committed loop ledger @8eff64e = 21 lines; wc + json.loads this session) | r22-plan-run.log; r22-divergence.diff; archived jsonl line 22 (json.loads this session) |
| T9 (anchor 9, 7th sampling) | batch 212043Z; proposal ts 21:22:43Z | r24 at d27af2d (3 commits past 8eff64e; the forward move itself was the disclosed unlogged actor event): same 3-value divergence, b-gate byte-identical; proposal line 23 appended to the shore ledger (22 -> 23), shore-working-tree only (committed upstream @d27af2d = 21 lines) | r24-run.log; r24-divergence.diff; shore jsonl line 23 (json.loads this session) |

Net after extension: the divergence is stable across all 9 reading runs and 7 sampling anchors (11.5), plus the committed-face-check-only anchors 6998c40 and 0a0a9c43 and the fa879e4 archaeology anchor (R2-44's birth-state rerun, per the R2-48/R2-53 records, not re-verified here), 34 upstream commits, 2 clones, two desk landings (0a0a9c43, 8cfebb44), and one disclosed unlogged fetch actor. Every reading-batch proposal for the case remains unapplied upstream.

### 11.5 Seven-sampling trend conclusions (ask item 2)

Trend A (divergence: persist / converge / fluctuate): PERSISTS, unbroken, and is VALUE-CONSTANT at every sampling - neither converging nor fluctuating.

| sampling | anchor (run) | committed face | recompute | diff | this-session evidence |
|---|---|---|---|---|---|
| 1 | f1b6e27 (R1=R2=R3) | 3/46/0.0588, wogc 2, escalated 0 | 1/38/0.0244, wogc 2, escalated 0 | same 3-value hunk | carried (sections 2-4) |
| 2 | 3e18590 (R4) | same | same | same | carried (sections 3-4) |
| 3 | 3a56b85 (r12) | same | same | same 471-byte diff | cmp r12 vs r24 diff IDENTICAL |
| 4 | c48a548 (r17) | same | same | same | cmp r17 vs r24 diff IDENTICAL |
| 5 | 8502146 (r20) | same | same | same | cmp r20 vs r24 diff IDENTICAL |
| 6 | 8eff64e (r22) | same (blob + values re-measured) | same | same | cmp r22 vs r24 diff IDENTICAL; committed blob a952af0 and parsed 3/46/0.0588, this session |
| 7 | d27af2d (r24) | same (blob + values + sha256 re-measured) | same | same | committed sha256 1ed190e1 and parsed 3/46/0.0588, produced blob 06998c8 via hash-object, all this session |

Every sampled quantity is identical at every sampling: repaired 3->1, unrecorded 46->38, repair_action_rate 0.0588->0.0244, watch_only_guard_correct 2 on both sides, escalated 0 on both sides. The committed face has not moved in 34 commits and has survived both desk landings, including 8cfebb44 - the landing that carried the case's own r17/r20 evidence upstream. The recompute shows zero drift (deterministic; B9's in-run rerun byte-identical, cmp rc=0 this session). Verdict for the ask's three-way choice: PERSIST, with zero value fluctuation and zero convergence. Case status remains OPEN; the root cause is adjudicated on the case-file side (H1 confirmed by R2-44, per the R2-48 record) - this ledger records, it does not re-adjudicate.

Counting note: samplings are numbered by the seats' own workorder count (R2-41 calls 8eff64e the 6th sampling; r24 calls d27af2d the 7th; the three f1b6e27 runs count as sampling 1). R2-47's receipt separately names a different "seven independent reading anchors" set (adds context 0765d671 and the fa879e4 archaeology, drops f1b6e27/3e18590); both enumerations are recorded, this table uses the workorder count.

Trend B (b-gate class-count trend): FLAT through all 9 runs and 34 commits: verdict not-ready, ready classes 0 of 3, remaining_to_b=3, per-class const-lt-field-re-exists 1/1, const-lt-field-re 0/0, jargon 1/1, errors 0, at every run including B8/B9; the committed b-gate face is byte-identical to the recompute at every anchor queried (cmp this session at 8eff64e and d27af2d; blob 6c823880). The B-gate pending state neither progressed nor regressed.

Trend C (proposal ledger growth): committed upstream 20 lines @8502146 -> 21 @8cfebb44 (the landing added committed line 21) -> 21 @8eff64e -> 21 @d27af2d (git show | wc -l at all four SHAs, this session). Shore live file: 23 lines - line 22 is the fa879e4 archaeology line (ts 20:55:47Z, per the R2-48 record), line 23 the d27af2d line (ts 21:22:43Z); the 8eff64e line (ts 20:15:19Z) exists in NO live tree, archived-only. The reading-batch chain for the case (lines 1, 2, 3, 4, 15, 19, 20, 21, [8eff64e archived-only], 22, 23) has strictly increasing ts (22:17:23Z, 23:02:10Z, 23:30:00Z, 23:46:58Z, 14:18:05Z, 15:42:14Z, 16:56:15Z, 19:24:17Z, 20:15:19Z, 20:55:47Z, 21:22:43Z); file-wide ts is non-decreasing (23/23 verified this session). The new lines record recurrence plus the standing regeneration / sync-guard proposal; no new root-cause claim; section 8 note 7 stands.

### 11.6 Proposal-ledger verification (this session): PASSED

Command: python3 -I /tmp/r2-51-jsonlcheck.py - per-line json.loads + ASCII + uniform-key-set + ts-order sweep over three sources (shore live file, r24 archived snapshot, r22 archived ledger); plus git show <sha>:zgx-out/zgx-ledger-proposals.jsonl | wc -l at four upstream SHAs.

Output: shore-live total_lines=23 parsed_ok=23 ascii_violations=0 key_sets=[actor,anchor,evidence,kind,points,schema,target,ts] ts_nondecreasing=True (line 21 anchor=8502146 ts=19:24:17Z; line 22 anchor=fa879e4 ts=20:55:47Z; line 23 anchor=d27af2d ts=21:22:43Z). r24 archived snapshot: 23/23, same tail. r22 archived ledger: 22/22, line 22 anchor=8eff64e ts=20:15:19Z. Committed upstream counts: 20 @8502146, 21 @8cfebb44, 21 @8eff64e, 21 @d27af2d. Line 23 is shore-working-tree only; the 8eff64e line is absent from all live trees (11.4).

### 11.7 Honesty notes (extension III)

1. This seat re-executed none of the six tools. B8/B9 readings are quoted from the r22/r24 archived captures, run logs, and receipts; the cross-run claims rest on the cmp / shasum / hash-object / json.loads / read-only git queries listed above, all run in this session. B1-B7 readings are carried over from sections 2, 9.2 and 10.2 without re-execution.
2. R2-50-receipt.md does not exist (checked at session start via Read and ls; re-checked late in the session). The 7th-sampling facts were taken from the r24 archive plus R2-47-receipt.md. No value was invented to fill that name, and this seat created no receipt numbered R2-50.
3. The ask's "eight-batch" numeral is recorded verbatim; its own anchor list resolves to nine runs over seven anchors (counting note at the section head). The table carries all nine runs; nothing was dropped to fit the numeral.
4. Zero network (NETRED honored); zero writes to any repo tree (all git invocations read-only at fixed SHAs with GIT_OPTIONAL_LOCKS=0; no checkout, no fetch by this seat); no proposal line appended; the only writes by this seat are this appended section and R2-51-receipt.md.
5. Concurrent-seat disclosure: R2-53 (delivery-survival audit at d27af2d) landed mid-session and was read after this seat's byte checks were already run; its independent corroborations (a952af0 lineage at d27af2d; 8cfebb44 = 17 paths, 16 A + 1 M; the 0a0a9c43 "41 items" reconciled as 38 landed + 3 pre-existing at the parent tree, refining 10.3's measured 38-path delta - different bases, both recorded) are cited in 11.3/11.4 and not re-derived here. No write conflict: R2-53 wrote only its own audit card and receipt.
6. Non-ASCII material (the zh jargon-rejection lines inside the out_3 captures, the D:/ zh upstream paths inside the out_4 captures, zh words inside upstream commit subjects) is referenced but not reproduced; this section is ASCII throughout (LC_ALL=C gate run after writing).
7. The 8eff64e proposal line's archived-only status is recorded, not repaired (repair belongs to the desk; r24 registered the observation in r24-run.log section 7).
8. The unlogged 2026-11-20T21:07:49Z fetch + checkout actor (8eff64e -> d27af2d) is disclosed by R2-47 and registered in netred_p6.md; unadjudicated by this ledger.

## 12. Batch extension section IV (2026-11-21, ticket R2-55b): ten-run full comparison and the eight-sampling trend

Ticket: R2-55b (ledger extension seat IV, read-only analysis; identity live-lumen, host Darwin arm64)
Date: 2026-11-21
Scope: extend sections 1-11 with the newest reading batch (r25 @ 4d76f4e, batch stamp 20261120T220606Z, the "8th sampling" per the ledger's own chapter count) into the full six-tool comparison over all runs on record, plus the ask-named eight-sampling divergence trend conclusion (persist / converge / fluctuate, value by value). This section appends no proposal line and writes nothing in any repo tree. Read this session: R2-50-receipt.md (the receipt that records the r25 batch; its seat's ticket is R2-48b), the r25-20261120T220606Z/ archive (t1..t6 tool outputs, t2-rerun, committed/produced scheduling faces, produced b-gate face, 406-byte diff artifact, r25-plan-run.log), the r24 archive, the R1-R4 zgx-out archives, and the shore proposals file; read-only git queries (GIT_OPTIONAL_LOCKS=0) against the rocqwash-loop clone at fixed SHAs (clone read at local HEAD=4d76f4e, origin/main=64fbc1d, working tree 0 status lines). Zero network. Every check quoted below was run in this session.

Source disclosure (fail-loud): the ask named R2-55-receipt.md (the 8th sampling) as input; that file does not exist - ls returned "No such file or directory" and grep over the b1-recursion dir returns 0 matches for R2-55 (checked this session). The 8th-sampling record was taken from the r25 archive plus R2-50-receipt.md, whose own header discloses its ticket as R2-48b and self-labels the seat "7th-sampling seat" (numbering overlap; see honesty note 4 below and the receipt's own honesty note 4). Nothing was invented to fill the R2-55 name, and this seat created no receipt under that number.

Counting note: the ask's "nine-batch" numeral is recorded verbatim; on disk it resolves to TEN six-tool runs (B1-B10) across eight sampling anchors (the three f1b6e27 runs count as sampling 1), continuing the established pattern (the R2-51 ask's "eight-batch" numeral likewise resolved to nine runs, section 11 counting note). The ask's other numeral, "eight-sampling", matches the disk exactly: f1b6e27, 3e18590, 3a56b85, c48a548, 8502146, 8eff64e, d27af2d, 4d76f4e are eight distinct divergence-sampling anchors. All ten runs are tabulated in 12.2 - nothing omitted to make either numeral fit.

### 12.1 Batch inventory extension and the extended anchor chain

| batch | collect stamp (UTC) | anchor | expected anchor | clone | record |
|---|---|---|---|---|---|
| R2-48b (r25) | 20261120T220606Z | 4d76f4e651791022c0dd925373df206d6ab08f7b | "d27af2d or newer" -> SATISFIED (4d76f4e is 7 commits past d27af2d) | rocqwash-loop | the "8th sampling" (ledger chapter count); fetch took 4 attempts over 3 backoffs (stall killed, rc=128 HTTP2 framing-layer, stall killed, then rc=0 via -c http.version=HTTP/1.1 - the transport knob is a fix for the diagnosed error, not a skipped fetch); pre-run tree clean; zero net tree write (post-restore status 0); proposal line 24 appended to the shore ledger, shore-working-tree only |

Anchor chain extension (git merge-base --is-ancestor YES at every link; rev-list --count, all run this session):

d27af2d ->(+7)-> 4d76f4e ->(+1)-> 9842e83 ->(+1)-> 64fbc1d; f1b6e27..64fbc1d = 43 commits (also d27af2d..64fbc1d = 9, d27af2d..4d76f4e = 7, 4d76f4e..64fbc1d = 2, f1b6e27..d27af2d = 34 carried from 11.1).

The +7 step d27af2d..4d76f4e: e775f91, 2bdc5ab, bbb0565, 2113080 (i18n unit re-lays v1/u20/v2/v3), 2220dca (feat(audit) P0 two-piece: tree_audit tool + evidence-annihilation triage class R19), cab9147 (v4), 4d76f4e (v5). The +2 past the sampling anchor: 9842e83 (i18n u1-slice five-field English header on the append-only ledger) and 64fbc1d (tree_audit counter-family extension). None of the 9 commits in d27af2d..64fbc1d touches zgx-out/ or any of docs/scheduling-feedback.json, docs/exp-ledger.jsonl, docs/b-gate-audit.json (git log over those paths = 0 rows, this session); the range's only touched paths are two zh-named doc pairs (9842e83), docs/recursive-evolution-whitepaper-v1.0-20261121.md and tools/tree_audit.py (64fbc1d).

### 12.2 Ten-run six-tool comparison, value by value

B1 carries the full compact reading (as in sections 2/10.2/11.2); B2-B9 cells are carried from sections 2 / 9.2 / 10.2 / 11.2; B10 cells carry this-session evidence against the B9 captures and the fixed-SHA queries.

| # | tool (step) | B1 R1 @f1b6e27 (221339Z) | B2 R2 @f1b6e27 | B3 R3 @f1b6e27 | B4 R4 @3e18590 | B5 r12 @3a56b85 | B6 r17 @c48a548 | B7 r20 @8502146 | B8 r22 @8eff64e | B9 r24 @d27af2d | B10 r25 @4d76f4e (220606Z) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready_classes 0/3; remaining_to_b=3; concl.real.const-lt-field-re-exists 1/1 not-ready; ineq.real.const-lt-field-re 0/0 not-ready; jargon 1/1 not-ready; errors=0 | identical | identical | identical (committed face == recompute) | identical | identical | identical | identical | identical (committed face == produced face, cmp rc=0 at d27af2d) | identical verdict (r25-plan-run.log t1); produced face byte-identical to committed @4d76f4e (cmp rc=0 this session) AND to the R1-R4 recompute archive (cmp rc=0 this session); blob 6c823880 at 4d76f4e/9842e83/64fbc1d (rev-parse this session) |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration ledger_present=true entries=0 agreement_rate=null; feedback_edge=open; errors=0 | identical | identical | identical recompute; DIVERGENT vs committed face (section 4) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (10.3) | identical recompute; DIVERGENT (11.3) | identical recompute (in-run rerun byte-identical); DIVERGENT (11.3) | identical recompute (values re-parsed this session: 1/38/0.0244, wogc 2, escalated 0, errors=[]; in-run rerun cmp rc=0 per log); produced face byte-identical to B9's produced face (cmp rc=0 this session); DIVERGENT vs committed face @4d76f4e (12.3) |
| 3 | jargon_map_sync (step 3) | mode=plan; md_faces=143; entries=159; count=159; appended=0 updated=0 unchanged=122 retagged=0; authority_kept=4; rejected=17; wrote=false; VERDICT IN-SYNC | identical | identical | identical | identical | identical | identical | identical | identical | identical (capture byte-identical to B9's, cmp this session) |
| 4 | pin_repair --plan (step 4) | ok=true action=none repairs=0 blocked=0 upstream-absent=2 (2 external snapshots SKIP-declared); repo doc pin d27b6402 == head, matched; VERDICT IN-SYNC | identical | identical | identical | identical; repo pin d27b6402 == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head (r25-plan-run.log t4; capture differs from B9's only by 3 lead "pin_repair:" preamble lines, diff 1,3d0 this session - capture-window shape, verdict lines identical) |
| 5 | t_engines_seeds (step 5) | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0; declared skips: test_detector_anchor (D:/ instrument absent), snapshot + transcription glossary sources absent | identical | identical | identical | identical | identical | identical | identical | identical stdout | identical (capture = B9's stdout + the merged stderr fixture lead line, diff 1d0 this session; the tmpdir token class moves qk1v8jqi (B9 stderr) -> 5ealhov0 (B10 lead line); 4390 = 4184 + 206 bytes) |
| 6 | t_engines_body (step 6) | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical | identical | identical | identical | identical | identical | identical | identical | identical (capture byte-identical to B9's, cmp this session) |

Ten-run matrix: all 60 tool-reading cells (6 tools x 10 runs) carry identical values, except the per-run byte classes already characterized in 11.2, which extend unchanged: (i) tool 4's repo-pin sha pair d27b6402 -> 83effa3f (input-tracking; B6-B10 mutually matched); (ii) tool 5's expected fail-loud fixture tmpdir token (now measured across six runs: n84ph9jk / 3aytb82w / 9hz7f94y / qentrg7o / qk1v8jqi / 5ealhov0), plus the newly observed capture-window class of the r25 archive (its t4/t5 captures carry stderr lead lines merged into the stdout stream; the B9 equivalents keep stderr separate - verdict lines identical either way). Not green: none in any run.

Cross-run byte checks run this session (cmp): r25 t1/t2/t2b/t3/t6 byte-identical to B9's captures (5/7 IDENTICAL); r25 t4/t5 differ only as named in rows 4-5; r25 committed-scheduling-feedback.json byte-identical to `git show 4d76f4e:docs/scheduling-feedback.json` (cmp rc=0); r25 produced-scheduling-feedback.json byte-identical to B9's produced face (cmp rc=0); r25 produced-b-gate-audit.json byte-identical to committed @4d76f4e and to the R1-R4 recompute archive b-gate-audit.20261119T232908Z.json (cmp rc=0 x2).

### 12.3 Divergence face at the new anchors (extends 9.3 / 10.3 / 11.3)

| face | repair_outcomes (repaired / unrecorded / rate) | wogc | escalated | blob (git hash-object / rev-parse, this session) | sha256 (shasum, this session) |
|---|---|---|---|---|---|
| committed @4d76f4e | 3 / 46 / 0.0588 | 2 | 0 | a952af079aa8e6baf68b38f60a5d68248963d86e | 1ed190e1 |
| recompute @4d76f4e (B10) | 1 / 38 / 0.0244 | 2 | 0 | 06998c8fbbcf3d88087d370fc1556bcb3fce8b08 | e66ca0a1 |
| committed @9842e83 | same blob (rev-parse this session; values not re-parsed) | - | - | a952af0 | - |
| committed @64fbc1d | same blob (rev-parse this session; values not re-parsed) | - | - | a952af0 | - |

- The committed scheduling blob is a952af0 at every anchor this ledger has queried, now including 4d76f4e, 9842e83 and 64fbc1d; last touch still fa879e4 (git log -1 --find-object: single introducing commit, no later move; git log -1 on the path at d27af2d, this session). Input side unchanged: docs/exp-ledger.jsonl at 4d76f4e and 64fbc1d = 41 rows, blob cf81fa36 (wc + rev-parse, this session).
- B10's produced face is byte-identical to B9's (cmp rc=0): the recompute remains deterministic across a third anchor and run on this host.
- docs/b-gate-audit.json at 4d76f4e: produced face byte-identical to the committed face and to the R1-R4 recompute archive (cmp rc=0 x2); blob 6c823880 at 4d76f4e/9842e83/64fbc1d. The stale-face class remains scheduling-feedback-specific.
- Artifact note (honesty): the r25 divergence diff artifact is 406 bytes, regenerated post-restore from the captured faces (R2-50-receipt honesty note 3), so it is not one of the five byte-identical 471-byte chapter diffs; the blob pair a952af0/06998c8 for the r25 chapter was instead established this session via git hash-object of the two captured faces, and the parsed hunk is the same 3-value change (repair_action_rate 0.0588->0.0244, repaired 3->1, unrecorded 46->38; the hunk is quoted verbatim in the 406-byte artifact and re-derived from the parsed faces this session).

### 12.4 Divergence trajectory extension (extends sections 5, 9.4, 10.4, 11.4)

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T10 (anchor 10, 8th sampling) | batch 220606Z; proposal ts 22:07:28Z | r25 at 4d76f4e (7 commits past d27af2d, spanning the feat(audit) P0 landing 2220dca): same 3-value divergence, b-gate byte-identical; proposal line 24 appended to the shore ledger (23 -> 24), shore-working-tree only (committed upstream @4d76f4e = 21 lines, git show | wc -l this session); the line's own text carries the receipt's numbering-overlap disclosure | r25-plan-run.log; R2-50-receipt.md; shore jsonl line 24 (json.loads this session, 12.6) |

Net after extension: the divergence is stable across all 10 reading runs and 8 sampling anchors (12.5), plus the committed-face-check-only anchors 6998c40, 0a0a9c43, 8cfebb4 and the fa879e4 archaeology anchor, 43 upstream commits, 2 clones, two desk landings (0a0a9c43, 8cfebb44) plus the feat(audit) P0 landing (2220dca), and one disclosed unlogged fetch actor. Every reading-batch proposal for the case remains unapplied upstream: the committed face is a952af0 at every commit queried through 64fbc1d.

### 12.5 Eight-sampling trend conclusions (ask item 2)

Trend A (divergence: persist / converge / fluctuate): PERSISTS, unbroken, and is VALUE-CONSTANT at every sampling - neither converging nor fluctuating.

| sampling | anchor (run) | committed face | recompute | diff | this-session evidence |
|---|---|---|---|---|---|
| 1 | f1b6e27 (R1=R2=R3) | 3/46/0.0588, wogc 2, escalated 0 | 1/38/0.0244, wogc 2, escalated 0 | same 3-value hunk | carried (sections 2-4) |
| 2 | 3e18590 (R4) | same | same | same | carried (sections 3-4) |
| 3 | 3a56b85 (r12) | same | same | same 471-byte diff | carried (11.5: cmp vs r24 IDENTICAL) |
| 4 | c48a548 (r17) | same | same | same | carried (11.5: cmp vs r24 IDENTICAL) |
| 5 | 8502146 (r20) | same | same | same | carried (11.5: cmp vs r24 IDENTICAL) |
| 6 | 8eff64e (r22) | same | same | same | carried (11.5: cmp vs r24 IDENTICAL) |
| 7 | d27af2d (r24) | same | same | same | carried (11.5, blob/sha256 re-measured there) |
| 8 | 4d76f4e (r25) | same (blob + values + sha256 re-measured this session: a952af0, 3/46/0.0588, 1ed190e1) | same (blob + values re-measured: 06998c8, 1/38/0.0244, e66ca0a1; byte-identical to B9's produced face) | same 3-value hunk (hash-object pair a952af0..06998c8 re-established) | all hash-object / shasum / cmp / json.loads rows in 12.2-12.3 |

Every sampled quantity is identical at every sampling: repaired 3->1, unrecorded 46->38, repair_action_rate 0.0588->0.0244, watch_only_guard_correct 2 on both sides, escalated 0 on both sides. The committed face has not moved in 43 commits, has survived both desk landings (including 8cfebb44, which carried the case's own r17/r20 evidence upstream) and the feat(audit) P0 landing, and is unchanged at the two commits past the 8th-sampling anchor (9842e83, 64fbc1d - both queried this session). The recompute shows zero drift across three anchors (B8=B9=B10 produced faces, cmp rc=0 x2 this session). Verdict for the ask's three-way choice: PERSIST, with zero value fluctuation and zero convergence. Case status remains OPEN; the root cause stands as adjudicated on the case-file side (H1 confirmed by R2-44, per the R2-48 record); this ledger records, it does not re-adjudicate.

Counting note (carried): samplings are numbered by the ledger's own chapter count, which treats the three f1b6e27 runs as sampling 1 (section 11.5). R2-50-receipt (the r25 seat) self-labels "7th-sampling seat" under a different enumeration; the overlap is disclosed in the receipt's honesty note 4 and inside proposal line 24 itself, and both enumerations are recorded here.

Trend B (b-gate class-count trend): FLAT through all 10 runs and 43 commits: verdict not-ready, ready classes 0 of 3, remaining_to_b=3, per-class const-lt-field-re-exists 1/1, const-lt-field-re 0/0, jargon 1/1, errors 0, at every run including B10; the committed b-gate face is byte-identical to the recompute at every anchor queried (this session: cmp rc=0 x2 at 4d76f4e; blob 6c823880 at 4d76f4e/9842e83/64fbc1d). The B-gate pending state neither progressed nor regressed.

Trend C (proposal ledger growth): committed upstream remains 21 lines at every SHA queried this session (d27af2d, 4d76f4e, 9842e83, 64fbc1d - git show | wc -l x4, blob 1d910324 constant). Shore live file: 24 lines - line 22 = fa879e4 archaeology (ts 20:55:47Z), line 23 = d27af2d (ts 21:22:43Z), line 24 = 4d76f4e (ts 22:07:28Z); the 8eff64e line (ts 20:15:19Z) exists in NO live tree, archived-only (11.4). The reading-batch chain for the case (lines 1, 2, 3, 4, 15, 19, 20, 21, [8eff64e archived-only], 22, 23, 24) has strictly increasing ts through 22:07:28Z; file-wide ts is non-decreasing (24/24 verified this session). Line 24 records recurrence plus the standing regeneration / sync-guard proposal; no new root-cause claim; section 8 note 7 stands.

### 12.6 Proposal-ledger verification (this session): PASSED

Command (this session): python3 -I heredoc - per-line json.loads over /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl with actor/kind/schema/key-set/ASCII assertions and a ts-order sweep.

Output: total_lines=24 parsed_ok=24 ascii_ok=True key_sets=[actor,anchor,evidence,kind,points,schema,target,ts] ts_nondecreasing=True; line 22 anchor=fa879e4 ts=2026-11-20T20:55:47Z; line 23 anchor=d27af2d ts=2026-11-20T21:22:43Z; line 24 anchor=4d76f4e ts=2026-11-20T22:07:28Z. Committed upstream counts re-verified: 21 lines at d27af2d, 4d76f4e, 9842e83, 64fbc1d (git show | wc -l x4, this session) - lines 22-24 are shore-working-tree only, the same uncommitted posture as every earlier batch line (section 8 note 4).

### 12.7 Honesty notes (extension IV)

1. This seat re-executed none of the six tools. B10 readings are quoted from the r25 archive captures, r25-plan-run.log, and R2-50-receipt.md; the cross-run claims rest on the cmp / hash-object / shasum / json.loads / read-only git queries listed above, all run in this session. B1-B9 readings are carried over from sections 2, 9.2, 10.2 and 11.2 without re-execution.
2. R2-55-receipt.md does not exist (checked via ls and grep this session; 0 matches). The 8th-sampling facts were taken from the r25 archive plus R2-50-receipt.md. No value was invented to fill that name, and this seat created no receipt numbered R2-55.
3. The ask's "nine-batch" numeral is recorded verbatim; its disk resolution is ten runs over eight sampling anchors (counting note at the section head). The table carries all ten runs; nothing was dropped to fit the numeral.
4. Numbering overlap: R2-50-receipt self-labels "7th-sampling seat" (ticket R2-48b) while the ledger's chapter chain makes d27af2d the 7th sampling and 4d76f4e the 8th; the receipt discloses this itself (its honesty note 4) and the overlap is written into proposal line 24. This ledger uses the chapter count; both enumerations recorded.
5. The r25 archive's t4/t5 captures carry stderr lead lines merged into the stdout stream (3 pin_repair preamble lines; the seeds fixture line with tmpdir token 5ealhov0), unlike B9's separate-stream captures; verdict lines are byte-identical either way (diff shapes 1,3d0 and 1d0, this session). The r25 divergence diff artifact is a 406-byte post-restore regeneration, not a fifth 471-byte chapter diff; the chapter's blob pair was established via git hash-object instead (12.3).
6. Zero network (NETRED honored); zero writes to any repo tree (all git invocations read-only queries at fixed SHAs, GIT_OPTIONAL_LOCKS=0; no checkout, no fetch by this seat; rocqwash-loop read at local HEAD=4d76f4e with origin/main=64fbc1d, working tree 0 status lines); no proposal line appended; the only writes by this seat are this appended section, the ask-named delivery-survival-audit-64fbc1d-20261121.md, and R2-56-receipt.md.
7. Non-ASCII material (zh upstream commit subjects in d27af2d..64fbc1d, the zh doc paths of 9842e83, the zh jargon faces inside the t3 captures) is referenced by short sha / file name only and not reproduced; this section is ASCII throughout (LC_ALL=C gate run after writing).
8. 9842e83 and 64fbc1d are committed-face-check-only anchors for tool 2 (blob queried, values not re-parsed); no tool has run at either. The 0765d671 (r5) and fa879e4 (archaeology) anchors remain context-only as in 11.4.
9. Post-session concurrent-actor observation (fail-loud, recorded not adjudicated): at 06:47 +0800 2026-11-21, after this section's checks were complete, the rocqwash-loop clone showed HEAD moved 4d76f4e -> 64fbc1d (a checkout this seat did not perform) and one modified path, docs/scheduling-feedback.json, carrying the canonical 3-value hunk (diff index a952af0..06998c8; file mtime 06:44:46 +0800) - most plausibly a concurrent reading seat running learning_feedback.py at the tip and not yet restored. This seat restored nothing (zero-write discipline in both directions) and does not count that run as a sampling: no receipt/archive of it is on file from this seat's viewpoint. Every state statement in this section refers to the read-time state (local HEAD=4d76f4e, status 0 lines), which was measured and held during all of this section's queries.

## 13. Batch extension section V (2026-11-21, ticket R2-62): eleven-run full comparison and the post-verdict case chapter

Ticket: R2-62 (ledger extension seat V, read-only analysis; identity live-lumen, host Darwin arm64)
Date: 2026-11-21
Scope: extend sections 1-12 with the newest reading batch (r26 @ 64fbc1d, batch stamp 20261120T224020Z, seat R2-54b, receipt R2-55-receipt.md) into the ask's "nine batches -> eleven batches" full six-tool comparison over all runs on record, including the ask-named anchors 8eff64e / 64fbc1d / new anchors; plus the ask-named post-verdict case-file status chapter (H1 confirmed; ghost 10 rows unrecoverable; Option A package ready). This section appends no proposal line and writes nothing in any repo tree. Read this session: R2-44-receipt.md, R2-47-receipt.md, R2-50-receipt.md, R2-55-receipt.md, R2-57-receipt.md, the case file v2 (divergence-case-scheduling-feedback-v2-20261121.md sections 1-10), the Option A package (option-a-package/OPTION-A-LANDING-COMMANDS.md + option-a-package/scheduling-feedback.regenerated.json), the r26 archive (t1..t6 captures, t2-rerun, committed+produced faces, 471-byte diff, r26-plan-run.log), the r24/r25 archives, and the shore proposals file; read-only git queries (GIT_OPTIONAL_LOCKS=0) against the rocqwash-loop clone at fixed SHAs (clone read at local HEAD = origin/main = 02ccffd, working tree 0 status lines). Zero network. Every check quoted below was run in this session.

Two disclosures at the section head:

1. Fail-loud file-state reconciliation: R2-50-receipt.md, recorded absent at section 11's time (its honesty note 2), is on file now (mtime 2026-11-21 06:08) as the r25 batch's receipt; this seat re-read it and found its content matches the section 12 record - no correction needed. Likewise R2-55-receipt.md, recorded absent at section 12's time (its honesty note 2), is on file now (mtime 06:48) as the r26 batch's receipt; section 12's statement was true at its own read time and is superseded by this note, not contradicted.
2. Tool-execution disclosure (first for an extension seat of this ledger): this seat ran tools/learning_feedback.py twice inside a /tmp sandbox (git archive export of 02ccffd; the R2-44 birth-state sandbox precedent; zero repo-tree writes; scratch deleted after). The trigger is an unrecorded state change this seat found on the case's input side: the ghost-row input state is now ON-REF upstream (13.7), which made the H1 inverse test - recorded NOT RUN (impossible) by R2-44 / case v2 section 4.3 - runnable for the first time. The runs are labeled sandbox measurements, not a reading batch; no six-tool batch exists at 02ccffd on file or from this seat.

Counting note: the ask's numerals are recorded verbatim. "Nine batches" was the previous ask's numeral (section 12 resolved it to the ten runs B1-B10); "eleven batches" resolves exactly on disk: ELEVEN six-tool runs (B1-B11, the eleventh being r26) over NINE distinct sampling anchors by the chapter count (the three f1b6e27 runs count as sampling 1; 4d76f4e = 8th; 64fbc1d = 9th). The ask's named anchors: 8eff64e is B8 (full run, carried from section 11); 64fbc1d was a committed-face-check-only anchor in section 12 and is now B11, a full run; the new post-batch anchor 02ccffd is face/input-check-only plus the disclosed sandbox measurement (no batch tool has run there). Numbering overlap (carried): r26 self-labels "8th sampling" (ticket R2-54b; receipt and ledger line 25 carry it), the chapter count makes it the 9th sampling anchor and 11th run; both enumerations recorded, this section uses the chapter count. Nothing was omitted to make any numeral fit.

### 13.1 Batch inventory extension and the extended anchor chain

| batch | collect stamp (UTC) | anchor | expected anchor | clone | record |
|---|---|---|---|---|---|
| R2-54b (r26) | 20261120T224020Z | 64fbc1d222f3c830ff76bdac99987d63e15f2234 | "64fbc1d or newer" -> SATISFIED exactly (rev-list --count 4d76f4e..HEAD = 2) | rocqwash-loop | self-labels "8th sampling" (R2-54b); fetch: attempt 1 rc=128 "not a git repository" (seat-side cd reset, no network attempted, logged verbatim), re-run stalled >45s and was killed, 120s backoff, attempt 2 via -c http.version=HTTP/1.1 rc=0 (the r25-diagnosed transport fix); pre-checkout tree clean; zero net tree write (post-restore status 0); proposal line 25 appended to the shore ledger, shore-working-tree only |

Anchor chain extension (git merge-base --is-ancestor YES at every link; rev-list --count, all run this session):

f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548 ->(+8)-> 0a0a9c43 ->(+3)-> 8502146 ->(+5)-> 8eff64e ->(+3)-> d27af2d ->(+7)-> 4d76f4e ->(+1)-> 9842e83 ->(+1)-> 64fbc1d ->(+6)-> 02ccffd; f1b6e27..64fbc1d = 43 (re-verified this session), f1b6e27..02ccffd = 49, 64fbc1d..02ccffd = 6.

The +6 post-batch step 64fbc1d..02ccffd: 180e36d (i18n unit-r1u1 gate4), 43fca6a (i18n unit-r2u2 whitepaper basis-annotation), 69ff756 (i18n unit-r2u1 wash engine), 19257b7 (evolve cycle6 re-harvest), 02da21f (README family refresh), 02ccffd ("fix(R20): restore guard-pinned v55 snapshot line (row N1); triage v1.6 + whitepaper R20 section", adate 2026-11-21T10:17:51+08:00). 02ccffd touches exactly 4 paths (git show --name-status, this session): README.md, docs/ci-triage-table.json, docs/ci-whitepaper-recursive-era-v1-20261116.md, docs/exp-ledger.jsonl. None of the 6 commits touches docs/scheduling-feedback.json or docs/b-gate-audit.json: the face blob is a952af0 at 64fbc1d and 02ccffd (rev-parse x2, this session), face last touch is still fa879e412b0312fcc7deaa3e47d8229e6c6b1ba0 at 02ccffd (git log -1, this session), and the b-gate blob is 6c8238804de36fa94d24f12131ca696f9404983d at 9842e83, 64fbc1d and 02ccffd (rev-parse x3, this session). 02ccffd DOES append 19 rows to docs/exp-ledger.jsonl (cf81fa36 -> babbfe2f, 41 -> 60 rows; byte-prefix append verified by cmp, this session) - the case-material input-side move, discharged in 13.7. The freshness seat R2-57 (window 10:45-10:49 +0800) independently recorded origin/main at 02ccffd with 0 new commits at its own fetch - cited, not re-derived.

### 13.2 Eleven-run six-tool comparison, value by value

B1 carries the full compact reading (as in sections 2/10.2/11.2/12.2); B2-B10 cells are carried from those sections; B11 cells carry this-session cmp evidence against the B9/B10 captures and the fixed-SHA queries of 13.1/13.3.

| # | tool (step) | B1 R1 @f1b6e27 (221339Z) | B2 R2 | B3 R3 | B4 R4 @3e18590 | B5 r12 @3a56b85 | B6 r17 @c48a548 | B7 r20 @8502146 | B8 r22 @8eff64e | B9 r24 @d27af2d | B10 r25 @4d76f4e | B11 r26 @64fbc1d (224020Z) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | b_gate_audit -> docs/b-gate-audit.json | verdict=not-ready; ready_classes 0/3; remaining_to_b=3; concl.real.const-lt-field-re-exists 1/1 not-ready; ineq.real.const-lt-field-re 0/0 not-ready; jargon 1/1 not-ready; errors=0 | identical | identical | identical (committed face == recompute) | identical | identical | identical | identical | identical (committed == produced, cmp rc=0) | identical (produced == committed @4d76f4e and == R1-R4 archive, cmp rc=0 x2) | identical verdict (r26-plan-run.log t1; t1 capture 559 B byte-identical to B9's stdout capture, cmp this session); produced b-gate byte-identical to committed @64fbc1d (cmp rc=0 this session); blob 6c823880 at 64fbc1d and 02ccffd |
| 2 | learning_feedback -> docs/scheduling-feedback.json | rounds total=2 auto=1 human_approved=1 approval_rate_auto=0.5; repair repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244; calibration ledger_present=true entries=0 agreement_rate=null; feedback_edge=open; errors=0 | identical | identical | identical recompute; DIVERGENT vs committed face (section 4) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (9.3) | identical recompute; DIVERGENT (10.3) | identical recompute; DIVERGENT (11.3) | identical recompute (in-run rerun byte-identical); DIVERGENT (11.3) | identical recompute; DIVERGENT (12.3) | identical recompute (out_2 and t2-rerun captures 399 B each, byte-identical to B9's out_2 and out_2b, cmp this session; in-run rerun cmp rc=0 per r26 log); produced face byte-identical to B9's AND B10's produced faces (cmp rc=0 x2 this session); DIVERGENT vs committed face @64fbc1d (13.3) |
| 3 | jargon_map_sync (step 3) | mode=plan; md_faces=143; entries=159; count=159; appended=0 updated=0 unchanged=122 retagged=0; authority_kept=4; rejected=17; wrote=false; VERDICT IN-SYNC | identical | identical | identical | identical | identical | identical | identical | identical | identical | identical (capture 1628 B byte-identical to B9's, cmp this session) |
| 4 | pin_repair --plan (step 4) | ok=true action=none repairs=0 blocked=0 upstream-absent=2 (2 external snapshots SKIP-declared); repo doc pin d27b6402 == head, matched; VERDICT IN-SYNC | identical | identical | identical; repo pin d27b6402 == head | same verdict; repo pin d27b6402 == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head | same verdict; repo pin 83effa3f == head (t4 capture = B9's + 3 merged preamble lines, diff 1,3d0) | same verdict; repo pin 83effa3f == head (r26 log t4); t4 capture 1971 B BYTE-IDENTICAL to B10's t4 (cmp this session) - the merged-preamble capture class, vs B9's separate-stream 1762 B (diff 1,3d0 class, section 12) |
| 5 | t_engines_seeds (step 5) | TOTAL-SELFTEST GREEN; segments=5 expected=5 passed=43 failed=0 missing=0; declared skips: test_detector_anchor (D:/ instrument absent), snapshot + transcription glossary sources absent | identical | identical | identical | identical | identical | identical | identical | identical stdout | identical (t5 = B9 stdout + merged fixture lead, 4390 = 4184 + 206; token 5ealhov0) | identical verdict (r26 log t5: 43 passed, 5/5 segments, 3 declared SKIPs); t5 capture 4390 B = B9 stdout + merged 206 B stderr lead (same class as B10); vs B10's t5 differs in EXACTLY one line (diff 1c1, this session): the tmpdir token 5ealhov0 -> h4az___q |
| 6 | t_engines_body (step 6) | TOTAL-ENGINES-BODY GREEN; segments=9 passed=60 failed=0 skipped=0 | identical | identical | identical | identical | identical | identical | identical | identical | identical | identical (capture 7141 B byte-identical to B9's, cmp this session) |

Eleven-run matrix: all 66 tool-reading cells (6 tools x 11 runs) carry identical values, except the per-run byte classes already characterized in 11.2/12.2, which extend unchanged: (i) tool 4's repo-pin sha pair d27b6402 -> 83effa3f (input-tracking; B6-B11 mutually matched); (ii) tool 5's expected fail-loud fixture tmpdir token, now measured across seven runs (n84ph9jk / 3aytb82w / 9hz7f94y / qentrg7o / qk1v8jqi / 5ealhov0 / h4az___q); (iii) the capture-window class first seen in the r25 archive recurs in r26 with the same shapes (t4 merged preamble byte-identical to r25's; t5 merged fixture lead differing only at the token line). Not green: none in any run.

Cross-run byte checks run this session (cmp): r26 t1/t2/t2-rerun/t3/t6 byte-identical to B9's stdout captures (5/7 IDENTICAL: 559/399/399/1628/7141 B); r26 t4 == B10's t4 (IDENTICAL); r26 t5 vs B10's t5 differs only at the token line (1c1); r26's scheduling-feedback.diff is 471 bytes and byte-identical to all four canonical chapter diffs (r12/r17/r20/r22; cmp rc=0 x4) and NOT identical to r25's 406-byte post-restore regeneration (the generator-shape difference recorded in 12.3); r26's committed-scheduling-feedback.json is byte-identical to `git show 64fbc1d:docs/scheduling-feedback.json` (cmp rc=0); r26's produced-scheduling-feedback.json is byte-identical to BOTH B9's and B10's produced faces (cmp rc=0 x2) - the recompute is deterministic across a fourth anchor and run on this host; r26's produced-b-gate-audit.json is byte-identical to the committed face at 64fbc1d (cmp rc=0).

### 13.3 Divergence face at B11 and the post-batch input-side move (extends 9.3 / 10.3 / 11.3 / 12.3)

| face | repair_outcomes (repaired / unrecorded / rate) | wogc | escalated | blob | sha256 |
|---|---|---|---|---|---|
| committed @64fbc1d (B11 anchor) | 3 / 46 / 0.0588 | 2 | 0 | a952af0 (rev-parse this session) | 1ed190e1 (per r26 log; blob re-verified this session) |
| recompute @64fbc1d (B11) | 1 / 38 / 0.0244 | 2 | 0 | 06998c8 (r26 log blob pair) | e66ca0a1 (r26 log; produced face cmp'd == B9/B10 this session) |
| committed @9842e83 and @02ccffd | same blob (rev-parse this session; values not re-parsed from the blob) | - | - | a952af0 | - |
| sandbox recompute @02ccffd over the committed 60-row input (this seat, /tmp, disclosed) | 5 / 53 / 0.0833 | 2 | 0 | ba7d081cf2ff79ba7b1acf72999ca1f1ecc4f3c5 (git hash-object in sandbox) | 572061ef7ba4ebbb0d75a0c1700102cf9ed0667c3c0c8713157abf99045478d1 (shasum, this session) |

- At 64fbc1d the chapter's closed form holds byte-for-byte: committed a952af0 / 3/46/0.0588 vs produced 06998c8 / 1/38/0.0244, the same 471-byte three-value hunk (13.2), b-gate byte-identical both sides, input ledger cf81fa36 / 41 rows at 64fbc1d (rev-parse + wc, this session).
- Post-batch, at 02ccffd: the committed face is unchanged (a952af0; last touch still fa879e4) but the input ledger MOVED to babbfe2f691436b2c67c7e59520dc41e95cd8b96, 60 rows (cf81fa36 is a byte-prefix of babbfe2f, cmp this session; +19 rows). The sandbox measurement (rc=0, errors: 0) shows the divergence at the tip persists with a NEW 3-value shape: repaired 3->5, unrecorded 46->53, rate 0.0588->0.0833, wogc 2 and escalated 0 unchanged on both sides - the old index pair a952af0..06998c8 no longer describes the tip. This is a sandbox measurement, NOT a sampling; no reading batch on file has run at 02ccffd.

### 13.4 Divergence trajectory extension (extends sections 5, 9.4, 10.4, 11.4, 12.4)

| # | time (UTC) | event | evidence |
|---|---|---|---|
| T11 (run 11, 9th sampling anchor) | batch 224020Z; proposal ts 22:47:09Z | r26 at 64fbc1d (2 commits past 4d76f4e): same 3-value divergence, b-gate byte-identical; proposal line 25 appended to the shore ledger (24 -> 25), shore-working-tree only (committed upstream @64fbc1d = 21 lines, git show | wc -l this session); the line carries the seat's own numbering note (its "8th sampling" label vs the chapter chain's 9th anchor) | r26-plan-run.log; R2-55-receipt.md; shore jsonl line 25 (json.loads this session, 13.6) |

Net after extension: eleven runs, nine sampling anchors (chapter count), plus the face/input-check-only anchors 6998c40, 0a0a9c43, 8cfebb44, 9842e83 and the fa879e4 archaeology anchor; 49 upstream commits through 02ccffd; 2 clones; two desk landings, the feat(audit) P0 landing, and now the R20 landing (02ccffd) - the first landing that changes the case's input side (13.7); one disclosed unlogged fetch actor. The value-constant streak (identical committed/produced face pair at every sampling) holds through 64fbc1d unbroken; 02ccffd changed the input side, not the face.

### 13.5 Trend conclusions update (extends 9.5 / 10.5 / 11.5 / 12.5)

Trend A (divergence persistence): PERSISTS, unbroken and VALUE-CONSTANT at all nine sampled anchors through 64fbc1d - every sampled quantity identical everywhere (repaired 3->1, unrecorded 46->38, rate 0.0588->0.0244, wogc 2 / escalated 0 both sides); sampling 9 = 64fbc1d (r26), carried by the cmp evidence of 13.2/13.3. Post-batch at 02ccffd the committed face is unchanged while the input moved, so the tip's face pair reads (3/46/0.0588 vs 5/53/0.0833) by sandbox measurement - still exactly a 3-value repair_outcomes hunk with wogc/escalated unchanged, still stale-face-on-ref, but unmeasured by any batch and therefore recorded as a post-batch development, not a tenth sampling. Verdict for the ask's persist/converge/fluctuate choice: PERSIST with zero value fluctuation and zero convergence through the nine sampled anchors; no convergence at the tip either.

Trend B (b-gate class-count trend): FLAT through all 11 runs and 49 commits: verdict not-ready, ready classes 0 of 3, remaining_to_b=3, per-class const-lt-field-re-exists 1/1, const-lt-field-re 0/0, jargon 1/1, errors 0, at every run including B11; the committed b-gate face is byte-identical to the recompute at every anchor queried (this session: cmp rc=0 at 64fbc1d; blob 6c823880 at 9842e83 / 64fbc1d / 02ccffd). Neither progressed nor regressed.

Trend C (proposal ledger growth): shore live file 24 -> 25 lines (line 25 = anchor 64fbc1d, ts 2026-11-20T22:47:09Z); committed upstream stays 21 lines at every SHA queried (d27af2d, 4d76f4e, 9842e83, 64fbc1d, 02ccffd; this session x2 new; zgx-out untouched in 64fbc1d..02ccffd, git diff --stat = 0 lines); the 8eff64e line remains archived-only (11.4). The reading-batch chain for the case (lines 1, 2, 3, 4, 15, 19, 20, 21, [8eff64e archived-only], 22, 23, 24, 25) has strictly increasing ts through 22:47:09Z; file-wide ts is non-decreasing (25/25 verified this session). Line 25 records recurrence plus the standing regenerate-and-land / sync-guard proposal; no new root-cause claim; section 8 note 7 stands.

### 13.6 Proposal-ledger verification (this session): PASSED

Command (this session): python3 -I heredoc - per-line json.loads over /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl with actor/schema/key-set/ASCII assertions and a ts-order sweep.

Output: total_lines=25, all lines parse, all ASCII, uniform 8-key set (actor,anchor,evidence,kind,points,schema,target,ts), actor=zgx, schema=zgx-proposal/1, ts non-decreasing=True; line 24 anchor=4d76f4e ts=2026-11-20T22:07:28Z; line 25 anchor=64fbc1d ts=2026-11-20T22:47:09Z. Committed upstream counts re-verified: 21 lines at 64fbc1d and 02ccffd (git show | wc -l x2, this session) - lines 22-25 are shore-working-tree only, the same uncommitted posture as every earlier batch line (section 8 note 4).

### 13.7 Case chapter after the root-cause verdict (ask item 2): H1 confirmed; the ghost 10 rows, unrecoverable at recon time, are now ON-REF; the Option A package is on file with its applicability boundary now measured

(a) The verdict as on file (carried by reference, not re-adjudicated): R2-44 confirmed H1 HIGH - the canonical face a952af0 was born stale in one commit, fa879e4 (2026-11-19T17:40:19Z), which rewrote the tool (v1.0 -> v1.1.0) and landed the face computed from a then-local 51-row dev-tree exp-ledger (+2 action=fix-content, +8 token-less vs shore cf81fa36/41; window (2026-11-18T17:05:56Z, 2026-11-19T17:40:19Z]) without landing its input rows; H1 survived two falsification runs (birth-state sandbox rerun -> 06998c8; all-refs census -> exactly 4 ledger blobs in a strict prefix chain, no 51-row state anywhere). Case file v2 section 4 is the canonical statement; R2-44-receipt.md section "Result" and its ask correction (total delta 10 rows, not 8) stand as written.

(b) "Ghost 10 rows unrecoverable" - the R2-44 statement is scoped ("unrecoverable on this host"; "never landed to any ref" AT RECON TIME) and remains true as scoped. This session found the state changed upstream: commit 02ccffd appended 19 rows to docs/exp-ledger.jsonl (cf81fa36/41 -> babbfe2f/60; byte-prefix append verified, 13.1/13.3). Rows 42-51 are EXP-20261119-0001..0010 with ts 2026-11-19T07:19:17Z..2026-11-19T16:43:14Z - ALL inside the ghost window - and classify, by the tool's own REPAIR_TOKENS first-match vocabulary (substring over the serialized row; the C2 manual re-count method of record, proposal line 19), as EXACTLY +2 action=fix-content (rows 45 = EXP-20261119-0004, 49 = EXP-20261119-0008) + 8 token-less: the ghost-row signature, shape and window both. Rows 52-60 (ts 2026-11-19T20:50:12Z..2026-11-21T02:15:35Z, all after the face's birth) classify +2 fix-content +7 token-less. No receipt or card on file records this connection (R2-57 recorded the tip's freshness only; R2-60 registered ai_flavor cards only); it is this seat's finding, grounded in the blobs and rows quoted above.

(c) The H1 inverse test, recorded NOT RUN (impossible - rows unrecoverable) by R2-44 / case v2 section 4.3, is NOW RUN (this session, /tmp sandbox, disclosure at the section head): the ghost-state ledger assembled from on-ref bytes alone (cf81fa36 prefix + rows 42-51 = 51 rows) fed to tools/learning_feedback.py at 02ccffd produces blob a952af079aa8e6baf68b38f60a5d68248963d86e / sha256 1ed190e168041c74488086f3aa5f55711a2a140fc436e043b0c183f58db19b14 with values 3/46/0.0588, wogc 2, escalated 0, rc=0, errors: 0 - the canonical committed face, BYTE-EXACT. H1's predictive content is thereby confirmed at blob level against a recovered input: rows 42-51 ARE the face's input state (at its 51-row prefix position), not merely same-shaped rows. Reproduction = git archive 02ccffd | tar -x into a scratch dir, swap docs/exp-ledger.jsonl for the 51 rows, python3 -I tools/learning_feedback.py, git hash-object docs/scheduling-feedback.json (exact commands in R2-62-receipt.md).

(d) Option A package (ask: "package ready" - VERIFIED on file, with a now-measured applicability boundary): return-package/option-a-package/ holds OPTION-A-LANDING-COMMANDS.md (13611 B; gates G1-G6, commit message, rollback forms, honest boundaries) and scheduling-feedback.regenerated.json (939 B, md5 9701700e222d7292242c936f4530666f, git blob 06998c8 per its header). This session: the packaged face is byte-identical to the r26 produced face (cmp rc=0; md5 equal), i.e. to the deterministic recompute shared by B9/B10/B11 - the package's "four independent seats, one blob" line extends to a fourth and fifth face file. Boundary, measured: the package's gate G2 (input blob must be cf81fa36) HOLDS at every anchor through 64fbc1d (rev-parse this session) and FAILS at 02ccffd (input is babbfe2f); by the package's own text a G2 failure is a STOP with the expected landing blob re-derived at the new anchor, and path B (landing the packaged bytes) is admissible only when G1+G2 both hold - so path B is inadmissible at the tip, and an Option-A landing executed at 02ccffd would produce the NEW blob ba7d081c with values 5/53/0.0833 (13.3 sandbox measurement), not the packaged 06998c8 / 1/38/0.0244. The package has NOT been executed by anyone: the face blob at the tip is still a952af0.

(e) Case status: OPEN pending one desk ruling - unchanged (case v2 section 5 non-adjudication clause; this ledger still ranks nothing). What changed on the record is the option space, and this chapter records the measurement without adjudicating it: B2's discharge burden ("produce the missing input state and demonstrate 3/46") was measured impossible-on-record at recon time because the 51-row state existed on no ref; it now exists on-ref as rows 1-51 of babbfe2f, while the committed ledger is 60 rows, so the tool over the COMMITTED state still yields ba7d081c, not the canonical face. Which state is authoritative - the face's own 51-row input, the 60-row committed ledger, or some re-adjudicated form - is a desk question this chapter does not answer. Two further on-record notes, carried not adjudicated: the input-blob-sha-keyed sync guard remains unbuilt (package honest boundary 4), and 02ccffd is a real-world instance of the guard's own named acceptance fixture shape ("ledger appended without face rerun fires the guard", package section 5 last row) - 19 ledger rows landed in a commit that did not rerun the face.

### 13.8 Honesty notes (extension V)

1. This seat re-executed none of the six tools for any batch column. B11 readings are quoted from the r26 archive captures, r26-plan-run.log and R2-55-receipt.md; the cross-run claims rest on the cmp / rev-parse / cat-file / wc / merge-base / rev-list / git log / json.loads queries listed in 13.1-13.6, all run in this session. B1-B10 readings are carried over from sections 2, 9.2, 10.2, 11.2 and 12.2 without re-execution.
2. The two learning_feedback.py sandbox runs are the first tool execution by an extension seat of this ledger; trigger, scope and cleanup are disclosed at the section head and in 13.3/13.7. Scratch (rm -rf of the sandbox dir and the three ledger extracts) ran this session; nothing outside /tmp and the two ask-named files was written.
3. The row classification in 13.7(b) is a manual token classification (C2 method, proposal line 19); as evidence it is superseded by the sandbox runs, whose outputs (5/53 and 3/46) agree with it exactly.
4. The 13.3 sandbox rows are labeled as measurements, not samplings: no six-tool batch ran at 02ccffd, and the tip's b-gate/jargon/pin/engines readings were not taken by this seat.
5. The ask's numerals are recorded verbatim and resolved at the counting note; the table carries all eleven runs; nothing was dropped to fit a numeral.
6. R2-57/R2-58/R2-60 receipts and b1-recursion-final.md are context only (three-repo freshness seat; ai_flavor trend seats; archive supplement seat) - none is a six-tool reading batch, none enters the batch count, and none recorded the 13.7 ghost-row connection.
7. Non-ASCII material (zh text inside exp-ledger rows 52-60 and upstream commit subjects of the i18n wave) is referenced by row number / short sha only and not reproduced; this section is ASCII throughout (LC_ALL=C gate run after writing).
8. Zero network (NETRED honored); zero writes to any repo tree (all git invocations read-only at fixed SHAs with GIT_OPTIONAL_LOCKS=0; no checkout, no fetch, no proposal line appended by this seat); the only writes by this seat are this appended section and R2-62-receipt.md (plus the disclosed /tmp scratch, deleted).
