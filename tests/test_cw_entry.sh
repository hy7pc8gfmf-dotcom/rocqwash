#!/bin/bash
# test_cw_entry.sh — selftest of the cw.sh unified entry (tests/).
#
# Purpose.  Behavioral check of the cw.sh routing layer, four sections:
#   (1) help-and-routing smoke — full tool table via help, no-arg usage
#   face, one-line hints, rc=2 on unknown tools, seven-tool --help
#   passthrough (argparse usage lines carry the target-script markers);
#   (2) functional passthrough — scan4 --json, dual-scan --out, chain on
#   a synthetic probe ledger, sync-ledger on a synthetic pair (rc=1 is
#   the ledger_sync documented "sync completed with findings; the new
#   ledger is still written" convention), cure --selftest, erasure
#   --selftest, no-arg probe FAIL-LOUD rc=2;
#   (3) zero-hardcoding proof — an empty-directory cw.sh copy routes scan4
#   to rc=9 (missing target script), proving repo-root-relative routing;
#   (4) bash 3.2 compatibility — /bin/bash -n syntax check.
#
# Interface.  bash tests/test_cw_entry.sh (no arguments); registered as
#   the t_cw_entry lane of tests/run_tests.sh; the expect_rc / expect_grep /
#   expect_file_nonempty helpers print one FAIL line per miss on stderr.
#
# Dependencies.  bash 3.2, python3, the read-only fixture
#   tests/fixtures/names_sample.v, the repository cw.sh; zero network,
#   zero real compiles, zero writes into the repository.
#
# Evidence.  Inputs are mktemp-synthesized or read-only fixture data; all
#   outputs land in the mktemp directory under a trap; reruns are idempotent.
#
# Exit-codes.  0 all assertions passed; 1 at least one failing assertion
#   (each miss listed on stderr, fail-loud).
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
CW="$REPO/cw.sh"
FIX="$REPO/tests/fixtures"
PY=python3

TMP=$(mktemp -d /tmp/rocqwash_cw_entry.XXXXXX)
trap 'rm -rf "$TMP"' EXIT INT TERM

PASS=0
FAIL=0

expect_rc() {  # $1=description $2=expected rc $3=observed rc
  # an absent/empty observation counts as a FAIL, never a harness crash:
  # command-substitution call sites $(grep -c ...) yield no third argument
  # when the file is missing, and under set -u an unset $3 aborted the
  # whole script mid-report (the 20261126 patrol face)
  if [ "${3:-x}" -eq "$2" ] 2>/dev/null; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — expected rc=$2, observed rc=${3:-<empty>}" >&2
  fi
}

expect_grep() {  # $1=description $2=expected hit count $3=observed hit count
  if [ "${3:-x}" -eq "$2" ] 2>/dev/null; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — expected $2 hits, observed ${3:-<empty>}" >&2
  fi
}

expect_file_nonempty() {  # $1=description $2=path
  if [ -s "$2" ]; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
    echo "FAIL: $1 — file missing or empty: $2" >&2
  fi
}

# ---------- Section 1: help and routing smoke ----------

bash "$CW" help >"$TMP/help.out" 2>&1
expect_rc "help rc" 0 $?
expect_grep "help output carries the seven tool target-script paths" 7 \
  $(grep -c "scan_v4_token\.py\|cure_applier\.py\|probe_engine\.py\|chain_graph\.py\|ledger_sync\.py\|erasure_classifier\.py\|dual_scan\.py" "$TMP/help.out")

bash "$CW" >"$TMP/noargs.out" 2>&1
expect_rc "no-arg usage rc" 0 $?
expect_grep "no-arg output carries Usage" 1 $(grep -c "Usage" "$TMP/noargs.out")

bash "$CW" help scan4 >"$TMP/hs4.out" 2>&1
expect_rc "help scan4 rc" 0 $?
expect_grep "help scan4 one-line hint carries the target script" 1 $(grep -c "scan_v4_token\.py" "$TMP/hs4.out")

bash "$CW" help bogus >/dev/null 2>&1
expect_rc "help unknown tool rc=2" 2 $?

bash "$CW" bogus >/dev/null 2>"$TMP/unk.err"
expect_rc "unknown tool rc=2" 2 $?
expect_grep "unknown-tool stderr carries the phrase unknown tool" 1 $(grep -c "unknown tool" "$TMP/unk.err")

# seven-tool --help passthrough smoke (asserts the argparse usage line carries the target-script basename marker)
for pair in \
  "scan4 scan_v4_token.py" \
  "cure cure_applier.py" \
  "probe probe_engine" \
  "chain chain_graph" \
  "sync-ledger ledger_sync" \
  "erasure erasure_classifier.py" \
  "dual-scan dual_scan.py"
do
  set -- $pair
  tool="$1"; marker="$2"
  bash "$CW" "$tool" --help >"$TMP/th.out" 2>&1
  expect_rc "$tool --help passthrough rc" 0 $?
  expect_grep "$tool --help output carries the $marker marker" 1 \
    $(grep -c "$marker" "$TMP/th.out")
done

# ---------- Section 2: functional passthrough ----------

bash "$CW" scan4 --file "$FIX/names_sample.v" --json "$TMP/s4.json" >/dev/null 2>&1
expect_rc "scan4 --file fixture --json rc" 0 $?
expect_file_nonempty "scan4 census JSON written" "$TMP/s4.json"
expect_grep "scan4 JSON carries the md5 fingerprint" 1 $(grep -c '"md5"' "$TMP/s4.json")

bash "$CW" dual-scan --file "$FIX/names_sample.v" --out "$TMP/ds.json" >/dev/null 2>&1
expect_rc "dual-scan --file --out rc" 0 $?
expect_file_nonempty "dual-scan report JSON written" "$TMP/ds.json"
expect_grep "dual-scan JSON carries the diff field" 1 $(grep -c '"diff"' "$TMP/ds.json")

# chain: a synthetic single-piece probe ledger (rocqwash-probe-ledger/1 records shell; the missing field used directly)
printf '{"records": {"A1.v": {"file": "A1.v", "rc": 1, "red": "Unable to locate library FooBar", "missing": "FooBar"}}}' >"$TMP/p.json"
bash "$CW" chain "$TMP/p.json" --json "$TMP/cg.json" >/dev/null 2>&1
expect_rc "chain synthetic ledger rc" 0 $?
expect_file_nonempty "chain chain-root graph JSON written" "$TMP/cg.json"
expect_grep "chain JSON carries the schema field" 1 $(grep -c '"schema"' "$TMP/cg.json")

# sync-ledger: a synthetic probe x status ledger pair (the five ledger_sync required columns, see the printf data row).
# The expected rc=1 is the ledger_sync documented convention "sync completed with findings (NO-MD5 and the like); the new ledger is still written".
printf '件名\tmd5\tRED\t状态\t备注\nA1.v\tdeadbeef\t1\t待洗\t-\n' >"$TMP/l.tsv"
bash "$CW" sync-ledger --probe "$TMP/p.json" --ledger "$TMP/l.tsv" \
  --out "$TMP/o.tsv" --report "$TMP/r.json" >/dev/null 2>&1
expect_rc "sync-ledger synthetic sync rc=1 (completed with findings)" 1 $?
expect_file_nonempty "sync-ledger new ledger written" "$TMP/o.tsv"
expect_file_nonempty "sync-ledger report JSON written" "$TMP/r.json"

bash "$CW" cure --selftest >/dev/null 2>&1
expect_rc "cure --selftest passthrough rc" 0 $?

bash "$CW" erasure --selftest >/dev/null 2>&1
expect_rc "erasure --selftest passthrough rc" 0 $?

bash "$CW" probe >"$TMP/pn.out" 2>"$TMP/pn.err"
expect_rc "probe no-arg FAIL-LOUD passthrough rc=2" 2 $?
# 2 hits = the cw.sh no-arg one-line hint plus the probe_engine FAIL-LOUD "--candidates is required" line, one each
expect_grep "probe no-arg stderr carries --candidates (hint plus FAIL-LOUD, two sources)" 2 \
  $(grep -c -- "--candidates" "$TMP/pn.err")

# ---------- Section 3: zero-hardcoding behavioral proof ----------

mkdir -p "$TMP/lonely"
cp "$CW" "$TMP/lonely/cw.sh"
bash "$TMP/lonely/cw.sh" scan4 --help >/dev/null 2>"$TMP/lonely.err"
expect_rc "empty-directory copy routes scan4 expecting rc=9 (missing target script = repo-relative-path behavioral proof)" 9 $?
expect_grep "rc=9 stderr names the missing relative path" 1 \
  $(grep -c "missing scan/scan_v4_token.py" "$TMP/lonely.err")

# ---------- Section 4: bash 3.2 compatibility ----------

/bin/bash -n "$CW" 2>/dev/null
expect_rc "/bin/bash -n syntax check (3.2 compatible)" 0 $?

# ---------- Summary ----------

echo "== test_cw_entry: $PASS passed / $FAIL failing =="
if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
