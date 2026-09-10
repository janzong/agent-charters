# 字段说明 SCHEMA v0.1

共 23 个字段。**粒度：一行 = 一份 `AGENTS.md` 文件。**

## 标识与可追溯

| 字段 | 类型 | 说明 |
|---|---|---|
| `repo_full_name` | str | `owner/repo` |
| `file_path` | str | 文件在仓库中的路径 |
| `file_sha` | str | Git blob SHA —— **内容指纹，用于去重与精确追溯** |
| `commit_date` | str | 仓库最后推送时间（快照时间点） |

> `file_sha` 是复现的关键：给定 SHA，任何人可以取回完全相同的字节。

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
| `categories` | list[str] | 命中的类别（多标签，按字母序） |
| `category_counts` | dict | 每类命中的章节数 |
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
| `taxonomy_version` | str | 分类法版本 |
| `used_fulltext_fallback` | bool | 是否启用了全文补救通道（说明该文件无有效标题） |

> **这三个字段必须随数据一起发布。** 分类规则一旦改动，旧结论不再可比。
> 这就是版本规则里"整数位递增＝定义变更、旧结论需重验"的具体落地。

## 示例行

```json
{
  "repo_full_name": "google/benchmark",
  "file_path": "AGENTS.md",
  "file_sha": "…",
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
  "categories": ["agent_meta", "boundaries"],
  "category_counts": {"agent_meta": 1, "boundaries": 2},
  "extractor_version": "extract_v1",
  "taxonomy_version": "taxonomy_v0.1"
}
```
