"""分类法 v0.1 —— 9 类定义与判定规则。

设计原则（详见 TAXONOMY.md）:
  1. 可判定：每条规则都能写成可执行的匹配表达式
  2. 基于内容，不基于文件名（AGENTS.md 这个文件名本身会污染 agent_meta 判断）
  3. 保守优先：宁可漏标，不做错标
"""

import re

VERSION = "taxonomy_v0.1"          # 九类的**定义**版本（类别是什么、边界在哪）
# 判定**规则**的版本。定义没变但规则变了（v0.1.1 加强模式通道 + 扩充关键词）时递增。
# 缺了它，两个数字不同的数据集会顶着同一个 taxonomy_version，无法机器校验可比性。
# v0.1.2（2026-09-11）两处规则修正，均来自"真用一次"的审计（work/usage_audit.md）：
#   U1 `is_pointer` 口径过宽：原先"提到 ≥2 个 .md 文件名 + 体积 <2000B"即判为转引用，
#      把有实质规则的小章程也剔出统计。11 份人工标注：真 4 / 半 2 / 误 5。
#   U2 `structure` 标题词表漏了"职责/归属"类标题：33 个这类章节里 9 个无标签。
# 与 refs.py 第一版那个 87% 假阳性同源——用"出现过文件名"代理"内容为空"。
# v0.1.3（2026-09-12）两处收紧，都由一次"回头看证据行"触发（`work/substring_audit.py`）：
#   (a) 标题通道由**子串**改为**词首**匹配：
#       `ci` 命中 De**ci**sions / Prin**ci**ples、`script` 命中 Type**Script**、
#       `build` 命中 allow**Build**s、`review` 命中 p**review**、`format` 命中 in**format**ion。
#   (b) `build_test` 标题词表删掉裸词 `make`，只留 `makefile` 与具体目标（`make build` 等）。
#       `make` 是普通英文动词：511 份里 12 份标题命中，逐条看 7 份是散文
#       （"Make changes" / "Where to make changes" / "make sure" / "makes variables global"），
#       只有 5 份真是构建工具——与 STRONG_PATTERNS 里"只认具体 make 目标"的既有口径对齐。
#   实测影响（511 份可用样本，`work/v0.2-to-v0.3-diff.md`）：18 份文件各掉 1 个类别标签
#   （build_test 11、agent_meta 2、environment 2、structure/style/workflow 各 1），**无一例新增**；
#   `build_test` 覆盖率 87.9% → 85.7%，其余类别 ≤0.5pp。11 份掉 build_test 的逐份复核过：
#   证据全是词中命中（principles / behavior / TypeScript / specification / description）。
#   注意：词首**前缀**命中是规则有意为之（`convention`→Conventions、`boundar`→Boundary、
#   `responsibilit`→Responsibility、`test`→Testing），不在本次收紧范围内。
RULESET_VERSION = "ruleset_v0.1.3"

CATEGORIES = [
    "overview",     # 项目概览、技术栈、目的、核心概念
    "structure",    # 架构、目录与文件组织、模块边界
    "build_test",   # 构建、测试、运行、CI
    "style",        # 代码风格、命名、格式、约定
    "workflow",     # 分支、提交、PR、评审、发布
    "environment",  # 环境、工具链、依赖、配置
    "boundaries",   # 禁令、边界、卫生规则
    "gotchas",      # 坑、陷阱、已知问题
    "agent_meta",   # 明确规定 AI 自身行为/语气/身份/协作方式
]

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

# 标题通道（强信号）
HEAD_RULES: dict[str, list[str]] = {
    "overview":    ["overview", "purpose", "about", "introduction", "what is",
                    "what this project", "tech stack", "quick reference",
                    "quick start", "start here", "background", "key concept",
                    "概述", "简介", "背景", "一句话", "项目介绍", "说明",
                    "what this is", "project context", "product direction",
                    "project summary", "current status", "technology stack",
                    "项目定位", "定位", "技术栈", "项目简介"],
    "structure":   ["architecture", "structure", "layout", "organization",
                    "organisation", "directory", "module", "repository map",
                    "repo map", "file organization", "source tree", "monorepo",
                    "key file", "key director", "where to look",
                    # v0.1.2 补：职责/归属类标题。实测 33 个这类章节里 9 个原先无标签，
                    # 而"新代码该放哪里/谁负责哪块"正是 structure 要答的问题。
                    "ownership", "code owner", "who owns", "responsibilit",
                    "maintainer guide", "component map", "domain map",
                    "架构", "目录", "结构", "布局", "模块", "路径", "代码组织",
                    "分工", "职责", "归属", "负责人"],
    # v0.1.3：裸词 `make` 已删——它是普通英文动词（"Make changes"），
    # 只留 makefile 与具体目标，与 STRONG_PATTERNS 的既有口径一致。
    "build_test":  ["build", "test", "command", "ci", "lint", "run",
                    "makefile", "make build", "make test", "make dev", "make run",
                    "make install", "make lint", "make check", "make clean",
                    "make all", "make command", "make target", "make ci",
                    "compile", "usage", "task", "script", "verification", "validation",
                    "quality check",
                    "构建", "测试", "命令", "运行", "编译", "校验",
                    "开发指南", "常用任务", "常用命令"],
    "style":       ["style", "convention", "naming", "format", "standard",
                    "best practice", "pattern", "idiom", "code quality", "type hints",
                    "error handling",
                    "风格", "规范", "命名", "约定", "代码质量"],
    "workflow":    ["workflow", "pull request", "pr ", "commit", "branch",
                    "review", "release", "version", "deploy", "merge", "contributing",
                    "changelog",
                    "流程", "提交", "发布", "分支", "合并", "发布交付",
                    "贡献", "变更日志"],
    "environment": ["environment", "tool", "dependency", "config", "cmake",
                    "requirement", "prerequisite", "setup", "install",
                    "环境", "工具", "依赖", "配置", "安装", "工具链"],
    "boundaries":  ["boundar", "rule", "never", "must not", "do not",
                    "prohibit", "restriction", "constraint", "hygiene",
                    "forbidden",
                    "禁止", "边界", "限制", "约束", "不要", "不得",
                    "规则", "准则", "要求", "红线"],
    "gotchas":     ["gotcha", "pitfall", "caveat", "known issue", "warning",
                    "troubleshoot", "common issue", "footgun", "limitation",
                    "陷阱", "注意", "常见问题", "坑", "注意事项", "调试",
                    "局限"],
    "agent_meta":  ["agent instruction", "agent guidance", "ai instruction",
                    "you are", "your role", "tone", "persona", "behavior",
                    "behaviour", "assistant", "subagent", "sub-agent",
                    "plan mode", "agent workflow", "agent behavior",
                    "协作", "行为", "角色", "智能体",
                    "agent note", "agent tool", "agent prompt",
                    "multi-agent safety", "agentic plugin", "agent skill"],
}

# 全文通道（补救）：仅当标题通道完全无结果时启用，避免过度标注。
BODY_RULES: dict[str, list[str]] = {
    "agent_meta":  [r"\byou are\b", r"\byour role\b",
                    r"\bdo not (?:praise|flatter|apologize)\b",
                    r"\bbe concise\b", r"\btone\b"],
    "boundaries":  [r"\bnever commit\b", r"\bdo not commit\b", r"\bmust not\b",
                    r"\bnever\b.{0,40}\b(?:secret|credential|token|key)\b"],
    "build_test":  [r"```(?:bash|sh|shell)?\n[^`]{0,200}\b(?:npm|yarn|pnpm|"
                    r"pytest|make|cargo|go test|mvn|gradle)\b"],
    "gotchas":     [r"\bgotcha\b", r"\bpitfall\b", r"\bwatch out\b",
                    r"\bnote that\b.{0,60}\b(fail|break|error)\b"],
}

FULLTEXT_RULES: dict[str, list[str]] = {
    "build_test": [
        r"(?m)^\s*[-*]?\s*(?:typecheck|lint|test|build|compile|format|check)\s*:",
        r"```[^`]{0,120}\b(?:cargo|npm|pnpm|yarn|pytest|make|go test|mvn|gradle|docker)\b",
        r"\brun\s+`[^`]+`",
    ],
    "boundaries": [
        r"\b(?:never|don't|do not|must not|avoid)\s+"
        r"(?:run|use|commit|delete|edit|add|modify|push)\b",
    ],
    "workflow": [
        r"\b(?:pull request|squash-?merged|rebase|branch)\b",
        r"\bcommit (?:message|format|style)\b",
    ],
    "agent_meta": [
        r"\bbefore (?:responding|acting|any user)\b",
        r"\byour (?:role|task|job)\b",
        r"\bsub-?agents?\b",
        r"\bplan mode\b",
        r"\brouting rules?\b",
        r"\binstructions? (?:are|is) in\b",
        r"\bonly a human may\b",
    ],
    "gotchas": [
        r"\b(?:gotcha|pitfall|known issue|breaks? if|footgun)\b",
    ],
    "environment": [
        r"\b(?:Turborepo|pnpm workspace|monorepo|workspace root)\b",
    ],
}

# 转引用：正文只是指向另一个文件（真实模式，值得单独标记）
POINTER_PAT = re.compile(
    r"(?:see|read|refer to)\s+[`\[]?\s*([A-Za-z0-9_\-\.]+\.(?:md|mdc))", re.I)
MD_LINK_PAT = re.compile(r"\]\([^)]*\.md(?:#[\w\-]+)?\)|`[A-Za-z0-9_\-\.]+\.md`")

# v0.1.2：判定"正文是不是空壳"用——去掉链接、路径、markdown 装饰后的正文字节数。
# 原先只看体积 + 提到几个 .md，把"短但有料"的章程误判为转引用（见 RULESET_VERSION 注释）。
_STRIP_LINK = re.compile(r"\[[^\]]*\]\([^)\s]+\)")
_STRIP_PATH = re.compile(r"`[^`\n]*`|[\w\-./]+\.(?:md|mdc|txt)\b")
_STRIP_DECOR = re.compile(r"[-*`#>|=|]")

# 语义门：这些话说等于作者自陈"本文件只是路由"，与厚度无关。
# 只用**精确自陈**的短语。"single source of truth" 这类口语化的不算——实测它在 34 份
# 文件里出现，其中大多是几万字节的大文件，拿它当判据会大面积误伤。
POINTER_SEMANTIC = re.compile(
    r"(?i)no instructions in this file|all instructions are in|thin[- ]pointer"
    r"|contains? routing rules|for guidance .{0,30}?see"
    r"|本文不写规则|全部规则在")


def content_bytes(text: str) -> int:
    """去掉链接/路径/markdown 装饰后的正文字节数——"壳"有多厚。"""
    s = _STRIP_LINK.sub("", text)
    s = _STRIP_PATH.sub("", s)
    s = _STRIP_DECOR.sub("", s)
    return len(re.sub(r"\s+", " ", s).strip().encode())

# 指令词密度用于判定 content_mode
IMPERATIVE_PAT = re.compile(
    r"\b(?:do not|don't|never|must|should|always|avoid|required)\b", re.I)

# 强模式通道：**总是运行**（独立于标题通道是否有结果）。
# 这些是跨语言的高精确信号——中文文档常常有内容但标题不含英文关键词，
# 只靠标题通道会给出"什么都没有"的错误结论，比没有工具更糟。
STRONG_PATTERNS: dict[str, list[str]] = {
    "build_test": [
        r"\b(?:pytest|vitest|jest|npm (?:run )?(?:test|build)|pnpm (?:run )?(?:test|build)"
        r"|yarn (?:test|build)|cargo (?:test|build|run|clippy)|go test"
        # 只认具体的 make 目标；`make \w+` 会命中 "make sure" 这类普通英文（假阳性）
        r"|make (?:test|build|install|lint|check|run|dev|all|clean|ci)\b"
        # 同理只认具体目标；`gradle \w+` 会命中 "Gradle 9"（版本号）
        r"|(?:mvn|gradle) (?:test|build|compile|package|install|verify|check"
        r"|clean|assemble|run|tasks|dependencies|clippy)"
        r"|\./gradlew \w+|docker compose)\b",
        r"\.venv/bin/python -m \w+",
    ],
    "workflow": [
        r"\bgit pull\b[\s\S]{0,80}?\bgit push\b",
        r"\bconventional commits?\b",
        r"\bcommit\b[\s\S]{0,24}?\bpush\b",
        r"\bpull request\b",
    ],
    "boundaries": [
        r"[🚫⛔]",
        r"\*\*(?:禁止|不要|不得|严禁)\*\*",
        r"\b(?:do not|never)\b[\s\S]{0,30}?\b(?:commit|push|delete|send)\b",
    ],
    "gotchas": [
        # 只收"这类知识本身"的词；"失败原因""注意事项"太泛（记录失败原因≠坑）
        r"中毒|踩坑|事故|风控|已知问题|经验教训|避坑",
        r"Content Exists Risk",
    ],
    "agent_meta": [
        r"会话压缩|跨会话|防遗忘|自动加载|协作约定",
    ],
}


def split_sections(text: str) -> list[tuple[str, str]]:
    """按标题切分，返回 [(heading, body), ...]；开头无标题部分 heading 为 ''。"""
    sections: list[tuple[str, str]] = []
    cur_head = ""
    buf: list[str] = []
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            if buf or cur_head:
                sections.append((cur_head, "\n".join(buf)))
            cur_head = m.group(2).strip()
            buf = []
        else:
            buf.append(line)
    sections.append((cur_head, "\n".join(buf)))
    return sections


def heading_keyword_hits(low_head: str, kw: str) -> bool:
    """标题关键词命中判定：**词首**匹配，不是任意子串。

    为什么要这样：关键词表里既有完整词（`build`、`review`）也有**故意截断的词干**
    （`convention`、`boundar`、`responsibilit`），所以不能用 `\b` 收口——那会把词干规则一起废掉。
    可行的判据是"命中点必须落在词首"：

      - 词首前缀命中算命中：`convention` → "Coding Conventions"、`test` → "Testing"、
        `boundar` → "Critical Boundaries"（规则有意为之）
      - 词中命中不算：`ci` → "De**ci**sions"、`script` → "Type**Script**"、
        `build` → "allow**Build**s"、`review` → "p**review**"、`format` → "in**format**ion"

    连字符视作词边界（"-" 不是字母）：`commit` 仍能命中 "Pre-Commit Requirements"。
    中文关键词与含空格的多词短语不适用词边界，按原样的子串/短语匹配。
    """
    if not kw.isascii() or " " in kw:
        return kw in low_head
    for m in re.finditer(re.escape(kw), low_head):
        if m.start() == 0 or not low_head[m.start() - 1].isalpha():
            return True
    return False


def classify(heading: str, body: str) -> tuple[set[str], dict[str, list[str]]]:
    """双通道分类：标题强信号 + 正文弱信号。"""
    tags: set[str] = set()
    evidence: dict[str, list[str]] = {}
    low_head = heading.lower()
    for cat, keys in HEAD_RULES.items():
        for k in keys:
            if heading_keyword_hits(low_head, k):
                tags.add(cat)
                evidence.setdefault(cat, []).append(f"heading:{k}")
                break
    for cat, pats in BODY_RULES.items():
        for p in pats:
            if re.search(p, body, re.I):
                tags.add(cat)
                evidence.setdefault(cat, []).append(f"body:{p[:28]}")
                break
    return tags, evidence


def classify_fulltext(text: str) -> tuple[set[str], dict[str, list[str]]]:
    """全文级分类，仅在章节分类无结果时启用。"""
    tags: set[str] = set()
    evidence: dict[str, list[str]] = {}
    for cat, pats in FULLTEXT_RULES.items():
        for p in pats:
            if re.search(p, text, re.I):
                tags.add(cat)
                evidence.setdefault(cat, []).append(f"fulltext:{p[:26]}")
                break
    return tags, evidence
