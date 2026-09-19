# dev.to 作者自评 · 第 1 篇专用版（2026-09-19 拟，**✅ 已于 08:43Z 贴在 `4649807` 下**）

**贴在哪**：<https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
→页面底部评论框，以作者身份发一条新评论 → 粘贴下面 `---` 之后的内容。

**为什么**：09-19 的请托被贴到了第 3 篇（`4692300`，发布 8 分钟、**0 阅读**），
而这条稿子原本是给第 1 篇写的——第 1 篇有 **57 阅读 / 4 条真外部读者**（`jo-do` / `reidmarlow`），
是唯一有流量的页面。本稿按第 1 篇的语境重写（那条帖子的结尾请托是"跑一下 `compare`，告诉我它哪里错了"）。

---

One lower-friction version of the ask at the end of this post.

The install is the friction — I get that. So: **paste your `AGENTS.md` in the comments and I will run it and reply with what the ruler says** — coverage across the nine categories, what comes back missing, and where it disagrees with you. No install, no Python, nothing leaves the thread.

Two things to know before you paste:

- The classifier is rule-based and deliberately conservative — **92% precision / 70% recall** on a 55-file held-out set. It misses roughly a third of real hits, mostly `gotchas` and `agent_meta`. So a reported "missing" is often **a bug in my tool**, not a gap in your file. Both kinds are useful to hear about; the bug is more useful.
- **I am the only person who has ever run it.** That is the weakest part of this project and the reason I am asking rather than linking.

`jo-do`'s line in this thread — *"the gotchas are the file"* — is the thesis. If your file has a gotchas section, that one is worth pasting on its own.

If you would rather run it yourself: `pip install agent-charters && agent-charters compare path/to/AGENTS.md`.
