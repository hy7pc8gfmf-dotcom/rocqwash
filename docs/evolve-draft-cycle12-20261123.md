# evolve-draft-cycle12-20261123.md — next-round task-brief draft produced by tools/evolve.py (human-review gate deliverable).

> **EvolveDraft**: the next-round task brief generated from harvested repository signals; candidates are proposals, the autonomous-execution gate stays with human review.
>
> Purpose.  Carry the evolution round's selected candidates to the reviewer as concrete task briefs: each carries a goal, an approach, an acceptance set and a mechanical grading; the constitution three-law preamble rides on every draft this engine emits.
>
> Interface.  Produced by `python3 tools/evolve.py --draft-out evolve-draft-cycle12-20261123.md` (with the harvested signal flags recorded below); consumed by the human reviewer, who turns accepted candidates into the next round's task assignments.
>
> Dependencies.  None to read this file; the engine that produced it runs on the Python 3 standard library and subprocesses the sibling engines only.
>
> Evidence.  Every candidate cites the harvested signal that derived it (the round inputs section below carries the full counts); the grading formula is impact x evidence / effort with evidence clamped to 10.
>
> Exit-codes.  Not applicable to a data face; the producing engine exits 0 on completion, 2 on usage error, 9 on missing or unreachable input.

## Preamble — constitution three laws (auto-carried)

1. Law one (annotation / normalization / English-ization): every newly
   written face is English-only, passes the normalization lint with zero
   error-level findings, and carries zero jargon residue against the mapping
   table (`docs/jargon-to-standard-mapping-v1.md`); translation replacement
   archives the replaced Chinese prose in a sibling `.zh.md` file.
2. Law two (contributor isolation): this round does not touch contrib-lane
   semantics; core-lane registry rows cross only through the intake pipeline
   (`docs/contrib-isolation-protocol-v1.0-20261113.md`); fetch before
   claiming, first canonical write wins, file-face layering holds.
3. Law three (autonomous evolution): this brief is produced by the evolution
   engine (`tools/evolve.py`); mutation = live-signal-derived candidates,
   selection = the suite/lint/gate checks, heredity = the frozen-ledger
   lineage.

Safety track: every candidate below is a proposal only. The
autonomous-execution gate stays with human review — the reviewer decides
which candidates become round tasks; nothing in this draft has been
executed, and the engine wrote nothing outside its explicit output paths.

## Round inputs (fitness account)

- Repository root: `/private/tmp/nfloop2`
- Draft width (--top): 5; candidates derived: 5; drafted: 5.
- Norm fitness: current error 750 / warn 1278 vs baseline 2267 / 1092; raw delta -1517 / +186; translatable delta -1515 / +161; reduction rate error 0.6692 warn -0.1703.
  - Frozen surfaces excluded from the translatable metric: `certify/freeze_manifest.py`, `names/mac_stmt_names.py`, `scan/mac_stmt_scan.py`, `seam/seam_probe.py`, `tools/cpu_guard.sh`, `verify/gate4_comment_guard.py`, `verify/verify_vo.py`, `wash/wash_engine.py`, `更新账.md`.
- Sentinel round: not harvested (no --watch-repo given).
- Suite state: not harvested (no --suite-ledger or --suite-now given).
- Registry audit: not harvested (no --registry-git given).
- Maintained UNRECOGNIZED events: not harvested (no --sentinel-events/--sentinel-state given).
- Gate health: doc_lint rc 1 (drift); recorded suite ledger unreadable (ledger directory missing: gate-ledgers); whitelist-variant norm errors 750 (whitelist `/private/tmp/nfloop2/docs/norm-lint-cjk-whitelist-20261113.txt`).

## Candidate 1 — gate-repair (rank 1, score 10.0000)

- **Goal** — Repair the adverse gate-health readings that gate the evolution loop: doc_lint drift (rc 1), recorded suite ledger unreadable (ledger directory missing: gate-ledgers), whitelist-variant norm error mass 750.
- **Approach** — Repair each adverse reading at its own face: doc_lint drift is repaired on the doc faces its report names (never by weakening the check), a recorded suite red is reproduced in isolation and fixed at the tool face the case attests (never weaken the case), and the whitelist-variant norm errors are carried per the mapping table with .zh.md archive siblings; an unreadable suite reading is repaired by recording a fresh ledger capture.
- **Acceptance** — doc_lint exits 0 (consistent); the latest recorded run ledger parses with 0 red; the whitelist-variant norm error count decreases against the starting account; no gate engine face was weakened.
- **Grading** — impact 2 x evidence 10 (raw 751, clamped to 10) / effort 2 = score 10.0000; recorded gate readings are evidence over the loop's own gates; live faces own the primary signals.
- **Evidence** — gate signal: doc_lint rc 1 (drift); suite ledger unreadable (ledger directory missing: gate-ledgers); whitelist-variant norm errors 750 (whitelist `/private/tmp/nfloop2/docs/norm-lint-cjk-whitelist-20261113.txt`).

## Candidate 2 — longtail-translation (rank 2, score 10.0000)

- **Goal** — Continue the law-one translation program on the prose long tail: reduce the remaining translatable error mass (193 error findings on non-frozen faces) by at least the next echelon (`seeds/jargon/_snapshots/annotation-whitepaper-v1.0-20260921.md` (107), `tools/vacgen.py` (13), `wrapper/verify_born.py` (12), `docs/ci-whitepaper-recursive-era-v1-20261116.md` (8)).
- **Approach** — Take the next echelon from the top error-carrying files in Evidence, translate each face per the mapping table with .zh.md archive siblings, keep code identifiers, CLI flags, schema field names and exit codes unchanged.
- **Acceptance** — The translatable error count strictly decreases against the starting account; every touched tool keeps --selftest rc=0; the full suite is green twice; zero jargon residue on the touched faces.
- **Grading** — impact 3 x evidence 10 (raw 193, clamped to 10) / effort 3 = score 10.0000; the fitness main signal, a broad long tail.
- **Evidence** — norm signal: translatable error mass 193; reduction rate error 0.6692 warn -0.1703 since baseline; top carriers: `seeds/jargon/_snapshots/annotation-whitepaper-v1.0-20260921.md` (107); `tools/vacgen.py` (13); `wrapper/verify_born.py` (12); `docs/ci-whitepaper-recursive-era-v1-20261116.md` (8); `docs/mcp.md` (7); `tools/mcp_server.py` (7); `README.md` (6); `seeds/jargon/_snapshots/terminology-general-project-20260921.md` (5).

## Candidate 3 — standing-candidate (rank 3, score 0.5000)

- **Goal** — Close the long-standing duplicate-block and anchor findings on the serviced books by running the audited prescription path.
- **Approach** — registry_audit --fix-plan for the prescription, then registry_fix dry run, then human review, then --apply (staged per-row md5 accounting with rollback); the books are regenerated on the current mainline per the isolation protocol, never hand-edited.
- **Acceptance** — A rerun audit shows zero duplicate residue on treated keys, no new anchor-text collisions, no orphan growth; the books are byte-identical outside the treated rows.
- **Grading** — impact 1 x evidence 1 (raw 1, clamped to 10) / effort 2 = score 0.5000; persisted memory with no live signal this round; baseline agenda weight.
- **Evidence** — heredity: ledger v54 entry, boundary list (re-statement); origin ledger v47 entry, roadmap section.

## Candidate 4 — standing-candidate (rank 4, score 0.5000)

- **Goal** — Execute the recorded final step of the multi-repo adaptation path (a real push against the protected main repository) once its recorded preconditions hold.
- **Approach** — Confirm the working-clone placement decision and the branch-protection posture recorded in the ledger, run the push planner in dry-run first, then the real push only after the human gate accepts the plan.
- **Acceptance** — The dry-run plan matches the recorded expectations; the real push (if approved) lands with its run evidence captured; no direct push to a protected branch.
- **Grading** — impact 1 x evidence 1 (raw 1, clamped to 10) / effort 2 = score 0.5000; persisted memory with no live signal this round; baseline agenda weight.
- **Evidence** — heredity: ledger v54 entry, boundary list; origin ledger v49 entry, boundary list.

## Candidate 5 — standing-candidate (rank 5, score 0.5000)

- **Goal** — Bring the single skipped suite case back into the running set once its missing input archive is restored.
- **Approach** — Restore the four-repo copy set the case reconciles (a desktop-archive decision recorded as pending), then run the case and confirm it joins the passing set.
- **Acceptance** — The suite runs with zero skips on a full local run; the case passes twice in a row.
- **Grading** — impact 1 x evidence 1 (raw 1, clamped to 10) / effort 2 = score 0.5000; persisted memory with no live signal this round; baseline agenda weight.
- **Evidence** — heredity: ledger v54 entry, boundary list; origin ledger v47 entry, boundary list.

## Boundary

This draft is a deliverable of the harvest→derive→draft pipeline only. The engine does not execute candidates, does not modify the repository, and does not touch the frozen surfaces; turning a candidate into a round task is the reviewer's decision.
