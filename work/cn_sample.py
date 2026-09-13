#!/usr/bin/env python3
"""v0.6 中文留出集：抽样 + 盲判题面（只看原文、不给规则输出）。

用法: .venv/bin/python work/cn_sample.py [--n 50] [--seed 20260913]
输入: data/raw/cn_manifest.jsonl（work/fetch_cn.py 产出）
输出: work/audit/v0.6-cn-sample.json     抽样记录（可复现）
      work/audit/v0.6-cn-worksheet.md    盲判题面（只给仓库名与本地路径）

框（frame）与选择偏差，务必随数字一起引用：
  「用 15 个中文关键词在 GitHub code search 里检索 `filename:AGENTS.md` 命中的仓库，
   其 HEAD 上的 AGENTS.md 且 doc_language=zh」。
  这个框**偏向中文**（1046 份里 1016 份判 zh = 97%），不能读成"GitHub 上的中文比例"。
  好处是它**与 v0.5 语料库零重叠**（v0.5 那批仓库已排除），所以这些文件从未参与过
  任何规则改动——这正是留出集要的。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_charters.taxonomy import CATEGORIES  # noqa: E402

# 与 work/audit_sample.py 同表（中文名是给判读者看的，不属于包里的分类规则）
CAT_ZH = {"overview": "概览", "structure": "架构", "build_test": "构建测试", "style": "风格",
          "workflow": "流程", "environment": "环境", "boundaries": "禁令",
          "gotchas": "坑", "agent_meta": "AI 行为"}

MANIFEST = ROOT / "data" / "raw" / "cn_manifest.jsonl"
CN_DIR = ROOT / "data" / "raw" / "cn"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260913)
    a = ap.parse_args()

    rows = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    frame = [r for r in rows if r["doc_language"] == "zh"]
    rng = random.Random(a.seed)
    picked = sorted(rng.sample(frame, min(a.n, len(frame))), key=lambda r: r["repo_full_name"])

    rec = {
        "seed": a.seed,
        "version": "v0.6-cn",
        "frame": "GitHub code search(filename:AGENTS.md + 15 个中文关键词) 的 HEAD:AGENTS.md"
                 " 且 doc_language=zh；与 v0.5 语料库零重叠",
        "fetched": len(rows),
        "pool_zh": len(frame),
        "main": [r["repo_full_name"] for r in picked],
        "rows": picked,
    }
    out = ROOT / "work/audit/v0.6-cn-sample.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

    L = [f"# v0.6 中文留出集 · 盲判题面（{len(picked)} 份）", "",
         "**只做一件事**：打开每份文件，列出它**实际有什么**（下面 9 类里选，可多选）。",
         "判的时候**不要**看任何规则输出、不要跑 `agent-charters`——这是留出集，先判后比。",
         "",
         f"抽样：seed `{a.seed}`，从 `doc_language=zh` 的 **{len(frame)}** 份里随机抽 {len(picked)}；",
         "框与选择偏差见 `work/cn_sample.py` 顶部注释。", "",
         "| 类别 | 中文 | 含义 |", "|---|---|---|"]
    for c in CATEGORIES:
        L.append(f"| `{c}` | {CAT_ZH.get(c, '')} | |")
    L += ["", "---", ""]
    for i, r in enumerate(picked, 1):
        p = CN_DIR / (r["repo_full_name"].replace("/", "__") + ".md")
        L += [f"## {i}. `{r['repo_full_name']}`", "",
              f"- 本地：`{p}`",
              f"- 字节：{r['bytes']}｜star：{r['repo_stars']}｜fork：{r['is_fork']}", "",
              "```", "call: []", "borderline: []", "why: ", "```", ""]

    ws = ROOT / "work/audit/v0.6-cn-worksheet.md"
    ws.write_text("\n".join(L), encoding="utf-8")
    print(f"框内 zh {len(frame)} 份 → 抽 {len(picked)} 份")
    print(f"写入 {out}\n写入 {ws}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
