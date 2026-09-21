# dev.to 回复 · anp2network 第三轮（2026-09-21 拟，**已由人贴出**，API 复核作者回复时间 2026-09-21 03:22:36Z，id `3fbdd`）

**贴在哪**：第 3 篇（id `4692300`）
→ `anp2network` 的评论（2026-09-21 02:55:21Z，1193 字符，id `3fbc9`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①65/65 只解决“精确复制”，不解决 prose 假阳性；②vendored 上游不在样本内时，SHA 去重无法识别第二次 adoption；③路径分类与字节去重失败位置不同；④应公开 per-path disposition，并明确 content/posts/agents.md 的准入规则与 vendored copy 属于 presence 还是 adoption。

**本轮核实（只读复算 active frame 缓存 seed `20260918`）**：

| 量 | 值 |
|---|---|
| 现行命中 | 65 paths / 51 repos / 65 distinct SHAs |
| Per-path disposition | root 46；first-party nested 17；vendored 1；content-basename 1 |
| 已核实假阳性 | `coderanger/coderanger.net` 的 `content/posts/agents.md` 是 2017 年文章《The Agents Are Coming》，非指令文件 |
| 剔除已知假阳性后 | 64 paths / 50 repos / 64 SHAs = **6.1%** |
| 再剔除 vendored（作为 adoption 口径）后 | 63 paths / 49 repos / 63 SHAs = **6.0%** |
| ledger 可复算性 | tree cache 已含 repo/path/SHA/size/truncated；逐路径 disposition 可离线导出，无需再访问 GitHub |

---

Agreed on the split: classification runs on paths, dedup runs on bytes, and they fail in different places.

The current admission rule is embarrassingly simple: any blob whose path ends in `AGENTS.md`, case-insensitively. That is why `content/posts/agents.md` got in. I checked the one such path in the active frame: it is `coderanger/coderanger.net`’s 2017 post *The Agents Are Coming*, not instructions to agents. So the honest revision is: one known path-level false positive. Excluding it leaves 64 paths across 50 repos, still 64 distinct SHAs. The headline becomes 50/817 = 6.1% presence.

The vendored case needs a second label. In *presence* terms it exists in the sampled repo. In *adoption* terms it is not evidence that the sampled repo made its own instruction-file decision. Excluding both the blog post and the vendored copy gives 63 paths across 49 repos = 6.0% as a conservative “adoption-like” central count. The upstream match is still worth recording, but it should not be silently counted as adoption by the vendor.

The per-path disposition is mechanically reproducible from the cached trees: repo, path, blob SHA, size, truncated, and label. Using the provisional labels:

```text
root               46
first-party nested 17
vendored            1
content-basename    1
total              65
```

“First-party nested” still needs one more pass before I would treat it as final: dotfiles, package subdirectories, and generated trees are all currently in that bucket. A content basename under `content/posts/` should not qualify on name alone. For the next run I would emit the ledger as the primary artifact and keep the headline rate as an aggregate view, not the reproducibility claim.
