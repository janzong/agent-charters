# 审计工作台（work/ui）

把「100 份人工核对」这件事从 Markdown 搬到浏览器里，顺带解决读英文原文的障碍：
**鼠标悬停在任意段落上，就地显示中文译文**（译文在 251 预生成、随页面内嵌，Mac 离线可用，不需要 API key）。

## 产物

- `workbench.html` —— 单文件、零依赖、可离线。拷走即用，双击即开。
- `cache/i18n.json` —— 段落级译文缓存（key = sha1(原文)）。重跑只补新段落，不重复付费。
- `build_workbench.py` / `i18n.py` / `template.html` —— 生成器。

## 界面

- **仪表盘**：语料规模、九类覆盖率、v0.2→v0.3→v0.4 版本对照、核对进度。
- **审计工作台**：左栏选文件、中间读原文（悬停出译文）、右栏标类别。判定存本机
  `localStorage`，随时「导出 JSON」或「复制答案汇总」回传。

### 交互

| 操作 | 效果 |
|---|---|
| 鼠标悬停段落 | 显示中文译文（开关在顶栏） |
| 点击段落 | 钉住译文，再点取消 |
| 点右栏圆钮 | 灰（未选）→ 绿（这份文件有这类）→ 橙 `?`（不确定） |
| `J` / `K` | 下一份 / 上一份 |
| `1`–`9` | 切换第 n 个类别 |
| `S` | 保存并下一份 |
| 顶栏「盲判模式」 | 开＝藏起规则结论（盲判用），关＝显示规则分配的类别 |

## 生成

```bash
.venv/bin/python work/ui/build_workbench.py                 # 全 100 份（含翻译）
.venv/bin/python work/ui/build_workbench.py --groups blind  # 只做盲判 20 份
.venv/bin/python work/ui/build_workbench.py --no-translate  # 只出英文
```

翻译走 DeepSeek（`DEEPSEEK_API_KEY` 从环境读，不落盘）；单段落失败会降级逐段重试，
批次长度校验不过就整批拆开重发——宁可慢，不写错译。

## 已知边界

- 译文是机器翻译，**仅供阅读**；判定依据始终是英文原文。
- 页面内嵌了 100 份原文全文，文件较大（约 2 MB），浏览器打开无压力，但别用邮件传。
- `localStorage` 按浏览器 + 域名隔离：换浏览器 / 换端口打开，进度不互通。判定后请及时导出 JSON。

## 在哪些 app 里打开（同一个地址）

固定地址：`http://127.0.0.1:8791/workbench.html`；起服务一条命令：

```bash
bash work/ui/serve.sh start     # 起（幂等）｜ stop ｜ status
```

| 场景 | 怎么开 |
|---|---|
| VS Code（本机或 Remote-SSH 远程窗口） | `Cmd/Ctrl+Shift+P` → **Open Integrated Browser** → 地址栏粘上面的 URL |
| VS Code 老命令 | `Simple Browser: Show`（命令 ID `simpleBrowser.show`）后填 URL |
| VS Code 端口面板 | 左侧「端口 / Ports」应能看到 251 上的 `8791`（自动转发），点地球图标用系统浏览器打开 |
| Safari / Chrome（在 251 本机） | 直接粘 URL |
| Safari / Chrome（在别的机器） | 先转发端口：VS Code 的 Ports 面板，或 `ssh -N -L 8791:127.0.0.1:8791 janz@<251>` |
| 完全离线 | 把 `workbench.html` 拷过去双击（Mac 已验证可开） |

**远程窗口的坑**：集成浏览器里 `127.0.0.1` 打不开时，检查设置
`workbench.browser.enableRemoteProxy`（远程代理，让 localhost 落到远端 251）。
另外 `workbench.browser.openLocalhostLinks` 控制 localhost 链接是否在集成浏览器里打开。

**为什么只绑回环**：页面内嵌 100 份原文全文，`127.0.0.1` 之外的地址一律不监听。

## 常驻（开机就有，不用管）

两端各一处，都已装好并验过自愈（杀掉进程会自动拉起）：

| 端 | 机制 | 装在哪 | 说明 |
|---|---|---|---|
| 251 | systemd **user** 服务 `agent-charters-ui.service` | `~/.config/systemd/user/`（仓库副本在 `work/ui/systemd/`） | `Restart=always`；已 `Linger=yes` → 重启自起、不用登录 |
| Mac | LaunchAgent `com.hermes.ui8791` | `~/Library/LaunchAgents/` | `KeepAlive` 自愈，走 `~/.ssh/config` 的 `Host 251`，把远端 8791 转到 Mac 回环 |

```bash
systemctl --user status agent-charters-ui     # 251 端
launchctl list | grep ui8791                  # Mac 端
```

掉线排查：先看 251 的 `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8791/workbench.html`
（应 200），再看 Mac 的 `lsof -nP -iTCP:8791 -sTCP:LISTEN`（应有监听）——哪端断就重启哪端的服务。
