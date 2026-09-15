# 「章程是指针」这件事有多大、长什么样、能不能跟随（2026-09-15，**只读探测**）

**为什么量**：`LIMITATIONS.md` §25 量出"同一仓库两份章程"里 38–49% 的成对**有一份是空壳/指针**，
而 `compare` 与 GitHub Action 是**单文件判定**——对着 13B 的 `@./AGENTS.md` 会报 **0/9**，
用户看到的是"你这章程很空"。**D40** 据此决定改做「指针识别 / 跟随」，但动手前得先知道问题有多大、
指针都长什么样、目标找不找得到。本文件**只量不实现**。

**样本**：`data/cache/trees/` 里缓存的 **508** 棵仓库树（`filetype_probe.py` 的产物，重跑零 API 成本），
取**根级** `AGENTS.md` / `CLAUDE.md`——共 **791** 份（`AGENTS.md` 507 / `CLAUDE.md` 284）。
脚本 `work/audit/pointer_probe.py`，正文走 blob API 缓存在 `data/cache/blobs/`（两个缓存目录都在 `.gitignore` 内）。

## 结果一：791 份里 **111 份是符号链接**、156 份是"非链接但 <2000B"

符号链接（`mode=120000`）在**本地 checkout 上会自动解析**（git 会把它签出成真链接），
所以它们不是"跟随"要解决的问题——**真正的问题在普通文件里的正文指针**。

## 结果二：156 份小文件的语法分布

| 形态 | 份数 |
|---|---|
| **`@导入`**（整行 `@路径.md`，Claude Code 的 import 语法） | **68** |
| 无指针语法（短但自足，本来就没指向别处） | 53 |
| `Read` / `See` + `.md` 文件名 | 10 |
| 本地 Markdown 链接 | 10 |
| `Read/See` + 本地链接 | 6 |
| `@导入` + `Read/See` | 4 |
| `@导入` + 本地链接 | 2 |
| 本地链接 + 自陈 / `Read/See` + 自陈 / 三者齐 | 各 1 |

**`@导入` 是主导形态（68/103 有指针语法的文件），而现有 `POINTER_PAT` 完全不认它**——
它的正则是 `(?:see|read|refer to)\s+([\w.-]+\.md)`（`taxonomy.py:447`），一个字都匹配不上。

## 结果三：「纯指针」＝ 薄 + 有指针语法 + 没有自己的规则/命令（复用 `is_pointer` 的反证闸口径）

| 指标 | 数值 |
|---|---|
| 份数 | **75**（占 156 份非链接小文件的 **48%**） |
| 体积 | 中位 **11B**；**≤100B 的 57 份**；最小 10B、最大 449B |
| 当前 `compare` 给它们的九类标签 | **69 份是 0/9** |
| 被指向的目标**在同一棵仓库树里找得到** | **73 / 75** |
| **现有 `is_pointer` 判据（`POINTER_PAT` / 语义门）完全看不见的** | **69 份** |

两种 69 只有 65 份重叠（都恰好是 69 是巧合）：**看不见**的里面 4 份不是 0/9（`Graphify-Labs/graphify`
411B、`Muxi-X/ccnubox_rn` 324B、`docling-project/docling` 149B、`ollama/ollama` 358B——它们靠强模式通道捞到了
1 个标签），**0/9** 的里面有 4 份现有判据看得见（`electric-sql/electric`、`google/adk-go`、
`ollama/ollama`、`screenpipe/screenpipe`——判成了指针，但**没有跟随**，用户仍然只拿到"空"）。

代表的真实形态（正文已缓存，逐条读过）：

| 文件 | 体积 | 正文 |
|---|---|---|
| `modelcontextprotocol/inspector/CLAUDE.md` | 13B | `@./AGENTS.md` |
| `HKUDS/LightRAG/CLAUDE.md`、`Significant-Gravitas/AutoGPT/CLAUDE.md` | 11B | `@AGENTS.md` |
| `usekaneo/kaneo/CLAUDE.md` | 87B | 标题 + `Canonical guidance: [AGENTS.md](./AGENTS.md)` + `@AGENTS.md` |
| `BerriAI/litellm/AGENTS.md` | 526B | 首行 `Read @CLAUDE.md for coding guidelines`，后面还有规则 |
| `JuliusBrussee/caveman/AGENTS.md` | 734B | `Read \`CLAUDE.md\` before repository work.` + 路由说明（九类 0/9） |

## 结论（这两条决定了怎么实现）

1. **收益明确**：≥69 份根级章程会从"0/9（空的）"变成"已跟随 → 真实结果/或明说这是指针"，
   而且**73/75 的目标就在同一棵树里**，纯本地解析路径即可，不需要额外网络请求。
2. **必须支持 `@路径` 语法**——现有判据对此完全失明（69 份里的大部分）。同时保留 `Read|See`、
   本地链接、以及"作者自陈"三条老通道；`modelcontextprotocol/inspector` 那种 `@./AGENTS.md`
   还要能归一化 `./` 前缀。
3. **不能静默**：跟随之后必须**在输出里说明**"这份是指针 → 规则在 X"，否则用户会把跟随后的
   九类覆盖当成"这个文件写的"——那是另一种错误结论。

## 边界

- 只看了**根级**的两个文件名（`AGENTS.md` / `CLAUDE.md`）；`.cursor/rules/*.mdc`、`GEMINI.md` 等没扫。
- 小文件门是 `<2000B`（与 `is_pointer` 的口径一致）：**>2000B 的文件里也可能有 `@导入`**（那种通常
  是"引用 + 大量自己的规则"，本就不该跟随，所以不扫）。
- `@导入` 的正则要求 `.md`/`.mdc` 后缀，`@user@host.md` 这类误配在样本里**没有出现过**（逐条看过上表 12 个样例）。
- 树只覆盖 508 / 558 个仓库（其余是 api.github.com 经代理抖动，`filetype_probe.py` 重跑即补）。
