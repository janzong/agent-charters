# 真用一次：工具审计（2026-09-11）

> 起因：`STATE.md` 6.7 的收敛点是"停止加维度，去用一次"。
> 做法：拿 `brief` / `refs` 跑当事人自己的 7 份章程，逐条核对它说得对不对。
> 结论：**工具能用，但暴露了三个问题**——一个口径过宽、一个漏检、一个我自己的 bug。

## 跑的是什么

```
.codex/AGENTS.md            7/9 类  缺 overview, structure
workspace/CLAUDE.md         4/9 类  缺 overview, workflow, environment, gotchas, agent_meta
mohu/AGENTS.md              3/9 类  缺 overview, style, workflow, environment, gotchas, agent_meta
mohu/CLAUDE.md              0/9
mohu/.gemini.md             0/9
moya/CODEX.md               1/9
rmas-v3/CODEX.md            6/9 类  缺 overview, style, environment
```

## U1｜`is_pointer` 口径过宽（正确性问题，非结论问题）

**怎么发现的**：`moya/CODEX.md`（53 行，有分工表、文件边界、关键文档表）被判为
`is_pointer=True`，理由是"引用 ≥2 个 `.md` + 体积 < 2000B"。
按定义它根本不是"只是指向另一个文件"的空壳。

**11 份 `is_pointer` 逐一人工标注**（判据：正文是否只是路由/指向，还是承载了实质规则）：

| 仓库 | 正文去链接后 | 人工判定 |
|---|---|---|
| MadsLorentzen/ai-job-search | 1226B | 真（自述 "Thin-Pointer Design"，典型） |
| calesthio/OpenMontage | 329B | 真（"no instructions in this file"） |
| chroma-core/chroma | 100B | 真（"See CLAUDE.md"，教科书式） |
| plotly/dash | 180B | 真（纯目录索引 → 6 个文件） |
| JuliusBrussee/caveman | 397B | 半（内容极少，但含公开/私有可见性约束） |
| voxel51/fiftyone | 239B | 半（有 overview + 两条边界规则） |
| VoltAgent/voltagent | 1200B | **误**（有 overview 段 + 指向 docs） |
| cobusgreyling/loop-engineering | 1381B | **误**（有完整 build 命令） |
| morganlinton/Albatross | 1225B | **误**（有 CI 命令与发布规则） |
| ningzimu/codex-ppt-skill | 1147B | **误**（有完整 contribution flow） |
| buttondown/docs | 208B | **误**（3 条具体规则；此条属边界） |

**真 4 / 半 2 / 误 5。**

**根因**：`MD_LINK_PAT` 把反引号里的 `CHANGELOG.md` 也算作链接，
于是"提到两个 .md 文件名"≈"只是指针"。**这与 `refs` 第一版那个 87% 假阳性是同一个错误**
——用"出现过文件名"代理"内容为空"。同一个坑，这个项目踩了两次。

**候选修正**：`正文去链接去路径后的字节数 < 400` **或** 命中语义门
（`no instructions in this file` / `all instructions are in` / `thin-pointer` / `single source of truth`）。
与人工标注一致 **10/11**（唯一不一致的 buttondown/docs 本身就是边界情形）。

**影响面（先测再改，D21）**：

| 类别 | 现状 507 份 | 修正后 514 份 | 差 |
|---|---|---|---|
| overview | 34.9% | 34.6% | −0.3 |
| structure | 58.6% | 57.8% | −0.8 |
| build_test | 87.8% | 87.4% | −0.4 |
| style | 57.4% | 56.6% | −0.8 |
| boundaries | 66.1% | 65.4% | −0.7 |
| gotchas | 14.0% | 14.0% | ±0.0 |

**九类全部 ≤0.8 个百分点**（分母变大，方向一致向下）。**对结论无实质影响**，
但影响工具的**用户可见行为**——任何人拿一份短但有料的章程跑 `compare`，
现在都会被判成"转引用文件"并从统计里剔除。

**建议**：改，但要按版本纪律走（ruleset_v0.1.2 + 重新生成 + 测试），不单独改规则。
可以并进 v0.2。

## U2｜ownership / 分工 章节有 27% 完全没被分类

含「分工 / 职责 / ownership / maintainer」类标题的文件：**30 / 507**，
这类章节共 **33 个，其中 9 个（27%）完全没有标签**。

样例：
```
[EKKOLearnAI/hermes-studio] 「Code Ownership Map」→ `packages/client/src` - Vue 3 client, stores, routes…
[amruthpillai/reactive-resume] 「Ownership map」→ Where each concern lives, and where new code for it goes:
```
这两条显然属于 `structure`（"新代码该放哪里"），却没被识别。

**与私有实践的呼应**：私有侧 `moya/CODEX.md` 的「五层分工」表同样未被识别。
也就是说这不是孤例，是规则集在"职责/归属"这类标题上的系统性盲区。
**规模不大（9 个章节），但方向明确。**

## U3｜`refs` 在全局章程上报假断链（我自己的 bug，已修）

`~/.codex/AGENTS.md` 写着"必须读并遵守**项目根** `CODEX.md`"，
`refs` 按章程**自身所在目录**解析，于是报"2 个路径找不到"。

**错在**：全局章程指向的是**别的项目的根**，它本来就不该在自己目录下找。

**修法**：新增第四态 `unverified`——当基准目录不是仓库根（无 `.git`）时**不判断链**，
输出"基准目录不是仓库根，N 个指向无法核验"。宁可说"验不了"，不要误报。
配套两条测试：非仓库根 → `unverified`；仓库根内 → 仍报 `missing`。

## 下一步

- U1：并进 v0.2（ruleset_v0.1.2），改动小但要重新生成数据集
- U2：给 `structure` 的标题词表加「分工/职责/ownership/ownership map」类词
- U3：已修（本次提交）
