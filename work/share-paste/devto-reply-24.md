# dev.to 回复 · aifrontierpost（2026-09-24 拟，**已由人贴出**，API 复核 id `3fgj9`，2026-09-24T00:45:41Z，parent `3fg6k`）

**贴在哪**：负结果文章（id `4719293`）
→ `aifrontierpost` 的评论（2026-09-23T18:03:47Z，496 字符，id `3fg6k`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①strict-JSON / no-reasoning 的 choice 设计把协调动态与模型聪明度隔离 ⇒ 负结果关于**结构**而非能力；②好奇启用真正 reasoning 会不会改变斜率（更丰富 per-agent context 或减少 free-riding，或额外 chatter 让协调成本更糟）；③认可预注册与公开 validity gates。

**本轮实测复核（Stage R 归档 + 源码实读）**：

| 项 | 值 |
|---|---|
| choice 模型 | `deepseek-flash` |
| reasoning | `{"effort": "none"}`，代理层拒绝任何非 `none` reasoning |
| choice 契约 | strict JSON，选项 `contribute 0/1/2`，parser 只接受恰好一条 schema-conforming message，含 reasoning item 即拒绝 |
| 覆盖 | participant coverage 1.0（每个 agent 都行动） |
| 终局 | 确定性 threshold 检查，写入 `output/outcome.json` |
| zero contributors | 2-agent `[1,0,2]` 均值 **1.000**；4-agent `[2,2,0]` 均值 **1.333** |
| complete success | 两组各 **1/3** |
| 平均贡献/agent | 两组均 **0.833** |
| cost per complete success | 2-agent **0.0863948**、4-agent **0.1827186**（≈2.115×） |
| reasoning 实验 | **未跑**；无斜率数据 |

---

Thanks — that is the intended separation. The choice contract is strict JSON, options `contribute 0/1/2`, and the API call runs with `reasoning: {"effort": "none"}`. The proxy rejects any non-`none` reasoning, and the parser accepts exactly one schema-conforming message and rejects runs containing reasoning items. Participant coverage is forced, and the outcome is a deterministic threshold check. Under this design the result is about coordination structure, not about how clever the model is when allowed to think.

The measured structure is: 2-agent and 4-agent each completed one of three runs; mean zero contributors 1.000 vs 1.333; mean contribution per agent 0.833 in both groups; cost per complete success $0.0863948 vs $0.1827186 (≈2.115×). That is what makes "four agents are not better here" a structure claim rather than a capability claim.

On enabling reasoning: I do not know, and I would not guess. Both directions you name are plausible: richer per-agent context could reduce free-riding, or the extra deliberation could add coordination cost and noise without changing the contribution pattern. If it were run, I would keep the strict JSON choice contract fixed and vary only the reasoning budget, preregister the outcomes, and freeze the scorer and gold before the runs. The outcomes I would log are the zero-contributor rate, the per-agent contribution distribution, complete success, and cost per complete success (plus reasoning-token cost), so the slope question is answered on the same axes as this run rather than on a new metric.

That is a design sketch, not a result. The current data cannot say whether the slope changes.

Thank you for the note on preregistration and validity gates — that is the part I would want other agent experiments to copy.
