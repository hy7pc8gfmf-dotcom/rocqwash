#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_mcp_face.py - tests/ suite shell for the RQW13 MCP face expansion
(tools/mcp_server.py).

Purpose.  Spawn the expanded MCP stdio server as a child process and drive
  one newline-delimited JSON-RPC session line by line, asserting the
  31-capability face: the RQW08 legacy 8, the RQW13 batch-1 zero-network 13,
  the engine-body ticket's three capabilities (graduated from
  docs/drafts/mcp-tool-specs-engine-body.md by the integration agent), the
  symbiosis ticket's one read-only capability (symbiosis_status, a
  capability_index-style file face over docs/symbiosis_sop.md, registered
  from the symbiosis ticket's spec section 1.1), and the MCP
  roster-expansion work stream 1's six capabilities (the M1 ticket, five
  INDEX entries already standing plus the gap_cluster entry that lands with
  the
  same increment), each new capability
  transcribed from its docs/CAPABILITY-INDEX.md section 2 entry line (the
  symbiosis INDEX entry line lands with the integration increment).

Interface.  `python3 tests/t_mcp_face.py` (rostered in tests/run_tests.sh
  as case t_mcp_face on 20261115, audit finding P0-6; the roster count is
  derived one-way from the CASES block in tests/run_tests.sh by doc_lint's
  second check).

Probes (one session, in order; zero network):
  1  initialize -> protocolVersion echo plus serverInfo name rocqwash-mcp
  2  notifications/initialized -> no response line
  3  tools/list -> exactly the 31 expected names in registration order,
     each with a description and a closed-object inputSchema
  4  live-call spot checks (three of the new batch, all zero network):
     4a http_backoff (no arguments; fixed --selftest) -> exit code: 0 with
        the frozen-vector pass face
     4b norm_lint {"selftest": true} -> exit code: 0 with the selftest
        final PASS line
     4c chain_graph {"ledgers": [a.json, b.json]} on two synthetic tmp
        ledgers -> exit code: 0 and a chain root in the markdown output
        (evidence for the array positional path: two array elements land
        as two positional LEDGER.json paths in one call)
  5  default deny -> tools/call net_probe returns isError true and names
     ROCQWASH_MCP_ALLOW_NET (the env is removed from the child)
  6  error faces -> resources/list -32601; unknown tool -32602; unknown
     argument on a new capability -32602; an array item starting with "-"
     -32602; a malformed line -32700 with id null

Dependencies.  Python 3 stdlib only; the server and every called CLI are
  stdlib-only; probes 4a/4b/4c run selftest faces or temporary fixtures
  only; no repository byte is written; zero network.

Evidence.  Every probe asserts a first-hand response line from the child
  server on this machine; nothing is inferred from source reading.

Exit-codes.  0 = all probes pass; 1 = any probe red (fail-loud, the red
  probe is printed; no silent downgrade).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(REPO, "tools", "mcp_server.py")

EXPECTED_TOOLS = [
    # RQW08 legacy 8 (integration order)
    "sentinel_status", "net_probe", "baselinediff", "ci_triage",
    "vacgen_generate", "exp_append", "pushci_status", "capability_index",
    # RQW13 batch-1 zero-network 13 (expansion-ticket order)
    "chain_graph", "doc_lint", "ledger_sync", "netname_normalize",
    "norm_lint", "render_events", "select_audit", "registry_audit",
    "registry_fix", "registry_regen", "registry_union", "abl1_4b_compile",
    "http_backoff",
    # the engine-body ticket's batch (3, graduated from the lane-8
    # draft docs/drafts/mcp-tool-specs-engine-body.md by the integration agent)
    "ai_flavor_detect", "jargon_plan", "i18n_pipeline_dryrun",
    # the symbiosis ticket's one read-only capability (spec section 1.1:
    # a capability_index-style file face over docs/symbiosis_sop.md; its
    # INDEX entry line lands with the integration increment)
    "symbiosis_status",
    # the MCP roster-expansion work stream 1 (the M1 ticket's six read/plan
    # faces:
    # termbase/verdict_diff/learning_feedback/b_gate_audit read,
    # evolution_dashboard/gap_cluster plan; each spec transcribed from its
    # docs/CAPABILITY-INDEX.md section 2 entry line)
    "termbase", "verdict_diff", "learning_feedback", "b_gate_audit",
    "evolution_dashboard", "gap_cluster",
]


def _session(requests):
    """Run one stdio session; requests are dicts or raw (malformed) strings."""
    env = dict(os.environ)
    env["ROCQWASH_HOME"] = REPO
    env.pop("ROCQWASH_MCP_ALLOW_NET", None)  # probe 5 exercises default deny
    payload = "".join(
        (r if isinstance(r, str) else json.dumps(r)) + "\n" for r in requests
    )
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-B", SERVER],
        input=payload.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=REPO, env=env, timeout=120,
    )
    lines = []
    for raw in proc.stdout.decode("utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if raw:
            lines.append(json.loads(raw))
    return proc.returncode, lines, proc.stderr.decode("utf-8", errors="replace")


def _by_id(lines, msg_id):
    for line in lines:
        if line.get("id") == msg_id and ("result" in line or "error" in line):
            return line
    return None


def _result_text(line):
    try:
        return line["result"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""


def _make_ledgers(tmp):
    """Two synthetic ledgers in the W13 shape (chain_graph selftest shape)."""
    la = {"LibX": {"file": "LibX", "rc": 0, "red": ""},
          "B1": {"file": "B1", "rc": 1,
                 "red": "Error: Unable to locate library | LibX"}}
    lb = {"B2": {"file": "B2", "rc": 0, "red": ""},
          "D1": {"file": "D1", "rc": 1,
                 "red": "Error: Unable to locate library | LibX"}}
    fa = os.path.join(tmp, "ledgerA.json")
    fb = os.path.join(tmp, "ledgerB.json")
    with open(fa, "w", encoding="utf-8") as h:
        json.dump(la, h)
    with open(fb, "w", encoding="utf-8") as h:
        json.dump(lb, h)
    return fa, fb, os.path.join(tmp, "graph.json"), os.path.join(tmp, "top.md")


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="t_mcp_face_")
    try:
        fa, fb, jf, mf = _make_ledgers(tmp)
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "t_mcp_face"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "http_backoff", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "norm_lint",
                        "arguments": {"selftest": True}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": [fa, fb],
                                      "json_out": jf, "md_out": mf}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
             "params": {"name": "net_probe", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 7, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
             "params": {"name": "no_such_tool", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": [fa], "bogus": True}}},
            {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
             "params": {"name": "chain_graph",
                        "arguments": {"ledgers": ["-x"]}}},
            "this line is not json",
        ]
        rc, lines, err = _session(requests)

        # Probe 1: initialize
        init = _by_id(lines, 1)
        info = (init or {}).get("result", {}).get("serverInfo", {})
        if not init or "result" not in init:
            fails.append("probe1 initialize should return a result")
        elif info.get("name") != "rocqwash-mcp":
            fails.append("probe1 serverInfo.name should be rocqwash-mcp, "
                         "got %r" % (info.get("name"),))
        elif not init["result"].get("protocolVersion"):
            fails.append("probe1 protocolVersion echo missing")

        # Probe 2: the notification gets no response line
        responses = [l for l in lines if "id" in l or "error" in l]
        if any(l.get("id") is None and l.get("error", {}).get("code")
               not in (None, -32700) for l in lines):
            fails.append("probe2 unexpected response for the notification")
        for l in lines:
            if l.get("method") == "notifications/initialized":
                fails.append("probe2 notification echoed back")

        # Probe 3: tools/list carries exactly the 25 expected names
        listing = _by_id(lines, 2)
        tools = (listing or {}).get("result", {}).get("tools", [])
        names = [t.get("name") for t in tools]
        if names != EXPECTED_TOOLS:
            fails.append("probe3 tools/list face drift\nexpected=%r\nactual=%r"
                         % (EXPECTED_TOOLS, names))
        for t in tools:
            if not t.get("description"):
                fails.append("probe3 %s missing description" % t.get("name"))
            schema = t.get("inputSchema")
            if not isinstance(schema, dict) or schema.get("type") != "object" \
                    or schema.get("additionalProperties") is not False:
                fails.append("probe3 %s inputSchema not a closed object"
                             % t.get("name"))

        # Probe 4a: http_backoff live call
        r3 = _by_id(lines, 3)
        text3 = _result_text(r3)
        if not r3 or r3.get("result", {}).get("isError"):
            fails.append("probe4a http_backoff should not be an error\n%s"
                         % text3)
        elif "exit code: 0" not in text3 or "SELFTEST PASS" not in text3:
            fails.append("probe4a http_backoff exit 0 + pass face missing\n%s"
                         % text3)

        # Probe 4b: norm_lint selftest live call
        r4 = _by_id(lines, 4)
        text4 = _result_text(r4)
        if not r4 or r4.get("result", {}).get("isError"):
            fails.append("probe4b norm_lint selftest should not be an error\n%s"
                         % text4)
        elif "exit code: 0" not in text4 or "PASS english-clean" not in text4:
            fails.append("probe4b norm_lint exit 0 + english-clean face "
                         "missing\n%s" % text4)

        # Probe 4c: chain_graph two-ledger merge (array positional path)
        r5 = _by_id(lines, 5)
        text5 = _result_text(r5)
        if not r5 or r5.get("result", {}).get("isError"):
            fails.append("probe4c chain_graph merge should not be an error\n%s"
                         % text5)
        elif "exit code: 0" not in text5:
            fails.append("probe4c chain_graph exit 0 missing\n%s" % text5)
        else:
            with open(mf, "r", encoding="utf-8") as h:
                md = h.read()
            if "LibX" not in md:
                fails.append("probe4c chain root LibX missing from md face")

        # Probe 5: default deny negative sample
        r6 = _by_id(lines, 6)
        text6 = _result_text(r6)
        if not r6 or not r6.get("result", {}).get("isError"):
            fails.append("probe5 net_probe should be denied by default\n%s"
                         % text6)
        elif "ROCQWASH_MCP_ALLOW_NET" not in text6:
            fails.append("probe5 denial should name ROCQWASH_MCP_ALLOW_NET\n%s"
                         % text6)

        # Probe 6: error faces
        r7 = _by_id(lines, 7)
        if not r7 or r7.get("error", {}).get("code") != -32601:
            fails.append("probe6a resources/list should be -32601")
        r8 = _by_id(lines, 8)
        if not r8 or r8.get("error", {}).get("code") != -32602:
            fails.append("probe6b unknown tool should be -32602")
        r9 = _by_id(lines, 9)
        if not r9 or r9.get("error", {}).get("code") != -32602:
            fails.append("probe6c unknown argument should be -32602")
        r10 = _by_id(lines, 10)
        if not r10 or r10.get("error", {}).get("code") != -32602:
            fails.append("probe6d array item starting with '-' should be "
                         "-32602")
        parse_errors = [l for l in lines
                        if l.get("error", {}).get("code") == -32700]
        if len(parse_errors) != 1 or parse_errors[0].get("id") is not None:
            fails.append("probe6e malformed line should be exactly one "
                         "-32700 with id null")

        if rc != 0:
            fails.append("server process should exit 0 on stdin EOF, got %d"
                         % rc)
        if err and "Traceback" in err:
            fails.append("server stderr carries a traceback\n%s" % err[-500:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T_MCP_FACE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-MCP-FACE SUITE SHELL PASS (6 probe groups, "
                     "%d capabilities, 3 live-call spot checks)\n"
                     % len(EXPECTED_TOOLS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
