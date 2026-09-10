"""批量抓取 AGENTS.md 及其仓库元数据（GraphQL，含配额监控）。

用法: .venv/bin/python work/fetch_full.py work/repos_topics.txt work/repos_all.txt
输出: data/raw/full/*.md  +  data/raw/full_manifest.jsonl
"""
import json
import subprocess
import sys
import time
from pathlib import Path


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def gql(query: str) -> dict:
    proc = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query],
                          capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:200])
    return json.loads(proc.stdout)


def quota_left() -> int:
    try:
        p = subprocess.run(["gh", "api", "rate_limit", "--jq",
                            ".resources.graphql.remaining"],
                           capture_output=True, text=True, timeout=30)
        return int(p.stdout.strip())
    except Exception:
        return -1


FIELDS = (
    'stargazerCount pushedAt isFork '
    'primaryLanguage { name } licenseInfo { spdxId } '
    'object(expression:"HEAD:AGENTS.md") { ... on Blob { byteSize oid text } }'
)


def main() -> None:
    repos: list[str] = []
    seen: set[str] = set()
    for path in sys.argv[1:]:
        for line in Path(path).read_text().splitlines():
            r = line.strip()
            if r and r not in seen:
                seen.add(r)
                repos.append(r)
    print(f"候选仓库数 = {len(repos)}   graphql 配额剩余 = {quota_left()}")

    outdir = Path("data/raw/full")
    outdir.mkdir(parents=True, exist_ok=True)
    batch = 20
    hits: list[dict] = []
    checked = 0
    errors = 0

    for start in range(0, len(repos), batch):
        if start % (batch * 10) == 0 and quota_left() < 300:
            print(f"!! graphql 配额不足，停在 {start}")
            break
        chunk = repos[start:start + batch]
        parts = []
        for j, full in enumerate(chunk):
            owner, name = full.split("/", 1)
            parts.append(f'r{j}: repository(owner:"{esc(owner)}", name:"{esc(name)}") '
                         f"{{ {FIELDS} }}")
        try:
            payload = gql("{" + " ".join(parts) + "}")
        except Exception as exc:
            print(f"batch {start}: ERROR {exc}")
            errors += 1
            time.sleep(3)
            continue
        checked += len(chunk)
        for j, full in enumerate(chunk):
            node = (payload.get("data") or {}).get(f"r{j}") or {}
            blob = node.get("object")
            if not blob or blob.get("text") is None:
                continue
            p = outdir / (full.replace("/", "__") + ".md")
            p.write_text(blob["text"], encoding="utf-8")
            hits.append({
                "repo_full_name": full,
                "file_path": "AGENTS.md",
                "file_sha": blob.get("oid"),
                "bytes": blob.get("byteSize"),
                "repo_stars": node.get("stargazerCount"),
                "repo_pushed_at": node.get("pushedAt"),
                "repo_language": (node.get("primaryLanguage") or {}).get("name"),
                "license": (node.get("licenseInfo") or {}).get("spdxId"),
                "is_fork": node.get("isFork"),
                "local_file": str(p),
            })
        if start % (batch * 10) == 0:
            print(f"  进度 {start}/{len(repos)}  命中={len(hits)}  "
                  f"配额剩余={quota_left()}", flush=True)

    mf = Path("data/raw/full_manifest.jsonl")
    with mf.open("w", encoding="utf-8") as fh:
        for row in hits:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n检查 {checked} 个仓库，失败批次 {errors}，命中 {len(hits)} 份 "
          f"({len(hits) * 100 // max(checked, 1)}%) -> {mf}")
    print(f"graphql 配额剩余 = {quota_left()}")


if __name__ == "__main__":
    main()
