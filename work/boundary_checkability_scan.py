"""边界「可检查性」切分（对外回复用，只读）。

问题（dev.to 4692300 / mnemehq 3fkbp）：禁令里多少指向可检查对象（路径/import/命令/阈值），
多少只是泛泛陈述？口径：行级正则，非语义；数据 v0.5（516 实质非 pointer）。
用法: .venv/bin/python work/boundary_checkability_scan.py
"""
import re
from pathlib import Path
import pandas as pd

RAW = Path("data/raw/full")
PARQUET = "data/processed/agent-charters-v0.5.parquet"

BOUNDARY_CUE = re.compile(
    r"禁止|不得|严禁|只读|仅可|只能(?:改|读|访问)"
    r"|\b(?:never|do not|don't|must not|cannot|should not)\b[^\n]{0,24}?"
    r"\b(?:commit|push|edit|modify|change|delete|touch|rename|merge|install|write|send"
    r"|add|use|import|create|remove|revert|overwrite|bypass|skip)\b"
    r"|read-only|maintainer-only|owner-only", re.I)

TIERS = {
    "path": re.compile(
        r"(?<![\w.`])(?:\.\.?/[\w.*-]+"
        r"|[\w.-]+/[\w.-]+/[\w.*-]+"
        r"|[\w.-]+/[\w.-]+\.(?:tsx?|jsx?|py|go|rs|java|rb|php|vue|md|json|ya?ml|toml|sh|sql|env)"
        r"|[\w.-]+/(?:src|app|lib|tests?|test|docs?|scripts?|crates?|packages?|vendor|config|internal|cmd|pkg|api|web|ui|core|db|migrations?|\.github)\b)"),
    "file": re.compile(r"`?[\w-]+\.(?:tsx?|jsx?|py|go|rs|java|rb|php|vue|md|json|ya?ml|toml|sh|sql|env)`?\b"),
    "import": re.compile(r"\b(?:import|require\(|from\s+\w+\s+import|use\s+\w+::)|\b[a-z_][\w-]*\(\)"),
    "command": re.compile(r"\b(?:git|npm|yarn|pnpm|pip|poetry|uv|cargo|go|make|docker|pytest|ruff"
                          r"|eslint|prettier|black|mypy|tox|gradle|mvn|bazel|terraform|kubectl)\b"),
    "threshold": re.compile(r"\b\d+\s*(?:ms|s|sec|seconds|minutes|hours|MB|GB|KB|lines?|tokens?|%)\b", re.I),
    "role": re.compile(r"maintainer|owner|@[\w-]+|维护者|负责人", re.I),
}
CHECKABLE = ("path", "file", "import", "command", "threshold")


def classify(line: str) -> str:
    for name in CHECKABLE + ("role",):
        if TIERS[name].search(line):
            return name
    return "pure_prohibition"


def main() -> None:
    df = pd.read_parquet(PARQUET)
    df = df[df["is_substantive"] & ~df["is_pointer"]].copy()
    df["key"] = df["repo_full_name"].str.replace("/", "__", regex=False)
    keys = set(df["key"])
    lines = []
    for p in sorted(RAW.glob("*.md")):
        if p.stem not in keys:
            continue
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip().lstrip("#-*> ").strip()
            if len(s) < 8 or not BOUNDARY_CUE.search(s):
                continue
            lines.append({"repo": p.stem, "text": s, "tier": classify(s)})
    r = pd.DataFrame(lines)
    n = len(r)
    print(f"边界句总数 {n}（{r['repo'].nunique()} 份文件，分母 {len(keys)} 份实质非 pointer）")
    for t in CHECKABLE + ("role", "pure_prohibition"):
        c = int((r["tier"] == t).sum())
        print(f"  {t:<16}{c:>6}  {c/n*100:5.1f}%")
    narrow = ("file", "import", "command", "threshold")
    nb = int(r["tier"].isin(narrow).sum())
    checkable = int(r["tier"].isin(CHECKABLE).sum())
    print(f"窄口径（文件/import/命令/阈值）{nb} = {nb/n*100:.1f}%"
          f" | 宽口径（含路径）{checkable} = {checkable/n*100:.1f}%"
          f" | 纯泛泛陈述 {n-checkable} = {(n-checkable)/n*100:.1f}%")
    per = r.groupby("repo")["tier"].apply(lambda s: set(s))
    allfiles = len(keys)
    has_check = sum(1 for v in per if v & set(CHECKABLE))
    has_narrow = sum(1 for v in per if v & set(narrow))
    only_proh = sum(1 for v in per if v == {"pure_prohibition"})
    print(f"文件级：含≥1条窄口径可检查边界 {has_narrow}/{allfiles} ({has_narrow/allfiles*100:.1f}%)")
    print(f"文件级：含≥1条可检查边界 {has_check}/{allfiles} ({has_check/allfiles*100:.1f}%)"
          f"；只有泛泛禁令 {only_proh}/{allfiles} ({only_proh/allfiles*100:.1f}%)"
          f"；有边界句的文件 {len(per)}/{allfiles}")
    for t in CHECKABLE + ("pure_prohibition",):
        sub = r[r["tier"] == t]
        if sub.empty:
            continue
        print(f"\n--- {t} 例（{len(sub)}）")
        for _, row in sub.head(3).iterrows():
            print(f"  [{row['repo'][:24]:<24}] {row['text'][:100]}")


if __name__ == "__main__":
    main()
