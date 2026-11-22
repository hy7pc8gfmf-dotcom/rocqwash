# rocqos (rocqwash) - the Rocq operations suite: constructive-proof unblocking and repository operations

> English main page: [README.md](README.md) · Chinese mirror: [README.zh.md](README.zh.md)

Purpose.  English-language project page for rocqwash (formal name rocqos, the
  Rocq operations suite): what the toolchain is, why its checks are mechanical,
  the three-chain architecture, installation, quickstart, the tool map, testing
  environment limits, and the honest-boundaries register.
Interface.  Documentation face; it links the English main page `README.md`, its
  Chinese mirror `README.zh.md`, the per-tool contract surface
  `docs/CAPABILITY-INDEX.md`, the architecture document
  `docs/en/architecture.md`, and the workflow-integration interface
  `README-cw.md`.
Dependencies.  Statements describe the modules under `scan/`, `names/`, `wash/`,
  `verify/`, `seam/`, `certify/`, `watch/`, `tools/`, `wrapper/`, and
  `cli/rocqwash`; commands assume `python3` >= 3.9 and, for the compile
  verification pieces, a Rocq/Coq toolchain on `PATH`.
Evidence.  Quickstart measurements quote rc values and hit lists as taken on a
  clone of this repository; suite and environment claims cite the recorded
  closes in `README.md`'s snapshot entries, with `tests/README.md` as the live
  authority for the case table.
Exit-codes.  None of its own; the exit codes it describes are those of the
  cited tools, described exactly as implemented.

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. Diagnoses are type-theoretic structural checks, fixes are idempotent and replayable, and verdicts come from exit codes, byte-level artifacts, and kernel-level census rather than from self-reported statements.

> **Core principle**: What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models. (The Chinese rendering of the motto is on the [Chinese mirror page](README.zh.md).)

Status snapshot: November 21, 2026, public repository, release tag `rw-v0.1.1-20261117` (GPG-signed, `git verify-tag` good signature). Formal name **rocqos**, the Rocq operations suite; the repository link name stays `rocqwash` (one repo, two names). Main advances continuously; the code and its `--help` output are the source of truth. The per-tool capability contract surface is [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md); the component-level architecture document is [`docs/en/architecture.md`](docs/en/architecture.md) (Chinese mirror: [`docs/zh/architecture.md`](docs/zh/architecture.md)).

## What it is

**Terminology**: this document's "...-face" terms denote the region of a `.v` file a tool operates on: statement-face = statement lines, annotation-face = comment/header text, as opposed to proof bodies. In scanner output, a "station" is one statement of the scanned file, reported by its declaration name; several findings on the same statement count as one station.

- **scan/**: statement-face Prop-leakage scanner (`scan/mac_stmt_scan.py`; five frozen families P1-P5 plus three negative-capture families, full channel definitions in [`docs/en/architecture.md`](docs/en/architecture.md) §4, with four-way RED/WHITELIST/EXEMPT/CAPTURE classification), token-level qualified-identifier census (`scan/scan_v4_token.py`), and a dual-scanner cross-check driver (`scan/dual_scan.py`) that reports per-file scanner disagreement as data.
- **names/**: statement-name ordinal extractor with an ordered-equality assertion (`names/mac_stmt_names.py`): N names in, N names asserted, exit 2 on mismatch.
- **wash/**: canonical ledger wash engine (`wash/wash_engine.py`, exact-string plus count assertion, idempotent replay), closure-compatibility probe engine (`wash/probe_engine.py`), consumer-cure pack (`wash/cure_pack.json` + `wash/cure_applier.py`, 24 deterministic rewrite patterns), and a comment-domain sweep sidecar (`wash/comment_sweep.py`).
- **verify/**: green-verdict four-pack checker (`verify/verify_vo.py`: exit code, log, `.vo` magic bytes, `.vo` freshness), gate4 comment guard (`verify/gate4_comment_guard.py`), gate6 census wrapper (`verify/verify_gate6.py`), gate7 English adaptation (`verify/retrofit_gate7_irr.py`).
- **seam/**: four-mechanism generation-gap fingerprint probe (`seam/seam_probe.py`), producing candidate lists with prescription mappings.
- **certify/**: two-tier freeze manifest (`certify/freeze_manifest.py`), push-window four-criteria gate (`certify/push_gate.py`, judges the window and never pushes), UNION v2 multi-world manifests, and the frozen-eight registry check (`certify/frozen8.py`, which reconciles the eight frozen in-service pieces against their md5 manifest).
- **watch/**: CI in-flight monitoring, pin-IP push wrapper (dry-run by default), and ls-remote double-read confirmation (`watch/watch.py`, zero-route by construction).
- **tools/**: operational tools, from the resident watcher (`cw_sentinel.py`) through CI triage, one-shot push-CI orchestration, health rollup, blockage clearing, registry hygiene, and documentation linting; see the [Tool map](#tool-map) below.
- **wrapper/**: adapter layers for frozen or out-of-repo originals (`wrapper/coqc_shim.sh`, `wrapper/gate7_probe.sh`, `wrapper/guard.sh`, `wrapper/scan_station.py`); criteria stay solely with the original tools.
- **cli/rocqwash**: unified entry that routes scan/names/wash/verify/seam/certify/watch with 1:1 argv and exit-code passthrough.

## Why

These capabilities are structural properties of Coq/Rocq type theory, not stronger prompts. Terminology: QeqT (likewise QltT/QleT') denotes the Set-carried predicate forms this toolchain washes Prop-carried statements onto, while Qeq/Qlt/Qle are the standard Prop-carried forms; Set and Prop are mutually exclusive sorts in the type theory, so a QeqT goal rejects Qeq-equality rewriting, and no prompt engineering overrides that. The comparison below is a capability statement, not a benchmark claim; each row names the mechanical mechanism that replaces a guess.

| Capability | Without a mechanical check | rocqwash mechanism |
|-----------|---------------------------|--------------------|
| Prop-leakage localization | reads the file and may miss lines | `scan/mac_stmt_scan.py` pins the exact line (measured on the bundled demo: 5 RED hits, see [Quickstart](#quickstart)) |
| Missing-dependency detection | guesses Require chains | Require line-by-line scan plus Set-tree diff |
| Seam classification | reads error text and guesses a direction | four-mechanism generation-gap fingerprint probe with prescription mapping (candidates, adjudicated by a human) |
| Wash rewriting | generates tactics that may not replay | exact-string plus count-asserted replacements, idempotent by construction |
| Compile verification | trusts self-report | subprocess exit codes plus `.vo` magic-byte check (`436f712100015ff4`) |
| Extraction audit | may miss spots | bare full-extraction magic count plus probe dual-face plus five-pattern grep (extraction-side conjunction currently partial, see [Honest boundaries](#honest-boundaries)) |
| N=N name table | may miscount | ordinal full-equality assertion (`names/mac_stmt_names.py`) |
| Multi-world integrity | may skip dependency copies | per-piece md5 manifests (freeze + UNION v2) |

**Core barrier**: these are not "better prompts". QeqT-goal Qeq-rewrite impossibility follows from Set/Prop type-theoretic mutual exclusion.

## Architecture

Three chains in one:

```
Toolchain (scripts + templates + canonical recipes)
    |
Logic Chain (criteria + gates + calibration standards)
    |
Derivation Chain (input -> wash -> verify -> land -> certify -> push)
```

Every compile is wrapped by the thermal guard `tools/cpu_guard.sh` (a ladder queue with a macOS pmset thermal gate and exit-code passthrough, so that long compile runs cannot overheat the host machine). The canonical wash sequence has seven steps (sandbox copy, three-state triage [true-wash / bridge-retain = exception registry / UNCERTAIN = probe-first], canonical face-mapping wash, compile verification, three-source extraction audit, gate7 English adaptation, N=N name-table assertion plus freeze md5); each step must pass before the next, and any failure is recorded as work-in-progress rather than re-labeled.

For each module directory, if it contains exactly one generic `.py` (a file whose name does not start with `_`), `cli/rocqwash <module>` routes to that file, passing arguments and exit codes through unchanged; `_`-prefixed internal tools are never auto-run. Component-level details, per-file status, and the exit-code table are in [`docs/en/architecture.md`](docs/en/architecture.md); the workflow-integration interface (sentinel presets, push-CI orchestration, offline injectors) is in [`README-cw.md`](README-cw.md), and an MCP stdio server is documented in [`docs/mcp.md`](docs/mcp.md).

## Installation

Prerequisites:

- `python3` >= 3.9, standard library only; no third-party packages are required
- a Rocq/Coq 9.x toolchain on `PATH`, needed only for the compile-verification pieces; everything else runs without it
- a Lean toolchain (lake/elan), needed only for the compile-verification leg of `tools/vacgen.py`; its skeleton-casting mode runs without one
- GNU `make`, needed only for the bundled full-chain demo (`make -C examples demo`); Git Bash on Windows does not ship it by default
- on Windows, use Git Bash as the shell (the toolchain is bash + python3)

```bash
git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh          # self-test suite; exit 0 = all green
```

On a stock Windows box, put a real CPython on `PATH` before the first run: the `python3` name can resolve to the Microsoft Store alias, which exits 49 without running anything (see [Testing](#testing)).

### Clean mode quickstart

Throughout this document, the "canonical environment" (likewise the "canonical machine") means this project's sanctioned reference macOS environment; the ConstructiveWorld production face, consumed by tools through hardcoded defaults or auto-detection and itemized in [`docs/clean-mode-manual-20261114.md`](docs/clean-mode-manual-20261114.md) §2; the suite-green claims in this document apply to that environment (see [Testing](#testing)). On a machine without the canonical Coq/Rocq environment, tools whose work depends on that environment report the missing requirement explicitly in English (`requires canonical environment: ...`) instead of failing with an interpreter-level error. Selection is by environment variable:

```bash
ROCWASH_CLEAN=1 python3 tools/<tool>.py ...   # one invocation
export ROCWASH_CLEAN=1                        # or the whole shell session
```

With the variable unset, tools keep automatic environment detection, and behavior on the canonical machine is unchanged. Operation notes: [`docs/clean-mode-manual-20261114.md`](docs/clean-mode-manual-20261114.md).

## Quickstart

First run: scan the bundled demo source for statement-face Prop leakage (measured on this clone, November 14, 2026, rc=0):

```bash
python3 scan/mac_stmt_scan.py --file examples/demo_prop_leak.v
# RED stations: ['demo_eq_self', 'demo_eq_sym', 'demo_le_eq', 'demo_le_self', 'demo_mixed']
```

A "station" is one statement of the scanned file, reported by its declaration name; several findings on the same statement count as one station.

First verification: the comment-hygiene gate on the bundled clean sample (measured on this clone, November 14, 2026, rc=0, PASS=1 FAIL=0):

```bash
python3 verify/gate4_comment_guard.py --file tests/fixtures/gate4_clean_sample.v
```

Token-level census (finds bare constructor references that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```

Main capabilities through the unified entry (examples transcribed from the tools' documented invocation lines):

```bash
# Scan a .v file for Prop leakage, via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against a baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487
# --expect N asserts the extracted statement-name count equals N (487 is an example value)

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing)
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# four-mechanism generation-gap seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json   # first freeze = the certify sub-verb; second = the action name (the pair is freeze|check)
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper: pins git push to a fixed pre-resolved remote address — --pin-ip rewrites the remote URL host to that IP, --url-host keeps the original name as the Host header — so the push does not depend on DNS resolution at push time (dry-run by default; masked output; --yes actually pushes)
python3 watch/watch.py push --repo . --remote origin --pin-ip 140.82.113.3 --url-host github.com  # example value; resolve GitHub's current IP at use time

# Post-push ls-remote double-read confirmation
python3 watch/watch.py confirm --repo . --remote origin --branch main --sha <sha>

# Full-chain demo (scan -> names -> N=N -> wash -> verify)
make -C examples demo

# Compile with thermal guard
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- rocq c -native-compiler no -Q . "" my_proof.v
# -Reg <dir> = a dedicated queue-registration lane; -Front/-Mid = ladder-queue tier cut-offs (FRONT tier runs nice 0, MID tier nice 10) — parameter reference: docs/en/architecture.md §6
```

## Tool map

The table condenses [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md) (one entry per registered tool; the index is the live authority and carries the full seven-field contract and a version-anchor duty). The table does not list every file under `tools/`: `tools/mcp_server.py`, the MCP stdio server (42 capabilities, registered in [`docs/mcp.md`](docs/mcp.md)), and the tools from the newer work streams appear below the table. `tools/cpu_guard.sh`, the thermal wrapper, is documented in [`docs/en/architecture.md`](docs/en/architecture.md) §6. Invocation lines are restored from each tool's argparse or usage text, with prefixes normalized to `python3` (the documented usage strings mix `python` and `python3` - use the interpreter available in your environment); "network" marks the five tools whose source text contains transport-class imports or network-class git subcommands, which therefore need a network window and remote access rights.

| File | Purpose | Example invocation | Network |
|---|---|---|---|
| `tools/_abl1_4b_compile.py` | internal helper: incremental OCaml compilation of an extracted module directory | `python3 tools/_abl1_4b_compile.py <extract_dir>` | zero |
| `tools/_gen_fin_mac.py` | internal helper: renders a probe template into a target-environment form | `python3 tools/_gen_fin_mac.py --source <value>` | zero |
| `tools/_http_backoff.py` | internal shared helper: pure-function HTTP rate-limit backoff, frozen-vector selftest | `python3 tools/_http_backoff.py --selftest` | zero |
| `tools/baseline_diff.py` | compares two baseline files and reports additions and removals (JSON and markdown output) | `python3 tools/baseline_diff.py <old> <new> --json <value>` | zero |
| `tools/chain_graph.py` | merges multiple probe ledgers into a chain-root graph and a ranked list | `python3 tools/chain_graph.py <ledgers> --json <value>` | zero |
| `tools/ci_triage.py` | fetches and triages logs of failing CI runs; `--offline` switches to local log input | `python3 tools/ci_triage.py --offline <value> --logs` | network |
| `tools/contrib_intake.py` | contribution intake inspector: a read-only four-gate check that issues a verdict | `python3 tools/contrib_intake.py --contrib-repo <value>` | network |
| `tools/cw_doctor.py` | aggregate health checker rolling up several domains (environment, network, registry, blockage) | `python3 tools/cw_doctor.py --json <value>` | zero |
| `tools/cw_sentinel.py` | resident real-time watcher over a repo, ledgers, and the build log, emitting a JSONL event stream | `python3 tools/cw_sentinel.py --interval <value> --once` | network |
| `tools/doc_lint.py` | docs-versus-implementation consistency checker: routing tables, the cw.sh routing block, and each tool's `--help` output | `python3 tools/doc_lint.py --repo <value>` | zero |
| `tools/evolve.py` | self-evolution engine v1: drafts evolution proposals from watcher events and ledger files; draft-only, never executes a candidate | `python3 tools/evolve.py --draft-out <value> --suite-now` | zero |
| `tools/ledger_sync.py` | TSV merge synchronizer between the probe ledger and the status ledger | `python3 tools/ledger_sync.py --probe <value>` | zero |
| `tools/net_probe.py` | network-window probe: bare-GET reachability over endpoints for N rounds; stable only after two consecutive all-endpoint passes | `python3 tools/net_probe.py --endpoints <value> --stable-window` | network |
| `tools/netname_normalize.py` | normalizes doubled `.v.v` suffixes (map can be emitted or applied with `--apply`) | `python3 tools/netname_normalize.py --dir <value> --apply` | zero |
| `tools/norm_lint.py` | annotation-face normalization lint, report-first form | `python3 tools/norm_lint.py --tree <value> --selftest` | zero |
| `tools/pushci.py` | one-shot push-then-CI orchestrator: push, ls-remote confirmation, CI watching, verdict reading, and heal rounds | `python3 tools/pushci.py --repo-path <value> --pre-scan-gate4` | network |
| `tools/red_dispatch.py` | red-event dispatcher: routes an event file to preset actions; default zero execution | `python3 tools/red_dispatch.py --event-file <value> --dry-run` | zero |
| `tools/registry_audit.py` | read-only hygiene audit over the two registry files, emitting a deterministic fix plan | `python3 tools/registry_audit.py --order <value> --fix-plan` | zero |
| `tools/registry_fix.py` | applies the fix plan produced by registry_audit (`--apply`; dry-run by default) | `python3 tools/registry_fix.py --audit-json <value> --apply` | zero |
| `tools/registry_regen.py` | regenerates contribution registration rows onto the merge-target line (dry run by default) | `python3 tools/registry_regen.py --base-repo <value> --apply` | zero |
| `tools/registry_union.py` | three-way union merger for the registry (base/main/branch inputs) | `python3 tools/registry_union.py --base <value> --apply` | zero |
| `tools/render_events.py` | renders a JSONL event stream into a markdown ledger | `python3 tools/render_events.py --events <value>` | zero |
| `tools/select_audit.py` | audits a selection list against the tree's order file by full-table grep | `python3 tools/select_audit.py --order <value>` | zero |
| `tools/toolchain_dyld_doctor.py` | diagnoses broken macOS dyld toolchain links (worker/donor locating and a smoke probe) | `python3 tools/toolchain_dyld_doctor.py --worker <value> --smoke` | zero |
| `tools/unclog.py` | blockage-clearing engine for compilation: candidate-chain probing and multi-round clearing (dry-run default) | `python3 tools/unclog.py --src <value> --apply` | zero |
| `tools/vacgen.py` | Lean vacuity probe skeleton generator with a four-layer shape-recognition engine; its zero-compile skeleton-casting mode runs without a Lean environment, the compile-verification leg needs a Lean toolchain | `python3 tools/vacgen.py --in <value> --force` | zero |
| `tools/wash_shape.py` | shape-normalizing five-stage pipeline for annotation-face text (header maps and presets, multi-round loop) | `python3 tools/wash_shape.py --file <value> --apply` | zero |

The Lean-side procedure for vacgen is in [`docs/vacgen_sop.md`](docs/vacgen_sop.md) with an English page at [`docs/en/vacgen.md`](docs/en/vacgen.md). Further reading: bundled full-chain demo [`examples/README.md`](examples/README.md), suite reference [`tests/README.md`](tests/README.md), contribution guide [`CONTRIBUTING.md`](CONTRIBUTING.md), changelog [`CHANGELOG.md`](CHANGELOG.md).

Newer work streams through tag `rw-v0.1.0`: the language-engine tools below all landed through that tag. `tools/ai_flavor.py` runs a 36-face AI-flavor wording battery plus an em-dash battery; `tools/ai_flavor_apply.py` plans advisory rewrites through handoff or HTTP providers (HTTP deny-by-default); `tools/jargon_apply.py` rewrites jargon to standard terms from the 159-entry map; `tools/termbase.py` is a read-only terminology lookup over the seed termbase; `tools/i18n_pipeline.py` orchestrates the zh-en four-linkage pipeline with a policy pre-check; `tools/i18n_translate.py` is the model-stage handoff emitter and ingester with nine-key per-segment annotation; `tools/i18n_verify.py` orchestrates the verification matrix plus the human ten-point gate; `tools/auto_round.py` keeps the round ledger with dual-gear admission, rollback, and salvage. `tools/exp_port.py` appends to the experience ledger (schema rocqwash-exp/1, idempotent), and `tools/periscope.py` collects six-source peripheral intelligence. Engine registration and growth rules live in [`seeds/engines/ENGINES.md`](seeds/engines/ENGINES.md); the per-tool contract face stays [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md).

After tag `rw-v0.1.1-20261117`: the MCP roster expanded in two rounds (work stream 1 at commit `a07403e`, 25 to 31 capabilities; work stream 2 at commit `2220dca`, 31 to 42), and `tools/tree_audit.py` landed a one-shot universal tree-surface audit (a single JSON report over files, bytes, lines, declarations, and the sorry/axiom/native_decide/unsafe counts, with per-directory breakdowns; zero network, zero subprocess, `python -I` safe). The recursive-evolution methodology canon is [`docs/recursive-evolution-whitepaper-v1.0-20261121.md`](docs/recursive-evolution-whitepaper-v1.0-20261121.md). The contract surface [`docs/CAPABILITY-INDEX.md`](docs/CAPABILITY-INDEX.md) was regenerated at anchor `0765d671` (November 20, 2026) and carries 56 tool entries against 60 `.py` files under `tools/` at this writing.

## Testing

```bash
bash tests/run_tests.sh          # exit 0 = all green; any red = exit 1
```

Suite self-check (injects one always-red case to verify the any-red contract):

```bash
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # expected: all cases pass + 1 injected red, exit 1
```

Meta-verification layer: [`tests/test_tool_selftests.py`](tests/test_tool_selftests.py) (suite case `t_tool_selftests`) enumerates every non-helper tool under `tools/` (57 at this writing: 60 `.py` files, 3 `_`-prefixed helpers excluded) and requires each to hold a declared `--selftest` face exiting green or a registered exemption marker; any red, missing, or undeclared face fails the suite loudly. The layer landed at commit `3f781a1`.

Idempotence and zero repository writes are documented suite properties in [`docs/en/architecture.md`](docs/en/architecture.md) §4 (tests row); they are cited here, not re-measured in this document.

Environment limits, stated as recorded rather than as aspirations:

- Scale: the case roster grows with the tree (67 cases at tag `rw-v0.1.0`); [`tests/README.md`](tests/README.md) is the live authority for the case table. Red-set discipline: post-change reds must be a subset of the pre-change roster (zero-new-red; see CONTRIBUTING.md section 4).
- Canonical macOS environment: at the closes recorded in `README.md`'s per-version snapshot entries (v55 through v57, November 13, 2026), the suite measured 62 pass, 0 red, 1 by-design skip (`t_quad8_check`, which needs canonical world copies). Suite-green claims in this document apply to that environment.
- Compile-dependent cases are gated by environment variables (`ROCWASH_ROCQ`, `GATE7_PROBE_SCRIPT`, `GATE6_SCRIPT`, `BORN_WORLD_ROCQ`, per the `README.md` snapshot entry v47, November 12, 2026) and record a SKIP when the gated piece is absent; a SKIP is recorded, never counted as green.
- Windows (Git Bash): on this project's Windows development machine at anchor `090be654`, a full run with a real CPython on `PATH` recorded 44 pass, 15 red, 4 skip, and a same-day repeat run recorded 45 pass, 14 red, 4 skip (one case flipped green between the two runs); the union of both red rosters is these 15 case names: `t_verify_vo`, `t_cpu_guard_direct_smoke`, `t_cpu_guard_direct_rc`, `t_frozen_call`, `t_verify_fresh`, `t_extract_magic`, `t_probe_engine`, `t_toolchain_dyld_doctor`, `t_cw_sentinel`, `t_wash_shape`, `t_unclog`, `t_relay_e2e`, `t_destructive_matrix`, `t_red_dispatch`, `t_registry_audit`. The 4 skips (`t_gate7_wrapper`, `t_quad8_check`, `t_gate6_born_wrapper`, `t_verify_gate6`) need out-of-repo canonical references. No green claim is made for this environment.
- Windows PATH caveat: the suite driver invokes `python3` from `PATH`; on a stock Windows box that name can resolve to the Microsoft Store alias, which exits 49 without running anything and turns cases red without any real output. Put a real CPython on `PATH` first.
- CI: the repository's workflow runs the suite on a single macOS leg; a CI green mark is a suite-level signal on one platform, not a substitute for the environment-specific statements above. The CI failure-class taxonomy for the recursive-iteration era is [`docs/ci-whitepaper-recursive-era-v1-20261116.md`](docs/ci-whitepaper-recursive-era-v1-20261116.md), with the machine-readable triage table [`docs/ci-triage-table.json`](docs/ci-triage-table.json) (version 1.5, classes R1 through R19).

## Honest boundaries

- Hit lists are findings, not verdicts. A "no leakage" verdict may only come from kernel-level census; any zero-hit result is a negative finding whose scope (what was scanned, what was not, which alias forms were not exhausted) is recorded by the emitting tool rather than promoted to an absolute claim.
- Candidates are not verdicts: seam fingerprints and extraction-erasure cluster dispositions are advisory output for human adjudication.
- Judging tools never act: `certify/push_gate.py` judges the push window and never pushes; `watch/watch.py push` defaults to a dry-run and pushes only with `--yes`; `watch/watch.py` contains no rerun or cancel code paths by construction.
- The five network-marked tools listed in the Tool map need a network window and remote access rights; the zero-network readings of the other tools are source-text negative findings, not runtime guarantees.
- Verification coverage is partial by design and recorded as such: `verify/verify_vo.py` covers the compiled-artifact four-pack; the extraction-side three-source conjunction awaits generalization (recorded as pending in [`docs/en/architecture.md`](docs/en/architecture.md)).
- Platform support: macOS is the full-support path (`tools/cpu_guard.sh` reads `pmset`, which is macOS-only); Windows is a Git Bash + python3 light-load path; Linux is unverified by this project's CI and reported as-is.
- `cli/rocqwash` never auto-runs `_`-prefixed internal tools; those carry hardcoded paths and are invoked directly when needed.
- Registry write actions are gated: `registry_audit.py` is read-only, and `registry_fix.py` / `registry_regen.py` / `registry_union.py` dry-run by default with writes only under explicit flags.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for attribution and the authorship statement. Contributions are made under the Individual Contributor License Agreement ([CLA/ICLA.md](CLA/ICLA.md)) before a first merged contribution, and represent substantial human authorship with AI tools allowed as instruments (CONTRIBUTING.md, section 0.5).
