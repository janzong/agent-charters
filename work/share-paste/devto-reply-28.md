# dev.to 回复 · mnemehq（Theo Valmis）第二轮（**已修正线程并贴出**；API 复核 id `3flae`，2026-09-26T12:37:21Z，parent `3fkbp`）

> **线程修正已完成**：原错层评论 `3fknd` 已删除；重贴后的 `3flae` 是 `3fkbp` 的直接子节点，会按 dev.to 规则通知被回复作者。

**最终位置**：第 3 篇（id `4692300`）→ `mnemehq` 的跟进评论 `3fkbp` 之下 → 我方回复 `3flae`。

**对方要点**：认可 build-only 2.7–9.7% 与 hard-prohibition 14.9%；观察"多数文件有 boundary 段，但少有工具真正可检查的内容"；问：**禁令里多少指向可检查对象（路径/import 等）vs 泛泛陈述**。

**本轮实测**（`work/boundary_checkability_scan.py`，只读；v0.5，516 份实质非 pointer，390 份有边界句；行级正则，非语义）：

| 桶 | 句数 | 占比 |
|---|---:|---:|
| path（含斜杠的路径 token） | 196 | 11.6% |
| file（带代码扩展名的文件名） | 142 | 8.4% |
| command（git/npm/pytest 等） | 124 | 7.3% |
| import/symbol（import 语句或 `foo()`） | 95 | 5.6% |
| threshold（数字+单位，如 5,000ms） | 1 | 0.1% |
| role（maintainer/owner/@handle） | 43 | 2.5% |
| 纯泛泛陈述 | 1,088 | 64.4% |
| **窄口径可检查**（file+import+command+threshold） | **362** | **21.4%** |
| **宽口径可检查**（再加 path） | **558** | **33.0%** |

文件级：含 ≥1 条窄口径可检查边界 **189/516 = 36.6%**；含 ≥1 条宽口径 **230/516 = 44.6%**；只有泛泛禁令 **150/516 = 29.1%**；有边界句的文件 390/516。

口径与边界：边界句=正则要求"否定义词 + 24 字内动作动词"，**名词式禁令会被漏掉**；"可检查"=句子点名了具体对象，**不等于真有工具能查**；path 桶最松（任何斜杠 token 都算，偶有 `unknown/any` 这类散文）。总句数 1,689。

---

Short answer: mostly no. I cut the boundary lines by whether they name something a checker could resolve — a path, a file, an import or symbol, a command, or a numeric threshold — versus a general statement.

Over the 516 substantive files I found 1,689 boundary lines in 390 files (line-level regex, not semantics; the cue requires a negative plus an action verb, so noun-phrased prohibitions are missed):

- narrow checkable (file, import/symbol, command, threshold): 362/1,689 = **21.4%**;
- broad checkable (adding paths): 558/1,689 = **33.0%**;
- the remaining 1,131/1,689 = **67.0%** are general statements with no resolvable object.

Breakdown, in priority order: path 196 (11.6%), file 142 (8.4%), command 124 (7.3%), import/symbol 95 (5.6%), threshold 1 (0.1%), role or owner 43 (2.5%), general 1,088 (64.4%).

File level: 189/516 files (36.6%) have at least one narrow checkable boundary, 230/516 (44.6%) once paths are included, and 150/516 (29.1%) contain only general prohibitions.

So your read holds numerically: boundary sections are common, but only a minority of the sentences inside them name something a checker could resolve — and when they do, it is usually a path or a filename rather than an import or a threshold. Two caveats: this is a keyword cut on a search-selected corpus, and the path bucket is the loosest by design (it counts any slash token, which occasionally catches prose like `unknown/any`). I would treat roughly a fifth to a third as the honest range for this corpus, not a precise rate.
