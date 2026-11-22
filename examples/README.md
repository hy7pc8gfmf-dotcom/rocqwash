# examples: single-file full-chain demo / `examples — 单文件全链演示样例`

> Purpose.  Demonstrate the full rocqwash chain **scan → names → (N=N
>   assertion) → wash → verify** on one single file, with the measured
>   per-step results and honest SKIP accounting; also documents the
>   supervisor-shell deployment artifact `sentinel_supervisor.sh`.
> Interface.  Entry `make demo` (stepwise: `make scan names nn wash verify
>   clean`); specimen `demo_prop_leak.v` plus wash target
>   `washed/demo_prop_leak_washed.v`, the wash step driven by the 16-patch
>   ledger `washed/demo_ledger.json` through `wash/wash_engine.py`; the
>   original Chinese text of this face is preserved in the sibling
>   `.zh.md` archive.
> Dependencies.  `make` and Python 3 for the scan/names/wash steps;
>   `wash/wash_engine.py` for the wash step; `names/mac_stmt_names.py
>   --compare` for the N=N assertion; rocq/coqc plus `tools/cpu_guard.sh`
>   only on machines that run the verify compile segment.
> Evidence.  The measured-results table below (authoring-machine run of
>   October 31, 2026; re-measured November 1, 2026, rqsup4 round-6
>   inspection, all values identical, `make demo` exit 0, `build/` products
>   byte-identical to the in-repository versions); the engine output is
>   `cmp`-asserted byte-identical to the reference specimen.
> Exit-codes.  `make demo` exits 0 when all RUN steps pass; a SKIP segment
>   is NOT-RUN; never a pass, never passing.

## Full-chain demo: scan → names → (N=N assertion) → wash → verify

This directory demonstrates the full rocqwash chain on a single file,
`demo_prop_leak.v` (original, with conclusion-position Prop bare forms),
plus the wash-target specimen `washed/demo_prop_leak_washed.v` (canonical
mapping per README "Seven Canonical Steps" step 3: conclusion bare `=`→`Id`
via `id_refl`, conclusion nat `<=`→`NatLe` via `natle_ok`; premise-position
Prop lawful keep preserved). Run:

```bash
make demo    # full chain; or stepwise make scan names nn wash verify clean
```

Measured results (authoring-machine run, October 31, 2026; re-measured
November 1, 2026, rqsup4 round-6 inspection, all values identical:
scan/names/N=N/wash line-by-line equal, `make demo` exit 0, `build/`
products byte-identical to the in-repository versions):

| Step | Result |
|---|---|
| scan, original | 5 RED stations (all 5 statements, conclusion position); by_cat `P4_bareeq:4, P5_le:4`; 3 premise-position EXEMPT (lawful keep); md5 `ddeb97fe…` |
| names, original | `total: 5`, `--expect 5` OK, anomalies 0, duplicates ∅ |
| N=N assertion | `断言 5=5 有序全等 : PASS` (original vs washed specimen; `mac_stmt_names.py --compare`) |
| scan, washed | `RED stations: []` (conclusion positions all migrated to Set carriers); 1 premise-position EXEMPT; md5 `5bf31d2f…` |
| wash | **RUN**; `washed/demo_ledger.json` (16-patch exact-string ledger) drives `wash_engine.py`: all 16 patches APPLY, the idempotent replay reports `applied=0 skipped=16`, and the engine output is **byte-identical** to the reference `washed/demo_prop_leak_washed.v` (`cmp` assertion; drift fails the demo). The Makefile designates the engine form directly (wash/ now holds the two generic entries `wash_engine.py` + `world_hook.py`; a bare `cli wash` = exit 4 with the entry list; the demo step calls the engine directly) |
| verify, compile segment | SKIP; the authoring machine has no rocq/coqc; on a rocq-equipped machine `make demo` compiles the washed specimen under `tools/cpu_guard.sh` automatically |
| verify, R4 segment | SKIP; `verify/` uses explicit sub-verb routing (`gate4|verify_vo|verify_gate6|retrofit`); no sub-verb = the four generic entries are not unique (cli exit 4 lists the entries; the R4 per-file entry is still TODO); call `cli/rocqwash verify verify_vo --v … --vo …` directly |

Honest notes:

- SKIP = NOT-RUN; never a pass, never passing; this demo never marks an
  unexecuted step as passed.
- The compilability of both .v files is **unverified** (no rocq/coqc on the
  authoring machine; compilation has never run); the proof bodies use only
  the Coq prelude (`le_n`/`reflexivity`/`eq_sym`/constructors), and once
  rocq is attached the first `make verify` run settles it.
- The scanner's RED is a true-hit candidate; the final ruling belongs to
  the kernel census alone (it reports the list, never a clean bill · E364).

## sentinel_supervisor.sh: resident watcher supervision shell (deployment artifact) / `哨长驻监督壳（部署工件·v1.0）`

`sentinel_supervisor.sh` is the **crash-auto-restart compensation shell**
for the long-running watcher (`tools/cw_sentinel.py --loop`); canonical
deployment form generalized 1:1 from the live /tmp runtime version (restart
cap / ×2 exponential backoff / state-continuation annotation / empty
scheduled-teardown hook slot; fully path-parameterized, no hardcoded
absolute paths; own exit codes 0/1/2/9). Precedent: the v50 round-10
IncompleteRead transport-layer crash with **zero-loss state continuation**
(the seen idempotency account carried across restart, zero duplicate
re-reporting). The deployment manual (precedent source,
generalization-point table, rc triage, deploy command forms) is §1.6 of
`docs/ops-sentinel-长驻手册-v1.0-20261112.md`; a **non-executing** smoke
vector (`bash -n` + key-line grep assertions, zero execution, zero network)
lives in the deployment-form vector of `cw_sentinel --selftest`.
