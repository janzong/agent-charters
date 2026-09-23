---
title: Your agent run passed. Can you prove it was allowed?
tags: ai, agents, governance, opensource
series: agent lab notes
published: false
description: A policy-as-code audit for agent runs: cost and call caps, declared artifact contracts, forbidden markers, and a canonical audit_hash. On 13 archived runs, the declared contract, not the data, decided whether they passed.
---

**Short version:** Most agent teams can show a run. Few can show, in one re-runnable command, whether that run was allowed under a policy. I added a policy-as-code audit to `agent-lab-trust`: it checks cost and call caps, the declared artifact contract, and forbidden markers, then emits a canonical `audit_hash`. On 13 archived runs, the default contract passed 0/13 and a declared GenMentor contract passed 13/13. The data did not change. The contract did.

## The gap

Dashboards answer "what happened". Governance needs "what was allowed, and by which rule". A run can succeed and still violate a budget, write an unexpected artifact, or carry a marker that should never ship.

The audit is deliberately boring:

```bash
agent-lab-trust audit <run-root> --policy policy.json
```

A policy can declare:

- `max_cost_usd` and `max_calls` per run;
- `required_artifacts` plus `required_artifacts_mode: all|any`;
- `forbidden_markers`.

The output is a finding list and a canonical `audit_hash`. `deletion-proof --output <path>` writes the deletion evidence used in the same policy flow.

## The demonstration

I ran the audit over 13 archived GenMentor runs.

- Trust-layer default contract (`output/structured.json` or `results/structured.json`): **0/13 passed**, `missing_artifact` ×13, `cost_exceeded` ×1.
- Declared GenMentor contract (`archive.json` and `summary.json`, mode `all`, cap `5.00`): **13/13 passed**, no findings.

Audit hashes:

- default structured contract: `2c122c4ff2c0d5eed11a0fc23b4ff717002864dbd941402e8fe18d6d17c96ce6`
- GenMentor contract: `368b75a06c0f5c205436d287881cfddcbabd94b7ad34a860e852fba59dad7ab5`

The one cost finding is real: `replay-8of8-20260920-a` recorded `3.9529266` under the trust-layer cap `0.60`. Under the GenMentor policy cap `5.00`, it passes. Caps are part of the contract too.

The lesson is not "the audit is noisy". It is that an audit without an explicit run-family contract silently embeds one family's format. The policy has to name the contract, the caps, and the markers.

## Reproduce

```bash
docker run --rm ghcr.io/janzong/agent-lab-trust:rc2
```

or `bash scripts/reproduce.sh`. Expected: `13 passed` under both `TZ=UTC` and `TZ=Asia/Shanghai`, `report_hash` `a841b192981fd7e7`, deletion `audit_hash` `4f0193abbd49a0f9`.

The `:rc2` tag points at the latest published build; `SERIES.md` pins the verification digest `sha256:2e178e63fff30e70ac68501cb17e5316097875932d1d7085e669ce4f8d5a105f`.

## What this does not prove

- no real governance deployment;
- no external reproduction yet;
- no real decision changed yet;
- the 13 runs are a private synthetic family, not published data.

## The series

This is piece 3 of a three-part line: **write it down → test it → govern it**.

1. `agent-charters`: what people actually tell agents.
2. `agent-lab-trust`: whether an agent run is valid and reproducible.
3. this audit: whether a run was allowed under a declared policy.

Index: https://github.com/janzong/agent-lab-trust/blob/main/SERIES.md

## Call

Run the audit on a run family you own. Tell me where the policy and the artifacts disagree. I am also looking for 3 independent reproductions of the trust layer: https://github.com/janzong/agent-lab-trust/issues/1
