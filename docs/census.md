# rocqwash tools/ Word-Face Census Re-scan | 2026-11-21

This document accompanies `census-tools.json` (machine-readable per-file records) and
`flag-shape.json` (AST-level flag classification); all three were written in the same pass.

Purpose.  Word-face census companion for the re-scan of `tools/`: per-item readings
  (docstring, argparse face, flag shape, network face, environment markers, invocation
  basis) plus the four-number reconciliation, all bound to the anchor recorded in section 1.
Interface.  Documentation face; sections 1 to 8; section 3 carries one entry per file;
  section 5 carries the four-number reconciliation table.
Dependencies.  Transcribed from the census outputs `census-tools.json` and
  `flag-shape.json` (60 `.py` files under `tools/`, AST word-face level).
Evidence.  Table cells and per-item lines transcribe this scan's JSON records; section 7
  records the register self-check measurements; section 8 records anchors and digests.
Exit-codes.  None of its own; exit-code semantics are runtime evidence not measured at
  cast time (census boundary, section 1).

## 1. Scope and Method

Against the working tree at HEAD `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` (measured via `git rev-parse HEAD` before the
scan; the anchor binds the verdicts below), this re-scan performs a purely lexical pass over
all 60 `.py` files in `tools/`. Command: `python -I docs/census_tools_build.py --tools-dir
D:/ComplexAnalysis/rocqwash/tools --out D:/ComplexAnalysis/rocqwash/docs/census-tools.json --head 2a1fe8fab9374d9a6aa7f672071aacfbab73e21e`,
followed by `python -I flag_shape_probe.py` (cwd = the output directory). Method: `ast.parse`
on each file's raw bytes, extracting bytes/sha256/line count, the module docstring, the
argparse face (import, parser descriptions, the full `add_argument` list, the `add_parser`
subcommand face), the usage-string face, the import list with classification, the network
face (three channels: transport-class imports, subprocess bridge tokens, git network
subcommand tokens), and the special-environment marker face (9 marker families). Flag shape:
each `add_argument` call site is classified value-taking vs boolean (rule: `action=`
`store_true`/`store_false`/`count` is boolean, everything else is value-taking); positional
arguments are bare-name call sites.

**Boundary**: word-face evidence only. No listed tool was executed, imported, or spawned by
either instrument; both ran stdlib-only under `python -I` with zero network. Runtime
behavior, real exit codes, and live `--help` output were not measured (that belongs to a
later light-probe pass; none ran in this re-scan). Scope is `*.py` only: `cpu_guard.sh`
(4,581 B), `taxonomy.json` (11,939 B), `vacgen_env_note.md` (5,639 B), 12 `.py.zh.md`
archive files plus the `vacgen_env_note.md.zh.md` sibling archive, and `__pycache__/` sit outside the census scope and are recorded as
metadata.

**Instrument note**: the builder is the 2026-11-14 cast instrument, this generation run
from the in-repo copy `docs/census_tools_build.py` (the same instrument the 2026-11-20
generation landed; its doc-face re-lay at `cab9147` was AST-identical modulo docstrings
with the CLI face `--tools-dir/--out/--head` unchanged; the 2026-11-14 archive copy stays
at `D:/ComplexAnalysis/attn/_archive/01-战役沙箱-20261117版/_rqw06_capindex_20261114/`). It
carries one hard-coded cast-time annotation (`new_item: true` on
`vacgen.py`), written for the 2026-11-14 cast when that file had just landed; at this anchor
the marker does not read as a delta fact and is voided here by declaration.

## 2. Summary Table

| File | Bytes | Lines | Doc | Arg | Pos/Opt | Network face (word) | Env markers | Selftest | Basis |
|---|---|---|---|---|---|---|---|---|---|
| _abl1_4b_compile.py | 5,621 | 116 | Y | N | 0/0 | zero | env(3), ocaml(28) | none | none |
| _gen_fin_mac.py | 9,761 | 166 | Y | Y | 0/6 | zero | ocaml(7), coq(12), thermal(2), runner(1) | none | arg |
| _http_backoff.py | 5,755 | 126 | Y | N | 0/0 | zero | none | token | none |
| ai_flavor.py | 20,687 | 481 | Y | Y | 0/5 | zero | none | flag | arg |
| ai_flavor_apply.py | 54,406 | 1,303 | Y | Y | 0/7 | urllib.request | none | flag | arg |
| auto_merge.py | 28,831 | 636 | Y | Y | 0/10 | zero | none | flag | arg |
| auto_round.py | 89,111 | 1,990 | Y | Y | 2/22 | zero | none | flag | arg |
| axiom_guard.py | 28,426 | 648 | Y | Y | 0/8 | zero | env(8), coq(49), thermal(1) | flag | arg |
| b_gate_audit.py | 21,052 | 498 | Y | Y | 0/1 | zero | none | flag | arg |
| baseline_diff.py | 42,201 | 822 | Y | Y | 2/2 | zero | none | token | arg |
| bus_feeder.py | 33,104 | 751 | Y | Y | 1/4 | zero | lean(1) | flag | arg |
| calibration_ledger.py | 32,404 | 747 | Y | Y | 0/12 | zero | env(2), lean(10) | flag | arg |
| chain_graph.py | 14,854 | 335 | Y | Y | 1/3 | zero | none | token | arg |
| ci_triage.py | 128,886 | 2,316 | Y | Y | 0/11 | urllib.request +bridge | coq(111), win(4), runner(2) | token | arg |
| contrib_intake.py | 62,130 | 1,365 | Y | Y | 0/11 | git: clone | coq(23) | token | arg |
| cw_doctor.py | 60,001 | 1,194 | Y | Y | 0/15 | zero | env(3), coq(5), dyld(31), thermal(6) | token | arg |
| cw_sentinel.py | 139,143 | 2,589 | Y | Y | 0/23 | http.client, socket, urllib.request +bridge | coq(1), dyld(1), win(5), thermal(3) | token | arg |
| doc_lint.py | 69,864 | 1,442 | Y | Y | 0/3 | zero | none | token | arg |
| evolution_dashboard.py | 52,889 | 1,080 | Y | Y | 0/8 | zero | lean(1) | flag | arg |
| evolve.py | 90,910 | 1,819 | Y | Y | 0/19 | zero | coq(7) | token | arg |
| exp_port.py | 23,281 | 540 | Y | Y | 1/13 | zero | env(2) | flag | arg |
| flaky_guard.py | 49,683 | 1,173 | Y | Y | 0/18 | zero | env(16) | flag | arg |
| gap_cluster.py | 30,859 | 657 | Y | Y | 0/4 | zero | lean(2), win(1) | token | arg |
| i18n_pipeline.py | 80,939 | 1,939 | Y | Y | 0/4 | zero | none | flag | arg |
| i18n_translate.py | 45,371 | 1,301 | Y | Y | 0/13 | urllib.request | none | flag | arg |
| i18n_verify.py | 51,819 | 1,109 | Y | Y | 0/13 | zero | win(1) | flag | arg |
| jargon_apply.py | 51,479 | 1,160 | Y | Y | 0/10 | zero | none | flag | arg |
| jargon_map_sync.py | 81,054 | 1,749 | Y | Y | 0/6 | zero | none | flag | arg |
| lean_sweep.py | 57,056 | 1,089 | Y | Y | 0/16 | zero | lean(32), thermal(1) | token | arg |
| learning_feedback.py | 35,331 | 740 | Y | Y | 0/1 | zero | lean(5) | flag | arg |
| ledger_sync.py | 26,938 | 549 | Y | Y | 0/5 | zero | none | token | arg |
| mcp_server.py | 103,772 | 2,009 | Y | Y | 0/1 | zero | env(3), ocaml(2), coq(11), lean(16), thermal(1) | flag | arg |
| net_probe.py | 28,501 | 612 | Y | Y | 0/7 | socket, ssl, urllib.request +bridge | none | token | arg |
| netname_normalize.py | 15,623 | 341 | Y | Y | 0/4 | zero | none | token | arg |
| norm_lint.py | 37,945 | 944 | Y | Y | 0/9 | zero | none | flag | arg |
| periscope.py | 75,772 | 1,720 | Y | Y | 0/6 | +bridge | lean(3) | flag | arg |
| pin_repair.py | 38,338 | 899 | Y | Y | 0/4 | zero | none | flag | arg |
| pushci.py | 104,495 | 2,138 | Y | Y | 0/21 | urllib.request git: ls-remote+push +bridge | env(1), coq(10) | token | arg |
| red_dispatch.py | 46,500 | 940 | Y | Y | 0/10 | zero | coq(4), win(2) | flag | arg |
| registry_audit.py | 49,582 | 1,030 | Y | Y | 0/11 | zero | coq(12) | token | arg |
| registry_fix.py | 73,501 | 1,420 | Y | Y | 0/9 | zero | env(1), coq(3) | token | arg |
| registry_regen.py | 62,190 | 1,355 | Y | Y | 0/15 | zero | coq(37), win(1) | token | arg |
| registry_union.py | 42,603 | 949 | Y | Y | 0/14 | zero | coq(4) | token | arg |
| render_events.py | 26,759 | 578 | Y | Y | 0/5 | zero | none | token | arg |
| repair_scope.py | 78,951 | 1,856 | Y | Y | 0/12 | zero | thermal(1) | flag | arg |
| repair_weekly.py | 34,095 | 769 | Y | Y | 0/13 | zero | none | flag | arg |
| repo_sync_status.py | 10,348 | 230 | Y | Y | 0/3 | zero | none | token | arg |
| roster_resync.py | 27,142 | 619 | Y | Y | 0/4 | zero | none | token | arg |
| row_render.py | 66,691 | 1,867 | Y | Y | 0/16 | urllib.request | lean(10) | flag | arg |
| scheduler_lite.py | 29,088 | 695 | Y | Y | 1/11 | zero | lean(1) | token | arg |
| select_audit.py | 32,094 | 675 | Y | Y | 0/6 | zero | ocaml(1) | token | arg |
| selfevolve_round.py | 31,385 | 732 | Y | Y | 0/4 | urllib.request git: push +bridge | none | flag | arg |
| symbiosis_bus.py | 39,589 | 880 | Y | Y | 1/9 | zero | none | flag | arg |
| termbase.py | 22,477 | 520 | Y | Y | 0/5 | zero | lean(1), win(1) | flag | arg |
| toolchain_dyld_doctor.py | 26,422 | 542 | Y | Y | 0/6 | zero | env(4), coq(32), dyld(45), win(1), thermal(6) | token | arg |
| tree_audit.py | 27,402 | 593 | Y | Y | 0/3 | zero | lean(15) | flag | arg |
| unclog.py | 103,325 | 1,943 | Y | Y | 0/30 | zero | coq(5), thermal(2) | token | arg |
| uplink.py | 59,383 | 1,392 | Y | Y | 0/11 | zero | none | flag | arg |
| vacgen.py | 146,132 | 3,105 | Y | Y | 0/21 | zero | lean(65), thermal(3) | flag | arg |
| verdict_diff.py | 33,797 | 668 | Y | Y | 0/6 | zero | none | token | arg |
| wash_shape.py | 123,970 | 2,521 | Y | Y | 0/16 | zero | env(6), coq(6), dyld(1), win(3) | token | arg |

Legend: Doc = module docstring present; Arg = argparse import present; Pos/Opt = positional/
optional flag counts (deduplicated call-site names); Network face = three-channel word-face
reading (`+bridge` = subprocess bridge token face; `git:` = network git subcommand tokens);
Env markers = marker families with word-face hit counts (env = `ROCWASH_*`; ocaml = ocamlc/
ocamldep/opam; coq = coqc/coqtop/coqchk/coqdep/rocq family; lean = lake/mathlib/Lean/elan;
dyld = macOS dyld tooling; win = Windows guard wording; gpg; thermal = cpu_guard/_THERMAL;
runner = self-hosted/actions-runner). Env markers are word-face hits, not proof of runtime
requirements (boundary in section 6). Selftest = `flag` (an argparse flag position), `token`
(the `--selftest` word face without an argparse position), `exempt` (a registered
`# selftest-exempt` line; `vacgen.py:3`), `none`. Basis = invocation reconstruction source
(`arg` = argparse; `none` = not reconstructed).

## 3. Per-Item Lines

60 items in filename order. The one-line purpose is a condensed transcription of the
docstring head; verbatim docstring text is recorded per file in `census-tools.json` field
`docstring.head` (first 600 characters). Invocation forms are reconstructed from argparse,
not verified by execution. Per-flag value/boolean classification lives in `flag-shape.json`.

### tools/_abl1_4b_compile.py
- Purpose: Compile the extracted OCaml module tree: module dependency order comes from ocamldep (its continuation lines are joined back into single records); modules are compiled in fixpoint rounds, a module compiling once its dependency set is a subset of the compiled set, each .mli before its .ml; the option.
- Invocation: not reconstructed at this anchor (no argparse import; the v2 docstring
  carries no command-line usage line)
- Imports: os, re, shutil, subprocess, sys (standard library only)
- Flag face: 0 positional, 0 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(3), ocaml(28) marker word faces

### tools/_gen_fin_mac.py
- Purpose: Emit the Mac-form censusFIN probe triple from a source .v module: the probe skeleton (statement-name list → named transparent aliases → single-command multi-name Separate Extraction), the manifest, and the guard-wrapped fire driver.
- Invocation: `python tools/_gen_fin_mac.py [--source] [--module] [--world] [--world-name] [--outdir] [--requires]` (reconstructed from argparse)
- Imports: argparse, io, json, mac_stmt_names, os, sys; local: mac_stmt_names
- Flag face: 0 positional, 6 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: ocaml(7), coq(12), thermal(2), runner(1) marker word faces

### tools/_http_backoff.py
- Purpose: The retry-status judgment, the exponential-backoff delay table and the Retry-After header parser live here once and are imported by `tools/ci_triage.py`, `tools/pushci.py` and `tools/cw_sentinel.py`, so the three inline copies cannot drift again.
- Invocation: not reconstructed at this anchor (no argparse import; the v37 doc face
  carries no command-line usage line); the `--selftest` word face is present
- Imports: sys (standard library only)
- Flag face: 0 positional, 0 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/ai_flavor.py
- Purpose: Scans a file or a directory tree for the 36 AI-flavor wording faces plus a separate em-dash battery (U+2014, target 0) and reports per-hit records with context windows; detection only, no rewriting, stdout reporting by default, zero files written unless --json is given. Interface.
- Invocation: `python tools/ai_flavor.py [--file] [--tree] [--selftest] [--json] [--word-map]` (reconstructed from argparse)
- Imports: argparse, json, os, re, sys (standard library only)
- Flag face: 0 positional, 5 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/ai_flavor_apply.py
- Purpose: Plans advisory rewrites from detector findings; applies them only through a rewrite provider behind gates: plan mode is zero-write; zh ban-remediation faces are human-only and never machine-written; stems offer the register neutral forms; sentence faces offer delete-or-restate; every write passes a.
- Invocation: `python tools/ai_flavor_apply.py [--file] [--json] [--emit-handoff] [--apply-handoff] [--state] [--provider] [--selftest]` (reconstructed from argparse)
- Imports: argparse, importlib.util, io, json, os, re, sys, tempfile, time, urllib.request (standard library only)
- Flag face: 0 positional, 7 optional (1 boolean per flag-shape.json)
- Network face: non-zero (urllib.request)
- SKIP face: no special-environment marker word faces

### tools/auto_merge.py
- Purpose: Judges one pull request against the six-verdict mergeability enum (merge-ok / hold-red / hold-conflict / already-landed / superseded-landed-elsewhere / escalate-unknown) from caller-gathered facts, then runs the safety rail: only merge-ok with a supply/* head branch is auto-execution eligible, under.
- Invocation: `python tools/auto_merge.py [--facts] [--head-branch] [--allow-prefix] [--daily-cap] [--ledger] [--merge-sha] [--post-merge] [--apply] [--json] [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, shutil, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 10 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/auto_round.py
- Purpose: Close the loop after a rewrite pass: admit the rewrite classes per the autonomy gear, commit the touched files as one verified round, append one ledger row (append-only JSONL), mark the commit with round trailers plus a lightweight round ref, and keep anchor, rollback, drift salvage and the query fa.
- Invocation: `python tools/auto_round.py <command> <refined> [--selftest] [--repo-root] [--autonomy] [--state] [--ledger] [--classes] [--files] [--hits] [--class-confidence] [--message] [--continue] [--dry-run] [--class] [--confidence] [--note] [--set] [--promote] [--to] [--from] [--emit] [--limit] [--round]` (reconstructed from argparse)
- Imports: argparse, datetime, json, os, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 2 positional, 22 optional (4 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/axiom_guard.py
- Purpose: Answer "what does each theorem actually rest on?" mechanically for the whole repository: every .v file is compiled in a private temp workdir and judged at two levels (a per-theorem Print Assumptions census plus the coqchk kernel recheck); the standard is strict - every statement Closed, the axiom wh.
- Invocation: `python tools/axiom_guard.py [--repo] [--out] [--rocq] [--coqchk] [--allow-axiom] [--timeout] [--keep] [--selftest]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 8 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(8), coq(49), thermal(1) marker word faces

### tools/b_gate_audit.py
- Purpose: The B threshold needs at least three instances, each backed by one applied round; a single-instance generalization is a false generalization. An instance is one admission of a class in one round (same-round duplicates collapse); rounds count distinct admitting rounds.
- Invocation: `python tools/b_gate_audit.py [--selftest]` (reconstructed from argparse)
- Imports: argparse, contextlib, io, json, os, sys, tempfile (standard library only)
- Flag face: 0 positional, 1 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/baseline_diff.py
- Purpose: Read two `unclog --audit` blockage baselines (schema `rocqwash-unclog/1`, audit form; argv order old then new, chronological order owned by the caller) and emit a blockage delta report. Read-only by default: the only disk writes are the explicit --json/--md report files.
- Invocation: `python tools/baseline_diff.py <old> <new> [--json] [--md]` (reconstructed from argparse)
- Imports: argparse, io, json, os, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 2 positional, 2 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/bus_feeder.py
- Purpose: Read one offline swap package (rocqwash-symbio/1, the export face of tools/symbiosis_bus.py), select its gap-class entries by a documented recognition set, and land one gap row per selected entry in the gap feed ledger (default docs/gap-feed-ledger.jsonl), keyed by the family shape chain of tools/ga.
- Invocation: `python tools/bus_feeder.py <command> [--selftest] [--swap] [--ledger] [--dry-run]` (reconstructed from argparse)
- Imports: argparse, gap_cluster, json, os, symbiosis_bus, sys, tempfile; local: gap_cluster, symbiosis_bus
- Flag face: 1 positional, 4 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(1) marker word faces

### tools/calibration_ledger.py
- Purpose: Pair each per-row predicted confidence in a vacgen v2 report with the measured compile-leg rc face and append one calibration entry per paired row into docs/exp-ledger.jsonl (schema rocqwash-exp/1, carrying correlationId = the report id), through the experience-bus port's idempotent seen set so a re.
- Invocation: `python tools/calibration_ledger.py [--report] [--rc-file] [--leg-map] [--default-leg] [--ledger] [--batch] [--ts] [--signal-threshold] [--signals-out] [--strict] [--dry-run] [--selftest]` (reconstructed from argparse)
- Imports: argparse, datetime, hashlib, io, json, os, shutil, sys, tempfile (standard library only)
- Flag face: 0 positional, 12 optional (3 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(2), lean(10) marker word faces

### tools/chain_graph.py
- Purpose: Merges N probe ledgers (argv order = merge order; the `rocqwash-probe-ledger/1` "records" shell from `probe_engine` and the bare {name: record} dict form are both accepted) and emits: (1) the union merge - later batches override earlier records on duplicate keys, every record accumulating its full `.
- Invocation: `python tools/chain_graph.py <ledgers> [--json] [--md] [--top]` (reconstructed from argparse)
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 1 positional, 3 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/ci_triage.py
- Purpose: Triages the jobs of a GitHub Actions run into failing and passing: prints a step-level table (step name/status/conclusion/start/ end/duration in seconds), assigns each job a family from the five-family classification taxonomy plus the all-passing state, and prescribes an action; with --baseline-seco.
- Invocation: `python tools/ci_triage.py [--offline] [--repo] [--run] [--logs] [--no-dump-filter] [--netrc] [--baseline-seconds] [--baseline-step] [--timeout] [--retry-max] [--json]` (reconstructed from argparse)
- Imports: _http_backoff, argparse, datetime, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request; local: _http_backoff
- Flag face: 0 positional, 11 optional (2 boolean per flag-shape.json)
- Network face: non-zero (urllib.request; bridge tokens)
- SKIP face: coq(111), win(4), runner(2) marker word faces

### tools/contrib_intake.py
- Purpose: Reconciles a contribution face (local clone or archive tree at a ref) against a base face, running four gates without short-circuit: `registry` replays the `registry_union` three-face union dry run (base face for merge-base and main, contrib face the branch), blocks on any assertion blast and attach.
- Invocation: `python tools/contrib_intake.py [--contrib-repo] [--contrib-ref] [--base-repo] [--base-ref] [--paths] [--order-path] [--project-path] [--lane-prefix] [--jargon-map] [--rocq-cmd] [--json]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, registry_union, shutil, subprocess, sys, tempfile; local: registry_union
- Flag face: 0 positional, 11 optional (0 boolean per flag-shape.json)
- Network face: non-zero (git: clone)
- SKIP face: coq(23) marker word faces

### tools/cw_doctor.py
- Purpose: One-shot overall health assessment: orchestrates the existing per-domain tools over four domains, each driven by subprocess (write orchestration, never re-implementation - each tool's CLI and JSON schema are read before wiring; a tool failure or malformed report is fail-loud; zero new engines), and.
- Invocation: `python tools/cw_doctor.py [--json] [--workdir] [--registry] [--src] [--sample] [--world] [--worker] [--donor] [--endpoints] [--guard] [--guard-reg] [--guard-maxwait] [--timeout] [--rocq-cmd] [--injector]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 15 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(3), coq(5), dyld(31), thermal(6) marker word faces

### tools/cw_sentinel.py
- Purpose: Three combinable signal sources (at least one required): (1) --watch-repo: new completed GitHub Actions runs -> ci_triage --offline -> {kind:ci-red, repo, run, family, action}; (2) --watch-ledgers: new ledger/probe JSON -> chain_graph.py -> {kind:blocking, top_root, dependents}; (3) --watch-buildlog.
- Invocation: `python tools/cw_sentinel.py [--once] [--loop] [--interval] [--max-rounds] [--watch-repo] [--branch] [--watch-ledgers] [--watch-buildlog] [--state-file] [--emit] [--emit-max-bytes] [--rebuild-state] [--on-red] [--on-red-preset] [--on-red-arg] [--netrc] [--timeout] [--retry-max] [--net-retries] [--subproc-timeout] [--injector] [--sleep-scale] [--json]` (reconstructed from argparse)
- Imports: _http_backoff, argparse, datetime, http.client, io, json, os, re, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request; local: _http_backoff
- Flag face: 0 positional, 23 optional (3 boolean per flag-shape.json)
- Network face: non-zero (http.client, socket, urllib.request; bridge tokens)
- SKIP face: coq(1), dyld(1), win(5), thermal(3) marker word faces

### tools/doc_lint.py
- Purpose: Runs the three checks (all purely local, zero network, zero compiles, Python 3 stdlib only, orchestrating zero new engines - every parsing rule is anchored to the current on-disk lines, no invented shapes) and reports whether the documentation and the implementation agree.
- Invocation: `python tools/doc_lint.py [--repo] [--json] [--help-cap]` (reconstructed from argparse)
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 3 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/evolution_dashboard.py
- Purpose: Aggregate the experience ledger (docs/exp-ledger.jsonl, schema rocqwash-exp/1), the round ledger (docs/round-ledger.jsonl, schema rocqwash-round/1), and vacgen v2 report JSON files (the TODO-SEAT faces) into one dashboard: the coverageLowerPct curve over report runs with a per-point TODO-SEAT delta.
- Invocation: `python tools/evolution_dashboard.py [--repo] [--exp-ledger] [--rounds] [--reports] [--json-out] [--md-out] [--stdout] [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, shutil, sys, tempfile (standard library only)
- Flag face: 0 positional, 8 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(1) marker word faces

### tools/evolve.py
- Purpose: The law-three harvest→derive→draft pipeline: turn live repository signals into a reviewed, human-gated task-brief draft for the next round.
- Invocation: `python tools/evolve.py [--draft-out] [--json] [--repo-root] [--top] [--baseline] [--jargon-map] [--watch-repo] [--sentinel-state] [--sentinel-state-seed] [--sentinel-branch] [--sentinel-events] [--sentinel-injector] [--suite-ledger] [--suite-now] [--registry-git] [--registry-ref] [--git-path-order] [--git-path-project] [--registry-baseline]` (reconstructed from argparse)
- Imports: argparse, frozen8, io, json, os, re, shutil, subprocess, sys, tempfile; local: frozen8
- Flag face: 0 positional, 19 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(7) marker word faces

### tools/exp_port.py
- Purpose: The single write/read port of the in-repository experience ledger docs/exp-ledger.jsonl (one JSON object per line, schema rocqwash-exp/1).
- Invocation: `python tools/exp_port.py <command> [--selftest] [--tool] [--points] [--evidence] [--batch] [--actor] [--id] [--ts] [--source-file] [--correlation-id] [--ledger] [--dry-run] [--limit]` (reconstructed from argparse)
- Imports: argparse, datetime, hashlib, json, os, shutil, sys, tempfile (standard library only)
- Flag face: 1 positional, 13 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(2) marker word faces

### tools/flaky_guard.py
- Purpose: Repair class E2-3. Classifies each red case in a suite log by an isolation probe (suite-red plus alone-green = order-dependent; red in both contexts = content red that stays visible) and, on --apply, moves an order-dependent case into tests/advisory_roster.txt so the default suite drops it (loud ADV.
- Invocation: `python tools/flaky_guard.py [--detect] [--probe] [--move] [--restore] [--status] [--selftest] [--log] [--json] [--no-probe] [--apply] [--green-rounds] [--budget] [--probe-timeout] [--repo] [--roster] [--ledger] [--suite] [--py]` (reconstructed from argparse)
- Imports: argparse, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 18 optional (5 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(16) marker word faces

### tools/gap_cluster.py
- Purpose: Collect gap entries from two local faces, the experience ledger (docs/exp-ledger.jsonl, schema rocqwash-exp/1, gap-class entries carrying the protocol tokens below) and vacgen report JSON files (assumptions[] entries with status todo_seat), and aggregate them by family shape key into a gap ledger (s.
- Invocation: `python tools/gap_cluster.py [--ledger] [--reports] [--out] [--json]` (reconstructed from argparse)
- Imports: argparse, hashlib, json, os, re, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 4 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(2), win(1) marker word faces

### tools/i18n_pipeline.py
- Purpose: Stages P0, P1, P3 and P6 of the zh<->en four-linkage pipeline (i18n SPEC sections 2-5, 7 and 9): P0 policy pre-check over the target-face regime table (refusal is a legal ledgered outcome); P1 prose segmentation under a token protection list; P3 linkage application L1-L4, mechanical rewrites limited.
- Invocation: `python tools/i18n_pipeline.py [--manifest] [--stage] [--json] [--selftest]` (reconstructed from argparse)
- Imports: argparse, datetime, hashlib, importlib.util, io, json, os, re, sys (standard library only)
- Flag face: 0 positional, 4 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/i18n_translate.py
- Purpose: Enforce per-segment model-site annotation (SPEC section 5): every machine-translated segment carries a nine-key record (segment_id, direction, model_id, prompt_template_ref, timestamp_utc, linkages_run, annotation_site, policy_precheck_ref, tenpoint_verdict); a backfill with no model_id, or a segmen.
- Invocation: `python tools/i18n_translate.py [--segments] [--direction] [--emit] [--ingest] [--provider] [--prompts] [--policy-ref] [--translated-out] [--ledger-out] [--netred-ledger] [--json] [--timeout] [--selftest]` (reconstructed from argparse)
- Imports: argparse, datetime, io, json, os, sys, urllib.error, urllib.request (standard library only)
- Flag face: 0 positional, 13 optional (1 boolean per flag-shape.json)
- Network face: non-zero (urllib.request)
- SKIP face: no special-environment marker word faces

### tools/i18n_verify.py
- Purpose: P4 runs the mechanical verify instruments over one target file as subprocesses (ai-flavor detector, norm_lint with the jargon map, doc_lint) and aggregates exit codes and reports into one matrix, schema rocqwash.i18n.verify/1; findings are data.
- Invocation: `python tools/i18n_verify.py [--verify-target] [--emit-tenpoint] [--ingest-tenpoint] [--selftest] [--faces] [--ai-flavor-tool] [--norm-lint-tool] [--doc-lint-tool] [--repo] [--jargon-map] [--ledger] [--timestamp] [--json]` (reconstructed from argparse)
- Imports: argparse, copy, io, json, os, re, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 13 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: win(1) marker word faces

### tools/jargon_apply.py
- Purpose: Reads seeds/jargon/jargon-map.json (159 entries: the 62-entry seed prefix plus the md-table superset the P1 sync absorbed) read-only and drives the E2 application face: plan every machine-applicable occurrence of a banned face on .py/.sh/.md prose faces; behind --apply only, splice the mapped standa.
- Invocation: `python tools/jargon_apply.py [--tree] [--file] [--jargon-map] [--plan] [--apply] [--json] [--guarded-interactive] [--guarded-out] [--selftest] [--a2-table]` (reconstructed from argparse)
- Imports: argparse, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 10 optional (4 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/jargon_map_sync.py
- Purpose: One-way sync of docs/jargon-to-standard-mapping-v1.md (detector map) into seeds/jargon/jargon-map.json (apply map), plus contract-prov-v2 S1 provenance: --apply re-signs v2 pins (repo to the blob sha of current bytes, external to the md5 of LF-normalized snapshot bytes) and refuses a v1-shaped seed;.
- Invocation: `python tools/jargon_map_sync.py [--md] [--map] [--apply] [--migrate] [--json] [--selftest]` (reconstructed from argparse)
- Imports: argparse, contextlib, hashlib, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 6 optional (3 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/lean_sweep.py
- Purpose: Bins vacuity probe files (witness, boundary, the canonical five refutation forms) into per-lane compile shots, dedups every probe against the union of all prior lane ledgers (skip-existing), casts merged shots with a row-offset map plus a zero-compile syntax precheck, and fires only when --fire is g.
- Invocation: `python tools/lean_sweep.py [--batches] [--out] [--json] [--fire] [--worktree] [--lake] [--guard] [--core] [--lanes] [--skip-ledgers] [--taxonomy] [--max-shot-items] [--big-item-bytes] [--liveness-interval] [--bisect-max] [--timeout-s]` (reconstructed from argparse)
- Imports: argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 16 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(32), thermal(1) marker word faces

### tools/learning_feedback.py
- Purpose: Read the round ledger, the round state, and the experience ledger (schemas rocqwash-round/1, rocqwash.round-state/1, rocqwash-exp/1) strictly read-only, and cast the scheduling feedback face (schema rocqwash.scheduling-feedback/1) into docs/scheduling-feedback.json: the round admission face, the rep.
- Invocation: `python tools/learning_feedback.py [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, re, shutil, sys, tempfile (standard library only)
- Flag face: 0 positional, 1 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(5) marker word faces

### tools/ledger_sync.py
- Purpose: Merges a probe ledger (the `rocqwash-probe-ledger/1` "records" shell from `probe_engine`, a freeze-ledger `items` shell, or a bare {name: record} dict) into a status-ledger TSV (the `件名`/`行数`/`md5`/ `RED`/`状态`/`备注` column family) row by row and writes the new status-ledger TSV.
- Invocation: `python tools/ledger_sync.py [--probe] [--ledger] [--out] [--report] [--policy]` (reconstructed from argparse)
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 5 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/mcp_server.py
- Purpose: Expose the repository tool capability surface over the Model Context Protocol (MCP) stdio transport: 43 registered capabilities, each spec transcribed from its docs/CAPABILITY-INDEX.md entry line.
- Invocation: `python tools/mcp_server.py [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, subprocess, sys (standard library only)
- Flag face: 0 positional, 1 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(3), ocaml(2), coq(11), lean(16), thermal(1) marker word faces

### tools/net_probe.py
- Purpose: Probe all endpoints with a bare GET and decide the dual-probe stability window (a single-probe round must not initiate): with --stable-window the window holds only when every endpoint is reachable in every round; without it exit 0 only means the probe completed.
- Invocation: `python tools/net_probe.py [--endpoints] [--rounds] [--interval] [--stable-window] [--jitter] [--seed] [--json]` (reconstructed from argparse)
- Imports: argparse, datetime, io, json, os, random, shutil, socket, ssl, subprocess, sys, tempfile, time, urllib.error, urllib.request (standard library only)
- Flag face: 0 positional, 7 optional (1 boolean per flag-shape.json)
- Network face: non-zero (socket, ssl, urllib.request; bridge tokens)
- SKIP face: no toolchain markers; runs need a network window (its own job). Note: the
  docstring documents `--selftest` while the argparse flag face (7 flags) does not list
  it; the doc-versus-argparse divergence recorded at census time persists at this anchor.

### tools/netname_normalize.py
- Purpose: A `.v` file mis-saved with the doubled `.v.v` suffix (editor append or script concatenation) makes the Require face resolve nothing under the clean name, a false gap in the dependency net.
- Invocation: `python tools/netname_normalize.py [--dir] [--apply] [--map] [--json]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 4 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/norm_lint.py
- Purpose: Machine-checks prose faces (comments, docstrings, shell help, documentation) of .py/.sh/.md files: (1) header shape, error -- banner plus five-field block, names Purpose. / Interface. / Dependencies. / Evidence. / Exit-codes.
- Invocation: `python tools/norm_lint.py [--tree] [--file] [--jargon-map] [--cjk-threshold] [--cjk-whitelist] [--json] [--ai-flavor-map] [--md] [--selftest]` (reconstructed from argparse)
- Imports: argparse, fnmatch, importlib.util, io, json, os, re, shutil, sys, tempfile, tokenize (standard library only)
- Flag face: 0 positional, 9 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/periscope.py
- Purpose: Sweep a configurable observation list of six sources (mathlib PR search, a single pull request, two arXiv legs, the coordination issue with its comments sub-face, and an upstream commit tip checked against a frozen prefix), write raw bodies plus a per-shot NETRED ledger, keep a sentinel window log w.
- Invocation: `python tools/periscope.py [--config] [--out] [--rounds] [--netrc] [--dry-run] [--selftest]` (reconstructed from argparse)
- Imports: argparse, copy, datetime, io, json, os, shutil, subprocess, sys, tempfile, time, xml.etree.ElementTree (standard library only)
- Flag face: 0 positional, 6 optional (2 boolean per flag-shape.json)
- Network face: non-zero (bridge tokens)
- SKIP face: lean(3) marker word faces

### tools/pin_repair.py
- Purpose: R15 auto-repair executor over the provenance v2 pins. Judgment is per pin kind: a repo source by its committed blob sha (git rev-parse HEAD:<path>); an external source by its in-repo snapshot md5 over CRLF-to-LF-normalized bytes (consistency layer) plus the upstream original's normalized md5 (freshn.
- Invocation: `python tools/pin_repair.py [--selftest] [--plan] [--apply] [--seed]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 4 optional (3 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/pushci.py
- Purpose: Run the post-fix push-and-CI sequence as one command: preflight checks, push, run watch, heal, verdict, optional PR merge. The four existing tools (doctor, net_probe, ci_triage, gate4) always run as subprocesses; this file supplies only the glue and the state machine. Interface.
- Invocation: `python tools/pushci.py [--repo-path] [--branch] [--base-ref] [--remote] [--pre-scan-gate4] [--pr] [--merge] [--merge-method] [--max-heal] [--watch-interval] [--probe-interval] [--watch-max-rounds] [--timeout] [--retry-max] [--steps] [--injector] [--git-caller] [--sleep-scale] [--netrc] [--json] [--dry-run]` (reconstructed from argparse)
- Imports: _http_backoff, argparse, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request; local: _http_backoff
- Flag face: 0 positional, 21 optional (3 boolean per flag-shape.json)
- Network face: non-zero (urllib.request; git: ls-remote+push; bridge tokens)
- SKIP face: env(1), coq(10) marker word faces

### tools/red_dispatch.py
- Purpose: Read sentinel events (cw_sentinel stream, rocqwash-sentinel-event/1 JSONL, make_event shape at cw_sentinel.py:435-443), look kind/family up in the route table, and emit action presets.
- Invocation: `python tools/red_dispatch.py [--event-file] [--preset] [--json] [--state-file] [--cooldown] [--repo-path] [--param] [--on-args] [--dry-run] [--selftest]` (reconstructed from argparse)
- Imports: argparse, contextlib, io, json, os, re, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 10 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(4), win(2) marker word faces

### tools/registry_audit.py
- Purpose: Read-only hygiene audits over the order.txt/_CoqProject registry pair: duplicate rows under one key; order-book anchor defects (anchor-text collisions, seq-form, malformed, missing anchors); cross-book orphans on the .v base-name basis; optional --live-src topology reconciliation.
- Invocation: `python tools/registry_audit.py [--order] [--project] [--git] [--ref] [--git-path-order] [--git-path-project] [--live-src] [--anchor-src] [--fix-plan] [--json] [--md]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, registry_union, shutil, subprocess, sys, tempfile; local: registry_union
- Flag face: 0 positional, 11 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(12) marker word faces

### tools/registry_fix.py
- Purpose: Execute the deterministic fix plan produced by `tools/registry_audit.py --fix-plan` over the audited order.txt/_CoqProject book pair: DEDUP keeps the first row of each duplicate group and drops the rest; REANCHOR rewrites anchor rows through the `registry_union.apply_reanchor` engine; non-mechanical.
- Invocation: `python tools/registry_fix.py [--audit-json] [--order] [--project] [--anchor-src] [--apply] [--orphan-add] [--work-dir] [--audit-tool] [--json]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, registry_union, shutil, subprocess, sys, tempfile; local: registry_union
- Flag face: 0 positional, 9 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(1), coq(3) marker word faces

### tools/registry_regen.py
- Purpose: Rebuild the contribution-side registry pair (order.txt and _CoqProject) as the merge-target books verbatim plus canonical rows for the named pieces, tail-appended in dependency order, each order row carrying the canonical anchor `#R<seq>-<md5-8>` recomputed from the piece entity.
- Invocation: `python tools/registry_regen.py [--base-repo] [--base-ref] [--contrib-repo] [--contrib-ref] [--pieces] [--anchor-src] [--dep-source] [--seq] [--base-path-order] [--base-path-project] [--contrib-path-order] [--contrib-path-project] [--out] [--apply] [--json]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, re, registry_union, shutil, subprocess, sys, tempfile; local: registry_union
- Flag face: 0 positional, 15 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(37), win(1) marker word faces

### tools/registry_union.py
- Purpose: Rebuild the registry after a branch/main tail-append collision: both sides appended to order.txt/_CoqProject and a line-by-line merge is impossible. The current main registry is the base; branch lines truly unique against the merge-base are appended in branch order.
- Invocation: `python tools/registry_union.py [--base] [--main] [--branch] [--git] [--ref-base] [--ref-main] [--ref-branch] [--git-path] [--kind] [--reanchor] [--anchor-src] [--out] [--apply] [--json]` (reconstructed from argparse)
- Imports: argparse, collections, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 14 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(4) marker word faces

### tools/render_events.py
- Purpose: Render event streams into a deterministic markdown ledger plus a `rocqwash-render-events/1` JSON summary; accepted input shapes: native `rocqwash-sentinel-event/1` and any JSON-object-per-line stream (measured: `rocqwash-exp/1` rows, bad_lines=0; missing kind `other`, family/action `(none)`); a fail.
- Invocation: `python tools/render_events.py [--events] [--dir] [--md] [--json] [--top]` (reconstructed from argparse)
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 5 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/repair_scope.py
- Purpose: One source of truth for the faces a repair class never targets: the frozen ledger rows (LEDGER8 and CHECKERS read at runtime from certify/frozen8.py), the append-only ledger document, and the frozen directory families.
- Invocation: `python tools/repair_scope.py [--selftest] [--repo] [--check] [--a2-table] [--classes] [--lane-detect] [--lane-apply] [--suite] [--ledger] [--json-out] [--doc-count-detect] [--doc-count-apply]` (reconstructed from argparse)
- Imports: argparse, ast, datetime, doc_lint, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile; local: doc_lint
- Flag face: 0 positional, 12 optional (6 boolean per flag-shape.json)
- Network face: zero
- SKIP face: thermal(1) marker word faces

### tools/repair_weekly.py
- Purpose: Aggregates the repair-outcome ledger (docs/repair-ledger.jsonl, append-only JSONL) into the weekly distribution face: the per-red outcome census under the E6 vocabulary, class and ticket distributions, and the ISO-week slice of --date.
- Invocation: `python tools/repair_weekly.py [--ledger] [--date] [--out] [--json] [--record] [--apply] [--class] [--target] [--repair-outcome] [--ticket] [--evidence-file] [--reason] [--selftest]` (reconstructed from argparse)
- Imports: argparse, datetime, hashlib, io, json, os, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 13 optional (3 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/roster_resync.py
- Purpose: The suite roster (the CASES block of tests/run_tests.sh) is the only count authority.
- Invocation: `python tools/roster_resync.py [--repo] [--apply] [--ledger] [--json]` (reconstructed from argparse)
- Imports: argparse, doc_lint, hashlib, io, json, os, repair_scope, shutil, subprocess, sys, tempfile, time; local: doc_lint, repair_scope
- Flag face: 0 positional, 4 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/row_render.py
- Purpose: Render a gap-cluster ledger (the W1 face) into candidate taxonomy rows for docs/drafts/taxonomy-candidates.json: emit a render packet, an external model-side agent backfills one candidate row per gap, and ingest admits every row only when the vacgen admission gate (validate_row, C3.4) passes; the fo.
- Invocation: `python tools/row_render.py [--gaps] [--emit] [--ingest] [--check-draft] [--emit-tenpoint] [--ingest-tenpoint] [--draft-out] [--provider] [--vacgen] [--prompts] [--policy-ref] [--ledger-out] [--netred-ledger] [--json] [--timeout] [--selftest]` (reconstructed from argparse)
- Imports: argparse, datetime, importlib.util, io, json, os, re, sys, tempfile, urllib.error, urllib.request (standard library only)
- Flag face: 0 positional, 16 optional (1 boolean per flag-shape.json)
- Network face: non-zero (urllib.request)
- SKIP face: lean(10) marker word faces

### tools/scheduler_lite.py
- Purpose: The lite scheduler of recursive batch 3 (ticket X2): watches the TODO-SEAT gap account (gap feed ledger plus vacgen report directory, aggregated by tools/gap_cluster.py) and the round cadence (docs/round-ledger.jsonl), and decides whether a jargon-class auto round is due under the tier-B auto gear (.
- Invocation: `python tools/scheduler_lite.py <command> [--gap-ledger] [--reports] [--rounds] [--autonomy] [--state] [--ef-marker] [--threshold] [--interval-seconds] [--now-utc] [--out] [--json]` (reconstructed from argparse)
- Imports: argparse, datetime, importlib.util, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 1 positional, 11 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(1) marker word faces

### tools/select_audit.py
- Purpose: Audits candidate selection lists against a full read of the tree's `order.txt` roster (line-by-line, never from memory), so in-batch duplicates, cross-batch name collisions, roster ghosts and duplicate roster rows surface before a batch enters a born world.
- Invocation: `python tools/select_audit.py [--order] [--select] [--grep] [--requires] [--world] [--json]` (reconstructed from argparse)
- Imports: argparse, io, json, os, re, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 6 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: ocaml(1) marker word faces

### tools/selfevolve_round.py
- Purpose: One mechanical round: census -> apply -> verify (py_compile / bash -n gates, norm_lint / doc_lint advisory) -> auto_round commit -> push -> route the CI judge (R13 sub-face 4). Frozen faces stay excluded by jargon_apply; zero fixes = no-op pass; residue != 0 = fail-loud red.
- Invocation: `python tools/selfevolve_round.py [--dry-run] [--pin-repair] [--seed] [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, shutil, subprocess, sys, tempfile, time, types, urllib.request (standard library only)
- Flag face: 0 positional, 4 optional (3 boolean per flag-shape.json)
- Network face: non-zero (urllib.request; git: push; bridge tokens)
- SKIP face: no special-environment marker word faces

### tools/symbiosis_bus.py
- Purpose: Carry experience entries (rocqwash-exp/1) between checkouts as offline swap files (rocqwash-symbio/1): export stamps sourceRepo and the HEAD anchor; import lands one entry per exp_port.append call (the single write face; duplicate ids skip idempotently); status counts both directions from content; d.
- Invocation: `python tools/symbiosis_bus.py <command> [--selftest] [--out] [--swap] [--ledger] [--source-repo] [--anchor] [--a] [--b] [--dry-run]` (reconstructed from argparse)
- Imports: argparse, exp_port, json, os, sys, tempfile; local: exp_port
- Flag face: 1 positional, 9 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/termbase.py
- Purpose: Load the built-in termbase seed (a read-only transcription snapshot), validate its schema fail-loud, and answer exact-face term lookups against the current-term column.
- Invocation: `python tools/termbase.py [--lookup] [--schema-check] [--selftest] [--db] [--json]` (reconstructed from argparse)
- Imports: argparse, ast, copy, io, json, os, re, shutil, sys, tempfile (standard library only)
- Flag face: 0 positional, 5 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(1), win(1) marker word faces

### tools/toolchain_dyld_doctor.py
- Purpose: Diagnoses dyld external-library breakage in the rocqworker binary; diagnose-only: restore advice is printed, never executed (the restore action belongs to the operator).
- Invocation: `python tools/toolchain_dyld_doctor.py [--worker] [--donor] [--smoke] [--coqc] [--guard] [--json]` (reconstructed from argparse)
- Imports: argparse, io, json, os, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 6 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(4), coq(32), dyld(45), win(1), thermal(6) marker word faces

### tools/tree_audit.py
- Purpose: One JSON-line census of a source tree: file/byte/line totals (lines and non-empty lines), declaration counts split into thm (theorem|lemma) and defFam (def|abbrev|structure|class|instance|inductive) with decls as their combined total, an unsound-feature sweep (sorry, sorryAx, axiom, opaque, native_d.
- Invocation: `python tools/tree_audit.py [--root] [--json] [--selftest]` (reconstructed from argparse)
- Imports: argparse, json, os, re, shutil, sys, tempfile (standard library only)
- Flag face: 0 positional, 3 optional (1 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(15) marker word faces

### tools/unclog.py
- Purpose: Closes the manual five-step unblocking procedure into a self-driving loop over the existing engines; dry run by default - writes happen only under --apply. Interface.
- Invocation: `python tools/unclog.py [--src] [--world] [--candidates] [--chain-ledgers] [--repo-path] [--rounds] [--apply] [--audit] [--top] [--scan-ids] [--pack] [--probe-resume] [--probe-parallel] [--rocq-cmd] [--guard] [--guard-reg] [--guard-front] [--guard-mid] [--guard-maxwait] [--timeout] [--workdir] [--json] [--events] [--once] [--loop] [--interval] [--loop-max] [--sleep-scale] [--injector] [--state-file]` (reconstructed from argparse)
- Imports: argparse, hashlib, io, json, os, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 30 optional (5 boolean per flag-shape.json)
- Network face: zero
- SKIP face: coq(5), thermal(2) marker word faces

### tools/uplink.py
- Purpose: One CLI gate for external return packages (zip plus md5 plus per-file manifest): `verify` checks declared digests and prints a per-file evidence list; `intake` re-checks and, only on green, appends one register line (schema `rocqwash-uplink/1`); `pr-prep` renders a pull-request draft.
- Invocation: `python tools/uplink.py <subcommand> [options] # subcommands: verify, intake, pr-prep` (reconstructed from argparse)
- Imports: argparse, hashlib, json, os, re, sys (standard library only)
- Flag face: 0 positional, 11 optional (2 boolean per flag-shape.json)
- Subcommands: verify, intake, pr-prep
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/vacgen.py
- Purpose: Cast the four-account vacuity probe skeleton directory for a Lean statement-face file (cast mode, v1 CLI face preserved verbatim) and run a zero-compile coverage preflight over a census-qualified file set (--preflight-all, difficulty map).
- Invocation: `python tools/vacgen.py [--in] [--out] [--toolchain] [--snapshot] [--audit-id] [--name] [--worktree] [--lake] [--guard] [--core] [--force] [--taxonomy] [--preflight-all] [--census] [--root] [--cluster-table] [--report] [--exp-draft] [--verify-anchors] [--selftest] [--mathlib]` (reconstructed from argparse)
- Imports: argparse, datetime, fractions, hashlib, json, os, re, sys (standard library only)
- Flag face: 0 positional, 21 optional (4 boolean per flag-shape.json)
- Network face: zero
- SKIP face: lean(65), thermal(3) marker word faces

### tools/verdict_diff.py
- Purpose: Merges the per-lane sweep ledgers into one judgment table with the canonical verdict buckets GREEN / ALERT / BLOCKED / MISSING / SKIPPED-TIERT plus a named exception list, records lane conflicts, and (with --baseline) diffs two judgment tables under the baseline-diff convergence caliber (verdict rea.
- Invocation: `python tools/verdict_diff.py [--results-lane] [--expected] [--batches] [--baseline] [--json] [--md]` (reconstructed from argparse)
- Imports: argparse, glob, json, os, shutil, subprocess, sys, tempfile (standard library only)
- Flag face: 0 positional, 6 optional (0 boolean per flag-shape.json)
- Network face: zero
- SKIP face: no special-environment marker word faces

### tools/wash_shape.py
- Purpose: Applies the canonical wash pipeline to every target file in order (each wash selectable via --only; per-wash contract in the extended comment block below): 1 lexical (gate4 word-face findings exchanged through the `wash/comment_pack.json` flag_words table, applied by `wash/comment_sweep.py --apply`;.
- Invocation: `python tools/wash_shape.py [--file] [--dir] [--exclude] [--only] [--header-map] [--header-map-preset] [--anchor-src] [--repo-root] [--json] [--apply] [--loop] [--interval] [--sleep-scale] [--max-rounds] [--events] [--injector]` (reconstructed from argparse)
- Imports: argparse, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, time (standard library only)
- Flag face: 0 positional, 16 optional (2 boolean per flag-shape.json)
- Network face: zero
- SKIP face: env(6), coq(6), dyld(1), win(3) marker word faces

## 4. Aggregates and Observations

Each line is a word-face fact of this re-scan at `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e`:

- Argparse face: 58/60 files carry an argparse import and a reconstructible flag face; 2
  files have no argparse (_abl1_4b_compile.py, _http_backoff.py); their doc faces carry no command-line usage line at this
  anchor, so the invocation basis is `none` (a form change against the 2026-11-14 cast, where
  two of them were restored from usage strings).
- Subcommand face: 1/60 files carry `add_parser` (uplink.py: intake/pr-prep/verify). The
  census-time reading `zero subcommand face across all files` no longer holds tree-wide.
- Network face: 50/60 files read zero across the three channels; 10 read non-zero (ai_flavor_apply.py, ci_triage.py, contrib_intake.py, cw_sentinel.py, i18n_translate.py, net_probe.py, periscope.py, pushci.py, row_render.py, selfevolve_round.py).
- Special-environment face: 35/60 files hit at least one of the 9 marker families (counting
  the `windows_guard` family as well); 25 files carry no marker at all.
- Docstring face: 60/60 files carry a file-header docstring; verbatim text in the JSON.
- Syntax face: 0 syntax errors across all 60 files (`ast.parse` on raw bytes).
- Selftest face: 58/60 files carry the `--selftest` word face; 31 of them hold an argparse
  flag position; `vacgen.py` carries the registered exemption line (`vacgen.py:3`) instead of
  a flag; 2 files carry neither (_abl1_4b_compile.py, _gen_fin_mac.py).
- Dependency face: zero third-party module names across all 60 files (scan boundary in
  section 6). In-repo local imports: 13 files; new local-import edges against the
  census-time snapshot: 6 (bus_feeder.py -> gap_cluster; bus_feeder.py -> symbiosis_bus; repair_scope.py -> doc_lint; roster_resync.py -> doc_lint; roster_resync.py -> repair_scope; symbiosis_bus.py -> exp_port).
  Conditional (try-block) imports: 10 files (auto_merge.py, bus_feeder.py, contrib_intake.py, jargon_map_sync.py, lean_sweep.py, registry_audit.py, registry_fix.py, registry_regen.py, repair_weekly.py, symbiosis_bus.py).
- Internal-item convention: the 3 files whose names begin with `_` (_abl1_4b_compile.py, _gen_fin_mac.py, _http_backoff.py)
  self-describe as internal helpers, consistent with their names.
- Size span: 5,621 B to 146,132 B; line counts 116 to 3,105.
- Non-`.py` metadata: `cpu_guard.sh` (4,581 B; grew from 4,053 B at census time),
  `taxonomy.json` (11,939 B; grew from 3,560 B at the 2026-11-20 generation),
  `vacgen_env_note.md` (5,639 B), twelve `.py.zh.md` archive files plus the
  `vacgen_env_note.md.zh.md` sibling archive, and `__pycache__/`.

## 5. Four-Number Reconciliation

| Face | Count | Time point | Measurement |
|---|---|---|---|
| Census-time cast | 27 | 2026-11-14 @ `5829f6d18a9ee2bc63c19ef46caad115e34a0c85` | transcribed record (the 2026-11-14 census.md and INDEX sections 0 to 1); not re-measured |
| Index entries | 56 | 2026-11-21 @ `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` | `grep -c "^### tools/" docs/CAPABILITY-INDEX.md` = 56, measured |
| Tree face | 60 | 2026-11-21 @ `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` | `ls tools/*.py | wc -l` = 60, measured; this census tabulates 60 records |
| MCP roster | 43 | 2026-11-21 @ `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` (working tree, the tree_audit registration increment) | `EXPECTED_TOOLS` in `tests/t_mcp_face.py` = 43 names, measured; `TOOL_SPECS` in `tools/mcp_server.py` = 43 specs (41 cli + 2 file), measured; the re-scan generation reading was 42 (40 cli + 2 file), advanced by one face since: `tree_audit` (`tools/tree_audit.py`, this increment) |

Deltas, each measured at this anchor:

- Tree 60 = census-time 27 + 33 files added after the 2026-11-14 cast (27 of the 27 still
  present; 0 retired: none). The 33 new files: ai_flavor.py, ai_flavor_apply.py, auto_merge.py, auto_round.py, axiom_guard.py, b_gate_audit.py, bus_feeder.py, calibration_ledger.py, evolution_dashboard.py, exp_port.py, flaky_guard.py, gap_cluster.py, i18n_pipeline.py, i18n_translate.py, i18n_verify.py, jargon_apply.py, jargon_map_sync.py, lean_sweep.py, learning_feedback.py, mcp_server.py, periscope.py, pin_repair.py, repair_scope.py, repair_weekly.py, roster_resync.py, row_render.py, scheduler_lite.py, selfevolve_round.py, symbiosis_bus.py, termbase.py, tree_audit.py, uplink.py, verdict_diff.py.
- Tree 60 vs index 56: 4 files carry no index entry (exp_port.py, jargon_map_sync.py, mcp_server.py, periscope.py).
  Index entries not on the tree: 0 (none).
- Roster 43 = 41 cli capabilities on 41 distinct tool files + 2 file faces
  (`docs/CAPABILITY-INDEX.md`, `docs/symbiosis_sop.md`); 60 - 41 = 19 tool files carry no
  MCP capability. The 43 name-to-target pairs, measured from `TOOL_SPECS`: sentinel_status -> tools/cw_sentinel.py; net_probe -> tools/net_probe.py; baselinediff -> tools/baseline_diff.py; ci_triage -> tools/ci_triage.py; vacgen_generate -> tools/vacgen.py; exp_append -> tools/exp_port.py; pushci_status -> tools/pushci.py; capability_index -> docs/CAPABILITY-INDEX.md; chain_graph -> tools/chain_graph.py; doc_lint -> tools/doc_lint.py; ledger_sync -> tools/ledger_sync.py; netname_normalize -> tools/netname_normalize.py; norm_lint -> tools/norm_lint.py; render_events -> tools/render_events.py; select_audit -> tools/select_audit.py; registry_audit -> tools/registry_audit.py; registry_fix -> tools/registry_fix.py; registry_regen -> tools/registry_regen.py; registry_union -> tools/registry_union.py; abl1_4b_compile -> tools/_abl1_4b_compile.py; http_backoff -> tools/_http_backoff.py; ai_flavor_detect -> tools/ai_flavor.py; jargon_plan -> tools/jargon_apply.py; i18n_pipeline_dryrun -> tools/i18n_pipeline.py; symbiosis_status -> docs/symbiosis_sop.md; termbase -> tools/termbase.py; verdict_diff -> tools/verdict_diff.py; learning_feedback -> tools/learning_feedback.py; b_gate_audit -> tools/b_gate_audit.py; evolution_dashboard -> tools/evolution_dashboard.py; gap_cluster -> tools/gap_cluster.py; repair_weekly -> tools/repair_weekly.py; roster_resync -> tools/roster_resync.py; scheduler_lite -> tools/scheduler_lite.py; axiom_guard -> tools/axiom_guard.py; symbiosis_bus_export -> tools/symbiosis_bus.py; uplink_verify -> tools/uplink.py; i18n_translate_handoff -> tools/i18n_translate.py; i18n_verify -> tools/i18n_verify.py; red_dispatch_report -> tools/red_dispatch.py; ai_flavor_apply_plan -> tools/ai_flavor_apply.py; row_render_check -> tools/row_render.py; tree_audit -> tools/tree_audit.py.
- Caller note: the four counts measure four different faces at four different times; none
  is derivable from another, and each stays bound to its own time point and basis.

### Re-scan generation, November 26, 2026 (rec-gen6)

The 2026-11-22 census (70 records, meta method "python -I AST word-face
parse; no listed tool executed; stdlib only") was produced by a lane-side
one-off that is not in the repository; the files that landed after it
could not be censused and count_guard's R6 face read the gap as a
declared-lag. This generation ships the lane as a repository tool
(`tools/census_rescan.py`, v1 rules documented in its docstring and cast
into seven selftest vectors, double-run stable) and appends the missing
rows through its --merge face: the 2026-11-22 rows are preserved verbatim
(spot-checked by bytes/sha256), the appended rows follow
census_rescan.py's documented v1 rules, and `meta.rescan_generation`
records the split (added list, generator, method note) so the mixed
generation is data rather than a silent method change.
`py_files_censused` now equals the disk count and the R6 face reads
anchored-current (zero-lag).

### Repo-sync merge, November 28, 2026 (the repo-sync registration increment)

The repo-sync registration increment (branch
`supply/desk-offpeak/stranger-call-beta-20261128`, base `origin/main` =
`aa9d0bc`, the probe-proof-face landing) lands `tools/repo_sync_status.py`
and appends its row through the in-repo `census_rescan --merge` face: the
standing rows are preserved verbatim, the appended row follows the same
documented v1 rules, and `meta.py_files_censused` advances 82 to 83 (the
disk count), so the count_guard R6 face reads anchored-current (zero-lag)
at this increment. The MCP roster face advanced 57 to 58 in the same
increment; the four-number reconciliation rows above stay the records of
their own cast times and are not rewritten.

## 6. Negative-Finding Boundaries (four elements)

Each item below is a negative finding of this scan, not an absolute claim.

### 6.1 Zero third-party dependencies (60 files)
1. Scanned: module names of all import statements in the 60 files, compared three ways
   against the stdlib module-name set, the tools/ sibling file-name set, and the full-repo
   `.py` file-name set (AST word face, 2026-11-21).
2. Not scanned: runtime dynamic imports (`importlib` / `__import__` call faces not dug into
   one by one); non-Python dependency faces (the shell environment `cpu_guard.sh` needs).
3. Not an absolute claim: only this word-face scan's zero third-party module-name hits.
4. Aliases not exhausted: import forms that build module names by dynamic string
   concatenation are not exhaustively ruled out.
Re-check condition: re-scan whenever a file is added under tools/ or this census re-runs.

### 6.2 The 50 files with a zero network face
1. Scanned: transport-class import faces (socket/ssl/urllib.request/http.client/requests and
   similar lists), subprocess bridge token faces (curl/wget/api host names/ghproxy), and git
   network-subcommand token faces (push/fetch/clone/pull/ls-remote; three channels, 2026-11-21).
2. Not scanned: actual runtime connection behavior; dynamically constructed host names and
   URLs (f-string assembly forms not semantically restored one by one); the network behavior
   of external programs these tools call (coqc/lake/git bodies).
3. Not an absolute claim: only this three-channel word-face scan's zero hits, not that these
   tools are necessarily zero-network at runtime.
4. Aliases not exhausted: endpoint injection through environment variables and network calls
   through shell aliases or wrapper scripts are not exhaustively ruled out.
Re-check condition: re-check with the light-probe step measuring `--help` and exit codes;
re-scan after tool versions advance.

### 6.3 The subcommand face outside uplink.py (59 files)
1. Scanned: a whole-tree AST scan of `add_parser` call faces across the 60 files (1 file
   hits: uplink.py, subcommands verify/intake/pr-prep).
2. Not scanned: non-argparse manual subcommand routing (`sys.argv[1]` branch forms, such as
   the command word of auto_round.py and symbiosis_bus.py) not semantically restored one by
   one; the mcp_server.py JSON-RPC method face is a transport protocol, not argparse.
3. Not an absolute claim: only the argparse `add_parser` mechanism's word-face reading.
4. Aliases not exhausted: subcommand semantics carried by flag combinations (`--steps`,
   `--stage`, `--only` families) are not exhaustively ruled out.
Re-check condition: re-check when the light-probe step spot-checks flag semantics.

### 6.4 The special-environment face readings
1. Scanned: word-face counts and samples for the 9 marker families (ocaml/opam, the coq/rocq
   family, lean/lake/mathlib, macOS dyld tooling, the Windows guard, GPG, cpu_guard thermal,
   self-hosted runner, `ROCWASH_*` environment variables) across the 60 files.
2. Not scanned: real runtime environment needs; dynamically assembled environment-variable
   names (a `"ROCWASH_" + suffix` form) not exhaustively ruled out.
3. Not an absolute claim: marker hits are word-face facts, not proof of runtime requirements;
   some hits come from comment and help vocabulary faces.
4. Aliases not exhausted: other environment-dependency forms (containers, specific shells,
   PATH layouts) not systematically surveyed.
Re-check condition: verify item by item at the light-probe step and at later real invocations.

## 7. Register Self-Check

The authored text of this file is scheduled for check with the two standing instruments of
the package: `ai_flavor` (the 36-face wording battery plus the em-dash U+2014 battery,
register source glossary sections 4.6/5) and `norm_lint` (annotation-face normalization
lint, 62 conditions), both driven through their MCP faces (`mcp__rocqwash__ai_flavor_detect`,
`mcp__rocqwash__norm_lint`), target = this whole file. At this generation the gate run is
bound to the increment that lands this file: the assembled text below carries the
placeholder until that run appends its measured output, and no gate verdict is claimed
before it runs. Verbatim docstring text is not carried
in this file (it lives in the JSON), so upstream docstring wording sits outside the battery
target. The standalone shell instrument `ai_flavor_selfcheck.sh` cited by the 2026-11-14 cast
was not found in the workspace at closing time; its coverage is carried by the `ai_flavor`
MCP face named above.

Registered exemptions (report-only findings carried as data, per the rule that every
exemption must be registered with its line, class, and basis):

- Class `cjk`, census.md L1: cured at a later repair increment (November 21, 2026):
  the bilingual title segment was Englished per the standing language law and the
  bilingual as-cast text is preserved verbatim in the sibling `census.md.zh.md`
  archive (annotation standard section 5, archive never delete); the 2026-11-20
  generation had registered the bilingual title as mandated and measured
  cjk_ratio 0.000105 against threshold 0.0 under it. Basis: standing English law,
  title form.
- Class `forbidden` (date stamps `2026-11-14` / `2026-11-20` / `2026-11-21`, title, section 1,
  section 5 table cells, section 8): time-point binding is this re-scan's own
  requirement; section 5 binds each of the four counts to its own time point and section 8
  is the provenance face. Basis: the re-scan work order; the contract surface itself
  carries dates in prose (the same class of finding reads on the 2026-11-14 census.md,
  measured error=6 warn=7 under the same instrument, recorded as the same-batch precedent).

Measured output at closing time:

```
(measured output appended after the gate run)
```

## 8. Provenance

- Scan tree: working tree `D:/ComplexAnalysis/rocqwash` at HEAD `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` (measured via
  `git rev-parse HEAD` immediately before the scan; the anchor binds the verdicts). Working-
  tree porcelain at scan time (measured immediately before the scan): 17 modified paths and
  3 untracked files. Of the censused `.py` faces, four (`exp_port.py`, `mcp_server.py`,
  `render_events.py`, `vacgen.py`) carry uncommitted working-tree modifications, so their
  measured bytes/sha256 are working-tree values at scan time, not committed values at the
  recorded HEAD (non-`.py` `taxonomy.json` is modified likewise and sits outside the census
  scope); the 3 untracked files sit at the repo root, outside `tools/`, with no census
  effect. The census read file bytes only and touched nothing (its own JSON outputs are
  written after the read pass).
- Instruments: `census_tools_build.py` (the in-repo `docs/` copy, CLI face
  `--tools-dir/--out/--head` unchanged since its integration) + `flag_shape_probe.py` (archive
  copy at `D:/ComplexAnalysis/attn/_archive/01-战役沙箱-20261117版/_rqw06_capindex_20261114/`,
  run unmodified), stdlib-only, run under `python -I` (isolated mode), zero network, zero
  tool execution. This document was assembled by the 2026-11-20 workbench builder, re-laid
  for this generation (anchor and date advanced; the roster table re-measured to the
  42-pair face; the hard-wired count literals parameterized; the metadata and porcelain
  faces re-measured); prose faces are the builder's text, table and per-item lines are
  transcribed from the JSON records.
- Machine-readable outputs: `census-tools.json` (meta + files[60], per-file sha256 anchors),
  sha256 `f63178c57a6a913dee35d8f0fbdda3b8556a6e8da1397c6a36a28ca4a8788a59` (the re-scan generation bytes, sha256 `f8ec20b2b52d411904a77ea5a518d5b902ae4157248944199ef9abd02fca5e94`, stay on record as the generation this table was transcribed from); `flag-shape.json` (60 records), sha256 `98d621f30e8280f96187731a3ab7600f37147d8b1d33c6e80bdf345152c045ea`.
- Increment re-run (the tree_audit MCP-face registration plus the net_probe unverifiable
  registration, 2026-11-21): the census builder re-ran over the working tree at the same
  HEAD `2a1fe8fab9374d9a6aa7f672071aacfbab73e21e` into `docs/census-tools.json` (the
  section 1 command, same anchor; `meta.py_files_censused` = 60, scope unchanged). Two
  censused faces carry new working-tree modifications at this increment: `mcp_server.py`
  (103,772 B, 2,009 lines; the tree_audit spec plus its frozen roster constant; the lean
  marker word face reads 16 against the table's 15, the added `.lean` spelling of the new
  spec text) and `net_probe.py` (28,501 B, 612 lines; the unverifiable registration adds
  the `ssl` transport import, so the network word face reads socket, ssl, urllib.request;
  SKIP markers stay none; the argparse flag face is unchanged on both files, so
  `flag-shape.json` was not re-run and stays byte-identical in content). The section 2
  and section 3 rows of these two files were re-transcribed from the fresh JSON at this
  increment; all other rows remain the re-scan generation's transcriptions. The aggregate
  faces of section 4 re-measured unchanged (58/60 argparse, 1/60 subcommands, 50/60 zero
  network, 35/60 any-marker, 60/60 docstrings, 0 syntax errors, 58/60 selftest word face).
- Census-time comparison base: the 2026-11-14 census (`census.md` + `census-tools.json` +
  `flag-shape.json`, archive path above), 27 files at `5829f6d18a9ee2bc63c19ef46caad115e34a0c85`.
- Prior generation on record: the 2026-11-20 re-scan (this directory's census.md +
  census-tools.json + flag-shape.json), 59 files at `0765d671a63193430de86faf3a9790f2d8a086a0`,
  landed at commit `13cefb0`; its JSON sha256 faces are recorded in that generation's own
  section 8.
- Cast time: 2026-11-21 (UTC timestamp in `census-tools.json` field `meta.generated_at_utc`).

