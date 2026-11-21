# SOP: Periscope Six-Source Peripheral-Intelligence Sweep and Judgment-Draft Tool / `SOP · periscope 六源外围情报采集与判读草案工具`

> Purpose.  Standard-operating-procedure face for `tools/periscope.py`, the re-runnable CLI that freezes the as-built craft of the round-1 peripheral-intelligence sweep of November 13, 2026 (six-source watchlist, window protocol, watcher companion, five-section judgment draft); adjudication upgrades (three-state collision verdicts, C1 rescans, external disclosure) never happen automatically inside the tool.
> Interface.  Documents the six-flag CLI `--config` / `--out` / `--rounds` / `--netrc` / `--dry-run` / `--selftest` (section 1), the config schema `rocqwash-periscope-config/1` and the default six-source as-built list (section 2), the three burned-in behaviors (section 3), the window and watcher-companion protocols (sections 4-5), the five-section judgment-draft template (section 6), the NETRED record forms and the read-only pledge (section 7), the offline selftest and suite membership (section 8), and the operating order (section 9). The original mixed-language text is preserved in the sibling `.zh.md` archive.
> Dependencies.  Subject face `tools/periscope.py` (Python 3 standard library only) and its suite shell `tests/t_periscope_shape.py`, which stays outside the `run_tests.sh` roster; credentials supplied through a netrc file passed to curl; the default config cites the `api.github.com` and `export.arxiv.org` endpoints. Read-only document face; no runtime dependency.
> Evidence.  The selftest vectors V1-V10 (section 8) attest every documented behavior; the six flags, the schema matrix, the three burned-in behaviors, the cap/stop/retry rules, the read-only full sweep, the draft template with its four mandatory negative-finding elements, dry-run zero writes, and the NETRED per-shot reconciliation; the worked sample is the round-1 judgment volume cited in section 6; the identifiers, endpoints, anchors and exit codes quoted here match `tools/periscope.py` as read on the tree (six flags, schema name, `ROUND_SECONDS`, `assert_read_only`, `render_draft`, selftest vectors V1-V10 all present).
> Exit-codes.  Not applicable to a document face; the tool's documented codes in section 1 (0 run/dry-run/selftest passing with negative findings and C1 triggers included; 1 selftest or draft-invariant failure; 2 usage/schema error; 9 missing input) are the implemented semantics, described as implemented.

---

## 0. Scope, pre-flight gates, and verdict semantics

### 0.1 Scope and I/O surface

- **Scope**: runs read-only GET collection against a configurable watchlist (schema `rocqwash-periscope-config/1`, default = the six-source as-built list), persists the raw bodies, the per-shot NETRED records and the watcher-window records to disk, and produces the five-section judgment draft `intel-ledger-draft.md`.
- **Inputs**: `--config` (six-source JSON, built-in default), `--out` (output directory, required for a real run), `--rounds` (watcher rounds), `--netrc` (credentials file, passed straight to curl; the tool itself never reads the credentials).
- **Outputs**: `<out>/raw/<key>.json` (fetched bodies), `raw/<key>.retry.json` (evidence bodies for definite 404 negative findings), `raw/<key>.a<n>.json` (per-shot bodies), `raw/<key>.netred.txt` + `raw/netred-master.txt` (per-shot records, failures included), `raw/windowsniff.netred.txt` (watcher-window records), `intel-ledger-draft.md` (the judgment draft).
- **Pre-flight gates (fail-loud)**:
  1. a missing `--out` refuses to initiate the run (exit 2); implicit network sweeps are forbidden;
  2. a missing `--config` file exits 9; schema drift exits 2 (unknown top-level keys / unknown kinds / out-of-range caps / non-hex frozen prefixes are all rejected);
  3. the read-only pledge, GET-only: the curl argument builder is structurally incapable of producing a write verb, and `assert_read_only` re-asserts it before every shot.

### 0.2 Top-level verdict semantics

- **Data, never errors**: negative findings (definite 404 conclusions / cap exhausted without collection / a dead window) and C1 triggers are all registered loudly and the tool exits 0; the upgrade paths (rescan / disclosure) stay pending execution, never automatic.
- **Draft ≠ verdict**: the draft's mechanical lines (three-state first screening / watcher conclusions / windowing suggestions) are a first screening; the verdict is the adjudicator's work. A watcher conclusion is valid only for the rounds actually measured (the same self-bounding rule as the negative-finding boundary).

## 1. CLI face (six flags)

| Flag | Meaning | Default |
|---|---|---|
| `--config FILE` | six-source JSON (schema `rocqwash-periscope-config/1`) | built-in as-built list |
| `--out DIR` | output directory; **required for a real run** (implicit sweeps refused, exit 2) |; |
| `--rounds N` | watcher companion rounds; one beat always fires after the sweep closes | 10 |
| `--netrc FILE` | passed to `curl --netrc-file`; the token is never read/logged by the tool | none |
| `--dry-run` | validate + plan + render the draft skeleton; zero network, zero writes | off |
| `--selftest` | offline frozen vector group (canned transport + virtual clock) | off |

Exit-codes: `0` run/dry-run/selftest passing (negative findings and C1 triggers included) · `1` selftest failing or draft invariant failing · `2` usage/schema error · `9` missing input (config absent, output root not creatable).

## 2. Config schema and the six-source as-built list

Schema `rocqwash-periscope-config/1` top-level keys: `schema` / `sentinel` / `defaults` / `deposit_anchors` / `sources` (unknown keys fail loud). Per-source keys: `key` / `kind` (`github_search` / `github_api` / `github_issue` / `github_commits` / `arxiv`) / `url` / `auth` (`netrc` / `none`) / `cap` (1-16, default 8) / `days_window` (the arXiv rolling window; the URL carries the `{WINDOW}` placeholder) / `comments` (the issue sub-face `{enabled, per_page}`) / `c1_frozen_prefix` (`github_commits` only, a hex prefix) / `screening` (`keywords` / `own_markers` / `anchor`) / `retry_param_overrides` (the per-retry URL parameter override table).

Default six sources (the round-1 as-built watchlist of November 13, 2026; the whole list is replaceable; an endpoint change only needs a config change):

| # | Key | Kind | Endpoint (as-built) | Reading face |
|---|---|---|---|---|
| 1 | `mathlibpr` | github_search | `api.github.com/search/issues?q=repo:leanprover-community/mathlib4+is:pr+zeta&per_page=10` | prior registration of the same topic / racing-discovery watch |
| 2 | `pr45912` | github_api | `api.github.com/repos/leanprover-community/mathlib4/pulls/45912` | state / mergeable / CI dynamics |
| 3 | `arxiv-dzeta` | arxiv | `export.arxiv.org/api/query?...all:"Dedekind zeta"...{WINDOW}` · days_window=30 | literature racing watch |
| 4 | `arxiv-quasir` | arxiv | same form ("quasi-Riemann") · days_window=30 | literature racing watch |
| 5 | `issues` | github_issue | `api.github.com/repos/hy7pc8gfmf-dotcom/ConstructiveWorld-Main/issues/3` + the `/comments?per_page=30` sub-face (configurable) | own ticket-assignment thread dynamics |
| 6 | `dzzftip` | github_commits | `api.github.com/repos/AxiomMath/DedekindZetaZeroFree/commits?per_page=3` · `c1_frozen_prefix=09afbb4` | C1 trigger decision |

Default `deposit_anchors`: `mathlib_pr45912_closed_at=2026-11-11T22:19:13Z`, `dzzf_tip_frozen_prefix=09afbb4`, `dzzf_freeze_observed_at=2026-11-10T17:42:11Z`; anchors that cross-check the first-screening time points.

## 3. The three burned-in behaviors

Three measured defects from the round-1 sweep of November 13, 2026 are burned into the tool body; each is documented as precedent → burn-in behavior → verification:

### Behavior a: the arXiv leg carries `-L` from the first shot

- **Precedent**: in the round-1 sweep the quasir leg went 8/8 shots all 301 (cap exhausted, zero yield), while the dzeta/leanrh legs, after adding `-L` to their parameters, returned 200 on the first shot; the redirect defect burned 16.7% of the shot budget.
- **Burn-in**: `build_curl_args` unconditionally appends `-L` from the first shot for `kind=arxiv` (and carries it on every attempt); non-arXiv sources omit it by default (openable through the `follow` config switch).
- **Verification**: selftest V3; the argument vectors for attempts 1-8 of the arXiv source assert `-L` shot by shot; the GitHub-source vectors assert no `-L` by default.

### Behavior b: the watcher companion leaves zero silent gaps (60s round spacing; every yield writes a SUSPEND line)

- **Precedent**: in the round-1 sweep the background-mode watcher ran at 97s spacing and R2→R3 carried a 15min46s zero-sampling gap; "not sampled" and "measured dead" could not be told apart.
- **Burn-in**: the watcher companion is built into the same process as collection: beat 1 samples before the sweep opens → the collection sweep runs (it may time out across several beats) → every skipped beat explicitly writes `SUSPEND|<beat>|<UTC>|collection-sweep-in-flight` (silent skipping is forbidden) → the beat right after the sweep must sample → the remaining rounds fill in at the 60s spacing. `_assert_no_silent_gap` mechanically asserts that beat numbers 1..N are contiguous with none missing; after the windowsniff record is persisted to disk it is read back and asserted (line count == beat count · header line in place), and any drift exits 9.
- **Verification**: selftest V5; under the virtual clock the collection sweep skips 2 beats → exactly 2 SUSPEND lines, contiguous numbering, the last beat is a sampling beat, and the read-back reconciliation passes.

### Behavior c: source 4's endpoint = the Main issue#3 plus the comments sub-face (configurable)

- **Precedent**: in the round-1 sweep, source 4 was pinned by the five-source list to `rocqwash/issues/3` and took a 404 as a definite negative finding; the root cause was that the ticket-assignment coordination thread actually lived at `ConstructiveWorld-Main` issue#3 (GET 200 · 87 comments verified); an endpoint pinning must first be proven by an existence GET.
- **Burn-in**: the default config pins the `issues` source URL to the Main repository issue#3; the `comments.enabled=true` + `per_page=30` sub-face is fetched within the same source cap right after the single point (≥2s between shots, every shot enters NETRED); on a 404 at the single point the sub-face does not start (the negative-finding four elements come first). The retired endpoint face (the rocqwash repository issue single point) stays out of the default list.
- **Verification**: selftest V4; the default issues endpoint equals the Main issue#3 and contains no rocqwash/issues; two canned shots (single point 200 → comments 200) assert the sub-face URL form, both shots entering the record, and the comments count parsed on file.

## 4. Window protocol (cap 8, stop when obtained, sleep-60 retry with changed parameters)

| Rule | Behavior |
|---|---|
| Cap | 8 shots per source (the config `cap` allows 1-16); watcher beats and comments sub-face shots likewise enter the record shot by shot |
| Stop-when-obtained | any shot with HTTP 200 and a parseable body → the source's terminal state is `obtained`; the remaining cap is not burned |
| Retry | not 200 and not 404 → sleep 60s → resend with **changed parameters**: each retry widens the effective timeout by 30s (`curl-timeout:NNs` recorded into the NETRED `changed=` field), and each override from the config `retry_param_overrides` is additionally recorded as `config-override:n` |
| Negative-definite 404 | a 404 stops immediately (no backoff, cap preserved) and the 404 body is preserved as `raw/<key>.retry.json` as the four-element evidence |
| Cap-exhausted | terminal state `cap-exhausted-registered` = registered, not failed; the four-element draft is mandatory |
| Parse-error | 200 but an unparseable body → `parse-error-retryable`, taking the failure-retry path (round-1 precedent: a body parse failure = pipeline data, not window data) |

## 5. Watcher companion protocol

- The `ROUND_SECONDS=60` spacing is burned in and not configurable (changing the spacing changes the behavior-b semantics; it requires changing the tool body and passing the selftest).
- Window-record line forms: `R<n>|<UTC>|<code>|LIVE|DEAD` plus `SUSPEND|<n>|<UTC>|<reason>`; the default watcher liveness endpoint is `api.github.com/rate_limit`.
- Watcher-conclusion boundary (hard-coded into item 1 of draft section 5): it covers only the measured rounds; an unmeasured segment cannot be finally established as dead or alive; the round-1 precedent: "26 minutes of continuous liveness evidence does not falsify the fragmentation hypothesis".

## 6. The judgment-draft template (five sections, mandatory form)

`render_draft` produces `intel-ledger-draft.md`; the five-section structure aligns to the round-1 judgment volume:

| Section | Content | Mandatory face |
|---|---|---|
| 1 Per-source digest | a per-source table: fetched-at (UTC) / shots / state / key facts (time-bound) | every source carries one row; the raw file pointers are attached |
| 2 Three-state collision first screening | per-entry lines: created/published vs the deposit anchor plus keyword overlap → `prior-registered` / `suspected-collision(adjudicate)` / `no-bearing` / `ours(registered)` | every mechanical first-screening line carries its criterion note; promoting a suspected collision never happens automatically |
| 3 C1 trigger decision | the tip sha vs the frozen prefix → `C1-CLEAN` / `C1-TRIGGERED` / `UNDETERMINED` | a trigger is registered loudly; the rescan stays pending execution |
| 4 Negative-finding four elements | one block per uncollected source: 1 scanned, 2 not scanned, 3 not an absolute claim, 4 aliased equivalents not exhausted | **mandatory**: for any `negative-definite` / `cap-exhausted` source the renderer raises AssertionError when any element is missing (exit 1, fail-loud); the four-element wording is the exact form pinned by the negative-finding boundary rule |
| 5 Five windowing suggestions | 1 first-release timing (watcher measurements plus the boundary sentence) 2 watcher companion (beat/SUSPEND counts plus the zero-silent-gap verification) 3 staggered timing between agents (the first-shot pickup face plus delaying arXiv) 4 caps and protocol (per-source shot counts vs the cap) 5 re-pinning and follow-up (C1 state / 404 re-pin candidates / suspected-collision counts) | the five-item form is fixed; every item carries its as-run mechanical data |

**Worked sample**: the round-1 judgment volume is `attn/_periscope_20261113/intel-ledger-20261113.md` (the 25-shot master record, 11 three-state first-screening lines, the C1 decision, the issues-404 four-element exemplar, and the five windowing suggestions verbatim); the tool's draft is that volume's skeleton-prefilled form, and the adjudicator continues writing the verdict sentences.

## 7. NETRED and the read-only pledge

- The per-shot record (failed shots included) is one line per shot: `<UTC>|<key>|attempt=<n>|GET <url>|HTTP <code>|<bytes>B|<verdict>[|changed=…]`; the per-source record and the master record are both persisted to disk.
- The read-only pledge's mechanical face: the argument builder has no write-verb slot; `assert_read_only` scans every vector for `-d/--data*` (rejected outright) and for `-X` with a non-GET verb (rejected); selftest V7 sweeps the five kinds × three attempt tiers in full.
- Credential exclusion: the tool never reads, stores or echoes the token; the netrc path goes straight to curl; NETRED lines carry no credential fields.
- The hosts pins (locally DNS-poisoned domains) are an environment face: the operator maintains the `hosts` file per the hosts card; the tool does not manage it.

## 8. Offline selftest and suite membership

- `--selftest` = a frozen group of 10 vectors: V1 CLI face (six flags + bare-run refusal) · V2 schema matrix (missing 9 / drift 2 × 5 forms) · V3 behavior a `-L` shot by shot · V4 behavior c endpoint + sub-face · V5 behavior b SUSPEND + zero silent gaps + read-back · V6 cap/stop/retry three-way split · V7 read-only full sweep · V8 draft five sections + four elements + both C1 branches + first-screening four states · V9 dry-run zero writes · V10 NETRED per-shot reconciliation. Canned transport + virtual clock; **zero network, zero disk writes** (zero bytes outside the temporary directory).
- `tests/t_periscope_shape.py` is the suite shell (four subprocess checks: the selftest marker / the `--help` face / the exit-code contract / dry-run skeleton and zero writes). It is **not entered in the `run_tests.sh` roster**: the roster count and the README.md lines reconcile mechanically in three places (doc_lint's second count check), and README membership is governed by the roster-authorization work stream; following the `t_exp_port.py` precedent (the same registration form at tests/t_exp_port.py:11-14).

## 9. Operating order (three steps for a real run)

1. **Dry-run validation**: `python tools/periscope.py --dry-run [--config my.json]`; read the six plan lines and the draft skeleton; confirm that endpoints/caps/anchors show no drift (zero network, zero disk writes);
2. **Real run**: `python tools/periscope.py --out <dir> [--netrc <file>] [--rounds 10]`; produces the raw bodies, the three records and the draft; the watcher beats probe ahead;
3. **Adjudication continuation**: with `intel-ledger-draft.md` as the skeleton, continue writing the verdict sentences in the worked volume's five-section form (three-state verdicts / C1 disposition / completing elements 2 and 4 of the four elements); the final volume is persisted to disk under its dated name; suspected-collision disclosure and rescans both stay pending execution.
