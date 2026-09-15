#!/usr/bin/env python3
"""「章程是指针」这件事有多少、长什么样、能不能跟随（**只读探测**）。

背景（`LIMITATIONS.md` §25）：同一仓库的 `AGENTS.md` / `CLAUDE.md` 里，38–49% 的成对**有一份是空壳/指针**。
而 `compare` 与 GitHub Action 是**单文件判定**——对着一个 13B 的 `@./AGENTS.md` 会报 0/9。
本脚本只回答三个问题，不实现任何东西：

  1. **有多少**：482 棵缓存树里，根级 `AGENTS.md` / `CLAUDE.md` 各有多少是"指针形态"
     （符号链接 / 体积极小 / 正文只是转引）；
  2. **长什么样**：指针的**语法**分布——`@path` 导入（Claude Code 的 import 语法，现有
     `POINTER_PAT` 完全不认）、`Read|See <file>.md`、本地 Markdown 链接、作者自陈、裸符号链接；
  3. **能不能跟随**：被指向的目标**在同仓库树里存不存在**（存不存在决定"跟随"是可行还是只能转述）。

用法：`.venv/bin/python work/audit/pointer_probe.py [--fetch-limit 200] [--no-fetch]`
（正文走 blob API，按 sha 缓存在 `data/cache/blobs/`，重跑不重复下载；两个缓存目录都在 .gitignore 内）
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
TREES = ROOT / "data/cache/trees"
BLOBS = ROOT / "data/cache/blobs"

NAMES = ("AGENTS.md", "CLAUDE.md")

# ① Claude Code / 本工具都不认的导入语法：整行 `@路径.md`（可带缩进与前缀文字）
AT_IMPORT = re.compile(r"(?m)^\s*(?:[-*]\s*)?@[\w./\-]+\.(?:md|mdc)\s*$")
AT_ANY = re.compile(r"(?<![\w`])@([\w./\-]+\.(?:md|mdc))")
# ② 祈使转引：Read / See / Refer to / 详见 / 参见 + 一个 .md 文件名
READ_REF = re.compile(
    r"(?i)(?:\b(?:read|see|refer to|consult|follow)\b|详见|参见|见)\s*[`\[]?\s*"
    r"([\w./\-]+\.(?:md|mdc))")
# ③ 本地 Markdown 链接（排除 http(s):// 外链）
LOCAL_LINK = re.compile(r"\]\(\s*(?!https?://|mailto:)([\w./\-]+\.(?:md|mdc))(?:\#[\w\-]+)?\s*\)")
# ④ 作者自陈"本文件只是路由"
SELF_DECLARE = re.compile(
    r"(?i)no instructions in this file|all instructions are in|contains? routing rules"
    r"|本文不写规则|全部规则在|this file is a pointer|see the .{0,20}\.md")

# 目标路径归一化用：把 `./a/b.md`、`a/b.md`、`/a/b.md` 统一成裸相对路径
def norm(path: str) -> str:
    p = path.strip().strip("`[]<>\"'").lstrip("/")
    while p.startswith("./"):
        p = p[2:]
    return p


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


def fetch(repo: str, sha: str, tok: str) -> str | None:
    BLOBS.mkdir(parents=True, exist_ok=True)
    f = BLOBS / f"{sha}.txt"
    if f.exists():
        return f.read_text(encoding="utf-8", errors="replace")
    url = f"https://api.github.com/repos/{repo}/git/blobs/{sha}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.raw",
        "User-Agent": "agent-charters-probe/1.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8", errors="replace")
            f.write_text(data, encoding="utf-8", errors="replace")
            return data
        except Exception:  # noqa: BLE001
            continue
    return None


def load_trees() -> list[tuple[str, dict]]:
    out = []
    for f in sorted(TREES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("_error"):
            continue
        out.append((f.stem.replace("__", "/"), d))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-limit", type=int, default=200,
                    help="最多下多少份正文（默认 200，够覆盖全部 <2000B 的非链接文件）")
    ap.add_argument("--no-fetch", action="store_true", help="只用已缓存正文，不联网")
    args = ap.parse_args()

    trees = load_trees()
    rows: list[tuple[str, str, dict, list[str]]] = []
    n_files = n_symlink = 0
    small: list[tuple[str, str, dict, list[str]]] = []
    for repo, d in trees:
        paths = {x["path"] for x in d.get("tree", []) if x.get("type") == "blob"}
        blobs = {x["path"]: x for x in d.get("tree", []) if x.get("type") == "blob"}
        for name in NAMES:
            x = blobs.get(name)
            if not x:
                continue
            n_files += 1
            if x.get("mode") == "120000":
                n_symlink += 1
                rows.append((repo, name, x, ["符号链接"]))
            elif x.get("size", 0) < 2000:
                small.append((repo, name, x, sorted(paths)))

    print(f"仓库树 {len(trees)} 棵｜根级 `AGENTS.md`/`CLAUDE.md` 共 **{n_files}** 份"
          f"｜其中**符号链接 {n_symlink}** 份｜非链接且 <2000B **{len(small)}** 份\n")

    todo = small[: args.fetch_limit]
    tok = "" if args.no_fetch else token()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        texts = list(ex.map(
            lambda t: fetch(t[0], t[2]["sha"], tok) if not args.no_fetch else None, todo))
    if args.fetch_limit < len(small):
        print(f"⚠ 只下了前 {args.fetch_limit} 份正文（--fetch-limit 可调大）\n")

    from agent_charters.extract import analyze_text
    from agent_charters.taxonomy import (OWN_RULES_PAT, POINTER_PAT,
                                         POINTER_SEMANTIC)

    kinds: dict[str, int] = {}
    followable = unfollowable = 0
    zero_cat = 0
    # "纯指针"＝薄（去链接/路径后 <400B）**且**有指针语法**且**没有自己的规则/命令
    # （复用 `is_pointer` 的反证闸口径）。这一栏才是"跟随"要救的对象。
    pure = 0
    pure_zero = 0
    pure_follow = 0
    pure_unseen = 0
    pure_sizes: list[int] = []
    pure_examples: list[str] = []
    examples: dict[str, list[str]] = {}
    for (repo, name, x, paths), text in zip(todo, texts):
        if text is None:
            continue
        tags = []
        targets: list[str] = []
        for m in AT_ANY.finditer(text):
            tags.append("@导入")
            targets.append(m.group(1))
        for m in READ_REF.finditer(text):
            tags.append("Read/See")
            targets.append(m.group(1))
        for m in LOCAL_LINK.finditer(text):
            tags.append("本地链接")
            targets.append(m.group(1))
        if SELF_DECLARE.search(text):
            tags.append("自陈")
        # 有没有"实质正文"：去链接去路径后还剩下多少字节
        from agent_charters.taxonomy import content_bytes
        thick = content_bytes(text)
        if not tags:
            kinds["无指针语法（短但自足）"] = kinds.get("无指针语法（短但自足）", 0) + 1
            continue
        key = "+".join(sorted(set(tags)))
        kinds[key] = kinds.get(key, 0) + 1
        ex = examples.setdefault(key, [])
        if len(ex) < 2:
            ex.append(f"{repo}/{name} ({x.get('size')}B, 正文 {thick}B)")
        ok = [norm(t) for t in targets]
        found = [t for t in ok if t in paths]
        base = {p.rsplit("/", 1)[0] for p in paths}
        found += [t for t in ok if t not in paths and (name + "/" + t) in paths]
        if found:
            followable += 1
        else:
            unfollowable += 1
        cats = analyze_text(text)["categories"]
        if not cats:
            zero_cat += 1
        if thick < 400 and not OWN_RULES_PAT.search(text):
            pure += 1
            if not cats:
                pure_zero += 1
            if found:
                pure_follow += 1
            pure_sizes.append(x.get("size", 0))
            # "现有工具看不见的指针"：`POINTER_PAT`（see/read X.md）与语义门都没命中
            # ⇒ `is_pointer` 也判不出来，用户拿到的是 0/9 而不是"这是指针"。
            if not (POINTER_PAT.search(text) or POINTER_SEMANTIC.search(text)):
                pure_unseen += 1
            if len(pure_examples) < 8:
                pure_examples.append(
                    f"{repo}/{name} ({x.get('size')}B, 正文 {thick}B, "
                    f"标签 {len(cats)}/9, 目标 {'在树里' if found else '找不到'})")

    print("=== 语法分布（非链接、<2000B、有正文的那些）===")
    for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {v:>4}  {k}")
        for e in examples.get(k, []):
            print(f"        e.g. {e}")
    print(f"\n=== 能不能跟随 ===\n  目标在**同一棵仓库树**里找得到：**{followable}** 份"
          f"｜找不到：**{unfollowable}** 份")
    print(f"=== 当前 `compare` 会怎么答 ===\n  这些小文件里，九类标签为 **0/9** 的有 **{zero_cat}** 份"
          f"（＝用户看到的是「你这章程很空」）")
    print(f"\n=== 「纯指针」（薄 + 有指针语法 + 无自己的规则，＝跟随要救的对象）===")
    sizes = sorted(pure_sizes)
    med = sizes[len(sizes) // 2] if sizes else 0
    tiny = sum(1 for v in sizes if v <= 100)
    print(f"  共 **{pure}** 份（占非链接小文件 {pure * 100 // max(len(todo), 1)}%）"
          f"｜其中九类 **0/9** 的 **{pure_zero}** 份"
          f"｜目标**能在树里找到**的 **{pure_follow}** 份")
    print(f"  体积：中位 **{med}B**、≤100B 的 **{tiny}** 份（最小 {sizes[0] if sizes else 0}B、"
          f"最大 {sizes[-1] if sizes else 0}B）")
    print(f"  而**现有 `is_pointer` 判据（`POINTER_PAT` / 语义门）看不见的**有 **{pure_unseen}** 份"
          f" ⇒ 这些用户拿到的是 0/9，而不是「这是指针」")
    for e in pure_examples:
        print(f"        {e}")

    print("\n=== 符号链接的落点（前 12 个）===")
    for i, (repo, name, x, _) in enumerate(r for r in rows if r[3] == ["符号链接"]):
        if i >= 12:
            break
        print(f"  {repo:<52} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
