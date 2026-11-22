# audit-ConstructiveWorld_Live-20261111.json: baseline production-account note / `产账说明`

> Purpose.  Sidecar note for the K=1 audit baseline `examples/baselines/audit-ConstructiveWorld_Live-20261111.json`:
>   records how the baseline was produced, what the candidate set was, and what the account concluded.
> Interface.  Document face (annotation only). It documents one recorded `tools/unclog.py --audit` run;
>   the JSON carries the data (args / timing / conclusion) and no program reads this note.
> Dependencies.  `tools/unclog.py --audit`, the runner workspace Live APFS clone (537 vo, serving
>   generation), the 27-piece candidate TSV, and the opam93 `coqc` binary named in the recorded
>   command; the run is `cpu_guard`-wrapped.
> Evidence.  The recorded command and its outputs are the JSON's own `args` / `timing` fields; the
>   27/27 RC0 conclusion is re-derivable by rerunning the same audit command against the same inputs.
> Exit-codes.  Not applicable (document face); the documented audit keeps its implemented exit-code
>   semantics (rc=0 produced; rc=127 environment-cause failing) unchanged.

- Production run: `tools/unclog.py --audit --src <Set 仓 ConstructiveWorld_Live> --world <runner 工作区 Live APFS clone（537 vo·现役代际）> --candidates <27 件 TSV> --rocq-cmd '…/opam93/rocq93/bin/coqc -native-compiler no -q -Q . "" {name}.v'` (wrapped in `cpu_guard` · the zero-disk-write hard guarantee held).
- Candidate set: the 27 pieces landed by the two batches of November 10, 2026 (b48-52 thirteen + b53-57 fourteen · md5 measured and backfilled into the TSV).
- Conclusion: **27/27 RC0 (`red=0`)**; the newly landed faces are all closure-compatible against the serving world generation; walls = 0; `cures_planned=0` (the audit is read-only).
- The `timing` section (enumerate null / manifest 1.289 / probe_chain 190.728 / total 194.086 s) is the only non-deterministic section · excluded from baseline comparison (registered in the `baseline_diff` `excluded_fields`).
- Run history: the first attempt failed with rc=127 for an environment cause (the compiler binary was missing) → the second attempt the same · **the honest wall correctly refused to judge, nothing force-fitted** ("generation-gap type / environment-cause failing") → the third attempt, carrying `--rocq-cmd`, produced the account; a field record of the tool's honesty design holding under real use.
