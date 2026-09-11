# 对外分享包 SHARE

> 给作者（人）用的发帖文案。**机器发帖会被当 spam，必须你自己发。**
> 这不是数据集的组成部分，发完可以删；留着也行——下次发 v0.2 时能复用结构。
> 文案里的每个数字都可由 `data/processed/agent-charters-v0.2.parquet` 复算。

## 0. 发布前 checklist

- [ ] 链接：`https://github.com/janzong/agent-charters`（Release `v0.2`）
- [ ] 先自己走一遍 README 的 `compare` 例子，评论里有人问细节时要能现场回答
- [ ] 只发你能守得住的量：一次 2 个渠道，隔 3–5 天再发下一批。
      同一天到处贴 = 看起来像推广机器人
- [ ] 准备好接受"这东西有什么用"和"LLM 生成的垃圾数据集"两类质疑（第 5 节）

**建议顺序（2026-09-11 按线路可达性重排，实测见 `ENVIRONMENT.md` §5.1）**

1. ✅ **知乎** —— 已发 2026-09-11（<https://zhuanlan.zhihu.com/p/2081788025013539447>）。链路可达，先用它把硬伤问出来
2. **开源中国**（本文件 §4.5）或掘金 —— **V2EX 在本线路被 SNI 阻断，发不出去**，用这两个顶短帖位
3. 隔 3–5 天再发 **HN** —— 它只是 DNS 污染，**加 hosts 就能发**（`209.216.230.207 news.ycombinator.com`，
   IP 会变、发前复核）；Show HN 只有一次机会，等中文站把问题挖完再上
4. 最后 **Reddit** —— DNS 污染 + SNI 阻断，**必须有代理**；没代理就跳过，别硬排

**时间**：HN 在北京时间 **20:00–23:00**（美东上午）；Reddit 同理。
知乎 / 开源中国 / 掘金在**工作日 10:00–12:00 或 20:00–22:00**。

---

## 1. Show HN（英文）

**标题**

```
Show HN: Dataset of 558 AGENTS.md files – what people actually tell coding agents
```

**正文**

```
I collected 558 AGENTS.md files from public GitHub repos and hand-wrote a rule-based
taxonomy for them (9 categories), then published the annotations. No model was used
to label anything; it's keyword/heading rules, so you can read exactly why any file
got any tag.

Percentages below are over the 511 files that actually contain instructions. Of the
558 collected, 40 are near-empty (<40 bytes) and 7 are pure pointers ("see CLAUDE.md").

Some things that surprised me:

- "How to build/test/run" dominates: 87% of files have build/test content. That's the
  single thing people most want their agent to know.
- Prohibitions come second (65%), ahead of architecture and style. People draw lines
  before they hand over autonomy.
- "Gotchas" is the rarest category at 14% — yet it's the knowledge you can't re-derive
  by reading the code. The most useful thing is the least written.
- 7 files contain no instructions at all, just a pointer: "see CLAUDE.md". Some teams
  have started to split their agent rules across several files.
- 73% of files are imperative (do/don't) rather than declarative knowledge.
- Only 5% are in Chinese, which seems low given GitHub's Chinese-speaking user base.

There's also a small CLI in the repo. The one I actually use:

    agent-charters compare path/to/AGENTS.md

It shows your file against the corpus baseline and tells you which categories you
never wrote about. I wrote it because I kept forgetting to document how to run tests.

What this is not: no full texts are redistributed (annotations + stats only, CC-BY-4.0;
code MIT). Classification is rule-based and not hand-verified per file, so coverage
numbers are lower bounds. Sample skews toward AI/agent-topic repos, so don't read it
as "all of GitHub".

Repo: https://github.com/janzong/agent-charters
Everything is reproducible: file_sha per row, plus retrieved_at, extractor and ruleset
versions. Happy to hear what categories I got wrong — that's the most useful feedback.
```

---

## 2. Reddit（英文）

**发在 r/LocalLLaMA 或 r/ChatGPTCoding**（标题用 `[OC]` 表明原创）

**标题**

```
[OC] I annotated 558 AGENTS.md files from public repos — 87% document build/test commands, only 14% warn about pitfalls
```

**正文**

```
Disclosure: I made this.

I kept writing AGENTS.md files for my own projects and wondering whether I was
missing the obvious. So I pulled 558 of them from public GitHub repos and wrote a
rule-based taxonomy to see what people actually put in these files.

9 categories, 30 fields per row. No LLM was used to label anything — it's heading +
keyword rules, and each row records which ruleset produced it.

Numbers worth a look (511 substantive files):

| category | share |
|---|---|
| build/test/run commands | 87% |
| git/PR/release workflow | 66% |
| prohibitions & boundaries | 65% |
| architecture & file layout | 59% |
| code style | 56% |
| environment & toolchain | 44% |
| AI-specific behavior rules | 36% |
| project overview | 34% |
| pitfalls / gotchas | 14% |

The 14% is the interesting one for me. "Don't use `bun install`, it breaks the
lockfile" is knowledge that no one can recover by reading the code, and it's the
least written-down category.

Also: 73% of files are imperative rather than explanatory, and 7 files are pure
stubs ("see CLAUDE.md"), which suggests some teams are splitting agent rules across
multiple files.

Caveats, because they matter: classification is rule-based, not hand-verified per
file, so treat the percentages as lower bounds. The corpus skews to AI/agent repos.
It's English-heavy (91%); Chinese is 5%, which is a real weakness of the dataset.

There's a CLI included — this is the part I use daily:

    agent-charters compare your/AGENTS.md

It prints your coverage against the baseline and flags what you never mention.

No full texts are redistributed (annotations + stats only). Data CC-BY-4.0, code MIT.

Repo + release: https://github.com/janzong/agent-charters

If you have an AGENTS.md that this taxonomy mislabels, I'd like to see it —
false positives are the ones that actually hurt.
```

**如果发 r/MachineLearning**：先读该版版规（对 self-promo 很敏感）。
那里更适合周更的 `[D]` Discussion 帖，而且**要等有外部分析引用之后再发**。

---

## 3. 知乎（中文长文）

**标题**

```
我把 558 份 AGENTS.md 全抓下来标了一遍：人到底想让 AI 知道什么
```

**正文**

```
有一个新文件正在悄悄进入软件仓库：AGENTS.md、CLAUDE.md、.cursorrules。
它不是给人看的文档，而是人写给 AI 智能体的行为规约。

我给自己的项目写过几份，写的时候总有个疑问：我是不是漏了最要紧的东西？
于是把 GitHub 上能公开拿到的 558 份 AGENTS.md 抓下来（来自 558 个仓库），
做了一次结构化标注，结果和直觉不太一样。

558 份里有 47 份不含实质内容（40 份近乎空文件、7 份只是转发指针），
下面所有百分比都以剩下的 **511 份**为分母。

## 方法：没有用大模型打标

这一点必须先说清楚，因为它决定了结论的可靠边界。

标注是用**规则**做的：先把文件按标题切分，用关键词判定九个类别
（构建测试、流程、禁令、架构、风格、环境、AI 行为规定、项目概览、坑），
再加一个跨语言的强信号通道。之所以不用模型打标：

- 规则可以被逐条审阅，模型打标不能——你要么信，要么做人工抽检
- 规则错了能改，改完还能复算；模型打标的漂移无法追溯
- 数据集里每一行都记着 file_sha、采集日期、抽取器版本、规则集版本，
  任何人在任何一天都能从原始仓库复现同一份数据

代价也很清楚：**关键词法只能识别写进词表的表达**。
它会给覆盖率一个偏低的下界，而且中文表达漏得更多。

## 五个发现

**一、"怎么跑起来"压倒一切（87%）**

构建、测试、运行的命令出现在 87% 的文件里，比第二位（git/PR 流程 66%）
高出一截。（按标签出现次数算，是第二位 git 流程的 2.6 倍。）
人给 AI 写的第一件事非常朴素：告诉它怎么编译、怎么测、怎么跑。

**二、禁令排在很前面（65%）**

一个很显眼的模式：大量文件用整节写"不要做什么"——
`NO FILE DELETION`、`DO NOT EVER`、`Never run cargo build`、
`ONLY use main, NEVER master`。

我的解读是：**人对 AI 的信任不是从授权开始的，是从划线开始的。**
先圈出不可逾越的边界，再谈交给它做什么。

**三、最值钱的知识写得最少（14%）**

"坑"是九类里覆盖率最低的，只有 14%。但这类内容恰恰是无法从代码里反推的：
"Ubuntu 24.04 下起多个服务会因 socket 冲突失败"、"别改 lockfile，`bun install` 会重写它"
—— 这种话只有踩过的人写得出来，读到的人省下的是几个小时。

**最有价值的规约内容，和写得最多的规约内容，几乎完全不重叠。**
这是我做完这份数据后最想继续追的问题。

**四、有一部分文件根本不写内容，只做转发（7 份）**

有些 AGENTS.md 全文只有一句：

    See CLAUDE.md for codebase conventions.

有的团队把规则拆成多个文件，顶层只做分发（COMMANDS.md / ARCHITECTURE.md /
TESTING.md / TROUBLESHOOTING.md）。这说明规约开始被当成工程资产来组织，
而不是一篇随手写的说明。

我还见到一份文件里有"Agent Findings"章节——**AI 开发过程中积累的发现被写回去，
给下一个 AI 看**。规约的方向开始不只是"人 → AI"。

**五、中文项目严重缺席（5%）**

511 份可用于统计的文件里，中文文档只有 26 份。
考虑到中文开发者在 GitHub 上的规模，这个比例低得不像话。
可能的原因有三个：中文项目用 AGENTS.md 的比例确实低、中文规约更爱放在
README/CONTRIBUTING 里、或者中文项目更倾向私有仓库。

我没有证据判断是哪一种，这需要更大范围的采集才能回答。

## 顺手做了个小工具

数据集本身我可以直接发，但我自己最常用的其实是一个对比命令：

    agent-charters compare 你的AGENTS.md

它会把你的文件和 511 份基线对照，输出每个类别的覆盖率、你命中了哪几类，
以及**语料库里写得很多、而你一个字没写的类别**。

写它的原因很实际：我总忘记把"怎么跑测试"写进去，而这是语料库里 87% 的人
都写了的东西。

## 边界（请认真看这段）

- 分类由规则完成，**没有逐份人工校验**。v0.1 时抽样 12 份人工核对的结果是
  准确 9、漏标 3、错标 0（v0.1.1 / v0.1.2 两轮改动未重做核对）——
  方向是"宁可漏标，不做错标"，所以所有覆盖率都是下界
- 候选仓库偏向 AI / agent 话题，**不能代表 GitHub 全体**
- 中文样本仅 5%，任何按语言做的对比都缺统计效力
- 数据集**不含任何原文全文**，只发布标注与统计特征，原文版权归各仓库作者

## 数据和代码

    仓库：https://github.com/janzong/agent-charters
    国内镜像（GitHub 访问不稳时用这个）：https://gitee.com/janzong/agent-charters
    数据集：558 行 × 30 列（parquet / jsonl），代码 MIT，数据 CC-BY-4.0

如果你手上有被它标错的 AGENTS.md，或者你觉得该有第十个类别，
这两类反馈对我最有用——**错标比漏标伤害大得多**。
```

---

## 4. V2EX（中文短贴）

**节点**：程序员 / 分享创造

**标题**

```
[分享] 抓了 558 份 AGENTS.md 做了标注，顺手写了个对比工具
```

**正文**

```
写 AGENTS.md 的时候总怀疑自己漏了要紧的东西，就把 GitHub 上公开的
558 份抓下来做了一次结构化标注（9 类，30 个字段）。

几条比较意外的：

- 87% 的文件写了构建/测试/运行的命令，比第二位（git 流程 66%）高出一截
- "不要做什么"排在很前面（65%）——信任是从划线开始的
- 坑/pitfall 只有 14%，是最低的一类，但这类知识恰恰没法从代码里反推
- 有 7 份文件全文只有一句"见 CLAUDE.md"，纯做转发
- 中文只有 5%，低得不太正常

标注没有用大模型，是关键词+标题规则，每一行都带 file_sha 和规则集版本，
可以复现。代价就是漏标多、覆盖率都是下界，这点我在文档里写清楚了。

另外做了个 CLI，我自己每天用的是这个：

    agent-charters compare 你的AGENTS.md

它会告诉你语料库里写得很多、而你一个字没写的类别。

https://github.com/janzong/agent-charters
国内镜像（打不开 GitHub 时用）：https://gitee.com/janzong/agent-charters

数据集不含原文全文，只有标注和统计。有标错的欢迎拍砖。
```

---

## 4.5 开源中国（中文，项目介绍体）

**为什么单独一版**：OSC 的读者是开源/开发者，打开就想知道"这是什么项目、能干嘛、怎么装"。
知乎那种"我发现了一个现象"的悬念开头在这里会显得绕——所以这一版是**项目介绍体**：
结论和安装放前面，发现放后面。

**发在哪**：登录 <https://www.oschina.net/home/login>（支持「使用 Gitee 登录」；免密登录下
**未注册的手机号验证后会自动注册**）→ 顶部导航「博客」→ 写博客。轻量版可发「动弹」
<https://www.oschina.net/osc-tweet/>，**同日只发其中一条**。

**注意**：OSC《社区规范》明确反对"恶意营销导流"。正文以技术内容为主，链接只留
GitHub + Gitee 两个，别在博客/动弹/问答里同时刷同一链接。新号首发可能进"待审核"。

**标题**

```
agent-charters：558 份 AGENTS.md 的标注数据集，外加一个一致性检查工具
```

**正文**

```
越来越多的仓库里出现一种新文件：AGENTS.md、CLAUDE.md、.cursorrules。
它不是给人看的文档，而是人写给 AI 智能体的行为规约。
我把它做成了一个开源数据集，外加一个用来检查自己有没有写漏的命令行工具。

## 这是什么

agent-charters 采集并标注了 GitHub 上公开的 558 份 AGENTS.md（来自 558 个仓库），
每份标注 30 个字段、九个内容类别（构建测试、流程、禁令、架构、风格、环境、
AI 行为规定、项目概览、坑）。

统计口径是 511 份：558 份里 40 份是近乎空的占位文件、7 份正文只有一句"见 CLAUDE.md"，
这两类都排除在百分比之外。

标注用规则完成，没有用大模型：先按标题切分，再用关键词判定类别；每一行都带
file_sha、采集日期、抽取器版本和规则集版本，任何人都能复算同一份数据。
代价是只能识别写进词表的表达，所以所有覆盖率都是下界。

产物在 Release 里，parquet + jsonl 两种格式。代码 MIT，数据 CC-BY-4.0，不含任何原文全文。

## 三条值得看的

1. "怎么跑起来"压倒一切：87% 的文件写了构建/测试/运行的命令，比第二位的 git/PR 流程（66%）
   高出一截（按标签出现次数算是 2.6 倍）。
2. 禁令排在很前面（65%）：大量文件用整节写"不要做什么"。人对 AI 的信任，
   看起来不是从授权开始的，是从划线开始的。
3. 最值钱的知识写得最少：坑/pitfall 只有 14%，是九类里最低的。而这类知识恰恰没法从代码里反推
   ——"别改 lockfile，bun install 会重写它"这种话，只有踩过的人写得出来。

最大的缺陷也在数字里：中文样本只有 5%（26/511），任何按语言做的对比都缺统计效力。

## 工具

仓库里带五个子命令，我自己最常用的是 compare：

    agent-charters compare 你的AGENTS.md

它会输出每个类别在语料库里的覆盖率、你命中了哪几类，以及"语料库里 87% 的人都写了、
而你一个字没写"的类别。另有 brief 命令，在动手写之前生成一份检查清单和可粘贴的提示词。

## 安装

    pip install git+https://gitee.com/janzong/agent-charters      # 国内
    pip install git+https://github.com/janzong/agent-charters     # 国外

也可以 clone 之后 pip install -e .。

    仓库：https://github.com/janzong/agent-charters
    国内镜像（GitHub 慢时用）：https://gitee.com/janzong/agent-charters

## 边界与反馈

分类是规则做的，覆盖率是下界；v0.1 时抽 12 份人工核对：准确 9、漏标 3、错标 0
（后续两轮改动未重做核对）。候选仓库偏向 AI / agent 话题，不能代表 GitHub 全体。

如果你手上有被它标错的 AGENTS.md，或者你觉得该有第十个类别，欢迎回帖或提 issue
——错标比漏标伤害大得多。
```

---

## 5. 预期质疑与答法

**"又一个 LLM 生成的垃圾数据集？"**

> 没有用模型打标，是规则匹配。九类关键词 + 跨语言强信号通道，
> 每一行都记了 ruleset 版本，改了什么、什么时候改的都写在 STATE.md 里。
> 局限我也写了：v0.1 时抽样 12 份人工核对，漏标 3、错标 0，所以覆盖率是下界。

**"这有什么用？"**

> 两个用途：一是看自己写章程时漏了什么（compare 命令）；
> 二是研究用途——比如"最值钱的知识写得最少"这个现象，
> 以前只能举例，现在有 511 份可以量化。
> 我不主张它是权威数据，它是一个有明确边界、可复算的样本。

**"为什么不抓 10000 份 / 为什么只有 AGENTS.md？"**

> 边际信息价值已经很低了（类别覆盖率的排序从 300 份起就稳定），
> 而抓更多种类（CLAUDE.md / .cursorrules）才是真正的下一步。
> 现在这个规模是为了先把管线跑通、把数据格式的坑踩完。

**"中文才 5%，数据不可信吧？"**

> 这是这份数据集最大的缺陷，我写在 LIMITATIONS 里。
> 它更可能是采集偏差 + 中文项目用这个文件的比例低，但我没有证据区分。
> 中文章程上的任何结论都应该当成下界。

**"版权呢？"**

> 只发布衍生标注与统计特征，不含原文全文。要原文请用 repo + file_sha 自行取回。
> 数据 CC-BY-4.0，代码 MIT。

**"数据能复现吗？"**

> 能。每行有 file_sha（内容指纹）和 retrieved_at（采集日期）。
> 产物在两种 PYTHONHASHSEED 下字节一致，且有测试守着。

---

## 6. 发完之后

- **别刷数据**：star 少不要紧，有一个人用上了就是判据 6 的突破
- 记下所有"这个标错了"的反馈 → 直接进 v0.2 的分类法修订清单
- 如果有人在别处引用/分析这份数据 → 立刻记进 STATE.md 第 2 节"外部信号"，
  这是比 star 更硬的证据
