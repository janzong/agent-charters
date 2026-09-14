"""GitHub Action 的判定逻辑（`action.yml` 只负责接线，判定都在这里）。

**为什么单独成模块**：①能进测试（`tests/test_smoke.py` 直接调 `evaluate()`）
②`::error::` / `::warning::` 协议和 `GITHUB_STEP_SUMMARY` 的写法有十几行，
塞进 `action.yml` 的 YAML 字符串里就看不见在干什么了 ③`fail-on-missing` /
`fail-on-dangling` 是**策略**不是语法——策略要能被读到、被测试钉住。

**判定两条**（都来自"真用一次"暴露的问题，不是想出来的）：
  1. **缺了哪些类别**——`compare` 的人读输出由 CLI 负责，这里只算"该不该失败"。
  2. **指向的路径存不存在**——最锋利的那条：章程指错方向比不指更糟，agent 会照着
     不存在的文件找。默认**不**因此失败：禁令清单里的路径（"绝不提交 `.env`"）不是断链，
     而扫描器目前分不清"去读这个"和"别提交这个"（见 `work/case-rmas-v3.md`）。

用法：`python -m agent_charters.gha`，读环境变量
`CHARTER_FILES` / `CHARTER_LANG` / `FAIL_ON_MISSING` / `FAIL_ON_DANGLING`。
退出码：0 通过（或只是报告）｜1 触发了 `fail-on-*` 策略。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .extract import CATEGORIES, analyze_file, category_coverage, load_corpus, substantive
from .refs import find_refs, resolve_targets


@lru_cache(maxsize=1)
def _coverage() -> dict[str, float]:
    """随包语料库的类别覆盖率——用来把"缺的那几类"按语料库写得最多的排前面。"""
    return category_coverage(substantive(load_corpus()))


@dataclass
class Result:
    files: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    unverified: int = 0
    failures: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)   # 用法错（配置写错了），也算失败

    @property
    def skipped(self) -> bool:
        return not self.files


def evaluate(files: list[str], fail_on_missing: tuple[str, ...] = (),
             fail_on_dangling: bool = False) -> Result:
    """给一组章程文件算结果。空文件列表＝跳过（不失败）。"""
    res = Result()
    res.files = [f for f in files if Path(f).is_file()]

    unknown = [c for c in fail_on_missing if c not in CATEGORIES]
    if unknown:
        res.problems.append(
            f"unknown category in `fail-on-missing`: {', '.join(unknown)} "
            f"(valid: {', '.join(CATEGORIES)})")
    if not res.files:
        return res

    mine: set[str] = set()
    for f in res.files:
        mine |= set(analyze_file(f)["categories"])
    res.missing = sorted((c for c in CATEGORIES if c not in mine), key=lambda c: -_coverage()[c])

    for f in res.files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        rec = find_refs(text)
        if not rec["routes_outward"]:
            continue
        for target, status in resolve_targets(rec, Path(f).parent):
            if status == "missing":
                res.dangling.append(f"{f}: {target}")
            elif status == "unverified":
                res.unverified += 1

    hit = [c for c in fail_on_missing if c in res.missing]
    if hit:
        res.failures.append(f"missing categories you asked to enforce: {', '.join(hit)}")
    if fail_on_dangling and res.dangling:
        res.failures.append(f"{len(res.dangling)} pointed-at path(s) do not exist")
    return res


def _summary_md(res: Result, lang: str) -> str:
    if res.skipped:
        return ("## agent-charters\n\n"
                "No charter file found (nothing to check). "
                "Set `path:` if yours lives somewhere other than `AGENTS.md`.\n")
    out = [f"## agent-charters ({len(res.files)} file(s))", ""]
    if res.missing:
        out += [f"Missing {len(res.missing)} of {len(CATEGORIES)} categories "
                f"(most common in the corpus first):", ""]
        out += [f"- `{c}`" for c in res.missing]
    else:
        out.append(f"All {len(CATEGORIES)} categories covered.")
    if res.dangling:
        out += ["", f"{len(res.dangling)} path(s) pointed at but not found:", ""]
        out += [f"- `{d}`" for d in res.dangling[:10]]
    if res.unverified:
        out += ["", f"({res.unverified} pointer(s) could not be verified: not a repo root.)"]
    out += ["", "Coverage is a process metric, not a quality score — "
                "nine filled boxes are not nine good boxes."]
    return "\n".join(out) + "\n"


def main(env: dict | None = None) -> int:
    env = os.environ if env is None else env
    files = (env.get("CHARTER_FILES") or "AGENTS.md").split()
    fail_on_missing = tuple(c.strip() for c in (env.get("FAIL_ON_MISSING") or "").split(",")
                            if c.strip())
    fail_on_dangling = (env.get("FAIL_ON_DANGLING") or "").strip().lower() in ("1", "true", "yes")
    res = evaluate(files, fail_on_missing, fail_on_dangling)

    if summary_path := env.get("GITHUB_STEP_SUMMARY"):
        try:
            with open(summary_path, "a", encoding="utf-8") as fh:
                fh.write(_summary_md(res, env.get("CHARTER_LANG") or "en"))
        except OSError as e:
            print(f"::warning::could not write step summary: {e}")

    if output_path := env.get("GITHUB_OUTPUT"):
        try:
            with open(output_path, "a", encoding="utf-8") as fh:
                fh.write(f"missing={','.join(res.missing)}\n")
                fh.write(f"dangling={len(res.dangling)}\n")
        except OSError:
            pass

    if res.skipped:
        print(f"::warning::no charter file found among: {', '.join(files)} — skipped")
        return 0

    print(f"checked {len(res.files)} file(s): missing {len(res.missing)}/{len(CATEGORIES)}"
          f" categories, {len(res.dangling)} dangling path(s)")
    for p in res.problems:
        print(f"::error::{p}")
    for f in res.failures:
        print(f"::error::{f}")
    if not res.problems and not res.failures:
        print("::notice::agent-charters: nothing to enforce was violated")
    return 1 if (res.problems or res.failures) else 0


if __name__ == "__main__":
    sys.exit(main())
