# tests/ — rocqwash 自测套件

## 运行

```bash
bash tests/run_tests.sh          # 全绿 EXIT 0；任一红 EXIT 1；幂等可重复
```

套件自检（验证「任一红 EXIT 1」契约，注入一恒红例）：

```bash
ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 预期 70 过 / 1 红 / EXIT 1
```

## 覆盖面（70 例）——现役数以 tests/run_tests.sh CASES 名册为准（加测后同步）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 1 | `t_scan_selftest` | `scan/mac_stmt_scan.py --selftest` | E364 冻结向量组全过，exit 0 |
| 2 | `t_names_expect_pos` | `names/mac_stmt_names.py --expect` | fixture census 口径 7=7，exit 0 |
| 3 | `t_names_expect_let` | 同上 `--include-let` | 会师口径 8=8，exit 0 |
| 4 | `t_names_expect_neg` | 同上（负判） | 6≠7 → exit 2（CONTRIBUTING §4 口径） |
| 5 | `t_gate4_clean` | `verify/gate4_comment_guard.py --file` | 净样例五字段齐 → PASS，exit 0 |
| 6 | `t_gate4_dirty` | 同上（负判） | 脏样例禁词/缺字段齐发 → FAIL，exit 1 |
| 7 | `t_retrofit_dryrun` | `verify/retrofit_gate7_irr.py` | 干跑（写请求全截获·零落盘）过其全部内建断言 |
| 8 | `t_wash_judgments` | `wash/_abl1_wash.py` | exact-string+count 正判/幂等重放/破坏反判三判 |
| 9 | `t_wash_engine` | `wash/wash_engine.py`（通用逐件引擎） | `tests/test_wash_engine.py` 六判：pos（APPLY·count 断言·嵌套注释保留）／幂等（applied=0 skipped=N·逐字节恒等）／neg（FAIL·NOT-WRITTEN）／括号反判 2／写隔离 2／CLI 契约 3·3·2·9·9 |
| 10 | `t_verify_vo` | `verify/verify_vo.py --selftest` | 绿判四件套九判：魔数正负/陈vo负/log双判/exit双判/互斥/缺件 |
| 11 | `t_seam_probe` | `seam/seam_probe.py --selftest` | W13 四机制各一正例＋注释掩蔽/前奏册负例 |
| 12 | `t_freeze_manifest` | `certify/freeze_manifest.py --selftest` | freeze 幂等/零漂移/三漂移（changed/added/removed 各1·exit 1）/tier2 篡改必现形 |
| 13 | `t_push_gate` | `certify/push_gate.py --selftest` | UNION v2 六判（幂等/零漂移/漂移/tier1 篡改/union 层篡改/侧册篡改）＋window 四判（c1 双源 PASS/c1 零证据与封顶窗未到 NOT-RUN/c2 behind=1 CLOSED/c4 红套件 CLOSED·本地 path 远端·零网络） |
| 14 | `t_watch` | `watch/watch.py --selftest` | ci 离线四判（idle 0/在飞 1/未知状态保守计在飞/畸形 1/缺件 9）＋rewrite_host·遮蔽单元＋push 干跑四判（改写 URL/extraheader 入账·url-host 不符 2·缺对 2·原样出账）＋env 遮蔽＋confirm 三判（双读全等 0/不一致 1/单读拒 2·真 ls-remote 本地 path 远端） |
| 15 | `t_cpu_guard_direct_smoke` | `tools/cpu_guard.sh -Direct` | 探针一发即退 + `DIRECT bypass` 横幅 |
| 16 | `t_cpu_guard_direct_rc` | 同上 | 探针退出码传播（rc=7） |
| 17 | `t_scan_station` | `wrapper/scan_station.py` | `tests/test_scan_station.py` 九判（裸调指认卡/断言正负/嵌记/透传 rc=9/正本缺失 9/站自检/文件面透传） |
| 18 | `t_gate7_wrapper` | `wrapper/gate7_probe.sh` ＋ `wrapper/coqc_shim.sh` | `tests/test_gate7_wrapper.py` 十三判（双 bash -n/shim argv `c` 注入＋逐字透传/shim 缺 rocq 9/probe 用法 2×3/缺件 9×4/`--dry-run` guard 档位与形装账＋order 装配·零编译零写盘） |
| 19 | `t_verify_born` | `wrapper/verify_born.py` | `tests/test_verify_born.py` 九判（裸调哑成功禁律 2/--help/站自检九判/正本指认 pin/裸形 born.rc 原件直喂正判/前缀形 BORN_RC=0 归一化正判/BORN_RC=1 负判透传 1/--json 逐件账/伪断言败拒 2·临时目录驱动零仓写） |
| 20 | `t_frozen8` | `certify/frozen8.py --selftest` | 账载四判（判① 账载≡文档·机械收割更新账.md 八件在册值逐件咬合/判② 盘≡账·现盘八件 md5 全等 8/8/判③ 名单≡账·幂等·freeze 名单 tier1/tier2 与账载逐字咬合＋重产逐字节恒同/判④ 对账闭环·篡改现形·名单 md5 篡改与侧册篡改各 rc=1） |
| 21 | `t_frozen8_check` | `certify/frozen8.py check` | 在册名单四环咬合对账随套件在跑（名单 tier2 自洽/名单≡账载/tier2 侧册咬合/盘≡账载·rc 0 全咬合·只读零写盘·名单与侧册=`certify/frozen8_manifest.json`＋`frozen8_tier2.md5`） |
| 22 | `t_quad8` | `wrapper/quad8_reconcile.py`（四仓同 md5 副本群对账） | `--selftest` 夹具八判：freeze 咬合幂等/零漂移＋audit 只录/群漂移现形/UNREGISTERED 扫出/tier2·侧册·缺失三现形（零触真仓） |
| 23 | `t_quad8_check` | `wrapper/quad8_reconcile.py check` | 在册四仓名单随套件在跑对账（11 副本/六环咬合/audit 域只录不判·零写盘） |
| 24 | `t_frozen_call` | `wrapper/frozen_call.py`（逐调断言层） | `--selftest` 夹具五判：PASS 透传入账/在册外拒执 rc 8/tier2 先验 2/缺件 9/账行双见（临时账面） |
| 25 | `t_gate6_born_wrapper` | `wrapper/gate6_census.sh`＋`wrapper/born_world.sh` | `tests/test_gate6_born_wrapper.py`（启动层形制判·零编译零写盘） |

## 形制说明

- **fixture 最小化**：`fixtures/` 全部为本套件自造样例，不引外部大件。
  `retrofit_cn_sample.v`（842 行＋末换行）例外说明：`retrofit_gate7_irr.py` 的
  行形断言（843 split·L34 分隔行·L36 Require 行·`mod.M` 逐行锚）为硬编码，
  该 fixture 由 `mod.M` 锚表机械合成（`python3 tests/test_retrofit_dryrun.py --regen`
  可重建），内容零外部素材。
- **席位硬编码件的驱动方式**：`retrofit_gate7_irr.py` 与 `_abl1_wash.py` 无 CLI、
  路径硬编码席位（`retrofit_gate7_irr.py:7-11`、`_abl1_wash.py:10`）。测试以模块
  导入＋常量补丁把真实 `main()` 驱动到 fixture 上；硬编码席位路径永不被触碰
  （retrofit 干跑的写请求全部截获到内存——不落盘的机械化证明；wash 只写 mkdtemp
  临时目录，测毕即删）。
- **幂等**：`python3 -B` 禁 `__pycache__`；临时日志 mktemp+trap 清理；对仓库零写入。
  重复运行输出逐字节恒同。
- **已知实测行为（非缺陷猜测）**：`_abl1_wash.py` 重放时 `abl_audit_base_v7.v:require`
  会再 APPLY 一次——其 `new` 以 `old` 为前缀，工具 SKIP 判据要求 `c_old==0`，
  该 tag 恒不满足（`test_wash_fixture.py` 幂等判按 old⊂new 集合动态断言）。
- 退出码口径承 [CONTRIBUTING.md §4](../CONTRIBUTING.md)：`0`=通过、`2`=断言失败
  （`--expect` 等）、`9`=缺件；套件层 `0`=全绿（**含 SKIP**——SKIP 不计红）、
  `1`=任一红；例级 `111`=SKIP（正本环境缺卷让席·正本机恒全量真扫）。

> **gate4 预扫三铁则（口径段旁注·20261101 v10 轮入册）**——gate4
> （`verify/gate4_comment_guard.py`）对 Set 仓树预扫描必守三则：
> ① **预扫必须自 Set 仓根用绝对路径跑**（cwd 错位伪绿判例）：相对 `--tree` 在错位
> cwd 下解析到别棵在盘树即扫错面出伪绿——工具侧仅对「树不存在」设防（FATAL rc=2，
> `gate4_comment_guard.py:747-750`），对「存在但非目标树」不设防；
> ② **头注 ≤30 行硬上限（CI 全树口径）**：`--length-cap` 默认 30
> （`gate4_comment_guard.py:732`、`check_file` 形参 `:379`、超标检 `:527-534`）；
> ③ **五字段带点形** `Mission.`／`Dependencies.`／`References.`／`Constructivity.`／
> `Build.`（`FIELD_SPECS` 五字段英文带点正则：`gate4_comment_guard.py:188-194`）。
> 〔给料属性：判例面①与「CI 全树口径」承 v10 轮工单；②③上限值与五字段词形为
> 工具侧在卷锚点。详见 `更新账.md` v10 节。〕

## 五课反馈轮补记（20261101·席 rqsupport·用例 26–29）

> 编号承接套件现势（run_tests.sh 已在册 25 例——其中 22–25（`t_quad8`/`t_quad8_check`/
> `t_frozen_call`/`t_gate6_born_wrapper`）四行为前轮新增、本表未及同步；本席只补本轮
> 四行，不代前轮补表。〔rqsup4 巡检打磨轮补注：上四行已由该席据 run_tests.sh 用例
> 注释与前账账段于 20261101 补齐如上——非前轮原笔，判据描述以 run_tests.sh 为准。〕）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 26 | `t_world_hook` | `wash/world_hook.py`（世界基校验钩子·新件①） | `tests/test_world_hook.py` 五判：工具 selftest 十二判／**五课负例①nw5**：偏斜世界 WDIFF→rc 9·引擎零落盘（born 前断言拦下）／WMISS→9／pos 透传洗刀→产物落盘／冻结引擎 md5=`664446bc…` 零触旁证 |
| 27 | `t_select_audit` | `tools/select_audit.py`（选件审计器·新件②·v6 判据轮扩） | `tests/test_select_audit.py` 二十判：selftest 十一判／**五课负例②nw6**：批内重复→rc 1·DUP-BATCH／**负例③enbig7**：双批同名→rc 1·DUP-CROSS／树外名→NOT-IN-ORDER／pos（含 #代签与 / 路径形）→AUDIT-CLEAN／**v6 判据（nw10/abl6 空账·20261030）15 判**：parse_requires 全形式解析（From X Require Import/Export 多名多行·裸 Require·注释 Ghost 剥·动词/From 逐名在账）→STDLIB_ROOTS 白名单豁免（判例六件对空世界零缺口）→audit_requires 世界 .v/.vo 存在性闭包（缺口恰二·UpReqBanach 不误咬 UpReqBanachExp.v·计数面 8/3/5）→fail-loud 两向（MissingPath）→CLI 四码 0/1/2/9→**实盘补件面**：字符串散文 Require 剥（UpReqIndex.v:2821 判例形）＋裸形 Stdlib 白名单→缺口恰一 LW0QPoly |
| 28 | `t_verify_gate6` | `verify/verify_gate6.py`（gate6 薄包装＋eum 判例器化·新件③） | `tests/test_verify_gate6.py` 五判：selftest 十判／**五课夹具④gate6 ch1**：eum before(ch1=1)→after(ch1=0·名 5=5)→GREEN／ch1 滞治→RED／薄调正判（正本真扫·夹具树 ch1≥1）／judge 单翼→2 |
| 29 | `t_recipe_s07` | `recipes/S07_projection_reanchor_E5.md`＋E5 病面机检（新件④⑤） | `tests/test_recipe_s07.py` 五判：处方件判例锚词面齐／**五课夹具⑤**：E5 病面（语句面裸投影·跨行连排）→命中／注释掩蔽→零命中／愈面（real_eq/real_lt/real_le）→零命中／冻结引擎 md5 零触旁证 |

## 五课打磨轮补记（20261101·席 rqsup4·用例 30–31）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 30 | `t_recipe_pw1` | `recipes/ENBIG7_same_domain_collision_PW1.md`＋PW1 链机检（五课件③） | `tests/test_recipe_enbig7_pw1.py` 五判：处方件判例锚词面齐（PW1/仲裁 36c35816/五步词）／**前兆负例**：双批同名→`select_audit` DUP-CROSS rc 1／**入侵置换负例**：fixture 世界错代→`world_hook` WDIFF rc 9·引擎零落盘／**愈面正判**：认证代世界→WORLD-BASE-OK·透传引擎落盘／冻结引擎 md5 零触旁证 |
| 31 | `t_precedent_station` | `wrapper/precedent_station.py`（三判例验收站·五课件⑤） | `tests/test_precedent_station.py` 七判：`--station-selftest` 十判／轻链正判烟（fixture 语句面全等·证明体异→exit 0·站账 verdict PASS·knife 记名）／负判（语句面多一句→①rc 2→exit 1·不短路仍出②账）／REVIEW 升格（`--gate4-length-cap 5`→exit 2）／gate7 形制（缺 module→2·缺 .v→9·零开步）／未知刀面拒→2／names·gate4 冻结 md5 零触旁证（gate7 实跑为真编译重步·E2E 归席位沙箱不入套件） |

## 实战判例工具化轮补记（20261101·用例 32–33）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 32 | `t_netname_normalize` | `tools/netname_normalize.py`（.v.v 双后缀名净名归一器·本轮工具化①） | `tests/test_netname_normalize.py` 九节：selftest 八判／干跑默认（MAP 映射表 `<净名>.v.v→<净名>.v` 逐条·零字节落盘）→rc 1 PENDING／`--apply` 归一落盘→rc 0·源亡标在／md5 前后验讫在账（RENAME 行 md5=＋VERIFY-OK·改名不改字节逐字节断言）／COLLIDE 拒覆写（X.v 与 X.v.v 并存→rc 1·对侧件内容保全）／净世界→rc 0 CLEAN／CLI 四码（help 0·未知形参 2·缺 --dir 2·--dir 缺失 9）／`--map` TSV＋`--json` 出账咬合／`.v.v.v` 形一层一归一（临时目录夹具·零触真仓） |
| 33 | `t_verify_fresh` | `verify/verify_vo.py --require-fresh`（fresh-compile 防线·本轮工具化②） | `tests/test_verify_fresh.py` 八节：verify_vo selftest 十三判（原九判＋防线四判）／正判（9.1 魔数＋vo 新鲜）→rc 0 FRESH-OK／陈 vo 负例（v 拨未来）→rc 9 fail-loud／坏魔数（头 8 字节非 `436f712100015ff4`）→rc 9（新鲜也拦·非本链产物）／缺 v·缺 vo→9／单参与混用→2／help 0·未知形参 2／魔数冻结口径对 `verify_vo.py` VO_MAGIC_HEX 模块级咬合（divmod_gen 陈旧 vo 假绿判例工具化·临时目录夹具零编译零触真仓） |


## gate7 涨账工具化轮补记（20261101·用例 34）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 34 | `t_extract_magic` | `verify/extract_magic_check.py`（gate7 提取面 Obj.magic 逐件机检闸·本轮工具化③） | `tests/test_extract_magic.py` 十一节 23 判：selftest 十二判／E2E 红判（假 rocq/ocamlc 桩全链·默认 max=0 魔数 2→rc 1·上下文逐行 L1/L2·VERDICT: FAIL）＋台账咬合（verdict/magic_ml/max/magic_lines/ocamlc status）／E2E 绿判（--max 2→rc 0 PASS·mode=driver·targets 咬合·md5_v 对模块级）／inline 形（.v 自带 Separate Extraction→mode=inline·commands 逐名）／driver 形（本仓自带 `fixtures/names_sample.v` 只读兜底收 census 7 名含 Unicode 名道＋driver 稿词面 Stdlib Extraction 前奏在盘）／提取红（假 rocq rc=1→fail-loud·rocq_tail 随账）／ml 未产出红（不可计数≠绿）／ocamlc 面红（在卷实跑红→rc 1）＋缺卷让席（NOT-RUN 不计红·魔数面独立判）／CLI 四码（help 0·未知形参 2·缺 --world 2·缺 v 9·world .vo 未编译 9）／grep -c 口径（行计数·一行多魔数计一）模块级咬合／**v15 盲区补全节（首战判例·gate7 四件 2 PASS/2 Class 盲区 fail-loud）**：Class 声明夹具（Class/Record/Scheme/Canonical/Context/Declare/Extraction/About/Close 全形）census 不再误判异常——声明/命令 vernacular 不入目标·唯真主定义 cls_pick/req_inst 入账·DECL_SKIP_EXT 十五 token 在册／G13 形裸 Extraction 命令同治／未知 vernacular 仍 fail-loud rc=9（盲区收窄≠静默扩容·token 集常量定位＝冻结件 names/mac_stmt_names.py:38–51 frozen8 tier1·扩补落工具 import 面·冻结件字节零触碰）。假桩全链零真编译零触真仓（真链 E2E 归席位沙箱不入套件·承 precedent_station 判例口径） |


## v29 判例工具化轮补记（20261103·用例 35–37·v30 轮代补记）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 35 | `t_scan_v4_token` | `scan/scan_v4_token.py`（token 级限定名普查·W15 工具化①） | `tests/test_scan_v4_token.py` 十一判：混合行遮蔽夹具三站复现＋旧法（行级 grep -v 式）同夹具漏站＝盲区机械实证＋binder 追踪零误报＋已洗参照件零站；真树抽查 `ROCWASH_TREE_SAMPLES` 环境门控缺省跳过不充红 |
| 36 | `t_cure_pack` | `wash/cure_pack.json`＋`cure_applier.py`（消费位治愈正典包·五式存量＋v1.1 九式＋v1.2 五式·W15 工具化②·v31/v32 扩） | `tests/test_cure_pack.py`：legacy 五式触发/幂等/门控自检＋v1.1 face-regex 九式自检（face/proof 域守卫·intros-tail guard·exclusive-group rc4）＋v1.2 S07 五式自检（壳除/记号重绑/桥裸名/谓词面收敛/binder 站型·binding-right 守卫·file_include 门）＋fixture 干跑-apply-二次零变更（qle/natle/shadow 三夹具·守卫负例逐字断言）＋S07 夹具流程（术前站数 1 report-only·干跑 A=2/B=1/C(a)=5/C(b)=2·apply＋binder 手术＋全零复跑·conflict --json rc4 器修回归）＋`cure_examples.v` 编译 rc=0（`ROCWASH_ROCQ` 门控·cpu_guard 包裹）＋门控 S07 编译弧（world 绿→base 红面 Illegal application→cured＋手术绿→Separate Extraction .ml/.mli 双面 Obj.magic 0/0·裸字段经全局实例解析）＋不透明 reflexivity 负证 rc≠0 |
| 37 | `t_erasure_classifier` | `verify/erasure_classifier.py`（擦除位六簇分类器·W15 工具化③） | `tests/test_erasure_classifier.py` 十三判：六簇判定/coq_ 前缀/多行 inner-component/premise 位/CAPTURE 交叉对拍/resolve 状态；真件回放 `ROCWASH_ERASURE_MLI/SCAN` 门控缺省跳过 |

## v30 探测战役工具化轮补记（20261103·用例 38–40）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 38 | `t_probe_engine` | `wash/probe_engine.py`（批量闭包相容探针引擎·承 W13 probe_batch.py·v30 工具化①） | `tests/test_probe_engine.py` 九节：工具 selftest 四判／stub 全链三分（WASHABLE rc0+RED>0／BORN-CLEAN rc0+RED=0／RED-MISSING_LIB rc1·missing 库名捕获·red_count/md5_match 回填）＋清场五件出世界入 logdir／NO-SRC 不编译如实出账／TIMEOUT（--timeout 2→rc=124）／resume 幂等（重跑 SKIP(done)＋台账字节恒同）＋--fresh 确定性同账／guard 队列制包裹（rc=7 真取透传＋留证日志 [cpu_guard] 横幅）／RED 缺列→RC0 三分不可判如实出／CLI 四码（help 0·未知形参 2·缺参 2·缺件 9）＋坏清单（缺 md5 列）rc2／真 rocq 全链门控节（`ROCWASH_ROCQ` 缺省 SKIP 不充红；门控轮：fixtures 一绿一红经 cpu_guard 包裹实编译→BORN-CLEAN＋RED-MISSING_LIB＋世界纯度＋logdir 留证全过）。夹具 `fixtures/probe_pass_sample.v`＋`probe_red_sample.v`（临时目录驱动零触真仓·stub 节零真编译） |
| 39 | `t_chain_graph` | `tools/chain_graph.py`（多账合并链根图·承 W25 w25_merge_ledgers.py·v30 工具化②） | `tests/test_chain_graph.py` 七节：selftest 六判／双形通吃（probe_engine records 壳×W13 裸 dict 混并）／合并语义（后批覆盖·batches 累积·标签取文件名去 .json）／链根自身可洗性三分（washable true/false/UNPROBED 逐字段）／missing 双源（字段直用·red regex 兜底 raw 空格形与「 | 」拼接形双咬合）／TOP 榜（n 降序·`--top` 截断·表头行·json top_order 保秩）＋json/md 重跑字节恒同／CLI 四码。合成双账临时目录夹具零触真仓零网络 |
| 40 | `t_ledger_sync` | `tools/ledger_sync.py`（probe×状态台账合并同步·v30 工具化③·v2.1 增补） | `tests/test_ledger_sync.py` 十节：selftest 十三判／CLEAN 全链（全覆盖 probe＋零发现 exit 0·UNPROBED 升格 rc0→WASHABLE／rc1→DRIFT-BLOCKED 逐行咬合·probe_engine 全字段记录直吞）／E1 去重（同件名多行保首行·逐笔 FINDING·行数正确）／E3 幽灵（只记账不落行·名单响亮）／特异 tag（rc=124→probe:timeout·NO_SRC→probe:no-src·UNPROBED 不升格）／NO-MD5（W13 老式账只注记不升格）／报告面（--report JSON schema/counts/逐笔发现咬合）／CLI 四码＋列校验两变体（缺必需列 rc2 不产出·行宽不齐 rc2）＋幂等重跑字节恒同／items 子键壳＋元数据滤除（PROBE-META-SKIP·全元数据零记录 rc2 拒同步）／GEN-DIVERGENCE 分歧出账（divergence_with 记录逐笔响亮＋行注记 probe:gen-div 洗代名·幂等·md5 咬合升格照常）。合成夹具临时目录零触真仓零网络 |
| 41 | `t_comment_pack` | `wash/comment_pack.json`＋`comment_sweep.py`（注释域 sweep 旁车·v31 工具化） | `tests/test_comment_pack.py` 六节：selftest 四判（旗词注释域换形＋字符串/嵌套注释免疫＋头注换代＋w7 code 行全等投影＋幂等）／pack 完整（engine=comment-state-machine·旗词表 载体→carrier·header_spec 五字段英形＋行上界 30）／fixture 流程（干跑零写→apply 换形 2 处·字符串字面量逐字保留·嵌套深度可达→重跑零变更）／头注换代（--header-map 数据驱动·换代后 code 行全等·重跑零变更）／头注形校验（五字段缺一报 problem report-only）／CLI 三码（help 0／缺参 2／缺件 9）。夹具临时目录副本驱动·零触真仓零网络 |

## v32 S07 适配式工具化轮补记（20261103·新增用例 42＋用例 36 扩节·W66 支撑席提案实装）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 42 | `t_dual_scan` | `scan/dual_scan.py`（双器对拍驱动·v32 工具化·承 seat_wash66 w66_dual_scan.py） | `tests/test_dual_scan.py` 十节：净样例双器 0/0＋双端空 diff／语句面站 only_stmt 非空 only_v4 空（单侧情·报而不决——器共识非全集证）／token 站 only_v4 非空 only_stmt 空／确定性（同目标两跑报告字节恒同）／CLI 四码（无目标 2·缺 dir 2·缺 file 9·缺器 9·help 0）。临时目录夹具驱动零触真仓零网络 |
| 36（v32 扩节） | `t_cure_pack` | `wash/cure_pack.json` v1.2＋`cure_applier.py`（S07 世系适配五式＋line-insert/station-report 两引擎＋exclusive-group --json 器修） | cure32_A 壳除（型注＋binder 双站·:=-binding-right 右位排除）／cure32_B 记号重绑（末个 Import 行后插 Notation 行·file_include＋裸 R 门·幂等跳过）／cure32_C(a) 桥裸名（face+proof 域·8 名交替）／cure32_C(b) 谓词面收敛（lt→real_lt/req→real_eq·mult 等含 lt 子串词零触碰·收敛目标=供给引理结论常量名机械断言）／cure32_station binder 壳站（report-only·术前 1/术后残差 0·--apply 幂等残差排除 report 型）／conflict 器修回归（--json 落盘＋rc=4＋零 traceback） |

## v34 E2/E3 提取面缺陷族 cure 扩节（20261104·用例 36 扩节·CI #178 逆向修订轮）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 36（v34 扩节） | `t_cure_pack` | `wash/cure_pack.json` v1.3＋`cure_applier.py`（E2/E3 缺陷族五式·零新引擎全复用 v32） | pack 完整（5+9+5+5=24·v34_lineage 在册·cure34_E2_station report-only·E3 对式序=站改写先于 shim 插入机械断言）＋selftest v34 向量（E3 站改写 2/shim 插入/shim 体 face_exclude 护体二遍零残差；E2 标注/元数/report 站/幂等；v34 whole-pack 幂等）＋夹具流程（E3 干跑 stations=2 shim=1→apply rc0→shim 行在·站改写·shim 体原样→全零复跑；E2 术前站数 1 report-only→apply→中间件面＋元数随行→全零复跑含 station 残差）＋门控 E2/E3 编译弧（`ROCWASH_ROCQ` 门控·cpu_guard 包裹：world 绿→**pre-fix 消费件编译绿＝提取时缺陷族实锤**→cure→cured 绿→Separate Extraction：E3 消费单元 magic 0/0＋`val ufx_nat : coq_Real -> coq_Real` 单态 shim 站；E2 修前 .mli `'a1 -> 'a1` 多态面→修后 `val unann : nat -> nat` 单态面→消费单元 magic 0/0→**world 访问器债=1 机械钉**〔实体修复工作流域·fixture world 头注与 canonical_note 记界〕）。夹具 `fixtures/cure34_e23_world.v`＋`cure34_e3_fixture.v`＋`cure34_e2_fixture.v`（临时目录驱动零触真仓·干跑永不编译） |

## 20261111 四工具波补记（集成席·用例 44–47）

> 编号承接套件现势（run_tests.sh 在册 47 例）：44（`t_registry_union`）由铸席随件
> 在册（run_tests.sh t_registry_union·本表此前未及）、45–47 为本轮集成席补的最小
> 自测壳三行；43（`t_cw_entry`·v33 轮）此前亦未及入表——遵「不代前轮补表」先例
> 本轮不代补，留主会话定夺。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 44 | `t_registry_union` | `tools/registry_union.py`（注册册 union 手术器·三席铸件·套件挂接铸席已在册·集成席核认） | `tests/test_registry_union.py` 九节：selftest 八判／coq 夹具组／陷阱组同名不同形对 merge-base 必过滤／重锚 md5 冻结向量 1414cddb／A2·A3 负判零写盘／干跑-apply-幂等／json 确定性／CLI 四码＋用法对偶／git 三 ref 直读（夹具只读输出全落 mktemp·零触真仓零网络零编译） |
| 45 | `t_toolchain_dyld_doctor` | `tools/toolchain_dyld_doctor.py`（dyld 工具链断链诊断器·只诊断＋restore 建议禁代执行） | `tests/test_toolchain_dyld_doctor.py` 最小自测壳两判：--selftest rc=0 且含 `DYLD-DOCTOR-SELFTEST PASS` 冻结标记／--help rc=0（otool 解析/exists-missing/同名兜底全链离线向量组由铸席 --selftest 自证·本壳挂接套件·零真 otool 零编译零网络零写盘） |
| 46 | `t_ci_triage` | `tools/ci_triage.py`（CI 红炉分诊器·五族+绿炉判类谱·红是数据非器红） | `tests/test_ci_triage.py` 最小自测壳两判：--selftest rc=0 且含 `CI-TRIAGE-SELFTEST PASS` 冻结标记／--help rc=0（判类谱六样张/基线 13.3x 判例/谱外 UNRECOGNIZED 离线向量由铸席 --selftest 自证·本壳挂接套件·零网络零写盘） |
| 47 | `t_net_probe` | `tools/net_probe.py`（网络窗探针·双探稳窗律·单探禁发射） | `tests/test_net_probe.py` 最小自测壳两判：--selftest rc=0 且含 `NET-PROBE-SELFTEST PASS` 冻结标记／--help rc=0（classify_error 分类/canned 注入/稳窗判定零网络向量由铸席 --selftest 自证·本壳挂接套件·零网络零写盘） |

## 20261111 pushci 轮补记（集成席·用例 48）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 48 | `t_pushci` | `tools/pushci.py`（推送 CI 一键流水线编排器·五段管线 preflight 发射闸→push→watch→heal→verdict±merge·v35 四器 subprocess 编排零新引擎·verdict 七态 success/fix-content/toolchain/unstable/heal-exhausted/gate4-block/dry-run） | `tests/test_pushci.py` 十节：selftest 冻结矢量（rc 0·`PUSHCI-SELFTEST PASS`）／tmp-git 仓 helper 自证（repo_path 由夹具建仓·push 永不真跑——场景层 git 全走 --git-caller canned）／S1 绿径（preflight 双闸→push 四调 get-url/rev-parse/push/ls-remote 远端为准→watch 2 轮 success→verdict success exit 0·零 heal 零 merge）／S2 NETRED 愈合（B 族 canned.jobs 真判类→probe STABLE→rerun 201 run_id 咬合→attempt2 success exit 0·heal_rounds==1）／S3 内容红（A 族→verdict fix-content exit 2·零 rerun 实证＝rounds 空＋fired_total==0＋api_calls 零 POST·判类 outcome 在册 last_triage）／S4 heal 耗尽（NETRED×3·--max-heal 2→heal-exhausted exit 1）／S5 merge 流（--pr 42 PUT merge 200→merge_sha 非空 exit 0）／S6 dry-run（计划输出·api_calls.json==[] 零 git calls.json==[]→verdict dry-run exit 0）／幂等（六场景各两跑 report 字节恒同·漂移叶限墙钟类窄键名）／CLI 五码（help 0·未知形参 2·缺必给 2·repo 缺失 9·injector-git-caller 单边 2）。夹具 `fixtures/pushci_scenarios/s1…s6` GitHub API 真形 canned 按轮次序列·远端恒指不可达假域 pushci.invalid·--sleep-scale 0＋--netrc 恒指不存在路径——结构性零真网络零真 push 零编译零写盘 |

## v37 工作流三器补记（20261111·用例 49–51·集成席本轮补表）

> 三例随 v37 轮已在 run_tests.sh 在册（run_tests.sh t_cw_sentinel/t_wash_shape/
> t_unclog）；本表此前未及——本轮集成席据 run_tests.sh 在册注释补表，判据描述
> 以 run_tests.sh 为准（遵「不代前轮补表」例外：本轮任务书钦定「计数同步」）。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 49 | `t_cw_sentinel` | `tools/cw_sentinel.py`（实时动态哨·三路信号源 CI runs/台账链根/buildlog 词面→JSONL 事件流·once/loop 双模·零动作是缺省） | `tests/test_cw_sentinel.py` 最小自测壳两判：--selftest rc=0 且含 `CW-SENTINEL-SELFTEST PASS` 冻结标记／--help rc=0（哨自身 --selftest 十二矢量 canned 注入零真网络零编译由铸席自证·v40 稳态席扩容⑪state 崩溃恢复（损坏红拒 9 禁静默重建·--rebuild-state 显式重建）⑫--emit-max-bytes JSONL 轮转（.1/.2 保留 2 代·seq 跨代续号）·本壳挂接套件） |
| 50 | `t_wash_shape` | `tools/wash_shape.py`（洗形器·正典形五洗流水·plan 缺省零写盘） | `tests/test_wash_shape.py` 最小自测壳三判：--selftest rc=0 且含 `WASH-SHAPE-SELFTEST PASS` 冻结标记（十八判向量全 tmp 夹具·v39 轮洗形席扩容 preset 链四判：模板库装载在位／preset·--header-map 胜 env／占位替换渲染→apply 端到端／同槽互斥 rc2·＋无源 plan-miss＋模板库缺失 rc9·v40 稳态席扩容判17 --loop 事件流同形对齐（rocqwash-sentinel-event/1·seq 跨进程续号）判18 plan 缓存失效语义（源件 md5 变→重算·恒同→hit 复用））／--help rc=0／退出码口径抽验 2/2/9 |
| 51 | `t_unclog` | `tools/unclog.py`（疏通堵塞闭环引擎·probe 归集→chain_graph 挑根→cure_applier 落刀→复核→verdict unclogged/wall/rounds-exhausted·缺省干跑·frozen 在册红拒） | `tests/test_unclog.py` 最小自测壳三判：--selftest rc=0 且含 `UNCLOG-SELFTEST PASS` 冻结标记（十三矢量全 --injector canned 罐装·v40 稳态席扩容⑪--state-file 同形哨态 seen 差分（red-new 事件 only-new·损坏 state 红拒 9 禁静默重建）⑫--rounds/--loop 与 --audit/--state-file 两组互斥 rc=2）／--help rc=0／退出码口径抽验 2/2/9 |

## v38 综合体检器补记（20261111·用例 52·集成席）

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 52 | `t_cw_doctor` | `tools/cw_doctor.py`（综合体检器·四域聚合：环境 dyld／网络 net_probe／注册册锚正典形审计／堵账 probe_engine＋chain_graph 抽样真探→综合健康分 0-100＋verdict healthy/degraded＋advice 处置清单·schema rocqwash-cwdoctor/1·只诊断禁代执行） | `tests/test_cw_doctor.py` 最小自测壳两判：--selftest rc=0 且含 `CW-DOCTOR-SELFTEST PASS` 冻结标记（九节向量全 --injector canned 罐装 tmp fixture：四域全绿 100／环境红降 60／注册 skip 归一 86.67／堵账 TOP 注入 88.75／advice 生成／JSON 幂等字节恒同／CLI 四码＋罐装全覆盖／注册审计单元——零真 otool 零真网络零真编译，chain_graph/注册审计真跑纯 stdlib 由铸席自证）／--help rc=0（缺壳由本集成席自补·零触真仓零写盘） |

## v39 文档核与接驳实战轮补记（20261111·用例 53–54·集成席）

> 53（`t_relay_e2e`）为工装席铸件（tests/test_relay_e2e.py 在盘·总套挂接归集成席）；
> 54（`t_doclint`）为 doc_lint 器自补最小自测壳（缺壳自补——器由工装席铸·壳由
> 本集成席仿既有最小自测壳形铸）。两例经 run_tests.sh 在跑全绿实证（本轮集成席
> 全绿验证 54/50/0red/4skip）。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 53 | `t_relay_e2e` | `tests/test_relay_e2e.py`（接驳实战核 e2e：cw_sentinel `--on-red-preset unclog` 全链·工装席铸件） | 三判：①事件触发——哨 --once＋injector canned CI 红炉（run 178 failure→ci_triage 子进程真判类 A-content-red）→ci-red 事件落 --emit JSONL→preset 代跑 unclog：actions 账 cmd=preset 逐字展开（含 unclog report 路径 `{emit_dir}/unclog_{run}.json`）·代跑 rc=9 如实入账（fixture 无 --world·fail-loud·哨退出码仍 0——旁路动作非器面铁律）②unclog 干跑 rc=0 且零写盘——同 fixture 树 unclog --audit（只读堵账基线：final=audit·cures 恒 0·--src 全文件 md5 清单跑前跑后自证恒同）·见红 red_files=["B"]·出可洗链根 A washable·墙空 ③JSONL 同盘 unclog report 路径——判1 actions 账所记路径与判2 实落 report 逐字节对拍（存在·schema=rocqwash-unclog/1·verdict=audit）。全 canned 罐装零真网络零真编译零触真仓（tmp 自管 mkdtemp 进 finally rmtree） |
| 54 | `t_doclint` | `tools/doc_lint.py`（文档←→实现一致性三查器·工具表查 cw.sh 四处互检＋tools/ 通用入口对账／计数查 CASES vs tests/README.md vs README.md／旗标查 doc 引用旗标 vs 各器 --help 实出·schema rocqwash-doclint/1） | `tests/test_doc_lint.py` 最小自测壳三判（缺壳由本集成席自补）：--selftest rc=0 且含 `DOC-LINT-SELFTEST PASS` 冻结标记（tmp 迷你仓六矢量 V1 一致仓 0 漂／V2 工具表缺一 hint／V3 计数漂／V4 旗标幻引／V5 CLI 三码＋--help-cap 0→2／V6 JSON 幂等字节恒同——由铸席 --selftest 自证）／--help rc=0／退出码口径抽验 2/2/9（--bogus=2／--help-cap 0=2／--repo 缺目录=9）。零网络零写盘零触真仓 |

## v40 破坏面矩阵与基线对比轮补记（20261111·用例 55–56·集成席）

> 55（`t_destructive_matrix`）为破坏面席铸件（tests/test_destructive_matrix.py 在盘·
> 总套挂接归集成席）；56（`t_baseline_diff`）为 baseline_diff 器自补最小自测壳
> （缺壳自补——器由工装席铸·壳由本集成席仿既有最小自测壳形铸）。两例经
> run_tests.sh 在跑全绿实证（本轮集成席全绿验证·见 submit 账）。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 55 | `t_destructive_matrix` | `tests/test_destructive_matrix.py`（破坏面复核矩阵·一行一拒写判据·破坏面席铸件） | 17 行拒写判据：器×写面×护栏锚 file:line 逐行断言——unclog×4（U1 缺 --apply 零写盘 tmp 树 md5 恒同／U2 --audit 零写盘＋与 --apply 互斥 rc2／U3 frozen 在册红拒 frozen8 实取／U4 非链根件零被动）＋wash_shape×4（W1 plan 零写盘／W2 --apply 后 rescan partial 不谎报 shaped／W3 冻结名显式指认红拒 rc2 收件即拒／W4 同槽互斥 rc2）＋pushci×3（P1 --dry-run api_calls/git-caller 双流水空／P2 内容红零 rerun heal.rounds 空＋api 零 POST／P3 heal 帽尽停 --max-heal 3 恰 3 发）＋cw_sentinel×2（S1 缺省 report-only actions 账空／S2 --on-red-preset 缺 --emit rc2）＋registry_union×2（R1 干跑 --out 给而不落／R2 --apply 才落刀＋无 --out rc2）＋cure_applier×2（C1 干跑目标件 md5 恒同／C2 --apply 才落刀＋幂等断言败 IDEMPOTENCE-FAIL rc1 零字节动）。全 tmp fixture＋injector 罐装零真网络零真仓零真编译；红＝护栏破 exit 1 响亮列破口 file:line |
| 56 | `t_baseline_diff` | `tools/baseline_diff.py`（堵账基线对比器·两份 unclog --audit 基线→三清单＋score_delta·verdict 四态·工装席铸件） | `tests/test_baseline_diff.py` 最小自测壳三判（缺壳由本集成席自补）：--selftest rc=0 且含 `BASELINE-DIFF-SELFTEST PASS` 冻结标记（六矢量①improved 红减②degraded 红增＋墙因变③stable＋timing 不入对比＋json/md 幂等字节恒同＋零写输入④incomparable 候选集异＋非 audit 形⑤md 输出⑥CLI 四码＋形坏拒判零出账——tmp 合成基线由铸席 --selftest 自证）／--help rc=0／退出码口径抽验 2/2/9（--bogus=2／缺两账=2／缺账文件=9）。零网络零编译零触真仓 |

## v46 红事件路由与注册册卫生审计轮补记（20261112·用例 57–58·集成席）

> 57/58 两器均为本轮铸席铸件（tools/red_dispatch.py·tools/registry_audit.py 在
> 盘·套件挂接与最小自测壳均归集成席缺壳自补）。两例经 run_tests.sh 在跑全绿
> 实证（本轮集成席全绿验证·见 submit 账）。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 57 | `t_red_dispatch` | `tools/red_dispatch.py`（红事件路由器·哨红事件→动作预设路由·三档 preset report-only/suggest/auto·缺省零执行·auto 显式才代跑 60s 帽 rc≠0 入账不改退出码·防重 state＋cooldown·五路由全挂既有 cw.sh 路由零新引擎·A 族内容红禁代修） | `tests/test_red_dispatch.py` 最小自测壳三判（缺壳由本集成席自补）：--selftest rc=0 且含 `RED-DISPATCH-SELFTEST PASS` 冻结标记（十二矢量①路由表全族覆盖②占位替换③auto 执行实证④state 防重⑤cooldown⑥report-only 缺省零执行⑦JSONL stdin 多事件⑧fail-loud 面⑨rc≠0 不改退出码⑩A 族 fix 清单＋C 族定令⑪确定性⑫整体单对象兜底——tmp 假仓根标记文件实证·由铸席 --selftest 自证）／--help rc=0／退出码口径抽验 2/2/9（--bogus=2／--dry-run 缺 auto 档=2／事件文件缺=9）。零网络零编译零触真仓 |
| 58 | `t_registry_audit` | `tools/registry_audit.py`（注册册卫生审计器·order.txt/_CoqProject 双册只读四账出账：重复行/锚撞/顺序号形/形怪/缺锚/孤儿/live 拓扑＋--fix-plan 确定性处方零写盘·--apply 不存在·键式/锚正典直用 registry_union 零重造·病灶是数据恒 exit 0·v35 判例代码化） | `tests/test_registry_audit.py` 最小自测壳三判（缺壳由本集成席自补）：--selftest rc=0 且含 `REGISTRY-AUDIT-SELFTEST PASS` 冻结标记（五判矢量：四账判类全谱 total=19／处方保首＋77c2b9a8 md5 冻结向量＋占位／只读实证双册与 live 树前后 md5 恒同＋--apply 不存在 rc2／确定性重跑字节恒同／git 直读 tmp clone＋坏 ref 9／CLI 四码——tmp 合成 v35 真账形态由铸席 --selftest 自证）／--help rc=0／退出码口径抽验 2/2/9（--bogus=2／无输入面=2／半册=2／缺册=9）。零网络零编译零触真仓 |

## v47 门控编译弧翻绿与注册册处方执行器轮补记（20261112·用例 59·集成席）

> 门控编译弧总开关（路线图④⑧A 案）已入 run_tests.sh（翻绿席铸·缺省探测四路径
> ROCWASH_ROCQ/GATE7_PROBE_SCRIPT/GATE6_SCRIPT/BORN_WORLD_ROCQ·env 已设则尊·
> 诸闸位判据语义零改动·env 缺且缺卷仍 SKIP）——门控弧两例（t_cure_pack 编译
> check 段/t_probe_engine 真 rocq 节）本在册恒跑，翻绿面以套件实跑 SKIP 现势为准；
> t_quad8_check 系四仓副本群缺卷族（另族）不在本案。59 例为集成席直挂
> （tools/registry_fix.py 在库·器 --selftest 八矢量全 canned tmp fixture·零触真仓）。

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 59 | `t_registry_fix` | `tools/registry_fix.py`（注册册处方执行器·registry_audit `--fix-plan` 处方逐条落刀·三类处方 DEDUP 保首/锚刷/ORPHAN-ADD skip·**缺省干跑**·`--apply` 落刀后断言三判炸即回滚·staging 全内存零写盘·同参纪律 audit↔执行器逐字咬合·schema `rocqwash-registry-fix/1`） | 器 `--selftest` 直挂八矢量 rc=0 且含 `REGISTRY-FIX-SELFTEST PASS` 冻结标记：①干跑零写盘＋逐条 md5 账＋skip 清单全谱＋干跑 report 重跑字节恒同②--apply 12 重复块→0＋断言三过（dup 零残留/锚撞零增/孤儿不增）＋md5 账对盘③77c2b9a8 锚刷 md5 冻结向量＋同输同出（registry_union CLI 逐字节恒同）④注入炸点 INJECT_ENV=post-write 回滚⑤自然炸点 A-fix-2 新撞锚回滚⑥staging 炸零写盘（work-dir 不建）⑦CLI 四码（help0/bogus2/无输入2/缺audit9/缺册9/坏schema2/无fix_plan2/同参破2/缺anchor-src9）⑧落刀确定性（双 fresh 夹具册面 bytes＋逐条 md5 账恒同）。全 canned tmp fixture·零网络零编译零触真仓 |
| 60 | `t_norm_lint` | `tools/norm_lint.py`（注释面规范化检查器·report-only 首形·header 五字段/jargon 词面/CJK 残留/禁类/头注行数帽五查·基线账报告出账 norm-lint-baseline json/md·全仓注释面现状如实） | `tests/test_norm_lint.py` 最小自测壳三判：--selftest rc=0 且六矢量 PASS（map-load/jargon-hit/fields-missing/substring-exemption/whitelist-exemption/english-clean 由器自证）／--help rc=0／退出码口径抽验（bogus=2／缺 tree=9／--selftest 与扫描旗标同用=2／非 .py/.sh/.md 扩展名=2／缺 jargon-map=9）。零网络零编译零触真仓 |

## Collaboration-isolation tooling addendum (cases 61-62)

| # | 用例 | 被测 | 判据 |
|---|------|------|------|
| 61 | `t_contrib_intake` | `tools/contrib_intake.py`（contribution intake inspector: read-only four-gate verdicts — registry / norm / gate expectation / isolation — over a contribution face vs a base face; gates never short-circuit, BLOCK is data, exit stays 0） | `tests/test_contrib_intake.py` minimal shell, three checks: --selftest rc=0 with `CONTRIB-INTAKE-SELFTEST PASS`（the tool's own dual-git-clone vectors attest the four gates: clean/collision/jargon/overlap plus read-only/determinism/archive parity/probe outcomes/CLI）／--help rc=0／exit-code spot checks bogus=2, no-input=2, missing-face=9, bad-ref=9。tmp fixtures only, zero writes, zero network, zero real-repository contact |
| 62 | `t_registry_regen` | `tools/registry_regen.py`（contribution registration-row regenerator: merge-target books verbatim as the draft bottom + canonical `#R<seq>-<md5-8>` rows tail-appended in dependency order; dry run by default, `--apply` writes only under an explicit `--out`） | `tests/test_registry_regen.py` minimal shell, three checks: --selftest rc=0 with `REGISTRY-REGEN-SELFTEST PASS`（the tool's own tmp-fixture vectors attest three-piece topological regeneration / missing-dependency BLOCK / the frozen md5 vector / dry-run zero-write / blast and divergence cases / CLI codes / rerun identity）／--help rc=0／exit-code spot checks bogus=2, no-input=2, apply-without-out=2, negative-seq=2, missing-base=9。tmp fixtures only, zero writes, zero network, zero real-repository contact |
| 63 | `t_evolve` | `tools/evolve.py`（autonomous evolution engine v1: harvest five signal classes by subprocess of the existing engines — norm-lint fitness with frozen surfaces excluded / sentinel `--once` dual-repo new ci-red events / suite last state / registry audit accounts with increment / maintained UNRECOGNIZED sentinel events; derive fixed-rule scored candidates plus genetic standing candidates from the ledger lineage; draft the constitution three-law-preamble task brief; draft-only, never executes a candidate, never writes the repository） | `tests/test_evolve.py` minimal shell, three checks: --selftest rc=0 with ten PASS vector groups（canned signal injection via real subprocesses / candidate rules / draft formation / frozen exclusion / sentinel seen-idempotence / deterministic double run）／--help rc=0／exit-code spot checks bogus=2, no-draft=2, no-signal=2, watch-without-state=2, two-suite-sources=2, missing-baseline=9, missing-parent=9。tmp fixtures only, zero writes, zero network, zero real-repository contact |
| 64 | `t_clean_mode` | clean-mode switch selftest（ROCWASH_CLEAN=1·canonical-dependency census in `docs/clean-mode-manual-20261114.md`：available / SKIP / degraded / unavailable four tiers） | `tests/test_clean_mode.py` 18 vectors, zero compile / zero network / zero writes outside mkdtemp: six unavailable-face positive vectors report `requires canonical environment` rc=9（scan_station `--baseline`／dyld_doctor default worker chain／cw_doctor real rollup without `--injector`／probe_engine default `--rocq-cmd` template／quad8 freeze·check without `--roots-file`／frozen_call default frozen manifest or campaign call log）／`tools/_abl1_4b_compile.py` clean adds the report line while keeping its own exit-1 toolchain contract（V16·V17）／default-mode negative vectors assert no report（V2·V5·V10·V17）／selftest faces are switch-invariant（rc under clean == rc under default·V4·V9·V12·V15）／caller-owned faces stay available（`--registry` print V13·explicit `--manifest`+`--log`）／suite gate word face present（V18） |
| 65 | `t_registry_fix_anchor` | REANCHOR-face tests for `tools/registry_fix.py`（anchor residual gate A-fix-6 `treated_anchors_canonical`: after a treated `--apply`, every executed REANCHOR key must carry no `anchor-seq-form` / `anchor-malformed` finding in the same-parameter re-audit; the oracle is the audit producer's own classification in registry_audit sections.anchors, so no anchor semantics are defined in the test or the gate） | `tests/test_registry_fix_anchor.py` four checks: --selftest rc=0 with the `REGISTRY-FIX-SELFTEST PASS` frozen marker／--help rc=0 usage face／exit-code spot checks bogus=2, no-input=2, missing --audit-json=9／anchor-face oracle vectors on a canned mkdtemp fixture（tool's own builder）: dry-run zero-write with assertions honestly NOT-RUN, apply with the four assertion fields PASS（treated_anchors_canonical included）, re-audit duplicates=0 with executed keys residual-free while skip-class keys（missing entity, missing anchor）stay by design, plus six unit vectors on the residual gate（blast ASSERT-TREATED-ANCHOR-NONZERO on treated seq-form/malformed; silent for untreated keys, anchor-collision kind, anchor-missing kind）. tmp fixtures only, zero writes outside mkdtemp, zero network, zero compile, zero real-repository contact |
