"""agent-charters 命令行入口。

  agent-charters stats                     全局分布
  agent-charters brief [FILE...]           写章程前的检查清单 + 可粘贴的提示词
  agent-charters compare FILE [FILE...]    把你的章程与语料库对比
  agent-charters show CATEGORY             看某类别的真实样本
  agent-charters refs FILE [FILE...]       看章程的外部引用与断链

输出语言：默认按 `LANG`/`LC_ALL` 自动判断（`zh*` → 中文，其余 → 英文），
每个命令都能用 `--lang en|zh` 覆盖。文案表在 `i18n.py`。

`brief` 是唯一的例外：那里的 `--lang` 管的是**喂给模型的提示词**语言
（默认 en），不给 `--lang` 时周边清单仍跟 locale 走。
"""

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

from . import __version__
from . import pointers
from .extract import (CATEGORIES, DATASET_VERSION, analyze_file,
                      category_coverage, load_corpus, substantive)
from .i18n import detect_lang, t


def _bar(pct: float, width: int = 28) -> str:
    filled = int(round(pct / 100 * width))
    return "█" * filled + "·" * (width - filled)


def _lang(args: argparse.Namespace) -> str:
    return args.lang or detect_lang()


def _corpus(args: argparse.Namespace, lang: str):
    """读语料库；读不了要说人话而不是抛 traceback。

    最现实的失败是：指了一份 `.parquet` 但没装可选依赖——那条路径要 pandas
    （0.4.0 起不再默认安装），报错得直接告诉用户装什么。
    """
    try:
        return load_corpus(args.data) if args.data else load_corpus()
    except (OSError, RuntimeError) as exc:
        print(t("cli.bad_corpus", lang, msg=exc), file=sys.stderr)
        return None


def _missing_files(args: argparse.Namespace) -> list[str]:
    """不存在的输入文件要报清楚，不要抛 traceback。

    为什么值这几行：这个 CLI 现在被 GitHub Action 直接调用（`action.yml`），
    而 Action 里最常见的手误就是路径写错（`path: docs/AGENTS.md`）。
    抛 FileNotFoundError 的 traceback 会淹没整段日志，说人话的一行则一眼可见。
    """
    return [f for f in getattr(args, "files", []) if not Path(f).is_file()]


def cmd_stats(args: argparse.Namespace) -> int:
    lang = _lang(args)
    corpus = _corpus(args, lang)
    if corpus is None:
        return 2
    sub = substantive(corpus)
    ruleset = (corpus.first("ruleset_version")
               if "ruleset_version" in corpus.columns else "ruleset_v0.1")
    print(t("stats.header", lang, ds=DATASET_VERSION, collected=len(corpus),
            sub=len(sub), snap=corpus.first("retrieved_at"), ruleset=ruleset))

    print(t("stats.coverage", lang))
    print("-" * 58)
    cov = category_coverage(sub)
    for c, pct in sorted(cov.items(), key=lambda x: -x[1]):
        print(f"  {c:<13} {pct:>5.1f}%  {_bar(pct)}")

    print("\n" + t("stats.mode", lang))
    print("-" * 58)
    total = len(sub)
    for mode, cnt in Counter(sub["content_mode"]).most_common():
        print(f"  {mode:<13} {cnt:>4}  {cnt * 100 // total:>3}%")

    print("\n" + t("stats.doclang", lang))
    print("-" * 58)
    for doclang, cnt in Counter(sub["doc_language"]).most_common():
        print(f"  {doclang:<13} {cnt:>4}  {cnt * 100 // total:>3}%")

    print("\n" + t("stats.size", lang))
    print("-" * 58)
    b = sub["bytes"]
    print(t("stats.bytes", lang, med=int(statistics.median(b)),
            mean=int(sum(b) / len(b)), mx=int(max(b))))
    print(t("stats.labels", lang, avg=sum(map(len, sub["categories"])) / len(sub)))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    lang = _lang(args)
    if bad := _missing_files(args):
        print(t("cli.no_such_file", lang, files=", ".join(bad)), file=sys.stderr)
        return 2
    loaded = _corpus(args, lang)
    if loaded is None:
        return 2
    corpus = substantive(loaded)
    cov = category_coverage(corpus)
    n = len(corpus)

    snap = loaded.first("retrieved_at")    # 注：快照日是数据集级字段，取未过滤那份
    print(t("cmp.baseline", lang, n=n, snap=snap))
    print(t("cmp.head", lang, cat=t("cmp.category", lang), corpus=t("cmp.corpus", lang)))
    print("-" * 52)

    all_mine: set[str] = set()
    for path in args.files:
        # 「这份文件是指针」不等于「这份文件是空的」：40% 的根级章程里有一份只写一行转引
        # （`@AGENTS.md` 是 11 个字节）。不跟过去就会报 0/9，给用户"你这章程很空"的错误结论
        # ——所以跟随，**并且把这件事说出来**（静默替换会让人把目标的覆盖当成这个文件写的）。
        src, ptr = pointers.resolve(path)
        if ptr is not None and ptr.resolved:
            print(t("cmp.followed", lang, src=path, raw=ptr.raw, target=ptr.target.name))
        elif ptr is not None:
            print(t("cmp.follow_dangling", lang, src=path, raw=ptr.raw))
        rec = analyze_file(src)
        all_mine.update(rec["categories"])
        state = t("cmp.pointer", lang) if rec["is_pointer"] else f"{rec['bytes']}B"
        print(f"\n### {path}  [{state}, {rec['doc_language']}, "
              f"{t('cmp.sections', lang, n=rec['section_count'])}, {rec['content_mode']}]")
        for c in CATEGORIES:
            mark = "✓" if c in rec["categories"] else "—"
            cnt = rec["category_counts"].get(c, 0)
            extra = f" x{cnt}" if cnt else ""
            print(f"  {c:<14}{cov[c]:>6.1f}%    {mark}{extra}")

    print("\n" + "=" * 52)
    absent = [c for c in CATEGORIES if c not in all_mine]
    print(t("cmp.total", lang, mine=len(all_mine), all=len(CATEGORIES)))
    if absent:
        print("\n" + t("cmp.absent", lang))
        for pct, c in sorted(((cov[c], c) for c in absent), reverse=True):
            print(t("cmp.cov_line", lang, c=c, pct=pct))
    else:
        # 平均标签数实时算——写死过一次（4.4），与语料库实际值不符
        avg = sum(map(len, corpus["categories"])) / len(corpus)
        print(t("cmp.full", lang, avg=avg))
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    from .brief import render
    if bad := _missing_files(args):
        print(t("cli.no_such_file", detect_lang(), files=", ".join(bad)), file=sys.stderr)
        return 2
    corpus = _corpus(args, _lang(args)) if args.data else None
    if args.data and corpus is None:
        return 2
    # 两件事分开：提示词默认英文（喂模型最稳），周边文案默认跟 locale；
    # 显式给了 --lang 就两处都用它（用户既然点名了语言，别再猜）。
    print(render(args.files, lang=args.lang or "en", corpus=corpus,
                 ui_lang=args.lang or detect_lang()))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    lang = _lang(args)
    loaded = _corpus(args, lang)
    if loaded is None:
        return 2
    corpus = substantive(loaded)
    hit = corpus.where(lambda r: args.category in r["categories"])
    if not hit:
        print(t("show.none", lang, cat=args.category))
        return 1
    print(t("show.head", lang, cat=args.category, n=len(hit),
            k=min(args.limit, len(hit))))
    # 按该类别的章节数降序——最能代表这个类别的排在前面
    def hits_in(rec: dict) -> int:
        return int(rec["category_counts"].get(args.category, 0))

    for r in sorted(hit, key=hits_in, reverse=True)[:args.limit]:
        rl = r["repo_language"] if isinstance(r["repo_language"], str) else "-"
        lic = r["license"] if isinstance(r["license"], str) else "-"
        print(f"  {r['repo_full_name']:<40} {int(r['bytes']):>6}B  "
              f"{rl:<12} {lic:<14} {args.category} x{hits_in(r)}")
    print(t("show.raw", lang, path=corpus.first("file_path")))
    return 0


def cmd_refs(args: argparse.Namespace) -> int:
    """看章程的外部引用：是自足的，还是把知识指去了别处。"""
    from .refs import find_refs, resolve_targets
    lang = _lang(args)
    if bad := _missing_files(args):
        print(t("cli.no_such_file", lang, files=", ".join(bad)), file=sys.stderr)
        return 2
    for f in args.files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        rec = find_refs(text)
        kind = (t("refs.kind.store", lang) if rec["hard"]
                else t("refs.kind.imperative", lang) if rec["imperative"]
                else t("refs.kind.self", lang))
        print(f"\n{f}")
        print(t("refs.type", lang, kind=kind, n=len(rec["targets"])))
        if not rec["routes_outward"]:
            print(t("refs.self", lang))
            continue
        res = resolve_targets(rec, Path(f).parent)
        order = {"missing": 0, "unverified": 1, "by_name": 2, "exists": 3}
        for target, st in sorted(res, key=lambda x: order[x[1]]):
            mark = {"exists": "✓", "by_name": "~", "missing": "✗",
                    "unverified": "?"}[st]
            print(f"    {mark} {target}")
        bad = [x for x, st in res if st == "missing"]
        unv = [x for x, st in res if st == "unverified"]
        if bad:
            print(t("refs.missing", lang, n=len(bad)))
        if unv:
            print(t("refs.unverified", lang, n=len(unv)))
    return 0


def _add_lang(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--lang", choices=["en", "zh"], default=None,
                    help=t("cli.lang_help", detect_lang()))


def _add_data(sp: argparse.ArgumentParser) -> None:
    """`--data` 在子命令上再挂一遍。

    放在顶层时 argparse 只认 `agent-charters --data X stats`，而人几乎一定会写成
    `agent-charters stats --data X`——那就撞一句 "unrecognized arguments"，看不出该
    往哪挪。`SUPPRESS` 是关键：子命令没给时不写入命名空间，顶层的值才不会被 None 盖掉。
    """
    sp.add_argument("--data", default=argparse.SUPPRESS,
                    help=t("cli.data_help", detect_lang(), ds=DATASET_VERSION))


def main(argv: list[str] | None = None) -> int:
    ui = detect_lang()
    p = argparse.ArgumentParser(
        prog="agent-charters",
        description=f"{t('cli.desc', ui)}（{DATASET_VERSION} / {__version__}）"
                    if ui == "zh" else
                    f"{t('cli.desc', ui)} ({DATASET_VERSION} / {__version__})")
    p.add_argument("--version", action="version",
                   version=f"agent-charters {__version__} ｜ dataset {DATASET_VERSION}")
    p.add_argument("--data", help=t("cli.data_help", ui, ds=DATASET_VERSION))
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("stats", help=t("cmd.stats", ui))
    _add_lang(s1)
    _add_data(s1)
    s1.set_defaults(func=cmd_stats)

    sb = sub.add_parser("brief", help=t("cmd.brief", ui))
    sb.add_argument("files", nargs="*", help=t("cmd.brief.files", ui))
    sb.add_argument("--lang", choices=["en", "zh"], default=None,
                    help=t("cmd.brief.lang", ui))
    _add_data(sb)
    sb.set_defaults(func=cmd_brief)

    s2 = sub.add_parser("compare", help=t("cmd.compare", ui))
    s2.add_argument("files", nargs="+", help=t("cmd.compare.files", ui))
    _add_lang(s2)
    _add_data(s2)
    s2.set_defaults(func=cmd_compare)

    s4 = sub.add_parser("refs", help=t("cmd.refs", ui))
    s4.add_argument("files", nargs="+", help=t("cmd.refs.files", ui))
    _add_lang(s4)
    _add_data(s4)
    s4.set_defaults(func=cmd_refs)

    s3 = sub.add_parser("show", help=t("cmd.show", ui))
    s3.add_argument("category", choices=CATEGORIES)
    s3.add_argument("--limit", type=int, default=10, help=t("cmd.show.limit", ui))
    _add_lang(s3)
    _add_data(s3)
    s3.set_defaults(func=cmd_show)

    p.set_defaults(data=None)         # 两个位置都没给时的兜底（子命令用 SUPPRESS 不覆盖）
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
