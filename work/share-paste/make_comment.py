#!/usr/bin/env python3
"""从 SHARE.md 的 §7 更正话术章节生成"可直接粘贴"的评论纯文本。

用法:
  .venv/bin/python work/share-paste/make_comment.py \
      --section "### 7.2 开源中国" --out work/share-paste/oschina-comment-02.txt

与 make_paste.py 的区别：更正评论只有**一个** fenced 块，且原样粘贴即可（不剥标记、不重排）。
这样评论正文只有 SHARE.md 一处事实源，不会两边漂移。
"""
from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", default=str(ROOT / "SHARE.md"))
    ap.add_argument("--section", required=True, help='章节起始行前缀，如 "### 7.2 开源中国"')
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    text = pathlib.Path(a.share).read_text(encoding="utf-8")
    i = text.index(a.section)
    rest = text[i + len(a.section):]
    j = rest.index("\n### ") if "\n### " in rest else len(rest)
    body = rest[:j]
    blocks = re.findall(r"```[a-z]*\n(.*?)```", body, re.S)
    if len(blocks) != 1:
        raise SystemExit(f"该章节应有且仅有一个 fenced 块，实际 {len(blocks)}")
    out = pathlib.Path(a.out)
    out.write_text(blocks[0].strip() + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(blocks[0].strip())} 字符)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
