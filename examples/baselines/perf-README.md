# examples/baselines/perf-README.md: probe profile collection protocol

> Purpose.  Companion to [`README.md`](README.md) (the blockage-record baseline intake and comparison protocol): that page governs the result axis (the failing-run and wall accounts · degraded is a fallback signal), this page governs the speed axis (the probe profile · timing-section differencing). **Two-axis separation rule**: the profile's object is exactly the baseline file's only non-deterministic segment (timing), so profile records and the blockage-record baseline are kept on separate axes and their readings never cross (the mirror of README §4 "human reading must not assert results from timings" · result reading never uses timings either · speed reading trusts only the timing section). The profiled tool = `tools/unclog.py --audit` (the probe-collection segment is the absolute majority of a real-compile run · 98.3% measured · the measurement report's section 2).
> Interface.  Document face (collection protocol, not executable). Governs: the profile target (the `report["timing"]` section, schema `rocqwash-unclog/1`, plus the `jobs` dimension); the three-step collection method (fix the face / three runs K=1,2,3 via `--probe-parallel K` / segment diffing); the wall-clock non-determinism reading rules; the ≤30-piece sample cap; the record template. Cited as the collection-method canon by the companion measurement report and by the `tools/unclog.py` docstring.
> Dependencies.  Document face only; the documented tool faces `tools/unclog.py`, `wash/probe_engine.py`, `tools/cpu_guard.sh`, and the sibling [`README.md`](README.md) baseline protocol; no runtime dependency.
> Evidence.  Every measured number in this protocol (the 98.3% probe-chain segment share · 190.728 s per K=1 run · ≈7.06 s/piece serial · the 0.078→0.102 same-K rerun pair) is transcribed from the measurement report `docs/perf-profile-v1.0-20261111.md`; the protocol states method and caps, introduces no new measurements, and invents no numbers.
> Exit-codes.  Not applicable to a document face; the documented tools keep their implemented exit-code semantics unchanged.

## 1. The profile target (the timing section and the jobs dimension)

`--audit` reports `report["timing"]` (schema `rocqwash-unclog/1`):

```json
{"enumerate_s": null, "manifest_s": 1.289, "probe_chain_s": 190.728,
 "total_s": 194.086, "jobs": 1}
```

- `enumerate_s` (the `--src` full-tree enumeration segment · null when the face is fed via `--candidates`) and `manifest_s` (the pre-run md5 manifest segment) are environment-noise segments; `probe_chain_s` (probe collection + `chain_graph`) is the profile's headline metric; `total_s` is the cross-check segment.
- The `jobs` dimension = the `--probe-parallel K` argument (the value passed through to `wash/probe_engine.py --jobs` · default 1); recorded starting with v41; an absent slot (v40-era reports) means K=1 serial, directly comparable with a new report's `jobs:1`. Runs over the same candidate face with different K, before and after, are aligned by this field.

## 2. Collection method (the three steps of probe --jobs K profile collection)

**Step 1 · fix the face**: supply the candidate face directly via `--candidates TSV` (enumerating from `--src` injects enumerate noise) · one TSV reused across the three runs; pin `--src/--world/--rocq-cmd/--timeout`; the `args` section is recorded in full every run · cross-run comparability presupposes an identical args section (any differing key is a spurious signal · never compare).

**Step 2 · three runs**: one run each at K=1/2/3 (`--probe-parallel K`) · each emits its account with `--json`; name the accounts `perf-<domain>-k<K>-<yyyymmdd>.json` (`<domain>` = the candidate face's domain · the README §2 naming rule on a separate axis; the perf prefix stays out of the `audit-` baseline series · keeps the differencing tool from mispairing):

```bash
python3 tools/unclog.py --src <source-tree-root> --world <world-dir> \
  --candidates <face>.tsv --audit --probe-parallel <K> \
  --guard tools/cpu_guard.sh --guard-reg <registry-dir> \
  --json /tmp/perf-<domain>-k<K>-<yyyymmdd>.json
```

**Step 3 · diff**: put the three runs' timing segments side by side · read the K effect from `probe_chain_s`; use `manifest_s`/`enumerate_s` as noise references; cross-check with `total_s`. The K effect on real-compile runs is read only from the three-run trend (the magnitude of a segment's values across K) · never from a single run's milliseconds (§3).

## 3. Wall-clock non-determinism note (three reading rules)

The timing section is measured wall clock and differs on every run (the report's only non-deterministic part); demonstrated by two same-command K=1 runs on the tmp fixture: probe_chain_s 0.078→0.102 (`docs/perf-profile-v1.0-20261111.md` section 3 · the A/B runs). The three reading rules:

1. **A single run concludes nothing**: rerun once at the same K to draw the noise band (the spread magnitude of the two runs) before reading the K effect;
2. **The identity prior**: except for the timing section (and the `args.probe_parallel` argument itself) · a same-input rerun is identical key by key; any out-of-scope key in a diff means fixture/parameter drift · discard the account and resample;
3. **Canned runs are not a profile**: `--injector` canned mode does zero real compilation · K is bypassed but still recorded (the mechanism is measurable · the speedup is not); a wall-clock profile must come from real-compile runs.

## 4. Recommended sample size (≤30 pieces · thermal control)

- **Candidate face ≤30 pieces**: the 27-piece precedent (`audit27.tsv`) runs real compiles serially at ≈7.06 s/piece · 190.728 s per run (v40 audit measurement · report section 2); the three K=1/2/3 runs total wall-clock minutes · both the per-face capacity and the thermal window are capped at ≤30 pieces; larger faces run in batches per domain.
- **Thermal control**: wrap every execution in `bash /Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh`; real-compile runs add `--guard` (probe_engine wraps every piece through the guard · the FRONT profile applies its own clamping); K>1 = multiple concurrent rocqworker processes on one machine = higher thermal load; K=2 is the advised level · stagger a K=3 run against earlier runs (thermal caution from the same source in the `wash/probe_engine.py` docstring · an advisory note, not enforced · the user decides).
- **Real-tree audit live runs belong to the main session** (`tools/unclog.py` docstring · the same rule in README §3); the perf side proves the fixture level only · the main session executes the real-tree three runs per this protocol.

## 5. Record template

```markdown
## probe profile record (<domain> · <yyyymmdd>)

- face: --candidates <face>.tsv (N pieces ≤30) · src=<source-tree-basename> · world=<world-basename>
- rocq_cmd: <template verbatim> · guard=<profile> · producer=<agent/main session>

| run | K | timing.jobs | enumerate_s | manifest_s | probe_chain_s | total_s | rc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 |  |  |  |  |  |  |
| 2 | 2 |  |  |  |  |  |  |
| 3 | 3 |  |  |  |  |  |  |

- noise band: a same-K rerun pair (K=1) segment-value spread = <...>
- reading: probe_chain_s trend across K = <...> · identity check = PASS/FAIL
- output: /tmp/perf-<domain>-k{1,2,3}-<yyyymmdd>.json (volatile · citing it in a docs/perf-profile-*.md report transcribes it into the repository)
```

## 6. Current-state boundary (v41)

- The `timing.jobs` dimension is recorded starting with v41 (frozen as vector ⑬ of `tools/unclog.py --selftest`); the absent slot in v40-era reports means K=1 and is semantically comparable.
- The first collection of the real-compile K=1/2/3 three runs has not been done (real-tree live runs belong to the main session); placeholders and measured progress are in `docs/perf-profile-v1.0-20261111.md` section 5.
