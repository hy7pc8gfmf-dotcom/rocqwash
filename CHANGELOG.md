# Changelog（对外可见器面变更总账 · public tool-face change ledger）

> **CHANGELOG.md**: the distilled, reader-facing change ledger of the rocqwash
> tool faces, Keep-a-Changelog style; the `[Unreleased]` section distills the
> key points of the v35-v39 work streams.
>
> Purpose.  Index the repository's user-visible changes on one public surface.
>   Per-round detail lives in `更新账.md` and in each tool's docstring /
>   `--help`, which remain the authoritative records; this file is a
>   distillation index only, and a disagreement with a tool is a bug (same
>   rule as CONTRIBUTING §1.5).
>
> Interface.  Markdown prose face, read by repository readers and graded by
>   `tools/norm_lint.py` under `docs/annotation-standard-v1.0-20261113.md`.
>   Section headings carry the version, the date and the commit hash; version
>   numbers follow the repository's vNN work-stream convention.
>   `[Unreleased]` is the standing section.
>
> Dependencies.  Plain Markdown only; no execution surface. The
>   pre-translation Chinese original is preserved in the sibling archive
>   `CHANGELOG.md.zh.md`.
>
> Evidence.  Every entry names the tool paths, schema names, suite counts and
>   commit hashes of the round it describes, so each claim can be checked
>   against the cited tool face or the cited test roster.
>
> Exit-codes.  Not applicable: this face carries no execution surface; the
>   tools it indexes keep their own 0/1/2/9 exit-code contracts.

## [Unreleased]

### v35: CI diagnostics toolchain work stream (2026-11-11 · acf9fe6)

**Added**

- `tools/toolchain_dyld_doctor.py`: diagnostic tool for dyld toolchain
  linkage failures: parses the `otool -L` external hard references of
  `rocqworker`, judges each entry exists/missing, traces a missing item back
  to its donor root, and only prints restore suggestions; never executes
  them; optional `--smoke` smoke check (SMOKERC plus the `.vo` magic-number
  report); schema `rocqwash-dyld-doctor/1`; exit codes 0 healthy / 1
  missing-libs / 2 usage / 9 the worker or `otool` missing.
- `tools/net_probe.py`: network-window probe of the upload endpoints: plain
  GET requests to the four default endpoints (an `HTTPError` 500/400 means
  the stack is up, so reachable equals healthy; `URLError` or a timeout means
  unreachable); the two-probe stability-window rule (STABLE only after two
  consecutive all-passing rounds; a single-probe round must not initiate).
- `tools/ci_triage.py`: CI failing-build triage tool: the five-family
  classification spectrum (A content-red / B NETRED / C toolchain break /
  D queue-resource wall / E coqchk-skipped) plus the watch-only action for
  all-passing runs; UNRECOGNIZED is never forced into a family;
  classification order UNRECOGNIZED > C > A > E > B > D; `--logs` prints the
  thirteen key-line families; a failing result is data, not a tool failure.
- `tools/registry_union.py`: registry union-operation tool: main is the
  base and rows unique against the merge-base are appended at the end;
  A1/A2/A3 fail-loud assertions; `--reanchor` md5-8 canonical form; CRLF
  preservation; dry run by default, writes only under `--apply`.

**Changed**

- `cw.sh` gains the doctor/net-probe/triage/union routes (eleven tools); the
  passthrough contract is untouched; the local mapping cw_paths goes
  v1.0→v1.1 (eight new root sections plus a moved-root watch list).
- Self-test suite 47 cases (43 pass / 0 failing / 4 SKIP · EXIT 0).

### v36: orchestration layer: the pushci single-command pipeline (2026-11-11 · 4026051)

**Added**

- `tools/pushci.py`: post-fix push-and-CI single-command pipeline (five
  stages: preflight doctor + net_probe checks + optional gate4 header-comment
  prescan → push over HTTP/1.1 with up to three attempts plus ghproxy
  reroute → resolve + watch (keyed on head_branch + head_sha) → heal
  (ci_triage classification routing, rerun capped at 3) → verdict ± merge
  (409 re-pulls the tip, retried ≤3)). The v35 tools are orchestrated through
  subprocess with zero new engines; the verdict set has seven states
  (success/dry-run=0 · heal-exhausted/unstable/toolchain=1 ·
  fix-content/gate4-block=2 · 9=target missing).
- `tests/test_pushci.py` + six-scenario canned fixtures (the passing path /
  NETRED healing / content-red with zero reruns / heal exhausted / merge 200
  / dry-run zero side effects) · 15 pass / 0 failing; the offline-testability
  hard requirement: `--injector` in both forms paired with `--git-caller`,
  `--sleep-scale 0`, and a bit-for-bit differential comparison of the
  api_calls/git-caller call streams.

**Changed**

- `cw.sh` twelve tools; the README-cw.md main pipeline upgrades to
  doctor→net-probe→pushci→triage (honest side note: the four push-window
  criteria still belong to `certify/push_gate.py`; the two doors stand side
  by side).
- Self-test suite 48 cases (44 pass / 0 failing / 4 SKIP).

### v37: service layer: three realtime-status tools (2026-11-11 · 41e74b0)

**Added**

- `tools/unclog.py`: closed-loop engine for clearing blockages: probes are
  collected → chain_graph locates the chain roots (self-washable judgment; a
  frozen8 refusal is fail-closed) → cure_applier applies the canonical pack
  only → scan_v4 rescans and the probe re-probes (md5-keyed) → verdict
  unclogged / wall (the honest wall verdict: each root lists its causes and a
  forced fit is forbidden) / rounds-exhausted; dry run by default; under
  `--injector` canned probes the chain/cure/scan/frozen8 stages still really
  run (a real orchestration, no stand-ins).
- `tools/wash_shape.py`: shape-normalizing tool · the canonical five-wash
  pipeline (lexical / token / header-shape / line-ending / anchor washes):
  plan and apply as two stages; plan writes nothing by default; after apply
  all five washes re-run for verification → shaped / partial as measured;
  the frozen roster is excluded automatically and an explicitly named frozen
  target is refused.
- `tools/cw_sentinel.py`: the realtime-status watcher: three signal sources
  (a new failing CI build → ci_triage classification / new local blockage
  records → chain_graph TOP / incremental build-log token surface) → a JSONL
  event stream (append + fsync + stdout mirror); `--state-file` makes the
  seen state idempotent; report-only by default with zero actions.
- The five interface disciplines run through all three tools: schemas
  designated (`rocqwash-unclog/1` · `rocqwash-shape/1` ·
  `rocqwash-sentinel/1`) · exit codes 0/1/2/9 (a failing result is data, not
  a tool failure) · `--once/--loop` dual mode · `--injector`/`--sleep-scale`
  offline testability · orchestration with zero new engines (all subprocess).

**Changed**

- `cw.sh` fifteen tools; README-cw.md gains a "workflow cooperation
  interface" section (the five disciplines at a glance + three typical
  background-watcher command lines + three typical workflow embedding blocks
  for pushci/unclog/wash_shape).
- Self-test suite 51 cases (47 pass / 0 failing / 4 SKIP).

### v38: docking and health-check layer (2026-11-11 · c205ea0)

**Added**

- `tools/cw_doctor.py`: composite health-check tool aggregating four
  domains: environment (dyld doctor) 40 / network (net_probe) 20 / register
  (order.txt anchor canonical-form audit) 25 / blockages (probe sampling →
  chain_graph TOP) 15 → a composite health score 0-100 plus verdict
  healthy/degraded and advice pointing each non-passing domain to its tool;
  diagnosis only, never execution on the tool's behalf; `--injector` makes
  it offline-testable (a missing key exits 9 and never silently runs for
  real).
- `tools/_http_backoff.py`: resilience-layer shared module: exponential
  backoff on 403/429/5xx (honors the Retry-After seconds header; 4xx
  semantics are not retried) shared by ci_triage / cw_sentinel / pushci;
  injector canned paths never retry and never touch the real network.
- Three canonical embedding blocks under `examples/workflows/`
  (backend-sentinel / step-pushci / loop-unclog; the samples were produced
  by real tmp-injection drills, not hand-written) +
  [`docs/workflow-integration-whitepaper-v1.0-20261111.md`](docs/workflow-integration-whitepaper-v1.0-20261111.md)
  (the five disciplines / the three embedding blocks / the five mechanisms
  for background tasks yielding to the interactive session / push_gate's
  four push-window criteria × the pushci preflight check; the dual-door
  arrangement).

**Changed**

- cw_sentinel gains `--on-red-preset` (preset unclog = dry-run
  clear-blockages / pushci = dry-run · the same executor as `--on-red`, zero
  new paths · the two are mutually exclusive rc=2 · `--on-red-arg K=V`
  passthrough).
- unclog gains `--audit`, the read-only blockage-record baseline (zero-write
  hard guarantee = the `--src` whole-file md5 proves itself identical before
  and after the run · mutually exclusive with `--apply`/`--loop`, rc=2 · the
  timing section is the only non-deterministic section).
- Hang-prevention caps: pushci `--timeout` · cw_sentinel `--subproc-timeout`
  (default 120s · on timeout, kill + fail-loud with the callee named);
  net_probe gains `--jitter/--seed` (spreads out retry storms · a fixed seed
  is deterministic).
- `cw.sh` sixteen tools; self-test suite 52 cases (48 pass / 0 failing /
  4 SKIP · the baseline regression is equally passing before and after the
  change).

### v39: corpus rolling-expansion work stream · document close-out (2026-11-11 · caa3a28)

**Added**

- `tests/fixtures/header_map_v1.json`: header template library v1 (preset
  `campaign_set_diamond` · distilled from the Set repository's
  canonical five-field form · six placeholders, each carrying its citation ·
  body content is never synthesized; a missing evidence entry refuses the
  load; "evidence required before issuance" is enforced by the code;
  schema `rocqwash-header-map/1`).
- `tools/doc_lint.py`: the doc-vs-implementation consistency checker with
  three checks: (1) the four cw.sh tool tables cross-checked and reconciled
  against the tools/ generic entry points; (2) the CASES vs tests/README.md
  vs README.md counts reconciled at all three sites; (3) every doc-cited
  flag checked one by one against each tool's real `--help` output; schema
  `rocqwash-doclint/1` · verdict consistent|drift (a failing result is data,
  not a tool failure · loud stdout).
- `tests/test_relay_e2e.py`: the cw_sentinel `--on-red-preset unclog`
  end-to-end three-check (event trigger / unclog dry run rc=0 zero writes /
  JSONL same-disk report path) +
  [`docs/ops-realtime-service-v1.0-20261111.md`](docs/ops-realtime-service-v1.0-20261111.md)
  runbook (standard background-watcher commands and JSONL usage / the three
  on-red preset forms side by side / the live-tree run procedure: audit
  baseline → human review → apply allowlist / interactive-session-yield
  coordination).

**Changed**

- `wash/cure_pack.json` v1.3→v1.4 (24→25 forms): evidence-gated expansion:
  a three-source survey produced 11 candidates and 1 form was accepted
  (cure39_ifq_connective_qualify · citing the Set-repository wash pass
  anchor commit `9a51c74`, the diff checked verbatim across 25 stations) ·
  10 rejected with a per-item reason (prefer no cure over a weak cure,
  enforced in code).
- wash_shape gains `--header-map-preset NAME` designated-template wiring
  (the same slot as `--header-map`, mutually exclusive rc=2 · template
  source probing order `--header-map` > preset > env).
- `cw.sh` seventeen → nineteen tools: the doc-lint route plus the
  netname-normalize and select-audit routes complete the roster (doc_lint's
  first real-repository run reported drift=3; the decision was to fill the
  gaps rather than keep a separate register · six sync sites); doc_lint's
  re-run is consistent with drift=0.
- Self-test suite 54 cases (50 pass / 0 failing / 4 SKIP).

> [Unreleased] note: the five v35-v39 work streams all landed on 2026-11-11
> and shipped with the repository's mainline evolution without a separate
> release; the next work stream v40 (canonicalization consolidation) is
> scheduled (long-run vectors + frozen-face recheck + full INDEX/README
> table alignment + the push_gate dual-door normalize assessment; see the
> v39 pending items in `更新账.md`).

### v53: comment-face normalization work stream: annotation card + norm_lint + entry-face / four-tool anglicization (2026-11-13 · unreleased, working tree only)

**Added**

- `docs/annotation-standard-v1.0-20261113.md`: the annotation standard card
  v1.0: the two-part header (banner + the five fields
  Purpose./Interface./Dependencies./Evidence./Exit-codes. verbatim) + the
  four forbidden-word families + the bilingual transition rules
  (translation-replacement is canonical; the original Chinese goes into a
  `.zh.md` archive instead of being deleted; code identifiers / CLI flags /
  JSON schema fields / exit-code semantics are never changed) + the
  error/warn grading and the checker's exit-code contract (0/1/2/9).
- `docs/jargon-to-standard-mapping-v1.md`: the jargon-to-standard mapping
  table v1 (the card's Appendix A · 142 active faces = the core 16 rows +
  the JARGON v0.9/v1.1 base carry-over + the tool-repository sweep expansion
  + the phrase-level rows + the English colloquial family · per-row context
  notes · the identifier-exemption register).
- `tools/norm_lint.py`: the annotation-face normalization checker,
  report-only first form: `--tree`/`--file` scans .py/.sh/.md prose faces ·
  five checks (header shape / jargon faces / CJK residue / forbidden classes
  / header line budget) · schema `rocqwash-norm-lint/1` · findings are data
  and the exit code never escalates on them (0/1/2/9) · `--selftest` six
  vectors · `*.zh.md` and `docs/zh/` archive faces are exempt from scanning.
- `docs/zh/ci_triage-docstring.zh.md` and siblings; the Chinese docstring
  originals of the four core tools archived (cw_sentinel / pushci / unclog /
  ci_triage · extracted programmatically, verbatim) plus the
  `README-cw.zh.md` / `cli/rocqwash.zh.md` bilingual-transition archives.

**Changed**

- Entry faces anglicized (translation-replacement, zero interface change):
  the header/help faces of `cw.sh` / `cli/rocqwash` / `README-cw.md`
  rewritten in English with identifiers / flags / exit codes byte-identical;
  the module docstrings of `tools/ci_triage.py` / `tools/pushci.py` /
  `tools/unclog.py` / `tools/cw_sentinel.py` anglicized (the inline-comment
  residue is registered as-is and forms the recursive-reduction baseline).
- `cw.sh` twenty-five tools: the norm-lint route is registered (six sync
  sites); the README-cw.md tool table gains the norm-lint row.
- `tools/doc_lint.py`: DEFAULT_HELP_CAP 24→25 (after norm_lint registered,
  25 tools; the cap overflow, probe_engine, rotates per the same precedent
  as v38/v46); doc-face collection exempts the `*.zh.md` and `docs/zh/`
  archive faces from scanning (archive files are not canonical faces,
  annotation card §5.2).
- tests/: the t_norm_lint hookup (`tests/test_norm_lint.py`, a minimal
  selftest shell with three checks) · self-test suite 59→60 cases; the
  README.md / tests/README.md count lines synced.

**Verification**

- The repo-wide norm_lint baseline ledger (`--tree` over the whole
  repository · no allowlist · the state as measured): files=140 · error=2441
  · warn=1036 · cjk_ratio=0.248597 · byte-identical on an identical-input
  rerun (`docs/norm-lint-baseline-20261113.{json,md}`).
- doc_lint consistent (help_run=25/25 · drift=0); the full suite green twice
  (60 cases: 59 pass / 0 failing / 1 skip ×2); `bash -n` passes on all .sh;
  the final jargon scan's registered remainder: about 26 narrative entry-face
  wordings cleared (work stream / effort / agent narratives · date stamps ·
  `seat` names · narrative-sense `dispatch` rewrites), the remainder registered
  honestly = the identifier-citation class (the cw.sh `dispatch` route name
  ×5 · README-cw.md example commands / doc-link filename dates ×6 · the
  cli/rocqwash `retrofit` sub-verb name ×4) + the four tools' inline-comment
  residue (jargon 2-14 · cjk_ratio 0.11-0.19).

### v58: self-evolution guardrail work stream: wash-map self-reference guard (2026-11-16)

**Fixed**

- `docs/jargon-to-standard-mapping-v1.md`: restored the 27 rows rewritten by the
  `e04f2f6` E2 jargon mechanical pass (`absorb`→`并入`, `finally established`→`已证结论`, `splice`→`splice`
  and 24 more). That pass rewrote the banned faces *themselves* inside the
  mapping table, which (a) dropped 11 of the 13 faces the seed contract says
  this table supplies (liquidated/thinned/machine ruling/delisted/credit tally/splice/double failure/cyclic account/unloaded/shot down/overturned)
  and (b) wrote plain English standard terms into the face column of 10 rows,
  so `norm_lint`'s default map started treating delisted / machine ruling /
  cyclic account and 7 more ordinary English phrases as banned jargon. After
  the restore the file md5 is exactly the seed-pinned value
  `9440fbd102187e15e01183e853242e30` (the seed needs no edit), the contract
  faces are back 13/13, and every corrupted English face is gone from the
  loader.
- `tools/jargon_apply.py`: new **self-reference guard**; the wash map's own
  source table (`--a2-table`, default
  `docs/jargon-to-standard-mapping-v1.md`) is never a wash target. `--tree`
  excludes it from the target set; `--file` on it is refused rc=1 loud. This
  closes the recurrence vector: before the fix `--tree . --plan` still
  reported would_fix=28 on that table (the next autonomous round would have
  washed its own map source again); after the fix the table leaves the scan
  face (files 232→231, would_fix 73→45).

**Added**

- `tests/test_destructive_matrix.py`: destructive-surface matrix gains row J1
  ("wash-map self-reference guard": tree exclusion + file refusal, both paths
  zero-write). The matrix goes 22→23 rows.

**Verification**

- Full local suite: 72 pass / 5 red / 4 skip over 81 cases (before the fix:
  70 pass / 7 red). All 5 remaining reds are platform-dependent and sit in
  the CI Linux/Windows platform roster (t_cpu_guard_direct_smoke /
  t_cpu_guard_direct_rc / t_extract_magic / t_probe_engine /
  t_toolchain_dyld_doctor).
- `t_engines_body` 60/60 green and `t_engines_seeds` 42/42 green (both were
  red on the `jargon/snapshot-md5` drift).
- Destructive-surface matrix 23/23 green (new row J1 PASS).

### v59: platform-reproducible CI work stream: three independent red causes (2026-11-16)

CI was red on all three hosted platforms (runs #89/#90/#91) for three
independent reasons, none of them caused by the v58 wash-map fix.

**Fixed**

- `tools/bus_feeder.py`: the selftest located its scratch directory through
  `TMP` or `TEMP` only and exited 9 when neither was set. GitHub runners
  expose `RUNNER_TEMP`/`TMPDIR`, not `TMP`, so `t_bus_feeder_shape` failed on
  every POSIX runner while passing on Windows (where `TMP` always exists).
  The scratch root now falls back through TMP/TEMP/TMPDIR to
  `tempfile.gettempdir()`.
- `certify/frozen8.py`: selftest judgment 9 amends a scratch commit and
  expects the git-anchor ring to report drift. An amend integration inside the
  same commit-timestamp granularity as the original commit reproduces the
  identical SHA (same tree, same message, same author and committer second),
  so no drift is visible and the assertion fails on fast machines (observed on
  the Linux and Windows runners). The amended commit now carries a pinned
  author date, so the new SHA cannot collide with the original.
- `.gitattributes` (new): the Windows checkout is CRLF while every committed
  blob and every recorded md5 pin is LF, so the byte-level assertions never
  matched the committed bytes; fourteen cases red on the Windows lane
  (t_gate4_clean, t_wash_judgments, t_wash_engine, t_scan_station,
  t_verify_born, t_frozen8, t_frozen8_check, t_frozen_call, t_world_hook,
  t_select_audit, t_recipe_s07, t_recipe_pw1, t_precedent_station,
  t_netname_normalize). The checkout is now pinned to LF on every platform.
  Every blob in the repository is already LF, so there is no renormalization
  churn.

**Added**

- `.github/workflows/ci.yml`: a local self-hosted lane
  (`runs-on: [self-hosted, Windows, X64]`, runner LIVE-ROCQWASH on this
  machine) runs the same stable roster locally instead of on a hosted runner,
  so a long suite is not bound by the hosted runner's job duration wall and a
  flaky hosted runner cannot block the signal.

**Verification**

- CI-shaped reproduction (a fresh clone with the system `core.autocrlf=true`
  setting: the checkout is LF only because of the new `.gitattributes`): the
  local suite went from 60 pass / 17 red / 4 skip to 70 pass / 7 red / 4 skip.
  Six of the seven remaining reds are platform-dependent and already sit in
  the CI Linux/Windows platform roster; the seventh (`t_frozen8_check`) was
  caused by this work stream's own edit to `certify/frozen8.py` and was closed by
  re-issuing the frozen roster through the tool's own `freeze` face
  (idempotent replay byte-identical, `frozen8 check` OK, 0 changed).

### v60: Windows stdout-codepage work stream: UTF-8 I/O forced on every lane (2026-11-16)

After v59 the macOS and Linux lanes were green, but both Windows lanes were
still red; the hosted one across 34 cases, the local self-hosted one across
5.

**Fixed**

- `.github/workflows/ci.yml`: Windows runners default to an ANSI stdout
  codepage (charmap on the hosted image, gbk on a zh-CN host). The suite
  prints Chinese prose and math symbols, so `print()` raised
  `UnicodeEncodeError` and took whole cases down with it; the hosted Windows
  lane lost 34 cases to it. Both jobs now set `PYTHONIOENCODING=utf-8` and
  `PYTHONUTF8=1`. Reproduced byte-identically before the fix
  (`PYTHONIOENCODING=gbk` raises `UnicodeEncodeError: 'gbk' codec can't
  encode character '\u2282' in position 59`, the same message the runner
  logged).
- `verify/erasure_classifier.py`: the selftest wrote its scratch file to the
  hardcoded POSIX path `/tmp/erasure_selftest_<pid>.mli`, which does not
  exist on a Windows runner. It now uses `tempfile.gettempdir()`.

### v61: Windows lane closure work stream: quoting, autocrlf and encoding (2026-11-16)

After v60 the macOS and Linux lanes were green and the hosted Windows lane
had dropped from 34 red cases to 2, with one more red on the local
self-hosted lane.

**Fixed**

- `wrapper/frozen_call.py`: the child was launched with `os.execv(argv[0],
  argv)`. On Windows `os.execv` rebuilds the command line by joining the argv
  with spaces and does not quote it, so an interpreter path containing a space
  (`C:\Program Files\Python313\python.exe`) was split and the child died on
  `argv[0]="C:\Program"` ("can't open file '...Files\Python313\python.exe'").
  The child is now spawned through the list form, which keeps the exit-code
  passthrough without the quoting hazard.
- `tools/registry_regen.py`: the CRLF-preservation vector of the selftest
  builds a scratch git repository whose base books carry CRLF and asserts the
  regenerated draft preserves it. On a Windows host whose git has
  `core.autocrlf=true` the CRLF base books are normalized to LF on commit, so
  the vector failed for a reason that has nothing to do with the tool. Every
  git call of the selftest now runs with an injected `core.autocrlf=false`
  (config injected into the environment, not written into the repository).
- `tests/run_tests.sh`: the suite entry point now exports `PYTHONIOENCODING`
  and `PYTHONUTF8` itself, so the UTF-8 guarantee holds for every caller and
  not only for the CI job environment.
- `tests/t_engines_body.py`: `base_env` forces the same two variables into
  every child it spawns, so a child that prints Chinese prose or math symbols
  cannot die with `UnicodeEncodeError` on an ANSI-codepage host.

### v62: isolated-mode encoding work stream: `-X utf8` reaches every child (2026-11-16)

**Fixed**

- The encoding guarantee from v60 did not reach the children: Python's
  isolated mode (`-I`) implies `-E`, which ignores every `PYTHON*`
  environment variable; so `PYTHONIOENCODING` and `PYTHONUTF8` were dropped
  exactly where they were needed, in the children that print Chinese prose or
  math symbols. The hosted Windows lane still raised
  `UnicodeEncodeError: 'charmap' codec ...` and the `norm_lint` selftest
  reported zero PASS lines.
- `-X utf8` is a command-line switch, so `-E` cannot discard it. Five test
  files already used that form (`t_bus_feeder_shape`, `t_periscope_shape`,
  `t_symbiosis_shape`, `t_uplink_shape`, `t_evolution_dashboard_shape`); this
  extends the same form to the remaining 29 isolated-mode call sites across
  18 files, so the whole repository now spawns children in UTF-8 mode. The two
  non-Python `-I` sites (the `ocamlc` include-directory flag in
  `verify/extract_magic_check.py` and `tools/_abl1_4b_compile.py`) are left
  untouched.

**Verification**

- CI run #95 on `b9dd1a7`: **success**. All four blocking lanes green;
  Self-test suite (macOS), (Linux), (Windows) and
  (Windows (local self-hosted), the runner LIVE-ROCQWASH on this machine).
  The two platform-sensitive roster watch jobs stay red by design (they run
  exactly the cases the blocking roster excludes, and the job carries
  `continue-on-error: true`).

### v63: platform-sensitive roster work stream: guard exit-code passthrough (2026-11-16)

The two platform-sensitive roster watch jobs stay red by design (they run
exactly the cases the blocking roster excludes). Two of their reds were real
defects rather than environment noise, and are closed here.

**Fixed**

- `tools/cpu_guard.sh`: the guard launched the wrapped command through
  `taskpolicy`, which is a macOS-only binary. On a Linux or Windows host the
  command is not found, so the shell reported 127 and the wrapped command's
  real exit code was swallowed; the probe's "the guard must pass the child's
  exit code through unchanged" judgment saw 127 where it expected 7. The
  guard now degrades in steps (taskpolicy → nice → direct exec); every step
  still passes the child's exit code through unchanged.
- `tools/toolchain_dyld_doctor.py`: the selftest injects a canned `otool`
  written as a POSIX shell script. A Windows host cannot execute it (chmod
  does not set the execute bit there), so the CLI vector failed for a reason
  that has nothing to do with the tool. The selftest now reports the honest
  skip (rc 111) on a non-POSIX host instead of a false red.
- `tests/test_toolchain_dyld_doctor.py`: the harness still judged that
  honest skip as a failure, because it only accepted rc=0 plus the pass
  marker. It now accepts rc 111 with a skip banner and exits 111 itself, so
  the suite records the case as SKIP (the suite's standing rc 111 contract)
  rather than red.

### v65: probe engine: Windows path folding and timeout visibility (2026-11-16)

**Fixed**

- `wash/probe_engine.py`: the probe command template was handed to `bash -c`
  as text, and a backslash inside that text is an escape character to the
  shell, not a path separator. A Windows path in the template was folded into
  a different word (`C:\a\b.sh` -> `C:ab.sh`), the command was not found, and
  every candidate was recorded as `RED-UNKNOWN` with rc 127. The MSYS runtime
  rewrites an argv path to forward slashes by itself, but not a path embedded
  in the text of `bash -c`. Drive-letter paths in the template, in the guard
  path and in the guard registry are now rewritten to forward slashes before
  they reach the shell; a POSIX path, a shell escape and a non-path `C:` text
  are left alone.
- `wash/probe_engine.py`: the probe command is a shell line, so the compiler
  it runs is a grandchild of the probe process. On a timeout only the direct
  child was killed, leaving that grandchild alive with the write end of the
  captured pipes still in its hands; the interpreter then waited for the pipe
  to reach EOF, so a 2s timeout was reported only after the grandchild's own
  lifetime (30s) had elapsed. The probe now runs in its own process group
  (Windows: a new process group) and a timeout reaps the whole tree, so the
  timeout is observable when it happens.

**Tests**

- `tests/test_probe_engine.py` grew two regression sections (9 -> 11): the
  drive-letter path in a command template must reach the stub (rc 0, not
  127), and a timeout must be visible at the deadline. The first also pins
  that the rewrite touches nothing but drive-letter paths.

### v64: destructive-matrix write-face judgment: git metadata out of scope (2026-11-16)

**Fixed**

- `tests/test_destructive_matrix.py`: the write-face judgment compared a full
  directory manifest, `.git` included. Git legitimately rewrites its own
  metadata (reflog, index, gc.log) when it resolves HEAD or refreshes the
  index, so on a runner whose git touches that metadata during the freeze the
  row read it as "the freeze wrote outside its write face" and went red
  (observed on the macOS lane; the judgment passed on every other platform and
  in every earlier run, which is what made it a flake rather than a defect).
  The manifest now skips the `.git` directory, so the row states what it
  means: the tool's own write face. The rows that guard git-object writes
  assert on the object store explicitly.

### v66: flaky quarantine guard: order-dependence repair class E2-3 (2026-11-16)

**Added**

- `tools/flaky_guard.py`: the class-③ guard of the E2 repair family.
  `--detect` classifies every red case in a suite log by an isolation
  probe (`ROCWASH_TESTS_ONLY=<case>`): suite-red plus alone-green is
  order-dependent quarantine material; red in both contexts is content
  red that stays visible (recorded, never hidden).  `--move --apply`
  writes the case into `tests/advisory_roster.txt` (the default suite
  then drops it with a loud `ADVISORY-OUT` line and the CI flaky-watch
  job keeps running it in a new advisory observation step), appends a
  `rocqwash-repair-ledger/1` repair row (class/target/outcome), and is
  budget-capped at two repairs per class per branch.  `--restore`
  returns a quarantined case only with green-round evidence (default
  three rounds; the CI-level cross-platform rule stays with the watch
  lane).  Dry run is the default; both write faces are scope-checked
  against `tools/repair_scope.py` and a frozen or out-of-scope target is
  refused loudly.  The sandbox `--selftest` carries 32 vectors over a
  tmp mini-suite; zero real-repo writes.

- `tools/repair_scope.py`: the shared exclusion single source for the E2
  guard family (the lane-extract work stream cast the core: runtime
  LEDGER8/CHECKERS rows via an AST read of `certify/frozen8.py`, the
  append-only ledger document, the frozen directory families); the
  flaky-quarantine class appends its provider scope in the marked append
  zone (read-merge-write, idempotent).

- `tests/run_tests.sh`: the advisory-roster hookup in the selection
  block.  Rostered cases are dropped from the default selection with a
  loud `ADVISORY-OUT` line; `ROCWASH_TESTS_ONLY` wins over the
  quarantine (a watch lane can name a quarantined case explicitly);
  unknown advisory names print one loud note and are ignored.  With an
  empty roster the default run is byte-identical to before.  Case count
  81 -> 82 (`t_flaky_guard` shell hookup; counts synced in
  `tests/README.md` and `README.md`).

- `.github/workflows/ci.yml`: the flaky-watch job gained an advisory
  "Observe advisory roster (flaky quarantine)" step (continue-on-error)
  plus a verdict line, so a quarantined case is watched, never silently
  hidden.
