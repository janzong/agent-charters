#!/usr/bin/env python3
"""「扩展文件类型」的可行性实测：**只读探测**，不改任何数据。

第三优先里挂着一条 ⏳「扩展文件类型（CLAUDE.md / .cursorrules / copilot-instructions.md）」。
要不要做，取决于**增量有多大**、以及**和现有 558 份有多少重叠**——这轮先把它量出来。

方法：用 GitHub trees API（`GET /repos/{repo}/git/trees/HEAD?recursive=1`）把**语料库那 558 个仓库**
的文件列表拉一遍（一次调用拿全树，比逐文件探测省 6 倍请求），在本地数这些"同类章程文件"：

    CLAUDE.md                ｜ .cursorrules（旧）/ .cursor/rules/*.mdc（新）
    .github/copilot-instructions.md ｜ GEMINI.md ｜ .windsurfrules / .windsurf/rules
    .aider* ｜ .clinerules ｜ .rules

产物：`data/cache/trees/*.json`（gitignore 里，重跑不再打 API）+ 一张概览表。
用法：`.venv/bin/python work/audit/filetype_probe.py [--limit N]`
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/cache/trees"

KINDS = {
    "CLAUDE.md": re.compile(r"(^|/)CLAUDE\.md$", re.I),
    ".cursorrules": re.compile(r"(^|/)\.cursorrules$"),
    ".cursor/rules": re.compile(r"(^|/)\.cursor/rules/.+\.mdc$"),
    "copilot-instructions": re.compile(r"(^|/)\.github/copilot-instructions\.md$", re.I),
    "GEMINI.md": re.compile(r"(^|/)GEMINI\.md$", re.I),
    "windsurf": re.compile(r"(^|/)(\.windsurf/rules/.+|\.windsurfrules)$"),
    "aider": re.compile(r"(^|/)\.aider(\.conf\.yml|rules\.md|\.model\.settings\.yml)?$"),
    ".clinerules": re.compile(r"(^|/)\.clinerules(/|$)"),
    ".rules": re.compile(r"(^|/)\.rules$"),
    "AGENTS.md": re.compile(r"(^|/)AGENTS\.md$", re.I),
}


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


def repos() -> list[str]:
    out = []
    for line in (ROOT / "data/raw/full_manifest.jsonl").read_text(encoding="utf-8").splitlines():
        out.append(json.loads(line)["repo_full_name"])
    return sorted(set(out))


def tree(repo: str, tok: str) -> dict | None:
    """拉一棵树并存缓存。**失败不写缓存**（否则重跑会把失败当成"已做过"跳过——
    第一版就是踩了这个坑：204 个仓库因为 `IncompleteRead` 被永久记账）。"""
    f = CACHE / (repo.replace("/", "__") + ".json")
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    url = f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
        "User-Agent": "agent-charters-probe/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            return d
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):          # 限流：等一下再试
                time.sleep(3 * (attempt + 1))
                continue
            f.write_text(json.dumps({"_error": f"HTTP {e.code}"}, ensure_ascii=False),
                         encoding="utf-8")
            return None                        # 404/409 这类是**真的没有**，可以记账
        except Exception:                      # noqa: BLE001 —— 网络类异常，重试
            time.sleep(1 + attempt)
    return None                                # 三次都失败：不写缓存，下次再试


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-fetch", action="store_true",
                    help="只用缓存算（网络抖的时候先出数；缺的仓库会被计成「未取到」）")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)

    todo, cached_hit = repos(), CACHE.glob("*.json")
    todo = todo if not args.limit else todo[:args.limit]
    print(f"仓库 {len(todo)} 个（缓存已有 {len(list(cached_hit))} 份）")

    if not args.no_fetch:
        tok = token()
        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(lambda r: tree(r, tok), todo))

    # 每仓库：各类命中的 (路径, blob sha, mode)。mode 120000 = 符号链接。
    hits: dict[str, list[str]] = {k: [] for k in KINDS}
    dup: dict[str, int] = {k: 0 for k in KINDS}          # 与同仓 AGENTS.md **逐字节相同**
    link: dict[str, int] = {k: 0 for k in KINDS}         # 符号链接
    files_of: dict[str, int] = {k: 0 for k in KINDS}
    dataset = {json.loads(l)["repo_full_name"]: json.loads(l)["file_sha"]
               for l in (ROOT / "data/processed" / "agent_charters_v0.5.jsonl")
               .read_text(encoding="utf-8").splitlines()}
    errors, per_repo = [], {}
    for r in todo:
        cf_ = CACHE / (r.replace("/", "__") + ".json")
        if not cf_.exists():
            errors.append((r, "未取到（网络/未跑）"))
            continue
        d = json.loads(cf_.read_text(encoding="utf-8"))
        if d.get("_error"):
            errors.append((r, d["_error"]))
            continue
        blobs = [n for n in d.get("tree", []) if n.get("type") == "blob"]
        got = []
        for k, pat in KINDS.items():
            mine = [n for n in blobs if pat.search(n["path"])]
            if not mine:
                continue
            got.append(k)
            hits[k].append(r)
            files_of[k] += len(mine)
            link[k] += sum(1 for n in mine if n.get("mode") == "120000")
            dup[k] += sum(1 for n in mine if n.get("sha") and n["sha"] == dataset.get(r))
        per_repo[r] = (got, len(blobs), bool(d.get("truncated")))

    n = len(per_repo)
    print(f"\n=== 成功探测 {n} 个仓库（失败 {len(errors)} 个，失败的不写缓存、下次重试）===")
    print(f"  {'文件类型':<24}{'有它的仓库':>10}{'占比':>8}{'文件数':>8}{'符号链接':>10}{'与AGENTS.md逐字节相同':>22}")
    for k in sorted(hits, key=lambda x: -len(hits[x])):
        print(f"  {k:<24}{len(hits[k]):>10}{len(hits[k]) * 100 / (n or 1):>7.1f}%"
              f"{files_of[k]:>8}{link[k]:>10}{dup[k]:>22}")
    multi = {r: got for r, (got, _, _) in per_repo.items() if len(got) > 1}
    only_other = {r: got for r, got in multi.items() if "AGENTS.md" not in got}
    print(f"\n  含 **≥2 类**（多文件、可做跨文件一致性检测）的仓库：{len(multi)} 个")
    print(f"  其中**没有 AGENTS.md**（纯增量、不在现有语料里）：{len(only_other)} 个")
    trunc = [r for r, (_, _, t) in per_repo.items() if t]
    if trunc:
        print(f"  ⚠ 树被 GitHub 截断（超大仓）{len(trunc)} 个，计数可能偏低：{trunc[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
