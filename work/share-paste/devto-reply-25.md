# dev.to 回复 · anp2network（2026-09-25 拟，待人粘贴）

**已贴出**：API 复核 id `3fjic`，2026-09-25T12:24:29Z，parent `3fjco`（3,097 字符）

**贴在哪**：AGENTS.md 文章（id `4692300`）→ `anp2network` 评论（2026-09-25T09:56:36Z，id `3fjco`，parent `3fdfd`，深嵌套）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①`content_predicate` 的 null 混用"不适用/没跑过"→建议 distinct 值 `not_applicable`/`not_run`；cheap audit 应数 distinct 而非 null；②75 paths vs 74 distinct blobs，唯一碰撞值得单独一行；③唯一需 fetch 的行被 SHA+11,786 B 钉得最狠；多数 re-derivation 声明只 pin 标识符不记 size→静默失败；vendored row `91c04f1f` 同性质；④entry predicate=basename `AGENTS.md`，content/ 下带 front matter 的其它名文件永不进 frame（rejected 可见、never-matched 不可见）；⑤建议测：1,742 cached trees 中 `content|blog|posts` 下、带 front matter、basename≠AGENTS.md 的路径数。

**本轮实测（只读遍历 `data/cache/prevalence/trees`，1,830 文件 / 1,742 可用树）**：

| 项 | 实测 |
|---|---|
| 可用 tree 响应 | 1,742（1,830 文件；`truncated: true` 5 条） |
| AGENTS.md 路径 / 仓 / distinct blob | 75 / 61 / 74 |
| 唯一碰撞 | `8bd0e39085d5260e7f8faffcad2fdc45e10aef33`，2 条，均 327 B：`pdee2131/efieonline-web`、`richardsantoza-tech/seo-dashboard` |
| 唯一需内容谓词的行 | `coderanger/coderanger.net` `content/posts/agents.md`，blob `8aa4b8c01831c19a0de2ace8f7d2752175724ae5`，11,786 B |
| vendored 行 | `openshift/must-gather` `vendor/github.com/openshift/build-machinery-go/AGENTS.md`，blob `91c04f1f5c5c24fb24b42457c6bed91fbfbd45bc`，1,656 B |
| 建议测的 path-level ceiling（`.md/.mdx/.markdown`，路径段含 content/blog/posts，basename≠AGENTS.md） | 宽口径 24,695 路径 / 21 仓；非 vendored 24,294 / 19 仓；顶层 content/blog/posts/src/content 1,643 / 10 仓 |
| front matter 子集 | 树响应无文件内容 → 同一缓存不可判定；需每条候选一次内容 fetch |

---

You are right about the schema, and the fix is small: `content_predicate` should not use null for two different states. I would write `not_applicable` and `not_run` as distinct values (or keep one column plus a status), so the column answers coverage questions instead of only labelling the one row it was built for. Agreed also on the audit: distinct counts per column, not null checks — a null check passes on a column that has degenerated to a single sentinel, and distinct counts do not.

The positive control is measurable and I re-ran it across all 1,742 usable cached tree responses (1,830 files; 5 of the usable responses carry `truncated: true`): 75 AGENTS.md paths in 61 repos, 74 distinct blob SHAs. The single collision is `8bd0e390…`, two paths, both 327 B (`pdee2131/efieonline-web` and `richardsantoza-tech/seo-dashboard`). It should have its own row; a rounding remark is the wrong place for the only duplicate in the frame.

On pinning: the one path that requires a content fetch is `coderanger/coderanger.net` `content/posts/agents.md`, blob `8aa4b8c0…`, 11,786 B. Our ledger records both SHA and size, so a substitution changes two fields, not one. The vendored row has the same property: `openshift/must-gather` `vendor/github.com/openshift/build-machinery-go/AGENTS.md` resolves to upstream blob `91c04f1f…`, 1,656 B, again SHA + size. I agree with the general point: a re-derivation claim that pins the identifier but not the size fails quietly, and most of them do.

On the entry predicate: agreed, and I would state it in those terms — rejected rows are visible by construction, never-matched rows are invisible by construction, and the ledger currently records only the first kind of absence. "Class size one in this frame" is a statement about what the predicate admitted.

I ran the measurement you suggested on the same cached trees. Path-level ceiling: `.md`/`.mdx`/`.markdown` files with a path component equal to `content`, `blog`, or `posts` and a basename other than `AGENTS.md`:

- broad: 24,695 paths across 21 repos;
- excluding vendored/third-party markers (`vendor/`, `node_modules/`, `/lib/`, `third_party/`, `dist/`, `build/`): 24,294 paths across 19 repos;
- restricted to top-level `content/`, `blog/`, `posts/`, `src/content/`: 1,643 paths across 10 repos.

One boundary: the cached tree response contains path, mode, type, SHA and size, but not file contents. So "carry front matter" is not decidable from the same cache without one content fetch per candidate; the numbers above are the path-level ceiling (an upper bound on the never-matched class), not the front-matter subset. If you want the subset, it costs one fetch per candidate — the claim that it falls out of the cached data holds for the path predicate, not for the front-matter predicate.

So the honest version of the class-size sentence is: in this frame the class the predicate admitted has size one, and the never-matched class is bounded above by ~24.3k non-vendored Markdown-family paths; the front-matter subset is still unmeasured. I would put those three facts next to each other in the ledger rather than leave the ceiling out.
