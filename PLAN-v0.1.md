# agent-charters v0.1 方案（一页纸）

> 撰写：2026-09-10 ｜ 状态：待确认后执行
> v0.1 的目标**不是做完研究**，而是**跑通一次完整闭环**：抓取 → 抽取 → 打包 → 发布 → 有人下载。

## 1. 范围与边界（刻意收窄）

- **只做 `AGENTS.md` 一种文件类型**（CLAUDE.md / .cursorrules / copilot-instructions.md 留给 v0.2）
- **目标规模 300–600 份文件**（不求多，求可追溯、可复现）
- **不发布原文全文**，只发布衍生标注 + 短引用 + 原文链接（版权安全）
- **不做 LLM 自由生成**，只做可判定的分类

## 2. 数据获取策略（技术前提已验证）

### 已验证的事实

```bash
# 一次 GraphQL 调用可批量探测多个仓库，并直接取回正文
gh api graphql -f query='{
  r0: repository(owner:"yanyiwu", name:"nodejieba") {
    object(expression:"HEAD:AGENTS.md") { ... on Blob { byteSize text } } }
}'
# → 实测成功：一次 30 个节点返回正常，正文可取
```

**这一步绕开了 `code_search` 10/min 的限流**，是本方案成立的关键。

### 三段式流程

| 阶段 | 做什么 | 配额 | 预估 |
|---|---|---|---|
| A 仓库发现 | `gh search repos` 多维度枚举候选（topic / 语言 / star 区间 / 活跃时间） | search 30/min | 数千个候选 |
| B 批量探测 | GraphQL 一次 30–50 个仓库，探测 `HEAD:AGENTS.md` 是否存在并**同时取回正文** | graphql 5000 pts/h | 一次调用覆盖几十个 |
| C 落库 | 命中的写本地（含 `commit_sha` 快照） | — | — |

**去重**：按 `repo_full_name + file_sha` 去重；fork 仓库默认排除。

**分片要点**：search API 单查询上限 1000 条，必须按语言 / star 区间 / 时间片切分后合并去重。

## 3. 分类法草案（TAXONOMY，v0.1 核心贡献）

每份文件按下列 9 类标注（多标签）+ 每类条目数：

| 类别 | 含义 |
|---|---|
| `build_test` | 构建 / 测试 / 运行命令 |
| `code_style` | 代码风格、格式、命名 |
| `architecture` | 架构、目录结构、模块边界 |
| `workflow` | 开发流程、PR、分支、提交规范 |
| `security` | 安全、权限、危险操作禁令 |
| `tooling` | 指定工具、MCP、依赖 |
| `context` | 项目背景与领域知识 |
| `communication` | 提交信息、注释、文档语言 |
| `ai_meta` | 关于 AI 自身行为的规定（如"不要恭维我"） |

> `ai_meta` 是最有研究价值的一类——`google/benchmark` 的 AGENTS.md 开头就写着
> "AI is a misnomer … it is merely a next-token guesser"，属于此类。

## 4. 字段设计（SCHEMA）

**粒度：一行 = 一份文件**（条目级留到 v0.2）

- **标识**：`repo_full_name`、`file_path`、`file_sha`、`commit_sha`、`commit_date`
- **仓库背景**：`repo_stars`、`repo_language`、`license`、`repo_pushed_at`
- **文件特征**：`bytes`、`lines`、`section_count`、`heading_tree`、`code_block_count`、`doc_language`
- **分类结果**：`category_*` 多标签 + `category_counts`（每类条目数）+ `total_rule_items`
- **抽取元数据**：`extractor_version`、`model_version`、`retrieved_at`

> `commit_sha` + `retrieved_at` 是可复现性的关键：指定 commit 就能重现同一份数据。
> `model_version` 必填——LLM 抽取有随机性，不记模型版本半年后无法复现。

## 5. 判据（全部可判定，无解释空间）

**成功标准**（6 条全中才算 v0.1 完成）：

1. 入库文件 ≥ 300 份
2. 每份都有 `commit_sha` 与 `retrieved_at`（可追溯）
3. 固定 commit 重跑脚本得到相同结果（可复现）
4. 发布在 GitHub Release，他人可下载并成功 load（可获取）
5. **至少 1 个非作者的人下载并确认能读**（被使用）
6. 不含任何原文全文，仅为衍生标注 + 短引用（版权合规）

**失败不等于降标准**：

- 抓不满 300 份 → **改发现策略**，不降低数量标准
- 抽不出类别 → **改分类法**，不放弃分类

## 6. 交付物

| 文件 | 作用 |
|---|---|
| `agent-charters-v0.1.parquet` / `.jsonl` | 主数据集 |
| `SCHEMA.md` | 字段说明 |
| `TAXONOMY.md` | **分类法定义（研究贡献）** |
| `FINDINGS.md` | 初步发现 3–5 条 |
| `crawl.py` / `extract.py` | 可复现脚本 |
| `README.md` | 含统计摘要 |

**发布位置**：GitHub `janzong/agent-charters` 仓库 + Release；
ModelScope 数据集（账号就绪后补）。

## 7. 工作分解与瓶颈

- **T0 分类法校准** ← **唯一的人工瓶颈**
  人工抽样 30 份文件、按 9 类标注、检查类别是否互斥且可判定。
  **这一步必须人做**，因为分类法一旦定错，后面全白干。
- **T1 抓取脚本**（仓库发现 + GraphQL 批量探测 + 落库）
- **T2 抽取脚本**（规则优先，LLM 仅做类别判定）
- **T3 打包 + 统计**
- **T4 文档**（README / SCHEMA / TAXONOMY / FINDINGS）
- **T5 发布**

T1–T4 按**智能时间**推进，可并行，实际以小时计。
**T0 是人和智能的分界线**——这也是本项目"人定坐标、智能做搜索"的第一个落点。

## 8. 下一步

请先确认三件事，我再动手：

1. **范围**：只做 `AGENTS.md`、300–600 份 —— 认可吗？
2. **分类法**：第 3 节那 9 类 —— 要增删吗？
3. **T0 怎么做**：你自己抽样标注，还是我先抽 30 份、你只做确认/修改？
