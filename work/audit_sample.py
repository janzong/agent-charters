#!/usr/bin/env python3
"""v0.2 人工核对：抽样并生成"可审核工作表"。

为什么这么抽样（方法上别搞错）：
- 要估计的是**整体准确率/漏标率**，所以主样本必须是**从 511 份里无分层随机抽**——
  按类别分层会让类别频率失真，算出来的不是语料库的真实准确率。
- 中文只有 26 份且是已知弱点，单独抽一组**只报分组结果**，不并入主样本估计。

产物：
- work/audit/v0.2-sample.json     抽样记录（seed + file_sha 列表 + identity 身份表，保证可复现）
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
    ap.add_argument("--main", "--n", dest="n", type=int, default=30)
    ap.add_argument("--zh", type=int, default=10)
    ap.add_argument("--edge", type=int, default=0, help="边界件（指针 + 空壳）")
    ap.add_argument("--rare", type=int, default=0, help="稀有类加成（gotchas/overview）")
    ap.add_argument("--blind", type=int, default=0, help="额外产出：只给题面的盲判组份数")
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--version", default="v0.2", help="数据版本，用于产物命名")
    ap.add_argument("--out", default="work/audit")
    a = ap.parse_args()

    allrows = load_corpus()
    df = substantive(allrows)
    rng = random.Random(a.seed)
    main_idx = sorted(rng.sample(list(df.index), min(a.n, len(df))))
    zh_idx = sorted(i for i in df.index if df.at[i, "doc_language"] == "zh")

    # 边界件：转引用文件（全取，语料库只有 7 份）+ 非实质空壳随机抽。
    # 注意指针池要从 allrows 取——从 df（=substantive() 的 511 基座）里找，
    # 等于在"已排除指针"的集合里找指针，恒为空。2026-09-12 的 C 组就是这么漏掉 7 份的。
    ptr_idx = sorted(i for i in allrows.index if allrows.at[i, "is_pointer"])
    shell_pool = [i for i in allrows.index if not allrows.at[i, "is_substantive"]]
    shell_idx = sorted(rng.sample(shell_pool, max(0, min(a.edge - len(ptr_idx), len(shell_pool))))) if a.edge else []
    edge_idx = ptr_idx + shell_idx

    # 稀有类加成：先 gotchas，再 overview（两组不重叠、也不与其它组重叠）
    used = set(main_idx) | set(zh_idx) | set(edge_idx)
    rare_idx: list = []
    if a.rare:
        got = [i for i in df.index if "gotchas" in df.at[i, "categories"] and i not in used]
        ov = [i for i in df.index if "overview" in df.at[i, "categories"]
              and "gotchas" not in df.at[i, "categories"] and i not in used]
        n_got = min(len(got), max(1, a.rare // 2))
        rare_idx = sorted(rng.sample(got, n_got)) + sorted(rng.sample(ov, min(a.rare - n_got, len(ov))))

    blind_idx = sorted(main_idx[: a.blind]) if a.blind else []

    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    # 身份表：file_sha 是**内容哈希**，空壳文件 30 个仓库共用一个 sha（9 字节空文件），
    # 只存 sha 会丢身份、下游 join 会张冠李戴（2026-09-12 踩过）。故并列存 repo/path。
    def ident(idx, src):
        return [{"sha": src.at[i, "file_sha"], "repo": src.at[i, "repo_full_name"],
                 "file_path": src.at[i, "file_path"]} for i in idx]

    rec = {"seed": a.seed, "version": a.version,
           "counts": {"main": len(main_idx), "zh_census": len(zh_idx),
                      "edge": len(edge_idx), "rare_boost": len(rare_idx), "blind": len(blind_idx)},
           "main": [df.at[i, "file_sha"] for i in main_idx],
           "zh_census": [df.at[i, "file_sha"] for i in zh_idx],
           "edge": [allrows.at[i, "file_sha"] for i in edge_idx],
           "rare_boost": [df.at[i, "file_sha"] for i in rare_idx],
           "blind20": [df.at[i, "file_sha"] for i in blind_idx],
           "identity": {"main": ident(main_idx, df), "zh_census": ident(zh_idx, df),
                        "edge": ident(edge_idx, allrows), "rare_boost": ident(rare_idx, df),
                        "blind20": ident(blind_idx, df)}}
    (outdir / f"{a.version}-sample.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    L: list[str] = []
    L.append(f"# {a.version} 人工核对工作表（待人工判定）\n")
    L.append(f"> 抽样（seed `{a.seed}`，可复现，清单见 `work/audit/{a.version}-sample.json`）："
             f"**主样本 {len(main_idx)} = 无分层随机（只有这组能代表全体）**；"
             f"中文 **普查** {len(zh_idx)} 份；边界件 {len(edge_idx)} 份（转引用 {len(ptr_idx)} + 空壳 {len(shell_idx)}）；"
             f"稀有类加成 {len(rare_idx)} 份。后三组**只报分组结果，不并入整体估计**。\n")
    L.append("> 判定口径：**准确** = 该类确实存在；**漏标** = 文件里明明有这类内容但没打上；"
             "**错标** = 打上了但文件里没有这类内容。\n")
    L.append("> 每组判定完，把汇总填进文末的统计表——那份汇总才是我要写进 `LIMITATIONS.md` 的东西。\n")
    L.append("> ⚠ **判「错标」请回到原文**，不要只信「命中证据」列：那一列是**抽取器实际用的证据**，它可能是错的\n"
             "> （实测：`ci` 命中了 `De**ci**sions` / `Prin**ci**ples`，`script` 命中了 `Type**Script**`）。\n"
             "> 「命中证据」错的场合，类别本身仍然可能是对的——两件事要分开判。每条的完整原文路径见该条末尾。\n")
    L.append("\n---\n")

    groups = [(f"主样本（随机 {len(main_idx)}，用于整体估计）", main_idx, df),
              (f"中文普查（{len(zh_idx)} 份，单独报告）", zh_idx, df),
              (f"边界件（{len(edge_idx)} 份，单独报告）", edge_idx, allrows),
              (f"稀有类加成（{len(rare_idx)} 份，单独报告）", rare_idx, df)]
    for title, idxs, src in groups:
        if not idxs:
            continue
        L.append(f"\n## {title}\n")
        for k, i in enumerate(idxs, 1):
            r = src.loc[i]
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
    for title, idxs in (("主样本（随机，代表全体）", main_idx), ("中文普查", zh_idx),
                        ("边界件", edge_idx), ("稀有类加成", rare_idx)):
        L.append(f"| {title} | {len(idxs)} | | | | |")
    L.append("\n按类别的漏标/错标明细（可选，有具体例子时填）：\n")
    L.append("| 类别 | 漏标例数 | 错标例数 | 典型例子（repo/标题） |")
    L.append("|---|---|---|---|")
    for c in CATS:
        L.append(f"| {CAT_ZH[c]} | | | |")

    ws = outdir / f"{a.version}-worksheet.md"
    ws.write_text("\n".join(L), encoding="utf-8")
    print(f"生成 {ws}：主样本 {len(main_idx)} + 中文 {len(zh_idx)} + 边界件 {len(edge_idx)} + 稀有 {len(rare_idx)}")

    if blind_idx:
        # 盲判组：**只给题面，不给任何规则输出**；正文也不内嵌（仓库不含原文全文），
        # 只给本地路径——判者自己打开文件读全文，避免"只摘 600 字"这种上次的坑。
        B = [
            f"# 盲判组（{len(blind_idx)} 份）——请只做一件事：列出每份文件里**实际有什么**\n",
            "> **怎么读**：对每条，打开「原文」那个路径读**全文**（VS Code 里点开即可）。\n",
            "> **怎么标**：通读后在「答案」行写下这份文件**确实包含**的类别（九类里选任意几类，"
            "没有的就不写）。**不要猜规则想要什么**——这一遍要的就是你的独立判断。\n",
            "> **判不准的**：在该类后面加 `?`（例：`风格?`），我会单独统计「犹豫」的比例。\n",
            f"> 判完把答案发我。之后我才会打开 `{ws.name}` 对照——先别看它，看了就白判了。\n",
            "",
            "## 九类是什么意思（判定依据只有这几行）\n",
            "| 类别 | 收什么 |",
            "|---|---|",
            "| 概览 overview | 这个项目/仓库是什么、技术栈、目的、核心概念 |",
            "| 架构 structure | 代码怎么组织：目录结构、模块划分、谁负责哪块、关键文件在哪 |",
            "| 构建测试 build_test | 怎么构建/测试/运行/校验（命令也算），以及「改完该跑什么」 |",
            "| 风格 style | 代码怎么写：命名、格式、约定、最佳实践、错误处理 |",
            "| 流程 workflow | 分支、提交信息、PR、评审、发布、版本、变更日志 |",
            "| 环境 environment | 环境、工具链、依赖、配置、安装、版本要求 |",
            "| 禁令 boundaries | 「不要做什么」：禁止、边界、卫生规则、红线 |",
            "| 坑 gotchas | 坑、陷阱、已知问题、踩过的雷、限制 |",
            "| AI行为 agent_meta | 对 AI 自身的规定：角色、语气、身份、协作方式、该怎么做事 |",
            "\n---\n",
        ]
        for k, i in enumerate(blind_idx, 1):
            r = df.loc[i]
            p = f"data/raw/full/{r['repo_full_name'].replace('/', '__')}.md"
            path = pathlib.Path(p)
            heads = [h for h, _ in split_sections(path.read_text(encoding="utf-8", errors="replace"))] if path.exists() else []
            B.append(f"### {k}. `{r['repo_full_name']}` — {r['file_path']}")
            B.append(f"- {r['doc_language']} ｜ {r['bytes']} 字节 ｜ {r['section_count']} 章节 ｜ {int(r['repo_stars'])} ★")
            B.append(f"- 原文：`{p}`")
            B.append(f"- 标题（{len(heads)}）：" + (" / ".join(h.strip() for h in heads[:14]) or "（无标题）"))
            hint = "（例：概览, 构建测试, 禁令；不确定的写 `风格?`）" if k == 1 else ""
            B.append(f"- **答案**：______ {hint}")
            B.append("")
        B.append("\n---\n\n## 答案汇总（判完把这段发我）\n")
        B.append("```text")
        for k in range(1, len(blind_idx) + 1):
            B.append(f"{k}. ")
        B.append("```")
        blind = outdir / f"{a.version}-blind{len(blind_idx)}.md"
        blind.write_text("\n".join(B), encoding="utf-8")
        print(f"生成 {blind}：{len(blind_idx)} 份，只有题面与路径，无任何规则输出")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
