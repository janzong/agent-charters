"""T0 取样：从仓库列表批量取回 AGENTS.md 正文（GraphQL 批量，绕开 code_search 限流）。

用法: .venv/bin/python work/fetch_samples.py work/repos_raw.txt
输出: data/raw/samples/*.md  +  data/raw/samples_manifest.jsonl
"""
import json
import subprocess
import sys
from pathlib import Path


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    listfile = sys.argv[1] if len(sys.argv) > 1 else "work/repos_raw.txt"
    repos = [l.strip() for l in Path(listfile).read_text().splitlines() if l.strip()]
    outdir = Path("data/raw/samples")
    outdir.mkdir(parents=True, exist_ok=True)

    batch_size = 25
    hits = []
    for start in range(0, len(repos), batch_size):
        chunk = repos[start:start + batch_size]
        parts = []
        for j, full in enumerate(chunk):
            owner, name = full.split("/", 1)
            parts.append(
                f'r{j}: repository(owner:"{esc(owner)}", name:"{esc(name)}") '
                '{ object(expression:"HEAD:AGENTS.md") '
                "{ ... on Blob { byteSize oid text } } }"
            )
        query = "{" + " ".join(parts) + "}"
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", "query=" + query],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            print(f"batch {start}: ERROR {proc.stderr[:160]}")
            continue
        payload = json.loads(proc.stdout)
        for j, full in enumerate(chunk):
            node = (payload.get("data") or {}).get(f"r{j}") or {}
            blob = node.get("object")
            if not blob or blob.get("text") is None:
                continue
            path = outdir / (full.replace("/", "__") + ".md")
            path.write_text(blob["text"], encoding="utf-8")
            hits.append({
                "repo_full_name": full,
                "file_path": "AGENTS.md",
                "file_sha": blob.get("oid"),
                "bytes": blob.get("byteSize"),
                "local_file": str(path),
            })
        print(f"batch {start}: cumulative hits = {len(hits)}")

    manifest = Path("data/raw/samples_manifest.jsonl")
    with manifest.open("w", encoding="utf-8") as fh:
        for row in hits:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"TOTAL hits = {len(hits)} -> {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
