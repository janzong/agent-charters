# 对照实验：机器生成的 AGENTS.md vs 仓库里人写的那份

**日期**：2026-09-10 ｜ **样本**：4 个公开仓库 ｜ **生成器**：Claude Code（`claude -p`）
**复现命令**：`work/auto_vs_human.py 标签:人写文件:生成文件 ...`

**要回答的问题**：既然编辑器/Agent 已经能一键生成章程，那"章程语料库"还有差异化用处吗？

---

## 方法（不这么做实验就没有意义）

1. `git clone --depth 1` 四个仓库；**把仓库里所有章程文件移出目录**
   （`AGENTS.md` / `CLAUDE.md` / `.cursorrules`）——否则生成器会读到并抄它，结果作废。
2. 用同一个提示词让生成器「只依据仓库里能找到的东西」写一份 `AGENTS.md`：
   > Analyze this repository and create an AGENTS.md file at its root. It must tell a
   > coding agent how to work in this codebase: project purpose, structure, how to
   > build/test/run, conventions, and anything it must not do. Base it only on what is
   > actually in the repository - do not invent commands that are not discoverable.
3. 把人写的版本放回对照，用本项目的分类器分别打标。

**抄写检测**（人写 vs 生成，8-gram 重叠）：ts1 1.1% / ts2 0% / Whale 0% / nano 0%。
**无抄袭，结果可用。** 唯一的 1.1% 是"项目是什么"这类必然重合的客观描述。

**已知泄漏点**：生成时 `git status` 显示 `D AGENTS.md`，有两个模型注意到了这条线索
（都明确说明没有从历史里取回内容）。若要更严格，应在生成前删掉 `.git`。

---

## 结果

| 仓库 | 类数 人/机 | 字节 人/机 | 章节 人/机 |
|---|---|---|---|
| HorusGoul/eslint-plugin-react-render-types (TS) | 5 / **8** | 5239 / 6226 | 16 / 8 |
| gotalab/cc-sdd (TS) | **6** / 4 | 3447 / 6064 | 10 / 6 |
| usewhale/Whale (Go) | **6** / 5 | 2918 / 5627 | 7 / 6 |
| NanoNative/nano (Java) | 5 / **6** | 2937 / 7694 | 7 / 9 |
| **平均** | 5.5 / **5.8** | 3635 / **6402** | 10 / 7.3 |

逐类（✓✓ 两边都有 / ✓— 只有人写 / —✓ 只有机器 / —— 都没有）：

| 类别 | 人写命中 | 机器命中 |
|---|---|---|
| `build_test` | 4/4 | 4/4 |
| `structure` | 4/4 | 4/4 |
| `boundaries` | 3/4 | 4/4 |
| `workflow` | **4/4** | 2/4 |
| `environment` | 3/4 | 1/4 |
| `overview` | 2/4 | 3/4 |
| `style` | 2/4 | 4/4 |
| `gotchas` | **0/4** | 1/4 |
| `agent_meta` | 0/4 | 0/4 |

---

## 发现

### 1. 在"写一份能用的章程"这件事上，机器已经打平——甚至更好

平均类别 5.8 vs 5.5，平均字节 6402 vs 3635，而耗时是分钟级。
**"自动生成会替代从零写章程"这个担心，在结构/命令/约定这几块是成立的。**

### 2. 但机器产出高度同质——而且人写的也已经是模板

四份机器文件全部收敛到同一个骨架：
`What this is → Layout → Build/test/run → Conventions → Do not`。

真正值得注意的是**人写的那两份**（Whale、nano）用的是同一个骨架：
`Repository Guidelines → Project Structure & Module Organization → Build, Test, and
Development Commands → Coding Style & Naming Conventions → Testing Guidelines →
Commit & Pull Request Guidelines → Security & Configuration Tips`。

在 558 份语料库里量化这个骨架：

- 39 份使用 `Repository Guidelines` 这个标题
- 20 份命中该骨架 ≥4/6 个子节（3.6%）
- 单看子节名：`Testing Guidelines` 25 份、`Build, Test, and Development Commands` 21 份、
  `Coding Style & Naming Conventions` 20 份

而 Whale 与 nano 两份人写文件**正文 8-gram 重合为 0%**——骨架相同、文字无重合。
说明这不是复制粘贴，而是**结构已经约定俗成到被独立采用**。

**结论：真正的分界线不是"人 vs 机器"，而是"能从仓库推导出来 vs 推导不出来"。**
机器写和人写在这条线上站在同一边。

### 3. 双方共同缺的是同一件事：只有经历过才知道的东西

- `gotchas`：人写 **0/4**，机器 1/4
- `agent_meta`：人写 0/4，机器 0/4

这和语料库整体一致（`gotchas` 14%，九类最低）。
**自动生成没有让这一点变好**——因为它不是生成能力问题，是"谁经历过"的问题。
"别改 lockfile，`bun install` 会重写它"这种话，仓库里通常没有证据可读。

### 4. 方法学发现：我说机器"漏掉"的部分，有一半是分类器口径造成的

机器"漏掉" `environment` 的三份里，人写的那一节标题是
`Security & Configuration Tips`（命中 `config`），而机器把同类内容写在
`Do not` 小节里（被判成 `boundaries`）。**内容没差那么多，是标题措辞不同。**

这实证了本数据集的一个真实局限：**分类依赖标题措辞**，
换一种写法就漏标。v0.1.1 补的是同义词，补不了这个结构性问题。

---

## 不能从这里推出什么

- **n=4，一个生成器，一个模型，一个提示词。** 这不是"自动生成的好坏评测"。
- 类别差异中有一部分是分类器口径（见发现 4），**不能全部读成内容差异**。
- 生成器只读了仓库，没有读 issue、PR 历史、CI 失败日志——**给它更多证据源，
  `gotchas` 未必还是空白**。发现 3 的严格说法是：
  机器能自动提取"仓库里已经写下来的东西"。

## 对项目定位的含义

1. "章程模板/最佳实践清单"这个卖点会被免费吃掉——不要站这条线。
2. 站得住的三件事：**尺子**（覆盖率基线）、**分布先验**（喂生成器/评测）、
   **有效性证据**（哪种写法真的让 agent 干得更好——目前是空场）。
3. 数据集的未来定位可以更精确：不是"人写的章程集合"，而是
   **"非自动可推导内容的分布"**。这需要在 v0.2 增加人写/机器写的判定字段。
