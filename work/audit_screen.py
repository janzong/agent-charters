#!/usr/bin/env python
"""v0.2 人工核对的**机器预筛**（不产生判定，只产生"哪条值得人看"）。

做三件事：
  1. 复算每个类别的命中证据（与抽取器同通道，见 work/audit_sample.py）
  2. 对证据分级：强（正文正则）> 标题（关键词命中）> 弱（仅全文强模式）
  3. 标出**可疑命中**——这类标签值得人眼复核，其余可快速通过

可疑的定义（机械可判，不含主观）：
  - `bogus_head`：标题关键词是**非独立词**命中的。taxonomy 的标题通道是 `k in heading`
    子串匹配，所以 "ci" 会命中 De**ci**sions / Prin**ci**ples，"script" 会命中 Type**Script**。
    命中词独立出现（如标题 "CI" / "Running Tests" 中的 run）不算可疑。
  - `strong_only`：该类除"全文强模式"外没有任何标题/正文证据，是证据链最弱的一档。
  - `no_evidence`：打了标签却取不到任何证据（应视为抽取器缺陷）。

输出：work/audit/v0.2-screen.md
用法：.venv/bin/python work/audit_screen.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from agent_charters.taxonomy import CATEGORIES, HEAD_RULES, STRONG_PATTERNS  # noqa: E402
from agent_charters.extract import split_sections, load_corpus, substantive  # noqa: E402
from agent_charters.taxonomy import classify, classify_fulltext  # noqa: E402

CAT_ZH = {"overview": "概览", "structure": "架构", "build_test": "构建测试", "style": "风格",
          "workflow": "流程", "environment": "环境", "boundaries": "禁令", "gotchas": "坑",
          "agent_meta": "AI行为"}

WORD = re.compile(r"[A-Za-z]+")


def keyword_is_clean(low_head: str, kw: str, tokens: set[str]) -> bool:
    """标题关键词命中是否"干净"。

    干净 = 至少有一次命中落在**词首**（"convention" 命中 "Conventions"、"boundar" 命中
    "Boundary" 属规则有意为之的截断词干，算干净）。
    不干净 = 只出现在词中（"ci" 只命中 De**ci**sions / Prin**ci**ples，"script" 只命中
    Type**Script**）——这类命中与词义无关，是子串匹配的假阳性。
    含空格的多词短语与中文关键词不适用词边界，一律算干净。
    """
    if " " in kw or not kw.isascii():
        return True
    for m in re.finditer(re.escape(kw), low_head):
        if m.start() == 0 or not low_head[m.start() - 1].isalpha():
            return True
    return False


def heading_hits(head: str) -> list[tuple[str, str, bool]]:
    """返回 [(类别, 命中词, 是否独立词)]，覆盖全部类别。"""
    low = head.lower()
    tokens = set(WORD.findall(low))
    out = []
    for cat, keys in HEAD_RULES.items():
        for k in keys:
            if k in low:
                standalone = keyword_is_clean(low, k, tokens)
                out.append((cat, k, standalone))
                break
    return out


def main() -> int:
    df = substantive(load_corpus())
    sample = json.loads(pathlib.Path("work/audit/v0.2-sample.json").read_text())
    groups = [("主样本（随机 30）", sample["main"]), ("中文补充 10", sample["zh_extra"])]

    by_sha = {r["file_sha"]: r for _, r in df.iterrows()}

    lines: list[str] = []
    lines.append("# v0.2 人工核对 —— 机器预筛（不构成判定）\n")
    lines.append("> 本文件由 `work/audit_screen.py` 生成，只做**证据分级**与**可疑命中标记**，不做准确/漏标判定。\n")
    lines.append("> 可疑 ≠ 错误：`bogus_head` 只说明「这个标签是靠子串碰上的」，该类内容可能确实存在。\n")

    stat = {"bogus": 0, "strong_only": 0, "no_ev": 0, "clean": 0}
    hot: list[str] = []

    for gname, shas in groups:
        lines.append(f"\n## {gname}\n")
        for i, sha in enumerate(shas, 1):
            r = by_sha.get(sha)
            if r is None:
                lines.append(f"{i}. `{sha[:12]}` —— 未在语料库中找到（跳过）\n")
                continue
            text = pathlib.Path("data/raw/full", r["repo_full_name"].replace("/", "__") + ".md").read_text(
                encoding="utf-8", errors="replace")
            cats = list(r["categories"])
            head_ev: dict[str, list[str]] = {c: [] for c in CATEGORIES}
            body_ev: dict[str, list[str]] = {c: [] for c in CATEGORIES}
            for head, body in split_sections(text):
                if not head.strip() and len(body.strip()) < 40:
                    continue
                _, detail = classify(head, body)
                for c, terms in detail.items():
                    for t in terms:
                        (head_ev if t.startswith("heading:") else body_ev)[c].append(f"{head or '(无标题段)'} ← {t}")
            ft_tags = classify_fulltext(text)[0]
            flags: list[str] = []
            row: list[str] = [f"### {i}. `{r['repo_full_name']}`（{CAT_ZH.get('x','')}{','.join(CAT_ZH[c] for c in cats) or '无'}）"]
            row.append("")
            for c in cats:
                he, be = head_ev[c], body_ev[c]
                note = []
                for h in he:
                    hit = h.split("←")[-1].strip().removeprefix("heading:")
                    hd = h.split("←")[0].strip()
                    if any(cat == c and kw == hit and not sa for cat, kw, sa in heading_hits(hd)):
                        note.append(f"bogus_head:{hit}@{hd[:32]}")
                strong = [p for p in STRONG_PATTERNS.get(c, []) if re.search(p, text, re.I)]
                if not he and not be and not strong and c not in ft_tags:
                    note.append("no_evidence")
                    stat["no_ev"] += 1
                elif not he and not be and not strong:
                    note.append("fulltext_only")
                    stat["strong_only"] += 1
                if any(x.startswith("bogus_head") for x in note):
                    stat["bogus"] += 1
                    hot.append(f"{r['repo_full_name']} :: {CAT_ZH[c]} ← {note[0]}")
                src = "标题" if he else ("正文" if be else ("全文规则" if c in ft_tags else "全文强模式"))
                detail_txt = (he or be or ["[全文兜底命中]"])[0]
                row.append(f"- {CAT_ZH[c]}（{src}）：{detail_txt}" + (f"  ⚠ {', '.join(note)}" if note else ""))
            if not cats:
                stat["clean"] += 1
            lines.extend(row)
            lines.append("")

    lines.append("\n## 汇总\n")
    lines.append(f"- 标了标签但取不到证据（抽取器缺陷）：{stat['no_ev']}")
    lines.append(f"- 只有全文强模式兜底（证据最弱）：{stat['strong_only']}")
    lines.append(f"- 靠非独立词子串碰上的标签：{stat['bogus']}")
    lines.append(f"- 无任何标签的文件：{stat['clean']}")
    lines.append("\n### 子串误命中清单（建议优先人眼复核）\n")
    lines.extend(f"- {h}" for h in hot)

    out = pathlib.Path("work/audit/v0.2-screen.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(json.dumps(stat, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
