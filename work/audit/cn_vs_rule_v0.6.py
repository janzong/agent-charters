#!/usr/bin/env python3
"""v0.6 中文留出集：盲判 × 规则，逐类对照。

用法: .venv/bin/python work/audit/cn_vs_rule_v0.6.py
输入: work/audit/v0.6-cn-calls-a*.json（盲判，可分批追加）+ data/raw/cn_manifest.jsonl
输出: work/audit/v0.6-cn-vs-rule.md

设计要点：
- **允许部分判完**（首批只判 3/50 也要能跑）——输出里显式写覆盖度，避免把"判了 3 份"
  读成"中文留出集结论"。
- 两种口径都算（与 §20 的自披露一致）：现行实现把「犹豫」计入错标，文档口径把它出局。
- 盲判文件按 repo 认身份（中文这批不与 v0.5 语料库重叠，无 sha 复用问题）。
"""
from __future__ import annotations

import collections
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent_charters.extract import analyze_text  # noqa: E402
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

CN_DIR = ROOT / "data/raw/cn"
OUT = ROOT / "work/audit/v0.6-cn-vs-rule.md"


def main() -> int:
    sample = json.loads((ROOT / "work/audit/v0.6-cn-sample.json").read_text(encoding="utf-8"))
    planned = sample["main"]
    calls: dict[str, dict] = {}
    for p in sorted(glob.glob(str(ROOT / "work/audit/v0.6-cn-calls-a*.json"))):
        for repo, v in json.loads(pathlib.Path(p).read_text(encoding="utf-8"))["files"].items():
            calls[repo] = v
    unknown = sorted(set(calls) - set(planned))
    if unknown:
        raise SystemExit(f"盲判里有不在抽样里的仓库：{unknown[:3]}")

    tp = collections.Counter(); fp = collections.Counter(); fn = collections.Counter()
    bl_hit = collections.Counter(); bl_miss = collections.Counter(); bl_fp = collections.Counter()
    exact = 0; det = []
    for repo in planned:
        c = calls.get(repo)
        if c is None:
            continue
        text = (CN_DIR / (repo.replace("/", "__") + ".md")).read_text(encoding="utf-8",
                                                                     errors="replace")
        rule = set(analyze_text(text)["categories"])
        h, bl = set(c["call"]), set(c.get("borderline", []))
        if h == rule:
            exact += 1
        for x in rule - h: fp[x] += 1
        for x in h - rule: fn[x] += 1
        for x in h & rule: tp[x] += 1
        for x in bl:
            (bl_hit if x in rule else bl_miss)[x] += 1
            if x in rule and x not in h: bl_fp[x] += 1
        if h != rule:
            det.append((repo, sorted(h - rule), sorted(rule - h), sorted(bl & rule)))

    n = len(calls)
    TP, FP, FN = sum(tp.values()), sum(fp.values()), sum(fn.values())
    # 文档口径：犹豫且规则命中 → 出局
    TP2 = TP + sum(bl_fp.values()); FP2 = FP - sum(bl_fp.values()); FN2 = FN
    L = ["# v0.6 中文留出集：盲判 × 规则（逐类对照）", "",
         f"- 生成：2026-09-13｜规则 `ruleset_v0.1.8`｜**覆盖度 {n}/{len(planned)} 份**"
         f"{'（⚠️ 未判完，下表只代表已判部分）' if n < len(planned) else ''}",
         f"- 框：GitHub code search（`filename:AGENTS.md` + 15 个中文关键词）命中的仓库，"
         f"其 `HEAD:AGENTS.md` 且 `doc_language=zh`；与 v0.5 语料库零重叠。"
         f"框内 zh 共 **{sample['pool_zh']}** 份，随机抽 {len(planned)}（seed `{sample['seed']}`）。",
         "- ⚠️ **框偏向中文**（1046 份抓取里 1016 份判 zh＝97%）：不要把这个比例读成"
         "GitHub 的真实语言分布，它是检索方式带来的。",
         "- 口径：两种都给——**现行实现**把「犹豫」计入错标（保守）；**文档口径**（§20 指出"
         "与实现不符的那条）把犹豫出局。", "",
         f"- 文件级完全一致：**{exact}/{n}**", ""]

    L += ["| 类别 | 人判 | 规则判 | 一致 | 漏标 | 错标 | precision | recall | 犹豫(有/无) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in CATEGORIES:
        h = tp[c] + fn[c]; rr = tp[c] + fp[c]
        p = f"{tp[c] / rr:.0%}" if rr else "—"
        rec = f"{tp[c] / h:.0%}" if h else "—"
        L.append(f"| `{c}` | {h} | {rr} | {tp[c]} | {fn[c]} | {fp[c]} | {p} | {rec} |"
                 f" {bl_hit[c]}/{bl_miss[c]} |")
    L += ["",
          f"**微平均（现行口径）**：precision **{TP / (TP + FP):.0%}** / recall "
          f"**{TP / (TP + FN):.0%}**（TP {TP} / FP {FP} / FN {FN}）",
          f"**微平均（文档口径，犹豫出局）**：precision **{TP2 / (TP2 + FP2):.0%}** / recall "
          f"**{TP2 / (TP2 + FN2):.0%}**（TP {TP2} / FP {FP2} / FN {FN2}）", ""]

    if det:
        L += ["## 逐份分歧（人−规则 = 漏标；规则−人 = 错标）", ""]
        for repo, miss, wrong, blr in det:
            L.append(f"- `{repo}`：漏 {miss or '—'}｜错 {wrong or '—'}"
                     f"{f'｜犹豫命中 {blr}' if blr else ''}")
        L.append("")
    if n < len(planned):
        todo = [r for r in planned if r not in calls]
        used = sorted(p.name for p in (ROOT / "work/audit").glob("v0.6-cn-calls-a*.json"))
        nxt = f"a{len(used) + 1}"
        L += ["## 尚未判读（续判用）", "",
              f"还差 **{len(todo)}** 份：" + "、".join(f"`{r}`" for r in todo[:12])
              + ("…" if len(todo) > 12 else ""), "",
              f"续判：按 `work/audit/v0.6-cn-worksheet.md` 顺序读原文（**先别跑规则**），"
              f"新建 `work/audit/v0.6-cn-calls-{nxt}.json`（格式同 "
              f"`{used[0] if used else 'a1'}`），重跑本脚本即可刷新本表。", ""]

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"覆盖 {n}/{len(planned)} 份 → {OUT}")
    if n:
        print(f"现行口径 precision {TP/(TP+FP):.0%} / recall {TP/(TP+FN):.0%}；"
              f"文档口径 {TP2/(TP2+FP2):.0%} / {TP2/(TP2+FN2):.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
