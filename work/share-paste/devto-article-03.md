---
title: How common is AGENTS.md, really? I sampled GitHub: 6.2% of active repos, 1.0% of all repos
tags: ai, agents, github, opensource
series: AGENTS.md in the wild
published: false
description: My last two posts gave rates with a self-selected denominator. This one fixes that: a generation-sliced sample of active repos (6.2%) and a uniform sample of the whole repo population (1.0%), plus the ecosystem numbers that surprised me.
---

**Short version:** Every rate in my previous two posts had a denominator I picked myself — the 558 repos
that already had an `AGENTS.md`. That is a fine way to describe a corpus and a terrible way to answer
"how common is this?". So I sampled GitHub two different ways:

- **6.2%** of *active* repos (pushed in the last 90 days, not a fork, not archived) contain an `AGENTS.md`
  — 51 of 817, 95% CI [4.8, 8.1]
- **1.0%** of *all* public repos do — 9 of 924, 95% CI [0.5, 1.8]

Same file, same counting rule, two numbers that differ by 6×. Which one you quote depends entirely on
the question you are asking, and I had been quietly dodging that choice.

Three things I did not expect, in order of how much they changed my mind:

1. **`CLAUDE.md` is at 5.4% of active repos.** Statistically indistinguishable from `AGENTS.md`. If you
   assumed one format won, it has not.
2. **93% of public repos have not been pushed in 90 days**, 29% are forks, and **8.3% are completely
   empty**. "GitHub" as a population is mostly a graveyard, which is why the stock rate is so low.
3. **Most `AGENTS.md` files in the wild are tombstones.** Of the 9 files my population sample found,
   **7 were in repos that have not been pushed in three months.**

## Why the denominator was missing

Here is the trap I was in. To build the corpus I searched GitHub for repos containing an `AGENTS.md`, then
labeled what I found. Every percentage since — "85.7% of files prohibit things", "13.6% record a
gotcha" — has a denominator of *files that already exist*. Those numbers are real and I stand by them,
but they cannot answer the question every reader actually has: **should I write one of these?**

For that you need a sample of repos drawn **independently of whether they have the file**. That is a
different sampling problem, and it needs two different frames, which I kept conflating:

| quantity | question it answers | frame |
|---|---|---|
| **stock rate** | "is this mainstream?" | every public repo |
| **active rate** | "is this what working projects do?" | repos pushed in the last 90 days |
| **trend** | "is it spreading?" | rates by repo creation year |

Mixing them produces confident nonsense, because the stock population is dominated by abandoned
one-off repos and the active population is not.

I wrote the decision rule down **before** running anything, so I could not move the goalposts after
seeing the number: **<1% ⇒ describe it as an early-adopter curiosity; 1–5% ⇒ "early but measurable",
and every rate must be labeled as in-corpus or ecosystem-wide; >10% ⇒ "standard practice".** It landed
in the middle band, slightly high — so: not a curiosity, not a standard either.

## Method, briefly

Both frames use **one tree call per repo** —
`GET /repos/{owner}/{repo}/git/trees/HEAD?recursive=1` — and check every path with a case-insensitive
match on the filename. Recursive matters: a root-only check would miss `docs/AGENTS.md` and friends and
under-count. Roughly 1,900 repos, all responses cached, seed `20260918`.

**Frame A — active rate, by creation cohort.** For each year 2010–2026 I picked one random slice of
creation time, queried
`created:<slice> pushed:>2026-06-20 fork:false archived:false`, **pulled every result** (rather than
taking the top page, which is ranked by GitHub's relevance and would bias toward popular repos), then
randomly sampled 50 repos from the slice. A 2026 week contains ~62,000 active repos, which exceeds the
1,000-result search cap, so recent cohorts narrowed to a random day and then a random hour.

**Frame B — stock rate, unweighted.** GitHub search cannot give you a random sample of the population —
there is no random sort, and ranking favors stars and activity. So I enumerated the ID space instead:
binary-searched the current maximum repo ID (1,375,203,308), then sampled IDs uniformly and asked
`GET /repositories/{id}`. **Only 35% of IDs correspond to an existing public repo** (the rest are
deleted, private, or never existed), so 1,000 usable repos cost 2,920 probes.

## Results

**Active repos (Frame A, n=817):**

```
AGENTS.md                        6.2%   [4.8, 8.1]
CLAUDE.md                        5.4%   [4.0, 7.2]
.github/copilot-instructions.md  1.1%   [0.6, 2.1]
.cursorrules / .cursor/rules     0.7%   [0.3, 1.6]
```

**All public repos (Frame B, n=924):**

```
all public repos                 1.0%   [0.5, 1.8]
non-fork, non-archived           0.5%   [0.2, 1.4]
AGENTS.md ∩ CLAUDE.md             18 repos
CLAUDE.md only, no AGENTS.md      26 repos
```

## The number I got wrong twice

In my corpus, **59.1%** of repos that have an `AGENTS.md` also have a `CLAUDE.md`. In the wild it is
**35.3%**. Both are correct; they are answered by different populations, and only one of them is
"typical".

The reason for the gap is a selection effect I should have predicted: a repo that has one agent
instruction file is already a repo whose author cares about agent tooling, so it is much more likely to
have several. My corpus is a sample of the *enthusiastic* end, and it over-represents multi-tool setups
by about 1.7×. If I had quoted 59.1% as a base rate, I would have been describing my sample, not the
world.

## The trend measurement failed, and I am not going to dress it up

I wanted to show adoption rising by cohort and I could not measure it. In Frame A,
`p_2026 / p_≤2022 = 0.67×` — if anything, *older* active repos are more likely to have the file.

That number is not evidence that adoption is flat, because creation year and repo age are perfectly
confounded. A repo created in 2010 that is still receiving pushes in 2026 is a **survivor** — a project
that lived long enough to accumulate conventions. A repo created in 2026 is mostly somebody's first
weekend project. The cohort axis is really an age axis, and age predicts having-writers and having-time.

Separating those would require reading commit history to find when each file was *added*. I did not do
that, so the honest deliverable here is "not measured", not "not spreading".

## A GitHub API gotcha worth knowing

Half a day of this project went into a bug that was not a bug. `403` from the REST API has **three**
distinct meanings, and you have to read the body to tell them apart:

1. **Primary rate limit** — `X-RateLimit-Remaining: 0`.
2. **Secondary rate limit** — burst/concurrency. GitHub's docs say it plainly: *make requests for a
   single user serially*. Three threads was enough to get me permanently throttled, while serial
   requests with connection reuse ran at ~8/s without complaint.
3. **A single repo blocked by GitHub** —
   `{"message":"Repository access blocked","block":{"reason":"tos"}}`.

I had classified (3) as (2), so my code kept sleeping and retrying the same blocked repo, forever. If
you write a bulk GitHub crawler, put that string in your error handling; it is stable, it is not a rate
limit, and it will silently eat your retry budget.

## What this changes about my own claims

I have to soften things I said earlier:

- **"`AGENTS.md` is the emerging standard"** — no. **6.2%** of active repos is a real practice, not a
  standard. It *is* roughly 6–9× more common than the vendor-specific alternatives, which is a
  measurable reason to keep the word "format" instead of a vendor name.
- **"`CLAUDE.md` is just a companion file"** — that was a conditional rate described as if it were a
  base rate. Unconditionally, the two are neck and neck.
- **"adoption is spreading"** — unmeasured, see above.

What survives: **it is a habit of active projects** (6.2%) **rather than something the population does**
(1.0%). Those two sentences imply completely different advice, and I could not tell them apart until I
sampled for it.

## The experiment I have not run

There is still a hole underneath all of this, and it is the one that matters: **does any of it work?**
Every number in this project — mine and everyone else's — is descriptive. Nobody has shown that a repo
with an `AGENTS.md` produces better outcomes than the same repo without one, because that requires a
controlled task, a blind judge, and an effect size, not a sample.

I wrote the design for that experiment (three arms, including a placebo arm that gets an equal-length
unrelated document, so "more context" and "this document" can be told apart) but I deliberately did not
run it yet. The sample sizes are brutal and the honest outcome is probably "we could not detect it".

If you have actually noticed a charter changing a decision — a rule that stopped you from doing
something you would otherwise have done — that is the data I cannot generate myself, and it is worth
more to me than a star.

## Reproduce it

```bash
pip install agent-charters              # the CLI
# the sampling code is in the repo, not the package:
git clone https://github.com/janzong/agent-charters
cd agent-charters
.venv/bin/python work/prevalence.py active --per-gen 50   # ~10 min, search-rate-limited
.venv/bin/python work/prevalence.py report
.venv/bin/python work/prevalence.py stock  --n 1000       # ~40 min
.venv/bin/python work/prevalence.py report-stock
```

Seed `20260918`, every response cached, so `report` is instant and costs nothing after the first run.
The full write-up with every caveat I could think of — including the two frames disagreeing (6.2% vs
1.8% on a 57-repo active sub-sample; the honest answer is a range of roughly 2–6%) — is in
`work/audit/prevalence.md` in the repo.

Repo: https://github.com/janzong/agent-charters
