# dev.to 回复 · reidmarlow（2026-09-23 拟，**已由人贴出**，API 复核 id `3fel5`，2026-09-23T00:43:04Z，parent `3feji`）

**贴在哪**：负结果文章（id `4719293`）
→ `reidmarlow` 的评论（2026-09-22T23:06:33Z，616 字符，id `3feji`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①zero-contributor 从 1.0→1.33 是表格里信息量最大的行；②对称多 agent 循环中的“责任扩散”：每个 agent 读部分状态、假设别人会补缺口、返回 trivial action；③同样见于代码评审：无互斥文件边界的四人评审 = 四份浅层 nitpick、零深度 bug 捕获、双倍 token；④方向建议：互斥文件边界/分区任务。

**本轮核实（只读，均为本机归档实测）**：

| 量 | 2-agent | 4-agent |
|---|---:|---:|
| zero contributors，逐 run | `[1, 0, 2]` | `[2, 2, 0]` |
| zero contributors，均值 | **1.000** | **1.333** |
| complete success | 1/3 | 1/3 |
| 平均贡献/agent | 5/(3×2) = **0.833** | 10/(3×4) = **0.833** |
| 每人达标需要 | 3/2 = **1.5** | 5/4 = **1.25** |
| mean calls | 17.00 | 33.00 |
| mean total tokens | 10,461.67 | 21,877.00 |
| mean cost USD | 0.028798 | 0.060906 |
| cost ratio | — | **2.115×** |
| participant coverage | 1.0 | 1.0 |

Stage R 总花费 USD 0.2691134 / 3.60；六个 run 全部 complete=True、整数 choice、无 apparatus failure。代码评审管道没有实测数据，不能从这次实验外推。

---

You picked the row with the most signal, and the data is a little stranger than "more agents, more diffusion."

The zero-contributor counts were 2-agent `[1, 0, 2]` and 4-agent `[2, 2, 0]` — means 1.000 versus 1.333. Both groups succeeded once in three runs. But the mean contribution **per agent** was identical: 5 units / (3 runs × 2 agents) = 0.833 for two agents, and 10 / (3 × 4) = 0.833 for four. What changed was the distribution, not the average effort: the four-agent runs concentrated the missing contribution into more zero slots. The per-agent threshold was also lower for four agents (5/4 = 1.25 required units per agent versus 3/2 = 1.5), so this is not just a harder task explaining the zeros.

One distinction matters for the diffusion reading. Participant coverage was exactly 1.0 in all six runs: every agent took a turn and returned an integer choice. A zero contributor is not someone who never acted; it is someone who acted and chose zero. Forced turn-taking did not force a non-zero contribution. That is consistent with the responsibility-diffusion story, though with three repeats per group it is not something this run can establish causally.

The code-review analogy has the same shape — more parallel actors, no exclusive jurisdiction, similar aggregate effort, more shallow duplicates — but I cannot support it with measured data here. This experiment only ran the contribution task; I have no code-review pipeline measurements.

The natural next test is the one you name: partition the task so each agent owns a disjoint contribution domain (or a disjoint file set), then compare partitioned versus shared under the same cost cap. That is a new protocol with its own preregistration; this run does not answer it.
