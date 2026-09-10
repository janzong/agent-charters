"""把抽取结果打成 parquet（发布格式）。

用法: .venv/bin/python work/pack.py
输出: data/processed/agent-charters-v0.1.parquet
"""
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    src = Path("data/processed/agent_charters_v0.1.jsonl")
    rows = [json.loads(l) for l in src.read_text().splitlines()]
    df = pd.DataFrame(rows)
    # list/dict 列在 parquet 里保留为列，便于下游直接展开
    out = Path("data/processed/agent-charters-v0.1.parquet")
    df.to_parquet(out, index=False, compression="zstd")
    print(f"{len(df)} 行 x {len(df.columns)} 列 -> {out}")
    print(f"文件大小 {out.stat().st_size / 1024:.1f} KB")
    print("\n列清单:")
    for c in df.columns:
        print(f"  {c:<24} {str(df[c].dtype):<10} 非空 {df[c].notna().sum()}")


if __name__ == "__main__":
    main()
