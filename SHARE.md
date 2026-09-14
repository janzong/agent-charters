# 对外分享包 SHARE

> 给作者（人）用的发帖文案。**机器发帖会被当 spam，必须你自己发。**
> 这不是数据集的组成部分，发完可以删；留着也行——下次发版时能复用结构。
> 文案里的每个数字都可由 `data/processed/agent-charters-v0.3.parquet` 复算。

## 数字口径（当前，2026-09-13）

**对外一律用数据集 v0.5 / `ruleset_v0.1.8`，分母 516。两个头条数字并列：**

| 类别 | 覆盖 | 说明 |
|---|---|---|
| 禁令 `boundaries` | **85.7%**（442/516） | 其中 **45.2%**（233 份）**专门开了一节**写禁令 |
| 构建测试 `build_test` | **82.8%**（427/516） | |

相差 2.9pp，**小于禁令通式约 3% 的已知假阳性幅度**（`LIMITATIONS.md` §13）——
所以对外说**并列第一**，不要说"禁令压倒了构建测试"。

`build_test` 这个数字改过三次，原因和留痕都在 `LIMITATIONS.md` §11 / §13 / §15：

| 版本 | 数字 | 怎么来的 |
|---|---|---|
| v0.2（错误） | 87.9% (449) | 标题通道子串匹配，`ci` 命中了 `Deci\|sions` 这类词 |
| 09-12 我口头给的更正 | 84.7% (433) | **推算错误**：拿"误命中组合数 16"当"会掉标签的份数" |
| v0.3（实测） | 85.7% (438/511) | 修好后逐份比对，真正掉标签的是 11 份 |
| **v0.5（实测，现行）** | **82.8% (427/516)** | 100 份人工核对落地：修掉"代码块里的 `# 注释` 被当标题"（−）、5 份误判指针收回（分母 511→516） |

**已按 87% 发布**：知乎（§3）、开源中国（§4.5）。
**已按 84.7% 发布**：掘金（§4.6）。
**三站都只需要贴一次最终更正**（§7，2026-09-13 版）——**不要**再按中间那版 85.7% 贴一轮，
省得同一件事更正三次。**未发布的渠道（HN / Reddit / V2EX）直接用 v0.5 的数字。**

**准确率类数字的对外口径增加了留出集一组**：`precision 92% / recall 70%`（55 份盲判，`LIMITATIONS.md` §19）。引用时须同时说明它是**单标注者、无中文**的留出集；in-sample 的 90%/75%（§16）只作对照，不再单独对外。

**v0.4 追加（2026-09-12）**：四条**口径裁决**落地（人定，见 `TAXONOMY.md`「口径裁决」），
其中一条改动了数字——`agent_meta`（"AI 行为规定"）**36.4% → 25.8%**：
标题里出现 agent/instructions 不再算数（那多是文件自己的名字）。

## 0. 发布前 checklist

- [x] 链接：`https://github.com/janzong/agent-charters`（Release `v0.5`，Gitee 镜像同名 Release 已建）
- [ ] 先自己走一遍 README 的 `compare` 例子，评论里有人问细节时要能现场回答
- [ ] 只发你能守得住的量：一次 2 个渠道，隔 3–5 天再发下一批。
      同一天到处贴 = 看起来像推广机器人
- [ ] 准备好接受"这东西有什么用"和"LLM 生成的垃圾数据集"两类质疑（第 5 节）

**建议顺序（2026-09-11 按线路可达性重排，实测见 `ENVIRONMENT.md` §5.1）**

1. ✅ **知乎** —— 已发 2026-09-11（<https://zhuanlan.zhihu.com/p/2081788025013539447>）。链路可达，先用它把硬伤问出来
2. ✅ **开源中国**（§4.5，2026-09-12 上线）与 ✅ **掘金**（§4.6，2026-09-12 上线）—— **V2EX 在本线路被 SNI 阻断，发不出去**，用这两个顶短帖位
3. 隔 3–5 天再发 **HN** —— 它只是 DNS 污染，**加 hosts 就能发**（`209.216.230.207 news.ycombinator.com`，
   IP 会变、发前复核）。**2026-09-14 复验**：`--resolve news.ycombinator.com:443:209.216.230.207` → **200**；注意别用 AliDNS 给的 `174.37.54.20`（已过期，会 20s 超时）；Show HN 只有一次机会，等中文站把问题挖完再上

   **2026-09-14 落实（四台实测，DNS 污染面确认）**：251 / 240 / 云电脑**已写入 hosts 条目**，
   Mac 待用户执行（需密码，命令见下）。写入前四台的默认解析全废：251 得 `199.59.149.232`、
   AliDNS/UDP 兜底得 `185.60.219.36`、腾讯得 `59.188.250.54`、Cloudflare-UDP 得 `202.160.130.66`
   —— **全是被污染或劫持的假 IP，直连一律 12s 超时**（`http=000`）。
   `209.216.230.207` 是 TLS 校验通过的（`curl` 未加 `-k`，证书链验过 ⇒ 排除中间人）；
   同段 `.208/.209/.210` **全部不通**，别扫段，只钉 `.207`。
   - Linux / 251：`sudo sh -c 'echo "209.216.230.207 news.ycombinator.com" >> /etc/hosts'`
   - macOS：同上加 `sudo`，再 `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`
   - Windows（240 / 云电脑）：编辑 `%SystemRoot%\System32\drivers\etc\hosts` 追加同一行，再 `ipconfig /flushdns`
   - 回滚：删掉那一行即可（251 上带 `# 2026-09-14 Codex` 注释便于定位；Windows 上就是裸行）
   - ⚠️ **HN 换 IP 后这个钉法会静默失效**——发帖前先复测一次，别在发布会场才发现打不开
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

Percentages below are over the 516 files that actually contain instructions. Of the
558 collected, 40 are near-empty (<40 bytes) and 2 are pure pointers ("see CLAUDE.md").

Some things that surprised me:

- Two things tie for first. "How to build/test/run" is in 82.8% of files. Prohibitions
  are in 85.7% — and 45.2% have a *dedicated* "don't do this" section. People draw lines
  at least as often as they hand over instructions. (The 2.9pp gap is smaller than the
  ~3% known false-positive rate of the prohibition detector, so I report them as tied.)
- "Gotchas" is the rarest category at 14% — yet it's the knowledge you can't re-derive
  by reading the code. The most useful thing is the least written.
- Only 2 files contain no instructions at all, just a pointer: "see CLAUDE.md". Some
  teams have started to split their agent rules across several files.
- 72% of files are imperative (do/don't) rather than declarative knowledge.
- Only 4.8% are in Chinese, which seems low given GitHub's Chinese-speaking user base.

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
[OC] I annotated 558 AGENTS.md files from public repos — 83% document build/test commands, 86% say what NOT to do, only 14% warn about pitfalls
```

**正文**

```
Disclosure: I made this.

I kept writing AGENTS.md files for my own projects and wondering whether I was
missing the obvious. So I pulled 558 of them from public GitHub repos and wrote a
rule-based taxonomy to see what people actually put in these files.

9 categories, 30 fields per row. No LLM was used to label anything — it's heading +
keyword rules, and each row records which ruleset produced it.

Numbers worth a look (516 substantive files):

| category | share |
|---|---|
| prohibitions & boundaries | 85.7% |
| build/test/run commands | 82.8% |
| git/PR/release workflow | 67.1% |
| architecture & file layout | 59.1% |
| code style | 54.5% |
| environment & toolchain | 45.0% |
| project overview | 32.2% |
| AI-specific behavior rules | 25.8% |
| pitfalls / gotchas | 13.6% |

The 14% is the interesting one for me. "Don't use `bun install`, it breaks the
lockfile" is knowledge that no one can recover by reading the code, and it's the
least written-down category.

Also: 72% of files are imperative rather than explanatory, and only 2 files are pure
stubs ("see CLAUDE.md") — though 54% point outward to other files, which suggests many
teams are splitting agent rules across several files.

Caveats, because they matter: classification is rule-based, not hand-verified per
file, so treat the percentages as lower bounds. The corpus skews to AI/agent repos.
It's English-heavy (91%); Chinese is 4.8%, which is a real weakness of the dataset.

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

> **状态：已发布 2026-09-11**（<https://zhuanlan.zhihu.com/p/2081788025013539447>）。
> 正文里的 87% / 2.6 倍是当时的数字；**引用请用 §7 的 v0.5 定稿数字（82.8% / 85.7% 并列）**。
> 下面保留原文不改，目的是留档"当时到底发了什么"。该站的更正评论已写好，见 §7.1。

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

- 两类并列第一：构建/测试/运行的命令 82.8%，"不要做什么"85.7%（其中 45.2% 的
  文件专门开了一节写禁令）——信任是从划线开始的，而且划线至少和交底一样常见
- 坑/pitfall 只有 13.6%，是最低的一类，但这类知识恰恰没法从代码里反推
- 只有 2 份文件全文只有一句"见 CLAUDE.md"，纯做转发
- 中文只有 4.8%，低得不太正常

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

> **状态：已发布 2026-09-12**（<https://my.oschina.net/u/9764589/blog/19758304>）。
> 正文数字是当时的 87%；评论区已贴过一轮更正（84.7%，事后看也偏低）。
> **不要再贴 85.7% 那一轮**——直接贴 §7.2 的 v0.5 定稿版（82.8% / 85.7% 并列），一次到位。

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

## 4.6 掘金（中文长文，Markdown 原生）

> **状态：已发布 2026-09-12**（<https://juejin.cn/post/7684156210712166442>）。
> 正文用的是**修正后**的 84.7% —— 事后实测应为 **82.8% / 禁令 85.7% 并列**（84.7% 是我推算错的那一版，
> 见 `LIMITATIONS.md` §11.4；82.8% 是 v0.5 重算，见 §13/§15）。
> **下面保留已发布的原文不改**，更正话术见 §7.3。

**为什么单独一版**：掘金编辑器原生吃 Markdown——**切到「Markdown 模式」直接粘源码即可**，
标题、代码块、链接都不会被吃掉（OSC 那种"编辑器吃 Markdown"的问题在这里不存在，见 `STATE.md` §2 末列的遗留）。
所以这一版的正文是**真 Markdown**，生成时用 `--raw`（不剥标记、不合并段落），正文里的代码块原样保留。

**数字口径（重要）**：这一版发布时用的是 84.7%（**推算值，不对**）。87% 是标题子串误命中的
高估值（`LIMITATIONS.md` §11）；84.7% 是把"误命中组合数"当"会掉标签的份数"推算出来的。
**v0.5 定稿值：`build_test` 82.8% 与 `boundaries` 85.7% 并列第一**（分母 516，§13/§15）。
**未发布的渠道一律用 v0.5 的数字。**

**发在哪**：<https://juejin.cn> → 写文章 → 切「Markdown 模式」。
分类建议 **后端**（或「人工智能」）；标签最多 5 个：`AGENTS.md`、`AI`、`开源`、`数据集`、`效率工具`。
勾「原创」，别开「付费」。

**标题**

````
我把 558 份 AGENTS.md 标了一遍：人到底想让 AI 知道什么
````

**正文**

````
我在 GitHub 上抓了 **558 份 `AGENTS.md`**（来自 558 个仓库），逐份标了 30 个字段。

不是评测模型，也不是教你怎么写——我想回答一个很朴素的问题：**人到底想让 AI 知道什么？**

先把结论放这儿：

- **头号需求不是"你是谁"，而是"怎么把项目跑起来"**：84.7% 的章程写了构建/测试/运行命令。
- **第二显眼的是"不要做什么"**（65%）：大量文件用整节写禁令。人对 AI 的信任，看起来不是从授权开始的，是从划线开始的。
- **最值钱的一类写得最少**：坑 / 踩雷只有 14%，是九类里最低的。而这类知识恰恰没法从代码里反推——"别改 lockfile，`bun install` 会重写它"这种话，只有踩过的人写得出来。

数据集开源了，另外带一个命令行工具，可以拿你自己的 `AGENTS.md` 跟这份基线对一遍，看哪几类一个字没写。

## 这是什么

`AGENTS.md`（以及 `CLAUDE.md`、`.cursorrules`）不是给人看的文档，是人写给 AI 智能体的行为规约。

- **558 份**：GitHub 公开仓库，快照 2026-09-10
- **30 个字段**：语言、体量、章节数、star、许可、九类标签、标签计数、内容模式（指令 / 知识）、转引用标记……
- **九个内容类别**：构建测试、流程、禁令、架构、风格、环境、AI 行为规定、项目概览、坑
- **统计口径 511 份**：558 份里 40 份是近乎空的占位文件、7 份正文只有一句"见 CLAUDE.md"，这两类排除在百分比之外
- **产物**：parquet + jsonl 两种格式，在 GitHub Release 里；代码 MIT，数据 CC-BY-4.0，**不含任何原文全文**

## 三条值得看的

**1. "怎么跑起来"压倒一切：84.7%**

433 / 511 份文件写了构建、测试、运行的命令。按标签出现次数算，是第二名（git/PR 流程，714 次）的 **2.6 倍**。

这个数字比我预期的更极端，但它符合直觉：把项目跑起来是一切的前提，写章程的人和读章程的 AI 都绕不过这一关。

**2. 禁令排在很前面：65%**

335 份文件里有明确的"不要做什么"。不是零散一句，而常常是整节：`NO FILE DELETION`、`DO NOT EVER`、`Never run cargo build`、`ONLY use main, NEVER master`。

有意思的是**禁令的写法普遍比授权更具体**——"必须用 pnpm，不要用 npm" 这类句子出现的频率，远高于"你应该写出高质量的代码"。

**3. 最有价值的知识写得最少：14%**

坑 / 陷阱类只有 72 / 511，是九类里最低的，而且**跨版本极其稳定**：补了一批关键词之后，也只从 13% 涨到 14%。

这类内容的特点是不可推导：读代码读不出来、跑测试跑不出来，只有踩过的人写下来。所以它覆盖率最低，恰恰说明**"人没时间写、或者没想到要写"**，而不是它不重要。

## 方法：没有用大模型打标

标注**全部由规则完成**：先按标题切分章节，再用关键词判定类别（标题通道 + 正文通道 + 全文兜底通道）。

每一行都带 `file_sha`、采集日期、抽取器版本和规则集版本（当前 `ruleset_v0.1.2`）——**任何人都能复算同一份数据**。

代价也要说清楚：规则只能识别写进词表的表达，所以**所有覆盖率都是下界**，不是真值。宁可漏标，不做错标——这是我定的一条硬规矩（错标会污染统计，漏标只损失召回）。

## 一处自我更正：87% → 84.7%

如果你在别的地方看过这篇，那边的数字写的是 87%——我发出后回头复核，发现是**我自己分类规则的一个 bug**：

标题匹配用的是**子串**，于是 `ci` 这个词命中了 `Deci-sions`、`Princi-ples` 里的 "ci"，把一批没有构建内容的章节算成了"构建测试"。

实测：511 份里有 **23 份文件**的某个类别只靠这类误命中撑着，其中"构建测试"占 16 份。修掉之后：

- 构建测试：87.9% → **84.7%**
- 其余类别影响 ≤0.5 个百分点（禁令、概览、坑 不变）

**方向不变**：构建测试仍是第一名、仍明显领先第二名。但既然写出来了，数字就得是准的。
`LIMITATIONS.md` 第 11 条记了完整口径、影响面和修法。

## 顺手做了个工具

```bash
pip install git+https://gitee.com/janzong/agent-charters
agent-charters compare 你的AGENTS.md
```

它会输出：每个类别在语料库里的覆盖率、你命中了哪几类、以及"语料库里大多数人写了、而你一个字没写"的类别。

拿我自己一个内部项目跑的真实输出（路径隐去）：

```text
### AGENTS.md  [4.0KB, zh, 6 章节]
  overview         34%    —
  structure        59%    ✓ x1
  build_test       84.7%  ✓ x1
  style            56%    —
  workflow         66%    ✓ x1
  environment      44%    —
  boundaries       65%    ✓ x1
  gotchas          14%    ✓ x1
  agent_meta       36%    ✓ x2

合计覆盖 6/9 类
你没有、但语料库写得最多的：style / environment / overview
```

另有 `brief` 子命令：在动手写之前生成一份检查清单和可粘贴的提示词。五个子命令是 `stats / brief / compare / show / refs`。

> 说明：上面示例里的 `build_test` 我按修正后的 84.7% 写出；工具**当前版本仍打印 87%**——规则修正随下一个 `ruleset` 版本一起发，`LIMITATIONS.md` §11 有记录。

## 边界（请认真看这段）

- **中文样本只有 5%**（26 / 511），任何按语言做的对比都缺统计效力。
- 候选仓库偏向 AI / agent 话题，**不代表 GitHub 全体**。
- 覆盖率是**下界**；分类由规则完成，不是逐份人工标注。
- v0.1 时抽 12 份人工核对：准确 9、漏标 3、**错标 0**（后续两轮改动未重做核对，正在进行中）。

## 数据和代码

- 仓库：https://github.com/janzong/agent-charters
- 国内镜像：https://gitee.com/janzong/agent-charters
- 数据在 Release（parquet + jsonl）；代码 MIT，数据 CC-BY-4.0

**错标比漏标伤害大得多**：你手上有被标错的 `AGENTS.md`，或者觉得该有第十个类别，回帖或提 issue 都行——我会写进下一版分类法修订，并在 Release 说明里注明来源。

如果这篇对你有用，点个赞让写章程的人也能看到。
````

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

**"你的数字改了两次（87% → 84.7% → 85.7%），还能信吗？"**

> 能信的是**最后一个**，因为它是唯一一个"跑出来的"。前两个都是**推算**：
> 87.9% 是没发现子串误命中时的实测值；84.7% 是我发现 bug 后用"有多少个误命中组合"
> 推算出来的掉幅——方向对、幅度没验。修完之后逐份比对两份数据集，真正掉标签的是 11 份，
> 所以是 438/511 = 85.7%。
> 教训我写进了 `LIMITATIONS.md` §11.4：**推算的幅度不许直接进对外文案，必须先跑一遍修复版再比差集。**
> 修完的审计脚本现在同时打印"误命中组合数"和"实际掉标签数"，两者不再混用。

**"数据能复现吗？"**

> 能。每行有 file_sha（内容指纹）和 retrieved_at（采集日期）。
> 产物在两种 PYTHONHASHSEED 下字节一致，且有测试守着。

---

## 5.5 dev.to（英文，**机器可发** —— 2026-09-14 新增）

**为什么是它**：HN / Reddit 从 251 发不出去（Reddit 全线路超时；HN 只是 DNS 污染，pin 对 IP 能 200，
但发帖要网页登录）。**dev.to 从 251 直连 200，且有正式发文 API** ⇒ 目前唯一能"机器端到端发"的英文渠道。

- 文章：`work/share-paste/devto-article.md`（front matter 里带 title / tags / published）
- 脚本：`work/share-paste/publish_devto.py`（只用标准库；**默认发草稿**，`--live` 才上线）

```bash
export DEVTO_API_KEY=...                                       # 或写进 ~/.devto_api_key（只读不打印）
.venv/bin/python work/share-paste/publish_devto.py --dry-run   # 先看会发什么，不联网
.venv/bin/python work/share-paste/publish_devto.py             # 发草稿 → 打印 id / url
.venv/bin/python work/share-paste/publish_devto.py --update <id>              # 改文，**状态不变**
.venv/bin/python work/share-paste/publish_devto.py --update <id> --live       # 改文并发布
.venv/bin/python work/share-paste/publish_devto.py --update <id> --draft      # 改文并下架
```

**状态是怎么定的（2026-09-14 定稿）**：新建默认草稿；`--update` 默认**保持现状**
（先 `GET /api/articles/me/all` 读回当前 `published` 再原样发回），`--live` / `--draft` 显式覆盖，
两者互斥。为什么不用"省略 `published` 字段"：省略时平台取什么默认值未知，而草稿↔发布的往返会
**换 slug**（首发 ID `4649807` 的草稿期 URL 尾是 `-temp-slug-2057155`，发布后才定成 `-34gb`），
一旦被动下架再上线就可能把已分享出去的链接打坏。所以状态一律显式写死。
另注：PUT 的回执里 `published` 恒为 `null`（平台行为），**判断状态要看列表端点**，别信回执。

- key：dev.to → Settings → Extensions → **DEV Community API Keys** → Generate
  （脚本从 `DEVTO_API_KEY` 或 `~/.devto_api_key` 读；文件用 `0600`，两处都**不打印**）
- ⚠️ 坑：`--live` 必须和 `--update <id>` 一起用才会发布 —— 2026-09-14 已修
  （原条件写成 `--live and not --update`，配 `--update` 时会静默只建/更新成草稿）。
  行尾打印的 `published=` 也已改成取 API 回执（原取自 front matter 字符串，会误报 `false`）。
- 首次发布留档：id `4649807`，2026-09-14 12:23Z 上线 ——
  <https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
- 口径：v0.5 数字 + 英中两个留出集（92%/70%、88%/73%），**不带三站更正尾巴**
- 文章尾部带一条公开请求：**找 2–3 个非作者的使用者跑 `compare`** —— 这正是判据里缺的那一格
- 纪律：dev.to 发文是平台支持的行为，但仍按"一次 2 个渠道、别同日到处贴"来

## 6. 发完之后

- **别刷数据**：star 少不要紧，有一个人用上了就是判据 6 的突破
- 记下所有"这个标错了"的反馈 → 直接进下一版分类法修订清单
- 如果有人在别处引用/分析这份数据 → 立刻记进 STATE.md 第 2 节"外部信号"，
  这是比 star 更硬的证据
- **已发布的数字更正要及时、要写清"我怎么错的"**：§7 是三站的更正话术；
  更正本身也是可信度的一部分，藏起来比说错更伤

---

## 7. 数字更正话术（三站，2026-09-13 定稿 —— ✅ §7.1–7.3 三站均已贴；§7.5–7.7 留出集评论待贴）

**背景一句话**：`build_test` 的现行正确值是 **82.8%（427/516）**，不是我先前说的 87%、
也不是我推算的 84.7%；同时 `boundaries`（禁令）以 **85.7%** 与它并列第一。
三处数字都错过，原因各不相同，全过程在 `LIMITATIONS.md` §11 / §13 / §15。

**贴法**：三站都只贴**一次**（下面 §7.1–7.3 各自按平台），不要再补一轮 85.7% 的中间版。

**§7.5–7.7 是另一件事**（不是更正，是补留出集）：55 份盲判 precision 92% / recall 70%，与 in-sample 差 3–5pp、方向一致，口径见 `LIMITATIONS.md` §18 / §19。
三站各贴一条，与 §7.1–7.3 并列，**不要**合成一条长评论。

### 7.1 知乎（追加在首发那条更正评论下面）

```
再更正一次，这次是 100 份人工核对全部落地后的重算，数字有变动，先说结论：

构建/测试/运行命令：82.8%（427/516），不是 85.7%，也不是 87%。
禁令（不要做什么）：85.7%（442/516）——两类并列第一，差距 2.9pp 小于禁令通道
约 3% 的已知假阳性，所以我不说"禁令压倒构建测试"。

分母也变了：511 → 516。

两个原因，都是修错，不是内容变了：
1）我在切章节时把代码块里的 `# 注释` 当成了标题——`# 3. Build`、`# Run tests`
   这些是 shell 注释。129/558 份文件有这种情况（最多一份 54 行）。
   修掉后 diffblue/cbmc 的章节数从 146 掉到 92，构建测试从 51 次证据掉到 22 次。
2）有 5 份短文件被我误判成"只是转发指针"而剔出了统计（比如 buttondown/docs：
   314 字节，写了"用 Bun 不用 npm"加三条具体规则）。收回来后分母 511 → 516。

这一轮是拿 100 份人工判读结果逐条改规则（改动清单在仓库 work/audit/v0.1.8-changelist.md），
不是我又拍脑袋估数。复算：agent-charters compare/stats，数据集 v0.5 / ruleset_v0.1.8。
```

### 7.2 开源中国（追加评论，≤500 字）

```
再更正一次，这次是 100 份人工核对全部落地后的重算，分母也变了（511 → 516）：

构建/测试/运行命令 82.8%（427/516），不是我上条说的 85.7%；
禁令 85.7%（442/516）——两类并列第一（差 2.9pp，小于禁令通道约 3% 的已知假阳性）。

两处修错，都不是内容变了：
① 切章节时把代码块里的 `# 注释` 当标题，`# 3. Build`、`# Run tests` 这类 shell 注释
   变成了章节；129/558 份文件有这种情况，修掉后 cbmc 章节数 146→92；
② 5 份短文件被误判成"只是转发指针"剔出了统计（如 buttondown/docs 314 字节，
   写了"用 Bun 不用 npm"和三条规则），收回后分母 511→516。

完整链条：87.9%（v0.2，含子串误命中）→ 84.7%（我推算错）→ 85.7%（v0.3 实测）
→ 82.8%（v0.5 定稿）。改动清单 work/audit/v0.1.8-changelist.md，LIMITATIONS.md §11/§13/§15。
```

### 7.3 掘金（追加评论）

```
补一处更正：文中"87%""84.7%"两处都作废，现行正确值（数据集 v0.5 / ruleset_v0.1.8）：

构建/测试/运行命令 82.8%（427/516）；禁令 85.7%（442/516）——两类并列第一
（差 2.9pp，小于禁令通道约 3% 的已知假阳性，所以不说"压倒"）。

分母也从 511 变成 516。两处修错：
① 代码块里的 `# 注释` 被当成了标题（`# 3. Build`、`# Run tests` 是 shell 注释），
   129/558 份文件受影响，修掉后 cbmc 的章节数 146→92、构建测试证据 51→22 次；
② 5 份短文件被误判成"只是转发指针"（如 buttondown/docs，314 字节但有四条真规则），
   收回后分母 +5。

这一轮是 100 份人工核对的结果，改动清单在 work/audit/v0.1.8-changelist.md，
复算脚本与教训在 LIMITATIONS.md §11 / §13 / §14 / §15。
```

### 7.4 若有人追问"那 87% 到底错在哪"

- **87.9% → 85.7%（v0.3）**：标题通道曾是纯子串——`ci` 命中 `Deci|sions`、`script` 命中
  `Type|Script`、`build` 命中 `allow|Builds`；另有裸词 `make` 把 `Make changes` 算成构建。
  修法：命中点必须落在词首（保留词首前缀），并删掉裸词 `make`。511 份里 23 处
  (文件, 类别) 组合的标签只靠误命中撑着 → 18 处掉标签（无一例新增）。
- **85.7% → 82.8%（v0.5）**：代码块里的 `# 注释` 被当成标题（129/558 份受影响），
  以及 5 份误判指针收回（分母 511 → 516）。
- **禁令 85.7% 哪来的**：v0.5 补了正文的 `Do not …` 通式（此前只认 `never commit` /
  `must not` / 中文模式）。它有约 3% 的已知假阳性（`workflows do not initialize submodules`
  这种描述句），**故意没收窄**——收紧会让召回塌掉（试过"只认行首"，全库只命中 26 处，
  而句中 2606 处里抽查 12/14 是真禁令）。详见 `LIMITATIONS.md` §13。
- 复算：`work/substring_audit.py`、`work/dataset_diff.py`、`work/audit/v0.1.8-changelist.md`。


### 7.5 知乎（留出集，2026-09-13 新增，待贴）

```
再补一条：留出集。

前面那些 82.8% / 85.7%，出自那 100 份人工核对——而那 100 份正是我用来改规则的样本，
所以它们是 in-sample，天生偏高。为了拿到一个真留出的数，我先剔掉改规则用过的全部样本
（去重后 106 份，其中 94 份落在 516 份实质样本里），可用池剩 422 份，再从里面随机抽
55 份，只看原文盲判，判完才打开规则结果：

precision 92% / recall 70%（TP 221 / FP 19 / FN 93）。

与 in-sample 那组对照：precision 90% → 92%、recall 75% → 70%，差 3-5pp 且方向一致
（precision 略升、recall 略降）⇒ v0.5 的规则改动没有明显过拟合，前面的数不是自己哄自己。

短板也说清楚：漏标 93 处 vs 错标 19 处，漏标集中在 gotchas（recall 32%）、
overview（40%）、agent_meta（45%）、environment（57%）——它们都散在正文里、
没有专门章节，正是标题通道的盲区。

这个数有三个边界：①只有一个标注者（我），换人判数字会动；②中文留出集 = 0
（语料库里 25 份中文上一轮全用掉了），中文准确率仍只有 in-sample；
③全库只有 7 份文件级完全一致（12.7%）——9 类任取子集逐类全中才算"完全一致"，
这是严格口径，多数分歧其实只是 1-2 个类别。

复算：work/audit/holdout_vs_rule_v0.5.py（抽样 seed 20260913）。
```

### 7.6 开源中国（留出集，追加评论，≤500 字，待贴）

```
补一条：v0.5 的准确率有留出集估计了。

前面 82.8% / 85.7% 出自那 100 份人工核对，而那 100 份就是我改规则用的样本，
天生偏高。于是先剔掉改规则用过的样本（去重后 106 份，命中实质样本 94 份），
可用池剩 422 份，从中随机抽 55 份盲判（只看原文、判完才看规则输出）：

precision 92% / recall 70%（TP 221 / FP 19 / FN 93），
与 in-sample 的 90% / 75% 差 3-5pp、方向一致 ⇒ 没有明显过拟合。

短板在漏标：93 处 vs 错标 19 处，集中在 gotchas（recall 32%）、overview（40%）、
agent_meta（45%）、environment（57%）——散在正文里、没有专门章节，是标题通道的盲区。

边界：只有我一个标注者；中文留出集 = 0（中文样本上一轮用光）。
复算 work/audit/holdout_vs_rule_v0.5.py，seed 20260913。
```

### 7.7 掘金（留出集，追加评论，待贴）

```
补一条：留出集估计出来了。

上面那些 82.8% / 85.7% 出自 100 份人工核对，而那 100 份正是我改规则用的样本，
所以是 in-sample、天生偏高。真留出集是这么抽的：先剔掉改规则用过的样本
（去重后 106 份，命中实质样本 94 份），可用池剩 422 份，从中随机抽 55 份，
只看原文盲判，判完才对照规则输出。

结果 precision 92% / recall 70%（TP 221 / FP 19 / FN 93）；
in-sample 是 90% / 75%，差 3-5pp 且方向一致 ⇒ v0.5 没有明显过拟合。

短板照旧在漏标：93 处 vs 错标 19 处，集中在 gotchas（recall 32%）、overview 40%、
agent_meta 45%、environment 57%——都散在正文、没有专门章节，是标题通道的盲区。

另外：只有我一个标注者；中文留出集为 0（中文样本上轮用光）。
复算：work/audit/holdout_vs_rule_v0.5.py（seed 20260913）。
```
