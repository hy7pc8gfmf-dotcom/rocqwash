# workflow-integration whitepaper v1.0: the interface contract for embedding the rocqwash tools into external workflow engines (issued November 11, 2026) / `工作流配合白皮书 v1.0`

> Purpose.  The normative interface face of rocqwash v37 (commit `41e74b0`) for cooperating with external workflow engines (dynamic workflow and similar) that provision sanitization, shape normalization, troubleshooting and blockage clearing in real time and dynamically. Every fact is taken from the tools' docstrings and `--help` output (captured per tool on November 11, 2026 · read before write · zero invented APIs); the document is the same-source complement of the `README-cw.md` "workflow cooperation interface" section (README-cw.md:71-140); the quick reference lives there, the mechanics here. The per-command expansions of the three canonical embed blocks are the three `examples/workflows/` files: `backend-sentinel.md` / `step-pushci.md` / `loop-unclog.md` (referenced in §2). Scope statement: this whitepaper covers the workflow-cooperation face only (the three v37 tools `sentinel` / `wash-shape` / `unclog`, plus the v36 `pushci` and the v37 interface disciplines); `cw.sh` / `tests/run_tests.sh` / the README family belong to the integration agent, and this document does not change one character of them.
> Interface.  Document face only; no runtime interface. Sections: §1 the five interface disciplines (a workflow embeds the tools by them, without knowing each tool's internals); §2 references to the three ready-made embed blocks under `examples/workflows/`; §3 the background-task and main-session yield mode; §4 the two-gate statement alongside `push_gate`'s four push-window criteria; Appendix A the real-run evidence of this whitepaper; Appendix B the change history and ownership. Audience: agents and people writing workflow scripts (sub-agent orchestration / background bash tasks). After reading, a reader can: ① embed the tools into any orchestration engine per the five disciplines of §1; ② take a ready-made embed block per §2; ③ set up the background-watcher yield relationship of §3; ④ distinguish the `pushci` preflight check from the `push_gate` push-window criteria; the two gates of §4. The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Cited sources only; no runtime dependency of this document face itself: the tools' docstrings and `--help` output at the rocqwash v37 state (commit `41e74b0`); `README-cw.md`; `CONTRIBUTING.md` (§1.5, §2, §5); `certify/push_gate.py`; `tools/pushci.py`; `tools/cw_sentinel.py`; `tools/unclog.py`; `tools/wash_shape.py`; the three workflow-block files under `examples/workflows/`. All line-number citations are anchored to the v37 `41e74b0` commit state (see Appendix B).
> Evidence.  The §2 samples and the Appendix A evidence table are real-run records of the November 11, 2026 casting session (all tmp fixtures · zero repository writes), not hand-written; every flag cited in a block was reconciled against the tools' `--help` output (all present · zero invented); the items not actually run; the `pushci` real-push stage and the `probe_engine` real-compilation verification; are declared as such in Appendix A.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged (§1 discipline ②, codes 0/1/2/9).

---

## §1 The five interface disciplines (shared by the three v37 tools · a workflow embeds by them · no need to know each tool's internals)

Normative source of the disciplines: `README-cw.md:71-140` (quick reference) plus each tool's docstring (mechanics). The mechanics follow, item by item.

### Discipline ①  JSON-in/JSON-out · designated schema · determinism

- Output is always written with `--json OUT`, with a designated schema: `rocqwash-sentinel/1` (overwritten every round), `rocqwash-shape/1`, `rocqwash-unclog/1`, `rocqwash-pushci/1`; in loop state the event stream `--events FILE` is line-by-line JSONL (sentinel line schema `rocqwash-sentinel-event/1` · the `seq` key is monotonic within the event stream, so a consumer sorting by `seq` restores the global order).
- Determinism: `--json` output is persisted with `sort_keys` (README-cw.md:82-86) · reruns on the same input are byte-identical; reports carry zero wall-clock fields and zero absolute paths (paths are emitted as base names only · the "output" section of the unclog docstring; with `--sleep-scale 0` the event-line `ts` field is turned off and annotated as `note:"ts=off…"` (cw_sentinel.py:301-306)).
- Event-stream writing: the sentinel `--emit` is a JSONL append plus per-line flush+fsync plus a stdout mirror (cw_sentinel.py:31, 310-321); the unclog `--events` file is opened for writing as soon as the process starts (`io.open(…, "w")` · unclog.py:733; one stream per closed loop); the wash-shape `--events` is a loop-append ledger (`--help`: "stdout always streams · this flag additionally persists to disk").

### Discipline ②  Exit codes 0/1/2/9 (a failing result is data, not a tool failure · loud stdout)

| Code | sentinel | wash-shape | unclog | pushci (same shape in v36) |
|----|----------|------------|--------|--------------------|
| 0 | inspection round completed (CI failing / blockage is event data) | clean / shaped | unclogged | success / dry-run |
| 1 |; (failing states travel in the event stream) | partial / plan-miss (the sanitization did not finish · loud output) | wall / rounds-exhausted (the honest wall · no forced results) | heal-exhausted / unstable / toolchain |
| 2 | usage error (missing mode / all three sources missing / malformed repo) | usage error / frozen-face refusal on a failing check / exit outside the engine shape | usage error / malformed injection scenario | fix-content / gate4-block / usage error |
| 9 | signal source unreachable (HTTP 4xx · injector coverage miss · subprocess rc≠0) | path missing | fail-loud (path missing / tool failure / frozen face unobtainable) | target missing (repo / remote / branch / PR / netrc / API unreachable · watch round cap reached) |

(Normative source: README-cw.md:94-101 plus pushci.py:91-93.) Key point: **a failing result never enters the exit code**; the watcher's failing states travel in the event stream, and unclog's failing states in the report's failing records; the exit code states only the tool face and the terminal outcome. Workflow branching is therefore two-level: first branch on the exit code for the tool face (2 = fix the call · 9 = supply the missing target), then read the JSON and branch on verdict/kind for the data face (each of the three §2 blocks carries its own branch table).

### Discipline ③  The `--once`/`--loop` dual mode

- `--once` (the default for sentinel/unclog) runs one round, emits the output and exits; for inline use inside a workflow step; wash-shape is once by default (the plan stage writes nothing to disk).
- `--loop --interval S` is the resident watcher state; for workflow background bash tasks (the nohup form is in §3). Round caps: sentinel `--max-rounds N` (0 = unlimited), wash-shape `--max-rounds N`, unclog `--loop-max N` (a count of rounds · after a non-terminal rounds-exhausted the tool rests for `--interval` and starts the next round; unclogged / wall are terminal and stop immediately).
- `--sleep-scale F` multiplies every sleep by F (0 = zero real sleeping plus the event `ts` turned off); for offline drills and determinism pinning; never given in the production shape.

### Discipline ④  Offline testability via `--injector` (zero real network, zero real compilation in drills)

| Tool | injector shape | uncovered semantics |
|----|-------------|-----------|
| sentinel | canned GitHub API table (`rocqwash-sentinel-injector/1` · `{"responses":[{url_contains,status,body}…]}` · consumed in order, first match wins, reusable cyclically; must be given together with `--watch-repo`) | fail-loud 9 · never silently falls through to the real network |
| wash-shape | canned subprocess-call layer `{engine key:{rc,stdout,report}}` (key set: gate4/scan_v4/cure/sweep/registry_union/frozen8) | fail-loud |
| unclog | `DIR/scenario.json` = `{"probe":[ledger…],"resprobe":[ledger…]}` · the two kinds of probe_engine calls are consumed strictly in order; chain_graph/cure_applier/scan_v4_token/frozen8 still run for real under injection (real orchestration, not a puppet) | exhausted / missing column / malformed shape fail loud 2 |
| pushci | `--injector DIR` plus `--git-caller FILE` must be given as a pair (one side alone = usage error 2 · prevents a silent real push from an injector without canned git) | mismatch fails loud |

(Normative source: the "offline testability" section of each tool's docstring.) Workflow self-tests and CI drills always use the injection shape plus `--sleep-scale 0`: the three tools' `--selftest` and the suite hookup files (`tests/test_cw_sentinel.py` / `test_wash_shape.py` / `test_unclog.py` / `test_pushci.py` · the four `t_*` sections of `tests/run_tests.sh`) all run with zero real network and zero real compilation; this discipline is its own evidence.

### Discipline ⑤  Zero new engines in orchestration

The three tools plus pushci call the existing engines directly by subprocess internally (README-cw.md:137-140): sentinel's classification is fully delegated to `ci_triage` and chain-root extraction fully to `chain_graph`; all five wash engines of wash-shape run by subprocess (gate4/scan_v4/cure_applier/comment_sweep/registry_union); all five unclog steps run by subprocess (probe_engine/chain_graph/cure_applier/scan_v4_token/frozen8); pushci orchestrates the four v35 tools (doctor/net_probe/ci_triage with gate4 as guard · pushci.py:5-7). Corollary (two constraints on the workflow author):

- **Zero new engines in orchestration is bidirectional**; the workflow side likewise writes no new logic for "judge the failing state once more / pick the root once more": call the tool and read its JSON. The tools have already turned their criteria into code (the preflight check / the four criteria / the honest wall).
- Real compilation always passes through the cpu_guard temperature-control wrapper (CONTRIBUTING §5): the watcher itself does zero compilation and zero networking (the "orchestration law" section of the cw_sentinel docstring); what needs real compilation is the probe_engine verification; unclog passes it through with `--guard PATH --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N` (present in `--help`).

### Supplement: python3 pure stdlib + fail-loud + zero hardcoded paths

The three tools are pure-standard-library with zero third-party dependencies (the same law as CONTRIBUTING §2); fail-loud forbids silent degradation (source unreachable 9 · injector coverage miss 9 · subprocess rc≠0 9; the watcher refuses to run in a degraded state, the source hard-error note at cw_sentinel.py:727); every path is a parameter with zero hardcoded absolute paths (tool paths derive from the repository this file lives in · the `pushci` `TOOLS_DIR` precedent). `cw.sh` is a 1:1 pass-through entry (exec · rewrites neither arguments nor exit codes · README-cw.md:9-11); in a workflow, `bash cw.sh <tool>` and a direct call `python3 tools/<tool>.py` are semantically identical, and every embed block in this document uses the cw.sh form (one fewer path coupling).

---

## §2 References to the three embed blocks (examples/workflows/)

The three canonical embed blocks are the per-command expansions of the `README-cw.md` "workflow cooperation interface" ⑥ (README-cw.md:121-135). Each file contains: a command block executable by whole-block copy, real JSONL/JSON output samples, an exit-code branch table, and pseudocode comments corresponding to the dynamic-workflow embed form. **The samples were all produced by the actual runs of the November 11, 2026 tmp injection drill, not hand-written** (each file's "honesty note" section self-reports its measured shape).

| Block | File | Tool | Scenario | Disciplines exercised |
|---|---|---|---|---|
| ① background watcher | `examples/workflows/backend-sentinel.md` | `cw.sh sentinel` (`tools/cw_sentinel.py`) | nohup-resident watch of the three signal sources → JSONL event stream plus consumer samples with grep/python3 | ③ loop background form · ① event stream · ② the 0/2/9 table |
| ② single-step CI push | `examples/workflows/step-pushci.md` | `cw.sh pushci` (`tools/pushci.py`) | `--dry-run` first for human review → the real push → seven-state verdict branching | ② the 0/1/2/9 book · ④ injector+git-caller pair |
| ③ blockage-record clearing loop | `examples/workflows/loop-unclog.md` | `cw.sh unclog` (`tools/unclog.py`) | dry run (zero writes) → human review of the plan → `--apply` → re-check by the three criteria · honest-wall seven-cause routing | ② the three-state book · ③/④ injection form · ⑤ orchestration |

wash-shape (`cw.sh wash_shape` → `tools/wash_shape.py` · the canonical five-wash pipeline) has no dedicated embed block: its two-stage form (plan writes nothing to disk by default → human review → `--apply` executes and re-runs the washes for verification) is isomorphic to block ③; read the three-line embed at README-cw.md:132-134 and the "two-stage form" section of that tool's docstring, and assemble it yourself following block ③'s human-review-apply skeleton; the normative command line for its loop watcher state is at README-cw.md:112-114.

---

## §3 The background-task and main-session yield mode

"Yield" means: after the workflow's main session (or main agent) hands the resident watcher to a background bash task, it does not compete with the watcher for writes to the same working set and does not poll the watcher process; it reads the watcher's self-reported products only at checkpoints. Five mechanisms guarantee this mode (all anchored to the tools' measured behavior):

1. **Self-held products**: all watcher output travels explicit parameter paths; `--emit` (the event stream), `--json` (the per-round report), `--state-file` (seen idempotency), and for unclog additionally `--workdir` (per-round ledger/report artifacts · with the default mkdtemp, stdout loudly reports the path). If the background task redirects stdout away, no evidence is lost: an event line is mirrored to stdout first, then appended to disk (cw_sentinel.py:311-321); `--emit` and the report are self-sufficient.
2. **Disjoint write domains**: a tool writes only the output paths and workdir it was explicitly given; unclog writes nothing inside `--world` (the "world discipline" docstring section); wash-shape auto-excludes the frozen faces and `更新账.md`, and an explicitly named frozen face is refused with a failing exit 2 (the "scope and no-touch faces" docstring section). While the main session is yielding, it keeps editing its own files as usual and cannot step on the watcher's write set; the watcher does not cross the boundary either.
3. **Bounded yielding**: a watcher is not an indefinite hang; the `--max-rounds` / `--loop-max` round caps let it stop itself; unclog stops and exits on a terminal verdict (unclogged / wall) (the "`--once`/`--loop` dual mode" docstring section); on a fail-loud 9 the watcher stops at once instead of running in a degraded state (cw_sentinel.py:727). The main session's yield means "wait until the checkpoint / the terminal outcome", not "hang forever".
4. **Checkpoint read-back**: the main session reads the event stream at phase checkpoints; the grep target `'"kind": "ci-red"'` relies on the event line's sort_keys byte order (discipline ①), and structured consumers sort by `seq` to restore the global order (with `--emit` in place, `seq` is based on the file's existing line count and continues numbering across processes, cw_sentinel.py:294-298). Samples and the canonical consumer form: `backend-sentinel.md` §2-3.
5. **Real compilation belongs to the guard**: while yielding, the watcher only emits signals and does no heavy work; the real heavy work (real probe compilation) happens inside block ③'s closed loop and always passes through the cpu_guard wrapper (unclog `--guard*` pass-through · discipline ⑤). The temperature-control invariant is in CONTRIBUTING §5.

The three canonical background-watcher command lines (one each for sentinel/wash-shape/unclog) are designated at README-cw.md:105-118; block ① gives their copyable versions plus the stopping form and the drill-form note.

**Anti-patterns (forbidden)**: the main session blocking on `tail -f` while waiting for events (use checkpoint read-back instead); hanging heavy work off the watcher's `--on-red` (on-red is a bypass action · 60s timeout cap · it does not change the watcher's exit code; heavy work belongs to the sub-agent step after the workflow has read the events); multiple watchers writing the same `--state-file` / `--emit` (both seq continuation and seen idempotency assume a "single writer").

---

## §4 The two-gate statement beside push_gate's four push-window criteria

**Two gates, each judging its own criteria, never a substitute for the other** (same wording at README-cw.md:57-60):

| | Gate A: the pushci preflight check (inside the preflight stage) | Gate B: push_gate's four push-window criteria (the window subcommand) |
|---|---|---|
| Tool | `cw.sh pushci` (`tools/pushci.py`, stage 1 of the five-stage pipeline) | `python3 certify/push_gate.py window` (`certify/push_gate.py` · the same file as the rocqwash-union-manifest) |
| What it judges | **whether the environment can initiate**: ① toolchain doctor verdict=healthy; ② the net-probe two-probe stability window STABLE; (optional ③ `--pre-scan-gate4` header pre-scan FAIL=0) | **timing and credentials** (carrying the effort's push-window invariant · push_gate.py:8-10 "the four push-window criteria"): c1 ci-idle (zero in-flight CI runs · evidence via `--runs-json` or the `--ci-capped-min` timeline); c2 local≥remote (behind==0); c3 fetch-clean (ls-remote double read returning the same sha, plus the remote sha is an ancestor of local); c4 cert-green (`tests/run_tests.sh` rc==0 · optional zero drift of the frozen faces) |
| Exit codes | follows the five-stage verdict book (pushci.py:91-93 · the pipeline stops at the stage where the check fails) | window: 0=OPEN / 1=CLOSED (including NOT-RUN) / 2=usage error / 9=path missing (push_gate.py:65) |
| Missing-evidence semantics | both gate tools render their own verdict (doctor/probe produce the verdict) | **NOT-RUN = window closed · absent corroboration never counts as passing** (the honesty law · push_gate.py:29); fail-closed |
| Coverage | excludes the suite-passing / behind==0 / CI-in-flight judgments (README-cw.md:58-60 states this explicitly as "not in this book") | excludes the network stability-window / toolchain health judgments (c1 judges only CI in flight · a missing evidence source means NOT-RUN) |

**Canonical serial order** (the pre-gate of workflow block ②):

```bash
# Gate B judges the window first (while the window is closed, Gate A does not run — saves one initiation attempt)
python3 certify/push_gate.py window --repo . --branch feature/x \
  --runs-json runs.json --json window.json          # continue only on 0=OPEN
# Gate A then runs the pipeline (§2 block ②: --dry-run first → the real push → verdict branching)
bash cw.sh pushci --repo-path . --branch feature/x \
  --pre-scan-gate4 --json pushci-report.json
```

Three key points:

1. **They do not re-check each other**: pushci does not re-run the four criteria, and push_gate does not re-run doctor/net-probe; judging one thing twice is waste, missing one gate is a hole. A workflow that needs both gates (a repository whose push-window discipline is on the books) runs them serially in the order above, each judging its own criteria.
2. **This tool only judges the window and never pushes**: `push_gate.py window` is read-only throughout (fetch/ls-remote are both read-only remote operations · the "write-domain declaration" of the push_gate.py docstring); the push action belongs to the caller; which is why the two gates chain naturally: Gate B returns OPEN, Gate A returns success, and each keeps its own record.
3. **The legacy chain stays on the books**: the manual legacy chain (the four criteria plus a bare `git push` · README-cw.md:57) is legal but is not in the workflow embed-block book; workflows always use the pushci form (the verdict book supports branching · the heal automatic recovery is bounded).

---

## Appendix A  Real-run evidence of this whitepaper (executed in the casting agent's actual runs of November 11, 2026 · all tmp · zero repository writes)

| Check | Command (wrapped by cpu_guard) | Measured |
|---|---|---|
| `--help` authoritative flags of the three tools | `python3 tools/cw_sentinel.py --help` / `tools/unclog.py --help` / `tools/wash_shape.py --help` / `tools/pushci.py --help` | all rc 0 · every flag recorded |
| three-source real run of the watcher | `cw_sentinel.py --once --watch-repo org/repo --branch main --injector … --emit … --json … --sleep-scale 0` (ci-red) plus `--once --watch-ledgers … --watch-buildlog … --sleep-scale 0` (blocking + build-signal) | rc 0 · event-line/report samples entered into block ① |
| the whole background-watcher block | `nohup bash cw.sh sentinel --loop … --max-rounds 2 --sleep-scale 0 --injector … &` (tmp drill form) | self-stopped after 2 rounds · 2 event lines · `grep -c '"kind": "ci-red"'` → 1 (rc 0) |
| pushci dry run | `pushci.py --repo-path . --branch main --dry-run --json …` | rc 0 · plan text plus report sample entered into block ② |
| unclog dry run | `unclog.py --src … --world … --candidates … --injector … --json …` (tmp fixture) | rc 0 · cure.stage=dry-run · the root file's md5 identical (proof of zero writes) |
| unclog apply | same plus `--apply` | rc 0 · stage=applied · rescan.residual_zero=true · resprobe.rc_ok=true · verdict unclogged |
| the unclog honest wall | `unclog.py --src … --chain-ledgers base.json --json …` (Y self-unwashable) | rc 1 · wall record sample entered into block ③ |
| flag reconciliation | each block's cited flags grepped against each tool's `--help` output | see the delivery notes (all present · zero invented) |

Not actually run (declared as such): the pushci real-push stage (needs real remote credentials · user-side); the probe_engine real-compilation verification (needs the rocq world base · user-side · real compilation always passes through cpu_guard). Both command shapes are given with `--help`/docstrings as the normative source; their runtime behavior was not verified by this agent's own runs.

## Appendix B  Change history and ownership

- v1.0 · November 11, 2026: initial version (§1-§4 plus the appendices). Written by the examples embed-block casting agent (the three workflow embed blocks plus this whitepaper). `cw.sh` / `tests/run_tests.sh` / the README family belong to the integration agent; the frozen eight / quad8 / `更新账.md` were under a no-touch rule and were not touched (this agent's session wrote zero of the above faces · the full write set is in the file list).
- Line-number citations in this document are anchored to the v37 **`41e74b0` commit state** (multiple agents develop concurrently · working-tree line numbers drift; when they drift, re-anchor by section name plus the tool's docstring).
- When upstream drifts, revise this document against the tools' docstrings plus `--help` as the normative source; a disagreement between this document and a tool counts as a bug (the same law as CONTRIBUTING §1.5).

(English abstract) This whitepaper is the normative interface contract for
embedding rocqwash v37 tools into external workflow engines. §1 five interface
disciplines (named JSON schemas + JSONL event streams with sort_keys determinism;
exit codes 0/1/2/9 where red is data not tool failure; --once/--loop dual mode;
--injector offline canned testing with fail-loud coverage; orchestration of
existing engines via subprocess; zero new engines). §2 references the three
canonical workflow blocks under `examples/workflows/` (background sentinel /
single-step push-CI / unclogging closed loop), each with copy-paste command
blocks, real captured outputs, exit-code branch tables and dynamic-workflow
pseudocode. §3 defines the background-task yield mode: sentinels own their
declared output paths, terminate on round caps or terminal verdicts, and the main
session reads the event stream at checkpoints only. §4 states the two-gate
doctrine: pushci's preflight emission gate (toolchain + net stable-window ± gate4
pre-scan) and push_gate's four push-window criteria (ci-idle / local≥remote /
fetch-clean / cert-green, NOT-RUN = closed) are independent gates to be run in
series, never substitutes for each other.
