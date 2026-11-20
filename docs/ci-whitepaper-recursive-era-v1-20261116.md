# rocqwash CI Technical Whitepaper: The Recursive-Iteration Era (v1.0), documented November 16, 2026.

> Purpose.  Failure-class taxonomy, triage interface and repair playbook for the rocqwash CI **after** recursive self-improvement (auto_round rounds, agent waves, the self-heal watch) became a normal producer of repository changes. Supersedes the host-mismatch era playbook (eleven root causes, November 16, 2026 assessment: code page / autocrlf / HOME override / isolated mode / shell escaping): those classes still occur, and this whitepaper covers what the old playbook **cannot**: failures caused by the iteration machinery itself and by its interaction with hosts, services and concurrent sessions.
> Interface.  Document face. Companion machine interface: `docs/ci-triage-table.json` (schema `rocqwash.ci-triage-table/1`): the symptom→cause→prescription table this whitepaper documents, in machine-readable form. Consumers: the self-heal watch (`selfheal_rocqwash.py`), any session or agent triaging a red run, and future auto-repair agents. Contract: match the failing step's log against `markers`; apply `prescription`; respect `auto_repairable` and `escalation`; record the outcome class in the repair ledger (repaired / escalated / watch-only-guard-correct). The original mixed-language text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Companion table `docs/ci-triage-table.json` and the repair ledger `docs/repair-ledger.jsonl` (outcome-class records, section 4); in-repo subjects cited by the classes: `autonomy.json` and `tools/axiom_guard.py` (the fitness-gate rewire, R5), `ci.yml` and `tools/mcp_server.py` (service-face coupling, R8), `tools/repair_scope.py` (guard classes, R1); desk-side or cross-line faces cited as pointers, not in-repo dependencies: the self-heal watch (`selfheal_rocqwash.py`), the service map `techdocs/本机服务面与勿扰清单-20261116.md` (R6/R8), the axiom-guard verify contract `techdocs/接口契约-axiom-guard-verify-换轴` (R5), and the cross-line experience index `exp/INDEX.md` (section 6). Read-only document face; no runtime dependency.
> Evidence.  Each class (R1-R16) states symptom, mechanism, guard, prescription and auto-repairable status with its originating run numbers and commit SHAs; section 5 records the case files (runs 43860918397, 43922602217, 44367838970, 44373602464 and 44374294488); section 6 carries the replication obligation: every new class lands here, as a `docs/ci-triage-table.json` row and as an experience card in the same round.
> Exit-codes.  Not applicable to a document face; the rc values quoted in the class sections (rc=0, rc=1, rc=2, rc=111, the rc>=128 downgrade branch) and the HTTP status codes quoted in the playbook and lineage (403, 409, 422) are the documented tools' and checks' observed codes, described as implemented.

---

## 1. Why this CI reddens easily, is hard to fix, and recurs

Four amplifiers, all structural:

1. **Landing cadence**: agents, rounds and waves push many small commits per day; red probability scales with integration count.
2. **One-sided verification**: a fix validated only on the machine that made it is unverified by construction elsewhere (host branches, env vars, platform temp dirs). Case: the TMP fallback landed with `tempfile.gettempdir()` but **without `import tempfile`**: green on Windows (TMP always set, fallback branch never taken), `NameError` on Linux (run 43860918397).
3. **Repair capacity at L1**: the repair agent executes approved actions only; content reds outside its rewrite table are recorded, not fixed. Until the fitness gate is rewired (axiom_guard) and the action space grows class by class, most content reds escalate to sessions by design.
4. **Multi-session concurrency**: several sessions push to the same branch from different working trees; the self-hosted runner's checkout resolves through a path-rewritten dependency on one of those trees staying current (see R8).

"Hard to fix" is therefore not one bug: it is the gap between **red production rate** (amplifier 1) and **classified, verified repair rate** (amplifiers 2-4). The remedy is this whitepaper + the triage table + the E-series guards, not ad-hoc heroics.

## 2. Failure-class taxonomy (recursive era)

Each class: **Symptom** (stable log/observable markers) → **Mechanism** → **Guard** (prevention) → **Prescription** (repair) → **Auto-repairable** (today).

### R1: Recursive-artifact drift (lane registered, artifact absent)
- Symptom: suite line `FAIL (rc=2)` with `can't open file '.../<name>.py'`; roster count includes a lane whose file is not in the checkout.
- Mechanism: a round/agent registered a test lane but the target file is untracked or landed in another lane; the roster grew before the artifact did.
- Guard: roster derivation must assert file existence per lane (registration without file = red at roster-build time).
- Prescription: drop the lane registration (commit 2748b52 precedent), keep the file lane pending; re-register when the file lands **with an rc=111 skip protocol**.
- Auto-repairable: **yes** (guard class 1 of the repair scope).

### R2: Mechanical-wash overreach (frozen / self-referential faces)
- Symptom: three stations fail-loud together; mapping-source table entries replaced by standard words (norm_lint then flags ordinary English phrases: an active false-positive machine).
- Mechanism: the wash engine's target set did not exclude the frozen set or the mapping source table itself (e04f2f6 precedent; 29ef3ba rollback).
- Guard: exclusion table as a single source (`tools/repair_scope.py`, F1); self-reference guard (`--a2-table` precedent).
- Prescription: revert the touched frozen faces to pre-round content (surgical `checkout HEAD^ -- <faces>`), keep the clean improvements, record the class in the round ledger.
- Auto-repairable: partial (revert leg yes; re-integrating the intended improvement needs an agent).

### R3: Stale repair target (superseded head)
- Symptom: a prepared repair no longer applies; the branch moved while the fix was being verified.
- Mechanism: fix prepared on head A; branch advanced to B; A's patch conflicts or is moot.
- Guard: compare-API discrimination (ahead/identical = covered → skip; behind/diverged = not proven → proceed), then re-apply the fix **onto the current head** with a 3-way apply; conflicts escalate.
- Prescription: repair-on-current-head procedure (E3).
- Auto-repairable: partial (re-apply yes; conflicts escalate).

### R4: Intent & queue violations
- Symptom: cancelled runs re-enter the queue; queued runs pile beyond capacity; "everything is queued and old runs fail again".
- Mechanism: pre-governor behavior: revival of cancelled runs treated as backlog; unbounded queue growth under push bursts.
- Guard: cancelled = intent, never auto-revived; queue governor keeps MAX_QUEUED_RUNS (3), oldest trimmed, in-progress never touched.
- Prescription: none needed (guard-correct); manual rerun remains available.
- Auto-repairable: the guard IS the repair (watch-only-guard-correct).

### R5: Fitness absence (repair without a real gate)
- Symptom: rounds land with `verify_rc` reflecting only the linter's selftest; a repair that "passed" breaks the suite or the proof surface.
- Mechanism: `DEFAULT_VERIFY_CMD` pointed at `norm_lint.py --selftest`: the gate validated the validator, not the change.
- Guard: rewire `verify_cmd` to the axiom_guard compile leg (autonomy.json; see `techdocs/接口契约-axiom-guard-verify-换轴`); repairs and rounds share the same gate.
- Prescription: rewire + measure the gate cost once, then set the round cadence from measurement.
- Auto-repairable: the rewiring is a one-time integration (done via autonomy.json), after which this class is structurally closed.

### R6: Watchdog reflexivity (the watch itself is the failure surface)
- Symptom variants: (a) run-level conclusion `skipped` misread as red; (b) the watch dies with the runner it guards; (c) the runner's checkout depends on an out-of-repo tree staying current (path-rewritten dependency), so a lagging tree fails `not our ref` at checkout: **the local self-hosted face class**. Variant (c) refinement (November 17, 2026): for rocqwash the bridge resolves to the DESK DEV TREE ITSELF (`.gitconfig` insteadOf → `file:///D:/ComplexAnalysis/rocqwash`), so the desk tree lagging remote by one commit reproduces the red; and `not our ref` must be adjudicated compare-API-first: verify ancestry (behind=0 = NOT an orphan) before concluding a force-push casualty (the November 17, 2026 case was a rebase integration, not an orphaning).
- Mechanism: guards and watchers are code too; their own lifecycle and dependencies are part of the failure surface.
- Guard: skip≠red judgment (three-way conclusion reading); runner heartbeat + schedule-failure alarm (watch-the-watch); the dependency tree must be kept current (sync before integration) and the dependency documented in the service map (`techdocs/本机服务面与勿扰清单`).
- Prescription: correct the judgment (skip = guard-correct); sync the dependency tree; escalate watch-death to the desk with the heartbeat evidence.
- Auto-repairable: judgment fixes yes; runner lifecycle needs the desk.

### R7: Environment-branch fixes (a fix with an unexercised branch)
- Symptom: a host-specific fallback added in a fix crashes **only on the host that takes that branch** (`NameError: name 'tempfile' is not defined` on Linux; green on Windows where TMP always exists: run 43860918397).
- Mechanism: the fix added a fallback referencing `tempfile.gettempdir()` without `import tempfile`; the dev machine never executes the fallback branch, so local green proves nothing for the branch.
- Guard: **every new host-branch in a fix must be executed at least once before integration** (unset the env vars locally and run; the suite's host-matrix exists for exactly this). The eleven-cause playbook's rule "pin irrelevant host variables inside the fixture boundary" extends to: "exercise every fallback branch you add".
- Prescription: add the missing import/requirement on the branch, land, and add the branch to the roster's platform-sensitive watch until three consecutive passing runs.
- Auto-repairable: yes (one-line class; the diagnosis needs this table).

### R8: Service-face coupling (repository updates break local services)
- Symptom: the self-hosted face disconnects; the MCP tools/list count changes or the server drops; the sentinel daemon stops matching its CLI contract.
- Mechanism: local services consume repository faces (`tools/mcp_server.py`, `ci.yml` matrix labels, sentinel CLI); a refactor that renames/moves/rescopes them breaks the wiring.
- Guard: the service map and do-not-touch rules (`techdocs/本机服务面与勿扰清单-20261116.md`): tool signatures additive-only; matrix labels checked against the runner's actual labels; stop-the-line declaration on any service anomaly.
- Prescription: follow the map's recovery pointers; re-register only per the map.
- Auto-repairable: no (service face is out-of-repo; desk-gated).

### R9: Platform evolution (runtime deprecations)
- Symptom: deprecation warnings escalating to failures on hosted runners ("Node 20 deprecated… forced to Node 24").
- Mechanism: action versions pin runtime majors; GitHub deprecates majors on a published schedule.
- Guard: quarterly `uses:` audit against each action's latest release (fetch-before-use precedent: upload-artifact v4 → v7.0.2).
- Prescription: bump the action, keep the flag face, watch one run.
- Auto-repairable: yes (one-line class).

### R10: Multi-session collision (same tree, same machine)
- Symptom: a repair or round touches faces another session holds dirty (uncommitted pending lanes); stash/rebase sequences; "my fix disappeared".
- Mechanism: concurrent sessions share one working tree; integration waves overlap pending lanes.
- Guard: each work session's face selection must read `git status --porcelain` first and exclude dirty faces (collision-free matrix before concurrency); integration waves use 3-way apply onto the current head and preserve pending lanes.
- Prescription: stash→rebase(resign)→push→pop sequence; record both sides in the ledger.
- Auto-repairable: partial (the union merge is mechanical; adjudication of conflicting intents is not). **Churn variant (November 17, 2026, run 138)**: with `cancel-in-progress: true`, the cancel fires when ANY run enters the group: an older QUEUED run, the moment it started, cancelled the NEWER in-flight tip run (the guard cancelled the fresh verdict it was meant to protect). Root cure: cancel-in-progress OFF (in-flight protected) + the self-heal `ci_queue_governor` retires stale QUEUED runs per head branch (keep newest, cancel older queued, in_progress never touched) in the reconcile and automerge-only passes.


### R11: shallow runner checkout × frozen git-anchor (DRIFT false-flag; November 16, 2026 live case)

- **Symptom**: `DRIFT git锚 HEAD <sha> 非 freeze_commit <sha> 后代` on the local self-hosted face while hosted faces pass; the workspace `.git/shallow` file present; the ancestry verdict fires even though the main lineage is linear and desk-approved.
- **Mechanism**: the runner workspace was a depth-1 shallow clone; `git merge-base --is-ancestor freeze_commit HEAD` evaluates over the visible (single-commit) history and reports not-ancestor (rc=1) - the check's DOWNGRADE branch (rc>=128, objects missing) never fires because rc=1 is a *verdict*, not an error. `ci.yml fetch-depth: 0` alone did not unshallow the cached workspace (the unshallow fetch must actually complete - a NETRED-window abort leaves the shallow file in place).
- **Guard**: the self-hosted checkout carries `fetch-depth: 0`; after one desk unshallow (git fetch --unshallow from the local dev tree via file:// transport, zero-network) the workspace keeps full history.
- **Prescription**: desk one-time unshallow of the runner workspace; durable fix = frozen8 check detects the shallow state and downgrades the git-anchor ring (desk-gated, frozen face).
- **Auto-repairable**: no (frozen face; desk-gated).


### R12: environment-conditional contract branch × runner PATH drift (November 17, 2026 live case)

- **Symptom**: one test red on the local self-hosted face only, all hosted faces green, every other face passing (t_clean_mode V16: `rc=0 out='COMPILED-ALL 0 modules ...'` against a report-and-refuse rc1 contract); the same job was green the day before with zero content change.
- **Mechanism**: a report/refuse branch keyed on environment presence (the clean-mode report lived INSIDE the import-time toolchain gate) silently changes meaning when the machine's PATH gains the dependency: ROCWASH_CLEAN=1 stopped being honored and the tool executed under clean mode. Content fingerprints cannot see environment drift: the suite went green→red with no code change (the runner PATH gained the Rocq/OCaml toolchain).
- **Guard**: every report/refuse branch keyed on environment presence must be executed on BOTH faces before integration (a PATH stub simulates presence); report-not-execute contracts must be checked ABOVE the presence gate, never inside it; test vectors asserting rc must be environment-aware (assert the invariant: marker absence, contract rc per branch: not one environment's rc); the test docstring's own "machine-independent" claim must hold per vector (it was false for V16/V17).
- **Prescription**: move the clean-mode check above the toolchain gate (report always, exit 1, never execute; keep the standing FATAL byte-identical for the absent path); make the default-mode vector environment-aware. Diagnosis recipe: `_runner_loop.log` timeline (green before / red after the environment change) + PATH-stub byte-level reproduction on the old blob.
- **Auto-repairable**: no (contract repair touches tool + test; desk-gated). Sibling class: R7 (a fix carrying an unexercised branch): R12 is the environment-drift flip of an exercised branch.


### R13: silent gate stall (a gate reads a signal no trigger produces; November 17, 2026 live case)

- **Symptom**: no red anywhere: a standing automation just never acts. PR #10 sat open with `hold (no head CI yet)` in every reconcile pass while its head commit had ZERO check runs; the desk noticed only because the user asked why the merge never happened.
- **Mechanism**: the automerge green gate matched push-event runs by head SHA, but ci.yml triggers only on `push: [main]` and `workflow_dispatch`: a supply/* PR head can NEVER produce the signal the gate waits for. The gate was implemented correctly against a pipeline that did not exist: the trigger was never extended when the gate landed.
- **Guard**: every gate's required signal must be wired end to end (trigger → run → verdict). Landing a gate demands the same audit as integration a lane: enumerate the producing trigger, the matching key, and the verdict source: a gate with no producer is a stall, not a hold. A reconcile log line repeating identically for hours is the stall's fingerprint.
- **Prescription**: extend the trigger (`pull_request` types opened/synchronize/reopened), broaden the match (push / workflow_dispatch / pull_request runs: a PR-event run's head_sha is the MERGE-ref commit, so match via the `pull_requests` link too), and let the gate self-start the missing signal (route ci.yml at the PR head branch when no run exists). Gate on the hosted faces via the jobs API, never the run-level conclusion: the local self-hosted face is main-only evidence (main_only gate) and a branch route from a ref whose ci.yml predates that gate still runs it.
- **Auto-repairable**: partial (match widening + route-on-demand is mechanical; trigger changes touch the blocking workflow: desk-gated). A blindness sub-face (November 17, 2026, run 118): GitHub emits NO workflow_run event for a validation-failed workflow file, so the self-heal watch is structurally blind to parse death ; the scheduled reconcile carries a read-only parse-death probe (newest main run jobs=0 = the signature; last-known-good reported alongside) as the in-system sensor; the blocking-file fix stays desk-gated.


### R14: data-shape change → consumer breakage (seed form migration; November 18, 2026 live case)

- **Symptom**: hosted faces green, the canonical face red with THREE stacked failures from one root: `jargon map has no active rows` (a loader reading the new JSON form with an md-table parser), `face absent from whitepaper` ×73 (a single-source transcription check rejecting tool-track faces), `source drifted from the pinned snapshot` (entries re-signed but the provenance md5 not). Every red is real on the canonical machine; every hosted face is green because its canonical-path checks SKIP.
- **Mechanism**: a sync tool migrated a seed's shape (md table → JSON, 62→159 entries) but did not carry its consumers: the loader stayed md-only, a checker kept a single-source assumption, and the sync's own half-finished step (md5 re-sign) was skipped. Hosted SKIP masked all of it; the canonical face is the only real judge.
- **Guard**: before a shape migration lands, grep every consumer of the old shape and patch them in the SAME commit (loader + checkers + provenance); the sync tool must run a post-sync consumer smoke (all consumers against the new shape) as its exit gate; treat hosted-green + canonical-red as the highest-priority signal (the red is real).
- **Prescription**: reproduce on the canonical machine by calling the check functions directly (prints full bad-detail faster than CI logs); patch each consumer to accept BOTH shapes during a transition window; re-sign drifted provenance md5 per the sync discipline; move time-dependent assertions (e.g. "raw X must fail loud") when the shape becomes legal. Local gates: seeds 42/0, body 60/0, selftest PASS before push.
- **Auto-repairable**: partial (loader/checker compatibility patches are mechanical once diagnosed; the sync discipline completion needs the sync tool's author).


### R15: provenance pin drift on a canonical-only verification layer (snapshot md5; November 19, 2026 live case)

- **Symptom**: the canonical face red with `t_engines_seeds` (jargon segment `snapshot-md5`) and `t_engines_body` (its regression segment re-runs the seed suite): `source drifted from the pinned snapshot; re-transcribe the seed per the sync discipline: ... (pinned 1b042a18 / current f21428f0)`. Hosted faces green on the SAME commit.
- **Mechanism**: a pinned-source edit (unit-u5, 9a5daeb: a jargon-mapping exemption cell) landed without re-signing the seed's provenance md5 pin (`seeds/jargon/jargon-map.json` still pinned the wave59 value). The check (`check_snapshot_md5`, tests/t_engines_seeds.py) opens the pinned sources at ABSOLUTE paths (two outside the repo, one in-repo but absolute); on hosted runners the paths raise OSError → the check SKIPs → hosted is structurally blind, and the canonical face is the only layer that actually verifies. The red surfaced only when the desk tree (the local face's bridge checkout = the dev tree, R6(c)) ingested the u-work stream , the red's appearance time ≠ the introduction time (trace the introduction with `git log -- <file>`).
- **Guard**: a pinned-source edit and its md5 re-sign are same-commit (R14's discipline applied to provenance); re-sign ONLY after the sync tool's zero-write plan verdicts IN-SYNC (content healthy, pin alone stale); hosted-green + canonical-red here is structural truth: the pin check cannot run anywhere but the canonical machine.
- **Prescription**: on the canonical machine run `python -I tools/jargon_map_sync.py` (zero-write plan) and require `VERDICT IN-SYNC`; if IN-SYNC, re-sign the drifted md5 in `seeds/jargon/jargon-map.json` provenance.sources (wave59 precedent 6d79e29; live precedent b3cbcf0) and land it the same commit as any source edit; if the plan is NOT in sync, escalate (content retag needed: machine-apply returns to note/alternation-guarded). Verify with `python -I tests/t_engines_seeds.py` (jargon segment 9/0) before pushing. A hosted-verifiable pin form (repo-relative for in-repo sources) is a design change ; desk-gated, separate ticket. **Discriminator (November 19, 2026, run 44506833563): if the zero-write plan verdicts IN-SYNC while snapshot-md5 still drifts, this is the cross-tree race (R17), NOT drift ; do NOT re-sign; tree-sync + rerun instead.**
- **Design landed (provenance v2, desk ruling November 19, 2026; schema face `docs/pin-provenance-v2.md`)**: pins now record the evidence body, not paths, and the prescription's "separate ticket" design change has landed. A repo source pins the committed git blob sha of its own content (`git rev-parse HEAD:<path>`), a pure git query every machine answers identically: the hosted faces now truly verify the consistency layer, the pin is EOL-immune, and the blob-sha pin is race-dead by construction (no second tree holds the pinned bytes). An external source pins the md5 of an in-repo byte snapshot taken at sign time (`seeds/jargon/_snapshots/`): the consistency layer (snapshot bytes against the pin) is machine-checkable everywhere, while the freshness layer (snapshot against the out-of-repo upstream) stays canonical-only by design; off the canonical machine an absent upstream reports `SKIP (declared, freshness unverifiable off-canonical: upstream absent)` rather than a silent skip. The structural blindness of this class (absolute-path OSError turning hosted verification into SKIP) is retired by the same change, and the consumers move in the same commit (R14's discipline applied to the pin form itself). The fingerprint law carries one further tightening (November 20, 2026 closing package): the pin is an EOL-agnostic fingerprint, both md5 comparison layers (snapshot consistency, upstream freshness) take the md5 over CRLF-to-LF normalized bytes, the same normalization law `.gitattributes` applies to the checkout, so a pin anchors content identity, not line endings.
- **Auto-repairable**: yes, conditionally: the mechanical md5 re-sign is safe ONLY behind the IN-SYNC plan verdict AND the R17 discriminator (IN-SYNC plan + drifted md5 = race, re-signing would pin STALER bytes); anything else escalates to the desk.


### R16: fingerprint-gate exemption dead (hashFiles negation; November 19, 2026 live case)

- **Symptom**: no red at all: the opposite: a pure-prose push computed a DIFFERENT verdict-cache key than the last green run (stored f7964454 → lookup c7576ef0), so every push ran FULL and the ANCHORS branch never executed once since the gate landed. The waste is silent; the skip half of the gate was unreachable by construction.
- **Mechanism**: `hashFiles('**', '!path...')` negation patterns do not exclude on the Actions runner: the FP changed even when the diff touched only allowlisted prose faces. Diagnosed by live validation (the first prose-only push since the gate landed, 17af7181) and confirmed by a two-run key comparison: the only honest evidence that an exemption face actually exempts.
- **Guard**: an FP exemption is only real if two runs' keys PROVE it: push a diff confined to the allowlist faces and compare the verdict-cache keys; key equality exempts, key difference indicts the construction. Never trust pattern syntax alone.
- **Prescription**: fingerprint the committed tree directly: `git ls-tree -r HEAD | grep -v -e '<allowlist patterns>' | git hash-object --stdin` (content-addressed blob listing, EOL-immune, portable across hosted Linux/Windows/macOS; standing form landed in 74cc082). Verify locally against real commit pairs (a prose-only diff leaves FP unchanged; code and data diffs change it). The next prose-only push then takes the ANCHORS branch (anchor tier: frozen8 + station + registry faces): judge the mode by the job-step conclusions, never the run-level conclusion (the canonical local face carries no gate (R12) and other faces may red for unrelated roots).
- **Auto-repairable**: no (workflow-file surgery is desk-gated; the two-run key comparison itself is mechanical and can run as a watch probe).


### R17: cross-tree pin race (checkout seed vs absolute-path source desync; November 19, 2026 live case)

- **Symptom**: identical text to R15 on the CANONICAL face: `source drifted from the pinned snapshot ... (pinned a82eb4d5 / current f21428f0)`: but the source edit landed WITH its re-sign (b2a3b7e, discipline followed), the canonical machine reproduces 9/0 GREEN on the same commit, and only one face (local self-hosted) is red while both hosted faces are green.
- **Mechanism**: the pinned path is ABSOLUTE and points into the dev tree, while the seed JSON travels in the runner checkout: two trees. The JOB_STARTED hook mirror-synced the dev-tree ref to the push head at 10:33:43, but actions/checkout (bridge-resolved, R6(c)) detached at the PREVIOUS head at 10:33:44; for the window until the working files caught up, the checkout's fresh seed (new pin) was compared against the dev-tree working file (old bytes). Same words as R15, opposite disease: transient desync, not content drift.
- **Guard**: the discriminator is mechanical: run the sync tool zero-write plan: IN-SYNC plan + drifted snapshot-md5 = race (the seed entries match the table, so only the pin-vs-file pair is stale); non-IN-SYNC plan = true drift (R15). NEVER re-sign in the race shape: the current bytes are the STALER side, and re-signing would regress the pin and mask the newer content.
- **Prescription**: tree-sync first, then rerun: bring the dev tree to the run head (desk; the checkout is already there), verify the seed suite green locally on the exact red commit, then rerun-failed-jobs (precedent 44506833563 → attempt 2 all-green). Record the outcome in the repair ledger. Durable cure candidate (third live evidence): repo-relative in-repo pin sources would collapse the two-tree window and the hosted structural blindness in one design change: desk-gated.
- **Auto-repairable**: no: the repair acts on the dev tree, which is desk territory the hosted self-heal cannot touch; the discriminator itself is mechanical and belongs in the R15 auto-leg's gate.
- **Design landed (provenance v2 sync, November 19, 2026; schema face `docs/pin-provenance-v2.md`)**: the race's repo-source form is structurally dead under the v2 pins. A repo source is judged against the blob sha recorded in its own commit (`git rev-parse HEAD:<path>`), so no second tree's working bytes can enter the judgment and the checkout-versus-dev-tree window has nothing left to disagree about; the durable cure this section pointed at (repo-relative in-repo pin sources) is the landed form. The external-source freshness layer remains canonical-only by design (an absent upstream reports the declared SKIP, never a silent one), while its consistency layer verifies the in-repo snapshot on every machine; the discriminator above remains the verdict of record for the v1 pin form and for external freshness on the canonical face.


### R18: evidence snapshot re-laid by a doc-face work stream (i18n x evidence-layer conflict; November 20, 2026 live case)

- **Symptom**: hosted Linux red at `jargon/snapshot-md5` with the v2 wording: `provenance pins red: external consistency seeds/jargon/_snapshots/annotation-whitepaper-....md: normalized snapshot md5 8876e13f != pinned f390121c`, while the repo blob pin and the terminology consistency PASS. Canonical freshness (desktop) diverged for terminology: normalize(upstream)=0eb8bf56 vs pin bd52cc8b.
- **Mechanism**: unit-u3 (59ef077) treated the EVIDENCE snapshot as a doc face: it re-laid the terminology snapshot under `seeds/jargon/_snapshots/` to the standard doc-face form, moved the TRUE upstream bytes to the `.zh.md` sibling, and re-pinned all three sources - the annotation pin to a value (f390121c) verifiable against neither the in-repo snapshot nor the desktop authority (a divergent annotation copy on the re-pinning machine, unreconciled). Evidence snapshots are byte-level corpus (the v2 contract), not authored faces; the doc-face sweep saw a `.md` carrying CJK and processed it.
- **Guard**: `_snapshots/` files are corpus, not prose: the five-gate sweep EXEMPTS them by registration (basis: byte-exact external evidence), and doc-face re-lays never touch them; upstream changes re-sign only from the DESKTOP authority through the sync tool (normalized md5), never from a foreign copy. The suite's snapshot-md5 check is the tripwire - it caught R15, R17 and R18 within one face run each.
- **Prescription**: restore evidence semantics - the true bytes (desktop-authority md5, preserved by the work stream in the `.zh.md` sibling) return to the primary snapshot slot; the re-laid face moves to a clearly-labeled non-evidence name (`.docface-re-laid`); pins re-sign to the normalized snapshot md5 (annotation 8876e13f, terminology 0eb8bf56 - v2 standing values). The foreign pin (f390121c) registers as a reconciliation finding for the agent (annotation-copy divergence, desktop vs Mac).
- **Auto-repairable**: no: requires the desktop authority judgment (which annotation version is canonical); the mechanical part (pin re-sign behind verified snapshot bytes) landed in this case's fix.

## 3. Judgment matrix

| Surface | Role |
|---|---|
| Linux / Windows hosted | blocking faces (stable roster) |
| Windows self-hosted (LIVE-ROCQWASH) | blocking face + canonical-path evidence (depends on R6 tree-currency; the bridge resolves to the dev tree itself: see R6(c) variant) |
| macOS hosted (mac-verify.yml) | advisory face (`continue-on-error`): a capacity-starved macos-15 queue must never block the pipeline (November 17, 2026 routing redundancy: the mac face moved out of the blocking matrix) |
| Platform-sensitive watch agents | advisory (`continue-on-error`), never block; host-noise tracked here |
| self-heal watch | triage + transient heal + content-red recording + weekly branch census (merged-stale stubs reported as deletion CANDIDATES, never deleted in-run); **its own skips are guard-correct, not red** |
| snapshot-md5 pin checks (absolute-path pinned sources) | canonical-only verification layer: hosted faces structurally SKIP (R15); the canonical face is the only judge |

## 4. Repair playbook (procedure per red)

1. Pull the **whole-run** log (single-job endpoint 403s; run endpoint works).
2. Match the failing step against `docs/ci-triage-table.json` markers → class.
3. Read the class section above; apply the prescription; respect `auto_repairable`.
4. Land the fix through the same gates as any change (fitness gate, language gates, certification-face exclusion).
5. Record the outcome class in the repair ledger (`repaired / escalated / watch-only-guard-correct`): this is how "watched" stays distinguishable from "failed to fix".

## 5. Case files

- **Run 43860918397** (two reds): R7 (Linux, tempfile import missing in the TMP-fallback branch: fix c9f23d3) + R6(c) (Windows self-hosted, `not our ref` at checkout ; the runner's path-rewritten dependency tree lagged the remote; resolved by syncing that tree, and registered as a standing dependency in the service map).
- **Run 43922602217** (attempt 3, November 17, 2026, three chained events): R6(c) variant (checkout `not our ref d8ba0a86`: the bridge resolves to the dev tree itself; the desk tree lagged the fresh rebase integration by one commit; hosted faces green; fix = desk fetch+ff then rerun-failed-jobs) → R12 (t_clean_mode V16: the runner PATH gaining the Rocq/OCaml toolchain flipped the clean-mode contract branch; fix 35d7f63 = report-not-execute above the gate + environment-aware V17; verified 18/18 on BOTH faces; the desk-side triage agent independently reproduced the red with a PATH stub on the old blob and recovered the green→red timeline from `_runner_loop.log`) → **CI #116 all green** with the routing redundancy live (mac-verify advisory green twice; the macos-15 capacity shortage structurally cured by moving the mac face out of the blocking matrix + concurrency supersede on the CI group).
- **Run 44367838970 + the November 19, 2026 repair chain** (two classes, one desk session): R15 (local face, run 44367838970: unit-u5 source edit 9a5daeb left the provenance pin stale; hosted structurally blind; the desk-tree ingestion surfaced the drift; re-signed by the agent itself in b3cbcf0 per the sync discipline) + R16 (17af7181 prose push → FULL with a key mismatch, proving the hashFiles negation dead → gate repaired in 74cc082 with the ls-tree construction, hosted FULL green run 44373602464 → prose push cdb0ae9 → **ANCHORS/ANCHORS on both hosted faces, judge run 44374294488: the anchor tier's first real execution**). Both classes landed in the taxonomy and the triage table in the same round.
- **Run 44506833563** (November 19, 2026): R17 (local face; unit-v15 b2a3b7e re-signed the pin correctly, yet snapshot-md5 compared the checkout's fresh seed against the ABSOLUTE dev-tree path still at the old bytes: hook ref-sync vs bridge checkout-detach race window; hosted green by structural blindness; desk ff + rerun-failed-jobs → attempt 2 all-green; repair ledger EXP-20261119-0002). **Why the self-heal could not fix it**: the failing text matches R15's content-red markers word-for-word, and R15-class reds are recorded-not-rerun by design; the R15 auto-leg's safe action (re-sign behind an IN-SYNC plan) would have pinned the STALER bytes: the wrong direction. Same words, two diseases; the discriminator (IN-SYNC plan + drifted md5 = race) now gates the R15 leg and routes this shape to the desk.
- **Provenance v2 integration** (November 19, 2026, desk ruling): the hosted-verifiable pin form that the R15 prescription and the R17 durable-cure note both pointed at landed as provenance v2 (schema face `docs/pin-provenance-v2.md`). Repo sources pin the committed blob sha of their content (`git rev-parse HEAD:<path>`); external sources pin the md5 of in-repo byte snapshots under `seeds/jargon/_snapshots/` taken at sign time; the v1 seed moves in one commit with its consumers patched (R14's discipline applied to the pin form), through the sync tool's one-shot migration form and the seed suite as the exit gate. This edit is prose-only, so it rides the fingerprint gate's exemption face. Hosted first-execution evidence slot: the hosted judge run's seed-suite log carrying the declared-SKIP line (`SKIP (declared, freshness unverifiable off-canonical: upstream absent)`) is the proof that the freshness layer runs honestly on hosted; record the run number here post-run.
- **Calibration wiring + EOL normalization integration** (November 20, 2026, closing package): one round carries two faces. First, the calibration signal reaches the scheduling feedback face: `learning_feedback` consumes the calibration lane, an empty calibration account reads as a null reading reported honestly (never padded), and the default run's stdout summary carries the calibration line; evidence slot: the default-run summary and the selftest verdict are recorded post-run. Second, the provenance pins become EOL-agnostic fingerprints: md5 over CRLF-to-LF normalized bytes on both comparison layers (the `.gitattributes` law), the pin anchoring content identity rather than line endings; the two snapshot copies and the seed pin re-sign in the same commit per the sync discipline, verified by `python -I tests/t_engines_seeds.py` (jargon segment) before push. Doc faces this round: the EOL-agnostic fingerprinting section in `docs/pin-provenance-v2.md`, the normalization wording in `seeds/jargon/SPEC.md`, the R15 sentence, and this line.

## 6. Lineage

- Host-mismatch era: eleven root causes (code page, autocrlf, HOME override, isolated mode, shell escaping, execv argv, taskpolicy, `.git` in write-sweep, MSYS path folding, grandchild process reaping): see the November 16, 2026 deployment/RSI assessment, section 2.
- Recursive era: this whitepaper. Update rule: every new class lands here AND as a row in `docs/ci-triage-table.json` AND as an experience card in the cross-line area (`exp/INDEX.md`) in the same round (the replication obligation).
- **PR #10 chain (November 17, 2026)**: R13 sub-face 2 (the PR LIST endpoint never computes `mergeable`: the leg re-reads the single PR before holding) + sub-face 3 (the PR head BRANCH was deleted while the PR stayed open: route 422; the leg restores the head ref from the head commit before dispatching) → **PR #10 MERGED autonomously (merge commit e73a34a9, hosted-jobs gate)** with the local-face checkout red tolerated by design (the bridge lacked the PR head objects) → the durable cure: the JOB_STARTED mirror-sync hook installed on the rocqwash runner (dev-tree = bridge target; explicit capital-GitHub upstream; dirty-tree-guarded main ff; pull-refs backfill; sparse neutralization; printf-style .env writers consume backslash escapes).
- **Fingerprint-skip gate + standing cron (November 17, 2026, desk order)**: hosted suite faces + mac advisory carry a fingerprint-keyed verdict cache (whole tree minus the pure-prose allowlist; actions/cache@v6; exact key per face label) - modes FULL / ANCHORS (anchor tier: frozen8 + station + registry faces, the doc-input faces); reruns and dispatches always run FULL; the canonical local face never skips (R12). The standing self-evolution cron (17 */4 * * *) runs one deterministic mechanical round per tick with zero model cost, no-ops cleanly at census zero, and dispatches its own CI judge (R13 sub-face 4 generalization). The stale merged branch (`fix/pr3-followups-20261115`) was deleted after squash-content equivalence; an uncancellable leftover route (cancel 409 on queued zero-job runs) was retired by deleting its already-merged branch ref.

- **ANCHORS-mode live validation (November 19, 2026, outcome + gate repair)**: the first pure-prose push since the gate landed did NOT hit the ANCHORS branch - both hosted faces computed a different verdict-cache key for a whitepaper-only diff, proving the hashFiles negation patterns (`'!path'`) are inert on the runner and the ANCHORS branch was unreachable by construction (every push forced FULL; the skip half of the gate never executed once since it landed). Repair (landed in the same commit as this paragraph): the fingerprint gate now hashes `git ls-tree -r HEAD` minus the pure-prose allowlist (grep -v filter + `git hash-object --stdin`) - committed-content-addressed, EOL-immune, portable across hosted Linux/Windows/macOS. Verified locally against real commit pairs: a whitepaper-only diff leaves the fingerprint unchanged while code and data (ledger) diffs change it. The next pure-prose push is the live validation of the repaired gate; its run verdict is recorded post-run.

- **ANCHORS-mode post-repair live validation (November 19, 2026)**: pure-prose push on the repaired gate - the verdict-cache key must be unchanged from the last green FULL run, so this push event must take the ANCHORS branch (verdict-cache hit -> anchor tier: frozen8 + station + registry faces) on both hosted faces. Verdict recorded post-run.
- **R15/R16 integration (November 19, 2026)**: both November 19, 2026 classes landed in this taxonomy, the triage table (rows 15-16) and the cross-line experience card in the same round per the replication obligation; R15's re-sign ran through the IN-SYNC plan verdict (b3cbcf0), R16's standing FP form is the ls-tree construction (74cc082) live-validated by cdb0ae9 (ANCHORS/ANCHORS, run 44374294488).
