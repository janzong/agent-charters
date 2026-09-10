"""章程修订史试点的分析（配合 work/charter_history.py 的抓取缓存）。

用法: .venv/bin/python work/charter_history_report.py
输入: data/raw/charter_history.jsonl（抓取缓存，未入库）+ data/raw/full_manifest.jsonl
输出: data/processed/charter-history-pilot-2026-09-11.tsv（指纹表，入库）
"""
import json
import re
import statistics as st
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

CACHE = Path("data/raw/charter_history.jsonl")
MANIFEST = Path("data/raw/full_manifest.jsonl")
OUT = Path("data/processed/charter-history-pilot-2026-09-11.tsv")

CLASSES = [
    ("init", r"(?i)^(add AGENTS\.md|initial|chore: init|create AGENTS)"),
    ("format", r"(?i)\b(format|prettier|lint|typo|整理|slim|consolidate|simplify|rename|reorganiz)"),
    ("correct", r"(?i)\b(stale|correct|outdated|broken link|修正)"),
    ("add_rule", r"(?i)\b(add (?:a )?(?:section|rule|note)|clarify|require|disallow|禁止|规则|policy)"),
    ("rides_code", r"(?i)^(feat|fix|refactor|chore|perf|build|ci)(\(|:)"),
]


def classify(msg: str) -> str:
    for name, rx in CLASSES:
        if re.search(rx, msg):
            return name
    return "other"


def main() -> None:
    recs = [json.loads(l) for l in CACHE.read_text().splitlines()]
    man = {json.loads(l)["repo_full_name"]: json.loads(l)
           for l in MANIFEST.read_text().splitlines()}

    rows = []
    for r in recs:
        m = man.get(r["repo"], {})
        revs = r.get("revisions", [])
        rows.append({
            "repo": r["repo"], "stars": m.get("repo_stars"),
            "n_revisions": r.get("n_revisions"),
            "first_rev": revs[-1]["date"] if revs else "",
            "last_rev": revs[0]["date"] if revs else "",
            "repo_pushed": (m.get("repo_pushed_at") or "")[:10],
            "changelog_revisions": r.get("changelog_revisions"),
        })
    df = pd.DataFrame(rows)
    df = df[df["last_rev"] != ""].copy()
    df["lag_days"] = [
        (date.fromisoformat(p) - date.fromisoformat(l)).days
        for p, l in zip(df["repo_pushed"], df["last_rev"])]
    df.sort_values("stars", ascending=False).to_csv(OUT, sep="\t", index=False)

    revs = [(r["repo"], v) for r in recs for v in r.get("revisions", [])]
    print(f"仓库 {len(df)} 个 / 修订 {len(revs)} 条 → {OUT}\n")

    print("=== F2：章程最后修订 落后 仓库最后推送")
    print(f"  中位 {df['lag_days'].median():.0f} 天｜最大 {df['lag_days'].max()}｜最小 {df['lag_days'].min()}")
    print(f"  落后 >30 天: {int((df['lag_days'] > 30).sum())} / {len(df)}")
    print(f"  落后 ≤7 天:  {int((df['lag_days'] <= 7).sum())} / {len(df)}")

    print("\n=== F1：修订提交信息类型（口径粗糙，仅作筛选用）")
    c = Counter(classify(v["message"]) for _, v in revs)
    for k, v in c.most_common():
        print(f"  {k:<12}{v:>5}  {v/len(revs)*100:>4.0f}%")
    print(f"  同一次提交也改了非文档文件: "
          f"{sum(1 for _, v in revs if v['code_touched'])} / {len(revs)}"
          "   ← monorepo 混淆，不能当'事故驱动'的证据")


if __name__ == "__main__":
    main()
