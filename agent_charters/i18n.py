"""CLI 输出文案（en / zh）+ 语言探测。

为什么要它：对外渠道以 dev.to（英文）为主，但 CLI 输出原来是硬编码中文——
英文读者从文章点进来、照抄命令，看到的是中文，等于把人挡在门口。

默认语言按环境变量判断（`LC_ALL` / `LC_MESSAGES` / `LANG` 里含 `zh` → 中文，
其余含未设置 → 英文——对外读者默认英文），每个命令都能用 `--lang en|zh` 覆盖。

**刻意的例外**：`brief` 的 `--lang` 管的是**喂给模型的提示词语言**，默认 en
（喂给模型最稳），所以它的默认值不是 None 而是「提示词 en + 周边文案跟 locale」。
见 `brief.render(lang=..., ui_lang=...)` 与 `cli.cmd_brief`。
"""
from __future__ import annotations

import os

LANGS = ("en", "zh")

T: dict[str, dict[str, str]] = {
    # ---- 顶层 ----
    "cli.desc": {
        "en": "A structured corpus of the written rules people give AI agents",
        "zh": "人写给 AI 智能体的书面规约语料库",
    },
    "cli.data_help": {
        "en": "custom corpus file: .jsonl/.jsonl.gz (stdlib) or .parquet (needs the "
              "[parquet] extra); defaults to the bundled {ds}",
        "zh": "自定义语料库路径：.jsonl/.jsonl.gz（标准库可读）或 .parquet（需 [parquet] "
              "附加依赖）；默认用随包的 {ds}",
    },
    "cli.bad_corpus": {
        "en": "cannot read the corpus: {msg}",
        "zh": "读不了语料库：{msg}",
    },
    "cli.lang_help": {
        "en": "output language (default: auto from LANG — zh* → Chinese, otherwise English)",
        "zh": "输出语言（默认按 LANG 自动判断：zh* → 中文，其余 → 英文）",
    },
    "cli.no_such_file": {
        "en": "no such file: {files}",
        "zh": "文件不存在：{files}",
    },
    "cmd.stats": {"en": "Global distribution", "zh": "全局分布"},
    "cmd.brief": {
        "en": "Checklist before writing a charter + a paste-ready generation prompt",
        "zh": "写章程前的检查清单 + 可直接粘贴的生成提示词",
    },
    "cmd.brief.files": {
        "en": "optional: existing charter files; the checklist marks what you are missing",
        "zh": "可选：已有的章程文件，清单会标出你缺了哪些",
    },
    "cmd.brief.lang": {
        "en": "prompt language (default en - most reliable when fed to a model; "
              "setting it also switches the surrounding text)",
        "zh": "提示词语言（默认 en：喂给模型最稳；指定后周边文案也用它）",
    },
    "cmd.compare": {
        "en": "Compare your charter against the corpus",
        "zh": "把你的章程与语料库对比",
    },
    "cmd.compare.files": {"en": "one or more charter files", "zh": "一个或多个章程文件"},
    "cmd.refs": {
        "en": "Show a charter's external references and dangling paths",
        "zh": "看章程的外部引用与断链",
    },
    "cmd.refs.files": {"en": "charter file paths", "zh": "章程文件路径"},
    "cmd.show": {"en": "Show real examples of one category", "zh": "看某类别的真实样本"},
    "cmd.show.limit": {"en": "how many to show", "zh": "展示多少份"},

    # ---- stats ----
    "stats.header": {
        "en": "corpus {ds}  |  collected {collected}  |  substantive {sub}  "
              "|  snapshot {snap}  |  {ruleset}\n",
        "zh": "语料库 {ds} ｜ 抓取 {collected} 份 ｜ 实质内容 {sub} 份 "
              "｜ 快照 {snap} ｜ {ruleset}\n",
    },
    "stats.coverage": {"en": "Category coverage (substantive files)",
                       "zh": "类别覆盖（实质文件）"},
    "stats.mode": {"en": "Content mode", "zh": "内容模式"},
    "stats.doclang": {"en": "Document language", "zh": "文档语言"},
    "stats.size": {"en": "Size", "zh": "体量"},
    "stats.bytes": {"en": "  median {med} B  |  mean {mean} B  |  max {mx} B",
                    "zh": "  中位数 {med} B ｜ 均值 {mean} B ｜ 最大 {mx} B"},
    "stats.labels": {"en": "  mean categories per file {avg:.1f}",
                     "zh": "  平均标签数 {avg:.1f}"},

    # ---- compare ----
    "cmp.baseline": {
        "en": "corpus baseline: {n} substantive files (snapshot {snap})\n",
        "zh": "语料库基线：{n} 份实质文件（快照 {snap}）\n",
    },
    "cmp.head": {"en": "{cat:<14}{corpus:>7}    your file",
                 "zh": "{cat:<14}{corpus:>7}    你的文件"},
    "cmp.category": {"en": "category", "zh": "类别"},
    "cmp.corpus": {"en": "corpus", "zh": "语料库"},
    "cmp.pointer": {"en": "pointer (no body text)", "zh": "pointer（无正文内容）"},
    "cmp.sections": {"en": "{n} sections", "zh": "{n} 章节"},
    "cmp.total": {"en": "coverage {mine}/{all} categories",
                  "zh": "合计覆盖 {mine}/{all} 类"},
    "cmp.absent": {"en": "Missing from yours, most common first:",
                   "zh": "你没有、但语料库写得最多的："},
    "cmp.cov_line": {"en": "  {c:<14} corpus coverage {pct:.1f}%",
                     "zh": "  {c:<14} 语料库覆盖率 {pct:.1f}%"},
    "cmp.full": {
        "en": "All nine categories covered - above the corpus mean of {avg:.1f}.",
        "zh": "九类全覆盖——超过语料库平均（{avg:.1f} 类）。",
    },
    "cmp.full_none": {
        "en": "All nine categories covered.",
        "zh": "九类全覆盖。",
    },

    # ---- show ----
    "show.none": {"en": "no file matched category {cat}",
                  "zh": "没有文件命中类别 {cat}"},
    "show.head": {"en": "category {cat}: {n} hits, showing the first {k}\n",
                  "zh": "类别 {cat}：{n} 份命中，展示前 {k} 份\n"},
    "show.raw": {"en": "\nfull text: https://github.com/<repo>/blob/HEAD/{path}",
                 "zh": "\n取原文：https://github.com/<repo>/blob/HEAD/{path}"},

    # ---- refs ----
    "refs.kind.store": {"en": "knowledge store / rules dir", "zh": "知识库/规则目录"},
    "refs.kind.imperative": {"en": "imperative pointer", "zh": "祈使转引"},
    "refs.kind.self": {"en": "self-contained", "zh": "自足"},
    "refs.type": {"en": "  kind: {kind}   points at {n} paths",
                  "zh": "  类型：{kind}   指向 {n} 个路径"},
    "refs.self": {"en": "  No outward references - this charter is self-contained.",
                  "zh": "  未发现外部引用——该章程是自足的。"},
    "refs.missing": {
        "en": "  ! {n} pointed-at paths not found - a wrong pointer is worse than none.",
        "zh": "  ⚠ {n} 个指向的路径找不到——指错方向比不指更糟。",
    },
    "refs.unverified": {
        "en": "  ({n} pointers could not be verified because the base dir is not a repo "
              "root - normal if the charter points at another project)",
        "zh": "  (基准目录不是仓库根，{n} 个指向无法核验——若章程指向的是别的项目，这是正常的)",
    },

    # ---- brief：表头与缺口行 ----
    "brief.gaps_head": {"en": "Gaps in the files you provided",
                        "zh": "你提供文件的缺口"},
    "brief.head_rates": {"en": "Charter checklist (sorted by corpus coverage)",
                         "zh": "写章程的检查清单（按语料库覆盖率排序）"},
    "brief.head_gap": {"en": "Charter checklist (\u2717 = missing from yours)",
                       "zh": "写章程的检查清单（\u2717 = 你没有的）"},
    "brief.gap_line": {"en": "  {f}: {n}/{all} categories, missing {missing}",
                       "zh": "  {f}: {n}/{all} 类，缺 {missing}"},
    "brief.none_word": {"en": "(none)", "zh": "（无）"},
    "brief.ask_head": {"en": "What to ask for in each slot", "zh": "每一项该问什么"},
    "brief.slot": {"en": "  [{c} - corpus {pct}%]", "zh": "  【{c} · 语料库 {pct}%】"},
    "brief.rules_head": {"en": "Generator notes (from an n=11 controlled run)",
                         "zh": "生成侧要点（来自 n=11 对照实验）"},
    "brief.refs_head": {"en": "External references (a structural signal, outside the nine categories)",
                        "zh": "外部引用（结构信号，不在九类之内）"},
    "brief.refs_ask": {"en": "  Ask: ", "zh": "  该问："},
    "brief.file_self": {"en": "  {f}: no outward references (self-contained)",
                        "zh": "  {f}: 未发现外部引用（章程是自足的）"},
    "brief.file_route": {"en": "  {f}: {kind}, pointing at {n} paths",
                         "zh": "  {f}: {kind}，指向 {n} 个路径"},
    "brief.file_missing": {"en": "  ! {n} not found: {list}", "zh": "  ⚠ {n} 个找不到：{list}"},
    "brief.file_byname": {"en": "  ({n} only found by name)", "zh": "  （{n} 个只在同名位置找到）"},
    "brief.file_unverified": {"en": "  ({n} unverifiable: the dir is not a repo root)",
                              "zh": "  （{n} 个无法核验：目录不是仓库根）"},
    "brief.rule_line": {"en": "  \u00b7 {title} - {why}", "zh": "  \u00b7 {title} \u2014\u2014 {why}"},
    "brief.prompt_head": {"en": "Paste-ready prompt", "zh": "可直接粘贴的提示词"},
    "brief.prompt_none": {"en": "  All nine categories covered - nothing to add.",
                          "zh": "  九类全覆盖，没有要补的槽位。"},
    "brief.prompt_other": {"en": "  To write a charter for another repo, just run: agent-charters brief",
                           "zh": "  若要换一份仓库重写，直接跑：agent-charters brief"},
    # brief：生成侧要点（下标 0=zh，1=en，沿用 brief.py 的 OUTPUT_LANG 约定）
    "brief.rule.name_slots": {
        "en": "Name every slot in the prompt|unnamed slots get skipped systematically "
              "(workflow 0/11 -> 3/3 once named)",
        "zh": "提示词必须点名每一个槽位|未点名的槽位会被系统性跳过（workflow 0/11 → 点名后 3/3）",
    },
    "brief.rule.no_guessing": {
        "en": "Ask for \"if there is no evidence, say so - do not guess\"|"
              "otherwise it invents commands that do not exist",
        "zh": "要求“没有证据就明说，不要猜”|否则会编出不存在的命令",
    },
    "brief.rule.verify_after": {
        "en": "Verify immediately after generating|run agent-charters compare against the corpus baseline",
        "zh": "生成后立刻核对|用 agent-charters compare 把结果与语料库基线对比",
    },
    "brief.rule.human_part": {
        "en": "Fill in the part only a person can|58% of the pitfalls are readable from the code, "
              "the remaining 8% have to be asked (see work/gotcha_origin.md)",
        "zh": "把人能补的那部分补上|58% 的坑读代码可得，剩下 8% 只能问人（见 work/gotcha_origin.md）",
    },
    "brief.rule.point_right": {
        "en": "If you point somewhere, make sure it is right|a wrong pointer is worse than none "
              "(the agent will read a file that does not exist) - check dangling paths with "
              "agent-charters refs",
        "zh": "指向别处就要保证指得对|指错方向比不指更糟——agent 会照着不存在的文件找；"
              "用 agent-charters refs 检查断链",
    },
}


def detect_lang(env: dict | None = None) -> str:
    """zh* → 中文，其余（含未设置）→ 英文。"""
    env = os.environ if env is None else env
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = (env.get(key) or "").lower()
        if val:
            return "zh" if val.startswith("zh") else "en"
    return "en"


def t(key: str, lang: str, **kw) -> str:
    entry = T[key]
    text = entry.get(lang) or entry["en"]
    return text.format(**kw) if kw else text
