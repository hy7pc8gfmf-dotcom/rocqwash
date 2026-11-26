# seeds/jargon: E2 banned-face-to-standard mapping seed (rocqwash-jargon-map/1)

Purpose.  Data seed for the jargon engine (E2): the machine-readable
  banned-face-to-standard mapping `jargon-map.json` plus this SPEC,
  transcribed read-only from the ConstructiveWorld annotation-standard sources.

Interface.  `jargon-map.json` (schema `rocqwash-jargon-map/1`; keys: schema, engine,
  seed_role, face_language, count, selection_rule, boundary_note, provenance (the
  v2 pin form: per source a locator, a repository-relative path, a pin object whose
  kind matches the locator, the informational upstream_path on external sources),
  entries; per entry: id, face, standard, standard_language, standard_source,
  source_line, disposition, exempts, cross_track_note, note), `SPEC.md`,
  `test_snippet.py` (merged into `tests/t_engines_seeds.py`).  Detection: project
  the JSON per section 2 and run `norm_lint --jargon-map` on the projection; raw
  JSON input fails loud.  Application: `wash_shape --apply` has no jargon face yet.

Dependencies.  `tools/norm_lint.py`, `tools/wash_shape.py` (absence probe), the pinned provenance faces
  in the v2 form (the committed mapping-table blob by its git blob sha; the two external authorities as
  in-repo snapshot copies under `seeds/jargon/_snapshots/` judged by md5 over CRLF-to-LF normalized bytes
  (EOL-agnostic fingerprint: content identity, not line endings; the `.gitattributes` normalization law),
  each upstream original an informational locator only a canonical machine can hash), the mapping table
  `docs/jargon-to-standard-mapping-v1.md`; Python 3 standard library only.

Evidence.  `test_snippet.py` asserts the data contract (provenance v2), the two-source
  transcription containment (snapshot verbatim; in-repo-md-v1 vs the md table), the v2
  pin checks (repo blob sha vs HEAD; snapshot md5; upstream freshness or declared skip),
  the detection round-trip, and the exemption, silence, fail-loud loader faces.

Exit-codes.  `test_snippet.py`: 0 no FAIL; 1 at least one FAIL (listed, fail-loud); missing
  externals yield loud SKIP lines; `norm_lint` keeps its own contract (0/1/2/9).

## 1. Scope and engine slot

- Five-engine slot: E2 (jargon). The seed fills the data-face gap: the
  annotation-track banned-face base and its standard replacements did not
  exist as machine-readable data inside this repository.
- The seed is data plus a testable contract only. The detection entry point
  already exists (`norm_lint --jargon-map`, parameterized); the application
  entry point exists without a jargon face (`wash_shape --apply`); both
  engine faces grow on the engine side, fed by this seed.

## 2. Detection face: ready to use through a fixed projection

- Loader contract (`tools/norm_lint.py:154-188`): the jargon map is a
  pipe-table file; data rows carry at least three cells (face, standard,
  note) plus an optional fourth cell of `;`-separated exempt regexes applied
  line-scoped; rows whose first cell is empty, carries the loader's CJK
  header marker, or is a dash run are skipped; duplicate faces are rejected
  (exit 1); a file with no active rows is rejected (exit 1); a missing file
  exits 9.  Loading and matching details: CJK faces match under a
  whole-word adjacency rule; backtick spans are masked on the jargon and CJK
  faces alike; markdown link destinations are likewise masked on the jargon
  and forbidden faces (a cited path is an identifier position, reading rule
  1 of the mapping table); the loaded table itself is exempt from its own
  check (`tools/norm_lint.py:617-618`).
- Projection rule (deterministic, defined here, exercised by the tests):
  one data row per entry: face cell = `face`; standard cell = `standard`
  when `disposition` is `replace`, otherwise the fixed suggestion string
  `rewrite per context or delete (no fixed standard recorded)`; note cell =
  a short source tag; exempt cell = `;`.join(`exempts`) when non-empty.
  Row grammar allows the tests to emit the separator-first ASCII variant;
  a human-facing projection carries the house header row, which the loader
  skips by its first-cell rules.
- Command shape: `python -I tools/norm_lint.py --tree <target> --jargon-map
  <projected-table.md>` (report-only form; findings are data, the exit code
  never escalates on them).
- Registered gap (grow phase, engine side): the loader has no JSON input.
  Handing the raw JSON path to `--jargon-map` exits 1 with "no active rows",
  which is fail-loud by design and asserted by the tests.  A JSON-native
  loader is engine work; this seed deliberately ships none.

## 3. Application face: wiring pending (`wash_shape --apply`)

- Verified absence at casting time: `jargon` does not occur in
  `tools/wash_shape.py` (first-hand probe, section 5).  `wash_shape` is the
  plan/apply executor of the five-wash pipeline: default plan with zero
  writes; `--apply` executes would-fix items and re-runs the washes for
  verification.
- Wiring candidate for the grow phase: a jargon wash face consuming this
  map's `replace` entries only.  Hard rules for that face, derived from the
  data: `rewrite_or_delete` entries are never machine-applied; guarded rows
  (rows whose `note` records a sense split or a context guard) need per-row
  handling before any apply; the preserve carve-out rides the loader's
  exempt mechanism, not blind string replacement.
- Single-track rule: the evolve loop already consumes `norm_lint` signals
  for replacement candidate generation; the jargon apply face should extend
  that loop rather than fork a second replacement path.
- This seed ships no apply code.  The tests carry a drift sentinel: if
  `jargon` ever appears in `tools/wash_shape.py`, the probe fails with an
  instruction to update this section.

Integration note (the engine-body ticket, integrated this round).  The wiring
candidate above has landed: the jargon wash face is wash 6 in
`tools/wash_shape.py`, driven by `tools/jargon_apply.py` with this map
read-only, under the hard rules this section lists (replace entries only;
`rewrite_or_delete` never machine-applied; guarded rows refuse by default
with the `--guarded-interactive` query hook; carve-outs ride the exempt
mechanism; backtick masking).  The drift sentinel in
`tests/t_engines_seeds.py` (`check_wash_shape_gap`) flipped at this integration
to assert the wired state: `jargon` now MUST appear in `tools/wash_shape.py`,
and the probe fails if the wiring is removed.  The original section text
above stands unchanged as the pre-integration record.

## 4. Selection rule and the 62-count label

- Mandated count: 62 entries.  Fill rule: the document-order prefix of the
  consolidated banned-word list in the annotation whitepaper snapshot
  (in-repo copy self-declares v1.8): faces 1 through 62.  The snapshot's
  consolidated list carries 115 faces; the list continues beyond the prefix
  and those faces remain banned by the source.  The prefix boundary is a
  seed-size decision, printed in the JSON itself (`selection_rule`,
  `boundary_note`).
- Composition under the fill rule: 46 entries carry annotation-track
  standard cells (whitepaper mapping table), 13 carry tool-track standard
  cells (`docs/jargon-to-standard-mapping-v1.md`, used for faces absent from
  the annotation-track table), and 3 entries have no fixed standard recorded
  in any in-scope source and carry `disposition: rewrite_or_delete` anchored
  to the whitepaper's rewrite-or-delete rule for engineering-metaphor
  process wording.
- Count-label findings (first-hand mechanical counts at casting time): the
  consolidated list carries 115 faces; the gate4 verifier
  (`verify/gate4_comment_guard.py`, identical across all three checked-out
  copies) carries 67 strings self-labeled as the 65-face base; the
  operational scan list file carries 85 lines while its receipt says 82; a
  legacy receipt calls the base "62 words" before a 21-face addition batch.
  No on-disk artifact contains exactly 62 faces.
- Negative finding on the 62-label, four elements.  (1) Scanned: the
  whitepaper snapshot's consolidated list (mechanical split), the three
  gate4 verifier copies (string counts), the tool-track table row census,
  the operational scan list file, and the legacy receipts quoting the label.
  (2) Not scanned: pre-revision whitepaper snapshots in the backup domains
  that the whitepaper's own revision notes reference (outside this seed
  casting's allowed boundary), and the restricted backup root.  (3) Not an
  absolute claim: the label's exact historical 62-face snapshot may exist in
  those unscanned domains.  (4) Aliased equivalents: face batteries under
  other file names or embedded in other verifiers were not exhaustively
  ruled out.  Consequence: the mandated count is carried as a stated prefix
  cut, not as an identification of the historical label.

## 5. First-hand runs backing this SPEC

All runs executed during this seed's casting session, on the casting
machine, against the sources pinned in the JSON `provenance`:

- `python -I tools/norm_lint.py --selftest`: rc 0, six vectors PASS
  (map-load, jargon-hit, fields-missing, substring-exemption,
  whitelist-exemption, english-clean).
- `python -I tools/wash_shape.py --help`: rc 0; plan/apply usage face
  present as described in section 3.
- `grep jargon tools/wash_shape.py`: no match (absence probe).
- Mechanical counts of section 4 (consolidated list split, gate4 string
  counts, scan-list line count): each produced by a standard-library
  Python one-off over the pinned files.
- The seed JSON was written by a throwaway generator that copied the face
  list and the standard cells by program and asserted per-entry containment
  before writing; `test_snippet.py` re-asserts the same containment against
  the current files on every run, so upstream edits to the originals turn
  the containment or md5 checks loud (the sync discipline of the read-only
  snapshot, mechanically enforced).

## 6. Boundaries

- Identifier positions (code identifiers, CLI flags, schema field names,
  file names, exit-code tokens) are never rewritten; tool names that embed a
  banned family word stay as identifiers, cited in backticks.
- The annotation-track standards are Chinese; the tool-track standards are
  English; each entry states its `standard_language`.  Track discipline: the
  standard column of an entry comes from exactly one track (stated per
  entry); cross-track rows are quoted as notes only, never merged into the
  standard column.
- The JSON keys and this SPEC are English per the seed discipline; the
  faces themselves are Chinese data (they are the banned surfaces).
- glossary section 4.5 (the deprecation list) contributes the cross-track
  row quotes and boundary statements only; its own additional deprecated
  faces (the screening, review-round numbering and similar families) lie
  outside the 62-face prefix and are enumerable from that source; they are
  not silently dropped; this boundary statement is their register here.

## 7. Transcription containment sources (the in-repo-md-v1 contract)

- The transcription contract carries two containment sources.  Source 1 is
  the pinned authorities: entries tagged `annotation-whitepaper` are
  verbatim against the pinned whitepaper snapshot; entries tagged with the
  original tool-track style (`(tool-repository track)`) carry
  whitepaper-verbatim standards under this contract and their containment
  source is the whitepaper.  Source 2 is the in-repo derivation: entries
  the sync admitted from `docs/jargon-to-standard-mapping-v1.md` carry the
  tag `(in-repo-md-v1)` (it extends the tool-track prefix so the applier's
  A2 gate keeps scoping them), and their containment is that table itself:
  the entry's standard must equal the paren-stripped standard cell of the
  face's single md row, derived by the same rule the sync uses (fullwidth
  and ASCII parenthetical annotations stripped, em-dash head as
  rewrite_or_delete, a surviving ` / ` or its fullwidth counterpart
  rejected as an alternation guard).
- Machine availability is the point of the second source: the md table and
  the sync tool are repository faces, so `check_md_containment` (in
  `test_snippet.py`, mirrored in `tests/t_engines_seeds.py`) runs on every
  machine and never depends on the pinned originals; a run with zero
  in-repo-tagged targets fails loud instead of passing vacuously.
- The four diverged originals (J012, J046, J061, J098) revert to their
  whitepaper-verbatim zh standards (the cast values, recoverable from the
  map's git history) and keep the original tool-track tag: the md's
  single-form suggestions for these faces were a mechanical normalization
  that contradicts the whitepaper register, and the register authority
  stays with the whitepaper until its owner updates it.  Machine apply
  returns to guarded for them (note-guard J012/J046, alternation-guard
  J061/J098); the md keeps the single-form suggestions, so detector and
  applier may differ on these guarded faces.
- Sync provenance rules under the same contract: every row the sync writes
  or already owns carries the in-repo source; an admitted row whose
  existing entry has an equal standard is retagged from the legacy
  tool-track style to the in-repo source (action `retagged`, the
  re-admission mark of this contract; 122 rows at this contract); an
  admitted row whose existing entry has a zh standard is a whitepaper-track
  transcription and is never machine-superseded (action `authority-kept`).
  The applier's A2 gate scopes to the in-repo-md-v1 rows (122/122 equal at
  this contract); the four authority rows sit outside that gate by the
  contract above.
