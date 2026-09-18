#!/usr/bin/env python3
"""章程有效性 —— **仪表轨**：在真实任务流里记三个字段，为「要不要做正式对照实验」提供依据。

设计：`work/audit/plan-efficacy.md`（2026-09-18 裁定：L1 主 + L3 辅 + L2 抽样；双判 + 一致率作废；
**先付 0 小时 = 本轨**；证据为正再投 1.5–2 小时做三臂对照 T/C1/C2）。

**为什么先做这个**：我们缺的不是"章程有多少人写"（分母研究已答），而是"**章程到底有没有用**"。
正式实验要人出判定时间；在那之前，真实任务流里本来就有天然变异（有的仓有章程、有的没有），
把它顺手记下来，成本≈0。

**记什么**（每完成一个**真实**任务记一行）：
  --repo          仓库
  --task          一句话任务描述
  --charter yes|no   任务运行时 agent 上下文里**确实有**该仓库的章程吗
                     （Codex 会自动加载 cwd 向上的 AGENTS.md；没有那份文件就填 no）
  --applicable    章程里**明写**且**适用于本任务**的规则（`;` 分隔）。判定只认这些，别的都不算
  --violated      产出**实际违反**的规则（必须是 applicable 的子集）
  --rework        发起方要求返工的轮数（0 = 一次过）
  --judge         谁判的（`作者` / `人` / `另一模型`）
  --arm           臂：仪表轨填 `fleet`（默认）；将来正式实验填 `T` / `C1` / `C2`

**同一张表既能装仪表轨、也能装正式实验**（正式实验只多一个 `--arm`），所以现在建不算白建。

用法：
  .venv/bin/python work/efficacy_log.py add --repo rmas-v3 --task "修 X" \
      --charter yes --applicable "不动 data/raw;提交用 conventional commits" --violated "" --rework 1
  .venv/bin/python work/efficacy_log.py report
  .venv/bin/python work/efficacy_log.py show --limit 20

⚠️ 本轨**非随机**（谁有章程和任务类型相关），所以只能读成"值不值得做正式实验"，**不能当因果证据**。
⚠️ **不要回填历史任务**：回填必然带着"已经知道结果"的偏差。表从 2026-09-18 开始。
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
ARMS = ("fleet", "T", "C1", "C2")


def load(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"⚠️  第 {i} 行不是合法 JSON，已跳过", file=sys.stderr)
    return out


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
    ds = []
    for _ in range(iters):
        ds.append(sum(rng.choices(a, k=len(a))) / len(a)
                  - sum(rng.choices(b, k=len(b))) / len(b))
    ds.sort()
    return ds[int(0.025 * iters)], ds[int(0.975 * iters)]


def cmd_add(args) -> int:
    app = [s.strip() for s in (args.applicable or "").split(";") if s.strip()]
    vio = [s.strip() for s in (args.violated or "").split(";") if s.strip()]
    bad = [v for v in vio if v not in app]
    if bad:
        print(f"✗ violated 里有不在 applicable 里的项：{bad}\n"
              f"  （判定只认「明写且适用」的规则；先把它加进 --applicable，或去掉）", file=sys.stderr)
        return 2
    if args.charter not in ("yes", "no"):
        print("✗ --charter 只能是 yes / no", file=sys.stderr)
        return 2
    if args.arm not in ARMS:
        print(f"✗ --arm 只能是 {'/'.join(ARMS)}", file=sys.stderr)
        return 2
    if args.charter == "no" and app:
        print("✗ 没有章程却填了 applicable —— 要么 --charter yes，要么清空 --applicable", file=sys.stderr)
        return 2
    now = dt.datetime.now().astimezone()
    row = {"ts": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
           "repo": args.repo, "task": args.task, "arm": args.arm,
           "charter": args.charter == "yes", "applicable": app, "violated": vio,
           "rework": int(args.rework), "judge": args.judge, "notes": args.notes or ""}
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"已记：{row['date']} {row['repo']}｜章程={'有' if row['charter'] else '无'}"
          f"｜适用规则 {len(app)} 条｜违规 {len(vio)} 条｜返工 {row['rework']}")
    return 0


def _key(row: dict) -> str:
    return row["arm"] if row.get("arm") in ("T", "C1", "C2") else (
        "有章程" if row.get("charter") else "无章程")


def cmd_report(args) -> int:
    rows = load(args.log)
    if not rows:
        print("表还是空的。第一个真实任务完成后用 `add` 记一行（**不要回填历史**）。")
        return 0
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(_key(r), []).append(r)

    print(f"=== 章程有效性·仪表轨（n={len(rows)}，"
          f"{rows[0]['date']} → {rows[-1]['date']}）===")
    print(f"  {'组':<8}{'任务':>5}{'违规任务':>10}{'违规率':>9}{'95% CI':>16}{'平均返工':>9}")
    stat = {}
    for g, rs in sorted(groups.items()):
        v = [1 if r["violated"] else 0 for r in rs]
        rw = [int(r["rework"]) for r in rs]
        k = sum(v)
        lo, hi = wilson(k, len(v))
        stat[g] = (v, rw)
        print(f"  {g:<8}{len(rs):>5}{k:>10}{k * 100 / len(rs):>8.1f}%"
              f"  [{lo * 100:4.1f},{hi * 100:4.1f}]{sum(rw) / len(rw):>9.2f}")

    for x, y in (("有章程", "无章程"), ("T", "C1"), ("T", "C2")):
        if x in stat and y in stat:
            ci = diff_ci(stat[x][0], stat[y][0])
            lo, hi = ci if ci else (0, 0)
            mark = "CI 跨 0 ⇒ 分不出来" if lo <= 0 <= hi else "CI 不跨 0"
            print(f"\n  违规率差（{x} − {y}）= "
                  f"{(sum(stat[x][0]) / len(stat[x][0]) - sum(stat[y][0]) / len(stat[y][0])) * 100:+.1f}pp"
                  f"  bootstrap 95% CI [{lo * 100:+.1f}, {hi * 100:+.1f}]pp  ⇒ {mark}")

    small = [g for g, rs in groups.items() if len(rs) < 20]
    if small:
        print(f"\n  ⚠️ {'、'.join(small)} 的样本 <20 —— 现在的差异**读不出任何东西**，继续攒。")
    print("  ⚠️ 本轨**非随机**（有章程的仓与任务类型相关）：只能读成"
          "「值不值得做正式三臂对照」，**不能当因果证据**。")
    return 0


def cmd_show(args) -> int:
    rows = load(args.log)
    for r in rows[-args.limit:]:
        v = f" 违规={len(r['violated'])}" if r["violated"] else ""
        print(f"{r['date']} [{r['arm']}] {'有' if r['charter'] else '无'}章程 "
              f"{r['repo']}｜{r['task']}｜返工 {r['rework']}{v}"
              + (f"｜{r['notes']}" if r.get("notes") else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="章程有效性·仪表轨（真实任务流记账）")
    ap.add_argument("--log", type=pathlib.Path, default=DEFAULT_LOG)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="记一行（每完成一个真实任务）")
    a.add_argument("--repo", required=True)
    a.add_argument("--task", required=True)
    a.add_argument("--charter", required=True, help="yes / no")
    a.add_argument("--applicable", default="", help="章程里明写且适用于本任务的规则，`;` 分隔")
    a.add_argument("--violated", default="", help="实际违反的（必须是 applicable 子集）")
    a.add_argument("--rework", default=0, help="返工轮数，0=一次过")
    a.add_argument("--judge", default="作者", help="作者 / 人 / 另一模型")
    a.add_argument("--arm", default="fleet", help="fleet（仪表轨）/ T / C1 / C2")
    a.add_argument("--notes", default="")

    sub.add_parser("report", help="分组统计 + bootstrap CI")
    s = sub.add_parser("show", help="看最近几行")
    s.add_argument("--limit", type=int, default=20)

    args = ap.parse_args()
    return {"add": cmd_add, "report": cmd_report, "show": cmd_show}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
