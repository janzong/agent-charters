# 分类法 TAXONOMY v0.1

> 9 个类别，多标签。一份文件可同时属于多个类别。
> 本分类法是 **v0.1 的核心贡献**，也是被迭代最多的部分（见文末演进史）。

## 设计原则

1. **可判定**：每条判定规则都能写成可执行的匹配表达式，不依赖主观理解。
2. **基于内容，不基于文件名**：`AGENTS.md` 这个文件名本身会污染 `agent_meta` 判断。
3. **保守优先**：宁可漏标，不做错标——错标会污染统计，漏标只是损失召回。

## 九个类别

| 类别 | 定义 | 典型标题 |
|---|---|---|
| `overview` | 项目是什么、技术栈、目的、核心概念 | Project Overview, Tech Stack, What This Is |
| `structure` | 架构、目录与文件组织、模块边界 | Architecture, Repository Layout, File Organization |
| `build_test` | 构建、测试、运行、CI 的命令与流程 | Commands, Testing, Build & Test |
| `style` | 代码风格、命名、格式、约定、最佳实践 | Coding Conventions, Naming, Best Practices |
| `workflow` | 分支、提交、PR、评审、发布流程 | Git Workflow, Commits, Release Process |
| `environment` | 环境、工具链、依赖、配置、安装 | Toolchain, Dependencies, Setup |
| `boundaries` | 禁令、边界、卫生规则、不可做的事 | Hard Rules, Boundaries, Do Not Ever |
| `gotchas` | 坑、陷阱、注意事项、已知问题 | Gotchas, Common Pitfalls, Known Issues |
| `agent_meta` | **明确规定 AI 自身行为/语气/身份/协作方式** | Agent Instructions, Your Role, Subagent Strategy |

## 判定规则

分类规则定义在 `agent_charters/taxonomy.py`（单一事实源；`work/extract_v1.py` 只是调用方）。
判定分**三个通道**：

1. **标题通道（强信号）**：把文件按标题切分为章节，逐个匹配类别关键词。
   命中即打标，并在 `category_counts` 里累加次数。
2. **全文通道（补救）**：仅当**标题通道完全无结果**时启用，避免过度标注。
   用于纯列表、纯散文式文件（这类文件没有标题，标题通道必然失败）。
3. **强模式通道（v0.1.1 新增）**：**总是运行**，与标题通道无关。
   只收跨语言、高精确的信号，例如 `pytest` / `npm run build` / `./gradlew`（`build_test`）、
   `git pull … git push` / `Conventional Commits`（`workflow`）、`🚫`（`boundaries`）。
   已命中的类别不重复计数。
   **动机**：中文文档常"有内容但标题不含英文关键词"，原先会被判成"什么都没有"——
   给出错误结论的工具比没有工具更糟。强模式把无标签的实质文件从 15 份降到 7 份。

另有两个**内容级模式匹配**，不受标题影响：

- `agent_meta`：`You are`、`Your role`、`Do not praise`、`Before responding`
- `boundaries`：`never commit`、`must not`、`never … secret/token/credential`

## 两个正交字段（不是类别）

- `content_mode`：`rule`（指令性）/ `knowledge`（陈述性）/ `mixed`。
  依据是指令词（do not / must / never / always / avoid）的出现密度。
  **这个字段很重要**：有些文件主体是领域知识（如"哪个发行版有哪个包"），
  而不是命令。不做这个区分，统计会把两类东西混在一起。
- `is_pointer`：正文只是指向另一个文件（如 "See CLAUDE.md"）。
  **这类文件本身没有内容类别**，`categories` 为空是正确结果，不是分类失败。

## 演进史（为什么是这 9 类）

| 版本 | 变化 | 触发原因 |
|---|---|---|
| v0（草案） | `context` / `tooling` / `security` / `decisions` / `ai_meta` | 凭常识设计 |
| v0.1a | `decisions` → **删除** | T0 实测仅 3% 命中，真实数据里几乎无人写决策记录 |
| v0.1a | 新增 `gotchas` | T0 发现 `gotchas` / `pitfalls` 反复出现，原分类法完全漏掉 |
| v0.1b | `ai_meta` 收紧为 `agent_meta` | T0 命中率 79% 是假象——文件名叫 `AGENTS.md` 而已 |
| v0.1c | `context`→`overview`、`security`→`boundaries`、`tooling`→`environment` | 更贴合真实标题用词 |
| v0.1d | 增加**全文通道** | 无标题文件（纯列表）在标题通道下必然漏标 |
| v0.1d | 增加**中文关键词** | 中文样本在纯英文关键词下全部漏标 |
| v0.1d | 增加 `is_pointer` | 发现"把章程分散到多个文件"是一种真实模式 |
| **v0.1.1** | 新增**强模式通道**（总是运行） | 中文文档被标题通道整体漏标，`compare` 对中文给出错误的 4/9 |
| **v0.1.1** | 标题关键词扩充（中英同义词：`技术栈`/`模块`/`规则`/`verification`/`key files`/`contributing`…） | 语料库里 2885 种标题从未被任何规则命中；中文长尾 179 种 |
| **v0.1.1** | 修两个假阳性：`make \w+`（会命中 "make sure"）、`gradle \w+`（会命中 "Gradle 9"） | 抽验新增标注时发现，已写成回归测试 |
| **v0.1.1** | 未采纳：把 `Repository Guidelines` 当 `overview` | 它是模板级标题（30 份），不携带内容信息——宁可漏标 |
| **v0.1.2** | 收紧 `is_pointer`：改为「薄（去链接去路径 <400B）**且**在指向」**或**「作者自陈只是路由」 | 旧口径"提到 ≥2 个 `.md` 文件名 + <2000B"把有实质规则的短章程也剔出统计。11 份人工标注：真 4 / 边界 2 / 误 5 |
| **v0.1.2** | `structure` 标题词表补「分工/职责/归属/ownership/code owner/responsibilit…」 | 33 个这类章节里 9 个原先完全无标签，而"新代码该放哪里、谁负责哪块"正是 `structure` 要答的 |
| **v0.1.3** | 标题通道由**子串**改为**词首**匹配（连字符算边界；保留词首前缀命中） | `ci` 命中 `Deci\|sions`、`script` 命中 `TypeScript`。实测 511 份里 23 处 (文件,类别) 组合的标签只靠这种误命中撑着，修好后 18 处掉标签 |
| **v0.1.3** | `build_test` 删裸词 `make`，只留 `makefile` 与具体目标（`make build`/`make dev`…） | 511 份里 12 个标题命中裸词，逐条看 7 份是散文（`Make changes`/`make sure`），与 `STRONG_PATTERNS` 既有口径对齐 |
| **v0.1.4** | `agent_meta` 删 3 个路由型标题词（`agent instruction` / `agent guidance` / `ai instruction`） | 这类标题多是文件自己的名字，标签无区分度（同 v0.1b 的教训）。实测 36.4% → 29.5%（−35 份，无新增）|

## 口径裁决（2026-09-12，由人定，非智能体自决）

`work/audit/v0.2-agent-verdicts.md` 里有 ≥6 条判定卡在"定义没说要收不收"。这类**定义边界**
不该由规则作者自己拍，2026-09-12 由项目所有者裁定如下四条。它们是后面 100 份人工核对的前提：
口径不定，审计会把"定义模糊"记成"规则错"，测出来的准确率不可信。

| # | 问题 | 裁决 | 对规则的影响 |
|---|---|---|---|
| 1 | `风格` 收不收 Git 规范（"Commit message: conventional commits"） | **收**——它是"写成什么形状"的约定，与命名/格式同族 | 无需改词表：实测 0 份受影响（这类标题已被 `convention` / `style` / `规范` 命中） |
| 2 | `环境` 收不收 SDK/语言版本号（"Node 22、Python ≥3.11"） | **收**——工具链版本就是环境的一部分 | 暂不加规则：实测只有 1 个候选，且是探针误报（`Ignore Python 2 compatibility` 并非版本清单）。**先记录口径，出现真实样本再补规则** |
| 3 | `构建测试` 收不收"该不该跑构建"（"默认不要执行编译/构建/测试，除非用户明确要求"） | **收**——类别定义是"构建/测试/运行**这件事**"，不是"命令清单"；"别盲目跑测试"恰是给 agent 的关键信息 | 无需改词表：这类章节含 `构建/测试` 等词，本就会命中 |
| 4 | `AI行为` 收不收"标题里出现 agent / instructions" | **不收**——见下 | 改词表：`agent_meta` 删 3 个路由型标题词 |

### 裁决 4 的依据与实测（`ruleset_v0.1.4`）

删掉 `agent instruction` / `agent guidance` / `ai instruction`。理由：这三类标题在实际语料里
几乎都是**文件自己的名字**（"WSL2 Distro Manager — Agent Instructions"、"Private Agent Instructions"），
而本语料库的每份文件按定义都是写给 agent 的——**这个标签不携带区分度**，
与 v0.1b 修掉的"文件名叫 `AGENTS.md` 导致命中率 79%"是同一类错误。

实测（511 份可用样本，`work/v0.3-to-v0.4-diff.md`）：

- `agent_meta` **36.4% (186) → 29.5% (151)**，−35 份，**无新增**；排名从第 7 位降到第 8 位（低于 `overview`）
- 副作用：`build_test` 438 → 439（某份文件因此章节无标签，落到全文兜底通道）
- 抽查确认没有误伤：`MervinPraison/PraisonAI` 这类**真有**行为内容的文件靠正文通道
  （`body:\byou are\b`）保住了标签；掉标签的是"标题叫 Agent Instructions、正文是项目规则"的那些

**更宽的删除口径未采纳**：若再删 `agent tool` / `agent prompt` / `agent note` / `agent skill` /
`agent behavior` / `agent workflow`，`agent_meta` 会到 25.2%（实测）。那些章节通常是内容型，
**等 100 份人工核对给出 precision 数据再定**——不凭"看起来像"删。

## 已知问题（v0.4 待改进）

0. **规则法无法处理同义表达**：只有写进关键词的措辞才能命中。
   v0.1.1 的扩充都是"补近义词"，不是"学会理解"——这条路天然有上限。
1. **召回率偏低**：抽查 12 份中 3 份有漏标（`overview` 和 `agent_meta` 为主）。
   v0.1.1 后未标签文件降至 7 份，但未做新的人工核对。
2. **`content_mode` 判定粗糙**：仅按指令词密度阈值切分，未做语义判断。
3. **类别边界有重叠**：如 `style` 与 `workflow` 在 "Commit Style" 上会同时命中
   （此处视为合理，因为该章节确实同时涉及两者）。
4. **散文式文件**（无标题、无列表）仍有漏标，如 `mastra-ai/mastra`。
