#!/usr/bin/env python3
"""活动仓库里的「死 AGENTS.md」：文件级最后提交 vs 仓库最后推送。

**为什么有这个脚本**：2026-09-20 dev.to 读者 `frankchu` 问——有没有外部信号能区分
「活文件」与「活仓库里的死内容」。先交底：随包语料的 `commit_date` 实测等于
`repo_pushed_at`（558/558），它记录的是仓库 HEAD 时间，**不是** AGENTS.md 的
最后修改时间，所以不能直接拿它回答。这里用 GraphQL 在每个仓库 HEAD 的
`history(path="AGENTS.md", until=快照日)` 取回文件级最后提交时间，再与
`data/raw/full_manifest.jsonl` 里冻结的 `repo_pushed_at` 比。

    .venv/bin/python work/active_stale_check.py          # 有缓存读缓存
    REFRESH=1 .venv/bin/python work/active_stale_check.py  # 强制重取

输出：仓库活跃 × 文件新旧的双向表、常见内容信号在「活文件 / 活仓库死文件」
两组里的占比、Fisher 双尾 p（手算，不依赖 scipy）。
边界：GraphQL `until` 只按日期截断；横截面；信号是相关性不是因果。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "agent_charters/data/agent-charters-v0.5.jsonl.gz"
MANIFEST = ROOT / "data/raw/full_manifest.jsonl"
CACHE = ROOT / "data/cache/active_stale/file_history.json"
YEAR_IN_HEADING = re.compile(r"\b(?:19|20)\d{2}\b")


def day(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date() if "T" in value else datetime.strptime(value, "%Y-%m-%d").date()


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    from math import comb
    n, r1, c1 = a + b + c + d, a + b, a + c

    def p(x: int) -> float:
        return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)

    obs = p(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs + 1e-12)


def fetch_history(repos: list[dict[str, str]]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for start in range(0, len(repos), 50):
        batch = repos[start:start + 50]
        parts = []
        for i, repo in enumerate(batch):
            owner, name = repo["name"].split("/", 1)
            until = repo["until"]
            parts.append(
                f'r{i}: repository(owner:"{owner}", name:"{name}") {{ '
                f'object(expression:"HEAD") {{ ... on Commit {{ '
                f'history(path:"AGENTS.md", first:1, until:"{until}") {{ '
                f'nodes {{ committedDate oid }} }} }} }} }}'
            )
        query = "query { " + " ".join(parts) + " }"
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(proc.stdout)
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {payload['errors'][:2]}")
        data = payload["data"]
        for i, repo in enumerate(batch):
            node = data.get(f"r{i}")
            history = ((node or {}).get("object") or {}).get("history") or {}
            nodes = history.get("nodes") or []
            if nodes:
                out[repo["name"]] = {"committed_date": nodes[0]["committedDate"], "oid": nodes[0]["oid"]}
            else:
                out[repo["name"]] = {"miss": "null history / renamed / deleted"}
        print(f"fetched {min(start + 50, len(repos))}/{len(repos)}", file=sys.stderr)
    return out


def main() -> int:
    import gzip

    rows = [json.loads(line) for line in gzip.open(CORPUS, "rt", encoding="utf-8")]
    manifest = {json.loads(line)["repo_full_name"]: json.loads(line) for line in open(MANIFEST, encoding="utf-8")}
    repos = [
        {"name": row["repo_full_name"], "until": row["retrieved_at"] + "T23:59:59Z"}
        for row in rows
    ]

    if REFRESH := os.environ.get("REFRESH"):
        history = fetch_history(repos)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"fetched_at": date.today().isoformat(), "repos": history}, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        history = json.loads(CACHE.read_text(encoding="utf-8"))["repos"]

    misses = [name for name, item in history.items() if "miss" in item]
    recs = []
    for row in rows:
        meta = manifest[row["repo_full_name"]]
        item = history[row["repo_full_name"]]
        if "miss" in item:
            continue
        asof = day(row["retrieved_at"])
        text = Path(meta["local_file"]).read_text(encoding="utf-8", errors="replace")
        headings = [line for line in text.splitlines() if line.lstrip().startswith("#")]
        recs.append({
            **row,
            "repo_idle": (asof - day(meta["repo_pushed_at"])).days,
            "file_age": (asof - day(item["committed_date"])).days,
            "dated_heading": any(YEAR_IN_HEADING.search(h) for h in headings),
        })

    active = [r for r in recs if r["repo_idle"] <= 90]
    idle = [r for r in recs if r["repo_idle"] > 90]
    print(f"可用样本 {len(recs)}/{len(rows)}（miss {len(misses)}；fetched_at {date.today() if REFRESH else 'cache'}）")
    print(f"仓库 >90 天未推（墓碑侧）：{len(idle)}；其中文件 >90 天未动：{sum(r['file_age'] > 90 for r in idle)}")
    print(f"仓库 ≤90 天有推送（active）：{len(active)}")
    for threshold in (30, 90, 180, 365):
        count = sum(r["file_age"] > threshold for r in active)
        print(f"  其中 AGENTS.md >{threshold} 天未动：{count}/{len(active)} = {100 * count / len(active):.1f}%")

    live = [r for r in active if r["file_age"] <= 90]
    stale = [r for r in active if r["file_age"] > 180]
    print(f"\n信号对比（active 仓库内；live=文件≤90 天 {len(live)}，stale=文件>180 天 {len(stale)}）")
    median = sorted(r["bytes"] for r in active)[len(active) // 2]
    signals = {
        "dated_heading": lambda r: r["dated_heading"],
        "duplicate_sha>1": lambda r: r["duplicate_sha_count"] > 1,
        "content_mode=knowledge": lambda r: r["content_mode"] == "knowledge",
        "not_substantive": lambda r: not r["is_substantive"],
        "routes_outward": lambda r: r["routes_outward"],
        "hard_route": lambda r: r["hard_route"],
        "bytes>median": lambda r: r["bytes"] > median,
    }
    print(f"  （active 中位体积 {median} B；Fisher 未做多重比较校正）")
    for key, fn in signals.items():
        a, b = sum(fn(r) for r in live), len(live)
        c, d = sum(fn(r) for r in stale), len(stale)
        pl, ps = 100 * a / b if b else 0, 100 * c / d if d else 0
        print(f"  {key}: live {a}/{b}={pl:.1f}% | stale {c}/{d}={ps:.1f}% | Fisher p={fisher_two_sided(a, b - a, c, d - c):.4f}")
    print("边界：按天取整；until=快照日全天；重命名/删库计入 miss；信号是横截面相关。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
