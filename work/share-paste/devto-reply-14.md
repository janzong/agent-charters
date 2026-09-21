# dev.to 回复 · glenallen（2026-09-21 拟，待人粘贴）

**贴在哪**：第 3 篇（id `4692300`）
→ `glenallen` 的评论（2026-09-21 09:40:02Z，742 字符，id `3fc13`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①adoption 与 effectiveness 的区分是下一步；②更有价值的是 decision impact：AGENTS.md 使 agent 行为改变的频率，以及这种差异是否避免真实错误；③担心越来越长的说明只是增加上下文而不改善决策。

**本轮核实（只读）**：

| 项 | 值 |
|---|---|
| 评论状态 | 在线；文章共 20 条评论 |
| 既有实验设计 | 前瞻三臂 T / C1 / C2 已预登记 |
| C2 设计 | 等长无关文档，用于剥离“ merely more context ”效应 |
| 主判据 | T vs C2 明写规则违规率差 ≥20pp，bootstrap CI 不跨 0 |
| 次判据 | 返工轮数同向差 ≥0.5 |
| 人工判定 | L2 盲判子集；一致率 <70% 则实验作废 |
| 仪表轨现况（2026-09-21 最新） | 94 个真实任务、35 个任务有章程、113 条适用规则、3 条违规，条目级合规率 97.3%；非随机，不能当因果证据 |
| 正式三臂状态 | 设计稿已预登记但三个执行岔路仍待人裁定，未启动；仪表轨因 97.3% 出现天花板效应，暂不建议直接投入正式实验 |

---

Agreed. I would even separate three levels: presence, use, and effect. This article only measured presence. It did not observe whether an agent read the file, whether the file changed a decision, or whether that change prevented a mistake.

The causal design we have preregistered — but not yet adjudicated or run — has three arms: the actual charter, no attached document, and an equal-length unrelated document. The third arm exists exactly for the risk you describe: if “charter” beats “nothing” but only ties “equal-length unrelated text,” the result is context volume, not charter value. The preregistered outcomes are mechanical rule violations, rework rounds, and a blinded human review of a usability subset rather than self-reported usefulness.

The operational part is running, but it is not yet causal evidence. So far it has recorded 94 real tasks. Only 35 had a repository charter with at least one applicable written rule; those 35 tasks exposed 113 such rules and 3 violations, or 97.3% rule-level compliance, with average rework of 0.41 rounds across all 94 tasks. Because assignment is not randomized and the covered-rule denominator is still thin, I read that as observability and prioritization data, not as evidence that charters improve decisions.

So your “decision impact” framing is the right target. The hard part is observing the counterfactual in normal work: without a paired control, we cannot know whether the same model would have made the same mistake without the file. That is why the next meaningful step is the randomized three-arm comparison rather than collecting more prevalence.
