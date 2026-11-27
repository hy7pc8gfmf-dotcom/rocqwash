# rocqwash agent-session contract (docs/agent-contract.md)

> **AgentSessionContract**: the session-calling contract for any agent session
>   or scripted consumer of this repository: acquisition, tool-face groups,
>   execution laws, forbidden actions and escalation, the living self-check
>   vector, and the red-line pointer.
>
> Purpose.  Give a stranger session, on any platform, the complete calling
>   discipline for this repository's tool face in one file, with zero private
>   knowledge.
>
> Interface.  Documentation face. It cites the repository's own registered
>   faces (`bash tests/run_tests.sh`, `tools/mcp_server.py`, the `tools/*.py`
>   entry points, their MCP wrappers). Contract authority chain: `docs/mcp.md`,
>   then `docs/CAPABILITY-INDEX.md`, then the live `capability_index` face.
>
> Dependencies.  Python 3.9 or newer, standard library only (no pip, no
>   venv), Git. The red-line anchor is
>   `docs/ci-whitepaper-recursive-era-v1-20261116.md`; the repository root
>   carries no CONSTRAINTS.md.
>
> Evidence.  The commands of sections 1 and 5 ran end to end on November 28,
>   2026 at `origin/main` = `b822bb3`; outputs are recorded in the claim
>   thread of board item TB-3 (issue #161). The vector of section 5
>   reproduces mechanically on any checkout.
>
> Exit-codes.  None of its own. Cited commands keep their owning tool's exit
>   codes: 0 pass, 1 finding, 2 usage error, 9 missing input, 111 honest skip
>   when a toolchain tier is unconfigured.

## 1. Acquisition and readiness

**Whole repository (recommended default).**

```bash
git clone --depth 1 https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh    # exit 0 = the suite is green = the trust credential
```

The suite is pure standard library: zero pip, zero venv. A fresh clone that
reaches exit 0 needs nothing else installed.

**Single tool (light session).**

Fetch one file from the raw face and verify it is alive through its own
`--selftest`, in the same shape the README's bootstrap path uses:

```bash
curl -L https://raw.githubusercontent.com/hy7pc8gfmf-dotcom/rocqwash/main/tools/net_probe.py -o net_probe.py
python3 -I net_probe.py --selftest
```

The detached design lets every tool run independently of the whole tree; the
per-tool entry line in `docs/CAPABILITY-INDEX.md` together with a live
selftest pass is the credential for the single-tool path.

**MCP face.** Spawn the server locally and point any MCP client at it:

```bash
python tools/mcp_server.py    # stdio, newline-delimited JSON-RPC 2.0
```

After every pull of newer code, restart the server: the spec table loads at
startup, so an old process keeps presenting an old face. An existing
connection that is not restarted sees no change notification.

**Align before use.** Run `git pull --ff-only` at session start and again
before you integrate your work; after aligning, rerun the selftest before
consuming any face.

**Version bookkeeping.** Call the `repo_sync_status` face (or read the
version block of the server's initialize response) and record the HEAD sha
the session consumed. Every consumption leaves a version trace; an audit
replays the trace against the recorded sha.

## 2. Tool-face groups and when to use each

The groups below are the applicability map; membership is read live from the
`capability_index` face, never restated as a count in this file.

| Group | Use it when | Faces (representative, live roster governs) |
|---|---|---|
| A. Audit chain | any audit, survey, or verification scenario; highest priority | `net_probe` (the reachability gate run before any network work), `axiom_guard`, `axiom_sweep`, `axiom_audit`, `tree_audit`, `statement_probes`, `vacgen_generate` / `vacgen_coq_generate` (the probe-casting canon channel), `numeric_probe`, `anchor_guard`, `verify_vo` / `attest_join` / `frozen8` / `gate4_comment_guard`, `select_audit` |
| B. Tree and registration | changing the repository or adding a tool | `capability_index` (discovery; the first call of any new session), `doc_lint`, `registry_audit` / `registry_fix` / `registry_union` / `roster_resync`, `repo_sync_status`, `repair_scope` (CLI face) |
| C. Evolution and adjudication | self-evolution, experience-ledger, and gap scenarios | `exp_append` (the ledger-append canon), `gap_cluster`, `b_gate_audit` / `learning_feedback` / `evolution_dashboard` / `scheduler_lite`, `capability_ratchet`, `render_events` / `sentinel_status` / `claim_watch`, `ci_triage` / `pushci_status` / `red_dispatch_report` / `http_backoff` |
| D. Landing and evidence chain | publishing and reconciliation scenarios | `source_fetch` / `sweep_verdict` / `release_chain`, `baselinediff` / `ledger_sync` / `verdict_diff` / `row_render_check`, `termbase` / `jargon_plan` / `norm_lint` / `ai_flavor_detect` / `ai_flavor_apply_plan`, `netname_normalize` / `uplink_verify` / `symbiosis_status` / `symbiosis_bus_export` |
| E. Environment and thermal | environment smoke and any compile | `smoke` (environment smoke face); `cpu_guard` (CLI face: every compile goes through the thermal wrapper, never a bare compiler call) |

## 3. Execution laws

1. **MCP first.** In the audit, casting, watch, ledger, and survey scenarios,
   the in-session live call goes through the MCP face under its registered
   name; reaching the same tool's CLI for a live call in those scenarios
   violates this law.
2. **CLI exemption form.** `--selftest` runs and meta-verification faces are
   repository test contracts; running them through the CLI is legal and does
   not violate law 1.
3. **Non-applicable registration.** When the MCP server is unreachable, the
   response window is exceeded, or no registered face covers the target, the
   work record states the reason and the substitute form in a
   non-applicable-registration note. Silence is a violation.
4. **Fail loud.** A disk or state conflict stops the work and reports. No
   fabricated values, no downgrades. A red finding is data, not a tool
   failure; respect each tool's own exit-code semantics.
5. **Session-boundary upgrade.** Pull and upgrade only at a session boundary;
   after an upgrade, restart the MCP server and rerun the selftest. No hot
   upgrade inside a session.
6. **Write-face discipline.** Ledger appends and pushes carry actor and
   batch. Credentials stay local and never enter configuration. Landing is
   pull-request-only per the repository rules.
7. **Cross-engine tolerance.** Any assertion across engines (runner against
   development shell, CI against local) never uses an exact equality on
   engine-dependent values; the core and optional faces stay separated.
8. **Verdict consumption.** A CI verdict is consumed through the JSON
   verdict face with its exit-code contract, with UTF-8 I/O declared
   explicitly; workflow names are matched by prefix, not by exact label.

## 4. Forbidden actions and escalation

Forbidden: introducing a third-party dependency (the standard-library-only
red line); exposing a public MCP endpoint without authentication; hot
upgrade inside a session; deleting a check vector or trading a skip for a
green state; consuming a face while bypassing its self-check.

Escalation: a missing interface face, a statement-face change that needs
real edits, a repair exceeding its round cap, or a discipline-block
violation is reported as a loud failure with the blocker list. Carrying a
known defect into further work is forbidden.

## 5. Living self-check vector

This file carries no roster count anywhere. The roster number lives in
exactly one place (`SELFTEST_ROSTER_COUNT` in `tools/mcp_server.py`) and is
cross-checked by two independent faces; a consumer runs all three readings
and requires one number:

```bash
python3 -I tools/mcp_server.py --selftest
# word face: MCP-SERVER-SELFTEST PASS (roster N specs, name map complete, schema validation green)
python3 -I -B tests/t_mcp_face.py
# suite line: T-MCP-FACE SUITE SHELL PASS (probe groups, N capabilities, live-call spot checks)
python3 -I tools/capability_index.py --mode summary
# per-tool lines; the mcp-face column sums to the same roster N
```

**Red condition.** If the three readings disagree on N, the state is red:
stop consumption and reconcile before any further call. This is the
consumer-side form of the set-equality that `tests/t_mcp_face.py` asserts
internally. **Self-drift guard:** this file goes red by construction if a
count is ever written into it:

```bash
grep -nE "[0-9]+ (tools|capabilities|faces|specs)" docs/agent-contract.md
# expected: no hits. A hit means this file has started hard-coding a
# drifting count; remove the figure and cite the chain above instead.
```

## 6. Red-line pointer

The red-line anchor of this repository is
`docs/ci-whitepaper-recursive-era-v1-20261116.md`, with the failing-case
classification table `docs/ci-triage-table.json`. Where documents conflict,
the higher authority adjudicates: the standing charter
(`docs/recursive-improvement-charter-v1.0-20261127.md`) governs the rules,
the recursive-evolution whitepaper governs the method. The repository root
carries no CONSTRAINTS.md; the whitepaper pointer above is the anchor of
record.
