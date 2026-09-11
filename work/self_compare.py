"""把一个仓库/用户的章程文件与 v0.1 语料库做对比。

用法:
  .venv/bin/python work/self_compare.py <标签>=<文件路径> [更多...]
示例:
  .venv/bin/python work/self_compare.py 全局=/home/janz/.codex/AGENTS.md
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_charters.extract import doc_language  # noqa: E402
from agent_charters.taxonomy import (CATEGORIES, classify,  # noqa: E402
                                     classify_fulltext, split_sections)


def analyze(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    size = len(text.encode("utf-8"))
    sections = split_sections(text)
    counts: dict[str, int] = {}
    for head, body in sections:
        if not head.strip() and len(body.strip()) < 40:
            continue
        tags, _ = classify(head, body)
        for t in tags:
            counts[t] = counts.get(t, 0) + 1
    if not counts:
        ft, _ = classify_fulltext(text)
        counts = {t: 1 for t in ft}
    return {
        "bytes": size,
        "lines": text.count("\n") + 1,
        "sections": len(sections),
        "doc_language": doc_language(text),
        "categories": sorted(counts),
        "counts": counts,
    }


def main() -> None:
    pairs = [a.split("=", 1) for a in sys.argv[1:]]
    df = pd.read_parquet("data/processed/agent-charters-v0.2.parquet")
    corpus = df[df["is_substantive"] & ~df["is_pointer"]]
    n = len(corpus)
    corpus_cov = {c: sum(1 for t in corpus["categories"] if c in t) * 100 // n
                  for c in CATEGORIES}

    print(f"语料库基线：{n} 份实质文件\n")
    print(f"{'类别':<14}{'语料库':>8}   你的文件")
    print("-" * 46)

    mine_all: set[str] = set()
    for label, path in pairs:
        r = analyze(path)
        mine_all.update(r["categories"])
        print(f"\n### {label}  ({r['bytes']}B, {r['lines']} 行, "
              f"{r['sections']} 章节, {r['doc_language']})")
        for c in CATEGORIES:
            mark = "✓" if c in r["categories"] else "—"
            cnt = r["counts"].get(c, 0)
            print(f"  {c:<14}{corpus_cov[c]:>6}%   {mark} {cnt if cnt else ''}")

    print("\n" + "=" * 46)
    print("汇总")
    print("=" * 46)
    absent = [c for c in CATEGORIES if c not in mine_all]
    print(f"\n你的全部文件合计覆盖 {len(mine_all)}/9 类")
    print(f"完全没出现的类别：{absent if absent else '（无）'}")

    print("\n语料库中覆盖率高但你没有的（按差距排）：")
    gaps = sorted(((corpus_cov[c], c) for c in absent), reverse=True)
    for cov, c in gaps[:6]:
        print(f"  {c:<14} 语料库覆盖率 {cov}%")

    pct = (corpus["bytes"] < analyze(pairs[0][1])["bytes"]).mean() * 100
    print(f"\n体量：你的主文件 {analyze(pairs[0][1])['bytes']}B，"
          f"在语料库中位于第 {pct:.0f} 百分位")


if __name__ == "__main__":
    main()
