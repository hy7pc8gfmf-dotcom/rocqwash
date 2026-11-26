> **rocqwash** — operating as **rocqos**, the *Rocq operations suite*: a self-evolving operations layer for Rocq-based constructive-proof repositories. Built on Rocq 9.3. The "rocq" prefix is used with attribution to the [Rocq prover](https://rocq-prover.org) and its community; rocqos is an independent operations layer, not affiliated with Inria and not part of the Rocq distribution.

# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine
> 中文镜像 · 英文正本：[README.md](README.md) · 英文项目页：[README_EN.md](README_EN.md)

[![CI](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/ci.yml) [![macOS advisory](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml/badge.svg?branch=main)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/actions/workflows/mac-verify.yml) [![certification](https://img.shields.io/badge/certification-machine--checked-brightgreen)](docs/ci-whitepaper-recursive-era-v1-20261116.md) [![Rocq](https://img.shields.io/badge/Rocq-9.3.0-blue)](https://rocq-prover.org) [![tag](https://img.shields.io/badge/tag-rw--v0.1.1--20261117-blue)](https://github.com/hy7pc8gfmf-dotcom/rocqwash/tree/rw-v0.1.1-20261117)

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. Where proof-unblocking is concerned, it replaces probabilistic guessing with mechanically verifiable checks: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: 凡可用类型论结构性判据机检的，一律不交给概率模型猜。
> (What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.)

> **服务层总览**: [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)（三链一图全景＋器面索引）· [docs/rocqwash-service-campaign-total-v1.0-20261111.md](docs/rocqwash-service-campaign-total-v1.0-20261111.md)（v35-v41 七波累账总报告）· [docs/ops-live-run-log-20261111.md](docs/ops-live-run-log-20261111.md)（conclude / close三闸实录）· [docs/roadmap-v43-plus-20261111.md](docs/roadmap-v43-plus-20261111.md)（v43+ 候选池·决策料非排程令：①②④⑦ 已执行——④ 见下方 v47 增补、①②⑦ 见下方 v48 增补；③⑤⑥⑧ 待指派）· [docs/ops-sentinel-长驻手册-v1.0-20261112.md](docs/ops-sentinel-长驻手册-v1.0-20261112.md)（哨长驻运维手册 v1.0·部署/使用/轮转恢复）· [docs/勘形-multi-repo-Main仓适配-20261112.md](docs/勘形-multi-repo-Main仓适配-20261112.md)（路线图⑦ Main repository CI 形制勘察·适配分级即用 4／小改 3／中改 2）

单行快照，最新在上；每条链接该轮的 docs/ 件面。完整条目原文见本文件的 git
历史（CHANGELOG.md 收录 v35-v39、v53、v58-v66）。

- **v57（2026-11-13·evolve cycle-2 执行轮）**: 六个器面按注释规范卡英文化（norm_lint 错误质量合计 111→0），新增两条 triage 证据注记矢量且未识别红类不充谱；norm_lint v3 基线落档（`docs/norm-lint-baseline-20261113.{json,md}`）；文档检查、全量套件、shell 语法检查全过。
- **v56（2026-11-13·九器翻译收口）**: 九个器面翻译完成，接口边界机检零改动（AST 对照 9/9 恒同），新增 zh 存档 7 件；norm_lint 对照 v53 基线 error 2441→2377（`docs/norm-lint-baseline-20261113.json`）。
- **v55（2026-11-13·信号→任务书生成器）**: `tools/evolve.py`（draft-only 闸：永不执行候选、永不写仓）；首轮真信号实跑（`docs/演示-evolve首轮-20261113.md`）。
- **v54（2026-11-13·贡献者隔离工装）**: 规程 `docs/contrib-isolation-protocol-v1.0-20261113.md`、只读四闸收件检查器 `tools/contrib_intake.py`、缺省 dry run 处方重生器 `tools/registry_regen.py`；管线在 Set PR#48 实跑。
- **v53（2026-11-13·注释面规范化地基）**: 注释规范卡 v1.0、黑话→标准对照表 v1、`tools/norm_lint.py` 检查器、首个全仓基线账（`docs/norm-lint-baseline-20261113.{json,md}`）；完整条目见 [CHANGELOG.md](CHANGELOG.md)。
- **v52（2026-11-13·Main 勘形＋首个活体闭环）**: Main 新内容勘形；一次 CI 回归被分类并由同事提交 ≈20 分钟自动复绿、全环零人工（`docs/判例-R3复发-route2tierA自愈-20261113.md`）；哨事件消费演练。
- **v51（2026-11-12·哨韧性轮）**: 传输层有界重试退避＋逐源 fallback、triage E 变体结论位校验、监督壳部署形（`examples/sentinel_supervisor.sh`）。
- **v50（2026-11-12·14 事件分类交叉验证）**: triage 器对照人工复核，run 级一致率 5/8、行级 10/14；分歧逐件在册，识别红类谱不充谱。
- **v49（2026-11-12·Main 仓适配轮）**: Main CI 形 fixtures＋triage/pushci 消费面、Main 全史 triage 账（369 runs）、战役总报告 v2.0（`docs/rocqwash-service-campaign-total-v2.0-20261112.md`）。
- **v42（2026-11-11·conclude/close 总档轮）**: 总报告、演练实录、路线图三档入 docs/（链接见上方总览行）；基线绿（文档一致性 drift=0、破坏面矩阵 17/17、全量套件零红）。

## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## 本页术语

下述词汇在全文直接使用不再解释。更完整定义：
[docs/zh/architecture.md](docs/zh/architecture.md) 与英文项目页
[README_EN.md](README_EN.md)（"What it is" 与 "Why" 两节）。

- **Prop 泄漏（Prop leakage）** — 语句仍以 `Prop` sort 陈述、未落到 Set 载体谓词形；扫描器把此类行标为 RED station。`Set` 与 `Prop` 在 Coq/Rocq 类型论中互斥，故此区分是机检事实而非风格偏好。
- **洗（wash）** — 用逐字精确串替换＋计数断言把被标记语句改写到正典 Set 载体形（Qlt→QltT、Qle→QleT'、==→QeqT 等）；构造上幂等，第二遍零改动。
- **QeqT / QltT / QleT'** — 洗的目标 Set 载体谓词形；Qeq/Qlt/Qle 为标准 Prop 载体原形。QeqT 目标拒绝 Qeq 等式改写——Set/Prop 互斥的推论。
- **-face（面）** — 工具操作的 `.v` 文件区域：statement-face＝语句行，annotation-face＝注释/头注文本，区别于证明体。
- **station（站）** — 一处被报告的位置：扫描器/探针列出的（名称， 行）对，交人工裁决；RED station＝判为 Prop 泄漏。
- **probe（检验）** — 试编译：候选文件在 world 内以 `rocq c` 编译，按退出码分拣为可洗／生而净／红因各类。
- **gate4 / gate6 / gate7** — 正典路径上的编号检查点：gate4＝注释卫生；gate6＝普查包装（`verify/verify_gate6.py`）；gate7＝英文化适配（CJK→0＋五字段头注帽）。
- **W13** — generation-gap 世代缝隙指纹探针（`seam/seam_probe.py`）：按四种机制指纹分类洗后语句仍红的原因，逐一映射到处方。
- **R4** — 提取侧三源审计：裸全提取 magic 计数、探针双面、五式 grep 三源须全净（提取侧合取现为部分完成——见英文项目页诚实边界册）。
- **N=N** — 名表断言：洗前读出 N 条语句名，断言洗后文件按同序恰有这 N 条名（不符即退出码 2）。
- **world（世界）** — 带自身依赖闭包的源树自足副本；探针对着 world 编译，多世界（UNION v2）清单逐世界冻结 md5 树。

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push (push pinned to a fixed remote IP) + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: 25 deterministic idempotent rewrite patterns (measured at pack v1.4.1: the legacy five plus statement-face, S07-lineage and CI-extraction-defect families), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine; the per-pattern inventory is the pack itself (`wash/cure_pack.json`) | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |
| `tools/pushci.py` | Push-CI one-shot pipeline orchestrator: five stages (preflight emission gate, push, CI watch, heal, verdict with optional PR merge), seven-state verdict (`success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run`), exit codes 0/1/2/9; orchestrates the v35 four tools via subprocess, zero new engines; offline-injectable (`--injector`/`--git-caller`/`--sleep-scale`); per-stage detail in `tools/pushci.py --help` and the v36 addendum below | Deterministic state machine over mechanical gates; LLM cannot be trusted to decide emission windows or auto-heal policies |

## Repository Layout / 目录结构

```
rocqwash/
├── cli/rocqwash          # 统一 CLI 入口 — unified CLI entry (scan/names/wash/verify/seam/certify/watch)
├── docs/
│   ├── zh/architecture.md  # 架构文档（中文）— architecture doc (Chinese)
│   └── en/architecture.md  # 架构文档（英文镜像）— architecture doc (English mirror)
├── CONTRIBUTING.md       # 贡献指南（流程/代码规范/测试要求/cpu_guard 使用说明）
├── examples/             # 全链演示样例 + Makefile — single-file full-chain demo (scan→names→N=N→wash→verify)
├── scan/  names/         # 已实现通用逐件工具（mac_stmt_scan.py / scan_v4_token.py / dual_scan.py）— implemented generic tools
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + work-stream tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + work-stream tools
├── verify/               # verify_vo.py four-point pass criterion + 战役验证工装 — four-pack green verdict + work-stream verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（91 例）/ CI 工作流占位 — test suite (91 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> 状态快照 2026-11-01（巡检打磨席 rqsup4）：`scan/`、`names/`、`tools/cpu_guard.sh`、
> `cli/`、`examples/`、`docs/`、`tests/`（34 例自测套件）已实现并实测；`wash/`
> （`wash_engine.py` 基于 ledger 的洗引擎＋`_abl1_wash.py` 战役件＋`world_hook.py` 世界基校验钩子）、
> `verify/`（`verify_vo.py` four-point pass criterion＋战役工装＋`verify_gate6.py` gate6 薄包装）、
> `seam/`（`seam_probe.py` W13 四机制指纹probe (tool citation) / check (generic sense)）、`certify/`（`freeze_manifest.py`
> 两层冻结清单＋`push_gate.py` 推窗四判据/UNION v2 深件·agent rqwash2＋`frozen8.py`
> 八件冻结名单机检）、`watch/`
> （`watch.py` CI 监控/钉 IP 推送/ls-remote 确证·零 route 结构保证）、`tools/`
> （`select_audit.py` 选件审计器）、`recipes/`（`S07_projection_reanchor_E5.md`＋
> `ENBIG7_same_domain_collision_PW1.md`·判例处方件双件）、`wrapper/`
> （适配层族：gate7 probe (tool citation) / check (generic sense)链 `coqc_shim.sh`＋`gate7_probe.sh`·cpu_guard 直通
> `guard.sh`·scan 指认包装 `scan_station.py`·agent rqadapt·三判例验收站
> `precedent_station.py`·rqsup4）已落地；
> `verify/` 统一入口已conclude / close（显式子动词分派 `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`·
> rqadapt 落三子动词 2026-10-31·rqsup4 四巡补 verify_gate6 20261101）；`certify/`
> 同款显式分派 `cli/rocqwash certify freeze|push_gate|frozen8`（rqsup4 五巡补
> frozen8 20261101）——冻结件零改动；R4 提取侧三源为待办。
> v30 增补（20261103·探测战役工具化轮）：`wash/probe_engine.py` 批量闭包相容
> probe (tool citation) / check (generic sense)引擎＋`tools/chain_graph.py` 多账合并链根图＋`tools/ledger_sync.py`
> probe×状态ledger同步器（E1 去重/E3 幽灵/列校验 fail-loud）——承 W13/W25/ledger
> v2 三原型 1:1 泛化，全路径参数化零硬编码；自测套件扩至 40 例全绿。
> v31 增补（20261103·shape normalization战役实战判例工具化轮）：`wash/cure_pack.json` v1.1
> 五式→十四式（Qle/Qlt 载体面降移两形·refl 桥开门·Import 遮蔽直通面双变体
> exclusive-group fail-loud·NatLe 前提提升＋intros-tail 守卫 drop 包裹）＋
> `wash/cure_applier.py` face-regex 域引擎（face/proof 域触发·逐面 token 守卫·
> 文件级前置条件）＋`wash/comment_pack.json`＋`comment_sweep.py` 注释域 sweep
> 旁车（嵌套注释+字符串感知状态机·旗词换形·数据驱动头注换代·w7 code 行全等
> 投影幂等断言）＋`tools/ledger_sync.py` v2.1（items 子键壳识别＋裸 dict 元数据
> 键响亮滤除＋GEN-DIVERGENCE 双代分歧出账——分歧优先序成文：kept 代＝下游账
> basis 榜系消费代，dropped 代只注记不弃账）；自测套件扩至 41 例全绿。
> v32 增补（20261103·S07 世系适配式工具化轮·W66 支撑席提案实装）：
> `wash/cure_pack.json` v1.1→v1.2 十四式→十九式（cure32_A 参数化壳去除·
> :=-binding-right 守卫／cure32_B 记号重绑 line-insert 引擎／cure32_C 投影桥
> 裸名形 face+proof 域／谓词面收敛 token_map——换名目标须取消费供给引理结论面
> 同一常量名·delta 等价异名编译绿而提取插 Obj.magic／binder 壳 report-only
> 站型——手刀辖区报站·术后站数归零）＋`scan/dual_scan.py` 双器differential comparison驱动
> （scan_v4＋mac_stmt_scan 双扫×逐件差异报告 only_v4/only_stmt）＋cure_applier
> 器修（exclusive-group 冲突＋--json 路径 report write / persist to disk·rc=4 文档值）；
> 自测套件扩至 42 例全绿（门控 S07 编译弧：failing→机械 cure→binder operation→passing→
> 提取 Obj.magic 0/0）。
> v34 增补（20261104·CI #178 提取面缺陷族逆向修订轮）：`wash/cure_pack.json`
> v1.2→v1.3 十九式→二十四式——task instructionfinally established两类缺陷族入 cure：E3 泛型接口实例化
> （cure34_E3_use_station_spec 抽象载体应用站改写特化 shim 调用＋cure34_E3_spec_shim
> line-insert 末个 Import 后生成具体载体中间 Definition；shim 体保留被特化的抽象
> 应用、face_exclude 护体防二遍自缠）＋E2 记录多态字段（cure34_E2_field_annot
> 无标注消费面重述为显式类型标注中间 Definition＋cure34_E2_use_arity 下游元数
> 站随行＋cure34_E2_station_unannot report-only 清账站）——五式全复用 v32 引擎
> 零新引擎；门控 E2/E3 编译弧第一手：pre-fix 编译绿（提取时缺陷族）、修后绿、
> E2 消费面 `'a1 -> 'a1`→`nat -> nat`、消费单元 magic 0/0、world 访问器债=1
> 机械钉（实体修复工作流域·canonical_note 记界）。自测套件 43 例。
> v36 增补（20261111·推送 CI single-command pipeline轮）：`tools/pushci.py` 修复后推送 CI
> single-command pipeline编排器——五段管线：preflight initiate / emit闸（dyld doctor verdict＋net-probe
> 稳窗双闸·可选 gate4 头注预扫·禁initiate / emit律代码化）→push（重试 3 发×45s＋
> https://github.com/ 形 ghproxy 换路·pushed_sha=ls-remote 远端 tip）→watch
> （status-only 口径轮询·updated_at 冻结非僵尸判据）→heal（ci_triage family
> 分派：B/E 族→稳窗过→rerun·帽 --max-heal 3·A 内容红禁代修·C toolchain 停·
> 表外族禁自动 rerun 人工指认）→verdict±merge（七态 success/fix-content/
> toolchain/unstable/heal-exhausted/gate4-block/dry-run·退出码 0/1/2/9）——
> v35 四器（doctor/net-probe/triage/union）subprocess 编排零新引擎；离线可测
> 注入内建（--injector/--git-caller/--sleep-scale·零真网络零真 push）；自测
> 套件扩至 48 例。
> v37 增补（20261111·实时动态三器轮·用户令：配合工作流实时动态提供清洗、shape normalization、
> 排障、clear blockages堵塞）：`tools/cw_sentinel.py` 实时动态哨（三路信号源 CI runs/ledger
> 链根/buildlog 词面→JSONL 事件流·once/loop 双模·classification全权在 ci_triage·链根
> 全权在 chain_graph·零动作是缺省）＋`tools/wash_shape.py` shape-normalizing tool·正典形五洗
> 流水（词面/token/头注/行尾/锚五洗全 subprocess 编排既有引擎·plan 缺省零写盘·
> --apply apply后复跑五洗复核）＋`tools/unclog.py` clear blockages堵塞闭环引擎（probe 归集
> →chain_graph 挑根→cure_applier apply→rescan/resprobe 复核→verdict
> unclogged/wall/rounds-exhausted·dry run by default·frozen 在册红拒·诚实墙禁硬凑）——
> 三器共同接口纪律五条：JSON-in/JSON-out（--json report·schema designated
> rocqwash-sentinel/1·rocqwash-shape/1·rocqwash-unclog/1·sort_keys 字节恒同）·
> 退出码 0/1/2/9（a failing result is data, not a tool failure·响亮 stdout）·--once/--loop 双模（--interval
> 可调·JSONL 事件流 --events）·离线可测（--injector 子进程调用层罐装＋
> --sleep-scale·零真网络零真编译于 selftest）·编排而非重造（零新引擎）；
> `cw.sh` 入口扩至十五工具（sentinel/wash-shape/unclog 三路由·四处同步）·
> 工作流配合接口速查见 [README-cw.md](README-cw.md)「工作流配合接口」节；
> 自测套件扩至 51 例（47 过/4 例正本缺卷让席·真本机全跑）。
> v38 增补（20261111·工作流集成与综合体检轮·四席并铸＋集成席conclude / close）：
> `tools/cw_doctor.py` 综合体检器·四域聚合（①环境＝toolchain_dyld_doctor 编排
> ②网络＝net_probe --rounds 1 ③注册册锚正典形审计 ④堵账＝probe_engine 真探
> ＋chain_graph 链根——逐域 subprocess 编排既有一器零新引擎→综合健康分 0-100
> ＋per-domain verdict＋advice 处置清单·schema rocqwash-cwdoctor/1·--injector
> 离线可测·只诊断禁代执行·a failing result is data, not a tool failure healthy=0/degraded=1）；工作流集成
> 面：`examples/workflows/` 三嵌段正典样例（backend-sentinel 后台哨／step-pushci
> 单步推 CI／loop-unclog 堵账clear blockages·全部离线可注入形）＋
> `docs/workflow-integration-whitepaper-v1.0-20261111.md` 集成白皮书（主会话
> 让路模式／后台任务拓扑／推窗四判据×initiate / emit闸双门并立）；韧性层：共享退避纯函数
> `tools/_http_backoff.py`（CI GET 403/429/5xx 指数退避·Retry-After 尊重·
> ci_triage/cw_sentinel/pushci 三器接入）＋net_probe `--jitter/--seed` 抖散
> ＋pushci `--timeout`／sentinel `--subproc-timeout` 子进程防挂（injector
> canned 路径一律零重试零真网络）；接口扩面：sentinel `--on-red-preset`
> （unclog dry run/pushci dry-run 预设动作·与 --on-red 互斥）＋unclog `--audit`
> 只读堵账基线（--src 全文件 md5 跑前跑后自证零写盘·verdict=audit exit 0）；
> `cw.sh` 入口扩至十六工具（cw-doctor 路由·四处同步）；自测套件扩至 52 例
> （t_cw_doctor 最小自测壳两判·缺壳集成席自补）。
> v39 增补（20261111·文档核与接驳实战轮·工装席四铸＋集成席conclude / close）：
> `tools/doc_lint.py` 文档←→实现一致性三查器（①工具表查＝cw.sh 头注/usage/
> hint/case 四处互检＋tools/ 通用入口reconcile ②计数查＝tests/run_tests.sh CASES
> vs tests/README.md vs README.md 三处reconcile ③旗标查＝docs 引用旗标 vs 各器
> --help 实出逐枚对照（--help 真跑·帽 20 器）——schema rocqwash-doclint/1·
> verdict consistent|drift·a failing result is data, not a tool failure·--selftest tmp 迷你仓六矢量·
> 零网络零写盘）；接驳实战核：`tests/test_relay_e2e.py` cw_sentinel
> --on-red-preset unclog 全链三判 e2e（事件触发→--audit dry run rc=0 零写盘
> md5 自证→JSONL 同盘 unclog report 路径逐字节differential comparison·全 canned 罐装·实跑原文
> 落 docs/ops-realtime-service-v1.0-20261111.md 实时动态服务运行手册）；
> shape-normalizing tool扩容：wash_shape `--header-map-preset NAME` designated头注模板库
> `tests/fixtures/header_map_v1.json`（战役正典蒸馏·gold-standard引据在册·schema
> rocqwash-header-map/1·与 --header-map 同槽互斥）＋cure_pack v1.4 语料survey
> 轮单式扩容：`cure39_ifq_connective_qualify` 接口量化连接词限定（20261111
> 证据门控survey·b48-52 wash-work stream 引据 commit 9a51c74·RI0 语境件语句面裸
> lt/le/plus 钉 @S01_BaseRing 投影形·树正典形；survey纪律 held——引据较薄之形
> 全数留 pending 不铸·夹具 cure39_t13/cure39_plain）。`cw.sh` 入口扩至十七工具
> （doc-lint 路由·四处同步）；自测套件扩至 54 例（t_relay_e2e 三判 e2e＋
> t_doclint 最小自测壳三判·缺壳集成席自补）。
> v40 增补（20261111·正典化巩固波·四席并铸＋集成席conclude / close）：`tools/baseline_diff.py`
> 堵账基线对比器（两份 unclog --audit 堵账基线 argv 序=旧→新→new_blocks/
> resolved_blocks/persistent 三清单＋score_delta·verdict improved/degraded/
> stable/incomparable·账面自洽预检拒手编基线·候选面四元组两账比对跨集如实拒判·
> timing 段不入对比＝基线唯一非确定段——schema rocqwash-baseline-diff/1·红是
> 数据非器红）＋`examples/baselines/` 堵账基线入仓规程（命名律
> audit-<域>-<yyyymmdd>.json·真树dry run产·timing 注记·工装席铸）；破坏面复核矩阵
> `tests/test_destructive_matrix.py` 17 行拒写判据一行一拒写（会写盘器×写面×护栏
> 锚 file:line：unclog×4/wash_shape×4/pushci×3/cw_sentinel×2/registry_union×2/
> cure_applier×2·全 tmp fixture＋injector 罐装零真网络零真仓零真编译·矩阵红＝
> 护栏破响亮列破口·破坏面席铸）；稳态三器扩容：cw_sentinel `--emit-max-bytes`
> JSONL 轮转（.1/.2 保留 2 代·seq 跨代续号）＋`--rebuild-state` 崩溃恢复
> （损坏 state 红拒 9 禁静默重建·显式重建唯一合法路）、unclog `--state-file`
> 同形哨态 seen 差分（red-new 事件 only-new·与 cw_sentinel state 同形互读写·
> --rounds/--loop 与 --audit/--state-file 两组互斥 rc=2·损坏红拒 9）、
> wash_shape --loop 事件流同形对齐（rocqwash-sentinel-event/1·seq 跨进程续号
> ＋ts=off 注记）＋plan 跨轮缓存（源件 md5 变→重算·恒同→hit 复用·plan_cache
> 响亮出账）（稳态席铸·selftest 十二/十三/十八矢量扩容）；`cw.sh` 入口扩至
> 二十工具（baseline-diff 路由·六处同步含 legal 两清单与计数行）；服务层总览
> [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
> （三链一图全景＋器面索引·docs 席铸）；自测套件扩至 56 例
> （t_destructive_matrix 17 行判据＋t_baseline_diff 最小自测壳三判·缺壳集成席
> 自补）。
> v41 增补（20261111·四席并铸＋集成席conclude / close）：cw_sentinel 预设表数据化扩至
> 五预设（unclog/pushci/wash-shape/triage/cw-doctor·各承dry run by defaultinvariant / hard requirement）＋
> `--on-red-preset` 可重复链式（按给定序逐件执行·一败续行不改哨退出码）＋
> on-red 双路同守卫（plain `--on-red` 与 preset 缺 `--emit` 皆 rc=2·破坏面
> 矩阵 S2 判据转正·矩阵仍 17 行）；probe_engine `--jobs` K 并行分片（缺省
> 1 逐件串行零漂移·典序account closing (deleted from prose)输出序不随完成序漂移·候选重名 fail-loud rc=2）；
> unclog `--probe-parallel` probe (tool citation) / check (generic sense)并行度透传（audit timing 段 jobs 维度入账·
> 同候选面异 K 前后跑可比）；性能剖面规程 docs/perf-profile-v1.0-20261111.md
> ＋examples/baselines/perf-README.md（K=1/2/3 三跑采集·两轴分离律·工装席
> 铸）；push_gate 推窗四判据×pushci preflight initiate / emit闸双门normalize评估
> docs/push-gate-dual-door-assessment-v1.0-20261111.md（只评估零代码变更·
> 护栏席铸）。自测套件保持 56 例（52 过/4 例正本缺卷让席）。
> v46 增补（20261112·红事件路由与注册册卫生审计集成轮·三席铸＋集成席conclude / close）：
> `tools/red_dispatch.py` 红事件路由器（哨红事件→动作预设路由·三档 preset
> report-only/suggest/auto·**缺省零执行**·suggest 出可复制命令块·auto 显式
> 才代跑 60s 帽 rc≠0 响亮入账不改退出码·防重 state＋cooldown·五路由全挂
> 既有 cw.sh 路由零新引擎：B/E 族→pushci 重派·A 族内容红禁代修出 fix 清单·
> C 族→doctor·blocking→unclog·build-signal→wash-shape·schema
> rocqwash-red-route/1·铸席铸）＋`tools/registry_audit.py` 注册册卫生
> 审计器（order.txt/_CoqProject 双册**只读**四账出账：重复行/锚撞文本/顺序
> 号形/形怪/缺锚/孤儿/live 拓扑引用＋`--fix-plan` 确定性处方零写盘·
> **`--apply` 不存在**留执行器·键式/锚正典直用 registry_union 零重造·病灶
> 是数据恒 exit 0·schema rocqwash-registry-audit/1·铸席铸·真仓活跑前置
> 注记承 v40 基线规程律 examples/baselines/README.md「真树活跑归主会话·席面
> 只证器级」）＋`docs/评估-push_gate推窗四判据与pushci归一-20261111.md`
> 推窗四判据×pushci normalize可行性评估（只评估零代码变更·评估席铸·与 v41
> 护栏席同题独立成文两判互证·裁决同为保持双门并立）；`cw.sh` 入口扩至
> 二十三工具（route/audit 两路由·四处同步·评估文档为文档无路由）；
> 自测套件扩至 58 例（t_red_dispatch/t_registry_audit 两例最小自测壳·
> 缺壳集成席自补）。
> v47 增补（20261112·门控编译弧翻绿与注册册处方执行器轮·三席铸＋集成席conclude / close）：
> 门控编译弧总开关翻绿（路线图候选④·任务书编号 ⑧A 案·两路径取 A＝指 9.3
> 多路器 `mac93_install_work/opam93/rocq93/bin/rocq`·v43 第三发 27/27 同源
> 实证）——`tests/run_tests.sh` 总开关缺省探测四路径（env 已设则尊·外部 clone
> 显式指认不受扰）：`ROCWASH_ROCQ`→t_cure_pack 编译 check 段＋t_probe_engine
> 真 rocq 节；`GATE7_PROBE_SCRIPT`/`GATE6_SCRIPT`→Set repository gate7/gate6 正本在卷
> 指认解锁 t_gate7_wrapper/t_verify_gate6；`BORN_WORLD_ROCQ`→CW Live rocq 缺卷
> 9.3 代役解锁 t_gate6_born_wrapper——诸闸位判据语义零改动（在即跑·缺才 SKIP·
> env 缺且缺卷仍 SKIP）只翻缺省面；t_quad8_check 系四仓副本群缺卷族（另族）
> 不在本案；翻绿是「现役世界代际」passing·非 9.1 复绿（诚实记界承 v43 9.3 门控弧
> 27/27 同口径）。＋`tools/registry_fix.py` 注册册处方执行器（registry_audit
> `--fix-plan` 处方逐条apply·三类处方 DEDUP 保首/锚刷/ORPHAN-ADD skip·**缺省
> dry run**·`--apply` apply后断言三判炸即回滚·staging 全内存零写盘·schema
> `rocqwash-registry-fix/1`·真树 `--apply` pending execution不入本波）；＋哨真仓首战
> （`tools/cw_sentinel.py --loop` 真实战役窗口挂哨·JSONL 事件流 events=33·
> v46 红事件路由消费面实战）；`cw.sh` 入口扩至二十四工具（registry-fix 路由·
> 四处同步）；自测套件扩至 59 例（t_registry_fix 直挂器 --selftest 八矢量·
> 集成席直挂）。
> v48 增补（20261112·DS4 三账conclude / close＋哨长驻运维手册＋Main 仓勘形轮·三席铸＋集成席conclude / close）：
> 路线图① DS4 K=3 账 `examples/baselines/audit-k3-20261112.json` 真树堵账基线落仓
> （27 件 RC0 red=0·timing jobs=3·probe_chain_s=165.202/total_s=169.684）——与 K=1/K=2
> 同候选面经 baseline_diff 双向 verdict=stable 三账齐（190.728/101.916/165.202·
> 加速比 1.87× 于 K=2 档位现拐点·K=3 负边际加速如实录·perf-profile §五三行占位
> 主会话已回填实数）；
> 路线图② `docs/ops-sentinel-长驻手册-v1.0-20261112.md` 哨长驻运维手册成档
> （部署落位规范／事件流消费与 render_events/red_dispatch 接驳／轮转与恢复纪律／
> v44-v48 实证账引用——零码改零新器零新旗标）；
> 路线图⑦ `docs/勘形-multi-repo-Main仓适配-20261112.md` Main repository CI 形制勘察档
> （只读零动码·api.github.com 实取现役 coq93.yml 形·适配分级 verdict＝
> 即用 4／小改 3／中改 2——pushci PR 路线 mirror-blind 咬合失配为最大缺口·
> 跨仓越权写盘non-negotiable constraint保持）。
> 组件级细节见 [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md)；贡献流程见
> [CONTRIBUTING.md](CONTRIBUTING.md)。

## 递归演进层：自验证、MCP 与能力索引

2026-11-19 起工具链闭合自身环路：审计自己的树、修复自己的红例、验证自己的验证器。

- **递归代工具族**（`tools/`）：`tree_audit.py`（只读树健康普查·`.v`/`.lean` 源树）、`axiom_guard.py`（全仓公理守卫·逐定理一枚 `Print Assumptions` 判决）、`auto_round.py`（轮次准入/提交/账本/回滚）、`scheduler_lite.py`（TODO-SEAT 阈值触发器）、`repair_scope.py`（修复面共享排除名册）、`repair_weekly.py`（修复结果周分布）、`selfevolve_round.py`（单发确定性机械轮：survey→apply→验证→提交→push→CI 判读）。
- **元验证层**：`tests/test_tool_selftests.py` 枚举 selftest 宇宙——57 器非 `_` 前缀 `tools/*.py`（60 件减 3 件 `_` 助手）——逐器运行声明的 `--selftest`，failing、缺失或未豁免即响亮失败；套件挂载为 `t_tool_selftests` 例。
- **方法论正典**：[docs/recursive-evolution-whitepaper-v1.0-20261121.md](docs/recursive-evolution-whitepaper-v1.0-20261121.md)——七律、七支柱、§7 2026-11-19/21 链实录。
- **CI 红例分类表**：[docs/ci-triage-table.json](docs/ci-triage-table.json) v1.5——19 类（R1–R19），上方递归代 CI 白皮书徽章背后的分类表。
- **逐器契约面**：[docs/CAPABILITY-INDEX.md](docs/CAPABILITY-INDEX.md)——一器一条目，每条七字段（路径、一行用途、调用形、可复制示例、imports、网络面、SKIP 面）。
- **MCP stdio 服务器**：`tools/mcp_server.py`——stdio 上换行分隔 JSON-RPC 2.0、三方法、57 能力名册（冻结 `SELFTEST_ROSTER_COUNT`；`tests/t_mcp_face.py` `EXPECTED_TOOLS = 57` 机检）；协议面与安全面见 [docs/mcp.md](docs/mcp.md)。

## Quick Start

Prerequisites (three lines):

- `python3` ≥ 3.9 — no third-party packages required
- a Rocq/Coq 9.x toolchain on `PATH` — needed only for the compile-verification pieces; everything else runs without it
- Windows: use Git Bash as your shell (the toolchain is bash + python3)

```bash
git clone https://github.com/hy7pc8gfmf-dotcom/rocqwash.git
cd rocqwash
bash tests/run_tests.sh          # self-test suite; exit 0 = all green
```

First run — scan a demo source for statement-face Prop leakage:

```bash
python3 scan/mac_stmt_scan.py --file examples/demo_prop_leak.v
# RED stations: ['demo_eq_self', 'demo_eq_sym', 'demo_le_eq', 'demo_le_self', 'demo_mixed']
```

First verification — comment-hygiene gate on a clean sample:

```bash
python3 verify/gate4_comment_guard.py --file tests/fixtures/gate4_clean_sample.v
# [gate4ext] ... 件数=1 (files=1)  PASS=1  FAIL=0  REVIEW(人工复核)=0 (human-review items)  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```


```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing); writes my_proof_washed.v
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Extract statement names and assert N=N against the washed file
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487
# --expect N asserts the extracted statement-name count equals N (487 is an example value)

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json   # first freeze = the certify sub-verb; second = the action name (the pair is freeze|check)
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper: pins git push to a fixed pre-resolved remote address — --pin-ip rewrites the remote URL host to that IP, --url-host keeps the original name as the Host header — so the push does not depend on DNS resolution at push time (dry-run by default; masked output; --yes actually pushes)
python3 watch/watch.py push --repo . --remote origin --pin-ip 140.82.113.3 --url-host github.com

# Post-push ls-remote double-read confirmation
python3 watch/watch.py confirm --repo . --remote origin --branch main --sha <sha>

# Equivalent direct invocation
python3 scan/mac_stmt_scan.py --file my_proof.v
python3 names/mac_stmt_names.py my_proof.v --names-out names.txt

# Full-chain demo (scan → names → N=N → wash → verify)
make -C examples demo

# Compile with thermal guard
bash tools/cpu_guard.sh -Reg /tmp/my_reg -Front 0 -Mid 1 -- rocq c -native-compiler no -Q . "" my_proof.v
# -Reg <dir> = a dedicated queue-registration lane; -Front/-Mid = ladder-queue tier cut-offs (FRONT tier runs nice 0, MID tier nice 10) — parameter reference: docs/en/architecture.md §6
```


## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Seven Canonical Steps (不可跳)

第 3 步的洗建立在一个类型论事实之上：`Set` 与 `Prop` 两 sort 在 Coq/Rocq 中互斥，
故 Prop 载体语句是改写到 Set 载体谓词形，而非原位编辑（见「本页术语」）。

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic `436f712100015ff4`＝`.vo` 文件头魔数 / vo newer than v / PA Closed＝Print Assumptions 审计无公理 / coqchk Axioms:none)
5. **R4 three-source conjunction** (bare full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0)
6. **gate7 English化 adaptation** (CJK→0 + five-field header 30-line cap)
7. **N=N name-table assertion** (mac_stmt_names.py ordinal full-equality) + freeze md5

Each step must pass before the next. Any failure = honest WIP, no green-washing.

## Four W13 Seam Mechanisms (Generation-Gap Auto-Classification)

1. **== statement rewrite/ring/reflexivity structurally unusable on QeqT(Id) goals** → flip back via qeq_imp_qeqT first
2. **Keyed-matching instantiation**: supply-side parameter must take the actual shape in the goal
3. **Premiss-carrying lemma consumption**: assert-化 + dual-shore bridge
4. **Cross-line Require topology leak**: statement-level multi-line awareness + driver idempotent resume

## LLM Integration

rocqwash is designed to **complement** LLM agents, not compete with them:

- **LLM excels at**: understanding "what does this math mean" (semantic layer)
- **rocqwash excels at**: ensuring "this proof is real" (mechanical layer)

**Collaboration pattern**: LLM understands → rocqwash diagnoses → LLM fixes → rocqwash verifies → LLM commits → rocqwash certifies.

## Why rocqwash Surpasses LLM/Probabilistic Approaches

The comparison below is a capability statement, not a benchmark claim; each row
names the mechanical mechanism that replaces a guess. It is the mechanical half
of the complement split above: the LLM agent proposes and fixes, rocqwash
verifies and certifies.

| Capability | LLM | rocqwash |
|-----------|-----|----------|
| Prop leakage localization | LLM needs to read entire file and may miss lines | `mac_stmt_scan.py` pins to exact line in milliseconds |
| Missing dependency detection | LLM guesses Require chains | Require line-by-line scan + Set tree diff = mechanical exhaustive, zero omissions |
| Seam type classification | LLM reads error messages and guesses direction | W13 four-mechanism grep fingerprint → prescription mapping = mechanical, not experiential |
| Wash mapping | LLM generates tactics that may hallucinate | Canonical 7-form exact-string replacement + count==1 assertion = idempotent replayable |
| Compile verification | LLM trusts self-report | `world.run("rocq",...)` exit code = deterministic |
| R4 three-source | LLM may miss spots | bare full-closure extraction + probe dual-face + five-pattern grep = triple-source conjunction |
| N=N name-table | LLM may miscount | `mac_stmt_names.py` ordinal full-equality assertion = mechanical |
| UNION world integrity | LLM may skip dependency copies | Per-piece md5 manifest = mechanical leak-proof |

**Core barrier**: These capabilities are not "better prompts" — they are structural properties of Coq/Rocq type theory. QeqT-goal Qeq-rewrite impossibility is a corollary of Set/Prop type-theoretic mutual exclusion. No prompt engineering can override type theory.

## License

- **Code:** AGPL-3.0-or-later, see [LICENSE](LICENSE).
- **Audit documents:** `docs/audits/**` and release assets of tags `f1p-audit-*` are CC-BY-4.0, free to reuse with attribution.
- Zenodo record (audit package): DOI 10.5281/zenodo.24238998
- Zenodo (tool release v0.1.0): DOI 10.5281/zenodo.24225678
