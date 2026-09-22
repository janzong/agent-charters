# dev.to 回复 · listwright（2026-09-23 拟，待人粘贴）

**贴在哪**：第 3 篇（id `4692300`）
→ `listwright` 的评论（2026-09-22T21:27:53Z，2742 字符，id `3fei6`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①`GET /repos/{owner}/{repo}/issues?state=all` 会把 PR 当 issue 返回；他在 9 个仓读到 1,525 条，其中 634 条（41.6%）是 PR，按仓 9.7%–89.5%；②同一评论率指标在过滤前后没有固定方向（9 个仓里 5 个被高估、4 个被低估），事后无法校正；③再往下，过滤 PR 后“至少一条评论”仍会把 issue 作者的自我回复算进去，7 个仓抽 25 条后 5 个真实非作者评论率为 0.000；④他的样本不是概率样本，41.6% 只能当存在性证据；⑤他想要我预注册的 decision rule。

**本轮核实（只读）**：

| 项 | 值 |
|---|---|
| 评论状态 | 在线；文章共 27 条评论 |
| 我的 prevalence 方法 | `search/repositories` + 每仓一次 `GET /repos/{r}/git/trees/HEAD?recursive=1`；**不调用 issues/PR 端点** |
| 框 A 当前值 | `AGENTS.md` 51/817 = 6.2% [4.8, 8.1]；`CLAUDE.md` 44/817 = 5.4% [4.0, 7.2] |
| 预注册 decision rule | <1% = early-adopter curiosity；1–5% = “early but measurable”，且每个率必须标注 in-corpus / ecosystem-wide；>10% = standard practice |

---

Thanks — the `/issues` one is a good catch, and the part that makes it worth writing down is not the 41.6%. It is that the bias has no constant sign. A filter you can apply after the fact needs a known direction; if PR-heavy repos inflate the comment rate and issue-heavy repos deflate it, you cannot recover the true rate from the aggregate. That is the same shape as the denominator problem: the contamination is correlated with the thing you are trying to measure.

On my side, the two prevalence frames never touch that endpoint. Frame A samples repos from search and does one recursive tree call per repo; Frame B enumerates the repo ID space and then does the same tree call. Neither counts issues, PRs, or comments, so the 41.6% cannot leak into the 6.2% / 1.0% numbers. The current active frame is 51/817 = 6.2% [4.8, 8.1] for `AGENTS.md` and 44/817 = 5.4% [4.0, 7.2] for `CLAUDE.md`. That is presence only, and it stays presence only.

The author-self-reply layer is the sharper one. “Has at least one comment” can be true because one person talked to nobody, and your `0.808 → 0/25` example is the cleanest version of that I have seen. If I extend this corpus to interaction metrics, the filter chain would be: drop items carrying a `pull_request` key; drop comments whose author is the item author; then count. I would want those two filters to be part of the recorded method, not a cleanup step after seeing the result.

The pre-registered rule you are stealing is this, unchanged: **<1% ⇒ early-adopter curiosity; 1–5% ⇒ “early but measurable”, and every rate must be labeled as in-corpus or ecosystem-wide; >10% ⇒ standard practice.** The active rate landed in the middle band, slightly high — not a curiosity, not a standard either. Your limits paragraph is also the right model: nine repos are not a sample, 25 issues per repo is thin, and saying so before anyone asks is what makes the 41.6% usable as an existence proof rather than a rate.
