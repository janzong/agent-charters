"""对照实验：机器生成的 AGENTS.md vs 仓库里人写的那份。

用法: .venv/bin/python work/auto_vs_human.py 标签:人写文件:生成文件 [更多...]

设计要点（不这么做实验就没有意义）：
  生成时**人写的那份必须已从仓库移走**，否则生成器会抄，结果不可用。
  本脚本只做对比，不负责生成。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_charters import analyze_file, category_coverage, load_corpus, substantive  # noqa: E402
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

base = category_coverage(substantive(load_corpus()))


def row(label: str, human: str, auto: str) -> dict:
    h, a = analyze_file(human), analyze_file(auto)
    hs, as_ = set(h["categories"]), set(a["categories"])
    return {"label": label, "h": h, "a": a, "hs": hs, "as": as_}


def main(pairs: list[str]) -> None:
    recs = []
    for spec in pairs:
        label, human, auto = spec.split(":", 2)
        recs.append(row(label, human, auto))

    print(f"{'仓库':<16}{'类数(人/机)':>12}{'字节(人/机)':>18}{'章节(人/机)':>14}")
    print("-" * 62)
    for r in recs:
        print(f"{r['label']:<16}"
              f"{len(r['hs']):>5} /{len(r['as']):<5}"
              f"{r['h']['bytes']:>9} /{r['a']['bytes']:<7}"
              f"{r['h']['section_count']:>6} /{r['a']['section_count']:<6}")

    print(f"\n{'类别':<14}" + "".join(f"{r['label'][:8]:>10}" for r in recs)
          + f"{'人写命中':>9}{'机器命中':>9}")
    print("-" * (14 + 10 * len(recs) + 18))
    for c in CATEGORIES:
        cells = ""
        for r in recs:
            hh, aa = c in r["hs"], c in r["as"]
            cells += f"{'✓✓' if hh and aa else '✓—' if hh else '—✓' if aa else '——':>10}"
        nh = sum(1 for r in recs if c in r["hs"])
        na = sum(1 for r in recs if c in r["as"])
        print(f"{c:<14}{cells}{nh:>9}{na:>9}")

    only_h = [c for c in CATEGORIES
              if sum(1 for r in recs if c in r["hs"]) > sum(1 for r in recs if c in r["as"])]
    both = [c for c in CATEGORIES
            if sum(1 for r in recs if c in r["hs"]) and sum(1 for r in recs if c in r["as"])]
    only_a = [c for c in CATEGORIES
              if sum(1 for r in recs if c in r["as"]) > sum(1 for r in recs if c in r["hs"])]
    print("\n只有人写到的类别：", ", ".join(only_h) or "（无）")
    print("两边都常写到：    ", ", ".join(both) or "（无）")
    print("只有机器写到的：  ", ", ".join(only_a) or "（无）")
    print(f"\n平均类数：人写 {sum(len(r['hs']) for r in recs)/len(recs):.1f}"
          f" ｜ 机器 {sum(len(r['as']) for r in recs)/len(recs):.1f}")
    print(f"平均字节：人写 {sum(r['h']['bytes'] for r in recs)//len(recs)}"
          f" ｜ 机器 {sum(r['a']['bytes'] for r in recs)//len(recs)}")
    # 机器写了但语料库里罕见的内容 vs 人写了但机器漏掉的内容——两个方向的证据都要留
    print("\n例证（人工阅读用）：")
    for r in recs:
        miss = sorted(r["hs"] - r["as"])
        print(f"  {r['label']}: 机器漏掉 {miss} ｜ 机器多出 {sorted(r['as'] - r['hs'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
