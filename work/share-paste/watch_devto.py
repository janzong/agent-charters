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
- **只通知别人的评论**：作者自己的回复不算（否则通知通道会为自己的回复白跑一轮）。
- 退出码：0 无事 ｜ 10 有新评论（systemd 单元要写 `SuccessExitStatus=10`，否则算失败）。
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


def logged_ids() -> set[str]:
    """日志里已经写过的评论 id_code（用于重试时的去重）。"""
    if not LOG.exists():
        return set()
    try:
        return set(re.findall(r"\| ([0-9A-Za-z]+) =====$", LOG.read_text(encoding="utf-8"), re.M))
    except OSError:
        return set()


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
        self_name = (a.get("user") or {}).get("username")
        for c in by_article.get(aid, []):
            # 首跑只建立基线：历史评论不算"新"，更不能触发通知
            if first_run or c.get("id_code") in seen:
                continue
            # 自己发的回复不算"需要人回"的评论：它会一路 ping 到 Hermes 收件箱，
            # 而那个通道要提醒的恰恰是"有人评论了、快去回"。
            # 2026-09-14 实测：两条自家回复触发了一次通知，通知链路白跑 3 分钟。
            if (c.get("user") or {}).get("username") == self_name:
                continue
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

    # 顺序很关键：①先落日志（durable）②再通知（可能要调 hermes，慢）③最后才推进 state。
    # 2026-09-14 踩过：通知卡在 hermes 上被 systemd 的 TimeoutStartSec 杀掉，
    # 而 state 在通知之前就写好了 —— 结果日志没有、通知没发、评论被静默吞掉（两条，
    # 隔了两个小时才被人发现）。任何一步被杀，下一轮都会重来一遍，最坏是重复通知，不是丢。
    if new_comments:
        # 日志按 id_code 去重：通知失败会整轮重试，重试不该把同一条评论写第二遍
        seen_in_log = logged_ids()
        fresh = [c for c in new_comments if c.get("id_code") not in seen_in_log]
        if fresh:
            try:
                LOG.parent.mkdir(parents=True, exist_ok=True)
                with LOG.open("a", encoding="utf-8") as f:
                    for c in fresh:
                        f.write(f"\n===== {c['created_at']} | {c['author']} "
                                f"| 文章 {c['article_id']} | {c['id_code']} =====\n{c['text']}\n")
            except OSError as e:
                print(f"⚠️ 日志写入失败（不影响通知）：{e}", file=sys.stderr)

    notify_ok = True
    if args.notify_hermes and new_comments:
        body = [f"dev.to 出现 {len(new_comments)} 条新评论（需要人贴回复；评论 API 只读，Codex 发不了）。"]
        for c in new_comments:
            body.append(f"\n· 文章《{c['article_title']}》\n  {c['article_url']}\n"
                        f"  作者 {c['author']} @ {c['created_at']}（{len(c['text'])} 字符）\n  {c['text'][:600]}")
        body.append("\n请求：把这条评论转给用户，并让 Codex 起草回复供用户粘贴"
                    "（评论全文已落 ~/.local/state/devto-watch.log，通知里只有前 600 字符）。"
                    "约束：不要自动发评论 —— dev.to 评论 API 只读（`POST /api/comments` 在真实站上不存在）。")
        cmd = os.environ.get("DEVTO_WATCH_NOTIFY_CMD", str(NOTIFY))
        # 必须比 notify-hermes.sh 自己的 `timeout 300` 大：让它自己超时并给出 rc，
        # 而不是被我们掐断（掐断会连 stderr 一起丢，排查时看不见原因）。
        try:
            out = subprocess.run([cmd, "\n".join(body)], capture_output=True, text=True, timeout=330)
            if out.returncode != 0:
                print(f"⚠️ 通知失败 rc={out.returncode}: {out.stderr.strip()[:200]}", file=sys.stderr)
                print("   （state 未推进，下一轮会重试；评论正文已落日志）", file=sys.stderr)
                notify_ok = False
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 通知异常: {type(e).__name__}: {e}", file=sys.stderr)
            print("   （state 未推进，下一轮会重试；评论正文已落日志）", file=sys.stderr)
            notify_ok = False

    # ③ 只有通知成功（或本来就不通知）才推进 state —— 否则下一轮重来
    if not args.no_state and notify_ok:
        save_state(state)
    elif not notify_ok:
        print("（本轮不算处理完成：state 保持原样，30 分钟后重试）", file=sys.stderr)

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
