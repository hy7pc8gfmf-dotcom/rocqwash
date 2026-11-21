# step-pushci.md: workflow block ②: single-step push CI (dry-run first → the real run → verdict branching) / `工作流嵌段②：单步推 CI（--dry-run 先行→真发→verdict 分流）`

> Purpose.  Expand the `README-cw.md:124-126` "pushci embed block" into a whole-block copyable command form + real output samples + the verdict branch table + dynamic-workflow embed pseudocode; one of the three canonical workflow-block samples of rocqwash v37.
> Interface.  Document face. It documents `cw.sh pushci` (`tools/pushci.py`; schema `rocqwash-pushci/1`; seven-state verdict `success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|dry-run`; README-cw.md:33, same register). The normative tool face: the `tools/pushci.py` docstring (v36 flagship · five-stage pipeline preflight→push→watch→heal→verdict±merge · pushci.py:5) and `--help`. Citations bind to the v37 capture state (commit `41e74b0`); working-tree line numbers drift. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  `tools/pushci.py` routed through `cw.sh`; a GitHub API token via `~/.netrc` for the push/watch stages; `tools/ci_triage.py` for the heal stage; the whitepaper `docs/workflow-integration-whitepaper-v1.0-20261111.md` §4 for the dual-door discipline. No runtime dependency of this document face itself.
> Evidence.  The §1 dry-run plan and report samples are a real-run record (rc=0) captured on November 11, 2026 by the authoring session; the §2 real-run block was not exercised (real credentials belong to the user side) and its flags were reconciled against the `tools/pushci.py --help` output captured the same day.
> Exit-codes.  Not applicable to a document face; the documented pipeline keeps its implemented exit-code semantics (§3, tools/pushci.py:91-93) unchanged.
>
> Discipline constraints (read before use):
> - **the --dry-run-first order is the canonical embed order**; `--dry-run` prints the plan only with zero side
>   effects, exit 0 (zero git, zero API calls, zero tool subprocesses; tools/pushci.py:87): a human reviews the
>   plan before the real run; a wrong plan does not open the gate.
> - **the verdict is a pinned roster**; the seven states and the exit codes 0/1/2/9 map one-to-one
>   (tools/pushci.py:91-93); branch actions in the §3 table. a failing result is data, not a tool failure:
>   fix-content is content-level failing data, and the tool face still reports normally.
> - **offline drills must come in pairs**; `--injector DIR` and `--git-caller FILE` must be given together;
>   one-sided = usage error exit 2 (an injector without canned git would silently reach a real push;
>   tools/pushci.py docstring "--git-caller" entry).
> - pushci's preflight check reruns only the doctor and net-probe checks (optionally `--pre-scan-gate4`);
>   the push-window four criteria such as suite passing / behind=0 are not in that roster; the two gates stand
>   side by side and neither substitutes for the other; see
>   `docs/workflow-integration-whitepaper-v1.0-20261111.md` §4 (same account at README-cw.md:57-60).

## 1. Step 1: --dry-run first (zero side effects · human review before the real run)

```bash
# ── step-pushci block · step 1: dry-run the plan (run at the rocqwash repository root) ──────
BRANCH=feature/x                 # the branch to push and watch (edit as needed)
REPO_PATH=.                      # target repository directory (zero hardcoding · fully parameterized)

bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --json pushci-dry.json --dry-run
echo "DRYRUN_RC=$?"              # canonical criterion: 0 = plan produced · the plan text goes to stdout
```

**Measured sample** (a live run of `python3 tools/pushci.py --repo-path . --branch main --dry-run --json …` on November 11, 2026
by the authoring session, rc=0; the stdout plan verbatim):

```text
=== ROCQWASH PUSHCI (post-fix push-CI one-shot pipeline) ===
mode=dry-run steps=preflight,push,watch,heal,verdict
PLAN [1] preflight.toolchain: python3 tools/toolchain_dyld_doctor.py (--worker probed by default, gate verdict=healthy)
PLAN [1] preflight.net: python3 tools/net_probe.py --rounds 2 --interval 60 --stable-window (gate STABLE)
PLAN [1] preflight.gate4: not enabled (--pre-scan-gate4 not given)
PLAN [2] push: git -C <repo> -c http.version=HTTP/1.1 push origin main (3 attempts x 45s wait; after three failures with remote host=github.com, ghproxy reroute 2 attempts)
PLAN [3] watch: GET /repos/<org/repo>/actions/runs?per_page=30 (head_branch=main and head_sha=<pushed_sha>, every 150s, status-only (a frozen updated_at is not a stall criterion; status is authoritative) until completed)
PLAN [4] heal: python3 tools/ci_triage.py --repo <org/repo> --run <id> (cap 3); B/E -> probe then rerun (403 accepted idempotently); A -> stop fix-content; C -> stop toolchain; out-of-table -> manual
PLAN [5] verdict: report schema rocqwash-pushci/1, exit codes 0/1/2/9
=== FINAL VERDICT: dry-run (exit 0) ===
```

The corresponding `--json` report (measured · rocqwash-pushci/1 · the plan goes into the `plan` array · zero `stages` side effects):

```json
{
 "args": { "base_ref": "main", "branch": "main", "max_heal": 3,
           "merge": false, "merge_method": "merge", "pr": null,
           "pre_scan_gate4": false, "probe_interval": 60.0,
           "remote": "origin", "watch_interval": 150.0 },
 "evidence": [],
 "final": { "conclusion": null, "verdict": "dry-run" },
 "mode": "dry-run",
 "plan": [ "[1] preflight.toolchain: …", "[2] push: …", "… (same text line-for-line as the stdout plan)" ],
 "schema": "rocqwash-pushci/1",
 "stages": {},
 "steps": [ "preflight", "push", "watch", "heal", "verdict" ],
 "verdict": "dry-run"
}
```

## 2. Step 2: the real run (take this step only after the dry-run plan passes human review)

```bash
# ── step-pushci block · step 2: the real run (all five stages) ────────────────────────
# optional additions: --pre-scan-gate4 (preflight adds the gate4 header-annotation guard pre-scan · passes only at FAIL=0)
#           --merge / --merge-method squash (merge the PR after passing · no open PR → 9 target-missing)
#           --watch-max-rounds N (watch round-cap safety valve · over the cap is fail-loud 9 · recommended for long-watch workflows)
bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --json pushci-report.json
echo "PUSHCI_RC=$?"              # branch on the seven-state roster per §3
```

Honesty note: **the real-run stage was not exercised here** (it needs real remote credentials and real push
permission, which belong to the user side; what was measured here is the `--dry-run` rc 0 and the `--selftest`
wiring face). Every flag in the block above was reconciled against `tools/pushci.py --help` (captured November 11, 2026).

## 3. verdict branch table (seven states × exit codes × workflow actions)

Normative source of the verdict/exit-code roster: tools/pushci.py:91-93 (same register at README-cw.md:33 and 69).

| Exit code | verdict | Meaning | Workflow action |
|---|---|---|---|
| 0 | `success` | all five stages passing (watch reached completed success · heal did not exhaust its cap) | close out; with `--merge` the PR is already merged at this point |
| 0 | `dry-run` | printed the plan only (the §1 canonical form) | read the plan for human review · not counted as a real run |
| 1 | `unstable` | the net-probe stability window did not hold (both probes unstable in the push or heal stage) → must not initiate | rerun after the network is repaired; read report.stages |
| 1 | `toolchain` | doctor verdict≠healthy (environment piece) | remediate the environment per the doctor rerun advice the tool ships |
| 1 | `heal-exhausted` | the watch reported failing · the family B/E reruns did not turn passing within `--max-heal` (default 3) rounds | read `stages.heal.last_triage` (family/action/evidence recorded in full) and decide manually |
| 2 | `fix-content` | classification A content failing (the heal stage stops · **no proxy repair**; repairing is the repair agent's or a human's job) or a merge 409 conflict (live content) | hand to the repair agent or a human; the family is recorded loud with its original value |
| 2 | `gate4-block` | the `--pre-scan-gate4` pre-scan found FAIL≠0 | read report.stages.preflight.gate4.fail_files and fix each file's header annotations |
| 2 | (no verdict) | argparse usage error (stage dependencies watch⇒push · heal⇒watch · --merge⇒watch and the like) | fix the command line; compare `bash cw.sh help pushci` |
| 9 | (no verdict) | fail-loud target missing (repo/remote/branch/PR/toolchain piece missing · netrc missing · API unreachable · API 4xx/5xx hard error · watch round cap reached) | supply the targets/credentials manually and rerun |

The same quick reference as the note at README-cw.md:54; pushci passes the verdict roster through:
success/dry-run=0 · heal-exhausted/unstable/toolchain=1 · fix-content/gate4-block=2 · 9 = target missing.

## 4. Offline drill form (for workflow self-test · zero real network, zero real push)

```bash
# injector (canned API + tools) and git-caller (canned git responses) must come as a pair —
# one-sided = usage error exit 2 (prevents an injector without canned git from silently reaching a real push)
bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --injector /path/to/injdir --git-caller /path/to/git-canned.json \
  --sleep-scale 0 --json pushci-inj.json
```

The scenario shapes and the six-scenario 15-case normative source: `tests/test_pushci.py` and the pushci docstring "offline-testable"
section (both the steps form and the flat form · the API call stream lands in `<injector>/api_calls.json` as evidence).

## 5. dynamic-workflow embed pseudocode

```text
// block ② single-step push CI: dry-run gate → real run → verdict branching (tool: cw.sh pushci)
phase "pushci-step" {
  // 1) dry-run gate: the mechanical pre-check before human plan review (the exit code is the confirmation · §10)
  const dry = await world.run("bash", ["cw.sh", "pushci",
      "--repo-path", ".", "--branch", "feature/x",
      "--json", "pushci-dry.json", "--dry-run"]);
  if (dry.exitCode !== 0) return { verdict: "plan-unusable", rc: dry.exitCode };

  // 2) plan review: a subagent reads the plan array of pushci-dry.json and judges only open-gate or hold
  const review = await agent({ role: "gate-reviewer",
    ask: "Read the plan array in pushci-dry.json and answer gate-open|gate-hold with a reason (modify no files)" });
  if (review.answer !== "gate-open") return { verdict: "held", why: review.reason };

  // 3) real run: a check the world has already adjudicated is not re-asked to a subagent — the exit code is the verdict-roster index
  const real = await world.run("bash", ["cw.sh", "pushci",
      "--repo-path", ".", "--branch", "feature/x",
      "--pre-scan-gate4", "--watch-max-rounds", "20",
      "--json", "pushci-report.json"]);
  switch (real.exitCode) {
    case 0: return { verdict: "success-or-dryrun" };            // read report.verdict for the split
    case 1: return { verdict: "env-red",                        // unstable/toolchain/heal-exhausted
                     next: "read report.stages and decide manually" };
    case 2: return { verdict: "content-red",                    // fix-content/gate4-block/usage error
                     next: "hand to the repair agent; for gate4-block read fail_files and fix each file" };
    case 9: return { verdict: "target-missing",                 // fail-loud
                     next: "supply the targets/credentials and rerun" };
  }
}
```

## 6. Honesty notes

- The two §1 samples were produced by a live `--dry-run` run of the authoring session on November 11, 2026 (rc=0 · tmp report
  path); the §2 real-run block was not exercised (credentials belong to the user side), its flags reconciled against the captured `tools/pushci.py --help` output.
- Every verdict-branch-table cell anchors the pushci docstring exit-code section (tools/pushci.py:91-93) and the five-stage
  pipeline section (pushci.py:5-46); unanchored cells (such as "usage errors map to 2") anchor the argparse stage-dependency
  clauses (docstring "stage dependencies (usage error 2)").
- The push-window four criteria (certify/push_gate.py window: c1 ci-idle / c2 local≥remote /
  c3 fetch-clean / c4 cert-green) and the pushci preflight check are **two doors**, neither substitutes for the other:
  the side-by-side account is in the whitepaper §4.

(English brief) Workflow block ②: single-step push-CI via `cw.sh pushci`.
Canonical order: `--dry-run` first (zero side effects, exit 0, plan printed +
report), human review of the plan, then the real run; branch on the seven-state
verdict roster (success/dry-run=0, heal-exhausted/unstable/toolchain=1,
fix-content/gate4-block=2, target-missing=9). Offline drills require
`--injector` + `--git-caller` as a pair (single-sided = usage error exit 2).
pushci's preflight gate (doctor + net-probe ± gate4 pre-scan) is deliberately
NOT the push-window four-criteria gate; see the whitepaper §4.
