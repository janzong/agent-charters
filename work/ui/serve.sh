#!/usr/bin/env bash
# 审计工作台的本地服务：起 / 停 / 状态，端口固定，地址固定。
#
#   bash work/ui/serve.sh start     # 起（已在跑就复用）
#   bash work/ui/serve.sh status
#   bash work/ui/serve.sh stop
#
# 只绑 127.0.0.1：页面内嵌 100 份原文全文，不能暴露到局域网/公网。
# VS Code（含 Remote-SSH 远程窗口）用内置浏览器开这个地址即可；别的 app 用端口转发或直接拷文件。
set -euo pipefail

PORT="${AC_UI_PORT:-8791}"
UI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$UI/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
PAGE="workbench.html"
URL="http://127.0.0.1:${PORT}/${PAGE}"
LOG="$UI/serve.log"

alive() { curl -fs -o /dev/null --max-time 2 "$URL" 2>/dev/null; }

case "${1:-start}" in
  start)
    if alive; then echo "已在运行：$URL"; exit 0; fi
    if [ ! -f "$UI/$PAGE" ]; then
      echo "缺 $UI/$PAGE —— 先生成：$PY work/ui/build_workbench.py" >&2; exit 1
    fi
    setsid nohup "$PY" -m http.server "$PORT" --bind 127.0.0.1 --directory "$UI" >> "$LOG" 2>&1 < /dev/null &
    for _ in 1 2 3 4 5 6 7 8 9 10; do sleep 0.4; alive && break; done
    alive && echo "已启动：$URL" || { echo "启动失败，看 $LOG" >&2; exit 1; }
    ;;
  stop)
    pkill -f "http.server ${PORT} .*--directory ${UI}" 2>/dev/null || true
    sleep 0.5
    alive && echo "仍在运行（可能是别的进程占端口）" || echo "已停止"
    ;;
  status)
    if alive; then
      echo "运行中：$URL"
      echo "VS Code 内置浏览器：Cmd/Ctrl+Shift+P → Open Integrated Browser → 粘贴上面地址"
    else
      echo "未运行（bash work/ui/serve.sh start）"
    fi
    ;;
  *) echo "用法: $0 {start|stop|status}" >&2; exit 2;;
esac
