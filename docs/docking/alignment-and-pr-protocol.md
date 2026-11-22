# Alignment and PR protocol

> Purpose.  The canonical alignment and PR protocol for construction work
>   streams on the receiver side: Gate A before PR assembly, Gate B when CI
>   goes green on your integration, the red discipline, and the known
>   structural gaps. Encoded from five live work stream executions per the
>   user orders of November 16–17, 2026. Quote; do not restate.
> Interface.  Markdown prose face for construction agents and reviewers;
>   read together with `recursive-evolution-paradigm.md` (the enforced laws)
>   and `../templates/pr-body-template.md` (the PR preamble).
> Dependencies.  `git` (fetch, re-base, cherry-pick, merge-base),
>   `certify/frozen8.py`, `tools/doc_lint.py`, `tools/axiom_guard.py`,
>   `ci.yml`. No execution surface of its own.
> Evidence.  Each gate step names its exact command form (fetch retry with
>   backoff, `git rev-list --reverse <base>..<tip>` verification, anchor
>   re-check); the structural-gap register carries its cure candidates.
> Exit-codes.  Not applicable (prose face); the tools it cites keep their
>   own 0/1/2/9 exit-code contracts.

## Gate A: before PR assembly

After your agents finish and before `git push`:

1. `git fetch origin main` (retry 4× with growing backoff; a connection reset is a
   transient window, not a verdict).
2. Re-base your branch onto the newest main. For construction branches cut before a
   squash integration of a sibling PR, rebuild the branch at `origin/main` and cherry-pick
   your own increment commits (verify `git rev-list --reverse <base>..<tip>` first);
   on conflict, restore the backup branch and escalate with the evidence.
3. Only then compose the PR payload; and write the fresh anchor into the PR body's
   baseline declaration.

Rationale: squash landings move main constantly (this repo's steward line lands in
minutes), and a stale head produces a noise PR that re-reviews already-landed content.

## Gate B: when CI goes green on your integration

When the CI on your PR head (or on main after a merge) goes green:

1. Align immediately (`fetch` + fast-forward; if your construction tree is occupied,
   fetch only and keep the tree).
2. Anchor-verify on the new anchor: re-run the light gates
   (`frozen8.py check --repo . --list certify/frozen8_manifest.json --tier2
   certify/frozen8_tier2.md5`; `doc_lint.py`; a fast `axiom_guard.py` pass) and judge
   the branch↔new-main relation (`git merge-base --is-ancestor`).
3. Squash-shape caveat: this repo lands via squash merges, so your branch tip is NOT an
   ancestor of main after any integration; judge by content relation, not sha ancestry, and
   re-base before a successor work stream so its PR carries only its own diff.

## Red discipline

- Red on main = do not rush. The self-heal workflow repairs mechanical reds; its own
  green is the "repair in progress" signal.
- Triage before acting: job-level and step-level logs first
  (`actions/runs/<id>/jobs`); a checkout-step failure on the self-hosted Windows lane is
  an infrastructure class (shallow-cache), not a content regression.
- If the red is the frozen8 git-anchor DRIFT line with all four reconciliation faces
  green: it is the squash×freeze-commit structural gap (below), cure = re-sign per SOP.

## Known structural gaps (registered · under ruling)

1. **Squash × freeze-commit**: every squash integration moves HEAD past `freeze_commit` and
   re-triggers the anchor check until a re-sign lands. Cure candidates: automerge-gate
   re-sign integration, or anchor-criterion upgrade (parent-chain break + content
   equivalence → downgrade registration; content drift still fails loud). Criterion
   upgrade touches a frozen checker; three-anchor ceremony and steward ruling required.
2. **No pull_request CI trigger**: `ci.yml` runs on main pushes only, so fork PRs have no
   pre-merge CI face. Cure candidates: add a `pull_request` trigger (additive), or give
   the automerge door a post-merge-only semantics (its revert arc already fits).
3. **Self-hosted shallow-cache checkout**: the cached workspace on the self-hosted
   Windows lane can false-flag or fail checkout after rapid successive landings
   (fetch-depth 0 fix landed; watch for recurrence on other cached lanes).
