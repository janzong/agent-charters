"""章程正文里的「指针」——把规则放在别的文件里，自己只留一行转引。

**为什么需要它**（`LIMITATIONS.md` §25、`work/audit/pointer-census.md`）：同一批仓库里，
根级 `AGENTS.md` / `CLAUDE.md` 有 **111/791 份是符号链接**、**75 份是"纯指针"**（中位 **11B**）。
`modelcontextprotocol/inspector` 的 `CLAUDE.md` 全文就是 `@./AGENTS.md`；
`Significant-Gravitas/AutoGPT` 是 `@AGENTS.md`。

而 `compare` 与 GitHub Action 是**单文件判定**：对着这 13 个字节，它们会报
**0/9**——用户看到的是"你的章程很空"，**这是错误结论**，也正是"跑一次就不再用"的那类体验。
实测这些指针里 **73/75 的目标就在同一棵树里**，本地解析路径即可跟随，不需要任何网络请求。

**与 `is_pointer`（`taxonomy.py`）的区别——两个东西，不要混**：

| | `is_pointer` | 本模块 |
|---|---|---|
| 用途 | **统计口径**：这份文件有没有正文，要不要算进覆盖率分母 | **工具行为**：这份文件是不是在指路，要不要跟过去 |
| 作用范围 | 数据集标签（已发布资产） | CLI / Action 的这一次运行 |
| 认不认 `@路径` | **不认**（正则只有 `see/read/refer to X.md`） | 认（`@导入` 是实测里的主导形态，68/103） |
| 改动的代价 | 动标签 ⇒ 按 D18 要重切数据集、发新版本 | 零，不动任何数据与规则集 |

所以这里**刻意不改** `is_pointer`，也不把两者合并：统计口径的改动要人裁定（D32），
工具行为可以自己迭代。

**什么时候算"指针"**（三个条件同时满足，宁可漏判也不要劫持有内容的文件）：
  ①**薄**：去掉链接/路径/装饰后 <400B（复用 `content_bytes`）；
  ②**确实在指**：出现 `@路径.md`、`Read|See|详见 X.md`、本地 Markdown 链接或作者自陈；
  ③**自己没有规则**：不含 `do not / must / never / 可执行命令` 这类（复用 `OWN_RULES_PAT` 反证闸）。
第三个条件是关键：`BerriAI/litellm` 的 `AGENTS.md` 首行是 `Read @CLAUDE.md for coding guidelines`，
**后面还写着自己的规则**——那种文件当然不能"跟随"，它本身就是内容。

**跟随是显式的**：调用方必须把结果**说出来**（"这份是指针，规则在 X"），
不能静默替换——否则用户会把目标的九类覆盖当成这个文件写的，那是另一种错误结论。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .taxonomy import OWN_RULES_PAT, content_bytes

POINTER_VERSION = "pointer_v0.1"

# 最多跟几跳。链条（A→B→C）理论上可以有，实测里没见过；设上限是为了防环。
MAX_HOPS = 3

# ① `@路径.md` —— Claude Code 的 import 语法（也见于 Cursor/Copilot 配置）。
#    整行优先（这才是 import），宽松匹配用于"Read @CLAUDE.md"这种行内写法。
_AT_LINE = re.compile(r"(?m)^\s*(?:[-*]\s*)?@([\w./\-]+\.(?:md|mdc))\s*$")
_AT_ANY = re.compile(r"(?<![\w`])@([\w./\-]+\.(?:md|mdc))")
# ② 祈使转引
_READ_REF = re.compile(
    r"(?i)(?:\b(?:read|see|refer to|consult|follow)\b|详见|参见|参阅|先读|必读)"
    r"[^\n]{0,40}?([\w./\-]+\.(?:md|mdc))")
# ③ 本地 Markdown 链接（外链不算）
_LOCAL_LINK = re.compile(
    r"\]\(\s*(?!https?://|mailto:)([\w./\-]+\.(?:md|mdc))(?:\#[\w\-]+)?\s*\)")
# ④ 作者自陈"本文件只是路由"
_SELF_DECLARE = re.compile(
    r"(?i)no instructions in this file|all instructions are in|contains? routing rules"
    r"|本文不写规则|全部规则在|this file is a pointer")


@dataclass(frozen=True)
class Pointer:
    """一份"指向别处"的章程。`target` 在 `resolved=False` 时可能不存在。"""

    source: Path
    raw: str          # 原文里写的那个路径（照抄，别归一化——报错时要让人能搜到）
    target: Path      # 按 `source` 所在目录解析后的路径
    resolved: bool    # 目标文件是否真的在


def _normalize(raw: str) -> str:
    p = raw.strip().strip("`[]<>\"'").lstrip("/")
    while p.startswith("./"):
        p = p[2:]
    return p


def targets(text: str) -> list[str]:
    """按出现顺序列出被指向的路径（归一化、去重、保序）。"""
    out: list[str] = []
    for rx in (_AT_LINE, _AT_ANY, _READ_REF, _LOCAL_LINK):
        for m in rx.finditer(text):
            t = _normalize(m.group(1))
            if t and t not in out:
                out.append(t)
    return out


def is_pointer_body(text: str) -> bool:
    """是不是"薄 + 在指路 + 自己没有规则"——三个条件都过才算。"""
    if content_bytes(text) >= 400:
        return False
    if OWN_RULES_PAT.search(text):
        return False
    return bool(_AT_LINE.search(text) or _AT_ANY.search(text) or _READ_REF.search(text)
                or _LOCAL_LINK.search(text) or _SELF_DECLARE.search(text))


def inspect(path: str | Path) -> Pointer | None:
    """看一份文件是不是指针；是的话，顺带把它指向哪个（能解析到的第一个）目标算出来。

    返回 `None` 表示"这不是指针"——绝大多数文件都走这条路，不该有任何开销之外的副作用。
    `resolved=False` 表示"像指针，但目标不在"（调用方要如实说"没跟到"，不要假装跟了）。

    跟随是**单跳优先、逐跳验证**：先试第一个能落地的目标；都落不了地就报第一个候选。
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not is_pointer_body(text):
        return None
    cands = targets(text)
    if not cands:
        return None

    seen = {p.resolve()}
    cur_raw, cur = cands[0], p
    for _ in range(MAX_HOPS):
        nxt = None
        for t in cands:
            cand = (cur.parent / t)
            if cand.is_file():
                nxt = (t, cand)
                break
        if nxt is None:
            return Pointer(source=p, raw=cur_raw, target=cur.parent / cur_raw,
                           resolved=False)
        cur_raw, cur = nxt[0], nxt[1].resolve()
        if cur in seen:                       # 环：如实报"跟不下去"
            return Pointer(source=p, raw=cur_raw, target=cur, resolved=True)
        seen.add(cur)
        try:
            ntext = cur.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return Pointer(source=p, raw=cur_raw, target=cur, resolved=True)
        if not is_pointer_body(ntext):        # 跟到了有正文的那一份 ⇒ 收工
            return Pointer(source=p, raw=cur_raw, target=cur, resolved=True)
        cands = targets(ntext) or cands
    return Pointer(source=p, raw=cur_raw, target=cur, resolved=True)


def resolve(path: str | Path) -> tuple[Path, Pointer | None]:
    """把"该判哪个文件"算出来——三个入口（`compare` / `brief` / Action）共用这一处。

    返回 `(要分析的文件, 指针信息或 None)`：普通文件就是它自己；指针且目标在，
    就是目标文件。**调用方有义务把 `Pointer` 说出来**（"这份是指针，规则在 X"）——
    静默替换会让用户把目标的九类覆盖当成这个文件写的，那是另一种错误结论。
    """
    ptr = inspect(path)
    if ptr is not None and ptr.resolved:
        return ptr.target, ptr
    return Path(path), ptr
