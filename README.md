# agent-charters ｜ 智能体章程语料库

> **人写给 AI 智能体的书面规约**的结构化语料库。
> v0.1 覆盖 `AGENTS.md`，共 **558 份**、来自 558 个公开仓库。

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
| 文件数 | 558（其中实质内容 518） |
| 仓库数 | 558（已排除 fork） |
| 采集时间 | 2026-09-10 |
| 总字节 | 5.5 MB |
| 每份平均标签数 | 4.4 |
| 许可 | 代码 MIT ｜ 数据 CC-BY-4.0 |

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

## 类别分布（实质文件 518 份）

| 类别 | 覆盖 | 含义 |
|---|---|---|
| `build_test` | 79% | 构建 / 测试 / 运行命令 |
| `boundaries` | 60% | 禁令、边界、不可做的事 |
| `workflow` | 57% | 分支、提交、PR、发布 |
| `structure` | 56% | 架构、目录与文件组织 |
| `style` | 55% | 代码风格、命名、约定 |
| `environment` | 44% | 环境、工具链、依赖 |
| `agent_meta` | 36% | 关于 AI 自身行为的规定 |
| `overview` | 33% | 项目概览、技术栈、目的 |
| `gotchas` | 12% | 坑、陷阱、已知问题 |

## 文档

- [`TAXONOMY.md`](TAXONOMY.md) —— 9 类分类法的定义与判定规则
- [`SCHEMA.md`](SCHEMA.md) —— 23 个字段的完整说明
- [`FINDINGS.md`](FINDINGS.md) —— 初步发现
- [`LIMITATIONS.md`](LIMITATIONS.md) —— **已知局限（请务必先读）**
- [`ENVIRONMENT.md`](ENVIRONMENT.md) —— 采集环境与通道备忘

## 复现

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python work/discover_repos2.py      # 枚举候选仓库
.venv/bin/python work/fetch_full.py work/repos_topics.txt  # 抓取
.venv/bin/python work/extract_v1.py           # 抽取
.venv/bin/python work/pack.py                 # 打包
```

> 抓取依赖已认证的 `gh` CLI，且需注意 `code_search` 限流（10/min）。
> 环境细节见 `ENVIRONMENT.md`。

## 引用

```
agent-charters v0.1 (2026). 智能体章程语料库.
https://github.com/janzong/agent-charters
```

## 已知局限

**请不要在不读 [`LIMITATIONS.md`](LIMITATIONS.md) 的情况下使用本数据。**
最关键的三条：分类基于规则而非人工逐份标注；中文样本仅 5%；
抓取池偏向 AI/agent 话题仓库，不代表 GitHub 全体。
