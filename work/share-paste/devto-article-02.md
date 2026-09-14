---
title: I looked at 558 AGENTS.md files: here's a 5-minute check for yours
tags: ai, agents, devtools, productivity
series: AGENTS.md in the wild
published: false
description: 85.7% of AGENTS.md files prohibit things, only 13.6% record a gotcha. The measured base rates across 558 files, the two slots nobody fills, and a 5-minute check for your own file.
---

**Short version:** I labeled 558 public `AGENTS.md` files against a 9-category taxonomy. The measured
base rates say something boring and useful — almost every file **prohibits** things (85.7%) and lists
**build/test commands** (82.8%), while almost none of them record a **gotcha** (13.6%). Two of the nine
slots are nearly empty across the whole corpus: `gotchas` and `agent_meta` (rules about the agent itself,
25.8%).

Then I ran the same ruler over two big, well-maintained files. Both missed `gotchas`. So here is a
five-minute check you can run on your own file, and the exact numbers behind it.

## The base rates

Measured on 516 substantive files (558 collected, the rest were one-line pointers):

```
boundaries     85.7%   what must never be done
build_test     82.8%   the commands CI runs
workflow       67.1%   commit format, branches, release steps
structure      59.1%   layout, where new code belongs
style          54.5%   naming, formatting — or a pointer to the config that enforces it
environment    45.0%   toolchain versions, required env vars
overview       32.2%   one paragraph: what this is, what it deliberately is not
agent_meta     25.8%   rules about the agent: tone, when to ask first
gotchas        13.6%   pitfalls that are NOT derivable from the code
```

The shape is not surprising once you see it as a genre: an `AGENTS.md` is usually written *defensively*,
as a list of things not to break. The file that would actually save you time is the one almost nobody
writes.

## Two receipts

`compare` prints your file's coverage next to the corpus baseline. Two real examples from the corpus:

| file | size | sections | coverage | missing |
|---|---|---|---|---|
| `langchain-ai/deepagents` | 10 KB | 22 | **7/9** | `overview`, `gotchas` |
| `openai/openai-agents-python` | 34 KB | 27 | **6/9** | `style`, `agent_meta`, `gotchas` |

Both are good files. The 34 KB one is one of the more thorough agent-instruction files in the corpus —
27 sections, 19 separate boundary markers. It still has nothing in it that you could only learn by
running the thing.

## Why gotchas are rare (and why that is not laziness)

You can only write a gotcha *after* being bitten by it — and by the time you have been bitten, the
temptation is to **fix the thing** rather than write the sentence down. The fix is visible in the code;
the sentence is a liability nobody wants to maintain.

There is a second, worse failure mode. I sampled 347 entries from the `Gotchas` / `Common Pitfalls` /
`Troubleshooting` sections in the corpus (an earlier snapshot, 507 files) and hand-labeled 120 of them:

- **58%** are readable from the repo itself (interface contracts, platform limits, build requirements)
- **34%** are not pitfalls at all — they are generic advice ("remember to install dependencies", "don't
  commit `.env`"), the same sentence you would write for any project
- **8%** are genuinely experience-only: upstream/third-party behaviour, past incidents, and the places
  where the docs disagree with the code

So the section is rare, and a third of what does live there is filler. The 8% is the part worth
handing to an agent, and it cannot be generated from a reading of the repository. It has to come from
a person who was there.

## The five-minute check

No tool needed. Ask these five questions about your own file:

1. **Are the commands copy-pasteable?** Not "run the tests" — the actual command CI runs, with the
   working directory. If your README says one port and production uses another, say so (that mistake
   is in the corpus, in a file that otherwise looks complete).
2. **Does it name what must never be committed or never touched?** This is the one thing the corpus
   does well (85.7%) — check that yours names the *tempting* case, not the obvious one. "Don't commit
   secrets" is obvious; "don't hand-edit the production database to fix a row, use the backfill script"
   is a boundary that will actually stop someone.
3. **Does it say anything about the agent's own behaviour?** Only 25.8% do. Tone, when to stop and ask,
   which actions need explicit approval, what must not leave the machine.
4. **Is there at least one sentence that is not derivable from the code?** If every line in your file
   could have been written by reading the repo, the file is documentation, not a charter. This is the
   gotcha test.
5. **Do the paths it points at exist?** Measured: 49% of files route to another file, and 15% point at a
   knowledge store or rules directory. A pointer to a file that moved is worse than no pointer — an
   agent will go looking, and will read whatever it finds there as authoritative.

## If you want the baseline instead of the feeling

```bash
git clone https://github.com/janzong/agent-charters   # CN mirror: gitee.com/janzong/agent-charters
cd agent-charters
python -m venv .venv && .venv/bin/pip install .
.venv/bin/agent-charters compare path/to/AGENTS.md   # coverage vs the 558-file baseline, plus gaps
.venv/bin/agent-charters brief                       # the checklist + a paste-ready prompt
.venv/bin/agent-charters refs path/to/AGENTS.md      # external pointers and dangling references
```

(Not on PyPI — the install is a clone. I verified the sequence above in a clean virtualenv on a
machine that had never seen the repo.)

`compare` is the one that answers question 4 in aggregate. It also does something I did not expect:
when I used `brief`'s prompt to write a charter for a real project, `compare` flagged coverage I had
skipped — and one of the nine slots it missed was the *name of the slot itself*, which is a bug in my
taxonomy, not in the file. That is the kind of thing a rule-based labeler gives you: you can point at
the pattern that fired and argue with it.

There is no LLM in the labeling loop. Every label is recomputable and arguable, which is the point —
if you disagree with a label, you can find the rule that produced it and overrule it.

## What this is not

I do not want to oversell the numbers, so:

- The classifier scores **92% precision / 70% recall** on a 55-file held-out English set, and
  **88% / 73%** on 50 held-out Chinese files. The recall number is the honest one: it misses roughly
  **three in ten** of the labels it should have produced. `gotchas` and `agent_meta` are the weakest
  slots in both languages.
- The held-out sets were labeled by **one person (me)**. No second annotator, no inter-annotator
  agreement.
- **Coverage is a process metric, not a quality metric.** In a 3-repo test, a checklist that names all
  nine slots pushed a generator from 4–5 categories to 9/9 — and filling all nine slots is not the same
  as writing a good file. It is a prompt for the questions, not a grade.
- The labels and the rates come from public files and a rule-based classifier, not from a language
  model. The one LLM in this story is the generator in the 3-repo test, which is why that number is
  reported as n=3.

## The ask

The weakest part of this project is that the only person who has ever tested it is its author. If you
have an `AGENTS.md` (or a `CLAUDE.md`, or a `.cursorrules`) on a real project, run `compare` on it and
tell me what it gets wrong — the file, the label, or the baseline rate. A wrong label on your file is
worth more to me than a star.

Repo: https://github.com/janzong/agent-charters
