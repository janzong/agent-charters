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

   🔴 **发 HN 时必须用 GitHub 链接，不要用 dev.to 链接**（2026-09-14 查证）：
   HN 默认把 `dev.to` 的提交**直接标成 dead**（"dev.to submissions will appear as dead by default
   in the 'New' queue"，2022-06-25 评论；另有 Ask HN 专帖《Why are most dev.to links submitted to HN dead?》
   20 分 / 36 评）。配套证据：116 分 / 106 评的《The collapsing quality of dev.to (2021)》，
   评论区原话"dev.to is almost entirely low-quality articles … not unexpected for HN to ban the site altogether"、
   "i stopped frequenting the dev.to community because the average quality of articles just got so low"。
   ⇒ **HN 提交 URL 一律指 GitHub 仓库**，dev.to 只做站外社区，两者别混。
4. 最后 **Reddit** —— DNS 污染 + SNI 阻断，**必须有代理**；没代理就跳过，别硬排

**时间**：HN 在北京时间 **20:00–23:00**（美东上午）；Reddit 同理。
知乎 / 开源中国 / 掘金在**工作日 10:00–12:00 或 20:00–22:00**。

---

## 1. Show HN（英文）

### 2026-09-22 现场复测与操作顺序（发布仍由人执行）

| 项 | 实测 |
|---|---|
| `news.ycombinator.com` / `/submit` / `/login` | 均 `HTTP 200`；无需 pin IP |
| HN 账号 `janzong` | 公共 API 返回 `null` ⇒ **该账号尚不存在** |
| 本仓库 URL 的历史提交 | Algolia 检索 `nbHits=0` ⇒ **尚未提交过** |
| 提交用链接 | 必须用 GitHub 仓库，**不要用 dev.to 链接**（HN 默认把 dev.to 提交标 dead） |

**上线前可试用性复核（2026-09-22，只读）**：

| 项 | 实测 |
|---|---|
| GitHub 仓库 | `PUBLIC`，最新 Release `v0.5`（2026-09-12），资产 `parquet 56,907 B` / `jsonl 553,371 B` / `SHA256SUMS` |
| PyPI | 最新 `0.4.1`，`requires-python >=3.10`，零运行时依赖；README 首推 `pipx install agent-charters` |
| 仓库首页 | `https://github.com/janzong/agent-charters` 返回 `200`（7.9s） |
| CLI 快速命令 | 本机实测 `agent-charters 0.4.1 ｜ dataset v0.5`，对本仓库 `AGENTS.md` 输出 `9/9 categories` |

⇒ HN 访客路径成立：公开仓库 → 一条安装 → 一条 `compare` 命令。唯一缺的是账号与人工发帖。

### 2026-09-22 注册卡点：HN 关闭了大陆出口的账号创建

两处独立网络实测都收到同一句拒绝：

| 来源 | 结果 |
|---|---|
| 251 直连 `POST /login`（`creating=t`） | `HTTP 200`，正文 `Sorry, account creation disabled.` |
| 云电脑（`-p 2222`，独立出口）`curl.exe POST /login` | 同样 `HTTP 200` / `account creation disabled` |
| Mac（`-p 2223`，独立出口）`curl POST /login` | 同样 `HTTP 200` / `account creation disabled` |

两处 `GET /login` 仍显示 create account 表单，`GET /submit` 也仍是 `200`；**只有创建账号被拒**。
⇒ 这不是 251 单机问题，也不是 TLS/墙：**251、云电脑、Mac 三个独立出口都被同一句拒绝**。
**HN 这一步只能改用已有账号**（登录不受影响），或等 HN 重新开放注册；不要再换机器重复试注册。

同轮顺带复测 V2EX：公开 DNS 返回污染地址，直连 443/80 全 `000`；改用 Cloudflare DoH 取真实地址时
`https://cloudflare-dns.com/dns-query` 本身 `Recv failure: Connection reset by peer`，无法完成 pin。
⇒ V2EX 在本线路仍不可用，不做发布尝试。

操作顺序：

1. 打开 <https://news.ycombinator.com/login>，用页面底部的 **create account**
   表单建号（只需用户名 + 密码，无邮箱步骤），用户名建议与 Gitee/GitHub 一致。
2. 登录后打开 <https://news.ycombinator.com/submit>：
   - `title` 用本节下面那行 `Show HN: …`；
   - `url` 填 <https://github.com/janzong/agent-charters>；
   - `text` 留空（链接帖不能同时带正文）。
3. 提交后立刻在**自己的帖子里**发一条评论交代背景、能试什么、哪里最需要反馈。
   ⚠️ HN 版规明写 **不得发布 AI 生成或 AI 编辑的文本**（`newsguidelines.html`：
   "Don't post generated text or AI-edited text"）⇒ 本节下方的正文只是事实要点，
   **不要整段粘贴**，要由本人用自己话重写。
4. 不要请人点赞/评论；Show HN 只发一次，不提"请 upvote"。
5. 建议时间：北京时间 20:00–23:00（美东上午）。发布后 1 小时内盯 `/newest` 与评论。

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

    pip install agent-charters                                   # PyPI（2026-09-15 上线）
    pip install agent-charters -i https://pypi.tuna.tsinghua.edu.cn/simple   # 国内拉依赖慢时

也可以直接装仓库（`pip install git+https://gitee.com/janzong/agent-charters`，国内约 10 秒），
或 clone 之后 pip install -e .。

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
pip install agent-charters
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
- **合集**：`AGENTS.md in the wild` → <https://dev.to/janzong/series/44219>（`collection_id 44219`，2026-09-14 建，
  已含本文；合集页实测 200 且含本文链接）。同主题文章在 front matter 带 `series:` 即自动进合集
- **第二篇（2026-09-14 12:5x 上线）**：id `4650835`，标题 *I looked at 558 AGENTS.md files: here's a 5-minute
  check for yours*，tags `ai/agents/devtools/productivity`，源码 `work/share-paste/devto-article-02.md`。
  主题＝**读者自查**（不碰任何私库材料）：九类基线率 → 两个实测案例（`langchain-ai/deepagents` 7/9 缺
  `overview`+`gotchas`；`openai/openai-agents-python` 6/9 缺 `style`/`agent_meta`/`gotchas`）→
  "坑"为什么稀少（120 条人工标注：58% 读代码可得 / **34% 根本不是坑** / 8% 只能靠经历）→ 五问自查
  → 工具用法 → 诚实的局限 → 请读者跑 `compare` 报告错标
- ✅ **包已上 PyPI**（2026-09-15）：对外文案现在**可以**写 `pip install agent-charters`。
  （2026-09-14 之前确实是 404，那时只能用 git 直装 —— **旧文案里"不能写 pip install"已作废**。）
  证据：`pip download` 走**默认索引**拉到轮子、sha256 与 PyPI 公布值逐字节一致；
  干净 venv 装完、换无关目录跑 `compare` 输出 8/9 正常。**国内拉依赖仍要加清华镜像**
- 首次发布留档：id `4649807`，2026-09-14 12:23Z 上线 ——
  <https://dev.to/janzong/i-labeled-558-agentsmd-files-heres-what-they-say-and-what-almost-nobody-writes-down-34gb>
- 口径：v0.5 数字 + 英中两个留出集（92%/70%、88%/73%），**不带三站更正尾巴**
- 文章尾部带一条公开请求：**找 2–3 个非作者的使用者跑 `compare`** —— 这正是判据里缺的那一格
- 纪律：dev.to 发文是平台支持的行为，但仍按"一次 2 个渠道、别同日到处贴"来
- **2026-09-17 复盘**：给 4 位评论者的回复**都已贴出**（`devto-reply-01..04.md`，API 复核时间
  12:49 / 13:26 / 14:19 / 14:19），**三天无人回应**；`devto-watch.timer`（每 30 分钟）会在有新评论时通知。
  对方没接住的可能原因是**门槛**：原请求要人 `pip install` 再跑命令。
  ⇒ 对策：`work/share-paste/devto-selfcomment-01.md` —— **作者自评一条**，把请求降成
  "把你的 `AGENTS.md` 贴在评论里，我来跑、我回"（零安装）。⚠️ **待人贴**（评论发不了，见 §5.5 实测）

### 口碑与对外分发（2026-09-14 查证，源：HN Algolia + dev.to/about + Forem 源码）

**名气**：英语世界最大的通用开发者社区之一，建在开源的 Forem 上；`dev.to/about` 原文确认
"DEV has joined forces with Major League Hacking (MLH)"。但在**技术精英圈（HN）口碑偏负**：
《The collapsing quality of dev.to (2021)》116 分 / 106 评，评论区直指"几乎全是低质文章"、
"平均质量低到不值得我花时间"。⇒ **它的价值是"触达中位数开发者 + SEO"，不是"拿技术背书"**
——对本项目（要的是中立的外部使用者，不是 HN 的赞）反而够用。

**对外分发，实测只有一条自动通道**：

| 通道 | 状态 | 证据 |
|---|---|---|
| **RSS**（`dev.to/feed/<用户名>`、`dev.to/feed/tag/<tag>`） | ✅ **通** | 实测均 200；用户 feed 里已含本篇文章，任何聚合器/机器人可消费 |
| 站内首页 / Tag 流 / reactions / 评论 / 收藏 | ✅ 有 | 站内算法，无外部加权 |
| **自动转发到 Twitter / X / Mastodon** | ❌ **没找到** | Forem 源码搜 `autoshare` **零命中**；社交字段（mastodon/twitter/github…）只是个人资料链接（`app/models/settings/general.rb`）。**不要指望发完自动扩散** |
| 第三方聚合（daily.dev 等） | ❓ 未证实 | 拉到的页面提到 Medium 21 次、`dev.to` 0 次，但页面是 JS 渲染，**不打包票** |

⇒ 结论：**dev.to 不负责把你推出去**。发文只是"有地方可被引用 + 进 RSS + 爬虫能抓"，
真正的扩散仍要靠人把链接贴到别处（而 HN 又拒收 dev.to 链接，见 §0）。
**可做的一件事**：在 dev.to 个人资料里把 GitHub 链接填上（Forem 支持 github 字段），
读者看文章时不显示，但点进主页能看到仓库入口。

### 渠道裁决（2026-09-14 由人定）

**外网以 dev.to 为主**，HN 押后（等中文站与 dev.to 把硬伤问出来，Show HN 只有一次机会）。
Reddit 无代理则跳过。

### 能自动到哪一步（2026-09-14 实测划界）

| 动作 | 能不能脚本化 | 依据 |
|---|---|---|
| 建草稿 / 发布 / 改文 / 下架 | ✅ 能 | `POST`/`PUT /api/articles` |
| **设合集（series）** | ✅ 能 | `PUT` 带 `series: <名字>`；首次自动建合集（本仓库→ `collection_id 44219`）。⚠️ 后续每次更新**必须继续带**，PUT 会覆盖字段 |
| 改个人资料（Bio / GitHub / Website） | ❌ **不能** | API 只有 `GET /api/users/me`，无写路由。文案见 `work/share-paste/devto-profile-setup.md` |
| 读文章状态、阅读量、评论 | ✅ 能 | `GET /api/articles/me/*`、`GET /api/comments?a_id=` |
| **发评论 / 回复评论** | ❌ **不能** | `POST /api/comments` **返回 HTML 404——该路由在真实站上不存在**（Forem 文档里有，未部署）。三种 body 写法都试过，全 404 |
| 点赞 / 关注 | ❌ 不能 | 无对应路由 |

⇒ **对外互动必须由人贴**。回复/评论文案写在 `work/share-paste/`，格式都是"复制即贴"。

**2026-09-14 裁决：先维持粘贴流程**（评论量还小；自动化需在 Mac 上建专用 Chrome 配置并登录一次，
属系统改动，等互动量上来再做。可行性已探明：Mac 有 Chrome + node v22 + npm 可达（官方源与 npmmirror 均 200）、
251 有 Chrome 153 + `~/.cache/ms-playwright` 缓存，两条路都通）。

### 第 3 篇：分母研究（2026-09-19 **已上线**）

- 文件 `work/share-paste/devto-article-03.md`，tags `ai/agents/github/opensource`，
  series `AGENTS.md in the wild`（已在页面上确认）
- **线上 id `4692300`**：`https://dev.to/janzong/how-common-is-agentsmd-really-i-sampled-github-62-of-active-repos-10-of-all-repos-1175`
  发布 2026-09-19T08:30:25Z（公开 `GET /api/articles/4692300` 返回 200，页面含 series 名）
- 主题＝分母研究：活跃仓 6.2% / 存量 1.0%、`CLAUDE.md` 5.4% 基本并驾齐驱、93% 存量仓近 90 天没 push、
  8.3% 空仓；主动交代趋势测不出来（世代 vs 年龄混淆）、两个框不一致（6.2% vs 1.8 ⇒ 区间 2–6%）、
  以及 `403` 三义那个 API 坑。
- ⚠️ **同时留下一个重复草稿 `4692252`**，已改名为 `[副本·已发布，勿发] …` 并在正文首行写了线上 URL。
  **API 删不掉**（`DELETE /api/articles/{id}` 是 404，和评论路由一样没有）；要清掉只能在 dev.to 后台手动删。

#### ⚠️ 踩到的命令陷阱（已加防呆）

`publish_devto.py --live` **不带 `--update` 会新建一篇**，而不是把已有草稿转正。
本次就是这么撞上的（草稿 4692252 留着、线上多出一篇 4692300）。正确写法：

```bash
# 把已有草稿转正（正确）
.venv/bin/python work/share-paste/publish_devto.py --file <稿> --update <草稿id> --live
# 全新文章（会新建）
.venv/bin/python work/share-paste/publish_devto.py --file <稿> --live
```

脚本现在会在"`--live` 且无 `--update`"时打印警告。

### 作者自评请托：贴错了文章（2026-09-19）

**发生了什么**：`devto-selfcomment-01.md` 明确指定贴在**第 1 篇**（`4649807`），实际 08:37Z 贴到了
**第 3 篇**（`4692300`，发布后 8 分钟、**0 阅读**）。API 复核：第 3 篇评论 1 条（`janzong` `3f8o6`）、
第 1 篇仍是 5 条（4 条真外部读者 + 1 条垃圾）。

**各篇流量（09-19 实测）**：第 1 篇 **57 阅读 / 5 评论** ｜ 第 2 篇 29 / 4 ｜ 第 3 篇 **0 / 1**。

**判断**：请托没坏（内容是自包含的），但**贴在了没有流量的页面**上，而且第 3 篇讲的是普及率、
请托讲的是九类覆盖，语境接不上。第 1 篇才是唯一有真实读者的地方。

**补救**：`work/share-paste/devto-selfcomment-02.md`（按第 1 篇语境重写、更短、引用了该线程里
`jo-do` 那句 "the gotchas are the file"）——**待人贴**。第 3 篇那条建议留着（不碍事，将来有读者时仍成立）。

### 评论盯梢（2026-09-14 装机，**只在有新评论时出声**）

**为什么盯评论**：文章我能自动发，评论我发不了（API 只读）——评论是唯一"需要人动手、漏了就浪费"的信号。
两条外部反馈都在发布后 25 分钟内出现，说明窗口很短。

- 脚本：`work/share-paste/watch_devto.py`（纯标准库）
  - `--changed-only`（timer 用的模式）：没新评论**完全不输出**，退出码 0 / 10（10＝有新评论）
  - `--notify-hermes`：有新评论时发一次固定收件箱（走 `notify-hermes.sh`，自带敏感信息闸门）
  - 状态 `~/.local/state/devto-watch.json`（记已见过的评论 id + 上次阅读/反应数）
  - 评论全文落 `~/.local/state/devto-watch.log`（通知正文只带前 600 字符）
  - **首跑只建立基线**，历史评论不算"新"、不通知（这条有 bug 已修：原实现首跑会把历史评论全当新的）
- systemd user 单元：`work/share-paste/systemd/devto-watch.{service,timer}`，每 30 分钟一次
  （`OnBootSec=3min` / `OnUnitActiveSec=30min` / `RandomizedDelaySec=120` / `Persistent=true`）
- ⚠️ **单元里必须带 `Environment=PATH=...hermes venv...`**：systemd user 的 PATH 不含
  `~/.hermes/hermes-agent/venv/bin`，而 `notify-hermes.sh` 用 `hermes` 命令——实测不加就找不到命令，
  而且要到第一条评论出现才暴露。装完用 `systemctl --user show devto-watch.service -p Environment`
  配合 `env -i PATH=... command -v hermes` 复验
- 安装 / 卸载：
  `cp work/share-paste/systemd/devto-watch.* ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now devto-watch.timer`
  ｜ `systemctl --user disable --now devto-watch.timer`
- 看历史：`journalctl --user -u devto-watch -n 30` ｜ 手动跑一次：`systemctl --user start devto-watch.service`
- 验证记录：装在 2026-09-14 21:30，timer 已排程（下次 22:02）；首跑静默 rc=0；
  **systemd 内端到端**用假通知命令复现过一次"新评论 → 通知正文 → 状态自愈"

### ⚠️ 盯梢的静默失败（2026-09-14 22:0x 踩到，已修）

**现象**：第二篇文章来了两条评论（`alexshev` 13:35:35Z、`raknaos` 13:42:27Z），
**没人被告知**——两小时后用户自己翻页面才看见。

**根因（systemd 日志坐实）**：`journalctl --user -u devto-watch` 里
`start operation timed out. Terminating.` ＋ `Failed with result 'timeout'`（22:02:15 → 22:05:15）。
原实现的三步顺序是 **①推进 state ②调 hermes 通知 ③写日志**，而
`notify-hermes.sh` 内部 `timeout 300` **大于**单元的 `TimeoutStartSec=180` ——
hermes 那轮卡住，systemd 在 180 秒把服务杀了：**日志没写、通知没发，而 state 已经推进**，
这两条评论从此永远不会再被看见。

**三条修法**（都在本次提交里）：
1. `watch_devto.py` 顺序改成 **①写日志（durable）②通知 ③只有通知成功才推进 state**；
   任何一步被杀，下一轮整轮重来 —— 最坏是**重复通知**，不是静默丢。
2. 日志按 `id_code` 去重（重试不会把同一条评论写第二遍）；日志头现在带 `| <id_code> =====`。
3. 单元 `TimeoutStartSec` 180 → **420**（> `notify-hermes.sh` 内部 300 > `subprocess timeout` 330），
   并给 `notify-hermes.sh` 一个比它自己更宽的窗口：**让它自己超时并给出 rc**，
   而不是被 systemd 掐断（掐断连 stderr 一起丢，排查时看不见原因）。

**复验**：假通知命令（`DEVTO_WATCH_NOTIFY_CMD=`）
① 退出 0 → 日志写一次 + state 推进 ✓
② 退出 1 → stderr 出「通知失败 rc=1 / state 未推进，下一轮会重试」，日志行数不变（去重生效）、
state 保持原样 ✓
③ 真实 timer 路径实跑一次：26 秒结束、无新评论静默 ✓
丢失的两条评论已补写进 `~/.local/state/devto-watch.log`（补写前的 state/log 备份在
`/tmp/devto-watch.{json,log}.bak`）。

### ⚠️ 同一晚又踩到两处（2026-09-14 22:35，已修）

换 key 后手动跑了一次真实 timer 路径，暴露出两个独立问题：
1. **自家回复也会触发通知**：`alexshev`/`raknaos` 的回复发出后，脚本把**我自己的两条回复**
   也当成"新评论"，一路 ping 进 Hermes 收件箱，通知链路白跑一轮（那一轮真花了 3.5 分钟）。
   已修：按**文章作者名**过滤 —— 作者自己的评论只记进 state，不通知、不写日志。
   复验：只把自家两条退回"未见过" → 输出「（无新评论）」、4.7 秒结束、state 正常回到 4 条 ✓
   （对照：同样条件下刷新一条外部评论 → 40 秒、通知真发出 ✓）
2. **退出码 10 被 systemd 记成失败**：脚本用 10 =「有新评论」，而 systemd 的 oneshot
   把任何非 0 当失败，于是 `Failed with result 'exit-code'` —— 天天报红，**真正的失败反而看不见**。
   已修：单元加 `SuccessExitStatus=10`。

顺带确认了 420 秒超时是对的：实测一次 `notify-hermes.sh` 花了 **~3.5 分钟**（旧的 180 秒
必然把它掐死——正是上面那个静默失败事故的成因）。

### ⚠️ 2026-09-20 第三次盯梢事故：闸门误报 + 人工探测吞 state（均已修）

- **现象**：`frankchu`/`mthburnsbarberweb` 两条评论（9-19 17:29Z / 19:35Z）从 01:59 CST 起
  每 30 分钟通知失败一次（共 15 次），state 不推进，**用户 8 小时没收到任何提醒**。
- **根因 1（闸门误报）**：`notify-hermes.sh` 的敏感信息闸门用**裸词** `token` 匹配，
  把公开评论里的 "3,281 tokens" 当成令牌拦下。已改成「赋值形状 + 常见凭据前缀」
  （`sk-`/`ghp_`/`github_pat_`/`gitee_`/PEM/Bearer 长值/JWT/`口令|密码`+赋值），
  源文件 `~/plugins/fleet-ops/scripts/notify-hermes.sh`，插件缓存重装到
  `0.1.0+codex.20260920012308`；9 条用例实测（3 条误报放行、6 条真凭据仍拦）。
- **根因 2（人工探测吞 state）**：手工跑 `--changed-only`（不带 `--notify-hermes`）
  会推进 state，随后 timer 认为"无新评论"而静默。已在 `watch_devto.py` 加防呆：
  `--changed-only` 单用只检查、**绝不推进 state**，并输出一行提示（实测 state mtime 不变）。
- **补发**：修复后已手动把两条评论补送 Hermes 固定收件箱（msg 263）。

### 第 3 篇 listwright：issues/PR 分母污染（2026-09-22，**回复已贴出**）

`listwright`（评论 id `3fei6`，2026-09-22T21:27:53Z，2742 字符，顶层评论）给出第二个分母污染实例：
`GET /repos/{owner}/{repo}/issues?state=all` 会把 PR 当 issue 返回；他在 9 个仓读到 1,525 条，其中
634 条（41.6%）是 PR，按仓 9.7%–89.5%；同一评论率指标过滤前后没有固定方向（9 个仓里 5 个高估、4 个低估），
事后无法校正；再过滤 PR 后，“至少一条评论”仍会把 issue 作者自我回复算进去，7 个仓抽 25 条后 5 个真实
非作者评论率为 0.000。局限性他也自己写明：9 个仓不是概率样本，41.6% 只能当存在性证据，3 个仓在 300 条
截断，25 条/仓偏薄。

**回复口径**：确认我的两个 prevalence 框只用 search + `git/trees`，不碰 issues/PR 端点，所以 41.6% 不会
进入 6.2%/1.0%；确认“偏差没有固定方向”是最关键的一点；确认作者自我回复问题；给出如扩展为互动指标时的
过滤链（丢掉带 `pull_request` key 的条目、丢掉评论者=条目作者的评论、再计数）；并原样交出预注册
decision rule（<1% / 1–5% / >10%）。

回复文案：`work/share-paste/devto-reply-18.md`（**已由人贴出**，API 复核 id `3fejc`，2026-09-22T22:29:05Z，
parent `3fei6`）。

### 第 3 篇 anp2network 四轮（2026-09-19 → 09-22，**全部回复已贴出**）

线程链路：`3f932`（truncated 提醒）→ `3f948`（我方 5/1,742 实测）→ `3f9ck`（anp2network：假阳性是类别、需逐命中准入规则）
→ `3fb9g`（我方：65 paths / 65 distinct SHA、vendored 上游核对）→ `3fbc9`（anp2network：dedup 只到比较集、要 per-path disposition）
→ `3fbdd`（我方 reply-12：逐路径 disposition 与 content/posts 假阳性）→ `3fdf6`（anp2network：六列里五列来自 tree、Label 不是谓词）
→ `3fdfd`（我方 reply-16：实测 **64/65** 可由路径谓词判定、1 条需内容谓词）。

reply-16 的关键实测：框 A 命中 65 paths / 51 repos / 65 SHAs；路径谓词覆盖 root 46 + first-party nested 17 + vendored 1；
唯一需要内容门的是 `coderanger/coderanger.net` 的 `content/posts/agents.md`（blob `8aa4b8c0…`，11,786 B）。
把范围从 active 扩到**全缓存框**：1,742 棵可用 tree、75 个 AGENTS 路径、61 仓、74 distinct SHA，content-like 路径仍是 **1**。
建议 ledger 字段：`path_class` / `rule_id` / `content_predicate` / `counted`；vendored 可用“解析模块路径 + 上游 blob SHA 比对”机械化。
文案：`work/share-paste/devto-reply-07.md`、`devto-reply-12.md`、`devto-reply-16.md`。

### 第 3 篇第五/六条外部评论：glenallen 两轮（2026-09-21，**两轮回复已贴出**）

两轮评论均从 **adoption vs effectiveness** 切入。第一轮 `3fc13`（09:40:02Z）提出更有价值的下一步是
**decision impact**：AGENTS.md 使 agent 行为改变的频率，以及这种差异是否避免真实错误；并担心更详细的
说明只是增加上下文。第二轮 `3fcdk`（14:23:18Z）回应我方 `3fcd4`，认可三臂设计与等长无关文档控制，
并追问随机结果会证明 charter 改变决策，还是只改变合规而不改善最终产出。

**回复口径**：如实区分 presence / use / effect；说明当前三臂比较的是最终产物而非逐决策遥测，
只能用 `T vs C2` 差距识别 charter 特异效应。若 T 只降机械违规而返工与盲评不改善，即
“合规但最终产出未变”；若 T 优于 C1 但只等于 C2，则只是通用上下文效应。仪表轨最新实测：
105 个真实任务、125 条适用规则、3 条违规，条目级合规率 **97.6%**，任务级违规 **2/105**，
平均返工 **0.39** 轮；该轨非随机且无 counterfactual，只作观察与优先级判断，不当因果证据。
两轮回复均已由人贴出并经 API 复核：`3fcd4`（09-21 14:00:42Z）、`3fd3n`（09-22 00:38:31Z）。
文案：`work/share-paste/devto-reply-14.md`、`devto-reply-15.md`。

### 第 3 篇第四条外部评论：florian131313（2026-09-20，**回复待贴**）

`florian131313`（id `3faof`，293 字符，17:37:13Z）：认为存量 1.0% 是"墓碑在说话"，工具默认应看
active rate；并指出 `CLAUDE.md` 5.4% 与 `AGENTS.md` 6.2% 相邻，建议双读两个文件名、其余视为本地家规。
**只读复算**（`work/prevalence.py report`）：`CLAUDE.md` 确为 **44/817 = 5.4% [4.0, 7.2]**，
与 `AGENTS.md` 51/817 = 6.2% [4.8, 8.1] 区间重叠；交叉 18 双有、26 只 `CLAUDE`，双读并集
**77/817 = 9.4% [7.6, 11.6]**。**工具现状**：CLI/Action 已支持多路径（Action `path: AGENTS.md CLAUDE.md`），
指针已跟随；但默认仍是 `AGENTS.md`，是否把 `CLAUDE.md` 纳入正式数据集按 D40 属版本化决策，不擅自承诺。
回复文案：`work/share-paste/devto-reply-11.md`。

### 第 3 篇第三条外部评论：salparvez（2026-09-20，**回复待贴**）

`salparvez`（id `3fak0`，822 字符，15:27:09Z）：他们的文件属于那 6.2%，但自认"几乎没有禁令"——
写的是**怎么读这个仓库**（证据档位跟主张走、仓库推导物先算最低档、推荐前先说明对面是谁），
并**明示请求跑分类器**（`MLSystemsRI/ml-systems-public`）。**本轮实跑**（远端 4,761 B，
与本机副本 sha256 一致）：`compare` 判 **3/9**（`overview`×1 / `boundaries`×3 / `agent_meta`×1），
7 节里 5 节有标签，无标签的两节 1,517 B（**全文 31.9%**）；`content_mode=rule`（关键词密度代理，
`do not`×4 + `never`×2）；`refs` 识别 9 个指针、**8 个在仓库 HEAD 存在**（`robots.txt` 是正文提及，
已知假阳性）。**定性**：不是召回漏判，是**作用域边界**——九类量"agent 在仓库里该做什么"，
该文件写"主张该怎么被读"（证据档位/来源身份），故记为 `LIMITATIONS.md` §28，按 D42 不新开维度。
回复文案：`work/share-paste/devto-reply-10.md`。

### 第 3 篇的两条外部评论：frankchu / mthburnsbarberweb（2026-09-19，**回复已贴出 09:38/09:39 CST**）

两条都指向「活仓库里的死 AGENTS.md」：`frankchu`（id `3f9ff`，773 字符）自查了自己那份
（16,230 字符 / 4 个带日期标题，只因"只增不删"），并问有没有**外部信号**区分活文件与死内容；
`mthburnsbarberweb`（id `3f9j4`，556 字符）判断 active-but-stale 比 tombstone
更危险、量级可能更大。**实测答案**（`work/active_stale_check.py`）：523 个 active 仓库里
52 个（9.9%）AGENTS.md >180 天未动、113 个（21.6%）>90 天未动，而 >90 天未推的仓库只有 33 个
—— 两个阈值下“活仓库死内容”桶都更大；带日期标题无区分力（0.7% vs 1.9%）。
**两条回复已由人贴出并经 API 复核**：`frankchu` 下 `3fa0i`（01:38:44Z），
`mthburnsbarberweb` 下 `3fa0j`（01:39:40Z）。
回复文案：`work/share-paste/devto-reply-08.md`（frankchu）、`devto-reply-09.md`（mthburnsbarberweb）。

### 第 2 篇的两条外部评论（2026-09-14，**回复已贴出 14:19Z**）

1. **`alexshev` @ 13:35:35Z（309 字符）**：给出比我们更干净的判据 ——
   *"whether each instruction changes a decision at the moment it matters"*，
   并主张"known failure modes + trigger/consequence/recovery"比一长串通用告诫有用。
   → 回复 `work/share-paste/devto-reply-03.md`（944 字符）：承认他的措辞更好、
   交底"这条我测不了（规则分类器只数类别）"，并补一个可查事实：语料库里 8 份 9/9 全中的文件，
   最短的只有 **7.7 KB**（`dbeaver/dbeaver`）——九格填满 ≠ 每格都能改变一次决策。
2. **`raknaos` @ 13:42:27Z（760 字符，本轮最值钱的一条）**：他**真拿尺子量了自己的文件**
   （"I just re-read it against your ruler"），并问两个具体问题：
   - 三仓库清单测试**有没有在已经 9/9 的文件上跑过**，还是只在不及格的样本上？
     → **当晚实测**：`brief` 对 9/9 文件只打 `All nine categories covered - nothing to add.`
     （`dbeaver/dbeaver` 7674B、`graykode/abtop` 21544B、`browser-use/browser-use` 38463B 三份）——
     即**清单是地板不是审阅者**；顺带交底 `agent_meta` 那个洞（照 `brief` 槽位名写标题，
     `compare` 会报 8/9，见 `work/case-rmas-v3.md` §3）。
   - 坑的缺口是**写作习惯还是复核习惯**（把复盘当事后必产物的团队这一格得分更高吗）？
     → 用唯一能测的代理变量实测：指向知识库/规则目录（`hard_route`）的章程
     **24.7%（19/77）** 写了 `gotchas`，其余 **11.6%（51/439）** —— **2.12×**，
     Fisher 双尾 **p=0.0037**，按体量四分位分层后四个分位都是前者更高（Q1 20.0/5.6｜Q2 10.0/7.3｜
     Q3 26.3/13.6｜Q4 33.3/21.9）。边界：代理变量测的是"指向外部载体"的写法而非复盘制度；
     横截面、方向未知；有 `gotchas` 一节 ≠ 里面写的是坑。
   → 回复 `work/share-paste/devto-reply-04.md`（1987 字符），末尾请他把自己那份文件跑一次
     `compare`（判据 6 缺的就是"非作者使用者"，他自称有 agent 文件）。

### 🔴 私库案例的外发口径（2026-09-14 定，**先看这条再写任何案例文**）

`rmas-v3` 是**私库**（`gh api repos/janzong/rmas-v3` → **404**；对照 `agent-charters` → `private=false`）。
所以"拿 rmas-v3 当第二个案例"这件事，有三层限制，别只记第一层：

| 不能做 | 为什么 |
|---|---|
| 不放仓库链接 / 不写仓库名 | 私库链接对外是 404/403；写名字也只是暴露存在 |
| **不整段外发章程正文**（`/tmp/rmas-v3-AGENTS.md`） | 这不是代码，是一张**内部生产系统地图**：主机代号 `148`、内部智能体 `Hermes`、内网端口 `18100/18180`（生产）与 `8002/4000`（本地）、`.env` 字段名（`SECRET_KEY`/`ADMIN_USERNAME`/`ADMIN_PASSWORD`/`DATABASE_URL`…）、生产库位置与 `deploy/`+`docs/DEPLOY.md` 流程、三处版本号不一致的具体数字 |
| 不贴具体条目清单 | `.gitignore` 第 4 行的 `null`、根目录 `node_modules` 无 `package.json` 这类细节组合起来可反推项目结构 |

**能发的是案例复盘**（`work/case-rmas-v3.md`），它讲的是**工具行为**不是项目：写成
"a private FastAPI + React internal project" 这种抽象主体即可。全文只需脱敏两处：
①`148 上 git pull 不补依赖` → "生产机上 `git pull` 不补依赖"；
②镜像核验段的 `/home/janz/workspace/rmas-v3/...` 路径与顶层条目清单 → 用通用占位。
**核心结论（`compare` 认不出自己的槽位名 `agent_meta`、`refs` 镜像核验法）是工具通用的，可全发。**

**第二条外部反馈（2026-09-14 13:04:20Z）**：`reidmarlow`（564 字符，第一篇下第 2 条顶层评论）。
他独立提出**环境漂移类失败**才是多 agent 仓库真正的摩擦点——"an unpinned CLI tool behaving
differently in a subshell or a rate limit on an unmocked internal service … it loops until context
runs out because the repo itself contains no evidence of why the command broke"。**这正好命中实测的
那 8% 桶**（`work/gotcha_origin.md`：58% 读代码可得 / 34% 不是坑 / 8% 只能靠经历）。
回复文案 `work/share-paste/devto-reply-02.md`（**已贴出 13:26Z**），补了两点：①`13.6%` 这个数**高估**了
真正被写下来的经验知识（章节罕见 + 内容大半不是坑）②机制=**自证失败 vs 非自证失败**。

### 首条外部反馈（2026-09-14 12:41Z，发布后 18 分钟）

`jo-do` 评论（484 字符），大意：85.7% 禁令 / 13.6% 坑 这个比例和他在一个"主要给 agent 用的
public board"上的观察一致；*"The gotchas are the file"*；称赞 rule-based 分类是
*"auditable beats clever"*。**回复文案：`work/share-paste/devto-reply-01.md`（已贴出 12:49Z）**，
回复里把那句"只被作者测过"如实交代，并请他在自己的 AGENTS.md 上跑 `compare`
——这正是判据 6 缺的那一格。

### 英文读者现在真的能用 CLI（2026-09-14 晚，工具侧 0.3.3）

发帖前发现一个自相矛盾的地方：渠道是英文的，但 `compare`/`stats`/`refs` 的输出
**全硬编码中文** —— 读者照抄文章里的命令，看到的是一屏中文。已修（commit `b30a39f`）：
五个命令都出中英两版，默认跟 `LANG`/`LC_ALL` 走，也能 `--lang en` 强制。

**对分享文案的影响**：文章正文里的示例输出仍是中文口径（当时机器就是中文），**不用改**
（示例本来就是"真实输出"的截图式引用）；但**回复评论时可以直接说**：英文环境跑出来就是英文，
中文环境的清单文案也还是中文（中文输出与改造前逐字一致，已逐命令 diff 验证）。
顺手记一条**读者可能踩的坑**：国内网络直连 PyPI 拉 pandas/pyarrow（62 MB）**会断流/哈希不符**
（2026-09-14 实测 3/3 失败），加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` 才稳（实测 9 秒）。

### 可复用的下一步：GitHub Action（2026-09-14，`6fa8a8e`+`f5ae512`）

`uses: janzong/agent-charters@v1` —— PR 里跑 `compare` + `refs`，结果进 job summary，
**默认只报告不拦**（闸门由使用者在自己 workflow 里显式开，理由见 `STATE.md` D34）。
本仓库自己也在用，徽章挂在 README 首屏。

**对分享的用法**：这是回答"我怎么持续用上"的现成答案——回复评论时可以直接给这五行 YAML，
比再让人手动跑一次命令更有粘性。**注意**：这也是唯一能自动落进别人仓库里的入口
（判据 6 的"反复使用"），但目前**只有本仓库在跑**，别人装没装要看 GitHub 的
`network/dependents` 或搜 `uses: janzong/agent-charters`。

**验证用的 fixture（别误认成真实用户）**：`janzong/agent-charters-action-test`
是 2026-09-14 为验证 `@v1` 建的一次性消费方仓库（`STATE.md` D35）：两个 job ——
`report-only` 走文档承诺的默认形态（绿）、`enforce` 故意要类别（红 + exit 1）。
**它跑起来不算判据 6**。再要复验 tag：`gh workflow run charter.yml --repo janzong/agent-charters-action-test`。

### 第 4 篇 hannune：zero-contributor 身份（2026-09-23，**回复已贴出**）

`hannune (Tae Kim)`（评论 id `3felf`，2026-09-23T01:07:49Z，255 字符，顶层评论，文章 id `4719293`）：
他跑过 3-agent 协调任务，多出的 agent 基本只是复述前两者的结论；问 zero-contributor 是同一批 agent
一贯缺席，还是跨 run 轮换。

**实测口径**（同 6 个 run 归档，逐 agent）：2-agent Alice `[0,1,0]`（2/3 为 0）、Bob `[2,2,0]`（1/3）；
4-agent Alice `[0,1,2]`（1/3）、Bob `[1,1,1]`（0/3）、Carmen `[0,0,1]`（2/3）、Dan `[2,0,1]`（1/3）。
结论：缺席者跨 run 轮换，不是固定同一人；最接近“一贯”的是 Alice（2-agent）与 Carmen（4-agent）各 2/3；
n=3、persona 目标不同，无法区分 persona 效应与采样噪声；无 3-agent 条件，无法验证 echo。
回复文案：`work/share-paste/devto-reply-20.md`（**已由人贴出**，API 复核 id `3femg`，2026-09-23T02:18:56Z，parent `3felf`）。

### 第 4 篇（负结果文章，id `4719293`）：reidmarlow 责任扩散（2026-09-22，**回复已贴出**）

`reidmarlow`（评论 id `3feji`，2026-09-22T23:06:33Z，616 字符，顶层评论，文章 id `4719293`）：
认为 zero-contributor 从 1.0→1.33 是表格里信息量最大的行；对称多 agent 循环会出现“责任扩散”
（每个 agent 读部分状态、假设别人会补缺口、返回 trivial action）；同一失败模式见于代码评审
（无互斥文件边界的四人评审 = 四份浅层 nitpick、零深度 bug 捕获、双倍 token）；建议互斥文件边界/分区任务。

**实测口径**（`runs/concordia/protocol-v15-{2,4}agent-r{1,2,3}`）：zero-contributor 2-agent `[1,0,2]`、
4-agent `[2,2,0]`，均值 **1.000 vs 1.333**；两组各 1/3 complete success；**平均贡献/agent 都是 0.833**
（5/(3×2) 与 10/(3×4)）；每人达标需要 **1.5 vs 1.25**；mean cost USD 0.028798 vs 0.060906，成本比 **2.115×**；
participant coverage 六个 run 全 1.0（每个 agent 都行动并返回整数 choice，zero 是“行动后选 0”而不是“没行动”）。
代码评审类比没有实测数据，未外推；互斥边界是新协议，本轮不回答。
回复文案：`work/share-paste/devto-reply-19.md`（**已由人贴出**，API 复核 id `3fel5`，2026-09-23T00:43:04Z，parent `3feji`）。

### 第 5 篇（治理审计文章，2026-09-23 **已上线**）

- dev.to id `4720590`，<https://dev.to/janzong/your-agent-run-passed-can-you-prove-it-was-allowed-3d5i>，
  published `2026-09-23T03:03:42Z`，tags `ai, agents, governance, opensource`；
- 主题：policy-as-code 审计；`max_cost_usd` / `max_calls`、`required_artifacts` +
  `required_artifacts_mode`、`forbidden_markers`，输出 canonical `audit_hash`；
- 实测：13 个 GenMentor run —— 默认 structured 合同 **0/13**（`missing_artifact` ×13、
  `cost_exceeded` ×1，`replay-8of8-20260920-a` cost `3.9529266` > `0.60`）；声明 GenMentor
  合同 **13/13**；audit_hash `2c122c4f…` / `368b75a0…`；
- 文章草稿：`work/share-paste/devto-article-05.md`；`series` 字段经 API 未挂上（返回 `null`），不影响正文。

### 第 5 篇 mihai_leanzero policy pinning（2026-09-23，**回复已贴出**）

`mihai_leanzero`（评论 id `3ff4f`，2026-09-23T06:36:52Z，519 字符，顶层评论，文章 `4720590`）：
认可 policy-vs-data 框架；问 `audit_hash` 是否覆盖 policy.json 内容；若只覆盖 findings，失败后改 policy
重跑可得到干净 hash、契约变更无痕迹；建议把 policy 钉在 run artifacts 旁。

**改动前后实测**：改动前 payload 仅含 `policy_keys`（键名）+ artifacts 契约值，max_cost 0.60 vs 100.0
同 hash `d39ac5fe…`；改动后 `audit_root` 把完整 canonical `policy` + `policy_sha256` 纳入结果，
两者变为 `79b25b9a…` vs `385f8ed6…`；fixture audit_hash `b304f294…`、policy_sha256 `cda4f1bb…`；
`audit --output` 写出 9 键 pinned JSON；13-run 结果不变（默认 0/13、GenMentor 13/13）。
回复文案：`work/share-paste/devto-reply-21.md`（**已由人贴出**，API 复核 id `3ffmc`，2026-09-23T14:20:30Z，parent `3ff4f`）。

### 2026-09-24 三条回复已贴出（reply-22/23/24）

| 回复 | 对象 | 文章 | API 复核 | 时间 | parent |
|---|---|---|---|---|---|
| reply-22 | axiru | `4720590` | `3ffpd` | 2026-09-23T15:14:27Z | `3ffnf` |
| reply-23 | nomad-link-id | `4719293` | `3fgje` | 2026-09-24T00:50:20Z | `3ffpf` |
| reply-24 | aifrontierpost | `4719293` | `3fgj9` | 2026-09-24T00:45:41Z | `3fg6k` |

reply-22：policy hash 已钉进同一 receipt（9 键含 `policy` + `policy_sha256`），pre-call allow/hold/deny 是另一层、未实装。
reply-23：cost per complete success 2-agent `0.0863948`、4-agent `0.1827186`、≈2.115×；scorer/gold 冻结。
reply-24：strict-JSON/no-reasoning 隔离结构 vs 能力；reasoning arm 未跑，只谈设计与边界。

## 6. 发完之后

- **别刷数据**：star 少不要紧，有一个人用上了就是判据 6 的突破
- 记下所有"这个标错了"的反馈 → 直接进下一版分类法修订清单
- 如果有人在别处引用/分析这份数据 → 立刻记进 STATE.md 第 2 节"外部信号"，
  这是比 star 更硬的证据
- **已发布的数字更正要及时、要写清"我怎么错的"**：§7 是三站的更正话术；
  更正本身也是可信度的一部分，藏起来比说错更伤

---

## 7. 数字更正话术（三站，2026-09-13 定稿 —— ✅ §7.1–7.3 三站均已贴；✅ §7.5–7.7 留出集评论 **2026-09-15 三站全部已贴**（用户确认））

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


### 7.5 知乎（留出集，2026-09-13 新增，✅ 2026-09-15 已贴）

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

### 7.6 开源中国（留出集，追加评论，≤500 字，✅ 2026-09-15 已贴）

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

### 7.7 掘金（留出集，追加评论，✅ 2026-09-15 已贴）

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

### 🔑 dev.to key 卫生（2026-09-14 第二次踩到，**照这个做**）

**规则**：key 只存在于 `~/.devto_api_key`（0600）。**不要贴进对话框** ——
对话内容会进模型上游的请求日志、也会落到本机 rollout 文件，而 dev.to 的 key
是**账号级**的（能改/删文章），比一个只读 token 值钱得多。

**为什么反复强调**：2026-09-14 同一天发生了两次 —— 先是一把 key 被贴进对话（随即轮换），
然后**新 key 又被贴了一次**。第二次的代价是：同一账号上两把 key 同时有效，
其中一把已经在对话历史里，必须再轮换一次并把旧的全部吊销。

**自己写文件（key 不进对话、不进 shell 历史）**：
```bash
read -rsp 'dev.to key: ' K && printf '%s' "$K" > ~/.devto_api_key \
  && chmod 600 ~/.devto_api_key && unset K && echo " 已写入 $(wc -c < ~/.devto_api_key) 字节"
```
**吊销旧 key**：<https://dev.to/settings/extensions> → *DEV Community API Keys* → 删掉不用的那几把。
**判断某把 key 还活着**（只读调用，不打印 key）：`GET https://dev.to/api/users/me`，
200 = 还活着、401 = 已失效。
**验证新 key 装好了**：`systemctl --user start devto-watch.service`（读文件里的 key；
无新评论时静默退出 0），或 `python3 work/share-paste/watch_devto.py` 看读数表。

**结局（2026-09-14 收口）**：那把**旧 key 已由人在 dev.to 上删除**，账号上只剩一把。
本机落点与复核（都只报状态，不打印 key）：

- `~/.devto_api_key` 24 字节（与当前这把 key 长度一致）、0600；`GET /api/users/me` → **200 `janzong`**。
- 盯梢服务读同一份文件、跑通：`watch_devto.py` 打出读数表后"无新评论"退出。
- **无残留**：`~/.bashrc` / `~/.profile` / `~/.bash_profile` / `~/.zshrc` / `~/.config/environment.d/*`、
  仓库（排除 `.git`/`.venv`）、`~/.local/state`、`~/.config/systemd/user` 里都搜不到旧 key；
  systemd 单元里**没有内联 key**（只 `Environment=PATH`，key 走文件）。

⇒ **本机只留一把 key、链路单一**；下次再换只改这一个文件（`publish_devto.py` 与
`watch_devto.py` 共用它），然后 `systemctl --user restart` 不需要（oneshot timer 每次重读）。

---

## 8. 发 PyPI（Trusted Publishing —— **不存任何 token**，2026-09-14 装机）

**目标**：让 `pip install agent-charters` 直接可用（此前只有 `pip install git+https://…`，
README 上那句"尚未发到 PyPI"就是它）。**顺带**：PyPI 是英文渠道读者最容易找到本项目的入口。

**为什么不用 token**：PyPI 支持 **Trusted Publishing（OIDC）**——GitHub Actions 用 job 的
OIDC 身份向 PyPI 换一次性上传凭据，仓库里**一个字都不用存**。相比 API token：
不会有(token 落到对话/日志/`~/.pypirc`)的泄露面，也不用轮换。本项目已有过两次 key 卫生事故，
这条直接绕开整类问题。

### 8.1 一次性人工前置（只有这一步要人在网页做）

1. 确认 PyPI 账号（本机实测 `https://pypi.org/user/janzong/` → **200**，账号已在）且**开了 2FA**（PyPI 强制）。
2. 打开 <https://pypi.org/manage/account/publishing/> → **Add a new pending publisher**
   （项目还没发过，所以是 *pending* publisher），**逐字照抄**：

   | 字段 | 值 |
   |---|---|
   | PyPI Project Name | `agent-charters` |
   | Owner | `janzong` |
   | Repository name | `agent-charters` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

   ⚠️ 五个字段**任一不符就 403**（PyPI 只认这条精确匹配，报错信息很不友好）。

### 8.2 触发（两种，都不用 token）

- **GitHub Release**：发一个 tag 与 `pyproject.toml` 的 version 一致的 Release（`published` 时触发）；
- **手动**：`gh workflow run publish.yml --repo janzong/agent-charters`。

workflow 在 `.github/workflows/publish.yml`，三道闸：

1. **tag 与版本必须逐字一致**（Release 触发时；不一致直接拒发）；
2. **已在 PyPI 上就跳过**（同一版本号只能传一次，重跑必然 400；这道闸让 Release 可以随便发）；
3. **上传前 `twine check --strict`**（元数据不合规就停在 runner 上，不进 PyPI）。

### 8.3 发下一版

1. 改 `pyproject.toml` 的 `version`（⚠️ **PyPI 上已发布的版本号不能重用**，只能往上升）；
2. 提交、推双端；
3. 要么发一个同名 Release，要么 `gh workflow run publish.yml`。

### 8.4 本地预演（不想等 CI 时）

```bash
python3 -m venv /tmp/ac-buildenv && /tmp/ac-buildenv/bin/pip install build twine \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
cd <repo> && /tmp/ac-buildenv/bin/python -m build --outdir /tmp/ac-dist .
/tmp/ac-buildenv/bin/python -m twine check --strict /tmp/ac-dist/*
```
⚠️ **别在项目 `.venv` 里造**：仓库里有个 `build/` 目录，`importlib.util.find_spec("build")`
会**误报"build 已装"**（实测踩过）。

**审过一遍的产物长什么样**（0.3.3 本地实测）：wheel 只含 `agent_charters/`（9 个 .py + 4 份
parquet 语料），sdist 额外含 `tests/` 与 `LICENSE`；`work/`、`data/raw/`、
`STATE.md`/`SHARE.md` **都不在里面**；元数据 `Metadata-Version: 2.4` +
`License-Expression: MIT` + 4 条 `Project-URL`。

### 8.5 已知缺口（0.3.4 后剩下的）

- ~~PyPI 页面上的 long description 是中文 README~~ → **0.3.4 已修**（见 §8.7）：
  `readme` 指向 `README.en.md`。**GitHub 首页仍是中文 README**（有意：
  沿用既有外链与中文渠道流量），两个 README 顶部互相带语言切换。
  ⚠️ **但 0.3.4 的相对链接只清了"正文"，漏了顶部那条切换器** ——
  PyPI **不重写相对路径**，`[中文](README.md)` 会解析成
  `pypi.org/project/agent-charters/README.md` → 404 → 跳回搜索页。
  0.3.5 修掉（§8.8），并加测试钉死。**教训：改完只数了 `](LIMITATIONS.md)` 一种形态，
  没扫全量链接** —— 复验口径要按"全量外部引用"取，不能只盯已知案例。
- ~~**依赖从国内直连 PyPI 会断流**（pandas + pyarrow ≈62 MB，实测 `exit=124`）——装的时候加清华镜像~~
  → **0.4.0 从根上解决**（§8.9）：运行时依赖归零，随包语料改成 `jsonl.gz`（标准库读）。

### 8.9 第四版 `0.4.0`（09-15 晚）—— 装包不再拖 62 MB

**要解决的问题**：`pip install agent-charters` 会连带装 pandas + pyarrow（≈62 MB）——
只为读一张 **550 KB** 的表。国内直连 PyPI 拉这两个包实测 `exit=124`（断流），于是
"看到 → 用上"这条链的最后一米经常断在这里；GitHub Action 每次运行也要多下 62 MB。

**做法**（`D37`）：

| 面 | 之前 | 之后 |
|---|---|---|
| 随包语料 | `agent_charters/data/*.parquet`（4 个版本，约 222 KB） | `agent-charters-<DS>.jsonl.gz`（**46 KB**，只带当前版本） |
| 运行时依赖 | `pandas>=2.0` + `pyarrow>=14` | **空**；新增 `[parquet]` 附加依赖给读/写 parquet 的人 |
| wheel | 219,591 B（0.3.3） | **104,143 B** |
| 数据读法 | `pd.read_parquet` | 标准库 `gzip` + `json` → `Corpus`（行＝dict） |
| 发布格式 | parquet（不变） | parquet（不变）+ jsonl，`data/processed/` 与 `SHA256SUMS` 原样 |
| CI 装包 | `-e ".[test]"` | 同；`tests` job 才装 pandas |

**关键约束：随包副本与发布副本仍是同一份数据** —— `agent-charters-v0.5.jsonl.gz` 解压后
与 `data/processed/agent_charters_v0.5.jsonl` **逐字节相同**（测试钉住），压缩用
`gzip.compress(..., mtime=0)` 所以 gz 里不带打包时间（不带时间戳那条由测试钉住）。
⚠️ **别把"字节可复现"写进承诺**：`gzip.compress` 的输出是 zlib 的实现细节，同一个输入在
不同 Python 版本上会给出**不同的合法 gzip 流** —— 0.4.0 首次 CI 就在 py3.10 上红了（py3.12 绿），
因为我一开始写的断言是"再压一遍字节相同"。**要钉的是内容，不是压缩帧。**

**复验**（干净 venv，`pip list` 里只有 `agent-charters==0.4.0`，`pandas`/`pyarrow` 均 `None`）：

- `agent-charters stats/show/compare/brief` 全部正常，且**数字与 parquet 路径逐字节一致**
  （`boundaries 85.7%`、中位数 6689 B / 均值 10740 B / 最大 154006 B、平均标签 4.7）；
- 指了 `.parquet` 又没装 `[parquet]` → 一行人话 + `exit 2`（不是 traceback）；
- 本地 `pytest` **168 passed**；CI（py3.10/3.12）**150 passed / 18 skipped**。

**顺带修掉的两处**：①`AGENTS.md` 里"包**不发 PyPI**"这句已经过期（0.3.3 就发了），
趁这次改文档一并订正；②`--data` 原先只认顶层位置（`agent-charters --data X stats`），
写在子命令后面会报 `unrecognized arguments` —— 现在两个位置都能用。

**发布实况**（run `34971331591`，三 job 全绿；CI `34971581434` 全绿）：

| 项 | 值 |
|---|---|
| wheel | `agent_charters-0.4.0-py3-none-any.whl` **104,851 B** ｜ sha256 `9754f3716916…4b6f4c` |
| sdist | `agent_charters-0.4.0.tar.gz` 138,190 B ｜ sha256 `10e9367b6217…f969a4` |
| 元数据 | **`requires_dist` 里没有无条件依赖**，只剩 `extra == "parquet"` / `extra == "test"` 两组 |
| 独立复验 | 从**默认索引** `pip install agent-charters==0.4.0`：**4.3 秒**装完，`pip list` 里只有 `agent-charters==0.4.0`（没有 pandas/numpy/pyarrow），换到无关目录 `stats`/`compare` 正常 |

⚠️ **这条踩坑（CI 抓的）**：我先写了一条"再压一遍 gzip 字节必须相同"的测试 —— py3.12 绿、
**py3.10 红**。`gzip.compress` 的输出是 zlib 的实现细节，同一个输入在不同 Python 版本上
就是两个不同的合法 gzip 流。**要钉的是内容，不是压缩帧**；现在只钉"gz 头里没有时间戳"
（与实现无关）。

### 8.10 第五版 `0.4.1`（09-15 深夜）—— 工具会**跟随指针**了

**为什么发**：这是 0.4.0 之后第一个**用户可见的行为变化**（`D40`）——`compare` / `brief` /
GitHub Action 遇到"这份章程本身就是指针"的文件时**跟过去判目标**，而不是报 0/9。
实测底盘：791 份根级章程里 **111** 份符号链接、**75** 份纯指针（中位 **11 字节**）、69 份原本报 0/9。
（数据、边界与实现口径：`work/audit/pointer-census.md`、`LIMITATIONS.md` §25。）

| 项 | 值 |
|---|---|
| 触发 | `gh workflow run publish.yml`（**沿用前四版的 workflow_dispatch**，不建 tag —— `vX.Y` 是数据集 tag 命名空间，别混，见 D35） |
| run | `34987867624`，三 job 全绿（preflight / build / upload OIDC） |
| wheel | `agent_charters-0.4.1-py3-none-any.whl` **111,868 B** ｜ sha256 `059d3e1c76590640…` |
| sdist | `agent_charters-0.4.1.tar.gz` 147,610 B ｜ sha256 `9793d0452ac31730…` |
| 元数据 | `requires_dist` **仍无无条件依赖**（只剩 `extra == "parquet"` / `extra == "test"` 两组） |
| 页面 | `README.en.md` 照旧英文渲染；语言切换器是**绝对地址**（0.3.5 那个 404 没有回归） |

**独立复验（干净 venv，默认索引，不经任何镜像）**：
`pip install agent-charters==0.4.1` **约 2 秒**装完、`pip list` 里只有它自己；
`agent-charters --version` → `0.4.1 ｜ dataset v0.5`；拿一份 11 字节的 `CLAUDE.md`（`@AGENTS.md`）
跑 `compare CLAUDE.md --lang zh` → 输出 `↪ CLAUDE.md 是指针（AGENTS.md）——已跟随…`，**不是 0/9**。
下载下来的轮子 sha256 与 PyPI 公布值一致；**内容哈希（排除 `RECORD`）与本地构建逐字节相同**。

⚠️ **别把"轮子字节可复现"当承诺**：本地 `python -m build` 出的轮子哈希与 PyPI 上的**不同**
（zip 存了 packing 时间戳），但解开后的内容一致。和 §8.9 那条 gzip 坑同一个道理 ——
**要钉的是内容，不是容器帧**。

### 8.6 首发实况（2026-09-15，`agent-charters 0.3.3`）

**结论：已上线** —— <https://pypi.org/project/agent-charters/>。对外文案现在**可以**写
`pip install agent-charters`（此前只能用 git 直装）。

| 项 | 值 |
|---|---|
| 触发 | `gh workflow run publish.yml` → run `34959442365`，**preflight / build / upload 三 job 全绿** |
| 轮子 | `agent_charters-0.3.3-py3-none-any.whl` 219,591 B ｜ sha256 `b5b8f631ce00998037639e34fdfd5dc86b6837ba9ae36cbb6ed87bd68f3131d3` |
| sdist | `agent_charters-0.3.3.tar.gz` 243,557 B ｜ sha256 `bdb567638e5e498bd6bbecd901cc182dce4aaa36450b5c7cc0d5ea76dddf325e` |
| 元数据 | MIT（SPDX）｜10 条 classifier｜4 条 Project-URL｜`requires-python >=3.10`｜long_description＝README 8837 字符 |
| 账号侧 | 2FA＝**TOTP**（Mac「密码」App 存码；已另存 recovery codes）；pending publisher 五字段照 §8.1 填 |

**独立复验**（关键：**不看 CI 自己的输出**）

1. 从**默认索引**（真 PyPI，不是镜像）`pip download --no-deps agent-charters==0.3.3`
   → 下到轮子，`sha256` 与上表**逐字节一致**（证明 PyPI 上那份就是我们构建的那份）；
2. 干净 venv 实装 → **换到无关工作目录**跑 `agent-charters compare <仓库外的文件>` 输出 8/9、
   `stats` 报语料库 558 份 ⇒ 语料库确实打在包里、不依赖仓库目录；
3. 中英双语输出正常（`--lang zh` / 默认 en）。

**仍未解决**：依赖（pandas + pyarrow ≈ 62 MB）从 251 **直连 PyPI 仍会断流**（本轮实测
`pip install agent-charters` 完整装超时 `exit=124`，卡在 pyarrow 50 MB 那步）⇒ 国内装的时候
依赖走清华镜像是常态操作，**不是包的问题**（包本身 219 KB，几秒就下来了）。

### 8.7 第二版 `0.3.4`（同日晚，`run 34966005314`）—— 把 PyPI 页面换成英文

首发（0.3.3）当天就暴露两个**只有真发上去才会看见**的问题，0.3.4 一起修掉：

| 问题 | 为什么首发时没发现 | 0.3.4 的做法 |
|---|---|---|
| PyPI 页面的 long description 是**中文** README | 本地看不出"页面给谁看" | 新增 `README.en.md` 全文翻译，`readme` 指向它 ⇒ GitHub 首页留中文、**PyPI 是英文** |
| README 里 **18 条相对链接**在 PyPI 上 404 | PyPI 不重写相对路径，GitHub 会 | 英文版链接**全部绝对化**（相对链接 0 条，只剩语言切换那条） |

复验：`/pypi/agent-charters/0.3.4/json` 的 description **16,900 字符**、含 `a structured corpus`、
`](LIMITATIONS.md)` 计数 **0**、绝对链接 22 条；从真 PyPI 升级装好后 `agent-charters --version`
→ `agent-charters 0.3.4 ｜ dataset v0.5`。
⚠️ **这个复验口径有洞**：只数了 `](LIMITATIONS.md)` 这一种形态，**没扫全量链接** ——
漏掉了顶部切换器的 `](README.md)`，用户当天点"中文切换"就退到了搜索页（§8.8）。
**扫描要按"剩下哪些相对链接"取，不能按"我改过的那几条"取。**
（⚠️ `https://pypi.org/pypi/agent-charters/json` 顶层端点有 **CDN 缓存**，刚发完可能还显示旧版本——
要看新版本就查 `.../pypi/agent-charters/<版本>/json` 或 `/simple/agent-charters/`。）

**顺带验证了"已在 PyPI 就跳过"那道闸**（真实运行，不是单测）：0.3.4 发布后**再触发一次**，
run `34966176206` 里 `build` 与 `upload` **都是 skipped**，只有 preflight success。

**发布下一版**：改 `pyproject.toml` 的 `version` → 推双端 → `gh workflow run publish.yml`
（或发同名 Release）。⚠️ **PyPI 上已发布的版本号不能重用**，只能往上升。

### 8.8 第三版 `0.3.5`（09-15 晚，`run 34966958406`）—— 修语言切换 404

**用户报的现象**：PyPI 页面是英文（0.3.4 的预期），但点顶部的**「中文」切换**会**退到 PyPI 搜索页**。

**根因**：`README.en.md` 第 3 行的切换器写的是**相对路径** `[中文](README.md)`。
GitHub 会把它重写成 `github.com/janzong/agent-charters/blob/main/README.md`；
**PyPI 不重写**，原样保留 → 浏览器解析成 `pypi.org/project/agent-charters/README.md` → 404 → 跳搜索。
0.3.4 把正文里的 18 条相对链接都绝对化了，**唯独漏了这一条**（复验时只数了 `](LIMITATIONS.md)`）。

**修法**（`8a39d4c`，双端已推）：

| 改动 | 文件 |
|---|---|
| 切换器改绝对地址（两个 README 互链都改，GitHub 上照常可用） | `README.en.md` / `README.md` 第 3 行 |
| 新增测试：剥掉围栏代码块与行内代码后，`README.en.md` **不许残留相对链接** | `tests/test_smoke.py` |
| 版本一致性测试加钉：`readme` 必须指向 `README.en.md`（防有人换回中文版，重新踩 D33 的坑） | `tests/test_smoke.py` |
| 0.3.4 → 0.3.5 | `pyproject.toml` / `agent_charters/__init__.py` |

**为什么非发版本不可**：PyPI 的 long description 是**上传那一刻的元数据快照**，
不是每次访问去 GitHub 拉——改链接**必须发新版本**才生效。

**复验**（`/pypi/agent-charters/0.3.5/json`，⚠️ 顶层端点有 CDN 缓存、会显示旧版本）：
description 16,952 字符 ｜ `](README.md)` 与 `](README.en.md)` 计数**都是 0** ｜
残留相对链接扫描只剩 `path` 一条，核对后确认它在**行内代码**里（`[text](path)`，是文档举例的
Markdown 指针语法，PyPI 不渲染成链接）⇒ 真实链接全部绝对。
测试本地 **162 passed**；CI `144 passed / 18 skipped`（py3.10 与 py3.12 两套都跑）。

**这条坑的普适形态**：只要 README 会被渲染到**不重写相对路径**的地方（PyPI / npm / crates.io…），
所有链接就必须是绝对地址——包括**看起来像"站内导航"的那几条**。

**同一轮顺手改掉第二处"发布时快照"陷阱**：两个 README 的 PyPI 提示语原本写死
`版本 \`0.3.4\``，而 PyPI 的 description 是上传那一刻的快照 ⇒ **每发一版，页面上的版本号就旧一版**。
改成指向**页面顶部的 PyPI 徽章**（`img.shields.io/pypi/v/agent-charters`，动态读当前版本），
这句话就再也不会过期。⚠️ 提醒：**0.3.5 已经发出去的那份快照里仍写着 `0.3.4`**
（改 README 不会回写历史版本，要等下一版发布才同步）——属于已知且无害的陈旧。

**复验这个页面的两个坑**（都踩过）：
1. `https://pypi.org/project/agent-charters/` 的 **HTML 一律抓不到**——Fastly 反爬会回
   `Client Challenge`（3 KB 的 JS 挑战页：`len(html)≈3038`、搜 `README.md` 得 **0**，
   **别把它当成"页面里没有链接"**）。2026-09-15 实测**四条路都过不去**：
   251 的 curl（含假 Chrome UA）、251 的 **headless Chrome**（PAT 请求 401、`PAT challenge aborted`）、
   **Mac**（经 `2223` 反隧道）的 curl 与 `Chrome --headless=new --dump-dom`（DOM 里 `<title>` 仍是
   `Client Challenge`）、以及两个公共取页代理（`r.jina.ai` 超时、`api.codetabs.com` 522）。
   ⇒ **只有在真浏览器里手工看**。程序化复验只能走 `/pypi/<ver>/json` 与 `/simple/`（这两个不挑战）。
   ⚠️ 推论：**页面里到底渲染成什么样，我们这边看不到**——排查时要么让用户看，
   要么看 JSON 里的 markdown 源（链接是绝对就一定会渲染成绝对锚点）。
2. 顶层 `/pypi/agent-charters/json` 有 **CDN 缓存**；要么查 `<版本>/json`，要么看 `/simple/`。

**再下一版见 §8.9（`0.4.0`，运行时依赖归零）。**
