# Recursive Evolution Technical Whitepaper v1.0 (RE-WP-v1.0), documented November 21, 2026.

> Purpose.  The methodology canon of recursive evolution: it states how the recursive chain is built, how it turns, how it self-corrects, and how it advances safely. Source: the rocqwash recursive chain of November 19-21, 2026, distilled from the nine-run effort (the four-P0 package + the meta-verification layer + the three gaps + R18 + work streams 1/2 end to end). The original Chinese text is preserved in the sibling `.zh.md` archive.
> Interface.  Document face; no runtime interface. Section map: section 0 states the definition and the three necessary conditions; sections 1-3 state the seven laws, the seven pillars and the layer-tier invariants; sections 4-6 state the meta-layer exposure curve, the repair-round autopsy law and the recursive-output format; section 7 records the November 19-21, 2026 chain as a live walk-through. Every round's wrap-up scroll must carry the recursive-output block of section 6.
> Dependencies.  Companion faces and skills cited read-only: the execution-level SOP skill `cw-recursive-sop` (the condensed operations face); the CI whitepaper `ci-whitepaper-recursive-era-v1-*.md` (CI failing-case classification); the triage table `docs/ci-triage-table.json`; the provenance-v2 contract `docs/pin-provenance-v2.md`. No runtime dependency.
> Evidence.  Every claim anchors on the recorded chain of section 7, whose leaps cite their commit SHAs (3f781a1, 6998c40, 3a56b854, 0765d671, c48a548a, 13cefb0, a07403e3); the precedents inside sections 1-5 name their source packages and rule-institution dates; the version-history table pins the v1.0 scope. No selftest: document face.
> Exit-codes.  Not applicable to a document face; the rc values quoted in the body (rc=0, rc=49, fail=N) are observed outputs of the named tools, described as implemented.

---

## 0. The definition of recursive evolution

**Recursive evolution = a system improving its own verification net, repairing its own failing cases, and extending its own capability faces while running, and writing each round's experience and precedents back into its own canon (whitepaper / triage table / experience cards), so that the next round starts higher than the last.**

Three necessary conditions (missing any one degrades it into ordinary automation):
1. **The meta-verification layer**: a verifier of verifiers exists (it enumerates every tool's selftest face and fails loudly); without it, failures hide in observation blind spots and never surface;
2. **Self-adjudication of the recursive chain**: after each round wraps up, the next round is re-cast automatically (no waiting for orders), and the adjudication boundary is drawn in plain text by the layer law;
3. **Experience written back into the canon**: each round's lessons / precedents / prescriptions must be written, in the same round, into the whitepaper + the triage table + the experience cards; unwritten, the next round's starting point does not rise.

---

## 1. The seven laws of the recursive chain

| Law | Content |
|---|---|
| **1 Completion-continuation law** | Any ticket wrapping up → execution record written to disk → ledger updated → **the next ticket is taken automatically; stopping is forbidden**; "finish one and stop" violates the law |
| **2 Escalation-interception law** | Five interception classes suspend and wrap up the run automatically: (1) code-class tree writes (2) budget over cap (3) hard network failures x3 (4) semantic ambiguity (5) exceeding the queue's authorized scope. Suspension = an honest wrap-up, not a malfunction |
| **3 Cap law** | The per-run recursion cap (usually 4-8 tickets); an emptied queue = a normal wrap-up; a full cap = the execution record registers the remaining queue and the standing authorization continues the loop automatically |
| **4 Wrap-up-record law** | Whatever ends the round, the wrap-up scroll must come out: this round's per-ticket ledger / next-round candidates / pending-execution state / escalated items |
| **5 Return law** | Each ticket's experience enters the exp card → the return package's pre-cast pieces accumulate per ticket (the three-way union discipline) |
| **6 Watch law** | After wrap-up, the standing watcher may continue optionally, independent of the driver |
| **7 Self-continuation law** | Wrap-up ≠ shutdown: the wrap-up scroll is persisted to disk → the driver session re-casts the next round automatically per STANDING-ROLE → the loop repeats. Shutdown is limited to three classes |

## 2. The seven pillars of the recursive chain (the methodology skeleton)

### Pillar 1 - the contract-first parallel method

Before multi-agent parallel construction starts, the interfaces are frozen first on contract faces (data / `contract-*.md`, CLI signatures, exit codes, output schemas, file caps, all written down); agents never wait on each other and zero files overlap, and the test agent casts the not-yet-readable half-products strictly against the contracts.

- Benefit: zero conflicts between parallel agents; an interface change is a contract version bump, never an improvisation; the test agent can cast first.
- Precedent source: the package-12 three-gap closure ran eight agents (eight contract faces such as `contract-pin-repair.md` were frozen first → eight agents in parallel with zero conflicts).

### Pillar 2 - the multi-run lineage (failure → adjudication → fix → follow-up run)

A ticket is not one run; it is a **lineage**: first run → honest escalation → adjudication → fix → follow-up run → ... → wrap-up all passing. Each failing result is not a failure; it is the signal that the check/agent discipline caught a real problem.

- Lineage record format: run number → root cause → adjudication → fix.
- Typical nine-run lineage (the four-P0 package): first run B1 escalates honestly → second run adjudicates and closes out the patch → third run three meta-layer failures → ... → ninth run CI FULL all passing.
- **Five escalation channels** (escalation = suspended pending adjudication; carrying a defect into further work is forbidden): (1) code-class tree writes (2) budget over cap (3) hard network failures x3 (4) semantic ambiguity (5) exceeding the authorized scope.

### Pillar 3 - the meta-verification layer (the verifier of verifiers)

A meta-test (`tests/test_tool_selftests.py`) enumerates every tool's `--selftest` face and folds every tool's self-attestation into one net: failing / missing / unregistered exemption → fail-loud with the names listed.

- **Value curve**: build the net → expose the standing failures → close each one with a machine test. The meta layer's first day caught the real symbiosis TMP failure, the G1 hang, the V18 false positive and the three-failure close-out: **a failing result is not a regression; it is the signal of an observation blind spot closing**.
- **Discipline**: the meta layer's own failures must be answered too (building the net without repairing the failures it exposes does not count); the meta layer's timeout criterion needs load resilience (one retry, two consecutive hits before failing: the 120 s cap false-positives under load).

### Pillar 4 - failure output must surface (observability)

The output of a failing case **must not be swallowed by a truncation window**: `run_tests.sh` prints **the first 40 lines plus the last 20 lines** on failure; the meta-test prints the **fail-first summary line** (failures listed first, line-level details after).

- Precedent: the Linux meta-layer failing case: the failing lines all sat in the late alphabetical segment and were swallowed by the first-40 truncation; after the tail-20-lines rule landed, one rerun fished out the real symbiosis TMP failure.
- **Audit quote**: "failure output that cannot be observed" ranks as a verification-surface defect on the same level as a "spurious pass".
- **The counting-caliber face (the same law on the success face; cast November 21, 2026, source: the audit requirement annex v2, supplements 3 and 4)**: a census count never leaves bare; every counting field carries its basis annotation (live example: `"lines": {"value": N, "basis": "LF-terminated lines, binary read"}`), and the output carries the top-level `scan_face` field (scanned / not_scanned / "a negative finding of this scan, not an absolute claim" / equivalents not exhaustive). This is the citability difference against ecosystem bare outputs: a reader of the count also receives the scan boundary.
- **The implemented counter family is the v2 minimum set** (the census face the audit line's work streams one and two ran, its regex set field-validated): files / bytes / lines / nonEmptyLines / thm (`theorem|lemma`) / defFam (`def|abbrev|structure|class|instance|inductive`) / the unsound-feature sweep (sorry, sorryAx, axiom, opaque, native_decide, unsafe, implemented_by, extern, ofReduceBool) / comment faces / per-directory / largest-10 / zero-declaration / import-roots; relative to the repo tool's flat `decls` family (`theorem|lemma|def|instance|abbrev` combined), the thm/defFam split and nonEmptyLines are the two additions.

### Pillar 5 - double-blind mutual corroboration (two independent diagnoses converging)

The same root cause is finally established independently by two diagnostic paths that know nothing of each other; two paths converging on one conclusion = the root cause is confirmed beyond doubt.

- Precedent: the R18 failing case: the MCP adjudication agent and the desk repair agent diagnosed independently, and both converged on "59ef077 re-signed against the wrong target f390121c".
- Value: a single diagnosis can be wrong (noise / blind spots); two independent converging diagnoses multiply the error rate down.

### Pillar 6 - the cap cross-check

Each agent's declared cap (the file-count cap) versus the actual `git diff` file set: **over cap = blocker** (the new law instituted after the package-15 E1 agent over-cap precedent). The reviewing agent cross-checks each agent against the declared caps, preventing an agent from widening its own range.

### Pillar 7 - the standing charter of the self-continuation loop

The STANDING-ROLE standing charter = the driver session's **canonical loop-execution form**: after each round's wrap-up the next round is re-cast automatically; shutdown is limited to three classes (the five escalation classes / the user explicitly stopping / an empty queue plus two rounds of zero census growth).

- Canonical form: `data/STANDING-ROLE.md` (the B1-package precedent illuminated the origin: the root cause of "run one ticket and stop" was the wrap-up design that waits for orders → the self-continuation revision abolished the wait-for-orders design).

## 3. The invariants of the recursive chain (the three-tier layer law: the premise of parallel safety)

| Tier | Rule | Parallel safety |
|---|---|---|
| Data tier | automatic (class B: round admissions / calibration readings) | ✅ safe for multiple executors (ledger appends go through the retry loop) |
| Code tier | gated (self-adjudication limited to mechanically decidable items; semantic ambiguity / over-scope escalates) | ⚠️ PR + review check (multiple executors merge through PRs) |
| Constitution tier | never automatic (zero reach) | N/A |

**The five parallel-safety rules** (the conflict points of multiple executors and their guardrails):

| # | Conflict point | Guardrail |
|---|---|---|
| 1 | dropped-row race on ledger appends | every appender goes through the "read head → replay rows → re-read on PATCH failure" loop |
| 2 | double counting on the B check | the actor field plus a deduplication key (the class's semantic content fingerprint) |
| 3 | colliding writes to the plan state file | each executor keeps its own plan state file (actor namespace) |
| 4 | double repair of one ticket | the claim system: the PR title is the claim (`[actor] topic date`); a title collision stops the work at once |
| 5 | the canonical-only tier | plan-only by default (a non-canonical executor structurally cannot do it; a declared skip is not a forgery) |

## 4. The exposure-period curve of the meta-verification layer

```
Before the net: failures hide in observation blind spots (the four-P0 cases crossed 84 commits untouched; invisible under the cap; the rc=49 stub family had no solver)
   ↓ build the net
Exposure period: the meta layer's first run reports fail=N (all standing failures surface: the G1 hang, the V18 false positive, the symbiosis TMP, the three-failure close-out)
   ↓ close each with a machine test
Steady state: the meta layer all passing; a new failure = a regression signal; caught and repaired at once
```

**Audit quote**: "the problem surface converged from '4 P0 + drift' to 'meta-test fail=2 + mcp hang', significantly narrower and far more machine-testable." This is exactly the meta layer's value curve: **build the net → expose the standing failures → close each with a machine test**.

**Discipline**: the failures of the exposure period must not be pretended away: each one must be closed with its own machine test; downgrading to a yellow class to buy a passing state is forbidden, and rebaseline-and-freeze is forbidden.

## 5. The automatic-recovery autopsy law of repair rounds

Every CI repair must do two things (the desk order of November 20, 2026, instituting the law):

1. **The automatic-recovery autopsy**: analyze "why the automatic recovery did not repair it": the root cause must be first-hand evidence (a triage-marker match / an environment difference / a sandbox artifact), never a guess.
2. **Experience/data revisions enter the whitepaper**: after the repair completes, the same round writes the lesson / precedent / prescription into the whitepaper-class section + the triage-table row + the experience card (all three in the same round; missing one = a violation).

**Typical precedent families produced by autopsies**:
- the same-word-two-diseases discriminator (v1 wording vs v2 wording → the triage-table data face lets the automatic-recovery routing separate them)
- the narrow sandbox PATH → the faithful shell form (Git Bash full paths + a `/usr/bin` prefix; quote-free assignments)
- the failure-output tail-N-lines rule + the fail-first summary (breaking the truncation blind spot)
- one retry for the meta-layer timeout (removes the load-induced false positive)
- the cap cross-check (prevents an agent from widening its own range)

## 6. The format of the recursive output (the next round's queue)

Every round's wrap-up scroll **must carry the recursive-output section**, in this format:

```
Recursive output (the next round's queue):
①<candidate 1: source / basis / expected cap>
②<candidate 2: ...>
③cross-agent reconciliation items (e.g. the annotation-copy divergence, on the Wang Xiaoxue side)
④layer-law gated items (threshold self-adaptation etc.; the calibration readings are in place)
```

The next round is driven by the desk's standing authorization: read the recursive output → form the agent team → assign the tickets → loop. **No waiting for orders** (desk order of November 21, 2026: "recursive evolution does not need to wait for my review; every decision is made on its own"). **Boundary**: the five escalation classes (semantic ambiguity / over-scope etc.) still suspend pending adjudication; self-adjudication is limited to mechanically decidable items.

**Registered next-round candidates (the audit annex, cast November 21, 2026; source: requirement annex v2 of the Alpöge RH audit line; the P1-2 ticket, supplement 1 and the release-face note):**

- **P1-2 claim-watch, the conclusion-level watch agent (the interface spec as a next-round candidate)**: watch targets may also be machine-readable status endpoints of the form `{url, phase-field, done-phases[], conclusion-keywords}` (the measured sample shape: one GET returns `phase` / `heartbeat_at` / `progress` / `active_command` together); a `heartbeat_at` staleness beyond its threshold is registered as target silent death; an honest record, not a false alarm; the first watch target is the RH/VERIFY dashboard (http://106.14.11.164/) with a conclusion-level trigger when its phase leaves compile; the Zulip web-public no-auth fetch recipe (via llms.txt) is built in; an unreachable target is registered as "unverifiable" and never fabricated; network-error backoff is built in. Source / basis: the work stream 1 precedents; the Zulip login-wall assumption falsified (all 222 messages fetched with no credentials), the MIT dashboard TLS block (the unverifiable registration precedent), and a conclusion-level signal observed live on November 20, 2026. Expected cap: one tool face plus selftest, P1 window, does not block the P0 pair.
- **P2-1 audit_service, the release-face reference**: the release-face reference checklist; SHA256SUMS / source-inventory / source-scan / verification.log / toolchain / manifest / telemetry, each independently fetchable; is the design reference for the audit-service release face. Source / basis: the requirement annex v2 release-face note (the RH/VERIFY `/artifacts/` board, every piece independently URL-fetchable). Expected cap: design-reference intake into the P2 survey, no tool work in this round.

## 7. Today's chain (a live walk-through, November 19-21, 2026)

```
Fourth review (the audit scroll overturned itself: the "clean zero" claim retracted)
  ↓
Four-P0 repairs + the meta-layer net built (nine runs, 3f781a1)
  ↓ the meta layer's first engagement caught the real symbiosis failure
Failure-output-must-surface + the stub probes (6998c40, 3a56b854, 0765d671)
  ↓
R18 evidence semantics + triage v1.4 (c48a548a)
  ↓
The MCP generation change 44→54 (13cefb0; the adjudication agent corroborated double-blind)
  ↓
The recursive ticket pair: work stream 1 roster 31 + cap derivation + meta-layer fail=2 closed (a07403e3)
  ↓
The recursive third round: work stream 2 roster 42 + the G11 assertion + meta-layer resilience (in flight)
  ↓
The next round's queue (driven automatically by the execution record; self-adjudication keeps the push going)
```

**The key transition**: repair no longer relies on "see a failure → human analysis → human fix": after the meta layer's net is built, failures surface automatically, the triage table classifies them automatically, prescriptions route them automatically, and the desk adjudicates only the two classes of genuine judgment calls: "semantic judgment" and "version authority".

---

## Version history

| Version | Date | Content |
|---|---|---|
| v1.0 | November 21, 2026 | Initial version: full-chain distillation of the four P0s + the meta-verification layer + the three gaps + R18 + work streams 1/2 (nine runs + the recursive ticket pair over three runs) |
