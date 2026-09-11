"""抽取逻辑：把一份 AGENTS.md 文本变成结构化记录。"""

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

import re as _re

from .refs import find_refs
from .taxonomy import (CATEGORIES, IMPERATIVE_PAT, MD_LINK_PAT, POINTER_PAT,
                       POINTER_SEMANTIC, RULESET_VERSION, STRONG_PATTERNS,
                       VERSION, classify, classify_fulltext, content_bytes,
                       split_sections)

EXTRACTOR_VERSION = "extract_v1"

# 数据集版本：决定发布文件名里的版本位（agent-charters-<DS>.parquet）。
# 与工具版本解耦（D24）——工具在迭代，数据没变时不该跟着升。
DATASET_VERSION = "v0.2"


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
    # v0.1.2：加"壳厚"门与语义门。原先 = (出现 see/read X.md 或 ≥2 个 .md 链接) 且 <2000B，
    # 于是"提到两个 .md 文件名"≈"只是指针"，把短但有料的章程剔出了统计（11 份里 5 份误判）。
    # 两个门必须都过：①薄（去链接去路径后 <400B）②确实在指向（出现 see/read X.md 或 ≥2 个 .md）
    # 或作者自陈"本文件只是路由"。
    thin = content_bytes(text) < 400
    routey = bool(POINTER_PAT.search(text)) or md_links >= 2
    is_pointer = size < 2000 and (bool(POINTER_SEMANTIC.search(text))
                                  or (thin and routey))
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
        # 定长稠密计数：九个类别全都出现，缺席写 0，顺序固定为 CATEGORIES。
        # 两个理由，都踩过坑：
        # 1) 稀疏 dict 经 parquet 会被展开成 struct，缺席项变 None/NaN——
        #    下游拿到的是 {"gotchas": None} 而不是 0，极易算错。
        # 2) 稀疏 dict 的键顺序来自 set 迭代顺序，而它依赖 PYTHONHASHSEED，
        #    同一份数据两次生成字节不同，发布资产的校验和无法复现。
        "category_counts": {c: tag_counts.get(c, 0) for c in CATEGORIES},
        "total_sections_tagged": sum(tag_counts.values()),
        "used_fulltext_fallback": used_fulltext,
        "strong_patterns": strong,
        "extractor_version": EXTRACTOR_VERSION,
        "taxonomy_version": VERSION,
        "ruleset_version": RULESET_VERSION,
        # v0.2（D28）：知识放在哪里——结构信号，不属于九类中的任何一类。
        # 只有指向，没有存在性判断（抽不到被指向的文件），存在性在 CLI refs 里现查。
        # 这四个字段是为了让文档里的口径**可从数据集复算**（D28 立的规矩）：
        #   imperative_route = 祈使转引（"read / 详见 X.md"）——FINDINGS 16 的 49%
        #   hard_route       = 指向知识库/规则目录——FINDINGS 16 的 15%
        #   routes_outward   = 两者任一（54%）；缺了 imperative_route，49% 那个数只能
        #                      靠 work/external_ref_scan.py + data/raw 才算得出。
        "_refs": find_refs(text),
    }
    _r = record.pop("_refs")
    record["routes_outward"] = _r["routes_outward"]
    record["imperative_route"] = _r["imperative"]
    record["hard_route"] = _r["hard"]
    record["ref_targets"] = len(_r["targets"])
    return record


def analyze_file(path: str | Path, meta: dict | None = None) -> dict:
    """分析一个章程文件。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    m = dict(meta or {})
    m.setdefault("file_path", p.name)
    return analyze_text(text, m)


_DATA = (Path(__file__).parent / "data"
         / f"agent-charters-{DATASET_VERSION}.parquet")


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
