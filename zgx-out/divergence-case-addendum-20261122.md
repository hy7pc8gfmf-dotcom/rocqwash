# Divergence Case Addendum (2026-11-22) -- input-ledger growth, first b-gate divergence, persistence reasserted, desk-ruling implications

Ticket: R2-65 (case addendum casting seat, written; identity live-lumen, host Darwin arm64)
Date: 2026-11-22 (primary sources dated 2026-11-21)
Case state carried forward: OPEN; root cause H1 CONFIRMED HIGH (unchanged by this addendum). This file REGISTERS post-v2 movement in four chapters; it modifies nothing in the v2 case file; it adjudicates nothing.

Sources (seat-of-record attributions used throughout):
- [V2]  `return-package/divergence-case-scheduling-feedback-v2-20261121.md` -- case file v2 (R2-48): face-value table, root-cause verdict H1, desk options, closed-form assertion, residuals.
- [R60c] `../R2-60c-receipt.md` -- PR#24 final-state + current-tip reading seat, 9th sampling (anchor df9687e, run window 2026-11-21T07:32Z..07:38Z).
Grounding sources read this session beyond the ask's two named files (disclosed, cited only as recorded):
- [R55] `../R2-55-receipt.md` -- 8th sampling receipt (anchor 64fbc1d; ticket self-labeled R2-54b).
- [R62] `../R2-62-receipt.md` -- ledger extension seat V (eleven-run comparison + post-verdict case chapter; sandbox inverse test + option-A package applicability boundary).

Discipline: this seat ran zero git queries, zero network, zero repo-tree writes. Writes are exactly two files: this addendum and `../R2-65-receipt.md`. Zero proposal lines appended (case-file seats do not propose; [V2] section 9 note 6 posture carried). Fresh checks executed this session are listed in section 7; everything else is cited to its seat of record.

---

## 1. State in one paragraph

At v2 casting the case was: committed scheduling-feedback face a952af0 (3/46/0.0588 over an implicit 51-row input) vs deterministic recompute 06998c8 (1/38/0.0244 over the committed 41-row input cf81fa36), diverging in exactly three values at every sampled anchor; root cause H1 (the face was born stale at fa879e4 over 10 ghost input rows that had never landed anywhere); companion docs/b-gate-audit.json byte-identical at every sampled anchor. The 8th and 9th samplings plus the landing-verify work moved the case on four fronts, registered here as four chapters: (I) the committed input ledger itself grew 41 -> 60 rows at commit 02ccffd, and the landed rows include the ghost ten -- the birth input state is now recoverable on-ref; (II) docs/b-gate-audit.json diverged for the first time in the series (+28 lines, 4 new not-ready classes) at the 9th sampling, riding in with new desk-side b-gate-domain activity; (III) the canonical scheduling-feedback face has not moved -- divergence persists, now against a wider input basis; (IV) the recompute baseline has consequently moved: under Option A the face to land is the current-tip recompute (ba7d081, 5/53/0.0833 at df9687e), not the historical 06998c8, whose packaged bytes are gate-inadmissible at tip per the option-A package's own text.

## 2. Chapter I -- input-ledger growth: 41 -> 60 rows, the desk-side landing empirically proven

### 2.1 The landing event

- docs/exp-ledger.jsonl grew 41 -> 60 rows; blob cf81fa3602a53ae5dbe14367520176802d718f3d -> babbfe2f691436b2c67c7e59520dc41e95cd8b96; landed in commit 02ccffd51f360e0c9876afd71b6ed2d0830ac063 ("fix(R20): restore guard-pinned v55 snapshot line (row N1); triage v1.6 + whitepaper R20 section", adate 2026-11-21T10:17:51+08:00 per [R62]), the single commit in 64fbc1d..df9687e touching the three face files (git log count = 1 per [R60c] section 3.3). cf81fa36 verified byte-prefix of babbfe2f (cmp, [R62]).
- This is the first committed change of the sole repair input in the case's entire recorded history. [V2] F4 had pinned the input blob cf81fa36 unchanged since 95460fd (which predates the birth commit fa879e4); at the 8th sampling that pin still held ([R55] section 4: "cf81fa36..., 41 rows, unchanged since 95460fd; H1 input side intact"). The pin is now historical, not current: the desk-side (shore) ledger-landing path demonstrably appends rows to the committed input ledger, and did so mid-case, between the 8th and 9th samplings.
- Anchor placement: 64fbc1d..02ccffd = 6 commits (180e36d, 43fca6a, 69ff756, 19257b7, 02da21f, 02ccffd) and f1b6e27..02ccffd = 49, verified by [R62]; the 9th-sampling anchor df9687e is 13 commits past 64fbc1d per [R60c] section 3.1. No six-tool reading batch exists at 02ccffd itself ([R62]: its 02ccffd runs are labeled sandbox measurements, not a sampling); the first full sampling on the new input basis is the 9th at df9687e.

### 2.2 The landed rows include the ghost ten

- [R62] found and verified: rows 42-51 of the committed 60-row ledger are EXP-20261119-0001..0010, ts 2026-11-19T07:19:17Z..16:43:14Z -- every timestamp inside the R2-44 ghost window (2026-11-18T17:05:56Z, 2026-11-19T17:40:19Z] -- classifying under the tool's REPAIR_TOKENS first-match vocabulary as exactly +2 action=fix-content (rows 45, 49) + 8 token-less. That is precisely the v2 ghost signature (+2 fix-content / +8 no-token, [V2] section 4.5).
- The H1 inverse test, recorded NOT RUN (impossible) at recon time because the 51-row state was unmaterializable ([V2] section 4.3), has now been RUN ([R62], /tmp sandbox, R2-44 precedent): ghost-state ledger = cf81fa36 prefix + rows 42-51 (51 rows) -> tools/learning_feedback.py gives repaired=3 escalated=0 wogc=2 unrecorded=46 rate=0.0588, rc=0, errors 0; git hash-object = a952af079aa8e6baf68b38f60a5d68248963d86e; shasum = 1ed190e168041c74488086f3aa5f55711a2a140fc436e043b0c183f58db19b14 -- the canonical committed face, BYTE-EXACT. [R62]'s words: "The landed rows ARE the face's input state."
- Consequences carried by this fact (registered, not adjudicated):
  1. The ghost ten are ghosts no longer: their exact content is now on-ref and recovered, resolving [V2] residual unknown 1 (which had recorded the content as unrecoverable on this host). [R62] scopes the old statement honestly: "unrecoverable on this host / never landed at recon time" -- the landing has since happened.
  2. H5's "late landing REFUTED HIGH" ([V2] section 4.4) was a measurement at recon time; the late landing has now occurred, at 02ccffd, two days after the birth commit. H1 itself is untouched: the face WAS stale on arrival (birth over a state not yet committed); the input caught up afterwards.
  3. The canonical face a952af0 is now reproducible from committed inputs -- as the 51-row prefix state (rows 1-51 of the 60-row ledger). This bears directly on Option B2; see section 5.3.

### 2.3 Derived arithmetic (this seat, from recorded run values only)

From [V2] section 1 (1/38 over 41), [R62] RUN B (3/46 over 51), [R60c] section 3.4 / [R62] RUN A (5/53 over 60):

| slice | rows | repaired | unrecorded |
|---|---|---|---|
| base committed input (cf81fa36) | 41 | 1 | 38 |
| ghost ten (rows 42-51, landed at 02ccffd) | +10 | +2 | +8 |
| genuinely new rows (rows 52-60) | +9 | +2 | +7 |
| total (babbfe2f, 60 rows) | 60 | 5 | 53 |

Rates: 3/51 = 0.0588, 1/41 = 0.0244, 5/60 = 0.0833; watch-only guard-correct 2 and escalated 0 unchanged on every recorded run. Cross-check executed this session (section 7, check 5): +2+2 = +4 repaired, +8+7 = +15 unrecorded, 10+9 = 19 rows -- all consistent with the recorded faces. The rows 52-60 slice (+2/+7 over 9 rows) is this seat's derived arithmetic, not a seat-run classification; [R62] honesty note 5 records that rows 52-60 carry non-ASCII text and this seat has not read their content.

### 2.4 Context around the landing window (as recorded by others)

[R60c] section 2.2 records unlogged-actor reflog forward moves in the loop clone 05:11-05:25Z (checkouts 8aa2af8, 18bc0f4, ff-merge to 311d32d) -- same unlogged-event class as the R2-47 21:07:49Z correction, recorded as-found, not performed by that seat. [R60c] section 1 records the two tip-adjacent upstream commits observed in its fetch window (ac74f19 "feat(mcp): tree_audit face + net_probe unverifiable semantics", df9687e "feat(audit): lean_axiom_sweep per-theorem axiom-closure classifier"). Both are other actors' work, cited here only to place the landing window; no causal claim is made by this seat.

## 3. Chapter II -- first b-gate-audit divergence (+28 lines, 4 new classes), entering with new desk-side b-gate-domain activity

### 3.1 The observation ([R60c] section 3.5, live that session)

At anchor df9687e the recomputed docs/b-gate-audit.json diverged from the committed face for the FIRST time in the series: git diff numstat +28/-0 confined to the classes array; four new not-ready class rows -- concl.ne.applied-nonzero, concl.nezero.predicate, concl.quantified.existential, concl.quantified.universal -- classes 3 -> 7; verdict fields identical on both sides (not-ready; ready classes empty; remaining_to_b=3; errors 0); blob pair 6c82388..5327b2996596a5c4389d5e7a872ef667075aef7a; cmp committed-vs-produced first difference char 46 line 4. The committed b-gate face (blob 6c8238804de36fa94d24f12131ca696f9404983d, sha256 3c70b52868b5c4dbf3cb5ae8adf0f26182890d8b3e5d405a3d8b66bc98d63e30, last touch 02ccffd) is unchanged -- the divergence is produced-side only, as with the scheduling-feedback case.

### 3.2 The eight consistent samplings before it

Through the 8th sampling the companion face had recomputed byte-identical at every sampled anchor: anchors f1b6e27 (x3), 3e18590, 3a56b85, c48a548, 8502146 and the post-verdict d27af2d recheck per [V2] sections 1-2 ("companion docs/b-gate-audit.json recomputes byte-identical everywhere"; the family precedent Option A leaned on), and the 8th sampling at 64fbc1d per [R55] section 4 ("produced cmp vs committed rc=0 IDENTICAL... family precedent intact: divergence class remains specific to scheduling-feedback.json"). First divergence: 9th sampling, df9687e, [R60c]. This matches the ask's framing: after eight consistent samplings, the first divergence appears.

### 3.3 Why now: frozen-current, then domain drift ([R60c]'s proof, not speculation)

[R60c] section 3.5 proves the committed b-gate face was CURRENT when frozen: committed face at df9687e cmp vs the r26-era produced face (r26-20261120T224020Z/produced-b-gate-audit.json) rc=0 byte-identical -- i.e. it matched a real tool output of its era -- and it went stale only through commits after 02ccffd. The four new classes therefore ride in with new desk-side b-gate-domain activity (the post-02ccffd commits; the tip-adjacent named commits are the two in section 2.4). [R60c] does not map individual classes to individual commits, and neither does this seat.
Fail-loud registration: [R60c] section 3.5 says "the 11 post-02ccffd commits", but the two receipts' own chain numbers derive 7 (64fbc1d..df9687e = 13 per [R60c] section 3.1; 64fbc1d..02ccffd = 6 including 02ccffd per [R62] section "Ask item 1"; 13 - 6 = 7). This seat ran no git and cannot resolve 11-vs-7; the staleness mechanism (byte-current at the 02ccffd freeze, divergent at df9687e) is unaffected by which count is right. Recorded as an unresolved discrepancy between receipts, not papered over.

### 3.4 What class of staleness this is

The b-gate divergence is a DIFFERENT staleness class from the scheduling-feedback case, and the contrast is now empirical, not hypothetical:
- scheduling-feedback: born stale (H1) -- the face was written from an input state that did not exist on any ref at commit time; committed side frozen since fa879e4 across every sampling.
- b-gate-audit: correct at freeze, stale by domain drift afterwards -- the ordinary "inputs moved, face not re-run" shape, instantiated by 02ccffd's ledger-appends-without-face-rerun for the scheduling-feedback input ([R62]: "02ccffd instantiates the sync guard's own acceptance fixture shape") and by the post-02ccffd b-gate-domain commits for this face.
The verdict fields being identical both sides, the b-gate divergence does not alter the b-gate verdict (still not-ready) and does not disturb the scheduling-feedback evidence; the two divergences now coexist in one reading batch ([R60c] section 3.5: git status after tool runs showed exactly two modified faces).

### 3.5 Superseded framings registered (v2 text stands for its own anchors)

1. [V2] section 1 (preserved from v1): "the divergence class is specific to scheduling-feedback.json" -- true of every anchor sampled through d27af2d and restated at the 8th ([R55]); no longer true of the current state as of the 9th sampling.
2. [V2] section 3 (family precedent for Option A: "docs/b-gate-audit.json recomputes byte-identical at every anchor") -- held through the 8th sampling; broken at the 9th.
3. Proposal line 24 ([R60c] section 4, verified on disk this session, section 7 check 4) already extends the input-blob-keyed sync guard to b-gate-audit.json and records that the staleness class is not scheduling-feedback-specific -- the proposal side had registered the new class before this addendum was cast.

## 4. Chapter III -- persistence reasserted: the canonical face has not moved

### 4.1 Persistence facts

At the 9th sampling the committed docs/scheduling-feedback.json is still blob a952af079aa8e6baf68b38f60a5d68248963d86e, sha256 1ed190e168041c74488086f3aa5f55711a2a140fc436e043b0c183f58db19b14, last touch fa879e4 (the birth commit) -- re-verified live by [R60c] section 3.2; [R62] independently records face blob still a952af0 and last touch still fa879e412b0312fcc7deaa3e47d8229e6c6b1ba0 at the 02ccffd-era tip. The divergence has now been re-observed at every sampling on record: samplings 1-7 (f1b6e27 x3, 3e18590, 3a56b85, c48a548, 8502146) and the post-verdict d27af2d recheck per [V2] section 2, the 8th at 64fbc1d per [R55] (471-byte diff, index a952af0..06998c8, cmp first difference char 400 line 17, diff byte-identical to the archived r12/r17/r20 captures), and the 9th at df9687e per [R60c]. (The receipts also carry a parallel batch/run count -- [R55] fail-loud 4 and [R62] record that the "8th sampling" ticket label and the ledger chapter chain's "ninth distinct confirming anchor / eleventh run" both appear on file; this addendum uses the sampling-ordinal series both receipts carry, and registers the duality once here.)

### 4.2 Closed-form assertion: updated form (supersedes the v2 wording for anchors at or after 02ccffd)

[V2] section 2's closed-form assertion ("every sampling slot's diff index names the same blob pair a952af0..06998c8") now holds on its committed half only. The 9th sampling's index is a952af0..ba7d081: the committed side is unchanged (a952af0 at every anchor on record, still true), and the produced side moved 06998c8 -> ba7d081 because the input basis moved. The deeper invariants all still hold, on the 9th sampling's own evidence: diff confined to exactly the three repair_outcomes lines (repair_action_rate 0.0588->0.0833, repaired 3->5, unrecorded 46->53); 471 bytes, the same hunk size as every prior chapter; cmp committed-vs-produced first difference at char 400 line 17, the same position as every prior chapter; produced face deterministic per input (t2 determinism rerun cmp rc=0, [R60c] section 3.4). Updated closed form: at any anchor whose input blob is cf81fa36 (through 64fbc1d) the pair is a952af0..06998c8; at any anchor at or after 02ccffd (input babbfe2f) the pair is a952af0..ba7d081 -- the committed half constant, the produced half a deterministic function of the input blob.

### 4.3 The gap is not closing

[R60c] section 3.5 answers the ask's sampling question directly: still divergent, and both sides did not converge -- the committed side is unchanged, the recomputed side moved further from it in value space (3 vs 5 repaired, 46 vs 53 unrecorded, 0.0588 vs 0.0833), on a 60-row committed input against a face whose frozen arithmetic asserts a 51-row generation-time input. [R60c]'s characterization on file: "The divergence is now WIDER than at the 8th sampling, not narrower."

## 5. Chapter IV -- implications for the desk ruling: the recompute baseline has moved

### 5.1 The baseline movement

The recompute row of [V2] section 1's face-value table (06998c8 / 1/38/0.0244 / 41 rows) is now a HISTORICAL baseline, valid only for anchors whose input blob is cf81fa36 (all samplings through the 8th). At any anchor at or after 02ccffd the deterministic recompute runs over the 60-row committed input and yields ba7d081cf2ff79ba7b1acf72999ca1f1ecc4f3c5 (sha256 572061ef7ba4ebbb0d75a0c1700102cf9ed0667c3c0c8713157abf99045478d1; 5/53/0.0833, rc=0, errors 0) -- measured twice independently: the 9th-sampling six-tool batch at df9687e ([R60c] sections 3.4-3.5) and the /tmp sandbox at 02ccffd ([R62] RUN A). No future default-path recompute at a current-basis tip will reproduce 06998c8; the 06998c8 baseline remains reproducible only against an input of cf81fa36.

### 5.2 Option A: the face to land is the current-tip recompute, not 06998c8

[V2] section 5 (Option A) itself wrote the gate that has now fired: "the landing blob should be 06998c8 or a descendant -- if it is not, the landing anchor's inputs have changed and the case must be re-adjudicated per the new inputs, not the old values copied." The antecedent has occurred: the inputs changed at 02ccffd, and the landing-anchor recompute is ba7d081, a different blob. The consequence, mechanical not preferential: under Option A the face to land is the recompute at the landing-time tip -- currently ba7d081 (5/53/0.0833 over 60 rows) at the latest full reading on record (df9687e) -- and the desk should expect Option A's landing to write DIFFERENT numbers than the v2 table showed (5/53/0.0833 replacing the 1/38/0.0244 that all v2-era discussion used). Landing the packaged 06998c8 bytes today would re-create the case's own defect class -- a face over an input state other than the committed one, the exact shape H1 diagnosed.
This is not merely this seat's inference; it is measured and on file: the option-A package (return-package/option-a-package/: OPTION-A-LANDING-COMMANDS.md 13611 B, scheduling-feedback.regenerated.json 939 B, verified present on disk this session, section 7 check 2) carries gate G2 (input = cf81fa36), which holds through 64fbc1d and FAILS at 02ccffd (babbfe2f); per the package's own text the prescribed action at tip is STOP + re-derive, and path B (landing the packaged bytes) is inadmissible at tip ([R62]). [R62] also records the package has NOT been executed by anyone: tip face blob still a952af0.
The remaining v2 Option A acceptance gates carry over unchanged, measured against the current committed face: rerun rc=0 errors=0 at the landing anchor (satisfied at df9687e, [R60c] section 3.4); diff limited to the three repair_outcomes fields against the committed face -- still exactly true at the 9th sampling (471 B, three lines, section 4.2); rerun determinism cmp rc=0 (satisfied, t2b); landing commit touches docs/ and carries the divergence-evidence references; the guard fires on the append-without-rerun fixture -- for which 02ccffd is now a real, on-ref instance ([R62]).

### 5.3 Option B column after the landing

- B1 (tool-rule defect) remains counter-evidenced and is untouched by the new facts: the tool behaved deterministically at the new input ([R60c] t2/t2b cmp rc=0), its counting is internally consistent across all three recorded input states (arithmetic in section 2.3), and H2's REFUTED disposition ([V2] section 4.4) needs no revision.
- B2 (keep the canonical face by supplying its input state) has had its discharge burden transformed: [V2] section 5 measured it impossible-on-record because the 51-row state existed nowhere; the state is now on-ref-constructible (cf81fa36 prefix + committed rows 42-51) and the tool over it yields the canonical face byte-exact ([R62] RUN B) -- the discharge demonstration B2 required has been performed in sandbox. Two measured facts bound what B2 would now mean, recorded here without adjudication: the discharge state is a 51-row PREFIX of the committed ledger, while the tool's default input path reads the full committed 60-row ledger (hence ba7d081 on the default path); and the committed face's values (3/46/0.0588) describe rows 1-51, not the committed 60-row state (5/53/0.0833). Which face is authoritative under a 60-row committed input is precisely the desk ruling this case awaits; [R62] records the same facts as "recorded, not adjudicated" and this addendum takes the same posture.

### 5.4 The guard case strengthens (measured, not ranked)

One reading batch now contains two live staleness instances of two different classes: scheduling-feedback (born stale since fa879e4, committed side frozen across nine sampling ordinals) and b-gate-audit (drift-stale since the post-02ccffd domain commits, committed side byte-current at its 02ccffd freeze). The standing proposal -- regenerate-and-land + input-blob-keyed sync guard, carried unchanged through proposal lines 15/19/20/21/22/23/25 per the receipts -- now has line 24 extending the guard to b-gate-audit.json (verified on disk this session), and 02ccffd itself instantiates the guard's acceptance-fixture shape on the real timeline ([R62]). The guard targets not only the historical birth defect but the operating hazard that produced the second instance. Registration only; selection between options remains the desk's ([V2] section 5 non-adjudication clause, carried verbatim in force).

### 5.5 Decision-surface posture

PR#24 (shore planface delivery; head bd5e10530f28606d6756f54df35f7bfee5586c94, base 02ccffd51f360e0c9876afd71b6ed2d0830ac063, branch zgx/planface-20261122) was OPEN and UNMERGED at the latest poll on record to this seat's sources (2026-11-21T07:32:08Z, ~3.6h after creation; no landing claimed; [R60c] section 1). The case remains OPEN pending one desk ruling. Note for the ruling's frame: the input growth of Chapter I and the b-gate drift of Chapter II both happened while the decision surface sat open -- the cost of waiting that [V2] section 3 anticipated ("every future read seat will re-discover the divergence") has continued to accrue, now on two faces.

## 6. What this addendum does NOT claim

1. No causal mapping from individual post-02ccffd commits to the four new b-gate classes ([R60c] provides none; this seat ran no git).
2. No resolution of the 11-vs-7 post-02ccffd commit-count discrepancy between receipts (section 3.3) -- registered, unresolved.
3. No classification of ledger rows 52-60 by this seat (their +2/+7 contribution is derived arithmetic from recorded run values, section 2.3; [R62] records they carry non-ASCII text; this seat has not read their content).
4. No claim about anchors beyond the record available to this seat's sources: the latest full sampling on record is df9687e (9th); the latest PR-state poll on record is 2026-11-21T07:32:08Z. If newer anchors exist, the same closed-form discipline applies (section 4.2): recompute at the actual landing-time tip.
5. No adjudication: nothing here ranks Option A vs B2 vs C, declares which face is authoritative, or closes the case.
6. v2's file is untouched; where this addendum supersedes a v2 framing for anchors at or after 02ccffd (exclusivity one-liner, closed-form blob pair, recompute table row), v2's text stands as written for its own anchors and the supersession is registered here, not edited into v2.

## 7. Fresh checks executed this session (this seat, R2-65)

1. Read in full: [V2] and [R60c] (the ask's two named sources). Read for grounding (disclosed): [R55] (header + sections 3-5 + fail-loud), [R62] (full).
2. Directory census (ls): return-package/option-a-package/ present with OPTION-A-LANDING-COMMANDS.md (13611 B) and scheduling-feedback.regenerated.json (939 B) -- matching [R62]'s cited sizes; no pre-existing divergence-case-addendum file; R2-61/61c/62/62c/63 receipts present (newer tickets exist in the directory; scanned for anchors/divergence mentions, none records a six-tool sampling newer than df9687e -- basis for section 6 item 4).
3. Shore proposal ledger (read-only): `wc -l /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl` -> 24; `sed -n '23p'` piped to `python3 -I` json.loads -> actor=zgx, anchor=df9687e, schema=zgx-proposal/1, target=docs/scheduling-feedback.json, ts=2026-11-21T07:37:00Z; `sed -n '24p'` -> actor=zgx, anchor=df9687e, schema=zgx-proposal/1, target=docs/b-gate-audit.json, ts=2026-11-21T07:37:00Z, ascii_only=True -- matching [R60c] section 4 field-for-field. ([R60c]'s fail-loud ledger-lineage disclosure -- physical lines vs sampling ordinals, parked rows in stash -- is quoted, not re-verified here; this seat appended nothing.)
4. Derived-arithmetic cross-check (`python3 -I`, this seat): ghost slice +2/+8 over 10 rows matches the v2 section 4.5 signature; rows 52-60 slice +2/+7 over 9; totals +4/+15/+19; rates 3/51=0.0588, 1/41=0.0244, 5/60=0.0833 -- all consistent with the recorded faces (output retained in the session transcript; summary in section 2.3).
5. Post-write: both written files (this addendum, ../R2-65-receipt.md) asserted all-ASCII via `python3 -I` byte decode; `ls -l` both.

## 8. Provenance summary

Chapters I-IV draw on: [V2] (face-value table, H1 verdict, option gates, closed-form assertion, residuals); [R60c] (9th sampling: input growth, both faces' blobs/sha256s, 471-byte three-line diff, first b-gate divergence + its frozen-current proof, PR#24 posture, proposal lines 23/24); [R55] (8th sampling: divergence byte-identical, b-gate still identical, input still cf81fa36, numbering duality); [R62] (02ccffd landing details, ghost-row identification + classification, sandbox RUN A/RUN B, option-A package G2 boundary, B2 discharge state, guard fixture shape). This seat's own new work: the section 2.3 derived arithmetic, the section 4.2 updated closed-form statement, the section 3.3 discrepancy registration, and the section 7 checks. Zero git, zero network, zero repo-tree writes.
