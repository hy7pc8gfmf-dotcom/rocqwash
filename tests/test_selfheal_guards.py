#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_selfheal_guards: suite shell for the self-heal driver's three
heal-leg guards (.github/scripts/selfheal_rocqwash.py).

    Purpose.  The three heal-leg guardrails as frozen vectors (attempt
      cap heal_leg :140-143 at-most-once; cancel-intent never-revive
      :144-145; live re-check :149-156 - cancelled or not completed is
      desk intent, transport error is a loud skip), the reconcile
      intent recording (:204-206), and the automerge stale-attempt
      head-CI selection (an older head's red never gates a green head).
    Interface.  No CLI.  Six vector groups, 28 checks: attempt-cap skip
      with zero POST and the cap preceding the live GET; cancel-intent
      skip with zero POST plus the cap-outranks-intent order pin; the
      live re-check four-way (in-progress / cancelled / transport error
      all skip; a still-completed run dispatches exactly one
      rerun-failed-jobs POST behind exactly one GET); the transient-only
      family whitelist; the reconcile intent recording with zero POSTs;
      the stale-attempt selection (exact preference, newest-only within
      a head, linked fallback, empty pool; replay = one merge PUT +
      exclusion line; red newest = hold, zero POSTs).
    Dependencies.  Python 3 stdlib only (argparse, datetime, importlib.util,
      json, os, sys); the driver module loads by path and its gh_api/time
      symbols are replaced with an in-process recording stub; tmp-free,
      zero network, zero real sleep, zero repository writes.
    Evidence.  The stub vectors assert on the recorded (method, path)
      call log; the selection vectors assert on the pure helper's
      return; nothing is inferred from source reading.
    Exit-codes.  0 all checks pass; 1 any check red (listed loudly).
"""
import importlib.util
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, ".github", "scripts", "selfheal_rocqwash.py")


def load_module():
    if not os.path.isfile(SCRIPT):
        sys.stderr.write("T-SELFHEAL-GUARDS FAIL selfheal_rocqwash.py "
                         "missing: %s\n" % SCRIPT)
        raise SystemExit(1)
    spec = importlib.util.spec_from_file_location(
        "rqw_test_selfheal_rocqwash", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ApiStub(object):
    """Recording gh_api stand-in: canned run/runs responses, a settable
    live-run state, zero network."""

    def __init__(self, live_run):
        self.live_run = live_run      # None = transport error on live GET
        self.calls = []               # (method, path) log

    def __call__(self, token, path, method="GET", body=None):
        self.calls.append((method, path))
        if path.endswith("/rerun-failed-jobs"):
            return {}, None
        if "/runs/" in path and path.rstrip("/").split("/")[-1].isdigit() \
                and "/jobs" not in path:
            if self.live_run is None:
                return None, "transport-error-canned"
            return self.live_run, None
        if "/runs" in path and "workflows" in path:
            return self.runs_list, None
        if "/jobs" in path:
            return {"jobs": []}, None
        return {}, None

    def posts(self):
        return [p for m, p in self.calls if m == "POST"]


def make_args(heal=True, delay=0):
    import argparse
    return argparse.Namespace(repo="org/repo", run=178, out=".",
                              heal=heal, heal_delay=delay, reconcile=False)


TRANSIENT = "transient-infra"


def run_guard(mod, api, run, family, heal=True, delay=0):
    """heal_leg with the stubbed transport; the real time.sleep face is
    bypassed by stubbing the module symbol (delay 0 even when not
    stubbed)."""
    mod.gh_api = api
    return mod.heal_leg(make_args(heal=heal, delay=delay), "token",
                        "org/repo", run, family)


def main():
    mod = load_module()
    fails = []

    def check(name, cond, detail=""):
        if cond:
            print("PASS %s" % name)
        else:
            fails.append("%s -- %s" % (name, detail))
            print("FAIL %s -- %s" % (name, detail))

    # ---- vector 1: the attempt cap (the at-most-once budget, :140-143) --
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 2,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("attempt-cap-skips", verdict == "skipped(attempt-cap)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("attempt-cap-attempt-echo", "attempt=2" in detail,
          "detail=%r" % detail)
    check("attempt-cap-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("attempt-cap-precedes-live-check", api.calls == [],
          "cap must precede the live re-check GET: %r" % api.calls)
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": None,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("attempt-missing-defaults-to-1", verdict != "skipped(attempt-cap)",
          "verdict=%r" % verdict)

    # ---- vector 2: cancel-intent (desk intent, never revived, :144-145) -
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "cancelled"},
                                TRANSIENT)
    check("cancel-intent-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("cancel-intent-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("cancel-intent-precedes-live-check", api.calls == [],
          "intent gate precedes the live re-check GET: %r" % api.calls)
    # the cap outranks the intent gate (guard order is pinned)
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, _ = run_guard(mod, api,
                           {"id": 178, "run_attempt": 3,
                            "status": "completed",
                            "conclusion": "cancelled"},
                           TRANSIENT)
    check("cap-outranks-intent", verdict == "skipped(attempt-cap)",
          "verdict=%r" % verdict)

    # ---- vector 3: the live re-check (before the rerun POST, :149-156) --
    # 3a: live in_progress = desk moved the run -> intent skip, zero POST
    api = ApiStub(live_run={"id": 178, "status": "in_progress",
                            "conclusion": None})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-in-progress-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-in-progress-live-get", ("GET", "/repos/org/repo/actions/"
                                        "runs/178") in api.calls,
          "calls=%r" % api.calls)
    check("live-in-progress-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3b: live cancelled = desk intent -> skip, zero POST
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "cancelled"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-cancelled-skips", verdict == "skipped(intent-cancelled)",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-cancelled-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3c: live-check transport failure = loud skip, zero POST
    api = ApiStub(live_run=None)
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-error-skips", verdict == "skipped(live-check: "
          "transport-error-canned)", "verdict=%r detail=%r"
          % (verdict, detail))
    check("live-error-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    # 3d: live still completed -> exactly one rerun POST
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                TRANSIENT)
    check("live-still-completed-dispatches", verdict == "dispatched",
          "verdict=%r detail=%r" % (verdict, detail))
    check("live-still-completed-one-post",
          api.posts() == ["/repos/org/repo/actions/runs/178/"
                          "rerun-failed-jobs"],
          "posts=%r" % api.posts())
    check("live-still-completed-single-get",
          api.calls == [("GET", "/repos/org/repo/actions/runs/178"),
                        ("POST", "/repos/org/repo/actions/runs/178/"
                         "rerun-failed-jobs")],
          "exactly one live GET then one rerun POST, in order: %r"
          % api.calls)

    # ---- vector 4: the family whitelist feeding the three guards -------
    api = ApiStub(live_run={"id": 178, "status": "completed",
                            "conclusion": "failure"})
    verdict, detail = run_guard(mod, api,
                                {"id": 178, "run_attempt": 1,
                                 "status": "completed",
                                 "conclusion": "failure"},
                                "content-red")
    check("content-red-not-healable",
          verdict == "skipped(family-not-healable)",
          "verdict=%r" % verdict)
    check("content-red-zero-post", api.posts() == [],
          "posts=%r" % api.posts())
    check("content-red-zero-live-check", api.calls == [],
          "family gate precedes every fetch: %r" % api.calls)

    # ---- vector 5: reconcile records cancelled as intent (:204-206) ----
    # fixture dates are computed relative to now so the canned cancelled
    # runs always sit inside the 48h RECONCILE_WINDOW_H (absolute stamps
    # aged out of the window and silently emptied the intent list)
    import datetime
    _now = datetime.datetime.now(datetime.timezone.utc)

    def _stamp(age_h):
        return (_now - datetime.timedelta(hours=age_h)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")

    api = ApiStub(live_run=None)
    api.runs_list = {"total_count": 3, "workflow_runs": [
        {"id": 201, "run_number": 10, "status": "queued",
         "conclusion": None, "created_at": _stamp(3)},
        {"id": 178, "run_number": 9, "status": "completed",
         "conclusion": "cancelled", "created_at": _stamp(1)},
        {"id": 155, "run_number": 8, "status": "completed",
         "conclusion": "cancelled", "created_at": _stamp(2)},
    ]}
    mod.gh_api = api
    token_saved = os.environ.pop("GITHUB_TOKEN", None)
    try:
        os.environ["GITHUB_TOKEN"] = "stub-token"   # the stub ignores it
        lines = mod.reconcile_leg(make_args(), "org/repo")
    finally:
        os.environ.pop("GITHUB_TOKEN", None)
        if token_saved is not None:
            os.environ["GITHUB_TOKEN"] = token_saved
    text = "\n".join(lines)
    check("reconcile-records-intent-not-revive",
          "cancelled=intent" in text and "not revived" in text, text)
    check("reconcile-cancels-counted",
          sum(1 for ln in lines if "cancelled=intent" in ln) == 2,
          "both cancelled runs recorded: %r" % lines)
    check("reconcile-never-revives", api.posts() == [],
          "reconcile never POSTs a revive: %r" % api.posts())

    # ---- vector 6: stale-attempt head-CI selection (automerge gate, the
    # PR #123 incident: attempt-1's red run permanently held the green
    # attempt-2 head; RIS-11) -------------------------------------------
    sha_a, sha_b = "a" * 40, "b" * 40
    red_old = {"id": 1, "head_sha": sha_a, "event": "pull_request",
               "status": "completed", "conclusion": "failure",
               "created_at": "2026-11-26T22:09:16Z",
               "pull_requests": [{"number": 123}]}
    green_new = {"id": 2, "head_sha": sha_b, "event": "pull_request",
                 "status": "completed", "conclusion": "success",
                 "created_at": "2026-11-26T22:42:20Z",
                 "pull_requests": [{"number": 123}]}
    jobs = {
        1: [{"name": "Self-test suite (Linux)", "conclusion": "failure"}],
        2: [{"name": "Self-test suite (Linux)", "conclusion": "success"},
            {"name": "Self-test suite (Windows (local self-hosted))",
             "conclusion": "skipped"}],
    }
    prs = [{"number": 123, "draft": False, "mergeable": True,
            "head": {"ref": "supply/ris-9", "sha": sha_b}}]

    # pure helper: exact-match preference over linked fallback
    judged, stale = mod.select_head_runs([red_old, green_new], sha_b)
    check("select-exact-prefers-current-head",
          len(judged) == 1 and judged[0]["id"] == 2 and stale == 1,
          "judged=%r stale=%r" % (judged, stale))
    # pure helper: linked fallback when no run matches the head sha
    # (legacy merge-ref reporting shape); newest linked run is judged
    legacy_a = dict(red_old, head_sha="c" * 40)
    legacy_b = dict(green_new, head_sha="d" * 40,
                    created_at="2026-11-26T22:45:00Z")
    judged, stale = mod.select_head_runs([legacy_a, legacy_b], sha_b)
    check("select-linked-fallback-newest",
          len(judged) == 1 and judged[0]["id"] == 2 and stale == 1,
          "judged=%r stale=%r" % (judged, stale))
    # pure helper: newest only within one head (rerun pair semantics)
    green_older = dict(green_new, created_at="2026-11-26T22:30:00Z")
    judged, stale = mod.select_head_runs(
        [green_older, dict(green_new, id=3,
                           created_at="2026-11-26T22:50:00Z")],
        sha_b)
    check("select-newest-within-same-head",
          len(judged) == 1 and judged[0]["id"] == 3 and stale == 1,
          "judged=%r stale=%r" % (judged, stale))
    # pure helper: empty pool
    judged, stale = mod.select_head_runs([], sha_b)
    check("select-empty-pool", judged == [] and stale == 0,
          "judged=%r stale=%r" % (judged, stale))

    # incident replay through the leg: older red linked + green current
    # head reaches exactly one merge PUT, with the exclusion report line
    class AutomergeStub(object):
        """Recording gh_api stand-in for automerge_leg: canned PR list,
        run lists, per-run jobs; records every call; zero network."""

        def __init__(self, prs_in, runs_a, runs_b, jobs_in):
            self.prs = prs_in
            self.runs_a = runs_a
            self.runs_b = runs_b
            self.jobs = jobs_in
            self.calls = []

        def __call__(self, token, path, method="GET", body=None):
            self.calls.append((method, path))
            if method == "GET" and "/pulls?state=open" in path:
                return self.prs, None
            if method == "GET" and "head_sha=" in path:
                return {"workflow_runs": self.runs_a}, None
            if method == "GET" and "event=pull_request" in path:
                return {"workflow_runs": self.runs_b}, None
            if method == "GET" and "/jobs" in path:
                rid = int(path.rstrip("/").split("/")[-2])
                return {"jobs": self.jobs.get(rid, [])}, None
            return {}, None

        def posts(self):
            return [p for m, p in self.calls if m == "POST"]

        def merge_puts(self):
            return [p for m, p in self.calls
                    if m == "PUT" and p.endswith("/pulls/123/merge")]

    api = AutomergeStub(prs, [green_new], [red_old, green_new], jobs)
    mod.gh_api = api
    lines = mod.automerge_leg("token", "org/repo")
    text = "\n".join(lines)
    check("incident-replay-merges-current-head",
          len(api.merge_puts()) == 1 and "MERGED" in text,
          "puts=%r lines=%r" % (api.merge_puts(), lines))
    check("incident-replay-reports-excluded-stale",
          "1 superseded run(s) excluded" in text, text)

    # a red newest run still holds, zero merge attempts
    jobs_red_newest = dict(jobs)
    jobs_red_newest[2] = [{"name": "Self-test suite (Linux)",
                           "conclusion": "failure"}]
    api = AutomergeStub(prs, [green_new], [red_old, green_new],
                        jobs_red_newest)
    mod.gh_api = api
    lines = mod.automerge_leg("token", "org/repo")
    text = "\n".join(lines)
    check("red-newest-holds",
          "hold (head CI hosted faces red)" in text
          and api.merge_puts() == [],
          "puts=%r lines=%r" % (api.merge_puts(), lines))
    check("red-newest-zero-post", api.posts() == [],
          "posts=%r" % api.posts())

    if fails:
        sys.stderr.write("T-SELFHEAL-GUARDS RED (%d): %s\n"
                         % (len(fails), "; ".join(fails)))
        return 1
    sys.stdout.write("T-SELFHEAL-GUARDS PASS (6 vector groups, 28 checks: "
                     "attempt-cap / cancel-intent / live re-check / family "
                     "whitelist / reconcile intent recording / stale-"
                     "attempt head-CI selection)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
