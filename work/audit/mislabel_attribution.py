#!/usr/bin/env python3
"""留出集 10 处错标归因（environment 5 / boundaries 5）+ 附带发现：口径与实现不符。

用法: .venv/bin/python work/audit/mislabel_attribution.py
输出: work/audit/v0.5-holdout-mislabel-attribution.md

纪律：**只归因，不改规则、不提改法**（§3.2 / D11 高 precision 低 recall 是刻意取舍）。
规则层任何调整都属于"改分类法"，须先由人裁定（D32）。

证据提取是程序化的（走 agent_charters 包的 classify()，与语料库同一条规则路径）；
人工那一列（"归因"）是本轮读原文后写的判断，硬编码在下面两张表里，改一个字都要重跑。
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent_charters.extract import analyze_text, split_sections  # noqa: E402
from agent_charters.taxonomy import classify  # noqa: E402

RAW = ROOT / "data" / "raw" / "full"
OUT = ROOT / "work/audit/v0.5-holdout-mislabel-attribution.md"

# (repo, 归因机制, 说明) —— 说明是读原文后写的，不是脚本推出来的
ENV = [
    ("owncloud/notes", "标题词多义",
     "`Dependency Management` 一节讲的是**依赖更新的流程与约束**（Dependabot PR 谁来审、"
     "新增依赖要先开 issue），不是环境/依赖清单；标题通道只看得到 `dependency` 这个词面。"),
    ("leon-ai/leon", "标题词多义",
     "`Tools` 一节讲 tool 的目录怎么放、继承哪个 SDK 基类、命名与导出约定——是**代码结构**"
     "（人判 structure）；`tool` 在英文里同时指「工具链」与「tool 这个抽象」。"),
    ("NateBJones-Projects/OB1", "标题词多义",
     "`Setup pattern` 讲多 agent 并行时「一个 agent 一个 worktree」的协作范式（人判 workflow）"
     "——`setup` 词面像「环境搭建」，实义是「工作模式」。"),
    ("deanpeters/Product-Manager-Skills", "正文关键词字面命中",
     "`Release Checklist` 里只有一句提到 `app/.env.example` 要跟着改（发布流程的一步）；"
     "配置文件名出现在**讲流程的句子**里，就点亮了 environment。"),
    ("coleam00/Archon", "标题词多义",
     "`Preserve provider configuration; scope capabilities` 讲 provider 配置的**归属与边界**"
     "（不得替换用户 home、节点只拿到显式声明的 skills）——语义落在 boundaries / agent_meta，"
     "不是项目环境配置。"),
]

BND = [
    ("morganlinton/Albatross", "正文句式：流程顺序",
     "`Do not mark release work complete until step 4 succeeds`——「没跑完第 4 步不许打勾」是"
     "**发版流程的步骤约束**，句式是禁令、语义是流程（人判 workflow）。"),
    ("youssefvdel/qwengate", "正文句式：代码约定",
     "`Export reusable builders, don't inline copies`——代码复用约定，夹在一串「配置放哪」的"
     "条目中间（人判 environment）。"),
    ("shikokuchuo/secretbase", "正文句式：风格 / 打包",
     "`don't reformat tests/tests.R`（Formatter 一节）与 `don't ship to CRAN`（Packaging 一节）"
     "——格式与打包规则，不是禁令（人判 style / build_test）。"),
    ("yashdev9274/supercli", "正文句式：描述句",
     "`global monitors don't receive mouseUp`——解释 macOS 事件机制**为什么**要绕开，是描述句；"
     "正是 `LIMITATIONS.md` §13 预告的那类残余假阳性。"),
    ("okwasniewski/MiniSim", "标题词多义",
     "`SwiftLint Rules` / `Disabled Rules`——`rules` 指 lint 规则（人判 style），不是禁令条目。"),
]


def evidence(repo: str, cat: str) -> list[tuple[str, list[str]]]:
    """该文件里所有产出 cat 标签的章节，以及命中的证据串。"""
    text = (RAW / f"{repo.replace('/', '__')}.md").read_text(encoding="utf-8", errors="replace")
    out = []
    for head, body in split_sections(text):
        if not head.strip() and len(body.strip()) < 40:
            continue
        tags, ev = classify(head, body)
        if cat in tags:
            out.append((head.strip(), ev.get(cat) or []))
    return out


def load_calls() -> dict[str, dict]:
    rows = {}
    for line in (ROOT / "data/processed/agent_charters_v0.5.jsonl").read_text(
            encoding="utf-8").splitlines():
        r = json.loads(line)
        rows[r["repo_full_name"]] = r
    out = {}
    for p in sorted((ROOT / "work/audit").glob("v0.5-holdout-calls-a*.json")):
        for repo, v in json.loads(p.read_text(encoding="utf-8"))["files"].items():
            out[rows[repo]["file_sha"]] = {"repo": repo, "call": set(v["call"]),
                                           "bl": set(v.get("borderline", []))}
    return out


def calibre(calls: dict[str, dict]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """两种口径下的 (TP, FP, FN)。A = 现行实现；B = 文档口径（犹豫出局）。"""
    A = collections.Counter()
    B = collections.Counter()
    for c in calls.values():
        text = (RAW / f"{c['repo'].replace('/', '__')}.md").read_text(encoding="utf-8",
                                                                   errors="replace")
        rule = set(analyze_text(text)["categories"])
        h, bl = c["call"], c["bl"]
        A["fp"] += len(rule - h); A["fn"] += len(h - rule); A["tp"] += len(h & rule)
        h2 = h | (bl & rule)
        B["fp"] += len(rule - h2); B["fn"] += len(h2 - rule); B["tp"] += len(h2 & rule)
    return (A["tp"], A["fp"], A["fn"]), (B["tp"], B["fp"], B["fn"])


def table(L: list[str], cat: str, entries: list[tuple[str, str, str]],
          calls: dict[str, dict], cat_zh: str) -> None:
    L += [f"## {cat_zh}（{len(entries)} 处错标）", "",
          "| # | repo | 规则命中证据 | 证据处数 | 所在章节 | 我盲判 | 归因机制 |",
          "|---|---|---|---|---|---|---|"]
    by_repo = {c["repo"]: c for c in calls.values()}
    for i, (repo, mech, _) in enumerate(entries, 1):
        ev = evidence(repo, cat)
        heads = "、".join(f"`{h[:38]}`" for h, _ in ev) or "—"
        spans = "；".join(x for _, e in ev for x in e) or "—"
        n = sum(len(e) for _, e in ev)
        c = by_repo[repo]
        note = f"`call`={sorted(c['call'])}" + (f"｜犹豫 {sorted(c['bl'])}" if c["bl"] else "")
        L.append(f"| {i} | `{repo}` | `{spans}` | {n} | {heads} | {note} | **{mech}** |")
    L.append("")
    for i, (repo, mech, why) in enumerate(entries, 1):
        L.append(f"**{i}. `{repo}`（{mech}）** —— {why}")
        L.append("")


def main() -> int:
    calls = load_calls()
    (atp, afp, afn), (btp, bfp, bfn) = calibre(calls)
    mech = collections.Counter([m for _, m, _ in ENV + BND])

    L = ["# 留出集错标归因：`environment` 5 处 / `boundaries` 5 处", "",
         "- 生成：2026-09-13｜规则 `ruleset_v0.1.8`｜数据 v0.5｜来源 "
         "`work/audit/v0.5-holdout-vs-rule.md`（55 份留出集盲判）",
         "- 为什么挑这两类：留出集里它们与 in-sample 差得最远——`environment` precision 77%"
         "（A 组 83%）、recall 57%（77%）；`boundaries` precision 88%（92%）、recall 88%（98%）。",
         "- ⚠️ **只归因，不改规则、不提改法**（§3.2 / D11：高 precision 低 recall 是刻意取舍）。"
         "规则层的任何调整都属于「改分类法」，须先由人裁定（D32）。",
         "- 复算：`.venv/bin/python work/audit/mislabel_attribution.py`；"
         "盲判原文 `work/audit/v0.5-holdout-calls-a*.json`。", "",
         "## 0. 一句话结论", "",
         "这 10 处错标全部落在**两个机制**里，没有第三种：",
         "",
         f"- **标题词多义 {mech['标题词多义']} 处**：`dependency` / `tool` / `setup` / `config` / "
         "`rules` 在英文里各自横跨两个语义域，标题通道只认词面。",
         f"- **正文命中 {mech['正文关键词字面命中'] + mech['正文句式：流程顺序'] + mech['正文句式：代码约定'] + mech['正文句式：风格 / 打包'] + mech['正文句式：描述句']} 处**："
         "4 处是「句式像禁令、语义不是禁令」（流程顺序 / 代码约定 / 风格打包 / 纯描述句），"
         "1 处是配置文件名出现在讲流程的句子里。",
         "",
         "支持面：**10 处的证据都只有 1–2 条**（`environment` 5 份全是 1 条），"
         "与 §13 说的「残余假阳性集中在只靠 1 处证据的文件里」一致。", ""]

    table(L, "environment", ENV, calls, "A. environment")
    table(L, "boundaries", BND, calls, "B. boundaries")

    L += ["## C. 附带发现：文档口径与实现不符（**未改任何数字**）", "",
          "归因过程中撞到一件事，性质不同、单独记在这里：", "",
          "- `work/audit/v0.5-human-vs-rule.md` 与 `work/audit/v0.5-holdout-vs-rule.md` 的开头都写着"
          "「人判**犹豫**的类别单列，**不计入漏标/错标**，另给宽松口径作对照」。",
          "- 但两个脚本的主口径都是 `for c in rule - call` —— **犹豫项实际被算进了错标**；"
          "且 in-sample 脚本里算好的宽松口径（`bl_fp`）**从未打印**，报告里根本找不到那列。",
          "- 实测影响（55 份留出集，同一批规则、同一批判读）：", "",
          "| 口径 | TP | FP | FN | precision | recall |",
          "|---|---|---|---|---|---|",
          f"| 现行实现（犹豫**计入**错标） | {atp} | {afp} | {afn} | **{atp/(atp+afp):.0%}** | "
          f"**{atp/(atp+afn):.0%}** |",
          f"| 文档口径（犹豫**出局**） | {btp} | {bfp} | {bfn} | **{btp/(btp+bfp):.0%}** | "
          f"**{btp/(btp+bfn):.0%}** |",
          "",
          "⇒ 对外引用的 **92% / 70% 是两者里更保守的那个**（把 12 处「我也拿不准」当成规则的错）；",
          "按文档写的口径算应是 97% / 71%。**这不是数字错了，是「文档描述的口径」与「代码实际的口径」"
          "不一致**——引用者按文档复算会得到另一个数。",
          "",
          "⚠️ **采用哪一条口径对外，属人裁定**（D32），本节只记录事实与两个数，"
          "不改任何对外数字、不改规则、不改脚本行为。",
          "",
          "两组主口径相同，所以 §16 与 §19 的「差 3–5pp」仍是同口径比较，结论不受影响。", ""]

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"写入 {OUT}")
    print(f"现行口径 precision {atp/(atp+afp):.0%} / recall {atp/(atp+afn):.0%}；"
          f"文档口径 {btp/(btp+bfp):.0%} / {btp/(btp+bfn):.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
