# 分歧案卷 v2：docs/scheduling-feedback.json —— 已提交面 vs 重算面（三值、调度反馈）· 根因定谳版

Ticket: R2-48（案卷 v2 铸席·书面；身份 live-lumen，主机 Darwin arm64）
Date: 2026-11-21
案态：根因已定谳 —— H1，HIGH，两跑反证存活（R2-44）。处置开放依旧，裁量权在台：本档登记定因后三选项的测量后果，不代台选择。
承替：本档承替 v1（R2-39，同目录 `divergence-case-scheduling-feedback-20261121.md`）。v1 的 §2 时间线与 §5 命令基座原样保留（本档 §2/§7）；中文为忠实转写，措辞与数字如有出入，以 v1 英文原文为准。全档以定因结论为基准行文：face 先于输入落库，10 行 ghost 行未随库。

依据（sources）:
- v1 案卷：`return-package/divergence-case-scheduling-feedback-20261121.md`
- R2-44 根因侦察卡：`return-package/divergence-rootcause-recon-20261121.md`
- R2-44 回执：`../R2-44-receipt.md`
- /Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl 行 22/23（本席本场核验，§8）

纪律：本席本场零 git 查询、零网络、零仓树写；写出仅两件——本案卷 v2 与 `../R2-48-receipt.md`。凡标〔R2-39 记录〕〔R2-44 记录〕者均为原席执行、本席逐字转引；本席亲自执行并出示输出的检查只有 §8 所列。

---

## 1. 案情一句话（定因版）

v1 的一句话原样成立：2026-11-19 以来每个取样锚上，docs/scheduling-feedback.json 的已提交 canonical 面与 tools/learning_feedback.py 对同一提交自身输入的确定性重算，恰在三个 repair_outcomes 值上相左；文件其余字节全同，伴面 docs/b-gate-audit.json 在同锚重算字节重合——分歧类专属 scheduling-feedback.json。

面值对（值引自提案行 1/15/19/21 与 R2-36 回执；blob 同一性 R2-39 会话重钉）：

| 侧 | blob | sha256 | repair_outcomes（repaired / unrecorded / rate / wogc / escalated） | 总行数 |
|---|---|---|---|---|
| canonical（已提交） | a952af079aa8e6baf68b38f60a5d68248963d86e | 1ed190e168041c74488086f3aa5f55711a2a140fc436e043b0c183f58db19b14 | 3 / 46 / 0.0588 / 2 / 0 | 51 |
| 重算（产出） | 06998c8fbbcf3d88087d370fc1556bcb3fce8b08 | e66ca0a1d1b862b6b0554b96d7852ed4b39e239a32f114ba09199fbadb9c423b（全值） | 1 / 38 / 0.0244 / 2 / 0 | 41 |

v1 记录产出侧 sha256 只有 16 位前缀（v1 诚实注记 6）；64 位全值已由 r24 批（提案行 23，本席 §8 核验）补上，缺口闭合。

定因后补的一句（v1 说不了、现在能说）：canonical 侧的「51」从来不是已提交事实，是 face 生成当时的输入行数。compute_repair 对每个合法 JSONL 行 total+1、rate=repaired/total（工具 256–276 行），故已提交 total=51 反推生成时输入恰 51 合法行；而已提交 ledger 只有 41 行，全史四 blob 无一 51 行（§4.2 证三）。〔R2-44 记录〕

差值算术（fail-loud 更正，R2-44 在案）：ask 原话「8 行」只是 unrecorded 差（46−38）；实测总差 10 行——unrecorded +8、repaired +2；wogc=2、escalated=0 两侧相同（自已提交面重钉）。三值之差是一个量的两种记法：3/51=0.0588，1/41=0.0244。

F1–F6（v1 §1，全部仍真，一行一条）：F1 canonical blob 全部 10 锚同为 a952af0；F2 重算确定性（四份归档重算面全 06998c8，r20 重跑 cmp rc=0）；F3 分歧 diff 恒为同一 471 字节三值 hunk（r12=r17=r20，本会话 cmp）；F4 唯一 repair 输入 blob cf81fa36 自 95460fd 未变、41 行，已提交输入下工具说 1/38；F5 face 末触笔 fa879e4，早于案发——face 到货即陈旧；F6 台 resolve 0a0a9c43 落了案的证据面、没动 face。定因把 F4 的「无已提交状态可出 3/46」从张力升级为普查证明（§4.2 证三）。

## 2. 时间线 T0–T6（v1 §2 原样保留；下为忠实转写，措辞以 v1 为准）

锚链（逐环 merge-base --is-ancestor YES、rev-list 计数如下；R2-39 记录）：
f1b6e27 ->(+2)-> 3e18590 ->(+2)-> 6998c40 ->(+1)-> 3a56b85 ->(+10)-> c48a548 ->(+8)-> 0a0a9c43 ->(+3)-> 8502146；f1b6e27..8502146 = 26 commits；c48a548..8502146 = 11；fa879e4 是 f1b6e27 之祖（6 commits）。

| # | 时间（UTC） | 锚 | 发生了什么 | 批次戳 / 提案行 | diff 形状 |
|---|---|---|---|---|---|
| T0 | 2026-11-19 22:13:39Z（批次）；行 1 ts 22:17:23Z | f1b6e27（3 样之 1） | 发现。克隆 /Users/zuguangzhao/rocqwash 内 f1b6e27 首次取样；b-gate 重算与已提交面字节同，scheduling-feedback 分歧；按 fail-loud 记录，当时不断言原因 | R1 批 20261119T221339Z；提案行 1 | git diff 恰为三值变化（行 1 证据；blob 对同 F1+F2） |
| T1 | 2026-11-19 23:00:26Z；行 2 ts 23:02:10Z | f1b6e27（3 样之 2） | 第二次独立复现，第二批；同三值；b-gate 仍字节同 | R2 批 20261119T230026Z；提案行 2 | 同三值变化（行 2 证据） |
| T2 | 2026-11-19 23:29:08Z；行 3 ts 23:30:00Z | f1b6e27（3 样之 3） | 第三次独立复现；已提交 vs 重算以 blob 级 cmp 核对（git show HEAD:docs/b-gate-audit.json 输出送 cmp） | R3 批 20261119T232908Z；提案行 3 | 同三值变化（行 3 证据） |
| T3 | 2026-11-19 23:46:22Z；行 4 ts 23:46:58Z | 3e18590 | 首次跨锚取样，PR#17 automerge 后新锚首测；分歧扛过锚移；exp-ledger 在 HEAD 与 fa879e4 各 41 行 →「未提交账态」假设入档（当时不断言为结论） | R4 批 20261119T234622Z；提案行 4 | 同三值 hunk 逐字引于 r4-plan-run.log 第 7 步；归档重算面哈希 06998c8（R2-39 会话） |
| T4 | 2026-11-20 14:16:31Z；行 15 ts 14:18:05Z | 6998c40（如标；见 caveat） | 「6998c40」标签下第四次取样。Caveat（账 9.7 注 3，F1 证实）：从未有工具在 6998c40 上跑过；tip 已 +1，读锚实为 3a56b85（= 6998c40+1）；6998c40 本身只出已提交面核（canonical blob 与值由 R2-39 会话在 6998c40 重钉）。本分歧首次改用 rocqwash-loop 克隆；提案升级为「重算并落新面」 | R2-20 批 20261120T141631Z；提案行 15；档案 r12-anchor-3a56b85-20261120T141631Z/ | r12-divergence.diff，471 字节，index a952af0..06998c8（本会话 cmp） |
| T5 | 2026-11-20 16:51:50Z；行 20 ts 16:56:15Z | c48a548 | 第五次取样，第三个独立锚目睹同一 blob 对（继 0765d671、3a56b85）；fetch 走完整 NETRED 通路（30s 低速中止 rc=128，120s 退避，HTTP/1.1 重试 rc=0）；提案加入流程诉求：面与其输入 blob sha 键控的 sync guard | R2-26 批 20261120T165150Z；提案行 20；档案 r17-anchor-c48a548-20261120T165150Z/ | r17-divergence.diff == r12-divergence.diff，471 字节，index a952af0..06998c8（本会话 cmp） |
| T6 | 2026-11-20 19:19:30Z；行 21 ts 19:24:17Z | 8502146 | 第六次取样，台 resolve 0a0a9c43 之后首次；分歧扛过台动作；行 21 原话：这张面挺过了三任读席与一次台 resolve，仍是陈旧的；提案不变（常设重算 + sync guard，行 21 称其已过期） | R2-36 批 20261120T191930Z；提案行 21；档案 r20-20261120T191930Z/ | r20-divergence.diff == r17 == r12，471 字节，index a952af0..06998c8（本会话 cmp） |

Context rows（非编号取样槽）：

| # | 时间 | 事件 | 证据 |
|---|---|---|---|
| C0（v2 新增·先于 T0） | 2026-11-19T17:40:19Z（fa879e4 adate 2026-11-20T01:40:19+08:00） | 出生笔 fa879e4。face a952af0 诞生于一次开发笔：同笔重写工具 v1.0→v1.1.0（calibration 接线、快照 EOL 规整），14 路径无一 ledger；pre-image 432094a6 的值恰为 1/38/0.0244（重算侧值）——这一笔把 face 从「对」改成「错」，输入侧 51 行 dev-tree ledger 未随库 | R2-44 记录（侦察卡 §1/§2）；face 内 diff 432094a6..a952af0 |
| C1（先于 T0） | 2026-11-19 20:45:25Z | 供给道 PR#17 批工件 zgx-out/scheduling-feedback.20261119T204525Z.json 已带重算侧值 1/38/0.0244；automerge 3e18590（2026-11-19T21:14:45Z，提交 97c809f 携批）并入 main——案的重算侧先于案的被发现就上了游 | 值由 R2-39 会话重析：git show 97c809f:zgx-out/scheduling-feedback.20261119T204525Z.json → repaired=1 unrecorded=38 rate=0.0244；PR#17 恰触 3 文件、全 zgx-out/（账 §3） |
| C2（T4、T5 之间） | 2026-11-20 15:42:14Z（提案 ts）；r5 批 20261120T153929Z | r5 席读锚 0765d671（3a56b85 与 c48a548 之间，+9 至 c48a548）：加分类规则人工重数（对已提交 41 行按工具动作词表独立分类：1 fix-content、2 watch-only、38 无词表 token——与工具完全吻合）与「到货即陈旧」发现（输入 blob cf81fa36 自 95460fd 未变，95460fd 先于 fa879e4）；标靶更名 stale-scheduling-feedback-face | 提案行 19；blob 同一性与祖先由 R2-39 会话复核（F4） |
| C3（T5、T6 之间） | 0a0a9c43 落笔 2026-11-21T03:03:06+08:00（= 2026-11-20T19:03:06Z），早 T6 批次戳 16 分钟 | 台 RESOLVE：落证据道（38 zgx-out 路径：读席批、r12 分歧证据、治理提案、双戳环境快照 204525Z+232908Z）。未触 docs/（§3） | git show --name-only 0a0a9c43：38 路径，0 出 zgx-out/（R2-39 会话） |
| C4（后于 T6） | 当时 tip a4d8d50（2026-11-21T03:30:24+08:00，0a0a9c43 后 4 笔） | 案在 tip 仍开：canonical 面仍 a952af0；已提交提案账 20 行（0a0a9c43、8502146、a4d8d50 三点实测）vs 工作树 21 行——行 21 未提交，与此前每条批行同姿态（账 8 注 4） | git rev-parse a4d8d50:docs/scheduling-feedback.json → a952af0；三笔处行数经 git show 计行（R2-39 会话） |
| C5（v2 新增·后于 T6） | 行 22 ts 2026-11-20T20:55:47Z；行 23 ts 21:22:43Z；侦察卡/回执 2026-11-21 | 定因落档与定因后复测：R2-44 侦察卡+回执交付，提案行 22 追加（根因 + 护栏精确标靶，json.loads 自检 21→22）；随后 r24 批（行 23）在上游新 tip d27af2d 复测——分歧原样（恰 3 行 diff，index a952af0..06998c8），输入 blob cf81fa36 未变，face 末触仍 fa879e4；其间有一次 21:07:49Z 未记档 fetch+checkout（netred_p6.md 披露，见 §6 残三）。R2-48 铸本案卷 v2 | R2-44 回执；行 22/23 本席 §8 核验 |

编号注：关联账的轨迹编号 T0–T7 中，账-T0 = 本档 C1，账-T1..T7 = 本档 T0..T6。本档编号沿用 ask 的取样锚方案，自洽。

同形断言（闭式，v1 原样保留）：对每个取样槽，diff index 必然同名同一 blob 对 a952af0..06998c8——已提交侧因 canonical blob 全锚同（F1），产出侧因每份归档重算面哈希 06998c8（F2），字面 index 行见于三份归档 diff 文件且彼此字节同（F3）。行 23（r24，d27af2d）的复测使该断言延伸到定因后的新上游 tip。

## 3. 台 resolve 0a0a9c43：落了什么、没落什么（v1 §3 保留；开放理由更新为定因版）

resolve 是什么（R2-39 记录）：单亲提交 0a0a9c43d4fc7aa11ba806d4ce2cc4da9375c955（父 a07403e），信息 "chore(zgx-out): land PR#18 content via desk resolve - her planface reading batches at anchors f1b6e27/3e18590/3a56b85/c48a548, r12 divergence evidence, governance proposals, and the dual-stamp environment snapshots (204525Z + 232908Z both preserved); zgx actor namespace (PR#18 resolve)"，committer date 2026-11-21T03:03:06+08:00；8502146 之祖（c48a548→0a0a9c43 = 8；0a0a9c43→8502146 = 3），亦 a4d8d50 之祖（+4）。

落了什么（38 路径，实测，R2-39 记录）：全部 zgx-out/（grep -c . = 38、grep -vc '^zgx-out/' = 0）。R20 工单言「40 items」，提交实载 38（账 10.3 在案；40-vs-38 措辞属落库核验席 R2-35 辖区，非本案）。提案证据道在 0a0a9c43/8502146/a4d8d50 各 20 已提交行——行 1–20 全链上游。双戳环境闭环：environment.20261119T204525Z.txt 与 232908Z.txt 皆在，blob 仅第 3 行戳行异。

没做什么：docs/ 零触——38 路径无一出 zgx-out/；face 末触仍 fa879e4；canonical blob 在 0a0a9c43 与 8502146 仍 a952af0、值 3/46/0.0588（F1）。陈旧面挺过了自己的落库：resolve 把分歧证据收进 zgx-out/ 的同一笔里，证据所描述的那张面在 docs/ 原样陈旧——同一提交。

开放理由（定因版）。案开，不因证据缺、不因读不稳——到 T6 分歧已确定性、输入锚定、字节稳定，跨 7 批/10 锚/26 commits/2 克隆在档。v1 把开放归为证据/动作不对称加「哪面权威」的权限问题；定因后前者照旧，后者半收：R2-44 不替台答「哪面权威」，但把证据面能答的全答了——已提交输入的出生笔忠实产物是重算面（§4.3 反证跑 a，机械事实在案）。于是案只开在一处：

1. 证据面全上游（0a0a9c43 落行 1–20；行 21/22/23 在盘在档，提交姿态见 §9 注 3）。
2. 对象面（blob a952af0）自 fa879e4 起无任何所有者动作在案。
3. 处置（A/B/C 择一、是否追究意图层）是裁决不是证据——读席无权，提案只能荐（行 15/19/20/21/22 皆荐非行）。
4. 管线中没有任何东西重算这张面，没有护栏把它与输入键控，未来每个读席都会重发现分歧——T4/T5/T6 乃至 r24（行 23）正是如此。0a0a9c43 resolve 的是案的记录，不是案。

案态 OPEN，待台一裁（§5 选项间）。

## 4. 根因定谳（新章）

### 4.1 H1 定谳表述（HIGH）

H1：canonical face blob a952af0 恰由一笔写出——fa879e4（"feat(evolution): two closing tickets ..."，作者 168888@live.cn，adate 2026-11-20T01:40:19+08:00 = 2026-11-19T17:40:19Z，单亲 5074eac）。同一笔重写 tools/learning_feedback.py（v1.0→v1.1.0，加 calibration 段），把 face 的 pre-image blob 432094a6——其值 1/38/0.0244，字节级即重算侧值——换成 a952af0（3/46/0.0588）；而 face 唯一 repair 输入 docs/exp-ledger.jsonl 全程停在 blob cf81fa36（41 行，自 95460fd 未变，95460fd 先于 fa879e4）。fa879e4 自己的工具跑自己已提交的输入，产出 blob 06998c8（1/38/0.0244，rc=0，errors=0）——出生笔复现不出自己的已提交面。全引用 ledger 普查恰 4 blob、严格 append-only 前缀链（27→30→38→41 行），无 51 行、无 3×fix-content；两克隆不可达对象、工作树、本机有界扫描皆无缺失态。故：face 由真实工具跑（输出形完整，含 calibration 段）对一份彼时本地的、先于岸账 10 行的 51 行 dev-tree ledger 算出——+2 action=fix-content、+8 无动作词表 token——而只提交了 face。10 行输入从未落任何引用，本机不可恢复。face 到货即陈旧；此后每次重算（含 face 提交 3h05m 后的 zgx 供给批、直至 r24/d27af2d）皆得 06998c8。〔R2-44 记录，证据见 §4.2–§4.3〕

说白了：一笔开发提交把算好的成绩单交了上去，原始答题卡留在了一台没进库的工作树里，后来答题卡丢了。此后全管线拿着成绩单与一份对不上的答题卡反复对账，每轮都发现对不上——缺的从来不是核算，是那 10 行。

### 4.2 三条决定性证据（皆 R2-44 会话执行，命令逐字）

证一·出生点考古。`git log --follow --format='%H|%aI|%cI|%an|%cn|%s' -- docs/scheduling-feedback.json`（两库各跑）。全史克隆恰得两笔：f88fe9af（2026-11-19T06:14:24+08:00，创建；face blob 432094a6，当席析值 1/38/0.0244——即重算侧值；同笔并创工具与 repair-plan-ledger 史）与 fa879e4（2026-11-20T01:40:19+08:00，a952af0 之生；git rev-parse fa879e4:docs/scheduling-feedback.json = a952af0…，fa879e4^: = 432094a6）。此后无任何一笔触碰 face（与 F1/F5 一致）。fa879e4 同笔 14 路径（ci-whitepaper、learning-feedback.md、pin-provenance-v2、scheduling-feedback.json、jargon SPEC+两快照+jargon-map+test_snippet、t_engines_seeds、evolution_dashboard/jargon_map_sync/learning_feedback/pin_repair 四工具）无一 ledger——face 重写搭的是工具功能笔的车，不是账目落库笔。rocqwash 浅克隆之 --follow 只见 3e18590，系 shallow graft 所致（is-shallow-repository=true，.git/shallow 持 2 笔），非第二出生；全史克隆为历史权威。

证二·出生态沙箱重算。`git archive fa879e4 | tar -x -C /tmp/r244-sbx && python3 -I tools/learning_feedback.py` → stdout "repair: repaired=1 escalated=0 watch_only_guard_correct=2 unrecorded=38 repair_action_rate=0.0244"，rc=0，errors: 0；写出面 git hash-object = 06998c8fbbcf3d88087d370fc1556bcb3fce8b08——恰为重算 blob。出生笔用自己已提交的输入复现不出自己已提交的 face；若 H1 假（已提交态已足），此跑当出 a952af0/3/46。/tmp 沙箱属既许例外，临时件查毕即删（§6 残五）。

证三·全引用 ledger 普查。`for c in $(git log --all --format=%H -- docs/exp-ledger.jsonl); do git rev-parse $c:docs/exp-ledger.jsonl; done | sort -u` → 恰 4 blob：

| blob | 首落笔 | 日期（+08:00） | 行数 | fix-content | watch-only | escalated | 无 token |
|---|---|---|---|---|---|---|---|
| ffd36594 | 523e7d4 | 2026-11-14T14:05:03 | 27 | 1 | 0 | 0 | 26 |
| 343fa11d | 70bb8c0 | 2026-11-15T17:00:39 | 30 | 1 | 0 | 0 | 29 |
| 3760669b | a69f370 | 2026-11-17T06:01:12 | 38 | 1 | 2 | 0 | 35 |
| cf81fa36 | 95460fd | 2026-11-19T02:16:45 | 41 | 1 | 2 | 0 | 38 |

严格 append-only 链（旧 blob 是新 blob 的字节前缀，3/3 链 True，当席 python 前缀检）。已提交史任何处无 51 行态：所有引用、所有 tag、所有已取远端分支、本地在场 3 个 PR 头（8b528beb/PR10、918d5f00/PR12、ad4e5d26/PR15，全带 343fa11d）皆无；`git fsck --unreachable --no-reflogs` 两克隆 0 个 ledger 形不可达 blob（rocqwash 41 个不可达 blob 全为合并冲突/文档遗留）；三份工作树 ledger 全 cf81fa36/41 行（f233b26 为第七锚）；有界主机 JSONL 扫描（45–60 行文件 × action=fix-content）零候选。

### 4.3 反证两跑（H1 的两次证伪尝试，均存活）

- 反证跑 (a)「已提交输入配出生期工具，能产出该 face 吗？」——DISPROVEN：即证二。产出 06998c8 而非 a952af0。〔RUN〕
- 反证跑 (b)「存在某个已提交 ledger 状态可出 3/46 吗？」——DISPROVEN：即证三。无任何 blob 51 行；唯一 blob 集是止于 cf81fa36 的严格前缀链。〔RUN〕
- 逆形式如实记：ask 示例测试的逆——「按 H1 预测行集重算应得 3/46」——不可执行：H1 行集不可物化（引用、不可达对象、工作树、主机文件皆无）。记 NOT RUN（不可能），普查结果代位。〔R2-44 在案〕

### 4.4 H2–H6 处置

| 假设 | 内容 | 处置 | 依据（皆 R2-44 记录） |
|---|---|---|---|
| H2 | 出生期工具规则缺陷（=选项 B1 形态） | REFUTED·HIGH | fa879e4 自己的工具跑自己已提交输入得重算 face（反证跑 a）；REPAIR_TOKENS 与 EXP_DEFAULT 出生=当前（工具 91/100–105 行；diff 至 8502146 零触及分类核）；C2 人工重数独立复核（提案行 19） |
| H3 | 外来输入文件（另一份 51 行 JSONL） | LOW·残余 | EXP_DEFAULT 出生即固定 ("docs","exp-ledger.jsonl")（RUN）；有界主机扫描零候选（RUN）。不可完全证伪——已删文件无痕；记残余，不主张 |
| H4 | 手改 face（非工具跑） | LOW·残余 | fa879e4 face diff 新增完全 schema 连贯的 calibration 段（entries 0 / ledger_present true / agreement null），而 cf81fa36 中 calibration_ledger 行数 = 0（RUN）——恰是真实跑对已提交（或不含 calibration 行的 51 行超集）输入的输出形；rounds 面字节未动。手改须凭空造段而 rounds 不动。不可严格证伪；记残余 |
| H5 | 差值行系桌面侧录入、后已补落上游 | 桌面侧来源 HIGH；迟补落 REFUTED·HIGH | 桌面双面追加是本账成例：95460fd 信息（"rows appended in the dev-tree ledger and landed via API git-data"）、a69f370（"union-sync the exp/repair ledgers after the rebase dance (both-side appends)"）。但涉事 10 行从未落 anywhere：普查+fsck+工作树+主机扫描全负（RUN）。10 行是 ghost 行：录在桌面（或暂存某处），从未上船 |
| H6 | 历史重写/未取远端引用藏 51 行笔 | LOW·部分开放 | 无支持证据——严格前缀链普查+fa879e4 的工具笔性格已足以解释现状。残余缺口如实：12 个远端引用未取（单飞 ls-remote 枚举 rc=0；fetch 会改 odb，只读纪律禁止）；本地在场 3 个 PR 头全净。年代学（PR 编号、batch35-20261117、tag 日期）把未取引用置于案窗当时或之后。定因后动态见 §6 残三 |

### 4.5 时间佐证与 ghost 行窗口

差值 10 行构成：+2 行 action=fix-content（repaired 3 vs 1）、+8 行无任何 REPAIR_TOKENS 词表 token（unrecorded 46 vs 38）；watch-only（2）与 escalated（0）不变。时间窗由已提交数据有界：晚于岸账末行 ts 2026-11-18T17:05:56Z（EXP-20261118-0002），早于 face 提交瞬间 2026-11-19T17:40:19Z。精确内容不可恢复（§6 残一）。

佐证：zgx 供给批工件在 2026-11-19T20:45:25Z（face 提交后 3h05m）已带 1/38/0.0244——51 行态在供给道跑时已不在（或从未在）其树中；51 行 dev-tree 态被正面钉住的瞬间恰是 face 提交瞬间。「桌面侧迟补落」之问（ask 原话 houtao ru zhang，R2-44 转述）已答：桌面侧来源 YES、迟补落 NO（§4.4 H5）。〔R2-44 记录〕

## 5. 台侧三选项：定因后的测量后果（决策面交台·禁代裁）

非裁决条款（v1 §4 原样保留，一字未松）：本档不排正确性秩、不表偏好、不收口。案在台裁决前保持 OPEN。定因改变的是各选项的代价与可行性测量，不是谁来做这个选择。

### 选项 A —— 重算并落新 face：机械支持

定因新增支持：重算面是已提交输入的出生笔忠实产物（§4.3 反证跑 a：出生工具 × 已提交输入 = 06998c8，rc=0 errors=0），且自 2026-11-19T20:45:25Z 起就是供给道的 face；家族成例不变（docs/b-gate-audit.json 每锚重算与已提交面字节同，blob 6c823880…，R2-39 会话重钉）。v1 §4 为 A 列的验收门原样有效：新锚重跑 rc=0 errors=0；diff 限 3 个 repair_outcomes 字段、其余字节同；重跑确定性 cmp rc=0；落库笔触 docs/（fa879e4 以来首笔）并携分歧证据引用（行 15/19/20/21/22）；护栏在「账追加而不重跑面」fixture 上实测点火。定因另添一条天然验收：落地 blob 应为 06998c8 或其后代——若不是，说明落地锚的输入已变，须按新输入另行定谳，不得照抄旧值。
在案推荐措辞：行 15/19/20/21（regenerate-and-land），行 22 以定因机制补强。

### 选项 B —— 保 canonical 面、修重算侧：两形皆挫

B1（工具规则缺陷）——反证在案：H2 REFUTED·HIGH（§4.4）。出生工具跑出生输入=重算面；分类核心出生至今零改动；C2 人工重数独立复核。B1 的 discharge 负担（以已提交态演示规则缺陷）目前在案无支持证据，反有两道独立反证。台若仍欲走 B1，须先推翻反证跑 (a) 或 C2 重数——二者皆 RUN 在案；推翻它们是新证据工程，不是重新断言。

B2（交出缺失的 51 行输入态）——就案面而言不可行：R2-44 测量结论原话 measured impossible-on-record。普查证明无任何已提交状态可出 3/46（§4.2 证三）；ghost 行本机不可恢复（§4.2 证三猎取全负）。B2 的 discharge 负担（交出该态或其重建，并演示工具出 3/46/0.0588）以现有案面之物无法满足。唯一理论出路在案面之外：作者另一台机器若仍有彼时工作树——本机档案既不能证明也不能证伪它，须台直接向作者取证。本档如实登记这条出路存在、不在案。

v1 §4 为 B 列的验收门（修正工具或供给输入对已提交态复现 3/46/0.0588、其余面不变、b-gate-audit 与六工具电池无扰）原样保留，供台若辟新路时用。

### 选项 C —— 其余路径（v1 原样，逐条更新）

- C1 只落护栏（不动面）：定因给护栏精确标靶——按输入 blob sha 键控的护栏在 fa879e4 本身就会点火：face 重跑而账未落，恰是「账追加而面未重跑」的镜像形（行 22 语）。但 C1 不解决在案分歧：现有分歧会立刻触护栏，事实上把台推回 A 或 B。
- C2 以「已知态」注记关案：定因后代价更清楚——案卷将同时载「根因已证」与「面保持错值」，且每个未来读席仍会重发现分歧（已 7 批 10 锚，行 23 又添 d27af2d），除非改读协议本身——抑制性改动，代价归台；F2/F4 确定性证据将无调和对留档。
- C3 专席落地/核验包装：适用 A 或 B，改执行人不改断言；本档数字零复用之禁令不变。
- C4 台自定义其他构造。

决策面交台·禁代裁：以上是测量，不是裁决。A 的机械支持不等于 A 正确——「权威」仍可属 B：若台认定 ghost 行才是应然账面，那是意图裁决，须台向作者取证，本档无此权。案 OPEN，候台一裁。

## 6. 残余未知五条（如实）

1. ghost 十行的精确内容（+2 fix-content、+8 无 token；窗 (2026-11-18T17:05:56Z, 2026-11-19T17:40:19Z]）：引用、不可达对象、工作树、本机文件四路皆不可恢复；算术只钉住 token 类计数。对真实行的逆重算 NOT RUN（不可能），普查代位。
2. 持机/持树：提交瞬间握有 51 行态的具体工作树/机器不可判定——在案环境快照全部 host=Darwin/arm64，无从区分。
3. 12 个未取远端引用的内容（H6 残余）：R2-44 会话仅 ls-remote 枚举（rc=0），fetch 被只读纪律禁止，内容未验。定因后动态（本席 §8 核验行 23）：其中 d27af2d 已由一次 21:07:49Z 未记档 fetch+checkout 进 loop 克隆并成为上游 main 顶端（netred_p6.md 披露），r24 批（行 23）在其上复测——分歧原样、输入 blob cf81fa36 未变、face 末触仍 fa879e4；即 12 引用中至少 main 顶端已验且无藏匿。其余引用内容仍未验——低险（年代学在案窗当时或之后）但未证伪，如实保留。
4. 作者意图（ghost 行是否曾拟上船）：从工件不可知。迟补落是账史常态（95460fd/a69f370 信息），「忘了落」是最省俭读法——但省俭不是证据；若台需要意图结论，唯一取证对象是作者本人。
5. sandbox 例外与有界扫描的边界：定谳的决定性重算（反证跑 a）在 /tmp 沙箱例外下执行（/tmp/r244-sbx 及 r244-* 临时件，查毕即删）；在案证据只有捕获 stdout 与出面 blob 06998c8，复核 = 原样重跑两命令。同帧如实记：首轮全_home JSONL 扫描 >120s 被杀、以有界扫描代之——「本机零候选」是有界负，不是穷尽负。

## 7. 复现基座

分歧面基座：v1 §5 全部命令（5.1 提案账完整性、5.2 锚链、5.3 canonical 面普查、5.4 diff 档案字节同、5.5 重算确定性与 blob 重钉、5.6 T0 合并批工件、5.7 resolve 内容、5.8 repair 输入同一性、5.9 读席证据序列）原样有效，逐字以 v1 §5 为准，本档不复抄。〔R2-39 记录〕

定因面新增命令（R2-44 记录，逐字见 §4.2；汇总）：
- 出生点考古：git log --follow --format='%H|%aI|%cI|%an|%cn|%s' -- docs/scheduling-feedback.json（两库）
- 出生态沙箱重算：git archive fa879e4，tar 解至 /tmp/r244-sbx 后 python3 -I tools/learning_feedback.py（/tmp 例外）
- 全引用普查：git log --all --format=%H -- docs/exp-ledger.jsonl 逐笔 rev-parse blob 后 sort -u
- 前缀链核验：逐对字节前缀检查（python，3/3 True）
- 不可达猎取：git fsck --unreachable --no-reflogs（两克隆）
- 工具核心读点：tools/learning_feedback.py 91 行（EXP_DEFAULT）、100–105 行（REPAIR_TOKENS）、256–276 行（compute_repair）
- 远端引用枚举：git ls-remote origin（单飞，仅枚举）

## 8. 本席本场执行的检查（R2-48，逐字）

1. 提案账在盘核验（read-only，/Users/zuguangzhao/rocqwash/zgx-out/zgx-ledger-proposals.jsonl）：
   - `wc -l` → 23（R2-44 回执记其会话 21→22；此后又有追加，见下第 3 条）。
   - `sed -n '22p'` 送 `python3 -I`（json.loads + 字段吐出 + ASCII 断言）→ json OK；ts=2026-11-20T20:55:47Z、actor=zgx、target=docs/scheduling-feedback.json、schema=zgx-proposal/1、ascii_only=True——与 R2-44 回执行 22 记载逐字段吻合，R2-44 的追加确在盘。
   - `tail -n 1`（= 行 23）送 `python3 -I` → json OK；ts=2026-11-20T21:22:43Z、actor=zgx、target=docs/scheduling-feedback.json、kind=proposal、ascii_only=True；evidence 字段记 r24 批 20261120T212043Z：d27af2d 复测（六工具 rc=0；face cmp 差首在 17 行 400 字符；committed sha256 1ed190e1… / produced e66ca0a1…b9c423b 全值；diff 恰 3 行；index a952af0..06998c8；8eff64e..d27af2d = 3 笔且三 docs 路径零触；输入 blob cf81fa36 未变；face 末触 fa879e4）；并披露 21:07:49Z 一次未记档 fetch+checkout（netred_p6.md）。行 23 属 r24 席辖，本档只登记其存在与要点（C5、§6 残三）。
2. 回执 ASCII 自检（write 后执行）：`python3 -I` 断言 ../R2-48-receipt.md 全 ASCII → ascii_only=True。
3. 两份写出文件在盘：ls -l 本档与 ../R2-48-receipt.md。

除此之外本席零检查；一切在案结论皆为转引（页首纪律行）。

## 9. 诚实注记

1. 本席零 git 查询、零网络、零仓树写（写出仅本档+回执）；未复跑任何原席检查——这是本席任务边界（书面铸造），不是遗漏。每条在案结论已标原席（〔R2-39 记录〕〔R2-44 记录〕）；复核通路 = v1 §5 + 侦察卡 §2–4 命令。
2. 中文时间线为 v1 §2 的忠实转写；措辞或数字如有出入，以 v1 英文原文为准，并按经验面纪律报勘误，不静默改写。
3. 行 21/22/23 的提交姿态：R2-39 记录已提交 20 行（0a0a9c43/8502146/a4d8d50 三点）；行 21 未提交；行 22 为 R2-44 追加（本席核验在盘）；行 23 为 r24 追加（本席核验在盘）。三者此刻是否已落上游，本席零 git 未能验——如实记「未验」。
4. 8eff64e 与 d27af2d：R2-44 观察前者为当时上游 main 顶端；行 23 记载后者经 21:07:49Z fetch+checkout 成为顶端并在其上复测。两 SHA 处的事实皆系他人席别记录，本席未独立核验 git 侧——转引如实。
5. 产出面 sha256 全值（e66ca0a1d1b862b6b0554b96d7852ed4b39e239a32f114ba09199fbadb9c423b）本席未复算，转引行 23；v1 诚实注记 6 的「仅 16 位前缀」缺口由此闭合，功劳归 r24 席。
6. 本档不裁决（§5 条款）、不追加任何提案行——案卷席不提案（v1 诚实注记 9 姿态不变）。
7. 本档全部数字溯源：§1–§7 转引页首四源；本席新测仅 §8 三项。

## 10. English summary（non-authoritative; the Chinese main face governs）

**Case.** At every anchor since 2026-11-19 the committed face of docs/scheduling-feedback.json (blob a952af0: repair_outcomes 3/46/0.0588 over "51 rows") disagrees with the deterministic recompute of tools/learning_feedback.py over the same commit's own inputs (blob 06998c8: 1/38/0.0244 over 41 rows) in exactly three values; everything else is byte-identical, and companion docs/b-gate-audit.json recomputes byte-identical everywhere. Total measured delta: 10 rows (+2 repaired, +8 unrecorded; wogc/escalated unchanged) - the "8 lines" framing was the unrecorded delta only (fail-loud correction on record by R2-44).

**Root cause - CONFIRMED, H1, HIGH (R2-44).** The stale face was born in one commit, fa879e4 (2026-11-19T17:40:19Z), which rewrote the tool (v1.0 -> v1.1.0), replaced the face's pre-image 432094a6 (whose values already were the recompute values) with a952af0, and touched no ledger path among its 14 paths: the face was computed by a real tool run against a then-local dev-tree exp-ledger of 51 valid rows (+2 action=fix-content, +8 token-less vs shore cf81fa36/41); only the face was committed. The face was stale on arrival; every recompute since - including the zgx supply batch 3h05m later and the r24 batch at d27af2d - yields 06998c8.

**Three decisive evidences.** (1) Birth archaeology: exactly two commits ever touched the face; the birth commit carried tool+face but no ledger. (2) Birth-state sandbox rerun: the birth commit's own tool over its own committed inputs yields 06998c8 (rc=0, errors 0), not the committed face. (3) All-refs census: exactly 4 ledger blobs in a strict append-only prefix chain (27/30/38/41 rows); no 51-row state exists in any ref, tag, remote branch, local PR head, unreachable object, working tree, or bounded host scan.

**Two falsification runs (H1 survived both).** (a) "committed inputs + birth-era tool can produce the face" - DISPROVEN (rerun yields 06998c8); (b) "some committed ledger state yields 3/46" - DISPROVEN (census). The inverse test over the real ghost rows is NOT RUN - impossible, the rows are unrecoverable; the census stands in its place.

**H2-H6.** H2 birth-era tool-rule defect REFUTED HIGH (this is option B1's form); H3 foreign-input-file LOW residual; H4 hand-edited face LOW residual (coherent new calibration section, zero calibration_ledger rows in the committed ledger); H5 desktop-side origin HIGH / late landing REFUTED HIGH (the 10 rows are ghost rows, never shipped); H6 history-rewrite/unfetched-refs LOW, partially open (12 remote refs enumerated, not fetched at recon time; post-recon, d27af2d has since been fetched and re-read with the divergence intact - proposal line 23; the rest remain unverified).

**Desk options after the verdict - consequences mapped, no adjudication.** Option A (regenerate and land) is mechanically supported: the recompute face is the birth-commit-faithful product of the committed inputs, plus the family precedent (b-gate-audit byte-identical at every anchor); a natural added gate: the landing blob should be 06998c8 or a descendant. Option B1 is counter-evidenced (H2 REFUTED; its discharge burden has no supporting evidence on record - overturning it would take new evidence work, not re-assertion). Option B2 is measured impossible-on-record (no committed state yields 3/46; the ghost rows are unrecoverable) - the only theoretical exit, the author's other machine, lies outside the record and is a matter for the desk to pursue with the author. The sync guard gains a precise target: keyed to input blob shas, it would have fired at fa879e4 itself (face rerun without ledger landing - the mirror shape). Selection remains the desk's; this file ranks nothing and closes nothing.

**Five residual unknowns.** (1) exact ghost-row content; (2) which tree/machine held the 51-row state at the commit instant; (3) contents of the 12 remote refs (d27af2d since fetched and re-read clean per line 23; the rest unverified); (4) author intent - unknowable from artifacts; (5) the evidence's own boundaries: the decisive rerun ran under the /tmp sandbox exception (scratch deleted; verification = re-running the recorded commands), and the "no candidate on this host" result is a bounded-scan negative, not an exhaustive one.

**Status.** Root cause CONFIRMED; case OPEN pending one desk ruling. This file supersedes v1 (R2-39) with the timeline and command base preserved; the casting seat (R2-48) ran zero git queries - every claim is attributed to its seat of record (R2-39 / R2-44 / r24 line 23 / R2-48 fresh checks in Chinese section 8).
