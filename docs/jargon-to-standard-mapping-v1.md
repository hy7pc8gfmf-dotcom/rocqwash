# Jargon-to-Standard Mapping Table v1 (rocqwash tool repository domain)

# jargon-to-standard-mapping-v1.md — project-jargon-to-standard-expression mapping table for the rocqwash tool repository, v1.
> Normative authority: `docs/annotation-standard-v1.0-20261113.md` (rocqwash Annotation Standard Card v1.0). This table is **Appendix A of that card**: every jargon face banned by the card is mapped here to its standard replacement, with a per-row context note that is the disambiguation authority for context-sensitive faces. Replacement applies to prose surfaces only (comments, docstrings, help text, documentation); see §6 for identifier positions, which are exempt.
> Purpose.  The repository's canonical term-standard table, Appendix A of the Annotation Standard Card: every jargon face the card bans on prose surfaces, mapped to its standard replacement, with the per-row context note as the disambiguation authority for context-sensitive faces.
> Interface.  Data face (not executable). The pipe tables in sections 2-5b carry three columns (jargon face | standard expression | context note), plus an optional fourth `;`-separated exempt-regex cell where a row needs a line-scoped preserve carve-out (loader contract, seeds/jargon/SPEC.md section 2), read by `tools/norm_lint.py` (this file is its default `--jargon-map`), `tools/jargon_apply.py`, and `tools/jargon_map_sync.py`; section 6 registers the identifier-position exemptions.
> Dependencies.  `tools/norm_lint.py`, `tools/jargon_apply.py`, `tools/jargon_map_sync.py`, and the machine-readable transcription `seeds/jargon/jargon-map.json`, which pins this file by md5 under its sync discipline.
> Evidence.  Every `norm_lint --tree` census loads this table as the default map (143 active faces); `seeds/jargon/test_snippet.py` re-asserts the in-repo transcription containment against this table's standard cells on every machine (`check_md_containment`); `tools/jargon_apply.py --plan` reads it for the repository residue census.
> Exit-codes.  Not applicable (data face); consumers keep their own contracts (`norm_lint` 0/1/2/9).

## 0. Status and provenance

- Repository state at issue: rocqwash v52, commit `79a766c`, working tree clean (reconciled November 13, 2026 via `git log --oneline -3` and `git status --porcelain` before this document cited any version).
- Base assets (cited, all read in full at issue time):
  1. **JARGON filter list v0.9→v1.1** — the From-Zero Paper-Construction Methodology Whitepaper v1.0 §9.1 (ConstructiveWorld `经验/docs/从零论文构建方法论白皮书-v1.0-20260927.md`), paper-track filter list; revision chain v0.9 (nine user-named words) → v1.0 (JARGON full survey merge) → v1.1 (DICT precedent entries).
  2. **Annotation whitepaper §4 mapping table v1.0→v1.8** (ConstructiveWorld `注释规范白皮书-v1.0-20260921.md`), .v-comment-track mapping, including the 65-face consolidated banned-word list enforced by `verify/gate4_comment_guard.py` (`BANNED_WORDS`, gate4_comment_guard.py:71-76).
  3. **M-wave Annotation Card, October 25, 2026** (ConstructiveWorld archive `收包-20261112-路线2TierA/_live_check_2f1ffbaf/docs/注释规范卡-M波-20261025.md`, section 4), whose forbidden-face families this table extends into the tool-repository domain.
- Inventory method ("on-the-ground full sweep"): per-term `grep -rl <term> --include="*.py" --include="*.sh" --include="*.md"` over this repository on November 13, 2026, excluding `更新账.md` (frozen ledger) and the two canonical documents of this wave; the count in each context note is the number of files containing the term (presence count, not occurrence count). Runs executed before this document existed, so the counts are free of self-contamination.
- Row grammar: each row has exactly three columns — [jargon face | standard expression | context note].

## 1. Reading rules

1. **Prose positions only.** Code identifiers, CLI flags, JSON schema field names, file-format names, and exit-code tokens are never rewritten (interface-stability boundary; Annotation Standard Card §5). When prose must refer to a tool whose name contains a banned-family word, cite the tool name verbatim in backticks — that is an identifier citation, not a jargon hit (§6).
2. **Word-boundary discipline.** Mechanical scanning must judge whole words/compounds, not substrings (JARGON v1.1 precedent 3: `入库` as an independent word is cleaned, `并入库内` is not triggered). The context note column states the sense in which each face is banned.
3. **Replacement is mandatory, not advisory**, on all canonical faces (new files, translated files) covered by the Annotation Standard Card §4. In not-yet-translated legacy Chinese content the hit is still reported at error level by the card's grading; the Chinese-only presence itself is warn-level during the transition window.
4. **No re-translation into fresh jargon.** The standard column is the target form; do not substitute a different metaphor (JARGON v1.1 precedent 1: narrative `收口` maps to close out, never to a different internal word).

## 2. Table A — core mappings (named in the issue, sixteen rows)

| 黑话 (jargon face) | 标准 (standard expression) | 语境注记 (context note) |
|---|---|---|
| 席（角色义）／席位／席名 | agent | Role noun; agent is the general term, the one-worker-per-seat topology wording (seat-worker) stays on ledger and identifier surfaces. Seat numbers/names never enter prose. 106 files (席). | 1003\ 增;4\.1\ 席位;\*\*——席位;据」·席\ 1;检索·席\ 1 |
| 盯守 | monitor | Banned face in gate4 extended family (verify/gate4_comment_guard.py:173). Standing-watch context: "monitor the run". 1 file. |
| 落刀 | apply | Apply the change to the tree. Default-dry-run tools apply only under an explicit `--apply` flag (cw.sh tool table, 27 files). | 1003\ 增;4\.1\ 席位;ce｜落刀：;日期.{1,3}变更.{1,3}落刀;查）｜落刀： |
| 上云 | push | 0 repository hits; adjacent-domain face for the push action. The `pushci` tool name is an identifier and stays. |
| 对账 | reconcile | Cross-checking two surfaces against each other (doc-vs-implementation counts, ledger-vs-state). 33 files. | 1003\ 升;保留确认\ 1;留；\*\*对账;笔\*\*（对账;锚面刷新工单 |
| 洗 | sanitize / clean | Engineering sense only. Tool name `wash_shape.py` / `wash-shape` stays as identifier; generic prose says sanitize. 46 files. |
| 炮 | run | "重炮" → rerun; "BACK 发炮" → issue the run. 3 files (e.g. wash/probe_engine.py:37, verify/_parse_fin_mac.py:12). |
| 红 | failing | Engineering sense only. The repo maxim 「红是数据非器红」 → "a failing result is data, not a tool failure" (Table C). 103 files. |
| 挂单 | queued | Banned face in gate4 extended family (gate4_comment_guard.py:173). Queue-state context: queued / awaiting scheduling. 1 file. |
| 收编 | absorb | In the 65-face consolidated base (gate4_comment_guard.py:72). Merge-into sense: absorb. 1 file. |
| 让位 | yield | 0 repository hits; precedence/concurrency context: yield (to a higher-priority run). |
| 扒皮 | strip | 0 repository hits; stripping process narration from comments: strip. |
| born-clean | axiom-free born | Classification face in wash/probe_engine.py:17-21 (BORN-CLEAN verdict line) — the verdict token stays as identifier; prose says axiom-free born. 6 files. |
| 金标 | gold-standard | Evidence-required discipline: 「无据不铸」 → "evidence required before issuance" (Table C); gold-standard evidence reference. 7 files (e.g. tools/wash_shape.py:578,602,630). |
| 活账 / 死账 | live ledger / stale ledger | 0 repository hits; ledger-freshness context: live vs stale ledger. |
| 仓 | repository | 仓根/仓内 → repository root / in the repository. 102 files. |

## 3. Table B0 — JARGON v0.9/v1.1 base carry-over (paper-track rows portable to tool prose)

| 黑话 (jargon face) | 标准 (standard expression) | 语境注记 (context note) |
|---|---|---|
| 元卖点 | primary feature | JARGON base row; marketing-flavored. 0 repository hits. |
| 底档 | source transcript | JARGON base row; verbatim archive sense. 0 repository hits. |
| 脊柱 | evidence chain | JARGON base row; backbone metaphor. 0 repository hits. |
| 红线 | non-negotiable constraint | JARGON base row; discipline metaphor — prose states the constraint itself. 16 files. |
| 核验定谳 | independently verified | JARGON base row. 定谳 is its own row below. 0 combined-face hits. |
| 一刀 | apply the revision | JARGON base row (一刀/落刀 family); 落刀 has its own Table A row. 0 repository hits. |
| 玩具（过程义） | toy instance (first use defined) / delete | Academic toy instance may stay with English gloss at first use; process-narrative sense is deleted. 0 repository hits. |
| 铁律 | invariant / hard requirement | JARGON base row; state the rule itself. 31 files. |
| 锻造 | construct | JARGON base row. 0 repository hits. |
| 直排 | reorganize | JARGON base row. 0 repository hits. |
| 回潮 | regression | JARGON base row. 0 repository hits. |
| 新伤 | newly introduced issue | JARGON base row. 0 repository hits. |
| 悬空 | dangling reference (kept only with English gloss) | JARGON base row; half-technical. 0 repository hits. |
| 落盘 | write / persist to disk | JARGON base row (落盘/在盘/入库 family). Highest-density face in this sweep: 61 files. | 1003\ 增;4\.1\ 席位 |
| 在盘 | present in the tree | JARGON base row. 0 repository hits. |
| 入库 | archived / written into the repository | JARGON base row; whole-word judgment only (§1.2). 0 repository hits. |
| 收口 | close out | JARGON base row; verb sense: close out, noun context: close-out. 17 files. | \*\*冲突勘注;\*\*闭合\*\* |
| 定谳 | finally established | JARGON base row; in the 65-face consolidated base (gate4_comment_guard.py:72). 10 files. | 定谳.{1,3}\*\*判定 |
| 总装 | integration | JARGON base row. 2 files. |
| 挂账 | pending item | In the 65-face consolidated base (gate4_comment_guard.py:71); JARGON base v1.3 row (遗留事项). 0 repository hits. | \*\*未消解项;\*\*结清\*\*;\*论文7\ 正 |
| 整改波 | revision round | JARGON base v1.1 row (整改轮次/修订批次). 0 repository hits. |
| 候施工票 | pending work item | JARGON base v1.1 row (候审工作项). 0 repository hits. |
| 算术马 | primary arithmetic component | JARGON base v1.1 row (arith workhorse). 0 repository hits. |
| 终门 | final validation | JARGON base row. 0 repository hits. |
| 门禁 | acceptance check | JARGON base row. 0 repository hits. |
| 过闸 | pass the acceptance check | JARGON base row. 0 repository hits. |

## 4. Table B — tool-repository inventory expansion (sweep-discovered faces)

| 黑话 (jargon face) | 标准 (standard expression) | 语境注记 (context note) |
|---|---|---|
| 台账 | ledger (data surface) / record list (generic prose) | Ledger is the repo's data-format name (`probe --out ledger.json`, `sync-ledger`); generic prose says record list. 52 files. | 1003\ 增;4\.1\ 席位;消费\ 归一\* |
| 回执 | execution record | In the 65-face consolidated base. 2 files. | 1003\ 增;4\.1\ 席位;\*AI\ 味词;\*\*《形式化;\*\*三轮术语;层源；回执＝;嵌入认证载体;据」·席\ 1;笔\*\*（对账 |
| 工单 | task instruction | In the 65-face consolidated base and gate4 extended family (gate4_comment_guard.py:173). 16 files. | 1003\ 增;4\.1\ 席位;锚面刷新工单 |
| 哨 / 哨兵 | watcher | The tool `cw_sentinel.py` is an identifier; narrative 哨/哨兵 → watcher (same family). 哨兵 is banned outright on the .v-comment track (65-face base). 38 files. | 旗舰认证面／ |
| 探针 | probe (tool citation) / check (generic sense) | The `probe` tool (`wash/probe_engine.py`, cw.sh probe) is an identifier; generic prose sense → check. 探针 banned outright on the .v-comment track. 44 files. | \*\*公理审计;嵌入认证载体;表新增「探针 |
| 分诊 | triage | Standard English term — translation mapping, not a purge; `ci_triage.py` identifier stays. 22 files. |
| 判词 | conclusion | In the 65-face consolidated base; `verdict` is reserved for the JSON schema field name (pushci verdict states). 22 files. |
| 判类 | classification | Classification of failing runs into the family spectrum. 36 files. |
| 炉 | build | 红炉 → failing build (红炉分诊 → failing-build triage, Table C). 21 files. |
| 绿（工程义） | passing | 全绿 → all passing; 绿判四件套 → four-point pass criterion (Table C). 68 files. | \*\*四关通过 |
| 闸（工程义） | check / preflight check | 发射闸 → preflight check. `gate4` identifiers (gate4_comment_guard.py, GATE4 tokens) stay verbatim. 40 files. |
| 发射 | initiate / emit | 发射闸 → preflight check; 单探禁发射 → a single-probe round must not initiate (Table C). 18 files. |
| 疏通 | clear blockages | The `unclog` tool name is an identifier; prose → clear blockages / unclog as verb. 18 files. |
| 堵 / 堵账 | blocked items / blockage record | Blockage-record context (unclog --audit baseline). 28 files. |
| 兜底 | fallback | Standard English — translation mapping, keep as fallback. 29 files. |
| 自愈 | automatic recovery | Self-heal acceptable with first-use gloss; preferred form automatic recovery. 10 files. |
| 候令 | pending execution | Banned face in gate4 extended family. 10 files. | 1003\ 增 |
| 收官 | wrap-up | 1 file. | 1003\ 增;4\.1\ 席位 |
| 现势 | current state | 21 files. | 1003\ 增;4\.1\ 席位;笔\*\*（对账;锚面刷新工单 |
| 旗舰 | flagship | In the 65-face consolidated base; 旗舰定理 → flagship theorem. 6 files. | \*\*主定理\*;\*论文7\ 正;中）｜旗舰（;旗舰认证面／;通过／旗舰→ |
| 实勘 | verify | In the 65-face consolidated base. 4 files. |
| 收割 | close out | In the 65-face consolidated base. 4 files. |
| 装机 | register | In the 65-face consolidated base; single-character 组装 is not triggered (assembly guard). 1 file. |
| 派发 | assignment | Narrative sense; the `red_dispatch.py` identifier stays. 4 files. |
| 喂参 | pass parameters | In the 65-face consolidated base. 1 file. |
| 直喂 | pass directly | In the 65-face consolidated base. 7 files. |
| 直配 | direct match | In the 65-face consolidated base. 1 file. |
| 回收 | restore / recover | In the 65-face consolidated base; toolchain-restore context (doctor). 1 file. |
| 换装 | restate | In the 65-face consolidated base. 1 file. |
| 宣言 | declaration | In the 65-face consolidated base. 1 file. |
| 干跑 | dry run | Standard English — translation mapping, keep as dry run. 39 files. |
| 对拍 | differential comparison | 双器对拍 → two-scanner differential run. 18 files. |
| 手术 | operation | registry union 手术 → union operation. 13 files. |
| 钦名 | designated | 钦名模板库 → designated template library. 11 files. |
| 榜 | top list / ranking | TOP 榜 → top list. 12 files. |
| 普查 | survey | token 级限定名普查 → token-level qualified-name survey. 18 files. |
| 断链 | broken linkage | dyld 工具链断链 → toolchain linkage failure. 18 files. |
| 归一 | normalize | Standard term — translation mapping, keep as normalize (净名归一 → name normalization). 24 files. | 消费\ 归一\* |
| 洗形 | shape normalization | `wash_shape.py` / `wash-shape` identifier stays; prose → shape normalization. 18 files. |
| 正典（内部行话义） | canonical | canonical is the standard English term and is kept; the internal-canon sense maps to canonical specification. 45 files. |
| 缝合 | splice | In the 65-face consolidated base. 2 files. |
| 上车 | onboard | In the 65-face consolidated base; process word, mapped to onboard in prose. 1 file. |
| 摘牌 | delisted | In the 65-face consolidated base. 1 file. |
| 计功 | credit tally | In the 65-face consolidated base. 1 file. |
| 双杀 | double failure | In the 65-face consolidated base. 1 file. |
| 击坠 | shot down | In the 65-face consolidated base. 1 file. |
| 翻牌 | overturned | In the 65-face consolidated base. 1 file. |
| 清盘 | liquidated | In the 65-face consolidated base. 1 file. |
| 增薄 | thinned | In the 65-face consolidated base. 1 file. |
| 机判 | machine ruling | In the 65-face consolidated base; → machine-checked decision. 1 file. |
| 卸出 | unloaded | In the 65-face consolidated base. 1 file. |
| 环账 | cyclic account | In the 65-face consolidated base. 1 file. |
| 批次 | batch (process sense) | gate4 extended family (战役组织族). 1 file. | 波（修订波次 |
| 对表 | cross-check against the reference | gate4 extended family (gate4_comment_guard.py:173). 1 file. |
| 断点 | checkpoint | gate4 extended family; resume-point sense. 1 file. |
| 白名单 | allowlist | gate4 extended family; exemption-list sense. 1 file. |
| 炸了 | failed | Colloquial family (gate4_comment_guard.py). 1 file. |
| 翻车 | regression | Colloquial family. 1 file. |
| 踩坑 | pitfall (avoid; state the defect) | Colloquial family. 1 file. | ｜坑／踩坑→ |
| 漏网 | missed | Colloquial family. 1 file. |
| 波次 | work stream / wave-number (deleted from prose) | gate4 extended family (战役组织族); 4 files. | 等）、波次（ |
| 派单 | ticket assignment | gate4 extended family (gate4_comment_guard.py:173). 1 file. |
| 交棒 | handoff (process narration — delete, state facts) | gate4 extended family. 1 file. |
| 停写令 | write freeze | gate4 extended family. 1 file. |
| 候查 | pending verification | JARGON base v1.5 row (候令/候查 family). 1 file. | 1003\ 增 |
| 收账 | account closing (deleted from prose) | gate4 extended family. 1 file. |
| 红屏 | failure output | gate4 extended metaphor family. 1 file. |
| 亮红 | showing failure | gate4 extended metaphor family. 1 file. |
| 秒红 | immediate failure | gate4 extended metaphor family. 1 file. |
| 假绿 | spurious pass | gate4 extended metaphor family. 1 file. |
| 假红 | spurious failure | gate4 extended metaphor family. 1 file. |
| 红温 | overheated state | gate4 extended metaphor family; Annotation whitepaper §3 v1.3 row (高温状态). 1 file. |

## 5. Table C — phrase-level mappings

| 黑话 (jargon phrase) | 标准 (standard expression) | 语境注记 (context note) |
|---|---|---|
| 红是数据非器红 | a failing result is data, not a tool failure | Repo maxim; 27 files. |
| 绿判四件套 | four-point pass criterion | 15 files. |
| 缺省干跑 | dry run by default | Default-dry-run discipline stated in tool Purpose fields. |
| 一键流水线 | single-command pipeline | 一键 16 files. |
| 无据不铸 | evidence required before issuance | tools/wash_shape.py:578,602,630. 2 files. |
| 单探禁发射 | a single-probe round must not initiate | net-probe stability-window rule. 9 files. |
| 洗形器 | shape-normalizing tool | `wash-shape` identifier stays. |
| 红炉分诊 | failing-build triage | `triage` identifier stays. |

## 5b. Table D — English colloquial / hyperbole / slang family (M-wave section 4 extension)

| 黑话 (jargon face) | 标准 (standard expression) | 语境注记 (context note) |
|---|---|---|
| wave（组织义） | work stream | 七工具波 → seven-tool release; the release sense stays on ledger surfaces. |
| seat | agent | M-wave campaign-organization family; seat numbers never enter prose; the one-worker-per-seat topology wording (seat-worker) stays on ledger and identifier surfaces. |
| seat-worker | agent | Compound residue of the earlier agent / seat-worker hybrid; prose uses agent. |
| campaign | effort / work stream | M-wave campaign-organization family; preset name `campaign_set_diamond` (tests/fixtures/header_map_v1.json) is data and stays. |
| dispatch（叙述义） | route | `red_dispatch.py` identifier stays. | ^#?\s*dispatch\s+red-event router |
| handover | — (delete the narration) | Process narration; state facts instead. |
| landing | integration | M-wave campaign-organization family. |
| retrofit | adaptation | M-wave campaign-organization family. |
| trivial（夸饰义） | — (delete, or state the actual fact) | Hyperbole ban, M-wave §四. |
| obvious（夸饰义） | — (delete) | Hyperbole ban. |
| hack | — (state the actual limitation) | Slang family (gate4_comment_guard.py). |
| workaround | — (state the actual limitation) | Slang family. |
| FIXME / XXX / HACK | — (remove) | Slang family, word-boundary match. |
| born-in-place | — (remove; state the actual provenance) | gate4 extended family (gate4_comment_guard.py:173). |

## 6. Identifier-position exemption register

The following faces are banned on prose surfaces but are **tool/toolchain identifiers in this repository and stay verbatim** (backtick-cited in prose; never rewritten in code, flags, schemas, or route tables):

`probe`, `wash-shape` / `wash_shape.py`, `wash`, `unclog`, `ledger` / `sync-ledger`, `sentinel` / `cw_sentinel.py`, `triage` / `ci_triage.py`, `dispatch` / `red_dispatch.py`, `cure` / `cure_applier.py`, `chain` / `chain_graph.py`, `gate4` / `gate4_comment_guard.py`, `pushci`, `BORN-CLEAN` (verdict token), `campaign_set_diamond` (preset name), `GATE-*` tokens.

## 7. Relation to the Annotation Standard Card

The card (`docs/annotation-standard-v1.0-20261113.md`) §4 defines the ban and its grading (jargon hit = error; Chinese-character residue and over-long header = warn); this table defines the replacement for every banned face and the sense boundaries for context-sensitive ones. When a prose face is not listed here, the card's default criterion applies: a sentence whose comprehension requires internal project context is non-conforming, and its standard form is the neutral, self-contained statement of the same fact.