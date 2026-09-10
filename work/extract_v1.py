"""内容级抽取器 v1：章节切分 + 双通道分类（标题强信号 / 正文弱信号）。

T0 校训结论已吸收：
  - 不用文件名做分类依据（AGENTS.md 本身会污染 agent_meta）
  - 无效内容（<100B 引用型）标记 is_substantive=False
  - 区分 content_mode（rule / knowledge / mixed）
  - 内容重复按 file_sha 计数

用法: .venv/bin/python work/extract_v1.py
输出: data/processed/agent_charters_v0.1.jsonl  +  data/processed/extract_report.md
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

HEAD_RULES: dict[str, list[str]] = {
    "overview":    ["overview", "purpose", "about", "introduction", "what is",
                    "what this project", "tech stack", "quick reference",
                    "quick start", "start here", "background", "key concept",
                    "概述", "简介", "背景", "一句话", "项目介绍", "说明",
                    "what this is", "project context", "product direction",
                    "project summary", "current status"],
    "structure":   ["architecture", "structure", "layout", "organization",
                    "organisation", "directory", "module", "repository map",
                    "repo map", "file organization", "source tree", "monorepo",
                    "架构", "目录", "结构", "布局"],
    "build_test":  ["build", "test", "command", "ci", "lint", "run", "make",
                    "compile", "usage", "task", "script", "构建", "测试",
                    "命令", "运行", "编译", "校验"],
    "style":       ["style", "convention", "naming", "format", "standard",
                    "best practice", "pattern", "idiom", "风格", "规范", "命名",
                    "约定"],
    "workflow":    ["workflow", "pull request", "pr ", "commit", "branch",
                    "review", "release", "version", "deploy", "merge", "流程",
                    "提交", "发布", "分支", "合并", "发布交付"],
    "environment": ["environment", "tool", "dependency", "config", "cmake",
                    "requirement", "prerequisite", "setup", "install",
                    "环境", "工具", "依赖", "配置", "安装", "工具链"],
    "boundaries":  ["boundar", "rule", "never", "must not", "do not",
                    "prohibit", "restriction", "constraint", "hygiene",
                    "forbidden", "禁止", "边界", "限制", "约束", "不要",
                    "不得"],
    "gotchas":     ["gotcha", "pitfall", "caveat", "known issue", "warning",
                    "troubleshoot", "common issue", "footgun", "陷阱", "注意",
                    "常见问题", "坑", "注意事项"],
    "agent_meta":  ["agent instruction", "agent guidance", "ai instruction",
                    "you are", "your role", "tone", "persona", "behavior",
                    "behaviour", "assistant", "subagent", "sub-agent",
                    "plan mode", "agent workflow", "agent behavior",
                    "协作", "行为", "角色", "智能体",
                    "agent note", "agent tool", "agent prompt",
                    "multi-agent safety", "agentic plugin", "agent skill"],
}

# 正文弱信号：命中需要更高阈值（避免像 T0 那样被文件名污染）
BODY_RULES: dict[str, list[str]] = {
    "agent_meta":  [r"\byou are\b", r"\byour role\b", r"\bdo not (?:praise|flatter|apologize)\b",
                    r"\bbe concise\b", r"\btone\b"],
    "boundaries":  [r"\bnever commit\b", r"\bdo not commit\b", r"\bmust not\b",
                    r"\bnever\b.{0,40}\b(?:secret|credential|token|key)\b"],
    "build_test":  [r"```(?:bash|sh|shell)?\n[^`]{0,200}\b(?:npm|yarn|pnpm|pytest|make|cargo|go test|mvn|gradle)\b"],
    "gotchas":     [r"\bgotcha\b", r"\bpitfall\b", r"\bwatch out\b", r"\bnote that\b.{0,60}\b(fail|break|error)\b"],
}

CATEGORIES = list(HEAD_RULES)

# 全文级规则：用于**无标题**文件（纯列表形式，章节分类必然漏标）
FULLTEXT_RULES: dict[str, list[str]] = {
    "build_test": [
        r"(?m)^\s*[-*]?\s*(?:typecheck|lint|test|build|compile|format|check)\s*:",
        r"```[^`]{0,120}\b(?:cargo|npm|pnpm|yarn|pytest|make|go test|mvn|gradle|docker)\b",
        r"\brun\s+`[^`]+`",
    ],
    "boundaries": [
        r"\b(?:never|don't|do not|must not|avoid)\s+(?:run|use|commit|delete|edit|add|modify|push)\b",
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

# 转引用：正文只是指向另一个文件（真实存在的一种模式，值得单独标记）
POINTER_PAT = re.compile(
    r"(?:see|read|refer to)\s+[`\[]?\s*([A-Za-z0-9_\-\.]+\.(?:md|mdc))", re.I)
MD_LINK_PAT = re.compile(r"\]\([^)]*\.md(?:#[\w\-]+)?\)|`[A-Za-z0-9_\-\.]+\.md`")


def split_sections(text: str) -> list[tuple[str, str]]:
    """返回 [(heading, body), ...]，开头无标题部分用 '' 作为 heading。"""
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
    """全文级分类，仅在章节分类无结果时启用（避免过度标注）。"""
    tags: set[str] = set()
    evidence: dict[str, list[str]] = {}
    for cat, pats in FULLTEXT_RULES.items():
        for p in pats:
            if re.search(p, text, re.I):
                tags.add(cat)
                evidence.setdefault(cat, []).append(f"fulltext:{p[:26]}")
                break
    return tags, evidence


def doc_language(text: str) -> str:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if cjk == 0:
        return "en"
    return "zh" if cjk * 12 > letters else "mixed"


def main() -> None:
    outdir = Path("data/processed")
    outdir.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in
            Path("data/raw/full_manifest.jsonl").read_text().splitlines()]

    sha_counts = Counter(r["file_sha"] for r in rows)
    records = []
    cat_doc_count = Counter()
    cat_item_count = Counter()
    substantively_empty = 0

    for r in rows:
        p = Path(r["local_file"])
        text = p.read_text(encoding="utf-8", errors="replace")
        size = len(text.encode("utf-8"))
        is_sub = size >= 100 and not re.fullmatch(
            r"\s*[^\n]{0,80}\.(?:md|mdc|txt)\s*", text)

        sections = split_sections(text)
        tag_counts: Counter = Counter()
        ev: dict[str, list[str]] = {}
        for head, body in sections:
            if not head.strip() and len(body.strip()) < 40:
                continue
            tags, evidence = classify(head, body)
            for t in tags:
                tag_counts[t] += 1
                ev.setdefault(t, []).extend(evidence.get(t, [])[:1])

        tags = sorted(tag_counts)

        # 无标题文件的补救：章节分类落空时启用全文级规则
        used_fulltext = False
        if not tags:
            ft_tags, ft_ev = classify_fulltext(text)
            if ft_tags:
                used_fulltext = True
                for t in ft_tags:
                    tag_counts[t] += 1
                    ev.setdefault(t, []).extend(ft_ev.get(t, [])[:1])
                tags = sorted(tag_counts)

        for t in tags:
            cat_doc_count[t] += 1
            cat_item_count[t] += tag_counts[t]
        if not is_sub:
            substantively_empty += 1

        rule_signals = len(re.findall(
            r"\b(?:do not|don't|never|must|should|always|avoid|required)\b",
            text, re.I))
        mode = ("rule" if rule_signals >= 5 else
                "knowledge" if rule_signals <= 1 else "mixed")

        md_links = len(MD_LINK_PAT.findall(text))
        is_pointer = (bool(POINTER_PAT.search(text)) or md_links >= 2) and size < 2000

        records.append({
            "repo_full_name": r["repo_full_name"],
            "file_path": r["file_path"],
            "file_sha": r["file_sha"],
            "commit_date": r.get("repo_pushed_at"),
            "repo_stars": r["repo_stars"],
            "repo_language": r["repo_language"],
            "license": r["license"],
            "bytes": size,
            "lines": text.count("\n") + 1,
            "section_count": len(sections),
            "doc_language": doc_language(text),
            "size_tier": ("small" if size < 1024 else
                          "medium" if size < 10240 else "large"),
            "is_substantive": is_sub,
            "is_pointer": is_pointer,
            "content_mode": mode,
            "rule_signals": rule_signals,
            "categories": tags,
            "category_counts": dict(tag_counts),
            "total_sections_tagged": sum(tag_counts.values()),
            "duplicate_sha_count": sha_counts[r["file_sha"]],
            "used_fulltext_fallback": used_fulltext,
            "extractor_version": "extract_v1",
            "taxonomy_version": "taxonomy_v0.1",
        })

    out = outdir / "agent_charters_v0.1.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n = len(records)
    valid = [r for r in records if r["is_substantive"]]
    no_tag = [r for r in valid if not r["categories"]]
    lines = [
        "# 抽取报告 extract_v1", "",
        f"- 总记录 {n}，其中实质内容 {len(valid)}，非实质 {n - len(valid)}",
        f"- 无任何类别标签的实质文件 {len(no_tag)}",
        f"- 内容重复文件（sha 出现>1 次）{sum(1 for r in records if r['duplicate_sha_count'] > 1)}",
        "", "## 类别分布（文件数 / 标签出现次数）", "",
    ]
    for c in CATEGORIES:
        lines.append(f"- `{c}`: {cat_doc_count[c]} 份 / {cat_item_count[c]} 次")
    lines += ["", "## content_mode 分布", ""]
    for m, c in Counter(r["content_mode"] for r in records).most_common():
        lines.append(f"- {m}: {c}")
    lines += ["", "## doc_language 分布", ""]
    for m, c in Counter(r["doc_language"] for r in records).most_common():
        lines.append(f"- {m}: {c}")
    lines += ["", "## size_tier 分布", ""]
    for m, c in Counter(r["size_tier"] for r in records).most_common():
        lines.append(f"- {m}: {c}")
    lines += ["", "## 未能归类的样本（前 15，供改进分类法）", ""]
    for r in no_tag[:15]:
        lines.append(f"- {r['repo_full_name']} ({r['bytes']}B, "
                     f"{r['section_count']} sections)")
    (outdir / "extract_report.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    print("\n".join(lines[:26]))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
