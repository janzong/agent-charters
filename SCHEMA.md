# 字段说明 SCHEMA v0.1

共 26 个字段（v0.1.1 起）。**粒度：一行 = 一份 `AGENTS.md` 文件。**

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

## 抽取元数据（可复现性）

| 字段 | 类型 | 说明 |
|---|---|---|
| `extractor_version` | str | 抽取脚本版本 |
| `taxonomy_version` | str | 分类法**定义**版本（九类是什么） |
| `ruleset_version` | str | 判定**规则**版本。定义没变但规则变了（v0.1.1 加强模式通道）时递增 |
| `used_fulltext_fallback` | bool | 是否启用了全文补救通道（说明该文件无有效标题） |
| `strong_patterns` | bool | 是否启用了强模式通道。**v0.1.1 全行为 `true`**；`false` 用于复现 v0.1 基线 |

> **这四个字段必须随数据一起发布。** 分类规则一旦改动，旧结论不再可比。
> 这就是版本规则里"整数位递增＝定义变更、旧结论需重验"的具体落地。

## 示例行

```json
{
  "repo_full_name": "google/benchmark",
  "file_path": "AGENTS.md",
  "file_sha": "…",
  "commit_date": "2026-09-08T04:11:07Z",
  "retrieved_at": "2026-09-10",
  "repo_stars": 9200,
  "repo_language": "C++",
  "license": "Apache-2.0",
  "bytes": 1716,
  "lines": 41,
  "section_count": 5,
  "size_tier": "medium",
  "doc_language": "en",
  "is_substantive": true,
  "is_pointer": false,
  "content_mode": "mixed",
  "rule_signals": 7,
  "categories": ["agent_meta", "boundaries"],
  "category_counts": {"overview": 0, "structure": 0, "build_test": 0, "style": 0,
                      "workflow": 0, "environment": 0, "boundaries": 2,
                      "gotchas": 0, "agent_meta": 1},
  "total_sections_tagged": 3,
  "used_fulltext_fallback": false,
  "strong_patterns": true,
  "extractor_version": "extract_v1",
  "taxonomy_version": "taxonomy_v0.1",
  "ruleset_version": "ruleset_v0.1.1",
  "duplicate_sha_count": 1
}
```
