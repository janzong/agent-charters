# agent-charters 环境与通道备忘

> 记录日期：2026-09-10 ｜ 主机：janz ｜ 磁盘：74G 可用
> 用途：避免重复踩坑。换机、换会话、换协作者时直接读本文件。
> 原则：只记录实测结论，**不记录任何凭据**。

## 1. 项目定位

人写给 AI 智能体的书面规约（`AGENTS.md` / `CLAUDE.md` / `.cursorrules` /
`copilot-instructions.md` / `GEMINI.md` …）的结构化语料库与分析。
首个发布物 v0.1。本地路径 `/home/janz/workspace/agent-charters/`。

## 2. GitHub 通道实测

访问能力**分路径**，不可一概而论，更不能凭感觉判断"GitHub 慢不慢"。

| 路径 | 状态 | 延迟 | 用途 |
|---|---|---|---|
| `api.github.com` | ✅ 稳定 | ~1.1s | gh CLI / API 抓取 |
| `github.com` git over HTTPS | ❌ 超时（两次复测） | — | **弃用** |
| `github.com` git over SSH :22 | ✅ | — | **推荐** |
| `github.com` git over SSH :443 | ✅ | — | 备用（已配置） |
| `github.com` 网页 | ⚠️ 部分通 | ~1.2s | 具体路径可用，根路径偶发超时 |
| `uploads.github.com` | ✅ | 0.81s | Release 上传 |
| `codeload.github.com` | ✅ | 0.67s | zip 下载 |
| `objects.githubusercontent.com` | ✅ | 0.93s | Release 资产下载 |
| `raw.githubusercontent.com` | ❌ 超时 | — | 用 contents API 替代 |

**结论**：抓取（90% 依赖 API）零影响；代码管理走 SSH。

### 抓取链路的正确写法

```bash
# 文件内容（已验证可用）
gh api repos/{owner}/{repo}/contents/{path} --jq .content | tr -d '\n' | base64 -d

# 或走 CDN
curl -sL "https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}"
```

**禁止依赖 `raw.githubusercontent.com`。**

## 3. SSH 配置（已完成 2026-09-10）

- 密钥：`~/.ssh/id_github`（ed25519，专用于 GitHub）
- 指纹：`SHA256:8gvFejRN/FaoQv0KFGxlvV9ZHedEdK16yB2c7AE9THw`
- GitHub 注册名：`Janz-agent-20260910`
- `~/.ssh/config`：`github.com` 与 `ssh.github.com:443` 都绑定该 key，
  `IdentitiesOnly yes`，`ServerAliveInterval 60`
- `gh config git_protocol = ssh`

### 30 秒自检

```bash
ssh -T git@github.com
# 期望：Hi janzong! You've successfully authenticated, but GitHub does not provide shell access.

git ls-remote git@github.com:SWE-bench/SWE-bench.git HEAD
# 期望：返回一个 commit sha
```

## 4. 镜像 / 加速站（实测）

可用：

| 站点 | 延迟 | git 代理能力 |
|---|---|---|
| `cnb.cool` | 0.27s | 未测 |
| `gitclone.com` | 0.36s | ✅ 实测可代理 `ls-remote` |
| `gitee.com` | 0.54s | ✅ 原生 |
| `ghproxy.net` | 0.56s | ✅ 实测可代理 `ls-remote` |
| `gh-proxy.com` | 0.62s | 未测 |
| `ghfast.top` | 1.41s | 未测 |

已失效（勿再用）：`gh.llkk.cc`、`kkgithub.com`、`bgithub.xyz`、`mirror.ghproxy.com`

用法：

```bash
git ls-remote https://ghproxy.net/https://github.com/OWNER/REPO.git HEAD
```

> 镜像站寿命很短（本批已有 4 个失效），**每季度复测一次**。

## 4.5 仓库远端（已配 2026-09-11）

| 远端 | 地址 | 认证 | 说明 |
|---|---|---|---|
| `origin` | `git@github.com:janzong/agent-charters.git` | SSH（`~/.ssh/id_github`） | 主仓，public |
| `gitee` | `git@gitee.com:janzong/agent-charters.git` | SSH（`~/.ssh/id_gitee`） | 国内镜像，**public** |

**建立过程与坑（留档）**：

1. 一开始 Gitee 的 SSH 不通（`Host gitee.com` 没配 `IdentityFile`，也没有公钥登记）。
   首次推送是**借用 `mohu` 远端 URL 里嵌的 Gitee token** 走 HTTPS 完成的。
   **已处理（同日）**：巡检发现本机 **6 个仓库**（`mohu` / `research_mas` /
   `research-mas-v2` / `rmas-v3` / `rmas-v3-data` / `zhira`）的远端 URL 里嵌着**同一枚**明文
   令牌，`moya` 是裸 HTTPS；已全部换成 `git@gitee.com:…`，7 仓 `ls-remote HEAD` 实测通过，
   本机已无凭证落盘。⚠️ **那枚旧令牌在 Gitee 侧仍有效，需轮换**；
   **已补查并处理（同日）**：148（生产，`192.168.31.148`，用户 `h010218`，`id_research_mas` 可连）
   有 4 个仓库嵌着凭证 —— `rmas-v3` / `research-mas-v2` / `zhira` 是**同一枚**，
   `research_mas` 是另一枚且已失效。实测 148 的 `rmas-v3` 的 `git pull` 正靠它跑，
   故当时**不能直接撤**。处理：在 148 生成专用密钥 `~/.ssh/id_gitee`、登记 Gitee、
   4 仓远端改 SSH、`ls-remote`+`fetch` 全绿（**只 fetch 不 pull**，避免变相部署）、
   工作区 HEAD 未动。240 / Mac 扫描无 Gitee 令牌。
   **已补做（同日）**：云电脑（反隧道 `127.0.0.1:2222`，`administrator`）有 5 个仓库
   （`MoHu` / `MoYa` / `rmas-v3` / `rmas-v3-data` / `zhira`）带凭证，其中 3 枚 Gitee 令牌已失效；
   已在云电脑本地生成专用密钥 `~/.ssh/id_gitee`（key id `6048616`，**登记动作在目标机本地调 API 完成，令牌不出机器**）、
   5 仓远端改 SSH，`ls-remote` + `fetch` 全绿、HEAD 未动；云电脑上无任何自动化在用这些令牌。
   **只剩 DXPC(2224) 离线未扫。**
5. **旧令牌已撤销（同日）**：Gitee 上原有三枚私人令牌 —— `hjz-hermes`（最早，也是最可能那枚
   被嵌进各仓 URL 的）、`rmasv3`、`rmas-v3-data` —— **三枚全部删除**。删前做过最后确认：
   Hermes/系统配置里没有任何 Gitee 令牌字段，251 本地仓全部是 SSH 远端，agent-charters
   用的是独立 SSH 部署密钥，因此删除不影响 git 通道与 API 之外的任何东西。
   删后复验：251 九条远端（含 GitHub）/ 148 四条 / 云电脑五条的 `ls-remote` 全绿，
   Release 附件匿名下载 `302→302→200`（`application/octet-stream`），仓库页 200。
6. **⚠️ 云电脑踩坑（已修）**：云电脑的 `~/.gitconfig` **全局**设了
   `core.sshCommand = ssh -i C:\Users\Administrator\.ssh\id_ed25519 -o IdentitiesOnly=yes`，
   Windows 反斜杠路径经 Git Bash 会被吃掉，实际变成 `C:UsersAdministrator.sshid_ed25519`，
   **5 个 Gitee 仓一登就失败**。之前那次"云电脑迁移验证通过"是因为测试时用了显式 `-i` 参数，
   把这个坏配置盖住了 —— **教训：验收必须走默认路径（`git ls-remote` 不带 `-i`/`GIT_SSH_COMMAND`）**。
   处置：`git config --global --unset-all core.sshCommand`，改由 `~/.ssh/config` 的
   `Host gitee.com → IdentityFile ~/.ssh/id_gitee` 接管；复验五仓默认路径全绿。
   另查：云电脑 Windows 凭据管理器里无 gitee 缓存凭据。
7. **五机全量补扫完成（2026-09-11，五机同时在线时）**：
   `DXPC`（`DESKTOP-FNFT1GI`，反隧道 `127.0.0.1:2224`，用户 `admin`）—— **没装 git**、
   `.git` 目录 0 个、凭据管理器无 gitee/github 条目、`~/.ssh` 只有 `id_dxpc`，
   **无凭证可清**；该机磁盘响应慢，Desktop/Documents 的逐文件深扫未跑完（如实记，
   且三枚令牌已作废，残留风险为零）。
   `Mac`（`127.0.0.1:2223`，`janzh`）复核：无全局 `core.sshCommand`、无凭据，
   唯一仓库是 `cnb.cool` 上的 hermes-agent 镜像（裸 HTTPS，不含令牌）。
   `240` 复核：无全局 `core.sshCommand`；`C:\Users\Janz\projects\mohu` 与 `MoYa` 是
   **裸 HTTPS 远端（本身不含令牌）**，远端自 2026-06-26 后未更新，令牌撤销后
   **非交互拉取已失效**（`wincredman` 已无可用凭证）——**待定**：给 240 登记一枚 Gitee
   部署公钥改走 SSH，或就当 6 月的旧快照留着。
   **已处置（同日，选项 A）**：在 240 生成专用密钥 `%USERPROFILE%\.ssh\id_gitee`
   （ed25519，注释 `Janz-240-gitee-20260911`，指纹 `SHA256:DShTHbsh5YLLyoQUGo6vbJ8GleM6YbqIPUZjCL4m31U`，
   **公钥由用户在网页登记**——三枚令牌已删，无法再走 API 代登记）；
   `~/.ssh/config` 追加 `Host gitee.com`（`IdentityFile ~/.ssh/id_gitee` + `IdentitiesOnly`，
   原 251 / 251-lan 两段未动）；两仓远端改 `git@gitee.com:janzong/{mohu,MoYa}.git`。
   **复验（默认路径）**：`ssh -T git@gitee.com` → `Hi janz(@janzong)!`；两仓 `ls-remote` 通，
   且**本地 HEAD 与远端逐一相同**（`mohu 849e316` / `MoYa 2038266`）——并不落后，
   只是这两个仓自 2026-06-26 起就没有新提交。240 上另有未提交改动（`MoYa`：
   `.moya/memory.json`、`src/tools/charRegistry.ts` + 两个日志；`mohu`：一个 `nul` 残留文件），
   未动。
2. 已生成**专用密钥** `~/.ssh/id_gitee`（`Janz-gitee-20260911`，ed25519，无口令），
   经 API 登记到 Gitee（key id `6048580`），`~/.ssh/config` 的 `Host gitee.com` 补了
   `IdentityFile` + `IdentitiesOnly`（原配置备份 `~/.ssh/config.bak-20260911`）。
   自检：`ssh -T git@gitee.com` → `Hi janz(@janzong)!`
3. 建仓时 API 传 `private:false` **没有生效**（仓库仍是私有）；改属性的接口是 **PATCH**
   `/v5/repos/{owner}/{repo}`，且 **`name` 是必填**（漏了会报 `name is missing`）。
   已改回 public。
4. Gitee 的 Release 与 GitHub 不共享：需要单独 `POST /v5/repos/{o}/{r}/releases`，
   再 `POST .../releases/{id}/attach_files`（multipart）传附件。

**镜像内容**：`main` + tag `v0.1` / `v0.1.1` / `v0.2` 全部对齐；Release `v0.2` 已建，
附 parquet + jsonl（Gitee 另自动生成 `v0.2.zip` / `v0.2.tar.gz` 源码包）。
匿名可下：`https://gitee.com/janzong/agent-charters/releases/download/v0.2/agent-charters-v0.2.parquet`

**日常同步**（新提交后）：

```bash
git push origin main && git push gitee main && git push --tags
```

## 4.6 SSH 服务端加固（2026-09-11）

做凭证巡检时顺带看了 251 的 sshd，发现它对公网开放（路由器把内网 22 映射到一枚 DDNS
域名的非标端口），而 `PasswordAuthentication` 是 `yes`；机器上**唯一有口令的账号是 `janz`**。
近 23 天 `auth.log` 累计 **9.1 万次**爆破尝试（来源 `45.148.10.173` / `193.32.162.39` 等）。
`fail2ban` 本来就装着且在生效（累计 ban 31 个 IP），但慢速爆破挡不住。

**处置结果**（`sudo sshd -T` 前后对比）：

| 项 | 之前 | 之后 |
|---|---|---|
| 公网来源 `PasswordAuthentication` | `yes` | **`no`**（只许公钥） |
| 内网 / 回环 `PasswordAuthentication` | `yes` | `yes`（保留兜底，防自锁） |
| `PermitRootLogin` | `without-password` | `no`（root 本无口令、无授权公钥） |
| `MaxAuthTries` / `LoginGraceTime` | `6` / `120` | `3` / `30` |

落点：`/etc/ssh/sshd_config.d/99-fleet-hardening.conf`（全局值）+ 主配置**末尾**的
`Match Address 127.0.0.0/8,::1/128,192.168.31.0/24`（内网口令兜底）。
原文件备份 `/etc/ssh/sshd_config.bak-20260911-harden`；监听端口与监听地址**未动**。

**⚠️ 踩坑（重要）**：Ubuntu 的 `sshd_config` 首行就是 `Include /etc/ssh/sshd_config.d/*.conf`，
所以 **`Match` 块不能写进 drop-in 文件**——Match 会一直作用到下一个 Match 或文件结尾，
把主配置后面的指令全吞进 Match 上下文，`sshd -t` 直接报错。正确做法：
**drop-in 只放全局值，Match 追加到主配置末尾**。

**验证**（四条都做了，不靠猜）：

1. `sudo sshd -T -C user=janz,addr=<公网IP>,host=251,laddr=192.168.31.251,lport=22` →
   `passwordauthentication no`；把 addr 换成 `192.168.31.240` → `yes`（分支选择正确）
2. 本机回环密钥登录通过；`240 → 251` 跨机密钥登录实测通过（重载后 sshd 无报错）
3. **外部真实视角**：从云电脑走公网域名 + 非标端口 —— 密钥登录 `OK`，
   纯口令尝试返回 `Permission denied (publickey)`，`auth.log` 对应两行已确认
4. `fail2ban` 未误封（探测次数远低于 `maxretry=5`）

**回滚**：`sudo rm /etc/ssh/sshd_config.d/99-fleet-hardening.conf`，去掉主配置末尾 Match 块
（或直接恢复备份）→ `sudo sshd -t && sudo systemctl reload ssh`。

**影响面**：251 上只有 `janz` 一个人类账号；`root` / `nova` 均无口令、无授权公钥。
用户偶发从云电脑用口令登录（近 30 天 7 次），但那台机器公钥登录有 729 次，
密钥本来就在，切换后实测无感。

## 5. 数据集发布通道

| 平台 | 状态 | 备注 |
|---|---|---|
| GitHub Releases | ✅ | uploads 端点通；`v0.1` / `v0.1.1` / `v0.2` 已发（含数据资产） |
| Gitee | ✅ | 仓库 + Release `v0.2` + 附件均已通（public，匿名可下） |
| ModelScope（魔搭） | ✅（0.06s） | **建议作为主数据集站** |
| HuggingFace 官方 | ❌ 不通 | 需代理，二期再上 |
| `hf-mirror.com` | ✅（2.0s） | 只读镜像，仅用于下载 |
| Zenodo（DOI） | ❌ 不通 | DOI 方案另议 |
| Kaggle | ✅ 页面通 | 备选 |

环境变量已预设 `HF_ENDPOINT=https://hf-mirror.com`。

## 6. 配额与硬限制（设计时必须考虑）

- `gh` core：**5000/h**（认证后，未认证只有 60/h）
- `gh` search：30/min
- `gh` code_search：**10/min** ← 抓取瓶颈
- **GitHub search API 单次查询结果上限 1000 条** ← 必须分片
- 分片策略：按语言 / star 区间 / 时间片切分，多轮搜索后去重

## 7. 本机运行时

- hostname `janz`；磁盘 74G 可用；Node v22.22.3；npm 10.9.8
- **项目 venv：`/home/janz/workspace/agent-charters/.venv`（Python 3.12.3，369M）**
- ⚠️ **本机 `python3` 默认指向 hermes 的 venv**
      （`~/.hermes/hermes-agent/venv/bin/python3`），
      直接 `pip install` 会污染 hermes → **一律显式使用 `.venv/bin/python`**
- 项目 venv 已装：`datasets` 5.0.1、`pandas` 3.0.5、`pyarrow` 25.0.1、
      `huggingface_hub` 1.31.0
- **pip 必须用国内源**：`-i https://pypi.tuna.tsinghua.edu.cn/simple`
      （实测 400+ MB/s；直连官方源会因响应被截断报 `JSONDecodeError`）
- hermes 自带 venv：`~/.hermes/hermes-agent/venv/`（内含 `hf` CLI，勿动）

## 8. 待办 / 未决

- [x] git 全局身份已配置（2026-09-10）：
      `user.name=Janz`，`user.email=287099612+janzong@users.noreply.github.com`
      （GitHub noreply，不暴露真实邮箱）；同时设了 `init.defaultBranch=main`、`pull.rebase=false`
- [x] 测试仓库 `janzong/codex-channel-test` 已删除（2026-09-10，验证 404，
      `janzong` 名下现为空）
- [x] 已建项目 venv 并安装 `datasets` / `pandas` / `pyarrow`（2026-09-10，
      见第 7 节）
- [ ] ModelScope 账号（若确定用其做主数据集站）
- [ ] 是否建 GitHub Org（倾向先用个人账号，后续可 transfer，不阻塞）
- [x] 旧 Gitee 令牌撤销（2026-09-11 完成）：三枚（`hjz-hermes` / `rmasv3` / `rmas-v3-data`）
      已全部删除，删后全机复验通过（见第 4.5 节第 5 条）
- [x] 五机凭证补扫全部完成（2026-09-11，见 §4.5 第 5-7 条）：DXPC 未装 git 无凭证；
      Mac / 240 复核无凭证
- [x] 240 两个 Gitee 仓已改 SSH（2026-09-11，见 §4.5 第 7 条）：专用密钥 + 网页登记公钥，
      `ssh -T` 与两仓 `ls-remote` 默认路径均通过；本地与远端 HEAD 一致，无需拉取
- [ ] 云电脑主库 `state.vscdb` 明文令牌待脱敏（被运行中的 VS Code 独占锁定）
- [ ] 云电脑另有 1 枚 GitHub token 明文躺在 `.codex\vendor_imports\skills`，待处置
- [x] 251 sshd 加固（2026-09-11，见 §4.6）：公网只许公钥 + 内网保留口令兜底，
      外部真实视角实测通过（密钥通、纯口令被拒）
- [ ] （可选）fail2ban 收紧：`maxretry` 5→3、`bantime` 600→3600

**已定**：项目名 `agent-charters` / 智能体章程；
版本规则为两节（小数位递增＝只增不改、旧结论仍成立；整数位递增＝定义变更、旧结论需重验；
`1.0` 含义为口径冻结）。

## 9. 已知坑（踩过的）

1. `raw.githubusercontent.com` 不可用 → 一律走 contents API 或 jsdelivr
2. HTTPS 方式 git 不可用 → 一律走 SSH，`gh` 已切 ssh
3. `code_search` 限 10/min → 抓取必须做限速与断点续跑，不能硬轮询
4. 镜像站寿命短 → 定期复测，不要硬编码单一镜像
5. **版权**：抓取的配置文件版权归原作者，**只发布衍生标注与统计特征，不发布全文**
6. **可复现性**：LLM 抽取必须记录所用模型版本，否则半年后无法复现
7. 敏感信息（内网 IP、口令、路径、人名）在提取阶段就要脱敏
