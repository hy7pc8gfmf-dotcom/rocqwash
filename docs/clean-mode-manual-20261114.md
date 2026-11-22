# Clean Mode Manual (ROCWASH_CLEAN=1)

> Purpose.  Document the `ROCWASH_CLEAN` switch of the rocqwash tool repository: what clean mode declares, how default and clean-mode behavior differ, what the canonical environment is, and the four-tier census of canonical-dependency faces (available, skip, degraded, unavailable). Semantic changes ship only through the env form; this manual does not document the `cw.sh` face.
> Interface.  Document face only (this markdown manual). The switch it documents is the `ROCWASH_CLEAN` environment variable (`1` enables clean mode), consumed by the tool suite and the test suite; the manual defines no runtime interface of its own.
> Dependencies.  Faces cited read-only: `tests/run_tests.sh`, `tests/test_clean_mode.py`, `tools/_abl1_4b_compile.py`, `tools/toolchain_dyld_doctor.py`, `tools/cw_doctor.py`, `tools/contrib_intake.py`, `tools/registry_regen.py`, `wash/probe_engine.py`, `wrapper/scan_station.py`, `wrapper/quad8_reconcile.py`, `wrapper/frozen_call.py`, `docs/CAPABILITY-INDEX.md`.
> Evidence.  Version anchor: rocqwash main commit `090be654192aa0ac599b71a945ed7595fc7bc522`, measured locally via `git rev-parse HEAD`, November 14, 2026. The declared wording quoted in section 4 is first-hand observed output (rc=1, observed November 14, 2026). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the exit codes quoted in the text (the exit-9 missing-input family, the `tools/_abl1_4b_compile.py` exit-1 toolchain contract) belong to the documented tools, described as implemented.

---

## 1. Semantics

**Default (env unset or not `1`)**: behavior byte-identical with historical versions; canonical-environment auto-detection stays fully active (it probes the 9.3 multiplexer, the Set repository gate6/gate7 canonical scripts, the CW Live toolchain, and the sanctioned-machine default paths); whatever is detected is used, and an empty detection result yields per the standing skip contract.

**Clean mode (`ROCWASH_CLEAN=1`)**: declares that the canonical environment (the ConstructiveWorld sanctioned-machine face) is absent on this machine:
- canonical-environment auto-detection never runs; the explicit canonical pointers (`ROCWASH_ROCQ`, `GATE6_SCRIPT`, `GATE7_PROBE_SCRIPT`, `BORN_WORLD_ROCQ`, `ROCWASH_CANON_*`) are not applied.
- canonical-dependency faces neither probe nor fail silently: they print `requires canonical environment: <what is missing>` and exit through each tool's standing exit-code family (the six tools use exit 9, the missing-input family; `tools/_abl1_4b_compile.py` keeps its own exit-1 toolchain contract).
- faces without canonical dependencies (selftests, fixtures, dry runs, word-face tools) all stay fully available; every face is listed in the four-tier census in section 3.

Default (env unset or not `1`): byte-identical historical behavior, with canonical-environment auto-detection fully active. Clean mode (`ROCWASH_CLEAN=1`): the canonical ConstructiveWorld environment is declared absent, auto-detection and explicit canonical pointers are not applied, and canonical-dependency faces print `requires canonical environment: <what>` and exit non-zero instead of probing; canonical-free faces (selftests, fixtures, dry runs, word-face tools) stay fully available.

## 2. What the canonical environment is

The ConstructiveWorld production face on the sanctioned machine, consumed by some rocqwash tools through hardcoded defaults or auto-detection:

| Face | Sanctioned-machine path (default) | Consumers |
|---|---|---|
| CW main tree + `cpu_guard` + the Live toolchain | `/Users/apple/Desktop/ConstructiveWorld` | `run_tests.sh` probing, `cw_doctor`, `toolchain_dyld_doctor`, `contrib_intake` |
| Set repository gate6/gate7 canonical scripts | `/Users/apple/Desktop/ConstructiveWorld-Set/scripts/gates/` | `run_tests.sh` probing, `contrib_intake` |
| Main-tree gate4 | `/Users/apple/Desktop/ConstructiveWorld-Main` | the `quad8_reconcile` audit domain |
| Effort workspace (W1 tree / per-call ledger) | `/Users/apple/Desktop/S系Prop清除战役工单` | the `mac_stmt_scan` baseline target, the `frozen_call` per-call-ledger default |
| Four-repository replica group, the `rq` replica | `/Users/apple/Desktop/rocqwash` | the ROOTS registered in `quad8_reconcile` |
| 9.3 multiplexer (rocq/rocqworker) | `/Users/apple/Desktop/mac93_install_work/opam93/rocq93/` | the `run_tests.sh` default probe, the `toolchain_dyld_doctor` default worker |
| PATH toolchain binaries | `rocq` / `coqc` / `coqdep` / `ocamlc` / `otool` | `probe_engine`, `registry_regen`, `_abl1_4b_compile`, `toolchain_dyld_doctor` |

## 3. Canonical-dependency census (four tiers)

### 3.1 Available (full function in clean mode; Python 3 standard library only; the registry tools additionally need `git`)

| Face | Anchor |
|---|---|
| `tools/`: doc_lint, norm_lint, baseline_diff, chain_graph, ledger_sync, netname_normalize, render_events, `red_dispatch`, registry_audit, registry_fix, registry_union, select_audit, vacgen (zero-compile faces) | each tool's `--selftest` frozen vectors |
| `tools/`: ci_triage `--selftest` and `--offline`, net_probe `--selftest`, cw_sentinel `--selftest`, pushci `--selftest`, evolve `--selftest`, registry_regen `--selftest`, wash_shape `--selftest`, unclog `--selftest`, contrib_intake `--selftest`, cw_doctor `--selftest`, toolchain_dyld_doctor `--selftest` | canned injection / temporary fixtures |
| `wash/`: wash_engine, comment_sweep, cure_applier (dry-run face), probe_engine `--selftest`, world_hook; `scan/`: mac_stmt_scan `--selftest` / `--file`, scan_v4_token, dual_scan; `names/`: mac_stmt_names `--expect` | per-case through the suite |
| `verify/`: verify_vo `--selftest`, gate4_comment_guard `--file`, erasure_classifier, extract_magic_check (stub chain), `retrofit_gate7_irr` dry run; `seam/`, `certify/` (freeze_manifest, frozen8, push_gate), `watch/`, `wrapper/` (scan_station, verify_born, quad8 `--selftest` / `--registry`, frozen_call `--selftest`, precedent_station) | per-case through the suite |

### 3.2 SKIP (the suite's standing skip contract; in clean mode these cases skip as usual and do not count as failing)

| Face | Skip-criterion anchor |
|---|---|
| t_gate7_wrapper | tests/run_tests.sh:409 (`CANON` / `GATE7_PROBE_SCRIPT`) |
| t_quad8_check | tests/run_tests.sh:436 (on-volume detection of the four-repository replica directories) |
| t_gate6_born_wrapper | tests/run_tests.sh:450 |
| t_verify_gate6 | tests/run_tests.sh:468 |
| the t_cure_pack compile section and the real-rocq section of t_probe_engine | tests/test_cure_pack.py:492, tests/test_probe_engine.py:259 (gated on `ROCWASH_ROCQ`) |

### 3.3 Degraded (function narrowed, still usable)

| Face | Degraded form | Anchor |
|---|---|---|
| tools/registry_regen.py | falls back to require-edge ordering when `coqdep` is absent | tools/registry_regen.py:341,612 |
| ci_triage `--offline` | the local-log face replaces the pull | the ci_triage entry in docs/CAPABILITY-INDEX.md |
| toolchain_dyld_doctor with explicit `--worker` (and `--smoke` with explicit `--coqc` / `--guard`) | analyzes the given binaries instead of the sanctioned-machine defaults | tools/toolchain_dyld_doctor.py:395-402 |
| quad8_reconcile `--roots-file` | fixture roots replace the registered ROOTS | wrapper/quad8_reconcile.py:583,588 |
| cw_doctor `--injector` | canned four-domain aggregation | tools/cw_doctor.py:1152 |
| contrib_intake gate7 availability face | records only an availability boolean, executes nothing | tools/contrib_intake.py:703-716 |

### 3.4 Unavailable (clean mode declares `requires canonical environment` explicitly, exit 9; the tool noted in the last row exits 1)

| Face | Declared content | Implementation anchor |
|---|---|---|
| mac_stmt_scan `--baseline` | the S09 worldT_mac baseline target in the effort workspace (general scans go through `--file`; the canonical target passes the `wrapper/scan_station.py` check; the canonical target itself is frozen and must not be edited; a direct call to the canonical target runs outside the check and reports through the standing missing-target contract) | `wrapper/scan_station.py` (the check before pass-through) |
| the toolchain_dyld_doctor default worker chain | the sanctioned-machine rocqworker default (`--worker` / env can bypass it) | tools/toolchain_dyld_doctor.py (at worker resolution) |
| cw_doctor real four-domain aggregation (without `--injector`) | the CW Live tree (guard default / the registered ledger / the probe world) | tools/cw_doctor.py (the check after run() value validation; the usage-face exit codes are untouched) |
| probe_engine real compile probe | the rocq toolchain (the default `--rocq-cmd` template is the real face; an explicit `--rocq-cmd` stub and `--selftest` stay available) | wash/probe_engine.py (the check after required-parameter validation) |
| quad8_reconcile `freeze` / `check` (without `--roots-file`) | the registered four-repository canonical replica group | wrapper/quad8_reconcile.py (the check before routing) |
| frozen_call real invocation face | the default in-repository frozen-name list or the effort per-call ledger (call sites passing `--manifest` and `--log` explicitly keep their own face) | wrapper/frozen_call.py (the check after the selftest branch) |
| _abl1_4b_compile | the OCaml toolchain (ocamlc/ocamldep via opam env) | tools/_abl1_4b_compile.py (the import-time toolchain check) |

Suite level: in clean mode the canonical-detection block of `tests/run_tests.sh` (the `CANON` decision plus the `ROCWASH_ROCQ` / `GATE7_PROBE_SCRIPT` / `GATE6_SCRIPT` / `BORN_WORLD_ROCQ` default assignments) is skipped as a whole, and each case in 3.2 skips under its standing contract.

## 4. Usage

```sh
# Full suite in clean mode (canonical-dependency cases skip)
ROCWASH_CLEAN=1 bash tests/run_tests.sh

# Single face: clean-mode liveness check
ROCWASH_CLEAN=1 python3 -B tests/test_clean_mode.py

# Single-tool example: in clean mode the real compile face declares itself
# (observed November 14, 2026, rc=1; the declared wording is transcribed below)
ROCWASH_CLEAN=1 python3 tools/_abl1_4b_compile.py
  requires canonical environment: the OCaml toolchain (ocamlc/ocamldep on PATH via opam env)
```

## 5. Boundaries

- Clean mode governs the canonical-environment face only; the network face (the pull and push of `ci_triage` / `cw_sentinel` / `pushci` / `net_probe`) is governed separately by the standing NETRED discipline, and `ROCWASH_CLEAN` does not turn the network off.
- Clean mode does not change any exit-code family semantics: declaration exits reuse each tool's standing missing-input code; no new exit code is introduced.
- `git` is a baseline dependency of the registry-family tools (not a canonical face); clean mode does not exempt it.
- The switch governs the canonical-environment face only; the network face stays under the standing NETRED discipline, and no exit-code family is redefined.
