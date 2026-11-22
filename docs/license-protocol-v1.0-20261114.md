# license-protocol: rocqwash usage and authorization protocol, v1.0 (issued November 14, 2026).
>
> **LicenseProtocolCard**: the usage and authorization protocol that accompanies the
> AGPL-3.0-or-later license of the rocqwash repository, v1.0 (issued November 14, 2026):
> what the tools do on the operator's behalf, what the operator authorizes, and the
> terms contributors accept. It does not replace the AGPL license; it operates within it.
>
> Purpose.  State, in one place and in plain language, the authorization surface of the
> rocqwash toolset: which actions the tools perform on repositories and continuous-
> integration systems, what credentials and scopes they require, the autonomy boundaries
> (budget caps, fail-loud rules), and the terms under which contributions are accepted.
>
> Interface.  This card binds three faces: (1) every tool under `tools/` and `wrapper/`
> and the MCP server face (`tools/mcp_server.py`), whose capability contract is
> `docs/CAPABILITY-INDEX.md`; (2) the repository workflow faces under
> `.github/workflows/`; (3) the contributor flow described in `CONTRIBUTING.md`.
> Where this card and the License differ, the License governs.
>
> Dependencies.  AGPL-3.0-or-later (`LICENSE`), `NOTICE`, `docs/CAPABILITY-INDEX.md`,
> `docs/contrib-isolation-protocol-v1.0-20261113.md`, the capability register
> (net-gated tools require `ROCQWASH_MCP_ALLOW_NET=1`).
>
> Evidence.  Grounded in the repository's own operating rules as landed: default-deny
> network gating for tools with a non-zero network face; budget-capped self-heal and
> auto-repair legs (one auto-retry per run, two repair rounds per branch, one backfill
> per cancelled run) with every outcome recorded in the experience ledger; fail-loud
> exit conventions across the toolset.
>
> Exit-codes.  Not applicable (documentation card); the exit-code semantics of every
> tool remain exactly as documented in each tool's own header; this card never alters them.

## 1. What the tools do on your behalf

rocqwash is a repository-hygiene and continuous-integration toolset. Its
faces read repositories and CI state, emit verdicts and reports, and; only
where the operator has enabled it; act: push with watching
(`pushci_status`), re-route failed jobs within budget caps
(self-heal legs), and apply mechanical, comment-surface-only repairs
(autofix legs) whose edit classes are desk-approved tables. Every acting
face is budget-capped and every outcome is appended to the in-repo
experience ledger with a fingerprint id, so an audit trail exists for any
autonomous action the tool ever took.

## 2. What the operator authorizes

The operator decides: (a) which repositories the tools point at; (b) which
credentials and scopes they run with (tokens are read from the operator's
own configuration, never embedded); (c) whether the network-facing tools
may reach the network at all (`ROCQWASH_MCP_ALLOW_NET=1` enables the
net-gated faces; the default is deny); (d) whether the acting faces are
wired into continuous integration at all. Granting write scopes to a
repository is the operator's explicit act; the toolset performs no
out-of-budget, out-of-scope, or unlogged write.

## 3. Autonomy boundaries

Three iron boundaries hold across all acting faces. First, budget caps:
auto-retry runs at most once per CI run and auto-repair at most twice per
branch per repair class; a backfill pass revives a cancelled run at most
once; caps are enforced from an on-disk state file the operator can read
and reset. Second, fail-loud: a watch or repair leg that itself breaks
shows red; a red verdict of the underlying CI is data, never an error the
tool hides. Third, edit-class whitelisting: auto-repair touches only the
comment-surface classes named in its approved tables; statement and proof
bodies are out of scope by construction.

## 4. Data, privacy, and the ledger

The experience ledger (`docs/exp-ledger.jsonl`) records tool actions and
verdicts. It contains repository names, run identifiers, and verdict
summaries; it must not be fed secrets (tokens are masked by the tools that
handle them, and masked reports are the artifact face). Operators who mirror
the ledger into public faces are responsible for reviewing it first.

## 5. Contributing

Contributions are accepted under AGPL-3.0-or-later, with the project's
Contributor License Agreement (`CLA/ICLA.md` for individuals,
`CLA/CCLA.md` for entities): by submitting a contribution, the contributor
grants copyright and patent rights to the Steward and all recipients,
authorizes dual licensing (alternative commercial terms), and states the
contribution contains the contributor's own substantive creative
authorship; artificial-intelligence systems act only as instruments
under the contributor's direction (human authorship). Contribution
isolation and review gates follow
`docs/contrib-isolation-protocol-v1.0-20261113.md`. Commercial licensing
for entities that cannot comply with the AGPL obligations follows
`CLA/commercial_license_template.md`.

## 6. No warranty

The toolset is provided under the AGPL-3.0 warranty and liability terms
(sections 15-17): "AS IS", without warranties of any kind, and to the
extent permitted by law no liability for damages arising from use:
including damages arising from autonomous actions the operator enabled.
The budget caps and audit ledger exist precisely so the operator can
bound and audit what the tools do before enabling them.


## 7. AI-assistance disclosure (standard form)

Contributions produced with AI agent assistance carry the following
disclosure in the pull-request description (three sentences, fixed
order; the bracketed parts are filled per change):

> AI-assistance disclosure (standard form): this change was produced
> through the project's own self-evolution pipeline; AI agents executed
> construction, verification, and assembly under the direction of the
> human engineer [name] ([steward / contributor]), who reviewed and
> accepted the results and takes full responsibility for the content.
> Substantive design decisions follow the workorder specification and
> the repository's canonical forms; boundaries and open items are
> registered in [section]. This statement is made under the NOTICE
> Authorship Statement and ICLA §5.2 (AI as instrument; human
> authorship).

Chinese mirror (for bilingual descriptions): the Chinese wording of the
disclosure above is preserved in the sibling `.zh.md` archive of this
file (section 7 there); use that wording when a bilingual pull-request
description needs the Chinese form.

Rules: (a) the human principal is named with their project role:
internal agent, work stream, or line labels are not part of the public
disclosure; (b) the responsibility sentence is effective only while the
contributor's ICLA (§5.2 included) is on file; file the ICLA before or
with the first merged contribution; (c) this section is the single
wording source for the disclosure; do not paraphrase it per pull
request.
