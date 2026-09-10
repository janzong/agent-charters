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

from agent_charters import analyze_file, analyze_text, load_corpus, substantive  # noqa: E402
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


# --- 可重放性 -----------------------------------------------------------

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
