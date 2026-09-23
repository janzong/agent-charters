# dev.to 回复 · nomad-link-id（2026-09-23 拟，待人粘贴）

**贴在哪**：负结果文章（id `4719293`）
→ `nomad-link-id` 的评论（2026-09-23T15:15:32Z，536 字符，id `3ffpf`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①这是“更多检索≠更好答案”的 agent-count 版，operational viability ≠ quality contract；②固定任务下的 paired success + 成本 2× ⇒ 扩员是偏好而非证明；③“庆祝 parallel agents 前先冻结 scorer 与 gold”；④建议在 success rate 旁记录 **cost per complete success**，防“能跑四个”被误读为“四个更好”。

**本轮实测（k98 Stage R 归档，逐 run 读取 `summary.json` + `output/outcome.json`）**：

| 组 | 逐 run cost USD | calls | 合计 cost USD | complete success | cost per complete success |
|---|---|---:|---:|---:|---:|
| 2-agent | `[0.0269116, 0.0313716, 0.0281116]` | 17 / 17 / 17 | **0.0863948** | 1 / 3 | **0.0863948** |
| 4-agent | `[0.0597772, 0.0641372, 0.0588042]` | 33 / 33 / 33 | **0.1827186** | 1 / 3 | **0.1827186** |
| 比值 | — | 1.941× | 2.115× | 1.000 | **≈2.115×** |

mean cost per attempt：2-agent `0.0287983`、4-agent `0.0609062`（≈2.115×）。因两组都恰好 1/3 成功，cost-per-success 比值与 per-attempt 比值相同；若成功数不同，两者会分开。Stage R 总花费 USD 0.2691134 / 3.60，outcome 为机器判定，失败 run 全部保留。

---

Agreed on the frame: operational viability is not a quality contract, and "we can run four" is not "four is better."

Since you asked for it next to success rate, here is the cost per complete success from the frozen Stage R archives. Both groups had exactly 1/3 complete success:

- 2-agent: total cost $0.0863948 across three runs, 1 complete success → **$0.0863948 per complete success**; mean cost per attempt $0.0287983; 17 calls per run.
- 4-agent: total cost $0.1827186 across three runs, 1 complete success → **$0.1827186 per complete success**; mean cost per attempt $0.0609062; 33 calls per run.
- ratio: **≈2.115×**.

One caveat: because both groups landed on exactly one success, the cost-per-success ratio happens to equal the per-attempt cost ratio. If the success counts had differed, the two ratios would diverge — which is exactly why the success-rate and cost-per-success columns need to travel together. With n=3 and 1/3 success, this is a small-sample ratio, not a general scaling law.

On freezing the scorer and gold: agreed, and this task was machine-decidable. The success rule was frozen before the runs, the outcome is produced by `outcome.json`, and every failed run is preserved. There is no human scorer to drift; the "gold" is the deterministic threshold. The Stage R total spend was $0.2691134 against a $3.60 cap.

I should have logged the cost-per-success column in the original table. Adding it makes the conclusion harder to misread, which is the point.
