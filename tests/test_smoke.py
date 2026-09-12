"""agent-charters 冒烟测试。

    .venv/bin/pytest -q

覆盖三类不变量：
  1. 随包语料库的形状与可追溯字段（判据 2）
  2. 分类器行为——含中文文档回归与两个已知假阳性回归
  3. 语料库可由 data/raw 重放（工具与数据集同源）
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_charters import (analyze_file, analyze_text, category_coverage,  # noqa: E402
                            load_corpus, substantive)
from agent_charters.extract import DATASET_VERSION  # noqa: E402
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

RAW = ROOT / "data" / "raw" / "full"
MANIFEST = ROOT / "data" / "raw" / "full_manifest.jsonl"


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


def test_corpus_shape(corpus):
    assert len(corpus) == 558
    assert len(corpus.columns) == 30
    sub = substantive(corpus)
    assert len(sub) == 511


def test_every_row_is_traceable(corpus):
    """判据 2：每行都能回答"这是谁的、什么时候抓的、按什么规则抽的"。"""
    for col in ["repo_full_name", "file_path", "file_sha", "commit_date",
                "retrieved_at", "extractor_version", "taxonomy_version",
                "ruleset_version"]:
        assert corpus[col].notna().all(), col
    assert set(corpus["retrieved_at"]) == {"2026-09-10"}


def test_categories_are_known(corpus):
    known = set(CATEGORIES)
    for tags in corpus["categories"]:
        assert set(tags) <= known


# --- 分类器行为 ---------------------------------------------------------

ZH_CHARTER = """# 项目章程

## 模块与分工
- 后端在 `backend/app`，前端在 `frontend/src`

## 强制规则
- 全量测试通过才允许 commit：`.venv/bin/python -m pytest tests -q`
- 🚫 禁止把密钥写进仓库

## 风控与踩坑
- 会话中毒时必须先备份再脱敏

## 协作约定
- 改动前先 `git pull`，完成后 `git push`
"""


def test_chinese_charter_is_not_invisible():
    """回归：中文文档曾被判成"什么都没有"（比没工具更糟）。"""
    rec = analyze_text(ZH_CHARTER)
    assert len(rec["categories"]) >= 6, rec["categories"]
    for c in ["structure", "boundaries", "gotchas", "agent_meta",
              "build_test", "workflow"]:
        assert c in rec["categories"], c
    assert rec["doc_language"] == "zh"


def test_non_substantive_marker():
    assert not analyze_text("AGENTS.md").get("is_substantive")


# --- v0.1.5：CJK 通道（首次中文盲判对照暴露的机制缺陷）------------------
# 依据 work/audit/v0.4-zh-verdicts.md：正文通道原先 4 个类别全是英文正则，
# CJK 文档的内容写在正文里、标题只有"提交规范"这种词，于是整节丢标签。

ZH_BODY_RULES = """# AGENTS

## 提交规范

- `git commit` 信息必须使用中文。
- 提交信息必须包含 `head + body` 两部分，不允许只有单行标题。
- 发布新版本时，必须参考 `docs/release.md` 执行。
"""


def test_chinese_prohibition_in_body_is_boundaries():
    """回归：`不允许…`写在正文里（标题是"提交规范"）曾整节漏标。"""
    cats = analyze_text(ZH_BODY_RULES)["categories"]
    assert "boundaries" in cats, cats


def test_chinese_body_environment_and_gotchas():
    text = ("# AGENTS\n\n## 说明\n\n如果运行 python，项目用的是 venv（将迁移到 pixi）。\n\n"
            "严禁使用 powershell 编辑代码文件，否则会出现严重的编码错误和损坏。\n")
    cats = analyze_text(text)["categories"]
    assert "environment" in cats, cats
    assert "gotchas" in cats, cats


def test_traditional_and_japanese_heading_forms():
    """繁体/日文汉字形：環境≠环境、設定≠设定、検証≠验证、構成≠构成。"""
    text = ("# AGENTS.md\n\n## 環境構築\n\n- Node 24 を使う。\n\n"
            "## 構成\n\n- `src/` に実装、`tests/` にテスト。\n\n"
            "## 方針\n\n- 本番反映は人手承認を必須とする。\n")
    cats = analyze_text(text)["categories"]
    for c in ("environment", "structure", "boundaries"):
        assert c in cats, (c, cats)
    assert analyze_text(text)["doc_language"] == "ja"


def test_japanese_purpose_heading_is_overview():
    assert "overview" in analyze_text("# A\n\n## 目的\n\n- 安全に変更する。\n")["categories"]


# --- 口径裁决 5–7（2026-09-12）：内容 vs 指针的边界 -------------------

def test_doc_pointer_table_is_structure():
    """裁决 7：文档指针表算 structure（Clutch 实测）。"""
    text = ("# AGENTS\n\n| 文档 | 读者 | 用途 |\n|---|---|---|\n"
            "| `CLAUDE.md` | 全体开发者 | 唯一权威 |\n")
    assert "structure" in analyze_text(text)["categories"]


def test_file_role_sentence_is_not_overview():
    """裁决 5：只说"本文件是入口"不算 overview；描述仓库的才算。"""
    role = "# A\n\n本文件是贡献者规则的入口。详细策略见 `.agents/docs/`。\n"
    assert "overview" not in analyze_text(role)["categories"]
    about = ("# A\n\n本文件为 AI 编码代理提供本仓库的构建、测试与架构要点。\n"
            "syc 是一个教学用编译器。\n")
    assert "overview" in analyze_text(about)["categories"]


def test_link_to_style_doc_is_not_style():
    """裁决 6：指向某规范的链接不算 style，类别只收内容本身。"""
    text = ("# AGENTS\n\n| 文档 | 读者 | 用途 |\n|---|---|---|\n"
            "| `docs/UI_UX_GUIDELINES.md` | 前端 | React + Tailwind UI/UX 规范 |\n")
    assert "style" not in analyze_text(text)["categories"]


# --- v0.1.6：围栏代码块内的 `# 注释` 不是标题 ---------------------------

FENCED = """# AGENTS

## 构建

```bash
# Rules
# Install
npm ci
```

## 测试

```bash
# Writing Style
npm test
```
"""


def test_code_comment_is_not_a_heading():
    """回归：bash 注释曾被当成章节标题，往标题通道灌假信号。

    实测 129/558 份文件在代码块里有这类行（最多一份 54 行）。
    `# Rules` 曾把 boundaries、`# Writing Style` 曾把 style 标进语料库。
    """
    rec = analyze_text(FENCED)
    assert "boundaries" not in rec["categories"], rec["categories"]
    assert "style" not in rec["categories"], rec["categories"]
    assert rec["section_count"] == 3, rec["section_count"]   # AGENTS / 构建 / 测试


def test_unclosed_fence_does_not_swallow_rest_of_file():
    """围栏数为奇时最后一个标记不作数，否则后文的真标题会被整段吞掉。"""
    text = "# A\n\n```bash\necho hi\n\n## 环境\n\n- nvm 24\n"
    assert "environment" in analyze_text(text)["categories"]


def test_malformed_nested_fence_with_many_headings_is_not_code():
    """```mdx 套 ```ts 这类格式不良的嵌套围栏会把真标题吞进代码块——
    一段围栏里藏着 ≥3 个 markdown 标题时，按标题密度反证它不是代码块。"""
    text = ("# A\n\n```mdx\n## 一\n\ntext\n\n## 二\n\ntext\n\n## 三\n\ntext\n```\n\n"
            "## 架构\n\n- `src/` 放实现。\n")
    assert "structure" in analyze_text(text)["categories"]


def test_shell_comment_block_is_not_a_heading():
    """发现 16（v0.1.8）：密度反证加了**语言标记门**。

    反证原本只看"围栏段里有没有 ≥3 行像标题"，于是 shell 注释块（`# Rules` /
    `# Build` / `# Writing Style`）直接触发反证、整段 bash 被当正文扫。
    实测全库 86/558 触发，假标题产出 build_test 69 份、environment 41、
    workflow 27、style 20；改后 15 份各掉 1 个标签、无一例新增，抽查全为真错。
    无标记的 ``` 仍走反证（`tempoxyz/mpp` 的 ```mdx 畸形嵌套因此没被误伤）。
    """
    text = ("# A\n\n```bash\n# Rules\n# Build\n# Writing Style\necho hi\n```\n\n"
            "## 架构\n\n- `src/` 放实现。\n")
    rec = analyze_text(text)
    assert "boundaries" not in rec["categories"], rec["categories"]
    assert "build_test" not in rec["categories"], rec["categories"]
    assert "style" not in rec["categories"], rec["categories"]
    assert rec["section_count"] == 2, rec["section_count"]   # A / 架构


@pytest.mark.parametrize("text,forbidden", [
    ("# A\n\n## Next steps\n\nReview each secondary monitor for regressions.\n", "environment"),
    ("# A\n\n## X\n\nNever commit `.env` to the repo.\n", "environment"),
])
def test_environment_patterns_do_not_fire_on_substrings(text, forbidden):
    """`conda` 会命中 se**conda**ry；裸 `.env` 多是"别提交"的禁令语句。"""
    assert forbidden not in analyze_text(text)["categories"]


@pytest.mark.parametrize("text, forbidden", [
    ("Please make sure to double check.", "build_test"),      # make sure ≠ make test
    ("Gradle 9.3.1 and AGP 9.1.1 are used.", "build_test"),   # 版本号 ≠ 构建命令
    ("记录输出日志、失败原因。", "gotchas"),                    # 记录失败原因 ≠ 坑
    # v0.1.3 删裸词 make 的实测依据：511 份里 12 个标题命中，7 个是散文。
    ("Never Make Legal Decisions as an Agent", "build_test"),  # Make ≠ make build
    ("Where to make changes", "build_test"),                   # make changes ≠ make
])

def test_known_false_positives_stay_out(text, forbidden):
    assert forbidden not in analyze_text(text)["categories"]


# U3（ruleset_v0.1.3）：标题通道曾是**纯子串**匹配，于是 "ci" 命中了 "De**ci**sions"、
# "script" 命中了 "Type**Script**"。实测 511 份里 18 份文件各掉 1 个类别标签（无一例新增），
# `build_test` 覆盖率因此从 87.9% 回到 85.7%（v0.2 的公开数字偏乐观）。
# 下面两条是相反方向的锁：词中命中必须消失，**词首前缀命中必须保留**（那是规则有意为之）。

@pytest.mark.parametrize("heading, forbidden", [
    ("Core development principles", "build_test"),             # ci ⊂ principles
    ("Types & TypeScript", "build_test"),                      # script ⊂ TypeScript
    ("Show uncommitted changes", "workflow"),                   # commit ⊂ uncommitted
    ("Learned Information (Dotcom)", "style"),                  # format ⊂ information
    ("3. open the preview", "workflow"),                        # review ⊂ preview
    ("allowBuilds", "build_test"),                              # build ⊂ allowBuilds
])
def test_substring_hits_do_not_tag(heading, forbidden):
    """词中命中不算命中——这是 v0.1.3 修掉的那一类假阳性。"""
    assert forbidden not in analyze_text(f"# {heading}\n\n正文。")["categories"]


@pytest.mark.parametrize("heading, expected", [
    ("Coding Conventions", "style"),            # 截断词干：convention
    ("Critical Boundaries", "boundaries"),      # 截断词干：boundar
    ("Code Ownership Map", "structure"),        # 截断词干：ownership
    ("Testing", "build_test"),                  # 词首前缀：test
    ("Running Tests", "build_test"),            # 词首前缀：run / test
    ("Pre-Commit Requirements", "workflow"),    # 连字符是词边界：commit
    ("CI", "build_test"),                       # 独立词仍要命中
    ("`make` commands", "build_test"),          # 删裸词 make 后，这些写法仍要抓住
    ("Makefile Build (Alternative)", "build_test"),
    ("Prerequisites before `make dev`", "build_test"),
])
def test_word_start_prefix_still_tags(heading, expected):
    """收紧词中命中时，不能把有意为之的词干/前缀规则一起废掉。"""
    assert expected in analyze_text(f"# {heading}\n\n正文。")["categories"]


# U1（v0.1.2）：`is_pointer` 曾被"提到 ≥2 个 .md 文件名"命中——于是"有实质规则但引用了
# 文档"的短章程被当成空壳剔除。11 份人工标注：真 4 / 半 2 / 误 5。
# 下面两个是相反方向的锁：真的指针要抓得住，假的指针不许再抓。

POINTER_LIKE = """# Chroma Codebase Guidelines for AI Agents

See [CLAUDE.md](./CLAUDE.md) for codebase conventions (commit message format, etc.).
"""


def test_true_pointer_is_kept():
    """教科书式转引："See CLAUDE.md"——正文去链接后 100B，没有实质规则。"""
    assert analyze_text(POINTER_LIKE)["is_pointer"] is True


# 形态取自 VoltAgent/voltagent（1200B 正文 + 4 条 docs 链接 + 命令块 + Gotchas）：
# 曾被 U1 判成指针，而它显然承载了实质规则。
NOT_A_POINTER = """# VoltAgent

VoltAgent is an open-source TypeScript framework for building and orchestrating AI agents.

## Overview

- View [`docs/structure.md`](./docs/structure.md) for the repository structure
- View [`docs/tooling.md`](./docs/tooling.md) for development tools
- View [`docs/testing.md`](./docs/testing.md) for testing guidelines
- View [`docs/linting.md`](./docs/linting.md) for formatting and linting

## Validating Changes

To validate your changes you can run the following commands:

```bash
pnpm test:all
pnpm build:all
pnpm lint
```

## Important Notes for AI Agents

1. **Always check existing patterns** before implementing new features
2. **Use the established registry patterns** for agent and tool management
3. **Maintain type safety** - this is a TypeScript-first codebase
4. **Follow the monorepo structure** - changes may impact multiple packages
5. **Test your changes** - ensure all tests pass before committing

## Gotchas

- **JSON.stringify** should never be used; use the `safeStringify` helper instead.
"""


def test_md_mentions_alone_do_not_make_a_pointer():
    """回归 U1：四个 .md 链接 + 正文不到 2KB，但有命令、有规则、有坑——不是空壳。"""
    rec = analyze_text(NOT_A_POINTER)
    assert rec["is_pointer"] is False
    assert rec["categories"], "被判成指针会连带丢掉类别"


def test_pointer_semantic_self_declaration():
    """语义门：作者自陈"本文件不写规则"时，厚度不该救它。"""
    text = ("# AGENTS.md\n\n" + "This file is a thin pointer.\n" * 20
            + "\nAll instructions are in `.github/memories/MEMORY.md`.\n")
    assert analyze_text(text)["is_pointer"] is True


@pytest.mark.xfail(strict=False, reason=(
    "已知边界（LIMITATIONS §10）：208B 正文 + 3 条具体规则仍被薄门判为指针。"
    "修掉它这条会变 XPASS——那时请把它改成普通断言。"))
def test_known_boundary_short_doc_with_rules():
    text = ("# Customer docs\n\nUses **Bun**, not npm or pnpm.\n\n"
            "- When adding a page, register it in `navigation.json`.\n"
            "- FAQs use a `faqItems` frontmatter field. See `billing.mdoc`.\n"
            "- Local build: `bun run build`.\n")
    assert analyze_text(text)["is_pointer"] is False


# U2（v0.1.2）：含「分工/职责/ownership」类标题的 33 个章节里 9 个完全没有标签，
# 而"新代码该放哪里、谁负责哪块"正是 structure 要答的问题。

def test_ownership_map_heading_is_structure():
    text = ("# Agent Map\n\n## Code Ownership Map\n\n"
            "- `packages/client/src` - Vue 3 client, stores, routes, i18n.\n"
            "- `packages/server/src` - Koa API, Socket.IO, persistence.\n")
    assert "structure" in analyze_text(text)["categories"]


def test_strong_patterns_can_be_disabled():
    """回归对比通道：关掉强模式应回到 v0.1 基线行为。"""
    assert "boundaries" in analyze_text(ZH_CHARTER)["categories"]
    off = analyze_text(ZH_CHARTER, strong=False)
    assert off["strong_patterns"] is False
    assert len(off["categories"]) < len(analyze_text(ZH_CHARTER)["categories"])


def test_analyze_file_on_own_readme():
    rec = analyze_file(ROOT / "README.md")
    assert rec["section_count"] > 0 and rec["bytes"] > 0


def test_published_checksums_match():
    """发布资产的 SHA256 必须与仓库里的一致——防止"改了数据忘了改清单"。"""
    sums = ROOT / "data" / "processed" / "SHA256SUMS"
    if not sums.exists():
        pytest.skip("无校验文件")
    import hashlib
    for line in sums.read_text().splitlines():
        digest, name = line.split()
        f = ROOT / "data" / "processed" / name
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        assert got == digest, f"{name} 校验和不符（重新生成后需更新 SHA256SUMS）"


def test_category_counts_are_dense(corpus):
    """九个类别必须全部在场、缺席为 0、顺序固定——稀疏 dict 会在 parquet 里变成 NaN。"""
    rec = analyze_text(ZH_CHARTER)
    assert list(rec["category_counts"]) == list(CATEGORIES)
    assert all(isinstance(v, int) for v in rec["category_counts"].values())
    for d in corpus["category_counts"].tolist():
        assert list(d) == list(CATEGORIES)
        assert not any(v is None for v in d.values())


# --- brief（生成时的检查清单）------------------------------------------

def test_brief_lists_every_category_with_live_base_rates(corpus):
    """清单里的比例必须来自语料库实时计算，不能硬编码。"""
    from agent_charters.brief import render
    out = render([], lang="zh")
    cov = category_coverage(substantive(corpus))
    for c in CATEGORIES:
        assert c in out, c
        assert f"{cov[c]:>5.1f}%" in out, f"{c} 的比例与语料库不一致"
    assert out.count("【") == len(CATEGORIES)


def test_brief_refs_rates_are_live(corpus):
    """外部引用的两个基准率同样必须实时算（D25）——49%/15% 曾是硬编码。"""
    from agent_charters.brief import refs_rates, render
    sub = substantive(corpus)
    n = len(sub)
    routed = round(int(sub["imperative_route"].sum()) * 100 / n)
    hard = round(int(sub["hard_route"].sum()) * 100 / n)
    assert refs_rates(corpus) == (routed, hard)
    out = render([], lang="zh", df=corpus)
    assert f"{routed}% 的章程会转引外部文件" in out
    assert f"{hard}% 指向知识库或规则目录" in out


def test_brief_gap_mode_only_asks_for_missing(tmp_path):
    from agent_charters.brief import render
    f = tmp_path / "AGENTS.md"
    f.write_text("# AGENTS.md\n\n## Build\nRun `pytest`.\n\n## Structure\n`src/`.\n",
                 encoding="utf-8")
    out = render([str(f)], lang="en")
    assert "✗" in out                                   # 缺口被标出
    assert "Cover every one of the following slots" in out
    # 提示词里只应出现缺的项：已覆盖的 build_test 不该再被要求
    prompt = out.split("可直接粘贴的提示词")[1]
    assert "- build_test" not in prompt
    assert "- workflow" in prompt


def test_brief_full_coverage_says_so(tmp_path):
    from agent_charters.brief import render
    f = tmp_path / "AGENTS.md"
    f.write_text("\n".join([
        "# Everything",
        "## Overview\nThis is a project. 技术栈: python. Overview of what this is.",
        "## Architecture 架构与目录\nsrc/ modules 模块 结构",
        "## Build and Test 构建测试\nrun `pytest` and npm run build in CI",
        "## Coding Style 规范\nnaming, format, lint config, code quality, type hints",
        "## Workflow 流程\nconventional commits, git pull then git push, pull request review, release",
        "## Environment 环境\ntoolchain, dependencies, setup, install, config, environment variables",
        "## Boundaries 禁止\n🚫 never commit secrets; **禁止** deleting files; keep this invariant",
        "## Gotchas 陷阱\nknown issue: upstream breaks if you do X; 踩坑 recorded here",
        "## Agent instructions\nyou are an assistant; your role; be concise; ask before acting",
    ]), encoding="utf-8")
    out = render([str(f)], lang="en")
    if "九类全覆盖" in out:
        assert "没有要补的槽位" in out
    else:                       # 有缺口就应给出针对性提示词，两者必居其一
        assert "Cover every one of the following slots" in out


def test_brief_carries_the_measured_pitfall_warning():
    """34% 不是坑、58% 读得出——这两条是实验结论，不许在重构中丢掉。"""
    from agent_charters.brief import render
    for lang in ("zh", "en"):
        out = render([], lang=lang)
        assert "34%" in out
        assert "58%" in out
        assert "workflow 0/11" in out or "11/11" in out


def test_brief_is_deterministic():
    from agent_charters.brief import render
    assert render([], lang="zh") == render([], lang="zh")


# --- 纵向基线 -----------------------------------------------------------

def test_baseline_matches_corpus(corpus):
    """基线快照必须与数据集一致，否则三个月后的纵向对比是在跟错误的对象比。"""
    base = ROOT / "data" / "processed" / "baseline-2026-09-10.tsv"
    if not base.exists():
        pytest.skip("无基线文件")
    rows = {}
    with base.open(encoding="utf-8") as fh:
        import csv
        for r in csv.DictReader(fh, delimiter="\t"):
            rows[r["repo_full_name"]] = r
    assert len(rows) == len(corpus) == 558
    for _, rec in corpus.iterrows():
        assert rows[rec["repo_full_name"]]["file_sha"] == rec["file_sha"]


def test_longitudinal_self_diff_is_zero():
    """拿基线跟当前清单比，必须报 0 变化——这是脚本没写错的证据。"""
    import subprocess
    r = subprocess.run([sys.executable, "work/longitudinal.py"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "**内容已改**      0" in r.stdout
    assert "新增              0" in r.stdout


# --- 可重放性 -----------------------------------------------------------

@pytest.mark.skipif(not MANIFEST.exists(), reason="data/raw 不在仓库里")
def test_jsonl_is_byte_identical_across_hash_seeds(tmp_path):
    """不同 PYTHONHASHSEED 下重跑抽取，产物必须逐字节相同。

    曾经不是：category_counts 的键顺序来自 set 迭代顺序，
    而 set 顺序随字符串哈希随机化——同一份数据两次生成校验和不同，
    发布资产的"可复现"就成了一句空话。
    """
    import os
    import subprocess

    outs = []
    for seed in ("0", "1"):
        outdir = tmp_path / f"seed{seed}"
        env = dict(os.environ, PYTHONHASHSEED=seed,
                   AGENT_CHARTERS_OUT=str(outdir))
        subprocess.run([sys.executable, "work/extract_v1.py"],
                       cwd=ROOT, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        rows = [json.loads(l) for l in
                (outdir / f"agent_charters_{DATASET_VERSION}.jsonl").read_text().splitlines()]
        import pandas as pd
        buf = outdir / "x.parquet"
        pd.DataFrame(rows).to_parquet(buf, index=False, compression="zstd")
        outs.append(((outdir / f"agent_charters_{DATASET_VERSION}.jsonl").read_bytes(),
                     buf.read_bytes()))
    assert outs[0][0] == outs[1][0], "jsonl 不确定：同数据不同哈希种子字节不同"
    assert outs[0][1] == outs[1][1], "parquet 不确定：同数据不同哈希种子字节不同"



def test_corpus_is_reproducible_from_raw(corpus):
    """数据集必须能由 work/extract_v1.py 从 data/raw 重放出来。

    若分类规则被改动却没重新生成数据集，这个测试会失败——这是刻意的刹车。
    """
    if not MANIFEST.exists():
        pytest.skip("data/raw 不在仓库里（发布包精简版）")
    rows = [json.loads(l) for l in MANIFEST.read_text().splitlines()]
    by_sha = {r["file_sha"]: r for r in rows}
    tainted = []
    for i, (_, rec) in enumerate(corpus.iterrows()):
        if i % 7:            # 抽样（约 1/7，够灵敏又不拖慢）
            continue
        src = by_sha[rec["file_sha"]]
        text = Path(src["local_file"]).read_text(encoding="utf-8",
                                                 errors="replace")
        fresh = analyze_text(text)
        if fresh["categories"] != sorted(rec["categories"]):
            tainted.append(rec["repo_full_name"])
    assert not tainted, f"数据集与分类规则不一致（需重跑 work/extract_v1.py）: {tainted[:5]}"


# —— 外部引用检测（refs）——
# 这一组守的是口径：第一版用「文本里出现任意 .md 路径」做信号，507 份里命中 87%，
# 抽验后判定为假阳性机器（README 列表、PR 模板、日志文件名全被算进去）。
# 下面第一条测试就是那个教训的回归锁。

def test_refs_rejects_plain_md_listings():
    """仅仅列出一堆 .md 文件不算"把知识外包"——必须是指去读。"""
    from agent_charters.refs import find_refs
    text = ("## Public Documentation\n\n"
            "Public entry points:\n"
            "- `README.md`\n- `README.en.md`\n- `WHITEPAPER.md`\n\n"
            "Fill in `.github/pull_request_template.md` when opening a PR.\n")
    assert find_refs(text)["routes_outward"] is False


def test_refs_detects_knowledge_store():
    from agent_charters.refs import find_refs
    rec = find_refs("# 规则\n\n改代码前先读 `.github/memories/MEMORY.md`。\n")
    assert rec["hard"] is True and rec["routes_outward"] is True


def test_refs_detects_imperative_routing():
    from agent_charters.refs import find_refs
    assert find_refs("Read ARCHITECTURE.md before touching the runtime.\n")["imperative"]
    assert find_refs("详见 `docs/theme-state-ui.md` 的 State Machine 节。\n")["imperative"]


def test_resolve_targets_three_states(tmp_path):
    from agent_charters.refs import find_refs, resolve_targets
    (tmp_path / ".git").mkdir()          # 假装是个仓库根，否则一律 unverified
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("x")
    (tmp_path / "deep").mkdir()
    (tmp_path / "deep" / "b.md").write_text("x")
    text = "参考 `docs/a.md`、`b.md`、`nowhere.md`。\n"
    got = dict(resolve_targets(find_refs(text), tmp_path))
    assert got["docs/a.md"] == "exists"
    assert got["b.md"] == "by_name"      # 只在 deep/ 下，同名
    assert got["nowhere.md"] == "missing"


def test_brief_reports_external_refs(tmp_path):
    from agent_charters.brief import render
    (tmp_path / ".git").mkdir()
    f = tmp_path / "AGENTS.md"
    f.write_text("# AGENTS.md\n\n## Build\nRun `pytest`.\n\n"
                 "改动前先读 `.github/memories/pitfalls.md`。\n", encoding="utf-8")
    out = render([str(f)], lang="zh")
    assert "外部引用" in out
    assert "pitfalls.md" in out


def test_refs_does_not_cry_wolf_on_global_charters(tmp_path):
    """真用一次发现的假警报：用户级章程指向的是"别的项目的根"。

    ~/.codex/AGENTS.md 写着"必须读并遵守项目根 CODEX.md"，按章程自身目录
    解析必然找不到——宁可说"验不了"，也不要点名报断链。
    """
    from agent_charters.refs import find_refs, resolve_targets
    f = tmp_path / "AGENTS.md"
    f.write_text("干活前必须读并遵守项目根 `CODEX.md`。\n", encoding="utf-8")
    res = resolve_targets(find_refs(f.read_text(encoding="utf-8")), tmp_path)
    assert [st for _, st in res] == ["unverified"]      # 不是 missing


def test_refs_still_reports_missing_inside_a_repo(tmp_path):
    from agent_charters.refs import find_refs, resolve_targets
    (tmp_path / ".git").mkdir()
    f = tmp_path / "AGENTS.md"
    f.write_text("先读 `docs/nope.md`。\n", encoding="utf-8")
    res = dict(resolve_targets(find_refs(f.read_text(encoding="utf-8")), tmp_path))
    assert res["docs/nope.md"] == "missing"


# --- v0.1.7：多义词标题通道 + 容器型标题（2026-09-12，A 主样本第一批）-----
#
# 这一批 bug 全部**只能靠真实正文复现**：合成文本"看起来对"，闸门类回归
# 会绿着把真问题放走（C 组教训，见 work/audit/v0.4-edge-verdicts.md）。
# 所以下面一律直读 data/raw/full 的原文。

def _real_cats(rel: str) -> set[str]:
    """读 data/raw/full/<owner__repo>.md 的真实正文，返回类别集合。"""
    text = (RAW / f"{rel}.md").read_text(encoding="utf-8")
    return set(analyze_text(text)["categories"])


def test_real_usage_heading_does_not_mean_build_test():
    """`usage` 只在标题**就是它**时才算 build_test。

    google/benchmark 的「AI usage」是 AI 使用政策、catatz 的「Color Usage Rules」
    是样式规范、astron-agent 的「Context7 Usage Rules」是工具规定——三份都曾
    只靠 `heading:usage` 拿到 build_test（全篇没有任何构建/测试命令）。
    """
    assert "build_test" not in _real_cats("google__benchmark")
    assert "build_test" not in _real_cats("kupzed__catatz")
    assert "build_test" not in _real_cats("iflytek__astron-agent")
    # 反面：fable-method 的「Usage」是斜杠命令用法，裸词，仍然算 build_test
    assert "build_test" in _real_cats("Sahir619__fable-method")


def test_ai_usage_policy_is_agent_meta_and_boundaries():
    """google/benchmark 是九类里最纯的 agent_meta 样本，此前 0 命中还倒贴 build_test。"""
    cats = _real_cats("google__benchmark")
    assert "agent_meta" in cats, cats
    assert "boundaries" in cats, cats


def test_real_start_here_is_not_overview():
    """`Start Here` 是导航段（阅读顺序/文档指针/纪律），不是项目概览。

    全库 7 份靠它拿 overview 的文件**全部**是误标（逐个读过原文）。
    """
    for rel in ("Kevandrew__sophia", "openclaw__Peekaboo", "ayghri__i-have-adhd",
                "fallow-rs__fallow", "botiverse__hands", "NanmiCoder__cc-haha"):
        assert "overview" not in _real_cats(rel), rel
    # 容器型标题单独出现时也不该产生 overview
    assert "overview" not in analyze_text(
        "# A\n\n## Start Here\n\n- 先读 `README.md`。\n")["categories"]


def test_real_dependency_topology_is_not_environment():
    """依赖的**拓扑/方向/角色**是架构；依赖的**管理/版本/安全**才是环境。"""
    assert "environment" not in _real_cats("langchain-ai__langgraph")
    assert "structure" in _real_cats("langchain-ai__langgraph")
    assert "environment" not in _real_cats("charmbracelet__crush")
    # 反面：钉版本、供应链姿态、Dependabot 维护仍是 environment
    assert "environment" in _real_cats("triggerdotdev__trigger.dev")
    assert "environment" in _real_cats("owncloud__notes")
    assert "environment" in _real_cats("hotosm__ui")


def test_real_howto_heading_is_workflow_not_structure():
    """`## Adding a new core module` 是流程，不是结构描述。"""
    cats = _real_cats("vcz-Gray__loophaus")
    assert "workflow" in cats, cats
    assert "structure" in cats, cats          # Project Structure 一节仍在


def test_real_module_naming_and_module_scope_are_not_structure():
    """裸词 module 太泛：命名规范是 style，i18n 陷阱是 gotchas。"""
    assert "structure" not in _real_cats("stablyai__orca")
    assert "style" in _real_cats("stablyai__orca")
    assert "structure" not in _real_cats("thunderbird__thunderbolt")


def test_prose_docker_compose_is_not_a_command():
    """正文里提到 `Docker Compose` 不是构建命令（astron-agent 的目录清单误命中）。"""
    prose = ("# A\n\n## Repository Structure\n\n- `docker` - Docker Compose and related "
             "infrastructure configuration\n")
    assert "build_test" not in analyze_text(prose)["categories"]
    assert "build_test" not in _real_cats("langgenius__dify")
    cmd = "# A\n\n## 部署\n\n```bash\ndocker compose up -d\n```\n"
    assert "build_test" in analyze_text(cmd)["categories"]
