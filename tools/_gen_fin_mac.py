#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_gen_fin_mac.py — Mac adaptation generator for the censusFIN probe template (S-series
    Prop-elimination effort · toolchain Mac-adaptation lane).
    Purpose.  Emit the Mac-form censusFIN probe triple from a source .v module: the probe skeleton
      (statement-name list → named transparent aliases → single-command multi-name Separate
      Extraction), the manifest, and the guard-wrapped fire driver. Lineage
      censusFIN/SortAlive_Probe_FIN1640.v — the SortAlive __-census check: statement names →
      named aliases → one-command Separate Extraction (per-command output reset is
      last-write-wins, so multi-target must be one command) → parse `(** val alive_N : ... **)`
      annotations and let bodies; `RED` iff `"__"` (extraction-erasure semantics; the
      lexicon-independent kernel-level judgment of non-negotiable-constraint ② gate 6).
    Interface.  python3 _gen_fin_mac.py --source <Module.v> --module <ModuleName> \
      --world <worldT_dir> --world-name <W> --outdir <dir> [--requires S01_BaseRing,...];
      default --requires = the ladder world chain S01_BaseRing..S09_EntropyReal up to --module;
      emits SortAlive_Probe_<W>.v, manifest_<W>.json, _fire_fin_<W>.sh (mode 0755). Dry-run
      verification: cd <outdir> && bash _fire_fin_<W>.sh && python3 _parse_fin_mac.py
      SortAlive_Probe_<W>.ml --manifest manifest_<W>.json --vo SortAlive_Probe_<W>.vo
      --source-v <source.v> --transcript _fin_<W>_build.log (verify on worldT_mac S09 while
      S10.vo is not passing; S10 live runs excluded; census 100/100 is the recorded expected baseline).
    Dependencies.  mac_stmt_names.py (<repo>/names, sys.path-injected; its extraction core is
      reused so the statement list shares the census grain — same token walk, same list);
      Python 3 standard library only; bash for the emitted driver.
    Evidence.  Field-verified at the October 22, 2026 Mac-adaptation pass (worldT_mac S09 dry run,
      census 100/100 recorded expected baseline; anomalies and the zero-statement case fail loud in main(), never silent).
    Exit-codes.  0 = probe, manifest and driver written; 9 = fail-loud (missing source or world
      dir, zero statements)."""
import argparse
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "names"))  # mac_stmt_names.py sits at <repo>/names
# reuse mac_stmt_names.py's extraction core (same token walk = the census-grain statement list): list consistency is guaranteed by the shared tool
import mac_stmt_names  # noqa: E402

LADDER = ["S01_BaseRing", "S02_CauchyComplete", "S03_QExp", "S04_RealExpLogConv",
          "S05_AlignmentGRPO", "S06_DiffSamplingGibbs", "S07_RealSetoidExpLog",
          "S08_RealMainlineDPO", "S09_EntropyReal", "S10_KVQuantTrig",
          "S11_TP3B5", "S12_B5RecycleSF", "S13_NLiveAudit", "S14_B5BatchBlock"]

COQC_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq"
OPAM_ENV_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/bin/opam env --switch live --root /Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam --set-root"
COQ_ARG = "c"  # rocq c = the coqc-compatible subcommand (Rocq 9.1)
COQLIB_MAC_DEFAULT = "/Users/apple/actions-runner/mac_rocq/lib/coq"
GUARD_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"

DRIVER_TMPL = r"""#!/bin/bash
# censusFIN_mac fire driver — world <WNAME> (Mac form, guard-wrapped, SW2 double export)
# box-ledger discipline: cmd (this file) + exit + log, three records per box; the exit code is coqc's real code (guard pass-through, no pipe).
#
# Mac pitfall note (measured at the October 22, 2026 Mac-adaptation pass): mac_rocq/bin/coqc is a shim — internally it
# re-runs `source env.sh` -> `opam env` (0.2s CPU, transient at normal priority, frozen in a nice19 crowded window) then
# exec rocq — environment resolution inside a guard nice19 process is a starvation trap. This driver pre-resolves the
# env in the driver shell (normal priority, not a compile) and lets the guard wrap the real `rocq c`; the compile body stays fully guard-wrapped (the §R2 invariant is unchanged).
set -u
COQC="${{COQC:-{coqc}}}"
COQARG="{coqarg}"
export COQLIB="${{COQLIB:-{coqlib}}}"
export ROCQLIB="${{ROCQLIB:-{coqlib}}}"
GUARD="${{GUARD:-{guard}}}"
WORLD="{world}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
echo "[fin-mac] guard=$GUARD world=$WORLD coqc=$COQC $COQARG" >&2
# env pre-resolve (not a compile · normal priority · ~0.2s; failure is fail-loud)
if [ -x /Users/apple/Desktop/ConstructiveWorld/Live/toolchain/bin/opam ]; then
  eval "$({opam_env} 2>/dev/null)" || {{ echo "FAIL-LOUD: opam env pre-resolve failed" >&2; exit 9; }}
fi
# crowded-window note (second correction, October 22, 2026): nice19 BACK tier is usable for the rocq c body itself (the
# piu_zz precedent worker measured 24-33% CPU); the real pitfall was the shim's opam env root lock, cured by the env
# pre-resolve. MaxWaitSec stays at the guard default 900s: after a 15 min window wait a BACK run finishes in 1-2 min.
# Never lengthen MaxWaitSec — a long item holding a slot blocks the queue (slots held for the whole command; the seq1 giant-item + seq3 frozen-coqchk placeholder precedent).
"$GUARD" -Front "${{FRONT:-{front}}}" -Mid "${{MID:-{mid}}}" -MaxWaitSec "${{MAXWAIT:-900}}" -- \
  "$COQC" "$COQARG" -native-compiler no -q -Q "$WORLD" "" SortAlive_Probe_{wname}.v \
  > _fin_{wname}_build.log 2>&1
rc=$?
echo "$rc" > _fin_{wname}.exit
tail -8 _fin_{wname}_build.log >&2
exit $rc
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="target module .v source (the statement-list extraction base)")
    ap.add_argument("--module", required=True, help="target module name (e.g. S09_EntropyReal)")
    ap.add_argument("--world", required=True, help="world directory (-Q <world> \"\")")
    ap.add_argument("--world-name", required=True, help="probe-file suffix (e.g. S09DRT)")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--requires", help="comma-separated Require chain; default = the ladder world chain up to --module")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not os.path.exists(args.source):
        print("FAIL-LOUD: source missing:", args.source)
        sys.exit(9)
    if not os.path.isdir(args.world):
        print("FAIL-LOUD: world dir missing:", args.world)
        sys.exit(9)
    requires = ([r.strip() for r in args.requires.split(",") if r.strip()]
                if args.requires else LADDER[:LADDER.index(args.module) + 1])
    if args.module not in requires:
        requires.append(args.module)

    inv = mac_stmt_names.extract_statements(args.source, include_let=False)
    stmts = inv["statements"]
    if inv["anomalies"]:
        print("ANOMALIES (fail-loud, itemized; never silent):", inv["anomalies"])
    if not stmts:
        print("FAIL-LOUD: zero statements extracted from", args.source)
        sys.exit(9)

    os.makedirs(args.outdir, exist_ok=True)
    w = args.world_name
    lines = []
    lines.append("(* SortAlive Probe %s -- censusFIN_mac (Mac form; template lineage "
                 "SortAlive_Probe_FIN1640.v) *)" % w)
    lines.append("(* spec source: E-STAGING-1484-PROPCLEAN-RECIPEBOOK section 5.1; "
                 "single-command multi-name Separate Extraction per cw-ci-sop §1·E law1 *)")
    lines.append("From Stdlib Require Import Extraction.")
    for mod in requires:
        lines.append("Require Import %s." % mod)
    for k, s in enumerate(stmts):
        lines.append("Definition alive_%d := %s.%s." % (k, args.module, s["name"]))
    names = " ".join("alive_%d" % k for k in range(len(stmts)))
    lines.append("Separate Extraction %s." % names)
    probe_v = os.path.join(args.outdir, "SortAlive_Probe_%s.v" % w)
    with io.open(probe_v, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    manifest = {"world": w, "source": os.path.abspath(args.source),
                "module": args.module, "requires": requires,
                "statements": [{"idx": k, "name": s["name"], "kind": s["kind"],
                                "decl_line": s["decl_line"]}
                               for k, s in enumerate(stmts)],
                "skips": inv["skips"], "anomalies": inv["anomalies"]}
    manifest_j = os.path.join(args.outdir, "manifest_%s.json" % w)
    with io.open(manifest_j, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=1))

    driver = os.path.join(args.outdir, "_fire_fin_%s.sh" % w)
    with io.open(driver, "w", encoding="utf-8", newline="\n") as f:
        f.write(DRIVER_TMPL.format(
            wname=w, world=os.path.abspath(args.world),
            coqc=COQC_MAC_DEFAULT, coqarg=COQ_ARG, opam_env=OPAM_ENV_MAC_DEFAULT,
            coqlib=COQLIB_MAC_DEFAULT,
            guard=GUARD_MAC_DEFAULT, front=1, mid=0))
    os.chmod(driver, 0o755)

    print(json.dumps({"probe": probe_v, "manifest": manifest_j, "driver": driver,
                      "statements": len(stmts), "requires": requires,
                      "let_skipped": inv["let_skipped"],
                      "anomalies_n": len(inv["anomalies"]),
                      "note": "compilation must run through the driver's cpu_guard wrap (-Front 1 -Mid 0);"
                              "parse with _parse_fin_mac.py (the ann :\\s* dual-form tolerance)"},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
