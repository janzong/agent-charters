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
# v0.1.4（2026-09-12）口径裁决落地（D31 同批，人定四条定义边界，见 TAXONOMY.md「口径裁决」）：
#   `agent_meta` 删掉三个**路由型**标题词（`agent instruction` / `agent guidance` / `ai instruction`）。
#   依据：这三类标题在实际语料里几乎都是**文件自己的名字**（"WSL2 Distro Manager — Agent Instructions"），
#   而本语料库的每份文件按定义都是写给 agent 的——所以这个标签不携带区分度，
#   与 v0.1b 修掉的"文件名叫 AGENTS.md 导致命中率 79%"是同一类错误。
#   实测（511 份）：agent_meta 36.4% → **29.5%**（−35 份，无新增）；副作用 build_test +1
#   （某份文件因此章节无标签，落到全文兜底通道）。正文通道（`you are` / `be concise`）保留，
#   真有行为内容的文件不掉（如 PraisonAI 靠 `body:\byou are\b` 保住）。
#   更宽的删除口径（再删 agent tool/prompt/note/skill/behavior/workflow）实测会到 25.2%——
#   **未采纳**：那些章节通常是内容型，等 100 份人工核对给出 precision 数据再定。
# v0.1.5（2026-09-12）CJK 通道修复，来自首次**中文**盲判对照（10 份，用户独立盲判）：
#   对照结果：逐类一致率 40–70%，规则多标 14 处、漏标 23 处（`work/audit/v0.4-zh-verdicts.md`）。
#   机制诊断：标题通道只认标题里的词表词；**正文弱信号通道 4 个类别全是英文正则**；
#   全文通道的门是"标题通道无结果才跑"。⇒ CJK 文档实际只剩「标题词 + 命令类强模式」两条窄路。
#   本轮三处改动：
#   (a) 标题词表补**繁体/日文汉字形**（環境≠环境、設定≠设定、検証≠验证、構成≠构成）与
#       中文常用标题词（目的/概要/注意点/方針/禁止事項/不可协商）；实测 LiveLog 7 个日文标题原先 0 命中。
#   (b) 正文通道补中文模式（禁令"不允许/严禁"、坑"否则会/会导致"、环境"环境变量/venv"、
#       概览"本项目/这是一个"、结构"目录结构/模块划分"、流程"提交信息/分支命名"、风格"命名规范"）。
#       只收高精度形式：`必须` 太泛（"必须运行测试"是 build_test 不是禁令）、`不要` 在散文里太多，均不收。
#   (c) `doc_language` 加假名判据：日文此前被判成 `zh`（LiveLog 假名 274 / 汉字 202）。
# v0.1.6（2026-09-12）`split_sections` 跳过围栏代码块内的行（``` / ~~~）。
#   此前**任何** `# 注释` 行都被当成标题。实测 129/558 份文件在代码块里有这类行
#   （最多一份 54 行），后果：① bash 注释变成章节标题，把正文切碎；
#   ② 往标题通道灌假信号（`# tools/…` → environment、`# Install` → build_test、
#      `# Rules` → boundaries、`# Writing Style` → style）；③ `section_count` 失真。
#   两条配套规矩：**围栏数为奇时最后一个标记不作数**（否则未闭合围栏会吞掉后文，
#   tempoxyz/mpp 的 39 个章节掉到 10 个）；**一段围栏里藏着 ≥3 个 markdown 标题时
#   不当它是代码块**（mpp 用 ```mdx 套 ```ts 的格式不良嵌套，CommonMark 会吞掉 7 个真标题）。
#   同批落地 `TAXONOMY.md` 口径裁决 5–7（人定）：①"本文件是…入口"这类文件自身角色不算 overview；
#   ②指向某规范的链接不算 style；③文档指针表算 structure（新增"表格型结构信号"，
#   只认表头首列为 文档/文件/路径/目录/模块/组件/包 的表，实测 structure 59.7%→59.9%）。
RULESET_VERSION = "ruleset_v0.1.7"

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
FENCE = re.compile(r"^\s{0,3}(?:```|~~~)")

# 标题层的否决式：词表命中后，标题整体落在这些模式里就撤掉该标签。
# 只为**多义词**而设，每条都来自一次实测误标（见 RULESET_VERSION v0.1.6 注释）。
HEAD_VETO: dict[str, list[str]] = {
    "style": [r"(?:提交|发布|流程|合并|分支|评审|工程)规范",
              r"(?:提交|发布|流程|合并|分支)约定"],
    "boundaries": [r"已知.{0,8}限制", r"限制（不是 bug"],
    # v0.1.7：`依赖` 的两种语义。依赖的**拓扑/方向/角色**是架构（structure），
    # 不是环境；实测 claudian「Dependency Direction」、crush「Key Dependency Roles」、
    # langgraph「Dependency map」三份都只有这一个词在撑 environment。
    # 依赖的**管理/版本/安全/钉版本**（management / pinning / security / versioning）
    # 仍是 environment，不在否决之列。
    "environment": [r"dependenc\w*\s+(?:direction|map|graph|role|diagram|topolog)"],
}

# 裸词白名单（v0.1.7）：这些词只有**整个标题就是它**（可带 guide/说明 等后缀）时才算数。
# 起因：`usage` 在 4 份文件里独撑 build_test，其中 3 份是错的——
# 「AI usage」（AI 使用政策 → agent_meta）、「Color Usage Rules」（样式规范）、
# 「Context7 Usage Rules」（工具使用规定）。带限定语时词义已经变了。
BARE_HEADING: dict[str, set[str]] = {"build_test": {"usage", "用法"}}
BARE_SUFFIX = {"", "guide", "说明", "指南", "用法", "instructions", "notes", "note"}

# 标题通道（强信号）
HEAD_RULES: dict[str, list[str]] = {
    # v0.1.5：补中日文标题词。缺的两类很典型——①中文常用标题词（目的/概要/注意点）；
    # ②**繁体/日文汉字形**（環境≠环境、設定≠设定、検証≠验证、構成≠构成），
    # 简体词表在繁体与日文文档上等于空转（实测 sankichi92/LiveLog：7 个日文标题 0 命中）。
    "overview":    ["overview", "purpose", "about", "introduction", "what is",
                    "what this project", "tech stack",
                    # v0.1.7：撤掉 `start here` / `quick start` / `quick reference`——
                    # 它们是**容器型/导航型**标题，本身不含类别信息，正文才决定类别。
                    # 实测：start here 独撑的 7 份、quick start 独撑的 3 份**全部**是
                    # 阅读顺序/文档指针/命令行块；quick reference 独撑的 10 份里 9 份
                    # 是命令块或规则表，只有 1 份（AReaL）真的是技术栈。
                    "background", "key concept",
                    "概述", "简介", "背景", "一句话", "项目介绍", "说明",
                    "what this is", "project context", "product direction",
                    "project summary", "current status", "technology stack",
                    "项目定位", "定位", "技术栈", "项目简介",
                    "目的", "概要", "介绍", "快速开始", "はじめに", "紹介"],
    "structure":   ["architecture", "structure", "layout", "organization",
                    "organisation", "directory", "repository map",
                    # v0.1.7：裸词 `module` 撤掉，换成具体形态。实测它独撑的 2 份
                    # 全错：「File and Module Naming」是命名规范（style）、
                    # 「Module scope freezes the locale」是坑（gotchas）；
                    # 另有「Adding a new core module」这种流程章节被误判成结构。
                    "module boundar", "module structure", "module layout",
                    "module organisation", "module organization", "module map",
                    "dependency direction", "dependency map", "dependency graph",
                    "dependency role", "依赖方向", "依赖图", "模块边界",
                    "repo map", "file organization", "source tree", "monorepo",
                    "key file", "key director", "where to look",
                    # v0.1.2 补：职责/归属类标题。实测 33 个这类章节里 9 个原先无标签，
                    # 而"新代码该放哪里/谁负责哪块"正是 structure 要答的问题。
                    "ownership", "code owner", "who owns", "responsibilit",
                    "maintainer guide", "component map", "domain map",
                    "架构", "目录", "结构", "布局", "模块", "路径", "代码组织",
                    "分工", "职责", "归属", "负责人",
                    "構成", "構造", "ディレクトリ", "ファイル構成", "モジュール",
                    "存放位置", "代码结构", "目录结构", "模块划分"],
    # v0.1.3：裸词 `make` 已删——它是普通英文动词（"Make changes"），
    # 只留 makefile 与具体目标，与 STRONG_PATTERNS 的既有口径一致。
    "build_test":  ["build", "test", "command", "ci", "lint", "run",
                    "makefile", "make build", "make test", "make dev", "make run",
                    "make install", "make lint", "make check", "make clean",
                    "make all", "make command", "make target", "make ci",
                    "compile", "usage", "task", "script", "verification", "validation",
                    "quality check",
                    "构建", "测试", "命令", "运行", "编译", "校验",
                    "开发指南", "常用任务", "常用命令",
                    "コマンド", "検証", "チェック", "ビルド", "テスト", "実行",
                    "开发命令", "本地开发", "上手指南", "启动"],
    "style":       ["style", "convention", "naming", "format", "standard",
                    "best practice", "pattern", "idiom", "code quality", "type hints",
                    "error handling",
                    "风格", "规范", "命名", "约定", "代码质量",
                    "コーディング", "命名規則", "スタイル", "規約",
                    "代码风格", "编码规范", "注释规范"],
    "workflow":    ["workflow", "pull request", "pr ", "commit", "branch",
                    "review", "release", "version", "deploy", "merge", "contributing",
                    "changelog",
                    "流程", "提交", "发布", "分支", "合并", "发布交付",
                    "贡献", "变更日志",
                    "手順", "フロー", "リリース", "コミット", "ブランチ", "レビュー",
                    "工作流", "协作流程",
                    # v0.1.7：workflow 此前只有 git/PR/发布词，整类"编号步骤型 how-to"
                    # 都漏（vcz-Gray/loophaus 的「Adding a new core module」4 步 +
                    # 「Adding a new platform」3 步，两条全丢）。
                    "adding a new", "adding new", "how to add", "how to create",
                    "新增", "添加新"],
    "environment": ["environment", "tool", "dependency", "config", "cmake",
                    "requirement", "prerequisite", "setup", "install",
                    "环境", "工具", "依赖", "配置", "安装", "工具链",
                    "環境", "設定", "依存関係", "ツール", "セットアップ", "インストール",
                    "开发环境", "运行环境", "环境准备", "环境搭建", "前置条件"],
    "boundaries":  ["boundar", "rule", "never", "must not", "do not",
                    "prohibit", "restriction", "constraint", "hygiene",
                    "forbidden",
                    "禁止", "边界", "限制", "约束", "不要", "不得",
                    "规则", "准则", "要求", "红线",
                    "方針", "ポリシー", "ガードレール", "ルール", "禁止事項", "制約", "厳禁",
                    "铁律", "硬性规则", "不可协商", "非协商"],
    "gotchas":     ["gotcha", "pitfall", "caveat", "known issue", "warning",
                    "troubleshoot", "common issue", "footgun", "limitation",
                    "陷阱", "注意", "常见问题", "坑", "注意事项", "调试",
                    "局限", "限制",
                    "注意点", "既知の問題", "トラブル", "ハマり", "落とし穴",
                    "常见错误", "易错", "坑点"],
    # v0.1.4：删掉 agent instruction / agent guidance / ai instruction（路由型标题，见 RULESET_VERSION 注释）
    "agent_meta":  ["you are", "your role", "tone", "persona", "behavior",
                    "behaviour", "assistant", "subagent", "sub-agent",
                    "plan mode", "agent workflow", "agent behavior",
                    "协作", "行为", "角色", "智能体", "あなた", "役割", "トーン",
                    "agent note", "agent tool", "agent prompt",
                    "multi-agent safety", "agentic plugin", "agent skill"],
}

# 全文通道（补救）：仅当标题通道完全无结果时启用，避免过度标注。
BODY_RULES: dict[str, list[str]] = {
# v0.1.5 补：中文/日文正文模式。此前正文通道 4 个类别**全是英文正则**，
# CJK 文档的正文通道等于不存在——内容在正文里（"提交信息必须包含 head+body""不允许只有单行标题"）
# 而标题是"提交规范"，于是整节只拿到标题命中的那一个类别。
# 只收高精度形式：`必须`太泛（"必须运行测试"是 build_test 不是禁令），`不要`在散文里太多，都不收。
    "boundaries":  [r"(?:严禁|禁止|不允许|请勿|切勿|绝对禁止|严格禁止|不得不)",
                    r"(?:不得|勿)[\s]{0,2}(?:提交|推送|删除|修改|执行|使用)",
                    r"\bnever commit\b", r"\bdo not commit\b", r"\bmust not\b",
                    r"\bnever\b.{0,40}\b(?:secret|credential|token|key)\b",
                    # v0.1.7：补"被禁止"类被动式。google/benchmark 通篇
                    # "are prohibited" / "forbidden"，此前 0 命中。
                    r"\b(?:is|are|be)\s+(?:strictly\s+)?prohibited\b", r"\bforbidden\b"],
    # ASCII 词一律加 \b：`conda` 会命中 "se**conda**ry"（4 份），与 v0.1.3 的
    # `ci` → "De**ci**sions" 是同一类子串 bug。裸 `.env` 不收——实测 28 份里多是
    # "Never commit `.env`" 这类**禁令**语句，指向的是 boundaries 不是 environment。
    "environment": [r"(?:环境变量|前置条件|本地(?:开发)?环境|需要安装|安装依赖|工具链)",
                    r"\b(?:venv|pyenv|conda|pixi|nvm|nvmrc)\b",
                    r"\.env\.(?:example|sample|template)\b"],
    # 必须有判断词（是/为/旨在…）：`本仓库对 Harness Engineering 的落地清单`
    # 是文档指针列表里的短语，不是项目概览（artemis 实测）。
    # 排除"本文件是…入口"这类**文件自身角色**的句子（claude-tap 实测误命中）。
    "overview":    [r"(?:本项目|该项目|本仓库|本文件|这是一个|是一款)"
                    r"(?:是|为|旨在|主要|用于|提供)(?![^。\n]{0,12}入口)",
                    # v0.1.7：撤掉容器型标题后，用正文把"技术栈"接回来
                    # （AReaL 的 Quick reference 正文就是 `**Tech stack**: ...`）。
                    r"(?:tech(?:nology)?\s+stack|技术栈)\**\s*[:：]"],
    # 裁决 7（2026-09-12）：文档指针表算 structure——"哪份文档在哪、谁读、什么放哪里"
    # 正是该类定义里的文件布局/路径/归属。只认**表头首列**是文档/文件/路径…的表，
    # 不认正文里出现的"文件"二字（那太泛）。
    "structure":   [r"(?:目录结构|代码结构|模块划分|分层结构|存放位置)",
                    r"(?m)^\s*\|\s*(?:文档|文件|路径|目录|模块|组件|包)\s*\|"],
    "workflow":    [r"(?:提交(?:信息|规范)|分支命名|发布流程|合并前)"],
    # 排除"分支/目录/文件命名规范"——那是 workflow/structure 的内容（Operit 实测误命中）。
    "style":       [r"(?:代码风格|编码规范|注释规范)",
                    r"(?<!分支)(?<!目录)(?<!文件)命名(?:规范|约定|规则)"],
    "agent_meta":  [r"\byou are\b", r"\byour role\b",
                    # v0.1.7：补"AI 使用政策"文体。此前 body 通道只有**人格指令**
                    # （you are / be concise / tone），于是 google/benchmark 这种
                    # "AI 能不能参与贡献、必须披露、责任归属"的政策文档 0 命中——
                    # 而它恰恰是九类里最纯的 agent_meta 样本。
                    # 只认"AI + 规范性情态"（must / shall / 披露 / 禁止）：
                    # 实测 `responsib|accountab` 太松——"Responsible AI principles"
                    # 是课程话题（microsoft/AI-For-Beginners 假阳性）；
                    # lookaround 排掉路径里的 ai（777genius 的 `ai/claude-runtime` 假阳性）。
                    r"(?<![/\w])AI(?!/[\w])[^.\n]{0,60}\b(?:must|shall|disclos|prohibit)",
                    r"\b(?:bot|autonomous)\w*\s+contributions?\b",
                    r"\bdo not (?:praise|flatter|apologize)\b",
                    r"\bbe concise\b", r"\btone\b"],
    "build_test":  [r"```(?:bash|sh|shell)?\n[^`]{0,200}\b(?:npm|yarn|pnpm|"
                    r"pytest|make|cargo|go test|mvn|gradle)\b"],
    "gotchas":     [r"\bgotcha\b", r"\bpitfall\b", r"\bwatch out\b",
                    r"\bnote that\b.{0,60}\b(fail|break|error)\b",
                    r"(?:否则(?:会|将)|会导致|会造成|容易出错|踩(?:过|到)坑|避坑|已知问题)",
                    # "注意事项：" 这种引导句（不带 ## 的正文小标题）——syc 实测漏标
                    r"注意(?:事项|点)[：:]"],
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
        r"|\./gradlew \w+|docker compose (?:up|down|build|run|logs|exec|ps|restart|stop|start))\b",
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
        # "踩坑" 单收太泛：命中过"有高频易踩坑，询问用户是否沉淀为 Skill"（不是坑知识）
        r"中毒|踩过坑|踩坑记录|事故|风控|已知问题|经验教训|避坑",
        r"Content Exists Risk",
    ],
    "agent_meta": [
        r"会话压缩|跨会话|防遗忘|自动加载|协作约定",
    ],
}


def split_sections(text: str) -> list[tuple[str, str]]:
    """按标题切分，返回 [(heading, body), ...]；开头无标题部分 heading 为 ''。

    v0.1.6：跳过围栏代码块（``` / ~~~）内的行。此前**任何** `# 注释` 行都被当成标题，
    实测 129/558 份文件在代码块里有这类行（最多一份 54 行），后果有三：
      ① bash 注释变成"章节标题"，把正文切碎；
      ② 往标题通道灌假信号（`# tools/get-winflexbison.sh …` → environment、
         `# 安装依赖` → build_test、`# Build` → build_test）；
      ③ `section_count` 这一列随之失真（它是发布出去的字段）。
    """
    lines = text.splitlines()
    fence_at = [i for i, ln in enumerate(lines) if FENCE.match(ln)]
    # 围栏数为奇 ⇒ 有一个没闭合。**把最后一个围栏标记当普通文本**，
    # 否则它后面的真标题会被整段吞掉（tempoxyz/mpp：39 个章节掉到 10 个）。
    if len(fence_at) % 2:
        fence_at = fence_at[:-1]
    code_lines = set()
    for a, b in zip(fence_at[0::2], fence_at[1::2]):
        # 护栏：一段围栏里若藏着 ≥3 个 markdown 标题，它多半不是代码块，而是
        # **格式不良的嵌套围栏**（tempoxyz/mpp 用 ```mdx 套 ```ts，作者没升到四反引号，
        # 于是 CommonMark 会把后文 7 个真标题吞进代码块）。真代码块里极少出现
        # "## 标题"这种行，所以按标题密度反证。
        if sum(1 for i in range(a, b + 1) if HEADING.match(lines[i])) >= 3:
            continue
        code_lines.update(range(a, b + 1))

    sections: list[tuple[str, str]] = []
    cur_head = ""
    buf: list[str] = []
    for i, line in enumerate(lines):
        m = None if i in code_lines else HEADING.match(line)
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


def is_bare_heading(low_head: str, kw: str) -> bool:
    """标题是否**就是**这个词（可带 guide/说明 这类后缀）。

    供 `BARE_HEADING` 用：多义词只有在标题整体等于它时才承认词义，
    带限定语的（AI usage / Color Usage Rules）交回给别的类别或正文通道。
    """
    norm = re.sub(r"[^\w\u4e00-\u9fff]+", " ", low_head).strip()
    if norm == kw:
        return True
    if norm.startswith(kw + " "):
        return norm[len(kw) + 1:] in BARE_SUFFIX
    return False


def classify(heading: str, body: str) -> tuple[set[str], dict[str, list[str]]]:
    """双通道分类：标题强信号 + 正文弱信号。

    v0.1.6 加 `HEAD_VETO`：标题命中后，若整个标题落在某条否决式里，就撤掉该标签。
    起因是**多义词**：`规范` 命中"提交规范/发布规范"（那是流程）、`约定` 命中
    "代码与提交流程约定"、`限制` 命中"已知文法/语义限制（不是 bug）"（那是坑）。
    词表本身没法区分，只有在标题层做否决。
    """
    tags: set[str] = set()
    evidence: dict[str, list[str]] = {}
    low_head = heading.lower()
    for cat, keys in HEAD_RULES.items():
        for k in keys:
            if heading_keyword_hits(low_head, k):
                if (k in BARE_HEADING.get(cat, set())
                        and not is_bare_heading(low_head, k)):
                    continue
                if any(re.search(p, low_head) for p in HEAD_VETO.get(cat, [])):
                    break
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
