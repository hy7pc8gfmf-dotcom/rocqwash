# Qed 成本 lint 设计卷（T7·20261126·rocqwash tools/ 候选）

> 来源：外部评估续分析3 真缺口③「forallb/Qed 性能 lint：全仓 forallb 零命中；vm_compute 仅被当证书词面计数」＋账本实证「folded pin 致 Qed 276.5 CPU-s、改写后 0.000s」（EXP-20261124 系）＋内核慢路磨点判例（pose proof+unfold+apply 拆解链把 vm_compute 33 秒的计算型谓词磨成内核层 500+ CPU 秒）。

## 一、判定信号（三源）

| 源 | 取什么 | 判什么 |
|---|---|---|
| 源码面（Proof..Qed 块） | 块行数；块内收尾战术（最后一战术行）；`vm_compute/compute/native_compute/decide` 出现面 | 长块（行数 > 阈值）且收尾非计算型 = 候重 Qed |
| `.glob` 面（结构） | Qed 行的 definition span；依赖链深度（glob 依赖计数） | 跨大 span 的 Qed = 候重 |
| coqc `-time` 日志面（时点） | 每命令墙钟/CPU 秒（`Chars ... - 0.xxx secs` 行） | 实测重命令 = 真信号（其余皆猜测） |

**结论**：源码/glob 两源只能产「候选」；日志面才是判定源。lint v1 = 源码面候选器（零工具链·纯文本）+ 日志面判定器接口（读既有编译日志·不发起编译）——两层同 anchor_guard 的两档自检形。

## 二、误报谱系六型（v1 必须各自有豁免/标注面）

| 型 | 场景 | 为何误报 | v1 处置 |
|---|---|---|---|
| ①vm_compute 收尾 | 计算型证书 Qed | 块长但 Qed 快（字节码旗定律·coqchk -bytecode-compiler yes） | 收尾=vm_compute 族 → 候选降级 |
| ②内核慢路磨点 | unfold 链 Qed | **源码不可见**（33s→500+s 发生在内核层） | v1 明示盲区：源码候选器判不了·日志面才可见（如实登记） |
| ③巨常量单核 | vm_compute 巨常量 | Qed 本体快·编译期重 | 不归 Qed lint（归编译预算票） |
| ④非 Qed 收尾 | Admitted/Defined/Save | 不走 Qed 面 | 块收尾词面过滤 |
| ⑤段/module 上下文 | Section 内 Qed | 行数统计含段变量噪声 | span 用 glob 面（v1 留接口） |
| ⑥转录/生成件 | transcribed/gen 文件 | 噪声源 | `--exclude` 前缀旗+豁免登记面 |

## 三、v1 语义（最小可用骨架）

- `python -I tools/qed_cost_lint.py --file F.v [--threshold N] [--json OUT] | --selftest | --tree DIR`
- 候选 = Proof..Qed 块行数 ≥ threshold（默认 40）且收尾战术不在 fast 集 {vm_compute, compute, native_compute, decide, now, easy, reflexivity}
- 输出 report-only（`rocqwash-qed-cost-lint/1`：{file, blocks:[{qed_line, proof_lines, closure, verdict:"candidate|fast-closure"}], summary}）——**默认零 rc failing**（report-only·与 norm_lint .v 道同款）；`--gate` 才 rc 语义（1=有 candidate·留给接线票）
- 双跑字节恒同；零网络；零工具链

## 四、后继票（登记不执行）

- 日志面判定器（读 coqc -time 日志·真信号）
- `.glob` span 面
- CI 接线票（report-only 先行·gate 后议）
- 阈值校准票（拿 Main repository 63 万行实测分布定价）

## 五、误报对照（本仓判例族）

276.5 CPU-s folded pin 案：源码面候选（块长）✓ 会被抓；改写后 0.000s 案：closure=vm_compute → 降级 ✓ 不误报；内核磨点案：源码盲区（②型）如实登记——**v1 的诚实边界**。
