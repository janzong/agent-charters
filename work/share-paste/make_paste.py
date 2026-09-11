#!/usr/bin/env python3
"""从 SHARE.md 的某个渠道章节生成"可直接粘贴"的纯文本。

用法：
  .venv/bin/python work/share-paste/make_paste.py \
      --section "## 3. 知乎" --header work/share-paste/header-zhihu.txt \
      --out work/share-paste/zhihu-article.txt

约定：该章节里必须有两个 fenced code block，顺序为 ①标题 ②正文。
生成时去掉 Markdown 标记（`##` / `**` / 反引号），并把源代码里为排版折开的硬换行
合并回整段——知乎/开源中国的编辑器不吃 Markdown，直接贴会到处断句。
"""
from __future__ import annotations

import argparse
import re
import pathlib

CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")
LIST = re.compile(r"^(- |\d+\. )")


def join(a: str, b: str) -> str:
    """把两片文本接起来，中英交界处补一个空格（中文排版惯例）。"""
    if not a:
        return b
    # 注意：re.search 返回 Match 对象，两个非空 Match 用 != 比较恒为真，必须取 bool
    if bool(CJK.search(a[-1])) != bool(CJK.search(b[0])):
        return a + " " + b
    if a.endswith("/") and b[0].isalnum():
        return a + " " + b
    return a + b


def reflow(raw: list[str]) -> str:
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        text = ""
        for piece in buf:
            piece = piece.strip()
            if not piece:
                continue
            text = join(text, piece)
        out.append(text)
        buf.clear()

    for line in raw:
        if line.strip() == "":
            flush()
            out.append("")
        elif line.startswith("    "):
            flush()
            out.append(line[4:].rstrip())
        elif line.startswith("## "):
            flush()
            out.append(line[3:].strip())
        elif LIST.match(line):
            flush()
            out.append(line.strip())
        elif line.startswith("  ") and out and LIST.match(out[-1]):
            out[-1] += line.strip()
        else:
            buf.append(line)
    flush()

    text = "\n".join(out)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text).replace("`", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="SHARE.md")
    ap.add_argument("--section", required=True, help='章节起始行，例如 "## 3. 知乎"')
    ap.add_argument("--header", required=True, help="含 {title} / {body} 占位的模板")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lines = pathlib.Path(args.source).read_text(encoding="utf-8").split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(args.section))
    except StopIteration:
        raise SystemExit(f"找不到章节：{args.section}")
    end = next(
        (i for i in range(start + 1, len(lines)) if re.match(r"^## \d", lines[i] or "")),
        len(lines),
    )
    fences = [i for i in range(start, end) if lines[i].strip() == "```"]
    if len(fences) < 4:
        raise SystemExit(f"章节里需要 2 个 fenced code block（实际 {len(fences) // 2} 个）：{args.section}")

    title = "\n".join(lines[fences[0] + 1 : fences[1]]).strip()
    body = reflow(lines[fences[2] + 1 : fences[3]])

    template = pathlib.Path(args.header).read_text(encoding="utf-8")
    text = template.replace("{title}", title).replace("{body}", body)
    pathlib.Path(args.out).write_text(text, encoding="utf-8")
    print(f"生成 {args.out}（标题 {len(title)} 字 / 正文 {len(body)} 字）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
