#!/usr/bin/env python3
"""「提到」vs「规定」：把 §22 那个机制**量化**，看值不值得为它改规则（**只测，不改规则**）。

背景：§22 记录了一个机制性缺陷——正文通道是"哪句话里出现了某个词"，不是"这句话在说什么"。
一句**讨论**禁令措辞的话（例如"本文件写的是「绝不」，而规则里只有「禁止」家族"）会被算成一条禁令。
§13 已量过同一成因的另一面（`Do not …` 通式的残余假阳性 ≈3%），但没有量过"提到"这一类。

本脚本用的反事实（与 §22 的最小对照同法）：**把"提到型"句子里的禁令词就地抹掉（等长占位）**，
再重跑 `analyze_text`：

    抹之前有 boundaries、抹之后没有  ⇒ 这个文件的 boundaries **完全靠这种句子撑着**（候选假阳性）
    抹之前有、抹之后还有            ⇒ 标签另有真凭据（说明这类句子是"多出来的一条"，不影响标签）

"提到型"的判据（保守，宁可漏判）：
  (a) 句子里有**谈论措辞本身**的词：这个词/二字/这类词/措辞/字眼/词表/所谓/叫作/写的是/引号…
      或英文 the word / the phrase / wording / terminology / quoted / literally；
  (b) 禁令词本身被**引号括起来当词用**（「绝不」/「禁止」/`do not`，引号内只有这个词）。

对照组：凡是有人工盲判的文件（英文留出集 55 / in-sample 100 / 中文留出集 50）都拿来判
"抹掉的是真标签还是假标签"——**这才是决定要不要改规则的证据**。

用法：`.venv/bin/python work/audit/mention_vs_rule.py`
"""

from __future__ import annotations

import json
import pathlib
import re

from agent_charters.extract import analyze_text

ROOT = pathlib.Path(__file__).resolve().parents[2]

# 与 taxonomy.py 的边界家族对齐（只取正文通道那几族里"会被元讨论引用"的词）
CJK_TOKENS = ["绝对禁止", "严格禁止", "绝不", "严禁", "禁止", "不允许", "请勿", "切勿",
              "不得不", "不得"]
EN_TOKENS = ["never commit", "do not commit", "must not", "must never", "do not", "don't",
             "never"]
TOKEN_RE = re.compile("|".join(re.escape(t) for t in CJK_TOKENS + EN_TOKENS), re.I)

CUES = re.compile(
    r"这个词|这二字|这两个字|二字|这类词|这种说法|这个说法|措辞|字眼|词表|所谓|叫作|叫做|"
    r"写的是|引号|"
    r"the word|the phrase|wording|terminology|quoted?|literally|spelling",
    re.I,
)
# --loose 用：故意放宽到"任何像在讨论规则/措辞的句子"，宁可错杀——用来检验结论稳不稳
LOOSE_EXTRA = re.compile(
    r"而不是|而非|区别于|规则|词|判定|分类|命中|例如|比如|即|也就是说|"
    r"rather than|instead of|rule|classif|label|e\.g\.|for example",
    re.I,
)
# 引号内**只有禁令词本身**（≤6 字 / ≤20 ASCII）＝在谈论这个词，不是在划线
QUOTED_WORD = re.compile(
    r"[「『“\"'`]\s*(" + "|".join(re.escape(t) for t in CJK_TOKENS + EN_TOKENS) +
    r")\s*[」』”\"'`]",
    re.I,
)
FILLER = {True: "\u3007", False: "x"}  # 〇 / x：等长替换，不改变结构


def scrub(text: str, loose: bool = False) -> tuple[str, int]:
    """把「提到型」句子里的禁令词抹成等长占位；返回（新文本, 抹掉的词数, 受影响的文件行数）。"""
    out, n = [], 0
    for line in text.splitlines(keepends=True):
        cue = CUES.search(line) or QUOTED_WORD.search(line)
        if loose and not cue:
            cue = LOOSE_EXTRA.search(line)
        if TOKEN_RE.search(line) and cue:
            def repl(m: re.Match) -> str:
                return FILLER[m.group(0).isascii()] * len(m.group(0))
            line, k = TOKEN_RE.subn(repl, line)
            n += k
        out.append(line)
    return "".join(out), n


def calls(paths: list[str]) -> dict[str, set[str]]:
    got: dict[str, set[str]] = {}
    for p in paths:
        f = ROOT / p
        if not f.exists():
            continue
        got.update({k: set(v.get("call", []))
                    for k, v in json.loads(f.read_text(encoding="utf-8"))["files"].items()})
    return got


def groups() -> dict[str, tuple[list[tuple[str, pathlib.Path]], dict[str, set[str]]]]:
    full = [(json.loads(l)["repo_full_name"], ROOT / json.loads(l)["local_file"])
            for l in (ROOT / "data/raw/full_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    cn = [(json.loads(l)["repo_full_name"],
           ROOT / "data/raw/cn" / (json.loads(l)["repo_full_name"].replace("/", "__") + ".md"))
          for l in (ROOT / "data/raw/cn_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    return {
        "v0.5 全库": (full, {}),
        "v0.6 中文": (cn, {}),
        "英文留出集 55": (full, calls([f"work/audit/v0.5-holdout-calls-a{i}.json" for i in range(1, 8)])),
        "in-sample 100": (full, calls([f"work/audit/v0.4-blind-calls-a{i}.json" for i in range(1, 14)]
                                      + [f"work/audit/v0.4-blind-calls-d{i}.json" for i in range(1, 4)])),
        "中文留出集 50": (cn, calls([f"work/audit/v0.6-cn-calls-a{i}.json" for i in range(1, 11)])),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--loose", action="store_true",
                    help="放宽「提到型」判据（连 规则/词/而不是/for example 这类也算）——用来检验结论稳不稳")
    args = ap.parse_args()
    print("「提到型」判据" + ("（**loose 放宽版**）" if args.loose else "") +
          "：谈论措辞本身的词（这个词/二字/措辞/词表/the word/…）或 引号内只有禁令词本身\n")
    for name, (files, human) in groups().items():
        target = [(r, p) for r, p in files if not human or r in human]
        dep, keep, scrubbed_words, n_b, touched = [], 0, 0, 0, 0
        for repo, path in target:
            text = path.read_text(encoding="utf-8", errors="replace")
            before = set(analyze_text(text)["categories"])
            if "boundaries" not in before:
                continue
            n_b += 1
            fixed, k = scrub(text, args.loose)
            scrubbed_words += k
            touched += 1 if k else 0
            after = set(analyze_text(fixed)["categories"])
            if "boundaries" in after:
                keep += 1
            else:
                dep.append(repo)
        print(f"=== {name}（测 {len(target)} 份；有 boundaries 的 {n_b} 份；"
              f"含「提到型」句子的文件 {touched} 份、抹掉禁令词 {scrubbed_words} 处）===")
        print(f"  抹掉「提到型」句子后**掉 boundaries** 的：{len(dep)} 份"
              f"（另有 {keep} 份标签另有真凭据、不受影响）")
        if human and dep:
            tp = [r for r in dep if "boundaries" in human[r]]
            fp = [r for r in dep if "boundaries" not in human[r]]
            border = [r for r in dep if "boundaries" in human[r]]
            print(f"  对照人工盲判：人判**也有** boundaries 的 {len(tp)} 份（抹掉＝丢真标签）／"
                  f"人判**没有**的 {len(fp)} 份（抹掉＝消掉假阳性）")
            for r in (fp + tp)[:10]:
                tag = "人判无（假阳性）" if r not in tp else "人判有（真标签）"
                print(f"      - {r:<55} {tag}")
        for r in dep[:6]:
            print(f"      · {r}")
        print()

    own = ROOT / "AGENTS.md"
    text = own.read_text(encoding="utf-8")
    fixed, k = scrub(text, args.loose)
    print("=== 本仓库自己的 AGENTS.md（§22 的原始案例）===")
    print(f"  抹掉 {k} 处「提到型」禁令词后：boundaries "
          f"{'仍在（另有真凭据）' if 'boundaries' in analyze_text(fixed)['categories'] else '消失'}"
          f"（现状 {'在' if 'boundaries' in analyze_text(text)['categories'] else '不在'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
