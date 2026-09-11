# 字段说明 SCHEMA v0.3

共 **30** 个字段（v0.2 起；v0.1.1 为 26 个）。**粒度：一行 = 一份 `AGENTS.md` 文件。**

> **v0.3 变更**（相对 v0.2）：字段与行数**都不变**（558 行 × 30 列），只换了判定规则
> `ruleset_v0.1.3`——修掉标题通道的子串误命中（`ci` 命中 `Deci|sions` 之类）。
> 覆盖率随之变动：`build_test` 87.9% → **85.7%**，其余类别 ≤0.5pp，方向与排序未变。
> **v0.2 与 v0.3 的覆盖率也不可直接比**（同一批文件、不同规则）。见 `LIMITATIONS.md` §11。
>
> **v0.2 变更**（相对 v0.1.1）：①新增 4 个"知识放在哪里"的结构字段（见下节）；
> ②`is_pointer` 判定收紧（ruleset v0.1.2），转引用文件 11 → 7，可用于统计的实质文件
> 507 → 511。**v0.1.1 与 v0.2 的覆盖率不可直接比较。**

## 标识与可追溯

| 字段 | 类型 | 说明 |
|---|---|---|
| `repo_full_name` | str | `owner/repo` |
| `file_path` | str | 文件在仓库中的路径 |
| `file_sha` | str | Git blob SHA —— **内容指纹，用于去重与精确追溯** |
| `commit_date` | str | 仓库最后推送时间（**内容**的时间） |
| `retrieved_at` | str | **采集**日期（`2026-09-10`）。与 `commit_date` 不同：一个是内容何时存在，一个是何时被取回 |

> `file_sha` 是复现的关键：给定 SHA，任何人可以取回完全相同的字节。
> `retrieved_at` 则保证任何结论都能回答"这是哪一天的世界"。

## 仓库背景

| 字段 | 类型 | 说明 |
|---|---|---|
| `repo_stars` | int | 快照时的 star 数 |
| `repo_language` | str | 主语言 |
| `license` | str | SPDX 标识（可能为空） |

## 文件物理特征

| 字段 | 类型 | 说明 |
|---|---|---|
| `bytes` | int | 字节数（UTF-8） |
| `lines` | int | 行数 |
| `section_count` | int | 标题（`#`~`######`）数量 |
| `size_tier` | str | `small`(<1KB) / `medium`(<10KB) / `large` |
| `doc_language` | str | `en` / `zh` / `mixed` |

## 有效性标记

| 字段 | 类型 | 说明 |
|---|---|---|
| `is_substantive` | bool | **是否为实质内容**。`False` 表示小于 100 字节或仅一行文件引用 |
| `is_pointer` | bool | 正文只是指向另一个文件（如 "See CLAUDE.md"）。这类文件 `categories` 为空是**正确结果** |
| `duplicate_sha_count` | int | 相同 `file_sha` 出现的次数（>1 表示存在复制/模板） |

## 分类结果

| 字段 | 类型 | 说明 |
|---|---|---|
| `categories` | list[str] | 命中的类别（多标签，按字母序）。空列表 = 该文件没有可识别的内容类别 |
| `category_counts` | dict[9] | 每类命中的章节数。**定长稠密：九个类别全部在场，缺席为 `0`，顺序固定为 `CATEGORIES`**。`categories` 是它的稀疏视图 |
| `total_sections_tagged` | int | 所有类别命中次数之和 |

## 内容模式

| 字段 | 类型 | 说明 |
|---|---|---|
| `content_mode` | str | `rule` / `knowledge` / `mixed` |
| `rule_signals` | int | 指令词（do not / must / never / always / avoid / required）出现次数 |

## 知识放在哪里（结构信号，v0.2 新增）

九类按**内容**分类，量不出"我指向别处"。这四个字段补上那个维度——
发现 16 表明近一半章程是**入口**而非全集（见 `FINDINGS.md`）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `routes_outward` | bool | 是否存在外部引用（下面两者任一）。实测 **54%** |
| `imperative_route` | bool | **祈使式**转引："read / see / 详见 X.md"。实测 **49%**（发现 16 的那个 49%） |
| `hard_route` | bool | 指向**知识载体或规则目录**（`memories/`、`MEMORY.md`、`pitfalls`、`.cursor/rules`、`copilot-instructions`…）。实测 **15%** |
| `ref_targets` | int | 检测到几个被指向的路径 |

> `imperative_route` 与 `hard_route` **不是**包含关系：既有"只祈使、不点载体"的
> （200 份），也有"只点载体、没有祈使动词"的（29 份）。`routes_outward` 是两者的并集。
> 口径来源：`work/external_ref_scan.py`（第一版"任意 .md 路径"命中 87%，是假阳性机器，已否决）。
>
> **这里只记录"指向"，不判断"指向的东西是否存在"**——存在性要拿到被指向的文件才能判，
> 属于工具侧能力（`agent-charters refs`，四态：`exists` / `by_name` / `missing` / `unverified`）。

## 抽取元数据（可复现性）

| 字段 | 类型 | 说明 |
|---|---|---|
| `extractor_version` | str | 抽取脚本版本 |
| `taxonomy_version` | str | 分类法**定义**版本（九类是什么） |
| `ruleset_version` | str | 判定**规则**版本。定义没变但规则变了时递增。v0.1.1 加强模式通道；v0.1.2 收紧 `is_pointer` + 补 `structure` 标题词表；v0.1.3 标题通道改词首匹配 + 删裸词 `make`（v0.3 数据集用的就是它） |
| `used_fulltext_fallback` | bool | 是否启用了全文补救通道（说明该文件无有效标题） |
| `strong_patterns` | bool | 是否启用了强模式通道。**v0.1.1 全行为 `true`**；`false` 用于复现 v0.1 基线 |

> **这四个字段必须随数据一起发布。** 分类规则一旦改动，旧结论不再可比。
> 这就是版本规则里"整数位递增＝定义变更、旧结论需重验"的具体落地。

## 示例行

> 取自数据集 v0.3 的真实一行（`google/benchmark`），不是编的。

```json
{
  "repo_full_name": "google/benchmark",
  "file_path": "AGENTS.md",
  "file_sha": "72f2abe0f0621fec538fa753b0b5e3f69a706ec0",
  "commit_date": "2026-09-10T08:35:13Z",
  "retrieved_at": "2026-09-10",
  "repo_stars": 10392,
  "repo_language": "C++",
  "license": "Apache-2.0",
  "bytes": 1716,
  "lines": 45,
  "section_count": 1,
  "size_tier": "medium",
  "doc_language": "en",
  "is_substantive": true,
  "is_pointer": false,
  "content_mode": "mixed",
  "rule_signals": 3,
  "categories": [
    "build_test"
  ],
  "category_counts": {
    "overview": 0,
    "structure": 0,
    "build_test": 1,
    "style": 0,
    "workflow": 0,
    "environment": 0,
    "boundaries": 0,
    "gotchas": 0,
    "agent_meta": 0
  },
  "total_sections_tagged": 1,
  "used_fulltext_fallback": false,
  "strong_patterns": true,
  "extractor_version": "extract_v1",
  "taxonomy_version": "taxonomy_v0.1",
  "ruleset_version": "ruleset_v0.1.3",
  "routes_outward": false,
  "imperative_route": false,
  "hard_route": false,
  "ref_targets": 0,
  "duplicate_sha_count": 1
}
```
