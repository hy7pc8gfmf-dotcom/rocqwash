# rocqwash MCP stdio server: protocol face and security face (docs/mcp.md)

> Purpose.  Usage and contract document for the rocqwash MCP stdio server (`tools/mcp_server.py`): the protocol face, the 31-capability schema table, startup, the security face, and the design SKIP face.
> Interface.  Document face. Describes the wire contract of `tools/mcp_server.py` (stdio transport, newline-delimited JSON-RPC 2.0, three methods) for any MCP-stdio caller; the underlying CLI true names and flag faces take `docs/CAPABILITY-INDEX.md` (the RQW06 contract surface) as the single authority.
> Dependencies.  `tools/mcp_server.py`, `docs/CAPABILITY-INDEX.md`, `docs/symbiosis_sop.md`, `docs/drafts/mcp-tool-specs-engine-body.md`, `tests/t_mcp_face.py`. No runtime dependency of its own (a document face).
> Evidence.  The version anchors below pin the transcribed capability names to measured HEADs (verified November 14, 2026); the measured runs in sections 7-8 record first-hand the active self-check PASS, the legacy handshake red, and the wording-instrument clean verdicts. The original Chinese text is preserved in the sibling `mcp.md.zh.md` archive.
> Exit-codes.  Not applicable to a document face; the rc values quoted in the text are the documented tools' observed exit codes, described as implemented.

Version anchor: pinned clone main at `4be42dedcade0cc0fe4b0da83ca1c82b7d4bbc75`, measured locally on November 14, 2026 (`git rev-parse HEAD`); the original 8 capability true names and call forms are transcribed line-by-line from `docs/CAPABILITY-INDEX.md` at that HEAD. Expansion anchor: working-tree HEAD `8e04cc6f9b6ee118e8e2729e9ae3edd6a163bf79` (measured locally on November 14, 2026); the 13 expansion capability true names and call forms are transcribed line-by-line from the INDEX section 2 entries at that HEAD, which does not yet contain this expansion batch's own commit (the self-referential integration form applies as before). The anchor line inside the INDEX records its own census-time HEAD (self-referential integration form; see the INDEX §0 caller duty).

Integration note (RQW08, November 14, 2026): this file landed in the same batch as `work.draft/mcp_server.py`; the protocol contract source is task instruction RQW08 section 0 (MCP stdio, newline-delimited JSON-RPC 2.0, three methods hand-written on the Python standard library, the zero-dependency law, net_probe/ci_triage/pushci_status denied by default, credential zero contact, ROCQWASH_HOME as the pinned base path).

## 1. Positioning

This file is the usage and contract document for the rocqwash MCP stdio server (`mcp_server.py`): the protocol face, the 31-capability schema table, startup, the security face, and the design SKIP face. Any MCP-stdio caller (a session, a subagent, an automation task) calls the 31 capabilities with zero path knowledge; the underlying CLI true names and flag faces take `docs/CAPABILITY-INDEX.md` (the RQW06 contract surface) as the single authority.

The MCP roster-expansion work stream 1 (the M1 ticket, at integration; baseline `c48a548a`) adds 6 further read/plan capabilities (termbase / verdict_diff / learning_feedback / b_gate_audit read; evolution_dashboard / gap_cluster plan), each transcribed from its `docs/CAPABILITY-INDEX.md` section 2 entry line per the roster survey table 2 rows 1-6 (five of the six entries already stood in the INDEX at the baseline; the `gap_cluster` entry lands with this same increment); additive again (the 25 existing specs and their schemas untouched); `tools/list` now carries **31 tools**. All six are zero-network faces and carry no gate. The layer law holds face by face: zero apply face, zero ledger-append face, zero credential face; the two plan faces write only caller-named output files (`evolution_dashboard` `--json-out`/`--md-out`, `gap_cluster` `--out`), and the two account faces (`learning_feedback`, `b_gate_audit`) declare their single fixed derived-report writes (`docs/scheduling-feedback.json`, `docs/b-gate-audit.json`) with their three inputs strictly read-only.

The symbiosis batch (the symbiosis ticket, spec section 1.1; the tool count was synced into this record on November 16, 2026) adds 1 further read-only capability, `symbiosis_status` (a `capability_index`-style file face over `docs/symbiosis_sop.md`; zero network, no subprocess, no side effects; at its integration `tools/list` carried **25 tools**); additive (the 24 then-existing specs and their schemas untouched).

The engine-body batch (the engine-body ticket, at integration) adds 3 further zero-network capabilities (ai_flavor_detect / jargon_plan / i18n_pipeline_dryrun), graduated from docs/drafts/mcp-tool-specs-engine-body.md (the lane-8 draft) by the integration agent; additive again (the 21 existing specs and schemas untouched); the ticket's only network face (the i18n http provider leg) is outside the batch and stays default-deny, neither registered nor gated.
Beyond the original 8 capabilities (the RQW08 integration), the RQW13 batch 1 adds 13 zero-network capabilities, each transcribed from its INDEX section 2 entry line; `baseline_diff` was already on this face under the name `baselinediff` and is not registered twice. The expansion is additive: the 8 existing specs and their schemas are untouched; the server only gains the array argument type and per-item `-` prefix validation, leaving existing call forms unchanged.

## 2. Protocol face

- **Transport**: line-delimited JSON over stdio. Exactly one JSON-RPC 2.0 object per line, UTF-8; responses are written to stdout line by line and flushed. Diagnostics and the ready log go to stderr only. stdin EOF exits the process with code 0.

**Methods**:

| Method | Kind | Request params | Response | Notes |
|---|---|---|---|---|
| initialize | request | `protocolVersion`, `capabilities`, `clientInfo` | `protocolVersion` (echoes the value the client reports; default `2024-11-05`), `capabilities.tools={listChanged:false}`, `serverInfo={name:"rocqwash-mcp",version}` | single capability face = tools |
| notifications/initialized | notification | none | no response (consumed silently; one diagnostic line on stderr) | JSON-RPC notifications get no reply |
| tools/list | request | none | `tools`: 31 entries, each carrying `name` / `description` / `inputSchema` (object, closed property set, additionalProperties:false) | the listing is static, no pagination cursor |
| tools/call | request | `name`, `arguments` | `content[0].text` + `isError` | execution-level failures return an `isError:true` result, not a protocol error |

**Error codes**:

| Code | Meaning | Raised when |
|---|---|---|
| -32700 | Parse error | the line is not valid JSON or not valid UTF-8 (id=null; the loop continues, no exit) |
| -32600 | Invalid request | the line is not an object, lacks `method`, or `method` is not a string |
| -32601 | Method not found | any request method outside the three methods |
| -32602 | Invalid params | unknown tool, malformed `params.name`, schema validation failure (missing required / wrong type / unknown key / value starting with `-`) |
| -32603 | Internal error | unexpected server exception (traced on stderr; the loop continues) |

- **Stream discipline**: stdout carries protocol response lines only; child stdout/stderr are captured (`subprocess.PIPE`) and never merged into the protocol stream. Empty lines are skipped; a malformed line gets `-32700` and the loop keeps serving.

## 3. Tool schema table

The original 8 capabilities are listed in the order the RQW08 ticket names them; the 13 RQW13 expansion capabilities are appended at the table tail in the expansion ticket's order; the engine-body batch's 3 capabilities follow (graduated from the lane-8 draft, wired at integration); the symbiosis ticket's `symbiosis_status` closes the pre-expansion table (spec section 1.1, a `capability_index`-style file read face); the MCP roster-expansion work stream 1's 6 capabilities (the M1 ticket) follow and close the table now, each transcribed from its INDEX section 2 entry line (survey table 2 rows 1-6). Underlying entry true names are transcribed from INDEX section 2; boolean `true` = the flag is appended, `false` = omitted; `*` = required; value flags pass `--flag value`; array arguments expand element by element (positional arrays continue in order, the argparse `nargs="*"` face; flag arrays repeat `--flag value` per element, the argparse `action="append"` face); argument values must not start with `-` (guarding against sub-CLI flag injection; array items are checked the same way).

| Capability | Underlying entry (INDEX true form) | Arguments (schema properties; * = required) | Security face |
|---|---|---|---|
| sentinel_status | `tools/cw_sentinel.py --once` | watch_repo, branch, state_file, timeout, sleep_scale | default deny (network face) |
| net_probe | `tools/net_probe.py` | endpoints, rounds, interval, stable_window, seed | default deny (network face) |
| baselinediff | `tools/baseline_diff.py OLD NEW` | old*, new*, json_out, md_out | allow |
| ci_triage | `tools/ci_triage.py` | repo, run, logs, offline, timeout, retry_max | default deny (network face) |
| vacgen_generate | `tools/vacgen.py` | input, out, toolchain, snapshot, audit_id, name, worktree, lake, core, force, preflight_all | allow (compile leg design SKIP) |
| exp_append | `tools/exp_port.py append` | tool*, points*, evidence, batch | allow (CLI in tree, idempotent seen set) |
| pushci_status | `tools/pushci.py` | repo_path, branch, base_ref, dry_run, watch_interval, watch_max_rounds, timeout | default deny (network + remote write face) |
| capability_index | `docs/CAPABILITY-INDEX.md` (file read, not a CLI) | none | allow |
| chain_graph | `tools/chain_graph.py LEDGERS...` | ledgers* (array, positional), json_out, md_out, top | allow |
| doc_lint | `tools/doc_lint.py` | repo, json_out, help_cap | allow (help runs read-only) |
| ledger_sync | `tools/ledger_sync.py` | probe, ledger, out, report, policy | allow |
| netname_normalize | `tools/netname_normalize.py` | dir, apply, map, json_out | allow (apply = local rename write face, limited to `--dir`) |
| norm_lint | `tools/norm_lint.py` | tree, file, jargon_map, cjk_threshold, cjk_whitelist, json_out, md_out, selftest | allow (report mode first) |
| render_events | `tools/render_events.py` | events, dir, md_out, json_out, top | allow |
| select_audit | `tools/select_audit.py` | order, select* (array, repeated-flag face), grep, requires, world, json_out | allow |
| registry_audit | `tools/registry_audit.py` | order, project, git, ref, git_path_order, git_path_project, live_src, anchor_src, fix_plan, json_out, md_out | allow (local git read-only) |
| registry_fix | `tools/registry_fix.py` | audit_json, order, project, anchor_src, apply, work_dir, audit_tool, json_out | allow (dry run by default; apply bounded by staged assertions + rollback) |
| registry_regen | `tools/registry_regen.py` | base_repo, base_ref, contrib_repo, contrib_ref, pieces, anchor_src, dep_source, seq, base_path_order, base_path_project, contrib_path_order, contrib_path_project, out, apply, json_out | allow (dry run by default; apply requires an explicit out) |
| registry_union | `tools/registry_union.py` | base, main, branch, git, ref_base, ref_main, ref_branch, git_path, kind, reanchor, anchor_src, out, apply, json_out | allow (dry run by default) |
| abl1_4b_compile | `tools/_abl1_4b_compile.py EXTRACT_DIR [DRIVER.ML]` | extract_dir* (positional), driver (positional) | allow (OCaml toolchain design SKIP face) |
| http_backoff | `tools/_http_backoff.py --selftest` | none | allow (pure-function selftest face) |
| ai_flavor_detect | `tools/ai_flavor.py` | file, tree, json_out, selftest | allow (zero network, zero writes in report mode) |
| jargon_plan | `tools/jargon_apply.py --plan` | file, tree, json_out | allow (plan writes nothing by default; the apply face is not exposed) |
| i18n_pipeline_dryrun | `tools/i18n_pipeline.py --stage p0\|p1` | manifest*, stage, json_out | allow (stage limited to the p0/p1 dry-run face; the p3/p6 write faces are not exposed) |
| symbiosis_status | `docs/symbiosis_sop.md` (file read, not a CLI) | none | allow (zero network, no subprocess, no side effects; a `capability_index`-style read-only face) |
| termbase | `tools/termbase.py --lookup TERM` | lookup, schema_check, selftest, db, json_out | allow (read-only lookup over the seed; the only outputs are stdout and the caller-named `--json` report) |
| verdict_diff | `tools/verdict_diff.py --results-lane GLOB` | results_lane*, expected, batches, baseline, json_out, md_out | allow (caller-named outputs only; the tool's pre-argparse `--selftest` route is not exposed, the registered `chain_graph` precedent) |
| learning_feedback | `tools/learning_feedback.py` | selftest | allow (the three standing ledgers read strictly read-only; the default run regenerates one derived report `docs/scheduling-feedback.json`; `--selftest` is zero repository paths) |
| b_gate_audit | `tools/b_gate_audit.py` | selftest | allow (round records read strictly read-only; the default run writes the derived audit report `docs/b-gate-audit.json`; `--selftest` is offline on temporary files) |
| evolution_dashboard | `tools/evolution_dashboard.py` | repo, exp_ledger, rounds, reports (array, repeated-flag face), json_out, md_out, stdout, selftest | allow (plan face: stdout by default, writes only the caller-named `--json-out`/`--md-out`; absent accounts are data) |
| gap_cluster | `tools/gap_cluster.py` | ledger (array, repeated-flag face), reports (array, repeated-flag face), out, json | allow (plan face: aggregation is a pure function of the input bytes; the only write is the caller-named gap ledger `--out`; `--json` prints to stdout) |

Table notes:

1. **Unexposed flags**: credential-shaped, injection, and test-hook flags (`--netrc`, `--injector`, `--git-caller`) are deliberately not exposed; remote mutation flags (`--merge`, `--pr`) are not exposed; the full flag face stays with the INDEX entry lines, and callers needing it use the CLI directly. Same law for the expansion batch: the opt-in `--orphan-add` face of `registry_fix` is not exposed (absent from the INDEX entry line transcribed at expansion time; the entry's Pos/Opt of 0/8 agrees), and the pre-argparse `--selftest` route of `chain_graph` is not exposed for the same reason (a doc-versus-argparse divergence of the same shape as the registered `net_probe` `--selftest` divergence).
2. **Local write faces**: four expansion capabilities carry local write flags (`netname_normalize --apply`, `registry_fix --apply`, `registry_regen --apply`, `registry_union --apply`); all dry run by default and their write faces stay inside the CLI's own assertion machinery (registry_fix applies staged in-memory assertions with rollback; registry_regen writes only under an explicit `--out`). None is gated: zero network face per the INDEX section 1 reading, caller duty rides with the underlying CLI.
3. **Child execution form**: children spawn as `[sys.executable, <cli>, ...]` with `cwd=ROCQWASH_HOME` and the parent environment passed through; call forms match the INDEX entry lines (`python tools/<name>.py ...`).
4. **Result shape**: text results carry an `exit code: <rc>` header line; child stderr is prefixed `[stderr]`; any non-zero rc yields `isError:true` (fail-loud).
5. **Batch-2 register (pending execution, not registered)**: of the 27 INDEX entries, the original 8 capabilities cover 6 true names (`cw_sentinel` / `net_probe` / `baseline_diff` / `ci_triage` / `vacgen` / `pushci`), this batch's 13 cover 13 more, and `baseline_diff` is covered by `baselinediff`; 8 true names remain unregistered (`_gen_fin_mac` / `contrib_intake` / `cw_doctor` / `evolve` / `red_dispatch` / `toolchain_dyld_doctor` / `unclog` / `wash_shape`). The ticket's "five network-or-heavy candidates await batch 2" reads, from the INDEX faces, as `contrib_intake` (git clone word face) / `unclog` (Coq compile clearing loops, heavy) / `wash_shape` (multi-round reshaping pipeline) / `evolve` (in-repo git commit face) / `cw_doctor` (multi-domain rollup probes); the other three (`red_dispatch`, `toolchain_dyld_doctor`, `_gen_fin_mac`) are outside the ticket's five and await their own lane decision. The five-name composition is this agent's INDEX-face reading; the ticket does not name them, and the batch-2 ticket governs at registration time.
   **Supersede note (the M1 ticket, November 21, 2026)**: this register was written against the census-27 face; the roster survey of November 20, 2026 (`D:/ComplexAnalysis/attn/_rqw_mcp_regen_20261120/roster-survey.md`, tree-59 face at HEAD `0765d671`) supersedes its candidate composition with 35 candidates in survey table 2, keeping the register's five network-or-heavy readings as input rows of that table. The MCP roster-expansion work stream 1 (this ticket) registers survey table 2 rows 1-6 (termbase / verdict_diff / learning_feedback / b_gate_audit / evolution_dashboard / gap_cluster); none of the six appears in the register's 8-name list above (all six postdate the census-27 scope), so no register row is struck; the register's remaining names stay pending their own tickets under the survey's face adjudications.

## 4. Startup

**Command**: `python -I mcp_server.py` (stdio transport; isolated mode).

**Env table**:

| Variable | Meaning | Default |
|---|---|---|
| ROCQWASH_HOME | the rocqwash repository root; required by tools/call; fail-loud when unset (silent guessing forbidden) | none (no path guessing) |
| ROCQWASH_MCP_ALLOW_NET | only the value `1` enables the four default-deny capabilities | unset = deny |
| ROCQWASH_MCP_TIMEOUT | hard timeout per tool call (seconds); on timeout the child is killed and a failed result is reported | 300 |

Measured environment: Python 3.13.2 (Windows 10, Git Bash); lower versions untested.

**Minimal session example** (three request lines, two response lines; notifications get no reply):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"capability_index","arguments":{}}}
```

## 5. Security face

1. Default deny: `net_probe` / `ci_triage` / `pushci_status` (the three the integration ticket names) plus `sentinel_status` (a strengthening cast by this integration) return a failed tool result (`isError:true`) naming `ROCQWASH_MCP_ALLOW_NET=1`; a denial is an execution-level result, not a protocol error; only the explicit environment opt-in enables them.
   **Registration note** (a strengthening beyond the ticket's minimal list, additive): the ticket names three; this integration also gates `sentinel_status` because INDEX §1 records a non-zero network word face for `tools/cw_sentinel.py` (http.client, socket, urllib.request) and its SKIP face requires a network window. Strengthening, not weakening; reverting to the verbatim three-name face is a one-line change (set `sentinel_status`'s `net_gated` to `False` in `TOOL_SPECS`).
2. Credential zero contact: the server reads no credential store, no token file, no netrc path, and exposes no credential-shaped argument; the child environment passes through unchanged and credential handling stays with the underlying CLIs. The only credential wording in the server source is the negation statement of this very face (`mcp_server.py:30-32`); the credential value-shape grep is 0 hits.
3. Subprocess isolation: child streams are captured; the protocol stream stays clean; the child runs with `cwd=ROCQWASH_HOME`; a hard timeout kills runaway children; arguments pass as an argv list (no shell, no string-concatenation injection face) and string values must not start with `-`.
4. Zero transport import face: the server itself imports `json`, `os`, `subprocess`, `sys` only; no socket/urllib/http face; the server body is zero-network.
5. Expansion batch adds no gated face: the 13 expansion capabilities all read zero-network under the INDEX section 1 word-face reading (three-channel zero hits, or local git reads only) and carry no `ROCQWASH_MCP_ALLOW_NET` gate; their local write faces stay inside the underlying CLIs' dry-run defaults and assertion/rollback machinery (section 3 table note 2). The server hard timeout and the no-leading-dash argument validation (array items checked the same way) apply to all 31 capabilities equally (the engine-body three follow the same law: zero network, no gate; the symbiosis batch's symbiosis_status is a file-read face with no subprocess and no flags, ungated likewise; the roster-expansion work stream's six are ungated on the same zero-network word-face reading: the two plan faces write only caller-named output files, and the two account faces declare their single fixed derived-report writes in the section 3 table, with their three inputs strictly read-only).

## 6. Design SKIP face

- **exp_append**: `tools/exp_port.py` is in place (the experience-bus A1 face, schema rocqwash-exp/1: the tool/points/evidence/batch four-field face, JSONL append into `docs/exp-ledger.jsonl`, idempotent seen set: a duplicate returns the existing id and writes nothing); the pre-integration not-found existence-probe form is retired. The registered argument face was re-verified against the integrated CLI.
- **vacgen_generate compile leg**: the zero-compile casting face runs anywhere; the compile verification leg needs a Lean toolchain (design SKIP face per INDEX §3.3) and stays SKIP when lake is absent.
- **Unimplemented MCP faces**: resources/prompts/completions/logging/ping/batching and the SSE transport are not implemented (unknown methods get `-32601`); `tools/listChanged` stays false; capabilities advertise the tools face only.
- **capability_index anchor**: the INDEX text is returned live from disk; its internal anchor line advances with the repo (caller duty per INDEX §0); the server neither caches nor rewrites it.
- **abl1_4b_compile toolchain leg**: the registration face lists with zero network, but the compile body needs an OCaml toolchain; with `ocamlc`/`ocamldep` absent the CLI exits loudly (INDEX entry SKIP face), surfacing over MCP as a non-zero `exit code` with `isError:true`, an execution-level result, not a protocol error.
- **The registry family targets serviced books**: `registry_audit` / `registry_fix` / `registry_regen` / `registry_union` target book repositories carrying `order.txt`/`_CoqProject`; on a repository without a registry (this repo), `registry_audit` measured rc=9 REGISTERED fail-loud (INDEX section 4.1 light-probe ledger), an execution-level result, not a tool fault.
- **http_backoff single-face exposure**: the tool has no argparse (usage-string face); MCP exposes the single `--selftest` call; its other face is module import (consumed by ci_triage, cw_sentinel and pushci) and does not go through MCP.

## 7. Self-check

**Active self-check**: `python -I -B tests/t_mcp_face.py` (the in-repo `tests/` face; landed with the RQW13 expansion batch). The test spawns `tools/mcp_server.py` as a subprocess (stdio) and asserts line by line in a single session: (1) initialize echoes protocolVersion plus serverInfo; (2) notifications/initialized is consumed silently with no reply; (3) tools/list carries exactly 31 tools, the name list matching the table verbatim (original 8 + expansion 13 + engine-body 3 + symbiosis 1 + the M1 roster-expansion 6), each with a description and a closed-property inputSchema; (4) at least 3 live-call spot checks (http_backoff `--selftest` rc=0, norm_lint `--selftest` rc=0, chain_graph `--selftest` rc=0, plus the chain_graph temporary-fixture dual-ledger array positional path rc=0); (5) the default-deny negative sample (net_probe refuses with isError:true naming `ROCQWASH_MCP_ALLOW_NET`); (6) the three error faces `-32601` / `-32602` (unknown tool + unknown argument on a new tool + rejected array negative item) / `-32700`. The whole run is zero-network (the live calls touch only selftest faces and temporary fixtures).

Roster note: this test is not on the `tests/run_tests.sh` roster (following the A1 agent's `tests/t_exp_port.py` precedent: the roster count is mechanically coupled to the README.md count line, the `README*` faces are zero-touch for this lane, and roster insertion rights belong to the lane holding README authorization). A standalone direct run is the complete self-check.

**Legacy handshake of record (RQW08 era)**: `python -I handshake.py` (RQW08 working directory `_rqw08_mcp_20261114/`; three probe calls asserting tools/list carries exactly 8 tools). After the expansion batch its probe 3 turns red as expected (the 8-tool face was superseded by the 21-tool face), the remaining probes stay green; the tool is kept as a snapshot of the RQW08 integration point, and the active self-check is the t_mcp_face paragraph above. Measured below.

Measured (November 14, 2026, first-hand run):

```text
python -I -B tests/t_mcp_face.py   -> T-MCP-FACE SUITE SHELL PASS (6 probe groups, 24 capabilities, 3 live-call spot checks)  exit 0
python -I handshake.py (RQW08 ws)  -> HANDSHAKE RED: 2 failed assertions (probe 2 "exactly 8 tools :: got 21" and "names match the 8-capability contract :: missing=[] extra=<exactly the 13 new names>"); the remaining probes (inputSchema face / capability_index / default deny / -32601 / -32602 / -32700) all PASS; exit 1
```

(Measured on November 14, 2026, first-hand run; the legacy tool's two reds are the expected post-expansion mismatch shape, not a fault.)

Measured addendum (November 16, 2026, first-hand run, the current tree after the symbiosis batch count sync):

```text
python -I -B tests/t_mcp_face.py   -> T-MCP-FACE SUITE SHELL PASS (6 probe groups, 25 capabilities, 3 live-call spot checks)  exit 0
```

## 8. Register self-check

Instrument = `ai_flavor_selfcheck.sh` (a 36-word-face battery plus an em-dash U+2014 battery; instrument copy at `D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh`, the same instrument as the census). Measured output (at close of work):

```text
mcp_server.py   : CH_3FAMILIES_10FACES lines=0 / EN_WORD_STEMS_15FACES lines=0 / EN_SENTENCE_8FACES lines=0 / EN_PARA_INITIAL_3FACES lines=0 / EM_DASH_U2014 count=0 (target 0) / TOTAL_WORDING_LINES=0 / VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
docs/mcp.md     : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
t_mcp_face.py   : VERDICT CLEAN (36 faces = 0; em-dash = 0)  rc=0
```

Credential-face check (value-shape regex pass over the three deliverables): 0 hits; the wording in `mcp_server.py:34-36` is the negation prose of section 5 item 2, not credential values.

**Em-dash settlement note**: before the expansion, the working-tree mcp.md section 6 exp_append lines carried two U+2014 hits left by the uncommitted A1 integration; that batch settled those together with its own additions (five in total, replaced by colon or comma, zero semantic change) and the re-measured count is zero on all three deliverables.

## 9. Reconnect note (RQW13 expansion batch, the user reconnect face)

Current: the user-level MCP config (`~/.zcode/cli/config.json`, key `mcp/servers/rocqwash`) spawns `python.exe -I D:/ComplexAnalysis/rocqwash/tools/mcp_server.py` with `ROCQWASH_HOME=D:/ComplexAnalysis/rocqwash` and `ROCQWASH_MCP_ALLOW_NET=1`; the server runs against this live tree, and a connected client currently sees 8 tools (sentinel_status / net_probe / baselinediff / ci_triage / vacgen_generate / exp_append / pushci_status / capability_index). After the client restarts this stdio server and reconnects, `tools/list` shows 31 tools (the RQW13 batch's 13 names per the section 3 table, the engine-body ticket's ai_flavor_detect / jargon_plan / i18n_pipeline_dryrun, landed at integration, the symbiosis ticket's symbiosis_status per its spec section 1.1, plus the MCP roster-expansion work stream 1's six names termbase / verdict_diff / learning_feedback / b_gate_audit / evolution_dashboard / gap_cluster). An existing connection that is not restarted keeps the old face (the listing is static, `listChanged:false`, no change notifications). Acceptance anchors: the expansion ticket's "after restart and reconnect the MCP tool count covers the new batch" plus "handshake and one live call per new tool, spot checked".
