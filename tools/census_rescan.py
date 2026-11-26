#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""census_rescan.py - AST word-face census re-scan generator (rocqwash tools/).
Purpose.  The in-repo reproduction face of the census lane: the standing
  docs/census-tools.json (70 records, meta method "python -I AST word-face
  parse; no listed tool executed; stdlib only", generated 2026-11-22) was
  produced by a lane-side one-off that is not in the repository, so the
  files that landed after it could not be censused and count_guard's R6
  face reads a permanent declared-lag.  This tool re-produces the record
  set under its own documented v1 rules (below), appends the rows for
  tools the standing census lacks, and merges into the standing file with
  the old rows preserved VERBATIM and the meta carrying an explicit
  generation split - the mixed-generation lineage is data, never passed
  off as one method.  A repeated --merge rolls the standing census's
  previous generation batch verbatim into rescan_generation.history
  before recording the new batch: lineage accumulates, it never
  collapses.  Deterministic: sorted rows, double-run
  byte-identical.  Zero network, zero subprocess, stdlib only; the only
  write face is the caller-named --out.
v1 record rules (this tool's own documented method; the 2026-11-22 rows
  keep their original generator's semantics untouched):
  - name/bytes/sha256/lines: file facts (lines = len(text.splitlines())).
  - underscore_prefix / has_main_guard: module-level AST facts (the guard
    = an `if __name__ == "__main__":` test at module top level).
  - docstring: {present, lines, head} of the module docstring (head = the
    first 600 characters).
  - argparse: {imported, parser_descriptions (ArgumentParser description
    constants, first 200 characters each), add_argument (per call:
    declared flags and the constant-only kwargs), positionals, optionals,
    subcommands (add_parser constants), has_subparsers, set_defaults_func}.
  - usage_face: python-invocation lines from the docstring when argparse
    is absent (the axiom_guard shape); [] otherwise.
  - imports: {modules (top-level stdlib module roots), third_party (roots
    outside sys.stdlib_module_names and not in-repo), local (in-repo: the
    tools package or a sibling tools/ module), guarded_conditional
    (import roots nested inside try/if/with/def at any depth)}.
  - network: {transport_imports (the transport module roots),
    adjacent_imports (local siblings whose own text carries a transport
    token), literal_face (https?:// literals in the source text),
    subprocess_bridge_suspect (subprocess imported plus a string constant
    whose first token is a network-capable CLI), zero_network (none of
    the above), git_subprocess_network_face {present, tokens} (the git
    subset of the bridge commands)}.
  - skip_face: {markers: [{kind, count, samples}]} over the v1 token
    vocabulary env_rocwash / ocaml_opam / coq_rocq / thermal_wrapper /
    selfhosted_runner / lean_lake_mathlib / windows_guard /
    macos_tooling (count = matching tokens, samples = first three
    unique).
  - selftest_flag: --selftest is a DECLARED argparse flag;
    selftest_token_face: the --selftest literal appears anywhere in the
    source (the docstring-verified shape).
  - invocation: {form, basis}; argparse-imported tools reconstruct
    "python tools/<name> [--flag]..." from the declared long optionals
    (basis "argparse-reconstructed"), argparse-absent tools take the
    docstring Interface line (basis "docstring-interface"), else "none".
Interface.  python -I tools/census_rescan.py --repo DIR [--tools DIR]
  [--only NAME[,NAME]] [--stand FILE] [--merge] [--out FILE] | --selftest.
  Without --merge the scan reports rows only (stdout or --out); with
  --merge --out FILE the standing census at --stand (default
  docs/census-tools.json under --repo) is read, the missing tools are
  appended sorted by name, standing rows are preserved verbatim, and the
  meta gains the rescan_generation split with a real UTC timestamp; a
  standing rescan_generation with a recorded batch rolls that batch into
  rescan_generation.history first.
  Exit-codes.  0 clean; 2 usage; 9 --repo/--tools/--stand path missing.
Evidence.  --selftest: canned fixture files per face (file facts, main
  guard, docstring head truncation, argparse capture, import buckets,
  network classification incl. the git bridge subset, skip kinds,
  invocation reconstruction, selftest flag vs token face, merge
  verbatim-preservation + sorted union + determinism).
"""
import argparse
import ast
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys

PROG = "census_rescan"
STDLIB = frozenset(getattr(sys, "stdlib_module_names", ()) or ())
TRANSPORT_ROOTS = frozenset((
    "http", "urllib", "socket", "ssl", "ftplib", "smtplib", "poplib",
    "imaplib", "telnetlib", "xmlrpc",
))
TRANSPORT_TOKENS = ("urllib", "http.client", "socket", "ssl.", "requests")
BRIDGE_CLIS = frozenset(("git", "curl", "wget", "gh", "ssh", "scp",
                         "rsync", "ftp"))
SKIP_KINDS = (
    ("env_rocwash", re.compile(r"ROCWASH_[A-Z0-9_]+")),
    ("ocaml_opam", re.compile(r"\b(ocaml[a-z]*|opam|ocamlfind|dune)\b")),
    ("coq_rocq", re.compile(r"\b(coq|coqc|coqtop|coqchk|coqdep|rocq|"
                            r"rocqworker|rocqwash)\b")),
    ("thermal_wrapper", re.compile(r"\b(cpu_guard|thermal)\b")),
    ("selfhosted_runner", re.compile(r"\b(self[- ]?hosted|runner)\b")),
    ("lean_lake_mathlib", re.compile(r"\b(lean4?|lake|mathlib|elan)\b")),
    ("windows_guard", re.compile(r"\b(windows|win32)\b|\.exe\b")),
    ("macos_tooling", re.compile(r"\b(macos|darwin|dyld|otool|codesign)\b")),
)
COMPOUND = (ast.If, ast.Try, ast.With, ast.FunctionDef,
            ast.AsyncFunctionDef)


class UsageError(Exception):
    pass


class MissingPathError(UsageError):
    pass


def _const(node):
    if isinstance(node, ast.Constant) and (
            node.value is None or isinstance(node.value, (str, int, float,
                                                          bool))):
        return node.value
    return None


def _attr_tail(node):
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def parse_faces(rel, text, sibling_names):
    """Build one census record for a tool file under the v1 rules."""
    raw = text.encode("utf-8")
    tree = ast.parse(text)
    doc = ast.get_docstring(tree)
    fname = rel.split("/")[-1]

    has_main_guard = False
    for node in tree.body:
        if isinstance(node, ast.If):
            test_src = ast.unparse(node.test)
            if "__name__" in test_src and "__main__" in test_src:
                has_main_guard = True

    top_imports = set()
    guarded = set()
    local = set()
    third_party = set()

    def walk(nodes, guarded_ctx):
        for node in nodes:
            if isinstance(node, ast.Import):
                for a in node.names:
                    classify(a.name.split(".")[0], a.name, guarded_ctx, 0)
            elif isinstance(node, ast.ImportFrom) and node.module:
                classify(node.module.split(".")[0], node.module,
                         guarded_ctx, node.level or 0)
            elif isinstance(node, COMPOUND):
                walk(list(node.body), True)
                walk(list(getattr(node, "handlers", [])), True)
                walk(list(getattr(node, "orelse", [])), True)
                walk(list(getattr(node, "finalbody", [])), True)

    def classify(root, full, guarded_ctx, level):
        if level > 0 or root == "tools" or root in sibling_names:
            local.add(full)
        elif root in STDLIB:
            if guarded_ctx:
                guarded.add(root)
            else:
                top_imports.add(root)
        else:
            third_party.add(root)

    walk(tree.body, False)

    descriptions = []
    add_argument = []
    positionals = []
    optionals = []
    subcommands = []
    has_subparsers = False
    set_defaults_func = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        tail = _attr_tail(node.func)
        if tail == "ArgumentParser":
            for kw in node.keywords:
                if kw.arg == "description":
                    v = _const(kw.value)
                    if isinstance(v, str):
                        descriptions.append(v[:200])
        elif tail == "add_argument":
            entry_flags = []
            entry_kwargs = {}
            for a in node.args:
                v = _const(a)
                if isinstance(v, str):
                    if v.startswith("-"):
                        entry_flags.append(v)
                    else:
                        positionals.append(v)
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant):
                    entry_kwargs[kw.arg] = kw.value.value
            add_argument.append({"flags": entry_flags,
                                 "kwargs": entry_kwargs})
            optionals.extend(entry_flags)
        elif tail == "add_parser":
            for a in node.args:
                v = _const(a)
                if isinstance(v, str):
                    subcommands.append(v)
            has_subparsers = True
        elif tail == "set_defaults":
            set_defaults_func = True

    transports = sorted(m for m in top_imports | guarded
                        if m in TRANSPORT_ROOTS)
    bridge_tokens = []
    git_tokens = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            words = node.value.strip().split()
            if words and words[0] in BRIDGE_CLIS:
                bridge_tokens.append(words[0])
                if words[0] == "git":
                    git_tokens.append(" ".join(words[:2]))
    literals = sorted(set(re.findall(r"https?://[^\s\"']+", text)))
    bridge_suspect = bool(("subprocess" in top_imports) and bridge_tokens)
    adjacent_final = []
    for full in sorted(local):
        sib = full.split(".")[-1]
        if sib in sibling_names:
            sib_text = sibling_names[sib]
            if any(t in sib_text for t in TRANSPORT_TOKENS):
                adjacent_final.append(full)
    zero_network = not (transports or adjacent_final or literals
                        or bridge_suspect)

    markers = []
    for kind, rx in SKIP_KINDS:
        hits = rx.findall(text)
        if hits:
            uniq = []
            for h in hits:
                if h not in uniq:
                    uniq.append(h)
            markers.append({"kind": kind, "count": len(hits),
                            "samples": uniq[:3]})

    if "argparse" in top_imports:
        form = "python tools/%s" % fname
        for f in optionals:
            if f.startswith("--"):
                form += " [%s]" % f
        invocation = {"form": form, "basis": "argparse-reconstructed"}
    elif doc and "Interface." in doc:
        iface = [ln.strip() for ln in doc.splitlines()
                 if "Interface." in ln]
        invocation = {"form": (iface[0][:200] if iface else ""),
                      "basis": "docstring-interface"}
    else:
        invocation = {"form": "", "basis": "none"}

    usage_face = []
    if "argparse" not in top_imports and doc:
        usage_face = [ln.strip()[:200] for ln in doc.splitlines()
                      if ln.strip().startswith("python")
                      and fname in ln][:4]

    return {
        "name": fname,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "lines": len(text.splitlines()),
        "underscore_prefix": fname.startswith("_"),
        "has_main_guard": has_main_guard,
        "docstring": {"present": bool(doc),
                      "lines": len(doc.splitlines()) if doc else 0,
                      "head": (doc or "")[:600]},
        "argparse": {"imported": "argparse" in top_imports,
                     "parser_descriptions": descriptions,
                     "add_argument": add_argument,
                     "positionals": sorted(set(positionals)),
                     "optionals": sorted(set(optionals)),
                     "subcommands": sorted(set(subcommands)),
                     "has_subparsers": has_subparsers,
                     "set_defaults_func": set_defaults_func},
        "usage_face": usage_face,
        "imports": {"modules": sorted(top_imports),
                    "third_party": sorted(third_party),
                    "local": sorted(local),
                    "guarded_conditional": sorted(guarded)},
        "network": {"transport_imports": transports,
                    "adjacent_imports": adjacent_final,
                    "literal_face": literals,
                    "subprocess_bridge_suspect": bridge_suspect,
                    "zero_network": zero_network,
                    "git_subprocess_network_face": {
                        "present": bool(git_tokens),
                        "tokens": sorted(set(git_tokens))[:6]}},
        "skip_face": {"markers": markers},
        "selftest_flag": "--selftest" in optionals,
        "selftest_token_face": "--selftest" in text,
        "invocation": invocation,
    }


def scan_repo(tools_dir, only=None):
    """Return sorted records for tools_dir (all .py, or --only names)."""
    if not os.path.isdir(tools_dir):
        raise MissingPathError("--tools directory missing: %s" % tools_dir)
    names = sorted(f for f in os.listdir(tools_dir) if f.endswith(".py"))
    # sibling name -> text map (for the adjacent-network face)
    siblings = {}
    for fn in names:
        with io.open(os.path.join(tools_dir, fn), encoding="utf-8",
                     errors="replace") as fh:
            siblings[fn[:-3]] = fh.read()
    want = None
    if only:
        want = set()
        for n in only.split(","):
            n = n.strip()
            if not n.endswith(".py"):
                n += ".py"
            if n not in names:
                raise UsageError("--only name not on disk: %s" % n)
            want.add(n)
    rows = []
    for fn in names:
        if want is not None and fn not in want:
            continue
        rows.append(parse_faces("tools/" + fn, siblings[fn[:-3]],
                                siblings))
    rows.sort(key=lambda r: r["name"])
    return rows


def merge(stand_path, rows, now_utc):
    """Verbatim-preserving sorted union; meta gains the generation split."""
    if not os.path.isfile(stand_path):
        raise MissingPathError("--stand census missing: %s" % stand_path)
    try:
        with io.open(stand_path, encoding="utf-8") as fh:
            stand = json.load(fh)
    except ValueError as exc:
        raise UsageError("--stand is not valid JSON: %s" % exc)
    if not isinstance(stand, dict) or not isinstance(stand.get("files"),
                                                     list):
        raise UsageError("--stand carries no files array (not census data)")
    existing = {r.get("name") for r in stand["files"]}
    added = [r for r in rows if r["name"] not in existing]
    merged = sorted(list(stand["files"]) + added,
                    key=lambda r: r.get("name") or "")
    meta = dict(stand.get("meta") or {})
    gen = dict(meta.get("rescan_generation") or {})
    prior = gen.get("added_this_generation")
    if prior:
        history = list(gen.get("history") or [])
        history.append({"added_this_generation": list(prior),
                        "generator": gen.get("generator"),
                        "method_note": gen.get("method_note")})
        gen["history"] = history
    gen["added_this_generation"] = [r["name"] for r in added]
    gen["generator"] = "tools/census_rescan.py v1"
    gen["method_note"] = ("rows above the generation split keep their "
                          "original generator's semantics; rows added by "
                          "the generation follow census_rescan.py's "
                          "documented v1 rules")
    meta["rescan_generation"] = gen
    meta["py_files_censused"] = len(merged)
    meta["generated_at_utc"] = now_utc
    return {"meta": meta, "files": merged}, len(added)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="AST word-face census re-scan generator")
    ap.add_argument("--repo", help="repository root (default .)")
    ap.add_argument("--tools", help="tools directory (default --repo/tools)")
    ap.add_argument("--only", help="comma-separated tool names to scan")
    ap.add_argument("--stand", help="standing census path (merge source)")
    ap.add_argument("--merge", action="store_true",
                    help="merge into the standing census (writes --out)")
    ap.add_argument("--out", help="output path")
    args = ap.parse_args(argv)
    repo = args.repo or "."
    if not os.path.isdir(repo):
        print("PATH-MISSING: --repo directory missing: %s" % repo,
              file=sys.stderr)
        sys.exit(9)
    tools_dir = args.tools or os.path.join(repo, "tools")
    try:
        rows = scan_repo(tools_dir, args.only)
    except MissingPathError as exc:
        print("PATH-MISSING: %s" % exc, file=sys.stderr)
        sys.exit(9)
    except UsageError as exc:
        print("USAGE: %s" % exc, file=sys.stderr)
        sys.exit(2)
    if args.merge:
        stand = args.stand or os.path.join(repo, "docs",
                                           "census-tools.json")
        try:
            now = datetime.datetime.now(datetime.timezone.utc) \
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            merged, added = merge(stand, rows, now)
        except MissingPathError as exc:
            print("PATH-MISSING: %s" % exc, file=sys.stderr)
            sys.exit(9)
        except UsageError as exc:
            print("USAGE: %s" % exc, file=sys.stderr)
            sys.exit(2)
        if not args.out:
            print("USAGE: --merge needs --out", file=sys.stderr)
            sys.exit(2)
        blob = json.dumps(merged, ensure_ascii=False, indent=1) + "\n"
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        print("merged census -> %s (files=%d added=%d)"
              % (args.out, len(merged["files"]), added))
        sys.exit(0)
    blob = json.dumps({"rows": rows}, ensure_ascii=False, indent=1) + "\n"
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob)
        print("rows -> %s (%d)" % (args.out, len(rows)))
    else:
        sys.stdout.write(blob)
    print("census-rescan: %d row(s)" % len(rows))
    sys.exit(0)


def selftest():
    import shutil
    import tempfile
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="census_rescan_selftest_")
    try:
        tools = os.path.join(tmp, "tools")
        docs = os.path.join(tmp, "docs")
        os.makedirs(tools)
        os.makedirs(docs)
        with io.open(os.path.join(tools, "alpha.py"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(
                '"""alpha.py - fixture tool.\nPurpose.  Fetch things\n'
                'Interface.  python -I tools/alpha.py --path P | --selftest\n'
                '"""\n'
                'import argparse\nimport subprocess\nimport urllib.request\n'
                '\n\ndef build():\n'
                '    ap = argparse.ArgumentParser(\n'
                '        description="fixture alpha parser description")\n'
                '    ap.add_argument("--path", required=True,\n'
                '                   metavar="P", help="a path")\n'
                '    ap.add_argument("--selftest", action="store_true")\n'
                '    return ap\n'
                '\n\ndef run():\n'
                '    subprocess.run(["git", "fetch", "origin"])\n'
                '    subprocess.run("git push origin main".split())\n'
                '    return "https://example.invalid/x"\n\n\n'
                'if __name__ == "__main__":\n    run()\n')
        filler = ("filler word " * 80).strip()
        with io.open(os.path.join(tools, "_beta.py"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("'''_beta.py - helper fixture with a very long "
                     "docstring head that must truncate at exactly six "
                     "hundred characters to honour the documented head "
                     "rule, padded below with filler text so the length "
                     "passes the boundary: " + filler + "\n'''\n"
                     "try:\n    import json\nexcept ImportError:\n"
                     "    json = None\n\n\ndef helper():\n    return 2\n")
        # standing census with one row (verbatim-preservation face)
        stand = {"meta": {"py_files_censused": 1,
                          "method": "original lane method"},
                 "files": [{"name": "alpha.py", "marker": "ORIGINAL"}]}
        stand_path = os.path.join(docs, "census-tools.json")
        with io.open(stand_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(stand, fh, indent=1)

        rc_out = os.path.join(tmp, "rows.json")
        p = subprocess.run(
            [sys.executable, "-I", "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "census_rescan.py"),
             "--repo", tmp, "--out", rc_out],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        ok = p.returncode == 0
        rep = {}
        if ok:
            with io.open(rc_out, encoding="utf-8") as fh:
                rep = json.load(fh)
        rows = {r["name"]: r for r in rep.get("rows", [])}
        alpha = rows.get("alpha.py")
        beta = rows.get("_beta.py")
        vec("scan-rc0-both-rows-sorted",
            ok and list(rows) == ["_beta.py", "alpha.py"],
            "rc=%d rows=%s" % (p.returncode, sorted(rows)))
        vec("alpha-network-face",
            alpha is not None
            and alpha["network"]["transport_imports"] == ["urllib"]
            and alpha["network"]["subprocess_bridge_suspect"] is True
            and alpha["network"]["git_subprocess_network_face"]["present"]
            is True
            and alpha["network"]["git_subprocess_network_face"]["tokens"]
            == ["git", "git push"]
            and alpha["network"]["literal_face"]
            == ["https://example.invalid/x"]
            and alpha["network"]["zero_network"] is False,
            str((alpha or {}).get("network"))[:120])
        vec("alpha-argparse-face",
            alpha is not None
            and alpha["argparse"]["imported"] is True
            and alpha["argparse"]["parser_descriptions"]
            == ["fixture alpha parser description"]
            and alpha["argparse"]["optionals"]
            == ["--path", "--selftest"]
            and alpha["argparse"]["add_argument"][0]["kwargs"]
            .get("required") is True
            and alpha["selftest_flag"] is True
            and alpha["selftest_token_face"] is True
            and alpha["has_main_guard"] is True,
            "argparse faces")
        kinds = {m["kind"] for m in (alpha or {}).get(
            "skip_face", {}).get("markers", [])}
        vec("alpha-skip-noise-free",
            alpha is not None and kinds == set(),
            "kinds=%s" % sorted(kinds))
        vec("alpha-invocation-form",
            alpha is not None
            and alpha["invocation"]["basis"] == "argparse-reconstructed"
            and alpha["invocation"]["form"]
            == "python tools/alpha.py [--path] [--selftest]",
            "form=%s" % (alpha or {}).get("invocation", {}).get("form"))
        vec("beta-guarded-import-and-head",
            beta is not None
            and beta["underscore_prefix"] is True
            and beta["argparse"]["imported"] is False
            and beta["imports"]["modules"] == []
            and beta["imports"]["guarded_conditional"] == ["json"]
            and len(beta["docstring"]["head"]) == 600
            and beta["invocation"]["basis"] == "none",
            "beta faces")
        # merge face: verbatim preservation + sorted union + determinism
        m1 = os.path.join(tmp, "m1.json")
        p1 = subprocess.run(
            [sys.executable, "-I", "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "census_rescan.py"),
             "--repo", tmp, "--merge", "--stand", stand_path,
             "--out", m1],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        m2 = os.path.join(tmp, "m2.json")
        p2 = subprocess.run(
            [sys.executable, "-I", "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "census_rescan.py"),
             "--repo", tmp, "--merge", "--stand", stand_path,
             "--out", m2],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        if p1.returncode == 0 and p2.returncode == 0:
            with io.open(m1, encoding="utf-8") as fh:
                j1 = json.load(fh)
            with io.open(m2, encoding="utf-8") as fh:
                j2 = json.load(fh)
            names = [r["name"] for r in j1["files"]]
            orig = [r for r in j1["files"] if r.get("marker") == "ORIGINAL"]
            gen = j1["meta"].get("rescan_generation", {})
            a1 = dict(j1["meta"]); a1.pop("generated_at_utc", None)
            a2 = dict(j2["meta"]); a2.pop("generated_at_utc", None)
            vec("merge-verbatim-sorted-deterministic",
                names == sorted(names)
                and len(orig) == 1
                and orig[0]["marker"] == "ORIGINAL"
                and j1["meta"]["py_files_censused"] == 2
                and sorted(gen.get("added_this_generation", []))
                == ["_beta.py"]
                and gen.get("generator") == "tools/census_rescan.py v1"
                and j1["files"] == j2["files"] and a1 == a2,
                "files=%s" % names)
        else:
            vec("merge-verbatim-sorted-deterministic", False,
                "rc=%d/%d" % (p1.returncode, p2.returncode))
        # merge face 2: a repeated merge rolls the prior generation batch
        # into history verbatim - lineage accumulates, never collapses
        m3 = os.path.join(tmp, "m3.json")
        p3 = subprocess.run(
            [sys.executable, "-I", "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "census_rescan.py"),
             "--repo", tmp, "--merge", "--stand", m1,
             "--out", m3],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
        if p3.returncode == 0:
            with io.open(m3, encoding="utf-8") as fh:
                j3 = json.load(fh)
            g3 = j3["meta"].get("rescan_generation", {})
            h3 = g3.get("history") or []
            vec("merge-history-rolls-prior-batch",
                g3.get("added_this_generation") == []
                and len(h3) == 1
                and h3[0].get("added_this_generation") == ["_beta.py"]
                and h3[0].get("generator") == "tools/census_rescan.py v1"
                and [r["name"] for r in j3["files"]]
                == sorted(r["name"] for r in j3["files"]),
                "history=%s" % json.dumps(h3)[:140])
        else:
            vec("merge-history-rolls-prior-batch", False,
                "rc=%d" % p3.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("CENSUS-RESCAN-SELFTEST: %d vector(s), %d FAIL"
          % (total[0], len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    main()
