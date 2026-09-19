# dev.to 回复 · anp2network 第二轮（2026-09-20 拟，**待贴**；贴后把本行改成「已由人贴出」+ API 复核时间）

**贴在哪**：<https://dev.to/janzong/how-common-is-agentsmd-really-i-sampled-github-62-of-active-repos-10-of-all-repos-1175>
→ `anp2network` 的跟进评论（2026-09-19 15:28:09Z，2552 字符，id `3f9ck`，嵌在 `3f948` 下）右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**对方要点**：①`content/posts/agents.md` 不是个案是**类别**——大小写不敏感的 basename 匹配会把"写 agents 的文章"和"写给 agents 的指令"一起数进来，且与被测信号同向；下一级样本量靠人眼分类失效，需要"每个命中由哪条判据收进/拒绝"的书面规则 ②`51/814`（剔截断）假设截断仓与余部同分布——但截断选中的是最宽的树，宽树带 `AGENTS.md` 概率更高；应改报区间 `[51/817, 54/817]` ③若 7MB≈6 万条，则每条 ≈117B、主导项是路径串 ⇒ 深树更早截断，而 `docs/AGENTS.md` 恰在深处——recursive 与 root-only 两口径从两侧挤同一群人；建议缓存上画"返回条目数 × 平均路径长度" ④联合集按 blob SHA 去重：vendored 对是上游文件的**副本**而非第二个决定；问：**51 个命中背后有多少 distinct blob SHA？**

**本轮实测（只读；未改代码）**：

| 量 | 值 |
|---|---|
| 框 A：命中路径 / 命中仓 / distinct SHA | 65 / 51 / **65**（**零重复**——每份都是不同 blob） |
| 框 B：命中路径 / 命中仓 / distinct SHA | 9 / 9 / **8**（唯一重复对：`richardsantoza-tech/seo-dashboard` 与 `pdee2131/efieonline-web` 的根 `AGENTS.md`，同为 327B，SHA `8bd0e390…`） |
| vendored 对的上游核对 | `openshift/must-gather` 的 `vendor/github.com/openshift/build-machinery-go/AGENTS.md` 与上游 `openshift/build-machinery-go/AGENTS.md` @HEAD **同一 blob** `91c04f1f…`（1,656B）——字节级坐实"一个决定、拷贝进场"；但上游仓不在样本内，SHA 去重看不到它 |
| 18 个联合仓的 AGENTS SHA | 18 仓 → **22** 个不同 blob（多文件仓抬升，非拷贝）；**跨仓重复 = 0** |
| 五个截断响应（紧凑序列化） | 42,932–68,555 条、**13.9–17.3MB** ⇒ **252–372 B/条**（117B 估值的 2–3 倍；主导项是 40 位 SHA + 每条 API URL + mode/type/size，不是路径） |
| 条目数 × 平均路径长度 | 全体 1,742 份：**r=+0.303**（符号相反，构成效应）；≥2 万条的 13 仓：**r=−0.019**（近天花板处无可分辨关系） |
| 区间报法 | **采纳**：truncated>0 时对外报 `[51/817, 54/817] = [6.2%, 6.6%]`，宽度摆在明处；`51/814` 退役 |

**上游核对命令**（一次只读调用，未入缓存）：
`gh api repos/openshift/build-machinery-go/contents/AGENTS.md --jq '{sha,size}'`

**待用户裁定的代码改动清单**（本轮未动；正文若承诺"下一次 crawl 逐命中输出 ledger"需你认可，否则删该句）：
1. `work/prevalence.py`：`report`/`report-stock` 补打印 `truncated` 计数（reply-06 遗留）。
2. `work/prevalence.py`：报告输出**逐命中 admission ledger**（路径 / SHA / root|first-party-nested|vendored|content-basename）。
3. root-only 升正式口径并补 `work/` 复算脚本 + 回填 `prevalence.md`/`LIMITATIONS.md`（reply-06 遗留）。

---

Direct answer: **65** — one distinct blob for every matched path. The 51 hit repos carry 65 AGENTS.md paths, and all 65 SHAs are different: zero copies anywhere in the active frame. Stock is the opposite in miniature: 9 hits, 8 distinct SHAs. The duplicate is two 327-byte root files sharing `8bd0e390…` — one template, two repos. That is exactly the copy rate the SHA split exposes. The search-selected corpus is full of identical shells; this random sample is not, which is selection bias showing up in a new place.

The vendored pair, verified to the byte: `openshift/must-gather`'s `vendor/…/build-machinery-go/AGENTS.md` and `openshift/build-machinery-go/AGENTS.md` at HEAD are the same blob, `91c04f1f…`, 1,656 bytes. You are right — that is one decision to ship, copied in by vendoring, not a second one. Within this sample its SHA has no twin (the upstream repo is not a hit), so SHA-dedup alone would not collapse it; the vendored rule does. Among the 18 joint repos there are 22 distinct AGENTS blobs and no cross-repo duplicate.

Bracket: adopted. When truncated > 0, the quoted rate becomes [51/817, 54/817] = [6.2%, 6.6%], with the width in the open. `51/814` retires.

The width arithmetic, measured rather than derived: the five truncated responses carry 42.9k–68.6k entries and 13.9–17.3 MB of compact JSON — so 252–372 bytes per entry, two to three times the 117 B your estimate assumes (and the documented 7 MB evidently binds somewhere else; these bodies are twice that at the truncation point). The dominant fixed terms are the 40-hex SHA and the per-entry API URL, not the path. The depth relation itself is not resolvable in this cache: across all 1,742 responses the correlation between entry count and mean path length is +0.30 — the wrong sign, composition — and among the 13 repos with ≥20k entries it is −0.02. So "truncation eats the nested-placement population first" stays a hypothesis: a good one, but this sample cannot demonstrate it, and I am not writing it down as measured.

The `content/posts/agents.md` point is the one I take most seriously, because it is a class and it correlates with the signal. Written criterion, from this sample onward: root file / first-party nested / vendored dependency / content basename — writing *about* agents versus writing *to* them. The five-way manual ledger is in this thread; having the crawl emit that label per hit is a code change queued behind a repo decision, so I will not claim it is done until it is.
