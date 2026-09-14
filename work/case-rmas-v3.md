# 第二个真用案例：从零写一份章程，全程拿 `compare` 当尺子（2026-09-14）

> 对应 `STATE.md` §5 队列 #4。第一个案例（`work/usage_audit.md`）是拿 `brief`/`refs` 审**已经写好的**
> 7 份章程；这次是**从零写一份新的**，把工具当检查清单用，看它到底改不改得动成稿。
>
> **一句话结论**：工具能当清单用（九槽被逐条点名，确实让我写出了本来会跳过的槽位），
> 但**不能直接当尺子**——照 `brief` 给的槽位名写标题时，`compare` 会漏判 `agent_meta`
> （九类里只有这一类），而且**给不出任何"我可能看漏了"的提示**。

## 0. 两条边界（先说，免得数字被过度引用）

- **对象是私有仓库**：`rmas-v3` 在 Gitee 上 API 404 / 网页 403（2026-09-14 实测），所以本文件
  不引它的正文，只报告**工具行为**与编辑决策；章程正文留在仓库外（`/tmp/rmas-v3-AGENTS.md`），
  **不入库、不发布**。
- **n=1，且作者＝使用者**：这是自测，**不算**判据里缺的那个"非作者的外部使用者"。

## 1. 做法

1. 先 `agent-charters brief --lang zh` 拿九槽清单（此时手上没有草稿）。
2. 只读采事实：`CODEX.md` / `MESSAGES.md` / `README.md` / `VERSION` / `docs/DEPLOY.md` /
   `scripts/setup-hooks.sh` / `scripts/pre-push` / `backend/pytest.ini` / `frontend/package.json` /
   `.env.example` / `.gitignore`；引用前逐一核实路径存在性（候选里的 `frontend/vite.config.js`
   不存在，故只写 `vite.config.ts`）。
3. 写 v1：107 行 / 7001B，九个二级标题写成「槽位名 + 中文释义」，如
   `## boundaries（每条都写了为什么）`、`## agent_meta（对 AI 自身的要求）`。
4. `compare` + `brief` + `refs` 各跑一遍 → 按输出改 → v6 定稿 7012B / 9 类。

## 2. 工具改变了成稿的地方

只有一处是**硬改**：

| 工具说 | 怎么改 |
|---|---|
| `agent_meta 25.8% —`（说我没有这一类，**但我明明写了一整节**） | 不是补内容，是**改标题措辞**（见 §3）|

其余是**清单效应**（n=1 自述，方向与 `FINDINGS.md` §14 / `work/auto_vs_human.md` 的 n=11 实验一致）：
九槽被逐条点名后我全部写了；其中 `workflow` 与 `gotchas` 若没人点名，按我自己的习惯会跳过——
`gotchas` 那 6 条是这次写章程时**现查仓库**挖出来的（三处版本号不一致、README 端口写错、
门禁比文档弱、`.gitignore` 里一行遗留的 `null`、根目录有 `node_modules` 却无 `package.json`、
148 上 `git pull` 不补依赖），不是从 `CODEX.md` 抄的。

## 3. 对照实验：把工具的槽位名当标题，`compare` 会漏判 `agent_meta`

同一份 v1，只动标题 / 加一行英文，跑 `compare`：

| 变体 | 相对 v1 的改动 | 大小 | 结果 |
|---|---|---|---|
| v1 | —（标题 `## agent_meta（对 AI 自身的要求）`） | 7001B | **8/9，`agent_meta` 漏** |
| v2 | 标题 → `## 智能体行为要求（对人机协作的约定）` | 7014B | 9/9 |
| v3 | 标题不动，正文加一行 `You are expected to …; tone must stay plain.` | 7064B | 9/9 |
| v4 | 标题 → `## Agent behavior` | 6977B | 9/9 |
| v5 | 九节标题**全部**换成裸槽位名（`## overview` … `## agent_meta`） | 6764B | **8/9，只有 `agent_meta` 漏** |
| v6 | 定稿：标题 → `## 智能体行为要求（对 AI 自身的要求）` | 7012B | 9/9 |

**v5 是关键**：`overview` / `structure` / `build_test` / `style` / `workflow` / `environment` /
`boundaries` / `gotchas` **八个槽位名都认得出来**，**只有 `agent_meta` 认不出**。
也就是说：照 `brief` 的提示词逐条写、标题就叫 `agent_meta`，`compare` 会一直回答"你缺 `agent_meta`"，
而用户唯一能得到的暗示是"再补点内容"——**补内容不会改变结果**。

## 4. 机制（读 `ruleset_v0.1.8` 得到）

- **标题通道**（`taxonomy.py` `HEAD_RULES["agent_meta"]`）：22 条，其中含中日文 7 条
  （协作 / 行为 / 角色 / 智能体 / あなた / 役割 / トーン）；**没有 `agent_meta` 这个字面**——
  料库里没有人类作者会把这个内部槽位名当标题。
- **正文通道 6 条 + 全文通道 7 条，合计 13 条规则，含中文的 0 条**
  （`\byou are\b`、`\byour role\b`、`AI … must|shall|disclos|prohibit`、`\btone\b` …）。
- 唯一的中文兜底是一条**总是运行**的强模式：`会话压缩|跨会话|防遗忘|自动加载|协作约定`（窄门）。
- 这与 `LIMITATIONS.md` §21 第 1 条是同一个洞的两半：那边是**留出集实测**（中文 `agent_meta`
  recall 26%），这边是**机制**（中文正文通道为空）＋ 一个**工具自洽问题**（自己的槽位名
  不在自己的标题词表里）。

## 5. `refs`：三个观察 + 一个能让它真核验的做法

- **在仓库外跑只能给「验不了」**：草案放在没有 `.git` 的目录里，`refs` 对 17 个指向全部输出 `?`
  （`unverified`）——这是 `work/usage_audit.md` U3 有意修的第四态，行为符合设计（宁可说验不了，
  不误报断链）。
- **「有没有 `.git`」这个判据会被一个空目录骗到**：本次 `/tmp` 下恰好存在一个**遗留的空 `.git`**
  （非本仓库创建），于是 `refs` 把 `/tmp` 当仓库根，对同一份草案报出 **16 个假断链**
  （含 `README.md`、`CODEX.md`、`frontend/`）。门应该更严（例如要求 `.git` 非空、或把
  「被描述的仓库」作为显式参数传入），否则这类假阳性能重现。**记下来不改**（D11 / D32）。
- **能让它真核验的做法（本次用上了，建议写进工具文档）**：章程不必放进被描述的仓库——
  做一个**镜像目录**即可：`mkdir -p /tmp/mirror-X/.git`，把被描述仓库的顶层条目 `ln -s` 进去，
  草案放成该目录下的 `AGENTS.md`。`refs` 按 `base_dir`（草案所在目录）解析，于是能真核验。
  实测：17 个指向 **15 ✓ / 1 `~` / 2 ✗**。
- **其中 2 个 ✗ 是工具的真缺陷**：`dist/` 与 `.venv/` 出现在 boundaries 段「**不提交**这些」的
  清单里——它们是**本来就不该存在**的路径。`refs` 分不清「去读这个」和「别提交这个」，
  对禁令清单里的路径会一律报断链。**记下来不改**。
- 剩下的 1 个 `~`（`tests/`）是**我该改的**：见下。

**这一趟修掉了章程的一处真缺陷**：结构段原文写「新路由放 `api/`、业务逻辑放 `services/`、
模型放 `models/`」——三个简写。`refs` 判 `~`（同名目录在 `backend/app/` 下、仓库根没有），
这提示**真的 agent 会去仓库根找 `api/`**。已改成全路径。这是本次工具给出的、唯一一处
内容级改进（`compare` 那处是措辞级）。

## 6. 判据怎么记

`STATE.md` §5 第一优先的判据是"**你自己在写下一份 `AGENTS.md` 时会主动用它**"。

- **会**：`brief` 的九槽清单确实改变了我的写法（n=1 自述，方向同 `FINDINGS.md` §14）。
- 但它现在的角色是**清单，不是尺子**：`compare` 的"缺什么"必须人工复核——本次就是人工复核
  推翻了它的结论（§3 的 v5 对照）。
- 判据 5/6 里"**非作者的外部使用者**"那一格**仍然是空的**：本案例的价值是暴露问题，不是填上那一格。

## 7. 复算

```bash
cd ~/workspace/agent-charters
.venv/bin/agent-charters brief --lang zh                 # 九槽清单 + 可粘贴提示词
.venv/bin/agent-charters compare /tmp/rmas-v3-AGENTS.md  # 定稿：9/9

# 让 refs 能真核验：镜像目录（顶层条目软链 + 一个 .git）
M=/tmp/mirror-rmas-v3; mkdir -p "$M/.git"
for e in CODEX.md MESSAGES.md README.md VERSION .env.example .gitignore \
         backend frontend deploy docs scripts node_modules; do
  ln -sfn "/home/janz/workspace/rmas-v3/$e" "$M/$e"
done
cp /tmp/rmas-v3-AGENTS.md "$M/AGENTS.md"
.venv/bin/agent-charters refs "$M/AGENTS.md"             # 15 ✓ / 1 ~ / 2 ✗（见 §5）
```

规则条数可复算（`ruleset_v0.1.8`）：

```bash
.venv/bin/python -c "import agent_charters.taxonomy as T,re; \
print(len(T.HEAD_RULES['agent_meta']), len(T.BODY_RULES['agent_meta']), len(T.FULLTEXT_RULES['agent_meta'])); \
print([r for r in T.BODY_RULES['agent_meta']+T.FULLTEXT_RULES['agent_meta'] if re.search(r'[\u4e00-\u9fff]',r)])"
```
