"""内容级抽取器：把 data/raw/full 的 558 份章程变成结构化数据集。

用法: .venv/bin/python work/extract_v1.py
输出: data/processed/agent_charters_v0.1.jsonl + data/processed/extract_report.md

设计：
  - 分类/切分逻辑**不在本文件**，全部委托给 agent_charters.extract.analyze_text，
    保证"随包发布的工具"与"生成语料库的脚本"用同一套规则（单一事实源）。
  - 本文件只负责：遍历清单、补数据集级字段（去重计数）、写 jsonl、生成报告。
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_charters.extract import EXTRACTOR_VERSION, analyze_text  # noqa: E402
from agent_charters.taxonomy import CATEGORIES, VERSION  # noqa: E402

# 抓取快照日期。判据 2 要求每行都带 retrieved_at（可追溯）。
# 注意：这与 commit_date（仓库最后推送时间）不同——后者是内容的时间，前者是采集的时间。
RETRIEVED_AT = "2026-09-10"


def main() -> None:
    outdir = Path("data/processed")
    outdir.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in
            Path("data/raw/full_manifest.jsonl").read_text().splitlines()]

    sha_counts = Counter(r["file_sha"] for r in rows)
    records = []
    cat_doc_count: Counter = Counter()
    cat_item_count: Counter = Counter()

    for r in rows:
        text = Path(r["local_file"]).read_text(encoding="utf-8", errors="replace")
        rec = analyze_text(text, {
            "repo_full_name": r["repo_full_name"],
            "file_path": r["file_path"],
            "file_sha": r["file_sha"],
            "commit_date": r.get("repo_pushed_at"),
            "retrieved_at": RETRIEVED_AT,
            "repo_stars": r["repo_stars"],
            "repo_language": r["repo_language"],
            "license": r["license"],
        })
        # 数据集级字段（需要跨行信息，单文件分析算不出来）
        rec["duplicate_sha_count"] = sha_counts[r["file_sha"]]
        rec["extractor_version"] = EXTRACTOR_VERSION
        records.append(rec)

        if rec["is_substantive"]:
            for t in rec["categories"]:
                cat_doc_count[t] += 1
                cat_item_count[t] += rec["category_counts"][t]

    out = outdir / "agent_charters_v0.1.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n = len(records)
    valid = [r for r in records if r["is_substantive"]]
    usable = [r for r in valid if not r["is_pointer"]]
    no_tag = [r for r in usable if not r["categories"]]
    lines = [
        "# 抽取报告 extract_v1", "",
        f"- 总记录 {n}，其中实质内容 {len(valid)}"
        f"（排除转引用后可用于分类统计 {len(usable)}），非实质 {n - len(valid)}",
        f"- 无任何类别标签的实质文件 {len(no_tag)}",
        f"- 内容重复文件（sha 出现>1 次）{sum(1 for r in records if r['duplicate_sha_count'] > 1)}",
        f"- 分类规则版本 {VERSION} ｜ 抽取器 {EXTRACTOR_VERSION}"
        f" ｜ 强模式通道 on",
        "", "## 类别分布（实质文件数 / 标签出现次数）", "",
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
