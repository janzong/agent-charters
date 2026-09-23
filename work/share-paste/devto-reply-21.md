# dev.to 回复 · mihai_leanzero（2026-09-23 拟，待人粘贴）

**贴在哪**：治理审计文章（id `4720590`）
→ `mihai_leanzero` 的评论（2026-09-23T06:36:52Z，519 字符，id `3ff4f`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认可 policy-vs-data 框架（同 13 run，0/13 vs 13/13，数据没动、契约动了）；②问 `audit_hash` 是否覆盖 policy.json 内容本身，还是只覆盖 findings；③风险：若只覆盖 findings，失败后编辑 policy 重跑可得到干净 hash、契约变更无痕迹；④建议把 policy 钉在 run artifacts 旁，而不只是声明。

**本轮核实（源码实读 + 实测）**：

| 项 | 结果 |
|---|---|
| `audit_hash` 载荷字段 | `runs`、`findings`、`passed`、`policy_keys`（仅排序后的键名）、`required_artifacts`、`required_artifacts_mode` |
| 覆盖 policy 值 | 只覆盖 artifacts 契约值（列表 + mode） |
| 不覆盖 policy 值 | `max_cost_usd`、`max_calls`、`forbidden_markers` 的具体值 |
| policy-a（max_cost 0.60）vs policy-b（max_cost 100.0） | 都 clean，**audit_hash 相同** `d39ac5fe0389d2d0f8a92bbf0b8df656f519c822038155e2e200f6b7af169c77` |
| policy-c（artifacts 改为 archive.json + summary.json） | 不同 hash `49dad7740a582b00284602dc4b889e069e66ad757c661fc7723b4fd1b3cee2ee` |
| policy pinning | 尚未实现 |

---

Direct answer: it covers the policy's key names, and the artifact contract's values, but not the numeric values of the caps or the marker list.

The hash payload is `{runs, findings, passed, policy_keys, required_artifacts, required_artifacts_mode}`. `policy_keys` is the sorted key list, so `max_cost_usd` appears as a key but its value does not. `required_artifacts` and `required_artifacts_mode` are included as values.

Measured on the fixture: two policies identical except `max_cost_usd` 0.60 vs 100.0 both pass and produce the same `audit_hash` `d39ac5fe0389d2d0f8a92bbf0b8df656f519c822038155e2e200f6b7af169c77`. Changing `required_artifacts` from the structured pair to `["archive.json","summary.json"]` produces a different hash `49dad7740a582b00284602dc4b889e069e66ad757c661fc7723b4fd1b3cee2ee`. So the artifact contract is bound; the cap values are not.

Your failure scenario is partly covered: a failing run has findings, so editing the policy and re-running changes the findings list and the hash. What is not covered is the quieter case: a clean policy whose cap is loosened (0.60 → 100.0, or a marker removed) can produce the same clean hash with no trace that the contract moved.

Pinning the policy content is the right fix. The honest version is to hash the canonical full policy into the audit result and store the policy alongside the run artifacts, so the contract itself is part of the evidence. That is not implemented yet; it is the next thing I would build.
