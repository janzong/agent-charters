#!/usr/bin/env python3
"""按季取一期「纵向面板」快照，并算出三个正交指标。

设计见 `work/longitudinal-plan.md`（决策 **D42**）。三条纪律必须守住：
  1. **TSV 与 T0 同 schema**（`baseline-2026-09-10.tsv`）—— 面板只加期、不改框。
  2. **死者留档**：404 / 归档 / 文件消失都写进表里、**永不删**；
     抓取抖动（限流 / 断流）**不算死亡**，标 unknown 等下次。
  3. **不发全文**：原文只落本机 `data/cache/panel/<date>/`（`.gitignore`）。
     留一份原文快照是有意的 —— "采集时没算的派生字段，事后补不回来"（D42 第 2 条）。

用法:
  .venv/bin/python work/panel_run.py --date 2026-12-10 --limit 5      # 试跑
  .venv/bin/python work/panel_run.py --date 2026-12-10                # 出新一期
  .venv/bin/python work/panel_run.py --date 2026-12-10 --report-only  # 不联网，只算指标
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_charters.extract import EXTRACTOR_VERSION, doc_language  # noqa: E402
from agent_charters.taxonomy import RULESET_VERSION  # noqa: E402

PROCESSED = ROOT / "data/processed"
CACHE = ROOT / "data/cache/panel"
T0 = PROCESSED / "baseline-2026-09-10.tsv"

# 与 T0 完全一致的列（**不许在这里加列**；额外信息一律进 panel-<date>.json）
COLS = ["repo_full_name", "file_path", "file_sha", "bytes", "doc_language", "retrieved_at"]
SAFE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
BATCH = 50
SHOW_CLUSTERS = [0]   # --show-clusters 用（模块级全局，避免到处穿参）


def gh_token() -> str:
    p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("拿不到 gh token：先 `gh auth login`")
    return p.stdout.strip()


def gql(query: str, timeout: int = 240) -> dict:
    """一次 GraphQL。gh 在响应带 errors 时也可能非 0 退出 —— 只要 stdout 是可解析 JSON 就用它。"""
    p = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query],
                       capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout)
    except Exception:
        raise RuntimeError("graphql 失败：" + (p.stderr or p.stdout)[:300])


def build_query(batch: list[str]) -> str:
    parts = []
    for i, repo in enumerate(batch):
        owner, name = repo.split("/")
        parts.append(
            f'r{i}: repository(owner: "{owner}", name: "{name}") {{'
            " nameWithOwner isArchived isDisabled stargazerCount pushedAt"
            ' object(expression: "HEAD:AGENTS.md") { ... on Blob { oid byteSize text } } }'
        )
    return "query {\n" + "\n".join(parts) + "\n}"


def rest_repo(repo: str, tok: str) -> tuple[dict | None, str]:
    """给"GraphQL 说没有"的仓库做一次落点确认：urllib 会跟随 301，
    最后一跳的 URL 不同 ⇒ 它是**改名/搬家**，不是死了。"""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Authorization": f"Bearer {tok}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "agent-charters-panel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), r.geturl()
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, f"ERR {type(e).__name__}"


def fetch_period(frame: list[str], date: str, tok: str, limit: int) -> dict[str, dict]:
    todo = frame[:limit] if limit else frame
    out: dict[str, dict] = {}
    cache_dir = CACHE / date
    cache_dir.mkdir(parents=True, exist_ok=True)
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    for bi, batch in enumerate(batches, 1):
        bad = [r for r in batch if not SAFE.match(r)]
        for r in bad:
            out[r] = {"status": "unknown", "note": "仓库名含非法字符，未查询"}
        batch = [r for r in batch if r not in bad]
        if not batch:
            continue
        print(f"[{bi}/{len(batches)}] 查 {len(batch)} 个仓库 …", flush=True)
        try:
            resp = gql(build_query(batch))
        except Exception as e:  # noqa: BLE001 —— 网络类失败：**不算死亡**
            for r in batch:
                out[r] = {"status": "unknown", "note": f"batch 失败 {e}"[:120]}
            continue
        data = (resp or {}).get("data") or {}
        for i, repo in enumerate(batch):
            node = data.get(f"r{i}")
            if not node:
                # 先别判死：可能是改名，也可能只是这一跳没拿到
                info, where = rest_repo(repo, tok)
                if info is None and where == "HTTP 404":
                    out[repo] = {"status": "dead", "note": where}
                elif info is None:
                    out[repo] = {"status": "unknown", "note": where}
                elif info.get("full_name", "").lower() != repo.lower():
                    out[repo] = {"status": "moved", "moved_to": info["full_name"],
                                 "archived": bool(info.get("archived")),
                                 "stars": info.get("stargazers_count"),
                                 "pushed_at": info.get("pushed_at")}
                else:
                    out[repo] = {"status": "unknown", "note": "rest 拿到了但 gql 没有"}
                continue
            blob = node.get("object")
            rec = {"archived": bool(node.get("isArchived")),
                   "disabled": bool(node.get("isDisabled")),
                   "stars": node.get("stargazerCount"),
                   "pushed_at": node.get("pushedAt")}
            if not blob:
                rec["status"] = "missing"          # 仓库在，AGENTS.md 没了
            else:
                rec["status"] = "archived" if rec["archived"] else "ok"
                rec["file_sha"] = blob.get("oid")
                text = blob.get("text")
                if text is not None:
                    # `bytes` 的定义 = **文本按 LF 归一后的 utf-8 字节数**（与 T0 一致）。
                    # 为什么不用 GraphQL 的 byteSize：①它对 CRLF 文件给的是"真实字节数"，
                    # T0 那一列却是 LF 归一后的长度（实测差的就是 CR 个数：artemis 差 52、uview-plus 差 11）；
                    # ②正文含 NUL 时，GraphQL 的 `text` 会把 NUL 写成两字节的 `^@`（REST raw blob 不会，
                    # 实测 1/558：`momozi1996/momo-code`）。口径钉在"我们手里的文本"上，跨期才可比；
                    # 真实 byteSize 另存 sidecar 的 `byte_size_gql` 备查，差异由 `text_lossy` 标出。
                    lf = text.replace("\r\n", "\n").replace("\r", "\n")
                    n_bytes = len(lf.encode("utf-8"))
                    rec["bytes"] = n_bytes
                    rec["byte_size_gql"] = blob.get("byteSize")
                    rec["text_lossy"] = n_bytes != blob.get("byteSize")
                    rec["doc_language"] = doc_language(text)
                    (cache_dir / (repo.replace("/", "__") + ".md")).write_text(
                        text, encoding="utf-8")
                else:
                    rec["bytes"] = blob.get("byteSize")
            out[repo] = rec
    return out


def load_tsv(path: pathlib.Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as fh:
        return {r["repo_full_name"]: r for r in csv.DictReader(fh, delimiter="\t")}


def pick_prev(date: str, explicit: str | None) -> pathlib.Path | None:
    if explicit:
        return pathlib.Path(explicit)
    cands = sorted(p for p in PROCESSED.glob("baseline-*.tsv") if p.name.split("-", 1)[1][:10] < date)
    return cands[-1] if cands else None


def compute(prev: dict[str, dict], meta: dict[str, dict]) -> dict:
    rows = {"alive": 0, "dead": 0, "moved": 0, "missing": 0, "archived": 0, "unknown": 0}
    for repo, m in meta.items():
        rows[m.get("status", "unknown")] = rows.get(m.get("status", "unknown"), 0) + 1
    same = changed = new = 0
    stable = 0
    for repo, m in meta.items():
        if m.get("status") not in ("ok", "archived"):
            continue
        old = prev.get(repo)
        if old is None:
            new += 1
        elif old.get("file_sha") == m.get("file_sha"):
            same += 1
            if m.get("pushed_at") and m["pushed_at"][:10] > old.get("retrieved_at", ""):
                stable += 1
        else:
            changed += 1
    sha_seen = Counter(m["file_sha"] for m in meta.values()
                       if m.get("file_sha") and m.get("status") in ("ok", "archived"))
    clusters = {sha: n for sha, n in sha_seen.items() if n > 1}
    cluster_names = {}
    for sha in clusters:
        cluster_names[sha] = sorted(r for r, m in meta.items() if m.get("file_sha") == sha)
    return {"counts": rows, "same": same, "changed": changed, "new": new,
            "stable": stable, "templates": len(clusters),
            "template_repos": sum(clusters.values()), "clusters": cluster_names}


def print_report(date: str, prev_name: str, m: dict) -> None:
    c = m["counts"]
    live = c["ok"] + c["archived"]
    print(f"\n=== 面板 {date}（对照 {prev_name}）===")
    print(f"存活率   {live}/{live + c['dead'] + c['moved'] + c['missing']}"
          f"   （dead {c['dead']} ｜ moved {c['moved']} ｜ missing {c['missing']}）")
    print(f"活跃率   ok {c['ok']} ｜ archived {c['archived']}")
    print(f"内容     未变 {m['same']} ｜ **已改 {m['changed']}** ｜ 新入框 {m['new']}")
    print(f"语义稳态 有 push 但 sha 未变：{m['stable']}（分母=未变 {m['same']}）")
    print(f"模板簇   同 sha 出现 >1 次的 sha 数 {m['templates']}，涉及 {m['template_repos']} 个仓库")
    if c["unknown"]:
        print(f"⚠️ unknown {c['unknown']} 个（网络抖动，**不算死亡**）—— 重跑补齐再下结论")
    if SHOW_CLUSTERS[0] and m["clusters"]:
        print("模板簇（同 sha 多仓库）:")
        for sha, names in sorted(m["clusters"].items(), key=lambda kv: -len(kv[1])):
            if len(names) < 2:
                continue
            print(f"   {sha[:10]} × {len(names):>3}: {', '.join(names[:6])}"
                  + (" …" if len(names) > 6 else ""))


def verify(date: str, meta: dict) -> None:
    """自证：把本地缓存文本重新算成 git blob sha，与 GraphQL 给的 oid 对拍。

    这道检查是**必须的** —— 它正是发现"GraphQL 的 text 会把 NUL 写成 `^@`"的那件工具；
    没有它，我们会以为本地副本与远端逐字节相同。
    """
    cache_dir = CACHE / date
    ok = bad = 0
    bad_list = []
    for repo, m in meta.items():
        if not m.get("file_sha"):
            continue
        f = cache_dir / (repo.replace("/", "__") + ".md")
        if not f.exists():
            continue
        raw = f.read_bytes()
        if hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest() == m["file_sha"]:
            ok += 1
        else:
            bad += 1
            bad_list.append(repo)
    print(f"自证   缓存文本 = 远端 blob：一致 {ok} ｜ 不一致 {bad}"
          + ("（text_lossy：本体被服务端改写过，sha 仍以远端为准）" if bad else ""))
    for r in bad_list[:5]:
        print(f"       - {r}")



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="本期日期，如 2026-12-10（默认今天；timer 用）")
    ap.add_argument("--frame", default=str(T0), help="面板框（默认 T0 基线）")
    ap.add_argument("--prev", default=None, help="对照期 tsv（默认：日期在本期之前的最新一份）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写任何文件")
    ap.add_argument("--show-clusters", type=int, default=0, help="打印前 N 个模板簇的仓库名")
    ap.add_argument("--report-only", action="store_true", help="不联网，用已有产物算指标")
    args = ap.parse_args()
    args.date = args.date or datetime.date.today().isoformat()
    SHOW_CLUSTERS[0] = args.show_clusters

    frame = list(load_tsv(pathlib.Path(args.frame)))
    prev_path = pick_prev(args.date, args.prev)
    out_tsv = PROCESSED / f"baseline-{args.date}.tsv"
    out_json = PROCESSED / f"panel-{args.date}.json"

    prev = load_tsv(prev_path) if prev_path else {}

    if args.report_only:
        if not out_json.exists():
            raise SystemExit(f"没有 {out_json}，先跑一次不带 --report-only 的")
        meta = json.loads(out_json.read_text(encoding="utf-8"))["repos"]
    else:
        meta = fetch_period(frame, args.date, gh_token(), args.limit)
    if args.report_only or args.dry_run:
        print_report(args.date, prev_path.name if prev_path else "（无对照期）", compute(prev, meta))
        return 0

    wrote = {**json.loads(out_json.read_text(encoding="utf-8"))["repos"], **meta} \
        if out_json.exists() else meta
    with out_tsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, delimiter="\t")
        w.writeheader()
        for repo in frame:
            m = wrote.get(repo, {})
            p = prev.get(repo, {})
            w.writerow({"repo_full_name": repo, "file_path": "AGENTS.md",
                        "file_sha": m.get("file_sha", ""),
                        "bytes": m.get("bytes", ""),
                        "doc_language": m.get("doc_language") or p.get("doc_language", ""),
                        "retrieved_at": args.date})
    out_json.write_text(json.dumps(
        {"date": args.date, "frame": str(args.frame), "rows": len(frame),
         "ruleset_version": RULESET_VERSION, "extractor_version": EXTRACTOR_VERSION,
         "repos": wrote}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已写 {out_tsv.name}（{len(frame)} 行，T0 同 schema）与 {out_json.name}")
    print_report(args.date, prev_path.name if prev_path else "（无对照期）", compute(prev, wrote))
    verify(args.date, wrote)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
