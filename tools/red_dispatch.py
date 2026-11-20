#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""red_dispatch.py: red-event router: sentinel red events to action presets.

    Purpose.  Read sentinel events (cw_sentinel stream, rocqwash-sentinel-event/1 JSONL,
      make_event shape at cw_sentinel.py:435-443), look kind/family up in the route table,
      and emit action presets. Report-only with zero execution is the default in every
      preset tier (a failing result is data, not a tool failure; dry-run default per
      cw_sentinel.py:47); the auto tier runs the suggested command only when explicitly
      requested (60s cap per event; a non-zero rc is recorded loudly, exit unchanged).
    Interface.  `--event-file PATH` | stdin JSONL (one event per line; if every line
      fails, one whole-text JSON object is the fallback); `--preset
      report-only|suggest|auto`; `--json OUT` (rocqwash-red-route/1, sort_keys);
      `--state-file PATH` (rocqwash-red-route-state/1; re-route guard,
      `--cooldown S` default 600); `--repo-path DIR`; `--param K=V` / `--on-args K=V`
      (aliases; PARAM_KEYS); `--dry-run` (auto tier only); `--selftest`. Required fields
      per kind in REQUIRED_FIELDS; a missing field exits 9, listed per event and field
      (validate-all-then-execute); routes bind existing cw.sh entries only; zero new
      engines.
    Dependencies.  Python 3 stdlib only. Input: JSONL from file or stdin. Output: the
      caller-designated `--json` / `--state-file` paths plus auto-tier command side
      effects; the selftest writes only mkdtemp directories. Auto execution is local;
      compilation thermal control stays inside the routed cw.sh tools.
    Evidence.  `--selftest`: 12 offline vectors on mkdtemp fixtures with a fake cw.sh
      marker file (route families, placeholders, auto execution, state dedup, cooldown,
      report-only zero execution, stdin multi-event, fail-loud faces, rc recording, fix
      list, determinism, single-object fallback); suite member tests/test_red_dispatch.py.
    Exit-codes.  0 = processed (rc, timeout, and skip facts recorded; exit unchanged);
      2 = usage error (--param guard, --dry-run tier mismatch, negative --cooldown,
      selftest assertion); 9 = missing input (absent file, missing fields, unsolvable
      parameters, metacharacter refusal, state corruption); 1 = reserved (data-facing).
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "red_dispatch"
SCHEMA = "rocqwash-red-dispatch/1"
STATE_SCHEMA = "rocqwash-red-dispatch-state/1"

EVENT_KINDS = ("ci-red", "blocking", "build-signal")
REQUIRED_FIELDS = {
    "ci-red": ("repo", "run", "family", "action"),
    "blocking": ("top_root",),
    "build-signal": ("hits",),
}
FAMILY_ALIASES = {"A": "A-content-red", "B": "B-netred", "C": "C-toolchain-break",
                  "D": "D-queue-wall", "E": "E-coqchk-skipped"}
PUSHCI_FAMILIES = ("B-netred", "E-coqchk-skipped")

WORLD_REL = "ConstructiveWorld_Live"   # relative-name anchor (REGISTRY_REL at cw_doctor.py:102)
DEFAULT_MAX_HEAL = "3"                 # same value as the --max-heal default 3 at pushci.py:2018
DEFAULT_COOLDOWN = 600
EXEC_TIMEOUT = 60                      # same cap as ON_RED_TIMEOUT at cw_sentinel.py:229
OUTPUT_CLIP = 400                      # same cap as clip(out, 400) at cw_sentinel.py:843
FIX_CLIP = 200
STATE_CMD_CLIP = 200

# route-parameter key union; unknown / duplicate / malformed keys exit 2
PARAM_KEYS = ("repo_path", "branch", "max_heal", "src", "world", "file", "apply")
# --param apply values that turn --apply on; anything else exits 2
APPLY_TRUTHY = ("1", "true", "yes", "on")

V_FILE_RE = re.compile(r"[A-Za-z0-9_./][A-Za-z0-9_./-]*\.v\b")  # word boundary; .vo is not swallowed
# shell metacharacters; a value containing any of these is refused at command
# construction. The set covers both executor shells the tool can land on:
# the POSIX sh specials (first half) and the cmd.exe-active specials `%`
# (variable expansion) and `^` (escape): subprocess shell=True runs cmd.exe
# on Windows, so a value carrying % or ^ would execute differently per
# platform (same input, different command), which the determinism contract
# forbids (T0-5 platform-defect family).
_SHELL_UNSAFE = set('; & | < > ( ) $ ` " \' \t \r \n \\ % ^')


class DispatchError(Exception):
    """fail-loud carrier: msg is the loud text; code is 2 (usage/assertion) or 9 (missing input)."""

    def __init__(self, msg, code):
        super().__init__(msg)
        self.msg = msg
        self.code = code


def clip(s, cap=OUTPUT_CLIP):
    """fixed-cap clipping (same shape as clip at cw_sentinel.py:254)."""
    s = str(s)
    return s if len(s) <= cap else s[:cap] + "...[clip]"


def shell_unsafe(v):
    """metacharacter guard on the command-construction face (injection defense; a value
    containing a metacharacter is refused)."""
    return any(c in _SHELL_UNSAFE for c in str(v))


def cmd_path(v):
    """command-construction path canonicalization (T0-5 platform-defect fix at
    the _SHELL_UNSAFE gate): on Windows the native separator (os.sep,
    backslash) is refused by shell_unsafe (it is an escape character under
    sh), so path-shaped parameter values are rewritten to forward slashes,
    which both executor shells (sh, cmd.exe) and every routed tool accept.
    No-op where os.sep is already "/"; a literal backslash inside a value on
    POSIX stays refused (fail-loud preserved, no silent rewrite). Apply this
    to path-shaped parameter values before shell_unsafe, never to branch
    names or free-text values."""
    v = str(v)
    if os.sep != "/":
        v = v.replace(os.sep, "/")
    return v


# ---- input parsing --------------------------------------------------------------

def parse_events(text, source):
    """input text → list of event dicts (JSONL one event per line; blank lines skipped;
    mixed malformed shapes exit 9 with a full listing; if every line fails, fall back
    to one whole-text JSON object). Determinism: line order is event order."""
    lines = [(i, l) for i, l in enumerate(text.splitlines(), 1) if l.strip()]
    if not lines:
        raise DispatchError("missing input: %s has zero valid lines (empty JSONL input)"
                            % source, 9)
    parsed, problems = [], []
    for lineno, line in lines:
        try:
            ev = json.loads(line)
        except ValueError as e:
            problems.append("line %d: JSON parse failed: %s" % (lineno, e))
            continue
        if not isinstance(ev, dict):
            problems.append("line %d: event is not a dict (found %s)"
                            % (lineno, type(ev).__name__))
            continue
        parsed.append(ev)
    if problems and parsed:
        raise DispatchError("malformed input: %s (%d bad lines; mixed shapes rejected; "
                            "JSONL is one event per line):\n  %s"
                            % (source, len(problems), "\n  ".join(problems)), 9)
    if parsed:
        return parsed
    try:
        ev = json.loads(text)
    except ValueError as e:
        raise DispatchError("malformed input: %s (%d per-line failures plus a whole-text "
                            "JSON failure %s; both shapes failed)"
                            % (source, len(problems), e), 9)
    if not isinstance(ev, dict):
        raise DispatchError("malformed input: %s (whole-text JSON is not a dict; found %s)"
                            % (source, type(ev).__name__), 9)
    return [ev]


def collect_field_problems(ev, where):
    """judge the required-field table key by key (missing fields listed fail-loud)
    → (problems, kind|None)."""
    problems = []
    kind = ev.get("kind")
    if kind is None:
        return ["%s: kind missing (required; one of %s)" % (where, ",".join(EVENT_KINDS))], None
    if kind not in EVENT_KINDS:
        return ["%s: kind unrecognized (found %r; must be one of %s)"
                % (where, kind, ",".join(EVENT_KINDS))], None
    for f in REQUIRED_FIELDS[kind]:
        v = ev.get(f)
        if v is None or (isinstance(v, str) and not v.strip()) \
                or (isinstance(v, (list, dict)) and not v):
            problems.append("%s: %s missing (required for %s)" % (where, f, kind))
    if kind == "ci-red" and ev.get("family") is not None \
            and not isinstance(ev.get("family"), str):
        problems.append("%s: family must be str (found %s)"
                        % (where, type(ev["family"]).__name__))
    if kind == "build-signal" and ev.get("hits") is not None \
            and not isinstance(ev.get("hits"), list):
        problems.append("%s: hits must be list (found %s)"
                        % (where, type(ev["hits"]).__name__))
    return problems, kind


def state_key(ev):
    """re-route guard key = kind+repo+run+family (missing slots become empty strings;
    blocking/build-signal lack these four fields, so the key degrades to kind granularity;
    the limitation is noted loudly in the module docstring)."""
    parts = []
    for k in ("kind", "repo", "run", "family"):
        v = ev.get(k)
        parts.append("" if v is None else str(v))
    return "|".join(parts)


# ---- parameter resolution -------------------------------------------------------

def resolve_param(key, ev, params, event_field=None):
    """the first two of the three resolution tiers: explicit --param > event field
    → (value|None, source|None)."""
    if key in params:
        return str(params[key]), "param"
    v = ev.get(event_field or key)
    if v is None:
        return None, None
    sv = str(v)
    if not sv.strip():
        return None, None
    return sv, "event"


def derive_world(repo_path):
    """the third resolution tier: --repo-path anchor plus the ConstructiveWorld_Live
    relative name (same relative anchor as REGISTRY_REL at cw_doctor.py:102).
    → (value|None, source|None)"""
    if not repo_path:
        return None, None
    return os.path.join(repo_path, WORLD_REL), "derive"


def build_route(ev, kind, params, repo_path):
    """route-table lookup → (route dict, problems).
    route dict: {id, cmd?, params?, fix_list?, notes[]}; non-empty problems mean the
    command face of this event is unsolvable (the caller lists everything and exits 9;
    validate-all-then-execute)."""
    notes = []
    problems = []
    route = {"id": None, "notes": notes}

    def _guard(k, v):
        if v is None:
            return False
        if shell_unsafe(v):
            problems.append("route parameter %s contains shell metacharacters; "
                            "construction refused (fail-loud injection guard): %r"
                            % (k, clip(v, 80)))
            return False
        return True

    if kind == "ci-red":
        fam = ev.get("family")
        if fam in FAMILY_ALIASES:
            notes.append("family alias %s→%s (classification-spectrum abbreviation "
                         "tolerance)" % (fam, FAMILY_ALIASES[fam]))
            fam = FAMILY_ALIASES[fam]
        if fam in PUSHCI_FAMILIES:
            route["id"] = "pushci"
            rp, s1 = resolve_param("repo_path", ev, params, event_field="repo")
            if rp is not None:
                rp = cmd_path(rp)   # path-shaped param: canonical separator face
            br, s2 = resolve_param("branch", ev, params, event_field="branch")
            mh, s3 = resolve_param("max_heal", ev, params)
            if mh is None:
                mh, s3 = DEFAULT_MAX_HEAL, "default"
            for k, v in (("repo_path", rp), ("branch", br), ("max_heal", mh)):
                if v is None:
                    problems.append("pushci route parameter unsolvable: %s "
                                    "(absent from both --param and the event)" % k)
                else:
                    _guard(k, v)
            if not problems:
                route["cmd"] = ("bash cw.sh pushci --repo-path %s --branch %s "
                                "--max-heal %s" % (rp, br, mh))
                route["params"] = {"repo_path": {"value": rp, "source": s1},
                                   "branch": {"value": br, "source": s2},
                                   "max_heal": {"value": mh, "source": s3}}
        elif fam == "A-content-red":
            route["id"] = "manual-fix-note"
            notes.append("family-A content failure is a content-face fix; no automated "
                         "edits (hard requirement; the auto hook never edits content; "
                         "zero commands, zero execution)")
            evidence = ev.get("evidence")
            if isinstance(evidence, list) and evidence:
                route["fix_list"] = [clip(str(x), FIX_CLIP) for x in evidence]
            else:
                notes.append("evidence absent (event carries none); fix list degrades "
                             "to pointer form")
                route["fix_list"] = ["repo=%s run=%s branch=%s (fetch the run log "
                                     "manually to name the target file; no automated "
                                     "edits)" % (ev.get("repo"), ev.get("run"),
                                                 ev.get("branch"))]
        elif fam == "C-toolchain-break":
            route["id"] = "doctor"
            route["cmd"] = "bash cw.sh doctor"
            notes.append("doctor = the toolchain_dyld_doctor route (cw.sh:28; all "
                         "parameters optional so the bare form; diagnosis only, no "
                         "automated fixes)")
        else:
            route["id"] = "watch-only"
            notes.append("family=%r is outside the route table; watch-only, zero "
                         "commands, manual review (D/UNRECOGNIZED/none and "
                         "out-of-spectrum; same as the ACTION_OF out-of-spectrum "
                         "handling at ci_triage.py:143)" % (fam,))
    elif kind == "blocking":
        route["id"] = "unclog"
        src, s1 = resolve_param("src", ev, params)
        if src is None:
            src, s1 = derive_world(repo_path)
        world, s2 = resolve_param("world", ev, params)
        if world is None:
            world, s2 = derive_world(repo_path)
        if src is not None:
            src = cmd_path(src)     # path-shaped param: canonical separator face
        if world is not None:
            world = cmd_path(world)
        for k, v in (("src", src), ("world", world)):
            if v is None:
                problems.append("unclog route parameter unsolvable: %s (absent from "
                                "both --param and the event; cannot derive %s without "
                                "--repo-path)" % (k, WORLD_REL))
            else:
                _guard(k, v)
        apply_on = "apply" in params and params["apply"].lower() in APPLY_TRUTHY
        if "apply" in params:
            notes.append("apply explicit=%s (--apply is appended only on an explicit "
                         "human instruction; the dry-run default invariant stands, "
                         "same as cw_sentinel.py:57)" % params["apply"])
        if not problems:
            route["cmd"] = ("bash cw.sh unclog --src %s --world %s%s"
                            % (src, world, " --apply" if apply_on else ""))
            route["params"] = {"src": {"value": src, "source": s1},
                               "world": {"value": world, "source": s2}}
    elif kind == "build-signal":
        route["id"] = "wash-shape"
        if "file" in params:
            files, fsource = [params["file"]], "param"
        elif isinstance(ev.get("file"), list) and ev["file"]:
            files, fsource = [str(x) for x in ev["file"]], "event"
        elif isinstance(ev.get("file"), str) and ev["file"].strip():
            files, fsource = [ev["file"]], "event"
        else:
            files, fsource = [], "derive"
            for h in (ev.get("hits") or []):
                for m in V_FILE_RE.findall(str(h)):
                    if m not in files:
                        files.append(m)
        files = [cmd_path(f) for f in files]   # path-shaped params: canonical separator face
        if not files:
            problems.append("wash-shape route parameter unsolvable: file (--param, "
                            "event file, and .v collection from the hits text are "
                            "all empty)")
        else:
            _guard("file", " ".join(files))
        if not problems:
            route["cmd"] = "bash cw.sh wash-shape" + "".join(
                " --file %s" % f for f in files)
            route["params"] = {"file": {"value": files, "source": fsource}}
    return route, problems


# ---- state (re-route guard persistence; shape corruption fails loudly, never
# ---- rebuilt) --------------------------------------------------------------------

def load_state(path):
    if not os.path.isfile(path):
        return {"schema": STATE_SCHEMA, "dispatched": {}}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise DispatchError("state shape corruption: %s (%s); fail loudly and refuse "
                            "to rebuild (same crash-recovery discipline as "
                            "cw_sentinel.py:136; recovery is manual file removal only)"
                            % (path, e), 9)
    if not isinstance(st, dict) or st.get("schema") != STATE_SCHEMA \
            or not isinstance(st.get("dispatched"), dict):
        raise DispatchError("state shape corruption: %s (schema/dispatched face "
                            "unrecognized; refusing to rebuild)" % path, 9)
    return st


def save_state(path, st):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise DispatchError("state directory missing: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


def write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise DispatchError("report output directory missing: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- execution and processing ---------------------------------------------------

def run_dispatch_cmd(cmd):
    """command executor (same shape as the cw_sentinel fire_on_red executor,
    py:831-842; 60s cap) → (rc|None, output). rc=None means timeout (the cap prevents
    hangs; it does not guarantee completion)."""
    try:
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=EXEC_TIMEOUT)
        out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return None, "timeout (%ds cap)" % EXEC_TIMEOUT


def process(args, items):
    """route each event → report dict. Only the auto tier executes and dedups
    (report-only/suggest have zero side effects; state keys already on file are still
    reported). Non-zero rc and timeouts are recorded loudly; the exit code is unchanged."""
    state = load_state(args.state_file) if args.state_file \
        else {"schema": STATE_SCHEMA, "dispatched": {}}
    entries, executed, skipped = [], 0, 0
    now = time.time()
    dirty = False
    for it in items:
        route = it["route"]
        entry = {"event": it["ev"], "route": route["id"], "key": it["key"],
                 "notes": list(route.get("notes") or [])}
        if route.get("cmd"):
            entry["action_cmd"] = route["cmd"]
        if route.get("params"):
            entry["params"] = route["params"]
        if route.get("fix_list") is not None:
            entry["fix_list"] = route["fix_list"]
        if args.preset == "auto" and entry.get("action_cmd"):
            if args.dry_run:
                entry["notes"].append("dry-run; command printed, not run (executed "
                                      "counts 0; state not written)")
            else:
                rec = state["dispatched"].get(it["key"])
                if rec is not None and \
                        (now - float(rec.get("ts") or 0.0)) < args.cooldown:
                    skipped += 1
                    entry["skipped"] = True
                    entry["notes"].append("skipped inside the cooldown window "
                                          "(cooldown=%ds; state record kept; a skip "
                                          "does not update ts)" % args.cooldown)
                else:
                    rc, out = run_dispatch_cmd(entry["action_cmd"])
                    entry["executed"] = True
                    entry["rc"] = rc
                    entry["output"] = clip(out)
                    executed += 1
                    dirty = True
                    state["dispatched"][it["key"]] = {
                        "ts": now, "rc": rc,
                        "cmd": clip(entry["action_cmd"], STATE_CMD_CLIP)}
                    if rc is None:
                        sys.stdout.write("executor note: timeout (%ds cap; recorded, "
                                         "exit unchanged) cmd=%s\n"
                                         % (EXEC_TIMEOUT, entry["action_cmd"]))
                    elif rc != 0:
                        sys.stdout.write("executor note: rc=%d non-zero (recorded "
                                         "loudly; exit unchanged) cmd=%s\n"
                                         % (rc, entry["action_cmd"]))
        entries.append(entry)
    if dirty and args.state_file:
        save_state(args.state_file, state)
    rep = {"schema": SCHEMA, "preset": args.preset, "cooldown": args.cooldown,
           "events": entries,
           "summary": {"routed": len(items), "executed": executed,
                       "skipped": skipped}}
    if args.state_file:
        rep["state_file"] = args.state_file
    if args.dry_run:
        rep["dry_run"] = True
    return rep


def identity(ev):
    """loud short identity string for one event (used in the per-event stdout lines)."""
    k = ev.get("kind")
    if k == "ci-red":
        return "repo=%s run=%s family=%s" % (ev.get("repo"), ev.get("run"),
                                             ev.get("family"))
    if k == "blocking":
        return "top_root=%s ledger=%s" % (ev.get("top_root"), ev.get("ledger"))
    if k == "build-signal":
        return "log=%s hits=%d" % (ev.get("log"), len(ev.get("hits") or []))
    return ""


def render(rep, args):
    """loud stdout report (deterministic wording; no ts; rc values recorded)."""
    w = sys.stdout.write
    preset = rep["preset"]
    mode_note = {"report-only": "a failing result is data; routing executes nothing",
                 "suggest": "a failing result is data; routing executes nothing, "
                            "plus copy blocks",
                 "auto": "auto hook; 60s cap; non-zero rc recorded, exit unchanged"}[preset]
    if rep.get("dry_run"):
        mode_note += "; dry-run prints only"
    w("=== RED-DISPATCH preset=%s events=%d (%s) ===\n"
      % (preset, len(rep["events"]), mode_note))
    for i, e in enumerate(rep["events"], 1):
        w("[%d] %s %s → %s\n" % (i, e["event"].get("kind"),
                                 identity(e["event"]), e["route"]))
        if "action_cmd" in e:
            w("    cmd: %s\n" % e["action_cmd"])
        for n in e.get("notes") or []:
            w("    note: %s\n" % n)
        for f in e.get("fix_list") or []:
            w("    fix list: %s\n" % f)
        if preset == "suggest" and "action_cmd" in e:
            w("    +-- copy and run --+\n    %s\n    +----------------+\n"
              % e["action_cmd"])
        if e.get("skipped"):
            w("    skipped (inside the cooldown window; not re-run)\n")
        if "executed" in e:
            rc = e.get("rc")
            if rc is None:
                w("    execution timed out (%ds cap; recorded, exit unchanged)\n"
                  % EXEC_TIMEOUT)
            elif rc == 0:
                w("    executed rc=0\n")
            else:
                w("    executed rc=%d (non-zero; recorded loudly; exit unchanged)\n" % rc)
    s = rep["summary"]
    w("=== SUMMARY routed=%d executed=%d skipped=%d (exit 0; a failing result is data, "
      "not a tool failure) ===\n"
      % (s["routed"], s["executed"], s["skipped"]))


# ---- CLI -----------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(prog=PROG)
    ap.add_argument("--event-file", dest="event_file", default=None, metavar="PATH",
                    help="sentinel red-event JSONL file (stdin is read by default; "
                         "when given, stdin is not read)")
    ap.add_argument("--preset", choices=("report-only", "suggest", "auto"),
                    default="report-only",
                    help="report-only = default, zero execution | suggest = plus copy "
                         "blocks | auto = runs on explicit request (60s cap)")
    ap.add_argument("--json", dest="json_out", default=None, metavar="OUT",
                    help="route report JSON output path (rocqwash-red-dispatch/1; "
                         "sort_keys)")
    ap.add_argument("--state-file", dest="state_file", default=None, metavar="PATH",
                    help="re-dispatch guard state (rocqwash-red-dispatch-state/1; "
                         "in-memory by default)")
    ap.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN, metavar="S",
                    help="minimum seconds between same-key dispatches (default 600; "
                         "0 disables the window)")
    ap.add_argument("--repo-path", dest="repo_path", default=None, metavar="DIR",
                    help="local repository root anchor (base for deriving unclog "
                         "src/world %s)" % WORLD_REL)
    ap.add_argument("--param", dest="params", action="append", default=[],
                    metavar="K=V",
                    help="extra route parameters (repeatable; keys %s)"
                         % ",".join(PARAM_KEYS))
    ap.add_argument("--on-args", dest="params", action="append", metavar="K=V",
                    help="alias of --param (the same option under a second spelling)")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="under the auto tier, print the would-be command without "
                         "running it (given under another tier -> 2)")
    ap.add_argument("--selftest", action="store_true",
                    help="vector self-check (offline, zero network; tmp fixtures; "
                         "0 = all passed / 2 = assertion failure)")
    a = ap.parse_args(argv)
    if a.cooldown < 0:
        raise DispatchError("--cooldown must be >= 0 (found %d)" % a.cooldown, 2)
    if a.dry_run and a.preset != "auto":
        raise DispatchError("--dry-run requires --preset auto (auto-tier semantics; "
                            "found preset=%s)" % a.preset, 2)
    seen = {}
    for raw in (a.params or []):
        if "=" not in raw:
            raise DispatchError("--param/--on-args malformed (expected K=V): %r" % raw, 2)
        k, v = raw.split("=", 1)
        k = k.strip().replace("-", "_")
        if not k:
            raise DispatchError("--param/--on-args empty K: %r" % raw, 2)
        if not v.strip():
            raise DispatchError("--param/--on-args empty V: %r" % raw, 2)
        if k not in PARAM_KEYS:
            raise DispatchError("--param/--on-args unknown key (key union %s): %s"
                                % (",".join(PARAM_KEYS), k), 2)
        if k in seen:
            raise DispatchError("--param/--on-args duplicate key: %s" % k, 2)
        seen[k] = v
    if "apply" in seen and seen["apply"].lower() not in APPLY_TRUTHY:
        raise DispatchError("--param apply value must be one of %s (found %r)"
                            % ("/".join(APPLY_TRUTHY), seen["apply"]), 2)
    a.params = seen
    return a


def _loud_err(e):
    tag = {2: "usage error", 9: "missing/malformed input"}.get(e.code, "error (rc=%d)" % e.code)
    sys.stdout.write("RED-DISPATCH %s (rc=%d): %s\n" % (tag, e.code, e.msg))


def main(argv=None, stdin_text=None):
    """entry → exit code (0 processed / 2 usage / 9 missing input). stdin_text is the
    test injection point (selftest use; bypasses the tty check)."""
    try:
        args = parse_args(sys.argv[1:] if argv is None else list(argv))
    except DispatchError as e:
        _loud_err(e)
        return e.code
    if args.selftest:
        return selftest()
    try:
        if args.event_file:
            if not os.path.isfile(args.event_file):
                raise DispatchError("missing input: event file not found: %s"
                                    % args.event_file, 9)
            with io.open(args.event_file, "r", encoding="utf-8") as fh:
                text = fh.read()
            source = args.event_file
        else:
            if stdin_text is not None:
                text = stdin_text
            elif sys.stdin.isatty():
                raise DispatchError("missing input: --event-file absent and stdin is a "
                                    "terminal (no piped input; see --help)", 9)
            else:
                text = sys.stdin.read()
            source = "stdin"
        events = parse_events(text, source)
        items, all_problems = [], []
        for idx, ev in enumerate(events, 1):
            where = "event %d" % idx
            problems, kind = collect_field_problems(ev, where)
            all_problems.extend(problems)
            if kind is None:
                continue
            route, rproblems = build_route(ev, kind, args.params, args.repo_path)
            all_problems.extend(rproblems)
            items.append({"ev": ev, "route": route, "key": state_key(ev)})
        if all_problems:
            raise DispatchError("missing/malformed input, %d finding(s) "
                                "(validate-all-then-execute; the whole batch dispatches "
                                "and executes nothing):\n  %s"
                                % (len(all_problems), "\n  ".join(all_problems)), 9)
        rep = process(args, items)
        if args.json_out:
            write_json(args.json_out, rep)
        render(rep, args)
        return 0
    except DispatchError as e:
        _loud_err(e)
        return e.code


# ---- selftest (vectors 1-12; tmp fixtures; offline, zero network) ----------------

def _write_tmp(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _load_tmp(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def selftest():
    sys.stdout.write("=== RED-DISPATCH SELFTEST (tmp fixtures; offline, zero network) ===\n")
    failures = []

    def check(name, cond, detail=""):
        if cond:
            sys.stdout.write("  PASS %s\n" % name)
        else:
            failures.append(name)
            sys.stdout.write("  FAIL %s %s\n" % (name, detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_red_dispatch_self_")
    oldcwd = os.getcwd()
    old_log = os.environ.get("RED_DISPATCH_LOG")
    old_rc = os.environ.get("RED_DISPATCH_RC")
    live = os.path.join(tmp, "ConstructiveWorld_Live")
    try:
        # fake repo root: the fake cw.sh proves route via a marker file
        # (RED_DISPATCH_LOG / RED_DISPATCH_RC environment parameters)
        _write_tmp(os.path.join(tmp, "cw.sh"),
                   '#!/bin/bash\nprintf \'%s\\n\' "$*" >> "$RED_DISPATCH_LOG"\n'
                   'exit ${RED_DISPATCH_RC:-0}\n')
        logp = os.path.join(tmp, "dispatched.log")

        EV_B = {"kind": "ci-red", "repo": "ORG/R1", "run": 178, "branch": "main",
                "family": "B-netred", "action": "rerun-after-stable-window",
                "evidence": ["failure-step: upload-artifact"]}
        EV_E = {"kind": "ci-red", "repo": "ORG/R1", "run": 179, "branch": "main",
                "family": "E-coqchk-skipped", "action": "rerun-after-stable-window",
                "evidence": ["coqchk step skipped = gate2 not reached (family E signature)"]}
        EV_A = {"kind": "ci-red", "repo": "ORG/R1", "run": 180, "branch": "dev",
                "family": "A-content-red", "action": "fix-content",
                "evidence": ["Error: AbsSq.v:12", "FAIL axiom count nonzero"]}
        EV_C = {"kind": "ci-red", "repo": "ORG/R1", "run": 181, "branch": "main",
                "family": "C-toolchain-break", "action": "restore-toolchain",
                "evidence": ["EXIT=134"]}
        EV_D = {"kind": "ci-red", "repo": "ORG/R1", "run": 182, "branch": "main",
                "family": "D-queue-wall", "action": "queue-etiquette",
                "evidence": ["steps=0 (zero steps)"]}
        EV_BL = {"kind": "blocking", "ledger": "probe_x.json", "top_root": "FooBasics",
                 "dependents": ["A.v", "B.v"], "n": 2}
        EV_BS = {"kind": "build-signal", "log": "/tmp/build.log",
                 "hits": ["Error: src/AbsSq.v:12: syntax error", "BUILD-FAIL: rc=1"]}

        # vector 1: route-table family coverage (six shapes; all five route rows
        # exercised, plus out-of-spectrum watch-only)
        r_b, p1 = build_route(EV_B, "ci-red", {}, None)
        check("v1B pushci route", r_b["id"] == "pushci" and not p1, str(p1))
        check("v1B command shape", r_b.get("cmd") ==
              "bash cw.sh pushci --repo-path ORG/R1 --branch main --max-heal 3",
              str(r_b.get("cmd")))
        r_e, _ = build_route(EV_E, "ci-red", {}, None)
        check("v1E pushci same route", r_e["id"] == "pushci")
        r_a, _ = build_route(EV_A, "ci-red", {}, None)
        check("v1A manual-fix-note", r_a["id"] == "manual-fix-note"
              and not r_a.get("cmd"))
        r_c, _ = build_route(EV_C, "ci-red", {}, None)
        check("v1C doctor fixed command", r_c["id"] == "doctor"
              and r_c.get("cmd") == "bash cw.sh doctor")
        r_bl, pbl = build_route(EV_BL, "blocking", {}, tmp)
        check("v1BL unclog derivation", r_bl["id"] == "unclog" and not pbl
              and r_bl.get("cmd") ==
              "bash cw.sh unclog --src %s --world %s" % (cmd_path(live),
                                                         cmd_path(live))
              and r_bl["params"]["src"]["source"] == "derive", str(r_bl.get("cmd")))
        r_bs, pbs = build_route(EV_BS, "build-signal", {}, None)
        check("v1BS wash-shape collection", r_bs["id"] == "wash-shape" and not pbs
              and r_bs.get("cmd") == "bash cw.sh wash-shape --file src/AbsSq.v"
              and r_bs["params"]["file"]["source"] == "derive", str(r_bs.get("cmd")))
        r_d, _ = build_route(EV_D, "ci-red", {}, None)
        check("v1D watch-only", r_d["id"] == "watch-only" and not r_d.get("cmd"))

        # vector 2: placeholder substitution (explicit param override / event field /
        # derive anchor)
        r2, p2 = build_route(EV_B, "ci-red", {"branch": "dev", "max_heal": "5"}, None)
        check("v2 param override", not p2 and r2.get("cmd") ==
              "bash cw.sh pushci --repo-path ORG/R1 --branch dev --max-heal 5"
              and r2["params"]["branch"]["source"] == "param", str(p2))
        r2b, _ = build_route(EV_B, "ci-red", {"repo_path": "/tmp/local"}, None)
        check("v2 explicit repo_path overrides the event",
              "--repo-path /tmp/local" in r2b.get("cmd", ""))
        r2c, _ = build_route(EV_BL, "blocking", {"src": "/x/s", "world": "/x/w"}, None)
        check("v2 explicit src/world", r2c.get("cmd") ==
              "bash cw.sh unclog --src /x/s --world /x/w")
        r2d, _ = build_route(EV_BL, "blocking", {"apply": "on"}, tmp)
        check("v2 explicit --apply appended", r2d.get("cmd", "").endswith(" --apply"))
        r2e, _ = build_route(EV_BL, "blocking", {}, tmp)
        check("v2 default omits --apply", "--apply" not in r2e.get("cmd", ""))

        # vectors 3-5: auto execution proof, state dedup, cooldown (chdir into the
        # fake repo root; marker file)
        os.chdir(tmp)
        os.environ["RED_DISPATCH_LOG"] = logp
        evfile = os.path.join(tmp, "ev_b.jsonl")
        _write_tmp(evfile, json.dumps(EV_B, sort_keys=True) + "\n")
        argv3 = ["--event-file", evfile, "--preset", "auto",
                 "--state-file", os.path.join(tmp, "st3.json"),
                 "--json", os.path.join(tmp, "r3.json")]
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            rc3 = main(argv3)
        check("v3 auto exit 0", rc3 == 0, str(rc3))
        log3 = _load_tmp(logp) if os.path.isfile(logp) else ""
        check("v3 marker-file proof", "--repo-path ORG/R1 --branch main --max-heal 3"
              in log3, repr(log3[:120]))
        rep3 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("v3 executed=1 rc=0",
              rep3["summary"] == {"routed": 1, "executed": 1, "skipped": 0}
              and rep3["events"][0].get("rc") == 0
              and rep3["events"][0].get("executed") is True,
              json.dumps(rep3["summary"], sort_keys=True))
        st3 = json.loads(_load_tmp(os.path.join(tmp, "st3.json")))
        check("v3 state key recorded",
              "ci-red|ORG/R1|178|B-netred" in st3["dispatched"]
              and st3["schema"] == "rocqwash-red-dispatch-state/1",
              json.dumps(st3, sort_keys=True)[:160])
        buf4 = io.StringIO()
        with contextlib.redirect_stdout(buf4):
            rc4 = main(argv3)
        rep4 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("v4 second run deduped, skipped", rc4 == 0
              and rep4["summary"] == {"routed": 1, "executed": 0, "skipped": 1}
              and rep4["events"][0].get("skipped") is True
              and len(log3.splitlines()) == len(_load_tmp(logp).splitlines()),
              json.dumps(rep4["summary"], sort_keys=True))
        argv5 = argv3 + ["--cooldown", "0"]
        buf5 = io.StringIO()
        with contextlib.redirect_stdout(buf5):
            rc5 = main(argv5)
        rep5 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("v5 cooldown=0 window open, dispatched again", rc5 == 0
              and rep5["summary"] == {"routed": 1, "executed": 1, "skipped": 0}
              and len(_load_tmp(logp).splitlines()) == 2,
              json.dumps(rep5["summary"], sort_keys=True))

        # vector 6: report-only default executes nothing (no marker file)
        if os.path.isfile(logp):
            os.unlink(logp)
        argv6 = ["--event-file", evfile, "--json", os.path.join(tmp, "r6.json")]
        buf6 = io.StringIO()
        with contextlib.redirect_stdout(buf6):
            rc6 = main(argv6)
        check("v6 report-only zero execution", rc6 == 0 and not os.path.isfile(logp)
              and json.loads(_load_tmp(os.path.join(tmp, "r6.json")))
              ["summary"] == {"routed": 1, "executed": 0, "skipped": 0},
              str(rc6))

        # vector 7: multi-event JSONL via stdin (suggest copy blocks)
        jsonl3 = "\n".join(json.dumps(x, sort_keys=True)
                           for x in (EV_B, EV_BL, EV_BS)) + "\n"
        argv7 = ["--preset", "suggest", "--repo-path", tmp,
                 "--json", os.path.join(tmp, "r7.json")]
        buf7 = io.StringIO()
        with contextlib.redirect_stdout(buf7):
            rc7 = main(argv7, stdin_text=jsonl3)
        rep7 = json.loads(_load_tmp(os.path.join(tmp, "r7.json")))
        out7 = buf7.getvalue()
        check("v7 three stdin events routed", rc7 == 0
              and rep7["summary"]["routed"] == 3
              and [e["route"] for e in rep7["events"]] ==
              ["pushci", "unclog", "wash-shape"],
              json.dumps(rep7["summary"], sort_keys=True))
        check("v7 suggest copy blocks", out7.count("+-- copy and run --+") == 3,
              out7[-300:])

        # vector 8: fail-loud faces
        buf8a = io.StringIO()
        with contextlib.redirect_stdout(buf8a):
            rc8a = main(["--preset", "report-only", "--json",
                         os.path.join(tmp, "r8a.json")],
                        stdin_text=json.dumps({"kind": "ci-red", "repo": "ORG/R2",
                                               "run": 9, "action": "fix-content"}))
        check("v8a missing family, exit 9, listed",
              rc8a == 9 and "family missing" in buf8a.getvalue(),
              "%d %s" % (rc8a, buf8a.getvalue()[:200]))
        buf8b = io.StringIO()
        with contextlib.redirect_stdout(buf8b):
            rc8b = main(["--preset", "report-only", "--param", "bogus=1"],
                        stdin_text=json.dumps(EV_B))
        check("v8b unknown param key, exit 2", rc8b == 2, str(rc8b))
        buf8c = io.StringIO()
        with contextlib.redirect_stdout(buf8c):
            rc8c = main(["--preset", "report-only", "--param", "branch=a",
                         "--on-args", "branch=b"], stdin_text=json.dumps(EV_B))
        check("v8c duplicate key, exit 2", rc8c == 2, str(rc8c))
        buf8d = io.StringIO()
        with contextlib.redirect_stdout(buf8d):
            rc8d = main(["--preset", "report-only", "--dry-run"],
                        stdin_text=json.dumps(EV_B))
        check("v8d dry-run tier mismatch, exit 2", rc8d == 2, str(rc8d))
        bad_meta = dict(EV_B, repo="ORG/R;rm")
        buf8e = io.StringIO()
        with contextlib.redirect_stdout(buf8e):
            rc8e = main(["--preset", "report-only"],
                        stdin_text=json.dumps(bad_meta))
        check("v8e metacharacter refusal, exit 9",
              rc8e == 9 and "shell metacharacters" in buf8e.getvalue(),
              "%d %s" % (rc8e, buf8e.getvalue()[:200]))
        _write_tmp(os.path.join(tmp, "st8f.json"), "]{not json")
        buf8f = io.StringIO()
        with contextlib.redirect_stdout(buf8f):
            rc8f = main(["--preset", "auto", "--event-file", evfile,
                         "--state-file", os.path.join(tmp, "st8f.json")])
        check("v8f state shape corruption, exit 9",
              rc8f == 9 and "state shape corruption" in buf8f.getvalue(),
              "%d %s" % (rc8f, buf8f.getvalue()[:200]))
        buf8g = io.StringIO()
        with contextlib.redirect_stdout(buf8g):
            rc8g = main(["--preset", "report-only"],
                        stdin_text=json.dumps({"kind": "weird"}))
        check("v8g unrecognized kind, exit 9",
              rc8g == 9 and "kind unrecognized" in buf8g.getvalue(),
              "%d" % rc8g)

        # vector 9: non-zero rc leaves the exit code unchanged (fake cw.sh exits 3;
        # rc=3 recorded)
        os.environ["RED_DISPATCH_RC"] = "3"
        argv9 = ["--event-file", evfile, "--preset", "auto",
                 "--state-file", os.path.join(tmp, "st9.json"),
                 "--json", os.path.join(tmp, "r9.json")]
        buf9 = io.StringIO()
        with contextlib.redirect_stdout(buf9):
            rc9 = main(argv9)
        rep9 = json.loads(_load_tmp(os.path.join(tmp, "r9.json")))
        check("v9 non-zero rc leaves exit unchanged", rc9 == 0
              and rep9["events"][0].get("rc") == 3
              and rep9["summary"]["executed"] == 1
              and "rc=3 (non-zero" in buf9.getvalue(),
              "%d %s" % (rc9, json.dumps(rep9["summary"], sort_keys=True)))
        if old_rc is None:
            os.environ.pop("RED_DISPATCH_RC", None)
        else:
            os.environ["RED_DISPATCH_RC"] = old_rc

        # vector 10: family-A fix list plus the family-C fixed command (content-face
        # coupling)
        check("v10A fix list = evidence excerpts",
              r_a.get("fix_list") == ["Error: AbsSq.v:12", "FAIL axiom count nonzero"]
              and any("no automated edits" in n for n in r_a.get("notes") or []),
              json.dumps(r_a.get("fix_list"), ensure_ascii=False))
        ev_a_noev = {"kind": "ci-red", "repo": "ORG/R1", "run": 183,
                     "branch": "dev", "family": "A-content-red",
                     "action": "fix-content"}
        r_a2, _ = build_route(ev_a_noev, "ci-red", {}, None)
        check("v10A missing evidence degrades to pointers",
              any("evidence absent" in n for n in r_a2.get("notes") or [])
              and r_a2.get("fix_list"), json.dumps(r_a2.get("notes")))
        check("v10C doctor bare form", r_c.get("cmd") == "bash cw.sh doctor")

        # vector 11: determinism (two suggest runs, byte-identical JSON)
        det_in = "\n".join(json.dumps(x, sort_keys=True)
                           for x in (EV_B, EV_A, EV_C)) + "\n"
        out_a, out_b = os.path.join(tmp, "d1.json"), os.path.join(tmp, "d2.json")
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--preset", "suggest", "--json", out_a], stdin_text=det_in)
            main(["--preset", "suggest", "--json", out_b], stdin_text=det_in)
        check("v11 two runs byte-identical", _load_tmp(out_a) == _load_tmp(out_b))

        # vector 12: whole-text single-object fallback
        pretty = json.dumps(EV_B, indent=1, sort_keys=True)
        check("v12 pretty single-object fallback", len(parse_events(pretty, "t")) == 1)
        check("v12 JSONL three lines", len(parse_events(jsonl3, "t")) == 3)
    finally:
        os.chdir(oldcwd)
        if old_log is None:
            os.environ.pop("RED_DISPATCH_LOG", None)
        else:
            os.environ["RED_DISPATCH_LOG"] = old_log
        if old_rc is not None:
            os.environ["RED_DISPATCH_RC"] = old_rc
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        sys.stdout.write("RED-DISPATCH-SELFTEST FAIL: %d failed check(s): %s\n"
                         % (len(failures), ",".join(failures)))
        return 2
    sys.stdout.write("RED-DISPATCH-SELFTEST PASS: all 12 vectors passed (route "
                     "families/placeholders/auto execution/state dedup/cooldown/"
                     "report-only zero execution/stdin multi-event/fail-loud/non-zero "
                     "rc recorded/fix list/determinism/single-object fallback)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
