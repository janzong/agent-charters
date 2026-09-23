# dev.to 回复 · mihai_leanzero（2026-09-23 拟，**pinning 已实现，待人粘贴**）

**贴在哪**：治理审计文章（id `4720590`）
→ `mihai_leanzero` 的评论（2026-09-23T06:36:52Z，519 字符，id `3ff4f`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①认可 policy-vs-data 框架；②问 `audit_hash` 是否覆盖 policy.json 内容；③若只覆盖 findings，失败后改 policy 重跑可得到干净 hash、契约变更无痕迹；④建议把 policy 钉在 run artifacts 旁。

**本轮核实（源码实读 + 改动前后实测）**：

| 项 | 改动前 | 改动后 |
|---|---|---|
| `audit_hash` 载荷 | `runs` / `findings` / `passed` / `policy_keys`（仅键名）/ `required_artifacts` / `required_artifacts_mode` | 增加完整 canonical `policy` 对象 + `policy_sha256` |
| `max_cost_usd` 0.60 vs 100.0 | 都 clean，**同 hash** `d39ac5fe…` | 不同 hash：`79b25b9a…` vs `385f8ed6…` |
| artifacts 契约变化 | 不同 hash `49dad774…` | 仍不同 hash `2a3ce600…` |
| 当前 fixture audit_hash | `c9be0b8b…` | `b304f294834a5901101d45fb98547c233d90e16c2f7cb5b965ce16641b1acbd3` |
| policy_sha256 | — | `cda4f1bb845433e83afc7b6b5f4af210c84973e4ebf277c8757fd61a12427160` |
| policy pinning | 未实现 | `audit --output <path>` 写出含 policy 快照的审计 JSON |

真实 13-run 结果不变：默认 structured 合同 0/13、GenMentor 合同 13/13。

---

Direct answer, then the change: before your comment, the hash payload was `{runs, findings, passed, policy_keys, required_artifacts, required_artifacts_mode}`. It covered the policy's key names and the artifact contract, but not the values of `max_cost_usd`, `max_calls`, or `forbidden_markers`. Measured on the fixture, two policies differing only in `max_cost_usd` (0.60 vs 100.0) both passed and produced the same `audit_hash` `d39ac5fe…`. The gap you described was real.

I changed it. The audit result now embeds the full canonical `policy` object plus a `policy_sha256`, and `audit --output <path>` writes that pinned result next to the run artifacts. The same two policies now produce different hashes: `79b25b9a…` for 0.60 and `385f8ed6…` for 100.0. The fixture audit hash is now `b304f294…` with `policy_sha256` `cda4f1bb…`. The artifact contract still changes the hash as before (`2a3ce600…` for the GenMentor-style contract).

The failure scenario is now covered both ways: a failing run changes findings, and a clean-but-loosened policy changes `policy_sha256` and therefore the audit hash. The qualitative result on the 13 real runs is unchanged: 0/13 under the structured contract, 13/13 under the declared GenMentor contract.

Thank you for pushing on the harder version. It was the right call.
