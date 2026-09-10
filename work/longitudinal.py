"""纵向对比：把一次新的抓取结果与基线快照比对。

用法:
  .venv/bin/python work/longitudinal.py                 # 与基线自身比（应报 0 变化，自检）
  .venv/bin/python work/longitudinal.py <基线.tsv> [新清单.jsonl]

基线: data/processed/baseline-2026-09-10.tsv
新清单: data/raw/full_manifest.jsonl（重抓后覆盖它，或另存新路径）

为什么要有这个脚本：
  本项目的定位之一是"非自动可推导内容的分布"。机器写的章程正在变多，
  但**没有任何一次抓取能测出这个变化**——只有纵向对比能。
  基线的价值只随时间增长，今天不存，三个月后就没有对照组。
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path("data/processed/baseline-2026-09-10.tsv")
MANIFEST = Path("data/raw/full_manifest.jsonl")


def load_baseline(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            rows[r["repo_full_name"]] = r
    return rows


def load_manifest(path: Path) -> dict[str, dict]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows[r["repo_full_name"]] = r
    return rows


def main(base_path: Path = BASE, manifest_path: Path = MANIFEST) -> None:
    base = load_baseline(base_path)
    new = load_manifest(manifest_path)

    added = sorted(set(new) - set(base))
    gone = sorted(set(base) - set(new))
    same, changed = [], []
    for repo in sorted(set(base) & set(new)):
        if base[repo]["file_sha"] == new[repo]["file_sha"]:
            same.append(repo)
        else:
            changed.append(repo)

    print(f"基线 {len(base)} 个仓库 ｜ 新抓 {len(new)} 个\n")
    print(f"  未变（sha 相同）  {len(same)}")
    print(f"  **内容已改**      {len(changed)}")
    print(f"  消失（抓不到）    {len(gone)}")
    print(f"  新增              {len(added)}")
    if changed:
        print("\n内容变化的仓库（前 20）:")
        for r in changed[:20]:
            print(f"  {r:<45} {base[r]['file_sha'][:8]} -> {new[r]['file_sha'][:8]}"
                  f"  {int(base[r]['bytes'])}B -> ")
        print("  → 这是「人有动作」的证据；再看新增里有多少是模板/机器产物")
    if gone:
        print("\n消失的仓库（前 10）:", ", ".join(gone[:10]))

    # 机器写/模板化的粗信号（基于新抓的 sha 分布）
    sha_groups = Counter(r["file_sha"] for r in new.values())
    clusters = {k: v for k, v in sha_groups.items() if v > 1}
    print(f"\n新抓里同 sha 成簇: {len(clusters)} 组，涉及 {sum(clusters.values())} 份"
          f"（基线是 3 组 / 34 份）")
    tiny = [r for r in new.values() if int(r.get("bytes", 0)) < 100]
    print(f"新抓里 <100B 的文件: {len(tiny)}（基线：40 份非实质，其中 30 份是 9 字节指针）")
    print("\n判据：内容变化数、新增里的模板簇——这两个数随时间上升，"
          "就是「章程在被批量生成」的直接证据。")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(Path(args[0]) if args else BASE,
         Path(args[1]) if len(args) > 1 else MANIFEST)
