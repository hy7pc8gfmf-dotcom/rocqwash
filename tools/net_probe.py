#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net_probe.py - network-window probe (rocqwash tools/).
Purpose.  Probe all endpoints with a bare GET and decide the dual-probe
  stability window (a single-probe round must not initiate): with
  --stable-window the window holds only when every endpoint is reachable
  in every round; without it exit 0 only means the probe completed.
  Reachable = any HTTP status from urlopen(url, timeout=12), 500/400
  included; URLError, timeout or DNS failure = unreachable (http_code=null);
  HTTPError subclasses URLError, so exceptions pass classify_error first.
  The unverifiable-outcome registration and the target-evidence rule are
  in the extended contract below.
Interface.  python3 tools/net_probe.py [--endpoints URL[,URL...]]
  [--rounds N] [--interval S] [--stable-window] [--jitter S] [--seed N]
  [--json out.json] | --selftest.  The defaults, the jitter semantics,
  the report schema, and the registration-key rules are in the extended
  contract.
Dependencies.  Python 3 standard library only; zero network under --selftest.
Evidence.  --selftest frozen vector group V1-V9; suite lane t_net_probe
  (tests/test_net_probe.py).
Exit-codes.  0 = probe completed and, with --stable-window, the window
  held; 1 = unstable window; 2 = usage error or report write failure.
"""

# Extended contract (kept outside the five-field header so the header
# stays within the 30-line budget of the annotation standard; the moved
# facts are carried over from the former header verbatim in substance):
#
# Unverifiable outcomes.  A failure whose error says nothing about the
#   target's existence or state (TLS handshake blocked, DNS failure,
#   connection timeout) is registered as "unverifiable" on the endpoint
#   entry, never as a claim about the target (unreachable is not
#   nonexistent; the MIT dashboard TLS-block precedent); target-evidence
#   failures (connection refused and friends) stay plain failures.
# Defaults and jitter.  --rounds 1 (>= 1), --interval 60 (>= 0, no sleep
#   after the last round), jitter off, default `DEFAULT_ENDPOINTS`
#   (--endpoints overrides); --jitter S (>= 0) sleeps uniform(0, S)
#   before each endpoint probe (--seed N pins the RNG; jitter_sec appears
#   only while --jitter > 0); --stable-window requires --rounds >= 2.
# Report schema rocqwash-net-probe/1: rounds[{at, endpoints[{url,
#   http_code, ok(, jitter_sec)(, status, reason_class, evidence,
#   registered_as)}]}], verdict (STABLE|UNSTABLE with --stable-window,
#   else all-up|partial|all-down); the four registration keys appear only
#   on unverifiable outcomes (status and registered_as = "unverifiable";
#   reason_class = tls-blocked | dns | timeout; evidence = the underlying
#   error text); existing ok and plain-failure entries carry no new keys;
#   writes deterministic, rounds[].at is wall-clock UTC (varies per
#   round).

import argparse
import io
import json
import os
import random
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROG = "net_probe"
SCHEMA = "rocqwash-net-probe/1"
TIMEOUT_SEC = 12
DEFAULT_ENDPOINTS = [
    "https://results-receiver-actions.githubusercontent.com",
    "https://productionresultssa1.blob.core.windows.net",
    "https://api.github.com",
    "https://github.com",
]

# Registration class for outcomes that cannot be verified: the probe could
# not reach the target for reasons that say nothing about the target's
# existence or state (unreachable does not mean nonexistent), so the report
# registers "unverifiable" instead of a plain failure red (an honest
# auditor registers cannot-verify, never a false alarm).
UNVERIFIABLE = "unverifiable"
REASON_TLS_BLOCKED = "tls-blocked"
REASON_DNS = "dns"
REASON_TIMEOUT = "timeout"

# DNS-resolution failure texts that surface as plain string reasons (the
# platform spellings of getaddrinfo failures); matched lowercase against
# the reason text of a URLError that carries no exception instance.
DNS_REASON_TEXTS = (
    "nodename nor servname",           # the BSD getaddrinfo spelling
    "name or service not known",       # the Linux getaddrinfo spelling
    "getaddrinfo failed",              # the desktop resolver spelling
    "temporary failure in name resolution",
    "no address associated",
)


def classify_error(exc):
    """Reachability classification: HTTPError (an HTTP status was received,
    the TLS/DNS stack resolved) -> reachable; everything else (URLError,
    timeout, DNS failure, bare OSError, any exception) -> unreachable.
    Canned exception instances can be injected directly (selftest
    zero-network vectors)."""
    return isinstance(exc, urllib.error.HTTPError)


def classify_unverifiable(exc):
    """Classify a probe exception into an unverifiable reason class.

    Returns REASON_TLS_BLOCKED, REASON_DNS or REASON_TIMEOUT when the
    failure says nothing about the target's existence or state: the probe
    path itself was blocked (a TLS handshake refused or torn down by a
    middlebox or policy, the MIT dashboard precedent; certificate
    verification failures are ssl.SSLError subclasses and ride the same
    class), the name did not resolve (DNS failure), or the connection
    attempt timed out.  Returns None when the error carries target
    evidence (an HTTP status was received, or the connection was actively
    refused) so the outcome stays a plain failure.  urlopen wraps the
    underlying transport error as URLError.reason, so both the exception
    itself and its .reason attribute are judged.
    """
    for face in (exc, getattr(exc, "reason", None)):
        if face is None:
            continue
        if isinstance(face, ssl.SSLError):
            return REASON_TLS_BLOCKED
        if isinstance(face, socket.gaierror):
            return REASON_DNS
        if isinstance(face, (socket.timeout, TimeoutError)):
            return REASON_TIMEOUT
    if isinstance(exc, urllib.error.URLError):
        text = str(getattr(exc, "reason", exc))
        lowered = text.lower()
        if "timed out" in lowered:
            return REASON_TIMEOUT
        if any(marker in lowered for marker in DNS_REASON_TEXTS):
            return REASON_DNS
    return None


def probe_once(url, timeout=TIMEOUT_SEC, _open=None):
    """Single-endpoint bare-GET probe -> (http_code: int|None, ok: bool,
    reason: str, reason_class: str|None).  reason_class carries the
    unverifiable registration class of a failure (classify_unverifiable)
    and is None for ok and plain-failure outcomes.  _open accepts a canned
    urlopen (selftest zero-network canned-exception injection point)."""
    opener = _open if _open is not None else urllib.request.urlopen
    try:
        resp = opener(url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - classify_error judges all
        ok = classify_error(exc)
        code = getattr(exc, "code", None) if ok else None
        reason = "%s: %s" % (type(exc).__name__, exc)
        return code, ok, reason, None if ok else classify_unverifiable(exc)
    code = getattr(resp, "status", None)
    if code is None and hasattr(resp, "getcode"):
        code = resp.getcode()
    close = getattr(resp, "close", None)
    if close:
        close()
    return code, True, "", None


def probe_round(endpoints, timeout=TIMEOUT_SEC, _open=None, jitter=0.0,
                rng=None, _sleep=None):
    """One full round over the endpoints (argument order) ->
    (entries[{url, http_code, ok(, jitter_sec)(, status, reason_class,
    evidence, registered_as)}], reasons{url: reason});
    reasons collects down endpoints only, feeds diagnostic stdout and never
    enters the JSON report.  Registration: a down endpoint whose error
    classifies unverifiable (classify_unverifiable) is registered as
    "unverifiable" on its entry with the four keys status, reason_class,
    evidence and registered_as, never as a claim about the target; ok and
    plain-failure entries gain no keys (backward-compatible shape).
    Resilience: when jitter > 0, sleep
    uniform(0, jitter) seconds before each endpoint probe (one independent
    draw per endpoint; rng defaults to the random module; _sleep is the
    injection point behind the selftest fixed-seed deterministic vectors);
    the draw is recorded in entry jitter_sec (additive key: jitter=0 means
    no key, no sleep, no behavior change)."""
    entries, reasons = [], {}
    do_sleep = _sleep if _sleep is not None else time.sleep
    r = rng if rng is not None else random
    for url in endpoints:
        jit = 0.0
        if jitter and jitter > 0:
            jit = r.uniform(0, jitter)
            do_sleep(jit)
        code, ok, reason, reason_class = probe_once(url, timeout=timeout,
                                                    _open=_open)
        entry = {"url": url, "http_code": code, "ok": ok}
        if jitter and jitter > 0:
            entry["jitter_sec"] = jit
        if not ok and reason_class is not None:
            entry["status"] = UNVERIFIABLE
            entry["reason_class"] = reason_class
            entry["evidence"] = reason
            entry["registered_as"] = UNVERIFIABLE
        entries.append(entry)
        if not ok:
            reasons[url] = reason
    return entries, reasons


def summarize_verdict(rounds):
    """Cross-round summary over all probes, three levels:
    all-up | partial | all-down (empty input defends as all-down; the CLI
    side rejects empty endpoint lists).  An unverifiable endpoint counts
    as not reached here: the verdict describes what this probe reached,
    and the per-entry registration (status/registered_as) is what
    separates cannot-verify from target-down."""
    probes = [e for r in rounds for e in r["endpoints"]]
    if not probes:
        return "all-down"
    ups = sum(1 for e in probes if e["ok"])
    if ups == len(probes):
        return "all-up"
    if ups == 0:
        return "all-down"
    return "partial"


def stable_window_holds(rounds):
    """Dual-probe stable-window criterion: a non-empty round set in which
    every endpoint is reachable in every round."""
    if not rounds:
        return False
    return all(e["ok"] for r in rounds for e in r["endpoints"])


def now_iso():
    """Round wall clock (UTC ISO, second precision).  rounds[].at is
    wall-clock UTC and varies per round: a round's report is that round's
    evidence, not invariant across rounds."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_report(path, report):
    """Deterministic report write (indent=1, ensure_ascii=False, sort_keys,
    newline="\\n")."""
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        print("FAIL-LOUD: report write failed %s: %s" % (path, exc),
              file=sys.stderr)
        sys.exit(2)


def run_args(argv, env=None):
    """Selftest helper: run this tool in a subprocess (stdout and stderr
    merged)."""
    import subprocess
    e = dict(os.environ) if env is None else dict(env)
    p = subprocess.run([sys.executable, "-B",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     PROG + ".py")] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def selftest():
    """Embedded frozen vector group (zero network, canned exception and
    response injection, zero compiles):
    V1 classify_error/probe_once classification: HTTPError (503/500/400) ->
       reachable with code; URLError -> unreachable; socket.timeout ->
       unreachable; canned response bodies 200/500 -> reachable with code
    V2 probe_round canned two-endpoint mix: entry shape and order; the
       canned DNS-text error rides the dns class; reasons collects down
       endpoints only
    V3 verdict three levels: all-up/partial/all-down (single round + mixed
       rounds + empty-input defense)
    V4 stable window, three decisions: two passing rounds -> True; a drop
       in the first round -> False; a drop in a later round -> False
       (empty input -> False)
    V5 CLI usage codes: --help -> 0; --bogus -> 2; --rounds 0 -> 2;
       --stable-window --rounds 1 -> 2; --endpoints empty -> 2; --endpoints
       missing scheme -> 2; --interval negative -> 2; --jitter negative -> 2
    V6 report write determinism: the same canned report written twice
       yields identical bytes
    V7 fixed-seed jitter determinism: same seed, same draw order; different
       seed, different order; bounds [0, S]; one draw per endpoint; draws
       recorded in jitter_sec; default jitter=0 means no key, no sleep, no
       behavior change
    V8 unverifiable registration (canned, per reason class, zero network):
       TLS handshake blocked (direct ssl.SSLError and the URLError-wrapped
       face), DNS failure (gaierror instance and the platform text
       spellings), connection timeout (socket.timeout and the URLError
       "timed out" reason); each carries status/reason_class/evidence/
       registered_as on the entry with registered_as = unverifiable
    V9 default path untouched: ok entries and target-evidence failures
       (connection refused) keep the exact legacy entry shape with no new
       keys, and the verdict/stable-window semantics read ok only (an
       unverifiable endpoint counts as not reached)
    """
    import shutil
    import tempfile

    class FakeResp(object):
        """Canned response body (urlopen stand-in, zero network)."""
        def __init__(self, status):
            self.status = status

        def close(self):
            pass

    def canned_open(resp=None, exc=None):
        def _open(url, timeout=None):
            if exc is not None:
                raise exc
            return resp
        return _open

    tmp = tempfile.mkdtemp(prefix="rocqwash_net_self_")
    try:
        # ---- V1 classification ----
        for code in (503, 500, 400):
            he = urllib.error.HTTPError("https://x", code,
                                        "HTTP Error %d" % code, None, None)
            assert classify_error(he) is True, \
                "HTTPError must be reachable: %d" % code
            got = probe_once("https://x", _open=canned_open(exc=he))
            assert got[0] == code and got[1] is True, got
        ue = urllib.error.URLError("[Errno 8] nodename nor servname provided")
        assert classify_error(ue) is False, "URLError must be unreachable"
        got = probe_once("https://x", _open=canned_open(exc=ue))
        assert got[0] is None and got[1] is False and "URLError" in got[2], got
        to = socket.timeout("timed out")
        got = probe_once("https://x", _open=canned_open(exc=to))
        assert got[0] is None and got[1] is False, got
        got = probe_once("https://x", _open=canned_open(resp=FakeResp(200)))
        assert got[0] == 200 and got[1] is True, got
        got = probe_once("https://x", _open=canned_open(resp=FakeResp(500)))
        assert got[0] == 500 and got[1] is True, "500 reachable means healthy"

        # ---- V2 probe_round shape ----
        ok_url, dead_url = "https://ok.example", "https://dead.example"

        def mixed_open(url, timeout=None):
            if url == ok_url:
                return FakeResp(200)
            raise ue
        entries, reasons = probe_round([ok_url, dead_url], _open=mixed_open)
        # The ok entry keeps the exact legacy shape; the dead entry's
        # canned error is the platform DNS-failure text, so it rides the
        # dns class and carries the registration keys (V8 judges the
        # key-by-key shape; the ok entry shape is asserted exactly here).
        assert entries[0] == {"url": ok_url, "http_code": 200,
                              "ok": True}, entries
        d0 = entries[1]
        assert d0["url"] == dead_url and d0["http_code"] is None \
            and d0["ok"] is False, d0
        assert d0["status"] == UNVERIFIABLE \
            and d0["registered_as"] == UNVERIFIABLE \
            and d0["reason_class"] == REASON_DNS, d0
        assert "URLError" in d0["evidence"], d0
        assert list(reasons) == [dead_url] and "URLError" in reasons[dead_url], \
            reasons

        # ---- V3 verdict levels ----
        up = {"endpoints": [{"url": "a", "http_code": 200, "ok": True}]}
        down = {"endpoints": [{"url": "b", "http_code": None, "ok": False}]}
        assert summarize_verdict([up]) == "all-up"
        assert summarize_verdict([up, up]) == "all-up"
        assert summarize_verdict([up, down]) == "partial"
        assert summarize_verdict([down]) == "all-down"
        assert summarize_verdict([]) == "all-down"

        # ---- V4 stable-window decisions ----
        assert stable_window_holds([up, up]) is True, \
            "two passing rounds must be STABLE"
        assert stable_window_holds([up, down]) is False, \
            "a later-round drop must be UNSTABLE"
        assert stable_window_holds([down, up]) is False, \
            "a first-round drop must be UNSTABLE"
        assert stable_window_holds([]) is False, "empty-input defense"

        # ---- V5 CLI usage codes ----
        p = run_args(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        for vec in (["--bogus"],
                    ["--rounds", "0"],
                    ["--stable-window", "--rounds", "1"],
                    ["--endpoints", "  "],
                    ["--endpoints", "ftp://x.example,https://y.example"],
                    ["--interval", "-1"],
                    ["--jitter", "-1"]):
            p = run_args(vec)
            assert p.returncode == 2, "usage error must be rc=2 (%d): %s" \
                % (p.returncode, vec)

        # ---- V6 report write determinism ----
        fixed = {"schema": SCHEMA,
                 "rounds": [{"at": "2026-11-11T00:00:00Z", "endpoints": [
                     {"url": "https://a", "http_code": 200, "ok": True}]}],
                 "verdict": "all-up"}
        j1 = os.path.join(tmp, "n1.json")
        j2 = os.path.join(tmp, "n2.json")
        write_report(j1, fixed)
        write_report(j2, fixed)
        assert io.open(j1, "rb").read() == io.open(j2, "rb").read(), \
            "json byte drift is a violation"
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "all-up", rep

        # ---- V7 fixed-seed jitter determinism (canned all-up probes) ----
        eps = ["https://a.example", "https://b.example", "https://c.example"]

        def up_open(url, timeout=None):
            return FakeResp(200)

        slept_a, slept_b, slept_c = [], [], []
        ea, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(2026), _sleep=slept_a.append)
        eb, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(2026), _sleep=slept_b.append)
        ec, _ = probe_round(eps, _open=up_open, jitter=0.5,
                            rng=random.Random(7), _sleep=slept_c.append)
        assert slept_a == slept_b, "same seed, same draws: %s vs %s" \
            % (slept_a, slept_b)
        assert slept_c != slept_a, "different seed, different draw order"
        assert len(slept_a) == 3, "one draw per endpoint, got %d" \
            % len(slept_a)
        assert all(0.0 <= s <= 0.5 for s in slept_a), slept_a
        assert [e["jitter_sec"] for e in ea] == slept_a, \
            "draws must be recorded in jitter_sec"
        assert all(set(e) == {"url", "http_code", "ok", "jitter_sec"}
                   for e in ea), ea
        ed, _ = probe_round(eps, _open=up_open)   # default jitter=0
        assert all(set(e) == {"url", "http_code", "ok"} for e in ed), \
            "default means no key and no behavior change"
        assert ed == [{"url": u, "http_code": 200, "ok": True} for u in eps], ed

        # ---- V8 unverifiable registration per reason class (canned
        # exceptions, zero network): each carries the four registration
        # keys on the entry with registered_as = unverifiable.
        tls = ssl.SSLError("SSL: HANDSHAKE_FAILURE_ALERT received")
        got = probe_once("https://x", _open=canned_open(exc=tls))
        assert got[1] is False and got[3] == REASON_TLS_BLOCKED, got
        tls_wrapped = urllib.error.URLError(tls)
        got = probe_once("https://x", _open=canned_open(exc=tls_wrapped))
        assert got[3] == REASON_TLS_BLOCKED, got
        dns_inst = socket.gaierror(8, "nodename nor servname provided")
        got = probe_once("https://x", _open=canned_open(exc=dns_inst))
        assert got[3] == REASON_DNS, got
        dns_wrapped = urllib.error.URLError(dns_inst)
        got = probe_once("https://x", _open=canned_open(exc=dns_wrapped))
        assert got[3] == REASON_DNS, got
        dns_text = urllib.error.URLError(
            "[Errno -2] Name or service not known")
        got = probe_once("https://x", _open=canned_open(exc=dns_text))
        assert got[3] == REASON_DNS, got
        to_inst = socket.timeout("timed out")
        got = probe_once("https://x", _open=canned_open(exc=to_inst))
        assert got[3] == REASON_TIMEOUT, got
        to_wrapped = urllib.error.URLError(OSError("timed out"))
        got = probe_once("https://x", _open=canned_open(exc=to_wrapped))
        assert got[3] == REASON_TIMEOUT, got

        def tls_open(url, timeout=None):
            raise tls_wrapped

        ev, _ = probe_round(["https://dashboard.example"], _open=tls_open)
        e0 = ev[0]
        assert e0["url"] == "https://dashboard.example" \
            and e0["http_code"] is None and e0["ok"] is False, e0
        assert e0["status"] == UNVERIFIABLE \
            and e0["registered_as"] == UNVERIFIABLE \
            and e0["reason_class"] == REASON_TLS_BLOCKED, e0
        assert "URLError" in e0["evidence"], e0
        assert set(e0) == {"url", "http_code", "ok", "status",
                           "reason_class", "evidence",
                           "registered_as"}, e0

        # ---- V9 default path untouched: ok entries and target-evidence
        # failures (connection refused) keep the exact legacy entry shape,
        # no new keys anywhere; the verdict and stable-window semantics
        # read ok only, so unverifiable counts as not reached.
        refused = urllib.error.URLError(OSError(111, "Connection refused"))

        def refused_open(url, timeout=None):
            raise refused

        er, _ = probe_round(["https://refused.example"],
                            _open=refused_open)
        assert er == [{"url": "https://refused.example",
                       "http_code": None, "ok": False}], er

        def up_open9(url, timeout=None):
            return FakeResp(200)

        eu, _ = probe_round(["https://up.example"], _open=up_open9)
        assert eu == [{"url": "https://up.example",
                       "http_code": 200, "ok": True}], eu
        assert summarize_verdict(
            [{"endpoints": ev}, {"endpoints": er}]) == "all-down", \
            "unverifiable counts as not reached (reachability semantics)"
        assert stable_window_holds([{"endpoints": ev}]) is False, \
            "an unverifiable round does not open the stable window"

        print("NET-PROBE-SELFTEST PASS: classification (HTTPError reachable,"
              " URLError/timeout unreachable, canned 200/500)/round shape and"
              " reasons/verdict levels/stable-window decisions/CLI usage"
              " codes/byte-identical report writes/fixed-seed jitter"
              " determinism/unverifiable registration (tls-blocked, dns,"
              " timeout)/default path untouched - nine sections all pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="network-window probe: bare-GET all-endpoint reachability"
                    " over N rounds with the dual-probe stable-window decision"
                    " (preflight check: --stable-window exits 0 only when"
                    " every round reaches every endpoint)")
    ap.add_argument("--endpoints", default=None, metavar="URL[,URL...]",
                    help="endpoint list (four defaults, comma-separated"
                         " override)")
    ap.add_argument("--rounds", type=int, default=1, metavar="N",
                    help="probe rounds (default 1, >= 1)")
    ap.add_argument("--interval", type=float, default=60.0, metavar="S",
                    help="seconds between rounds (default 60, no sleep after"
                         " the last round)")
    ap.add_argument("--stable-window", action="store_true",
                    dest="stable_window",
                    help="stable-window check: exit 0 only when rounds >= 2"
                         " and every round reaches every endpoint")
    ap.add_argument("--jitter", type=float, default=0.0, metavar="S",
                    help="random pre-probe jitter seconds per endpoint"
                         " (uniform(0, S), default 0 = off, >= 0)")
    ap.add_argument("--seed", type=int, default=None, metavar="N",
                    help="jitter random seed (default system entropy; a fixed"
                         " seed gives determinism)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="probe report output path (schema"
                         " rocqwash-net-probe/1)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    endpoints = list(DEFAULT_ENDPOINTS)
    if args.endpoints is not None:
        endpoints = [u.strip() for u in args.endpoints.split(",") if u.strip()]
        if not endpoints:
            print("FAIL-LOUD: --endpoints expands to an empty list",
                  file=sys.stderr)
            sys.exit(2)
        for u in endpoints:
            if not (u.startswith("http://") or u.startswith("https://")):
                print("FAIL-LOUD: endpoint lacks an http(s) scheme: %s" % u,
                      file=sys.stderr)
                sys.exit(2)
    if args.rounds < 1:
        print("FAIL-LOUD: --rounds must be >= 1, got %d" % args.rounds,
              file=sys.stderr)
        sys.exit(2)
    if args.interval < 0:
        print("FAIL-LOUD: --interval must be >= 0, got %s" % args.interval,
              file=sys.stderr)
        sys.exit(2)
    if args.stable_window and args.rounds < 2:
        print("FAIL-LOUD: --stable-window requires --rounds >= 2 (a"
              " single-probe round must not initiate)", file=sys.stderr)
        sys.exit(2)
    if args.jitter < 0:
        print("FAIL-LOUD: --jitter must be >= 0, got %s" % args.jitter,
              file=sys.stderr)
        sys.exit(2)
    rng = random.Random(args.seed)

    print("=== NET-PROBE ===")
    print("rounds=%d interval=%ss timeout=%ss stable_window=%s endpoints=%d"
          % (args.rounds, args.interval, TIMEOUT_SEC, args.stable_window,
             len(endpoints))
          + (" jitter=%gs seed=%s" % (args.jitter, args.seed)
             if args.jitter > 0 else ""))
    rounds = []
    for i in range(args.rounds):
        if i > 0:
            time.sleep(args.interval)
        at = now_iso()
        entries, reasons = probe_round(endpoints, jitter=args.jitter, rng=rng)
        rounds.append({"at": at, "endpoints": entries})
        ups = sum(1 for e in entries if e["ok"])
        print("round %d @%s: %d/%d up" % (i + 1, at, ups, len(entries)))
        for e in entries:
            mark = " UP " if e["ok"] else "DOWN"
            code = str(e["http_code"]) if e["http_code"] is not None else "--"
            reason = (" (%s)" % reasons[e["url"]]) if not e["ok"] else ""
            print("  [%s] %s %s%s" % (mark, code, e["url"], reason))

    verdict = ("STABLE" if stable_window_holds(rounds) else "UNSTABLE") \
        if args.stable_window else summarize_verdict(rounds)
    if args.json:
        write_report(args.json, {"schema": SCHEMA, "rounds": rounds,
                                 "verdict": verdict})
        print("json ->", args.json)
    print("verdict: %s" % verdict)
    if args.stable_window:
        if verdict == "UNSTABLE":
            print("FAIL: stable window does not hold (UNSTABLE; any down"
                  " endpoint in any round bars initiation)", file=sys.stderr)
            sys.exit(1)
        print("STABLE-WINDOW OK (all rounds all endpoints passing; clear to"
              " initiate)")
    sys.exit(0)


if __name__ == "__main__":
    main()
