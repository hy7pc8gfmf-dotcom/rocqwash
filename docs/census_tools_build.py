#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""census_tools_build.py -- word-face census builder for rocqwash tools/ .

Method: pure lexical/AST analysis (ast.parse over source bytes). No tool
listed in tools/ is executed, imported, or spawned by this script; only the
Python standard library is used and the script itself is run with -I
(isolated mode). Extraction faces per file:

  name / bytes / sha256 / line count
  module docstring (verbatim head, bounded)
  argparse face: imports, ArgumentParser descriptions, add_argument list
    (flags + constant kwargs), add_parser subcommands, set_defaults(func=...)
  usage string face: "usage:" / "python3 tools/X.py" lines
  dependency face: import list, stdlib / third-party / local classification
  network face: transport-capable imports, urllib-adjacent imports,
    literal token scan (curl/wget/api hosts), subprocess bridge suspicion
  special-environment (SKIP) face: lexical markers (ROCWASH_* env, Coq/Rocq,
    Lean/lake/mathlib, macOS tooling, Windows guards, GPG, thermal wrapper,
    self-hosted runner)
  invocation form: reconstructed from argparse when present, else from
    usage strings, else marked not reconstructed.

Boundary: everything here is word-face evidence. Runtime behavior, real exit
codes, and help-text output are NOT measured by this census (that belongs to
a later light-probe pass). Negative findings are recorded with their scan
boundary stated in census.md.
"""

import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import sys

TOOLS_DIR = "D:/ComplexAnalysis/rocqwash/tools"
OUT_JSON = "D:/ComplexAnalysis/attn/_rqw06_capindex_20261114/census-tools.json"

# --- network classification -------------------------------------------------
TRANSPORT_IMPORTS = {
    "urllib.request", "urllib.error.request", "http.client", "http.cookiejar",
    "socket", "socketserver", "ssl", "requests", "httpx", "aiohttp",
    "ftplib", "telnetlib", "smtplib", "poplib", "imaplib", "nntplib",
    "xmlrpc.client", "xmlrpc.server", "websocket", "websockets", "curl_cffi",
}
TRANSPORT_ROOTS = {"socket", "ssl", "requests", "httpx", "aiohttp", "ftplib",
                   "telnetlib", "smtplib", "poplib", "imaplib", "nntplib",
                   "websocket", "websockets", "curl_cffi"}
ADJACENT_IMPORTS = {"urllib.parse", "urllib.error", "urllib.response",
                    "urllib.robotparser", "ipaddress", "http.cookies"}

NET_LITERAL_TOKENS = [
    ("curl_subprocess", re.compile(r"\bcurl\b")),
    ("wget", re.compile(r"\bwget\b")),
    ("api_github", re.compile(r"api\.github\.com")),
    ("githubusercontent", re.compile(r"githubusercontent\.com")),
    ("github_com", re.compile(r"(?<![\w.])github\.com")),
    ("https_url", re.compile(r"https?://")),
    ("ghproxy", re.compile(r"ghproxy")),
]
SUBPROCESS_BRIDGE_TOKENS = re.compile(
    r"\bcurl\b|\bwget\b|api\.github\.com|githubusercontent\.com|ghproxy")
# git subcommands that reach the network, as standalone quoted tokens
# (list-form subprocess invocation never matches a line-level "git push").
GIT_NET_TOKENS = re.compile(r"[\"'](push|fetch|clone|pull|ls-remote)[\"']")

# --- SKIP-face marker families ---------------------------------------------
SKIP_MARKERS = [
    ("env_rocwash", re.compile(r"ROCWASH_[A-Z0-9_]+")),
    ("ocaml_opam", re.compile(r"\bocamlc\b|\bocamldep\b|\bopam\b")),
    ("coq_rocq", re.compile(r"\bcoq(c|top|chk|dep)\b|\brocqw?orker\b|\brocq\b(?!\w)|_CoqProject")),
    ("lean_lake_mathlib", re.compile(r"\blake\b|\bmathlib\b|\bLean4?\b|\bLEAN_[A-Z_]+|\belan\b|\.lean\b")),
    ("macos_tooling", re.compile(r"/opt/homebrew|\bdyld\w*|\botool\b|install_name_tool|\bdarwin\b|\bmacos\b", re.I)),
    ("windows_guard", re.compile(r"\bwin32\b|\bWindows\b")),
    ("gpg_signing", re.compile(r"\bgpg\b", re.I)),
    ("thermal_wrapper", re.compile(r"cpu_guard|_THERMAL[A-Z_]*")),
    ("selfhosted_runner", re.compile(r"self-hosted|actions-runner")),
]
SKIP_KINDS_SPECIAL = {"env_rocwash", "ocaml_opam", "coq_rocq",
                      "lean_lake_mathlib", "macos_tooling", "gpg_signing",
                      "thermal_wrapper", "selfhosted_runner"}

USAGE_RE = re.compile(r"^[ \t]*(?:usage|用法)[ \t]*[:：]", re.M)
PYLINE_RE = re.compile(r"^[ \t]*(?:\$[ \t]*)?python3?[ \t]+(?:tools/|tools\\)?[\w./\\]+\.py[^\n]*", re.M)
REPO_STEMS = frozenset()


def const_of(node):
    """Return the constant value of an AST node, or None."""
    if isinstance(node, ast.Constant):
        v = node.value
        return v if isinstance(v, (str, int, float, bool, type(None))) else None
    return None


def kwarg_record(call):
    """Summarize relevant constant kwargs of a call node."""
    keys = ("action", "nargs", "default", "required", "choices", "type",
            "dest", "metavar", "help")
    out = {}
    for kw in call.keywords:
        if kw.arg in keys:
            v = const_of(kw.value)
            if v is None and not isinstance(kw.value, ast.Constant):
                out[kw.arg] = "<dynamic>"
            elif isinstance(v, (list, tuple)):
                out[kw.arg] = [const_of(e) if isinstance(e, ast.Constant) else "<expr>" for e in kw.value.elts] if isinstance(kw.value, ast.Expr) else v
            else:
                out[kw.arg] = v
    return out


def analyze(path, sibling_stems, repo_stems):
    global REPO_STEMS
    REPO_STEMS = repo_stems
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    size = len(raw)
    sha = hashlib.sha256(raw).hexdigest()
    lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)

    rec = {
        "name": os.path.basename(path),
        "bytes": size,
        "sha256": sha,
        "lines": lines,
        "underscore_prefix": os.path.basename(path).startswith("_"),
        "has_main_guard": bool(re.search(
            r"__name__\s*==\s*['\"]__main__['\"]", text)),
        "docstring": {"present": False, "lines": 0, "head": ""},
        "argparse": {"imported": False, "parser_descriptions": [],
                     "add_argument": [], "positionals": [],
                     "optionals": [], "subcommands": [],
                     "has_subparsers": False, "set_defaults_func": False},
        "usage_face": [],
        "imports": {"modules": [], "third_party": [], "local": [],
                    "guarded_conditional": []},
        "network": {"transport_imports": [], "adjacent_imports": [],
                    "literal_face": [], "subprocess_bridge_suspect": False,
                    "zero_network": True},
        "skip_face": {"markers": [], "needs_special_environment": False},
        "invocation": {"form": "", "basis": ""},
        "selftest_flag": False,
    }

    # ---- docstring ----
    try:
        tree = ast.parse(raw)
    except SyntaxError as exc:
        rec["syntax_error"] = str(exc)
        tree = None
    if tree is not None:
        doc = ast.get_docstring(tree)
        if doc:
            rec["docstring"]["present"] = True
            rec["docstring"]["lines"] = doc.count("\n") + 1
            rec["docstring"]["head"] = doc[:600]

    # ---- imports ----
    import_mods = set()
    guarded = set()
    if tree is not None:
        class ImpVisitor(ast.NodeVisitor):
            def __init__(self):
                self.try_depth = 0
            def visit_Try(self, node):
                self.try_depth += 1
                self.generic_visit(node)
                self.try_depth -= 1
            def _add(self, name):
                import_mods.add(name)
                if self.try_depth > 0:
                    guarded.add(name)
            def visit_Import(self, node):
                for alias in node.names:
                    self._add(alias.name)
            def visit_ImportFrom(self, node):
                if node.module and node.level == 0:
                    self._add(node.module)
        ImpVisitor().visit(tree)
    rec["imports"]["modules"] = sorted(import_mods)
    rec["imports"]["guarded_conditional"] = sorted(guarded)

    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    local, external = [], []
    for m in sorted(import_mods):
        root = m.split(".")[0]
        if m.startswith(".") or root in sibling_stems or root in REPO_STEMS:
            local.append(m)
        elif stdlib and root in stdlib:
            continue  # stdlib: listed in imports.modules only
        else:
            external.append(m)
    rec["imports"]["third_party"] = external
    rec["imports"]["local"] = local

    # ---- network face ----
    transport, adjacent = set(), set()
    for m in import_mods:
        root = m.split(".")[0]
        if m in TRANSPORT_IMPORTS or root in TRANSPORT_ROOTS or root == "urllib":
            # urllib root: inspect submodule detail
            if m.startswith("urllib"):
                if m in ("urllib.request", "urllib.error.request"):
                    transport.add("urllib.request")
                elif m in ("urllib.parse", "urllib.error", "urllib.response",
                           "urllib.robotparser"):
                    adjacent.add(m)
                else:
                    # bare "import urllib" or unknown submodule: conservative
                    transport.add("urllib(unknown-submodule)")
            else:
                transport.add(m)
        elif m in ADJACENT_IMPORTS:
            adjacent.add(m)
    rec["network"]["transport_imports"] = sorted(transport)
    rec["network"]["adjacent_imports"] = sorted(adjacent)

    lit_hits = []
    for label, rx in NET_LITERAL_TOKENS:
        n = len(rx.findall(text))
        if n:
            lit_hits.append({"token": label, "count": n})
    rec["network"]["literal_face"] = lit_hits

    has_subprocess = "subprocess" in import_mods
    bridge = has_subprocess and bool(SUBPROCESS_BRIDGE_TOKENS.search(text))
    rec["network"]["subprocess_bridge_suspect"] = bridge
    git_net_tokens = sorted(set(GIT_NET_TOKENS.findall(text)))
    rec["network"]["git_subprocess_network_face"] = {
        "present": has_subprocess and bool(git_net_tokens),
        "tokens": git_net_tokens,
    }
    rec["network"]["zero_network"] = (not transport) and (not bridge) and \
        not rec["network"]["git_subprocess_network_face"]["present"]
    rec["selftest_token_face"] = "--selftest" in text

    # ---- SKIP face ----
    markers = []
    for kind, rx in SKIP_MARKERS:
        found = rx.findall(text)
        if found:
            distinct = sorted(set(found))[:5]
            markers.append({"kind": kind, "count": len(found),
                            "samples": distinct})
    rec["skip_face"]["markers"] = markers
    rec["skip_face"]["needs_special_environment"] = any(
        m["kind"] in SKIP_KINDS_SPECIAL for m in markers)

    # ---- usage face ----
    usage_lines = []
    for m in PYLINE_RE.finditer(text):
        s = m.group(0).strip()
        if s not in usage_lines:
            usage_lines.append(s)
        if len(usage_lines) >= 6:
            break
    for m in USAGE_RE.finditer(text):
        end = text.find("\n", m.start())
        s = text[m.start():end].strip() if end != -1 else text[m.start():].strip()
        if s not in usage_lines:
            usage_lines.append(s)
        if len(usage_lines) >= 8:
            break
    rec["usage_face"] = usage_lines[:8]

    # ---- argparse face ----
    events = []  # (lineno, kind, payload)
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    attr = func.attr
                elif isinstance(func, ast.Name):
                    attr = func.id
                else:
                    continue
                if attr == "add_argument" and node.args:
                    first = const_of(node.args[0])
                    flags = []
                    for a in node.args:
                        v = const_of(a)
                        if isinstance(v, str):
                            flags.append(v)
                    events.append((node.lineno, "add_argument",
                                   {"flags": flags, "kwargs": kwarg_record(node)}))
                elif attr == "add_parser" and node.args:
                    name = const_of(node.args[0])
                    helpv = None
                    for kw in node.keywords:
                        if kw.arg == "help":
                            helpv = const_of(kw.value)
                    events.append((node.lineno, "add_parser",
                                   {"name": name, "help": helpv}))
                elif attr == "ArgumentParser" or (isinstance(func, ast.Name) and attr == "ArgumentParser"):
                    desc = None
                    for kw in node.keywords:
                        if kw.arg == "description":
                            desc = const_of(kw.value)
                    events.append((node.lineno, "parser_ctor", {"description": desc}))
                elif attr == "set_defaults":
                    has_func = any(kw.arg == "func" for kw in node.keywords)
                    if has_func:
                        events.append((node.lineno, "set_defaults_func", {}))
                elif attr == "add_subparsers":
                    events.append((node.lineno, "add_subparsers", {}))

    ap = rec["argparse"]
    argparse_imported = any(m == "argparse" or m.startswith("argparse.")
                            for m in import_mods) or \
        any(m.split(".")[0] == "argparse" for m in import_mods)
    ap["imported"] = argparse_imported

    current_sub = None
    for lineno, kind, payload in sorted(events):
        if kind == "parser_ctor":
            if payload.get("description"):
                ap["parser_descriptions"].append(payload["description"][:200])
            current_sub = None
        elif kind == "add_subparsers":
            ap["has_subparsers"] = True
        elif kind == "set_defaults_func":
            ap["set_defaults_func"] = True
        elif kind == "add_parser":
            ap["subcommands"].append({"name": payload["name"],
                                      "help": payload["help"]})
            current_sub = payload["name"]
        elif kind == "add_argument":
            entry = {"flags": payload["flags"], "kwargs": payload["kwargs"]}
            if current_sub is not None:
                entry["after_subcommand"] = current_sub
            ap["add_argument"].append(entry)
            for f in payload["flags"]:
                if f.startswith("-"):
                    ap["optionals"].append(f)
                else:
                    ap["positionals"].append(f)
                if "selftest" in f.lower():
                    rec["selftest_flag"] = True

    # dedupe preserving order
    ap["positionals"] = list(dict.fromkeys(ap["positionals"]))
    ap["optionals"] = list(dict.fromkeys(ap["optionals"]))

    # ---- invocation form ----
    subs = [s["name"] for s in ap["subcommands"]]
    if argparse_imported and (ap["add_argument"] or subs):
        if subs:
            form = ("python tools/%s <subcommand> [options]  # subcommands: %s"
                    % (rec["name"], ", ".join(subs)))
        else:
            parts = ["python tools/" + rec["name"]]
            parts += ["<" + p + ">" for p in ap["positionals"]]
            parts += ["[" + o + "]" for o in ap["optionals"]]
            form = " ".join(parts)
        rec["invocation"] = {"form": form, "basis": "argparse-reconstructed"}
    elif usage_lines:
        rec["invocation"] = {"form": usage_lines[0], "basis": "usage-string"}
    else:
        rec["invocation"] = {"form": "", "basis": "not-reconstructed"}

    return rec


def main():
    parser = argparse.ArgumentParser(description="word-face census builder (no tool execution)")
    parser.add_argument("--tools-dir", default=TOOLS_DIR)
    parser.add_argument("--out", default=OUT_JSON)
    parser.add_argument("--head", default="", help="git HEAD sha of the scanned tree (recorded verbatim)")
    args = parser.parse_args()

    names = sorted(f for f in os.listdir(args.tools_dir) if f.endswith(".py"))
    sibling_stems = {os.path.splitext(f)[0] for f in os.listdir(args.tools_dir)}
    sibling_stems |= {f[1:-3] for f in names if f.startswith("_") and f.endswith(".py")}

    repo_stems = set()
    repo_root = os.path.dirname(os.path.abspath(args.tools_dir))
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            if fn.endswith(".py"):
                repo_stems.add(fn[:-3])

    records = []
    for f in names:
        rec = analyze(os.path.join(args.tools_dir, f), sibling_stems, repo_stems)
        if f == "vacgen.py":
            rec["new_item"] = True
        records.append(rec)

    meta = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "python -I AST word-face parse; no listed tool executed; stdlib only",
        "tools_dir": args.tools_dir,
        "git_head_recorded": args.head,
        "py_files_censused": len(records),
        "non_py_files_present": sorted(f for f in os.listdir(args.tools_dir) if not f.endswith(".py")),
        "summary": {
            "with_argparse": sum(1 for r in records if r["argparse"]["imported"]),
            "with_subcommands": sum(1 for r in records if r["argparse"]["has_subparsers"]),
            "zero_network": sum(1 for r in records if r["network"]["zero_network"]),
            "needs_special_environment": sum(1 for r in records if r["skip_face"]["needs_special_environment"]),
            "invocation_reconstructed": sum(1 for r in records if r["invocation"]["basis"] == "argparse-reconstructed"),
            "invocation_usage_string": sum(1 for r in records if r["invocation"]["basis"] == "usage-string"),
            "invocation_not_reconstructed": sum(1 for r in records if r["invocation"]["basis"] == "not-reconstructed"),
            "syntax_errors": sum(1 for r in records if "syntax_error" in r),
        },
    }

    out = {"meta": meta, "files": records}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("WROTE", args.out, "files=", len(records))

    # compact stdout digest for review
    for r in records:
        doc1 = (r["docstring"]["head"].strip().splitlines() or [""])[0][:90]
        subs = ",".join(s["name"] for s in r["argparse"]["subcommands"])
        print("- %s | %6dB | arg=%d sub=%d | net0=%d | env=%d | inv=%s" % (
            r["name"], r["bytes"], int(r["argparse"]["imported"]),
            len(r["argparse"]["subcommands"]),
            int(r["network"]["zero_network"]),
            int(r["skip_face"]["needs_special_environment"]),
            r["invocation"]["basis"]))
        if doc1:
            print("    doc: %s" % doc1)
        if subs:
            print("    subs: %s" % subs)
        if not r["network"]["zero_network"]:
            print("    net: %s | bridge=%s | git=%s" % (
                ",".join(r["network"]["transport_imports"]) or "-",
                r["network"]["subprocess_bridge_suspect"],
                r["network"]["git_subprocess_network_face"]["tokens"]))
        kinds = [m["kind"] for m in r["skip_face"]["markers"]]
        if kinds:
            print("    skip-kinds: %s" % ",".join(kinds))


if __name__ == "__main__":
    main()
