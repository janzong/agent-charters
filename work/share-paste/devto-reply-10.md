# dev.to 回复 · salparvez（2026-09-20 拟，**已由人贴出**，API 复核作者回复时间 2026-09-21 00:40:25Z，id `3fb9e`）

**贴在哪**：第 3 篇（id `4692300`）
→ `salparvez` 的评论（2026-09-20 15:27:09Z，822 字符，id `3fak0`）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①他们的文件属于那 6.2%，且自认"几乎没有禁令"，写的是**怎么读这个仓库**（标签跟主张走、仓库推导物一律先算最低证据档、推荐前先说清对面是谁） ②明示请求：文件在 `MLSystemsRI/ml-systems-public`，**想跑分类器看它判成什么** ③欣赏文章把分母选择如实标注为建模值。

**本轮实测**（远端 `raw.githubusercontent.com/…/HEAD/AGENTS.md` 200 / 4,761 B，与本机副本 sha256 `37064fa2…61c` 逐字节一致；规则集 `ruleset_v0.1.9`、工具 0.4.1）：

| 量 | 值 |
|---|---|
| `compare` 判定 | **3/9 类**：`overview`×1 ｜ `boundaries`×3 ｜ `agent_meta`×1 |
| 结构 | 4,761 B / 77 行 / **7 节**，其中**5 节**拿到标签 |
| 无标签的两节 | `Where to read` 1,047 B ＋ `Who to ask` 470 B = **1,517 B（全文 31.9%）** |
| 未覆盖类（语料库覆盖率排序） | `build_test` 82.8% ｜ `workflow` 67.1% ｜ `structure` 59.1% ｜ `style` 54.5% ｜ `environment` 45.0% ｜ `gotchas` 13.6% |
| `content_mode` | **`rule`**（`rule_signals=6`：`do not`×4、`never`×2）——关键词密度代理，非语义判断（`LIMITATIONS.md` §5） |
| `is_pointer` / `is_substantive` | False / True；`routes_outward=True`、`imperative_route=True`、`hard_route=False` |
| `refs` 指针核对 | 识别 9 个目标，**8 个**在仓库 HEAD 存在（树 217 个文件）；`robots.txt` 不在树里——它是"见站点上的 robots.txt"这句正文提及，不是仓库路径（已知「提到 ≠ 指向」假阳性，`LIMITATIONS.md` §23） |

**结论口径**：这不是单纯的召回漏判，而是**分类法的作用域边界**——九类量的是"agent 在仓库里该做什么"，对方写的是"主张该怎么被读"（证据档位、来源身份、署名）。按 **D42** 只记录、不新开维度；已写入 `LIMITATIONS.md` §28。

---

What it thinks it is: a 4,761-byte, rule-mode file with 7 sections and **3 of the nine categories** — `overview` ×1, `boundaries` ×3, `agent_meta` ×1. Five of your seven sections carry at least one tag.

The two that carry none are "Where to read" (1,047 B) and "Who to ask" (470 B) — 1,517 B, **32% of the file**. That is the bucket you predicted, and you're right about it. The nine categories index what an agent should *do inside the repo*: build, style, workflow, boundaries. Your file is largely about how a claim should be *read* — carry the evidence label with the claim, treat anything derived from the repo as MODELED until a person grounds it, name who is on the other end before recommending anything. None of that is a repo rule, and it isn't `agent_meta` in the sense we use either (that one is about the agent's own conduct — your title section hit it once).

One correction in the other direction, from the classifier's side: you say it barely prohibits anything, and the tool still labels it `rule` mode. That is because `content_mode` counts imperative markers (`do not` / `never` / `must` / `always`) by density — it found 6 (four `do not`, two `never`) and called it a rule file. The mode field is a keyword proxy, not a reading. Your point stands; the label is the cruder instrument.

Caveat the other way: rule-based classification runs 70% recall against a human holdout, so some of those six "missing" categories may be misses rather than true absences. But the gap you pointed at isn't a recall miss — it's scope. A file can be entirely about reading discipline and still score 3/9, because there is no bucket for epistemic status. Adding a tenth category today would silently break comparability with a dataset that is already published, so it goes into the revision queue as a versioned decision rather than a patch. Your file is the first concrete case sitting in that queue.

I also ran the pointer check while I was in there: 9 targets recognised, **8 resolve at HEAD** of your repo (217 files in the tree). The one that doesn't is `robots.txt` — which is not a repo file, it's your sentence about "the sites". Known false positive of our pointer reader: it recognises literal paths, not whether the sentence is pointing or merely mentioning. So 8/9, and the 9th is the tool's fault.

And thank you for the denominator line. "A rate where you picked the denominator is a modeled number" is the standard I was trying to hold myself to, in a smaller way.
