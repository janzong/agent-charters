#!/usr/bin/env python3
"""分母研究：AGENTS.md 这类"写给 AI 的书面规约"的**生态率**（此前所有百分比都是框内率）。

设计见 `work/audit/plan-prevalence.md`（预登记）。两个框：

  框 A（主指标 + 趋势）：按**创建世代**（2010..2026 每年随机取一周/日/时切片）
      查 `created:<切片> pushed:>cutoff fork:false archived:false`，分页取尽，
      切片内随机抽 N 个仓库 → 拉一次递归树 → 看有没有 AGENTS.md。
      ⇒ p_active = P(有 AGENTS.md | 近 90 天有 push、非 fork、非 archived)

  框 B（存量率，无偏）：`GET /repositories/{id}` 在 [1, 上界] 上均匀抽 ID。

每仓库一次 `GET /repos/{r}/git/trees/HEAD?recursive=1`（递归，才看得见 `docs/AGENTS.md`）。
失败**不写缓存**（filetype_probe 踩过：失败记账 → 重跑永久跳过）。
所有响应缓存到 `data/cache/prevalence/`（gitignore），重跑零成本。

用法：
  .venv/bin/python work/prevalence.py active [--per-gen 50] [--seed 20260918]
  .venv/bin/python work/prevalence.py stock  [--n 1000] [--seed 20260918]
  .venv/bin/python work/prevalence.py report          # 只用缓存出数
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import pathlib
import random
import re
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/cache/prevalence"
SEARCH_CACHE = CACHE / "search"
TREE_CACHE = CACHE / "trees"

CUTOFF_DAYS = 90
KINDS = {
    "AGENTS.md": re.compile(r"(^|/)AGENTS\.md$", re.I),
    "CLAUDE.md": re.compile(r"(^|/)CLAUDE\.md$", re.I),
    "cursor": re.compile(r"(^|/)(\.cursorrules|\.cursor/rules/.+\.mdc)$"),
    "copilot": re.compile(r"(^|/)\.github/copilot-instructions\.md$", re.I),
}
API = "https://api.github.com"


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


# 连接复用（urllib 每次重握手，慢了 20 倍）；并发压到 6，别撞次级限流。
_SESSION = requests.Session()
_SESSION.mount("https://", requests.adapters.HTTPAdapter(pool_connections=8, pool_maxsize=8))
_HEAD = {"Accept": "application/vnd.github+json",
         "User-Agent": "agent-charters-prevalence/1.0"}


class SecondaryLimit(Exception):
    pass


_PACE_T = [0.0]
_PACE_L = threading.Lock()
PACE = 0.12          # 全局最小请求间隔（秒）；**串行**请求（并发会撞次级限流）
BACKOFF = [0.0]      # 撞到次级限流后的全局静默截止时刻


def _pace() -> None:
    with _PACE_L:
        now = time.monotonic()
        dt_ = max(_PACE_T[0], BACKOFF[0]) - now
        if dt_ > 0:
            time.sleep(dt_)
        _PACE_T[0] = time.monotonic() + PACE


def _get(url: str, tok: str, timeout: int = 30) -> dict:
    _pace()
    r = _SESSION.get(url, headers={**_HEAD, "Authorization": f"Bearer {tok}"}, timeout=timeout)
    if r.status_code == 403 and "Repository access blocked" in r.text:
        # 单个仓库被 GitHub 以 ToS/DMCA 封禁（**不是**限流，也不是"没有这个仓库"）。
        # 稳定状态 → 可以记账，但它不该混进分母（没法学）。
        return {"_error": "blocked-tos"}
    if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
        return {"_error": "ratelimit-403"}
    if r.status_code in (403, 429):
        raise SecondaryLimit(f"{r.headers.get('Retry-After', '30')}|{url}|{r.text[:240]}")
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- 缓存层

def cached_json(path: pathlib.Path, fetch, retries: int = 12):
    """命中缓存直接返回；**只有成功（拿到 JSON）才落盘**。"""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    last = None
    for attempt in range(retries):
        try:
            d = fetch()
        except SecondaryLimit as e:                   # 次级限流：**全局**静默 60s，不记账
            with _PACE_L:
                BACKOFF[0] = max(BACKOFF[0], time.monotonic() + 60)
            print(f"  [次级限流] 全局静默 60s …{str(e)[:300]}", flush=True)
            last = SecondaryLimit("global")
            continue
        except requests.HTTPError as e:
            code = e.response.status_code
            if code in (403, 429):
                time.sleep(3 * (attempt + 1))
                last = e
                continue
            if code == 422:
                raise
            d = {"_error": f"HTTP {code}"}            # 404/409/451 是真没有，可记账
        except Exception as e:                        # noqa: BLE001 网络异常 → 重试，不记账
            last = e
            time.sleep(1 + attempt)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return d
    if last is not None:
        raise last
    return None


def search_repos(q: str, tok: str, page: int = 1, per_page: int = 100) -> dict:
    key = hashlib.sha1(f"{q}|{page}|{per_page}".encode()).hexdigest()[:16]
    url = (f"{API}/search/repositories?q={urllib.parse.quote(q)}"
           f"&per_page={per_page}&page={page}")
    return cached_json(SEARCH_CACHE / f"{key}.json", lambda: _get(url, tok))


def repo_by_id(rid: int, tok: str) -> dict:
    return cached_json(CACHE / "ids" / f"{rid}.json",
                       lambda: _get(f"{API}/repositories/{rid}", tok))


def tree(repo: str, tok: str) -> dict:
    return cached_json(TREE_CACHE / (repo.replace("/", "__") + ".json"),
                       lambda: _get(f"{API}/repos/{repo}/git/trees/HEAD?recursive=1", tok))


def raw_search_one(q: str, tok: str) -> dict:
    """只取 total_count 的轻查询（不缓存 items）。"""
    return search_repos(q, tok, page=1, per_page=1)


# ---------------------------------------------------------------- 框 A

def generations(seed: int) -> list[tuple[int, dt.date, dt.date]]:
    """2010..2026 每年随机取一周（周一..周日）。"""
    rng = random.Random(f"gen-{seed}")
    out = []
    for year in range(2010, 2027):
        d = dt.date(year, 1, 1) + dt.timedelta(days=rng.randrange(365 - 7))
        mon = d - dt.timedelta(days=d.weekday())
        out.append((year, mon, mon + dt.timedelta(days=6)))
    return out


def _iso(d: dt.date, hour: int | None = None) -> str:
    if hour is None:
        return d.strftime("%Y-%m-%d")
    return f"{d.strftime('%Y-%m-%d')}T{hour:02d}:00:00Z"


def _iso_end(d: dt.date, hour: int | None = None) -> str:
    if hour is None:
        return d.strftime("%Y-%m-%d")
    return f"{d.strftime('%Y-%m-%d')}T{hour:02d}:59:59Z"


def slice_query(lo: str, hi: str, cutoff: str) -> str:
    return (f"created:{lo}..{hi} pushed:>{cutoff} fork:false archived:false")


def resolve_slice(mon: dt.date, cutoff: str, tok: str,
                  rng: random.Random) -> tuple[str, int, str]:
    """把切片收敛到 total_count ≤ 1000（周 → 随机一日 → 随机一小时）。"""
    q = slice_query(_iso(mon), _iso(mon + dt.timedelta(days=6)), cutoff)
    for gran, lo_end in ((("周", None), None), (("日", None), None)):
        n = raw_search_one(q, tok)["total_count"]
        if n <= 1000:
            return q, n, gran[0]
        time.sleep(2.2)
        if gran[0] == "周":
            day = mon + dt.timedelta(days=rng.randrange(7))
            q = slice_query(_iso(day), _iso(day), cutoff)
            mono = day
        else:
            h = rng.randrange(24)
            q = slice_query(_iso(mono, h), _iso_end(mono, h), cutoff)
            return q, raw_search_one(q, tok)["total_count"], "时"
    return q, raw_search_one(q, tok)["total_count"], "时"


def paginate(q: str, tok: str, cap: int = 10) -> list[dict]:
    items, page = [], 1
    while page <= cap:
        d = search_repos(q, tok, page=page)
        got = d.get("items", [])
        items.extend(got)
        if len(got) < 100:
            break
        page += 1
        time.sleep(2.2)                                    # 搜索 30/min
    return items


def run_active(args) -> None:
    tok = token()
    cutoff = (dt.date.today() - dt.timedelta(days=CUTOFF_DAYS)).isoformat()
    rng = random.Random(f"slice-{args.seed}")
    picked, meta = [], []
    for year, mon, sun in generations(args.seed):
        q, total, gran = resolve_slice(mon, cutoff, tok, rng)
        time.sleep(2.2)
        items = paginate(q, tok)
        if len(items) < total:                              # 取尽失败（>10 页或限流）
            print(f"  ! {year}: total={total} 只取到 {len(items)}，降权标注")
        k = min(args.per_gen, len(items))
        sample = rng.sample(items, k) if items else []
        picked.extend((year, r["full_name"]) for r in sample)
        meta.append({"year": year, "week_start": mon.isoformat(), "query": q,
                     "total_count": total, "fetched": len(items), "granularity": gran,
                     "sampled": k})
        print(f"  {year} 切片 {gran:1s} total={total:>5} 取到 {len(items):>4} 抽 {k:>3}")
        time.sleep(2.2)

    (CACHE / "active_slices.json").write_text(
        json.dumps({"cutoff": cutoff, "seed": args.seed, "slices": meta},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    reachable = [r for _, r in picked]
    print(f"\n拉树：{len(reachable)} 个仓库（16 线程）…")
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(lambda r: tree(r, tok), reachable))
    print("树拉完。跑 report 出数。")
    (CACHE / "active_sample.json").write_text(
        json.dumps([{"year": y, "repo": r} for y, r in picked],
                   ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- 框 B

def since_probe(since: int, tok: str) -> int:
    """`GET /repositories?since=N` 返回 id ≥ N 的一批（升序）；空 ⇒ N 超过上界。"""
    d = cached_json(CACHE / "since" / f"{since}.json",
                    lambda: _get(f"{API}/repositories?since={since}&per_page=1", tok))
    return len(d) if isinstance(d, list) else -1


def id_upper_bound(tok: str) -> int:
    """二分找"最大存在的仓库 id"（约 31 次核心调用）。"""
    lo, hi = 1, 2_000_000_000
    while lo < hi:
        mid = (lo + hi + 1) // 2
        n = since_probe(mid, tok)
        if n > 0:
            lo = mid
        elif n == 0:
            hi = mid - 1
        else:
            raise RuntimeError(f"since={mid} 返回异常")
    return lo


def run_stock(args) -> None:
    tok = token()
    rng = random.Random(f"stock-{args.seed}")
    top = id_upper_bound(tok)
    print(f"仓库 id 上界 = {top}")
    found: list[int] = []
    tried = 0
    budget = args.n * 6
    while len(found) < args.n and tried < budget:
        batch = [rng.randrange(1, top + 1)
                 for _ in range(min(40, budget - tried))]
        tried += len(batch)
        def safe(i: int):
            try:
                return (i, repo_by_id(i, tok))
            except Exception:                          # noqa: BLE001 极少数拿不到就跳过
                return (i, None)

        res = [safe(i) for i in batch]              # 串行：GitHub 要求单用户不并发
        for i, d in res:
            if isinstance(d, dict) and d.get("full_name"):
                found.append(i)
        if tried % 400 < 40:
            print(f"  探测 {tried} 命中 {len(found)}"
                  f"（{len(found) * 100 / (tried or 1):.0f}%）", flush=True)
    (CACHE / "stock_ids.json").write_text(
        json.dumps({"upper_bound": top, "seed": args.seed, "tried": tried,
                    "ids": found}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"命中 {len(found)}/{tried}（命中率 {len(found) * 100 / (tried or 1):.0f}%）")

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda i: repo_by_id(i, tok), found))

    # 全量落档（fork / archived / 活跃与否都要，报告里要分开算）
    rows = []
    for rid in found:
        d = repo_by_id(rid, tok)
        rows.append({"id": rid, "repo": d["full_name"], "fork": bool(d.get("fork")),
                     "archived": bool(d.get("archived")),
                     "created_at": d.get("created_at"), "pushed_at": d.get("pushed_at"),
                     "size": d.get("size"), "stars": d.get("stargazers_count")})
    (CACHE / "stock_sample.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"落档 {len(rows)} 条，拉树…")
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        list(ex.map(lambda r: tree(r["repo"], tok), rows))
    print("树拉完。跑 report-stock 出数。")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% 区间（小比例必备，正态近似会给出负下限）。"""
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def run_report_stock(args) -> None:
    ids = json.loads((CACHE / "stock_ids.json").read_text(encoding="utf-8"))
    rows = json.loads((CACHE / "stock_sample.json").read_text(encoding="utf-8"))
    cutoff = (dt.date.today() - dt.timedelta(days=CUTOFF_DAYS)).isoformat()
    cuts: dict[str, list] = {}

    def bucket(name: str, pred) -> None:
        cuts.setdefault(name, []).extend(r for r in rows if pred(r))

    cuts["全部公开仓库"] = list(rows)
    bucket("非 fork", lambda r: not r["fork"])
    bucket("非 fork 非 archived", lambda r: not r["fork"] and not r["archived"])
    bucket("近 90 天有 push（含 fork）", lambda r: (r["pushed_at"] or "") >= cutoff)
    bucket("活跃（非 fork 非 archived + 90 天）",
           lambda r: not r["fork"] and not r["archived"] and (r["pushed_at"] or "") >= cutoff)

    print(f"\n=== 框 B：存量率（id 均匀抽样，seed {ids['seed']}，id 上界 {ids['upper_bound']}）===")
    print(f"探测 {ids['tried']} 次命中 {len(ids['ids'])}"
          f"（命中率 {len(ids['ids']) * 100 / (ids['tried'] or 1):.0f}%）")
    print(f"  {'子总体':<28}{'n':>6}{'AGENTS.md':>12}{'95% CI':>18}{'CLAUDE.md':>11}")
    for name in ["全部公开仓库", "非 fork", "非 fork 非 archived", "近 90 天有 push（含 fork）",
                 "活跃（非 fork 非 archived + 90 天）"]:
        rs = cuts[name]
        ok = [(r, kinds_of(r["repo"])) for r in rs]
        ok = [(r, c) for r, c in ok if c["status"] == "ok"]
        k = sum(1 for _, c in ok if c["hit"]["AGENTS.md"])
        kc = sum(1 for _, c in ok if c["hit"]["CLAUDE.md"])
        lo, hi = wilson(k, len(ok))
        print(f"  {name:<28}{len(ok):>6}{k:>7} {fmt_pct(k, len(ok)):>4}"
              f"  [{lo * 100:4.1f},{hi * 100:4.1f}]{kc:>6}"
              f" {fmt_pct(kc, len(ok))}")
    n_fork = sum(1 for r in rows if r["fork"])
    n_arch = sum(1 for r in rows if r["archived"])
    n_act = sum(1 for r in rows if (r["pushed_at"] or "") >= cutoff)
    print(f"\n  成分：fork {n_fork * 100 / len(rows):.0f}%｜archived {n_arch * 100 / len(rows):.0f}%"
          f"｜近 90 天有 push {n_act * 100 / len(rows):.0f}%")
    for k in KINDS:
        if k == "AGENTS.md":
            continue
        kk = sum(1 for r in rows if kinds_of(r["repo"])["status"] == "ok"
                 and kinds_of(r["repo"])["hit"][k])
        print(f"  全样本 {k:<12} {kk:>4}/{len(rows)} = {fmt_pct(kk, len(rows))}")


# ---------------------------------------------------------------- 报告

def kinds_of(repo: str) -> dict:
    f = TREE_CACHE / (repo.replace("/", "__") + ".json")
    if not f.exists():
        return {"status": "missing"}
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("_error"):
        return {"status": "error", "error": d["_error"]}
    if "tree" not in d:
        return {"status": "error", "error": "no tree"}
    blobs = [n["path"] for n in d["tree"] if n.get("type") == "blob"]
    return {"status": "ok", "blobs": len(blobs),
            "truncated": bool(d.get("truncated")),
            "hit": {k: any(p.search(b) for b in blobs) for k, p in KINDS.items()}}


def fmt_pct(a: int, b: int) -> str:
    return f"{a * 100 / b:5.1f}%" if b else "  n/a"


def run_report(args) -> None:
    sp = CACHE / "active_sample.json"
    if not sp.exists():
        raise SystemExit("没有 active_sample.json，先跑 active")
    rows = json.loads(sp.read_text(encoding="utf-8"))
    meta = json.loads((CACHE / "active_slices.json").read_text(encoding="utf-8"))
    per_year: dict[int, list] = {}
    pooled = {"ok": 0, "missing": 0, "error": 0, "truncated": 0}
    hits = {k: 0 for k in KINDS}
    for r in rows:
        c = kinds_of(r["repo"])
        pooled[c["status"]] = pooled.get(c["status"], 0) + 1
        per_year.setdefault(r["year"], []).append(c)
        if c["status"] == "ok":
            if c["truncated"]:
                pooled["truncated"] += 1
            for k, v in c["hit"].items():
                hits[k] += bool(v)
    print(f"\n=== 框 A：活跃率（cutoff {meta['cutoff']}，seed {meta['seed']}）===")
    print(f"样本 {len(rows)}｜拿到树 ok={pooled['ok']}｜404/409={pooled['missing']}"
          f"｜其它错误={pooled['error']}｜其中 truncated={pooled['truncated']}")
    ok = pooled["ok"]
    for k in KINDS:
        lo, hi = wilson(hits[k], ok)
        print(f"  {k:<14} {hits[k]:>4}/{ok} = {fmt_pct(hits[k], ok)}"
              f"  95% CI [{lo * 100:4.1f}, {hi * 100:4.1f}]")
    # 交叉表：AGENTS.md × CLAUDE.md（"聚焦面该不该换"直接读这张表）
    both = sum(1 for r in rows if (c := kinds_of(r["repo"]))["status"] == "ok"
               and c["hit"]["AGENTS.md"] and c["hit"]["CLAUDE.md"])
    only_c = sum(1 for r in rows if (c := kinds_of(r["repo"]))["status"] == "ok"
                 and c["hit"]["CLAUDE.md"] and not c["hit"]["AGENTS.md"])
    print(f"\n  AGENTS∩CLAUDE {both}｜只在 CLAUDE {only_c}"
          f"｜条件率 P(CLAUDE|AGENTS) = {fmt_pct(both, hits['AGENTS.md'])}")
    print("\n 世代  切片total 抽n  有AGENTS.md")
    for y in sorted(per_year):
        cs = [c for c in per_year[y] if c["status"] == "ok"]
        h = sum(1 for c in cs if c["hit"]["AGENTS.md"])
        sl = next((m for m in meta["slices"] if m["year"] == y), {})
        lo, hi = wilson(h, len(cs))
        print(f"  {y}  {sl.get('total_count', 0):>8} {len(cs):>4}  {h:>3} / {len(cs):<3}"
              f" {fmt_pct(h, len(cs))}  [{lo * 100:4.1f},{hi * 100:4.1f}]")
    early = [c for y in per_year if y <= 2022 for c in per_year[y] if c["status"] == "ok"]
    late = [c for y in per_year if y == 2026 for c in per_year[y] if c["status"] == "ok"]
    pe = sum(1 for c in early if c["hit"]["AGENTS.md"]) / (len(early) or 1)
    pl = sum(1 for c in late if c["hit"]["AGENTS.md"]) / (len(late) or 1)
    print(f"\n  趋势 p_2026/p_≤2022 = {pl:.3f}/{pe:.3f} = {(pl / pe if pe else float('inf')):.2f}×")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["active", "stock", "report", "report-stock", "probe"])
    ap.add_argument("--per-gen", type=int, default=50)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260918)
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    if args.mode == "active":
        run_active(args)
    elif args.mode == "report":
        run_report(args)
    elif args.mode == "report-stock":
        run_report_stock(args)
    elif args.mode == "probe":
        tok = token()
        print(json.dumps(raw_search_one(
            slice_query("2026-01-05", "2026-01-11",
                        (dt.date.today() - dt.timedelta(days=CUTOFF_DAYS)).isoformat()),
            tok), ensure_ascii=False)[:400])
    else:
        run_stock(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
