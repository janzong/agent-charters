# dev.to 回复 · arhancanli（**已发布，API 复核通过**）

> 发布位置：第 7 篇（id `4837102`）→ `arhancanli` 评论 `3hjhf` 之下 → 我方回复 `3hk47`
> （2026-10-13T12:34:02Z，子节点关系正确，正文 2624 字符逐字复核通过）

**位置**：第 7 篇（id `4837102`，From shadow to gate）→ `arhancanli` 评论（2026-10-13T09:00:30Z，1480 字符）之下。

**对方要点**（四条，全部有效）：
1. 重建后 inbound=1.00 是**按构造成立**——表由正文引用反推，指标只验重建代码，不验「来源是否支持句子」。
2. 闸值 0.5 用修复后分布定标（P10=0.857），几乎不会触发；应改用影子期（修前）分布定标，并加独立抽样「支持率」复核。
3. 文中 0.32 与表格 0.45 两个修前基线并存，未说明是两种口径还是两批数据。
4. 追问 6/148 fallback 报告的处置——若仍带旧表，恰恰是闸门最该管的对象。

**我方核验**（rmas-v3 @ `9e46811b`）：
- 按构造：成立。`rebuild_refs_from_body`（`report_finalizer.py:378`）终稿以正文《》引用反建表；P0 表格自己就注了「按构造」。
- 两层闸：per-report `citation_gate` 阈值 0.5（`council.py:1022`，拦知识入库不拦交付）是粗粒度结构兜底；per-batch `batch_quality_contract.py:41` 的 `m1_reconcile_p10≥0.60` 才是灵敏回归警报——0.60 落在修前 P10=0.176 与修后 P10=0.83~0.889 之间，朝修前态回归即触发。对方「单看 0.5 几乎不触发」的判断对，但漏了这层批合同。
- 0.32 vs 0.45：**同一修前 148 批、两版计量**。0.32=早期口径；审计中发现 370/633 正文引用是 KB 长标题的截短版，精确交集系统性低估，改双向 ≥4 字包含匹配后同批复测 P50=0.45（`citation_audit.py` docstring、续216 回放）。文章没写清，属笔误级遗漏。
- 6/148：低密度（正文引用<3）保留素材表，但 P2-10（`3c1aa2c2`）已加 `_merge_body_cites_into_table`——把 KB 可解析的正文引用合并进表尾，不静默携带孤儿旧表；citation_gate 对所有路径一律生效。
- 「真实标题≠支持该句」：完全同意，inbound 是必要非充分条件；独立支持率抽样（人工或另一管线+区间报告）是正确的下一步。

---

Thanks — this is the most careful read the post has gotten, and two of your four points are documentation errors on my side.

**On "1.00 by construction": you're right, and it's intended.** After the fix the reference table is generated from the body's citations, so inbound measures the rebuild code, not whether sources support claims. Our own internal table even annotates the post-fix number "by construction." The honest framing is: inbound is a *structural consistency* check (table ↔ body), which is necessary but not sufficient. A citation can resolve to a real title and still not support its sentence — we don't claim otherwise, and an independent support-rate sample (human or a second pipeline, reported with an interval) is exactly the right next layer.

**On the 0.32 vs 0.45: same pre-fix batch, two versions of the metric.** During the shadow audit we found 370/633 body citations were truncated forms of longer KB titles, so exact intersection systematically undercounted. 0.32 was the earlier exact-match number; after switching to bidirectional containment matching (≥4 chars), the same pre-fix batch re-measured at P50 0.45. Post-rebuild is 1.00. The article should have said this explicitly — good catch.

**On gate calibration: there are two layers, and your critique applies to the coarse one.** The per-report gate at 0.5 is deliberately a backstop — it blocks knowledge ingestion on structural failure, and on the repaired distribution it barely fires, as you note. The sensitive alarm is the per-batch contract: P10 reconciliation must stay ≥0.60, a threshold set between the pre-fix P10 (0.176) and the post-fix P10 (0.83–0.889), so a batch drifting back toward the pre-fix regime trips it even when individual reports pass. Calibrating the *per-report* blocker on the pre-fix median would permanently reject ~half of a structurally sound batch, which is why the pre-fix distribution defines "broken" while the post-fix distribution defines the new floor.

**On the 6/148 fallbacks: they don't silently carry the old table.** Those were low-density reports (<3 body citations) where replacing the material table would have been worse. The follow-up fix keeps the material table but merges every KB-resolvable body citation into it (numbering continued, no fabrication), and the citation gate applies to all reports regardless of which path produced the table.

The general point I take from your comment: a gate calibrated where it can barely fire invites complacency, and "resolves to a real title" is a much weaker property than "supports the claim." Both are worth separating explicitly in any citation contract.
