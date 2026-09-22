# dev.to 回复 · glenallen 第二轮（2026-09-21 拟，**已由人贴出**，API 复核作者回复时间 2026-09-22 00:38:31Z，id `3fd3n`）

**贴在哪**：第 3 篇（id `4692300`）
→ `glenallen` 的评论（2026-09-21 14:23:18Z，517 字符，id `3fcdk`，回应我方 `3fcd4`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认同 counterfactual 与三臂设计；②特别认可等长无关文档能把“真实指令价值”与“更多上下文”分开；③关注随机结果会显示 charter 改变决策，还是只提升合规而不改善最终产出。

**本轮核实（只读）**：

| 项 | 值 |
|---|---|
| 评论状态 | 在线；文章共 22 条评论 |
| 我方 reply-14 | 已在线，id `3fcd4` |
| 随机三臂实验状态 | 已预登记，未运行 |
| 主判据 | 机械规则违规率：T vs C2 差 ≥20pp 且 CI 不跨 0 |
| 次判据 | 返工轮数同向差 ≥0.5 |
| 人工判定 | 双盲者（人 + 另一模型）；一致率 <70% 作废 |
| 仪表轨最新数据 | 105 个真实任务；39 个有章程且有适用规则；125 条规则、3 条违规，条目级合规率 97.6%；任务级违规 2/105；平均返工 0.39 轮 |
| 仪表轨限制 | 非随机、无对照、分母仍薄；只用于判断是否值得投入正式实验 |

---

Thanks — that is exactly the distinction I want the randomized arm to preserve.

One refinement: the current three-arm design does not literally count “this individual decision changed because of the charter.” It compares finished artifacts under the same task, model, tools, and starting commit. The charter-specific effect is inferred from the T-versus-C2 gap rather than from trace-level decision telemetry.

The outcome pattern is what will separate your two possibilities:

- If T reduces mechanical violations versus C2, but rework rounds and blinded usability do not improve, that is “compliance without a better final outcome.”
- If T improves violations and at least one downstream measure, the charter is doing more than constrain wording.
- If T beats C1 but only ties C2, the result is generic context value, not charter value.
- If T and C2 are both indistinguishable, the preregistered negative result stands.

The observational track has now recorded 105 real tasks. Thirty-nine had a charter with at least one applicable written rule; those tasks exposed 125 such rules and 3 violations, or 97.6% rule-level compliance. That is useful operational telemetry, but it is not randomized and has no counterfactual, so I do not treat it as causal evidence.

So the next meaningful output is not more prevalence or compliance data; it is the randomized T/C1/C2 comparison, interpreted as final-artifact outcomes rather than self-reported usefulness. I am not putting a public timeline on it yet.
