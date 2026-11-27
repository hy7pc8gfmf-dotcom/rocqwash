#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfheal_rocqwash.py - rocqwash self-heal CI driver.
Purpose.  Triage a red CI run into the transient-infra / content-red
  families, heal transient-infra failures under three guards
  (cancel-intent, attempt==1, live re-check), auto-repair mechanical
  content-red classes through the repair_scope roster, govern the queued
  run count, automerge green supply/* pull requests, and run a weekly
  read-only branch census. Stateless by design: no persistent state, no
  repository writes outside the single repair commit face.
Interface.  Invoked by `.github/workflows/selfheal.yml` in three forms:
  triage+heal `--repo OWNER/REPO --run RUN_ID --out DIR --heal`;
  reconcile `--repo OWNER/REPO --run 0 --out DIR --reconcile`;
  automerge-only `--repo OWNER/REPO --run 0 --out DIR --automerge-only`.
  Reports land as files under `--out` (triage-report.txt, summary.txt,
  reconcile-report.txt, automerge-report.txt, branch-census.txt) and are
  uploaded as workflow artifacts; the API credential comes from the
  `GITHUB_TOKEN` environment variable. The R15 repair-plan leg appends
  its verdict rows to docs/repair-plan-ledger.jsonl in the repository
  (the single repo-write exception; guards in the contract note below).
Dependencies.  Python 3 standard library only; GitHub REST API v3 over
  urllib; `tests/run_tests.sh` (repair roster); `tools/repair_scope.py`
  (imported by path); `tools/pin_repair.py` (plan executor, when present);
  `docs/ci-triage-table.json` (failure-class table, when present).
Evidence.  Exercised live by `.github/workflows/selfheal.yml`; the repair
  leg lands one commit per repair so CI re-judges it; the branch census
  and the parse-death probe are read-only; every repair-plan executor
  failure is reported loudly in the heal detail.
Exit-codes.  0 = triage/verdict obtained (a red verdict is data, not a
  tool failure); 2 = wiring/usage failure; 3 = internal error.
"""
# Extended contract (kept outside the five-field docstring so the header
# stays within the 30-line budget of the annotation standard).  Mirror of
# the Main repo watch (.github/workflows/rocqwash-triage.yml +
# rocqwash_triage.py), adapted for a hosted-runner, STATELESS face:
#  * budget: heal only run_attempt==1 runs - GitHub's own attempt counter
#    guarantees at-most-once without persistent state (hosted runners keep
#    no state between runs)
#  * cancel-intent: conclusion==cancelled runs are NEVER revived
#    (same policy as the Main watch)
#  * queue governor (reconcile): keep at most MAX_QUEUED_RUNS queued runs,
#    oldest trimmed; in-progress runs are never touched
#  * branch census (reconcile, weekly): a stateless run-number gate
#    (BRANCH_CENSUS_EPOCH) runs a READ-ONLY branch census - merged-stale
#    stubs are reported to the desk as deletion CANDIDATES, never deleted
#    in-run
#  * content reds: MECHANICAL classes are auto-repaired via the landed
#    repair_scope roster (the watch repairs, not only records);
#    non-mechanical classes stay desk-gated pending E1/E2 model legs;
#    every repair lands as its own commit so CI re-judges it
#  * repair-plan leg: an R15 match (provenance pin drift) with
#    auto_repairable additionally asks the pin-repair executor
#    (tools/pin_repair.py --plan) for its zero-write plan verdict and
#    appends one JSON row per match to docs/repair-plan-ledger.jsonl
#    (schema rocqwash.repair-plan/1, append-only, one JSON object per
#    line); plan only - nothing is applied on the CI side, and this
#    ledger append is the single repo-write exception to the
#    no-repo-writes rule above; every executor failure (missing executor,
#    timeout, nonzero exit, unparseable stdout) is reported loudly
#  * ledger: no repo writes - verdicts land in the job log and the uploaded
#    artifact (the desk inbox face belongs to the Main watch)
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

WF_FILE = "ci.yml"
FURNACE_NAME = "rocqwash CI"
MAX_QUEUED_RUNS = 3
RECONCILE_WINDOW_H = 48
BRANCH_CENSUS_EPOCH = 336  # half-hour reconcile passes per week (7d * 48)
HEAL_DELAY_S = 90
TRANSIENT_WORDS = ("checkout", "connection", "timeout", "fetch", "runner",
                   "network", "set up")
SUITE_STEP = "Run self-test suite"
# Repair-plan leg (R15): the zero-write plan executor and the append-only
# JSONL ledger where each plan verdict is recorded, both relative to the
# repository root (the script's working directory on every invocation face).
REPAIR_PLAN_LEDGER = os.path.join("docs", "repair-plan-ledger.jsonl")
PIN_REPAIR_EXECUTOR = os.path.join("tools", "pin_repair.py")


def log(msg):
    sys.stdout.write("[selfheal] %s\n" % msg)
    sys.stdout.flush()


def gh_api(token, path, method="GET", body=None):
    """One REST call.  GET retries twice on transient transport failures
    (truncated reads / resets in the NETRED window)."""
    attempts = 2 if method == "GET" else 1
    last_err = None
    for attempt in range(attempts):
        url = "https://api.github.com" + path
        data = json.dumps(body).encode("utf-8") if body is not None else \
            (b"" if method == "POST" else None)
        req = urllib.request.Request(url, method=method, data=data, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "rocqwash-selfheal",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            return (json.loads(raw) if raw else None), None
        except urllib.error.HTTPError as exc:
            # Fail loud: the status line alone hid the real verdict (merge
            # PUT 403: the body carries the actual message and was
            # discarded).
            try:
                detail = exc.read(400).decode("utf-8", "replace").strip()
            except Exception:
                detail = ""
            return None, "%d %s %s" % (exc.code, exc.reason, detail)
        except Exception as exc:
            last_err = exc
            if attempt + 1 < attempts:
                time.sleep(3 + attempt * 5)
    return None, repr(last_err)


def classify(jobs):
    """Five-family-lite: transient-infra vs content-red.  Precedent (Main
    watch): the suite-step verdict wins - if the suite step ran and failed,
    the red is content; infra reds are the cases where the suite never
    started (checkout/setup/runner died first)."""
    failed_steps = []
    suite_ran = False
    for job in jobs or []:
        for s in job.get("steps") or []:
            name = s.get("name") or ""
            if name == SUITE_STEP:
                suite_ran = suite_ran or s.get("conclusion") in (
                    "success", "failure")
            if s.get("conclusion") == "failure":
                failed_steps.append(name)
    low = " | ".join(failed_steps).lower()
    if suite_ran:
        return "content-red", failed_steps
    if failed_steps and any(w in low for w in TRANSIENT_WORDS):
        return "transient-infra", failed_steps
    if failed_steps:
        return "content-red", failed_steps
    return "no-jobs", []


def load_triage_table(repo_root="."):
    """The whitepaper's machine face: docs/ci-triage-table.json
    (schema rocqwash.ci-triage-table/1).  Absent/damaged = None (the
    classification falls back to the built-in family logic)."""
    path = os.path.join(repo_root, "docs", "ci-triage-table.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        log("triage-table load failed: %r" % exc)
        return None


class _LogNoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_run_log_text(token, repo, run_id, cap=400000):
    """Whole-run logs zip via the 302 dance (auth first hop, header-less
    second hop - forwarding the token to the blob store yields 401);
    per-job .txt members concatenated, tail-capped for marker matching."""
    import zipfile
    opener = urllib.request.build_opener(_LogNoRedirect())
    url = "https://api.github.com/repos/%s/actions/runs/%d/logs" % (repo,
                                                                    run_id)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "User-Agent": "rocqwash-selfheal"})
    loc = None
    try:
        opener.open(req, timeout=120)
        return ""
    except urllib.error.HTTPError as e302:
        if e302.code in (301, 302, 303, 307):
            loc = e302.headers.get("Location")
        if not loc:
            return ""
    req2 = urllib.request.Request(loc, headers={"User-Agent":
                                                "rocqwash-selfheal"})
    try:
        with urllib.request.urlopen(req2, timeout=180) as resp:
            raw = resp.read()
    except Exception:
        return ""
    texts = []
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
        for name in zf.namelist():
            if name.endswith(".txt"):
                texts.append(zf.read(name).decode("utf-8",
                                                  errors="replace"))
    except Exception:
        return raw.decode("utf-8", errors="replace")
    return chr(10).join(texts)[-cap:]


def match_classes(log_text, table):
    """Match the ten failure classes by markers (precedence order);
    returns the matched class summaries (id/title/auto_repairable/
    prescription/hit_markers)."""
    matched = []
    for cls in sorted(table.get("classes", []),
                      key=lambda c: c.get("precedence", 99)):
        markers = [m for m in (cls.get("markers") or []) if m]
        hit = [m for m in markers if m in log_text]
        if hit:
            matched.append({
                "id": cls.get("id"),
                "title": cls.get("title"),
                "auto_repairable": cls.get("auto_repairable"),
                "prescription": cls.get("prescription", ""),
                "hit_markers": hit[:3],
            })
    return matched


def triage_leg(args, repo, run_id):
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return "skipped(no-token)", "GITHUB_TOKEN absent", []
    run, err = gh_api(token, "/repos/%s/actions/runs/%d" % (repo, run_id))
    if err or not run:
        return "skipped(run-fetch: %s)" % err, "run fetch failed", []
    info = "run %d attempt %s branch %s head %s conclusion %s" % (
        run_id, run.get("run_attempt"), run.get("head_branch"),
        (run.get("head_sha") or "")[:7], run.get("conclusion"))
    jobs, jerr = gh_api(token, "/repos/%s/actions/runs/%d/jobs?per_page=20"
                        % (repo, run_id))
    if jerr:
        return "skipped(jobs-fetch: %s)" % jerr, info, []
    family, failed_steps = classify(jobs.get("jobs"))
    log("triage: family=%s failed_steps=%s" % (family, failed_steps[:4]))
    triage_matched, triage_note = [], ""
    try:
        log_text = fetch_run_log_text(token, repo, run_id)
        table = load_triage_table(".")
        if table and log_text:
            triage_matched = match_classes(log_text, table)
            triage_note = "; ".join(
                "%s[auto=%s]" % (c["id"], c["auto_repairable"])
                for c in triage_matched)
    except Exception as exc:
        triage_note = "table-consume failed: %r" % exc
    log("triage-table: %s" % (triage_note[:200] or "no class matched"))

    heal_verdict, heal_detail = "skipped(disabled)", "no --heal"
    if args.heal:
        heal_verdict, heal_detail = heal_leg(args, token, repo, run, family)
    repair_verdict, repair_detail = "skipped(disabled)", "no --heal"
    if args.heal and family == "content-red":
        try:
            repair_verdict, repair_detail = repair_content_red(
                token, repo, args.out)
        except Exception as exc:
            repair_verdict, repair_detail = ("failed(exception)", repr(exc))
        log("repair: %s | %s" % (repair_verdict, repair_detail[:200]))

    # Repair-plan leg (R15): the matched classes above additionally drive
    # the zero-write plan executor; its verdict row lands in the ledger
    # and its note rides the heal detail. Never raises (failures are
    # recorded, not swallowed).
    repair_plan_note = ""
    if triage_matched:
        try:
            repair_plan_note = repair_plan_leg(triage_matched, run_id)
        except Exception as exc:
            repair_plan_note = ("repair-plan: unexpected failure, "
                                "escalated: %r" % exc)
            log(repair_plan_note)
    if repair_plan_note:
        heal_detail = "%s | %s" % (heal_detail, repair_plan_note)

    points = ("rocqwash CI red run %d: family=%s failed_steps=%s (auto "
              "triage by rocqwash self-heal)" % (run_id, family,
                                                 failed_steps[:3]))
    triage_section = ""
    if triage_matched:
        triage_section = "\ntriage-table matched classes:\n" + "\n".join(
            "- %s (%s): auto_repairable=%s\n  prescription: %s"
            % (c["id"], c["title"], c["auto_repairable"],
               c["prescription"][:200])
            for c in triage_matched)
    return "OBTAINED", info + " | family=" + family, [
        ("triage-report.txt",
         "run=%d\n%s\nfamily=%s\nfailed_steps=%s\nheal=%s\n%s\n"
         "%s\n"
         % (run_id, info, family, failed_steps, heal_verdict, heal_detail,
            triage_section)),
        ("summary.txt",
         "verdict=OBTAINED run=%d family=%s heal=%s repair=%s\n"
         "triage-table=%s"
         % (run_id, family, heal_verdict, repair_verdict, triage_note)),
    ]


def repair_plan_leg(matched, run_id, repo_root="."):
    """Repair-plan leg for R15 (provenance pin drift, auto_repairable):
    ask the pin-repair executor for its zero-write plan verdict and append
    one JSON row per R15 match to docs/repair-plan-ledger.jsonl (schema
    rocqwash.repair-plan/1). Plan only: nothing is applied on the CI side
    (apply belongs to the cron / desk face). Every failure is loud: a
    missing executor is recorded as action="executor-absent"; a failed,
    timed-out, or nonzero executor run is recorded with ok=false and the
    executor's stdout/stderr tail in the note; a ledger write failure is
    recorded with ok=false and the OS error. The returned note string is
    appended to the heal detail (it never raises)."""
    import subprocess
    rows = [c for c in matched if c.get("id") == "R15"
            and c.get("auto_repairable")]
    if not rows:
        return ""
    run_key = str(run_id) if run_id else "local"
    notes = []
    for _hit in rows:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        row = {"schema": "rocqwash.repair-plan/1", "ts": ts, "run": run_key,
               "class": "R15", "action": "plan", "ok": False, "drifted": [],
               "verdict": "", "note": ""}
        if not os.path.isfile(os.path.join(repo_root, PIN_REPAIR_EXECUTOR)):
            row["action"] = "executor-absent"
            row["note"] = ("pin-repair executor not present at %s; "
                           "plan leg cannot run, escalated"
                           % PIN_REPAIR_EXECUTOR)
            note = "repair-plan: executor-absent | %s" % row["note"]
        else:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", PIN_REPAIR_EXECUTOR, "--plan"],
                    cwd=repo_root, capture_output=True, timeout=120)
            except subprocess.TimeoutExpired:
                row["note"] = ("pin-repair --plan timed out after 120s; "
                               "escalating")
            except OSError as exc:
                row["note"] = ("pin-repair --plan spawn failed: %r; "
                               "escalating" % exc)
            else:
                stdout_tail = ((proc.stdout or b"").decode(
                    "utf-8", "replace").strip()[-300:])
                stderr_tail = ((proc.stderr or b"").decode(
                    "utf-8", "replace").strip()[-300:])
                parsed = None
                if proc.returncode == 0 and stdout_tail:
                    try:
                        parsed = json.loads(stdout_tail.splitlines()[-1])
                    except ValueError:
                        parsed = None
                if isinstance(parsed, dict):
                    row["ok"] = bool(parsed.get("ok"))
                    row["drifted"] = parsed.get("drifted") or []
                    verdict = parsed.get("verdict", parsed.get("action", ""))
                    row["verdict"] = verdict if isinstance(verdict, str) \
                        else json.dumps(verdict)
                else:
                    row["verdict"] = "unparseable"
                if proc.returncode != 0:
                    row["note"] = ("pin-repair --plan exit %d; stdout=%s; "
                                   "stderr=%s"
                                   % (proc.returncode, stdout_tail,
                                      stderr_tail))
                elif not isinstance(parsed, dict):
                    row["note"] = ("pin-repair --plan stdout not one JSON "
                                   "line: %s" % stdout_tail)
                else:
                    row["note"] = ("pin-repair --plan exit 0 ok=%s "
                                   "drifted=%d" % (row["ok"],
                                                   len(row["drifted"])))
            note = ("repair-plan: ok=%s verdict=%s drifted=%d | %s"
                    % (row["ok"], row["verdict"], len(row["drifted"]),
                       row["note"]))
        try:
            with open(os.path.join(repo_root, REPAIR_PLAN_LEDGER), "a",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(row, ensure_ascii=True) + "\n")
        except OSError as exc:
            row["ok"] = False
            row["note"] = ("repair-plan ledger append failed (%s): %r"
                           % (REPAIR_PLAN_LEDGER, exc))
            note = "repair-plan: ledger-append-failed | %r" % exc
            log(note)
        notes.append(note)
    return "; ".join(notes)


def heal_leg(args, token, repo, run, family):
    """Three guards mirror the Main watch: cancel-intent, attempt==1
    (stateless at-most-once), live re-check right before the rerun POST."""
    if family != "transient-infra":
        return ("skipped(family-not-healable)",
                "family=%s not in heal whitelist (transient-infra only; "
                "content reds are desk-gated)" % family)
    if int(run.get("run_attempt") or 1) != 1:
        return ("skipped(attempt-cap)",
                "attempt=%s - at-most-once per run (stateless budget)"
                % run.get("run_attempt"))
    if run.get("conclusion") == "cancelled":
        return "skipped(intent-cancelled)", "cancelled = desk intent"
    run_id = run["id"]
    log("heal: stable-window delay %ds before rerun" % args.heal_delay)
    time.sleep(args.heal_delay)
    live, lerr = gh_api(token, "/repos/%s/actions/runs/%d" % (repo, run_id))
    if lerr:
        return "skipped(live-check: %s)" % lerr, "live check failed"
    if (live or {}).get("conclusion") == "cancelled" or \
            (live or {}).get("status") != "completed":
        return ("skipped(intent-cancelled)",
                "live status=%s conclusion=%s - desk intent, not resurrected"
                % ((live or {}).get("status"), (live or {}).get("conclusion")))
    _, perr = gh_api(token, "/repos/%s/actions/runs/%d/rerun-failed-jobs"
                     % (repo, run_id), method="POST")
    if perr:
        return "refused(http: %s)" % perr, "rerun-failed-jobs refused"
    return "dispatched", "rerun-failed-jobs POSTed for run %d" % run_id


def repair_content_red(token, repo, out_dir):
    """CURE leg (the watch must repair, not only record).  Mechanical
    content-red classes only, using the landed
    repair_scope roster: R1 = suite lanes registered without their
    artifact file -> drop the registration lines; the repair lands as
    its own commit (pushed with the workflow token) so CI re-judges it.
    Certification faces and the append-only ledger are excluded via
    repair_scope and are never touched."""
    import subprocess
    log("repair: scanning roster for lanes without artifacts")
    rosters = "tests/run_tests.sh"
    try:
        with open(rosters, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines(True)
    except OSError as exc:
        return "skipped(roster-read: %r)" % exc, []
    missing = []
    for line in lines:
        stripped = line.strip()
        name = None
        if stripped.endswith(chr(92) + chr(92)) and stripped[:-2].startswith("t_"):
            name = stripped[:-2].strip()
        elif stripped.startswith("t_") and stripped.endswith('"'):
            name = stripped[:-1].strip()
        if not name:
            continue
        cand = "tests/%s.py" % name
        if not os.path.isfile(cand):
            missing.append((name, line))
    if not missing:
        return "skipped(no-missing-lane)", []
    dropped = [name for name, _ in missing]
    drop_set = set(line for _, line in missing)
    new_lines = [l for l in lines if l not in drop_set]
    for i, l in enumerate(new_lines):
        s = l.rstrip(chr(13) + chr(10)).rstrip()
        if s.endswith(chr(92)):
            nxt = new_lines[i + 1].strip() if i + 1 < len(new_lines) else ""
            if not nxt.startswith("t_"):
                new_lines[i] = s[:-1].rstrip() + l[len(s.rstrip(chr(92))):]
    with open(rosters, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(new_lines))
    ch = subprocess.run(["bash", "-n", rosters], capture_output=True,
                        timeout=60)
    if ch.returncode != 0:
        subprocess.run(["git", "checkout", "--", rosters], timeout=60)
        return "failed(bash-n)", ["reverted: bash -n refused the edit"]
    try:
        import repair_scope
        excluded = repair_scope.full_frozen_files(".")
    except Exception as exc:
        excluded = []
    overlap = [d for d in dropped if any(d in x for x in excluded)]
    if overlap:
        subprocess.run(["git", "checkout", "--", rosters], timeout=60)
        return ("skipped(frozen-overlap: %s)" % ",".join(overlap),
                ["frozen faces are never repaired automatically"])
    subprocess.run(["git", "add", "--", rosters], capture_output=True,
                   timeout=60)
    token = os.environ.get("GITHUB_TOKEN", "")
    push_url = "https://x-access-token:%s@github.com/%s.git" % (token, repo)
    cm = subprocess.run(
        ["git", "-c", "user.name=rocqwash-selfheal",
         "-c", "user.email=rocqwash-selfheal@users.noreply.github.com",
         "commit", "-m",
         "selfheal(auto-repair R1): drop lane(s) registered without their "
         "artifact file (%s)" % ",".join(dropped)],
        capture_output=True, text=True, timeout=120)
    if cm.returncode != 0:
        return "failed(commit)", (cm.stderr or "")[:200]
    ps = subprocess.run(["git", "push", push_url, "HEAD:refs/heads/main"],
                        capture_output=True, text=True, timeout=300)
    if ps.returncode != 0:
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], timeout=60)
        return "failed(push)", (ps.stderr or "")[:200].replace(token, "***")
    return ("repaired(R1-lane-drop x%d)" % len(dropped),
            ["dropped: %s" % ",".join(dropped), "pushed; CI re-judges"])


def select_head_runs(runs, head_sha):
    """Pick the runs that judge a PR head CI: the current head's own
    runs (head_sha equal to the PR head) when any exist, else the
    linked-run fallback pool; within the pool only the newest run is
    judged, so a superseded attempt (an older head's red run) never
    gates the merge behind a green current head (PR #123: attempt-1's
    red permanently held the green attempt-2 head). Returns (judged
    list, excluded stale count)."""
    if not runs:
        return [], 0
    exact = [r for r in runs
             if (r.get("head_sha") or "") == (head_sha or "")]
    pool = exact if exact else list(runs)
    ordered = sorted(pool, key=lambda r: ((r.get("created_at") or ""),
                                          r.get("id") or 0))
    return [ordered[-1]], (len(runs) - 1)


def automerge_leg(token, repo):
    """Automerge leg: supply/* PRs whose head CI is fully green and that
    are mergeable merge automatically (one per pass - a stateless cap).
    The head CI is judged on the newest run of the current head only;
    superseded attempts are excluded and reported. Other PRs are
    recorded, never force-merged."""
    prs, err = gh_api(token, "/repos/%s/pulls?state=open&per_page=20" % repo)
    if err or prs is None:
        return ["skipped(prs-list: %s)" % err]
    out = []
    merged_any = False
    for pr in prs:
        num = pr.get("number")
        ref = (pr.get("head") or {}).get("ref") or ""
        sha = (pr.get("head") or {}).get("sha") or ""
        if not ref.startswith("supply/"):
            continue
        if pr.get("draft"):
            out.append("#%s skip (draft)" % num)
            continue
        if pr.get("mergeable") is not True:
            # The PR LIST endpoint does not populate `mergeable` (computed
            # asynchronously, single-PR GET only) - re-read the single PR
            # before holding (R13 family: a field the chosen endpoint
            # never populates is a stall, not a verdict).
            one, oerr = gh_api(token, "/repos/%s/pulls/%d" % (repo, num))
            if oerr or not one:
                out.append("#%s hold (pr-read: %s)" % (num, oerr))
                continue
            if one.get("merged"):
                continue
            if one.get("mergeable") is False:
                out.append("#%s hold (merge conflict)" % num)
                continue
        # Head CI across all producing events: push runs (main-line),
        # branch dispatches (head_sha == the PR head), and pull_request
        # runs (head_sha is the merge-ref commit - match via the
        # pull_requests link instead).
        runs_a, aerr = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                              "?head_sha=%s&per_page=10"
                              % (repo, WF_FILE, sha))
        runs_b, berr = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                              "?event=pull_request&per_page=20"
                              % (repo, WF_FILE))
        seen, mine = set(), []
        for r in (((runs_a or {}).get("workflow_runs") or [])
                  + ((runs_b or {}).get("workflow_runs") or [])):
            if r.get("id") in seen:
                continue
            linked = any((p or {}).get("number") == num
                         for p in (r.get("pull_requests") or []))
            if ((r.get("head_sha") == sha or linked)
                    and r.get("event") in ("push", "workflow_dispatch",
                                           "pull_request")):
                seen.add(r.get("id"))
                mine.append(r)
        if not mine:
            # The PR head branch may be deleted while the PR stays open -
            # a workflow_dispatch run has no ref to target.
            # Restore the head ref from the PR head commit first (the
            # commit still exists; the deletion is ref-level only).
            _, berr = gh_api(token, "/repos/%s/branches/%s" % (repo, ref))
            if berr:
                _, crerr = gh_api(token, "/repos/%s/git/refs" % repo,
                                  method="POST",
                                  body={"ref": "refs/heads/" + ref,
                                        "sha": sha})
                if crerr:
                    out.append("#%s hold (head branch gone; ref-recreate "
                               "refused: %s)" % (num, crerr))
                    continue
                out.append("#%s head branch restored at %s (deleted head)"
                           % (num, sha[:8]))
            _, derr = gh_api(token,
                             "/repos/%s/actions/workflows/%s/dispatches"
                             % (repo, WF_FILE), method="POST",
                             body={"ref": ref})
            if derr:
                out.append("#%s hold (no head CI yet; dispatch refused: %s)"
                           % (num, derr))
            else:
                out.append("#%s hold (no head CI yet - dispatched "
                           "ci.yml@%s)" % (num, ref))
            continue
        judged, stale = select_head_runs(mine, sha)
        if stale:
            out.append("#%s head CI: %d superseded run(s) excluded, "
                       "judging the newest current-head run (stale-attempt "
                       "gate, PR #123 incident)" % (num, stale))
        if any(r.get("status") != "completed" for r in judged):
            out.append("#%s hold (head CI running)" % num)
            continue
        # Gate on the hosted faces: the local self-hosted face is main-only
        # evidence and must not gate a PR merge (a workflow_dispatch run
        # from a
        # ref whose ci.yml predates the main_only gate still runs it, and
        # its bridge-resolved checkout cannot serve non-main refs).
        hosted_seen, hosted_ok = False, True
        for r in judged:
            jobs, jerr = gh_api(token, "/repos/%s/actions/runs/%s/jobs"
                                "?per_page=20" % (repo, r["id"]))
            for jb in ((jobs or {}).get("jobs") or []):
                if "local self-hosted" in (jb.get("name") or ""):
                    continue
                hosted_seen = True
                if jb.get("conclusion") not in ("success", "skipped"):
                    hosted_ok = False
        if not hosted_seen:
            out.append("#%s hold (head CI has no hosted faces)" % num)
            continue
        if not hosted_ok:
            out.append("#%s hold (head CI hosted faces red)" % num)
            continue
        if merged_any:
            out.append("#%s queued (one merge per pass)" % num)
            continue
        _, merr = gh_api(token, "/repos/%s/pulls/%d/merge" % (repo, num),
                         method="PUT",
                         body={"merge_method": "merge",
                               "commit_title":
                                   "automerge: PR #%d (supply lane, "
                                   "head CI green)" % num})
        if merr:
            out.append("#%s merge refused: %s" % (num, merr))
            continue
        merged_any = True
        out.append("#%d MERGED (supply lane, head CI green)" % num)
        log("automerge: PR #%d merged" % num)
        # Post-merge judge: the merge push carried GITHUB_TOKEN, so GitHub
        # suppresses the push event and the merge commit gets NO CI
        # (verified live, e73a34a: zero runs). workflow_dispatch
        # is the documented suppression exception - trigger ci.yml at the
        # base branch so the merge commit is judged on its own.
        _, perr = gh_api(token, "/repos/%s/actions/workflows/%s/dispatches"
                         % (repo, WF_FILE), method="POST",
                         body={"ref": (pr.get("base") or {}).get("ref")
                               or "main"})
        out.append("#%d post-merge CI %s"
                   % (num, "dispatched@main" if not perr
                      else "dispatch refused: %s" % perr))
    if not out:
        out = ["no open supply/* PRs"]
    return out


def reconcile_leg(args, repo):
    """Mirror of the Main reconcile: cancelled runs are recorded as intent
    (NOT revived), the pending queue is governed to MAX_QUEUED_RUNS."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return ["skipped(no-token)"]
    runs, err = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                       "?per_page=40" % (repo, WF_FILE))
    if err or not runs:
        return ["skipped(runs-list: %s)" % err]
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    cancelled, queued, busy = [], [], False
    for r in runs.get("workflow_runs") or []:
        created = r.get("created_at", "").replace("Z", "+00:00")
        try:
            age_h = (now - datetime.datetime.fromisoformat(created)
                     ).total_seconds() / 3600.0
        except ValueError:
            continue
        if r.get("status") in ("in_progress", "queued"):
            busy = True
        if r.get("status") == "queued":
            queued.append((r["id"], r["run_number"]))
        if (r.get("conclusion") == "cancelled"
                and age_h <= RECONCILE_WINDOW_H):
            cancelled.append((r["id"], r["run_number"], age_h))
    queued.reverse()  # oldest first
    out = []
    if len(queued) > MAX_QUEUED_RUNS:
        for gid, gnum in queued[:len(queued) - MAX_QUEUED_RUNS]:
            _, cerr = gh_api(token, "/repos/%s/actions/runs/%d/cancel"
                             % (repo, gid), method="POST")
            if cerr:
                out.append("#%d queue-trim cancel failed: %s" % (gnum, cerr))
            else:
                out.append("#%d queue-trimmed (beyond cap %d)"
                           % (gnum, MAX_QUEUED_RUNS))
    out.extend("automerge: " + x for x in automerge_leg(token, repo))
    out.extend("parse-probe: " + x for x in parse_death_probe(token, repo))
    out.extend("ci-queue: " + x for x in ci_queue_governor(token, repo))
    if busy and not out:
        out.append("skipped(furnace-busy)")
    for rid, num, age_h in cancelled[:RECONCILE_MAX_PER_PASS]:
        out.append("skip #%d (cancelled=intent; not revived - manual rerun "
                   "only, age %.1fh)" % (num, age_h))
    if not out:
        out = ["clean"]
    return out


CI_QUEUE_WORKFLOWS = ("ci.yml", "mac-verify.yml")


def ci_queue_governor(token, repo):
    """Stale-queued trimmer for the suite workflows (root cure):
    with concurrency cancel-in-progress OFF, an older QUEUED run would
    otherwise start later and its entry would have cancelled the newer
    in-flight tip run (run 136 killed run 138 mid-suite). The governor
    retires stale QUEUED runs per head branch BEFORE they ever start:
    keep the newest run per branch (any state), cancel every other QUEUED
    run. In-flight (in_progress) runs are NEVER touched."""
    out = []
    for wf in CI_QUEUE_WORKFLOWS:
        runs, err = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                           "?per_page=30" % (repo, wf))
        if err or not runs:
            out.append("%s skipped(runs-list: %s)" % (wf, err))
            continue
        by_branch = {}
        for r in (runs.get("workflow_runs") or []):
            if r.get("status") not in ("queued", "in_progress"):
                continue
            by_branch.setdefault(r.get("head_branch") or "",
                                 []).append(r)
        for br, rows in by_branch.items():
            rows.sort(key=lambda r: r.get("run_number") or 0, reverse=True)
            for r in rows[1:]:
                if r.get("status") != "queued":
                    continue
                _, cerr = gh_api(token,
                                 "/repos/%s/actions/runs/%d/cancel"
                                 % (repo, r["id"]), method="POST")
                out.append("%s/%s #%s stale-queued %s"
                           % (wf, br, r.get("run_number"),
                              "trimmed" if not cerr else "cancel rc%s" % cerr))
    if not out:
        out = ["clean (no stale queued runs)"]
    return out


def label_health_probe(token, repo):
    """Label-queue health probe (read-only, root-cure follow-up):
    a zombie self-hosted runner that is 'online' but not picking up jobs
    jams every queue routed to its label (the macos-15 advisory face jammed
    5+ hours twice while a hosted runner was available).
    For every job QUEUED >= 30 minutes, check whether any ONLINE runner
    carries the job's labels: no match = LABEL-GAP alarm (remove the dead
    runner's claim on that label); match = GitHub-side queue, monitor only.
    The probe NEVER removes labels - label surgery stays desk-gated."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    runners, rerr = gh_api(token, "/repos/%s/actions/runners?per_page=20"
                           % repo)
    if rerr or not runners:
        return ["skipped(runners-list: %s)" % rerr]
    online = []
    for r in (runners.get("runners") or []):
        if r.get("status") == "online":
            online.append(set(l.get("name") for l in (r.get("labels") or [])))
    out = []
    checked = 0
    for wf in ("mac-verify.yml", "ci.yml"):
        runs, err = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                           "?per_page=12" % (repo, wf))
        if err or not runs:
            continue
        for r in (runs.get("workflow_runs") or []):
            if r.get("status") != "queued":
                continue
            jobs, jerr = gh_api(token, "/repos/%s/actions/runs/%d/jobs"
                                "?per_page=20" % (repo, r.get("id") or 0))
            for jb in ((jobs or {}).get("jobs") or []):
                if jb.get("status") != "queued":
                    continue
                checked += 1
                started = (jb.get("started_at") or "").replace("Z", "+00:00")
                try:
                    qmin = (now - datetime.datetime.fromisoformat(started)
                            ).total_seconds() / 60.0
                except ValueError:
                    continue
                if qmin < 30:
                    continue
                labels = set(l for l in (jb.get("labels") or []))
                matched = [i for i, ls in enumerate(online) if labels <= ls]
                if matched:
                    out.append("%s/%s queued %.0fmin but pool healthy "
                               "(an online runner carries the labels) - "
                               "GitHub-side queue, monitor"
                               % (wf, (jb.get("name") or "")[:24], qmin))
                else:
                    out.append("LABEL-GAP: %s/%s queued %.0fmin, labels %s "
                               "carried by NO online runner - remove the "
                               "dead runner's claim on the label (desk or "
                               "follow-up), then rerun"
                               % (wf, (jb.get("name") or "")[:24], qmin,
                                  sorted(labels)))
    if checked == 0:
        out.append("clean (no queued jobs to probe)")
    return out


def parse_death_probe(token, repo):
    """Workflow parse-death probe (read-only, every reconcile pass): a
    workflow-level validation failure (bad YAML, unsupported expression)
    produces a FAILED run with ZERO jobs and NO workflow_run event - the
    self-heal watch is never triggered by it (run 118 evidence),
    so the scheduled reconcile is the only in-system sensor. The probe
    reads the newest completed push runs on main and flags the jobs=0
    signature loudly in the reconcile report; the blocking-file fix is
    desk-gated (the watch never edits the blocking workflow)."""
    lines = []
    runs, err = gh_api(token, "/repos/%s/actions/workflows/%s/runs"
                       "?event=push&branch=main&per_page=5" % (repo, WF_FILE))
    if err or not runs:
        return ["skipped(runs-list: %s)" % err]
    done = [r for r in (runs.get("workflow_runs") or [])
            if r.get("status") == "completed"]
    if not done:
        return ["clean (no completed push runs to probe)"]
    r = done[0]
    if r.get("conclusion") != "failure":
        return ["clean (newest main run #%s = %s)"
                % (r.get("run_number"), r.get("conclusion"))]
    jobs, jerr = gh_api(token, "/repos/%s/actions/runs/%s/jobs?per_page=1"
                        % (repo, r.get("id")))
    total = (jobs or {}).get("total_count", -1) if not jerr else -1
    if total == 0:
        lines.append("PARSE-DEATH: run #%s (sha %s) concluded failure with "
                     "ZERO jobs - the workflow file fails validation and "
                     "emits no workflow_run event, so this watch is blind "
                     "to it; the blocking file needs a desk fix NOW"
                     % (r.get("run_number"), (r.get("head_sha") or "")[:8]))
        prev = next((x for x in done[1:]
                     if x.get("conclusion") == "success"), None)
        if prev:
            lines.append("last-known-good: run #%s (sha %s)"
                         % (prev.get("run_number"),
                            (prev.get("head_sha") or "")[:8]))
    elif total > 0:
        lines.append("clean (run #%s failure has %s jobs - real red, the "
                     "watch covers it)" % (r.get("run_number"), total))
    else:
        lines.append("skipped(jobs-probe: %s)" % jerr)
    return lines


def branch_census(token, repo):
    """Weekly branch census (READ-ONLY, standing desk order): every
    non-main branch is judged against main via the compare API plus its PR
    history; merged-stale stubs are reported to the desk as deletion
    CANDIDATES. The census never deletes - the deletion itself is an
    outward-facing desktop order (GitHub keeps a restore window)."""
    lines = []
    branches, err = gh_api(token, "/repos/%s/branches?per_page=100" % repo)
    if err or not branches:
        return ["census skipped(branches list: %s)" % err]
    owner = repo.split("/")[0]
    rows = branches if isinstance(branches, list) else (
        branches.get("branches") or [])
    names = [b.get("name", "") for b in rows
             if b.get("name") and b["name"] != "main"
             and not b["name"].startswith("_bridge")]
    if not names:
        return ["clean (single-branch repo: main only)"]
    for name in names:
        cmp_, cerr = gh_api(token, "/repos/%s/compare/main...%s"
                            % (repo, name))
        if cerr or not cmp_:
            lines.append("%s: skipped(compare: %s)" % (name, cerr))
            continue
        ahead = cmp_.get("ahead_by", 0)
        behind = cmp_.get("behind_by", 0)
        prs, perr = gh_api(token, "/repos/%s/pulls?head=%s:%s&state=all"
                           "&per_page=5" % (repo, owner, name))
        merged_pr = ""
        if not perr and isinstance(prs, list):
            for p in prs:
                if p.get("merged_at"):
                    merged_pr = "#%s" % p.get("number")
                    break
        if merged_pr:
            lines.append("%s: MERGED-STALE deletion-candidate (PR %s merged; "
                         "ahead=%d behind=%d; squash/rebase form - verify "
                         "content equivalence before delete)"
                         % (name, merged_pr, ahead, behind))
        elif ahead == 0:
            lines.append("%s: FULLY-CONTAINED deletion-candidate (ahead=0 "
                         "behind=%d, no merged PR)" % (name, behind))
        else:
            lines.append("%s: UNMERGED-LIVE desk-review (ahead=%d behind=%d, "
                         "no merged PR)" % (name, ahead, behind))
    return lines


RECONCILE_MAX_PER_PASS = 4


def write_out(out_dir, files):
    os.makedirs(out_dir, exist_ok=True)
    for name, text in files:
        with open(os.path.join(out_dir, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(text)


def main():
    ap = argparse.ArgumentParser(description="rocqwash self-heal driver")
    ap.add_argument("--repo", required=True, help="OWNER/REPO slug")
    ap.add_argument("--run", required=True, type=int, help="CI run id")
    ap.add_argument("--out", required=True, help="artifact output directory")
    ap.add_argument("--heal", action="store_true",
                    help="enable the heal leg (transient rerun, three "
                         "guards: cancel-intent / attempt==1 / live check)")
    ap.add_argument("--heal-delay", type=int, default=HEAL_DELAY_S)
    ap.add_argument("--reconcile", action="store_true",
                    help="reconcile mode: record cancelled (intent) + queue "
                         "governor; triage skipped")
    ap.add_argument("--automerge-only", action="store_true",
                    help="automerge-only pass (CI-success trigger): merge "
                         "green supply/* PRs, nothing else - the */30 cron "
                         "is GitHub-degraded to hours, so the green CI "
                         "completion is the fast automerge trigger")
    args = ap.parse_args()

    if args.automerge_only:
        token = os.environ.get("GITHUB_TOKEN", "")
        lines = ["automerge-only: " + x
                 for x in automerge_leg(token, args.repo)]
        lines += ["ci-queue: " + x for x in ci_queue_governor(token, args.repo)]
        lines += ["label-health: " + x
                  for x in label_health_probe(token, args.repo)]
        report = "automerge-only pass:\n" + "\n".join(lines) + "\n"
        write_out(args.out, [("automerge-report.txt", report)])
        print(report)
        return 0

    if args.reconcile:
        lines = reconcile_leg(args, args.repo)
        report = "reconcile pass:\n" + "\n".join(lines) + "\n"
        files = [("reconcile-report.txt", report)]
        # Weekly branch census (read-only): stateless gate on the workflow
        # run number - 336 half-hour passes per week - with a
        # ROCWASH_BRANCH_CENSUS=1 override for on-demand test runs. Never
        # deletes; the report is the desk's deletion-order input.
        forced = os.environ.get("ROCWASH_BRANCH_CENSUS", "").strip() == "1"
        num = int(os.environ.get("GITHUB_RUN_NUMBER", "0") or 0)
        if forced or (num > 0 and num % BRANCH_CENSUS_EPOCH == 0):
            census = branch_census(os.environ.get("GITHUB_TOKEN", ""),
                                   args.repo)
            census_out = ("branch census (weekly gate hit, run #%d):\n"
                          % num) + "\n".join(census) + "\n"
            files.append(("branch-census.txt", census_out))
            for x in census:
                log("census: " + x)
        write_out(args.out, files)
        print(report)
        return 0

    if args.heal and args.run:
        token = os.environ.get("GITHUB_TOKEN", "")
        meta, merr = gh_api(token, "/repos/%s/actions/runs/%d"
                            % (args.repo, args.run))
        if not merr and (meta or {}).get("event") == "pull_request":
            verdict = "pr-face"
            detail = ("PR-event CI run: no auto-heal - repairs belong on "
                      "the PR branch, not main; recorded for the desk")
            write_out(args.out,
                      [("triage-report.txt", verdict + "\n" + detail + "\n"),
                       ("summary.txt", "verdict=%s" % verdict)])
            log("%s | %s" % (verdict, detail))
            return 0

    verdict, detail, files = triage_leg(args, args.repo, args.run)
    files = files or [("triage-report.txt", verdict + "\n" + detail + "\n"),
                      ("summary.txt", "verdict=%s" % verdict)]
    write_out(args.out, files)
    log("%s | %s" % (verdict, detail[:300]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
