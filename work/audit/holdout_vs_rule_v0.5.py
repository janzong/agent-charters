#!/usr/bin/env python3
"""留出集 55 份盲判 × v0.5 规则（ruleset_v0.1.8）：逐类对照表。

用法: .venv/bin/python work/audit/holdout_vs_rule_v0.5.py [--md 输出路径]

⚠️ 与 human_vs_rule_v0.5.py 的区别：那 100 份**驱动了 v0.5 的规则改动**（in-sample，
数字是上界）；本脚本用的 55 份是**留出集**——先按 identity 排除上一轮用过的 106 份，
再随机抽 55 份，盲判时只看原文、不看规则输出。所以这里的 precision/recall 才是
对未见数据的估计。

盲判文件：work/audit/v0.5-holdout-calls-a1..a7.json
抽样记录：work/audit/v0.5-holdout-sample.json（seed 20260913）
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent_charters.extract import analyze_text  # noqa: E402
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

RAW = ROOT / "data" / "raw" / "full"
SAMPLES = ["v0.5-holdout-calls-a1.json", "v0.5-holdout-calls-a2.json",
           "v0.5-holdout-calls-a3.json", "v0.5-holdout-calls-a4.json",
           "v0.5-holdout-calls-a5.json", "v0.5-holdout-calls-a6.json",
           "v0.5-holdout-calls-a7.json"]


def load_rows() -> dict[str, dict]:
    rows = {}
    for line in (ROOT / "data/processed/agent_charters_v0.5.jsonl").read_text(
            encoding="utf-8").splitlines():
        r = json.loads(line)
        rows[r["repo_full_name"]] = r
    return rows


def load_calls(rows: dict[str, dict]) -> dict[str, dict]:
    """{sha: {call, borderline, why, src}}；键按 repo_full_name 对回 sha。"""
    out: dict[str, dict] = {}
    for name in SAMPLES:
        p = ROOT / "work/audit" / name
        d = json.loads(p.read_text(encoding="utf-8"))
        for repo, v in d["files"].items():
            row = rows.get(repo)
            if row is None:
                raise SystemExit(f"盲判里的 repo 不在数据集里：{repo}（{name}）")
            out[row["file_sha"]] = {
                "call": set(v["call"]),
                "borderline": set(v.get("borderline", [])),
                "why": v.get("why", ""),
                "repo": repo,
                "src": name,
            }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(ROOT / "work/audit/v0.5-holdout-vs-rule.md"))
    a = ap.parse_args()

    rows = load_rows()
    calls = load_calls(rows)
    sample = json.loads((ROOT / "work/audit/v0.5-holdout-sample.json").read_text(encoding="utf-8"))
    # 可用池 = 可用样本（is_substantive）减去上一轮已用过的 identity（按 repo+file_path）
    ex_pairs = {(it["repo"], it["file_path"])
                for items in (json.loads((ROOT / "work/audit/v0.4-sample.json").read_text(
                    encoding="utf-8")).get("identity") or {}).values() for it in items}
    pool = {r["file_sha"] for r in rows.values()
            if r.get("is_substantive") and (r["repo_full_name"], r["file_path"]) not in ex_pairs}
    planned = set(sample["main"])
    missing = planned - set(calls)
    extra = set(calls) - planned
    if missing or extra:
        raise SystemExit(f"盲判与抽样不符：缺 {len(missing)} 份 {sorted(missing)[:3]}；多 {len(extra)}")

    n = len(calls)
    tp = collections.Counter(); fp = collections.Counter(); fn = collections.Counter()
    bl_hit = collections.Counter(); bl_miss = collections.Counter()
    exact = 0; bl_total = 0
    bl_fp = collections.Counter()
    det = []
    for sha, c in calls.items():
        repo = c["repo"]
        text = (RAW / f"{repo.replace('/', '__')}.md").read_text(encoding="utf-8", errors="replace")
        rule = set(analyze_text(text)["categories"])
        h = c["call"]; bl = c["borderline"]
        bl_total += len(bl)
        if h == rule:
            exact += 1
        for x in rule - h: fp[x] += 1
        for x in h - rule: fn[x] += 1
        for x in h & rule: tp[x] += 1
        for x in bl:
            (bl_hit if x in rule else bl_miss)[x] += 1
            if x in rule and x not in h:
                # 「犹豫」且规则命中、人判也不算 ⇒ **文档口径**下这条不算错标（§20 第 2 件）
                bl_fp[x] += 1
        if h != rule:
            det.append((repo, sorted(h - rule), sorted(rule - h),
                        sorted(bl & rule)))

    today = __import__("datetime").date.today()
    L = ["# 留出集 55 份盲判 × v0.5 规则：逐类对照", "",
         f"- 生成：{today}｜规则 `ruleset_v0.1.8`｜数据 v0.5｜抽样 seed `{sample['seed']}`",
         f"- 样本：**{n} 份**（从可用池 **{len(pool)}** 份中随机抽；先按 `repo+file_path` 排除上一轮已用的 {len(ex_pairs)} 份）",
         "- ✅ **本表是留出集估计**：这 55 份**没有**参与 v0.5 规则改动；盲判时只读原文、未看规则输出。",
         "- 口径（两种都给，与 `cn_vs_rule_v0.6.py` 同款算法）：**现行实现**把「犹豫」计入错标",
         "  （更保守，也是对外引用的那个数）；**文档口径**把「犹豫且规则命中」的出局。",
         "  两口径差的只有下面「犹豫」那一列的命中数，逐类数字同源。", ""]

    L += [f"## 总览（{n} 份）", "",
          f"- 文件级完全一致：**{exact}/{n} = {round(exact * 100 / n, 1)}%**",
          f"- 漏标（人判有、规则没有）：**{sum(fn.values())}** 处",
          f"- 错标（规则有、人判没有）：**{sum(fp.values())}** 处",
          f"- 盲判标「犹豫」的类次数：{bl_total}（其中规则也判有 {sum(bl_hit.values())} / 规则没判 {sum(bl_miss.values())}）", "",
          "| 类别 | 人判 | 规则判 | 一致 | 漏标 | 错标 | precision | recall | 犹豫(规则有/无) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in CATEGORIES:
        h = tp[c] + fn[c]; rr = tp[c] + fp[c]
        p = f"{tp[c] / rr:.0%}" if rr else "—"
        rec = f"{tp[c] / h:.0%}" if h else "—"
        L.append(f"| `{c}` | {h} | {rr} | {tp[c]} | {fn[c]} | {fp[c]} | {p} | {rec} |"
                 f" {bl_hit[c]}/{bl_miss[c]} |")
    TP, FP, FN = sum(tp.values()), sum(fp.values()), sum(fn.values())
    mp = f"{TP / (TP + FP):.0%}" if TP + FP else "—"
    mr = f"{TP / (TP + FN):.0%}" if TP + FN else "—"
    # 文档口径：犹豫且规则命中 → 出局（§20 记的那条；cn_vs_rule_v0.6.py 同款算法）
    TP2 = TP + sum(bl_fp.values()); FP2 = FP - sum(bl_fp.values()); FN2 = FN
    mp2 = f"{TP2 / (TP2 + FP2):.0%}" if TP2 + FP2 else "—"
    mr2 = f"{TP2 / (TP2 + FN2):.0%}" if TP2 + FN2 else "—"
    L += ["",
          f"**微平均（现行口径，犹豫计入错标）**：precision **{mp}**｜recall **{mr}**"
          f"（TP {TP} / FP {FP} / FN {FN}）",
          f"**微平均（文档口径，犹豫出局）**：precision **{mp2}**｜recall **{mr2}**"
          f"（TP {TP2} / FP {FP2} / FN {FN2}）", ""]

    if det:
        L += ["## 逐份分歧（人−规则 = 漏标；规则−人 = 错标）", ""]
        for repo, miss, extra, blh in det:
            bl = f"｜犹豫命中 {blh}" if blh else ""
            L.append(f"- `{repo}`：漏 {miss or '—'}｜错 {extra or '—'}{bl}")
        L.append("")

    L += ["## 与 in-sample 对照（这批留出集是否被「教过」）", "",
          "同一批规则、同一个标注者（本智能体），只换样本：",
          "",
          "| 指标 | in-sample A 组 55 份（§16） | **留出集 55 份（本表）** |",
          "|---|---|---|",
          "| 微平均 precision | 90% | **92%** |",
          "| 微平均 recall | 75% | **70%** |",
          "| 漏标 / 错标 | 79 / 25 | **93 / 19** |",
          "| 文件级完全一致 | 7/55 (12.7%) | **7/55 (12.7%)** |",
          "",
          "**结论：v0.5 的规则改动没有明显过拟合。** 留出集与 in-sample 只差 3–5pp",
          "（recall 略降、precision 略升），方向一致；in-sample 数字**没有**被显著高估。",
          "逐类看，留出集上 `build_test`（95%）、`style`（79%）比 in-sample 好，",
          "`environment`（57% vs 77%）和 `boundaries`（88% vs 98%）明显更差——",
          "后两类值得在下一轮单独看分歧清单，而不是假设它们已经解决。", "",
          "## 怎么读", "",
          "- **留出集数字才是对外可引用的**；`v0.5-human-vs-rule.md`（100 份，in-sample）",
          "  只能当「改完还剩多少分歧」。",
          "- 「犹豫」怎么算：**主口径（现行实现）把它算成错标**，所以引用的 92% / 70% 是两种算法里",
          "  **更保守**的那个；按「犹豫出局」复算是 97% / 71%。两条都列在上面，别只引一条。",
          "- 局限：**单一标注者**（本智能体），没有第二人独立复判；且留出集**没有中文、没有指针文件**（见 §18）。",
          "- 复算：`.venv/bin/python work/audit/holdout_vs_rule_v0.5.py`；",
          "  盲判原文 `work/audit/v0.5-holdout-calls-a*.json`、抽样 `work/audit/v0.5-holdout-sample.json`。"]
    Path(a.md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n写入 {a.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
