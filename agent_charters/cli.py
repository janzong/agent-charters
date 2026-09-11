"""agent-charters 命令行入口。

  agent-charters stats                     全局分布
  agent-charters brief [FILE...]           写章程前的检查清单 + 可粘贴的提示词
  agent-charters compare FILE [FILE...]    把你的章程与语料库对比
  agent-charters show CATEGORY             看某类别的真实样本
  agent-charters refs FILE [FILE...]       看章程的外部引用与断链
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

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


def cmd_brief(args: argparse.Namespace) -> int:
    from .brief import render
    df = load_corpus(args.data) if args.data else None
    print(render(args.files, lang=args.lang, df=df))
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


def cmd_refs(args: argparse.Namespace) -> int:
    """看章程的外部引用：是自足的，还是把知识指去了别处。"""
    from .refs import find_refs, resolve_targets
    for f in args.files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        rec = find_refs(text)
        kind = ("知识库/规则目录" if rec["hard"]
                else "祈使转引" if rec["imperative"] else "自足")
        print(f"\n{f}")
        print(f"  类型：{kind}   指向 {len(rec['targets'])} 个路径")
        if not rec["routes_outward"]:
            print("  未发现外部引用——该章程是自足的。")
            continue
        res = resolve_targets(rec, Path(f).parent)
        order = {"missing": 0, "unverified": 1, "by_name": 2, "exists": 3}
        for t, st in sorted(res, key=lambda x: order[x[1]]):
            mark = {"exists": "✓", "by_name": "~", "missing": "✗",
                    "unverified": "?"}[st]
            print(f"    {mark} {t}")
        bad = [t for t, st in res if st == "missing"]
        unv = [t for t, st in res if st == "unverified"]
        if bad:
            print(f"  ⚠ {len(bad)} 个指向的路径找不到——指错方向比不指更糟。")
        if unv:
            print(f"  (基准目录不是仓库根，{len(unv)} 个指向无法核验——"
                  f"若章程指向的是别的项目，这是正常的)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="agent-charters",
        description="人写给 AI 智能体的书面规约语料库（数据 v0.1.1 / 工具 v0.2.0）")
    p.add_argument("--data", help="自定义语料库 parquet 路径（默认用随包的 v0.1.1）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("stats", help="全局分布")
    s1.set_defaults(func=cmd_stats)

    sb = sub.add_parser("brief",
                        help="写章程前的检查清单 + 可直接粘贴的生成提示词")
    sb.add_argument("files", nargs="*",
                    help="可选：已有的章程文件，清单会标出你缺了哪些")
    sb.add_argument("--lang", choices=["en", "zh"], default="en",
                    help="提示词语言（默认 en：喂给模型最稳）")
    sb.set_defaults(func=cmd_brief)

    s2 = sub.add_parser("compare", help="把你的章程与语料库对比")
    s2.add_argument("files", nargs="+", help="一个或多个章程文件")
    s2.set_defaults(func=cmd_compare)

    s4 = sub.add_parser("refs", help="看章程的外部引用与断链")
    s4.add_argument("files", nargs="+", help="章程文件路径")
    s4.set_defaults(func=cmd_refs)

    s3 = sub.add_parser("show", help="看某类别的真实样本")
    s3.add_argument("category", choices=CATEGORIES)
    s3.add_argument("--limit", type=int, default=10)
    s3.set_defaults(func=cmd_show)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
