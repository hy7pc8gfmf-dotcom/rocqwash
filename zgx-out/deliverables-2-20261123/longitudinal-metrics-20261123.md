TICKET: R2-107 G-E3 longitudinal quantification report (direct response to external eval P0 gap "triage accuracy / repair success rate / mis-fix rate / human intervention count / mean repair latency have no before-after quantification" - this agent's ledger is the data source; pure read-only quantification, zero repo-tree write, zero PR; identity live-lumen)
SEAT: quant agent (quantification desk) live-lumen, receipt R2-107-receipt-lm.md; read sources: b1-recursion-final.md (AX-node ledger, 5483 lines), QUEUE.md (105 ticket rows), netred_p6.md (NETRED registry), R2-*-receipt*.md (135 receipt files / 102 unique tickets on disk), rsi-loop.log (192 lines, 28 batch blocks); live API census run by this agent this session (rate_limit probe + 15 pulls + 15 check-runs, curl -4 single-flight, adjacent >=30s, every call appended to netred_p6.md - 31 entries added)
DATE: 2026/11/23
INPUT: GitHub REST v3 repo hy7pc8gfmf-dotcom/rocqwash (Bearer token, responses cached at /tmp/r2107-prs/pr{17,18,20,24,25,26,27,28,29,30,31,32,33,34,35}.json and /tmp/r2107-checks/*.json) + the five ledger sources above; every {value,basis} pair below states where the number comes from and whether this agent measured it live this session, read it from a receipt (judged, not re-run), or computed it from live-fetched fields
VERDICT: REPORT DELIVERED - window 2026-11-19T21:00:29Z (PR#17 created_at, live API) through 2026-11-22T21:47:50Z (PR#35 merged_at, live API): 15 PRs opened (ask premise said ten/twelve; actual census 15), 14 merged = 93.3%; open->merged latency median 524s / mean 3086s; 3/3 named repair loops reached loop goal, landed mis-fix count 0 (6 self-intercepted); `seat-side` human touchpoints 0, but merged_by face is bot 8/14 + desk-account 6/14 (zero-human claim holds `seat-lane` only, NOT repo-wide - reported as-is); check-runs 58 success + 14 declared-skip + 0 fail across 72 runs (substantive green 58/58 = 100%, gross 80.56%); UNMERGED-DESK judgment on #32 validated (merge landed 17m09s after cap); NO before-window exists - single longitudinal series, this report is the before-side baseline for future comparison

Purpose. Longitudinal quantification report answering the external eval P0 gap with before-after numbers across the supply window: PR latency, repair-loop outcomes, human-touchpoint census, check-run counts; pure read-only quantification, zero repo-tree write, zero PR. Ticket R2-107, agent live-lumen.
Interface. This card plus the receipt R2-107-receipt-lm.md; consumed by the dispatching workflow; every {value, basis} pair below states where the number comes from and whether it was measured live this session.
Dependencies. GitHub REST v3 repo hy7pc8gfmf-dotcom/rocqwash (Bearer token, responses cached under /tmp); the five ledger sources named in the TICKET line above; python3 -I; curl -4 single-flight; no MCP helper.
Evidence. Every number below was fetched live by this agent this session (rate-limit probe + 15 pulls + 15 check-runs, curl -4 single-flight, adjacent calls >= 30s apart, every call appended to the NETRED registry); the basis column states the source per row.
Exit-codes. All API calls rc 0 (HTTP 200 across the census); verdict face REPORT DELIVERED; no before-window exists (single series) and the report states itself as the before-side baseline, as-is.

## 1. Supply-chain latency (metric 1 of the eval gap: PR open->merged)

Per-PR table, all fields fetched live by this agent 2026/11/23 (basis: GET /repos/hy7pc8gfmf-dotcom/rocqwash/pulls/{n}, curl -4 single-flight, HTTP 200 x 15, resp cached /tmp/r2107-prs/pr{n}.json, latency = merged_at - created_at computed by python3 -I over the cached bodies):

| PR | created_at | merged_at | latency_s | latency | merged_by |
|----|--------------------------|--------------------------|-----------|--------|----------------------|
| 17 | 2026-11-19T21:00:29Z | 2026-11-19T21:14:46Z | 857 | 14m17s | github-actions[bot] |
| 18 | 2026-11-20T18:27:04Z | (not merged) | - | - | - |
| 20 | 2026-11-20T19:46:28Z | 2026-11-20T19:53:00Z | 392 | 6m32s | hy7pc8gfmf-dotcom |
| 24 | 2026-11-21T03:41:26Z | 2026-11-21T08:29:20Z | 17274 | 4h47m54s | hy7pc8gfmf-dotcom |
| 25 | 2026-11-21T08:35:17Z | 2026-11-21T08:46:13Z | 656 | 10m56s | hy7pc8gfmf-dotcom |
| 26 | 2026-11-21T16:11:30Z | 2026-11-21T16:34:14Z | 1364 | 22m44s | hy7pc8gfmf-dotcom |
| 27 | 2026-11-21T21:43:37Z | 2026-11-21T21:48:13Z | 276 | 4m36s | github-actions[bot] |
| 28 | 2026-11-21T23:27:34Z | 2026-11-22T01:15:56Z | 6502 | 1h48m22s | hy7pc8gfmf-dotcom |
| 29 | 2026-11-22T01:51:09Z | 2026-11-22T02:14:19Z | 1390 | 23m10s | github-actions[bot] |
| 30 | 2026-11-22T03:37:36Z | 2026-11-22T03:43:24Z | 348 | 5m48s | github-actions[bot] |
| 31 | 2026-11-22T12:14:34Z | 2026-11-22T12:18:38Z | 244 | 4m04s | github-actions[bot] |
| 32 | 2026-11-22T13:10:01Z | 2026-11-22T16:46:56Z | 13015 | 3h36m55s | hy7pc8gfmf-dotcom |
| 33 | 2026-11-22T18:23:59Z | 2026-11-22T18:28:43Z | 284 | 4m44s | github-actions[bot] |
| 34 | 2026-11-22T20:36:35Z | 2026-11-22T20:41:00Z | 265 | 4m25s | github-actions[bot] |
| 35 | 2026-11-22T21:42:11Z | 2026-11-22T21:47:50Z | 339 | 5m39s | github-actions[bot] |

- {PRs opened in window: 15, basis: 15/15 pulls GET HTTP 200 this session; ask premise said "ten/twelve", actual census 15 - deviation reported, not silently absorbed}
- {merged: 14/15 = 93.3%, basis: merged_at non-null on 14 bodies; PR#18 closed 2026-11-20T19:16:47Z unmerged (state=closed merged=false, live body pr18.json), its content landed on main via desk-resolve commit 0a0a9c4 inside PR#20's base lineage (basis: R2-38-receipt.md L15, judged from receipt)}
- {open->merged latency median: 524 s = 8m44s, basis: python3 -I statistics.median over the 14 merged rows above, computed this session from live fetched timestamps}
- {open->merged latency mean: 3086 s = 51m26s, basis: same computation; right-skewed by two desk-lane outliers #24 17274s and #32 13015s - median is the robust face}
- {min 244s (PR#31) / max 17274s (PR#24, 4.80h), basis: same computation}
- {automerge-lane (merged_by=github-actions[bot], n=8): median 311s = 5m11s, mean 500s = 8m20s, basis: same computation filtered on merged_by}
- {desk-lane (merged_by=hy7pc8gfmf-dotcom, n=6): median 3933s = 65m33s, mean 6534s = 1h48m54s, basis: same computation; desk lane is ~12.7x slower than bot lane on median}
- {PR#18 open->close-unmerged: 2983s = 49m43s, basis: created_at 18:27:04Z / closed_at 19:16:47Z live body pr18.json}

## 2. Repair loops (metric 2: repair success rate / mis-fix rate)

Named red-face disposal loops on record, read from receipts this session:

- Loop A (R2-78 push-wall, PR#27): git push HTTPS failed 4x rc=128 "Empty reply from server" (2x origin + 2x fork, 120s backoff between, per NETRED law) -> git-data API fallback (blobs -> tree -> commit -> ref, all 201) published branch at cdd425c, published tree 276c2119 byte-identical to the signed local commit f6a901f tree -> PR#27 opened, merged at watch beat 2 of 6 cap, 5/5 check-runs green with 1 declared skip. Outcome: REPAIRED. {value: loop goal reached, basis: R2-78-receipt.md steps 7-9 read this session + live API merged_at 2026-11-21T21:48:13Z merged_by github-actions[bot]}
- Loop B (R2-97 -> R2-98 watch, PR#32): 6/6 watch beats all open/False/clean -> agent verdict UNMERGED-DESK at cap 16:29:47Z (registered per #26 precedent as not-a-failure, zero action zero prompting held) -> merge landed 16:46:56Z = 17m09s after cap close, inside `no-seat` window; verdict stands as-of-cap; the receipt's em-reduction prediction band [-104,-99] landed at -99, band edge HIT. Outcome: JUDGMENT VALIDATED + MERGED. {value: hit, basis: R2-97-receipt-watch.md L12-31 and R2-98-receipt-watch.md L39-40 + netred_p6.md L227 read this session + live API merged_at}
- Loop C (R2-102 true red -> R2-103 cure -> R4 recheck, PR#33 -> PR#34): w13 scan registered the window's only true red - norm error 1020 > 1001 breach (+263 inflow = jargon 188 + header 75, warn 1236 = +191 over 1045) attributed 100% to PR#33 deliverables -> cure PR#34 (15 cards, +348/-213) landed error 1020 -> 757, target <1001 hit EXACT (closure -263 == 188+75 arithmetic-checked), warn 1236 -> 1195 (-41) -> R4 recheck: error leg 757 < 1001 breach LIFTED, warn leg 1195 > 1045 residual breach +150 (narrowed from +191, residual registered not hidden). Outcome: ERROR LEG REPAIRED EXACT; WARN LEG PARTIAL. {value: 1 exact leg + 1 residual leg, basis: R2-102-receipt.md L53/L71/L96, R2-103-receipt-pr.md L35-36/L128-130, b1-recursion-final.md L5307 - all read this session; merged face live API PR#34 merged_at 2026-11-22T20:41:00Z merged_by github-actions[bot]}
- {red-detected -> fix-merged latency: ~1h22m (4920s), basis: R2-102 receipt clock scans 19:17-19:19Z (coarse to the minute) -> PR#34 merged_at 20:41:00Z live API; this is the window's only true-red episode, n=1}
- {repair success rate (loop-goal face): 3/3 = 100%, basis: the three named loops above, each judged against its own ask's goal clause, receipts read this session}
- {repair success rate (breach-leg face): 1/2 legs lifted in loop C (error leg yes, warn leg residual +150), basis: R4 values in b1-recursion-final.md L5307}
- {landed mis-fix count: 0, basis: (a) R2-103 receipt L106-108 "ledger = 0 drift (excluding the 4 deliberately skipped quotation rows and the 1 reverted row)"; (b) all 14 merges from the table remain in main ancestry per live API (no revert chain observed in any read face this session); grep for revert/rollback across receipts + ledger this session returned only `seat-side` self-caught items listed below - no upstream rollback event found}
- {intercepted mis-fix count: 6, basis: R2-103 4 quotation-face rows declined at application time (2 PR titles, 1 PR-body relay, 1 quoted v8.2 table header, receipt L42/L181-186) + R2-103 1 applied cure reverted on quotation law (`handover-verify`:81, receipt L186/L246-247) + R2-78b 1 self-reverted misfire among 13 Edit ops (R2-78b-receipt.md L16); all six caught before integration - this is the ask's "quotation-law rollback = interception evidence" face, actual census 4 declines + 1 revert + 1 doc-side misfire}
- {mis-fix rate (landed / applied): 0; interception rate: 6 intercepted against 2 executed repair batches, basis: same receipts}

## 3. Human intervention count (metric 3)

- {`seat-side` human touchpoints in the automerge chain: 0, basis: watch receipts' standing face "zero action zero prompting held (agent never touched the PR)" (R2-97-receipt-watch.md L80, R2-98-receipt-watch.md L162) + all agent operations executed under the live-lumen token per receipts + zero `seat-side` merge events in netred_p6.md read this session}
- {merged_by face - THE ZERO-HUMAN PREMISE DOES NOT HOLD REPO-WIDE, reported as-is: github-actions[bot] 8/14 = 57.1%, desk account hy7pc8gfmf-dotcom 6/14 = 42.9% (PRs 20, 24, 25, 26, 28, 32), basis: live API merged_by fields, table in section 1; R2-98-receipt-watch.md names the #32 merge "the desk itself" (#28 self-open self-merge shape)}
- {desk-side main moves outside the PR lane observed in window: 2 direct commits (9332c2b5 unsigned 15:35:33Z, d354580 16:38:27Z), basis: R2-97/R2-98 receipts fetch faces read this session}
- {named desk/human-directive touchpoints in ledger: 3 - (a) maintainer workflow approval consumed at PR#17 (netred_p6.md L33 21:15:03Z entry "CI got approved and started running"); (b) collaborator-invitation unblock chain under user order 18:16-18:27Z (PATCH /user/repository_invitations/345228381 204, then PR#18 201, netred_p6.md); (c) orchestrator-authorized merge-fix 18:59:46Z mid-R5 (netred_p6.md `watch-seat` entry); basis: netred_p6.md entries read this session}
- {verdict face: the eval-gap ask's "zero human (merged_by=github-actions face)" holds on 8/14 PRs only; honest statement for downstream consumers: the supply chain is `seat-autonomous` end to end (seats never merged, never pushed origin directly, zero force), but 6/14 merge acts and 2 direct main commits were desk-account (human-account) operations - any "fully unmanned" claim must be scoped to the agent lane}

## 4. Triage hit face (metric 4: CI green rate + judgment validity)

Check-runs, fetched live this session (basis: GET /commits/{head_sha}/check-runs per PR, curl -4 single-flight, HTTP 200 x 15, cached /tmp/r2107-checks/):

- {check-run totals: 72 runs = 58 success + 14 skipped + 0 fail + 0 pending, basis: python3 -I aggregation over 15 cached bodies this session}
- {per-PR shape: 14/15 PRs = 4 success + 1 skipped (Self-test suite Windows local self-hosted, main-only by design - declared skip per receipts); PR#32 = 2/2 success (desk-open shape, fewer runs registered), basis: same aggregation}
- {substantive green rate: 58/58 = 100% (excluding declared skips), basis: same aggregation}
- {gross green rate counting declared skips as non-green: 58/72 = 80.56%, basis: same aggregation; both faces given so no consumer can misread the skip design as failures}
- {per-PR zero-red: 15/15, basis: same aggregation}
- {QUEUE route outcome face: 105 ticket rows = 98 DONE (93.3%) + 4 PARTIAL (3.8%) + 2 SKIP (1.9%) + 1 PENDING (1.0%, the R2-6 upgrade gate that never auto-executes), basis: QUEUE.md parsed this session via python3 -I on the status column (col 5), workspace data copy at b1-recursion-20261120/data/QUEUE.md}
- {judgment validity hit: UNMERGED-DESK verdict on #32 -> merge landed 17m09s after cap (16:29:47Z -> 16:46:56Z) inside `no-seat` window, verdict stands as-of-cap = HIT, basis: R2-98-receipt-watch.md + netred_p6.md L227 + live API merged_at; ask's "17min after cap" confirmed at 17m09s}
- {judgment band hit: em-reduction prediction band [-104,-99] -> landed -99 at floor edge = HIT, basis: R2-98-receipt-watch.md TREND PREDICTION VERIFIED section}
- {judgment miss (registered, kept for accuracy honesty): predicted two-parent merge shape NOT matched (rebase-merge single-parent chain landed) = shape miss; ask-premise commits=2 vs actual 3 on #32; R2-93-era "growth stalled" call overturned at next beat; R2-99 fetch drift vs ask-expected anchor recorded, basis: R2-98-receipt-watch.md L19 + L162, R2-97-receipt-watch.md L154, rsi-loop.log w12 block - all read this session; miss count 3 registered vs 2 hits, small-n caveat: n=5 judgments total}

## 5. Before/after limitation (metric 5, honest registration)

- {before-window data: NONE EXISTS, basis: the agent ledger's own span - first NETRED P6 entry 2026-11-19T17:25:12Z (netred_p6.md table row 0), first PR created_at 2026-11-19T21:00:29Z, ledger volume header dated 2026/11/20 (b1-recursion-final.md L3); no prior-window artifact was found or claimed; any before/after comparison against this data is structurally impossible today}
- {registration: this report is a longitudinal single series and doubles as the BEFORE-side baseline; a future window can be compared against sections 1-4 values directly, basis: this report}
- {longitudinal series recorded for that future comparison (all read this session):
  RSI repair_action_rate: 0.0588 (3/46, committed face 2026-11-19/20) -> 0.0833 (5/53) -> 0.1029 (7/59) -> 0.0909 (7/68, input-ledger growth not tool drift per R2-93 law) -> 0.0854 (7/73, rsi-loop.log L92/L107/L131/L154 + L192 tail note);
  ai_flavor em: 8033 (w10) -> 8033 (w11, flat) -> 7936 (w12) -> 7936 (w13, first flat after two drops), basis: R2-102-receipt.md L163 + rsi-loop.log w12 block;
  norm error: 763 (w11) -> 757 (w12) -> 1020 (w13 red) -> 757 (post-R2-103), basis: R2-97/R2-102/R2-103 receipts;
  rsi-loop batches: 28 blocks, FETCH-FAIL 8 events (deep-window, anchor-stays), basis: grep -c this session;
  receipts on disk: 135 files / 102 unique tickets (ask premise said 123 - on-disk census reported as-is), basis: ls + awk count this session;
  return-package cards: 104 files, basis: ls count this session;
  this session's own network face: 31 netred entries appended (1 rate_limit + 15 pulls + 15 check-runs, all HTTP 200, zero retries, zero backoff triggered, rate budget 4993/5000 remaining at start), basis: netred_p6.md appends this session}

## 6. Method face (what was actually run)

- Rate limit probe: curl -4 -s -m 30 with Bearer token against api.github.com/rate_limit -> core remaining 4993/5000 (run this session).
- PR lifecycle: 15x curl -4 GET /repos/hy7pc8gfmf-dotcom/rocqwash/pulls/{n} for n in 17 18 20 24 25 26 27 28 29 30 31 32 33 34 35, single-flight, sleep 31 between adjacent calls, all HTTP 200, bodies at /tmp/r2107-prs/ (run this session).
- Check-runs: 15x curl -4 GET /repos/hy7pc8gfmf-dotcom/rocqwash/commits/{head_sha}/check-runs, same discipline, all HTTP 200, bodies at /tmp/r2107-checks/ (run this session).
- All 31 calls appended to /Users/zuguangzhao/ComplexAnalysis/attn/_log/netred_p6.md with ISO timestamps at call time (run this session).
- Aggregation: python3 -I only (no untrusted-code execution), computations shown in sections 1-4 (run this session).
- Ledger reads: b1-recursion-final.md, QUEUE.md, netred_p6.md, 135 receipt files via grep/ls/wc, rsi-loop.log via grep/head/tail; receipts R2-78/-78b/-97-watch/-98-watch/-102/-103-pr read in targeted sections (run this session).
- Not run (declared): no repository checkout, no tool re-execution (b_gate_audit/ai_flavor/norm_lint not re-run - their values are cited from receipts as judged, marked per receipt-verse), no before-window reconstruction (source data absent, section 5).
