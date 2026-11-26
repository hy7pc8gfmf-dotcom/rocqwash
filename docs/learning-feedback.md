# learning-feedback - the scheduling feedback edge over the round accounts.

Ticket: recursive three-gap closing batch (November 19, 2026), learning-feedback lane.
Statement faces: tools/learning_feedback.py; docs/scheduling-feedback.json
  (schema rocqwash.scheduling-feedback/1); tools/evolution_dashboard.py
  (feedback section)
Source route: repo docs/ (this file; the schema is defined by the tool and
  summarized here)
Command: python -I tools/learning_feedback.py --selftest
Registry: CAPABILITY-INDEX entry added same round

> Purpose.  Compute the unread approval signal in the round records: the
>   auto versus human-approved round split and approval rate, the
>   per-class gear and confidence readings, the four-state repair outcome
>   tally, and the optional calibration reading (docs/scheduling-feedback.json).
> Interface.  `python -I tools/learning_feedback.py [--selftest]`; the
>   default run reads the three standing accounts read-only
>   (docs/round-ledger.jsonl, docs/round-state.json,
>   docs/exp-ledger.jsonl) and writes docs/scheduling-feedback.json plus
>   a stdout summary.
> Dependencies.  Python 3 standard library only (argparse, JSON and JSONL
>   reading, tempfile fixtures); the three account files as read-only
>   inputs.
> Evidence.  --selftest runs fourteen vectors on tempfile fixtures (the
>   eight standing faces, the promotion row lock, the exp_port interop,
>   and the four feedback-edge faces: closed, partial, the open kill
>   shape, tolerant-absent); zero network; fixture-tree writes; import-safe.
> Exit-codes.  0 = readings are data: a missing account or damaged row
>   lands in an errors field and the stdout summary fails loud; a null
>   repair_action_rate on a zero denominator is reported, never padded.

## Problem

Round records carry an approval signal that had no computed face. Each
round entry states whether a class entered by the auto gear or by a human
approval, and the repair records carry outcome information, but neither
number was computed anywhere: the approval rate was unaccounted and the
repair outcome mix had no readable face. This tool computes that signal;
the honest boundary is stated in its own section below.

## Inputs

All three inputs are read-only; the tool never writes them.

| Face | Role |
|---|---|
| `docs/round-ledger.jsonl` | one row per round: `round_id`, mode, `verify_rc`, `admissions[]` with `class`, gear, `confidence` |
| `docs/round-state.json` | `admitted_classes`, the admitted-class roster |
| `docs/exp-ledger.jsonl` | repair records; the outcome is not a stored column, so each row is classified from its `action` and `points` wording into `repaired`, `escalated`, or `watch_only_guard_correct`, and a row that fits none stays `unrecorded`; its `calibration_ledger` rows also feed the optional `calibration` section |

A missing or unparseable ledger is recorded in the `errors` field of the
affected section and the run continues; it is also printed in the stdout
summary (fail-loud, never silent).

## Output

`docs/scheduling-feedback.json`, schema `rocqwash.scheduling-feedback/1`:

```json
{"schema": "rocqwash.scheduling-feedback/1",
 "rounds": {"total": 2, "auto": 1, "human_approved": 1,
            "approval_rate_auto": 0.5,
            "by_class": [{"class": "jargon", "rounds": 1,
                          "gear": "auto", "confidence": 1.0}]},
 "repair_outcomes": {"repaired": 0, "escalated": 0,
                     "watch_only_guard_correct": 0, "unrecorded": 0,
                     "repair_action_rate": null},
 "calibration": {"section": "calibration", "ledger_present": true,
                 "entries": 2, "agreement_rate": 0.5,
                 "by_class": [{"class": "HIGH", "entries": 2,
                               "agreeing": 1, "agreement_rate": 0.5}],
                 "errors": []},
 "feedback_edge": {"status": "partial",
                   "scheduler_source": "tools/scheduler_lite.py",
                   "read": true, "apply_edge": true, "record": true,
                   "ledger_trace": false, "trace_rows": 0,
                   "note": "edge partial: the scheduler consumes approval_rate_auto at the plan face (read=true apply=true record=true) but the face is a subset; 0 round-ledger row(s) carry scheduling_input"}}
```

`approval_rate_auto` divides the auto-admitted round count by the total round
count, with human-approved rounds inside the denominator.
`repair_action_rate` is `repaired` over the four-state total and is `null`
when that total is zero.

Section presence: every section shown above is present on every run, and
each carries its `errors` list, empty when the account is clean and one
entry per missing or unparseable input otherwise (see Inputs).

The calibration section: an always-present section carrying optional
readings.  Rows of the experience ledger whose `tool` is
`calibration_ledger` (the writer is `tools/calibration_ledger.py`,
consumed read-only here) are read into `ledger_present` (true when the
ledger file exists and holds at least one valid row of any tool; an
absent or row-empty file reports false with null readings, stated never
padded), `entries` (the count of calibration rows), `agreement_rate`
(agreeing over readable entries, rounded to 4 decimals, `null` when no
entry is readable), and `by_class` (the breakdown by predicted grade,
sorted by name; per class: `class`, `entries`, `agreeing`,
`agreement_rate`).  An entry agrees when its predicted grade (`HIGH`
reads 1.0, `MID` reads 0.5) pairs with its measured face (`PASS` reads
1.0, `FAIL` reads 0.0) as `HIGH` with `PASS`; a `MID` row cannot agree
at value level by construction, and a `HIGH` row measured `FAIL` is the
rot shape.  A calibration row whose points text carries no readable
predicted/measured pair stays counted in `entries`, is excluded from the
readings, and is named in `errors` (fail loud, never swallowed).  The
stdout summary carries the calibration line, and calibration errors gate
the exit code like every other account.

## The feedback edge (computed, never hard-coded)

`feedback_edge.status` is computed from two carriers, both reported in the
face so an auditor can re-derive the grade from the face alone:

| Field | Meaning |
|---|---|
| `status` | `closed` / `partial` / `open` (the only three states) |
| `scheduler_source` | the scanned consumer source, reported repo-relative on the default run (`tools/scheduler_lite.py`), so the tracked file carries no machine-specific path |
| `read` | the consumed key and this document's name appear in the parsed runtime source |
| `apply_edge` | the consumption application is called in the parsed runtime source |
| `record` | the per-influence record site exists in the parsed runtime source (`schedulingInput`) |
| `ledger_trace` / `trace_rows` | round-ledger rows carrying the `scheduling_input` trace object |

Grading: `open` = no live consumption (the kill-test state; a commented-out
or deleted consumption path scans absent because the source is judged from
its parsed form, where comments do not exist, and a dead definition is not
a call); `partial` = the consumption is live at the plan face but the face
is a subset (the record site or the ledger trace is missing); `closed` =
full consumption with the trace landed on at least one round-ledger row.
An absent or unparseable consumer source grades `open` with the reason in
`note` (stated, never an error, never guessed).

The three source flags are source-level evidence read from the parsed
module (the module body minus its `selftest` face): they prove that the
consumption chain is present, not that one plan run executed it.  A kill
that keeps the apply call in place but detaches its result from the
cadence decision is not told apart by this scan; the scheduler's own
selftest carries the behavioral check on that path (a rate below 0.5 must
flip the verdict), so the two faces are read together.

The trace contract (`scheduling_input` on a round-ledger row):
`{"approval_rate_auto": <number|null>, "action": <string>, "basis":
<string>}`. The scan accepts only round rows (round_id and mode present)
whose trace object carries a readable rate and a non-empty action. No
writer embeds the object yet: the round commit face
(tools/auto_round.py) validates a strict row key set, and the scheduler
plans only and never fires. Until a writer lands and the first steered
round is traced, the honest standing grade is `partial`.

## Honest boundary

The edge grade is derived, not declared: every boolean that decides the
status is carried on the face.  What the tool does NOT do: it does not
fire rounds, so the ledger trace appears only when the round machinery
starts embedding `scheduling_input` on steered rounds; until then the
standing grade stays `partial` even with the consumption fully live, and
that is the honest reading, not a gap to be padded.

The calibration reading is consultative in the same sense: it states how
often the stored calibration entries agree at value level, and nothing
consumes it.  The admission port (tools/auto_round.py) is untouched by
this reading; an empty or absent calibration account reads null, never a
padded zero, and the agreement rule is a value-level reading of the
stored points text, not an independent re-judgment of any row.

## Selftest

`python -I tools/learning_feedback.py --selftest` runs fourteen vectors on
temporary fixtures: one auto plus one human round; malformed-line tolerance;
empty ledgers; all four outcome states unrecorded; the three calibration
forms (a populated calibration account, an empty or absent ledger, a
calibration row with no readable pair); the promotion row lock and the
exp_port interop; and the four feedback-edge faces (a closed edge with a
live consumer and a trace row, the two partial forms, the open kill shape
plus the selftest-face exclusion, and the tolerant-absent sources).  No
network; writes stay inside the fixture tree; importing the module has no
side effects.
