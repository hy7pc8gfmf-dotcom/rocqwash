<!-- README-cw.zh.md — 中文原版留档（bilingual transition archive · 20261113）-->
<!-- English-first 正版：[README-cw.md](README-cw.md)（双语过渡期以英文主版为正；工具名/旗标/路径/退出码语义两版一致）-->
<!-- 计数行 re-sync 20261121（随正本 96aa710/3f781a1/2220dca 三波推进补账）：64 路由 / 62 工具·MCP 42 能力·锚 tag rw-v0.1.1-20261117·表补 tag 后 22 路由；其余正文仍为 20261113 转档原文（corpus）-->

> **English-first version:** see [README-cw.md](README-cw.md) — 本文件为 `cw.sh` 速查文档的原中文全文留档
> （翻译替换波 20261113·双语过渡期·内容与英文主版互引；术语以黑话→标准表述对照表为准）。

# cw.sh — 统一入口速查（正式名 rocqos·链接名 rocqwash·64 路由 / 62 工具）/ Unified entry quick reference

`cw.sh` 是 rocqwash v29-v32 七工具＋20261111 五工具＋v37 三器＋v38 一器＋v39 三器（doc-lint/netname-normalize/select-audit）＋v40 一器＋v45 一器＋v46 两器（route/audit）＋v47 一器（registry-fix）＋norm-lint 一器（批注面规范化 linter·共二十五个）的**一键调用入口**（repo 根；此枚举为 25 器，其中 22 器载于主表、netname-normalize／select-audit／render-events 三器载于下方第二表；入口现势合计 64 路由 / 62 工具）：

```
bash cw.sh <tool> [args...]
```

- **零配置**：路径全部相对仓根（ROOT 取自脚本所在目录），仓随迁随用；
- **透传**：参数与退出码 1:1 直转（`exec`），不改写、不模拟；
- **bash 3.2 兼容**：macOS 自带 `/bin/bash` 可直接跑；只读路由层，自身零写盘；
- **与 `cli/rocqwash` 互补**：后者路由 v29 前七模块（scan/names/wash/verify/
  seam/certify/watch）；v29-v32 工具所在目录已含多个通用入口，模块级自动路由
  的歧义保护（exit 4）不覆盖它们——本入口按工具名显式补位。20261111 五工具
  （doctor/net-probe/triage/union/pushci）同落 `tools/` 多入口目录，同此显式名
  补位路由。


> 正式名 **rocqos**（Rocq 运维套件·Rocq operations suite）·链接名仍 `rocqwash`。现势锚=tag `rw-v0.1.1-20261117`（公开仓）。全量契约面=[docs/CAPABILITY-INDEX.md](docs/CAPABILITY-INDEX.md)·MCP 面=[docs/mcp.md](docs/mcp.md)·语言引擎=[seeds/engines/ENGINES.md](seeds/engines/ENGINES.md)·协议=AGPL-3.0-or-later＋CLA。

## 中文速查表

| 工具 | 目标脚本 | 用途 | 一行示例 |
|------|----------|------|----------|
| `scan4` | `scan/scan_v4_token.py` | token 级限定名普查（限定名/遮蔽源/追踪 id） | `bash cw.sh scan4 --file demo.v --json report.json --text` |
| `cure` | `wash/cure_applier.py` | 消费位治愈正典包（**dry run by default**，`--apply` 才写盘） | `bash cw.sh cure --file demo.v --apply` |
| `probe` | `wash/probe_engine.py` | 批量闭包相容探针（候选清单×世界目录→rc 分流台账） | `bash cw.sh probe --candidates list.tsv --src src/ --world world/ --out ledger.json` |
| `chain` | `tools/chain_graph.py` | 多份 probe 台账合并→链根图＋TOP 榜 | `bash cw.sh chain l1.json l2.json --md top.md --top 25` |
| `sync-ledger` | `tools/ledger_sync.py` | probe 台账×状态台账 TSV 合并同步 | `bash cw.sh sync-ledger --probe ledger.json --ledger status.tsv --out new.tsv --report sync.json` |
| `erasure` | `verify/erasure_classifier.py` | 提取擦除位分类顾问（.mli 逐位归类） | `bash cw.sh erasure --mli out.mli --md-out ledger.md` |
| `dual-scan` | `scan/dual_scan.py` | 双器对拍（scan_v4_token×mac_stmt_scan 逐件差异） | `bash cw.sh dual-scan --dir src/ --out report.json` |
| `doctor` | `tools/toolchain_dyld_doctor.py` | dyld 工具链断链诊断（批量 EXIT=134 面·只诊断＋restore 建议·**禁代执行**） | `bash cw.sh doctor --worker PATH --donor DIR --json dyld.json` |
| `net-probe` | `tools/net_probe.py` | 网络窗探针（双探稳窗·a single-probe round must not initiate·HTTPError 即可达） | `bash cw.sh net-probe --rounds 2 --interval 60 --stable-window` |
| `triage` | `tools/ci_triage.py` | CI failing-build triage（五族+绿炉判类谱·a failing result is data, not a tool failure） | `bash cw.sh triage --repo ORG/REPO --run ID --logs` |
| `union` | `tools/registry_union.py` | 注册册 union operation（main 为底＋对 merge-base 真独有尾插·**dry run by default**） | `bash cw.sh union --base b --main m --branch x --kind order --json r.json` |
| `pushci` | `tools/pushci.py` | 修复后推送 CI single-command pipeline（五段管线 preflight 发射闸→push→watch→heal→verdict±merge·v35 四器 subprocess 编排零新引擎·verdict 七态 `success\|fix-content\|toolchain\|unstable\|heal-exhausted\|gate4-block\|dry-run` 对应退出码 0/1/2/9） | `bash cw.sh pushci --repo-path . --branch feature/x --json report.json` |
| `sentinel` | `tools/cw_sentinel.py` | 实时动态哨（三路信号源 CI runs/台账链根/buildlog 词面→JSONL 事件流·once/loop 双模·判类全权在 ci_triage·**零动作是缺省**·`--on-red-preset` 五预设可重复链式按序一败续行——unclog/pushci/wash-shape/triage/cw-doctor·各承缺省干跑铁律·与 `--on-red` 互斥·旁路动作必伴 `--emit` 双路同守卫 rc=2） | `bash cw.sh sentinel --once --watch-ledgers ledgers/ --on-red-preset unclog --on-red-arg src=src/ --emit events.jsonl --json r.json` |
| `wash-shape` | `tools/wash_shape.py` | shape-normalizing tool·正典形五洗流水（词面/token/头注/行尾/锚·plan 缺省零写盘·`--apply` 落刀后复跑五洗复核·③头注模板源三路探测：`--header-map` 逐件数据 > `--header-map-preset` 钦名模板库 `tests/fixtures/header_map_v1.json`（战役正典蒸馏·金标引据在册·schema `rocqwash-header-map/1`）> env·同槽显传互斥 rc=2） | `bash cw.sh wash-shape --file demo.v --header-map-preset campaign_set_diamond --json plan.json` |
| `unclog` | `tools/unclog.py` | 疏通堵塞闭环引擎（probe 归集→chain_graph 挑根→cure_applier apply→复核→verdict `unclogged\|wall\|rounds-exhausted\|audit`·dry run by default·frozen 在册红拒·`--audit` 只读堵账基线零写盘自证·与 `--apply`/`--loop` 互斥·`--probe-parallel K` 探针并行度透传 probe_engine `--jobs`·timing 段 jobs 维度入账同候选面异 K 前后跑可比） | `bash cw.sh unclog --src src/ --world world/ --audit --probe-parallel 2 --json r.json` |
| `cw-doctor` | `tools/cw_doctor.py` | 综合体检器·四域聚合（环境 dyld／网络 net_probe／注册册锚正典形审计／堵账 probe_engine＋chain_graph 逐域 subprocess 编排既有一器→综合健康分 0-100＋verdict `healthy\|degraded`＋advice 处置清单·**只诊断禁代执行**·a failing result is data, not a tool failure·schema `rocqwash-cwdoctor/1`·`--injector` 离线可测） | `bash cw.sh cw-doctor --json r.json --registry order.txt` |
| `doc-lint` | `tools/doc_lint.py` | 文档←→实现一致性三查器（①cw.sh 头注/usage/hint/case 四处工具表互检＋tools/ 通用入口对账 ②CASES vs tests/README.md vs README.md 计数三处对账 ③doc 引用旗标 vs 各器 `--help` 实出逐枚对照·verdict `consistent\|drift`·a failing result is data, not a tool failure·schema `rocqwash-doclint/1`·`--repo` 被审仓根缺省本仓） | `bash cw.sh doc-lint --repo . --json doclint.json` |
| `baseline-diff` | `tools/baseline_diff.py` | 堵账基线对比器（两份 unclog `--audit` 基线 argv 序=旧→新→`new_blocks`/`resolved_blocks`/`persistent` 三清单＋`score_delta`·verdict 四态 `improved\|degraded\|stable\|incomparable`·账面自洽预检拒手编·timing 不入对比·a failing result is data, not a tool failure·schema `rocqwash-baseline-diff/1`·入仓规程见 [examples/baselines/README.md](examples/baselines/README.md)） | `bash cw.sh baseline-diff audit-wash-20261101.json audit-wash-20261111.json --md diff.md` |
| `dispatch` | `tools/red_dispatch.py` | 红事件路由器（哨红事件→动作预设·三档 preset `report-only\|suggest\|auto`·**缺省 report-only 零执行**·suggest 出可复制命令块·auto 显式才代跑 60s 帽 rc≠0 入账不改退出码·防重 state＋cooldown·路由全挂既有 cw.sh 路由零新引擎·A 族内容红禁代修出 fix 清单·schema `rocqwash-red-dispatch/1`） | `bash cw.sh dispatch --event-file events.jsonl --preset suggest --json route.json` |
| `audit` | `tools/registry_audit.py` | 注册册卫生审计器（order.txt/_CoqProject 双册**只读**四账出账：重复行/锚撞文本/顺序号形/形怪/缺锚/孤儿/live 拓扑引用＋`--fix-plan` 确定性处方零写盘·**`--apply` 不存在**·键式/锚正典直用 registry_union 零重造·病灶是数据恒 exit 0·schema `rocqwash-registry-audit/1`·真仓活跑前置注记（v40 基线规程同律 [examples/baselines/README.md](examples/baselines/README.md)：真树活跑归主会话·席面只证器 selftest/夹具级）） | `bash cw.sh audit --order order.txt --project _CoqProject --live-src src/ --fix-plan --json audit.json` |
| `registry-fix` | `tools/registry_fix.py` | 注册册处方执行器（`audit --fix-plan` 处方逐条落刀·三类处方 DEDUP 保首/锚刷/ORPHAN-ADD skip·**dry run by default**·`--apply` 落刀后断言三判（dup 零残留/锚撞零增/孤儿不增）炸即回滚·staging 全内存零写盘·同参纪律 audit↔执行器逐字咬合·schema `rocqwash-registry-fix/1`） | `bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --json fix.json` |
| `norm-lint` | `tools/norm_lint.py` | 批注面规范化 linter·report-only 首形（机检 `.py`/`.sh`/`.md` 散文面：头注横幅＋五字段块 `Purpose.`/`Interface.`/`Dependencies.`/`Evidence.`/`Exit-codes.` 逐字；jargon 映射表面词边界·反引号引文豁免；逐文件 CJK 残留 warn；禁类 warn；头注预算 30 行；`*.zh.md` 与 `docs/zh/` 留档跳过；findings 是数据——退出码不因其升格·schema `rocqwash-norm-lint/1`） | `bash cw.sh norm-lint --tree .` |
| `help` | — | 总帮助；`help <tool>` 看该工具一行提示 | `bash cw.sh help probe` |

典型流水线（发现→治愈→复核）：

```
bash cw.sh scan4 --file demo.v --json census.json      # 1 survey
bash cw.sh cure   --file demo.v                        # 2 干跑看方案
bash cw.sh cure   --file demo.v --apply               # 3 apply（写盘）
bash cw.sh scan4  --file demo.v --json after.json      # 4 复扫应为零
```

CI 红炉修复链（doctor→net-probe→pushci(含 watch+heal)→triage）：

```
bash cw.sh doctor --json dyld.json                              # 1 dyld 断链诊断（批量 EXIT=134 面·restore 建议只打印禁代执行）
bash cw.sh net-probe --rounds 2 --interval 60 --stable-window   # 2 双探稳窗（连续两轮全端点可达才准发射·a single-probe round must not initiate）
bash cw.sh pushci --repo-path . --branch feature/x --json report.json   # 3 single-command pipeline（preflight 内复跑 doctor＋net-probe 双闸→push→watch CI→heal automatic recovery rerun→verdict±--merge·verdict 七态见上表）
bash cw.sh triage --repo ORG/REPO --run ID --logs               # 4 verdict≠success 时红炉分诊（a failing result is data, not a tool failure·按族给 action）
```

> 手动老链仍在册可单独用：`python3 certify/push_gate.py window ...` 推窗四判据
> ＋裸 `git push`。pushci 的 preflight 发射闸只复跑 doctor＋net-probe 两闸（可选
> `--pre-scan-gate4` 头注预扫）——套件绿/behind=0 等推窗四判据不在此册，pass the acceptance check
> 纪律仍归 `certify/push_gate.py`。

注册册卫生闭环（audit→fix·两器两态·干跑先行·v47）：

```
bash cw.sh audit        --order order.txt --project _CoqProject --live-src src/ --fix-plan --json audit.json   # 1 只读审计出四账＋确定性 fix-plan 处方（零写盘）
bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --json plan.json   # 2 干跑预演（逐条 md5 账＋skip 清单·零写盘·断言 NOT-RUN）
bash cw.sh registry-fix --audit-json audit.json --order order.txt --project _CoqProject --anchor-src src/ --apply --json fixed.json   # 3 apply（断言三判：dup 零残留/锚撞零增/孤儿不增·炸即回滚）
bash cw.sh audit        --order order.txt --project _CoqProject --live-src src/ --json after.json   # 4 复审对账（duplicates 应清零）
```

> `--audit-json` 须为同参 `audit --fix-plan` 产出（处方行号系绑定被审册面·
> 异册即用法错 exit 2）；ORPHAN-ADD 缺模板序号/缺 md5 与 anchor-missing 病灶
> 归 skip 清单如实直传人工分判（禁机械造锚）；audit 计数>0 恒 exit 0（红是
> 数据非器红）。真树 `--apply` 活跑归主会话（器 selftest/夹具级全验在册）。


## 速查表·后继波新增（tag `rw-v0.1.0-20261114` 之后·至现势）

> 本表 42 行＝先前已载的 20 行（至 tag `rw-v0.1.0-20261114`）＋tag 之后新增的
> 22 行；后者前 15 行已随 tag `rw-v0.1.1-20261117` 入册，后 7 行
> （jargon-map-sync/repair-weekly/selfevolve-round/pin-repair/learning-
> feedback/b-gate/tree-audit）为该 tag 之后现势工作树新增。两表（上表＋本表）
> 合计覆盖现势全部 64 路由（62 工具：64−2 别名 ci-triage→triage·
> baseline-diff-facade→baseline-diff）。tag 后新增的 22 行多为
> 递归代面（auto-round 轮次＋代理波＋automatic recovery watch 成为常态变更生产者之后）的
> 产出与守卫器——失败分类/分诊接口/修复手册见
> [docs/ci-whitepaper-recursive-era-v1-20261116.md](docs/ci-whitepaper-recursive-era-v1-20261116.md)
> （zh 存档同目录 `.zh.md`·配套机读表 [docs/ci-triage-table.json](docs/ci-triage-table.json)）。

| 工具 | 目标脚本 | 用途 | 一行示例 |
|------|----------|------|----------|
| `netname-normalize` | `tools/netname_normalize.py` | `.v.v` 双后缀净名归一器（映射表可出可施，`--apply` 落改） | `bash cw.sh netname-normalize --dir <value> --apply` |
| `select-audit` | `tools/select_audit.py` | 批选清单对树 order 文件的全表 grep 剔重审计 | `bash cw.sh select-audit --order <value>` |
| `render-events` | `tools/render_events.py` | 事件流 JSONL 到 markdown 记录的渲染器 | `bash cw.sh render-events --events <value>` |
| `registry-regen` | `tools/registry_regen.py` | 贡献面注册行到合并目标线的再生成器（基线/贡献两仓双 ref、分片表、路径表均参数化） | `bash cw.sh registry-regen --base-repo <value> --apply` |
| `contrib-intake` | `tools/contrib_intake.py` | 外部贡献 intake 检查器：四道只读闸核验后出结论（贡献仓/基线仓/ref/路径/jargon 映射均参数化） | `bash cw.sh contrib-intake --contrib-repo <value>` |
| `evolve` | `tools/evolve.py` | 自演化引擎 v1：从 watcher 事件与记录面生成演化草案并登记（sentinel/suite/registry 系旗标面在卷） | `bash cw.sh evolve --draft-out <value> --suite-now` |
| `vacgen` | `tools/vacgen.py` | Lean vacuity 探针骨架生成器：四层形状识别（前提分解、taxonomy 查表、置信评分、分层回归），含零编译覆盖 preflight 与难度地图（`--preflight-all`） | `bash cw.sh vacgen --in <value> --force` |
| `ci-triage` | `tools/ci_triage.py` | 拉取并分诊失败 CI 炉的日志，输出分诊结论（`--offline` 可改走本地日志面） | `bash cw.sh ci-triage --offline <value> --logs` |
| `baseline-diff-facade` | `tools/baseline_diff.py` | 对比两份基线文件，产出增减报告（JSON/markdown 双出形） | `bash cw.sh baseline-diff-facade <old> <new> --json <value>` |
| `exp-append` | `tools/exp_port.py` | 经验总线追加面（schema rocqwash-exp/1：tool/points/evidence/batch 四字段；幂等 seen 集·重复条目返回既有 id 零写入） | `bash cw.sh exp-append append --tool <tool> --points <text> --batch <batch>` |
| `mcp-server` | `tools/mcp_server.py` | MCP stdio 服务器（tools/list 现 42 能力·EXPECTED_TOOLS=42 见 [docs/mcp.md](docs/mcp.md)·零网络门控·未知方法 -32601） | `bash cw.sh mcp-server tools/mcp_server.py` |
| `periscope` | `tools/periscope.py` | 六源外围情报采集器（观察清单/arXiv 查询/自家 issues→机检情报条目·sha 与时点绑定·撞车检测） | `bash cw.sh periscope --help` |
| `ai-flavor` | `tools/ai_flavor.py` | AI 味词面检测本体：36 词面电池（中文 3 族 10 面、英文词干 15、句式 8、段首 3）加独立 em-dash 电池（U+2014 计数，目标 0），词表只读 `seeds/ai_flavor/word-map.json`（正则字面逐字转录）；命中是数据非错误 | `bash cw.sh ai-flavor --file docs/report.md --json out/ai-flavor-report.json` |
| `ai-flavor-apply` | `tools/ai_flavor_apply.py` | AI 味施加面：全部写入建议性（advisory）且在写入门（`--apply-handoff`／`--provider http`）后，改写一律经改写提供者（handoff 默认零网络：`--emit-handoff` 出段包、回填后 `--apply-handoff` 校验写入；http 腿 default-deny）；中文 10 面永不机改，词干面取 register 中性直陈形，句式面删或改述；预算帽每目标文件每类一轮（`--state`，缺省落目标件旁 `<file>.aiflavor-state.json`）；改写后重跑检测残留=0 方 GREEN | `bash cw.sh ai-flavor-apply --file docs/report.md --emit-handoff out/handoff.jsonl --state out/state.json` |
| `auto-round` | `tools/auto_round.py` | 轮次账回档本体：autonomy.json 双档准入（auto 自批/gated 等人批·同一代码路径 admission_decision）加 §7.2 十键轮次账 JSONL（append-only）加 commit trailer（Rocqwash-Round/-Mode/Salvage-Of）加轻量 ref refs/rocqwash/rounds/\<n\> 加回档=先归档 refs/rocqwash/drift/ 后单 revert 回锚（零 reset 零 force 零 push）加 salvage 精修包往返加振荡告警加 max_unreviewed_rounds 软停（--continue 显式放行）加 status/list/log 三查询面 | `bash cw.sh auto-round status --repo-root .` |
| `i18n-pipeline` | `tools/i18n_pipeline.py` | zh<->en 双向四联动管线编排本体：六操作签名不可变（承 `seeds/i18n/pipeline_stub.py`），本道实现 P0 政策预查（`repo`/`paper`/`supplement` regime 表，refusal 即合法结果 exit 0 记记录）、P1 分段器（保护名单、段=连续散文行区间、段账十键（含 policy_precheck_ref））、P3 四联动编排（L1 termbase 查词、L2 jargon 投影、L3 CJK 零残留加 em-dash 密度、L4 ai_flavor 检测）、P6 段账闭合校验 | `bash cw.sh i18n-pipeline --manifest out/run.json --stage p1 --json out/segments.json` |
| `i18n-translate` | `tools/i18n_translate.py` | 模型处层（P2）：handoff 形默认零网络（`--emit` 出段包、回填后 `--ingest` 十键校验（含 policy_precheck_ref），缺 model_id 或缺标注即违规拒收 fail-loud）；http 形可选 default-deny（OpenAI 兼容端点逐段调用逐段标注 `annotation_site="model"`，NETRED 记录逐次含失败）；prompt 模板 `--prompts <dir>`（缺省内置常数） | `bash cw.sh i18n-translate --segments out/segments.json --emit out/handoff.jsonl` |
| `i18n-verify` | `tools/i18n_verify.py` | P4 机械验证编排（子进程调 `tools/ai_flavor.py`／`tools/norm_lint.py --jargon-map`／`tools/doc_lint.py`，汇成验证矩阵 JSON `rocqwash.i18n.verify/1`）；P5 人工十点单面（`--emit-tenpoint` 出审读表单按目标面形态取变体；`--ingest-tenpoint` 校验结论写回段账 `tenpoint_verdict`；引擎不替人判） | `bash cw.sh i18n-verify --emit-tenpoint docs/report.en.md --json out/tenpoint-form.json` |
| `jargon-apply` | `tools/jargon_apply.py` | 黑话到标准术施加面：数据只读 `seeds/jargon/jargon-map.json`（159 条）；只机改 `disposition:"replace"` 条目；`rewrite_or_delete` 永不机改（findings 列出处置=human）；guarded 行默认拒改上报（`--guarded-interactive` 出逐行问询文件）；preserve 豁免走 exempt 机制；标识符位永不改写（反引号跨段遮蔽）；默认 plan 零写列 before/after 对，`--apply` 后自动重扫残留=0 方 exit 0，幂等 | `bash cw.sh jargon-apply --tree docs --plan --json out/jargon-plan.json` |
| `termbase` | `tools/termbase.py` | 术语库只读薄层：`seeds/termbase/termbase.json` 只读（stdlib json，schema 校验 fail-loud）加 `lookup(term) -> entries` 精确面查词（剥强调与全角括号、按分隔符拆面）加 `--selftest` | `bash cw.sh termbase --selftest` |
| `gap-cluster` | `tools/gap_cluster.py` | TODO-SEAT 与 gap 台账条目聚合为按族形键控的 gap 台账（确定性；重跑字节恒同；零 gap 是数据） | `bash cw.sh gap-cluster --selftest` |
| `row-render` | `tools/row_render.py` | gap 台账经 E4 P2 handoff 形渲染为候选 taxonomy 行（vacgen 准入门＋十点人审门；全准入才落草稿） | `bash cw.sh row-render --gaps <value> --emit <value>` |
| `calibration-ledger` | `tools/calibration_ledger.py` | vacgen v2 预测置信×编译腿实测 rc 配对为逐行校准条目（correlationId·幂等 seen 集·row-rot 信号面；信号是数据） | `bash cw.sh calibration-ledger --selftest` |
| `lean-sweep` | `tools/lean_sweep.py` | vacuity 探针批量 sweep 编排器（分箱/去重/零编译预检铸造；编译腿设计性 SKIP，除非 `--fire` 且工具链探针通过） | `bash cw.sh lean-sweep --selftest` |
| `verdict-diff` | `tools/verdict_diff.py` | sweep 台账机械判官（GREEN/ALERT/BLOCKED/MISSING/SKIPPED-TIERT＋例外清单；ALERT exit 2 stop-work·基线收敛口径） | `bash cw.sh verdict-diff --selftest` |
| `symbiosis-bus` | `tools/symbiosis_bus.py` | 跨仓经验总线（`docs/exp-ledger.jsonl`·swap schema `rocqwash-symbio/1`·import 走 exp_port append 面·export/status/diff 只读·设计零网络） | `bash cw.sh symbiosis-bus status` |
| `uplink` | `tools/uplink.py` | 外部回传包 intake 闸（verify/intake/pr-prep·md5 不符或缺声明成员 fail-loud·intake 登记行与调用方钦名草稿为仅有的写面·设计零网络） | `bash cw.sh uplink verify --package <value>` |
| `evolution-dashboard` | `tools/evolution_dashboard.py` | 三常备账自演化仪表盘（经验台账＋轮次台账＋vacgen v2 TODO-SEAT 报告→覆盖率曲线＋轮次转化＋逐轮 gap 温度计·JSON/markdown 双面·常备路径缺失是数据） | `bash cw.sh evolution-dashboard --selftest` |
| `bus-feeder` | `tools/bus_feeder.py` | symbiosis swap 包的 gap 台账投喂器（`rocqwash-symbio/1` 入·TODO-SEAT gap 行出·按 id 与指纹幂等·gap 投喂台账为唯一写面·设计零网络） | `bash cw.sh bus-feeder --selftest` |
| `axiom-guard` | `tools/axiom_guard.py` | 全仓公理卫兵（每个 .v 编译三分类：compile-ok／compile-broken 欠账登记／skip-no-toolchain；compile-ok 件两级检测：逐定理 Print Assumptions survey＋权威 `coqchk -o` 内核复检；Closed 零公理·白名单缺省空·env 门控 rc 111 诚实跳过·零仓写） | `bash cw.sh axiom-guard --repo <value>` |
| `flaky-guard` | `tools/flaky_guard.py` | flaky 隔离卫兵·修复类 E2-3（隔离探针判类：套红单绿=顺序依赖·两境皆红=内容红保持可见；`--move` 隔离入 `tests/advisory_roster.txt` 缺省套件响亮 ADVISORY-OUT 放行·CI flaky-watch 持续观察；对 `tools/repair_scope.py` 范围核查·每类每分支预算帽 2；dry run by default·`--restore` 需绿轮证据） | `bash cw.sh flaky-guard --selftest` |
| `repair-scope` | `tools/repair_scope.py` | E2 卫兵族共享修复范围排除表（frozen LEDGER8/CHECKERS 行运行时读自 `certify/frozen8.py`＋append-only 台账文档＋冻结目录族；逐类可写面＋预算登记；全体修复卫兵导入的单一源） | `bash cw.sh repair-scope --classes` |
| `roster-resync` | `tools/roster_resync.py` | 名册计数漂移卫兵·修复类 E2-2（run_tests.sh CASES 名册为唯一计数权威；tests/README.md＋README.md 的 doc_lint 计数行自其单向重导并原位同步漂移数字；名册文件永不写；dry run by default） | `bash cw.sh roster-resync --selftest` |
| `scheduler-lite` | `tools/scheduler_lite.py` | jargon tier-B 自动档 TODO-SEAT 阈值触发规划器（gap 投喂台账＋vacgen 报告经 `tools/gap_cluster.py`＋`docs/round-ledger.jsonl` 轮次节律→verdict `quiet\|due\|blocked`；点火以 EF 全绿标记为闸；设计干跑：零 apply 零 commit 零网络） | `bash cw.sh scheduler-lite --selftest` |
| `auto-merge` | `tools/auto_merge.py` | X5 自动合并闸判官＋安全轨（六值 mergeability 枚举 `merge-ok\|hold-red\|hold-conflict\|already-landed\|superseded-landed-elsewhere\|escalate-unknown`；五样本校准集 S-1..S-5 钉死；轨=supply/* 头分支白名单＋日预算帽 3＋append-only 合并台账＋合并后红 revert 弧；零网络·dry run by default） | `bash cw.sh auto-merge --selftest` |
| `jargon-map-sync` | `tools/jargon_map_sync.py` | jargon 映射同步·md 表→seed JSON（检测器表策展超集吸收进施加表；单形准入：括注剥离、em-dash 单元格落 rewrite_or_delete、斜杠交替与六个注记守卫标记拒收；既有条目 id/exempts/cross_track_note 保留；精确计数标签；plan 零写缺省·`--apply` 写表） | `bash cw.sh jargon-map-sync --selftest` |
| `repair-weekly` | `tools/repair_weekly.py` | 修复结局台账周分布面·修复类 E6（`docs/repair-ledger.jsonl` 聚合为 ISO 周逐红结局普查＋类/票分布；台账只读·`--out`/`--json` 为仅有的写面；`--record` 在受约词表内追加一行 `rocqwash-repair-ledger/2`·`--apply` 必需） | `bash cw.sh repair-weekly --selftest` |
| `selfevolve-round` | `tools/selfevolve_round.py` | 一次确定性机械轮·cron 面（survey jargon_apply `--plan`→apply→verify py_compile/bash -n 硬闸＋norm_lint/doc_lint 顾问→auto_round commit→push→CI 判官路由；jargon_apply 冻结面排除；零合资格修复=干净空转；apply 残留非零=fail-loud 不 commit） | `bash cw.sh selfevolve-round --dry-run` |
| `pin-repair` | `tools/pin_repair.py` | jargon seed 映射出处 pin 漂移修复·分诊行 R15 自动修复执行器（在同步器零写计划 IN-SYNC 判定后重签漂移 provenance.sources md5 pin；`--plan` 零写·`--apply` 只触 md5 值并复跑 seeds 套件·failing verify 回滚到 apply 前字节） | `bash cw.sh pin-repair --selftest` |
| `learning-feedback` | `tools/learning_feedback.py` | 三常备台账排程反馈面（轮次台账/轮次状态/经验台账只读→`docs/scheduling-feedback.json`：自动对人批轮次拆分＋批准率＋逐类分布＋四态修复结局计数；缺失或损坏输入入 errors 字段绝不猜测） | `bash cw.sh learning-feedback --selftest` |
| `b-gate` | `tools/b_gate_audit.py` | 轮次记录 B 级泛化阈值审计（3 实例且每个由至少 1 个已执行轮支撑；逐类实例与轮次计数＋逐类就绪判定＋显式缺口清单→`docs/b-gate-audit.json`·schema `rocqwash.b-gate-audit/1`；计数自记录实测绝不虚增） | `bash cw.sh b-gate --selftest` |
| `tree-audit` | `tools/tree_audit.py` | `.lean`/`.v` 源树只读树健康审计（单行 JSON survey：总量/声明/不健全特性扫/头注面/逐目录与最大文件表/import 根；字节字面计数经普查 oracle 校准；零子进程零网络零树写） | `bash cw.sh tree-audit --selftest` |

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 通过 |
| 2 | 未知工具（`cw.sh bogus`）；或工具自身 argparse 用法错/断言失败（透传） |
| 9 | 目标脚本缺失（`cw.sh xxx: missing <path>`）；或工具自身目标文件缺失（透传） |
| 其余 | 各工具自身口径 1:1 透传（如 sync-ledger `1`=同步完成带发现·net-probe `1`=不稳窗·doctor `1`=missing-libs·pushci verdict 封册 success/dry-run=0·heal-exhausted/unstable/toolchain=1·fix-content/gate4-block=2·9=目标缺失·cw-doctor `1`=degraded 综合健康分<90 a failing result is data, not a tool failure·doc-lint `1`=drift 文档漂移红是数据非器红） |

## 工作流配合接口（v37 三器共同·配合工作流实时动态提供清洗、shape normalization、排障、疏通堵塞）

v37 三器（`sentinel`/`wash-shape`/`unclog`）共同接口纪律五条——工作流（dynamic
workflow 子代理/后台 bash 任务）按此嵌入，不必懂各器内部：

**① --once/--loop 双模**：`--once` 单轮巡检/闭环出账即退（工作流步骤内联用）；
`--loop --interval S` 长驻哨态（后台 bash 任务用·`--max-rounds N` 轮帽 0=无限；
unclog 用 `--loop-max` 命周数·rounds-exhausted 非终局歇 `--interval` 再下一周）。
wash-shape 缺省即 once（plan 段零写盘），`--loop` 显式开哨态且可与 `--apply`
并用逐轮落刀。`--sleep-scale F` 全睡乘 F（selftest 用 0=零真睡）。

**② JSON-in/JSON-out＋JSONL 事件流**：`--json OUT` 出确定性报告（sort_keys·
schema designated `rocqwash-sentinel/1`·`rocqwash-shape/1`·`rocqwash-unclog/1`·同输入
重跑字节恒同）；loop 态事件逐行 append `--events FILE`（JSONL·逐行 flush·行
schema `rocqwash-sentinel-event/1`，sentinel 事件键含 `seq` 事件流内单调——使用
方按 seq 排序即恢复全局序）。

**③ --injector 离线可测**：子进程调用层罐装（sentinel= canned GitHub API 表
`rocqwash-sentinel-injector/1`·未命中 fail-loud 9 **绝不静默走真网络**；
wash-shape= 引擎 `{rc,stdout,report}` 罐装；unclog= probe/resprobe canned 台账
scenario.json）＋`--sleep-scale 0`——零真网络零真编译于 selftest，工作流演练/CI
全离线。

**④ 退出码 0/1/2/9 口径（a failing result is data, not a tool failure·响亮 stdout）**：

| 码 | sentinel | wash-shape | unclog |
|----|----------|------------|--------|
| 0 | 巡检完成（CI failing/堵塞是事件数据） | clean/shaped | unclogged |
| 1 | —（红走事件流） | partial/plan-miss（洗未尽·响亮出账） | wall/rounds-exhausted（诚实墙·禁硬凑） |
| 2 | 用法错（缺模式/三源全缺/repo 形坏） | 用法错/冻结件红拒/引擎形外退出 | 用法错/注入场景形错 |
| 9 | 信号源不可达（HTTP 4xx·injector 未覆盖·子进程 rc≠0） | 路径缺失 | fail-loud（路径缺失/器红/frozen 不可得） |

**⑤ 典型后台哨命令行**（工作流后台任务逐条照抄·事件流供主流程 tail 使用）：

```
# 哨态：台账链根＋buildlog 双源巡检·JSONL 事件流·seen 幂等（loop 须给 --state-file）
nohup bash cw.sh sentinel --loop --interval 60 \
  --watch-ledgers ledgers/ --watch-buildlog build.log \
  --state-file .sentinel-state.json --emit events.jsonl \
  --json sentinel-report.json >/dev/null 2>&1 &

# 洗形哨态：逐轮 plan→apply apply→复跑五洗复核（--max-rounds 界定）
nohup bash cw.sh wash-shape --dir src/ --loop --interval 300 --max-rounds 8 \
  --apply --events shape-events.jsonl --json shape-report.json >/dev/null 2>&1 &

# 疏通哨态：五步闭环周而复始·wall/unclogged 终局即停即退
nohup bash cw.sh unclog --src src/ --world world/ --loop --interval 600 --loop-max 8 \
  --events unclog-events.jsonl --json unclog-report.json >/dev/null 2>&1 &
```

**⑥ 三典型工作流嵌段**（工作流脚本内联步·全部离线可注入形）：

```
# pushci 嵌段（发射闸→push→watch→heal→verdict·七态封册按退出码分流）
bash cw.sh pushci --repo-path . --branch feature/x --json pushci.json
case $? in 0) : ;; 1|2) bash cw.sh triage --repo ORG/REPO --run ID --logs ;; esac

# unclog 嵌段（堵塞疏通闭环·verdict 三态按退出码分流·缺省干跑看墙账）
bash cw.sh unclog --src src/ --world world/ --json unclog.json
case $? in 0) echo unclogged ;; 1) echo "wall/rounds-exhausted：读 unclog.json wall 账人工判定" ;; esac

# wash-shape 嵌段（正典形五洗·plan 零写盘先行·人审后再 --apply 两段全施）
bash cw.sh wash-shape --file demo.v --json plan.json      # plan 段（rc 0/1 均有账）
bash cw.sh wash-shape --file demo.v --apply --json shaped.json   # apply＋复跑复核
```

> 三器编排而非重造：sentinel 判类全权在 `ci_triage`（subprocess 直调）、链根全权
> 在 `chain_graph`；wash-shape 五洗引擎全 subprocess（gate4/scan_v4/cure_applier/
> comment_sweep/registry_union）；unclog 五步全 subprocess（probe_engine/chain_graph/
> cure_applier/scan_v4_token/frozen8）。工作流调它们即调全部既有引擎。

**⑦ v38 注记（preset／audit／韧性层·20261111）**——三器接口在上述五条纪律上扩面：

- **preset**：sentinel 增 `--on-red-preset NAME`（红事件预设动作·预设即模板
  sugar·v41 预设表数据化扩至五预设：`unclog`＝干跑疏通（**不带 --apply**·
  人审后再落刀）、`pushci`＝`--dry-run` 只打计划、`wash-shape`＝只出 plan
  （**不带 --apply**·plan 零写盘）、`triage`＝对红 run 复诊重判类（repo/run
  事件直替族）、`cw-doctor`＝全缺省体检——各预设自动接驳各器缺省干跑铁律；
  **可重复＝链式**按给定序逐件执行·一败续行不改哨退出码·actions 账每条
  一笔）；展开走与 `--on-red` **同一执行器**（60s 帽·rc≠0 不改哨退出码·
  零新执行路径）；必传参数经 `--on-red-arg K=V` 透传（链式参数面＝全链
  并集）·`{emit_dir}` 取 `--emit` 所在目录；与 `--on-red` **互斥**（同给
  rc=2 fail-loud 禁静默择一）；**旁路动作必伴事件流**——plain `--on-red`
  与 preset 缺 `--emit` 双路同守卫 rc=2（v41 破坏面矩阵 S2 判据转正）。
  wash-shape 同形扩面（v39 轮）：
  ③头注形洗模板源增 `--header-map-preset NAME` 钦名模板（`tests/fixtures/
  header_map_v1.json` 战役正典蒸馏库·schema `rocqwash-header-map/1`·占位全承
  目标件自身 Require 面与既有头注逐字·任一绑不上 plan-miss 不硬造；与
  `--header-map` 同槽互斥 rc=2·模板源探测次序 `--header-map` > preset > env）。
- **audit**：unclog 增 `--audit` 只读堵账基线（单遍 probe 干跑归集→chain_graph
  →出基线报告·`final.verdict=audit` exit 0 红是基线数据非器红·cures 恒 0＝
  零落刀零复核）；**零写盘硬保证**＝`--src` 全文件 md5 清单跑前跑后自证恒同
  （违同 fail-loud 9·染污基线不出账）；与 `--apply`/`--loop` 互斥 rc=2；
  timing 段实测墙钟为报告唯一非确定段——v41 增 `--probe-parallel K` 检验
  并行度透传 probe_engine `--jobs`（timing 段 jobs 维度入账·同候选面异 K
  前后跑可比·--guard 同给建议 K≤2 温控自裁）。
- **韧性层**：CI GET 403/429/5xx 指数退避重试抽公共件 `tools/_http_backoff.py`
  纯函数（`ci_triage`/`cw_sentinel`/`pushci` 三器共享·`--retry-max` 缺省 3·
  Retry-After 秒数头尊重·4xx 语义面不重试）；net-probe 增 `--jitter/--seed`
  （每端点探测前随机微抖·抖散对齐性重试风暴·加法式键缺省零行为变化）；
  pushci 增 `--timeout`（真子进程防挂帽）·sentinel 增 `--subproc-timeout`
  （编排子进程防挂）——**injector canned 路径一律零重试零真网络**（离线可测
  铁律）。各器形详锚其 docstring 与 `--help`。

**⑧ 三嵌段正典样例（examples/workflows/·可整段复制）＋集成白皮书**：

- 嵌段①后台哨：[examples/workflows/backend-sentinel.md](examples/workflows/backend-sentinel.md)
  （⑤ 后台哨命令块整段复制版＋JSONL 消费端 grep/python3 双形＋退出码分支表＋
  dynamic-workflow 嵌段伪码）
- 嵌段②单步推 CI：[examples/workflows/step-pushci.md](examples/workflows/step-pushci.md)
  （⑥ pushci 嵌段展开·`--dry-run` 先行→真发→verdict 七态分流表＋离线演练形）
- 嵌段③堵账疏通：[examples/workflows/loop-unclog.md](examples/workflows/loop-unclog.md)
  （⑥ unclog 嵌段展开·dry run→人审→`--apply`→复核四判＋诚实墙因分派表）
- 集成白皮书：[docs/workflow-integration-whitepaper-v1.0-20261111.md](docs/workflow-integration-whitepaper-v1.0-20261111.md)
  （主会话让路模式／后台任务拓扑／双门并立——推窗四判据×发射闸）
- 实时动态服务运行手册：[docs/ops-realtime-service-v1.0-20261111.md](docs/ops-realtime-service-v1.0-20261111.md)
  （后台哨标准命令与 JSONL 使用／preset 接驳 unclog 全链三判 e2e＝
  `tests/test_relay_e2e.py`·tmp 注入演练实跑原文在册·与器 `--help` 冲突时以器为准）
- 服务层总览（v40）：[docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)
  （三链一图全景＋器面索引·docs 席铸）
- 堵账基线入仓规程（v40）：[examples/baselines/README.md](examples/baselines/README.md)
  （`unclog --audit` 基线命名律 `audit-<域>-<yyyymmdd>.json`／timing 非确定段
  注记／baseline-diff 对比判读与红线纪律·工装席铸）

**⑨ 红事件路由嵌段（v46·red_dispatch 配对例·哨红事件→动作预设路由）**：

```
# 哨态红事件→路由器接驳（--on-red 模板配对例·<json> 取 --emit 事件流同盘
# 路径——哨每遇红事件即以事件流整盘喂路由器·suggest 档零执行出复制块）
bash cw.sh sentinel --once --watch-ledgers ledgers/ --emit events.jsonl \
  --on-red 'python3 tools/red_dispatch.py --event-file <json> --preset suggest'

# 单步直调（不经哨·对既有事件流补一轮路由账·report-only 缺省零执行）
bash cw.sh route --event-file events.jsonl --preset suggest --json route.json
```

> route 是路由而非引擎：五路由（B/E 族→pushci 重派·A 族→manual-fix-note
> 禁代修出 fix 清单·C 族→doctor·blocking→unclog·build-signal→wash-shape）
> 全挂既有 cw.sh 路由零新引擎；三档 preset 缺省 report-only 零执行（红是
> 数据），auto 显式才代跑（60s 帽·rc≠0 响亮入账不改退出码·防重 state＋
> cooldown）；与哨 `--on-red` 配对时占位替换 `{family}/{run}/{repo}` 既有
> 语义不动——路由器自行从事件流读全事件。

## English brief

`cw.sh` is the one-command entry for the seven tools introduced in the
rocqwash v29-v32 waves plus the five tools added on 20261111 plus the three
v37 tools plus the v38 aggregate doctor plus the v39 trio (doc-lint plus
netname-normalize/select-audit) plus the v40 baseline-diff plus the v45
render-events plus the v46 route/audit pair plus the v47 registry-fix
prescription applier plus the annotation-face normalization linter norm-lint
(twenty-five in total — 22 housed in the main table, with the
netname-normalize / select-audit / render-events trio in the second table
above; the entry as a whole now carries 74 routes over 74 tools). It
lives at the repository root:

```
bash cw.sh <tool> [args...]
```

Tool names map 1:1 to the underlying scripts: `scan4`→`scan/scan_v4_token.py`
(token-level qualified-identifier census), `cure`→`wash/cure_applier.py`
(consumer-cure pack, dry-run by default), `probe`→`wash/probe_engine.py`
(batch closure-compatibility probing), `chain`→`tools/chain_graph.py`
(multi-ledger chain-root graph), `sync-ledger`→`tools/ledger_sync.py`
(probe×status-ledger merge), `erasure`→`verify/erasure_classifier.py`
(extraction erasure advisor), `dual-scan`→`scan/dual_scan.py`
(dual-scanner cross-check), and the 20261111 additions `doctor`→
`tools/toolchain_dyld_doctor.py` (dyld toolchain-breakage diagnostics; prints
restore advice, never executes it), `net-probe`→`tools/net_probe.py`
(network-window probe, double-probe stable window), `triage`→`tools/ci_triage.py`
(CI red-run triage), `union`→`tools/registry_union.py` (registry union surgery,
dry-run by default), `pushci`→`tools/pushci.py` (push-CI one-shot pipeline:
preflight emission gate → push → CI watch → heal rerun → verdict ± merge;
seven-state verdict `success|fix-content|toolchain|unstable|heal-exhausted|
gate4-block|dry-run`), the v37 additions `sentinel`→`tools/cw_sentinel.py`
(real-time watch sentinel: CI runs / local ledger chain-roots / buildlog
tokens → JSONL event stream, once/loop dual mode, report-only by default),
`wash-shape`→`tools/wash_shape.py` (canonical five-pass shaping pipeline:
lexical/token/header/EOL/anchor; plan is zero-write by default, `--apply`
re-runs all five passes for verification; the ③ header-pass template source is
probed in order `--header-map` per-file data > `--header-map-preset` named
template library `tests/fixtures/header_map_v1.json` > env, with the two
explicit flags mutually exclusive rc=2), `unclog`→`tools/unclog.py`
(blockage-unclogging closed loop: probe collection → chain-root pick →
cure-applier → re-scan/re-probe → verdict `unclogged|wall|rounds-exhausted`;
dry-run by default, frozen8 red-refusal), the v38 addition `cw-doctor`→
`tools/cw_doctor.py` (aggregate health check orchestrating the existing tools
per domain — dyld environment / net_probe network / registry anchor audit /
probe_engine+chain_graph clog sampling — into a 0-100 score with verdict
`healthy|degraded` and per-domain advice; diagnosis only, never executes
fixes; `--injector`-offline-testable), plus the v39 addition
`doc-lint`→`tools/doc_lint.py` (docs↔implementation consistency linter, three
checks: cw.sh four-place tool-table cross-check + tools/ generic-entry
reconciliation, CASES count three-way check against tests/README.md and
README.md, and doc flag references verified against each tool's real `--help`
output; verdict `consistent|drift`, red is data not tool failure), plus the
v40 addition `baseline-diff`→`tools/baseline_diff.py` (clog-baseline differ:
two `unclog --audit` baselines in argv order old→new → `new_blocks` /
`resolved_blocks` / `persistent` block lists plus `score_delta`, verdict
`improved|degraded|stable|incomparable` with honest refusal on candidate-set
mismatch; red is data, not tool failure; intake protocol at
`examples/baselines/README.md`), plus the v45 addition
`render-events`→`tools/render_events.py` (sentinel-event JSONL → markdown
ledger renderer), plus the v46 additions
`dispatch`→`tools/red_dispatch.py` (red-event router: sentinel red events →
action presets in three presets `report-only|suggest|auto` — report-only
zero-execution by default, suggest prints a copy-paste command block, auto
executes only when explicit under a 60s cap with rc≠0 recorded loudly without
touching the exit code; dedup state + cooldown; all five routes wired onto
existing cw.sh routes, zero new engines; family-A content-red is never
auto-fixed — it emits a fix list), and
`audit`→`tools/registry_audit.py` (registry hygiene auditor: order.txt/
_CoqProject dual-book read-only four-account output — duplicate rows / anchor
collisions / seq-form / malformed / missing anchors / orphans / live topology —
plus a `--fix-plan` deterministic prescription with zero writes; `--apply`
does not exist; keys and the anchor canon are reused from registry_union,
zero re-invention; findings are data, always exit 0), plus
the v47 addition `registry-fix`→`tools/registry_fix.py` (registry
prescription applier: executes the `audit --fix-plan` prescription item by
item in three prescription kinds — DEDUP keep-first / anchor re-stamp /
ORPHAN-ADD skip; dry-run by default; `--apply` writes with three post-write
assertions (duplicates zero-residue / anchor-collision text zero-addition /
orphans non-increasing) and rolls back on any blast; staging is fully
in-memory zero-write; same-parameter discipline binds the audit JSON to the
applier's `--order`/`--project` verbatim), plus
`help`. The v37 tools share a
common workflow-interface discipline (once/loop dual mode, deterministic
JSON reports + JSONL event streams, `--injector` offline canned testing,
exit codes 0/1/2/9 where red is data not tool failure) — see the Chinese
section 「工作流配合接口」 above. v38 extensions to that interface (preset
table expanded in v41): sentinel
`--on-red-preset` (five canned red-event actions — unclog dry-run / pushci
dry-run / wash-shape plan-only / triage re-triage / cw-doctor checkup —
each honoring its tool's dry-run-by-default discipline, repeatable for
chained sequential fire where one failure continues the chain without
touching the sentinel exit code; mutually exclusive with `--on-red`;
both plain and preset forms require `--emit`, rc=2 otherwise), unclog
`--audit` (read-only clog baseline with an md5 no-write proof;
`--probe-parallel K` threads the probe fan-out through probe_engine
`--jobs` with a jobs dimension recorded in the timing section for
cross-K comparisons), and a shared resilience layer
(`tools/_http_backoff.py` exponential
backoff, net-probe `--jitter/--seed`, pushci `--timeout`, sentinel
`--subproc-timeout`). Three copy-paste canonical workflow blocks live in
`examples/workflows/` (`backend-sentinel.md`, `step-pushci.md`,
`loop-unclog.md`), with the integration whitepaper at
`docs/workflow-integration-whitepaper-v1.0-20261111.md`; the ops runbook for
the realtime service (backend sentinel standard commands, JSONL consumption,
and the `--on-red-preset unclog` relay e2e in `tests/test_relay_e2e.py`) is at
`docs/ops-realtime-service-v1.0-20261111.md`.

Design contract: all paths are resolved relative to the repository root from
the script's own location (no hardcoded paths; the repo can be cloned anywhere);
arguments and exit codes pass through 1:1 via `exec` (fail-loud, never
rewritten); requires only `bash` 3.2 and `python3` ≥ 3.9, no third-party
dependencies; the entry itself is a read-only dispatcher and writes nothing.
`bash cw.sh help <tool>` prints a one-line usage hint per tool. It complements
the existing `cli/rocqwash` router, which covers the pre-v29 modules — the
v29-v32 tools live in directories with several generic entries each, where the
module auto-router's ambiguity guard declines to guess, so this entry routes
them by explicit tool name. Self-test: `bash tests/test_cw_entry.sh` (also part
of `bash tests/run_tests.sh`).
