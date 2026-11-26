# Migration ledger - autonomy.json `max_unreviewed_rounds`

> Purpose.  Register one governance change to the round-admission autonomy
  record as a migration ledger line: the field changed, its old value, its
  new value, the reason, the effect on every lane that runs rounds, and
  the rollback.
> Interface.  Document face.  The changed record is `autonomy.json` at the
  repository root; its reader is `tools/auto_round.py` (the `commit` face,
  the unreviewed-round soft stop).  The file name carries the registration
  date.
> Dependencies.  None; the line cites the record it changed and the two
  constants it reasons from.
> Evidence.  The table row below: its old and new values are the literal
  values of `autonomy.json` before and after the change.
> Exit-codes.  Not applicable to a document face.

| field | old value | new value | reason | effect | rollback |
|---|---|---|---|---|---|
| `max_unreviewed_rounds` | `12` | `3` | External falsifiability.  The round verifier belongs to the verified system (`verify_cmd` is the tree's own `tools/axiom_guard.py`), so a run of unreviewed rounds has no outside check: twelve of them without a review is the direct source of the "self-validated, never externally reviewed" finding.  Three rounds also aligns one human-review period with the B-gate instance accumulation cycle (`THRESHOLD_INSTANCES = 3` in `tools/b_gate_audit.py`, one admission per round), so every B-level class ignition window is covered by exactly one human review. | Every lane that runs `tools/auto_round.py commit` (the cron round included) soft-stops once three unreviewed rounds have accumulated since the anchor: the commit refuses until a review promote (`anchor --promote`) or an explicit `--continue`.  The admission gears and every other autonomy field are unchanged. | Set `max_unreviewed_rounds` back to `12` in `autonomy.json` (a one-line edit; no other state carries this value).  This line stays on record as the migration ledger of the change. |

Registered by the capability-ratchet increment on branch `supply/rsi-capability-ratchet-20261125` (base `origin/main` = `ba47e98`).
