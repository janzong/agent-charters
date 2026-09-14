# dev.to 回复 · alexshev（2026-09-14，**待人贴**）

**贴在哪**：<https://dev.to/janzong/i-looked-at-558-agentsmd-files-heres-a-5-minute-check-for-yours-5cih>
→ `alexshev` 那条评论（13:35:35Z）右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**对方原文（309 字符）**：
> The useful test is whether each instruction changes a decision at the moment it matters. A compact
> "known failure modes" section with trigger, consequence, and recovery path is more actionable than a
> long list of generic cautions—and it gives future agents a reasoned boundary rather than a vague
> prohibition.

**他命中了什么**：他给的判据（"改不改变一次决策"）比我写的 34% 那一条更干净——同一把尺子。
回复目的：①承认他的措辞更好 ②交底"这条我测不了"（规则分类器只数类别）③补一个可查的事实：
语料库里 8 份 9/9 全中的文件，最短的只有 7.7 KB —— 九格填满 ≠ 每一格都能改变一次决策。

---

Agreed, and that is the test my own labeling keeps pointing at. I hand-labelled 120 entries from the Gotchas / Common Pitfalls sections in the corpus: 58% were readable from the repo (contracts, platform limits, build requirements), 34% were generic cautions that would fit any project, and 8% were experience-only. "Changes a decision at the moment it matters" draws that 34% line more cleanly than anything I wrote — a caution that changes no decision is decoration, a failure mode with trigger / consequence / recovery is an instruction.

The awkward half is that I cannot measure it. A rule-based classifier can count sections; it cannot tell whether the paragraph inside one would change a decision. Which is why the number the tool prints is a floor and not a score: the corpus has 8 files that cover all nine categories, and the shortest is 7.7 KB. It names all nine slots — that is not the same as each of them changing a decision.
