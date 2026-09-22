# dev.to 回复 · anp2network 第四轮（2026-09-22 拟，**已由人贴出**，API 复核作者回复时间 2026-09-22 07:43:02Z，id `3fdfd`）

**贴在哪**：第 3 篇（id `4692300`）
→ `anp2network` 的评论（2026-09-22 07:37:01Z，id `3fdf6`，嵌在 `3fbdd` 下）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①disposition 表六列里五列来自 tree response，Label 不是；判 `content/posts/agents.md` 是 2017 年文章需要打开文件，这一步是阅读不是谓词；②因此 6.24%→6.1%→6.0% 依赖唯一一个重跑者无法从缓存重建的列；③“active frame 里只有 1 个”弱于“这个类就是 1”，truncated 有谓词所以能扫 1,742 份，content-basename 目前没有；④所谓“逐行 disposition 可复现”只复现总数；问：**65 个里有几个标签能写成谓词？**

**本轮实测（只读）**：

| 量 | 值 |
|---|---|
| 框 A 命中 | 65 paths / 51 repos / 65 distinct SHAs |
| 可由路径谓词判定 | **64**（root 46；first-party nested 17；vendored 1） |
| 必须走内容谓词 | **1**：`coderanger/coderanger.net` 的 `content/posts/agents.md` |
| 该 blob | `8aa4b8c01831c19a0de2ace8f7d2752175724ae5`，11,786 B |
| 该 blob 内容特征 | 起始 YAML front matter=true；`title:`=true；`date:`=true；标题 7 个；围栏代码块 0 个 |
| **全缓存框**（非只 active） | 1,742 棵可用 tree / 75 个 AGENTS 路径 / 61 仓 / 74 distinct SHA |
| 全缓存框内 content-like 路径 | **仍是 1**，同一 blob ⇒ 这个类在本缓存框内不是“碰巧出现一个"，而是全框 1 个 |
| vendored 可机械化 | `vendor/...` 路径可解析上游仓；本轮 1 条，上游同一 blob `91c04f1f…` |

---

Direct answer: **64 of 65**. Root, first-party nested, and vendored survive as path predicates. Exactly one row does not: `coderanger/coderanger.net`’s `content/posts/agents.md`. No path-only predicate separates “a file of instructions to agents” from “a 2017 post about agents”; that one needs a content gate.

I also widened the count beyond the active sample, because you are right that “one found” is weaker than “class size one.” Across all 1,742 usable cached tree responses — active and stock together — there are 75 AGENTS.md paths, 74 distinct blobs, and exactly **one** content-like path, the same `8aa4b8c01831c19a0de2ace8f7d2752175724ae5` (11,786 B). That is not all of GitHub, but it is the whole cached frame rather than one slice of it. So the honest statement is: in this frame the class size is one and it was found by sweeping; outside the frame it is still unmeasured.

The gate can be written as a predicate, but it is a content predicate, not a path one. The version I would record for this row is: path matches `content|blog|posts`, blob begins with YAML front matter, has both `title:` and `date:`, and is judged by that rule rather than by the reader’s memory. Applied here, it returns false for instruction-file status and the row is counted as `content-basename/rejected`. The open risk is instructions that live under a content directory and carry front matter; I have not measured that false-negative class. That is why the ledger should carry `path_class`, `rule_id`, `content_predicate`, and `counted`, with `content_predicate: null` on the other 64 rows.

Vendored is mechanizable and I would treat it that way: parse the module path from `vendor/...`, fetch the upstream blob, compare SHA. This frame has one vendored row, and the upstream file is the same blob `91c04f1f…`. So of the 65, 64 are deterministic from the tree response and one is deterministic from the tree response plus a blob fetch by SHA and a versioned content rule. A re-runner can reproduce the classification, not just the total — but it still has to run that content gate; it cannot read the answer off the path.
