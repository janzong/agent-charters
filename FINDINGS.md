# 初步发现 FINDINGS v0.1

> 基于 518 份实质 `AGENTS.md`（2026-09-10 快照）。
> **这些是观察，不是结论**——样本偏向 AI/agent 话题仓库，且分类由规则完成。

## 1. "怎么跑起来"压倒一切（79%）

`build_test` 覆盖率 **79%**，标签出现 **1780 次**，是第二名（`boundaries` 630 次）的
近三倍。人写给 agent 的第一要务非常朴素：**告诉它怎么构建、怎么测试、怎么运行。**

## 2. "不要做什么"写得比"要做什么"还显眼（60%）

`boundaries` 覆盖 60%。大量文件用整节写禁令：
`NO FILE DELETION`、`DO NOT EVER`、`Never run cargo build`、`ONLY Use main, NEVER master`。

**推测**：人对 AI 的信任建立方式，是先划出不可逾越的线，而不是先授权。

## 3. 坑，被系统性低估（12%）

`gotchas` 只有 12%，是九类中最低的。但这类内容恰恰是**最难自己发现、
最需要前人告知**的知识（如"Ubuntu 24.04 启用多个 INTERNAL builtin service 时
xinetd 会因 socket 冲突启动失败"）。

**这是本数据集最有研究价值的切入点**：为什么最有价值的知识被写得最少？

## 4. 章程的主体是命令，不是知识（72% vs 15%）

- `rule`（指令性）：374 份（72%）
- `knowledge`（陈述性）：76 份（15%）
- `mixed`：68 份（13%）

但也有反例：`sous-chefs/xinetd` 的主体是**领域事实**（各发行版的包可用性与 EOL 日期），
只有少数几条是命令。**这类"知识型章程"是少数派，但可能代表一种更成熟的用法。**

## 5. 中文项目严重缺席（5%）

518 份实质文件中，中文文档仅 **26 份（5%）**，英文 475 份（92%）。

考虑中文开发者占 GitHub 活跃用户的比例，5% 明显偏低。
**这是一个真实空白**，不是采样偏差能完全解释的。

## 6. 一份章程平均覆盖 4.4 个主题

多标签分布集中在 4–6 个（259 份，占一半）。只有 4 份文件同时命中 9 类。

**含义**：`AGENTS.md` 不是单一用途文档，而是**项目协作知识的聚合点**。
用单一维度评价它（"这是风格指南"或"这是命令清单"）都会失真。

## 7. 存在"转引用"这种模式（11 份）

有些 `AGENTS.md` 本身几乎没内容，只做**路由**：

```
# Chroma Codebase Guidelines for AI Agents
See CLAUDE.md for codebase conventions (commit message format, etc.).
```

```
For guidance on working with this repository, see the .ai/ directory:
- COMMANDS.md / ARCHITECTURE.md / TESTING.md / TROUBLESHOOTING.md …
```

**含义**：一部分团队已经把 agent 规约**分层**——顶层只做分发，细节分散到多个文件。
这是规约工程化的信号。

## 8. 规约不是单向的：agent 也在往里写

`sous-chefs/xinetd` 有一个章节叫 **"Agent Findings"**，内容是开发过程中积累的发现。
这说明 `AGENTS.md` 不只承载"人 → AI"的指令，也开始承载"AI → 下一个 AI"的知识。

**这可能是本数据集最值得追踪的长期变化。**

## 9. 生态画像

- **语言**：TypeScript 185、Python 129、Go 50、Rust 44、JavaScript 28
- **许可**：MIT 244 + Apache-2.0 116 = **70% 为宽松许可**（对二次使用友好）
- **规模**：中位数 6.7 KB，p75 12 KB，最长 154 KB

## 可验证性说明

以上每一条都可由 `data/processed/agent-charters-v0.1.parquet` 直接复算。
复算方式见 `README.md` 的"快速开始"。
