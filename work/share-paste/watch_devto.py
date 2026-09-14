#!/usr/bin/env python3
"""盯 dev.to：文章阅读/反应/评论，**只在出现新评论时出声**。

为什么是评论：文章我能自动发，评论我发不了（`POST /api/comments` 在真实站上不存在，
见 SHARE.md §5.5）——所以评论是唯一"需要人动手、漏了就浪费"的信号。

- key：环境变量 DEVTO_API_KEY → 其次 ~/.devto_api_key（两处都**不打印**）
- 状态：~/.local/state/devto-watch.json（记已见过的评论 id 与上次的阅读/反应数）
- 用法：
    python3 watch_devto.py                    # 人看：表格 + 新评论全文
    python3 watch_devto.py --changed-only     # 给 timer 用：没新评论就完全静默（退出码 0 / 10）
    python3 watch_devto.py --notify-hermes    # 有新评论时发一次 Hermes 收件箱
    python3 watch_devto.py --json             # 机器可读
- 首跑只建立基线，不把历史评论当"新"，不通知。
"""
from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://dev.to/api"
KEY_ENV = "DEVTO_API_KEY"
KEY_FILE = pathlib.Path.home() / ".devto_api_key"
STATE = pathlib.Path.home() / ".local" / "state" / "devto-watch.json"
LOG = pathlib.Path.home() / ".local" / "state" / "devto-watch.log"
NOTIFY = pathlib.Path.home() / "plugins" / "fleet-ops" / "scripts" / "notify-hermes.sh"
UA = "agent-charters-watcher/1.0"
EXIT_NEW = 10


def read_key() -> str:
    key = os.environ.get(KEY_ENV, "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        txt = KEY_FILE.read_text(encoding="utf-8").strip()
        if txt:
            return txt
    raise SystemExit(f"没有 API key：设 {KEY_ENV}，或写进 {KEY_FILE}（只读不打印）")


def get(url: str, key: str):
    req = urllib.request.Request(url, headers={
        "api-key": key, "Accept": "application/vnd.forem.api-v1+json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def text_of(c: dict) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", c.get("body_html") or "")).split())


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"articles": {}, "comments": {}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(STATE)


def collect(key: str) -> tuple[list[dict], dict[str, list[dict]]]:
    arts = [a for a in get(f"{API}/articles/me/all?per_page=100", key) if a.get("published")]
    by_article: dict[str, list[dict]] = {}
    for a in arts:
        try:
            cs = get(f"{API}/comments?a_id={a['id']}", key)
        except urllib.error.HTTPError:
            cs = []
        flat = []

        def walk(items):
            for c in items:
                flat.append(c)
                walk(c.get("children") or [])

        walk(cs)
        by_article[str(a["id"])] = flat
    return arts, by_article


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed-only", action="store_true", help="没有新评论就完全不输出（供 timer 用）")
    ap.add_argument("--notify-hermes", action="store_true", help="有新评论时发一次 Hermes 收件箱")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-state", action="store_true", help="不读不写状态（调试用）")
    args = ap.parse_args()

    key = read_key()
    state = {"articles": {}, "comments": {}} if args.no_state else load_state()
    first_run = not state.get("comments") and not state.get("articles")
    arts, by_article = collect(key)

    new_comments: list[dict] = []
    lines: list[str] = []
    for a in arts:
        aid = str(a["id"])
        seen = set(state["comments"].get(aid, []))
        ids = [c.get("id_code") for c in by_article.get(aid, [])]
        for c in by_article.get(aid, []):
            # 首跑只建立基线：历史评论不算"新"，更不能触发通知
            if not first_run and c.get("id_code") not in seen:
                new_comments.append({
                    "article_id": aid, "article_title": a.get("title"), "article_url": a.get("url"),
                    "id_code": c.get("id_code"),
                    "author": (c.get("user") or {}).get("username"),
                    "created_at": c.get("created_at"),
                    "text": text_of(c),
                })
        prev = state["articles"].get(aid, {})
        views, react, coms = a.get("page_views_count"), a.get("public_reactions_count"), a.get("comments_count")

        def delta(now, before):
            if before is None or now is None:
                return ""
            return f" (+{now - before})" if now > before else ""

        lines.append(f"[{aid}] {str(a.get('title'))[:60]}")
        lines.append(f"        阅读 {views}{delta(views, prev.get('views'))}"
                     f" ｜ 反应 {react}{delta(react, prev.get('reactions'))}"
                     f" ｜ 评论 {coms}{delta(coms, prev.get('comments'))}")
        if not first_run:
            state["comments"][aid] = ids
        state["articles"][aid] = {"views": views, "reactions": react, "comments": coms,
                                  "title": a.get("title"), "url": a.get("url")}
    if first_run:
        for a in arts:
            state["comments"][str(a["id"])] = [c.get("id_code") for c in by_article.get(str(a["id"]), [])]
    if not args.no_state:
        save_state(state)

    if args.notify_hermes and new_comments:
        body = [f"dev.to 出现 {len(new_comments)} 条新评论（需要人贴回复；评论 API 只读，Codex 发不了）。"]
        for c in new_comments:
            body.append(f"\n· 文章《{c['article_title']}》\n  {c['article_url']}\n"
                        f"  作者 {c['author']} @ {c['created_at']}（{len(c['text'])} 字符）\n  {c['text'][:600]}")
        body.append("\n请求：把这条评论转给用户，并让 Codex 起草回复供用户粘贴"
                    "（评论全文已落 ~/.local/state/devto-watch.log，通知里只有前 600 字符）。"
                    "约束：不要自动发评论 —— dev.to 评论 API 只读（`POST /api/comments` 在真实站上不存在）。")
        cmd = os.environ.get("DEVTO_WATCH_NOTIFY_CMD", str(NOTIFY))
        try:
            out = subprocess.run([cmd, "\n".join(body)], capture_output=True, text=True, timeout=300)
            if out.returncode != 0:
                print(f"⚠️ 通知失败 rc={out.returncode}: {out.stderr.strip()[:200]}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 通知异常: {type(e).__name__}: {e}", file=sys.stderr)

    if new_comments:
        try:
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a", encoding="utf-8") as f:
                for c in new_comments:
                    f.write(f"\n===== {c['created_at']} | {c['author']} | 文章 {c['article_id']} =====\n"
                            f"{c['text']}\n")
        except OSError:
            pass

    if args.json:
        print(json.dumps({"articles": state["articles"], "new_comments": new_comments},
                         ensure_ascii=False, indent=2))
    elif new_comments:
        print(f"🔔 新评论 {len(new_comments)} 条\n")
        for c in new_comments:
            print(f"--- {c['author']} @ {c['created_at']}（{len(c['text'])} 字符）")
            print(f"    文章：{str(c['article_title'])[:70]}")
            print(f"    {c['text']}\n")
    elif not args.changed_only:
        print("（无新评论）")
    if not args.changed_only and not args.json:
        print("当前读数")
        for line in lines:
            print("  " + line)
        if first_run:
            print("  （首跑：已建立基线，历史评论不计为新）")
    return EXIT_NEW if new_comments else 0


if __name__ == "__main__":
    raise SystemExit(main())
