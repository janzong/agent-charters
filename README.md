# agent-charters ｜ 智能体章程语料库

> **人写给 AI 智能体的书面规约**的结构化语料库。
> 数据集 **v0.5** 覆盖 `AGENTS.md`，共 **558 份**、来自 558 个公开仓库。

## 这是什么

越来越多的软件仓库里出现一种新文件：`AGENTS.md`、`CLAUDE.md`、`.cursorrules`、
`copilot-instructions.md`。它们不是给人看的文档，而是**人写给 AI 智能体的行为规约**。

本项目把这类文件收集起来，做**结构化标注**，用来回答：

- 人到底想让 AI 知道什么？（哪些主题被反复强调，哪些被系统性忽略）
- 规约是"命令"还是"知识"？
- 不同语言、不同规模的项目，写法有什么差异？

## 数据

| 项 | 值 |
|---|---|
| 文件数 | 558（实质内容 518，其中可用于分类统计 516） |
| 仓库数 | 558（已排除 fork） |
| 采集时间 | 2026-09-10 |
| 总字节 | 5.3 MB |
| 每份平均标签数 | 4.7（九类全中的有 8 份） |
| 许可 | 代码 MIT ｜ 数据 CC-BY-4.0 |

> 为什么有两个口径：`is_substantive` 只排掉空壳文件，`is_pointer` 还要排掉
> "正文只是指向别的文件"的转引用文件（**2 份**，v0.4 时是 7 份）。后者
> `categories` 为空**是正确结果**，不该算进分母。所有类别覆盖率都按 **516** 计算。
>
> ⚠️ **版本间覆盖率不可直接比**：v0.2 收紧了 `is_pointer` 口径（分母 507→511，见
> [`LIMITATIONS.md`](LIMITATIONS.md) §10）；v0.3 修掉了标题通道的子串误命中
> （`build_test` 87.9% → 85.7%，见 §11）；**v0.5** 修掉了"代码块里的 `# 注释` 被当成标题"
> （`build_test` 85.9% → **82.8%**，同一批文件里 `section_count` 从 146 降到 92 这种变化都是它）
> 并把 5 份被误判为指针的短章程收回统计口径（分母 511→516，见 §14）。同一批文件、不同规则，
> 数字不可混用。

**不含原文全文**——只发布衍生标注与统计特征。原文版权归各仓库作者。

> **国内访问**：主仓在 GitHub；国内镜像 <https://gitee.com/janzong/agent-charters>（含
> [Release `v0.5`](https://gitee.com/janzong/agent-charters/releases/tag/v0.5)）。数据集也可从
> [GitHub Release `v0.5`](https://github.com/janzong/agent-charters/releases/tag/v0.5) 直接下载（parquet + jsonl）。

## 快速开始

```python
import pandas as pd

df = pd.read_parquet("data/processed/agent-charters-v0.5.parquet")

# 最常出现的主题
from collections import Counter
c = Counter(t for tags in df["categories"] for t in tags)
print(c.most_common())

# 只要实质内容
sub = df[df["is_substantive"] & ~df["is_pointer"]]
print(len(sub))
```

## 类别分布（516 份实质文件，数据集 v0.5 / `ruleset_v0.1.8`）

| 类别 | 覆盖 | 含义 |
|---|---|---|
| `boundaries` | **85.7%** | 禁令、边界、不可做的事（**45.2%** 至少有一个**整节**写禁令） |
| `build_test` | **82.8%** | 构建 / 测试 / 运行命令 |
| `workflow` | 67.1% | 分支、提交、PR、发布 |
| `structure` | 59.1% | 架构、目录与文件组织 |
| `style` | 54.5% | 代码风格、命名、约定 |
| `environment` | 45.0% | 环境、工具链、依赖 |
| `overview` | 32.2% | 项目概览、技术栈、目的 |
| `agent_meta` | 25.8% | 关于 AI 自身行为的规定 |
| `gotchas` | 13.6% | 坑、陷阱、已知问题 |

> 两类并列第一，差距 2.9pp **小于 `boundaries` 的已知假阳性幅度**（正文通式约 3%），
> 不宜宣称严格领先。另外 `boundaries` 有两个口径：**有专门的禁令章节** 45.2%（标题通道），
> **全文任意一处出现禁令语句** 85.7%（含正文的 `Do not …` 通式）。两个数都对，问法不同。
> 详见 [`FINDINGS.md`](FINDINGS.md) §1。

## 命令行工具

装好依赖后（或在仓库根目录直接 `.venv/bin/python -m agent_charters`）：

```bash
# 写章程之前：检查清单 + 可直接粘贴给生成器的提示词
agent-charters brief
# 已有文件：清单会标出你缺哪些，并把缺口写进提示词
agent-charters brief path/to/AGENTS.md

# 全局分布：语料库长什么样
agent-charters stats

# 把你手上的章程与语料库对比——看它缺了什么
agent-charters compare path/to/AGENTS.md [更多文件...]

# 看某个类别的真实写法（按该类别章节数降序）
agent-charters show gotchas --limit 8

# 知识放在哪：章程是自足的，还是把 agent 指去了别处（顺带查断链）
agent-charters refs path/to/AGENTS.md
```

`compare` 是给写章程的人用的：它会指出**语料库里写得最多、而你完全没写的类别**，
以及每个类别在语料库里的覆盖率。中文文件同样适用。

`brief` 是给"要生成一份章程"的人用的，它的依据是实测而不是经验：
11 个仓库的对照实验发现，自动生成的覆盖面**由提示词的形状决定**——
提示词不点名"协作流程"，11/11 份都没写；点名后 3/3 立刻写出。

`refs` 量的是九类之外的另一个维度：**知识放在哪里**。
实测 516 份里，**49%** 的章程会转引别的文件（祈使式"read / 详见 X.md"）、
**15%** 直接指向知识库或规则目录、两者合起来 **54%**——
也就是"一份 `AGENTS.md` 承载全部规约"这个假设，对近一半样本不成立。
v0.2 起这三个数已是数据集字段（`imperative_route` / `hard_route` / `routes_outward`），
可自行复算。
它会同时列出**指向了但找不到的路径**：指错方向比不指更糟，agent 会照着不存在的文件找。
所以 `brief` 输出的是**该问哪些问题**（比例由语料库实时算出），
外加一段可直接粘贴的提示词。拿这份提示词重跑上述仓库，
覆盖从 4–5 类升到 **9/9**（见 `work/auto_vs_human.md` 第 6 节）。

## 文档

**如果你是接手的智能体或协作者，请先读 [`STATE.md`](STATE.md)** —— 项目状态、决策记录、
不可争议区、路线图都在那里。

- [`STATE.md`](STATE.md) —— **接手入口**：状态 / 决策记录 / 路线图 / 不可争议区
- [`TAXONOMY.md`](TAXONOMY.md) —— 9 类分类法的定义与判定规则
- [`SCHEMA.md`](SCHEMA.md) —— 30 个字段的完整说明
- [`FINDINGS.md`](FINDINGS.md) —— 初步发现
- [`LIMITATIONS.md`](LIMITATIONS.md) —— **已知局限（请务必先读）**
- [`ENVIRONMENT.md`](ENVIRONMENT.md) —— 采集环境与通道备忘

## 复现

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python work/discover_repos2.py      # 枚举候选仓库
.venv/bin/python work/fetch_full.py work/repos_topics.txt  # 抓取
.venv/bin/python work/extract_v1.py           # 抽取
.venv/bin/python work/pack.py                 # 打包（同时更新随包的 parquet）
.venv/bin/pytest -q                           # 冒烟测试（138 项）
```

**纵向基线**：`data/processed/baseline-2026-09-10.tsv` 固化了本快照每个仓库的
`file_sha`。三个月后重抓一次、跑 `work/longitudinal.py`，就能测出
"有多少章程被换掉、新增里有多少是同 sha 的模板产物"——
这是"机器正在批量写章程"唯一的测量方法。

> `work/extract_v1.py` 不自己实现分类规则——它调用 `agent_charters.extract`，
> 保证"生成数据集用的规则"与"随包分发的规则"是同一套。
> 测试里有一项会在两者不一致时失败，这是刻意的刹车。

> 抓取依赖已认证的 `gh` CLI，且需注意 `code_search` 限流（10/min）。
> 环境细节见 `ENVIRONMENT.md`。

## 许可与版权

- **代码**（`agent_charters/`、`work/`）：MIT，见 [`LICENSE`](LICENSE)
- **数据**（`data/processed/` 下的标注与统计）：CC-BY-4.0，署名 `agent-charters v0.5`
- **原文**：本仓库**不含任何 `AGENTS.md` 原文全文**（`data/raw/` 已在 `.gitignore` 中）。
  数据集只含衍生标注、统计特征与极短引用，原文版权归各仓库作者。

要取回原文：用每行的 `repo_full_name` + `file_path` + `file_sha`
从 GitHub 取回与快照**逐字节相同**的文件。

## 引用

```
agent-charters v0.5 (2026). 智能体章程语料库.
https://github.com/janzong/agent-charters
```

## 已知局限

**请不要在不读 [`LIMITATIONS.md`](LIMITATIONS.md) 的情况下使用本数据。**
最关键的四条：

- 分类基于规则而非逐份人工标注。**实测准确率**（100 份核对，见 `LIMITATIONS.md` §16）：
  微平均 precision **80–92%**、recall **75–84%**；最弱的是 `gotchas`（recall 38%）与
  中文样本上的 `build_test`（precision 61%）。⚠️ 该数字是 **in-sample 上界**。
- 中文样本仅 4.8%（25/516），任何按语言做的对比都缺统计效力。
- 抓取池偏向 AI/agent 话题仓库，不代表 GitHub 全体。
- `boundaries` 的正文 `Do not …` 通式有约 3% 已知假阳性，它决定了头条排序（§13）。
