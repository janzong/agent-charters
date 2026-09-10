"""T0 校准用的规则分类器（v0，仅基于标题匹配）。

目的不是最终分类，而是**暴露分类法的盲区**：
哪些标题无法归入现有 9 类。
用法: .venv/bin/python work/classify_v0.py
"""
import json
import re
from pathlib import Path

CATEGORIES = {
    "overview":     ["overview", "purpose", "what this project", "tech stack",
                     "introduction", "about", "background", "quick reference",
                     "quick start", "start here", "project"],
    "structure":    ["architecture", "structure", "layout", "repository map",
                     "directory", "module", "source"],
    "build_test":   ["test", "build", "command", "ci", "lint", "run", "make",
                     "compile", "install"],
    "style":        ["style", "convention", "naming", "format", "guideline"],
    "workflow":     ["workflow", "pull request", "commit", "branch", "review",
                     "release", "version"],
    "environment":  ["environment", "tool", "setup", "dependency", "cmake",
                     "config", "skill"],
    "boundaries":   ["boundar", "rule", "never", "do not", "must not",
                     "hygiene", "restriction", "constraint"],
    "decisions":    ["decision", "settled", "adr", "rationale", "choice"],
    "agent_meta":   ["agent", "ai ", "assistant", "you are", "tone", "instruction"],
}

HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


def classify_heading(text: str) -> list[str]:
    low = text.lower()
    return [name for name, keys in CATEGORIES.items() if any(k in low for k in keys)]


def main() -> None:
    manifest = [json.loads(l) for l in
                Path("data/raw/samples_manifest.jsonl").read_text().splitlines()]
    unmatched: dict[str, int] = {}
    per_cat: dict[str, int] = {k: 0 for k in CATEGORIES}
    rows = []

    for item in manifest:
        path = Path(item["local_file"])
        text = path.read_text(encoding="utf-8", errors="replace")
        heads = [m.group(2).strip() for m in
                 (HEADING.match(l) for l in text.splitlines()) if m]
        tags: set[str] = set()
        for h in heads:
            hit = classify_heading(h)
            if hit:
                tags.update(hit)
            else:
                key = h.lower()[:48]
                unmatched[key] = unmatched.get(key, 0) + 1
        for t in tags:
            per_cat[t] += 1
        rows.append({"repo": item["repo_full_name"], "bytes": item["bytes"],
                     "n_headings": len(heads), "tags": sorted(tags)})

    total = len(rows)
    print(f"样本数 = {total}\n")
    print("各类别命中文件数（多标签，故合计 > 样本数）:")
    for name, cnt in sorted(per_cat.items(), key=lambda x: -x[1]):
        print(f"  {name:<12} {cnt:>3}  ({cnt * 100 // total}%)")

    no_tag = [r for r in rows if not r["tags"]]
    print(f"\n一个标签都没落到的文件: {len(no_tag)}")
    for r in no_tag[:10]:
        print(f"  {r['repo']} ({r['bytes']}B, {r['n_headings']} headings)")

    print("\n=== 无法归类的标题 Top 30（分类法盲区）===")
    for h, c in sorted(unmatched.items(), key=lambda x: -x[1])[:30]:
        print(f"  {c:>3}  {h}")

    Path("work/classify_v0.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
