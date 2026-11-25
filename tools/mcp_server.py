"""mcp_server.py - rocqwash MCP server, stdio plus optional HTTP transport (rocqwash tools/).
Purpose.  Expose the repository tool capability surface over the Model
  Context Protocol (MCP) through two transports served by one shared
  dispatcher: the newline-delimited JSON-RPC 2.0 stdio face, and the
  --http face (POST application/json on /mcp, streamable-style
  request/response, with an internal Mcp-Session-Id response header;
  Python stdlib http.server, zero new dependencies).  51 registered
  capabilities, each spec transcribed from its docs/CAPABILITY-INDEX.md
  entry line (seven later increments from their tools' own CLI contract
  headers).  Default deny for the network and heavy capabilities
  (sentinel_status, net_probe, ci_triage, pushci_status, claim_watch,
  source_fetch, release_chain): a failed tool result names
  ROCQWASH_MCP_ALLOW_NET=1 until that variable equals 1.
  Credential zero contact: no credential store, token file or netrc
  path is read; child stdout and stderr are captured, never merged into
  the protocol stream; every call runs under ROCQWASH_MCP_TIMEOUT
  (default 300) and a timed-out child is reported as failed.

Interface.  `python -I mcp_server.py [--stdio] [--http PORT
  [--http-host HOST]] [--selftest]`; the flag gate runs before any
  service loop: --selftest exits with the frozen interface-shape and
  dispatcher round-trip vectors (no stdin read, no service loop, no
  socket unless ROCQWASH_MCP_HTTP_SMOKE=1), --help exits 0, an unknown
  flag exits 2, no flag serves stdio.  --http PORT alone serves the
  HTTP face standalone; --stdio --http PORT serves both faces in one
  process, so a dead stdio pipe or a dead HTTP session costs one
  transport, never the tool registry.  The HTTP listener binds
  127.0.0.1 unless --http-host widens it (trusted-network-only: the
  endpoint performs no authentication unless ROCWASH_MCP_TOKEN is
  configured - then every POST must carry X-ROCQWASH-TOKEN or
  Authorization: Bearer, else 401; unconfigured prints one loud
  auth-disabled warning at startup and stays open, never fail-closed); GET /mcp answers 405 with a
  plain hint, other methods and paths answer 404, and a malformed
  body answers a JSON-RPC parse-error object, never a traceback.  The
  service face needs ROCQWASH_HOME at the repository root and answers
  one compact JSON-RPC 2.0 object per request (contract: docs/mcp.md).

Dependencies.  Python 3 standard library only (argparse, http.client
  [selftest smoke only], http.server, json, os, subprocess, sys,
  threading); registered CLIs resolve under ROCQWASH_HOME.

Evidence.  tests/t_mcp_face.py asserts the 51-name roster and the wire
  contract; --selftest self-proofs the frozen interface-shape vectors
  plus the dispatcher round-trip vectors (initialize, tools/list, one
  tools/call shape), with the socket smoke gated behind
  ROCQWASH_MCP_HTTP_SMOKE=1.

Exit-codes.  0 green (selftest pass, --help, stdin end of file); 1 selftest red
  (red list on stderr) or HTTP bind failure; 2 usage error (unknown flag,
  out-of-range --http port); wire error codes per docs/mcp.md.
"""

import argparse
import hmac
import http.client
import http.server
import json
import os
import subprocess
import sys
import threading

PROTOCOL_VERSION_DEFAULT = "2024-11-05"
SERVER_NAME = "rocqwash-mcp"
SERVER_VERSION = "0.1.0"
DEFAULT_TIMEOUT_S = 300
ALLOW_NET_ENV = "ROCQWASH_MCP_ALLOW_NET"
TIMEOUT_ENV = "ROCQWASH_MCP_TIMEOUT"
HOME_ENV = "ROCQWASH_HOME"
# R-1 HTTP transport: the HTTP face shares the stdio dispatcher; the
# listener binds the loopback default unless --http-host widens it
# (trusted-network-only), and the socket smoke stays env-gated out of
# the default selftest.
HTTP_ENDPOINT_PATH = "/mcp"
HTTP_DEFAULT_HOST = "127.0.0.1"
HTTP_SESSION_HEADER = "Mcp-Session-Id"
HTTP_SMOKE_ENV = "ROCQWASH_MCP_HTTP_SMOKE"
AUTH_TOKEN_ENV = "ROCWASH_MCP_TOKEN"
HTTP_MAX_BODY_BYTES = 32 * 1024 * 1024
# Frozen selftest vector: the M2 roster (25 standing specs, six M1
# additions, eleven M2 ticket additions, the tree_audit registration
# increment, the axiom_sweep registration increment, the claim_watch
# registration increment, the v2-B audit-line batch of three:
# source_fetch, sweep_verdict, release_chain, plus the numeric-probe
# registration batch of two: numeric_probe, statement_probes, plus the
# vacgen-coq registration increment (ticket 14 work stream 1, one face:
# vacgen_coq_generate, plus the formal-audit trust-face registration
# increment of four: attest_join, frozen8, verify_vo, gate4_comment_guard
# (R2-122; the MCP faces wire existing differentiated CLIs, zero new tool
# code; the frozen8 face is an exposure-list gate carrying only its two
# read-only top-level flags); a roster change re-freezes this value and
# EXPECTED_TOOLS in tests/t_mcp_face.py in the same round.
SELFTEST_ROSTER_COUNT = 56

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class InvalidParams(Exception):
    """Raised when tools/call parameters fail validation."""


def _object_schema(properties, required=()):
    """Build an inputSchema: an object with a closed property set."""
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


TOOL_SPECS = [
    {
        "name": "sentinel_status",
        "kind": "cli",
        "cli": os.path.join("tools", "cw_sentinel.py"),
        "net_gated": True,
        "fixed_args": ["--once"],
        "arg_map": (
            ("watch_repo", "--watch-repo"),
            ("branch", "--branch"),
            ("state_file", "--state-file"),
            ("timeout", "--timeout"),
            ("sleep_scale", "--sleep-scale"),
        ),
        "schema": _object_schema(
            {
                "watch_repo": {"type": "string", "description": "repository path to watch; CLI flag --watch-repo"},
                "branch": {"type": "string", "description": "branch to watch; CLI flag --branch"},
                "state_file": {"type": "string", "description": "sentinel state file path; CLI flag --state-file"},
                "timeout": {"type": "number", "description": "per step timeout in seconds; CLI flag --timeout"},
                "sleep_scale": {"type": "number", "description": "sleep scale factor; CLI flag --sleep-scale"},
            }
        ),
        "description": (
            "Run one watch round of the resident sentinel over a repo, ledgers and the "
            "build log (tools/cw_sentinel.py --once, event stream output). Default deny: "
            "the tool carries a non-zero network face in CAPABILITY-INDEX; requires "
            "ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "net_probe",
        "kind": "cli",
        "cli": os.path.join("tools", "net_probe.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("endpoints", "--endpoints"),
            ("rounds", "--rounds"),
            ("interval", "--interval"),
            ("stable_window", "--stable-window"),
            ("seed", "--seed"),
        ),
        "schema": _object_schema(
            {
                "endpoints": {"type": "string", "description": "comma separated endpoint list; CLI flag --endpoints"},
                "rounds": {"type": "integer", "description": "number of probe rounds; CLI flag --rounds"},
                "interval": {"type": "number", "description": "seconds between rounds; CLI flag --interval"},
                "stable_window": {
                    "type": "integer",
                    "description": "consecutive all-pass rounds for a stable window; CLI flag --stable-window",
                },
                "seed": {"type": "integer", "description": "jitter seed; CLI flag --seed"},
            }
        ),
        "description": (
            "Probe bare GET reachability over endpoints for N rounds with a two round "
            "stable window rule (tools/net_probe.py). Default deny: network probing is "
            "the tool's own subject; requires ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "baselinediff",
        "kind": "cli",
        "cli": os.path.join("tools", "baseline_diff.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("old", "@0"),
            ("new", "@1"),
            ("json_out", "--json"),
            ("md_out", "--md"),
        ),
        "schema": _object_schema(
            {
                "old": {"type": "string", "description": "path of the old baseline JSON file (positional OLD)"},
                "new": {"type": "string", "description": "path of the new baseline JSON file (positional NEW)"},
                "json_out": {"type": "string", "description": "write the JSON report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
            },
            required=("old", "new"),
        ),
        "description": (
            "Compare two baseline JSON files and report additions and removals "
            "(tools/baseline_diff.py OLD NEW, JSON and markdown output). Zero network face."
        ),
    },
    {
        "name": "ci_triage",
        "kind": "cli",
        "cli": os.path.join("tools", "ci_triage.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("run", "--run"),
            ("logs", "--logs"),
            ("offline", "--offline"),
            ("timeout", "--timeout"),
            ("retry_max", "--retry-max"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "repository slug for the CI query; CLI flag --repo"},
                "run": {"type": "integer", "description": "CI run number to triage; CLI flag --run"},
                "logs": {"type": "boolean", "description": "include fetched log dumps in the output; bare CLI flag --logs"},
                "offline": {"type": "string", "description": "path to a jobs JSON file to triage from local input instead of fetching (CLI --offline JOBS.json)"},
                "timeout": {"type": "number", "description": "network timeout in seconds; CLI flag --timeout"},
                "retry_max": {"type": "integer", "description": "maximum retries; CLI flag --retry-max"},
            }
        ),
        "description": (
            "Fetch and triage logs of failing CI runs and emit a verdict (tools/ci_triage.py). "
            "Default deny: requires ROCQWASH_MCP_ALLOW_NET=1; the gate is tool level, so "
            "--offline calls are gated here too."
        ),
    },
    {
        "name": "vacgen_generate",
        "kind": "cli",
        "cli": os.path.join("tools", "vacgen.py"),
        "net_gated": False,
        "fixed_args": [],
        # Full MCP flag face of tools/vacgen.py (21 flags, argparse
        # declaration order).  Count convention (baseline 20/23, unchanged
        # by the cast-repair work stream): the argparse face now holds 24
        # add_argument sites; the 3 mode flags stay outside this schema on
        # purpose (--from-statements/--from-repo ride the statement_probes
        # MCP face, --selftest is not exposed), so 24 - 3 = 21 here.  The
        # micro-ticket expanded this schema from the previous 11-flag
        # subset; the cast-repair work stream appended the opt-in
        # allow_bare_type_limb W5 waiver flag; properties and arg_map stay
        # one-to-one.
        "arg_map": (
            ("input", "--in"),
            ("out", "--out"),
            ("toolchain", "--toolchain"),
            ("snapshot", "--snapshot"),
            ("audit_id", "--audit-id"),
            ("name", "--name"),
            ("worktree", "--worktree"),
            ("lake", "--lake"),
            ("guard", "--guard"),
            ("core", "--core"),
            ("force", "--force"),
            ("taxonomy", "--taxonomy"),
            ("preflight_all", "--preflight-all"),
            ("census", "--census"),
            ("root", "--root"),
            ("cluster_table", "--cluster-table"),
            ("report", "--report"),
            ("exp_draft", "--exp-draft"),
            ("verify_anchors", "--verify-anchors"),
            ("mathlib", "--mathlib"),
            ("allow_bare_type_limb", "--allow-bare-type-limb"),
        ),
        "schema": _object_schema(
            {
                "input": {"type": "string", "description": "input Lean source file (the statement-face file of the audited artifact; mutually exclusive with preflight_all); CLI flag --in"},
                "out": {"type": "string", "description": "output four-account skeleton directory; CLI flag --out"},
                "toolchain": {"type": "string", "description": "Lean toolchain pin recorded in the headers; CLI flag --toolchain"},
                "snapshot": {"type": "string", "description": "mathlib snapshot window recorded in the headers; CLI flag --snapshot"},
                "audit_id": {"type": "string", "description": "audit identifier stamped into the skeleton header; CLI flag --audit-id"},
                "name": {"type": "string", "description": "artifact name (default: the sanitized input file stem); CLI flag --name"},
                "worktree": {"type": "string", "description": "compile working tree recorded in the build command line; CLI flag --worktree"},
                "lake": {"type": "string", "description": "lake executable recorded in the build command line; CLI flag --lake"},
                "guard": {"type": "string", "description": "cpu_guard wrapper recorded in the build command line; CLI flag --guard"},
                "core": {"type": "integer", "description": "core count recorded in the build command line; CLI flag --core"},
                "force": {"type": "boolean", "description": "overwrite the generator-owned targets if they exist; bare CLI flag --force"},
                "taxonomy": {"type": "string", "description": "taxonomy table path (chain: this flag, then the VACGEN_TAXONOMY environment variable, then the tool-adjacent taxonomy.json, then the builtin starter row); CLI flag --taxonomy"},
                "preflight_all": {"type": "boolean", "description": "preflight mode over census-qualified files: zero-compile coverage pass into a difficulty map (mutually exclusive with input); bare CLI flag --preflight-all"},
                "census": {"type": "string", "description": "census.json path (required with preflight_all; read-only); CLI flag --census"},
                "root": {"type": "string", "description": "clone root the census walk used (required with preflight_all); CLI flag --root"},
                "cluster_table": {"type": "string", "description": "optional cluster keyword table JSON (the stratify key surface) for by-cluster aggregation; CLI flag --cluster-table"},
                "report": {"type": "string", "description": "coverage report JSON path in cast mode, or difficulty map path in preflight mode (default difficulty-map.json in the working directory); CLI flag --report"},
                "exp_draft": {"type": "string", "description": "experience-ledger draft JSON path written in cast mode; CLI flag --exp-draft"},
                "verify_anchors": {"type": "boolean", "description": "re-run the anchor admission gate over the loaded taxonomy table; bare CLI flag --verify-anchors"},
                "mathlib": {"type": "string", "description": "mathlib checkout root used by verify_anchors; CLI flag --mathlib"},
                "allow_bare_type_limb": {"type": "boolean", "description": "opt-in W5 waiver: release a cast through the bare-type-conjunct-limb front gate when a limb head resolves neither as the audited file's own def : Prop nor as a Mathlib/Std predicate family head; every released limb is registered loud on stdout and in the report JSON (report.waiver); the default (flag off) stays fail-loud rc=1; bare CLI flag --allow-bare-type-limb"},
            }
        ),
        "description": (
            "Cast a Lean vacuity probe skeleton with the four layer shape recognition engine "
            "(tools/vacgen.py, zero-compile casting face). The schema mirrors the tool's "
            "argparse flag face minus the 3 mode flags (--from-statements/--from-repo live on "
            "the statement_probes face, --selftest is not exposed): all 21 flags, one-to-one. "
            "Zero network face. The compile "
            "verification leg needs a Lean toolchain and stays a design SKIP face when the "
            "toolchain is absent."
        ),
    },
    {
        "name": "exp_append",
        "kind": "cli",
        "cli": os.path.join("tools", "exp_port.py"),
        "net_gated": False,
        "fixed_args": ["append"],
        "arg_map": (
            ("tool", "--tool"),
            ("points", "--points"),
            ("evidence", "--evidence"),
            ("batch", "--batch"),
            ("actor", "--actor"),
        ),
        "schema": _object_schema(
            {
                "tool": {"type": "string", "description": "tool name of the entry"},
                "points": {"type": "string", "description": "one-line takeaways of the entry"},
                "evidence": {"type": "string", "description": "evidence pointer of the entry"},
                "batch": {"type": "string", "description": "batch label of the entry"},
                "actor": {"type": "string", "description": "optional actor (seat or operator name) carried verbatim on the appended ledger row; empty default (the field is first-class since the micro-ticket that promoted the points-line prefix workaround; it stays outside the idempotent fingerprint seen set); CLI flag --actor"},
            },
            required=("tool", "points"),
        ),
        "description": (
            "Append one structured experience entry to the in-repo experience ledger "
            "(tools/exp_port.py append, schema rocqwash-exp/1, idempotent seen set: "
            "re-appending an already-seen entry returns the existing id and writes "
            "nothing). The optional actor field rides the appended row verbatim when "
            "provided and stays outside the fingerprint seen set. The returned text "
            "carries the entry id of the ledger line."
        ),
    },
    {
        "name": "pushci_status",
        "kind": "cli",
        "cli": os.path.join("tools", "pushci.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("repo_path", "--repo-path"),
            ("branch", "--branch"),
            ("base_ref", "--base-ref"),
            ("dry_run", "--dry-run"),
            ("watch_interval", "--watch-interval"),
            ("watch_max_rounds", "--watch-max-rounds"),
            ("timeout", "--timeout"),
        ),
        "schema": _object_schema(
            {
                "repo_path": {"type": "string", "description": "local repository path to push; CLI flag --repo-path"},
                "branch": {"type": "string", "description": "branch to push and watch; CLI flag --branch"},
                "base_ref": {"type": "string", "description": "base ref for comparison; CLI flag --base-ref"},
                "dry_run": {"type": "boolean", "description": "plan without pushing; CLI flag --dry-run"},
                "watch_interval": {"type": "number", "description": "watch poll interval in seconds; CLI flag --watch-interval"},
                "watch_max_rounds": {"type": "integer", "description": "maximum watch rounds; CLI flag --watch-max-rounds"},
                "timeout": {"type": "number", "description": "network timeout in seconds; CLI flag --timeout"},
            }
        ),
        "description": (
            "One-shot push then CI orchestration: push, ls-remote confirmation, run watching, "
            "verdict reading and heal rounds (tools/pushci.py). Default deny: network and "
            "remote write face; requires ROCQWASH_MCP_ALLOW_NET=1."
        ),
    },
    {
        "name": "capability_index",
        "kind": "cli",
        "cli": os.path.join("tools", "capability_index.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("mode", "--mode"),
            ("tool", "--tool"),
        ),
        "schema": _object_schema(
            {
                "mode": {"type": "string", "enum": ["full", "summary"], "description": "index render: full (default) emits the complete per-tool record set sorted by tool name, summary emits exactly one line per tool (name, one-phrase purpose, MCP face count) and exists because the full index overran harness response caps in two measured rounds (130KB against 50KB); CLI flag --mode"},
                "tool": {"type": "string", "description": "optional single-tool filter rendering one full record (tool base name with or without .py, e.g. chain_graph or chain_graph.py); full mode only, a summary/tool combination is refused as usage on the CLI; CLI flag --tool"},
            }
        ),
        "description": (
            "Tool capability index rendered from the census masters "
            "(tools/capability_index.py reads docs/census-tools.json and "
            "docs/flag-shape.json, plus the TOOL_SPECS roster of this server "
            "read AST-level, so a summary count and a full record cannot "
            "disagree). mode=full (default, unchanged by the summary "
            "increment) renders the complete index, one full record per "
            "censused tool, sorted by tool name; mode=summary renders one "
            "line per tool (name, one-phrase purpose, MCP face count); "
            "tool=<name> renders the single full record of one tool and "
            "equals that tool's block in full mode. Zero network face, "
            "read-only; the --selftest face stays CLI-side."
        ),
    },
    # ---- zero-network capabilities: thirteen specs, each transcribed
    # from its docs/CAPABILITY-INDEX.md section 2 entry line.
    # baseline_diff was already on this face as baselinediff (above) and
    # is not re-registered.
    {
        "name": "chain_graph",
        "kind": "cli",
        "cli": os.path.join("tools", "chain_graph.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("ledgers", "@0"),
            ("json_out", "--json"),
            ("md_out", "--md"),
            ("top", "--top"),
        ),
        "schema": _object_schema(
            {
                "ledgers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "probe ledger JSON paths, merged into one chain-root graph (positional LEDGER.json list)",
                },
                "json_out": {"type": "string", "description": "write the rocqwash-chain-graph/1 JSON report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
                "top": {"type": "integer", "description": "ranked-list length cap; CLI flag --top"},
            },
            required=("ledgers",),
        ),
        "description": (
            "Merge probe ledgers into a chain-root graph and a ranked list (tools/chain_graph.py, "
            "graph schema rocqwash-chain-graph/1; the ledgers array carries one LEDGER.json path "
            "per element). Zero network face. The CLI also dispatches a --selftest frozen-vector "
            "face before argparse; it is not part of the INDEX entry line and not exposed here."
        ),
    },
    {
        "name": "doc_lint",
        "kind": "cli",
        "cli": os.path.join("tools", "doc_lint.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("json_out", "--json"),
            ("help_cap", "--help-cap"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "audited repository root; CLI flag --repo (defaults to the repo holding the tool)"},
                "json_out": {"type": "string", "description": "write the rocqwash-doclint/1 report to this path; CLI flag --json"},
                "help_cap": {"type": "integer", "description": "check-3 real --help run cap; CLI flag --help-cap"},
            }
        ),
        "description": (
            "Docs-versus-implementation consistency three-check over a repository: the tool table "
            "(cw.sh four-place mutual inspection plus the tools/ generic-entry reconciliation), the "
            "count check (suite roster versus README count lines) and the flag check (doc-cited "
            "flags versus real --help output, capped) (tools/doc_lint.py, schema rocqwash-doclint/1). "
            "Zero network face; the flag check runs in-repo tools with --help only (read-only)."
        ),
    },
    {
        "name": "ledger_sync",
        "kind": "cli",
        "cli": os.path.join("tools", "ledger_sync.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("probe", "--probe"),
            ("ledger", "--ledger"),
            ("out", "--out"),
            ("report", "--report"),
            ("policy", "--policy"),
        ),
        "schema": _object_schema(
            {
                "probe": {"type": "string", "description": "probe ledger TSV path; CLI flag --probe"},
                "ledger": {"type": "string", "description": "status ledger TSV path; CLI flag --ledger"},
                "out": {"type": "string", "description": "merged TSV output path; CLI flag --out"},
                "report": {"type": "string", "description": "sync report output path; CLI flag --report"},
                "policy": {"type": "string", "description": "merge policy name; CLI flag --policy"},
            }
        ),
        "description": (
            "TSV merge synchronizer between the probe ledger and the status ledger, with the "
            "merge policy parameterized (tools/ledger_sync.py). Zero network face."
        ),
    },
    {
        "name": "netname_normalize",
        "kind": "cli",
        "cli": os.path.join("tools", "netname_normalize.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("dir", "--dir"),
            ("apply", "--apply"),
            ("map", "--map"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "dir": {"type": "string", "description": "world directory indexed by os.walk; CLI flag --dir"},
                "apply": {"type": "boolean", "description": "apply the renames instead of reporting only; bare CLI flag --apply"},
                "map": {"type": "string", "description": "write the rename mapping table to this TSV path; CLI flag --map"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Normalize doubled .v.v file suffixes over a world directory; the mapping table can be "
            "emitted (--map) or applied (--apply, the write face) (tools/netname_normalize.py). "
            "Zero network face; --apply renames only inside the directory given by --dir."
        ),
    },
    {
        "name": "norm_lint",
        "kind": "cli",
        "cli": os.path.join("tools", "norm_lint.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("tree", "--tree"),
            ("file", "--file"),
            ("jargon_map", "--jargon-map"),
            ("cjk_threshold", "--cjk-threshold"),
            ("cjk_whitelist", "--cjk-whitelist"),
            ("json_out", "--json"),
            ("md_out", "--md"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "tree": {"type": "string", "description": "directory to lint (mutually exclusive with file); CLI flag --tree"},
                "file": {"type": "string", "description": "single file to lint (mutually exclusive with tree); CLI flag --file"},
                "jargon_map": {"type": "string", "description": "jargon mapping file path; CLI flag --jargon-map"},
                "cjk_threshold": {"type": "number", "description": "CJK ratio threshold; CLI flag --cjk-threshold"},
                "cjk_whitelist": {"type": "string", "description": "CJK whitelist file path; CLI flag --cjk-whitelist"},
                "json_out": {"type": "string", "description": "write the rocqwash-norm-lint/1 report to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the human-readable report to this path; CLI flag --md"},
                "selftest": {"type": "boolean", "description": "run the built-in frozen-vector selftest; bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Annotation-face normalization lint in report-first form over one tree or one file, "
            "with the jargon map, CJK threshold and whitelist parameterized (tools/norm_lint.py, "
            "schema rocqwash-norm-lint/1). Zero network face; the built-in --selftest "
            "frozen-vector face is on the INDEX entry line and exposed here."
        ),
    },
    {
        "name": "render_events",
        "kind": "cli",
        "cli": os.path.join("tools", "render_events.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("events", "--events"),
            ("dir", "--dir"),
            ("md_out", "--md"),
            ("json_out", "--json"),
            ("top", "--top"),
        ),
        "schema": _object_schema(
            {
                "events": {"type": "string", "description": "event stream JSONL path; accepted row shapes, declared per the tool's measured behavior: rocqwash-sentinel-event/1 rows (the native cw_sentinel.py stream) or any JSON-object-per-line stream such as rocqwash-exp/1 experience-ledger rows (unknown keys are ignored; missing kind counts as other, missing family/action as (none)); CLI flag --events"},
                "dir": {"type": "string", "description": "event directory alternative input; every *.jsonl file inside is merged (same accepted row shapes as events); CLI flag --dir"},
                "md_out": {"type": "string", "description": "markdown ledger output path; CLI flag --md"},
                "json_out": {"type": "string", "description": "JSON report output path; CLI flag --json"},
                "top": {"type": "integer", "description": "ranked-list length cap; CLI flag --top"},
            }
        ),
        "description": (
            "Render a JSONL event stream into a markdown ledger (tools/render_events.py; input "
            "via --events or --dir, output via --md or --json). Accepted input shapes, declared "
            "per the tool's measured behavior (an exp/1 stream of 58 rows rendered with "
            "bad_lines=0): rocqwash-sentinel-event/1 rows, the native cw_sentinel.py stream, "
            "and any JSON-object-per-line stream, e.g. rocqwash-exp/1 experience-ledger rows; "
            "rows not matching the native shape render with kind counted as other and "
            "family/action as (none), and bad lines are skipped and counted, never fatal. "
            "Zero network face."
        ),
    },
    {
        "name": "select_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "select_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("order", "--order"),
            ("select", "--select"),
            ("grep", "--grep"),
            ("requires", "--requires"),
            ("world", "--world"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "order": {"type": "string", "description": "certification tree order.txt full table (read-only); CLI flag --order"},
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "batch selection list paths, repeatable (one array element per --select occurrence)",
                },
                "grep": {"type": "string", "description": "single-name full-table grep name; CLI flag --grep"},
                "requires": {"type": "string", "description": "requires file (.v) to audit against; CLI flag --requires"},
                "world": {"type": "string", "description": "world directory for the closure face; CLI flag --world"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Audit a batch selection against the tree order file by full-table grep (tools/"
            "select_audit.py; the select array carries one selection-list path per element and "
            "maps to repeated --select occurrences). Zero network face."
        ),
    },
    {
        "name": "registry_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("order", "--order"),
            ("project", "--project"),
            ("git", "--git"),
            ("ref", "--ref"),
            ("git_path_order", "--git-path-order"),
            ("git_path_project", "--git-path-project"),
            ("live_src", "--live-src"),
            ("anchor_src", "--anchor-src"),
            ("fix_plan", "--fix-plan"),
            ("json_out", "--json"),
            ("md_out", "--md"),
        ),
        "schema": _object_schema(
            {
                "order": {"type": "string", "description": "order.txt path; CLI flag --order"},
                "project": {"type": "string", "description": "_CoqProject path; CLI flag --project"},
                "git": {"type": "string", "description": "repository to read the registry pair from; CLI flag --git"},
                "ref": {"type": "string", "description": "git ref to read; CLI flag --ref"},
                "git_path_order": {"type": "string", "description": "order.txt path inside the git tree; CLI flag --git-path-order"},
                "git_path_project": {"type": "string", "description": "_CoqProject path inside the git tree; CLI flag --git-path-project"},
                "live_src": {"type": "string", "description": "live source directory; CLI flag --live-src"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "fix_plan": {"type": "boolean", "description": "emit the deterministic fix plan; bare CLI flag --fix-plan"},
                "json_out": {"type": "string", "description": "write the audit JSON to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the markdown report to this path; CLI flag --md"},
            }
        ),
        "description": (
            "Read-only hygiene audit over the two registry files, emitting a deterministic fix "
            "plan with --fix-plan (tools/registry_audit.py, the producer side of the audit-fix "
            "pair). Zero network face; local git reads only. Aimed at serviced Coq books: on a "
            "repository whose tree carries no order.txt or _CoqProject the audit exits nonzero "
            "with its REGISTERED fail-loud face (measured; CAPABILITY-INDEX section 4.1)."
        ),
    },
    {
        "name": "registry_fix",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_fix.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("audit_json", "--audit-json"),
            ("order", "--order"),
            ("project", "--project"),
            ("anchor_src", "--anchor-src"),
            ("apply", "--apply"),
            ("work_dir", "--work-dir"),
            ("audit_tool", "--audit-tool"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "audit_json": {"type": "string", "description": "fix-plan JSON produced by registry_audit; CLI flag --audit-json"},
                "order": {"type": "string", "description": "order.txt path; CLI flag --order"},
                "project": {"type": "string", "description": "_CoqProject path; CLI flag --project"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "apply": {"type": "boolean", "description": "write the plan instead of dry running; bare CLI flag --apply"},
                "work_dir": {"type": "string", "description": "scratch work directory; CLI flag --work-dir"},
                "audit_tool": {"type": "string", "description": "registry_audit path for the same-parameter re-audit; CLI flag --audit-tool"},
                "json_out": {"type": "string", "description": "write the execution JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Apply the fix plan produced by registry_audit (tools/registry_fix.py, the executor "
            "side of the audit-fix pair; dry run by default, --apply writes under staged "
            "in-memory assertions with rollback). Zero network face. The opt-in --orphan-add face "
            "is not exposed here: it is absent from the INDEX entry line transcribed above."
        ),
    },
    {
        "name": "registry_regen",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_regen.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("base_repo", "--base-repo"),
            ("base_ref", "--base-ref"),
            ("contrib_repo", "--contrib-repo"),
            ("contrib_ref", "--contrib-ref"),
            ("pieces", "--pieces"),
            ("anchor_src", "--anchor-src"),
            ("dep_source", "--dep-source"),
            ("seq", "--seq"),
            ("base_path_order", "--base-path-order"),
            ("base_path_project", "--base-path-project"),
            ("contrib_path_order", "--contrib-path-order"),
            ("contrib_path_project", "--contrib-path-project"),
            ("out", "--out"),
            ("apply", "--apply"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "base_repo": {"type": "string", "description": "base repository; CLI flag --base-repo"},
                "base_ref": {"type": "string", "description": "base ref; CLI flag --base-ref"},
                "contrib_repo": {"type": "string", "description": "contribution repository; CLI flag --contrib-repo"},
                "contrib_ref": {"type": "string", "description": "contribution ref; CLI flag --contrib-ref"},
                "pieces": {"type": "string", "description": "piece table, comma separated module names; CLI flag --pieces"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "dep_source": {"type": "string", "description": "dependency source selector; CLI flag --dep-source"},
                "seq": {"type": "integer", "description": "row sequence number; CLI flag --seq"},
                "base_path_order": {"type": "string", "description": "order.txt path in the base repo; CLI flag --base-path-order"},
                "base_path_project": {"type": "string", "description": "_CoqProject path in the base repo; CLI flag --base-path-project"},
                "contrib_path_order": {"type": "string", "description": "order.txt path in the contribution repo; CLI flag --contrib-path-order"},
                "contrib_path_project": {"type": "string", "description": "_CoqProject path in the contribution repo; CLI flag --contrib-path-project"},
                "out": {"type": "string", "description": "output directory for the apply face; CLI flag --out"},
                "apply": {"type": "boolean", "description": "write the regenerated rows (requires out); bare CLI flag --apply"},
                "json_out": {"type": "string", "description": "write the regeneration JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Regenerate contribution registration rows onto the merge-target line (tools/"
            "registry_regen.py; base and contribution repos, refs, piece table and path table "
            "parameterized; dry run by default, --apply writes only under an explicit out). "
            "Zero network face; local git reads only."
        ),
    },
    {
        "name": "registry_union",
        "kind": "cli",
        "cli": os.path.join("tools", "registry_union.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("base", "--base"),
            ("main", "--main"),
            ("branch", "--branch"),
            ("git", "--git"),
            ("ref_base", "--ref-base"),
            ("ref_main", "--ref-main"),
            ("ref_branch", "--ref-branch"),
            ("git_path", "--git-path"),
            ("kind", "--kind"),
            ("reanchor", "--reanchor"),
            ("anchor_src", "--anchor-src"),
            ("out", "--out"),
            ("apply", "--apply"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "base": {"type": "string", "description": "base registry file; CLI flag --base"},
                "main": {"type": "string", "description": "main registry file; CLI flag --main"},
                "branch": {"type": "string", "description": "branch registry file; CLI flag --branch"},
                "git": {"type": "string", "description": "repository to read the registries from; CLI flag --git"},
                "ref_base": {"type": "string", "description": "ref for the base registry; CLI flag --ref-base"},
                "ref_main": {"type": "string", "description": "ref for the main registry; CLI flag --ref-main"},
                "ref_branch": {"type": "string", "description": "ref for the branch registry; CLI flag --ref-branch"},
                "git_path": {"type": "string", "description": "registry path inside the git tree; CLI flag --git-path"},
                "kind": {"type": "string", "description": "kind selection name; CLI flag --kind"},
                "reanchor": {"type": "string", "description": "re-anchor name list, comma separated; CLI flag --reanchor"},
                "anchor_src": {"type": "string", "description": "anchor source directory; CLI flag --anchor-src"},
                "out": {"type": "string", "description": "merged output file; CLI flag --out"},
                "apply": {"type": "boolean", "description": "write the merged file; bare CLI flag --apply"},
                "json_out": {"type": "string", "description": "write the union JSON to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Three-way union merger for the registry (tools/registry_union.py; base/main/branch "
            "inputs with re-anchoring and kind selection parameterized; dry run by default, "
            "--apply writes). Zero network face; local git reads only."
        ),
    },
    {
        "name": "abl1_4b_compile",
        "kind": "cli",
        "cli": os.path.join("tools", "_abl1_4b_compile.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("extract_dir", "@0"),
            ("driver", "@1"),
        ),
        "schema": _object_schema(
            {
                "extract_dir": {"type": "string", "description": "extracted module directory to compile (positional EXTRACT_DIR)"},
                "driver": {"type": "string", "description": "optional driver .ml to link and run (positional DRIVER.ML)"},
            },
            required=("extract_dir",),
        ),
        "description": (
            "Internal helper: incremental OCaml compilation of an extracted module directory in "
            "dependency fixpoint order, interface files first, optionally linking and running a "
            "driver (tools/_abl1_4b_compile.py, positional EXTRACT_DIR plus optional DRIVER.ML). "
            "Zero network face. Design SKIP face: the tool exits loudly when ocamlc/ocamldep are "
            "absent from PATH, so this capability needs an OCaml toolchain on the host."
        ),
    },
    {
        "name": "http_backoff",
        "kind": "cli",
        "cli": os.path.join("tools", "_http_backoff.py"),
        "net_gated": False,
        "fixed_args": ["--selftest"],
        "arg_map": (),
        "schema": _object_schema({}),
        "description": (
            "Internal shared helper: pure-function HTTP rate-limit backoff with a frozen-vector "
            "selftest, no transport and no IO (tools/_http_backoff.py). This capability exposes "
            "the --selftest face only; the helper's other face is module import by ci_triage, "
            "cw_sentinel and pushci. Zero network face."
        ),
    },
    # ---- three zero-network capability specs graduated from the draft
    # docs/drafts/mcp-tool-specs-engine-body.md; additive after the block
    # above (the existing specs and schemas untouched); the draft's only
    # network face (the i18n http provider leg) stays unregistered.
    {
        "name": "ai_flavor_detect",
        "kind": "cli",
        "cli": os.path.join("tools", "ai_flavor.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("file", "--file"),
            ("tree", "--tree"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "string", "description": "target file to scan; CLI flag --file"},
                "tree": {"type": "string", "description": "target directory to scan (*.py *.sh *.md *.json *.ts); CLI flag --tree"},
                "json_out": {"type": "string", "description": "write the rocqwash.ai-flavor.report/1 report to this path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the clean and polluted probe pair; bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Run the 36-face AI-flavor wording battery plus the em-dash battery over a file "
            "or a directory tree (tools/ai_flavor.py, schema rocqwash.ai-flavor.report/1). "
            "Zero network face, zero writes, report-first. Exit codes: 0 clean, 1 hits "
            "(findings are data, not errors), 2 usage."
        ),
    },
    {
        "name": "jargon_plan",
        "kind": "cli",
        "cli": os.path.join("tools", "jargon_apply.py"),
        "net_gated": False,
        "fixed_args": ["--plan"],
        "arg_map": (
            ("file", "--file"),
            ("tree", "--tree"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "string", "description": "target file to plan; CLI flag --file"},
                "tree": {"type": "string", "description": "target directory to plan; CLI flag --tree"},
                "json_out": {"type": "string", "description": "write the zero-write plan report (before/after pairs) to this path; CLI flag --json"},
            }
        ),
        "description": (
            "Plan jargon-to-standard rewrites over a file or a tree with zero writes "
            "(tools/jargon_apply.py --plan; before/after pairs from the 62-entry map "
            "seeds/jargon/jargon-map.json). Zero network face. The apply face is not "
            "exposed over MCP; callers carrying write duty use the CLI directly, where "
            "plan also stays the default."
        ),
    },
    {
        "name": "i18n_pipeline_dryrun",
        "kind": "cli",
        "cli": os.path.join("tools", "i18n_pipeline.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("manifest", "--manifest"),
            ("stage", "--stage"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "manifest": {"type": "string", "description": "run manifest path (i18n SPEC section 9 run manifest shape); CLI flag --manifest"},
                "stage": {"type": "string", "enum": ["p0", "p1"], "description": "dry-run stage: p0 policy pre-check (a refusal is a legal exit-0 outcome with its ledger row) or p1 segmentation with the protection list; p3/p6 are write-bearing and withheld from this face; CLI flag --stage"},
                "json_out": {"type": "string", "description": "write the stage report to this path; CLI flag --json"},
            },
            required=("manifest", "stage"),
        ),
        "description": (
            "Dry-run the analysis stages of the i18n pipeline over a run manifest "
            "(tools/i18n_pipeline.py --stage p0|p1): p0 policy pre-check and p1 "
            "segmentation with the protection list (segment ledger rows, i18n SPEC "
            "section 9 nine-key shape). Zero network face (the P2 model stage lives in "
            "tools/i18n_translate.py and is not part of this face). Write face: stage "
            "account rows go to the ledger path named by the manifest; the target face "
            "is never written at the exposed stages."
        ),
    },
    # ---- one read-only capability registered on the capability_index
    # wiring (a file-kind spec over docs/symbiosis_sop.md section 1.1;
    # no subprocess, no gate); additive after the block above (the
    # existing specs and schemas untouched).
    {
        "name": "symbiosis_status",
        "kind": "file",
        "path": os.path.join("docs", "symbiosis_sop.md"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (),
        "schema": _object_schema({}),
        "description": (
            "Return the full text of docs/symbiosis_sop.md, the single "
            "symbiosis-bus contract surface, resolved from ROCQWASH_HOME. "
            "Read-only file face on the capability_index wiring: zero "
            "network face, no subprocess, no side effects."
        ),
    },
    # ---- the MCP roster-expansion work stream 1 (the M1 ticket): six
    # read/plan
    # faces over the terminology seed, the sweep judgments, and the standing
    # account reports. Each spec is transcribed from its
    # docs/CAPABILITY-INDEX.md section 2 entry line (the gap_cluster entry
    # lands with this increment), additive after the block above: the
    # existing specs and schemas untouched. Layer law: zero apply face, zero
    # ledger-append face, zero credential face, zero network gate; the two
    # plan faces write only caller-named output files, and the two account
    # faces declare their single fixed derived-report writes.
    {
        "name": "termbase",
        "kind": "cli",
        "cli": os.path.join("tools", "termbase.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("lookup", "--lookup"),
            ("schema_check", "--schema-check"),
            ("selftest", "--selftest"),
            ("db", "--db"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "lookup": {"type": "string", "description": "term to look up against the current-term faces; CLI flag --lookup"},
                "schema_check": {"type": "boolean", "description": "validate the database schema only; CLI flag --schema-check"},
                "selftest": {"type": "boolean", "description": "run the selftest vectors; CLI flag --selftest"},
                "db": {"type": "string", "description": "database path (default: the built-in seed); CLI flag --db"},
                "json_out": {"type": "string", "description": "write the report to this path instead of stdout; CLI flag --json"},
            }
        ),
        "description": (
            "Read-only terminology lookup thin layer over the E3 seed "
            "(tools/termbase.py --lookup; schema validation fails loud). "
            "Zero network face; zero repository writes; the only output faces "
            "are stdout and the caller-named --json report."
        ),
    },
    {
        "name": "verdict_diff",
        "kind": "cli",
        "cli": os.path.join("tools", "verdict_diff.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("results_lane", "--results-lane"),
            ("expected", "--expected"),
            ("batches", "--batches"),
            ("baseline", "--baseline"),
            ("json_out", "--json"),
            ("md_out", "--md"),
        ),
        "schema": _object_schema(
            {
                "results_lane": {"type": "string", "description": "glob of per-lane ledgers, e.g. DIR/results-lane*.tsv; CLI flag --results-lane"},
                "expected": {"type": "string", "description": "expected universe JSON for the MISSING face (alternative to --batches); CLI flag --expected"},
                "batches": {"type": "string", "description": "sweep batches plan JSON as the expected universe (alternative to --expected); CLI flag --batches"},
                "baseline": {"type": "string", "description": "prior judgment-table report for the convergence diff; CLI flag --baseline"},
                "json_out": {"type": "string", "description": "write the report JSON (schema rocqwash-verdict-diff/1) to this path; CLI flag --json"},
                "md_out": {"type": "string", "description": "write the human-readable markdown table to this path; CLI flag --md"},
            },
            required=("results_lane",),
        ),
        "description": (
            "Mechanical judge for vacuity probe sweep results: merges per-lane "
            "ledgers into the judgment table plus a named exception list, with "
            "an optional baseline convergence diff (tools/verdict_diff.py "
            "--results-lane). Zero network face; outputs go to stdout and the "
            "caller-named --json/--md paths. The tool's pre-argparse --selftest "
            "route is not exposed (the registered chain_graph precedent); "
            "callers needing it use the CLI directly."
        ),
    },
    {
        "name": "learning_feedback",
        "kind": "cli",
        "cli": os.path.join("tools", "learning_feedback.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "selftest": {"type": "boolean", "description": "run the seven selftest vectors on temporary fixtures (zero repository paths); CLI flag --selftest"},
            }
        ),
        "description": (
            "Scheduling feedback face over the three standing ledgers: the "
            "round ledger, the round state, and the experience ledger are read "
            "strictly read-only and cast into the scheduling feedback face "
            "(schema rocqwash.scheduling-feedback/1). The default run writes "
            "exactly one derived report, docs/scheduling-feedback.json (a "
            "deterministic regeneration; the three inputs are never written); "
            "missing or corrupt inputs are named in the errors list and exit 1 "
            "fail-loud (tools/learning_feedback.py). --selftest runs the seven "
            "vectors on temporary fixtures. Zero network face."
        ),
    },
    {
        "name": "b_gate_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "b_gate_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "selftest": {"type": "boolean", "description": "run four offline vectors on temporary files; CLI flag --selftest"},
            }
        ),
        "description": (
            "Measure the B-level generalization gate from round records: reads "
            "the round ledger, round state and taxonomy files strictly "
            "read-only and writes the derived audit report "
            "docs/b-gate-audit.json (schema rocqwash.b-gate-audit/1, sorted "
            "keys, deterministic) plus a stdout summary; a not-ready verdict "
            "is data and exits 0, read errors are named in the errors field "
            "and exit 1 fail-loud (tools/b_gate_audit.py). --selftest runs the "
            "vectors offline on temporary files. Zero network face."
        ),
    },
    {
        "name": "evolution_dashboard",
        "kind": "cli",
        "cli": os.path.join("tools", "evolution_dashboard.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("exp_ledger", "--exp-ledger"),
            ("rounds", "--rounds"),
            ("reports", "--reports"),
            ("json_out", "--json-out"),
            ("md_out", "--md-out"),
            ("stdout", "--stdout"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "repository root (default: the parent of tools/); CLI flag --repo"},
                "exp_ledger": {"type": "string", "description": "experience ledger path (default docs/exp-ledger.jsonl under the repo root; an explicit path must exist); CLI flag --exp-ledger"},
                "rounds": {"type": "string", "description": "round ledger path (default docs/round-ledger.jsonl under the repo root; an explicit path must exist); CLI flag --rounds"},
                "reports": {"type": "array", "description": "vacgen report file or directory, repeatable (default docs/vacgen-reports under the repo root); CLI flag --reports"},
                "json_out": {"type": "string", "description": "write the JSON face to this file; CLI flag --json-out"},
                "md_out": {"type": "string", "description": "write the markdown face to this file; CLI flag --md-out"},
                "stdout": {"type": "string", "enum": ["markdown", "json"], "description": "full face printed to stdout (default markdown); CLI flag --stdout"},
                "selftest": {"type": "boolean", "description": "frozen fixture vectors; zero writes outside one temporary directory; CLI flag --selftest"},
            }
        ),
        "description": (
            "Self-evolution dashboard over the experience ledger, the round "
            "ledger, and vacgen v2 TODO-SEAT report faces "
            "(tools/evolution_dashboard.py). The plan face prints to stdout by "
            "default and writes only the caller-named --json-out/--md-out "
            "files; absent accounts are data (reported as present=false), not "
            "faults. Zero network face."
        ),
    },
    {
        "name": "gap_cluster",
        "kind": "cli",
        "cli": os.path.join("tools", "gap_cluster.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("ledger", "--ledger"),
            ("reports", "--reports"),
            ("out", "--out"),
            ("json", "--json"),
        ),
        "schema": _object_schema(
            {
                "ledger": {"type": "array", "description": "experience ledger JSONL (schema rocqwash-exp/1), repeatable; CLI flag --ledger"},
                "reports": {"type": "array", "description": "vacgen report JSON file or a directory of *.json files, repeatable; CLI flag --reports"},
                "out": {"type": "string", "description": "write the gap ledger JSON (schema rocqwash-gap-ledger/1) to this caller-named file; CLI flag --out"},
                "json": {"type": "boolean", "description": "print the gap ledger JSON to stdout; CLI flag --json"},
            }
        ),
        "description": (
            "Aggregate TODO-SEAT and gap entries from the experience ledger "
            "and the vacgen report faces into a family-shape-keyed gap ledger "
            "(tools/gap_cluster.py). Aggregation is a pure function of the "
            "input bytes: fixed ordering rules, no wall clock, basenames only, "
            "so equal inputs give byte-identical output; the only write is the "
            "explicit caller-named --out gap ledger; --json prints to stdout; "
            "zero gaps is data (empty cluster list, exit 0); missing or "
            "corrupt input exits 9 fail-loud. Zero network face."
        ),
    },
    # ---- the MCP roster-expansion work stream 2 (the M2 ticket): eleven
    # read/plan/partial faces over the repair and roster guards, the
    # scheduler, the axiom guard, the cross-repository bus and uplink
    # gates, the i18n handoff faces, the red dispatcher, and the row
    # renderer.  Each spec is transcribed from its
    # docs/CAPABILITY-INDEX.md section 2 entry line (the roster survey
    # table 2 rows 7-17), additive after the block above: the existing
    # specs and schemas untouched.  Layer law face by face: zero apply
    # face, zero ledger-append face, zero credential face, zero network
    # leg (the three http provider legs stay unregistered, the provider
    # argument never enters the schemas, so the call forms carry the
    # default zero-network providers).  The apply, import, intake,
    # ingest, and auto-tier faces stay CLI-side per the plan-first layer
    # law (the jargon_plan and i18n_pipeline_dryrun precedents);
    # choice-pinned faces declare their withheld choices in the schema
    # enum (the registered i18n_pipeline_dryrun stage form).
    {
        "name": "repair_weekly",
        "kind": "cli",
        "cli": os.path.join("tools", "repair_weekly.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("ledger", "--ledger"),
            ("date", "--date"),
            ("out", "--out"),
            ("json_out", "--json"),
            ("record", "--record"),
            ("record_class", "--class"),
            ("target", "--target"),
            ("repair_outcome", "--repair-outcome"),
            ("ticket", "--ticket"),
            ("evidence_file", "--evidence-file"),
            ("reason", "--reason"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "ledger": {"type": "string", "description": "repair-outcome ledger JSONL path (default docs/repair-ledger.jsonl under the repo root; an explicit path must exist); CLI flag --ledger"},
                "date": {"type": "string", "description": "ISO date YYYY-MM-DD selecting the weekly window (required for the aggregate face); CLI flag --date"},
                "out": {"type": "string", "description": "write the weekly markdown face to this caller-named file; CLI flag --out"},
                "json_out": {"type": "string", "description": "write the weekly JSON face (schema rocqwash-repair-weekly/1) to this caller-named path; CLI flag --json"},
                "record": {"type": "boolean", "description": "plan one per-red outcome row: the would-append row is printed with zero writes (needs --class, --target, --repair-outcome); CLI flag --record"},
                "record_class": {"type": "string", "description": "repair class of the planned row (with --record); CLI flag --class"},
                "target": {"type": "string", "description": "target of the planned row (with --record); CLI flag --target"},
                "repair_outcome": {"type": "string", "description": "outcome token of the planned row (with --record); CLI flag --repair-outcome"},
                "ticket": {"type": "string", "description": "optional ticket key of the planned row; CLI flag --ticket"},
                "evidence_file": {"type": "string", "description": "optional evidence path of the planned row; CLI flag --evidence-file"},
                "reason": {"type": "string", "description": "optional reason text of the planned row; CLI flag --reason"},
                "selftest": {"type": "boolean", "description": "run the selftest vectors on temporary fixtures (takes no other flag); CLI flag --selftest"},
            }
        ),
        "description": (
            "Weekly distribution face over the repair-outcome ledger "
            "(tools/repair_weekly.py, repair class E6): the aggregate face "
            "reads the ledger strictly read-only and casts the per-red "
            "outcome census under the E6 vocabulary plus the class and "
            "ticket distributions for the ISO week of --date (an absent "
            "default-path ledger is a zero-row report); --record plans one "
            "row and prints the would-append JSON with zero writes. Zero "
            "network face. The --apply append face is not exposed over "
            "MCP (the ledger-append face stays CLI-side); outputs are "
            "stdout and the caller-named --out/--json paths."
        ),
    },
    {
        "name": "roster_resync",
        "kind": "cli",
        "cli": os.path.join("tools", "roster_resync.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("ledger", "--ledger"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "audited repository root (default: the parent of tools/); CLI flag --repo"},
                "ledger": {"type": "string", "description": "repair ledger path (default docs/repair-ledger.jsonl under the repo root; untouched on this face); CLI flag --ledger"},
                "json_out": {"type": "string", "description": "write the drift plan report (schema rocqwash-roster-resync/1, sort_keys determinism) to this caller-named path; CLI flag --json"},
            }
        ),
        "description": (
            "Roster count drift guard recount face (tools/roster_resync.py, "
            "E2 repair class 2): recounts the suite roster (the CASES "
            "block of tests/run_tests.sh, the only count authority) "
            "against the doc_lint count lines of tests/README.md and "
            "README.md and reports the drift plan; dry-run by construction "
            "on this face, the roster file bytes never change, and every "
            "outcome is loud (a red is data, exit 1 on drift found). Zero "
            "network face. The --apply rewrite face is not exposed over "
            "MCP (the README count-line rewrite is an authorization face "
            "owned by another lane); the pre-argparse --selftest route is "
            "not exposed (the registered chain_graph precedent); the plan "
            "report goes to stdout and the caller-named --json path."
        ),
    },
    {
        "name": "scheduler_lite",
        "kind": "cli",
        "cli": os.path.join("tools", "scheduler_lite.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("gap_ledger", "--gap-ledger"),
            ("reports", "--reports"),
            ("rounds", "--rounds"),
            ("autonomy", "--autonomy"),
            ("state", "--state"),
            ("ef_marker", "--ef-marker"),
            ("threshold", "--threshold"),
            ("interval_seconds", "--interval-seconds"),
            ("now_utc", "--now-utc"),
            ("out", "--out"),
            ("json", "--json"),
        ),
        "schema": _object_schema(
            {
                "gap_ledger": {"type": "array", "description": "gap feed ledger JSONL paths, repeatable (default docs/gap-feed-ledger.jsonl under the repo root); CLI flag --gap-ledger"},
                "reports": {"type": "array", "description": "vacgen report files or directories, repeatable (default docs/vacgen-reports); CLI flag --reports"},
                "rounds": {"type": "string", "description": "round ledger path (default docs/round-ledger.jsonl under the repo root); CLI flag --rounds"},
                "autonomy": {"type": "string", "description": "autonomy table path (default autonomy.json); CLI flag --autonomy"},
                "state": {"type": "string", "description": "round state path (default docs/round-state.json); CLI flag --state"},
                "ef_marker": {"type": "string", "description": "EF all-green marker path (the marker gate is reported, never fired); CLI flag --ef-marker"},
                "threshold": {"type": "integer", "description": "TODO-SEAT threshold (default from the measured constant); CLI flag --threshold"},
                "interval_seconds": {"type": "integer", "description": "round interval seconds (default: the measured backfill 40566); CLI flag --interval-seconds"},
                "now_utc": {"type": "string", "description": "plan clock override ISO8601Z so equal inputs stay byte-identical; CLI flag --now-utc"},
                "out": {"type": "string", "description": "write the plan document (schema rocqwash.scheduler-lite.plan/1) to this caller-named file; CLI flag --out"},
                "json": {"type": "boolean", "description": "print the plan document on stdout; CLI flag --json"},
            }
        ),
        "description": (
            "TODO-SEAT threshold trigger plan face for the jargon tier-B "
            "auto gear (tools/scheduler_lite.py): watches the gap account "
            "and the round cadence and decides whether a jargon-class "
            "auto round is due; the verdict quiet | due | blocked with "
            "reason tokens is data, absent defaults are data, and corrupt "
            "explicit input exits 9. The positional command takes only "
            "plan and defaults to it, so the face is plan-only by "
            "construction (the command itself is not exposed); ignition "
            "stays behind the EF all-green marker gate and no ignition "
            "face exists. Zero network face; the only write is the "
            "caller-named --out plan file; the pre-argparse --selftest "
            "route is not exposed (the registered chain_graph precedent)."
        ),
    },
    {
        "name": "axiom_guard",
        "kind": "cli",
        "cli": os.path.join("tools", "axiom_guard.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("repo", "--repo"),
            ("out", "--out"),
            ("allow_axiom", "--allow-axiom"),
            ("timeout", "--timeout"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "repo": {"type": "string", "description": "repository root to guard (tool-required for the guard face; --selftest runs without it); CLI flag --repo"},
                "out": {"type": "string", "description": "report directory (axiom-guard-report.json written under it; sorted inputs, byte-identical double run); CLI flag --out"},
                "allow_axiom": {"type": "array", "description": "axiom names admitted by the whitelist, repeatable (default empty); CLI flag --allow-axiom"},
                "timeout": {"type": "integer", "description": "per-file compile timeout seconds (default 600); CLI flag --timeout"},
                "selftest": {"type": "boolean", "description": "run the offline selftest vectors (takes no repo); CLI flag --selftest"},
            }
        ),
        "description": (
            "Repo-wide axiom guard read face (tools/axiom_guard.py): "
            "compiles every .v file under --repo in a private temp "
            "workdir (the repository tree gains zero bytes) and judges "
            "compile-ok files at two levels, the per-theorem Print "
            "Assumptions light face and the coqchk -o heavy face as the "
            "authority; the report JSON goes to the caller-named --out "
            "directory. Zero network face (local rocq/coqchk subprocesses "
            "only). The ROCWASH_ROCQ / ROCWASH_COQCHK environment "
            "variables are the registered toolchain form: with neither "
            "configured the tool exits 111 as an honest skip judging "
            "nothing rather than simulating; the --rocq and --coqchk "
            "binary-path flags and the temp-retention --keep flag are not "
            "exposed over MCP (the binary faces stay CLI-side)."
        ),
    },
    {
        "name": "symbiosis_bus_export",
        "kind": "cli",
        "cli": os.path.join("tools", "symbiosis_bus.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("command", "@command"),
            ("out", "--out"),
            ("swap", "--swap"),
            ("ledger", "--ledger"),
            ("source_repo", "--source-repo"),
            ("anchor", "--anchor"),
            ("side_a", "--a"),
            ("side_b", "--b"),
            ("dry_run", "--dry-run"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "command": {"type": "string", "enum": ["export", "status", "diff"], "description": "bus face: export renders the local ledger as an offline swap package, status counts both directions from entry content, diff lists the entry-id difference of two ledgers (import is not part of this face); CLI positional"},
                "out": {"type": "string", "description": "export: swap file to write, schema rocqwash-symbio/1 (required for a real export; a --dry-run export writes nothing); CLI flag --out"},
                "swap": {"type": "array", "description": "status: swap file paths to count, repeatable; CLI flag --swap"},
                "ledger": {"type": "string", "description": "ledger path override (default docs/exp-ledger.jsonl under the repo root); CLI flag --ledger"},
                "source_repo": {"type": "string", "description": "export: source repository name (default: this checkout's directory name); CLI flag --source-repo"},
                "anchor": {"type": "string", "description": "export: source HEAD anchor (default: the commit read from .git); CLI flag --anchor"},
                "side_a": {"type": "string", "description": "diff: first ledger path; CLI flag --a"},
                "side_b": {"type": "string", "description": "diff: second ledger path; CLI flag --b"},
                "dry_run": {"type": "boolean", "description": "export: validate and report, write nothing; CLI flag --dry-run"},
                "selftest": {"type": "boolean", "description": "run the temporary-fixture vector group (takes no command); CLI flag --selftest"},
            }
        ),
        "description": (
            "Cross-repository experience bus read/plan faces "
            "(tools/symbiosis_bus.py): export renders the local ledger as "
            "an offline swap package to the caller-named --out "
            "(timestamps ride entry content, never a clock), status "
            "counts bus rows from entry content, and diff lists the "
            "entry-id difference of two ledgers. Zero network face by "
            "design (exchange walks offline files). The import face (the "
            "exp_port append leg) is not part of this face and is not "
            "exposed over MCP (the ledger-append face stays CLI-side)."
        ),
    },
    {
        "name": "uplink_verify",
        "kind": "cli",
        "cli": os.path.join("tools", "uplink.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("command", "@command"),
            ("package", "--package"),
            ("digest", "--digest"),
            ("manifest", "--manifest"),
            ("register", "--register"),
            ("out", "--out"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "command": {"type": "string", "enum": ["verify", "pr-prep"], "description": "gate face: verify checks one return package against its declared md5 face, pr-prep renders the pull-request description draft of one register row (intake is not part of this face; --selftest takes no command); CLI positional"},
                "package": {"type": "string", "description": "return package zip path; CLI flag --package"},
                "digest": {"type": "string", "description": "verify: md5 digest, a 32-hex string or a sidecar file path (verify needs --digest or --manifest); CLI flag --digest"},
                "manifest": {"type": "string", "description": "verify: md5sum-line manifest path (verify needs --digest or --manifest); CLI flag --manifest"},
                "register": {"type": "string", "description": "pr-prep: register file to read the row from (default docs/uplink-intake.jsonl; verified rows only); CLI flag --register"},
                "out": {"type": "string", "description": "pr-prep: draft markdown path to write (required for pr-prep; zero git calls, never opens a pull request); CLI flag --out"},
                "selftest": {"type": "boolean", "description": "run the 19 frozen vectors on temporary fixtures (takes no command); CLI flag --selftest"},
            }
        ),
        "description": (
            "Standard intake gate verify and draft faces (tools/uplink.py): "
            "verify compares the package zip against its md5 sidecar or "
            "manifest member by member and prints the per-file evidence "
            "list to stdout (any mismatch or missing declared member is "
            "fail-loud rc=1); pr-prep renders the pull-request "
            "description draft of one verified register row to the "
            "caller-named --out (zero git calls, deterministic "
            "byte-identical output). Zero network face by design. The "
            "intake face (the register-row append leg) is not part of "
            "this face and is not exposed over MCP (the ledger-append "
            "face stays CLI-side)."
        ),
    },
    {
        "name": "i18n_translate_handoff",
        "kind": "cli",
        "cli": os.path.join("tools", "i18n_translate.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("segments", "--segments"),
            ("direction", "--direction"),
            ("emit", "--emit"),
            ("ingest", "--ingest"),
            ("prompts", "--prompts"),
            ("policy_ref", "--policy-ref"),
            ("translated_out", "--translated-out"),
            ("ledger_out", "--ledger-out"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "segments": {"type": "string", "description": "segments JSON file (array, or object with a segments key; required for the handoff faces); CLI flag --segments"},
                "direction": {"type": "string", "enum": ["zh2en", "en2zh"], "description": "translation direction (required for the handoff faces); CLI flag --direction"},
                "emit": {"type": "string", "description": "write the handoff packet as JSONL to this caller-named path (zero network); CLI flag --emit"},
                "ingest": {"type": "string", "description": "validate a backfill JSONL file at this path (zero network; a missing model_id or missing annotation is a violation and the ingest refuses fail-loud); CLI flag --ingest"},
                "prompts": {"type": "string", "description": "prompt template dir with <direction>*.txt/.md files (default: built-in constants); CLI flag --prompts"},
                "policy_ref": {"type": "string", "description": "P0 policy pre-check pointer stamped into ingest rows; CLI flag --policy-ref"},
                "translated_out": {"type": "string", "description": "write the translated segments JSON to this caller-named path; CLI flag --translated-out"},
                "ledger_out": {"type": "string", "description": "write the segment ledger rows JSONL to this caller-named path; CLI flag --ledger-out"},
                "json_out": {"type": "string", "description": "write a run report JSON to this caller-named path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the offline selftest and exit (takes no other action); CLI flag --selftest"},
            }
        ),
        "description": (
            "Model-site layer P2 handoff faces (tools/i18n_translate.py): "
            "--emit writes the segment handoff packet as JSONL and "
            "--ingest runs the ten-key backfill validation including "
            "policy_precheck_ref (a missing model_id or missing "
            "annotation is a violation and the ingest refuses fail-loud); "
            "both faces are zero-network. The provider argument never "
            "enters this schema, so the call form always carries the "
            "default handoff provider: the http provider leg (the "
            "ROCWASH_LLM_* environment gate and the NETRED ledger) is "
            "not registered (the same graduation law as the registered "
            "i18n_pipeline_dryrun face)."
        ),
    },
    {
        "name": "i18n_verify",
        "kind": "cli",
        "cli": os.path.join("tools", "i18n_verify.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("verify_target", "--verify-target"),
            ("emit_tenpoint", "--emit-tenpoint"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "verify_target": {"type": "string", "description": "run the P4 mechanical verification faces over this target (the local ai_flavor / norm_lint / doc_lint instruments at their standing paths, merged into the verification matrix JSON rocqwash.i18n.verify/1); CLI flag --verify-target"},
                "emit_tenpoint": {"type": "string", "description": "emit the P5 human ten-point review form for this target (a variant per target-face shape; the engine emits the form, it never produces a verdict); CLI flag --emit-tenpoint"},
                "json_out": {"type": "string", "description": "write the run report JSON to this caller-named path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the offline selftest and exit; CLI flag --selftest"},
            }
        ),
        "description": (
            "E4 P4/P5 verification faces (tools/i18n_verify.py): the P4 "
            "face runs the mechanical instruments over --verify-target in "
            "read-only probe runs and the P5 face emits the human "
            "ten-point review form for --emit-tenpoint. Zero network "
            "face. The --ingest-tenpoint face (the verdict write-back "
            "into the segment ledger) is not exposed over MCP, and the "
            "instrument-path override flags stay CLI-side (the standing "
            "sibling paths are the registered form)."
        ),
    },
    {
        "name": "red_dispatch_report",
        "kind": "cli",
        "cli": os.path.join("tools", "red_dispatch.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("event_file", "--event-file"),
            ("preset", "--preset"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "event_file": {"type": "string", "description": "sentinel red-event JSONL path (the stdin face is not part of this registration); CLI flag --event-file"},
                "preset": {"type": "string", "enum": ["report-only", "suggest"], "description": "route face: report-only routes with zero execution (default), suggest adds the copy blocks; the auto tier (which executes local commands) is not part of this face; CLI flag --preset"},
                "json_out": {"type": "string", "description": "write the route report JSON (rocqwash-red-route/1, sort_keys) to this caller-named path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "vector self-check on temporary fixtures, offline, zero network; CLI flag --selftest"},
            }
        ),
        "description": (
            "Red-event dispatcher report faces (tools/red_dispatch.py): "
            "routes an event file to preset actions under report-only "
            "(zero side effects) or suggest (plus copy blocks, still zero "
            "side effects); only the auto tier executes and dedups, and "
            "that tier is not part of this face (the preset choices are "
            "limited to the two zero-execution faces). Zero network face; "
            "the state-file, cooldown, repo-path, and parameter flags "
            "parameterize the auto tier and stay CLI-side."
        ),
    },
    {
        "name": "ai_flavor_apply_plan",
        "kind": "cli",
        "cli": os.path.join("tools", "ai_flavor_apply.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("file", "--file"),
            ("json_out", "--json"),
            ("emit_handoff", "--emit-handoff"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "string", "description": "target text file (read-only in plan and emit modes); CLI flag --file"},
                "json_out": {"type": "string", "description": "write the run report JSON to this caller-named path; CLI flag --json"},
                "emit_handoff": {"type": "string", "description": "emit the provider handoff package JSONL to this caller-named path (zero writes to the target); CLI flag --emit-handoff"},
                "selftest": {"type": "boolean", "description": "run the built-in vector suite on temporary fixtures (takes no other flag); CLI flag --selftest"},
            }
        ),
        "description": (
            "Advisory rewrite planner and handoff emitter "
            "(tools/ai_flavor_apply.py): the plan face scans the target "
            "read-only and casts the zh ban faces, stem faces, and "
            "sentence faces into suggestions (the 10 zh ban faces are "
            "never machine-written, disposition=human), and "
            "--emit-handoff writes the segment package for the human "
            "backfill loop. Zero network face. The --apply-handoff apply "
            "form and the http provider (the rewrite path and the "
            "default-deny direct-apply path, with the budget-cap state "
            "face) are not exposed over MCP; they stay CLI-side."
        ),
    },
    {
        "name": "row_render_check",
        "kind": "cli",
        "cli": os.path.join("tools", "row_render.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("gaps", "--gaps"),
            ("emit", "--emit"),
            ("check_draft", "--check-draft"),
            ("vacgen", "--vacgen"),
            ("prompts", "--prompts"),
            ("policy_ref", "--policy-ref"),
            ("ledger_out", "--ledger-out"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "gaps": {"type": "string", "description": "gap-cluster ledger JSON file (required for --emit); CLI flag --gaps"},
                "emit": {"type": "string", "description": "write the render packet as JSONL to this caller-named path (zero network); CLI flag --emit"},
                "check_draft": {"type": "string", "description": "re-run the vacgen admission gate over a draft JSON (the R6 re-acceptance face); CLI flag --check-draft"},
                "vacgen": {"type": "string", "description": "admission host path (default: the ROW_RENDER_VACGEN env var, then the sibling tools/vacgen.py); CLI flag --vacgen"},
                "prompts": {"type": "string", "description": "render prompt dir with render*.txt/.md files (default: built-in constant); CLI flag --prompts"},
                "policy_ref": {"type": "string", "description": "layer-law first-admission reference stamped into gaps; CLI flag --policy-ref"},
                "ledger_out": {"type": "string", "description": "write the nine-key render ledger rows JSONL to this caller-named path; CLI flag --ledger-out"},
                "json_out": {"type": "string", "description": "write a run report JSON to this caller-named path; CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the offline selftest and exit; CLI flag --selftest"},
            }
        ),
        "description": (
            "Refinery W2 row renderer emit and check faces "
            "(tools/row_render.py): --emit renders a gap-cluster ledger "
            "into a candidate-row render packet (zero network) and "
            "--check-draft re-runs the vacgen admission gate over a "
            "draft JSON. The ingest and tenpoint faces (the draft write "
            "and the verdict write-back into "
            "docs/drafts/taxonomy-candidates.json) and the http provider "
            "leg are not exposed over MCP; they stay CLI-side under the "
            "same graduation law as the i18n handoff faces."
        ),
    },
    # ---- the tree_audit registration increment: one read-only audit face
    # over the landed census CLI (tools/tree_audit.py --root/--json/
    # --selftest, its real argparse flag face).  Additive after the block
    # above: the existing specs and schemas untouched.
    {
        "name": "tree_audit",
        "kind": "cli",
        "cli": os.path.join("tools", "tree_audit.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("root", "--root"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "root": {"type": "string", "description": "directory to audit; every report field travels with its counting rule as {value, basis} and the root field records this directory as given; CLI flag --root"},
                "json_out": {"type": "string", "description": "additionally write the JSON report to this path (every top-level field as {value, basis} except scan_face, the top-level field that states what the scan covers and what it cannot see); CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the built-in fixture vectors on temporary directories and exit (takes no other flag); bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Read-only tree health audit over .lean and .v source trees "
            "(tools/tree_audit.py): one JSON report of file, byte, line and "
            "declaration totals plus an unsound-feature sweep (sorry, "
            "sorryAx, axiom, opaque, native_decide, unsafe, implemented_by, "
            "extern, ofReduceBool).  Every top-level report field except "
            "scan_face carries {value, basis} so each number travels with "
            "its counting rule, and the top-level scan_face field states "
            "what the scan covers and what it cannot see.  Zero network "
            "face; the tree is read-only and the only write is the "
            "caller-named --json path.  --selftest runs the fixture vectors "
            "offline on temporary directories (takes no other flag).  Exit "
         "codes: 0 green, 1 red (selftest, scan or report-write "
         "failures), 2 usage (missing or non-directory --root)."
        ),
    },
    # ---- the axiom_sweep registration increment: one read/plan face over
    # the landed per-theorem Lean axiom-closure classifier
    # (tools/lean_axiom_sweep.py --root/--json/--allow-axiom/--timeout/
    # --selftest/--snapshot/--baseline/--toolchain-doctor, its real
    # argparse flag face; the closure-snapshot increment adds the
    # snapshot/baseline mappings: the beyond-platform closure-evolution
    # audit, platform tools give today's closure, nobody gives closure
    # evolution; the toolchain-pin increment appends the toolchain_doctor
    # mapping, the standalone diagnostic face over the pin resolution
    # chain, exit 0 always).  Additive after
    # the block above: the existing specs and schemas untouched.
    {
        "name": "axiom_sweep",
        "kind": "cli",
        "cli": os.path.join("tools", "lean_axiom_sweep.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("root", "--root"),
            ("json_out", "--json"),
            ("allow_axiom", "--allow-axiom"),
            ("selftest", "--selftest"),
            ("timeout", "--timeout"),
            ("snapshot", "--snapshot"),
            ("baseline", "--baseline"),
            ("toolchain_doctor", "--toolchain-doctor"),
        ),
        "schema": _object_schema(
            {
                "root": {"type": "string", "description": "target .lean file or directory (tool-required for the sweep face; --selftest runs without it); CLI flag --root"},
                "json_out": {"type": "string", "description": "additionally write the single-line JSON report (schema rocqwash-axiom-sweep/1) to this path (every counter field as {value, basis} plus the top-level scan_face coverage statement); CLI flag --json"},
                "allow_axiom": {"type": "array", "description": "extra axiom names admitted into BENIGN-STANDARD, repeatable (sorryAx is never admitted); CLI flag --allow-axiom"},
                "selftest": {"type": "boolean", "description": "run the frozen offline vector group on canned fixtures and exit (takes no other flag); bare CLI flag --selftest"},
                "timeout": {"type": "integer", "description": "per-probe subprocess timeout seconds (default 600); CLI flag --timeout"},
                "snapshot": {"type": "string", "description": "additionally write a machine closure snapshot of the sweep to this path (schema rocqwash-axiom-closure-snapshot/1: per classified declaration the full probe name, the sorted axiom set and the class; deterministic - sorted, double-run byte-identical - so a later run can diff against it); the beyond-platform closure-evolution audit face: platform tools give today's closure, nobody gives closure evolution; CLI flag --snapshot"},
                "baseline": {"type": "string", "description": "diff the current closure against this previously written snapshot file (schema rocqwash-axiom-closure-snapshot/1) and emit the closure_diff block: per-declaration UNCHANGED / AXIOM-SET-CHANGED (from -> to listed) / NEW-THEOREM / LOST-THEOREM, a {value, basis} summary per verdict kind, and a top-level diff_alarm true when any NEW-DEPENDENCY (a previously-clean declaration gaining an axiom) or any AXIOM-SET-CHANGED exists; the diff reads only the two snapshots' data, no Lean toolchain involvement - the closure evolution audit face of this beyond-platform increment; CLI flag --baseline"},
                "toolchain_doctor": {"type": "boolean", "description": "print the standalone toolchain resolution-chain report (schema rocqwash-toolchain-doctor/1: lean/lake resolved paths and version tokens, the target lean-toolchain pin and its directory, the match verdict, the elan installed-list excerpt, and the exact one-line fix (elan toolchain install <pin>) when the pin is missing; every field {value, basis}) and exit 0 always - the diagnostic face, it judges nothing and touches nothing; requires --root, takes no other flag; bare CLI flag --toolchain-doctor"},
            }
        ),
        "description": (
            "Per-theorem axiom-closure classifier for Lean claim audits "
            "(tools/lean_axiom_sweep.py): enumerates the line-start "
            "theorem/lemma/def names of the target and probes each one by "
            "the copy-append form - a copy of the target file in a private "
            "temp directory with one `#print axioms <decl>` probe line per "
            "declaration appended (each probe line carries an exact-name "
            "marker comment and output alignment is derived from the "
            "emitted probe list, never positional counting) - so private "
            "declarations are probed in their own file's context, where "
            "they resolve; the import-based checker form survives only "
            "for cross-file aggregated sweeps where copy-append is not "
            "applicable. The checker runs via the target's own lake "
            "environment or a direct lean binary, and classification is "
            "per declaration: CLEAN, BENIGN-STANDARD (subset of propext / "
            "Classical.choice / Quot.sound, the wave-2 three-axioms "
            "adjudication), SORRY-ALARM (sorryAx, never whitelisted), "
            "CUSTOM-AXIOM-ALARM (any other name, verbatim), "
            "PRIVATE-COVERED (a private declaration successfully probed "
            "via the copy-append form; its axiom closure counts normally "
            "toward the verdict, not a pass-by-absence), UNPARSED "
            "(honest; a failed or unresolved probe maps only to its own "
            "declaration, no sibling cascade). Zero network "
            "face (local lean/lake subprocesses only); the audited tree is "
            "read-only and the only write is the caller-named --json path. "
            "Without a usable Lean toolchain (lean or lake on PATH passing "
            "a version probe) the tool exits 112 as an honest skip "
            "judging nothing rather than simulating; the --selftest face "
            "runs offline on canned fixtures regardless of toolchain. "
            "Closure-evolution audit face (beyond the platform: platform "
            "tools give today's closure, nobody gives closure evolution): "
            "--snapshot writes the deterministic machine closure snapshot "
            "(schema rocqwash-axiom-closure-snapshot/1, sorted, "
            "double-run byte-identical) and --baseline diffs the current "
            "closure against a previous snapshot into the closure_diff "
            "block (per-declaration UNCHANGED / AXIOM-SET-CHANGED with "
            "from -> to listed / NEW-THEOREM / LOST-THEOREM, a summary per "
            "verdict kind, top-level diff_alarm on any NEW-DEPENDENCY or "
            "AXIOM-SET-CHANGED); the diff reads only the two snapshots' "
            "data, so the snapshot and diff faces are "
            "toolchain-independent. Toolchain pin gate: when the target "
            "carries a lean-toolchain pin (nearest such file walking up "
            "from the root), the pin must be in the elan installed list "
            "(`elan toolchain list`) for the sweep to run at all; an "
            "installed pin is honored (LEAN_TOOLCHAIN=<pin> injected into "
            "every probe child environment over the cwd lean-toolchain "
            "lookup, so the pinned binaries, never the PATH default, "
            "answer) and the report's toolchain block carries the match "
            "conclusion as pin/target_pin/match; a missing or "
            "unverifiable pin is the honest rc 112 skip upgraded with a "
            "doctor block on stdout naming the exact fix (`elan "
            "toolchain install <pin>`), zero rows judged; no pin file "
            "keeps today's PATH-default behavior."
        ),
    },
    # ---- the claim_watch registration increment (ticket 13, the
    # rocqwash side): one net-gated live watch face over the landed
    # native resident watch CLI (tools/claim_watch.py --config/
    # --round-label/--ledger/--actor/--offline-selftest, its real
    # argparse flag face).  Additive after the block above: the existing
    # specs and schemas untouched.  Default deny: the live face is the
    # network face; the offline selftest face (--offline-selftest, zero
    # network) is the only face reachable without the env opt-in.
    {
        "name": "claim_watch",
        "kind": "cli",
        "cli": os.path.join("tools", "claim_watch.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("config", "--config"),
            ("round_label", "--round-label"),
            ("ledger", "--ledger"),
            ("actor", "--actor"),
            ("offline_selftest", "--offline-selftest"),
        ),
        "schema": _object_schema(
            {
                "config": {"type": "string", "description": "signal config file (schema rocqwash-claim-watch-config/1, the three frozen signal forms repo-path / status-endpoint / zulip-web-public; the seed seeds/claim-watch/signals-rh-ns.json carries the ticket 13 eight RH signals and three NS/Euler triggers); required for a live round, not for the selftest; CLI flag --config"},
                "round_label": {"type": "string", "description": "watch round label carried on every ledger row (default: the run's UTC minute stamp); CLI flag --round-label"},
                "ledger": {"type": "string", "description": "append-only round ledger JSONL (default docs/claim-watch-ledger.jsonl); one row per signal per round, every row carrying at_utc + actor + round_label; CLI flag --ledger"},
                "actor": {"type": "string", "description": "actor namespace carried on every ledger row (default claim_watch); CLI flag --actor"},
                "offline_selftest": {"type": "boolean", "description": "run the frozen canned vector group (zero network, canned transport + virtual clock) and exit; bare CLI flag --offline-selftest"},
            }
        ),
        "description": (
            "Native resident claim watch over a signal config "
            "(tools/claim_watch.py): one round fetches every signal's "
            "source once and appends one honest ledger row per signal "
            "(append-only JSONL).  Registration families: conclusion "
            "keyword hits (ok=false, the verbatim matching text quoted; "
            "forwarding to adjudication, no auto rescan, no auto "
            "disclosure), status-endpoint phase flips and heartbeat "
            "silence (heartbeat_at beyond the staleness threshold "
            "registers as target silent death, its own outcome class, "
            "never a false alarm), baseline and drift (a config hash_pin "
            "or the previous round's digest; a fetch failure never "
            "enters the drift branch), and honest non-verification "
            "(TLS/DNS/timeout registered unverifiable per net_probe's "
            "classification; a zulip 401 registers unverifiable "
            "honestly).  NETRED backoff (max-retries + schedule from "
            "the config) is built in.  Default deny: the live face is "
            "the network face and requires ROCQWASH_MCP_ALLOW_NET=1; "
            "the zero-network --offline-selftest face runs canned "
            "fixtures without the env opt-in."
        ),
    },
    # ---- the v2-B audit-line registration increment: three faces over
    # the landed audit-line CLIs (the fetch leg, the judge leg, the
    # release leg of the v2-B micro-bundle).  source_fetch and
    # release_chain are net-gated (their live faces are the network
    # faces); sweep_verdict is a zero-network judge.  Each spec is
    # transcribed from its tool's own frozen CLI contract header (the
    # axiom_sweep/claim_watch precedent; the INDEX entries await their
    # own lane), and each arg_map covers exactly the tool's real
    # argparse flag face: the three CLIs route --selftest before
    # argparse, so that route is not an argparse flag and stays out of
    # the arg_maps (the registered chain_graph precedent).  Additive
    # after the block above: the existing specs and schemas untouched.
    {
        "name": "source_fetch",
        "kind": "cli",
        "cli": os.path.join("tools", "source_fetch.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("url", "--url"),
            ("sha256", "--sha256"),
            ("sha256_source", "--sha256-source"),
            ("mirror", "--mirror"),
            ("trap_sniff", "--trap-sniff"),
            ("out", "--out"),
            ("timeout", "--timeout"),
            ("retries", "--retries"),
            ("backoff_base", "--backoff-base"),
        ),
        "schema": _object_schema(
            {
                "url": {"type": "string", "description": "primary fetch target (tool-required for the fetch face; the CLI usage-errors rc 2 without it); CLI flag --url"},
                "sha256": {"type": "string", "description": "expected sha256 from the caller, lowercase 64-hex, never a tool constant (mutually exclusive with sha256_source); CLI flag --sha256"},
                "sha256_source": {"type": "string", "description": "URL of the CI file carrying the expected sha256 as its single 64-hex token (the constant-fetched-from-CI-file-at-source pattern; mutually exclusive with sha256; two or more distinct tokens is source-ambiguous, none is source-digest-missing, both fail loud); CLI flag --sha256-source"},
                "mirror": {"type": "string", "description": "mirror fetch target; both byte streams must hash-equal (the dual-source cross-pin); CLI flag --mirror"},
                "trap_sniff": {"type": "boolean", "description": "sniff fetched bodies for HTML-trap responses (the any-path-returns-200 precedent: a hit registers TRAP-DETECTED and is never saved; a clean sniff is a negative finding, the sha256 pin is the binding evidence); bare CLI flag --trap-sniff"},
                "out": {"type": "string", "description": "directory the verified bytes are written to (created if missing; only fully verified bytes land, trap and mismatch bytes are registered and never reach disk); CLI flag --out"},
                "timeout": {"type": "number", "description": "per-attempt timeout seconds (default 180); CLI flag --timeout"},
                "retries": {"type": "integer", "description": "NETRED retry cap (default 3; 403/429/5xx and the transient dns/timeout faces retry, tls-blocked and 401/404 never retry); CLI flag --retries"},
                "backoff_base": {"type": "number", "description": "exponential backoff base seconds (default 2.0); CLI flag --backoff-base"},
            }
        ),
        "description": (
            "Pinned, dual-source, trap-sniffing audit fetch face "
            "(tools/source_fetch.py, schema rocqwash-source-fetch/1): "
            "fetches the --url artifact under NETRED retry/backoff, "
            "verifies sha256 where the expected digest comes from the "
            "caller (--sha256) or from a CI file fetched at "
            "--sha256-source (the constant-fetched-from-CI-file-at-source "
            "pattern, never hardcoded), cross-pins the optional --mirror "
            "(both streams must hash-equal), and sniffs HTML-trap "
            "responses under --trap-sniff (a hit registers TRAP-DETECTED "
            "and is never saved); only verified bytes reach --out. One "
            "JSON report line; every counter travels wrapped {value, "
            "basis} with the top-level scan_face coverage statement; a "
            "fetch with no pin lands fetched-unverified and says so "
            "honestly. Default deny: the live fetch face is the network "
            "face and requires ROCQWASH_MCP_ALLOW_NET=1 (the CLI answers "
            "its own honest rc 111 net-gated face without it). The CLI's "
            "frozen-vector --selftest route is pre-argparse and not "
            "exposed here (the registered chain_graph precedent); its "
            "INDEX entry awaits its own lane."
        ),
    },
    {
        "name": "sweep_verdict",
        "kind": "cli",
        "cli": os.path.join("tools", "sweep_verdict.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("lanes", "--lanes"),
            ("expected_red", "--expected-red"),
            ("out", "--out"),
        ),
        "schema": _object_schema(
            {
                "lanes": {"type": "string", "description": "directory of per-lane result .tsv files, one lane per file, idx|probe|status|note with an optional column-naming header (tool-required; a file path where the directory is required usage-errors rc 2, the shared append ledger anti-shape that caused the first audit sweep's failure is refused at the front door); CLI flag --lanes"},
                "expected_red": {"type": "string", "description": "expected by-design-fail rows (idx<TAB>probe lines): matched rows stay out of EXCEPTION (the baselinediff interlock, a baselined red is not failing), their absent rows are recorded MISSING, and stale entries are listed; CLI flag --expected-red"},
                "out": {"type": "string", "description": "additionally write the stdout JSON payload (schema rocqwash-sweep-verdict/1) to this caller-named path; CLI flag --out"},
            }
        ),
        "description": (
            "Mechanical verdict face over per-lane sweep ledgers "
            "(tools/sweep_verdict.py, schema rocqwash-sweep-verdict/1): "
            "unions every per-lane result .tsv inside the --lanes "
            "directory with dedup on (idx, probe), judges GREEN / "
            "EXCEPTION / MISSING with full listings (unexpected status "
            "tokens quoted verbatim; a conflict keeps the later lane in "
            "sorted order and lists the divergence loud), and interlocks "
            "the --expected-red file. One JSON report line; every "
            "counter travels wrapped {value, basis} with the top-level "
            "scan_face coverage statement; MISSING is declared "
            "not-computed as null without the file, never fabricated as "
            "zero. Zero network, zero compile, deterministic. The CLI's "
            "frozen-vector --selftest route is pre-argparse and not "
            "exposed here (the registered chain_graph precedent); its "
            "INDEX entry awaits its own lane."
        ),
    },
    {
        "name": "release_chain",
        "kind": "cli",
        "cli": os.path.join("tools", "release_chain.py"),
        "net_gated": True,
        "fixed_args": [],
        "arg_map": (
            ("issue", "--issue"),
            ("release_title", "--release-title"),
            ("assets", "--assets"),
            ("zenodo_metadata", "--zenodo-metadata"),
            ("confirm_publish", "--confirm-publish"),
            ("dry_run", "--dry-run"),
            ("repo", "--repo"),
            ("stage", "--stage"),
            ("release_id", "--release-id"),
            ("deposit_id", "--deposit-id"),
            ("timeout", "--timeout"),
        ),
        "schema": _object_schema(
            {
                "issue": {"type": "integer", "description": "the issue number the chain hangs off (tool-required; the CLI usage-errors rc 2 without it); CLI flag --issue"},
                "release_title": {"type": "string", "description": "the Release title (tool-required; also pins the deterministic tag slug); CLI flag --release-title"},
                "assets": {"type": "string", "description": "directory of release assets, flat and non-recursive, bytes and sha256 pinned at plan time and re-verified at upload (tool-required; missing dir fails loud rc 9); CLI flag --assets"},
                "zenodo_metadata": {"type": "string", "description": "Zenodo deposit metadata JSON file (a JSON object with a title key); without it the Zenodo layer is listed blocked honestly; CLI flag --zenodo-metadata"},
                "confirm_publish": {"type": "boolean", "description": "PUBLISH STOP-GATE KEY: warning, this is the key that leaves the dry-run plan and executes ONE gated stage against the live services (stage 4 publish is irreversible); without it the face stays at the default dry-run plan with zero network; requires the ROCQWASH_MCP_ALLOW_NET opt-in at this face and the stage credentials at the CLI; bare CLI flag --confirm-publish"},
                "dry_run": {"type": "boolean", "default": True, "description": "plan-only dry run, the default face of this capability (schema default true; a pure computation over local inputs, zero network, the plan is the deliverable, nothing is simulated); bare CLI flag --dry-run"},
                "repo": {"type": "string", "description": "the repository owner/name carrying the issue and Release (dry-run carries the {owner}/{repo} placeholder without it; execution resolves it from this flag or git remote origin and fails loud rc 9 rather than guess); CLI flag --repo"},
                "stage": {"type": "integer", "enum": [1, 2, 3, 4], "description": "which gated layer to execute with confirm_publish, one stage per invocation: 1 issue body update, 2 Release create plus per-asset uploads, 3 deposit create plus bucket PUTs, 4 publish (irreversible; additionally demands deposit_id, the mechanical stop-gate carry); without confirm_publish the plan always covers all layers; CLI flag --stage"},
                "release_id": {"type": "integer", "description": "a stage-2 minted Release id carried into a stage-1 finalize re-run (verbatim from its log); CLI flag --release-id"},
                "deposit_id": {"type": "string", "description": "the stage-3 minted deposit id; REQUIRED for stage 4 (the publish stop-gate carry: the irreversible publish cannot run without stage 3's minted handle); the CLI declares no int type, so it rides as a string; CLI flag --deposit-id"},
                "timeout": {"type": "number", "description": "per-call timeout seconds (default 120); CLI flag --timeout"},
            }
        ),
        "description": (
            "Release chain face, issue -> GitHub Release -> Zenodo, with "
            "separately gated publish steps (tools/release_chain.py, "
            "schema rocqwash-release-chain/1): emits the three-layer "
            "checklist with exact API calls (issue body update, Release "
            "create plus per-asset uploads, Zenodo deposit create plus "
            "bucket PUTs plus publish). Default face: dry-run (the "
            "schema carries dry_run default true), a pure computation "
            "over local inputs, zero network. Default deny: the live "
            "face is the network face and requires "
            "ROCQWASH_MCP_ALLOW_NET=1; actual steps additionally need "
            "confirm_publish, the publish stop-gate key, one stage per "
            "invocation, each layer stopping for verification before the "
            "next (publish stop-gates, never bundled), and stage 4 (the "
            "irreversible publish) also demands deposit_id, the "
            "mechanical stop-gate carry. Minted URLs/DOIs are read "
            "verbatim from responses, never assembled. One JSON report "
            "line; every counter travels wrapped {value, basis} with the "
            "top-level scan_face coverage statement. The CLI's "
            "frozen-vector --selftest route is pre-argparse and not "
            "exposed here (the registered chain_graph precedent); its "
            "INDEX entry awaits its own lane."
        ),
    },
    # ---- the numeric-probe registration increment: one exact-arithmetic
    # re-verification gate face over the landed claim-gate CLI
    # (tools/numeric_probe.py --claim/--out/--selftest, its real argparse
    # flag face), plus one statement-ingestion batch face over the landed
    # vacgen v2 batch flags (tools/vacgen.py --from-statements/
    # --from-repo, exactly those real argparse flags).  Both zero-network,
    # both ungated.  Additive after the block above: the existing specs
    # and schemas untouched.
    {
        "name": "numeric_probe",
        "kind": "cli",
        "cli": os.path.join("tools", "numeric_probe.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("claim", "--claim"),
            ("out", "--out"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "claim": {"type": "string", "description": "claim file: a JSON array of claim objects, each carrying id, kind, statement, the discriminating field left|interval|target, and source_anchor (tool-required for the probe face; --selftest runs without it); CLI flag --claim"},
                "out": {"type": "string", "description": "additionally write the JSON report to this caller-named path; CLI flag --out"},
                "selftest": {"type": "boolean", "description": "run the frozen 42-vector group in-process and exit (takes no other flag); bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Exact-arithmetic re-verification gate for claimed numerical "
            "verifications (tools/numeric_probe.py, schema "
            "rocqwash-numeric-probe/1): reads the caller-named --claim "
            "JSON array and mechanically re-verifies each claim with "
            "Fraction exact arithmetic, zero floats, zero subprocess, "
            "zero network.  kind rational-bound executes A < B / A <= B / "
            "A = B (entries as p/q strings or declared-precision decimals, "
            "a decimal carrying the band value +/- 10^-d/2 for its d "
            "written fraction digits, an explicit precision k overriding "
            "d, a bare integer an exact point); kind interval-containment "
            "executes x-band containment in [lo, hi]; kind "
            "transcendental-plan (zeta/theta/psi/ln targets) emits a "
            "bound-discipline verification plan and returns PLANNED, the "
            "honest plan-only face until a high-precision backend ticket "
            "lands, never a fabricated numeric verdict; any claim whose "
            "numbers fail to parse lands an honest UNPARSED row.  One "
            "JSON report line: per-claim verdicts (PASS / FAIL / PLANNED "
            "/ UNPARSED) with the exact executed comparison recorded in "
            "each row basis, counts wrapped {value, basis}, and the "
            "top-level scan_face coverage statement.  rc 0 iff no FAIL "
            "and no UNPARSED row; rc 1 names every red row id on stderr "
            "(fail loud); rc 2 usage.  --selftest runs the frozen "
            "42-vector group offline in-process (takes no other flag)."
        ),
    },
    {
        "name": "statement_probes",
        "kind": "cli",
        "cli": os.path.join("tools", "vacgen.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("from_statements", "--from-statements"),
            ("from_repo", "--from-repo"),
        ),
        "schema": _object_schema(
            {
                "from_statements": {"type": "string", "description": "statement-block file: theorem statements in the audited repo's own syntax, one per block, blank-line separated, text exactly as the repo states it (tool-required on this face unless from_repo is given; the two faces are mutually exclusive); CLI flag --from-statements"},
                "from_repo": {"type": "string", "description": "audited repo root: enumerate line-start theorem/lemma declarations in *.lean files (the lean_axiom_sweep enumeration face; .git skipped) and cast each as --from-statements does (tool-required on this face unless from_statements is given; the two faces are mutually exclusive); CLI flag --from-repo"},
            }
        ),
        "description": (
            "Statement-ingestion batch faces over the landed casting CLI "
            "tools/vacgen.py (the v2 batch face, zero-compile, zero "
            "network): --from-statements FILE casts statement blocks "
            "(blank-line separated, the audited repo's own syntax) through "
            "the untouched single-challenge machinery into <out>/casts/"
            "<id>/ with a per-statement JSON at <out>/reports/<id>.json, "
            "the exact block text under <out>/sources/, and <out>/summary."
            "json (schema vacgen-batch-summary/1); --from-repo DIR "
            "enumerates line-start theorem/lemma declarations in *.lean "
            "files (the lean_axiom_sweep enumeration face, .git skipped, "
            "comment bodies not masked) and casts each the same way.  The "
            "two flags are mutually exclusive and either one is "
            "tool-required (calling neither lands the v1 single-challenge "
            "face, which usage-errors rc 1 without --in).  arg_map covers "
            "exactly these two real flags; the batch output root is the "
            "CLI default vacgen_batch_out under the repository root (the "
            "--out redirect is not exposed here; caller duty rides with "
            "the underlying CLI).  Per-statement failures are counted, "
            "never raised: an unparseable statement is an honest UNPARSED "
            "row with the parse reason carried verbatim, never a silent "
            "skip; rc 0 batch complete, rc 1 batch-level fail-loud.  Zero "
            "network, zero compile: the cast writes skeletons, sources, "
            "reports and summary only; the build command line is recorded "
            "as text, never executed."
        ),
    },
    # ---- the vacgen-coq registration increment (ticket 14 work stream 1, the
    # Rocq domain support): one zero-network batch coverage face over the
    # landed Coq-side sibling CLI (tools/vacgen_coq.py --from-v/
    # --taxonomy/--out/--limit/--selftest, exactly the tool's real
    # argparse flag face).  Additive after the block above: the existing
    # specs and schemas untouched.  Dual-domain coverage law: the Lean
    # vacgen_generate face stays for the Lean domain, this face covers the
    # Rocq domain; the sibling CLIs share no code path (architecture and
    # report discipline only).
    {
        "name": "vacgen_coq_generate",
        "kind": "cli",
        "cli": os.path.join("tools", "vacgen_coq.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("from_v", "--from-v"),
            ("taxonomy", "--taxonomy"),
            ("out", "--out"),
            ("limit", "--limit"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "from_v": {"type": "string", "description": "batch input: a .v file, or a directory whose *.v files are walked recursively (.git skipped); tool-required for the batch face; --selftest runs without it; CLI flag --from-v"},
                "taxonomy": {"type": "string", "description": "taxonomy table path (chain: this flag, then the VACGEN_COQ_TAXONOMY environment variable, then the tool-adjacent taxonomy-coq.json, then the builtin starter row); CLI flag --taxonomy"},
                "out": {"type": "string", "description": "batch output root (default: vacgen_coq_batch_out under the repository root); the only disk face the batch face writes, one JSON per statement plus summary.json under it; CLI flag --out"},
                "limit": {"type": "integer", "description": "cap the number of statements processed after enumeration (must be a positive integer, usage error rc 2 otherwise; counted in summary.input.limitApplied); CLI flag --limit"},
                "selftest": {"type": "boolean", "description": "run the in-process offline vector face and exit (takes no other flag): taxonomy-load vector, recognition vectors over the fixture known families, unknown-shape todo_seat vector, hole-face degradation vector, builtin chain-end vector, L1 extraction/split vector, L3 computation vector, batch end-to-end vector inside a TemporaryDirectory; bare CLI flag --selftest"},
            }
        ),
        "description": (
            "Rocq statement-face coverage prober over the landed Coq-side "
            "sibling CLI (tools/vacgen_coq.py, ticket 14 wave 1, the Rocq "
            "domain support; the Lean vacgen_generate face stays for the "
            "Lean domain - dual-domain coverage, the sibling CLIs share no "
            "code path).  The batch face enumerates line-start Rocq "
            "assertion statements in the --from-v .v file or *.v directory "
            "walk (.git skipped), splits each statement into premise and "
            "conclusion faces, classifies every face against the data-driven "
            "taxonomy table (zero family knowledge in-engine), and reports "
            "the Coq-L3 coverage per statement and per batch, with honest "
            "TODO-SEAT degradation for unknown shapes (counted, never "
            "silent): one JSON per statement plus summary.json under --out "
            "(default vacgen_coq_batch_out).  --selftest runs the offline "
            "in-process vector face.  Zero network face, zero compile: no "
            "Rocq process is ever started, the only write root is the "
            "caller-named --out directory."
        ),
    },
    # R2-122 formal-audit trust-face registration increment of four:
    # attest_join, frozen8, verify_vo, gate4_comment_guard.  These faces
    # wire existing differentiated CLI tools (tools/attest_join.py,
    # certify/frozen8.py, verify/verify_vo.py,
    # verify/gate4_comment_guard.py) - zero new tool code, pure MCP-face
    # registration.  Danger gates are baked into the exposure lists
    # themselves: every write-bearing or network-capable flag of frozen8
    # (freeze --out/--tier2, check --json/--attest/--gpg-sig/--tsr, the
    # timestamp subcommand with its freetsa.org TSA leg) is unreachable
    # through the face because no subcommand token or such flag can be
    # formed from the arg_map; gate4_comment_guard's ledger-emit write
    # faces (--emit-ledger/--ledger-tsv, the latter with a script-dir
    # default) stay CLI-side; verify_vo's nargs=2 --require-fresh flag is
    # mechanically unexposable through the repeat-per-item argv builder
    # and stays CLI-side with its constituent judgments already carried
    # by the four-piece face.
    {
        "name": "attest_join",
        "kind": "cli",
        "cli": os.path.join("tools", "attest_join.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("attest", "--attest"),
            ("report", "--report"),
            ("out", "--out"),
            ("basename_fallback", "--basename-fallback"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "attest": {"type": "string", "description": "cw.attest/v1 module archive JSON (read-only input); the run face requires all three of attest/report/out (usage error rc 2 otherwise); CLI flag --attest"},
                "report": {"type": "string", "description": "rocqwash.b-axiom-audit/1 audit report JSON (read-only input); required for the run face; CLI flag --report"},
                "out": {"type": "string", "description": "join table JSON output path (the only disk face this tool writes; written atomically via tmp + rename, sorted keys, byte-identical reruns); required for the run face; CLI flag --out"},
                "basename_fallback": {"type": "boolean", "description": "join on basename + .v for misaligned roots; ambiguous basenames fail loud rc 2 with the ambiguity enumeration (never merged silently); CLI flag --basename-fallback"},
                "selftest": {"type": "boolean", "description": "run the frozen offline vector group (29 vectors) and exit; standalone law: --selftest rejects any run flag with usage error rc 2, and the run face rejects a missing input flag rc 2; CLI flag --selftest"},
            }
        ),
        "description": (
            "Side-by-side join table of the cw.attest/v1 module archive "
            "and the rocqwash.b-axiom-audit/1 audit report "
            "(tools/attest_join.py).  Juxtaposition, never an equality "
            "check: rows are placed side by side for human audit, no "
            "merge verdict is emitted.  Exit contract: 0 joined / 2 "
            "usage or structural ambiguity or invalid audit / 3 archive "
            "trouble degrades to the empty table (rc 3 never weakens the "
            "audit, it only reports the archive side unreadable).  Zero "
            "network face (the frozen-vector selftest self-spawns the "
            "script itself with -I -B, nothing else); the only disk "
            "write is the caller-named --out path.  --selftest runs the "
            "29-vector offline frozen vector group."
        ),
    },
    {
        "name": "frozen8",
        "kind": "cli",
        "cli": os.path.join("certify", "frozen8.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("selftest", "--selftest"),
            ("ledger", "--ledger"),
        ),
        "schema": _object_schema(
            {
                "selftest": {"type": "boolean", "description": "nine-judgment self-proof on offline scratch trees (checked before --ledger when both are passed); CLI flag --selftest"},
                "ledger": {"type": "boolean", "description": "print the ten-entry roster as md5 + relpath rows (LEDGER8 eight + CHECKERS two) and exit 0; a file missing in-roster fails loud rc 9; CLI flag --ledger"},
            }
        ),
        "description": (
            "Frozen-roster certification tool face "
            "(certify/frozen8.py) carrying ONLY its two read-only "
            "top-level faces: --selftest (nine offline judgments over "
            "temporary scratch trees) and --ledger (stdout print of the "
            "ten-entry md5 roster).  This is an exposure-list gate: the "
            "write faces (freeze --out manifest and --tier2 side "
            "roster, check --json reconciliation) and every "
            "network-capable leg (the timestamp subcommand with its "
            "freetsa.org RFC 3161 TSA request, check --attest shelling "
            "to gh, check --gpg-sig shelling to gpg) are NOT reachable "
            "through this face - no subcommand token or such flag can "
            "be formed from the exposed argument set - so the face is "
            "zero-network by construction with no environment gate "
            "needed; those rings (manifest, side roster, disk, git "
            "anchor, gpg, gh attestation, RFC 3161) stay CLI-side.  "
            "With neither flag the child prints usage to stderr and "
            "exits 2 (honest usage error).  The tool's own NETRED "
            "whitelist for its timestamp face covers the CLI lane, not "
            "this MCP face."
        ),
    },
    {
        "name": "verify_vo",
        "kind": "cli",
        "cli": os.path.join("verify", "verify_vo.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("v", "--v"),
            ("vo", "--vo"),
            ("rc", "--rc"),
            ("exit_file", "--exit-file"),
            ("log", "--log"),
            ("magic", "--magic"),
            ("json_out", "--json"),
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "v": {"type": "string", "description": "source .v path (read-only input); required together with vo (usage error rc 2 otherwise; --selftest runs without them); CLI flag --v"},
                "vo": {"type": "string", "description": "compiled .vo path (read-only input); required together with v; CLI flag --vo"},
                "rc": {"type": "integer", "description": "compile exit code (mutually exclusive with exit_file, rc 2 if both passed); CLI flag --rc"},
                "exit_file": {"type": "string", "description": "file whose first line holds the compile exit code (mutually exclusive with rc, rc 2 if both passed); CLI flag --exit-file"},
                "log": {"type": "string", "description": "compile log path (read-only; judged for zero Error lines); CLI flag --log"},
                "magic": {"type": "string", "description": "expected .vo magic bytes in hex (default 436f712100015ff4, the frozen Rocq 9.1 header); CLI flag --magic"},
                "json_out": {"type": "string", "description": "per-piece ledger JSON output path (the only disk face this tool writes, caller-named); CLI flag --json"},
                "selftest": {"type": "boolean", "description": "run the embedded frozen vector group (thirteen judgments) and exit; standalone, checked first; CLI flag --selftest"},
            }
        ),
        "description": (
            "Four-piece green-verdict machine check over a .v/.vo pair "
            "(verify/verify_vo.py): compile exit code (from --rc or "
            "--exit-file), compile log with zero Error lines, .vo "
            "leading 8-byte magic equal to the frozen Rocq 9.1 header, "
            "and .vo mtime strictly fresher than .v.  Exit contract: 0 "
            "PASS / 1 FAIL / 2 usage / 9 missing path or fresh-compile "
            "reject (rc 9 is fail-loud and never merged into ordinary "
            "FAIL).  Zero network, zero subprocess face; probed files "
            "are never written; the only write is the caller-named "
            "--json ledger.  Withheld from this face and CLI-side: "
            "--require-fresh (an nargs=2 flag the repeat-per-item argv "
            "mechanics cannot express; its two constituent judgments - "
            "magic and mtime freshness - are already carried by the "
            "four-piece face).  --selftest runs the thirteen-judgment "
            "embedded vector group."
        ),
    },
    {
        "name": "gate4_comment_guard",
        "kind": "cli",
        "cli": os.path.join("verify", "gate4_comment_guard.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("file", "--file"),
            ("tree", "--tree"),
            ("tree_recursive", "--tree-recursive"),
            ("baseline", "--baseline"),
            ("length_cap", "--length-cap"),
            ("length_fail", "--length-fail"),
            ("no_principle", "--no-principle"),
            ("json_out", "--json"),
        ),
        "schema": _object_schema(
            {
                "file": {"type": "array", "description": "single-file scan targets, repeatable (flag repeated per item); at least one of file/tree/tree_recursive is required (usage error rc 2 otherwise); CLI flag --file"},
                "tree": {"type": "array", "description": "flat directory scan targets (non-recursive), repeatable; CLI flag --tree"},
                "tree_recursive": {"type": "array", "description": "deep directory scan targets (recursive, the v2.1 blind-spot upgrade), repeatable; CLI flag --tree-recursive"},
                "baseline": {"type": "string", "description": "survey-result JSON to compare against (baseline compare mode, read-only); CLI flag --baseline"},
                "length_cap": {"type": "integer", "description": "header comment line-count cap (default 30); over-cap items are review-level unless length_fail is set; CLI flag --length-cap"},
                "length_fail": {"type": "boolean", "description": "promote over-cap findings to hard FAIL (default keeps them review-level, never hard-red); CLI flag --length-fail"},
                "no_principle": {"type": "boolean", "description": "skip the principle-sentence presence judgment; CLI flag --no-principle"},
                "json_out": {"type": "string", "description": "scan report JSON output path (caller-named, the only disk face this face writes); CLI flag --json"},
            }
        ),
        "description": (
            "Five-field header guard and comment-hygiene scanner "
            "(verify/gate4_comment_guard.py v2.1 EXT) over caller-named "
            "files, flat trees, or recursive trees (three domains), "
            "with optional baseline compare mode.  Exit contract: 0 "
            "clean / 1 any FAIL / 2 REVIEW or UNREADABLE or usage - "
            "review items are never hard-red unless --length-fail is "
            "passed.  Zero network, zero subprocess face; scanning is "
            "read-only (one open per file for the header parse); the "
            "only write is the caller-named --json report.  Withheld "
            "from this face and CLI-side (write-bearing): --emit-ledger "
            "(writes the exemption-ledger JSON) and --ledger-tsv (a "
            "write face whose default lands beside the tool itself).  "
            "No --selftest flag exists in the CLI (usage-proven); the "
            "verification face of record is the scan itself on "
            "caller-named inputs."
        ),
    },
    {
        "name": "anchor_guard",
        "kind": "cli",
        "cli": os.path.join("tools", "anchor_guard.py"),
        "net_gated": False,
        "fixed_args": [],
        "arg_map": (
            ("selftest", "--selftest"),
        ),
        "schema": _object_schema(
            {
                "selftest": {"type": "boolean", "description": "run the embedded two-tier vector suite and exit (tier a pure Python always; the toolchain tier only when BOTH ROCWASH_ROCQ and ROCWASH_COQCHK are present in the child environment, unconfigured = honest skip exit 111 with the SKIP line); takes no other flag (combined flags are refused exit 2 by the tool before argparse); CLI flag --selftest"},
            }
        ),
        "description": (
            "Anchor and certificate guard face (tools/anchor_guard.py) "
            "carrying ONLY its one read-only standalone top-level face: "
            "--selftest, the embedded vector suite on private temporary "
            "fixtures (tier a pure-Python vectors, tier b the guarded "
            "pipeline double-run; exits 0 all pass / 2 assertion failure "
            "/ 111 toolchain tier not configured / 9 configured binary "
            "missing).  This is an exposure-list gate: the guard run "
            "itself (--repo, --manifest) and with it the --out report "
            "write, the private temporary workdir with its --keep "
            "retention face, and every rocq/coqchk toolchain leg are NOT "
            "reachable through this face - no such argument token can be "
            "formed from the exposed argument set - so judging stays "
            "CLI-side (wrapped in tools/cpu_guard.sh there); the CLI has "
            "no standalone census/plan/report-render flags (the census "
            "rules and the stdout summary are internal faces of the "
            "run).  Zero network by construction (import scan zero hits, "
            "stdlib only; binaries resolve from flags or environment, "
            "never downloaded, never simulated); the selftest writes "
            "only its own private temporary directory and removes it.  "
            "If the operator exports both ROCWASH_ROCQ and ROCWASH_COQCHK "
            "into the server environment the selftest's embedded "
            "toolchain tier engages (still zero network, still "
            "private-temporary only).  Combined with any other flag the "
            "tool exits 2 before argparse (honest usage)."
        ),
    },
]

TOOLS_BY_NAME = {spec["name"]: spec for spec in TOOL_SPECS}

_TYPE_CHECKS = {
    "string": lambda value: isinstance(value, str),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "array": lambda value: isinstance(value, list)
    and all(isinstance(item, str) for item in value),
}


def _log(message):
    """Diagnostics go to stderr; stdout carries protocol lines only."""
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def _emit(payload):
    """Write one compact JSON-RPC line in UTF-8 and flush."""
    data = json.dumps(payload, ensure_ascii=False)
    sys.stdout.buffer.write((data + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _tool_result(msg_id, text, is_error):
    return _result(
        msg_id,
        {"content": [{"type": "text", "text": text}], "isError": bool(is_error)},
    )


def _deny_text(name):
    return (
        "denied by default security face: capability '{0}' drives network or heavy "
        "tooling and is disabled unless the environment variable {1}=1 is set. "
        "See docs/mcp.md section 5 for the security face."
    ).format(name, ALLOW_NET_ENV)


def _timeout_s():
    raw = os.environ.get(TIMEOUT_ENV, "")
    if not raw:
        return DEFAULT_TIMEOUT_S
    try:
        value = int(raw)
    except ValueError:
        _log("invalid {0}={1!r}; using default {2}s".format(TIMEOUT_ENV, raw, DEFAULT_TIMEOUT_S))
        return DEFAULT_TIMEOUT_S
    return value if value > 0 else DEFAULT_TIMEOUT_S


def _validate_arguments(spec, arguments):
    if not isinstance(arguments, dict):
        raise InvalidParams("Invalid params: arguments must be an object")
    properties = spec["schema"]["properties"]
    for key, value in arguments.items():
        if key not in properties:
            raise InvalidParams("Invalid params: unknown argument '{0}'".format(key))
        expected = properties[key]["type"]
        if not _TYPE_CHECKS[expected](value):
            raise InvalidParams(
                "Invalid params: argument '{0}' must be of type {1}".format(key, expected)
            )
        if expected == "string" and value.startswith("-"):
            raise InvalidParams(
                "Invalid params: argument '{0}' must not start with '-'".format(key)
            )
        if expected == "array" and any(item.startswith("-") for item in value):
            raise InvalidParams(
                "Invalid params: array argument '{0}' must not contain "
                "items starting with '-'".format(key)
            )
        choices = properties[key].get("enum")
        if choices is not None and value not in choices:
            # A value outside the declared enum is refused at the guard and
            # never forwarded to the CLI: the enum is how a choice-pinned
            # face declares its withheld choices (the auto tier of the
            # red-event router, the import/intake append legs, the
            # write-bearing i18n pipeline stages).
            raise InvalidParams(
                "Invalid params: argument '{0}' must be one of: {1}".format(
                    key, ", ".join(str(item) for item in choices)
                )
            )
    for key in spec["schema"]["required"]:
        if key not in arguments:
            raise InvalidParams("Invalid params: missing required argument '{0}'".format(key))


def _build_argv(spec, arguments, cli_path):
    """Map schema arguments onto the INDEX entry-line call form.

    Booleans: True appends the flag, False omits it. Values marked '@N' are
    positional. Arrays (RQW13 batch 1): for a positional target the items
    extend the argv in order (an argparse nargs="*" face); for a value flag
    the flag is repeated once per item (an argparse action="append" face).
    Everything else is a value flag passed as --flag value.
    """
    argv = [sys.executable, cli_path]
    argv.extend(spec["fixed_args"])
    for key, flag in spec["arg_map"]:
        if key not in arguments:
            continue
        value = arguments[key]
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        elif isinstance(value, list):
            if flag.startswith("@"):
                argv.extend(str(item) for item in value)
            else:
                for item in value:
                    argv.extend([flag, str(item)])
        elif flag.startswith("@"):
            argv.append(str(value))
        else:
            argv.extend([flag, str(value)])
    return argv


def _run_cli(argv, cwd):
    """Run a tool CLI with captured streams and a hard timeout."""
    timeout_s = _timeout_s()
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "", "tool call timed out after {0}s; child process killed".format(timeout_s)
    except OSError as exc:
        return None, "", "tool call failed to start: {0}".format(exc)
    out = completed.stdout.decode("utf-8", "replace")
    err = completed.stderr.decode("utf-8", "replace")
    code = completed.returncode
    if code is None:
        return None, out, err
    return code, out, err


def _handle_initialize(msg_id, params):
    requested = ""
    if isinstance(params, dict):
        value = params.get("protocolVersion")
        if isinstance(value, str) and value:
            requested = value
    version = requested or PROTOCOL_VERSION_DEFAULT
    return _result(
        msg_id,
        {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    )


def _tools_listing():
    return [
        {
            "name": spec["name"],
            "description": spec["description"],
            "inputSchema": spec["schema"],
        }
        for spec in TOOL_SPECS
    ]


def _handle_tools_call(msg_id, params):
    name = params.get("name")
    if not isinstance(name, str) or not name:
        raise InvalidParams("Invalid params: params.name must be a non-empty string")
    spec = TOOLS_BY_NAME.get(name)
    if spec is None:
        raise InvalidParams("Unknown tool: {0}".format(name))
    arguments = params.get("arguments")
    if arguments is None:
        arguments = {}
    if spec["net_gated"] and os.environ.get(ALLOW_NET_ENV) != "1":
        return _tool_result(msg_id, _deny_text(name), True)
    _validate_arguments(spec, arguments)
    home = os.environ.get(HOME_ENV, "")
    if not home:
        return _tool_result(
            msg_id,
            "capability '{0}' cannot run: environment variable {1} is not set; set it to "
            "the rocqwash repository root and restart the server (docs/mcp.md section 4).".format(name, HOME_ENV),
            True,
        )
    if spec["kind"] == "file":
        path = os.path.join(home, spec["path"])
        if not os.path.isfile(path):
            return _tool_result(
                msg_id,
                "capability '{0}': file not found: {1}".format(name, path),
                True,
            )
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            return _tool_result(
                msg_id,
                "capability '{0}': read failed: {1}".format(name, exc),
                True,
            )
        return _tool_result(msg_id, text, False)
    cli_path = os.path.join(home, spec["cli"])
    if not os.path.isfile(cli_path):
        return _tool_result(
            msg_id,
            "capability '{0}': underlying CLI not found: {1}. Registered ahead of its "
            "landing; see docs/mcp.md section 6.".format(name, cli_path),
            True,
        )
    argv = _build_argv(spec, arguments, cli_path)
    code, out, err = _run_cli(argv, home)
    if code is None:
        return _tool_result(msg_id, err or "tool call failed", True)
    chunks = []
    if out:
        chunks.append(out.rstrip("\r\n"))
    if err:
        chunks.append("[stderr] " + err.rstrip("\r\n"))
    text = "\n".join(chunks) if chunks else "(no output)"
    return _tool_result(msg_id, "exit code: {0}\n{1}".format(code, text), code != 0)


def _dispatch(message):
    if not isinstance(message, dict):
        return _error(None, INVALID_REQUEST, "Invalid Request: expected one JSON object per line")
    msg_id = message.get("id")
    if "id" not in message:
        # A notification gets no response under JSON-RPC 2.0 and MCP.
        _log("notification consumed without response: {0!r}".format(message.get("method")))
        return None
    method = message.get("method")
    if not isinstance(method, str):
        return _error(msg_id, INVALID_REQUEST, "Invalid Request: method must be a string")
    if method == "initialize":
        return _handle_initialize(msg_id, message.get("params"))
    if method == "tools/list":
        return _result(msg_id, {"tools": _tools_listing()})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict):
            return _error(msg_id, INVALID_PARAMS, "Invalid params: params must be an object")
        try:
            return _handle_tools_call(msg_id, params)
        except InvalidParams as exc:
            return _error(msg_id, INVALID_PARAMS, str(exc))
        except OSError as exc:
            return _error(msg_id, INTERNAL_ERROR, "Internal error: {0}".format(exc))
    if method == "ping":
        # MCP ping, the one method R-1 adds to the dispatcher (the design
        # enumeration initialize/tools/list/tools/call/ping): it answers an
        # empty result on both transports.
        return _result(msg_id, {})
    return _error(msg_id, METHOD_NOT_FOUND, "Method not found: {0}".format(method))


def _dispatch_message(message):
    """One parsed JSON-RPC message object in, one response object out.

    The single dispatcher face both transports feed: the stdio loop and
    the HTTP endpoint call it unchanged, so a route rule lands on both
    wires at once.  A route exception becomes an INTERNAL_ERROR
    envelope, never a traceback on the wire; a notification returns None
    (no response under JSON-RPC 2.0 and MCP).
    """
    try:
        return _dispatch(message)
    except Exception as exc:  # fail loud on the wire, keep serving
        msg_id = message.get("id") if isinstance(message, dict) else None
        _log("internal error: {0!r}".format(exc))
        return _error(msg_id, INTERNAL_ERROR, "Internal error: {0}".format(exc))


def _selftest():
    """Run the frozen interface-shape and dispatcher round-trip vectors;
    return 0 green or 1 red.

    V1-V4 inspect module state only (the spec table, the name map, the
    arg_map/schema one-to-one sync, and the schema validation behavior of
    _validate_arguments); V5 round-trips the HTTP-transport dispatcher
    faces in process (body parse, initialize, tools/list, one tools/call
    shape) with no socket; V5b judges the HTTP token gate offline on
    fabricated header dicts (no socket, the env token configured and
    restored in-block); V6, the socket smoke, runs only under
    ROCQWASH_MCP_HTTP_SMOKE=1 against one ephemeral loopback server.
    Zero stdin read, zero writes, and zero sockets in the default face.
    The roster count is a
    frozen vector (the M2 roster: 25 standing specs, six M1 additions,
    eleven M2 ticket additions, the tree_audit registration increment,
    the axiom_sweep registration increment, the claim_watch
    registration increment, the v2-B audit-line batch of three:
    source_fetch, sweep_verdict, release_chain, plus the numeric-probe
    registration batch of two: numeric_probe, statement_probes), the
    same freeze discipline as EXPECTED_TOOLS in tests/t_mcp_face.py; a
    roster change re-freezes both.
    """
    failures = []

    def check(name, cond, detail=""):
        if not cond:
            failures.append("{0}: {1}".format(name, detail or "assertion red"))

    # V1 roster count: the spec table matches the frozen roster size.
    check(
        "V1 roster count",
        len(TOOL_SPECS) == SELFTEST_ROSTER_COUNT,
        "TOOL_SPECS holds {0} specs, the frozen vector expects {1}".format(
            len(TOOL_SPECS), SELFTEST_ROSTER_COUNT
        ),
    )

    # V2 name map: TOOLS_BY_NAME is the complete identity mapping of the
    # spec table, with no duplicate or empty name.
    names = [spec.get("name") for spec in TOOL_SPECS]
    check(
        "V2 spec names are non-empty strings",
        all(isinstance(name, str) and name for name in names),
        "a spec name is missing, empty, or not a string",
    )
    check(
        "V2 spec names unique",
        len(set(names)) == len(names),
        "a duplicate spec name is present",
    )
    check(
        "V2 name map complete",
        len(TOOLS_BY_NAME) == len(TOOL_SPECS)
        and set(TOOLS_BY_NAME) == set(names)
        and all(TOOLS_BY_NAME[name] is spec for name, spec in zip(names, TOOL_SPECS)),
        "TOOLS_BY_NAME is not the identity mapping of TOOL_SPECS",
    )

    # V3 schema validation shape: every spec carries a closed object
    # schema, and _validate_arguments enforces it (empty arguments are
    # accepted exactly when the required list is empty; an unknown
    # argument is refused; a value outside a declared enum is refused).
    for spec in TOOL_SPECS:
        name = spec["name"]
        schema = spec.get("schema")
        shape_ok = (
            isinstance(schema, dict)
            and schema.get("type") == "object"
            and isinstance(schema.get("properties"), dict)
            and isinstance(schema.get("required"), list)
            and set(schema["required"]) <= set(schema["properties"])
            and schema.get("additionalProperties") is False
        )
        check(
            "V3 schema shape {0}".format(name),
            shape_ok,
            "schema is not a closed object schema",
        )
        if not shape_ok:
            continue
        try:
            _validate_arguments(spec, {})
        except InvalidParams:
            empty_refused = True
        else:
            empty_refused = False
        check(
            "V3 empty arguments {0}".format(name),
            empty_refused == bool(schema["required"]),
            "empty-argument verdict does not match the required list",
        )
        try:
            _validate_arguments(spec, {"no_such_argument": "x"})
        except InvalidParams:
            check("V3 unknown argument {0}".format(name), True)
        else:
            check(
                "V3 unknown argument {0}".format(name),
                False,
                "an unknown argument was accepted",
            )
        for key, prop in schema["properties"].items():
            choices = prop.get("enum")
            if not choices:
                continue
            outside = next(
                (item for item in ("__no_such_choice__", -1)
                 if item not in choices),
                None,
            )
            try:
                _validate_arguments(spec, {key: outside})
            except InvalidParams:
                check("V3 enum refusal {0}.{1}".format(name, key), True)
            else:
                check(
                    "V3 enum refusal {0}.{1}".format(name, key),
                    False,
                    "a value outside the declared enum was accepted",
                )

    # V4 arg_map/schema sync: every spec's schema property set matches its
    # arg_map key set one-to-one.  A schema flag with no arg_map row would
    # be accepted at the guard and then silently dropped from the child
    # argv; an arg_map row with no schema property would be unreachable
    # from the wire.  (Micro-ticket face: this vector pins the expanded
    # vacgen_generate flag table against its schema.)
    for spec in TOOL_SPECS:
        name = spec["name"]
        arg_keys = sorted(key for key, _flag in spec["arg_map"])
        schema_keys = sorted(spec["schema"]["properties"])
        check(
            "V4 arg_map/schema sync {0}".format(name),
            arg_keys == schema_keys,
            "arg_map keys {0} != schema properties {1}".format(arg_keys, schema_keys),
        )

    # V5 HTTP-transport dispatcher round trips: the shared body-parse and
    # dispatcher faces the HTTP endpoint feeds, exercised in process with
    # no socket (R-1: one dispatcher, two wires).  The initialize and
    # tools/list envelopes and one tools/call shape are pinned here so a
    # transport cannot drift from the stdio contract.
    status, init_resp = _http_handle_body(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 101,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION_DEFAULT},
            }
        ).encode("utf-8")
    )
    check("V5 initialize status", status == 200, "status {0}".format(status))
    check(
        "V5 initialize round trip",
        isinstance(init_resp, dict)
        and init_resp.get("jsonrpc") == "2.0"
        and init_resp.get("id") == 101
        and init_resp.get("result", {}).get("protocolVersion")
        == PROTOCOL_VERSION_DEFAULT
        and init_resp.get("result", {}).get("serverInfo", {}).get("name")
        == SERVER_NAME,
        "the initialize envelope drifted",
    )
    status, init_default = _http_handle_body(
        json.dumps({"jsonrpc": "2.0", "id": 102, "method": "initialize"}).encode(
            "utf-8"
        )
    )
    check(
        "V5 initialize default version",
        status == 200
        and (init_default or {}).get("result", {}).get("protocolVersion")
        == PROTOCOL_VERSION_DEFAULT,
        "a params-less initialize must answer the default protocol version",
    )
    status, listing_resp = _http_handle_body(
        json.dumps({"jsonrpc": "2.0", "id": 103, "method": "tools/list"}).encode(
            "utf-8"
        )
    )
    listed = (listing_resp or {}).get("result", {}).get("tools", [])
    check(
        "V5 tools list round trip",
        status == 200
        and len(listed) == len(TOOL_SPECS)
        and [tool.get("name") for tool in listed] == [spec["name"] for spec in TOOL_SPECS]
        and all(isinstance(tool.get("inputSchema"), dict) for tool in listed),
        "the tools/list face drifted",
    )
    status, unknown_resp = _http_handle_body(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 104,
                "method": "tools/call",
                "params": {"name": "__no_such_tool__", "arguments": {}},
            }
        ).encode("utf-8")
    )
    check(
        "V5 tools call unknown tool",
        status == 200
        and (unknown_resp or {}).get("error", {}).get("code") == INVALID_PARAMS
        and "Unknown tool"
        in (unknown_resp or {}).get("error", {}).get("message", ""),
        "an unknown tool must be an INVALID_PARAMS envelope",
    )
    status, badargs_resp = _http_handle_body(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 105,
                "method": "tools/call",
                "params": {"name": "capability_index",
                           "arguments": {"no_such_argument": 1}},
            }
        ).encode("utf-8")
    )
    check(
        "V5 tools call argument guard",
        status == 200
        and (badargs_resp or {}).get("error", {}).get("code") == INVALID_PARAMS,
        "an unknown argument must be refused by the shared guard",
    )
    # V5 tools/call shape through the home gate: ROCQWASH_HOME is cleared
    # for this one call (restored below), so the envelope is the
    # deterministic not-set face -- no child process, no file read, no
    # socket; the dispatcher's full tools/call path (validation, gate,
    # home check) is exercised and stops deterministically.
    saved_home = os.environ.get(HOME_ENV)
    try:
        os.environ.pop(HOME_ENV, None)
        status, call_resp = _http_handle_body(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 106,
                    "method": "tools/call",
                    "params": {"name": "capability_index", "arguments": {}},
                }
            ).encode("utf-8")
        )
    finally:
        if saved_home is not None:
            os.environ[HOME_ENV] = saved_home
    call_text = (((call_resp or {}).get("result") or {}).get("content") or [{}])[
        0
    ].get("text", "")
    check(
        "V5 tools call shape",
        status == 200
        and (call_resp or {}).get("result", {}).get("isError") is True
        and HOME_ENV in call_text,
        "the tools/call shape must reach the home gate without a subprocess",
    )
    status, ping_resp = _http_handle_body(
        json.dumps({"jsonrpc": "2.0", "id": 107, "method": "ping"}).encode("utf-8")
    )
    check(
        "V5 ping round trip",
        status == 200 and (ping_resp or {}).get("result") == {},
        "ping must answer an empty result on the shared dispatcher",
    )
    status, method_resp = _http_handle_body(
        json.dumps({"jsonrpc": "2.0", "id": 108, "method": "resources/list"}).encode(
            "utf-8"
        )
    )
    check(
        "V5 method not found",
        status == 200
        and (method_resp or {}).get("error", {}).get("code") == METHOD_NOT_FOUND,
        "resources/list must stay METHOD_NOT_FOUND",
    )
    status, notification = _http_handle_body(
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode(
            "utf-8"
        )
    )
    check(
        "V5 notification no response",
        status == 202 and notification is None,
        "a notification must produce no envelope",
    )
    status, parse_resp = _http_handle_body(b"{definitely not json")
    check(
        "V5 malformed body parse error",
        status == 400
        and (parse_resp or {}).get("error", {}).get("code") == PARSE_ERROR
        and (parse_resp or {}).get("id") is None,
        "a malformed body must be a parse-error object, never a traceback",
    )
    status, utf_resp = _http_handle_body(b"\xff\xfe\xfd")
    check(
        "V5 non-utf8 body parse error",
        status == 400
        and (utf_resp or {}).get("error", {}).get("code") == PARSE_ERROR,
        "a non-UTF-8 body must be a parse-error object",
    )

    # V5b auth gate offline vectors: _http_auth_failure judged directly on
    # fabricated header dicts (no socket); the env token is configured and
    # restored around the block (the gate reads the env per call).  These
    # always-on vectors cover the constant-time comparison face between
    # smokes, where only the V7 socket vectors exercise the gate.
    saved_token = os.environ.get(AUTH_TOKEN_ENV)
    try:
        os.environ.pop(AUTH_TOKEN_ENV, None)
        check(
            "V5b auth gate unconfigured is open",
            _http_auth_failure({}) is None,
            "no ROCWASH_MCP_TOKEN in the env = the gate answers None",
        )
        os.environ[AUTH_TOKEN_ENV] = "v5b-token-42"
        check(
            "V5b auth gate missing credential",
            _http_auth_failure({}) == "missing",
            "configured gate + no credential header = missing",
        )
        check(
            "V5b auth gate bearer mismatch",
            _http_auth_failure({"Authorization": "Bearer wrong-token"})
            == "mismatch",
            "configured gate + a wrong bearer token = mismatch",
        )
        check(
            "V5b auth gate bearer match",
            _http_auth_failure(
                {"Authorization": "Bearer v5b-token-42"}) is None,
            "configured gate + the right bearer token = None",
        )
        check(
            "V5b auth gate header match",
            _http_auth_failure(
                {"X-ROCQWASH-TOKEN": "v5b-token-42"}) is None,
            "configured gate + the right X-ROCQWASH-TOKEN = None",
        )
    finally:
        if saved_token is None:
            os.environ.pop(AUTH_TOKEN_ENV, None)
        else:
            os.environ[AUTH_TOKEN_ENV] = saved_token

    # V6 socket smoke: env-gated (default off -- the default selftest
    # opens no socket, binds no port, answers no SYN).
    if os.environ.get(HTTP_SMOKE_ENV) == "1":
        _http_smoke_vectors(check)
    else:
        _log(
            "http socket smoke skipped (default off; set {0}=1 to include it)".format(
                HTTP_SMOKE_ENV
            )
        )

    if failures:
        for line in failures:
            sys.stderr.write("MCP-SERVER-SELFTEST FAIL {0}\n".format(line))
        return 1
    sys.stdout.write(
        "MCP-SERVER-SELFTEST PASS (roster {0} specs, name map complete, "
        "schema validation green)\n".format(len(TOOL_SPECS))
    )
    return 0


def _serve():
    """Serve the MCP stdio loop until stdin reaches end of file."""
    _log(
        "rocqwash MCP stdio server ready: methods initialize/tools/list/tools/call; "
        "allow-net={0}".format(os.environ.get(ALLOW_NET_ENV) == "1")
    )
    for raw in sys.stdin.buffer:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            _emit(_error(None, PARSE_ERROR, "Parse error: line is not valid UTF-8"))
            continue
        line = text.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            _emit(_error(None, PARSE_ERROR, "Parse error: line is not valid JSON"))
            continue
        response = _dispatch_message(message)
        if response is not None:
            _emit(response)
    return 0


# ---- R-1 HTTP transport: one shared dispatcher, two wires.  The stdio
# face keeps its loop; the HTTP face answers POST /mcp with the same
# envelopes, so a dead client connection costs one HTTP session and never
# the tool registry.


class _McpSessionTable:
    """Registry of the internal session ids handed out in the
    Mcp-Session-Id response header.

    Advisory correlation state, not an authentication face: a request
    with no id, or with an id this process never issued, is served a
    fresh session without error.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._known = set()

    def create(self):
        session_id = "mcp-" + os.urandom(12).hex()
        with self._lock:
            self._known.add(session_id)
        return session_id

    def holds(self, session_id):
        with self._lock:
            return session_id in self._known


def _http_auth_failure(headers):
    """The HTTP token gate (ROCWASH_MCP_TOKEN): when the env token is
    configured, every POST must carry it (an X-ROCQWASH-TOKEN header, or
    Authorization: Bearer <token>); an unauthenticated request answers 401.
    Unconfigured = the gate is open (never fail-closed: a runner upgrading
    to this build keeps serving); the serve faces print one loud
    auth-disabled warning at startup so the open gate is never silent.
    GET is the 405 hint face only and carries no data, so it is ungated.
    Reads the env per request, so a running server can be gated or opened
    by env changes without a restart (the smoke vectors rely on this).
    The comparison is constant time (hmac.compare_digest over the utf-8
    encodings), so request handling does not leak the token through
    comparison timing."""
    expected = os.environ.get(AUTH_TOKEN_ENV, "")
    if not expected:
        return None
    supplied = headers.get("X-ROCQWASH-TOKEN") or ""
    if not supplied:
        auth = headers.get("Authorization") or ""
        if auth.startswith("Bearer "):
            supplied = auth[len("Bearer "):].strip()
    if not hmac.compare_digest(supplied.encode("utf-8"),
                               expected.encode("utf-8")):
        return "missing" if not supplied else "mismatch"
    return None


class _McpHttpHandler(http.server.BaseHTTPRequestHandler):
    """The HTTP face of the shared MCP dispatcher.

    Contract: POST /mcp with one JSON-RPC 2.0 object as the body, one
    application/json envelope back (202 Accepted with an empty body for
    a notification), and an Mcp-Session-Id response header carrying an
    internal session id.  GET /mcp answers 405 with a plain hint; every
    other method and path answers 404; a malformed body answers a
    JSON-RPC parse-error object, never a traceback.  Dispatch runs under
    the same fail-loud guard as the stdio loop.
    """

    server_version = SERVER_NAME + "/" + SERVER_VERSION
    protocol_version = "HTTP/1.1"
    # Injected per listener by _build_http_server: each server owns its
    # session table (the smoke listener stays isolated from a real one).
    session_table = None

    # -- response plumbing ------------------------------------------

    def _split_path(self):
        return self.path.split("?", 1)[0]

    def _respond(self, status, body, content_type, session_id=None, extra_headers=()):
        self.send_response(status)
        for key, value in extra_headers:
            self.send_header(key, value)
        if session_id is not None:
            self.send_header(HTTP_SESSION_HEADER, session_id)
        if body:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _respond_json(self, status, payload, session_id=None):
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self._respond(status, body, "application/json", session_id)

    def _respond_hint(self, status, text, extra_headers=()):
        body = (text + "\n").encode("utf-8")
        self._respond(
            status, body, "text/plain; charset=utf-8", None, extra_headers
        )

    def _read_declared_body(self):
        """Drain a declared request body so keep-alive framing survives a
        response that does not consume it (wrong path, wrong method)."""
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            return
        try:
            length = int(length_header)
        except ValueError:
            self.close_connection = True
            return
        if length < 0 or length > HTTP_MAX_BODY_BYTES:
            self.close_connection = True
        elif length:
            self.rfile.read(length)

    def _resolve_session(self):
        """Reuse the session id the client echoes when this process issued
        it; otherwise mint one.  Always returns a non-empty id."""
        requested = self.headers.get(HTTP_SESSION_HEADER)
        if (
            isinstance(requested, str)
            and requested
            and self.session_table is not None
            and self.session_table.holds(requested)
        ):
            return requested
        return self.session_table.create()

    # -- the method faces -------------------------------------------

    def do_POST(self):
        if self._split_path() != HTTP_ENDPOINT_PATH:
            self._read_declared_body()
            self._respond_hint(
                404,
                "Not Found: the MCP endpoint is POST {0} with a JSON-RPC 2.0 "
                "object; this path serves nothing.".format(HTTP_ENDPOINT_PATH),
            )
            return
        auth_reason = _http_auth_failure(self.headers)
        if auth_reason is not None:
            self._read_declared_body()
            self._respond_hint(
                401,
                "Unauthorized ({0}): the ROCQWASH_MCP_TOKEN gate is configured; "
                "carry the X-ROCQWASH-TOKEN header (or Authorization: Bearer "
                "<token>).".format(auth_reason),
            )
            return
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            body = b""  # no declared body: the parse face answers the envelope
        else:
            try:
                length = int(length_header)
            except ValueError:
                self._respond_hint(
                    400, "Bad Request: Content-Length is not an integer."
                )
                return
            if length < 0:
                self._respond_hint(400, "Bad Request: Content-Length is negative.")
                return
            if length > HTTP_MAX_BODY_BYTES:
                # Not drained on purpose; the Connection header ends it.
                self._respond_hint(
                    413,
                    "Payload Too Large: the request body cap is {0} bytes.".format(
                        HTTP_MAX_BODY_BYTES
                    ),
                    extra_headers=(("Connection", "close"),),
                )
                return
            body = self.rfile.read(length)
        session_id = self._resolve_session()
        status, response = _http_handle_body(body)
        if response is None:
            self._respond(status, b"", "", session_id)
        else:
            self._respond_json(status, response, session_id)

    def do_GET(self):
        self._read_declared_body()
        if self._split_path() == HTTP_ENDPOINT_PATH:
            self._respond_hint(
                405,
                "Method Not Allowed: POST a JSON-RPC 2.0 object to {0} "
                "(application/json); this server answers protocol JSON, "
                "not HTML.".format(HTTP_ENDPOINT_PATH),
                extra_headers=(("Allow", "POST"),),
            )
            return
        self._respond_hint(
            404,
            "Not Found: the MCP endpoint is POST {0}.".format(HTTP_ENDPOINT_PATH),
        )

    def do_HEAD(self):
        self._respond_hint(
            404, "Not Found: only POST {0} speaks MCP JSON-RPC.".format(
                HTTP_ENDPOINT_PATH
            )
        )

    def _method_not_supported(self):
        self._read_declared_body()
        headers = (
            (("Allow", "POST"),) if self._split_path() == HTTP_ENDPOINT_PATH else ()
        )
        self._respond_hint(
            404,
            "Not Found: only POST {0} speaks MCP JSON-RPC.".format(
                HTTP_ENDPOINT_PATH
            ),
            extra_headers=headers,
        )

    def __getattr__(self, name):
        # Every method without an explicit face above (PUT, DELETE, PATCH,
        # OPTIONS, TRACE, and any exotic verb) answers 404 per the R-1
        # contract: unsupported methods are 404, never the stdlib default 501.
        if name.startswith("do_"):
            return self._method_not_supported
        raise AttributeError(name)

    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        _log("http {0} - {1}".format(self.address_string(), format % args))


class _McpHttpServer(http.server.ThreadingHTTPServer):
    """Threading HTTP listener for the shared dispatcher; daemon threads
    so a co-tenant transport's exit never waits on an open connection."""

    daemon_threads = True
    allow_reuse_address = True


def _build_http_server(host, port):
    """Bind the HTTP face on host:port; None on bind failure (the caller
    turns that into exit code 1 with the reason on stderr)."""
    table = _McpSessionTable()

    class _BoundMcpHttpHandler(_McpHttpHandler):
        session_table = table

    try:
        return _McpHttpServer((host, port), _BoundMcpHttpHandler)
    except OSError as exc:
        _log("http bind failed on {0}:{1}: {2}".format(host, port, exc))
        return None


def _http_handle_body(raw):
    """One HTTP request body in, one (status, envelope-or-None) out.

    The HTTP-side parse face onto the same shared dispatcher the stdio
    loop feeds: a body that is not valid UTF-8 JSON comes back as a
    JSON-RPC parse-error object with HTTP 400, a notification as
    (202, None), everything else as (200, envelope).  Never raises.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return 400, _error(None, PARSE_ERROR, "Parse error: body is not valid UTF-8")
    try:
        message = json.loads(text)
    except ValueError:
        return 400, _error(None, PARSE_ERROR, "Parse error: body is not valid JSON")
    response = _dispatch_message(message)
    if response is None:
        return 202, None
    return 200, response


def _serve_http(host, port):
    """Serve the HTTP face standalone: no stdin read, no stdio face."""
    server = _build_http_server(host, port)
    if server is None:
        return 1
    bound_host, bound_port = server.server_address[:2]
    if not os.environ.get(AUTH_TOKEN_ENV):
        _log("WARNING auth-disabled: {0} unset - the HTTP face answers "
             "unauthenticated POSTs (trusted-network-only binding; set the "
             "token to require X-ROCQWASH-TOKEN on every POST)".format(AUTH_TOKEN_ENV))
    _log(
        "rocqwash MCP http server ready: POST http://{0}:{1}{2} "
        "(application/json, {3} header per response); stdio face not served; "
        "allow-net={4}".format(
            bound_host,
            bound_port,
            HTTP_ENDPOINT_PATH,
            HTTP_SESSION_HEADER,
            os.environ.get(ALLOW_NET_ENV) == "1",
        )
    )
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        _log("http server interrupted; shutting down")
    finally:
        server.server_close()
    return 0


def _serve_stdio_and_http(host, port):
    """Serve both faces in one process: the stdio loop on the main thread,
    the HTTP listener on a daemon thread.  A dead stdio pipe ends the
    process and the listener with it; a dead HTTP session ends only that
    one connection -- neither takes the tool registry down."""
    server = _build_http_server(host, port)
    if server is None:
        return 1
    bound_host, bound_port = server.server_address[:2]
    if not os.environ.get(AUTH_TOKEN_ENV):
        _log("WARNING auth-disabled: {0} unset - the HTTP face answers "
             "unauthenticated POSTs (trusted-network-only binding; set the "
             "token to require X-ROCQWASH-TOKEN on every POST)".format(AUTH_TOKEN_ENV))
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True
    )
    thread.start()
    _log(
        "rocqwash MCP dual transport ready: stdio plus POST http://{0}:{1}{2}".format(
            bound_host, bound_port, HTTP_ENDPOINT_PATH
        )
    )
    try:
        code = _serve()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)
    return code


def _http_smoke_vectors(check):
    """V6 socket smoke: bind one ephemeral loopback server and run real
    HTTP round trips through it (initialize, session echo, tools/list,
    malformed body, GET 405, unknown path 404, unsupported method 404,
    notification 202).  Called only under the ROCQWASH_MCP_HTTP_SMOKE=1
    gate: the default selftest opens no socket at all."""
    import http.client

    server = _build_http_server("127.0.0.1", 0)
    if server is None:
        check("V6 smoke bind", False, "the ephemeral loopback bind failed")
        return
    port = server.server_address[1]
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    )
    thread.start()
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:

        def _json_body(response):
            try:
                return json.loads(response.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return {}

        post_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        connection.request(
            "POST",
            HTTP_ENDPOINT_PATH,
            body=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "initialize",
                    "params": {"protocolVersion": PROTOCOL_VERSION_DEFAULT},
                }
            ),
            headers=post_headers,
        )
        response = connection.getresponse()
        body = _json_body(response)
        session_id = response.getheader(HTTP_SESSION_HEADER)
        check(
            "V6 smoke initialize status",
            response.status == 200,
            "status {0}".format(response.status),
        )
        check(
            "V6 smoke initialize content type",
            (response.getheader("Content-Type") or "").startswith("application/json"),
            "Content-Type {0!r}".format(response.getheader("Content-Type")),
        )
        check(
            "V6 smoke session header issued",
            isinstance(session_id, str) and bool(session_id),
            "no {0} response header".format(HTTP_SESSION_HEADER),
        )
        check(
            "V6 smoke initialize body",
            body.get("id") == 7
            and body.get("result", {}).get("serverInfo", {}).get("name") == SERVER_NAME,
            "body {0!r}".format(body),
        )

        echo_headers = dict(post_headers)
        echo_headers[HTTP_SESSION_HEADER] = session_id or "unissued"
        connection.request(
            "POST",
            HTTP_ENDPOINT_PATH,
            body=json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/list"}),
            headers=echo_headers,
        )
        response = connection.getresponse()
        body = _json_body(response)
        check(
            "V6 smoke session echo",
            response.getheader(HTTP_SESSION_HEADER) == session_id,
            "session header {0!r}".format(response.getheader(HTTP_SESSION_HEADER)),
        )
        check(
            "V6 smoke tools list count",
            len(body.get("result", {}).get("tools", [])) == SELFTEST_ROSTER_COUNT,
            "tools {0}".format(len(body.get("result", {}).get("tools", []))),
        )

        connection.request(
            "POST", HTTP_ENDPOINT_PATH, body="{not json", headers=post_headers
        )
        response = connection.getresponse()
        body = _json_body(response)
        check(
            "V6 smoke malformed status",
            response.status == 400,
            "status {0}".format(response.status),
        )
        check(
            "V6 smoke malformed parse error",
            body.get("error", {}).get("code") == PARSE_ERROR and body.get("id") is None,
            "body {0!r}".format(body),
        )

        connection.request("GET", HTTP_ENDPOINT_PATH, headers={"Accept": "text/plain"})
        response = connection.getresponse()
        hint = response.read()
        check(
            "V6 smoke get 405 hint",
            response.status == 405
            and b"POST" in hint
            and response.getheader("Allow") == "POST",
            "status {0} hint {1!r}".format(response.status, hint[:120]),
        )

        connection.request("GET", "/no-such-face", headers={"Accept": "text/plain"})
        response = connection.getresponse()
        response.read()
        check(
            "V6 smoke unknown path 404",
            response.status == 404,
            "status {0}".format(response.status),
        )

        connection.request(
            "PUT", HTTP_ENDPOINT_PATH, body=b"x", headers={"Content-Length": "1"}
        )
        response = connection.getresponse()
        response.read()
        check(
            "V6 smoke unsupported method 404",
            response.status == 404,
            "status {0}".format(response.status),
        )

        connection.request(
            "POST",
            HTTP_ENDPOINT_PATH,
            body=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            headers=post_headers,
        )
        response = connection.getresponse()
        payload = response.read()
        check(
            "V6 smoke notification 202",
            response.status == 202
            and payload == b""
            and bool(response.getheader(HTTP_SESSION_HEADER)),
            "status {0} body {1!r}".format(response.status, payload[:50]),
        )
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)

    # V7 token gate (ROCWASH_MCP_TOKEN): one fresh ephemeral server with
    # the env token configured - unauthenticated POST answers 401, the
    # authenticated POST is served, and the gate reads the env per request
    # so the finally-restore reopens the face without a restart.
    token_server = _build_http_server("127.0.0.1", 0)
    if token_server is None:
        check("V7 token gate bind", False, "the ephemeral loopback bind failed")
    else:
        token_port = token_server.server_address[1]
        token_thread = threading.Thread(
            target=token_server.serve_forever, kwargs={"poll_interval": 0.05},
            daemon=True,
        )
        token_thread.start()
        token_connection = http.client.HTTPConnection(
            "127.0.0.1", token_port, timeout=10)
        init_body = json.dumps(
            {"jsonrpc": "2.0", "id": 41, "method": "initialize",
             "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                        "clientInfo": {"name": "smoke", "version": "0"}}})
        os.environ[AUTH_TOKEN_ENV] = "smoke-token-42"
        try:
            token_connection.request(
                "POST",
                HTTP_ENDPOINT_PATH,
                body=init_body,
                headers={"Content-Type": "application/json",
                         "Accept": "application/json",
                         "Content-Length": str(len(init_body))},
            )
            response = token_connection.getresponse()
            payload = response.read()
            check(
                "V7 token 401 unauthenticated",
                response.status == 401 and b"Unauthorized" in payload,
                "status {0} body {1!r}".format(response.status, payload[:50]),
            )
            token_connection.request(
                "POST",
                HTTP_ENDPOINT_PATH,
                body=init_body,
                headers={"Content-Type": "application/json",
                         "Accept": "application/json",
                         "Content-Length": str(len(init_body)),
                         "X-ROCQWASH-TOKEN": "smoke-token-42"},
            )
            response = token_connection.getresponse()
            payload = response.read()
            check(
                "V7 token authenticated passes",
                response.status == 200,
                "status {0} body {1!r}".format(response.status, payload[:50]),
            )
        finally:
            os.environ.pop(AUTH_TOKEN_ENV, None)
            token_connection.close()
            token_server.shutdown()
            token_server.server_close()
            token_thread.join(timeout=5.0)


def _build_parser():
    """The argparse flag gate, shared by main and the selftest vectors."""
    parser = argparse.ArgumentParser(
        prog="mcp_server.py",
        description="rocqwash MCP server: newline-delimited JSON-RPC 2.0 over "
        "stdin and stdout by default, with an optional HTTP transport on the "
        "same shared dispatcher (docs/mcp.md).",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the frozen interface-shape vectors and the dispatcher "
        "round-trip vectors and exit; no service loop, no stdin read, and no "
        "socket unless {0}=1 (then one ephemeral loopback server is used for "
        "the HTTP smoke)".format(HTTP_SMOKE_ENV),
    )
    parser.add_argument(
        "--http",
        metavar="PORT",
        type=int,
        help="serve MCP JSON-RPC over HTTP on this TCP port at endpoint {0} "
        "(POST, application/json responses); combined with --stdio both "
        "transports run in one process, without --stdio the process serves "
        "HTTP only and does not read stdin".format(HTTP_ENDPOINT_PATH),
    )
    parser.add_argument(
        "--http-host",
        metavar="HOST",
        default=HTTP_DEFAULT_HOST,
        help="address for the HTTP listener (default: 127.0.0.1, local only). "
        "Widening it (for example 0.0.0.0) exposes the endpoint beyond this "
        "machine; trusted-network-only: the endpoint performs no "
        "authentication, so never expose it to an untrusted network",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="serve the newline-delimited JSON-RPC stdio face on stdin and "
        "stdout (the default face when no flag selects a transport); combine "
        "with --http to run both transports in one process",
    )
    return parser


def main(argv=None):
    """Parse the CLI flag gate, then route to the selected face or faces;
    with no flag the stdio service loop is the one face."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.http is not None:
        if not 1 <= args.http <= 65535:
            parser.error("--http PORT must be an integer between 1 and 65535")
        if args.stdio:
            return _serve_stdio_and_http(args.http_host, args.http)
        return _serve_http(args.http_host, args.http)
    return _serve()


if __name__ == "__main__":
    sys.exit(main())
