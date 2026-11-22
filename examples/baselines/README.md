# examples/baselines/README.md: blockage-record baseline intake protocol

> Purpose.  The intake and comparison protocol for this directory's real-tree blockage-record baselines (produced by `tools/unclog.py --audit`, schema `rocqwash-unclog/1` audit form): what a baseline is, the file-naming law, how a baseline is produced, the timing-segment caveat, the two-account comparison reading, and the discipline constraints.
> Interface.  Document face (protocol, not executable). Governs the `audit-<domain>-<yyyymmdd>.json` naming law, the `python3 tools/unclog.py --src <source-tree-root> --audit` production command, and the `python3 tools/baseline_diff.py OLD.json NEW.json` comparison command with its `rocqwash-baseline-diff/1` schema and four-state verdict; the companion page [`perf-README.md`](perf-README.md) governs the speed axis (the probe profile).
> Dependencies.  The documented tool faces `tools/unclog.py`, `tools/baseline_diff.py`, `wash/probe_engine.py` (probe collection), `tools/cpu_guard.sh` (thermal guard, per the companion profile protocol), and the baseline files of this directory; no runtime dependency of its own.
> Evidence.  The audit form, the md5 zero-write self-check, the `no-chain-root` entry rule, the `excluded_fields=["timing"]` comparer rule, and the exit-code contract are transcribed from the documented tool faces (`tools/unclog.py`, `tools/baseline_diff.py`) and re-stated by the sibling [`perf-README.md`](perf-README.md) protocol. The original Chinese text is preserved in the sibling `README.md.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit codes unchanged (0 improved/stable, 1 degraded/incomparable, 2 form error, 9 missing path).

This directory holds the rocqwash **real-tree blockage-record baselines** (produced by `tools/unclog.py --audit`) and their comparison protocol. A baseline is **data**, not a tool failure: a recorded failing-run/wall account is the run record as it happened, and `degraded` is a fallback signal, not a tool failure. The production discipline, the naming law, and the comparison reading all live on this page.

## 1. What a baseline is

`tools/unclog.py --audit` is a read-only audit (single-pass probe collection → `chain_graph` → the blockage-record baseline report):

- schema `rocqwash-unclog/1` **audit form**: `final.verdict="audit"` plus `mode.audit=true`, a single round (`probe_summary`/`chain_top` both present), `cures_planned`/`cures_applied` always 0 (= zero applies, zero re-checks), exit 0 (the failing runs are baseline data, not a tool failure).
- Zero-write hard guarantee: the `--src` whole-file md5 manifest self-verifies as identical before and after the run (a violation fails loud with 9; a polluted baseline never leaves the tool).
- The wall-account graph verdicts are recorded root by root: unprobed / self-unwashable / frozen-in-service, each chain root; failing runs with zero chain roots get a `no-chain-root` entry (walls are never left silent).

## 2. The naming law (the only file-name form entering the repository)

```
audit-<domain>-<yyyymmdd>.json
```

- `<domain>` = the `--src` source-tree basename (for example `wash`) → `audit-wash-20261101.json`;
- `<yyyymmdd>` = the production date; several baselines in one domain sort into a time axis by file name;
- comparison happens within **one domain** only (cross-domain / cross-candidate is incomparable · see §5);
- file names carry no status words (the `audit-wash-fixed.json` shape is banned); the run state lives in the account's `final.red_files`/`wall`, not in the file name.

## 3. Producing a baseline (real-tree runs belong to the main session)

```bash
python3 tools/unclog.py --src <source-tree-root> [--world <world-dir>] --audit \
  --json examples/baselines/audit-<domain>-<yyyymmdd>.json
```

- Real-tree audit live runs belong to **the main session** (the tooling agent proves the instrument face at fixture level only; the same rule in the `tools/unclog.py` docstring); this directory stores baselines and the protocol, not production scripts.
- Offline drills use `--injector DIR` (canned probes, zero real compile, zero real network); the output is instrument-face verification only and **never enters the repository**.

## 4. The timing segment note (the single non-deterministic segment)

`report["timing"]` (per-phase wall-clock seconds: enumerate / manifest / probe+chain / total) is **measured wall clock and differs on every run**; the single non-deterministic segment of a baseline file. The comparer `tools/baseline_diff.py` never includes it in comparison (`excluded_fields=["timing"]` is recorded in the report); "same-input reruns are byte-identical" holds for everything outside the timing segment. Human reading must not assert run state from timings either.

## 5. Comparison (the blockage increase/decrease report)

```bash
python3 tools/baseline_diff.py \
  examples/baselines/audit-<domain>-<old-date>.json \
  examples/baselines/audit-<domain>-<new-date>.json \
  --md /tmp/diff-<domain>-<old-date>-<new-date>.md     # the diff report is a scratch output, never stored in this directory
```

- schema `rocqwash-baseline-diff/1`: `new_blocks` / `resolved_blocks` / `persistent` (keyed by chain root, wall reasons aligned factor by factor; old/new `reason`·`detail` per item plus the change flag; failing-file entries carry the `chain_top` chain-root attribution, honest null when absent) / `score_delta` / `verdict`.
- four verdict states: `improved` (failures decreased) | `degraded` (failures increased) | `stable` (unchanged) | `incomparable` (different candidate sets refuse judgment honestly; deltas always empty, `score_delta=null`). The candidate-face quadruple = `mode.source` + `args.src` + `args.candidates` + `args.chain_ledgers` (basename form); a non-audit-form report mixed into the comparison judges `incomparable` the same way.
- the verdict reads only the failing-run count `n_red`; wall-account changes enter the three lists but never drive the verdict.
- exit codes: 0 = improved/stable · 1 = degraded/incomparable (a failing result is data, not a tool failure · loud stdout) · 2 = input form error · 9 = missing path.

## 6. Discipline (the non-negotiable constraints)

- **No hand-edited baselines**: the comparer's account-consistency checks (`n_red=|red_files|`, `wall_count=|wall|`, `probe_summary`↔`final` failing-run agreement) reject with rc=2 when violated; a polluted comparison never ships.
- **Same-domain same-candidate comparison**: any difference in the candidate-face quadruple → honest `incomparable` (cross-candidate-set deltas are spurious signals; never forced). After changing the candidate list, change the `<domain>` name or record the break explicitly; never mix axes.
- **A baseline is data**: `degraded`/`incomparable` exit 1 is the loud signal the reading face has to accept, not a tool failure; read the `--md` report and decide the handling.
- **timing never enters verdict reading**: see §4.
