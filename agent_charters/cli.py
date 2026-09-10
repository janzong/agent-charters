"""agent-charters 命令行入口。

  agent-charters stats                     全局分布
  agent-charters compare FILE [FILE...]    把你的章程与语料库对比
  agent-charters show CATEGORY             看某类别的真实样本
"""

import argparse
import sys
from collections import Counter

from .extract import (CATEGORIES, analyze_file, category_coverage, load_corpus,
                      substantive)


def _bar(pct: int, width: int = 28) -> str:
    filled = int(round(pct / 100 * width))
    return "█" * filled + "·" * (width - filled)


def cmd_stats(args: argparse.Namespace) -> int:
    df = load_corpus(args.data) if args.data else load_corpus()
    sub = substantive(df)
    ruleset = (df["ruleset_version"].iloc[0]
               if "ruleset_version" in df.columns else "ruleset_v0.1")
    print(f"语料库 v0.1.1 ｜ 抓取 {len(df)} 份 ｜ 实质内容 {len(sub)} 份 "
          f"｜ 快照 {df['retrieved_at'].iloc[0]} ｜ {ruleset}\n")

    print("类别覆盖（实质文件）")
    print("-" * 58)
    cov = category_coverage(sub)
    for c, pct in sorted(cov.items(), key=lambda x: -x[1]):
        print(f"  {c:<13} {pct:>3}%  {_bar(pct)}")

    print("\n内容模式")
    print("-" * 58)
    total = len(sub)
    for mode, cnt in Counter(sub["content_mode"]).most_common():
        print(f"  {mode:<13} {cnt:>4}  {cnt * 100 // total:>3}%")

    print("\n文档语言")
    print("-" * 58)
    for lang, cnt in Counter(sub["doc_language"]).most_common():
        print(f"  {lang:<13} {cnt:>4}  {cnt * 100 // total:>3}%")

    print("\n体量")
    print("-" * 58)
    b = sub["bytes"]
    print(f"  中位数 {int(b.median())} B ｜ 均值 {int(b.mean())} B "
          f"｜ 最大 {int(b.max())} B")
    print(f"  平均标签数 {sub['categories'].map(len).mean():.1f}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    corpus = substantive(load_corpus(args.data) if args.data else load_corpus())
    cov = category_coverage(corpus)
    n = len(corpus)

    snap = load_corpus(args.data).iloc[0]["retrieved_at"] if args.data else \
        load_corpus().iloc[0]["retrieved_at"]
    print(f"语料库基线：{n} 份实质文件（快照 {snap}）\n")
    print(f"{'类别':<14}{'语料库':>7}    你的文件")
    print("-" * 52)

    all_mine: set[str] = set()
    for path in args.files:
        rec = analyze_file(path)
        all_mine.update(rec["categories"])
        state = "pointer（无正文内容）" if rec["is_pointer"] else f"{rec['bytes']}B"
        print(f"\n### {path}  [{state}, {rec['doc_language']}, "
              f"{rec['section_count']} 章节, {rec['content_mode']}]")
        for c in CATEGORIES:
            mark = "✓" if c in rec["categories"] else "—"
            cnt = rec["category_counts"].get(c, 0)
            extra = f" x{cnt}" if cnt else ""
            print(f"  {c:<14}{cov[c]:>5}%    {mark}{extra}")

    print("\n" + "=" * 52)
    absent = [c for c in CATEGORIES if c not in all_mine]
    print(f"合计覆盖 {len(all_mine)}/{len(CATEGORIES)} 类")
    if absent:
        print("\n你没有、但语料库写得最多的：")
        for pct, c in sorted(((cov[c], c) for c in absent), reverse=True):
            print(f"  {c:<14} 语料库覆盖率 {pct}%")
    else:
        print("九类全覆盖——超过语料库平均（4.4 类）。")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    df = substantive(load_corpus(args.data) if args.data else load_corpus())
    hit = df[df["categories"].map(lambda t: args.category in t)]
    if hit.empty:
        print(f"没有文件命中类别 {args.category}")
        return 1
    print(f"类别 {args.category}：{len(hit)} 份命中，"
          f"展示前 {min(args.limit, len(hit))} 份\n")
    # 按该类别的章节数降序——最能代表这个类别的排在前面
    hit = hit.assign(_n=hit["category_counts"].map(
        lambda d: d.get(args.category, 0))).sort_values("_n", ascending=False)
    for _, r in hit.head(args.limit).iterrows():
        lang = r["repo_language"] if isinstance(r["repo_language"], str) else "-"
        lic = r["license"] if isinstance(r["license"], str) else "-"
        print(f"  {r['repo_full_name']:<40} {int(r['bytes']):>6}B  "
              f"{lang:<12} {lic:<14} {args.category} x{int(r['_n'])}")
    print(f"\n取原文：https://github.com/<repo>/blob/HEAD/{df['file_path'].iloc[0]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="agent-charters",
        description="人写给 AI 智能体的书面规约语料库（v0.1）")
    p.add_argument("--data", help="自定义语料库 parquet 路径（默认用随包的 v0.1）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("stats", help="全局分布")
    s1.set_defaults(func=cmd_stats)

    s2 = sub.add_parser("compare", help="把你的章程与语料库对比")
    s2.add_argument("files", nargs="+", help="一个或多个章程文件")
    s2.set_defaults(func=cmd_compare)

    s3 = sub.add_parser("show", help="看某类别的真实样本")
    s3.add_argument("category", choices=CATEGORIES)
    s3.add_argument("--limit", type=int, default=10)
    s3.set_defaults(func=cmd_show)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
