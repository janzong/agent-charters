#!/usr/bin/env python3
"""抓取中文候选仓库的 AGENTS.md（v0.6 中文留出集专用）。

用法: .venv/bin/python work/fetch_cn.py
输入: work/cn-candidates.txt（work/discover_cn.py 产出）
输出: data/raw/cn/<owner>__<repo>.md + data/raw/cn_manifest.jsonl

⚠️ 与 work/fetch_full.py 的区别：**必须另起目录**。fetch_full.py 写 data/raw/full/
并整体重写 data/raw/full_manifest.jsonl——直接用会把 v0.5 语料库的原始件和清单冲掉。
本脚本只写 data/raw/cn/，语料库那份一个字都不碰。

语言判定复用 agent_charters.extract.doc_language（与语料库同一条规则），
不另写一套 CJK 阈值，否则"中文"在两个地方会有两个定义。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_charters.extract import doc_language  # noqa: E402

OUTDIR = ROOT / "data" / "raw" / "cn"
MANIFEST = ROOT / "data" / "raw" / "cn_manifest.jsonl"
BATCH = 20


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def gql(query: str) -> dict:
    p = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query],
                       capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[:200])
    return json.loads(p.stdout)


def quota_left() -> int:
    try:
        p = subprocess.run(["gh", "api", "rate_limit", "--jq",
                            ".resources.graphql.remaining"],
                           capture_output=True, text=True, timeout=30)
        return int(p.stdout.strip())
    except Exception:
        return -1


FIELDS = ('stargazerCount pushedAt isFork primaryLanguage { name } '
          'licenseInfo { spdxId } '
          'object(expression:"HEAD:AGENTS.md") { ... on Blob { byteSize oid text } }')


def main() -> int:
    repos = [r.strip() for r in (ROOT / "work/cn-candidates.txt").read_text(
        encoding="utf-8").splitlines() if r.strip()]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"候选 {len(repos)} 个｜graphql 配额 {quota_left()}")

    hits: list[dict] = []
    errors = 0
    for start in range(0, len(repos), BATCH):
        if start % (BATCH * 10) == 0 and quota_left() < 300:
            print(f"!! 配额不足，停在 {start}")
            break
        chunk = repos[start:start + BATCH]
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
        for j, full in enumerate(chunk):
            node = (payload.get("data") or {}).get(f"r{j}") or {}
            blob = node.get("object")
            if not blob or blob.get("text") is None:
                continue
            text = blob["text"]
            lang = doc_language(text)
            p = OUTDIR / (full.replace("/", "__") + ".md")
            p.write_text(text, encoding="utf-8")
            hits.append({
                "repo_full_name": full,
                "file_path": "AGENTS.md",
                "file_sha": blob.get("oid"),
                "bytes": blob.get("byteSize"),
                "doc_language": lang,
                "cjk": sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff"),
                "repo_stars": node.get("stargazerCount"),
                "repo_pushed_at": node.get("pushedAt"),
                "repo_language": (node.get("primaryLanguage") or {}).get("name"),
                "license": (node.get("licenseInfo") or {}).get("spdxId"),
                "is_fork": node.get("isFork"),
            })
        if start % (BATCH * 20) == 0:
            print(f"  进度 {start}/{len(repos)}  命中={len(hits)}  "
                  f"配额={quota_left()}", flush=True)

    with MANIFEST.open("w", encoding="utf-8") as fh:
        for row in hits:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    zh = [h for h in hits if h["doc_language"] == "zh"]
    print(f"\n取到 {len(hits)} 份（失败批次 {errors}）→ {MANIFEST}")
    print(f"其中 doc_language=zh 的 **{len(zh)}** 份；"
          f"mixed {sum(1 for h in hits if h['doc_language'] == 'mixed')}、"
          f"en {sum(1 for h in hits if h['doc_language'] == 'en')}、"
          f"ja {sum(1 for h in hits if h['doc_language'] == 'ja')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
