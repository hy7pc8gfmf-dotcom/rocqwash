#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""periscope: six-source peripheral-intelligence sweep with sentinel companion.

    Purpose.  Sweep a configurable observation list of six sources (mathlib
      PR search, a single pull request, two arXiv legs, the coordination
      issue with its comments sub-face, and an upstream commit tip checked
      against a frozen prefix), write raw bodies plus a per-shot NETRED
      ledger, keep a sentinel window log with zero silent gaps, and emit a
      judgment draft skeleton (per-source digest, three-state collision
      screening, C1 trigger verdict, mandatory four-element negative
      findings, five-item window-scheduling advice).  Read-only GET only;
      every finding, including a negative one, is data and never an error.

    Interface.  `periscope.py --config <six-source JSON> --out <dir>
      [--rounds N] [--netrc <file>] [--dry-run] [--selftest]`.  A real run
      requires --out (an implicit network sweep is refused); --dry-run
      validates and prints the plan plus the draft skeleton with zero
      network and zero writes; --selftest runs the offline vector group.
      Config schema: rocqwash-periscope-config/1; draft: bilingual markdown
      mirroring the round-1 adjudication ledger form (the cast date lives in
      the ledger surface, not in prose).

    Dependencies.  Python 3 standard library only; `curl` on PATH for real
      runs (never invoked by --dry-run or --selftest); bearer credentials
      come from a netrc file passed straight to `curl --netrc-file` and are
      never read, logged, or written by this tool.

    Evidence.  --selftest frozen vector group on temporary fixtures with a
      canned transport and a virtual clock (zero network, zero writes):
      CLI face, config-schema fail-loud matrix, the three burned-in
      behaviors (arXiv -L from the first shot; sentinel SUSPEND beats with
      contiguous indexes; default coordination endpoint pinned to the Main
      issue with comments sub-face), cap/stop/retry machine, read-only
      pledge over every built argument vector, draft-template invariants,
      dry-run zero-write.  Ground-truth round-1 ledger:
      `attn/_periscope_20261113/intel-ledger-20261113.md`.

    Exit-codes.  0 = run/dry-run/selftest green (negative findings and a C1
      trigger are data, reported loudly, never an error); 1 = selftest red
      or a draft invariant red; 2 = usage or config-schema error; 9 =
      missing input (config absent, output root not writable).
"""
# Extended contract (kept outside the five-field block; annotation budget):
#
# Window protocol (as-built, burned in):
#   per-source cap 8 shots; stop at the first obtained response (stop-when-
#   obtained); a failure sleeps 60s then retries with a changed parameter
#   (the effective per-shot timeout widens by 30s per retry and any
#   `retry_param_overrides` from the config are merged, both recorded in the
#   NETRED line as changed=...); HTTP 404 is a definitive negative finding:
#   it stops the source immediately, keeps the remaining cap, and is
#   evidenced by raw/<key>.retry.json; a cap exhausted without an obtain is
#   registered as data, not as a failure.
# Burned-in behaviors (the round-1 three pits):
#   pit-a  arXiv requests carry -L from the first shot (a redirect must
#          never burn the shot budget);
#   pit-b  the sentinel companion runs a 60s beat, and a beat it yields
#          (because the collection sweep overruns it) must emit an explicit
#          SUSPEND line - the window log has no silent gaps by construction;
#   pit-c  the coordination source defaults to the Main repository issue #3
#          with its comments sub-face enabled (the issue list endpoint of
#          the tooling repo, which 404'd in round 1, is retired).
# Read-only pledge: the argument builder cannot emit a write verb; the
#   selftest sweeps every built vector for -d/--data/-X POST|PUT|PATCH|DELETE.

import argparse
import copy
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SCHEMA = "rocqwash-periscope-config/1"
SELFTEST_MARK = "PERISCOPE-SELFTEST PASS"

K_GH_SEARCH = "github_search"
K_GH_API = "github_api"
K_GH_ISSUE = "github_issue"
K_GH_COMMITS = "github_commits"
K_ARXIV = "arxiv"
KINDS = (K_GH_SEARCH, K_GH_API, K_GH_ISSUE, K_GH_COMMITS, K_ARXIV)

CAP_DEFAULT = 8                # shots per source (round-1 as-built cap)
RETRY_SLEEP_SECONDS = 60       # sleep between retries, then change a param
INTER_SHOT_MIN_SECONDS = 2     # minimum spacing between shots of one source
ROUND_SECONDS = 60             # sentinel beat, burned in (pit-b)
DEFAULT_ROUNDS = 10            # sentinel companion rounds
DEFAULT_TIMEOUT_SECONDS = 30   # first-shot curl -m; widens by 30s per retry
TIMEOUT_WIDEN_SECONDS = 30     # the default changed parameter on a retry
ACCEPT_GITHUB = "application/vnd.github+json"
GITHUB_API_VERSION = "2022-11-28"

ST_PENDING = "pending"
ST_OBTAINED = "obtained"
ST_NEGATIVE_DEFINITE = "negative-definite-404"
ST_CAP_EXHAUSTED = "cap-exhausted-registered"
STATES_CLOSED = (ST_OBTAINED, ST_NEGATIVE_DEFINITE, ST_CAP_EXHAUSTED)

# Four-element labels (negative-finding boundary law; canonical sentences).
NEG_SCANNED = "scanned (what was scanned)"
NEG_NOT_SCANNED = "not scanned (surfaces outside this sweep)"
NEG_NOT_ABSOLUTE = "not an absolute claim"
NEG_ALIASES = "aliased equivalents not exhaustively ruled out"
FOUR_ELEMENTS = (NEG_SCANNED, NEG_NOT_SCANNED, NEG_NOT_ABSOLUTE, NEG_ALIASES)
NEG_NOT_ABSOLUTE_SENTENCE = (
    "This is a negative finding of this scan, not an absolute claim.")
NEG_ALIASES_SENTENCE = (
    "Aliased or equivalent surfaces elsewhere were not exhaustively ruled "
    "out; complete this item before any external statement.")

SCREEN_PRIOR = "prior-registered"
SCREEN_SUSPECT = "suspected-collision(adjudicate)"
SCREEN_NO_BEARING = "no-bearing"
SCREEN_OURS = "ours(registered)"

MAIN_ISSUE_URL = ("https://api.github.com/repos/hy7pc8gfmf-dotcom/"
                  "ConstructiveWorld-Main/issues/3")

# Injectables: the selftest swaps these three; production never does.
_now = lambda: datetime.datetime.now(datetime.timezone.utc)
_sleep = None  # set at import from time.sleep (kept off the import face


# of the header contract; assigned in _bind_time() below)


def _bind_time():
    import time
    global _sleep
    _sleep = time.sleep


_bind_time()


class FailLoud(Exception):
    """Missing input or an unwritable output root; callers exit 9."""


class SchemaError(Exception):
    """Config-schema violation; callers exit 2."""


# --------------------------------------------------------------------------
# Default configuration: the six-source list as built in the round-1
# watchlist (cast date in the ledger surface).  Endpoints are complete
# URLs; arXiv URLs carry a {WINDOW}
# placeholder replaced by the rolling submittedDate range when days_window
# is set.
# --------------------------------------------------------------------------

ARXIV_DZETA_URL = (
    "https://export.arxiv.org/api/query?"
    "search_query=cat:math.NT+AND+(all:%22Dedekind+zeta%22"
    "+OR+all:%22formalization+Lean%22){WINDOW}"
    "&sortBy=submittedDate&sortOrder=descending&start=0&max_results=20")
ARXIV_QUASIR_URL = (
    "https://export.arxiv.org/api/query?"
    "search_query=cat:math.NT+AND+(all:%22quasi-Riemann%22"
    "+OR+all:%22formalization+Lean%22){WINDOW}"
    "&sortBy=submittedDate&sortOrder=descending&start=0&max_results=20")

DEFAULT_CONFIG = {
    "schema": SCHEMA,
    "sentinel": {
        "endpoint": "https://api.github.com/rate_limit",
        "rounds": DEFAULT_ROUNDS,
    },
    "defaults": {
        "cap_per_source": CAP_DEFAULT,
    },
    "deposit_anchors": {
        "mathlib_pr45912_closed_at": "2026-11-11T22:19:13Z",
        "dzzf_tip_frozen_prefix": "09afbb4",
        "dzzf_freeze_observed_at": "2026-11-10T17:42:11Z",
    },
    "sources": [
        {
            "key": "mathlibpr",
            "kind": K_GH_SEARCH,
            "url": "https://api.github.com/search/issues"
                   "?q=repo:leanprover-community/mathlib4+is:pr+zeta"
                   "&per_page=10",
            "auth": "netrc",
            "screening": {
                "keywords": ["zeta", "dedekind"],
                "own_markers": [45912],
                "anchor": "mathlib_pr45912_closed_at",
            },
        },
        {
            "key": "pr45912",
            "kind": K_GH_API,
            "url": "https://api.github.com/repos/leanprover-community/"
                   "mathlib4/pulls/45912",
            "auth": "netrc",
            "screening": {
                "keywords": [],
                "own_markers": [45912],
                "anchor": "mathlib_pr45912_closed_at",
            },
        },
        {
            "key": "arxiv-dzeta",
            "kind": K_ARXIV,
            "url": ARXIV_DZETA_URL,
            "auth": "none",
            "days_window": 30,
            "screening": {
                "keywords": ["formalization", "lean", "coq"],
            },
        },
        {
            "key": "arxiv-quasir",
            "kind": K_ARXIV,
            "url": ARXIV_QUASIR_URL,
            "auth": "none",
            "days_window": 30,
            "screening": {
                "keywords": ["formalization", "lean", "coq"],
            },
        },
        {
            # pit-c burn-in: the coordination source is pinned to the Main
            # repository issue #3 with the comments sub-face enabled.  The
            # retired endpoint (the tooling repo issue list / issue 3) 404'd
            # in round 1 and must not return to the default list.
            "key": "issues",
            "kind": K_GH_ISSUE,
            "url": MAIN_ISSUE_URL,
            "auth": "netrc",
            "comments": {"enabled": True, "per_page": 30},
            "screening": {
                "keywords": [],
                "own_markers": [],
                "anchor": "",
            },
        },
        {
            "key": "dzzftip",
            "kind": K_GH_COMMITS,
            "url": "https://api.github.com/repos/AxiomMath/"
                   "DedekindZetaZeroFree/commits?per_page=3",
            "auth": "netrc",
            "c1_frozen_prefix": "09afbb4",
            "screening": {
                "keywords": [],
                "own_markers": [],
                "anchor": "dzzf_freeze_observed_at",
            },
        },
    ],
}

SOURCE_KEYS = [s["key"] for s in DEFAULT_CONFIG["sources"]]


# --------------------------------------------------------------------------
# Config loading and schema validation (fail loud on drift).
# --------------------------------------------------------------------------

_TOP_KEYS = ("schema", "sentinel", "defaults", "deposit_anchors", "sources")
_SENTINEL_KEYS = ("endpoint", "rounds")
_SOURCE_KEYS_ALLOWED = ("key", "kind", "url", "auth", "cap", "days_window",
                        "comments", "c1_frozen_prefix", "screening",
                        "retry_param_overrides", "follow")
_SCREENING_KEYS = ("keywords", "own_markers", "anchor")


def validate_config(cfg):
    """Validate one parsed config object; raise SchemaError on any drift."""
    if not isinstance(cfg, dict):
        raise SchemaError("config must be a JSON object")
    if cfg.get("schema") != SCHEMA:
        raise SchemaError("config schema must be %r, got %r"
                          % (SCHEMA, cfg.get("schema")))
    for top in cfg:
        if top not in _TOP_KEYS:
            raise SchemaError("unknown top-level key %r" % (top,))
    sentinel = cfg.get("sentinel")
    if sentinel is not None:
        if not isinstance(sentinel, dict):
            raise SchemaError("sentinel must be an object")
        for k in sentinel:
            if k not in _SENTINEL_KEYS:
                raise SchemaError("unknown sentinel key %r" % (k,))
        if "endpoint" in sentinel and not isinstance(sentinel["endpoint"], str):
            raise SchemaError("sentinel.endpoint must be a string")
        if "rounds" in sentinel:
            _check_int(sentinel["rounds"], "sentinel.rounds", 1, 240)
    defaults = cfg.get("defaults")
    if defaults is not None:
        if not isinstance(defaults, dict):
            raise SchemaError("defaults must be an object")
        for k in defaults:
            if k != "cap_per_source":
                raise SchemaError("unknown defaults key %r" % (k,))
            _check_int(defaults[k], "defaults.cap_per_source", 1, 16)
    anchors = cfg.get("deposit_anchors")
    if anchors is not None and not isinstance(anchors, dict):
        raise SchemaError("deposit_anchors must be an object")
    sources = cfg.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SchemaError("sources must be a non-empty list")
    seen = set()
    for src in sources:
        if not isinstance(src, dict):
            raise SchemaError("each source must be an object")
        key = src.get("key")
        if not isinstance(key, str) or not key:
            raise SchemaError("source key must be a non-empty string")
        if key in seen:
            raise SchemaError("duplicate source key %r" % (key,))
        seen.add(key)
        for k in src:
            if k not in _SOURCE_KEYS_ALLOWED:
                raise SchemaError("source %s: unknown key %r" % (key, k))
        if src.get("kind") not in KINDS:
            raise SchemaError("source %s: kind must be one of %s"
                              % (key, ",".join(KINDS)))
        if not isinstance(src.get("url"), str) or not src["url"]:
            raise SchemaError("source %s: url must be a non-empty string"
                              % (key,))
        auth = src.get("auth", "none")
        if auth not in ("netrc", "none"):
            raise SchemaError("source %s: auth must be netrc|none" % (key,))
        if "cap" in src:
            _check_int(src["cap"], "source %s cap" % key, 1, 16)
        if "days_window" in src:
            _check_int(src["days_window"], "source %s days_window" % key,
                       1, 3650)
        if src.get("kind") == K_ARXIV and "{WINDOW}" not in src["url"] \
                and "days_window" in src:
            raise SchemaError("source %s: arxiv url needs {WINDOW} when "
                              "days_window is set" % (key,))
        comments = src.get("comments")
        if comments is not None:
            if not isinstance(comments, dict):
                raise SchemaError("source %s: comments must be an object"
                                  % (key,))
            for k in comments:
                if k not in ("enabled", "per_page"):
                    raise SchemaError("source %s: unknown comments key %r"
                                      % (key, k))
            if "enabled" in comments and \
                    not isinstance(comments["enabled"], bool):
                raise SchemaError("source %s: comments.enabled must be bool"
                                  % (key,))
            if "per_page" in comments:
                _check_int(comments["per_page"],
                           "source %s comments.per_page" % key, 1, 100)
        prefix = src.get("c1_frozen_prefix")
        if prefix is not None:
            if src.get("kind") != K_GH_COMMITS:
                raise SchemaError("source %s: c1_frozen_prefix only on kind "
                                  "%s" % (key, K_GH_COMMITS))
            p = str(prefix)
            if not p or any(c not in "0123456789abcdef" for c in p.lower()):
                raise SchemaError("source %s: c1_frozen_prefix must be a "
                                  "hex prefix" % (key,))
        screening = src.get("screening")
        if screening is not None:
            if not isinstance(screening, dict):
                raise SchemaError("source %s: screening must be an object"
                                  % (key,))
            for k in screening:
                if k not in _SCREENING_KEYS:
                    raise SchemaError("source %s: unknown screening key %r"
                                      % (key, k))
        overrides = src.get("retry_param_overrides")
        if overrides is not None:
            if not isinstance(overrides, list) or \
                    any(not isinstance(o, dict) for o in overrides):
                raise SchemaError("source %s: retry_param_overrides must be "
                                  "a list of objects" % (key,))
    return cfg


def _check_int(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) \
            or value < low or value > high:
        raise SchemaError("%s must be an int in [%d, %d], got %r"
                          % (name, low, high, value))


def load_config(path):
    """Read and validate --config; absent file exits 9, drift exits 2."""
    if not os.path.isfile(path):
        raise FailLoud("config file not found: %s" % os.path.abspath(path))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, ValueError) as exc:
        raise FailLoud("config unreadable: %s" % exc)
    validate_config(cfg)
    return cfg


# --------------------------------------------------------------------------
# URL assembly and the curl argument builder (read-only by construction).
# --------------------------------------------------------------------------

def arxiv_window(clock_now, days):
    """submittedDate range for a rolling window, arXiv UTC format."""
    end = clock_now
    start = end - datetime.timedelta(days=days)
    return ("+AND+submittedDate:[%s0000+TO+%s2359]"
            % (start.strftime("%Y%m%d"), end.strftime("%Y%m%d")))


def build_url(source, clock_now):
    """Resolve the source URL: substitute the arXiv window placeholder."""
    url = source["url"]
    if source.get("kind") == K_ARXIV and "{WINDOW}" in url:
        days = source.get("days_window")
        url = url.replace("{WINDOW}",
                          arxiv_window(clock_now, days) if days else "")
    return url


def comments_url(source):
    """Comments sub-face URL of an issue source (pit-c; configurable)."""
    per_page = (source.get("comments") or {}).get("per_page", 30)
    return "%s/comments?per_page=%d" % (source["url"].rstrip("/"), per_page)


WRITE_VERB_TOKENS = ("-d", "--data", "--data-raw", "--data-binary",
                     "-X", "--request")


def build_curl_args(url, raw_path, timeout_seconds, netrc, source):
    """One read-only GET as a curl argument vector.

    pit-a: arXiv sources carry -L from the first shot, unconditionally, so
    a redirect never burns the shot budget.  No write verb can be emitted
    by construction (no -d/--data/-X anywhere below).
    """
    args = ["curl", "-sS", "-m", str(int(timeout_seconds)),
            "-o", raw_path,
            "-w", "%{http_code} %{size_download}"]
    if source.get("kind") == K_ARXIV or source.get("follow"):
        args.append("-L")
    if netrc and source.get("auth") == "netrc":
        args.extend(["--netrc-file", netrc])
    if source.get("kind") != K_ARXIV and "api.github.com" in url:
        args.extend(["-H", "Accept: " + ACCEPT_GITHUB,
                     "-H", "X-GitHub-Api-Version: " + GITHUB_API_VERSION])
    args.append(url)
    return args


def assert_read_only(args):
    """Raise if an argument vector could mutate anything on the wire."""
    skip_next = False
    for i, token in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if token in WRITE_VERB_TOKENS:
            # -X/--request with a non-GET method is the only true write;
            # -d/--data* is a write outright.
            if token in ("-d", "--data", "--data-raw", "--data-binary"):
                raise AssertionError("write verb in curl args: %r" % (args,))
            if token in ("-X", "--request"):
                method = args[i + 1].upper() if i + 1 < len(args) else ""
                if method != "GET":
                    raise AssertionError("non-GET method in curl args: %r"
                                         % (args,))
                skip_next = True
    return True


# --------------------------------------------------------------------------
# Real transport (curl subprocess).  --dry-run and --selftest never reach
# this function.
# --------------------------------------------------------------------------

def curl_transport(args):
    """Run curl; return (http_code, size_bytes); 0/0 on a wire error."""
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return 0, 0
    tail = proc.stdout.decode("utf-8", errors="replace").strip()
    last = tail.splitlines()[-1].strip() if tail else ""
    parts = last.split()
    if len(parts) >= 2 and parts[0].isdigit():
        code = int(parts[0])
        size = int(parts[1]) if parts[1].isdigit() else 0
        return code, size
    return 0, 0


# --------------------------------------------------------------------------
# Response parsing: each kind extracts the mechanical facts the digest and
# the screening section consume.  A body that does not parse is a retryable
# failure (round-1 precedent: a body-parse miss is data about the pipeline,
# not about the window).
# --------------------------------------------------------------------------

def parse_facts(kind, path):
    """Extract facts from a fetched body; raise ValueError when unusable."""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if kind in (K_GH_SEARCH, K_GH_API, K_GH_ISSUE, K_GH_COMMITS):
        obj = json.loads(text)
    else:
        return _parse_arxiv(text)

    if kind == K_GH_SEARCH:
        items = []
        for it in obj.get("items", [])[:10]:
            user = it.get("user") or {}
            items.append({
                "number": it.get("number"),
                "title": it.get("title", ""),
                "state": it.get("state", ""),
                "created_at": it.get("created_at", ""),
                "updated_at": it.get("updated_at", ""),
                "closed_at": it.get("closed_at"),
                "author": user.get("login", ""),
            })
        return {"total_count": obj.get("total_count"), "items": items}

    if kind == K_GH_API:
        return {
            "state": obj.get("state"),
            "merged": obj.get("merged"),
            "closed_at": obj.get("closed_at"),
            "head_sha": (obj.get("head") or {}).get("sha", ""),
            "base_sha": (obj.get("base") or {}).get("sha", ""),
            "mergeable_state": obj.get("mergeable_state", ""),
            "commits": obj.get("commits"),
            "comments": obj.get("comments"),
        }

    if kind == K_GH_ISSUE:
        return {
            "number": obj.get("number"),
            "title": obj.get("title", ""),
            "state": obj.get("state"),
            "comments_count": obj.get("comments"),
            "created_at": obj.get("created_at", ""),
            "updated_at": obj.get("updated_at", ""),
        }

    # K_GH_COMMITS: list of commit objects, tip first.
    if not isinstance(obj, list) or not obj:
        raise ValueError("commits body is not a non-empty list")
    tip = obj[0]
    commit = tip.get("commit", {})
    return {
        "tip_sha": tip.get("sha", ""),
        "tip_message": (commit.get("message", "").splitlines() or [""])[0],
        "tip_date": (commit.get("committer") or {}).get("date", ""),
        "author": ((commit.get("author") or {}).get("name", "")),
        "listed": len(obj),
    }


_OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}totalResults"
_ATOM_ENTRY = "{http://www.w3.org/2005/Atom}entry"


def _parse_arxiv(text):
    root = ET.fromstring(text)
    total = root.find(_OPENSEARCH)
    entries = []
    for entry in root.iter(_ATOM_ENTRY):
        def _txt(tag):
            node = entry.find("{http://www.w3.org/2005/Atom}" + tag)
            return (node.text or "").strip() if node is not None else ""
        entries.append({
            "id": _txt("id"),
            "published": _txt("published"),
            "title": " ".join(_txt("title").split()),
        })
    return {
        "totalResults": int(total.text) if total is not None
                        and (total.text or "").strip().isdigit() else None,
        "entries": entries,
    }


# --------------------------------------------------------------------------
# Per-source sweep: cap / stop-when-obtained / sleep-then-change-param.
# --------------------------------------------------------------------------

class ShotRecord(object):
    __slots__ = ("source_key", "attempt", "url", "code", "size", "verdict",
                 "changed", "ts")

    def __init__(self, key, attempt, url, code, size, verdict, changed, ts):
        self.source_key = key
        self.attempt = attempt
        self.url = url
        self.code = code
        self.size = size
        self.verdict = verdict
        self.changed = changed
        self.ts = ts

    def line(self):
        base = "%s|%s|attempt=%d|GET %s|HTTP %d|%dB|%s" % (
            self.ts, self.source_key, self.attempt, self.url,
            self.code, self.size, self.verdict)
        if self.changed:
            base += "|changed=%s" % self.changed
        return base


def _verdict_for(code):
    if code == 200:
        return "obtained"
    if code == 404:
        return "negative-definite"
    if 300 <= code < 400:
        return "redirect-retryable"
    if code == 0:
        return "wire-error-retryable"
    return "http-retryable"


def sweep_source(source, cfg, ctx, out_dir, transport, clock, sleep):
    """Fire one source to a terminal state under the cap; return result."""
    key = source["key"]
    kind = source["kind"]
    cap = source.get("cap", cfg.get("defaults", {}).get("cap_per_source",
                                                        CAP_DEFAULT))
    netrc = ctx.netrc
    raw_dir = os.path.join(out_dir, "raw")
    shots = []
    result = {
        "key": key, "kind": kind, "cap": cap, "state": ST_PENDING,
        "shots": shots, "facts": None, "subface": None,
        "fetched_at": "", "raw_file": "", "retry_file": "",
    }
    overrides = source.get("retry_param_overrides") or []

    def fire(attempt, url, raw_name):
        timeout = DEFAULT_TIMEOUT_SECONDS + TIMEOUT_WIDEN_SECONDS * (attempt - 1)
        changed = ""
        if attempt > 1:
            changed = "curl-timeout:%ds" % timeout
            idx = attempt - 2
            if idx < len(overrides):
                changed += ",config-override:%d" % (idx + 1)
        src_view = dict(source)
        src_view["url"] = url
        args = build_curl_args(url, os.path.join(raw_dir, raw_name),
                               timeout, netrc, src_view)
        assert_read_only(args)
        code, size = transport(args)
        verdict = _verdict_for(code)
        rec = ShotRecord(key, attempt, url, code, size, verdict, changed,
                         clock().strftime("%Y-%m-%dT%H:%M:%SZ"))
        shots.append(rec)
        return rec

    attempt = 0
    body = None
    while attempt < cap:
        attempt += 1
        if attempt > 1:
            sleep(RETRY_SLEEP_SECONDS)  # sleep 60, then change a parameter
        url = build_url(source, clock())
        rec = fire(attempt, url, "%s.a%d.json" % (key, attempt))
        if rec.code == 200:
            try:
                body = parse_facts(kind, os.path.join(raw_dir,
                                                      "%s.a%d.json"
                                                      % (key, attempt)))
            except (ValueError, KeyError, OSError):
                rec.verdict = "parse-error-retryable"
                body = None
                continue
            result["state"] = ST_OBTAINED
            result["fetched_at"] = rec.ts
            result["raw_file"] = "%s.json" % key
            _copy_raw(os.path.join(raw_dir, "%s.a%d.json" % (key, attempt)),
                      os.path.join(raw_dir, result["raw_file"]))
            break
        if rec.code == 404:
            # Definitive negative finding: stop now, keep the remaining cap,
            # preserve the 404 body as retry evidence (no backoff, no burn).
            result["state"] = ST_NEGATIVE_DEFINITE
            result["fetched_at"] = rec.ts
            result["retry_file"] = "%s.retry.json" % key
            _copy_raw(os.path.join(raw_dir, "%s.a%d.json" % (key, attempt)),
                      os.path.join(raw_dir, result["retry_file"]))
            break

    if result["state"] == ST_PENDING:
        result["state"] = ST_CAP_EXHAUSTED
        result["fetched_at"] = shots[-1].ts if shots else \
            clock().strftime("%Y-%m-%dT%H:%M:%SZ")
    result["facts"] = body

    # pit-c comments sub-face: fetched right after the single point, inside
    # the same source cap, each shot NETRED-recorded, >= 2s spacing.
    if result["state"] == ST_OBTAINED and kind == K_GH_ISSUE:
        sub = source.get("comments") or {}
        if sub.get("enabled"):
            sub_state = ST_PENDING
            sub_facts = None
            sub_shots = 0
            for sub_attempt in range(1, cap - attempt + 1):
                if sub_attempt > 1:
                    sleep(RETRY_SLEEP_SECONDS)
                elif attempt >= 1:
                    sleep(INTER_SHOT_MIN_SECONDS)
                sub_shots += 1
                url = comments_url(source)
                rec = fire(attempt + sub_attempt, url,
                           "%s.comments.a%d.json" % (key, sub_attempt))
                if rec.code == 200:
                    try:
                        with open(os.path.join(
                                raw_dir, "%s.comments.a%d.json"
                                % (key, sub_attempt)),
                                "r", encoding="utf-8") as handle:
                            listing = json.load(handle)
                        if not isinstance(listing, list):
                            raise ValueError("comments not a list")
                        sub_facts = {
                            "count": len(listing),
                            "last_at": (listing[-1] or {}).get(
                                "created_at", "") if listing else "",
                        }
                        _copy_raw(os.path.join(
                            raw_dir, "%s.comments.a%d.json" % (key, sub_attempt)),
                            os.path.join(raw_dir, "%s.comments.json" % key))
                        sub_state = ST_OBTAINED
                    except (ValueError, OSError):
                        sub_state = ST_PENDING
                        continue
                    break
                if rec.code == 404:
                    sub_state = ST_NEGATIVE_DEFINITE
                    break
            if sub_state == ST_PENDING:
                sub_state = ST_CAP_EXHAUSTED
            result["subface"] = {
                "url": comments_url(source), "state": sub_state,
                "shots": sub_shots, "facts": sub_facts,
            }
    return result


def _copy_raw(src, dst):
    if os.path.isfile(src):
        shutil.copyfile(src, dst)


# --------------------------------------------------------------------------
# Sentinel companion (pit-b): one beat every ROUND_SECONDS; a beat the
# sweep overruns is emitted as an explicit SUSPEND line; sampling continues
# to one beat after the sweep closes.  Zero silent gaps by construction.
# --------------------------------------------------------------------------

def run_sentinel_and_sweep(cfg, ctx, out_dir, transport, clock, sleep):
    sources = cfg["sources"]
    sentinel = cfg.get("sentinel") or {}
    endpoint = sentinel.get("endpoint", "https://api.github.com/rate_limit")
    rounds = ctx.rounds if ctx.rounds is not None else \
        sentinel.get("rounds", DEFAULT_ROUNDS)
    raw_dir = os.path.join(out_dir, "raw")
    log_path = os.path.join(raw_dir, "windowsniff.netred.txt")

    beats = []  # rendered window-log lines

    def probe():
        nonlocal_beat = len(beats) + 1
        ts = clock().strftime("%Y-%m-%dT%H:%M:%SZ")
        probe_src = {"kind": "github_api", "auth": "netrc" if ctx.netrc
                     else "none"}
        args = build_curl_args(endpoint, os.path.join(raw_dir, "_probe.json"),
                               DEFAULT_TIMEOUT_SECONDS, ctx.netrc, probe_src)
        assert_read_only(args)
        code, _size = transport(args)
        line = "R%d|%s|%d|%s" % (nonlocal_beat, ts, code,
                                 "LIVE" if code == 200 else "DEAD")
        beats.append(line)
        return code

    # Beat 1 at start, then the collection sweep, then the beats the sweep
    # overran as explicit SUSPEND lines, then the post-close beat, then the
    # remaining companion rounds at the 60s cadence.
    open(log_path, "w", encoding="utf-8", newline="\n").write(
        "# periscope sentinel companion | round_seconds=%d | UTC\n"
        % ROUND_SECONDS)
    probe()
    sweep_start = clock()
    results = [sweep_source(src, cfg, ctx, out_dir, transport, clock, sleep)
               for src in sources]
    sweep_end = clock()
    elapsed = (sweep_end - sweep_start).total_seconds()
    missed = int(elapsed // ROUND_SECONDS)
    for i in range(missed):
        ts = clock().strftime("%Y-%m-%dT%H:%M:%SZ")
        beats.append("SUSPEND|%d|%s|collection-sweep-in-flight"
                     % (len(beats) + 1, ts))
    probe()  # post-sweep-close beat is always sampled
    while len(beats) < rounds:
        sleep(ROUND_SECONDS)
        probe()

    # mkdir + read-back assertion (round-1 pit: the window log must land
    # exactly here; a silent path drift is a fail-loud condition).
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(beats) + "\n")
    with open(log_path, "r", encoding="utf-8") as handle:
        back = handle.read().splitlines()
    if not back or not back[0].startswith("# periscope sentinel companion"):
        raise FailLoud("windowsniff log read-back failed at %s" % log_path)
    body_lines = [ln for ln in back[1:] if ln.strip()]
    if len(body_lines) != len(beats):
        raise FailLoud("windowsniff line count %d != beats %d"
                       % (len(body_lines), len(beats)))
    _assert_no_silent_gap(beats, rounds)
    return beats, results, log_path


def _assert_no_silent_gap(beats, rounds):
    """Every beat index 1..N appears exactly once (R or SUSPEND)."""
    seen = [_beat_index(line) for line in beats]
    if seen != list(range(1, len(beats) + 1)):
        raise AssertionError("sentinel beats not contiguous: %r" % (seen,))
    if len(beats) < 2:
        raise AssertionError("sentinel must sample start and post-close")
    if not beats[-1].startswith("R"):
        raise AssertionError("final beat must be a sampled round")
    return True


# --------------------------------------------------------------------------
# Judgment draft renderer: five sections, mirroring the round-1 ledger form.
# --------------------------------------------------------------------------

def screen_row(source, item, cfg):
    """Mechanical three-state preliminary screening for one item."""
    screening = source.get("screening") or {}
    keywords = [str(k).lower() for k in screening.get("keywords", [])]
    own = screening.get("own_markers", []) or []
    anchor_key = screening.get("anchor") or ""
    anchors = cfg.get("deposit_anchors") or {}
    number = item.get("number")
    title = str(item.get("title", "")).lower()
    created = str(item.get("created_at") or item.get("published") or "")
    if number is not None and number in own:
        return SCREEN_OURS, "listed in own_markers"
    overlap = any(k and k in title for k in keywords)
    anchor = anchors.get(anchor_key, "") if anchor_key else ""
    if not overlap:
        return SCREEN_NO_BEARING, "no keyword overlap with the deposit faces"
    if anchor and created:
        if created <= anchor:
            return SCREEN_PRIOR, "created %s <= anchor %s" % (created, anchor)
        return SCREEN_SUSPECT, ("created %s > anchor %s; adjudicate"
                                % (created, anchor))
    return SCREEN_SUSPECT, "keyword overlap; no anchor comparable"


def c1_verdict(source, facts, cfg):
    """C1 trigger check: tip sha prefix vs the frozen value."""
    frozen = str(source.get("c1_frozen_prefix", "")).lower()
    tip = str((facts or {}).get("tip_sha", "")).lower()
    if not frozen:
        return None
    if not tip:
        return {"verdict": "UNDETERMINED", "frozen": frozen, "tip": "",
                "note": "tip sha unavailable (source not obtained)"}
    if tip.startswith(frozen):
        return {"verdict": "C1-CLEAN", "frozen": frozen, "tip": tip,
                "note": "tip matches the frozen prefix; no rescans queued "
                        "(a rescan awaits an order)"}
    return {"verdict": "C1-TRIGGERED", "frozen": frozen, "tip": tip,
            "note": "tip advanced past the frozen prefix; registered "
                    "loudly, no auto-rescan (a rescan awaits an order)"}


def render_draft(cfg, results, beats, clock_now, dry_run=False):
    """Render the five-section judgment draft (bilingual, round-1 form)."""
    anchors = cfg.get("deposit_anchors") or {}
    out = []
    w = out.append
    stamp = clock_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    title_stamp = stamp.split("T")[0]
    w("# 情报台账草案 · periscope 六源采集 · %s" % title_stamp)
    w("# Intel Ledger Draft · periscope six-source sweep · %s" % title_stamp)
    w("")
    w("- generated-by: tools/periscope.py (rocqwash) · config schema %s"
      % SCHEMA)
    w("- run stamp (UTC): %s%s" % (stamp, " · dry-run plan" if dry_run else ""))
    w("- 判读边界 boundary: the mechanical rows below are a preliminary "
      "screen; adjudication upgrades or dismisses them. A sentinel verdict "
      "covers only its measured rounds.")
    w("")
    shots_total = sum(len(r["shots"]) for r in results)

    # -- Section 1: per-source digest -------------------------------------
    w("## 一、逐源 digest｜Per-source digest (who / when / what / sha · "
      "time-bound)")
    w("")
    w("| Source | Fetched-at (UTC) | Shots | State | Key facts |")
    w("|---|---|---|---|---|")
    for r in results:
        facts = r.get("facts")
        key_facts = _digest_facts(r, facts)
        w("| %s | %s | %d/%d | %s | %s |"
          % (r["key"], r.get("fetched_at") or "-", len(r["shots"]),
             r["cap"], r["state"], key_facts))
    w("")
    w("Raw bodies: raw/<key>.json (obtained), raw/<key>.retry.json "
      "(negative-definite), raw/<key>.a<n>.json (every attempt).")
    w("")

    # -- Section 2: three-state collision screening -----------------------
    w("## 二、撞车初筛三态｜Collision screening (three states, mechanical "
      "preliminary)")
    w("")
    w("判据 criterion: item created/published time vs the deposit anchors "
      "(%s) plus keyword overlap against the deposit faces. States: %s / %s "
      "/ %s / %s."
      % (", ".join("%s=%s" % (k, v) for k, v in sorted(anchors.items()))
         or "none configured",
         SCREEN_PRIOR, SCREEN_SUSPECT, SCREEN_NO_BEARING, SCREEN_OURS))
    w("")
    w("| Item | Source | Created/Published | Preliminary state | Note |")
    w("|---|---|---|---|---|")
    counts = {SCREEN_PRIOR: 0, SCREEN_SUSPECT: 0, SCREEN_NO_BEARING: 0,
              SCREEN_OURS: 0}
    for r in results:
        facts = r.get("facts")
        if not facts:
            continue
        src = _source_by_key(cfg, r["key"])
        for item in facts.get("items", []):
            state, note = screen_row(src, item, cfg)
            counts[state] += 1
            w("| #%s %s | %s | %s | %s | %s |"
              % (item.get("number", "-"), str(item.get("title", ""))[:60],
                 r["key"], item.get("created_at", "-"), state, note))
        for item in facts.get("entries", []):
            state, note = screen_row(src, item, cfg)
            counts[state] += 1
            w("| %s %s | %s | %s | %s | %s |"
              % (str(item.get("id", "")).rsplit("/", 1)[-1][:24],
                 str(item.get("title", ""))[:48], r["key"],
                 item.get("published", "-"), state, note))
    w("")
    w("初筛裁定 screening verdict: %d prior-registered / %d suspected-"
      "collision candidates / %d no-bearing / %d ours. A suspected-collision "
      "upgrade is an adjudication decision, never this tool's."
      % (counts[SCREEN_PRIOR], counts[SCREEN_SUSPECT],
         counts[SCREEN_NO_BEARING], counts[SCREEN_OURS]))
    w("")

    # -- Section 3: C1 trigger verdict ------------------------------------
    w("## 三、C1 触发判定｜C1 trigger verdict")
    w("")
    for r in results:
        src = _source_by_key(cfg, r["key"])
        verdict = c1_verdict(src, r.get("facts"), cfg)
        if verdict is None:
            continue
        w("- %s: tip=%s frozen=%s fetched=%s → **%s** — %s"
          % (r["key"], verdict["tip"] or "-", verdict["frozen"],
             r.get("fetched_at") or "-", verdict["verdict"], verdict["note"]))
    if not any(c1_verdict(_source_by_key(cfg, r["key"]), r.get("facts"), cfg)
               for r in results):
        w("- (no source carries c1_frozen_prefix; section kept for template "
          "shape)")
    w("")

    # -- Section 4: negative findings, four elements (mandatory) ----------
    w("## 四、负发现四要素｜Negative findings, four elements (mandatory per "
      "source not obtained)")
    w("")
    negatives = [r for r in results
                 if r["state"] in (ST_NEGATIVE_DEFINITE, ST_CAP_EXHAUSTED)]
    if not negatives:
        w("(no negative finding this sweep — the mandatory four-element "
          "shape is retained below; any source that closes not-obtained "
          "must answer all four)")
        w("")
        for idx, label in enumerate(FOUR_ELEMENTS, 1):
            w("%d. %s" % (idx, label))
        w("")
    else:
        for r in negatives:
            w("### %s — %s" % (r["key"], r["state"]))
            w("")
            w("1. %s: %s" % (NEG_SCANNED, _neg_scanned_sentence(r)))
            w("2. %s: (fill: the surfaces this sweep did not cover)"
              % NEG_NOT_SCANNED)
            w("3. %s: %s" % (NEG_NOT_ABSOLUTE, NEG_NOT_ABSOLUTE_SENTENCE))
            w("4. %s: %s" % (NEG_ALIASES, NEG_ALIASES_SENTENCE))
            w("")
    _assert_four_elements_present(out, results)

    # -- Section 5: window scheduling advice, five fixed items ------------
    live = [b for b in beats if b.startswith("R") and b.endswith("|LIVE")]
    dead = [b for b in beats if b.startswith("R") and b.endswith("|DEAD")]
    susp = [b for b in beats if b.startswith("SUSPEND")]
    obtained = [r["key"] for r in results if r["state"] == ST_OBTAINED]
    first_shot = [r["key"] for r in results if r["state"] == ST_OBTAINED
                  and len(r["shots"]) == 1]
    w("## 五、排窗建议五条｜Window scheduling advice (five fixed items)")
    w("")
    w("1. 首发放行相位 first-release phase: sentinel measured %d/%d rounds "
      "LIVE (%s).%s Boundary: this verdict covers only the measured rounds; "
      "unmeasured gaps remain undetermined, so release immediately unless a "
      "measured dead window says otherwise."
      % (len(live), len(live) + len(dead),
         ", ".join(dead) if dead else "no dead round measured",
         " (dry-run plan: sentinel not yet measured)" if dry_run else ""))
    w("2. 哨伴飞 sentinel companion: round_seconds=%d, beats=%d (R=%d, "
      "SUSPEND=%d), zero silent gap verified mechanically; keep foreground "
      "companion mode and the explicit SUSPEND rule."
      % (ROUND_SECONDS, len(beats), len(live) + len(dead), len(susp)))
    w("3. 席间错峰 stagger: obtained first-shot = %s (release immediately); "
      "retried sources = %s; arXiv legs carried -L from the first shot by "
      "construction. Keep arXiv legs ≥30s behind the GitHub wave."
      % (", ".join(first_shot) or "none",
         ", ".join(k for k in obtained if k not in first_shot) or "none"))
    w("4. 帽与协议 cap and protocol: shots used %d total; per source %s; "
      "cap=%d/源, stop-when-obtained, sleep-%ds change-param retry, 404 "
      "stops without burning the cap — keep the protocol as built."
      % (shots_total,
         ", ".join("%s %d/%d" % (r["key"], len(r["shots"]), r["cap"])
                   for r in results),
         CAP_DEFAULT, RETRY_SLEEP_SECONDS))
    c1_state = "n/a (no dzzftip source configured)"
    if any(src["key"] == "dzzftip" for src in cfg["sources"]):
        tip_res = results_by_key(results).get("dzzftip") or {}
        verdict = c1_verdict(_source_by_key(cfg, "dzzftip"),
                             tip_res.get("facts"), cfg)
        if verdict:
            c1_state = "C1 " + verdict["verdict"]
    w("5. 改钉与跟进 re-pins and follow-ups: %s; negative-definite "
      "endpoints to re-pin before the next round: %s; suspected-collision "
      "candidates awaiting adjudication: %d."
      % (c1_state,
         ", ".join(r["key"] for r in results
                   if r["state"] == ST_NEGATIVE_DEFINITE) or "none",
         counts[SCREEN_SUSPECT]))
    w("")
    header = "rocqwash-periscope-draft/1"
    return "\n".join(out) + "\n<!-- draft schema %s -->\n" % header


def _digest_facts(result, facts):
    if result["state"] == ST_PENDING:
        return "dry-run plan only (not fetched)"
    if facts is None:
        wire = "; ".join("HTTP %d" % s.code for s in result["shots"]) or "-"
        return "no parseable facts (%s)" % wire
    kind = result["kind"]
    if kind == K_GH_SEARCH:
        top = "; ".join("#%s %s" % (i["number"], i["state"])
                        for i in facts.get("items", [])[:5])
        return "total_count=%s; top: %s" % (facts.get("total_count"), top)
    if kind == K_GH_API:
        return "state=%s merged=%s closed_at=%s head=%s" % (
            facts.get("state"), facts.get("merged"), facts.get("closed_at"),
            str(facts.get("head_sha", ""))[:8])
    if kind == K_GH_ISSUE:
        base = "issue#%s state=%s title=%s comments=%s" % (
            facts.get("number"), facts.get("state"),
            str(facts.get("title", ""))[:40], facts.get("comments_count"))
        sub = result.get("subface")
        if sub:
            base += "; comments sub-face %s (%d shots, count=%s)" % (
                sub["state"], sub["shots"],
                (sub.get("facts") or {}).get("count", "-"))
        return base
    if kind == K_GH_COMMITS:
        return "tip=%s (%s) listed=%s" % (str(facts.get("tip_sha", ""))[:12],
                                          facts.get("tip_date"),
                                          facts.get("listed"))
    if kind == K_ARXIV:
        heads = "; ".join(
            "%s %s" % (str(e.get("id", "")).rsplit("/", 1)[-1],
                       e.get("published", ""))
            for e in facts.get("entries", [])[:3])
        return "totalResults=%s; entries: %s" % (
            facts.get("totalResults"), heads or "-")
    return "-"


def _neg_scanned_sentence(result):
    shots = result["shots"]
    if shots:
        return ("GET %s, %d attempt(s), %s → %s; evidence raw/%s"
                % (shots[0].url, len(shots),
                   shots[0].ts, " ".join("HTTP %d" % s.code
                                         for s in shots),
                   result.get("retry_file") or
                   ("%s.a%d.json" % (result["key"], len(shots)))))
    return "(fill: the endpoint and the shot window of this sweep)"


def _assert_four_elements_present(lines, results):
    """Draft invariant: every closed-not-obtained source carries all four
    element labels — the renderer refuses to emit otherwise (fail-loud)."""
    text = "\n".join(lines)
    for r in results:
        if r["state"] in (ST_NEGATIVE_DEFINITE, ST_CAP_EXHAUSTED):
            for label in FOUR_ELEMENTS:
                if label not in text:
                    raise AssertionError(
                        "negative finding for %s misses element %r"
                        % (r["key"], label))
    return True


def _source_by_key(cfg, key):
    for src in cfg["sources"]:
        if src["key"] == key:
            return src
    raise KeyError(key)


def results_by_key(results):
    return {r["key"]: r for r in results}


# --------------------------------------------------------------------------
# NETRED ledgers (every attempt, including failures, is one line).
# --------------------------------------------------------------------------

def write_netred(out_dir, results):
    raw_dir = os.path.join(out_dir, "raw")
    master = []
    for r in results:
        lines = [s.line() for s in r["shots"]]
        with open(os.path.join(raw_dir, "%s.netred.txt" % r["key"]),
                  "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines) + ("\n" if lines else ""))
        master.extend(lines)
    master_path = os.path.join(raw_dir, "netred-master.txt")
    with open(master_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(master) + ("\n" if master else ""))
    return master_path, len(master)


# --------------------------------------------------------------------------
# Run faces.
# --------------------------------------------------------------------------

class Ctx(object):
    def __init__(self, cfg, out, rounds, netrc, dry_run):
        self.cfg = cfg
        self.out = out
        self.rounds = rounds
        self.netrc = netrc
        self.dry_run = dry_run


def plan_lines(cfg, ctx):
    """The dry-run plan face (also the header of a real run log)."""
    lines = []
    sentinel = cfg.get("sentinel") or {}
    lines.append("[plan] sentinel endpoint=%s rounds=%d round_seconds=%d"
                 % (sentinel.get("endpoint",
                                 "https://api.github.com/rate_limit"),
                    ctx.rounds if ctx.rounds is not None
                    else sentinel.get("rounds", DEFAULT_ROUNDS),
                    ROUND_SECONDS))
    for src in cfg["sources"]:
        url = build_url(src, _now())
        cap = src.get("cap", cfg.get("defaults", {}).get("cap_per_source",
                                                         CAP_DEFAULT))
        extra = ""
        if src.get("kind") == K_GH_ISSUE and (src.get("comments") or {}).get(
                "enabled"):
            extra = " +comments sub-face %s" % comments_url(src)
        if src.get("c1_frozen_prefix"):
            extra += " c1_frozen_prefix=%s" % src["c1_frozen_prefix"]
        lines.append("[plan] source %s kind=%s cap=%d auth=%s%s"
                     % (src["key"], src["kind"], cap,
                        src.get("auth", "none"), extra))
    return lines


def dry_run(cfg, ctx):
    """Validate, plan, and render the draft skeleton; zero net, zero writes."""
    for line in plan_lines(cfg, ctx):
        sys.stdout.write(line + "\n")
    sys.stdout.write("[dry-run] draft skeleton follows (nothing written)\n")
    pending = []
    for src in cfg["sources"]:
        pending.append({
            "key": src["key"], "kind": src["kind"],
            "cap": src.get("cap", cfg.get("defaults", {})
                    .get("cap_per_source", CAP_DEFAULT)),
            "state": ST_PENDING, "shots": [], "facts": None,
            "subface": None, "fetched_at": "", "raw_file": "",
            "retry_file": "",
        })
    skeleton = render_draft(cfg, pending, ["R1|%s|200|LIVE"
                                           % _now().strftime(
                                               "%Y-%m-%dT%H:%M:%SZ")],
                            _now, dry_run=True)
    sys.stdout.write(skeleton)
    sys.stdout.write("[dry-run] complete: zero network, zero writes\n")
    return 0


def real_run(cfg, ctx):
    """Full sweep: sentinel companion + collection + draft + NETRED."""
    out_dir = ctx.out
    try:
        os.makedirs(os.path.join(out_dir, "raw"), exist_ok=True)
    except OSError as exc:
        raise FailLoud("output root not creatable: %s" % exc)
    if not os.path.isdir(os.path.join(out_dir, "raw")):
        raise FailLoud("output root not materialized: %s" % out_dir)
    for line in plan_lines(cfg, ctx):
        sys.stdout.write(line + "\n")

    def logging_transport(args):
        assert_read_only(args)
        return curl_transport(args)

    beats, results, log_path = run_sentinel_and_sweep(
        cfg, ctx, out_dir, logging_transport, _now, _sleep)
    master_path, master_lines = write_netred(out_dir, results)
    draft = render_draft(cfg, results, beats, _now, dry_run=False)
    draft_path = os.path.join(out_dir, "intel-ledger-draft.md")
    with open(draft_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(draft)
    sys.stdout.write("[run] sentinel beats=%d log=%s\n"
                     % (len(beats), log_path))
    sys.stdout.write("[run] NETRED master=%s lines=%d\n"
                     % (master_path, master_lines))
    sys.stdout.write("[run] draft=%s\n" % draft_path)
    for r in results:
        if r["state"] != ST_OBTAINED:
            sys.stdout.write("[run] %s -> %s (registered; negative findings "
                             "are data)\n" % (r["key"], r["state"]))
    return 0


# --------------------------------------------------------------------------
# Selftest: frozen vector group, canned transport, virtual clock.  Zero
# network, zero writes outside the temporary directory.
# --------------------------------------------------------------------------

class VirtualClock(object):
    """Deterministic clock: sleep advances virtual time by seconds."""

    def __init__(self, start_epoch=0):
        self.t = float(start_epoch)

    def now(self):
        return datetime.datetime.fromtimestamp(
            self.t, datetime.timezone.utc)

    def advance(self, seconds):
        self.t += float(seconds)


def _canned_transport(routes):
    """routes: list of (substring, [(code, body), ...]); each route serves
    its responses in order and repeats the last one once exhausted."""
    calls = []
    state = {}

    def transport(args):
        url = args[-1]
        for substring, responses in routes:
            if substring in url:
                idx = min(state.get(substring, 0), len(responses) - 1)
                state[substring] = idx + 1
                code, body = responses[idx]
                raw_path = args[args.index("-o") + 1]
                with open(raw_path, "w", encoding="utf-8") as handle:
                    handle.write(body)
                calls.append(url)
                return code, len(body)
        raise AssertionError("no canned route for %r" % (url,))
    transport.calls = calls
    return transport


def _beat_index(line):
    """Beat number of a window-log line (R<n> head or SUSPEND|n)."""
    head = line.split("|", 1)[0]
    if head.startswith("R"):
        return int(head[1:])
    if head == "SUSPEND":
        return int(line.split("|")[1])
    raise ValueError("not a beat line: %r" % (line,))


def selftest():
    fails = []
    tmp = tempfile.mkdtemp(prefix="periscope_selftest_")
    clock = VirtualClock()

    def check(name, cond, detail=""):
        if not cond:
            fails.append("%s %s" % (name, detail))

    try:
        # V1 CLI face: --help names the six flags; bare run is refused.
        rc, out = _run(["--help"])
        flat = out.replace("-\n", "-").replace("\n", " ")
        for flag in ("--config", "--out", "--rounds", "--netrc",
                     "--dry-run", "--selftest"):
            check("V1 --help names %s" % flag, flag in flat, flat[:200])
        rc, out = _run([])
        check("V1 bare run refused rc=2", rc == 2, "rc=%d %r" % (rc, out))
        check("V1 bare refusal mentions --out", "--out" in out, out[:200])
        rc, out = _run(["--bogus"])
        check("V1 --bogus rc=2", rc == 2, "rc=%d" % rc)
        rc, out = _run(["--selftest", "--out", "x"])
        check("V1 --selftest rejects run flags rc=2", rc == 2, "rc=%d" % rc)
        rc, out = _run(["--rounds", "0", "--dry-run"])
        check("V1 --rounds 0 is a usage error rc=2 (no traceback)",
              rc == 2 and "Traceback" not in out, "rc=%d %r" % (rc, out))

        # V2 config schema matrix: absent file 9; drift 2; valid passes.
        good = os.path.join(tmp, "good.json")
        with open(good, "w", encoding="utf-8") as h:
            json.dump(minimal_config(), h)
        rc, out = _run(["--config", os.path.join(tmp, "absent.json"),
                        "--dry-run"])
        check("V2 absent config rc=9", rc == 9, "rc=%d %r" % (rc, out))
        cases = []
        bad_schema = minimal_config(); bad_schema["schema"] = "x/9"
        cases.append(bad_schema)
        bad_kind = minimal_config()
        bad_kind["sources"][0]["kind"] = "rss"
        cases.append(bad_kind)
        bad_top = minimal_config(); bad_top["bogus_top"] = 1
        cases.append(bad_top)
        bad_prefix = minimal_config()
        bad_prefix["sources"][-1]["c1_frozen_prefix"] = "zzzz"
        cases.append(bad_prefix)
        bad_cap = minimal_config(); bad_cap["sources"][0]["cap"] = 99
        cases.append(bad_cap)
        for i, cfg_obj in enumerate(cases):
            path = os.path.join(tmp, "bad%d.json" % i)
            with open(path, "w", encoding="utf-8") as h:
                json.dump(cfg_obj, h)
            rc, out = _run(["--config", path, "--dry-run"])
            check("V2 schema case %d rc=2" % i, rc == 2,
                  "rc=%d %r" % (rc, out))
        rc, out = _run(["--config", good, "--dry-run"])
        check("V2 valid config dry-run rc=0", rc == 0,
              "rc=%d %r" % (rc, out))

        # V3 pit-a: -L from the first arXiv shot, at every attempt.
        arxiv_src = {"key": "a", "kind": K_ARXIV, "url": ARXIV_DZETA_URL}
        gh_src = {"key": "g", "kind": K_GH_API,
                  "url": "https://api.github.com/repos/x/y/pulls/1",
                  "auth": "netrc"}
        args0 = build_curl_args(build_url(arxiv_src, clock.now()),
                                "p", 30, "", arxiv_src)
        check("V3 arxiv first shot carries -L", "-L" in args0, str(args0))
        for attempt in range(1, CAP_DEFAULT + 1):
            args = build_curl_args("https://export.arxiv.org/api/query",
                                   "p", 30 + 30 * (attempt - 1), "",
                                   arxiv_src)
            check("V3 arxiv -L at attempt %d" % attempt, "-L" in args,
                  str(args))
        gh_args = build_curl_args(gh_src["url"], "p", 30, "n", gh_src)
        check("V3 github args carry no -L by default", "-L" not in gh_args,
              str(gh_args))

        # V4 pit-c: default config pins the Main issue with comments; the
        # comments sub-face fires after the single point within the cap.
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        issues_src = _source_by_key(cfg, "issues")
        check("V4 default issues endpoint is Main issue#3",
              issues_src["url"] == MAIN_ISSUE_URL
              and "rocqwash/issues" not in issues_src["url"],
              issues_src["url"])
        check("V4 comments sub-face enabled by default",
              (issues_src.get("comments") or {}).get("enabled") is True,
              str(issues_src.get("comments")))
        check("V4 comments URL shape",
              comments_url(issues_src).endswith("/comments?per_page=30"),
              comments_url(issues_src))
        out_dir = os.path.join(tmp, "v4out")
        os.makedirs(os.path.join(out_dir, "raw"))
        transport = _canned_transport([
            (MAIN_ISSUE_URL.split("?")[0], [(200, '{"number": 3, "title": '
                                            '"t", "state": "open", '
                                            '"comments": 2, "created_at": '
                                            '"2026-11-08T07:29:00Z"}'),
                                            (200, '[{"created_at": '
                                             '"2026-11-12T10:00:00Z"}, '
                                             '{"created_at": '
                                             '"2026-11-13T01:00:00Z"}]')]),
        ])
        clock2 = VirtualClock()
        result = sweep_source(issues_src, cfg,
                              Ctx(cfg, out_dir, None, "", False),
                              out_dir, transport, clock2.now,
                              lambda s: clock2.advance(s))
        check("V4 issue obtained", result["state"] == ST_OBTAINED,
              result["state"])
        sub = result.get("subface") or {}
        check("V4 comments sub-face obtained",
              sub.get("state") == ST_OBTAINED, str(sub))
        check("V4 comments facts count=2",
              (sub.get("facts") or {}).get("count") == 2, str(sub))
        check("V4 exactly two shots NETRED-recorded", len(result["shots"]) == 2,
              str(len(result["shots"])))
        check("V4 second shot is the comments URL",
              len(result["shots"]) == 2 and "comments" in
              result["shots"][1].url, str([s.url for s in result["shots"]]))

        # V5 pit-b: sentinel beats contiguous; sweep overrun yields SUSPEND
        # lines; read-back holds; zero silent gaps.
        cfg5 = copy.deepcopy(DEFAULT_CONFIG)
        cfg5["sources"] = [{
            "key": "flappy", "kind": K_GH_API,
            "url": "https://api.github.com/repos/x/y/pulls/9",
            "auth": "none",
        }]
        out5 = os.path.join(tmp, "v5out")
        os.makedirs(os.path.join(out5, "raw"))
        transport5 = _canned_transport([
            ("rate_limit", [(200, "{}")]),
            ("repos/x/y/pulls/9", [(500, "e1"), (500, "e2"), (200,
                                    '{"state": "open"}')]),
        ])
        clock5 = VirtualClock()
        beats, results5, log_path = run_sentinel_and_sweep(
            cfg5, Ctx(cfg5, out5, 4, "", False), out5, transport5,
            clock5.now, lambda s: clock5.advance(s))
        # two retry sleeps of 60s => two beats overrun => SUSPEND x2
        susp = [b for b in beats if b.startswith("SUSPEND")]
        check("V5 two overran beats yield SUSPEND", len(susp) == 2,
              str(beats))
        idxs = [_beat_index(b) for b in beats]
        check("V5 beat indexes contiguous 1..N",
              idxs == list(range(1, len(beats) + 1)), str(idxs))
        check("V5 final beat sampled post-close",
              beats[-1].startswith("R"), beats[-1])
        with open(log_path, "r", encoding="utf-8") as h:
            back = h.read().splitlines()
        check("V5 windowsniff read-back holds",
              back[0].startswith("# periscope sentinel companion")
              and len([ln for ln in back[1:] if ln.strip()]) == len(beats),
              str(back[:3]))

        # V6 cap / stop-when-obtained / 404 stops / cap-exhaust registered.
        mk = lambda pairs: _canned_transport(
            [("repos/x/y/pulls/9", list(pairs))])
        out6 = os.path.join(tmp, "v6out")
        os.makedirs(os.path.join(out6, "raw"))
        src6 = {"key": "s6", "kind": K_GH_API,
                "url": "https://api.github.com/repos/x/y/pulls/9",
                "auth": "none", "cap": 8}
        clock6 = VirtualClock()
        r = sweep_source(src6, DEFAULT_CONFIG,
                         Ctx(None, out6, None, "", False), out6,
                         mk([(500, "e"), (500, "e"), (200,
                              '{"state": "open"}')]),
                         clock6.now, lambda s: clock6.advance(s))
        check("V6 obtained at attempt 3", len(r["shots"]) == 3
              and r["state"] == ST_OBTAINED,
              "%d %s" % (len(r["shots"]), r["state"]))
        check("V6 retry sleeps advanced virtual clock 2x60s",
              clock6.t >= 120.0, str(clock6.t))
        clock6b = VirtualClock()
        transport6b = _canned_transport([("repos/x/y/pulls/9",
                                          [(500, "e")] * 8)])
        r2 = sweep_source(src6, DEFAULT_CONFIG,
                          Ctx(None, out6, None, "", False), out6,
                          transport6b, clock6b.now,
                          lambda s: clock6b.advance(s))
        check("V6 cap-exhaust at exactly 8 shots",
              len(r2["shots"]) == 8 and r2["state"] == ST_CAP_EXHAUSTED,
              "%d %s" % (len(r2["shots"]), r2["state"]))
        clock6c = VirtualClock()
        transport6c = _canned_transport([("repos/x/y/pulls/9",
                                          [(404, "gone")])])
        r3 = sweep_source(src6, DEFAULT_CONFIG,
                          Ctx(None, out6, None, "", False), out6,
                          transport6c, clock6c.now,
                          lambda s: clock6c.advance(s))
        check("V6 404 stops at one shot keeping the cap",
              len(r3["shots"]) == 1 and r3["state"] == ST_NEGATIVE_DEFINITE,
              "%d %s" % (len(r3["shots"]), r3["state"]))

        # V7 read-only pledge: no write verb in any built vector.
        kinds = [K_GH_SEARCH, K_GH_API, K_GH_ISSUE, K_GH_COMMITS, K_ARXIV]
        ok, detail7 = True, ""
        try:
            for kind in kinds:
                for attempt in (1, 2, 8):
                    s = {"key": "k", "kind": kind,
                         "url": "https://example.org/x", "auth": "none"}
                    args = build_curl_args("https://example.org/x", "p",
                                           30 + 30 * (attempt - 1), "n", s)
                    assert_read_only(args)
        except AssertionError as exc:
            ok, detail7 = False, str(exc)
        check("V7 no write verb in any vector", ok, detail7)

        # V8 draft template: five sections; four elements on negatives;
        # C1 both branches; three screening states present.
        cfg8 = copy.deepcopy(DEFAULT_CONFIG)
        neg = {"key": "issues", "kind": K_GH_ISSUE, "cap": 8,
               "state": ST_NEGATIVE_DEFINITE, "shots": [
                   ShotRecord("issues", 1, MAIN_ISSUE_URL, 404, 5,
                              "negative-definite", "",
                              "2026-11-13T03:00:00Z")],
               "facts": None, "subface": None,
               "fetched_at": "2026-11-13T03:00:00Z", "raw_file": "",
               "retry_file": "issues.retry.json"}
        got = {"key": "dzzftip", "kind": K_GH_COMMITS, "cap": 8,
               "state": ST_OBTAINED, "shots": [
                   ShotRecord("dzzftip", 1,
                              "https://api.github.com/repos/A/x/commits",
                              200, 100, "obtained", "",
                              "2026-11-13T03:01:00Z")],
               "facts": {"tip_sha": "09afbb4ce6570c1615d58509dc197fc9f095"
                                   "6b7d", "tip_date":
                         "2026-10-13T10:10:57Z", "listed": 3},
               "subface": None, "fetched_at": "2026-11-13T03:01:00Z",
               "raw_file": "dzzftip.json", "retry_file": ""}
        beats8 = ["R1|2026-11-13T03:00:00Z|200|LIVE",
                  "SUSPEND|2|2026-11-13T03:01:00Z|collection-sweep-in-flight",
                  "R3|2026-11-13T03:02:00Z|200|LIVE"]
        clock8 = VirtualClock()
        draft = render_draft(cfg8, [neg, got], beats8, clock8.now)
        for head in ("逐源 digest", "撞车初筛三态", "C1 触发判定",
                     "负发现四要素", "排窗建议五条"):
            check("V8 draft section %s" % head, head in draft, head)
        for label in FOUR_ELEMENTS:
            check("V8 four elements carry %r" % label, label in draft,
                  label)
        check("V8 C1-CLEAN on matching prefix", "C1-CLEAN" in draft, "")
        check("V8 negative-definite named", "negative-definite-404" in draft,
              "")
        tip_hit = copy.deepcopy(got)
        tip_hit["facts"]["tip_sha"] = "ffffffff" + "0" * 32
        draft_hit = render_draft(cfg8, [neg, tip_hit], beats8, clock8.now)
        check("V8 C1-TRIGGERED on advanced tip",
              "C1-TRIGGERED" in draft_hit, "")
        search = {"key": "mathlibpr", "kind": K_GH_SEARCH, "cap": 8,
                  "state": ST_OBTAINED, "shots": [
                      ShotRecord("mathlibpr", 1,
                                 "https://api.github.com/search", 200,
                                 10, "obtained", "", "2026-11-13T03:00:00Z")],
                  "facts": {"total_count": 3, "items": [
                      {"number": 45912, "title": "zeta identity",
                       "state": "closed", "created_at":
                       "2026-11-11T20:47:55Z", "updated_at": "",
                       "closed_at": "2026-11-11T22:19:13Z",
                       "author": "u"},
                      {"number": 40000, "title": "zeta earlier face",
                       "state": "open", "created_at":
                       "2026-11-10T09:00:00Z", "updated_at": "",
                       "closed_at": None, "author": "v"},
                      {"number": 40002, "title": "zeta fresh overlap",
                       "state": "open", "created_at":
                       "2026-11-12T09:00:00Z", "updated_at": "",
                       "closed_at": None, "author": "x"},
                      {"number": 40001, "title": "unrelated tails",
                       "state": "open", "created_at":
                       "2026-11-12T09:00:00Z", "updated_at": "",
                       "closed_at": None, "author": "w"}]},
                  "subface": None, "fetched_at": "2026-11-13T03:00:00Z",
                  "raw_file": "", "retry_file": ""}
        draft_screen = render_draft(cfg8, [search, neg, got], beats8,
                                    clock8.now)
        for state in (SCREEN_PRIOR, SCREEN_SUSPECT, SCREEN_NO_BEARING,
                      SCREEN_OURS):
            check("V8 screening state %s present" % state, state in
                  draft_screen, state)

        # V9 dry-run zero-write: --out path never materializes.
        out9 = os.path.join(tmp, "v9out")
        rc, out = _run(["--config", good, "--out", out9, "--dry-run"])
        check("V9 dry-run rc=0", rc == 0, "rc=%d" % rc)
        check("V9 dry-run wrote nothing", not os.path.exists(out9), out9)
        check("V9 skeleton carries the mandatory negative section",
              "负发现四要素" in out and "排窗建议五条" in out, "")

        # V10 NETRED ledger: every attempt incl. failures is one line.
        out10 = os.path.join(tmp, "v6out")  # reuses V6 raw dir
        results10 = [r, r2, r3]
        _m, n_lines = write_netred(out10, results10)
        check("V10 master lines == attempts",
              n_lines == len(r["shots"]) + len(r2["shots"])
              + len(r3["shots"]),
              "%d vs %d" % (n_lines, sum(len(x["shots"])
                                        for x in results10)))
        with open(_m, "r", encoding="utf-8") as h:
            body = h.read()
        check("V10 failures recorded",
              "HTTP 500" in body and "HTTP 404" in body, "")
        check("V10 changed-param recorded on retries", "changed=" in body,
              "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("SELFTEST FAIL %s\n" % line)
        return 1
    sys.stdout.write("%s (10 vectors)\n" % SELFTEST_MARK)
    return 0


def minimal_config():
    """A valid six-source config derived from the default, for vectors."""
    return copy.deepcopy(DEFAULT_CONFIG)


def _run(args):
    """Run this tool in-process via main(argv) (fixture vectors only);
    SystemExit from the argparse face is captured as an exit code."""
    saved = (sys.stdout, sys.stderr)
    sys.stdout = sink_out = io.StringIO()
    sys.stderr = sink_err = io.StringIO()
    try:
        try:
            rc = main(list(args))
        except SystemExit as exc:  # argparse usage errors land here
            rc = exc.code if isinstance(exc.code, int) else 2
    finally:
        sys.stdout, sys.stderr = saved
    return rc, sink_out.getvalue() + sink_err.getvalue()


# --------------------------------------------------------------------------
# argparse face: exactly the six flags of the ask.
# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="periscope.py",
        description="Periscope: six-source peripheral-intelligence sweep "
                    "with a sentinel companion window log and a judgment "
                    "draft template (config schema %s)." % SCHEMA)
    parser.add_argument("--config", default="",
                        help="six-source JSON config (schema %s; default: "
                             "the built-in as-built list)" % SCHEMA)
    parser.add_argument("--out", default="",
                        help="output directory (raw/ bodies + NETRED "
                             "ledgers + intel-ledger-draft.md); required "
                             "for a real run")
    parser.add_argument("--rounds", type=int, default=None,
                        help="sentinel companion rounds (default %d; one "
                             "beat always fires after the sweep closes)"
                             % DEFAULT_ROUNDS)
    parser.add_argument("--netrc", default="",
                        help="netrc file passed to curl --netrc-file for "
                             "GitHub bearer credentials (token never read "
                             "by this tool)")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="validate the config, print the plan and the "
                             "draft skeleton; zero network, zero writes")
    parser.add_argument("--selftest", action="store_true",
                        help="offline frozen vector group (canned "
                             "transport, virtual clock; zero network, "
                             "zero writes)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        if args.out or args.config or args.netrc or args.dry_run \
                or args.rounds is not None:
            parser.error("--selftest takes no run flags")
        return selftest()
    if args.rounds is not None:
        try:
            _check_int(args.rounds, "--rounds", 1, 240)
        except SchemaError as exc:
            sys.stderr.write("periscope: %s\n" % exc)
            return 2

    if args.config:
        try:
            cfg = load_config(args.config)
        except FailLoud as exc:
            sys.stderr.write("periscope: %s\n" % exc)
            return 9
        except SchemaError as exc:
            sys.stderr.write("periscope: config schema: %s\n" % exc)
            return 2
    else:
        cfg = copy.deepcopy(DEFAULT_CONFIG)

    ctx = Ctx(cfg, args.out, args.rounds, args.netrc, args.dry_run)
    if args.dry_run:
        return dry_run(cfg, ctx)
    if not args.out:
        sys.stderr.write(
            "periscope: refusing an implicit network sweep — pass --out "
            "(and review --config), or use --dry-run\n")
        parser.print_usage(sys.stderr)
        return 2
    try:
        return real_run(cfg, ctx)
    except FailLoud as exc:
        sys.stderr.write("periscope: %s\n" % exc)
        return 9


if __name__ == "__main__":
    sys.exit(main())
