# dev.to 回复 · mnemehq（Theo Valmis）（2026-09-25 拟，**待贴**）

**贴在哪**：第 3 篇（id `4692300`）
→ `mnemehq` 的评论（2026-09-25T14:23:52Z，278 字符，id `3fjoa`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：6.2% 很低，说明多数 agent 完全没有 repo 级指令；想知道这些文件里**多少含规则**、**多少只是构建命令**——只有规则类才真正约束行为。

**本轮实测**（本地数据集 `data/processed/agent_charters_v0.5.jsonl`，516 份实质非 pointer 文件；ruleset v0.1.8）：

| 项 | 实测 |
|---|---|
| 有 build/test/run 章节 | 427/516 = **82.8%** |
| 有 boundaries（禁令/边界）章节 | 442/516 = **85.7%** |
| 句子级显式祈使（`imperative_route`） | 251/516 = **48.6%** |
| 句子级硬禁令（`hard_route`） | 77/516 = **14.9%** |
| 只有命令、无 boundaries 章节 | 50/516 = **9.7%** |
| 只有命令、无任何规则类（boundaries/style/workflow/agent_meta） | 14/516 = **2.7%** |
| 有 boundaries、无命令章节 | 65/516 = 12.6% |
| 两者都有 | 377/516 = 73.1% |
| 两者都无 | 24/516 = 4.7% |
| 文件级 mode | rule 374（72.5%）/ mixed 68（13.2%）/ knowledge 74（14.3%） |

口径说明：`categories` 是**标题通道**（章节名），"有规则"= 有谈禁令/边界的章节，不等于每句都可执行；
README 另记 stricter 读法（专门禁令章节）为 45.2%，本轮重算 `imperative_route ∧ boundaries` 为 43.4% —— 两个数都对，问法不同。

---

Good question, and the answer depends on which channel you count. I ran it over the 516 substantive, non-pointer files in the shipped dataset (v0.5 / ruleset v0.1.8; search-selected corpus, so read it as this population, not the ecosystem):

- commands: 427/516 = 82.8% have at least one build/test/run section;
- rules: 442/516 = 85.7% have at least one section about boundaries or prohibitions; if you require a dedicated prohibition section rather than any mention, the documented stricter reading is 45.2%;
- build-only: 50/516 = 9.7% have a build/test section and no boundary section; if you count every rule-ish category (boundaries, style, workflow, agent-meta), only 14/516 = 2.7% are build-only;
- rules but no build section: 65/516 = 12.6%; both: 377/516 = 73.1%; neither: 24/516 = 4.7%.

The channel matters more than the number. The category pass is heading-based, so "has rules" means the file has a section that talks about boundaries — not that every sentence constrains. A sentence-level pass over the same files finds an explicit imperative in 251/516 = 48.6% and a hard prohibition ("never", "must not", "do not") in 77/516 = 14.9%. So the strictest honest statement is: commands are near-universal, explicit prohibitions are the smaller half, and build-only is a small minority (2.7–9.7% depending on how wide you draw "rule").

One more cut from the same dataset: the file-level mode is rule 374/516 = 72.5%, mixed 13.2%, knowledge-only 14.3%. So "no repo-level instructions" is common at the repo level, but when the file exists, commands are near-universal and prohibitions are the smaller half.
