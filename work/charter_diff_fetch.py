"""抓取"纯文档型"章程修订的 diff（patch），用于回测 H-F1。

H-F1（章程是被事故逼出来的）在提交信息层测不出来——monorepo 混淆 + 口径覆盖不住。
本脚本只取 `code_touched == False` 的修订（试点的 101 条），拿它们的 patch，
看**新增的行是不是规则句**、**有没有写明触发原因**。

用法: .venv/bin/python work/charter_diff_fetch.py
输出: data/raw/charter_diffs.jsonl（缓存，未入库；只存 AGENTS.md 的新增/删除行）
"""
import json
import subprocess
from pathlib import Path

SRC = Path("data/raw/charter_history.jsonl")
OUT = Path("data/raw/charter_diffs.jsonl")
MAX_LINES = 400


def gh_diff(repo: str, sha: str) -> str | None:
    r = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.diff",
         f"repos/{repo}/commits/{sha}"],
        capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def slice_agents(diff: str) -> list[str]:
    """只保留 AGENTS.md 那个文件的 hunk 行。"""
    keep, on = [], False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            on = "AGENTS.md" in line
            continue
        if on and line[:1] in ("+", "-") and not line.startswith(("+++", "---")):
            keep.append(line)
            if len(keep) >= MAX_LINES:
                break
    return keep


def main() -> None:
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            try:
                done.add(json.loads(line)["sha"])
            except json.JSONDecodeError:
                pass

    targets = []
    for line in SRC.read_text().splitlines():
        rec = json.loads(line)
        for v in rec.get("revisions", []):
            if not v["code_touched"] and v["sha"] not in done:
                targets.append((rec["repo"], v["sha"], v["date"], v["message"]))

    print(f"待抓 {len(targets)} 条（已缓存 {len(done)}）")
    with OUT.open("a", encoding="utf-8") as fh:
        for i, (repo, sha, date, msg) in enumerate(targets, 1):
            diff = gh_diff(repo, sha)
            if diff is None:
                print(f"  [{i}] {repo} {sha} 失败", flush=True)
                continue
            lines = slice_agents(diff)
            added = [l[1:] for l in lines if l.startswith("+")]
            removed = [l[1:] for l in lines if l.startswith("-")]
            fh.write(json.dumps({"repo": repo, "sha": sha, "date": date,
                                 "message": msg, "added": added,
                                 "removed": removed[:100]},
                                ensure_ascii=False) + "\n")
            fh.flush()
            if i % 20 == 0 or i == len(targets):
                print(f"  [{i}/{len(targets)}] {repo}", flush=True)
    print("完成")


if __name__ == "__main__":
    main()
