# annotation-standard: rocqwash Annotation Standard Card v1.0 (issued November 13, 2026).
> **AnnotationStandardCard**: the canonical comment/annotation standard for the rocqwash tool repository, v1.0 (November 13, 2026).
>
> Purpose.  Define the file-header form, the five-field doc block, the forbidden-word surface, and the bilingual-transition rules for every prose face of this repository (code comments, docstrings, shell help text, documentation), together with the error/warn grading a mechanical checker applies. Adapted from the M-work stream Annotation Card (October 25, 2026) into the tool-repository context; Appendix A (`docs/jargon-to-standard-mapping-v1.md`) supplies the per-word replacement table.
>
> Interface.  Applies to `*.py`, `*.sh` (including `cw.sh` help text), and `*.md` prose faces repo-wide. Consumers: translation-replacement work, the future mechanical checker, and review gates. Five-field names are spelled exactly `Purpose.` / `Interface.` / `Dependencies.` / `Evidence.` / `Exit-codes.` (trailing period mandatory, verbatim).
>
> Dependencies.  Grounded in three read-in-full base assets: the JARGON filter list v0.9→v1.1 (§9.1 of the ConstructiveWorld paper-construction methodology whitepaper v1.0, the paper-track filter list), the Annotation whitepaper §4 mapping table v1.0→v1.8 plus the 65-face consolidated banned-word list enforced by `verify/gate4_comment_guard.py`, and the M-work stream Annotation Card (October 25, 2026). The first source is cited by its verbatim title and archive path in Appendix A §0. Repository state reconciled before any version citation: v52, `79a766c`, clean tree (November 13, 2026).
>
> Evidence.  Lineage: M-work stream five fields Mission./Dependencies./References./Constructivity./Build. are renamed to the tool-repository five fields as Purpose.(←Mission.), Interface.(new: CLI/schema face), Dependencies.(unchanged), Evidence.(←References., absorbing Constructivity.), Exit-codes.(←Build. contract side). Header-length warn threshold follows gate4's `length_cap=30` review-grade default (gate4_comment_guard.py:379,527).
>
> Exit-codes.  For the future mechanical checker of §6: 0 = pass; 1 = error-level violations present; 2 = undecidable or usage error; 9 = missing input (fail-loud, no silent downgrade). Existing tool exit-code semantics are never altered by this card (§5.4).

## 1. Scope

1. **Object surfaces**; comments, docstrings, shell help text, and documentation prose (`*.py`, `*.sh`, `*.md`). This card governs what those surfaces say; it does not govern what the code does.
2. **Stability boundary**; code identifiers, CLI flags, JSON schema field names, file-format names, and exit-code semantics are outside this card's rewrite scope in all cases (§5.4). A standard that moved an interface would fail the repository's own doc-vs-implementation consistency checks (`tools/doc_lint.py`).
3. **Audience criterion (inherited from the `gate4` judgment principle)**; the only assumed reader of any prose face is an international reader with no internal project context. A sentence whose comprehension requires internal organization, process history, or agent topology is non-conforming even when no listed word appears.

## 2. File header (A-zone, two-part)

Every canonical file opens with a **banner line** followed by a **structured doc block**.

### 2.1 Banner line

```
# <filename> — <one-line description of the file's role>.
```

- Markdown files: the banner is the H1 line itself (`# <filename> — <one-line description>.`).
- Continuation of a long banner is allowed on the next comment line with two-space alignment.
- No invented license clauses; no version narration in the banner (version state lives in `CHANGELOG.md`/`README.md`, not per-file headers).

### 2.2 Structured doc block (five fields)

Python docstring form (shell/Markdown adapt the same block shape):

```
"""<ModuleName>: <one-line title>.

    Purpose.  <what this file checks/applies and its scope; defaults stated
      explicitly (e.g. dry run by default, write only under --apply)>.

    Interface.  <CLI invocation shape; flags verbatim; output schema name;
      interplay with the cw.sh route table. Identifiers cited in backticks.>

    Dependencies.  <Python 3 stdlib-only statement; bash 3.2 compatibility
      where routed through cw.sh; repo-relative path assumptions.>

    Evidence.  <how correctness is attested: --selftest vectors, suite
      membership under tests/, fixture/gold-standard evidence reference,
      ground-truth precedent. One sentence per attestation, no claims
      without a stated check.>

    Exit-codes.  <the implemented 0/1/2/9 semantics, described exactly as
      implemented — described, never redesigned.>
"""
```

- **Field spelling is verbatim**: `Purpose.` `Interface.` `Dependencies.` `Evidence.` `Exit-codes.`; capital first letter, trailing period, exactly this order. Missing any of the five = error (§6).
- Identifiers are cited in backticks; continuation lines indent two spaces.
- The block states facts about the present implementation only. Process narration (how the file came to be, who wrote which work stream) is forbidden (§3, §4.4).

### 2.3 Subordinate headers

Function/class/section comments: one English line stating the unit's role; no empty names, no date stamps. Shell help text: each tool's usage block states purpose, invocation, and exit-code semantics in the same five-field spirit, compressed to the cw.sh tool-table line budget that `tools/doc_lint.py` enforces (`--help-cap 25`, tools/doc_lint.py:97).

## 3. In-body comments

- **Write the reason**: why the step holds, why the branch is split, what the invariant is; mathematical/technical fact sentences, lowercase start.
- **Forbidden**: process narration (round numbers, dates, "fixed by …"), agent/agent topology narrations, engineering jargon (§4), empty flattery (`# trivial`), Chinese (on canonical faces; §5).
- Lexer trap: after a sentence-ending period inside a comment, one blank space before the next token (inherited from the M-work stream `.(*` rule, applied to `#`/`"""` faces).

## 4. Forbidden-word surface

The banned faces are classified in §4.1–4.3 and §4.4 and enumerated verbatim, one row per face, in Appendix A (`docs/jargon-to-standard-mapping-v1.md`), which supplies each face's standard replacement and sense boundary, and additionally maps a small near-standard superset (phrase-level mappings such as a failing result is data, not a tool failure and translation mappings such as checkpoint→checkpoint) that are prose-replacement targets without being hard bans. For mechanical enumerability the classification is stated here while the verbatim face lists live in Appendix A:

### 4.1 Hard faces (literal ban, multi-character, error on any prose hit)

- Campaign/organization family: role and organization nouns, work-stream and round numbering, queue-state and freeze wording, ledger data surfaces and ledger-freshness slang, handoff and other process narration, ticket assignment, task instruction, and the process-verb faces.
- Engineering-metaphor family: evidence and conclusion metaphors, build-state and gate metaphors, blockage metaphors, assembly, splice, and integration metaphors, invariant slogans, failure/pass color wording, and the remaining metaphor faces.
- Both families are enumerated verbatim in Appendix A (Tables A, B0, B, and D), the authoritative enumeration surface; a suspected face absent from that enumeration is judged by the audience criterion of §1.3.

### 4.2 Context faces (error when used in the engineering sense of their Appendix A row)

Two groups: (a) standard English terms that double as translation targets; run, failing, passing, build, watcher, triage, classification, fallback, normalize, dry run, canonical, operation, repository; (b) sense-split faces whose Appendix A row marks the banned sense in its context note (role-noun sense, engineering sense, narrative sense, internal-canon sense). A context face is an error only in the sense its Appendix A row marks. Each face's sense boundary and standard form = its Appendix A row's context note; identifier citations are exempt (Appendix A §6).

### 4.3 English slang / hyperbole faces (literal ban, word boundary, error)

The English-language slang family, banned literally at word boundary: organization metaphors, process-narration nouns, route-narration senses, hyperbole adjectives, limitation slang, and unfinished-work markers. The faces and their per-face dispositions (delete the narration, state the actual limitation, or remove) are enumerated in Appendix A Table D. Data/preset/preset-name occurrences are identifier citations, not hits (Appendix A §6).

### 4.4 Process-narration classes (error)

Agent numbers and names; effort names; date/time stamps in comments; "this round / previously / fixed by …" narrations; file-progress accounting inside headers. These are detectable as classes (inherited from gate4's judgment-principle heuristics) and are errors regardless of whether any §4.1–4.3 word appears.

## 5. Bilingual transition rules

1. **Existing Chinese docstrings/help/README prose = translation-replacement targets.** Translation replacement is the canonical form going forward: the canonical path carries the English text after replacement.
2. **Archive, never delete.** Before replacing any Chinese prose, its original is preserved in a sibling archive file `<name>.zh.md` in the same directory (for a code file `f.py`/`f.sh`, the archive sibling is `f.py.zh.md`/`f.sh.zh.md`). The existing `docs/zh/` directory form is grandfathered as an equivalent archive form. An archive file is not a canonical face: it is exempt from §2 field checks, §4 scanning, and §6 grading.
3. **New files are English-only.** A file created after this card carries no Chinese on its canonical face; its Chinese counterpart, if one is needed for the transition, is born as the `.zh.md` archive sibling.
4. **Zero-change boundary (restated)**; translation replacement touches only comments/documentation/help surfaces. Code identifiers, CLI flags, JSON schema field names, file-format names, and exit-code semantics are unchanged, without exception. Where an identifier contains a banned-family word (Appendix A §6 register), prose cites it verbatim in backticks.
5. **Canonical-face Chinese during the window**; Chinese characters remaining on a canonical face are warn-level (§6), not license to postpone: each replacement work stream reduces the residue; jargon faces inside that residue are still error-level.

## 6. Norm grading

Applies to canonical faces (all files except `.zh.md` archives and `docs/zh/` grandfathered archives).

| Level | Condition | Checker exit effect |
|---|---|---|
| error | any of the five field names missing (§2.2) | counted toward exit 1 |
| error | forbidden-face hit at a prose position (§4.1–4.4; context faces in their banned sense) | counted toward exit 1 |
| warn | Chinese-character residue on a canonical face (transition window, §5.5) | reported; exit 0 unless `--strict` |
| warn | header block longer than 30 lines (banner + doc block; threshold = gate4 `length_cap=30` review-grade default) | reported; exit 0 unless `--strict` |

Checker exit semantics: **0** = pass (warns may be present, unless `--strict` promotes them); **1** = error-level violations; **2** = undecidable or usage error; **9** = missing input (fail-loud, no silent downgrade). These are the semantics of a future checker of this card; they alter no existing tool's behavior.

## 7. Verdict method (mechanical, per file)

1. Header is two-part and all five field names are present with exact spelling (`grep` for `Purpose\.` `Interface\.` `Dependencies\.` `Evidence\.` `Exit-codes\.`).
2. No §4 face at a prose position (word-boundary scan; identifier positions exempt per Appendix A §6).
3. Chinese-character residue counted on the canonical face (transition metric).
4. Header line budget: banner + doc block ≤ 30 lines.
5. Zero-change audit: for translated files, confirm identifiers/flags/schema fields/exit-code tokens are byte-identical to the pre-translation state (diff restricted to prose regions).

A file conforming to 1–4 with residue only at warn level is transition-conforming; any error-level finding sends the file back to the translation-replacement work, citing the Appendix A row.

## 8. Appendix A

The jargon-to-standard mapping table `docs/jargon-to-standard-mapping-v1.md` (v1) is **Appendix A of this card**: it is the sole authority for per-word replacements and context-sense boundaries. This card defines the ban and grading; the appendix defines the cure. Unlisted suspected faces are judged by §1.3's audience criterion and added to the appendix by the increment procedure its §0 defines.
