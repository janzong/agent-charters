# 子串误命中的语料库级影响（只读评估）

- 被审计数据集：`data/processed/agent-charters-v0.2.parquet`（出错的那版）；对照修复版：`data/processed/agent-charters-v0.3.parquet`
- 实质文件：511
- **子串误命中**：23 处 (文件, 类别) 组合，涉及 23 份文件
- 其中**实际掉标签**：18 处（其余靠正文/强模式通道兜住，标签仍在，只是证据变干净）
- **仅兜底通道**（全文规则/强模式，证据弱但不是子串问题）：0 处，涉及 0 份文件

## 子串误命中按类别

- 构建测试：16 份
- AI行为：2 份
- 环境：2 份
- 架构：1 份
- 流程：1 份
- 风格：1 份

## 子串误命中明细（文件 :: 类别 :: 误命中词@标题 :: 是否掉标签）

- AgriciDaniel/claude-seo :: 构建测试 ← ci@Key Principles :: **掉**
- Comfy-Org/ComfyUI :: 构建测试 ← ci@Nodes and User-Facing Behavior :: **掉**
- Devin-AXIS/iPolloWork :: 构建测试 ← script@TypeScript :: **掉**
- HKUDS/LightRAG :: AI行为 ← tone@Full suite — ~7000 tests, >6 min; milest :: **掉**
- Human-Agent-Society/CORAL :: 构建测试 ← ci@2. Scope discipline :: **掉**
- Kiln-AI/Kiln :: 构建测试 ← ci@Never Make Legal Decisions as an Agent :: 保留（另有正文/强模式证据）
- QwenLM/qwen-code :: 架构 ← structure@Core Infrastructure Is Maintainer-Only ( :: **掉**
- Utopai-Research/pai-pro :: 构建测试 ← ci@Editing principles :: 保留（另有正文/强模式证据）
- ValueCell-ai/ClawX :: 构建测试 ← ci@Cursor Cloud specific instructions :: 保留（另有正文/强模式证据）
- every-app/open-seo :: 构建测试 ← ci@Engineering principles :: **掉**
- gotalab/cc-sdd :: 构建测试 ← ci@Steering vs Specification :: **掉**
- icip-cas/PPTAgent :: 构建测试 ← ci@3. Simplicity As A Constraint :: 保留（另有正文/强模式证据）
- jacklandrin/OnlySwitch :: 构建测试 ← ci@Project-specific working rules :: **掉**
- kenryu42/cc-safety-net :: 构建测试 ← ci@Scope Discipline :: **掉**
- kortix-ai/suna :: 环境 ← tool@Driving the real UI (chrome-devtools MCP :: **掉**
- mukul975/Anthropic-Cybersecurity-Skills :: 构建测试 ← script@Writing a description :: **掉**
- nesquena/hermes-webui :: 环境 ← install@Onboarding and reinstall support :: **掉**
- superagent-ai/grok-cli :: 构建测试 ← ci@Cursor Cloud specific instructions :: **掉**
- tastyeffectco/sandboxd :: 流程 ← review@3. open the preview (browsers resolve *. :: **掉**
- MichaelSimoneau/michael-simoneau-com :: 风格 ← format@Learned Information (Dotcom) :: **掉**
- fancy1108/Clutch :: 构建测试 ← ci@Cursor Cloud specific instructions :: 保留（另有正文/强模式证据）
- sebastien/monitoring :: AI行为 ← tone@auth_strategy = keystone :: **掉**
- stefan-vatov/hardertofool :: 构建测试 ← ci@At the Point of Decision :: **掉**

## 仅兜底通道明细（不计入子串问题）

