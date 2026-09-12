#!/usr/bin/env python3
"""100 份人工核对 × v0.5 规则：逐类对照表。

用法: .venv/bin/python work/audit/human_vs_rule_v0.5.py [--md 输出路径]

⚠️ 口径：这 100 份**就是驱动 v0.5 规则改动的那批样本**，所以算出来的是一致率的
**上界（in-sample）**，不是留出集估计。它回答的问题是"改完之后还剩多少分歧"，
不是"规则在未见数据上有多准"。逐类分歧清单比汇总数字更有用。

分组：A 主样本 55（唯一能代表全体）/ B 中文普查 26 / C 边界件 10 / D 稀有类加成 9。
B/C/D 是配额样本，**只报分组，不并入整体**。
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


def load_rows() -> dict[str, dict]:
    rows = {}
    for line in (ROOT / "data/processed/agent_charters_v0.5.jsonl").read_text(
            encoding="utf-8").splitlines():
        r = json.loads(line)
        rows[r["file_sha"]] = r
    return rows


def load_labels() -> dict[str, dict]:
    """把 agent 的盲判文件与用户在审计工作台上的判定合并成 {sha: {...}}。

    只读、只做结构化解析——不做任何人工判读。
    """
    shas = {r["repo_full_name"]: r for r in load_rows().values()}
    out: dict[str, dict] = {}
    for path in sorted(glob.glob(str(ROOT / "work/audit/v0.4-blind-*.json"))):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        items = {}
        if isinstance(d.get("files"), dict):
            for k, v in d["files"].items():
                if "call" in v:
                    items[k] = (v["call"], v.get("borderline", []))
                elif "cats" in v:
                    items[k] = ([c for c, x in v["cats"].items() if x != 0],
                                [c for c, x in v["cats"].items() if x == 2])
        for k, v in d.items():
            if not k.startswith("_") and isinstance(v, dict) and "call" in v:
                items[k] = (v["call"], v.get("borderline", []))
        for k, (cats, bl) in items.items():
            repo, _, fp = k.partition("|")
            row = shas.get(repo)
            if row is None:
                continue
            if fp and row["file_path"] != fp:
                continue
            sha = row["file_sha"]
            prev = out.get(sha)
            if prev:
                prev["cats"] |= set(cats)
                prev["borderline"] |= set(bl)
                prev["src"].append(Path(path).name)
            else:
                out[sha] = {"cats": set(cats), "borderline": set(bl),
                            "src": [Path(path).name]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(ROOT / "work/audit/v0.5-human-vs-rule.md"))
    a = ap.parse_args()

    rows = load_rows()
    labels = load_labels()
    plan = json.loads((ROOT / "work/audit/v0.4-sample.json").read_text(encoding="utf-8"))
    groups = {"A-main": plan["main"][:], "B-zh": plan["zh_census"][:],
              "C-edge": plan["edge"][:], "D-rare": plan["rare_boost"][:]}

    rule_cache: dict[str, set[str]] = {}
    for sha in labels:
        text = (RAW / f"{rows[sha]['repo_full_name'].replace('/', '__')}.md").read_text(
            encoding="utf-8", errors="replace")
        rule_cache[sha] = set(analyze_text(text)["categories"])

    L = ["# 100 份人工核对 × v0.5 规则：逐类对照", "",
         f"- 生成：{__import__('datetime').date.today()}｜规则 `ruleset_v0.1.8`｜数据 v0.5",
         f"- 已标注样本 **{len(labels)} 份**（计划 100，其中 4 份是 9–29B 存根，C 组判定为非实质、不进对照）",
         "- ⚠️ **这是 in-sample 一致率**：这 100 份正是驱动 v0.5 改动的那批样本，",
         "  所以数字是**上界**，不是留出集估计。它回答「改完还剩多少分歧」。",
         "- 口径：**主口径**只算人判确认的类别（agent 的 `call`、用户工作台判 1）；",
         "  人判「犹豫」的类别（`borderline` / 用户判 2）**单列**，不计入漏标/错标，另给宽松口径作对照。", ""]

    summary = {}
    for gname, shas in groups.items():
        uniq = [s for s in dict.fromkeys(shas) if s in labels]
        if not uniq:
            continue
        tp = collections.Counter(); fp = collections.Counter(); fn = collections.Counter()
        exact = 0; bl_total = 0
        rowsdet = []
        bl_hit = collections.Counter(); bl_miss = collections.Counter(); bl_fp = collections.Counter()
        for sha in uniq:
            h = labels[sha]["cats"]; r = rule_cache[sha]
            bl = labels[sha]["borderline"]
            bl_total += len(bl)
            if h == r:
                exact += 1
            for c in r - h: fp[c] += 1
            for c in h - r: fn[c] += 1
            for c in h & r: tp[c] += 1
            for c in bl:
                if c in r: bl_hit[c] += 1
                else: bl_miss[c] += 1
            for c in (bl & r):
                if c not in h: bl_fp[c] += 1
            if h != r:
                rowsdet.append((rows[sha]["repo_full_name"], sorted(h - r), sorted(r - h)))
        n = len(uniq)
        L += [f"## {gname}（{n} 份）", "",
              f"- 文件级完全一致：**{exact}/{n} = {round(exact * 100 / n, 1)}%**",
              f"- 分歧处（人判有、规则漏）：**{sum(fn.values())}**｜（规则有、人判无 → 错标）：**{sum(fp.values())}**",
              f"- 人判标记「犹豫」的类次数：{bl_total}（其中规则也判有 {sum(bl_hit.values())} / 规则没判 {sum(bl_miss.values())}）", "",
              "| 类别 | 人判 | 规则判 | 一致 | 漏标 | 错标 | precision | recall | 犹豫(规则有/无) |",
              "|---|---|---|---|---|---|---|---|---|"]
        for c in CATEGORIES:
            h = tp[c] + fn[c]; rr = tp[c] + fp[c]
            p = f"{tp[c] / rr:.0%}" if rr else "—"
            rec = f"{tp[c] / h:.0%}" if h else "—"
            if h or rr or bl_hit[c] or bl_miss[c]:
                L.append(f"| `{c}` | {h} | {rr} | {tp[c]} | {fn[c]} | {fp[c]} | {p} | {rec} |"
                         f" {bl_hit[c]}/{bl_miss[c]} |")
        if rowsdet:
            L += ["", "**逐份分歧**（人−规则 / 规则−人）：", ""]
            for repo, miss, extra in rowsdet:
                L.append(f"- `{repo}`：漏 {miss or '—'}｜错 {extra or '—'}")
        L.append("")
        TP, FP, FN = sum(tp.values()), sum(fp.values()), sum(fn.values())
        micro_p = TP / (TP + FP) if TP + FP else 0
        micro_r = TP / (TP + FN) if TP + FN else 0
        summary[gname] = (n, exact, FN, FP, micro_p, micro_r,
                          "本智能体" if gname.startswith("A") or gname.startswith("D")
                          else "**用户（第二标注者）**")

    L += ["## 汇总（分组，不合并）", "",
          "| 组 | 份数 | 标注者 | 完全一致 | 漏标 | 错标 | 微平均 precision | 微平均 recall |",
          "|---|---|---|---|---|---|---|---|"]
    for g, (n, e, fn, fp, mp, mr, who) in summary.items():
        L.append(f"| {g} | {n} | {who} | {e} ({round(e * 100 / n)}%) | {fn} | {fp} |"
                 f" **{mp:.0%}** | **{mr:.0%}** |")
    L += ["",
          "## 怎么读这张表", "",
          "- **微平均 precision 80–92%、recall 75–84%**：错标的量级已经压住了，**漏标仍是主要短板**（按类看最弱 38%）。",
          "  这与 v0.1 那轮「准确 9 / 漏标 3 / 错标 0」的结论同向，只是现在有数字了。",
          "- **最弱的四类**：`gotchas`（A 组 recall 38%）、`overview`（41%）、`agent_meta`（A 组 55%、B 组 44%）、",
          "  `environment`（B 组 62%）——前三类都与「散落在正文里、没有专门章节」有关，",
          "  正是标题通道结构性命中的盲区（见 `LIMITATIONS.md` §2）。",
          "- **B 组（用户独立盲判）暴露的错标**：`build_test` precision 仅 **61%**（中文文件里",
          "  「运行/命令/启动」这类动词被当成构建证据）、`gotchas` 67%、`style` 71%——",
          "  中文样本的 precision 明显低于英文，这是**配额样本**结论（n=26），不要外推到全体。",
          "- **A 组与 B 组的分歧模式不同**：A（本智能体判）错标少、漏标多；B（用户判）",
          "  两边都多。同一份规则、不同的判读者，「准确率」就会移动——这就是 `LIMITATIONS.md` §12",
          "  说的「定义边界是人定的」在数字上的体现。",
          "- ⚠️ **in-sample**：这 100 份驱动了 v0.5 的改动，所以以上都是**上界**。",
          "  真正的留出集估计需要新一轮未参与改规则的样本。"]
    Path(a.md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:40]))
    print(f"\n... 完整表格写入 {a.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
