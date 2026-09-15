#!/usr/bin/env python3
"""`hard_route`（章程是否指向知识库/规则目录）× `gotchas`（有没有写坑）。

**为什么有这个脚本**：2026-09-14 一位外部读者（dev.to 的 `raknaos`）问
"坑的缺口是写作习惯还是复核习惯——把复盘当事后必产物的团队，这一格得分更高吗"。
手上唯一能测的代理变量就是 `hard_route`（v0.2 起进数据集的字段：章程是把知识
**指去别处**，还是自己写全）。这个脚本把它算成可复算的两个数和一张分层表，
免得那两条回复里的数字只活在回复里（D25 的纪律：对外引用的比例必须算得出来）。

    .venv/bin/python work/hard_route_gotchas.py

输出：2×2 列联表 + 比值 + Fisher 双尾 p（无 scipy 时手算）+ 体量四分位分层。
**这不是因果结论**：横截面、代理变量测的是"指向外部载体"的写法而非"团队有没有复盘制度"；
而且"有 gotchas 一节"≠"里面写的是坑"（120 条人工标注里 34% 根本不是坑）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_charters import load_corpus, substantive  # noqa: E402


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """双尾 Fisher 精确检验（不依赖 scipy）。"""
    try:
        from scipy.stats import fisher_exact
        return float(fisher_exact([[a, b], [c, d]])[1])
    except ImportError:
        from math import comb
        n, r1, c1 = a + b + c + d, a + b, a + c
        if min(r1, c1, n - r1, n - c1) < 0:
            return float("nan")

        def p(x):
            return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)

        obs = p(a)
        lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
        return sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs + 1e-12)


def main() -> int:
    # 语料库已改成纯标准库的 Corpus（随包不再依赖 pandas）；分析脚本里再转回
    # DataFrame 最省事——work/ 不进 wheel，也不进 sdist。
    df = pd.DataFrame(substantive(load_corpus()))
    df["has_gotchas"] = df["categories"].map(lambda x: "gotchas" in x)
    df["hard"] = df["hard_route"] == True  # noqa: E712
    n = len(df)

    a = int((df["hard"] & df["has_gotchas"]).sum())
    b = int((df["hard"] & ~df["has_gotchas"]).sum())
    c = int((~df["hard"] & df["has_gotchas"]).sum())
    d = int((~df["hard"] & ~df["has_gotchas"]).sum())
    p_hr, p_rest = a / (a + b), c / (c + d)

    print(f"实质文件 {n}\n")
    print("2×2（行=hard_route，列=写了 gotchas）")
    print(f"  指向外部载体   {a:>4} 有 / {b:>4} 无   → {100 * p_hr:.1f}%")
    print(f"  其余           {c:>4} 有 / {d:>4} 无   → {100 * p_rest:.1f}%")
    print(f"\n比值 {p_hr / p_rest:.2f}×    Fisher 双尾 p = {fisher_two_sided(a, b, c, d):.4f}")
    print(f"\n体量中位数：指向外部载体 {int(df.loc[df['hard'], 'bytes'].median())} B"
          f" ｜ 其余 {int(df.loc[~df['hard'], 'bytes'].median())} B"
          f"（体量是明显的混杂因素，所以要分层看）")

    df["q"] = pd.qcut(df["bytes"], 4, labels=["Q1 最小", "Q2", "Q3", "Q4 最大"])
    print("\n按体量四分位分层：")
    for q, g in df.groupby("q", observed=True):
        hr, rest = g[g["hard"]]["has_gotchas"], g[~g["hard"]]["has_gotchas"]
        f = lambda s: f"{int(s.sum())}/{len(s)} = {100 * s.mean():.1f}%" if len(s) else "—"  # noqa: E731
        print(f"  {q:<8} 指向外部载体 {f(hr):<18} 其余 {f(rest)}")
    print("\n边界：横截面（方向未知）｜代理变量测的是「指向外部载体」的写法，不是复盘制度｜"
          "有 gotchas 一节 ≠ 写的是坑（34% 不是）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
