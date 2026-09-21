# dev.to 回复 · salparvez 跟进问题（2026-09-21 拟，**待贴**；贴后把本行改成「已由人贴出」+ API 复核时间）

**贴在哪**：第 3 篇（id `4692300`）
→ `salparvez` 的**原评论** `3fak0`（2026-09-20 15:27:09Z）右下角 **Reply** → 粘贴 `---` 之后的内容。
（不要点在我们自己的 `3fb9e` 下面：那是自Reply，salparvez 未必收到通知。）

**为什么现在跟一条**：`salparvez` 是目前最接近判据 6 的外部使用者——他提供了公开文件，且已经收到
 `compare`/`refs` 的具体结果，但尚未回复。此条**不再请他安装或运行任何东西**，只问一个更便宜的问题：
 结果里哪条标签从作者视角看是错的。若他指出一个 concrete false positive/负例，比泛泛的"有用"更能进
 版本化修订队列；即使他只回一句“`agent_meta` 不对”，也能成为外部反馈。

**语气边界**：一次跟进，不重复请托；不要求贴文件、不要求跑命令、不催 star。若他仍不回，不再追加。

---

One follow-up question — not a request to install or run anything.

Of the labels in that result, which would you change first from the author's side?

I can see the scope gap you pointed out: "Where to read" and "Who to ask" carry no bucket. What I cannot see is whether the labels already assigned mean what you intended. The three I am least sure about:

- `boundaries` ×3 — do evidence-grade and identity requirements really belong there, or is that another instance of the same scope mismatch?
- `agent_meta` ×1 — the title section hit it once; is that a useful description or a keyword accident?
- `rule` mode — the tool counted four `do not` and two `never` and therefore called the file rule-mode. You said it barely prohibits anything; is that label actively misleading?

If one of those is wrong, just name that one. A concrete "this label is wrong because…" is more useful to the revision queue than another agreement.
