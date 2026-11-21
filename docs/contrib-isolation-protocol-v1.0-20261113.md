# contrib-isolation-protocol-v1.0-20261113.md: contributor-isolation protocol for the rocqwash tool repository, v1.0.
>
> **ContributorIsolationProtocol**: the canonical protocol that keeps every contributor update inside an isolated lane; a subdirectory, a namespaced registry segment, or a topic branch; so the continuously-evolving core lane is never destabilized by an un-audited contribution.
>
> Purpose.  Institutionalize the collaboration-isolation law of the repository constitution (the v53 three-law
>   base release) as mechanical, checkable rules: the isolation principle and its precedent lanes (§1), the
>   lane-placement specification (§2), the four-check intake pipeline audit → norm → gate → merge (§3), the
>   registry regeneration rule for tail-zone collisions (§4), and the two-stream etiquette (§5).
>
> Interface.  Governs every contribution face to the serviced proof repositories: proof files, registry rows
>   (`order.txt`, `_CoqProject`), prose faces, and topic branches. Command faces are cited verbatim from the
>   routed tools `tools/registry_audit.py`, `tools/norm_lint.py`, `tools/registry_union.py`,
>   `tools/registry_fix.py` (cw.sh routes `audit`, `norm-lint`, `union`, `registry-fix`); every flag cited
>   here is a flag the owning tool's `--help` actually emits.
>
> Dependencies.  The Annotation Standard Card `docs/annotation-standard-v1.0-20261113.md` and its Appendix A
>   mapping table `docs/jargon-to-standard-mapping-v1.md` (prose-face law; new files are English-only). Evidence
>   accounts: `docs/勘形-Main新内容预热-20261113.md` (Main `y_e1_gamma_nodes/` survey) and
>   `docs/判例-R3复发-route2tierA自愈-20261113.md` (Set supply, PR#48 collision). Tools are stdlib-only.
>
> Evidence.  Each rule in §1–§5 carries its precedent anchor in place, drawn from the two evidence accounts
>   and the frozen ledger, not from narration. Mechanical self-checks run at issue time: a zero-error norm
>   lint of this file against the mapping table, `tools/norm_lint.py --selftest` rc=0, and
>   `tools/doc_lint.py --repo <root>` verdict consistent (zero drift).
>
> Exit-codes.  No new exit codes. Each pipeline check keeps its implemented semantics; `registry_audit`
>   0/2/9 (findings are data, exit 0 with a loud account), `norm_lint` 0/1/2/9 report-only,
>   `registry_union` 0/2/9, `registry_fix` 0/1/2/9; and an intake stops at the first check with a
>   blocking finding.

## 1. Isolation principle

**Rule.** A contributor update lands only in an isolated lane; it never writes into the core lane directly.
Three lane forms are canonical:

1. **Subdirectory lane**; the update is deposited under its own directory and carries its own manifest; it
   is unregistered by design and stays outside the build and certification face of the core lane.
2. **Namespaced lane**; the update is registered in the core registry books under a lane-namespace prefix,
   inside a delimited contrib segment (§2).
3. **Topic-branch lane**; the update stays on a branch and earns its CI evidence there, before intake.

The lane form is chosen at deposit time and recorded in the update's own manifest or intake record; a mixed
update (part registered, part not) is split or rejected.

**Precedent anchors.**

- Subdirectory lane: Main `y_e1_gamma_nodes/`: 92 `.v` files plus `MANIFEST.json` plus `README.md` deposited
  by PR#9 at repository root, then mirrored into `ConstructiveWorld_Live/y_e1_gamma_nodes/` (a 94/92 dual
  point). The manifest self-declares the lane: "channel: fork sandbox branch; no CI trigger; the gamma line
  is not registered in the Main tree (no GaC files, no order.txt rows)", with per-node acceptance carried by
  the manifest itself (six-chain: lint/gate4/compile/coqchk/print_assumptions/md5_ledger). All four registry
  books grep `y_e1_gamma_nodes` with zero hits (Live/order.txt 1104 lines, vo/order.txt 1056, Live/_CoqProject
  1001, vo/_CoqProject 955); the deposit never touched a core registry row (subdirectory-survey section
  of `docs/勘形-Main新内容预热-20261113.md`).
- Topic-branch lane: Set branch `fix/route2-tierA-supply-20261112`: the route2-tierA supply (7 pieces) was
  developed and CI-validated entirely on the branch (runs #301/#302 failing → restore commit `bd8f38b` →
  runs #303/#304 passing, a 20-minute monitor → classify → automatic-recovery loop with zero human
  intervention, recorded in `docs/判例-R3复发-route2tierA自愈-20261113.md`, case-timeline and recovery
  sections); main absorbed the supply
  commit `9b9631b` and the mac-lane restore `074eaa4` afterwards. All evidence was earned before the core
  lane changed.
- Negative anchor (what isolation prevents): PR#48, head branch `landing/g1-pipeline`, carried registry rows
  that collided with main's regenerated tail zone (mergeable=False, mergeable_state=dirty; `order.txt`
  +554/−537 and `_CoqProject` +15); a registry-crossing update whose books were regenerated against a
  different mainline. §4 is the cure; the prevention is that registry rows cross the lane boundary only
  through the §3.4 merge check.

**Invariant.** The core lane's registry books, build surface, and certification surface change only through
the §3 pipeline; every other write a contributor makes stays lane-internal.

## 2. Lane-placement specification

**Directory convention.** Contributor-owned files live under `contrib/<lane>/`, where `<lane>` is the
contributor or topic short name (lowercase, hyphen-separated, no spaces). Anything a contributor pull request
adds outside its lane directory must be justified in the intake record; the default answer is that it does
not. A bulk proof deposit that must stay outside the build and certification face uses the subdirectory lane
of §1 with its own `MANIFEST.json` and `README.md`, exactly as the Main `y_e1_gamma_nodes/` deposit did.

**Registry namespace prefix.** When contrib content is registered, its `order.txt` key is path-shaped:
`contrib/<lane>/<module>.v`. The key extractor splits an order row at the first `#` and keeps everything
before it (`tools/registry_union.py:160-167`), so a path-shaped key flows through the union, audit, and fix
tools unchanged. Path-shaped keys already have one precedent in the core books (the flat `order.txt` row
`Local/LW0LeibSeparation.v#R160-eb42d3`); a contrib segment turns that exception into an expected second key
form, and the intake record states the expected path-key count so the audit account is read against a known
shape, not as surprise drift.

**Registry isolation row segment.** Contrib rows sit in a delimited tail segment of `order.txt`:

- The segment opens with a separator comment line of fixed form `# --- contrib lane rows below ---`. A
  comment line has an empty key (`key_of` returns None), so the union operation preserves it verbatim on the
  main side and never inserts one from a branch side (`tools/registry_union.py:160-167`); the separator is
  therefore stable under every merge.
- Core rows stay above the separator; contrib rows stay below it. A core-lane append and a contrib-lane
  append then touch different zones of the book, and a reviewer can enumerate the lane with a single grep
  for the separator.
- The `#R<seq>[-<md5_8>]` anchor discipline is lane-independent: anchors inside the contrib segment obey the
  same canonical form (`tools/registry_audit.py:119`), and the audit's four accounts; duplicates, anchors,
  orphans, live topology (`tools/registry_audit.py:27-39`); apply to contrib rows exactly as to core rows.
- `_CoqProject` carries the same namespace: contrib module lines are `contrib/<lane>/<module>.v`, which the
  coqproject key extractor reduces to the bare module name (`tools/registry_union.py:164-166`).

**Which lane, when.** Default = topic-branch lane until intake. Registered contrib content = namespaced rows
in the delimited segment. A deposit that must not enter the build or certification face at all = subdirectory
lane with manifest self-declaration. Moving between lanes (for example promoting a subdirectory deposit into
registered rows) is itself an intake and runs the full §3 pipeline.

## 3. Intake pipeline: four checks, each fail-loud

A contrib lane enters the core lane only through the pipeline below, in this order; each check is a hard
stop; a check whose output shows a blocking finding halts the intake with no partial integration and no silent
downgrade.

### 3.1 Audit check (registry hygiene)

Run the read-only auditor on the two registry books before anything else; it writes nothing and emits the
four accounts plus, on demand, a deterministic prescription:

```
python3 tools/registry_audit.py --order order.txt --project _CoqProject --live-src <live-tree> --fix-plan --json intake-audit.json --md intake-audit.md
```

Blocking surface: a duplicates, anchor, or orphans finding that touches contrib rows blocks the lane until
the prescription is applied through `tools/registry_fix.py` (§4). Exit semantics as implemented: findings
are data and the tool exits 0 with a loud account; 2 = usage error and 9 = missing input are hard stops.
A subdirectory deposit (§1) is expected to surface as `live-extra` rows ("on disk, not in the book") because
the audit's topology account walks the live tree recursively while the flat CI scans do not; the asymmetry
is registered in the intake record as the lane's known shape, not treated as an unexpected failure (Main
subdirectory survey, decision demand D2).

### 3.2 Norm check (annotation faces)

Run the report-only linter on every prose face the lane adds:

```
python3 tools/norm_lint.py --file contrib/<lane>/README.md --jargon-map docs/jargon-to-standard-mapping-v1.md --json intake-norm.json --md intake-norm.md
```

(or `tools/norm_lint.py --tree contrib/<lane>` for the whole lane at once). Required surface: the two-part
header (banner line plus the five-field block `Purpose.` `Interface.` `Dependencies.` `Evidence.`
`Exit-codes.` verbatim, within the 30-line budget, `tools/norm_lint.py:83-85`) and zero error-level
findings; a mapping-table jargon face at any prose position blocks the lane. New contrib files are
English-only per the Annotation Standard Card §5.3, so zero CJK outside backticked citations is the target;
warn-level findings (date stamps, header budget) are listed in the intake record, not hidden. The linter's
exit code never escalates on findings (report-only by design); the gate is the finding surface itself.

### 3.3 Gate check (CI visibility expectations)

The lane must be visible to the target repository's CI gates exactly as its lane form intends; visibility
is decided by the lane form, never discovered by accident:

- Registered namespaced rows: the order.txt-driven extraction gate `gate7` (it reads "for every order.txt
  module") and the census gate `gate6` (it walks top-level `.v` globs) must cover the contrib rows. A
  registered row that the build tree cannot reach is an expectation mismatch and blocks intake.
- Unregistered subdirectory deposit: constructively invisible to `gate6` and `gate7`; the flat
  comment-guard scan `gate4` emits a loud per-run warning when subdirectories exist (observed live on Main
  run#50, log line 1391, two subdirectories unswept). The deposit's acceptance is the manifest-carried
  per-node six-chain of §1, and the `gate4` warning is recorded as known-state.
- The per-row choice (registered vs. manifest-gated) is the Main-side decision set the survey registered as
  D1/D3; the intake record states it explicitly rather than leaving it to the scanner's silence.

### 3.4 Merge check (registry union operation)

Registry rows cross into the core books only through the union operation; never through a hand edit, and
never through a plain git merge of two independently regenerated books:

```
python3 tools/registry_union.py --git <repo> --ref-base <merge-base> --ref-main main --ref-branch <lane-branch> --kind order --out order.union.txt --apply --json union-order.json
python3 tools/registry_union.py --git <repo> --ref-base <merge-base> --ref-main main --ref-branch <lane-branch> --kind coqproject --out _CoqProject.union.txt --apply --json union-project.json
```

Semantics as implemented (`tools/registry_union.py:3-61`): the main current version is the output's base,
preserved line-by-line; only rows present on the branch and absent from the merge-base are appended:
extracting against main instead would misread same-key-different-anchor generation rows as new
(`tools/registry_union.py:191-212`); three assertions fail loud at exit 2 with zero writes (A1 internal key
uniqueness, A2 added keys not already in main, A3 no new anchor-text duplicate pairs,
`tools/registry_union.py:215-263`); line endings and the final newline follow the main side; the run is a
dry run unless `--apply` is given with an explicit `--out`.

## 4. Regeneration rule (registry tail-zone collisions)

Trigger: a contributor pull request carries regenerated registry books and reports mergeable=False /
mergeable_state=dirty because both sides appended rows to the same tail zone against their own mainlines
(PR#48: `order.txt` +554/−537 and `_CoqProject` +15, with the blob-level divergence concentrated in exactly
those two books; `docs/判例-R3复发-route2tierA自愈-20261113.md` §6.2/§6.3). A line-level merge of two
independently regenerated books is infeasible and is never attempted.

Prescription (PR#48 case law): **regenerate on the current main line.** The contributor rebuilds the pull
request's registry rows against main's current tip, re-using the method of the pull request's own regenerate
commit (`d389dc2`, "regenerate on main lineage") with the baseline moved to the current mainline, and the
pull request is then re-evaluated. The reviewer side never hand-edits a collided book.

Mechanical face; the prescription is emitted and applied by tools, not by hand:

```
python3 tools/registry_audit.py --order order.txt --project _CoqProject --anchor-src <live-tree> --fix-plan --json regen-audit.json
python3 tools/registry_fix.py --audit-json regen-audit.json --order order.txt --project _CoqProject --anchor-src <live-tree> --apply --work-dir <work-dir> --json regen-fix-report.json
```

`tools/registry_audit.py --fix-plan` emits three deterministic prescription kinds (DEDUP keep-first, anchor
re-stamp, ORPHAN-ADD template) and never writes; `tools/registry_fix.py` applies them one by one; dry run
by default, staging in memory, per-row md5 accounting, three post-apply assertions (treated keys show zero
duplicate residue, no new anchor-text duplicate pairs, no orphan growth) with automatic rollback and the
evidence in the report on any failure (`tools/registry_fix.py:11-35`). Where rows must be re-anchored rather
than deduplicated, `tools/registry_union.py --reanchor <name1,name2> --anchor-src <dir>` rewrites the named
rows to the canonical anchor form `#R<seq>-<md5_8>`: sequence number preserved, fingerprint recomputed from
the on-disk entity (`tools/registry_union.py:81`, `:300-346`).

The same rule covers the reverse direction: PR#48's eight witness files proved byte-identical (8/8
blob-SAME) to their Main-tree versions, which is what made "regenerate the rows, keep the file blobs" the
correct shape; file content that is already canonical is never regenerated; only its registry rows are.

## 5. Two-stream collaboration etiquette

The mechanical pipeline of §3 presupposes a human-side discipline; the v53 constitution base release ran two
work streams over the same domain and landed them with zero conflicts, and this section fixes that record as
etiquette (frozen ledger `更新账.md` v53 entry, dual-stream case record, law two field-tested):

1. **Fetch before claiming.** Before claiming a number, an issue, or a work item, fetch the remote state and
   read the latest tip of the core lane (`git fetch origin`, then inspect the tip); a lane is never planned
   against a stale mainline. This feeds the §3.4 merge check directly; a stale merge-base misclassifies
   generation rows as unique.
2. **Canonical-first.** When two streams produce the same face, the first canonical write wins and the later
   duplicate is dropped; never merged, never re-adjudicated. The duplicated standard card and mapping table
   of the base release were resolved exactly this way.
3. **File-face layering.** A stream writes only its own files and never touches another stream's output;
   frozen surfaces (the frozen eight files, `quad8`, the frozen ledger `更新账.md`) are read-only citation
   surfaces for every stream. Layering extends across faces: a stream that owns a tool face owns its
   docstrings; a prose-only stream never edits code identifiers, CLI flags, schema field names, or exit-code
   semantics (the Annotation Standard Card §5.4 zero-change boundary).
4. **Record, don't narrate.** Each stream records what it dropped (paths, self-check results, exit codes) in
   its own intake record; a sibling stream consumes the record, not the working tree. Process narration
   stays out of prose faces; the record states facts, and the §3 pipeline consumes those facts.

The etiquette is the complement of the pipeline: fetch-first keeps the merge-base true, canonical-first
keeps the core lane single-headed, and file-face layering keeps every check of §3 attributable to exactly
one owner.
