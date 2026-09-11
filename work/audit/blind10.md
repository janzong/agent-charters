# 盲判组（前 10 份，主样本随机抽出的前 10 个）

> 只判这 10 份。判完再打开 `work/audit/v0.2-agent-verdicts.md` 对比。
> 每条只需在文末写一句：`1. 准确` 或 `1. 漏标:坑,流程` 或 `1. 错标:风格`，可加几个字理由。

> 抽查口径：**漏标**＝原文明明有这类内容却没打上；**错标**＝打上了但原文没有。

> ⚠ **判「错标」请回到原文**（每条的完整原文路径在条目里）：「命中证据」列是**抽取器用的证据**，它本身可能是错的
> （实测 `ci` 命中了 `De**ci**sions`）。证据列错 ≠ 类别错，两件事分开判。


---

### 1. `AAswordman/Operit` — AGENTS.md
- 语言 zh ｜ 2428 字节 ｜ 2 章节 ｜ 7679 ★ ｜ 许可 LGPL-3.0
- **规则分配**：构建测试、流程、禁令
- 命中证据：
  - 构建测试：[强模式命中]（全文正则，跨语言通道）
  - 流程：[全文规则命中]（无标题/正文信号时的兜底通道）
  - 禁令：执行准则 ← heading:准则
- 文件标题（2）：AGENTS.md / 执行准则
- 原文摘录（前 600 字）：

```text
# AGENTS.md
执行准则章节是对Agent, AI 或 你 的限制，不是对项目或者软件的限制，无需写入文档
## 执行准则
- 默认不要执行编译、构建或测试命令。
- 只有在用户明确要求时，才执行编译/构建/测试（例如 `./gradlew :app:compileDebugKotlin`、`npm run build`、`pnpm run build`）。
- 创建分支时，必须遵守 `docs/doc-src/dev-core/CONTRIBUTING.md` 中“创建 Pull Request”的分支命名规范。
当针对用户接口的方案更换时，一定要询问用户是否该版本为已发布版本。如果是，请做向前兼容。如果不是，请彻彻底底把老的方案的一切代码全部清理，除非是还能用到的一些部分就继续留着。
Don't Break Userspace ，但是开发中能内部消解的方案更换不算，只要用户能尽可能拿到一样的接口就行
但是需要给协作者必要的便利，提供恰当的文档说明和ci脚本
如果是方案迭代，则只要在原来的基础上进行正常增删即可。
除非用户要求，禁止写一切的回退代码。优先查找真正的发生原因。这是一条严格执行的规则，回退是正常被禁止的。
严令禁止各种回退逻辑，包括“xxx才会退回”、“降级处理”、“优先 再”、“如果没有 就””要加fallback“这种字眼，绝对禁止！！！绝对禁止！！！这种
```
- 完整原文：`data/raw/full/AAswordman__Operit.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 2. `Kiln-AI/Kiln` — AGENTS.md
- 语言 en ｜ 4433 字节 ｜ 9 章节 ｜ 5056 ★ ｜ 许可 NOASSERTION
- **规则分配**：概览、构建测试、流程、环境、禁令、AI行为
- 命中证据：
  - 概览：Project Overview ← heading:overview ；Tech Stack ← heading:tech stack
  - 构建测试：Never Make Legal Decisions as an Agent ← heading:ci
  - 流程：Code Review Guidelines ← heading:review
  - 环境：Agent Tools ← heading:tool
  - 禁令：Never Make Legal Decisions as an Agent ← heading:never
  - AI行为：Agent Tools ← heading:agent tool ；Agent Prompts ← heading:agent prompt
- 文件标题（9）：Project Overview / Project Goals / Tech Stack / Agent Tools / Agent Prompts / General Agent Guidance / Code Review Guidelines / Never Make Legal Decisions as an Agent / Final
- 原文摘录（前 600 字）：

```text
## Project Overview
Kiln is an app for building AI systems. It includes evals, synthetic data gen, fine tuning, RAG, and more. It has an intuitive UI as well as a python library.
This repo is a monorepo containing all of the source code, in the following structure:
- libs/core - a python library with the core functionality of Kiln
- libs/server - a FastAPI REST server wrapping the core library
- app/web_ui - our svelte web app for Kiln. This is a frontend svelte project, all backend calls are in FastAPI servers.
- app/desktop - our python desktop app, which is a pyinstaller app which runs a Fa
```
- 完整原文：`data/raw/full/Kiln-AI__Kiln.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 3. `KomorGiaoGiao/FirstCoder` — AGENTS.md
- 语言 en ｜ 3847 字节 ｜ 8 章节 ｜ 198 ★ ｜ 许可 MIT
- **规则分配**：架构、构建测试、风格、流程、环境、禁令
- 命中证据：
  - 架构：Project Structure & Module Organization ← heading:structure
  - 构建测试：Build, Test, and Development Commands ← heading:build, body:```(?:bash|sh|shell)?\n[^`]{ ；Testing Guidelines ← heading:test
  - 风格：Coding Style & Naming Conventions ← heading:style
  - 流程：Commit & Pull Request Guidelines ← heading:pull request
  - 环境：Security & Configuration Tips ← heading:config
  - 禁令：Security & Configuration Tips ← body:\bdo not commit\b ；Benchmark Evidence and Recovery ← body:\bnever commit\b
- 文件标题（8）：Repository Guidelines / Project Structure & Module Organization / Build, Test, and Development Commands / Coding Style & Naming Conventions / Testing Guidelines / Commit & Pull Request Guidelines / Security & Configuration Tips / Benchmark Evidence and Recovery
- 原文摘录（前 600 字）：

```text
# Repository Guidelines
## Project Structure & Module Organization
FirstCoder is a Python local coding-agent project. Source code lives in `firstcoder/`, with clear domain modules: `agent/` for orchestration, `app/` for the Textual TUI, `context/` for session context and compaction, `providers/` for model adapters, `tools/` for tool execution, `permissions/` for policy and grants, and `session/` for persistence and resume flows. Tests live in `tests/` and generally mirror the source domains. Design notes and implementation plans are in `docs/`; benchmarks and learning sandboxes are under `benc
```
- 完整原文：`data/raw/full/KomorGiaoGiao__FirstCoder.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 4. `OpenBMB/UltraRAG` — AGENTS.md
- 语言 en ｜ 17069 字节 ｜ 59 章节 ｜ 5686 ★ ｜ 许可 Apache-2.0
- **规则分配**：架构、构建测试、风格、流程、环境、禁令、AI行为
- 命中证据：
  - 架构：2) Repository Map (What Matters Most) ← heading:repository map ；7) Core Python Modules (Authoritative Guide) ← heading:module
  - 构建测试：Phase A: Build ← heading:build ；Phase B: Run ← heading:run
  - 风格：8.1 Registration styles ← heading:style ；17) Coding Standards (Repository-Conformant) ← heading:standard
  - 流程：5.4 Branch block ← heading:branch
  - 环境：5.5 Prompt vs Tool step semantics ← heading:tool ；8.4 Entrypoint requirement ← heading:requirement
  - 禁令：6) Variable Resolution and Data Flow Rules ← heading:rule
  - AI行为：16.5 Modify UI pipeline behavior ← heading:behavior
- 文件标题（59）：AGENTS.md / 1) Project Identity / 2) Repository Map (What Matters Most) / 3) Mental Model of the System / 4) Two-Phase Execution Lifecycle / Phase A: Build / Phase B: Run / 5) Pipeline DSL Reference / 5.1 Plain step / 5.2 Step with input/output remapping / 5.3 Loop block / 5.4 Branch block / 5.5 Prompt vs Tool step semantics / 6) Variable Resolution and Data Flow Rules
- 原文摘录（前 600 字）：

```text
# AGENTS.md
This document is the primary engineering guide for autonomous coding agents working in the `UltraRAG` repository.
Use this file as the source of truth for architecture, conventions, workflows, and safe change patterns.
If `CLAUDE.md` exists, it should only point to this file.
---
## 1) Project Identity
`UltraRAG` is a lightweight RAG framework built around the Model Context Protocol (MCP).
The key design choice is strict modularization: retrieval, prompting, generation, routing, memory, and evaluation are implemented as independent MCP servers orchestrated by YAML pipelines.
Curren
```
- 完整原文：`data/raw/full/OpenBMB__UltraRAG.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 5. `QuintinShaw/pi-dynamic-workflows` — AGENTS.md
- 语言 en ｜ 685 字节 ｜ 2 章节 ｜ 502 ★ ｜ 许可 MIT
- **规则分配**：流程
- 命中证据：
  - 流程：Workflow documentation ← heading:workflow
- 文件标题（2）：Repository guidance / Workflow documentation
- 原文摘录（前 600 字）：

```text
# Repository guidance
## Workflow documentation
Before changing the workflow runtime, tool API, capability contract, or `workflow-authoring` skill, read [Protected workflow-authoring guidance](CONTRIBUTING.md#protected-workflow-authoring-guidance).
- Keep stable capability facts in the executable capability contract and generated documentation.
- Keep detailed authoring guidance in the on-demand skill, not the always-on prompt.
- Do not copy live model or agent-type catalogues into static guidance.
- Run `npm run context:check` with the other checks listed in the contributor guide.
- If a prot
```
- 完整原文：`data/raw/full/QuintinShaw__pi-dynamic-workflows.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 6. `VoltAgent/voltagent` — AGENTS.md
- 语言 en ｜ 1519 字节 ｜ 6 章节 ｜ 10585 ★ ｜ 许可 MIT
- **规则分配**：概览、构建测试、坑
- 命中证据：
  - 概览：What is VoltAgent? ← heading:what is ；Overview ← heading:overview
  - 构建测试：Validating Changes ← body:```(?:bash|sh|shell)?\n[^`]{
  - 坑：Gotchas ← heading:gotcha
- 文件标题（6）：VoltAgent / What is VoltAgent? / Overview / Validating Changes / Important Notes for AI Agents / Gotchas
- 原文摘录（前 600 字）：

```text
# VoltAgent
VoltAgent is an open-source TypeScript framework for building and orchestrating AI agents.
## What is VoltAgent?
VoltAgent is a comprehensive framework that enables developers to build sophisticated AI agents with memory, tools, observability, and sub-agent capabilities. It provides direct AI SDK integration with comprehensive OpenTelemetry tracing built-in.
## Overview
- View [`docs/structure.md`](./docs/structure.md) for the repository structure and organization
- View [`docs/tooling.md`](./docs/tooling.md) for development tools and utilities
- View [`docs/testing.md`](./docs/tes
```
- 完整原文：`data/raw/full/VoltAgent__voltagent.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 7. `bostrot/wsl2-distro-manager` — AGENTS.md
- 语言 en ｜ 67761 字节 ｜ 18 章节 ｜ 3993 ★ ｜ 许可 NOASSERTION
- **规则分配**：概览、架构、构建测试、风格、流程、禁令、坑、AI行为
- 命中证据：
  - 概览：What This Is ← heading:what this is
  - 架构：Key Directories ← heading:key director ；Widget Structure Notes ← heading:structure
  - 构建测试：Commands ← heading:command ；Post-Change Verification ← heading:verification
  - 风格：State Management Patterns ← heading:pattern
  - 流程：Commits ← heading:commit ；Version Management ← heading:version
  - 禁令：[全文规则命中]（无标题/正文信号时的兜底通道）
  - 坑：fluent_ui Gotchas ← heading:gotcha ；WSL / Windows Subprocess Gotchas ← heading:gotcha
  - AI行为：WSL2 Distro Manager — Agent Instructions ← heading:agent instruction
- 文件标题（18）：WSL2 Distro Manager — Agent Instructions / What This Is / Commands / Post-Change Verification / Commits / Build Order (CI) / Version Management / Key Directories / Testing / i18n / Community catalogue (`cdn/scripts.json`) / Release Pipeline (`.github/workflows/releaser.yml`) / Navigation / fluent_ui Gotchas
- 原文摘录（前 600 字）：

```text
# WSL2 Distro Manager — Agent Instructions
## What This Is
Flutter desktop app for managing WSL distributions on Windows x64 (primary target), with a native macOS port that manages Linux/macOS VMs through Apple's Virtualization.framework instead. Uses Provider for state management and `fluent_ui` for Windows-native UI.
## Commands
| Task | Command | Notes |
|------|---------|-------|
| Get deps | `flutter pub get` | 2-3 min, do not cancel |
| Static analysis | `flutter analyze --no-fatal-infos` | Must pass before PR; the same gate `macos.yml` runs. Warnings and errors fail it, the pre-existing
```
- 完整原文：`data/raw/full/bostrot__wsl2-distro-manager.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 8. `career-ops-hq/career-ops` — AGENTS.md
- 语言 mixed ｜ 52787 字节 ｜ 37 章节 ｜ 70967 ★ ｜ 许可 MIT
- **规则分配**：概览、构建测试、风格、禁令、AI行为
- 命中证据：
  - 概览：What is career-ops ← heading:what is
  - 构建测试：First Run — Onboarding (IMPORTANT) ← heading:run ；Offer Verification -- MANDATORY ← heading:verification
  - 风格：Stack and Conventions ← heading:convention ；TSV Format for Tracker Additions ← heading:format
  - 禁令：Source-of-Truth Boundary (CRITICAL) ← heading:boundar ；Where rules live ← heading:rule
  - AI行为：Auto-memory scope (clarification, not exception) ← body:\btone\b ；Personalization ← heading:persona
- 文件标题（37）：Career-Ops -- AI Job Search Pipeline / Origin / Data Contract (CRITICAL) / Source-of-Truth Boundary (CRITICAL) / Auto-memory scope (clarification, not exception) / Where rules live / Untrusted External Content (CRITICAL) / Update Check / What is career-ops / Codex invocation / Main Files / Plugins (optional) / First Run — Onboarding (IMPORTANT) / Step 0: Free Tier Check
- 原文摘录（前 600 字）：

```text
# Career-Ops -- AI Job Search Pipeline
## Origin
Built and used by [santifer](https://santifer.io) to evaluate 740+ offers, generate 100+ tailored CVs, and land a Head of Applied AI role. The archetypes, scoring, and negotiation scripts reflect that search; his portfolio is also open source: [cv-santiago](https://github.com/santifer/cv-santiago).
**It works out of the box, but it's designed to be made yours.** You (AI Agent) can edit the user's files: they say "change the archetypes to data engineering roles" and you do it. That's the whole point.
## Data Contract (CRITICAL)
Two layers — full 
```
- 完整原文：`data/raw/full/career-ops-hq__career-ops.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 9. `deepseek-ai/deepseek-harness` — AGENTS.md
- 语言 en ｜ 16619 字节 ｜ 12 章节 ｜ 218764 ★ ｜ 许可 MIT
- **规则分配**：架构、构建测试、风格、流程、禁令
- 命中证据：
  - 架构：Repository layout ← heading:layout
  - 构建测试：Commands ← heading:command, body:```(?:bash|sh|shell)?\n[^`]{ ；Run relevant checks locally ← heading:run
  - 风格：Conventions ← heading:convention ；Defensive patterns ← heading:pattern
  - 流程：Pre-stable APIs and released Session data ← heading:release
  - 禁令：Secrets / .env ← body:\bnever commit\b
- 文件标题（12）：AGENTS.md / Pre-stable APIs and released Session data / Repository layout / Commands / Host sandbox failures / Run relevant checks locally / Secrets / .env / Conventions / Defensive patterns / Type safety and documentation / Editing these instructions / Vendoring policy
- 原文摘录（前 600 字）：

```text
# AGENTS.md
DeepSeek Harness is an all-plugin Cordis agent harness. Read [docs/architecture.md](docs/architecture.md) before changing `packages/`; follow [docs/AGENTS.md](docs/AGENTS.md) for documentation.
## Pre-stable APIs and released Session data
Public APIs are pre-stable; update every consumer. [Session version/status](docs/session-format-status.md) defines the authorities. [Adjacent migration](.agents/notes/implemented/architecture/2026-08-31-released-session-format-migrations.md) may add a version-named successor but never move, overwrite, or delete committed generations; predecessors 
```
- 完整原文：`data/raw/full/deepseek-ai__deepseek-harness.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：
### 10. `get-bb/bb` — AGENTS.md
- 语言 en ｜ 6309 字节 ｜ 9 章节 ｜ 3488 ★ ｜ 许可 MIT
- **规则分配**：构建测试、流程、禁令
- 命中证据：
  - 构建测试：Task Completion ← heading:task ；Build And Test ← heading:build
  - 流程：Issues, Pull Requests, And Debugging ← heading:pull request
  - 禁令：Build And Test ← body:\bnever commit\b
- 文件标题（9）：Codebase Guidelines / Task Completion / Code And Contracts / Server And Daemon / CLI And Plugin API / Data Access / UI / Build And Test / Issues, Pull Requests, And Debugging
- 原文摘录（前 600 字）：

```text
# Codebase Guidelines
## Task Completion
- Carry the requested change through implementation, relevant verification, and fixes for failures it causes. Continue authorized, reversible local work without asking for approval at each step; ask when a missing user decision blocks progress.
- Match verification to the change. Once relevant checks pass, broaden or repeat them only for new changes, failures, or unresolved concerns.
- Read the linked guidance when its topic applies to the task.
## Code And Contracts
- Code comments are forbidden, except for semantic tool directives and Plugin SDK decla
```
- 完整原文：`data/raw/full/get-bb__bb.md`（本页只摘前 600 字）
- 判定：□ 准确　□ 漏标（缺哪类：______）　□ 错标（多哪类：______）　备注：

---

## 我的判定（请填在这里）

1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
