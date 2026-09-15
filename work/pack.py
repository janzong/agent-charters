"""把抽取结果打成两件东西：发布用的 parquet，与随包的 jsonl.gz。

用法: .venv/bin/python work/pack.py

输出:
  data/processed/agent-charters-<DS>.parquet      发布资产（SHA256SUMS 钉住）
  agent_charters/data/agent-charters-<DS>.jsonl.gz 随包语料（CLI 读的就是它）

为什么随包那份不是 parquet（0.4.0 改）：读 parquet 要 pandas + pyarrow（≈62 MB），
而 CLI 只需要那张表本身——装包因此从 62 MB 降到几百 KB。jsonl.gz 解压后与
data/processed/agent_charters_<DS>.jsonl **逐字节相同**（有测试钉着），
所以"随包副本与发布副本是同一份数据"这条不变。
"""
import gzip
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
    # 随包那份：jsonl.gz（纯标准库可读），解压后与 data/processed 的 jsonl 逐字节相同。
    # mtime=0 是为了让 gz 里不带打包时间（否则每次打包字节都不同）。
    # ⚠️ 别指望"同样输入压出同样字节"：gzip 的输出随 zlib 版本变（py3.10 与 py3.12 就不同）。
    pkg = Path(f"agent_charters/data/agent-charters-{DATASET_VERSION}.jsonl.gz")
    pkg.parent.mkdir(parents=True, exist_ok=True)
    pkg.write_bytes(gzip.compress(src.read_bytes(), compresslevel=9, mtime=0))
    print(f"{len(df)} 行 x {len(df.columns)} 列 -> {out}")
    print(f"                               -> {pkg}（随包）")
    print(f"文件大小 {out.stat().st_size / 1024:.1f} KB"
          f"（随包 jsonl.gz {pkg.stat().st_size / 1024:.1f} KB）")
    print("\n列清单:")
    for c in df.columns:
        print(f"  {c:<24} {str(df[c].dtype):<10} 非空 {df[c].notna().sum()}")


if __name__ == "__main__":
    main()
