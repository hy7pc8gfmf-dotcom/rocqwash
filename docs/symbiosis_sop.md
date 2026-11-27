# SOP · 共生总线跨仓经验交换 / SOP: Symbiosis-Bus Cross-Repository Experience Exchange (tools/symbiosis_bus.py)

> **一句话 One-liner**: 共生总线把单仓经验总线升级为跨仓共生总线：经验条目（哨事件类条目随行）双向交换、版本锚随行、账面单口只增；判读升级永远不在工具内自动发生。
> One-liner: the symbiosis bus upgrades the single-repository experience ledger into a cross-repository exchange, both directions, anchor-versioned, single-port append only; judgment upgrades never happen automatically inside the tool.
> Ticket GD-20261115-RQWPLUG-01 §1.1 freezes this statement face; the six-section form follows `docs/periscope_sop.md`.
>
> Purpose.  Upgrade the single-repository experience bus (`tools/exp_port.py`
>   append face plus `docs/exp-ledger.jsonl`, schema `rocqwash-exp/1`) into a
>   cross-repository bus over rocqwash / Main / Set: entries (sentinel-shaped
>   events ride as ordinary entries) move in both directions through
>   versioned offline swap packages, and the target ledger grows only
>   through the single append port. Read-only except `import`; findings are data.
> Interface.  `python tools/symbiosis_bus.py [--selftest] {export|import|
>   status|diff} [--out SWAP.jsonl] [--swap SWAP.jsonl] [--ledger P]
>   [--source-repo NAME] [--anchor HEX] [--a LEDGER_A] [--b LEDGER_B]
>   [--dry-run]` (export needs `--out`; import one `--swap`; diff
>   `--a`/`--b`; per the tool `--help` face).  MCP face `symbiosis_status`
>   returns this document from `ROCQWASH_HOME`; schema `rocqwash-symbio/1`; zero network.
> Dependencies.  Python 3 stdlib only, import set within `json/os/re/sys/
>   argparse/hashlib/pathlib/typing/datetime`; the import leg drives the
>   existing append contract of `tools/exp_port.py` and its ledger
>   resolution; zero `eval`/`exec`; no silent fallback.
> Evidence.  Attestation faces named by the same ticket: the shape test
>   `tests/t_symbiosis_shape.py` and the execution round with the swap
>   package attached as `docs/symbiosis-swap-round1.jsonl`; the MCP face of
>   this document is witnessed by `python -B tests/t_mcp_face.py`
>   (25-capability roster).
> Exit-codes.  0 face green (skips, zero matches, non-empty diffs, zero
>   counts are data); 1 selftest red; 2 usage or IO failure; 9 missing or
>   corrupt input, envelope schema drift included (fail loud, zero writes).

## 〇、适用域、前置闸与总判定语义 Scope, Pre-Flight Gates, and Verdict Semantics

主题句：本工具只做一件事，让两个 repository 的经验账通过离线交换包互相喂饱，而账面写入权始终只在 append 单口手里。

### 0.1 适用域与输入输出面 Scope and I/O Surface

- **适用域 Scope**: the local experience ledger (`docs/exp-ledger.jsonl`,
  schema `rocqwash-exp/1`, written only through the `tools/exp_port.py`
  append port) and the same-shape ledger of another repository. Sentinel
  events (CI triage rows and the like) enter the bus as ordinary
  `rocqwash-exp/1` entries, so the bus carries them without a second schema.
- **输入 Inputs**: the local ledger path; for `diff`, a second ledger path;
  for `import`, the swap-package JSONL path.
- **输出 Outputs**: for `export`, the swap-package JSONL (schema
  `rocqwash-symbio/1`, one envelope line per entry); for `status` and
  `diff`, the report face (human-readable and machine-readable forms; exact
  flags on the tool `--help` face).

### 0.2 前置门 Pre-Flight Gates (fail-loud)

1. Zero network by design: the tool opens no socket and imports no network
   module (no `fetch`/`requests`/`urllib` face); exchange walks offline
   files only; the NETRED register row states `no network by design`.
2. Single-port oath: `import` writes each entry through the
   `tools/exp_port.py` append contract only; `export`/`status`/`diff` are
   read-only; a code path that writes the ledger directly does not exist.
3. Determinism: entry ids and time points come from entry content only (the
   import leg carries the content-stamped `id`/`ts`); the runtime clock and
   randomness never enter the logic; same input, same output.
4. Stdlib only; zero `eval`/`exec`; every failure path raises or exits
   loudly with its own code (`0/1/2/9`); no try-pass-continue swallowing.

### 0.3 总判定语义 Top-Level Verdict Semantics

- **一切发现皆数据 Data, never errors**: duplicate skips, zero matches,
  non-empty diff sets and zero counts are all reported loudly at exit 0.
- **损坏与缺件响亮 Damage is loud**: a ledger or package line that is not
  valid JSON exits 9 before any write is attempted; missing input exits 9;
  usage or schema errors exit 2; a selftest red exits 1.
- **判读升级不自动 No automatic escalation**: `status` and `diff` produce
  readings only; opening the next exchange round is always an explicit
  caller decision.

## 一、CLI face 契约 CLI Face Contract（四 face·ticket order）

| Face | Input | Output | Write face | Exit semantics |
|---|---|---|---|---|
| `export` | local ledger (`rocqwash-exp/1`) | swap package JSONL (`rocqwash-symbio/1`, one envelope per entry) | the package file only | 0 with the per-entry export count; 9 ledger missing/corrupt |
| `import` | swap package JSONL | per-entry `appended`/`duplicate-skip` report lines plus the summary line | none of its own; every write rides the `tools/exp_port.py` append port | 0 (skips are data); 2 usage; 9 corrupt/missing/damaged input, envelope schema drift included (zero writes) |
| `status` | local ledger (provenance fields included) | both-direction counts plus the last exchange time point | none | 0 whenever the ledger is readable; 9 missing/corrupt |
| `diff` | two ledgers | the entry-id set difference (only-in-A / only-in-B) | none | 0 (a non-empty diff is data); 9 missing/corrupt |

- The `0/1/2/9` contract holds for every face and is stated in each face
  docstring together with its INPUT-OUTPUT form (input shape, output shape,
  side-effect face, exit codes).
- Provenance rule: the envelope fields `sourceRepo`/`anchor` ride the
  append correlationId face, synthesized as
  `symbio:<sourceRepo>@<anchor>` when the entry carries no
  `correlationId` of its own (`correlationId` is a schema increment
  outside the fingerprint seen set); they are never spliced into the four
  carrier fields.

## 二、schema `rocqwash-symbio/1` 字段表 Field Table

交换包是 JSONL：首行一封筒，随后一行一条原样条目（合流对齐注记：本节字段形按工具实词面转录——envelope 系单行包头携 entryCount，条目行随其后，与 `tools/symbiosis_bus.py` 的 `--selftest` 冻结矢量逐字节同形）。The package is JSONL: line 1 is the envelope (a header object carrying the count), then one verbatim entry line per entry — the field shape below is transcribed from the tool's real word face and matches its frozen selftest vectors byte for byte. Envelope line shape:

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | constant `rocqwash-symbio/1` |
| `kind` | string | constant `symbiosis-swap-envelope` |
| `sourceRepo` | string | identity of the exporting repository (e.g. `rocqwash` / `Main` / `Set`; default: the checkout directory name, or `--source-repo`) |
| `anchor` | string | versioning anchor of the source at export time (the commit read from `.git`, or `--anchor`), so an import can tell which vintage it is reading |
| `entryCount` | integer | number of entry lines that follow; import refuses a mismatch loudly before any write |

Entry line shape (one `rocqwash-exp/1` entry carried verbatim: `schema`/`id`/`ts`/`tool`/`points`/`evidence`/`batch`/`fingerprint`, plus optional `correlationId`/`source`).

Import mapping (envelope → append contract):

| entry field | append parameter | rule |
|---|---|---|
| `tool` / `points` / `evidence` / `batch` | the four carrier fields | carried verbatim; the fingerprint (sha256 over the four, per `tools/exp_port.py`) must survive the ride unchanged, or the seen set loses its cross-repository identity |
| `id` | the append face's explicit id parameter (`exp_port --id`) | verbatim from entry content; import never mints ids (an entry without an id is refused before any write) |
| `ts` | the append face's explicit ts parameter (`exp_port --ts`) | verbatim from entry content; the runtime clock never enters the import leg |
| envelope `sourceRepo` / `anchor` | the correlationId face (`exp_port --correlation-id`) | synthesized as `symbio:<sourceRepo>@<anchor>` when the entry carries none; a schema increment outside the fingerprint seen set |

## 三、交换窗口协议 Exchange Window Protocol（离线文件交换·零网络 Offline File Exchange, Zero Network)

主题句：交换包是文件，不是连接。

- The package is a file, not a connection: it moves with the repository
  tree or an offline bundle channel; the tool itself performs zero network
  calls; the NETRED register row states `no network by design`.
- Direction pairing: repository A `export` produces the package; repository
  B `import` replays it through the append port; the reverse direction is
  B `export` then A `import`. Replaying the same package is legal and adds
  zero lines (idempotency, section 四).
- Time-point discipline: exchange time points are read from entry content
  (`ts` / `anchor`); the runtime clock and randomness never enter the
  logic.
- Window reading: the `status` counts plus the last exchange time point are
  the window reading; whether to open the next round belongs to the
  caller, never to the tool.

## 四、幂等与冲突规则 Idempotency and Conflict Rules

主题句：同包重放零新增；冲突是数据，不是异常。

- **幂等 seen 集 Idempotent seen set** (inherited from
  `tools/exp_port.py`): an entry whose `id` or `fingerprint` is already
  present prints the loud skip line (with its axis) and writes nothing at
  exit 0; re-importing the same package therefore adds zero lines (the
  execution-round acceptance anchor: same package, second import, zero
  additions).
- **指纹保真 Fingerprint fidelity**: `import` never alters the four carrier
  fields (the fingerprint's domain); exchange provenance rides the
  provenance face only.
- **跳过分类 Skip taxonomy**: `axis=fingerprint` means the same content is
  already present (benign); `axis=id` with a different fingerprint means a
  cross-repository id collision, reported as data for the judgment face;
  the bus never mutates an existing line (append-only).
- **损坏响亮 Loud damage**: a package or ledger line that is not valid JSON
  exits 9 with zero writes (no partial append); missing input exits 9.
- **只增誓言 Append-only oath**: the ledger grows and is never rewritten; a
  wrong import is corrected by a later entry; no update or delete face
  exists.

## 五、判读面 Judgment Face

主题句：工具产读数，判读方产裁定；边界只及实读面。

- **status 读数 Status reading**: the outbound count (entries exported into
  packages) and the inbound count (entries imported through the append
  port), plus the last exchange time point taken from entry content; zero
  counts and zero matches are data at exit 0.
- **diff 读数 Diff reading**: the entry-id set difference between two
  ledgers (only-in-A / only-in-B); a non-empty diff is data, not an error.
- **负发现边界 Negative-finding boundary**: a "not found" reading covers
  only the ledgers actually read, stated with the four elements (what was
  scanned; what was not scanned; not an absolute claim; aliased equivalents
  not exhaustively ruled out).
- **升级不自动 No automatic escalation**: suspected collisions, unusual
  diff sets and skip classifications await the reader's adjudication; the
  tool never auto-exports, auto-imports or rewrites.
- **MCP face**: `symbiosis_status` is the read-only MCP window onto this
  contract, on the `capability_index` wiring (it returns the full text of
  `docs/symbiosis_sop.md` resolved from `ROCQWASH_HOME`; zero network face,
  no side effects; see `docs/mcp.md` for the server face).

## 六、缺口账喂送面 The Gap-Ledger Feed Face (tools/bus_feeder.py)

主题句：交换包喂入缺口账；喂送是独立的下游工具面，总线 `import` 腿仍只落经验账，单口誓言不变。

- **位置 Positioning**: downstream of `export`: an exported package
  (schema `rocqwash-symbio/1`) feeds the TODO-SEAT gap account through
  `tools/bus_feeder.py`, a separate tool and not a new face of the bus;
  the bus `import` leg keeps writing the experience ledger only (the
  single-port oath of section 〇.2 is unchanged).
- **识别集 Recognition set** (documented order, first hit wins, reported
  per row in the `recognition` field): the pitfall category token U+5751
  under the top-level `category` key or under the source dict's
  `category` / zh key spellings; the literal `TODO-SEAT` token in points
  or evidence; the literal `status=todo_seat` token in evidence.  A
  non-gap entry is counted and excluded; zero gap rows are data at
  exit 0.
- **族形状到缺口行 Family shape to gap row**: one gap row per selected
  entry lands in the gap feed ledger (default `docs/gap-feed-ledger.jsonl`,
  `--ledger` overrides).  The row keeps the swap entry verbatim (schema
  `rocqwash-exp/1`, the fingerprint domain untouched) plus three schema
  increments outside the fingerprint domain: `correlationId` synthesized
  as `feed:<sourceRepo>@<anchor>` from the envelope, `shapeKey` computed
  by the `tools/gap_cluster.py` key chain (`fam:<familyId>` when an
  explicit familyId is present, `fam:<token>` when the points text
  carries a family token after `TODO-SEAT`, else `shape:<abstracted>`),
  and `recognition` naming the rule that selected the entry.

| Face | Input | Output | Write face | Exit semantics |
|---|---|---|---|---|
| `feed` | one swap package (deep-validated) | one fed/skip line per selected entry plus the summary line | the gap feed ledger only; `--dry-run` writes nothing | 0 (skips and zero gap rows are data); 2 usage or IO; 9 missing or corrupt input, nothing written |
| `status` | the gap feed ledger, optional swap packages | count lines plus the shape-to-rows mapping plus per-package present/new counts | none | 0 whenever the ledger is readable; 2 usage or IO; 9 missing or corrupt |

- **幂等与跳过轴 Idempotency and skip axes** (the `exp_port` taxonomy,
  precedence preserved): a repeated id skips on the `id` axis; otherwise
  a repeated fingerprint skips on the `fingerprint` axis; both print the
  loud skip line and write nothing at exit 0; a repeated id with a
  different fingerprint is a collision reported as data; rows are
  append-only and never mutated.  The same package replays
  byte-identically into fresh ledgers: ids and time points ride entry
  content, the runtime clock never enters the logic.
- **写面与誓言 Write surface and pledges**: `feed` writes only the gap
  feed ledger; `feed --dry-run` and `status` write nothing; no face of
  the feeder reads or writes `docs/exp-ledger.jsonl`.  Exit codes
  `0/1/2/9`: 0 face answered, 1 selftest red, 2 usage or IO, 9 missing
  or corrupt input with nothing written.  Zero network by design (the
  NETRED register row states `no network by design`).
- **边界（负发现四要素） Boundary (negative-finding, four elements)**:
  scanned = the three recognition rules above over envelope-validated
  entry lines; not scanned = free text outside the points / evidence /
  category / familyId fields, and gap markers in other spellings; not an
  absolute claim = a row's gap face rests on this recognition set;
  aliased equivalents were not exhaustively ruled out.  Rescan
  condition: the recognition set changes or a new package arrives.
  Named divergence, closed (aligned by the gap-trigger alignment item):
  `tools/gap_cluster.py` pinned its category token as the
  escape `\u5748` (code point U+5748) while its own producer
  (`tools/vacgen.py` line 2470) emits U+5751, and read only the
  `category` key spelling, so aggregation of a fed ledger recognized
  the `TODO-SEAT` / status rows but not category-only rows.  The
  reader-side rule now reads both tokens (U+5751 producer-real, U+5748
  legacy) under both key spellings at both levels, so a category-only
  fed row counts on the aggregation face (asserted mechanically in
  `tests/t_bus_feeder_shape.py` check 7).
- **真实样本 Real sample**: `docs/symbiosis-swap-round1.jsonl` (envelope
  `rocqwash@2bd712f`, 27 entries) validates on the dry-run face and
  reports `would-feed=1 nonGap=26`; a real feed writes only the
  caller-named ledger, never a repository file.
- **shape 测试 Shape test**: `tests/t_bus_feeder_shape.py` runs directly
  and is deliberately not rostered in `tests/run_tests.sh` (the roster
  count is mechanically coupled to the README count lines through
  doc_lint's second check; roster insertion belongs to the work stream
  holding that authorization; the `t_exp_port` / `t_periscope_shape` /
  `t_symbiosis_shape` / `t_uplink_shape` precedent applies).
