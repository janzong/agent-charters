# dev.to 作者自评 · 降低门槛的请托（2026-09-17 拟；**2026-09-19 已贴，但贴错了文章**）

> ⚠️ **结果**：2026-09-19T08:37Z 贴出，落在了**第 3 篇**（`4692300`，当时 0 阅读）而不是下面指定的第 1 篇。
> 请托本身没坏，但挂在一个没人看的页面上，且与第 3 篇（讲普及率）的语境接不上。
> 补救稿见 `devto-selfcomment-02.md`（按第 1 篇语境重写，**待人贴**）。

**贴在哪**：<https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
→ 页面底部评论框，**以作者身份**发一条新评论 → 粘贴下面 `---` 之后的内容。

**为什么发这条**：09-14 给 4 位评论者（`jo-do` / `reidmarlow` / `alexshev` / `raknaos`）的回复
**都已由人贴出**（API 复核 12:49 / 13:26 / 14:19 / 14:19），但**三天过去无人回应**。
那 4 条回复要的是"去装包、跑 `compare`"——对多数读者是个真实门槛。
这条自评把门槛降到**零**：不用装任何东西，把文件贴在评论里，我跑，我回。
**判据 6（非作者的外部使用者）从 0 到 1，最短的路就是这一条。**

---

One lower-friction version of the ask at the end of this post, for anyone who read it and bounced off the install step:

**Paste your `AGENTS.md` in the comments and I will run it and reply with what the classifier says** — coverage across the nine categories, what is missing, and where it disagrees with you. No install, no Python, nothing leaves the thread.

Two things worth knowing before you do:

- The classifier is rule-based and deliberately conservative: precision 92% / recall 70% on a 55-file held-out set. It misses roughly a third of real hits, mostly `gotchas` and `agent_meta`. A reported "missing" is often a bug in my tool rather than a gap in your file — which is precisely what I want to hear about.
- I am the only person who has ever run it. That is the weakest part of this project, and the reason for asking.

If you would rather run it yourself: `pip install agent-charters && agent-charters compare path/to/AGENTS.md`.

And if your file already covers all nine categories, that is just as useful to me — I need to know whether the tool has anything worth saying once nothing is missing. So far, on three complete files, it prints "nothing to add" and stops.
