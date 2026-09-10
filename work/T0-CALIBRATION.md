# T0 分类法校准报告

> 日期：2026-09-10 ｜ 样本：98 份真实 `AGENTS.md`（来自 `gh search code`）
> 方法：GraphQL 批量取回正文 → 基于**标题**的规则分类器（`work/classify_v0.py`）
> 目的：不是产出分类结果，而是**暴露分类法的盲区**

## 1. 样本规模分布（形态差异极大）

```
n = 98        总计 586,380 B      均值 5,983 B
min 29 B  |  p25 2,393  |  median 3,760  |  p75 6,757  |  max 37,549 B
```

从 **29 字节**（只有一个路径的引用）到 **37 KB**（完整工程指南），跨度三个数量级。
**结论：小文件不适用章节级分类，必须先分层。**

## 2. 命中分布（规则分类器 v0）

| 类别 | 命中文件数 | 占比 |
|---|---|---|
| `agent_meta` | 78 | **79%** ⚠️ |
| `build_test` | 66 | 67% |
| `style` | 47 | 47% |
| `overview` | 46 | 46% |
| `structure` | 46 | 46% |
| `workflow` | 40 | 40% |
| `environment` | 36 | 36% |
| `boundaries` | 32 | 32% |
| `decisions` | 3 | **3%** ⚠️ |

## 3. 三个关键发现

### 发现 A：`agent_meta` 在标题层面不可判定（79% 是噪声）

标题里含 "agent" 的次数：

```
27  AGENTS.md          ← 文件标题本身
 4  Agent Instructions ← 也是文件标题
 2  Agents / 2 AGENTS  ← 同上
…其余零散
```

命中率高不是因为内容都在讲 AI 行为，而是**文件名就叫 AGENTS.md**。
真正规范 AI 行为的章节其实很少（如 `Workflow for AI Agents`、`Key Agent Config Defaults`）。

**结论：`agent_meta` 必须改为内容级判定，且定义要收紧到"明确规定 AI 自身行为/语气/身份"。**

### 发现 B：`decisions` 几乎不存在（3%），应替换

真实数据里几乎没人写"决策记录"。但**大量出现的是"坑"**——分类法完全漏掉了：

```
2  gotchas          2  common gotchas
2  when making changes    2  before finishing
2  common tasks    2  key concepts / key patterns
3  examples        2  database / java / html
```

**结论：删 `decisions`，增 `gotchas`（坑、陷阱、注意事项、已知问题）。**

### 发现 C：内容有"规则"和"知识"两种模式

`sous-chefs/xinetd` 的 AGENTS.md 主体是**领域知识**（哪个发行版有哪个包、EOL 时间），
只有少数几条是**指令**（"Do not add systemd unit management…"）。
而 `tovifun/VivalArc` 几乎全是指令。

**结论：需要独立字段 `content_mode`，否则统计会把两类东西混在一起。**

## 4. 修订后的分类法（v0.1 定稿建议）

| 类别 | 含义 | 相比原稿 |
|---|---|---|
| `overview` | 项目概览、目的、技术栈、关键概念、快速参考 | 原 `context`，扩入 quick reference |
| `structure` | 架构、目录与文件组织、模块划分 | 不变 |
| `build_test` | 构建、测试、运行命令、CI | 不变 |
| `style` | 代码风格、命名、格式、最佳实践 | 不变 |
| `workflow` | 开发流程、分支、PR、提交、发布 | 不变 |
| `environment` | 环境、工具链、依赖、配置、安装 | 原 `tooling` 扩展 |
| `boundaries` | 禁令、边界、卫生规则、不可做的事 | 原 `security` 放宽 |
| `gotchas` | 坑、陷阱、注意事项、已知问题 | **新增** |
| `agent_meta` | **明确规定 AI 自身行为/语气/身份/协作方式** | **收紧定义 + 内容级判定** |

## 5. 需要新增的非分类字段

| 字段 | 取值 | 为什么需要 |
|---|---|---|
| `is_substantive` | bool | 过滤无效内容：纯路径引用（29B）、索引文件、玩笑内容（见 `dwebagents/AgentPipe`："Begin every comment with 'Yes chef'"） |
| `content_mode` | `rule` / `knowledge` / `mixed` | 区分指令性与陈述性内容（发现 C） |
| `size_tier` | `small`/`medium`/`large` | 小文件不适用章节级分类（第 1 节） |

## 6. 方法论警告（必须记下）

本报告基于**标题**匹配，存在系统性偏差：

- 无标题的文件（如 29 B 那个）完全无法分类
- 标题用词与内容主题可能不一致
- `agent_meta` 79% 正是这种偏差的直接结果

**v0.1 正式抽取必须做内容级判定（标题 + 正文），不能只看标题。**

## 7. 待确认

1. 第 4 节修订后的 9 类 —— 认可吗？
2. 第 5 节三个新字段 —— `is_substantive` 是必填（过滤噪声），另两个是否要？
3. `agent_meta` 收紧后的定义（"明确规定 AI 自身行为"）—— 够清晰吗？
