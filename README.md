> **rocqwash** — operating as **rocqos**, the *Rocq operations system*: a self-evolving operations layer for Rocq-based constructive-proof repositories. Built on Rocq 9.3. The "rocq" prefix is used with attribution to the [Rocq prover](https://rocq-prover.org) and its community; rocqos is an independent operations layer, not affiliated with Inria and not part of the Rocq distribution.

# rocqwash — Coq/Rocq Constructive Proof Unblocking Engine
> English: [README_EN.md](README_EN.md)

**rocqwash** is a mechanical diagnosis, washing, verification, and certification toolchain for Coq/Rocq constructive mathematics projects. It is designed to **naturally surpass LLM/probabilistic approaches** in proof-unblocking: every diagnostic is a type-theoretic structural property, every fix is idempotent and replayable, every verification is independently reproducible.

> **Core Principle**: 凡可用类型论结构性判据机检的，一律不交给概率模型猜。
> (What can be mechanically verified via type-theoretic structural criteria shall never be delegated to probabilistic models.)

> **服务层总览**: [docs/service-layer-overview-v1.0-20261111.md](docs/service-layer-overview-v1.0-20261111.md)（三链一图全景＋器面索引）· [docs/rocqwash-service-campaign-total-v1.0-20261111.md](docs/rocqwash-service-campaign-total-v1.0-20261111.md)（v35-v41 七波累账总报告）· [docs/ops-live-run-log-20261111.md](docs/ops-live-run-log-20261111.md)（收口三闸实录）· [docs/roadmap-v43-plus-20261111.md](docs/roadmap-v43-plus-20261111.md)（v43+ 候选池·候令未排程）· [docs/ops-sentinel-长驻手册-v1.0-20261112.md](docs/ops-sentinel-长驻手册-v1.0-20261112.md)（哨长驻运维手册 v1.0·部署/使用/轮转恢复）· [docs/勘形-multi-repo-Main仓适配-20261112.md](docs/勘形-multi-repo-Main仓适配-20261112.md)（路线图⑦ Main 仓 CI 形制勘察·适配分级即用 4／小改 3／中改 2）
>
> **v42 快照（2026-11-11·收口总档波·四席并铸＋集成席收口）**: 总报告/演练实录/路线图三档入 docs/（服务层总览 v40 在库续用）·cw_paths v1.x 双件入 ConstructiveWorld·rocqwash v41 `c5df4d4`——三闸收口基准：doc_lint drift=0／破坏面矩阵 17 判全过／总套零红（SKIP 不计红）。
>
> **v57 snapshot (2026-11-13, evolve cycle-2 execution round — draft candidates 1+2+3 executed, integration close)**: translation echelon (candidate 1, norm-baseline-guided top-6 by per-file error mass): six tool faces Englished per the annotation standard card（`tools/wash_shape.py` 25→0 · `wrapper/wash_station.py` 19→0 · `tools/ci_triage.py` 19→0 · `tools/cw_doctor.py` 17→0 · `tools/unclog.py` 16→0 · `tools/doc_lint.py` 15→0 — echelon error mass 111→0; five-field headers prepended, function-level comments and CLI output literals translated, identifiers/flags/schema/exit codes zero-change; zh archives 4 new `docs/zh/`（wash_shape/wash_station/cw_doctor/doc_lint）＋2 updated（ci_triage/unclog carried prior archives）; guard-anchor line sync in `tests/test_destructive_matrix.py`）; registry hygiene execution (candidate 2 residue, Set-repo side — the only worker authorized to write that repository): commit `987a1b5` "registry hygiene cycle-2: reanchor canonical form (541 rows) + orphan registration (3 pieces)" landed on the `hy7pc8gfmf-dotcom/ConstructiveWorld-Set` working main（registry_fix --apply over the fresh audit fix-plan with --anchor-src for the 541 reanchor rows plus registry_regen batch-anchor --apply registering the 3 orphan pieces — verified locally by this integration turn as commit + message; push/CI evidence rides the registry worker's report）; taxonomy supplement (candidate 3, evidence-not-reclassification discipline held): `tools/ci_triage.py` two-shape evidence-note vectors — the Main#3 runner-lost form（failure + zero red steps + build step hanging in_progress + logs-GET 404 BlobNotFound）annotated `runner-lost-candidate` with the family kept UNRECOGNIZED via the new canned fixture `tests/fixtures/ci_triage_runner_lost.json`（review-ledger §二 S3 verbatim transcription）, and the #10 GATE2-ATTEST-RED auth-state form annotated `auth-state-red-maintained`（UNREC maintained, no taxonomy inflation）; `docs/retro-triage-Main仓全史-20261112.md` evidence-note section; `--selftest` rc=0 with both vectors; integration close: norm_lint `--tree` fitness reconciliation against the v2 baseline——error 2377→2267 warn 1098→1092 cjk_ratio 0.214081→0.189684, files 153→154（the cycle-2 draft face enters the scan）: −111 error = the echelon's increment（six tools to zero）, +1 error = ledger vintage drift（the v56 committed `更新账.md` append raced the v2 snapshot — parent-blob 492 vs HEAD 493 verified, zero ledger writes this turn）, warn −21 on the echelon +8 the new draft face +1 the retro doc section +3 ledger vintage +3 the snapshot line's own date-stamp churn（v56 same convention）; v3 baseline landed same-name `docs/norm-lint-baseline-20261113.{json,md}`（v2 recoverable at git HEAD; byte-identical double rerun）; three-gate close: doc_lint consistent／suite green twice（63 cases 62 pass 0 red 1 skip ×2·skip=t_quad8_check）／`bash -n` 12 shell faces pass; selftest spot checks rc=0 ×5（wash_shape/cw_doctor/unclog/doc_lint/ci_triage）＋wash_station via `tests/test_scan_station.py` 9/9.
>
> **v56 snapshot (2026-11-13, annotation-face Englishing round two — nine-tool translation close)**: three workers translated nine tool faces（`scan/dual_scan.py`·`tools/chain_graph.py`·`tools/ledger_sync.py`·`verify/erasure_classifier.py`·`verify/retrofit_gate7_irr.py`·`verify/verify_gate6.py`·`wash/comment_sweep.py`·`wash/cure_applier.py`·`wash/probe_engine.py`）per the annotation standard card（two-part header＋five fields; function-level comments and CLI output literals included this round）——interface boundary zero-change machine-verified（identifier/flag/schema/exit-code AST comparison vs HEAD, nine of nine identical）; jargon word-face census per `docs/jargon-to-standard-mapping-v1.md`: mapping-table findings on the nine tools 35→0（norm_lint authority）, raw occurrences 48→3 with the 3 residue hits all in exempt JSON-schema key positions（`"seat": "W9"` fixture data etc., table §1 identifier exemption）; zh archives: 7 new `docs/zh/` records（4 Chinese module docstrings verbatim-faithful: chain_graph/ledger_sync/verify_gate6/probe_engine · comment_sweep/cure_applier pre-restructuring docstring archives with honest provenance note · retrofit_gate7_irr three-line header comment archive · dual_scan/erasure_classifier carried zero CJK at HEAD, no archive due）; integration close: norm_lint `--tree` fitness reconciliation against the v53 baseline——error 2441→2377 warn 1036→1098, the nine tool faces all cured to zero findings（error −81 warn −20＝the round's fitness increment, fed to evolve cycle-2）, remainder＝13 v54/v55 new faces（error 5 warn 61）＋README/ledger append churn; v2 baseline landed same-name `docs/norm-lint-baseline-20261113.json`（v1 recoverable at git HEAD）; three-gate close: doc_lint consistent（drift=0）／suite green twice（63 cases 62 pass 0 red 1 skip ×2·skip=t_quad8_check）／`bash -n` 13 shell faces pass; selftest spot checks rc=0 ×3（`tools/chain_graph.py`·`verify/verify_gate6.py`·`wash/probe_engine.py`）; `norm_lint --file` ×9 error=0.
>
> **v55 snapshot (2026-11-13, autonomous-evolution engine wave — constitution law-three body)**: engine `tools/evolve.py`（autonomous evolution engine v1, schema `rocqwash-evolve/1` — the harvest→derive→draft pipeline with the autonomous-execution gate kept at human review: harvest five signal classes by subprocess of the existing engines（norm-lint fitness vs the v53 baseline with the frozen surfaces excluded / sentinel one-shot dual-repo new ci-red events with seen-idempotence / suite last state / registry-audit accounts with increment / maintained UNRECOGNIZED sentinel events）→ derive fixed-rule scored candidates（impact × evidence / effort, evidence clamped 10）plus genetic standing candidates from the ledger lineage → draft the constitution three-law-preamble task brief to `--draft-out`; **draft-only spawn gate: never executes a candidate, never writes the repository**; adverse signals are data, exit 0/2/9）— `--selftest` rc=0（ten PASS vector groups）; round-one live cycle（demo record `docs/演示-evolve首轮-20261113.md` — real signals S1 norm account / S2 sentinel dual-repo / S3 registry audit, zero mocks; task-brief draft `docs/evolve-draft-cycle1-20261113.md` — candidates C1–C5, TOP1 = C1 red-triage score 12.0, curable-error reduction rate honestly 0.00%（frozen ledger excluded, error 1960→1960）plus the curable-basis measurement rule registered for the engine spec; companion engine draft `docs/draft-evolve-v55-20261113.md`; ops manual `docs/ops-evolve-手册-v1.0-20261113.md` — variation/selection/inheritance mapped to implemented machinery, draft-only safety invariants）; suite hook-up（`t_evolve` case in `tests/run_tests.sh` · cw.sh routes `evolve`, six-place sync, 28 tools · `doc_lint` `DEFAULT_HELP_CAP` 27→28 on the registered-tool precedent · counts synced to 63 in `tests/README.md`＋`README.md`）——three-gate close: doc_lint consistent（help_run=28/28·drift=0）／suite green twice（63 cases 62 pass 0 red 1 skip ×2·skip=t_quad8_check）／`bash -n` pass（cw.sh＋run_tests.sh）; norm_lint tree re-run against the v53 baseline: 152 files error 2441→2449 warn 1036→1106 — the +8 error delta sits entirely on the frozen ledger's committed v54 append（`更新账.md` byte-identical to HEAD this turn, zero writes）; the two new engine/suite faces（`tools/evolve.py`·`tests/test_evolve.py`）carry 0 error 0 warn, the four new doc faces carry 0 error（warn = CJK residue data per the account-doc convention）.
>
> **v54 snapshot (2026-11-13, contributor-isolation tooling close)**: protocol `docs/contrib-isolation-protocol-v1.0-20261113.md`（contributor-isolation protocol v1.0 — isolation lanes with the Main `y_e1_gamma_nodes/` subdirectory and Set topic-branch precedents, `contrib/<lane>/` lane placement with the `# --- contrib lane rows below ---` separator segment, the four-check intake pipeline audit→norm→gate→merge over the routed registry/norm/union/fix tools, the PR#48 tail-zone regeneration rule, fetch-first/canonical-first two-stream etiquette）; tools `tools/contrib_intake.py`（read-only four-gate intake inspector, schema `rocqwash-contrib-intake/1` — registry union dry run / norm lint / gate expectation / lane isolation over a contribution face vs a base face, gates never short-circuit, BLOCK verdicts are data, exit 0/1/2/9）＋`tools/registry_regen.py`（merge-target books verbatim as the draft bottom + canonical `#R<seq>-<md5-8>` rows tail-appended in dependency order, dry run by default, `--apply` writes only under an explicit `--out`, schema `rocqwash-registry-regen/1`）— both `--selftest` rc=0; verification record `docs/检验-PR48-intake四闸-20261113.md`（the four-check pipeline run for real on Set PR#48: audit findings as data total 564, lane norm target empty, 8/8 witness visibility satisfied with 2 build-unreachable order-row mismatches, merge-check A2 firing as the already-landed guard, landed books byte-equal to the prescribed regeneration shape in both books）; suite hook-up（`t_contrib_intake`/`t_registry_regen` cases in `tests/run_tests.sh` with self-supplemented minimal shells · cw.sh routes `contrib-intake`＋`registry-regen`, six-place sync, 27 tools · `doc_lint` `DEFAULT_HELP_CAP` 26→27 on the registered-tool precedent · counts synced to 62 in `tests/README.md`＋`README.md`）——three-gate close: doc_lint consistent（help_run=27/27·drift=0）／suite green twice（62 cases 61 pass 0 red 1 skip ×2·skip=t_quad8_check）／`bash -n` pass（cw.sh＋run_tests.sh）; norm_lint tree re-run against the v53 baseline: 146 files（+6, every new face error-level 0）error 2441→2446 warn 1036→1056 — the whole delta sits on the frozen ledger `更新账.md`（byte-identical to HEAD md5 `d0059f5d…`, a vintage of the committed baseline, zero writes this turn）; the four new suite/tool faces carry 0 error 0 warn.
>
> **v53 快照（2026-11-13·注释面规范化波·宪法三律〔①国际化/规范化/英文化＋翻译替换·黑话禁令 ②协作隔离 ③自主递归演进〕·四产出铸＋集成席收口）**: 规范双件 `docs/annotation-standard-v1.0-20261113.md`（注释规范卡 v1.0——两段式头注 banner＋五字段 Purpose./Interface./Dependencies./Evidence./Exit-codes. 逐字·禁词面四族·双语过渡规则〔翻译替换为正·原中文入 .zh.md 留档而非删除·代码标识符/CLI 旗标/JSON schema 字段/退出码语义零改动〕·error/warn 分级与检查器 0/1/2/9 口径）＋`docs/jargon-to-standard-mapping-v1.md`（黑话→标准表述对照表 v1＝规范卡 Appendix A·142 活跃词面·语境注记逐行·标识符豁免登记在册）；检查器 `tools/norm_lint.py`（注释面规范化检查 report-only 首形——.py/.sh/.md 散文面五查〔头注形/黑话词面/CJK 残留/禁类/头注行数帽 30〕·schema rocqwash-norm-lint/1·findings 是数据退出码不升级·--selftest 六矢量·*.zh.md 与 docs/zh/ 归档面免扫）＋基线账 `docs/norm-lint-baseline-20261113.{json,md}`（全仓现状如实 files=140·error=2441·warn=1036·cjk_ratio=0.248597·同输入重跑字节恒同）；翻译面四件（入口面 `cw.sh`/`cli/rocqwash`/`README-cw.md` ＋核心四器 `tools/ci_triage.py`/`tools/pushci.py`/`tools/unclog.py`/`tools/cw_sentinel.py` 头注/帮助面英文化——标识符/旗标/schema 字段/退出码语义零改动·原中文入 `README-cw.zh.md`/`cli/rocqwash.zh.md`/`docs/zh/` 四器 docstring 原档共六件留档）；集成席四件（①norm_lint 全仓基线账＝全仓扫描无白名单现状如实出账＋重跑字节恒同验证 ②t_norm_lint 挂接 tests/test_norm_lint.py 最小自测壳三判＋总套两遍绿＋doc_lint consistent＋bash -n 全 sh 过 ③cw.sh norm-lint 路由入册二十五工具六处同步＋README-cw.md 工具表补行＋doc_lint DEFAULT_HELP_CAP 24→25 换代〔norm_lint 入册后 25 器·帽溢出 wash/probe_engine.py 按 v38/v46 同 precedent·--jobs 实在 help 在册·幻引假阳性清偿〕＋doc_lint 归档面免扫〔*.zh.md 与 docs/zh/＝规范卡 §5.2 归档非正本面〕＋入口面叙述类词面清偿约 26 处〔wave/campaign/seat 叙述·日期戳·席名·叙述义 dispatch 改写〕④README v53 快照行＋CHANGELOG v53 补行＋黑话终扫在册＝余量如实登记——标识符引形类〔cw.sh dispatch 路由名×5·README-cw.md 例命令/文档链接文件名日期×6·cli/rocqwash retrofit 子动词名×4〕＋四器行内注释残留〔jargon 2-14·cjk_ratio 0.11-0.19·模块 docstring 已英文化·函数 docstring 与行内注释属递归波消减基线〕）——三闸收口：doc_lint consistent（help_run=25/25·drift=0）／总套两遍绿（60 例 59 过 0 红 1 略×2·略=t_quad8_check）／`bash -n` 全过（cw.sh＋run_tests.sh）。
>
> **v52 快照（2026-11-13·Main 新内容勘形＋R3 复发判例＋哨消费演练·三席铸＋集成席收口）**: 勘形席 `docs/勘形-Main新内容预热-20261113.md`（承前档《勘形-multi-repo-Main仓适配-20261112.md》现势跟进·只读 api 取证 Main tip `d2e74c2b` 三面新内容——① `y_e1_gamma_nodes/` 子目录 92 件双点并存（未注册设计内）②unif limbs 波（`planb4_l3_limbs_discharge.v` 落 Live＋双册注册·三肢清偿）③gate8 permanent vacuity sentinel（9e381d61）·六轮取证书＋`ci_triage` 真发两炉（run#50 family=none 17 步全绿／run#46 `--logs` 两跳 family=B-netred·checkout couldn't find remote ref 直证）→**预热需求 10 条 verdict＝即用 2／小改 4／候令 4**）；判例席 `docs/判例-R3复发-route2tierA自愈-20261113.md`（判例复发实录·**服务层闭环首例**——Set route2-tierA run#301/302（sha `8f59c8f`）R3「相对路径 cwd=workdir 错位·驱动同秒全灭」复发：哨活逮（events.jsonl seq 58·04:38）→`ci_triage` 判类 A-content-red→同事 restore `bd8f38b` 自愈→run#303/304 双绿·首红至复绿 ≈20 分钟全环零人工·附 Set PR#48 八件重叠 blob 8/8 SAME 勘形预热注记）；演练席 `docs/演练-哨事件消费-20261113.md`（消费演练·零新功能纯实跑——哨长驻产账（`_log/sentinel_v48/` JSONL 事件流）消费端三连：`render_events` 台账化（events_total=64·bad_lines=0）＋事件分析（kind/family 分布·活逮清单·UNREC 维持件清点）＋state.json seen 对账与 report.json 轮史续接核验（round1→3 递进·600s 节奏活证）·与哨长驻同窗并行终态 65 事件·任务书给形三处不符如实登记按实取为准）；集成席三件（README v52 快照行／总套钦令两遍绿／docs 清单查勘＝无独立清单件·三件经由本快照行具名登记＝v49-v51 同法·更新账.md 禁触）——三闸收口：doc_lint `--help-cap 24` consistent／总套两遍绿（59 例 58 过 0 红 1 略×2·略=t_quad8_check）／`bash -n` 全过（run_tests.sh）。
>
> **v51 快照（2026-11-12·哨韧性修＋triage 精化＋监督壳部署件波·三席铸＋集成席收口）**: 哨韧性修 `tools/cw_sentinel.py`（v50 round10 IncompleteRead 传输层崩〔更新账.md:3999〕器修两轨——①韧性层传输层瞬断有界重试 `--net-retries` 缺省 3 发退避 5s/15s/45s〔TRANSIENT_TRANSPORT_ERRORS＝IncompleteRead/RemoteDisconnected/BadStatusLine/ConnectionError/socket.timeout·区别于 HTTPError 状态码面〕耗尽 9 fail-loud 保持·非瞬态零吞原样上抛；②loop 层逐源兜底＝异常源本轮 skip＋source-error 事件响亮注记·宁跳轮不崩驻·seen 未记下轮重报宁重复不丢件·once 直通 fail-loud rc 9 语义不动；selftest ⑭⑮ 两矢 canned 注入〔canned IncompleteRead 真崩栈同形 371261/72721·loop 401 双轮 rc0 对照 once 9〕）；triage 精化 `tools/ci_triage.py`（复核台账 token 二分限形落地：E 变体结论位校验——GATE2-ATTEST-RED/判定=CLEAN 真执行 token 在〔dump 行滤除后〕＝认证态红形留 UNRECOGNIZED 不充谱＝run#10 转正验收判〔器判=复核判词·v50 E 假阳性清偿〕·coqchk 步 success 完走形同留 UNREC·banner-absent 形保持 E〔run#7/8/20/26〕；KEY_LOG_PATTERNS 增 GATE2-ATTEST-RED/R4 覆盖划分/appendix 缺 三枚＝五 token 全员在册＋dump 行滤除〔青色脚本回显/组指令行非真执行行〕`--no-dump-filter` 可关＋`--offline` 顶层 job_logs 扩展位 canned 日志注入；`tests/fixtures/ci_triage_gate2_only_{cancelled,failure}.json` 增 canned job_logs 真执行行誊录〔run#7 banner-absent 真行＋2 dump 行／run#10 ATTEST-RED 真行＋1 dump 行＝证据陷阱原形在册〕）；监督壳部署件 `examples/sentinel_supervisor.sh`（哨长驻崩溃自动重启补偿壳正典部署形·重启帽/×2 指数退避/state 续接注记/定时收兵钩位留空/rc 分诊〔0 轮尽自停·2 用法错不进重启环·9 其余退避计帽〕·路径全参数化零硬编码）＋`docs/ops-sentinel-长驻手册-v1.0-20261112.md` §1.6 监督壳部署形＋`examples/README.md` 双语登记；集成席三件（挂载确认＝三席新矢全经既有 t_cw_sentinel/t_ci_triage `--selftest` 在册例直达·run_tests.sh 零新挂载位仅注释登记／README v51 快照行／真发抽验＝哨 `--once` 真网络 rc=0 韧性修后现形）——三闸收口：doc_lint `--help-cap 24` consistent／总套两遍绿（59 例 58 过 0 红 1 略×2）／`bash -n` 全过（监督壳＋run_tests.sh）。
>
> **v50 快照（2026-11-12·UNREC 14 事件判类交叉验证集成波·三席铸＋集成席收口）**: 工装席 triage 修（`tools/ci_triage.py` logs 端点两跳 415 修法〔Accept application/vnd.github+json→302 签名 URL→零 Authorization 第二跳 200·探针实测；415/403/404 原码入证据〕＋gate2-only 连坐形入谱 E 变体〔红步集 ⊆ {gate2+上传族} 且纯 gate2 红步在册·前置 build/coqchk 非 content 红·出处 Main retro #7/#8/#20/#26 banner-absent 连坐四发＋#10 认证态红一发〕＋`tests/fixtures/ci_triage_gate2_only_{cancelled,failure}.json` 真形两件〔retro 台账 run#7/#10 逐字段誊录·selftest〔十〕直挂〕＋`docs/retro-triage-Main仓全史-20261112.md` §八增补）；复核席 `docs/复核-UNREC-14事件-20261112.md`（哨 8＋retro 6＝14 件逐件人工判类独立 ground truth·判词分布（14 行）A×1/B×1/E×8/UNREC 维持×4·gate2-only 步名形二相性：GATE-BANNER-ABSENT 连坐×4 run→E／GATE2-ATTEST-RED 认证态×1 run（Main#10·parser CLEAN 公理=0·R4 划分破）→UNREC 人工指认）；验证席 `docs/验证-Main档案位实用化-20261112.md`（Main 档案位三步全过：fetch 直连 rc=0＋tip 三面对齐 `2f793c4`＋registry_audit 五账出账＋pushci --dry-run 真仓两跑幂等字节恒同零副作用）；集成席交叉验证（修后器面 `--repo/--run --logs` 线上重判 8 distinct run／14 台账行：**一致率 run 级 5/8·行级 10/14**·分歧 3 run 4 行逐件在册不强行收敛——S1 Set#284 run 级谱外置顶遮蔽 mac 主红〔job 级器面=A 与复核一致〕·S2 Set#286 判类序 E>B 取先遮蔽 mac 主红〔job 级器面=B 一致〕·S6/R4 Main#10 E 变体假阳性＝GATE2-ATTEST-RED 认证态红形被步名子集规则吞＋GATE-BANNER-ABSENT 青色 dump 行假确证〔真执行行=判定=CLEAN 公理总数=0〕＝复核台账 §三-2 陷阱面器面复现——分歧即判类谱下一候选：scan 层 dump 行滤除／GATE2-ATTEST-RED 等五 token 入册／认证态红形留 UNREC 禁充谱）——三闸收口：doc_lint `--help-cap 24` consistent／总套两遍绿／`bash -n` 全过。
>
> **v49 快照（2026-11-12·Main 仓适配小改＋实测收口波·四席并铸＋集成席收口）**: fixtures 席 Main 形两件入 tests/（`tests/fixtures/ci_triage_main_coq93.json`＝Main CI 9.3 coq93.yml 真形 16 步 canned＋`tests/fixtures/pushci_scenarios/s7_main_dry_run.json`＝branch main 直推路线 dry-run）·消费面＝`tools/ci_triage.py --selftest`〔九〕Main 形判读矢（兼容表 15 行机检＋E 两件齐）＋`tests/test_pushci.py` 七场景壳（t_ci_triage/t_pushci 既有例已挂登记·run_tests.sh 零改动）；retro 台账 `docs/retro-triage-Main仓全史-20261112.md`（Main 全史 369 runs 实取·现役 coq93 31 条逐判＋coq#340 桥件·红炉并集 19 事件·与哨对账 30/30 零分歧）；K3b 复采样 `examples/baselines/audit-k3b-20261112.json`（probe_chain_s=190.719·perf-profile 律 1 噪声带首采 [165.202, 190.719]·K=3 无收益两发稳健结论）；总报告 v2.0 `docs/rocqwash-service-campaign-total-v2.0-20261112.md`（v1.0 基座全保留＋v43-v48 六波增补章）——三闸收口：doc_lint `--help-cap 24` consistent／破坏面矩阵 17 判全过／总套 59 例 58 过 0 红 1 略（t_quad8_check 四仓副本群正本缺卷·SKIP 不计红）。

## Architecture: Three Chains in One

```
Toolchain (scripts + templates + canonical recipes)
    ↓
Logic Chain (criteria + gates + calibration standards)
    ↓
Derivation Chain (input → wash → verify → land → certify → push)
```

## Components

| Module | Purpose | LLM Surpass |
|--------|---------|-------------|
| `scan/` | Prop leakage scanner (5 frozen lanes + 3 negative-capture lanes) | Exact to line; LLM cannot guarantee exhaustive |
| `names/` | Statement-name ordinal list extractor + N=N assertion | LLM cannot guarantee ordinal counting |
| `wash/` | Canonical 7-step wash engine (exact-string + count==1 + idempotent) | LLM-generated tactics not idempotently replayable |
| `verify/` | R4 three-source (bare magic=0 + probe dual-face + five-pattern grep) | LLM cannot enumerate full closure |
| `seam/` | Generation-gap seam probe (W13 four-mechanism auto-classification) | Mechanical supply-signature Check vs LLM guess |
| `certify/` | Two-tier freeze system + push-window four-criteria + UNION v2 | LLM cannot replace deterministic process |
| `watch/` | CI monitoring + pin-IP push + thermal guard | Deterministic workflow vs LLM instability |
| `tools/` | cpu_guard.sh thermal wrapper + shared utilities | Hardware-aware process control |
| `wrapper/` | Adapter layers for frozen / out-of-repo pieces: `coqc_shim.sh` + `gate7_probe.sh` (gate7 probe chain → local `rocq c`, guard-wrapped launcher) + `guard.sh` + `scan_station.py` | Canonical argv/env adaptation; criteria stay solely with the original tools |
| `scan/scan_v4_token.py` | Token-level qualified-identifier census (bare vs dotted constructor references, binder-aware) — closes the mixed-line masking blind spot of line-level filters | Token census is exhaustive at token granularity; line-level `grep -v` drops lines that carry both forms |
| `wash/cure_pack.json` + `wash/cure_applier.py` | Consumer-cure canonical pack: twenty-four deterministic idempotent rewrite patterns — the legacy five (bridge-wrapped rewrite, goal-opening downshift, opaque-reflexivity cure, qualified successor form, NatLe supply bridge), nine v1.1 statement-face patterns from the 20261103 wash-campaign field report (Qle/Qlt carrier-face downshifts in token and %-scoped notation forms, refl bridge opener, Import-shadow direct-face qualification as two exclusive variants with fail-loud conflict detection, NatLe premise lift + intros-tail-guarded drop wrap), five v1.2 S07-lineage adaptation patterns from the W66 field report (parameterized-shell drop with a :=-binding-right guard, notation rebind line-insertion, @field projection-bridge bare form, predicate-face convergence token map whose targets must be the consuming supply lemma's conclusion constant names, and a report-only binder-shell station for the manual binder surgery), and five v1.3 patterns for the CI #178 extraction-defect families (E3 generic-interface instantiation: abstract-carrier application stations rewritten to a concrete-carrier specialization shim generated after the last import; E2 record polymorphic field: the un-annotated field-consumption Definition restated as an explicit-type-annotated middleware with downstream arity adaptation and a report-only sweep-completion station), applied by a face/proof-scoped regex engine with per-face token guards plus a line-insert and a station-report engine | Exact trigger + template + second-run-zero-change assertion; LLM-generated rewrites are not idempotently replayable |
| `scan/dual_scan.py` | Dual-scanner cross-check driver: runs scan_v4_token + mac_stmt_scan over the same candidate files and reports per-file station counts plus a diff (only_v4 / only_stmt / common) — turns shared scanner blindness (application/type-face red causes) into a mechanical fact per file instead of a silent assumption | Both scanners' exit codes and station line-sets are mechanical; scanner consensus is reported, never blessed as completeness |
| `verify/erasure_classifier.py` | Extraction-erasure station classifier: six clusters with disposition suggestions, CAPTURE cross-check, markdown adjudication ledger | Deterministic pattern rules over extraction artifacts; advisory output for human adjudication, never a verdict |
| `wash/probe_engine.py` | Batch closure-compatibility probe engine: candidates TSV × world dir → per-file `rocq c` under cpu_guard → rc triage (WASHABLE / BORN-CLEAN / red-cause classes incl. MISSING_LIB) → idempotent ledger JSON | Real exit codes + red-cause regex classification are mechanical; LLM guesses at closure compatibility |
| `tools/chain_graph.py` | Multi-ledger merger → missing-lib chain-root graph (dependents count + root self-washability) → TOP ranking markdown + JSON | Union/override merge and dependents counting are deterministic; LLM loses track across ledgers |
| `wash/comment_pack.json` + `wash/comment_sweep.py` | Comment-domain sweep sidecar (does not impersonate a statement-face pattern): nested-comment-and-string-aware state machine, comment-domain flag-word exchange (review-bias word → neutral English term), data-driven leading-header replacement with a five-field shape spec; every application mechanically asserts the code-line-equality projection (comment-strip per the w7 criterion) and second-run zero-change | Comment-domain-only edits are provable by the code-strip projection; LLM edits leak into code silently |
| `tools/ledger_sync.py` | Probe-ledger × status-ledger TSV sync: E1 dedup / E3 ghost / MD5-drift / NO-MD5 / generation-divergence findings (v2.1: recognizes the freeze-ledger `items` subkey shell and filters bare-dict metadata keys loudly; divergence-carrying records are surfaced per-entry with an idempotent row note, never silently dropped) / loud column validation → new TSV, idempotent | Fail-loud bookkeeping with deterministic row upgrades; LLM silently drops or duplicates rows |
| `tools/pushci.py` | Push-CI one-shot pipeline orchestrator: five stages — preflight emission gate (dyld doctor verdict + net-probe stable window + optional gate4 comment pre-scan; the no-emission-on-single-probe discipline is codified here), push (retry ×3 + ghproxy re-route for https://github.com/ remotes; pushed_sha = ls-remote remote tip), CI watch (status-only polling — a frozen updated_at is not a zombie verdict), heal (ci_triage family dispatch: NETRED/coqchk-skipped → stable-window → rerun, capped; content-red is never auto-fixed; off-table families are never auto-rerun), verdict ± PR merge — seven-state verdict (`success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|dry-run`), exit codes 0/1/2/9; orchestrates the v35 four tools via subprocess, zero new engines; fully offline-injectable (`--injector`/`--git-caller`/`--sleep-scale`) | Deterministic state machine over mechanical gates; LLM cannot be trusted to decide emission windows or auto-heal policies |

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
├── tools/                # cpu_guard.sh 温控包裹 + 战役工装 — thermal guard + campaign tools
├── wrapper/              # 适配层族（gate7 探针链 shim/启动器＋cpu_guard 直通＋scan 指认包装）— adapter layers (gate7 shim/probe, guard pass-through, scan station)
├── wash/                 # wash_engine.py 通用逐件洗引擎 + probe_engine.py 批量闭包探针 + 治愈包/战役批洗 — generic wash engine + batch probe engine + cure pack + campaign tools
├── verify/               # verify_vo.py 绿判四件套 + 战役验证工装 — four-pack green verdict + campaign verify tools
├── seam/                 # seam_probe.py W13 四机制指纹探针 — W13 four-mechanism fingerprint probe
├── certify/              # freeze_manifest.py 两层冻结 + push_gate.py 推窗四判据/UNION v2 + frozen8.py 八件冻结名单 — two-tier freeze + push-window gate + UNION v2 + frozen-eight registry
├── watch/                # watch.py CI 监控/钉 IP 推送/ls-remote 确证 — CI monitoring / pin-IP push / ls-remote confirm
├── tests/  workflows/    # 自测套件（70 例）/ CI 工作流占位 — test suite (70 cases) / CI placeholder
└── README.md  LICENSE  .gitignore
```

> 状态快照 2026-11-01（巡检打磨席 rqsup4）：`scan/`、`names/`、`tools/cpu_guard.sh`、
> `cli/`、`examples/`、`docs/`、`tests/`（34 例自测套件）已实现并实测；`wash/`
> （`wash_engine.py` 台账洗引擎＋`_abl1_wash.py` 战役件＋`world_hook.py` 世界基校验钩子·
> 五课①）、`verify/`（`verify_vo.py` 绿判四件套＋战役工装＋`verify_gate6.py` gate6 薄包装·
> 五课③）、`seam/`（`seam_probe.py` W13 四机制指纹探针）、`certify/`（`freeze_manifest.py`
> 两层冻结清单＋`push_gate.py` 推窗四判据/UNION v2 深件·席 rqwash2＋`frozen8.py`
> 八件冻结名单机检）、`watch/`
> （`watch.py` CI 监控/钉 IP 推送/ls-remote 确证·零 dispatch 结构保证）、`tools/`
> （`select_audit.py` 选件审计器·五课②）、`recipes/`（`S07_projection_reanchor_E5.md`
> 五课④＋`ENBIG7_same_domain_collision_PW1.md` 五课③·判例处方件双件）、`wrapper/`
> （适配层族：gate7 探针链 `coqc_shim.sh`＋`gate7_probe.sh`·cpu_guard 直通
> `guard.sh`·scan 指认包装 `scan_station.py`·席 rqadapt·三判例验收站
> `precedent_station.py`·五课⑤ rqsup4）已落地；
> `verify/` 统一入口已收口（显式子动词分派 `cli/rocqwash verify gate4|verify_vo|verify_gate6|retrofit`·
> rqadapt 落三子动词 2026-10-31·rqsup4 四巡补 verify_gate6 20261101）；`certify/`
> 同款显式分派 `cli/rocqwash certify freeze|push_gate|frozen8`（rqsup4 五巡补
> frozen8 20261101）——冻结件零改动；R4 提取侧三源为待办。
> v30 增补（20261103·探测战役工具化轮）：`wash/probe_engine.py` 批量闭包相容
> 探针引擎＋`tools/chain_graph.py` 多账合并链根图＋`tools/ledger_sync.py`
> probe×状态台账同步器（E1 去重/E3 幽灵/列校验 fail-loud）——承 W13/W25/台账
> v2 三原型 1:1 泛化，全路径参数化零硬编码；自测套件扩至 40 例全绿。
> v31 增补（20261103·洗形战役实战判例工具化轮）：`wash/cure_pack.json` v1.1
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
> 站型——手刀辖区报站·术后站数归零）＋`scan/dual_scan.py` 双器对拍驱动
> （scan_v4＋mac_stmt_scan 双扫×逐件差异报告 only_v4/only_stmt）＋cure_applier
> 器修（exclusive-group 冲突＋--json 路径 report 落盘·rc=4 文档值）；
> 自测套件扩至 42 例全绿（门控 S07 编译弧：红→机械 cure→binder 手术→绿→
> 提取 Obj.magic 0/0）。
> v34 增补（20261104·CI #178 提取面缺陷族逆向修订轮）：`wash/cure_pack.json`
> v1.2→v1.3 十九式→二十四式——工单定谳两类缺陷族入 cure：E3 泛型接口实例化
> （cure34_E3_use_station_spec 抽象载体应用站改写特化 shim 调用＋cure34_E3_spec_shim
> line-insert 末个 Import 后生成具体载体中间 Definition；shim 体保留被特化的抽象
> 应用、face_exclude 护体防二遍自缠）＋E2 记录多态字段（cure34_E2_field_annot
> 无标注消费面重述为显式类型标注中间 Definition＋cure34_E2_use_arity 下游元数
> 站随行＋cure34_E2_station_unannot report-only 清账站）——五式全复用 v32 引擎
> 零新引擎；门控 E2/E3 编译弧第一手：pre-fix 编译绿（提取时缺陷族）、修后绿、
> E2 消费面 `'a1 -> 'a1`→`nat -> nat`、消费单元 magic 0/0、world 访问器债=1
> 机械钉（实体修复工作流域·canonical_note 记界）。自测套件 43 例。
> v36 增补（20261111·推送 CI 一键流水线轮）：`tools/pushci.py` 修复后推送 CI
> 一键流水线编排器——五段管线：preflight 发射闸（dyld doctor verdict＋net-probe
> 稳窗双闸·可选 gate4 头注预扫·禁发射律代码化）→push（重试 3 发×45s＋
> https://github.com/ 形 ghproxy 换路·pushed_sha=ls-remote 远端 tip）→watch
> （status-only 口径轮询·updated_at 冻结非僵尸判据）→heal（ci_triage family
> 分派：B/E 族→稳窗过→rerun·帽 --max-heal 3·A 内容红禁代修·C toolchain 停·
> 表外族禁自动 rerun 人工指认）→verdict±merge（七态 success/fix-content/
> toolchain/unstable/heal-exhausted/gate4-block/dry-run·退出码 0/1/2/9）——
> v35 四器（doctor/net-probe/triage/union）subprocess 编排零新引擎；离线可测
> 注入内建（--injector/--git-caller/--sleep-scale·零真网络零真 push）；自测
> 套件扩至 48 例。
> v37 增补（20261111·实时动态三器轮·用户令：配合工作流实时动态提供清洗、洗形、
> 排障、疏通堵塞）：`tools/cw_sentinel.py` 实时动态哨（三路信号源 CI runs/台账
> 链根/buildlog 词面→JSONL 事件流·once/loop 双模·判类全权在 ci_triage·链根
> 全权在 chain_graph·零动作是缺省）＋`tools/wash_shape.py` 洗形器·正典形五洗
> 流水（词面/token/头注/行尾/锚五洗全 subprocess 编排既有引擎·plan 缺省零写盘·
> --apply 落刀后复跑五洗复核）＋`tools/unclog.py` 疏通堵塞闭环引擎（probe 归集
> →chain_graph 挑根→cure_applier 落刀→rescan/resprobe 复核→verdict
> unclogged/wall/rounds-exhausted·缺省干跑·frozen 在册红拒·诚实墙禁硬凑）——
> 三器共同接口纪律五条：JSON-in/JSON-out（--json report·schema 钦名
> rocqwash-sentinel/1·rocqwash-shape/1·rocqwash-unclog/1·sort_keys 字节恒同）·
> 退出码 0/1/2/9（红是数据非器红·响亮 stdout）·--once/--loop 双模（--interval
> 可调·JSONL 事件流 --events）·离线可测（--injector 子进程调用层罐装＋
> --sleep-scale·零真网络零真编译于 selftest）·编排而非重造（零新引擎）；
> `cw.sh` 入口扩至十五工具（sentinel/wash-shape/unclog 三路由·四处同步）·
> 工作流配合接口速查见 [README-cw.md](README-cw.md)「工作流配合接口」节；
> 自测套件扩至 51 例（47 过/4 例正本缺卷让席·真本机全跑）。
> v38 增补（20261111·工作流集成与综合体检轮·四席并铸＋集成席收口）：
> `tools/cw_doctor.py` 综合体检器·四域聚合（①环境＝toolchain_dyld_doctor 编排
> ②网络＝net_probe --rounds 1 ③注册册锚正典形审计 ④堵账＝probe_engine 真探
> ＋chain_graph 链根——逐域 subprocess 编排既有一器零新引擎→综合健康分 0-100
> ＋per-domain verdict＋advice 处置清单·schema rocqwash-cwdoctor/1·--injector
> 离线可测·只诊断禁代执行·红是数据非器红 healthy=0/degraded=1）；工作流集成
> 面：`examples/workflows/` 三嵌段正典样例（backend-sentinel 后台哨／step-pushci
> 单步推 CI／loop-unclog 堵账疏通·全部离线可注入形）＋
> `docs/workflow-integration-whitepaper-v1.0-20261111.md` 集成白皮书（主会话
> 让路模式／后台任务拓扑／推窗四判据×发射闸双门并立）；韧性层：共享退避纯函数
> `tools/_http_backoff.py`（CI GET 403/429/5xx 指数退避·Retry-After 尊重·
> ci_triage/cw_sentinel/pushci 三器接入）＋net_probe `--jitter/--seed` 抖散
> ＋pushci `--timeout`／sentinel `--subproc-timeout` 子进程防挂（injector
> canned 路径一律零重试零真网络）；接口扩面：sentinel `--on-red-preset`
> （unclog 干跑/pushci dry-run 预设动作·与 --on-red 互斥）＋unclog `--audit`
> 只读堵账基线（--src 全文件 md5 跑前跑后自证零写盘·verdict=audit exit 0）；
> `cw.sh` 入口扩至十六工具（cw-doctor 路由·四处同步）；自测套件扩至 52 例
> （t_cw_doctor 最小自测壳两判·缺壳集成席自补）。
> v39 增补（20261111·文档核与接驳实战轮·工装席四铸＋集成席收口）：
> `tools/doc_lint.py` 文档←→实现一致性三查器（①工具表查＝cw.sh 头注/usage/
> hint/case 四处互检＋tools/ 通用入口对账 ②计数查＝tests/run_tests.sh CASES
> vs tests/README.md vs README.md 三处对账 ③旗标查＝docs 引用旗标 vs 各器
> --help 实出逐枚对照（--help 真跑·帽 20 器）——schema rocqwash-doclint/1·
> verdict consistent|drift·红是数据非器红·--selftest tmp 迷你仓六矢量·
> 零网络零写盘）；接驳实战核：`tests/test_relay_e2e.py` cw_sentinel
> --on-red-preset unclog 全链三判 e2e（事件触发→--audit 干跑 rc=0 零写盘
> md5 自证→JSONL 同盘 unclog report 路径逐字节对拍·全 canned 罐装·实跑原文
> 落 docs/ops-realtime-service-v1.0-20261111.md 实时动态服务运行手册）；
> 洗形器扩容：wash_shape `--header-map-preset NAME` 钦名头注模板库
> `tests/fixtures/header_map_v1.json`（战役正典蒸馏·金标引据在册·schema
> rocqwash-header-map/1·与 --header-map 同槽互斥）＋cure_pack v1.4 语料普查
> 轮单式扩容：`cure39_ifq_connective_qualify` 接口量化连接词限定（20261111
> 证据门控普查·b48-52 wash-wave 引据 commit 9a51c74·RI0 语境件语句面裸
> lt/le/plus 钉 @S01_BaseRing 投影形·树正典形；普查纪律 held——引据较薄之形
> 全数留 pending 不铸·夹具 cure39_t13/cure39_plain）。`cw.sh` 入口扩至十七工具
> （doc-lint 路由·四处同步）；自测套件扩至 54 例（t_relay_e2e 三判 e2e＋
> t_doclint 最小自测壳三判·缺壳集成席自补）。
> v40 增补（20261111·正典化巩固波·四席并铸＋集成席收口）：`tools/baseline_diff.py`
> 堵账基线对比器（两份 unclog --audit 堵账基线 argv 序=旧→新→new_blocks/
> resolved_blocks/persistent 三清单＋score_delta·verdict improved/degraded/
> stable/incomparable·账面自洽预检拒手编基线·候选面四元组两账比对跨集如实拒判·
> timing 段不入对比＝基线唯一非确定段——schema rocqwash-baseline-diff/1·红是
> 数据非器红）＋`examples/baselines/` 堵账基线入仓规程（命名律
> audit-<域>-<yyyymmdd>.json·真树干跑产·timing 注记·工装席铸）；破坏面复核矩阵
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
> v41 增补（20261111·四席并铸＋集成席收口）：cw_sentinel 预设表数据化扩至
> 五预设（unclog/pushci/wash-shape/triage/cw-doctor·各承缺省干跑铁律）＋
> `--on-red-preset` 可重复链式（按给定序逐件执行·一败续行不改哨退出码）＋
> on-red 双路同守卫（plain `--on-red` 与 preset 缺 `--emit` 皆 rc=2·破坏面
> 矩阵 S2 判据转正·矩阵仍 17 行）；probe_engine `--jobs` K 并行分片（缺省
> 1 逐件串行零漂移·典序收账输出序不随完成序漂移·候选重名 fail-loud rc=2）；
> unclog `--probe-parallel` 探针并行度透传（audit timing 段 jobs 维度入账·
> 同候选面异 K 前后跑可比）；性能剖面规程 docs/perf-profile-v1.0-20261111.md
> ＋examples/baselines/perf-README.md（K=1/2/3 三跑采集·两轴分离律·工装席
> 铸）；push_gate 推窗四判据×pushci preflight 发射闸双门归一评估
> docs/push-gate-dual-door-assessment-v1.0-20261111.md（只评估零代码变更·
> 护栏席铸）。自测套件保持 56 例（52 过/4 例正本缺卷让席）。
> v46 增补（20261112·红事件路由与注册册卫生审计集成轮·三席铸＋集成席收口）：
> `tools/red_dispatch.py` 红事件路由器（哨红事件→动作预设路由·三档 preset
> report-only/suggest/auto·**缺省零执行**·suggest 出可复制命令块·auto 显式
> 才代跑 60s 帽 rc≠0 响亮入账不改退出码·防重 state＋cooldown·五路由全挂
> 既有 cw.sh 路由零新引擎：B/E 族→pushci 重派·A 族内容红禁代修出 fix 清单·
> C 族→doctor·blocking→unclog·build-signal→wash-shape·schema
> rocqwash-red-dispatch/1·铸席铸）＋`tools/registry_audit.py` 注册册卫生
> 审计器（order.txt/_CoqProject 双册**只读**四账出账：重复行/锚撞文本/顺序
> 号形/形怪/缺锚/孤儿/live 拓扑引用＋`--fix-plan` 确定性处方零写盘·
> **`--apply` 不存在**留执行器·键式/锚正典直用 registry_union 零重造·病灶
> 是数据恒 exit 0·schema rocqwash-registry-audit/1·铸席铸·真仓活跑前置
> 注记承 v40 基线规程律 examples/baselines/README.md「真树活跑归主会话·席面
> 只证器级」）＋`docs/评估-push_gate推窗四判据与pushci归一-20261111.md`
> 推窗四判据×pushci 归一可行性评估（只评估零代码变更·评估席铸·与 v41
> 护栏席同题独立成文两判互证·裁决同为保持双门并立）；`cw.sh` 入口扩至
> 二十三工具（dispatch/audit 两路由·四处同步·评估文档为文档无路由）；
> 自测套件扩至 58 例（t_red_dispatch/t_registry_audit 两例最小自测壳·
> 缺壳集成席自补）。
> v47 增补（20261112·门控编译弧翻绿与注册册处方执行器轮·三席铸＋集成席收口）：
> 门控编译弧总开关翻绿（路线图候选④·任务书编号 ⑧A 案·两路径取 A＝指 9.3
> 多路器 `mac93_install_work/opam93/rocq93/bin/rocq`·v43 第三发 27/27 同源
> 实证）——`tests/run_tests.sh` 总开关缺省探测四路径（env 已设则尊·外部 clone
> 显式指认不受扰）：`ROCWASH_ROCQ`→t_cure_pack 编译 check 段＋t_probe_engine
> 真 rocq 节；`GATE7_PROBE_SCRIPT`/`GATE6_SCRIPT`→Set 仓 gate7/gate6 正本在卷
> 指认解锁 t_gate7_wrapper/t_verify_gate6；`BORN_WORLD_ROCQ`→CW Live rocq 缺卷
> 9.3 代役解锁 t_gate6_born_wrapper——诸闸位判据语义零改动（在即跑·缺才 SKIP·
> env 缺且缺卷仍 SKIP）只翻缺省面；t_quad8_check 系四仓副本群缺卷族（另族）
> 不在本案；翻绿是「现役世界代际」绿·非 9.1 复绿（诚实记界承 v43 9.3 门控弧
> 27/27 同口径）。＋`tools/registry_fix.py` 注册册处方执行器（registry_audit
> `--fix-plan` 处方逐条落刀·三类处方 DEDUP 保首/锚刷/ORPHAN-ADD skip·**缺省
> 干跑**·`--apply` 落刀后断言三判炸即回滚·staging 全内存零写盘·schema
> `rocqwash-registry-fix/1`·真树 `--apply` 候令不入本波）；＋哨真仓首战
> （`tools/cw_sentinel.py --loop` 真实战役窗口挂哨·JSONL 事件流 events=33·
> v46 红事件路由消费面实战）；`cw.sh` 入口扩至二十四工具（registry-fix 路由·
> 四处同步）；自测套件扩至 59 例（t_registry_fix 直挂器 --selftest 八矢量·
> 集成席直挂）。
> v48 增补（20261112·DS4 三账收口＋哨长驻运维手册＋Main 仓勘形轮·三席铸＋集成席收口）：
> 路线图① DS4 K=3 账 `examples/baselines/audit-k3-20261112.json` 真树堵账基线落仓
> （27 件 RC0 red=0·timing jobs=3·probe_chain_s=165.202/total_s=169.684）——与 K=1/K=2
> 同候选面经 baseline_diff 双向 verdict=stable 三账齐（190.728/101.916/165.202·
> 加速比 1.87× 于 K=2 档位现拐点·K=3 负边际加速如实录·perf-profile §五三行占位
> 主会话已回填实数）；
> 路线图② `docs/ops-sentinel-长驻手册-v1.0-20261112.md` 哨长驻运维手册成档
> （部署落位规范／事件流消费与 render_events/red_dispatch 接驳／轮转与恢复纪律／
> v44-v48 实证账引用——零码改零新器零新旗标）；
> 路线图⑦ `docs/勘形-multi-repo-Main仓适配-20261112.md` Main 仓 CI 形制勘察档
> （只读零动码·api.github.com 实取现役 coq93.yml 形·适配分级 verdict＝
> 即用 4／小改 3／中改 2——pushci PR 路线 mirror-blind 咬合失配为最大缺口·
> 跨仓越权写盘红线保持）。
> 组件级细节见 [docs/zh/architecture.md](docs/zh/architecture.md) /
> [docs/en/architecture.md](docs/en/architecture.md)；贡献流程见
> [CONTRIBUTING.md](CONTRIBUTING.md)。

## Getting Started (5 minutes)

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
# [gate4ext] ... 件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  UNREADABLE=0 ...
```

Token-level successor-qualification census (finds bare constructor references
that line-level filters miss):

```bash
python3 scan/scan_v4_token.py --file path/to/file.v --json census.json
```

## Platform Support

| Platform | Support | Notes |
|---|---|---|
| macOS | full | `tools/cpu_guard.sh` thermal gate uses `pmset` (macOS-only); queue/nice lanes are POSIX |
| Windows | Git Bash + python3 | light-load direct runs; bring your own thermal policy if needed (`cpu_guard.sh` thermal reading degrades gracefully without `pmset`) |
| Linux | same path as Windows | unverified by this project's CI — reported as-is, no claims |

## Quick Start

```bash
# Scan a .v file for Prop leakage — via the unified CLI entry
cli/rocqwash scan --file my_proof.v

# Extract statement names and assert N=N against baseline
cli/rocqwash names my_proof.v --names-out names.txt
cli/rocqwash names my_proof.v --compare my_proof_washed.v --expect 487

# Wash with an explicit exact-string ledger (idempotent, fail-loud, no guessing)
cli/rocqwash wash my_proof.v --patch wash_ledger.json --out my_proof_washed.v

# Green-verdict four-pack on a compiled pair (magic / freshness / exit / log)
cli/rocqwash verify verify_vo --v my_proof.v --vo my_proof.vo --rc 0 --log build.log

# W13 four-mechanism seam fingerprints (candidate list + prescriptions)
cli/rocqwash seam --file my_proof.v

# Two-tier freeze manifest (tier1 per-file md5 + tier2 manifest md5)
cli/rocqwash certify freeze freeze . --out manifest.json
cli/rocqwash certify freeze check . --manifest manifest.json

# Push-window four-criteria gate (judges the window, never pushes)
cli/rocqwash certify push_gate window --repo . --runs-json runs.json --suite tests/run_tests.sh

# UNION v2 multi-world manifest (per-world tier1/tier2 + union tier)
cli/rocqwash certify push_gate union-freeze --world wa=./world_a --world wb=./world_b --out union.json
cli/rocqwash certify push_gate union-check --manifest union.json

# CI in-flight monitoring (offline evidence mode; online read-only query also available)
python3 watch/watch.py ci --runs-json runs.json

# Pin-IP push wrapper (dry-run by default; masked output; --yes actually pushes)
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
```

## Seven Canonical Steps (不可跳)

1. **cp source into sandbox** (write-isolation)
2. **Three-state triage** (true-wash / bridge-retain=exception-registry / UNCERTAIN=probe-first)
3. **Canonical face-mapping wash** (Qlt→QltT / Qle→QleT' / ==→QeqT / bare=→Id+id_cong / nat≤→NatLe)
4. **Compile verification** (RC=0 / magic 436f712100015ff4 / vo newer than v / PA Closed / coqchk Axioms:none)
5. **R4 three-source conjunction** (bare full-extraction magic=0 + probe dual-face magic=0 + five-pattern grep=0)
6. **gate7 English化 retrofit** (CJK→0 + five-field header 30-line cap)
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
