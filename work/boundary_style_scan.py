"""候选信号影响面扫描：边界是按什么划的？（H-F8）

假设来源（私有实践 S8）：moya TRUST.md 按「保护区/协作区/扩展区」划、
COLLABORATION.md 按文件名划、rmas-v3 CODEX.md 对到目录——都是**按对象**划。
H-F8 断言：边界主要按"路径"划，而不是按"角色/负责人"划。

方法纪律（D21）：先影响面统计 + 抽验命中，本脚本不改规则、不改数据集。
用法: .venv/bin/python work/boundary_style_scan.py [--sample N]
"""
import random
import re
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/full")
PARQUET = "data/processed/agent-charters-v0.2.parquet"

# 一行"在划边界"的线索（第一版线索太松：抽验发现 never/do not 命中的
# 多是普通英文散文，如 "never from the stored token"，与边界无关。收紧为"必须带对象"）
BOUNDARY_CUE = re.compile(
    # 中文：这些词本身就带强制义
    r"禁止|不得|严禁|只读|仅可|只能(?:改|读|访问)"
    # 英文：否定义动词 + 24 字内的具体动作对象
    r"|\b(?:never|do not|don't|must not|cannot|should not)\b[^\n]{0,24}?"
    r"\b(?:commit|push|edit|modify|change|delete|touch|rename|merge|install|write|send"
    r"|add|use|import|create|remove|revert|overwrite|bypass|skip)\b"
    # 只读 / 角色限定
    r"|read-only|maintainer-only|owner-only", re.I)

# 四档表达方式（按优先级判定：路径 > 具名文件 > 角色 > 纯动作禁止）
# 第一版把 markdown 的 ** 当成 glob，误报严重；现在要求路径必须带 /
TIERS = {
    "path":   re.compile(r"(?<![\w.`])[\w.-]+/[\w.*/-]+|\*[\w-]+\*|\.\./"),
    "file":   re.compile(r"`?[\w-]+\.(?:tsx?|jsx?|py|go|rs|java|rb|php|vue|md|json|ya?ml)`?\b"),
    "role":   re.compile(r"maintainer|owner|@[\w-]+|维护者|负责人"
                         r"|由[\s\S]{0,10}?(?:维护|负责)", re.I),
}


def classify(line: str) -> str:
    for name in ("path", "file", "role"):
        if TIERS[name].search(line):
            return name
    return "pure_prohibition"


def main() -> None:
    sample_n = 6
    if "--sample" in sys.argv:
        sample_n = int(sys.argv[sys.argv.index("--sample") + 1])
    random.seed(2)

    df = pd.read_parquet(PARQUET)
    df = df[df["is_substantive"] & ~df["is_pointer"]].copy()
    df["key"] = df["repo_full_name"].str.replace("/", "__", regex=False)
    boundary_repos = set(df[df["categories"].apply(lambda t: "boundaries" in list(t))]["key"])
    print(f"有 boundaries 类别的文件: {len(boundary_repos)}\n")

    lines = []
    for p in sorted(RAW.glob("*.md")):
        if p.stem not in boundary_repos:
            continue
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip().lstrip("#-*> ").strip()
            if len(s) < 8 or not BOUNDARY_CUE.search(s):
                continue
            lines.append({"repo": p.stem, "text": s, "tier": classify(s)})

    r = pd.DataFrame(lines)
    n = len(r)
    print(f"边界句总数: {n}（来自 {r['repo'].nunique()} 份文件）\n")
    print(f"{'表达方式':<18}{'句数':>7}{'占比':>8}")
    print("-" * 34)
    for t in ("path", "file", "role", "pure_prohibition"):
        c = int((r["tier"] == t).sum())
        print(f"{t:<18}{c:>7}{c/n*100:>7.0f}%")

    # —— 文件级视角：一份章程的边界"主要靠什么表达" ——
    print("\n=== 文件级（335 份 boundaries 文件）")
    per = r.groupby("repo")["tier"].apply(lambda s: set(s))
    has_path = sum(1 for v in per if "path" in v)
    has_role = sum(1 for v in per if "role" in v)
    only_proh = sum(1 for v in per if v == {"pure_prohibition"})
    print(f"  含路径式边界: {has_path} ({has_path/len(per)*100:.0f}%)")
    print(f"  含角色式边界: {has_role} ({has_role/len(per)*100:.0f}%)")
    print(f"  只有纯动作禁令、完全不含路径/文件/角色: {only_proh} ({only_proh/len(per)*100:.0f}%)")

    # —— 追问：公开语料里有多少份在给"多个 AI 智能体"分工？——
    AGENT_NAMES = {"Claude": r"\bClaude\b|claude-code", "Codex": r"\bCodex\b",
                   "Copilot": r"\bCopilot\b", "Cursor": r"\bCursor\b",
                   "Gemini": r"\bGemini\b", "Aider": r"\bAider\b",
                   "Cline": r"\bCline\b", "Windsurf": r"\bWindsurf\b"}
    multi = []
    for p_ in sorted(RAW.glob("*.md")):
        if p_.stem not in boundary_repos:
            continue
        t = p_.read_text(encoding="utf-8", errors="replace")
        found = [k for k, rx in AGENT_NAMES.items() if re.search(rx, t)]
        if len(found) >= 2:
            multi.append((p_.stem, found))
    print(f"\n=== 提到 ≥2 个具名 AI 工具的 boundaries 文件: {len(multi)} / {len(boundary_repos)}"
          f" ({len(multi)/len(boundary_repos)*100:.0f}%)")
    for nm, f in multi[:8]:
        print(f"   [{nm[:30]:<30}] {f}")

    print("\n=== 抽验命中（D21 要求）")
    for t in ("path", "file", "role", "pure_prohibition"):
        sub = r[r["tier"] == t]
        if sub.empty:
            continue
        print(f"\n--- {t} ({len(sub)})")
        for _, row in sub.sample(min(sample_n, len(sub)), random_state=3).iterrows():
            print(f"  [{row['repo'][:26]:<26}] {row['text'][:110]}")


if __name__ == "__main__":
    main()
