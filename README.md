# agent-charters ｜ 智能体章程语料库

> **人写给 AI 智能体的书面规约**的结构化语料库。
> 数据集 **v0.1.1** 覆盖 `AGENTS.md`，共 **558 份**、来自 558 个公开仓库。

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
| 文件数 | 558（实质内容 518，其中可用于分类统计 507） |
| 仓库数 | 558（已排除 fork） |
| 采集时间 | 2026-09-10 |
| 总字节 | 5.5 MB |
| 每份平均标签数 | 4.7（九类中全中的有 6 份） |
| 许可 | 代码 MIT ｜ 数据 CC-BY-4.0 |

> 为什么有两个口径：`is_substantive` 只排掉空壳文件，`is_pointer` 还要排掉
> "只写了一句『见 CLAUDE.md』"的转引用文件（11 份）。后者 `categories` 为空
> **是正确结果**，不该算进分母。所有类别覆盖率都按 **507** 计算。

**不含原文全文**——只发布衍生标注与统计特征。原文版权归各仓库作者。

## 快速开始

```python
import pandas as pd

df = pd.read_parquet("data/processed/agent-charters-v0.1.parquet")

# 最常出现的主题
from collections import Counter
c = Counter(t for tags in df["categories"] for t in tags)
print(c.most_common())

# 只要实质内容
sub = df[df["is_substantive"] & ~df["is_pointer"]]
print(len(sub))
```

## 类别分布（507 份实质文件）

| 类别 | 覆盖 | 含义 |
|---|---|---|
| `build_test` | 87% | 构建 / 测试 / 运行命令 |
| `workflow` | 66% | 分支、提交、PR、发布 |
| `boundaries` | 66% | 禁令、边界、不可做的事 |
| `structure` | 58% | 架构、目录与文件组织 |
| `style` | 57% | 代码风格、命名、约定 |
| `environment` | 45% | 环境、工具链、依赖 |
| `agent_meta` | 36% | 关于 AI 自身行为的规定 |
| `overview` | 34% | 项目概览、技术栈、目的 |
| `gotchas` | 14% | 坑、陷阱、已知问题 |

## 命令行工具

装好依赖后（或在仓库根目录直接 `.venv/bin/python -m agent_charters`）：

```bash
# 全局分布：语料库长什么样
agent-charters stats

# 把你手上的章程与语料库对比——看它缺了什么
agent-charters compare path/to/AGENTS.md [更多文件...]

# 看某个类别的真实写法（按该类别章节数降序）
agent-charters show gotchas --limit 8
```

`compare` 是给写章程的人用的：它会指出**语料库里写得最多、而你完全没写的类别**，
以及每个类别在语料库里的覆盖率。中文文件同样适用。

## 文档

**如果你是接手的智能体或协作者，请先读 [`STATE.md`](STATE.md)** —— 项目状态、决策记录、
不可争议区、路线图都在那里。

- [`STATE.md`](STATE.md) —— **接手入口**：状态 / 决策记录 / 路线图 / 不可争议区
- [`TAXONOMY.md`](TAXONOMY.md) —— 9 类分类法的定义与判定规则
- [`SCHEMA.md`](SCHEMA.md) —— 25 个字段的完整说明
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
.venv/bin/pytest -q                           # 冒烟测试（11 项）
```

> `work/extract_v1.py` 不自己实现分类规则——它调用 `agent_charters.extract`，
> 保证"生成数据集用的规则"与"随包分发的规则"是同一套。
> 测试里有一项会在两者不一致时失败，这是刻意的刹车。

> 抓取依赖已认证的 `gh` CLI，且需注意 `code_search` 限流（10/min）。
> 环境细节见 `ENVIRONMENT.md`。

## 引用

```
agent-charters v0.1.1 (2026). 智能体章程语料库.
https://github.com/janzong/agent-charters
```

## 已知局限

**请不要在不读 [`LIMITATIONS.md`](LIMITATIONS.md) 的情况下使用本数据。**
最关键的三条：分类基于规则而非人工逐份标注；中文样本仅 5%；
抓取池偏向 AI/agent 话题仓库，不代表 GitHub 全体。
