#!/usr/bin/env python
"""把审计样本 + 原文 + 译文打包成一个单文件 HTML 工作台。

产物 work/ui/workbench.html 不依赖网络/服务器：拷到任何机器双击即可用
（Mac 上直接用浏览器打开）。译文在 251 预生成并缓存，Mac 侧不需要 API key。

身份键说明（2026-09-12 修正）：`file_sha` 是内容哈希，空壳文件有 30 个仓库共用一个
sha（9 字节空文件），只按 sha join 会张冠李戴。故一律用 (repo, file_path) 作身份键。

用法：
  .venv/bin/python work/ui/build_workbench.py                     # 全部 5 个分区
  .venv/bin/python work/ui/build_workbench.py --sections blind    # 只做盲判 20
  .venv/bin/python work/ui/build_workbench.py --no-translate      # 只出英文
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "ui"))
from i18n import Translator  # noqa: E402

CATS = [
    ("overview", "概览"),
    ("structure", "架构"),
    ("build_test", "构建测试"),
    ("style", "风格"),
    ("workflow", "流程"),
    ("environment", "环境"),
    ("boundaries", "禁令"),
    ("gotchas", "坑"),
    ("agent_meta", "AI行为"),
]
# (分区短名, 样本文件里的键, 界面名, 列表前缀)
SECTIONS = [
    ("main", "main", "主样本 55", "主"),
    ("zh", "zh_census", "中文普查 26", "中"),
    ("edge", "edge", "边界件 10", "边"),
    ("rare", "rare_boost", "稀有加成 9", "稀"),
    ("blind", "blind20", "盲判组 20", "盲"),
    ("blind_zh", "blind_zh", "盲判·中文 10", "中盲"),
    ("blind_zh2", "blind_zh2", "盲判·中文二组 16", "中盲2"),
]


# ---------- markdown 轻量切块 ----------
def split_blocks(text: str) -> list[dict]:
    blocks, buf, in_code = [], [], False
    lines = text.split("\n")
    for ln in lines + [""]:
        if ln.strip().startswith("```"):
            if in_code:
                buf.append(ln)
                blocks.append({"k": "code", "t": "\n".join(buf)})
                buf, in_code = [], False
            else:
                if buf:
                    blocks.extend(_prose(buf))
                    buf = []
                buf, in_code = [ln], True
            continue
        if in_code:
            buf.append(ln)
            continue
        if not ln.strip():
            if buf:
                blocks.extend(_prose(buf))
                buf = []
        else:
            buf.append(ln)
    return blocks


def _prose(lines: list[str]) -> list[dict]:
    first = lines[0].lstrip()
    m = re.match(r"^(#{1,6})\s+(.*)$", first)
    if m and len(lines) == 1:
        return [{"k": "h", "lvl": len(m.group(1)), "t": m.group(2).strip()}]
    bullet = re.match(r"^\s*([-*+]|\d+\.)\s+", lines[0])
    if bullet and all(re.match(r"^\s*([-*+]|\d+\.)\s+", ln) or ln.startswith("  ") for ln in lines):
        return [{"k": "ul", "t": lines}]
    return [{"k": "p", "t": "\n".join(lines)}]


def prose_texts(blocks: list[dict]) -> list[str]:
    out = []
    for b in blocks:
        if b["k"] == "p":
            out.append(b["t"])
        elif b["k"] == "ul":
            out.append("\n".join(b["t"]))
    return out


def ident_key(repo: str, path: str) -> str:
    return f"{repo}|{path}"


# ---------- 数据装配 ----------
def load_entries(sections: list[str]) -> list[dict]:
    df = pd.read_parquet(ROOT / "data/processed/agent-charters-v0.4.parquet")
    sample = json.loads((ROOT / "work/audit/v0.4-sample.json").read_text("utf-8"))
    by_key = {ident_key(r.repo_full_name, r.file_path): r for r in df.itertuples()}

    entries, blockcache = [], {}
    for short, skey, label, prefix in SECTIONS:
        if short not in sections:
            continue
        for no, ident in enumerate(sample["identity"][skey], 1):
            key = ident_key(ident["repo"], ident["file_path"])
            row = by_key.get(key)
            if row is None:
                print(f"[warn] {key} 不在 v0.4 数据集里，跳过", file=sys.stderr)
                continue
            if key not in blockcache:
                raw = ROOT / "data" / "raw" / "full" / (ident["repo"].replace("/", "__") + ".md")
                blockcache[key] = (
                    split_blocks(raw.read_text("utf-8", errors="replace")) if raw.exists() else []
                )
            cats = [c for c, _ in CATS if c in set(row.categories)]
            entries.append(
                {
                    "key": key,
                    "sec": short,
                    "secname": label,
                    "prefix": prefix,
                    "no": no,
                    "sha": ident["sha"],
                    "repo": ident["repo"],
                    "file_path": ident["file_path"],
                    "bytes": int(row.bytes),
                    "sections": int(row.section_count),
                    "stars": int(row.repo_stars),
                    "lang": row.doc_language,
                    "license": "" if pd.isna(row.license) else str(row.license),
                    "cats": cats,
                    "blocks": blockcache[key],
                }
            )
    return entries


def dashboard_stats(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["_k"] = df.repo_full_name + "|" + df.file_path
    base = df[df.is_substantive & ~df.is_pointer]
    n = len(base)
    cov = {k: round(100.0 * base.categories.apply(lambda a: k in a).sum() / n, 1) for k, _ in CATS}
    hist = []
    for ver in ["v0.2", "v0.3", "v0.4"]:
        p = ROOT / f"data/processed/agent-charters-{ver}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        d["_k"] = d.repo_full_name + "|" + d.file_path
        d = d[d._k.isin(base._k)]
        m = len(d)
        hist.append(
            {
                "ver": ver,
                "n": m,
                "cov": {
                    k: round(100.0 * d.categories.apply(lambda a: k in a).sum() / m, 1)
                    for k, _ in CATS
                },
            }
        )
    return {
        "total": int(len(df)),
        "base_n": int(n),
        "empty": int((~df.is_substantive).sum()),
        "pointer": int((df.is_substantive & df.is_pointer).sum()),
        "cov": cov,
        "hist": hist,
        "lang": {k: int(v) for k, v in df.doc_language.value_counts().items()},
        "tier": {k: int(v) for k, v in df.size_tier.value_counts().items()},
        "cats": [{"key": k, "label": v} for k, v in CATS],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--sections",
        "--groups",
        dest="sections",
        default="main,zh,edge,rare,blind,blind_zh,blind_zh2",
    )
    ap.add_argument("--out", default=str(ROOT / "work/ui/workbench.html"))
    ap.add_argument("--no-translate", action="store_true")
    args = ap.parse_args()
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]

    df = pd.read_parquet(ROOT / "data/processed/agent-charters-v0.4.parquet")
    entries = load_entries(sections)
    print(f"[build] {len(entries)} 行（工作表口径），{sum(e['bytes'] for e in entries)} 字节")

    if args.no_translate:
        for e in entries:
            for b in e["blocks"]:
                if b["k"] in ("p", "ul"):
                    b["zh"] = ""
    else:
        tr = Translator(ROOT / "work/ui/cache/i18n.json")
        all_texts = list(dict.fromkeys(t for e in entries for t in prose_texts(e["blocks"])))
        _cjk = lambda t: sum(1 for ch in t if '\u4e00' <= ch <= '\u9fff') / max(1, len(t))
        _before = len(all_texts)
        all_texts = [t for t in all_texts if _cjk(t) < 0.25]  # 中文段落不送翻译
        print(f"[i18n] 跳过中文段落 {_before - len(all_texts)} 段")
        print(f"[i18n] 待译段落 {len(all_texts)}（缓存命中 {tr.hits}）")
        got = tr.translate(all_texts, label=f"{len(entries)}行")
        tr.flush()
        miss = sum(1 for t in all_texts if not got.get(t))
        print(f"[i18n] 完成，未译段落 {miss}")
        for e in entries:
            for b in e["blocks"]:
                if b["k"] == "p":
                    b["zh"] = got.get(b["t"], "")
                elif b["k"] == "ul":
                    b["zh"] = got.get("\n".join(b["t"]), "")

    payload = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "sections": {s: lab for s, _, lab, _ in SECTIONS if s in sections},
        "entries": entries,
        "stats": dashboard_stats(df),
    }
    tpl = (ROOT / "work/ui/template.html").read_text("utf-8")
    html = tpl.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    pathlib.Path(args.out).write_text(html, "utf-8")
    print(f"[build] 写出 {args.out} ({pathlib.Path(args.out).stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
