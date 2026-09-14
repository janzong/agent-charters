# dev.to 回复 · jo-do（2026-09-14 **已由人贴出**，API 复核作者回复时间 12:49:28Z）

**贴在哪**：<https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
→ `jo-do` 那条评论右下角的 **Reply** → 粘贴下面 `---` 之后的内容 → 提交。
**为什么不能自动发**：dev.to 评论 API **只读**（见 `SHARE.md` §5.5 实测）；`POST /api/comments` 在真实站上不存在。

**对方原文（484 字符，已读全文）**：
> 85.7% prohibitions and 13.6% gotchas tracks with what I see running a public board used mostly by
> agents: everyone writes down what the agent must not do, almost nobody writes down the one weird
> thing that will actually bite it. The gotchas are the file. An agent can pick up your style from
> three source files; it cannot infer that the migration script deadlocks when two run at once.
> Nice call keeping the classifier rule-based too - for a dataset like this, auditable beats clever.

**回复的目的**：①承认对方把论点说得更准 ②补一条机制解释（不是客套）③借他的场景问出
**判据 6 缺的那一格**——请一个非作者的人跑 `compare`。

---

Thanks — "the gotchas are the file" is the thesis stated better than I managed to state it.

The mechanical reason the number is so low: a gotcha can only be written by someone who has already been bitten by it, and the moment you have been bitten you usually fix the thing instead of writing the sentence down. Style you can pick up from any three files in the repo; "the migration script deadlocks when two run at once" has to be paid for first.

On rule-based vs. clever: deliberate. Every label has to be re-runnable and argueable — when a label disagrees with you, you can point at the pattern that fired and overrule it. A model can't hand you that, and for a dataset other people are supposed to check, auditable beats clever by a wide margin.

An ungrateful ask, since you clearly sit on the corpus I don't: you run a board that agents actually use — would you run `compare` on its AGENTS.md? `agent-charters compare <file>` prints your nine-category coverage against the 558-file baseline and what's missing. I am specifically looking for what it gets wrong on a setup that isn't mine: so far the only person who has ever tested the classifier is its author, and that is the weakest part of the whole thing. Honest numbers: precision 92% / recall 70% on a 55-file held-out set.

Repo: https://github.com/janzong/agent-charters
