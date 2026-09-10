"""按语言分片枚举含 AGENTS.md 的仓库（绕开 code_search 的 1000 条上限与 10/min 限流）。

用法: .venv/bin/python work/discover_repos.py
输出: work/repos_all.txt （去重后的 owner/repo 列表）
"""
import json
import subprocess
import time
from pathlib import Path

QUERIES = [
    "",
    "language:Python",
    "language:TypeScript",
    "language:JavaScript",
    "language:Go",
    "language:Rust",
    "language:Java",
    "language:C++",
    "language:Ruby",
    "language:Shell",
    "language:Jupyter Notebook",
    "language:C#",
    "language:PHP",
    "language:Kotlin",
    "language:Swift",
]

PER_QUERY = 100
SLEEP_SEC = 7.0  # code_search 限 10/min


def main() -> None:
    found: dict[str, str] = {}
    for i, q in enumerate(QUERIES):
        args = ["gh", "search", "code", "--filename", "AGENTS.md",
                "--limit", str(PER_QUERY), "--json", "repository"]
        if q:
            args.append(q)
        proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            print(f"[{i:>2}] {q or '(all)':<26} ERROR {proc.stderr[:90]}")
        else:
            items = json.loads(proc.stdout or "[]")
            new = 0
            for it in items:
                full = it["repository"]["nameWithOwner"]
                if full not in found:
                    found[full] = q or "all"
                    new += 1
            print(f"[{i:>2}] {q or '(all)':<26} +{new:>3} new  (total {len(found)})")
        if i < len(QUERIES) - 1:
            time.sleep(SLEEP_SEC)

    out = Path("work/repos_all.txt")
    out.write_text("\n".join(sorted(found)) + "\n", encoding="utf-8")
    Path("work/repos_origin.json").write_text(
        json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nTOTAL unique repos = {len(found)} -> {out}")


if __name__ == "__main__":
    main()
