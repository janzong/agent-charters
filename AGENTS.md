# AGENTS.md —— 在这个仓库里干活的约定

## 这是什么

`agent-charters` 是**人写给 AI 智能体的书面规约**（`AGENTS.md`、`CLAUDE.md`、`.cursorrules`）
的结构化语料库：数据集 **v0.5**，558 个公开仓库各一份，其中 516 份是可供统计的实质文件。
附带五个命令（`stats` / `brief` / `compare` / `show` / `refs`），把任意一份章程与这份基线对比。

**它刻意不是什么**：不给章程打质量分（覆盖率是过程指标，填满九格不等于写好，见 `LIMITATIONS.md`）；
不是模板库；不做生成。它只回答"你跳过了哪一格"和"你指出去的路径还在不在"。

## 目录与关键文件

| 路径 | 是什么 |
|---|---|
| `agent_charters/` | 随包的 Python 包：`cli.py`（命令）`brief.py`（清单与提示词）`refs.py`（外部引用）`extract.py`（抽取与统计）`i18n.py`（中英文案）`taxonomy.py`（九类规则集） |
| `agent_charters/data/*.jsonl.gz` | **随包语料库**——CLI 实际读的就是这一份（纯标准库可读，0.4.0 起不再随包发 parquet） |
| `data/processed/` | **发布资产**（parquet + jsonl + `SHA256SUMS`），Release 用这一份 |
| `work/` | 一次性分析脚本与审计记录（`work/audit/` 是人工核对逐条存档），对外引用的每个比例都出自这里 |
| `tests/test_smoke.py` | 唯一的测试套件（单文件，168 条） |

文档各管一摊，别混：`STATE.md`（状态与决策记录）、`FINDINGS.md`（对外结论）、
`LIMITATIONS.md`（已知边界与错在哪里）、`TAXONOMY.md`（九类定义与口径裁决）、
`SCHEMA.md`（字段）、`SHARE.md`（发帖文案）、`ENVIRONMENT.md`（网络/渠道可达性）。

## 构建、运行、测试

```bash
python -m venv .venv && .venv/bin/pip install -e ".[test]"  # 国内网络加 -i https://pypi.tuna.tsinghua.edu.cn/simple
.venv/bin/python -m pytest -q                               # 期望全绿；缺 data/raw 时少数用例自动跳过
.venv/bin/python -m agent_charters.cli compare AGENTS.md --lang en
```

CI 是 `.github/workflows/charter.yml`：两个 Python（3.10 / 3.12）跑测试套件，
另有一个 job 用本仓库自己的 action 检查这份 `AGENTS.md`。

## 代码风格与提交

- 注释与文档用中文；**提交信息用 conventional commits**，正文写清"为什么"而不只是"改了什么"。
- 不加版权/许可头（`LICENSE` 已经够）。
- 不引入新依赖：运行时只用 `pandas` / `pyarrow`，`i18n`、`refs`、`brief` 全是标准库。
  加依赖前先问"能不能用标准库写"。
- 改动尽量小且集中；顺手修无关的 bug 要单独一个提交，并在信息里说明。

## 提交流程

1. `git pull` → 改 → `.venv/bin/python -m pytest -q` → conventional commit。
2. **push 两个远端**：`origin`（GitHub）+ `gitee`（Gitee 镜像），两边必须一致。
   push ≠ 部署：数据集的 Release 与对外发帖由人执行。
3. 数据集升版要**同时动四处**：`data/processed/` 的 jsonl 与 parquet、随包 `.jsonl.gz`（跑 `work/pack.py`
   一次生成）、`data/processed/SHA256SUMS`、`taxonomy.py` 里的版本字段；漏一处会被测试或 `work/`
   下的复算脚本打回（"随包副本与发布副本是同一份"有测试钉着）。

## 运行环境

- Python ≥ 3.10，纯 Python 实现（无编译步骤）。Linux / macOS 都要能跑。
- **输出语言跟 locale 走**（`LC_ALL` → `LC_MESSAGES` → `LANG`，`zh*` 中文，其余英文），
  每个命令可用 `--lang en|zh` 覆盖；英文输出里不许出现汉字（有测试钉住）。
- **运行时零依赖**（0.4.0 起）：语料以 `jsonl.gz` 随包，只用到标准库的 gzip + json。
  `pandas` / `pyarrow` 只在读 parquet（`[parquet]` 附加依赖）与跑测试（`[test]`）时需要——
  别把这两个加回 `dependencies`：装包会从几百 KB 变成 62 MB，而国内直连拉它们常断流（有测试钉住）。
- 包已发 PyPI（2026-09-15 起，Trusted Publishing/OIDC，仓库不存 token）：`pip install agent-charters`；
  国内更快的一条是 `pipx install "git+https://gitee.com/janzong/agent-charters"`。

## 绝对不能做

- **绝不提交原文全文**：语料库里的 558 份章程正文只存在于本地与数据集产物里；
  控制台工作台的产物内嵌 100 份全文，已被 `.gitignore` 挡住——不许解禁、不许进 Release 资产。
- **绝不把密钥写进仓库或贴进对话**（Gitee / GitHub / dev.to 的凭据一律只读文件、不打印）。
- **不改 `STATE.md` §3「不可争议区」，不放宽判据**；已决事项不要再辩论一遍——
  要改先按 `STATE.md` 的 D 编号规则写清"实测影响"，再由人裁定。
- **对外说出口的每个比例都必须算得出来**，不许凭记忆写常量（这条有历史教训，见下）。
- 不自己发帖：dev.to / HN / 知乎 / V2EX 的发布由人执行（机器发帖会被当 spam）。

## 容易踩的坑（都是出过事的）

- **同一个数据集在仓库里有两份**：`agent_charters/data/`（随包、CLI 读）与
  `data/processed/`（发布）。只更新一份的后果是"工具打印旧数字，Release 上是新的"，
  而两边各自都能通过校验——所以有一条测试专门逐字节比对这两份。
- **量纲改过三次**：`build_test` 的对外数字走过 87% → 84.7%（推算错）→ 85.7% → **82.8%**，
  每一次都是"写死常量"或"拿组合数当份数"造成的。所以比例一律实时计算，改规则前后都要实测。
- **`brief` 的 `--lang` 不是输出语言**，是**喂给模型的提示词**语言（默认 en）；
  周边清单文案另跟 locale 走（`STATE.md` D33）。
- **`refs` 分不清"去读这个"与"别提交这个"**：禁令清单里的路径会被报成断链。
  因此（a）本文件里对 gitignore 目录的提法不加反引号，只为让 action 的报告干净——
  这属于**迁就工具**，要修的是工具；（b）action 的 `fail-on-dangling` 默认关闭。
  实测的一次：本文件开头列了 `CLAUDE.md` / `.cursorrules`（说明"语料库覆盖哪些文件类型"），
  self-check 一开 `fail-on-dangling` 就红着报"`CLAUDE.md` 找不到"——**提到 ≠ 指向**，
  `refs` 认的是字面路径，不认周围的句子在说什么（`LIMITATIONS.md` §22 第三例）。
- **照 `brief` 的槽位名当标题写，`compare` 会漏判 `agent_meta`**（实测 5 组，其余八个槽位名都认得，见 `work/case-rmas-v3.md`）。
  也就是说本工具**不能用自己给的词汇去衡量自己**——写标题时用自然说法。
- **本文件当过漏判的例子，现已修好**：2026-09-14 时 `compare AGENTS.md` 报 **8/9**——`overview` 漏了
  （标题「这是什么」不在词表里），`boundaries` 也漏（本文件写的是「**绝不**」，而规则家族里只有
  「禁止」）。当时那个「禁止」还是**假命中**：靠本节这段"解释缺口"的话里的字面词蒙到的。
  `ruleset_v0.1.9` 补了 `绝不` / `这是什么` 两条词（`LIMITATIONS.md` §22.1），现在是 **9/9 且是真凭据**。
- **但"提到即命中"这个性质还在**：正文通道认的是"哪句话里出现了某个词"，不是"这句话在说什么"。
  代价已量化（`LIMITATIONS.md` §22.2）：五个语料里**没有一个文件**靠这种元讨论句子拿标签，
  故意放宽判据也只消掉 1 个假阳性、同时丢掉 1 个真标签 ⇒ **不修这个机制**，按已知性质记着就行。
  **所以别为了让它变绿去改措辞**：文档是给智能体看的，迁就分类器只会让文档变差，还会把缺陷藏起来。
- **`LC_ALL` 优先于 `LANG`**：本机 `LANG=zh_CN.UTF-8` 但 `LC_ALL=C.UTF-8` 时，CLI 默认输出**英文**。想中文就 `--lang zh`。

## 对智能体自身的要求

- 沟通与提交信息用中文；对外文案（`SHARE.md`、dev.to 文稿）用英文，除非注明是中文渠道。
- **动手前先读** `STATE.md` §0（接手入口）/ §3（不可争议区）/ §5（下一步队列），
  以及 `LIMITATIONS.md` 里与任务相关的边界段落；不要凭会话记忆假设。
- 结论要带证据：命令 + 真实输出，不写"应该没问题"。声称"全绿"之前必须真跑一遍。
- **需要人裁定的事写进 `STATE.md` 挂账，不要自己拍板**；不确定就明说不确定。
- 会话很长时主动建议开新会话接力，并说明关键状态已写进哪个文件。
- 这个仓库的价值是**可复算**：宁可交出一个数字难看但能复现的结论，
  也不要一个好看但算不出来的结论。
