# v0.5 — 禁令与构建测试并列第一；100 份人工核对落地（`ruleset_v0.1.8`）

数据集 **v0.5**（规则集 `ruleset_v0.1.8`）。**行数与字段都不变**（558 行 × 30 列），
但**可用样本 511 → 516**、多类判定规则都动过——所以**不要把 v0.4 与 v0.5 的数字放进同一张表**。

## 改了三处会动数字的地方

1. **禁令补上正文通式**：`do not` / `don't` / `must not` / `must never`（排除
   `do not need / hesitate / worry / forget` 四种非禁令句式）。全库 2632 处命中、
   **102 份文件因此多拿到 `boundaries`**。此前正文通道只认 `never commit` /
   `do not commit` / `must not` 与中文模式——最常见的英文禁令写法整类漏掉。
2. **代码块里的 `# 注释` 不再当成标题**：`# 3. Build`、`# Run tests` 是 shell 注释，
   此前被当成章节标题。129/558 份文件受影响，`diffblue/cbmc` 的章节数 146 → 92。
3. **`is_pointer` 加反证闸**：只要文件里有它自己的规则/约束/可执行命令，就不是"纯指针"。
   5 份"短但写了规则"的文件收回统计口径，指针 7 → 2，分母 511 → 516。

## 覆盖率（分母 516）

| 类别 | v0.4（511） | **v0.5（516）** | 差 |
|---|---|---|---|
| `boundaries` 禁令 | 65.6% | **85.7%**（442） | **+20.1pp** |
| `build_test` 构建测试 | 85.9% | **82.8%**（427） | −3.1pp |
| `workflow` 流程 | 65.9% | 67.1%（346） | +1.2 |
| `structure` 架构 | 59.7% | 59.1%（305） | −0.6 |
| `style` 风格 | 56.8% | 54.5%（281） | −2.3 |
| `environment` 环境 | 44.4% | 45.0%（232） | +0.6 |
| `overview` 概览 | 34.8% | 32.2%（166） | −2.6 |
| `agent_meta` AI 行为规定 | 29.5% | 25.8%（133） | −3.7 |
| `gotchas` 坑 | 14.1% | 13.6%（70） | −0.5 |

**头条：两类并列第一。** `boundaries` 85.7% 与 `build_test` 82.8% 相差 **2.9pp**，
**小于禁令通式约 3% 的已知假阳性幅度**（`LIMITATIONS.md` §13），
所以说法是**并列第一**，不是"禁令压倒了构建测试"。

`boundaries` 必须**报两个口径**（它们回答不同问题）：

| 问法 | 定义 | 覆盖 |
|---|---|---|
| 有没有**专门写禁令的章节**？ | 章节标题命中 `Not Allowed` / `Never commit` / `禁止` … | **45.2%**（233 份） |
| **任意一处**出现禁令语句？ | 加上正文通式 | **85.7%**（442 份） |

## 100 份人工核对：第一次有实测准确率

| 组 | 份数 | 标注者 | precision | recall |
|---|---|---|---|---|
| A 主样本（唯一能代表全体） | 55 | 本智能体盲判 | **90%** | **75%** |
| B 中文普查 | 26 | **用户独立盲判** | **80%** | **79%** |
| D 稀有类加成 | 9 | 本智能体盲判 | **92%** | **84%** |

- 错标的量级已经压住（80–92%），**漏标才是主要短板**：`gotchas` recall 38%、
  `overview` 41%、`agent_meta` 55%（共同点：内容散在正文、没有专门章节）。
- 中文组暴露反方向的问题：`build_test` precision 只有 **61%**（"运行 / 命令 / 启动"
  这类动词在中文散文里被当成构建证据）。
- ⚠️ **这是 in-sample 上界**：这 100 份正是驱动本轮规则改动的样本。
  真正的留出集估计需要新一轮未参与改规则的样本。
- 详见 `work/audit/v0.5-human-vs-rule.md` 与 `LIMITATIONS.md` §16。

## 一处自我更正：59.9% → 45.2%

v0.5 的文档初稿里写了"其中 **59.9%（309 份）** 是专门开了一节写禁令"。**那个数字是错的**：
写进文档时没有记录定义，事后用三种可定义的口径都复算不出来（标题通道 233、
标题∪强模式 302、全文兜底 315）。按"专门开一节"的字面定义（标题通道）重报为
**45.2%（233/516）**，并把这个口径的定义写进表格。头条数字 85.7% 不受影响，
三站文案没有引用过这个数。全过程与教训：`LIMITATIONS.md` §17。

## 复算

```bash
pip install -e .                    # 或 pip install git+https://github.com/janzong/agent-charters
agent-charters stats                # 应打印 v0.5 / 516 份、boundaries 85.7% / build_test 82.8%
.venv/bin/python work/audit/boundaries_channels.py      # boundaries 三个口径
.venv/bin/python work/audit/human_vs_rule_v0.5.py       # 100 份核对逐类表
python work/dataset_diff.py --old data/processed/agent-charters-v0.4.parquet \
                            --new data/processed/agent-charters-v0.5.parquet --out /tmp/diff.md
```

测试：138 passed（新增围栏语言标记、块 3a/3b 的参数化锁、`is_pointer` 反证闸等）。

## 资产

- `agent-charters-v0.5.parquet` —— 主数据集（558 行 × 30 列，zstd）
- `agent_charters_v0.5.jsonl` —— 同内容的行式版
- `SHA256SUMS` —— 含 v0.2–v0.5 全部资产的校验和（旧资产继续保留，不静默替换）

> v0.4 没有单独发 Release；**v0.4 的数字请继续按 v0.4 引用**，v0.5 起对外一律用
> **85.7% / 82.8%（并列第一）**。改动清单：`work/audit/v0.1.8-changelist.md`。
