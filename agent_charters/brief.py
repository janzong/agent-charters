"""brief —— 写/生成章程前的检查清单，以及可直接粘贴的生成提示词。

为什么是"清单"而不是"模板"：

  1. 对照实验（work/auto_vs_human.md，n=11）发现，自动生成的覆盖面由**提示词的形状**
     决定，而不是由仓库里有什么决定：提示词不点名"协作流程"，11/11 份都不写；
     点名后 3/3 立刻写出。所以缺的不是知识，是**提问**。
  2. 语料库的类别分布就是"该问哪些问题"的答案，而且是**算出来的、不是编出来的**。
  3. `gotchas` 单独给子清单：120 条人工标注显示 58% 读得出来、34% 根本不是坑、
     只有 8% 需要经历或外部世界的证据（work/gotcha_origin.md）。

本模块不含任何硬编码的比例——基准率一律从随包语料库实时计算。
"""

from pathlib import Path

from .extract import category_coverage, substantive
from .refs import find_refs, resolve_targets
from .taxonomy import CATEGORIES

# 每个类别对应"作者/生成器该问自己什么"。中文用于清单，英文用于粘贴的提示词。
ASK: dict[str, tuple[str, str]] = {
    "build_test": (
        "装、构建、跑测试、跑 CI 各是什么命令？给可复制的准确命令，不要写“运行测试”。",
        "Exact commands to install, build, test, and lint — the ones CI runs. "
        "Give copy-pasteable commands, not \"run the tests\"."),
    "workflow": (
        "提交信息什么格式？分支怎么开？PR 谁来评审？发布怎么做？"
        "（实测：不点名就没人写，11/11 份自动生成的章程都跳过了这一项）",
        "Commit message format, branch strategy, PR review rules, release steps. "
        "(Measured: this is the slot generators skip unless the prompt names it.)"),
    "boundaries": (
        "绝对不能做什么？删文件、改 lockfile、动 main、提交密钥——每条都写上为什么。",
        "Hard prohibitions: what must never be done, and why. "
        "Name the tempting-but-forbidden action explicitly."),
    "structure": (
        "目录/模块怎么划分？新代码该放哪里？关键文件是哪几个？",
        "How the repo is laid out, where new code belongs, which files are load-bearing."),
    "style": (
        "命名、格式、注释、错误处理的约定？最好直接指向配置文件。",
        "Naming, formatting, comments, error handling — point at the config files "
        "that enforce them."),
    "environment": (
        "工具链版本、必需的环境变量、本地开发的先决条件、性能/平台限制？",
        "Toolchain versions, required env vars, local-dev prerequisites, "
        "platform constraints."),
    "agent_meta": (
        "对 AI 自身的要求：语气、什么时候先问、哪些操作必须先征得同意、"
        "哪些信息不要外传。",
        "Rules about the agent itself: tone, when to ask first, "
        "which actions require explicit approval, what must not leave the machine."),
    "overview": (
        "一句话：这是什么、给谁用、不做什么。",
        "One paragraph: what this is, who it is for, and what it deliberately is not."),
    "gotchas": (
        "只写三类：①仓库之外的事实（操作系统/上游/第三方行为）②出过的事故与原因 "
        "③文档与实际不一致之处。",
        "Pitfalls that are NOT derivable from the code: OS/upstream/third-party "
        "behaviour, past incidents and their causes, and places where the docs "
        "disagree with the code."),
}

# gotchas 的"别写什么"——来自 120 条人工标注（work/gotcha_origin.md）
GOTCHA_ANTI = (
    "别写“记得装依赖”“别提交 .env”这类通用建议：语料库里 34% 的坑其实不是坑。",
    "Do not write generic advice (\"remember to install dependencies\", "
    "\"don't commit .env\"): 34% of the pitfalls in the corpus are not pitfalls.")

# 外部引用不是一个"类别"，而是"知识放在哪里"。规则集尚未覆盖它，
# 所以这两个基准率**不是**从随包语料库实时算的，出处是 work/external_ref_scan.py
# （507 份实测）。等 v0.2 把该信号并入数据集后，改为实时计算（STATE.md D28）。
REFS_BASE = {
    "zh": "语料库实测：49% 的章程会转引外部文件，15% 指向知识库或规则目录"
          "（来源 work/external_ref_scan.py，非实时计算）",
    "en": "Measured on the corpus: 49% route to another file, 15% point at a "
          "knowledge store or rules directory (source: work/external_ref_scan.py, "
          "not computed live)",
}

REFS_ASK = (
    "知识放在哪？如果坑/模式写在别的文件里，章程要明确指过去——"
    "并且要检查指过去的路径真的存在。",
    "Where does the knowledge live? If pitfalls or patterns are kept in other "
    "files, say so explicitly - and make sure every path you point at exists.",
)

# 实验得出的生成侧要点
GENERATOR_RULES = [
    ("提示词必须点名每一个槽位", "未点名的槽位会被系统性跳过（workflow 0/11 → 点名后 3/3）"),
    ("要求“没有证据就明说，不要猜”", "否则会编出不存在的命令"),
    ("生成后立刻核对", "用 agent-charters compare 把结果与语料库基线对比"),
    ("把人能补的那部分补上", "58% 的坑读代码可得，剩下 8% 只能问人（见 work/gotcha_origin.md）"),
    ("指向别处就要保证指得对", "指错方向比不指更糟——agent 会照着不存在的文件找；"
     "用 agent-charters refs 检查断链"),
]

OUTPUT_LANG = {"en": 1, "zh": 0}


def _bar(pct: int, width: int = 20) -> str:
    filled = int(round(pct / 100 * width))
    return "█" * filled + "·" * (width - filled)


def base_rates(df=None) -> dict[str, int]:
    from .extract import load_corpus
    return category_coverage(substantive(df if df is not None else load_corpus()))


def render(files: list[str], lang: str = "en", df=None) -> str:
    """打印清单（可选对比文件）并输出可粘贴的提示词。"""
    cov = base_rates(df)
    out: list[str] = []

    mine: set[str] = set()
    if files:
        from .extract import analyze_file
        out.append("你提供文件的缺口")
        out.append("-" * 58)
        for f in files:
            rec = analyze_file(f)
            mine |= set(rec["categories"])
            missing = [c for c in CATEGORIES if c not in rec["categories"]]
            out.append(f"  {f}: {len(rec['categories'])}/{len(CATEGORIES)} 类，"
                       f"缺 {', '.join(missing) if missing else '（无）'}")
        out.append("")

    head = "写章程的检查清单" + ("（按语料库覆盖率排序）" if not files else "（✗ = 你没有的）")
    out += [head, "-" * 58]
    for c, pct in sorted(cov.items(), key=lambda kv: -kv[1]):
        mark = "" if not files else ("   " if c in mine else " ✗ ")
        out.append(f"  {mark}{c:<13}{pct:>3}%  {_bar(pct)}")
    out.append("")

    out += ["每一项该问什么", "-" * 58]
    for c, pct in sorted(cov.items(), key=lambda kv: -kv[1]):
        out.append(f"  【{c} · 语料库 {pct}%】")
        out.append(f"     {ASK[c][OUTPUT_LANG[lang]]}")
        if c == "gotchas":
            out.append(f"     ⚠ {GOTCHA_ANTI[OUTPUT_LANG[lang]]}")
    out.append("")

    out += ["生成侧要点（来自 n=11 对照实验）", "-" * 58]
    for title, why in GENERATOR_RULES:
        out.append(f"  · {title} —— {why}")
    out.append("")

    out += ["外部引用（不在九类之内，规则集尚未覆盖）", "-" * 58]
    out.append(f"  {REFS_BASE[lang]}")
    out.append(f"  该问：{REFS_ASK[OUTPUT_LANG[lang]]}")
    if files:
        for f in files:
            rec = find_refs(Path(f).read_text(encoding="utf-8", errors="replace"))
            if not rec["routes_outward"]:
                out.append(f"  {f}: 未发现外部引用（章程是自足的）")
                continue
            kind = "知识库/规则目录" if rec["hard"] else "祈使转引"
            res = resolve_targets(rec, Path(f).parent)
            bad = [t for t, st in res if st == "missing"]
            soft = [t for t, st in res if st == "by_name"]
            line = f"  {f}: {kind}，指向 {len(rec['targets'])} 个路径"
            if bad:
                line += f"  ⚠ {len(bad)} 个找不到：{', '.join(bad[:4])}"
            if soft:
                line += f"  （{len(soft)} 个只在同名位置找到）"
            unv = [p for p, st in res if st == "unverified"]
            if unv:
                line += f"  （{len(unv)} 个无法核验：目录不是仓库根）"
            out.append(line)
    out.append("")

    targets = [c for c in CATEGORIES if (not files) or c not in mine]
    out += ["可直接粘贴的提示词", "-" * 58]
    if not targets:
        out.append("  九类全覆盖，没有要补的槽位。")
        out.append("  若要换一份仓库重写，直接跑：agent-charters brief")
    else:
        out += _indent(generator_prompt(targets, lang, files))
    return "\n".join(out)


def _indent(text: str) -> list[str]:
    return ["  " + line if line.strip() else "" for line in text.splitlines()]


def generator_prompt(categories: list[str] | None = None, lang: str = "en",
                     files: list[str] | None = None) -> str:
    """生成一份"该问什么"的提示词。categories 为 None 表示全部九类。"""
    cats = list(categories or CATEGORIES)
    if lang == "en":
        lines = [
            "Analyze this repository and write an AGENTS.md at its root.",
            "Cover every one of the following slots explicitly:",
        ]
        for c in cats:
            lines.append(f"- {c}: {ASK[c][1]}")
        lines += [
            "If a slot has no evidence in the repository, write that explicitly "
            "instead of guessing.",
            "For pitfalls, do not write generic advice: "
            "34% of the pitfalls in a 507-file corpus of AGENTS.md files are not "
            "pitfalls at all.",
            "If the knowledge lives in other files (pitfalls list, rules directory, "
            "decision log), say so explicitly and make sure every path you point at "
            "actually exists.",
            "Base everything on what is actually in the repository - never invent a "
            "command that is not discoverable.",
        ]
    else:
        lines = [
            "分析这个仓库，在根目录写一份 AGENTS.md。",
            "以下每一项都必须显式写到：",
        ]
        for c in cats:
            lines.append(f"- {c}：{ASK[c][0]}")
        lines += [
            "如果某一项在仓库里找不到依据，就明写“仓库里没有证据”，不要猜。",
            "写坑的时候不要写通用建议：507 份章程语料库里 34% 的“坑”其实不是坑。",
            "如果知识放在别的文件里（坑点清单、规则目录、决策记录），要明确指过去，"
            "并确保每个路径都真实存在。",
            "一切以仓库里真实存在的东西为准，不要编造找不到的命令。",
        ]
    if files:
        lines.append("")
        lines.append("(Existing file under review: " + ", ".join(files) + ")"
                     if lang == "en" else
                     "（正在审查的现有文件：" + "、".join(files) + "）")
    return "\n".join(lines)
