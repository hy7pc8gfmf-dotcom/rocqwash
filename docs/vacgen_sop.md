# SOP: Vacuity Probe Tooling and Verdict Grading (vacgen)

> Purpose.  Turn the five generalization crafts measured effective in the vacmain v2 four-fold-convergence audit (source execution record §4) into executable steps, each with a machine-checkable verdict surface; fix the five-grade verdict law for probe results and the limited-form, three-bounds statement template; draft the independent-repo candidate README skeleton. Zero-compile: this scroll regulates; it fires no build itself.
> Interface.  Document face only (a regulation scroll). Consumed by the self-check agent (phase 2: the shape regression cross-check plus compile adjudication of the filled pieces) and the assembly agent (phase 3: independent-repo candidate registration) per this scroll's §1/§2/§3; the top-level verdict semantics it fixes are stated in §0.3. The wording self-check instrument ships beside this scroll as `ai_flavor_selfcheck.sh` in the same directory.
> Dependencies.  The source execution record `D:/ComplexAnalysis/attn/_vacmain_audit_20261112/回执-vacmain完备审计v2-20261112.md`, the shape originals under `D:/ComplexAnalysis/attn/_vacmain_audit_20261112/sbx_v2/`, the two mechanical tools `_tools/scan_boundary_tokens.py` and `_tools/judge_census_completed.py`, and the wording register `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md`, all listed under Sources below; the cited instruments are python -I, pure standard library; no build and no network dependency.
> Evidence.  Every verdict surface below cites an exact command shape; the wording self-check of §5 was executed in the casting session with first-hand output recorded in the scroll (36 registered faces = 0; em-dash count = 0); the §4 md5 manifest cross-check closed 14/14 MATCH against the source execution record §5.
> Exit-codes.  Not applicable to a document face; the rc values quoted in the command shapes are the documented tools' observed exit codes (0 = passing compile or clean scan; 1 = an expected-fail probe staying quiet, or a failing scan; 2 = a usage or IO error, rerun and do not pass, per §1.3).

- **Date**: November 12, 2026 (job date); casting finalized November 13, 2026, 00:04 local (midnight crossing registered as it happened)
- **Job ID**: `vacgen-20261112`; track B spec agent (SOP casting, zero compile)
- **Sources** (all read first-hand in the casting session):
  1. the source execution record `D:/ComplexAnalysis/attn/_vacmain_audit_20261112/回执-vacmain完备审计v2-20261112.md` (§3 the limited-form three bounds; §4 the five generalization crafts; §5 the md5 manifest, the shape cross-check reference);
  2. the eight shape originals under `D:/ComplexAnalysis/attn/_vacmain_audit_20261112/sbx_v2/` (eight probe files plus four adjudication scrolls; the manifest table in §4);
  3. two mechanical tools: `_tools/scan_boundary_tokens.py`, `_tools/judge_census_completed.py`;
  4. the wording register: `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md` §4.6 and §5.
- **Consumers**: the self-check agent (phase 2) and the assembly agent (phase 3) execute per this scroll's §1/§2/§3; the wording self-check instrument is stored beside this scroll in the same directory as `ai_flavor_selfcheck.sh`.
- **Conventions**: headings and table headers in English (the bilingual as-cast text is preserved verbatim in the sibling `vacgen_sop.md.zh.md` archive); newly cast probe files carry an English header comment whose four fields (audit ID / statement face / verdict semantics / build command line) are the minimum configuration.

---

## 0. Scope, Pre-Flight Gates, and Top-Level Verdict Semantics

### 0.1 Scope and I/O Surface

**Scope**: a vacuity audit of the headline theorem (a challenge-`main`-form statement) of any Lean artifact: deciding whether its premise conjunction is vacuously true (vacuously true: the premises are unsatisfiable, which makes the sorry-proven statement true vacuously). This SOP is the isomorphic migration of the Rocq-side gate8 vacuity watcher into the Lean/mathlib context (the codification of the measured-effective form, item 1 of the source execution record §4).

**Input surface**:

| # | Input | Form | Gate |
|---|---|---|---|
| 1 | Artifact statement face | target path + sha256 (two-point cross-check) | a sha mismatch means UPGRADE; never issue the run in a known-bad state |
| 2 | Toolchain pin | the `lean-toolchain` file value + a measured `lake env lean --version` | all three exactly equal; any drift means UPGRADE |
| 3 | mathlib snapshot | snapshot root path + `.lean` file count + registration date | the window quadruple (path, count, date, pin) is registered in the scroll |

**Output surface** (the four accounts; the generator casts the skeletons, and after filling, grading follows §2):

| # | Account | Expected verdict | Content |
|---|---|---|---|
| 1 | witness face | expected-green | an existence-instance envelope theorem (constructive witness, two anchors spliced) |
| 2 | refutation spectrum | expected-fail | multi-form refutation probes (full form / specialization / context / discipline face / tactic spectrum) |
| 3 | boundary machine check | expected-green | the closed-form real-order separation theorem group |
| 4 | absence verdict | expected-absent | the name-family census plus the four-strand joint verdict (§1.4) |

### 0.2 Pre-Flight Gates (fail-loud: any failed gate halts work and escalates)

| # | Gate | Command shape | PASS criterion |
|---|---|---|---|
| G1 | Toolchain equality | `cat lean-toolchain` + `lake env lean --version` | the output equals the pin exactly, verbatim |
| G2 | Target fingerprint | `sha256sum <artifact>` (fired once at each of the two points: the shipped copy and the original) | both points agree on the value |
| G3 | Shape originals on disk | `md5sum <the eight files>` cross-checked against the reference manifest in §4 | every file's value agrees |
| G4 | python availability | `python -I -c "print('ok')"` | exit 0; generator and scanners are python -I, pure stdlib |

### 0.3 Top-Level Verdict Semantics

**A passing compile on a refutation face is the vacuity alert, the highest level.** If an expected-fail probe (an expected-fail piece) compiles with rc=0, then the premise conjunction is unsatisfiable and the audited sorry-proven statement is vacuously true; this confirms vacuity: freeze all further runs, escalate and report, and set the audit verdict `ok = false`. An expected-fail watcher that stays quiet (rc=1) is the healthy state. All other faces grade per the five-grade law in §2. This semantics was measured effective in the source audit's four-fold convergence (refutation spectrum 5/5 rc=1, zero alerts).

---

## 1. The Five Generalization Crafts, Codified

> Each craft = executable steps (the S series) plus a verdict surface (the V series, a machine-check table). The steps are the operating procedure; the verdict surfaces are the acceptance criteria; every PASS/RED row in a verdict surface is mechanically re-checkable from its command shape.

### 1.1 Craft 1: Sentinel Semantics (Expected-Red Discipline)

**Craft in one sentence**: every probe file must have declared its expected verdict before the run is issued; the refutation face is a COMPILE-MUST-FAIL watcher: a passing compile is the alert, a staying-failing compile is health.

**Steps**:

- **S1-1 Expected-verdict declaration first**: every probe file's header comment states the expected verdict before the run is issued. Refutation faces are marked `EXPECTED-FAIL` (including the expected locus: the written-form closing read locus or the residual goal); witness/boundary/skeleton faces are marked expected-green. Placeholder sorry positions are explicitly declared and counted with `EXPECTED-FAIL`/`TODO-SEAT` comments.
- **S1-2 The skeleton verification run goes first**: fire the skeleton verification file first (it shares the module header, the import face, the probe-point lemma, the bites, and the `#print axioms` command with the five refutation faces, but carries no must-fail theorem) and require rc=0 passing. Until the skeleton is proven sound, any refutation failing result must not be read as evidence (the failing result may come from a skeleton defect rather than the verdict). Source-audit example: `_vacsmoke.lean` ran rc=0 first, and only then were the five forms' failing results the expected verdict (source execution record §1 entry 2).
- **S1-3 Refutation faces fire and register their loci**: fire the refutation faces one by one, recording rc and the adjudication locus (the compiler error's `file:line`) per face. The locus must fall inside the declared closing read locus; a drifted locus is a shape-discrepancy event and is registered as observed.
- **S1-4 Alert rule**: any `EXPECTED-FAIL` face with rc=0 is the vacuity alert: freeze all further runs, escalate and report, and set `ok = false`. The alert verdict takes this face's compile log as its only evidence.

**Verdict surface V1 (machine-check table)**:

| Check | Command shape | PASS | RED |
|---|---|---|---|
| Expected-verdict markers in place | `command grep -c "EXPECTED-FAIL" <probe.lean>` per face in the header region | refutation faces >=1; expected-green faces =0 | a face fired with its marker missing |
| Skeleton run passing first | guard-wrapped compile of the smoke file, `echo RC=$?` taken directly without a pipe | an rc=0 record exists before any refutation adjudication | smoke rc=1 means a skeleton defect; a refutation failing result must not be read as evidence |
| Refutation face failing with the locus inside the read locus | guard-wrapped compile per face, `echo RC=$?` plus the archived log | rc=1 and the error locus equals the declared read locus | rc=0 means the vacuity alert (S1-4); a drifted locus means shape discrepancy |
| Placeholder count monotone | `command grep -c "TODO-SEAT" <file>` compared between fill rounds | the count is monotone non-increasing | write no exact-equality invariant against a live counter (forbidden; see the §2.2 note) |

### 1.2 Craft 2: Probe Casting, Four-Piece Set

**Craft in one sentence**: every probe file consists of four pieces: the English header comment, the verbatim-transcription machine check, machine bites, and the per-theorem `#print axioms` report; only with all four pieces can a passing or failing verdict be attributed.

**Steps**:

- **S2-1 (a) English header comment**: the probe file's header comment block is all English, with the four minimum fields: audit ID, statement face (which target artifact and which premise interface the transcription came from), verdict semantics (the expected verdict plus what passing and failing each mean), and build command line (the full thermal-guard-wrapped form); plus a discipline line (no sorry / no admit / no native_decide / no new axioms). Reference form: the header comments of the eight `sbx_v2/` files.
- **S2-2 (b) Verbatim-transcription machine check**: the audited premise interface is transcribed verbatim into the probe's hypothesis positions; the transcribed text is mechanically compared against the target artifact's original text (string/token-level equality) and the comparison output is kept on record. **The target artifact itself never enters the import face** (its sorry-proven piece would pollute the axiom audit); the probe carries the interface by re-declaration (source execution record §1 entry 2, the "verbatim-transcription machine check" row).
- **S2-3 (c) Machine bites**: a group of small theorems instantiating the interface vocabulary at concrete probe points, intentionally compiling passing, proving that the transcribed interface is typeable against the same import face the target artifact declares. All bites passing is the precondition for reading a refutation failing result as evidence (the interface-engagement check).
- **S2-4 (d) Per-theorem `#print axioms` report**: at the end of the file, issue `#print axioms` for every compilable declaration; the expected profile is a subset of `[propext, Classical.choice, Quot.sound]`; a `sorryAx` hit is failing; a newly declared axiom is failing.

**Verdict surface V2 (machine-check table)**:

| Check | Command shape | PASS | RED |
|---|---|---|---|
| Header four fields complete | `command grep -c -E "Audit|Statement|Verdict|Build" <probe.lean>` field by field over the header region | each of the four fields >=1 | any field missing |
| Transcription-equality machine check | the `python -I` comparison script (transcribed text against the target artifact's original text) | a PASS output kept on record | any inequality |
| Target artifact zero-imported | `command grep -n "<artifact-module>" <probe.lean>` over the import face | 0 hits | >=1 (the pollution source is present) |
| All bites passing | per bite theorem in the compile log, check rc and the `#print axioms` line | all rc=0 plus the three standard axioms | any one failing means the interface failed to engage; a refutation failing result must not be read as evidence |
| Three-standard axiom profile | `command grep -c "sorryAx" <log>` | 0 | >=1 (failing; UPGRADE) |

### 1.3 Craft 3: Token Breakwater Scanner

**Craft in one sentence**: admission tokens (the sorry/admit/native_decide/axiom family) must have zero hits on the statement/proof faces; the scanner strips nested block comments and string literals, and the code face and the comment face are accounted separately: a comment-face hit is reported as observed but is not a violation.

**Tool**: `_tools/scan_boundary_tokens.py` (python -I, pure stdlib, single-pass scan; md5 in the §4 manifest; the line-15 token table is `\b(sorry|admit|native_decide|sorryAx|axiom|axiomX|Admitted|Abort)\b`).

**Steps**:

- **S3-1 Scan per file**: one shot per probe file: `python -I scan_boundary_tokens.py <probe.lean>`; `echo RC=$?` takes the exit code directly.
- **S3-2 Two-account reading**: read both accounts, `CODE_FACE_HITS` (the statement/proof faces after comment stripping) and `RAW_FACE_HITS` (the full text including comments). The criterion applies to the code face only: a comment-face hit (for example the header discipline line's own "no sorry") is listed as observed and is not a violation.
- **S3-3 Mechanism boundary (two no-false-positive rules)**: the scanner strips `/- -/` (including the `/-- -/` docstring form) and `--` line comments and string literals; the Rocq-form `(* *)` is deliberately not stripped: a `.lean` file using it is itself unparseable (source-audit boundary-file precedent, attempt 1: Rocq-form delimiters inside a Lean header comment meant a failing compile, a fail-loud shape-discrepancy registration, and a statement face left untouched).

**Verdict surface V3 (machine-check table)**:

| Check | Command shape | PASS | RED |
|---|---|---|---|
| Scanner fingerprint | `md5sum _tools/scan_boundary_tokens.py` | the same value as in the §4 manifest | any drift means UPGRADE (never scan in a known-bad state) |
| Per-file code face zero hits | `python -I scan_boundary_tokens.py <probe.lean>` | `VERDICT CLEAN` and RC=0 | `VERDICT RED` (RC=1 is fail-loud); RC=2 is a usage/IO error, rerun and do not pass |
| Both accounts reported | read the two output lines `CODE_FACE_HITS`/`RAW_FACE_HITS` | both lines present | a single account only means the split accounting failed |

### 1.4 Craft 4: Full-Tree Name-Family Census

**Craft in one sentence**: the absence verdict = zero hits in the name-family census plus the three collateral strands conjoined; a zero hit on a single name family is only a name-level negative finding and does not constitute the absence verdict.

**Tool**: `_tools/judge_census_completed.py` (python -I; walks all `.lean` files, counts per variant and reports file counts; md5 in the §4 manifest). For generalized use, rewrite the `VARIANTS` name family and the census roots for the target face; the instrument's form stays unchanged.

**Steps**:

- **S4-1 Pin the snapshot window**: pin the census roots first (the mathlib snapshot path plus the local asset root) and register the window quadruple (path, file count, date, toolchain pin). The file count is the snapshot's registered value, not a live invariant; re-measure it at every audit run and register it with its date.
- **S4-2 Define the name family**: the target construction's candidate name family has >=3 variants (the CamelCase proper name / a snake_case variant / a module-qualified form); the variant set is written into the census script and registered with the scroll.
- **S4-3 Fire the census**: run `python -I judge_census_completed.py`; read per tree the `lean files scanned: N` line, the per-variant hit counts, and the `JOINT VERDICT` line.
- **S4-4 The four-strand joint verdict**: the absence verdict requires the four strands of evidence **conjoined** (the source audit's four strands; source execution record §1 entry 4 and the absence-verdict scroll §6): (a) zero hits for all three name-family variants; (b) the owner module's own TODO/roadmap face is present; (c) the existing definition face is a series/junk-value form (an out-of-domain value witness is present); (d) the module's full theorem list carries no extension-form statement. Any single strand is only name-level or local evidence; all four together are the absence verdict.
- **S4-5 The negative finding draws its own boundary**: the absence statement draws its boundary by itself per the §2.4 four elements (what was scanned / what was not scanned / the non-absolute form / aliases not exhausted).

**Verdict surface V4 (machine-check table)**:

| Check | Command shape | PASS | RED |
|---|---|---|---|
| Window quadruple on record | read the audit scroll's registration line | all four of (path, count, date, pin) present | any one missing means the window is unpinned; no absence verdict may be issued |
| Census output complete | the output of `python -I judge_census_completed.py` | per tree the scanned N line, the per-variant counts, and the JOINT line | a `READ_FAIL` line means a fail-loud registration |
| Four strands conjoined | the four strands registered line by line (a/b/c/d, each with its first-hand evidence path) | all four present | any one missing downgrades the statement to a "name-level negative finding"; writing "absence verdict" is forbidden |
| JOINT verdict reading | read `JOINT VERDICT ... = 0` | =0 means ABSENT (the pending grade); >0 means PRESENT (the absence grade withdrawn and the witness face rerun) | mixing the readings (writing "does not exist" directly from zero hits) is an overreach claim |

### 1.5 Craft 5: Shot-Order Registration

**Craft in one sentence**: record-face runs and adjudication-evidence runs are accounted separately: record-face runs at the script layer (zero-cost to replay, possibly predating the probe files) do not constitute adjudication evidence; adjudication cites only post-cast, guard-wrapped evidence runs whose rc was taken directly without a pipe.

**Steps**:

- **S5-1 Two accounts kept apart**: account every compile launch at launch time: a **record-face run** (launched by the script layer's record face; Resume/Amend replays are zero-cost; the probe files may not exist yet at launch; its rc cannot be attributed to a verdict) versus an **evidence run** (launched after the probe files are in the tree, guard-wrapped, rc taken directly without a pipe, the log archived and pinned by md5). Every run enters exactly one account; compiling outside the accounts is forbidden.
- **S5-2 Four requirements per evidence run**: every evidence run cited for adjudication carries all four requirements: (a) the guard trace line on record (core pin / authorization / gear / done exit); (b) the log file in the manifest; (c) rc taken directly without a pipe (`echo RC=$?`; taking the code after `cmd | tail` is forbidden); (d) the launch timestamp registered. Source-audit example: the five record-face runs launched before casting, their rc=1 not attributable; the adjudication evidence = the post-cast guard-wrapped compiles plus the Judge's per-run replay (source execution record §1 entry 2, the "shot-order registration" row).
- **S5-3 Independent replay**: before close-out, replay every evidence run once independently (recompile run by run; cross-check each face against the recorded run account); close out only on zero divergence; any divergence is a fail-loud shape discrepancy.
- **S5-4 The thermal guard canonical form**: every compile goes through the thermal guard wrap (the local canonical form is `cpu_guard_v3.ps1 -TempLimit 98 -CoreN <N> -AllowG3 -GearForce 0`; bare `lake` is forbidden); on another machine substitute the local equivalent wrap per the assignment protocol; bare runs are forbidden.

**Verdict surface V5 (machine-check table)**:

| Check | Command shape | PASS | RED |
|---|---|---|---|
| Both accounts complete | the run-order ledger labeled line by line | every run in exactly one account; record-face runs explicitly marked non-evidence | a compile outside the accounts, or mixed accounts |
| Four evidence requirements | per cited log, `command grep -c -E "pinned to core|done exit" <log>` plus the rc line | all four requirements present | any one missing disqualifies that run as adjudication evidence |
| Independent replay, zero divergence | per replay log, cross-check against the recorded run account | rc and locus equal per run | any divergence is a fail-loud shape discrepancy |
| Replay artifacts pinned | `md5sum <replay logs>` into the manifest | all present | an artifact missing from the manifest |

---

## 2. Verdict Grading Law

### 2.1 The Five Grades

| Grade | Mechanical trigger | Reading | Mandatory action |
|---|---|---|---|
| **strong red** | statement-face break: the probe's own statement fails against the interface (an Unknown identifier at the transcription position, an unusable constructor, a Cannot find witness form) | **form registration only, no evidential force** (the probe never engaged the interface; it proves neither vacuity nor non-vacuity) | register the form; repair the probe; re-issue the run |
| **weak red** | a mechanical failing result that is not a statement-face break, with the locus inside the declared read locus (an automation exhausted or unsolved goals form) | **nonempty evidence**: the premise interface resisted this refutation attempt at this spectrum strength | register rc and locus per face; enter the convergence account |
| **refutation green** | an `EXPECTED-FAIL` face compiles with rc=0 | **the vacuity alert, the highest level**: the premise conjunction is unsatisfiable and the audited statement is vacuously true | freeze, escalate and report, and set `ok = false` |
| **boundary green** | the boundary machine-check face (expected-green) compiles with rc=0 | **a positive machine check**: the closed-form separation computation holds | register; state it in limited form (judge only that closed-form fact) |
| **absence** | the §1.4 four-strand conjunction holds inside the pinned snapshot | **pending**: a formalization-gap record; not an alert, not a vacuity claim, not a provability claim | register per the §2.4 four elements; re-audit condition = the upstream formalization lands |

**Supplementary grade for an expected-green face turning failing**: a compile failing on a witness/boundary/skeleton face (all expected-green) is a probe-side defect or a broken splice face (for example a witness splice-anchor mismatch) and is handled the same way as strong red: fail-loud shape-discrepancy registration, repair the probe, re-issue the run; it must never be read as any judgment about the audited artifact (same form as the source execution record's escalation channel 3).

### 2.2 Scoping Note and Live-Counter Note

- **Scope**: this five-grade law applies to the vacuity probe family (the transcribed interface plus the refutation/boundary/witness faces). Other probe families (for example inversion probes against a corrected form) declare their own expected-verdict mapping at casting time per Craft 1 S1-1, and the grade semantics follow that mapping; a run without a declared expected verdict does not enter grade adjudication.
- **No exact-equality invariants against live counters**: quantities that evolve over time, such as probe counts, skeleton fill counts, and snapshot file counts, take only monotone bounds as their invariants (for example "the TODO-SEAT count is monotone non-increasing" and "an EXPECTED-FAIL face must not turn passing"); **exact-equality invariants are forbidden** (for example "always exactly N files", "exactly K successes"); snapshot numbers are always registered with their date and never count as live-check bounds (artifact-verifier design law, rule 1).

### 2.3 Limited-Form, Three-Bounds Template

Audit conclusions and escalation statements are always in limited form; any extrapolation beyond the three bounds is invalid. Template (slots marked with angle brackets):

```text
Escalation / conclusion statement (limited form):
  "<artifact> (<path>, sha256 <64 hex chars>) passed the vacuity audit (<UTC date>):
   <one-line conclusion per face: witness face / refutation spectrum / boundary machine check / absence verdict>."
Three bounds:
  1. Object bound: applies to this artifact instance only (sha-locked);
     no extrapolation to other pieces or other versions of the same artifact.
  2. Spectrum bound: applies to this probe spectrum only (manifest-locked);
     no extrapolation to other probe forms or to forms added later.
  3. Window bound: applies to this toolchain pin and this mathlib snapshot window only;
     the verdict must be re-audited once upstream advances; no permanent claim.
  Out-of-bound extrapolation (universal statements such as "the whole repository is
  audited", "valid forever", or the truth value of the zero-point freeness
  proposition) is invalid.
```

**Worked example (measured form from the source audit, excerpt)**: "The axiom-challenge face `main` (`DedekindZetaChallenge.lean`, sha256 `dd2562c8…62be`) passed the axiom-closure + vacuity double audit (November 12, 2026): the ℚ specialization face's constructive witness compiled passing; all five refutation forms stayed failing (nonempty evidence, zero vacuity alerts); the boundary machine check passed; the generic-extension face's formalization absence is honestly recorded as pending." The verbatim three-bound binding is in the source execution record §3.

### 2.4 Negative-Finding Boundary, Four Elements

Any statement of the "not detected / zero hits / no precedent on the scanned face" kind (a negative finding) must carry the four elements in the same sentence; missing any element downgrades it to "not detected by this tool face on this run":

| # | Element | Content |
|---|---|---|
| 1 | what was scanned | per item: the face, the method, the point in time (which trees, which criterion, file-level or name-level, the UTC point) |
| 2 | what was not scanned | explicitly declare the uncovered faces (for example "a name search, not a file-by-file full read") |
| 3 | non-absolute | phrase it as "a negative finding on this scanned face"; writing "does not exist / has never been done" is forbidden |
| 4 | aliases not exhausted | same-name different forms, translation variants, and semantically equivalent implementations may lie outside this scanned face |

Every absence conclusion must also carry a **re-audit condition** (when the scanned face is rescanned: a census rerun whenever the upstream snapshot advances); a pending item without a re-audit condition is not closed out.

### 2.5 Erratum (November 14, 2026): as-cast envelope malformed-shape registration (registered engine debt)

**Defect statement (first-hand evidence on record)**: for artifacts whose
headline theorem declares *implicit binders* (e.g. `{K : Set (Fin n → ℝ)}`),
the as-cast witness envelope is malformed Lean: the binder's **type** is
spliced into the conjunction chain as a bare conjunct (`∧ Set (Fin n → ℝ)`:
a `Type`-sorted expression in a `Prop` conjunction) and the binder variable is
left **unbound** (referenced by later conjuncts with no existential prefix
segment of its own). Root cause (engine-side, two cooperating faces):
(a) the L1 splitter classification; explicit hypotheses land in `S1 vars`
(`hK : IsCompact K` became a "var") while implicit binders land in
`S2 assumptions` (`K : Set (Fin n → ℝ)` became an "assumption");
(b) `envelope_statement` splicing (`tools/vacgen.py:640-650` at revision
2.0.1) joins `S2_assumps` types verbatim into the `∧` chain and prefixes only
`S1_vars`. First-hand evidence: batch-1 item-16 verdict (MahlerConjecture.lean,
sha256 `40718172…20ea0`, source execution record §3 account 1; malformed
signature transcribed there) and the rqw11 round-1 replay (`recast/16` cast
log + witness fire rc=1 with `SMul ℝ ℤ` synthesis failure and
`unknown constant …_premises_witness`).

**Checker blind spot (registered alongside)**: the cast's own bound-form
invariant `envelope_free_vars_zero` reports PASS on the malformed envelope
(word-face free-variable scan sees the binder name absent from the envelope
body, not the type-as-conjunct ill-typedness); a bound-form PASS is therefore
**not** evidence of envelope well-typedness until the checker is extended.

**Handling (same grade as §2.1 expected-green-face-red)**: an expected-green
witness face failing on the malformed envelope is a probe-side defect, never a
judgment about the audited artifact. Canonical hand-cast repair form (zero
premise weakening; transcribed from the batch-1 item-16 verdict, source
execution record §3 account 1):

```text
∃ n : ℕ, ∃ K : Set (Fin n → ℝ),
  1 ≤ n ∧ IsCompact K ∧ Convex ℝ K ∧ (∀ x ∈ K, -x ∈ K) ∧ (interior K).Nonempty
```

with the registered fill precedent `K := Metric.closedBall (0 : Fin 1 → ℝ) 1`
(compact, convex, symmetric, nonempty interior; repair round 2 of the ≤2
budget, rc=0, PA 3-standard, `sorryAx` 0). Anchor set measured first-hand on
November 14, 2026: `isCompact_closedBall`
(`Mathlib/Analysis/InnerProductSpace/EuclideanDist.lean:79`), `convex_closedBall`
(`Mathlib/Analysis/Normed/Module/Convex.lean:70`), `interior_closedBall`
(`Mathlib/Analysis/Normed/Module/RCLike/Real.lean:76`); the batch-1 verdict's
scratch citations carried abbreviated paths; this section carries the measured
locations.

**Open engine debt (honestly registered, not repaired by this work stream)**: the
engine-side repair (L1 splitter classification, `envelope_statement` splicing,
bound-form checker extension) lies outside the auto-apply surface of the
healing work stream (this erratum + the shape-table row + test assertions only).
Re-audit condition: after the engine repair work stream lands, re-cast every artifact
cast under this erratum and re-run `tests/t_vacgen_envelope_shape.py`; until
then every implicit-binder artifact requires the hand-cast repair above.

**Registered self-healing surfaces (this work stream, all verified)**:
1. **Shape-table row**: `tools/taxonomy.json` landed on November 14, 2026 (builtin
   starter row carried verbatim + `geo.symmetric-set-premise` row matching the
   `∀ v ∈ S, -v ∈ S` premise face). Measured effect on the Mahler-family
   artifact: L3 coverage 0/5 → 1/5 (top family `geo.symmetric-set-premise`);
   the row registers the family and the fill precedent in data; it does not
   repair the engine splice. `requireVarBinding` deliberately false: the set
   variable is not among `S1 var` names under the current classification, so
   the v1 parity binding check would block recognition.
2. **Test assertions**: `tests/t_vacgen_envelope_shape.py` (fixture A pins the
   well-formed-envelope contract on a well-formed face; fixture B pins the
   registered debt signature `∧ Set (` on an implicit-binder face as a
   loud known-debt vector; red there means the engine debt was FIXED and the
   pin must be updated with the engine repair registration). The two existing
   vacgen tests (`tests/t_vacgen_shape.py`, `tests/t_vacgen_expectedred.py`)
   were **unwired** in `tests/run_tests.sh` (zero mentions found by grep on
   November 14, 2026) and are wired by this work stream;
   `tests/t_vacgen_shape.py`'s subprocess read face additionally lacked
   `encoding="utf-8"` (GBK-locale reader-thread decode failure on cast reports
   with math symbols) and was aligned with the `t_vacgen_expectedred.py` read
   face.

---

## 3. Independent-Repo Candidate README Skeleton

### 3.1 Zero-Preemption Declaration

**Independent-repo candidate = registration only, no repository created (zero-preemption)**: this section registers candidate skeleton text only; no repository has been created, no name registered, nothing published, and nothing submitted upstream. The skeleton text is a draft; any follow-up is handled as a separate task instruction. This section's text is the target outward face (the publication body) and is written in the outward register: it states only what was done and what was measured, with zero internal numbering and zero priority claims.

### 3.2 README Skeleton Draft

```markdown
# vacgen · Vacuity Probe Generator for Lean Artifacts (candidate tool)

**Status**: candidate registration only: no repository has been created,
no name registered, nothing published, nothing submitted upstream. This page is
a draft skeleton for a possible future standalone repository.

## What it does

Given a Lean artifact's headline theorem, vacgen generates a four-account
vacuity probe package and grades the results:

1. **Witness face**: an existence-instance envelope theorem showing a concrete
   witness function satisfies the artifact's premise conjunction (constructive
   non-vacuity evidence for the specialized face);
2. **Refutation spectrum**: expected-fail probes attempting to derive `False`
   from the transcribed premise interface; a probe that compiles means the
   interface is unsatisfiable, i.e. the artifact's `sorry`-proven statement is
   vacuously true (the alert);
3. **Boundary machine check**: closed-form separation computations over the
   relevant regions (positive machine checks);
4. **Absence verdict**: a name-family census over the pinned library snapshot,
   deciding whether the formalization face of the needed background theory is
   present or absent (absence is recorded as pending, never as an alert).

## Input surface

- the artifact statement face (target file + sha256, verified at two points);
- the toolchain pin (`lean-toolchain` value, verified against the running
  toolchain);
- the pinned mathlib snapshot (path + `.lean` file count + registration date).

## Output surface

Four accounts (witness / refutation spectrum / boundary / absence), each with
per-probe exit codes, verdict loci, `#print axioms` profiles
(`propext`/`Classical.choice`/`Quot.sound` tolerated; `sorryAx` is a red
finding), and an md5 manifest of every probe and log.

## Dependency boundary

- The generator itself: Python 3 standard library only; zero network; zero
  compilation.
- Probe compilation: consumer-provided Lean toolchain + mathlib snapshot
  (pinned; every absence verdict and every witness splice anchor is relative
  to that snapshot window).
- Verdicts carry their snapshot window: when the upstream library advances,
  absence verdicts must be re-run (re-run condition registered with each
  verdict); splice anchors are re-verified against the new snapshot before
  any reuse.

## Non-goals

- It does not judge the mathematical truth of open clauses inside the
  artifact (a refutation red records that the interface resisted the attempted
  strength; it is not a satisfiability proof).
- It does not replace kernel checking; it composes with it.
- It registers no priority claims of any kind.
```

**Skeleton four-element cross-check** (self-check by this agent, line-level verification):

| Required element | Location in skeleton |
|---|---|
| tool name | the title line `vacgen · Vacuity Probe Generator for Lean Artifacts` |
| I/O surface | the `Input surface` / `Output surface` sections |
| zero-preemption declaration | the first `Status` paragraph |
| snapshot boundary | the whole `Dependency boundary` section (window binding + re-audit condition) |

---

## 4. Shape-Original Manifest and Cross-Check

**Measurement basis**: the md5 values below were measured first-hand with `md5sum` in the casting session (November 13, 2026, 00:0x local); the cross-check reference is the manifest in the source execution record §5; all ten files plus four scrolls agreeing value-for-value establishes the same entities (the cross-check law: a verdict reference is always md5/sha cross-checked against the reference, never trusted by filename or size intuition).

**Probes and tools (10 files)**:

| File | md5 (measured) | vs source execution record §5 manifest |
|---|---|---|
| `sbx_v2/_vacmain_q_witness.lean` | `451a796ecdb700305cc35bdc0e5e6f5e` | MATCH |
| `sbx_v2/_vacmain_boundary.lean` | `91b2c094295261ce4d25be94df80316b` | MATCH |
| `sbx_v2/_vacsmoke.lean` | `d05e87ec243f323bf0716c08b8ac0b3f` | MATCH |
| `sbx_v2/_vacfalsify_full.lean` | `428a8134f7344e45bbb8a4767789d6d1` | MATCH |
| `sbx_v2/_vacfalsify_rat.lean` | `01c29f5daab1988caa8a51e5be1438d3` | MATCH |
| `sbx_v2/_vacfalsify_gamma.lean` | `aa6ec7aaeb54dfb04636e7bb8a0d6cc7` | MATCH |
| `sbx_v2/_vacfalsify_noclassic.lean` | `b68a0a46bbf92d3749aea46c1bb21f65` | MATCH |
| `sbx_v2/_vacfalsify_tactics.lean` | `73536866405e175eff90b92575a7703d` | MATCH |
| `_tools/scan_boundary_tokens.py` | `5e8b308f8c3c8201c27afabf73ec1d77` | MATCH |
| `_tools/judge_census_completed.py` | `8d8ca9feaf3fe83c6c7df4d2c389755c` | MATCH |

**Adjudication scrolls (4)**:

| File | md5 (measured) | vs source execution record §5 manifest |
|---|---|---|
| `sbx_v2/witness判读-20261112.md` | `c49f89f52193692e55fc88cb6917fdef` | MATCH |
| `sbx_v2/否证谱判读-20261112.md` | `6ae392743bc2cac2ddca31faeed84c51` | MATCH |
| `sbx_v2/边界机检判读-20261112.md` | `2807832ac2d721807078e5e32aaa227a` | MATCH |
| `sbx_v2/延拓缺位定谳-20261112.md` | `31851ad7d1210bc1945c76f0651ec6e7` | MATCH |

**Cross-check conclusion**: 14/14 byte-for-byte MATCH; the shape originals are present in the tree without drift, and the phase-2 shape regression cross-check may take this table as its baseline.

---

## 5. AI-Flavor Wording Self-Check (Assertion on Record)

### 5.1 Register and Instrument

- **Register**: `D:/ComplexAnalysis/规范术语/术语表-通用-项目级-20260921.md` §4.6 (the AI-flavor wording register, Chinese word row A and expression-pattern row C) plus §5 (the three English families: word faces, sentence patterns, structures); the operational mirror is `C:/Users/Live/.zcode/skills/cw-wf-dispatch/references/constraint-blocks.md` §13.
- **Battery**: the Chinese battery, three families and 10 faces (the officialese-verb family, the pseudo-abstract-noun family, the slogan-compression family; the family names and the full face list are governed by register §4.6 row A and the instrument's embedded regexes; the face literals stay out of this scroll to avoid self-contamination hits), plus the English battery, 26 patterns (15 word stems + 8 sentence patterns + 3 paragraph-initial transitions), plus the em-dash (U+2014) count.
- **Instrument**: `ai_flavor_selfcheck.sh` in this scroll's directory (the face literals are embedded in the instrument; the instrument is outside its own assertion domain; measured with `command grep`; a single-shot ugrep shim run is forbidden).
- **Two-way validation of the instrument (first-hand, this agent)**: the positive-control fixture (embedding one known hit face per battery plus one em-dash) measured `VERDICT RED`, exit 1, with each of the four battery counts exactly 1 and the em-dash count exactly 1; the negative control (this scroll) measured `VERDICT CLEAN`, exit 0. Only a two-way pass feeds the §5.2 assertion (an audit instrument is validated against known truth before it produces numbers).

### 5.2 Measured Output (first-hand in the casting session, November 13, 2026, 00:0x local)

Command (verbatim, one shell line; the as-cast two-line continuation form is preserved in the sibling `.zh.md` archive):

`sh "D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/ai_flavor_selfcheck.sh" "D:/ComplexAnalysis/attn/_vacgen_20261112/selftest/SOP-vacuity探针工具化-20261112.md"`

Measured output (verbatim):

```text
CH_3FAMILIES_10FACES lines=0
EN_WORD_STEMS_15FACES lines=0
EN_SENTENCE_8FACES lines=0
EN_PARA_INITIAL_3FACES lines=0
EM_DASH_U2014 count=0 (target 0)
TOTAL_WORDING_LINES=0
VERDICT CLEAN (36 faces = 0; em-dash = 0)
```

(Instrument exit 0; final-measurement timestamp November 13, 2026, 00:11 local. Honest process note: the first measurement round read `EM_DASH_U2014 count=45` (RED; the draft contained Chinese dashes and README English dashes); after clearing each occurrence, the final measurement is as above; the wording batteries were already all-zero in the first round. The final measurement is bound to the scroll-closing state; validity is governed by §5.3.)

### 5.3 Assertion and Validity

**Assertion**: at the scroll-closing point, this scroll (as-cast title `SOP-vacuity探针工具化-20261112.md`) measured grep=0 over the 36-face wording battery and em-dash=0. This is a **closed-window scan assertion over that file's static content at that point in time** (a snapshot assertion, registered with its date), not a live invariant; any later change to the file voids the assertion immediately, and the changing agent must rerun the instrument and register the new measurement. This is the documentation version of "the wording face and the implementation pass the same gate": the self-check claimed in §5 and the checks the instrument actually executes correspond token for token (the instrument's regexes are the register's full face list, with no omissions and no extensions).

Translation note (registered by this translation): this English face is itself a later change in the sense above, so the as-cast assertion does not carry over to the translated text; the instrument is not present in this repository, so no re-registration is possible here, and the as-cast measurement remains on record in the `.zh.md` archive. The §6 checklist likewise records the as-cast state.

---

## 6. Acceptance Checklist (Five Deliverables of This Scroll, recorded at the as-cast closing)

| # | Deliverable | Verdict surface | Status |
|---|---|---|---|
| 1 | The five generalization crafts codified (each craft = executable steps + a verdict surface) | §1: each of the five crafts carries an S-series step list plus a V-series machine-check table (20 steps and 20 verdict-table rows, counted and verified) | DONE |
| 2 | The verdict grading law (five grades) + the limited-form three-bounds template | §2: the five-grade table (§2.1) + the scoping and live-counter notes (§2.2) + the three-bounds template (§2.3) + the negative-finding four elements (§2.4) | DONE |
| 3 | The independent-repo candidate README skeleton (four elements) | §3: the zero-preemption declaration (§3.1) + the skeleton body (§3.2) + the four-element cross-check (tool name / I/O surface / zero-preemption / snapshot boundary all in place) | DONE |
| 4 | The AI-flavor wording self-check grep=0 assertion on record | §5: the register + the instrument + the first-hand measured output (36 faces=0, em-dash=0, exit 0) + the validity clause | DONE |
| 5 | Bilingual headings + English table headers | across the scroll, every `#`/`##`/`###` heading bilingual and every table header column in English (re-verified by enumerating every table at casting) | DONE |

**Honest boundary (what this scroll does not cover)**: the vacgen generator entity, the two-artifact end-to-end self-check, the OAI boundary-file fill compile, and the whole-effort md5 manifest close-out belong to the casting, self-check, and assembly agents' authority faces; this scroll supplies only their regulation and grading law. The scroll itself is zero-compile and fired no run (an SOP is a document file; the zero-compile discipline applies).

*This scroll does not state its own md5 (a self-reference paradox guard, same-pattern precedent in the source execution record); the scroll recipient md5sums it and cross-checks.*
