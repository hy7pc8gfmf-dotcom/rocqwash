# exp-bus-backlog.md: experience-bus import backlog for tools/exp_port.py.

> **ExperienceBusBacklog**: the two experience-draft lines registered as
> pending imports for the append face, plus the observed candidate found on
> disk outside this integration's import list. Registration only; no entry is
> invented before a real draft exists.
>
> Purpose.  Keep the experience-bus intake honest: every line that promised
>   experience entries has a registered row here until its draft file lands
>   on disk, and each integration imports through `tools/exp_port.py append`
>   (schema rocqwash-exp/1) so the ledger grows only through one face.
>
> Interface.  One row per pending line: expected draft location, status,
>   and the append-face import form. Imports are per entry, e.g.
>   `python tools/exp_port.py append --tool <tool> --points <points>
>   --evidence <evidence> --batch <line>-<date> [--id <draft-id>]`.
>
> Dependencies.  `tools/exp_port.py` (stdlib only), the ledger
>   `docs/exp-ledger.jsonl`, and the draft files the pending lines will
>   write; no network face and no new tooling.
>
> Evidence.  The waiting rows rest on a name-level `find` over the attn
>   work area at the UTC moment recorded in the scan-boundary section
>   below; the observed row was read (entry count and field names) before
>   registration.
>
> Exit-codes.  No new exit codes; the import form keeps the port's own
>   0/1/2/9 contract.

## Pending lines

| Line | Draft location (expected) | Status | Import form |
|---|---|---|---|
| vacmain audit line | not on disk yet (its exp-draft is written by that line when it closes) | waiting | `exp_port.py append ... --batch vacmain-<date>` per entry |
| RQW11 (OAI replicate) line | not on disk yet (same contract) | waiting | `exp_port.py append ... --batch rqw11-<date>` per entry |

## Observed candidate (outside this integration's import list)

`attn/_vacgenv2_20261113/exp-entries-draft.json` exists on disk: 8 entries,
English field names (id/date/tool/category/points/evidencePointer/
erratumBlock/rescanCondition). It is a ready import candidate for the next
exp-bus work stream; it was not imported by this integration because this
integration's import list names the periscope 5 entries only.

## Scan boundary

The two "not on disk yet" rows rest on a name-level find over
`D:/ComplexAnalysis/attn` at 2026-11-13T19:12:58Z (`find ... -iname
'*vacmain*' -o -iname '*rqw11*'` plus `-iname '*exp-draft*' -o -iname
'*exp-entries*'`); searched by name rather than read file-by-file, and
aliased equivalents outside the attn work area were not exhaustively ruled
out. This is a negative finding of that scan, not an absolute claim. The
contract stays: whichever exp-draft file a line writes, its entries import
through the append face and become ledger rows.
