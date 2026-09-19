# dev.to 回复 · anp2network（2026-09-19 **已由人贴出**，API 复核作者回复时间 11:30:18Z，id `3f948`）

**贴在哪**：<https://dev.to/janzong/how-common-is-agentsmd-really-i-sampled-github-62-of-active-repos-10-of-all-repos-1175>
→ `anp2network` 那条评论（11:03:49Z，2170 字符，id `3f932`）右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**对方原文要点**（技术审查级，全部先核实再回）：
1. 递归树 API 会 `truncated: true` 静默截断；只读 `response["tree"]` 的代码会把大仓里
   **真实存在的** `AGENTS.md` 记成没有。漏检与仓库大小相关，817 次抽样不会洗掉；
   要求把约 1,900 个缓存响应里的 `truncated` 数出来打印（"detector 从没响过不等于不存在"）。
2. 大小写不敏感的全路径匹配会把 `vendor/` / `node_modules/` 里第三方依赖自带的
   `AGENTS.md` 数进来——方向相反、同样随树大小走，两者不能假设抵消；
   建议给命中做深度直方图，并对外报 root-only sensitivity band。
3. 子模块在树响应里是 commit 条目、永不展开，属另一类问题。
4. 35.3% 联合率要两个文件都通过同一过滤器，单文件漏检代价 ≈2 倍，且截断漏检同仓不独立
   ——应最后重推。

**本轮实测（只读遍历 `data/cache/prevalence/trees/`，未改任何代码）**：

| 量 | 值 |
|---|---|
| 缓存树文件 / 可判定响应 | 1,830 / **1,742** |
| `truncated: true` 合计 | **5**（框 A 3/817；框 B 2/924） |
| 五个截断仓的返回段里有无命中 | **无**（AGENTS.md / CLAUDE.md 都无） |
| 框 A 三个截断仓返回条目 | 69,373 / 56,185 / 44,985（**7MB 上限先于 10 万条触发**） |
| 框 A 主指标含/剔截断 | 51/817 = 6.24% ｜ 51/814 = 6.27%（audit 文档已发布这一对） |
| `prevalence.py` 检测现状 | `kinds_of` 读 `truncated`；`report`（框 A）**打印计数**；`report-stock` **不打印** → 真实报告缺口 |
| 最坏上界（每个截断仓都藏一份） | 框 A 54/817 = **6.6%**；框 B 11/924 = **1.2%** |
| 框 A 嵌套-only 命中 | 5 仓：3 个 dotfiles 配置（`.codex/`、`agents/codex/global/`、`pi/.pi/agent/`）、1 个 **真 vendored**（`openshift/must-gather` 的 `vendor/github.com/openshift/build-machinery-go/AGENTS.md`）、1 个**博文假阳性**（`content/posts/agents.md`）；`node_modules/` 命中 **0** |
| root-only sensitivity band | 框 A 46/817 = **5.6%** [4.2, 7.4] vs 6.2%；框 B 7/924 = **0.8%** [0.4, 1.6] vs 1.0% |
| 35.3% 联合率的截断影响 | 18 个联合仓里**截断 = 0** → 本样本不受截断影响；但其中 **1 个是 vendored 双文件**（同一依赖同时带两个文件）；root/root 联合 = 13/46 = **28.3%** |
| CLAUDE.md 边际（备查，未进正文） | 44 any → 39 root-only |

**两个"采纳"承诺（是否兑现由用户定；不认可可删正文对应句）**：①`report-stock` 补打印
`truncated` 计数（报告缺口，改的是打印不是测量）；②对外把 root-only 与 recursive 并排报。
若 root-only 要成为正式口径，应补一个 `work/` 复算脚本并回填 `prevalence.md`/`LIMITATIONS.md`
——本轮约束"不擅自扩大改动范围"，未动代码。

---

Counted: **5**, not zero.

Across 1,742 usable cached tree responses (1,830 files; the rest are 404/409 payloads), `truncated: true` appears 5 times — 3 in the active frame (n=817), 2 in stock (n=924). None of the five shows an AGENTS.md or a CLAUDE.md in the returned portion. All three active ones returned 45k–69k entries, so the 7 MB cap fires well before 100k entries on wide trees — worth knowing if you ever eyeball "only 60k entries, surely fine": no.

Where the detector lives: the flag is read, and the active report prints it — the audit write-up published the pair 51/817 = 6.24% including truncated, 51/814 = 6.27% excluding them. You are right about the other half: `report-stock` doesn't print the count. That is a reporting gap rather than a detection gap, and it is on me — I will add it before quoting the stock number again.

Worst-case bound, since "they might hide one" cannot be settled from the cache: if all three truncated active repos each contain a hidden AGENTS.md, the active rate is 54/817 = 6.6%; stock would be 11/924 = 1.2%. So truncation moves these numbers by at most ~0.4pp in this sample.

The vendored direction is live too, and richer than you predicted. Of the 51 active hits, 46 are root files. The five nested-only: three are dotfiles configs (`.codex/`, `agents/codex/global/`, `pi/.pi/agent/`), one is your exact case — a vendored dependency at `vendor/github.com/…/AGENTS.md` — and one is a false positive you did not predict: `content/posts/agents.md`, a blog post caught by case-insensitive filename matching. No `node_modules/` hits in either frame. Root-only sensitivity band:

- active: 46/817 = 5.6% [4.2, 7.4] vs 6.2% [4.8, 8.1]
- stock: 7/924 = 0.8% [0.4, 1.6] vs 1.0% [0.5, 1.8]

I will publish root-only next to recursive from here on — that is a reporting change, no re-crawl needed.

On the 35.3%: none of the 18 joint repos is truncated, so truncation does not touch it in this sample. But one of the 18 is that vendored pair — the same dependency ships both files — and the root/root version is 13/46 = 28.3%. The honest sensitivity on the overlap is therefore 28–35%.

Submodules: agreed, and your framing is the right one. The matcher only looks at `type == "blob"`, so submodule commit entries never expand. That is an under-count direction, and "presence" here means the repo's own tree.
