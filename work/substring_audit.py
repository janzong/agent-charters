#!/usr/bin/env python
"""子串误命中的语料库级影响评估（只读，不改数据）。

背景：taxonomy 的标题通道是 `keyword in heading.lower()` 的**子串**匹配，
所以 "ci" 会命中 De**ci**sions / Prin**ci**ples，"script" 会命中 Type**Script**，
"build" 会命中 allow**Build**s。这些命中与词义无关。

本脚本按"命中是否落在词首"重算一遍标题通道，统计：
  - 有多少个 (文件, 类别) 组合**只**靠这种误命中撑着（= 该标签应被拿掉的候选）
  - 其中有多少**实际掉了标签**（其余靠正文/强模式通道兜住，标签仍在，只是证据变干净）

⚠️ 必须对**出错的那一版快照**跑，不能对修好后的当前数据跑——所以默认读 v0.2 数据集。
   用法: .venv/bin/python work/substring_audit.py [--dataset data/processed/agent-charters-v0.2.parquet]
输出：work/audit/substring-impact.md
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent_charters.extract import load_corpus, split_sections, substantive  # noqa: E402
from agent_charters.taxonomy import CATEGORIES, HEAD_RULES, STRONG_PATTERNS  # noqa: E402
from agent_charters.taxonomy import classify, classify_fulltext  # noqa: E402

CAT_ZH = {"overview": "概览", "structure": "架构", "build_test": "构建测试", "style": "风格",
          "workflow": "流程", "environment": "环境", "boundaries": "禁令", "gotchas": "坑",
          "agent_meta": "AI行为"}


def clean(low: str, kw: str) -> bool:
    if " " in kw or not kw.isascii():
        return True
    for m in re.finditer(re.escape(kw), low):
        if m.start() == 0 or not low[m.start() - 1].isalpha():
            return True
    return False


def main() -> int:
    import argparse

    import pandas as pd

    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/processed/agent-charters-v0.2.parquet",
                    help="被审计的那一版数据集（默认 v0.2＝出错的那版）")
    ap.add_argument("--fixed", default="data/processed/agent-charters-v0.3.parquet",
                    help="修好后的数据集，用来核对哪些标签实际掉了")
    args = ap.parse_args()

    df = substantive(pd.read_parquet(args.dataset))
    fixed = {r["repo_full_name"]: set(r["categories"])
             for _, r in substantive(pd.read_parquet(args.fixed)).iterrows()}
    dirty_only: list[tuple[str, str, str]] = []
    weak_only: list[tuple[str, str]] = []
    dirty_files: set[str] = set()
    weak_files: set[str] = set()
    per_cat = collections.Counter()
    for _, r in df.iterrows():
        text = pathlib.Path("data/raw/full", r["repo_full_name"].replace("/", "__") + ".md").read_text(
            encoding="utf-8", errors="replace")
        good: dict[str, list[str]] = collections.defaultdict(list)
        bad: dict[str, list[str]] = collections.defaultdict(list)
        for head, body in split_sections(text):
            if not head.strip() and len(body.strip()) < 40:
                continue
            low = head.lower()
            for cat, keys in HEAD_RULES.items():
                for k in keys:
                    if k in low:
                        (good if clean(low, k) else bad)[cat].append(f"{k}@{head.strip()[:40]}")
                        break
            _, detail = classify(head, body)
            for c, terms in detail.items():
                for t in terms:
                    if not t.startswith("heading:"):
                        good[c].append(t)
        ft = classify_fulltext(text)[0]
        for cat in r["categories"]:
            if cat in good:
                continue
            if bad.get(cat):
                # 子串误命中：标签所依据的标题命中落在词中，与词义无关
                dirty_only.append((r["repo_full_name"], cat, bad[cat][0]))
                dirty_files.add(r["repo_full_name"])
                per_cat[cat] += 1
            elif cat not in ft and not any(re.search(p, text, re.I) for p in STRONG_PATTERNS.get(cat, [])):
                # 兜底通道（全文规则/强模式）：证据弱，但不是子串问题，单独计
                weak_only.append((r["repo_full_name"], cat))
                weak_files.add(r["repo_full_name"])

    lost = sorted({(repo, cat) for repo, cat, _ in dirty_only
                   if repo in fixed and cat not in fixed[repo]})
    out = ["# 子串误命中的语料库级影响（只读评估）\n",
           f"- 被审计数据集：`{args.dataset}`（出错的那版）；对照修复版：`{args.fixed}`",
           f"- 实质文件：{len(df)}",
           f"- **子串误命中**：{len(dirty_only)} 处 (文件, 类别) 组合，涉及 {len(dirty_files)} 份文件",
           f"- 其中**实际掉标签**：{len(lost)} 处（其余靠正文/强模式通道兜住，标签仍在，只是证据变干净）",
           f"- **仅兜底通道**（全文规则/强模式，证据弱但不是子串问题）：{len(weak_only)} 处，涉及 {len(weak_files)} 份文件\n",
           "## 子串误命中按类别\n"]
    for c, n in per_cat.most_common():
        out.append(f"- {CAT_ZH[c]}：{n} 份")
    out.append("\n## 子串误命中明细（文件 :: 类别 :: 误命中词@标题 :: 是否掉标签）\n")
    lost_set = set(lost)
    for repo, cat, ev in dirty_only:
        mark = "**掉**" if (repo, cat) in lost_set else "保留（另有正文/强模式证据）"
        out.append(f"- {repo} :: {CAT_ZH[cat]} ← {ev} :: {mark}")
    out.append("\n## 仅兜底通道明细（不计入子串问题）\n")
    for repo, cat in weak_only:
        out.append(f"- {repo} :: {CAT_ZH[cat]}")
    p = pathlib.Path("work/audit/substring-impact.md")
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {p}; 受影子串标签 {len(dirty_only)} 处 / 文件 {len(dirty_files)}；实际掉标签 {len(lost)} 处")
    print(dict(per_cat))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
