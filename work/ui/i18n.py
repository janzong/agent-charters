"""逐段翻译（DeepSeek）+ 磁盘缓存，供审计工作台预生成中英对照。

设计取舍：
- 段落级缓存（key = sha1(原文)）：重跑、扩样本、换排版都不重复付费。
- 批量 + 并发：一次请求塞多段，多个请求并行；长度校验失败就降级逐段，宁可慢不写错译。
- 只翻正文段落；代码块由调用方过滤，不进这里。
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request

API = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
BATCH_SEGS = 10
BATCH_CHARS = 3500
WORKERS = 10

SYSTEM = (
    "你是技术文档翻译引擎。把输入数组里的每一段英文翻译成简体中文。规则："
    "1) 逐段对应，输出数组长度必须与输入完全相同；"
    "2) 代码、命令、路径、参数名、标识符、markdown 标记原样保留；"
    "3) 不要解释、不要加注释、不要合并或拆分段落；"
    '4) 只输出 JSON 数组，形如 ["译1","译2"]，不要代码块包裹。'
)


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class Translator:
    def __init__(self, cache_path: pathlib.Path, offline: bool = False):
        self.cache_path = pathlib.Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, str] = {}
        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text("utf-8"))
        self.key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.offline = offline or not self.key
        self.lock = threading.Lock()
        self.hits = 0

    # ---------- 单次 API ----------
    def _call(self, segs: list[str]) -> list[str]:
        body = json.dumps(
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(segs, ensure_ascii=False)},
                ],
                "temperature": 0,
                "max_tokens": 8000,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            API,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
        )
        last = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.loads(r.read())
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                out = json.loads(text)
                if not isinstance(out, list) or len(out) != len(segs):
                    raise ValueError(f"seg count mismatch {len(out)} != {len(segs)}")
                if not all(isinstance(x, str) for x in out):
                    raise ValueError("non-string element")
                return out
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"translate failed: {last}")

    def _translate_batch(self, segs: list[str]) -> list[str]:
        try:
            return self._call(segs)
        except RuntimeError as exc:
            print(f"  [warn] batch fallback -> per-seg ({exc})", file=sys.stderr)
            return [self._call([s])[0] for s in segs]

    # ---------- 对外 ----------
    def translate(self, texts: list[str], label: str = "") -> dict[str, str]:
        """返回 {原文: 译文}（原文重复自动去重）。"""
        uniq = list(dict.fromkeys(t for t in texts if t and t.strip()))
        todo = [t for t in uniq if _sha1(t) not in self.cache]
        self.hits += len(uniq) - len(todo)
        if self.offline or not todo:
            return {t: self.cache.get(_sha1(t), "") for t in uniq}

        batches, cur, n = [], [], 0
        for t in todo:
            if cur and (len(cur) >= BATCH_SEGS or n + len(t) > BATCH_CHARS):
                batches.append(cur)
                cur, n = [], 0
            cur.append(t)
            n += len(t)
        if cur:
            batches.append(cur)

        done = 0
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futs = {pool.submit(self._translate_batch, b): b for b in batches}
            for fut in cf.as_completed(futs):
                batch = futs[fut]
                try:
                    out = fut.result()
                except Exception as exc:  # noqa: BLE001
                    print(f"  [error] batch skipped: {exc}", file=sys.stderr)
                    continue
                with self.lock:
                    for src, tr in zip(batch, out):
                        self.cache[_sha1(src)] = tr
                    done += 1
                    if done % 10 == 0 or done == len(batches):
                        self.cache_path.write_text(
                            json.dumps(self.cache, ensure_ascii=False), "utf-8"
                        )
                        print(f"  [i18n] {label} 批次 {done}/{len(batches)} (缓存 {len(self.cache)})")
        return {t: self.cache.get(_sha1(t), "") for t in uniq}

    def flush(self) -> None:
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False), "utf-8")
