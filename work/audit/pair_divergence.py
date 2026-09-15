#!/usr/bin/env python3
"""同一仓库两份章程的**分歧**实测（最小验证，**只读**）。

问题：`AGENTS.md`（Codex/Cursor/我们的 Action 读）与 `CLAUDE.md`（Claude Code 读）在同一仓库里
往往**不是同一份东西**。这轮先做最小验证：**这种分歧里有多少是真有价值的矛盾**，而不是"那份更长"这种废话。
答案决定要不要做 §STATE §5 里的选项 3（跨文件一致性产物）。

方法：
  1. 从 `data/cache/trees/*.json`（`filetype_probe.py` 的产物）挑"根级、非符号链接、内容不同"的成对文件；
  2. 按尺寸比分三档取样（近似 → 差一截 → 极端）：近似的最可能藏着真矛盾，极端的能暴露指针/空壳；
  3. 下两份正文（blob API，按 sha 取，缓存到 `data/cache/blobs/`），跑两件事：
     - 九类覆盖对照（我们自己的工具）；
     - **槽位对照**：包管理器 / 测试 / 格式化 / lint / 合并策略 / 提交规范 / CI / 锁文件 八类"选择位"，
       两份里都有但**取值不同** ⇒ **冲突**；只有一份有 ⇒ **单边缺失**。

用法：`.venv/bin/python work/audit/pair_divergence.py [--pairs 18]`
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import difflib
import json
import pathlib
import re
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
TREES = ROOT / "data/cache/trees"
BLOBS = ROOT / "data/cache/blobs"

# 槽位＝"这件事只能有一种做法"的选择位。取值互相排斥，两份文档给不同取值 ⇒ 真冲突。
SLOTS: dict[str, dict[str, str]] = {
    "包管理器": {"npm": r"\bnpm\b", "pnpm": r"\bpnpm\b", "yarn": r"\byarn\b", "bun": r"\bbun\b",
                 "poetry": r"\bpoetry\b", "uv": r"\buv\s+(?:sync|run|add)\b",
                 "pip": r"\bpip install\b", "go modules": r"\bgo (?:mod|get|build)\b",
                 "cargo": r"\bcargo\b"},
    "测试": {"pytest": r"\bpytest\b", "jest": r"\bjest\b", "vitest": r"\bvitest\b",
             "mocha": r"\bmocha\b", "go test": r"\bgo test\b", "cargo test": r"\bcargo test\b",
             "rspec": r"\brspec\b", "phpunit": r"\bphpunit\b"},
    "格式化": {"prettier": r"\bprettier\b", "black": r"\bblack\b", "ruff format": r"ruff format",
               "gofmt": r"\bgofmt\b", "rustfmt": r"\brustfmt\b", "dprint": r"\bdprint\b"},
    "lint": {"eslint": r"\beslint\b", "ruff": r"\bruff\b", "flake8": r"\bflake8\b",
             "clippy": r"\bcargo clippy\b|\bclippy\b", "golangci": r"golangci",
             "pylint": r"\bpylint\b", "mypy": r"\bmypy\b", "biome": r"\bbiome\b"},
    "合并策略": {"squash": r"\bsquash\b", "rebase": r"\brebase\b", "merge commit": r"\bmerge commit\b"},
    "提交规范": {"conventional": r"conventional commit", "commitizen": r"commitizen",
                 "中文提交": r"提交(?:信息|说明).{0,6}(?:中文|汉字)", "emoji": r"\bemoji\b"},
    "CI": {"github actions": r"github actions|\.github/workflows", "gitlab ci": r"gitlab ci|\.gitlab-ci",
           "circleci": r"circleci", "jenkins": r"jenkins", "buildkite": r"buildkite"},
    "锁文件": {"package-lock": r"package-lock\.json", "pnpm-lock": r"pnpm-lock\.yaml",
               "yarn.lock": r"yarn\.lock", "bun.lock": r"bun\.lockb?",
               "poetry.lock": r"poetry\.lock", "uv.lock": r"uv\.lock", "Cargo.lock": r"Cargo\.lock"},
}
POINTER = re.compile(r"^\s*@\.?/?.+\.md\s*$|^\s*(?:Read|See|Follow)\s+`?CLAUDE\.md`?", re.I)

# 槽位内的**互斥族**：只有同一族里取值不同才算冲突（"一边多写了个 pip"不算冲突，那是单边信息）。
FAMILIES: dict[str, list[set[str]]] = {
    "包管理器": [{"npm", "pnpm", "yarn", "bun"}, {"poetry", "pip", "uv"},
                 {"go modules"}, {"cargo"}],
    "测试": [{"pytest"}, {"jest", "vitest", "mocha"}, {"go test"}, {"cargo test"},
             {"rspec"}, {"phpunit"}],
    "lint": [{"eslint", "biome"}, {"ruff", "flake8", "pylint", "mypy"}, {"clippy"},
             {"golangci"}],
    "合并策略": [{"squash"}, {"rebase"}, {"merge commit"}, {"squash", "rebase", "merge commit"}],
}


def real_conflicts(slot: str, va: set[str], vc: set[str]) -> list[str]:
    """同一互斥族里两边的取值都非空、且不相交 ⇒ 真冲突。"""
    out = []
    for fam in FAMILIES.get(slot, []):
        a, c = va & fam, vc & fam
        if a and c and not (a & c):
            out.append(f"{slot}: {'/'.join(sorted(a))} vs {'/'.join(sorted(c))}")
    return out


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


def fetch(repo: str, sha: str, tok: str) -> str | None:
    BLOBS.mkdir(parents=True, exist_ok=True)
    f = BLOBS / f"{sha}.txt"
    if f.exists():
        return f.read_text(encoding="utf-8", errors="replace")
    url = f"https://api.github.com/repos/{repo}/git/blobs/{sha}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.raw",
        "User-Agent": "agent-charters-probe/1.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8", errors="replace")
            f.write_text(data, encoding="utf-8", errors="replace")
            return data
        except Exception:  # noqa: BLE001
            continue
    return None


def pairs(n: int) -> list[tuple[str, dict, dict]]:
    out = []
    for f in TREES.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("_error"):
            continue
        repo = f.stem.replace("__", "/")
        blobs = {x["path"]: x for x in d.get("tree", []) if x.get("type") == "blob"}
        a, c = blobs.get("AGENTS.md"), blobs.get("CLAUDE.md")
        if not a or not c or a.get("mode") == "120000" or c.get("mode") == "120000":
            continue
        if a["sha"] == c["sha"]:
            continue
        out.append((repo, a, c))
    # 按尺寸比取样：近似 8 对 / 差一截 6 对 / 极端 4 对（默认 18 对）
    def ratio(t):
        a, c = t[1].get("size", 1), t[2].get("size", 1)
        return max(a, c) / max(min(a, c), 1)
    out.sort(key=ratio)
    # 分档取样：近似 45% / 差一截 33% / 极端 22%（档位随 --pairs 缩放，别写死）
    bands = [(1.0, 2.0, max(1, round(n * 0.45))), (2.0, 10.0, max(1, round(n * 0.33))),
             (10.0, 1e9, max(1, n - round(n * 0.45) - round(n * 0.33)))]
    picked: list[tuple[str, dict, dict]] = []
    for lo, hi, k in bands:
        band = [t for t in out if lo <= ratio(t) < hi]
        step = max(1, len(band) // max(k, 1))
        picked += band[::step][:k]
    return picked[:n] if n else picked


def lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def similarity(ta: str, tc: str) -> tuple[float, int, int]:
    """两份文档有多像（行级 difflib），以及各自**独有**的行数。

    为什么必须是这个指标：光看尺寸/九类会把"CLAUDE.md 只是 AGENTS.md 的拷贝"算成一对样本，
    那样既高估了增量（选项 2），也高估了分歧（选项 3）。
    """
    la, lc = lines(ta), lines(tc)
    ratio = difflib.SequenceMatcher(None, la, lc, autojunk=True).ratio()
    sa, sc = set(la), set(lc)
    return round(ratio, 3), len(sa - sc), len(sc - sa)


def slots(text: str) -> dict[str, set[str]]:
    return {name: {v for v, rx in vals.items() if re.search(rx, text, re.I)}
            for name, vals in SLOTS.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=18)
    args = ap.parse_args()
    chosen = pairs(args.pairs)
    tok = token()
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        texts = list(ex.map(lambda t: (fetch(t[0], t[1]["sha"], tok), fetch(t[0], t[2]["sha"], tok)),
                            chosen))
    from agent_charters.extract import analyze_text
    print(f"取样 {len(chosen)} 对（根级、非链接、内容不同）｜缓存 {len(list(BLOBS.glob('*.txt'))) } 份正文\n")
    conflicts_total = onesided_total = 0
    rows, stats = [], []
    for (repo, a, c), (ta, tc) in zip(chosen, texts):
        if ta is None or tc is None:
            print(f"⚠ {repo}：正文没下到（跳过）")
            continue
        sa, sc = slots(ta), slots(tc)
        conflicts, onesided = [], []
        for name in SLOTS:
            va, vc = sa[name], sc[name]
            conflicts += real_conflicts(name, va, vc)
            if va and vc and va != vc and not conflicts:
                pass  # 一边多列取值 ⇒ 算单边信息（下面按"多出来的那侧"记）
            elif va and not vc:
                onesided.append(f"AGENTS.md 独有 {name}: {sorted(va)}")
            elif vc and not va:
                onesided.append(f"CLAUDE.md 独有 {name}: {sorted(vc)}")
            elif va != vc:
                extra_a, extra_c = va - vc, vc - va
                if extra_a:
                    onesided.append(f"AGENTS.md 多写 {name}: {sorted(extra_a)}")
                if extra_c:
                    onesided.append(f"CLAUDE.md 多写 {name}: {sorted(extra_c)}")
        conflicts_total += len(conflicts)
        onesided_total += len(onesided)
        ca = sorted(analyze_text(ta)["categories"])
        cc = sorted(analyze_text(tc)["categories"])
        ptr = "指针" if (len(tc) < 400 and POINTER.search(tc)) else ""
        sim, only_a, only_c = similarity(ta, tc)
        # 分类顺序有讲究：**先认出"其中一份不携带信息"**（指针/空壳/子集），
        # 否则它们会被计成"两份不同"，把真分歧的规模估高（第一版就这么高估了）。
        stub = min(only_a, only_c)
        if ptr or len(ta) < 400 or len(tc) < 400 or stub <= 3:
            kind = "指针/空壳/单边子集"
        elif sim >= 0.8:
            kind = "近重复"
        elif min(only_a, only_c) < 10:
            kind = "一边是另一边的摘录"
        else:
            kind = "真分叉（两边都有独有内容）"
        stats.append((repo, a.get("size"), c.get("size"), sim, only_a, only_c, kind,
                      len(conflicts), ptr))
        print(f"=== {repo} ｜ AGENTS {a.get('size')}B / CLAUDE {c.get('size')}B"
              f" ｜ 相似度 {sim:.2f}（{kind}）｜ 独有行 AGENTS {only_a} / CLAUDE {only_c} {ptr}")
        print(f"    九类：AGENTS {len(ca)}/9 {ca}")
        print(f"          CLAUDE {len(cc)}/9 {cc}")
        for line in conflicts:
            print(f"    🔴 冲突   {line}")
        for line in onesided:
            print(f"    ⚪ 单边   {line}")
        if not conflicts and not onesided:
            print("    — 槽位上无分歧")
        rows.append((repo, conflicts, onesided))
        print()
    print(f"合计：**真冲突 {conflicts_total} 条**、单边缺失 {onesided_total} 条（{len(rows)} 对里）")
    print(f"有真冲突的对：{sum(1 for _, c, _ in rows if c)} / {len(rows)}")
    close = [(r, a, c) for (r, a, c), (ta, tc) in zip(chosen, texts)
             if ta and tc and max(a.get("size", 1), c.get("size", 1)) / max(
                 min(a.get("size", 1), c.get("size", 1)), 1) <= 1.5]
    # 三分类汇总：这是决定"选项 2/3 值不值"的那个数
    from collections import Counter
    kinds = Counter(k for *_, k, _, _ in stats)
    print("\n=== 把取样按「两份到底是不是同一份东西」分类 ===")
    for k in ("指针/空壳/单边子集", "近重复", "一边是另一边的摘录", "真分叉（两边都有独有内容）"):
        if kinds[k]:
            print(f"  {k:<8} {kinds[k]:>3} 对（{kinds[k] * 100 / max(len(stats), 1):.0f}%）")
    print("\n  真冲突明细（同一互斥槽位取值不同）：")
    冲突对 = [(t, c) for t, (_, c, _) in zip(stats, rows) if c]
    for (repo, sa_, sc_, sim, oa, oc, k, nconf, ptr), conf in 冲突对:
        print(f"    {repo:<48} 相似度 {sim:.2f} ｜ " + "；".join(conf))
    fork = [t for t in stats if t[6].startswith("真分叉")]
    if fork:
        print("\n  同源分叉的那些（两边都有对方没有的内容 ⇒ 才是真分歧）：")
        for repo, sa_, sc_, sim, oa, oc, k, nconf, ptr in sorted(fork, key=lambda x: -min(x[4], x[5])):
            print(f"    {repo:<48} 相似度 {sim:.2f} ｜ 独有行 {oa}/{oc} ｜ 真冲突 {nconf}")
    print(f"\n  尺寸接近（≤1.5×）的 {len(close)} 对：差异不是「那份更长」造成的")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
