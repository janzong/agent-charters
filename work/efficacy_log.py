#!/usr/bin/env python3
"""章程有效性 —— **仪表轨**：在真实任务流里记账，回答一个问题：

    **写在章程里的规则，实际被遵守的比例是多少？**（合规率 / ceiling check）

设计：`work/audit/plan-efficacy.md`（2026-09-18 裁定：L1 主 + L3 辅 + L2 抽样；双判 + 一致率作废；
**先付 0 小时 = 本轨**；证据为正再投 1.5–2 小时做三臂对照 T/C1/C2）。

**为什么主指标是"合规率"而不是"有/无章程的差异"**（2026-09-18 调整，原来的设计有个硬伤）：
我们机队只在自己那几个仓上干活，而这些仓**几乎都有章程**（rmas-v3 / agent-charters 都有，
Codex 还会自动加载）⇒ "无章程"那一臂**根本没有样本**，靠它做对照只会得到空表。
反过来，"章程里明写的规则有没有被遵守"**不需要对照组**、当天就能出数，而且它正好是决定
"**值不值得花人力做正式实验**"的那个量：

    合规率 ≥95% ⇒ 天花板效应，T/C1/C2 测不出东西 ⇒ **不做正式实验**（省下那 1.5–2 小时）
    70–95%     ⇒ 有空间 ⇒ **值得做**
    <70%       ⇒ 问题不是"有没有用"而是"**根本没被执行**" ⇒ 换方向（执行机制），别做有效性实验

同样一张表将来仍能直接装正式实验（多一个 `--arm T|C1|C2`）。

**记什么**（每完成一个**真实**任务记一行）：
  --repo      仓库
  --task      一句话任务描述
  --rules     适用的规则编号（`work/efficacy-rules.jsonl` 里登记的，逗号分隔，如 `ac1,ac7`；
              没有适用规则就写 `none`）
  --applicable  登记表之外的规则，自由文本（`;` 分隔，可选）
  --violated  产出**实际违反**的规则（编号或原文，必须是适用集合的子集，脚本会拦）
  --rework    发起方要求返工的轮数（0 = 一次过）
  --charter   yes|no：任务运行时上下文里**确实有**该仓章程吗（默认 yes；只在无章程的仓上才填 no）
  --judge     谁判的（`作者` / `人` / `另一模型`）
  --arm       `fleet`（默认）/ `T` / `C1` / `C2`

用法：
  .venv/bin/python work/efficacy_log.py rules                        # 看规则登记表
  .venv/bin/python work/efficacy_log.py add --repo agent-charters --task "修 X" \\
      --rules ac1,ac7 --violated ac7 --rework 1
  .venv/bin/python work/efficacy_log.py report
  .venv/bin/python work/efficacy_log.py show --limit 20

⚠️ 纪律：**不回填历史任务**（回填带"已知结果"的偏差）；**每个真实任务都记，不许挑着记**。
⚠️ 合规率的分母是"规则条目数"，把同一条规则在不同任务上的表现当独立观察——这会**高估**精度，
   所以 CI 只当参考，不当结论。真正能读的还是"离天花板有多远"。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "work/efficacy-log.jsonl"
DEFAULT_RULES = ROOT / "work/efficacy-rules.jsonl"
ARMS = ("fleet", "T", "C1", "C2")


# ---------------------------------------------------------------- 规则登记表

def registry(path: pathlib.Path) -> dict[str, dict[str, str]]:
    """{repo: {rule_id: 规则原文}}"""
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            out[d["repo"]] = {r["id"]: r["rule"] for r in d["rules"]}
    return out


def cmd_rules(args) -> int:
    reg = registry(args.rules_file)
    if not reg:
        print("还没有登记表。")
        return 0
    for repo, rs in reg.items():
        print(f"\n{repo}")
        for rid, rule in rs.items():
            print(f"  {rid:<5} {rule}")
    return 0


# ---------------------------------------------------------------- 记账

def load(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"⚠️  第 {i} 行不是合法 JSON，已跳过", file=sys.stderr)
    return out


def cmd_add(args) -> int:
    reg = registry(args.rules_file).get(args.repo, {})
    ids = [s.strip() for s in (args.rules or "").split(",") if s.strip() and s.strip() != "none"]
    unknown = [i for i in ids if i not in reg]
    if unknown:
        print(f"✗ {args.repo} 的登记表里没有这些编号：{unknown}\n"
              f"  先看 `.venv/bin/python work/efficacy_log.py rules`；要加规则就编辑 "
              f"work/efficacy-rules.jsonl", file=sys.stderr)
        return 2
    if args.repo in registry(args.rules_file) and not args.rules and not args.applicable:
        print(f"✗ {args.repo} 有规则登记表：适用就填 --rules，确实没有适用规则就写 --rules none",
              file=sys.stderr)
        return 2
    extra = [s.strip() for s in (args.applicable or "").split(";") if s.strip()]
    applicable = [reg[i] for i in ids] + extra
    vio = [s.strip() for s in (args.violated or "").split(",") if s.strip()]
    vio = [reg.get(v, v) for v in vio]                      # 允许用编号或原文
    bad = [v for v in vio if v not in applicable]
    if bad:
        print(f"✗ violated 里有不在适用集合里的项：{bad}\n"
              f"  （判定只认「明写且适用」的规则；先把它加进去，或去掉）", file=sys.stderr)
        return 2
    if args.charter not in ("yes", "no") or args.arm not in ARMS:
        print("✗ --charter 只能是 yes/no；--arm 只能是 " + "/".join(ARMS), file=sys.stderr)
        return 2
    now = dt.datetime.now().astimezone()
    row = {"ts": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
           "repo": args.repo, "task": args.task, "arm": args.arm,
           "charter": args.charter == "yes", "applicable_ids": ids,
           "applicable": applicable, "violated": vio,
           "rework": int(args.rework), "judge": args.judge, "notes": args.notes or ""}
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"已记：{row['date']} {row['repo']}｜适用规则 {len(applicable)} 条｜违规 {len(vio)} 条"
          f"｜返工 {row['rework']}")
    return 0


# ---------------------------------------------------------------- 统计

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    ph, d = k / n, 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def diff_ci(a: list[int], b: list[int], iters: int = 5000, seed: int = 20260918):
    """两臂均值差的 bootstrap 95% 区间（小样本用，不做正态假设）。"""
    if not a or not b:
        return None
    rng = random.Random(seed)
    ds = sorted(sum(rng.choices(a, k=len(a))) / len(a) - sum(rng.choices(b, k=len(b))) / len(b)
                for _ in range(iters))
    return ds[int(0.025 * iters)], ds[int(0.975 * iters)]


CEILING_GE, CEILING_LO = 0.95, 0.70        # 预登记档位（见 plan-efficacy.md §9）


def cmd_report(args) -> int:
    rows = load(args.log)
    if not rows:
        print("表还是空的。第一个真实任务完成后用 `add` 记一行（**不要回填历史**）。")
        return 0

    tot_rules = sum(len(r["applicable"]) for r in rows)
    tot_vio = sum(len(r["violated"]) for r in rows)
    tasks_with_rules = sum(1 for r in rows if r["applicable"])
    tasks_vio = sum(1 for r in rows if r["violated"])

    print(f"=== 章程有效性·仪表轨（n={len(rows)} 任务，{rows[0]['date']} → {rows[-1]['date']}）===")
    print(f"\n【主指标】合规率（规则条目级）")
    if tot_rules:
        k = tot_rules - tot_vio
        lo, hi = wilson(k, tot_rules)
        print(f"  {k}/{tot_rules} = {k * 100 / tot_rules:.1f}%"
              f"  95% CI [{lo * 100:.1f}, {hi * 100:.1f}]（CI 偏乐观，仅供参考）")
        if tot_rules / len(rows) < 1.0 or tasks_with_rules < len(rows):
            print(f"  ⚠️ 覆盖：{tasks_with_rules}/{len(rows)} 个任务有适用规则、"
                  f"平均每个任务 {tot_rules / len(rows):.1f} 条 ⇒ 分母还太薄")
        rate = k / tot_rules
        if rate >= CEILING_GE:
            verdict = "≥95% ⇒ **天花板效应**：正式 T/C1/C2 实验测不出东西，**建议不做**（省下那 1.5–2 小时）"
        elif rate >= CEILING_LO:
            verdict = "70–95% ⇒ 有空间 ⇒ **值得做**正式三臂对照"
        else:
            verdict = "<70% ⇒ 问题不是\"有没有用\"而是\"**根本没被执行**\" ⇒ 换方向（执行机制），别做有效性实验"
        print(f"  预登记档位：{verdict}")
    else:
        print("  还没有任何任务填过适用规则 ⇒ 分母为 0，先让 `add` 真的带上 --rules。")

    print(f"\n【辅】任务级：{tasks_vio}/{len(rows)} 个任务至少违反一条"
          f"（{tasks_vio * 100 / len(rows):.1f}%）；平均返工 "
          f"{sum(r['rework'] for r in rows) / len(rows):.2f} 轮")

    # 分组（臂 / 章程有无）——只在真的有方差时才有意义
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r.get("arm") if r.get("arm") in ("T", "C1", "C2")
                          else ("有章程" if r.get("charter") else "无章程"), []).append(r)
    print(f"\n【分组】", end="")
    for g, rs in sorted(groups.items()):
        nr = sum(len(x["applicable"]) for x in rs)
        nv = sum(len(x["violated"]) for x in rs)
        print(f"\n  {g:<8} 任务 {len(rs):<4} 规则 {nr:<4} 违规 {nv:<4}"
              f" 合规率 {100 * (nr - nv) / nr:5.1f}%" if nr else
              f"\n  {g:<8} 任务 {len(rs):<4} 规则 0（填不出分母）")
    for x, y in (("有章程", "无章程"), ("T", "C1"), ("T", "C2")):
        if x in groups and y in groups:
            a = [1 if r["violated"] else 0 for r in groups[x]]
            b = [1 if r["violated"] else 0 for r in groups[y]]
            ci = diff_ci(a, b)
            if ci:
                lo, hi = ci
                mark = "CI 跨 0 ⇒ 分不出来" if lo <= 0 <= hi else "CI 不跨 0"
                print(f"  违规率差（{x} − {y}）= "
                      f"{(sum(a) / len(a) - sum(b) / len(b)) * 100:+.1f}pp"
                      f"  [{lo * 100:+.1f}, {hi * 100:+.1f}]pp ⇒ {mark}")

    print("\n  ⚠️ 本轨**非随机**：只能读成「值不值得做正式实验」，**不能当因果证据**。")
    if len(rows) < 20:
        print(f"  ⚠️ 只有 {len(rows)} 行 —— 现在什么都读不出来，继续攒。")
    return 0


def cmd_show(args) -> int:
    for r in load(args.log)[-args.limit:]:
        v = f" 违规={';'.join(x[:28] for x in r['violated'])}" if r["violated"] else ""
        print(f"{r['date']} [{r.get('arm', '?')}] {r['repo']}｜{r['task']}"
              f"｜适用 {len(r['applicable'])}｜返工 {r['rework']}{v}"
              + (f"｜{r['notes'][:80]}" if r.get("notes") else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="章程有效性·仪表轨（真实任务流记账）")
    ap.add_argument("--log", type=pathlib.Path, default=DEFAULT_LOG)
    ap.add_argument("--rules-file", type=pathlib.Path, default=DEFAULT_RULES)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("rules", help="打印规则登记表")

    a = sub.add_parser("add", help="记一行（每完成一个真实任务）")
    a.add_argument("--repo", required=True)
    a.add_argument("--task", required=True)
    a.add_argument("--rules", default="", help="登记表里的规则编号，逗号分隔；没有适用规则写 none")
    a.add_argument("--applicable", default="", help="登记表之外的规则（自由文本，; 分隔）")
    a.add_argument("--violated", default="", help="实际违反的（编号或原文，必须是适用集合子集）")
    a.add_argument("--rework", default=0, help="返工轮数，0=一次过")
    a.add_argument("--charter", default="yes", help="yes / no（上下文里确实有该仓章程吗）")
    a.add_argument("--judge", default="作者", help="作者 / 人 / 另一模型")
    a.add_argument("--arm", default="fleet", help="fleet（仪表轨）/ T / C1 / C2")
    a.add_argument("--notes", default="")

    sub.add_parser("report", help="合规率 + 预登记档位 + 分组")
    s = sub.add_parser("show", help="看最近几行")
    s.add_argument("--limit", type=int, default=20)

    args = ap.parse_args()
    return {"rules": cmd_rules, "add": cmd_add,
            "report": cmd_report, "show": cmd_show}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
