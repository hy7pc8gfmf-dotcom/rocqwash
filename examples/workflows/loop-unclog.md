# loop-unclog.md: workflow block ③: the unclogging closed loop (dry run → human review → --apply → re-verify · honest-wall branch) / `工作流嵌段③：堵账疏通闭环（dry run→人审→--apply→复核·诚实墙分支）`

> Purpose.  The fully copyable form of the `README-cw.md` unclog tool row (README-cw.md:71), expanded into whole-block copyable commands + real output samples + an exit-code branch table (honest-wall branch) + dynamic-workflow embed pseudocode; one of the three canonical workflow-block samples of rocqwash v37. Normative tool face: the `tools/unclog.py` docstring (manual five steps closed into a self-driving loop: probe collection → chain_graph chain-root pick → cure_applier apply → rescan/resprobe re-check → verdict; schema `rocqwash-unclog/1`; closed-loop verdicts `unclogged|wall|rounds-exhausted`; unclog.py:205-216) and `--help`.
> Interface.  Document face. It documents `cw.sh unclog` (`tools/unclog.py`); the tool docstring and `--help` are normative. Citations bind to the HEAD d3c84e6 commit state (concurrent multi-agent development · working-tree line numbers drift). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Dependencies.  `tools/unclog.py` routed through `cw.sh`; its engines always run as subprocesses (`wash/probe_engine.py` probes, `tools/chain_graph.py` chain roots, `wash/cure_applier.py` cures against the canonical pack `wash/cure_pack.json` (v1.4.1 at drill time), the scan_v4_token rescan, the `certify/frozen8.py` roster fetch); `README-cw.md` "workflow-integration interface" (README-cw.md:159-199) for the five joint disciplines. The drill form in this file needs no rocq toolchain (injector-canned probes, zero real compiles); no runtime dependency of this document face itself.
> Evidence.  Every output sample in §1/§3/§4 is a real-run record of the November 19, 2026 tmp injection drill of the current tool at HEAD d3c84e6 (fixture data · zero real network, zero real compilation; probe/resprobe canned, chain/cure/scan/frozen8 ran for real), not hand-written; each sample states its measured rc. The predecessor captures of November 11, 2026 (v37, commit 41e74b0; stdout labels then Chinese, frozen roster then 8 entries) are archived verbatim in the sibling `.zh.md`; the current tool emits the English wording shown. Tmp path prefixes in the samples are abbreviated to `…` (machine-local tmp dirs; the report itself carries basenames only; unclog.py docstring "report face"). No real compilation probe was run for this document (the real-probe form needs the rocq world base); the offline injection form is what was measured.
> Exit-codes.  Not applicable to a document face; the documented closed loop keeps its implemented exit-code semantics (§4: 0 unclogged / 1 wall or rounds-exhausted / 2 usage or scenario shape / 9 fail-loud) unchanged.
>
> Non-negotiable constraints (read before use):
> - **--apply defaults to off = dry run everywhere, zero disk writes** (single switch · `--yes` is not needed; unclog.py docstring "Safety rules" section): the apply lands only on **chain-root files** (`<src>/<root>.v`; outside the root pick there is no cure_applier call path · structurally guaranteed against non-root files), and only through the canonical cure pack (no free-form edits).
> - **the honest wall is never force-fitted**; when every top-list entry has `self.washable=false`, or every washable root dead-ends → `verdict=wall exit 1`; the wall record lists a non-actionable reason per root, zero applies, nothing forced (unclog.py:90).
> - **a failing result is data, not a tool failure**; a probe rc-1 candidate is produced data; the exit code states only the tool face and the terminal verdict (0=unclogged · 1=wall/rounds-exhausted · 2=usage/scenario-shape error · 9=fail-loud).
> - **world-generation discipline**; the tool never writes `--world`; whether a re-check failure clears after a cure depends on the world's `.vo` foundation turning over a generation (the caller seeds generations per the wash/world_hook.py certification discipline); the tool only records what it observed (unclog.py docstring "World discipline" section).

## 1. Step 1: dry run (zero disk writes by default · produces the plan record)

```bash
# ── loop-unclog block · step 1: dry run (run at the rocqwash repository root) ──────
SRC=src/                          # source-tree root (the root file <root>.v is taken from here)
WORLD=world/                      # world directory (probe compiles here · the caller seeds the .vo base)
CANDS=cands.tsv                   # candidate TSV (header row `件名\tmd5` · probe_engine's required form)

bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates "$CANDS" \
  --json unclog-dry.json --events unclog-dry-events.jsonl
echo "UNCLOG_DRY_RC=$?"           # 0=failure account already clear (no apply needed) · 1=wall/rounds-exhausted · read the record and decide
```

> The dry-run block carries no `--apply`; that is the **structural default**,
> not an omission (see the first constraint above).

**Measured sample** (real tmp-injection drill of November 19, 2026 at the
current tool face, HEAD d3c84e6: `--src … --world … --candidates …
--injector inj/ --json … --events …`, rc=0; verbatim stdout progress, tmp
path prefixes abbreviated to `…`):

```text
workdir -> …/T/rocqwash_unclog_o6qm9fq0
candidate face: --candidates …/cands.tsv
injector: …/inj (probe canned 2 shots; resprobe canned 1)
frozen roster: 10 entries (fetched live via certify/frozen8.py --ledger; precheck rejection)
[round 1/5] collect: probe failing 1: B
chain_top: A(n=1,washable=True)
RECHECK A rescan_station=0 resprobe_rc=0
[round 1/5] root=A cures=1
[round 2/5] collect: probe failing 0: -
[round 2/5] root=- cures=0 (red empty)
report -> …/unclog-dry.json
VERDICT: unclogged (exit 0)
```

Corresponding report round record (measured excerpt · rocqwash-unclog/1 ·
cure.stage=dry-run = nothing applied; the `args`, `probe_summary`, `log`, and
timing fields are omitted here for width):

```json
{
 "mode": { "apply": false, "injector": true, "loop": false, "source": "tsv" },
 "rounds": [ {
   "chain_top": [ { "dependents": ["B"], "lib": "A", "n": 1,
                    "self": { "probed": true, "rc": 0,
                              "verdict": "RC0", "washable": true } } ],
   "cure": { "md5_after": "69cccc393d849a7c96a87565b6dc72c2",
             "md5_before": "d47bbca3db58dbfeb55c4ad0cb47e950",
             "on_disk_md5_match": true,
             "patterns": { "cure13_natle_premise_lift": 1 },
             "rc": 0, "stage": "dry-run", "total_matches": 1 },
   "cures_applied": 0, "cures_planned": 1, "root": "A", "root_file": "A.v",
   "rescan": { "ids": "S", "rc": 0, "residual_zero": true, "station_count": 0 },
   "resprobe": { "md5_match": null, "n_records": 1, "rc": 0, "rc_ok": true },
   "round": 1 } ],
 "final": { "cures_applied_total": 0, "cures_planned_total": 1,
            "red_files": [], "rounds_run": 2, "verdict": "unclogged",
            "wall_count": 0 },
 "schema": "rocqwash-unclog/1",
 "verdict": "unclogged",
 "wall": {}
}
```

**Zero-write proof** (same run): after the dry run the root file's md5 still
equals `cure.md5_before` (`d47bbca3db58dbfeb55c4ad0cb47e950`); the file was
untouched.

## 2. Step 2: human review of the plan (read the dry-run record · no tool run)

Three review questions (all answered from the report, no new engine runs):

| Where to read | What to judge |
|---|---|
| `rounds[].chain_top[].self.washable` | the chain roots' washability verdicts (chain_graph wording); all false → expect a wall |
| `rounds[].cure.patterns` | the canonical pack's planned pattern names and counts (e.g. `cure13_natle_premise_lift: 1`); a wrong plan → do not open `--apply` |
| `rounds[].cure.stage` | `dry-run` = nothing applied; the value flips to `applied` only after `--apply` |

## 3. Step 3: --apply apply + Step 4 re-verify (one command produces the full record)

```bash
# ── loop-unclog block · steps 3-4: apply + re-verify (only after human review passes) ──
bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates "$CANDS" \
  --apply --json unclog-apply.json --events unclog-apply-events.jsonl
echo "UNCLOG_APPLY_RC=$?"
```

**Measured sample** (same-day tmp drill of November 19, 2026 · rc=0; verbatim
stdout of the apply and the re-check, tmp path prefixes abbreviated to `…`):

```text
workdir -> …/T/rocqwash_unclog_n6hrxdo_
candidate face: --candidates …/cands.tsv
injector: …/inj (probe canned 2 shots; resprobe canned 1)
frozen roster: 10 entries (fetched live via certify/frozen8.py --ledger; precheck rejection)
[round 1/5] collect: probe failing 1: B
chain_top: A(n=1,washable=True)
APPLIED A cures=1 md5_after=69cccc393d849a7c96a87565b6dc72c2 on_disk_match=True
RECHECK A rescan_station=0 resprobe_rc=0
[round 1/5] root=A cures=1
[round 2/5] collect: probe failing 0: -
[round 2/5] root=- cures=0 (red empty)
report -> …/unclog-apply.json
VERDICT: unclogged (exit 0)
```

Re-check three criteria (inside the report · the same-source engines re-run
after the apply):

- `rounds[].rescan.residual_zero == true` (scan_v4_token re-scans the treated
  file; the cured-token residual should be zero; measured `station_count: 0`
  in the sample);
- `rounds[].resprobe.rc_ok == true` (probe_engine re-probes the treated file;
  rc should be 0; measured `rc: 0` in the sample);
- `final.red_files == []` and `final.cures_applied_total == 1` (an empty
  failure account = blockages cleared).

**Honest form when the re-check fails**: when `resprobe.rc_ok=false`, stdout
loudly appends the suffix `resprobe-rc=… (expected 0, not reached; recorded as
observed)` (unclog.py:902-904); the tool never dresses "applied" up as
"cleared"; whether the failure account is truly cleared is decided by
world-generation turnover (fourth constraint above).

## 4. Exit-code branch table (verdict states · honest-wall branch)

| Exit code | verdict | Meaning (unclog --help/docstring wording) | Workflow action |
|---|---|---|---|
| 0 | `unclogged` | failure account empty (blockages cleared · or none to begin with) | close out; read final.cures_*_total into the record |
| 1 | `wall` | **honest wall**: every top-list entry unwashable, or every washable root dead-ends → zero applies, nothing forced · the wall record lists a reason per root (wall field) | human review routes on the wall record: see the wall-reason table below |
| 1 | `rounds-exhausted` | `--rounds` (default 5) exhausted with the failure account uncleared · per-round records + the final judging probe on file | read the rounds[] per-round records · a human decides: more rounds / world turnover / manual repair |
| 2 | (no verdict) | usage error / injection-scenario shape error (e.g. canned series exhausted / column missing / shape broken; consumed strictly in order, fail-loud) | fix the command line or complete the canned scenario |
| 9 | (no verdict) | fail-loud (missing path / engine subprocess non-zero non-data exit / frozen roster unavailable / whole-tree enumeration found zero candidates) | supply the path or repair the tool face by hand |

**Wall-reason routing table** (wall field `reason` values · normative at
unclog.py:90 and the wall_add call sites):

| reason | Meaning | Routed to |
|---|---|---|
| `unprobed` | a top-list root never entered the candidate set (its root file was never probed) | human adds it as a candidate and re-runs |
| `self-unwashable` | mid-chain ring · the root file is itself blocked (why the root must be treated first) | human (the tool never force-fits) |
| `no-chain-root` | no failing file in the account is a missing-library chain root (generation-gap/tool-cause failure · the wall never goes silent) | human triage (against the ci_triage classification spectrum) |
| `root-file-missing` | the chain-root file is missing (the library a failing file lacks has no corresponding source file) | human supplies the file |
| `cure-miss` | the canonical pack's dry run offers zero plan (total_matches=0 · nothing fabricated) | human extends or rewrites the pack |
| `frozen-in-service` | the root name/root file collides with the frozen roster → loud precheck rejection | **frozen files are untouchable**; take a different path |
| `exclusive-group-conflict` | variants require a human `--only` choice (no automatic substitution) | a human picks one, then rerun |
| `idempotence-fail` | the apply-time idempotence assertion refused the write (cure_applier refused · file untouched) | human checks for duplicate patterns |

**Wall-record measured sample** (real tmp drill of November 19, 2026: the
base.json ledger holds Y failing with rc 1 RED-OTHER and C1 missing Y → chain
root Y is self-unwashable; rc=1):

```text
candidate face: --chain-ledgers …/base.json (merge mode; no per-round whole re-probe)
frozen roster: 10 entries (fetched live via certify/frozen8.py --ledger; precheck rejection)
[round 1/5] collect: merge failing 2: C1,Y
WALL: Y — self-unwashable (the root file is itself blocked rc=1 verdict=RED-OTHER (a mid-chain ring; cure the root's own cause first))
[round 1/5] root=- cures=0 (wall)
VERDICT: wall (exit 1)
```

```json
{ "final": { "cures_applied_total": 0, "cures_planned_total": 0,
             "red_files": ["C1", "Y"], "rounds_run": 1,
             "verdict": "wall", "wall_count": 1 },
  "rounds": [ { "chain_top": [ { "dependents": ["C1"], "lib": "Y", "n": 1,
                                 "self": { "probed": true, "rc": 1,
                                           "verdict": "RED-OTHER",
                                           "washable": false } } ],
                "cure": null, "cures_applied": 0, "cures_planned": 0,
                "root": null, "round": 1 } ],
  "schema": "rocqwash-unclog/1", "verdict": "wall",
  "wall": { "Y": { "detail": "the root file is itself blocked rc=1 verdict=RED-OTHER (a mid-chain ring; cure the root's own cause first)",
                   "reason": "self-unwashable", "root": "Y" } } }
```

## 5. The three candidate sources and the offline injection form

Three candidate sources, any one (mutually exclusive · docstring "Three
candidate sources" section):

```bash
# source ①: candidates TSV fed directly (header row `件名<TAB>md5`)
bash cw.sh unclog --src "$SRC" --world "$WORLD" --candidates cands.tsv --json r.json
# source ②: merge existing probe ledgers (argv order = merge order · later batches override earlier · merge mode has no per-round whole re-probe)
bash cw.sh unclog --src "$SRC" --chain-ledgers l1.json l2.json --json r.json
# source ③ (neither given): --src whole-tree enumeration, per-file md5 over *.v
bash cw.sh unclog --src "$SRC" --world "$WORLD" --json r.json
```

Offline injection (workflow drill / CI use · discipline ③): `--injector DIR/`,
`DIR/scenario.json = {"probe":[ledger...],"resprobe":[ledger...]}`; the two
probe_engine call classes, probe/resprobe, consume canned ledgers **strictly
in order** (written verbatim into the workdir, then still feeding the real
chain_graph · exhausted/missing-column/broken-shape fail loud 2);
chain_graph/cure_applier/scan_v4_token/frozen8 keep running for real under
injection mode (real orchestration, not a puppet; unclog.py docstring
"Offline-testable" section). Ledger record shape (`rocqwash-probe-ledger/1` ·
the form this document's drill used):

```json
{ "schema": "rocqwash-probe-ledger/1", "n_records": 2, "records": {
    "A": { "file": "A", "md5": null, "rc": 0, "red": "", "missing": null,
           "red_class": null, "verdict": "RC0", "red_count": null, "md5_match": null },
    "B": { "file": "B", "md5": null, "rc": 1,
           "red": "Error: Unable to locate library | A (while searching for a .vos file).",
           "missing": "A", "red_class": "MISSING_LIB",
           "verdict": "RED-MISSING_LIB", "red_count": null, "md5_match": null } } }
```

Canned consumption order, measured note (lesson of the November 19, 2026 tmp
drill · recorded as observed): candidates mode **re-probes whole every round**
: each round's probe consumes one canned shot (dry run included); each
re-check's resprobe consumes one shot; a series exhausted = fail-loud 2. A
drill scenario's probe series must therefore be at least as long as the round
count.

**Loop watch state** (same shape as README-cw.md:165-168; example at
README-cw.md:215): `--loop --interval 600 --loop-max 8
--events unclog-events.jsonl`; the closed loop turns pass after pass; a
terminal `unclogged/wall` stops and exits at once; a non-terminal
`rounds-exhausted` rests `--interval` before the next pass (`--loop-max` caps
the pass count · 0 = unlimited).

## 6. dynamic-workflow embed pseudocode

```text
// workflow block ③ unclogging: dry-run gate -> human review -> --apply -> re-check criteria · honest-wall split (tool: cw.sh unclog)
phase "unclog-loop" {
  // 1) dry run (zero disk writes by default · structural guarantee) — the exit code is the terminal verdict in rehearsal
  const dry = await world.run("bash", ["cw.sh", "unclog", "--src", "src/",
      "--world", "world/", "--candidates", "cands.tsv",
      "--json", "unclog-dry.json"]);
  if (dry.exitCode === 0) return { verdict: "already-unclogged" };

  // 2) human review of the plan: the subagent reads only the dry record (washable/patterns/stage) and answers apply|hold
  const review = await agent({ role: "cure-reviewer",
    ask: "read unclog-dry.json rounds[].cure.patterns and the wall record, answer apply|hold with a reason" });
  if (review.answer !== "apply") return { verdict: "held", why: review.reason };

  // 3) apply + re-verify (one command produces the full record · --apply is the only write switch)
  const apply = await world.run("bash", ["cw.sh", "unclog", "--src", "src/",
      "--world", "world/", "--candidates", "cands.tsv", "--apply",
      "--json", "unclog-apply.json"]);
  switch (apply.exitCode) {
    case 0: return { verdict: "unclogged" };              // confirmed by reading the rescan/resprobe three criteria from the record
    case 1: {                                             // wall or rounds-exhausted
      const wall = await agent({ role: "wall-triage",
        ask: "read the wall record in unclog-apply.json and route by reason (frozen-in-service is always untouchable)" });
      return { verdict: "wall", wall: wall.answer };
    }
    case 2: return { verdict: "usage-or-scenario" };
    case 9: return { verdict: "fail-loud" };
  }
}
```

## 7. Honesty notes

- All output samples in this file were produced by real runs of this
  repository's `tools/unclog.py` (current state, HEAD d3c84e6) in the tmp
  injection drill of November 19, 2026 (dry run rc 0 / --apply rc 0 / wall
  rc 1 · fixture A.v/B.v and canned ledgers both tmp-made · zero real
  compilation), not hand-written; sample path prefixes are abbreviated to `…`
  (machine-local tmp dirs; the report itself carries basenames only; unclog.py
  docstring "report face" section). The predecessor captures of November 11,
  2026 (v37 41e74b0), whose stdout labels then carried Chinese wording and
  whose frozen roster then read 8 entries, are archived verbatim in the
  sibling `.zh.md` archive.
- `cure13_natle_premise_lift` is a real canonical-pack pattern name
  (`wash/cure_pack.json`, v1.4.1 at drill time · the `patterns` field value is
  verbatim from the real run report).
- No real compilation probe was run for this document (the real-probe form
  needs the rocq world base · a real compile must ride the cpu_guard wrap:
  `--guard PATH --guard-reg DIR …` pass-through, unclog --help "--guard"
  entry); the real-probe form is the user face; the offline injection form is
  what was measured.
- The exit-code branch table anchors cell-by-cell to the unclog docstring
  "exit codes" section and the `--help` tail note; the wall-reason table
  anchors to the unclog.py:90 honest-wall section and the wall_add call sites
  (unclog.py:666 unprobed · 670 self-unwashable · 737 frozen-in-service · 785
  no-chain-root · 815 root-file-missing · 823/852 exclusive-group-conflict ·
  842 cure-miss · 857 idempotence-fail). Line numbers anchor to the HEAD
  d3c84e6 commit state (concurrent multi-agent development · working-tree line
  numbers drift).

(English brief) Workflow block ③: the unclogging closed loop. Canonical order:
dry-run first (default; `--apply` is the only write switch; dry run touches
nothing, proven by md5 equality), human review of the planned cure patterns, then
`--apply` (canonical cure-pack only, chain-root files only, structurally), then
re-verify (`rescan.residual_zero` + `resprobe.rc_ok` + empty red ledger). Honest
wall (`verdict=wall`, exit 1) reports per-root reasons instead of forcing cures.
Verdicts `unclogged|wall|rounds-exhausted` map to exit 0|1|1; usage/scenario
errors 2; fail-loud 9.
