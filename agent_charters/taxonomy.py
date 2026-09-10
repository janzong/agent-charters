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
RULESET_VERSION = "ruleset_v0.1.1"

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
                    "架构", "目录", "结构", "布局", "模块", "路径", "代码组织"],
    "build_test":  ["build", "test", "command", "ci", "lint", "run", "make",
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


def classify(heading: str, body: str) -> tuple[set[str], dict[str, list[str]]]:
    """双通道分类：标题强信号 + 正文弱信号。"""
    tags: set[str] = set()
    evidence: dict[str, list[str]] = {}
    low_head = heading.lower()
    for cat, keys in HEAD_RULES.items():
        for k in keys:
            if k in low_head:
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
