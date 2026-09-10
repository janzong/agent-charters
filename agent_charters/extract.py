"""抽取逻辑：把一份 AGENTS.md 文本变成结构化记录。"""

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

import re as _re

from .taxonomy import (CATEGORIES, IMPERATIVE_PAT, MD_LINK_PAT, POINTER_PAT,
                       RULESET_VERSION, STRONG_PATTERNS, VERSION, classify,
                       classify_fulltext, split_sections)

EXTRACTOR_VERSION = "extract_v1"


def doc_language(text: str) -> str:
    """粗判文档语言：en / zh / mixed。"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk == 0:
        return "en"
    return "zh" if cjk * 12 > letters else "mixed"


def analyze_text(text: str, meta: dict | None = None, *,
                 strong: bool = True) -> dict:
    """分析一份章程文本，返回与语料库同构的记录。

    meta 可提供 repo_full_name / repo_stars / repo_language / license 等背景字段。
    strong=False 关闭强模式通道，用于回归对比（语料库 v0.1 基线即无强模式）。
    """
    meta = dict(meta or {})
    size = len(text.encode("utf-8"))
    sections = split_sections(text)

    tag_counts: Counter = Counter()
    for head, body in sections:
        if not head.strip() and len(body.strip()) < 40:
            continue
        tags, _ = classify(head, body)
        for t in tags:
            tag_counts[t] += 1

    # 无标题文件的补救：章节分类落空时启用全文级规则
    used_fulltext = False
    if not tag_counts:
        ft_tags, _ = classify_fulltext(text)
        if ft_tags:
            used_fulltext = True
            for t in ft_tags:
                tag_counts[t] += 1

    # 强模式通道：总是运行。跨语言有效，防止中文文档被误判为"什么都没有"。
    if strong:
        for cat, pats in STRONG_PATTERNS.items():
            if cat in tag_counts:      # 标题通道已命中，不再叠计数
                continue
            for p in pats:
                if _re.search(p, text, _re.I):
                    tag_counts[cat] += 1
                    break

    is_sub = size >= 100 and not re.fullmatch(
        r"\s*[^\n]{0,80}\.(?:md|mdc|txt)\s*", text)
    md_links = len(MD_LINK_PAT.findall(text))
    is_pointer = (bool(POINTER_PAT.search(text)) or md_links >= 2) and size < 2000
    rule_signals = len(IMPERATIVE_PAT.findall(text))
    mode = ("rule" if rule_signals >= 5 else
            "knowledge" if rule_signals <= 1 else "mixed")

    record = {
        "repo_full_name": meta.get("repo_full_name"),
        "file_path": meta.get("file_path", "AGENTS.md"),
        "file_sha": meta.get("file_sha"),
        "commit_date": meta.get("commit_date"),
        "retrieved_at": meta.get("retrieved_at"),
        "repo_stars": meta.get("repo_stars"),
        "repo_language": meta.get("repo_language"),
        "license": meta.get("license"),
        "bytes": size,
        "lines": text.count("\n") + 1,
        "section_count": len(sections),
        "doc_language": doc_language(text),
        "size_tier": ("small" if size < 1024 else
                      "medium" if size < 10240 else "large"),
        "is_substantive": is_sub,
        "is_pointer": is_pointer,
        "content_mode": mode,
        "rule_signals": rule_signals,
        "categories": sorted(tag_counts),
        "category_counts": dict(tag_counts),
        "total_sections_tagged": sum(tag_counts.values()),
        "used_fulltext_fallback": used_fulltext,
        "strong_patterns": strong,
        "extractor_version": EXTRACTOR_VERSION,
        "taxonomy_version": VERSION,
        "ruleset_version": RULESET_VERSION,
    }
    return record


def analyze_file(path: str | Path, meta: dict | None = None) -> dict:
    """分析一个章程文件。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    m = dict(meta or {})
    m.setdefault("file_path", p.name)
    return analyze_text(text, m)


_DATA = Path(__file__).parent / "data" / "agent-charters-v0.1.parquet"


def load_corpus(path: str | Path | None = None) -> pd.DataFrame:
    """加载随包发布的语料库（558 份）。"""
    return pd.read_parquet(path or _DATA)


def substantive(df: pd.DataFrame) -> pd.DataFrame:
    """过滤出可用于统计的实质文件（排除空壳与转引用）。"""
    return df[df["is_substantive"] & ~df["is_pointer"]]


def category_coverage(df: pd.DataFrame) -> dict[str, int]:
    """各类别的覆盖率（百分比，整数）。"""
    n = len(df) or 1
    return {c: int(sum(1 for tags in df["categories"] if c in tags) * 100 / n)
            for c in CATEGORIES}
