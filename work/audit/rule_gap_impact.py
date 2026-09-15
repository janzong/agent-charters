#!/usr/bin/env python3
"""两处词表缺口的全库影响实测（v0.5 / ruleset_v0.1.8）—— **只测，不改规则**。

`LIMITATIONS.md` §22 记了两个召回缺口：`boundaries` 的正文禁令家族缺「绝不」、
`overview` 的标题词表缺「这是什么」（外加标题词表缺「绝对不能做」）。
当时的处置是"待人裁定"，并按 D32 要求 —— **改规则前先实测影响**。本脚本把影响测出来：

    探针 A：`BODY_RULES["boundaries"]` 加「绝不」
    探针 B：`HEAD_RULES["overview"]` 加「这是什么」
    探针 C：`HEAD_RULES["boundaries"]` 加「绝对不能做」

四个面（都不改仓库里的任何常量，全在内存里打完就还原）：

  1. v0.5 全库 558 份：多少份新增/丢失标签、内容模式是否变化、**516 份实质文件的覆盖率怎么动**；
  2. v0.6 新采的 1046 份中文：新增多少（这是"会不会只对英文友好"的对照）;
  3. 中文留出集 **50 份盲判**：新命中里有多少条**人判过"有"**（真召回），
     多少条人判"无"（那就是新引入的假阳性）—— 这是判"该不该加词"最硬的一条证据；
  4. 新增 `boundaries` / `overview` 的**上下文**：§22 说正文通道是"提到即命中"，
     所以逐行打出来供人判断是"规定"还是"只是在讨论这个词"。

用法：`.venv/bin/python work/audit/rule_gap_impact.py`
      加 `--dump /tmp/rule-gap-contexts.txt` 把上下文写到文件。
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
from pathlib import Path

import agent_charters.taxonomy as tax
from agent_charters.extract import analyze_text

ROOT = Path(__file__).resolve().parents[2]

PROBES = {
    "A": "绝不 → boundaries（正文禁令家族）",
    "B": "这是什么 → overview（标题词表）",
    "C": "绝对不能做 → boundaries（标题词表）",
}
PROBE_SETS = [("A",), ("B",), ("C",), ("A", "B"), ("A", "B", "C")]


@contextlib.contextmanager
def patched(ids: tuple[str, ...]):
    """在内存里加词，退出时还原——仓库里的常量一个字都不动。"""
    body = {k: list(v) for k, v in tax.BODY_RULES.items()}
    head = {k: list(v) for k, v in tax.HEAD_RULES.items()}
    if "A" in ids:
        tax.BODY_RULES["boundaries"].insert(0, "绝不")
    if "B" in ids:
        tax.HEAD_RULES["overview"].append("这是什么")
    if "C" in ids:
        tax.HEAD_RULES["boundaries"].append("绝对不能做")
    try:
        yield
    finally:
        tax.BODY_RULES, tax.HEAD_RULES = body, head


def load_full() -> list[tuple[str, Path]]:
    out = []
    for line in (ROOT / "data/raw/full_manifest.jsonl").read_text(
            encoding="utf-8").splitlines():
        d = json.loads(line)
        out.append((d["repo_full_name"], ROOT / d["local_file"]))
    return out


def load_cn() -> list[tuple[str, Path]]:
    out = []
    for line in (ROOT / "data/raw/cn_manifest.jsonl").read_text(
            encoding="utf-8").splitlines():
        d = json.loads(line)
        out.append((d["repo_full_name"],
                    ROOT / "data/raw/cn" / (d["repo_full_name"].replace("/", "__") + ".md")))
    return out


def holdout_calls() -> dict[str, set[str]]:
    calls = {}
    for i in range(1, 11):
        p = ROOT / f"work/audit/v0.6-cn-calls-a{i}.json"
        if p.exists():
            calls.update({k: set(v["call"])
                          for k, v in json.loads(p.read_text(encoding="utf-8"))["files"].items()})
    return calls


def analyzed(files) -> dict[str, dict]:
    out = {}
    for repo, path in files:
        out[repo] = analyze_text(path.read_text(encoding="utf-8", errors="replace"))
    return out


def substantive_repos() -> set[str]:
    """数据集里那 516 份（is_substantive 且非转引用）——覆盖率的分母，前后同一批。"""
    rows = [json.loads(l) for l in
            (ROOT / "data/processed" / "agent_charters_v0.5.jsonl").read_text(
                encoding="utf-8").splitlines()]
    return {r["repo_full_name"] for r in rows if r["is_substantive"] and not r["is_pointer"]}


def coverage(labels: dict[str, set[str]], repos: set[str]) -> dict[str, float]:
    n = len(repos) or 1
    return {c: round(sum(1 for r in repos if c in labels[r]) * 100 / n, 1)
            for c in ("overview", "boundaries", "gotchas", "agent_meta",
                      "structure", "workflow", "style", "environment", "build_test")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", help="把新增命中的上下文写到这个文件（含原文片段，别放仓库）")
    ap.add_argument("--verify-v05", action="store_true",
                    help="改了规则之后跑这里：用当前规则重算 558 份，逐份对比已发布的 v0.5 标签，"
                         "有差异就打印并退出码 1（例行检查：这次改词有没有动到已发布资产）")
    args = ap.parse_args()

    full, cn = load_full(), load_cn()
    print(f"v0.5 全库 {len(full)} 份 ｜ v0.6 中文 {len(cn)} 份")

    with patched(()):
        base_full = analyzed(full)
        base_cn = analyzed(cn)
    labels = {r: set(v["categories"]) for r, v in base_full.items()}
    sub = substantive_repos()
    base_cov = coverage(labels, sub)

    calls = holdout_calls()
    print(f"\n中文留出集：{len(calls)} 份有盲判", end="")
    with patched(()):
        base_hold = {r: set(analyze_text(
            (ROOT / "data/raw/cn" / (r.replace("/", "__") + ".md")).read_text(
                encoding="utf-8", errors="replace"))["categories"]) for r in calls}
    print(f"；其中规则当前就标了 boundaries 的 {sum('boundaries' in v for v in base_hold.values())} 份、"
          f"overview {sum('overview' in v for v in base_hold.values())} 份")

    rows = []
    for ids in PROBE_SETS:
        with patched(ids):
            new_full = analyzed(full)
            new_cn = analyzed(cn)
            new_hold = {r: set(analyze_text(
                (ROOT / "data/raw/cn" / (r.replace("/", "__") + ".md")).read_text(
                    encoding="utf-8", errors="replace"))["categories"]) for r in calls}

        gained: dict[str, set[str]] = {}
        lost, mode_changed = set(), set()
        for repo, rec in new_full.items():
            new, old = set(rec["categories"]), labels[repo]
            if new - old:
                for c in new - old:
                    gained.setdefault(c, set()).add(repo)
            if old - new:
                lost.add(repo)
            if rec["content_mode"] != base_full[repo]["content_mode"]:
                mode_changed.add(repo)
        print(f"\n=== 探针 {'+'.join(ids)}：{' / '.join(PROBES[i] for i in ids)} ===")
        for c in sorted(gained):
            print(f"  v0.5 新增 {c:<12} {len(gained[c]):>3} 份")
        print(f"  丢失任何标签：{len(lost)} 份 ｜ 内容模式变化：{len(mode_changed)} 份")
        if gained.get("boundaries"):
            cn_gain = [r for r in gained["boundaries"] if r in {x for x, _ in cn}]
            print(f"  其中中文文件（v0.6 集合）新增 boundaries：{len(cn_gain)} 份")
        cn_gained = {}
        for repo, rec in new_cn.items():
            old = set(base_cn[repo]["categories"])
            for c in set(rec["categories"]) - old:
                cn_gained.setdefault(c, set()).add(repo)
        for c in sorted(cn_gained):
            print(f"  v0.6 中文 1046 份新增 {c:<12} {len(cn_gained[c]):>3} 份")

        # 盲判对照：新命中里，人判过"有"的算真召回，人判"无"的算新假阳性
        for cat in ("boundaries", "overview"):
            newly = [r for r in calls if cat in new_hold[r] and cat not in base_hold[r]]
            if not newly:
                continue
            tp = [r for r in newly if cat in calls[r]]
            fp = [r for r in newly if cat not in calls[r]]
            print(f"  盲判（50 份）：新增 {cat} {len(newly)} 份 —— "
                  f"人判也有 {len(tp)} 份（真召回）／人判没有 {len(fp)} 份（新假阳性）")
            for r in fp[:6]:
                print(f"      ⚠ 人判无：{r}")

        new_sub_cov = coverage({r: set(v["categories"]) for r, v in new_full.items()}, sub)
        moved = {c: (base_cov[c], new_sub_cov[c]) for c in base_cov
                 if abs(base_cov[c] - new_sub_cov[c]) > 1e-9}
        if moved:
            print("  516 份实质文件的覆盖率变化：" +
                  " ｜ ".join(f"{c} {a}%→{b}%" for c, (a, b) in moved.items()))
        else:
            print("  516 份实质文件的覆盖率：无变化")
        rows.append((ids, gained, lost, mode_changed, cn_gained))

    # --- 三个补充问题：词在库里到底多常见 / 对自家 AGENTS.md 有没有用 / 新增的是真是假 ---
    print("\n=== 补充：这几个词在全库里的出现面 ===")
    probes_lit = {"绝不": "boundaries", "这是什么": "overview", "绝对不能做": "boundaries"}
    for probe, cat in probes_lit.items():
        for name, files_ in (("v0.5", full), ("v0.6 中文", cn)):
            hit = [r for r, p_ in files_ if probe in p_.read_text(encoding="utf-8", errors="replace")]
            already = [r for r in hit if cat in labels.get(r, set())] if name == "v0.5" else []
            extra = f"，其中本来就有 {cat} 的 {len(already)} 份" if name == "v0.5" else ""
            print(f"  「{probe}」：{name} {len(hit)}/{len(files_)} 份含这个词{extra}")
        hold_hit = [r for r in calls
                    if probe in (ROOT / "data/raw/cn" / (r.replace("/", "__") + ".md")).read_text(
                        encoding="utf-8", errors="replace")]
        print(f"      └ 中文留出集 50 份里含它的：{len(hold_hit)} 份"
              f"（盲判里判了 {cat} 的 {sum(cat in calls[r] for r in hold_hit)} 份）")

    print("\n=== 补充：对本仓库自己的 AGENTS.md（不在语料库里，所以上面的覆盖率测不到它）===")
    own = ROOT / "AGENTS.md"
    cats = ("overview", "structure", "build_test", "style", "workflow", "environment",
            "boundaries", "gotchas", "agent_meta")
    for ids in [(), ("A",), ("B",), ("A", "B")]:
        with patched(ids):
            got = set(analyze_text(own.read_text(encoding="utf-8"))["categories"])
        label = "（现状）" if not ids else f"加 {'+'.join(ids)}"
        miss = [c for c in cats if c not in got]
        print(f"  {label:<10} {len(got & set(cats))}/9 类 ｜ 还缺：{', '.join(miss) or '无'}")

    if args.verify_v05:
        # 与 dump 分开：这条是"改完规则后的例行验证"，用**当前**规则重算，不再打补丁。
        rows = [json.loads(l) for l in (ROOT / "data/processed" / "agent_charters_v0.5.jsonl")
                .read_text(encoding="utf-8").splitlines()]
        stored = {r["repo_full_name"]: r for r in rows}
        cur = analyzed(full)
        print(f"\n=== --verify-v05：当前规则（{tax.RULESET_VERSION}）对 v0.5 的标签中性检查 ===")
        print(f"  已发布 {len(stored)} 份 ｜ 本次重算 {len(cur)} 份"
              f"（键唯一性：{'OK' if len(cur) == len(full) else '有重名仓库，已按仓库名合并'}）")
        bad = []
        for repo, rec in sorted(cur.items()):
            old_row = stored.get(repo)
            if old_row is None:
                bad.append((repo, "重算里有、已发布里没有", "", ""))
                continue
            new_cats, old_cats = set(rec["categories"]), set(old_row["categories"])
            if new_cats != old_cats or rec["content_mode"] != old_row["content_mode"]:
                bad.append((repo, "+".join(sorted(new_cats - old_cats)),
                            "-".join(sorted(old_cats - new_cats)),
                            f"mode {old_row['content_mode']}→{rec['content_mode']}"))
        missing = sorted(set(stored) - set(cur))
        for repo in missing:
            bad.append((repo, "", "", "重算里没有（文件缺失？）"))
        if bad:
            print(f"  ❌ {len(bad)} 份有差异：")
            for repo, added, removed, extra in bad:
                print(f"     {repo:<58} +{added or '-':<14} -{removed or '-':<14} {extra}")
        else:
            print("  ✅ 逐份标签与内容模式**完全一致**——这次改动对 v0.5 是标签中性的。")
        sub_cov = coverage({r: set(v["categories"]) for r, v in cur.items()}, substantive_repos())
        print("  516 份实质文件覆盖率：" +
              " / ".join(f"{c} {sub_cov[c]}%" for c in ("boundaries", "overview")))
        return 1 if bad else 0

    if args.dump:
        # 注意：v0.5 全库的新增是 0，真正有新增的是 **v0.6 中文**那 6+8 份，
        # 所以这里两个语料都要扫（早先只扫 v0.5 → 永远 0 行）。
        word_for = {"boundaries": "绝不", "overview": "这是什么"}
        out, hits = [], 0
        for label, files_, base in (("v0.5", full, base_full), ("v0.6 中文", cn, base_cn)):
            with patched(("A", "B")):
                new = analyzed(files_)
            for repo, rec in sorted(new.items()):
                gained = set(rec["categories"]) - set(base[repo]["categories"])
                cats = sorted(gained & set(word_for))
                if not cats:
                    continue
                hits += 1
                lines = dict(files_)[repo].read_text(encoding="utf-8", errors="replace").splitlines()
                for cat in cats:
                    word = word_for[cat]
                    out.append(f"### {label}\t{repo}\t新增 {cat}")
                    for i, line in enumerate(lines, 1):
                        if word in line:
                            out.append(f"    L{i}: {line.strip()[:200]}")
        Path(args.dump).write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"\n新增命中（A/B）的文件 {hits} 份、上下文 {len(out)} 行 → {args.dump}")
        print("⚠️ 这个 dump 含原文片段：只给人看，**别放进仓库**（与 `data/raw/` 同一道边界）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
