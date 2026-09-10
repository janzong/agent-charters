"""用 topic 定位 AI/agent 相关仓库池（比 code_search 的语言分片有效）。

用法: .venv/bin/python work/discover_repos2.py
输出: work/repos_topics.txt
"""
import json
import subprocess
import time
from pathlib import Path

QUERIES = [
    ("topic:ai-agents", 200),
    ("topic:agent", 200),
    ("topic:mcp", 200),
    ("topic:llm", 200),
    ("topic:coding-agent", 200),
    ("topic:claude-code", 200),
    ("topic:ai", 200),
    ("topic:developer-tools", 200),
]


def main() -> None:
    found: dict[str, str] = {}
    for i, (q, lim) in enumerate(QUERIES):
        proc = subprocess.run(
            ["gh", "search", "repos", q, "--limit", str(lim),
             "--json", "fullName,stargazersCount,isFork"],
            capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            print(f"[{i}] {q:<24} ERROR {proc.stderr[:90]}")
        else:
            items = json.loads(proc.stdout or "[]")
            new = 0
            for it in items:
                full = it["fullName"]
                if it.get("isFork"):
                    continue
                if full not in found:
                    found[full] = q
                    new += 1
            print(f"[{i}] {q:<24} {len(items):>4} hits, +{new:>4} new (total {len(found)})")
        time.sleep(2.5)

    Path("work/repos_topics.txt").write_text(
        "\n".join(sorted(found)) + "\n", encoding="utf-8")
    print(f"\nTOTAL unique repos from topics = {len(found)}")


if __name__ == "__main__":
    main()
