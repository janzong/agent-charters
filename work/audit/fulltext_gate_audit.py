#!/usr/bin/env python3
"""「全文兜底门」放宽的代价实测（**只测，不改规则**）。

背景：`v0.1.8` 收紧标题通道时顺手把**全文兜底门**关小了一格，`crewAIInc/crewAI` 因此丢了
build_test（撑它的是全文通道的 `run \\`...\\``）。当时的留档（`work/audit/v0.1.8-changelist.md` §A/B.3）
给了一个数："若把门放宽成'已标注章节 ≤1 也跑全文'，全库 8 份会补标签（workflow 4 / build_test 3 /
agent_meta+gotchas 1）"，并把**单独审计**留给下一版（现在是 v0.1.10）。

本脚本把那份审计做出来，口径同 §22.1 的"先测后改"：对四种门算出逐份标签变化、覆盖率变化，
再用**三组人工盲判**判"补上的标签是真还是假"。

门（`analyze_text(fulltext_gate=…)`，见 `agent_charters/extract.py::FULLTEXT_GATES`）：
    empty        现行：完全没有标签，或 ≤1 个标题时才跑全文（＝已发布的 v0.5 口径）
    le1_sections 已标注**章节数** ≤1 也跑（changelist 里点名要审计的那个）
    le1_counts   已标注 (章节,类别) **对数** ≤1 也跑（更宽一点）
    always       总是跑，只做并集（**上界**，用来看这条路最多能补多少、代价多大）

用法：`.venv/bin/python work/audit/fulltext_gate_audit.py`
"""

from __future__ import annotations

import json
import pathlib
import re

from agent_charters.extract import analyze_text
from agent_charters.taxonomy import FULLTEXT_RULES

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATES = ("le1_sections", "le1_counts", "always")
CATS = ("overview", "structure", "build_test", "style", "workflow", "environment",
        "boundaries", "gotchas", "agent_meta")


def load(manifest: str, subdir: str) -> list[tuple[str, pathlib.Path]]:
    out = []
    for line in (ROOT / manifest).read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        name = d["repo_full_name"]
        p = ROOT / d["local_file"] if subdir == "full" else ROOT / "data/raw" / subdir / (
            name.replace("/", "__") + ".md")
        out.append((name, p))
    return out


def calls(paths: list[str]) -> dict[str, set[str]]:
    got: dict[str, set[str]] = {}
    for rel in paths:
        f = ROOT / rel
        if f.exists():
            got.update({k: set(v.get("call", []))
                        for k, v in json.loads(f.read_text(encoding="utf-8"))["files"].items()})
    return got


def substantive() -> set[str]:
    rows = [json.loads(l) for l in (ROOT / "data/processed" / "agent_charters_v0.5.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    return {r["repo_full_name"] for r in rows if r["is_substantive"] and not r["is_pointer"]}


def coverage(labels: dict[str, set[str]], repos: set[str]) -> dict[str, float]:
    n = len(repos) or 1
    return {c: round(sum(1 for r in repos if c in labels[r]) * 100 / n, 1) for c in CATS}


def run(files, gate: str) -> dict[str, dict]:
    out = {}
    for repo, path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rec = analyze_text(text, fulltext_gate=gate)
        out[repo] = {"cats": set(rec["categories"]), "mode": rec["content_mode"]}
    return out


def why(text: str, cat: str) -> str:
    """这个类别是靠哪条全文规则补上的（给人看证据，不参与判定）。"""
    for pat in FULLTEXT_RULES.get(cat, []):
        if re.search(pat, text, re.I):
            m = re.search(pat, text, re.I)
            return f"{pat[:38]} → …{text[max(0, m.start() - 20):m.end() + 20].replace(chr(10), ' ')[:90]}"
    return "(标题/其它通道)"


def main() -> int:
    full = load("data/raw/full_manifest.jsonl", "full")
    cn = load("data/raw/cn_manifest.jsonl", "cn")
    human = {
        "英文留出集": calls([f"work/audit/v0.5-holdout-calls-a{i}.json" for i in range(1, 8)]),
        "in-sample": calls([f"work/audit/v0.4-blind-calls-a{i}.json" for i in range(1, 14)]
                           + [f"work/audit/v0.4-blind-calls-d{i}.json" for i in range(1, 4)]),
        "中文留出集": calls([f"work/audit/v0.6-cn-calls-a{i}.json" for i in range(1, 11)]),
    }
    print(f"v0.5 全库 {len(full)} 份 ｜ v0.6 中文 {len(cn)} 份"
          f"（v0.6 只算「会不会更宽」：它没有人工标注、也没进任何已发布资产）\n")

    base = run(full, "empty")
    sub = substantive()
    base_cov = coverage({r: v["cats"] for r, v in base.items()}, sub)
    print("基线覆盖率（516 份实质文件）：" +
          " / ".join(f"{c} {base_cov[c]}%" for c in CATS) + "\n")
    for gate in GATES:
        cur = run(full, gate)
        added: dict[str, list[str]] = {}
        lost: dict[str, list[str]] = {}
        mode = []
        for repo, rec in cur.items():
            for c in rec["cats"] - base[repo]["cats"]:
                added.setdefault(c, []).append(repo)
            for c in base[repo]["cats"] - rec["cats"]:
                lost.setdefault(c, []).append(repo)
            if rec["mode"] != base[repo]["mode"]:
                mode.append(repo)
        n_new = sum(len(v) for v in added.values())
        n_lost = sum(len(v) for v in lost.values())
        print(f"=== 门 = {gate} ===")
        print(f"  558 份：新增标签 {n_new} 处 / 丢失 {n_lost} 处 / 内容模式变化 {len(mode)} 份")
        for c in CATS:
            if added.get(c) or lost.get(c):
                print(f"    {c:<12} +{len(added.get(c, [])):<3} -{len(lost.get(c, []))}")
        cov = coverage({r: v["cats"] for r, v in cur.items()}, sub)
        moved = {c: (base_cov[c], cov[c]) for c in CATS if abs(base_cov[c] - cov[c]) > 1e-9}
        print("  516 份覆盖率变化：" +
              ("；".join(f"{c} {a}%→{b}%" for c, (a, b) in moved.items()) if moved else "无"))
        # 人工盲判对照：只看新增的 (文件, 类别) 对在盲判里有没有
        print("  人工盲判对照（新增标签落在被盲判过的文件上时，人判有没有这个类）：")
        for name, hc in human.items():
            tgt = {c: [r for r in rs if r in hc] for c, rs in added.items()}
            tgt = {c: rs for c, rs in tgt.items() if rs}
            if not tgt:
                print(f"    {name}：没有新增标签落在它的样本上")
                continue
            tp = sum(1 for c, rs in tgt.items() for r in rs if c in hc[r])
            fp = sum(1 for c, rs in tgt.items() for r in rs if c not in hc[r])
            print(f"    {name}：新增落在其样本上 {tp + fp} 处 —— 人判**有** {tp} 处（真）／"
                  f"人判**没有** {fp} 处（假）")
            for c, rs in sorted(tgt.items()):
                for r in rs:
                    tag = "人判有" if c in hc[r] else "⚠ 人判无"
                    print(f"        {r:<45} +{c:<12} {tag}")
        # 逐条证据（给人判"补上的是真还是假"——这批往往没有盲判覆盖，只能读原文）
        if gate in ("le1_sections", "le1_counts"):
            print("  逐条证据（补上的标签是靠哪条全文规则、原文长什么样）：")
            for c in CATS:
                for r in added.get(c, []):
                    text = dict(full)[r].read_text(encoding="utf-8", errors="replace")
                    print(f"    {r:<45} +{c:<12} {why(text, c)}")
        print()

    print("=== v0.6 中文（只看量级）===")
    cn_base, cn_le1 = run(cn, "empty"), run(cn, "le1_sections")
    n = sum(len(cn_le1[r]["cats"] - cn_base[r]["cats"]) for r in cn_base)
    print(f"  le1_sections：1046 份新增标签 {n} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
