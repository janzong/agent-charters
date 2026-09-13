#!/usr/bin/env python3
"""发现「含中文的 AGENTS.md」候选仓库（v0.6 中文留出集专用）。

用法: .venv/bin/python work/discover_cn.py
输出: work/cn-candidates.txt （owner/repo，已排除 v0.5 语料库已有的仓库）

为什么用中文关键词查：GitHub code search 对中文是按字面切的，用中文词能直接
把「正文里有中文」的文件捞出来，比按 language: 分片再筛 CJK 便宜得多。
`--filename AGENTS.md` 保证只命中文件名；每个查询最多 100 条（code_search 限 10/min，
故查询间睡 7s）。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "full"
OUT = ROOT / "work" / "cn-candidates.txt"

QUERIES = [
    "本项目", "项目结构", "代码风格", "开发规范", "提交前",
    "不要", "禁止", "环境变量", "构建", "依赖",
    "运行测试", "分支", "文档", "注意事项", "约定",
]

PER_QUERY = 100
SLEEP_SEC = 7.0


def known_repos() -> set[str]:
    """v0.5 语料库已收录的仓库（原始文件名是 owner__repo.md）。"""
    return {p.stem.replace("__", "/") for p in RAW.glob("*.md")}


def search(query: str) -> list[str]:
    args = ["gh", "search", "code", "--filename", "AGENTS.md",
            "--limit", str(PER_QUERY), "--json", "repository", query]
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        print(f"  ！查询失败 {query!r}: {p.stderr.strip()[:120]}")
        return []
    return [x["repository"]["nameWithOwner"] for x in json.loads(p.stdout or "[]")]


def main() -> int:
    known = known_repos()
    print(f"语料库已有仓库：{len(known)}")
    found: dict[str, list[str]] = {}
    for i, q in enumerate(QUERIES):
        hits = search(q)
        for r in hits:
            found.setdefault(r, []).append(q)
        print(f"[{i+1}/{len(QUERIES)}] {q!r} → {len(hits)} 条（累计 {len(found)}）")
        if i != len(QUERIES) - 1:
            time.sleep(SLEEP_SEC)

    fresh = sorted(r for r in found if r not in known)
    OUT.write_text("\n".join(fresh) + "\n", encoding="utf-8")
    print(f"\n候选 {len(found)} 个 → 排除已收录后 **{len(fresh)}** 个新仓库 → {OUT}")
    print(f"（其中 {len(found) - len(fresh)} 个已在语料库里）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
