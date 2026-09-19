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
- front matter 支持的字段：title / tags / published / canonical_url / description / **series**
  （`series` 是合集名，首次带它会自动建合集；后续更新**必须继续带**，否则合集会被摘掉）
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
    # series 必须每次都带上：dev.to 用 PUT 覆盖字段，漏掉会把已挂的合集摘掉
    if meta.get("series"):
        payload["series"] = meta["series"]
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


def current_published(article_id: str, key: str) -> bool:
    """读回文章当前的 published 状态（只为'不改状态地更新'用）。"""
    req = urllib.request.Request(
        f"{API}/me/all?per_page=1000",
        headers={"api-key": key, "Accept": "application/vnd.forem.api-v1+json",
                 "User-Agent": "agent-charters-publisher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        arts = json.load(r)
    for a in arts:
        if str(a.get("id")) == str(article_id):
            return bool(a.get("published"))
    raise SystemExit(f"在 /api/articles/me/all 里找不到 id={article_id}；"
                     f"要改状态请显式加 --live 或 --draft")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=pathlib.Path, default=DEFAULT_FILE)
    ap.add_argument("--dry-run", action="store_true", help="只打印会发的正文信息，不联网")
    ap.add_argument("--live", action="store_true", help="发布（不加则只建草稿）")
    ap.add_argument("--draft", action="store_true", help="明确打回草稿（下架）")
    ap.add_argument("--update", metavar="ARTICLE_ID", help="更新已有文章而不是新建")
    args = ap.parse_args()
    if args.live and args.draft:
        print("--live 和 --draft 互斥", file=sys.stderr)
        return 2

    meta, payload = parse_front_matter(args.file.read_text(encoding="utf-8"))

    if args.dry_run:
        print(f"file        : {args.file}")
        print(f"title       : {payload['title']}")
        print(f"tags        : {payload['tags']}")
        if args.update and not args.live and not args.draft:
            print("published   : (保持现状——要联网读回当前状态)")
        else:
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

    # 显式定状态：新建默认草稿；更新默认**保持现状**（别因为漏字段把线上文章打回草稿）
    if args.live:
        payload["published"] = True
    elif args.draft:
        payload["published"] = False
    elif args.update:
        payload["published"] = current_published(args.update, key)

    if args.live and not args.update:
        print("⚠️  没有 --update：这会**新建**一篇，而不是把已有草稿转正。\n"
              "    要把草稿转正请用：--update <草稿id> --live", file=sys.stderr)
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
