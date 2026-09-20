# dev.to 回复 · frankchu（2026-09-20 **已由人贴出 09:38 CST**；API 复核 09:41 CST，上线评论 id `3fa0i`）

**贴在哪**：第 3 篇（id `4692300`）
→ `frankchu` 的评论（2026-09-19 17:29:42Z，773 字符，id `3f9ff`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认可丢掉前两篇分母的做法 ②自查自己那份：16,230 字符 / 约 3,281 tokens / 10 节 / 4 个带日期标题，原因是"只增不删" ③真实代价：一条 stale 行让 agent 自信地讲早已自动化的手工流程 ④问：有没有**外部信号**能区分活文件与"活仓库里的死内容"；他判断后者更大也更危险。

**本轮实测（`work/active_stale_check.py`）**：随包 `commit_date` 实测 == `repo_pushed_at`（558/558），不能当文件修改时间用；改取文件级 `history(path=AGENTS.md, until=快照日)` 重算（556/558 可解析）。523 个 ≤90 天有推送的仓库里，AGENTS.md >180 天未动 **52（9.9%）**、>90 天 113（21.6%）、>365 天 4（0.8%）；>90 天未推的仓库仅 33 个 —— 两个阈值下"活仓库死内容"桶都更大。信号对比：带日期标题 0.7% vs 1.9%（p=0.38，无区分力）；copy-paste 重复 2.4% vs 23.1%、knowledge 模式 14.1% vs 48.1%、空壳 2.7% vs 30.8%、指向外部 58.0% vs 25.0%（live 410 / stale 52，未做多重比较校正）。

---

Short answer: yes — the file's own last-commit date, against the repo's last push. It is cheap, and the "active repo, dead contents" bucket is not a corner case.

Disclosure first, because it changes what the shipped dataset can answer: `commit_date` in the corpus equals `repo_pushed_at` in 558/558 rows — it records repository HEAD time, not the AGENTS.md blob's last touch. So I fetched file-level history (`history(path="AGENTS.md", until=snapshot day)`) for every repo and re-measured at the 2026-09-10 snapshot (556/558 resolvable; 2 renamed/deleted counted as misses).

Among 523 repos pushed within 90 days:
- >30d since AGENTS.md last changed: 262 (50.1%)
- >90d: 113 (21.6%)
- >180d: 52 (9.9%)
- >365d: 4 (0.8%)

33 repos were idle >90 days, and all of those files are stale by construction. So your second category is bigger than the tombstone bucket at both thresholds: 52 vs 33 (>180d), and 113 vs 33 (>90d).

Your dated-heading habit specifically: too rare to work as a population signal. Only 4 of 462 comparable files carry a year in any heading, and it does not separate live from stale (0.7% vs 1.9%, Fisher p=0.38).

What does separate them (active repos only; live <=90d n=410 vs stale >180d n=52; not corrected for multiple comparisons): copy-paste duplicates 23.1% of stale vs 2.4% of live; knowledge-mode prose 48.1% vs 14.1%; non-substantive stubs 30.8% vs 2.7%; and live files point outward to other docs 58.0% vs 25.0%.

That last line is the actionable one for your failure mode: for a stale line, the trust axis is not recency — it is whether the file's pointers still resolve. `agent-charters refs` checks exactly that (dangling paths), and `compare` gives the nine-category read on your own file.

Caveat: search-selected corpus, so read these shares as this population, not the ecosystem.
