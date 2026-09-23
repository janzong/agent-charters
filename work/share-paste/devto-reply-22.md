# dev.to 回复 · axiru（2026-09-23 拟，待人粘贴）

**贴在哪**：治理审计文章（id `4720590`）
→ `axiru` 的评论（2026-09-23T14:37:38Z，475 字符，id `3ffnf`，顶层评论）右下角 **Reply** → 粘贴 `---` 之后的内容。

**对方要点**：①“passed 的 run”与“allowed 的 run”是两种证明；②认可 findings 封存方向；③退款/支付类工具的 sealed object 必须包含 provider call 之前的决策本身（allow/hold/deny + reason code），而不只是资金流动后的 artifacts；④问扩展到 money tool 时，会把 policy document hash 钉进同一 receipt，还是只钉 findings 列表。

**本轮核实（源码实读 + 实测）**：

| 项 | 结果 |
|---|---|
| 当前 main | `4b739ac0` |
| `audit --output` receipt | 9 键：`runs` / `findings` / `passed` / `policy_keys` / `policy` / `policy_sha256` / `required_artifacts` / `required_artifacts_mode` / `audit_hash` |
| fixture `audit_hash` | `b304f294834a5901101d45fb98547c233d90e16c2f7cb5b965ce16641b1acbd3` |
| fixture `policy_sha256` | `cda4f1bb845433e83afc7b6b5f4af210c84973e4ebf277c8757fd61a12427160` |
| policy 快照内容 | 含 `max_cost_usd`、`required_artifacts`、`forbidden_markers` 等完整值 |
| pre-call allow/hold/deny/receipt | 源码中不存在；当前 `validate` / `report` / `audit` 均针对已有 run artifacts（post-hoc） |
| deletion proof | 合成演练，不是资金/支付前置决策 |

---

Direct answer: yes — the policy document hash goes into the same receipt, not only the findings list. The current audit result pins the full canonical `policy` object plus `policy_sha256` (the fixture is `b304f294…` with `policy_sha256` `cda4f1bb…`), and `audit --output <path>` writes that 9-key receipt next to the run artifacts. `audit_hash` is computed over the result including the policy snapshot, so the contract cannot move without changing the hash.

Your stronger point is the one I cannot answer from the current implementation: a pre-call allow/hold/deny decision is a different object from a post-hoc audit. `passed` here means "no findings under the declared policy for the artifacts that exist"; it is not an authorization issued before the provider call. The tool is a post-hoc validator — `validate`, `report`, and `audit` all run over existing run artifacts, and the deletion proof is a synthetic drill.

If this became a money tool, the receipt I would want is a pre-call record with `policy_sha256`, the decision (`allow` / `hold` / `deny`), a reason code, and a hash of the inputs the decision saw; the post-hoc audit would then chain to that pre-call receipt rather than restate the decision after the money moved. That is not implemented, and I will not claim it is. It is the right next layer for a payout path.

So: policy hash pinned — yes, already. Pre-call decision receipt — no, not yet; that is a separate design.
