# v0.3 — 修正标题通道的子串误命中（`ruleset_v0.1.3`）

数据集 **v0.3**（规则集 `ruleset_v0.1.3`）。**字段与行数都不变**（558 行 × 30 列），
只有判定规则变了——所以**不要把 v0.2 与 v0.3 的数字放进同一张表**。

## 修了什么

`taxonomy.py` 的标题通道原是 `if k in heading.lower()`——**纯子串，没有词边界**：

- `ci` 命中 `De**ci**sions` / `Prin**ci**ples`（一批没有构建内容的章节被算成"构建测试"）
- `script` 命中 `Type**Script**`、`build` 命中 `allow**Build**s`、`review` 命中 `p**review**`
- 另有一类不是子串、但同样误命中：裸词 `make` 是普通英文动词，`Make changes` 也算"构建"

修法（两处，都不动语料、不动九类定义）：

1. **词首匹配**：命中点必须落在词首，连字符算词边界（`commit` 仍命中 `Pre-Commit`）。
   **词首前缀命中保留**（`convention`→Conventions、`boundar`→Boundary、`test`→Testing）。
2. `build_test` 删掉裸词 `make`，只留 `makefile` 与具体目标（`make build` / `make dev` …）。
   依据：511 份里 12 个标题命中裸词，逐条看 **7 份是散文**，只有 5 份真是构建工具。

## 影响（511 份可用样本）

| 类别 | v0.2 | v0.3 | 差 |
|---|---|---|---|
| 构建测试 | 87.9% (449) | **85.7% (438)** | −11 份 |
| 流程 | 66.1% (338) | 65.9% (337) | −1 |
| 环境 | 44.8% (229) | 44.4% (227) | −2 |
| AI行为 | 36.8% (188) | 36.4% (186) | −2 |
| 架构 | 59.9% (306) | 59.7% (305) | −1 |
| 风格 | 56.9% (291) | 56.8% (290) | −1 |
| 禁令 / 概览 / 坑 | — | 不变 | 0 |

- 23 处 (文件, 类别) 组合的标签**只**靠误命中撑着 → **18 处实际掉标签，无一例新增**
- 其余 5 处被正文规则或强模式通道兜住：**标签仍成立，只是证据列变干净**
  （"证据错了"和"标签错了"是两件事，本项目分开判）

**方向与排序完全不变**：`build_test` 仍是第一名、仍明显领先第二名（65.9%）。

## 一处自我更正：84.7% → 85.7%

09-12 我把 `build_test` 的修正值说成 **84.7%（433/511）**——**那个数是错的**，
正确值是 **85.7%（438/511）**。

错因：我拿审计脚本打印的"误命中**组合数**（构建测试 16 处）"直接相减，
当成"会掉标签的**文件数**"。实际掉标签的是 11 份（另 5 处被兜底通道救回）。
**推算出来的幅度不能直接进对外文案**——教训与全过程写在 `LIMITATIONS.md` §11.4。

## 其他修正

- `extract_report.md` 的类别分布原先按 518 份（实质）算，与 `category_coverage()` 的
  511 份口径差 7 份；现统一
- CLI `stats` / `compare` / `brief` 的覆盖率由整数改为**一位小数**：
  整数取整会把 85.7% 印成 85%，与对外文案对不上
- `work/substring_audit.py` 改为对**出错的那版快照**跑，并同时输出
  "误命中组合数"与"实际掉标签数"（两者混用正是上面那次推算错误的根源）
- 新增 `work/dataset_diff.py`：任意两版数据集逐行比差集

## 复算

```bash
pip install -e .            # 或 pip install git+https://github.com/janzong/agent-charters
agent-charters stats        # 应打印 build_test 85.7%
python work/dataset_diff.py --old data/processed/agent-charters-v0.2.parquet \
                            --new data/processed/agent-charters-v0.3.parquet --out /tmp/diff.md
```

测试：51 passed + 1 xfailed（新增"词中命中不许打标签／词首前缀必须打标签"两组参数化锁）。

## 资产

- `agent-charters-v0.3.parquet` —— 主数据集（558 行 × 30 列，zstd）
- `agent_charters_v0.3.jsonl` —— 同内容的行式版
- `SHA256SUMS` —— 含 v0.2 与 v0.3 两份的校验和（v0.2 资产继续保留，不静默替换）

> v0.2 的数字请继续按 v0.2 引用；v0.3 起对外**一律用 85.7%**。
