# dev.to 回复 · hannune (Tae Kim)（2026-09-23 拟，待人粘贴）

**贴在哪**：负结果文章（id `4719293`）
→ `hannune` 的评论（2026-09-23T01:07:49Z，255 字符，id `3felf`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①他跑过 3-agent 协调任务，多出来的那个基本只是复述前两者的结论；②问 zero-contributor 是“同几个 agent 一贯缺席”，还是“跨 run 轮换”。

**本轮实测（只读，来自 k98 的 6 个 run 归档）**：

| 组 | agent | 逐 run 贡献 | zero 次数 | 合计 | 均值 |
|---|---|---:|---:|---:|---:|
| 2-agent | Alice | `[0, 1, 0]` | 2 / 3 | 1 | 0.333 |
| 2-agent | Bob | `[2, 2, 0]` | 1 / 3 | 4 | 1.333 |
| 4-agent | Alice | `[0, 1, 2]` | 1 / 3 | 3 | 1.000 |
| 4-agent | Bob | `[1, 1, 1]` | 0 / 3 | 3 | 1.000 |
| 4-agent | Carmen | `[0, 0, 1]` | 2 / 3 | 1 | 0.333 |
| 4-agent | Dan | `[2, 0, 1]` | 1 / 3 | 3 | 1.000 |

结论：缺席者身份**跨 run 轮换**，不是固定同一人；样本内最接近“一贯缺席”的是 2-agent 的 Alice 与 4-agent 的 Carmen（各 2/3）。n=3，且各 agent 目标不同，无法区分 persona 效应与采样噪声。没有 3-agent 条件，无法验证“多出的 agent 只复述”这一点。

---

Direct answer: identity-level data exists, and the absentees rotated rather than staying fixed — with a little persistence at this sample size.

By agent, across the three repeats per group:

- 2-agent: Alice `[0, 1, 0]` (zero in 2 of 3), Bob `[2, 2, 0]` (1 of 3).
- 4-agent: Alice `[0, 1, 2]` (1 of 3), Bob `[1, 1, 1]` (0 of 3), Carmen `[0, 0, 1]` (2 of 3), Dan `[2, 0, 1]` (1 of 3).

No agent sat out every run; the zero slot moved. The closest thing to persistence is Alice in the 2-agent group and Carmen in the 4-agent group, each zero in two of three runs. With three repeats per group, and with fixed personas that carry different goals, I cannot separate persona-specific behaviour from sampling noise.

On your 3-agent echo observation: there is no 3-agent condition in this run, so I cannot confirm or deny it here. Your description is consistent with a coordination bottleneck where the third agent adds no independent action, but that is not measured in this data.
