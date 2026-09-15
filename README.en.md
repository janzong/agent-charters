# agent-charters ｜ a structured corpus of AGENTS.md

[中文](https://github.com/janzong/agent-charters/blob/main/README.md) ｜ **English**

[![charter](https://github.com/janzong/agent-charters/actions/workflows/charter.yml/badge.svg)](https://github.com/janzong/agent-charters/actions/workflows/charter.yml)
[![PyPI](https://img.shields.io/pypi/v/agent-charters)](https://pypi.org/project/agent-charters/)

> A structured corpus of **the written rules humans hand to AI agents**.
> Dataset **v0.5** covers `AGENTS.md`: **558 files** from 558 public repositories.
> It ships a command-line tool that compares any one charter against the baseline of
> the **516 substantive files** in the corpus, and tells you what it is missing.

## A 30-second check-up for your `AGENTS.md`

`compare` answers one question: **which of the nine categories does your charter cover,
and is it missing the ones the corpus writes about most?**

```bash
# One command, from PyPI (published 2026-09-15)
pipx install agent-charters
#   no pipx? use a venv:
#   python -m venv .venv && .venv/bin/pip install agent-charters
#   slow/blocked link to PyPI (the two deps are ~62 MB)? use a mirror:
#   pip install agent-charters -i https://pypi.tuna.tsinghua.edu.cn/simple

agent-charters compare path/to/AGENTS.md
```

Here is a real file from the corpus — `openai/openai-agents-python`'s `AGENTS.md`
(the source text is in [Release `v0.5`](https://github.com/janzong/agent-charters/releases/tag/v0.5);
`data/raw/` is not in the repository, so the path in the output is illustrative —
put in your own file's path and you get your own result):

```text
### AGENTS.md  [34658B, en, 27 sections, rule]
  overview        32.2%    ✓ x1
  structure       59.1%    ✓ x2
  build_test      82.8%    ✓ x3
  style           54.5%    —
  workflow        67.1%    ✓ x7
  environment     45.0%    ✓ x1
  boundaries      85.7%    ✓ x19
  gotchas         13.6%    —
  agent_meta      25.8%    —
```

34 KB, 27 sections, 19 prohibitions — **and it still does not write down any `gotchas`**.
Only **13.6%** of charters in the corpus do; and of the items that do get written down,
**34% are not gotchas at all** ("remember to install the dependencies" and the like;
120 hand-labelled items, see [work/gotcha_origin.md](https://github.com/janzong/agent-charters/blob/main/work/gotcha_origin.md)).

**It does not score your file.** Coverage is a process metric, not a quality metric —
filling all nine boxes does not mean the charter is good. The reasoning is in
[LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md).
What the tool points out is **which box you skipped**.

**Output language**: all five commands print in English or Chinese, following
`LANG` / `LC_ALL` by default — `zh*` → Chinese, anything else (including unset) → **English**.
Force it with `--lang en` / `--lang zh`:

```bash
LANG=en_US.UTF-8 agent-charters compare --lang en path/to/AGENTS.md
```

(For `brief`, `--lang` sets the language of the **prompt handed to the model**, English by
default — the safest thing to feed a model. Without `--lang`, the surrounding checklist
text still follows your machine's locale. See
[agent_charters/i18n.py](https://github.com/janzong/agent-charters/blob/main/agent_charters/i18n.py).)

> The package **is on PyPI**: `pip install agent-charters` (first release 2026-09-15;
> **the current version is on the badge above**). Uploads go through **Trusted Publishing (OIDC)** — the repository
> **stores no token at all**; see [SHARE.md](https://github.com/janzong/agent-charters/blob/main/SHARE.md) §8.
> **Zero runtime dependencies** (since 0.4.0): the install is a few hundred KB and pulls
> no pandas/pyarrow — those are only needed if you want to read parquet
> (`pip install "agent-charters[parquet]"`), which the everyday commands do not.
> The corpus ships as `jsonl.gz` inside the package (~46 KB), so it runs from any directory.
> For a faster route in China: `pipx install "git+https://gitee.com/janzong/agent-charters"`.

## Put it in CI (GitHub Action)

Charters do not usually fail by being wrong — they **quietly go stale**: a directory is
renamed, a script is deleted, a command changes, and the charter still points at the old
path while the agent goes looking for files that no longer exist. So this repository ships
an action that measures it on every PR:

```yaml
# .github/workflows/charter.yml
name: charter
on: [pull_request]
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: janzong/agent-charters@v1
        with:
          path: AGENTS.md
          # optional: turn the job red when these categories are missing
          # (default is report-only, never fail)
          fail-on-missing: 'workflow,gotchas'
```

It does two things, both written to the job summary (it never touches your files and
never posts comments):
**① nine-category coverage** against the 516-file baseline — which categories are missing,
most-common-in-the-corpus first;
**② external references** — checks whether the **Markdown pointers** in the charter
(`[text](path)` links, backticked `.md` / `.mdc` / `.txt` paths, backticked `dir/`)
still exist in the repository.
⚠️ **Only those forms are recognised**: bare filenames such as `scripts/build.sh`,
`agent_charters/gha.py` or `.env` are outside the scan (the narrow scope is deliberate;
the cost is in [LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md) §23).
`fail-on-dangling` is **off** by default — a directory inside a prohibition list
("never commit `dist/`") is not a broken pointer, and the scanner cannot yet tell
"go read this" from "do not commit this", so turning it on will misfire.

This repository uses it too (`uses: ./`, see `.github/workflows/charter.yml`) —
**and it immediately caught us**: our own `AGENTS.md` was judged 8/9, and the missing
`overview` *was* written — its heading ("这是什么") simply is not in the word list.
The attribution and a minimal control are recorded in
[LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md) §22;
**we did not reword the document to turn it green.**

**Two kinds of version number — do not mix them up**: `v1` is the **action tag** — that is
what `uses: janzong/agent-charters@v1` in an external repository resolves to; it follows the
tool and moves when necessary (pin a full commit SHA if you need immutability).
`v0.1` / `v0.5` and friends are **dataset versions**: one-shot, never moved, each with its
own Release and sha256 (see "The data" below).

## What this is

More and more repositories contain a new kind of file: `AGENTS.md`, `CLAUDE.md`,
`.cursorrules`, `copilot-instructions.md`. They are not documentation for humans —
they are **behavioural contracts humans write for AI agents**.

This project collects those files and **annotates them structurally**, in order to answer:

- What do people actually want the AI to know? (Which topics get repeated, which are
  systematically ignored?)
- Is a charter "commands" or "knowledge"?
- How do the conventions differ across languages and repository sizes?

## The data

| Item | Value |
|---|---|
| Files | 558 (518 substantive; 516 usable for category statistics) |
| Repositories | 558 (forks excluded) |
| Collection date | 2026-09-10 |
| Total bytes | 5.3 MB |
| Average labels per file | 4.7 (8 files hit all nine) |
| Licence | code MIT ｜ data CC-BY-4.0 |

> Why two denominators: `is_substantive` only drops empty shells, while `is_pointer` also
> drops files whose body merely points elsewhere (**2 files**; 7 in v0.4). For those, an
> empty `categories` **is the correct result** and they must not be counted in the
> denominator. Every category coverage figure is computed over **516**.
>
> ⚠️ **Coverage figures are not comparable across versions**: v0.2 tightened the
> `is_pointer` rule (denominator 507→511, see [LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md) §10);
> v0.3 fixed substring false hits in the heading channel (`build_test` 87.9% → 85.7%, §11);
> **v0.5** fixed "a `# comment` inside a code block counted as a heading"
> (`build_test` 85.9% → **82.8%** — changes like `section_count` dropping from 146 to 92 on
> the same files come from that) and returned 5 short charters that had been misjudged as
> pointers to the statistic (denominator 511→516, §14). Same files, different rules —
> do not mix the numbers.

**No source text is published** — only derived annotations and statistics. The original
text belongs to each repository's authors.

> **From China**: the main repository is on GitHub; the mirror is
> <https://gitee.com/janzong/agent-charters> (including
> [Release `v0.5`](https://gitee.com/janzong/agent-charters/releases/tag/v0.5)).
> The dataset can also be downloaded straight from
> [GitHub Release `v0.5`](https://github.com/janzong/agent-charters/releases/tag/v0.5)
> (parquet + jsonl).

## Quick start: reading the dataset

```python
import pandas as pd

df = pd.read_parquet("data/processed/agent-charters-v0.5.parquet")
# with the package installed, the same corpus is one line away (no parquet file needed):
# import agent_charters; df = pd.DataFrame(agent_charters.load_corpus())

# the most common topics
from collections import Counter
c = Counter(t for tags in df["categories"] for t in tags)
print(c.most_common())

# substantive files only
sub = df[df["is_substantive"] & ~df["is_pointer"]]
print(len(sub))
```

## Category distribution (516 substantive files, dataset v0.5 / `ruleset_v0.1.8`)

| Category | Coverage | Meaning |
|---|---|---|
| `boundaries` | **85.7%** | prohibitions, limits, things not to do (**45.2%** have at least one **dedicated section** of prohibitions) |
| `build_test` | **82.8%** | build / test / run commands |
| `workflow` | 67.1% | branches, commits, PRs, releases |
| `structure` | 59.1% | architecture, directory and file layout |
| `style` | 54.5% | code style, naming, conventions |
| `environment` | 45.0% | environment, toolchain, dependencies |
| `overview` | 32.2% | project overview, stack, purpose |
| `agent_meta` | 25.8% | rules about the AI's own behaviour |
| `gotchas` | 13.6% | pitfalls, traps, known issues |

> The top two are tied within 2.9pp — **smaller than the known false-positive rate of
> `boundaries`** (the `Do not …` pattern, ~3%) — so we do not claim a clear lead.
> `boundaries` also has two readings: **a dedicated prohibition section** in 45.2%
> (heading channel) versus **a prohibition statement anywhere** in 85.7% (including the
> `Do not …` pattern in the body). Both numbers are right; they answer different questions.
> See [FINDINGS.md](https://github.com/janzong/agent-charters/blob/main/FINDINGS.md) §1.

## Command-line tool (full reference)

The shortest path was above; this is the whole set. With the dependencies installed
(or `.venv/bin/python -m agent_charters` from the repository root):

```bash
# before writing a charter: a checklist + a prompt you can paste into a generator
agent-charters brief
# with an existing file: the checklist marks what you are missing, and the
# gaps go into the prompt
agent-charters brief path/to/AGENTS.md

# version numbers (tool version + dataset version)
agent-charters --version

# the big picture: what the corpus looks like
agent-charters stats

# compare your charter against the corpus — see what it is missing
agent-charters compare path/to/AGENTS.md [more files...]

# see how a category is actually written (by number of sections, descending)
agent-charters show gotchas --limit 8

# where the knowledge lives: is the charter self-contained, or does it send the
# agent elsewhere (and are those pointers still valid?)
agent-charters refs path/to/AGENTS.md
```

`compare` is for people writing a charter: it names **the categories the corpus writes
about most that you have not written at all**, plus each category's coverage in the
corpus. Chinese files work the same way.

`compare` also does something the measurements forced on it: when the file **is itself a
pointer** — a `CLAUDE.md` whose entire body is `@AGENTS.md`, or a single line like
`Read \`CLAUDE.md\` before repository work.` — it does not report "you wrote nothing".
It **follows the pointer and judges the target**, saying so in the output ("the numbers
below are `AGENTS.md`"). This is not a corner case: of 791 root-level charters, **111**
are symlinks and **75** are such pure pointers, median **11 bytes** — reporting 0/9 for
those would be a wrong answer. When the target is not next to the file, it says the
pointer could not be followed instead of pretending it did.

`brief` is for people about to *generate* a charter, and it is based on measurement
rather than folklore: a controlled experiment over 11 repositories found that
auto-generated coverage **is decided by the shape of the prompt** — when the prompt did
not name "collaboration workflow", 11/11 charters omitted it; when it did, 3/3 wrote it
immediately.

`refs` measures a dimension outside the nine categories: **where the knowledge lives**.
Of the 516 files, **49%** route the agent elsewhere ("read / see X.md"), **15%** point at a
knowledge store or rules directory, **54%** do either — meaning the assumption that
"one `AGENTS.md` carries all the rules" does not hold for nearly half the sample.
Since v0.2 those three are dataset fields (`imperative_route` / `hard_route` /
`routes_outward`) and can be recomputed by anyone.

It also lists **paths that are pointed at but do not exist**: pointing the wrong way is
worse than not pointing at all, because the agent will go looking for a file that is not
there.

So `brief` outputs **the questions worth asking** (proportions computed live from the
corpus) plus a prompt you can paste. Re-running those repositories with that prompt moved
coverage from 4–5 categories to **9/9** (see `work/auto_vs_human.md`, section 6).

## Documentation

**If you are an agent or collaborator taking this over, read
[STATE.md](https://github.com/janzong/agent-charters/blob/main/STATE.md) first** — project
status, decision records, the non-negotiable zone and the roadmap all live there.

- [STATE.md](https://github.com/janzong/agent-charters/blob/main/STATE.md) — **entry point for a handover**: status / decisions / roadmap / non-negotiables
- [TAXONOMY.md](https://github.com/janzong/agent-charters/blob/main/TAXONOMY.md) — the definition and decision rules of the nine categories
- [SCHEMA.md](https://github.com/janzong/agent-charters/blob/main/SCHEMA.md) — all 30 fields
- [FINDINGS.md](https://github.com/janzong/agent-charters/blob/main/FINDINGS.md) — early findings
- [LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md) — **known limitations (please read first)**
- [ENVIRONMENT.md](https://github.com/janzong/agent-charters/blob/main/ENVIRONMENT.md) — collection environment and channel notes

## Reproducing

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python work/discover_repos2.py      # enumerate candidate repositories
.venv/bin/python work/fetch_full.py work/repos_topics.txt  # fetch
.venv/bin/python work/extract_v1.py           # extract
.venv/bin/python work/pack.py                 # package (release parquet + bundled jsonl.gz)
.venv/bin/pytest -q                           # smoke tests (168)
```

**Longitudinal baseline**: `data/processed/baseline-2026-09-10.tsv` freezes each
repository's `file_sha` for this snapshot. Re-fetch in three months and run
`work/longitudinal.py` to measure "how many charters were replaced, and how many of the
new ones are template output sharing a sha" — the only way we know of to measure
machines writing charters in bulk.

> `work/extract_v1.py` does not implement the classification rules itself — it calls
> `agent_charters.extract`, so that "the rules used to build the dataset" and "the rules
> shipped in the package" are necessarily the same set. One test fails if they ever
> diverge; that brake is intentional.

> Fetching relies on an authenticated `gh` CLI, and note the `code_search` rate limit
> (10/min). Environment details are in `ENVIRONMENT.md`.

## Licence and copyright

- **Code** (`agent_charters/`, `work/`): MIT, see [LICENSE](https://github.com/janzong/agent-charters/blob/main/LICENSE)
- **Data** (annotations and statistics under `data/processed/`): CC-BY-4.0, attribution `agent-charters v0.5`
- **Source text**: this repository contains **no `AGENTS.md` source text at all**
  (`data/raw/` is in `.gitignore`). The dataset holds only derived annotations,
  statistical features and very short quotations; the original text belongs to each
  repository's authors.

To retrieve the source text: use each row's `repo_full_name` + `file_path` + `file_sha`
to fetch the byte-identical file from GitHub.

## Citation

```
agent-charters v0.5 (2026). A corpus of agent charters (AGENTS.md).
https://github.com/janzong/agent-charters
```

## Known limitations

**Please do not use this data without reading
[LIMITATIONS.md](https://github.com/janzong/agent-charters/blob/main/LIMITATIONS.md).**
The four most important ones:

- Classification is rule-based, not item-by-item human labelling. **Measured accuracy**:
  on a 55-file holdout (never used to tune the rules) micro-averaged precision **92%** /
  recall **70%** (`LIMITATIONS.md` §19); on 100 in-sample files, precision 80–92% /
  recall 75–84% (§16, an upper bound). Weakest: `gotchas` (recall 32–38%) and
  `build_test` on Chinese files (precision 61%, in-sample only).
- Chinese files are only 4.8% of the corpus (25/516); any per-language comparison lacks
  statistical power.
- The crawl pool is biased towards AI/agent-topic repositories; it is not GitHub.
- The body pattern `Do not …` for `boundaries` has a known ~3% false-positive rate, and
  it drives the headline ordering (§13).
