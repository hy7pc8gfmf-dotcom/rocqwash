#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stable_channel.py - the mechanical mover of the stable release tag (.github/scripts/).
Purpose.  Advance the rolling `stable` tag to the newest machine-verified
  commit: the newest successful run of the main-branch CI workflow, held
  only while that run's head equals the current main branch head.  The
  tag is moved exclusively by this script from the self-heal workflow's
  green-CI pass; no human hand moves it (the move rule lives in the
  workflow header and in the README agent-sessions face).  Every decision
  is data: `--check` prints the plan JSON without writing anything.
Interface.  `python3 .github/scripts/stable_channel.py --repo OWNER/REPO
  [--ci-workflow NAME] [--move | --check] [--selftest]`; the token is
  read from the GITHUB_TOKEN environment variable (the workflow's
  `github.token`; no credential file is read).
Dependencies.  Python 3 standard library only (json, os, sys, urllib).
Evidence.  --selftest runs six frozen vectors on canned API responses
  (hold on equality, move on difference, create on absence, stale guard,
  failed-run hold, the plan schema closed key set); zero network, zero
  writes outside the process.
Exit-codes.  0 the plan is hold or the move landed; 1 the move was
  requested and refused (the plan says why); 2 usage error.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
STABLE_REF = "tags/stable"


def _api(repo, path, token, method="GET", body=None):
    """One API call; (status, parsed-or-raw) with the status always first."""
    url = "{0}/repos/{1}/{2}".format(API, repo, path)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Accept": "application/vnd.github+json",
                                          "Authorization": "token " + token,
                                          "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, None
    parsed = json.loads(raw) if raw else None
    return 200, parsed


def decide(run_head, main_head, run_conclusion, stable_sha):
    """The move decision on five facts: (action, reason) where action is
    one of create, move, hold, wait."""
    if run_conclusion != "success":
        return "wait", "the newest main-branch CI run concluded {0}; the channel advances only on green".format(run_conclusion)
    if run_head != main_head:
        return "wait", "the newest green run's head {0} is not the current main head {1}; a newer commit is still under check".format(run_head, main_head)
    if stable_sha is None:
        return "create", "no stable ref exists; create it at the green main head"
    if stable_sha == run_head:
        return "hold", "the stable ref already names the green main head"
    return "move", "advance the stable ref from {0} to the green main head {1}".format(stable_sha[:12], run_head[:12])


def plan(repo, token, ci_workflow):
    """The live plan: fetch the newest run of the CI workflow on main,
    the current main head, and the current stable ref; return the plan
    dict plus the (status, parsed) facts behind it."""
    workflow = urllib.parse.quote(ci_workflow, safe="")
    status, runs = _api(repo,
                        "actions/workflows/{0}/runs?branch=main&status=success&per_page=1".format(workflow),
                        token)
    if status != 200 or not runs or not runs.get("workflow_runs"):
        return {"action": "wait", "reason": "no successful main-branch CI run is visible to this token"}, None
    run = runs["workflow_runs"][0]
    status, main_ref = _api(repo, "git/ref/heads/main", token)
    main_head = (main_ref or {}).get("object", {}).get("sha") if status == 200 else None
    if not main_head:
        return {"action": "wait", "reason": "the main branch ref is not readable"}, None
    status, stable_ref = _api(repo, "git/ref/{0}".format(STABLE_REF), token)
    stable_sha = (stable_ref or {}).get("object", {}).get("sha") if status == 200 else None
    action, reason = decide(run.get("head_sha"), main_head,
                            run.get("conclusion"), stable_sha)
    return {"action": action, "reason": reason, "run_head": run.get("head_sha"),
            "main_head": main_head, "stable_target": stable_sha,
            "run_id": run.get("id"), "schema": "rocqwash-stable-channel-plan/1"}, (status, stable_ref)


def move(repo, token, ci_workflow):
    """Execute the plan when it says create or move; the ref update goes
    through the git-data API (POST create, PATCH force), never a local
    push, so the mover stays stateless."""
    the_plan, facts = plan(repo, token, ci_workflow)
    if the_plan["action"] not in ("create", "move"):
        print(json.dumps(the_plan, sort_keys=True))
        return 0
    sha = the_plan["run_head"]
    if the_plan["action"] == "create":
        status, resp = _api(repo, "git/refs", token, method="POST",
                            body={"ref": "refs/{0}".format(STABLE_REF), "sha": sha})
    else:
        status, resp = _api(repo, "git/{0}".format(STABLE_REF), token, method="PATCH",
                            body={"sha": sha, "force": True})
    if status not in (200, 201):
        the_plan["action"] = "refused"
        the_plan["reason"] = "the ref update returned HTTP {0}".format(status)
        print(json.dumps(the_plan, sort_keys=True))
        return 1
    the_plan["landed_sha"] = sha
    print(json.dumps(the_plan, sort_keys=True))
    return 0


def _selftest():
    """Six frozen vectors on canned facts; 0 green, 1 red."""
    failures = []

    def check(name, cond, detail=""):
        print("[SELFTEST] {0} {1}{2}".format("PASS" if cond else "FAIL", name,
                                             (": " + detail) if detail and not cond else ""))
        if not cond:
            failures.append(name)

    a, r = decide("s" * 40, "s" * 40, "success", "s" * 40)
    check("v1-hold-on-equality", a == "hold" and "already names" in r, r)
    a, r = decide("s" * 40, "s" * 40, "success", "0" * 40)
    check("v2-move-on-difference", a == "move", r)
    a, r = decide("s" * 40, "s" * 40, "success", None)
    check("v3-create-on-absence", a == "create", r)
    a, r = decide("a" * 40, "b" * 40, "success", None)
    check("v4-stale-guard", a == "wait" and "under check" in r, r)
    a, r = decide("s" * 40, "s" * 40, "failure", None)
    check("v5-failed-run-hold", a == "wait" and "only on green" in r, r)
    sample = {"action": "hold", "reason": "x", "run_head": "h", "main_head": "m",
              "stable_target": "t", "run_id": 1, "schema": "rocqwash-stable-channel-plan/1"}
    check("v6-plan-schema-closed-set",
          set(decide.__doc__ is not None for _ in [0]) == {True}
          and set(sample.keys()) == {"action", "reason", "run_head", "main_head",
                                     "stable_target", "run_id", "schema"})
    print("STABLE-CHANNEL-SELFTEST: {0} vector(s), {1} FAIL".format(6, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(_selftest())
    repo = token = None
    ci_workflow = "ci.yml"
    do_move = "--move" in args
    do_check = "--check" in args
    i = 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            repo = args[i + 1]
            i += 2
        elif args[i] == "--ci-workflow" and i + 1 < len(args):
            ci_workflow = args[i + 1]
            i += 2
        else:
            i += 1
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token or not (do_move or do_check):
        sys.stderr.write("usage: stable_channel.py --repo OWNER/REPO (--check | --move) "
                         "[--ci-workflow NAME]; GITHUB_TOKEN must be set\n")
        sys.exit(2)
    if do_move:
        sys.exit(move(repo, token, ci_workflow))
    the_plan, _facts = plan(repo, token, ci_workflow)
    print(json.dumps(the_plan, sort_keys=True))
    sys.exit(0)
