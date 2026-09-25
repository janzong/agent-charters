# dev.to 回复 · nomad-link-id（2026-09-22 拟，**待贴**；2026-09-25 复核：评论 `3fe82` 仍未被回复，数字已更新）

**贴在哪**：第 3 篇（id `4692300`）
→ `nomad-link-id` 的评论（2026-09-22 15:11:15Z，399 字符，id `3fe82`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①presence 不等于 decision impact；6% 只说明实践存在，不证明文件改变了结果；②应先做三臂检查（charter / nothing / equal-length placebo）再把 prevalence 当作可靠性；③active repo 里的 stale file 是最危险的中间状态。

**本轮核实（只读）**：

| 项 | 值 |
|---|---|
| 评论状态 | 在线；文章共 26 条评论 |
| 框 A prevalence | `AGENTS.md` 51/817 = **6.2%** [4.8, 8.1]；`CLAUDE.md` 44/817 = **5.4%** [4.0, 7.2] |
| 单读漏掉的 active 仓 | 只在 `CLAUDE.md` 26 个；双读并集 77/817 = 9.4% |
| 三臂设计 | 已预登记：T（charter）/ C1（no document）/ C2（equal-length unrelated document）；T vs C2 为主对比；未运行 |
| 仪表轨最新（2026-09-25 重算） | 330 个真实任务；99 个在带章程仓；320 条适用规则；3 条违规 = **99.1%**；任务级违规 2/330；平均返工 **0.224** 轮 |
| 仪表轨限制 | 非随机、无 counterfactual、覆盖分母薄；只能读作 observability，不是 effect |
| stale 中间态 | 523 个 active 仓中，52 个（9.9%）AGENTS.md >180 天未动、113 个（21.6%）>90 天未动；>90 天未推的仓只有 33 个 |

---

Agreed: presence is not effect, and the headline should stay a presence number. In the cached active frame, `AGENTS.md` is 51/817 = 6.2% [4.8, 8.1] and `CLAUDE.md` is 44/817 = 5.4% [4.0, 7.2]; 26 repos carry `CLAUDE.md` only. That is adoption inside this frame, not evidence that any of those files changed an outcome.

The three-arm check is preregistered but not run: the actual charter, no attached document, and an equal-length unrelated document. The primary contrast is charter versus placebo, so the result cannot be explained by simply adding context. Outcomes are mechanical rule violations, rework rounds, and a blinded usability subset.

The non-random operational track has grown, but it still cannot answer the counterfactual: 330 real tasks, 99 in repos with a charter, 320 applicable written rules, and 3 violations, or 99.1% rule-level compliance; 2/330 tasks had a violation and average rework was 0.224 rounds. Assignment is not randomized and the covered-rule denominator is thin, so I read that as observability and prioritization data, not as proof the charter changed decisions.

And agreed on the dangerous middle: an active repo with a stale file. Checking file-level history, 52/523 active repos had an `AGENTS.md` untouched for more than 180 days and 113/523 for more than 90 days, while only 33 repos had gone more than 90 days without a push. The active-but-stale bucket is the larger one at both thresholds. That is why the next meaningful output is the randomized charter-versus-placebo comparison, not more presence data.
