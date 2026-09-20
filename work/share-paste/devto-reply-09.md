# dev.to 回复 · mthburnsbarberweb（2026-09-20 拟，**待贴**；贴后把本行改成「已由人贴出」+ API 复核时间）

**贴在哪**：第 3 篇（id `4692300`）
→ `mthburnsbarberweb` 的评论（2026-09-19 19:35:48Z，556 字符，id `3f9j4`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认可 stock/active 双口径（"two honest answers to different questions"）②tombstone（7/9 落在未动仓）是文章里最扎眼的数 ③顺着 frankchu 的追问指出：active-but-stale 比 tombstone 更危险 —— 归档仓的失败是静默的，活仓的失败是"自信且错的"；并猜这一类在真实审计中占大头。

**本轮实测（`work/active_stale_check.py`）**：523 个 active 仓库里 52 个（9.9%）AGENTS.md >180 天未动，>90 天未推的仓库只有 33 个 —— 两个阈值下"活仓库死内容"桶都更大（详见 `devto-reply-08.md` 的完整表）。

---

Your guess is measurable in this corpus, and it holds.

The shipped `commit_date` turned out to equal `repo_pushed_at` in 558/558 rows — repository HEAD time, not the file's last touch — so I fetched file-level history for every AGENTS.md instead. At the 2026-09-10 snapshot (556/558 resolvable): among 523 repos pushed within 90 days, 52 (9.9%) had not touched AGENTS.md in >180 days and 4 (0.8%) in >365 days. Total repos idle >90 days: 33. So the active-but-stale bucket is the bigger one at both thresholds — 52 vs 33 at >180d, 113 vs 33 at >90d.

The confident-and-wrong shape also shows up in what stale files contain: they are far more often knowledge-mode prose (48.1% vs 14.1% for live files), copy-paste duplicates (23.1% vs 2.4%), or non-substantive stubs (30.8% vs 2.7%) — while live files point outward to other docs (58.0% vs 25.0%). n=410 live / 52 stale, Fisher p<0.001, not corrected for multiple comparisons. Same caveat as the article: search-selected corpus, so read it as this population rather than the ecosystem.
