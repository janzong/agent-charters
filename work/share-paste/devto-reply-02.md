# dev.to 回复 · reidmarlow（2026-09-14 **已由人贴出**，API 复核作者回复时间 13:26:53Z）

**贴在哪**：<https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
→ `reidmarlow` 那条评论右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**对方原文（564 字符，13:04:20Z）**：
> The % figure for external gotchas matches the friction in multi-agent repos. When an agent fails on
> local code, it usually hits a syntax error or a failing test that it can recover from. When it fails
> on environment drift, like an unpinned CLI tool behaving differently in a subshell or a rate limit on
> an unmocked internal service, it loops until context runs out because the repo itself contains no
> evidence of why the command broke. Putting those edge-case runtime failures into the context file
> saves far more agent turns than repeating standard linting rules.

**他命中了什么**：他描述的"环境漂移"＝我实测的**那 8%**（只能靠经历得知的部分）。
回复的目的：①把 58/34/8 三个桶摊开，指出 `13.6%` 这个数**高估**了真正写下来的经验知识
②补上他说对但我没想清的机制——**自证失败 vs 非自证失败**（前者终止循环，后者让 agent 空转到上下文耗尽）
③问他把这类笔记放在哪（自然引出 `compare`，但不用重复上次那套请求）

---

This is the sharpest version of the distinction I was fumbling toward.

I hand-labeled 120 entries from the `Gotchas` / `Common Pitfalls` sections in the corpus to separate the buckets: 58% were readable from the repo (contracts, platform limits, build requirements), 34% were generic advice that would fit any project, and only 8% were experience-only — the class you are describing. So the 13.6% figure actually *overstates* how much of this knowledge gets written down: the section is rare, and most of what is inside it is not the thing that would have saved the agent.

The asymmetry you point at is the part I had not articulated. A syntax error or a failing test is self-evidencing — it puts the signal into the agent's context, so the loop terminates. Environment drift produces either a plausible wrong answer or a hang, and the repo contains no evidence of why. It is the one failure class the agent cannot self-correct from.

Which is why it can only be written by someone who was there. Do you keep those notes in the repo (an `AGENTS.md`-style file), or somewhere separate?
