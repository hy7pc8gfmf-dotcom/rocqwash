#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cw_doctor.py — aggregate health doctor: four-domain rollup (rocqwash tools/).

Purpose.  One-shot overall health assessment: orchestrates the existing
  per-domain tools over four domains, each driven by subprocess (write
  orchestration, never re-implementation — each tool's CLI and JSON schema
  are read before wiring; a tool failure or malformed report is fail-loud;
  zero new engines), and aggregates them into an overall health score 0-100
  plus a per-domain verdict plus an advice list (one entry per non-passing
  domain, pointing at the corresponding tool).  Domain 1 env (weight 40) =
  subprocess toolchain_dyld_doctor (the worker default probe is decided
  inside that tool: flag / env ROCWASH_ROCQWORKER / the sanctioned-machine
  default) -> report verdict healthy|missing-libs|worker-missing ->
  healthy scores 100, anything else 0 (a failing result is data, not a tool
  failure).  Domain 2 net (20) = subprocess net_probe --rounds 1 --interval
  0 (the default four endpoints) -> report verdict all-up|partial|all-down
  (without --stable-window, net_probe exit 0 only means the probe completed
  — reachability is read from the report's verdict field, not the exit
  code) -> score = reachability rate x 100.  Domain 3 registry (25) =
  --registry PATH explicit (missing ledger fails loud 9) > env CW_SET
  /ConstructiveWorld_Live/order.txt probe (a missing ledger skips honestly)
  > none skips -> the anchor canonical-form audit: the compliance rate of
  the #R<seq>-<md5_8> form -> score = rate x 100.  Domain 4 clog (15) =
  --src DIR (skipped by default) + --sample N (default 0 = no sampling ->
  the domain skips honestly; the domain is active only with --src and
  --sample>0) -> whole-tree canonical-order .v enumeration -> equidistant
  sampling -> candidates TSV -> subprocess probe_engine --fresh -> ledger ->
  chain_graph --top 1 always runs (pure stdlib, zero compiles, zero
  network; real orchestration, never a puppet) -> the red-account rate
  (stats.rc1 union stats.other) -> score = (1 - red rate) x 100, plus a TOP
  entry when a missing-library chain root exists.

Interface.  python3 tools/cw_doctor.py [--json OUT] [--workdir DIR]
  [--registry PATH] [--src DIR --sample N [--world DIR]] [--worker PATH]
  [--donor DIR] [--endpoints URL[,URL...]] [--guard PATH] [--guard-reg DIR]
  [--guard-maxwait S] [--timeout S] [--rocq-cmd TPL] [--injector DIR]
  | --selftest.  Report schema rocqwash-cwdoctor/1.  Score = sum(domain
  score x weight) / sum(active weights) (skipped domains drop their weight;
  round 2 places); verdict healthy (>=90) | degraded (<90).  Advice: env ->
  trace and restore with toolchain_dyld_doctor (advice only, never
  auto-executed); net -> a two-probe stable window with net_probe
  --stable-window; registry -> re-anchor to the canonical form with
  registry_union --reanchor; clog -> clear blockages with the unclog closed
  loop; a skipped domain -> pass its switch and re-run.  Offline-testable:
  --injector DIR/scenario.json = {engine key: {"rc": int, "stdout": str,
  "report": dict}} with the fixed key set dyld/net/probe (the wash_shape
  Injector contract; unknown key -> 2); the canned table must cover every
  tool call this run will issue (a missing key -> 9; it never silently
  falls through to the real tool on the real network).  Determinism: the
  report carries no wall-clock field, every path is a basename, sort_keys
  on write; same input and environment rerun byte-identical.

Dependencies.  Python 3 standard library only; every path parameterized
  except the sanctioned --guard default (the ConstructiveWorld cpu_guard.sh
  path, the same default as toolchain_dyld_doctor; overridable).  Zero
  sleeps, zero loops in this tool itself (--sleep-scale is irrelevant; the
  net round interval is always 0).

Evidence.  --selftest frozen vectors on a tmp fixture tree with canned
  subprocess-layer injection (zero real otool, zero real network, zero real
  compiles; chain_graph and the registry audit run for real — pure stdlib):
  the four-domain all-green 100, the env-red 60.0 degradation, the registry
  skip renormalization 86.67 plus the CW_SET missing-ledger honest skip,
  the clog TOP injection 88.75, advice generation, JSON idempotence,
  CLI four codes with canned full-coverage, and the registry-audit unit;
  suite membership tests/test_cw_doctor.py.

Exit-codes.  0 = healthy (overall score >= 90); 1 = degraded (< 90, the
  failing domains reported loudly — a domain failure is data, not a tool
  failure); 2 = usage error (argparse / negative --sample / invalid
  --timeout / malformed injector scenario / unknown key); 9 = missing
  (tool missing / explicit --registry ledger missing / --src directory
  missing / --world missing for a real probe / --guard missing / --src with
  zero candidates / injector scenario missing, canned not covering /
  subprocess tool failure / unrecognized report schema / registry decode
  failure).
"""
# Extended contract (kept outside the five-field block per the annotation
# standard 30-line header budget):
# domain 4 pipeline detail: whole-tree canonical-order enumeration (the unclog
# form), equidistant sampling at i*total//N indexes (N >= tree size means a
# full census, no sampling), candidates TSV, probe_engine --fresh (a real probe
# requires --world; --guard defaults to the ConstructiveWorld cpu_guard.sh
# thermal wrapper — the same sanctioned default as toolchain_dyld_doctor,
# overridable via --guard), the probe ledger, chain_graph --top 1 (always runs
# for real), the red-account rate over stats.rc1 union stats.other, and a TOP
# entry (the first top_order name with its n and self washability) when a
# missing-library chain root exists.
# canned rc semantics follow the real tools: dyld rc in {0,1,9} with a
# parseable report is data (1/9 = a data-side failure); rc=2 / missing report /
# malformed = tool failure 9; net/probe rc != 0 = tool failure 9.  A canned
# probe ledger is written to the workdir verbatim and still feeds the real
# chain_graph (real orchestration, never a puppet).
# anchor canonical form: #R<seq>-<md5 first 8 lowercase hex> — the
# registry_union.md5_8_of product form; ANCHOR_RE mirrors registry_union.py:81
# 1:1; comment lines and blank lines are not audited (the key_of semantics);
# anchorless body rows count into no_anchor and stay out of the compliance-rate
# denominator; the non-form list caps at 20 with the total reported honestly.

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROG = "cw_doctor"
SCHEMA = "rocqwash-cwdoctor/1"

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
TOOL_DYLD = os.path.join(TOOLS_DIR, "toolchain_dyld_doctor.py")
TOOL_NET = os.path.join(TOOLS_DIR, "net_probe.py")
TOOL_PROBE = os.path.join(REPO_ROOT, "wash", "probe_engine.py")
TOOL_CHAIN = os.path.join(TOOLS_DIR, "chain_graph.py")

SCHEMA_DYLD = "rocqwash-dyld-doctor/1"
SCHEMA_NET = "rocqwash-net-probe/1"
SCHEMA_PROBE = "rocqwash-probe-ledger/1"
SCHEMA_CHAIN = "rocqwash-chain-graph/1"

DOMAIN_ORDER = ("env", "net", "registry", "clog")
WEIGHTS = {"env": 40, "net": 20, "registry": 25, "clog": 15}
HEALTHY_MIN = 90.0
NON_FORM_CAP = 20

# anchor shape mirrors registry_union.py:81 ANCHOR_RE 1:1; the canonical form is
# #R<seq>-<first 8 lowercase hex of md5> (the registry_union.md5_8_of =
# hexdigest()[:8] product form)
ANCHOR_RE = re.compile(r"#(R\d+(?:-[0-9A-Fa-f]+)?)")
CANON_ANCHOR_RE = re.compile(r"R\d+-[0-9a-f]{8}")

ENV_REGISTRY = "CW_SET"
REGISTRY_REL = ("ConstructiveWorld_Live", "order.txt")
# the sanctioned-machine default (the same DEFAULT_GUARD as
# toolchain_dyld_doctor.py; overridable via --guard)
DEFAULT_GUARD = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (`docs/clean-mode-manual-20261114.md`). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"


class UsageError(Exception):
    """Usage error / malformed scenario shape (exit 2)."""


class MissingInput(Exception):
    """Missing input (exit 9)."""


class ToolError(Exception):
    """Orchestrated tool failure / malformed report (exit 9; fail-loud, silent degradation forbidden)."""


# ---- small pieces (deterministic helpers; local copies of the unclog/wash_shape forms; no package layout, no cross-imports) ----

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def basename_of(p):
    return os.path.basename(p.rstrip(os.sep)) if p else p


def dump_json(obj, path):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_json(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, UnicodeDecodeError, OSError) as e:
        raise ToolError("%s JSON malformed: %s (%s)" % (what, path, e))


def run_py(tool_path, cli):
    """The python3 -B <tool> <cli> subprocess single point (stdout+stderr
    merged; the unclog form).  Missing tool -> 9."""
    if not os.path.isfile(tool_path):
        raise MissingInput("toolchain file missing: %s" % tool_path)
    p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def write_cands_tsv(path, pairs):
    """Candidates TSV (name/md5 columns; the probe_engine-required column form; the unclog form).  KEEP (data face): the header row is probe_engine's required TSV vocabulary."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("件名\tmd5\n")
        for name, md5 in pairs:
            fh.write("%s\t%s\n" % (name, md5))


def enumerate_tree(src):
    """Whole-tree enumeration of --src *.v -> [(name (relative path, /
    separated, .v stripped), md5)] (deterministic, doubly sorted; the unclog
    form)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, src).replace(os.sep, "/")
                out.append((rel[:-2], md5_of(fp)))
    return out


def sample_pairs(pairs, n):
    """Deterministic equidistant sampling: on the canonical-order enumeration
    take the i*total//N indexes (for total>n the span length guarantees the
    multiples exist -> strictly increasing, never repeated indexes); N>=total
    means a full census (no sampling)."""
    total = len(pairs)
    if n >= total:
        return list(pairs)
    out, seen = [], set()
    for i in range(n):
        idx = i * total // n
        if idx not in seen:
            seen.add(idx)
            out.append(pairs[idx])
    return out


# ---- injection point: the subprocess call layer, canned (offline testability; the wash_shape Injector form) ----

class Injector(object):
    """--injector DIR: canning the subprocess call layer (DIR/scenario.json;
    the unclog form).  Scenario JSON {engine key: {"rc": int, "stdout": str,
    "report": dict}}; key set = dyld/net/probe; a tool call whose key matches
    always returns the canned response — no real subprocess.  The canned table
    must cover every tool call this run will issue (checked up front in run();
    a missing key -> 9 — it never silently falls through to the real tool on
    the real network; the cw_sentinel rule)."""

    KEYS = ("dyld", "net", "probe")

    def __init__(self, dirpath):
        sj = os.path.join(dirpath, "scenario.json")
        if not os.path.isfile(sj):
            raise MissingInput("injector scenario missing: %s" % sj)
        try:
            with io.open(sj, "r", encoding="utf-8") as fh:
                scen = json.load(fh)
        except Exception as e:
            raise UsageError("injector scenario JSON malformed: %s (%s)" % (sj, e))
        if not isinstance(scen, dict):
            raise UsageError("injector scenario must be a dict: %s" % sj)
        bad = [k for k in scen if k not in self.KEYS]
        if bad:
            raise UsageError("unknown injector scenario key (need one of %s):"
                             " %s" % (",".join(self.KEYS), sorted(bad)))
        for k, ent in sorted(scen.items()):
            rc = ent.get("rc") if isinstance(ent, dict) else None
            if (not isinstance(ent, dict)
                    or not isinstance(rc, int) or isinstance(rc, bool)
                    or not isinstance(ent.get("stdout", ""), str)
                    or not isinstance(ent.get("report", {}), dict)):
                raise UsageError("injector canned entry %r malformed (need"
                                 " {rc:int, stdout?:str, report?:dict}): %r"
                                 % (k, ent))
        self.scen = scen

    def require(self, keys):
        """Canned full-coverage precheck (a missing key -> 9; prevents a half-canned run from silently falling through to the real tool on the real network)."""
        miss = [k for k in keys if k not in self.scen]
        if miss:
            raise MissingInput("injector canned does not cover %s (the canned"
                               " table must cover every tool call about to be"
                               " issued; it never silently falls through to the"
                               " real tool on the real network)"
                               % ",".join(miss))

    def take(self, key):
        ent = self.scen[key]
        return ent.get("rc", 0), ent.get("stdout", ""), ent.get("report")


# ---- domain 1: env ----

def domain_env(args, workdir, inj):
    """Domain 1 env: subprocess toolchain_dyld_doctor --json (the worker
    default probe is decided inside that tool; --worker/--donor pass through).
    verdict healthy scores 100, anything else 0; rc in {0,1,9} with a report is
    data (1/9 = a data-side failure); rc=2 / missing report / malformed = tool
    failure 9."""
    report_path = os.path.join(workdir, "dyld.json")
    if inj is not None:
        rc, out, rep = inj.take("dyld")
        dump_json(rep, report_path)
    else:
        cli = ["--json", report_path]
        if args.worker:
            cli += ["--worker", args.worker]
        if args.donor:
            cli += ["--donor", args.donor]
        rc, out = run_py(TOOL_DYLD, cli)
        rep = load_json(report_path, "dyld report") \
            if os.path.isfile(report_path) else None
    if rep is None:
        raise ToolError("toolchain_dyld_doctor tool failure rc=%d (no report"
                        " written): %s" % (rc, out[-300:]))
    if rc not in (0, 1, 9):
        raise ToolError("toolchain_dyld_doctor tool failure rc=%d: %s" % (rc, out[-300:]))
    if not isinstance(rep, dict) or rep.get("schema") != SCHEMA_DYLD:
        raise ToolError("dyld report schema unrecognized: %r (expected %s)"
                        % (rep.get("schema") if isinstance(rep, dict) else rep,
                           SCHEMA_DYLD))
    verdict = rep.get("verdict")
    if verdict not in ("healthy", "missing-libs", "worker-missing"):
        raise ToolError("dyld report verdict unrecognized: %r" % (verdict,))
    refs = rep.get("external_refs")
    if not isinstance(refs, list):
        raise ToolError("dyld report external_refs malformed: %r" % (refs,))
    for e in refs:
        if not isinstance(e, dict) or not isinstance(e.get("path"), str) \
                or not isinstance(e.get("exists"), bool):
            raise ToolError("dyld report external_refs entry malformed: %r" % (e,))
    missing = [e["path"] for e in refs if not e["exists"]]
    return {"status": "ok", "weight": WEIGHTS["env"],
            "tool": "tools/toolchain_dyld_doctor.py", "rc": rc,
            "worker": basename_of(rep.get("worker")), "verdict": verdict,
            "score": 100.0 if verdict == "healthy" else 0.0,
            "external_refs": len(refs), "missing_refs": missing}


# ---- domain 2: net ----

def domain_net(args, workdir, inj):
    """Domain 2 net: subprocess net_probe --rounds 1 --interval 0 (the default
    four endpoints; --endpoints overridable).  Without --stable-window,
    net_probe exit 0 only means the probe completed — reachability is read
    from the report's verdict field; score = reachability rate x 100."""
    report_path = os.path.join(workdir, "net.json")
    if inj is not None:
        rc, out, rep = inj.take("net")
        dump_json(rep, report_path)
    else:
        cli = ["--rounds", "1", "--interval", "0", "--json", report_path]
        if args.endpoints:
            cli += ["--endpoints", args.endpoints]
        rc, out = run_py(TOOL_NET, cli)
        rep = load_json(report_path, "net report") \
            if os.path.isfile(report_path) else None
    if rc != 0:
        raise ToolError("net_probe tool failure rc=%d: %s" % (rc, out[-300:]))
    if not isinstance(rep, dict) or rep.get("schema") != SCHEMA_NET:
        raise ToolError("net report schema unrecognized: %r (expected %s)"
                        % (rep.get("schema") if isinstance(rep, dict) else rep,
                           SCHEMA_NET))
    verdict = rep.get("verdict")
    if verdict not in ("all-up", "partial", "all-down"):
        raise ToolError("net report verdict unrecognized: %r" % (verdict,))
    rounds = rep.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise ToolError("net report rounds malformed: %r" % (rounds,))
    entries = []
    for r in rounds:
        if not isinstance(r, dict) or not isinstance(r.get("endpoints"), list):
            raise ToolError("net report round malformed: %r" % (r,))
        for e in r["endpoints"]:
            if not isinstance(e, dict) or not isinstance(e.get("url"), str) \
                    or not isinstance(e.get("ok"), bool):
                raise ToolError("net report endpoint entry malformed: %r" % (e,))
            entries.append(e)
    total = len(entries)
    if total == 0:
        raise ToolError("net report probed zero endpoints")
    ups = sum(1 for e in entries if e["ok"])
    rate = float(ups) / total
    return {"status": "ok", "weight": WEIGHTS["net"],
            "tool": "tools/net_probe.py", "verdict": verdict,
            "score": round(rate * 100.0, 2), "up": ups, "total": total,
            "rate": round(rate, 4),
            "down_endpoints": [e["url"] for e in entries if not e["ok"]]}


# ---- domain 3: registry ----

def resolve_registry(args):
    """Registry ledger three-way resolution: explicit --registry (a missing
    ledger fails loud 9; an explicitly given input is never silently skipped)
    > env CW_SET probe (a missing ledger skips honestly) > none skips.
    -> (path|None, source|None, skip_reason|None)."""
    if args.registry:
        if not os.path.isfile(args.registry):
            raise MissingInput("the explicit --registry ledger is missing: %s" % args.registry)
        return args.registry, "flag", None
    cw = os.environ.get(ENV_REGISTRY)
    if cw:
        cand = os.path.join(cw, *REGISTRY_REL)
        if os.path.isfile(cand):
            return cand, "CW_SET", None
        return None, None, ("under env %s=%s the ledger is missing (%s not on"
                            " disk)" % (ENV_REGISTRY, cw, "/".join(REGISTRY_REL)))
    return None, None, "--registry not given and env %s not set" % ENV_REGISTRY


def audit_registry(path):
    """Ledger anchor canonical-form audit (pure reads, zero subprocesses): on
    non-empty non-comment lines (the registry_union key_of semantics — blank
    before the first # means comment/blank, skipped) take the first ANCHOR_RE
    match (the anchor_of first-hit-per-line form) -> a fullmatch judgment of
    the canonical form #R<seq>-<md5_8>.  The non-form list caps at NON_FORM_CAP
    entries; the total is reported honestly."""
    try:
        with io.open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise MissingInput("registry ledger unreadable / decode failure: %s (%s)" % (path, e))
    lines = [ln.rstrip("\r\n").strip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    scanned = anchored = canonical = no_anchor = non_form_total = 0
    non_form = []
    for idx, ln in enumerate(lines, start=1):
        if not ln:
            continue
        if not ln.split("#", 1)[0].strip():
            continue          # comment line (blank before the first #; the key_of semantics; not a body row)
        scanned += 1
        m = ANCHOR_RE.search(ln)
        if m is None:
            no_anchor += 1
            continue
        anchored += 1
        if CANON_ANCHOR_RE.fullmatch(m.group(1)):
            canonical += 1
        else:
            non_form_total += 1
            if len(non_form) < NON_FORM_CAP:
                non_form.append({"line_no": idx, "anchor": m.group(0),
                                 "line": ln[:120]})
    rate = (float(canonical) / anchored) if anchored else 0.0
    return {"lines_scanned": scanned, "anchored": anchored,
            "canonical": canonical, "rate": rate, "no_anchor": no_anchor,
            "non_form_total": non_form_total, "non_form": non_form}


def domain_registry(reg_path, reg_source, skip_reason):
    """Domain 3 registry: the anchor canonical-form audit -> compliance rate
    x 100.  anchored==0 (zero anchors in the ledger) = rate 0, honestly
    non-canonical; a skipped domain drops its weight from the sum."""
    if reg_path is None:
        return {"status": "skip", "weight": WEIGHTS["registry"],
                "reason": skip_reason}
    st = audit_registry(reg_path)
    rate = st["rate"]
    out = {"status": "ok", "weight": WEIGHTS["registry"],
           "tool": "tools/registry_union.py", "source": reg_source,
           "registry": basename_of(reg_path),
           "verdict": "healthy"
                      if (st["anchored"] and st["canonical"] == st["anchored"])
                      else "non-canonical",
           "score": round(rate * 100.0, 2),
           "lines_scanned": st["lines_scanned"], "anchored": st["anchored"],
           "canonical": st["canonical"], "rate": round(rate, 4),
           "no_anchor": st["no_anchor"],
           "non_form_total": st["non_form_total"], "non_form": st["non_form"]}
    return out


# ---- domain 4: clog ----

def domain_clog(args, workdir, inj):
    """Domain 4 clog: active only with --src and --sample>0 (default 0 = no
    sampling -> skips honestly).  Whole-tree canonical-order enumeration ->
    equidistant sampling -> candidates TSV -> probe_engine --fresh (a real
    probe requires --world; --guard thermal wrapper) -> ledger -> chain_graph
    --top 1 always runs -> the red-account rate -> one TOP entry."""
    if not args.src:
        return {"status": "skip", "weight": WEIGHTS["clog"],
                "reason": "--src not given (the clog domain is skipped by default)"}
    if args.sample <= 0:
        return {"status": "skip", "weight": WEIGHTS["clog"],
                "reason": "--src given but --sample 0 (no sampling by"
                          " default; a real probe needs --sample N>0)"}
    ledger_path = os.path.join(workdir, "probe.json")
    graph_path = os.path.join(workdir, "chain.json")
    source = "injector" if inj is not None else "probe"
    out = ""
    if inj is not None:
        rc, out, rep = inj.take("probe")
        dump_json(rep, ledger_path)   # the canned ledger lands in the workdir verbatim; it still feeds the real chain_graph
    else:
        pairs = enumerate_tree(args.src)
        if not pairs:
            raise MissingInput("--src whole-tree enumeration found zero .v candidates: %s" % args.src)
        pairs = sample_pairs(pairs, args.sample)
        tsv = os.path.join(workdir, "cands.tsv")
        write_cands_tsv(tsv, pairs)
        print("clog candidate face: whole-tree enumeration sampled %d files"
              " (--sample %d) -> %s" % (len(pairs), args.sample, tsv))
        if not args.world:
            raise MissingInput("--world is required (the real clog probe; for offline use --injector)")
        if not os.path.isfile(args.guard):
            raise MissingInput("--guard missing: %s" % args.guard)
        cli = ["--candidates", tsv, "--src", args.src,
               "--world", args.world, "--out", ledger_path,
               "--logdir", os.path.join(workdir, "probe-logs"),
               "--timeout", str(args.timeout), "--fresh",
               "--guard", args.guard, "--guard-reg", args.guard_reg,
               "--guard-maxwait", str(args.guard_maxwait)]
        if args.rocq_cmd:
            cli += ["--rocq-cmd", args.rocq_cmd]
        rc, out = run_py(TOOL_PROBE, cli)
    if rc != 0:
        raise ToolError("probe_engine tool failure rc=%d: %s" % (rc, out[-300:]))
    ledger = load_json(ledger_path, "probe ledger")
    if not isinstance(ledger, dict) or ledger.get("schema") != SCHEMA_PROBE \
            or not isinstance(ledger.get("records"), dict):
        raise ToolError("probe ledger schema/shape unrecognized: %r (expected"
                        " %s plus a records dict)"
                        % (ledger.get("schema")
                           if isinstance(ledger, dict) else ledger,
                           SCHEMA_PROBE))
    # the chain-root graph always runs for real (pure stdlib; zero compiles, zero network; real orchestration, never a puppet); one TOP entry
    rc2, out2 = run_py(TOOL_CHAIN, [ledger_path, "--json", graph_path,
                                    "--top", "1"])
    if rc2 != 0:
        raise ToolError("chain_graph tool failure rc=%d: %s" % (rc2, out2[-300:]))
    graph = load_json(graph_path, "chain-root graph")
    if not isinstance(graph, dict) or graph.get("schema") != SCHEMA_CHAIN:
        raise ToolError("chain-root graph schema unrecognized: %r (expected"
                        " %s)"
                        % (graph.get("schema")
                           if isinstance(graph, dict) else graph,
                           SCHEMA_CHAIN))
    stats = graph.get("stats")
    if not isinstance(stats, dict) or not isinstance(stats.get("merged_total"),
                                                     int):
        raise ToolError("chain-root graph stats malformed: %r" % (stats,))
    merged = stats["merged_total"]
    red = sorted(set(stats.get("rc1") or []) | set(stats.get("other") or []))
    red_rate = (float(len(red)) / merged) if merged else 0.0
    top1 = None
    for lib in list(graph.get("top_order") or [])[:1]:
        e = (graph.get("libs") or {}).get(lib)
        if e:
            top1 = {"lib": lib, "n": e.get("n"),
                    "self": dict(e.get("self") or {})}
    return {"status": "ok", "weight": WEIGHTS["clog"],
            "tool": "tools/unclog.py", "source": source,
            "sample": args.sample, "probed": merged,
            "verdict": "healthy" if not red else "clogged",
            "score": round((1.0 - red_rate) * 100.0, 2),
            "red": len(red), "red_rate": round(red_rate, 4),
            "red_files": red, "chain_top1": top1}


# ---- aggregation: overall score + verdict + advice ----

def compute_score(domains):
    """Overall score = sum(domain score x weight) / sum(active weights)
    (skipped domains drop their weight; round 2 places).  env/net always run ->
    the denominator >= 60; everything skipped is an internal-invariant
    explosion (fail-loud)."""
    num = 0.0
    den = 0
    for d in DOMAIN_ORDER:
        dom = domains[d]
        if dom["status"] != "ok":
            continue
        num += dom["score"] * WEIGHTS[d]
        den += WEIGHTS[d]
    if den <= 0:
        raise UsageError("internal invariant explosion: all four domains skipped (env/net always run; this should not happen)")
    return round(num / den, 2), den


def advice_of(domains):
    """The advice list: one disposition suggestion per non-passing domain
    (fixed domain order; points at the corresponding tool; a skipped domain
    points at its switch).  All passing -> an empty list."""
    out = []
    env = domains["env"]
    if env["status"] == "ok" and env["verdict"] != "healthy":
        out.append({"domain": "env",
                    "tool": "tools/toolchain_dyld_doctor.py",
                    "text": "env domain verdict=%s (%d external hard"
                            " references missing) — run python3"
                            " tools/toolchain_dyld_doctor.py [--donor DIR] to"
                            " trace the missing libraries and restore them by"
                            " hand per the restore suggestions (advice only,"
                            " never auto-executed)"
                            % (env["verdict"], len(env["missing_refs"]))})
    net = domains["net"]
    if net["status"] == "ok" and net["verdict"] != "all-up":
        out.append({"domain": "net", "tool": "tools/net_probe.py",
                    "text": "net domain %s (%d/%d up) — before initiating a"
                            " run, take a two-probe stable window with python3"
                            " tools/net_probe.py --rounds 2 --stable-window"
                            % (net["verdict"], net["up"], net["total"])})
    reg = domains["registry"]
    if reg["status"] == "skip":
        out.append({"domain": "registry", "tool": "--registry",
                    "text": "registry domain skipped (%s) — pass --registry"
                            " PATH (e.g."
                            " $CW_SET/ConstructiveWorld_Live/order.txt) and"
                            " re-run the check" % reg["reason"]})
    elif reg["verdict"] != "healthy":
        out.append({"domain": "registry", "tool": "tools/registry_union.py",
                    "text": "registry domain anchor-form compliance rate"
                            " %.4f (%d non-form entries, cap %d listed) —"
                            " re-anchor to the #R<seq>-<md5_8> canonical form"
                            " with python3 tools/registry_union.py --reanchor"
                            " <name> --anchor-src <DIR>"
                            % (reg["rate"], reg["non_form_total"],
                               NON_FORM_CAP)})
    clog = domains["clog"]
    if clog["status"] == "skip":
        out.append({"domain": "clog", "tool": "--src",
                    "text": "clog domain skipped (%s) — pass --src DIR"
                            " --sample N for a real probe (under the cpu_guard"
                            " thermal wrapper) and re-run the check"
                            % clog["reason"]})
    elif clog["verdict"] != "healthy":
        top1 = clog.get("chain_top1")
        top_txt = ("TOP1=%s(n=%d)" % (top1["lib"], top1["n"])) if top1 \
            else "TOP1=none (no failing file has a missing-library chain root)"
        out.append({"domain": "clog", "tool": "tools/unclog.py",
                    "text": "clog domain red-account rate %.4f (%d failing"
                            " of %d; chain root %s) — clear the blockages with"
                            " the python3 tools/unclog.py --src <DIR>"
                            " --world <DIR> closed loop"
                            % (clog["red_rate"], clog["red"],
                               clog["probed"], top_txt)})
    return out


# ---- main flow ----

def args_summary(args, reg_source):
    """The args summary (always basenames — absolute paths never enter the report; the determinism discipline)."""
    return {"sample": args.sample,
            "src": basename_of(args.src),
            "world": basename_of(args.world) if args.world else None,
            "registry": basename_of(args.registry) if args.registry else None,
            "registry_source": reg_source,
            "worker": basename_of(args.worker) if args.worker else None,
            "donor": basename_of(args.donor) if args.donor else None,
            "guard": basename_of(args.guard),
            "injector": basename_of(args.injector) if args.injector else None,
            "endpoints_source": "flag" if args.endpoints else "default"}


def run(args):
    """Main flow: value validation (2) -> tool presence precheck (9) ->
    registry three-way resolution -> canned full-coverage precheck -> the four
    domains one by one -> overall score -> verdict -> advice -> report
    (0 = healthy / 1 = degraded)."""
    # 值校验（2）
    if args.sample < 0:
        raise UsageError("--sample must be >= 0 (0 = no sampling), got %d" % args.sample)
    if args.timeout < 1:
        raise UsageError("--timeout must be >= 1, got %d" % args.timeout)
    if args.guard_maxwait < 1:
        raise UsageError("--guard-maxwait must be >= 1, got %d" % args.guard_maxwait)
    # Clean mode: the four-domain real rollup drives canonical faces (the
    # sanctioned guard default, the registry ledger, the probe world);
    # report and refuse after the usage-face validation above (usage errors
    # keep their own exit codes). Offline canned runs stay available via
    # --injector and the frozen --selftest vectors.
    if _clean_mode() and not args.injector:
        print("requires canonical environment: the ConstructiveWorld live "
              "tree (sanctioned cpu_guard default, registry ledger, probe "
              "world); offline canned runs stay available via --injector")
        sys.exit(9)
    # tool presence precheck (9; orchestration adds no new engine — the four tools must be in place)
    for label, p in (("toolchain_dyld_doctor", TOOL_DYLD),
                     ("net_probe", TOOL_NET),
                     ("probe_engine", TOOL_PROBE),
                     ("chain_graph", TOOL_CHAIN)):
        if not os.path.isfile(p):
            raise MissingInput("tool missing: %s (%s)" % (label, p))
    if args.src is not None and not os.path.isdir(args.src):
        raise MissingInput("--src directory missing: %s" % args.src)
    if args.world is not None and not os.path.isdir(args.world):
        raise MissingInput("--world directory missing: %s" % args.world)
    reg_path, reg_source, reg_skip = resolve_registry(args)
    clog_active = bool(args.src) and args.sample > 0
    inj = Injector(args.injector) if args.injector else None
    if inj is not None:
        inj.require(["dyld", "net"] + (["probe"] if clog_active else []))
        print("injector: %s (canned %s; the subprocess call layer is canned, no real subprocess)"
              % (args.injector, ",".join(sorted(inj.scen))))
    # workdir
    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)
        workdir = args.workdir
    else:
        workdir = tempfile.mkdtemp(prefix="rocqwash_cwdoctor_")
    print("workdir -> %s" % workdir)

    domains = {
        "env": domain_env(args, workdir, inj),
        "net": domain_net(args, workdir, inj),
        "registry": domain_registry(reg_path, reg_source, reg_skip),
        "clog": domain_clog(args, workdir, inj),
    }
    score, active_w = compute_score(domains)
    verdict = "healthy" if score >= HEALTHY_MIN else "degraded"
    advice = advice_of(domains)
    report = {"schema": SCHEMA, "verdict": verdict, "score": score,
              "healthy_min": HEALTHY_MIN, "weights": dict(WEIGHTS),
              "active_weight": active_w, "domains": domains,
              "advice": advice, "args": args_summary(args, reg_source)}

    # loud stdout (deterministic domain order)
    print("=== CW-DOCTOR (aggregate health check, four-domain rollup) ===")
    for d in DOMAIN_ORDER:
        dom = domains[d]
        if dom["status"] == "skip":
            print("[%-8s] skip  weight=%d (%s)" % (d, dom["weight"],
                                                   dom["reason"]))
            continue
        print("[%-8s] ok    weight=%d verdict=%s score=%s"
              % (d, dom["weight"], dom["verdict"], dom["score"]))
        if d == "env":
            print("    worker=%s external=%d missing=%d"
                  % (dom["worker"], dom["external_refs"],
                     len(dom["missing_refs"])))
        elif d == "net":
            print("    up=%d/%d rate=%.4f down=%d"
                  % (dom["up"], dom["total"], dom["rate"],
                     len(dom["down_endpoints"])))
        elif d == "registry":
            print("    source=%s registry=%s anchored=%d/%d rate=%.4f "
                  "no_anchor=%d non_form=%d"
                  % (dom["source"], dom["registry"], dom["canonical"],
                     dom["anchored"], dom["rate"], dom["no_anchor"],
                     dom["non_form_total"]))
        elif d == "clog":
            top1 = dom["chain_top1"]
            print("    source=%s probed=%d red=%d rate=%.4f top1=%s"
                  % (dom["source"], dom["probed"], dom["red"],
                     dom["red_rate"],
                     ("%s(n=%d)" % (top1["lib"], top1["n"])) if top1
                     else "none"))
    print("--- scoring ---")
    print("active weight %d/%d · SCORE=%s · verdict: %s"
          % (active_w, sum(WEIGHTS.values()), score, verdict))
    if advice:
        print("--- advice (one entry per non-passing domain) ---")
        for a in advice:
            print("  [%s] %s\n    -> %s" % (a["domain"], a["tool"],
                                            a["text"]))
    else:
        print("--- advice: all passing, no dispositions ---")
    if args.json:
        dump_json(report, args.json)
        print("json -> %s" % args.json)
    print("VERDICT: %s (exit %d)" % (verdict, 0 if verdict == "healthy" else 1))
    return 0 if verdict == "healthy" else 1


# ---- --selftest (frozen vectors; tmp fixture tree; everything canned at the subprocess layer) ----

def selftest():
    """Vectors (tmp fixtures + injector subprocess-layer canning; zero real
    otool, zero real network, zero real compiles; chain_graph and the registry
    audit run for real — pure stdlib):
    V1  four domains all green, score 100 (exit 0; empty advice; active
        weight 100)
    V2  env failing lowers the score (missing-libs -> env 0 -> 60.0;
        degraded; advice points at dyld)
    V3  registry ledger-missing skip renormalizes (CW_SET stripped + net
        partial -> 86.67; active weight 75; advice carries the net and
        registry entries) plus the CW_SET missing-ledger honest skip
    V4  clog TOP injection (canned red account 3/4 -> clog 25.0 -> 88.75;
        chain TOP1=A(n=2); advice points at unclog)
    V5  advice generation (asserted entry by entry for V2/V3/V4; the
        all-green empty list already covered in V1)
    V6  JSON idempotence (same scenario, two runs, different workdirs,
        byte-identical)
    V7  CLI four codes (--help 0; --bogus 2; negative --sample 2; missing
        --registry ledger 9; missing --src directory 9; missing --injector
        scenario 9; unknown scenario key 2; canned not covering 9)
    V8  registry-audit unit (mixed forms rate 2/6; comment/blank/anchorless
        line counts; cap 25 -> 20; 7/8/9-digit fingerprints and uppercase hex
        are all non-form; a zero-anchor ledger; the CW_SET positive probe with
        source=CW_SET)
    """
    tmp = tempfile.mkdtemp(prefix="rocqwash_cwdoctor_self_")
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, PROG + ".py")

    def run(aargs, env_extra=None, strip_cw=True):
        e = dict(os.environ)
        if strip_cw:
            e.pop("CW_SET", None)
        if env_extra:
            e.update(env_extra)
        p = subprocess.run([sys.executable, "-B", script] + list(aargs),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=e)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wtext(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def wjson(path, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        dump_json(obj, path)

    def scenario(name, dyld_rep, net_rep, probe_rep=None):
        d = os.path.join(tmp, "inj_" + name)
        scen = {"dyld": {"rc": 0 if dyld_rep["verdict"] == "healthy" else 1,
                         "stdout": "", "report": dyld_rep},
                "net": {"rc": 0, "stdout": "", "report": net_rep}}
        if probe_rep is not None:
            scen["probe"] = {"rc": 0, "stdout": "", "report": probe_rep}
        wjson(os.path.join(d, "scenario.json"), scen)
        return d

    def rec0(f):
        return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
                "red_class": None, "verdict": "RC0", "red_count": None,
                "md5_match": None}

    def rec1(f, lib):
        return {"file": f, "md5": None, "rc": 1,
                "red": "Error: Unable to locate library | %s (while searching"
                       " for a .vos file)." % lib,
                "missing": lib, "red_class": "MISSING_LIB",
                "verdict": "RED-MISSING_LIB", "red_count": None,
                "md5_match": None}

    # canned reports (frozen vectors; all paths fake; zero machine dependency)
    DYLD_OK = {"schema": SCHEMA_DYLD, "worker": "/fake/rocqworker",
               "external_refs": [
                   {"path": "/fake/Live/toolchain/gmp/lib/libgmp.10.dylib",
                    "exists": True},
                   {"path": "/fake/Live/toolchain/zmq/lib/libzmq.5.dylib",
                    "exists": True}],
               "verdict": "healthy"}
    DYLD_MISS = {"schema": SCHEMA_DYLD, "worker": "/fake/rocqworker",
                 "external_refs": [
                     {"path": "/fake/Live/toolchain/gmp/lib/libgmp.10.dylib",
                      "exists": False}],
                 "verdict": "missing-libs"}

    def net_rep(pairs):
        eps = [{"url": u, "http_code": (200 if ok else None), "ok": ok}
               for u, ok in pairs]
        ups = sum(1 for e in eps if e["ok"])
        verdict = "all-up" if ups == len(eps) else \
            ("all-down" if ups == 0 else "partial")
        return {"schema": SCHEMA_NET,
                "rounds": [{"at": "2026-11-11T00:00:00Z", "endpoints": eps}],
                "verdict": verdict}

    NET_UP = net_rep([("https://a.example", True), ("https://b.example", True),
                      ("https://c.example", True), ("https://d.example",
                                                    True)])
    NET_PART = net_rep([("https://a.example", True), ("https://b.example",
                                                      True),
                        ("https://c.example", False),
                        ("https://d.example", False)])

    def probe_rep(records):
        return {"schema": SCHEMA_PROBE, "n_records": len(records),
                "records": records}

    PROBE_GREEN = probe_rep({"A": rec0("A"), "B": rec0("B")})
    # red-account vector: A is a washable chain root; B/C miss A; D misses B -> TOP1=A(n=2); 3/4 failing
    PROBE_RED = probe_rep({"A": rec0("A"), "B": rec1("B", "A"),
                           "C": rec1("C", "A"), "D": rec1("D", "B")})

    SCEN_OK = scenario("ok", DYLD_OK, NET_UP, PROBE_GREEN)
    SCEN_ENVRED = scenario("envred", DYLD_MISS, NET_UP, PROBE_GREEN)
    SCEN_NETPART = scenario("netpart", DYLD_OK, NET_PART, PROBE_GREEN)
    SCEN_CLOGRED = scenario("clogred", DYLD_OK, NET_UP, PROBE_RED)

    def make_registry(path, lines):
        wtext(path, "\n".join(lines) + "\n")
        return path

    REG_GREEN = make_registry(
        os.path.join(tmp, "reg_green.txt"),
        ["# canonical-ledger fixture (all #R<seq>-<md5_8> form)",
         "S01_BaseRing.v#R0-d66910ab",
         "S02_Cauchy.v#R1-0123abcd",
         "S03_QExp.v#R2-deadbeef",
         ""])
    REG_MIX = make_registry(
        os.path.join(tmp, "reg_mix.txt"),
        ["A.v#R0-d66910ab",            # canonical
         "B.v#R1-0123abcd",            # canonical
         "C.v#R2",                     # non-form, bare seq
         "D.v#R3-abcdef",              # non-form, 5 digits
         "E.v#R4-D66910AB",            # non-form, uppercase 8 (md5_8 is always lowercase)
         "F.v#R5-d66910abc",           # non-form, 9 digits
         "G.v",                        # anchorless body row -> no_anchor
         "# comment #R9-d66910ab",      # comment line -> not audited
         ""])                          # blank line -> not audited
    src_empty = os.path.join(tmp, "src_empty")
    os.makedirs(src_empty)

    try:
        # ---- V1 four domains all green, score 100 ----
        j1 = os.path.join(tmp, "v1.json")
        wd1 = os.path.join(tmp, "wd_v1a")
        p = run(["--json", j1, "--workdir", wd1, "--registry", REG_GREEN,
                 "--src", src_empty, "--sample", "2", "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j1, encoding="utf-8").read())
        assert rep["schema"] == SCHEMA and rep["verdict"] == "healthy", rep
        assert rep["score"] == 100.0 and rep["active_weight"] == 100, rep
        doms = rep["domains"]
        for d in DOMAIN_ORDER:
            assert doms[d]["status"] == "ok", (d, doms[d])
        assert doms["env"]["verdict"] == "healthy" and \
            doms["env"]["score"] == 100.0, doms["env"]
        assert doms["net"]["verdict"] == "all-up" and \
            doms["net"]["up"] == 4, doms["net"]
        assert doms["registry"]["verdict"] == "healthy" and \
            doms["registry"]["rate"] == 1.0, doms["registry"]
        assert doms["clog"]["verdict"] == "healthy" and \
            doms["clog"]["red"] == 0 and \
            doms["clog"]["chain_top1"] is None, doms["clog"]
        assert rep["advice"] == [], rep["advice"]
        assert "SCORE=100.0" in p.stdout, p.stdout[-400:]
        # the fixed four domain keys (deterministic shape)
        assert sorted(doms) == ["clog", "env", "net", "registry"], sorted(doms)

        # ---- V2 env failing lowers the score (0x40 -> 60.0; degraded; advice points at dyld) ----
        j2 = os.path.join(tmp, "v2.json")
        p = run(["--json", j2, "--registry", REG_GREEN, "--src", src_empty,
                 "--sample", "2", "--injector", SCEN_ENVRED])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j2, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 60.0, rep
        env = rep["domains"]["env"]
        assert env["verdict"] == "missing-libs" and env["score"] == 0.0, env
        assert env["missing_refs"] == \
            ["/fake/Live/toolchain/gmp/lib/libgmp.10.dylib"], env
        assert rep["advice"][0]["domain"] == "env" and \
            rep["advice"][0]["tool"] == "tools/toolchain_dyld_doctor.py", \
            rep["advice"]
        assert "toolchain_dyld_doctor" in p.stdout, p.stdout[-400:]

        # ---- V3 registry ledger-missing skip renormalizes (CW_SET stripped; net partial -> 86.67) ----
        j3 = os.path.join(tmp, "v3.json")
        p = run(["--json", j3, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_NETPART])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j3, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 86.67, rep
        assert rep["active_weight"] == 75, rep["active_weight"]
        reg = rep["domains"]["registry"]
        assert reg["status"] == "skip" and "reason" in reg, reg
        assert rep["domains"]["net"]["verdict"] == "partial" and \
            rep["domains"]["net"]["score"] == 50.0, rep["domains"]["net"]
        assert [a["domain"] for a in rep["advice"]] == ["net", "registry"], \
            rep["advice"]
        # CW_SET set but the ledger missing -> skips honestly (the reason carries "missing")
        cw_empty = os.path.join(tmp, "cwset_empty")
        os.makedirs(cw_empty)
        j3b = os.path.join(tmp, "v3b.json")
        p = run(["--json", j3b, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK], env_extra={"CW_SET": cw_empty})
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j3b, encoding="utf-8").read())
        reg = rep["domains"]["registry"]
        assert reg["status"] == "skip" and "missing" in reg["reason"], reg

        # ---- V4 clog TOP injection (3/4 failing -> clog 25.0 -> 88.75; TOP1=A) ----
        j4 = os.path.join(tmp, "v4.json")
        p = run(["--json", j4, "--registry", REG_GREEN, "--src", src_empty,
                 "--sample", "2", "--injector", SCEN_CLOGRED])
        assert p.returncode == 1, p.stdout[-800:]
        rep = json.loads(io.open(j4, encoding="utf-8").read())
        assert rep["verdict"] == "degraded" and rep["score"] == 88.75, rep
        clog = rep["domains"]["clog"]
        assert clog["verdict"] == "clogged" and clog["score"] == 25.0, clog
        assert clog["red"] == 3 and clog["probed"] == 4 and \
            clog["red_rate"] == 0.75, clog
        assert clog["red_files"] == ["B", "C", "D"], clog
        top1 = clog["chain_top1"]
        assert top1["lib"] == "A" and top1["n"] == 2 and \
            top1["self"]["washable"] is True, top1
        adv = [a for a in rep["advice"] if a["domain"] == "clog"]
        assert len(adv) == 1 and adv[0]["tool"] == "tools/unclog.py" and \
            "TOP1=A(n=2)" in adv[0]["text"], rep["advice"]

        # ---- V6 JSON idempotence: same scenario, two runs, different workdirs, byte-identical ----
        j6a = os.path.join(tmp, "v6a.json")
        j6b = os.path.join(tmp, "v6b.json")
        p = run(["--json", j6a, "--workdir", os.path.join(tmp, "wd6a"),
                 "--registry", REG_GREEN, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        p = run(["--json", j6b, "--workdir", os.path.join(tmp, "wd6b"),
                 "--registry", REG_GREEN, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        ba = io.open(j6a, "rb").read()
        bb = io.open(j6b, "rb").read()
        assert ba == bb, "json byte drift = violation"
        rep = json.loads(ba.decode("utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]

        # ---- V7 CLI four codes ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should rc=2, got %d" % p.returncode
        p = run(["--sample", "-1"])
        assert p.returncode == 2, "negative --sample should rc=2, got %d" % p.returncode
        p = run(["--registry", os.path.join(tmp, "nope.txt")])
        assert p.returncode == 9, "explicit missing ledger should rc=9, got %d" % p.returncode
        p = run(["--src", os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "missing --src directory should rc=9, got %d" % p.returncode
        p = run(["--injector", os.path.join(tmp, "no_inj")])
        assert p.returncode == 9, "missing injector scenario should rc=9, got %d" \
            % p.returncode
        bad_scen = os.path.join(tmp, "inj_bad")
        wjson(os.path.join(bad_scen, "scenario.json"), {"bogus_key": {}})
        p = run(["--injector", bad_scen])
        assert p.returncode == 2, "unknown scenario key should rc=2, got %d" % p.returncode
        half_scen = os.path.join(tmp, "inj_half")
        wjson(os.path.join(half_scen, "scenario.json"),
              {"dyld": {"rc": 0, "report": DYLD_OK}})
        p = run(["--injector", half_scen])
        assert p.returncode == 9, "canned not covering should rc=9, got %d" \
            % p.returncode
        # --src given but --sample 0 (no sampling by default) -> the clog domain skips honestly, no real probe
        j7 = os.path.join(tmp, "v7.json")
        p = run(["--json", j7, "--src", src_empty, "--injector", SCEN_OK])
        assert p.returncode == 0, p.stdout[-400:]
        rep = json.loads(io.open(j7, encoding="utf-8").read())
        assert rep["domains"]["clog"]["status"] == "skip" and \
            "--sample 0" in rep["domains"]["clog"]["reason"], \
            rep["domains"]["clog"]

        # ---- V8 registry-audit unit ----
        st = audit_registry(REG_MIX)
        assert st["lines_scanned"] == 7 and st["anchored"] == 6 and \
            st["canonical"] == 2, st
        assert abs(st["rate"] - 2.0 / 6) < 1e-12, st
        assert st["no_anchor"] == 1 and st["non_form_total"] == 4, st
        assert [e["anchor"] for e in st["non_form"]] == \
            ["#R2", "#R3-abcdef", "#R4-D66910AB", "#R5-d66910abc"], st
        # cap 20: 25 non-form rows -> the list holds 20, the total reports 25
        cap_lines = ["X%d.v#R%d" % (i, i) for i in range(25)]
        cap_path = make_registry(os.path.join(tmp, "reg_cap.txt"), cap_lines)
        st = audit_registry(cap_path)
        assert st["non_form_total"] == 25 and len(st["non_form"]) == 20, \
            (st["non_form_total"], len(st["non_form"]))
        # zero-anchor ledger -> rate 0, non-canonical
        z_path = make_registry(os.path.join(tmp, "reg_noanchor.txt"),
                               ["A.v", "B.v"])
        st = audit_registry(z_path)
        assert st["anchored"] == 0 and st["rate"] == 0.0, st
        dom = domain_registry(z_path, "flag", None)
        assert dom["verdict"] == "non-canonical" and dom["score"] == 0.0, dom
        # CW_SET positive probe: the ledger at CW_SET/ConstructiveWorld_Live/order.txt
        cw_ok = os.path.join(tmp, "cwset_ok")
        make_registry(os.path.join(cw_ok, "ConstructiveWorld_Live",
                                   "order.txt"),
                      ["S01.v#R0-d66910ab", "S02.v#R1-0123abcd"])
        j8 = os.path.join(tmp, "v8.json")
        p = run(["--json", j8, "--src", src_empty, "--sample", "2",
                 "--injector", SCEN_OK], env_extra={"CW_SET": cw_ok})
        assert p.returncode == 0, p.stdout[-800:]
        rep = json.loads(io.open(j8, encoding="utf-8").read())
        reg = rep["domains"]["registry"]
        assert reg["status"] == "ok" and reg["source"] == "CW_SET" and \
            reg["verdict"] == "healthy" and reg["anchored"] == 2, reg
        assert rep["args"]["registry_source"] == "CW_SET", rep["args"]

        print("CW-DOCTOR-SELFTEST PASS: four domains all green 100 / env-red"
              " down to 60 / registry skip renormalized 86.67 + the CW_SET"
              " missing ledger / clog TOP injection 88.75 / advice generation /"
              " JSON idempotence byte-identical / CLI four codes + canned full"
              " coverage / the registry-audit unit (mixed forms 2of6, cap 20,"
              " zero anchors, the CW_SET positive probe) — all eight vectors"
              " pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="aggregate health doctor, four-domain rollup:"
                    " env/net/registry/clog each driven by subprocess over the"
                    " existing per-domain tool -> an overall health score 0-100"
                    " plus per-domain verdicts plus advice (schema"
                    " rocqwash-cwdoctor/1)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="health report output path (rocqwash-cwdoctor/1;"
                         " sort_keys determinism)")
    ap.add_argument("--workdir", default=None, metavar="DIR",
                    help="artifacts directory (the dyld/net reports, the"
                         " probe ledger, the chain-root graph; default"
                         " mkdtemp; the path is printed to stdout)")
    ap.add_argument("--registry", default=None, metavar="PATH",
                    help="explicit registry ledger (order.txt form; by default"
                         " probes env %s/ConstructiveWorld_Live/order.txt;"
                         " neither present -> the registry domain skips)"
                         % ENV_REGISTRY)
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="the clog-domain source tree (the clog domain is"
                         " skipped without it)")
    ap.add_argument("--sample", type=int, default=0, metavar="N",
                    help="clog sampling cap (default 0 = no sampling -> the"
                         " clog domain skips; N>0 samples equidistantly; N >="
                         " tree size = a full census)")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="the clog real-probe world directory (required for a"
                         " real probe; for offline use --injector)")
    ap.add_argument("--worker", default=None, metavar="PATH",
                    help="passed through to toolchain_dyld_doctor --worker (by"
                         " default the tool probes flag/env/the sanctioned"
                         " machine default itself)")
    ap.add_argument("--donor", default=None, metavar="DIR",
                    help="passed through to toolchain_dyld_doctor --donor"
                         " (tracing missing entries)")
    ap.add_argument("--endpoints", default=None, metavar="URL[,URL...]",
                    help="passed through to net_probe --endpoints (the default"
                         " four endpoints)")
    ap.add_argument("--guard", default=DEFAULT_GUARD, metavar="PATH",
                    help="cpu_guard.sh passed through to probe_engine (the"
                         " clog real-probe thermal wrapper; defaults to the"
                         " sanctioned-machine path)")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_cw_doctor", metavar="DIR")
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int,
                    default=600, metavar="S")
    ap.add_argument("--timeout", type=int, default=1500, metavar="S",
                    help="per-file timeout seconds passed through to"
                         " probe_engine")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd", default=None, metavar="TPL",
                    help="the probe command template passed through to"
                         " probe_engine (by default its own built-in default)")
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="offline canning scenario (DIR/scenario.json; keys"
                         " dyld/net/probe; the subprocess call layer canned"
                         " with {rc,stdout,report}; the canned table must"
                         " cover every tool call about to be issued)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        code = run(args)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except (MissingInput, ToolError) as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
