# dev.to 回复 · raknaos（2026-09-19 **已由人贴出**，API 复核作者回复时间 10:15:18Z，id `3f919`）

**贴在哪**：<https://dev.to/janzong/how-common-is-agentsmd-really-i-sampled-github-62-of-active-repos-10-of-all-repos-1175>
→ `raknaos` 那条评论（09:23:47Z，766 字符，id `3f8pj`）右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**对方原文要点**：①认可"把分母挑明"才算测量而不是氛围 ②push：90 天"活跃"是**仓库级**的——
任何原因的 push 都算，会把"CI 天天推、`AGENTS.md` 只是脚手架带出来一次"的仓也数进去
③问：有没有按「**文件在窗口内改过** vs 只是存在」拆过？那能把"在被维护"和"只是被脚手架生成过"分开。

**回复策略**（本轮**不开新测**，只用已发布数字；约束是"只起草"）：
1. 直接答"没拆过"，并把测量层级交底：`pushed_at` 是仓库级；文件判定是 HEAD 的一次递归树调用，
   只有**存在性**、没有历史。
2. 给一条已有数据支持他的方向：存量框 9 个 `AGENTS.md` 命中里 **7 个**在 90 天没 push 的仓里——
   存量命中里"文件在、仓已停"才是众数，所以 6.2% 只能读成"被维护惯例"的**上界**。
3. 指出他的切法比"趋势"便宜：定位加入时间要翻提交历史；"最后一个碰过该文件的 commit"
   是每个命中仓一次路径过滤调用（51 个命中 ≈ 51 次，仓库已缓存）。**没跑，如实说没测。**
4. 预登记两条边界：①bot 每次重新生成文件也会通过这个测试——它分开的是"文本在被维护 vs 脚手架"，
   仍不是"在被使用"；②反方向误差同样存在——一年没改的章程不等于死文件，"常改"和"在用"是两个主张。
5. 收束：这个切法会得到**第三个诚实的数**（"活跃仓里、文件本身在被维护"），应当明显小于 6.2%——
   这不是修正，两个数回答的是不同问题，正是他开头的论点。

**为什么不再请他跑 `compare`**：09-14 的回复（`devto-reply-04.md`）末尾已经请过一次，
同一人短期内重复请托会变成催债；本条专注回答他这一问。

---

No — and your split is the right next cut, so here is exactly what the number does and does not contain.

"Active" is repo-level: `pushed_at` within 90 days, not a fork, not archived. The file check is one recursive tree call at HEAD, so it measures presence, never history. Your mechanism is live in the data: a repo whose CI pushes six times a week counts the same whether its AGENTS.md was scaffolded once and never touched or is edited alongside the code.

One existing result already leans your way. In the unweighted population sample, 7 of the 9 AGENTS.md hits sit in repos that had not been pushed in three months — among stock hits, "file exists, repo idle" is the modal state. That is part of why I read 6.2% as an upper bound on "maintained convention" rather than the convention rate itself.

Your cut is also cheaper than the one I gave up on. Dating when each file was added means walking history; "last commit that touched the file" is one path-filtered commits call per hit — about 51 calls against already-cached repos. I have not run it, so the honest answer today is: unmeasured, mechanism plausible.

If I do run it, two caveats go in before the number:

- A bot that regenerates the file passes the test. It separates maintained text from scaffolded text — better than repo pushes, but still a claim about the text.
- The reverse error is real too. A charter untouched for a year is not necessarily dead: a rule file that agents still read is doing its job, and "edited recently" and "in use" are different claims.

So the split would add a third honest number: active repos where the file itself is under active maintenance. It should land well below 6.2%, and that is not a correction — the two numbers answer different questions, which is the point you started on.
