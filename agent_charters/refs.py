"""外部引用检测 —— 章程是"入口"还是"全集"。

为什么单独一个模块：这不是九类里的哪一类，而是"知识放在哪里"。
规则集（taxonomy）按内容分类，量不出"我指向别处"这件事。

口径来源与代价（work/external_ref_scan.py，507 份实测）：
  · 第一版用「文本里出现任意 .md 路径」→ 命中 87%，抽验后判定为假阳性机器
    （README 列表、PR 模板、日志文件名全被算进去）。
  · 收紧为「祈使转引」+「载体专名」后才可用：
    49% 的章程存在祈使转引，15% 指向知识/记忆载体或规则目录。

因此本模块只认两种东西：
  1. **祈使转引**——"read / see / 详见 X.md"，即明确把 agent 指去读另一个文件；
  2. **载体专名**——memories/、MEMORY.md、pitfalls、.cursor/rules、copilot-instructions…
除此之外的任何 .md 提及都不算。
"""

from __future__ import annotations

import re
from pathlib import Path

REFSET_VERSION = "refs_v0.1"

# 1. 祈使转引
IMPERATIVE_EN = re.compile(
    r"(?i)\b(?:read|consult|refer to|check|see|follow)\b"
    r"[^\n]{0,50}?[\w\-./]*[\w\-]+\.(?:md|mdc|txt)\b")
IMPERATIVE_ZH = re.compile(
    r"(?:先读|必读|必须先|请读|阅读|参见|详见|参阅|参考[^\n]{0,4}?\.md)"
    r"[^\n]{0,30}?[\w\-./]*[\w\-]+\.md")

# 2. 载体专名
KNOWLEDGE_STORE = re.compile(
    r"(?i)memories/|MEMORY\.md|pitfalls|lessons\.md|lessons-learned"
    r"|知识库|记忆文件|踩坑记录|经验记录|DECISIONS\.md|ADR\b")
RULES_DIR = re.compile(
    r"(?i)\.cursor/rules|\.github/instructions|copilot-instructions"
    r"|(?<!\w)rules/[\w\-]+\.md")

# 3. 指向的具体路径（用于断链检查）
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_PATH = re.compile(r"`([\w\-./]+\.(?:md|mdc|txt)|[\w\-./]+/)`")


def find_refs(text: str) -> dict:
    """返回一份章程的外部引用情况。"""
    imperative = bool(IMPERATIVE_EN.search(text) or IMPERATIVE_ZH.search(text))
    store = bool(KNOWLEDGE_STORE.search(text))
    rules = bool(RULES_DIR.search(text))

    targets: list[str] = []
    for m in MD_LINK.finditer(text):
        targets.append(m.group(1))
    targets += [m.group(1) for m in BACKTICK_PATH.finditer(text)]

    cleaned: list[str] = []
    for t in targets:
        if t.startswith(("http://", "https://", "mailto:", "#", "//")):
            continue
        t = t.split("#", 1)[0].strip()
        if not t or t in cleaned:
            continue
        cleaned.append(t)

    return {
        "imperative": imperative,
        "knowledge_store": store,
        "rules_dir": rules,
        "targets": cleaned,
        "routes_outward": imperative or store or rules,
        "hard": store or rules,
        "refset_version": REFSET_VERSION,
    }


SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".venv", "__pycache__", "vendor"}


def _index(base: Path, max_depth: int = 4) -> set[str]:
    """浅扫仓库，收下所有文件名与相对目录名，供"找不到但存在"的判定用。"""
    names: set[str] = set()
    stack = [(base, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > max_depth:
            continue
        try:
            for child in cur.iterdir():
                if child.name in SKIP_DIRS or child.name == ".git":
                    continue          # 注意：`.github` 等隐藏目录要收，知识库常在那里
                names.add(child.name)
                if child.is_dir():
                    stack.append((child, depth + 1))
        except (PermissionError, OSError):
            continue
    return names


def resolve_targets(refs: dict, base_dir: str | Path) -> list[tuple[str, str]]:
    """把每个指向的路径判成三态之一。

    这是本模块最有用的部分：指错方向比不指更糟——agent 会照着不存在的文件找。

    三态：`exists` 精确存在 ｜ `by_name` 精确路径不对但同名文件在仓库里
    （多为相对某个目录写短名，如 `pitfalls.md` 实际在 `.github/memories/`）｜
    `missing` 全仓库找不到同名文件。
    """
    base = Path(base_dir)
    if not base.exists():
        return []
    index = _index(base)
    out: list[tuple[str, str]] = []
    for t in refs["targets"]:
        if t.startswith("/") or ".." in Path(t).parts:
            continue                      # 仓库外的不判
        if (base / t).exists():
            out.append((t, "exists"))
        elif Path(t).name in index:
            out.append((t, "by_name"))
        else:
            out.append((t, "missing"))
    return out
