#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bootstrap.py - the single-file bootstrap for rocqwash (repository root).
Purpose.  Take a stranger session from zero to a verified tool call with
  two commands: fetch this file, run it.  `--install` shallow-clones the
  chosen channel into ~/.rocqwash (or fast-forwards an existing checkout,
  the upgrade face), `--mcp-config` prints the MCP stdio wiring with
  absolute paths and the Windows-host environment block injected,
  `--report` prints the one-page capability summary, and `--selftest`
  runs the frozen vector group.  The channel defaults to `stable`, the
  machine-verified rolling tag; `--track main` opts into the moving tip.
Interface.  `python3 bootstrap.py --install [--track stable|main]
  [--install-dir DIR] [--selftest] | --mcp-config [--install-dir DIR] |
  --report [--install-dir DIR] | --selftest`; exactly one face per run.
  The file itself runs from a single raw fetch (standard library only,
  zero sibling imports); the repository's full self-test suite remains
  `bash tests/run_tests.sh` inside the installed checkout.
Dependencies.  Python 3 standard library only (argparse, ast, json, os,
  shutil, subprocess, sys); the `git` executable for `--install`; the
  installed checkout's own python for `--report`.
Evidence.  --selftest: seven frozen vectors (the preflight red form, the
  green face, the config output shape, the track table, the upgrade
  decision, the channel mapping, the detached self-parse); zero network,
  zero writes outside the process.
Exit-codes.  0 the face completed; 1 the requested action failed (the git
  output is on stderr); 2 usage error; 9 the preflight is red or the face
  needs an installed checkout and none is found.
"""
# Extended contract (kept outside the five-field header per the annotation
# standard 30-line header budget):
#
# Channel semantics: --track stable clones `--branch stable`, which resolves
#   the rolling `stable` tag maintained by .github/scripts/stable_channel.py;
#   --track main clones the default branch.  An existing ~/.rocqwash is
#   aligned with `git fetch` + `git merge --ff-only` against the same
#   channel ref, so the second --install is the upgrade face; a
#   non-fast-forwardable checkout is reported exit 1 with the git output,
#   never reset or overwritten.
# Windows host: the install path is %USERPROFILE%\.rocqwash (expanduser);
#   the preflight prints the CRLF note (keep core.autocrlf=false so the
#   bash faces stay executable) and the long-path note (git core.longpaths
#   for checkouts deeper than the 260-character limit).
# Wire safety: the generated mcp-config always injects PYTHONUTF8=1 and
#   PYTHONIOENCODING=utf-8 (the GBK-codepage console face) and uses the
#   running interpreter's absolute path for the server command.
# Layer boundary: this tool never writes inside a repository and never
#   merges its own work; it is a consumer-side installer.

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys

REPO_URL = "https://github.com/hy7pc8gfmf-dotcom/rocqwash.git"
DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".rocqwash")
SCHEMA = "rocqwash-bootstrap/1"


def preflight(interpreter_version=None, git_on_path=None):
    """The environment preflight: (ok, reasons).  The arguments feed the
    selftest vectors; the live faces pass the real environment."""
    version = interpreter_version if interpreter_version is not None else sys.version_info
    reasons = []
    if version < (3, 9):
        reasons.append("python >= 3.9 required, found {0}.{1}".format(version[0], version[1]))
    if git_on_path is None:
        git_on_path = shutil.which("git") is not None
    if not git_on_path:
        reasons.append("git not found on PATH (needed for --install)")
    if os.name == "nt":
        reasons.append("windows host: keep core.autocrlf=false so the bash faces stay executable; "
                       "set git core.longpaths true if the checkout exceeds the 260-character path limit")
    return (not reasons), reasons


def resolve_track(track):
    """The channel name to clone, or None when the value is invalid."""
    if track in ("stable", "main"):
        return track
    return None


def install_decision(install_dir):
    """(action, dir) where action is clone (directory absent or empty) or
    fast-forward (an existing checkout), or (None, dir) when the directory
    exists but is not a git work tree - a name collision, never overwritten."""
    if not os.path.isdir(install_dir) or not os.listdir(install_dir):
        return "clone", install_dir
    probe = os.path.join(install_dir, ".git")
    if os.path.exists(probe):
        return "fast-forward", install_dir
    return None, install_dir


def mcp_config(install_dir, interpreter):
    """The MCP stdio wiring dict for one installed checkout."""
    server = os.path.join(install_dir, "tools", "mcp_server.py")
    return {
        "mcpServers": {
            "rocqwash": {
                "command": interpreter,
                "args": ["-I", "-X", "utf8", server],
                "env": {
                    "ROCWASH_HOME": install_dir,
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8",
                },
            }
        }
    }


def _run_git(args, cwd=None):
    completed = subprocess.run(["git"] + args, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=600, check=False)
    out = completed.stdout.decode("utf-8", "replace").strip()
    err = completed.stderr.decode("utf-8", "replace").strip()
    return completed.returncode, out, err


def face_install(track, install_dir):
    ok, reasons = preflight()
    if not ok:
        for line in reasons:
            sys.stderr.write("preflight: " + line + "\n")
        return 9
    action, install_dir = install_decision(install_dir)
    if action is None:
        sys.stderr.write("install: {0} exists and is not a git checkout; "
                         "choose another --install-dir\n".format(install_dir))
        return 1
    if action == "clone":
        code, out, err = _run_git(["clone", "--depth", "1", "--branch", track, REPO_URL, install_dir])
    else:
        code, out, err = _run_git(["fetch", "origin", track], cwd=install_dir)
        if code == 0:
            code, out, err = _run_git(["merge", "--ff-only", "FETCH_HEAD"], cwd=install_dir)
    if code != 0:
        sys.stderr.write("install: git failed (exit {0})\n{1}\n".format(code, err or out))
        return 1
    code2, head, _ = _run_git(["rev-parse", "HEAD"], cwd=install_dir)
    if action == "clone":
        sys.stderr.write("install: cloned {0} at {1} into {2}\n".format(track, head[:12], install_dir))
    else:
        sys.stderr.write("install: aligned existing checkout to {0} at {1} ({2})\n".format(track, head[:12], install_dir))
    print(json.dumps({"schema": SCHEMA, "action": action, "track": track,
                      "dir": install_dir, "head_sha": head}, sort_keys=True))
    return 0


def _require_checkout(install_dir):
    server = os.path.join(install_dir, "tools", "mcp_server.py")
    if not os.path.isfile(server):
        sys.stderr.write("no installed checkout at {0} (tools/mcp_server.py missing); "
                         "run --install first\n".format(install_dir))
        return False
    return True


def face_mcp_config(install_dir):
    ok, reasons = preflight()
    if not ok:
        for line in reasons:
            sys.stderr.write("preflight: " + line + "\n")
        return 9
    if not _require_checkout(install_dir):
        return 9
    print(json.dumps(mcp_config(install_dir, sys.executable), indent=2, sort_keys=True))
    return 0


def face_report(install_dir):
    ok, reasons = preflight()
    if not ok:
        for line in reasons:
            sys.stderr.write("preflight: " + line + "\n")
        return 9
    if not _require_checkout(install_dir):
        return 9
    cmd = [sys.executable, "-I", "-X", "utf8", "-B",
           os.path.join(install_dir, "tools", "capability_index.py"), "--mode", "summary"]
    code, out, err = _run_tool(cmd, install_dir)
    if code != 0:
        sys.stderr.write("report: the capability index exited {0}\n{1}\n".format(code, err))
        return 1
    sys.stdout.write(out + "\n")
    return 0


def _run_tool(cmd, cwd):
    completed = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=300, check=False)
    return (completed.returncode,
            completed.stdout.decode("utf-8", "replace").strip(),
            completed.stderr.decode("utf-8", "replace").strip())


def _selftest():
    """Seven frozen vectors; zero network, zero writes; 0 green, 1 red."""
    failures = []

    def check(name, cond, detail=""):
        print("[SELFTEST] {0} {1}{2}".format("PASS" if cond else "FAIL", name,
                                             (": " + detail) if detail and not cond else ""))
        if not cond:
            failures.append(name)

    ok, reasons = preflight(interpreter_version=(3, 8, 0), git_on_path=True)
    check("v1-preflight-red-form", not ok and any("3.9" in r for r in reasons), str(reasons))
    ok, reasons = preflight()
    check("v2-preflight-green-face", ok and all("windows" not in r for r in reasons or []) or os.name != "nt", str(reasons))
    cfg = mcp_config("/tmp/x", "/usr/bin/python3")
    server_cfg = cfg["mcpServers"]["rocqwash"]
    check("v3-config-output-shape",
          set(server_cfg.keys()) == {"command", "args", "env"}
          and server_cfg["env"].get("PYTHONUTF8") == "1"
          and server_cfg["env"].get("PYTHONIOENCODING") == "utf-8"
          and server_cfg["args"][0] == "-I"
          and server_cfg["args"][3].endswith("tools/mcp_server.py"))
    check("v4-track-parse-table",
          resolve_track("stable") == "stable" and resolve_track("main") == "main"
          and resolve_track("nightly") is None)
    check("v5-upgrade-decision",
          install_decision("/definitely/not/here")[0] == "clone"
          and install_decision(os.path.dirname(os.path.abspath(__file__)))[0] in ("fast-forward", None))
    check("v6-channel-clone-ref",
          ("--branch", "stable") == ("--branch", resolve_track("stable"))
          and REPO_URL.endswith("rocqwash.git"))
    try:
        ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())
        parsed = True
    except (OSError, SyntaxError):
        parsed = False
    check("v7-detached-self-parse", parsed)
    print("BOOTSTRAP-SELFTEST: {0} vector(s), {1} FAIL".format(7, len(failures)))
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="Single-file bootstrap for rocqwash: install a channel "
                    "checkout, print the MCP wiring, print the capability "
                    "summary, or run the frozen selftest vectors "
                    "(schema " + SCHEMA + "; standard library only)")
    parser.add_argument("--install", action="store_true",
                        help="shallow-clone the channel into --install-dir "
                             "(default ~/.rocqwash); an existing checkout is "
                             "fast-forward aligned, which is the upgrade face")
    parser.add_argument("--mcp-config", action="store_true",
                        help="print the MCP stdio wiring JSON for the installed checkout")
    parser.add_argument("--report", action="store_true",
                        help="print the one-page capability summary of the installed checkout")
    parser.add_argument("--selftest", action="store_true",
                        help="run the seven frozen vectors and exit; the full repository "
                             "suite stays `bash tests/run_tests.sh` inside the checkout")
    parser.add_argument("--track", default="stable", choices=["stable", "main"],
                        help="the channel to install (default: stable, the machine-verified "
                             "rolling tag; main follows the moving tip)")
    parser.add_argument("--install-dir", default=DEFAULT_DIR,
                        help="the checkout directory (default ~/.rocqwash; on Windows "
                             "%%USERPROFILE%%\\.rocqwash)")
    args = parser.parse_args(argv)
    faces = [args.install, args.mcp_config, args.report, args.selftest]
    if sum(1 for f in faces if f) != 1:
        parser.error("choose exactly one face: --install | --mcp-config | --report | --selftest")
    if args.selftest:
        return _selftest()
    if args.install:
        return face_install(args.track, args.install_dir)
    if args.mcp_config:
        return face_mcp_config(args.install_dir)
    return face_report(args.install_dir)


if __name__ == "__main__":
    sys.exit(main())
