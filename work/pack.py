"""把抽取结果打成 parquet（发布格式）。

用法: .venv/bin/python work/pack.py
输出: data/processed/agent-charters-<DATASET_VERSION>.parquet
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_charters.extract import DATASET_VERSION  # noqa: E402


def main() -> None:
    src = Path(f"data/processed/agent_charters_{DATASET_VERSION}.jsonl")
    rows = [json.loads(l) for l in src.read_text().splitlines()]
    df = pd.DataFrame(rows)
    # list/dict 列在 parquet 里保留为列，便于下游直接展开
    out = Path(f"data/processed/agent-charters-{DATASET_VERSION}.parquet")
    df.to_parquet(out, index=False, compression="zstd")
    # 随包发布的那一份必须与仓库里的一致，否则 CLI 与数据集会对不上
    pkg = Path(f"agent_charters/data/agent-charters-{DATASET_VERSION}.parquet")
    pkg.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(pkg, index=False, compression="zstd")
    print(f"{len(df)} 行 x {len(df.columns)} 列 -> {out}")
    print(f"                               -> {pkg}（随包）")
    print(f"文件大小 {out.stat().st_size / 1024:.1f} KB")
    print("\n列清单:")
    for c in df.columns:
        print(f"  {c:<24} {str(df[c].dtype):<10} 非空 {df[c].notna().sum()}")


if __name__ == "__main__":
    main()
