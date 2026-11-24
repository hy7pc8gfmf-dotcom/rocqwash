#!/bin/bash
# run_tests.sh — rocqwash tests/ self-test suite entry point
#
# Purpose.  Run the statically rostered 89-case suite one case at a time with a
#   per-case PASS/FAIL/SKIP line and a final summary; all green exits 0, any red
#   exits 1.  Idempotent: zero bytes written into the repository, byte-identical
#   reruns; sole exception: ROCWASH_GATE_LEDGER_DIR opts into the gate-ledger
#   append face, which writes only under that caller-designated directory.
#
# Interface.  bash tests/run_tests.sh; ROCWASH_TESTS_FAIL_PROBE=1 bash
#   tests/run_tests.sh injects one always-red case (suite self-check; must exit 1);
#   ROCWASH_TESTS_ONLY / ROCWASH_TESTS_EXCLUDE select cases; ROCWASH_ADVISORY_ROSTER
#   points at the flaky-quarantine roster; ROCWASH_CLEAN=1 disables canonical
#   auto-detection; ROCWASH_PY overrides the interpreter; ROCWASH_GATE_LEDGER_DIR
#   names a standing gate-ledger directory (set: one summary row lands under it
#   per run, the ledger the evolve --gate-ledger-dir reading parses; unset:
#   nothing written).  Exit-code contract per CONTRIBUTING section 4.
#
# Dependencies.  bash 3.2+ and python3; the rostered test faces under tests/;
#   the canonical pointers ROCWASH_CANON_SET / ROCWASH_CANON_CW / ROCWASH_CANON_W1
#   and the guarded compile-arc switch (ROCWASH_ROCQ / GATE7_PROBE_SCRIPT /
#   GATE6_SCRIPT / BORN_WORLD_ROCQ), probed by default and overridable by env.
#
# Evidence.  One case per t_* function below; the per-case contract tables (89
#   rows) live in tests/README.md; the CASES roster count is pinned by
#   tools/doc_lint.py check 2 against the tests/README.md count lines; the roster
#   is never written at run time.
#
# Exit-codes.  0 = all green (SKIP not counted red); 1 = any red (the failing
#   case's first 40 log lines print); 2 = selection error; case rc 111 = SKIP.
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
FIX="$REPO/tests/fixtures"
PY=${ROCWASH_PY:-python3}
# Fail loud when the selected interpreter is a non-working stub (the Windows
# Store python3 alias silently exits rc=49 on some hosts and produced the
# unexplained rc=49 family); one probe, zero output, actionable hint.
if ! "$PY" -c "import sys" >/dev/null 2>&1; then
  echo "FAIL-LOUD: PY=$PY does not run on this host (store alias or broken shim?) - set ROCWASH_PY=<a working python> and retry" >&2
  exit 49
fi
# Force UTF-8 I/O for every case and every child process they spawn: on a
# Windows host the default stdout codepage (charmap on the hosted runner
# image, gbk on a zh-CN host) makes a tool that prints Chinese prose or math
# symbols die with UnicodeEncodeError, which the suite then reads as a red
# case. Pinned here, in the suite's own entry point, so the guarantee holds
# for every caller and not only for the CI job environment.
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# ---------- canonical-environment probe (CI admission) ----------
# Four cases (t_gate7_wrapper / t_quad8_check / t_gate6_born_wrapper /
# t_verify_gate6) judge against the on-machine canonical environment at run
# time: the Set repository gate scripts, the CW rocq toolchain, and the
# four-repository replica set.  Canonical environment absent -> those cases
# exit 2 = SKIP; the paths are overridable via ROCWASH_CANON_* (CI rehearsal).
CANON_SET=${ROCWASH_CANON_SET:-/Users/apple/Desktop/ConstructiveWorld-Set}
CANON_CW=${ROCWASH_CANON_CW:-/Users/apple/Desktop/ConstructiveWorld}
CANON_W1=${ROCWASH_CANON_W1:-/Users/apple/Desktop/S系Prop清除战役工单}
CANON=0
# Clean mode (ROCWASH_CLEAN=1): canonical-environment auto-detection is
# disabled and explicit canonical pointers are not applied; the canonical
# paths resolve to a non-existent sentinel so the canonical-dependent cases
# SKIP by their standing contract (docs/clean-mode-manual-20261114.md).
if [ "${ROCWASH_CLEAN:-0}" = "1" ]; then
  CANON_SET="${TMPDIR:-/tmp}/rocqwash-clean-no-canonical"
  CANON_CW="$CANON_SET"
  CANON_W1="$CANON_SET"
  echo "(clean-mode note) ROCWASH_CLEAN=1: canonical-environment auto-detection disabled; canonical faces report 'requires canonical environment' and canonical-dependent cases SKIP"
else
if [ -f "$CANON_SET/scripts/gates/gate6_statement_census.py" ] \
   && [ -f "$CANON_SET/scripts/gates/gate7_extract_run.py" ] \
   && [ -x "$CANON_CW/Live/toolchain/opam/live/bin/rocq" ]; then
  CANON=1
fi
fi

# ---------- guarded compile-arc master switch (work stream 47 item 8A; default probing, 2026-11-12) ----------
# An env value already set wins (an external clone's explicit pointers stay
# undisturbed); otherwise the on-disk canonical/deputy paths are probed and
# exported.  The gate criteria keep their semantics (run when present, SKIP
# only when absent); only the default face flips:
#   ROCWASH_ROCQ        t_cure_pack compile-check section + t_probe_engine
#                       real-rocq section (9.3 multiplexer probe; the v43
#                       third shot's 27/27 same-source evidence,
#                       `更新账.md:3753`)
#   GATE7_PROBE_SCRIPT  t_gate7_wrapper (Set repository gate7 canonical;
#                       judge13 resolves the same path by default)
#   GATE6_SCRIPT        t_verify_gate6 + t_gate6_born_wrapper census section
#                       (Set repository gate6 canonical)
#   BORN_WORLD_ROCQ     t_gate6_born_wrapper born section (the existence
#                       check at born_world.sh:114; that test compiles
#                       nothing and never touches generation semantics; CW
#                       Live rocq absent -> the 9.3 multiplexer deputizes)
GATE93_ROCQ=/Users/apple/Desktop/mac93_install_work/opam93/rocq93/bin/rocq
# Clean mode skips the whole default-pointer block below (auto-detection off;
# ROCWASH_ROCQ/GATE7_PROBE_SCRIPT/GATE6_SCRIPT/BORN_WORLD_ROCQ stay unset so
# the env-gated compile sections SKIP by contract).
if [ "${ROCWASH_CLEAN:-0}" != "1" ]; then
if [ -z "${ROCWASH_ROCQ:-}" ] && [ -x "$GATE93_ROCQ" ]; then
  export ROCWASH_ROCQ="$GATE93_ROCQ"
  echo "(probe note) ROCWASH_ROCQ unset -> 9.3 multiplexer on disk; defaulted to ${ROCWASH_ROCQ} (item 8A)"
fi
if [ -z "${GATE7_PROBE_SCRIPT:-}" ] && [ -f "$CANON_SET/scripts/gates/gate7_extract_run.py" ]; then
  export GATE7_PROBE_SCRIPT="$CANON_SET/scripts/gates/gate7_extract_run.py"
  echo "(probe note) GATE7_PROBE_SCRIPT unset -> Set repository gate7 canonical on disk; defaulted (unlocks t_gate7_wrapper)"
fi
if [ -z "${GATE6_SCRIPT:-}" ] && [ -f "$CANON_SET/scripts/gates/gate6_statement_census.py" ]; then
  export GATE6_SCRIPT="$CANON_SET/scripts/gates/gate6_statement_census.py"
  echo "(probe note) GATE6_SCRIPT unset -> Set repository gate6 canonical on disk; defaulted (unlocks the t_verify_gate6 / t_gate6_born_wrapper census sections)"
fi
if [ -z "${BORN_WORLD_ROCQ:-}" ]; then
  if [ -x "$CANON_CW/Live/toolchain/opam/live/bin/rocq" ]; then
    export BORN_WORLD_ROCQ="$CANON_CW/Live/toolchain/opam/live/bin/rocq"
  elif [ -x "$GATE93_ROCQ" ]; then
    export BORN_WORLD_ROCQ="$GATE93_ROCQ"
    echo "(probe note) BORN_WORLD_ROCQ unset and CW Live rocq absent -> the 9.3 multiplexer deputizes (unlocks t_gate6_born_wrapper; that test compiles nothing, existence check only)"
  fi
fi
fi

PASS=0; FAIL=0; SKIP=0; TOTAL=0; REDS=""; SKIPS=""
LOG=$(mktemp /tmp/rocqwash_tests.XXXXXX)
trap 'rm -f "$LOG"' EXIT INT TERM

CASES="\
t_scan_selftest \
t_names_expect_pos \
t_names_expect_let \
t_names_expect_neg \
t_gate4_clean \
t_gate4_dirty \
t_retrofit_dryrun \
t_wash_judgments \
t_wash_engine \
t_verify_vo \
t_seam_probe \
t_freeze_manifest \
t_push_gate \
t_watch \
t_cpu_guard_direct_smoke \
t_cpu_guard_direct_rc \
t_scan_station \
t_gate7_wrapper \
t_verify_born \
t_frozen8 \
t_frozen8_check \
t_quad8 \
t_quad8_check \
t_frozen_call \
t_gate6_born_wrapper \
t_world_hook \
t_select_audit \
t_verify_gate6 \
t_recipe_s07 \
t_recipe_pw1 \
t_precedent_station \
t_netname_normalize \
t_verify_fresh \
t_extract_magic \
t_scan_v4_token \
t_cure_pack \
t_erasure_classifier \
t_probe_engine \
t_chain_graph \
t_ledger_sync \
t_comment_pack \
t_dual_scan \
 t_cw_entry \
 t_registry_union \
 t_toolchain_dyld_doctor \
 t_ci_triage \
 t_net_probe \
 t_pushci \
 t_cw_sentinel \
 t_wash_shape \
 t_unclog \
 t_cw_doctor \
 t_relay_e2e \
 t_doclint \
 t_destructive_matrix \
 t_baseline_diff \
 t_red_dispatch \
 t_registry_audit \
 t_registry_fix \
 t_registry_fix_dedup \
 t_registry_fix_orphan_add \
 t_registry_fix_anchor \
 t_norm_lint \
 t_contrib_intake \
 t_registry_regen \
 t_evolve \
 t_clean_mode \
 t_vacgen_shape \
 t_vacgen_expectedred \
 t_refinery \
 t_symbiosis_shape \
 t_bus_feeder_shape \
 t_uplink_shape \
 t_evolution_dashboard_shape \
 t_mcp_face \
 t_exp_port \
 t_periscope_shape \
 t_engines_body \
 t_engines_seeds \
 t_evolve_flag_contract \
 t_watch_repo_form \
 t_flaky_guard \
 t_roster_resync \
 t_auto_merge \
 t_selfheal_guards \
 t_jargon_map_sync \
 t_tool_selftests \
 t_axiom_audit \
 t_lean_parity"
NCASES=$(echo $CASES | wc -w | tr -d ' ')
if [ "${ROCQWASH_TESTS_FAIL_PROBE:-0}" = "1" ]; then
  CASES="$CASES t_fail_probe"
  NCASES=$((NCASES + 1))
fi

# ---------- advisory roster: flaky quarantine (repair class E2-3) ----------
#   tools/flaky_guard.py --move writes an order-dependent case into
#   tests/advisory_roster.txt (repair-ledger row class/target/outcome;
#   budget <= 2 per class per branch; scope-checked against the shared
#   tools/repair_scope.py exclusion table).  The default suite then drops
#   the case here (main roster shrinks, one loud ADVISORY-OUT line each)
#   and the CI flaky-watch lane keeps running quarantined cases in its
#   own observation step.  ROCWASH_TESTS_ONLY wins over the quarantine (a
#   watch lane can name a quarantined case explicitly); unknown advisory
#   names print one loud note and are ignored (rosters evolve, same
#   contract as EXCLUDE).  Restore is the guard's --restore face with
#   green-round evidence (ledger row outcome=restored).
ADVISORY_ROSTER=${ROCWASH_ADVISORY_ROSTER:-"$REPO/tests/advisory_roster.txt"}
_advisory=""
if [ -f "$ADVISORY_ROSTER" ]; then
  for _n in $(grep -v '^[[:space:]]*#' "$ADVISORY_ROSTER" | tr '\n\r' '  '); do
    [ -z "$_n" ] && continue
    _hit=0
    for _c in $CASES; do
      [ "$_c" = "$_n" ] && _hit=1 && break
    done
    if [ "$_hit" = "1" ]; then
      _advisory="$_advisory $_n"
    else
      echo "ADVISORY-NOTE: advisory-roster name is not in the roster (ignored): $_n"
    fi
  done
fi

# ---------- roster selection: platform-sensitive / flaky separation ----------
#   ROCWASH_TESTS_ONLY     space-separated case names; run ONLY these.
#   ROCWASH_TESTS_EXCLUDE  space-separated case names; run the default roster
#                          minus these (each excluded case prints one loud
#                          SELECTED-OUT line and is not counted).
#   Carried by the CI matrix (ci.yml): ubuntu/windows jobs exclude the
#   platform-sensitive roster for the blocking job and run it alone in the
#   advisory flaky-watch job, so a platform-bound red cannot mask a real
#   regression and cannot fail the run either (failure-rate target <5%).
#   Unknown ONLY names are a loud rc=2 (the caller named a case that does
#   not exist); unknown EXCLUDE names print one loud note and are ignored
#   (rosters evolve). The exit contract (0 all green / 1 any red) is
#   unchanged; selection never turns a red into a pass.
if [ -n "${ROCWASH_TESTS_ONLY:-}" ] || [ -n "${ROCWASH_TESTS_EXCLUDE:-}" ] || [ -n "$_advisory" ]; then
  _sel_all="$CASES"
  if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then
    for _want in $ROCWASH_TESTS_ONLY; do
      _hit=0
      for _c in $_sel_all; do
        [ "$_c" = "$_want" ] && _hit=1 && break
      done
      if [ "$_hit" != "1" ]; then
        echo "SELECTION-ERROR: ROCWASH_TESTS_ONLY name is not in the roster: $_want"
        exit 2
      fi
    done
  fi
  _selected=""
  for _c in $_sel_all; do
    _drop=0
    if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then
      _drop=1
      for _want in $ROCWASH_TESTS_ONLY; do
        [ "$_c" = "$_want" ] && _drop=0 && break
      done
    else
      for _ex in ${ROCWASH_TESTS_EXCLUDE:-}; do
        if [ "$_c" = "$_ex" ]; then
          _drop=1
          printf 'SELECTED-OUT %-26s (platform-sensitive roster; advisory watch job covers it)\n' "$_c"
        fi
      done
      for _ax in $_advisory; do
        if [ "$_c" = "$_ax" ]; then
          _drop=1
          printf 'ADVISORY-OUT %-26s (flaky quarantine; the advisory watch lane covers it)\n' "$_c"
        fi
      done
    fi
    [ "$_drop" != "1" ] && _selected="$_selected $_c"
  done
  CASES="$_selected"
  NCASES=$(echo $CASES | wc -w | tr -d ' ')
  if [ -z "$(echo $CASES | tr -d ' ')" ]; then
    echo "SELECTION-ERROR: case selection is empty (ONLY matched nothing usable)"
    exit 2
  fi
fi

# ---------- cases (each case owns its exit code; 0 = that case green) ----------

t_scan_selftest() {
  "$PY" -B "$REPO/scan/mac_stmt_scan.py" --selftest
}

t_names_expect_pos() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --expect 7
}

t_names_expect_let() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --include-let --expect 8
}

t_names_expect_neg() {
  "$PY" -B "$REPO/names/mac_stmt_names.py" "$FIX/names_sample.v" --expect 6 >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 2 ] || { echo "negative case should exit 2 (CONTRIBUTING section 4 contract), got $rc"; return 1; }
}

t_gate4_clean() {
  "$PY" -B "$REPO/verify/gate4_comment_guard.py" --file "$FIX/gate4_clean_sample.v"
}

t_gate4_dirty() {
  "$PY" -B "$REPO/verify/gate4_comment_guard.py" --file "$FIX/gate4_dirty_sample.v" >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 1 ] || { echo "dirty sample should FAIL with exit 1, got $rc"; return 1; }
}

t_retrofit_dryrun() {
  "$PY" -B "$REPO/tests/test_retrofit_dryrun.py"
}

t_wash_judgments() {
  "$PY" -B "$REPO/tests/test_wash_fixture.py"
}

t_wash_engine() {
  "$PY" -B "$REPO/tests/test_wash_engine.py"
}

t_verify_vo() {
  "$PY" -B "$REPO/verify/verify_vo.py" --selftest
}

t_seam_probe() {
  "$PY" -B "$REPO/seam/seam_probe.py" --selftest
}

t_freeze_manifest() {
  "$PY" -B "$REPO/certify/freeze_manifest.py" --selftest
}

t_push_gate() {
  "$PY" -B "$REPO/certify/push_gate.py" --selftest
}

t_watch() {
  "$PY" -B "$REPO/watch/watch.py" --selftest
}

t_cpu_guard_direct_smoke() {
  local out rc
  out=$("$REPO/tools/cpu_guard.sh" -Direct -- true 2>&1)  # one-shot probe (no queueing, no registration)
  rc=$?
  [ "$rc" -eq 0 ] || { echo "probe should return rc=0, got $rc"; echo "$out"; return 1; }
  case "$out" in
    *"DIRECT bypass"*) : ;;
    *) echo "missing the [cpu_guard] DIRECT bypass banner"; echo "$out"; return 1 ;;
  esac
}

t_cpu_guard_direct_rc() {
  "$REPO/tools/cpu_guard.sh" -Direct -- sh -c 'exit 7' >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq 7 ] || { echo "exit code should propagate the probe rc=7, got $rc"; return 1; }
}

t_scan_station() {
  "$PY" -B "$REPO/tests/test_scan_station.py"
}

t_gate7_wrapper() {
  # judge11/13 depend on the Set repository gate7 canonical face; absent ->
  # the case yields (still runs when the positive-face GATE7_PROBE_SCRIPT
  # override is on disk)
  [ "$CANON" = "1" ] || [ -n "${GATE7_PROBE_SCRIPT:-}" ] || { echo "SKIP: gate7 canonical not on disk ($CANON_SET/scripts/gates/gate7_extract_run.py)"; return 111; }
  "$PY" -B "$REPO/tests/test_gate7_wrapper.py"
}

t_verify_born() {
  "$PY" -B "$REPO/tests/test_verify_born.py"
}

t_frozen8() {
  "$PY" -B "$REPO/certify/frozen8.py" --selftest
}

t_frozen8_check() {
  # the registered eight-piece frozen list reconciles at every suite run (a push-window c4 green suite includes this eight-piece reconciliation; read-only, zero writes)
  "$PY" -B "$REPO/certify/frozen8.py" check \
    --list "$REPO/certify/frozen8_manifest.json" \
    --tier2 "$REPO/certify/frozen8_tier2.md5"
}

t_quad8() {
  # four-repository same-md5 replica-set reconciler: the fixture eight-check group (zero real-repo touch; 20261031 agent rqadapt)
  "$PY" -B "$REPO/wrapper/quad8_reconcile.py" --selftest
}

t_quad8_check() {
  # the registered four-repository list reconciles at every suite run (11
  # replicas; the audit domain records without judging; read-only, zero writes)
  # the replica set spans the four repository canonicals; absent -> the case
  # yields (the fixture eight checks in t_quad8 have no dependency and always run)
  [ -d "$CANON_CW" ] && [ -d "$CANON_SET" ] && [ -d "$CANON_W1" ] || { echo "SKIP: the four-repository replica set is not on disk (the quad8 live reconciliation runs on the canonical machine only)"; return 111; }
  "$PY" -B "$REPO/wrapper/quad8_reconcile.py" check \
    --list "$REPO/wrapper/quad8_manifest.json" \
    --tier2 "$REPO/wrapper/quad8_tier2.md5"
}

t_frozen_call() {
  # wrapper-layer per-call assertion fixture, five checks (zero touch of the real repository and components; temporary account face)
  "$PY" -B "$REPO/wrapper/frozen_call.py" --selftest
}

t_gate6_born_wrapper() {
  # wrapper-layer gate6 survey-check launch layer + born world-baseline shape,
  # sixteen checks (zero compile, zero writes)
  # the census criterion depends on the Set repository gate6 canonical; the
  # born criterion depends on the CW rocq toolchain; absent -> the case yields
  [ "$CANON" = "1" ] || [ -n "${GATE6_SCRIPT:-}" ] || [ -n "${BORN_WORLD_ROCQ:-}" ] || { echo "SKIP: gate6 canonical / rocq toolchain not on disk ($CANON_SET/scripts/gates/ + $CANON_CW/Live/toolchain)"; return 111; }
  "$PY" -B "$REPO/tests/test_gate6_born_wrapper.py"
}

t_world_hook() {
  # five-lesson feedback round, negative example 1 nw5 world skew: the assertion intercepts before born + the frozen-engine zero-touch side evidence (zero compile, zero writes)
  "$PY" -B "$REPO/tests/test_world_hook.py"
}

t_select_audit() {
  # five-lesson feedback round, negative example 2 nw6 in-batch duplicates +
  # example 3 enbig7 cross-batch name collisions + the v6 criteria nw10/abl6
  # empty ledger
  # Require face (parse_requires / STDLIB_ROOTS / audit_requires; zero
  # repository writes, zero network)
  "$PY" -B "$REPO/tests/test_select_audit.py"
}

t_verify_gate6() {
  # five-lesson feedback round, fixture 4 gate6 ch1: the eum judgment positive
  # case / untreated negative case / canonical true scan (canonical read-only;
  # -B bans pycache)
  # the "canonical true scan" sub-check depends on the Set repository gate6
  # canonical; absent -> the case yields (the two selftest fixture sub-checks
  # have no dependency and always run)
  [ "$CANON" = "1" ] || [ -n "${GATE6_SCRIPT:-}" ] || { echo "SKIP: gate6 canonical not on disk ($CANON_SET/scripts/gates/gate6_statement_census.py)"; return 111; }
  "$PY" -B "$REPO/tests/test_verify_gate6.py"
}

t_recipe_s07() {
  # five-lesson feedback round, fixture 5 S07 projection re-anchor E5: prescription-piece anchor word face + diseased/masked/cured machine checks (frozen engine read-only import)
  "$PY" -B "$REPO/tests/test_recipe_s07.py"
}

t_recipe_pw1() {
  # five-lesson polish round, courseware 3 dver2-enbig7 same-domain collision:
  # the PW1 prescription-piece anchor word face + precursor DUP-CROSS /
  # invasive-substitution WDIFF interception (zero disk writes) +
  # private-occupancy rebuild WORLD-BASE-OK (zero compile, zero writes)
  "$PY" -B "$REPO/tests/test_recipe_enbig7_pw1.py"
}

t_precedent_station() {
  # five-lesson polish round, courseware 5 three-precedent script toolified:
  # the three-precedent acceptance station ten-check selftest + light-chain
  # positive/negative judgments (names cross-check against the reference /
  # gate4 / REVIEW escalation / gate7 shape / apply-face naming; zero compile,
  # zero writes; the real gate7 run stays out of the suite)
  "$PY" -B "$REPO/tests/test_precedent_station.py"
}

t_netname_normalize() {
  # this round's precedent toolification 1: the .v.v double-suffix clean-name
  # normalizer (tests/test_netname_normalize.py; nine sections: dry run by
  # default zero-write / --apply with md5 before-and-after verification
  # (rename without byte change) / COLLIDE refuses overwrite / CLI four codes
  # help 0, unknown flag 2, missing dir 2, absent dir 9 — zero real-repo touch)
  "$PY" -B "$REPO/tests/test_netname_normalize.py"
}

t_verify_fresh() {
  # this round's precedent toolification 2: the fresh-compile defense line
  # against the divmod_gen stale-vo spurious-pass precedent
  # (tests/test_verify_fresh.py; eight sections: --require-fresh dual judgment
  # on the 9.1 magic number + freshness; either failing -> rc=9 fail-loud —
  # zero real-repo touch, zero compile)
  "$PY" -B "$REPO/tests/test_verify_fresh.py"
}

t_extract_magic() {
  # this round's precedent toolification 3: the gate7 extraction-face
  # Obj.magic per-file machine check (toolification of the tenth defect-ledger
  # entry; run97/98's three-file ledger growth 28/4/1, fed by the task
  # instruction).  tests/test_extract_magic.py, eleven sections: Separate
  # Extraction parsing (inline/driver forms) -> rocq extraction -> ocamlc ->
  # grep -c Obj.magic -> --max red/green judgment + --json ledger; fake
  # rocq/ocamlc stubs across the whole chain (zero real compile, zero
  # real-repo touch; fixtures include this repository's own names_sample.v
  # read-only); v15 adds the blind-spot completion section (first battle G09
  # Class / G13 Extraction double red -> declaration/command vernacular
  # expanded in place; the Class fixture no longer misjudged by the census;
  # unknown vernacular still red 9)
  "$PY" -B "$REPO/tests/test_extract_magic.py"
}

t_fail_probe() {
  echo "(suite self-check injected case: always red)"
  return 1
}

t_scan_v4_token() {
  # W15 toolification 1: the token-level survey (mixed-line shadowing fixture
  # across three stations + mechanical evidence of the old method's blind spot
  # + binder tracking with zero false positives; real-tree spot checks gated
  # by ROCWASH_TREE_SAMPLES, zero hardcoded paths; fixture-level checks always
  # run by default)
  "$PY" -B "$REPO/tests/test_scan_v4_token.py"
}

t_cure_pack() {
  # W15 toolification 2: the consumer-site cure canonical pack, five forms
  # (applier selftest + pack integrity + dry run/apply/idempotence; compile
  # verification gated on ROCWASH_ROCQ and wrapped by tools/cpu_guard.sh; the
  # suite probes by default and runs automatically (work stream 47 item 8A,
  # the run_tests.sh master switch); env absent and 9.3 absent -> still SKIP)
  "$PY" -B "$REPO/tests/test_cure_pack.py"
}

t_erasure_classifier() {
  # W15 toolification 3: the erasure-site six-cluster classifier (selftest +
  # synthetic interface + CAPTURE differential comparison; real-artifact
  # replay gated by ROCWASH_ERASURE_MLI/SCAN; skipped by default)
  "$PY" -B "$REPO/tests/test_erasure_classifier.py"
}

t_probe_engine() {
  # v30 toolification 1: the batch closure-compatibility probe engine
  # (succeeds W13 probe_batch.py; tests/test_probe_engine.py nine sections:
  # stub full-chain rc three-way split / NO-SRC / TIMEOUT / resume idempotence /
  # guard-wrapped true rc capture / RED missing column / CLI four codes; the
  # real rocq full chain gated on ROCWASH_ROCQ; the suite probes by default
  # and runs automatically (work stream 47 item 8A); env absent and 9.3 absent
  # -> still SKIP; zero real-repo touch, zero network)
  "$PY" -B "$REPO/tests/test_probe_engine.py"
}

t_chain_graph() {
  # v30 toolification 2: the multi-ledger merge chain-root graph (succeeds W25
  # w25_merge_ledgers.py; synthetic double ledger, seven sections: both forms
  # accepted / later batch overrides / chain-root own-washability three-way
  # split / missing dual source / top list + determinism / CLI four codes;
  # zero real-repo touch, zero network)
  "$PY" -B "$REPO/tests/test_chain_graph.py"
}

t_ledger_sync() {
  # v30 toolification 3: the probe-by-status ledger merge sync (E1 dedup /
  # E3 ghosts / MD5-DRIFT / NO-MD5 / promotion policy / column validation
  # fail-loud / idempotent byte-identical reruns / CLI four codes; synthetic
  # fixtures, eight sections; zero real-repo touch, zero network)
  "$PY" -B "$REPO/tests/test_ledger_sync.py"
}

t_comment_pack() {
  # v31 toolification: the comment-domain sweep sidecar (comment_pack.json +
  # comment_sweep.py; nesting- and string-aware state machine / flag-word
  # rewording / header regeneration / w7 code-line equality / idempotence;
  # six sections, zero real-repo touch)
  "$PY" -B "$REPO/tests/test_comment_pack.py"
}

t_dual_scan() {
  # v32 toolification: the two-scanner differential run driver
  # (scan/dual_scan.py; scan_v4_token + mac_stmt_scan double scan with
  # per-file difference reports only_v4/only_stmt/common; deterministic
  # byte-identical reruns; CLI four codes; tests/test_dual_scan.py ten
  # sections; zero real-repo touch, zero network)
  "$PY" -B "$REPO/tests/test_dual_scan.py"
}

t_cw_entry() {
  # v33 toolification: the cw.sh v29-v32 unified tool entry
  # (tests/test_cw_entry.sh; four sections: help/route smoke + seven-tool
  # --help passthrough + functional passthrough (scan4/dual-scan/chain/
  # sync-ledger synthetic ledger/cure/erasure selftest/probe no-arg
  # FAIL-LOUD) + zero-hardcoding behavioral proof (empty-directory copy
  # rc=9) + /bin/bash 3.2 syntax check; fixtures read-only, outputs to
  # mktemp; zero real-repo touch, zero network)
  bash "$REPO/tests/test_cw_entry.sh"
}

t_registry_union() {
  # 20261110 precedent-operation toolification: the registry union operation
  # tool (tools/registry_union.py; tests/test_registry_union.py nine sections:
  # selftest eight checks / coq fixture group / trap group same-name
  # different-shape filtered against merge-base / re-anchor md5 frozen vector
  # 1414cddb / A2 and A3 negatives zero-write / dry run-apply-idempotence /
  # json determinism / CLI four codes + usage duality / git three-ref direct
  # read; fixtures read-only, outputs to mktemp; zero real-repo touch, zero
  # network, zero compile)
  "$PY" -B "$REPO/tests/test_registry_union.py"
}

t_toolchain_dyld_doctor() {
  # 20261111 integration-agent hookup: the dyld toolchain linkage-failure
  # doctor (tools/toolchain_dyld_doctor.py; the casting agent's --selftest
  # full-chain offline vector group is self-attested;
  # tests/test_toolchain_dyld_doctor.py minimal shell two checks: --selftest
  # frozen marker + --help smoke; zero real otool, zero compile, zero network)
  "$PY" -B "$REPO/tests/test_toolchain_dyld_doctor.py"
}

t_ci_triage() {
  # 20261111 integration-agent hookup: the failing-build triage tool
  # (tools/ci_triage.py; the five-family + green-build classification
  # spectrum; the casting agent's --selftest offline samples self-attested;
  # tests/test_ci_triage.py minimal shell two checks: --selftest frozen
  # marker + --help smoke; zero network, zero writes)
  "$PY" -B "$REPO/tests/test_ci_triage.py"
}

t_net_probe() {
  # 20261111 integration-agent hookup: the network-window probe
  # (tools/net_probe.py; the dual-probe stability-window rule; the casting
  # agent's --selftest zero-network vector group self-attested;
  # tests/test_net_probe.py minimal shell two checks: --selftest frozen
  # marker + --help smoke; zero network, zero writes)
  "$PY" -B "$REPO/tests/test_net_probe.py"
}

t_pushci() {
  # 20261111 integration-agent hookup: the push-CI single-command pipeline
  # orchestrator (tools/pushci.py; five-stage pipeline preflight check ->
  # push -> watch -> heal -> verdict +/- merge; v35 four-tool subprocess
  # orchestration, zero new engines; tests/test_pushci.py six-scenario shell
  # ten sections: selftest frozen vectors + tmp repository helper + S1 green
  # path + S2 NETRED healing + S3 content red zero rerun + S4 heal exhausted
  # + S5 merge + S6 dry-run + six-scenario idempotent byte-identical reruns
  # + CLI five codes — fully offline, fully injected, zero real network, zero
  # real push, zero compile, zero writes)
  # work stream 41 registration: zero new pushci-tool vectors — this work
  # stream's pushci output = the guard agent's push_gate four-criteria
  # push-window x pushci preflight-check dual-door normalization assessment
  # (docs/push-gate-dual-door-assessment-v1.0-20261111.md; assessment only,
  # zero code changes; the preflight three checks toolchain/net/gate4 and the
  # seven verdict states unchanged; the pushci P1-P3 matrix three checks stay
  # registered in t_destructive_matrix and rerun with the suite)
  "$PY" -B "$REPO/tests/test_pushci.py"
}

t_cw_sentinel() {
  # 20261111 v37 hookup: the realtime watcher (tools/cw_sentinel.py; three
  # signal sources — CI runs / local ledger chain roots / buildlog word faces
  # -> JSONL event stream; once/loop dual mode; ci_triage / chain_graph
  # subprocess orchestration, zero new engines; tests/test_cw_sentinel.py
  # minimal shell two checks: --selftest frozen marker CW-SENTINEL-SELFTEST
  # PASS + --help smoke; the watcher's own --selftest thirteen canned
  # injection vectors, zero real network, zero compile (v40 steady-state
  # expansion 11 --state-file crash recovery / 12 --emit-max-bytes JSONL
  # rotation; v41 guard/preset expansion 9 on-red dual path same guard —
  # plain --on-red without --emit rc=2 (destructive-matrix S2 promoted) /
  # 13 the preset table extended to five chained presets; the v51 work
  # stream 14 resilience layer bounded retry on transport-layer transient
  # breaks (--net-retries backoff 5s/15s/45s) + loop per-source skip — skip
  # a round rather than crash; 15 the supervisor-shell deployment-form smoke
  # examples/sentinel_supervisor.sh bash -n + key-line static assertions;
  # zero execution, zero network)
  "$PY" -B "$REPO/tests/test_cw_sentinel.py"
}

t_wash_shape() {
  # 20261111 v37 shape-normalization-agent hookup, v39 expansion, v40
  # steady-state re-expansion: the shape-normalizing tool, canonical-form
  # five-wash pipeline (tools/wash_shape.py; gate4 word face / scan_v4 +
  # cure_applier canonical pack / header template backfill / line-ending
  # normalization / registry_union re-anchor — five washes, subprocess
  # orchestration; two-stage plan -> apply rerun recheck; schema
  # rocqwash-shape/1; tests/test_wash_shape.py minimal shell three checks:
  # --selftest frozen marker WASH-SHAPE-SELFTEST PASS (eighteen vector
  # checks, all tmp fixtures; the v39 round adds four preset-chain checks:
  # template library loaded / preset beats env / placeholder render ->
  # apply end to end / same-slot mutual exclusion rc2, plus missing template
  # library rc9; the v40 round adds check 17 --loop event-stream same-shape
  # alignment (rocqwash-sentinel-event/1, seq continuing across processes)
  # and check 18 plan-cache invalidation semantics (source md5 changed ->
  # recompute; unchanged -> cache hit)) + --help smoke + exit-code spot
  # checks 2/2/9; zero compile, zero network, zero writes)
  "$PY" -B "$REPO/tests/test_wash_shape.py"
}

t_unclog() {
  # 20261111 v37 integration-agent hookup, v40 steady-state expansion, v41
  # performance expansion: the clear-blockages closed-loop engine
  # (tools/unclog.py; manual five-step closed loop — probe collection ->
  # chain_graph root picking -> cure_applier apply -> rescan/resprobe
  # recheck -> verdict; schema rocqwash-unclog/1; tests/test_unclog.py
  # minimal shell three checks: --selftest frozen marker UNCLOG-SELFTEST
  # PASS (fourteen vectors, all --injector canned; the v40 round adds
  # 11 --state-file same-shape watcher-state seen diffing (red-new events
  # only-new; damaged state refused red 9, silent rebuild banned) and
  # 12 --rounds/--loop vs --audit/--state-file mutual exclusion rc=2; the
  # v41 adds 12 --probe-parallel 0 usage check rc=2 and 13 a --jobs
  # dimension recorded into the audit timing section (jobs=K; default 1 and
  # K=2 each recorded, the same candidate face comparable across runs with
  # different K)) + --help smoke + exit-code spot checks 2/2/9 (bogus /
  # no-arg / missing path verified by this integration agent's real runs);
  # zero real compile, zero network, zero real-repo touch)
  "$PY" -B "$REPO/tests/test_unclog.py"
}

t_cw_doctor() {
  # 20261111 v38 integration-agent hookup: the comprehensive checkup tool,
  # four-domain aggregation (tools/cw_doctor.py; four domains orchestrate the
  # existing tools by subprocess (dyld / net_probe / probe_engine +
  # chain_graph / registry anchor audit) -> composite health score 0-100 +
  # verdict healthy/degraded + advice; schema rocqwash-cwdoctor/1;
  # tests/test_cw_doctor.py minimal shell two checks: --selftest frozen
  # marker CW-DOCTOR-SELFTEST PASS (nine sections of vectors, all --injector
  # canned) + --help smoke; the missing shell self-supplemented by this
  # integration agent; zero real otool, zero real network, zero real compile,
  # zero real-repo touch)
  "$PY" -B "$REPO/tests/test_cw_doctor.py"
}

t_relay_e2e() {
  # 20261111 v39 tooling-agent cast, integration-agent hookup: the relay
  # live-check e2e (tests/test_relay_e2e.py; cw_sentinel --on-red-preset
  # unclog full chain, three checks: 1 the watcher --once + injector canned
  # failing CI build -> ci_triage true classification A-content-red ->
  # ci-red event -> the preset runs unclog on the tool's behalf, rc=9
  # recorded honestly (side-effect actions are not the tool face; the
  # watcher exit code stays 0); 2 unclog --audit dry run rc=0; the --src
  # full-file md5 inventory proves zero writes before and after; red seen
  # red_files=["B"]; a washable chain root emerges; walls empty; 3 the
  # JSONL-recorded unclog report path byte-compared against the actually
  # written file, schema/verdict interlock — all canned, zero real network,
  # zero real compile, zero real-repo touch)
  "$PY" -B "$REPO/tests/test_relay_e2e.py"
}

t_doclint() {
  # 20261111 v39 integration-agent shell self-supplement hookup: the
  # docs-vs-implementation consistency three-check tool (tools/doc_lint.py;
  # tooling-agent cast; schema rocqwash-doclint/1; tests/test_doc_lint.py
  # minimal shell three checks: --selftest frozen marker DOC-LINT-SELFTEST
  # PASS (tmp mini-repo seven vectors V1-V7 self-attested by the casting
  # agent's --selftest) + --help smoke + exit-code spot checks 2/2/9 (bogus /
  # --help-cap 0 / missing repo, verified by this integration agent's real
  # runs); zero network, zero writes, zero real-repo touch)
  "$PY" -B "$REPO/tests/test_doc_lint.py"
}

t_destructive_matrix() {
  # 20261111 v40 destructive-surface-agent cast, integration-agent hookup:
  # the destructive-surface review matrix, one refuse-to-write criterion per
  # row (tests/test_destructive_matrix.py; the active 33 rows assert the
  # refuse-to-write guards row by row as writing-tool x write-face x guard
  # anchor file:line: unclog x4 / wash_shape x4 / pushci x3 /
  # cw_sentinel×2/registry_union×2/cure_applier×4/frozen8×2/axiom_guard×1/
  # jargon_apply x1 — dry run zero-write / writes only under --apply / frozen
  # refused red / content red zero rerun / heal stops at the cap /
  # report-only default zero action, and so on; the X6 work stream adds 10 rows
  # under whoever-writes-joins-the-matrix: scheduler_lite x2 (SL1 plan
  # without --out zero-write, dryRun always true / SL2 the only write face is
  # an explicit --out, byte-identical across two runs) + auto_merge x3 (AM1
  # without --apply zero-write / AM2 hold never authorizes + foreign-branch
  # allowlist refused red / AM3 the daily budget cap + duplicate refusal) +
  # repair_scope x1 (RS1 the --check query face zero-write + the shared
  # roster criterion interlock) + the four E-series guards x4 (E2A lane-extract
  # / E2B roster-resync / E2C flaky-quarantine / E2D doc-count — all four
  # dry-run, zero writes, zero ledger, plus the exclusion check and the
  # budget cap recording only escalated rows); all tmp fixtures + injector
  # canned, zero real network, zero real repository, zero real compile (the
  # single exception W3 hands over a real registered-file path, refused on
  # receipt, zero reads zero writes); a matrix red = a broken guard, exit 1
  # loudly listing the breach file:line + evidence)
  "$PY" -B "$REPO/tests/test_destructive_matrix.py"
}

t_baseline_diff() {
  # 20261111 v40 tooling-agent cast, integration-agent shell self-supplement
  # hookup: the blockage-record baseline comparator (tools/baseline_diff.py;
  # two unclog --audit baselines in argv order old -> new -> new_blocks /
  # resolved_blocks / persistent three lists + score_delta; verdict
  # improved/degraded/stable/incomparable; the account self-consistency
  # precheck refuses hand-edits; candidate four-tuple comparison; the timing
  # section excluded from comparison; schema rocqwash-baseline-diff/1;
  # tests/test_baseline_diff.py minimal shell three checks: --selftest frozen
  # marker BASELINE-DIFF-SELFTEST PASS (six vectors self-attested by the
  # casting agent's --selftest) + --help smoke + exit-code spot checks 2/2/9
  # (bogus / missing args = 2 / missing ledger file = 9, verified by this
  # integration agent's real runs); zero network, zero compile, zero
  # real-repo touch)
  "$PY" -B "$REPO/tests/test_baseline_diff.py"
}

t_red_dispatch() {
  # 20261112 v46 casting-agent cast, integration-agent shell self-supplement
  # hookup: the red-event router (tools/red_dispatch.py; watcher red events
  # -> action-preset routing; the three presets report-only/suggest/auto;
  # zero execution by default; auto runs on the tool's behalf only when
  # explicit, 60s cap, rc!=0 recorded without changing the exit code;
  # dedup state + cooldown; all five routes hang off the existing cw.sh
  # routes, zero new engines; family A content red never auto-repaired, a
  # fix list is emitted; schema rocqwash-red-route/1;
  # tests/test_red_dispatch.py minimal shell three checks: --selftest frozen
  # marker RED-DISPATCH-SELFTEST PASS (twelve vectors self-attested by the
  # casting agent's --selftest) + --help smoke + exit-code spot checks 2/2/9
  # (bogus / dry-run mistaken tier = 2 / missing event file = 9, verified by
  # this integration agent's real runs); zero network, zero compile, zero
  # real-repo touch)
  "$PY" -B "$REPO/tests/test_red_dispatch.py"
}

t_registry_audit() {
  # 20261112 v46 casting-agent cast, integration-agent shell self-supplement
  # hookup: the registry hygiene auditor (tools/registry_audit.py; the
  # order.txt/_CoqProject double book read-only, four account classes:
  # duplicate rows / anchor collisions / sequence-number shapes / odd shapes
  # / missing anchors / orphans / the live topology + --fix-plan
  # deterministic prescriptions zero-write; --apply does not exist; keys and
  # anchor canonicals used directly through registry_union, zero rebuilds;
  # the defect is data, always exit 0; schema rocqwash-registry-audit/1;
  # tests/test_registry_audit.py minimal shell three checks: --selftest
  # frozen marker REGISTRY-AUDIT-SELFTEST PASS (five vector groups
  # self-attested by the casting agent's --selftest) + --help smoke +
  # exit-code spot checks 2/2/9 (bogus / no input face / half a book = 2 /
  # missing book = 9, verified by this integration agent's real runs); zero
  # network, zero compile, zero real-repo touch)
  "$PY" -B "$REPO/tests/test_registry_audit.py"
}

t_registry_fix() {
  # 20261112 v47 integration-agent direct hookup: the registry prescription
  # executor (tools/registry_fix.py; applies each registry_audit --fix-plan
  # prescription row by row; the three prescription classes DEDUP keep-first
  # / anchor refresh / ORPHAN-ADD skip; dry run by default; after --apply the
  # assertions run — zero duplicate residue / no new anchor collisions / no
  # new orphans / zero treated-anchor residual (A-fix-6; two extra orphan
  # checks under --orphan-add); any failure rolls back; staging fully
  # in-memory, zero writes; the same-parameter discipline interlocks the
  # audit and the executor verbatim; schema rocqwash-registry-fix/1 — the
  # tool's --selftest eight vectors, all canned tmp fixtures; zero network,
  # zero compile, zero real-repo touch)
  "$PY" -B "$REPO/tools/registry_fix.py" --selftest
}

t_registry_fix_dedup() {
  # RQW09 duplicates-family executor agent (20261114): DEDUP contract unit
  # tests for tools/registry_fix.py — keep-first fix_plan direction pinned
  # from the registry_audit --fix-plan producer semantics, dry-run
  # zero-write, apply keep-first with exact per-item diff and post
  # re-audit duplicates=0, INJECT_BLAST post-write rollback, stale-plan
  # staging blast, CLI exit-code spot checks. tmp fixtures only, zero
  # real-repository contact, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_dedup.py"
}

t_registry_fix_orphan_add() {
  # ORPHAN-ADD apply-path tests for tools/registry_fix.py
  # (tests/test_registry_fix_orphan_add.py): the opt-in --orphan-add face
  # executes the mechanically solvable order-only orphan prescriptions
  # (placeholder-free template appended to the coqproject book) - eight
  # fixture-based checks: default-off parity pin, dry run, apply with the
  # full assertion face, project-only skip stability, suffix-typo guard
  # (paired .v.v registration left for human adjudication), blast-hook
  # rollback (ROCWASH_REGISTRY_FIX_INJECT_BLAST=post-write), stale-
  # prescription guard, determinism. All on mkdtemp fixtures, zero
  # real-repo touch, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_orphan_add.py"
}

t_registry_fix_anchor() {
  # REANCHOR-face tests for tools/registry_fix.py
  # (tests/test_registry_fix_anchor.py): the anchor residual gate
  # (A-fix-6 treated_anchors_canonical) plus the suite shell face — the
  # frozen --selftest marker, --help smoke, exit-code spot checks
  # (bogus=2/no-input=2/missing-audit-json=9), dry-run zero-write, apply
  # with the four assertion fields green, re-audit with executed keys
  # residual-free while skip-class keys stay by design, and six unit
  # vectors on the residual gate (blast on treated seq-form/malformed;
  # silent for untreated/collision/missing kinds). All on mkdtemp
  # fixtures, zero real-repo touch, zero network, zero compile.
  "$PY" -B "$REPO/tests/test_registry_fix_anchor.py"
}

t_norm_lint() {
  # annotation-face normalization linter hookup (tools/norm_lint.py;
  # tests/test_norm_lint.py minimal shell three checks: --selftest seven
  # vectors + --help smoke + exit-code spot checks 2/9 — report-only first
  # form, baseline account reports emitted; zero network, zero compile, zero
  # real-repo touch)
  "$PY" -B "$REPO/tests/test_norm_lint.py"
}

t_contrib_intake() {
  # contribution intake inspector (tools/contrib_intake.py): the protocol
  # four-check pipeline in one read-only run — registry/norm/gate
  # expectation/isolation gates never short-circuit, a BLOCK verdict is
  # data and the exit code stays 0. tests/test_contrib_intake.py minimal
  # shell, three checks: --selftest rc=0 with the CONTRIB-INTAKE-SELFTEST
  # PASS frozen marker (the tool's own dual-git-clone vectors attest the
  # four gates), --help smoke, exit-code spot checks bogus=2/no-input=2/
  # missing-face=9/bad-ref=9; tmp fixtures only, zero writes, zero
  # network, zero real-repository contact.
  "$PY" -B "$REPO/tests/test_contrib_intake.py"
}

t_evolve() {
  # autonomous evolution engine hook (tools/evolve.py):
  # harvest signal classes by subprocess of the existing engines, derive
  # scored candidates by fixed rules, draft the human-gated next-round task
  # brief (constitution three-law preamble auto-carried). tests/test_evolve.py
  # minimal shell, three checks: --selftest rc=0 with eleven PASS vector
  # groups (canned signal injection via real subprocesses and stub engines,
  # gate-health harvest, candidate rules, draft formation, frozen exclusion,
  # sentinel seen-idempotence, deterministic
  # double run), --help smoke, exit-code contract spot checks bogus=2/
  # no-draft=2/no-signal=2/watch-without-state=2/two-suite-sources=2/
  # missing-baseline=9/missing-parent=9; tmp fixtures only, zero writes,
  # zero network, zero real-repository contact, draft-only (never executes
  # a candidate).
  "$PY" -B "$REPO/tests/test_evolve.py"
}

t_registry_regen() {
  # contribution registration-row regenerator (tools/registry_regen.py):
  # merge-target books verbatim as the draft bottom plus canonical
  # #R<seq>-<md5-8> rows tail-appended in dependency order, dry run by
  # default, --apply writes only under an explicit --out.
  # tests/test_registry_regen.py minimal shell, three checks: --selftest
  # rc=0 with the REGISTRY-REGEN-SELFTEST PASS frozen marker (the tool's
  # own tmp-fixture vectors attest the regeneration semantics), --help
  # smoke, exit-code spot checks bogus=2/no-input=2/apply-without-out=2/
  # negative-seq=2/missing-base=9; tmp fixtures only, zero writes, zero
  # network, zero real-repository contact.
  "$PY" -B "$REPO/tests/test_registry_regen.py"
}

t_clean_mode() {
  # clean-mode switch selftest (tests/test_clean_mode.py · ROCWASH_CLEAN=1):
  # canonical-dependency faces report "requires canonical environment" and
  # refuse; default mode (env unset) stays unchanged; clean-available
  # selftest faces still pass under the switch. Zero compile, zero network,
  # zero writes outside mkdtemp. Census: docs/clean-mode-manual-20261114.md.
  "$PY" -B "$REPO/tests/test_clean_mode.py"
}

t_vacgen_shape() {
  # 20261114 recursive-self-healing-agent hookup: the vacgen four-account
  # skeleton shape selftest (tests/t_vacgen_shape.py; zeta-face fixture
  # shapes; four accounts, 8 files asserted on disk; zero compile, zero
  # network).  This case and t_vacgen_expectedred had been on disk since
  # 20261113 without a hookup (zero mentions in run_tests.sh = invisible to
  # the suite; the same gap as the RQW12 precedent); both hooked up this
  # round; the subprocess read face adds encoding=utf-8 (a GBK locale breaks
  # read-thread decoding; aligned with the expectedred read shape).
  "$PY" -B "$REPO/tests/t_vacgen_shape.py"
}

t_vacgen_expectedred() {
  # 20261114 recursive-self-healing-agent hookup: the vacgen expected-red
  # contract selftest (tests/t_vacgen_expectedred.py; three checks:
  # EXPECTED-FAIL per-face registration / counter-contract vectors /
  # red-green boundary; an expected red is data, not a tool failure; only an
  # unregistered red is a defect; zero compile, zero network).
  "$PY" -B "$REPO/tests/t_vacgen_expectedred.py"
}

t_vacgen_envelope_shape() {
  # 20261114 recursive-self-healing-agent new cast: the witness envelope word
  # face shape selftest (tests/t_vacgen_envelope_shape.py; fixture A pins the
  # well-formed-face contract (no bare-type disjuncts) + fixture B pins the
  # implicit-binder known debt (the debt signature with Set ( present = pinned
  # passing; re-pinned failing after an engine fix = update the pin per the
  # SOP section 2.5 erratum); the only machine check guarding the engine debt
  # registered 20261114; zero compile, zero network).
  "$PY" -B "$REPO/tests/t_vacgen_envelope_shape.py"
}

t_refinery() {
  # refinery merge contract suite (tests/t_refinery.py): aggregates the six
  # lane segments under tests/refinery_segments/ (seam / vacgen / gap /
  # render / calib / sweep) into one SUMMARY + TOTAL line. Import-safe,
  # zero network, zero compile; an absent segment file is one loud SKIP.
  "$PY" -B "$REPO/tests/t_refinery.py"
}

t_symbiosis_shape() {
  # 20261115 roster hookup (audit finding P0-6): cross-repository
  # experience bus shape shell (tests/t_symbiosis_shape.py over
  # tools/symbiosis_bus.py) - seven subprocess checks: the export schema
  # matrix (rocqwash-symbio/1 envelope), import through the single
  # exp_port append face (rocqwash-exp/1 rows), idempotent re-import,
  # status and diff faces, exit-code convention, dry-run zero-write.
  # Offline by construction, tmp fixtures only. Supersedes the file's
  # earlier standing "not rostered" note.
  "$PY" -B "$REPO/tests/t_symbiosis_shape.py"
}

t_bus_feeder_shape() {
  # 20261115 roster hookup (audit finding P0-6): gap-ledger feeder shape
  # shell (tests/t_bus_feeder_shape.py over tools/bus_feeder.py) - seven
  # checks: the tool's own frozen selftest group, the real sample
  # docs/symbiosis-swap-round1.jsonl through the dry-run face (read-only),
  # the export-to-gap-rows end-to-end leg, idempotent re-feed, damaged
  # package refusals, usage and exit codes, status mapping and the write
  # surface. Offline, tmp fixtures.
  "$PY" -B "$REPO/tests/t_bus_feeder_shape.py"
}

t_uplink_shape() {
  # 20261115 roster hookup (audit finding P0-6): external return-package
  # intake gate shell (tests/t_uplink_shape.py over tools/uplink.py) -
  # three faces on tmp zip+md5 fixtures: verify (fail-loud red on any
  # digest mismatch or missing member, per-file evidence), intake (exactly
  # one docs/uplink-intake.jsonl row, schema rocqwash-uplink/1, nothing
  # else written) and pr-prep (a draft file only, never opens a pull
  # request); the repository-tree checksum must stay unchanged.
  "$PY" -B "$REPO/tests/t_uplink_shape.py"
}

t_evolution_dashboard_shape() {
  # 20261115 roster hookup (audit finding P0-6): self-evolution dashboard
  # shape shell (tests/t_evolution_dashboard_shape.py over
  # tools/evolution_dashboard.py) - seven fixture checks (three-source
  # aggregation over rocqwash-exp/1 + rocqwash-round/1 + vacgen v2 report
  # faces, conversion math, coverageLowerPct curve ordering with the
  # TODO-SEAT delta, default/explicit absence rule, exit codes,
  # determinism of both output faces) plus one read-only live check over
  # the standing account paths.
  "$PY" -B "$REPO/tests/t_evolution_dashboard_shape.py"
}

t_mcp_face() {
  # 20261115 roster hookup (audit finding P0-6): MCP stdio server face
  # shell (tests/t_mcp_face.py spawning tools/mcp_server.py) - one
  # newline-delimited JSON-RPC session asserting the 25-capability face
  # (legacy 8 + batch-1 zero-network 13 + engine-body 3 + symbiosis 1)
  # plus live-call spot checks; zero network by construction.
  "$PY" -B "$REPO/tests/t_mcp_face.py"
}

t_exp_port() {
  # 20261115 roster hookup (audit finding P0-6): experience-bus port
  # shell (tests/t_exp_port.py over tools/exp_port.py) - four checks:
  # --selftest rc=0 with the EXP-PORT-SELFTEST PASS frozen marker, --help
  # usage face, exit-code spot checks (bogus=2, append without
  # --points=2, query on an absent ledger=9), copy dry-run reports a
  # would-be id and writes nothing.
  "$PY" -B "$REPO/tests/t_exp_port.py"
}

t_periscope_shape() {
  # 20261115 roster hookup (audit finding P0-6): periscope sweep shell
  # (tests/t_periscope_shape.py over tools/periscope.py) - six checks:
  # --selftest rc=0 with the PERISCOPE-SELFTEST PASS frozen marker, --help
  # naming the six CLI flags, exit-code convention spot checks, a valid
  # six-source config dry-run, the draft-template invariants (five
  # judgment-template sections plus four negative-finding element labels),
  # and the dry-run writing zero bytes.
  "$PY" -B "$REPO/tests/t_periscope_shape.py"
}

t_engines_body() {
  # 20261115 roster hookup (audit finding P0-6): engine-body contract
  # suite (tests/t_engines_body.py, nine segments / 60 checks over the
  # ai_flavor, jargon_apply, ai_flavor_apply, i18n_pipeline,
  # i18n_translate, i18n_verify and termbase modules) - clean and polluted
  # probes, exit codes, idempotence, zero-write defaults, nine-key ledger
  # validation, the default-deny network gate, the budget cap and the
  # legal refusal path; modules load dynamically from tools/ and a
  # not-yet-landed module is one loud SKIP line, never a silent pass.
  "$PY" -B "$REPO/tests/t_engines_body.py"
}

t_engines_seeds() {
  # 20261115 roster hookup (audit finding P0-6): five-engine seed
  # assertions (tests/t_engines_seeds.py, E1..E5 segments / 40 checks with
  # EXPECTED_SEGMENTS accounting); seeds are located relative to the file,
  # and off-machine anchors report SKIP with a reason, never a silent
  # pass; zero network, zero writes.
  "$PY" -B "$REPO/tests/t_engines_seeds.py"
}

t_evolve_flag_contract() {
  # 20261115 roster hookup (audit finding P0-6): evolve.py flag-face
  # contract pin (tests/test_evolve_flag_contract.py, four checks: the six
  # cycle-3 ask flags verbatim in the --help face, the
  # --sentinel-events/--sentinel-state pair accepted without --watch-repo,
  # a no-signal-source round exits 2 fail-loud, the registry pair against
  # a book-less repository exits 9 fail-loud); tmpdir fixtures, zero
  # network, zero repository writes.
  "$PY" -B "$REPO/tests/test_evolve_flag_contract.py"
}

t_watch_repo_form() {
  # 20261115 roster hookup (audit finding P0-6): cw_sentinel --watch-repo
  # ORG/REPO form negative vectors (tests/test_watch_repo_form.py, three
  # checks: a local-directory form and a bare token are both refused with
  # rc=2 and the ORG/REPO message, and the REPO_RE match gate stays
  # anchored in tools/cw_sentinel.py; the form check fires before any
  # fetch, zero network reached).
  "$PY" -B "$REPO/tests/test_watch_repo_form.py"
}

t_flaky_guard() {
  # 20261116 repair-class E2-3 hookup: flaky quarantine guard
  # (tools/flaky_guard.py; tests/test_flaky_guard.py four checks: the
  # tool's 32-vector sandbox --selftest (order-dependent vs content-red
  # verdicts / dry-run zero-write / apply with ledger row / idempotent
  # re-apply / three green rounds with ADVISORY-OUT / budget and
  # frozen-target refusals / restore both ways / scope invariant / CLI
  # codes) plus --help plus exit-code spots plus one read-only --status
  # against the standing repo; zero writes outside mkdtemp, zero network,
  # zero compile).
  "$PY" -B "$REPO/tests/test_flaky_guard.py"
}

t_roster_resync() {
  # 20261116 repair-class E2-2 hookup: roster count drift guard
  # (tools/roster_resync.py; tests/test_roster_resync.py four checks:
  # --selftest rc=0 with the ROSTER-RESYNC-SELFTEST PASS frozen marker,
  # --help rc=0, --bogus=2, a missing --repo directory=9; the guard's own
  # tmp-fixture selftest attests the real doc_lint consistent flip as the
  # green criterion, the one-way CASES roster derivation (the roster file
  # is never written), the per-class per-branch budget cap at 2, and the
  # shared repair_scope exclusion gate; zero writes outside mkdtemp, zero
  # network, zero compile).
  "$PY" -B "$REPO/tests/test_roster_resync.py"
}

t_auto_merge() {
  # 20261116 X5-gate hookup: auto-merge gate judge plus safety rail
  # (tools/auto_merge.py; tests/test_auto_merge.py five checks: --selftest
  # rc=0 with the AUTO-MERGE-SELFTEST PASS frozen marker (24 vectors incl.
  # the five calibration samples S-1..S-5 pinned to their verdicts, the
  # supply/* whitelist both ways, the daily budget cap, dry-run zero-write,
  # the duplicate refusals, the post-merge revert arc four families),
  # --help face, exit-code spots 2/9, the five calibration fixtures judged
  # through the real CLI face, dry-run zero-write plus the rail refusal
  # exit contract; tmp fixtures only, zero network, zero repository
  # writes).
  "$PY" -B "$REPO/tests/test_auto_merge.py"
}

t_selfheal_guards() {
  # 20261116 X6-agent hookup: the three self-heal guardrail reinforcement
  # points as frozen vectors (.github/scripts/selfheal_rocqwash.py;
  # tests/test_selfheal_guards.py five vector groups 20 checks: the
  # attempt cap skipped(attempt-cap) at-most-once budget, the
  # cancel-intent never-revive gate plus its cap-outranks-intent order
  # pin, the live re-check before the rerun POST (in-progress/cancelled/
  # transport-error all skip; only a still-completed run reaches exactly
  # one rerun-failed-jobs POST), the transient-only family whitelist, and
  # the reconcile intent recording (cancelled=intent, never revived, zero
  # POSTs).  The script module loads by path with gh_api/time stubbed
  # in-process: zero network, zero real sleep, zero repository writes.
  "$PY" -B "$REPO/tests/test_selfheal_guards.py"
}

t_jargon_map_sync() {
  # 20261117 P1 cast-agent hookup (normwave59 work stream): the jargon map sync
  # tool (tools/jargon_map_sync.py; tests/test_jargon_map_sync.py six
  # checks: --selftest rc=0 with the SYNC-SELFTEST PASS frozen marker (the
  # tool's own tmp-fixture vectors attest the single-form derivation with
  # the parenthetical-annotation stripping, the slash and fullwidth-slash
  # alternation rejects, the six note-guard rejects, the em-dash
  # rewrite-or-delete bucket, the upsert preserve rules for
  # id/exempts/cross_track_note, the exact count label, rerun
  # determinism, the duplicate-face refusal and the CLI faces), --help
  # rc=0, --bogus=2, a missing --map=9, the live plan face read-only
  # IN-SYNC over the standing map (zero bytes, exact count label), and a
  # tmp end-to-end arc (plan pending rc=1 zero-write, apply writes once,
  # second apply byte-identical); zero network, zero writes outside
  # mkdtemp, zero repository writes.
  "$PY" -B "$REPO/tests/test_jargon_map_sync.py"
}

t_tool_selftests() {
  # the tools/ selftest meta enumerator (tests/test_tool_selftests.py).
  # Enumerates every tools/*.py (leading-'_'
  # names excluded) and requires each tool to either pass its declared
  # --selftest face (rc=0; rc=111 SKIP by the suite contract) or carry the
  # in-file "# selftest-exempt: <basis>" registration.  Any red, missing, or
  # unregistered selftest fails with the tool names listed, so a tool
  # self-proof absence stays visible on every suite run and on both CI
  # faces.  Per-tool subprocess cap 120 seconds; zero network; zero writes
  # (python -B child runs; offline vector faces only).
  "$PY" -B "$REPO/tests/test_tool_selftests.py"
}

t_axiom_audit() {
  # the axiom-audit tool four-segment selftest (tests/t_axiom_audit.py).
  # Drives tools/axiom_audit.py (the beyond-platform axiom audit:
  # transitive per-statement census, four-grade classification, reverse
  # provenance map, machine-readable report with a Lean parity table)
  # through its contract: offline classification vectors and CLI
  # exit-code faces run module-local (no toolchain); the engine-gated
  # census and report faces assert exact axiom sets and grades over the
  # tests/fixtures/axiom_audit corpus on a resolving compile engine and
  # report one loud SKIP line with the reason when no engine resolves,
  # never a silent pass.  Exit contract 0/1 only, so the suite runner
  # reads it as PASS/FAIL with no SKIP face of its own; zero network;
  # writes only inside temporary directories.
  "$PY" -B "$REPO/tests/t_axiom_audit.py"
}

t_lean_parity() {
  # the Lean/Rocq parity crosswalk three-leg suite hook
  # (tests/t_lean_parity.py).  Drives tools/lean_parity_crosswalk.py
  # (the crosswalk engine: both parent tools' frozen vectors crosswalked
  # row by row on the five mirror proposition keys, the bilingual mirror
  # fixture group under tests/fixtures/lean_parity, the grade mapping
  # read verbatim from axiom_audit.LEAN_PARITY_ROWS) through its
  # contract: leg A the offline frozen-vector crosswalk runs
  # unconditionally with no engine; leg B the real axiom_audit census
  # over the mirror .v files runs on a resolving compile engine and
  # skips loudly otherwise; leg C the real lean_axiom_sweep over the
  # mirror .lean files runs on a usable Lean toolchain and skips loudly
  # otherwise ("SKIP: Lean toolchain absent - leg C not run").  Exit
  # contract 0 (all legs ran green) / 1 (any FAIL, red outranks skip) /
  # 111 (a gated leg skipped for its absent engine), so the suite runner
  # renders the Lean-absent face as SKIP; zero network; writes only
  # inside temporary directories.
  "$PY" -B "$REPO/tests/t_lean_parity.py"
}

# ---------- summary execution ----------

echo "== rocqwash tests/ self-test suite (repo=${REPO}) =="
for c in $CASES; do
  TOTAL=$((TOTAL + 1))
  if "$c" >"$LOG" 2>&1; then
    PASS=$((PASS + 1))
    printf '[%d/%d] %-26s PASS\n' "$TOTAL" "$NCASES" "$c"
  else
    rc=$?
    if [ "$rc" -eq 111 ]; then
      SKIP=$((SKIP + 1)); SKIPS="$SKIPS $c"
      printf '[%d/%d] %-26s SKIP (canonical environment absent, rc=111)\n' "$TOTAL" "$NCASES" "$c"
    else
      FAIL=$((FAIL + 1)); REDS="$REDS $c"
      printf '[%d/%d] %-26s FAIL (rc=%s)\n' "$TOTAL" "$NCASES" "$c" "$rc"
      echo "-------- $c output (first 40 lines) --------"
      sed -n '1,40p' "$LOG"
      echo "-------- $c output (last 20 lines) --------"
      tail -20 "$LOG"
      echo "------------------------------------"
    fi
  fi
done

echo "== summary: $PASS pass / $FAIL failing / $SKIP skipped / $TOTAL cases total =="
if [ "$SKIP" -ne 0 ]; then
  echo "skipped cases (canonical environment absent; the canonical machine runs the full sweep):$SKIPS"
fi
SUITE_RC=0
if [ "$FAIL" -ne 0 ]; then
  echo "failing cases:$REDS"
  SUITE_RC=1
fi

# ---------- env-gated gate-ledger append (standing suite ledger) ----------
# ROCWASH_GATE_LEDGER_DIR opts this run into the standing gate-ledger face:
# one row file <dir>/suite-<UTC-stamp>.txt carrying the run's rc, the UTC
# timestamp, the roster mode (full-roster or selection), and the canonical
# summary line — the standing suite-ledger data shape that tools/evolve.py
# SUITE_SUMMARY_RE and tools/flaky_guard.py SUMMARY_RES parse (timestamped
# row names sort chronologically, so the latest-wins lexicographic reading
# stays wall-clock-free).  The row is emitted through "$PY" with \u escapes
# so this face stays ASCII-only.  Unset (default): zero bytes written and
# the zero-write contract above holds unchanged.  An append failure prints
# a loud note on stderr and never flips the suite's own exit code (an
# unrecorded run leaves the ledger at its last row; the evolve reading
# reports the latest recorded row and a stale row is data, never failure).
if [ -n "${ROCWASH_GATE_LEDGER_DIR:-}" ]; then
  GL_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  GL_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  GL_MODE="full-roster"
  if [ -n "${ROCWASH_TESTS_ONLY:-}" ] || [ -n "${ROCWASH_TESTS_EXCLUDE:-}" ] \
     || [ -n "${_advisory:-}" ]; then
    GL_MODE="selection"
  fi
  if "$PY" -B -c '
import io
import os
import sys
d, stamp, ts, mode, rc, passed, red, skip, total = sys.argv[1:10]
try:
    os.makedirs(d, exist_ok=True)
    row = (
        "== rocqwash gate ledger row ==\n"
        "ts_utc: " + ts + "\n"
        "rc: " + rc + "\n"
        "mode: " + mode + "\n"
        "== \u6c47\u603b: " + passed + " \u8fc7 / " + red + " \u7ea2 / "
        + skip + " \u7565 / \u5171 " + total + " \u4f8b ==\n"
    )
    with io.open(os.path.join(d, "suite-" + stamp + ".txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(row)
except OSError as exc:
    sys.stderr.write("gate-ledger note: append failed (%s)\n" % exc)
    sys.exit(1)
' "$ROCWASH_GATE_LEDGER_DIR" "$GL_STAMP" "$GL_TS" "$GL_MODE" "$SUITE_RC" \
     "$PASS" "$FAIL" "$SKIP" "$TOTAL"; then
    echo "(gate-ledger) row appended: $ROCWASH_GATE_LEDGER_DIR/suite-$GL_STAMP.txt"
  else
    echo "(gate-ledger note) row append failed; the ledger stays at its last row" >&2
  fi
fi
exit $SUITE_RC
