# dev.to 回复 · raknaos（2026-09-14 **已由人贴出**，API 复核作者回复时间 14:19:46Z）

**贴在哪**：<https://dev.to/janzong/i-looked-at-558-agentsmd-files-heres-a-5-minute-check-for-yours-5cih>
→ `raknaos` 那条评论（13:42:27Z，760 字符）右下角 **Reply** → 粘贴下面 `---` 之后的内容。

**他问了两个具体问题**（这是本轮最值钱的一条评论——他真去拿尺子量了自己的文件）：
1. 那份三仓库清单测试，有没有在**已经 9/9 的文件**上跑过，还是只在不及格的样本上？→ **实测回答了**
   （`dbeaver/dbeaver` 7674B、`graykode/abtop` 21544B、`browser-use/browser-use` 38463B 三份 9/9：
   `brief` 只打 `All nine categories covered - nothing to add.`；`compare` 打 9/9）
2. 坑的缺口是"写作习惯"还是"复核习惯"——把复盘当事后必产物的团队，这一格得分更高吗？
   → **用手上唯一能测的代理变量实测回答了**（`hard_route`，见下）

**新增的两个数**（可复算：`.venv/bin/python work/hard_route_gotchas.py`，自测覆盖在 `tests/test_smoke.py`）：
| 分组 | n | 写了 `gotchas` 的比例 |
|---|---|---|
| 指向知识库/规则目录（`hard_route=True`） | 77 | **24.7%**（19） |
| 其余 | 439 | **11.6%**（51） |

2.12×，Fisher 双尾 **p=0.0037**；按体量四分位分层后四个分位都是前者更高
（Q1 20.0% vs 5.6%｜Q2 10.0% vs 7.3%｜Q3 26.3% vs 13.6%｜Q4 33.3% vs 21.9%），
所以不是"文件大所以覆盖多"能解释的。**边界**：代理变量测的是"指向外部载体"这种写法，
不是"团队有没有复盘制度"；横截面数据，方向未知；有 gotchas 一节 ≠ 里面写的是坑（34% 不是）。

**为什么末尾要再请他跑一次**：他自称有自己的 agent 文件——这正是判据 6 缺的"非作者使用者"。

---

Two good questions, and the honest answer to the first is no.

The three-repo test only ran on files that were already falling short: the human versions scored 6, 5 and 5 of nine categories, and the checklist-generated ones came out at 9/9. I had never pointed it at a complete file until just now. Result: it prints "All nine categories covered — nothing to add" and stops. So the checklist is a floor, not a reviewer. It can name the empty slot; once none are empty it has nothing to say. Your framing — whether an instruction changes a decision — is the reviewer I do not have yet.

One related wart, since you re-read your own gotchas against my ruler: write a file using the checklist's own slot names as headings and my classifier misses `agent_meta`. Five variants tested, the other eight slot names are recognized, that one never is — a file written from my prompt can be reported as 8/9 by my own tool.

On writing habit versus review habit: I cannot see postmortem culture in this data, but there is one proxy I can measure — whether the file points at an external knowledge store or rules directory. Files that do write a gotchas section 24.7% of the time (19/77) against 11.6% (51/439). That is 2.1×, Fisher p ≈ 0.004, and it holds inside every size quartile, so it is not just "bigger files cover more" (the smallest quartile has 5 files with the pointer, so treat that cell as noise). It is a pointer-style proxy, not a postmortem measure, and it is cross-sectional, so I cannot tell you the direction: the pointer and the gotchas section may both come from the same habit of keeping notes outside the code. But of the two hypotheses you offered, it leans process rather than writing style.

Since you offered an outside label: if any of your agent files is public, `agent-charters compare AGENTS.md` on it would tell me something I cannot get from my own machine — the only person who has ever run this classifier is its author. Current held-out numbers are precision 92% / recall 70%, and both kinds of mistakes are useful to hear about.
