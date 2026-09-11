#!/usr/bin/env python
"""从工作表切出"盲判组"（默认前 10 份），只含题面，不含任何结论。

为什么要脚本：工作表会被反复重生成（改口径、补证据），手抄容易漂移。
盲判组必须与工作表**逐字一致**，否则人判的和我判的不是同一个题面。

用法：.venv/bin/python work/audit_blind.py [--n 10]
输出：work/audit/blind10.md
"""
from __future__ import annotations

import argparse
import pathlib
import re

WS = pathlib.Path("work/audit/v0.2-worksheet.md")
OUT = pathlib.Path("work/audit/blind10.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    text = WS.read_text(encoding="utf-8")
    start = text.index("\n## 主样本")
    end = text.index("\n## 中文补充样本")
    main_part = text[start:end]
    blocks = re.split(r"(?m)^(?=### \d+\. )", main_part)
    blocks = [b for b in blocks if b.startswith("### ")]
    picked = blocks[: a.n]

    L = [f"# 盲判组（前 {a.n} 份，主样本随机抽出的前 {a.n} 个）\n",
         f"> 只判这 {a.n} 份。判完再打开 `work/audit/v0.2-agent-verdicts.md` 对比。",
         "> 每条只需在文末写一句：`1. 准确` 或 `1. 漏标:坑,流程` 或 `1. 错标:风格`，可加几个字理由。\n",
         "> 抽查口径：**漏标**＝原文明明有这类内容却没打上；**错标**＝打上了但原文没有。\n",
         "> ⚠ **判「错标」请回到原文**（每条的完整原文路径在条目里）：「命中证据」列是**抽取器用的证据**，它本身可能是错的\n"
         "> （实测 `ci` 命中了 `De**ci**sions`）。证据列错 ≠ 类别错，两件事分开判。\n",
         "\n---\n"]
    for b in picked:
        L.append(b.rstrip("\n"))
    L.append("\n---\n\n## 我的判定（请填在这里）\n")
    for i in range(1, len(picked) + 1):
        L.append(f"{i}. ")
    pathlib.Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {a.out}：{len(picked)} 份")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
