---
title: I labeled 558 AGENTS.md files. Here's what they say — and what almost nobody writes down
tags: ai, agents, opensource, data
published: false
description: 558 AGENTS.md files, labeled against 9 categories and measured on held-out samples: 85.7% ban something, 13.6% write down a gotcha — and a third of those aren't gotchas.
---

**TL;DR** — I collected **558 `AGENTS.md` files** from public repos and labeled each one against a 9-category
taxonomy with a **rule-based** classifier (no LLM in the loop, so it is auditable and recomputable). Then I
blind-labeled held-out samples and compared: **92% precision / 70% recall** on 55 English files,
**88% / 73%** on 50 Chinese files. The most common categories are prohibitions (**85.7%**) and build/test
commands (**82.8%**). The rarest: **gotchas (13.6%)** and instructions about how the agent itself should behave
(**25.8%**).

## Why bother

Almost every discussion about `AGENTS.md` is anecdote-led: *my* repo's file works, *my* agent ignores it,
a good one is a model upgrade, a bad one is worse than nothing. All of that may be true — but nobody
seems to have the distribution. So I built it: snapshot of 558 files from 558 public repos
(2026-09-10, 5.3 MB, **516 usable for statistics**), labeled, versioned, and published with the tooling.

## Method, in one paragraph

Nine categories: `boundaries`, `build_test`, `workflow`, `structure`, `style`, `environment`, `overview`,
`agent_meta` (rules about the AI itself), `gotchas`. Labeling is done by pattern rules over headings and
body text — deliberately, because a rule set can be read, argued with, and re-run, and every number below
can be recomputed from the released dataset. I then measured how well the rules match a human reading:
**100 files in-sample** (upper bound, 90%/75%) and two held-out sets I had never tuned against —
55 English (92%/70%) and 50 Chinese (88%/73%). Held-out numbers use the *conservative* reading
(items I was unsure about count as classifier errors).

## Five things the numbers say

### 1. Two categories dominate — and they are tied

| category | share of 516 files |
|---|---|
| `boundaries` (what you must never do) | **85.7%** |
| `build_test` (install/build/test/CI commands) | **82.8%** |
| `workflow` (branching, commits, review, release) | 67.1% |
| `structure` | 59.1% |
| `style` | 54.5% |
| `environment` | 45.0% |
| `overview` | 32.2% |
| `agent_meta` | 25.8% |
| `gotchas` | 13.6% |

The 2.9 pp gap between the top two is *smaller* than the known false-positive rate (~3%) of the
prohibition pattern — so the honest statement is **tied for first**, not "prohibitions beat build commands".

### 2. Nobody writes down their scars

`gotchas` is dead last at 13.6%. Worse: when people *do* open a "known issues" section, a third of it
isn't a gotcha. I hand-read 120 items from those sections:

- **58%** were readable straight from the repo (config, code, README mismatch),
- **34%** were not gotchas at all (generic advice: "remember to install dependencies"),
- **8%** needed experience or the outside world (OS behavior, an upstream outage, yesterday's incident).

That 8% is the part an agent can never derive from the code — and it is exactly the part that is
almost never written down.

### 3. The slot language models skip is `workflow`

In a controlled experiment (11 repos × 3 prompt styles), prompts that listed topics explicitly produced
**9/9 categories**, while prompts that left the slots implicit skipped `workflow` in **11 out of 11** files.
Point at `workflow` by name and it appears **3/3** times, with real content. The gap is not knowledge,
it is *questions* — which is why I turned the corpus distribution into a checklist tool.

### 4. Your weakest category depends on the language

English files fail differently from Chinese ones. English: `gotchas` recall 32–38% — the classifier
misses casual "watch out" prose. Chinese: `agent_meta` recall **26%** — Chinese files express agent rules
in the second person ("you are the dispatcher, not the executor"), and the body-pattern rules for that
category are entirely English, so the whole style is invisible to them. File-level exact agreement
(9/9 categories identical) is **12%** in both languages.

### 5. Half of these files are entry points, not documentation

**49%** point to some other file; **15%** route to a knowledge or rules directory. That's a structural
fact about the format, and it means "does this repo have an `AGENTS.md`?" is a much weaker question than
"what is actually in it".

## The tool

```
pip install agent-charters

agent-charters brief      # checklist of the 9 slots + a paste-ready prompt
agent-charters compare your-AGENTS.md   # your coverage vs the 558-file baseline
agent-charters refs your-AGENTS.md      # does your file point at paths that exist
```

Honest note: `compare` is a **checklist, not an oracle**. It warned me that one of the nine categories was
missing from a file I wrote myself — it was actually present, but the heading used the tool's own slot name
instead of natural language. That is documented in the repo (along with the exact experiment) rather than
quietly patched, because a tool that tells you "you're missing X" should be checked by a human.

## What this is not

- **Rule-based labels, not per-file human labels.** Precision/recall above are the honest measures; the
  per-category numbers in the dataset carry that error.
- **Not a representative sample of GitHub.** Repos were found through AI/agent topics and Chinese keyword
  search; the Chinese set came out 97% Chinese by construction, which says nothing about GitHub's language mix.
- **Single annotator.** The blind labeling was done by one model-driven annotator, not multiple raters.
- **A snapshot, not a trend.** A baseline of file hashes is stored so that a future re-crawl can measure
  how these files change — that measurement doesn't exist yet.

## Links

- Code + tooling: https://github.com/janzong/agent-charters (mirror: https://gitee.com/janzong/agent-charters)
- Dataset **v0.5** release + methodology, limitations and every number above: see `LIMITATIONS.md` in the repo

## The ask

I'm looking for **2–3 people who are not me** to run `compare` on an `AGENTS.md` they actually maintain and
tell me where it's wrong — missing a category you clearly have, or claiming one you don't. That is the one
piece of evidence this project doesn't have yet: an external user. Issues and comments are both fine.
