#!/usr/bin/env python
"""两个数据集版本的差异报告（只读）。

用法:
  .venv/bin/python work/dataset_diff.py --old data/processed/agent-charters-v0.2.parquet \
      --new data/processed/agent-charters-v0.3.parquet --out work/v0.2-to-v0.3-diff.md

口径与 `agent_charters.extract.substantive()` 一致（实质且非转引用），
所以这里的百分比可以直接与 README / FINDINGS / 对外文案对齐。
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent_charters.extract import substantive  # noqa: E402
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

ZH = {"overview": "概览", "structure": "架构", "build_test": "构建测试", "style": "风格",
      "workflow": "流程", "environment": "环境", "boundaries": "禁令", "gotchas": "坑",
      "agent_meta": "AI行为"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="data/processed/agent-charters-v0.2.parquet")
    ap.add_argument("--new", default="data/processed/agent-charters-v0.3.parquet")
    ap.add_argument("--out", default="work/dataset-diff.md")
    a = ap.parse_args()

    old_df, new_df = pd.read_parquet(a.old), pd.read_parquet(a.new)
    old, new = substantive(old_df), substantive(new_df)
    det = {
        "old": {c: sum(1 for t in old["categories"] if c in t) for c in CATEGORIES},
        "new": {c: sum(1 for t in new["categories"] if c in t) for c in CATEGORIES},
    }
    it = {
        "old": {c: int(old["category_counts"].apply(lambda x: x.get(c, 0)).sum()) for c in CATEGORIES},
        "new": {c: int(new["category_counts"].apply(lambda x: x.get(c, 0)).sum()) for c in CATEGORIES},
    }

    old_map = {r["repo_full_name"]: r for _, r in old.iterrows()}
    changed = []
    for _, r in new.iterrows():
        o = old_map.get(r["repo_full_name"])
        if o is None:
            continue
        lost = sorted(set(o["categories"]) - set(r["categories"]))
        gained = sorted(set(r["categories"]) - set(o["categories"]))
        if lost or gained:
            changed.append((r["repo_full_name"], lost, gained))

    n_old, n_new = len(old), len(new)
    out = [f"# 数据集差异：`{pathlib.Path(a.old).name}` → `{pathlib.Path(a.new).name}`", "",
           f"- 规则集：`{old_df['ruleset_version'].iloc[0]}` → `{new_df['ruleset_version'].iloc[0]}`",
           f"- 行数：{len(old_df)} → {len(new_df)}（不变）",
           f"- 可用样本（实质且非转引用）：{n_old} → {n_new}", "",
           "## 九类覆盖率（文件数；百分比以各自可用样本为分母）", "",
           "| 类别 | 旧 | 新 | 差 |", "|---|---|---|---|"]
    for c in CATEGORIES:
        d = det["new"][c] - det["old"][c]
        out.append(f"| {ZH[c]} | {det['old'][c]*100/n_old:.1f}% ({det['old'][c]}) "
                   f"| {det['new'][c]*100/n_new:.1f}% ({det['new'][c]}) | {d:+d} |")
    out += ["", "## 标签次数", "", "| 类别 | 旧 | 新 | 差 |", "|---|---|---|---|"]
    for c in CATEGORIES:
        out.append(f"| {ZH[c]} | {it['old'][c]} | {it['new'][c]} | {it['new'][c]-it['old'][c]:+d} |")
    out += ["", "## content_mode", "", "| 模式 | 旧 | 新 |", "|---|---|---|"]
    for m in ("rule", "knowledge", "mixed"):
        out.append(f"| {m} | {int((old['content_mode']==m).sum())} | {int((new['content_mode']==m).sum())} |")
    out += ["", "## 类别集合变化的文件", "", "| 仓库 | 去掉 | 新增 |", "|---|---|---|"]
    for repo, lost, gained in changed:
        out.append(f"| {repo} | {'、'.join(ZH[c] for c in lost) or '—'} "
                   f"| {'、'.join(ZH[c] for c in gained) or '—'} |")
    n_lost = sum(1 for _, lost, _ in changed if lost)
    n_gain = sum(1 for _, _, g in changed if g)
    out += ["", f"合计 **{len(changed)}** 份文件的类别集合变化（掉标签 {n_lost} 份、新增标签 {n_gain} 份）。", ""]
    p = pathlib.Path(a.out)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {p}; 变化 {len(changed)} 份（掉 {n_lost} / 增 {n_gain}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
