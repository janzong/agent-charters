# dev.to 回复 · quietlabops（**已作废：目标评论 `3fk0j` 的永久链接返回 404**）

**贴在哪**：第 3 篇（id `4692300`）
→ `quietlabops` 的评论（2026-09-25T15:07:32Z，227 字符，id `3fk0j`，当前最新）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①只列工具的 AGENTS.md 依然会变成 chat pile；②他们的做法是把文件当 "seat file"——named job + one reversible deliverable + explicit STOP；③附外链 `grokbotplaybook.grok.me/`（field-test checklist，轻度自推广）。

**本轮实测**（`data/raw/full/*.md` 全文 + `data/processed/agent_charters_v0.5.jsonl`，516 份实质非 pointer 文件；**正则关键词级**，非语义判定）：

| 信号 | 实测 |
|---|---|
| 显式停止/审批条件（stop / ask before / wait for / escalate / when in doubt） | 174/516 = **33.7%** |
| 命名职责（you are / your role / act as / your job is） | 82/516 = **15.9%** |
| 可逆交付物线索（one small change / reversible / revert / atomic） | 78/516 = **15.1%** |
| build/test/run 命令 | 427/516 = **82.8%** |
| boundaries（禁令/边界）章节 | 442/516 = **85.7%** |
| **只列命令**（build 且无 boundaries/style/workflow/agent_meta） | 14/516 = **2.7%** |
| 上述 14 份里含显式停止/审批语句 | **1/14 = 7.1%** |

口径与限制：关键词级计数，不做语义判定；语料是 search-selected（"存在的文件的总体"，不是"尝试过章程的仓"），因此"只列命令很少见"是选择性结果，不能当因果；外链未访问、不背书。

---

Agreed on the premise: a tool list is not a charter, and the corpus is consistent with that. Over the 516 substantive, non-pointer files (dataset v0.5; keyword-level counts, not semantic ones):

- an explicit stop or approval condition ("stop", "ask before", "wait for", "escalate", "when in doubt"): 174/516 = 33.7%;
- a named job or role statement ("you are", "your role", "act as", "your job is"): 82/516 = 15.9%;
- a deliverable or reversibility cue ("one small change", "reversible", "revert", "atomic"): 78/516 = 15.1%;
- build/test/run commands: 427/516 = 82.8%.

The tool-only slice is the one that speaks to your point: 14/516 files have a build/test section and no boundary, style, workflow, or agent-role section — and exactly one of those 14 carries an explicit stop or approval phrase (1/14). So "only lists tools" is rare in this corpus, but when it happens the seat-file ingredients are almost entirely absent. That is a selection caveat, not a causal claim: this is a search-selected corpus of files that exist, not a sample of repos that attempted a charter.

On the seat-file framing itself: I read it as three separate checks, and the data says they are not automatically correlated. A file can be full of prohibitions (85.7% have a boundaries section) and still never say what the agent's job is or when to stop — the role and stop signals are present in only 15.9% and 33.7% respectively. I have not tested the checklist at grokbotplaybook.grok.me and won't vouch for it; the three things it names are the right three to test, and the numbers above are the baseline I would want it to beat.

> 核查（2026-09-26）：`https://dev.to/quietlabops/comment/3fk0j` → **HTTP 404**，即该评论已被删除/移除；
> 文章页 HTML 也不渲染它（`grep -c 3fk0j` = 0，`comments_sort=latest/top` 均同）。API `comments?a_id=` 仍短暂返回，
> **不能作为"评论还在"的依据**——写回复前先查评论永久链接的状态码。
