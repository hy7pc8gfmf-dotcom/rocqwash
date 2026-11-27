#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repo_sync_status.py - local repository sync offset reader (rocqwash tools/).
Purpose.  One read-only offset measurement of the working repository against
  the last fetched remote main ref: how many commits the local HEAD is ahead
  of and behind `refs/remotes/origin/main`, whether the two agree, and the
  HEAD/tag identity of the measured tree - the staleness face a remote
  consumer needs before trusting this checkout's answers.  Every field is a
  `{value, basis}` pair; a measurement that cannot be taken is exit 9 with
  the reason, never a guessed zero.
Interface.  `python -I tools/repo_sync_status.py [--repo DIR] [--json OUT] |
  --selftest`; the default face prints one compact JSON report object
  (schema `rocqwash-repo-sync-status/1`) to stdout and exits 0; `--json OUT`
  writes the same object to the named path.
Dependencies.  Python 3 standard library only; the `git` executable must be
  on PATH (three local git calls per measurement; zero network - the origin
  side of the comparison is the last fetched `refs/remotes/origin/main`,
  never a live remote query; zero writes inside --repo).
Evidence.  --selftest runs six frozen vectors: the three offset states
  (up-to-date, ahead, behind) on temporary git fixtures built in a private
  temporary directory, the unknown-origin and not-a-repository refusal
  forms (exit 9 with the named reason), and the report schema closed key
  set; zero network, zero writes outside the temporary directory.
Exit-codes.  0 measured (every offset state is data, including up-to-date);
  2 usage error (unknown flag); 9 not measurable (not a git work tree, or
  no fetched origin/main ref - the stderr reason names which).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "rocqwash-repo-sync-status/1"
ORIGIN_REF = "refs/remotes/origin/main"
GIT_TIMEOUT_S = 30


def _field(value, basis):
    """One measured field: the value and where it came from."""
    return {"value": value, "basis": basis}


def _git(repo, *args):
    """One local git call; (stdout strip, "") on success, (None, stderr) on
    any failure - a missing git executable and a git error are the same
    honest None to the caller."""
    try:
        completed = subprocess.run(
            ["git", "-C", repo] + list(args),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "git call failed to run: {0}".format(exc)
    if completed.returncode != 0:
        return None, completed.stderr.decode("utf-8", "replace").strip()
    return completed.stdout.decode("utf-8", "replace").strip(), ""


def measure(repo):
    """The sync report, or (None, reason) when the offset cannot be taken."""
    head, err = _git(repo, "rev-parse", "HEAD")
    if head is None:
        return None, (
            "not measurable: git rev-parse HEAD failed at {0} ({1}) - the path "
            "is not a git work tree, or git is unavailable".format(repo, err or "no output")
        )
    origin, oerr = _git(repo, "rev-parse", "--verify", ORIGIN_REF)
    if origin is None:
        return None, (
            "not measurable: {0} does not resolve at {1} ({2}) - fetch the "
            "remote first; the offset face never queries the network"
            .format(ORIGIN_REF, repo, oerr or "unresolved")
        )
    counts, cerr = _git(repo, "rev-list", "--left-right", "--count",
                        "HEAD...{0}".format(ORIGIN_REF))
    if counts is None or len(counts.split()) != 2:
        return None, "not measurable: the offset count failed ({0})".format(cerr or counts)
    ahead_s, behind_s = counts.split()
    ahead, behind = int(ahead_s), int(behind_s)
    tag, _ = _git(repo, "describe", "--tags", "--exact-match", "HEAD")
    tag_basis = "git describe --tags --exact-match HEAD"
    if not tag:
        tag_basis += "; no tag names this commit"
    return {
        "schema": SCHEMA,
        "repo": _field(os.path.abspath(repo), "the measured repository root"),
        "head_sha": _field(head, "git rev-parse HEAD"),
        "tag": _field(tag or "", tag_basis),
        "origin_ref": _field(ORIGIN_REF,
                             "the last fetched remote state; a re-fetch refreshes it, "
                             "the measurement itself stays local"),
        "origin_sha": _field(origin, "git rev-parse --verify {0}".format(ORIGIN_REF)),
        "ahead": _field(ahead, "git rev-list --left-right --count HEAD...{0}".format(ORIGIN_REF)),
        "behind": _field(behind, "git rev-list --left-right --count HEAD...{0}".format(ORIGIN_REF)),
        "up_to_date": _field(ahead == 0 and behind == 0,
                             "ahead == 0 and behind == 0 against the last fetched origin/main"),
    }, ""


def _fixture(source_root, name):
    """A private temporary fixture directory under one caller-made root."""
    path = os.path.join(source_root, name)
    os.makedirs(path)
    return path


def _run(args, cwd):
    completed = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=GIT_TIMEOUT_S, check=False)
    return completed.returncode, completed.stdout.decode("utf-8", "replace"), \
        completed.stderr.decode("utf-8", "replace")


def _init_main(path):
    """git init with an explicit main branch, version-tolerant."""
    rc, _, _ = _run(["git", "init", "-q"], path)
    if rc != 0:
        return rc
    return _run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], path)[0]


def _selftest():
    """Six frozen vectors on private temporary fixtures; 0 green, 1 red."""
    failures = []

    def check(name, cond, detail=""):
        print("[SELFTEST] {0} {1}{2}".format("PASS" if cond else "FAIL", name,
                                             (": " + detail) if detail and not cond else ""))
        if not cond:
            failures.append(name)

    root = tempfile.mkdtemp(prefix="repo-sync-selftest-")
    try:
        origin = _fixture(root, "origin")
        _run(["git", "init", "-q", "--bare"], origin)
        _run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], origin)
        work = _fixture(root, "work")
        _init_main(work)
        _run(["git", "remote", "add", "origin", origin], work)
        with open(os.path.join(work, "f.txt"), "w") as handle:
            handle.write("one\n")
        _run(["git", "add", "f.txt"], work)
        _run(["git", "-c", "user.email=t@local", "-c", "user.name=t",
              "commit", "-q", "-m", "one"], work)
        _run(["git", "push", "-q", "-u", "origin", "main"], work)

        # V1 up-to-date: HEAD equals the fetched origin/main.
        report, reason = measure(work)
        report_ok = report
        check("v1-up-to-date", bool(report) and report["ahead"]["value"] == 0
              and report["behind"]["value"] == 0
              and report["up_to_date"]["value"] is True, reason)

        # V2 ahead: one local commit the fetched ref lacks.
        with open(os.path.join(work, "f.txt"), "a") as handle:
            handle.write("two\n")
        _run(["git", "add", "f.txt"], work)
        _run(["git", "-c", "user.email=t@local", "-c", "user.name=t",
              "commit", "-q", "-m", "two"], work)
        report, reason = measure(work)
        check("v2-ahead", bool(report) and report["ahead"]["value"] == 1
              and report["behind"]["value"] == 0
              and report["up_to_date"]["value"] is False, reason)

        # V3 behind: the fetched ref advances past the local HEAD.
        _run(["git", "push", "-q", "origin", "main"], work)
        _run(["git", "reset", "-q", "--hard", "HEAD~1"], work)
        report, reason = measure(work)
        check("v3-behind", bool(report) and report["ahead"]["value"] == 0
              and report["behind"]["value"] == 1
              and report["up_to_date"]["value"] is False, reason)

        # V4 unknown origin: a repository with no fetched origin/main.
        bare = _fixture(root, "bare")
        _init_main(bare)
        _run(["git", "-c", "user.email=t@local", "-c", "user.name=t",
              "commit", "-q", "--allow-empty", "-m", "one"], bare)
        report, reason = measure(bare)
        check("v4-unknown-origin", report is None and "origin/main" in reason, reason)

        # V5 not a repository: a plain directory.
        plain = _fixture(root, "plain")
        report, reason = measure(plain)
        check("v5-not-a-repo", report is None and "not measurable" in reason, reason)

        # V6 report schema closed key set (the V1 measurement).
        expected = {"schema", "repo", "head_sha", "tag", "origin_ref",
                    "origin_sha", "ahead", "behind", "up_to_date"}
        check("v6-schema-closed-set", bool(report_ok) and set(report_ok.keys()) == expected,
              "keys={0}".format(sorted(report_ok.keys()) if report_ok else None))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("REPO-SYNC-STATUS-SELFTEST: {0} vector(s), {1} FAIL".format(
        6, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    parser = argparse.ArgumentParser(
        prog="repo_sync_status",
        description="Local repository sync offset reader (schema "
                    + SCHEMA + "; zero network; the origin side is the last "
                    "fetched refs/remotes/origin/main)")
    parser.add_argument("--repo", default=".",
                        help="repository root to measure (default: the working directory)")
    parser.add_argument("--json", default=None, metavar="OUT",
                        help="write the report JSON object to this path")
    args = parser.parse_args()
    report, reason = measure(args.repo)
    if report is None:
        sys.stderr.write(reason + "\n")
        sys.exit(9)
    text = json.dumps(report, ensure_ascii=False, sort_keys=True)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    sys.exit(0)
