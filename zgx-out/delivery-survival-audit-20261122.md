# Delivery Survival Audit at upstream d27af2d (PR#18 + PR#20 faces)

- Ticket: R2-52 (delivery survival audit seat, read-only) / execution receipt: R2-53
- Date: 2026-11-21
- Auditor: live-lumen (Mac seat, zsh), actor namespace zgx
- Repo: /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop
- Audited tip: **d27af2dee259d30cf560965089754607b337b545** (`git rev-parse HEAD` at audit time; commit message begins "i18n(unit-u19): corporate CLA re-laid ...")
- Method: pure git object reads only (`git rev-parse`, `git cat-file -e/-t/blob`, `git ls-tree`, `git diff-tree`, `git log`). Zero working-tree writes, zero checkout, zero network. NETRED single-flight: no network attempted, trivially compliant.
- Fail-loud policy: any vanished path would be listed verbatim in the census lines below and in Section 4's register. The register is EMPTY: no delivered item disappeared.

## 0. Anchor verification (all run live this audit)

| Anchor | Full sha | Verified by |
|---|---|---|
| HEAD / audited tip | d27af2dee259d30cf560965089754607b337b545 | `git rev-parse HEAD` -> d27af2dee259d30cf560965089754607b337b545 |
| PR#18 desk resolve | 0a0a9c43d4fc7aa11ba806d4ce2cc4da9375c955 | `git cat-file -t` -> commit; `git log --oneline -1` -> "chore(zgx-out): land PR#18 content via desk resolve ... zgx actor namespace (PR#18 resolve)" |
| PR#20 face | 8cfebb44be43eea72f1dd2751eafa04307f06141 | `git cat-file -t` -> commit; `git log --oneline -1` -> "chore(zgx-out): add planface batches 20261121 at anchors c48a548/8502146 with proposal ledger update" |
| PR#20 batch anchor 1 | c48a548a7bd2095bd081e6b6837266f5576dee8c | `git rev-parse c48a548` |
| PR#20 batch anchor 2 | 8502146d4acdcd5df102901cfeb46c75eafd8de1 | `git rev-parse 8502146` |

Ancestry (both deliveries inside the audited tip, run via `git merge-base --is-ancestor`):

- 0a0a9c43 IS ancestor of d27af2d.
- 8cfebb4 IS ancestor of d27af2d.
- First-parent order at d27af2d: ... 0a0a9c4 (PR#18 land) ... 8502146 -> a4d8d50 -> 8cfebb4 (PR#20 land) -> 8eff64e -> 63026ad -> bd511c4 -> a5c4a2a -> 2ed1c12 -> d27af2d. Five i18n commits sit between 8cfebb4 and the tip; none of them touched zgx-out (census below proves byte stability through the tip).

Parentage note (recorded verbatim, fail-loud honesty): the ask calls 8cfebb4 a "merge"; `git rev-list --parents -n 1 8cfebb4` returns exactly one parent (a4d8d50dec3ed3d1c812830c4330aed7969f1c9a). It is a single-parent landed face, not a two-parent merge by git parentage. The survival audit proceeds against the commit as landed; the parentage label difference does not affect any census below. (Same shape at 0a0a9c43: single parent a07403e3628804fceab4c213b87c28d5c0a87e48.)

## 1. PR#18 face (desk resolve 0a0a9c43, zgx-out + dual-stamp environment)

### 1.1 Census population (the 41 items)

Command: `git ls-tree -r --name-only 0a0a9c43 -- zgx-out/ | wc -l` -> **41**.

Reconciliation of the 41: `git diff-tree -r --name-status --no-renames 0a0a9c43` shows **38 additions (all status A)** under zgx-out/; **3 files pre-existed at the parent a07403e** (verified by `comm` of parent tree vs commit tree):

1. zgx-out/b-gate-audit.20261119T204525Z.json
2. zgx-out/environment.txt
3. zgx-out/scheduling-feedback.20261119T204525Z.json

38 added + 3 pre-existing = 41. The dual-stamp environment pair (204525Z + 232908Z, per the commit message "dual-stamp environment snapshots (204525Z + 232908Z both preserved)") is among the 38 additions: `zgx-out/environment.20261119T204525Z.txt` and `zgx-out/environment.20261119T232908Z.txt`.

### 1.2 Full census: per-item presence + blob-sha at d27af2d (41 items, not a sample)

Per item p: base blob via `git rev-parse 0a0a9c43:$p`; presence/type at tip via `git cat-file -t d27af2d:$p` and `git rev-parse d27af2d:$p`.

Result line (script output, verbatim):

```
PR18_CENSUS total=41 present=41 missing=0 same_sha=40 changed_sha=1
```

- **41/41 present at d27af2d. 0 missing / 0 GONE.**
- 40 of 41 byte-identical to the PR#18 land (same blob sha at both commits).
- The single changed item: `zgx-out/zgx-ledger-proposals.jsonl`, base blob e1390c7b4f4725e11b0f2e226bf293b67cb8f0de -> tip blob 1d91032432ed34371557afd06361636f755b5042. This change is the PR#20 ledger append (see 1.4): not a loss, an append.
- Cross-check of namespace totals: `git ls-tree -r --name-only d27af2d -- zgx-out/ | wc -l` -> **57** = 41 (PR#18 face, all still present) + 16 (PR#20 r20 batch, Section 2). `comm -13` of the two trees returns exactly the 16 r20 paths and nothing else; nothing from the 41 vanished.

### 1.3 Sample of 15 (explicit `git cat-file -e` + `-t` at d27af2d)

Command per item: `git cat-file -e d27af2d:<path>` (then `-t` and `rev-parse` for type/sha). All 15 chosen to span the face (both environment stamps, both b-gate stamps, all scheduling-feedback stamps, r12 evidence, r17 evidence, ledger). Output, verbatim (type=blob on every line):

```
SAMPLE18[1] PRESENT blob=5dfca54756b41ef54ceace86398c93033a259f0e zgx-out/environment.20261119T204525Z.txt
SAMPLE18[2] PRESENT blob=6251fa93cf6d1ca18f4410fb5868d5a8bba74f4b zgx-out/environment.20261119T232908Z.txt
SAMPLE18[3] PRESENT blob=6c8238804de36fa94d24f12131ca696f9404983d zgx-out/b-gate-audit.20261119T230026Z.json
SAMPLE18[4] PRESENT blob=6c8238804de36fa94d24f12131ca696f9404983d zgx-out/b-gate-audit.20261119T232908Z.json
SAMPLE18[5] PRESENT blob=06998c8fbbcf3d88087d370fc1556bcb3fce8b08 zgx-out/scheduling-feedback.20261119T230026Z.json
SAMPLE18[6] PRESENT blob=06998c8fbbcf3d88087d370fc1556bcb3fce8b08 zgx-out/scheduling-feedback.20261119T232908Z.json
SAMPLE18[7] PRESENT blob=06998c8fbbcf3d88087d370fc1556bcb3fce8b08 zgx-out/r4-anchor-3e18590-20261119T234622Z/scheduling-feedback.json
SAMPLE18[8] PRESENT blob=6c8238804de36fa94d24f12131ca696f9404983d zgx-out/r4-anchor-3e18590-20261119T234622Z/b-gate-audit.json
SAMPLE18[9] PRESENT blob=e3408ba9a47b7f3d8608d15c8a287281e3d5fe2a zgx-out/r12-anchor-3a56b85-20261120T141631Z/r12-divergence.diff
SAMPLE18[10] PRESENT blob=c656b0e22992ee0537e7dbdfc49aea8036f6e7ca zgx-out/r12-anchor-3a56b85-20261120T141631Z/r12-post-status.txt
SAMPLE18[11] PRESENT blob=617bf36bafa70845c2ce0282f562bc452970e659 zgx-out/r12-anchor-3a56b85-20261120T141631Z/out_pin_repair__plan.stdout
SAMPLE18[12] PRESENT blob=e3408ba9a47b7f3d8608d15c8a287281e3d5fe2a zgx-out/r17-anchor-c48a548-20261120T165150Z/r17-divergence.diff
SAMPLE18[13] PRESENT blob=8f6d579ff6bc5694205adf69091c00df5d1de755 zgx-out/r17-anchor-c48a548-20261120T165150Z/out_6-t_engines_body.stdout
SAMPLE18[14] PRESENT blob=c656b0e22992ee0537e7dbdfc49aea8036f6e7ca zgx-out/r17-anchor-c48a548-20261120T165150Z/r17-post-status.txt
SAMPLE18[15] PRESENT blob=1d91032432ed34371557afd06361636f755b5042 zgx-out/zgx-ledger-proposals.jsonl
sample18_size=15
```

Sample: **15/15 PRESENT**. Note the dual environment stamps survived with DISTINCT blobs (5dfca547 vs 6251fa93): both stamps preserved, neither collapsed onto the other. Same holds for the shared-evidence blobs (identical diff/post-status bytes reused across r12 and r17 by content addressing).

### 1.4 The one sha change is append-only (ledger)

- Bytes at PR#18 land: 28108 (20 JSONL lines); bytes at d27af2d: 31974 (21 lines).
- Prefix check: `head -c 28108 <d27 blob> | cmp - <PR#18 blob>` -> rc=0. The PR#18-era ledger bytes are a byte-exact prefix of the tip ledger; the +3866 bytes / +1 line is the single PR#20 entry (Section 2.3).
- `git log 0a0a9c43..d27af2d -- zgx-out/zgx-ledger-proposals.jsonl` -> exactly one commit: 8cfebb4. No other hand touched the ledger between the two deliveries, and none after.

### 1.5 PR#18 survival rate

**41/41 = 100%. Disappeared items: 0. Byte-level survival 40/41 identical + 1 append-only extension (no PR#18 bytes lost, proven by prefix cmp).**

## 2. PR#20 face (8cfebb4, batch at anchors c48a548/8502146)

### 2.1 Census population (17 paths)

`git diff-tree -r --name-status --no-renames 8cfebb4` -> **16 additions (A)** under `zgx-out/r20-20261120T191930Z/` + **1 modification (M)** of `zgx-out/zgx-ledger-proposals.jsonl` = **17 paths**.

The r20 batch dir (16 files): out_{1..6} stdout/stderr pairs (b_gate_audit, learning_feedback, jargon_map_sync, pin_repair, t_engines_seeds, t_engines_body), r20-divergence-stat.txt, r20-divergence.diff, r20-post-status.txt, r20-pre-status.txt.

Anchor linkage (ask: "c48a548/8502146 batch"): the 16 r20 files themselves do not name the anchors (grep -cE 'c48a548|8502146' over each of the 4 status/stat/diff files -> 0 lines). The linkage lives in the ledger batch entry appended by 8cfebb4: `{"actor": "zgx", "kind": "proposal", "target": "docs/scheduling-feedback.json", "ts": "2026-11-20T19:24:17Z", "anchor": "8502146", ...}` whose body cites "at reading anchor 8502146 (11 commits past the r17 anchor c48a548 (git rev-list --count c48a548..8502146 = 11))". Both anchor commits verified to exist (Section 0). The batch is therefore: the 16 r20 evidence files + the 1 ledger entry, taken at anchors c48a548/8502146.

### 2.2 Full census + sample of 15 at d27af2d

Full census (same per-item rev-parse/cat-file method as 1.2), script output verbatim:

```
PR20_CENSUS total=17 present=17 missing=0 same_sha=17 changed_sha=0
```

**17/17 present, 17/17 byte-identical to the 8cfebb4 land, 0 missing, 0 changed.**

Sample of 15 (explicit `git cat-file -e` + `-t` at d27af2d), output verbatim:

```
SAMPLE20[1] PRESENT blob=bf36e44be551040ad3f21f292914856ae567a5e9 zgx-out/r20-20261120T191930Z/out_1-b_gate_audit.stdout
SAMPLE20[2] PRESENT blob=5bea83b37473afe507c9897f4a42c06b303bdf0a zgx-out/r20-20261120T191930Z/out_2-learning_feedback.stdout
SAMPLE20[3] PRESENT blob=392c36e56205ae4ce431e0e048142262415f48a3 zgx-out/r20-20261120T191930Z/out_3-jargon_map_sync.stdout
SAMPLE20[4] PRESENT blob=9d98ce3923ca9f41098e9dc3c79929f08265677b zgx-out/r20-20261120T191930Z/out_4-pin_repair.stdout
SAMPLE20[5] PRESENT blob=1d1b7d6f511d16fb1ebef5fd01906ccfc6bec596 zgx-out/r20-20261120T191930Z/out_5-t_engines_seeds.stdout
SAMPLE20[6] PRESENT blob=8f6d579ff6bc5694205adf69091c00df5d1de755 zgx-out/r20-20261120T191930Z/out_6-t_engines_body.stdout
SAMPLE20[7] PRESENT blob=e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 zgx-out/r20-20261120T191930Z/out_1-b_gate_audit.stderr
SAMPLE20[8] PRESENT blob=e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 zgx-out/r20-20261120T191930Z/out_2-learning_feedback.stderr
SAMPLE20[9] PRESENT blob=77b604f83012cde9e07262ca149498828cb9b0cc zgx-out/r20-20261120T191930Z/out_4-pin_repair.stderr
SAMPLE20[10] PRESENT blob=3a6b9b94e81561a168a873148380481ee5fe81df zgx-out/r20-20261120T191930Z/out_5-t_engines_seeds.stderr
SAMPLE20[11] PRESENT blob=a07a1e807b704e55f58ba1df67593b3d7c8545e9 zgx-out/r20-20261120T191930Z/r20-divergence-stat.txt
SAMPLE20[12] PRESENT blob=e3408ba9a47b7f3d8608d15c8a287281e3d5fe2a zgx-out/r20-20261120T191930Z/r20-divergence.diff
SAMPLE20[13] PRESENT blob=573541ac9702dd3969c9bc859d2b91ec1f7e6e56 zgx-out/r20-20261120T191930Z/r20-post-status.txt
SAMPLE20[14] PRESENT blob=1a880c394848b961936b8867a1b719774744c444 zgx-out/r20-20261120T191930Z/r20-pre-status.txt
SAMPLE20[15] PRESENT blob=1d91032432ed34371557afd06361636f755b5042 zgx-out/zgx-ledger-proposals.jsonl
sample20_size=15
```

Sample: **15/15 PRESENT**. (The four empty-stderr blobs are git's canonical empty blob e69de29b, correct for clean tool runs.)

### 2.3 PR#20 survival rate

**17/17 = 100%. Disappeared items: 0. All 17 byte-identical at the tip (same_sha=17).**

## 3. scheduling-feedback canonical face at d27af2d (blob sha / a952af0 lineage)

- Canonical path: `docs/scheduling-feedback.json`.
- Blob at d27af2d: `git rev-parse d27af2d:docs/scheduling-feedback.json` -> **a952af079aa8e6baf68b38f60a5d68248963d86e**. Short form **a952af0 resolves as a blob** (`git cat-file -t a952af0` -> blob; full sha above).
- **Verdict: YES - the canonical face is still the a952af0 blob, exactly, at d27af2d.**
- Stability history: `git log --all --find-object a952af079aa8e6baf68b38f60a5d68248963d86e` -> single introducing commit fa879e4 ("feat(evolution): two closing tickets - (1) calibration ledger wired read-side into scheduling ..."). `--follow` on the path shows last touch fa879e4; no later commit moved it. Blob verified IDENTICAL at all six anchors run live this audit:

```
fa879e4  -> a952af079aa8e6baf68b38f60a5d68248963d86e
c48a548  -> a952af079aa8e6baf68b38f60a5d68248963d86e
8502146  -> a952af079aa8e6baf68b38f60a5d68248963d86e
0a0a9c43 -> a952af079aa8e6baf68b38f60a5d68248963d86e
8cfebb4  -> a952af079aa8e6baf68b38f60a5d68248963d86e
d27af2d  -> a952af079aa8e6baf68b38f60a5d68248963d86e
```

- Present at tip: `git cat-file -e d27af2d:docs/scheduling-feedback.json` -> rc=0, type blob.
- Divergence context (read from the zgx-out evidence, for the record): the four zgx-out stamp copies (r4-anchor + the 20261119T{204525,230026,232908}Z stamps) all carry blob 06998c8fbbcf3d88087d370fc1556bcb3fce8b08 - the face her reading runs regenerate from the committed inputs. The PR#20 ledger proposal (ts 2026-11-20T19:24:17Z, anchor 8502146) proposes regenerating the canonical face (committed a952af0 vs produced 06998c8f: repaired 3->1, unrecorded 46->38, repair_action_rate 0.0588->0.0244) and pairing it with a sync guard. That proposal is STILL UNAPPLIED at d27af2d: the committed canonical face remains a952af0. So: the canonical face is intact (still a952af0) and, per her standing proposal, still stale relative to deterministic regeneration - an open proposal, not a loss.
- Also recorded: the r20 batch pre-status captured a local uncommitted regeneration (`M docs/scheduling-feedback.json` in the working tree at batch time); the committed tree at every anchor through the tip still pins a952af0. Nothing committed ever replaced it.

## 4. Fail-loud register + verdict

Fail-loud register (disappeared/replaced/lost items across both faces): **EMPTY**.

| Face | Census | Present | Missing | Byte-identical | Survival | Disappeared |
|---|---|---|---|---|---|---|
| PR#18 (0a0a9c43, 41 zgx-out items incl. dual-stamp environment) | full 41 + sample 15 | 41 | 0 | 40 (+1 append-only ledger) | **100%** | 0 |
| PR#20 (8cfebb4, 16 r20 files + ledger entry) | full 17 + sample 15 | 17 | 0 | 17 | **100%** | 0 |
| scheduling-feedback canonical face | blob sha check at 6 anchors | present | - | a952af0 unchanged since fa879e4 | intact | 0 |

Verdict: **BOTH DELIVERIES FULLY ALIVE AT d27af2d.** Every item each delivery landed is present at the audited tip; the only byte delta anywhere in the two faces is the append-only ledger extension performed BY the second delivery itself (PR#18 prefix byte-exact under the PR#20 append, proven by cmp). The scheduling-feedback canonical face still carries blob a952af079aa8e6baf68b38f60a5d68248963d86e; her regeneration proposal remains open and unapplied.

Scope note (honest): this audit covers presence and byte-identity of the delivered objects at the tip, per the ask. It does not re-run the tools that produced the evidence, and it does not judge whether the canonical face SHOULD be regenerated (that is the standing zgx proposal's question).

All numbers in this card come from git commands executed live during this audit in /Users/zuguangzhao/ComplexAnalysis/rocqwash-loop; none are carried over from prior tickets without re-execution.
