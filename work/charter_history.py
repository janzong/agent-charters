"""抓取章程的**修订史**（不是快照），用于回测 H-F1 / H-F2 / H-F7。

私有来源假设（见 work/paired_hypotheses.md）：
  F1 章程是被事故逼出来的  F2 章程寿命长于代码活跃期  F7 高产期=记录荒废期

用法:
  .venv/bin/python work/charter_history.py --limit 40 [--offset 0]
输出: data/raw/charter_history.jsonl（追加式缓存，可断点续跑）

注意：只取元数据与提交信息，不落原文；单仓库调用数 ≈ 2 + min(修订数, 10)。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

OUT = Path("data/raw/charter_history.jsonl")
CACHE = {}
if OUT.exists():
    for line in OUT.read_text().splitlines():
        try:
            rec = json.loads(line)
            CACHE[rec["repo"]] = rec
        except json.JSONDecodeError:
            pass


def gh(path: str) -> list | dict | None:
    r = subprocess.run(["gh", "api", "-X", "GET", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def fetch(repo: str, max_rev: int = 10) -> dict:
    revs = gh(f"repos/{repo}/commits?path=AGENTS.md&per_page=100")
    if not isinstance(revs, list):
        return {"repo": repo, "error": "no_history"}
    rec = {"repo": repo, "n_revisions": len(revs), "revisions": []}
    for c in revs[:max_rev]:
        sha, commit = c["sha"], c["commit"]
        detail = gh(f"repos/{repo}/commits/{sha}") or {}
        files = [f.get("filename", "") for f in detail.get("files", [])]
        msg = (commit.get("message") or "").splitlines()[0]
        rec["revisions"].append({
            "sha": sha[:10],
            "date": commit["author"]["date"][:10],
            "message": msg[:200],
            "files_changed": len(files),
            "code_touched": any(not f.endswith((".md", ".mdc", ".txt")) for f in files),
            "files": files[:12],
        })
    cl = gh(f"repos/{repo}/commits?path=CHANGELOG.md&per_page=100")
    rec["changelog_revisions"] = len(cl) if isinstance(cl, list) else None
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--sort", default="stars", choices=["stars", "alpha"])
    args = ap.parse_args()

    import pandas as pd
    df = pd.read_parquet("data/processed/agent-charters-v0.1.parquet")
    df = df[df["is_substantive"] & ~df["is_pointer"]]
    if args.sort == "stars":
        df = df.sort_values("repo_stars", ascending=False)
    targets = df["repo_full_name"].tolist()[args.offset:args.offset + args.limit]

    done = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for i, repo in enumerate(targets, 1):
            if repo in CACHE:
                continue
            rec = fetch(repo)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            done += 1
            r = rec.get("n_revisions", rec.get("error"))
            print(f"  [{i}/{len(targets)}] {repo:<45} 修订={r}", flush=True)
    print(f"\n完成 {done} 个，累计缓存 {len(CACHE) + done}")


if __name__ == "__main__":
    main()
