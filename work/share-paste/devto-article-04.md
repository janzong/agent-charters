---
title: We ran 2 vs 4 agents six times. Four agents cost 2.1× and did not improve success
tags: ai, agents, llm, opensource
series: agent lab notes
published: false
description: A preregistered deterministic task, six valid live runs, hard call and cost caps, and a negative result. More agents were operationally viable but did not improve task success, at 2.115× the cost.
---

**Short version:** I ran a preregistered 2-agent versus 4-agent comparison on a deterministic task.
Six live runs completed under hard caps. Both groups succeeded in exactly one of three repeats.
The 4-agent group cost **2.115×** more per run and per complete success. More agents were operationally
viable; they were not better on this task.

## The task

The scenario is a deterministic public-repair contribution task:

- eight named participants;
- each participant chooses how many repair units to contribute;
- the task succeeds only if the total reaches a fixed threshold;
- participant coverage is forced, so every selected agent acts;
- no LLM reasoning is used for the choice; the model returns a strict JSON choice.

The point of forcing coverage was to avoid the earlier failure mode where one agent dominated every
turn and the other participants never acted.

## Protocol

| Item | Value |
|---|---|
| Groups | 2 agents / 3 steps; 4 agents / 5 steps |
| Repeats | 3 per group |
| Caps per run | 150 calls / USD 0.50 / 600s |
| Choice model | `deepseek-flash` on a Responses API contract |
| Outcome | machine-decidable `outcome.json` |
| Validity | provenance, coverage, integer choices, arithmetic, caps, port closure, archive hashes |

All six runs passed every validity gate. No parser failure, no budget breach, no port leak.

## Results

| Run | Agents | Total / threshold | Success | Zero contributors | Calls | Total tokens | Cost USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2-agent r1 | 2 | 2 / 3 | no | 1 | 17 | 10,060 | 0.0269116 |
| 2-agent r2 | 2 | 3 / 3 | yes | 0 | 17 | 11,070 | 0.0313716 |
| 2-agent r3 | 2 | 0 / 3 | no | 2 | 17 | 10,255 | 0.0281116 |
| 4-agent r1 | 4 | 3 / 5 | no | 2 | 33 | 21,493 | 0.0597772 |
| 4-agent r2 | 4 | 2 / 5 | no | 2 | 33 | 22,679 | 0.0641372 |
| 4-agent r3 | 4 | 5 / 5 | yes | 0 | 33 | 21,459 | 0.0588042 |

Group aggregates:

| Metric | 2-agent | 4-agent | Ratio |
|---|---:|---:|---:|
| complete successes | 1 / 3 | 1 / 3 | 1.000 |
| mean calls | 17.00 | 33.00 | 1.941 |
| mean total tokens | 10,461.67 | 21,877.00 | 2.091 |
| mean cost USD | 0.028798 | 0.060906 | 2.115 |
| cost per complete success USD | 0.0863948 | 0.1827186 | 2.115 |
| mean zero contributors | 1.000 | 1.333 | 1.333 |

## What I take from it

- More agents are not automatically better. In this task they doubled cost and left more participants
  contributing nothing on average.
- The result is a valid negative result, not an apparatus failure. Every run completed and every
  artifact passed its gates.
- The 4-agent group did produce one complete success, so the mechanism is not broken. It is simply
  not worth 2.115× the cost on this task.

## What this does not show

- It does not show that four agents are worse in general.
- It does not transfer to another task or to a real user.
- It says nothing about agent quality under human review, because no human scored these runs.
- The sample is three repeats per group on one synthetic task.

## Reproduce it

Two pieces are now public:

- **Method package:** https://github.com/janzong/agent-lab-method (MIT, commit `6cc70156facb37baf23fe5fe57dad93d43502b91`) — schema, synthetic GenMentor adapter, fixtures, tests;
- **Trust layer:** https://github.com/janzong/agent-lab-trust (MIT, release `v0.1.0-rc2`) — local-first run validation, hashed reports, and a synthetic deletion proof.

The full protocol and the archived runs stay private. The result is intentionally boring: a negative result with caps, hashes, and every failed run preserved.

I am also looking for **three independent reproductions by non-authors**. The trust layer guide expects `13 passed` under both `TZ=UTC` and `TZ=Asia/Shanghai`, `report_hash` `a841b192981fd7e7`, and deletion `audit_hash` `4f0193abbd49a0f9`. If you run it and any hash differs, that is the most useful reply I can get. If you have a task where you believe more agents should win, that is the experiment I want to run next.
