# 纵向面板 T1 预注册（2026-12-10）

> 预注册时间：2026-10-26。本文只固定 T1 的采集与读法，不采数据、不改规则、不重标历史。

## 1. 固定项

- **期次**：T1 = 2026-12-10 03:30（本机 timer 已装）。
- **面板**：沿用 2026-09 vintage 的 558 个仓库。
- **主文件**：`AGENTS.md`。
- **比较基线**：
  - T0 = 2026-09-10；
  - T0.5 = 2026-09-16。
- **schema**：与 T0 完全一致：

```text
repo_full_name
file_path
file_sha
bytes
doc_language
retrieved_at
fetch_status
```

- **规则版本**：沿用 `ruleset_v0.1.9` 与当期 extractor 版本。
- **原始正文**：只落本机 `data/cache/panel/`，不入 Git、不入 Release。
- **历史行**：T0 / T0.5 永不重标。

## 2. 采集动作

1. 采集前备份：

```bash
cp data/raw/full_manifest.jsonl data/raw/full_manifest.pre-T1.jsonl
```

2. 确认 timer 与 stamp：

```bash
systemctl --user list-timers agent-charters-panel.timer
stat ~/.local/share/systemd/timers/stamp-agent-charters-panel.timer
```

3. 采集命令：

```bash
.venv/bin/python work/panel_run.py --date 2026-12-10
```

4. 若 timer 自动执行，只核对产物，不重复跑。

## 3. 主指标（预注册）

只预注册四个描述性指标，不在 T1 后新增指标：

### 3.1 存活率

```text
alive / 558
```

判定：

- repository still returns 200 and is not archived ⇒ alive；
- 404 / 410 / confirmed missing ⇒ dead；
- fetch incomplete / rate limited ⇒ unknown，不计死。

### 3.2 章程在场率

```text
same-path present / 558
```

指针文件不算消失；必须跟随指针并记录目标是否可达。

### 3.3 内容变化率

```text
file_sha changed since T0 / present files
```

同时输出 T0.5 → T1 的短期变化，但主口径固定为 T0 → T1。

### 3.4 语义稳态

```text
repository has push but file_sha unchanged / unchanged files
```

解释边界：

- 只代表文件内容未变；
- 不代表章程被遵守；
- 不代表智能体没有使用其他配置文件。

## 4. 附加观察（不进入主结论）

这些字段只作为异常探针：

```text
same-sha template clusters
pointer-only files
moved repositories
new archived repositories
```

T1 只报告数量，不做生态趋势解释。趋势判断至少等 T2。

## 5. 禁止事项

1. 不改 T0 / T0.5 行。
2. 不用新规则重算旧期。
3. 不把 unknown 计成 dead。
4. 不把指针文件直接计成 substantive charter。
5. 不把同 sha 指针簇解释为机写模板。
6. 不因 T1 单点变化改变采样框。
7. 不在 T1 采集时新增“人写 / 机写”维度；该事项仍待人裁定。

## 6. 产物与提交

提交：

```text
data/processed/baseline-2026-12-10.tsv
work/panel-2026-12-10.json
work/longitudinal-T1-report.md
```

提交信息：

```text
data(panel): add 2026-12-10 T1 vintage
```

报告必须给出：

```text
row count
fetch status counts
alive / dead / unknown
present / missing
changed / unchanged
template clusters
pointer counts
```

## 7. 预注册解释边界

T1 只有三个时间点：

```text
T0
T0.5
T1
```

它能够回答：

- 90 天内多少仓库仍存活；
- 多少章程仍在原路径；
- 多少文件 sha 改变；
- 有无明显模板簇变化。

它不能回答：

- 章程是否更有效；
- 生态是否已经转向 CLAUDE.md；
- 机写比例是否上升；
- 章程治理质量是否提高；
- 长期存活原因。

这些判断需等 T2/T3/T4 序列。
