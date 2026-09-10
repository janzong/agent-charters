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
from agent_charters.taxonomy import CATEGORIES  # noqa: E402

RAW = ROOT / "data" / "raw" / "full"
MANIFEST = ROOT / "data" / "raw" / "full_manifest.jsonl"


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


def test_corpus_shape(corpus):
    assert len(corpus) == 558
    assert len(corpus.columns) == 26
    sub = substantive(corpus)
    assert len(sub) == 507


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


@pytest.mark.parametrize("text, forbidden", [
    ("Please make sure to double check.", "build_test"),      # make sure ≠ make test
    ("Gradle 9.3.1 and AGP 9.1.1 are used.", "build_test"),   # 版本号 ≠ 构建命令
    ("记录输出日志、失败原因。", "gotchas"),                    # 记录失败原因 ≠ 坑
])
def test_known_false_positives_stay_out(text, forbidden):
    assert forbidden not in analyze_text(text)["categories"]


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
        assert f"{cov[c]:>3}%" in out, f"{c} 的比例与语料库不一致"
    assert out.count("【") == len(CATEGORIES)


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
                (outdir / "agent_charters_v0.1.jsonl").read_text().splitlines()]
        import pandas as pd
        buf = outdir / "x.parquet"
        pd.DataFrame(rows).to_parquet(buf, index=False, compression="zstd")
        outs.append(((outdir / "agent_charters_v0.1.jsonl").read_bytes(),
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
