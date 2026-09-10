"""候选信号影响面扫描：章程是否"把知识外包给外部载体"。

起因（私有实践假设 F9，见 work/SELF-TRACE.md 第 9 节与 STATE.md D26/D27）：
当事人自己的章程里 gotchas 为空，但正文明确指向 .github/memories/。
若这类占比不低，则语料库 14% 的 gotchas 覆盖率是"量错了对象"，不是"人没写"。

方法纪律（D21）：先做影响面统计 + 抽验命中，再决定是否改规则。本脚本**不改规则、不改数据集**。

已记录的假阳性教训：第一版用「文本里出现任意 .md 路径」做信号，命中 87%（442/507），
抽验 12 条后判定为假阳性机器——README 列表、PR 模板、日志文件名全被算进来。
故最终口径收紧为「祈使转引」+「知识/规则载体专名」。

用法: .venv/bin/python work/external_ref_scan.py
"""
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/full")
PARQUET = "data/processed/agent-charters-v0.1.parquet"

# —— 已否决的口径（留档，别再用）——
REJECTED = re.compile(r"[\w\-./]*[\w\-]+\.(?:md|mdc|txt)\b", re.I)

# —— 最终口径 ——
CANDIDATES = {
    # 祈使式转引：把 agent 指去读另一个文件
    "imperative_en": re.compile(
        r"(?i)\b(?:read|consult|refer to|check|see|follow)\b"
        r"[^\n]{0,50}?[\w\-./]*[\w\-]+\.(?:md|mdc|txt)\b"),
    "imperative_zh": re.compile(
        r"(?:先读|必读|必须先|请读|阅读|参见|详见|参阅|参考[^\n]{0,4}?\.md)"
        r"[^\n]{0,30}?[\w\-./]*[\w\-]+\.md"),
    # 知识/记忆载体专名（强信号）
    "knowledge_store": re.compile(
        r"(?i)memories/|MEMORY\.md|pitfalls|lessons\.md|lessons-learned"
        r"|知识库|记忆文件|踩坑记录|经验记录|DECISIONS\.md|ADR\b"),
    # 规则目录（强信号）
    "rules_dir": re.compile(
        r"(?i)\.cursor/rules|\.github/instructions|copilot-instructions"
        r"|(?<!\w)rules/[\w\-]+\.md"),
}


def main() -> None:
    df = pd.read_parquet(PARQUET)
    df = df[df["is_substantive"] & ~df["is_pointer"]].copy()
    df["gotchas"] = df["categories"].apply(lambda t: "gotchas" in list(t))
    df["key"] = df["repo_full_name"].str.replace("/", "__", regex=False)
    df = df.set_index("key")

    rows = []
    for path in sorted(RAW.glob("*.md")):
        if path.stem not in df.index:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rec = {"repo": df.loc[path.stem, "repo_full_name"],
               "gotchas": bool(df.loc[path.stem, "gotchas"]),
               "rejected_broad": bool(REJECTED.search(text))}
        for name, rx in CANDIDATES.items():
            rec[name] = bool(rx.search(text))
        rows.append(rec)

    r = pd.DataFrame(rows)
    n = len(r)
    r["route"] = r["imperative_en"] | r["imperative_zh"] | r["knowledge_store"] | r["rules_dir"]
    r["hard"] = r["knowledge_store"] | r["rules_dir"]

    print(f"扫描 {n} 份实质文件\n")
    print(f"（留档）已否决的宽口径 '任意 .md 路径' 命中 "
          f"{r['rejected_broad'].sum()} 份 = {r['rejected_broad'].mean()*100:.0f}%"
          f"  ← 假阳性，勿用\n")

    print(f"{'信号':<24}{'命中':>6}{'占比':>8}")
    print("-" * 40)
    for name in CANDIDATES:
        print(f"{name:<24}{r[name].sum():>6}{r[name].mean()*100:>7.0f}%")
    print(f"{'任一外包信号':<24}{r['route'].sum():>6}{r['route'].mean()*100:>7.0f}%")
    print(f"{'强外包(store|rules)':<24}{r['hard'].sum():>6}{r['hard'].mean()*100:>7.0f}%")

    print("\n=== 交叉表：强外包 × 有 gotchas")
    print(pd.crosstab(r["hard"], r["gotchas"],
                      rownames=["强外包"], colnames=["有gotchas"]))
    ng, g = r[~r["gotchas"]], r[r["gotchas"]]
    print(f"\ngotchas 缺席 {len(ng)} 份 → 强外包率 {ng['hard'].mean()*100:.1f}%")
    print(f"gotchas 在场 {len(g)} 份 → 强外包率 {g['hard'].mean()*100:.1f}%")
    print("\n结论：外包率与 gotchas 在场**正相关**，'替代假说'不成立——"
          "外包是增量，不是替换。")


if __name__ == "__main__":
    main()
