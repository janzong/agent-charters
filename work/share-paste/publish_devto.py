#!/usr/bin/env python3
"""把 dev.to 文章发出去（或更新已有文章）。

- API key：优先环境变量 DEVTO_API_KEY，其次 ~/.devto_api_key（文件首行）。
  key 只从这两处读，**不写进任何文件、不打印**。
- 默认发**草稿**（published=false）；加 --live 才会真的上线。
- 用法：
    python3 work/share-paste/publish_devto.py --dry-run           # 只看会发什么，不联网
    python3 work/share-paste/publish_devto.py                     # 发草稿，打印 id/url
    python3 work/share-paste/publish_devto.py --live              # 直接发布
    python3 work/share-paste/publish_devto.py --update 1234567     # 更新已有文章
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://dev.to/api/articles"
HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "devto-article.md"
KEY_ENV = "DEVTO_API_KEY"
KEY_FILE = pathlib.Path.home() / ".devto_api_key"


def read_key() -> str | None:
    import os

    key = os.environ.get(KEY_ENV, "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        txt = KEY_FILE.read_text(encoding="utf-8").strip()
        if txt:
            return txt
    return None


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise SystemExit("缺少 front matter（文件要以 --- 开头的 title/tags 块）")
    _, fm, body = text.split("---", 2)
    meta: dict = {}
    for line in fm.strip().splitlines():
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]
    if len(tags) > 4:
        raise SystemExit(f"dev.to 最多 4 个 tag，现在是 {len(tags)} 个：{tags}")
    payload = {
        "title": meta.get("title", "").strip(),
        "body_markdown": body.lstrip("\n"),
        "tags": tags,
        "published": False,
    }
    if not payload["title"]:
        raise SystemExit("front matter 里缺 title")
    if meta.get("canonical_url"):
        payload["canonical_url"] = meta["canonical_url"]
    if meta.get("description"):
        payload["description"] = meta["description"]
    return meta, payload


def call(url: str, key: str, payload: dict, method: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps({"article": payload}).encode("utf-8"),
        headers={"api-key": key, "Content-Type": "application/json",
                 "Accept": "application/vnd.forem.api-v1+json",
                 "User-Agent": "agent-charters-publisher/1.0"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=pathlib.Path, default=DEFAULT_FILE)
    ap.add_argument("--dry-run", action="store_true", help="只打印会发的正文信息，不联网")
    ap.add_argument("--live", action="store_true", help="发布（不加则只建草稿）")
    ap.add_argument("--update", metavar="ARTICLE_ID", help="更新已有文章而不是新建")
    args = ap.parse_args()

    meta, payload = parse_front_matter(args.file.read_text(encoding="utf-8"))
    if args.live:
        payload["published"] = True

    if args.dry_run:
        print(f"file        : {args.file}")
        print(f"title       : {payload['title']}")
        print(f"tags        : {payload['tags']}")
        print(f"published   : {payload['published']}")
        print(f"body bytes  : {len(payload['body_markdown'])}")
        print(f"body lines  : {payload['body_markdown'].count(chr(10)) + 1}")
        print(f"key present : {bool(read_key())}")
        return 0

    key = read_key()
    if not key:
        print(f"没有 API key：设环境变量 {KEY_ENV}，或把 key 写进 {KEY_FILE}（只读不打印）。",
              file=sys.stderr)
        return 2

    url = f"{API}/{args.update}" if args.update else API
    method = "PUT" if args.update else "POST"
    try:
        art = call(url, key, payload, method)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return 1
    print(f"id={art.get('id')}  url={art.get('url')}  published={art.get('published')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
