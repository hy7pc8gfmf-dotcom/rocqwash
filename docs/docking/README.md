# Contributor docking kit · recursive-evolution workflow stack

> Purpose.  Everything an external contributor side needs to dock with this
>   repository's recursive-evolution loop and run the same construction work
>   streams this repo runs on itself; workflow templates, the paradigm, the
>   component map, the verification gates, and the PR protocol; as
>   repo-canonical assets. This kit is the in-repository canonical face of
>   the recursive-evolution workflow stack.
> Interface.  Markdown prose face for contributors; graded by
>   `tools/norm_lint.py` under `docs/annotation-standard-v1.0-20261113.md`.
>   Revision flow: edit only this directory → note it in
>   `docs/CAPABILITY-INDEX.md` → register it in the execution record
>   (single-source discipline, same as `docs/license-protocol-v1.0-20261114.md`
>   §7).
> Dependencies.  The faces it cites: `recursive-evolution-paradigm.md`,
>   `component-map.md`, `alignment-and-pr-protocol.md`,
>   `templates/wf-recursion-wave-template.dwf.ts`, `templates/ci-green-watch.sh`,
>   `templates/pr-body-template.md`, `docs/license-protocol-v1.0-20261114.md`,
>   `CONTRIBUTING.md`. No execution surface of its own.
> Evidence.  The five-step protocol and the file table cite each gate, path,
>   and command verbatim from the in-repo faces named there;
>   `component-map.md` in this directory cross-checks every tool citation.
> Exit-codes.  Not applicable (prose face); the tools it cites keep their
>   own 0/1/2/9 exit-code contracts.

## The loop in one paragraph

Φ = cluster gaps (`tools/gap_cluster.py`) → render candidate rows (`tools/row_render.py`) →
**human point-order** (data-layer classes need one human first-admission; code-layer always
waits for approval) → admit (`tools/auto_round.py approve`) → verify (fitness gate:
`tools/axiom_guard.py` compile leg + `tools/norm_lint.py`) → land as a ledgered round
(`docs/round-ledger.jsonl` + `refs/rocqwash/rounds/<n>`). Φ\* = the loop re-enters itself:
a trigger (`tools/scheduler_lite.py`) opens a round when measured gaps accumulate, the bus
feeder (`tools/bus_feeder.py`) drips external experience in, the calibration→render feedback
edge makes each round smarter, and `tools/evolution_dashboard.py` watches the whole thing.
Self-heal (`tools/cw_sentinel.py` + the watch workflows) repairs reds; the automerge door
(`tools/auto_merge.py`) merges whitelisted green PRs under a daily budget with a revert arc.

## Five-step docking protocol

1. **Clone and align**: `git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash`
   then keep local aligned with origin/main before every construction session
   (`git fetch origin main && git merge --ff-only origin/main`). Alignment is a law, not a
   courtesy: build on a stale tree and every later gate judges the wrong world.
2. **Pick your work stream template**: copy `templates/wf-recursion-wave-template.dwf.ts`,
   fill the parameter block (REPO tree, OUT dir, BRANCH name, the agent specs for your work stream),
   and run it through your workflow host. The template encodes this repo's proven work stream shape:
   P0 cloud alignment → parallel construction agents → mechanical verification gates →
   branch → fork push → PR → CI judge. See the `<<FILL>>` parameter block in
   `templates/wf-recursion-wave-template.dwf.ts` for the parameter table.
3. **Build inside the scope guards**: the frozen set (`certify/frozen8.py`
   LEDGER8, eight files), the append-only ledger (`更新账.md`), and the legal/data faces
   (`CLA/`, `seeds/`, `docs/zh`) are permanently out of scope for mechanical repair waves;
   `tools/repair_scope.py` is the single shared exclusion source. Certification faces
   (certify/scan/verify/wrapper/names/seam) need the three-anchor ceremony and a human desk
   order. Everything you write goes into `tests/test_destructive_matrix.py` (whoever writes,
   enters the matrix).
4. **Pass the real gates**: `python -B tools/axiom_guard.py --repo <tree>
   --rocq <rocq> --coqchk <coqchk>` (every theorem Closed, zero axioms, no `Admitted`/`Axiom`/
   `Hypothesis`, no Prop leakage), `python -B tools/norm_lint.py` + `tools/doc_lint.py`
   (zero new findings), `bash tests/run_tests.sh` (reds ⊆ the anchor red roster, zero new).
   Note for your machine: bare `python`/`python3` may be a store stub on Windows; use the
   real launcher (`py`) or set `ROCWASH_PY` (the suite's escape hatch).
5. **Land via PR with the canonical preamble**: branch from the
   aligned anchor, push to your fork, open the PR with (a) the dual-role header
   (`技术总监：王宝军（笔名：王小哥）（递归演进线·Steward）` / `执行总监：<your name>`),
   (b) the AI-assistance disclosure standard form quoted **verbatim** from
   `docs/license-protocol-v1.0-20261114.md` §7 (three sanctioned slots only), (c) the ICLA
   section per `CONTRIBUTING.md` §0.5; signed personally, never proxy-signed; unsigned is
   non-blocking (AGPL inbound intact, commercial track constrained). Pre-PR alignment law:
   fetch the newest main and re-base (or cherry-pick your increments) immediately before
   assembly; squash landings move main fast and stale heads produce noise PRs.

## Post-merge

- The stable-roster CI runs on main; if your integration moves HEAD past `freeze_commit`
  (squash landings always do), re-sign the frozen manifest with the canonical face:
  `python -B certify/frozen8.py freeze --repo . --out certify/frozen8_manifest.json --tier2
  certify/frozen8_tier2.md5` (registered structural gap: squash × freeze-commit; candidates
  under ruling; automerge-gate re-sign integration or anchor-criterion upgrade).
- CI state on main: the `rocqwash CI` workflow; the self-heal workflow repairs mechanical
  reds and its own green is the "repair in progress" signal. Reds on the self-hosted
  Windows lane have a known infra class (shallow-cache checkout); see
  `docs/audit-vacgen-20261116.md` siblings and the run logs before treating them as content.

## Files

| File | Role |
|---|---|
| `recursive-evolution-paradigm.md` | the paradigm: axioms S1–S5, Φ/Φ\*, theorems, laws |
| `component-map.md` | every callable component with its CLI one-liner |
| `alignment-and-pr-protocol.md` | the alignment law, PR protocol, known structural gaps |
| `../templates/wf-recursion-wave-template.dwf.ts` | the work stream workflow template (parameterized) |
| `../templates/ci-green-watch.sh` | the CI-green sentinel (alignment trigger) |
| `../templates/pr-body-template.md` | the PR preamble template (dual-role header + disclosure + ICLA) |
