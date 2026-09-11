#!/usr/bin/env python3
"""v0.2 人工核对：抽样并生成"可审核工作表"。

为什么这么抽样（方法上别搞错）：
- 要估计的是**整体准确率/漏标率**，所以主样本必须是**从 511 份里无分层随机抽**——
  按类别分层会让类别频率失真，算出来的不是语料库的真实准确率。
- 中文只有 26 份且是已知弱点，单独抽一组**只报分组结果**，不并入主样本估计。

产物：
- work/audit/v0.2-sample.json     抽样记录（seed + file_sha 列表，保证可复现）
- work/audit/v0.2-worksheet.md    人工核对工作表（每份附：分配类别 + 命中证据 + 原文摘录 + 判定栏）

用法：
  .venv/bin/python work/audit_sample.py --n 30 --zh 10 --seed 20260911
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import re

import pandas as pd

from agent_charters.extract import load_corpus, substantive
from agent_charters.taxonomy import STRONG_PATTERNS, classify, classify_fulltext, split_sections

CATS = ["overview", "structure", "build_test", "style", "workflow",
        "environment", "boundaries", "gotchas", "agent_meta"]
CAT_ZH = {"overview": "概览", "structure": "架构", "build_test": "构建测试", "style": "风格",
          "workflow": "流程", "environment": "环境", "boundaries": "禁令", "gotchas": "坑",
          "agent_meta": "AI行为"}


def evidence_for(text: str, tags: set[str]) -> dict[str, list[str]]:
    """按与抽取器相同的通道，取出每个类别的命中证据（标题 + 命中词）。"""
    ev: dict[str, list[str]] = {c: [] for c in tags}
    for head, body in split_sections(text):
        if not head.strip() and len(body.strip()) < 40:
            continue
        got, detail = classify(head, body)
        for c in got & tags:
            terms = ", ".join(detail.get(c, [])[:4])
            ev[c].append(f"{head or '(无标题段)'} ← {terms}" if terms else (head or "(无标题段)"))
    for c in tags:
        if ev[c]:
            continue
        # 兜底顺序必须与抽取器一致：先全文规则通道，再强模式通道。
        # 2026-09-11 修：先前漏了 classify_fulltext 这一档，导致靠全文规则打上的标签
        # 在工作表里显示成"空证据"（如 jantimon/web-performance-debugger 的"流程"），
        # 会把人误导成"错标"。
        ft, _ = classify_fulltext(text)
        if c in ft:
            ev[c].append("[全文规则命中]（无标题/正文信号时的兜底通道）")
            continue
        for p in STRONG_PATTERNS.get(c, []):
            if re.search(p, text, re.I):
                ev[c].append("[强模式命中]（全文正则，跨语言通道）")
                break
    return ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--zh", type=int, default=10)
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--out", default="work/audit")
    a = ap.parse_args()

    df = substantive(load_corpus())
    rng = random.Random(a.seed)
    main_idx = sorted(rng.sample(list(df.index), min(a.n, len(df))))
    zh_pool = [i for i in df.index if df.at[i, "doc_language"] == "zh" and i not in main_idx]
    zh_idx = sorted(rng.sample(zh_pool, min(a.zh, len(zh_pool))))

    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    rec = {"seed": a.seed, "n": a.n, "zh": a.zh,
           "main": [df.at[i, "file_sha"] for i in main_idx],
           "zh_extra": [df.at[i, "file_sha"] for i in zh_idx]}
    (outdir / "v0.2-sample.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    L: list[str] = []
    L.append("# v0.2 人工核对工作表（待人工判定）\n")
    L.append(f"> 抽样：主样本 {a.n} 份 = 从 511 份实质文件中**无分层随机抽**（seed `{a.seed}`）；"
             f"中文补充 {a.zh} 份单独统计。抽中清单见 `work/audit/v0.2-sample.json`，可复现。\n")
    L.append("> 判定口径：**准确** = 该类确实存在；**漏标** = 文件里明明有这类内容但没打上；"
             "**错标** = 打上了但文件里没有这类内容。\n")
    L.append("> 每组判定完，把汇总填进文末的统计表——那份汇总才是我要写进 `LIMITATIONS.md` 的东西。\n")
    L.append("> ⚠ **判「错标」请回到原文**，不要只信「命中证据」列：那一列是**抽取器实际用的证据**，它可能是错的\n"
             "> （实测：`ci` 命中了 `De**ci**sions` / `Prin**ci**ples`，`script` 命中了 `Type**Script**`）。\n"
             "> 「命中证据」错的场合，类别本身仍然可能是对的——两件事要分开判。每条的完整原文路径见该条末尾。\n")
    L.append("\n---\n")

    for title, idxs in (("主样本（随机 30，用于整体估计）", main_idx),
                        ("中文补充样本（单独报告）", zh_idx)):
        L.append(f"\n## {title}\n")
        for k, i in enumerate(idxs, 1):
            r = df.loc[i]
            raw = pathlib.Path(r["local_file"]).read_text(encoding="utf-8", errors="replace") \
                if "local_file" in df.columns and isinstance(r.get("local_file"), str) else ""
            if not raw:
                cand = pathlib.Path("data/raw/full") / f"{r['repo_full_name'].replace('/', '__')}.md"
                raw = cand.read_text(encoding="utf-8", errors="replace") if cand.exists() else ""
            tags = set(r["categories"])
            ev = evidence_for(raw, tags)
            heads = [h for h, _ in split_sections(raw) if h.strip()]
            L.append(f"### {k}. `{r['repo_full_name']}` — {r['file_path']}")
            L.append(f"- 语言 {r['doc_language']} ｜ {r['bytes']} 字节 ｜ {r['section_count']} 章节 ｜ "
                     f"{int(r['repo_stars'])} ★ ｜ 许可 {r['license']}")
            L.append("- **规则分配**：" + ("、".join(f"{CAT_ZH[c]}" for c in CATS if c in tags) or "（无）"))
            L.append("- 命中证据：")
            for c in CATS:
                if c in ev and ev[c]:
                    L.append(f"  - {CAT_ZH[c]}：{' ；'.join(ev[c][:2])}")
            L.append(f"- 文件标题（{len(heads)}）：" + (" / ".join(heads[:14]) or "（无标题）"))
            body = re.sub(r"\n{2,}", "\n", raw.strip())[:600]
            L.append("- 原文摘录（前 600 字）：\n\n```text\n" + body + "\n```")
            cand_path = f"data/raw/full/{r['repo_full_name'].replace('/', '__')}.md"
            L.append(f"- 完整原文：`{cand_path}`（本页只摘前 600 字）")
            L.append("- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：")
            L.append("")
    L.append("\n---\n\n## 汇总（判完填这里）\n")
    L.append("| 组 | 份数 | 准确 | 漏标 | 错标 | 备注 |")
    L.append("|---|---|---|---|---|---|")
    L.append(f"| 主样本（随机） | {len(main_idx)} | | | | |")
    L.append(f"| 中文补充 | {len(zh_idx)} | | | | |")
    L.append("\n按类别的漏标/错标明细（可选，有具体例子时填）：\n")
    L.append("| 类别 | 漏标例数 | 错标例数 | 典型例子（repo/标题） |")
    L.append("|---|---|---|---|")
    for c in CATS:
        L.append(f"| {CAT_ZH[c]} | | | |")

    (outdir / "v0.2-worksheet.md").write_text("\n".join(L), encoding="utf-8")
    print(f"生成 {(outdir/'v0.2-worksheet.md')}：主样本 {len(main_idx)} 份 + 中文 {len(zh_idx)} 份")
    print("主样本 file_sha：" + ", ".join(df.at[i, "file_sha"][:8] for i in main_idx[:5]) + " ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
