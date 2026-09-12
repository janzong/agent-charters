#!/usr/bin/env python3
"""`boundaries` 三个口径的复算脚本（v0.5 / ruleset_v0.1.8）。

背景：v0.5 文档里曾写"其中 59.9%（309 份）是**专门开了一节**写禁令"，但这个值
**没有任何可复算的定义**撑得住——见 `LIMITATIONS.md` §17。本脚本把三个能复算的口径
全部打印出来，供任何人核对：

  1. 标题通道（= "专门开一节写禁令"的字面含义）：章节标题命中 `HEAD_RULES["boundaries"]`
  2. 标题 ∪ 强模式（不依赖正文弱信号）
  3. 任意一处（数据集 `categories` 里的 `boundaries`，= 85.7%）

用法：`.venv/bin/python work/audit/boundaries_channels.py`
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from agent_charters.taxonomy import (STRONG_PATTERNS, classify,
                                     classify_fulltext, split_sections)

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "data/processed/agent-charters-v0.5.parquet"
MANIFEST = ROOT / "data/raw/full_manifest.jsonl"


def load() -> list[tuple[str, str, bool]]:
    """返回 (repo, 原文, 数据集里是否标了 boundaries)。"""
    man = {}
    with MANIFEST.open(encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            man[(d["repo_full_name"], d["file_path"])] = d["local_file"]
    df = pd.read_parquet(PARQUET)
    df = df[df["is_substantive"] & ~df["is_pointer"]]
    out = []
    for r in df.itertuples():
        path = man.get((r.repo_full_name, r.file_path))
        if not path:
            continue
        out.append((r.repo_full_name,
                    Path(path).read_text(encoding="utf-8", errors="replace"),
                    "boundaries" in r.categories))
    return out


def main() -> int:
    docs = load()
    n = len(docs)
    head = head_or_strong = any_channel = fulltext = 0
    for _repo, text, tagged in docs:
        sections = [(h, b) for h, b in split_sections(text)
                    if not (not h.strip() and len(b.strip()) < 40)]
        h_hit = any(any(e.startswith("heading:")
                        for e in classify(h, b)[1].get("boundaries", []))
                    for h, b in sections)
        strong = any(re.search(p, text, re.I)
                     for p in STRONG_PATTERNS.get("boundaries", []))
        head += h_hit
        head_or_strong += h_hit or strong
        any_channel += tagged
        fulltext += "boundaries" in classify_fulltext(text)[0]

    print(f"可用样本 {n}（v0.5 / ruleset_v0.1.8）\n")
    print(f"1. 标题通道（专门开一节写禁令）  {head:4d}  {head / n * 100:5.1f}%")
    print(f"2. 标题 ∪ 强模式                {head_or_strong:4d}  {head_or_strong / n * 100:5.1f}%")
    print(f"   全文兜底通道单独               {fulltext:4d}  {fulltext / n * 100:5.1f}%")
    print(f"3. 任意一处（数据集字段）        {any_channel:4d}  {any_channel / n * 100:5.1f}%")
    print("\n旧文档里的 59.9%（309 份）对不上以上任何一个口径：见 LIMITATIONS.md §17。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
