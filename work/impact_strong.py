"""回归量化：强模式通道对 v0.1 语料库分类的影响。

用法: .venv/bin/python work/impact_strong.py
输出: 各类别覆盖率变化 + 变动的文件数 + 中文文档明细
（一次性分析脚本，不参与发布流水线。）
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json

from agent_charters.extract import analyze_text, doc_language
from agent_charters.taxonomy import CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "full"
MANIFEST = ROOT / "data" / "raw" / "full_manifest.jsonl"

meta_by_file = {}
for line in MANIFEST.read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        meta_by_file[r.get("file_name") or r.get("slug")] = r

rows = []
for f in sorted(RAW.glob("*.md")):
    text = f.read_text(encoding="utf-8", errors="replace")
    off = analyze_text(text, {"file_path": f.name}, strong=False)
    on = analyze_text(text, {"file_path": f.name}, strong=True)
    rows.append((f.name, off, on))

sub = [(n, a, b) for n, a, b in rows
       if a["is_substantive"] and not a["is_pointer"]]
print(f"总 {len(rows)} 份 ｜ 实质 {len(sub)} 份 "
      f"（与语料库 507 对齐检查）\n")

n = len(sub)
print(f"{'类别':<14}{'无强模式':>8}{'有强模式':>8}{'增量':>7}   变动文件")
print("-" * 62)
for c in CATEGORIES:
    a = sum(1 for _, o, _ in sub if c in o["categories"])
    b = sum(1 for _, _, p in sub if c in p["categories"])
    changed = sum(1 for _, o, p in sub if c in p["categories"] and c not in o["categories"])
    print(f"{c:<14}{a*100//n:>7}%{b*100//n:>7}%{changed:>7}   {changed}")
print("-" * 62)
tot_a = sum(len(o['categories']) for _, o, _ in sub) / n
tot_b = sum(len(p['categories']) for _, _, p in sub) / n
print(f"平均标签数 {tot_a:.2f} → {tot_b:.2f}")

# 中文文档：强模式的主要救济对象
zh = [(nm, o, p) for nm, o, p in sub if o["doc_language"] in ("zh", "mixed")]
print(f"\n中文/混合文档 {len(zh)} 份")
better = worse = 0
for nm, o, p in zh:
    da = len(o["categories"]); db = len(p["categories"])
    if db > da: better += 1
    elif db < da: worse += 1
print(f"  标签增多 {better} 份 ｜ 标签减少 {worse} 份")

# 强模式独有贡献的样例（只看中文）
print("\n中文文档：强模式新捞出来的类别（前 12 份）")
shown = 0
for nm, o, p in sorted(zh, key=lambda x: -(len(x[2]['categories']) - len(x[1]['categories']))):
    new = sorted(set(p["categories"]) - set(o["categories"]))
    if not new:
        continue
    print(f"  {nm:<48} +{','.join(new)}")
    shown += 1
    if shown >= 12:
        break

# 英文侧是否有反例（强模式不该在英文文档上乱加）
en_new = Counter()
for nm, o, p in sub:
    if o["doc_language"] == "en":
        for c in set(p["categories"]) - set(o["categories"]):
            en_new[c] += 1
print("\n英文文档被强模式新增的类别计数（假阳性观察窗口）")
for c, k in en_new.most_common():
    print(f"  {c:<14}{k}")
