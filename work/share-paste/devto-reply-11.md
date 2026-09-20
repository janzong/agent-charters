# dev.to 回复 · florian131313（2026-09-21 拟，**待贴**；贴后把本行改成「已由人贴出」+ API 复核时间）

**贴在哪**：第 3 篇（id `4692300`）
→ `florian131313` 的评论（2026-09-20 17:37:13Z，293 字符，id `3faof`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认为存量 1.0% 是"墓碑在说话"，决策应看 active rate ②指出 `CLAUDE.md` active 5.4% 与 `AGENTS.md` 6.2% 相邻 ③建议工具**双读两个文件名**，其余视为本地家规。

**本轮核实（只读复算 `work/prevalence.py report`，缓存 seed `20260918`）**：

| 量 | 值 |
|---|---|
| 框 A 样本 | 818 抽样 / 817 棵树可用 / 1 个单仓 403 / 3 棵截断 |
| `AGENTS.md` | 51/817 = **6.2%** [4.8, 8.1] |
| `CLAUDE.md` | 44/817 = **5.4%** [4.0, 7.2] |
| 交叉 | `AGENTS∩CLAUDE` 18 ｜ 只 `CLAUDE` 26 ｜ `P(CLAUDE\|AGENTS)` 35.3% |
| 双读并集 | 77/817 = **9.4%** [7.6, 11.6] |
| 单读 AGENTS 漏掉的 active 仓 | 26/817 = **3.2pp**；相对 51 个 AGENTS 命中多 **51%** |
| 其余格式 | `.github/copilot-instructions.md` 9/817 = 1.1%；`.cursorrules`/`.cursor/rules/*.mdc` 6/817 = 0.7% |

**工具现状（已实测）**：CLI `compare`/`refs` 都接受**多个路径**并合并覆盖；Action 的 `path` 本来就是空格分隔（默认 `AGENTS.md`，可写 `AGENTS.md CLAUDE.md`）；0.4.1 已跟随 `@AGENTS.md`/`Read CLAUDE.md` 这类指针。**不擅自承诺**改默认值或扩语料；是否把 `CLAUDE.md` 纳入正式数据集属版本化决策（D40 曾因 49% 成对一边 <400B、真冲突仅 2.5% 而推后）。

---

Agreed on which number should drive a tool default. Stock answers "how much of everything has this file today"; active answers "what a working project is likely to adopt now." For a detector, active is the right denominator.

I re-ran the cached active frame rather than quoting from memory: `AGENTS.md` 51/817 = 6.2% [4.8, 8.1], `CLAUDE.md` 44/817 = 5.4% [4.0, 7.2]. The intervals overlap, so I would not rank them, but "sits next to" is fair. The cross-table is the part that makes your point concrete: 18 repos have both, and 26 have `CLAUDE.md` only. So single-file detection misses 26/817 = 3.2 percentage points of active repos — 51% more charter-bearing repos than the 51 caught by `AGENTS.md` alone. Dual-reading both gives 77/817 = 9.4% [7.6, 11.6].

On the tool side: `compare` and `refs` already accept multiple paths, and the GitHub Action input is space-separated (`path: AGENTS.md CLAUDE.md`; the default remains `AGENTS.md`). Pointer stubs like `@AGENTS.md` or `Read CLAUDE.md` are followed explicitly. What I would not do silently is fold `CLAUDE.md` into the published corpus: that is a versioned dataset decision, because the fixed 558-repo frame is the comparability guarantee, and the paired-file audit found 49% of pairs with one side under 400 B (pointer/empty-shell territory) and only 2.5% true conflicts in the audited sample.

"Treat the rest as a local house rule" matches the measured drop-off too: `.github/copilot-instructions.md` is 9/817 = 1.1% and Cursor rules 6/817 = 0.7% in this frame. They can still be passed to the tool explicitly; I just would not hard-code every convention into the default yet.
